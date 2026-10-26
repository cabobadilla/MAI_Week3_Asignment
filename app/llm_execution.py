from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import AppConfig
from .llm_client import LLMError, LLMResult

from .run_budget import reserve_call
from .runs import _atomic, get_run

__all__ = ['CallOutcomeUnknown', 'execute_call', 'LLMError', 'LLMResult']

_REQUEST_ID_RE = re.compile(r'[A-Za-z0-9_-]{1,120}')
_STAGES = frozenset(('generator', 'reviewer'))
_MESSAGE_ROLES = frozenset(('system', 'user', 'assistant'))
_MISSING = object()


class CallOutcomeUnknown(ValueError):
    def __init__(self, message: str = 'LLM call outcome is unknown') -> None:
        super().__init__(message)


def _compact_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _message_hash(messages: list[dict[str, str]]) -> str:
    return hashlib.sha256(_compact_json(messages).encode('utf-8')).hexdigest()


def _validate_inputs(
    conn: Any,
    request_id: str,
    messages: Any,
    stage: str,
    config: AppConfig,
    client: Any,
) -> tuple[list[dict[str, str]], str, str, int, int, int]:
    if getattr(conn, 'in_transaction', False):
        raise ValueError('invalid call context')
    if type(request_id) is not str or _REQUEST_ID_RE.fullmatch(request_id) is None:
        raise ValueError('invalid request')
    if type(messages) is not list or not 1 <= len(messages) <= 32:
        raise ValueError('invalid messages')
    safe_messages: list[dict[str, str]] = []
    for message in messages:
        if type(message) is not dict or set(message.keys()) != {'role', 'content'}:
            raise ValueError('invalid messages')
        role = message['role']
        content = message['content']
        if type(role) is not str or role not in _MESSAGE_ROLES:
            raise ValueError('invalid messages')
        if type(content) is not str or not content.strip():
            raise ValueError('invalid messages')
        safe_messages.append({'role': role, 'content': content})
    if type(stage) is not str or stage not in _STAGES:
        raise ValueError('invalid stage')
    if not callable(getattr(client, 'complete', None)):
        raise ValueError('invalid client')

    model = getattr(config, 'model', None)
    if type(model) is not str or not model.strip():
        raise ValueError('invalid config')
    max_input_tokens = getattr(config, 'max_input_tokens', None)
    max_output_tokens = getattr(config, 'max_output_tokens', None)
    if type(max_input_tokens) is not int or max_input_tokens < 0:
        raise ValueError('invalid config')
    if type(max_output_tokens) is not int or max_output_tokens < 0:
        raise ValueError('invalid config')

    input_tokens = 8 + sum(
        len(item['content'].encode('utf-8')) + 8 for item in safe_messages
    )
    if input_tokens > max_input_tokens:
        raise ValueError('input too large')
    return (
        safe_messages,
        _message_hash(safe_messages),
        model,
        max_input_tokens,
        max_output_tokens,
        input_tokens,
    )


def _metrics_from_run(run: Any) -> tuple[dict[str, Any], str]:
    if not isinstance(run, dict):
        raise ValueError('invalid run')
    metrics = run.get('metrics')
    metrics_json = run.get('metrics_json')
    if metrics is None:
        if not isinstance(metrics_json, str):
            raise ValueError('invalid run')
        try:
            metrics = json.loads(metrics_json)
        except (TypeError, ValueError):
            raise ValueError('invalid run') from None
    if not isinstance(metrics, dict):
        raise ValueError('invalid run')
    if not isinstance(metrics_json, str):
        metrics_json = _compact_json(metrics)
    return metrics, metrics_json


def _llm_calls(metrics: dict[str, Any]) -> dict[str, Any]:
    calls = metrics.get('llm_calls')
    if calls is None:
        return {}
    if not isinstance(calls, dict):
        raise ValueError('invalid run')
    return calls


def _payload_matches(
    entry: Any,
    stage: str,
    model: str,
    message_hash: str,
) -> bool:
    return (
        isinstance(entry, dict)
        and entry.get('stage') == stage
        and entry.get('model') == model
        and entry.get('message_hash') == message_hash
    )


def _write_running_metrics(
    conn: Any,
    run_id: str,
    expected_metrics_json: str,
    metrics: dict[str, Any],
) -> None:
    cursor = conn.execute(
        'UPDATE generation_run SET metrics_json = ?, updated_at = ? '
        'WHERE id = ? AND status = ? AND metrics_json = ?',
        (
            _compact_json(metrics),
            _now(),
            run_id,
            'running',
            expected_metrics_json,
        ),
    )
    if cursor.rowcount != 1:
        raise ValueError('unable to persist call')


def _rehydrate(
    entry: dict[str, Any],
    request_id: str,
    model: str,
) -> LLMResult:
    stored = entry.get('result')
    if not isinstance(stored, dict):
        raise ValueError('invalid prior result')
    text = stored.get('text')
    stored_model = stored.get('model')
    stored_request_id = stored.get('request_id')
    input_tokens = stored.get('input_tokens')
    output_tokens = stored.get('output_tokens')
    if type(text) is not str or not text.strip():
        raise ValueError('invalid prior result')
    if stored_model != model or stored_request_id != request_id:
        raise ValueError('invalid prior result')
    if type(input_tokens) is not int or input_tokens < 0:
        raise ValueError('invalid prior result')
    if type(output_tokens) is not int or output_tokens < 0:
        raise ValueError('invalid prior result')
    return LLMResult(
        text=text,
        model=stored_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        request_id=stored_request_id,
        provider=stored.get('provider'),
        reported_cost=stored.get('reported_cost'),
        response_id=stored.get('response_id'),
    )


def _entry_error_fields(entry: dict[str, Any]) -> tuple[str, bool, bool]:
    nested = entry.get('error')
    if not isinstance(nested, dict):
        nested = {}
    code = entry.get('code', nested.get('code'))
    retryable = entry.get('retryable', nested.get('retryable', False))
    outcome_unknown = entry.get(
        'outcome_unknown',
        nested.get('outcome_unknown', False),
    )
    if type(code) is not str:
        code = 'error'
    return code, bool(retryable), bool(outcome_unknown)


def _safe_error_fields(error: LLMError) -> tuple[str, bool, bool]:
    code = getattr(error, 'code', None)
    if type(code) is not str:
        code = 'error'
    return (
        code,
        bool(getattr(error, 'retryable', False)),
        bool(getattr(error, 'outcome_unknown', False)),
    )


def _validated_result(
    result: Any,
    *,
    request_id: str,
    model: str,
    max_input_tokens: int,
    max_output_tokens: int,
) -> LLMResult:
    if not isinstance(result, LLMResult):
        raise ValueError('invalid result')
    text = getattr(result, 'text', None)
    result_model = getattr(result, 'model', None)
    result_request_id = getattr(result, 'request_id', None)
    input_tokens = getattr(result, 'input_tokens', None)
    output_tokens = getattr(result, 'output_tokens', None)
    if type(text) is not str or not text.strip():
        raise ValueError('invalid result')
    if result_model != model or result_request_id != request_id:
        raise ValueError('invalid result')
    if (
        type(input_tokens) is not int
        or input_tokens < 0
        or input_tokens > max_input_tokens
    ):
        raise ValueError('invalid result')
    if (
        type(output_tokens) is not int
        or output_tokens < 0
        or output_tokens > max_output_tokens
    ):
        raise ValueError('invalid result')
    return LLMResult(
        text=text,
        model=result_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        request_id=result_request_id,
        provider=result.provider,
        reported_cost=result.reported_cost,
        response_id=result.response_id,
    )


def _persist_terminal(
    conn: Any,
    run_id: str,
    request_id: str,
    *,
    stage: str,
    model: str,
    message_hash: str,
    status: str,
    result: dict[str, Any] | None = None,
    error: tuple[str, bool, bool] | None = None,
) -> None:
    try:
        with _atomic(conn):
            run = get_run(conn, run_id)
            if not isinstance(run, dict) or run.get('status') != 'running':
                raise RuntimeError('run unavailable')
            metrics, metrics_json = _metrics_from_run(run)
            calls = _llm_calls(metrics)
            entry = calls.get(request_id, _MISSING)
            if not isinstance(entry, dict):
                raise RuntimeError('ledger unavailable')
            if (
                entry.get('status') != 'started'
                or entry.get('stage') != stage
                or entry.get('model') != model
                or entry.get('message_hash') != message_hash
            ):
                raise RuntimeError('ledger changed')

            updated_entry = dict(entry)
            updated_entry['status'] = status
            if result is not None:
                updated_entry.pop('code', None)
                updated_entry.pop('retryable', None)
                updated_entry.pop('outcome_unknown', None)
                updated_entry['result'] = result
            elif error is not None:
                updated_entry.pop('result', None)
                code, retryable, outcome_unknown = error
                updated_entry['code'] = code
                updated_entry['retryable'] = bool(retryable)
                updated_entry['outcome_unknown'] = bool(outcome_unknown)
            else:
                updated_entry.pop('result', None)
                updated_entry.pop('code', None)
                updated_entry.pop('retryable', None)
                updated_entry.pop('outcome_unknown', None)

            updated_calls = dict(calls)
            updated_calls[request_id] = updated_entry
            updated_metrics = dict(metrics)
            updated_metrics['llm_calls'] = updated_calls
            _write_running_metrics(conn, run_id, metrics_json, updated_metrics)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise CallOutcomeUnknown() from None


def execute_call(
    conn: Any,
    run_id: str,
    request_id: str,
    messages: list[dict[str, str]],
    *,
    stage: str,
    config: AppConfig,
    client: Any,
) -> LLMResult:
    (
        safe_messages,
        message_hash,
        model,
        max_input_tokens,
        max_output_tokens,
        input_tokens,
    ) = _validate_inputs(conn, request_id, messages, stage, config, client)

    with _atomic(conn):
        run = get_run(conn, run_id)
        if not isinstance(run, dict) or run.get('status') != 'running':
            raise ValueError('run is not available')
        metrics, _metrics_json = _metrics_from_run(run)
        calls = _llm_calls(metrics)
        existing = calls.get(request_id, _MISSING)
        if existing is not _MISSING:
            if not _payload_matches(existing, stage, model, message_hash):
                raise ValueError('request conflicts with a prior call')
            existing_status = existing.get('status')
            if existing_status == 'completed':
                return _rehydrate(existing, request_id, model)
            if existing_status in ('started', 'uncertain'):
                raise CallOutcomeUnknown()
            if existing_status == 'failed':
                code, retryable, outcome_unknown = _entry_error_fields(existing)
                raise LLMError(
                    code,
                    retryable=retryable,
                    outcome_unknown=outcome_unknown,
                ) from None
            raise ValueError('request conflicts with a prior call')

        reserve_call(
            conn,
            run_id,
            request_id,
            stage=stage,
            input_tokens=input_tokens,
            max_output_tokens=max_output_tokens,
            config=config,
        )
        updated_run = get_run(conn, run_id)
        if not isinstance(updated_run, dict) or updated_run.get('status') != 'running':
            raise ValueError('run is not available')
        updated_metrics, updated_metrics_json = _metrics_from_run(updated_run)
        updated_calls = _llm_calls(updated_metrics)
        if request_id in updated_calls:
            raise ValueError('request conflicts with a prior call')
        started_calls = dict(updated_calls)
        started_calls[request_id] = {
            'status': 'started',
            'stage': stage,
            'model': model,
            'message_hash': message_hash,
        }
        started_metrics = dict(updated_metrics)
        started_metrics['llm_calls'] = started_calls
        _write_running_metrics(
            conn,
            run_id,
            updated_metrics_json,
            started_metrics,
        )

    try:
        result = client.complete(safe_messages, request_id=request_id)
        validated = _validated_result(
            result,
            request_id=request_id,
            model=model,
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
        )
    except LLMError as error:
        code, retryable, outcome_unknown = _safe_error_fields(error)
        terminal_status = 'uncertain' if outcome_unknown else 'failed'
        _persist_terminal(
            conn,
            run_id,
            request_id,
            stage=stage,
            model=model,
            message_hash=message_hash,
            status=terminal_status,
            error=(code, retryable, outcome_unknown),
        )
        raise LLMError(
            code,
            retryable=retryable,
            outcome_unknown=outcome_unknown,
        ) from None
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        _persist_terminal(
            conn,
            run_id,
            request_id,
            stage=stage,
            model=model,
            message_hash=message_hash,
            status='uncertain',
        )
        raise CallOutcomeUnknown() from None
    else:
        stored_result = {
            'text': validated.text,
            'model': validated.model,
            'input_tokens': validated.input_tokens,
            'output_tokens': validated.output_tokens,
            'request_id': validated.request_id,
            'provider': validated.provider,
            'reported_cost': validated.reported_cost,
            'response_id': validated.response_id,
        }
        _persist_terminal(
            conn,
            run_id,
            request_id,
            stage=stage,
            model=model,
            message_hash=message_hash,
            status='completed',
            result=stored_result,
        )
        return validated
