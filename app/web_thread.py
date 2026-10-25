from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from . import campaigns, organizations, storage, versions


_BAD_REQUEST = "Solicitud inválida"
_UNAVAILABLE = "Servicio no disponible"


def _global_record_supersede_map(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT id, supersedes_id
        FROM distribution_record
        WHERE supersedes_id IS NOT NULL
        ORDER BY occurred_at, recorded_at, id
        """
    ).fetchall()
    result: dict[str, str] = {}
    for row in rows:
        result[row["supersedes_id"]] = row["id"]
    return result


def _global_followup_supersede_map(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT id, supersedes_id
        FROM followup_event
        WHERE supersedes_id IS NOT NULL
        ORDER BY occurred_at, recorded_at, id
        """
    ).fetchall()
    result: dict[str, str] = {}
    for row in rows:
        result[row["supersedes_id"]] = row["id"]
    return result


def _get_records(
    conn: sqlite3.Connection,
    organization_id: str,
    campaign_id: str | None,
    supersede_map: dict[str, str],
) -> list[dict]:
    sql = """
        SELECT *
        FROM distribution_record
        WHERE kind = 'email_sent'
          AND json_extract(destination_snapshot_json, '$.company_id') = ?
    """
    params: list[str] = [organization_id]
    if campaign_id is not None:
        sql += " AND campaign_id = ?"
        params.append(campaign_id)
    sql += " ORDER BY occurred_at, recorded_at, id"

    rows = conn.execute(sql, params).fetchall()
    records: list[dict] = []
    for row in rows:
        record = dict(row)
        record["destination"] = json.loads(row["destination_snapshot_json"])
        record["version"] = versions.get_version(conn, row["content_version_id"])
        campaign = campaigns.get_campaign(conn, row["campaign_id"])
        record["campaign_title"] = campaign['title'] if campaign is not None else None
        record["superseded_by"] = supersede_map.get(row["id"])
        records.append(record)
    return records


def _get_notes(
    conn: sqlite3.Connection,
    organization_id: str,
    campaign_id: str | None,
    supersede_map: dict[str, str],
) -> list[dict]:
    sql = """
        SELECT f.*
        FROM followup_event AS f
        LEFT JOIN campaign_recipient AS cr
          ON cr.id = f.campaign_recipient_id
         AND cr.campaign_id = f.campaign_id
        LEFT JOIN distribution_record AS d
          ON d.id = f.distribution_id
         AND d.campaign_id = f.campaign_id
        WHERE (
            json_extract(cr.snapshot_json, '$.company_id') = ?
            OR json_extract(d.destination_snapshot_json, '$.company_id') = ?
        )
    """
    params: list[str] = [organization_id, organization_id]
    if campaign_id is not None:
        sql += " AND f.campaign_id = ?"
        params.append(campaign_id)
    sql += " ORDER BY f.occurred_at, f.recorded_at, f.id"

    rows = conn.execute(sql, params).fetchall()
    notes: list[dict] = []
    for row in rows:
        note = dict(row)
        note["superseded_by"] = supersede_map.get(row["id"])
        note["display_kind"] = "note" if row["kind"] == "next_step" else row["kind"]
        notes.append(note)
    return notes


def mount_thread(app, db_path: Path) -> None:
    router = APIRouter(dependencies=[Depends(app.state.require_operator)])

    @router.get("/api/organizations/{organization_id}/thread")
    def get_organization_thread(
        organization_id: str,
        campaign_id: str | None = None,
    ):
        conn = None
        try:
            conn = storage.connect(db_path)
            try:
                organization = organizations.get_organization(conn, organization_id)
                if organization is None:
                    raise ValueError("organization not found")

                record_supersedes = _global_record_supersede_map(conn)
                followup_supersedes = _global_followup_supersede_map(conn)

                return {
                    "organization": organization,
                    "records": _get_records(
                        conn,
                        organization_id,
                        campaign_id,
                        record_supersedes,
                    ),
                    "notes": _get_notes(
                        conn,
                        organization_id,
                        campaign_id,
                        followup_supersedes,
                    ),
                    "untrusted_history": True,
                }
            finally:
                conn.close()
        except ValueError:
            raise HTTPException(status_code=400, detail=_BAD_REQUEST)
        except (sqlite3.Error, OSError):
            raise HTTPException(status_code=503, detail=_UNAVAILABLE)

    app.include_router(router)
