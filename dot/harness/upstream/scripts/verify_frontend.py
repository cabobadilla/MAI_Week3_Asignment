#!/usr/bin/env python3
"""Trusted verifier for static-browser-only candidates. No candidate code runs in Node."""
import argparse,base64,datetime,fcntl,hashlib,json,os,pathlib,re,signal,socket,subprocess,tempfile,time,urllib.request,stat
P=pathlib.Path
ALLOWED={'public/index.html','public/styles.css','public/app.mjs','public/questionnaire.mjs','public/scoring.mjs'}
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def tree(root):
 root=P(root).resolve();items=[]
 for p in sorted(root.rglob('*'),key=lambda x:x.relative_to(root).as_posix().encode()):
  if p.is_symlink():
   if not p.resolve().is_relative_to(root):raise ValueError('External symlink in protected runtime')
   items.append((p.relative_to(root).as_posix(),'link:'+os.readlink(p)))
  elif p.is_file():items.append((p.relative_to(root).as_posix(),sha(p)))
 return hashlib.sha256(''.join(a+'\t'+b+'\n' for a,b in items).encode()).hexdigest()
def git(repo,*args):return subprocess.run(['git','-C',str(repo),*args],capture_output=True,check=True).stdout

def clean(repo,c):
 if git(repo,'rev-parse','HEAD').decode().strip()!=c['candidate_sha']:raise ValueError('Candidate HEAD changed')
 if git(repo,'status','--porcelain=v2','-z','--untracked-files=all'):raise ValueError('Dirty/untracked worktree')
 ignored=git(repo,'ls-files','--others','--ignored','--exclude-standard','-z').decode().split('\0');actual={};incidental={}
 policy=c.get('incidental_metadata_policy')
 if policy is not None and policy!='record-ds-store-outside-public-v1':raise ValueError('Unknown incidental metadata policy')
 for n in ignored:
  if not n:continue
  p=repo/n
  if policy and p.name=='.DS_Store':
   info=p.lstat()
   if n.startswith('public/') or not stat.S_ISREG(info.st_mode) or p.is_symlink() or info.st_nlink!=1 or info.st_mode&0o111 or info.st_size>2_000_000 or p.read_bytes()[:8]!=b'\x00\x00\x00\x01Bud1':raise ValueError('Invalid/out-of-artifact metadata exception: '+n)
   incidental[n]=sha(p)
  else:actual[n]=sha(p)
 if actual!=c.get('baseline_ignored',{}):raise ValueError('Unexpected ignored content')
 return incidental

def stop(p):
 if p and p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()

def collect(s,found):
 for spec in s.get('specs',[]):
  for t in spec.get('tests',[]):found.append((t['projectName'],spec['title'],t))
 for sub in s.get('suites',[]):collect(sub,found)

def run(contract):
 c=json.loads(P(contract).read_text());repo=P(c['repo']).resolve();bundle=P(c['bundle']).resolve();runtime=P(c['runtime']).resolve();browser=P(c['browser']).resolve();out=P(c['out']).resolve()
 if c['kind']!='static-browser-only' or c['phase'] not in ['development','independent_final']:raise ValueError('Unsupported kind/phase')
 for n in ['base_sha','candidate_sha']:
  if not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',c[n]):raise ValueError('Full Git SHA required')
 if set(c['allowed_files'])!=ALLOWED:raise ValueError('Static file-map scope must be explicit and exact')
 if out.is_relative_to(repo) or out.is_relative_to(bundle) or out.is_relative_to(runtime):raise ValueError('Evidence must be outside protected/candidate roots')
 if out.exists():raise ValueError('Evidence path already exists; reconcile rather than rerun')
 incidental_before=clean(repo,c)
 if c.get('require_external_controls') and (bundle.is_relative_to(repo) or runtime.is_relative_to(repo)):raise ValueError('Controls must be frozen outside candidate worktree')
 if tree(bundle)!=c['bundle_sha256'] or tree(runtime)!=c['runtime_sha256'] or sha(browser)!=c['browser_sha256']:raise ValueError('Protected input hash mismatch')
 for p,h in c['inputs'].items():
  if sha(p)!=h:raise ValueError('Spec/acceptance input changed: '+p)
 changes=set(git(repo,'diff','--no-renames','--name-only','-z',c['base_sha'],c['candidate_sha']).decode().strip('\0').split('\0'))-{''}
 if not changes<=ALLOWED:raise ValueError('Candidate changes protected/out-of-scope paths: '+repr(sorted(changes-ALLOWED)))
 out.mkdir(parents=True);scratch=out/'scratch';scratch.mkdir();export=out/'candidate';export.mkdir()
 for record in git(repo,'ls-tree','-rz','--full-tree',c['candidate_sha']).split(b'\0'):
  if not record:continue
  meta,name=record.split(b'\t',1);mode,kind,oid=meta.decode().split();n=name.decode();p=export/n
  if kind!='blob' or mode not in ['100644','100755'] or P(n).is_absolute() or '..' in P(n).parts:raise ValueError('Unsupported candidate tree entry')
  if n in ALLOWED and mode!='100644':raise ValueError('Executable static source rejected')
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(git(repo,'cat-file','blob',oid))
 if not all((export/n).is_file() for n in ALLOWED):raise ValueError('Candidate app files missing')
 export_hash=tree(export)
 if {p.relative_to(export).as_posix() for p in (export/'public').rglob('*') if p.is_file()}!=ALLOWED:raise ValueError('Unexpected static asset/worker source')
 # Pure scoring unit tests execute in a browser module host, never through Node imports.
 package=json.loads((runtime/'node_modules/@playwright/test/package.json').read_text());assert package['version']==c['playwright_version']
 inventory=json.loads((bundle/'expected-tests.json').read_text());expected={(p,t) for p in ['desktop','mobile'] for t in inventory['survey']}
 sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();url=f'http://127.0.0.1:{port}'
 env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','HOME':str(scratch),'TMPDIR':str(scratch),'CI':'1','WRANGLER_SEND_METRICS':'false'}
 config=scratch/'wrangler.json';config.write_text(json.dumps({'name':'genai-value-survey-local-verification','compatibility_date':'2026-09-01','assets':{'directory':str(export/'public')}}))
 sl=(out/'server.log').open('w');server=None;runner=None;manifest={'run_id':c['run_id'],'phase':c['phase'],'kind':c['kind'],'repo':str(repo),'base_sha':c['base_sha'],'candidate_sha':c['candidate_sha'],'contract_sha256':sha(contract),'bundle_sha256':c['bundle_sha256'],'runtime_sha256':c['runtime_sha256'],'browser_sha256':c['browser_sha256'],'inputs':c['inputs'],'protected_roots':{'bundle':str(bundle),'runtime':str(runtime),'browser':str(browser)},'baseline_ignored':c.get('baseline_ignored',{}),'incidental_metadata_policy':c.get('incidental_metadata_policy'),'incidental_before':incidental_before,'export_sha256':export_hash,'delivery_accepted':False,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  server=subprocess.Popen([c['wrangler'],'dev','--local','--ip','127.0.0.1','--port',str(port),'--config',str(config)],cwd=str(scratch),env=env,stdout=sl,stderr=sl,start_new_session=True)
  deadline=time.monotonic()+30
  while True:
   if server.poll() is not None:raise RuntimeError('Local Wrangler exited; see server.log')
   try:
    urllib.request.urlopen(url,timeout=1).close();break
   except Exception:
    if time.monotonic()>deadline:raise TimeoutError('Local server readiness timeout')
    time.sleep(.2)
  env.update({'DOT_PLAYWRIGHT_MODULE':str(runtime/'node_modules/@playwright/test'),'DOT_OUT':str(out),'DOT_BASE_URL':url,'DOT_BROWSER':str(browser),'DOT_RUN_ID':c['run_id'],'DOT_PHASE':c['phase'],'DOT_SUITE':'survey','DOT_CANDIDATE_SHA':c['candidate_sha']})
  args=[c['node'],str(runtime/'node_modules/@playwright/test/cli.js'),'test','-c',str(bundle/'playwright.config.cjs')];manifest['argv']=args
  runner=subprocess.Popen(args,cwd=str(bundle),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try:stdout,stderr=runner.communicate(timeout=300)
  except subprocess.TimeoutExpired:stop(runner);stdout,stderr=runner.communicate();raise TimeoutError('Playwright global timeout')
  (out/'runner.stdout.log').write_text(stdout);(out/'runner.stderr.log').write_text(stderr);manifest['process_exit']=runner.returncode
  report=json.loads((out/'report.json').read_text());found=[];collect(report,found)
  actual=[(p,t) for p,t,_ in found];manifest['expected_tests']=sorted(expected);manifest['executed_tests']=actual
  if len(actual)!=len(set(actual)) or set(actual)!=expected:raise ValueError('Missing, duplicate or unexpected test IDs/projects')
  passed=True
  for project,title,t in found:
   if t.get('status')!='expected' or t.get('expectedStatus')!='passed' or len(t.get('results',[]))!=1 or t['results'][0].get('status')!='passed':passed=False
   result=t['results'][0];meta=[]
   for a in result.get('attachments',[]):
    if a.get('name')=='runtime-metadata':
     if a.get('path'):meta.append(json.loads(P(a['path']).read_text()))
     elif a.get('body'):meta.append(json.loads(base64.b64decode(a['body'],validate=True)))
   if len(meta)!=1 or meta[0]['candidate_sha']!=c['candidate_sha'] or meta[0]['run_id']!=c['run_id'] or meta[0]['phase']!=c['phase'] or meta[0]['browser']!=c['browser_version']:raise ValueError('Missing/mismatched per-test identity metadata')
   if result.get('status')!='passed' and not any(a.get('name')=='trace' and P(a.get('path','')).is_file() for a in result.get('attachments',[])):raise ValueError('Failure trace missing')
  manifest['incidental_after']=clean(repo,c)
  if tree(export)!=export_hash:raise ValueError('Candidate export changed during tests')
  if tree(bundle)!=c['bundle_sha256'] or tree(runtime)!=c['runtime_sha256'] or sha(browser)!=c['browser_sha256']:raise ValueError('Evaluator inputs changed during run')
  for p,h in c['inputs'].items():
   if sha(p)!=h:raise ValueError('Acceptance inputs changed during run')
  passed=passed and runner.returncode==0 and not report.get('errors');manifest.update({'deterministic_outcome':'pass' if passed else 'fail','state':('review_pending' if c['phase']=='independent_final' else 'development_complete') if passed else 'rejected','browser_version':c['browser_version'],'playwright_version':c['playwright_version']})
 except Exception as e:manifest.update({'deterministic_outcome':'incomplete','state':'blocked','reason':str(e)})
 finally:
  stop(runner);stop(server);sl.close();manifest['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();manifest['artifacts']=[{'path':p.relative_to(out).as_posix(),'sha256':sha(p)} for p in out.rglob('*') if p.is_file() and not p.is_relative_to(export)];(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'manifest':str(out/'manifest.json'),'state':manifest['state'],'deterministic_outcome':manifest['deterministic_outcome'],'delivery_accepted':False}));return 0 if manifest['deterministic_outcome']=='pass' else 1

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--contract');ap.add_argument('--recheck');a=ap.parse_args()
 lockfd=os.open('/tmp/dotharness-executor-'+str(os.getuid())+'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(lockfd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if a.recheck:
  m=json.loads(P(a.recheck).read_text());repo=P(m['repo']);clean(repo,m);roots=m['protected_roots'];valid=tree(roots['bundle'])==m['bundle_sha256'] and tree(roots['runtime'])==m['runtime_sha256'] and sha(roots['browser'])==m['browser_sha256'] and all(sha(p)==h for p,h in m['inputs'].items());print(json.dumps({'evidence_current':bool(valid),'candidate_sha':m['candidate_sha']}));return 0 if valid else 1
 if not a.contract:ap.error('--contract or --recheck required')
 return run(a.contract)
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,RuntimeError,BlockingIOError,subprocess.CalledProcessError) as e:print(json.dumps({'state':'blocked','reason':str(e)}));raise SystemExit(2)
