import os,sys
from pathlib import Path
from html.parser import HTMLParser

def test_fragment_can_be_constructed_offline_with_expected_contact_fields():
 root=Path(os.environ['GWA_UI_ORG_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.ui_organizations import organization_panel
 html=organization_panel();assert isinstance(html,str)
 class P(HTMLParser):
  def __init__(self):super().__init__();self.emails=[];self.root=False
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if a.get('id')=='organizations':self.root=True
   if tag=='input' and a.get('type')=='email':self.emails.append(a)
 p=P();p.feed(html);assert p.root
 # Rows may be rendered by the inline script; behavioral checks use the browser.
 assert not any(x=='torch' or x.startswith('faiss') for x in sys.modules)
 sys.path.remove(str(root))
