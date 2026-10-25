'''Pure-stdlib file-map guard.

This module parses and writes coordinator-owned .py file maps. It never
runs, imports, or interprets file content, and it does not use commands,
the network, credentials, or environment variables.

Only .py paths are accepted and forbidden or hidden parts are rejected.
apply_filemap assumes the coordinator is the single writer for the
targets it changes. It checks containment, symlinks, hardlinks, and
expected hashes again before commit, creates missing parent directories
inside the root when needed, and rolls back destinations and any newly
created directories when a later commit fails. Limits: an adversarial
concurrent OS writer can still win a time-of-check/time-of-use race
between the last check and os.replace, or replace a checked parent
directory. Use an external lock and restrictive directory permissions
for such an adversary.

The public functions do not mutate expected_base.
'''

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
from pathlib import Path

_MAX_FILE = 250000
_MAX_TOTAL = 1000000
_NUL = chr(0)
_BACKSLASH = chr(92)
_FORBIDDEN = frozenset({'.git', '.env', 'dot', 'docs', 'tests'})
_CHUNK = 1024 * 1024


def _root_dir(root: Path) -> Path:
    try:
        root = Path(root)
        st = os.lstat(root)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise ValueError('root does not exist') from exc
    except (TypeError, ValueError) as exc:
        raise ValueError('root must be a path') from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise ValueError('root must be a real directory')
    try:
        resolved = root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError('root cannot be resolved') from exc
    st = os.lstat(resolved)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise ValueError('root must be a real directory')
    return resolved


def _parts(path: object) -> tuple[str, ...]:
    if type(path) is not str:
        raise ValueError('path must be a string')
    if path == '' or _NUL in path:
        raise ValueError('invalid path')
    try:
        path.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise ValueError('path is not valid UTF-8') from exc
    if path.startswith('/') or _BACKSLASH in path or ':' in path:
        raise ValueError(f'absolute, drive, or backslash path: {path!r}')
    parts = path.split('/')
    if any(part == '' for part in parts):
        raise ValueError(f'empty path segment: {path!r}')
    for part in parts:
        if part in ('.', '..'):
            raise ValueError(f'dot path segment: {path!r}')
        if part.startswith('.'):
            raise ValueError(f'hidden path segment: {path!r}')
        if part.casefold() in _FORBIDDEN:
            raise ValueError(f'forbidden path segment: {path!r}')
    if not parts[-1].endswith('.py'):
        raise ValueError(f'only .py paths are allowed: {path!r}')
    return tuple(parts)


def _within(root: Path, target: Path) -> bool:
    root_s = os.path.normcase(os.path.abspath(os.fspath(root)))
    target_s = os.path.normcase(os.path.abspath(os.fspath(target)))
    try:
        return os.path.commonpath((root_s, target_s)) == root_s
    except ValueError:
        return False


def _remove_created_dirs(dirs: list[Path]) -> None:
    for directory in reversed(dirs):
        try:
            os.rmdir(directory)
        except OSError:
            pass


def _ensure_parent_dirs(root: Path, path: str) -> list[Path]:
    parts = _parts(path)
    current = root
    created: list[Path] = []
    try:
        for part in parts[:-1]:
            nxt = current / part
            if not _within(root, nxt):
                raise ValueError(f'path escapes root: {path!r}')
            try:
                st = os.lstat(nxt)
            except FileNotFoundError:
                try:
                    os.mkdir(nxt, 0o777)
                except FileExistsError:
                    try:
                        st = os.lstat(nxt)
                    except FileNotFoundError as exc:
                        raise ValueError(f'parent disappeared for {path!r}') from exc
                except OSError as exc:
                    if exc.errno == errno.ELOOP:
                        raise ValueError(f'symlink parent for {path!r}') from exc
                    raise
                else:
                    created.append(nxt)
                    current = nxt
                    continue
            if stat.S_ISLNK(st.st_mode):
                raise ValueError(f'symlink parent for {path!r}')
            if not stat.S_ISDIR(st.st_mode):
                raise ValueError(f'non-directory parent for {path!r}')
            current = nxt
    except BaseException:
        _remove_created_dirs(created)
        raise
    return created


def _target(root: Path, path: str, require_parents: bool) -> Path:
    parts = _parts(path)
    current = root
    for part in parts[:-1]:
        nxt = current / part
        try:
            st = os.lstat(nxt)
        except FileNotFoundError:
            if require_parents:
                raise ValueError(f'missing parent directory for {path!r}')
            break
        if stat.S_ISLNK(st.st_mode):
            raise ValueError(f'symlink parent for {path!r}')
        if not stat.S_ISDIR(st.st_mode):
            raise ValueError(f'non-directory parent for {path!r}')
        current = nxt
    target = root.joinpath(*parts)
    if not _within(root, target):
        raise ValueError(f'path escapes root: {path!r}')
    try:
        resolved = target.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f'cannot resolve path: {path!r}') from exc
    if not _within(root, resolved):
        raise ValueError(f'path escapes root: {path!r}')
    return target


def _regular_stat(path: Path, rel: str) -> os.stat_result | None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    except NotADirectoryError as exc:
        raise ValueError(f'invalid path: {rel!r}') from exc
    if stat.S_ISLNK(st.st_mode):
        raise ValueError(f'symlink file: {rel!r}')
    if not stat.S_ISREG(st.st_mode):
        raise ValueError(f'not a regular file: {rel!r}')
    if st.st_nlink != 1:
        raise ValueError(f'hardlinked file: {rel!r}')
    return st


def _read_file(path: Path, rel: str) -> bytes | None:
    st = _regular_stat(path, rel)
    if st is None:
        return None
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError(f'symlink file: {rel!r}') from exc
        raise
    try:
        fst = os.fstat(fd)
        if stat.S_ISLNK(fst.st_mode) or not stat.S_ISREG(fst.st_mode) or fst.st_nlink != 1:
            raise ValueError(f'unsafe file: {rel!r}')
        if fst.st_dev != st.st_dev or fst.st_ino != st.st_ino:
            raise ValueError(f'file changed while opening: {rel!r}')
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, _CHUNK)
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks)
    finally:
        os.close(fd)


def _hash(data: bytes | None) -> str | None:
    if data is None:
        return None
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path, paths: list[str]) -> dict[str, str | None]:
    '''Return SHA256 hex strings for regular files, or None when missing.'''
    real = _root_dir(root)
    if type(paths) is not list:
        raise ValueError('paths must be a list')
    seen: set[str] = set()
    out: dict[str, str | None] = {}
    for path in paths:
        _parts(path)
        folded = path.casefold()
        if folded in seen:
            raise ValueError(f'duplicate path: {path!r}')
        seen.add(folded)
        target = _target(real, path, False)
        out[path] = _hash(_read_file(target, path))
    return out


def _allowed(root: Path, allowed_paths: list[str]) -> set[str]:
    if type(allowed_paths) is not list:
        raise ValueError('allowed_paths must be a list')
    seen: set[str] = set()
    allowed: set[str] = set()
    for path in allowed_paths:
        _parts(path)
        folded = path.casefold()
        if folded in seen:
            raise ValueError(f'duplicate allowlist path: {path!r}')
        seen.add(folded)
        allowed.add(path)
        target = _target(root, path, False)
        _regular_stat(target, path)
    return allowed


def validate_filemap(
    text: str,
    allowed_paths: list[str],
    root: Path,
) -> dict[str, str]:
    '''Return the validated path-to-content map or raise ValueError.'''
    if type(text) is not str or _NUL in text:
        raise ValueError('text must be a NUL-free string')

    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        obj: dict[str, object] = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError(f'duplicate JSON key: {key!r}')
            obj[key] = value
        return obj

    try:
        doc = json.loads(text, object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('invalid JSON') from exc
    if type(doc) is not dict or set(doc.keys()) != {'files'}:
        raise ValueError('JSON must have exactly the files key')
    files = doc['files']
    if type(files) is not list:
        raise ValueError('files must be a list')
    real = _root_dir(root)
    allowed = _allowed(real, allowed_paths)
    result: dict[str, str] = {}
    seen_paths: set[str] = set()
    total = 0
    for item in files:
        if type(item) is not dict or set(item.keys()) != {'path', 'content'}:
            raise ValueError('each file must have exactly path and content')
        path = item['path']
        content = item['content']
        if type(path) is not str or type(content) is not str:
            raise ValueError('path and content must be strings')
        _parts(path)
        folded = path.casefold()
        if folded in seen_paths:
            raise ValueError(f'duplicate path: {path!r}')
        seen_paths.add(folded)
        if path not in allowed:
            raise ValueError(f'path is not in the allowlist: {path!r}')
        if _NUL in content:
            raise ValueError(f'NUL in content: {path!r}')
        try:
            data = content.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise ValueError(f'content is not valid UTF-8: {path!r}') from exc
        if len(data) > _MAX_FILE:
            raise ValueError(f'file too large: {path!r}')
        total += len(data)
        if total > _MAX_TOTAL:
            raise ValueError('file map is too large')
        target = _target(real, path, False)
        _regular_stat(target, path)
        result[path] = content
    return result


def _prepare_mapping(root: Path, mapping: dict[str, str]) -> list[tuple[str, bytes, Path]]:
    if type(mapping) is not dict:
        raise ValueError('mapping must be a dict')
    seen: set[str] = set()
    total = 0
    prepared: list[tuple[str, bytes, Path]] = []
    for path, content in mapping.items():
        if type(path) is not str or type(content) is not str:
            raise ValueError('mapping keys and values must be strings')
        _parts(path)
        folded = path.casefold()
        if folded in seen:
            raise ValueError(f'duplicate path: {path!r}')
        seen.add(folded)
        if _NUL in content:
            raise ValueError(f'NUL in content: {path!r}')
        try:
            data = content.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise ValueError(f'content is not valid UTF-8: {path!r}') from exc
        if len(data) > _MAX_FILE:
            raise ValueError(f'file too large: {path!r}')
        total += len(data)
        if total > _MAX_TOTAL:
            raise ValueError('file map is too large')
        target = _target(root, path, False)
        _regular_stat(target, path)
        prepared.append((path, data, target))
    return prepared


def _expected_values(
    expected_base: dict[str, str | None],
    paths: list[str],
) -> dict[str, str | None]:
    if type(expected_base) is not dict:
        raise ValueError('expected_base must be a dict')
    values: dict[str, str | None] = {}
    for path in paths:
        if path not in expected_base:
            raise ValueError(f'expected_base is missing {path!r}')
        value = expected_base[path]
        if value is not None and type(value) is not str:
            raise ValueError(f'invalid expected hash for {path!r}')
        values[path] = value
    return values


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError('short write while staging')
        view = view[written:]


def _unlink_quiet(path: Path) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def _stage(parent: Path, data: bytes) -> Path:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, 'O_NOFOLLOW', 0)
        | getattr(os, 'O_BINARY', 0)
    )
    for _ in range(32):
        candidate = parent / ('.filemap-' + os.urandom(12).hex() + '.tmp')
        try:
            fd = os.open(candidate, flags, 0o666)
        except FileExistsError:
            continue
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise ValueError('unsafe temporary path') from exc
            raise
        try:
            _write_all(fd, data)
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            _unlink_quiet(candidate)
            raise
        try:
            os.close(fd)
        except OSError:
            _unlink_quiet(candidate)
            raise
        return candidate
    raise OSError('could not create a temporary file')


def _direct_restore(root: Path, path: str, target: Path, data: bytes) -> None:
    _target(root, path, True)
    _regular_stat(target, path)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_TRUNC
        | getattr(os, 'O_NOFOLLOW', 0)
        | getattr(os, 'O_BINARY', 0)
    )
    fd = os.open(target, flags, 0o666)
    try:
        fst = os.fstat(fd)
        if stat.S_ISLNK(fst.st_mode) or not stat.S_ISREG(fst.st_mode) or fst.st_nlink != 1:
            raise ValueError(f'unsafe rollback file: {path!r}')
        _write_all(fd, data)
    finally:
        os.close(fd)


def _restore(root: Path, path: str, target: Path, original: bytes | None) -> None:
    _target(root, path, True)
    if original is None:
        try:
            os.unlink(target)
        except FileNotFoundError:
            pass
        return
    temp = _stage(target.parent, original)
    try:
        os.replace(temp, target)
    except Exception:
        _unlink_quiet(temp)
        _direct_restore(root, path, target, original)


def _rollback(
    root: Path,
    touched: list[tuple[str, Path, bytes | None]],
) -> list[tuple[str, BaseException]]:
    errors: list[tuple[str, BaseException]] = []
    for path, target, original in reversed(touched):
        try:
            _restore(root, path, target, original)
        except BaseException as exc:
            errors.append((path, exc))
    return errors


def apply_filemap(
    mapping: dict[str, str],
    root: Path,
    expected_base: dict[str, str | None],
) -> dict[str, str]:
    '''Apply a validated mapping with atomic replaces and return post hashes.'''
    if type(expected_base) is not dict:
        raise ValueError('expected_base must be a dict')
    real = _root_dir(root)
    prepared = _prepare_mapping(real, mapping)
    expected = _expected_values(expected_base, [item[0] for item in prepared])
    originals: dict[str, bytes | None] = {}
    for path, _data, target in prepared:
        blob = _read_file(target, path)
        originals[path] = blob
        if _hash(blob) != expected[path]:
            raise ValueError(f'stale expected_base or changed file: {path!r}')
    created_dirs: list[Path] = []
    staged: list[tuple[str, bytes, Path, Path]] = []
    succeeded = False
    try:
        for path, _data, _dest in prepared:
            created_dirs.extend(_ensure_parent_dirs(real, path))
        for path, _data, target in prepared:
            target = _target(real, path, True)
            blob = _read_file(target, path)
            if _hash(blob) != expected[path]:
                raise ValueError(f'stale expected_base or changed file: {path!r}')
        for path, data, target in prepared:
            staged.append((path, data, target, _stage(target.parent, data)))
        for path, _data, target, _temp in staged:
            _target(real, path, True)
            blob = _read_file(target, path)
            if _hash(blob) != expected[path]:
                raise ValueError(f'stale expected_base or changed file: {path!r}')
        touched: list[tuple[str, Path, bytes | None]] = []
        try:
            for path, _data, target, temp in staged:
                _target(real, path, True)
                blob = _read_file(target, path)
                if _hash(blob) != expected[path]:
                    raise ValueError(f'stale expected_base or changed file: {path!r}')
                os.replace(temp, target)
                touched.append((path, target, originals[path]))
        except BaseException as exc:
            for path, rollback_exc in _rollback(real, touched):
                exc.add_note(f'rollback failed for {path!r}: {rollback_exc!r}')
            raise
        result = {
            path: hashlib.sha256(data).hexdigest()
            for path, data, _tgt, _tmp in staged
        }
        succeeded = True
        return result
    finally:
        for _path, _data, _dest, temp in staged:
            _unlink_quiet(temp)
        if not succeeded:
            _remove_created_dirs(created_dirs)
