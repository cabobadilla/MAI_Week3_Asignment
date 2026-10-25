from pathlib import Path
import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from . import distribution, storage, web_auth


_ALLOWED_FIELDS = frozenset({
    'version_id',
    'channel',
    'occurred_at',
    'operation_id',
    'confirmed',
    'public_url',
    'repeat_reason',
})
_REQUIRED_TEXT_FIELDS = ('version_id', 'channel', 'occurred_at', 'operation_id')


def _validate(payload):
    if not isinstance(payload, dict):
        raise ValueError
    if set(payload) - _ALLOWED_FIELDS:
        raise ValueError
    for field in _REQUIRED_TEXT_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError
    if payload.get('confirmed') is not True:
        raise ValueError
    public_url = payload.get('public_url')
    repeat_reason = payload.get('repeat_reason')
    if public_url is not None and not isinstance(public_url, str):
        raise ValueError
    if repeat_reason is not None and not isinstance(repeat_reason, str):
        raise ValueError
    return (
        payload['version_id'],
        payload['channel'],
        payload['occurred_at'],
        payload['operation_id'],
        public_url,
        repeat_reason,
    )


def mount_publications(app, db_path: Path) -> None:
    router = APIRouter(
        dependencies=[Depends(app.state.require_operator)],
    )

    @router.post('/api/campaigns/{cid}/publications')
    async def record_publication(cid: str, request: Request):
        try:
            payload, error = await web_auth._read_json_object(request)
            if error is not None:
                return error
            (
                version_id,
                channel,
                occurred_at,
                operation_id,
                public_url,
                repeat_reason,
            ) = _validate(payload)

            conn = storage.connect(db_path)
            try:
                record = distribution.record_publication(
                    conn,
                    cid,
                    version_id,
                    channel,
                    occurred_at,
                    operation_id,
                    confirmed=True,
                    actor='operator',
                    public_url=public_url,
                    repeat_reason=repeat_reason,
                )
            finally:
                conn.close()
            return {'record': record}
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={'detail': 'Solicitud no válida'},
            )
        except (sqlite3.Error, OSError):
            return JSONResponse(
                status_code=503,
                content={'detail': 'Servicio no disponible'},
            )

    app.include_router(router)
