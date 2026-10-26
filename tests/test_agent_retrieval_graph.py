import os,sys,uuid,importlib.abc
from pathlib import Path
import pytest
@pytest.fixture
def api(monkeypatch):
 monkeypatch.syspath_prepend(os.environ['GWA_GRAPH_CANDIDATE'])
 class NoNative(importlib.abc.MetaPathFinder):
  def find_spec(self,fullname,path=None,target=None):
   if fullname.split('.')[0] in ('torch','faiss','sentence_transformers','sklearn','numpy'):raise AssertionError('Native imports forbidden in graph mock tests')
 monkeypatch.setattr(sys,'meta_path',[NoNative(),*sys.meta_path])
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):monkeypatch.delitem(sys.modules,k,raising=False)
 from app.agent_graph import build_retrieval_graph
 from langgraph.checkpoint.sqlite import SqliteSaver
 from langgraph.types import Command
 return build_retrieval_graph,SqliteSaver,Command

def fixture():
 campaign=str(uuid.uuid4());run=str(uuid.uuid4());return {'campaign_id':campaign,'run_id':run,'query':'Synthetic AI workshop'}, {'configurable':{'thread_id':'gwa:'+campaign+':'+run},'recursion_limit':12}
def chunk():return {'chunk_id':'doc:chunk1','source_id':'synthetic-doc','content_version':'0.2','text':'Synthetic validated source text','trusted_instructions':False}
def test_context_success_persists_evidence_without_approval(api,tmp_path):
 build,S,C=api;state,cfg=fixture();calls=[]
 def retrieve(q):calls.append(q);return [chunk()]
 with S.from_conn_string(str(tmp_path/'graph.sqlite')) as saver:
  g=build(checkpointer=saver,retrieve=retrieve);x=g.invoke(state,cfg);assert x['status']=='context_ready' and x['query_count']==1 and x['sources']==[chunk()] and not x.get('approved',False);assert g.get_state(cfg).values['sources']==[chunk()]
 assert calls==[state['query']]
def test_no_sources_two_reads_then_persistent_human_interrupt(api,tmp_path):
 build,S,C=api;state,cfg=fixture();calls=[];p=tmp_path/'graph.sqlite'
 def retrieve(q):calls.append(q);return []
 with S.from_conn_string(str(p)) as saver:
  g=build(checkpointer=saver,retrieve=retrieve);x=g.invoke(state,cfg);assert len(calls)==2 and x['query_count']==2 and x['status']=='waiting_input' and x['__interrupt__'];assert x['sources']==[]
 with S.from_conn_string(str(p)) as saver:
  g=build(checkpointer=saver,retrieve=retrieve);x=g.invoke(C(resume={'answer':'Synthetic clarification'}),cfg);assert x['human_answer']=='Synthetic clarification' and x['status']=='waiting_input' and x['sources']==[];assert len(calls)==2 and not x.get('approved',False)
def test_transient_retrieval_error_is_bounded_and_sanitized(api,tmp_path):
 build,S,C=api;state,cfg=fixture();calls=[]
 def retrieve(q):calls.append(q);raise RuntimeError('SYNTHETIC_SECRET_EXCEPTION')
 with S.from_conn_string(str(tmp_path/'graph.sqlite')) as saver:
  x=build(checkpointer=saver,retrieve=retrieve).invoke(state,cfg);assert x['status']=='waiting_input' and len(calls)==2 and 'SYNTHETIC_SECRET_EXCEPTION' not in repr(x)
def test_malformed_source_never_enters_context(api,tmp_path):
 build,S,C=api;state,cfg=fixture()
 with S.from_conn_string(str(tmp_path/'graph.sqlite')) as saver:
  x=build(checkpointer=saver,retrieve=lambda q:[{'chunk_id':'x','text':''}]).invoke(state,cfg);assert x['sources']==[] and x['status']=='waiting_input'
def test_thread_identity_mismatch_rejected_before_read(api,tmp_path):
 build,S,C=api;state,cfg=fixture();cfg['configurable']['thread_id']='other';calls=[]
 with S.from_conn_string(str(tmp_path/'graph.sqlite')) as saver:
  with pytest.raises(ValueError):build(checkpointer=saver,retrieve=lambda q:calls.append(q)).invoke(state,cfg)
 assert calls==[]
