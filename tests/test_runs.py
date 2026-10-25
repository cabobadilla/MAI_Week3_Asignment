import os,sys,json,sqlite3,uuid
from pathlib import Path
import pytest
@pytest.fixture
def db(tmp_path):
 root=Path(os.environ['GWA_RUNS_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,runs
 p=tmp_path/'runs.sqlite';storage.initialize(p,Path(os.environ['GWA_SCHEMA_FILE']));c=storage.connect(p);cam=campaigns.create_campaign(c,'Synthetic','Training','Goal',formats=['email']);yield c,campaigns,runs,cam,p
 c.close();sys.path.remove(str(root))

def test_new_run_is_prepared_with_brief_snapshot(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);assert x['status']=='prepared' and x['config_revision']==cam['config_revision'];assert x['config']['objective']=='Goal' and x['metrics']['attempts']==0;assert x['sources']==[]

def test_create_retry_by_uuid_is_idempotent(db):
 c,ca,r,cam,p=db;id=str(uuid.uuid4());a=r.create_run(c,cam['id'],run_id=id);b=r.create_run(c,cam['id'],run_id=id);assert a==b and c.execute('SELECT count(*) FROM generation_run').fetchone()[0]==1

def test_run_id_cannot_move_campaign(db):
 c,ca,r,cam,p=db;id=str(uuid.uuid4());r.create_run(c,cam['id'],run_id=id);other=ca.create_campaign(c,'Other','Training','Goal',formats=['email'])
 with pytest.raises(ValueError):r.create_run(c,other['id'],run_id=id)

def test_status_transition_and_optimistic_expected(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);y=r.transition_run(c,x['id'],'running','retrieve',expected_status='prepared');assert y['status']=='running'
 with pytest.raises(ValueError):r.transition_run(c,x['id'],'waiting_input','ask',expected_status='prepared')
 assert r.get_run(c,x['id'])['status']=='running'

@pytest.mark.parametrize('terminal',['finished','cancelled'])
def test_terminal_cannot_restart(db,terminal):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);r.transition_run(c,x['id'],'running','retrieve');r.transition_run(c,x['id'],terminal,'done')
 with pytest.raises(ValueError):r.transition_run(c,x['id'],'running','draft')

def test_stale_brief_blocks_start(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);ca.update_campaign(c,cam['id'],objective='Changed')
 with pytest.raises(ValueError):r.transition_run(c,x['id'],'running','retrieve')
 assert r.get_run(c,x['id'])['status']=='prepared'

def test_waiting_and_failed_can_resume_explicitly(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);r.transition_run(c,x['id'],'running','retrieve');r.transition_run(c,x['id'],'waiting_input','ask');r.transition_run(c,x['id'],'running','draft');r.transition_run(c,x['id'],'failed','draft');assert r.transition_run(c,x['id'],'running','draft')['status']=='running'

def test_snapshots_persist_and_freeze_after_attempt(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);a=r.set_snapshots(c,x['id'],[],{'items':[],'context_hash':'0'*64});assert a['context']['context_hash']=='0'*64;c.execute('UPDATE generation_run SET metrics_json=? WHERE id=?',(json.dumps({'attempts':1}),x['id']))
 with pytest.raises(ValueError):r.set_snapshots(c,x['id'],[],{'items':[],'context_hash':'1'*64})
 assert r.set_snapshots(c,x['id'],[],{'items':[],'context_hash':'0'*64})['context']==a['context']

def test_unknown_or_bad_status_does_not_mutate(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id'])
 with pytest.raises(ValueError):r.transition_run(c,x['id'],'published','done')
 with pytest.raises(ValueError):r.get_run(c,'missing')
 assert r.get_run(c,x['id'])['status']=='prepared'

def test_restart_preserves_state_without_running_anything(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);r.transition_run(c,x['id'],'running','retrieve');r.transition_run(c,x['id'],'waiting_input','ask');other=sqlite3.connect(p);other.row_factory=sqlite3.Row
 try:assert r.get_run(other,x['id'])['status']=='waiting_input'
 finally:other.close()

def test_list_campaign_isolation(db):
 c,ca,r,cam,p=db;x=r.create_run(c,cam['id']);other=ca.create_campaign(c,'Other','Training','Goal',formats=['email']);assert r.list_runs(c,other['id'])==[] and r.list_runs(c,cam['id'])[0]['id']==x['id']
