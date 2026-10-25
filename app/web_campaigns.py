from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from . import campaigns, storage

_MAX_BODY_BYTES = 64 * 1024
_INVALID_DETAIL = 'Solicitud inválida'
_UNAVAILABLE_DETAIL = 'Servicio no disponible'

_POST_KEYS = frozenset({
    'title',
    'topic',
    'objective',
    'audience_segment',
    'tone',
    'formats',
    'academic_suite',
})
_POST_REQUIRED_KEYS = frozenset({'title', 'topic', 'objective'})
_PUT_KEYS = frozenset({
    'title',
    'topic',
    'objective',
    'audience_segment',
    'tone',
    'formats',
    'expected_revision',
})
_TEXT_KEYS = frozenset({
    'title',
    'topic',
    'objective',
    'audience_segment',
    'tone',
})


def _invalid() -> HTTPException:
    return HTTPException(status_code=400, detail=_INVALID_DETAIL)


def _unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail=_UNAVAILABLE_DETAIL)


def _reject_nonstandard_json(value: str) -> Any:
    raise ValueError('invalid JSON constant')


async def _read_json_object(request: Request) -> dict[str, Any]:
    raw_length = request.headers.get('content-length')
    if raw_length is not None:
        try:
            content_length = int(raw_length)
        except (TypeError, ValueError):
            raise _invalid() from None
        if content_length < 0 or content_length > _MAX_BODY_BYTES:
            raise _invalid() from None

    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > _MAX_BODY_BYTES:
            raise _invalid() from None
        chunks.append(chunk)

    try:
        payload = json.loads(
            b''.join(chunks),
            parse_constant=_reject_nonstandard_json,
        )
    except (TypeError, ValueError):
        raise _invalid() from None

    if not isinstance(payload, dict):
        raise _invalid() from None
    return payload


def _validate_text_fields(payload: dict[str, Any]) -> None:
    for key in _TEXT_KEYS.intersection(payload):
        if not isinstance(payload[key], str):
            raise _invalid() from None


def _validate_create_payload(payload: dict[str, Any]) -> None:
    if set(payload) - _POST_KEYS:
        raise _invalid() from None
    if not _POST_REQUIRED_KEYS.issubset(payload):
        raise _invalid() from None
    _validate_text_fields(payload)
    if 'academic_suite' in payload and not isinstance(payload['academic_suite'], bool):
        raise _invalid() from None


def _validate_update_payload(payload: dict[str, Any]) -> None:
    if set(payload) - _PUT_KEYS:
        raise _invalid() from None
    _validate_text_fields(payload)
    if 'expected_revision' in payload:
        revision = payload['expected_revision']
        if isinstance(revision, bool) or not isinstance(revision, int):
            raise _invalid() from None


def mount_campaigns(app, db_path: Path) -> None:
    operator_dependency = app.state.require_operator
    router = APIRouter(
        prefix='/api/campaigns',
        tags=['campaigns'],
        dependencies=[Depends(operator_dependency)],
    )

    @router.get('', response_model=None)
    async def list_campaigns_endpoint() -> Any:
        conn = None
        try:
            conn = storage.connect(db_path)
            return campaigns.list_campaigns(conn)
        except ValueError:
            raise _invalid() from None
        except sqlite3.Error:
            raise _unavailable() from None
        finally:
            if conn is not None:
                conn.close()

    @router.get('/{campaign_id}', response_model=None)
    async def get_campaign_endpoint(campaign_id: str) -> Any:
        conn = None
        try:
            conn = storage.connect(db_path)
            return campaigns.get_campaign(conn, campaign_id)
        except ValueError:
            raise _invalid() from None
        except sqlite3.Error:
            raise _unavailable() from None
        finally:
            if conn is not None:
                conn.close()

    @router.post('', response_model=None)
    async def create_campaign_endpoint(request: Request) -> Any:
        payload = await _read_json_object(request)
        _validate_create_payload(payload)

        optional_fields = {
            key: payload[key]
            for key in ('audience_segment', 'tone', 'formats', 'academic_suite')
            if key in payload
        }

        conn = None
        try:
            conn = storage.connect(db_path)
            return campaigns.create_campaign(
                conn,
                payload['title'],
                payload['topic'],
                payload['objective'],
                **optional_fields,
            )
        except ValueError:
            raise _invalid() from None
        except sqlite3.Error:
            raise _unavailable() from None
        finally:
            if conn is not None:
                conn.close()

    @router.put('/{campaign_id}', response_model=None)
    async def update_campaign_endpoint(campaign_id: str, request: Request) -> Any:
        payload = await _read_json_object(request)
        _validate_update_payload(payload)

        conn = None
        try:
            conn = storage.connect(db_path)
            return campaigns.update_campaign(conn, campaign_id, **payload)
        except ValueError:
            raise _invalid() from None
        except sqlite3.Error:
            raise _unavailable() from None
        finally:
            if conn is not None:
                conn.close()

    app.include_router(router)


__all__ = ['mount_campaigns']