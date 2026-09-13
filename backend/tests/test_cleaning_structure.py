import pytest
from app.services.document.cleaner import TextCleaner
from app.services.document.structure import StructureDetector
from app.services.document.models import ParsedDocument, DocumentElement, ElementType


def test_unicode_normalization():
    # Test ligature normalization (e.g. \ufb01 = 'fi')
    ligature_text = "The scienti\ufb01c platform"
    cleaned = TextCleaner.normalize_unicode(ligature_text)
    assert cleaned == "The scientific platform"


def test_control_character_removal():
    text_with_artifacts = "Start of text\x0cPage break\x00Null character"
    cleaned = TextCleaner.remove_control_characters(text_with_artifacts)
    assert "\x0c" not in cleaned
    assert "\x00" not in cleaned
    assert "Start of text\nPage breakNull character" == cleaned


def test_hyphenated_line_break_repair():
    broken_text = "Automated transfor-\nmation of documents."
    fixed = TextCleaner.fix_hyphenated_line_breaks(broken_text)
    assert fixed == "Automated transformation of documents."


def test_whitespace_compaction():
    messy_text = "Word1    Word2\u00a0Word3\n\n\n\nWord4"
    cleaned = TextCleaner.compact_whitespace(messy_text)
    assert cleaned == "Word1 Word2 Word3\n\nWord4"


def test_structure_heading_detection():
    # Markdown heading
    md = StructureDetector.detect_heading("## Executive Summary")
    assert md is not None
    assert md[0] == 2
    assert md[1] == "Executive Summary"

    # Numbered heading
    num = StructureDetector.detect_heading("1.2 System Architecture")
    assert num is not None
    assert num[0] == 2
    assert "1.2 System Architecture" in num[1]

    # All caps short heading
    caps = StructureDetector.detect_heading("CORE METHODOLOGY")
    assert caps is not None
    assert caps[0] == 1
    assert caps[1] == "CORE METHODOLOGY"

    # Regular sentence should NOT be a heading
    regular = StructureDetector.detect_heading("This is a normal body paragraph that contains standard text.")
    assert regular is None


def test_structure_enrichment():
    elements = [
        DocumentElement(text="1. Introduction", page_number=1),
        DocumentElement(text="This is introductory body text.", page_number=1),
        DocumentElement(text="- Key feature item", page_number=1),
        DocumentElement(text="2. Evaluation", page_number=2),
        DocumentElement(text="Evaluation metrics details.", page_number=2),
    ]
    parsed = ParsedDocument(elements=elements, page_count=2)
    enriched = StructureDetector.enrich_document_structure(parsed)

    assert enriched.elements[0].element_type == ElementType.HEADING
    assert enriched.elements[0].section_title == "1. Introduction"

    assert enriched.elements[1].element_type == ElementType.PARAGRAPH
    assert enriched.elements[1].section_title == "1. Introduction"

    assert enriched.elements[2].element_type == ElementType.LIST_ITEM
    assert enriched.elements[2].section_title == "1. Introduction"

    assert enriched.elements[3].element_type == ElementType.HEADING
    assert enriched.elements[3].section_title == "2. Evaluation"

    assert enriched.elements[4].element_type == ElementType.PARAGRAPH
    assert enriched.elements[4].section_title == "2. Evaluation"
