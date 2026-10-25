import os,sys,json,hashlib,sqlite3
from pathlib import Path
import pytest

@pytest.fixture
def db(tmp_path):
 root=Path(os.environ.get('GWA_VERSION_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,versions,approval
 path=tmp_path/'content.sqlite';storage.initialize(path,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));conn=storage.connect(path)
 cam=campaigns.create_campaign(conn,'Title','Topic','Goal',formats=['email'])
 yield conn,campaigns,versions,approval,cam
 conn.close();sys.path.remove(str(root))

def version(db,body='General sample draft'):
 c,ca,v,a,cam=db;return v.create_version(c,cam['id'],'email',body)

def approve(db,ids,**kw):
 c,ca,v,a,cam=db;return a.approve_bundle(c,cam['id'],ids,'0'*64,'1'*64,**kw)

def test_version_hash(db):
 c,ca,v,a,cam=db;x=version(db);assert x['content_hash']==hashlib.sha256(x['body'].encode()).hexdigest();assert x['revision_no']==1

def test_edit_preserves_original(db):
 c,ca,v,a,cam=db;x=version(db);y=v.edit_version(c,x['id'],'Edited');assert y['id']!=x['id'] and y['revision_no']==2 and y['parent_version_id']==x['id'];assert v.get_version(c,x['id'])['body']=='General sample draft'

def test_db_content_immutable(db):
 c,ca,v,a,cam=db;x=version(db)
 with pytest.raises(sqlite3.IntegrityError):c.execute('UPDATE content_version SET body=? WHERE id=?',('bad',x['id']))

def test_missing_and_unknown_formats(db):
 c,ca,v,a,cam=db
 for fmt,body in [('fax','body'),('email','  ')]:
  with pytest.raises(ValueError):v.create_version(c,cam['id'],fmt,body)

def test_cross_campaign_parent_rejected(db):
 c,ca,v,a,cam=db;x=version(db);other=ca.create_campaign(c,'Other','Topic','Goal',formats=['email'])
 with pytest.raises(ValueError):v.create_version(c,other['id'],'email','B',parent_version_id=x['id'])

def test_parent_piece_identity(db):
 c,ca,v,a,cam=db;x=version(db)
 with pytest.raises(ValueError):v.create_version(c,cam['id'],'article','B',parent_version_id=x['id'])

def test_approval_exact_manifest(db):
 c,ca,v,a,cam=db;x=version(db);approved=approve(db,[x['id']]);assert len(approved['revision_hash'])==64;assert a.approval_covers(c,approved['id'],[x['id']]) is True
 y=v.edit_version(c,x['id'],'New text');assert a.approval_covers(c,approved['id'],[y['id']]) is False;assert a.approval_covers(c,approved['id'],[x['id']]) is True

def test_no_empty_or_duplicate_approval(db):
 x=version(db)
 for ids in [[],[x['id'],x['id']]]:
  with pytest.raises(ValueError):approve(db,ids)

def test_missing_selected_format_blocks(db):
 c,ca,v,a,cam=db;ca.update_campaign(c,cam['id'],formats=['email','linkedin']);x=version(db)
 with pytest.raises(ValueError):approve(db,[x['id']])

def test_unresolved_material_issue_blocks(db):
 x=version(db)
 with pytest.raises(ValueError):approve(db,[x['id']],unresolved_material_issues=['unbacked claim'])

def test_cross_campaign_bundle_blocks(db):
 c,ca,v,a,cam=db;other=ca.create_campaign(c,'Other','T','G',formats=['email']);x=v.create_version(c,other['id'],'email','body')
 with pytest.raises(ValueError):approve(db,[x['id']])

def test_stale_config_blocks(db):
 c,ca,v,a,cam=db;x=version(db);ca.update_campaign(c,cam['id'],objective='changed')
 with pytest.raises(ValueError):approve(db,[x['id']],expected_config_revision=1)

def test_approval_does_not_distribute(db):
 c,ca,v,a,cam=db;x=version(db);approve(db,[x['id']]);assert c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0;assert c.execute('SELECT count(*) FROM export_record').fetchone()[0]==0

def test_external_text_not_falsely_approved(db):
 c,ca,v,a,cam=db;x=v.create_version(c,cam['id'],'email','External exact copy',origin='manual_external');assert x['origin']=='manual_external';assert c.execute('SELECT count(*) FROM approval').fetchone()[0]==0

@pytest.mark.parametrize('hashval',['short','x'*64])
def test_bad_provenance_hash_rejected(db,hashval):
 c,ca,v,a,cam=db;x=version(db)
 with pytest.raises(ValueError):a.approve_bundle(c,cam['id'],[x['id']],hashval,'1'*64)

def test_approval_rows_immutable(db):
 c,ca,v,a,cam=db;x=version(db);ap=approve(db,[x['id']])
 with pytest.raises(sqlite3.IntegrityError):c.execute('DELETE FROM approval WHERE id=?',(ap['id'],))
