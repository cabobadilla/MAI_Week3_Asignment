import os,sys,json,shutil
from pathlib import Path
import pytest
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_BOOTSTRAP_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import bootstrap
 p=tmp_path/'project';(p/'config').mkdir(parents=True);shutil.copyfile(Path(os.environ['GWA_CONFIG_TOML']),p/'config/local.toml');yield bootstrap,p
 sys.path.remove(str(root))

def test_missing_dotenv_defaults_disabled(ctx):
 m,p=ctx;c=m.load_runtime_config(p,env={});assert c.llm_enabled is False and c.api_key is None

def test_loads_synthetic_dotenv_without_inference(ctx):
 m,p=ctx;(p/'.env').write_text('OPENROUTER_API_KEY=SYNTHETIC-KEY\nAPP_LLM_MODEL=qwen/qwen3.8-flash\nAPP_LLM_ENABLED=true\n');c=m.load_runtime_config(p,env={});assert c.llm_enabled and c.model=='qwen/qwen3.8-flash' and c.api_key=='SYNTHETIC-KEY';assert 'SYNTHETIC-KEY' not in repr(c) and 'SYNTHETIC-KEY' not in json.dumps(c.safe_summary())

def test_explicit_environment_wins_and_is_not_mutated(ctx):
 m,p=ctx;(p/'.env').write_text('OPENROUTER_API_KEY=SYNTHETIC-FILE\nAPP_LLM_MODEL=other/model\nAPP_LLM_ENABLED=true\n');env={'OPENROUTER_API_KEY':'SYNTHETIC-ENV','APP_LLM_MODEL':'qwen/qwen3.8-flash'};old=dict(env);c=m.load_runtime_config(p,env=env);assert c.api_key=='SYNTHETIC-ENV' and c.model=='qwen/qwen3.8-flash' and env==old

def test_demo_ignores_dotenv_and_any_enabled_environment(ctx,monkeypatch):
 m,p=ctx;(p/'.env').write_text('APP_LLM_ENABLED=true\nOPENROUTER_API_KEY=SYNTHETIC-SECRET\nAPP_LLM_MODEL=qwen/qwen3.8-flash\n');original=Path.open
 def no_env_read(self,*a,**kw):
  if self.name=='.env':raise AssertionError('demo must not read dotenv')
  return original(self,*a,**kw)
 monkeypatch.setattr(Path,'open',no_env_read);c=m.load_runtime_config(p,demo=True,env={'APP_LLM_ENABLED':'true','OPENROUTER_API_KEY':'SYNTHETIC-ENV','APP_LLM_MODEL':'qwen/qwen3.8-flash'});assert not c.llm_enabled and c.api_key is None and c.model is None

def test_model_is_configurable_not_hardcoded(ctx):
 m,p=ctx;c=m.load_runtime_config(p,env={'APP_LLM_ENABLED':'true','OPENROUTER_API_KEY':'SYNTHETIC','APP_LLM_MODEL':'synthetic/another-model'});assert c.model=='synthetic/another-model'

def test_missing_model_and_invalid_limits_fail_without_secret_values(ctx):
 m,p=ctx
 for env in [{'APP_LLM_ENABLED':'true','OPENROUTER_API_KEY':'SYNTHETIC-SECRET'},{'APP_LLM_MAX_RETRIES':'99','OPENROUTER_API_KEY':'SYNTHETIC-SECRET'}]:
  with pytest.raises(ValueError) as e:m.load_runtime_config(p,env=env)
  assert 'SYNTHETIC-SECRET' not in str(e.value)

def test_dotenv_symlink_rejected(ctx,tmp_path):
 m,p=ctx;other=tmp_path/'elsewhere';other.write_text('OPENROUTER_API_KEY=SYNTHETIC\n');(p/'.env').symlink_to(other)
 with pytest.raises(ValueError):m.load_runtime_config(p,env={})

def test_interpolation_does_not_read_unrelated_environment(ctx,monkeypatch):
 m,p=ctx;monkeypatch.setenv('SOME_UNRELATED_SECRET','SYNTHETIC-MACHINE-SECRET');(p/'.env').write_text('OPENROUTER_API_KEY=${SOME_UNRELATED_SECRET}\nAPP_LLM_MODEL=qwen/qwen3.8-flash\nAPP_LLM_ENABLED=true\n');c=m.load_runtime_config(p,env={});assert c.api_key=='${SOME_UNRELATED_SECRET}'
