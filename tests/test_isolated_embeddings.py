import os,sys,json,subprocess
from pathlib import Path
import pytest
IDENTITY='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
@pytest.fixture
def ctx(tmp_path,monkeypatch):
 root=Path(os.environ['GWA_ISOLATED_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import isolated_embeddings as m
 model=tmp_path/'model';model.mkdir();manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps({'model_id':IDENTITY.split('@')[0],'revision':IDENTITY.split('@')[1],'files':{}}));calls=[]
 class Fake:
  pid=234567;returncode=0
  def __init__(self,argv,**kw):self.kw=kw;self.argv=argv;calls.append(self)
  def communicate(self,input=None,timeout=None):
   self.input=input;payload=json.loads(input);self.timeout=timeout;return json.dumps({'ok':True,'identity':IDENTITY,'pid':self.pid,'vectors':[[1.]+[0.]*383 for _ in payload['texts']],'faiss_loaded':False,'torch_loaded':True}),''
  def kill(self):self.killed=True;self.returncode=-9
  def wait(self,timeout=None):return self.returncode
 monkeypatch.setattr(m.subprocess,'Popen',Fake)
 yield m,model,manifest,calls,Fake
 sys.path.remove(str(root))

def test_proxy_uses_owned_fresh_python_and_no_native_imports(ctx,monkeypatch):
 m,model,manifest,calls,Fake=ctx;monkeypatch.setenv('OPENROUTER_API_KEY','SYNTHETIC-SECRET');x=m.IsolatedEmbeddings(model,manifest);v=x.encode(['one','two']);assert len(v)==2 and len(v[0])==384 and x.identity==IDENTITY;c=calls[0];assert c.argv[0]==sys.executable and '-I' in c.argv and '-B' in c.argv and Path(c.argv[-1]).name=='embedding_worker.py';assert not c.kw.get('shell',False);assert 'OPENROUTER_API_KEY' not in c.kw['env'] and 'SYNTHETIC-SECRET' not in json.dumps(c.kw);assert c.kw['env']['HF_HUB_OFFLINE']=='1' and c.kw['env']['HF_HUB_DISABLE_IMPLICIT_TOKEN']=='1';assert not any(x=='torch' or x.startswith('faiss') for x in sys.modules)

@pytest.mark.parametrize('field,value',[('identity','wrong-model'),('pid',1),('faiss_loaded',True),('torch_loaded',False),('vectors',[[0.]*384]),('vectors',[[1.]*383]),('vectors',[[float('nan')]+[0.]*383])])
def test_bad_worker_reply_rejected(ctx,monkeypatch,field,value):
 m,model,manifest,calls,Fake=ctx;old=Fake.communicate
 def reply(self,input=None,timeout=None):
  out,err=old(self,input,timeout);d=json.loads(out);d[field]=value;return json.dumps(d),'never expose raw stderr'
 monkeypatch.setattr(Fake,'communicate',reply)
 with pytest.raises(m.EmbeddingWorkerError) as exc:m.IsolatedEmbeddings(model,manifest).encode(['one'])
 assert 'raw stderr' not in str(exc.value) and exc.value.retryable is False

def test_worker_nonzero_does_not_expose_or_retry(ctx,monkeypatch):
 m,model,manifest,calls,Fake=ctx
 def bad(self,input=None,timeout=None):self.returncode=134;return '', 'SYNTHETIC private text'
 monkeypatch.setattr(Fake,'communicate',bad)
 with pytest.raises(m.EmbeddingWorkerError) as exc:m.IsolatedEmbeddings(model,manifest).encode(['one'])
 assert 'SYNTHETIC' not in str(exc.value) and len(calls)==1

def test_timeout_stops_only_owned_worker(ctx,monkeypatch):
 m,model,manifest,calls,Fake=ctx
 def timed(self,input=None,timeout=None):
  if not getattr(self,'killed',False):raise subprocess.TimeoutExpired(self.argv,timeout)
  return '',''
 monkeypatch.setattr(Fake,'communicate',timed)
 with pytest.raises(m.EmbeddingWorkerError):m.IsolatedEmbeddings(model,manifest,timeout_seconds=2).encode(['one'])
 assert len(calls)==1 and calls[0].killed is True

def test_bad_input_never_launches_worker(ctx):
 m,model,manifest,calls,Fake=ctx;x=m.IsolatedEmbeddings(model,manifest)
 for v in [[],[''],'not-a-list']:
  with pytest.raises(ValueError):x.encode(v)
 assert calls==[]
