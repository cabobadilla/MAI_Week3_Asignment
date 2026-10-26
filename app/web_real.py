"""Authenticated HTTP start/status API for real campaign runs."""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse

from . import real_execution, real_results, runs, storage, web_auth

_REQUIRED_KEYS = frozenset(("run_id", "query", "confirmed_data"))
_BAD_DETAIL = "Solicitud no válida"
_NOT_FOUND_DETAIL = "No encontrado"
_UNAVAILABLE_DETAIL = "Servicio no disponible"
_IN_PROGRESS_WARNING = (
    "Ejecución IA real en curso; consulta su estado antes de iniciar otra."
)


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def _as_metrics(run: dict | None) -> dict:
    raw = (run or {}).get("metrics")
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        if isinstance(parsed, dict):
            return dict(parsed)
    return {}


def _is_canonical_uuid4(value: Any) -> bool:
    if not isinstance(value, str) or value != value.lower():
        return False
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError):
        return False
    return (
        parsed.version == 4
        and parsed.variant == uuid.RFC_4122
        and str(parsed) == value
    )


def _safe_rollback(conn) -> None:
    if conn is not None:
        try:
            conn.rollback()
        except sqlite3.Error:
            pass


def _execute_safely(
    executor,
    project_root: Path,
    db_path: Path,
    work_dir: Path,
    run_id: str,
    query: str,
) -> None:
    try:
        executor(project_root, db_path, work_dir, run_id, query)
    except Exception:
        # The executor is responsible for recording any durable failure.
        return


def mount_real(
    app,
    db_path: Path,
    project_root: Path,
    work_dir: Path,
    *,
    executor=None,
) -> None:
    selected_executor = executor or real_execution.execute_run
    router = APIRouter(dependencies=[Depends(app.state.require_operator)])

    @router.post("/api/campaigns/{campaign_id}/real")
    async def start_real(
        campaign_id: str,
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> JSONResponse:
        payload, error_response = await web_auth._read_json_object(request)
        if error_response is not None:
            return error_response

        if not isinstance(payload, dict) or set(payload) != _REQUIRED_KEYS:
            return _error(400, _BAD_DETAIL)

        run_id = payload.get("run_id")
        query = payload.get("query")
        confirmed_data = payload.get("confirmed_data")
        if (
            not _is_canonical_uuid4(run_id)
            or not isinstance(query, str)
            or not query.strip()
            or len(query) > 300
            or confirmed_data is not True
        ):
            return _error(400, _BAD_DETAIL)

        conn = None
        should_schedule = False
        run_status = "prepared"
        try:
            conn = storage.connect(db_path)
            conn.execute("BEGIN IMMEDIATE")
            presence = conn.execute(
                "SELECT id FROM generation_run WHERE id = ?", (run_id,)
            ).fetchone()
            existing = runs.get_run(conn, run_id) if presence is not None else None
            if existing is not None:
                metrics = _as_metrics(existing)
                if (
                    existing.get("campaign_id") != campaign_id
                    or metrics.get("agent_mode") != "real"
                ):
                    _safe_rollback(conn)
                    return _error(400, _BAD_DETAIL)
                run_status = existing.get("status") or "prepared"
                should_schedule = run_status == "prepared"
                _safe_rollback(conn)
            else:
                created = runs.create_run(conn, campaign_id, run_id=run_id)
                metrics = _as_metrics(created)
                metrics["agent_mode"] = "real"
                conn.execute(
                    "UPDATE generation_run SET metrics_json = ? WHERE id = ?",
                    (json.dumps(metrics, ensure_ascii=False), run_id),
                )
                conn.commit()
                run_status = created.get("status") or "prepared"
                should_schedule = run_status == "prepared"
        except sqlite3.Error:
            _safe_rollback(conn)
            return _error(503, _UNAVAILABLE_DETAIL)
        except (KeyError, LookupError, ValueError):
            _safe_rollback(conn)
            return _error(400, _BAD_DETAIL)
        except Exception:
            _safe_rollback(conn)
            return _error(503, _UNAVAILABLE_DETAIL)
        finally:
            if conn is not None:
                conn.close()

        if should_schedule:
            background_tasks.add_task(
                _execute_safely,
                selected_executor,
                project_root,
                db_path,
                work_dir,
                run_id,
                query,
            )

        return JSONResponse(
            status_code=202,
            content={
                "run_id": run_id,
                "campaign_id": campaign_id,
                "status": run_status,
                "mode": "real",
            },
        )

    @router.get("/api/runs/{run_id}/real")
    async def get_real(run_id: str) -> JSONResponse:
        if not _is_canonical_uuid4(run_id):
            return _error(400, _BAD_DETAIL)

        conn = None
        try:
            conn = storage.connect(db_path)
            presence = conn.execute(
                "SELECT id FROM generation_run WHERE id = ?", (run_id,)
            ).fetchone()
            if presence is None:
                return _error(404, _NOT_FOUND_DETAIL)
            run = runs.get_run(conn, run_id)

            metrics = _as_metrics(run)
            if (
                metrics.get("agent_mode") != "real"
                and metrics.get("agent_result") is None
            ):
                return _error(404, _NOT_FOUND_DETAIL)

            bundle = real_results.get_bundle(conn, run_id)
            if not isinstance(bundle, dict):
                return _error(503, _UNAVAILABLE_DETAIL)

            result = dict(bundle)
            if metrics.get("agent_result") is None:
                result["mode"] = "real"
                result["generation"] = "llm"
                result["warnings"] = [_IN_PROGRESS_WARNING]
                bundled_run = result.get("run")
                if isinstance(bundled_run, dict):
                    bundled_run = dict(bundled_run)
                    bundled_run["metrics"] = metrics
                    result["run"] = bundled_run

            return JSONResponse(status_code=200, content=result)
        except sqlite3.Error:
            return _error(503, _UNAVAILABLE_DETAIL)
        except Exception:
            return _error(503, _UNAVAILABLE_DETAIL)
        finally:
            if conn is not None:
                conn.close()

    app.include_router(router)
