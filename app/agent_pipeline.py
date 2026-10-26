from __future__ import annotations

import uuid
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .agent_generation_node import make_generation_node
from .agent_graph import build_retrieval_graph
from .agent_review_node import make_review_node


class AgentState(TypedDict, total=False):
    campaign_id: str
    run_id: str
    query: str
    brief: Any
    history: Any
    sources: list[Any]
    query_count: int
    status: str
    events: list[dict[str, Any]]
    questions: list[Any]
    human_answer: Any
    answer_round: int
    answer_operation_id: str
    cycle: int
    draft: Any
    draft_hash: str
    draft_history: list[Any]
    review: Any
    review_hash: str
    review_history: list[Any]
    error: Any


def _is_canonical_uuid4(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except (TypeError, ValueError):
        return False
    return (
        str(parsed) == value
        and parsed.version == 4
        and parsed.variant == uuid.RFC_4122
    )


def _prepare(state: AgentState) -> dict[str, Any]:
    return {
        'cycle': state.get('cycle', 0),
        'draft_history': state.get('draft_history', []),
        'review_history': state.get('review_history', []),
        'events': state.get('events', []),
        'questions': state.get('questions', []),
        'query_count': state.get('query_count', 0),
        'answer_round': state.get('answer_round', 0),
    }


def _ask_for_information(state: AgentState) -> dict[str, Any]:
    resume = interrupt(
        {
            'kind': 'missing_information',
            'questions': state.get('questions', []),
            'approved': False,
        }
    )
    if not isinstance(resume, dict):
        raise ValueError('resume must be a dict with a non-empty answer')
    answer = resume.get('answer')
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 2000:
        raise ValueError('answer must be a non-empty string of at most 2000 characters')
    operation_id = resume.get('operation_id')
    if operation_id is not None and not _is_canonical_uuid4(operation_id):
        raise ValueError('operation_id must be a canonical UUID4')
    answer_round = state.get('answer_round', 0)
    if type(answer_round) is not int or answer_round < 0 or answer_round > 7:
        raise ValueError('answer_round must be an integer between 0 and 7')
    update = {
        'human_answer': answer,
        'answer_round': answer_round + 1,
        'status': 'context_ready',
        'questions': state.get('questions', []),
    }
    if operation_id is not None:
        update['answer_operation_id'] = operation_id
    return update


def _advance_cycle(state: AgentState) -> dict[str, Any]:
    return {'cycle': state.get('cycle', 0) + 1}


def _waiting_input(_state: AgentState) -> dict[str, Any]:
    return {'status': 'waiting_input'}


def _revision_limit_reached(_state: AgentState) -> dict[str, Any]:
    return {'status': 'failed', 'error': {'code': 'revision_limit', 'retryable': False, 'outcome_unknown': False}}


def _after_context(state: AgentState) -> str:
    if state.get('sources') and state.get('status') == 'context_ready':
        return 'generate'
    return 'end'


def _after_generation(state: AgentState) -> str:
    status = state.get('status')
    if status == 'draft_ready':
        return 'review'
    if status == 'waiting_input':
        return 'ask'
    return 'end'


def build_agent_graph(
    *,
    checkpointer: Any,
    retrieve: Callable[..., Any],
    call: Callable[..., Any],
    max_revisions: int = 2,
) -> Any:
    if type(max_revisions) is not int or max_revisions not in (0, 1, 2):
        raise ValueError('max_revisions must be exactly 0, 1, or 2')

    def _after_review(state: AgentState) -> str:
        status = state.get('status')
        if status == 'needs_human_review':
            return 'end'
        if status == 'waiting_input':
            return 'ask'
        if status == 'revision_required':
            if state.get('cycle', 0) < max_revisions:
                return 'advance'
            return 'limit'
        return 'end'

    builder = StateGraph(AgentState)
    builder.add_node('prepare', _prepare)
    builder.add_node(
        'context',
        build_retrieval_graph(checkpointer=True, retrieve=retrieve),
    )
    builder.add_node('generate', make_generation_node(call))
    builder.add_node('review', make_review_node(call))
    builder.add_node('ask', _ask_for_information)
    builder.add_node('advance_cycle', _advance_cycle)
    builder.add_node('revision_limit', _revision_limit_reached)
    builder.add_node('waiting_input', _waiting_input)

    builder.add_edge(START, 'prepare')
    builder.add_edge('prepare', 'context')
    builder.add_conditional_edges(
        'context',
        _after_context,
        {'generate': 'generate', 'end': END},
    )
    builder.add_conditional_edges(
        'generate',
        _after_generation,
        {'review': 'review', 'ask': 'ask', 'end': END},
    )
    builder.add_conditional_edges(
        'review',
        _after_review,
        {
            'advance': 'advance_cycle',
            'limit': 'revision_limit',
            'ask': 'ask',
            'end': END,
        },
    )
    builder.add_edge('advance_cycle', 'generate')
    builder.add_edge('revision_limit', END)
    builder.add_conditional_edges(
        'ask',
        _after_context,
        {'generate': 'generate', 'end': 'waiting_input'},
    )
    builder.add_edge('waiting_input', END)

    return builder.compile(checkpointer=checkpointer)
