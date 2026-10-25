import os,sys
from pathlib import Path
from fastapi import Depends
from fastapi.testclient import TestClient

def test_real_password_sqlite_cookie_csrf_and_restart(tmp_path):
 root=Path(os.environ['GWA_WEB_AUTH_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.storage import initialize
 from app.auth import AuthService
 from app.web_auth import create_auth_app
 db=tmp_path/'auth.sqlite';initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);a=AuthService(db);app=create_auth_app(a,port=8501)
 @app.get('/api/test-protected')
 async def protected(s=Depends(app.state.require_operator)):return {'operator':s['operator']}
 h={'Origin':'http://127.0.0.1:8501'}
 with TestClient(app,base_url='http://127.0.0.1:8501') as c:
  assert c.post('/api/auth/setup',headers=h,json={'password':'SYNTHETIC-password','confirmation':'SYNTHETIC-password'}).status_code==200
  r=c.post('/api/auth/login',headers=h,json={'password':'SYNTHETIC-password'});assert r.status_code==200;csrf=r.json()['csrf'];token=c.cookies.get('gwa_session');assert 'SYNTHETIC-password' not in r.text and token not in r.text
  assert c.get('/api/test-protected').status_code==200
  assert c.post('/api/auth/logout',headers=dict(h,**{'X-CSRF-Token':csrf})).status_code==200
  assert c.get('/api/test-protected').status_code==401
 b=AuthService(db);assert b.has_password();assert b.authenticate(token) is None
 assert b.login('SYNTHETIC-password')['csrf']
 sys.path.remove(str(root))
