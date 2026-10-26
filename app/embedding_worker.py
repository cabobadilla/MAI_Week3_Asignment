'''Standalone worker process for local embedding generation.'''

import contextlib
import importlib
import importlib.util
import json
import math
import os
import signal
import sys
import types
from pathlib import Path


MODEL_ID = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MODEL_REVISION = 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
IDENTITY = MODEL_ID + '@' + MODEL_REVISION

_EMBEDDING_DIM = 384
_MAX_TEXTS = 10_000
_MAX_TEXT_CHARS = 2_000
_MAX_INPUT_BYTES = 32 * 1024 * 1024
_COMPONENT_PACKAGE_NAME = '_gwa_component_worker_app'
_COMPONENT_MODULE_NAME = _COMPONENT_PACKAGE_NAME + '.component_embeddings'
_COMPONENT_PACKAGE_DIR = Path(__file__).resolve().parent
_COMPONENT_PACKAGE_INIT_PATH = _COMPONENT_PACKAGE_DIR / '__init__.py'


def _reject_constant(_value: str) -> None:
    raise ValueError('non-finite JSON value')


def _pairs_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _faiss_present() -> bool:
    for module_name in tuple(sys.modules):
        if module_name == 'faiss' or module_name.startswith('faiss.'):
            return True
    return False


def _read_request() -> dict[str, object]:
    try:
        stream = getattr(sys.stdin, 'buffer', None)
        if stream is not None:
            raw_value = stream.read(_MAX_INPUT_BYTES + 1)
        else:
            raw_value = sys.stdin.read(_MAX_INPUT_BYTES + 1).encode('utf-8')
    except Exception:
        raise ValueError('invalid worker request') from None
    if isinstance(raw_value, str):
        try:
            raw_value = raw_value.encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError('invalid worker request') from None
    if not isinstance(raw_value, (bytes, bytearray)):
        raise ValueError('invalid worker request')
    raw = bytes(raw_value)
    if len(raw) > _MAX_INPUT_BYTES:
        raise ValueError('worker request too large')
    try:
        request_text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError('invalid worker request') from None
    try:
        request = json.loads(
            request_text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (TypeError, ValueError):
        raise ValueError('invalid worker request') from None
    if type(request) is not dict:
        raise ValueError('invalid worker request')
    return request


def _validate_request(
    request: dict[str, object],
) -> tuple[list[str], Path, Path, int]:
    expected_fields = {'texts', 'model_dir', 'manifest_path', 'timeout_seconds'}
    if set(request.keys()) != expected_fields:
        raise ValueError('invalid worker request')
    texts = request['texts']
    if not isinstance(texts, list):
        raise ValueError('invalid worker request')
    if not 1 <= len(texts) <= _MAX_TEXTS:
        raise ValueError('invalid worker request')
    checked_texts: list[str] = []
    for text in texts:
        if not isinstance(text, str):
            raise ValueError('invalid worker request')
        if not text.strip():
            raise ValueError('invalid worker request')
        if len(text) > _MAX_TEXT_CHARS:
            raise ValueError('invalid worker request')
        checked_texts.append(text)
    model_dir_value = request['model_dir']
    manifest_path_value = request['manifest_path']
    if not isinstance(model_dir_value, str) or not model_dir_value.strip():
        raise ValueError('invalid worker request')
    if not isinstance(manifest_path_value, str) or not manifest_path_value.strip():
        raise ValueError('invalid worker request')
    timeout_seconds = request['timeout_seconds']
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int):
        raise ValueError('invalid worker request')
    if not 1 <= timeout_seconds <= 30:
        raise ValueError('invalid worker request')
    try:
        model_dir = Path(model_dir_value)
        manifest_path = Path(manifest_path_value)
    except (TypeError, ValueError):
        raise ValueError('invalid worker request') from None
    return checked_texts, model_dir, manifest_path, timeout_seconds


def _load_local_embeddings() -> object:
    package_name = _COMPONENT_PACKAGE_NAME
    package_dir = _COMPONENT_PACKAGE_DIR
    package_init_path = _COMPONENT_PACKAGE_INIT_PATH
    cached_package = sys.modules.get(package_name)
    if cached_package is not None:
        cached_file = getattr(cached_package, '__file__', None)
        if cached_file is None or Path(cached_file).resolve() != package_init_path:
            raise RuntimeError('local embeddings unavailable')
    else:
        spec = importlib.util.spec_from_file_location(
            package_name,
            package_init_path,
            submodule_search_locations=[str(package_dir)],
        )
        if spec is None or spec.loader is None:
            raise RuntimeError('local embeddings unavailable')
        package = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = package
        try:
            spec.loader.exec_module(package)
        except BaseException:
            sys.modules.pop(package_name, None)
            raise
    component = importlib.import_module(_COMPONENT_MODULE_NAME)

    @contextlib.contextmanager
    def _component_call():
        install_audit_hook = getattr(component, '_install_audit_hook', None)
        if callable(install_audit_hook):
            install_audit_hook()
        guard = _embedding_runtime_guard()
        guard.assert_compatible('embedding')
        finder = getattr(guard, '_FINDER', None)
        finder_index = None
        if finder is not None:
            for index, candidate in enumerate(sys.meta_path):
                if candidate is finder:
                    finder_index = index
                    break
        if finder_index is not None:
            del sys.meta_path[finder_index]
        try:
            yield
        finally:
            if finder_index is not None:
                sys.meta_path.insert(finder_index, finder)
            guard.assert_compatible('embedding')

    class _LocalEmbeddings(component.ComponentEmbeddings):
        def __init__(self, model_dir, manifest_path):
            with _component_call():
                component.ComponentEmbeddings.__init__(
                    self, model_dir, manifest_path
                )

        def encode(self, texts):
            with _component_call():
                return component.ComponentEmbeddings.encode(self, texts)

    return types.SimpleNamespace(LocalEmbeddings=_LocalEmbeddings)


def _validated_vectors(encoded: object, expected_count: int) -> list[list[float]]:
    tolist = getattr(encoded, 'tolist', None)
    try:
        vectors = tolist() if callable(tolist) else encoded
    except Exception:
        raise RuntimeError('local embeddings failed') from None
    if not isinstance(vectors, list):
        raise RuntimeError('local embeddings returned invalid vectors')
    if len(vectors) != expected_count:
        raise RuntimeError('local embeddings returned invalid vectors')
    converted_vectors: list[list[float]] = []
    for vector in vectors:
        if not isinstance(vector, list) or len(vector) != _EMBEDDING_DIM:
            raise RuntimeError('local embeddings returned invalid vectors')
        converted_vector: list[float] = []
        nonzero = False
        for component in vector:
            if isinstance(component, bool) or not isinstance(component, (int, float)):
                raise RuntimeError('local embeddings returned invalid vectors')
            try:
                value = float(component)
            except (TypeError, ValueError, OverflowError):
                raise RuntimeError('local embeddings returned invalid vectors') from None
            if not math.isfinite(value):
                raise RuntimeError('local embeddings returned invalid vectors')
            if value != 0.0:
                nonzero = True
            converted_vector.append(value)
        if not nonzero:
            raise RuntimeError('local embeddings returned invalid vectors')
        converted_vectors.append(converted_vector)
    return converted_vectors


def _embedding_runtime_guard():
    name = '_gwa_embedding_runtime_guard'
    guard_path = Path(__file__).resolve().with_name('native_runtime_guard.py')
    cached = sys.modules.get(name)
    if cached is not None:
        cached_file = getattr(cached, '__file__', None)
        if cached_file is None or Path(cached_file).resolve() != guard_path:
            raise RuntimeError('runtime guard unavailable')
        return cached
    spec = importlib.util.spec_from_file_location(name, guard_path)
    if spec is None or spec.loader is None:
        raise RuntimeError('runtime guard unavailable')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard_file = getattr(guard, '__file__', None)
    if guard_file is None or Path(guard_file).resolve() != guard_path:
        raise RuntimeError('runtime guard unavailable')
    sys.modules[name] = guard
    return guard


def _run_embedding(
    texts: list[str],
    model_dir: Path,
    manifest_path: Path,
) -> list[list[float]]:
    guard = _embedding_runtime_guard()
    guard.install_guard('embedding')
    guard.assert_compatible('embedding')
    if _faiss_present():
        raise RuntimeError('faiss must not be loaded')
    module = _load_local_embeddings()
    guard.assert_compatible('embedding')
    if _faiss_present():
        raise RuntimeError('faiss must not be loaded')
    embeddings_class = getattr(module, 'LocalEmbeddings', None)
    if not callable(embeddings_class):
        raise RuntimeError('local embeddings unavailable')
    embedder = embeddings_class(model_dir, manifest_path)
    guard.assert_compatible('embedding')
    if _faiss_present():
        raise RuntimeError('faiss must not be loaded')
    try:
        identity = embedder.identity
    except Exception:
        raise RuntimeError('local embeddings unavailable') from None
    if identity != IDENTITY:
        raise RuntimeError('local embeddings unavailable')
    encoded = embedder.encode(list(texts))
    guard.assert_compatible('embedding')
    if _faiss_present():
        raise RuntimeError('faiss must not be loaded')
    vectors = _validated_vectors(encoded, len(texts))
    if _faiss_present():
        raise RuntimeError('faiss must not be loaded')
    return vectors


def _success_json(vectors: list[list[float]]) -> str:
    document = {
        'ok': True,
        'identity': IDENTITY,
        'pid': os.getpid(),
        'vectors': vectors,
        'faiss_loaded': False,
        'torch_loaded': 'torch' in sys.modules,
    }
    return json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        separators=(',', ':'),
    )


def _emit_error() -> None:
    try:
        text = json.dumps(
            {'ok': False, 'error': 'embedding_worker_failed'},
            separators=(',', ':'),
        )
        sys.stdout.write(text)
        sys.stdout.flush()
    except BaseException:
        pass


def main() -> int:
    try:
        request = _read_request()
        texts, model_dir, manifest_path, timeout_seconds = _validate_request(request)
    except BaseException:
        _emit_error()
        return 1

    try:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.alarm(timeout_seconds)
    except BaseException:
        _emit_error()
        return 1

    try:
        try:
            vectors = _run_embedding(texts, model_dir, manifest_path)
            output_text = _success_json(vectors)
        except BaseException:
            _emit_error()
            return 1
    finally:
        try:
            signal.alarm(0)
        except BaseException:
            pass

    try:
        sys.stdout.write(output_text)
        sys.stdout.flush()
    except BaseException:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
