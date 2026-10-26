import os,sys,json,uuid
import pytest
@pytest.fixture
def api(monkeypatch):
 monkeypatch.syspath_prepend(os.environ['GWA_GENERATION_NODE_CANDIDATE'])
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):monkeypatch.delitem(sys.modules,k,raising=False)
 from app.agent_generation_node import make_generation_node
 from app.llm_client import LLMResult,LLMError
 return make_generation_node,LLMResult,LLMError

def state():return {'run_id':str(uuid.uuid4()),'brief':{'title':'Synthetic','objective':'Purpose','formats':['email']},'sources':[{'chunk_id':'doc:1','source_id':'doc','content_version':'0.2','text':'No confirmed partnership','trusted_instructions':False}],'history':{'items':[]},'cycle':0,'events':[]}
def draft():return {'status':'draft','questions':[],'pieces':[{'format':'email','variant':'','body':'Invitación a explorar una colaboración.','citations':['doc:1']}]}
def test_generation_node_keeps_citations_and_never_approves(api):
 make,R,E=api;s=state();calls=[]
 def call(m,*,stage,request_id):calls.append((m,stage,request_id));return R(text=json.dumps(draft()),model='qwen/qwen3.8-flash',input_tokens=40,output_tokens=30,request_id=request_id)
 x=make(call)(s);assert x['status']=='draft_ready' and x['draft']==draft() and len(x['draft_hash'])==64 and len(x['draft_history'])==1;assert calls[0][1]=='generator' and calls[0][2]==s['run_id']+'-generator-0';assert 'approved' not in x and 'sent' not in x
 assert s['events']==[] and 'draft' not in s
def test_generation_question_does_not_create_content(api):
 make,R,E=api;s=state()
 def call(m,*,stage,request_id):return R(text=json.dumps({'status':'needs_input','questions':['¿Qué aporte se propone?'],'pieces':[]}),model='qwen/qwen3.8-flash',input_tokens=2,output_tokens=2,request_id=request_id)
 x=make(call)(s);assert x['status']=='waiting_input' and x['draft'] is None and x['questions'] and x['draft_history']==[]
def test_invalid_response_does_not_become_draft(api):
 make,R,E=api;s=state()
 def call(m,*,stage,request_id):return R(text='not json',model='qwen/qwen3.8-flash',input_tokens=2,output_tokens=2,request_id=request_id)
 x=make(call)(s);assert x['status']=='failed' and x['error']['code']=='invalid_generation' and x['draft'] is None
def test_transport_error_metadata_sanitized(api):
 make,R,E=api
 def call(*a,**k):raise E('provider_transport',outcome_unknown=True)
 x=make(call)(state());assert x['status']=='failed' and x['error']['outcome_unknown'] is True
def test_revision_has_stable_unique_request_id_and_previous_evidence(api):
 make,R,E=api;s=state();s.update(cycle=1,review={'verdict':'revise','issues':[{'message':'No afirmar alianza'}],'questions':[]},draft_history=[{'cycle':0,'hash':'0'*64,'pieces':[]}]);seen=[]
 def call(m,*,stage,request_id):seen.append((json.loads(m[1]['content']),request_id));return R(text=json.dumps(draft()),model='qwen/qwen3.8-flash',input_tokens=2,output_tokens=2,request_id=request_id)
 x=make(call)(s);assert seen[0][1].endswith('-generator-1') and seen[0][0]['feedback']==s['review'] and len(x['draft_history'])==2
def test_cycle_limit_prevents_call(api):
 make,R,E=api;s=state();s['cycle']=3;calls=[];x=make(lambda *a,**k:calls.append('x'))(s);assert x['status']=='failed' and calls==[]
