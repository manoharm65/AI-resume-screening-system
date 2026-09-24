from __future__ import annotations

import re

from .eligibility import evaluate_eligibility
from .models import Candidate, Penalty, ScoreResult


def _text(candidate: Candidate) -> str:
    projects = [
        " ".join([project.name, project.description, *project.technologies, *project.evidence])
        for project in candidate.projects
    ]
    return " ".join([*projects, *candidate.experience, *candidate.engineering_evidence]).lower()


def _matches(text: str, patterns: tuple[str, ...]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, re.IGNORECASE)]


def score_candidate(candidate: Candidate, github_points: int = 0, github_evidence: list[str] | None = None) -> ScoreResult:
    eligibility = evaluate_eligibility(candidate)
    if not eligibility.eligible:
        raise ValueError("Only eligible candidates can be scored")

    text = _text(candidate)
    ai_evidence = _matches(text, ("rag", "retrieval", "embedding", "vector", "agent", "tool calling", "state", "orchestration", "evaluation"))
    backend_evidence = _matches(text, ("python", "fastapi", "django", "flask", "backend", "api", "postgres", "redis", "async", "architecture"))
    platform_evidence = _matches(text, ("gcp", "cloud", "docker", "deploy", "ci/cd", "react", "next.js", "full.?stack"))
    engineering_evidence = _matches(text, ("test", "cache", "queue", "observability", "concurren", "error handling", "retry", "failure"))

    ai = min(40, sum((8, 8, 7, 7, 5, 5)[index] for index, pattern in enumerate(("retrieval|rag|vector|embedding", "agent|tool calling", "state|orchestration", "business|workflow|backend", "evaluation|test", "implement|built|developed")) if re.search(pattern, text, re.IGNORECASE)))
    backend = min(30, sum((10, 6, 5, 3, 3, 3)[index] for index, pattern in enumerate(("python", "fastapi|django|flask|backend|api", "postgres|sql", "async", "redis", "architecture")) if re.search(pattern, text, re.IGNORECASE)))
    platform = min(15, sum((8, 7)[index] for index, pattern in enumerate(("gcp|cloud|docker|deploy|ci/cd", "react|next.js|full.?stack")) if re.search(pattern, text, re.IGNORECASE)))
    engineering = min(5, len(engineering_evidence))

    penalties: list[Penalty] = []
    shallow_wrapper = re.search(r"(?:openai|gemini|llm)\s+(?:api|integration)", text, re.IGNORECASE) and not re.search(
        r"(?:rag|retrieval|embedding|vector|agent|tool calling|evaluation|workflow|state)", text, re.IGNORECASE
    )
    if shallow_wrapper:
        penalties.append(Penalty(reason="AI project appears to be a thin LLM API wrapper", points=-10))

    github = max(0, min(10, github_points))
    categories = {
        "ai_agentic_rag_depth": ai,
        "python_backend_engineering": backend,
        "cloud_deployment_full_stack": platform,
        "github_activity": github,
        "engineering_depth": engineering,
    }
    total = max(0, sum(categories.values()) + sum(penalty.points for penalty in penalties))
    evidence = {
        "ai_agentic_rag_depth": ai_evidence,
        "python_backend_engineering": backend_evidence,
        "cloud_deployment_full_stack": platform_evidence,
        "github_activity": github_evidence or [],
        "engineering_depth": engineering_evidence,
    }
    return ScoreResult(total=total, categories=categories, evidence=evidence, penalties=penalties)