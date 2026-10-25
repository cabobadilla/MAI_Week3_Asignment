import os,sys,json,sqlite3
from pathlib import Path
import pytest
@pytest.fixture
def db(tmp_path):
 root=Path(os.environ.get('GWA_ORG_FORMS_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,organizations,campaigns,recipients
 p=tmp_path/'org.sqlite';storage.initialize(p,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))),organizations=True);c=storage.connect(p);yield c,organizations,campaigns,recipients
 c.close();sys.path.remove(str(root))

def rows(n=1):return [{'name':'Synthetic Contact '+str(i),'email':f'contact{i}@example.invalid'} for i in range(n)]
def counts(c):return (c.execute('SELECT count(*) FROM company').fetchone()[0],c.execute('SELECT count(*) FROM contact').fetchone()[0])

def test_one_required_two_empty_optional(db):
 c,o,ca,re=db;x=o.save_organization(c,'Synthetic Co',rows()+[{'name':'','email':''},{'name':' ','email':' '}]);assert len(x['contacts'])==1 and counts(c)==(1,1)

def test_three_contacts_are_normalized_rows(db):
 c,o,ca,re=db;x=o.save_organization(c,'Synthetic Co',rows(3));assert len(x['contacts'])==3 and counts(c)==(1,3)

def test_three_slots_not_database_limit(db):
 c,o,ca,re=db;x=o.save_organization(c,'Synthetic Co',rows(4));assert len(x['contacts'])==4

@pytest.mark.parametrize('contacts',[[],[{'name':'','email':''}],[{'name':'Only name','email':''}],[{'name':'','email':'person@example.invalid'}],[{'name':'Person','email':'bad email'}]])
def test_invalid_or_missing_required_contact_rolls_back(db,contacts):
 c,o,ca,re=db
 with pytest.raises(ValueError):o.save_organization(c,'Synthetic Co',contacts)
 assert counts(c)==(0,0)

def test_duplicate_casefold_email_is_atomic(db):
 c,o,ca,re=db
 with pytest.raises(ValueError):o.save_organization(c,'Synthetic Co',[{'name':'One','email':'ONE@example.invalid'},{'name':'Two','email':'one@example.invalid'}])
 assert counts(c)==(0,0)

def test_beneficiary_uses_same_form_and_one_entity(db):
 c,o,ca,re=db;x=o.save_organization(c,'Municipalidad Ejemplo',rows(),roles=['beneficiaria']);assert x['roles']==['beneficiaria'] and counts(c)==(1,1)

def test_both_roles_and_role_filter(db):
 c,o,ca,re=db;x=o.save_organization(c,'Synthetic Co',rows(),roles=['aportante','beneficiaria']);assert set(x['roles'])=={'aportante','beneficiaria'};assert o.list_organizations(c,role='beneficiaria')[0]['id']==x['id']

def test_edit_preserves_omitted_contacts_and_roles_notes(db):
 c,o,ca,re=db;x=o.save_organization(c,'Synthetic Co',rows(4),roles=['beneficiaria'],notes='Preserve notes');before={a['id']:dict(a) for a in x['contacts']};edit=x['contacts'][0];y=o.save_organization(c,'Changed org',[{'id':edit['id'],'name':'Changed contact','email':edit['email']}],organization_id=x['id']);assert len(y['contacts'])==4 and y['roles']==['beneficiaria'] and y['notes']=='Preserve notes'
 for a in y['contacts']:
  if a['id']!=edit['id']:assert a==before[a['id']]
 assert counts(c)==(1,4)

def test_contact_from_other_org_cannot_be_overwritten(db):
 c,o,ca,re=db;a=o.save_organization(c,'First',rows());b=o.save_organization(c,'Second',[{'name':'Another','email':'other@example.invalid'}]);before=counts(c)
 with pytest.raises(ValueError):o.save_organization(c,'First changed',[{'id':b['contacts'][0]['id'],'name':'Wrong','email':'new@example.invalid'}],organization_id=a['id'])
 assert counts(c)==before and o.get_organization(c,a['id'])['name']=='First'

def test_sql_failure_rolls_back_entire_create(db):
 c,o,ca,re=db;c.execute("CREATE TEMP TRIGGER force_contact_error BEFORE INSERT ON contact WHEN (SELECT count(*) FROM contact)>0 BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
 with pytest.raises((ValueError,sqlite3.IntegrityError)):o.save_organization(c,'Synthetic',rows(3))
 assert counts(c)==(0,0)

def test_nested_transaction_failure_preserves_outer_write(db):
 c,o,ca,re=db;c.execute('BEGIN IMMEDIATE');c.execute("INSERT INTO company(id,name,notes,created_at) VALUES('outer-fixture','Outer preserved','','now')");c.execute("CREATE TEMP TRIGGER force_contact_error BEFORE INSERT ON contact WHEN (SELECT count(*) FROM contact)>0 BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
 with pytest.raises((ValueError,sqlite3.IntegrityError)):o.save_organization(c,'Synthetic',rows(3))
 assert counts(c)==(1,0) and c.execute("SELECT name FROM company WHERE id='outer-fixture'").fetchone()[0]=='Outer preserved';c.rollback()

def test_beneficiary_and_contributor_contacts_keep_campaign_dedup(db):
 c,o,ca,re=db;a=o.save_organization(c,'Contributor',rows(),roles=['aportante']);b=o.save_organization(c,'Beneficiary',rows(),roles=['beneficiaria']);cam=ca.create_campaign(c,'Campaign','Topic','Goal',formats=['email']);re.add_recipient(c,cam['id'],a['contacts'][0]['id'])
 with pytest.raises(ValueError):re.add_recipient(c,cam['id'],b['contacts'][0]['id'])
 assert len(re.list_recipients(c,cam['id']))==1

def test_invalid_role_does_not_create(db):
 c,o,ca,re=db
 with pytest.raises(ValueError):o.save_organization(c,'Synthetic',rows(),roles=['confirmed_sponsor'])
 assert counts(c)==(0,0)
