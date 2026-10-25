from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from . import campaigns, demo_generation, runs, storage
from .web_auth import _read_json_object

_BAD_REQUEST = 'Solicitud no válida'
_UNAVAILABLE = 'Servicio no disponible'


def _bad_request() -> JSONResponse:
    return JSONResponse(status_code=400, content={'detail': _BAD_REQUEST})


def _unavailable() -> JSONResponse:
    return JSONResponse(status_code=503, content={'detail': _UNAVAILABLE})


def _is_bad_request_error(exc: BaseException) -> bool:
    if isinstance(exc, ValueError):
        return True
    return any(cls.__name__ == 'ServiceValueError' for cls in type(exc).__mro__)


def _is_uuid4_text(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return uuid.UUID(value).version == 4
    except (AttributeError, TypeError, ValueError):
        return False


def mount_demo(app: Any, db_path: Path) -> None:
    router = APIRouter(dependencies=[Depends(app.state.require_operator)])

    @router.post('/api/campaigns/{campaign_id}/demo', name='demo')
    async def demo(campaign_id: str, request: Request) -> Any:
        payload, error = await _read_json_object(request)
        if error is not None:
            return error
        if not isinstance(payload, dict):
            return _bad_request()
        if set(payload) - {'run_id'}:
            return _bad_request()

        run_id: str | None = None
        if 'run_id' in payload:
            candidate = payload['run_id']
            if not _is_uuid4_text(candidate):
                return _bad_request()
            run_id = candidate

        conn = None
        try:
            conn = storage.connect(db_path)
            return demo_generation.generate_demo(conn, campaign_id, run_id=run_id)
        except sqlite3.Error:
            return _unavailable()
        except Exception as exc:
            if _is_bad_request_error(exc):
                return _bad_request()
            raise
        finally:
            if conn is not None:
                conn.close()

    @router.get('/api/runs/{run_id}/bundle', name='bundle')
    async def bundle(run_id: str) -> Any:
        conn = None
        try:
            conn = storage.connect(db_path)
            return demo_generation.get_demo_bundle(conn, run_id)
        except sqlite3.Error:
            return _unavailable()
        except Exception as exc:
            if _is_bad_request_error(exc):
                return _bad_request()
            raise
        finally:
            if conn is not None:
                conn.close()

    @router.get('/api/campaigns/{campaign_id}/runs', name='campaign_runs')
    async def campaign_runs(campaign_id: str) -> Any:
        conn = None
        try:
            conn = storage.connect(db_path)
            campaigns.get_campaign(conn, campaign_id)
            return runs.list_runs(conn, campaign_id)
        except sqlite3.Error:
            return _unavailable()
        except Exception as exc:
            if _is_bad_request_error(exc):
                return _bad_request()
            raise
        finally:
            if conn is not None:
                conn.close()

    app.include_router(router)
