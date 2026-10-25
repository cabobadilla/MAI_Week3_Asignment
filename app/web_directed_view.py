from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app import storage
from app import campaigns, distribution, recipients, versions


def mount_directed_view(app, db_path: Path) -> None:
    router = APIRouter(dependencies=[Depends(app.state.require_operator)])

    @router.get("/api/campaigns/{cid}/directed")
    def directed_campaign(cid: str) -> dict:
        conn = None
        try:
            conn = storage.connect(db_path)
            campaign = campaigns.get_campaign(conn, cid)
            if not campaign:
                raise ValueError("campaign not found")

            email_versions = [
                item
                for item in versions.list_versions(conn, cid, latest_only=False)
                if item.get("format") == "email"
            ]
            recipient_rows = recipients.list_recipients(
                conn, cid, include_archived=True
            )
            sent_records = [
                item
                for item in distribution.list_distributions(
                    conn, cid, include_superseded=True
                )
                if item.get("kind") == "email_sent"
            ]

            return {
                "campaign": campaign,
                "versions": email_versions,
                "recipients": recipient_rows,
                "records": sent_records,
            }
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Solicitud no válida"
            ) from exc
        except (sqlite3.Error, OSError) as exc:
            raise HTTPException(
                status_code=503, detail="Servicio no disponible"
            ) from exc
        finally:
            if conn is not None:
                conn.close()

    app.include_router(router)
