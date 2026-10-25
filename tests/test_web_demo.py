import os,sys,uuid
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_DEMO_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns
 from app.web_demo import mount_demo
 db=tmp_path/'api.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','Tema','Objetivo',academic_suite=True);app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_demo(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,campaigns
 conn.close();sys.path.remove(str(root))
def test_post_is_explicit_demo_and_no_approval(ctx):
 c,db,cam,ca=ctx;r=c.post('/api/campaigns/'+cam['id']+'/demo',json={'run_id':str(uuid.uuid4())});assert r.status_code==200;x=r.json();assert x['mode']=='demo' and x['generation']=='simulated' and len(x['versions'])==6 and x['run']['status']=='needs_review'
 for table in ['approval','export_record','distribution_record']:assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
 assert x['run']['metrics']['attempts']==0
def test_read_and_retry_do_not_regenerate(ctx):
 c,db,cam,ca=ctx;id=str(uuid.uuid4());url='/api/campaigns/'+cam['id']+'/demo';a=c.post(url,json={'run_id':id}).json();b=c.post(url,json={'run_id':id}).json();read=c.get('/api/runs/'+id+'/bundle');assert read.status_code==200;assert {x['id'] for x in a['versions']}=={x['id'] for x in b['versions']}=={x['id'] for x in read.json()['versions']};assert db.execute('SELECT count(*) FROM content_version').fetchone()[0]==6;assert len(c.get('/api/campaigns/'+cam['id']+'/runs').json())==1
def test_campaign_isolation(ctx):
 c,db,cam,ca=ctx;other=ca.create_campaign(db,'Otra','T','O');c.post('/api/campaigns/'+cam['id']+'/demo',json={});assert c.get('/api/campaigns/'+other['id']+'/runs').json()==[]
def test_bad_request_has_no_write(ctx):
 c,db,cam,ca=ctx;url='/api/campaigns/'+cam['id']+'/demo'
 for p in [[],{'run_id':'not-a-uuid'},{'run_id':3},{'provider':'real'}]:assert c.post(url,json=p).status_code==400
 assert db.execute('SELECT count(*) FROM generation_run').fetchone()[0]==0
 assert c.get('/api/runs/missing/bundle').status_code==400
def test_auth_required(ctx):
 c,db,cam,ca=ctx;c.headers.pop('X-Test-Auth');assert c.post('/api/campaigns/'+cam['id']+'/demo',json={}).status_code==401;assert c.get('/api/campaigns/'+cam['id']+'/runs').status_code==401
