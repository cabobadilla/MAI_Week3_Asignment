import os,sys,json,sqlite3
from pathlib import Path
import pytest

@pytest.fixture
def db(tmp_path):
 root=Path(os.environ.get('GWA_FOLLOWUP_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,companies,campaigns,recipients,versions,distribution,followup
 p=tmp_path/'followup.sqlite';storage.initialize(p,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));c=storage.connect(p);cam=campaigns.create_campaign(c,'Synthetic','Topic','Goal',formats=['email']);co=companies.create_company(c,'Synthetic Co');ct=companies.create_contact(c,co['id'],'one@example.invalid');r=recipients.add_recipient(c,cam['id'],ct['id']);v=versions.create_version(c,cam['id'],'email','Common body');sent=distribution.record_email_batch(c,cam['id'],v['id'],[r['id']],'2026-10-24T12:30:00+00:00','original',confirmed=True)[0]
 yield c,companies,campaigns,recipients,versions,distribution,followup,cam,r,v,sent
 c.close();sys.path.remove(str(root))

def note(db,**kw):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;return fo.add_followup(c,cam['id'],'note','Synthetic note','2026-10-24T13:30:00+00:00',**kw)

def correct(db,changes=None,**kw):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;args=dict(confirmed=True);args.update(kw);return fo.correct_distribution(c,sent['id'],'fix1','Operator corrects typo',changes or {'occurred_at':'2026-10-24T11:30:00+00:00'},**args)

def test_manual_response_associated_coherently(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;x=fo.add_followup(c,cam['id'],'response','User reported reply','2026-10-24T13:30:00+00:00',distribution_id=sent['id']);assert x['campaign_recipient_id']==r['id'] and x['distribution_id']==sent['id'];assert len(di.list_distributions(c,cam['id']))==1

def test_note_without_distribution_does_not_invent_link(db):
 x=note(db);assert x['distribution_id'] is None and x['campaign_recipient_id'] is None

def test_next_step_is_only_local_note(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;x=fo.add_followup(c,cam['id'],'next_step','Review next week','2026-10-24T13:30:00+00:00',due_at='2026-10-31T12:00:00+00:00');assert x['due_at'] and c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==1

def test_due_date_requires_next_step(db):
 with pytest.raises(ValueError):note(db,due_at='2026-10-31T12:00:00+00:00')

@pytest.mark.parametrize('kind,body',[('send','body'),('note','  ')])
def test_kind_and_body_validation(db,kind,body):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db
 with pytest.raises(ValueError):fo.add_followup(c,cam['id'],kind,body,'2026-10-24T13:30:00+00:00')

def test_cross_campaign_distribution_rejected(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;other=ca.create_campaign(c,'Other','Topic','Goal',formats=['email'])
 with pytest.raises(ValueError):fo.add_followup(c,other['id'],'note','body','2026-10-24T13:30:00+00:00',distribution_id=sent['id'])

def test_mismatched_recipient_rejected(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;company=co.create_company(c,'Other');ct=co.create_contact(c,company['id'],'two@example.invalid');r2=re.add_recipient(c,cam['id'],ct['id'])
 with pytest.raises(ValueError):fo.add_followup(c,cam['id'],'note','body','2026-10-24T13:30:00+00:00',distribution_id=sent['id'],campaign_recipient_id=r2['id'])

def test_followup_correction_preserves_original(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;x=note(db);y=fo.correct_followup(c,x['id'],'Correct note',body='Revised note');assert y['supersedes_id']==x['id'];assert c.execute('SELECT body FROM followup_event WHERE id=?',(x['id'],)).fetchone()[0]=='Synthetic note';assert [x['id'] for x in fo.list_followups(c,cam['id'])]==[y['id']];assert len(fo.list_followups(c,cam['id'],include_superseded=True))==2

def test_followup_only_one_correction_branch(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;x=note(db);fo.correct_followup(c,x['id'],'Correct note',body='Revised')
 with pytest.raises(ValueError):fo.correct_followup(c,x['id'],'Other branch',body='Other')

def test_distribution_correction_requires_confirmed(db):
 with pytest.raises(ValueError):correct(db,confirmed=False)
 assert db[0].execute('SELECT count(*) FROM distribution_record').fetchone()[0]==1

def test_distribution_correction_preserves_audit_and_current_projection(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;x=correct(db);assert x['supersedes_id']==sent['id'] and x['correction_reason']=='Operator corrects typo';old=c.execute('SELECT * FROM distribution_record WHERE id=?',(sent['id'],)).fetchone();assert old['occurred_at']=='2026-10-24T12:30:00+00:00';assert [i['id'] for i in di.list_distributions(c,cam['id'])]==[x['id']];assert len(di.list_distributions(c,cam['id'],include_superseded=True))==2

def test_distribution_correction_retry_idempotent(db):
 x=correct(db);y=correct(db);assert x['id']==y['id'] and db[0].execute('SELECT count(*) FROM distribution_record').fetchone()[0]==2

def test_distribution_correction_operation_collision(db):
 correct(db)
 with pytest.raises(ValueError):correct(db,{'occurred_at':'2026-10-23T11:30:00+00:00'})

def test_cannot_branch_superseded_record(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;correct(db)
 with pytest.raises(ValueError):fo.correct_distribution(c,sent['id'],'other-fix','Another correction',{'occurred_at':'2026-10-22T11:30:00+00:00'},confirmed=True)

def test_correction_chain_allowed_from_current(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;x=correct(db);y=fo.correct_distribution(c,x['id'],'fix2','Second correction',{'occurred_at':'2026-10-22T11:30:00+00:00'},confirmed=True);assert y['supersedes_id']==x['id'];assert len(di.list_distributions(c,cam['id']))==1 and len(di.list_distributions(c,cam['id'],include_superseded=True))==3

def test_correction_rejects_unknown_or_campaign_changes(db):
 with pytest.raises(ValueError):correct(db,{'campaign_id':'different'})
 with pytest.raises(ValueError):correct(db,{'kind':'publication'})

def test_correction_cannot_move_version_across_campaigns(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;other=ca.create_campaign(c,'Other','Topic','Goal',formats=['email']);new=ve.create_version(c,other['id'],'email','Other body')
 with pytest.raises(ValueError):correct(db,{'content_version_id':new['id']})

def test_followup_history_campaign_isolation(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;note(db);other=ca.create_campaign(c,'Other','Topic','Goal',formats=['email']);assert fo.list_followups(c,other['id'])==[]

def test_immutable_followup_rows(db):
 c=db[0];x=note(db)
 with pytest.raises(sqlite3.IntegrityError):c.execute('UPDATE followup_event SET body=? WHERE id=?',('bad',x['id']))

def test_correction_preserves_destination_after_contact_archival(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;row=c.execute('SELECT contact_id FROM campaign_recipient WHERE id=?',(r['id'],)).fetchone();co.archive_contact(c,row['contact_id']);x=correct(db);assert x['destination_snapshot_json']==sent['destination_snapshot_json']

def test_correction_requires_reason(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db
 with pytest.raises(ValueError):fo.correct_distribution(c,sent['id'],'fix1',' ',{'occurred_at':'2026-10-24T11:30:00+00:00'},confirmed=True)
 assert c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==1

def test_followup_invalid_timestamp_rejected(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db
 with pytest.raises(ValueError):fo.add_followup(c,cam['id'],'note','body','2026-10-24')

def test_publication_correction_cannot_add_recipient(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;pubv=ve.create_version(c,cam['id'],'linkedin','Public sample');pub=di.record_publication(c,cam['id'],pubv['id'],'linkedin','2026-10-24T12:30:00+00:00','pub',confirmed=True)
 with pytest.raises(ValueError):fo.correct_distribution(c,pub['id'],'pubfix','Wrong destination',{'campaign_recipient_id':r['id']},confirmed=True)


def test_correction_sql_failure_preserves_outer_transaction(db):
 c,co,ca,re,ve,di,fo,cam,r,v,sent=db;c.execute('BEGIN IMMEDIATE');c.execute("INSERT INTO company(id,name,notes,created_at) VALUES('outer-fixture','Outer preserved','','now')");c.execute("CREATE TEMP TRIGGER force_correction_error BEFORE INSERT ON distribution_record BEGIN SELECT RAISE(ABORT,'synthetic correction failure'); END")
 with pytest.raises((ValueError,sqlite3.IntegrityError)):correct(db)
 assert c.execute("SELECT count(*) FROM company WHERE id='outer-fixture'").fetchone()[0]==1 and c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==1;c.rollback()
