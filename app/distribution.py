'''Manual external distribution recording.'''
from __future__ import annotations

import hashlib
import json
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from urllib.parse import urlsplit

_OPERATION_RE = re.compile(r'^[A-Za-z0-9_-]{1,120}$')
_PUBLIC_CHANNELS = frozenset(('linkedin', 'web', 'ad', 'other_public'))
_FORMAT_FOR_CHANNEL = {'linkedin': 'linkedin', 'web': 'article', 'ad': 'ad'}
_MAX_RECIPIENTS = 500
_MAX_URL = 2048


@contextmanager
def _transaction(conn):
    if conn.in_transaction:
        name = 'distribution_' + uuid.uuid4().hex
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
        return
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield
    except BaseException:
        conn.rollback()
        raise
    else:
        try:
            conn.commit()
        except BaseException:
            conn.rollback()
            raise


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _text(value, message):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(message)
    return value


def _require_operation(value):
    if not isinstance(value, str) or _OPERATION_RE.fullmatch(value) is None:
        raise ValueError('invalid operation id')
    return value


def _require_actor(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('invalid actor')
    return value


def _require_confirmed(value):
    if value is not True:
        raise ValueError('operator confirmation required')


def _require_occurred(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('invalid occurred date')
    text = value.strip()
    candidate = text[:-1] + '+00:00' if text.endswith('Z') else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        raise ValueError('invalid occurred date') from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('invalid occurred date')
    return text


def _require_repeat(value):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError('invalid repeat reason')
    return value


def _require_recipient_ids(value):
    if not isinstance(value, (list, tuple)):
        raise ValueError('invalid recipient list')
    if not value:
        raise ValueError('recipient list is empty')
    if len(value) > _MAX_RECIPIENTS:
        raise ValueError('too many recipients')
    seen = set()
    result = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError('invalid recipient')
        if item in seen:
            raise ValueError('duplicate recipient')
        seen.add(item)
        result.append(item)
    return result


def _require_campaign(conn, campaign_id, active):
    if not isinstance(campaign_id, str) or not campaign_id.strip():
        raise ValueError('invalid campaign')
    row = conn.execute('SELECT * FROM campaign WHERE id = ?', (campaign_id,)).fetchone()
    if row is None or (active and row['archived_at'] is not None):
        raise ValueError('campaign not available')
    return dict(row)


def _require_version(conn, campaign_id, version_id, required_format=None):
    if not isinstance(version_id, str) or not version_id.strip():
        raise ValueError('invalid version')
    row = conn.execute('SELECT * FROM content_version WHERE id = ? AND campaign_id = ?', (version_id, campaign_id)).fetchone()
    if row is None:
        raise ValueError('version not available')
    if required_format is not None and row['format'] != required_format:
        raise ValueError('version format mismatch')
    if not isinstance(row['body'], str) or _sha(row['body']) != row['content_hash']:
        raise ValueError('version integrity check failed')
    return dict(row)


def _load_recipient(conn, campaign_id, recipient_id):
    row = conn.execute(
        'SELECT cr.id AS recipient_id, cr.campaign_id AS recipient_campaign_id, '
        'cr.contact_id AS recipient_contact_id, cr.email_key AS selection_email_key, '
        'cr.snapshot_json AS snapshot_json, cr.selected_at AS selected_at, '
        'cr.archived_at AS selection_archived_at, ct.email_key AS contact_email_key, '
        'ct.archived_at AS contact_archived_at, co.archived_at AS company_archived_at '
        'FROM campaign_recipient cr JOIN contact ct ON ct.id = cr.contact_id '
        'JOIN company co ON co.id = ct.company_id WHERE cr.id = ? AND cr.campaign_id = ?',
        (recipient_id, campaign_id),
    ).fetchone()
    if row is None or row['recipient_campaign_id'] != campaign_id:
        raise ValueError('recipient not available')
    if row['selection_archived_at'] is not None or row['contact_archived_at'] is not None or row['company_archived_at'] is not None:
        raise ValueError('recipient not available')
    try:
        snapshot = json.loads(row['snapshot_json'])
    except (TypeError, ValueError):
        raise ValueError('recipient requires reselection') from None
    if not isinstance(snapshot, dict):
        raise ValueError('recipient requires reselection')
    key = snapshot.get('email_key')
    if not isinstance(key, str) or not key.strip() or key != row['contact_email_key']:
        raise ValueError('recipient requires reselection')
    return {
        'id': row['recipient_id'],
        'campaign_id': row['recipient_campaign_id'],
        'contact_id': row['recipient_contact_id'],
        'email_key': row['selection_email_key'],
        'snapshot': snapshot,
        'selected_at': row['selected_at'],
        'archived_at': row['selection_archived_at'],
    }


def _email_payload(campaign_id, version_id, occurred_at, actor, repeat_reason, recipients):
    ordered = sorted(recipients, key=lambda item: item['id'])
    return {
        'campaign_id': campaign_id,
        'content_version_id': version_id,
        'recipient_ids': [item['id'] for item in ordered],
        'destinations': [{'recipient_id': item['id'], 'snapshot': item['snapshot']} for item in ordered],
        'occurred_at': occurred_at,
        'actor': actor,
        'repeat_reason': repeat_reason,
        'kind': 'email_sent',
    }


def _publication_payload(campaign_id, version_id, channel, occurred_at, actor, public_url, repeat_reason):
    return {
        'campaign_id': campaign_id,
        'content_version_id': version_id,
        'recipient_ids': [],
        'destinations': {},
        'occurred_at': occurred_at,
        'actor': actor,
        'repeat_reason': repeat_reason,
        'kind': 'publication',
        'channel': channel,
        'public_url': public_url,
    }


def _payload_hash(payload):
    return _sha(_json(payload))


def _current_email_duplicate(conn, campaign_id, version_id, recipient_id):
    row = conn.execute(
        'SELECT 1 FROM distribution_record d WHERE d.campaign_id = ? '
        'AND d.content_version_id = ? AND d.campaign_recipient_id = ? '
        'AND d.kind = ? AND d.channel = ? AND NOT EXISTS '
        '(SELECT 1 FROM distribution_record x WHERE x.supersedes_id = d.id) LIMIT 1',
        (campaign_id, version_id, recipient_id, 'email_sent', 'email'),
    ).fetchone()
    return row is not None


def _current_publication_duplicate(conn, campaign_id, version_id, channel):
    row = conn.execute(
        'SELECT 1 FROM distribution_record d WHERE d.campaign_id = ? '
        'AND d.content_version_id = ? AND d.channel = ? AND d.kind = ? '
        'AND NOT EXISTS (SELECT 1 FROM distribution_record x WHERE x.supersedes_id = d.id) LIMIT 1',
        (campaign_id, version_id, channel, 'publication'),
    ).fetchone()
    return row is not None


def _operation_rows(conn, operation_id):
    rows = conn.execute('SELECT * FROM distribution_record WHERE operation_id = ? ORDER BY recorded_at, id', (operation_id,)).fetchall()
    return [dict(row) for row in rows]


def _match_email_operation(rows, campaign_id, version_id, recipient_ids, occurred_at, actor, repeat_reason):
    if not rows:
        raise ValueError('operation collision')
    batch_ids = {row['batch_id'] for row in rows}
    if len(batch_ids) != 1 or None in batch_ids:
        raise ValueError('operation collision')
    existing = {}
    for row in rows:
        if row['kind'] != 'email_sent' or row['channel'] != 'email':
            raise ValueError('operation collision')
        if row['campaign_id'] != campaign_id or row['content_version_id'] != version_id:
            raise ValueError('operation collision')
        if row['occurred_at'] != occurred_at or row['actor'] != actor:
            raise ValueError('operation collision')
        if row['repeat_reason'] != repeat_reason or row['batch_size'] != len(recipient_ids):
            raise ValueError('operation collision')
        recipient_id = row['campaign_recipient_id']
        if recipient_id is None or recipient_id in existing:
            raise ValueError('operation collision')
        existing[recipient_id] = row
    if set(existing) != set(recipient_ids):
        raise ValueError('operation collision')
    return sorted(existing.values(), key=lambda item: item['id'])


def _match_publication_operation(rows, campaign_id, version_id, channel, occurred_at, actor, public_url, repeat_reason):
    if len(rows) != 1:
        raise ValueError('operation collision')
    row = rows[0]
    if row['kind'] != 'publication' or row['channel'] != channel:
        raise ValueError('operation collision')
    if row['campaign_id'] != campaign_id or row['content_version_id'] != version_id:
        raise ValueError('operation collision')
    if row['occurred_at'] != occurred_at or row['actor'] != actor:
        raise ValueError('operation collision')
    if row['repeat_reason'] != repeat_reason or row['public_url'] != public_url:
        raise ValueError('operation collision')
    if row['campaign_recipient_id'] is not None:
        raise ValueError('operation collision')
    return row


def _require_public_url(value):
    if value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > _MAX_URL:
        raise ValueError('invalid public url')
    if any(ch.isspace() or ord(ch) < 32 for ch in value):
        raise ValueError('invalid public url')
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in ('http', 'https'):
            raise ValueError('invalid public url')
        if not parts.netloc or '@' in parts.netloc:
            raise ValueError('invalid public url')
        if parts.username is not None or parts.password is not None:
            raise ValueError('invalid public url')
    except ValueError:
        raise ValueError('invalid public url') from None
    return value


def preview_email_batch(conn, campaign_id, version_id, recipient_ids):
    ids = _require_recipient_ids(recipient_ids)
    _require_campaign(conn, campaign_id, True)
    _require_version(conn, campaign_id, version_id, 'email')
    recipients = [_load_recipient(conn, campaign_id, recipient_id) for recipient_id in ids]
    warnings = []
    for recipient_id in ids:
        if _current_email_duplicate(conn, campaign_id, version_id, recipient_id):
            warnings.append('duplicate recorded distribution for this version')
    return {'recipients': recipients, 'warnings': warnings}


def record_email_batch(conn, campaign_id, version_id, recipient_ids, occurred_at, operation_id, *, confirmed=False, actor='operator', repeat_reason=None):
    _require_confirmed(confirmed)
    campaign_key = _text(campaign_id, 'invalid campaign')
    version_key = _text(version_id, 'invalid version')
    ids = _require_recipient_ids(recipient_ids)
    occurred = _require_occurred(occurred_at)
    operation = _require_operation(operation_id)
    actor_value = _require_actor(actor)
    reason = _require_repeat(repeat_reason)
    with _transaction(conn):
        existing = _operation_rows(conn, operation)
        if existing:
            return _match_email_operation(existing, campaign_key, version_key, ids, occurred, actor_value, reason)
        _require_campaign(conn, campaign_key, True)
        _require_version(conn, campaign_key, version_key, 'email')
        recipients = [_load_recipient(conn, campaign_key, recipient_id) for recipient_id in ids]
        duplicate = False
        for recipient_id in ids:
            if _current_email_duplicate(conn, campaign_key, version_key, recipient_id):
                duplicate = True
                break
        if duplicate and reason is None:
            raise ValueError('repeat reason required')
        payload_hash = _payload_hash(_email_payload(campaign_key, version_key, occurred, actor_value, reason, recipients))
        batch_id = str(uuid.uuid4())
        recorded_at = _now()
        batch_size = len(ids)
        for recipient in recipients:
            conn.execute(
                'INSERT INTO distribution_record '
                '(id, campaign_id, content_version_id, campaign_recipient_id, kind, channel, '
                'occurred_at, recorded_at, actor, destination_snapshot_json, public_url, batch_id, '
                'operation_id, operation_item_key, payload_hash, batch_size, repeat_reason, '
                'supersedes_id, correction_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    str(uuid.uuid4()), campaign_key, version_key, recipient['id'], 'email_sent', 'email',
                    occurred, recorded_at, actor_value, _json(recipient['snapshot']), None, batch_id,
                    operation, 'email:' + operation + ':' + recipient['id'], payload_hash, batch_size,
                    reason, None, None,
                ),
            )
        rows = conn.execute('SELECT * FROM distribution_record WHERE batch_id = ? ORDER BY id', (batch_id,)).fetchall()
        if len(rows) != batch_size:
            raise ValueError('distribution could not be recorded')
        return [dict(row) for row in rows]


def record_publication(conn, campaign_id, version_id, channel, occurred_at, operation_id, *, confirmed=False, actor='operator', public_url=None, repeat_reason=None):
    _require_confirmed(confirmed)
    campaign_key = _text(campaign_id, 'invalid campaign')
    version_key = _text(version_id, 'invalid version')
    if not isinstance(channel, str) or channel not in _PUBLIC_CHANNELS:
        raise ValueError('invalid publication channel')
    occurred = _require_occurred(occurred_at)
    operation = _require_operation(operation_id)
    actor_value = _require_actor(actor)
    reason = _require_repeat(repeat_reason)
    url = _require_public_url(public_url)
    with _transaction(conn):
        existing = _operation_rows(conn, operation)
        if existing:
            return _match_publication_operation(existing, campaign_key, version_key, channel, occurred, actor_value, url, reason)
        _require_campaign(conn, campaign_key, True)
        version_row = _require_version(conn, campaign_key, version_key, _FORMAT_FOR_CHANNEL.get(channel))
        if channel == 'other_public' and version_row['format'] == 'email':
            raise ValueError('version format mismatch')
        if _current_publication_duplicate(conn, campaign_key, version_key, channel) and reason is None:
            raise ValueError('repeat reason required')
        payload_hash = _payload_hash(_publication_payload(campaign_key, version_key, channel, occurred, actor_value, url, reason))
        distribution_id = str(uuid.uuid4())
        recorded_at = _now()
        conn.execute(
            'INSERT INTO distribution_record '
            '(id, campaign_id, content_version_id, campaign_recipient_id, kind, channel, '
            'occurred_at, recorded_at, actor, destination_snapshot_json, public_url, batch_id, '
            'operation_id, operation_item_key, payload_hash, batch_size, repeat_reason, '
            'supersedes_id, correction_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                distribution_id, campaign_key, version_key, None, 'publication', channel,
                occurred, recorded_at, actor_value, '{}', url, None, operation,
                'public:' + operation + ':' + campaign_key + ':' + channel + ':' + version_key,
                payload_hash, 1, reason, None, None,
            ),
        )
        row = conn.execute('SELECT * FROM distribution_record WHERE id = ?', (distribution_id,)).fetchone()
        if row is None:
            raise ValueError('distribution could not be recorded')
        return dict(row)


def list_distributions(conn, campaign_id, *, include_superseded=False):
    _require_campaign(conn, campaign_id, False)
    sql = 'SELECT * FROM distribution_record d WHERE d.campaign_id = ?'
    if not include_superseded:
        sql += ' AND NOT EXISTS (SELECT 1 FROM distribution_record x WHERE x.campaign_id = d.campaign_id AND x.supersedes_id = d.id)'
    sql += ' ORDER BY d.recorded_at ASC, d.id ASC'
    return [dict(row) for row in conn.execute(sql, (campaign_id,)).fetchall()]
