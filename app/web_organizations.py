'''HTTP endpoints for the existing organization service.'''

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable, TypeVar

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request

from . import storage
from .organizations import get_organization, list_organizations, save_organization

_MAX_BODY_BYTES = 64 * 1024
_ALLOWED_FIELDS = frozenset({'name', 'contacts', 'roles', 'notes'})
_INVALID_DATA = 'Datos de organización no válidos'
_UNAVAILABLE = 'Servicio de organizaciones no disponible'
_BAD_REQUEST = 'Solicitud de organización no válida'
_TOO_LARGE = 'Solicitud demasiado grande'
_UNSET = object()
_T = TypeVar('_T')


def _bad_request() -> HTTPException:
    return HTTPException(status_code=400, detail=_BAD_REQUEST)


def _too_large() -> HTTPException:
    return HTTPException(status_code=413, detail=_TOO_LARGE)


async def _read_json_object(request: Request) -> dict[str, Any]:
    content_length = request.headers.get('content-length')
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except (TypeError, ValueError):
            raise _bad_request()
        if declared_length < 0:
            raise _bad_request()
        if declared_length > _MAX_BODY_BYTES:
            raise _too_large()

    body = bytearray()
    async for chunk in request.stream():
        if not chunk:
            continue
        if len(body) + len(chunk) > _MAX_BODY_BYTES:
            raise _too_large()
        body.extend(chunk)

    if not body:
        raise _bad_request()

    try:
        payload = json.loads(bytes(body))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise _bad_request()

    if not isinstance(payload, dict):
        raise _bad_request()
    return payload


def _parse_organization_payload(
    payload: dict[str, Any],
) -> tuple[str, list[dict[str, Any]], Any, Any]:
    if set(payload) - _ALLOWED_FIELDS:
        raise _bad_request()
    if 'name' not in payload or 'contacts' not in payload:
        raise _bad_request()

    name = payload['name']
    contacts = payload['contacts']
    if not isinstance(name, str) or not isinstance(contacts, list):
        raise _bad_request()
    if any(not isinstance(contact, dict) for contact in contacts):
        raise _bad_request()

    roles: Any = _UNSET
    if 'roles' in payload:
        roles = payload['roles']
        if not isinstance(roles, list):
            raise _bad_request()
        if any(not isinstance(role, str) for role in roles):
            raise _bad_request()

    notes: Any = _UNSET
    if 'notes' in payload:
        notes = payload['notes']
        if not isinstance(notes, str):
            raise _bad_request()

    return name, contacts, roles, notes


def _save_options(roles: Any, notes: Any) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if roles is not _UNSET:
        options['roles'] = roles
    if notes is not _UNSET:
        options['notes'] = notes
    return options


def _with_connection(
    db_path: Path,
    operation: Callable[[sqlite3.Connection], _T],
) -> _T:
    connection: sqlite3.Connection | None = None
    try:
        connection = storage.connect(db_path)
        return operation(connection)
    except ValueError:
        raise HTTPException(status_code=400, detail=_INVALID_DATA)
    except sqlite3.Error:
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    finally:
        if connection is not None:
            connection.close()


def mount_organizations(app: FastAPI, db_path: Path) -> None:
    db_path = Path(db_path)
    router = APIRouter(
        prefix='/api/organizations',
        dependencies=[Depends(app.state.require_operator)],
    )

    @router.get('')
    async def list_organizations_endpoint() -> list[dict[str, Any]]:
        return _with_connection(
            db_path,
            lambda connection: list_organizations(connection),
        )

    @router.get('/{id}')
    async def get_organization_endpoint(id: str) -> dict[str, Any]:
        return _with_connection(
            db_path,
            lambda connection: get_organization(connection, id),
        )

    @router.post('')
    async def create_organization_endpoint(request: Request) -> dict[str, Any]:
        payload = await _read_json_object(request)
        name, contacts, roles, notes = _parse_organization_payload(payload)
        options = _save_options(roles, notes)
        return _with_connection(
            db_path,
            lambda connection: save_organization(
                connection,
                name,
                contacts,
                **options,
            ),
        )

    @router.put('/{id}')
    async def update_organization_endpoint(
        id: str,
        request: Request,
    ) -> dict[str, Any]:
        payload = await _read_json_object(request)
        name, contacts, roles, notes = _parse_organization_payload(payload)
        options = _save_options(roles, notes)
        return _with_connection(
            db_path,
            lambda connection: save_organization(
                connection,
                name,
                contacts,
                organization_id=id,
                **options,
            ),
        )

    app.include_router(router)
