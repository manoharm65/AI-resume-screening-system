from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
RESULTS = OUTPUT / "results.json"


def styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="TitleCenter", parent=base["Title"], alignment=TA_CENTER, fontSize=22, leading=28, spaceAfter=18))
    base.add(ParagraphStyle(name="Subtitle", parent=base["Normal"], alignment=TA_CENTER, fontSize=11, textColor=colors.HexColor("#4B5563"), spaceAfter=24))
    base.add(ParagraphStyle(name="Section", parent=base["Heading1"], fontSize=16, leading=20, textColor=colors.HexColor("#123B5D"), spaceBefore=14, spaceAfter=8))
    base.add(ParagraphStyle(name="Subsection", parent=base["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#256D85"), spaceBefore=10, spaceAfter=5))
    base.add(ParagraphStyle(name="BodySmall", parent=base["BodyText"], fontSize=9.5, leading=13, spaceAfter=6))
    base.add(ParagraphStyle(name="CodeBlock", parent=base["Code"], fontSize=8.5, leading=11, backColor=colors.HexColor("#F3F4F6"), borderPadding=6, spaceAfter=6))
    return base


def p(text: str, style) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def bullet(text: str, style) -> Paragraph:
    return Paragraph("&#8226; " + escape(text), style)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(0.65 * inch, 0.4 * inch, "AI Resume Screening and Ranking System")
    canvas.drawRightString(7.85 * inch, 0.4 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_project_report(data: dict, path: Path) -> None:
    s = styles()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.65 * inch, bottomMargin=0.65 * inch)
    summary = data["summary"]
    ranked = data["ranked_candidates"]
    rejected = data.get("rejected_candidates", [])
    example = ranked[0] if ranked else (rejected[0] if rejected else {})
    story = [
        p("AI Resume Screening & Ranking System", s["TitleCenter"]),
        p("Formal project approach and achieved results", s["Subtitle"]),
        p("Submitted By", s["Section"]),
    ]
    student_rows = [
        [p("Name", s["BodySmall"]), p("Manohar", s["BodySmall"])],
        [p("Branch", s["BodySmall"]), p("CSE", s["BodySmall"])],
        [p("USN", s["BodySmall"]), p("1RV22CS108", s["BodySmall"])],
        [p("College", s["BodySmall"]), p("R V College of Engineering", s["BodySmall"])],
    ]
    student_table = Table(student_rows, colWidths=[1.2 * inch, 4.8 * inch])
    student_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#DCEAF2")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([student_table, Spacer(1, 12),
        p("Executive Summary", s["Section"]),
        p("This project implements a batch resume screening pipeline for an SDE internship requiring Python fundamentals and practical AI or agentic-system experience. The system processes resumes, extracts structured candidate information, applies hard eligibility rules before ranking, calculates an explainable score, optionally enriches public GitHub data, and produces machine-readable JSON output.", s["BodySmall"]),
        p("Achieved Results", s["Section"]),
    ])
    result_rows = [[p("Metric", s["BodySmall"]), p("Result", s["BodySmall"])]]
    for key, label in [("total_files", "Total files"), ("successfully_parsed", "Successfully parsed"), ("eligible_count", "Eligible candidates"), ("rejected_count", "Rejected candidates"), ("failed_count", "Failed resumes"), ("duplicate_count", "Duplicate files")]:
        result_rows.append([p(label, s["BodySmall"]), p(str(summary.get(key, 0)), s["BodySmall"])])
    table = Table(result_rows, colWidths=[3.6 * inch, 2.4 * inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF2")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7)]))
    story.append(table)
    story += [
        p("System Approach", s["Section"]),
        bullet("Discover PDF, DOCX, and TXT files recursively without modifying the input dataset.", s["BodySmall"]),
        bullet("Extract and normalize text, including clickable PDF hyperlink annotations for GitHub profiles.", s["BodySmall"]),
        bullet("Build conservative structured candidate records with Pydantic models.", s["BodySmall"]),
        bullet("Apply the deterministic Python plus meaningful AI hard filter before scoring.", s["BodySmall"]),
        bullet("Score only eligible candidates using a transparent 100-point model.", s["BodySmall"]),
        bullet("Enrich GitHub activity when enabled, with caching and graceful API failure handling.", s["BodySmall"]),
        bullet("Write ranked candidates, rejected candidates, failures, duplicates, evidence, and summaries to JSON.", s["BodySmall"]),
        p("Eligibility Logic", s["Section"]),
        p("A candidate is eligible only when Python evidence and meaningful AI, LLM, RAG, machine-learning, or agentic implementation evidence are both present. Ranking cannot override a failed eligibility condition.", s["BodySmall"]),
        p("Scoring Model", s["Section"]),
    ]
    score_rows = [[p("Category", s["BodySmall"]), p("Maximum", s["BodySmall"]), p("Evidence considered", s["BodySmall"])], [p("AI / Agentic / RAG depth", s["BodySmall"]), p("40", s["BodySmall"]), p("Retrieval, embeddings, agents, tools, state, orchestration, evaluation, business logic", s["BodySmall"])], [p("Python and backend", s["BodySmall"]), p("30", s["BodySmall"]), p("Python, FastAPI, backend APIs, PostgreSQL, Redis, async, architecture", s["BodySmall"])], [p("Cloud / deployment / full stack", s["BodySmall"]), p("15", s["BodySmall"]), p("Cloud, Docker, deployment, CI/CD, React, Next.js", s["BodySmall"])], [p("GitHub activity", s["BodySmall"]), p("10", s["BodySmall"]), p("Recent public events and relevant repositories", s["BodySmall"])], [p("Engineering depth", s["BodySmall"]), p("5", s["BodySmall"]), p("Tests, caching, queues, observability, concurrency, failures", s["BodySmall"])]]
    score_table = Table(score_rows, colWidths=[1.8 * inch, 0.7 * inch, 3.5 * inch])
    score_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF2")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(score_table)
    story += [p("Top Ranked Candidates", s["Section"])]
    top_rows = [[p("Rank", s["BodySmall"]), p("Candidate", s["BodySmall"]), p("Score", s["BodySmall"]), p("Primary signal", s["BodySmall"])]]
    for row in ranked[:10]:
        top_rows.append([p(str(row.get("ranking_number", row.get("rank", ""))), s["BodySmall"]), p(str(row.get("candidate_name") or "Unknown"), s["BodySmall"]), p(str(row.get("total_score", row.get("score", 0))), s["BodySmall"]), p((row.get("strength") or "")[:90], s["BodySmall"])])
    top_table = Table(top_rows, colWidths=[0.55 * inch, 1.6 * inch, 0.65 * inch, 3.2 * inch])
    top_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF2")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(top_table)
    story += [p("Example Resume Output", s["Section"]), p("Each resume produces a structured record with identity, eligibility, matched skills, project summary, GitHub status, score details, and ranking when eligible.", s["BodySmall"])]
    example_rows = [
        [p("Field", s["BodySmall"]), p("Example value", s["BodySmall"])],
        [p("PDF / source file", s["BodySmall"]), p(Path(str(example.get("source_file", ""))).name, s["BodySmall"])],
        [p("Candidate", s["BodySmall"]), p(str(example.get("candidate_name", "Unknown")), s["BodySmall"])],
        [p("Eligibility", s["BodySmall"]), p(str(example.get("eligible", False)), s["BodySmall"])],
        [p("Ranking number", s["BodySmall"]), p(str(example.get("ranking_number", example.get("rank", "Not ranked"))), s["BodySmall"])],
        [p("Total score", s["BodySmall"]), p(str(example.get("total_score", example.get("score", "Not scored"))), s["BodySmall"])],
        [p("Matched skills", s["BodySmall"]), p(", ".join(example.get("matched_skills", [])[:12]), s["BodySmall"])],
        [p("Strengths", s["BodySmall"]), p("; ".join(example.get("strengths", [])), s["BodySmall"])],
        [p("Concerns", s["BodySmall"]), p("; ".join(example.get("concerns", [])) or "None recorded", s["BodySmall"])],
    ]
    example_table = Table(example_rows, colWidths=[1.45 * inch, 4.55 * inch])
    example_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF2")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(example_table)
    story += [p("Rejected Candidates", s["Section"]), p("Rejected resumes remain in the final JSON and are not ranked. The following table lists every rejected person and the exact eligibility reason.", s["BodySmall"])]
    rejected_rows = [[p("PDF", s["BodySmall"]), p("Candidate", s["BodySmall"]), p("Rejection reason", s["BodySmall"])]]
    for row in rejected:
        rejected_rows.append([p(Path(str(row.get("source_file", ""))).name, s["BodySmall"]), p(str(row.get("candidate_name") or "Unknown"), s["BodySmall"]), p("; ".join(row.get("rejection_reasons", [])), s["BodySmall"])])
    rejected_table = Table(rejected_rows, colWidths=[1.15 * inch, 1.65 * inch, 3.2 * inch], repeatRows=1)
    rejected_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FDE2E2")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(rejected_table)
    story += [p("Reliability and Explainability", s["Section"]), bullet("Each resume is isolated so malformed files do not stop the batch.", s["BodySmall"]), bullet("Rejection reasons identify the exact failed rule.", s["BodySmall"]), bullet("Score evidence and visible penalties support interview discussion.", s["BodySmall"]), bullet("The generated JSON preserves detailed machine-readable output for review.", s["BodySmall"])]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def build_technical_guide(path: Path) -> None:
    s = styles()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.65 * inch, bottomMargin=0.65 * inch)
    story = [p("Technical Reference Guide", s["TitleCenter"]), p("How to explain the main files, functions, and data flow", s["Subtitle"]), p("How to Present the Project", s["Section"]), p("Explain the system as a sequence: discover files, extract text, build a Candidate model, apply eligibility, score eligible candidates, enrich GitHub, sort by score, and write JSON. Emphasize that eligibility is deterministic and happens before ranking.", s["BodySmall"]), p("Main Files", s["Section"])]
    files = [
        ("main.py", "CLI entry point. Parses --input, --output, and --no-github arguments, creates the GitHub client, runs the pipeline, and prints a concise summary."),
        ("src/parser.py", "Format-aware ingestion. discover_resume_files finds PDF, DOCX, and TXT files. extract_pdf_text uses pypdf and reads PDF link annotations. extract_docx_text reads paragraphs from DOCX XML. extract_text_resume handles UTF-8 TXT. extract_resume_text dispatches by extension."),
        ("src/models.py", "Pydantic contracts. Candidate stores extracted resume data; Project stores project details; EligibilityResult stores hard-filter evidence; ScoreResult stores category scores and penalties; GitHubResult stores enrichment status."),
        ("src/utils.py", "Conservative extraction helpers. normalize and section helpers clean layout artifacts. _skills detects explicit and canonical technologies. _github_url selects profile URLs. extract_candidate builds the structured Candidate without inventing missing facts."),
        ("src/eligibility.py", "Owns the hard filter. detect_python_evidence and detect_ai_evidence collect evidence. evaluate_eligibility returns eligible=True only when both evidence groups exist."),
        ("src/scorer.py", "Owns explainable ranking. It calculates the five weighted categories, caps each category, applies visible shallow-wrapper penalties, and raises an error if an ineligible candidate is passed."),
        ("src/github.py", "Optional public enrichment. Extracts username, caches per username, calls profile/repository/event endpoints, estimates recent activity and relevance, and converts failures into structured statuses."),
        ("src/llm.py", "Provider boundary. An optional structured extractor can be injected. If it fails, deterministic extraction is used and the failure is recorded."),
        ("src/pipeline.py", "Orchestrator. Hashes files for duplicates, parses each file independently, extracts candidates, evaluates eligibility, enriches eligible candidates, scores them, assigns rank and ranking_number, and writes results.json."),
        ("tests/", "Focused tests cover parser formats, hyperlink extraction, name handling, eligibility, scoring, GitHub caching/failures, and batch failure isolation."),
    ]
    rows = [[p("File", s["BodySmall"]), p("Purpose and explanation", s["BodySmall"])]] + [[p(name, s["BodySmall"]), p(description, s["BodySmall"])] for name, description in files]
    table = Table(rows, colWidths=[1.35 * inch, 4.95 * inch], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF2")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(table)
    story += [p("Important Data Structures", s["Section"]), p("Candidate", s["Subsection"]), p("Represents one resume after extraction: name, contact data, skills, projects, experience, Python evidence, AI evidence, engineering evidence, and GitHub URL.", s["BodySmall"]), p("EligibilityResult", s["Subsection"]), p("Represents the hard decision and the exact evidence or rejection reasons. This object is created before any score is calculated.", s["BodySmall"]), p("ScoreResult", s["Subsection"]), p("Represents the total score, category breakdown, evidence lists, and visible penalties. The maximum is 100.", s["BodySmall"]), p("GitHubResult", s["Subsection"]), p("Represents profile URL, username, status, public activity summary, score, and error details. GitHub failure never rejects a candidate.", s["BodySmall"]), p("End-to-End Explanation", s["Section"])]
    steps = ["1. discover_resume_files recursively finds supported files.", "2. extract_resume_text selects the correct parser and normalizes text.", "3. extract_candidate creates a Pydantic Candidate using evidence only.", "4. evaluate_eligibility applies Python plus AI hard requirements.", "5. GitHub enrichment runs only for eligible candidates and is cached.", "6. score_candidate calculates the explainable 100-point score.", "7. pipeline sorts eligible candidates descending and assigns rank/ranking_number.", "8. JSON output includes eligible, rejected, failed, duplicate, evidence, and batch summary sections."]
    story.extend([bullet(step, s["BodySmall"]) for step in steps])
    story += [p("Interview Talking Points", s["Section"]), bullet("Why deterministic eligibility? It is predictable, testable, and prevents ranking from overriding minimum requirements.", s["BodySmall"]), bullet("Why a fallback extractor? The batch remains useful without an LLM key and continues when an optional provider fails.", s["BodySmall"]), bullet("Why cache GitHub? It avoids repeated network calls for the same public profile.", s["BodySmall"]), bullet("Why visible penalties? They make shallow AI projects explainable instead of silently reducing scores.", s["BodySmall"]), bullet("Why isolate files? One malformed resume must not terminate processing for the other candidates.", s["BodySmall"])]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    OUTPUT.mkdir(exist_ok=True)
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    build_project_report(data, OUTPUT / "project_approach_and_results.pdf")
    build_technical_guide(OUTPUT / "technical_reference_guide.pdf")
    print("Generated project_approach_and_results.pdf")
    print("Generated technical_reference_guide.pdf")
