import os,sys
from pathlib import Path
from fastapi.testclient import TestClient

def test_real_auth_organization_campaign_http_flow(tmp_path):
 root=Path(os.environ['GWA_CATALOG_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.storage import initialize,connect
 from app.auth import AuthService
 from app.web_auth import create_auth_app
 from app.web_organizations import mount_organizations
 from app.web_campaigns import mount_campaigns
 db=tmp_path/'catalog.sqlite';initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);app=create_auth_app(AuthService(db),port=8501);mount_organizations(app,db);mount_campaigns(app,db)
 h={'Origin':'http://127.0.0.1:8501'}
 with TestClient(app,base_url='http://127.0.0.1:8501') as c:
  assert c.get('/api/organizations').status_code==401
  assert c.post('/api/auth/setup',headers=h,json={'password':'SYNTHETIC-password','confirmation':'SYNTHETIC-password'}).status_code==200
  login=c.post('/api/auth/login',headers=h,json={'password':'SYNTHETIC-password'});assert login.status_code==200;h['X-CSRF-Token']=login.json()['csrf']
  body={'name':'Organización sintética','roles':['aportante','beneficiaria'],'contacts':[{'name':'Uno','email':'uno@example.test'},{'name':'Dos','email':'dos@example.test'},{'name':'Tres','email':'tres@example.test'}]}
  org=c.post('/api/organizations',headers=h,json=body);assert org.status_code==200;o=org.json();assert len(o['contacts'])==3
  cam=c.post('/api/campaigns',headers=h,json={'title':'Campaña sintética','topic':'Formación','objective':'Presentar propósito','academic_suite':True});assert cam.status_code==200;assert len(cam.json()['formats'])==4
  assert len(c.get('/api/organizations').json())==1 and len(c.get('/api/campaigns').json())==1
  bad=dict(body);bad['name']='No debe guardarse';bad['contacts']=[{'name':'Parcial','email':''}];assert c.post('/api/organizations',headers=h,json=bad).status_code==400;assert len(c.get('/api/organizations').json())==1
  assert c.post('/api/campaigns',headers={'Origin':'http://evil.test','X-CSRF-Token':h['X-CSRF-Token']},json={'title':'Ataque','topic':'T','objective':'O'}).status_code==403
  assert len(c.get('/api/campaigns').json())==1
  assert c.post('/api/auth/logout',headers=h).status_code==200;assert c.get('/api/campaigns').status_code==401
 conn=connect(db)
 try:assert conn.execute('SELECT count(*) FROM contact').fetchone()[0]==3;assert conn.execute('SELECT count(*) FROM campaign').fetchone()[0]==1
 finally:conn.close()
 assert not any(x=='torch' or x.startswith('faiss') for x in sys.modules)
 sys.path.remove(str(root))
