"""Temporary trusted supervisor: GO-only file-map, no native tools. No app code."""
from pathlib import Path
import argparse,json,subprocess,os,socket,secrets,base64,urllib.request,urllib.parse,time,signal,hashlib
GO='opencode-go/deepseek-v4.1-flash';AGENT='growwithai-coder';BINARY=os.environ.get('GWA_TEST_FAKE_CLI','/Users/bobadillachristian/.opencode/bin/opencode')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--prompt');ap.add_argument('--preflight-only',action='store_true');a=ap.parse_args()
 out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);cwd=out/'coder';cwd.mkdir();pw=secrets.token_urlsafe(32)
 rules=[{'action':'*','resource':'*','effect':'deny'},{'action':'provider.use','resource':'opencode-go','effect':'allow'}]
 config={'$schema':'https://opencode.ai/config.json','model':GO,'small_model':GO,'permission':'deny','agent':{AGENT:{'description':'Scoped file-map-only Python coder; no tools','mode':'primary','model':GO,'permission':{'*':'deny','provider.use':{'opencode-go':'allow'}}}}}
 (cwd/'opencode.json').write_text(json.dumps(config))
 env={k:os.environ[k] for k in ['HOME','USER','TMPDIR','LANG'] if k in os.environ};env.update({'PATH':'/opt/homebrew/bin:/usr/bin:/bin','PWD':str(cwd),'OPENCODE_PASSWORD':pw,'OPENCODE_SERVER_PASSWORD':pw,'OPENCODE_DISABLE_CLAUDE_CODE':'1','OPENCODE_DISABLE_CLAUDE_CODE_SKILLS':'1','OPENCODE_DISABLE_AUTOUPDATE':'1'})
 env['GWA_FAKE_CASE']=os.environ.get('GWA_FAKE_CASE','valid') if os.environ.get('GWA_TEST_FAKE_CLI') else '';s=socket.socket();s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close();url=f'http://127.0.0.1:{port}'
 auth='Basic '+base64.b64encode(('opencode:'+pw).encode()).decode();server=None;client=None
 report={'model_requested':GO,'agent':AGENT,'cwd':str(cwd),'port':port,'server_owned':True,'inference_submitted':False,'process_outcome':'started','application_llm_calls':False,'execution_mode':'fake-cli' if os.environ.get('GWA_TEST_FAKE_CLI') else 'real-go-no-tools'}
 def req(path,body=None):
  return json.load(urllib.request.urlopen(urllib.request.Request(url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':auth,'Content-Type':'application/json','x-opencode-directory':urllib.parse.quote(str(cwd),safe='')}),timeout=5))
 def effect(agent,action,resource):
  import fnmatch
  result='allow'
  for r in agent['permissions']:
   if fnmatch.fnmatchcase(action,r['action']) and fnmatch.fnmatchcase(resource,r['resource']):result=r['effect']
  return result
 def stop(proc):
  if proc is not None and proc.poll() is None:
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=4)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 def clean(s):return s.replace(pw,'[EPHEMERAL-REDACTED]')
 try:
  ver=subprocess.run([BINARY,'--version'],cwd=cwd,env=env,capture_output=True,text=True,timeout=10,check=True).stdout.strip();assert ver=='opencode v2.0.32',ver
  report['version']=ver;report['binary_sha256']=hashlib.sha256(Path(BINARY).read_bytes()).hexdigest()
  server=subprocess.Popen([BINARY,'serve','--hostname','127.0.0.1','--port',str(port)],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  report['server_pid']=server.pid;agent=None;end=time.monotonic()+30
  while time.monotonic()<end:
   if server.poll() is not None:raise RuntimeError('Owned server exited before readiness')
   try:
    data=req('/api/agent?'+urllib.parse.urlencode({'location[directory]':str(cwd)}));agent=next((x for x in data.get('data',[]) if x['id']==AGENT),None)
    if agent:break
   except Exception:pass
   time.sleep(.25)
  if not agent:raise RuntimeError('Named scoped agent not ready')
  assert agent['mode']=='primary' and agent['model']=={'id':'deepseek-v4.1-flash','providerID':'opencode-go'},'Unexpected effective model'
  for action in ['read','edit','shell','subagent','browser','webfetch','websearch','question','external_directory','tool.*']:assert effect(agent,action,'*')=='deny',action
  assert effect(agent,'provider.use','opencode-go')=='allow' and effect(agent,'provider.use','other')=='deny','Provider permission mismatch'
  report['effective_agent']=agent
  sess=req('/api/session',{'title':'GrowWithAI scoped backend task','agent':AGENT,'model':{'id':'deepseek-v4.1-flash','providerID':'opencode-go'},'location':{'directory':str(cwd)},'permissions':rules});sess=sess.get('data',sess)
  assert sess['location']['directory']==str(cwd) and sess['agent']==AGENT and sess['model']['providerID']=='opencode-go' and sess['model']['id']=='deepseek-v4.1-flash'
  report['session_id']=sess['id'];report['effective_model']=sess['model'];report['native_tools']='all_denied'
  if a.preflight_only:report['process_outcome']='preflight_pass';return 0
  if not a.prompt:raise RuntimeError('Prompt file required')
  prompt=Path(a.prompt).read_text();report['prompt_sha256']=hashlib.sha256(prompt.encode()).hexdigest();report['inference_submitted']=not bool(os.environ.get('GWA_TEST_FAKE_CLI'));(out/'state.json').write_text(json.dumps({'stage':'coder_request','session_id':sess['id'],'model':GO,'execution_mode':report['execution_mode']}))
  client=subprocess.Popen([BINARY,'run','--server',url,'--agent',AGENT,'--model',GO,'--session',sess['id'],'--format','json',prompt],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try:stdout,stderr=client.communicate(timeout=600)
  except subprocess.TimeoutExpired:stop(client);raise RuntimeError('Coder timeout; reconcile this run before retry')
  report['cli_exit']=client.returncode;textparts={};events=[]
  for ln in stdout.splitlines():
   try:e=json.loads(ln)
   except ValueError:continue
   typ=e.get('type','');part=e.get('part',{})
   if e.get('sessionID') not in [None,sess['id']]:raise RuntimeError('Unexpected session id')
   if 'reasoning' in typ or part.get('type')=='reasoning':continue
   if 'tool' in typ or part.get('type') in ['tool','tool-invocation']:raise RuntimeError('Unexpected native tool event')
   if typ=='error':raise RuntimeError('Coder returned an error; inspect sanitized metadata')
   if typ=='text' or part.get('type')=='text':textparts[part.get('id') or str(len(textparts))]=part.get('text',e.get('text',''))
   events.append(e)
  response='\n'.join(textparts.values());(out/'response.txt').write_text(response);(out/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events));(out/'stderr.log').write_text(clean(stderr))
  if client.returncode or not response:raise RuntimeError('No successful file-map response')
  report['response_sha256']=hashlib.sha256(response.encode()).hexdigest();report['process_outcome']='response_received';report['delivery_outcome']='not_accepted_pending_guard_and_tests'
  return 0
 except Exception as e:report['process_outcome']='blocked';report['reason']=clean(str(e));return 1
 finally:
  stop(client);stop(server)
  if server:
   so,se=server.communicate();(out/'server.log').write_text(clean(so+'\n'+se))
  report['server_stopped']=server is None or server.poll() is not None;(out/'request.json').write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps({k:report.get(k) for k in ['process_outcome','reason','model_requested','effective_model','native_tools','inference_submitted','server_stopped']}),flush=True)
if __name__=='__main__':raise SystemExit(main())
