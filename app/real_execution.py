from .storage import connect
from .runs import get_run, transition_run, set_snapshots
from .real_results import save_result, get_bundle
from .bootstrap import load_runtime_config
from .history_context import build_context
from .live_retrieval import LocalRetriever
from .llm_client import LLMClient
from .llm_execution import execute_call
from .response_schemas import generation_schema, review_schema
from .agent_pipeline import build_agent_graph


APP_MODEL = 'qwen/qwen3.8-flash'

_TERMINAL_RUN_STATUSES = frozenset(
    ('needs_review', 'waiting_input', 'failed', 'finished', 'cancelled')
)

_PUBLIC_OUTPUT_KEYS = frozenset(
    (
        'campaign_id',
        'run_id',
        'query',
        'brief',
        'history',
        'sources',
        'query_count',
        'status',
        'events',
        'questions',
        'human_answer',
        'cycle',
        'draft',
        'draft_hash',
        'draft_history',
        'review',
        'review_hash',
        'review_history',
        'error',
    )
)


def _review_piece_keys(formats):
    return [
        fmt + ':' + variant
        for fmt in formats
        for variant in (['A', 'B', 'C'] if fmt == 'ad' else [''])
    ]


def execute_run(
    project_root,
    db_path,
    work_dir,
    run_id,
    query,
    *,
    config=None,
    retrieve=None,
    client_factory=None,
):
    conn = None
    client_stack = None
    current = None
    try:
        conn = connect(db_path)
        existing = get_run(conn, run_id)
        if existing is None:
            raise ValueError('run not found')

        status = existing.get('status')
        if status in _TERMINAL_RUN_STATUSES:
            try:
                return get_bundle(conn, run_id)
            except Exception:
                raise ValueError('stored result is unavailable') from None
        if status == 'running':
            raise ValueError('run is already running; outcome is uncertain')
        if status != 'prepared':
            raise ValueError('run is not prepared')

        if not isinstance(query, str) or not query.strip() or len(query) > 300:
            raise ValueError('invalid query')

        if config is None:
            try:
                config = load_runtime_config(
                    project_root,
                    env={
                        'APP_LLM_ENABLED': 'true',
                        'APP_LLM_MODEL': APP_MODEL,
                        'APP_LLM_TIMEOUT_SECONDS': '60',
                    },
                )
            except Exception:
                raise ValueError('configuration is unavailable') from None

        if not bool(getattr(config, 'llm_enabled', False)):
            raise ValueError('llm must be enabled')
        if getattr(config, 'model', None) != APP_MODEL:
            raise ValueError('unsupported llm model')

        try:
            current = transition_run(
                conn,
                run_id,
                'running',
                'execute',
                expected_status='prepared',
            )
        except Exception:
            latest = get_run(conn, run_id)
            if latest is not None and latest.get('status') in _TERMINAL_RUN_STATUSES:
                try:
                    return get_bundle(conn, run_id)
                except Exception:
                    raise ValueError('stored result is unavailable') from None
            raise ValueError('could not start run') from None

        execution_failed = False
        try:
            from contextlib import ExitStack
            from pathlib import Path

            current_run = get_run(conn, run_id) or current
            history = build_context(
                conn, current_run['campaign_id']
            )

            work_dir = Path(work_dir)
            work_dir.mkdir(parents=True, exist_ok=True)

            if retrieve is None:
                retriever = LocalRetriever(
                    project_root, work_dir / 'index'
                )
            else:
                retriever = retrieve

            def wrapped_retrieve(value):
                sources = retriever(value)
                set_snapshots(conn, run_id, sources, history)
                return sources

            client_stack = ExitStack()
            clients = {}

            if client_factory is None:

                def factory(cfg, *, stage, response_schema):
                    return LLMClient(
                        cfg,
                        allow_remote=True,
                        response_schema=response_schema,
                        response_model_aliases=(APP_MODEL + '-20260826',),
                        reasoning_enabled=False,
                    )

            else:
                factory = client_factory

            def call(messages, *, stage, request_id):
                if stage not in ('generator', 'reviewer'):
                    raise ValueError('invalid stage')

                snapshot = get_run(conn, run_id)
                if snapshot is None:
                    raise ValueError('run not found')
                ids = [source['chunk_id'] for source in snapshot['sources']]
                formats = snapshot['config']['formats']

                if stage == 'generator':
                    response_schema = generation_schema(formats, ids)
                else:
                    response_schema = review_schema(
                        _review_piece_keys(formats), ids
                    )

                if stage not in clients:
                    clients[stage] = client_stack.enter_context(
                        factory(
                            config,
                            stage=stage,
                            response_schema=response_schema,
                        )
                    )
                client = clients[stage]

                call_conn = connect(db_path)
                try:
                    return execute_call(
                        call_conn,
                        run_id,
                        request_id,
                        messages,
                        stage=stage,
                        config=config,
                        client=client,
                    )
                finally:
                    try:
                        call_conn.close()
                    except Exception:
                        pass

            from langgraph.checkpoint.sqlite import SqliteSaver

            checkpoint_path = work_dir / 'checkpoints.sqlite'
            with SqliteSaver.from_conn_string(str(checkpoint_path)) as saver:
                graph = build_agent_graph(
                    checkpointer=saver,
                    retrieve=wrapped_retrieve,
                    call=call,
                    max_revisions=1,
                )
                initial_state = {
                    'campaign_id': current_run['campaign_id'],
                    'run_id': run_id,
                    'query': query,
                    'brief': current_run['config'],
                    'history': history,
                }
                graph_config = {
                    'configurable': {
                        'thread_id': (
                            f'gwa:{current_run["campaign_id"]}:{run_id}'
                        )
                    },
                    'recursion_limit': 20,
                }
                graph_result = graph.invoke(initial_state, graph_config)

            if not isinstance(graph_result, dict):
                raise TypeError('invalid graph result')

            interrupted = '__interrupt__' in graph_result
            output = {
                key: graph_result[key]
                for key in _PUBLIC_OUTPUT_KEYS
                if key in graph_result
            }
            if interrupted:
                output['status'] = 'waiting_input'
                interrupt_questions = []
                interrupts = graph_result.get('__interrupt__')
                if isinstance(interrupts, (tuple, list)):
                    for interrupt in interrupts:
                        value = getattr(interrupt, 'value', None)
                        if not isinstance(value, dict):
                            continue
                        questions = value.get('questions')
                        if (
                            isinstance(questions, list)
                            and 1 <= len(questions) <= 5
                            and all(
                                isinstance(question, str)
                                and question.strip()
                                and len(question) <= 500
                                for question in questions
                            )
                        ):
                            interrupt_questions = questions
                            break
                if interrupt_questions:
                    output['questions'] = interrupt_questions[:5]

            latest = get_run(conn, run_id) or current_run
            output['campaign_id'] = current_run['campaign_id']
            output['run_id'] = run_id
            output['brief'] = current_run['config']
            output['sources'] = latest.get('sources') or []
            output.setdefault('query', query)
            output.setdefault('history', history)
            output.setdefault('questions', [])

        except Exception:
            execution_failed = True

        if execution_failed:
            try:
                current_run = get_run(conn, run_id) or current
                failed_output = {
                    'campaign_id': current_run.get('campaign_id'),
                    'run_id': run_id,
                    'sources': current_run.get('sources') or [],
                    'brief': current_run.get('config') or {},
                    'status': 'failed',
                    'events': [],
                    'questions': [],
                    'draft': None,
                    'review': None,
                    'error': {
                        'code': 'execution_failed',
                        'retryable': False,
                        'outcome_unknown': True,
                    },
                }
                return save_result(conn, run_id, failed_output)
            except Exception:
                raise ValueError('could not persist execution result') from None

        try:
            return save_result(conn, run_id, output)
        except Exception:
            raise ValueError('could not persist execution result') from None

    finally:
        if client_stack is not None:
            try:
                client_stack.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
