import hashlib
import json
import sqlite3
from itertools import count

from . import demo_generation, generation_contract, review_contract, runs, versions

_OUTPUT_KEYS = (
    'campaign_id',
    'run_id',
    'query',
    'brief',
    'history',
    'sources',
    'query_count',
    'status',
    'events',
    'questions',
    'human_answer',
    'cycle',
    'draft',
    'draft_hash',
    'draft_history',
    'review',
    'review_hash',
    'review_history',
    'error',
)
_OUTPUT_KEY_SET = frozenset(_OUTPUT_KEYS)
_ALLOWED_STATUSES = frozenset(('needs_human_review', 'waiting_input', 'failed'))
_MAX_OUTPUT_BYTES = 256 * 1024
_REAL_WARNING = 'IA real: revisión automática no equivale a aprobación humana.'
_SAVEPOINT_IDS = count()


def _canonical_json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('value is not canonical JSON') from exc


def _canonical_hash(value):
    return hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()


def _safe_output(output):
    if not isinstance(output, dict):
        raise ValueError('output must be a dict')
    if any(key not in _OUTPUT_KEY_SET for key in output):
        raise ValueError('output contains non-public keys')
    safe = {key: output[key] for key in _OUTPUT_KEYS if key in output}
    status = safe.get('status')
    if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
        raise ValueError('invalid result status')
    if len(_canonical_json(safe).encode('utf-8')) > _MAX_OUTPUT_BYTES:
        raise ValueError('output exceeds 256 KiB')
    return safe


def _agent_record(metrics):
    if metrics is None:
        return None
    if not isinstance(metrics, dict):
        raise ValueError('generation_run.metrics is corrupted')
    if 'agent_result' not in metrics:
        return None
    record = metrics['agent_result']
    if not isinstance(record, dict):
        raise ValueError('agent_result is corrupted')
    output = record.get('output')
    digest = record.get('hash')
    if not isinstance(output, dict) or not isinstance(digest, str):
        raise ValueError('agent_result is corrupted')
    safe = _safe_output(output)
    if _canonical_hash(safe) != digest:
        raise ValueError('agent_result hash mismatch')
    return safe, digest


def _chunk_ids_for_run(run):
    sources = run.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('run sources are required')
    result = []
    seen = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError('invalid run source')
        chunk_id = source.get('chunk_id')
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError('invalid run source chunk_id')
        if chunk_id in seen:
            raise ValueError('duplicate run source chunk_id')
        seen.add(chunk_id)
        result.append(chunk_id)
    return result


def _validate_new_result(run, run_id, output):
    if output.get('run_id') != run_id:
        raise ValueError('run_id mismatch')
    if output.get('campaign_id') != run.get('campaign_id'):
        raise ValueError('campaign_id mismatch')
    if 'sources' not in output or output.get('sources') != run.get('sources'):
        raise ValueError('sources do not match the immutable run snapshot')
    if 'brief' in output and output.get('brief') != run.get('config'):
        raise ValueError('brief does not match the run config')
    if run.get('status') != 'running':
        raise ValueError('run is not running')
    status = output['status']
    if status == 'needs_human_review':
        config = run.get('config')
        formats = config.get('formats') if isinstance(config, dict) else None
        if not isinstance(formats, list) or not formats:
            raise ValueError('run does not have selected formats')
        draft_value = output.get('draft')
        review_value = output.get('review')
        if not isinstance(draft_value, dict) or not isinstance(review_value, dict):
            raise ValueError('draft and review must be dicts')
        chunk_ids = _chunk_ids_for_run(run)
        try:
            draft = generation_contract.parse_generation(
                _canonical_json(draft_value),
                formats=formats,
                chunk_ids=chunk_ids,
            )
        except Exception as exc:
            raise ValueError('invalid draft') from exc
        if not isinstance(draft, dict) or draft.get('status') != 'draft':
            raise ValueError('draft did not parse as a final draft')
        pieces = []
        piece_keys = []
        for item in draft.get('pieces') or []:
            if not isinstance(item, dict):
                raise ValueError('invalid draft piece')
            piece_format = item.get('format')
            piece_body = item.get('body')
            piece_variant = item.get('variant', '')
            if not isinstance(piece_format, str) or not isinstance(piece_body, str) or not isinstance(piece_variant, str):
                raise ValueError('invalid draft piece')
            pieces.append({'format': piece_format, 'body': piece_body, 'variant': piece_variant})
            piece_keys.append(piece_format + ':' + piece_variant)
        if not pieces:
            raise ValueError('draft has no pieces')
        try:
            review = review_contract.parse_review(
                _canonical_json(review_value),
                piece_keys=piece_keys,
                chunk_ids=chunk_ids,
            )
        except Exception as exc:
            raise ValueError('invalid review') from exc
        if not isinstance(review, dict) or review.get('verdict') != 'pass':
            raise ValueError('review did not pass')
        if output.get('draft_hash') != _canonical_hash(draft):
            raise ValueError('draft_hash mismatch')
        if output.get('review_hash') != _canonical_hash(review):
            raise ValueError('review_hash mismatch')
        return pieces, 'needs_review', 'human_review'
    if status == 'waiting_input':
        return [], 'waiting_input', 'human_input'
    if status == 'failed':
        return [], 'failed', 'agent_failure'
    raise ValueError('invalid result status')


def _persist_agent_result(conn, run_id, metrics, output, digest):
    if metrics is None:
        base = {}
    elif isinstance(metrics, dict):
        base = dict(metrics)
    else:
        raise ValueError('generation_run.metrics is corrupted')
    base['agent_result'] = {'output': output, 'hash': digest}
    payload = _canonical_json(base)
    cursor = conn.execute(
        'UPDATE generation_run SET metrics_json = ? WHERE id = ?',
        (payload, run_id),
    )
    if cursor.rowcount != 1:
        raise ValueError('generation_run row disappeared during save')


class _Transaction:
    def __init__(self, conn):
        self.conn = conn
        self.own = False
        self.name = None
        self.active = False

    def __enter__(self):
        self.own = not self.conn.in_transaction
        if self.own:
            self.conn.execute('BEGIN IMMEDIATE')
        else:
            self.name = 'real_results_sp_%d' % next(_SAVEPOINT_IDS)
            self.conn.execute('SAVEPOINT %s' % self.name)
        self.active = True
        return self.conn

    def __exit__(self, exc_type, exc, traceback):
        if not self.active:
            return False
        try:
            if exc_type is None:
                if self.own:
                    self.conn.commit()
                else:
                    self.conn.execute('RELEASE SAVEPOINT %s' % self.name)
            else:
                if self.own:
                    self.conn.rollback()
                else:
                    self.conn.execute('ROLLBACK TO SAVEPOINT %s' % self.name)
                    self.conn.execute('RELEASE SAVEPOINT %s' % self.name)
        finally:
            self.active = False
        return False


def save_result(conn: sqlite3.Connection, run_id: str, output: dict) -> dict:
    safe_output = _safe_output(output)
    digest = _canonical_hash(safe_output)
    with _Transaction(conn):
        run = runs.get_run(conn, run_id)
        if run is None:
            raise ValueError('run not found')
        existing = _agent_record(run.get('metrics'))
        if existing is not None:
            if existing[1] != digest:
                raise ValueError('run already has a different immutable result')
        else:
            pieces, new_status, new_step = _validate_new_result(run, run_id, safe_output)
            for piece in pieces:
                versions.create_version(
                    conn,
                    run['campaign_id'],
                    piece['format'],
                    piece['body'],
                    variant=piece['variant'],
                    run_id=run_id,
                    origin='generated',
                )
            runs.transition_run(
                conn,
                run_id,
                new_status,
                new_step,
                expected_status='running',
            )
            _persist_agent_result(conn, run_id, run.get('metrics'), safe_output, digest)
    return get_bundle(conn, run_id)


def get_bundle(conn, run_id):
    bundle = demo_generation.get_demo_bundle(conn, run_id)
    run = runs.get_run(conn, run_id)
    if run is None:
        return bundle
    record = _agent_record(run.get('metrics'))
    if record is None:
        if (run.get('metrics') or {}).get('agent_mode') == 'real':
            return dict(bundle, mode='real', generation='llm', warnings=['Ejecución IA real pendiente; consulta el estado antes de iniciar otra.'])
        return bundle
    output, digest = record
    result = dict(bundle)
    result['mode'] = 'real'
    result['generation'] = 'llm'
    result['warnings'] = [_REAL_WARNING]
    result['agent'] = output
    result['agent_hash'] = digest
    if output.get('status') == 'failed':
        result['versions'] = []
    return result
