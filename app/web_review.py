from __future__ import annotations

import inspect
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from . import approval, campaigns, demo_generation, runs, storage, versions
from .web_auth import _read_json_object

_BAD = 'Solicitud no válida'
_UNAVAILABLE = 'Servicio no disponible'
_NOT_FOUND = 'No encontrado'


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={'detail': detail})


def _bad() -> JSONResponse:
    return _error(400, _BAD)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    keys = getattr(value, 'keys', None)
    if callable(keys):
        return {key: _jsonable(value[key]) for key in keys()}
    return value


def _value(record: Any, key: str, default: Any = None) -> Any:
    if record is None:
        return default
    if isinstance(record, dict):
        return record.get(key, default)
    try:
        return record[key]
    except (KeyError, IndexError, TypeError):
        return getattr(record, key, default)


async def _read_body(request: Request) -> tuple[dict[str, Any] | None, Any]:
    result = _read_json_object(request)
    if inspect.isawaitable(result):
        result = await result
    return result


@contextmanager
def _write_transaction(conn: Any) -> Iterator[None]:
    if conn.in_transaction:
        name = '_web_review_savepoint'
        conn.execute(f'SAVEPOINT {name}')
        try:
            yield
        except BaseException:
            conn.execute(f'ROLLBACK TO SAVEPOINT {name}')
            conn.execute(f'RELEASE SAVEPOINT {name}')
            raise
        else:
            conn.execute(f'RELEASE SAVEPOINT {name}')
    else:
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            conn.rollback()
            raise
        else:
            conn.commit()


def _version_rank(version: dict[str, Any]) -> tuple[int, str, str]:
    revision = version.get('revision_no')
    try:
        revision_no = int(revision)
    except (TypeError, ValueError):
        revision_no = -1
    return (
        revision_no,
        str(version.get('created_at') or ''),
        str(version.get('id') or ''),
    )


def _current_versions(bundle: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not bundle:
        return []
    items = bundle.get('versions')
    if not isinstance(items, list):
        return []
    chosen: dict[tuple[Any, Any], dict[str, Any]] = {}
    for item in items:
        version = _jsonable(item)
        if not isinstance(version, dict):
            continue
        key = (version.get('format'), version.get('variant'))
        previous = chosen.get(key)
        if previous is None or _version_rank(version) > _version_rank(previous):
            chosen[key] = version
    return list(chosen.values())


def _current_version_ids(bundle: dict[str, Any] | None) -> list[Any]:
    return [version.get('id') for version in _current_versions(bundle)]


def _current_id_for_piece(current: list[dict[str, Any]], version: dict[str, Any]) -> Any:
    key = (version.get('format'), version.get('variant'))
    for candidate in current:
        if (candidate.get('format'), candidate.get('variant')) == key:
            return candidate.get('id')
    return None


def _find_approval(
    conn: Any,
    campaign_id: str,
    run_id: str,
    bundle: dict[str, Any],
    current_ids: list[Any],
) -> dict[str, Any] | None:
    rows = conn.execute(
        'SELECT id FROM approval WHERE campaign_id = ? ORDER BY approved_at DESC, id',
        (campaign_id,),
    ).fetchall()
    run = bundle.get('run') or {}
    for row in rows:
        approval_id = _value(row, 'id')
        if approval_id is None:
            continue
        record = _jsonable(approval.get_approval(conn, approval_id))
        if not isinstance(record, dict):
            continue
        if record.get('run_id') != run_id:
            continue
        if record.get('config_revision') != run.get('config_revision'):
            continue
        if record.get('source_hash') != bundle.get('source_hash'):
            continue
        if record.get('context_hash') != bundle.get('context_hash'):
            continue
        if not approval.approval_covers(conn, approval_id, current_ids):
            continue
        return record
    return None


def _exports_for(conn: Any, approval_id: Any) -> list[Any]:
    rows = conn.execute(
        'SELECT * FROM export_record WHERE approval_id = ? ORDER BY occurred_at DESC, id',
        (approval_id,),
    ).fetchall()
    return [_jsonable(row) for row in rows]


def _service_error(exc: Exception) -> JSONResponse | None:
    if isinstance(exc, sqlite3.Error):
        return _error(503, _UNAVAILABLE)
    if isinstance(exc, ValueError) or exc.__class__.__name__ == 'ServiceValueError':
        return _bad()
    return None


def _db_path(request: Request) -> Path:
    return Path(request.app.state.web_review_db_path)


router = APIRouter()


@router.get('/api/campaigns/{campaign_id}/review')
def get_campaign_review(
    campaign_id: str,
    request: Request,
    run_id: str | None = None,
) -> Any:
    conn = None
    try:
        conn = storage.connect(_db_path(request))
        campaign_raw = campaigns.get_campaign(conn, campaign_id)
        if campaign_raw is None:
            return _error(404, _NOT_FOUND)
        campaign = _jsonable(campaign_raw)
        if not isinstance(campaign, dict):
            return _error(404, _NOT_FOUND)

        run_rows = runs.list_runs(conn, campaign_id) or []
        selected_run_id: str | None = None
        if run_id is not None:
            for row in run_rows:
                if _value(row, 'id') == run_id:
                    selected_run_id = run_id
                    break
            if selected_run_id is None:
                return _bad()
        elif run_rows:
            selected_run_id = _value(run_rows[0], 'id')

        if selected_run_id is None:
            return {
                'campaign': campaign,
                'bundle': None,
                'approval': None,
                'exports': [],
            }

        bundle_raw = demo_generation.get_demo_bundle(conn, selected_run_id)
        bundle = _jsonable(bundle_raw)
        if not isinstance(bundle, dict):
            return _error(404, _NOT_FOUND)
        current_ids = _current_version_ids(bundle)
        approval_record = _find_approval(
            conn, campaign_id, selected_run_id, bundle, current_ids
        )
        exports = []
        if approval_record is not None:
            exports = _exports_for(conn, approval_record.get('id'))
        return {
            'campaign': campaign,
            'bundle': bundle,
            'approval': approval_record,
            'exports': exports,
        }
    except Exception as exc:
        response = _service_error(exc)
        if response is not None:
            return response
        raise
    finally:
        if conn is not None:
            conn.close()


@router.put('/api/versions/{version_id}')
async def put_version(version_id: str, request: Request) -> Any:
    conn = None
    try:
        body, error = await _read_body(request)
        if error is not None:
            return error
        if not isinstance(body, dict):
            return _bad()
        if any(key not in {'body', 'expected_hash'} for key in body):
            return _bad()
        if 'body' not in body or 'expected_hash' not in body:
            return _bad()
        new_body = body['body']
        expected_hash = body['expected_hash']
        if not isinstance(new_body, str) or not isinstance(expected_hash, str):
            return _bad()

        conn = storage.connect(_db_path(request))
        with _write_transaction(conn):
            version_raw = versions.get_version(conn, version_id)
            if version_raw is None:
                return _error(404, _NOT_FOUND)
            version = _jsonable(version_raw)
            if not isinstance(version, dict):
                return _error(404, _NOT_FOUND)
            if version.get('content_hash') != expected_hash:
                return _bad()
            run_id = version.get('run_id')
            if run_id is None:
                return _bad()
            bundle_raw = demo_generation.get_demo_bundle(conn, run_id)
            bundle = _jsonable(bundle_raw)
            if not isinstance(bundle, dict):
                return _bad()
            current = _current_versions(bundle)
            if _current_id_for_piece(current, version) != version_id:
                return _bad()
            new_version = versions.edit_version(conn, version_id, new_body)
            if new_version is None:
                return _bad()
            return _jsonable(new_version)
    except Exception as exc:
        response = _service_error(exc)
        if response is not None:
            return response
        raise
    finally:
        if conn is not None:
            conn.close()


@router.post('/api/campaigns/{campaign_id}/approvals')
async def post_campaign_approval(campaign_id: str, request: Request) -> Any:
    conn = None
    try:
        body, error = await _read_body(request)
        if error is not None:
            return error
        if not isinstance(body, dict):
            return _bad()
        if any(key not in {'run_id', 'version_ids', 'confirmed'} for key in body):
            return _bad()
        if 'run_id' not in body or 'version_ids' not in body or 'confirmed' not in body:
            return _bad()
        run_id = body['run_id']
        version_ids = body['version_ids']
        confirmed = body['confirmed']
        if not isinstance(run_id, str) or not isinstance(version_ids, list):
            return _bad()
        if confirmed is not True:
            return _bad()
        if any(not isinstance(value, str) for value in version_ids):
            return _bad()
        if len(version_ids) != len(set(version_ids)):
            return _bad()

        conn = storage.connect(_db_path(request))
        with _write_transaction(conn):
            campaign_raw = campaigns.get_campaign(conn, campaign_id)
            if campaign_raw is None:
                return _error(404, _NOT_FOUND)
            campaign = _jsonable(campaign_raw)
            if not isinstance(campaign, dict):
                return _error(404, _NOT_FOUND)

            bundle_raw = demo_generation.get_demo_bundle(conn, run_id)
            bundle = _jsonable(bundle_raw)
            if not isinstance(bundle, dict):
                return _error(404, _NOT_FOUND)
            run = bundle.get('run')
            if not isinstance(run, dict):
                return _bad()
            if run.get('id') != run_id or run.get('campaign_id') != campaign_id:
                return _bad()
            if run.get('status') not in {'needs_review', 'finished'}:
                return _bad()
            if run.get('config_revision') != campaign.get('config_revision'):
                return _bad()

            current_ids = _current_version_ids(bundle)
            if (
                len(version_ids) != len(current_ids)
                or set(version_ids) != set(current_ids)
            ):
                return _bad()

            result = approval.approve_bundle(
                conn,
                campaign_id,
                current_ids,
                bundle.get('source_hash'),
                bundle.get('context_hash'),
                actor='operator',
                run_id=run_id,
                expected_config_revision=run.get('config_revision'),
            )
            if not isinstance(result, dict) or 'id' not in result:
                return _bad()
            full = approval.get_approval(conn, result['id'])
            if full is None:
                return _error(404, _NOT_FOUND)
            return _jsonable(full)
    except Exception as exc:
        response = _service_error(exc)
        if response is not None:
            return response
        raise
    finally:
        if conn is not None:
            conn.close()


def mount_review(app: FastAPI, db_path: Path) -> None:
    app.state.web_review_db_path = Path(db_path)
    protected = APIRouter(dependencies=[Depends(app.state.require_operator)])
    protected.include_router(router)
    app.include_router(protected)
