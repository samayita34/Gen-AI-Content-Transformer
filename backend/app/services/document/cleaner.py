import re
import unicodedata
from typing import List
from app.services.document.models import ParsedDocument, DocumentElement


class TextCleaner:
    """
    Deterministic text cleaning pipeline for preserving semantic meaning
    while stripping extraction artifacts without LLM rewriting.
    """

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Applies NFKC Unicode normalization to eliminate strange glyphs and ligatures."""
        if not text:
            return ""
        # NFKC normalizes compatibility characters (e.g., ﬁ -> fi)
        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def remove_control_characters(text: str) -> str:
        """Strips non-printable control characters except standard whitespace and newlines."""
        if not text:
            return ""
        # Remove form feed (\x0c), null bytes (\x00), vertical tabs, etc.
        text = text.replace("\x0c", "\n").replace("\x00", "")
        # Remove other unprintable control characters
        return "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch == "\r" or unicodedata.category(ch)[0] != "C")

    @staticmethod
    def fix_hyphenated_line_breaks(text: str) -> str:
        """
        Repairs words broken across lines by hyphenation in PDFs:
        e.g., 'transfor-\\nmation' -> 'transformation'
        """
        # Match lowercase-to-lowercase hyphenation across newline
        return re.sub(r"(\b[a-z]+)-\n([a-z]+\b)", r"\1\2", text)

    @staticmethod
    def compact_whitespace(text: str) -> str:
        """
        Compacts multiple horizontal spaces into a single space,
        and limits consecutive newlines to at most 2.
        """
        # Replace non-breaking spaces with standard space
        text = text.replace("\u00a0", " ")
        # Compact consecutive tabs/spaces (horizontal whitespace)
        text = re.sub(r"[ \t]+", " ", text)
        # Compact 3+ newlines into 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Executes full cleaning pipeline on a raw text string."""
        if not text:
            return ""
        text = cls.normalize_unicode(text)
        text = cls.remove_control_characters(text)
        text = cls.fix_hyphenated_line_breaks(text)
        text = cls.compact_whitespace(text)
        return text

    @classmethod
    def clean_parsed_document(cls, doc: ParsedDocument) -> ParsedDocument:
        """Cleans all extracted elements in a parsed document in place."""
        cleaned_elements: List[DocumentElement] = []

        for elem in doc.elements:
            cleaned_text = cls.clean_text(elem.text)
            if cleaned_text:
                elem.text = cleaned_text
                cleaned_elements.append(elem)

        cleaned_raw = cls.clean_text(doc.raw_text)

        return ParsedDocument(
            elements=cleaned_elements,
            raw_text=cleaned_raw,
            page_count=doc.page_count,
            metadata=doc.metadata,
        )


cleaner = TextCleaner()
