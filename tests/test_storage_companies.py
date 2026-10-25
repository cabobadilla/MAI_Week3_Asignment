import importlib.util,os,sys,sqlite3
from pathlib import Path
import pytest

@pytest.fixture
def modules():
 root=Path(os.environ.get('GWA_DB_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for name in ['app.storage','app.companies','app']:sys.modules.pop(name,None)
 import app.storage as storage
 import app.companies as companies
 yield storage,companies
 sys.path.remove(str(root))

@pytest.fixture
def db(modules,tmp_path):
 storage,companies=modules;path=tmp_path/'db/app.sqlite';storage.initialize(path,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));conn=storage.connect(path)
 yield conn,storage,companies,path
 conn.close()

def test_schema_and_foreign_keys(db):
 c,st,co,p=db;assert c.execute('PRAGMA foreign_keys').fetchone()[0]==1;assert c.execute('PRAGMA user_version').fetchone()[0]==1
 assert c.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]==11

def test_idempotent_initialize(db):
 c,st,co,p=db;a=co.create_company(c,'Example A');st.initialize(p,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));assert co.list_companies(c)[0]['id']==a['id']

def test_company_create_update_archive(db):
 c,st,co,p=db;a=co.create_company(c,' Example A ');assert a['name']=='Example A'
 co.update_company(c,a['id'],name='Example B',notes='note');assert co.list_companies(c)[0]['name']=='Example B'
 co.archive_company(c,a['id']);assert co.list_companies(c)==[];assert co.list_companies(c,include_archived=True)[0]['id']==a['id']

def test_company_similar_names_not_merged(db):
 c,st,co,p=db;a=co.create_company(c,'Example');b=co.create_company(c,'Example');assert a['id']!=b['id']

@pytest.mark.parametrize('name',['','  '])
def test_invalid_company(db,name):
 c,st,co,p=db
 with pytest.raises(ValueError):co.create_company(c,name)

def test_contacts_normalization_and_duplicates(db):
 c,st,co,p=db;a=co.create_company(c,'Example A');x=co.create_contact(c,a['id'],' Person+Tag@Example.invalid ',name='Person')
 assert x['email_key']=='person+tag@example.invalid' and x['email']=='Person+Tag@Example.invalid'
 with pytest.raises(ValueError):co.create_contact(c,a['id'],'person+tag@example.invalid')
 co.create_contact(c,a['id'],'person.tag@example.invalid');assert len(co.list_contacts(c,a['id']))==2

def test_contact_same_email_other_company_not_merged(db):
 c,st,co,p=db;a=co.create_company(c,'A');b=co.create_company(c,'B');x=co.create_contact(c,a['id'],'a@example.invalid');y=co.create_contact(c,b['id'],'a@example.invalid');assert x['id']!=y['id']

@pytest.mark.parametrize('email',['bad','a@','a b@example.invalid','a@@example.invalid',''])
def test_invalid_email(db,email):
 c,st,co,p=db;a=co.create_company(c,'A')
 with pytest.raises(ValueError):co.create_contact(c,a['id'],email)

def test_unknown_and_archived_company_contact(db):
 c,st,co,p=db
 with pytest.raises(ValueError):co.create_contact(c,'missing','a@example.invalid')
 a=co.create_company(c,'A');co.archive_company(c,a['id'])
 with pytest.raises(ValueError):co.create_contact(c,a['id'],'a@example.invalid')

def test_contact_update_archive(db):
 c,st,co,p=db;a=co.create_company(c,'A');x=co.create_contact(c,a['id'],'old@example.invalid');co.update_contact(c,x['id'],name='N',email='new@example.invalid');assert co.list_contacts(c,a['id'])[0]['email_key']=='new@example.invalid'
 co.archive_contact(c,x['id']);assert co.list_contacts(c,a['id'])==[];assert co.list_contacts(c,a['id'],include_archived=True)[0]['id']==x['id']

def test_transaction_rolls_back(db):
 c,st,co,p=db
 with pytest.raises(RuntimeError):
  with st.transaction(c):co.create_company(c,'A');raise RuntimeError('synthetic failure')
 assert co.list_companies(c)==[]

def test_transaction_commit(db):
 c,st,co,p=db
 with st.transaction(c):co.create_company(c,'A')
 assert len(co.list_companies(c))==1

def test_unknown_db_not_reset(modules,tmp_path):
 st,co=modules;path=tmp_path/'foreign.sqlite';c=sqlite3.connect(path);c.execute('CREATE TABLE private_data(x)');c.commit();c.close()
 with pytest.raises(ValueError):st.initialize(path,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))))
 c=sqlite3.connect(path);assert c.execute("SELECT name FROM sqlite_master WHERE name='private_data'").fetchone();c.close()
