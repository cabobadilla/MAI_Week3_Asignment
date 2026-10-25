import os,sys,uuid,json
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_DIRECTED_VIEW_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,organizations,recipients,demo_generation,companies
 from app.web_directed_view import mount_directed_view
 db=tmp_path/'directed.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','T','O',academic_suite=True);orgs=[organizations.save_organization(conn,'Org '+str(i),[{'name':'Persona','email':f'p{i}@example.test'}],roles=['aportante']) for i in range(2)];targets=[recipients.add_recipient(conn,cam['id'],o['contacts'][0]['id']) for o in orgs];bundle=demo_generation.generate_demo(conn,cam['id']);email=next(v for v in bundle['versions'] if v['format']=='email');app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_directed_view(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,orgs,targets,bundle,email,companies
 conn.close();sys.path.remove(str(root))
def test_read_only_versions_and_frozen_recipients(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;r=c.get('/api/campaigns/'+cam['id']+'/directed');assert r.status_code==200;d=r.json();assert len(d['versions'])==1 and d['versions'][0]['id']==e['id'];assert {x['id'] for x in d['recipients']}=={x['id'] for x in targets};assert d['records']==[]
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0

def test_manual_records_isolated_and_preserved(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;from app.distribution import record_email_batch
 from app.campaigns import create_campaign
 rows=record_email_batch(db,cam['id'],e['id'],[x['id'] for x in targets],'2026-10-25T12:00:00+00:00',str(uuid.uuid4()),confirmed=True)
 d=c.get('/api/campaigns/'+cam['id']+'/directed').json();assert {x['id'] for x in d['records']}=={x['id'] for x in rows}
 other=create_campaign(db,'Otra','T','O');assert c.get('/api/campaigns/'+other['id']+'/directed').json()['records']==[]

def test_auth_and_missing_campaign(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;assert c.get('/api/campaigns/missing/directed').status_code==400;c.headers.pop('X-Test-Auth');assert c.get('/api/campaigns/'+cam['id']+'/directed').status_code==401
