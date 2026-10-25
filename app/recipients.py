import json
import sqlite3
import uuid
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).isoformat()

def _from_row(row):
    data = dict(row)
    data['snapshot'] = json.loads(data.pop('snapshot_json'))
    return data

def _row(conn, recipient_id):
    row = conn.execute('SELECT id, campaign_id, contact_id, email_key, snapshot_json, selected_at, archived_at FROM campaign_recipient WHERE id = ?', (recipient_id,)).fetchone()
    if row is None:
        raise ValueError('Recipient selection was not found.')
    return row

def _active_campaign(conn, campaign_id):
    return conn.execute('SELECT id FROM campaign WHERE id = ? AND archived_at IS NULL', (campaign_id,)).fetchone()

def _active_contact(conn, contact_id):
    return conn.execute('SELECT ct.id, ct.name, ct.email, ct.email_key, ct.company_id, co.name AS company_name FROM contact ct JOIN company co ON co.id = ct.company_id WHERE ct.id = ? AND ct.archived_at IS NULL AND co.archived_at IS NULL', (contact_id,)).fetchone()

def add_recipient(conn, campaign_id, contact_id):
    if _active_campaign(conn, campaign_id) is None:
        raise ValueError('Campaign is unavailable.')
    contact = _active_contact(conn, contact_id)
    if contact is None:
        raise ValueError('Contact is unavailable.')
    email_key = contact['email_key']
    if not isinstance(email_key, str) or not email_key.strip():
        raise ValueError('Contact is not eligible.')
    same_contact = conn.execute('SELECT id FROM campaign_recipient WHERE campaign_id = ? AND contact_id = ? AND archived_at IS NULL LIMIT 1', (campaign_id, contact_id)).fetchone()
    if same_contact is not None:
        raise ValueError('Contact is already selected for this campaign.')
    existing = conn.execute('SELECT archived_at FROM campaign_recipient WHERE campaign_id = ? AND email_key = ? LIMIT 1', (campaign_id, email_key)).fetchone()
    if existing is not None:
        if existing['archived_at'] is not None:
            raise ValueError('Existing selection can be restored.')
        raise ValueError('This email is already selected for this campaign.')
    snapshot = {
        'company_id': contact['company_id'],
        'company_name': contact['company_name'],
        'contact_id': contact['id'],
        'contact_name': contact['name'],
        'email': contact['email'],
        'email_key': email_key,
    }
    recipient_id = str(uuid.uuid4())
    try:
        conn.execute('INSERT INTO campaign_recipient (id, campaign_id, contact_id, email_key, snapshot_json, selected_at, archived_at) VALUES (?, ?, ?, ?, ?, ?, NULL)', (recipient_id, campaign_id, contact_id, email_key, json.dumps(snapshot, ensure_ascii=False, sort_keys=True), _now()))
    except sqlite3.IntegrityError:
        raise ValueError('Recipient selection could not be added.') from None
    return get_recipient(conn, recipient_id)

def get_recipient(conn, id):
    return _from_row(_row(conn, id))

def list_recipients(conn, campaign_id, include_archived=False):
    sql = 'SELECT cr.id, cr.campaign_id, cr.contact_id, cr.email_key, cr.snapshot_json, cr.selected_at, cr.archived_at FROM campaign_recipient cr JOIN contact ct ON ct.id = cr.contact_id JOIN company co ON co.id = ct.company_id WHERE cr.campaign_id = ?'
    if not include_archived:
        sql += ' AND cr.archived_at IS NULL AND ct.archived_at IS NULL AND co.archived_at IS NULL'
    sql += ' ORDER BY cr.selected_at ASC, cr.id ASC'
    rows = conn.execute(sql, (campaign_id,)).fetchall()
    return [_from_row(row) for row in rows]

def archive_recipient(conn, id):
    row = _row(conn, id)
    if row['archived_at'] is None:
        conn.execute('UPDATE campaign_recipient SET archived_at = ? WHERE id = ? AND archived_at IS NULL', (_now(), id))
    return get_recipient(conn, id)

def restore_recipient(conn, id):
    row = _row(conn, id)
    snapshot = _from_row(row)['snapshot']
    if _active_campaign(conn, row['campaign_id']) is None:
        raise ValueError('Campaign is unavailable.')
    contact = _active_contact(conn, row['contact_id'])
    if contact is None:
        raise ValueError('Contact is unavailable.')
    original_key = snapshot.get('email_key') if isinstance(snapshot, dict) else None
    if not isinstance(original_key, str) or contact['email_key'] != original_key:
        raise ValueError('Contact email no longer matches this selection.')
    try:
        conn.execute('UPDATE campaign_recipient SET archived_at = NULL WHERE id = ?', (id,))
    except sqlite3.IntegrityError:
        raise ValueError('Recipient selection could not be restored.') from None
    return get_recipient(conn, id)
