import os,sys
from pathlib import Path
from html.parser import HTMLParser

def test_workspace_constructs_offline_without_provider_or_native_imports():
 root=Path(os.environ['GWA_UI_WORK_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.ui_work import workspace_panel
 html=workspace_panel();assert isinstance(html,str)
 class P(HTMLParser):
  def __init__(self):super().__init__();self.ids=set()
  def handle_starttag(self,t,a):
   a=dict(a)
   if 'id' in a:self.ids.add(a['id'])
   if t in ['script','iframe']:assert not a.get('src')
 p=P();p.feed(html);assert {'work','work-actions','work-exports'}<=p.ids
 assert not any(x=='torch' or x.startswith('faiss') for x in sys.modules)
 sys.path.remove(str(root))
