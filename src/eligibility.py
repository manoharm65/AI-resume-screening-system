from __future__ import annotations

import re

from .models import Candidate, EligibilityResult


PYTHON_PATTERN = re.compile(r"\bpython\b", re.IGNORECASE)
AI_PATTERN = re.compile(
    r"\b(?:ai|ml|machine learning|deep learning|llm|rag|"
    r"retrieval[- ]augmented generation|retrieval|embedding(?:s)?|"
    r"vector (?:search|database|store)|langchain|langgraph|llamaindex|"
    r"agentic|agents?|multi-agent|tool calling|openai|gemini|tensorflow|pytorch)\b",
    re.IGNORECASE,
)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = " ".join(value.split())
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            result.append(cleaned)
    return result


def _implementation_text(candidate: Candidate) -> list[str]:
    project_text = [
        " ".join(part for part in [project.name, project.description, *project.technologies, *project.evidence] if part)
        for project in candidate.projects
    ]
    return _unique([*project_text, *candidate.experience, *candidate.ai_evidence])


def detect_python_evidence(candidate: Candidate) -> list[str]:
    evidence = [skill for skill in candidate.skills if PYTHON_PATTERN.search(skill)]
    evidence.extend(item for item in candidate.python_evidence if PYTHON_PATTERN.search(item))
    evidence.extend(item for item in _implementation_text(candidate) if PYTHON_PATTERN.search(item))
    return _unique(evidence)


def detect_ai_evidence(candidate: Candidate) -> list[str]:
    implementation_text = _implementation_text(candidate)
    return _unique([item for item in implementation_text if AI_PATTERN.search(item)])


def evaluate_eligibility(candidate: Candidate) -> EligibilityResult:
    python_evidence = detect_python_evidence(candidate)
    ai_evidence = detect_ai_evidence(candidate)
    reasons: list[str] = []

    if not python_evidence:
        reasons.append("No evidence of Python implementation")
    if not ai_evidence:
        reasons.append("No meaningful AI, LLM, RAG, or agentic evidence")

    return EligibilityResult(
        eligible=not reasons,
        rejection_reasons=reasons,
        python_evidence=python_evidence,
        ai_evidence=ai_evidence,
    )