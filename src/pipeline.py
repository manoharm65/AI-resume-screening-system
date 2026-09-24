from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .eligibility import evaluate_eligibility
from .github import GitHubClient, github_username
from .llm import StructuredExtractor, extract_candidate_with_fallback
from .models import Candidate, GitHubResult, ParseFailure
from .parser import ResumeParseError, discover_resume_files, extract_resume_text
from .scorer import score_candidate


def _candidate_result(candidate: Candidate, github: GitHubResult | None = None) -> dict[str, Any]:
    eligibility = evaluate_eligibility(candidate)
    result: dict[str, Any] = {
        "candidate_name": candidate.candidate_name,
        "source_file": candidate.source_file,
        "github_url": candidate.github_url,
        "github_username": github.username if github else github_username(candidate.github_url),
        "eligible": eligibility.eligible,
        "rejection_reasons": eligibility.rejection_reasons,
        "matched_skills": candidate.skills,
        "project_summary": [project.model_dump() for project in candidate.projects],
        "github": (github or GitHubResult(status="not_applicable")).model_dump(),
        "strengths": [],
        "concerns": [],
    }
    if not eligibility.eligible:
        result["strength"] = None
        result["concerns"] = eligibility.rejection_reasons
        return result

    github = github or GitHubResult(status="missing")
    score = score_candidate(candidate, github_points=github.score, github_evidence=[github.status])
    result["score"] = score.total
    result["total_score"] = score.total
    result["score_breakdown"] = score.categories
    result["score_evidence"] = score.evidence
    result["penalties"] = [penalty.model_dump() for penalty in score.penalties]
    result["strength"] = _strength(candidate)
    result["strengths"] = _strengths(candidate)
    result["concerns"] = _concerns(candidate, score)
    return result


def _strength(candidate: Candidate) -> str:
    evidence = [*candidate.ai_evidence, *candidate.engineering_evidence, *candidate.python_evidence]
    return evidence[0] if evidence else "Eligible based on Python and AI implementation evidence"


def _strengths(candidate: Candidate) -> list[str]:
    strengths: list[str] = []
    if candidate.python_evidence:
        strengths.append("Python implementation evidence")
    if candidate.ai_evidence:
        strengths.append("AI/LLM/agentic implementation evidence")
    if candidate.projects:
        strengths.append("Project evidence available")
    return strengths


def _concerns(candidate: Candidate, score: Any) -> list[str]:
    concerns: list[str] = []
    if not candidate.github_url:
        concerns.append("No GitHub profile found")
    if score.categories.get("engineering_depth", 0) == 0:
        concerns.append("Limited engineering-depth evidence")
    concerns.extend(penalty.reason for penalty in score.penalties)
    return concerns


def run_pipeline(
    input_path: Path,
    output_path: Path,
    github_client: GitHubClient | None = None,
    provider: StructuredExtractor | None = None,
) -> dict[str, Any]:
    """Process every discovered PDF and write a machine-readable batch result."""
    github_client = github_client or GitHubClient()
    ranked: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    llm_fallbacks: list[dict[str, str]] = []
    duplicate_files: list[dict[str, str]] = []
    seen_hashes: dict[str, str] = {}
    successfully_parsed = 0

    for file_path in discover_resume_files(input_path):
        try:
            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            if file_hash in seen_hashes:
                duplicate_files.append({"file": str(file_path), "duplicate_of": seen_hashes[file_hash]})
                continue
            seen_hashes[file_hash] = str(file_path)
            parsed = extract_resume_text(file_path)
            successfully_parsed += 1
            candidate, llm_error = extract_candidate_with_fallback(parsed.text, file_path, provider, parsed.links)
            if llm_error:
                llm_fallbacks.append({"file": str(file_path), "error": llm_error})
            eligibility = evaluate_eligibility(candidate)
            github = (
                github_client.enrich(candidate.github_url)
                if eligibility.eligible
                else GitHubResult(
                    status="not_applicable",
                    profile_url=candidate.github_url,
                    username=github_username(candidate.github_url),
                )
            )
            result = _candidate_result(candidate, github)
            (ranked if result["eligible"] else rejected).append(result)
        except (ResumeParseError, OSError, ValueError) as exc:
            failures.append(ParseFailure(file=str(file_path), error=str(exc)).model_dump())
        except Exception as exc:
            failures.append(ParseFailure(file=str(file_path), error=f"Unexpected processing error: {exc}").model_dump())

    ranked.sort(key=lambda result: result.get("score", 0), reverse=True)
    for index, result in enumerate(ranked, start=1):
        result["rank"] = index
        result["ranking_number"] = index

    output = {
        "ranked_candidates": ranked,
        "rejected_candidates": rejected,
        "failed_resumes": failures,
        "duplicate_files": duplicate_files,
        "summary": {
            "total_files": len(ranked) + len(rejected) + len(failures) + len(duplicate_files),
            "successfully_parsed": successfully_parsed,
            "eligible_count": len(ranked),
            "rejected_count": len(rejected),
            "failed_count": len(failures),
            "duplicate_count": len(duplicate_files),
            "llm_fallback_count": len(llm_fallbacks),
        },
        "llm_fallbacks": llm_fallbacks,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output