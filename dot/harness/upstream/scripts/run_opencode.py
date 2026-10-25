#!/usr/bin/env python3
"""One primary GO-only request through an owned, ready private v2 server."""
import argparse,base64,hashlib,fcntl,fnmatch,json,os,pathlib,re,secrets,selectors,signal,socket,subprocess,time,urllib.request,urllib.parse
from check_plan import validate_plan,validate_round,RepairLimitExceeded
P=pathlib.Path;MODEL='opencode-go/deepseek-v4.1-flash'
LOCK_PATH=P('/tmp')/('dotharness-executor-'+str(os.getuid())+'.lock')
def kill(p):
 if p and p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=4)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def validate_agent(agent):
 if not agent or agent.get('mode')!='primary' or agent.get('model')!={'id':'deepseek-v4.1-flash','providerID':'opencode-go'}:raise RuntimeError('Unexpected primary/model')
 def effect(action,resource):
  result='allow'
  for r in agent.get('permissions',[]):
   if fnmatch.fnmatchcase(action,r['action']) and fnmatch.fnmatchcase(resource,r['resource']):result=r['effect']
  return result
 for action in ['read','edit','shell','subagent','browser','webfetch','websearch','question','external_directory']:
  if effect(action,'*')!='deny':raise RuntimeError('Unexpected tool permission: '+action)
 if effect('provider.use','opencode-go')!='allow' or effect('provider.use','other')!='deny':raise RuntimeError('Provider allowlist mismatch')
def validate_session(session,cwd):
 if not re.fullmatch(r'ses[A-Za-z0-9_]+',session.get('id','')):raise RuntimeError('Invalid owned session ID')
 if session.get('location',{}).get('directory')!=str(P(cwd).resolve()):raise RuntimeError('Session location mismatch before inference')
 model=session.get('model',{})
 if model.get('id')!='deepseek-v4.1-flash' or model.get('providerID')!='opencode-go' or model.get('variant') not in [None,'default'] or session.get('agent')!='survey-coder':raise RuntimeError('Owned session agent/model mismatch')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--plan',required=True);ap.add_argument('--preflight-only',action='store_true');ap.add_argument('--round',type=int);ap.add_argument('--expected-version',default='2.0.32');ap.add_argument('--opencode',required=True);ap.add_argument('--cwd',required=True);ap.add_argument('--prompt',required=True);ap.add_argument('--out',required=True);ap.add_argument('--timeout',type=int,default=600);a=ap.parse_args();out=P(a.out).resolve();out.mkdir(exist_ok=False);cwd=P(a.cwd).resolve();prompt=P(a.prompt).read_text();lock=os.open(LOCK_PATH,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 port=None;password=secrets.token_urlsafe(24);env=os.environ.copy();env.update({'PWD':str(cwd),'OPENCODE_PASSWORD':password,'OPENCODE_SERVER_PASSWORD':password,'OPENCODE_DISABLE_CLAUDE_CODE':'1','OPENCODE_DISABLE_CLAUDE_CODE_SKILLS':'1'});url=None;auth='Basic '+base64.b64encode(('opencode:'+password).encode()).decode();server=None;client=None;report={'driver_sha256':hashlib.sha256(P(__file__).read_bytes()).hexdigest(),'prompt_sha256':hashlib.sha256(P(a.prompt).read_bytes()).hexdigest(),'cwd':str(cwd),'requested_model':MODEL,'agent':'survey-coder','inference_text_observed':False,'cost':'not_reported','server_owned':True,'fallback_allowed':False};parts={};events=[];sid=None
 seq_state=0;phase_started=time.monotonic()
 def progress(phase,**extra):
  nonlocal seq_state
  seq_state+=1;event={'seq':seq_state,'phase':phase,'elapsed_seconds':round(time.monotonic()-phase_started,2),'run_id':out.name,**extra};tmp=out/'.state.tmp'
  with tmp.open('w') as f:json.dump(event,f);f.flush();os.fsync(f.fileno())
  os.replace(tmp,out/'state.json')
  with (out/'progress.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
  print(json.dumps(event),flush=True)
 def request(path,body=None):return json.load(urllib.request.urlopen(urllib.request.Request(url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':auth,'Content-Type':'application/json','x-opencode-directory':urllib.parse.quote(str(cwd),safe='')}),timeout=5))
 def clean(s):return re.sub(r'(?i)(bearer\s+|api[_-]?key[=: ]+|sk-)[A-Za-z0-9_./+-]+',r'\1[REDACTED]',s.replace(password,'[REDACTED]'))
 try:
  progress('preflight')
  report['planning']=validate_plan(a.plan,require_design=not a.preflight_only)
  report['declared_round']=a.round
  if not a.preflight_only:report['repair_budget']=validate_round(report['planning'],a.round)
  version=subprocess.run([a.opencode,'--version'],cwd=cwd,env=env,capture_output=True,text=True,timeout=5,check=True).stdout.strip().removeprefix('v')
  if version!=a.expected_version or version!='2.0.32':raise RuntimeError('Unsupported OpenCode version; adapter verified only for 2.0.32')
  report['opencode_version']=version;report['opencode_sha256']=hashlib.sha256(P(a.opencode).read_bytes()).hexdigest()
  s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close();url=f'http://127.0.0.1:{port}';progress('agent_readiness')
  server=subprocess.Popen([a.opencode,'serve','--hostname','127.0.0.1','--port',str(port)],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True);deadline=time.monotonic()+30;counts=[];agent=None
  while time.monotonic()<deadline:
   try:
    v=request('/api/agent?'+urllib.parse.urlencode({'location[directory]':str(cwd)}));counts.append(len(v.get('data',[])));agent=next((x for x in v.get('data',[]) if x['id']=='survey-coder'),None)
    if agent:break
   except Exception:pass
   if server.poll() is not None:raise RuntimeError('Owned server exited during readiness')
   time.sleep(.2)
  if not agent:raise RuntimeError('Agent readiness timeout; no inference submitted')
  validate_agent(agent)
  report['ready_agent']=agent;report['readiness_counts']=counts;(out/'readiness.json').write_text(json.dumps({'counts':counts,'agent':agent},indent=2)+'\n');print('READY: primary survey-coder, GO exact, native tools denied',flush=True)
  progress('session_binding',readiness_counts=counts)
  payload={'title':'GenAI survey '+out.name,'agent':'survey-coder','model':{'id':'deepseek-v4.1-flash','providerID':'opencode-go'},'location':{'directory':str(cwd)},'permissions':[{'action':'*','resource':'*','effect':'deny'},{'action':'provider.use','resource':'opencode-go','effect':'allow'}]};(out/'create-session-intent.json').write_text(json.dumps(payload,indent=2)+'\n');created=request('/api/session',payload);created=created.get('data',created);sid=created['id'];report['created_session']={k:created[k] for k in ['id','location','model','agent'] if k in created}
  validate_session(created,cwd)
  progress('session_bound',session_id=sid)
  if a.preflight_only:
   report['status']='preflight_complete';report['inference_submitted']=False;return 0
  report['inference_submitted']=True;progress('inference',session_id=sid)
  args=[a.opencode,'run','--server',url,'--agent','survey-coder','--model',MODEL,'--title','GenAI survey bounded implementation','--session',sid,'--format','json',prompt];client=subprocess.Popen(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);sel=selectors.DefaultSelector();sel.register(client.stdout,selectors.EVENT_READ,'stdout');sel.register(client.stderr,selectors.EVENT_READ,'stderr');buffers={'stdout':b'','stderr':b''};stderr=[];start=time.monotonic();last=start;seq=0
  def line(text,kind):
   nonlocal sid,seq
   if kind=='stderr':stderr.append(clean(text));return
   try:e=json.loads(text)
   except Exception:events.append({'type':'unparsed','text':clean(text)[:1000]});return
   typ=e.get('type','');p=e.get('part',{});event_sid=e.get('sessionID');
   if event_sid and sid and event_sid!=sid:raise RuntimeError('CLI session identity changed')
   sid=event_sid or sid
   if 'reasoning' in typ or p.get('type')=='reasoning':return
   if typ=='error':report['error']=e.get('error');events.append(e);return
   if 'tool' in typ or p.get('type') in ['tool','tool-invocation']:report['tool_event']=True
   if typ=='text' or p.get('type')=='text':
    text=p.get('text',e.get('text',''));key=p.get('id') or str(seq);parts[key]=text;seq+=1
   events.append(e)
  while sel.get_map():
   if time.monotonic()-start>min(a.timeout,600):report['timeout']=True;kill(client);break
   for key,_ in sel.select(timeout=1):
    chunk=os.read(key.fileobj.fileno(),65536)
    if not chunk:sel.unregister(key.fileobj);continue
    kind=key.data;buffers[kind]+=chunk
    while b'\n' in buffers[kind]:
     raw,buffers[kind]=buffers[kind].split(b'\n',1);line(raw.decode(errors='replace'),kind)
   if time.monotonic()-last>20:progress('inference',session_id=sid,wait_seconds=round(time.monotonic()-start),text_characters=sum(map(len,parts.values())));last=time.monotonic()
  for kind,b in buffers.items():
   if b:line(b.decode(errors='replace'),kind)
  client.wait(timeout=5);report['cli_exit']=client.returncode;report['seconds']=round(time.monotonic()-start,2);report['session_id']=sid;report['inference_text_observed']=bool(parts);text='\n'.join(parts.values());(out/'response.txt').write_text(text);(out/'events.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in events));(out/'stderr.log').write_text('\n'.join(stderr))
  if sid and re.fullmatch(r'ses[A-Za-z0-9_]+',sid):
   info=request('/api/session/'+sid);info=info.get('data',info);report['session_metadata']={k:info[k] for k in ['id','location','model','agent','cost','usage','tokens'] if k in info}
  if client.returncode!=0 or report.get('error') or report.get('tool_event') or report.get('timeout'):raise RuntimeError('CLI request incomplete/error/tool event; inspect report, no file map accepted')
  if not text:raise RuntimeError('No text response received')
  if hashlib.sha256(P(a.plan).read_bytes()).hexdigest()!=report['planning']['plan_sha256']:raise RuntimeError('Planning input changed during request')
  report['status']='response_received';print('RESPONSE received: '+str(len(text))+' characters',flush=True)
 except Exception as e:
  report['status']='blocked';report['reason']=clean(str(e));report['escalation_required']=isinstance(e,RepairLimitExceeded);print('BLOCKED: '+report['reason'],flush=True)
 finally:
  kill(client);kill(server)
  if server:
   so,se=server.communicate();(out/'server.log').write_text(clean(so+'\n'+se))
  progress(report.get('status','blocked'),server_stopped=server is None or server.poll() is not None,escalation_required=report.get('escalation_required',False))
  report['execution_mode']='metadata-preflight' if a.preflight_only else 'file-map-no-tools';report['requested_by']='operator';report['test_execution']='not_run_by_this_adapter';report['server_stopped']=server is None or server.poll() is not None;(out/'request.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report.get(k) for k in ['status','reason','requested_model','inference_text_observed','session_id','seconds','cli_exit','cost','server_stopped']},ensure_ascii=False),flush=True)
 return 0 if report['status'] in ['response_received','preflight_complete'] else 1
if __name__=='__main__':raise SystemExit(main())
