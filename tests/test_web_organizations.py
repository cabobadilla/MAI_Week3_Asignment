import os,sys
from pathlib import Path
import pytest
from fastapi import FastAPI,HTTPException,Request
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_ORG_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage
 from app.web_organizations import mount_organizations
 db=tmp_path/'test.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True)
 app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator','csrf':'synthetic'}
 app.state.require_operator=require;mount_organizations(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as c:yield c,storage,db
 sys.path.remove(str(root))
def data(n=1):return {'name':'Organización sintética','roles':['aportante','beneficiaria'],'contacts':[{'name':f'Contacto {i}','email':f'c{i}@example.test'} for i in range(n)]}
def test_one_with_blank_optional_rows(ctx):
 c,s,db=ctx;p=data();p['contacts'] += [{'name':'','email':''}]*2;r=c.post('/api/organizations',json=p);assert r.status_code==200;r=r.json();assert len(r['contacts'])==1 and set(r['roles'])=={'aportante','beneficiaria'};assert isinstance(r['id'],str)
def test_three_contacts_round_trip(ctx):
 c,s,db=ctx;r=c.post('/api/organizations',json=data(3));assert r.status_code==200;o=r.json();assert len(o['contacts'])==3;assert c.get('/api/organizations/'+o['id']).json()['name']=='Organización sintética';assert len(c.get('/api/organizations').json())==1
def test_partial_invalid_rolls_back(ctx):
 c,s,db=ctx;p=data();p['contacts'].append({'name':'Solo nombre','email':''});assert c.post('/api/organizations',json=p).status_code==400;assert c.get('/api/organizations').json()==[]
def test_edit_preserves_contacts_and_ids(ctx):
 c,s,db=ctx;o=c.post('/api/organizations',json=data(3)).json();p={'name':'Municipalidad sintética','contacts':[{'id':o['contacts'][0]['id'],'name':'Editado','email':o['contacts'][0]['email']}]};r=c.put('/api/organizations/'+o['id'],json=p);assert r.status_code==200;o2=r.json();assert len(o2['contacts'])==3 and {x['id'] for x in o2['contacts']}=={x['id'] for x in o['contacts']}
def test_no_rigid_three_limit(ctx):
 c,s,db=ctx;r=c.post('/api/organizations',json=data(4));assert r.status_code==200 and len(r.json()['contacts'])==4
def test_reject_unknown_and_bad_body(ctx):
 c,s,db=ctx;p=data();p['sql']='drop';assert c.post('/api/organizations',json=p).status_code==400;assert c.post('/api/organizations',json=[]).status_code==400
def test_unauthenticated_cannot_read_or_write(ctx):
 c,s,db=ctx;c.headers.pop('X-Test-Auth');assert c.get('/api/organizations').status_code==401;assert c.post('/api/organizations',json=data()).status_code==401
