import os,sys,json,sqlite3
from pathlib import Path
import pytest
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ.get('GWA_ORG_MIGRATION_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,companies,campaigns,recipients,versions,distribution
 p=tmp_path/'legacy.sqlite';schema=Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql')));storage.initialize(p,schema);c=storage.connect(p);co=companies.create_company(c,'Legacy Co');ct=companies.create_contact(c,co['id'],'legacy@example.invalid');cam=campaigns.create_campaign(c,'Legacy','Topic','Goal',formats=['email']);re=recipients.add_recipient(c,cam['id'],ct['id']);v=versions.create_version(c,cam['id'],'email','Legacy body');di=distribution.record_email_batch(c,cam['id'],v['id'],[re['id']],'2026-10-24T12:00:00+00:00','legacy',confirmed=True)[0];c.close();yield storage,p,schema,co,ct,cam,re,v,di
 sys.path.remove(str(root))
def snapshot(c):
 out={}
 for table in ['contact','campaign','campaign_recipient','content_version','distribution_record']:
  out[table]=[dict(x) for x in c.execute('SELECT * FROM '+table+' ORDER BY id')]
 return out

def test_migrate_preserves_ids_contacts_history(ctx):
 st,p,schema,co,ct,cam,re,v,di=ctx;c=st.connect(p);before=snapshot(c);c.close();st.initialize(p,schema,organizations=True);c=st.connect(p)
 try:
  assert c.execute('PRAGMA user_version').fetchone()[0]==2;assert snapshot(c)==before;row=dict(c.execute('SELECT * FROM company WHERE id=?',(co['id'],)).fetchone());assert json.loads(row['roles_json'])==['aportante'] and row['name']=='Legacy Co';assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
 finally:c.close()

def test_migration_retry_is_idempotent_and_base_initializer_accepts_v2(ctx):
 st,p,schema,*_=ctx;st.initialize(p,schema,organizations=True);st.initialize(p,schema,organizations=True);st.initialize(p,schema);c=st.connect(p)
 try:assert c.execute('PRAGMA user_version').fetchone()[0]==2 and c.execute('SELECT count(*) FROM company').fetchone()[0]==1
 finally:c.close()

def test_fresh_target_v2_and_legacy_default_v1(ctx,tmp_path):
 st,p,schema,*_=ctx;new=tmp_path/'new.sqlite';st.initialize(new,schema,organizations=True);c=st.connect(new)
 try:assert c.execute('PRAGMA user_version').fetchone()[0]==2 and 'roles_json' in {x['name'] for x in c.execute('PRAGMA table_info(company)')}
 finally:c.close()
 legacy=tmp_path/'base.sqlite';st.initialize(legacy,schema);c=st.connect(legacy)
 try:assert c.execute('PRAGMA user_version').fetchone()[0]==1
 finally:c.close()

@pytest.mark.parametrize('roles',[[],['unknown'],['aportante','aportante'],['aportante','beneficiaria','other']])
def test_invalid_role_shapes_rejected_by_db(ctx,roles):
 st,p,schema,co,*_=ctx;st.initialize(p,schema,organizations=True);c=st.connect(p)
 try:
  with pytest.raises(sqlite3.IntegrityError):c.execute('UPDATE company SET roles_json=? WHERE id=?',(json.dumps(roles),co['id']))
 finally:c.close()

def test_both_roles_can_be_represented_without_duplicate_organization(ctx):
 st,p,schema,co,*_=ctx;st.initialize(p,schema,organizations=True);c=st.connect(p)
 try:c.execute('UPDATE company SET roles_json=? WHERE id=?',(json.dumps(['aportante','beneficiaria']),co['id']));assert c.execute('SELECT count(*) FROM company').fetchone()[0]==1
 finally:c.close()

def test_unknown_version_never_reset(ctx):
 st,p,schema,*_=ctx;c=st.connect(p);c.execute('PRAGMA user_version=99');before=snapshot(c);c.close()
 with pytest.raises(ValueError):st.initialize(p,schema,organizations=True)
 c=st.connect(p)
 try:assert c.execute('PRAGMA user_version').fetchone()[0]==99 and snapshot(c)==before
 finally:c.close()

def test_failure_after_alter_rolls_back_schema_and_records(ctx,monkeypatch):
 st,p,schema,*_=ctx;c=st.connect(p);before=snapshot(c);c.close();original=st.connect
 def guarded(path):
  c=original(path)
  def auth(action,a,b,db,source):
   return sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_PRAGMA and a=='user_version' and b=='2' else sqlite3.SQLITE_OK
  c.set_authorizer(auth);return c
 monkeypatch.setattr(st,'connect',guarded)
 with pytest.raises((ValueError,sqlite3.DatabaseError)):st.initialize(p,schema,organizations=True)
 c=original(p)
 try:assert c.execute('PRAGMA user_version').fetchone()[0]==1 and 'roles_json' not in {x['name'] for x in c.execute('PRAGMA table_info(company)')} and snapshot(c)==before
 finally:c.close()
