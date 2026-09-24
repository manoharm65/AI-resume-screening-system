from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .models import Candidate
from .utils import extract_candidate


StructuredExtractor = Callable[[str, str], Candidate]


def extract_candidate_with_fallback(
    text: str,
    source_file: Path | str,
    provider: StructuredExtractor | None = None,
    links: list[str] | None = None,
) -> tuple[Candidate, str | None]:
    """Use an optional structured provider while preserving a deterministic fallback."""
    if provider is None:
        return extract_candidate(text, source_file, links), None
    try:
        candidate = provider(text, str(source_file))
        return candidate, None
    except Exception as exc:
        return extract_candidate(text, source_file, links), str(exc)