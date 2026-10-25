import json
import sqlite3
import uuid
from datetime import datetime, timezone

CAMPAIGN_FORMATS = ('linkedin', 'email', 'article', 'ad')
_ALLOWED_FORMATS = frozenset(CAMPAIGN_FORMATS)
_UPDATE_FIELDS = frozenset(('title', 'topic', 'objective', 'audience_segment', 'tone', 'formats'))

def _now():
    return datetime.now(timezone.utc).isoformat()

def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Required campaign text is invalid.')
    return value

def _formats(value, academic_suite=False):
    if value is None:
        value = list(CAMPAIGN_FORMATS)
    if not isinstance(value, list) or not value:
        raise ValueError('Formats must be a non-empty list.')
    for item in value:
        if not isinstance(item, str) or item not in _ALLOWED_FORMATS:
            raise ValueError('Unknown format.')
    if len(set(value)) != len(value):
        raise ValueError('Duplicate formats are not allowed.')
    if academic_suite:
        return list(CAMPAIGN_FORMATS)
    return list(value)

def _from_row(row):
    data = dict(row)
    data['formats'] = json.loads(data.pop('formats_json'))
    return data

def _row(conn, campaign_id):
    row = conn.execute('SELECT id, title, topic, objective, audience_segment, tone, formats_json, config_revision, created_at, archived_at FROM campaign WHERE id = ?', (campaign_id,)).fetchone()
    if row is None:
        raise ValueError('Campaign was not found.')
    return row

def create_campaign(conn, title, topic, objective, audience_segment='companies', tone='Cercano', formats=None, academic_suite=False):
    title = _text(title)
    topic = _text(topic)
    objective = _text(objective)
    audience_segment = _text(audience_segment)
    tone = _text(tone)
    selected = _formats(formats, academic_suite=bool(academic_suite))
    campaign_id = str(uuid.uuid4())
    try:
        conn.execute('INSERT INTO campaign (id, title, topic, objective, audience_segment, tone, formats_json, config_revision, created_at, archived_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, NULL)', (campaign_id, title, topic, objective, audience_segment, tone, json.dumps(selected, ensure_ascii=False), _now()))
    except sqlite3.IntegrityError:
        raise ValueError('Campaign could not be created.') from None
    return get_campaign(conn, campaign_id)

def get_campaign(conn, id):
    return _from_row(_row(conn, id))

def list_campaigns(conn, include_archived=False):
    sql = 'SELECT id, title, topic, objective, audience_segment, tone, formats_json, config_revision, created_at, archived_at FROM campaign'
    if not include_archived:
        sql += ' WHERE archived_at IS NULL'
    sql += ' ORDER BY created_at DESC, id ASC'
    return [_from_row(row) for row in conn.execute(sql).fetchall()]

def update_campaign(conn, id, **fields):
    expected_revision = fields.pop('expected_revision', None)
    if set(fields) - _UPDATE_FIELDS:
        raise ValueError('Unknown campaign field.')
    row = _row(conn, id)
    current = _from_row(row)
    if row['archived_at'] is not None:
        raise ValueError('Campaign is archived.')
    if expected_revision is not None:
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool):
            raise ValueError('Expected revision must be an integer.')
        if expected_revision != current['config_revision']:
            raise ValueError('Campaign revision is stale.')
    if not fields:
        return current
    updates = {}
    relevant_change = False
    if 'title' in fields:
        updates['title'] = _text(fields['title'])
    if 'formats' in fields:
        selected = _formats(fields['formats'])
        updates['formats_json'] = json.dumps(selected, ensure_ascii=False)
        relevant_change = selected != current['formats']
    for name in ('topic', 'objective', 'audience_segment', 'tone'):
        if name in fields:
            value = _text(fields[name])
            updates[name] = value
            if value != current[name]:
                relevant_change = True
    parts = [name + ' = ?' for name in updates]
    params = list(updates.values())
    if relevant_change:
        parts.append('config_revision = config_revision + 1')
    params.append(id)
    where = 'id = ? AND archived_at IS NULL'
    if expected_revision is not None:
        where += ' AND config_revision = ?'
        params.append(expected_revision)
    cursor = conn.execute('UPDATE campaign SET ' + ', '.join(parts) + ' WHERE ' + where, tuple(params))
    if cursor.rowcount != 1:
        raise ValueError('Campaign was modified or is unavailable.')
    return get_campaign(conn, id)

def archive_campaign(conn, id):
    row = _row(conn, id)
    if row['archived_at'] is None:
        conn.execute('UPDATE campaign SET archived_at = ? WHERE id = ? AND archived_at IS NULL', (_now(), id))
    return get_campaign(conn, id)
