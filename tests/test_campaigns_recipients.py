import os,sys,json,sqlite3
from pathlib import Path
import pytest

@pytest.fixture
def db(tmp_path):
 root=Path(os.environ.get('GWA_CAMPAIGN_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for key in list(sys.modules):
  if key=='app' or key.startswith('app.'):sys.modules.pop(key,None)
 from app import storage,companies,campaigns,recipients
 path=tmp_path/'campaign.sqlite';storage.initialize(path,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));conn=storage.connect(path)
 yield conn,companies,campaigns,recipients
 conn.close();sys.path.remove(str(root))

def seed(db):
 c,co,ca,re=db;a=co.create_company(c,'Company A');b=co.create_company(c,'Company B');x=co.create_contact(c,a['id'],'x@example.invalid',name='X');y=co.create_contact(c,b['id'],'y@example.invalid',name='Y');campaign=ca.create_campaign(c,'Title','Topic','Objective');return a,b,x,y,campaign

def test_campaign_suite_and_subset(db):
 c,co,ca,re=db;a=ca.create_campaign(c,'T','Topic','Goal',academic_suite=True,formats=['email']);assert set(a['formats'])=={'linkedin','email','article','ad'}
 b=ca.create_campaign(c,'Daily','Topic','Goal',formats=['linkedin']);assert b['formats']==['linkedin'] and re.list_recipients(c,b['id'])==[]

@pytest.mark.parametrize('formats',[[],['fax'],['email','email']])
def test_invalid_formats(db,formats):
 c,co,ca,re=db
 with pytest.raises(ValueError):ca.create_campaign(c,'T','Topic','Goal',formats=formats)

@pytest.mark.parametrize('field',['title','topic','objective'])
def test_required_fields(db,field):
 c,co,ca,re=db;kw={'title':'T','topic':'Topic','objective':'Goal'};kw[field]='  '
 with pytest.raises(ValueError):ca.create_campaign(c,**kw)

def test_revision_and_conflict(db):
 c,co,ca,re=db;a=ca.create_campaign(c,'T','Topic','Goal');old=a['config_revision'];a=ca.update_campaign(c,a['id'],title='New title');assert a['config_revision']==old
 a=ca.update_campaign(c,a['id'],objective='New goal',expected_revision=old);assert a['config_revision']==old+1
 with pytest.raises(ValueError):ca.update_campaign(c,a['id'],tone='wrong',expected_revision=old)
 assert ca.get_campaign(c,a['id'])['tone']!='wrong'

def test_archive_not_delete(db):
 c,co,ca,re=db;a=ca.create_campaign(c,'T','Topic','Goal');ca.archive_campaign(c,a['id']);assert ca.list_campaigns(c)==[];assert ca.list_campaigns(c,include_archived=True)[0]['id']==a['id']
 with pytest.raises(ValueError):ca.update_campaign(c,a['id'],topic='Change')

def test_multi_company_recipients_no_distribution(db):
 c,co,ca,re=db;a,b,x,y,cam=seed(db);re.add_recipient(c,cam['id'],x['id']);re.add_recipient(c,cam['id'],y['id']);assert len(re.list_recipients(c,cam['id']))==2
 assert c.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==0
 assert c.execute('SELECT count(*) FROM approval').fetchone()[0]==0

def test_duplicate_email_across_companies(db):
 c,co,ca,re=db;a,b,x,y,cam=seed(db);other=co.create_contact(c,b['id'],'X@example.invalid');re.add_recipient(c,cam['id'],x['id'])
 with pytest.raises(ValueError):re.add_recipient(c,cam['id'],other['id'])

def test_contact_snapshot_immutable_on_edit(db):
 c,co,ca,re=db;a,b,x,y,cam=seed(db);r=re.add_recipient(c,cam['id'],x['id']);co.update_contact(c,x['id'],name='Changed',email='new@example.invalid');co.update_company(c,a['id'],name='Changed company')
 snap=re.get_recipient(c,r['id'])['snapshot'];assert snap['email']=='x@example.invalid' and snap['contact_name']=='X' and snap['company_name']=='Company A'

def test_restore_keeps_id_and_snapshot(db):
 c,co,ca,re=db;a,b,x,y,cam=seed(db);r=re.add_recipient(c,cam['id'],x['id']);re.archive_recipient(c,r['id']);assert re.list_recipients(c,cam['id'])==[]
 with pytest.raises(ValueError):re.add_recipient(c,cam['id'],x['id'])
 re.restore_recipient(c,r['id']);assert re.list_recipients(c,cam['id'])[0]['id']==r['id']

def test_changed_address_not_silent_restore(db):
 c,co,ca,re=db;a,b,x,y,cam=seed(db);r=re.add_recipient(c,cam['id'],x['id']);re.archive_recipient(c,r['id']);co.update_contact(c,x['id'],email='new@example.invalid')
 with pytest.raises(ValueError):re.restore_recipient(c,r['id'])

def test_archived_parent_not_selectable(db):
 c,co,ca,re=db;a,b,x,y,cam=seed(db);co.archive_company(c,a['id'])
 with pytest.raises(ValueError):re.add_recipient(c,cam['id'],x['id'])

def test_cross_campaign_lists(db):
 c,co,ca,re=db;a,b,x,y,cam=seed(db);other=ca.create_campaign(c,'Other','Topic','Goal');re.add_recipient(c,cam['id'],x['id']);assert re.list_recipients(c,other['id'])==[]

def test_unknown_field_no_write(db):
 c,co,ca,re=db;a=ca.create_campaign(c,'T','Topic','Goal')
 with pytest.raises(ValueError):ca.update_campaign(c,a['id'],sent=True)
 assert ca.get_campaign(c,a['id'])['config_revision']==1

def test_sql_text_is_data(db):
 c,co,ca,re=db;title="'; DROP TABLE contact;--";a=ca.create_campaign(c,title,'Topic','Goal');assert a['title']==title;assert c.execute('SELECT count(*) FROM contact').fetchone()[0]==0
