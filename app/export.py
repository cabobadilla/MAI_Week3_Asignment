'''Bounded backend export bundling.'''
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import uuid
from pathlib import Path, PurePosixPath

from app.approval import approval_covers
from app.versions import _FORMATS, _now, _require_campaign, _sha, _write_tx

_OP_RE = re.compile(r'^[A-Za-z0-9_-]{1,120}$')
_SAFE_RE = re.compile(r'^[A-Za-z0-9_-]{1,120}$')
_VARIANT_RE = re.compile(r'^[A-Za-z0-9_-]{0,40}$')
_HEX64 = re.compile(r'^[0-9a-f]{64}$')
_LABEL = 'BORRADOR APROBADO PARA EXPORTACIÓN'
_ERROR = 'export could not be completed'


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def _operation(value):
    if not isinstance(value, str) or _OP_RE.fullmatch(value) is None:
        raise ValueError('invalid operation id')
    return value


def _safe(value, label):
    if not isinstance(value, str) or _SAFE_RE.fullmatch(value) is None:
        raise ValueError('invalid ' + label)
    return value


def _lstat(path):
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError:
        raise ValueError('invalid filesystem path') from None


def _assert_dirs(path, label):
    parts = path.parts
    if not parts:
        raise ValueError('invalid ' + label)
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        info = _lstat(current)
        if info is None:
            break
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(label + ' must not contain symlinks')
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError(label + ' must be a directory')
    return path


def _normalise_root(output_root):
    try:
        raw = os.fspath(output_root)
    except TypeError:
        raise ValueError('invalid output root') from None
    if not isinstance(raw, str) or not raw or chr(0) in raw:
        raise ValueError('invalid output root')
    path = Path.cwd().joinpath(raw)
    _assert_dirs(path, 'output root')
    root = Path(os.path.abspath(raw))
    _assert_dirs(root, 'output root')
    return root


def _relative_parts(value):
    if not isinstance(value, str) or not value or chr(92) in value or chr(0) in value:
        raise ValueError('invalid export manifest')
    pure = PurePosixPath(value)
    parts = pure.parts
    if pure.is_absolute() or not parts or pure.as_posix() != value:
        raise ValueError('invalid export manifest')
    if any(part in ('', '.', '..') for part in parts):
        raise ValueError('invalid export manifest')
    return parts


def _parse_files(raw):
    if not isinstance(raw, str):
        raise ValueError('invalid export manifest')
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        raise ValueError('invalid export manifest') from None
    if not isinstance(data, list) or not data:
        raise ValueError('invalid export manifest')
    files = []
    seen = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError('invalid export manifest')
        relative = item.get('relative_path')
        digest = item.get('sha256')
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise ValueError('invalid export manifest')
        _relative_parts(relative)
        if _HEX64.fullmatch(digest) is None or relative in seen:
            raise ValueError('invalid export manifest')
        seen.add(relative)
        files.append({'relative_path': relative, 'sha256': digest})
    return files


def _payload(root, approval_id, revision, campaign_id, operation_id):
    value = {
        'approval_id': approval_id,
        'approval_revision_hash': revision,
        'campaign_id': campaign_id,
        'operation_id': operation_id,
        'output_root': str(root),
    }
    return _sha(_canonical(value))


def _bundle_id(campaign_id, approval_id, operation_id):
    seed = 'gwa-export:' + campaign_id + ':' + approval_id + ':' + operation_id
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def _with_files(row, files):
    result = dict(row)
    result['files'] = files
    return result


def _read(path):
    info = _lstat(path)
    if info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ValueError('export file is unavailable')
    try:
        with open(path, 'rb') as handle:
            return handle.read()
    except OSError:
        raise ValueError('export file is unavailable') from None


def _verify_existing(root, campaign_id, files):
    for item in files:
        parts = _relative_parts(item['relative_path'])
        if parts[0] != campaign_id:
            raise ValueError('invalid export manifest')
        path = root.joinpath(*parts)
        _assert_dirs(path.parent, 'bundle path')
        data = _read(path)
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('export file has changed')


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
    formats = set()
    for value in data:
        if not isinstance(value, str) or value not in _FORMATS:
            raise ValueError('invalid campaign formats')
        formats.add(value)
    return formats


def _manifest_versions(approval):
    raw = approval['version_manifest_json']
    if not isinstance(raw, str):
        raise ValueError('invalid approval manifest')
    try:
        manifest = json.loads(raw)
    except (TypeError, ValueError):
        raise ValueError('invalid approval manifest') from None
    if _sha(_canonical(manifest)) != approval['revision_hash']:
        raise ValueError('approval manifest hash mismatch')
    if isinstance(manifest, dict):
        if 'campaign_id' in manifest and manifest['campaign_id'] != approval['campaign_id']:
            raise ValueError('invalid approval manifest')
        if 'config_revision' in manifest and manifest['config_revision'] != approval['config_revision']:
            raise ValueError('invalid approval manifest')
        versions = manifest.get('versions')
    elif isinstance(manifest, list):
        versions = manifest
    else:
        raise ValueError('invalid approval manifest')
    if not isinstance(versions, list) or not versions:
        raise ValueError('invalid approval manifest')
    result = []
    seen = set()
    for item in versions:
        if not isinstance(item, dict):
            raise ValueError('invalid approval manifest')
        version_id = item.get('id')
        content_hash = item.get('content_hash')
        if not isinstance(version_id, str) or not version_id or version_id in seen:
            raise ValueError('invalid approval manifest')
        if not isinstance(content_hash, str) or _HEX64.fullmatch(content_hash) is None:
            raise ValueError('invalid approval manifest')
        fmt = item.get('format')
        variant = item.get('variant')
        if fmt is not None and (not isinstance(fmt, str) or fmt not in _FORMATS):
            raise ValueError('invalid approval manifest')
        if variant is not None and (not isinstance(variant, str) or _VARIANT_RE.fullmatch(variant) is None):
            raise ValueError('invalid approval manifest')
        seen.add(version_id)
        result.append((version_id, content_hash, fmt, variant))
    return result


def _load_versions(conn, approval, campaign, entries):
    if approval['config_revision'] != campaign['config_revision']:
        raise ValueError('approval is stale')
    formats = _campaign_formats(campaign)
    versions = []
    ids = []
    logical = set()
    for version_id, approved_hash, approved_format, approved_variant in entries:
        row = conn.execute('SELECT * FROM content_version WHERE id = ?', (version_id,)).fetchone()
        if row is None or row['campaign_id'] != approval['campaign_id']:
            raise ValueError('approved version not found')
        fmt = row['format']
        variant = row['variant']
        body = row['body']
        if not isinstance(fmt, str) or fmt not in _FORMATS:
            raise ValueError('invalid approved version')
        if not isinstance(variant, str) or _VARIANT_RE.fullmatch(variant) is None:
            raise ValueError('invalid approved version')
        if not isinstance(body, str) or _sha(body) != row['content_hash']:
            raise ValueError('approved version changed')
        if row['content_hash'] != approved_hash:
            raise ValueError('approved version changed')
        if approved_format is not None and approved_format != fmt:
            raise ValueError('approved version changed')
        if approved_variant is not None and approved_variant != variant:
            raise ValueError('approved version changed')
        key = (fmt, variant)
        if key in logical:
            raise ValueError('duplicate version')
        logical.add(key)
        versions.append(row)
        ids.append(version_id)
    if {row['format'] for row in versions} != formats:
        raise ValueError('campaign config changed')
    if 'ad' in formats:
        named = {row['variant'] for row in versions if row['format'] == 'ad' and row['variant']}
        if len(named) < 3:
            raise ValueError('campaign config changed')
    if not approval_covers(conn, approval['id'], ids):
        raise ValueError('approval is not valid')
    return versions


def _render(version, approval_id):
    header = chr(10).join((
        _LABEL,
        '',
        'format: ' + version['format'],
        'variant: ' + version['variant'],
        'content_hash: ' + version['content_hash'],
        'approval_id: ' + approval_id,
        'version_id: ' + version['id'],
    ))
    return (header + chr(10) + chr(10) + version['body']).encode('utf-8')


def _expected_files(campaign_id, bundle_id, versions, approval_id):
    single = len(versions) == 1
    expected = {}
    files = []
    for version in sorted(versions, key=lambda row: (row['format'], row['variant'], row['id'])):
        filename = 'piece.md' if single else version['format'] + '-' + version['id'] + '.md'
        relative = campaign_id + '/' + bundle_id + '/' + filename
        data = _render(version, approval_id)
        digest = hashlib.sha256(data).hexdigest()
        expected[filename] = (data, digest)
        files.append({'relative_path': relative, 'sha256': digest})
    files.sort(key=lambda item: item['relative_path'])
    return expected, files


def _ensure_dir(path, label):
    _assert_dirs(path, label)
    try:
        os.makedirs(path, mode=0o700, exist_ok=True)
    except OSError:
        raise ValueError(label + ' is unavailable') from None
    info = _lstat(path)
    if info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ValueError(label + ' is unavailable')
    _assert_dirs(path, label)
    return path


def _stage(campaign_dir, expected):
    stage = campaign_dir / ('.export-stage-' + uuid.uuid4().hex)
    try:
        os.mkdir(stage, 0o700)
        for name in sorted(expected):
            data = expected[name][0]
            with open(stage / name, 'xb') as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
    except BaseException:
        try:
            shutil.rmtree(stage)
        except OSError:
            pass
        raise
    return stage


def _matches(final, expected):
    info = _lstat(final)
    if info is None:
        return False
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ValueError('bundle path conflict')
    found = set()
    try:
        with os.scandir(final) as entries:
            for entry in entries:
                if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                    raise ValueError('bundle path conflict')
                found.add(entry.name)
    except OSError:
        raise ValueError('bundle path conflict') from None
    if found != set(expected):
        raise ValueError('bundle path conflict')
    for name in sorted(expected):
        data = _read(final / name)
        if hashlib.sha256(data).hexdigest() != expected[name][1]:
            raise ValueError('bundle path conflict')
    return True


def _publish(stage, final):
    _assert_dirs(final.parent, 'bundle path')
    if _lstat(final) is not None:
        raise ValueError('bundle path conflict')
    try:
        os.rename(stage, final)
    except OSError:
        try:
            shutil.rmtree(stage)
        except OSError:
            pass
        raise ValueError('bundle path conflict') from None


def export_bundle(conn, approval_id: str, output_root: Path, operation_id: str) -> dict:
    try:
        operation = _operation(operation_id)
        if not isinstance(approval_id, str) or not approval_id or chr(0) in approval_id:
            raise ValueError('invalid approval')
        root = _normalise_root(output_root)
        with _write_tx(conn):
            existing = conn.execute('SELECT * FROM export_record WHERE operation_id = ?', (operation,)).fetchone()
            if existing is not None:
                record = dict(existing)
                _safe(record['campaign_id'], 'campaign id')
                if record['approval_id'] != approval_id:
                    raise ValueError('operation does not match')
                approval = conn.execute('SELECT * FROM approval WHERE id = ?', (approval_id,)).fetchone()
                if approval is None or approval['campaign_id'] != record['campaign_id']:
                    raise ValueError('operation does not match')
                expected_payload = _payload(root, approval_id, approval['revision_hash'], record['campaign_id'], operation)
                if record['payload_hash'] != expected_payload:
                    raise ValueError('operation does not match')
                files = _parse_files(record['files_manifest_json'])
                _verify_existing(root, record['campaign_id'], files)
                return _with_files(record, files)
            approval = conn.execute('SELECT * FROM approval WHERE id = ?', (approval_id,)).fetchone()
            if approval is None:
                raise ValueError('approval not found')
            campaign_id = approval['campaign_id']
            _safe(campaign_id, 'campaign id')
            campaign = _require_campaign(conn, campaign_id, True)
            if approval['config_revision'] != campaign['config_revision']:
                raise ValueError('approval is stale')
            entries = _manifest_versions(approval)
            versions = _load_versions(conn, approval, campaign, entries)
            for version in versions:
                _safe(version['id'], 'version id')
            payload_hash = _payload(root, approval_id, approval['revision_hash'], campaign_id, operation)
            bundle_id = _bundle_id(campaign_id, approval_id, operation)
            expected, files = _expected_files(campaign_id, bundle_id, versions, approval_id)
            campaign_dir = root / campaign_id
            final = campaign_dir / bundle_id
            _ensure_dir(root, 'output root')
            _ensure_dir(campaign_dir, 'campaign path')
            _assert_dirs(final.parent, 'bundle path')
            if not _matches(final, expected):
                stage = _stage(campaign_dir, expected)
                _publish(stage, final)
            record_id = str(uuid.uuid4())
            occurred_at = _now()
            manifest_json = _canonical(files)
            try:
                conn.execute(
                    'INSERT INTO export_record (id, campaign_id, approval_id, operation_id, payload_hash, files_manifest_json, occurred_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (record_id, campaign_id, approval_id, operation, payload_hash, manifest_json, occurred_at),
                )
            except sqlite3.IntegrityError:
                existing = conn.execute('SELECT * FROM export_record WHERE operation_id = ?', (operation,)).fetchone()
                if existing is None:
                    raise ValueError('export could not be recorded') from None
                record = dict(existing)
                if record['payload_hash'] != payload_hash or record['approval_id'] != approval_id:
                    raise ValueError('operation does not match')
                files = _parse_files(record['files_manifest_json'])
                _verify_existing(root, record['campaign_id'], files)
                return _with_files(record, files)
            row = conn.execute('SELECT * FROM export_record WHERE id = ?', (record_id,)).fetchone()
            if row is None:
                raise ValueError('export record not found')
            return _with_files(dict(row), files)
    except ValueError:
        raise
    except (OSError, sqlite3.DatabaseError):
        raise ValueError(_ERROR) from None
