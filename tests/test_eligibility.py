from src.eligibility import evaluate_eligibility
from src.models import Candidate, Project


def candidate(**overrides: object) -> Candidate:
    values = {"source_file": "candidate.pdf", **overrides}
    return Candidate.model_validate(values)


def test_python_and_implemented_rag_project_are_eligible() -> None:
    result = evaluate_eligibility(
        candidate(
            skills=["Python", "FastAPI"],
            projects=[
                Project(
                    name="Document assistant",
                    description="Built a RAG pipeline with embeddings and vector retrieval.",
                    technologies=["Python"],
                )
            ],
        )
    )

    assert result.eligible is True
    assert result.rejection_reasons == []
    assert result.python_evidence
    assert result.ai_evidence


def test_python_without_ai_evidence_is_rejected() -> None:
    result = evaluate_eligibility(candidate(skills=["Python", "Django"]))

    assert result.eligible is False
    assert result.rejection_reasons == ["No meaningful AI, LLM, RAG, or agentic evidence"]


def test_ai_skill_without_implementation_is_not_enough() -> None:
    result = evaluate_eligibility(candidate(skills=["Python", "LangChain", "OpenAI"]))

    assert result.eligible is False
    assert result.rejection_reasons == ["No meaningful AI, LLM, RAG, or agentic evidence"]


def test_ai_project_without_python_is_rejected() -> None:
    result = evaluate_eligibility(
        candidate(
            skills=["JavaScript"],
            projects=[Project(description="Built an OpenAI-powered document retrieval assistant.")],
        )
    )

    assert result.eligible is False
    assert result.rejection_reasons == ["No evidence of Python implementation"]