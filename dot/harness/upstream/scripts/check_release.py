#!/usr/bin/env python3
"""Offline checks of frozen release intent and normalized receipts, never deploys or reads secrets."""
import argparse,hashlib,json,pathlib,re,math
from check_plan import validate_plan,nonempty
from check_delivery import validate_delivery
P=pathlib.Path
POLICY_KEYS={'policy_version','app_plan_sha256','target_environment','target_runtime','authorization_ref','expectation_source','expectations_copied_from_candidate','config_sha256','validator_bundle_sha256','root_authenticated_status','root_anonymous_status','api_anonymous_status','cpu_budget_ms','previous_cpu_budget_ms','cpu_increase_authorization_ref','critical_features','dependencies_reviewed','dependency_manifest_sha256','external_material_authority','sandbox_proves_trust','probe_cleanup_required'}
RECEIPT_KEYS={'receipt_version','candidate_sha','app_plan_sha256','policy_sha256','phase','environment','target_runtime','deployment_version','config_sha256','identity_verified','secret_presence_verified','validators_before_sha256','validators_after_sha256','assets_mode','synthetic_root_rewrite','compatibility_probes','measurements','smoke','probe_cleanup','evidence_class'}
def exact_keys(value,keys,label):
 if not isinstance(value,dict) or set(value)!=keys:raise ValueError(label+' missing/unknown fields; do not include secret values')
def digest(value):return isinstance(value,str) and bool(re.fullmatch('[a-f0-9]{64}',value))
def integer(value):return type(value) is int and value>0
def validate_release(plan_path,policy_path,receipt_path,auth_report_path,candidate_sha):
 planning=validate_plan(plan_path);auth=validate_delivery(plan_path,auth_report_path,candidate_sha)
 policy_bytes=P(policy_path).read_bytes();receipt_bytes=P(receipt_path).read_bytes();p=json.loads(policy_bytes);e=json.loads(receipt_bytes)
 exact_keys(p,POLICY_KEYS,'Policy');exact_keys(e,RECEIPT_KEYS,'Receipt')
 if p['policy_version']!='1' or e['receipt_version']!='1':raise ValueError('Unsupported release verification contract')
 if p['app_plan_sha256']!=planning['plan_sha256'] or e['app_plan_sha256']!=planning['plan_sha256'] or e['policy_sha256']!=hashlib.sha256(policy_bytes).hexdigest() or e['candidate_sha']!=candidate_sha:raise ValueError('Release policy/plan/candidate identity mismatch')
 environment=p['target_environment']
 if environment not in ['local','test_remote','production'] or e['environment']!=environment or not nonempty(p['target_runtime']) or e['target_runtime']!=p['target_runtime']:raise ValueError('Evidence is not from the declared target runtime/environment')
 if not nonempty(p['authorization_ref']):raise ValueError('Separate release authorization required')
 if not nonempty(p['expectation_source']) or p['expectations_copied_from_candidate'] is not False:raise ValueError('Expected results must come from frozen acceptance, not candidate output')
 if p['dependencies_reviewed'] is not True or not digest(p['dependency_manifest_sha256']) or p['external_material_authority']!='data-only' or p['sandbox_proves_trust'] is not False:raise ValueError('Dependency origin/integrity review required; external material and sandbox confer no trust')
 for key in ['config_sha256','validator_bundle_sha256']:
  if not digest(p[key]):raise ValueError('Frozen config/validator digest required')
 if e['config_sha256']!=p['config_sha256'] or e['validators_before_sha256']!=p['validator_bundle_sha256'] or e['validators_after_sha256']!=p['validator_bundle_sha256']:raise ValueError('Deployment config or independent validators changed')
 if e['phase']!='independent_final' or not nonempty(e['deployment_version']) or e['identity_verified'] is not True or e['secret_presence_verified'] is not True:raise ValueError('Version receipt, independent checks and identity/secret-presence booleans required')
 expected_class='local_e2e' if environment=='local' else 'authenticated_remote' if planning['authentication']['required'] else 'remote_e2e_auth_exempted'
 if e['evidence_class']!=expected_class:raise ValueError('Public checks, local tests or user confirmation cannot substitute authenticated target evidence')
 if e['synthetic_root_rewrite'] is not False or e['assets_mode']!=('wrangler-real-assets' if environment=='local' else 'target-real-assets'):raise ValueError('Real assets and original root request required; synthetic root rewrite masks routing failures')
 for key in ['root_authenticated_status','root_anonymous_status','api_anonymous_status']:
  if type(p[key]) is not int or not 100<=p[key]<=599:raise ValueError('Explicit HTTP expectations required')
 features=p['critical_features'];probes=e['compatibility_probes']
 if not isinstance(features,list) or not features or not isinstance(probes,list):raise ValueError('Target compatibility probes required before auth rollout')
 expected={};actual={}
 for f in features:
  exact_keys(f,{'id','parameters_sha256','decision_ref'},'Critical feature')
  if not nonempty(f['id']) or f['id'] in expected or not digest(f['parameters_sha256']) or not nonempty(f['decision_ref']):raise ValueError('Unique feature, frozen parameters and explicit decision required')
  expected[f['id']]=f['parameters_sha256']
 for probe in probes:
  exact_keys(probe,{'id','parameters_sha256','status','environment','evidence_ref'},'Compatibility probe')
  if not nonempty(probe['id']) or probe['id'] in actual or probe['status']!='passed' or probe['environment']!=environment or not nonempty(probe['evidence_ref']):raise ValueError('Target runtime compatibility unverified/failed/duplicated')
  actual[probe['id']]=probe['parameters_sha256']
 if actual!=expected:raise ValueError('Missing or mismatched actual-target parameter probe')
 budget=p['cpu_budget_ms'];previous=p['previous_cpu_budget_ms']
 if not integer(budget) or not integer(previous):raise ValueError('Explicit CPU budgets required, never inferred from wall time')
 if budget>previous and not nonempty(p['cpu_increase_authorization_ref']):raise ValueError('CPU limit increase requires separate explicit authorization')
 measurements=e['measurements'];observed={}
 if not isinstance(measurements,list):raise ValueError('CPU and wall measurements required')
 for m in measurements:
  exact_keys(m,{'environment','metric','value','source_ref'},'Measurement')
  key=(m['environment'],m['metric'])
  if m['environment'] not in ['local',environment] or m['metric'] not in ['cpu_ms','wall_ms'] or key in observed or type(m['value']) not in [int,float] or not math.isfinite(m['value']) or m['value']<0 or not nonempty(m['source_ref']):raise ValueError('Label CPU/wall and local/target measurements with their real source')
  observed[key]=m['value']
 if (environment,'cpu_ms') not in observed or (environment,'wall_ms') not in observed:raise ValueError('Actual-target CPU and wall measurements required; local timing alone is insufficient')
 if observed[(environment,'cpu_ms')]>budget:raise ValueError('Observed target CPU exceeds authorized budget')
 viewports={'desktop','mobile'} if planning['ui'] else {'api_only'}
 if not isinstance(e['smoke'],dict) or set(e['smoke'])!=viewports:raise ValueError('Complete target smoke viewports required')
 for result in e['smoke'].values():
  exact_keys(result,{'root_authenticated_status','root_anonymous_status','api_anonymous_status','login','panel','api','logout','anonymous_denied'},'Smoke')
  if any(type(result[k]) is not int or result[k]!=p[k] for k in ['root_authenticated_status','root_anonymous_status','api_anonymous_status']):raise ValueError('Root/API status regression against frozen acceptance')
  required=['api']+(['panel'] if planning['ui'] else [])+(['login','logout','anonymous_denied'] if planning['authentication']['required'] else [])
  if any(result[k]!='passed' for k in required):raise ValueError('Login/panel/API/logout/anonymous denial smoke incomplete or failed')
 cleanup=e['probe_cleanup'];exact_keys(cleanup,{'status','authorization_ref','reason'},'Probe cleanup')
 if type(p['probe_cleanup_required']) is not bool:raise ValueError('Explicit probe cleanup decision required')
 if p['probe_cleanup_required']:
  if cleanup['status']!='completed' or not nonempty(cleanup['authorization_ref']):raise ValueError('Authorized probe cleanup must be confirmed')
 elif cleanup['status']!='not_applicable' or not nonempty(cleanup['reason']):raise ValueError('Record why probe cleanup is not applicable')
 return {'release_gate':'review_pending','delivery_accepted':False,'candidate_sha':candidate_sha,'policy_sha256':hashlib.sha256(policy_bytes).hexdigest(),'receipt_sha256':hashlib.sha256(receipt_bytes).hexdigest(),'authentication_gate':auth['authentication_gate'],'environment':environment}
def main():
 ap=argparse.ArgumentParser()
 for name in ['plan','policy','receipt','auth-report','candidate-sha']:ap.add_argument('--'+name,required=True)
 a=ap.parse_args()
 try:print(json.dumps(validate_release(a.plan,a.policy,a.receipt,a.auth_report,a.candidate_sha)));return 0
 except (ValueError,OSError,TypeError) as err:print(json.dumps({'state':'blocked','reason':str(err),'delivery_accepted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
