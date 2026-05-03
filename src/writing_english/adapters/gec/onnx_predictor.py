"""Minimal-dependency GECToR inference using ONNX Runtime.

Runtime dependencies (no torch / no transformers):
    - onnxruntime
    - tokenizers
    - numpy

Vendored from gector/src/gector/onnx_predict.py.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np  # type: ignore[import-not-found]
import onnxruntime as ort  # type: ignore[import-not-found]
from tokenizers import Tokenizer  # type: ignore[import-not-found]


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Numerically-stable softmax."""
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def load_verb_dict(verb_file: str) -> Tuple[dict[str, str], dict[str, str]]:
    """Load verb conjugation table (same format as the original predict.py)."""
    encode: dict[str, str] = {}
    decode: dict[str, str] = {}
    with open(verb_file, encoding="utf-8") as f:
        for line in f:
            words, tags = line.split(":")
            word1, word2 = words.split("_")
            tag1, tag2 = tags.split("_")
            decode_key = f"{word1}_{tag1}_{tag2.strip()}"
            if decode_key not in decode:
                encode[words] = tags
                decode[decode_key] = word2
    return encode, decode


def edit_src_by_tags(
    srcs: List[List[str]],
    pred_labels: List[List[str]],
    encode: dict[str, str],
    decode: dict[str, str],
) -> List[List[str]]:
    edited_srcs = []
    for tokens, labels in zip(srcs, pred_labels):
        edited_tokens = []
        for t, lbl in zip(tokens, labels):
            n_token = process_token(t, lbl, encode, decode)
            if n_token is None:
                n_token = t
            edited_tokens += n_token.split(" ")
        if len(tokens) > len(labels):
            omitted_tokens = tokens[len(labels) :]
            edited_tokens += omitted_tokens
        temp_str = (
            " ".join(edited_tokens)
            .replace(" $MERGE_HYPHEN ", "-")
            .replace(" $MERGE_SPACE ", "")
            .replace(" $DELETE", "")
            .replace("$DELETE ", "")
        )
        edited_srcs.append(temp_str.split(" "))
    return edited_srcs


def process_token(
    token: str,
    label: str,
    encode: dict[str, str],
    decode: dict[str, str],
) -> str:
    if "$APPEND_" in label:
        return token + " " + label.replace("$APPEND_", "")
    elif token == "$START":
        return token
    elif label in ["<PAD>", "<OOV>", "$KEEP"]:
        return token
    elif "$TRANSFORM_" in label:
        return g_transform_processer(token, label, encode, decode)
    elif "$REPLACE_" in label:
        return label.replace("$REPLACE_", "")
    elif label == "$DELETE":
        return label
    elif "$MERGE_" in label:
        return token + " " + label
    else:
        return token


def g_transform_processer(
    token: str,
    label: str,
    encode: dict[str, str],
    decode: dict[str, str],
) -> str:
    if label == "$TRANSFORM_CASE_LOWER":
        return token.lower()
    elif label == "$TRANSFORM_CASE_UPPER":
        return token.upper()
    elif label == "$TRANSFORM_CASE_CAPITAL":
        return token.capitalize()
    elif label == "$TRANSFORM_CASE_CAPITAL_1":
        if len(token) <= 1:
            return token
        return token[0] + token[1:].capitalize()
    elif label == "$TRANSFORM_AGREEMENT_PLURAL":
        return token + "s"
    elif label == "$TRANSFORM_AGREEMENT_SINGULAR":
        return token[:-1]
    elif label == "$TRANSFORM_SPLIT_HYPHEN":
        return " ".join(token.split("-"))
    else:
        encoding_part = f"{token}_{label[len('$TRANSFORM_VERB_') :]}"
        decoded_target_word = decode.get(encoding_part)
        if decoded_target_word is None:
            return token
        return decoded_target_word


def get_word_masks_from_word_ids(
    word_ids_list: List[List[Optional[int]]],
) -> List[List[int]]:
    word_masks = []
    for word_ids in word_ids_list:
        previous_id: int | None = 0
        mask = []
        for _id in word_ids:
            if _id is None:
                mask.append(0)
            elif previous_id != _id:
                mask.append(1)
            else:
                mask.append(0)
            previous_id = _id
        word_masks.append(mask)
    return word_masks


class GECToRONNXPredictor:
    """Drop-in lightweight predictor that runs a GECToR ONNX model."""

    def __init__(
        self,
        model_dir: str,
        verb_file: Optional[str] = None,
        keep_confidence: float = 0.0,
        min_error_prob: float = 0.0,
        batch_size: int = 128,
        n_iteration: int = 5,
    ) -> None:
        model_path = Path(model_dir)
        config_path = model_path / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"config.json not found in {model_dir}")

        with open(config_path, encoding="utf-8") as f:
            raw_config = json.load(f)

        self.config = raw_config
        self.label2id = {k: int(v) for k, v in raw_config["label2id"].items()}
        self.id2label = {int(k): v for k, v in raw_config["id2label"].items()}
        self.d_label2id = {k: int(v) for k, v in raw_config["d_label2id"].items()}
        self.keep_label = raw_config.get("keep_label", "$KEEP")
        self.incorrect_label = raw_config.get("incorrect_label", "$INCORRECT")
        self.keep_index = self.label2id[self.keep_label]
        self.incor_idx = self.d_label2id[self.incorrect_label]
        self.no_correction_ids = [
            self.label2id[lbl] for lbl in ["$KEEP", "<OOV>", "<PAD>"]
        ]
        self.is_official_model = raw_config.get("is_official_model", False)
        self.max_length = raw_config.get("max_length", 80)

        tokenizer_path = model_path / "tokenizer.json"
        if not tokenizer_path.exists():
            raise FileNotFoundError(f"tokenizer.json not found in {model_dir}")
        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.tokenizer.enable_padding(length=self.max_length)
        self.tokenizer.enable_truncation(max_length=self.max_length)

        onnx_path = model_path / "model.onnx"
        if not onnx_path.exists():
            raise FileNotFoundError(f"model.onnx not found in {model_dir}")

        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        sess_options.log_severity_level = 3
        self.session = ort.InferenceSession(
            str(onnx_path),
            sess_options,
            providers=["CPUExecutionProvider"],
        )

        self.keep_confidence = keep_confidence
        self.min_error_prob = min_error_prob
        self.batch_size = batch_size
        self.n_iteration = n_iteration

        self.encode: dict[str, str] = {}
        self.decode: dict[str, str] = {}
        if verb_file is not None and os.path.exists(verb_file):
            self.encode, self.decode = load_verb_dict(verb_file)

    def _predict_batch(
        self, srcs: List[List[str]]
    ) -> Tuple[List[List[str]], List[bool]]:
        """Run a single inference batch and return word-level labels."""
        encs = self.tokenizer.encode_batch(
            srcs,
            is_pretokenized=True,
            add_special_tokens=not self.is_official_model,
        )
        input_ids = np.array([enc.ids for enc in encs], dtype=np.int64)
        attention_mask = np.array([enc.attention_mask for enc in encs], dtype=np.int64)
        word_ids_list = [enc.word_ids for enc in encs]
        word_masks = np.array(
            get_word_masks_from_word_ids(word_ids_list), dtype=np.float32
        )

        logits_d, logits_labels = self.session.run(
            None, {"input_ids": input_ids, "attention_mask": attention_mask}
        )

        prob_labels = softmax(logits_labels, axis=-1)
        prob_d = softmax(logits_d, axis=-1)

        # Bias $KEEP confidence (same as original predict())
        prob_labels[:, :, self.keep_index] += self.keep_confidence
        pred_label_ids = np.argmax(prob_labels, axis=-1)

        # Sentence-level minimum error probability
        prob_d_incor = prob_d[:, :, self.incor_idx]
        max_error_prob = np.max(prob_d_incor * word_masks, axis=-1)
        pred_label_ids[max_error_prob < self.min_error_prob, :] = self.keep_index

        # Token-level minimum error probability
        max_label_prob = np.max(prob_labels, axis=-1)
        pred_label_ids[max_label_prob < self.min_error_prob] = self.keep_index

        # Align subword predictions back to words
        pred_labels = []
        no_corrections = []
        for i in range(len(srcs)):
            labels = []
            no_correct = True
            previous_word_idx = None
            for j, idx in enumerate(word_ids_list[i]):
                if idx is None:
                    continue
                if idx != previous_word_idx:
                    lid = int(pred_label_ids[i, j])
                    label = self.id2label[lid]
                    labels.append(label)
                    if lid not in self.no_correction_ids:
                        no_correct = False
                previous_word_idx = idx
            pred_labels.append(labels)
            no_corrections.append(no_correct)

        return pred_labels, no_corrections

    def predict(self, texts: List[str]) -> List[str]:
        """Iteratively correct a list of raw sentences."""
        srcs = [["$START"] + text.split(" ") for text in texts]
        final_edited_sents = ["-1"] * len(srcs)
        to_be_processed = srcs
        original_sent_idx = list(range(len(srcs)))

        for itr in range(self.n_iteration):
            pred_labels, no_corrections = self._predict_batch(to_be_processed)
            current_srcs = []
            current_pred_labels = []
            current_orig_idx = []
            for i, yes in enumerate(no_corrections):
                if yes:
                    final_edited_sents[original_sent_idx[i]] = " ".join(
                        to_be_processed[i]
                    ).replace("$START ", "")
                else:
                    current_srcs.append(to_be_processed[i])
                    current_pred_labels.append(pred_labels[i])
                    current_orig_idx.append(original_sent_idx[i])
            if not current_srcs:
                break
            edited_srcs = edit_src_by_tags(
                current_srcs, current_pred_labels, self.encode, self.decode
            )
            to_be_processed = edited_srcs
            original_sent_idx = current_orig_idx

        for i in range(len(to_be_processed)):
            final_edited_sents[original_sent_idx[i]] = " ".join(
                to_be_processed[i]
            ).replace("$START ", "")
        assert "-1" not in final_edited_sents
        return final_edited_sents
