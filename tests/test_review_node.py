import os,sys,json,uuid
import pytest
@pytest.fixture
def api(monkeypatch):
 monkeypatch.syspath_prepend(os.environ['GWA_REVIEW_NODE_CANDIDATE'])
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):monkeypatch.delitem(sys.modules,k,raising=False)
 from app.agent_review_node import make_review_node
 from app.llm_client import LLMResult,LLMError
 return make_review_node,LLMResult,LLMError

def state():return {'run_id':str(uuid.uuid4()),'brief':{'objective':'Purpose','formats':['email']},'sources':[{'chunk_id':'doc:1','source_id':'doc','content_version':'0.2','text':'No confirmed partnership','trusted_instructions':False}],'history':{'items':[]},'cycle':0,'events':[],'draft':{'status':'draft','questions':[],'pieces':[{'format':'email','variant':'','body':'Invitación a conversar.','citations':['doc:1']}]}}
def test_pass_still_waits_for_human(api):
 make,R,E=api;s=state();calls=[]
 def call(m,*,stage,request_id):calls.append((m,stage,request_id));return R(text=json.dumps({'verdict':'pass','issues':[],'questions':[]}),model='qwen/qwen3.8-flash',input_tokens=10,output_tokens=10,request_id=request_id)
 x=make(call)(s);assert x['status']=='needs_human_review' and len(x['review_history'])==1 and 'approved' not in x and 'draft' not in x;assert calls[0][1]=='reviewer' and calls[0][2]==s['run_id']+'-reviewer-0'
def test_actionable_revision_preserves_original_draft(api):
 make,R,E=api;s=state();d=json.loads(json.dumps(s['draft']));review={'verdict':'revise','issues':[{'piece_key':'email:','category':'unsupported_fact','message':'Eliminar alianza no confirmada','citations':['doc:1']}],'questions':[]}
 def call(m,*,stage,request_id):return R(text=json.dumps(review),model='qwen/qwen3.8-flash',input_tokens=1,output_tokens=1,request_id=request_id)
 x=make(call)(s);assert x['status']=='revision_required' and x['review']==review and s['draft']==d and s['events']==[]
def test_question_yields_waiting_input(api):
 make,R,E=api
 def call(m,*,stage,request_id):return R(text=json.dumps({'verdict':'needs_input','issues':[],'questions':['¿Hay fuente validada?']}),model='qwen/qwen3.8-flash',input_tokens=1,output_tokens=1,request_id=request_id)
 assert make(call)(state())['status']=='waiting_input'
def test_bad_review_never_reaches_human_ready(api):
 make,R,E=api
 def call(m,*,stage,request_id):return R(text='invalid',model='qwen/qwen3.8-flash',input_tokens=1,output_tokens=1,request_id=request_id)
 x=make(call)(state());assert x['status']=='failed' and x['error']['code']=='invalid_review'
def test_unknown_transport_is_not_auto_retried(api):
 make,R,E=api;calls=[]
 def call(*a,**k):calls.append(1);raise E('provider_transport',outcome_unknown=True)
 x=make(call)(state());assert x['status']=='failed' and x['error']['outcome_unknown'] and len(calls)==1
