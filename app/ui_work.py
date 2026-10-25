'''GWA work capability workspace fragment.'''

WORKSPACE_HTML = r'''<section id='work' class='work-view' hidden aria-labelledby='work-title'>
  <style>
    #work {
      --work-paper: #fffef9;
      --work-bg: #f3f4ed;
      --work-ink: #173a35;
      --work-green: #215b48;
      --work-line: #dce3d5;
      color: var(--work-ink);
      background: var(--work-bg);
      font-family: inherit;
      padding: 16px;
      overflow-wrap: anywhere;
    }
    #work[hidden], #work [hidden] { display: none !important; }
    #work *, #work *::before, #work *::after { box-sizing: border-box; }
    #work .work-shell { width: 100%; max-width: 1240px; margin: 0 auto; }
    #work .work-topbar { display: flex; justify-content: flex-start; margin-bottom: 12px; }
    #work .work-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 16px; }
    #work .work-titleblock { flex: 1 1 420px; min-width: 0; }
    #work .work-kicker { margin: 0 0 4px; color: var(--work-green); font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    #work h1, #work h2, #work p { margin-top: 0; }
    #work h1 { margin-bottom: 8px; font-size: clamp(1.65rem, 3vw, 2.4rem); line-height: 1.08; letter-spacing: -.02em; }
    #work h2 { margin-bottom: 8px; font-size: 1rem; line-height: 1.2; }
    #work .work-topic { margin-bottom: 10px; font-size: .92rem; opacity: .82; }
    #work .work-brief { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 18px; margin: 0; max-width: 760px; }
    #work dt { color: var(--work-green); font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    #work dd { margin: 2px 0 0; min-width: 0; line-height: 1.45; overflow-wrap: anywhere; }
    #work .work-generate-block { flex: 0 1 320px; min-width: 0; }
    #work .work-statusline { min-height: 24px; margin-bottom: 6px; }
    #work .work-status { display: inline-flex; align-items: center; min-height: 26px; padding: 3px 10px; border: 1px solid var(--work-line); border-radius: 999px; background: var(--work-paper); font-size: 12px; font-weight: 700; }
    #work .work-btn { display: inline-flex; align-items: center; justify-content: center; min-width: 44px; min-height: 44px; padding: 10px 16px; border: 1px solid var(--work-line); border-radius: 12px; background: var(--work-paper); color: var(--work-ink); font: inherit; font-weight: 700; line-height: 1.2; text-align: center; cursor: pointer; touch-action: manipulation; }
    #work .work-btn:hover:not(:disabled) { border-color: var(--work-green); }
    #work .work-btn:disabled { opacity: .48; cursor: not-allowed; }
    #work .work-btn-primary { border-color: var(--work-green); background: var(--work-green); color: var(--work-paper); }
    #work .work-btn-ghost { background: transparent; }
    #work .work-btn:focus-visible, #work .work-tab:focus-visible, #work .work-variant:focus-visible, #work .work-textarea:focus-visible { outline: 3px solid var(--work-green); outline-offset: 2px; }
    #work .work-helper { margin: 8px 0 0; font-size: 12px; line-height: 1.4; opacity: .78; }
    #work .work-alert { margin: 0 0 14px; padding: 12px 14px; border: 1px solid var(--work-green); border-radius: 12px; background: var(--work-paper); font-size: 14px; font-weight: 700; line-height: 1.45; }
    #work .work-loading { margin: 0; padding: 18px; border: 1px solid var(--work-line); border-radius: 16px; background: var(--work-paper); }
    #work .work-grid { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }
    #work .work-editor { min-width: 0; padding: 16px; border: 1px solid var(--work-line); border-radius: 16px; background: var(--work-paper); }
    #work .work-editor-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
    #work .work-dirty { display: inline-flex; align-items: center; min-height: 28px; padding: 3px 10px; border: 1px solid var(--work-line); border-radius: 999px; background: var(--work-bg); color: var(--work-ink); font-size: 12px; font-weight: 700; }
    #work .work-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 14px; padding: 0 0 12px; border-bottom: 1px solid var(--work-line); }
    #work .work-tab { min-width: 44px; min-height: 44px; padding: 8px 14px; border: 1px solid var(--work-line); border-radius: 999px; background: transparent; color: var(--work-ink); font: inherit; font-size: .9rem; font-weight: 700; cursor: pointer; }
    #work .work-tab[aria-selected='true'] { border-color: var(--work-green); background: var(--work-green); color: var(--work-paper); }
    #work .work-variantrow { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 14px; }
    #work .work-label { display: block; margin-bottom: 6px; color: var(--work-green); font-size: 11px; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }
    #work .work-variantrow .work-label { margin: 0 4px 0 0; }
    #work .work-variants { display: flex; flex-wrap: wrap; gap: 6px; }
    #work .work-variant { min-width: 44px; min-height: 44px; padding: 8px 12px; border: 1px solid var(--work-line); border-radius: 12px; background: transparent; color: var(--work-ink); font: inherit; font-weight: 700; cursor: pointer; }
    #work .work-variant[aria-pressed='true'] { border-color: var(--work-green); background: var(--work-green); color: var(--work-paper); }
    #work .work-muted { margin: 0; font-size: 13px; opacity: .68; }
    #work .work-piece { padding-top: 14px; border-top: 1px solid var(--work-line); }
    #work .work-piece-empty { margin-bottom: 12px; font-size: 14px; opacity: .72; }
    #work .work-piece-meta { margin-bottom: 12px; padding: 12px; border: 1px solid var(--work-line); border-radius: 12px; background: var(--work-bg); }
    #work .work-piece-meta p { margin: 0 0 4px; font-size: 12px; line-height: 1.4; }
    #work .work-piece-meta p:last-child { margin-bottom: 0; }
    #work code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; word-break: break-word; white-space: normal; }
    #work .work-textarea { display: block; width: 100%; min-height: 420px; resize: vertical; padding: 14px; border: 1px solid var(--work-line); border-radius: 12px; background: var(--work-paper); color: var(--work-ink); font: inherit; font-size: 1rem; line-height: 1.65; }
    #work .work-editor-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    #work .work-evidence { display: grid; gap: 12px; min-width: 0; }
    #work .work-card { min-width: 0; padding: 14px; border: 1px solid var(--work-line); border-radius: 16px; background: var(--work-paper); }
    #work .work-card-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
    #work .work-card-head h2 { margin: 0; }
    #work .work-data { display: grid; gap: 10px; margin: 0; }
    #work .work-data > div { min-width: 0; }
    #work .work-break { overflow-wrap: anywhere; word-break: break-word; }
    #work .work-stale { margin-bottom: 10px; padding: 10px; border: 1px solid var(--work-green); border-radius: 12px; background: var(--work-bg); font-size: 13px; line-height: 1.45; }
    #work .work-list { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
    #work .work-list li { min-width: 0; line-height: 1.45; }
    #work .work-source { display: grid; gap: 6px; padding-top: 8px; border-top: 1px solid var(--work-line); }
    #work .work-source:first-child { padding-top: 0; border-top: 0; }
    #work .work-source-text, #work .work-warning { font-size: 13px; overflow-wrap: anywhere; }
    #work .work-list-empty { font-size: 13px; opacity: .7; }
    #work .work-chip { display: inline-block; max-width: 100%; padding: 2px 8px; border: 1px solid var(--work-line); border-radius: 999px; font-size: 10px; font-weight: 700; line-height: 1.4; letter-spacing: .04em; text-transform: uppercase; }
    #work .work-chip-warn { border-color: var(--work-green); background: var(--work-bg); color: var(--work-green); white-space: normal; }
    #work .work-integration { background: var(--work-bg); }
    #work .work-slot-note { margin: 0; font-size: 12px; opacity: .68; }
    #work .work-empty { padding: 24px; border: 1px dashed var(--work-line); border-radius: 16px; background: var(--work-paper); }
    #work .work-empty h2 { font-size: 1.15rem; }
    #work .work-empty p { margin: 0; max-width: 65ch; line-height: 1.55; }
    #work .work-sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
    @media (max-width: 900px) {
      #work .work-grid { grid-template-columns: 1fr; }
      #work .work-header { flex-direction: column; align-items: stretch; }
      #work .work-generate-block { flex-basis: auto; }
      #work .work-textarea { min-height: 320px; }
    }
    @media (max-width: 480px) {
      #work { padding: 10px; }
      #work .work-brief { grid-template-columns: 1fr; }
      #work .work-editor, #work .work-card, #work .work-empty { padding: 12px; }
      #work .work-textarea { min-height: 300px; font-size: 16px; }
    }
  </style>
  <div class='work-shell'>
    <div class='work-topbar'>
      <button id='work-back' class='work-btn work-btn-ghost' type='button'>Back to Campañas</button>
    </div>
    <header class='work-header'>
      <div class='work-titleblock'>
        <p class='work-kicker'>Workspace de campaña</p>
        <h1 id='work-title'>Elige una campaña</h1>
        <p id='work-topic' class='work-topic' hidden></p>
        <dl class='work-brief'>
          <div>
            <dt>Objetivo</dt>
            <dd id='work-objective'>—</dd>
          </div>
          <div>
            <dt>Audiencia</dt>
            <dd id='work-audience'>—</dd>
          </div>
        </dl>
      </div>
      <div class='work-generate-block'>
        <div class='work-statusline'>
          <span id='work-status' class='work-status' hidden></span>
        </div>
        <button id='work-generate' class='work-btn work-btn-primary' type='button' disabled>Generar demo</button>
        <p class='work-helper'>Generación simulada: no se ejecuta Qwen ni recuperación semántica.</p>
      </div>
    </header>
    <div id='work-alert' class='work-alert' role='alert' hidden></div>
    <p id='work-loading' class='work-loading' role='status' aria-live='polite' hidden>Cargando workspace…</p>
    <section id='work-no-campaign' class='work-empty' hidden>
      <h2>Elige una campaña</h2>
      <p>Selecciona una campaña para revisar su workspace.</p>
    </section>
    <section id='work-empty' class='work-empty' hidden>
      <h2 id='work-empty-title'>Todavía no hay una demo</h2>
      <p id='work-empty-text'>Genera una demo de forma explícita para preparar las piezas de esta campaña.</p>
    </section>
    <div id='work-content' class='work-grid' hidden>
      <main class='work-editor' aria-label='Editor de piezas'>
        <div class='work-editor-head'>
          <div>
            <p class='work-kicker'>Piezas demo</p>
            <h2>Editor</h2>
          </div>
          <span id='work-dirty' class='work-dirty' hidden>Cambios sin guardar</span>
        </div>
        <div id='work-tabs' class='work-tabs' role='tablist' aria-label='Formatos de la campaña'></div>
        <div class='work-variantrow'>
          <span class='work-label'>Variante</span>
          <div id='work-variants' class='work-variants' role='group' aria-label='Variantes disponibles'></div>
        </div>
        <section id='work-piece-panel' class='work-piece' role='tabpanel' aria-label='Pieza seleccionada'>
          <div id='work-piece-empty' class='work-piece-empty' hidden>No hay una pieza demo para este formato.</div>
          <div id='work-piece-body'>
            <div class='work-piece-meta'>
              <p>Revisión <strong id='work-revision'>—</strong></p>
              <p class='work-idline'>ID de versión <code id='work-version-id'></code></p>
              <p class='work-idline'>Hash <code id='work-content-hash'></code></p>
            </div>
            <label class='work-label' for='work-body'>Contenido</label>
            <textarea id='work-body' class='work-textarea' rows='18' spellcheck='true' aria-describedby='work-immutable-help'></textarea>
            <div class='work-editor-actions'>
              <button id='work-save' class='work-btn work-btn-primary' type='button' disabled>Guardar nueva versión</button>
              <button id='work-discard' class='work-btn work-btn-ghost' type='button' disabled>Descartar</button>
            </div>
            <p id='work-immutable-help' class='work-helper'>Cada guardado crea una versión nueva e inmutable. La versión anterior no se modifica.</p>
          </div>
        </section>
      </main>
      <aside class='work-evidence' aria-label='Evidencia de la demo'>
        <section class='work-card'>
          <div class='work-card-head'><h2>Run</h2></div>
          <dl class='work-data'>
            <div><dt>Estado</dt><dd id='work-run-status'>—</dd></div>
            <div><dt>Run ID</dt><dd><code id='work-run-id' class='work-break'></code></dd></div>
            <div><dt>Modo</dt><dd id='work-run-mode'>—</dd></div>
            <div><dt>Revisión de configuración</dt><dd id='work-run-revision'>—</dd></div>
          </dl>
        </section>
        <section class='work-card'>
          <div class='work-card-head'><h2>Configuración</h2></div>
          <div id='work-stale' class='work-stale' role='status' hidden>La revisión de configuración del run no coincide con la campaña. Revisa esta pieza antes de continuar.</div>
          <dl class='work-data'>
            <div><dt>Revisión de campaña</dt><dd id='work-brief-revision'>—</dd></div>
            <div><dt>Source hash</dt><dd><code id='work-source-hash' class='work-break'></code></dd></div>
            <div><dt>Context hash</dt><dd><code id='work-context-hash' class='work-break'></code></dd></div>
          </dl>
        </section>
        <section class='work-card'>
          <div class='work-card-head'><h2>Fuentes sintéticas</h2></div>
          <ul id='work-sources' class='work-list'></ul>
        </section>
        <section class='work-card'>
          <div class='work-card-head'><h2>Advertencias</h2></div>
          <ul id='work-warnings' class='work-list'></ul>
        </section>
        <section class='work-card'>
          <div class='work-card-head'><h2>Contexto capturado</h2></div>
          <dl class='work-data'>
            <div><dt>Piezas previas</dt><dd id='work-previous-count'>0</dd></div>
            <div><dt>Distribuciones manuales</dt><dd id='work-manual-count'>0</dd></div>
            <div><dt>Confianza</dt><dd id='work-untrusted'>—</dd></div>
          </dl>
        </section>
        <section class='work-card work-integration'>
          <div id='work-actions'></div>
          <div id='work-exports'></div>
          <p class='work-slot-note'>Revisión humana antes de exportar</p>
        </section>
      </aside>
    </div>
  </div>
  <script>
    (() => {
      'use strict';

      const root = document.getElementById('work');
      if (!root) return;

      const els = {
        back: document.getElementById('work-back'),
        title: document.getElementById('work-title'),
        topic: document.getElementById('work-topic'),
        objective: document.getElementById('work-objective'),
        audience: document.getElementById('work-audience'),
        status: document.getElementById('work-status'),
        generate: document.getElementById('work-generate'),
        alert: document.getElementById('work-alert'),
        loading: document.getElementById('work-loading'),
        noCampaign: document.getElementById('work-no-campaign'),
        empty: document.getElementById('work-empty'),
        emptyTitle: document.getElementById('work-empty-title'),
        emptyText: document.getElementById('work-empty-text'),
        content: document.getElementById('work-content'),
        dirty: document.getElementById('work-dirty'),
        tabs: document.getElementById('work-tabs'),
        variants: document.getElementById('work-variants'),
        piecePanel: document.getElementById('work-piece-panel'),
        pieceEmpty: document.getElementById('work-piece-empty'),
        pieceBody: document.getElementById('work-piece-body'),
        revision: document.getElementById('work-revision'),
        versionId: document.getElementById('work-version-id'),
        contentHash: document.getElementById('work-content-hash'),
        body: document.getElementById('work-body'),
        save: document.getElementById('work-save'),
        discard: document.getElementById('work-discard'),
        runStatus: document.getElementById('work-run-status'),
        runId: document.getElementById('work-run-id'),
        runMode: document.getElementById('work-run-mode'),
        runRevision: document.getElementById('work-run-revision'),
        briefRevision: document.getElementById('work-brief-revision'),
        stale: document.getElementById('work-stale'),
        sourceHash: document.getElementById('work-source-hash'),
        contextHash: document.getElementById('work-context-hash'),
        sources: document.getElementById('work-sources'),
        warnings: document.getElementById('work-warnings'),
        previousCount: document.getElementById('work-previous-count'),
        manualCount: document.getElementById('work-manual-count'),
        untrusted: document.getElementById('work-untrusted')
      };

      const FORMAT_DEFS = [
        { key: 'linkedin', label: 'LinkedIn', aliases: ['linkedin', 'linkedin_post', 'linkedin post'] },
        { key: 'email', label: 'Email general', aliases: ['email', 'email_general', 'email general'] },
        { key: 'article', label: 'Artículo', aliases: ['article', 'articulo'] },
        { key: 'ads', label: 'Anuncios', aliases: ['ads', 'anuncios', 'advertisements'] }
      ];

      const STATUS_LABELS = {
        needs_review: 'Pendiente de revisión',
        failed: 'Falló',
        waiting_input: 'Espera información',
        running: 'En ejecución',
        prepared: 'Preparado',
        finished: 'Finalizado',
        cancelled: 'Cancelado'
      };

      const state = {
        pageCampaignId: '',
        review: null,
        format: '',
        variant: '',
        cachedBody: '',
        dirty: false,
        loading: false,
        generating: false,
        saving: false,
        loadFailed: false,
        loadSeq: 0,
        demoRunId: null
      };

      function normalizeValue(value) {
        return String(value == null ? '' : value).trim().toLowerCase();
      }

      function formatDefFor(value) {
        const normalized = normalizeValue(value);
        for (const def of FORMAT_DEFS) {
          if (def.aliases.includes(normalized)) return def;
        }
        return null;
      }

      function formatKeyFor(value) {
        const def = formatDefFor(value);
        return def ? def.key : '';
      }

      function revisionValue(version) {
        const value = Number(version && version.revision_no);
        return Number.isFinite(value) ? value : 0;
      }

      function variantOf(version) {
        return String(version && version.variant != null ? version.variant : '');
      }

      function bundleOf() {
        return state.review && state.review.bundle ? state.review.bundle : null;
      }

      function versionsForFormat(formatKey) {
        const bundle = bundleOf();
        if (!bundle || !Array.isArray(bundle.versions)) return [];
        return bundle.versions.filter((version) => formatKeyFor(version.format) === formatKey);
      }

      function formatDefsPresent() {
        const campaign = state.review && state.review.campaign ? state.review.campaign : null;
        const formats = campaign && Array.isArray(campaign.formats) ? campaign.formats : [];
        const present = FORMAT_DEFS.filter((def) => formats.some((value) => formatKeyFor(value) === def.key));
        if (present.length > 0) return present;
        const withPieces = new Set();
        const bundle = bundleOf();
        if (bundle && Array.isArray(bundle.versions)) {
          for (const version of bundle.versions) {
            const key = formatKeyFor(version.format);
            if (key) withPieces.add(key);
          }
        }
        return FORMAT_DEFS.filter((def) => withPieces.has(def.key));
      }

      function compareVariants(left, right) {
        const order = { A: 0, B: 1, C: 2 };
        const leftKey = String(left).toUpperCase();
        const rightKey = String(right).toUpperCase();
        const leftOrder = Object.prototype.hasOwnProperty.call(order, leftKey) ? order[leftKey] : 99;
        const rightOrder = Object.prototype.hasOwnProperty.call(order, rightKey) ? order[rightKey] : 99;
        if (leftOrder !== rightOrder) return leftOrder - rightOrder;
        return String(left).localeCompare(String(right), 'es');
      }

      function variantChoices() {
        const groups = new Map();
        for (const version of versionsForFormat(state.format)) {
          const key = variantOf(version);
          const existing = groups.get(key);
          if (!existing || revisionValue(version) >= revisionValue(existing)) {
            groups.set(key, version);
          }
        }
        return Array.from(groups.entries()).sort((left, right) => compareVariants(left[0], right[0]));
      }

      function selectedVersion() {
        if (!state.format) return null;
        let selected = null;
        for (const version of versionsForFormat(state.format)) {
          if (variantOf(version) !== state.variant) continue;
          if (!selected || revisionValue(version) >= revisionValue(selected)) selected = version;
        }
        return selected;
      }

      function chooseSelection(keepFormat, keepVariant) {
        const defs = formatDefsPresent();
        let nextFormat = '';
        if (keepFormat && defs.some((def) => def.key === keepFormat)) {
          nextFormat = keepFormat;
        } else {
          const chosen = defs.find((def) => versionsForFormat(def.key).length > 0);
          nextFormat = chosen ? chosen.key : (defs[0] ? defs[0].key : '');
        }
        state.format = nextFormat;
        const choices = variantChoices();
        let nextVariant = '';
        if (keepVariant && choices.some((entry) => entry[0] === keepVariant)) {
          nextVariant = keepVariant;
        } else if (choices.length > 0) {
          nextVariant = choices[0][0];
        }
        state.variant = nextVariant;
      }

      function statusLabel(status) {
        const key = String(status == null ? '' : status);
        if (Object.prototype.hasOwnProperty.call(STATUS_LABELS, key)) return STATUS_LABELS[key];
        return key || 'Sin estado';
      }

      function formatValue(value) {
        if (value === null || value === undefined || value === '') return '—';
        return String(value);
      }

      function errorMessage(error) {
        if (typeof error === 'string' && error.trim()) return error.trim();
        const message = error && typeof error.message === 'string' ? error.message.trim() : '';
        return message || 'No se pudo completar la solicitud.';
      }

      function plainText(value) {
        if (typeof value === 'string') return value;
        if (value == null) return '';
        try { return JSON.stringify(value); } catch (error) { return String(value); }
      }

      function sourceText(source) {
        if (typeof source === 'string') return source.trim() || 'Fuente sintética';
        if (!source || typeof source !== 'object') return String(source);
        const fields = ['title', 'name', 'label', 'url', 'id'];
        for (const field of fields) {
          const value = source[field];
          if (typeof value === 'string' && value.trim()) return value.trim();
        }
        try { return JSON.stringify(source); } catch (error) { return 'Fuente sintética'; }
      }

      function publish() {
        const snapshot = {
          review: state.review || null,
          dirty: Boolean(state.dirty),
          loading: Boolean(state.loading || state.generating || state.saving)
        };
        window.gwaWorkSnapshot = snapshot;
        document.dispatchEvent(new CustomEvent('gwa:review', { detail: snapshot }));
      }

      function showAlert(message) {
        els.alert.textContent = String(message);
        els.alert.hidden = false;
      }

      function clearAlert() {
        els.alert.textContent = '';
        els.alert.hidden = true;
      }

      function externalBusy() {
        return window.gwaWorkActionBusy === true;
      }

      function guardDirty(action) {
        if (!state.dirty) return false;
        showAlert(`Guarda o descarta los cambios antes de ${action}.`);
        return true;
      }

      function updateDirtyUI() {
        els.dirty.hidden = !state.dirty;
      }

      function updateControls() {
        const busy = Boolean(state.loading || state.generating || state.saving);
        const bundle = bundleOf();
        const version = selectedVersion();
        const canGenerate = Boolean(state.pageCampaignId) && !busy;
        els.generate.disabled = !canGenerate;
        if (state.generating) {
          els.generate.textContent = 'Generando demo…';
        } else {
          els.generate.textContent = bundle ? 'Generar otra demo' : 'Generar demo';
        }
        els.back.disabled = state.generating || state.saving;
        const canEdit = Boolean(version) && !busy;
        els.body.disabled = !canEdit;
        els.save.disabled = !state.dirty || !version || busy;
        els.discard.disabled = !state.dirty || !version || busy;
        els.dirty.hidden = !state.dirty;
        root.setAttribute('aria-busy', busy ? 'true' : 'false');
      }

      function renderHeader() {
        const campaign = state.review && state.review.campaign ? state.review.campaign : null;
        const bundle = bundleOf();
        const run = bundle ? bundle.run : null;

        if (campaign) {
          els.title.textContent = campaign.title ? String(campaign.title) : 'Campaña';
          if (campaign.topic) {
            els.topic.textContent = `Tema: ${String(campaign.topic)}`;
            els.topic.hidden = false;
          } else {
            els.topic.textContent = '';
            els.topic.hidden = true;
          }
          els.objective.textContent = campaign.objective ? String(campaign.objective) : '—';
          els.audience.textContent = campaign.audience_segment ? String(campaign.audience_segment) : '—';
        } else {
          els.title.textContent = state.pageCampaignId ? 'Workspace de campaña' : 'Elige una campaña';
          els.topic.textContent = '';
          els.topic.hidden = true;
          els.objective.textContent = '—';
          els.audience.textContent = '—';
        }

        if (run && run.status) {
          const label = statusLabel(run.status);
          els.status.textContent = label;
          els.status.setAttribute('aria-label', `Estado: ${label}`);
          els.status.hidden = false;
        } else {
          els.status.textContent = '';
          els.status.removeAttribute('aria-label');
          els.status.hidden = true;
        }
      }

      function renderState() {
        const busy = Boolean(state.loading || state.generating || state.saving);
        const bundle = bundleOf();

        if (busy) {
          els.loading.hidden = false;
          els.noCampaign.hidden = true;
          els.empty.hidden = true;
          els.content.hidden = true;
          return;
        }

        els.loading.hidden = true;
        if (!state.pageCampaignId) {
          els.noCampaign.hidden = false;
          els.empty.hidden = true;
          els.content.hidden = true;
          return;
        }

        els.noCampaign.hidden = true;
        if (!state.review) {
          els.content.hidden = true;
          els.empty.hidden = false;
          if (state.loadFailed) {
            els.emptyTitle.textContent = 'No se pudo cargar el workspace';
            els.emptyText.textContent = 'Vuelve a abrir la campaña para intentarlo de nuevo.';
          } else {
            els.emptyTitle.textContent = 'Preparando el workspace';
            els.emptyText.textContent = 'Cargando la revisión de la campaña.';
          }
          return;
        }

        if (!bundle) {
          els.content.hidden = true;
          els.empty.hidden = false;
          els.emptyTitle.textContent = 'Todavía no hay una demo';
          els.emptyText.textContent = 'Genera una demo de forma explícita para preparar las piezas de esta campaña.';
          return;
        }

        els.empty.hidden = true;
        els.content.hidden = false;
      }

      function clearEditorDom() {
        els.tabs.replaceChildren();
        els.variants.replaceChildren();
        els.body.value = '';
        els.revision.textContent = '—';
        els.versionId.textContent = '';
        els.contentHash.textContent = '';
        els.sources.replaceChildren();
        els.warnings.replaceChildren();
        els.stale.hidden = true;
        els.previousCount.textContent = '0';
        els.manualCount.textContent = '0';
        els.untrusted.textContent = '—';
        state.cachedBody = '';
        updateControls();
      }

      function appendEmpty(list, text) {
        const item = document.createElement('li');
        item.className = 'work-list-empty';
        item.textContent = text;
        list.append(item);
      }

      function renderEvidence() {
        const bundle = bundleOf();
        if (!bundle) return;
        const run = bundle.run || {};
        const campaign = state.review && state.review.campaign ? state.review.campaign : {};
        const context = run.context || {};
        const briefRevision = campaign.config_revision;
        const runRevision = run.config_revision;

        els.runStatus.textContent = statusLabel(run.status);
        els.runId.textContent = formatValue(run.id);
        const modeParts = [];
        if (bundle.mode != null && String(bundle.mode).trim()) modeParts.push(String(bundle.mode));
        if (bundle.generation != null && String(bundle.generation).trim()) modeParts.push(String(bundle.generation));
        els.runMode.textContent = modeParts.length ? modeParts.join(' · ') : '—';
        els.runRevision.textContent = formatValue(runRevision);
        els.briefRevision.textContent = formatValue(briefRevision);
        const stale = briefRevision != null && runRevision != null && String(briefRevision) !== String(runRevision);
        els.stale.hidden = !stale;
        els.sourceHash.textContent = formatValue(bundle.source_hash);
        els.contextHash.textContent = formatValue(bundle.context_hash);

        els.sources.replaceChildren();
        const sources = Array.isArray(run.sources) ? run.sources : [];
        if (sources.length === 0) appendEmpty(els.sources, 'Sin fuentes registradas.');
        sources.forEach((source) => {
          const item = document.createElement('li');
          item.className = 'work-source';
          const badge = document.createElement('span');
          badge.className = 'work-chip work-chip-warn';
          badge.textContent = 'Sintético · demo-fixture';
          const text = document.createElement('span');
          text.className = 'work-source-text';
          text.textContent = sourceText(source);
          item.append(badge, text);
          els.sources.append(item);
        });

        els.warnings.replaceChildren();
        const warnings = Array.isArray(bundle.warnings) ? bundle.warnings : [];
        if (warnings.length === 0) appendEmpty(els.warnings, 'Sin advertencias.');
        warnings.forEach((warning) => {
          const item = document.createElement('li');
          item.className = 'work-warning';
          item.textContent = plainText(warning);
          els.warnings.append(item);
        });

        els.previousCount.textContent = String(Array.isArray(context.previous_pieces) ? context.previous_pieces.length : 0);
        const manualValue = Number(context.manual_distribution_count);
        els.manualCount.textContent = String(Number.isFinite(manualValue) ? manualValue : 0);
        els.untrusted.textContent = context.untrusted === true ? 'Contexto no confiable (demo)' : '—';
      }

      function renderTabs() {
        els.tabs.replaceChildren();
        const defs = formatDefsPresent();
        if (defs.length === 0) {
          const note = document.createElement('p');
          note.className = 'work-muted';
          note.textContent = 'No hay formatos disponibles en esta campaña.';
          els.tabs.append(note);
          return;
        }
        defs.forEach((def) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'work-tab';
          button.id = `work-tab-${def.key}`;
          button.setAttribute('role', 'tab');
          button.setAttribute('aria-selected', state.format === def.key ? 'true' : 'false');
          button.setAttribute('aria-controls', 'work-piece-panel');
          button.textContent = def.label;
          button.addEventListener('click', () => { selectFormat(def.key); });
          els.tabs.append(button);
        });
      }

      function renderVariants() {
        els.variants.replaceChildren();
        if (!state.format) return;
        const choices = variantChoices();
        if (choices.length === 0) {
          const note = document.createElement('span');
          note.className = 'work-muted';
          note.textContent = 'Sin variantes demo.';
          els.variants.append(note);
          return;
        }
        choices.forEach((entry) => {
          const variant = entry[0];
          const display = String(variant || '—').toUpperCase();
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'work-variant';
          button.setAttribute('aria-pressed', state.variant === variant ? 'true' : 'false');
          button.setAttribute('aria-label', `Variante ${display}`);
          button.title = `Variante ${display}`;
          const label = document.createElement('span');
          label.textContent = display;
          const sr = document.createElement('span');
          sr.className = 'work-sr-only';
          sr.textContent = `Variante ${display}`;
          button.append(label, sr);
          button.addEventListener('click', () => { selectVariant(variant); });
          els.variants.append(button);
        });
      }

      function renderPiece() {
        const version = selectedVersion();
        const hasVersion = Boolean(version);
        els.pieceEmpty.hidden = hasVersion;
        els.pieceBody.hidden = !hasVersion;

        if (!hasVersion) {
          els.piecePanel.removeAttribute('aria-labelledby');
          state.cachedBody = '';
          els.revision.textContent = '—';
          els.versionId.textContent = '';
          els.contentHash.textContent = '';
          els.body.value = '';
          updateControls();
          return;
        }

        els.piecePanel.setAttribute('aria-labelledby', `work-tab-${state.format}`);
        const body = version.body == null ? '' : String(version.body);
        state.cachedBody = body;
        els.revision.textContent = version.revision_no == null ? '—' : String(version.revision_no);
        els.versionId.textContent = version.id == null ? '' : String(version.id);
        els.contentHash.textContent = version.content_hash == null ? '' : String(version.content_hash);
        els.body.value = body;
        updateControls();
      }

      function setDirty(value) {
        const next = Boolean(value);
        if (state.dirty === next) {
          updateDirtyUI();
          updateControls();
          return;
        }
        state.dirty = next;
        updateDirtyUI();
        updateControls();
        publish();
      }

      function selectFormat(key) {
        if (key === state.format) return;
        if (state.loading || state.saving || state.generating || externalBusy()) return;
        if (guardDirty('cambiar de formato')) return;
        state.format = key;
        const choices = variantChoices();
        state.variant = choices.length > 0 ? choices[0][0] : '';
        renderTabs();
        renderVariants();
        renderPiece();
      }

      function selectVariant(variant) {
        if (variant === state.variant) return;
        if (state.loading || state.saving || state.generating || externalBusy()) return;
        if (guardDirty('cambiar de variante')) return;
        state.variant = variant;
        renderVariants();
        renderPiece();
      }

      async function refreshReview(options) {
        const campaignId = String(options && options.campaignId != null ? options.campaignId : '').trim();
        const runId = options && options.runId != null && options.runId !== '' ? String(options.runId) : null;
        const preserveSelection = Boolean(options && options.preserveSelection);
        const clearDirty = Boolean(options && options.clearDirty);
        if (!campaignId || campaignId !== String(state.pageCampaignId)) return false;

        const keepFormat = state.format;
        const keepVariant = state.variant;
        const seq = state.loadSeq + 1;
        state.loadSeq = seq;
        state.loading = true;
        state.loadFailed = false;
        clearAlert();
        publish();
        renderState();
        updateControls();

        try {
          let path = `/api/campaigns/${encodeURIComponent(campaignId)}/review`;
          if (runId) path += `?run_id=${encodeURIComponent(runId)}`;
          const nextReview = await window.gwaApi(path, 'GET');
          if (seq !== state.loadSeq) return false;
          if (campaignId !== String(state.pageCampaignId)) {
            state.loading = false;
            updateControls();
            publish();
            return false;
          }
          if (!nextReview || !nextReview.campaign) {
            throw new Error('La respuesta no incluye la campaña.');
          }
          if (String(nextReview.campaign.id) !== campaignId) {
            throw new Error('La campaña devuelta no coincide con la seleccionada.');
          }
          const nextBundle = nextReview.bundle || null;
          if (runId && !nextBundle) {
            throw new Error('La demo todavía no está disponible.');
          }
          if (runId && nextBundle && nextBundle.run) {
            if (nextBundle.run.campaign_id != null && String(nextBundle.run.campaign_id) !== campaignId) {
              throw new Error('El run devuelto no pertenece a la campaña seleccionada.');
            }
            if (nextBundle.run.id != null && String(nextBundle.run.id) !== runId) {
              throw new Error('El run devuelto no coincide con la demo solicitada.');
            }
          }

          state.review = nextReview;
          state.loading = false;
          state.loadFailed = false;
          if (clearDirty) state.dirty = false;
          chooseSelection(preserveSelection ? keepFormat : '', preserveSelection ? keepVariant : '');
          renderHeader();
          renderState();
          if (state.review.bundle) {
            renderTabs();
            renderVariants();
            renderPiece();
            renderEvidence();
          } else {
            els.tabs.replaceChildren();
            els.variants.replaceChildren();
            els.body.value = '';
            state.cachedBody = '';
          }
          updateDirtyUI();
          updateControls();
          publish();
          return true;
        } catch (error) {
          if (seq !== state.loadSeq) return false;
          state.loading = false;
          if (!state.review) state.loadFailed = true;
          showAlert(`No se pudo cargar el workspace. ${errorMessage(error)}`);
          renderHeader();
          renderState();
          updateControls();
          publish();
          return false;
        }
      }

      function enterWork(rawCampaignId) {
        const campaignId = String(rawCampaignId == null ? '' : rawCampaignId).trim();
        if (state.generating || state.saving) {
          showAlert('Espera a que termine la acción en curso.');
          return;
        }

        if (!campaignId) {
          if (state.dirty && state.pageCampaignId) {
            showAlert('Guarda o descarta los cambios antes de cambiar de campaña.');
            return;
          }
          state.loadSeq += 1;
          state.pageCampaignId = '';
          state.review = null;
          state.format = '';
          state.variant = '';
          state.dirty = false;
          state.loading = false;
          state.loadFailed = false;
          state.demoRunId = null;
          clearAlert();
          clearEditorDom();
          renderHeader();
          renderState();
          updateDirtyUI();
          updateControls();
          publish();
          return;
        }

        const changed = state.pageCampaignId !== campaignId;
        if (state.dirty) {
          if (changed) {
            showAlert('Guarda o descarta los cambios de la campaña anterior antes de abrir otra campaña.');
          } else {
            showAlert('Guarda o descarta los cambios antes de recargar el workspace.');
          }
          return;
        }

        const keepRunId = !changed && state.review && state.review.bundle && state.review.bundle.run ? state.review.bundle.run.id : null;
        if (changed) {
          state.loadSeq += 1;
          state.pageCampaignId = campaignId;
          state.review = null;
          state.format = '';
          state.variant = '';
          state.dirty = false;
          state.loading = false;
          state.loadFailed = false;
          state.demoRunId = null;
          clearEditorDom();
          renderHeader();
          renderState();
          updateControls();
          publish();
        }

        refreshReview({
          campaignId,
          runId: keepRunId,
          preserveSelection: !changed,
          clearDirty: true
        });
      }

      document.addEventListener('gwa:show', (event) => {
        if (event.detail !== 'work') return;
        enterWork(window.gwaCampaignId);
      });

      els.back.addEventListener('click', () => {
        if (state.generating || state.saving) {
          showAlert('Espera a que termine la acción en curso.');
          return;
        }
        if (externalBusy()) return;
        if (guardDirty('volver a Campañas')) return;
        state.loadSeq += 1;
        state.loading = false;
        updateControls();
        publish();
        window.gwaShowView('campaigns');
      });

      els.generate.addEventListener('click', async () => {
        if (externalBusy() || state.generating || state.saving || state.loading) return;
        const campaignId = String(state.pageCampaignId || '').trim();
        if (!campaignId) {
          showAlert('Elige una campaña antes de generar una demo.');
          return;
        }
        if (guardDirty('generar una demo')) return;

        let runId = state.demoRunId;
        if (!runId) {
          try {
            runId = crypto.randomUUID();
          } catch (error) {
            showAlert('No se pudo iniciar la demo. Inténtalo de nuevo.');
            return;
          }
          state.demoRunId = runId;
        }

        const preserveSelection = Boolean(state.review && state.review.bundle);
        state.generating = true;
        state.loading = true;
        clearAlert();
        publish();
        renderState();
        updateControls();

        try {
          await window.gwaApi(`/api/campaigns/${encodeURIComponent(campaignId)}/demo`, 'POST', { run_id: runId });
          if (String(state.pageCampaignId) !== campaignId) return;
          const loaded = await refreshReview({
            campaignId,
            runId,
            preserveSelection,
            clearDirty: false
          });
          if (loaded) state.demoRunId = null;
        } catch (error) {
          showAlert(`No se pudo generar la demo. ${errorMessage(error)} Puedes reintentar la generación explícita.`);
        } finally {
          state.generating = false;
          state.loading = false;
          renderState();
          updateControls();
          publish();
        }
      });

      els.body.addEventListener('input', () => {
        if (state.loading || state.saving || state.generating) return;
        if (!selectedVersion()) return;
        setDirty(els.body.value !== state.cachedBody);
      });

      els.save.addEventListener('click', async () => {
        if (externalBusy() || state.generating || state.saving || state.loading) return;
        if (!state.dirty) return;
        const version = selectedVersion();
        const review = state.review;
        const bundle = bundleOf();
        if (!version || !review || !review.campaign || !bundle) return;

        const campaignId = String(review.campaign.id || state.pageCampaignId);
        const runId = bundle.run && bundle.run.id ? String(bundle.run.id) : null;
        const body = els.body.value;
        const expectedHash = version.content_hash;

        state.saving = true;
        state.loading = true;
        clearAlert();
        publish();
        renderState();
        updateControls();

        try {
          await window.gwaApi(`/api/versions/${encodeURIComponent(String(version.id))}`, 'PUT', {
            body,
            expected_hash: expectedHash
          });
          if (String(state.pageCampaignId) !== campaignId) return;
          await refreshReview({
            campaignId,
            runId,
            preserveSelection: true,
            clearDirty: true
          });
        } catch (error) {
          showAlert(`No se pudo guardar la nueva versión. ${errorMessage(error)}`);
        } finally {
          state.saving = false;
          state.loading = false;
          renderState();
          updateControls();
          publish();
        }
      });

      els.discard.addEventListener('click', () => {
        if (externalBusy() || state.loading || state.saving || state.generating) return;
        if (!state.dirty) return;
        els.body.value = state.cachedBody;
        setDirty(false);
        clearAlert();
        els.body.focus();
      });

      window.gwaReloadWork = function () {
        if (state.loading || state.saving || state.generating || externalBusy()) return Promise.resolve(false);
        if (state.dirty) {
          showAlert('Guarda o descarta los cambios antes de recargar el workspace.');
          return Promise.resolve(false);
        }
        const review = state.review;
        if (!review || !review.campaign) return Promise.resolve(false);
        const campaignId = String(review.campaign.id || state.pageCampaignId);
        const runId = review.bundle && review.bundle.run && review.bundle.run.id ? review.bundle.run.id : null;
        return refreshReview({
          campaignId,
          runId,
          preserveSelection: true,
          clearDirty: true
        });
      };

      window.addEventListener('beforeunload', (event) => {
        if (!state.dirty) return;
        event.preventDefault();
        event.returnValue = '';
      });

      renderHeader();
      renderState();
      updateControls();
      publish();
    })();
  </script>
</section>'''


def workspace_panel() -> str:
    '''Return the work workspace HTML fragment.'''
    return WORKSPACE_HTML
