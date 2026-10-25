import os,sys
from pathlib import Path
from html.parser import HTMLParser

def test_campaign_panel_is_constructible_offline():
 root=Path(os.environ['GWA_UI_CAMPAIGN_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.ui_campaigns import campaigns_panel
 html=campaigns_panel();assert isinstance(html,str)
 class P(HTMLParser):
  root=False
  def handle_starttag(self,t,a):
   a=dict(a)
   if a.get('id')=='campaigns':self.root=True
   if t in ['script','iframe']:assert not a.get('src')
 p=P();p.feed(html);assert p.root;assert not any(x=='torch' or x.startswith('faiss') for x in sys.modules)
 sys.path.remove(str(root))
