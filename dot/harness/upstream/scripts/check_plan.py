#!/usr/bin/env python3
"""Small offline readiness check; trusted coordinator supplies protected plan."""
import argparse,hashlib,json,pathlib
P=pathlib.Path
DESTINATIONS={'local_simple','docker_local','cloudflare'}
AUTH_TEST_GROUPS=('unauthenticated','session_logout','authorization')
def nonempty(value):return isinstance(value,str) and bool(value.strip()) and not value.startswith('REPLACE')
def string_list(value,allow_empty=False):return isinstance(value,list) and (allow_empty or bool(value)) and all(nonempty(x) for x in value) and len(value)==len(set(value))
PASSWORD_CASES=('below_minimum','at_minimum','above_minimum')
PASSWORD_SURFACES=('ui','backend','provisioning')
def validate_password_policy(d,a):
 if d.get('plan_version')!='4':return
 if type(a.get('passwords')) is not bool:raise ValueError('Explicit passwords selection required; other auth mechanisms remain valid')
 policy=a.get('password_policy')
 if not a['required'] and a['passwords']:raise ValueError('Exempted authentication cannot select passwords')
 if not a['passwords']:
  if policy is not None:raise ValueError('Non-password authentication must not impose password policy')
  return
 if not isinstance(policy,dict):raise ValueError('Password policy required: default minimum 8 characters, longer allowed')
 minimum=policy.get('min_characters');ref=policy.get('higher_minimum_ref')
 if type(minimum) is not int or minimum<8 or (minimum>8 and not nonempty(ref)) or (minimum==8 and ref is not None):raise ValueError('Minimum is 8 characters by default; higher minimum requires explicit user/regulatory reference')
 if policy.get('length_unit')!='unicode-code-points' or policy.get('storage')!='password-hash' or policy.get('rate_limiting') is not True or policy.get('no_silent_truncation') is not True:raise ValueError('Preserve hashed storage, rate limiting, code-point counting and no silent truncation')
 tests=policy.get('test_ids')
 if not isinstance(tests,dict) or set(tests)!=set(PASSWORD_SURFACES):raise ValueError('Password boundary tests required for UI/backend/provisioning')
 for surface in PASSWORD_SURFACES:
  cases=tests[surface]
  if surface=='ui' and d.get('ui') is False and cases is None:continue
  if not isinstance(cases,dict) or set(cases)!=set(PASSWORD_CASES) or not all(nonempty(x) for x in cases.values()) or len(set(cases.values()))!=3:raise ValueError('Each applicable password surface requires below/at/above minimum test IDs')
 ids=[test_id for cases in tests.values() if cases is not None for test_id in cases.values()]
 if len(ids)!=len(set(ids)):raise ValueError('Password boundary test IDs must identify each surface/case uniquely')
def authentication_policy(d):
 if d.get('plan_version') not in ['3','4']:
  if 'authentication' in d:raise ValueError('Legacy plan cannot adopt authentication policy implicitly; use plan v3')
  return {'status':'legacy-not-checked','required':None}
 a=d.get('authentication')
 if not isinstance(a,dict) or type(a.get('required')) is not bool:raise ValueError('Authentication required by default: explicit plan v3 definition required')
 tests=a.get('test_ids')
 if not isinstance(tests,dict) or set(tests)!=set(AUTH_TEST_GROUPS):raise ValueError('Authentication acceptance groups required')
 if a['required']:
  if a.get('status')!='specified' or not nonempty(a.get('approach')) or not string_list(a.get('roles')) or not string_list(a.get('protected_resources')) or a.get('exception') is not None:raise ValueError('Authentication approach, roles and protected resources required before architecture/readiness')
  if not all(string_list(tests[g]) for g in AUTH_TEST_GROUPS):raise ValueError('Authentication tests required: unauthenticated, sessions/logout and authorization')
 else:
  e=a.get('exception')
  if a.get('status')!='exempted' or not isinstance(e,dict) or e.get('requested_by')!='user' or e.get('omit_authentication') is not True or not nonempty(e.get('request_ref')) or not nonempty(e.get('reason')):raise ValueError('Omitting authentication requires explicit user request and recorded exception')
  if a.get('approach') is not None or a.get('roles')!=[] or a.get('protected_resources')!=[] or any(tests[g]!=[] for g in AUTH_TEST_GROUPS):raise ValueError('Exempted authentication must not claim implementation or auth tests')
 validate_password_policy(d,a)
 return a
class RepairLimitExceeded(ValueError):pass
def repair_policy(d):
 version=d.get('plan_version')
 if version=='1':
  if 'execution' in d:raise ValueError('Legacy plan v1 cannot override repair policy; explicitly adopt plan v2')
  return {'max_repairs':1,'source':'legacy-plan-v1'}
 if version not in ['2','3','4']:raise ValueError('Unsupported plan version')
 execution=d.get('execution')
 if not isinstance(execution,dict):raise ValueError('Plan v2 execution policy required')
 limit=execution.get('max_repairs')
 if type(limit) is not int or not 0<=limit<=2:raise ValueError('Plan v2 execution.max_repairs must be an integer from 0 to 2')
 return {'max_repairs':limit,'source':'plan-v'+version}
def validate_round(planning,current_round):
 policy=planning['repair_policy'];limit=policy['max_repairs']
 if current_round is None and policy['source']=='legacy-plan-v1':current_round=0
 if type(current_round) is not int or current_round<0:raise ValueError('Explicit nonnegative --round required for inference with plan v2')
 if current_round>limit:raise RepairLimitExceeded('Repair limit exhausted: blocked; escalate to user before another attempt')
 return {'round':current_round,'max_repairs':limit,'repairs_remaining_after_round':limit-current_round,'counter_authority':'protected-coordinator-history'}
def validate_plan(path,require_design=True):
 p=P(path).resolve();d=json.loads(p.read_text())
 policy=repair_policy(d);authentication=authentication_policy(d)
 choice=d.get('destination',{})
 if choice.get('mode') not in DESTINATIONS or choice.get('approved_by')!='user' or not choice.get('approval_ref'):raise ValueError('Explicit user destination choice required before architecture/implementation')
 stack=d.get('stack',{});exception=stack.get('exception')
 compatible=stack.get('baseline')=='cloudflare' and stack.get('local_runner')=='wrangler'
 if not compatible and not (isinstance(exception,dict) and exception.get('approved_by')=='user' and exception.get('approval_ref') and exception.get('reason')):raise ValueError('Cloudflare-compatible baseline and Wrangler local required, or explicit approved incompatibility exception')
 ai=d.get('runtime_ai',{})
 if type(ai.get('enabled')) is not bool:raise ValueError('Runtime AI decision required')
 if ai['enabled'] and ai.get('gateway')!='openrouter':raise ValueError('Runtime app LLM gateway must be openrouter; coder provider is separate')
 if not ai['enabled'] and ai.get('gateway') is not None:raise ValueError('Non-LLM runtime has no gateway')
 if type(d.get('ui')) is not bool:raise ValueError('UI decision required')
 if d['ui'] and require_design:
  design=d.get('design',{});options=design.get('options',[]);selected=design.get('selected');keys=set()
  if len(options)<2 or not selected or not design.get('approval_ref') or design.get('approved_by')!='user':raise ValueError('Two mockup options and explicit current user choice required')
  for opt in options:
   key=(opt.get('id'),opt.get('version'))
   if not all(isinstance(x,str) and x for x in key) or key in keys:raise ValueError('Unique option/version required')
   keys.add(key);assets=opt.get('assets',[])
   if not {'desktop','mobile'} <= {a.get('viewport') for a in assets}:raise ValueError('Each option requires desktop/mobile mockups')
   for a in assets:
    rel=P(a.get('path',''))
    if not a.get('state') or rel.is_absolute() or not rel.parts or '..' in rel.parts:raise ValueError('Invalid mockup state/path')
    f=p.parent/rel
    if any(q.is_symlink() for q in [f,*f.parents]) or not f.resolve().is_relative_to(p.parent) or not f.is_file():raise ValueError('Mockup must be a regular protected local file')
    if hashlib.sha256(f.read_bytes()).hexdigest()!=a.get('sha256'):raise ValueError('Mockup changed; approval invalidated')
  if (selected.get('id'),selected.get('version')) not in keys:raise ValueError('Selected option/version missing or stale')
 return {'password_policy_checked':d.get('plan_version')=='4','authentication':authentication,'repair_policy':policy,'destination':choice['mode'],'cloudflare_baseline':compatible,'runtime_ai':ai,'ui':d['ui'],'design_checked':bool(d['ui'] and require_design),'plan_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('plan');ap.add_argument('--preflight-only',action='store_true');a=ap.parse_args()
 try:r=validate_plan(a.plan,not a.preflight_only);print(json.dumps({'ready':True,**r}));return 0
 except (ValueError,OSError,TypeError) as e:print(json.dumps({'ready':False,'reason':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
