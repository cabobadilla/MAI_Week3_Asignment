'''Offline TOML configuration loading.'''
from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

_API_BASE = 'https://openrouter.ai/api/v1'

__all__ = ['AppConfig', 'load_config']


@dataclass(frozen=True)
class AppConfig:
    host: str
    port: int
    llm_enabled: bool
    model: str | None
    api_key: str | None = field(repr=False)
    api_base: str
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens_per_run: int
    max_request_attempts_per_run: int
    max_retries: int
    timeout_seconds: int
    budget_control: str

    def safe_summary(self) -> dict[str, object]:
        data = asdict(self)
        data.pop('api_key', None)
        return data


def _toml_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f'{name} must be a boolean')
    return value


def _env_bool(env: Mapping[str, str], name: str) -> bool | None:
    if name not in env:
        return None
    value = env[name]
    if not isinstance(value, str):
        raise ValueError(f'{name} must be true or false')
    if value == 'true':
        return True
    if value == 'false':
        return False
    raise ValueError(f'{name} must be true or false')


def _int(value: object, name: str, minimum: int, maximum: int | None = None, from_env: bool = False) -> int:
    if from_env:
        if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
            raise ValueError(f'{name} must be an integer')
        try:
            number = int(value)
        except ValueError:
            raise ValueError(f'{name} must be an integer') from None
    else:
        if type(value) is not int:
            raise ValueError(f'{name} must be an integer')
        number = value
    if number < minimum or (maximum is not None and number > maximum):
        if maximum is None:
            raise ValueError(f'{name} must be at least {minimum}')
        raise ValueError(f'{name} must be between {minimum} and {maximum}')
    return number


def _env_int(env: Mapping[str, str], name: str, minimum: int, maximum: int | None = None) -> int | None:
    if name not in env:
        return None
    return _int(env[name], name, minimum, maximum, True)


def _toml_int(value: object, name: str, minimum: int, maximum: int | None = None) -> int:
    return _int(value, name, minimum, maximum, False)


def _env_override(env: Mapping[str, str], name: str, current: int, minimum: int, maximum: int | None = None) -> int:
    value = _env_int(env, name, minimum, maximum)
    return current if value is None else value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f'{name} must be a non-empty string')
    return value


def _env_text(env: Mapping[str, str], name: str) -> str | None:
    if name not in env:
        return None
    value = env[name]
    if not isinstance(value, str):
        raise ValueError(f'{name} must be a string')
    if not value.strip():
        return None
    return value


def _valid_model(value: str, name: str) -> str:
    if value != value.strip() or value.count('/') != 1 or any(c.isspace() for c in value):
        raise ValueError(f'{name} must use provider/model syntax')
    provider, model_name = value.split('/', 1)
    if not provider or not model_name:
        raise ValueError(f'{name} must use provider/model syntax')
    return value


def load_config(env: Mapping[str, str], config_path: Path) -> AppConfig:
    try:
        with Path(config_path).open('rb') as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        raise ValueError('Unable to read configuration file') from None
    if not isinstance(data, dict):
        raise ValueError('Configuration must be a TOML table')
    app = data.get('app', {})
    llm = data.get('llm', {})
    if not isinstance(app, dict) or not isinstance(llm, dict):
        raise ValueError('Invalid configuration sections')

    host = _text(app.get('host', '127.0.0.1'), 'host')
    if host not in ('127.0.0.1', 'localhost'):
        raise ValueError('host must be 127.0.0.1 or localhost')
    port = _toml_int(app.get('port', 8501), 'port', 1, 65535)

    provider = _text(llm.get('provider', 'openrouter'), 'provider')
    if provider != 'openrouter':
        raise ValueError('provider must be openrouter')
    api_base = _text(llm.get('api_base', _API_BASE), 'api_base')
    if api_base != _API_BASE:
        raise ValueError('api_base must be the official OpenRouter endpoint')
    if _toml_bool(llm.get('model_fallback', False), 'model_fallback'):
        raise ValueError('model_fallback must be false')
    budget_control = _text(llm.get('budget_control', 'user_managed_api_key'), 'budget_control')
    enabled_env = _text(llm.get('enabled_env', 'APP_LLM_ENABLED'), 'enabled_env')
    model_env = _text(llm.get('model_env', 'APP_LLM_MODEL'), 'model_env')
    api_key_env = _text(llm.get('api_key_env', 'OPENROUTER_API_KEY'), 'api_key_env')

    enabled = _toml_bool(llm.get('enabled_default', False), 'enabled_default')
    enabled_override = _env_bool(env, enabled_env)
    if enabled_override is not None:
        enabled = enabled_override

    max_input_tokens = _toml_int(llm.get('max_input_tokens', 12000), 'max_input_tokens', 1)
    max_input_tokens = _env_override(env, 'APP_LLM_MAX_INPUT_TOKENS', max_input_tokens, 1)
    max_output_tokens = _toml_int(llm.get('max_output_tokens', 4096), 'max_output_tokens', 1)
    max_output_tokens = _env_override(env, 'APP_LLM_MAX_OUTPUT_TOKENS', max_output_tokens, 1)
    max_total_tokens_per_run = _toml_int(llm.get('max_total_tokens_per_run', 64000), 'max_total_tokens_per_run', 1)
    max_total_tokens_per_run = _env_override(env, 'APP_LLM_MAX_TOTAL_TOKENS_PER_RUN', max_total_tokens_per_run, 1)
    max_request_attempts_per_run = _toml_int(llm.get('max_request_attempts_per_run', 8), 'max_request_attempts_per_run', 1)
    max_request_attempts_per_run = _env_override(env, 'APP_LLM_MAX_REQUEST_ATTEMPTS_PER_RUN', max_request_attempts_per_run, 1)
    max_retries = _toml_int(llm.get('max_retries', 2), 'max_retries', 0, 2)
    max_retries = _env_override(env, 'APP_LLM_MAX_RETRIES', max_retries, 0, 2)
    timeout_seconds = _toml_int(llm.get('timeout_seconds', 30), 'timeout_seconds', 1)
    timeout_seconds = _env_override(env, 'APP_LLM_TIMEOUT_SECONDS', timeout_seconds, 1)

    if max_input_tokens + max_output_tokens > max_total_tokens_per_run:
        raise ValueError('APP_LLM_MAX_INPUT_TOKENS + APP_LLM_MAX_OUTPUT_TOKENS must not exceed APP_LLM_MAX_TOTAL_TOKENS_PER_RUN')

    api_key = _env_text(env, api_key_env)
    model = _env_text(env, model_env)
    if enabled:
        if api_key is None:
            raise ValueError(f'{api_key_env} is required when {enabled_env} is true')
        if model is None:
            raise ValueError(f'{model_env} is required when {enabled_env} is true')
        model = _valid_model(model, model_env)
    else:
        api_key = None
        model = None

    return AppConfig(
        host=host,
        port=port,
        llm_enabled=enabled,
        model=model,
        api_key=api_key,
        api_base=api_base,
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens,
        max_total_tokens_per_run=max_total_tokens_per_run,
        max_request_attempts_per_run=max_request_attempts_per_run,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        budget_control=budget_control,
    )
