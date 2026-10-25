import os,sys,json,sqlite3,hashlib
from pathlib import Path
import pytest

@pytest.fixture
def db(tmp_path):
 root=Path(os.environ.get('GWA_EXPORT_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,versions,approval,export
 path=tmp_path/'export.sqlite';storage.initialize(path,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));c=storage.connect(path);cam=campaigns.create_campaign(c,'Title','Topic','Goal',formats=['email']);v=versions.create_version(c,cam['id'],'email','General sample draft');a=approval.approve_bundle(c,cam['id'],[v['id']],'0'*64,'1'*64)
 yield c,campaigns,versions,approval,export,cam,v,a,tmp_path/'outputs'
 c.close();sys.path.remove(str(root))

def test_approved_export_files_and_label(db):
 c,ca,v,a,e,cam,piece,approved,out=db;r=e.export_bundle(c,approved['id'],out,'op1');assert r['files']
 for item in r['files']:
  f=out/item['relative_path'];assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256']
 text='\n'.join((out/x['relative_path']).read_text() for x in r['files'] if Path(x['relative_path']).suffix in ['.md','.txt']);assert 'BORRADOR APROBADO PARA EXPORTACIÓN' in text and 'General sample draft' in text
 assert c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0

def test_retry_operation_idempotent(db):
 c,ca,v,a,e,cam,piece,approved,out=db;x=e.export_bundle(c,approved['id'],out,'op1');y=e.export_bundle(c,approved['id'],out,'op1');assert x['id']==y['id'];assert c.execute('SELECT count(*) FROM export_record').fetchone()[0]==1

def test_same_operation_different_payload_rejected(db):
 c,ca,v,a,e,cam,piece,approved,out=db;e.export_bundle(c,approved['id'],out,'op1')
 with pytest.raises(ValueError):e.export_bundle(c,approved['id'],out.parent/'other','op1')

def test_no_approval_no_files(db):
 c,ca,v,a,e,cam,piece,approved,out=db
 with pytest.raises(ValueError):e.export_bundle(c,'missing',out,'op1')
 assert not out.exists() and c.execute('SELECT count(*) FROM export_record').fetchone()[0]==0

def test_config_changed_no_new_export(db):
 c,ca,v,a,e,cam,piece,approved,out=db;ca.update_campaign(c,cam['id'],objective='Changed')
 with pytest.raises(ValueError):e.export_bundle(c,approved['id'],out,'op1')
 assert c.execute('SELECT count(*) FROM export_record').fetchone()[0]==0

def test_symlink_root_rejected(db):
 c,ca,v,a,e,cam,piece,approved,out=db;other=out.parent/'elsewhere';other.mkdir();out.symlink_to(other,target_is_directory=True)
 with pytest.raises(ValueError):e.export_bundle(c,approved['id'],out,'op1')
 assert list(other.iterdir())==[]

def test_symlink_nested_rejected(db):
 c,ca,v,a,e,cam,piece,approved,out=db;out.mkdir();other=out.parent/'elsewhere';other.mkdir();(out/cam['id']).symlink_to(other,target_is_directory=True)
 with pytest.raises(ValueError):e.export_bundle(c,approved['id'],out,'op1')
 assert list(other.iterdir())==[]

def test_existing_corrupt_file_not_overwritten(db):
 c,ca,v,a,e,cam,piece,approved,out=db;r=e.export_bundle(c,approved['id'],out,'op1');f=out/r['files'][0]['relative_path'];f.write_text('changed externally')
 with pytest.raises(ValueError):e.export_bundle(c,approved['id'],out,'op1')
 assert f.read_text()=='changed externally'

def test_output_file_not_directory_leaves_no_record(db):
 c,ca,v,a,e,cam,piece,approved,out=db;out.write_text('preserve')
 with pytest.raises((ValueError,OSError)):e.export_bundle(c,approved['id'],out,'op1')
 assert out.read_text()=='preserve' and c.execute('SELECT count(*) FROM export_record').fetchone()[0]==0

@pytest.mark.parametrize('operation',['','../bad'])
def test_operation_identifier_validation(db,operation):
 c,ca,v,a,e,cam,piece,approved,out=db
 with pytest.raises(ValueError):e.export_bundle(c,approved['id'],out,operation)

def test_db_failure_and_retry_recovers_without_duplicate(db):
 c,ca,v,a,e,cam,piece,approved,out=db
 c.execute("CREATE TEMP TRIGGER force_export_error BEFORE INSERT ON export_record BEGIN SELECT RAISE(ABORT,'synthetic export fault'); END")
 with pytest.raises((ValueError,sqlite3.IntegrityError)):e.export_bundle(c,approved['id'],out,'retry1')
 assert c.execute('SELECT count(*) FROM export_record').fetchone()[0]==0
 c.execute('DROP TRIGGER force_export_error');r=e.export_bundle(c,approved['id'],out,'retry1');assert r['files'];assert c.execute('SELECT count(*) FROM export_record').fetchone()[0]==1
 assert c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0

def test_symlink_ancestor_rejected(db):
 c,ca,v,a,e,cam,piece,approved,out=db;real=out.parent/'real';real.mkdir();link=out.parent/'link';link.symlink_to(real,target_is_directory=True)
 with pytest.raises(ValueError):e.export_bundle(c,approved['id'],link/'outputs','op1')
 assert list(real.iterdir())==[]

def test_edit_does_not_export_new_unapproved_text(db):
 c,ca,v,a,e,cam,piece,approved,out=db;v.edit_version(c,piece['id'],'New unapproved body');r=e.export_bundle(c,approved['id'],out,'op1');text='\n'.join((out/x['relative_path']).read_text() for x in r['files']);assert 'General sample draft' in text and 'New unapproved body' not in text
