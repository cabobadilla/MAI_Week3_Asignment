#!/usr/bin/env python3
# Offline test double; never imports/calls OpenCode or an AI provider.
import sys,json,os,http.server,urllib.parse,pathlib
args=sys.argv[1:]
if args==['--version']:print('2.0.32');sys.exit()
agent={'id':'survey-coder','mode':'primary','model':{'id':'deepseek-v4.1-flash','providerID':'opencode-go'},'permissions':[{'action':'*','resource':'*','effect':'deny'},{'action':'provider.use','resource':'opencode-go','effect':'allow'}]}
session={'id':'ses_fixture','location':{'directory':os.getcwd()},'model':agent['model'],'agent':'survey-coder'}
if args[0]=='run':
 pathlib.Path('fixture-run-called').write_text('synthetic only')
 print(json.dumps({'type':'text','sessionID':'ses_fixture','part':{'type':'text','id':'fixture','text':'{}'}}));sys.exit()
assert args[0]=='serve';port=int(args[args.index('--port')+1]);count=0
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  global count
  path=urllib.parse.urlparse(self.path).path
  if path=='/api/agent':count+=1;data={'data':[] if count==1 else [agent]}
  else:data={'data':session}
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(data).encode())
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert data['location']['directory']==os.getcwd();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'data':session}).encode())
http.server.HTTPServer(('127.0.0.1',port),Handler).serve_forever()
