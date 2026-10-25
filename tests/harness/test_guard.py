import importlib.util,json,os
from pathlib import Path
import pytest

@pytest.fixture
def guard():
 p=Path(os.environ.get('GWA_GUARD_FILE',str(Path(__file__).resolve().parents[2]/'scripts/filemap_guard.py')))
 s=importlib.util.spec_from_file_location('guard',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def payload(path='app/config.py',content='x=1\n'):
 return json.dumps({'files':[{'path':path,'content':content}]})

def test_valid_subset(guard,tmp_path):
 root=tmp_path.resolve();r=guard.validate_filemap(payload(),['app/config.py','app/state.py'],root);assert r=={'app/config.py':'x=1\n'}

@pytest.mark.parametrize('path',['/tmp/evil.py','../evil.py','app/../evil.py','app//evil.py','./app/x.py','app\\x.py','C:/x.py','app/.env.py','.git/x.py','docs/x.py','dot/x.py','tests/x.py','app/x.txt'])
def test_invalid_paths(guard,tmp_path,path):
 with pytest.raises(ValueError):guard.validate_filemap(payload(path),[path],tmp_path.resolve())

def test_unallowed_file(guard,tmp_path):
 with pytest.raises(ValueError):guard.validate_filemap(payload('app/extra.py'),['app/config.py'],tmp_path.resolve())

@pytest.mark.parametrize('text',['{"files":[],"files":[]}','{"files":[],"command":"rm"}','{"files":[{"path":"app/config.py","content":"","mode":"755"}]}'])
def test_schema_duplicate_keys(guard,tmp_path,text):
 with pytest.raises(ValueError):guard.validate_filemap(text,['app/config.py'],tmp_path.resolve())

def test_case_duplicate(guard,tmp_path):
 text=json.dumps({'files':[{'path':'app/config.py','content':'x'},{'path':'APP/config.py','content':'y'}]})
 with pytest.raises(ValueError):guard.validate_filemap(text,['app/config.py','APP/config.py'],tmp_path.resolve())

@pytest.mark.parametrize('content',['\0','á'*130000])
def test_content_limits(guard,tmp_path,content):
 with pytest.raises(ValueError):guard.validate_filemap(payload(content=content),['app/config.py'],tmp_path.resolve())

def test_symlink_parent(guard,tmp_path):
 root=tmp_path/'candidate';root.mkdir();other=tmp_path/'outside';other.mkdir();(root/'app').symlink_to(other,target_is_directory=True)
 with pytest.raises(ValueError):guard.validate_filemap(payload(),['app/config.py'],root.resolve())

def test_hardlink(guard,tmp_path):
 root=tmp_path/'candidate';(root/'app').mkdir(parents=True);a=root/'app/config.py';a.write_text('x');os.link(a,tmp_path/'duplicate.py')
 with pytest.raises(ValueError):guard.snapshot(root.resolve(),['app/config.py'])

def test_apply_and_untouched(guard,tmp_path):
 root=tmp_path.resolve();(root/'keep.txt').write_text('keep');base=guard.snapshot(root,['app/config.py']);original=base.copy()
 post=guard.apply_filemap({'app/config.py':'hello=1\n'},root,base)
 assert (root/'app/config.py').read_text()=='hello=1\n' and (root/'keep.txt').read_text()=='keep';assert len(post['app/config.py'])==64;assert base==original

def test_stale_no_writes(guard,tmp_path):
 root=tmp_path.resolve();(root/'app').mkdir();(root/'app/config.py').write_text('before');base=guard.snapshot(root,['app/config.py','app/new.py']);(root/'app/config.py').write_text('changed')
 with pytest.raises(ValueError):guard.apply_filemap({'app/config.py':'bad','app/new.py':'bad'},root,base)
 assert (root/'app/config.py').read_text()=='changed' and not (root/'app/new.py').exists()

def test_missing_expected(guard,tmp_path):
 with pytest.raises(ValueError):guard.apply_filemap({'app/config.py':'bad'},tmp_path.resolve(),{})

def test_atomic_rollback(guard,tmp_path,monkeypatch):
 root=tmp_path.resolve();(root/'app').mkdir();(root/'app/a.py').write_text('A');(root/'app/b.py').write_text('B');base=guard.snapshot(root,['app/a.py','app/b.py']);real=os.replace;counter=[0]
 def replace(src,dst,*a,**kw):
  if str(dst).endswith('/app/b.py') and counter[0]==0:counter[0]+=1;raise OSError('synthetic commit failure')
  return real(src,dst,*a,**kw)
 monkeypatch.setattr(os,'replace',replace)
 with pytest.raises(OSError):guard.apply_filemap({'app/a.py':'newA','app/b.py':'newB'},root,base)
 assert (root/'app/a.py').read_text()=='A' and (root/'app/b.py').read_text()=='B'
