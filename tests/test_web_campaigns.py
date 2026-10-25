import os,sys
from pathlib import Path
import pytest
from fastapi import FastAPI,HTTPException,Request
from fastapi.testclient import TestClient
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_WEB_CAMPAIGN_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage
 from app.web_campaigns import mount_campaigns
 db=tmp_path/'test.sqlite';storage.initialize(db,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);app=FastAPI()
 async def require(request:Request):
  if request.headers.get('X-Test-Auth')!='yes':raise HTTPException(401)
  return {'operator':'operator'}
 app.state.require_operator=require;mount_campaigns(app,db)
 with TestClient(app,headers={'X-Test-Auth':'yes'}) as c:yield c
 sys.path.remove(str(root))
def brief():return {'title':'Campaña sintética','topic':'Formación','objective':'Presentar propósito','academic_suite':True}
def test_create_academic_and_list(ctx):
 c=ctx;r=c.post('/api/campaigns',json=brief());assert r.status_code==200;x=r.json();assert set(x['formats'])=={'linkedin','email','article','ad'};assert isinstance(x['id'],str);assert c.get('/api/campaigns/'+x['id']).json()==x;assert len(c.get('/api/campaigns').json())==1
def test_separate_campaigns(ctx):
 c=ctx;a=c.post('/api/campaigns',json=brief()).json();p=brief();p['title']='Otra';b=c.post('/api/campaigns',json=p).json();assert a['id']!=b['id'] and len(c.get('/api/campaigns').json())==2
def test_update_and_stale_revision(ctx):
 c=ctx;x=c.post('/api/campaigns',json=brief()).json();url='/api/campaigns/'+x['id'];r=c.put(url,json={'objective':'Nuevo','expected_revision':1});assert r.status_code==200 and r.json()['config_revision']==2;assert c.put(url,json={'objective':'Otro','expected_revision':1}).status_code==400;assert c.get(url).json()['objective']=='Nuevo'
def test_malformed_rejected(ctx):
 c=ctx
 for p in [[],{},dict(brief(),sql='drop'),dict(brief(),academic_suite='false'),dict(brief(),formats=['invalid'])]:assert c.post('/api/campaigns',json=p).status_code==400
 assert c.get('/api/campaigns').json()==[]
def test_auth_required(ctx):
 c=ctx;c.headers.pop('X-Test-Auth');assert c.get('/api/campaigns').status_code==401;assert c.post('/api/campaigns',json=brief()).status_code==401
