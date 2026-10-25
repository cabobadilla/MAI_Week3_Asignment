def directed_record_controls() -> str:
    return r'''<form id='gwa-directed-record-form' class='gwa-dr-form' novalidate>
<style>
#directed-record-controls,
#directed-record-controls * {
  box-sizing: border-box;
}
#directed-record-controls {
  color: #173a35;
  font: inherit;
  max-width: 100%;
  min-width: 0;
}
#directed-record-controls [hidden] {
  display: none !important;
}
#directed-record-controls .gwa-dr-form {
  display: grid;
  gap: 16px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  margin: 0;
  padding: 16px;
  background: #fffef9;
  color: #173a35;
  border: 1px solid #dce3d5;
  border-radius: 12px;
  font: inherit;
  overflow: hidden;
}
#directed-record-controls .gwa-dr-field {
  display: grid;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
}
#directed-record-controls .gwa-dr-label,
#directed-record-controls label {
  color: #173a35;
  font: inherit;
  font-weight: 700;
  line-height: 1.35;
}
#directed-record-controls select,
#directed-record-controls input[type='datetime-local'],
#directed-record-controls input[type='text'] {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid #dce3d5;
  border-radius: 8px;
  background: #fffef9;
  color: #173a35;
  font: inherit;
}
#directed-record-controls select:focus,
#directed-record-controls input:focus,
#directed-record-controls button:focus,
#directed-record-controls input[type='checkbox']:focus {
  outline: 2px solid #215b48;
  outline-offset: 2px;
}
#directed-record-controls .gwa-dr-body {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 64px;
  max-height: 240px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  border: 1px solid #dce3d5;
  border-radius: 8px;
  background: #fffef9;
  color: #173a35;
  font: inherit;
  line-height: 1.5;
}
#directed-record-controls .gwa-dr-check {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  max-width: 100%;
  min-height: 44px;
  padding: 8px 0;
  color: #173a35;
  font: inherit;
  font-weight: 400;
  line-height: 1.4;
  cursor: pointer;
}
#directed-record-controls .gwa-dr-check input {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  margin: 2px 0 0;
  accent-color: #215b48;
}
#directed-record-controls .gwa-dr-submit {
  width: 100%;
  max-width: 100%;
  min-height: 44px;
  padding: 10px 16px;
  border: 1px solid #215b48;
  border-radius: 8px;
  background: #215b48;
  color: #fffef9;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
#directed-record-controls .gwa-dr-submit:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
#directed-record-controls .gwa-dr-status,
#directed-record-controls .gwa-dr-error {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid #dce3d5;
  border-radius: 8px;
  background: #fffef9;
  color: #173a35;
  font: inherit;
  font-size: 0.9rem;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
#directed-record-controls .gwa-dr-error {
  font-weight: 700;
  border-left: 4px solid #215b48;
}
@media (max-width: 420px) {
  #directed-record-controls .gwa-dr-form {
    padding: 14px;
    gap: 14px;
  }
}
</style>
<div class='gwa-dr-field'>
<label for='gwa-dr-version'>Versión del email</label>
<select id='gwa-dr-version' name='version' required>
<option value='' selected disabled>Selecciona una versión</option>
</select>
</div>
<div class='gwa-dr-field'>
<span class='gwa-dr-label' id='gwa-dr-body-label'>Cuerpo del email</span>
<pre id='gwa-dr-body' class='gwa-dr-body' aria-labelledby='gwa-dr-body-label'></pre>
</div>
<div class='gwa-dr-field'>
<label for='gwa-dr-date'>Fecha del envío externo</label>
<input id='gwa-dr-date' name='occurred_at' type='datetime-local' required autocomplete='off'>
</div>
<div class='gwa-dr-field'>
<label for='gwa-dr-reason'>Motivo de repetición</label>
<input id='gwa-dr-reason' name='repeat_reason' type='text' placeholder='Opcional' autocomplete='off'>
</div>
<label class='gwa-dr-check' for='gwa-dr-confirm'>
<input id='gwa-dr-confirm' name='confirmed' type='checkbox' required>
<span>Confirmo que este correo se envió fuera de la app</span>
</label>
<button id='gwa-dr-submit' class='gwa-dr-submit' type='submit' disabled>Registrar envío externo</button>
<p id='gwa-dr-status' class='gwa-dr-status' role='status' aria-live='polite'>Este registro es manual: no envía ningún correo desde la app.</p>
<p id='gwa-dr-error' class='gwa-dr-error' role='alert' aria-live='assertive' hidden></p>
<script>
(function () {
  'use strict';
  var host = document.getElementById('directed-record-controls');
  if (!host) {
    return;
  }
  var form = document.getElementById('gwa-directed-record-form');
  if (!form) {
    return;
  }
  if (form.parentNode !== host) {
    host.appendChild(form);
  }
  if (form.getAttribute('data-gwa-dr-ready') === '1') {
    return;
  }
  form.setAttribute('data-gwa-dr-ready', '1');
  var select = form.querySelector('#gwa-dr-version');
  var bodyPreview = form.querySelector('#gwa-dr-body');
  var dateInput = form.querySelector('#gwa-dr-date');
  var reasonInput = form.querySelector('#gwa-dr-reason');
  var confirmInput = form.querySelector('#gwa-dr-confirm');
  var submitButton = form.querySelector('#gwa-dr-submit');
  var statusBox = form.querySelector('#gwa-dr-status');
  var errorBox = form.querySelector('#gwa-dr-error');
  if (!select || !bodyPreview || !dateInput || !reasonInput || !confirmInput || !submitButton || !statusBox || !errorBox) {
    return;
  }
  var snapshot = window.gwaDirectedSnapshot || {};
  var localBusy = false;
  var pendingFingerprint = '';
  var pendingOperationId = '';

  function resetPending() {
    pendingFingerprint = '';
    pendingOperationId = '';
  }

  function currentCampaignId() {
    if (!snapshot || snapshot.campaignId === null || snapshot.campaignId === undefined) {
      return '';
    }
    return String(snapshot.campaignId);
  }

  function allVersions() {
    return snapshot && Array.isArray(snapshot.versions) ? snapshot.versions : [];
  }

  function preparedRecipients() {
    return snapshot && Array.isArray(snapshot.preparedRecipients) ? snapshot.preparedRecipients : [];
  }

  function selectedVersion() {
    var value = select.value;
    if (value === '') {
      return null;
    }
    var versions = allVersions();
    var index;
    for (index = 0; index < versions.length; index += 1) {
      var version = versions[index];
      if (version && version.id !== null && version.id !== undefined && String(version.id) === value) {
        return version;
      }
    }
    return null;
  }

  function dateIsValid() {
    var value = dateInput.value;
    if (!value) {
      return false;
    }
    return !Number.isNaN(new Date(value).getTime());
  }

  function globalBusy() {
    return !!window.gwaDirectedActionBusy;
  }

  function refreshSubmit() {
    var campaignId = currentCampaignId();
    var version = selectedVersion();
    var recipients = preparedRecipients();
    var snapshotBusy = !!(snapshot && snapshot.busy);
    submitButton.disabled = !!(
      localBusy ||
      globalBusy() ||
      snapshotBusy ||
      !campaignId ||
      !version ||
      recipients.length === 0 ||
      !confirmInput.checked ||
      !dateIsValid()
    );
    form.setAttribute('aria-busy', localBusy ? 'true' : 'false');
  }

  function updateBody() {
    var version = selectedVersion();
    bodyPreview.textContent = version && version.body !== null && version.body !== undefined ? String(version.body) : '';
  }

  function versionLabel(version) {
    var parts = [];
    if (version.revision_no !== null && version.revision_no !== undefined) {
      parts.push('Revisión ' + String(version.revision_no));
    }
    if (version.format) {
      parts.push(String(version.format));
    }
    if (version.variant) {
      parts.push(String(version.variant));
    }
    if (parts.length === 0) {
      parts.push('Versión ' + String(version.id));
    }
    return parts.join(' · ');
  }

  function render() {
    var previousValue = select.value;
    while (select.firstChild) {
      select.removeChild(select.firstChild);
    }
    var placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Selecciona una versión';
    placeholder.disabled = true;
    select.appendChild(placeholder);
    var versions = allVersions();
    var fragment = document.createDocumentFragment();
    var index;
    var selectedStillExists = false;
    for (index = 0; index < versions.length; index += 1) {
      var version = versions[index];
      if (!version || version.id === null || version.id === undefined) {
        continue;
      }
      var option = document.createElement('option');
      var value = String(version.id);
      option.value = value;
      option.textContent = versionLabel(version);
      if (value === previousValue) {
        selectedStillExists = true;
      }
      fragment.appendChild(option);
    }
    select.appendChild(fragment);
    if (selectedStillExists) {
      select.value = previousValue;
    } else {
      select.value = '';
    }
    updateBody();
    refreshSubmit();
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function hideError() {
    errorBox.textContent = '';
    errorBox.hidden = true;
  }

  function onVersionChange() {
    confirmInput.checked = false;
    resetPending();
    hideError();
    statusBox.textContent = 'Este registro es manual: no envía ningún correo desde la app.';
    updateBody();
    refreshSubmit();
  }

  function onDateChange() {
    resetPending();
    refreshSubmit();
  }

  function onReasonChange() {
    resetPending();
  }

  function onConfirmChange() {
    refreshSubmit();
  }

  select.addEventListener('change', onVersionChange);
  dateInput.addEventListener('input', onDateChange);
  dateInput.addEventListener('change', onDateChange);
  reasonInput.addEventListener('input', onReasonChange);
  reasonInput.addEventListener('change', onReasonChange);
  confirmInput.addEventListener('change', onConfirmChange);

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    hideError();
    if (localBusy || globalBusy() || (snapshot && snapshot.busy)) {
      return;
    }
    var campaignId = currentCampaignId();
    var version = selectedVersion();
    var recipients = preparedRecipients();
    if (!campaignId || !version || recipients.length === 0 || !confirmInput.checked || !dateIsValid()) {
      refreshSubmit();
      return;
    }
    var occurredAt;
    try {
      occurredAt = new Date(dateInput.value).toISOString();
    } catch (error) {
      refreshSubmit();
      return;
    }
    var rawReason = reasonInput.value;
    var repeatReason = rawReason.trim() === '' ? null : rawReason.trim();
    var recipientIds = recipients.map(function (recipient) {
      return recipient.id;
    });
    var fingerprint = JSON.stringify({
      campaign_id: campaignId,
      version_id: version.id,
      recipient_ids: recipientIds.slice().sort(),
      occurred_at: occurredAt,
      repeat_reason: repeatReason
    });
    var operationId = pendingOperationId;
    if (!operationId || fingerprint !== pendingFingerprint) {
      operationId = crypto.randomUUID();
      pendingFingerprint = fingerprint;
      pendingOperationId = operationId;
    }
    var payload = {
      version_id: version.id,
      recipient_ids: recipientIds,
      occurred_at: occurredAt,
      operation_id: operationId,
      confirmed: true,
      repeat_reason: repeatReason
    };
    localBusy = true;
    window.gwaDirectedActionBusy = true;
    refreshSubmit();
    try {
      await window.gwaApi('/api/campaigns/' + encodeURIComponent(campaignId) + '/directed', 'POST', payload);
      pendingFingerprint = '';
      pendingOperationId = '';
      window.gwaDirectedActionBusy = false;
      confirmInput.checked = false;
      statusBox.textContent = 'Envío externo registrado. La app no envió este correo.';
      if (typeof window.gwaReloadDirected === 'function') {
        try {
          await window.gwaReloadDirected();
        } catch (reloadError) {
        }
      }
    } catch (error) {
      showError('No se pudo registrar el envío externo. Inténtalo de nuevo.');
    } finally {
      localBusy = false;
      if (window.gwaDirectedActionBusy) {
        window.gwaDirectedActionBusy = false;
      }
      refreshSubmit();
    }
  });

  document.addEventListener('gwa:directed', function (event) {
    var previousCampaignId = currentCampaignId();
    var previousPreparedIds = preparedRecipients().map(function (recipient) {
      return recipient.id;
    }).sort();
    snapshot = event.detail || {};
    var nextCampaignId = currentCampaignId();
    var nextPreparedIds = preparedRecipients().map(function (recipient) {
      return recipient.id;
    }).sort();
    if (previousCampaignId !== nextCampaignId) {
      select.value = '';
      dateInput.value = '';
      reasonInput.value = '';
      confirmInput.checked = false;
      resetPending();
      hideError();
      statusBox.textContent = 'Este registro es manual: no envía ningún correo desde la app.';
    } else if (JSON.stringify(previousPreparedIds) !== JSON.stringify(nextPreparedIds)) {
      confirmInput.checked = false;
      resetPending();
      hideError();
    }
    render();
  });

  render();
})();
</script>
</form>'''