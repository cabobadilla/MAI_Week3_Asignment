import os,sys,uuid,json,hashlib
from pathlib import Path
import pytest
from fastapi import FastAPI,Request,HTTPException
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_EXPORT_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,demo_generation,approval,versions
 from app.web_export import mount_export
 db=tmp_path/'api.sqlite';out=tmp_path/'exports';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(db);cam=campaigns.create_campaign(conn,'Demo','Tema','Objetivo',academic_suite=True);b=demo_generation.generate_demo(conn,cam['id']);a=approval.approve_bundle(conn,cam['id'],[v['id'] for v in b['versions']],b['source_hash'],b['context_hash'],run_id=b['run']['id'],expected_config_revision=cam['config_revision']);app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_export(app,db,out)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as client:yield client,conn,cam,b,a,out,versions,tmp_path
 conn.close();sys.path.remove(str(root))
def post(c,a,operation=None):return c.post('/api/approvals/'+a['id']+'/exports',json={'operation_id':operation or str(uuid.uuid4())})
def test_unapproved_cannot_export(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;r=c.post('/api/approvals/missing/exports',json={'operation_id':str(uuid.uuid4())});assert r.status_code==400;assert db.execute('SELECT count(*) FROM export_record').fetchone()[0]==0;assert list(out.rglob('*.md'))==[]
def test_export_download_exact_manifest_and_no_distribution(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;r=post(c,a);assert r.status_code==200;x=r.json();assert len(x['files'])==6
 for item in x['files']:
  d=c.get(item['download_url']);assert d.status_code==200;assert hashlib.sha256(d.content).hexdigest()==item['sha256'];assert 'DEMO' in d.text;assert 'attachment' in d.headers['content-disposition'];assert (out/item['relative_path']).read_bytes()==d.content
 assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0
def test_retry_export_idempotent(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;op=str(uuid.uuid4());one=post(c,a,op);two=post(c,a,op);assert one.status_code==two.status_code==200 and one.json()['id']==two.json()['id'];assert db.execute('SELECT count(*) FROM export_record').fetchone()[0]==1
def test_edit_does_not_sneak_new_body_through_old_approval(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;v.edit_version(db,b['versions'][0]['id'],'UNAPPROVED-NEW-CONTENT');r=post(c,a);assert r.status_code==200
 for item in r.json()['files']:assert 'UNAPPROVED-NEW-CONTENT' not in c.get(item['download_url']).text
def test_corrupted_artifact_rejected(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;x=post(c,a).json();f=x['files'][0];(out/f['relative_path']).write_bytes(b'changed');assert c.get(f['download_url']).status_code==400
def test_symlink_cannot_read_outside_artifact(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;x=post(c,a).json();f=x['files'][0];outside=tmp/'outside-test.txt';outside.write_text('SYNTHETIC-SECRET-MUST-NOT-RETURN');p=out/f['relative_path'];p.unlink();p.symlink_to(outside);r=c.get(f['download_url']);assert r.status_code==400 and 'SYNTHETIC-SECRET' not in r.text
def test_invalid_index_and_untrusted_root_payload(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;x=post(c,a).json();assert c.get('/api/exports/'+x['id']+'/files/-1').status_code==400;assert c.get('/api/exports/'+x['id']+'/files/99').status_code==400;r=c.post('/api/approvals/'+a['id']+'/exports',json={'operation_id':str(uuid.uuid4()),'output_root':'/tmp/forbidden'});assert r.status_code==400
def test_auth_required_on_download(ctx):
 c,db,cam,b,a,out,v,tmp=ctx;x=post(c,a).json();c.headers.pop('X-Test-Auth');assert c.get(x['files'][0]['download_url']).status_code==401;assert post(c,a).status_code==401
