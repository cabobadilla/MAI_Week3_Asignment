from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_DOMAIN_TABLES = frozenset((
    'company',
    'contact',
    'campaign',
    'campaign_recipient',
    'generation_run',
    'content_version',
    'approval',
    'export_record',
    'distribution_record',
    'followup_event',
    'operator_credentials',
))

_ADD_ORGANIZATION_ROLES_SQL = '''ALTER TABLE company ADD COLUMN roles_json TEXT NOT NULL DEFAULT '["aportante"]' CHECK (
    CASE
        WHEN json_valid(roles_json) = 0 THEN 0
        WHEN json_type(roles_json) <> 'array' THEN 0
        WHEN json_array_length(roles_json) NOT IN (1, 2) THEN 0
        WHEN json_array_length(roles_json) = 1 THEN
            CASE
                WHEN json_type(roles_json, '$[0]') = 'text'
                 AND json_extract(roles_json, '$[0]') IN ('aportante', 'beneficiaria')
                THEN 1
                ELSE 0
            END
        ELSE
            CASE
                WHEN json_type(roles_json, '$[0]') = 'text'
                 AND json_type(roles_json, '$[1]') = 'text'
                 AND json_extract(roles_json, '$[0]') IN ('aportante', 'beneficiaria')
                 AND json_extract(roles_json, '$[1]') IN ('aportante', 'beneficiaria')
                 AND json_extract(roles_json, '$[0]') <> json_extract(roles_json, '$[1]')
                THEN 1
                ELSE 0
            END
    END
)'''


def connect(db_path: Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), isolation_level=None, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


def _tables(conn: sqlite3.Connection) -> set[str]:
    names: set[str] = set()
    for row in conn.execute('SELECT name, type FROM sqlite_master'):
        name = row[0]
        if row[1] == 'table' and not name.startswith('sqlite_'):
            names.add(name)
    return names


def _company_columns(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    return {row[1]: row for row in conn.execute('PRAGMA table_info(company)')}


def _apply_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    sql = Path(schema_path).read_text(encoding='utf-8-sig')
    if not sql.strip():
        raise ValueError('invalid schema')
    buffer = ''
    for ch in sql:
        buffer += ch
        if ch == ';' and sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                conn.execute(statement)
            buffer = ''
    tail = buffer.strip()
    if tail and any(
        line.strip() and not line.strip().startswith('--')
        for line in tail.splitlines()
    ):
        conn.execute(tail)


def _roles_value_valid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        roles = json.loads(value)
    except (TypeError, ValueError):
        return False
    if not isinstance(roles, list) or not 1 <= len(roles) <= 2:
        return False
    if any(
        not isinstance(role, str)
        or role not in ('aportante', 'beneficiaria')
        for role in roles
    ):
        return False
    return len(roles) == len(set(roles))


def _validate_roles(conn: sqlite3.Connection) -> None:
    for row in conn.execute('SELECT roles_json FROM company'):
        if not _roles_value_valid(row[0]):
            raise ValueError('unsupported database')


def _add_organization_roles(conn: sqlite3.Connection) -> None:
    if 'roles_json' in _company_columns(conn):
        raise ValueError('unsupported database')
    conn.execute(_ADD_ORGANIZATION_ROLES_SQL)
    _validate_roles(conn)
    conn.execute('PRAGMA user_version = 2')


def _validate_v2(conn: sqlite3.Connection, tables: set[str]) -> None:
    if not _DOMAIN_TABLES.issubset(tables):
        raise ValueError('unsupported database')
    if 'roles_json' not in _company_columns(conn):
        raise ValueError('unsupported database')
    _validate_roles(conn)


def initialize(db_path: Path, schema_path: Path, *, organizations: bool = False) -> None:
    if not isinstance(organizations, bool):
        raise ValueError('unsupported database')
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        conn.execute('BEGIN IMMEDIATE')
        try:
            version = int(conn.execute('PRAGMA user_version').fetchone()[0])
            tables = _tables(conn)
            if version == 0:
                if tables:
                    raise ValueError('unsupported database')
                try:
                    _apply_schema(conn, Path(schema_path))
                except sqlite3.Error:
                    raise ValueError('invalid schema') from None
                if not _DOMAIN_TABLES.issubset(_tables(conn)):
                    raise ValueError('invalid schema')
                if organizations:
                    _add_organization_roles(conn)
                else:
                    conn.execute('PRAGMA user_version = 1')
            elif version == 1:
                if not _DOMAIN_TABLES.issubset(tables):
                    raise ValueError('unsupported database')
                if 'roles_json' in _company_columns(conn):
                    raise ValueError('unsupported database')
                if organizations:
                    _add_organization_roles(conn)
            elif version == 2:
                _validate_v2(conn, tables)
            else:
                raise ValueError('unsupported database')
            conn.execute('COMMIT')
        except BaseException:
            if conn.in_transaction:
                conn.execute('ROLLBACK')
            raise
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    if conn.in_transaction:
        raise ValueError('transaction already active')
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield conn
        conn.execute('COMMIT')
    except BaseException:
        if conn.in_transaction:
            conn.execute('ROLLBACK')
        raise
