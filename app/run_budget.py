'''Atomic pre-call LLM budget reservations.'''
from __future__ import annotations

import json
from datetime import datetime, timezone

from . import runs
from .config import AppConfig

_LIMIT_KEYS = (
    'max_input_tokens',
    'max_output_tokens',
    'max_total_tokens_per_run',
    'max_request_attempts_per_run',
)
_RESERVATION_KEYS = frozenset((
    'request_id',
    'stage',
    'input_tokens',
    'max_output_tokens',
    'reserved_tokens',
    'status',
))
_REQUEST_CHARS = frozenset('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
_ALLOWED_STAGES = frozenset(('generator', 'reviewer'))


def _utcnow():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def _positive_limit(value):
    return type(value) is int and value >= 1


def _config_limits(config):
    if not isinstance(config, AppConfig):
        raise ValueError('LLM budget is unavailable')
    if config.llm_enabled is not True:
        raise ValueError('LLM is disabled')
    limits = {}
    for key in _LIMIT_KEYS:
        value = getattr(config, key, None)
        if not _positive_limit(value):
            raise ValueError('LLM budget is unavailable')
        limits[key] = value
    return limits


def _validate_request_id(value):
    if not isinstance(value, str):
        raise ValueError('invalid request id')
    if not 1 <= len(value) <= 120:
        raise ValueError('invalid request id')
    for character in value:
        if character not in _REQUEST_CHARS:
            raise ValueError('invalid request id')
    return value


def _validate_stage(value):
    if not isinstance(value, str) or value not in _ALLOWED_STAGES:
        raise ValueError('invalid stage')
    return value


def _validate_tokens(value, maximum):
    if type(value) is not int or value < 1 or value > maximum:
        raise ValueError('invalid token count')
    return value


def _build_ledger(metrics, attempts, limits):
    if 'llm_budget' not in metrics:
        if attempts != 0:
            raise ValueError('budget ledger unavailable')
        return {
            'limits': dict(limits),
            'reserved_tokens': 0,
            'requests': {},
        }
    raw = metrics['llm_budget']
    if not isinstance(raw, dict):
        raise ValueError('budget ledger unavailable')
    if set(raw) != {'limits', 'reserved_tokens', 'requests'}:
        raise ValueError('budget ledger unavailable')
    raw_limits = raw['limits']
    if not isinstance(raw_limits, dict):
        raise ValueError('budget ledger unavailable')
    if set(raw_limits) != set(_LIMIT_KEYS):
        raise ValueError('budget ledger unavailable')
    stored_limits = {}
    for key in _LIMIT_KEYS:
        value = raw_limits[key]
        if not _positive_limit(value):
            raise ValueError('budget ledger unavailable')
        stored_limits[key] = value
    if stored_limits != limits:
        raise ValueError('budget limits changed')
    total = raw['reserved_tokens']
    if type(total) is not int or total < 0:
        raise ValueError('budget ledger unavailable')
    raw_requests = raw['requests']
    if not isinstance(raw_requests, dict):
        raise ValueError('budget ledger unavailable')
    requests = {}
    computed_total = 0
    for request_id, reservation in raw_requests.items():
        _validate_request_id(request_id)
        if not isinstance(reservation, dict):
            raise ValueError('budget ledger unavailable')
        if set(reservation) != _RESERVATION_KEYS:
            raise ValueError('budget ledger unavailable')
        if reservation['request_id'] != request_id:
            raise ValueError('budget ledger unavailable')
        stage = _validate_stage(reservation['stage'])
        input_tokens = _validate_tokens(reservation['input_tokens'], stored_limits['max_input_tokens'])
        max_output_tokens = _validate_tokens(reservation['max_output_tokens'], stored_limits['max_output_tokens'])
        reserved_tokens = reservation['reserved_tokens']
        if type(reserved_tokens) is not int or reserved_tokens != input_tokens + max_output_tokens:
            raise ValueError('budget ledger unavailable')
        if reservation['status'] != 'reserved':
            raise ValueError('budget ledger unavailable')
        requests[request_id] = {
            'request_id': request_id,
            'stage': stage,
            'input_tokens': input_tokens,
            'max_output_tokens': max_output_tokens,
            'reserved_tokens': reserved_tokens,
            'status': 'reserved',
        }
        computed_total += reserved_tokens
    if computed_total != total:
        raise ValueError('budget ledger unavailable')
    if len(requests) != attempts:
        raise ValueError('budget ledger unavailable')
    if attempts > stored_limits['max_request_attempts_per_run']:
        raise ValueError('budget ledger unavailable')
    if total > stored_limits['max_total_tokens_per_run']:
        raise ValueError('budget ledger unavailable')
    return {
        'limits': stored_limits,
        'reserved_tokens': total,
        'requests': requests,
    }


def _check_campaign(conn, campaign_id, config_revision):
    row = conn.execute(
        'SELECT config_revision, archived_at FROM campaign WHERE id = ?',
        (campaign_id,),
    ).fetchone()
    if row is None:
        raise ValueError('campaign is not active')
    if hasattr(row, 'keys'):
        revision = row['config_revision']
        archived_at = row['archived_at']
    else:
        revision = row[0]
        archived_at = row[1]
    if archived_at is not None:
        raise ValueError('campaign is not active')
    if revision != config_revision:
        raise ValueError('campaign brief has changed')


def _same_reservation(existing, request_id, stage, input_tokens, max_output_tokens, reserved_tokens):
    return (
        existing['request_id'] == request_id
        and existing['stage'] == stage
        and existing['input_tokens'] == input_tokens
        and existing['max_output_tokens'] == max_output_tokens
        and existing['reserved_tokens'] == reserved_tokens
        and existing['status'] == 'reserved'
    )


def reserve_call(conn, run_id, request_id, *, stage, input_tokens, max_output_tokens, config: AppConfig) -> dict:
    try:
        limits = _config_limits(config)
        request_id = _validate_request_id(request_id)
        stage = _validate_stage(stage)
        input_tokens = _validate_tokens(input_tokens, limits['max_input_tokens'])
        max_output_tokens = _validate_tokens(max_output_tokens, limits['max_output_tokens'])
        reserved_tokens = input_tokens + max_output_tokens
        with runs._atomic(conn):
            run = runs.get_run(conn, run_id)
            if run['status'] != 'running':
                raise ValueError('generation run is not running')
            _check_campaign(conn, run['campaign_id'], run['config_revision'])
            metrics = run['metrics']
            if not isinstance(metrics, dict):
                raise ValueError('generation run unavailable')
            if 'attempts' not in metrics:
                raise ValueError('generation run unavailable')
            attempts = metrics['attempts']
            if type(attempts) is not int or attempts < 0:
                raise ValueError('generation run unavailable')
            ledger = _build_ledger(metrics, attempts, limits)
            requests = ledger['requests']
            existing = requests.get(request_id)
            if existing is not None:
                if _same_reservation(existing, request_id, stage, input_tokens, max_output_tokens, reserved_tokens):
                    return dict(existing)
                raise ValueError('request id already reserved')
            if attempts + 1 > limits['max_request_attempts_per_run']:
                raise ValueError('request attempt limit exceeded')
            new_total = ledger['reserved_tokens'] + reserved_tokens
            if new_total > limits['max_total_tokens_per_run']:
                raise ValueError('token budget exceeded')
            reservation = {
                'request_id': request_id,
                'stage': stage,
                'input_tokens': input_tokens,
                'max_output_tokens': max_output_tokens,
                'reserved_tokens': reserved_tokens,
                'status': 'reserved',
            }
            requests = dict(requests)
            requests[request_id] = reservation
            ledger = {
                'limits': dict(ledger['limits']),
                'reserved_tokens': new_total,
                'requests': requests,
            }
            new_metrics = dict(metrics)
            new_metrics['attempts'] = attempts + 1
            new_metrics['llm_budget'] = ledger
            try:
                metrics_json = json.dumps(
                    new_metrics,
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(',', ':'),
                )
            except Exception:
                raise ValueError('budget reservation unavailable') from None
            now = _utcnow()
            cursor = conn.execute(
                'UPDATE generation_run SET metrics_json = ?, updated_at = ? WHERE id = ? AND status = ? AND metrics_json = ?',
                (metrics_json, now, run_id, run['status'], run['metrics_json']),
            )
            if cursor.rowcount != 1:
                raise ValueError('generation run changed')
            return dict(reservation)
    except ValueError:
        raise
    except Exception:
        raise ValueError('budget reservation unavailable') from None
