import unittest,tempfile,pathlib,json,hashlib,subprocess,os,sys,copy,importlib.util
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parents[1];S=H/'scripts';sys.path.insert(0,str(S))
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,S/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
plan=module('check_plan','check_plan.py');driver=module('driver','run_opencode.py');verify=module('verify','verify_frontend.py');delivery=module('check_delivery','check_delivery.py')
# CLI fixtures use a real flock in their own scratch root, never the live host lock.
# This override exists only in the trusted test process, not as a product CLI/env option.
def driver_argv(*args):
 wrapper="import pathlib,runpy,sys;sys.dont_write_bytecode=True;sys.path.insert(0,str(pathlib.Path(sys.argv[1]).parent));ns=runpy.run_path(sys.argv[1]);ns['main'].__globals__['LOCK_PATH']=pathlib.Path(sys.argv[sys.argv.index('--out')+1]).parent/'fixture-executor.lock';sys.argv=sys.argv[1:];raise SystemExit(ns['main']())"
 return [sys.executable,'-c',wrapper,str(S/'run_opencode.py'),*args]
class Controls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='dot-controls-');self.root=pathlib.Path(self.tmp.name).resolve();self.p=self.root/'plan.json'
  a=self.root/'mock.png';a.write_bytes(b'synthetic mock asset');self.asset={'path':'mock.png','sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'viewport':'desktop','state':'results'}
  opts=[{'id':i,'version':'v1','assets':[self.asset,{**self.asset,'viewport':'mobile'}]} for i in ['A','B']]
  self.d={'stack':{'baseline':'cloudflare','local_runner':'wrangler','exception':None},'plan_version':'1','destination':{'mode':'local_simple','approved_by':'user','approval_ref':'synthetic-test-only'},'runtime_ai':{'enabled':False,'gateway':None},'ui':True,'design':{'options':opts,'selected':{'id':'A','version':'v1'},'approved_by':'user','approval_ref':'synthetic-test-only'}}
 def tearDown(self):self.tmp.cleanup()
 def save(self):self.p.write_text(json.dumps(self.d));return self.p
 def test_two_repairs_after_initial_then_user_escalation(self):
  self.d.update(plan_version='2',execution={'max_repairs':2});p=plan.validate_plan(self.save())
  for n in [0,1,2]:self.assertEqual(plan.validate_round(p,n)['round'],n)
  with self.assertRaisesRegex(plan.RepairLimitExceeded,'escalate to user'):plan.validate_round(p,3)
  for n in [None,-1,True]:
   with self.assertRaises(ValueError):plan.validate_round(p,n)
 def test_repair_limit_cannot_be_broadened_or_legacy_silently_migrated(self):
  legacy=plan.validate_plan(self.save());self.assertEqual(plan.validate_round(legacy,None)['max_repairs'],1)
  with self.assertRaises(plan.RepairLimitExceeded):plan.validate_round(legacy,2)
  self.d['execution']={'max_repairs':2}
  with self.assertRaisesRegex(ValueError,'Legacy'):plan.validate_plan(self.save())
  self.d['plan_version']='2'
  for limit in [3,-1,True,None]:
   self.d['execution']['max_repairs']=limit
   with self.assertRaises(ValueError):plan.validate_plan(self.save())
  self.d['execution']['max_repairs']=0;p=plan.validate_plan(self.save());self.assertEqual(plan.validate_round(p,0)['round'],0)
  with self.assertRaises(plan.RepairLimitExceeded):plan.validate_round(p,1)
 def test_exhausted_round_blocks_before_any_cli_and_retains_prior_evidence(self):
  self.d.update(plan_version='2',execution={'max_repairs':2});self.save();prior=self.root/'round-002-failure.json';prior.write_text('{"failed":true}');before=prior.read_bytes();marker=self.root/'invoked';fake=self.root/'fake';fake.write_text('#!/bin/sh\ntouch '+str(marker)+'\necho 2.0.32\n');fake.chmod(0o700);out=self.root/'round-003'
  run=subprocess.run(driver_argv('--plan',str(self.p),'--round','3','--opencode',str(fake),'--cwd',str(self.root),'--prompt',str(self.p),'--out',str(out)),capture_output=True,text=True)
  self.assertEqual(run.returncode,1);self.assertFalse(marker.exists());report=json.loads((out/'request.json').read_text());self.assertEqual(report['status'],'blocked');self.assertTrue(report['escalation_required']);self.assertEqual(report['declared_round'],3);self.assertTrue(json.loads((out/'state.json').read_text())['escalation_required']);self.assertFalse(report.get('inference_submitted',False));self.assertFalse(report['fallback_allowed']);self.assertEqual(prior.read_bytes(),before)
 def test_contract_and_plan_template_share_two_repair_ceiling(self):
  c=json.loads((H/'templates/contrato.schema.json').read_text());self.assertEqual(c['properties']['contract_version']['const'],'6');self.assertEqual(c['properties']['limits']['properties']['max_repairs']['maximum'],2);self.assertFalse(c['properties']['models']['properties']['silent_fallback']['const']);p=json.loads((H/'templates/plan.json.example').read_text());self.assertEqual(p['plan_version'],'4');self.assertEqual(p['execution']['max_repairs'],2)
 def auth_plan(self):
  self.d.update(plan_version='3',execution={'max_repairs':2},authentication={'required':True,'status':'specified','approach':'local application session boundary','roles':['owner'],'protected_resources':['/api/private'],'test_ids':{'unauthenticated':['AUTH-ANON'],'session_logout':['AUTH-SESSION'],'authorization':['AUTH-ACCESS']},'exception':None});return self.d['authentication']
 def auth_report(self,mode='application'):
  self.save();e={'phase':'independent_final','candidate_sha':'a'*40,'plan_sha256':hashlib.sha256(self.p.read_bytes()).hexdigest(),'identity_mode':mode,'test_results':[{'id':x,'status':'passed'} for x in ['AUTH-ANON','AUTH-SESSION','AUTH-ACCESS']]};p=self.root/'auth-report.json';p.write_text(json.dumps(e));return p,e
 def test_new_app_auth_missing_pending_blocks_before_cli_even_preflight(self):
  a=self.auth_plan()
  for absent in [True,False]:
   if absent:self.d.pop('authentication')
   else:self.d['authentication']={**a,'status':'pending'}
   with self.assertRaisesRegex(ValueError,'Authentication'):plan.validate_plan(self.save())
  marker=self.root/'called';fake=self.root/'fake';fake.write_text('#!/bin/sh\ntouch '+str(marker)+'\necho 2.0.32\n');fake.chmod(0o700)
  for preflight in [False,True]:
   out=self.root/('preflight-auth' if preflight else 'run-auth');argv=driver_argv('--plan',str(self.p),'--round','0','--opencode',str(fake),'--cwd',str(self.root),'--prompt',str(self.p),'--out',str(out))
   if preflight:argv+=['--preflight-only']
   z=subprocess.run(argv,capture_output=True,text=True);self.assertEqual(z.returncode,1);self.assertFalse(marker.exists());self.assertFalse(json.loads((out/'request.json').read_text()).get('inference_submitted',False))
 def test_auth_approach_roles_resources_and_all_acceptance_groups_required(self):
  self.auth_plan();self.assertTrue(plan.validate_plan(self.save())['authentication']['required'])
  original=copy.deepcopy(self.d)
  for key,bad in [('approach',None),('roles',[]),('protected_resources',[])]:
   self.d=copy.deepcopy(original);self.d['authentication'][key]=bad
   with self.assertRaises(ValueError):plan.validate_plan(self.save())
  for group in ['unauthenticated','session_logout','authorization']:
   self.d=copy.deepcopy(original);self.d['authentication']['test_ids'][group]=[]
   with self.assertRaises(ValueError):plan.validate_plan(self.save())
 def test_auth_omission_only_explicit_user_request_not_local_demo(self):
  a=self.auth_plan();a.update(required=False,status='exempted',approach=None,roles=[],protected_resources=[],test_ids={k:[] for k in a['test_ids']})
  for e in [None,{'requested_by':'coordinator','omit_authentication':True,'request_ref':'local-demo','reason':'simple'},{'requested_by':'user','omit_authentication':True,'request_ref':'','reason':'asked'}]:
   a['exception']=e
   with self.assertRaisesRegex(ValueError,'explicit user'):plan.validate_plan(self.save())
  a['exception']={'requested_by':'user','omit_authentication':True,'request_ref':'synthetic-user-request','reason':'User explicitly requested no authentication'};self.assertEqual(plan.validate_plan(self.save())['authentication']['status'],'exempted');report,e=self.auth_report('exempted');self.assertEqual(delivery.validate_delivery(self.p,report,'a'*40)['authentication_gate'],'exempted')
 def test_auth_delivery_requires_real_boundary_and_exact_evidence_identity(self):
  self.auth_plan();report,e=self.auth_report();good=delivery.validate_delivery(self.p,report,'a'*40);self.assertEqual(good['authentication_gate'],'pass');self.assertFalse(good['delivery_accepted'])
  original=copy.deepcopy(e)
  for key,bad in [('identity_mode','fixture-only'),('candidate_sha','b'*40),('plan_sha256','0'*64),('phase','development')]:
   e=copy.deepcopy(original);e[key]=bad;report.write_text(json.dumps(e))
   with self.assertRaises(ValueError):delivery.validate_delivery(self.p,report,'a'*40)
 def test_auth_delivery_missing_failed_skipped_not_run_duplicate_never_pass(self):
  self.auth_plan();report,e=self.auth_report();original=copy.deepcopy(e)
  for state in ['failed','skipped','not_run']:
   e=copy.deepcopy(original);e['test_results'][0]['status']=state;report.write_text(json.dumps(e))
   with self.assertRaises(ValueError):delivery.validate_delivery(self.p,report,'a'*40)
  for results in [[],original['test_results'][:-1],original['test_results']+[original['test_results'][0]]]:
   e=copy.deepcopy(original);e['test_results']=results;report.write_text(json.dumps(e))
   with self.assertRaises(ValueError):delivery.validate_delivery(self.p,report,'a'*40)
 def test_legacy_auth_not_silently_adopted_or_accepted_by_new_delivery_gate(self):
  self.assertEqual(plan.validate_plan(self.save())['authentication']['status'],'legacy-not-checked');report,e=self.auth_report()
  with self.assertRaisesRegex(ValueError,'plan v3'):delivery.validate_delivery(self.p,report,'a'*40)
  self.d['authentication']={'required':False}
  with self.assertRaisesRegex(ValueError,'Legacy'):plan.validate_plan(self.save())
 def test_auth_schema_and_draft_template_default_to_required(self):
  c=json.loads((H/'templates/contrato.schema.json').read_text());self.assertIn('authentication',c['required']);a=c['$defs']['authentication'];self.assertIn('exception',a['required']);self.assertEqual(a['properties']['exception']['properties']['requested_by']['const'],'user');p=json.loads((H/'templates/plan.json.example').read_text());self.assertTrue(p['authentication']['required']);self.assertEqual(p['authentication']['status'],'pending')
 def password_plan(self,minimum=8,reference=None):
  a=self.auth_plan();self.d['plan_version']='4';a['passwords']=True;a['password_policy']={'min_characters':minimum,'higher_minimum_ref':reference,'length_unit':'unicode-code-points','storage':'password-hash','rate_limiting':True,'no_silent_truncation':True,'test_ids':{surface:{case:surface+'-'+case for case in ['below_minimum','at_minimum','above_minimum']} for surface in ['ui','backend','provisioning']}};return a['password_policy']
 def password_report(self):
  report,e=self.auth_report();p=self.d['authentication']['password_policy'];minimum=p['min_characters']
  for surface,cases in p['test_ids'].items():
   if cases is None:continue
   for case,test_id in cases.items():e['test_results'].append({'id':test_id,'status':'passed','password_length':minimum-1 if case=='below_minimum' else minimum if case=='at_minimum' else minimum+12,'accepted':case!='below_minimum'})
  report.write_text(json.dumps(e));return report,e
 def test_password_default_7_rejected_8_and_longer_accepted_on_all_surfaces(self):
  self.password_plan();p=plan.validate_plan(self.save());self.assertTrue(p['password_policy_checked']);report,e=self.password_report();result=delivery.validate_delivery(self.p,report,'a'*40);self.assertTrue(result['password_policy_checked']);self.assertFalse(result['delivery_accepted'])
  original=copy.deepcopy(e)
  for surface in ['ui','backend','provisioning']:
   for case in ['below_minimum','at_minimum','above_minimum']:
    e=copy.deepcopy(original);row=next(x for x in e['test_results'] if x['id']==surface+'-'+case);row['accepted']=not row['accepted'];report.write_text(json.dumps(e))
    with self.assertRaisesRegex(ValueError,'Password boundary mismatch'):delivery.validate_delivery(self.p,report,'a'*40)
 def test_password_policy_higher_minimum_only_explicit_and_protections_preserved(self):
  self.password_plan();original=copy.deepcopy(self.d)
  for key,bad in [('min_characters',7),('min_characters',True),('min_characters',10),('storage','plaintext'),('rate_limiting',False),('no_silent_truncation',False)]:
   self.d=copy.deepcopy(original);self.d['authentication']['password_policy'][key]=bad
   with self.assertRaises(ValueError):plan.validate_plan(self.save())
  self.password_plan(12,'synthetic-explicit-user-or-regulatory-requirement');report,e=self.password_report();self.assertEqual(delivery.validate_delivery(self.p,report,'a'*40)['authentication_gate'],'pass')
 def test_passwords_not_imposed_on_other_auth_and_no_ui_not_faked(self):
  a=self.auth_plan();self.d['plan_version']='4';a.update(passwords=False,password_policy=None);self.assertTrue(plan.validate_plan(self.save())['authentication']['required']);report,e=self.auth_report();self.assertEqual(delivery.validate_delivery(self.p,report,'a'*40)['authentication_gate'],'pass')
  self.password_plan();self.d['ui']=False;self.d['authentication']['password_policy']['test_ids']['ui']=None;self.assertTrue(plan.validate_plan(self.save())['password_policy_checked']);self.d['ui']=True
  with self.assertRaises(ValueError):plan.validate_plan(self.save())
 def test_password_evidence_never_stores_values_or_passes_missing_boundary(self):
  self.password_plan();report,e=self.password_report();original=copy.deepcopy(e)
  for extra in [True,False]:
   e=copy.deepcopy(original)
   if extra:e['test_results'][-1]['password']='REDACTED-SYNTHETIC-NOT-A-CREDENTIAL'
   else:e['test_results'].pop()
   report.write_text(json.dumps(e))
   with self.assertRaisesRegex(ValueError,'Password boundary evidence'):delivery.validate_delivery(self.p,report,'a'*40)
 def test_three_destinations(self):
  for mode in ['local_simple','docker_local','cloudflare']:
   self.d['destination']['mode']=mode;self.assertEqual(plan.validate_plan(self.save())['destination'],mode)
 def test_incompatible_stack_needs_explicit_exception(self):
  self.d['stack']['local_runner']='arbitrary-server'
  with self.assertRaisesRegex(ValueError,'Wrangler'):plan.validate_plan(self.save())
  self.d['stack']['exception']={'approved_by':'user','approval_ref':'synthetic-test-only','reason':'Incompatible requirement documented'}
  self.assertFalse(plan.validate_plan(self.save())['cloudflare_baseline'])
 def test_missing_destination(self):
  self.d['destination']['mode']=None
  with self.assertRaisesRegex(ValueError,'destination'):plan.validate_plan(self.save())
 def test_missing_user_ref(self):
  self.d['destination']['approval_ref']=None
  with self.assertRaises(ValueError):plan.validate_plan(self.save())
 def test_openrouter_runtime_separate_from_go(self):
  self.d['runtime_ai']={'enabled':True,'gateway':'opencode-go'}
  with self.assertRaisesRegex(ValueError,'openrouter'):plan.validate_plan(self.save())
  self.d['runtime_ai']['gateway']='openrouter';self.assertTrue(plan.validate_plan(self.save())['runtime_ai']['enabled']);self.assertEqual(driver.MODEL,'opencode-go/deepseek-v4.1-flash')
 def test_design_pending_blocks_but_metadata_preflight_allowed(self):
  self.d['design']['selected']=None
  with self.assertRaises(ValueError):plan.validate_plan(self.save())
  self.assertFalse(plan.validate_plan(self.save(),False)['design_checked'])
 def test_one_option_blocks(self):
  self.d['design']['options']=self.d['design']['options'][:1]
  with self.assertRaises(ValueError):plan.validate_plan(self.save())
 def test_stale_version_blocks(self):
  self.d['design']['selected']['version']='v0'
  with self.assertRaisesRegex(ValueError,'stale'):plan.validate_plan(self.save())
 def test_changed_mockup_blocks(self):
  self.save();(self.root/'mock.png').write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'changed'):plan.validate_plan(self.p)
 def test_path_escape_blocks(self):
  self.d['design']['options'][0]['assets'][0]['path']='../outside.png'
  with self.assertRaises(ValueError):plan.validate_plan(self.save())
 def test_driver_missing_approval_never_calls_cli(self):
  self.d['design']['selected']=None;self.save();marker=self.root/'invoked';fake=self.root/'fake';fake.write_text('#!/bin/sh\ntouch '+str(marker)+'\necho 2.0.32\n');fake.chmod(0o700);out=self.root/'run'
  run=subprocess.run(driver_argv('--plan',str(self.p),'--opencode',str(fake),'--cwd',str(self.root),'--prompt',str(self.p),'--out',str(out)),capture_output=True,text=True)
  self.assertEqual(run.returncode,1);self.assertFalse(marker.exists());report=json.loads((out/'request.json').read_text());self.assertEqual(report['status'],'blocked');self.assertFalse(report.get('inference_submitted',False));self.assertEqual(json.loads((out/'state.json').read_text())['phase'],'blocked')
 def test_wrong_cli_version_blocks_before_server(self):
  self.save();fake=self.root/'fake';fake.write_text('#!/bin/sh\necho 9.9.9\n');fake.chmod(0o700);out=self.root/'run'
  run=subprocess.run(driver_argv('--plan',str(self.p),'--opencode',str(fake),'--cwd',str(self.root),'--prompt',str(self.p),'--out',str(out)),capture_output=True,text=True)
  self.assertEqual(run.returncode,1);report=json.loads((out/'request.json').read_text());self.assertIn('Unsupported OpenCode',report['reason']);self.assertFalse(report.get('inference_submitted',False));self.assertTrue(report['server_stopped'])
 def test_synthetic_owned_server_preflight_and_response(self):
  self.save();fake=self.root/'fake';fake.write_bytes((H/'tests/fake_opencode.py').read_bytes());fake.chmod(0o700)
  for preflight in [True,False]:
   out=self.root/('preflight' if preflight else 'response');args=driver_argv('--plan',str(self.p),'--opencode',str(fake),'--cwd',str(self.root),'--prompt',str(self.p),'--out',str(out))
   if preflight:args+=['--preflight-only']
   run=subprocess.run(args,capture_output=True,text=True,timeout=20);self.assertEqual(run.returncode,0,run.stderr+run.stdout);report=json.loads((out/'request.json').read_text());self.assertTrue(report['server_stopped']);self.assertIn(0,report['readiness_counts']);self.assertIn(1,report['readiness_counts']);self.assertEqual(report['status'],'preflight_complete' if preflight else 'response_received');self.assertEqual(report['inference_submitted'],not preflight);self.assertEqual((self.root/'fixture-run-called').exists(),not preflight)
   states=[json.loads(line)['phase'] for line in (out/'progress.jsonl').read_text().splitlines()];self.assertIn('session_bound',states);self.assertEqual(states[-1],report['status'])
 def test_second_repair_submits_only_synthetic_cli_with_fixed_go_model(self):
  self.d.update(plan_version='2',execution={'max_repairs':2});self.save();fake=self.root/'fake';fake.write_bytes((H/'tests/fake_opencode.py').read_bytes());fake.chmod(0o700);out=self.root/'repair-002'
  run=subprocess.run(driver_argv('--plan',str(self.p),'--round','2','--opencode',str(fake),'--cwd',str(self.root),'--prompt',str(self.p),'--out',str(out)),capture_output=True,text=True,timeout=20)
  self.assertEqual(run.returncode,0,run.stderr+run.stdout);report=json.loads((out/'request.json').read_text());self.assertEqual(report['repair_budget']['round'],2);self.assertEqual(report['repair_budget']['repairs_remaining_after_round'],0);self.assertTrue(report['inference_submitted']);self.assertEqual(report['requested_model'],'opencode-go/deepseek-v4.1-flash');self.assertFalse(report['fallback_allowed'])
 def test_real_recorded_sessions_replay(self):
  for d in json.loads((H/'tests/recorded_adapter.json').read_text()):
   driver.validate_agent(d['ready_agent']);driver.validate_session(d['created_session'],d['cwd'])
 def test_session_wrong_workspace_or_model_blocks(self):
  s={'id':'ses_owned','location':{'directory':str(self.root)},'agent':'survey-coder','model':{'id':'deepseek-v4.1-flash','providerID':'opencode-go'}};driver.validate_session(s,self.root);s['location']['directory']='/wrong'
  with self.assertRaisesRegex(RuntimeError,'location'):driver.validate_session(s,self.root)
  s['location']['directory']=str(self.root);s['model']['providerID']='openrouter'
  with self.assertRaisesRegex(RuntimeError,'model'):driver.validate_session(s,self.root)
 def test_agent_open_shell_blocks(self):
  s={'mode':'primary','model':{'id':'deepseek-v4.1-flash','providerID':'opencode-go'},'permissions':[{'action':'*','resource':'*','effect':'allow'}]}
  with self.assertRaisesRegex(RuntimeError,'permission'):driver.validate_agent(s)
class Metadata(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='dot-meta-');self.r=pathlib.Path(self.tmp.name);self.git('init','-q');(self.r/'.gitignore').write_text('.DS_Store\n*.ignored\n');(self.r/'source.mjs').write_text('original');self.git('add','.');self.git('-c','user.name=fixture','-c','user.email=fixture@invalid','-c','commit.gpgSign=false','commit','-qm','fixture');self.c={'candidate_sha':self.git('rev-parse','HEAD').strip(),'baseline_ignored':{},'incidental_metadata_policy':'record-ds-store-outside-public-v1'}
 def git(self,*a):return subprocess.check_output(['git','-C',str(self.r),*a],text=True)
 def tearDown(self):self.tmp.cleanup()
 def ds(self,name,tail=b'x'):
  p=self.r/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'\x00\x00\x00\x01Bud1'+tail)
 def test_incidental_changes_recorded_outside_artifact(self):
  self.ds('.DS_Store');a=verify.clean(self.r,self.c);self.ds('.DS_Store',b'changed');self.ds('dot/.DS_Store');b=verify.clean(self.r,self.c);self.assertNotEqual(a['.DS_Store'],b['.DS_Store']);self.assertIn('dot/.DS_Store',b)
 def test_public_metadata_blocks(self):
  self.ds('public/.DS_Store')
  with self.assertRaisesRegex(ValueError,'metadata exception'):verify.clean(self.r,self.c)
 def test_fake_metadata_blocks(self):
  (self.r/'.DS_Store').write_bytes(b'not Finder metadata')
  with self.assertRaises(ValueError):verify.clean(self.r,self.c)
 def test_unknown_ignored_blocks(self):
  (self.r/'config.ignored').write_text('unexpected')
  with self.assertRaisesRegex(ValueError,'ignored'):verify.clean(self.r,self.c)
 def test_dirty_source_blocks(self):
  (self.r/'source.mjs').write_text('changed')
  with self.assertRaisesRegex(ValueError,'Dirty'):verify.clean(self.r,self.c)
 def test_untracked_source_blocks(self):
  (self.r/'extra.mjs').write_text('new')
  with self.assertRaisesRegex(ValueError,'Dirty'):verify.clean(self.r,self.c)
 def test_legacy_contract_remains_strict(self):
  self.ds('.DS_Store');self.c.pop('incidental_metadata_policy')
  with self.assertRaisesRegex(ValueError,'ignored'):verify.clean(self.r,self.c)
if __name__=='__main__':unittest.main(verbosity=2)
