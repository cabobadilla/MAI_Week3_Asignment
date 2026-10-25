'''HTTP authentication boundary for the local operator console.'''

from __future__ import annotations

import hmac
import json
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

__all__ = ['create_auth_app']

_COOKIE_NAME = 'gwa_session'
_COOKIE_MAX_AGE = 28800
_MAX_BODY_BYTES = 64 * 1024
_UNSAFE_METHODS = frozenset({'POST', 'PUT', 'PATCH', 'DELETE'})
_CSRF_EXEMPT_PATHS = frozenset({'/api/auth/setup', '/api/auth/login'})


def _secure(response: Response) -> Response:
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def _error(status_code: int, detail: str) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={'detail': detail},
    )
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


async def _read_json_object(
    request: Request,
) -> tuple[dict[str, object] | None, Response | None]:
    content_length = request.headers.get('content-length')
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except (TypeError, ValueError):
            return None, _error(400, 'Invalid request')
        if declared_length < 0:
            return None, _error(400, 'Invalid request')
        if declared_length > _MAX_BODY_BYTES:
            return None, _error(413, 'Request body too large')

    raw_body = bytearray()
    async for chunk in request.stream():
        if not chunk:
            continue
        if len(raw_body) + len(chunk) > _MAX_BODY_BYTES:
            return None, _error(413, 'Request body too large')
        raw_body.extend(chunk)

    try:
        text = bytes(raw_body).decode('utf-8')
        payload = json.loads(text)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None, _error(400, 'Invalid request')

    if not isinstance(payload, dict):
        return None, _error(400, 'Invalid request')
    return payload, None


def _session_token(request: Request) -> str | None:
    token = request.cookies.get(_COOKIE_NAME)
    if isinstance(token, str) and token:
        return token
    return None


def _authenticate_session(
    auth: Any,
    token: str | None,
) -> dict[str, object] | None:
    if token is None:
        return None
    session = auth.authenticate(token)
    if not isinstance(session, dict):
        return None
    csrf = session.get('csrf')
    if not isinstance(csrf, str) or not csrf:
        return None
    return session


def _csrf_matches(provided: str | None, expected: object) -> bool:
    if not isinstance(provided, str) or not isinstance(expected, str):
        return False
    return hmac.compare_digest(
        expected.encode('utf-8'),
        provided.encode('utf-8'),
    )


def create_auth_app(auth: Any, *, port: int = 8501) -> FastAPI:
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    allowed_hosts = frozenset(
        {
            f'127.0.0.1:{port}',
            f'localhost:{port}',
        }
    )
    allowed_origins = frozenset(
        {
            f'http://127.0.0.1:{port}',
            f'http://localhost:{port}',
        }
    )

    @app.middleware('http')
    async def enforce_loopback_boundary(
        request: Request,
        call_next: Any,
    ) -> Response:
        if request.headers.get('host') not in allowed_hosts:
            return _error(403, 'Forbidden')

        if request.method.upper() in _UNSAFE_METHODS:
            origin = request.headers.get('origin')
            expected_origin = (
                f'{request.url.scheme}://{request.url.netloc}'
            )
            if (
                not origin
                or origin not in allowed_origins
                or origin != expected_origin
            ):
                return _error(403, 'Forbidden')

            if request.url.path not in _CSRF_EXEMPT_PATHS:
                token = _session_token(request)
                session = _authenticate_session(auth, token)
                if session is None:
                    return _error(401, 'Unauthorized')
                provided_csrf = request.headers.get('x-csrf-token')
                if not _csrf_matches(provided_csrf, session.get('csrf')):
                    return _error(403, 'Forbidden')
                request.state.operator_session = session
                request.state.session_token = token

        response = await call_next(request)
        return _secure(response)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ) -> Response:
        return _error(500, 'Internal server error')

    @app.get('/api/health')
    async def health() -> Response:
        return _secure(
            JSONResponse(
                {
                    'status': 'ok',
                    'mode': 'demo',
                    'generation': 'simulated',
                }
            )
        )

    @app.get('/api/session')
    async def session_status(request: Request) -> Response:
        token = _session_token(request)
        session = _authenticate_session(auth, token)
        if session is not None:
            return _secure(
                JSONResponse(
                    {
                        'authenticated': True,
                        'csrf': session['csrf'],
                        'setup_required': False,
                    }
                )
            )
        return _secure(
            JSONResponse(
                {
                    'authenticated': False,
                    'setup_required': not bool(auth.has_password()),
                }
            )
        )

    @app.post('/api/auth/setup')
    async def setup(request: Request) -> Response:
        payload, error = await _read_json_object(request)
        if error is not None:
            return error
        if payload is None:
            return _error(400, 'Invalid request')

        password = payload.get('password')
        confirmation = payload.get('confirmation')
        if not isinstance(password, str) or not isinstance(confirmation, str):
            return _error(400, 'Invalid request')

        if auth.has_password():
            return _error(409, 'Setup already complete')

        try:
            auth.setup(password, confirmation)
        except ValueError:
            if auth.has_password():
                return _error(409, 'Setup already complete')
            return _error(400, 'Invalid request')

        return _secure(JSONResponse({'ok': True}))

    @app.post('/api/auth/login')
    async def login(request: Request) -> Response:
        payload, error = await _read_json_object(request)
        if error is not None:
            return error
        if payload is None:
            return _error(400, 'Invalid request')

        password = payload.get('password')
        if not isinstance(password, str):
            return _error(400, 'Invalid request')

        try:
            result = auth.login(password, client_id='local')
        except ValueError:
            return _error(401, 'Invalid credentials')

        if not isinstance(result, dict):
            return _error(500, 'Internal server error')
        token = result.get('token')
        csrf = result.get('csrf')
        if (
            not isinstance(token, str)
            or not token
            or not isinstance(csrf, str)
            or not csrf
        ):
            return _error(500, 'Internal server error')

        response = JSONResponse({'ok': True, 'csrf': csrf})
        response.set_cookie(
            key=_COOKIE_NAME,
            value=token,
            max_age=_COOKIE_MAX_AGE,
            path='/',
            httponly=True,
            secure=False,
            samesite='strict',
        )
        return _secure(response)

    @app.post('/api/auth/logout')
    async def logout(request: Request) -> Response:
        token = _session_token(request)
        if token is not None:
            auth.logout(token)

        response = JSONResponse({'ok': True})
        response.delete_cookie(
            key=_COOKIE_NAME,
            path='/',
            secure=False,
            httponly=True,
            samesite='strict',
        )
        return _secure(response)

    async def require_operator(request: Request) -> dict[str, object]:
        token = _session_token(request)
        session = _authenticate_session(auth, token)
        if session is None:
            raise HTTPException(status_code=401, detail='Unauthorized')
        return session

    app.state.require_operator = require_operator
    return app
