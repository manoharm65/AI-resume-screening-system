import pytest

from src.models import Candidate, Project
from src.scorer import score_candidate


def test_score_is_explainable_and_capped() -> None:
    candidate = Candidate(
        source_file="candidate.pdf",
        skills=["Python", "FastAPI"],
        projects=[
            Project(
                name="Knowledge assistant",
                description="Built a RAG workflow with retrieval, embeddings, vector search, tool calling, state, and evaluation.",
                technologies=["Python", "PostgreSQL", "Docker"],
            )
        ],
    )

    result = score_candidate(candidate, github_points=20, github_evidence=["recent activity"])

    assert result.total <= 100
    assert result.categories["github_activity"] == 10
    assert result.evidence["ai_agentic_rag_depth"]
    assert result.penalties == []


def test_thin_llm_wrapper_penalty_is_visible() -> None:
    candidate = Candidate(
        source_file="candidate.pdf",
        skills=["Python"],
        projects=[Project(description="Built a chatbot using the OpenAI API.")],
    )

    result = score_candidate(candidate)

    assert result.penalties[0].points == -10
    assert "thin LLM API wrapper" in result.penalties[0].reason


def test_ineligible_candidate_cannot_be_scored() -> None:
    candidate = Candidate(source_file="candidate.pdf", skills=["JavaScript"])

    with pytest.raises(ValueError, match="Only eligible"):
        score_candidate(candidate)