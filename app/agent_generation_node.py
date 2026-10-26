from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass

from .answer_messages import generation_messages as answer_generation_messages
from .answer_messages import request_id as answer_request_id
from .generation_contract import generation_messages, parse_generation
from .llm_client import LLMError

_MISSING = object()
_NEEDS = {'needs_input', 'needsinput', 'needs-input', 'requires_input', 'requiresinput', 'waiting_input'}
_DRAFT = {'draft', 'draft_ready', 'validated_draft', 'validateddraft', 'valid', 'ok', 'completed', 'complete'}
_INVALID = {'invalid', 'invalid_input', 'invalid_generation', 'error', 'failed', 'failure'}


def _field(value, name, default=_MISSING):
    if isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    return default


def _status(value):
    for name in ('status', 'kind', 'type', 'outcome', 'result'):
        raw = _field(value, name, _MISSING)
        if isinstance(raw, str):
            return raw.strip().lower()
    return None


def _is_needs_input(value):
    status = _status(value)
    if status in _NEEDS:
        return True
    if status in _DRAFT:
        return False
    marker = _field(value, 'needs_input', _MISSING)
    if marker is True:
        return True
    name = value.__class__.__name__.lower().replace('_', '')
    if 'needsinput' in name:
        return True
    if isinstance(value, Mapping):
        if 'questions' in value and 'pieces' not in value and 'draft' not in value:
            return True
    elif hasattr(value, 'questions') and not hasattr(value, 'pieces') and not hasattr(value, 'draft'):
        return True
    return False


def _is_invalid(value):
    status = _status(value)
    if status in _INVALID:
        return True
    name = value.__class__.__name__.lower().replace('_', '')
    return name in {'invaliddraft', 'invalidgeneration', 'parseerror'}


def _extract_pieces(value, draft):
    pieces = _field(value, 'pieces', _MISSING)
    if pieces is not _MISSING:
        return pieces
    pieces = _field(draft, 'pieces', _MISSING)
    if pieces is not _MISSING:
        return pieces
    return []


def _extract_questions(value):
    questions = _field(value, 'questions', _MISSING)
    if questions is _MISSING:
        return []
    return questions


def _plain(value):
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return value


def _hash(value):
    payload = json.dumps(_plain(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _event_list(state):
    events = state.get('events')
    if not isinstance(events, list):
        return None
    return list(events)


def _history_list(value):
    if value is None:
        return []
    if not isinstance(value, list):
        return None
    return list(value)


def _failure(state, code, retryable, outcome_unknown):
    update = {
        'status': 'failed',
        'draft': None,
        'draft_hash': None,
        'questions': [],
        'error': {'code': code, 'retryable': bool(retryable), 'outcome_unknown': bool(outcome_unknown)},
    }
    cycle = state.get('cycle')
    if isinstance(cycle, int) and not isinstance(cycle, bool):
        update['cycle'] = cycle
    history = _history_list(state.get('draft_history'))
    if history is not None:
        update['draft_history'] = history
    events = _event_list(state)
    if events is not None:
        update['events'] = events
    return update


def _valid_run_id(run_id):
    if not isinstance(run_id, str):
        return False
    try:
        parsed = uuid.UUID(run_id)
    except (ValueError, AttributeError, TypeError):
        return False
    return parsed.version == 4 and parsed.variant == uuid.RFC_4122 and str(parsed) == run_id


def _is_llm_error(exc):
    if isinstance(exc, LLMError):
        return True
    return hasattr(exc, 'code') and hasattr(exc, 'retryable') and hasattr(exc, 'outcome_unknown')


def _validated(state):
    if not isinstance(state, Mapping):
        return None
    run_id = state.get('run_id')
    if not _valid_run_id(run_id):
        return None
    cycle = state.get('cycle')
    if type(cycle) is not int or cycle < 0 or cycle > 2:
        return None
    brief = state.get('brief')
    if not isinstance(brief, Mapping):
        return None
    formats = brief.get('formats')
    if not isinstance(formats, list):
        return None
    sources = state.get('sources')
    if not isinstance(sources, list):
        return None
    chunk_ids = []
    for source in sources:
        if not isinstance(source, Mapping):
            return None
        chunk_id = source.get('chunk_id')
        if not isinstance(chunk_id, str) or not chunk_id:
            return None
        chunk_ids.append(chunk_id)
    history = state.get('history')
    if not isinstance(history, dict):
        return None
    events = state.get('events')
    if not isinstance(events, list):
        return None
    prior_history = _history_list(state.get('draft_history'))
    if prior_history is None:
        return None
    review = state.get('review', None)
    if review is not None and not isinstance(review, dict):
        return None
    return {
        'run_id': run_id,
        'brief': brief,
        'sources': sources,
        'history': history,
        'cycle': cycle,
        'events': events,
        'draft_history': prior_history,
        'review': review,
        'chunk_ids': chunk_ids,
        'formats': formats,
    }


def _answer_context(state):
    answer_round = state.get('answer_round', 0)
    if type(answer_round) is not int or answer_round < 0 or answer_round > 8:
        return None
    human_answer = state.get('human_answer')
    if human_answer is None:
        return answer_round, None
    if not isinstance(human_answer, str) or not human_answer.strip() or len(human_answer) > 2000:
        return None
    questions = state.get('questions', [])
    if not isinstance(questions, list) or len(questions) > 5:
        return None
    for question in questions:
        if not isinstance(question, str) or len(question) > 500:
            return None
    return answer_round, human_answer


def _llm_failure(state, exc):
    code = getattr(exc, 'code', 'llm_error')
    retryable = bool(getattr(exc, 'retryable', False))
    outcome_unknown = bool(getattr(exc, 'outcome_unknown', False))
    return _failure(state, code, retryable, outcome_unknown)


def make_generation_node(call):
    if not callable(call):
        raise TypeError('call must be callable')

    def generation_node(state):
        valid = _validated(state)
        if valid is None:
            safe_state = state if isinstance(state, Mapping) else {}
            return _failure(safe_state, 'invalid_input', False, False)
        run_id = valid['run_id']
        cycle = valid['cycle']
        answer_context = _answer_context(state)
        if answer_context is None:
            return _failure(state, 'invalid_input', False, False)
        answer_round, human_answer = answer_context
        try:
            request_id = answer_request_id(run_id, 'generator', cycle, answer_round)
        except Exception:
            return _failure(state, 'invalid_input', False, False)
        feedback = valid['review'] if cycle > 0 else None
        try:
            if human_answer is None:
                messages = generation_messages(valid['brief'], valid['sources'], valid['history'], feedback=feedback)
            else:
                messages = answer_generation_messages(
                    valid['brief'],
                    valid['sources'],
                    valid['history'],
                    feedback=feedback,
                    human_answer=human_answer,
                    questions=state.get('questions', []),
                )
        except Exception as exc:
            if _is_llm_error(exc):
                return _llm_failure(state, exc)
            if human_answer is not None:
                return _failure(state, 'invalid_input', False, False)
            return _failure(state, 'generation_failed', False, True)
        try:
            response = call(messages, stage='generator', request_id=request_id)
            text = response.text
        except Exception as exc:
            if _is_llm_error(exc):
                return _llm_failure(state, exc)
            return _failure(state, 'generation_failed', False, True)
        try:
            parsed = parse_generation(text, formats=valid['formats'], chunk_ids=valid['chunk_ids'])
        except Exception:
            return _failure(state, 'invalid_generation', False, False)
        if parsed is None or _is_invalid(parsed):
            return _failure(state, 'invalid_generation', False, False)
        if _is_needs_input(parsed):
            questions = _extract_questions(parsed)
            event = {'stage': 'generator', 'status': 'requires_input', 'request_id': request_id}
            return {
                'status': 'waiting_input',
                'draft': None,
                'draft_hash': None,
                'draft_history': valid['draft_history'],
                'questions': questions,
                'error': None,
                'events': valid['events'] + [event],
                'cycle': cycle,
            }
        draft = parsed
        if draft is None:
            return _failure(state, 'invalid_generation', False, False)
        try:
            digest = _hash(draft)
        except (TypeError, ValueError):
            return _failure(state, 'invalid_generation', False, False)
        pieces = _extract_pieces(parsed, draft)
        entry = {'cycle': cycle, 'hash': digest, 'pieces': pieces}
        next_history = valid['draft_history'] + [entry]
        if len(next_history) > 3:
            next_history = next_history[-3:]
        event = {'stage': 'generator', 'status': 'completed', 'request_id': request_id, 'draft_hash': digest}
        return {
            'status': 'draft_ready',
            'draft': draft,
            'draft_hash': digest,
            'draft_history': next_history,
            'questions': [],
            'error': None,
            'events': valid['events'] + [event],
            'cycle': cycle,
        }

    return generation_node
