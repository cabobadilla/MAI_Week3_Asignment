import os,sys,sqlite3
from pathlib import Path
import pytest

@pytest.fixture
def service(tmp_path):
 root=Path(os.environ.get('GWA_AUTH_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app.storage import initialize
 from app.auth import AuthService
 db=tmp_path/'auth.sqlite';initialize(db,Path(os.environ.get('GWA_SCHEMA_FILE',str(Path(__file__).resolve().parents[1]/'app/migrations/001_initial.sql'))));clock=[1000.0];auth=AuthService(db,clock=lambda:clock[0])
 yield auth,clock,db
 sys.path.remove(str(root))

@pytest.mark.parametrize('password',['12345678','more-than-eight-characters','🙂'*8])
def test_setup_login_hashed(service,password):
 a,clock,path=service;a.setup(password,password);session=a.login(password);assert session['token'] and session['csrf'];assert a.authenticate(session['token']) is not None
 c=sqlite3.connect(path);stored=c.execute('SELECT encoded_password_hash FROM operator_credentials').fetchone()[0];c.close();assert password not in stored and stored.startswith('$argon2id$')

def test_setup_short_or_mismatch(service):
 a,clock,path=service
 for x,y in [('1234567','1234567'),('12345678','12345679')]:
  with pytest.raises(ValueError):a.setup(x,y)

def test_no_silent_trim(service):
 a,clock,path=service;a.setup(' 12345678 ',' 12345678 ')
 with pytest.raises(ValueError):a.login('12345678')
 assert a.login(' 12345678 ')['token']

def test_repeat_setup_cannot_overwrite(service):
 a,clock,path=service;a.setup('12345678','12345678')
 with pytest.raises(ValueError):a.setup('otherpass','otherpass')
 assert a.login('12345678')['token']

def test_unknown_session_and_logout(service):
 a,clock,path=service;a.setup('12345678','12345678');assert a.authenticate('missing') is None;s=a.login('12345678');a.logout(s['token']);assert a.authenticate(s['token']) is None

def test_idle_expiry(service):
 a,t,path=service;a.setup('12345678','12345678');s=a.login('12345678');t[0]+=1801;assert a.authenticate(s['token']) is None

def test_absolute_expiry_even_with_touches(service):
 a,t,path=service;a.setup('12345678','12345678');s=a.login('12345678')
 for _ in range(28):t[0]+=1000;assert a.authenticate(s['token']) is not None
 t[0]+=1000;assert a.authenticate(s['token']) is None

def test_rate_limit_and_reset(service):
 a,t,path=service;a.setup('12345678','12345678')
 for _ in range(5):
  with pytest.raises(ValueError):a.login('wrong',client_id='fixture')
 with pytest.raises(ValueError):a.login('12345678',client_id='fixture')
 t[0]+=301;assert a.login('12345678',client_id='fixture')['token']

def test_restart_clears_sessions_not_password(service):
 a,t,path=service;a.setup('12345678','12345678');s=a.login('12345678');b=type(a)(path,clock=lambda:t[0]);assert b.authenticate(s['token']) is None;assert b.login('12345678')['token']

def test_password_not_in_errors_or_repr(service):
 a,t,path=service;secret='synthetic-password';a.setup(secret,secret)
 with pytest.raises(ValueError) as e:a.login('synthetic-wrong-password')
 assert 'synthetic-wrong-password' not in str(e.value) and secret not in repr(a)

def test_csrf_changes_between_sessions(service):
 a,t,path=service;a.setup('12345678','12345678');x=a.login('12345678');y=a.login('12345678');assert x['token']!=y['token'] and x['csrf']!=y['csrf']
