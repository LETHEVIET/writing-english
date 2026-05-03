from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from writing_english.adapters.base import GECAdapter, GECError

if TYPE_CHECKING:
    pass

_WORD_RE = re.compile(r"\S+")

_PUNCTUATION = frozenset(".,;:!?-–—()[]{}'\"")

_CATEGORIES: dict[str, tuple[str, str]] = {
    "spelling": ("Spelling", "Possible spelling mistake"),
    "punctuation": ("Punctuation", "Punctuation error"),
    "capitalization": ("Capitalization", "Capitalization error"),
    "article": ("Article", "Incorrect article"),
    "verb_form": ("Verb Form", "Incorrect verb form"),
    "deletion": ("Unnecessary Word", "Unnecessary word — should be deleted"),
    "insertion": ("Missing Word", "Missing word — should be added"),
    "merge": ("Merge", "Words should be merged"),
    "split": ("Split", "Word should be split"),
    "reordering": ("Word Order", "Words should be reordered"),
    "grammar": ("Grammar", "Possible grammar error"),
}


def _classify_error(original: str, suggestion: str) -> tuple[str, str]:
    orig_lower = original.lower().strip()
    sugg_lower = suggestion.lower().strip()

    if not suggestion:
        return "deletion", _CATEGORIES["deletion"]

    if orig_lower == sugg_lower and original != suggestion:
        return "capitalization", _CATEGORIES["capitalization"]

    orig_is_punct = all(c in _PUNCTUATION or c.isspace() for c in original)
    sugg_is_punct = all(c in _PUNCTUATION or c.isspace() for c in suggestion)

    if orig_is_punct or sugg_is_punct:
        if orig_is_punct and sugg_is_punct:
            return "punctuation", _CATEGORIES["punctuation"]
        if sugg_is_punct:
            return "punctuation", ("Punctuation", "Missing punctuation")
        return "punctuation", ("Punctuation", "Unnecessary punctuation")

    if original in ("a", "an", "the") or suggestion in ("a", "an", "the"):
        return "article", _CATEGORIES["article"]

    if "-" in suggestion and "-" not in original:
        return "merge", _CATEGORIES["merge"]
    if "-" in original and "-" not in suggestion:
        return "split", _CATEGORIES["split"]

    if not orig_is_punct and not sugg_is_punct:
        # Check for simple pluralization/singularization
        if (
            orig_lower + "s" == sugg_lower
            or orig_lower + "es" == sugg_lower
            or sugg_lower + "s" == orig_lower
            or sugg_lower + "es" == orig_lower
        ):
            return "grammar", _CATEGORIES["grammar"]  # Noun Number (maps to Grammar)

        # Check for simple verb form changes (-ing, -ed, -s)
        if (
            (orig_lower.endswith("ing") and sugg_lower.startswith(orig_lower[:-3]))
            or (sugg_lower.endswith("ing") and orig_lower.startswith(sugg_lower[:-3]))
            or (orig_lower.endswith("ed") and sugg_lower.startswith(orig_lower[:-2]))
            or (sugg_lower.endswith("ed") and orig_lower.startswith(sugg_lower[:-2]))
        ):
            return "verb_form", _CATEGORIES["verb_form"]

        # Irregular verb forms or other verb mappings
        verb_pairs = {("is", "are"), ("was", "were"), ("has", "have"), ("do", "does")}
        for v1, v2 in verb_pairs:
            if (orig_lower == v1 and sugg_lower == v2) or (
                orig_lower == v2 and sugg_lower == v1
            ):
                return "verb_form", _CATEGORIES["verb_form"]

        # Use SequenceMatcher to detect spelling mistakes (high similarity)
        matcher = difflib.SequenceMatcher(None, orig_lower, sugg_lower)
        ratio = matcher.ratio()

        if len(orig_lower) > 3 and ratio >= 0.75:
            return "spelling", _CATEGORIES["spelling"]

    return "grammar", _CATEGORIES["grammar"]


class GectorAdapter(GECAdapter):
    def __init__(self, model_dir: Path) -> None:
        self._model_dir = model_dir
        self._predictor: Any | None = None

    def is_available(self) -> bool:
        try:
            import onnxruntime  # noqa: F401
            import tokenizers  # noqa: F401
            import numpy  # noqa: F401
        except ImportError:
            return False

        if not self._model_dir.exists():
            return False

        required = (
            "model.onnx",
            "config.json",
            "tokenizer.json",
            "verb-form-vocab.txt",
        )
        return all((self._model_dir / f).exists() for f in required)

    def check(self, text: str) -> list[GECError]:
        if not text.strip():
            return []

        self._load()
        if self._predictor is None:
            return []

        paragraphs = text.split("\n")
        paragraphs_to_check: list[str] = []
        offsets: list[int] = []
        offset = 0
        for para in paragraphs:
            if para.strip():
                paragraphs_to_check.append(para)
                offsets.append(offset)
            offset += len(para) + 1

        if not paragraphs_to_check:
            return []

        corrected_list = self._predictor.predict(paragraphs_to_check)

        all_errors: list[GECError] = []
        for para, corrected, offset in zip(
            paragraphs_to_check, corrected_list, offsets
        ):
            if corrected == para:
                continue
            errors = self._parse_response(para, corrected)
            for err in errors:
                all_errors.append(
                    GECError(
                        start=err["start"] + offset,
                        length=err["length"],
                        original=err["original"],
                        suggestion=err["suggestion"],
                        message=err["message"],
                        category=err["category"],
                    )
                )

        return all_errors

    def _load(self) -> None:
        if self._predictor is not None:
            return

        from writing_english.adapters.gec.onnx_predictor import GECToRONNXPredictor

        verb_file = str(self._model_dir / "verb-form-vocab.txt")
        self._predictor = GECToRONNXPredictor(
            model_dir=str(self._model_dir),
            verb_file=verb_file,
            keep_confidence=0.0,
            min_error_prob=0.0,
            batch_size=128,
            n_iteration=5,
        )

    def _parse_response(self, original: str, corrected: str) -> list[GECError]:
        orig_words = list(_WORD_RE.finditer(original))
        corr_words = list(_WORD_RE.finditer(corrected))

        orig_tokens = [m.group() for m in orig_words]
        corr_tokens = [m.group() for m in corr_words]

        matcher = difflib.SequenceMatcher(None, orig_tokens, corr_tokens)
        errors: list[GECError] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            start = orig_words[i1].start() if i1 < len(orig_words) else len(original)
            end = (
                orig_words[i2 - 1].end() if i2 > 0 and i2 <= len(orig_words) else start
            )
            original_str = original[start:end]

            if j1 < len(corr_words):
                sugg_start = corr_words[j1].start()
                sugg_end = corr_words[j2 - 1].end() if j2 > j1 else sugg_start
                suggestion = corrected[sugg_start:sugg_end]
            else:
                suggestion = ""

            category, (cat_label, cat_msg) = _classify_error(original_str, suggestion)

            message = cat_msg
            if suggestion and original_str:
                message = f'{cat_msg}: "{original_str}" → "{suggestion}"'

            errors.append(
                GECError(
                    start=start,
                    length=end - start,
                    original=original_str,
                    suggestion=suggestion,
                    message=message,
                    category=cat_label,
                )
            )

        return errors
