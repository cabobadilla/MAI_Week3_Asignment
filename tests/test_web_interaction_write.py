import os,sys,uuid,json
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_INTERACTION_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,organizations,recipients,demo_generation,companies
 from app.web_interactions import mount_interactions
 db=tmp_path/'directed.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','T','O',academic_suite=True);orgs=[organizations.save_organization(conn,'Org '+str(i),[{'name':'Persona','email':f'p{i}@example.test'}],roles=['aportante']) for i in range(2)];targets=[recipients.add_recipient(conn,cam['id'],o['contacts'][0]['id']) for o in orgs];bundle=demo_generation.generate_demo(conn,cam['id']);email=next(v for v in bundle['versions'] if v['format']=='email');app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_interactions(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,orgs,targets,bundle,email,companies
 conn.close();sys.path.remove(str(root))
def payload(target,**kw):
 p={'kind':'note','body':'Nota manual sintética','occurred_at':'2026-10-25T12:00:00+00:00','event_id':str(uuid.uuid4()),'campaign_recipient_id':target['id']};p.update(kw);return p

def test_note_response_and_retry(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/interactions';p=payload(targets[0]);a=c.post(url,json=p);z=c.post(url,json=p);assert a.status_code==z.status_code==200 and a.json()['id']==z.json()['id'];assert c.post(url,json=payload(targets[0],kind='response')).status_code==200
 assert db.execute('SELECT count(*) FROM followup_event').fetchone()[0]==2
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0

def test_collision_does_not_append(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/interactions';p=payload(targets[0]);assert c.post(url,json=p).status_code==200;p['body']='Otra';assert c.post(url,json=p).status_code==400;assert db.execute('SELECT count(*) FROM followup_event').fetchone()[0]==1

def test_reject_crm_missing_reference_and_bad_event(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/interactions'
 for kw in [{'kind':'next_step'},{'due_at':'tomorrow'},{'actor':'forged'},{'campaign_recipient_id':None},{'event_id':None},{'event_id':'bad'},{'campaign_recipient_id':'missing'}]:assert c.post(url,json=payload(targets[0],**kw)).status_code==400
 assert db.execute('SELECT count(*) FROM followup_event').fetchone()[0]==0

def test_public_reaction_note_only_and_exact_distribution(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;from app.distribution import record_publication
 li=next(v for v in b['versions'] if v['format']=='linkedin');record=record_publication(db,cam['id'],li['id'],'linkedin','2026-10-25T12:00:00+00:00',str(uuid.uuid4()),confirmed=True)
 url='/api/campaigns/'+cam['id']+'/interactions';p=payload(targets[0],campaign_recipient_id=None,distribution_id=record['id']);assert c.post(url,json=p).status_code==200;p['event_id']=str(uuid.uuid4());p['kind']='response';assert c.post(url,json=p).status_code==400
 assert db.execute('SELECT count(*) FROM followup_event').fetchone()[0]==1

def test_campaign_isolation_and_auth(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;from app.campaigns import create_campaign
 other=create_campaign(db,'Other','T','O');assert c.post('/api/campaigns/'+other['id']+'/interactions',json=payload(targets[0])).status_code==400
 c.headers.pop('X-Test-Auth');assert c.post('/api/campaigns/'+cam['id']+'/interactions',json=payload(targets[0])).status_code==401
