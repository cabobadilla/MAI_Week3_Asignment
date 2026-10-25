#!/usr/bin/env python3
"""Spec documents/reference DDL only; no application, network, model or real data."""
from pathlib import Path
import sqlite3,json,re,hashlib,subprocess,urllib.parse
P=Path(__file__).resolve().parents[1];S=P/'docs/specs/sponsor-materials'
def put(n,s):
 f=P/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
# Reference DDL validation. All data synthetic, in-memory and discarded; no app behavior claimed.
checks=[];db=sqlite3.connect(':memory:');db.executescript((S/'schema-proposal.sql').read_text());checks.append('reference DDL parses in SQLite :memory:')
tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")];assert len(tables)==11
def rejected(label,sql,args=()):
 try:db.execute(sql,args)
 except sqlite3.IntegrityError:checks.append(label);return
 raise AssertionError('Constraint did not reject: '+label)
db.execute("INSERT INTO company(id,name,created_at) VALUES('co1','Empresa ejemplo A','t'),('co2','Empresa ejemplo B','t')")
db.execute("INSERT INTO contact(id,company_id,email,email_key,created_at) VALUES('ct1','co1','a@example.invalid','a@example.invalid','t'),('ct2','co2','a@example.invalid','a@example.invalid','t')")
for cid in ['c1','c2']:db.execute("INSERT INTO campaign(id,title,topic,objective,audience_segment,tone,formats_json,created_at) VALUES(?,?,?,?,?,?,?,?)",(cid,'Ejemplo','Tema','Objetivo','Empresas','Cercano','["email"]','t'))
db.execute("INSERT INTO campaign_recipient VALUES('r1','c1','ct1','a@example.invalid','{}','t',NULL)")
rejected('same email cannot duplicate campaign recipient across companies',"INSERT INTO campaign_recipient VALUES('rdup','c1','ct2','a@example.invalid','{}','t',NULL)")
for vid,cid,rev,parent in [('v1','c1',1,None),('v2','c1',2,'v1'),('w1','c2',1,None)]:db.execute("INSERT INTO content_version(id,campaign_id,format,revision_no,body,content_hash,origin,parent_version_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(vid,cid,'email',rev,'Texto ejemplo','0'*64,'generated',parent,'t'))
def dist(did,cid,vid,rid,kind,channel,key,sup=None,reason=None):
 return (did,cid,vid,rid,kind,channel,'2026-10-25T12:00:00Z','2026-10-25T12:01:00Z','operator','{}','op-'+key,key,'0'*64,sup,reason)
ins='INSERT INTO distribution_record(id,campaign_id,content_version_id,campaign_recipient_id,kind,channel,occurred_at,recorded_at,actor,destination_snapshot_json,operation_id,operation_item_key,payload_hash,supersedes_id,correction_reason) VALUES('+','.join('?'*15)+')'
db.execute(ins,dist('d1','c1','v1','r1','email_sent','email','item1'))
rejected('cross-campaign content reference rejected',ins,dist('dx','c1','w1','r1','email_sent','email','cross'))
rejected('email distribution without recipient rejected',ins,dist('dn','c1','v1',None,'email_sent','email','norec'))
rejected('public distribution cannot have recipient',ins,dist('dp','c1','v1','r1','publication','linkedin','pubrec'))
rejected('operation item retry cannot duplicate distribution',ins,dist('dd','c1','v1','r1','email_sent','email','item1'))
rejected('correction requires reason',ins,dist('dc','c1','v1','r1','email_sent','email','corr0','d1',None))
db.execute(ins,dist('d2','c1','v1','r1','email_sent','email','corr1','d1','Fecha corregida'))
rejected('correction chain cannot branch',ins,dist('d3','c1','v1','r1','email_sent','email','corr2','d1','Otra'))
rejected('content version immutable after distribution',"UPDATE content_version SET body='cambiado' WHERE id='v1'")
rejected('manual distribution immutable; correction appends',"UPDATE distribution_record SET content_version_id='v2' WHERE id='d1'")
assert db.execute("SELECT content_version_id FROM distribution_record WHERE id='d1'").fetchone()[0]=='v1';checks.append('editing via new v2 preserves distribution to v1')
db.commit();before=db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]
try:
 db.execute('BEGIN IMMEDIATE');db.execute(ins,dist('batch1','c1','v1','r1','email_sent','email','batch1'));db.execute(ins,dist('batch2','c1','v1',None,'email_sent','email','batch2'));db.commit()
except sqlite3.IntegrityError:db.rollback()
assert db.execute('SELECT count(*) FROM distribution_record').fetchone()[0]==before;checks.append('example batch transaction rollback leaves no partial records')
assert db.execute('PRAGMA foreign_key_check').fetchall()==[];checks.append('foreign_key_check clean for synthetic reference data')
db.close()
# Internal Markdown links for canonical specs, ignoring clearly marked planned task paths.
links=[];broken=[]
for f in S.glob('*.md'):
 for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)',f.read_text()):
  raw=raw.strip('<>');u=urllib.parse.urlsplit(raw)
  if u.scheme or raw.startswith('#'):continue
  target=(f.parent/urllib.parse.unquote(u.path)).resolve();links.append({'from':f.name,'target':raw})
  if not target.exists() and target!=S/'spec-verification.json':broken.append({'from':f.name,'target':raw})
assert not broken,broken
criteria=re.findall(r'^\| AC-(\d+) \|.*?\| ([A-Z][A-Z0-9-]+) \| ([A-Z][A-Z0-9-]+) \|$',(S/'acceptance.md').read_text(),re.M)
assert len(criteria)==30 and len(set(x[0] for x in criteria))==30
assert len(set(x[1] for x in criteria))==30
tasks=set(re.findall(r'^## ([A-Z][A-Z0-9-]+) ·',(S/'tasks.md').read_text(),re.M))
assert all(x[2] in tasks for x in criteria)
for a in re.findall(r'AC-\d+',(S/'user-stories.md').read_text()):assert a in {'AC-'+x[0] for x in criteria},a
for f in S.glob('*.md'):assert 'REPLACE_' not in f.read_text(),f.name
source=json.loads((P/'docs/references/manifest.json').read_text())
for x in source:
 for key,hashkey in [('path','sha256'),('extracted_path','extracted_sha256')]:assert hashlib.sha256((P/x[key]).read_bytes()).hexdigest()==x[hashkey]
dm=P/'dot/design/gwa-ui-v1/design-manifest.json';design=json.loads(dm.read_text())
for a in design['assets']:assert hashlib.sha256((dm.parent/a['path']).read_bytes()).hexdigest()==a['sha256']
manifest=json.loads((P/'dot/harness/manifest.json').read_text())
for c in manifest['copies']:assert hashlib.sha256((P/c['destination']).read_bytes()).hexdigest()==c['sha256']
origin=subprocess.check_output(['git','-C',str(P),'remote','get-url','origin'],text=True).strip();assert origin=='https://github.com/cabobadilla/MAI_Week3_Asignment.git'
assert json.loads((P/'opencode.json').read_text())['permission']=='deny'
file_hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(S.iterdir()) if f.is_file() and f.name!='spec-verification.json'}
e={'spec_revision':'r4','phase':'documentation_and_reference_ddl_only','scope_confirmation':'Sentinel_83058765897481918dd7fe55e183ae63','application_tests':'not_run','application_implemented':False,'inference_submitted':False,'portal_mutations':False,'library_uploads':False,'sqlite_version':sqlite3.sqlite_version,'reference_schema_tables':tables,'reference_ddl_checks':checks,'criteria_count':30,'planned_application_test_ids':[x[1] for x in criteria],'planned_app_tests_executed':False,'backlog_tasks':sorted(tasks),'criterion_task_coverage':'30/30','internal_links_checked':len(links),'broken_links':broken,'placeholders':'none in canonical Markdown','source_hashes':'preserved','design_v1_asset_hashes':'60 preserved','harness_copies':'44 preserved','git_origin':'preserved','opencode':'deny-all','input_file_sha256':file_hashes,'limits':['reference SQLite constraints are not service/app tests','no live LLM quality/latency/cost measured','new B-v2 details not drawn or approved','runtime/lock/auth/driver isolation not implemented','portal login only; authenticated API not verified']}
put('docs/specs/sponsor-materials/spec-verification.json',json.dumps(e,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'pass','reference_ddl_checks':len(checks),'criteria':len(criteria),'tasks':len(tasks),'links':len(links),'app_tests':'not_run'}))
