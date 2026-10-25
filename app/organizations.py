import json
from contextlib import contextmanager

from . import companies

_ROLES = ('aportante', 'beneficiaria')
_ROLE_SET = frozenset(_ROLES)
_MAX_CONTACT_NAME = 160
_SAVEPOINT = 'gwa_save_organization'


def _blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ''
    return False


def _normalize_name(name):
    if not isinstance(name, str):
        raise ValueError('invalid organization name')
    result = name.strip()
    if not result:
        raise ValueError('invalid organization name')
    return result


def _validate_roles(roles):
    if isinstance(roles, (str, bytes)):
        raise ValueError('invalid roles')
    if not isinstance(roles, (list, tuple)):
        raise ValueError('invalid roles')
    seen = set()
    result = []
    for role in roles:
        if not isinstance(role, str) or role not in _ROLE_SET:
            raise ValueError('invalid roles')
        if role in seen:
            raise ValueError('invalid roles')
        seen.add(role)
        result.append(role)
    if not result:
        raise ValueError('invalid roles')
    return result


def _parse_roles(raw):
    if raw is None:
        return ['aportante']
    if not isinstance(raw, str):
        raise ValueError('invalid roles')
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        raise ValueError('invalid roles') from None
    return _validate_roles(value)


def _serialize_roles(roles):
    return json.dumps(list(roles), ensure_ascii=False, separators=(',', ':'))


def _optional_id(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError('invalid id')
    text = value.strip()
    if not text:
        return None
    if '\x00' in text or len(text) > 255:
        raise ValueError('invalid id')
    return text


def _required_id(value):
    parsed = _optional_id(value)
    if parsed is None:
        raise ValueError('invalid id')
    return parsed


def _normalize_email(email):
    if not isinstance(email, str) or not email.strip():
        raise ValueError('invalid contact email')
    try:
        display, key = companies.normalize_email(email)
    except Exception:
        raise ValueError('invalid contact email') from None
    if not isinstance(display, str) or not display.strip():
        raise ValueError('invalid contact email')
    if not isinstance(key, str):
        raise ValueError('invalid contact email')
    key = key.strip()
    if not key or '@' not in key or any(ch.isspace() for ch in key):
        raise ValueError('invalid contact email')
    return display.strip(), key


def _parse_contacts(contacts):
    if isinstance(contacts, (str, bytes)):
        raise ValueError('invalid contacts')
    if not isinstance(contacts, (list, tuple)):
        raise ValueError('invalid contacts')
    parsed = []
    ids = set()
    for row in contacts:
        if not isinstance(row, dict):
            raise ValueError('invalid contact')
        contact_id = _optional_id(row.get('id'))
        name = row.get('name')
        email = row.get('email')
        if contact_id is None and _blank(name) and _blank(email):
            continue
        if _blank(name) or _blank(email):
            raise ValueError('invalid contact')
        if not isinstance(name, str) or not isinstance(email, str):
            raise ValueError('invalid contact')
        clean_name = name.strip()
        if not clean_name or len(clean_name) > _MAX_CONTACT_NAME:
            raise ValueError('invalid contact')
        display, key = _normalize_email(email)
        if contact_id is not None:
            if contact_id in ids:
                raise ValueError('duplicate contact id')
            ids.add(contact_id)
        parsed.append({'id': contact_id, 'name': clean_name, 'email': display, 'email_key': key})
    return parsed


def _existing_email_key(contact):
    if not isinstance(contact, dict):
        return None
    key = contact.get('email_key')
    if isinstance(key, str) and key.strip():
        return key.strip().casefold()
    email = contact.get('email')
    if isinstance(email, str) and email.strip():
        try:
            return companies.normalize_email(email)[1].strip().casefold()
        except Exception:
            return email.strip().casefold()
    return None


def _validate_against_existing(submitted, existing):
    active = {}
    for contact in existing:
        if isinstance(contact, dict) and contact.get('id') is not None:
            active[contact.get('id')] = contact
    submitted_ids = set()
    for row in submitted:
        contact_id = row['id']
        if contact_id is not None:
            if contact_id not in active:
                raise ValueError('invalid contact id')
            submitted_ids.add(contact_id)
    submitted_keys = set()
    for row in submitted:
        key = row['email_key']
        if key in submitted_keys:
            raise ValueError('duplicate contact email')
        submitted_keys.add(key)
    preserved_keys = set()
    for contact_id, contact in active.items():
        if contact_id in submitted_ids:
            continue
        key = _existing_email_key(contact)
        if key is not None:
            preserved_keys.add(key)
    if submitted_keys & preserved_keys:
        raise ValueError('duplicate contact email')


def _ensure_roles_column(conn):
    conn.execute('SELECT roles_json FROM company LIMIT 1').fetchone()


def _select_company(conn, organization_id):
    return conn.execute(
        'SELECT id, name, notes, roles_json, created_at, archived_at FROM company WHERE id = ?',
        (organization_id,),
    ).fetchone()


def _row_value(row, index, name):
    if isinstance(row, dict):
        return row[name]
    return row[index]


def _row_to_organization(conn, row):
    organization_id = _row_value(row, 0, 'id')
    return {
        'id': organization_id,
        'name': _row_value(row, 1, 'name'),
        'notes': _row_value(row, 2, 'notes'),
        'created_at': _row_value(row, 4, 'created_at'),
        'archived_at': _row_value(row, 5, 'archived_at'),
        'roles': _parse_roles(_row_value(row, 3, 'roles_json')),
        'contacts': companies.list_contacts(conn, organization_id, include_archived=False),
    }


@contextmanager
def _write_transaction(conn):
    if getattr(conn, 'in_transaction', False):
        conn.execute('SAVEPOINT ' + _SAVEPOINT)
        try:
            yield
            conn.execute('RELEASE SAVEPOINT ' + _SAVEPOINT)
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT ' + _SAVEPOINT)
            except Exception:
                pass
            try:
                conn.execute('RELEASE SAVEPOINT ' + _SAVEPOINT)
            except Exception:
                pass
            raise
    else:
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield
            conn.commit()
        except BaseException:
            try:
                conn.rollback()
            except Exception:
                pass
            raise


def _write_roles(conn, organization_id, roles):
    conn.execute(
        'UPDATE company SET roles_json = ? WHERE id = ?',
        (_serialize_roles(roles), organization_id),
    )


def _save_contacts(conn, organization_id, submitted, existing):
    active = {}
    for contact in existing:
        if isinstance(contact, dict) and contact.get('id') is not None:
            active[contact.get('id')] = contact
    for row in submitted:
        contact_id = row['id']
        if contact_id is None:
            companies.create_contact(conn, organization_id, row['email'], name=row['name'])
        else:
            current = active[contact_id]
            if current.get('name') != row['name'] or current.get('email') != row['email']:
                companies.update_contact(conn, contact_id, email=row['email'], name=row['name'])


def save_organization(conn, name, contacts, *, organization_id=None, notes=None, roles=None):
    clean_name = _normalize_name(name)
    if notes is not None and not isinstance(notes, str):
        raise ValueError('invalid notes')
    normalized_roles = None
    if roles is not None:
        normalized_roles = _validate_roles(roles)
    submitted = _parse_contacts(contacts)
    editing = organization_id is not None
    if editing:
        target_id = _required_id(organization_id)
    else:
        target_id = None
        if not submitted:
            raise ValueError('organization requires a contact')
        for row in submitted:
            if row['id'] is not None:
                raise ValueError('invalid contact id')
        _validate_against_existing(submitted, [])
    with _write_transaction(conn):
        _ensure_roles_column(conn)
        if editing:
            row = _select_company(conn, target_id)
            if row is None or _row_value(row, 5, 'archived_at') is not None:
                raise ValueError('organization not found')
            existing = companies.list_contacts(conn, target_id, include_archived=False)
            _validate_against_existing(submitted, existing)
            updates = {'name': clean_name}
            if notes is not None:
                updates['notes'] = notes
            companies.update_company(conn, target_id, **updates)
            if normalized_roles is not None:
                _write_roles(conn, target_id, normalized_roles)
            _save_contacts(conn, target_id, submitted, existing)
        else:
            new_notes = '' if notes is None else notes
            created = companies.create_company(conn, clean_name, new_notes)
            target_id = created['id']
            storage_roles = ['aportante'] if normalized_roles is None else normalized_roles
            _write_roles(conn, target_id, storage_roles)
            _save_contacts(conn, target_id, submitted, [])
        final_row = _select_company(conn, target_id)
        if final_row is None:
            raise ValueError('organization not found')
        return _row_to_organization(conn, final_row)


def get_organization(conn, id):
    organization_id = _required_id(id)
    row = _select_company(conn, organization_id)
    if row is None:
        raise ValueError('organization not found')
    return _row_to_organization(conn, row)


def list_organizations(conn, *, role=None, include_archived=False):
    if role is not None:
        if not isinstance(role, str) or role not in _ROLE_SET:
            raise ValueError('invalid role')
    sql = 'SELECT id, name, notes, roles_json, created_at, archived_at FROM company'
    if not include_archived:
        sql += ' WHERE archived_at IS NULL'
    sql += ' ORDER BY name ASC, id ASC'
    rows = conn.execute(sql).fetchall()
    organizations = []
    for row in rows:
        roles = _parse_roles(_row_value(row, 3, 'roles_json'))
        if role is not None and role not in roles:
            continue
        organizations.append(_row_to_organization(conn, row))
    return organizations
