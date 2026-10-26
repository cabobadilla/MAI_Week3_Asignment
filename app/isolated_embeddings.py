'''Process-isolated local embedding transport.'''

import json
import math
import os
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path


MODEL_ID = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MODEL_REVISION = 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
IDENTITY = MODEL_ID + '@' + MODEL_REVISION

_MAX_TEXTS = 10_000
_MAX_TEXT_CHARS = 2_000
_MAX_INPUT_BYTES = 32 * 1024 * 1024
_MAX_RESPONSE_BYTES = 128 * 1024 * 1024
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_EMBEDDING_DIM = 384
_ERROR_MESSAGE = 'embedding worker failed'


class EmbeddingWorkerError(RuntimeError):
    '''Raised when the isolated worker cannot produce a valid result.'''

    retryable = False

    def __init__(self, message: str = _ERROR_MESSAGE) -> None:
        super().__init__(message)
        self.retryable = False


def _reject_constant(_value: str) -> None:
    raise ValueError('non-finite JSON value')


def _pairs_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _read_manifest_header(path: Path) -> dict[str, object]:
    try:
        if not path.is_file():
            raise ValueError('invalid embedding manifest')
        if path.stat().st_size > _MAX_MANIFEST_BYTES:
            raise ValueError('invalid embedding manifest')
        raw = path.read_bytes()
    except OSError:
        raise ValueError('invalid embedding manifest') from None
    if len(raw) > _MAX_MANIFEST_BYTES:
        raise ValueError('invalid embedding manifest')
    try:
        header = json.loads(
            raw.decode('utf-8'),
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, TypeError, ValueError):
        raise ValueError('invalid embedding manifest') from None
    if type(header) is not dict:
        raise ValueError('invalid embedding manifest')
    return header


def _validate_manifest(path: Path) -> None:
    header = _read_manifest_header(path)
    if header.get('model_id') != MODEL_ID or header.get('revision') != MODEL_REVISION:
        raise ValueError('unsupported embedding manifest')


def _normalize_timeout(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError('invalid embedding timeout')
    if isinstance(value, int):
        timeout_seconds = value
    elif isinstance(value, float) and value.is_integer():
        timeout_seconds = int(value)
    else:
        raise ValueError('invalid embedding timeout')
    if not 1 <= timeout_seconds <= 30:
        raise ValueError('invalid embedding timeout')
    return timeout_seconds


def _validate_texts(texts: list[str]) -> list[str]:
    if not isinstance(texts, list):
        raise ValueError('invalid embedding texts')
    if not 1 <= len(texts) <= _MAX_TEXTS:
        raise ValueError('invalid embedding texts')
    checked: list[str] = []
    for text in texts:
        if not isinstance(text, str):
            raise ValueError('invalid embedding texts')
        if not text.strip():
            raise ValueError('invalid embedding texts')
        if len(text) > _MAX_TEXT_CHARS:
            raise ValueError('invalid embedding texts')
        checked.append(text)
    return checked


def _worker_command() -> list[str]:
    worker_path = Path(__file__).resolve().with_name('embedding_worker.py')
    return [sys.executable, '-I', '-B', str(worker_path)]


def _reject_unsafe_path(path: Path) -> None:
    try:
        text = os.fspath(path)
    except TypeError:
        raise ValueError('invalid embedding configuration') from None
    if not isinstance(text, str):
        raise ValueError('invalid embedding configuration')
    if '\x00' in text or '\n' in text or '\r' in text:
        raise ValueError('invalid embedding configuration')


def _resolve_manifest_path(path: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        raise ValueError('invalid embedding manifest') from None
    _validate_manifest(resolved)
    return resolved


def _validate_model_directory(model_dir: Path, manifest_path: Path) -> Path:
    try:
        resolved = model_dir.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        raise ValueError('invalid embedding configuration') from None
    try:
        if not resolved.is_dir():
            raise ValueError('invalid embedding configuration')
    except OSError:
        raise ValueError('invalid embedding configuration') from None
    protected_paths = [
        Path('/'),
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
        Path(sys.prefix).resolve(),
        manifest_path,
        Path('/Users'),
        Path('/private/tmp'),
        Path('/private/var'),
        Path('/Volumes'),
        Path('/Library/Keychains'),
        Path('/Library/Application Support'),
        Path('/opt/homebrew/etc'),
        Path('/opt/homebrew/var'),
    ]
    try:
        protected_paths.append(Path.home().resolve())
    except (OSError, RuntimeError):
        pass
    for protected_path in protected_paths:
        if resolved == protected_path or resolved in protected_path.parents:
            raise ValueError('invalid embedding configuration')
    return resolved


def _sandbox_literal(path: Path) -> str:
    try:
        text = str(path.resolve())
    except (OSError, RuntimeError, ValueError):
        raise ValueError('invalid sandbox path') from None
    if '\x00' in text or '\n' in text or '\r' in text:
        raise ValueError('invalid sandbox path')
    return json.dumps(text)


def _sandbox_profile(
    model_dir: Path,
    manifest_path: Path,
    scratch: Path,
) -> str:
    app_dir = Path(__file__).resolve().parent
    venv_dir = Path(sys.prefix).resolve()
    purelib_dir = Path(sysconfig.get_paths()['purelib']).resolve()
    model_path = Path(model_dir).resolve()
    manifest_file = Path(manifest_path).resolve()
    scratch_path = Path(scratch).resolve()

    denied_read_roots = (
        Path('/Users'),
        Path('/private/tmp'),
        Path('/private/var'),
        Path('/Volumes'),
        Path('/Library/Keychains'),
        Path('/Library/Application Support'),
        Path('/opt/homebrew/etc'),
        Path('/opt/homebrew/var'),
    )
    denied_read_line = '(deny file-read-data ' + ' '.join(
        '(subpath ' + _sandbox_literal(path) + ')' for path in denied_read_roots
    ) + ')'
    lines = [
        '(version 1)',
        '(allow default)',
        '(deny network*)',
        '(deny file-write*)',
        '(allow file-write* (literal ' + _sandbox_literal(Path('/dev/null')) + ') (subpath ' + _sandbox_literal(scratch_path) + '))',
        denied_read_line,
        '(allow file-read-data (subpath ' + _sandbox_literal(venv_dir) + '))',
        '(allow file-read-data (subpath ' + _sandbox_literal(app_dir) + '))',
        '(allow file-read-data (subpath ' + _sandbox_literal(model_path) + '))',
        '(allow file-read-data (subpath ' + _sandbox_literal(scratch_path) + '))',
        '(allow file-read-data (literal ' + _sandbox_literal(manifest_file) + ') (subpath ' + _sandbox_literal(Path('/private/var/db/dyld')) + '))',
        '(deny mach-lookup (global-name "com.apple.securityd") (global-name "com.apple.securityd.xpc") (global-name "com.apple.accountsd.accountmanager"))',
        '(deny file-read* (subpath ' + _sandbox_literal(purelib_dir / 'sklearn') + '))',
        '(deny file-read* (subpath ' + _sandbox_literal(purelib_dir / 'faiss') + '))',
    ]
    return '\n'.join(lines) + '\n'


def _minimal_environment(temporary_directory: str) -> dict[str, str]:
    trusted_path = os.environ.get('PATH') or os.defpath
    return {
        'PATH': trusted_path,
        'HOME': temporary_directory,
        'TMPDIR': temporary_directory,
        'HF_HOME': temporary_directory,
        'HF_HUB_OFFLINE': '1',
        'TRANSFORMERS_OFFLINE': '1',
        'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1',
        'HF_HUB_DISABLE_TELEMETRY': '1',
        'TOKENIZERS_PARALLELISM': 'false',
        'OMP_NUM_THREADS': '1',
        'OPENBLAS_NUM_THREADS': '1',
    }


def _decode_response(stdout: object) -> dict[str, object]:
    if isinstance(stdout, (bytes, bytearray)):
        raw_bytes = bytes(stdout)
        if len(raw_bytes) > _MAX_RESPONSE_BYTES:
            raise EmbeddingWorkerError()
        try:
            response_text = raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            raise EmbeddingWorkerError() from None
    elif isinstance(stdout, str):
        if len(stdout) > _MAX_RESPONSE_BYTES:
            raise EmbeddingWorkerError()
        try:
            raw_bytes = stdout.encode('utf-8')
        except UnicodeEncodeError:
            raise EmbeddingWorkerError() from None
        if len(raw_bytes) > _MAX_RESPONSE_BYTES:
            raise EmbeddingWorkerError()
        response_text = stdout
    else:
        raise EmbeddingWorkerError()
    try:
        response = json.loads(
            response_text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (TypeError, ValueError):
        raise EmbeddingWorkerError() from None
    if type(response) is not dict:
        raise EmbeddingWorkerError()
    return response


def _parse_response(
    stdout: object,
    process: object,
    expected_count: int,
) -> list[list[float]]:
    response = _decode_response(stdout)
    if response.get('ok') is not True:
        raise EmbeddingWorkerError()
    if response.get('identity') != IDENTITY:
        raise EmbeddingWorkerError()
    worker_pid = response.get('pid')
    if isinstance(worker_pid, bool) or not isinstance(worker_pid, int):
        raise EmbeddingWorkerError()
    try:
        process_pid = process.pid
    except Exception:
        raise EmbeddingWorkerError() from None
    if worker_pid != process_pid or worker_pid == os.getpid():
        raise EmbeddingWorkerError()
    if response.get('faiss_loaded') is not False:
        raise EmbeddingWorkerError()
    if response.get('torch_loaded') is not True:
        raise EmbeddingWorkerError()
    vectors = response.get('vectors')
    if type(vectors) is not list or len(vectors) != expected_count:
        raise EmbeddingWorkerError()
    converted_vectors: list[list[float]] = []
    for vector in vectors:
        if type(vector) is not list or len(vector) != _EMBEDDING_DIM:
            raise EmbeddingWorkerError()
        converted_vector: list[float] = []
        nonzero = False
        for component in vector:
            if isinstance(component, bool) or not isinstance(component, (int, float)):
                raise EmbeddingWorkerError()
            try:
                value = float(component)
            except (TypeError, ValueError, OverflowError):
                raise EmbeddingWorkerError() from None
            if not math.isfinite(value):
                raise EmbeddingWorkerError()
            if value != 0.0:
                nonzero = True
            converted_vector.append(value)
        if not nonzero:
            raise EmbeddingWorkerError()
        converted_vectors.append(converted_vector)
    return converted_vectors


class IsolatedEmbeddings:
    '''Transport embeddings across a dedicated local worker process.'''

    identity = IDENTITY

    def __init__(
        self,
        model_dir: Path,
        manifest_path: Path,
        *,
        timeout_seconds: int = 30,
    ) -> None:
        try:
            model_path = Path(model_dir)
            manifest_path_value = Path(manifest_path)
        except (TypeError, ValueError):
            raise ValueError('invalid embedding configuration') from None
        self.timeout_seconds = _normalize_timeout(timeout_seconds)
        _reject_unsafe_path(model_path)
        _reject_unsafe_path(manifest_path_value)
        self.manifest_path = _resolve_manifest_path(manifest_path_value)
        self.model_dir = _validate_model_directory(model_path, self.manifest_path)

    def encode(self, texts: list[str]) -> list[list[float]]:
        checked_texts = _validate_texts(texts)
        payload = {
            'texts': checked_texts,
            'model_dir': os.path.abspath(str(self.model_dir)),
            'manifest_path': os.path.abspath(str(self.manifest_path)),
            'timeout_seconds': self.timeout_seconds,
        }
        try:
            request_text = json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                separators=(',', ':'),
            )
            request_bytes = request_text.encode('utf-8')
        except (TypeError, ValueError, UnicodeEncodeError):
            raise ValueError('invalid embedding input') from None
        if len(request_bytes) > _MAX_INPUT_BYTES:
            raise ValueError('embedding input too large')

        command = _worker_command()
        with tempfile.TemporaryDirectory(prefix='isolated-embeddings-') as temporary_directory:
            try:
                scratch = Path(temporary_directory).resolve(strict=True)
                if not scratch.is_dir():
                    raise ValueError('invalid sandbox scratch')
                profile_path = scratch / 'worker.sb'
                profile_text = _sandbox_profile(
                    self.model_dir,
                    self.manifest_path,
                    scratch,
                )
                profile_path.write_text(profile_text, encoding='utf-8')
            except Exception:
                raise EmbeddingWorkerError() from None

            try:
                sandbox_available = (
                    Path('/usr/bin/sandbox-exec').is_file()
                    and os.access(Path('/usr/bin/sandbox-exec'), os.X_OK)
                )
            except Exception:
                raise EmbeddingWorkerError() from None
            if not sandbox_available:
                raise EmbeddingWorkerError()

            command = [
                '/usr/bin/sandbox-exec',
                '-f',
                str(profile_path),
            ] + command

            environment = _minimal_environment(temporary_directory)
            try:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=environment,
                    close_fds=True,
                    cwd=str(scratch),
                )
            except Exception:
                raise EmbeddingWorkerError() from None

            try:
                stdout, _stderr = process.communicate(
                    input=request_text,
                    timeout=self.timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except Exception:
                    pass
                try:
                    process.wait()
                except Exception:
                    pass
                raise EmbeddingWorkerError() from None
            except Exception:
                raise EmbeddingWorkerError() from None

            try:
                return_code = process.returncode
            except Exception:
                raise EmbeddingWorkerError() from None
            if return_code != 0:
                raise EmbeddingWorkerError() from None

            try:
                return _parse_response(stdout, process, len(checked_texts))
            except EmbeddingWorkerError:
                raise
            except Exception:
                raise EmbeddingWorkerError() from None
