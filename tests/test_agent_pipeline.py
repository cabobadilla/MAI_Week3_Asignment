import os,sys,json,uuid,importlib.abc
import pytest
@pytest.fixture
def api(monkeypatch):
 monkeypatch.syspath_prepend(os.environ['GWA_PIPELINE_CANDIDATE'])
 class NoNative(importlib.abc.MetaPathFinder):
  def find_spec(self,fullname,path=None,target=None):
   if fullname.split('.')[0] in ('torch','faiss','sentence_transformers','sklearn','numpy'):raise AssertionError('Native import forbidden')
 monkeypatch.setattr(sys,'meta_path',[NoNative(),*sys.meta_path])
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):monkeypatch.delitem(sys.modules,k,raising=False)
 from app.agent_pipeline import build_agent_graph
 from app.llm_client import LLMResult
 from langgraph.checkpoint.sqlite import SqliteSaver
 from langgraph.types import Command
 return build_agent_graph,LLMResult,SqliteSaver,Command

def state():
 c=str(uuid.uuid4());r=str(uuid.uuid4());return {'campaign_id':c,'run_id':r,'query':'AI purpose','brief':{'title':'Synthetic','objective':'Invite sponsors','formats':['email']},'history':{'items':[]}}, {'configurable':{'thread_id':'gwa:'+c+':'+r},'recursion_limit':20}
def sources():return [{'chunk_id':'doc:1','source_id':'doc','content_version':'0.2','text':'No confirmed partners.','trusted_instructions':False}]
def draft(body='Invitación a explorar colaboración.'):return {'status':'draft','questions':[],'pieces':[{'format':'email','variant':'','body':body,'citations':['doc:1']}]}
def review(verdict='pass'):return {'verdict':verdict,'issues':[] if verdict=='pass' else [{'piece_key':'email:','category':'unsupported_fact','message':'Eliminar convenio no confirmado.','citations':['doc:1']}],'questions':[]}
def caller(R,queue,calls):
 def call(messages,*,stage,request_id):calls.append((stage,request_id));return R(text=json.dumps(queue.pop(0)),model='qwen/qwen3.8-flash',input_tokens=30,output_tokens=20,request_id=request_id)
 return call

def test_verified_context_generation_review_stops_before_human_approval(api,tmp_path):
 build,R,S,C=api;s,cfg=state();calls=[];path=tmp_path/'graph.sqlite'
 with S.from_conn_string(str(path)) as saver:
  g=build(checkpointer=saver,retrieve=lambda q:sources(),call=caller(R,[draft(),review()],calls));x=g.invoke(s,cfg);assert x['status']=='needs_human_review' and x['draft']==draft() and x['review']['verdict']=='pass' and len(x['sources'])==1;assert [x[0] for x in calls]==['generator','reviewer'] and not x.get('approved',False)
 with S.from_conn_string(str(path)) as saver:
  g=build(checkpointer=saver,retrieve=lambda q:sources(),call=caller(R,[],calls));assert g.get_state(cfg).values['draft']==draft() and len(calls)==2

def test_review_revision_changes_hash_and_keeps_both_versions(api,tmp_path):
 build,R,S,C=api;s,cfg=state();calls=[];bad=draft('Convenio confirmado SIN RESPALDO, control sintético.');good=draft()
 with S.from_conn_string(str(tmp_path/'graph.sqlite')) as saver:
  x=build(checkpointer=saver,retrieve=lambda q:sources(),call=caller(R,[bad,review('revise'),good,review()],calls)).invoke(s,cfg)
 assert x['status']=='needs_human_review' and x['cycle']==1 and x['draft']==good and len(x['draft_history'])==2 and x['draft_history'][0]['hash']!=x['draft_history'][1]['hash'];assert len(x['review_history'])==2 and len(calls)==4

def test_revision_limit_no_approval_or_infinite_loop(api,tmp_path):
 build,R,S,C=api;s,cfg=state();calls=[]
 with S.from_conn_string(str(tmp_path/'graph.sqlite')) as saver:
  x=build(checkpointer=saver,retrieve=lambda q:sources(),call=caller(R,[draft(),review('revise')],calls),max_revisions=0).invoke(s,cfg)
 assert x['status']=='failed' and x['error']['code']=='revision_limit' and len(calls)==2 and not x.get('approved',False)

def test_missing_sources_interrupts_without_llm_calls(api,tmp_path):
 build,R,S,C=api;s,cfg=state();calls=[];reads=[]
 with S.from_conn_string(str(tmp_path/'graph.sqlite')) as saver:
  def retrieve(q):reads.append(q);return []
  x=build(checkpointer=saver,retrieve=retrieve,call=caller(R,[],calls)).invoke(s,cfg)
 assert x.get('__interrupt__') and len(reads)==2 and calls==[]

def test_generator_question_yields_persistent_human_gate(api,tmp_path):
 build,R,S,C=api;s,cfg=state();calls=[];p=tmp_path/'graph.sqlite'
 with S.from_conn_string(str(p)) as saver:
  x=build(checkpointer=saver,retrieve=lambda q:sources(),call=caller(R,[{'status':'needs_input','questions':['¿Qué aporte se solicita?'],'pieces':[]}],calls)).invoke(s,cfg);assert x.get('__interrupt__') and len(calls)==1
 with S.from_conn_string(str(p)) as saver:
  x=build(checkpointer=saver,retrieve=lambda q:sources(),call=caller(R,[],calls)).invoke(C(resume={'answer':'Se solicita reunión exploratoria.'}),cfg);assert x['status']=='waiting_input' and len(calls)==1 and not x.get('approved',False)
