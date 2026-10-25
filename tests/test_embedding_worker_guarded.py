import os,sys,types,importlib,importlib.abc,importlib.util
from pathlib import Path
import pytest
IDENTITY='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
@pytest.fixture
def worker(monkeypatch):
 root=Path(os.environ['GWA_GUARDED_WORKER_CANDIDATE']);old_meta=list(sys.meta_path);old_modules=set(sys.modules)
 for k in list(sys.modules):
  if any(k==n or k.startswith(n+'.') for n in ['torch','faiss','sklearn']):monkeypatch.delitem(sys.modules,k,raising=False)
 spec=importlib.util.spec_from_file_location('_test_guarded_worker',root/'app/embedding_worker.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);assert sys.meta_path==old_meta
 calls=[]
 class F(importlib.abc.MetaPathFinder,importlib.abc.Loader):
  def find_spec(self,fullname,path=None,target=None):
   if fullname in ['torch','faiss','sklearn']:return importlib.util.spec_from_loader(fullname,self)
  def create_module(self,spec):return types.ModuleType(spec.name)
  def exec_module(self,module):calls.append(module.__name__)
 sys.meta_path.insert(0,F())
 yield m,calls
 sys.meta_path[:]=old_meta
 for key in set(sys.modules)-old_modules:
  module=sys.modules.get(key);file=getattr(module,'__file__','') or ''
  if file==str(root/'app/native_runtime_guard.py') or key in ['torch','faiss','sklearn']:sys.modules.pop(key,None)

def fake_local():
 class Local:
  identity=IDENTITY
  def __init__(self,model,manifest):pass
  def encode(self,texts):return [[1.]+[0.]*383 for _ in texts]
 return types.SimpleNamespace(LocalEmbeddings=Local)

def test_guard_precedes_loader_and_blocks_both_opposing_packages(worker,monkeypatch,tmp_path):
 m,calls=worker;observed=[]
 def loader():
  for name in ['faiss','sklearn']:
   with pytest.raises(ImportError):importlib.import_module(name)
   observed.append(name)
  importlib.import_module('torch');return fake_local()
 monkeypatch.setattr(m,'_load_local_embeddings',loader);vectors=m._run_embedding(['Synthetic'],tmp_path,tmp_path/'manifest.json')
 assert len(vectors)==1 and len(vectors[0])==384 and observed==['faiss','sklearn'] and calls==['torch']

@pytest.mark.parametrize('present',['faiss.external','sklearn'])
def test_existing_conflict_stops_before_local_loader(worker,monkeypatch,tmp_path,present):
 m,calls=worker;monkeypatch.setitem(sys.modules,present,types.ModuleType(present));loaded=[];monkeypatch.setattr(m,'_load_local_embeddings',lambda:loaded.append(True))
 with pytest.raises((ImportError,RuntimeError)):m._run_embedding(['Synthetic'],tmp_path,tmp_path/'m.json')
 assert loaded==[] and calls==[]

def test_import_during_encode_fails_before_fake_native_loader(worker,monkeypatch,tmp_path):
 m,calls=worker
 class Bad:
  identity=IDENTITY
  def __init__(self,*args):pass
  def encode(self,texts):importlib.import_module('sklearn');return [[1.]+[0.]*383]
 monkeypatch.setattr(m,'_load_local_embeddings',lambda:types.SimpleNamespace(LocalEmbeddings=Bad))
 with pytest.raises(ImportError):m._run_embedding(['Synthetic'],tmp_path,tmp_path/'m.json')
 assert calls==[]
