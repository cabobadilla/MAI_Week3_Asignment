def directed_panel() -> str:
    return '''<div id='directed' hidden>
<style>
#directed{width:100%;max-width:375px;margin:0 auto;background:#fffef9;color:#173a35;font-family:inherit;overflow-x:hidden;overflow-wrap:anywhere;}
#directed[hidden]{display:none !important;}
#directed *{box-sizing:border-box;min-width:0;}
#directed .directed-shell{padding:12px;display:grid;grid-template-columns:minmax(0,1fr);gap:16px;}
#directed .directed-tabs{display:grid;grid-template-columns:minmax(0,1fr);gap:8px;}
#directed button,#directed select,#directed .directed-contact{min-height:44px;}
#directed button{width:100%;border:1px solid #dce3d5;border-radius:8px;background:#fffef9;color:#173a35;font:inherit;padding:10px 12px;text-align:left;cursor:pointer;}
#directed button[aria-selected='true']{background:#215b48;color:#fffef9;border-color:#215b48;}
#directed button:disabled{opacity:0.55;cursor:not-allowed;}
#directed select{width:100%;border:1px solid #dce3d5;border-radius:8px;background:#fffef9;color:#173a35;font:inherit;padding:8px 10px;}
#directed .directed-field,#directed .directed-section{display:grid;grid-template-columns:minmax(0,1fr);gap:10px;}
#directed .directed-label{font-weight:700;}
#directed h1,#directed h2,#directed h3{font:inherit;margin:0;color:#173a35;}
#directed h1{font-size:1.15rem;color:#215b48;}
#directed h2{font-size:1rem;}
#directed h3{font-size:0.95rem;}
#directed .directed-status{margin:0;color:#48685e;font-size:0.9rem;line-height:1.4;}
#directed .directed-contact{display:flex;align-items:center;gap:10px;padding:8px;border:1px solid #dce3d5;border-radius:8px;background:#fffef9;overflow-wrap:anywhere;}
#directed .directed-contact span{min-width:0;overflow-wrap:anywhere;}
#directed input[type='checkbox']{width:20px;height:20px;min-width:20px;accent-color:#215b48;}
#directed .directed-list{display:grid;grid-template-columns:minmax(0,1fr);gap:8px;}
#directed .directed-history-item{border:1px solid #dce3d5;border-radius:8px;padding:10px;display:grid;grid-template-columns:minmax(0,1fr);gap:6px;background:#fffef9;}
#directed .directed-superseded{border-left:4px solid #215b48;}
#directed .directed-meta{margin:0;color:#48685e;font-size:0.85rem;line-height:1.4;}
#directed .directed-body{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.45;}
#directed .directed-badge{display:inline-block;border:1px solid #dce3d5;border-radius:999px;padding:2px 8px;color:#215b48;font-size:0.78rem;}
#directed .directed-group-title{margin-top:4px;}
#directed ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:minmax(0,1fr);gap:8px;}
#directed .directed-prepared-item{border:1px solid #dce3d5;border-radius:8px;padding:8px;background:#fffef9;display:grid;gap:2px;overflow-wrap:anywhere;}
#directed .directed-prepared-person{font-weight:600;overflow-wrap:anywhere;}
#directed [role='alert']{margin:0;border:1px solid #b42318;border-radius:8px;background:#fff4f2;color:#7a271a;padding:8px;font-size:0.9rem;}
</style>
<div class='directed-shell'>
  <div class='directed-tabs' role='tablist' aria-label='Publicaciones'>
    <button id='directed-tab-tracking' type='button' role='tab' aria-selected='false'>Publicaciones generales</button>
    <button id='directed-tab-directed' type='button' role='tab' aria-selected='true' aria-current='page'>Comunicaciones dirigidas</button>
  </div>
  <h1>Comunicaciones dirigidas</h1>
  <p id='directed-no-campaign' class='directed-status' role='status'>Selecciona una campaña en Campañas</p>
  <p id='directed-load-error' role='alert' hidden></p>
  <div id='directed-content' hidden>
    <div class='directed-field'>
      <label class='directed-label' for='directed-org'>Organización</label>
      <select id='directed-org' disabled>
        <option value=''>Selecciona una organización</option>
      </select>
    </div>
    <section class='directed-section' aria-labelledby='directed-contacts-title'>
      <h2 id='directed-contacts-title'>Contactos</h2>
      <p id='directed-contacts-empty' class='directed-status'>Selecciona una organización para ver sus contactos.</p>
      <div id='directed-contacts' class='directed-list'></div>
    </section>
    <section class='directed-section' aria-labelledby='directed-prepare-title'>
      <h2 id='directed-prepare-title'>Preparar destinatarios</h2>
      <p class='directed-status'>Preparar destinatarios solo guarda los datos de destino. No se envía ninguna comunicación.</p>
      <button id='directed-prepare' type='button' disabled>Preparar destinatarios</button>
      <p id='directed-prepare-status' class='directed-status' role='status' aria-live='polite'></p>
      <p id='directed-prepare-error' role='alert' hidden></p>
    </section>
    <section id='directed-prepared' class='directed-section' aria-labelledby='directed-prepared-title' hidden>
      <h2 id='directed-prepared-title'>Destinatarios preparados</h2>
      <p id='directed-prepared-summary' class='directed-status'></p>
      <ul id='directed-prepared-list'></ul>
    </section>
    <section class='directed-section' aria-labelledby='directed-thread-title'>
      <h2 id='directed-thread-title'>Historial de la organización</h2>
      <p id='directed-thread-status' class='directed-status' role='status'></p>
      <div id='directed-thread' class='directed-list'></div>
    </section>
    <div id='directed-record-controls'></div>
    <div id='directed-note-controls'></div>
  </div>
</div>
<script>
(function () {
  'use strict';
  var root = document.getElementById('directed');
  if (!root || root.getAttribute('data-gwa-directed-init') === '1') { return; }
  root.setAttribute('data-gwa-directed-init', '1');
  root.hidden = true;
  var refs = {
    noCampaign: root.querySelector('#directed-no-campaign'),
    loadError: root.querySelector('#directed-load-error'),
    content: root.querySelector('#directed-content'),
    tabGeneral: root.querySelector('#directed-tab-tracking'),
    org: root.querySelector('#directed-org'),
    contacts: root.querySelector('#directed-contacts'),
    contactsEmpty: root.querySelector('#directed-contacts-empty'),
    prepare: root.querySelector('#directed-prepare'),
    prepareStatus: root.querySelector('#directed-prepare-status'),
    prepareError: root.querySelector('#directed-prepare-error'),
    prepared: root.querySelector('#directed-prepared'),
    preparedSummary: root.querySelector('#directed-prepared-summary'),
    preparedList: root.querySelector('#directed-prepared-list'),
    threadTitle: root.querySelector('#directed-thread-title'),
    threadStatus: root.querySelector('#directed-thread-status'),
    thread: root.querySelector('#directed-thread')
  };
  var state = { campaignId: null, organization: null, versions: [], preparedRecipients: [], thread: null, busy: false };
  var chosen = new Map();
  var organizations = [];
  var busyCount = 0;
  var campaignToken = 0;
  var threadToken = 0;
  var loadedCampaignId = null;
  var actionBusy = typeof window.gwaDirectedActionBusy === 'boolean' ? window.gwaDirectedActionBusy : false;
  function globalActionBusy() { return window.gwaDirectedActionBusy === true; }
  try {
    Object.defineProperty(window, 'gwaDirectedActionBusy', {
      configurable: true,
      enumerable: true,
      get: function () { return actionBusy; },
      set: function (value) { actionBusy = value === true; syncControls(); }
    });
  } catch (error) {
    window.gwaDirectedActionBusy = actionBusy;
  }
  function campaignIdText(value) {
    if (value === null || value === undefined) { return null; }
    var text = String(value);
    return text.length ? text : null;
  }
  function textOf(value) {
    if (value === null || value === undefined) { return ''; }
    return String(value);
  }
  function hasValue(value) {
    return value !== null && value !== undefined && value !== '';
  }
  function clearNode(node) {
    if (!node) { return; }
    while (node.firstChild) { node.removeChild(node.firstChild); }
  }
  function makeText(tagName, className, value) {
    var node = document.createElement(tagName);
    if (className) { node.className = className; }
    node.textContent = textOf(value);
    return node;
  }
  function showLoadError(message) {
    if (!refs.loadError) { return; }
    refs.loadError.textContent = textOf(message);
    refs.loadError.hidden = !message;
  }
  function showPrepareError(message) {
    if (!refs.prepareError) { return; }
    refs.prepareError.textContent = textOf(message);
    refs.prepareError.hidden = !message;
  }
  function showPrepareStatus(message) {
    if (refs.prepareStatus) { refs.prepareStatus.textContent = textOf(message); }
  }
  function syncControls() {
    if (!refs.prepare) { return; }
    var cid = campaignIdText(window.gwaCampaignId);
    var sameCampaign = cid !== null && cid === state.campaignId;
    var blocked = busyCount > 0 || globalActionBusy();
    refs.prepare.disabled = !sameCampaign || chosen.size === 0 || blocked;
    root.setAttribute('aria-busy', blocked ? 'true' : 'false');
  }
  function publish() {
    state.busy = busyCount > 0;
    var snapshot = {
      campaignId: state.campaignId,
      organization: state.organization || null,
      versions: Array.isArray(state.versions) ? state.versions.slice() : [],
      preparedRecipients: Array.isArray(state.preparedRecipients) ? state.preparedRecipients.slice() : [],
      thread: state.thread || null,
      busy: state.busy === true
    };
    window.gwaDirectedSnapshot = snapshot;
    syncControls();
    try {
      document.dispatchEvent(new CustomEvent('gwa:directed', { detail: snapshot }));
    } catch (error) {}
  }
  function beginBusy() {
    busyCount += 1;
    state.busy = true;
    publish();
  }
  function endBusy() {
    busyCount = busyCount > 0 ? busyCount - 1 : 0;
    state.busy = busyCount > 0;
    publish();
  }
  function callApi(path, method, data) {
    if (typeof window.gwaApi !== 'function') {
      return Promise.reject(new Error('API no disponible'));
    }
    try {
      if (method === 'POST') {
        return Promise.resolve(window.gwaApi(path, method, data));
      }
      return Promise.resolve(window.gwaApi(path, method || 'GET'));
    } catch (error) {
      return Promise.reject(error);
    }
  }
  function activeRecipients(data) {
    var raw = data && Array.isArray(data.recipients) ? data.recipients : [];
    var active = [];
    for (var index = 0; index < raw.length; index += 1) {
      var recipient = raw[index];
      if (recipient && typeof recipient === 'object' && !recipient.archived_at) {
        active.push(recipient);
      }
    }
    return active;
  }
  function recipientSnapshot(recipient) {
    if (!recipient || typeof recipient !== 'object') { return {}; }
    if (recipient.snapshot && typeof recipient.snapshot === 'object') { return recipient.snapshot; }
    return {};
  }
  function recipientText(recipient, key) {
    var snapshot = recipientSnapshot(recipient);
    if (hasValue(snapshot[key])) { return textOf(snapshot[key]); }
    if (recipient && hasValue(recipient[key])) { return textOf(recipient[key]); }
    return '';
  }
  function extractRecipients(response) {
    if (Array.isArray(response)) { return response; }
    if (!response || typeof response !== 'object') { return []; }
    if (Array.isArray(response.recipients)) { return response.recipients; }
    if (Array.isArray(response.prepared_recipients)) { return response.prepared_recipients; }
    if (response.data && Array.isArray(response.data.recipients)) { return response.data.recipients; }
    if (Array.isArray(response.data)) { return response.data; }
    return [];
  }
  function versionLabel(version) {
    var parts = [];
    if (version && hasValue(version.revision_no)) {
      parts.push('Versión ' + textOf(version.revision_no));
    } else {
      parts.push('Versión');
    }
    if (version && hasValue(version.format)) { parts.push(textOf(version.format)); }
    return parts.join(' · ');
  }
  function dateText(value) {
    if (!hasValue(value)) { return ''; }
    return textOf(value);
  }
  function describeRef(value) {
    if (!hasValue(value)) { return ''; }
    if (typeof value === 'object') {
      if (hasValue(value.id)) { return textOf(value.id); }
      if (hasValue(value.revision_no)) { return 'versión ' + textOf(value.revision_no); }
      return 'otro registro';
    }
    return textOf(value);
  }
  function noteLabel(note) {
    var raw = note && hasValue(note.display_kind) ? note.display_kind : note ? note.kind : '';
    var kind = textOf(raw).toLowerCase();
    if (kind === 'response' || kind === 'reply' || kind === 'respuesta') { return 'Respuesta'; }
    return 'Nota';
  }
  function renderPrepared() {
    if (!refs.prepared || !refs.preparedList) { return; }
    clearNode(refs.preparedList);
    var list = Array.isArray(state.preparedRecipients) ? state.preparedRecipients : [];
    var count = list.length;
    refs.prepared.hidden = count === 0;
    if (refs.preparedSummary) {
      refs.preparedSummary.textContent = count === 0 ? '' : count + ' destinatarios preparados';
    }
    for (var index = 0; index < list.length; index += 1) {
      var recipient = list[index];
      var name = recipientText(recipient, 'contact_name');
      var email = recipientText(recipient, 'email');
      var company = recipientText(recipient, 'company_name');
      var item = document.createElement('li');
      item.className = 'directed-prepared-item';
      var person = makeText('div', 'directed-prepared-person', name + (name && email ? ' — ' : '') + email);
      if (!person.textContent) { person.textContent = 'Destinatario preparado'; }
      item.appendChild(person);
      if (company) { item.appendChild(makeText('div', 'directed-meta', company)); }
      refs.preparedList.appendChild(item);
    }
  }
  function renderContacts() {
    if (!refs.contacts) { return; }
    clearNode(refs.contacts);
    var org = state.organization;
    var contacts = org && Array.isArray(org.contacts) ? org.contacts : [];
    if (!org) {
      if (refs.contactsEmpty) { refs.contactsEmpty.hidden = false; refs.contactsEmpty.textContent = 'Selecciona una organización para ver sus contactos.'; }
      syncControls();
      return;
    }
    if (!contacts.length) {
      if (refs.contactsEmpty) { refs.contactsEmpty.hidden = false; refs.contactsEmpty.textContent = 'Esta organización no tiene contactos.'; }
      syncControls();
      return;
    }
    if (refs.contactsEmpty) { refs.contactsEmpty.hidden = true; }
    contacts.forEach(function (contact) {
      if (!contact || contact.id === null || contact.id === undefined) { return; }
      var key = String(contact.id);
      var label = document.createElement('label');
      label.className = 'directed-contact';
      var input = document.createElement('input');
      input.type = 'checkbox';
      input.value = key;
      input.checked = chosen.has(key);
      input.setAttribute('data-contact-id', key);
      input.addEventListener('change', function () {
        if (input.checked) { chosen.set(key, contact.id); } else { chosen.delete(key); }
        invalidatePrepared();
        showPrepareError('');
        showPrepareStatus('');
        syncControls();
        publish();
      });
      var name = textOf(contact.name);
      var email = textOf(contact.email);
      label.appendChild(input);
      label.appendChild(makeText('span', '', name + ' — ' + email));
      refs.contacts.appendChild(label);
    });
    syncControls();
  }
  function renderRecord(record) {
    var data = record && typeof record === 'object' ? record : {};
    var article = document.createElement('article');
    article.className = 'directed-history-item';
    if (data.superseded_by !== null && data.superseded_by !== undefined && data.superseded_by !== false && data.superseded_by !== '') { article.className += ' directed-superseded'; }
    var meta = [];
    if (hasValue(data.occurred_at)) { meta.push(dateText(data.occurred_at)); }
    if (hasValue(data.campaign_title)) { meta.push(textOf(data.campaign_title)); }
    if (meta.length) { article.appendChild(makeText('p', 'directed-meta', meta.join(' · '))); }
    var version = data.version && typeof data.version === 'object' ? data.version : {};
    article.appendChild(makeText('h3', '', versionLabel(version)));
    var destination = data.destination && typeof data.destination === 'object' ? data.destination : {};
    var destinationParts = [];
    if (hasValue(destination.company_name)) { destinationParts.push('Empresa: ' + textOf(destination.company_name)); }
    if (hasValue(destination.contact_name)) { destinationParts.push('Contacto: ' + textOf(destination.contact_name)); }
    if (hasValue(destination.email)) { destinationParts.push(textOf(destination.email)); }
    if (destinationParts.length) { article.appendChild(makeText('p', 'directed-meta', destinationParts.join(' · '))); }
    var body = document.createElement('div');
    body.className = 'directed-body';
    body.textContent = textOf(version.body);
    article.appendChild(body);
    if (data.superseded_by !== null && data.superseded_by !== undefined && data.superseded_by !== false && data.superseded_by !== '') {
      article.appendChild(makeText('p', 'directed-meta', 'Reemplazado por: ' + describeRef(data.superseded_by)));
    }
    return article;
  }
  function renderNote(note) {
    var data = note && typeof note === 'object' ? note : {};
    var article = document.createElement('article');
    article.className = 'directed-history-item';
    if (data.superseded_by !== null && data.superseded_by !== undefined && data.superseded_by !== false && data.superseded_by !== '') { article.className += ' directed-superseded'; }
    var meta = [];
    meta.push(noteLabel(data));
    if (hasValue(data.occurred_at)) { meta.push(dateText(data.occurred_at)); }
    article.appendChild(makeText('p', 'directed-meta', meta.join(' · ')));
    article.appendChild(makeText('div', 'directed-body', data.body));
    if (data.superseded_by !== null && data.superseded_by !== undefined && data.superseded_by !== false && data.superseded_by !== '') {
      article.appendChild(makeText('p', 'directed-meta', 'Reemplazado por: ' + describeRef(data.superseded_by)));
    }
    return article;
  }
  function renderThread(thread) {
    if (!refs.thread) { return; }
    clearNode(refs.thread);
    var data = thread && typeof thread === 'object' ? thread : {};
    var records = Array.isArray(data.records) ? data.records : [];
    var notes = Array.isArray(data.notes) ? data.notes : [];
    if (!records.length && !notes.length) {
      refs.thread.appendChild(makeText('p', 'directed-status', 'Sin historial para esta organización.'));
      return;
    }
    if (records.length) {
      refs.thread.appendChild(makeText('h3', 'directed-group-title', 'Comunicaciones registradas'));
      records.forEach(function (record) { refs.thread.appendChild(renderRecord(record)); });
    }
    if (notes.length) {
      refs.thread.appendChild(makeText('h3', 'directed-group-title', 'Notas y respuestas'));
      notes.forEach(function (note) { refs.thread.appendChild(renderNote(note)); });
    }
  }
  function updateThreadTitle() {
    if (!refs.threadTitle) { return; }
    var name = state.organization && hasValue(state.organization.name) ? textOf(state.organization.name) : '';
    refs.threadTitle.textContent = name ? 'Historial de ' + name : 'Historial de la organización';
  }
  function resetThreadView(message) {
    state.thread = null;
    threadToken += 1;
    clearNode(refs.thread);
    if (refs.threadStatus) { refs.threadStatus.textContent = textOf(message); }
    updateThreadTitle();
  }
  function invalidatePrepared() {
    state.preparedRecipients = [];
    renderPrepared();
  }
  function renderOrganizationsPlaceholder() {
    if (!refs.org) { return; }
    clearNode(refs.org);
    var option = document.createElement('option');
    option.value = '';
    option.textContent = 'Selecciona una organización';
    refs.org.appendChild(option);
    refs.org.value = '';
    refs.org.disabled = true;
  }
  function resetCampaignFor(cid) {
    state.campaignId = cid;
    chosen.clear();
    state.preparedRecipients = [];
    state.versions = [];
    state.thread = null;
    loadedCampaignId = null;
    if (cid === null) {
      state.organization = null;
      organizations = [];
      renderOrganizationsPlaceholder();
    }
    threadToken += 1;
    clearNode(refs.thread);
    if (refs.threadStatus) { refs.threadStatus.textContent = ''; }
    updateThreadTitle();
    renderPrepared();
    renderContacts();
    showLoadError('');
    showPrepareError('');
    showPrepareStatus('');
    syncControls();
  }
  function applyOrganizations(data) {
    var raw = Array.isArray(data) ? data : [];
    organizations = [];
    var selectedId = state.organization && state.organization.id !== null && state.organization.id !== undefined ? String(state.organization.id) : '';
    clearNode(refs.org);
    var placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Selecciona una organización';
    refs.org.appendChild(placeholder);
    var selected = null;
    for (var index = 0; index < raw.length; index += 1) {
      var org = raw[index];
      if (!org || typeof org !== 'object' || org.id === null || org.id === undefined) { continue; }
      organizations.push(org);
      var option = document.createElement('option');
      option.value = String(org.id);
      option.textContent = textOf(org.name);
      refs.org.appendChild(option);
      if (selectedId && String(org.id) === selectedId) { selected = org; }
    }
    refs.org.disabled = organizations.length === 0;
    if (selected) {
      state.organization = selected;
      refs.org.value = String(selected.id);
    } else {
      state.organization = null;
      refs.org.value = '';
    }
    renderContacts();
    updateThreadTitle();
    if (!selected) {
      resetThreadView(organizations.length ? 'Selecciona una organización para consultar el historial.' : 'No hay organizaciones disponibles.');
    }
  }
  function applyDirected(data, preservePrepared) {
    var directed = data && typeof data === 'object' ? data : {};
    state.versions = Array.isArray(directed.versions) ? directed.versions : [];
    if (!preservePrepared) {
      state.preparedRecipients = activeRecipients(directed);
    }
    renderPrepared();
  }
  function findOrganization(orgId) {
    var wanted = String(orgId);
    for (var index = 0; index < organizations.length; index += 1) {
      if (String(organizations[index].id) === wanted) { return organizations[index]; }
    }
    return null;
  }
  function loadThread(orgId) {
    var token = ++threadToken;
    var cid = campaignIdText(window.gwaCampaignId);
    var orgKey = String(orgId);
    if (refs.threadStatus) { refs.threadStatus.textContent = 'Cargando historial...'; }
    beginBusy();
    return callApi('/api/organizations/' + encodeURIComponent(orgKey) + '/thread', 'GET').then(function (data) {
      if (token !== threadToken || campaignIdText(window.gwaCampaignId) !== cid || !state.organization || String(state.organization.id) !== orgKey) {
        return null;
      }
      state.thread = data && typeof data === 'object' ? data : { records: [], notes: [] };
      if (data && data.organization && typeof data.organization === 'object') {
        var merged = {};
        var key;
        if (state.organization) {
          for (key in state.organization) {
            if (Object.prototype.hasOwnProperty.call(state.organization, key)) { merged[key] = state.organization[key]; }
          }
        }
        for (key in data.organization) {
          if (Object.prototype.hasOwnProperty.call(data.organization, key)) { merged[key] = data.organization[key]; }
        }
        state.organization = merged;
        if (refs.org && refs.org.options[refs.org.selectedIndex] && hasValue(state.organization.name)) {
          refs.org.options[refs.org.selectedIndex].textContent = textOf(state.organization.name);
        }
      }
      if (refs.threadStatus) { refs.threadStatus.textContent = ''; }
      updateThreadTitle();
      renderThread(state.thread);
      publish();
      return null;
    }, function () {
      if (token !== threadToken || campaignIdText(window.gwaCampaignId) !== cid || !state.organization || String(state.organization.id) !== orgKey) {
        return null;
      }
      state.thread = null;
      clearNode(refs.thread);
      if (refs.threadStatus) { refs.threadStatus.textContent = 'No se pudo cargar el historial.'; }
      publish();
      return null;
    }).then(function () { endBusy(); }, function () { endBusy(); });
  }
  function loadCampaign(cid, preservePrepared) {
    var token = ++campaignToken;
    showLoadError('');
    beginBusy();
    var organizationsRequest = callApi('/api/organizations', 'GET');
    var directedRequest = callApi('/api/campaigns/' + encodeURIComponent(cid) + '/directed', 'GET');
    return Promise.all([organizationsRequest, directedRequest]).then(function (results) {
      if (token !== campaignToken || campaignIdText(window.gwaCampaignId) !== cid || state.campaignId !== cid) {
        return null;
      }
      applyOrganizations(results[0]);
      applyDirected(results[1], preservePrepared);
      loadedCampaignId = cid;
      if (state.organization && state.organization.id !== null && state.organization.id !== undefined) {
        return loadThread(String(state.organization.id));
      }
      return null;
    }, function () {
      if (token !== campaignToken || campaignIdText(window.gwaCampaignId) !== cid || state.campaignId !== cid) {
        return null;
      }
      showLoadError('No se pudo cargar la información de la campaña.');
      return null;
    }).then(function () { endBusy(); }, function () { endBusy(); });
  }
  function refreshDirected() {
    var cid = campaignIdText(window.gwaCampaignId);
    if (state.campaignId !== cid) { resetCampaignFor(cid); }
    if (cid === null) {
      loadedCampaignId = null;
      state.campaignId = null;
      if (refs.noCampaign) { refs.noCampaign.hidden = false; refs.noCampaign.textContent = 'Selecciona una campaña en Campañas'; }
      if (refs.content) { refs.content.hidden = true; }
      if (refs.prepare) { refs.prepare.disabled = true; }
      publish();
      return;
    }
    if (refs.noCampaign) { refs.noCampaign.hidden = true; }
    if (refs.content) { refs.content.hidden = false; }
    loadCampaign(cid, loadedCampaignId === cid);
  }
  function prepareSelection() {
    var cid = campaignIdText(window.gwaCampaignId);
    if (!cid || chosen.size === 0 || busyCount > 0 || globalActionBusy()) { return; }
    if (cid !== state.campaignId) {
      resetCampaignFor(cid);
      publish();
      return;
    }
    showPrepareError('');
    showPrepareStatus('Preparando destinatarios...');
    beginBusy();
    var ids = [];
    chosen.forEach(function (value) { ids.push(value); });
    callApi('/api/campaigns/' + encodeURIComponent(cid) + '/recipients', 'POST', { contact_ids: ids }).then(function (response) {
      if (campaignIdText(window.gwaCampaignId) !== cid || state.campaignId !== cid) { return null; }
      var recipients = extractRecipients(response);
      state.preparedRecipients = recipients;
      renderPrepared();
      showPrepareStatus(recipients.length + ' destinatarios preparados');
      publish();
      return null;
    }, function () {
      if (campaignIdText(window.gwaCampaignId) !== cid || state.campaignId !== cid) { return null; }
      showPrepareError('No se pudieron preparar los destinatarios. Inténtalo de nuevo.');
      showPrepareStatus('');
      publish();
      return null;
    }).then(function () { endBusy(); }, function () { endBusy(); });
  }
  if (refs.tabGeneral) {
    refs.tabGeneral.addEventListener('click', function () {
      if (typeof window.gwaShowView === 'function') { window.gwaShowView('tracking'); }
    });
  }
  if (refs.org) {
    refs.org.addEventListener('change', function () {
      var cid = campaignIdText(window.gwaCampaignId);
      if (!cid) { return; }
      if (cid !== state.campaignId) {
        resetCampaignFor(cid);
        publish();
        return;
      }
      var orgId = refs.org.value;
      if (!orgId) {
        state.organization = null;
        resetThreadView('Selecciona una organización para consultar el historial.');
        renderContacts();
        publish();
        return;
      }
      var org = findOrganization(orgId);
      if (!org) {
        org = { id: orgId, name: '', contacts: [] };
        var selectedOption = refs.org.options[refs.org.selectedIndex];
        if (selectedOption) { org.name = selectedOption.textContent; }
      }
      state.organization = org;
      renderContacts();
      state.thread = null;
      threadToken += 1;
      clearNode(refs.thread);
      if (refs.threadStatus) { refs.threadStatus.textContent = 'Cargando historial...'; }
      updateThreadTitle();
      publish();
      loadThread(String(org.id));
    });
  }
  if (refs.prepare) { refs.prepare.addEventListener('click', prepareSelection); }
  document.addEventListener('gwa:show', function (event) {
    if (!event) { return; }
    if (event.detail === 'tracking') { root.hidden = true; return; }
    if (event.detail !== 'directed') { return; }
    root.hidden = false;
    refreshDirected();
  });
  window.gwaReloadDirected = async function () {
    if (busyCount > 0 || globalActionBusy()) { return false; }
    var cid = campaignIdText(window.gwaCampaignId);
    if (cid === null) {
      if (state.campaignId !== null) { resetCampaignFor(null); }
      loadedCampaignId = null;
      if (refs.noCampaign) { refs.noCampaign.hidden = false; refs.noCampaign.textContent = 'Selecciona una campaña en Campañas'; }
      if (refs.content) { refs.content.hidden = true; }
      publish();
      return false;
    }
    if (state.campaignId !== cid) { resetCampaignFor(cid); }
    if (refs.noCampaign) { refs.noCampaign.hidden = true; }
    if (refs.content) { refs.content.hidden = false; }
    await loadCampaign(cid, true);
    return true;
  };
  state.campaignId = campaignIdText(window.gwaCampaignId);
  publish();
})();
</script>
</div>'''