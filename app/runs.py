import json
import math
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
_STATUSES = (
    'prepared',
    'running',
    'waiting_input',
    'needs_review',
    'finished',
    'failed',
    'cancelled',
)
_ALLOWED = {
    'prepared': frozenset(('running', 'cancelled', 'failed')),
    'running': frozenset(('waiting_input', 'needs_review', 'finished', 'failed', 'cancelled')),
    'waiting_input': frozenset(('running', 'failed', 'cancelled')),
    'needs_review': frozenset(('running', 'finished', 'failed', 'cancelled')),
    'failed': frozenset(('running', 'cancelled')),
    'finished': frozenset(),
    'cancelled': frozenset(),
}
_RUN_COLUMNS = (
    'id',
    'campaign_id',
    'status',
    'step',
    'config_revision',
    'config_json',
    'sources_json',
    'context_json',
    'metrics_json',
    'error_json',
    'created_at',
    'updated_at',
)
_CAMPAIGN_COLUMNS = (
    'id',
    'title',
    'topic',
    'objective',
    'audience_segment',
    'tone',
    'formats_json',
    'config_revision',
    'archived_at',
)
_RUN_SELECT = 'SELECT ' + ', '.join(_RUN_COLUMNS) + ' FROM generation_run'
_CAMPAIGN_SELECT = 'SELECT ' + ', '.join(_CAMPAIGN_COLUMNS) + ' FROM campaign'
_MAX_SNAPSHOT_BYTES = 100 * 1024
_CREDENTIAL_MARKERS = ('apikey', 'authorization', 'secret', 'accesstoken', 'password', 'credential')
def _utcnow():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
def _dumps(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
def _row_to_dict(row, columns):
    if row is None:
        return None
    if hasattr(row, 'keys'):
        return {name: row[name] for name in columns}
    return dict(zip(columns, row))
def _decode_run(row):
    data = _row_to_dict(row, _RUN_COLUMNS)
    if data is None:
        raise ValueError('generation run not found')
    try:
        config = json.loads(data['config_json'])
        sources = json.loads(data['sources_json'])
        context = json.loads(data['context_json'])
        metrics = json.loads(data['metrics_json'])
        error = None if data['error_json'] is None else json.loads(data['error_json'])
    except Exception:
        raise ValueError('generation run unavailable') from None
    if not isinstance(config, dict):
        raise ValueError('generation run unavailable')
    if not isinstance(sources, list):
        raise ValueError('generation run unavailable')
    if not isinstance(context, dict):
        raise ValueError('generation run unavailable')
    if not isinstance(metrics, dict):
        raise ValueError('generation run unavailable')
    data['config'] = config
    data['sources'] = sources
    data['context'] = context
    data['metrics'] = metrics
    data['error'] = error
    return data
def _fetch_run(conn, run_id):
    return conn.execute(_RUN_SELECT + ' WHERE id = ?', (run_id,)).fetchone()
def _fetch_campaign(conn, campaign_id):
    return conn.execute(_CAMPAIGN_SELECT + ' WHERE id = ?', (campaign_id,)).fetchone()
def _formats(value):
    try:
        parsed = json.loads(value)
    except Exception:
        raise ValueError('campaign brief is unavailable') from None
    if not isinstance(parsed, list):
        raise ValueError('campaign brief is unavailable')
    return parsed
def _campaign_config(row):
    data = _row_to_dict(row, _CAMPAIGN_COLUMNS)
    if data is None:
        raise ValueError('campaign brief is unavailable')
    return {
        'title': data['title'],
        'topic': data['topic'],
        'objective': data['objective'],
        'segment': data['audience_segment'],
        'tone': data['tone'],
        'formats': _formats(data['formats_json']),
        'config_revision': data['config_revision'],
    }
def _uuid4(value):
    if not isinstance(value, str):
        raise ValueError('invalid run id')
    try:
        parsed = uuid.UUID(value)
    except Exception:
        raise ValueError('invalid run id') from None
    if parsed.version != 4 or str(parsed) != value:
        raise ValueError('invalid run id')
    return value
def _status(value):
    if value not in _STATUSES:
        raise ValueError('invalid run status')
    return value
def _step(value):
    if not isinstance(value, str):
        raise ValueError('invalid step')
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 80:
        raise ValueError('invalid step')
    return cleaned
def _check_key(key):
    compact = ''.join(character for character in key.lower() if character.isalnum())
    for marker in _CREDENTIAL_MARKERS:
        if marker in compact:
            raise ValueError('snapshot contains credentials')
def _validate_json_value(value, seen):
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('snapshot must be JSON data')
        return
    if isinstance(value, list):
        marker = id(value)
        if marker in seen:
            raise ValueError('snapshot must be JSON data')
        seen.add(marker)
        try:
            for item in value:
                _validate_json_value(item, seen)
        finally:
            seen.discard(marker)
        return
    if isinstance(value, dict):
        marker = id(value)
        if marker in seen:
            raise ValueError('snapshot must be JSON data')
        seen.add(marker)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError('snapshot must be JSON data')
                _check_key(key)
                _validate_json_value(item, seen)
        finally:
            seen.discard(marker)
        return
    raise ValueError('snapshot must be JSON data')
def _prepare_snapshots(sources, context):
    if not isinstance(sources, list):
        raise ValueError('sources must be a list')
    if not isinstance(context, dict):
        raise ValueError('context must be a dict')
    seen = set()
    _validate_json_value(sources, seen)
    _validate_json_value(context, seen)
    try:
        sources_json = _dumps(sources)
        context_json = _dumps(context)
    except Exception:
        raise ValueError('snapshot must be JSON data') from None
    combined = len(sources_json.encode('utf-8')) + len(context_json.encode('utf-8'))
    if combined > _MAX_SNAPSHOT_BYTES:
        raise ValueError('snapshot is too large')
    return sources_json, context_json
@contextmanager
def _atomic(conn):
    if getattr(conn, 'in_transaction', False):
        name = 'run_sp_' + uuid.uuid4().hex
        conn.execute('SAVEPOINT ' + name)
        try:
            yield
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT ' + name)
            finally:
                conn.execute('RELEASE SAVEPOINT ' + name)
            raise
        else:
            conn.execute('RELEASE SAVEPOINT ' + name)
    else:
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            conn.execute('ROLLBACK')
            raise
        else:
            conn.execute('COMMIT')
def create_run(conn, campaign_id, *, run_id=None):
    try:
        if run_id is not None:
            run_id = _uuid4(run_id)
        with _atomic(conn):
            campaign_row = _fetch_campaign(conn, campaign_id)
            campaign = _row_to_dict(campaign_row, _CAMPAIGN_COLUMNS)
            if campaign is None or campaign['archived_at'] is not None:
                raise ValueError('campaign is not active')
            revision = campaign['config_revision']
            if run_id is not None:
                existing_row = _fetch_run(conn, run_id)
                if existing_row is not None:
                    existing = _row_to_dict(existing_row, _RUN_COLUMNS)
                    if existing['campaign_id'] != campaign_id:
                        raise ValueError('run id collision')
                    if existing['config_revision'] != revision:
                        raise ValueError('campaign brief has changed')
                    return _decode_run(existing_row)
            config_json = _dumps(_campaign_config(campaign_row))
            now = _utcnow()
            if run_id is None:
                generated = None
                for _ in range(10):
                    candidate = str(uuid.uuid4())
                    if _fetch_run(conn, candidate) is None:
                        generated = candidate
                        break
                if generated is None:
                    raise ValueError('generation run unavailable')
                run_id = generated
            conn.execute(
                'INSERT INTO generation_run (id, campaign_id, status, step, config_revision, config_json, sources_json, context_json, metrics_json, error_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    run_id,
                    campaign_id,
                    'prepared',
                    'prepared',
                    revision,
                    config_json,
                    _dumps([]),
                    _dumps({}),
                    _dumps({'attempts': 0}),
                    None,
                    now,
                    now,
                ),
            )
            inserted = _fetch_run(conn, run_id)
            if inserted is None:
                raise ValueError('generation run unavailable')
            return _decode_run(inserted)
    except ValueError:
        raise
    except Exception:
        raise ValueError('generation run unavailable') from None
def get_run(conn, id):
    try:
        row = _fetch_run(conn, id)
        if row is None:
            raise ValueError('generation run not found')
        return _decode_run(row)
    except ValueError:
        raise
    except Exception:
        raise ValueError('generation run unavailable') from None
def list_runs(conn, campaign_id):
    try:
        rows = conn.execute(
            _RUN_SELECT + ' WHERE campaign_id = ? ORDER BY created_at DESC, id DESC',
            (campaign_id,),
        ).fetchall()
        return [_decode_run(row) for row in rows]
    except ValueError:
        raise
    except Exception:
        raise ValueError('generation run unavailable') from None
def transition_run(conn, id, new_status, step, *, expected_status=None):
    try:
        new_status = _status(new_status)
        step = _step(step)
        if expected_status is not None:
            expected_status = _status(expected_status)
        with _atomic(conn):
            row = _fetch_run(conn, id)
            if row is None:
                raise ValueError('generation run not found')
            current = _decode_run(row)
            current_status = current['status']
            current_step = current['step']
            if current_status == new_status and current_step == step:
                return current
            if expected_status is not None and current_status != expected_status:
                raise ValueError('generation run changed')
            allowed = _ALLOWED.get(current_status)
            if allowed is None or new_status not in allowed:
                raise ValueError('transition not allowed')
            if new_status == 'running':
                campaign_row = _fetch_campaign(conn, current['campaign_id'])
                campaign = _row_to_dict(campaign_row, _CAMPAIGN_COLUMNS)
                if campaign is None or campaign['archived_at'] is not None:
                    raise ValueError('campaign is not active')
                if campaign['config_revision'] != current['config_revision']:
                    raise ValueError('campaign brief has changed')
            now = _utcnow()
            cursor = conn.execute(
                'UPDATE generation_run SET status = ?, step = ?, updated_at = ? WHERE id = ? AND status = ? AND step = ?',
                (new_status, step, now, id, current_status, current_step),
            )
            if cursor.rowcount != 1:
                raise ValueError('generation run changed')
            updated = _fetch_run(conn, id)
            if updated is None:
                raise ValueError('generation run unavailable')
            return _decode_run(updated)
    except ValueError:
        raise
    except Exception:
        raise ValueError('generation run unavailable') from None
def set_snapshots(conn, id, sources, context):
    try:
        sources_json, context_json = _prepare_snapshots(sources, context)
        with _atomic(conn):
            row = _fetch_run(conn, id)
            if row is None:
                raise ValueError('generation run not found')
            current = _decode_run(row)
            current_status = current['status']
            if current_status not in ('prepared', 'running'):
                raise ValueError('snapshots are frozen')
            attempts = current['metrics'].get('attempts', 0)
            if isinstance(attempts, bool) or not isinstance(attempts, (int, float)):
                raise ValueError('generation run unavailable')
            if isinstance(attempts, float) and not math.isfinite(attempts):
                raise ValueError('generation run unavailable')
            same = current['sources'] == sources and current['context'] == context
            if attempts > 0:
                if same:
                    return current
                raise ValueError('snapshots are frozen')
            if same:
                return current
            now = _utcnow()
            cursor = conn.execute(
                'UPDATE generation_run SET sources_json = ?, context_json = ?, updated_at = ? WHERE id = ? AND status = ? AND metrics_json = ?',
                (sources_json, context_json, now, id, current_status, current['metrics_json']),
            )
            if cursor.rowcount != 1:
                raise ValueError('generation run changed')
            updated = _fetch_run(conn, id)
            if updated is None:
                raise ValueError('generation run unavailable')
            return _decode_run(updated)
    except ValueError:
        raise
    except Exception:
        raise ValueError('generation run unavailable') from None