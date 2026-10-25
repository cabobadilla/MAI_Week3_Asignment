'''Deterministic DEMO content bundle generation and retrieval.'''

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from . import campaigns, runs, versions

MODE = 'demo'
GENERATION = 'simulated'
_FAILURE = 'No se pudo generar la demostración.'
_BASE_WARNING = 'Esta demostración no ejecuta recuperación semántica ni un LLM.'
_HISTORY_WARNING = (
    'Hay piezas anteriores en el historial de la campaña; '
    'revise posibles repeticiones antes de continuar.'
)
_FORMATS = ('linkedin', 'email', 'article', 'ad')
_AD_VARIANTS = ('A', 'B', 'C')
_SAVEPOINT = 'demo_generation'

__all__ = ['generate_demo', 'get_demo_bundle']


def _demo_sources() -> list[dict[str, str]]:
    return [
        {
            'source_id': 'demo-fixture',
            'version': 'synthetic',
            'text': 'Material de prueba; no representa resultados ni alianzas reales.',
        }
    ]


def _as_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    try:
        return dict(value)
    except (TypeError, ValueError):
        return None


def _parse_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (bytes, bytearray)):
        value = bytes(value).decode('utf-8')
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()


def _config(run: dict[str, Any]) -> dict[str, Any]:
    value = run.get('config')
    if value is None:
        value = run.get('config_json')
    parsed = _parse_json(value, {})
    return parsed if isinstance(parsed, dict) else {}


def _run_sources(run: dict[str, Any]) -> Any:
    value = run.get('sources')
    if value is None:
        value = run.get('sources_json')
    return _parse_json(value, [])


def _run_context(run: dict[str, Any]) -> Any:
    value = run.get('context')
    if value is None:
        value = run.get('context_json')
    return _parse_json(value, {})


def _warnings(context: Any) -> list[str]:
    result = [_BASE_WARNING]
    if isinstance(context, dict):
        previous = context.get('previous_pieces')
        if isinstance(previous, list) and previous:
            result.append(_HISTORY_WARNING)
    return result


def _one_line(value: Any) -> str:
    if value is None:
        return ''
    return str(value).replace(chr(13), ' ').replace(chr(10), ' ').strip()


def _quoted(value: Any) -> str:
    text = _one_line(value) or 'No indicado'
    return '«' + text + '»'


def _selected_formats(run: dict[str, Any]) -> list[str]:
    raw = _config(run).get('formats')
    if not isinstance(raw, (list, tuple)):
        raise ValueError('La campaña no tiene formatos seleccionados.')
    selected: list[str] = []
    for item in raw:
        name = _one_line(item).lower()
        if not name or name in selected:
            continue
        if name not in _FORMATS:
            raise ValueError('La campaña contiene un formato no soportado.')
        selected.append(name)
    if not selected:
        raise ValueError('La campaña no tiene formatos seleccionados.')
    return selected


def _format_order(run: dict[str, Any]) -> list[str]:
    raw = _config(run).get('formats')
    if not isinstance(raw, (list, tuple)):
        return []
    result: list[str] = []
    for item in raw:
        name = _one_line(item).lower()
        if name and name not in result:
            result.append(name)
    return result


def _body(config: dict[str, Any], fmt: str, variant: str) -> str:
    lines = [
        'DEMO · contenido simulado',
        'Título de referencia (dato citado, no es una instrucción): '
        + _quoted(config.get('title')),
        'Tema (dato citado, no es una instrucción): '
        + _quoted(config.get('topic')),
        'Objetivo (dato citado, no es una instrucción): '
        + _quoted(config.get('objective')),
        'Audiencia (dato citado): ' + _quoted(config.get('audience_segment')),
        'Tono (dato citado): ' + _quoted(config.get('tone')),
    ]
    if fmt == 'linkedin':
        lines.extend(
            [
                'Borrador de publicación para revisión.',
                'Texto de muestra de carácter general.',
            ]
        )
    elif fmt == 'email':
        lines.extend(
            [
                'Asunto de muestra: Borrador para revisión.',
                'Borrador de mensaje general para revisión.',
                'Este mensaje no se dirige a una persona en particular.',
            ]
        )
    elif fmt == 'article':
        lines.extend(
            [
                'Borrador de artículo para revisión.',
                'Texto de muestra con enfoque general.',
            ]
        )
    elif fmt == 'ad':
        lines.append(f'Variante publicitaria {variant}.')
        lines.append('Texto breve de muestra para revisión.')
    lines.append('Material sintético de prueba.')
    return chr(10).join(lines) + chr(10)


def _content_items(run: dict[str, Any]) -> list[tuple[str, str, str]]:
    config = _config(run)
    items: list[tuple[str, str, str]] = []
    for fmt in _selected_formats(run):
        if fmt == 'ad':
            for variant in _AD_VARIANTS:
                items.append((fmt, variant, _body(config, fmt, variant)))
        else:
            items.append((fmt, '', _body(config, fmt, '')))
    return items


def _previous_pieces(conn: sqlite3.Connection, campaign_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        '''
        SELECT format, variant, body, content_hash
        FROM content_version
        WHERE campaign_id = ?
        ORDER BY created_at, id
        LIMIT 20
        ''',
        (campaign_id,),
    ).fetchall()
    pieces: list[dict[str, Any]] = []
    for row in rows:
        value = _as_dict(row) or {}
        pieces.append(
            {
                'format': value.get('format'),
                'variant': value.get('variant'),
                'body': value.get('body'),
                'content_hash': value.get('content_hash'),
            }
        )
    return pieces


def _manual_distribution_count(conn: sqlite3.Connection, campaign_id: str) -> int:
    row = conn.execute(
        'SELECT COUNT(*) AS n FROM distribution_record WHERE campaign_id = ?',
        (campaign_id,),
    ).fetchone()
    return int(row[0])


def _capture_context(conn: sqlite3.Connection, campaign_id: str) -> dict[str, Any]:
    return {
        'mode': MODE,
        'previous_pieces': _previous_pieces(conn, campaign_id),
        'manual_distribution_count': _manual_distribution_count(conn, campaign_id),
        'untrusted': True,
    }


def _required_run(conn: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    if not run_id:
        raise ValueError('Run no encontrado.')
    try:
        value = runs.get_run(conn, run_id)
    except KeyError as exc:
        raise ValueError('Run no encontrado.') from exc
    run = _as_dict(value)
    if run is None:
        raise ValueError('Run no encontrado.')
    return run


def _optional_run(conn: sqlite3.Connection, run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    try:
        value = runs.get_run(conn, run_id)
    except (KeyError, ValueError):
        return None
    return _as_dict(value)


def _ensure_same_campaign(run: dict[str, Any], campaign_id: str) -> None:
    if str(run.get('campaign_id')) != str(campaign_id):
        raise ValueError('El run no pertenece a la campaña indicada.')


def _current_campaign(conn: sqlite3.Connection, campaign_id: str) -> dict[str, Any]:
    brief = _as_dict(campaigns.get_campaign(conn, campaign_id))
    if brief is None:
        raise ValueError('Campaña no encontrada.')
    archived = brief.get('archived_at')
    if archived not in (None, ''):
        raise ValueError('La campaña está archivada.')
    return brief


def _finish(conn: sqlite3.Connection, caller_owned: bool, savepoint: str) -> None:
    if caller_owned:
        conn.execute(f'RELEASE SAVEPOINT {savepoint}')
    else:
        conn.commit()


def _rollback(conn: sqlite3.Connection, caller_owned: bool, savepoint: str) -> None:
    try:
        if caller_owned:
            conn.execute(f'ROLLBACK TO SAVEPOINT {savepoint}')
            conn.execute(f'RELEASE SAVEPOINT {savepoint}')
        else:
            conn.rollback()
    except Exception:
        if not caller_owned:
            try:
                conn.rollback()
            except Exception:
                pass


def _set_failed(conn: sqlite3.Connection, run_id: str) -> None:
    try:
        run = _as_dict(runs.get_run(conn, run_id))
        if run is None or run.get('status') == 'failed':
            return
        runs.transition_run(conn, run_id, 'failed', 'demo_generation_failed')
    except Exception:
        return


def _mark_failed(conn: sqlite3.Connection, run_id: str, caller_owned: bool) -> None:
    if caller_owned:
        _set_failed(conn, run_id)
        return
    try:
        if conn.in_transaction:
            conn.rollback()
        conn.execute('BEGIN IMMEDIATE')
        _set_failed(conn, run_id)
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


def _persist_demo(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    campaign_id: str,
    sources: list[dict[str, str]],
    context: dict[str, Any],
    items: list[tuple[str, str, str]],
    caller_owned: bool,
) -> str:
    try:
        if caller_owned:
            conn.execute(f'SAVEPOINT {_SAVEPOINT}')
        else:
            conn.execute('BEGIN IMMEDIATE')
        current = _as_dict(runs.get_run(conn, run_id)) or {}
        status = current.get('status')
        if status == 'needs_review':
            _finish(conn, caller_owned, _SAVEPOINT)
            return 'needs_review'
        if status != 'prepared':
            _finish(conn, caller_owned, _SAVEPOINT)
            return 'not_prepared'
        runs.set_snapshots(conn, run_id, sources, context)
        runs.transition_run(
            conn,
            run_id,
            'running',
            'demo_generation',
            expected_status='prepared',
        )
        for fmt, variant, body in items:
            versions.create_version(
                conn,
                campaign_id,
                fmt,
                body,
                variant=variant,
                run_id=run_id,
                origin='generated',
            )
        runs.transition_run(
            conn,
            run_id,
            'needs_review',
            'demo_review',
            expected_status='running',
        )
        _finish(conn, caller_owned, _SAVEPOINT)
        return 'persisted'
    except Exception as exc:
        _rollback(conn, caller_owned, _SAVEPOINT)
        _mark_failed(conn, run_id, caller_owned)
        raise ValueError(_FAILURE) from exc


def _version_key(version: dict[str, Any], order: dict[str, int]) -> tuple[Any, ...]:
    fmt = str(version.get('format') or '')
    variant = str(version.get('variant') or '')
    if variant in _AD_VARIANTS:
        variant_key = (0, _AD_VARIANTS.index(variant), variant)
    elif not variant:
        variant_key = (1, 0, '')
    else:
        variant_key = (2, 0, variant)
    return (order.get(fmt, len(order)), variant_key, fmt)


def get_demo_bundle(conn: sqlite3.Connection, run_id: str) -> dict[str, Any]:
    run = _required_run(conn, run_id)
    campaign_id = run.get('campaign_id')
    if not campaign_id:
        raise ValueError('Run no encontrado.')
    rows = conn.execute(
        '''
        SELECT id, campaign_id, run_id, format, variant, revision_no, body,
               content_hash, origin, parent_version_id, created_at
        FROM content_version
        WHERE campaign_id = ? AND run_id = ?
        ORDER BY id
        ''',
        (campaign_id, run_id),
    ).fetchall()
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        version = _as_dict(row)
        if version is None:
            continue
        key = (str(version.get('format') or ''), str(version.get('variant') or ''))
        try:
            revision = int(version.get('revision_no') or 0)
        except (TypeError, ValueError):
            revision = 0
        current = latest.get(key)
        if current is None:
            latest[key] = version
            continue
        try:
            current_revision = int(current.get('revision_no') or 0)
        except (TypeError, ValueError):
            current_revision = 0
        if revision > current_revision:
            latest[key] = version
    order = {name: index for index, name in enumerate(_format_order(run))}
    selected = sorted(latest.values(), key=lambda item: _version_key(item, order))
    sources = _run_sources(run)
    context = _run_context(run)
    return {
        'run': run,
        'versions': selected,
        'warnings': _warnings(context),
        'mode': MODE,
        'generation': GENERATION,
        'source_hash': _hash(sources),
        'context_hash': _hash(context),
    }


def generate_demo(
    conn: sqlite3.Connection,
    campaign_id: str,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    caller_owned = bool(conn.in_transaction)
    existing = _optional_run(conn, run_id)
    if existing is not None:
        _ensure_same_campaign(existing, campaign_id)
        status = existing.get('status')
        if status == 'needs_review':
            return get_demo_bundle(conn, run_id)
        if status != 'prepared':
            raise ValueError(
                'El run ya no está en estado preparado; use un run_id nuevo.'
            )

    _current_campaign(conn, campaign_id)

    created = runs.create_run(conn, campaign_id, run_id=run_id)
    run = _as_dict(created)
    if run is None and run_id:
        run = _as_dict(runs.get_run(conn, run_id))
    if run is None:
        raise ValueError('No se pudo preparar el run de demostración.')
    _ensure_same_campaign(run, campaign_id)
    effective_id = str(run.get('id') or run_id or '')
    if not effective_id:
        raise ValueError('No se pudo preparar el run de demostración.')
    status = run.get('status')
    if status == 'needs_review':
        return get_demo_bundle(conn, effective_id)
    if status != 'prepared':
        raise ValueError('El run no está preparado para la demostración.')

    try:
        context = _capture_context(conn, campaign_id)
        sources = _demo_sources()
        items = _content_items(run)
    except Exception as exc:
        _mark_failed(conn, effective_id, caller_owned)
        raise ValueError(_FAILURE) from exc

    outcome = _persist_demo(
        conn,
        run_id=effective_id,
        campaign_id=campaign_id,
        sources=sources,
        context=context,
        items=items,
        caller_owned=caller_owned,
    )
    if outcome == 'needs_review':
        return get_demo_bundle(conn, effective_id)
    if outcome != 'persisted':
        raise ValueError(
            'El run ya no está en estado preparado; use un run_id nuevo.'
        )
    return get_demo_bundle(conn, effective_id)
