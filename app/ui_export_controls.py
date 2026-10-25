def export_controls() -> str:
    return r"""<style>
#work-export-controls{box-sizing:border-box;width:100%;max-width:100%;min-width:0;display:flex;flex-direction:column;gap:8px;background:#fffef9;color:#173a35;font:inherit;overflow-wrap:anywhere}
#work-export-controls *{box-sizing:border-box;font:inherit}
#work-export-controls .gwa-export-row{display:flex;width:100%;min-width:0}
#work-export-controls .gwa-export-button{display:block;width:100%;min-height:44px;max-width:100%;padding:10px 16px;border:1px solid #215b48;border-radius:8px;background:#215b48;color:#fffef9;font:inherit;font-weight:700;line-height:1.2;white-space:normal;overflow-wrap:anywhere;cursor:pointer}
#work-export-controls .gwa-export-button:disabled{cursor:not-allowed;opacity:.55}
#work-export-controls .gwa-export-progress,#work-export-controls .gwa-export-error{max-width:100%;margin:0;padding:0 2px;color:#173a35;font:inherit;line-height:1.35;overflow-wrap:anywhere}
#work-export-controls [hidden]{display:none}
#work-exports{box-sizing:border-box;width:100%;max-width:100%;min-width:0;display:flex;flex-direction:column;gap:4px;background:#fffef9;color:#173a35;font:inherit;overflow-wrap:anywhere}
#work-exports a{display:block;max-width:100%;min-width:0;min-height:44px;padding:10px 2px;color:#215b48;font:inherit;line-height:1.3;overflow-wrap:anywhere;word-break:break-word}
</style>
<div id='work-export-controls' class='gwa-export-controls'>
  <div class='gwa-export-row'>
    <button type='button' class='gwa-export-button' disabled>Exportar materiales</button>
  </div>
  <p class='gwa-export-progress' role='status' aria-live='polite' hidden></p>
  <p class='gwa-export-error' role='alert' aria-live='assertive' hidden></p>
</div>
<script>
(function () {
  'use strict';
  var actions = document.getElementById('work-actions');
  if (!actions) return;
  var root = document.getElementById('work-export-controls');
  if (!root) {
    root = document.createElement('div');
    root.id = 'work-export-controls';
    root.className = 'gwa-export-controls';
  }
  if (root.getAttribute('data-gwa-export-ready') === '1') return;
  if (root.parentNode !== actions) actions.appendChild(root);
  var button = root.querySelector('.gwa-export-button');
  if (!button) {
    var row = document.createElement('div');
    row.className = 'gwa-export-row';
    button = document.createElement('button');
    button.type = 'button';
    button.className = 'gwa-export-button';
    row.appendChild(button);
    root.insertBefore(row, root.firstChild);
  }
  button.type = 'button';
  button.textContent = 'Exportar materiales';
  var progress = root.querySelector('.gwa-export-progress');
  if (!progress) {
    progress = document.createElement('p');
    progress.className = 'gwa-export-progress';
    root.appendChild(progress);
  }
  progress.setAttribute('role', 'status');
  progress.setAttribute('aria-live', 'polite');
  progress.textContent = '';
  progress.hidden = true;
  var error = root.querySelector('.gwa-export-error');
  if (!error) {
    error = document.createElement('p');
    error.className = 'gwa-export-error';
    root.appendChild(error);
  }
  error.setAttribute('role', 'alert');
  error.setAttribute('aria-live', 'assertive');
  error.textContent = '';
  error.hidden = true;
  var localBusy = false;
  var errorSource = null;
  var operationIds = Object.create(null);
  function ensureSnapshot() {
    var snap = window.gwaWorkSnapshot;
    if (!snap || typeof snap !== 'object') snap = { review: null, dirty: false, loading: false };
    if (!('review' in snap)) snap.review = null;
    if (!('dirty' in snap)) snap.dirty = false;
    if (!('loading' in snap)) snap.loading = false;
    if (typeof snap.dirty !== 'boolean') snap.dirty = !!snap.dirty;
    if (typeof snap.loading !== 'boolean') snap.loading = !!snap.loading;
    window.gwaWorkSnapshot = snap;
    return snap;
  }
  function hasApproval(review) {
    return !!review && !!review.approval && typeof review.approval === 'object' && typeof review.approval.id === 'string' && review.approval.id.length > 0;
  }
  function hasBundle(review) {
    return !!review && !!review.bundle && !!review.bundle.run && Array.isArray(review.bundle.versions) && review.bundle.versions.length > 0;
  }
  function sameRevision(review) {
    var campaign = review && review.campaign;
    var run = review && review.bundle && review.bundle.run;
    if (!campaign || !run || campaign.config_revision === undefined || campaign.config_revision === null || run.config_revision === undefined || run.config_revision === null) return false;
    return String(campaign.config_revision) === String(run.config_revision);
  }
  function canExport() {
    var snap = ensureSnapshot();
    var review = snap.review;
    if (!review || snap.loading || snap.dirty) return false;
    if (localBusy || window.gwaWorkActionBusy) return false;
    return hasApproval(review) && hasBundle(review) && sameRevision(review);
  }
  function renderButton() {
    var allowed = canExport();
    button.disabled = !allowed;
    button.setAttribute('aria-disabled', allowed ? 'false' : 'true');
  }
  function showError(message, source) {
    error.textContent = message;
    error.hidden = false;
    errorSource = source || 'general';
  }
  function clearError(source) {
    if (source && errorSource !== source) return;
    error.textContent = '';
    error.hidden = true;
    errorSource = null;
  }
  function setProgress(message) {
    var text = typeof message === 'string' ? message : '';
    progress.textContent = text;
    progress.hidden = text.length === 0;
  }
  function basename(path) {
    var index = path.lastIndexOf('/');
    return index >= 0 ? path.slice(index + 1) : path;
  }
  function renderDownloads() {
    var host = document.getElementById('work-exports');
    if (!host) return;
    host.textContent = '';
    var snap = ensureSnapshot();
    var review = snap.review;
    var rows = review && Array.isArray(review.exports) ? review.exports : [];
    var malformed = false;
    for (var i = 0; i < rows.length; i += 1) {
      var row = rows[i];
      if (!row || typeof row !== 'object' || typeof row.id !== 'string' || row.id.length === 0) {
        malformed = true;
        continue;
      }
      var files;
      try {
        files = typeof row.files_manifest_json === 'string' ? JSON.parse(row.files_manifest_json) : row.files_manifest_json;
      } catch (parseError) {
        malformed = true;
        continue;
      }
      if (!Array.isArray(files)) {
        malformed = true;
        continue;
      }
      for (var j = 0; j < files.length; j += 1) {
        var file = files[j];
        if (!file || typeof file !== 'object' || typeof file.relative_path !== 'string' || file.relative_path.length === 0 || typeof file.sha256 !== 'string' || file.sha256.length === 0) {
          malformed = true;
          continue;
        }
        var label = basename(file.relative_path);
        if (!label) {
          malformed = true;
          continue;
        }
        var link = document.createElement('a');
        link.setAttribute('href', '/api/exports/' + encodeURIComponent(row.id) + '/files/' + j);
        link.textContent = label;
        host.appendChild(link);
      }
    }
    if (malformed) {
      showError('Algunos archivos exportados no se pudieron mostrar.', 'downloads');
    } else {
      clearError('downloads');
    }
  }
  function renderAll() {
    renderButton();
    renderDownloads();
  }
  function operationFor(approvalId) {
    if (!Object.prototype.hasOwnProperty.call(operationIds, approvalId)) {
      operationIds[approvalId] = window.crypto.randomUUID();
    }
    return operationIds[approvalId];
  }
  function runExport(approvalId) {
    var operationId;
    try {
      operationId = operationFor(approvalId);
    } catch (operationError) {
      showError('No se pudo iniciar la exportación.', 'export');
      return;
    }
    localBusy = true;
    window.gwaWorkActionBusy = true;
    clearError();
    setProgress('Exportando materiales...');
    renderButton();
    (async function () {
      try {
        await window.gwaApi('/api/approvals/' + encodeURIComponent(approvalId) + '/exports', 'POST', { operation_id: operationId });
        window.gwaWorkActionBusy = false;
        setProgress('Exportación completada. Actualizando...');
        try {
          await window.gwaReloadWork();
        } catch (reloadError) {
          showError('La exportación se completó, pero no se pudo actualizar la vista.', 'export');
        }
        setProgress('');
      } catch (exportError) {
        window.gwaWorkActionBusy = false;
        setProgress('');
        showError('No se pudo exportar. Inténtalo de nuevo.', 'export');
      } finally {
        localBusy = false;
        renderAll();
      }
    })();
  }
  button.addEventListener('click', function () {
    if (localBusy || window.gwaWorkActionBusy) return;
    var snap = ensureSnapshot();
    var review = snap.review;
    if (!canExport() || !hasApproval(review)) return;
    runExport(review.approval.id);
  });
  document.addEventListener('gwa:review', function (event) {
    var detail = event ? event.detail : null;
    var snap = ensureSnapshot();
    if (detail === null) {
      snap.review = null;
    } else if (detail && typeof detail === 'object') {
      if (Object.prototype.hasOwnProperty.call(detail, 'review')) {
        snap.review = detail.review;
        if (Object.prototype.hasOwnProperty.call(detail, 'dirty')) snap.dirty = !!detail.dirty;
        if (Object.prototype.hasOwnProperty.call(detail, 'loading')) snap.loading = !!detail.loading;
      } else if (detail.campaign !== undefined || detail.bundle !== undefined || detail.approval !== undefined || detail.exports !== undefined) {
        snap.review = detail;
      } else {
        if (Object.prototype.hasOwnProperty.call(detail, 'dirty')) snap.dirty = !!detail.dirty;
        if (Object.prototype.hasOwnProperty.call(detail, 'loading')) snap.loading = !!detail.loading;
      }
    }
    ensureSnapshot();
    renderAll();
  });
  ensureSnapshot();
  renderAll();
  root.setAttribute('data-gwa-export-ready', '1');
})();
</script>"""
