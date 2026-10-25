import os,sys,uuid
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_PUBLIC_VIEW_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,demo_generation
 from app.web_publication_view import mount_publication_view
 db=tmp_path/'pub.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','T','O',academic_suite=True);bundle=demo_generation.generate_demo(conn,cam['id']);version=next(v for v in bundle['versions'] if v['format']=='linkedin');app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_publication_view(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,version,bundle
 conn.close();sys.path.remove(str(root))
def test_read_empty_never_writes(ctx):
 c,db,cam,v,b=ctx;r=c.get('/api/campaigns/'+cam['id']+'/publications');assert r.status_code==200;data=r.json();assert data['records']==data['notes']==[];assert len(data['versions'])==5 and all(x['format']!='email' for x in data['versions']);assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0

def test_read_exact_history_and_notes_isolated(ctx):
 c,db,cam,v,b=ctx;from app.distribution import record_publication
 from app.followup import add_followup,correct_distribution
 old=record_publication(db,cam['id'],v['id'],'linkedin','2026-10-25T12:00:00+00:00',str(uuid.uuid4()),confirmed=True)
 add_followup(db,cam['id'],'note','Reacción manual','2026-10-25T13:00:00+00:00',distribution_id=old['id'],event_id=str(uuid.uuid4()))
 corrected=correct_distribution(db,old['id'],str(uuid.uuid4()),'Fecha corregida',{'occurred_at':'2026-10-24T12:00:00+00:00'},confirmed=True)
 data=c.get('/api/campaigns/'+cam['id']+'/publications').json();assert {r['id'] for r in data['records']}=={old['id'],corrected['id']};assert len(data['notes'])==1
 from app.campaigns import create_campaign
 other=create_campaign(db,'Otra','T','O');assert c.get('/api/campaigns/'+other['id']+'/publications').json()['records']==[]

def test_auth_unknown_campaign(ctx):
 c,db,cam,v,b=ctx;assert c.get('/api/campaigns/missing/publications').status_code==400;c.headers.pop('X-Test-Auth');assert c.get('/api/campaigns/'+cam['id']+'/publications').status_code==401
