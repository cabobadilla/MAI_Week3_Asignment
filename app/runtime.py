from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse

from . import (
    bootstrap,
    storage,
    ui_approval,
    ui_campaigns,
    ui_directed,
    ui_directed_record,
    ui_directed_note,
    ui_export_controls,
    ui_organizations,
    ui_publications,
    ui_shell,
    ui_work,
    web_auth,
    web_campaigns,
    web_demo,
    web_directed,
    web_directed_view,
    web_recipients,
    web_thread,
    web_interactions,
    web_export,
    web_organizations,
    web_publication_view,
    web_publications,
    web_review,
)
from .auth import AuthService


def _validate_port(port: int) -> None:
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError('port must be an integer between 1024 and 65535')


def _resolve_data_dir(root: Path, value: Path | None) -> Path:
    if value is None:
        return root / 'data' / 'demo'
    raw = Path(value).expanduser()
    if not raw.is_absolute():
        raw = root / raw
    return raw.parent.resolve() / raw.name


def create_demo_app(project_root: Path, *, data_dir: Path | None = None, port: int = 8501) -> FastAPI:
    _validate_port(port)
    root = Path(project_root).resolve()
    cfg = bootstrap.load_runtime_config(root, demo=True, env={})
    assert cfg.llm_enabled is False, 'real LLM support is unavailable in the demo runtime'

    selected_data_dir = _resolve_data_dir(root, data_dir)
    selected_data_dir.mkdir(parents=True, exist_ok=True)
    db_path = selected_data_dir / 'app.sqlite'
    storage.initialize(
        db_path,
        root / 'app' / 'migrations' / '001_initial.sql',
        organizations=True,
    )

    export_root = selected_data_dir / 'exports'
    export_root.mkdir(parents=True, exist_ok=True)

    auth = AuthService(db_path)
    app = web_auth.create_auth_app(auth, port=port)

    app.state.db_path = db_path
    app.state.data_dir = selected_data_dir
    app.state.export_root = export_root
    app.state.mode = 'demo'
    app.state.project_root = root

    @app.get('/', response_class=HTMLResponse)
    def root_page() -> HTMLResponse:
        html = ui_shell.render_shell([
            ui_organizations.organization_panel(),
            ui_campaigns.campaigns_panel(),
            ui_work.workspace_panel(),
            ui_approval.approval_controls(),
            ui_export_controls.export_controls(),
            ui_publications.publication_panel(),
            ui_directed.directed_panel(),
            ui_directed_record.directed_record_controls(),
            ui_directed_note.directed_note_controls(),
        ])
        return HTMLResponse(html)

    @app.get('/favicon.ico', include_in_schema=False)
    def favicon() -> Response:
        return Response(status_code=204)

    web_organizations.mount_organizations(app, db_path)
    web_campaigns.mount_campaigns(app, db_path)
    web_demo.mount_demo(app, db_path)
    web_review.mount_review(app, db_path)
    web_export.mount_export(app, db_path, export_root)
    web_publications.mount_publications(app, db_path)
    web_publication_view.mount_publication_view(app, db_path)
    web_directed.mount_directed(app, db_path)
    web_directed_view.mount_directed_view(app, db_path)
    web_recipients.mount_recipients(app, db_path)
    web_thread.mount_thread(app, db_path)
    web_interactions.mount_interactions(app, db_path)

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', required=True)
    parser.add_argument('--port', type=int, default=8501)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not args.demo:
        parser.error('--demo is required')
    app = create_demo_app(args.project_root, port=args.port)
    uvicorn.run(
        app,
        host='127.0.0.1',
        port=args.port,
        proxy_headers=False,
        access_log=False,
        log_level='warning',
    )


if __name__ == '__main__':
    main()
