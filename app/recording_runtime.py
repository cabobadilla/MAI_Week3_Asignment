from __future__ import annotations

import re
from pathlib import Path
from typing import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

_HISTORICAL_TITLE = "Ejecución real anterior · 26 de octubre de 2026"
_HISTORICAL_NOTE = (
    "Resultados guardados de Qwen; no es una generación nueva ni una simulación. "
    "Las ediciones se guardan solo en esta copia de grabación."
)
_BLOCKED_DETAIL = (
    "La grabación muestra una ejecución real anterior; no inicia nuevas generaciones."
)
_BLOCKED_POST_PATH = re.compile(r"^/api/campaigns/[^/]+/(?:real|demo)$")
_BODY_OPEN = re.compile(r"(<body\b[^>]*>)", re.IGNORECASE)
_BANNER = (
    '<div id="recording-historical-banner" role="status" aria-live="polite">'
    f"<strong>{_HISTORICAL_TITLE}</strong>"
    f'<span class="recording-historical-note">{_HISTORICAL_NOTE}</span>'
    "</div>"
    "<style>"
    "#real-start-controls{display:none!important;visibility:hidden!important;}"
    "#recording-historical-banner{display:block;position:relative;z-index:2147483647;"
    "margin:0;padding:12px 16px;background:#fff7d6;border-bottom:1px solid #9a6b00;"
    "color:#332400;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;"
    "font-size:15px;line-height:1.45;text-align:center;}"
    "#recording-historical-banner strong{font-weight:700;}"
    "#recording-historical-banner .recording-historical-note{"
    "display:block;margin-top:3px;font-size:13px;font-weight:400;}"
    "</style>"
)


def _resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _insert_historical_banner(html: str) -> str:
    injected, count = _BODY_OPEN.subn(
        lambda match: match.group(1) + _BANNER,
        html,
        count=1,
    )
    return injected if count else _BANNER + html


def _response_charset(content_type: str) -> str:
    match = re.search(r"charset\s*=\s*([^;\s]+)", content_type, re.IGNORECASE)
    if not match:
        return "utf-8"
    return match.group(1).strip().strip('"').strip("'") or "utf-8"


def _build_html_response(response: Response, body: bytes) -> Response:
    content_type = response.headers.get("content-type", "")
    charset = _response_charset(content_type)
    try:
        html = body.decode(charset)
    except (LookupError, UnicodeDecodeError):
        charset = "utf-8"
        html = body.decode(charset, errors="replace")

    new_html = _insert_historical_banner(html)
    try:
        new_body = new_html.encode(charset)
    except (LookupError, UnicodeEncodeError):
        charset = "utf-8"
        new_body = new_html.encode(charset)

    new_response = Response(
        content=new_body,
        status_code=response.status_code,
        background=getattr(response, "background", None),
    )
    headers = [
        (name, value)
        for name, value in response.raw_headers
        if name.lower() != b"content-length"
    ]
    headers.append((b"content-length", str(len(new_body)).encode("latin-1")))
    new_response.raw_headers = headers
    return new_response


def _install_recording_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def recording_guard(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method == "POST" and _BLOCKED_POST_PATH.fullmatch(request.url.path):
            return JSONResponse(
                status_code=409,
                content={"detail": _BLOCKED_DETAIL},
            )

        response = await call_next(request)

        if (
            request.method == "GET"
            and request.url.path == "/"
            and "text/html" in response.headers.get("content-type", "").lower()
        ):
            body = bytearray()
            body_iterator = getattr(response, "body_iterator", None)
            if body_iterator is None:
                body.extend(getattr(response, "body", b""))
            else:
                async for chunk in body_iterator:
                    if isinstance(chunk, str):
                        chunk = chunk.encode("utf-8")
                    body.extend(chunk)
            return _build_html_response(response, bytes(body))

        return response


def create_recording_app(
    project_root: Path,
    *,
    data_dir: Path,
    port: int = 8502,
) -> FastAPI:
    project_root = Path(project_root)
    data_dir = Path(data_dir)

    preserved_demo = (project_root / "data" / "demo").resolve()
    if _resolve(data_dir) == preserved_demo:
        raise ValueError(
            "data_dir debe ser una copia de grabación, no el directorio de datos de demostración."
        )

    if not (data_dir / "app.sqlite").is_file():
        raise ValueError(
            "data_dir no contiene app.sqlite; se requiere una copia existente de una ejecución real."
        )

    from .runtime import create_real_app

    app = create_real_app(project_root, data_dir=data_dir, port=port)
    _install_recording_middleware(app)
    return app
