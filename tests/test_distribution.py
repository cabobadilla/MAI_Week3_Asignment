import os,sys,json,sqlite3
from pathlib import Path
import pytest

@pytest.fixture
def db(tmp_path):
 root=Path(os.environ.get('GWA_DISTRIBUTION_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,companies,campaigns,recipients,versions,distribution
 p=tmp_path/'records.sqlite';storage.initialize(p,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));c=storage.connect(p)
 cam=campaigns.create_campaign(c,'Synthetic','Topic','Goal',formats=['email']);co=companies.create_company(c,'Synthetic Co');ct1=companies.create_contact(c,co['id'],'one@example.invalid');ct2=companies.create_contact(c,co['id'],'two@example.invalid');rs=[recipients.add_recipient(c,cam['id'],x['id']) for x in [ct1,ct2]];v=versions.create_version(c,cam['id'],'email','Common unapproved external draft')
 yield c,companies,campaigns,recipients,versions,distribution,cam,co,[ct1,ct2],rs,v
 c.close();sys.path.remove(str(root))

def record(db,**kw):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;args=dict(confirmed=True);args.update(kw)
 return di.record_email_batch(c,cam['id'],v['id'],[x['id'] for x in rs],'2026-10-24T12:30:00+00:00','op1',**args)

def count(c):return c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]

def test_preview_never_records(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;p=di.preview_email_batch(c,cam['id'],v['id'],[x['id'] for x in rs]);assert len(p['recipients'])==2;assert count(c)==0

def test_requires_explicit_declaration(db):
 with pytest.raises(ValueError):record(db,confirmed=False)
 assert count(db[0])==0

def test_batch_exact_version_and_snapshots(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;rows=record(db);assert len(rows)==2 and count(c)==2;assert len({x['batch_id'] for x in rows})==1
 for row,r in zip(sorted(rows,key=lambda x:x['campaign_recipient_id']),sorted(rs,key=lambda x:x['id'])):
  assert row['campaign_id']==cam['id'] and row['content_version_id']==v['id'] and row['kind']=='email_sent' and row['channel']=='email' and row['batch_size']==2
  assert json.loads(row['destination_snapshot_json'])==r['snapshot']
 assert c.execute('SELECT count(*) FROM approval').fetchone()[0]==0

def test_retry_idempotent_even_order_changed(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;a=record(db);b=di.record_email_batch(c,cam['id'],v['id'],[x['id'] for x in reversed(rs)],'2026-10-24T12:30:00+00:00','op1',confirmed=True);assert {x['id'] for x in a}=={x['id'] for x in b};assert count(c)==2

def test_retry_different_payload_rejected(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;record(db)
 with pytest.raises(ValueError):di.record_email_batch(c,cam['id'],v['id'],[rs[0]['id']],'2026-10-24T12:30:00+00:00','op1',confirmed=True)
 assert count(c)==2

def test_cross_campaign_recipient_rolls_back_all(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;other=ca.create_campaign(c,'Other','Topic','Goal',formats=['email']);r=re.add_recipient(c,other['id'],cts[0]['id'])
 with pytest.raises(ValueError):di.record_email_batch(c,cam['id'],v['id'],[rs[0]['id'],r['id']],'2026-10-24T12:30:00+00:00','op1',confirmed=True)
 assert count(c)==0

def test_sql_failure_rolls_back_entire_batch(db):
 c=db[0];c.execute("CREATE TEMP TRIGGER force_batch_error BEFORE INSERT ON distribution_record WHEN (SELECT count(*) FROM distribution_record)>0 BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
 with pytest.raises((ValueError,sqlite3.IntegrityError)):record(db)
 assert count(c)==0

def test_duplicate_recipient_list_rejected(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db
 with pytest.raises(ValueError):di.record_email_batch(c,cam['id'],v['id'],[rs[0]['id'],rs[0]['id']],'2026-10-24T12:30:00+00:00','op1',confirmed=True)
 assert count(c)==0

def test_empty_recipient_list_rejected(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db
 with pytest.raises(ValueError):di.record_email_batch(c,cam['id'],v['id'],[],'2026-10-24T12:30:00+00:00','op1',confirmed=True)

def test_archived_recipient_blocks(db):
 re=db[3];re.archive_recipient(db[0],db[9][0]['id'])
 with pytest.raises(ValueError):record(db)
 assert count(db[0])==0

def test_archived_company_blocks(db):
 db[1].archive_company(db[0],db[7]['id'])
 with pytest.raises(ValueError):record(db)
 assert count(db[0])==0

def test_changed_contact_email_requires_reselection(db):
 db[1].update_contact(db[0],db[8][0]['id'],email='changed@example.invalid')
 with pytest.raises(ValueError):record(db)
 assert count(db[0])==0

def test_repeat_requires_reason(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;record(db)
 with pytest.raises(ValueError):di.record_email_batch(c,cam['id'],v['id'],[rs[0]['id']],'2026-10-25T12:30:00+00:00','op2',confirmed=True)
 assert count(c)==2

def test_confirmed_repeat_has_new_rows_and_warning(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;record(db);p=di.preview_email_batch(c,cam['id'],v['id'],[rs[0]['id']]);assert p['warnings'];rows=di.record_email_batch(c,cam['id'],v['id'],[rs[0]['id']],'2026-10-25T12:30:00+00:00','op2',confirmed=True,repeat_reason='Operator declared real repeat');assert len(rows)==1 and count(c)==3

def test_publication_no_fictional_recipient(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;pub=ve.create_version(c,cam['id'],'linkedin','General public body');row=di.record_publication(c,cam['id'],pub['id'],'linkedin','2026-10-24T12:30:00+00:00','pub1',confirmed=True,public_url='https://example.invalid/post');assert row['campaign_recipient_id'] is None and row['kind']=='publication' and count(c)==1

def test_publication_cannot_use_email_channel(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db
 with pytest.raises(ValueError):di.record_publication(c,cam['id'],v['id'],'email','2026-10-24T12:30:00+00:00','pub1',confirmed=True)
 assert count(c)==0

def test_publication_retry_idempotent(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;pub=ve.create_version(c,cam['id'],'linkedin','Public draft');args=(c,cam['id'],pub['id'],'linkedin','2026-10-24T12:30:00+00:00','pub1');a=di.record_publication(*args,confirmed=True);b=di.record_publication(*args,confirmed=True);assert a['id']==b['id'] and count(c)==1

@pytest.mark.parametrize('date',['bad','2026-10-24','2026-10-24T12:30:00'])
def test_aware_datetime_required(db,date):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db
 with pytest.raises(ValueError):di.record_email_batch(c,cam['id'],v['id'],[rs[0]['id']],date,'op1',confirmed=True)
 assert count(c)==0

def test_records_immutable(db):
 c=db[0];rows=record(db)
 with pytest.raises(sqlite3.IntegrityError):c.execute('DELETE FROM distribution_record WHERE id=?',(rows[0]['id'],))

def test_history_campaign_isolation(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;record(db);other=ca.create_campaign(c,'Other','Topic','Goal',formats=['email']);assert di.list_distributions(c,other['id'])==[] and len(di.list_distributions(c,cam['id']))==2

def test_retry_preserves_recorded_destination_after_contact_change(db):
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;old=record(db);co.update_contact(c,cts[0]['id'],email='new@example.invalid');same=record(db);assert {x['id'] for x in old}=={x['id'] for x in same} and count(c)==2

def test_batch_failure_inside_outer_transaction_is_atomic(db):
 c=db[0];c.execute('BEGIN IMMEDIATE');c.execute("INSERT INTO company(id,name,notes,created_at) VALUES('outer-fixture','Outer preserved','','now')")
 c.execute("CREATE TEMP TRIGGER force_nested_error BEFORE INSERT ON distribution_record WHEN (SELECT count(*) FROM distribution_record)>0 BEGIN SELECT RAISE(ABORT,'synthetic nested failure'); END")
 with pytest.raises((ValueError,sqlite3.IntegrityError)):record(db)
 assert count(c)==0 and c.execute("SELECT count(*) FROM company WHERE id='outer-fixture'").fetchone()[0]==1
 c.rollback()

def test_two_clicks_same_operation_create_only_one_batch(db):
 from concurrent.futures import ThreadPoolExecutor
 from threading import Barrier
 c,co,ca,re,ve,di,cam,company,cts,rs,v=db;path=c.execute('PRAGMA database_list').fetchone()['file'];barrier=Barrier(2)
 def click():
  from app import storage
  other=storage.connect(path)
  try:
   barrier.wait(timeout=3);return di.record_email_batch(other,cam['id'],v['id'],[x['id'] for x in rs],'2026-10-24T12:30:00+00:00','concurrent',confirmed=True)
  finally:other.close()
 with ThreadPoolExecutor(max_workers=2) as pool:
  fs=[pool.submit(click) for _ in range(2)];rows=[f.result(timeout=10) for f in fs]
 assert {x['id'] for x in rows[0]}=={x['id'] for x in rows[1]} and count(c)==2
