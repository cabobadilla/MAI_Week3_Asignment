import os,sys,uuid,json
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_DIRECTED_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,organizations,recipients,demo_generation,companies
 from app.web_directed import mount_directed
 db=tmp_path/'directed.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','T','O',academic_suite=True);orgs=[organizations.save_organization(conn,'Org '+str(i),[{'name':'Persona','email':f'p{i}@example.test'}],roles=['aportante']) for i in range(2)];targets=[recipients.add_recipient(conn,cam['id'],o['contacts'][0]['id']) for o in orgs];bundle=demo_generation.generate_demo(conn,cam['id']);email=next(v for v in bundle['versions'] if v['format']=='email');app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_directed(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,orgs,targets,bundle,email,companies
 conn.close();sys.path.remove(str(root))
def payload(e,targets,**kw):
 p={'version_id':e['id'],'recipient_ids':[r['id'] for r in targets],'occurred_at':'2026-10-25T12:00:00+00:00','operation_id':str(uuid.uuid4()),'confirmed':True};p.update(kw);return p
def test_confirmed_batch_only_registers_external_facts(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/directed';assert c.post(url,json=payload(e,targets,confirmed=False)).status_code==400;r=c.post(url,json=payload(e,targets));assert r.status_code==200;rows=r.json();assert len(rows)==2 and len({x['batch_id'] for x in rows})==1 and all(x['batch_size']==2 for x in rows);assert all(x['kind']=='email_sent' for x in rows);assert db.execute('SELECT count(*) FROM followup_event').fetchone()[0]==0;assert db.execute('SELECT count(*) FROM export_record').fetchone()[0]==0
def test_retry_reordered_is_idempotent(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/directed';p=payload(e,targets);a=c.post(url,json=p);p['recipient_ids'].reverse();z=c.post(url,json=p);assert a.status_code==z.status_code==200 and {x['id'] for x in a.json()}=={x['id'] for x in z.json()};assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==2
def test_retry_after_contact_edit_preserves_original_snapshot(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/directed';p=payload(e,targets);a=c.post(url,json=p).json();co.update_contact(db,orgs[0]['contacts'][0]['id'],email='new@example.test');z=c.post(url,json=p);assert z.status_code==200 and {x['id'] for x in z.json()}=={x['id'] for x in a};snap=[json.loads(x['destination_snapshot_json']) for x in z.json()];assert any(x['email']=='p0@example.test' for x in snap)
def test_bad_target_or_format_rolls_back_whole_batch(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/directed';p=payload(e,targets);p['recipient_ids'].append('missing');assert c.post(url,json=p).status_code==400;li=next(v for v in b['versions'] if v['format']=='linkedin');assert c.post(url,json=payload(li,targets)).status_code==400;assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0
def test_no_forged_contact_or_actor_payload(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;url='/api/campaigns/'+cam['id']+'/directed';p=payload(e,targets);p['actor']='other';assert c.post(url,json=p).status_code==400;p=payload(e,targets);p['contact_ids']=['fake'];assert c.post(url,json=p).status_code==400
def test_auth_gate(ctx):
 c,db,cam,orgs,targets,b,e,co=ctx;c.headers.pop('X-Test-Auth');url='/api/campaigns/'+cam['id']+'/directed';assert c.get(url).status_code==405;assert c.post(url,json=payload(e,targets)).status_code==401
