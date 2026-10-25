'''Core operator authentication backend.

This module provides password setup and login/session primitives only.
HTTP routing, cookie handling, CSRF/Origin request checks, and UI code are
outside this module's scope.
'''

from __future__ import annotations

import hashlib
import secrets
import sqlite3
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

__all__ = ['AuthService']

_INVALID_CREDENTIALS = 'Invalid credentials'
_PASSWORD_ALREADY_SET = 'Operator password is already configured'


class AuthService:
    _DB_TIMEOUT_SECONDS = 5.0
    _MIN_PASSWORD_CODEPOINTS = 8
    _IDLE_TTL_SECONDS = 1800
    _ABSOLUTE_TTL_SECONDS = 28800
    _RATE_WINDOW_SECONDS = 300
    _RATE_MAX_FAILURES = 5
    _OPERATOR_IDENTIFIER = 'operator'

    def __init__(
        self,
        db_path: Path,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._db_path = Path(db_path)
        self._clock = clock
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=1,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )
        self._lock = threading.RLock()
        self._sessions: dict[str, dict[str, object]] = {}
        self._failures: dict[str, list[float]] = {}

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(
            str(self._db_path),
            timeout=self._DB_TIMEOUT_SECONDS,
        )

    def _updated_at(self) -> str:
        return datetime.fromtimestamp(
            float(self._clock()),
            tz=timezone.utc,
        ).isoformat()

    def setup(self, password: str, confirmation: str) -> None:
        if not isinstance(password, str) or not isinstance(confirmation, str):
            raise ValueError('Password must be a string')
        if password != confirmation:
            raise ValueError('Passwords do not match')
        if len(password) < self._MIN_PASSWORD_CODEPOINTS:
            raise ValueError('Password must contain at least 8 characters')
        if self.has_password():
            raise ValueError(_PASSWORD_ALREADY_SET)

        encoded_hash = self._hasher.hash(password)
        updated_at = self._updated_at()

        conn = self._connect()
        try:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute(
                'INSERT INTO operator_credentials '
                '(id, encoded_password_hash, updated_at) VALUES (?, ?, ?)',
                (1, encoded_hash, updated_at),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(_PASSWORD_ALREADY_SET) from None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def has_password(self) -> bool:
        conn = self._connect()
        try:
            row = conn.execute(
                'SELECT 1 FROM operator_credentials WHERE id = ? LIMIT 1',
                (1,),
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def _load_encoded_hash(self) -> str | None:
        conn = self._connect()
        try:
            row = conn.execute(
                'SELECT encoded_password_hash '
                'FROM operator_credentials WHERE id = ?',
                (1,),
            ).fetchone()
            if row is None:
                return None
            encoded_hash = row[0]
            return encoded_hash if isinstance(encoded_hash, str) else None
        finally:
            conn.close()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def _prune_rate_limits_locked(self, now: float) -> None:
        cutoff = now - self._RATE_WINDOW_SECONDS
        empty_clients: list[str] = []
        for client_id, timestamps in self._failures.items():
            fresh = [stamp for stamp in timestamps if stamp > cutoff]
            if fresh:
                self._failures[client_id] = fresh
            else:
                empty_clients.append(client_id)
        for client_id in empty_clients:
            del self._failures[client_id]

    def _check_rate_limit_locked(self, client_id: str, now: float) -> None:
        self._prune_rate_limits_locked(now)
        if len(self._failures.get(client_id, ())) >= self._RATE_MAX_FAILURES:
            raise ValueError(_INVALID_CREDENTIALS)

    def _issue_session_locked(self, now: float) -> tuple[str, str]:
        while True:
            token = secrets.token_urlsafe(32)
            token_hash = self._hash_token(token)
            if token_hash not in self._sessions:
                break
        csrf = secrets.token_urlsafe(32)
        self._sessions[token_hash] = {
            'operator': self._OPERATOR_IDENTIFIER,
            'csrf': csrf,
            'issued': now,
            'lastseen': now,
        }
        return token, csrf

    def login(
        self,
        password: str,
        client_id: str = 'local',
    ) -> dict[str, object]:
        now = float(self._clock())
        with self._lock:
            self._check_rate_limit_locked(client_id, now)

        encoded_hash = self._load_encoded_hash()
        valid = False
        if isinstance(password, str) and encoded_hash is not None:
            try:
                valid = bool(self._hasher.verify(encoded_hash, password))
            except (
                InvalidHashError,
                VerificationError,
                VerifyMismatchError,
            ):
                valid = False

        if not valid:
            with self._lock:
                self._failures.setdefault(client_id, []).append(now)
            raise ValueError(_INVALID_CREDENTIALS) from None

        with self._lock:
            self._check_rate_limit_locked(client_id, now)
            self._failures.pop(client_id, None)
            token, csrf = self._issue_session_locked(now)

        return {
            'token': token,
            'csrf': csrf,
            'expires_in': self._ABSOLUTE_TTL_SECONDS,
        }

    def authenticate(self, token: str) -> dict[str, object] | None:
        if not isinstance(token, str) or not token:
            return None

        now = float(self._clock())
        token_hash = self._hash_token(token)
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is None:
                return None

            issued = float(session['issued'])
            lastseen = float(session['lastseen'])
            if (
                now - issued >= self._ABSOLUTE_TTL_SECONDS
                or now - lastseen >= self._IDLE_TTL_SECONDS
            ):
                del self._sessions[token_hash]
                return None

            session['lastseen'] = now
            return {
                'operator': session['operator'],
                'csrf': session['csrf'],
            }

    def logout(self, token: str) -> None:
        if not isinstance(token, str) or not token:
            return
        token_hash = self._hash_token(token)
        with self._lock:
            self._sessions.pop(token_hash, None)
