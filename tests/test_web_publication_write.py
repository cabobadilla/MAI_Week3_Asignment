import os,sys,uuid
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_PUBLIC_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,demo_generation
 from app.web_publications import mount_publications
 db=tmp_path/'pub.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','T','O',academic_suite=True);bundle=demo_generation.generate_demo(conn,cam['id']);version=next(v for v in bundle['versions'] if v['format']=='linkedin');app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_publications(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,version,bundle
 conn.close();sys.path.remove(str(root))
def payload(v,**kw):
 p={'version_id':v['id'],'channel':'linkedin','occurred_at':'2026-10-25T12:00:00+00:00','operation_id':str(uuid.uuid4()),'confirmed':True};p.update(kw);return p
def test_confirmed_manual_record_only(ctx):
 c,db,cam,v,b=ctx;url='/api/campaigns/'+cam['id']+'/publications'
 assert c.post(url,json=payload(v,confirmed=False)).status_code==400
 r=c.post(url,json=payload(v));assert r.status_code==200 and r.json()['record']['campaign_recipient_id'] is None
 assert db.execute('SELECT count(*) FROM company').fetchone()[0]==0
 assert db.execute('SELECT count(*) FROM followup_event').fetchone()[0]==0
 assert db.execute('SELECT count(*) FROM export_record').fetchone()[0]==0

def test_retry_idempotent_and_payload_collision(ctx):
 c,db,cam,v,b=ctx;url='/api/campaigns/'+cam['id']+'/publications';p=payload(v)
 a=c.post(url,json=p);z=c.post(url,json=p);assert a.status_code==z.status_code==200 and a.json()==z.json()
 p['occurred_at']='2026-10-24T12:00:00+00:00';assert c.post(url,json=p).status_code==400
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==1

def test_invalid_input_no_write(ctx):
 c,db,cam,v,b=ctx;url='/api/campaigns/'+cam['id']+'/publications'
 for kw in [{'channel':'web'},{'occurred_at':'2026-10-25'},{'actor':'someone'},{'reaction_note':'Not this operation'},{'confirmed':'true'},{'version_id':'missing'}]:
  assert c.post(url,json=payload(v,**kw)).status_code==400
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0

def test_duplicate_needs_explicit_repeat_reason(ctx):
 c,db,cam,v,b=ctx;url='/api/campaigns/'+cam['id']+'/publications'
 assert c.post(url,json=payload(v)).status_code==200
 assert c.post(url,json=payload(v)).status_code==400
 assert c.post(url,json=payload(v,repeat_reason='Republicación manual sintética')).status_code==200
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==2

def test_auth_and_no_automatic_read_write(ctx):
 c,db,cam,v,b=ctx;url='/api/campaigns/'+cam['id']+'/publications'
 assert c.get(url).status_code==405
 c.headers.pop('X-Test-Auth');assert c.post(url,json=payload(v)).status_code==401
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0
