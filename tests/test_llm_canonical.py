import os,sys,json
from pathlib import Path
import pytest,httpx
KEY='SYNTHETIC-KEY-NOT-REAL';MODEL='qwen/qwen3.8-flash'
@pytest.fixture
def api(monkeypatch):
 monkeypatch.syspath_prepend(os.environ['GWA_LLM_CLIENT_CANDIDATE'])
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):monkeypatch.delitem(sys.modules,k,raising=False)
 from app.config import AppConfig
 from app.llm_client import LLMClient,LLMError
 def config(**kw):
  values=dict(host='127.0.0.1',port=8501,llm_enabled=True,model=MODEL,api_key=KEY,api_base='https://openrouter.ai/api/v1',max_input_tokens=12000,max_output_tokens=4096,max_total_tokens_per_run=64000,max_request_attempts_per_run=8,max_retries=2,timeout_seconds=30,budget_control='user_managed_api_key');values.update(kw);return AppConfig(**values)
 return LLMClient,LLMError,config

def reply(**kw):
 d={'model':MODEL,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'Synthetic grounded draft'}}],'usage':{'prompt_tokens':30,'completion_tokens':12}};d.update(kw);return d

def test_single_mock_request_exact_provider_and_no_key_repr(api,caplog):
 C,E,cfg=api;calls=[]
 def handler(req):
  calls.append(req);assert str(req.url)=='https://openrouter.ai/api/v1/chat/completions';assert req.headers['authorization']=='Bearer '+KEY;body=json.loads(req.content);assert body['model']==MODEL and body['max_tokens']==4096 and body['stream'] is False;return httpx.Response(200,json=reply())
 with C(cfg(),transport=httpx.MockTransport(handler)) as client:r=client.complete([{'role':'user','content':'Synthetic prompt'}],request_id='test-1')
 assert len(calls)==1 and r.text=='Synthetic grounded draft' and r.model==MODEL and r.input_tokens==30 and r.output_tokens==12 and r.request_id=='test-1';assert KEY not in repr(r)+repr(client)+caplog.text

def test_real_transport_requires_explicit_opt_in(api):
 C,E,cfg=api
 with pytest.raises(E) as exc:C(cfg())
 assert exc.value.code=='remote_disabled'

def test_disabled_mode_never_calls(api):
 C,E,cfg=api;calls=[]
 with C(cfg(llm_enabled=False),transport=httpx.MockTransport(lambda req:calls.append(req))) as c:
  with pytest.raises(E) as exc:c.complete([{'role':'user','content':'X'}],request_id='test-2')
 assert exc.value.code=='disabled' and calls==[]

@pytest.mark.parametrize('status,code,retryable,unknown',[(401,'provider_auth',False,False),(429,'rate_limited',True,False),(500,'provider_server',False,True),(302,'provider_redirect',False,False)])
def test_http_failure_sanitized_without_retry(api,status,code,retryable,unknown):
 C,E,cfg=api;calls=[]
 def h(req):calls.append(req);return httpx.Response(status,json={'error':KEY+' private source'},headers={'Location':'https://invalid.example/'})
 with C(cfg(),transport=httpx.MockTransport(h)) as c:
  with pytest.raises(E) as exc:c.complete([{'role':'user','content':'X'}],request_id='test-3')
 e=exc.value;assert e.code==code and e.retryable is retryable and e.outcome_unknown is unknown and len(calls)==1;assert KEY not in str(e) and 'private source' not in str(e)

def test_timeout_is_uncertain_and_not_automatically_retried(api):
 C,E,cfg=api;calls=[]
 def h(req):calls.append(req);raise httpx.ReadTimeout(KEY+' private source')
 with C(cfg(),transport=httpx.MockTransport(h)) as c:
  with pytest.raises(E) as exc:c.complete([{'role':'user','content':'X'}],request_id='test-4')
 assert exc.value.outcome_unknown is True and exc.value.retryable is False and len(calls)==1 and KEY not in str(exc.value)

@pytest.mark.parametrize('bad',[[],[{'role':'tool','content':'X'}],[{'role':'user','content':False}],[{'role':'user','content':'X','name':'override'}]])
def test_invalid_messages_never_call(api,bad):
 C,E,cfg=api;calls=[]
 with C(cfg(),transport=httpx.MockTransport(lambda req:calls.append(req))) as c:
  with pytest.raises(E):c.complete(bad,request_id='test-5')
 assert calls==[]

def test_conservative_input_bound_never_calls(api):
 C,E,cfg=api;calls=[]
 with C(cfg(max_input_tokens=10),transport=httpx.MockTransport(lambda req:calls.append(req))) as c:
  with pytest.raises(E) as exc:c.complete([{'role':'user','content':'X'*30}],request_id='test-6')
 assert exc.value.code=='input_limit' and calls==[]

@pytest.mark.parametrize('data',[reply(model='other/model'),reply(usage={'prompt_tokens':True,'completion_tokens':1}),reply(choices=[]),reply(choices=[{'finish_reason':'length','message':{'content':'partial'}}])])
def test_malformed_or_wrong_model_reply_rejected(api,data):
 C,E,cfg=api
 with C(cfg(),transport=httpx.MockTransport(lambda req:httpx.Response(200,json=data))) as c:
  with pytest.raises(E):c.complete([{'role':'user','content':'X'}],request_id='test-7')

def test_non_official_api_base_never_calls(api):
 C,E,cfg=api;calls=[]
 with pytest.raises(E):
  with C(cfg(api_base='https://invalid.example/v1'),transport=httpx.MockTransport(lambda req:calls.append(req))) as c:c.complete([{'role':'user','content':'X'}],request_id='test-8')
 assert calls==[]


def test_provider_reported_metadata_preserved_without_reasoning(api):
 from decimal import Decimal
 C,E,cfg=api;d=reply(provider='Alibaba',id='gen-synthetic',usage={'prompt_tokens':30,'completion_tokens':12,'cost':0.000021});d['choices'][0]['message']['reasoning']='PRIVATE REASONING MUST NOT BE RETURNED'
 with C(cfg(),transport=httpx.MockTransport(lambda req:httpx.Response(200,json=d))) as c:r=c.complete([{'role':'user','content':'X'}],request_id='metadata-1')
 assert r.provider=='Alibaba' and r.response_id=='gen-synthetic' and Decimal(r.reported_cost)==Decimal('0.000021') and 'PRIVATE REASONING' not in repr(r)

@pytest.mark.parametrize('cost',[-1,True,'NaN'])
def test_bad_cost_metadata_rejected(api,cost):
 C,E,cfg=api;d=reply(usage={'prompt_tokens':30,'completion_tokens':12,'cost':cost})
 with C(cfg(),transport=httpx.MockTransport(lambda req:httpx.Response(200,json=d))) as c:
  with pytest.raises(E) as exc:c.complete([{'role':'user','content':'X'}],request_id='metadata-2')
 assert exc.value.code=='invalid_response'


def test_remote_optin_uses_verified_native_os_context(api,monkeypatch):
 import types,ssl
 C,E,cfg=api;seen=[];ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
 class FakeClient:
  def __init__(self,**kw):seen.append(kw)
  def close(self):pass
 def factory(protocol):assert protocol==ssl.PROTOCOL_TLS_CLIENT;return ctx
 monkeypatch.setitem(sys.modules,'truststore',types.SimpleNamespace(SSLContext=factory));monkeypatch.setattr(httpx,'Client',FakeClient)
 with C(cfg(),allow_remote=True):pass
 assert seen[0]['verify'] is ctx and ctx.check_hostname is True and ctx.verify_mode==ssl.CERT_REQUIRED and seen[0]['trust_env'] is False

def test_remote_invalid_trust_context_fails_closed(api,monkeypatch):
 import types,ssl
 C,E,cfg=api;seen=[];ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.check_hostname=False
 monkeypatch.setitem(sys.modules,'truststore',types.SimpleNamespace(SSLContext=lambda protocol:ctx));monkeypatch.setattr(httpx,'Client',lambda **kw:seen.append(kw))
 with pytest.raises(E):C(cfg(),allow_remote=True)
 assert seen==[]


def test_verified_canonical_alias_keeps_requested_model(api):
 C,E,cfg=api;alias=MODEL+'-20260826';seen=[]
 def h(req):seen.append(json.loads(req.content)['model']);return httpx.Response(200,json=reply(model=alias))
 with C(cfg(),transport=httpx.MockTransport(h),response_model_aliases=(alias,)) as c:r=c.complete([{'role':'user','content':'X'}],request_id='canonical-1')
 assert seen==[MODEL] and r.model==MODEL

@pytest.mark.parametrize('aliases',[('other/model',),(MODEL+'-wrong',),(MODEL+'-20260826',MODEL+'-20260826'),[MODEL+'-20260826']])
def test_unverified_or_invalid_alias_configuration_rejected(api,aliases):
 C,E,cfg=api
 with pytest.raises(E):C(cfg(),transport=httpx.MockTransport(lambda req:None),response_model_aliases=aliases)
