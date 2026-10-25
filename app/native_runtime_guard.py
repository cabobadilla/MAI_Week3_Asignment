'''Pre-import Python runtime guard for native-backed embedding/vector stacks.

This module installs a process-local ``sys.meta_path`` finder that rejects
imports of selected top-level Python package roots for a chosen runtime role:

* ``embedding`` blocks ``faiss`` and ``sklearn``, including dotted submodules.
  ``torch`` and ``sentence_transformers`` remain allowed.
* ``vector`` blocks ``torch``, ``sentence_transformers``, and ``sklearn``,
  including dotted submodules. ``faiss`` remains allowed.

``sklearn`` is intentionally blocked for both roles until the transitive
OpenMP audit is resolved. This guard does not claim that an embedding model or
any other runtime is ready.

Limitations: this is an in-process Python import guard only. It does not
provide a security sandbox, process isolation, filesystem or network
restrictions, or an exclusive physical OpenMP guarantee. Native code can still
be loaded through ``ctypes``/``cffi``/``dlopen``, subprocesses, preloaded or
already-loaded extension modules, or transitive dependencies that do not
import one of the guarded top-level Python names. It guards Python import
attempts made through ``sys.meta_path`` in this process; it does not inspect,
unload, or otherwise control native libraries or their dependencies.
'''

import sys
import threading

__all__ = [
    'NativeRuntimeConflict',
    'install_guard',
    'current_role',
    'assert_compatible',
]

_ALLOWED_ROLES = ('embedding', 'vector')
_FORBIDDEN_ROOTS = {
    'embedding': ('faiss', 'sklearn'),
    'vector': ('torch', 'sentence_transformers', 'sklearn'),
}
_KNOWN_ROOTS = ('torch', 'faiss', 'sentence_transformers', 'sklearn')

_LOCK = threading.RLock()
_ROLE = None
_FINDER = None


class NativeRuntimeConflict(ImportError):
    '''Raised when a native-runtime import or role is incompatible.'''


def _validate_role(role):
    if not isinstance(role, str) or role not in _ALLOWED_ROLES:
        raise ValueError('role must be exactly embedding or vector')


def _matches_root(name, root):
    return name == root or name.startswith(root + '.')


def _find_conflict(role):
    forbidden = _FORBIDDEN_ROOTS[role]
    for name in list(sys.modules):
        if not isinstance(name, str):
            continue
        for root in forbidden:
            if _matches_root(name, root):
                return name
    return None


class _NativeRuntimeGuardFinder:
    '''Meta-path finder that enforces the installed role for native families.'''

    _native_runtime_guard_finder = True

    def __init__(self, role):
        self._role = role

    def find_spec(self, fullname, path=None, target=None):
        role = self._role
        if any(_matches_root(fullname, r) for r in _KNOWN_ROOTS):
            if _find_conflict(role) is not None:
                raise NativeRuntimeConflict(
                    "Native runtime conflict detected"
                )
        for root in _KNOWN_ROOTS:
            if _matches_root(fullname, root):
                if root in _FORBIDDEN_ROOTS[role]:
                    raise NativeRuntimeConflict(
                        'prohibited import for role %s: %s' % (role, fullname)
                    )
                return None
        return None


def install_guard(role: str) -> None:
    '''Install the one process-wide guard finder for ``role``.'''
    global _ROLE, _FINDER
    _validate_role(role)
    with _LOCK:
        if _ROLE is not None and _ROLE != role:
            raise NativeRuntimeConflict(
                'a native runtime guard is already installed for another role'
            )
        if _find_conflict(role) is not None:
            raise NativeRuntimeConflict(
                'a prohibited native module is already present in sys.modules'
            )
        if _ROLE == role:
            finder = _FINDER
            if finder is not None and not any(
                item is finder for item in sys.meta_path
            ):
                sys.meta_path.insert(0, finder)
            return
        finder = _NativeRuntimeGuardFinder(role)
        sys.meta_path.insert(0, finder)
        _FINDER = finder
        _ROLE = role


def current_role() -> str | None:
    '''Return the installed role, or ``None`` before installation.'''
    with _LOCK:
        return _ROLE


def assert_compatible(role: str) -> None:
    '''Raise if ``role`` is not installed or prohibited modules are present.'''
    _validate_role(role)
    with _LOCK:
        if _ROLE != role or _find_conflict(role) is not None:
            raise NativeRuntimeConflict('native runtime compatibility check failed')
