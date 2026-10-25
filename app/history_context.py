# Read-only historical context construction.
import hashlib
import json
import sqlite3


_BAD_MESSAGE = 'invalid history context request'


def _bad():
    raise ValueError(_BAD_MESSAGE)


def _compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def _items_length(items):
    return len(_compact(items))


def _truncate_text(text):
    return text[:1200]


def _validated_int(value, low, high):
    if type(value) is not int or value < low or value > high:
        _bad()


def build_context(conn, campaign_id, *, related_campaign_ids=None, max_items=8, max_chars=6000):
    try:
        return _build_context(
            conn,
            campaign_id,
            related_campaign_ids=related_campaign_ids,
            max_items=max_items,
            max_chars=max_chars,
        )
    except sqlite3.Error:
        raise ValueError(_BAD_MESSAGE) from None


def _build_context(conn, campaign_id, *, related_campaign_ids=None, max_items=8, max_chars=6000):
    _validated_int(max_items, 1, 20)
    _validated_int(max_chars, 512, 12000)
    if not isinstance(campaign_id, str) or campaign_id == '':
        _bad()

    if related_campaign_ids is None:
        related = []
    else:
        if not isinstance(related_campaign_ids, (list, tuple)):
            _bad()
        related = list(related_campaign_ids)
        if len(related) > 20:
            _bad()
        seen = set()
        for rid in related:
            if not isinstance(rid, str) or rid == '':
                _bad()
            if rid in seen:
                _bad()
            seen.add(rid)

    selected = [campaign_id]
    for rid in related:
        if rid != campaign_id:
            selected.append(rid)

    markers = ','.join('?' for _ in selected)
    campaign_rows = conn.execute(
        'SELECT id, archived_at FROM campaign WHERE id IN (' + markers + ')',
        selected,
    ).fetchall()
    campaigns = {row['id']: row['archived_at'] for row in campaign_rows}
    if campaign_id not in campaigns or campaigns[campaign_id] is not None:
        _bad()
    for rid in related:
        if rid not in campaigns:
            _bad()

    distribution_rows = conn.execute(
        'SELECT d.id, d.campaign_id, d.kind, d.occurred_at, d.recorded_at, '
        'd.content_version_id, d.channel, cv.body AS text '
        'FROM distribution_record AS d '
        'JOIN content_version AS cv '
        'ON cv.id = d.content_version_id AND cv.campaign_id = d.campaign_id '
        'WHERE d.campaign_id IN (' + markers + ') '
        'AND d.kind IN (?, ?) '
        'AND NOT EXISTS ('
        'SELECT 1 FROM distribution_record AS newer '
        'WHERE newer.supersedes_id = d.id'
        ') '
        'ORDER BY d.occurred_at DESC, d.recorded_at DESC, d.id DESC '
        'LIMIT 200',
        selected + ['email_sent', 'publication'],
    ).fetchall()

    followup_rows = conn.execute(
        'SELECT f.id, f.campaign_id, f.kind, f.occurred_at, f.recorded_at, '
        'f.body AS text '
        'FROM followup_event AS f '
        'WHERE f.campaign_id IN (' + markers + ') '
        'AND f.kind IN (?, ?) '
        'AND NOT EXISTS ('
        'SELECT 1 FROM followup_event AS newer '
        'WHERE newer.supersedes_id = f.id'
        ') '
        'ORDER BY f.occurred_at DESC, f.recorded_at DESC, f.id DESC '
        'LIMIT 200',
        selected + ['response', 'note'],
    ).fetchall()

    def distribution_item(row):
        return {
            'id': row['id'],
            'campaign_id': row['campaign_id'],
            'kind': row['kind'],
            'occurred_at': row['occurred_at'],
            'content_version_id': row['content_version_id'],
            'channel': row['channel'],
            'text': _truncate_text(row['text']),
            'untrusted': True,
        }

    def followup_item(row):
        return {
            'id': row['id'],
            'campaign_id': row['campaign_id'],
            'kind': row['kind'],
            'occurred_at': row['occurred_at'],
            'content_version_id': None,
            'channel': None,
            'text': _truncate_text(row['text']),
            'untrusted': True,
        }

    responses = []
    notes = []
    for row in followup_rows:
        if row['kind'] == 'response':
            responses.append(followup_item(row))
        else:
            notes.append(followup_item(row))

    distributions = [distribution_item(row) for row in distribution_rows]
    ranked = responses + distributions + notes

    items = []
    for item in ranked:
        if len(items) >= max_items:
            break
        text = item['text']
        if _items_length(items + [item]) <= max_chars:
            items.append(item)
            continue
        low = 0
        high = len(text)
        while low < high:
            middle = (low + high + 1) // 2
            item['text'] = text[:middle]
            if _items_length(items + [item]) <= max_chars:
                low = middle
            else:
                high = middle - 1
        if low == 0:
            item['text'] = text
            continue
        item['text'] = text[:low]
        items.append(item)
        break

    payload = {'campaign_id': campaign_id, 'items': items}
    context_hash = hashlib.sha256(_compact(payload).encode('utf-8')).hexdigest()

    return {
        'campaign_id': campaign_id,
        'items': items,
        'untrusted_history': True,
        'context_hash': context_hash,
    }
