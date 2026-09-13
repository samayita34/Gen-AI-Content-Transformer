import re
import unicodedata
from typing import List, Optional
from app.services.verification.models import AtomicClaim


# Regex for stripping markdown formatting artifacts
MARKDOWN_BOLD_ITALIC = re.compile(r"(\*\*|__|\*|_|~~|`|#+|>+)")
HTML_TAGS = re.compile(r"<[^>]+>")
LIST_PREFIXES = re.compile(r"^[\s*\-•\d.)\]>]+", re.MULTILINE)
WHITESPACE_COLLAPSE = re.compile(r"\s+")
TRAILING_PUNCTUATION_CLEAN = re.compile(r"[\s,;:]+$")
MULTIPLE_PERIODS = re.compile(r"\.{2,}")

# Smart quotation and dash maps
QUOTE_DASH_MAP = {
    "“": '"',
    "”": '"',
    "„": '"',
    "‘": "'",
    "’": "'",
    "‚": "'",
    "—": " - ",
    "–": " - ",
    "−": " - ",
    "\u00a0": " ",
    "\u200b": "",
}

# Compound conjunction splitting regex (splits independent clauses joined by coordinating conjunctions)
COMPOUND_SPLIT_REGEX = re.compile(
    r"\s*;\s*|\s*,\s*(?:and|furthermore|additionally|moreover|consequently|whereas|meanwhile)\s+",
    re.IGNORECASE,
)


class ClaimNormalizer:
    """
    Deterministic Claim Normalizer for source-grounded verification.
    
    Transforms raw extracted claims into standardized retrieval queries without
    altering factual assertions, preserving all numbers, dates, names, units, and metrics.
    Keeps both the original claim text and the normalized claim text.
    """

    @classmethod
    def normalize_claim_text(cls, text: str) -> str:
        """
        Applies deterministic text normalization to a single claim string.
        Preserves numbers, dates, units, named entities, and factual assertions.
        """
        if not text or not text.strip():
            return ""

        # 1. Unicode NFKC Normalization (eliminates weird ligatures/glyphs)
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Control character removal (keep standard printables)
        normalized = "".join(
            ch for ch in normalized
            if ch in ("\n", "\t", " ") or unicodedata.category(ch)[0] != "C"
        )

        # 3. Replace smart quotes, typographic dashes, non-breaking spaces
        for k, v in QUOTE_DASH_MAP.items():
            normalized = normalized.replace(k, v)

        # 4. Remove HTML tags if any
        normalized = HTML_TAGS.sub(" ", normalized)

        # 5. Remove list prefixes (e.g. '1. ', '- ', '• ', 'a) ')
        normalized = LIST_PREFIXES.sub("", normalized)

        # 6. Remove markdown formatting markers (bold, italic, backticks, hashes)
        normalized = MARKDOWN_BOLD_ITALIC.sub("", normalized)

        # 7. Collapse whitespace
        normalized = WHITESPACE_COLLAPSE.sub(" ", normalized).strip()

        # 8. Clean trailing dangling punctuation (e.g. trailing comma, semicolon, colon)
        normalized = TRAILING_PUNCTUATION_CLEAN.sub("", normalized).strip()

        # 9. Clean multi-period ellipses into a single period if at end
        normalized = MULTIPLE_PERIODS.sub(".", normalized)

        return normalized

    @classmethod
    def split_compound_claim(cls, text: str) -> List[str]:
        """
        Splits compound assertions into independent propositions where practical.
        Returns original text in a single-element list if splitting would create incomplete fragments.
        """
        clean_text = cls.normalize_claim_text(text)
        if not clean_text:
            return []

        parts = COMPOUND_SPLIT_REGEX.split(clean_text)
        valid_propositions: List[str] = []

        for p in parts:
            p_clean = cls.normalize_claim_text(p)
            # Retain split proposition only if long enough and contains at least 3 words
            if len(p_clean) >= 15 and len(p_clean.split()) >= 3:
                valid_propositions.append(p_clean)

        # If splitting failed to yield multiple viable propositions, return original cleaned statement
        if len(valid_propositions) > 1:
            return valid_propositions
        return [clean_text]

    @classmethod
    def normalize_claim(cls, claim: AtomicClaim) -> AtomicClaim:
        """
        Normalizes an AtomicClaim instance in-place and returns it.
        Preserves original `claim.text` while updating `claim.normalized_text`.
        """
        normalized_str = cls.normalize_claim_text(claim.text or claim.statement)
        claim.normalized_text = normalized_str
        claim.normalized_statement = normalized_str
        return claim

    @classmethod
    def normalize_claims(cls, claims: List[AtomicClaim]) -> List[AtomicClaim]:
        """
        Normalizes a batch of atomic claims.
        """
        return [cls.normalize_claim(c) for c in claims]
