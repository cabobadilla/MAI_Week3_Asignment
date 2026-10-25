import os,sys,types,importlib,importlib.abc,importlib.util
from pathlib import Path
import pytest

ROOTS=('torch','faiss','sentence_transformers','sklearn')
@pytest.fixture
def guard(monkeypatch):
 root=Path(os.environ['GWA_NATIVE_GUARD_CANDIDATE']);monkeypatch.syspath_prepend(str(root));prior=list(sys.meta_path)
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.') or any(k==n or k.startswith(n+'.') for n in ROOTS):monkeypatch.delitem(sys.modules,k,raising=False)
 from app import native_runtime_guard as m
 calls=[]
 class FakeFinder(importlib.abc.MetaPathFinder,importlib.abc.Loader):
  def find_spec(self,fullname,path=None,target=None):
   if fullname in ROOTS:return importlib.util.spec_from_loader(fullname,self)
  def create_module(self,spec):return types.ModuleType(spec.name)
  def exec_module(self,module):calls.append(module.__name__)
 sys.meta_path.insert(0,FakeFinder())
 yield m,calls
 sys.meta_path[:]=prior
 for k in list(sys.modules):
  if any(k==n or k.startswith(n+'.') for n in ROOTS):sys.modules.pop(k,None)

@pytest.mark.parametrize('role,allowed,blocked',[('embedding','torch',['faiss','sklearn']),('vector','faiss',['torch','sentence_transformers','sklearn'])])
def test_opposing_imports_blocked_before_loader_exec(guard,role,allowed,blocked):
 m,calls=guard;m.install_guard(role);assert m.current_role()==role
 for name in blocked:
  with pytest.raises(m.NativeRuntimeConflict):importlib.import_module(name)
 assert calls==[]
 importlib.import_module(allowed);assert calls==[allowed];m.assert_compatible(role)

@pytest.mark.parametrize('role,loaded',[('embedding','faiss'),('embedding','faiss._swigfaiss'),('embedding','sklearn'),('vector','torch'),('vector','sentence_transformers'),('vector','sklearn')])
def test_existing_conflict_rejected_without_installing(guard,monkeypatch,role,loaded):
 m,calls=guard;before=list(sys.meta_path);monkeypatch.setitem(sys.modules,loaded,types.ModuleType(loaded))
 with pytest.raises(m.NativeRuntimeConflict):m.install_guard(role)
 assert m.current_role() is None and sys.meta_path==before and calls==[]

def test_install_idempotent_role_switch_rejected(guard):
 m,calls=guard;m.install_guard('embedding');before=list(sys.meta_path);m.install_guard('embedding');assert sys.meta_path==before
 with pytest.raises(m.NativeRuntimeConflict):m.install_guard('vector')
 assert m.current_role()=='embedding'

def test_assert_requires_guard_and_detects_late_incompatible_state(guard,monkeypatch):
 m,calls=guard
 with pytest.raises(m.NativeRuntimeConflict):m.assert_compatible('vector')
 m.install_guard('vector');monkeypatch.setitem(sys.modules,'torch.fake',types.ModuleType('torch.fake'))
 with pytest.raises(m.NativeRuntimeConflict):m.assert_compatible('vector')
 assert calls==[]

@pytest.mark.parametrize('bad',[None,True,{},[], 'embeddingx','VECTOR'])
def test_invalid_role_never_installs(guard,bad):
 m,calls=guard;before=list(sys.meta_path)
 with pytest.raises(ValueError):m.install_guard(bad)
 assert m.current_role() is None and sys.meta_path==before

def test_concurrent_same_role_installs_only_once(guard):
 from concurrent.futures import ThreadPoolExecutor
 m,calls=guard;before=len(sys.meta_path)
 with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda _:m.install_guard('vector'),range(8)))
 assert m.current_role()=='vector' and len(sys.meta_path)==before+1 and calls==[]

def test_late_conflict_blocks_next_allowed_native_loader(guard,monkeypatch):
 m,calls=guard;m.install_guard('embedding');monkeypatch.setitem(sys.modules,'faiss.external',types.ModuleType('faiss.external'))
 with pytest.raises(m.NativeRuntimeConflict):importlib.import_module('torch')
 assert calls==[]
