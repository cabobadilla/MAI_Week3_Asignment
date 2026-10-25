import hashlib
import inspect
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from . import export as export_service
from . import storage, web_auth


BAD_REQUEST_DETAIL = 'Solicitud no válida'
UNAVAILABLE_DETAIL = 'Servicio no disponible'


def _bad_request() -> Response:
    return JSONResponse(status_code=400, content={'detail': BAD_REQUEST_DETAIL})


def _unavailable() -> Response:
    return JSONResponse(status_code=503, content={'detail': UNAVAILABLE_DETAIL})


def _safe_filename(relative_path: str) -> str:
    candidate = Path(relative_path).name
    if not candidate or candidate in {'.', '..'}:
        return 'material.md'
    for character in candidate:
        if character.isascii() and character.isalnum():
            continue
        if character in {'_', '.', '-'}:
            continue
        return 'material.md'
    return candidate


async def _read_body(request: Request) -> tuple[dict | None, Response | None]:
    try:
        payload, error_response = await web_auth._read_json_object(request)
    except (sqlite3.Error, OSError):
        return None, _unavailable()

    if error_response is not None:
        return None, error_response
    if not isinstance(payload, dict):
        return None, _bad_request()
    if set(payload) != {'operation_id'}:
        return None, _bad_request()
    operation_id = payload['operation_id']
    if not isinstance(operation_id, str) or not operation_id:
        return None, _bad_request()
    return {'operation_id': operation_id}, None


def _record_with_links(record: dict) -> dict:
    record_id = record['id']
    raw_files = record['files']
    if not isinstance(raw_files, list):
        raise ValueError
    files = []
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            raise ValueError
        enriched = dict(item)
        enriched['download_url'] = f'/api/exports/{record_id}/files/{index}'
        files.append(enriched)
    response_record = dict(record)
    response_record['files'] = files
    return response_record


def mount_export(app, db_path: Path, output_root: Path) -> None:
    router = APIRouter(dependencies=[Depends(app.state.require_operator)])

    @router.post('/api/approvals/{approval_id}/exports')
    async def create_export(approval_id: str, request: Request):
        body, failure = await _read_body(request)
        if failure is not None:
            return failure
        if body is None:
            return _bad_request()
        conn = None
        try:
            conn = storage.connect(db_path)
            record = export_service.export_bundle(
                conn,
                approval_id,
                output_root,
                body['operation_id'],
            )
            return JSONResponse(
                status_code=200,
                content=_record_with_links(record),
            )
        except ValueError:
            return _bad_request()
        except (sqlite3.Error, OSError):
            return _unavailable()
        finally:
            if conn is not None:
                conn.close()

    @router.get('/api/exports/{export_id}/files/{index}')
    async def download_export_file(export_id: str, index: int):
        conn = None
        try:
            conn = storage.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM export_record WHERE id=?',
                (export_id,),
            ).fetchone()
            if row is None:
                return _bad_request()
            record = dict(row)
            campaign_id = record.get('campaign_id')
            manifest_json = record.get('files_manifest_json')
            if not isinstance(campaign_id, str) or not campaign_id:
                return _bad_request()
            if not isinstance(manifest_json, str) or not manifest_json:
                return _bad_request()
            files = export_service._parse_files(manifest_json)
            if index < 0 or index >= len(files):
                return _bad_request()
            export_service._verify_existing(output_root, campaign_id, files)
            selected = files[index]
            relative_path = selected['relative_path']
            expected_hash = selected['sha256']
            data = export_service._read(output_root / relative_path)
            if hashlib.sha256(data).hexdigest() != expected_hash.lower():
                raise ValueError
            filename = _safe_filename(relative_path)
            quote = chr(34)
            return Response(
                content=data,
                media_type='text/markdown',
                status_code=200,
                headers={
                    'Content-Disposition': 'attachment; filename=' + quote + filename + quote,
                },
            )
        except ValueError:
            return _bad_request()
        except (sqlite3.Error, OSError):
            return _unavailable()
        finally:
            if conn is not None:
                conn.close()

    app.include_router(router)
