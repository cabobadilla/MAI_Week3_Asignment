import bisect
import hashlib
import json
import os
import stat
from pathlib import Path
_APPROVED = (
    'libfile_6c37cc40080c8191b552dd3b1d48f25b',
    'libfile_53f339c6e3808191aa4d31aa25664829',
)
_APPROVED_SET = frozenset(_APPROVED)
_HANDOUT = 'libfile_4ced0bc870a88191815184ca416bf8f5'
_VERSION = '0.2'
_MAX_ORIGINAL = 10 * 1024 * 1024
_MAX_EXTRACTED = 2 * 1024 * 1024
_MAX_MANIFEST = 100 * 1024
_MAX_CHUNKS = 10000
_LF = chr(10)
_ERROR = 'invalid ingestion source'
_PARAM_ERROR = 'invalid ingestion request'
_HEX = frozenset('0123456789abcdefABCDEF')
class _Invalid(ValueError):
    pass
class _DuplicateKey(Exception):
    pass
def _fail(message=_ERROR):
    raise _Invalid(message)
def _sha256(data):
    return hashlib.sha256(data).hexdigest()
def _is_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(ch in _HEX for ch in value)
def _duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey()
        result[key] = value
    return result
def _within(root, path):
    try:
        return os.path.commonpath((str(root), str(path))) == str(root)
    except (OSError, ValueError):
        return False
def _project_root(project_root):
    try:
        root = Path(os.path.abspath(os.fspath(project_root)))
    except (OSError, TypeError, ValueError):
        _fail(_PARAM_ERROR)
    try:
        ok = os.path.isdir(root)
    except (OSError, ValueError):
        _fail(_PARAM_ERROR)
    if not ok:
        _fail(_PARAM_ERROR)
    return root
def _safe_regular(root, path):
    if not _within(root, path):
        _fail()
    try:
        rel = path.relative_to(root)
    except ValueError:
        _fail()
    if not rel.parts:
        _fail()
    current = root
    final = None
    for part in rel.parts:
        current = current / part
        try:
            info = os.lstat(current)
        except (OSError, ValueError):
            _fail()
        if stat.S_ISLNK(info.st_mode):
            _fail()
        if current == path:
            if not stat.S_ISREG(info.st_mode):
                _fail()
            final = info
        elif not stat.S_ISDIR(info.st_mode):
            _fail()
    if final is None:
        _fail()
    return final
def _read_bounded(path, limit):
    fd = -1
    try:
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            _fail()
        parts = []
        remaining = limit + 1
        while remaining > 0:
            piece = os.read(fd, min(65536, remaining))
            if not piece:
                break
            parts.append(piece)
            remaining -= len(piece)
        data = b''.join(parts)
        if len(data) > limit:
            _fail()
        return data
    except _Invalid:
        raise
    except (OSError, OverflowError, ValueError):
        _fail()
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
def _manifest_location(root, manifest_path):
    try:
        path = Path(os.fspath(manifest_path))
    except (OSError, TypeError, ValueError):
        _fail(_PARAM_ERROR)
    if any(part == '..' for part in path.parts):
        _fail(_PARAM_ERROR)
    try:
        if not path.is_absolute():
            path = root / path
        path = Path(os.path.abspath(os.fspath(path)))
        root_real = Path(os.path.realpath(root))
    except (OSError, TypeError, ValueError):
        _fail(_PARAM_ERROR)
    if _within(root, path):
        return root, path
    if _within(root_real, path):
        return root_real, path
    _fail()
def _load_manifest(root, manifest_path):
    base, path = _manifest_location(root, manifest_path)
    _safe_regular(base, path)
    raw = _read_bounded(path, _MAX_MANIFEST)
    try:
        document = raw.decode('utf-8')
    except UnicodeDecodeError:
        _fail()
    try:
        manifest = json.loads(document, object_pairs_hook=_duplicate_keys)
    except (_DuplicateKey, json.JSONDecodeError, RecursionError, ValueError):
        _fail()
    if not isinstance(manifest, list):
        _fail()
    entries = {}
    for item in manifest:
        if not isinstance(item, dict):
            _fail()
        source_id = item.get('library_file_id')
        if not isinstance(source_id, str) or not source_id:
            _fail()
        if source_id in entries:
            _fail()
        entries[source_id] = item
    return entries
def _select_sources(source_ids):
    if source_ids is None:
        return list(_APPROVED)
    if isinstance(source_ids, (str, bytes, bytearray)):
        _fail(_PARAM_ERROR)
    try:
        requested = list(source_ids)
    except TypeError:
        _fail(_PARAM_ERROR)
    for source_id in requested:
        if not isinstance(source_id, str):
            _fail(_PARAM_ERROR)
    if len(requested) != len(set(requested)):
        _fail(_PARAM_ERROR)
    for source_id in requested:
        if source_id == _HANDOUT or source_id not in _APPROVED_SET:
            _fail(_PARAM_ERROR)
    if isinstance(source_ids, (set, frozenset)):
        requested = [source_id for source_id in _APPROVED if source_id in requested]
    return requested
def _validate_chunking(chunk_size, overlap):
    if type(chunk_size) is not int or chunk_size < 200 or chunk_size > 2000:
        _fail(_PARAM_ERROR)
    if type(overlap) is not int or overlap < 0 or overlap > chunk_size // 2:
        _fail(_PARAM_ERROR)
def _entry_path(root, value):
    if not isinstance(value, str) or not value:
        _fail()
    try:
        path = Path(value)
    except (OSError, TypeError, ValueError):
        _fail()
    if path.is_absolute() or os.path.isabs(value):
        _fail()
    if value[0] in ('/', chr(92)):
        _fail()
    if len(value) >= 2 and value[1] == ':' and value[0].isalpha():
        _fail()
    if any(part == '..' for part in path.parts):
        _fail()
    try:
        path = Path(os.path.abspath(os.fspath(root / path)))
    except (OSError, TypeError, ValueError):
        _fail()
    if not _within(root, path):
        _fail()
    _safe_regular(root, path)
    return path
def _source_fields(entry):
    version = entry.get('content_version')
    if not isinstance(version, str) or version != _VERSION:
        _fail()
    original_rel = entry.get('path')
    extracted_rel = entry.get('extracted_path')
    original_hash = entry.get('sha256')
    extracted_hash = entry.get('extracted_sha256')
    if not isinstance(original_rel, str) or not original_rel:
        _fail()
    if not isinstance(extracted_rel, str) or not extracted_rel:
        _fail()
    if not _is_digest(original_hash) or not _is_digest(extracted_hash):
        _fail()
    return original_rel, extracted_rel, original_hash.lower(), extracted_hash.lower()
def _prepare_source(root, source_id, entry):
    original_rel, extracted_rel, expected_original, expected_extracted = _source_fields(entry)
    original = _entry_path(root, original_rel)
    extracted = _entry_path(root, extracted_rel)
    original_bytes = _read_bounded(original, _MAX_ORIGINAL)
    if _sha256(original_bytes) != expected_original:
        _fail()
    extracted_bytes = _read_bounded(extracted, _MAX_EXTRACTED)
    if _sha256(extracted_bytes) != expected_extracted:
        _fail()
    try:
        text = extracted_bytes.decode('utf-8')
    except UnicodeDecodeError:
        _fail()
    if not text.strip():
        _fail()
    source_name = Path(original_rel).name
    if not source_name:
        _fail()
    return {
        'source_id': source_id,
        'content_version': _VERSION,
        'source_name': source_name,
        'source_hash': expected_original,
        'extracted_hash': expected_extracted,
        'text': text,
    }
def _chunk_source(source, chunk_size, overlap):
    text = source['text']
    length = len(text)
    newlines = [index for index, character in enumerate(text) if character == _LF]
    step = chunk_size - overlap
    spans = []
    start = 0
    while start < length:
        end = start + chunk_size
        if end > length:
            end = length
        segment = text[start:end]
        if segment.strip():
            spans.append((start, end))
        if end >= length:
            break
        start += step
    chunks = []
    for start, end in spans:
        segment = text[start:end]
        line_start = bisect.bisect_left(newlines, start) + 1
        line_end = bisect.bisect_left(newlines, end) + 1
        chunk_id = ':'.join((source['source_id'], source['content_version'], source['extracted_hash'], str(start), str(end)))
        chunks.append({
            'source_id': source['source_id'],
            'content_version': source['content_version'],
            'source_name': source['source_name'],
            'source_hash': source['source_hash'],
            'text_hash': _sha256(segment.encode('utf-8')),
            'chunk_id': chunk_id,
            'start': start,
            'end': end,
            'line_start': line_start,
            'line_end': line_end,
            'text': segment,
            'trusted_instructions': False,
        })
    return chunks
def load_chunks(project_root: Path, manifest_path: Path, *, source_ids=None, chunk_size=900, overlap=120) -> list[dict]:
    _validate_chunking(chunk_size, overlap)
    requested = _select_sources(source_ids)
    if not requested:
        return []
    root = _project_root(project_root)
    entries = _load_manifest(root, manifest_path)
    for source_id in requested:
        if source_id not in entries:
            _fail()
    sources = []
    for source_id in requested:
        sources.append(_prepare_source(root, source_id, entries[source_id]))
    chunks = []
    for source in sources:
        source_chunks = _chunk_source(source, chunk_size, overlap)
        if not source_chunks:
            _fail()
        if len(chunks) + len(source_chunks) > _MAX_CHUNKS:
            _fail()
        chunks.extend(source_chunks)
    return chunks
def source_fingerprint(chunks) -> str:
    if chunks is None or isinstance(chunks, (str, bytes, bytearray)):
        _fail(_PARAM_ERROR)
    try:
        items = list(chunks)
    except TypeError:
        _fail(_PARAM_ERROR)
    rows = []
    required = ('source_id', 'content_version', 'source_name', 'source_hash', 'text_hash', 'chunk_id', 'start', 'end', 'line_start', 'line_end', 'text', 'trusted_instructions')
    for item in items:
        if not isinstance(item, dict):
            _fail(_PARAM_ERROR)
        if any(key not in item for key in required):
            _fail(_PARAM_ERROR)
        for key in ('source_id', 'content_version', 'source_name', 'source_hash', 'text_hash', 'chunk_id', 'text'):
            if not isinstance(item[key], str):
                _fail(_PARAM_ERROR)
        for key in ('start', 'end', 'line_start', 'line_end'):
            if type(item[key]) is not int:
                _fail(_PARAM_ERROR)
        if item['trusted_instructions'] is not False:
            _fail(_PARAM_ERROR)
        if not _is_digest(item['source_hash']) or not _is_digest(item['text_hash']):
            _fail(_PARAM_ERROR)
        if item['start'] < 0 or item['end'] <= item['start']:
            _fail(_PARAM_ERROR)
        if item['line_start'] < 1 or item['line_end'] < item['line_start']:
            _fail(_PARAM_ERROR)
        rows.append((
            item['source_id'],
            item['content_version'],
            item['source_name'],
            item['source_hash'],
            item['text_hash'],
            item['chunk_id'],
            item['start'],
            item['end'],
            item['line_start'],
            item['line_end'],
            item['trusted_instructions'],
        ))
    rows.sort()
    document = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    return _sha256(document.encode('utf-8'))