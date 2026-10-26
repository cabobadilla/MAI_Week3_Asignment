_SHELL = '''<!doctype html>
<html lang='es'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<meta name='color-scheme' content='light'>
<title>GrowWithAI · Mesa editorial</title>
<style>
  :root {
    --gwa-ink: #173a35;
    --gwa-green: #215b48;
    --gwa-paper: #fffef9;
    --gwa-bg: #f3f4ed;
    --gwa-line: #dce3d5;
    --gwa-muted: #5b6b63;
    --gwa-amber-bg: #f8e7b2;
    --gwa-amber-ink: #6b4b00;
    --gwa-danger-bg: #fff4ef;
    --gwa-danger-line: #e4b8aa;
    --gwa-danger-ink: #7a2f21;
    --gwa-radius: 16px;
    --ink: var(--gwa-ink);
    --green: var(--gwa-green);
    --paper: var(--gwa-paper);
    --bg: var(--gwa-bg);
    --line: var(--gwa-line);
    --muted: var(--gwa-muted);
  }
  *,
  *::before,
  *::after { box-sizing: border-box; }
  [hidden] { display: none !important; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    overflow-x: hidden;
    background: var(--gwa-bg);
    color: var(--gwa-ink);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.55;
  }
  button,
  input { font: inherit; }
  button { cursor: pointer; }
  :focus-visible { outline: 3px solid #d6a924; outline-offset: 3px; }
  .gwa-loading {
    min-height: 100vh;
    min-height: 100dvh;
    display: grid;
    place-items: center;
    padding: 24px;
    background: var(--gwa-bg);
  }
  .gwa-loading-card {
    padding: 18px 22px;
    border: 1px solid var(--gwa-line);
    border-radius: var(--gwa-radius);
    background: var(--gwa-paper);
    color: var(--gwa-muted);
    font-weight: 600;
  }
  .gwa-auth-wrap {
    min-height: 100vh;
    min-height: 100dvh;
    display: grid;
    place-items: center;
    padding: 24px 16px;
  }
  .gwa-auth-card {
    width: 100%;
    max-width: 460px;
    padding: clamp(20px, 5vw, 32px);
    border: 1px solid var(--gwa-line);
    border-radius: var(--gwa-radius);
    background: var(--gwa-paper);
  }
  .gwa-auth-eyebrow {
    margin: 0 0 4px;
    color: var(--gwa-green);
    font-size: .78rem;
    font-weight: 800;
    letter-spacing: .12em;
    text-transform: uppercase;
  }
  .gwa-auth-card h1 {
    margin: 0;
    color: var(--gwa-ink);
    font-size: clamp(1.65rem, 5vw, 2rem);
    line-height: 1.12;
    letter-spacing: -.03em;
  }
  .gwa-auth-intro { margin: 10px 0 20px; color: var(--gwa-muted); }
  .gwa-alert {
    margin: 0 0 16px;
    padding: 10px 12px;
    border: 1px solid var(--gwa-danger-line);
    border-radius: 12px;
    background: var(--gwa-danger-bg);
    color: var(--gwa-danger-ink);
    font-size: .92rem;
    overflow-wrap: anywhere;
  }
  .gwa-field { margin: 0 0 14px; }
  .gwa-field label {
    display: block;
    margin: 0 0 6px;
    color: var(--gwa-ink);
    font-size: .92rem;
    font-weight: 700;
  }
  .gwa-input {
    width: 100%;
    min-height: 46px;
    padding: 10px 12px;
    border: 1px solid var(--gwa-line);
    border-radius: 12px;
    background: #ffffff;
    color: var(--gwa-ink);
  }
  .gwa-input:focus {
    border-color: var(--gwa-green);
    outline: 3px solid rgba(33, 91, 72, .18);
    outline-offset: 0;
  }
  .gwa-primary {
    width: 100%;
    min-height: 46px;
    padding: 10px 16px;
    border: 1px solid var(--gwa-green);
    border-radius: 12px;
    background: var(--gwa-green);
    color: var(--gwa-paper);
    font-weight: 700;
  }
  .gwa-primary:hover:not(:disabled) { background: #1a4a3b; }
  .gwa-primary:disabled { opacity: .68; cursor: not-allowed; }
  .gwa-fineprint {
    margin: 18px 0 0;
    padding-top: 14px;
    border-top: 1px solid var(--gwa-line);
    color: var(--gwa-muted);
    font-size: .82rem;
  }
  .gwa-header {
    width: 100%;
    background: var(--gwa-paper);
    border-bottom: 1px solid var(--gwa-line);
  }
  .gwa-header-inner {
    width: 100%;
    max-width: 1120px;
    margin: 0 auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .gwa-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    min-width: 0;
  }
  .gwa-brand {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 2px 10px;
    min-width: 0;
  }
  .gwa-brand-name {
    color: var(--gwa-ink);
    font-size: 1.08rem;
    font-weight: 800;
    letter-spacing: -.02em;
  }
  .gwa-brand-sub { color: var(--gwa-muted); font-size: .88rem; font-weight: 650; }
  .gwa-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 10px;
    min-width: 0;
  }
  .gwa-demo-badge {
    max-width: 100%;
    padding: 6px 10px;
    border: 1px solid #e7cf91;
    border-radius: 999px;
    background: var(--gwa-amber-bg);
    color: var(--gwa-amber-ink);
    font-size: .72rem;
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: .01em;
    text-align: center;
    overflow-wrap: anywhere;
  }
  .gwa-logout {
    min-height: 38px;
    padding: 7px 12px;
    border: 1px solid var(--gwa-line);
    border-radius: 999px;
    background: var(--gwa-paper);
    color: var(--gwa-green);
    font-weight: 700;
  }
  .gwa-logout:hover:not(:disabled) { border-color: var(--gwa-green); }
  .gwa-logout:disabled { opacity: .65; cursor: not-allowed; }
  .gwa-nav { display: flex; flex-wrap: wrap; gap: 8px; min-width: 0; }
  .gwa-nav button {
    min-height: 40px;
    padding: 8px 14px;
    border: 1px solid var(--gwa-line);
    border-radius: 999px;
    background: var(--gwa-bg);
    color: var(--gwa-ink);
    font-weight: 700;
  }
  .gwa-nav button:hover { border-color: var(--gwa-green); }
  .gwa-nav button.is-active {
    border-color: var(--gwa-green);
    background: var(--gwa-green);
    color: var(--gwa-paper);
  }
  .gwa-main {
    width: 100%;
    max-width: 1120px;
    margin: 0 auto;
    padding: 20px 16px 48px;
  }
  .gwa-notice {
    margin: 0 0 18px;
    padding: 14px 16px;
    border: 1px solid var(--gwa-line);
    border-radius: var(--gwa-radius);
    background: var(--gwa-paper);
  }
  .gwa-notice p { margin: 0; color: var(--gwa-muted); font-size: .9rem; }
  .gwa-notice p + p { margin-top: 6px; }
  .gwa-notice strong { color: var(--gwa-ink); }
  #gwaPanels { min-width: 0; max-width: 100%; }
  #gwaPanels > * { max-width: 100%; min-width: 0; }
  @media (max-width: 520px) {
    .gwa-actions { width: 100%; justify-content: space-between; }
    .gwa-demo-badge { flex: 1 1 220px; }
    .gwa-logout { flex: 0 0 auto; }
    .gwa-nav button { flex: 1 1 auto; }
    .gwa-main { padding: 16px 16px 40px; }
  }
</style>
<script>
(function () {
  'use strict';

  var VIEW_IDS = ['organizations', 'campaigns', 'work', 'tracking', 'directed'];
  var NAV_FOR = {
    organizations: 'organizations',
    campaigns: 'campaigns',
    work: 'campaigns',
    tracking: 'tracking',
    directed: 'tracking'
  };

  var csrfToken = null;
  var authenticated = false;
  var setupRequired = false;
  var authMode = null;
  var lastView = 'organizations';

  window.gwaCampaignId = null;

  function byId(id) {
    return document.getElementById(id);
  }

  function sanitizeDetail(value) {
    if (typeof value !== 'string') return '';
    var clean = '';
    for (var i = 0; i < value.length; i += 1) {
      var code = value.charCodeAt(i);
      clean += (code < 32 || code === 127) ? ' ' : value.charAt(i);
    }
    return clean.trim().slice(0, 240);
  }

  function hidePanels() {
    for (var i = 0; i < VIEW_IDS.length; i += 1) {
      var panel = byId(VIEW_IDS[i]);
      if (panel) panel.hidden = true;
    }
  }

  function updateNav(activeView) {
    var nav = byId('gwaNav');
    if (!nav) return;
    var navId = NAV_FOR[activeView];
    var buttons = nav.querySelectorAll('button[data-gwa-view]');
    for (var i = 0; i < buttons.length; i += 1) {
      var button = buttons[i];
      var isActive = button.getAttribute('data-gwa-view') === navId;
      button.classList.toggle('is-active', isActive);
      if (isActive) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    }
  }

  function gwaShowView(id) {
    if (typeof id !== 'string' || VIEW_IDS.indexOf(id) === -1) return false;
    lastView = id;
    for (var i = 0; i < VIEW_IDS.length; i += 1) {
      var panel = byId(VIEW_IDS[i]);
      if (panel) panel.hidden = VIEW_IDS[i] !== id;
    }
    updateNav(id);
    document.dispatchEvent(new CustomEvent('gwa:show', { detail: id }));
    return true;
  }
  window.gwaShowView = gwaShowView;

  async function gwaApi(path, method, data) {
    var verb = String(method || 'GET').toUpperCase();
    if (typeof path !== 'string' || path.indexOf('/api/') !== 0 || path.indexOf('//') !== -1) {
      throw new Error('Solicitud no válida.');
    }
    var headers = {};
    var options = { method: verb, credentials: 'same-origin', headers: headers };
    if (data !== undefined) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(data);
    }
    var unsafe = verb !== 'GET' && verb !== 'HEAD' && verb !== 'OPTIONS';
    if (unsafe && csrfToken) headers['X-CSRF-Token'] = csrfToken;
    var response;
    try {
      response = await fetch(path, options);
    } catch (error) {
      throw new Error('No se pudo conectar con el servidor local.');
    }
    var raw = '';
    try {
      raw = await response.text();
    } catch (error) {
      raw = '';
    }
    var payload = null;
    if (raw) {
      try {
        payload = JSON.parse(raw);
      } catch (error) {
        payload = null;
      }
    }
    if (!response.ok) {
      if (response.status === 401) handleUnauthorized();
      var detail = '';
      if (payload && typeof payload === 'object') {
        if (typeof payload.detail === 'string') detail = payload.detail;
        else if (typeof payload.message === 'string') detail = payload.message;
      }
      detail = sanitizeDetail(detail);
      throw new Error(detail || 'La solicitud no se pudo completar.');
    }
    return payload === null ? {} : payload;
  }
  window.gwaApi = gwaApi;

  function setAuthError(message) {
    var node = byId('gwaAuthError');
    if (!node) return;
    node.textContent = message ? String(message) : '';
    node.hidden = !message;
  }

  function clearAuthError() {
    setAuthError('');
  }

  function clearPasswordInputs() {
    var ids = ['gwaLoginPassword', 'gwaSetupPassword', 'gwaSetupConfirmation'];
    for (var i = 0; i < ids.length; i += 1) {
      var input = byId(ids[i]);
      if (input) input.value = '';
    }
  }

  function setPending(button, pending, busyLabel, idleLabel) {
    if (!button) return;
    button.disabled = !!pending;
    button.textContent = pending ? busyLabel : idleLabel;
    if (pending) button.setAttribute('aria-busy', 'true');
    else button.removeAttribute('aria-busy');
  }

  function setAuthMode(mode) {
    authMode = mode === 'setup' ? 'setup' : 'login';
    var loginForm = byId('gwaLoginForm');
    var setupForm = byId('gwaSetupForm');
    var intro = byId('gwaAuthIntro');
    if (loginForm) loginForm.hidden = authMode !== 'login';
    if (setupForm) setupForm.hidden = authMode !== 'setup';
    if (intro) {
      intro.textContent = authMode === 'setup'
        ? 'Crea una contraseña local de al menos 8 caracteres para esta instalación.'
        : 'Ingresa la contraseña local para continuar.';
    }
  }

  function showAuth(mode, message) {
    var loading = byId('gwaLoading');
    var auth = byId('gwaAuth');
    var header = byId('gwaHeader');
    var main = byId('gwaMain');
    if (loading) loading.hidden = true;
    if (auth) auth.hidden = false;
    if (header) header.hidden = true;
    if (main) main.hidden = true;
    setAuthMode(mode);
    if (message) setAuthError(message);
  }

  function showApp() {
    var loading = byId('gwaLoading');
    var auth = byId('gwaAuth');
    var header = byId('gwaHeader');
    var main = byId('gwaMain');
    if (loading) loading.hidden = true;
    if (auth) auth.hidden = true;
    if (header) header.hidden = false;
    if (main) main.hidden = false;
    gwaShowView(lastView);
  }

  function handleUnauthorized() {
    var wasAuthenticated = authenticated;
    csrfToken = null;
    authenticated = false;
    window.gwaCampaignId = null;
    hidePanels();
    showAuth(wasAuthenticated ? 'login' : (authMode === 'setup' ? 'setup' : 'login'));
    if (wasAuthenticated) {
      clearPasswordInputs();
      setAuthError('La sesión terminó. Ingresa de nuevo para continuar.');
    }
  }

  async function performLogout() {
    var button = byId('gwaLogout');
    if (!button || button.disabled) return;
    var previousError = byId('gwaLogoutError');
    if (previousError) previousError.remove();
    button.disabled = true;
    button.textContent = 'Saliendo…';
    try {
      await gwaApi('/api/auth/logout', 'POST', {});
    } catch (error) {
      if (authenticated) {
        button.disabled = false;
        button.textContent = 'Cerrar sesión';
        var logoutError = document.createElement('p');
        logoutError.id = 'gwaLogoutError';
        logoutError.setAttribute('role', 'alert');
        logoutError.textContent = 'No se pudo confirmar el cierre de sesión. Reintenta.';
        if (button.parentElement) button.parentElement.appendChild(logoutError);
        return;
      }
    }
    csrfToken = null;
    authenticated = false;
    setupRequired = false;
    window.gwaCampaignId = null;
    lastView = 'organizations';
    clearPasswordInputs();
    hidePanels();
    clearAuthError();
    showAuth('login');
    try {
      window.location.reload();
    } catch (error) {
      // La pantalla de acceso queda visible si el navegador no puede recargar.
    }
  }

  async function initializeAuth() {
    try {
      var session = await gwaApi('/api/session', 'GET');
      if (!session || typeof session !== 'object') throw new Error('Sesión no disponible.');
      if (session.authenticated === true) {
        if (typeof session.csrf !== 'string' || session.csrf.length === 0) {
          throw new Error('Sesión no disponible.');
        }
        csrfToken = session.csrf;
        setupRequired = false;
        authenticated = true;
        showApp();
        return;
      }
      csrfToken = null;
      authenticated = false;
      setupRequired = session.setup_required === true;
      showAuth(setupRequired ? 'setup' : 'login');
    } catch (error) {
      csrfToken = null;
      authenticated = false;
      showAuth('login');
      setAuthError('No se pudo verificar la sesión. Recarga la página para intentarlo de nuevo.');
    }
  }

  async function onLoginSubmit(event) {
    event.preventDefault();
    var passwordInput = byId('gwaLoginPassword');
    var button = byId('gwaLoginButton');
    if (!passwordInput || !button || button.disabled) return;
    clearAuthError();
    var password = passwordInput.value;
    setPending(button, true, 'Ingresando…', 'Ingresar');
    try {
      var result = await gwaApi('/api/auth/login', 'POST', { password: password });
      if (!result || result.ok !== true || typeof result.csrf !== 'string' || result.csrf.length === 0) {
        throw new Error('Respuesta de acceso no válida.');
      }
      csrfToken = result.csrf;
      setupRequired = false;
      authenticated = true;
      clearPasswordInputs();
      showApp();
    } catch (error) {
      setAuthError('No se pudo iniciar sesión. Verifica la contraseña e inténtalo de nuevo.');
    } finally {
      setPending(button, false, '', 'Ingresar');
    }
  }

  async function onSetupSubmit(event) {
    event.preventDefault();
    var passwordInput = byId('gwaSetupPassword');
    var confirmationInput = byId('gwaSetupConfirmation');
    var button = byId('gwaSetupButton');
    if (!passwordInput || !confirmationInput || !button || button.disabled) return;
    clearAuthError();
    var password = passwordInput.value;
    var confirmation = confirmationInput.value;
    if (password.length < 8) {
      setAuthError('La contraseña debe tener al menos 8 caracteres.');
      passwordInput.focus();
      return;
    }
    if (password !== confirmation) {
      setAuthError('Las contraseñas no coinciden.');
      confirmationInput.focus();
      return;
    }
    setPending(button, true, 'Creando…', 'Crear contraseña');
    var setupDone = false;
    try {
      await gwaApi('/api/auth/setup', 'POST', { password: password, confirmation: confirmation });
      setupDone = true;
      var result = await gwaApi('/api/auth/login', 'POST', { password: password });
      if (!result || result.ok !== true || typeof result.csrf !== 'string' || result.csrf.length === 0) {
        throw new Error('Respuesta de acceso no válida.');
      }
      csrfToken = result.csrf;
      setupRequired = false;
      authenticated = true;
      clearPasswordInputs();
      showApp();
    } catch (error) {
      if (setupDone) {
        setupRequired = false;
        clearPasswordInputs();
        setAuthMode('login');
        setAuthError('Contraseña creada. Ingresa con tu contraseña para continuar.');
        var loginInput = byId('gwaLoginPassword');
        if (loginInput) loginInput.focus();
      } else {
        setAuthError('No se pudo crear la contraseña. Inténtalo de nuevo.');
      }
    } finally {
      setPending(button, false, '', 'Crear contraseña');
    }
  }

  function boot() {
    var nav = byId('gwaNav');
    if (nav) {
      nav.addEventListener('click', function (event) {
        var button = event.target && event.target.closest ? event.target.closest('button[data-gwa-view]') : null;
        if (!button || !nav.contains(button)) return;
        gwaShowView(button.getAttribute('data-gwa-view'));
      });
    }
    var logoutButton = byId('gwaLogout');
    if (logoutButton) logoutButton.addEventListener('click', function () { performLogout(); });
    var loginForm = byId('gwaLoginForm');
    if (loginForm) loginForm.addEventListener('submit', onLoginSubmit);
    var setupForm = byId('gwaSetupForm');
    if (setupForm) setupForm.addEventListener('submit', onSetupSubmit);
    initializeAuth();
  }

  function scheduleBoot() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        window.setTimeout(boot, 0);
      }, { once: true });
    } else {
      window.setTimeout(boot, 0);
    }
  }

  scheduleBoot();
})();
</script>
</head>
<body>
<div id='gwaLoading' class='gwa-loading' role='status' aria-live='polite'>
  <div class='gwa-loading-card'>Cargando…</div>
</div>
<div id='gwaAuth' hidden>
  <div class='gwa-auth-wrap'>
    <section class='gwa-auth-card' aria-labelledby='gwaAuthTitle'>
      <p class='gwa-auth-eyebrow'>GrowWithAI</p>
      <h1 id='gwaAuthTitle'>Mesa editorial</h1>
      <p id='gwaAuthIntro' class='gwa-auth-intro'>Verificando acceso local…</p>
      <div id='gwaAuthError' class='gwa-alert' role='alert' hidden></div>
      <form id='gwaLoginForm' method='post' hidden>
        <div class='gwa-field'>
          <label for='gwaLoginPassword'>Contraseña</label>
          <input id='gwaLoginPassword' name='password' class='gwa-input' type='password' autocomplete='current-password' required>
        </div>
        <button id='gwaLoginButton' class='gwa-primary' type='submit'>Ingresar</button>
      </form>
      <form id='gwaSetupForm' method='post' hidden>
        <div class='gwa-field'>
          <label for='gwaSetupPassword'>Contraseña</label>
          <input id='gwaSetupPassword' name='password' class='gwa-input' type='password' autocomplete='new-password' minlength='8' required>
        </div>
        <div class='gwa-field'>
          <label for='gwaSetupConfirmation'>Confirmar contraseña</label>
          <input id='gwaSetupConfirmation' name='confirmation' class='gwa-input' type='password' autocomplete='new-password' minlength='8' required>
        </div>
        <button id='gwaSetupButton' class='gwa-primary' type='submit'>Crear contraseña</button>
      </form>
      <p class='gwa-fineprint'>Acceso local para la mesa editorial.</p>
    </section>
  </div>
</div>
<header id='gwaHeader' class='gwa-header' hidden>
  <div class='gwa-header-inner'>
    <div class='gwa-topbar'>
      <div class='gwa-brand' aria-label='GrowWithAI, Mesa editorial'>
        <span class='gwa-brand-name'>GrowWithAI</span>
        <span class='gwa-brand-sub'>Mesa editorial</span>
      </div>
      <div class='gwa-actions'>
        <span class='gwa-demo-badge'>DEMO · generación simulada · sin llamadas LLM</span>
        <button id='gwaLogout' class='gwa-logout' type='button'>Cerrar sesión</button>
      </div>
    </div>
    <nav id='gwaNav' class='gwa-nav' aria-label='Navegación editorial'>
      <button type='button' data-gwa-view='organizations'>Organizaciones</button>
      <button type='button' data-gwa-view='campaigns'>Campañas</button>
      <button type='button' data-gwa-view='tracking'>Registro y contexto</button>
    </nav>
  </div>
</header>
<main id='gwaMain' class='gwa-main' hidden>
  <section class='gwa-notice' aria-label='Aviso de demo local'>
    <p><strong>Demo local con SQLite persistente.</strong> Organizaciones, campañas y registros se guardan en este equipo; la exportación no publica ni envía datos.</p>
    <p>Los envíos y publicaciones se registran manualmente; ocurren fuera de esta app.</p>
  </section>
  <div id='gwaPanels'>
<!--GWA_PANELS-->
  </div>
</main>
</body>
</html>
'''


def render_shell(panels: list[str], *, real: bool = False) -> str:
    html = _SHELL
    if real:
        html = html.replace(
            'DEMO · generación simulada · sin llamadas LLM',
            'IA real · Qwen vía OpenRouter · aprobación humana',
        )
        html = html.replace(
            "aria-label='Aviso de demo local'",
            "aria-label='Aviso de app local'",
        )
        html = html.replace(
            '<strong>Demo local con SQLite persistente.</strong>',
            '<strong>App local con SQLite persistente.</strong>',
        )
    return html.replace('<!--GWA_PANELS-->', ''.join(panels))
