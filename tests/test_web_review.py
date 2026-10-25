import os,sys
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_REVIEW_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,demo_generation,versions
 from app.web_review import mount_review
 db=tmp_path/'api.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','Tema','Objetivo',academic_suite=True);app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_review(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,campaigns,demo_generation,versions
 conn.close();sys.path.remove(str(root))
def payload(bundle,confirmed=True):return {'run_id':bundle['run']['id'],'version_ids':[v['id'] for v in bundle['versions']],'confirmed':confirmed}
def test_empty_review_is_not_generation(ctx):
 c,db,cam,ca,g,v=ctx;r=c.get('/api/campaigns/'+cam['id']+'/review');assert r.status_code==200;x=r.json();assert x['bundle'] is None and x['approval'] is None and x['exports']==[];assert db.execute('SELECT count(*) FROM generation_run').fetchone()[0]==0
def test_review_requires_human_confirmation(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);url='/api/campaigns/'+cam['id']+'/approvals';assert c.post(url,json=payload(b,False)).status_code==400;assert c.post(url,json=payload(b,'true')).status_code==400
 r=c.post(url,json=payload(b));assert r.status_code==200;a=r.json();assert len(a['manifest']['versions'])==6;assert a['source_hash']==b['source_hash'] and a['context_hash']==b['context_hash'];assert c.get('/api/campaigns/'+cam['id']+'/review').json()['approval']['id']==a['id']
 for t in ['export_record','distribution_record']:assert db.execute('SELECT count(*) FROM '+t).fetchone()[0]==0
def test_repeat_approval_idempotent(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);url='/api/campaigns/'+cam['id']+'/approvals';a=c.post(url,json=payload(b));again=c.post(url,json=payload(b));assert a.status_code==again.status_code==200 and a.json()['id']==again.json()['id'];assert db.execute('SELECT count(*) FROM approval').fetchone()[0]==1
def test_edit_appends_and_invalidates_current_approval(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);url='/api/campaigns/'+cam['id']+'/approvals';a=c.post(url,json=payload(b)).json();old=b['versions'][0];r=c.put('/api/versions/'+old['id'],json={'body':'DEMO editado por humano','expected_hash':old['content_hash']});assert r.status_code==200;new=r.json();assert new['id']!=old['id'] and new['parent_version_id']==old['id'];assert v.get_version(db,old['id'])['body']==old['body'];status=c.get('/api/campaigns/'+cam['id']+'/review').json();assert status['approval'] is None;assert c.post(url,json=payload(b)).status_code==400;assert c.post(url,json=payload(status['bundle'])).status_code==200;assert db.execute('SELECT count(*) FROM approval').fetchone()[0]==2
def test_wrong_hash_and_stale_edit_do_not_overwrite(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);old=b['versions'][0];url='/api/versions/'+old['id'];assert c.put(url,json={'body':'Nuevo','expected_hash':'0'*64}).status_code==400;assert c.put(url,json={'body':'Nuevo','expected_hash':old['content_hash']}).status_code==200;assert c.put(url,json={'body':'Obsoleto','expected_hash':old['content_hash']}).status_code==400;assert len(v.list_versions(db,cam['id']))==7
def test_cross_campaign_and_partial_bundle_rejected(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);other=ca.create_campaign(db,'Otra','T','O');assert c.post('/api/campaigns/'+other['id']+'/approvals',json=payload(b)).status_code==400;url='/api/campaigns/'+cam['id']+'/approvals';p=payload(b);p['version_ids']=p['version_ids'][:-1];assert c.post(url,json=p).status_code==400;assert c.post(url,json=dict(payload(b),source_hash='f'*64)).status_code==400;assert db.execute('SELECT count(*) FROM approval').fetchone()[0]==0
def test_changed_brief_blocks_approval(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);ca.update_campaign(db,cam['id'],objective='Cambió');assert c.post('/api/campaigns/'+cam['id']+'/approvals',json=payload(b)).status_code==400;assert db.execute('SELECT count(*) FROM approval').fetchone()[0]==0
def test_specific_run_cannot_move_campaign(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);other=ca.create_campaign(db,'Otra','T','O');assert c.get('/api/campaigns/'+other['id']+'/review',params={'run_id':b['run']['id']}).status_code==400
def test_read_after_new_connection_preserves_approval(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);a=c.post('/api/campaigns/'+cam['id']+'/approvals',json=payload(b)).json();one=c.get('/api/campaigns/'+cam['id']+'/review').json();two=c.get('/api/campaigns/'+cam['id']+'/review').json();assert one['approval']['id']==two['approval']['id']==a['id']
def test_unauthenticated_cannot_read_or_edit(ctx):
 c,db,cam,ca,g,v=ctx;b=g.generate_demo(db,cam['id']);c.headers.pop('X-Test-Auth');assert c.get('/api/campaigns/'+cam['id']+'/review').status_code==401;assert c.put('/api/versions/'+b['versions'][0]['id'],json={'body':'No','expected_hash':b['versions'][0]['content_hash']}).status_code==401
