import os,sys,types,importlib,importlib.abc,importlib.util
from pathlib import Path
import pytest
@pytest.fixture
def env(monkeypatch):
 root=Path(os.environ['GWA_VECTOR_GUARD_CANDIDATE']);monkeypatch.syspath_prepend(str(root));prior=list(sys.meta_path)
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.') or any(k==n or k.startswith(n+'.') for n in ['numpy','faiss','torch','sklearn','sentence_transformers']):monkeypatch.delitem(sys.modules,k,raising=False)
 calls=[]
 class F(importlib.abc.MetaPathFinder,importlib.abc.Loader):
  def find_spec(self,fullname,path=None,target=None):
   if fullname in ['numpy','faiss','torch']:return importlib.util.spec_from_loader(fullname,self)
  def create_module(self,spec):return types.ModuleType(spec.name)
  def exec_module(self,module):calls.append(module.__name__)
 sys.meta_path.insert(0,F());yield calls
 sys.meta_path[:]=prior
 for n in ['numpy','faiss','torch']:sys.modules.pop(n,None)

def test_clean_vector_import_installs_guard_before_fake_faiss(env):
 calls=env;from app import retrieval,native_runtime_guard
 assert native_runtime_guard.current_role()=='vector' and calls==['faiss','numpy']
 with pytest.raises(native_runtime_guard.NativeRuntimeConflict):importlib.import_module('torch')
 assert calls==['faiss','numpy']

@pytest.mark.parametrize('name',['torch','torch.fake','sentence_transformers','sklearn'])
def test_existing_tensor_or_sklearn_rejected_before_any_native_loader(env,monkeypatch,name):
 monkeypatch.setitem(sys.modules,name,types.ModuleType(name))
 with pytest.raises(ImportError):importlib.import_module('app.retrieval')
 assert env==[]

def test_late_conflict_blocks_vector_build_before_embedder(env,monkeypatch):
 from app import retrieval
 monkeypatch.setitem(sys.modules,'torch.external',types.ModuleType('torch.external'));calls=[]
 class E:
  identity='fake'
  def encode(self,texts):calls.append(texts);return []
 with pytest.raises(ImportError):retrieval.VectorStore.build([],E())
 assert calls==[]
