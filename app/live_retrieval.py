'''Current-source local semantic retrieval over the approved corpus.'''

import hashlib
import os
from pathlib import Path

from app.ingestion import load_chunks, source_fingerprint
from app.isolated_embeddings import IsolatedEmbeddings

_APPROVED_SOURCES = frozenset(
    (
        'libfile_6c37cc40080c8191b552dd3b1d48f25b',
        'libfile_53f339c6e3808191aa4d31aa25664829',
    )
)
_CONTENT_VERSION = '0.2'
_CHUNK_SIZE = 400
_OVERLAP = 60
_MAX_QUERY_CHARS = 300
_UNAVAILABLE = 'local retrieval unavailable'
_EMBEDDING_IDENTITY = (
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    '@e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
)


class LocalRetriever:
    '''Retrieve from the current approved corpus using a local index.'''

    source_fingerprint: str
    embedding_identity: str
    chunk_count: int
    index_path: Path

    def __init__(self, project_root: Path, index_dir: Path) -> None:
        try:
            root = Path(os.path.abspath(os.fspath(project_root)))
            chunks = load_chunks(
                root,
                root / 'docs/references/manifest.json',
                chunk_size=_CHUNK_SIZE,
                overlap=_OVERLAP,
            )
            self._validate_chunks(chunks)
            fingerprint = source_fingerprint(chunks)
            if not isinstance(fingerprint, str) or not fingerprint:
                raise ValueError('invalid source fingerprint')

            embedder = IsolatedEmbeddings(
                root / 'data/models/multilingual-minilm',
                root / 'config/embedding-model.json',
                timeout_seconds=30,
            )
            identity = getattr(embedder, 'identity', _EMBEDDING_IDENTITY)
            if isinstance(identity, str) and identity != _EMBEDDING_IDENTITY:
                raise ValueError('invalid embedding identity')

            resolved_index_dir = Path(
                os.path.realpath(os.path.abspath(os.fspath(index_dir)))
            )
            resolved_index_dir.mkdir(parents=True, exist_ok=True)
            identity_short = hashlib.sha256(
                _EMBEDDING_IDENTITY.encode('utf-8')
            ).hexdigest()[:16]
            index_path = resolved_index_dir / (
                fingerprint + '-' + identity_short + '.json'
            )

            from app.retrieval import VectorStore

            try:
                os.lstat(os.fspath(index_path))
            except FileNotFoundError:
                index_exists = False
            else:
                index_exists = True

            if index_exists:
                store = VectorStore.load(
                    index_path,
                    embedder,
                    expected_source_fingerprint=fingerprint,
                )
            else:
                store = VectorStore.build(chunks, embedder)
                store.save(index_path)

            self.source_fingerprint = fingerprint
            self.embedding_identity = _EMBEDDING_IDENTITY
            self.chunk_count = len(chunks)
            self.index_path = index_path
            self.store = store
        except Exception:
            raise ValueError(_UNAVAILABLE) from None

    @staticmethod
    def _validate_chunks(chunks: object) -> None:
        if not isinstance(chunks, list):
            raise ValueError('invalid chunks')
        found = set()
        for chunk in chunks:
            if not isinstance(chunk, dict):
                raise ValueError('invalid chunks')
            source_id = chunk.get('source_id')
            if not isinstance(source_id, str):
                raise ValueError('invalid chunks')
            if chunk.get('content_version') != _CONTENT_VERSION:
                raise ValueError('invalid chunks')
            if chunk.get('trusted_instructions') is not False:
                raise ValueError('invalid chunks')
            found.add(source_id)
        if found != _APPROVED_SOURCES:
            raise ValueError('invalid chunks')

    def __call__(self, query: str) -> list[dict]:
        if not isinstance(query, str):
            raise ValueError('invalid query')
        if len(query) > _MAX_QUERY_CHARS or not query.strip():
            raise ValueError('invalid query')
        try:
            return self.store.search(query, top_k=4, min_score=0.0)
        except Exception:
            raise ValueError(_UNAVAILABLE) from None
