#!/usr/bin/env python3
"""Check normalized auth acceptance evidence; trusted coordinator still reviews actual security."""
import argparse,hashlib,json,pathlib,re
from check_plan import validate_plan,AUTH_TEST_GROUPS
P=pathlib.Path
def validate_delivery(plan_path,report_path,candidate_sha):
 if not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',candidate_sha):raise ValueError('Exact full candidate SHA required')
 p=validate_plan(plan_path);a=p['authentication']
 if a['status']=='legacy-not-checked':raise ValueError('New-app auth delivery requires plan v3; retain legacy contracts separately')
 report_bytes=P(report_path).read_bytes();e=json.loads(report_bytes)
 if not isinstance(e,dict) or e.get('phase')!='independent_final' or e.get('candidate_sha')!=candidate_sha or e.get('plan_sha256')!=p['plan_sha256']:raise ValueError('Authentication evidence phase/plan/candidate identity mismatch')
 if a['required']:
  if e.get('identity_mode')!='application':raise ValueError('Fixture-only identity is not application authentication')
  results=e.get('test_results')
  if not isinstance(results,list) or not all(isinstance(x,dict) and isinstance(x.get('id'),str) for x in results):raise ValueError('Auth test results required')
  ids=[x['id'] for x in results]
  if len(ids)!=len(set(ids)):raise ValueError('Duplicate auth test evidence')
  found={x['id']:x.get('status') for x in results};expected={x for g in AUTH_TEST_GROUPS for x in a['test_ids'][g]}
  if any(found.get(x)!='passed' for x in expected):raise ValueError('Missing, failed, skipped or not-run mandatory authentication test')
  if p['password_policy_checked'] and a['passwords']:
   policy=a['password_policy'];minimum=policy['min_characters'];by_id={x['id']:x for x in results}
   for cases in policy['test_ids'].values():
    if cases is None:continue
    for case,test_id in cases.items():
     result=by_id.get(test_id,{})
     if result.get('status')!='passed' or set(result)!={'id','status','password_length','accepted'} or type(result['password_length']) is not int or type(result['accepted']) is not bool:raise ValueError('Password boundary evidence missing/failed or includes fields beyond length and outcome')
     length=result['password_length'];accepted=result['accepted']
     valid=(length==minimum-1 and not accepted) if case=='below_minimum' else (length==minimum and accepted) if case=='at_minimum' else (length>minimum and accepted)
     if not valid:raise ValueError('Password boundary mismatch: reject below minimum, accept minimum and longer')
  outcome='pass'
 else:
  if e.get('identity_mode')!='exempted':raise ValueError('Evidence must preserve explicit user exemption')
  outcome='exempted'
 return {'password_policy_checked':p['password_policy_checked'],'authentication_gate':outcome,'candidate_sha':candidate_sha,'plan_sha256':p['plan_sha256'],'report_sha256':hashlib.sha256(report_bytes).hexdigest(),'delivery_accepted':False,'review_required':True}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--plan',required=True);ap.add_argument('--report',required=True);ap.add_argument('--candidate-sha',required=True);a=ap.parse_args()
 try:print(json.dumps(validate_delivery(a.plan,a.report,a.candidate_sha)));return 0
 except (ValueError,OSError,TypeError) as e:print(json.dumps({'state':'blocked','reason':str(e),'delivery_accepted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
