def approval_controls() -> str:
    return r'''<style>
#work-approval-controls {
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  margin: 12px 0;
  padding: 12px;
  border: 1px solid #dce3d5;
  border-radius: 8px;
  background: #fffef9;
  color: #173a35;
  font: inherit;
  overflow-wrap: anywhere;
}
#work-approval-controls *,
#work-approval-controls *::before,
#work-approval-controls *::after {
  box-sizing: border-box;
}
#work-approval-controls .gwa-approval-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0 0 10px;
  font: inherit;
  line-height: 1.35;
}
#work-approval-controls .gwa-approval-label input {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  margin: 2px 0 0;
  accent-color: #215b48;
}
#work-approval-controls .gwa-approval-label span {
  min-width: 0;
}
#work-approval-controls button {
  display: block;
  width: 100%;
  max-width: 100%;
  min-height: 44px;
  padding: 10px 14px;
  border: 1px solid #215b48;
  border-radius: 6px;
  background: #215b48;
  color: #fffef9;
  font: inherit;
  font-weight: 600;
  line-height: 1.2;
  cursor: pointer;
}
#work-approval-controls button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
#work-approval-controls p {
  margin: 8px 0 0;
  font: inherit;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
#work-approval-controls p:empty {
  display: none;
}
#work-approval-controls .gwa-approval-alert {
  color: #8a1f1f;
}
@media (max-width: 400px) {
  #work-approval-controls {
    padding: 10px;
  }
}
</style>
<div id="work-approval-controls" class="gwa-approval" aria-label="Aprobación de materiales">
  <label class="gwa-approval-label" for="gwa-approval-confirm">
    <input id="gwa-approval-confirm" type="checkbox">
    <span>Confirmo que revisé las piezas y las fuentes de demostración</span>
  </label>
  <button id="gwa-approval-submit" type="button" disabled>Aprobar materiales</button>
  <p id="gwa-approval-status" class="gwa-approval-status" role="status" aria-live="polite"></p>
  <p id="gwa-approval-alert" class="gwa-approval-alert" role="alert" aria-live="assertive"></p>
</div>
<script>
(() => {
  'use strict';
  const CONFIRM_TEXT = 'Confirmo que revisé las piezas y las fuentes de demostración';
  const BUTTON_TEXT = 'Aprobar materiales';
  const GENERIC_ERROR = 'No se pudo aprobar. Revisa la conexión e inténtalo de nuevo.';
  const EMPTY_SNAPSHOT = { review: null, dirty: false, loading: false };

  let snapshot = (window.gwaWorkSnapshot && typeof window.gwaWorkSnapshot === 'object')
    ? window.gwaWorkSnapshot
    : EMPTY_SNAPSHOT;
  let lastIdentity = bundleIdentity(snapshot);
  let busy = false;
  let mounted = false;
  let checkbox = null;
  let button = null;
  let statusNode = null;
  let alertNode = null;

  function bundleIdentity(value) {
    const review = value && typeof value === 'object' ? value.review : null;
    const bundle = review && typeof review === 'object' ? review.bundle : null;
    const run = bundle && typeof bundle === 'object' ? bundle.run : null;
    if (!bundle || !run) return '';
    const versions = Array.isArray(bundle.versions) ? bundle.versions : [];
    const versionIds = versions.map(function (version) {
      return version && version.id !== undefined && version.id !== null ? String(version.id) : '';
    });
    return JSON.stringify([
      run.id === undefined || run.id === null ? '' : String(run.id),
      versionIds,
      bundle.source_hash === undefined || bundle.source_hash === null ? '' : String(bundle.source_hash),
      bundle.context_hash === undefined || bundle.context_hash === null ? '' : String(bundle.context_hash)
    ]);
  }

  function currentView() {
    const source = snapshot && typeof snapshot === 'object' ? snapshot : EMPTY_SNAPSHOT;
    const review = source.review && typeof source.review === 'object' ? source.review : null;
    const campaign = review && review.campaign && typeof review.campaign === 'object' ? review.campaign : null;
    const bundle = review && review.bundle && typeof review.bundle === 'object' ? review.bundle : null;
    const run = bundle && bundle.run && typeof bundle.run === 'object' ? bundle.run : null;
    const versions = bundle && Array.isArray(bundle.versions) ? bundle.versions : [];
    const approval = review && review.approval && typeof review.approval === 'object' ? review.approval : null;
    return {
      review: review,
      campaign: campaign,
      bundle: bundle,
      run: run,
      versions: versions,
      approval: approval,
      dirty: source.dirty === true,
      loading: source.loading === true
    };
  }

  function statusAllowsApproval(run) {
    return !!run && (run.status === 'needs_review' || run.status === 'finished');
  }

  function isStale(view) {
    return !!(view.campaign && view.run && view.campaign.config_revision !== view.run.config_revision);
  }

  function versionsReady(versions) {
    if (!Array.isArray(versions) || versions.length === 0) return false;
    for (let index = 0; index < versions.length; index += 1) {
      const version = versions[index];
      if (!version || version.id === undefined || version.id === null || String(version.id) === '') {
        return false;
      }
    }
    return true;
  }

  function canSubmit(view) {
    if (!mounted || !checkbox || !checkbox.checked || busy) return false;
    if (view.approval) return false;
    if (!view.review || !view.campaign || !view.bundle || !view.run) return false;
    if (!versionsReady(view.versions)) return false;
    if (!statusAllowsApproval(view.run)) return false;
    if (view.dirty || view.loading) return false;
    if (isStale(view)) return false;
    if (view.campaign.id === undefined || view.campaign.id === null || String(view.campaign.id) === '') return false;
    if (view.run.id === undefined || view.run.id === null || String(view.run.id) === '') return false;
    if (window.gwaWorkActionBusy === true) return false;
    return true;
  }

  function render() {
    if (!mounted || !checkbox || !button || !statusNode) return;
    const view = currentView();
    if (view.approval) {
      const actor = view.approval.actor === undefined || view.approval.actor === null ? '' : String(view.approval.actor);
      const approvedAt = view.approval.approved_at === undefined || view.approval.approved_at === null ? '' : String(view.approval.approved_at);
      let message = 'Materiales aprobados.';
      if (actor) message += ' Por: ' + actor + '.';
      if (approvedAt) message += ' Fecha: ' + approvedAt + '.';
      statusNode.textContent = message;
    } else if (busy) {
      statusNode.textContent = 'Enviando aprobación de materiales.';
    } else if (!view.review || !view.bundle || !view.run) {
      statusNode.textContent = 'Sin materiales para revisar.';
    } else if (view.versions.length === 0) {
      statusNode.textContent = 'No hay versiones para aprobar.';
    } else if (view.dirty) {
      statusNode.textContent = 'Hay cambios sin guardar.';
    } else if (view.loading) {
      statusNode.textContent = 'Cargando materiales de demostración.';
    } else if (isStale(view)) {
      statusNode.textContent = 'La revisión está desactualizada. Recarga los materiales.';
    } else if (statusAllowsApproval(view.run)) {
      statusNode.textContent = 'DEMO: revisa y confirma las piezas antes de aprobar.';
    } else {
      statusNode.textContent = 'El estado de la revisión no permite aprobar.';
    }
    button.disabled = !canSubmit(view);
  }

  async function onApprove() {
    if (busy || !mounted || !button || button.disabled) {
      render();
      return;
    }
    const view = currentView();
    if (!canSubmit(view) || window.gwaWorkActionBusy === true) {
      render();
      return;
    }
    const campaignId = view.campaign.id;
    const runId = view.run.id;
    const versionIds = view.versions.map(function (version) {
      return version.id;
    });
    const payload = Object.freeze({
      run_id: runId,
      version_ids: Object.freeze(versionIds),
      confirmed: true
    });

    busy = true;
    window.gwaWorkActionBusy = true;
    if (alertNode) alertNode.textContent = '';
    render();

    try {
      await window.gwaApi(
        '/api/campaigns/' + encodeURIComponent(campaignId) + '/approvals',
        'POST',
        payload
      );
      window.gwaWorkActionBusy = false;
      await window.gwaReloadWork();
    } catch (error) {
      window.gwaWorkActionBusy = false;
      if (alertNode) alertNode.textContent = GENERIC_ERROR;
    } finally {
      busy = false;
      render();
    }
  }

  function applySnapshot(next) {
    if (!next || typeof next !== 'object') return;
    const identity = bundleIdentity(next);
    if (identity !== lastIdentity) {
      lastIdentity = identity;
      if (checkbox) checkbox.checked = false;
      if (alertNode) alertNode.textContent = '';
    }
    snapshot = next;
    if (!mounted) mount();
    render();
  }

  function mount() {
    if (mounted) return true;
    const host = document.getElementById('work-actions');
    if (!host) return false;

    let component = document.getElementById('work-approval-controls');
    if (!component) {
      component = document.createElement('div');
      component.id = 'work-approval-controls';
    }
    if (component.parentNode !== host) host.appendChild(component);
    while (component.firstChild) component.removeChild(component.firstChild);
    component.className = 'gwa-approval';
    component.setAttribute('aria-label', 'Aprobación de materiales');

    const label = document.createElement('label');
    label.className = 'gwa-approval-label';
    label.setAttribute('for', 'gwa-approval-confirm');

    checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = 'gwa-approval-confirm';
    checkbox.checked = false;

    const confirmText = document.createElement('span');
    confirmText.textContent = CONFIRM_TEXT;

    label.appendChild(checkbox);
    label.appendChild(confirmText);

    button = document.createElement('button');
    button.type = 'button';
    button.id = 'gwa-approval-submit';
    button.textContent = BUTTON_TEXT;
    button.disabled = true;

    statusNode = document.createElement('p');
    statusNode.id = 'gwa-approval-status';
    statusNode.className = 'gwa-approval-status';
    statusNode.setAttribute('role', 'status');
    statusNode.setAttribute('aria-live', 'polite');

    alertNode = document.createElement('p');
    alertNode.id = 'gwa-approval-alert';
    alertNode.className = 'gwa-approval-alert';
    alertNode.setAttribute('role', 'alert');
    alertNode.setAttribute('aria-live', 'assertive');

    component.appendChild(label);
    component.appendChild(button);
    component.appendChild(statusNode);
    component.appendChild(alertNode);

    checkbox.addEventListener('change', render);
    button.addEventListener('click', onApprove);

    mounted = true;
    render();
    return true;
  }

  document.addEventListener('gwa:review', function (event) {
    applySnapshot(event ? event.detail : null);
  });

  if (!mount() && document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount, { once: true });
  }
})();
</script>'''