def real_start_controls() -> str:
    return '''<div id="real-start-controls">
  <p class="work-helper">El brief, las fuentes y el historial de esta campaña se enviarán a OpenRouter. Para esta prueba usa datos sintéticos, sin nombres ni correos de contactos reales.</p>
  <div class="real-start-actions">
    <button id="real-start-generate" type="button" class="work-btn">Generar con IA real</button>
    <button id="real-start-check" type="button" class="work-btn" hidden>Consultar estado</button>
  </div>
  <p id="real-start-progress" role="status" aria-live="polite" class="work-helper"></p>
  <p id="real-start-error" role="alert" class="work-helper" hidden></p>
</div>
<script>
(function () {
  'use strict';

  const controls = document.getElementById('real-start-controls');
  if (!controls) return;

  const mount = document.querySelector('#work .work-generate-block');
  if (!mount) {
    controls.hidden = true;
    return;
  }

  mount.appendChild(controls);
  const legacyGenerate = document.getElementById('work-generate');
  if (legacyGenerate) legacyGenerate.hidden = true;

  const generateButton = document.getElementById('real-start-generate');
  const checkButton = document.getElementById('real-start-check');
  const progressEl = document.getElementById('real-start-progress');
  const errorEl = document.getElementById('real-start-error');
  if (!generateButton || !checkButton || !progressEl || !errorEl) return;

  const DEFAULT_QUERY = 'GrowWithAI propósito del piloto y colaboración';
  const POLL_INTERVAL_MS = 1500;
  const MAX_POLLS = 240;
  const TERMINAL = Object.freeze({
    needs_review: true,
    waiting_input: true,
    failed: true,
    finished: true,
    cancelled: true
  });
  const STAGE_LABELS = Object.freeze({
    source_retrieval: 'Recuperando fuentes',
    source_discovery: 'Recuperando fuentes',
    sources: 'Recuperando fuentes',
    retrieval: 'Recuperando fuentes',
    generator: 'Generador en curso',
    generation: 'Generador en curso',
    drafting: 'Generador en curso',
    writer: 'Generador en curso',
    reviewer: 'Revisor en curso',
    review: 'Revisor en curso',
    evaluation: 'Revisor en curso',
    validation: 'Validando borradores',
    finalization: 'Finalizando'
  });

  let snapshot = readSnapshot();
  let ownBusy = false;
  let bridgeBusy = false;
  let pendingRunId = '';
  let pendingCampaignId = '';
  let pollTimer = null;
  let pollToken = 0;
  let terminalPinned = false;

  function isRecord(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }

  function readSnapshot() {
    const value = window.gwaWorkSnapshot;
    return isRecord(value) ? value : null;
  }

  function reviewOf(value) {
    return value && isRecord(value.review) ? value.review : null;
  }

  function campaignOf(value) {
    const review = reviewOf(value);
    return review && isRecord(review.campaign) ? review.campaign : null;
  }

  function campaignIdOf(value) {
    const campaign = campaignOf(value);
    if (!campaign) return '';
    if (typeof campaign.id === 'string') return campaign.id.trim();
    if (typeof campaign.id === 'number' && Number.isFinite(campaign.id)) return String(campaign.id);
    return '';
  }

  function snapshotHasDirty(value) {
    return !!(value && value.dirty === true);
  }

  function snapshotIsLoading(value) {
    return !!(value && value.loading === true);
  }

  function normalizedStatus(value) {
    return typeof value === 'string' ? value.trim().toLowerCase() : '';
  }

  function isPendingStatus(value) {
    const status = normalizedStatus(value);
    return status === 'prepared' || status === 'running';
  }

  function isTerminalStatus(value) {
    return TERMINAL[normalizedStatus(value)] === true;
  }

  function scalar(value) {
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed.length > 160 ? trimmed.slice(0, 157) + '...' : trimmed;
    }
    if (typeof value === 'number' && Number.isFinite(value)) return String(value);
    if (typeof value === 'boolean') return value ? 'sí' : 'no';
    return '';
  }

  function normalizeRun(value) {
    let candidate = value;
    if (isRecord(candidate) && isRecord(candidate.run)) candidate = candidate.run;
    if (isRecord(candidate) && isRecord(candidate.real_run)) candidate = candidate.real_run;
    if (!isRecord(candidate)) return null;
    let idValue = candidate.id;
    if (idValue === undefined || idValue === null) idValue = candidate.run_id;
    const id = scalar(idValue);
    const status = normalizedStatus(candidate.status);
    if (!id && !status) return null;
    return {
      id: id,
      status: status,
      metrics: isRecord(candidate.metrics) ? candidate.metrics : null
    };
  }

  function isExplicitRealRun(value) {
    const candidate = isRecord(value) && isRecord(value.run) ? value.run : value;
    if (!isRecord(candidate)) return false;
    const kind = normalizedStatus(candidate.kind);
    const mode = normalizedStatus(candidate.mode);
    const type = normalizedStatus(candidate.type);
    const runType = normalizedStatus(candidate.run_type);
    const source = normalizedStatus(candidate.source);
    const engine = normalizedStatus(candidate.engine);
    return kind === 'real' || mode === 'real' || type === 'real' ||
      runType === 'real' || source === 'real' || engine === 'real' ||
      candidate.is_real === true || candidate.real === true;
  }

  function latestRunFromValue(value) {
    if (Array.isArray(value)) {
      for (let index = value.length - 1; index >= 0; index -= 1) {
        const run = normalizeRun(value[index]);
        if (run) return run;
      }
      return null;
    }
    return normalizeRun(value);
  }

  function latestRealRun(value) {
    const review = reviewOf(value);
    if (!review) return null;
    const sources = [];
    if (isRecord(review.campaign)) sources.push(review.campaign);
    if (isRecord(review.bundle)) sources.push(review.bundle);
    sources.push(review);
    const runFieldNames = [
      'latest_real_run',
      'latestRealRun',
      'real_run',
      'realRun',
      'real_runs',
      'realRuns',
      'realrun'
    ];
    for (const source of sources) {
      for (const fieldName of runFieldNames) {
        if (Object.prototype.hasOwnProperty.call(source, fieldName)) {
          const run = latestRunFromValue(source[fieldName]);
          if (run) return run;
        }
      }
      if (Array.isArray(source.runs)) {
        for (let index = source.runs.length - 1; index >= 0; index -= 1) {
          if (isExplicitRealRun(source.runs[index])) {
            const run = normalizeRun(source.runs[index]);
            if (run) return run;
          }
        }
      }
    }
    return null;
  }

  function pendingFor(value, campaignId) {
    if (!campaignId) return null;
    if (pendingRunId && pendingCampaignId === campaignId) {
      return { id: pendingRunId, campaignId: campaignId };
    }
    const latest = latestRealRun(value);
    if (latest && latest.id && isPendingStatus(latest.status)) {
      return { id: latest.id, campaignId: campaignId };
    }
    return null;
  }

  function runFromPayload(payload) {
    if (!isRecord(payload)) return null;
    const direct = normalizeRun(payload);
    if (direct) return direct;
    if (isRecord(payload.data)) {
      const nested = normalizeRun(payload.data);
      if (nested) return nested;
    }
    return null;
  }

  function currentCampaignMatches(campaignId) {
    const value = snapshot || readSnapshot();
    return !!campaignId && campaignIdOf(value) === campaignId;
  }

  function queryFor(value) {
    const campaign = campaignOf(value);
    const topic = campaign && typeof campaign.topic === 'string' ? campaign.topic.trim() : '';
    return topic && topic.length <= 300 ? topic : DEFAULT_QUERY;
  }

  function stageLabel(stage) {
    const key = normalizedStatus(stage).split('-').join('_').split(' ').join('_');
    if (STAGE_LABELS[key]) return STAGE_LABELS[key];
    const raw = scalar(stage);
    return raw ? 'Etapa: ' + raw : 'Ejecución en curso';
  }

  function callStatusLabel(status) {
    const value = normalizedStatus(status);
    if (value === 'started' || value === 'running' || value === 'in_progress') return 'en curso';
    if (value === 'finished' || value === 'completed' || value === 'done' || value === 'succeeded') return 'completado';
    if (value === 'failed' || value === 'error') return 'fallido';
    if (value === 'cancelled' || value === 'canceled') return 'cancelado';
    if (value === 'prepared' || value === 'pending') return 'pendiente';
    return scalar(status);
  }

  function describeCall(entry) {
    if (!isRecord(entry)) return '';
    const result = isRecord(entry.result) ? entry.result : null;
    const model = result ? scalar(result.model) : '';
    const provider = result ? scalar(result.provider) : '';
    const inputTokens = scalar(entry.input_tokens);
    const outputTokens = scalar(entry.output_tokens);
    const reportedCost = scalar(entry.reported_cost);
    let text = entry.stage ? stageLabel(entry.stage) : 'Ejecución en curso';
    const callStatus = callStatusLabel(entry.status);
    if (callStatus && callStatus !== 'en curso') text += ' (' + callStatus + ')';
    if (model) text += '. Modelo: ' + model;
    if (provider) text += '. Proveedor: ' + provider;
    if (inputTokens || outputTokens) {
      text += '. Tokens: ' + (inputTokens || '0') + ' entrada / ' + (outputTokens || '0') + ' salida';
    }
    if (reportedCost) text += '. Coste informado: ' + reportedCost;
    return text + '.';
  }

  function describeRun(run, status) {
    if (normalizedStatus(status) === 'prepared') return 'Recuperando fuentes';
    const metrics = run && isRecord(run.metrics) ? run.metrics : null;
    const calls = metrics && Array.isArray(metrics.llm_calls) ? metrics.llm_calls : [];
    for (let index = calls.length - 1; index >= 0; index -= 1) {
      const line = describeCall(calls[index]);
      if (line) return line;
    }
    return 'Recuperando fuentes';
  }

  function terminalMessage(status) {
    const value = normalizedStatus(status);
    if (value === 'needs_review') return 'Borradores listos para revisión humana';
    if (value === 'waiting_input') return 'La ejecución espera información adicional. No se aprobó ni exportó nada.';
    if (value === 'failed') return 'La ejecución falló. No se aprobó ni exportó nada.';
    if (value === 'finished') return 'La ejecución terminó. No se aprobó ni exportó nada.';
    if (value === 'cancelled') return 'La ejecución se canceló. No se aprobó ni exportó nada.';
    return 'La ejecución se detuvo. No se aprobó ni exportó nada.';
  }

  function setProgress(message) {
    progressEl.textContent = message;
  }

  function clearError() {
    errorEl.textContent = '';
    errorEl.hidden = true;
  }

  function showFailure(runId) {
    const suffix = runId ? ' ID de ejecución: ' + runId : '';
    errorEl.textContent = 'No se confirmó el resultado. Consulta el estado antes de volver a generar.' + suffix;
    errorEl.hidden = false;
  }

  function acquireBusy() {
    if (typeof window.gwaSetRealWorkBusy !== 'function') return false;
    try {
      return window.gwaSetRealWorkBusy(true) === true;
    } catch (_) {
      return false;
    }
  }

  function releaseBusy() {
    if (!bridgeBusy) return;
    bridgeBusy = false;
    if (typeof window.gwaSetRealWorkBusy !== 'function') return;
    try {
      window.gwaSetRealWorkBusy(false);
    } catch (_) {}
  }

  function updateUi() {
    const value = snapshot || readSnapshot();
    const campaignId = campaignIdOf(value);
    const latest = latestRealRun(value);
    generateButton.disabled =
      ownBusy ||
      snapshotIsLoading(value) ||
      snapshotHasDirty(value) ||
      !campaignId ||
      !!(latest && isPendingStatus(latest.status));
    const pending = pendingFor(value, campaignId);
    checkButton.hidden = !pending;
    checkButton.disabled = !pending || ownBusy;
    if (!ownBusy && campaignId && !terminalPinned && latest && isPendingStatus(latest.status)) {
      progressEl.textContent = 'Ejecución pendiente; consulta su estado';
    }
  }

  async function handleGenerate() {
    if (ownBusy) return;
    const value = snapshot || readSnapshot();
    const campaignId = campaignIdOf(value);
    const latest = latestRealRun(value);
    if (!campaignId || snapshotHasDirty(value) || snapshotIsLoading(value) || (latest && isPendingStatus(latest.status))) {
      updateUi();
      return;
    }
    ownBusy = true;
    terminalPinned = false;
    clearError();
    setProgress('Recuperando fuentes');
    updateUi();
    if (!acquireBusy()) {
      ownBusy = false;
      setProgress('');
      updateUi();
      return;
    }
    bridgeBusy = true;
    let runId = pendingRunId && pendingCampaignId === campaignId ? pendingRunId : '';
    if (!runId) {
      try {
        runId = window.crypto.randomUUID();
      } catch (_) {
        releaseBusy();
        ownBusy = false;
        setProgress('');
        updateUi();
        return;
      }
      pendingRunId = runId;
      pendingCampaignId = campaignId;
    }
    const body = {
      run_id: runId,
      query: queryFor(value),
      confirmed_data: true
    };
    try {
      if (typeof window.gwaApi !== 'function') throw new Error('unavailable');
      await window.gwaApi('/api/campaigns/' + encodeURIComponent(campaignId) + '/real', 'POST', body);
    } catch (_) {
      if (!currentCampaignMatches(campaignId)) {
        releaseBusy();
        ownBusy = false;
        setProgress('');
        updateUi();
        return;
      }
      showFailure(runId);
      releaseBusy();
      ownBusy = false;
      updateUi();
      return;
    }
    if (!currentCampaignMatches(campaignId)) {
      releaseBusy();
      ownBusy = false;
      setProgress('');
      updateUi();
      return;
    }
    startPolling(runId, campaignId);
  }

  function handleCheck() {
    if (ownBusy) return;
    const value = snapshot || readSnapshot();
    const campaignId = campaignIdOf(value);
    if (!campaignId) return;
    const pending = pendingFor(value, campaignId);
    if (!pending) {
      updateUi();
      return;
    }
    pendingRunId = pending.id;
    pendingCampaignId = campaignId;
    ownBusy = true;
    terminalPinned = false;
    clearError();
    setProgress('Consultando estado');
    updateUi();
    startPolling(pending.id, campaignId);
  }

  function handleReview(event) {
    const detail = event ? event.detail : null;
    snapshot = isRecord(detail) ? detail : readSnapshot();
    updateUi();
  }

  function startPolling(runId, campaignId) {
    pollToken += 1;
    const token = pollToken;
    let iterations = 0;
    if (pollTimer !== null) {
      window.clearTimeout(pollTimer);
      pollTimer = null;
    }

    function failPolling() {
      showFailure(runId);
      releaseBusy();
      ownBusy = false;
      updateUi();
    }

    function abortForCampaign() {
      releaseBusy();
      ownBusy = false;
      setProgress('');
      updateUi();
    }

    async function tick() {
      if (token !== pollToken) return;
      if (iterations >= MAX_POLLS) {
        terminalPinned = false;
        failPolling();
        return;
      }
      iterations += 1;
      if (!currentCampaignMatches(campaignId)) {
        abortForCampaign();
        return;
      }
      let payload;
      try {
        if (typeof window.gwaApi !== 'function') throw new Error('unavailable');
        payload = await window.gwaApi('/api/runs/' + encodeURIComponent(runId) + '/real', 'GET');
      } catch (_) {
        if (token !== pollToken) return;
        if (!currentCampaignMatches(campaignId)) {
          abortForCampaign();
          return;
        }
        terminalPinned = false;
        failPolling();
        return;
      }
      if (token !== pollToken) return;
      if (!currentCampaignMatches(campaignId)) {
        abortForCampaign();
        return;
      }
      const run = runFromPayload(payload);
      const status = run ? run.status : '';
      if (isTerminalStatus(status)) {
        terminalPinned = true;
        setProgress(terminalMessage(status));
        await finishTerminal(runId, campaignId);
        return;
      }
      setProgress(describeRun(run, status));
      if (iterations >= MAX_POLLS) {
        terminalPinned = false;
        failPolling();
        return;
      }
      pollTimer = window.setTimeout(function () {
        pollTimer = null;
        if (token === pollToken) tick();
      }, POLL_INTERVAL_MS);
    }

    tick().catch(function () {
      if (token !== pollToken) return;
      terminalPinned = false;
      failPolling();
    });
  }

  async function finishTerminal(runId, campaignId) {
    if (!currentCampaignMatches(campaignId)) {
      releaseBusy();
      ownBusy = false;
      setProgress('');
      updateUi();
      return;
    }
    releaseBusy();
    let loaded = false;
    if (currentCampaignMatches(campaignId) && typeof window.gwaLoadWorkRun === 'function') {
      try {
        loaded = (await window.gwaLoadWorkRun(runId)) === true;
      } catch (_) {
        loaded = false;
      }
    }
    if (!currentCampaignMatches(campaignId)) {
      ownBusy = false;
      setProgress('');
      updateUi();
      return;
    }
    if (loaded) {
      pendingRunId = '';
      pendingCampaignId = '';
      clearError();
    } else {
      showFailure(runId);
    }
    ownBusy = false;
    updateUi();
  }

  snapshot = readSnapshot();
  updateUi();

  generateButton.addEventListener('click', async function () {
    try {
      await handleGenerate();
    } catch (_) {
      showFailure(pendingRunId);
      releaseBusy();
      ownBusy = false;
      updateUi();
    }
  });

  checkButton.addEventListener('click', function () {
    try {
      handleCheck();
    } catch (_) {
      showFailure(pendingRunId);
      releaseBusy();
      ownBusy = false;
      updateUi();
    }
  });

  document.addEventListener('gwa:review', handleReview);
})();
</script>'''
