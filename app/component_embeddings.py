"""Pinned local MiniLM component embeddings.

This module deliberately avoids the sentence-transformers, faiss, and sklearn
packages.  Model loading is lazy and occurs only after the component isolation
guard has passed.
"""

import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path

import numpy as np


IDENTITY = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@"
    "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
)

_MAX_BATCH = 10_000
_MAX_TEXT_CHARS = 2_000
_MAX_TOKENS = 128
_HIDDEN_DIMENSION = 384

_FORBIDDEN_ROOTS = ("faiss", "sklearn", "sentence_transformers")
_BINARY_FORBIDDEN_ROOTS = ("faiss", "sklearn")
_AUDIT_MARKER = "_component_embeddings_isolation_audit_installed"

_ERROR = "component embeddings operation failed"
_ISOLATION_ERROR = "component isolation violation"


def _at_forbidden_root(name):
    if not isinstance(name, str):
        return False
    for root in _FORBIDDEN_ROOTS:
        if name == root or name.startswith(root + "."):
            return True
    return False


def _isolation_audit_hook(event, args):
    if event == "import" and args:
        if _at_forbidden_root(args[0]):
            raise ValueError(_ISOLATION_ERROR)


def _install_audit_hook():
    if getattr(sys, _AUDIT_MARKER, False):
        return
    sys.addaudithook(_isolation_audit_hook)
    setattr(sys, _AUDIT_MARKER, True)


def assert_component_isolation():
    """Fail if a forbidden component is loaded or available for import."""

    try:
        module_names = tuple(sys.modules)
    except Exception:
        raise ValueError(_ISOLATION_ERROR) from None

    for name in module_names:
        if _at_forbidden_root(name):
            raise ValueError(_ISOLATION_ERROR) from None

    _install_audit_hook()

    for name in _BINARY_FORBIDDEN_ROOTS:
        try:
            spec = importlib.util.find_spec(name)
        except Exception:
            raise ValueError(_ISOLATION_ERROR) from None
        if spec is not None:
            raise ValueError(_ISOLATION_ERROR) from None


def _read_local_json(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except Exception:
        raise ValueError(_ERROR) from None
    if not isinstance(value, dict):
        raise ValueError(_ERROR)
    return value


def _read_local_modules(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except Exception:
        raise ValueError(_ERROR) from None
    if not isinstance(value, list):
        raise ValueError(_ERROR)
    return value


def _validate_component_configuration(root):
    sentence_bert = _read_local_json(root / "sentence_bert_config.json")
    if sentence_bert.get("max_seq_length") != _MAX_TOKENS:
        raise ValueError(_ERROR)
    if sentence_bert.get("do_lower_case") is not False:
        raise ValueError(_ERROR)

    pooling = _read_local_json(root / "1_Pooling" / "config.json")
    if pooling.get("word_embedding_dimension") != _HIDDEN_DIMENSION:
        raise ValueError(_ERROR)
    if pooling.get("pooling_mode_mean_tokens") is not True:
        raise ValueError(_ERROR)
    if pooling.get("pooling_mode_cls_token") is not False:
        raise ValueError(_ERROR)
    if pooling.get("pooling_mode_max_tokens") is not False:
        raise ValueError(_ERROR)
    if pooling.get("pooling_mode_mean_sqrt_len_tokens") is not False:
        raise ValueError(_ERROR)

    modules = _read_local_modules(root / "modules.json")
    if len(modules) != 2:
        raise ValueError(_ERROR)

    transformer, pooling_module = modules
    if not isinstance(transformer, dict) or not isinstance(pooling_module, dict):
        raise ValueError(_ERROR)

    if transformer.get("type") != "sentence_transformers.models.Transformer":
        raise ValueError(_ERROR)
    if transformer.get("path") != "":
        raise ValueError(_ERROR)
    if pooling_module.get("type") != "sentence_transformers.models.Pooling":
        raise ValueError(_ERROR)
    if pooling_module.get("path") != "1_Pooling":
        raise ValueError(_ERROR)


def _sequence_length(input_ids):
    try:
        return len(input_ids)
    except Exception:
        raise ValueError(_ERROR) from None


def prepare_inputs(tokenizer, texts):
    """Validate texts and tokenize them without silently truncating originals."""

    if type(texts) is not list:
        raise ValueError(_ERROR)
    if not 1 <= len(texts) <= _MAX_BATCH:
        raise ValueError(_ERROR)

    originals = []
    for text in texts:
        if type(text) is not str:
            raise ValueError(_ERROR)
        if not text.strip() or len(text) > _MAX_TEXT_CHARS:
            raise ValueError(_ERROR)
        originals.append(text)

    for text in originals:
        try:
            encoded = tokenizer(text, add_special_tokens=True, truncation=False)
            input_ids = encoded["input_ids"]
        except Exception:
            raise ValueError(_ERROR) from None
        length = _sequence_length(input_ids)
        if not 1 <= length <= _MAX_TOKENS:
            raise ValueError(_ERROR)

    try:
        inputs = tokenizer(
            originals,
            padding=True,
            truncation=True,
            max_length=_MAX_TOKENS,
            return_tensors="pt",
        )
    except Exception:
        raise ValueError(_ERROR) from None

    if not isinstance(inputs, Mapping):
        raise ValueError(_ERROR)
    if "input_ids" not in inputs or "attention_mask" not in inputs:
        raise ValueError(_ERROR)
    return inputs


def mean_pool_normalize(tokens, attention_mask):
    """Masked mean pooling followed by float32 L2 normalization."""

    try:
        token_array = np.asarray(tokens)
        mask_array = np.asarray(attention_mask)
    except Exception:
        raise ValueError(_ERROR) from None

    if token_array.ndim != 3 or token_array.shape[2] != _HIDDEN_DIMENSION:
        raise ValueError(_ERROR)
    if token_array.shape[0] < 1 or token_array.shape[1] < 1:
        raise ValueError(_ERROR)
    if mask_array.ndim != 2:
        raise ValueError(_ERROR)
    if mask_array.shape != token_array.shape[:2]:
        raise ValueError(_ERROR)

    if not np.issubdtype(token_array.dtype, np.floating):
        raise ValueError(_ERROR)
    try:
        token_array = token_array.astype(np.float32, copy=False)
    except Exception:
        raise ValueError(_ERROR) from None

    if mask_array.dtype == np.bool_:
        mask_binary = mask_array
    else:
        if not np.issubdtype(mask_array.dtype, np.floating):
            if not np.issubdtype(mask_array.dtype, np.integer):
                raise ValueError(_ERROR)
        try:
            mask_binary = mask_array == 1
            other_values = mask_array != 0
            invalid = np.logical_and(other_values, mask_array != 1)
            if np.any(invalid):
                raise ValueError(_ERROR)
        except ValueError:
            raise
        except Exception:
            raise ValueError(_ERROR) from None

    if not np.all(np.isfinite(token_array)):
        raise ValueError(_ERROR)

    mask_float = mask_binary.astype(np.float32, copy=False)
    counts = np.sum(mask_float, axis=1, dtype=np.float32)
    if np.any(counts < 1.0) or not np.all(np.isfinite(counts)):
        raise ValueError(_ERROR)

    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        weighted = np.sum(
            token_array * mask_float[..., None], axis=1, dtype=np.float32
        )
        pooled = weighted / counts[:, None]
        norms = np.sqrt(
            np.sum(pooled * pooled, axis=1, keepdims=True, dtype=np.float32)
        )
        if not np.all(np.isfinite(pooled)) or not np.all(np.isfinite(norms)):
            raise ValueError(_ERROR)
        if np.any(norms <= 0.0):
            raise ValueError(_ERROR)
        normalized = pooled / norms

    if not np.all(np.isfinite(normalized)):
        raise ValueError(_ERROR)
    return np.ascontiguousarray(normalized, dtype=np.float32)


class ComponentEmbeddings:
    identity = IDENTITY

    def __init__(self, model_dir: Path, manifest_path: Path):
        assert_component_isolation()

        try:
            from .local_embeddings import (
                _read_manifest,
                _validate_manifest,
                _verify_model_files,
            )
        except Exception:
            raise ValueError(_ERROR) from None

        try:
            root = Path(model_dir)
            manifest_file = Path(manifest_path)
        except Exception:
            raise ValueError(_ERROR) from None

        try:
            manifest = _read_manifest(manifest_file)
            files = _validate_manifest(manifest)
            _verify_model_files(root, files)
            _validate_component_configuration(root)
        except ValueError:
            raise
        except Exception:
            raise ValueError(_ERROR) from None

        assert_component_isolation()

        try:
            from transformers.models.bert.modeling_bert import BertModel
            from transformers.tokenization_utils_fast import PreTrainedTokenizerFast

            tokenizer = PreTrainedTokenizerFast.from_pretrained(
                str(root),
                local_files_only=True,
                trust_remote_code=False,
                token=False,
            )
            model = BertModel.from_pretrained(
                str(root),
                local_files_only=True,
                trust_remote_code=False,
                token=False,
                use_safetensors=True,
            )
            model.to("cpu").eval()

            import torch
        except Exception:
            raise ValueError(_ERROR) from None

        assert_component_isolation()

        self.model = model
        self.tokenizer = tokenizer
        self.torch = torch

    def encode(self, texts):
        assert_component_isolation()

        try:
            inputs = prepare_inputs(self.tokenizer, texts)
            cpu_inputs = {}
            for key, value in inputs.items():
                if hasattr(value, "to"):
                    cpu_inputs[key] = value.to("cpu")
                else:
                    cpu_inputs[key] = value

            with self.torch.inference_mode():
                output = self.model(**cpu_inputs)
            hidden_states = output.last_hidden_state.detach().cpu().numpy()
            mask = cpu_inputs["attention_mask"].detach().cpu().numpy()
            result = mean_pool_normalize(hidden_states, mask)
        except ValueError:
            raise
        except Exception:
            raise ValueError(_ERROR) from None

        assert_component_isolation()
        return result
