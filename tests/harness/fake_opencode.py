#!/opt/homebrew/bin/python3
"""Synthetic fixture only. Never calls a provider or reads user authentication."""
import sys,json,os
from http.server import HTTPServer,BaseHTTPRequestHandler
if '--version' in sys.argv:print('opencode v2.0.32');raise SystemExit
if sys.argv[1]=='serve':
 class H(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def response(self,data):self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(data).encode())
  def do_GET(self):
   provider='wrong-provider' if os.environ.get('GWA_FAKE_CASE')=='wrong-model' else 'opencode-go'
   self.response({'data':[{'id':'growwithai-coder','mode':'primary','model':{'id':'deepseek-v4.1-flash','providerID':provider},'permissions':[{'action':'*','resource':'*','effect':'deny'},{'action':'provider.use','resource':'opencode-go','effect':'allow'}]}]})
  def do_POST(self):
   body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));self.response({'id':'ses_fixture1',**body})
 HTTPServer(('127.0.0.1',int(sys.argv[sys.argv.index('--port')+1])),H).serve_forever()
elif sys.argv[1]=='run':
 if os.environ.get('GWA_FAKE_CASE')=='tool':print(json.dumps({'type':'tool','sessionID':'ses_fixture1','part':{'type':'tool'}}))
 else:print(json.dumps({'type':'text','sessionID':'ses_fixture1','part':{'id':'p1','type':'text','text':'{"files":[{"path":"app/config.py","content":"# fixture only\\n"}]}'}}))
else:raise SystemExit(2)
