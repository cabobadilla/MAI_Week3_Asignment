import importlib.util,json,os,sys
from pathlib import Path
import pytest

@pytest.fixture
def module():
 p=Path(os.environ.get('GWA_CONFIG_FILE',str(Path(__file__).resolve().parents[1]/'app/config.py')));s=importlib.util.spec_from_file_location('gwa_test_config',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m

@pytest.fixture
def settings(tmp_path):
 f=tmp_path/'local.toml';f.write_text('''[app]
host="127.0.0.1"
port=8501
[llm]
provider="openrouter"
api_base="https://openrouter.ai/api/v1"
model_env="APP_LLM_MODEL"
api_key_env="OPENROUTER_API_KEY"
enabled_env="APP_LLM_ENABLED"
enabled_default=false
budget_control="user_managed_api_key"
model_fallback=false
max_input_tokens=12000
max_output_tokens=4096
max_total_tokens_per_run=64000
max_request_attempts_per_run=8
max_retries=2
timeout_seconds=30
''');return f

def test_disabled_no_model_or_secret(module,settings):
 c=module.load_config({},settings);assert c.llm_enabled is False and c.model is None;assert c.api_key is None

def test_enabled_explicit_model(module,settings):
 env={'APP_LLM_ENABLED':'true','OPENROUTER_API_KEY':'FAKE_NOT_A_KEY','APP_LLM_MODEL':'fixture/model'}
 c=module.load_config(env,settings);assert c.llm_enabled and c.model=='fixture/model';assert c.api_key=='FAKE_NOT_A_KEY';assert 'FAKE_NOT_A_KEY' not in repr(c)

@pytest.mark.parametrize('missing',['OPENROUTER_API_KEY','APP_LLM_MODEL'])
def test_missing_required(module,settings,missing):
 e={'APP_LLM_ENABLED':'true','OPENROUTER_API_KEY':'FAKE_NOT_A_KEY','APP_LLM_MODEL':'fixture/model'};e.pop(missing)
 with pytest.raises(ValueError) as err:module.load_config(e,settings)
 assert missing in str(err.value) and 'FAKE_NOT_A_KEY' not in str(err.value)

@pytest.mark.parametrize('key,value',[('APP_LLM_ENABLED','perhaps'),('APP_LLM_MAX_RETRIES','3'),('APP_LLM_MAX_RETRIES','-1'),('APP_LLM_TIMEOUT_SECONDS','0'),('APP_LLM_MAX_INPUT_TOKENS','0'),('APP_LLM_MAX_OUTPUT_TOKENS','x'),('APP_LLM_MAX_REQUEST_ATTEMPTS_PER_RUN','0')])
def test_invalid_values(module,settings,key,value):
 with pytest.raises(ValueError):module.load_config({key:value},settings)

def test_env_not_modified(module,settings):
 e={'APP_LLM_ENABLED':'false'};orig=e.copy();module.load_config(e,settings);assert e==orig

def test_loopback_only(module,settings):
 settings.write_text(settings.read_text().replace('127.0.0.1','0.0.0.0'))
 with pytest.raises(ValueError):module.load_config({},settings)

def test_no_arbitrary_endpoint(module,settings):
 settings.write_text(settings.read_text().replace('https://openrouter.ai/api/v1','http://evil.invalid'))
 with pytest.raises(ValueError):module.load_config({},settings)

def test_no_model_fallback(module,settings):
 with pytest.raises(ValueError):module.load_config({'APP_LLM_ENABLED':'true','OPENROUTER_API_KEY':'FAKE_NOT_A_KEY'},settings)

def test_coherent_token_limits(module,settings):
 with pytest.raises(ValueError):module.load_config({'APP_LLM_MAX_INPUT_TOKENS':'100000'},settings)
