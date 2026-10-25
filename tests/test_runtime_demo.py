import os,sys,shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def runtime(tmp_path,monkeypatch):
 candidate=Path(os.environ['GWA_RUNTIME_CANDIDATE']);sys.path.insert(0,str(candidate))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import bootstrap
 from app.runtime import create_demo_app
 def deny_env(*args,**kwargs):raise AssertionError('DEMO must never read .env')
 monkeypatch.setattr(bootstrap,'_read_dotenv',deny_env)
 root=tmp_path/'project';(root/'config').mkdir(parents=True);(root/'app/migrations').mkdir(parents=True)
 shutil.copyfile(os.environ['GWA_CONFIG_TOML'],root/'config/local.toml');shutil.copyfile(os.environ['GWA_SCHEMA_FILE'],root/'app/migrations/001_initial.sql')
 (root/'.env').write_text('OPENROUTER_API_KEY=SYNTHETIC-never-load\nAPP_LLM_ENABLED=true\n')
 yield create_demo_app,root
 sys.path.remove(str(candidate))

def login(c,setup=True):
 h={'Origin':'http://127.0.0.1:8501'}
 if setup:assert c.post('/api/auth/setup',headers=h,json={'password':'SYNTHETIC-demo-password','confirmation':'SYNTHETIC-demo-password'}).status_code==200
 r=c.post('/api/auth/login',headers=h,json={'password':'SYNTHETIC-demo-password'});assert r.status_code==200
 return dict(h,**{'X-CSRF-Token':r.json()['csrf']})

def test_demo_wiring_auth_and_persistence(runtime):
 create,root=runtime;app=create(root)
 with TestClient(app,base_url='http://127.0.0.1:8501') as c:
  assert c.get('/').status_code==200 and 'DEMO' in c.get('/').text
  assert c.get('/api/organizations').status_code==401
  h=login(c);r=c.post('/api/organizations',headers=h,json={'name':'Sintética','roles':['beneficiaria'],'contacts':[{'name':'Persona','email':'p@example.test'}]});assert r.status_code==200
  camp=c.post('/api/campaigns',headers=h,json={'title':'DEMO','topic':'T','objective':'O','audience_segment':'companies','tone':'Cercano','academic_suite':True}).json();assert isinstance(camp['id'],str)
  r=c.post('/api/campaigns/'+camp['id']+'/demo',headers=h,json={});assert r.status_code==200 and len(r.json()['versions'])==6
  cookie=c.cookies.get('gwa_session')
 app2=create(root)
 with TestClient(app2,base_url='http://127.0.0.1:8501') as c:
  c.cookies.set('gwa_session',cookie);assert c.get('/api/organizations').status_code==401
  login(c,setup=False);assert len(c.get('/api/organizations').json())==1;assert len(c.get('/api/campaigns').json())==1
 assert not any(k=='torch' or k.startswith('faiss') for k in sys.modules)

def test_demo_port_and_local_host_guard(runtime):
 create,root=runtime
 for port in [0,True,65536]:
  with pytest.raises((ValueError,TypeError)):create(root,port=port)
 app=create(root)
 with TestClient(app,base_url='http://outside.test:8501') as c:assert c.get('/api/health').status_code==403
