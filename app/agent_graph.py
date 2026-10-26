from __future__ import annotations

import copy
import json
import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class State(TypedDict, total=False):
    campaign_id: str
    run_id: str
    query: str
    sources: list[dict]
    query_count: int
    status: str
    events: list[str]
    questions: list[str]
    human_answer: str


_SECOND_SUFFIX = ' contexto general adicional'
_QUESTIONS = [
    '¿Puedes aportar o indicar una fuente validada relevante para la consulta?',
    '¿Qué aclaración o contexto adicional ayudaría a localizar evidencia verificable?',
    '¿Debe limitarse la búsqueda a alguna fuente o ámbito concreto?',
]
_MISSING = object()


def _is_uuid4(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def _is_nonblank_str(value):
    return isinstance(value, str) and bool(value.strip())


def _validate_input(state: State, config):
    campaign_id = state.get('campaign_id')
    run_id = state.get('run_id')
    query = state.get('query')
    if not _is_uuid4(campaign_id):
        raise ValueError('campaign_id must be a canonical UUID4 string')
    if not _is_uuid4(run_id):
        raise ValueError('run_id must be a canonical UUID4 string')
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise ValueError('query must be nonblank and at most 500 characters')
    configurable = config.get('configurable') if isinstance(config, dict) else None
    if not isinstance(configurable, dict):
        raise ValueError('missing configurable')
    expected_thread_id = f'gwa:{campaign_id}:{run_id}'
    if configurable.get('thread_id') != expected_thread_id:
        raise ValueError('invalid thread_id')
    return {
        'campaign_id': campaign_id,
        'run_id': run_id,
        'query': query,
        'sources': [],
        'query_count': 0,
        'status': 'retrieving',
        'events': ['config_validated'],
        'questions': [],
    }


def _second_query(query):
    base = query if isinstance(query, str) and query.strip() else 'consulta'
    return base + _SECOND_SUFFIX


def _question_list(state):
    questions = state.get('questions')
    if isinstance(questions, list) and questions and all(_is_nonblank_str(q) for q in questions):
        return list(questions)
    return list(_QUESTIONS)


def _validate_sources(raw):
    try:
        if not isinstance(raw, list) or not raw or len(raw) > 4:
            return None
        copied = []
        for item in raw:
            if not isinstance(item, dict):
                return None
            chunk_id = item.get('chunk_id')
            source_id = item.get('source_id')
            text = item.get('text')
            content_version = item.get('content_version', _MISSING)
            trusted = item.get('trusted_instructions', _MISSING)
            if not _is_nonblank_str(chunk_id) or not _is_nonblank_str(source_id) or not _is_nonblank_str(text):
                return None
            if not isinstance(content_version, str) or content_version != '0.2':
                return None
            if trusted is not False:
                return None
            if len(text) > 2000:
                return None
            copied.append(copy.deepcopy(item))
        encoded = json.dumps(copied, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        if len(encoded.encode('utf-8')) > 16000:
            return None
        return copied
    except Exception:
        return None


def _attempt_node(state, retrieve):
    events = list(state.get('events') or [])
    count = state.get('query_count', 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        count = 0
    if count >= 2:
        return {
            'sources': [],
            'query_count': count,
            'status': 'waiting_input',
            'questions': _question_list(state),
            'events': events + ['missing_information_requested'],
        }
    attempt_number = count + 1
    base_query = state.get('query')
    attempt_query = base_query if attempt_number == 1 else _second_query(base_query)
    if not _is_nonblank_str(attempt_query):
        attempt_query = 'consulta'
    events.append('retrieval_attempt')
    sources = None
    try:
        raw = retrieve(attempt_query)
    except Exception:
        events.append('retrieval_error')
    else:
        if raw is None or (isinstance(raw, list) and not raw):
            events.append('retrieval_empty')
        elif not isinstance(raw, list):
            events.append('retrieval_malformed')
        else:
            sources = _validate_sources(raw)
            if sources is None:
                events.append('retrieval_invalid')
    if sources is None:
        events.append('retrieval_failed')
        if attempt_number < 2:
            events.append('retry_scheduled')
            return {
                'query': attempt_query,
                'sources': [],
                'query_count': attempt_number,
                'status': 'retrieving',
                'events': events,
            }
        events.append('missing_information_requested')
        return {
            'query': attempt_query,
            'sources': [],
            'query_count': attempt_number,
            'status': 'waiting_input',
            'questions': list(_QUESTIONS),
            'events': events,
        }
    events.append('context_ready')
    return {
        'query': attempt_query,
        'sources': sources,
        'query_count': attempt_number,
        'status': 'context_ready',
        'events': events,
    }


def _ask_node(state):
    questions = _question_list(state)
    resume_value = interrupt({
        'kind': 'missing_information',
        'questions': questions,
        'approved': False,
    })
    if not isinstance(resume_value, dict):
        raise ValueError('invalid human answer')
    human_answer = resume_value.get('answer')
    if not _is_nonblank_str(human_answer) or len(human_answer) > 2000:
        raise ValueError('invalid human answer')
    events = list(state.get('events') or [])
    return {
        'human_answer': human_answer,
        'status': 'waiting_input',
        'questions': questions,
        'events': events + ['human_answer_recorded'],
    }


def _route_after_attempt(state):
    if state.get('sources'):
        return 'end'
    count = state.get('query_count', 0)
    if isinstance(count, int) and not isinstance(count, bool) and count < 2:
        return 'retry'
    return 'ask'


def build_retrieval_graph(*, checkpointer, retrieve):
    def attempt_node(state):
        return _attempt_node(state, retrieve)

    graph = StateGraph(State)
    graph.add_node('validate', _validate_input)
    graph.add_node('attempt', attempt_node)
    graph.add_node('ask', _ask_node)
    graph.add_edge(START, 'validate')
    graph.add_edge('validate', 'attempt')
    graph.add_conditional_edges(
        'attempt',
        _route_after_attempt,
        {'retry': 'attempt', 'ask': 'ask', 'end': END},
    )
    graph.add_edge('ask', END)
    return graph.compile(checkpointer=checkpointer)
