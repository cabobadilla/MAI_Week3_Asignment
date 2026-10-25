import os,sys,uuid,json
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_RECIPIENTS_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,organizations,companies,versions,distribution
 from app.web_recipients import mount_recipients
 db=tmp_path/'recipients.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','T','O',academic_suite=True);orgs=[organizations.save_organization(conn,'Org '+str(i),[{'name':'Persona '+str(j),'email':f'p{i}{j}@example.test'} for j in range(2)],roles=['aportante'] if i==0 else ['beneficiaria']) for i in range(2)];contacts=[ct for org in orgs for ct in org['contacts']];app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_recipients(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,orgs,contacts,companies,versions,distribution,organizations
 conn.close();sys.path.remove(str(root))
def select(c,cam,ids):return c.post('/api/campaigns/'+cam['id']+'/recipients',json={'contact_ids':ids})
def test_many_org_contacts_selection_no_delivery(ctx):
 c,db,cam,orgs,cts,co,v,d,o=ctx;r=select(c,cam,[x['id'] for x in cts]);assert r.status_code==200 and len(r.json())==4;assert {x['snapshot']['company_id'] for x in r.json()}=={x['id'] for x in orgs};assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0
def test_repeat_selection_reuses_frozen_ids(ctx):
 c,db,cam,orgs,cts,co,v,d,o=ctx;ids=[x['id'] for x in cts[:2]];a=select(c,cam,ids).json();b=select(c,cam,ids).json();assert [x['id'] for x in a]==[x['id'] for x in b];assert db.execute('SELECT count(*) FROM campaign_recipient').fetchone()[0]==2
def test_bad_or_duplicate_contact_rolls_back_selection(ctx):
 c,db,cam,orgs,cts,co,v,d,o=ctx
 for ids in [[cts[0]['id'],'missing'],[cts[0]['id'],cts[0]['id']],[]]:assert select(c,cam,ids).status_code==400
 assert db.execute('SELECT count(*) FROM campaign_recipient').fetchone()[0]==0
def test_duplicate_email_across_orgs_rejected_atomically(ctx):
 c,db,cam,orgs,cts,co,v,d,o=ctx;other=co.create_contact(db,orgs[1]['id'],cts[0]['email'],'Duplicado');assert select(c,cam,[cts[0]['id'],other['id']]).status_code==400;assert db.execute('SELECT count(*) FROM campaign_recipient').fetchone()[0]==0
def test_changed_email_preserves_old_sent_snapshot_and_can_restore(ctx):
 c,db,cam,orgs,cts,co,v,d,o=ctx;ct=cts[0];old=select(c,cam,[ct['id']]).json()[0];ver=v.create_version(db,cam['id'],'email','DEMO email general');sent=d.record_email_batch(db,cam['id'],ver['id'],[old['id']],'2026-10-25T12:00:00+00:00',str(uuid.uuid4()),confirmed=True)[0];co.update_contact(db,ct['id'],email='new@example.test');r=select(c,cam,[ct['id']]);assert r.status_code==200;new=r.json()[0];assert new['id']!=old['id'] and new['snapshot']['email']=='new@example.test';raw=db.execute('SELECT snapshot_json,archived_at FROM campaign_recipient WHERE id=?',(old['id'],)).fetchone();assert json.loads(raw[0])['email']==ct['email'] and raw[1];assert json.loads(db.execute('SELECT destination_snapshot_json FROM distribution_record WHERE id=?',(sent['id'],)).fetchone()[0])['email']==ct['email'];co.update_contact(db,ct['id'],email=ct['email']);restored=select(c,cam,[ct['id']]);assert restored.status_code==200 and restored.json()[0]['id']==old['id'];assert db.execute('SELECT count(*) FROM campaign_recipient').fetchone()[0]==2 and db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==1
def test_auth_and_unknown_fields(ctx):
 c,db,cam,orgs,cts,co,v,d,o=ctx;url='/api/campaigns/'+cam['id']+'/recipients';assert c.post(url,json={'contact_ids':[cts[0]['id']],'snapshot':{}}).status_code==400;c.headers.pop('X-Test-Auth');assert c.get(url).status_code==405;assert select(c,cam,[cts[0]['id']]).status_code==401
