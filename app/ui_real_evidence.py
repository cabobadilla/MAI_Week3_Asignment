'''Read-only public evidence for real agent runs.'''

def real_evidence_controls() -> str:
    return _CONTROLS


_CONTROLS = r'''<section id='real-agent-evidence' class='work-card' hidden aria-live='polite'>
  <p class='work-kicker'>Solo lectura · evidencia pública</p>
  <h2 class='work-title'>Evidencia del agente real</h2>
  <div id='real-agent-evidence-content' class='work-list'></div>
</section>
<script>
(function () {
  'use strict';
  var root = document.getElementById('real-agent-evidence');
  if (!root || root.getAttribute('data-real-evidence-bound') === '1') { return; }
  root.setAttribute('data-real-evidence-bound', '1');
  var target = document.getElementById('real-agent-evidence-content');
  if (!target) { return; }
  var chipOriginals = new WeakMap();
  var hasRendered = false;
  var COST_UNKNOWN = 'Coste no reportado completo';

  function make(tag, cls, txt) {
    var node = document.createElement(tag);
    if (cls) { node.className = cls; }
    if (txt !== undefined && txt !== null) { node.textContent = String(txt); }
    return node;
  }

  function allowWrap(node) {
    if (!node || !node.style) { return node; }
    node.style.overflowWrap = 'anywhere';
    node.style.wordBreak = 'break-word';
    return node;
  }

  function textValue(value) {
    if (typeof value === 'string') { return value.length ? value : '—'; }
    if (typeof value === 'number' && isFinite(value)) { return String(value); }
    if (typeof value === 'boolean') { return value ? 'sí' : 'no'; }
    return '—';
  }

  function yesNo(value) {
    if (value === true) { return 'sí'; }
    if (value === false) { return 'no'; }
    return textValue(value);
  }

  function arrayValue(value) { return Array.isArray(value) ? value : []; }

  function objectValue(value) {
    return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
  }

  function makeCode(value, cls) {
    return allowWrap(make('code', cls || 'work-break', textValue(value)));
  }

  function field(parent, label, value, asCode) {
    var row = make('div', 'work-item');
    row.appendChild(make('span', 'work-label', label + ': '));
    if (asCode) {
      row.appendChild(makeCode(value));
    } else {
      row.appendChild(allowWrap(make('span', 'work-break', textValue(value))));
    }
    parent.appendChild(row);
    return row;
  }

  function note(parent, text) {
    return parent.appendChild(allowWrap(make('p', 'work-break', text)));
  }

  function makeCard(title, kicker) {
    var card = make('article', 'work-card');
    if (kicker) { card.appendChild(make('p', 'work-kicker', kicker)); }
    card.appendChild(make('h3', 'work-title', title));
    var list = make('div', 'work-list');
    card.appendChild(list);
    return { card: card, list: list };
  }

  function place() {
    var host = document.querySelector('#work .work-evidence');
    if (!host) { return; }
    var ref = host.querySelector('.work-integration, #work-integration, [data-work-integration]');
    while (ref && ref.parentElement && ref.parentElement !== host) { ref = ref.parentElement; }
    if (ref === root) { ref = null; }
    if (root.parentElement === host && (!ref || root.nextElementSibling === ref)) { return; }
    host.insertBefore(root, ref || null);
  }

  function replaceText(element, from, to) {
    if (!element) { return; }
    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    var node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue && node.nodeValue.indexOf(from) !== -1) {
        node.nodeValue = node.nodeValue.split(from).join(to);
      }
    }
  }

  function replacePrefix(element, from, to) {
    if (!element) { return; }
    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    var node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue && node.nodeValue.indexOf(from) === 0) {
        node.nodeValue = to + node.nodeValue.slice(from.length);
        return;
      }
    }
    var whole = element.textContent || '';
    if (whole.indexOf(from) === 0) { element.textContent = to + whole.slice(from.length); }
  }

  function neutralizeStaticCopy() {
    var nodes = document.querySelectorAll('#work h1, #work h2, #work h3, #work h4, #work h5, #work h6, #work .work-title, #work .work-kicker, #work .kicker');
    var i;
    for (i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      if (node.closest && node.closest('#real-agent-evidence')) { continue; }
      var label = (node.textContent || '').trim();
      if (label === 'Fuentes sintéticas') { node.textContent = 'Fuentes'; }
      else if (label === 'Piezas demo') { node.textContent = 'Piezas para revisar'; }
    }
    var approvalLabel = document.querySelector('label[for=gwa-approval-confirm]');
    if (approvalLabel) { replaceText(approvalLabel, 'de demostración', 'mostradas'); }
    var status = document.querySelector('#gwa-approval-status');
    if (status) { replacePrefix(status, 'DEMO:', 'IA real:'); }
  }

  function syncExistingSources(real, sources) {
    var chips = document.querySelectorAll('#work-sources .work-chip');
    var i;
    if (!real) {
      for (i = 0; i < chips.length; i++) {
        var chip = chips[i];
        var item = chip.closest ? chip.closest('.work-item, li, .work-source') : null;
        item = item || chip.parentElement || chip;
        var oldCodes = item.querySelectorAll('.real-chunk-id');
        var j;
        for (j = 0; j < oldCodes.length; j++) { oldCodes[j].remove(); }
        var original = chipOriginals.get(chip);
        if (original !== undefined) {
          chip.textContent = original;
          chipOriginals.delete(chip);
        }
      }
      return;
    }
    for (i = 0; i < sources.length && i < chips.length; i++) {
      var src = objectValue(sources[i]) || {};
      var current = chips[i];
      var holder = current.closest ? current.closest('.work-item, li, .work-source') : null;
      holder = holder || current.parentElement || current;
      if (!chipOriginals.has(current)) { chipOriginals.set(current, current.textContent || ''); }
      var name = (typeof src.source_name === 'string' && src.source_name) ? src.source_name : textValue(src.source_id);
      var version = (typeof src.content_version === 'string' && src.content_version) ? src.content_version : '0.2';
      current.textContent = name + ' · v' + version;
      var code = holder.querySelector('.real-chunk-id');
      if (!code) {
        code = make('code', 'real-chunk-id work-break', '');
        current.appendChild(code);
      }
      allowWrap(code);
      code.textContent = textValue(src.chunk_id);
    }
  }

  function bundleFrom(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') { return null; }
    var review = snapshot.review;
    if (!review || typeof review !== 'object') { return null; }
    var bundle = review.bundle;
    if (!bundle || typeof bundle !== 'object' || Array.isArray(bundle)) { return null; }
    return bundle;
  }

  function snapshotFrom(detail) {
    if (!detail || typeof detail !== 'object') { return null; }
    if (detail.snapshot && typeof detail.snapshot === 'object') { return detail.snapshot; }
    return detail;
  }

  function renderRun(bundle, run, agent) {
    var card = makeCard('Estado de la ejecución', 'Evidencia pública · solo lectura');
    field(card.list, 'Run', run.id, true);
    field(card.list, 'Estado del run', run.status, true);
    field(card.list, 'Generación', bundle.generation, true);
    field(card.list, 'Modo', bundle.mode, true);
    field(card.list, 'Estado del agente', agent ? agent.status : 'Sin resultado', true);
    field(card.list, 'Hash del agente', bundle.agent_hash, true);
    target.appendChild(card.card);
  }

  function renderStages(agent) {
    var events = arrayValue(agent.events);
    var card = makeCard('Etapas y eventos', 'Eventos reportados: ' + events.length);
    if (!events.length) {
      note(card.list, 'Sin etapas/eventos reportados.');
    } else {
      for (var i = 0; i < events.length; i++) {
        var event = events[i];
        var text;
        if (typeof event === 'string') {
          text = event;
        } else {
          var obj = objectValue(event) || {};
          text = 'Etapa: ' + textValue(obj.stage) + ' · Estado: ' + textValue(obj.status);
        }
        card.list.appendChild(allowWrap(make('div', 'work-item work-break', text)));
      }
    }
    target.appendChild(card.card);
  }

  function renderSources(run, sources) {
    var card = makeCard('Fuentes y procedencia', 'Metadatos públicos · ' + sources.length + ' fuente(s)');
    if (!sources.length) {
      note(card.list, 'Sin fuentes reportadas.');
    } else {
      for (var i = 0; i < sources.length; i++) {
        var src = objectValue(sources[i]) || {};
        var item = make('div', 'work-item');
        var name = (typeof src.source_name === 'string' && src.source_name) ? src.source_name : textValue(src.source_id);
        item.appendChild(allowWrap(make('strong', 'work-break', name)));
        field(item, 'ID de fuente', src.source_id, true);
        field(item, 'Chunk', src.chunk_id, true);
        field(item, 'Versión de contenido', src.content_version);
        if (src.line_start == null && src.line_end == null) {
          field(item, 'Líneas', '—');
        } else {
          field(item, 'Líneas', textValue(src.line_start) + '–' + textValue(src.line_end));
        }
        field(item, 'Hash de fuente', src.source_hash, true);
        field(item, 'Hash de texto', src.text_hash, true);
        field(item, 'Instrucciones de confianza', yesNo(src.trusted_instructions));
        card.list.appendChild(item);
      }
    }
    target.appendChild(card.card);
  }

  function isDecimalString(value) {
    if (typeof value !== 'string') { return false; }
    return /^[0-9]+([.][0-9]+)?$/.test(value.trim());
  }

  function isTokenNumber(value) {
    return typeof value === 'number' && isFinite(value) && value >= 0 && Math.floor(value) === value;
  }

  function sumDecimals(values) {
    var scale = 0;
    var parts = [];
    var i;
    for (i = 0; i < values.length; i++) {
      var raw = values[i].trim();
      var dot = raw.indexOf('.');
      var intPart = dot < 0 ? raw : raw.slice(0, dot);
      var fracPart = dot < 0 ? '' : raw.slice(dot + 1);
      if (fracPart.length > scale) { scale = fracPart.length; }
      parts.push([intPart, fracPart]);
    }
    var factor = BigInt(1);
    for (i = 0; i < scale; i++) { factor = factor * BigInt(10); }
    var total = BigInt(0);
    for (i = 0; i < parts.length; i++) {
      var whole = parts[i][0];
      var fraction = parts[i][1];
      while (fraction.length < scale) { fraction += '0'; }
      total += BigInt(whole) * factor + BigInt(fraction || '0');
    }
    var out = total.toString();
    if (scale > 0) {
      out = out.padStart(scale + 1, '0');
      out = out.slice(0, out.length - scale) + '.' + out.slice(out.length - scale);
      out = out.replace(/0+$/, '');
      if (out.charAt(out.length - 1) === '.') { out = out.slice(0, -1); }
    }
    return out || '0';
  }

  function callsFromRun(run) {
    var metrics = objectValue(run.metrics);
    var calls = metrics ? objectValue(metrics.llm_calls) : null;
    if (!calls) { return []; }
    var ids = Object.keys(calls);
    var out = [];
    var i;
    for (i = 0; i < ids.length; i++) {
      var call = objectValue(calls[ids[i]]) || {};
      var result = objectValue(call.result) || {};
      out.push({
        id: ids[i],
        stage: call.stage,
        status: call.status,
        model: result.model,
        provider: result.provider,
        inputTokens: result.input_tokens,
        outputTokens: result.output_tokens,
        reportedCost: result.reported_cost,
        responseId: result.response_id
      });
    }
    return out;
  }

  function reportedCost(value) {
    if (typeof value === 'string' && value.trim().length) { return value; }
    return 'No reportado';
  }

  function renderUsage(run) {
    var entries = callsFromRun(run);
    var card = makeCard('Llamadas, tokens y coste', 'Metadatos de llamadas · sin contenido de respuesta');
    var list = card.list;
    var totalIn = null;
    var totalOut = null;
    var completed = 0;
    var allCostKnown = true;
    var costs = [];
    var providers = new Map();
    var i;
    for (i = 0; i < entries.length; i++) {
      var info = entries[i];
      if (isTokenNumber(info.inputTokens)) { totalIn = (totalIn === null ? 0 : totalIn) + info.inputTokens; }
      if (isTokenNumber(info.outputTokens)) { totalOut = (totalOut === null ? 0 : totalOut) + info.outputTokens; }
      if (info.status === 'completed') {
        completed += 1;
        if (isDecimalString(info.reportedCost)) { costs.push(info.reportedCost.trim()); }
        else { allCostKnown = false; }
        var provider = (typeof info.provider === 'string' && info.provider) ? info.provider : 'Proveedor no indicado';
        if (!providers.has(provider)) { providers.set(provider, { costs: [], allKnown: true }); }
        var group = providers.get(provider);
        if (isDecimalString(info.reportedCost)) { group.costs.push(info.reportedCost.trim()); }
        else { group.allKnown = false; }
      }
    }
    var totalCost = (completed > 0 && allCostKnown) ? sumDecimals(costs) : COST_UNKNOWN;
    field(list, 'Coste informado total', totalCost, true);
    field(list, 'Tokens de entrada informados', totalIn === null ? '—' : String(totalIn));
    field(list, 'Tokens de salida informados', totalOut === null ? '—' : String(totalOut));
    field(list, 'Llamadas completadas', String(completed));
    if (providers.size) {
      var providerBox = make('div', 'work-item');
      providerBox.appendChild(make('p', 'work-label', 'Coste informado por proveedor'));
      providers.forEach(function (group, provider) {
        var providerCost = group.allKnown ? sumDecimals(group.costs) : COST_UNKNOWN;
        field(providerBox, provider, providerCost, true);
      });
      list.appendChild(providerBox);
    }
    if (completed > 0 && allCostKnown) {
      note(list, 'Suma de importes informados en llamadas completadas.');
    } else if (completed > 0) {
      note(list, 'Solo se muestran importes informados; los costes ausentes no se interpretan como cero.');
    } else {
      note(list, 'No hay llamadas completadas con coste informado.');
    }
    note(list, 'Los tokens se suman solo cuando están informados; no se estiman valores ausentes.');
    if (!entries.length) {
      note(list, 'Sin llamadas registradas.');
    } else {
      var callsBox = make('div', 'work-item');
      callsBox.appendChild(make('p', 'work-label', 'Llamadas registradas (' + entries.length + ')'));
      for (i = 0; i < entries.length; i++) {
        var entry = entries[i];
        var item = make('div', 'work-item');
        var request = make('p', 'work-break');
        request.appendChild(make('span', 'work-label', 'Solicitud: '));
        request.appendChild(makeCode(entry.id));
        item.appendChild(request);
        field(item, 'Etapa', entry.stage);
        field(item, 'Estado', entry.status);
        field(item, 'Modelo', entry.model);
        field(item, 'Proveedor', entry.provider);
        field(item, 'Tokens de entrada', isTokenNumber(entry.inputTokens) ? String(entry.inputTokens) : '—');
        field(item, 'Tokens de salida', isTokenNumber(entry.outputTokens) ? String(entry.outputTokens) : '—');
        field(item, 'Coste informado', reportedCost(entry.reportedCost));
        field(item, 'ID de respuesta', entry.responseId, true);
        callsBox.appendChild(item);
      }
      list.appendChild(callsBox);
    }
    target.appendChild(card.card);
  }

  function renderPieces(parent, pieces) {
    if (!pieces.length) {
      note(parent, 'Sin piezas en este ciclo.');
      return;
    }
    var shown = pieces.slice(0, 6);
    if (pieces.length > 6) { note(parent, 'Mostrando 6 de ' + pieces.length + ' piezas.'); }
    for (var i = 0; i < shown.length; i++) {
      var piece = objectValue(shown[i]) || {};
      var item = make('div', 'work-item');
      field(item, 'Formato', piece.format);
      field(item, 'Variante', piece.variant);
      var bodyText = typeof piece.body === 'string' ? piece.body : '—';
      if (!bodyText.length) { bodyText = 'Sin contenido.'; }
      item.appendChild(allowWrap(make('div', 'work-break', bodyText)));
      var citations = arrayValue(piece.citations);
      var parts = [];
      for (var j = 0; j < citations.length; j++) { parts.push(textValue(citations[j])); }
      item.appendChild(allowWrap(make('p', 'work-break', 'Citas: ' + (parts.length ? parts.join(', ') : '—'))));
      parent.appendChild(item);
    }
  }

  function renderDraft(agent) {
    var card = makeCard('Borrador generado · pendiente de revisión humana', 'Contenido generado · solo lectura');
    note(card.list, 'La revisión automática corresponde al borrador generado; las ediciones posteriores requieren revisión humana.');
    var draft = objectValue(agent.draft);
    var history = arrayValue(agent.draft_history);
    if (draft) { field(card.list, 'Estado del borrador', draft.status); }
    if (history.length) {
      var shown = history.slice(-3);
      if (history.length > 3) { note(card.list, 'Mostrando los 3 ciclos más recientes de ' + history.length + '.'); }
      for (var i = 0; i < shown.length; i++) {
        var entry = objectValue(shown[i]) || {};
        var pieces = arrayValue(entry.pieces);
        var details = make('details', 'work-item real-draft-cycle');
        details.open = i === shown.length - 1;
        details.appendChild(make('summary', 'work-break', 'Ciclo ' + textValue(entry.cycle) + ' · ' + pieces.length + ' pieza' + (pieces.length === 1 ? '' : 's')));
        var body = make('div', 'work-list');
        if (entry.hash !== undefined) { field(body, 'Hash del ciclo', entry.hash, true); }
        renderPieces(body, pieces);
        details.appendChild(body);
        card.list.appendChild(details);
      }
    } else if (draft) {
      var currentPieces = arrayValue(draft.pieces);
      var currentDetails = make('details', 'work-item real-draft-cycle');
      currentDetails.open = true;
      currentDetails.appendChild(make('summary', 'work-break', 'Borrador actual · ' + currentPieces.length + ' pieza' + (currentPieces.length === 1 ? '' : 's')));
      var currentBody = make('div', 'work-list');
      renderPieces(currentBody, currentPieces);
      currentDetails.appendChild(currentBody);
      card.list.appendChild(currentDetails);
    } else {
      note(card.list, 'Sin borrador generado.');
    }
    target.appendChild(card.card);
  }

  function renderIssues(parent, rawIssues) {
    var issues = arrayValue(rawIssues);
    var box = make('div', 'work-item');
    box.appendChild(make('p', 'work-label', 'Hallazgos (' + issues.length + ')'));
    if (!issues.length) {
      note(box, 'Sin hallazgos.');
    } else {
      var shown = issues.slice(0, 12);
      for (var i = 0; i < shown.length; i++) {
        var issue = objectValue(shown[i]) || {};
        var item = make('div', 'work-item');
        field(item, 'Pieza', issue.piece_key, true);
        field(item, 'Categoría', issue.category);
        var message = (typeof issue.message === 'string' && issue.message.length) ? issue.message : '—';
        item.appendChild(allowWrap(make('p', 'work-break', message)));
        var citations = arrayValue(issue.citations);
        var parts = [];
        for (var j = 0; j < citations.length; j++) { parts.push(textValue(citations[j])); }
        item.appendChild(allowWrap(make('p', 'work-break', 'Citas: ' + (parts.length ? parts.join(', ') : '—'))));
        box.appendChild(item);
      }
      if (issues.length > shown.length) { note(box, 'Mostrando 12 de ' + issues.length + ' hallazgos.'); }
    }
    parent.appendChild(box);
  }

  function renderQuestions(parent, rawQuestions, title) {
    var questions = arrayValue(rawQuestions);
    var box = make('div', 'work-item');
    box.appendChild(make('p', 'work-label', title + ' (' + questions.length + ')'));
    if (!questions.length) {
      note(box, 'Sin preguntas.');
    } else {
      for (var i = 0; i < questions.length; i++) {
        var value = typeof questions[i] === 'string' ? questions[i] : textValue(questions[i]);
        if (!value.length) { value = '—'; }
        box.appendChild(allowWrap(make('p', 'work-break', value)));
      }
    }
    parent.appendChild(box);
    return questions;
  }

  function renderReview(agent) {
    var card = makeCard('Revisión automática', 'Hallazgos del revisor · no aprueba automáticamente');
    var history = arrayValue(agent.review_history);
    var current = objectValue(agent.review);
    var displayedQuestions = [];
    var hasReview = false;
    var i;
    if (history.length) {
      var shown = history.slice(-3);
      if (history.length > 3) { note(card.list, 'Mostrando las 3 revisiones más recientes de ' + history.length + '.'); }
      for (i = 0; i < shown.length; i++) {
        var entry = objectValue(shown[i]) || {};
        var review = objectValue(entry.review);
        var details = make('details', 'work-item real-review-cycle');
        details.open = i === shown.length - 1;
        details.appendChild(make('summary', 'work-break', 'Ciclo ' + textValue(entry.cycle) + ' · Veredicto: ' + textValue(review ? review.verdict : null)));
        var body = make('div', 'work-list');
        if (!review) {
          note(body, 'Sin datos de revisión.');
        } else {
          field(body, 'Veredicto', review.verdict, true);
          if (entry.hash !== undefined) { field(body, 'Hash del ciclo', entry.hash, true); }
          renderIssues(body, review.issues);
          renderQuestions(body, review.questions, 'Preguntas del revisor');
          var reviewQuestions = arrayValue(review.questions);
          for (var q = 0; q < reviewQuestions.length; q++) {
            if (typeof reviewQuestions[q] === 'string' && displayedQuestions.indexOf(reviewQuestions[q]) === -1) {
              displayedQuestions.push(reviewQuestions[q]);
            }
          }
        }
        details.appendChild(body);
        card.list.appendChild(details);
        hasReview = true;
      }
    } else if (current) {
      var currentDetails = make('details', 'work-item real-review-cycle');
      currentDetails.open = true;
      currentDetails.appendChild(make('summary', 'work-break', 'Revisión actual · Veredicto: ' + textValue(current.verdict)));
      var currentBody = make('div', 'work-list');
      field(currentBody, 'Veredicto', current.verdict, true);
      renderIssues(currentBody, current.issues);
      renderQuestions(currentBody, current.questions, 'Preguntas del revisor');
      var currentQuestions = arrayValue(current.questions);
      for (i = 0; i < currentQuestions.length; i++) {
        if (typeof currentQuestions[i] === 'string' && displayedQuestions.indexOf(currentQuestions[i]) === -1) {
          displayedQuestions.push(currentQuestions[i]);
        }
      }
      currentDetails.appendChild(currentBody);
      card.list.appendChild(currentDetails);
      hasReview = true;
    }
    if (!hasReview) { note(card.list, 'Sin revisión automática registrada.'); }
    var topQuestions = arrayValue(agent.questions);
    var extras = [];
    for (i = 0; i < topQuestions.length; i++) {
      var topValue = typeof topQuestions[i] === 'string' ? topQuestions[i] : textValue(topQuestions[i]);
      if (displayedQuestions.indexOf(topValue) === -1) {
        extras.push(topQuestions[i]);
        displayedQuestions.push(topValue);
      }
    }
    if (extras.length) { renderQuestions(card.list, extras, 'Preguntas registradas'); }
    target.appendChild(card.card);
  }

  function renderError(agent) {
    var error = objectValue(agent.error);
    if (!error && agent.status !== 'failed') { return; }
    var card = makeCard('Error de la ejecución', 'Requiere revisión humana');
    if (error) {
      field(card.list, 'Código', error.code, true);
      field(card.list, 'Reintentable', yesNo(error.retryable));
      field(card.list, 'Resultado desconocido', yesNo(error.outcome_unknown));
      if (error.code === 'revision_limit') {
        note(card.list, 'Detenido: se alcanzó el límite de revisiones; requiere revisión humana. No hay aprobación automática.');
      } else {
        note(card.list, 'La ejecución falló; requiere revisión humana. No hay aprobación automática.');
      }
    } else {
      note(card.list, 'El agente terminó con estado fallido; requiere revisión humana. No hay aprobación automática.');
    }
    target.appendChild(card.card);
  }

  function render(snapshot) {
    hasRendered = true;
    place();
    target.replaceChildren();
    var bundle = bundleFrom(snapshot);
    if (!bundle || bundle.mode !== 'real') {
      root.hidden = true;
      syncExistingSources(false, []);
      return;
    }
    root.hidden = false;
    neutralizeStaticCopy();
    var run = objectValue(bundle.run) || {};
    var agent = objectValue(bundle.agent);
    var sources = arrayValue(run.sources);
    syncExistingSources(true, sources);
    renderRun(bundle, run, agent);
    if (agent) { renderStages(agent); }
    renderSources(run, sources);
    if (agent) {
      renderDraft(agent);
      renderReview(agent);
      renderError(agent);
    } else {
      var pending = makeCard('Resultado del agente', 'Sin resultado todavía');
      note(pending.list, 'El agente aún no ha producido un resultado. Se muestran el estado del run y los metadatos de las llamadas; la lista de fuentes existente puede permanecer visible.');
      target.appendChild(pending.card);
    }
    renderUsage(run);
  }

  document.addEventListener('gwa:review', function (event) {
    render(snapshotFrom(event && event.detail));
  });

  function boot() {
    place();
    if (!hasRendered) { render(window.gwaWorkSnapshot); }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  }
  boot();
})();
</script>'''