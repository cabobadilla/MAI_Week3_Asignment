import unittest,tempfile,pathlib,sys,json,hashlib,copy
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(H/'scripts'))
from check_release import validate_release
class ReleaseChecks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='release-controls-');self.r=pathlib.Path(self.tmp.name);self.plan=self.r/'plan.json';self.policy=self.r/'policy.json';self.receipt=self.r/'receipt.json';self.auth=self.r/'auth.json'
  asset=self.r/'mock.png';asset.write_bytes(b'synthetic-only');a={'path':'mock.png','sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'state':'synthetic','viewport':'desktop'}
  plan={'plan_version':'3','execution':{'max_repairs':2},'destination':{'mode':'cloudflare','approved_by':'user','approval_ref':'fixture-choice'},'stack':{'baseline':'cloudflare','local_runner':'wrangler','exception':None},'runtime_ai':{'enabled':False,'gateway':None},'ui':True,'design':{'options':[{'id':k,'version':'v1','assets':[a,{**a,'viewport':'mobile'}]} for k in ['A','B']],'selected':{'id':'A','version':'v1'},'approved_by':'user','approval_ref':'fixture-design'},'authentication':{'required':True,'status':'specified','approach':'synthetic declared application session boundary','roles':['owner'],'protected_resources':['/api/private'],'test_ids':{'unauthenticated':['A'],'session_logout':['S'],'authorization':['Z']},'exception':None}}
  self.plan.write_text(json.dumps(plan));ph=hashlib.sha256(self.plan.read_bytes()).hexdigest();self.auth.write_text(json.dumps({'phase':'independent_final','candidate_sha':'a'*40,'plan_sha256':ph,'identity_mode':'application','test_results':[{'id':x,'status':'passed'} for x in ['A','S','Z']]}))
  self.p={'policy_version':'1','app_plan_sha256':ph,'target_environment':'production','target_runtime':'fixture-remote-runtime','authorization_ref':'fixture-release-approved','expectation_source':'frozen-acceptance-ROOT-01','expectations_copied_from_candidate':False,'config_sha256':'c'*64,'validator_bundle_sha256':'d'*64,'root_authenticated_status':200,'root_anonymous_status':302,'api_anonymous_status':401,'cpu_budget_ms':5000,'previous_cpu_budget_ms':1000,'cpu_increase_authorization_ref':'fixture-separate-cpu-approval','critical_features':[{'id':'critical-auth-feature','parameters_sha256':'e'*64,'decision_ref':'fixture-design-decision'}],'dependencies_reviewed':True,'dependency_manifest_sha256':'f'*64,'external_material_authority':'data-only','sandbox_proves_trust':False,'probe_cleanup_required':True}
  smoke={'root_authenticated_status':200,'root_anonymous_status':302,'api_anonymous_status':401,'login':'passed','panel':'passed','api':'passed','logout':'passed','anonymous_denied':'passed'}
  self.e={'receipt_version':'1','candidate_sha':'a'*40,'app_plan_sha256':ph,'policy_sha256':None,'phase':'independent_final','environment':'production','target_runtime':'fixture-remote-runtime','deployment_version':'fixture-version','config_sha256':'c'*64,'identity_verified':True,'secret_presence_verified':True,'validators_before_sha256':'d'*64,'validators_after_sha256':'d'*64,'assets_mode':'target-real-assets','synthetic_root_rewrite':False,'compatibility_probes':[{'id':'critical-auth-feature','parameters_sha256':'e'*64,'status':'passed','environment':'production','evidence_ref':'reviewed-probe'}],'measurements':[{'environment':'local','metric':'cpu_ms','value':520,'source_ref':'fixture-local-cpu'},{'environment':'production','metric':'cpu_ms','value':2400,'source_ref':'fixture-target-cpu'},{'environment':'production','metric':'wall_ms','value':10000,'source_ref':'fixture-elapsed-clock'}],'smoke':{'desktop':smoke,'mobile':copy.deepcopy(smoke)},'probe_cleanup':{'status':'completed','authorization_ref':'fixture-cleanup-approved','reason':None},'evidence_class':'authenticated_remote'}
 def tearDown(self):self.tmp.cleanup()
 def check(self):
  self.policy.write_text(json.dumps(self.p));self.e['policy_sha256']=hashlib.sha256(self.policy.read_bytes()).hexdigest();self.receipt.write_text(json.dumps(self.e));return validate_release(self.plan,self.policy,self.receipt,self.auth,'a'*40)
 def test_real_root_failure_then_fix_against_unchanged_frozen_expectation(self):
  self.e['smoke']['mobile']['root_authenticated_status']=404
  with self.assertRaisesRegex(ValueError,'Root/API'):self.check()
  self.e['smoke']['mobile']['root_authenticated_status']=200;self.assertEqual(self.check()['release_gate'],'review_pending');self.assertFalse(self.check()['delivery_accepted'])
 def test_stub_or_public_checks_cannot_hide_missing_authenticated_remote_evidence(self):
  original=copy.deepcopy(self.e)
  for key,bad in [('synthetic_root_rewrite',True),('assets_mode','mock-stub'),('evidence_class','public_checks_only'),('evidence_class','user_confirmation'),('evidence_class','local_e2e'),('phase','development')]:
   self.e=copy.deepcopy(original);self.e[key]=bad
   with self.assertRaises(ValueError):self.check()
 def test_real_target_compatibility_and_exact_parameters_required(self):
  original=copy.deepcopy(self.e)
  for key,bad in [('environment','local'),('status','failed'),('parameters_sha256','0'*64)]:
   self.e=copy.deepcopy(original);self.e['compatibility_probes'][0][key]=bad
   with self.assertRaises(ValueError):self.check()
  self.e=copy.deepcopy(original);self.e['compatibility_probes']=[]
  with self.assertRaises(ValueError):self.check()
 def test_cpu_and_wall_are_separate_and_local_does_not_certify_target(self):
  self.assertEqual(self.check()['release_gate'],'review_pending') # wall10000 is not CPU2400
  self.e['measurements']=[self.e['measurements'][0]]
  with self.assertRaisesRegex(ValueError,'Actual-target CPU'):self.check()
 def test_cpu_budget_changes_require_approval_and_target_measurement_must_fit(self):
  self.p['cpu_increase_authorization_ref']=None
  with self.assertRaisesRegex(ValueError,'CPU limit increase'):self.check()
  self.p['cpu_increase_authorization_ref']='fixture-separate-approval';self.e['measurements'][1]['value']=5001
  with self.assertRaisesRegex(ValueError,'exceeds authorized budget'):self.check()
 def test_candidate_config_and_verifiers_must_remain_exact(self):
  original=copy.deepcopy(self.e)
  for key,bad in [('candidate_sha','b'*40),('config_sha256','0'*64),('validators_after_sha256','0'*64)]:
   self.e=copy.deepcopy(original);self.e[key]=bad
   with self.assertRaises(ValueError):self.check()
 def test_approval_secret_presence_and_authorized_probe_cleanup_are_required(self):
  self.e['secret_presence_verified']=False
  with self.assertRaises(ValueError):self.check()
  self.e['secret_presence_verified']=True;self.e['probe_cleanup']['status']='not_run'
  with self.assertRaisesRegex(ValueError,'probe cleanup'):self.check()
  self.e['probe_cleanup']['status']='completed';self.e['secret_values']='DO-NOT-STORE'
  with self.assertRaisesRegex(ValueError,'secret values'):self.check()
 def test_candidate_golden_output_external_commands_and_missing_smoke_rejected(self):
  self.p['expectations_copied_from_candidate']=True
  with self.assertRaisesRegex(ValueError,'frozen acceptance'):self.check()
  self.p['expectations_copied_from_candidate']=False;self.p['external_material_authority']='instructions'
  with self.assertRaisesRegex(ValueError,'Dependency origin'):self.check()
  self.p['external_material_authority']='data-only';self.e['smoke']['desktop']['logout']='not_run'
  with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main(verbosity=2)
