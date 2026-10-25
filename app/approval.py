'''Bundle approval persistence.'''
from __future__ import annotations

import json
import re
import sqlite3
import uuid

from app.versions import _FORMATS, _now, _require_campaign, _sha, _validate_run, _write_tx

_HEX64 = re.compile(r'^[0-9a-fA-F]{64}$')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def _require_hex(value, label):
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise ValueError('invalid ' + label)


def _normalise_ids(version_ids, strict):
    if isinstance(version_ids, str):
        if strict:
            raise ValueError('invalid version ids')
        return None
    try:
        ids = list(version_ids)
    except TypeError:
        if strict:
            raise ValueError('invalid version ids') from None
        return None
    if not ids:
        if strict:
            raise ValueError('version ids required')
        return None
    seen = set()
    for version_id in ids:
        if not isinstance(version_id, str) or not version_id or version_id in seen:
            if strict:
                raise ValueError('invalid version ids')
            return None
        seen.add(version_id)
    return ids


def _campaign_formats(campaign):
    raw = campaign['formats_json']
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            raise ValueError('invalid campaign formats') from None
    else:
        data = raw
    if not isinstance(data, list) or not data:
        raise ValueError('invalid campaign formats')
    formats = []
    for value in data:
        if not isinstance(value, str) or value not in _FORMATS:
            raise ValueError('invalid campaign formats')
        formats.append(value)
    return formats


def _selected_versions(conn, version_ids, campaign_id):
    rows = []
    for version_id in version_ids:
        row = conn.execute('SELECT * FROM content_version WHERE id = ?', (version_id,)).fetchone()
        if row is None or row['campaign_id'] != campaign_id:
            raise ValueError('version does not belong to campaign')
        body = row['body']
        if not isinstance(body, str) or _sha(body) != row['content_hash']:
            raise ValueError('version hash mismatch')
        if row['format'] not in _FORMATS:
            raise ValueError('invalid version format')
        rows.append(row)
    return rows


def _find_existing(conn, campaign_id, revision_hash):
    return conn.execute('SELECT * FROM approval WHERE campaign_id = ? AND revision_hash = ? ORDER BY approved_at, id LIMIT 1', (campaign_id, revision_hash)).fetchone()


def _parse_manifest(raw):
    if not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _row_dict(row, with_manifest=False):
    out = dict(row)
    if with_manifest:
        out['manifest'] = _parse_manifest(out.get('version_manifest_json'))
    return out


def approve_bundle(conn, campaign_id, version_ids, source_hash, context_hash, *, actor='operator', run_id=None, unresolved_material_issues=None, expected_config_revision=None):
    ids = _normalise_ids(version_ids, True)
    _require_hex(source_hash, 'source_hash')
    _require_hex(context_hash, 'context_hash')
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError('actor required')
    if unresolved_material_issues:
        raise ValueError('unresolved material issues')
    with _write_tx(conn):
        campaign = _require_campaign(conn, campaign_id, True)
        if expected_config_revision is not None and expected_config_revision != campaign['config_revision']:
            raise ValueError('config revision mismatch')
        _validate_run(conn, run_id, campaign_id)
        rows = _selected_versions(conn, ids, campaign_id)
        required = set(_campaign_formats(campaign))
        selected = {row['format'] for row in rows}
        if selected != required:
            raise ValueError('formats do not match campaign')
        logical = set()
        for row in rows:
            key = (row['format'], row['variant'])
            if key in logical:
                raise ValueError('duplicate format and variant')
            logical.add(key)
        if 'ad' in required:
            named_variants = {row['variant'] for row in rows if row['format'] == 'ad' and isinstance(row['variant'], str) and row['variant']}
            if len(named_variants) < 3:
                raise ValueError('ad requires three variants')
        versions = []
        for row in rows:
            versions.append({'content_hash': row['content_hash'], 'format': row['format'], 'id': row['id'], 'variant': row['variant']})
        versions.sort(key=lambda item: (item['format'], item['variant'], item['id']))
        manifest = {'campaign_id': campaign_id, 'config_revision': campaign['config_revision'], 'context_hash': context_hash, 'source_hash': source_hash, 'versions': versions}
        manifest_json = _canonical(manifest)
        revision_hash = _sha(manifest_json)
        existing = _find_existing(conn, campaign_id, revision_hash)
        if existing is not None:
            return _row_dict(existing)
        approval_id = str(uuid.uuid4())
        approved_at = _now()
        try:
            conn.execute('''INSERT INTO approval
                (id, campaign_id, run_id, config_revision, version_manifest_json, source_hash, context_hash, revision_hash, actor, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (approval_id, campaign_id, run_id, campaign['config_revision'], manifest_json, source_hash, context_hash, revision_hash, actor, approved_at))
        except sqlite3.IntegrityError:
            existing = _find_existing(conn, campaign_id, revision_hash)
            if existing is not None:
                return _row_dict(existing)
            raise ValueError('approval could not be stored') from None
        row = conn.execute('SELECT * FROM approval WHERE id = ?', (approval_id,)).fetchone()
        if row is None:
            raise ValueError('approval not found')
        return _row_dict(row)


def get_approval(conn, id):
    if not isinstance(id, str) or not id:
        raise ValueError('invalid approval')
    row = conn.execute('SELECT * FROM approval WHERE id = ?', (id,)).fetchone()
    if row is None:
        raise ValueError('approval not found')
    return _row_dict(row, True)


def _manifest_pairs(manifest):
    if isinstance(manifest, dict):
        versions = manifest.get('versions')
    elif isinstance(manifest, list):
        versions = manifest
    else:
        return None
    if not isinstance(versions, list):
        return None
    pairs = set()
    ids = set()
    for item in versions:
        if not isinstance(item, dict):
            return None
        version_id = item.get('id')
        content_hash = item.get('content_hash')
        if not isinstance(version_id, str) or not version_id or not isinstance(content_hash, str) or version_id in ids:
            return None
        ids.add(version_id)
        pairs.add((version_id, content_hash))
    return pairs


def approval_covers(conn, approval_id, version_ids):
    if not isinstance(approval_id, str) or not approval_id:
        return False
    approval = conn.execute('SELECT * FROM approval WHERE id = ?', (approval_id,)).fetchone()
    if approval is None:
        return False
    ids = _normalise_ids(version_ids, False)
    if ids is None:
        return False
    pairs = _manifest_pairs(_parse_manifest(approval['version_manifest_json']))
    if pairs is None:
        return False
    current = set()
    for version_id in ids:
        version = conn.execute('SELECT * FROM content_version WHERE id = ?', (version_id,)).fetchone()
        if version is None or version['campaign_id'] != approval['campaign_id']:
            return False
        body = version['body']
        if not isinstance(body, str) or _sha(body) != version['content_hash']:
            return False
        current.add((version_id, version['content_hash']))
    if current != pairs:
        return False
    campaign = conn.execute('SELECT config_revision FROM campaign WHERE id = ?', (approval['campaign_id'],)).fetchone()
    if campaign is None or campaign['config_revision'] != approval['config_revision']:
        return False
    return True
