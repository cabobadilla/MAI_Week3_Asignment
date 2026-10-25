from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Tuple


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _company_name(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError('invalid name')
    value = value.strip()
    if not value:
        raise ValueError('invalid name')
    return value


def _plain_notes(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError('invalid notes')
    return value


def _contact_name(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError('invalid name')
    return value.strip()


def normalize_email(email: object) -> Tuple[str, str]:
    if not isinstance(email, str):
        raise ValueError('invalid email')
    display = email.strip()
    if not display or len(display) > 254:
        raise ValueError('invalid email')
    if display.count('@') != 1:
        raise ValueError('invalid email')
    if any(ch.isspace() for ch in display):
        raise ValueError('invalid email')
    local, domain = display.split('@')
    if not local or not domain or '.' not in domain:
        raise ValueError('invalid email')
    if domain.startswith('.') or domain.endswith('.') or '..' in domain:
        raise ValueError('invalid email')
    for label in domain.split('.'):
        if not label or label.startswith('-') or label.endswith('-'):
            raise ValueError('invalid email')
        if not all(ch.isalnum() or ch == '-' for ch in label):
            raise ValueError('invalid email')
    return display, display.casefold()


def _fetch_company(conn: sqlite3.Connection, id: str) -> dict:
    row = conn.execute(
        'SELECT id, name, notes, created_at, archived_at FROM company WHERE id = ?',
        (id,),
    ).fetchone()
    if row is None:
        raise ValueError('company not found')
    return dict(row)


def _fetch_contact(conn: sqlite3.Connection, id: str) -> dict:
    row = conn.execute(
        'SELECT id, company_id, name, email, email_key, created_at, archived_at '
        'FROM contact WHERE id = ?',
        (id,),
    ).fetchone()
    if row is None:
        raise ValueError('contact not found')
    return dict(row)


def _require_active_company(conn: sqlite3.Connection, company_id: str) -> None:
    row = conn.execute(
        'SELECT archived_at FROM company WHERE id = ?',
        (company_id,),
    ).fetchone()
    if row is None:
        raise ValueError('company not found')
    if row[0] is not None:
        raise ValueError('company archived')


def create_company(conn: sqlite3.Connection, name: str, notes: str = '') -> dict:
    company_name = _company_name(name)
    note_text = _plain_notes(notes)
    id = str(uuid.uuid4())
    now = _now()
    try:
        conn.execute(
            'INSERT INTO company (id, name, notes, created_at) VALUES (?, ?, ?, ?)',
            (id, company_name, note_text, now),
        )
    except sqlite3.IntegrityError:
        raise ValueError('invalid company') from None
    return _fetch_company(conn, id)


def update_company(conn: sqlite3.Connection, id: str, *, name=None, notes=None) -> dict:
    fields = []
    params = []
    if name is not None:
        fields.append('name = ?')
        params.append(_company_name(name))
    if notes is not None:
        fields.append('notes = ?')
        params.append(_plain_notes(notes))
    try:
        if fields:
            conn.execute(
                'UPDATE company SET ' + ', '.join(fields) + ' WHERE id = ?',
                params + [id],
            )
    except sqlite3.IntegrityError:
        raise ValueError('invalid company') from None
    return _fetch_company(conn, id)


def archive_company(conn: sqlite3.Connection, id: str) -> dict:
    now = _now()
    conn.execute(
        'UPDATE company SET archived_at = COALESCE(archived_at, ?) WHERE id = ?',
        (now, id),
    )
    return _fetch_company(conn, id)


def list_companies(conn: sqlite3.Connection, include_archived: bool = False) -> list[dict]:
    query = 'SELECT id, name, notes, created_at, archived_at FROM company'
    if not include_archived:
        query += ' WHERE archived_at IS NULL'
    query += ' ORDER BY created_at, rowid'
    return [dict(row) for row in conn.execute(query)]


def create_contact(conn: sqlite3.Connection, company_id: str, email: str, name: str = '') -> dict:
    _require_active_company(conn, company_id)
    display, key = normalize_email(email)
    contact_name = _contact_name(name)
    id = str(uuid.uuid4())
    now = _now()
    try:
        conn.execute(
            'INSERT INTO contact (id, company_id, name, email, email_key, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (id, company_id, contact_name, display, key, now),
        )
    except sqlite3.IntegrityError:
        raise ValueError('invalid contact') from None
    return _fetch_contact(conn, id)


def update_contact(conn: sqlite3.Connection, id: str, *, email=None, name=None) -> dict:
    fields = []
    params = []
    if email is not None:
        display, key = normalize_email(email)
        fields.append('email = ?')
        fields.append('email_key = ?')
        params.append(display)
        params.append(key)
    if name is not None:
        fields.append('name = ?')
        params.append(_contact_name(name))
    try:
        if fields:
            conn.execute(
                'UPDATE contact SET ' + ', '.join(fields) + ' WHERE id = ?',
                params + [id],
            )
    except sqlite3.IntegrityError:
        raise ValueError('invalid contact') from None
    return _fetch_contact(conn, id)


def archive_contact(conn: sqlite3.Connection, id: str) -> dict:
    now = _now()
    conn.execute(
        'UPDATE contact SET archived_at = COALESCE(archived_at, ?) WHERE id = ?',
        (now, id),
    )
    return _fetch_contact(conn, id)


def list_contacts(conn: sqlite3.Connection, company_id: str, include_archived: bool = False) -> list[dict]:
    if include_archived:
        query = (
            'SELECT id, company_id, name, email, email_key, created_at, archived_at '
            'FROM contact WHERE company_id = ? ORDER BY created_at, rowid'
        )
    else:
        query = (
            'SELECT ct.id, ct.company_id, ct.name, ct.email, ct.email_key, '
            'ct.created_at, ct.archived_at FROM contact ct '
            'JOIN company c ON c.id = ct.company_id '
            'WHERE ct.company_id = ? AND ct.archived_at IS NULL '
            'AND c.archived_at IS NULL ORDER BY ct.created_at, ct.rowid'
        )
    return [dict(row) for row in conn.execute(query, (company_id,))]
