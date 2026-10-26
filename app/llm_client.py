from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Final, NoReturn

import httpx

from .config import AppConfig

_PROVIDER_BASE: Final[str] = 'https://openrouter.ai/api/v1'
_CHAT_PATH: Final[str] = '/chat/completions'
_MAX_RESPONSE_BYTES: Final[int] = 1_048_576
_MAX_MESSAGES: Final[int] = 32
_REQUEST_ID = re.compile(r'[A-Za-z0-9_-]{1,120}')
_ROLES: Final[frozenset[str]] = frozenset({'system', 'user', 'assistant'})
_MESSAGE_KEYS: Final[frozenset[str]] = frozenset({'role', 'content'})
_ROLE_OVERHEAD: Final[int] = 8
_REQUEST_OVERHEAD: Final[int] = 8
_SAFE_MESSAGE: Final[str] = 'LLM request failed'


class LLMError(Exception):
    code: str
    retryable: bool
    outcome_unknown: bool

    def __init__(self, code: str, *, retryable: bool = False, outcome_unknown: bool = False) -> None:
        super().__init__(_SAFE_MESSAGE)
        self.code = code
        self.retryable = retryable
        self.outcome_unknown = outcome_unknown


@dataclass(frozen=True, slots=True)
class LLMResult:
    text: str = field(repr=False)
    model: str
    input_tokens: int
    output_tokens: int
    request_id: str
    provider: str | None = None
    reported_cost: str | None = None
    response_id: str | None = None


def _raise_error(code: str, *, retryable: bool = False, outcome_unknown: bool = False) -> NoReturn:
    raise LLMError(code, retryable=retryable, outcome_unknown=outcome_unknown) from None


def _has_control(value: str) -> bool:
    for char in value:
        point = ord(char)
        if point < 0x20 or 0x7F <= point <= 0x9F:
            return True
    return False


def _valid_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not _has_control(value)


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _freeze_response_schema(response_schema: Any) -> dict[str, Any]:
    if type(response_schema) is not dict:
        _raise_error('invalid_configuration')
    if response_schema.get('type') != 'object':
        _raise_error('invalid_configuration')
    properties = response_schema.get('properties')
    if not isinstance(properties, dict) or not properties:
        _raise_error('invalid_configuration')
    required = response_schema.get('required')
    if not isinstance(required, list):
        _raise_error('invalid_configuration')
    if any(not isinstance(name, str) for name in required):
        _raise_error('invalid_configuration')
    if len(set(required)) != len(required):
        _raise_error('invalid_configuration')
    if set(required) != set(properties.keys()):
        _raise_error('invalid_configuration')
    if response_schema.get('additionalProperties') is not False:
        _raise_error('invalid_configuration')
    try:
        encoded = json.dumps(response_schema, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, OverflowError):
        _raise_error('invalid_configuration')
    if len(encoded) > 24000:
        _raise_error('invalid_configuration')
    try:
        schema = json.loads(encoded)
    except (TypeError, ValueError, UnicodeError):
        _raise_error('invalid_configuration')
    if type(schema) is not dict:
        _raise_error('invalid_configuration')
    return schema


def _validate_config(config: AppConfig) -> None:
    if not isinstance(config, AppConfig):
        _raise_error('invalid_configuration')
    model = getattr(config, 'model', None)
    api_key = getattr(config, 'api_key', None)
    api_base = getattr(config, 'api_base', None)
    if not _valid_text(model) or not _valid_text(api_key):
        _raise_error('invalid_configuration')
    if api_base != _PROVIDER_BASE:
        _raise_error('invalid_configuration')
    if not isinstance(getattr(config, 'llm_enabled', None), bool):
        _raise_error('invalid_configuration')
    for name in ('max_input_tokens', 'max_output_tokens', 'max_total_tokens_per_run'):
        if not _is_positive_int(getattr(config, name, None)):
            _raise_error('invalid_configuration')
    timeout = getattr(config, 'timeout_seconds', None)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        _raise_error('invalid_configuration')


def _validate_messages(messages: Any) -> None:
    if not isinstance(messages, list) or not 1 <= len(messages) <= _MAX_MESSAGES:
        _raise_error('invalid_messages')
    for message in messages:
        if not isinstance(message, dict) or set(message.keys()) != _MESSAGE_KEYS:
            _raise_error('invalid_messages')
        role = message.get('role')
        content = message.get('content')
        if not isinstance(role, str) or role not in _ROLES:
            _raise_error('invalid_messages')
        if not isinstance(content, str) or not content.strip():
            _raise_error('invalid_messages')


def _input_upper_bound(messages: list[dict[str, Any]]) -> int:
    total = _REQUEST_OVERHEAD
    for message in messages:
        total += len(message['content'].encode('utf-8')) + _ROLE_OVERHEAD
    return total


def _raise_status(status: int) -> NoReturn:
    if status in (401, 403):
        _raise_error('provider_auth')
    if status == 429:
        _raise_error('rate_limited', retryable=True)
    if 500 <= status <= 599:
        _raise_error('provider_server', outcome_unknown=True)
    if 300 <= status <= 399:
        _raise_error('provider_redirect')
    if 400 <= status <= 499:
        _raise_error('provider_request')
    _raise_error('invalid_response')


def _read_bounded_body(response: httpx.Response) -> bytes:
    declared = response.headers.get('content-length')
    if declared is not None:
        try:
            if int(declared) > _MAX_RESPONSE_BYTES:
                _raise_error('response_too_large')
        except ValueError:
            pass
    data = bytearray()
    for chunk in response.iter_bytes():
        if len(data) + len(chunk) > _MAX_RESPONSE_BYTES:
            _raise_error('response_too_large')
        data.extend(chunk)
    return bytes(data)


def _parse_success(
    body: bytes,
    config: AppConfig,
    request_id: str,
    *,
    response_model_aliases: tuple[str, ...] = (),
) -> LLMResult:
    try:
        payload = json.loads(body.decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        _raise_error('invalid_response')
    if not isinstance(payload, dict):
        _raise_error('invalid_response')
    response_model = payload.get('model')
    if response_model != config.model and response_model not in response_model_aliases:
        _raise_error('invalid_response')
    choices = payload.get('choices')
    if not isinstance(choices, list) or len(choices) != 1:
        _raise_error('invalid_response')
    choice = choices[0]
    if not isinstance(choice, dict):
        _raise_error('invalid_response')
    message = choice.get('message')
    if not isinstance(message, dict) or message.get('role') != 'assistant':
        _raise_error('invalid_response')
    tool_calls = message.get('tool_calls')
    if tool_calls not in (None, []):
        _raise_error('invalid_response')
    text = message.get('content')
    if not isinstance(text, str) or not text:
        _raise_error('invalid_response')
    finish_reason = choice.get('finish_reason')
    if finish_reason == 'length':
        _raise_error('output_limit')
    if finish_reason != 'stop':
        _raise_error('invalid_response')
    usage = payload.get('usage')
    if not isinstance(usage, dict):
        _raise_error('invalid_response')
    input_tokens = usage.get('prompt_tokens')
    output_tokens = usage.get('completion_tokens')
    if not _is_nonnegative_int(input_tokens) or not _is_nonnegative_int(output_tokens):
        _raise_error('invalid_response')
    if input_tokens > config.max_input_tokens:
        _raise_error('input_limit')
    if output_tokens > config.max_output_tokens:
        _raise_error('output_limit')
    if input_tokens + output_tokens > config.max_total_tokens_per_run:
        _raise_error('total_limit')
    provider_value = payload.get('provider') if isinstance(payload, dict) else None
    response_id_value = payload.get('id') if isinstance(payload, dict) else None
    cost_value = usage.get('cost') if isinstance(usage, dict) else None

    provider = None
    if provider_value is not None:
        if (
            not isinstance(provider_value, str)
            or not provider_value.strip()
            or len(provider_value) > 160
            or _has_control(provider_value)
        ):
            _raise_error('invalid_response')
        provider = provider_value

    response_id = None
    if response_id_value is not None:
        if (
            not isinstance(response_id_value, str)
            or not response_id_value.strip()
            or len(response_id_value) > 160
            or _has_control(response_id_value)
        ):
            _raise_error('invalid_response')
        response_id = response_id_value

    reported_cost = None
    if cost_value is not None:
        if isinstance(cost_value, bool) or not isinstance(cost_value, (int, float, str)):
            _raise_error('invalid_response')
        from decimal import Decimal, InvalidOperation

        try:
            cost_decimal = Decimal(str(cost_value))
        except (InvalidOperation, ValueError):
            cost_decimal = None
        if cost_decimal is None or not cost_decimal.is_finite() or cost_decimal < 0:
            _raise_error('invalid_response')
        reported_cost = str(cost_decimal)

    return LLMResult(
        text=text,
        model=config.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        request_id=request_id,
        provider=provider,
        reported_cost=reported_cost,
        response_id=response_id,
    )


class LLMClient:
    def __init__(
        self,
        config: AppConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        allow_remote: bool = False,
        response_model_aliases: tuple[str, ...] = (),
        reasoning_enabled: bool = False,
        response_schema: dict | None = None,
    ) -> None:
        _validate_config(config)
        if not isinstance(response_model_aliases, tuple):
            _raise_error('invalid_configuration')
        if len(response_model_aliases) > 4:
            _raise_error('invalid_configuration')
        for alias in response_model_aliases:
            if not isinstance(alias, str):
                _raise_error('invalid_configuration')
        if len(set(response_model_aliases)) != len(response_model_aliases):
            _raise_error('invalid_configuration')
        alias_pattern = re.compile(re.escape(config.model) + r'-[0-9]{8}')
        for alias in response_model_aliases:
            if len(alias) > 160 or not alias.isascii():
                _raise_error('invalid_configuration')
            if alias_pattern.fullmatch(alias) is None:
                _raise_error('invalid_configuration')
        self._config = config
        self._response_model_aliases = response_model_aliases
        if type(reasoning_enabled) is not bool:
            _raise_error('invalid_configuration')
        self._reasoning_enabled = reasoning_enabled
        if response_schema is None:
            self._response_schema = None
        else:
            self._response_schema = _freeze_response_schema(response_schema)
        self._closed = False
        if transport is None and not allow_remote:
            _raise_error('remote_disabled')
        try:
            verify = True
            if transport is None:
                import ssl
                import truststore

                verify = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                if not (
                    verify.check_hostname is True
                    and verify.verify_mode == ssl.CERT_REQUIRED
                ):
                    _raise_error('invalid_configuration')
            self._client = httpx.Client(
                transport=transport,
                verify=verify,
                trust_env=False,
                follow_redirects=False,
                timeout=config.timeout_seconds,
            )
        except Exception:
            _raise_error('invalid_configuration')

    def __repr__(self) -> str:
        return '<LLMClient>'

    def __enter__(self) -> 'LLMClient':
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._client.close()
        except Exception:
            pass

    def complete(self, messages: list[dict], *, request_id: str) -> LLMResult:
        config = self._config
        if not config.llm_enabled:
            _raise_error('disabled')
        if self._closed:
            _raise_error('client_closed')
        if not isinstance(request_id, str) or _REQUEST_ID.fullmatch(request_id) is None:
            _raise_error('invalid_request_id')
        _validate_messages(messages)
        if _input_upper_bound(messages) > config.max_input_tokens:
            _raise_error('input_limit')
        response_format = {'type': 'json_object'}
        if self._response_schema is not None:
            response_format = {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'growwithai_response',
                    'strict': True,
                    'schema': self._response_schema,
                },
            }
        payload = {
            'model': config.model,
            'messages': [{'role': message['role'], 'content': message['content']} for message in messages],
            'max_tokens': config.max_output_tokens,
            'stream': False,
            'response_format': response_format,
            'reasoning': {'enabled': self._reasoning_enabled, 'exclude': True},
        }
        if self._response_schema is not None:
            payload['provider'] = {'require_parameters': True}
        headers = {'Authorization': f'Bearer {config.api_key}'}
        try:
            with self._client.stream(
                'POST',
                _PROVIDER_BASE + _CHAT_PATH,
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    _raise_status(response.status_code)
                body = _read_bounded_body(response)
        except LLMError:
            raise
        except httpx.TimeoutException:
            _raise_error('provider_transport', outcome_unknown=True)
        except httpx.TransportError:
            _raise_error('provider_transport', outcome_unknown=True)
        except Exception:
            _raise_error('provider_transport', outcome_unknown=True)
        return _parse_success(
            body,
            config,
            request_id,
            response_model_aliases=self._response_model_aliases,
        )
