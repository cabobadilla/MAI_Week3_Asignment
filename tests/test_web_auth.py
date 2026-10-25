import os,sys
from pathlib import Path
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
class FakeAuth:
 def __init__(self):self.set=False;self.sessions={};self.password=None
 def has_password(self):return self.set
 def setup(self,password,confirmation):
  if self.set:raise ValueError('already')
  if password!=confirmation or len(password)<8:raise ValueError('invalid')
  self.set=True;self.password=password
 def login(self,password,client_id='local'):
  if not self.set or password!=self.password:raise ValueError('SYNTHETIC-SECRET')
  self.sessions['SYNTHETIC-TOKEN']={'operator':'operator','csrf':'SYNTHETIC-CSRF'};return {'token':'SYNTHETIC-TOKEN','csrf':'SYNTHETIC-CSRF','expires_in':28800}
 def authenticate(self,token):return self.sessions.get(token)
 def logout(self,token):self.sessions.pop(token,None)
@pytest.fixture
def ctx():
 root=Path(os.environ['GWA_WEB_AUTH_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.web_auth import create_auth_app
 auth=FakeAuth();app=create_auth_app(auth,port=8501)
 @app.get('/api/protected')
 async def protected(session=Depends(app.state.require_operator)):return {'operator':session['operator']}
 @app.post('/api/write')
 async def write():return {'ok':True}
 with TestClient(app,base_url='http://127.0.0.1:8501') as c:yield c,auth
 sys.path.remove(str(root))
def setup_login(c):
 h={'Origin':'http://127.0.0.1:8501'}
 assert c.post('/api/auth/setup',headers=h,json={'password':'SYNTHETIC-PASS','confirmation':'SYNTHETIC-PASS'}).status_code==200
 return c.post('/api/auth/login',headers=h,json={'password':'SYNTHETIC-PASS'})
def test_host_boundary(ctx):
 c,a=ctx
 for h in ['evil.test','127.0.0.1:9999','127.0.0.1.evil:8501','localhost:8502']:
  assert c.get('/api/health',headers={'Host':h}).status_code==403
 assert c.get('/api/health').json()['generation']=='simulated'
def test_origin_required_and_exact(ctx):
 c,a=ctx
 for h in [{},{'Origin':'https://evil.test'},{'Origin':'http://localhost:8501'},{'Origin':'http://127.0.0.1:9999'}]:
  assert c.post('/api/auth/setup',headers=h,json={'password':'SYNTHETIC-PASS','confirmation':'SYNTHETIC-PASS'}).status_code==403
 assert not a.set
def test_setup_and_session_status(ctx):
 c,a=ctx;assert c.get('/api/session').json()['setup_required'];r=setup_login(c);assert r.status_code==200
 assert c.post('/api/auth/setup',headers={'Origin':'http://127.0.0.1:8501'},json={'password':'SYNTHETIC-PASS','confirmation':'SYNTHETIC-PASS'}).status_code==409
 s=c.get('/api/session').json();assert s['authenticated'] and s['csrf']=='SYNTHETIC-CSRF' and not s['setup_required']
def test_cookie_no_token_leak_and_headers(ctx):
 c,a=ctx;r=setup_login(c);assert 'SYNTHETIC-TOKEN' not in r.text
 cookie=r.headers['set-cookie'].lower();assert 'httponly' in cookie and 'samesite=strict' in cookie and 'path=/' in cookie
 assert r.headers['cache-control']=='no-store' and r.headers['x-content-type-options']=='nosniff'
def test_read_dependency_and_write_csrf(ctx):
 c,a=ctx;assert c.get('/api/protected').status_code==401;assert c.post('/api/write',headers={'Origin':'http://127.0.0.1:8501'}).status_code==401
 setup_login(c);assert c.get('/api/protected').status_code==200
 h={'Origin':'http://127.0.0.1:8501'};assert c.post('/api/write',headers=h).status_code==403
 h['X-CSRF-Token']='wrong';assert c.post('/api/write',headers=h).status_code==403
 h['X-CSRF-Token']='SYNTHETIC-CSRF';assert c.post('/api/write',headers=h).status_code==200
def test_logout_invalidates(ctx):
 c,a=ctx;setup_login(c);assert c.post('/api/auth/logout',headers={'Origin':'http://127.0.0.1:8501','X-CSRF-Token':'SYNTHETIC-CSRF'}).status_code==200;assert not a.sessions;assert c.get('/api/protected').status_code==401
def test_wrong_login_sanitized(ctx):
 c,a=ctx;setup_login(c);r=c.post('/api/auth/login',headers={'Origin':'http://127.0.0.1:8501'},json={'password':'wrong'});assert r.status_code==401;assert 'SYNTHETIC-SECRET' not in r.text
def test_malformed_and_oversized(ctx):
 c,a=ctx;h={'Origin':'http://127.0.0.1:8501'}
 for payload in [[],{}, {'password':3,'confirmation':3}]:assert c.post('/api/auth/setup',headers=h,json=payload).status_code==400
 assert c.post('/api/auth/setup',headers=h,content=b'x'*65537).status_code in (400,413)
def test_docs_disabled(ctx):
 c,a=ctx
 for path in ['/docs','/redoc','/openapi.json']:assert c.get(path).status_code==404
