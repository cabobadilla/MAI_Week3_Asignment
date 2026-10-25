def campaigns_panel() -> str:
    return '''<style>
#campaigns[hidden], #campaigns [hidden] { display: none !important; }
#campaigns { --campaigns-paper: #fffef9; --campaigns-bg: #f3f4ed; --campaigns-text: #173a35; --campaigns-primary: #215b48; --campaigns-border: #dce3d5; --campaigns-muted: rgba(23, 58, 53, 0.68); width: 100%; padding: 32px 24px 56px; color: var(--campaigns-text); background: var(--campaigns-bg); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.5; }
#campaigns, #campaigns * { box-sizing: border-box; }
#campaigns .gwa-campaigns__inner { width: 100%; max-width: 1180px; margin: 0 auto; }
#campaigns .gwa-campaigns__header { margin: 0 0 22px; }
#campaigns .gwa-campaigns__title { margin: 0; font-size: 30px; line-height: 1.15; letter-spacing: -0.02em; }
#campaigns .gwa-campaigns__layout { display: grid; grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr); gap: 24px; align-items: start; }
#campaigns .gwa-campaigns__card { min-width: 0; padding: 24px; border: 1px solid var(--campaigns-border); border-radius: 16px; background: var(--campaigns-paper); }
#campaigns .gwa-campaigns__card-heading { margin: 0 0 16px; font-size: 19px; line-height: 1.3; letter-spacing: -0.01em; }
#campaigns button { font: inherit; }
#campaigns .gwa-campaigns__button { min-height: 44px; padding: 10px 16px; border: 1px solid var(--campaigns-primary); border-radius: 10px; color: var(--campaigns-paper); background: var(--campaigns-primary); font: inherit; font-weight: 600; line-height: 1.2; cursor: pointer; }
#campaigns .gwa-campaigns__button--secondary { color: var(--campaigns-text); background: var(--campaigns-paper); border-color: var(--campaigns-border); white-space: nowrap; }
#campaigns .gwa-campaigns__button--secondary:hover:not(:disabled) { border-color: var(--campaigns-primary); }
#campaigns .gwa-campaigns__button:disabled { opacity: 0.58; cursor: not-allowed; }
#campaigns :focus-visible { outline: 3px solid var(--campaigns-primary); outline-offset: 2px; }
#campaigns .gwa-campaigns__state { margin: 0; padding: 14px 0; color: var(--campaigns-muted); font-size: 14px; }
#campaigns .gwa-campaigns__state-box { display: grid; gap: 10px; padding: 14px; border: 1px dashed var(--campaigns-border); border-radius: 12px; background: var(--campaigns-bg); }
#campaigns .gwa-campaigns__state-box--error { border-style: solid; border-color: var(--campaigns-primary); background: var(--campaigns-paper); }
#campaigns .gwa-campaigns__state-box p { margin: 0; font-size: 14px; overflow-wrap: anywhere; }
#campaigns .gwa-campaigns__state-title { font-weight: 600; }
#campaigns .gwa-campaigns__state-box .gwa-campaigns__button { justify-self: start; }
#campaigns .gwa-campaigns__list { display: grid; gap: 12px; }
#campaigns .gwa-campaigns__item { display: flex; align-items: center; justify-content: space-between; gap: 14px; min-width: 0; padding: 14px; border: 1px solid var(--campaigns-border); border-radius: 12px; }
#campaigns .gwa-campaigns__item-body { min-width: 0; }
#campaigns .gwa-campaigns__item-title { margin: 0 0 4px; font-size: 16px; line-height: 1.3; overflow-wrap: anywhere; }
#campaigns .gwa-campaigns__meta { margin: 0; color: var(--campaigns-muted); font-size: 13px; overflow-wrap: anywhere; }
#campaigns .gwa-campaigns__form { display: grid; gap: 14px; }
#campaigns .gwa-campaigns__field { display: grid; gap: 6px; min-width: 0; }
#campaigns .gwa-campaigns__label, #campaigns .gwa-campaigns__legend { margin: 0; font-size: 14px; font-weight: 600; line-height: 1.35; }
#campaigns .gwa-campaigns__required { color: var(--campaigns-primary); }
#campaigns .gwa-campaigns__input, #campaigns .gwa-campaigns__select, #campaigns .gwa-campaigns__textarea { width: 100%; max-width: 100%; min-height: 44px; padding: 10px 12px; border: 1px solid var(--campaigns-border); border-radius: 10px; color: var(--campaigns-text); background: var(--campaigns-paper); font: inherit; }
#campaigns .gwa-campaigns__textarea { min-height: 100px; resize: vertical; }
#campaigns .gwa-campaigns__input::placeholder, #campaigns .gwa-campaigns__textarea::placeholder { color: var(--campaigns-muted); }
#campaigns .gwa-campaigns__row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
#campaigns .gwa-campaigns__fieldset { min-width: 0; margin: 0; padding: 0; border: 0; }
#campaigns .gwa-campaigns__legend { margin-bottom: 8px; padding: 0; }
#campaigns .gwa-campaigns__formats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
#campaigns .gwa-campaigns__check, #campaigns .gwa-campaigns__suite { display: flex; align-items: flex-start; gap: 9px; min-width: 0; min-height: 44px; padding: 10px; border: 1px solid var(--campaigns-border); border-radius: 10px; background: var(--campaigns-paper); font-size: 14px; font-weight: 500; line-height: 1.3; cursor: pointer; }
#campaigns .gwa-campaigns__check { align-items: center; padding: 8px 10px; }
#campaigns .gwa-campaigns__suite { gap: 10px; background: var(--campaigns-bg); font-weight: 600; }
#campaigns .gwa-campaigns__check input, #campaigns .gwa-campaigns__suite input { flex: 0 0 auto; width: 18px; height: 18px; margin: 0; accent-color: var(--campaigns-primary); }
#campaigns .gwa-campaigns__check.is-disabled { opacity: 0.62; cursor: not-allowed; }
#campaigns .gwa-campaigns__help { margin: -2px 0 0; color: var(--campaigns-muted); font-size: 13px; line-height: 1.5; }
#campaigns .gwa-campaigns__message { margin: 0; padding: 10px 12px; border: 1px solid var(--campaigns-primary); border-radius: 10px; background: var(--campaigns-bg); font-size: 14px; line-height: 1.45; overflow-wrap: anywhere; }
#campaigns .gwa-campaigns__message--success { background: var(--campaigns-paper); }
#campaigns .gwa-campaigns__actions { display: flex; justify-content: flex-start; }
#campaigns .gwa-campaigns__actions .gwa-campaigns__button { min-width: 180px; }
@media (max-width: 760px) {
  #campaigns { padding: 22px 16px 42px; }
  #campaigns .gwa-campaigns__title { font-size: 26px; }
  #campaigns .gwa-campaigns__layout { grid-template-columns: minmax(0, 1fr); gap: 18px; }
  #campaigns .gwa-campaigns__card { padding: 18px; }
}
@media (max-width: 430px) {
  #campaigns .gwa-campaigns__row, #campaigns .gwa-campaigns__formats { grid-template-columns: minmax(0, 1fr); }
  #campaigns .gwa-campaigns__actions, #campaigns .gwa-campaigns__actions .gwa-campaigns__button, #campaigns .gwa-campaigns__state-box .gwa-campaigns__button, #campaigns .gwa-campaigns__item .gwa-campaigns__button { width: 100%; }
  #campaigns .gwa-campaigns__item { align-items: stretch; flex-direction: column; }
}
</style>
<section id='campaigns' class='gwa-campaigns' aria-labelledby='campaigns-panel-title' hidden>
  <div class='gwa-campaigns__inner'>
    <header class='gwa-campaigns__header'>
      <h2 class='gwa-campaigns__title' id='campaigns-panel-title'>Campañas</h2>
    </header>
    <div class='gwa-campaigns__layout'>
      <section class='gwa-campaigns__card gwa-campaigns__catalog' aria-labelledby='campaigns-catalog-title'>
        <h3 class='gwa-campaigns__card-heading' id='campaigns-catalog-title'>Campañas actuales</h3>
        <p id='campaigns-loading' class='gwa-campaigns__state' role='status' hidden>Cargando campañas…</p>
        <div id='campaigns-list' class='gwa-campaigns__list' hidden></div>
        <div id='campaigns-empty' class='gwa-campaigns__state-box' hidden>
          <p class='gwa-campaigns__state-title'>Aún no hay campañas.</p>
          <p>Crea la primera campaña con el formulario.</p>
        </div>
        <div id='campaigns-catalog-error' class='gwa-campaigns__state-box gwa-campaigns__state-box--error' role='alert' hidden>
          <p id='campaigns-catalog-error-text'></p>
          <button id='campaigns-retry' class='gwa-campaigns__button gwa-campaigns__button--secondary' type='button'>Reintentar</button>
        </div>
      </section>
      <section class='gwa-campaigns__card' aria-labelledby='campaigns-form-title'>
        <h3 class='gwa-campaigns__card-heading' id='campaigns-form-title'>Nueva campaña</h3>
        <form id='campaigns-form' class='gwa-campaigns__form' novalidate>
          <div class='gwa-campaigns__field'>
            <label class='gwa-campaigns__label' for='campaigns-name'>Nombre de campaña <span class='gwa-campaigns__required' aria-hidden='true'>*</span></label>
            <input class='gwa-campaigns__input' id='campaigns-name' name='title' type='text' autocomplete='off' required>
          </div>
          <div class='gwa-campaigns__field'>
            <label class='gwa-campaigns__label' for='campaigns-topic'>Tema <span class='gwa-campaigns__required' aria-hidden='true'>*</span></label>
            <input class='gwa-campaigns__input' id='campaigns-topic' name='topic' type='text' required>
          </div>
          <div class='gwa-campaigns__field'>
            <label class='gwa-campaigns__label' for='campaigns-objective'>Objetivo <span class='gwa-campaigns__required' aria-hidden='true'>*</span></label>
            <textarea class='gwa-campaigns__textarea' id='campaigns-objective' name='objective' rows='3' required></textarea>
          </div>
          <div class='gwa-campaigns__row'>
            <div class='gwa-campaigns__field'>
              <label class='gwa-campaigns__label' for='campaigns-audience'>Audiencia <span class='gwa-campaigns__required' aria-hidden='true'>*</span></label>
              <select class='gwa-campaigns__select' id='campaigns-audience' name='audience_segment' required>
                <option value=''>Selecciona una audiencia</option>
                <option value='companies'>Empresas</option>
                <option value='beneficiaries'>Municipalidades/beneficiarias</option>
                <option value='allies'>Aliados</option>
                <option value='youth'>Jóvenes</option>
                <option value='general'>General</option>
              </select>
            </div>
            <div class='gwa-campaigns__field'>
              <label class='gwa-campaigns__label' for='campaigns-tone'>Tono <span class='gwa-campaigns__required' aria-hidden='true'>*</span></label>
              <select class='gwa-campaigns__select' id='campaigns-tone' name='tone' required>
                <option value=''>Selecciona un tono</option>
                <option value='cercano'>Cercano</option>
                <option value='institucional'>Institucional</option>
                <option value='directo'>Directo</option>
              </select>
            </div>
          </div>
          <fieldset class='gwa-campaigns__fieldset'>
            <legend class='gwa-campaigns__legend'>Formatos</legend>
            <div class='gwa-campaigns__formats'>
              <label class='gwa-campaigns__check is-disabled'><input type='checkbox' name='formats' value='linkedin' checked disabled><span>LinkedIn</span></label>
              <label class='gwa-campaigns__check is-disabled'><input type='checkbox' name='formats' value='email' checked disabled><span>Email general</span></label>
              <label class='gwa-campaigns__check is-disabled'><input type='checkbox' name='formats' value='article' checked disabled><span>Artículo</span></label>
              <label class='gwa-campaigns__check is-disabled'><input type='checkbox' name='formats' value='ad' checked disabled><span>Anuncios</span></label>
            </div>
          </fieldset>
          <label class='gwa-campaigns__suite'>
            <input id='campaigns-academic-suite' type='checkbox' checked aria-describedby='campaigns-help'>
            <span>Suite académica: cuatro formatos</span>
          </label>
          <p class='gwa-campaigns__help' id='campaigns-help'>Los anuncios incluyen tres variantes. El email es general; el envío ocurre fuera de la app.</p>
          <p class='gwa-campaigns__message' id='campaigns-form-error' role='alert' hidden></p>
          <p class='gwa-campaigns__message gwa-campaigns__message--success' id='campaigns-form-success' role='status' hidden></p>
          <div class='gwa-campaigns__actions'>
            <button class='gwa-campaigns__button' id='campaigns-submit' type='submit'>Crear campaña</button>
          </div>
        </form>
      </section>
    </div>
  </div>
</section>
<script>
(function () {
  'use strict';

  const root = document.getElementById('campaigns');
  if (!root || root.getAttribute('data-campaigns-ready') === '1') return;
  root.setAttribute('data-campaigns-ready', '1');

  const form = document.getElementById('campaigns-form');
  if (!form) return;

  const catalogList = document.getElementById('campaigns-list');
  const catalogLoading = document.getElementById('campaigns-loading');
  const catalogEmpty = document.getElementById('campaigns-empty');
  const catalogError = document.getElementById('campaigns-catalog-error');
  const catalogErrorText = document.getElementById('campaigns-catalog-error-text');
  const retryButton = document.getElementById('campaigns-retry');
  const submitButton = document.getElementById('campaigns-submit');
  const formError = document.getElementById('campaigns-form-error');
  const formSuccess = document.getElementById('campaigns-form-success');
  const titleInput = document.getElementById('campaigns-name');
  const topicInput = document.getElementById('campaigns-topic');
  const objectiveInput = document.getElementById('campaigns-objective');
  const audienceSelect = document.getElementById('campaigns-audience');
  const toneSelect = document.getElementById('campaigns-tone');
  const suiteCheckbox = document.getElementById('campaigns-academic-suite');
  const formatInputs = Array.from(form.querySelectorAll('input[name=formats]'));

  const audienceLabels = {
    companies: 'Empresas',
    beneficiaries: 'Municipalidades/beneficiarias',
    allies: 'Aliados',
    youth: 'Jóvenes',
    general: 'General'
  };

  let catalogRequest = 0;
  let saving = false;

  function errorMessage(error, fallback) {
    if (error && typeof error.message === 'string') {
      const message = error.message.trim();
      if (message) return message;
    }
    return fallback;
  }

  function formatCountLabel(count) {
    return count === 1 ? '1 formato' : String(count) + ' formatos';
  }

  function audienceLabel(value) {
    return audienceLabels[value] || 'Audiencia no indicada';
  }

  function renderCatalog(campaigns) {
    catalogList.replaceChildren();
    if (campaigns.length === 0) {
      catalogList.hidden = true;
      catalogEmpty.hidden = false;
      return;
    }

    catalogEmpty.hidden = true;
    catalogList.hidden = false;

    campaigns.forEach(function (campaign) {
      const article = document.createElement('article');
      article.className = 'gwa-campaigns__item';

      const body = document.createElement('div');
      body.className = 'gwa-campaigns__item-body';

      const heading = document.createElement('h4');
      heading.className = 'gwa-campaigns__item-title';
      heading.textContent = campaign && typeof campaign.title === 'string' && campaign.title.trim()
        ? campaign.title
        : 'Campaña sin título';

      const formats = campaign && Array.isArray(campaign.formats) ? campaign.formats : [];
      const meta = document.createElement('p');
      meta.className = 'gwa-campaigns__meta';
      meta.textContent = audienceLabel(campaign && campaign.audience_segment) + ' · ' + formatCountLabel(formats.length);

      body.appendChild(heading);
      body.appendChild(meta);

      const openButton = document.createElement('button');
      openButton.type = 'button';
      openButton.className = 'gwa-campaigns__button gwa-campaigns__button--secondary';
      openButton.textContent = 'Abrir mesa';

      const campaignId = campaign && typeof campaign.id === 'string' ? campaign.id : '';
      openButton.disabled = !campaignId;
      openButton.addEventListener('click', function () {
        if (!campaignId) return;
        window.gwaCampaignId = campaignId;
        window.gwaShowView('work');
      });

      article.appendChild(body);
      article.appendChild(openButton);
      catalogList.appendChild(article);
    });
  }

  async function loadCatalog(options) {
    const quiet = Boolean(options && options.quiet);
    const requestId = ++catalogRequest;

    if (!quiet) {
      catalogLoading.hidden = false;
      catalogError.hidden = true;
      catalogErrorText.textContent = '';
      catalogEmpty.hidden = true;
      catalogList.hidden = true;
    }

    try {
      const data = await window.gwaApi('/api/campaigns', 'GET');
      if (requestId !== catalogRequest) return;
      if (!Array.isArray(data)) throw new Error('Respuesta inválida del servidor.');
      catalogLoading.hidden = true;
      catalogError.hidden = true;
      catalogErrorText.textContent = '';
      renderCatalog(data);
    } catch (error) {
      if (requestId !== catalogRequest) return;
      catalogLoading.hidden = true;
      if (quiet) return;
      catalogList.hidden = true;
      catalogEmpty.hidden = true;
      catalogError.hidden = false;
      catalogErrorText.textContent = errorMessage(error, 'No pudimos cargar las campañas. Inténtalo de nuevo.');
    }
  }

  function syncAcademicSuite() {
    const locked = suiteCheckbox.checked;
    formatInputs.forEach(function (input) {
      if (locked) input.checked = true;
      input.disabled = locked;
      if (input.parentElement) {
        input.parentElement.classList.toggle('is-disabled', locked);
      }
    });
  }

  function setSaving(value) {
    saving = value;
    submitButton.disabled = value;
    if (value) {
      submitButton.setAttribute('aria-busy', 'true');
      submitButton.textContent = 'Creando…';
    } else {
      submitButton.removeAttribute('aria-busy');
      submitButton.textContent = 'Crear campaña';
    }
  }

  function showFormError(message, target) {
    formSuccess.hidden = true;
    formSuccess.textContent = '';
    formError.textContent = message;
    formError.hidden = false;
    if (target && typeof target.focus === 'function') target.focus();
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (saving) return;

    formError.hidden = true;
    formError.textContent = '';
    formSuccess.hidden = true;
    formSuccess.textContent = '';

    const title = titleInput.value.trim();
    const topic = topicInput.value.trim();
    const objective = objectiveInput.value.trim();
    const audience = audienceSelect.value;
    const tone = toneSelect.value;

    if (!title) { showFormError('Escribe el nombre de la campaña.', titleInput); return; }
    if (!topic) { showFormError('Escribe el tema de la campaña.', topicInput); return; }
    if (!objective) { showFormError('Escribe el objetivo de la campaña.', objectiveInput); return; }
    if (!audience) { showFormError('Selecciona una audiencia.', audienceSelect); return; }
    if (!tone) { showFormError('Selecciona un tono.', toneSelect); return; }

    const formats = formatInputs
      .filter(function (input) { return input.checked; })
      .map(function (input) { return input.value; });

    if (formats.length === 0) {
      showFormError('Selecciona al menos un formato.', formatInputs[0]);
      return;
    }

    const payload = {
      title: title,
      topic: topic,
      objective: objective,
      audience_segment: audience,
      tone: tone,
      formats: formats,
      academic_suite: suiteCheckbox.checked
    };

    setSaving(true);

    let result;
    try {
      result = await window.gwaApi('/api/campaigns', 'POST', payload);
    } catch (error) {
      setSaving(false);
      showFormError(errorMessage(error, 'No pudimos crear la campaña. Inténtalo de nuevo.'));
      return;
    }

    if (!result || typeof result.id !== 'string' || !result.id) {
      setSaving(false);
      showFormError('No recibimos un identificador válido de la campaña.');
      return;
    }

    window.gwaCampaignId = result.id;
    formSuccess.textContent = 'Campaña creada.';
    formSuccess.hidden = false;
    form.reset();
    syncAcademicSuite();
    await loadCatalog({ quiet: true });
    setSaving(false);
    window.gwaShowView('work');
  });

  suiteCheckbox.addEventListener('change', syncAcademicSuite);
  retryButton.addEventListener('click', function () {
    loadCatalog();
  });

  document.addEventListener('gwa:show', function (event) {
    if (event && event.detail === 'campaigns') {
      loadCatalog();
    }
  });

  syncAcademicSuite();
})();
</script>'''