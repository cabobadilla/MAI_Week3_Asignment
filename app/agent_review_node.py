from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Callable

from .answer_messages import request_id as answer_request_id
from .answer_messages import review_messages as answer_review_messages
from .llm_client import LLMResult, LLMError
from .review_contract import review_messages, parse_review

__all__ = ['make_review_node']

_REVIEW_VERDICTS = {'pass', 'revise', 'needs_input'}


class _InvalidReviewInput(Exception):
    pass


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


def _prepare_state(state: Any) -> tuple[
    str,
    dict[str, Any],
    list[Any],
    dict[str, Any],
    dict[str, Any],
    int,
    list[Any],
    list[Any],
    list[str],
    list[str],
]:
    if not isinstance(state, dict):
        raise _InvalidReviewInput

    run_id = state.get('run_id')
    if not _is_canonical_uuid4(run_id):
        raise _InvalidReviewInput

    cycle = state.get('cycle')
    if isinstance(cycle, bool) or not isinstance(cycle, int) or cycle < 0 or cycle > 2:
        raise _InvalidReviewInput

    brief = state.get('brief')
    sources = state.get('sources')
    history = state.get('history')
    draft = state.get('draft')
    if (
        not isinstance(brief, dict)
        or not isinstance(sources, list)
        or not isinstance(history, dict)
        or not isinstance(draft, dict)
    ):
        raise _InvalidReviewInput

    if draft.get('status') != 'draft':
        raise _InvalidReviewInput
    draft_questions = draft.get('questions')
    pieces = draft.get('pieces')
    if not isinstance(draft_questions, list) or not isinstance(pieces, list):
        raise _InvalidReviewInput

    piece_keys: list[str] = []
    for piece in pieces:
        if not isinstance(piece, dict):
            raise _InvalidReviewInput
        piece_format = piece.get('format')
        variant = piece.get('variant')
        if (
            not isinstance(piece_format, str)
            or not piece_format
            or not isinstance(variant, str)
        ):
            raise _InvalidReviewInput
        piece_keys.append(f'{piece_format}:{variant}')

    chunk_ids: list[str] = []
    for source in sources:
        if not isinstance(source, dict):
            raise _InvalidReviewInput
        chunk_id = source.get('chunk_id')
        if not isinstance(chunk_id, str) or not chunk_id:
            raise _InvalidReviewInput
        chunk_ids.append(chunk_id)

    events = state.get('events', [])
    if not isinstance(events, list):
        raise _InvalidReviewInput

    if 'review_history' in state and state['review_history'] is not None:
        review_history = state['review_history']
        if not isinstance(review_history, list):
            raise _InvalidReviewInput
    else:
        review_history = []

    return (
        run_id,
        brief,
        sources,
        history,
        draft,
        cycle,
        events,
        review_history,
        piece_keys,
        chunk_ids,
    )


def _failed(code: Any, *, retryable: bool, outcome_unknown: bool) -> dict[str, Any]:
    return {
        'status': 'failed',
        'error': {
            'code': code,
            'retryable': bool(retryable),
            'outcome_unknown': bool(outcome_unknown),
        },
        'approved': False,
        'sent': False,
        'published': False,
    }


def _answer_context(state: dict[str, Any]) -> Any:
    answer_round = state.get('answer_round', 0)
    if type(answer_round) is not int or answer_round < 0 or answer_round > 8:
        return None
    human_answer = state.get('human_answer')
    if human_answer is not None:
        if not isinstance(human_answer, str) or not human_answer.strip() or len(human_answer) > 2000:
            return None
    return answer_round, human_answer


def _review_hash(review: dict[str, Any]) -> str:
    canonical = json.dumps(review, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def make_review_node(
    call: Callable[..., LLMResult],
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def review_node(state: dict[str, Any]) -> dict[str, Any]:
        try:
            (
                run_id,
                brief,
                sources,
                history,
                draft,
                cycle,
                events,
                review_history,
                piece_keys,
                chunk_ids,
            ) = _prepare_state(state)
        except _InvalidReviewInput:
            return _failed(
                'invalid_review_input',
                retryable=False,
                outcome_unknown=False,
            )
        except Exception:
            return _failed(
                'review_failed',
                retryable=False,
                outcome_unknown=True,
            )

        answer_context = _answer_context(state)
        if answer_context is None:
            return _failed(
                'invalid_review_input',
                retryable=False,
                outcome_unknown=False,
            )
        answer_round, human_answer = answer_context

        try:
            request_id = answer_request_id(run_id, 'reviewer', cycle, answer_round)
        except Exception:
            return _failed(
                'invalid_review_input',
                retryable=False,
                outcome_unknown=False,
            )

        try:
            if human_answer is None:
                messages = review_messages(brief, sources, history, draft)
            else:
                messages = answer_review_messages(
                    brief,
                    sources,
                    history,
                    draft,
                    human_answer=human_answer,
                )
        except LLMError as exc:
            return _failed(
                exc.code,
                retryable=exc.retryable,
                outcome_unknown=exc.outcome_unknown,
            )
        except Exception:
            if human_answer is not None:
                return _failed(
                    'invalid_review_input',
                    retryable=False,
                    outcome_unknown=False,
                )
            return _failed(
                'review_failed',
                retryable=False,
                outcome_unknown=True,
            )

        try:
            result = call(messages, stage='reviewer', request_id=request_id)
        except LLMError as exc:
            return _failed(
                exc.code,
                retryable=exc.retryable,
                outcome_unknown=exc.outcome_unknown,
            )
        except Exception:
            return _failed(
                'review_failed',
                retryable=False,
                outcome_unknown=True,
            )

        try:
            review = parse_review(
                result.text,
                piece_keys=piece_keys,
                chunk_ids=chunk_ids,
            )
            if not isinstance(review, dict):
                raise ValueError
            verdict = review['verdict']
            issues = review['issues']
            review_questions = review['questions']
            if not isinstance(verdict, str) or verdict not in _REVIEW_VERDICTS:
                raise ValueError
            if not isinstance(issues, list) or not isinstance(review_questions, list):
                raise ValueError
            review_hash = _review_hash(review)
        except ValueError:
            return _failed(
                'invalid_review',
                retryable=False,
                outcome_unknown=False,
            )
        except Exception:
            return _failed(
                'review_failed',
                retryable=False,
                outcome_unknown=True,
            )

        if verdict == 'pass':
            status = 'needs_human_review'
            questions: list[Any] = []
        elif verdict == 'revise':
            status = 'revision_required'
            questions = []
        else:
            status = 'waiting_input'
            questions = list(review_questions)

        event = {
            'stage': 'reviewer',
            'status': verdict,
            'request_id': request_id,
            'issue_count': len(issues),
            'review_hash': review_hash,
        }
        review_history_entry = {
            'cycle': cycle,
            'hash': review_hash,
            'review': review,
        }

        return {
            'status': status,
            'review': review,
            'review_hash': review_hash,
            'questions': questions,
            'error': None,
            'review_history': [*review_history, review_history_entry],
            'events': [*events, event],
        }

    return review_node
