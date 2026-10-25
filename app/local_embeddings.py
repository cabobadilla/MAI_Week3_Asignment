'''Local pinned sentence-transformer embeddings with manifest verification.'''

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import numpy as np

__all__ = ['LocalEmbeddings']

_MODEL_ID = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
_REVISION = 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
_IDENTITY = f'{_MODEL_ID}@{_REVISION}'

_MAX_MANIFEST_BYTES = 100 * 1024
_MAX_MODULES_BYTES = 1024 * 1024
_EMBEDDING_DIMENSION = 384
_MAX_TEXTS = 10_000
_MAX_TEXT_CHARACTERS = 2_000
_MAX_SEQUENCE_LENGTH = 128

_BACKSLASH = chr(92)
_NUL = chr(0)

_REQUIRED_FILES = frozenset(
    {
        'config.json',
        'modules.json',
        'model.safetensors',
        'tokenizer.json',
        '1_Pooling/config.json',
    }
)
_ALLOWED_MODULE_TYPES = frozenset(
    {
        'sentence_transformers.models.Transformer',
        'sentence_transformers.models.Pooling',
        'sentence_transformers.models.Normalize',
    }
)
_HEX_DIGITS = frozenset('0123456789abcdefABCDEF')


def _invalid_manifest() -> ValueError:
    return ValueError('invalid local embeddings manifest')


def _invalid_model() -> ValueError:
    return ValueError('invalid local embeddings model')


def _invalid_input() -> ValueError:
    return ValueError(
        'texts must be a non-empty list of at most 10000 non-blank '
        'strings of at most 2000 characters'
    )


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _invalid_manifest()
        result[key] = value
    return result


def _read_manifest(path: Path) -> dict:
    try:
        with open(path, 'rb') as handle:
            data = handle.read(_MAX_MANIFEST_BYTES + 1)
            if len(data) > _MAX_MANIFEST_BYTES:
                raise _invalid_manifest()
            if handle.read(1):
                raise _invalid_manifest()
    except ValueError:
        raise
    except Exception:
        raise _invalid_manifest() from None
    try:
        manifest = json.loads(
            data.decode('utf-8'),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except Exception:
        raise _invalid_manifest() from None
    if not isinstance(manifest, dict):
        raise _invalid_manifest()
    return manifest


def _validate_relative_path(relative: str) -> None:
    if not isinstance(relative, str) or not relative:
        raise _invalid_manifest()
    if (
        relative.startswith('/')
        or _BACKSLASH in relative
        or _NUL in relative
        or ':' in relative
    ):
        raise _invalid_manifest()
    parts = relative.split('/')
    if any(part in ('', '.', '..') for part in parts):
        raise _invalid_manifest()


def _validate_manifest(manifest: dict) -> dict[str, tuple[int, str]]:
    if manifest.get('model_id') != _MODEL_ID:
        raise _invalid_manifest()
    if manifest.get('revision') != _REVISION:
        raise _invalid_manifest()
    files = manifest.get('files')
    if not isinstance(files, dict) or not files:
        raise _invalid_manifest()
    verified: dict[str, tuple[int, str]] = {}
    for relative, entry in files.items():
        _validate_relative_path(relative)
        if not isinstance(entry, dict):
            raise _invalid_manifest()
        digest = entry.get('sha256')
        size = entry.get('bytes')
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in _HEX_DIGITS for character in digest)
        ):
            raise _invalid_manifest()
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise _invalid_manifest()
        verified[relative] = (size, digest.lower())
    if not _REQUIRED_FILES.issubset(verified):
        raise _invalid_manifest()
    return verified


def _verify_file(
    root: str,
    relative: str,
    expected_size: int,
    expected_digest: str,
) -> bytes | None:
    current = root
    final_stat = None
    for part in relative.split('/'):
        current = os.path.join(current, part)
        try:
            current_stat = os.lstat(current)
        except Exception:
            raise _invalid_manifest() from None
        if stat.S_ISLNK(current_stat.st_mode):
            raise _invalid_manifest()
        final_stat = current_stat

    if (
        final_stat is None
        or not stat.S_ISREG(final_stat.st_mode)
        or final_stat.st_nlink != 1
    ):
        raise _invalid_manifest()

    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    try:
        descriptor = os.open(current, flags)
    except Exception:
        raise _invalid_manifest() from None

    hasher = hashlib.sha256()
    total = 0
    modules_chunks: list[bytes] | None = [] if relative == 'modules.json' else None
    try:
        opened_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_stat.st_mode)
            or opened_stat.st_nlink != 1
            or (opened_stat.st_dev, opened_stat.st_ino)
            != (final_stat.st_dev, final_stat.st_ino)
        ):
            raise _invalid_manifest()
        with os.fdopen(descriptor, 'rb', closefd=True) as handle:
            descriptor = -1
            while True:
                chunk = handle.read(4 * 1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                hasher.update(chunk)
                if modules_chunks is not None:
                    if total <= _MAX_MODULES_BYTES:
                        modules_chunks.append(chunk)
                    else:
                        modules_chunks = None
    except Exception:
        raise _invalid_manifest() from None
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except Exception:
                pass

    if total != expected_size:
        raise _invalid_manifest()
    if hasher.hexdigest() != expected_digest:
        raise _invalid_manifest()
    if relative == 'modules.json':
        if modules_chunks is None:
            raise _invalid_manifest()
        return b''.join(modules_chunks)
    return None


def _validate_modules(data: bytes) -> None:
    try:
        modules = json.loads(
            data.decode('utf-8'),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except Exception:
        raise _invalid_manifest() from None
    if not isinstance(modules, list) or not modules:
        raise _invalid_manifest()
    for module in modules:
        if not isinstance(module, dict):
            raise _invalid_manifest()
        if module.get('type') not in _ALLOWED_MODULE_TYPES:
            raise _invalid_manifest()
        module_path = module.get('path')
        if not isinstance(module_path, str):
            raise _invalid_manifest()
        if module_path not in ('', '.'):
            _validate_relative_path(module_path)


def _verify_model_files(
    model_root: Path,
    files: dict[str, tuple[int, str]],
) -> None:
    try:
        root = os.fspath(model_root)
    except Exception:
        raise _invalid_manifest() from None
    if not isinstance(root, str) or not root:
        raise _invalid_manifest()
    try:
        root = os.path.abspath(root)
        root_parts = Path(root).parts
    except Exception:
        raise _invalid_manifest() from None
    current = ''
    for part in root_parts:
        current = os.path.join(current, part)
        try:
            component_stat = os.lstat(current)
        except Exception:
            raise _invalid_manifest() from None
        if stat.S_ISLNK(component_stat.st_mode) or not stat.S_ISDIR(component_stat.st_mode):
            raise _invalid_manifest()

    modules_data = None
    for relative in sorted(files):
        size, digest = files[relative]
        data = _verify_file(root, relative, size, digest)
        if relative == 'modules.json':
            modules_data = data
    if modules_data is None:
        raise _invalid_manifest()
    _validate_modules(modules_data)


def _load_model(model_root: Path):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        raise _invalid_model() from None
    try:
        return SentenceTransformer(
            str(model_root),
            device='cpu',
            local_files_only=True,
            trust_remote_code=False,
            token=False,
            model_kwargs={'use_safetensors': True},
        )
    except Exception:
        raise _invalid_model() from None


def _model_limit(model) -> int:
    try:
        limit = int(model.max_seq_length)
    except Exception:
        raise _invalid_model() from None
    if limit != _MAX_SEQUENCE_LENGTH:
        raise _invalid_model()
    return limit


def _validate_texts(texts: object) -> list[str]:
    if not isinstance(texts, list):
        raise _invalid_input()
    if not texts or len(texts) > _MAX_TEXTS:
        raise _invalid_input()
    for text in texts:
        if not isinstance(text, str):
            raise _invalid_input()
        if len(text) > _MAX_TEXT_CHARACTERS:
            raise _invalid_input()
        if not text.strip():
            raise _invalid_input()
    return list(texts)


def _check_token_length(model, text: str, limit: int) -> None:
    try:
        encoded = model.tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
        )
        input_ids = encoded['input_ids']
        if (
            isinstance(input_ids, (list, tuple))
            and input_ids
            and isinstance(input_ids[0], (list, tuple))
        ):
            length = len(input_ids[0])
        else:
            length = len(input_ids)
    except Exception:
        raise ValueError('unable to tokenize text') from None
    if length < 1 or length > limit:
        raise ValueError('text exceeds maximum sequence length')


class LocalEmbeddings:
    identity = _IDENTITY

    def __init__(self, model_dir: Path, manifest_path: Path) -> None:
        try:
            root = Path(model_dir)
            manifest_file = Path(manifest_path)
        except Exception:
            raise ValueError('invalid local embeddings configuration') from None
        manifest = _read_manifest(manifest_file)
        files = _validate_manifest(manifest)
        _verify_model_files(root, files)
        model = _load_model(root)
        self._max_sequence_length = _model_limit(model)
        self._model = model

    def encode(self, texts: list[str]) -> np.ndarray:
        validated = _validate_texts(texts)
        model = getattr(self, '_model', None)
        limit = getattr(self, '_max_sequence_length', None)
        if model is None or limit is None:
            raise _invalid_model()
        for text in validated:
            _check_token_length(model, text, limit)
        try:
            output = model.encode(
                validated,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception:
            raise ValueError('unable to encode texts') from None
        try:
            array = np.asarray(output, dtype=np.float32)
        except Exception:
            raise ValueError('unable to encode texts') from None
        if (
            array.ndim != 2
            or array.shape[0] != len(validated)
            or array.shape[1] != _EMBEDDING_DIMENSION
        ):
            raise ValueError('invalid embeddings output')
        if not np.isfinite(array).all():
            raise ValueError('invalid embeddings output')
        try:
            norms = np.linalg.norm(array, axis=1, keepdims=True)
        except Exception:
            raise ValueError('invalid embeddings output') from None
        if not np.isfinite(norms).all() or np.any(norms <= 0.0):
            raise ValueError('invalid embeddings output')
        normalized = np.asarray(array / norms, dtype=np.float32)
        if not np.isfinite(normalized).all():
            raise ValueError('invalid embeddings output')
        return normalized