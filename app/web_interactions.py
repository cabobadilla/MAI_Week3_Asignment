from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from . import followup, storage, web_auth

_ALLOWED_KEYS = frozenset(
    {
        'kind',
        'body',
        'occurred_at',
        'event_id',
        'campaign_recipient_id',
        'distribution_id',
    }
)
_REQUIRED_KEYS = ('kind', 'body', 'occurred_at', 'event_id')
_BAD_REQUEST = 'Solicitud no válida'
_UNAVAILABLE = 'Servicio no disponible'


def _optional_ref(payload: dict, key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError
    return value


def mount_interactions(app, db_path: Path) -> None:
    router = APIRouter()

    @router.post('/api/campaigns/{cid}/interactions')
    async def create_interaction(
        cid: str,
        request: Request,
        _operator=Depends(app.state.require_operator),
    ):
        try:
            payload, error = await web_auth._read_json_object(request)
            if error is not None:
                return error

            if not isinstance(payload, dict):
                raise ValueError
            if any(key not in _ALLOWED_KEYS for key in payload):
                raise ValueError
            if any(key not in payload for key in _REQUIRED_KEYS):
                raise ValueError

            kind = payload['kind']
            if kind not in {'note', 'response'}:
                raise ValueError

            event_id = payload['event_id']
            if not isinstance(event_id, str) or not event_id:
                raise ValueError

            campaign_recipient_id = _optional_ref(payload, 'campaign_recipient_id')
            distribution_id = _optional_ref(payload, 'distribution_id')
            if campaign_recipient_id is None and distribution_id is None:
                raise ValueError

            conn = storage.connect(db_path)
            try:
                if distribution_id is not None:
                    row = conn.execute(
                        '''
                        SELECT kind
                        FROM distribution_record
                        WHERE id = ? AND campaign_id = ?
                        ''',
                        (distribution_id, cid),
                    ).fetchone()
                    if row is None:
                        raise ValueError

                    distribution_kind = row[0]
                    if distribution_kind in ('publication', 'public'):
                        if kind != 'note' or campaign_recipient_id is not None:
                            raise ValueError

                result = followup.add_followup(
                    conn,
                    cid,
                    kind,
                    payload['body'],
                    payload['occurred_at'],
                    campaign_recipient_id=campaign_recipient_id,
                    distribution_id=distribution_id,
                    actor='operator',
                    event_id=event_id,
                )
            finally:
                conn.close()

            return result
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={'detail': _BAD_REQUEST},
            )
        except (sqlite3.Error, OSError):
            return JSONResponse(
                status_code=503,
                content={'detail': _UNAVAILABLE},
            )

    app.include_router(router)
