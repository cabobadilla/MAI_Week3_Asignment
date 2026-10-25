import os,sys
from pathlib import Path
from html.parser import HTMLParser

def test_shell_composes_trusted_fragments_without_loading_model_or_files():
 root=Path(os.environ['GWA_UI_SHELL_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.ui_shell import render_shell
 from app.ui_organizations import organization_panel
 html=render_shell([organization_panel()]);assert isinstance(html,str) and '<!doctype html' in html.lower();assert 'organizations' in html
 assert not any(x=='torch' or x.startswith('faiss') for x in sys.modules)
 class P(HTMLParser):
  def handle_starttag(self,t,a):
   d=dict(a)
   if t in ['script','iframe']:assert not d.get('src')
   if t=='link':assert not d.get('href','').startswith(('http:','https:','//'))
 P().feed(html)
 sys.path.remove(str(root))
