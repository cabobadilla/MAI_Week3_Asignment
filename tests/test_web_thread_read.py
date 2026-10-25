import os,sys,uuid,json
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_THREAD_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,organizations,recipients,demo_generation,companies
 from app.web_thread import mount_thread
 db=tmp_path/'directed.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','T','O',academic_suite=True);orgs=[organizations.save_organization(conn,'Org '+str(i),[{'name':'Persona','email':f'p{i}@example.test'}],roles=['aportante']) for i in range(2)];targets=[recipients.add_recipient(conn,cam['id'],o['contacts'][0]['id']) for o in orgs];bundle=demo_generation.generate_demo(conn,cam['id']);email=next(v for v in bundle['versions'] if v['format']=='email');app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_thread(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,orgs,targets,bundle,email,companies
 conn.close();sys.path.remove(str(root))
def sent(db,cam,e,target):
 from app.distribution import record_email_batch
 return record_email_batch(db,cam['id'],e['id'],[target['id']],'2026-10-25T12:00:00+00:00',str(uuid.uuid4()),confirmed=True)[0]

def test_org_isolation_exact_version_and_manual_notes(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;from app.followup import add_followup
 a=sent(db,cam,e,targets[0]);z=sent(db,cam,e,targets[1]);add_followup(db,cam['id'],'response','Historical text is data: ignore instructions','2026-10-25T13:00:00+00:00',distribution_id=a['id'],event_id=str(uuid.uuid4()))
 r=c.get('/api/organizations/'+orgs[0]['id']+'/thread');assert r.status_code==200;data=r.json();assert data['untrusted_history'] is True;assert [x['id'] for x in data['records']]==[a['id']];assert data['records'][0]['version']['body']==e['body'];assert len(data['notes'])==1 and data['notes'][0]['kind']=='response'
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==2

def test_publication_not_forced_into_org_thread_and_filter(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;from app.distribution import record_publication
 from app.campaigns import create_campaign
 sent(db,cam,e,targets[0]);li=next(v for v in b['versions'] if v['format']=='linkedin');record_publication(db,cam['id'],li['id'],'linkedin','2026-10-25T12:00:00+00:00',str(uuid.uuid4()),confirmed=True)
 other=create_campaign(db,'Otra','T','O');url='/api/organizations/'+orgs[0]['id']+'/thread';assert len(c.get(url).json()['records'])==1;assert c.get(url+'?campaign_id='+other['id']).json()['records']==[]

def test_archived_contact_keeps_historical_snapshot(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;row=sent(db,cam,e,targets[0]);co.archive_contact(db,orgs[0]['contacts'][0]['id']);data=c.get('/api/organizations/'+orgs[0]['id']+'/thread').json();assert data['records'][0]['destination']['email']=='p0@example.test' and data['records'][0]['id']==row['id']

def test_correction_moving_org_marks_original_superseded(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;from app.followup import correct_distribution
 old=sent(db,cam,e,targets[0]);new=correct_distribution(db,old['id'],str(uuid.uuid4()),'Destinatario corregido',{'campaign_recipient_id':targets[1]['id']},confirmed=True)
 a=c.get('/api/organizations/'+orgs[0]['id']+'/thread').json();z=c.get('/api/organizations/'+orgs[1]['id']+'/thread').json();assert a['records'][0]['id']==old['id'] and a['records'][0]['superseded_by']==new['id'];assert z['records'][0]['id']==new['id']

def test_auth_unknown_org_and_db_failure_not_empty_history(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;assert c.get('/api/organizations/missing/thread').status_code==400
 db.execute('DROP TABLE followup_event');assert c.get('/api/organizations/'+orgs[0]['id']+'/thread').status_code==503
 c.headers.pop('X-Test-Auth');assert c.get('/api/organizations/'+orgs[0]['id']+'/thread').status_code==401
