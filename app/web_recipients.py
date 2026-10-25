from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from . import campaigns, distribution, recipients, storage
from .web_auth import _read_json_object


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def mount_recipients(app, db_path: Path) -> None:
    router = APIRouter(dependencies=[Depends(app.state.require_operator)])

    @router.post("/api/campaigns/{cid}/recipients")
    async def select_campaign_recipients(cid: str, request: Request):
        payload, error = await _read_json_object(request)
        if error is not None:
            return error
        if not isinstance(payload, dict) or set(payload) != {"contact_ids"}:
            return _error(400, "Solicitud no válida")

        contact_ids = payload["contact_ids"]
        if not isinstance(contact_ids, list) or not contact_ids:
            return _error(400, "Solicitud no válida")
        if len(contact_ids) > distribution._MAX_RECIPIENTS:
            return _error(400, "Solicitud no válida")

        seen: set[str] = set()
        for contact_id in contact_ids:
            if not isinstance(contact_id, str) or not contact_id or contact_id in seen:
                return _error(400, "Solicitud no válida")
            seen.add(contact_id)

        conn = None
        try:
            conn = storage.connect(db_path)
            with distribution._transaction(conn):
                campaign = campaigns.get_campaign(conn, cid)
                if campaign is None or campaign["archived_at"] is not None:
                    raise ValueError("Campaña no disponible")

                existing = recipients.list_recipients(
                    conn, cid, include_archived=True
                )
                by_contact: dict[str, list[dict]] = {}
                for record in existing:
                    by_contact.setdefault(record["contact_id"], []).append(record)

                selected = []
                for contact_id in contact_ids:
                    contact = recipients._active_contact(conn, contact_id)
                    if contact is None:
                        raise ValueError("Contacto no disponible")

                    email_key = contact["email_key"]
                    records = by_contact.get(contact_id, [])

                    current = next(
                        (
                            record
                            for record in records
                            if record["email_key"] == email_key
                            and record["archived_at"] is None
                        ),
                        None,
                    )
                    if current is not None:
                        selected.append(current)
                        continue

                    archived = next(
                        (
                            record
                            for record in records
                            if record["email_key"] == email_key
                            and record["archived_at"] is not None
                        ),
                        None,
                    )

                    for record in records:
                        if (
                            record["email_key"] != email_key
                            and record["archived_at"] is None
                        ):
                            recipients.archive_recipient(conn, record["id"])

                    if archived is not None:
                        selected.append(
                            recipients.restore_recipient(conn, archived["id"])
                        )
                    else:
                        selected.append(
                            recipients.add_recipient(conn, cid, contact_id)
                        )
            return selected
        except ValueError:
            return _error(400, "Solicitud no válida")
        except sqlite3.Error:
            return _error(503, "Servicio no disponible")
        finally:
            if conn is not None:
                conn.close()

    app.include_router(router)
