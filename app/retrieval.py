import copy
import hashlib
import json
import math
import os
import stat
import tempfile
from pathlib import Path

from app.native_runtime_guard import install_guard, assert_compatible

install_guard('vector')
assert_compatible('vector')

import faiss
import numpy as np
from app.ingestion import source_fingerprint

_MAX_BYTES = 64 * 1024 * 1024
_MAX_CHUNKS = 10000
_MAX_TEXT = 2000
_MAX_DIMS = 4096
_VERSION = 1
_KEYS = frozenset(('version', 'chunks', 'vectors', 'embedding_identity', 'source_fingerprint', 'integrity'))


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _identity(embedder):
    value = getattr(embedder, 'identity', None)
    if callable(value):
        try:
            value = value('')
        except TypeError:
            try:
                value = value()
            except TypeError:
                raise ValueError('invalid embedder identity') from None
    if not isinstance(value, str) or len(value) > 300:
        raise ValueError('invalid embedder identity')
    return value


def _copy_chunks(chunks):
    if not isinstance(chunks, list) or len(chunks) > _MAX_CHUNKS:
        raise ValueError('invalid chunks')
    out = []
    seen = set()
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError('invalid chunk')
        cid = chunk.get('chunk_id')
        try:
            if cid in seen:
                raise ValueError('duplicate chunk_id')
            seen.add(cid)
        except TypeError:
            raise ValueError('invalid chunk_id') from None
        text = chunk.get('text')
        if not isinstance(text, str) or not text.strip() or len(text) > _MAX_TEXT:
            raise ValueError('invalid chunk text')
        if hashlib.sha256(text.encode('utf-8')).hexdigest() != chunk.get('text_hash'):
            raise ValueError('invalid chunk text hash')
        out.append(copy.deepcopy(chunk))
    try:
        fingerprint = source_fingerprint(out)
    except Exception:
        raise ValueError('invalid chunk provenance') from None
    if not isinstance(fingerprint, str) or not fingerprint:
        raise ValueError('invalid source fingerprint')
    return out, fingerprint


def _vectors(raw, count):
    try:
        arr = np.asarray(raw)
        if arr.ndim != 2 or arr.shape[0] != count or not 1 <= arr.shape[1] <= _MAX_DIMS:
            raise ValueError('invalid vectors')
        if arr.dtype.kind not in 'fiu':
            raise ValueError('invalid vectors')
        arr = np.array(arr, dtype=np.float32, order='C', copy=True)
    except (TypeError, ValueError, OverflowError):
        raise ValueError('invalid vectors') from None
    if not np.isfinite(arr).all():
        raise ValueError('invalid vectors')
    if arr.shape[0] and not np.all(np.any(arr != 0, axis=1)):
        raise ValueError('invalid vectors')
    return arr


def _normalize(arr):
    if arr.shape[0] == 0:
        return np.ascontiguousarray(arr, dtype=np.float32)
    norms = np.linalg.norm(arr.astype(np.float64), axis=1)
    if not np.isfinite(norms).all() or np.any(norms == 0):
        raise ValueError('invalid vectors')
    return np.ascontiguousarray(arr / norms[:, None], dtype=np.float32)


def _absolute(path):
    try:
        return Path(os.path.abspath(os.fspath(path)))
    except (TypeError, ValueError, OSError):
        raise ValueError('invalid path') from None


def _inspect(path, allow_missing):
    current = Path(path.anchor)
    if path == current:
        raise ValueError('invalid path')
    for part in path.parts[1:]:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            if current == path and allow_missing:
                return None
            raise ValueError('invalid path') from None
        except OSError:
            raise ValueError('invalid path') from None
        if stat.S_ISLNK(info.st_mode):
            raise ValueError('invalid path')
        if current == path:
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('invalid path')
            return info
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError('invalid path')
    raise ValueError('invalid path')


def _read(path):
    p = _absolute(path)
    info = _inspect(p, False)
    if info.st_size > _MAX_BYTES:
        raise ValueError('invalid vector store')
    try:
        fd = os.open(p, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    except OSError:
        raise ValueError('invalid vector store') from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_BYTES:
            raise ValueError('invalid vector store')
        with os.fdopen(fd, 'rb') as handle:
            fd = -1
            data = handle.read(_MAX_BYTES + 1)
    finally:
        if fd != -1:
            os.close(fd)
    if len(data) > _MAX_BYTES:
        raise ValueError('invalid vector store')
    return data


def _write(path, data):
    p = _absolute(path)
    temp_name = None
    try:
        info = _inspect(p, True)
        if info is not None and info.st_nlink != 1:
            raise ValueError('invalid path')
        fd, temp_name = tempfile.mkstemp(prefix='.' + p.name + '.', suffix='.tmp', dir=str(p.parent))
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        info = _inspect(p, True)
        if info is not None and info.st_nlink != 1:
            raise ValueError('invalid path')
        os.replace(temp_name, p)
        temp_name = None
    except Exception as error:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        if isinstance(error, ValueError):
            raise
        raise ValueError('invalid path') from None


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError('invalid constant')


def _parse(data):
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=_no_duplicates, parse_constant=_bad_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
        raise ValueError('invalid vector store') from None


class VectorStore:
    @classmethod
    def build(cls, chunks, embedder):
        assert_compatible('vector')
        identity = _identity(embedder)
        chunks, fingerprint = _copy_chunks(chunks)
        texts = [chunk['text'] for chunk in chunks]
        try:
            raw = embedder.encode(texts)
        except Exception:
            raise ValueError('embedding failed') from None
        vectors = _vectors(raw, len(chunks))
        index = faiss.IndexFlatIP(vectors.shape[1])
        if len(chunks):
            index.add(_normalize(vectors))
        store = cls.__new__(cls)
        store._chunks = chunks
        store._vectors = vectors
        store._embedder = embedder
        store._identity = identity
        store._source_fingerprint = fingerprint
        store._index = index
        return store

    @property
    def source_fingerprint(self):
        return self._source_fingerprint

    def search(self, query, top_k=4, *, exclude_ids=None, min_score=0.0):
        assert_compatible('vector')
        if not isinstance(query, str):
            raise ValueError('invalid query')
        if type(top_k) is not int or not 1 <= top_k <= 8:
            raise ValueError('invalid top_k')
        try:
            valid_score = not isinstance(min_score, bool) and isinstance(min_score, (int, float)) and math.isfinite(min_score) and -1 <= min_score <= 1
        except (TypeError, OverflowError):
            valid_score = False
        if not valid_score:
            raise ValueError('invalid min_score')
        if exclude_ids is None:
            excluded = set()
        elif isinstance(exclude_ids, str):
            excluded = {exclude_ids}
        else:
            try:
                excluded = set(exclude_ids)
            except (TypeError, ValueError):
                raise ValueError('invalid exclude_ids') from None
        if not query.strip():
            return []
        if len(query) > 1000:
            raise ValueError('invalid query')
        try:
            raw = self._embedder.encode([query])
        except Exception:
            raise ValueError('embedding failed') from None
        query_vector = _vectors(raw, 1)
        if query_vector.shape[1] != self._index.d:
            raise ValueError('invalid query dimension')
        if self._index.ntotal == 0:
            return []
        distances, indices = self._index.search(_normalize(query_vector), self._index.ntotal)
        found = []
        for score, position in zip(distances[0], indices[0]):
            if position < 0:
                continue
            chunk = self._chunks[int(position)]
            if chunk['chunk_id'] in excluded:
                continue
            score = float(score)
            if not math.isfinite(score):
                raise ValueError('invalid score')
            if score < min_score:
                continue
            found.append((score, chunk))
        found.sort(key=lambda item: (-item[0], str(item[1]['chunk_id'])))
        result = []
        for score, chunk in found[:top_k]:
            item = copy.deepcopy(chunk)
            item['score'] = score
            result.append(item)
        return result

    def save(self, path):
        assert_compatible('vector')
        body = {
            'version': _VERSION,
            'chunks': self._chunks,
            'vectors': self._vectors.tolist(),
            'embedding_identity': self._identity,
            'source_fingerprint': self._source_fingerprint,
        }
        try:
            integrity = hashlib.sha256(_canonical(body)).hexdigest()
            payload = dict(body)
            payload['integrity'] = integrity
            data = _canonical(payload)
        except (TypeError, ValueError, OverflowError):
            raise ValueError('invalid vector store') from None
        if len(data) > _MAX_BYTES:
            raise ValueError('vector store too large')
        _write(path, data)

    @classmethod
    def load(cls, path, embedder, *, expected_source_fingerprint):
        assert_compatible('vector')
        try:
            return cls._load(path, embedder, expected_source_fingerprint)
        except Exception:
            raise ValueError('invalid vector store') from None

    @classmethod
    def _load(cls, path, embedder, expected_source_fingerprint):
        payload = _parse(_read(path))
        if not isinstance(payload, dict) or set(payload) != _KEYS:
            raise ValueError('invalid vector store')
        if type(payload.get('version')) is not int or payload['version'] != _VERSION:
            raise ValueError('invalid vector store')
        integrity = payload.get('integrity')
        if not isinstance(integrity, str) or len(integrity) != 64:
            raise ValueError('invalid vector store')
        body = {key: value for key, value in payload.items() if key != 'integrity'}
        if hashlib.sha256(_canonical(body)).hexdigest() != integrity:
            raise ValueError('invalid vector store')
        chunks, fingerprint = _copy_chunks(payload['chunks'])
        stored = payload.get('source_fingerprint')
        if not isinstance(expected_source_fingerprint, str) or stored != fingerprint or expected_source_fingerprint != fingerprint:
            raise ValueError('invalid vector store')
        identity = payload.get('embedding_identity')
        if not isinstance(identity, str) or len(identity) > 300:
            raise ValueError('invalid vector store')
        if _identity(embedder) != identity:
            raise ValueError('invalid vector store')
        vectors = _vectors(payload['vectors'], len(chunks))
        index = faiss.IndexFlatIP(vectors.shape[1])
        if len(chunks):
            index.add(_normalize(vectors))
        store = cls.__new__(cls)
        store._chunks = chunks
        store._vectors = vectors
        store._embedder = embedder
        store._identity = identity
        store._source_fingerprint = fingerprint
        store._index = index
        return store
