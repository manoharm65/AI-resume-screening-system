from src.utils import extract_candidate


def test_extract_candidate_keeps_missing_values_empty() -> None:
    candidate = extract_candidate(
        "Asha Rao\n"
        "asha@example.com\n"
        "Skills: Python, FastAPI, PostgreSQL\n"
        "Projects\n"
        "Document assistant\n"
        "Built a RAG pipeline with vector retrieval.\n"
        "Experience\n"
        "Backend Intern - built REST APIs\n"
        "GitHub\n",
        "candidate.pdf",
        links=[
            "https://github.com/asha-rao/project",
            "https://github.com/asha-rao",
        ],
    )

    assert candidate.candidate_name == "Asha Rao"
    assert candidate.email == "asha@example.com"
    assert candidate.github_url == "https://github.com/asha-rao"
    assert candidate.skills == ["Python", "FastAPI", "PostgreSQL", "RAG"]
    assert candidate.projects[0].description == "Document assistant Built a RAG pipeline with vector retrieval."
    assert candidate.phone is None


def test_extract_candidate_adds_canonical_skills_from_project_evidence() -> None:
    candidate = extract_candidate(
        "Asha Rao\n"
        "Projects\n"
        "Built a LangGraph RAG service with FastAPI, PostgreSQL, Redis and Docker.\n",
        "candidate.pdf",
    )

    assert candidate.skills == [
        "FastAPI",
        "PostgreSQL",
        "Redis",
        "Docker",
        "LangGraph",
        "RAG",
    ]


def test_extract_candidate_does_not_invent_contact_or_project_data() -> None:
    candidate = extract_candidate("Frontend Developer\nSkills: React, JavaScript", "candidate.pdf")

    assert candidate.email is None
    assert candidate.github_url is None
    assert candidate.projects == []
    assert candidate.experience == []


def test_extract_candidate_skips_numeric_page_header() -> None:
    candidate = extract_candidate(
        "1\nANJALI PATIL\nanjalipatil1220@gmail.com — +91 9380186313\nSUMMARY\nJava Backend Developer",
        "candidate_42.pdf",
    )

    assert candidate.candidate_name == "ANJALI PATIL"