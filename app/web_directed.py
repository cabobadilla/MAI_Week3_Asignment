from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from . import distribution, storage, web_auth


def _invalid_request() -> JSONResponse:
    return JSONResponse(
        {"detail": "Solicitud inválida."},
        status_code=400,
    )


def _service_unavailable() -> JSONResponse:
    return JSONResponse(
        {"detail": "Servicio temporalmente no disponible."},
        status_code=503,
    )


def mount_directed(app, db_path: Path) -> None:
    router = APIRouter(
        dependencies=[Depends(app.state.require_operator)],
    )

    @router.post("/api/campaigns/{cid}/directed")
    async def directed_batch(cid: str, request: Request):
        payload, error = await web_auth._read_json_object(request)
        if error is not None:
            return error

        if not isinstance(payload, dict):
            return _invalid_request()
        allowed = {"version_id", "recipient_ids", "occurred_at", "operation_id", "confirmed", "repeat_reason"}
        if set(payload) - allowed:
            return _invalid_request()

        try:
            version_id = payload["version_id"]
            recipient_ids = payload["recipient_ids"]
            occurred_at = payload["occurred_at"]
            operation_id = payload["operation_id"]
            confirmed = payload["confirmed"]
        except (KeyError, TypeError):
            return _invalid_request()

        repeat_reason = payload.get("repeat_reason")

        if confirmed is not True:
            return _invalid_request()
        if not isinstance(version_id, str):
            return _invalid_request()
        if not isinstance(occurred_at, str):
            return _invalid_request()
        if not isinstance(operation_id, str):
            return _invalid_request()
        if not isinstance(recipient_ids, list):
            return _invalid_request()
        if not all(isinstance(recipient_id, str) for recipient_id in recipient_ids):
            return _invalid_request()
        if repeat_reason is not None and not isinstance(repeat_reason, str):
            return _invalid_request()

        try:
            conn = storage.connect(db_path)
        except sqlite3.Error:
            return _service_unavailable()

        try:
            rows = distribution.record_email_batch(
                conn,
                cid,
                version_id,
                recipient_ids,
                occurred_at,
                operation_id,
                confirmed=True,
                actor="operator",
                repeat_reason=repeat_reason,
            )
        except ValueError:
            return _invalid_request()
        except sqlite3.Error:
            return _service_unavailable()
        finally:
            conn.close()

        return JSONResponse([dict(row) for row in rows])

    app.include_router(router)
