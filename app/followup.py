'''Manual follow-up events and append-only distribution corrections.'''
from __future__ import annotations

import sqlite3
import uuid

from .distribution import (
    _FORMAT_FOR_CHANNEL,
    _json,
    _load_recipient,
    _now,
    _payload_hash,
    _require_actor,
    _require_campaign,
    _require_confirmed,
    _require_occurred,
    _require_operation,
    _require_public_url,
    _require_version,
    _text,
    _transaction,
)

_KINDS = frozenset(('response', 'note', 'next_step'))
_CHANGE_KEYS = frozenset(('occurred_at', 'content_version_id', 'campaign_recipient_id', 'public_url'))
_MAX_BODY = 20000
_MAX_ACTOR = 120


def _require_kind(value):
    if not isinstance(value, str) or value not in _KINDS:
        raise ValueError('invalid kind')
    return value


def _require_body(value):
    if not isinstance(value, str) or not value.strip() or len(value) > _MAX_BODY:
        raise ValueError('invalid body')
    return value


def _require_actor_value(value):
    text = _require_actor(value)
    if len(text) > _MAX_ACTOR:
        raise ValueError('invalid actor')
    return text


def _require_reason(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('invalid correction reason')
    return value


def _require_record_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('invalid record')
    return value


def _recipient_row(conn, campaign_id, recipient_id):
    if not isinstance(recipient_id, str) or not recipient_id.strip():
        raise ValueError('invalid recipient')
    row = conn.execute(
        'SELECT archived_at FROM campaign_recipient WHERE id = ? AND campaign_id = ?',
        (recipient_id, campaign_id),
    ).fetchone()
    if row is None:
        raise ValueError('recipient not available')
    return row


def _require_direct_recipient(conn, campaign_id, recipient_id):
    row = _recipient_row(conn, campaign_id, recipient_id)
    if row['archived_at'] is not None:
        raise ValueError('recipient not available')
    return recipient_id


def _load_distribution(conn, campaign_id, distribution_id):
    if not isinstance(distribution_id, str) or not distribution_id.strip():
        raise ValueError('invalid distribution')
    row = conn.execute(
        'SELECT * FROM distribution_record WHERE id = ? AND campaign_id = ?',
        (distribution_id, campaign_id),
    ).fetchone()
    if row is None:
        raise ValueError('distribution not available')
    return dict(row)


def _resolve_followup_refs(conn, campaign_id, recipient_id, distribution_id):
    if distribution_id is None:
        if recipient_id is None:
            return None, None
        return _require_direct_recipient(conn, campaign_id, recipient_id), None
    distribution = _load_distribution(conn, campaign_id, distribution_id)
    if distribution['kind'] == 'publication':
        if recipient_id is not None:
            raise ValueError('recipient does not match distribution')
        return None, distribution['id']
    expected_recipient = distribution['campaign_recipient_id']
    if expected_recipient is None:
        raise ValueError('distribution not available')
    _recipient_row(conn, campaign_id, expected_recipient)
    if recipient_id is not None:
        if not isinstance(recipient_id, str) or not recipient_id.strip() or recipient_id != expected_recipient:
            raise ValueError('recipient does not match distribution')
    return expected_recipient, distribution['id']


def add_followup(conn, campaign_id, kind, body, occurred_at, *, campaign_recipient_id=None, distribution_id=None, due_at=None, actor='operator', event_id=None):
    campaign_key = _text(campaign_id, 'invalid campaign')
    kind_value = _require_kind(kind)
    body_value = _require_body(body)
    occurred_value = _require_occurred(occurred_at)
    due_value = None if due_at is None else _require_occurred(due_at)
    actor_value = _require_actor_value(actor)
    if kind_value != 'next_step' and due_value is not None:
        raise ValueError('due date not allowed')
    with _transaction(conn):
        _require_campaign(conn, campaign_key, True)
        recipient_value, distribution_value = _resolve_followup_refs(
            conn, campaign_key, campaign_recipient_id, distribution_id
        )
        if event_id is None:
            followup_id = str(uuid.uuid4())
            existing = None
        else:
            if not isinstance(event_id, str):
                raise ValueError('invalid event id')
            try:
                event_uuid = uuid.UUID(event_id)
            except (AttributeError, TypeError, ValueError):
                raise ValueError('invalid event id') from None
            if event_uuid.version != 4 or event_uuid.variant != uuid.RFC_4122 or str(event_uuid) != event_id:
                raise ValueError('invalid event id')
            followup_id = event_id
            existing = conn.execute(
                'SELECT * FROM followup_event WHERE id = ?', (followup_id,)
            ).fetchone()
        if existing is not None:
            if (
                existing['campaign_id'] == campaign_key
                and existing['campaign_recipient_id'] == recipient_value
                and existing['distribution_id'] == distribution_value
                and existing['kind'] == kind_value
                and existing['body'] == body_value
                and existing['occurred_at'] == occurred_value
                and existing['due_at'] == due_value
                and existing['actor'] == actor_value
                and existing['supersedes_id'] is None
                and existing['correction_reason'] is None
            ):
                return dict(existing)
            raise ValueError('followup id already exists')
        recorded_at = _now()
        try:
            conn.execute(
                'INSERT INTO followup_event '
                '(id, campaign_id, campaign_recipient_id, distribution_id, kind, body, '
                'occurred_at, recorded_at, due_at, actor, supersedes_id, correction_reason) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    followup_id, campaign_key, recipient_value, distribution_value, kind_value,
                    body_value, occurred_value, recorded_at, due_value, actor_value, None, None,
                ),
            )
        except sqlite3.IntegrityError:
            if event_id is not None:
                existing = conn.execute(
                    'SELECT * FROM followup_event WHERE id = ?', (followup_id,)
                ).fetchone()
                if existing is not None:
                    if (
                        existing['campaign_id'] == campaign_key
                        and existing['campaign_recipient_id'] == recipient_value
                        and existing['distribution_id'] == distribution_value
                        and existing['kind'] == kind_value
                        and existing['body'] == body_value
                        and existing['occurred_at'] == occurred_value
                        and existing['due_at'] == due_value
                        and existing['actor'] == actor_value
                        and existing['supersedes_id'] is None
                        and existing['correction_reason'] is None
                    ):
                        return dict(existing)
                    raise ValueError('followup id already exists') from None
            raise ValueError('followup could not be recorded') from None
        row = conn.execute('SELECT * FROM followup_event WHERE id = ?', (followup_id,)).fetchone()
        if row is None:
            raise ValueError('followup could not be recorded')
        return dict(row)


def list_followups(conn, campaign_id, *, campaign_recipient_id=None, include_superseded=False):
    _require_campaign(conn, campaign_id, False)
    sql = 'SELECT * FROM followup_event f WHERE f.campaign_id = ?'
    params = [campaign_id]
    if campaign_recipient_id is not None:
        if not isinstance(campaign_recipient_id, str) or not campaign_recipient_id.strip():
            raise ValueError('invalid recipient')
        sql += ' AND f.campaign_recipient_id = ?'
        params.append(campaign_recipient_id)
    if not include_superseded:
        sql += ' AND NOT EXISTS (SELECT 1 FROM followup_event x WHERE x.campaign_id = f.campaign_id AND x.supersedes_id = f.id)'
    sql += ' ORDER BY f.recorded_at ASC, f.id ASC'
    return [dict(row) for row in conn.execute(sql, tuple(params)).fetchall()]


def correct_followup(conn, id, reason, *, body=None, occurred_at=None, due_at=None, actor='operator'):
    followup_id = _require_record_id(id)
    reason_value = _require_reason(reason)
    actor_value = _require_actor_value(actor)
    body_value = None if body is None else _require_body(body)
    occurred_value = None if occurred_at is None else _require_occurred(occurred_at)
    due_value = None if due_at is None else _require_occurred(due_at)
    with _transaction(conn):
        row = conn.execute('SELECT * FROM followup_event WHERE id = ?', (followup_id,)).fetchone()
        if row is None:
            raise ValueError('followup not available')
        original = dict(row)
        replacement = conn.execute(
            'SELECT 1 FROM followup_event WHERE supersedes_id = ? LIMIT 1',
            (followup_id,),
        ).fetchone()
        if replacement is not None:
            raise ValueError('followup is not current')
        if due_value is not None and original['kind'] != 'next_step':
            raise ValueError('due date not allowed')
        new_body = original['body'] if body is None else body_value
        new_occurred = original['occurred_at'] if occurred_at is None else occurred_value
        new_due = original['due_at'] if due_at is None else due_value
        new_id = str(uuid.uuid4())
        recorded_at = _now()
        try:
            conn.execute(
                'INSERT INTO followup_event '
                '(id, campaign_id, campaign_recipient_id, distribution_id, kind, body, '
                'occurred_at, recorded_at, due_at, actor, supersedes_id, correction_reason) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    new_id, original['campaign_id'], original['campaign_recipient_id'],
                    original['distribution_id'], original['kind'], new_body, new_occurred,
                    recorded_at, new_due, actor_value, followup_id, reason_value,
                ),
            )
        except sqlite3.IntegrityError:
            raise ValueError('followup could not be recorded') from None
        new_row = conn.execute('SELECT * FROM followup_event WHERE id = ?', (new_id,)).fetchone()
        if new_row is None:
            raise ValueError('followup could not be recorded')
        return dict(new_row)


def _normalize_changes(changes):
    if not isinstance(changes, dict) or not changes:
        raise ValueError('invalid changes')
    normalized = {}
    for key, value in changes.items():
        if key not in _CHANGE_KEYS:
            raise ValueError('invalid changes')
        if key == 'occurred_at':
            if value is None:
                raise ValueError('invalid changes')
            normalized[key] = _require_occurred(value)
        elif key == 'content_version_id':
            if value is None:
                raise ValueError('invalid changes')
            normalized[key] = _text(value, 'invalid version')
        elif key == 'campaign_recipient_id':
            if value is None:
                raise ValueError('invalid changes')
            normalized[key] = _text(value, 'invalid recipient')
        else:
            normalized[key] = _require_public_url(value)
    return normalized


def _correction_item_key(operation_id, record_id):
    return 'correction:' + operation_id + ':' + record_id


def _correction_payload(record, record_id, reason, changes, actor):
    return {
        'kind': 'correction',
        'record_id': record_id,
        'campaign_id': record['campaign_id'],
        'source_kind': record['kind'],
        'channel': record['channel'],
        'reason': reason,
        'changes': changes,
        'actor': actor,
    }


def _match_existing_correction(conn, operation_id, record, record_id, reason, changes, actor):
    rows = conn.execute(
        'SELECT * FROM distribution_record WHERE operation_id = ? ORDER BY id ASC',
        (operation_id,),
    ).fetchall()
    if not rows:
        return None
    if len(rows) != 1:
        raise ValueError('operation collision')
    row = dict(rows[0])
    if row['supersedes_id'] != record_id or row['correction_reason'] is None:
        raise ValueError('operation collision')
    if row['batch_size'] != 1:
        raise ValueError('operation collision')
    if row['campaign_id'] != record['campaign_id'] or row['kind'] != record['kind'] or row['channel'] != record['channel']:
        raise ValueError('operation collision')
    if row['operation_item_key'] != _correction_item_key(operation_id, record_id):
        raise ValueError('operation collision')
    expected_hash = _payload_hash(_correction_payload(record, record_id, reason, changes, actor))
    if row['payload_hash'] != expected_hash:
        raise ValueError('operation collision')
    return row


def _require_version_for_record(conn, record, version_id):
    if record['kind'] == 'email_sent':
        _require_version(conn, record['campaign_id'], version_id, 'email')
        return
    required_format = _FORMAT_FOR_CHANNEL.get(record['channel'])
    version = _require_version(conn, record['campaign_id'], version_id, required_format)
    if record['channel'] == 'other_public' and version['format'] == 'email':
        raise ValueError('version format mismatch')


def correct_distribution(conn, record_id, operation_id, reason, changes, *, confirmed=False, actor='operator'):
    _require_confirmed(confirmed)
    record_key = _require_record_id(record_id)
    operation = _require_operation(operation_id)
    reason_value = _require_reason(reason)
    actor_value = _require_actor_value(actor)
    normalized_changes = _normalize_changes(changes)
    with _transaction(conn):
        row = conn.execute('SELECT * FROM distribution_record WHERE id = ?', (record_key,)).fetchone()
        if row is None:
            raise ValueError('distribution not available')
        original = dict(row)
        existing = _match_existing_correction(
            conn, operation, original, record_key, reason_value, normalized_changes, actor_value
        )
        if existing is not None:
            return existing
        replacement = conn.execute(
            'SELECT 1 FROM distribution_record WHERE supersedes_id = ? LIMIT 1',
            (record_key,),
        ).fetchone()
        if replacement is not None:
            raise ValueError('distribution is not current')
        new_occurred = normalized_changes.get('occurred_at', original['occurred_at'])
        new_version = normalized_changes.get('content_version_id', original['content_version_id'])
        new_recipient = original['campaign_recipient_id']
        new_public_url = normalized_changes.get('public_url', original['public_url'])
        new_snapshot = original['destination_snapshot_json']
        if original['kind'] == 'publication':
            if 'campaign_recipient_id' in normalized_changes:
                raise ValueError('invalid changes')
        else:
            if 'campaign_recipient_id' in normalized_changes:
                candidate_recipient = normalized_changes['campaign_recipient_id']
                if candidate_recipient != original['campaign_recipient_id']:
                    recipient = _load_recipient(conn, original['campaign_id'], candidate_recipient)
                    new_snapshot = _json(recipient['snapshot'])
                    new_recipient = candidate_recipient
            if new_recipient is None:
                raise ValueError('recipient not available')
            if new_public_url is not None:
                raise ValueError('invalid public url')
        if 'content_version_id' in normalized_changes:
            _require_version_for_record(conn, original, new_version)
        new_id = str(uuid.uuid4())
        recorded_at = _now()
        try:
            conn.execute(
                'INSERT INTO distribution_record '
                '(id, campaign_id, content_version_id, campaign_recipient_id, kind, channel, '
                'occurred_at, recorded_at, actor, destination_snapshot_json, public_url, batch_id, '
                'operation_id, operation_item_key, payload_hash, batch_size, repeat_reason, '
                'supersedes_id, correction_reason) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    new_id, original['campaign_id'], new_version, new_recipient, original['kind'],
                    original['channel'], new_occurred, recorded_at, actor_value, new_snapshot,
                    new_public_url, original['batch_id'], operation,
                    _correction_item_key(operation, record_key),
                    _payload_hash(_correction_payload(original, record_key, reason_value, normalized_changes, actor_value)),
                    1, None, record_key, reason_value,
                ),
            )
        except sqlite3.IntegrityError:
            raise ValueError('correction could not be recorded') from None
        new_row = conn.execute('SELECT * FROM distribution_record WHERE id = ?', (new_id,)).fetchone()
        if new_row is None:
            raise ValueError('correction could not be recorded')
        return dict(new_row)
