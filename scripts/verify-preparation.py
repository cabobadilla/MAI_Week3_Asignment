#!/usr/bin/env python3
"""Verify setup/provenance only; never execute upstream or infer."""
from pathlib import Path
import json,hashlib,subprocess,tomllib
r=Path(__file__).resolve().parents[1]
for n in ['AGENTS.md','README.md','dot/README.md','dot/STATUS.md','dot/DECISIONS.md','dot/PYTHON_AGENT_PROFILE.md','dot/LESSONS.md','dot/ADAPTER_PROPOSAL.md']:assert (r/n).is_file(),n
m=json.loads((r/'dot/harness/manifest.json').read_text())
assert m['source_url']=='https://github.com/cabobadilla/dotHarness.git'
assert m['source_git_sha']=='2e5d217f55b3a26543d3d52edb39d7204e35c258'
inv=sorted(m['source_package_inventory'],key=lambda x:x['path'].encode())
assert hashlib.sha256(''.join(x['path']+'\t'+x['sha256']+'\n' for x in inv).encode()).hexdigest()==m['source_package_sha256']
for c in m['copies']:assert hashlib.sha256((r/c['destination']).read_bytes()).hexdigest()==c['sha256'],c['destination']
assert json.loads((r/'opencode.json').read_text())['permission']=='deny'
assert json.loads((r/'opencode.json').read_text())['model']=='opencode-go/deepseek-v4.1-flash'
assert json.loads((r/'opencode.json').read_text())['small_model']=='opencode-go/deepseek-v4.1-flash'
for x in json.loads((r/'docs/references/manifest.json').read_text()):
 for a,b in [('path','sha256'),('extracted_path','extracted_sha256')]:assert hashlib.sha256((r/x[a]).read_bytes()).hexdigest()==x[b],x[a]
 assert len((r/x['extracted_path']).read_text())>100
tomllib.loads((r/'config/local.toml').read_text())
for base in ['docs','dot','scripts']:
 for f in (r/base).rglob('*'):
  if f.is_file() and f.suffix in ['.md','.json','.txt','.py']:assert ('my'+'code'+'factory') not in f.read_text().lower(),str(f)
for n in ['AGENTS.md','README.md','opencode.json']:assert ('my'+'code'+'factory') not in (r/n).read_text().lower()
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=r,text=True).strip()=='https://github.com/cabobadilla/MAI_Week3_Asignment.git'
ignored=['.venv/x','.setup-venv/x','.env','data/checkpoints/a.sqlite','outputs/a.md']
assert set(subprocess.check_output(['git','check-ignore',*ignored],cwd=r,text=True).splitlines())==set(ignored)
print('PASS: harness pin/copy hashes, source hashes, deny-all, no retired instructions, JSON/TOML, ignores and preserved origin.')

# OpenRouter example only: never inspect the real .env.
c=tomllib.loads((r/'config/local.toml').read_text())['llm']
assert c['provider']=='openrouter' and c['enabled_default'] is False
assert c['budget_control']=='user_managed_api_key' and 'model' not in c
example={}
for line in (r/'.env.example').read_text().splitlines():
 if line and not line.startswith('#'):
  k,v=line.split('=',1);example[k]=v
assert example['OPENROUTER_API_KEY']=='' and example['APP_LLM_MODEL']=='qwen/qwen3.8-flash'
assert example['APP_LLM_ENABLED']=='false'
for k,v in [('APP_LLM_MAX_INPUT_TOKENS','max_input_tokens'),('APP_LLM_MAX_OUTPUT_TOKENS','max_output_tokens'),('APP_LLM_MAX_TOTAL_TOKENS_PER_RUN','max_total_tokens_per_run'),('APP_LLM_MAX_REQUEST_ATTEMPTS_PER_RUN','max_request_attempts_per_run'),('APP_LLM_MAX_RETRIES','max_retries'),('APP_LLM_TIMEOUT_SECONDS','timeout_seconds')]:assert int(example[k])==c[v]
assert subprocess.run(['git','check-ignore','.env.example'],cwd=r,capture_output=True).returncode==1
print('PASS: safe OpenRouter example, selected configurable Qwen model, API-key budget control, matching technical limits and trackable example; real .env untouched.')
