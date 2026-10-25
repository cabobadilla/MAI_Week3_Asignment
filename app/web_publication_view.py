from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from . import campaigns, distribution, followup, storage, versions


def _value(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def mount_publication_view(app, db_path: Path) -> None:
    router = APIRouter(dependencies=[Depends(app.state.require_operator)])

    @router.get('/api/campaigns/{cid}/publications')
    def get_publications(cid: str):
        try:
            conn = storage.connect(db_path)
            try:
                campaign = campaigns.get_campaign(conn, cid)
                if campaign is None:
                    raise ValueError('missing campaign')

                public_versions = [
                    item
                    for item in versions.list_versions(
                        conn, cid, latest_only=False
                    )
                    if _value(item, 'format') in ('linkedin', 'article', 'ad')
                ]

                public_records = [
                    item
                    for item in distribution.list_distributions(
                        conn, cid, include_superseded=True
                    )
                    if _value(item, 'kind') == 'publication'
                ]

                record_ids = set()
                for item in public_records:
                    for key in ('id', 'distribution_id', 'record_id'):
                        value = _value(item, key)
                        if value is not None:
                            record_ids.add(value)

                notes = [
                    item
                    for item in followup.list_followups(
                        conn, cid, include_superseded=True
                    )
                    if _value(item, 'distribution_id') in record_ids
                ]

                return {
                    'campaign': campaign,
                    'versions': public_versions,
                    'records': public_records,
                    'notes': notes,
                }
            finally:
                conn.close()
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail='Solicitud no válida'
            ) from exc
        except (sqlite3.Error, OSError) as exc:
            raise HTTPException(
                status_code=503, detail='Servicio no disponible'
            ) from exc

    app.include_router(router)
