import os,sys
from pathlib import Path
from html.parser import HTMLParser

def test_directed_record_controls_construct_without_network_or_native_models():
 root=Path(os.environ['GWA_UI_DIRECTED_RECORD_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.ui_directed_record import directed_record_controls
 html=directed_record_controls();assert isinstance(html,str)
 class P(HTMLParser):
  def handle_starttag(self,t,a):
   a=dict(a)
   if t in ['script','iframe']:assert not a.get('src')
 P().feed(html);assert not any(x=='torch' or x.startswith('faiss') for x in sys.modules)
 sys.path.remove(str(root))
