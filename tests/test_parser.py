from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.parser import (
    ResumeParseError,
    discover_pdf_files,
    discover_resume_files,
    extract_docx_text,
    extract_pdf_text,
    extract_text_resume,
    normalize_text,
)


def test_discover_pdf_files_recurses_and_ignores_other_extensions(tmp_path: Path) -> None:
    (tmp_path / "resume.PDF").touch()
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "second.pdf").touch()
    (nested / "notes.txt").touch()

    assert discover_pdf_files(tmp_path) == [tmp_path / "nested" / "second.pdf", tmp_path / "resume.PDF"]


def test_discover_resume_files_includes_docx_and_txt(tmp_path: Path) -> None:
    (tmp_path / "resume.pdf").touch()
    (tmp_path / "resume.docx").touch()
    (tmp_path / "resume.txt").touch()
    (tmp_path / "notes.md").touch()

    assert [path.suffix for path in discover_resume_files(tmp_path)] == [".docx", ".pdf", ".txt"]


def test_normalize_text_preserves_lines_and_collapses_layout_spaces() -> None:
    raw_text = " Name\u00a0  Here  \n\nSkills:\tPython   SQL "

    assert normalize_text(raw_text) == "Name Here\nSkills: Python SQL"


def test_extract_pdf_text_returns_normalized_result(tmp_path: Path) -> None:
    pdf_path = tmp_path / "candidate.pdf"
    pdf_path.touch()
    page = Mock()
    page.extract_text.return_value = " Candidate  Name \n Python "
    page.get.return_value = []
    reader = Mock(pages=[page])

    with patch("src.parser.PdfReader", return_value=reader):
        result = extract_pdf_text(pdf_path)

    assert result.file_path == pdf_path
    assert result.page_count == 1
    assert result.text == "Candidate Name\nPython"
    assert result.links == []


def test_extract_pdf_text_collects_hyperlinks(tmp_path: Path) -> None:
    pdf_path = tmp_path / "candidate.pdf"
    pdf_path.touch()
    page = Mock()
    page.extract_text.return_value = "Candidate Name\nGitHub"
    annotation = Mock()
    annotation.get_object.return_value = {"/A": {"/URI": "https://github.com/example"}}
    page.get.return_value = [annotation]
    reader = Mock(pages=[page])

    with patch("src.parser.PdfReader", return_value=reader):
        result = extract_pdf_text(pdf_path)

    assert result.links == ["https://github.com/example"]


def test_extract_pdf_text_rejects_empty_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.touch()
    page = Mock()
    page.extract_text.return_value = ""
    reader = Mock(pages=[page])

    with patch("src.parser.PdfReader", return_value=reader), pytest.raises(
        ResumeParseError, match="no extractable text"
    ):
        extract_pdf_text(pdf_path)


def test_extract_pdf_text_wraps_reader_failures(tmp_path: Path) -> None:
    pdf_path = tmp_path / "broken.pdf"
    pdf_path.touch()

    with patch("src.parser.PdfReader", side_effect=ValueError("bad file")), pytest.raises(
        ResumeParseError, match="Unable to read PDF"
    ):
        extract_pdf_text(pdf_path)


def test_extract_text_resume_reads_txt(tmp_path: Path) -> None:
    file_path = tmp_path / "resume.txt"
    file_path.write_text("Asha Rao\nPython\n", encoding="utf-8")

    result = extract_text_resume(file_path)

    assert result.text == "Asha Rao\nPython"


def test_extract_docx_text_reads_paragraphs(tmp_path: Path) -> None:
    from zipfile import ZipFile

    file_path = tmp_path / "resume.docx"
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:r><w:t>Asha Rao</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Python</w:t></w:r></w:p></w:body></w:document>'
    )
    with ZipFile(file_path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    result = extract_docx_text(file_path)

    assert result.text == "Asha Rao\nPython"