#!/usr/bin/env python3
"""Coordinator-owned fixed-suite runner; no shell, provider, .env, or browser."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
SUITES={
 'guard':(['scripts/filemap_guard.py'],'tests/harness/test_guard.py',{'GWA_GUARD_FILE':'scripts/filemap_guard.py'}),
 'campaign':(['app/__init__.py','app/config.py','app/storage.py','app/companies.py','app/campaigns.py','app/recipients.py'],'tests/test_campaigns_recipients.py',{}),
 'auth':(['app/__init__.py','app/config.py','app/storage.py','app/auth.py'],'tests/test_auth.py',{}),
 'versions':(['app/__init__.py','app/config.py','app/storage.py','app/campaigns.py','app/versions.py','app/approval.py'],'tests/test_versions_approval.py',{}),
 'export':(['app/__init__.py','app/config.py','app/storage.py','app/campaigns.py','app/versions.py','app/approval.py','app/export.py'],'tests/test_export.py',{}),
 'distribution':(['app/__init__.py','app/config.py','app/storage.py','app/companies.py','app/campaigns.py','app/recipients.py','app/versions.py','app/distribution.py'],'tests/test_distribution.py',{}),
 'followup':(['app/__init__.py','app/config.py','app/storage.py','app/companies.py','app/campaigns.py','app/recipients.py','app/versions.py','app/distribution.py','app/followup.py'],'tests/test_followup.py',{}),
 'ingestion':(['app/__init__.py','app/config.py','app/ingestion.py'],'tests/test_ingestion.py',{}),
 'retrieval':(['app/__init__.py','app/config.py','app/ingestion.py','app/retrieval.py'],'tests/test_retrieval.py',{}),
 'embeddings':(['app/__init__.py','app/config.py','app/local_embeddings.py'],'tests/test_local_embeddings.py',{}),
 'organization_migration':(['app/__init__.py','app/config.py','app/storage.py','app/companies.py','app/campaigns.py','app/recipients.py','app/versions.py','app/distribution.py'],'tests/test_organization_migration.py',{}),
 'organization_forms':(['app/__init__.py','app/config.py','app/storage.py','app/companies.py','app/organizations.py','app/campaigns.py','app/recipients.py'],'tests/test_organization_forms.py',{}),
 'config':(['app/__init__.py','app/config.py'],'tests/test_config.py',{'GWA_CONFIG_FILE':'app/config.py'}),
 'storage':(['app/__init__.py','app/config.py','app/storage.py','app/companies.py'],'tests/test_storage_companies.py',{})}
SUITES.update({
 'bootstrap':(['app/__init__.py','app/config.py','app/bootstrap.py'],'tests/test_bootstrap.py',{'GWA_BOOTSTRAP_CANDIDATE':'.'}),
 'web_auth':(['app/__init__.py','app/config.py','app/web_auth.py'],'tests/test_web_auth.py',{'GWA_WEB_AUTH_CANDIDATE':'.'}),
 'web_auth_real':(['app/__init__.py','app/config.py','app/storage.py','app/auth.py','app/web_auth.py'],'tests/test_web_auth_real.py',{'GWA_WEB_AUTH_CANDIDATE':'.'}),
 'runs':(['app/__init__.py','app/config.py','app/storage.py','app/campaigns.py','app/runs.py'],'tests/test_runs.py',{'GWA_RUNS_CANDIDATE':'.'}),
 'isolated_embeddings_mock':(['app/__init__.py','app/config.py','app/isolated_embeddings.py','app/embedding_worker.py'],'tests/test_isolated_embeddings.py',{'GWA_ISOLATED_CANDIDATE':'.'})})

# Fixed accepted HTTP/runtime suites; coordinator-owned controls, no native ML.
_HTTP_SOURCES=['app/__init__.py', 'app/config.py', 'app/storage.py', 'app/companies.py', 'app/organizations.py', 'app/campaigns.py', 'app/recipients.py', 'app/versions.py', 'app/approval.py', 'app/export.py', 'app/distribution.py', 'app/followup.py', 'app/runs.py', 'app/demo_generation.py', 'app/web_auth.py', 'app/web_organizations.py', 'app/web_campaigns.py', 'app/web_demo.py', 'app/web_review.py', 'app/web_export.py', 'app/web_publications.py', 'app/web_publication_view.py', 'app/web_directed.py', 'app/web_directed_view.py', 'app/web_recipients.py', 'app/web_interactions.py', 'app/web_thread.py', 'app/auth.py', 'app/bootstrap.py', 'app/ui_shell.py', 'app/ui_organizations.py', 'app/ui_campaigns.py', 'app/ui_work.py', 'app/ui_approval.py', 'app/ui_export_controls.py', 'app/ui_publications.py', 'app/ui_directed.py', 'app/ui_directed_record.py', 'app/ui_directed_note.py', 'app/runtime.py']
EXTRA_SUITES={'web_organizations': ('test_web_organizations.py', 'GWA_WEB_ORG_CANDIDATE'), 'web_campaigns': ('test_web_campaigns.py', 'GWA_WEB_CAMPAIGN_CANDIDATE'), 'web_demo': ('test_web_demo.py', 'GWA_WEB_DEMO_CANDIDATE'), 'web_review': ('test_web_review.py', 'GWA_WEB_REVIEW_CANDIDATE'), 'web_export': ('test_web_export.py', 'GWA_WEB_EXPORT_CANDIDATE'), 'web_publication_write': ('test_web_publication_write.py', 'GWA_WEB_PUBLIC_CANDIDATE'), 'web_publication_view': ('test_web_publication_view.py', 'GWA_WEB_PUBLIC_VIEW_CANDIDATE'), 'web_directed_write': ('test_web_directed_write.py', 'GWA_WEB_DIRECTED_CANDIDATE'), 'web_directed_view': ('test_web_directed_view.py', 'GWA_WEB_DIRECTED_VIEW_CANDIDATE'), 'web_recipient_write': ('test_web_recipient_write.py', 'GWA_WEB_RECIPIENTS_CANDIDATE'), 'web_interaction_write': ('test_web_interaction_write.py', 'GWA_WEB_INTERACTION_CANDIDATE'), 'web_thread_read': ('test_web_thread_read.py', 'GWA_WEB_THREAD_CANDIDATE'), 'runtime_demo': ('test_runtime_demo.py', 'GWA_RUNTIME_CANDIDATE')}
for _name,(_test,_env) in EXTRA_SUITES.items():
 SUITES[_name]=(_HTTP_SOURCES,"tests/"+_test,{_env:"."})

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--suite',choices=sorted(SUITES),required=True);a=ap.parse_args()
 if a.suite in ['embeddings','retrieval']:
  incident=ROOT/'dot/implementation/RAG-native-crash.json'
  if incident.exists() and json.loads(incident.read_text()).get('native_reproduction_suspended',True):
   print('BLOCKED: native RAG suites explicitly paused after OpenMP crashes; no candidate executed. See dot/implementation/RAG-native-crash.json');return 2
 sources,test,variables=SUITES[a.suite]
 for rel in [*sources,test]:
  f=ROOT/rel
  if not f.is_file() or f.is_symlink():raise SystemExit('Missing regular controlled input: '+rel)
 control=Path(tempfile.mkdtemp(prefix='gwa-validate-',dir='/tmp')).resolve();scratch=control/'scratch';scratch.mkdir();candidate=control/'candidate';candidate.mkdir();tests=control/'tests';tests.mkdir()
 for rel in sources:
  f=candidate/rel;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,f)
 frozen=tests/Path(test).name;shutil.copyfile(ROOT/test,frozen);(control/'pytest.ini').write_text('[pytest]\n')
 if a.suite in ['storage','campaign','auth','versions','export','distribution','followup','organization_migration','organization_forms','runs','web_auth_real'] or a.suite in EXTRA_SUITES:shutil.copyfile(ROOT/'app/migrations/001_initial.sql',control/'schema.sql')
 if a.suite=='embeddings':shutil.copyfile(ROOT/'config/embedding-model.json',control/'embedding-model.json')
 if a.suite=='bootstrap' or a.suite in EXTRA_SUITES:shutil.copyfile(ROOT/'config/local.toml',control/'local.toml')
 sealed=control/'sealed.txt';sealed.write_text('synthetic protected control')
 forbidden=Path(tempfile.mkstemp(prefix='gwa-deny-canary-',dir='/tmp')[1]).resolve();forbidden.write_text('synthetic outside data')
 home_canary=ROOT/'dot/implementation/canary-deny.txt';home_canary.parent.mkdir(parents=True,exist_ok=True);home_canary.write_text('synthetic home boundary canary')
 q=lambda s:json.dumps(str(s))
 profile='(version 1)\n(allow default)\n(deny network*)\n(deny file-write*)\n(allow file-write* (literal "/dev/null") (subpath '+q(scratch)+'))\n(deny file-read-data (subpath "/Users") (subpath "/private/tmp") (subpath "/private/var") (subpath "/Volumes") (subpath "/Library/Keychains") (subpath "/Library/Application Support") (subpath "/opt/homebrew/etc") (subpath "/opt/homebrew/var"))\n(allow file-read-data (subpath '+q(ROOT/'.venv')+') (subpath '+q(control)+') (subpath "/private/var/db/dyld"))\n(deny mach-lookup (global-name "com.apple.securityd") (global-name "com.apple.securityd.xpc") (global-name "com.apple.accountsd.accountmanager"))\n'
 if a.suite=='embeddings':profile+='(allow file-read-data (subpath '+q(ROOT/'data/models/multilingual-minilm')+'))\n'
 (control/'profile.sb').write_text(profile)
 canary=control/'canary.py';canary.write_text('from pathlib import Path\nimport socket\nchecks=[]\n'+f'for name,fn in [("outside",lambda:Path({str(forbidden)!r}).read_text()),("home",lambda:Path({str(home_canary)!r}).read_text()),("controlwrite",lambda:Path({str(sealed)!r}).write_text("bad")),("network",lambda:socket.create_connection(("127.0.0.1",9),timeout=1))]:\n'+ ' try:fn()\n except PermissionError:checks.append(name)\n else:raise RuntimeError(name+" unexpectedly allowed")\nprint("PASS canaries",checks)\n')
 env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','HOME':str(scratch),'TMPDIR':str(scratch),'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','LANGSMITH_TRACING':'false','LANGCHAIN_TRACING_V2':'false'}
 if a.suite=='embeddings':env.update({'GWA_EMBEDDING_CANDIDATE':str(candidate),'GWA_EMBEDDING_MODEL':str(ROOT/'data/models/multilingual-minilm'),'GWA_EMBEDDING_MANIFEST':str(control/'embedding-model.json'),'HF_HOME':str(scratch/'hf'),'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','HF_HUB_DISABLE_IMPLICIT_TOKEN':'1','OMP_NUM_THREADS':'2','TOKENIZERS_PARALLELISM':'false'})
 for k,rel in variables.items():env[k]=str(candidate/rel)
 if a.suite=='bootstrap' or a.suite in EXTRA_SUITES:env['GWA_CONFIG_TOML']=str(control/'local.toml')
 if a.suite in ['runs','web_auth_real'] or a.suite in EXTRA_SUITES:env['GWA_SCHEMA_FILE']=str(control/'schema.sql')
 if a.suite=='campaign':env['GWA_CAMPAIGN_CANDIDATE']=str(candidate)
 if a.suite=='retrieval':env['GWA_RETRIEVAL_CANDIDATE']=str(candidate)
 if a.suite=='ingestion':env['GWA_INGESTION_CANDIDATE']=str(candidate)
 if a.suite=='organization_forms':env['GWA_ORG_FORMS_CANDIDATE']=str(candidate)
 if a.suite=='organization_migration':env['GWA_ORG_MIGRATION_CANDIDATE']=str(candidate)
 if a.suite=='followup':env['GWA_FOLLOWUP_CANDIDATE']=str(candidate)
 if a.suite=='distribution':env['GWA_DISTRIBUTION_CANDIDATE']=str(candidate)
 if a.suite=='export':env['GWA_EXPORT_CANDIDATE']=str(candidate)
 if a.suite=='versions':env['GWA_VERSION_CANDIDATE']=str(candidate)
 if a.suite=='auth':env['GWA_AUTH_CANDIDATE']=str(candidate)
 if a.suite in ['storage','campaign','auth','versions','export','distribution','followup','organization_migration','organization_forms']:env.update({'GWA_DB_CANDIDATE':str(candidate),'GWA_SCHEMA_FILE':str(control/'schema.sql')})
 prefix=['/usr/bin/sandbox-exec','-f',str(control/'profile.sb'),str(ROOT/'.venv/bin/python'),'-I','-B']
 pre=subprocess.run(prefix+[str(canary)],cwd=control,env=env,capture_output=True,text=True,timeout=15)
 if pre.returncode:raise SystemExit('Canary failed; candidate not executed: '+pre.stdout+pre.stderr)
 sealed_inputs=[frozen,*[candidate/x for x in sources]]+([control/'embedding-model.json'] if a.suite=='embeddings' else [])
 before={str(f.relative_to(control)):digest(f) for f in sealed_inputs}
 argv=prefix+['-m','pytest','-q','-p','no:cacheprovider','-c',str(control/'pytest.ini'),'--basetemp='+str(scratch/'pytest'),'--junitxml='+str(scratch/'junit.xml'),str(frozen)]
 run=subprocess.run(argv,cwd=control,env=env,capture_output=True,text=True,timeout=120)
 after={str(f.relative_to(control)):digest(f) for f in sealed_inputs}
 assert before==after,'Candidate or protected tests changed during validation'
 stamp=str(time.time_ns());dest=ROOT/'dot/implementation/reports'/f'{a.suite}-{stamp}';dest.mkdir(parents=True)
 (dest/'stdout.txt').write_text(run.stdout);(dest/'stderr.txt').write_text(run.stderr)
 if (scratch/'junit.xml').exists():shutil.copyfile(scratch/'junit.xml',dest/'junit.xml')
 report={'suite':a.suite,'exit_code':run.returncode,'phase':'protected_backend_snapshot','control_root':str(control),'input_sha256':before,'inputs_unchanged':True,'canaries':pre.stdout.strip(),'profile_sha256':digest(control/'profile.sb'),'model_calls':False,'env_real_read':False,'network':'denied','base_kind':'file_sha256_snapshot_no_git_candidate','argv':argv,'limits':'fixed backend suites, not proof of UI/app LLM quality or general sandbox portability'}
 (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(run.stdout,end='');print(run.stderr,end='');print('Evidence:',dest);return run.returncode
if __name__=='__main__':raise SystemExit(main())
