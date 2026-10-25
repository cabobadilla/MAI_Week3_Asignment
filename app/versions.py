'''Content version persistence.'''
from __future__ import annotations

import hashlib
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

_FORMATS = frozenset(('linkedin', 'email', 'article', 'ad'))
_ORIGINS = frozenset(('generated', 'human_edit', 'manual_external'))
_VARIANT_RE = re.compile(r'^[A-Za-z0-9_-]{0,40}$')


@contextmanager
def _write_tx(conn):
    if conn.in_transaction:
        yield
    else:
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            conn.rollback()
            raise
        else:
            conn.commit()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _require_format(value):
    if not isinstance(value, str) or value not in _FORMATS:
        raise ValueError('invalid format')


def _require_origin(value):
    if not isinstance(value, str) or value not in _ORIGINS:
        raise ValueError('invalid origin')


def _require_body(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('body must be a non-blank string')


def _require_variant(value, fmt):
    if not isinstance(value, str) or _VARIANT_RE.fullmatch(value) is None:
        raise ValueError('invalid variant')
    if fmt == 'ad' and not value:
        raise ValueError('ad requires a named variant')


def _require_campaign(conn, campaign_id, active):
    if not isinstance(campaign_id, str) or not campaign_id:
        raise ValueError('invalid campaign')
    row = conn.execute('SELECT * FROM campaign WHERE id = ?', (campaign_id,)).fetchone()
    if row is None or (active and row['archived_at'] is not None):
        raise ValueError('campaign not available')
    return row


def _q(name):
    quote = chr(34)
    return quote + name.replace(quote, quote + quote) + quote


def _columns(conn, name):
    try:
        rows = conn.execute('PRAGMA table_info(' + _q(name) + ')').fetchall()
    except sqlite3.DatabaseError:
        return set()
    return {row['name'] for row in rows}


def _run_table(conn):
    try:
        fks = conn.execute('PRAGMA foreign_key_list(content_version)').fetchall()
    except sqlite3.DatabaseError:
        fks = []
    for fk in fks:
        if fk['from'] == 'run_id':
            name = fk['table']
            if name and {'id', 'campaign_id'} <= _columns(conn, name):
                return name
    try:
        rows = conn.execute('SELECT name FROM sqlite_master WHERE type = ?', ('table',)).fetchall()
    except sqlite3.DatabaseError:
        rows = []
    preferences = ('run', 'campaign_run', 'generation_run', 'runs', 'campaign_runs', 'generation_runs')
    ranked = []
    for row in rows:
        name = row['name']
        low = name.lower()
        if low.startswith('sqlite_') or 'run' not in low:
            continue
        if not {'id', 'campaign_id'} <= _columns(conn, name):
            continue
        rank = len(preferences)
        for index, preferred in enumerate(preferences):
            if low == preferred:
                rank = index
                break
        ranked.append((rank, name))
    if not ranked:
        return None
    ranked.sort()
    return ranked[0][1]


def _validate_run(conn, run_id, campaign_id):
    if run_id is None:
        return
    if not isinstance(run_id, str) or not run_id:
        raise ValueError('invalid run')
    table = _run_table(conn)
    if table is None:
        raise ValueError('run not available')
    row = conn.execute('SELECT 1 FROM ' + _q(table) + ' WHERE id = ? AND campaign_id = ?', (run_id, campaign_id)).fetchone()
    if row is None:
        raise ValueError('run not in campaign')


def _require_parent(conn, parent_version_id, campaign_id, fmt, variant):
    if not isinstance(parent_version_id, str) or not parent_version_id:
        raise ValueError('invalid parent version')
    row = conn.execute('SELECT * FROM content_version WHERE id = ?', (parent_version_id,)).fetchone()
    if row is None or row['campaign_id'] != campaign_id or row['format'] != fmt or row['variant'] != variant:
        raise ValueError('parent version mismatch')


def _insert_version(conn, campaign_id, fmt, body, variant, run_id, parent_version_id, origin):
    version_id = str(uuid.uuid4())
    created_at = _now()
    content_hash = _sha(body)
    try:
        conn.execute('''INSERT INTO content_version
            (id, campaign_id, run_id, format, variant, revision_no, body, content_hash, origin, parent_version_id, created_at)
            VALUES (?, ?, ?, ?, ?, (SELECT COALESCE(MAX(revision_no), 0) + 1 FROM content_version WHERE campaign_id = ? AND format = ? AND variant = ?), ?, ?, ?, ?, ?)''',
            (version_id, campaign_id, run_id, fmt, variant, campaign_id, fmt, variant, body, content_hash, origin, parent_version_id, created_at))
    except sqlite3.IntegrityError:
        raise ValueError('version could not be created') from None
    row = conn.execute('SELECT * FROM content_version WHERE id = ?', (version_id,)).fetchone()
    if row is None:
        raise ValueError('version not found')
    return dict(row)


def create_version(conn, campaign_id, format, body, variant='', run_id=None, parent_version_id=None, origin='generated'):
    _require_format(format)
    _require_origin(origin)
    _require_body(body)
    _require_variant(variant, format)
    with _write_tx(conn):
        _require_campaign(conn, campaign_id, True)
        _validate_run(conn, run_id, campaign_id)
        if parent_version_id is not None:
            _require_parent(conn, parent_version_id, campaign_id, format, variant)
        return _insert_version(conn, campaign_id, format, body, variant, run_id, parent_version_id, origin)


def edit_version(conn, id, new_body):
    _require_body(new_body)
    with _write_tx(conn):
        original = conn.execute('SELECT * FROM content_version WHERE id = ?', (id,)).fetchone()
        if original is None:
            raise ValueError('version not found')
        _require_campaign(conn, original['campaign_id'], True)
        return _insert_version(conn, original['campaign_id'], original['format'], new_body, original['variant'], original['run_id'], original['id'], 'human_edit')


def get_version(conn, id):
    row = conn.execute('SELECT * FROM content_version WHERE id = ?', (id,)).fetchone()
    if row is None:
        raise ValueError('version not found')
    return dict(row)


def list_versions(conn, campaign_id, format=None, latest_only=False):
    _require_campaign(conn, campaign_id, False)
    if format is not None:
        _require_format(format)
    where = 'campaign_id = ?'
    params = [campaign_id]
    if format is not None:
        where += ' AND format = ?'
        params.append(format)
    if latest_only:
        where += ' AND revision_no = (SELECT MAX(v2.revision_no) FROM content_version v2 WHERE v2.campaign_id = content_version.campaign_id AND v2.format = content_version.format AND v2.variant = content_version.variant)'
    sql = 'SELECT * FROM content_version WHERE ' + where + ' ORDER BY format, variant, revision_no, id'
    return [dict(row) for row in conn.execute(sql, params).fetchall()]
