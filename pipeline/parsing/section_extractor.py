"""
Unified section extractor that works with multiple input formats.

Supports:
  - GROBID TEI XML (via GrobidParser)
  - PMC NXML full-text (via pubmed_parser)
  - Plain text with heuristic section detection
  - Pre-parsed PubMed metadata dicts

Normalises everything into a common ``PaperSections`` object consumed
by the extraction agents.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .grobid_parser import GrobidParser
from .pubmed_parser import (
    extract_pmc_sections,
    fetch_pmc_fulltext,
    fetch_pubmed_metadata,
)

logger = logging.getLogger(__name__)


@dataclass
class PaperSections:
    """Normalised representation of a parsed paper."""

    title: str = ""
    abstract: str = ""
    methods: str = ""
    results: str = ""
    introduction: str = ""
    discussion: str = ""
    full_text: str = ""
    # Raw section list for agents that want heading-level granularity
    sections: List[Dict[str, str]] = field(default_factory=list)
    # Metadata carried through from the source
    metadata: Dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    def all_text(self) -> str:
        """Concatenate all meaningful text (for whole-document agents)."""
        parts = [self.title, self.abstract, self.methods, self.results,
                 self.introduction, self.discussion]
        return "\n\n".join(p for p in parts if p)

    def methods_or_fallback(self) -> str:
        """Return methods text, falling back to full_text if unavailable."""
        if self.methods and len(self.methods) > 100:
            return self.methods
        return self.full_text or self.all_text()

    @property
    def has_methods(self) -> bool:
        return bool(self.methods) and len(self.methods) > 100

    @property
    def tag_source(self) -> str:
        return "methods" if self.has_methods else "title_abstract"


def from_sections_list(sections: List[Dict[str, str]],
                       metadata: Dict = None) -> PaperSections:
    """Build a PaperSections from a list of {heading, text, type} dicts."""
    ps = PaperSections(sections=sections, metadata=metadata or {})

    methods_parts: List[str] = []
    results_parts: List[str] = []
    intro_parts: List[str] = []
    discussion_parts: List[str] = []
    all_parts: List[str] = []

    for sec in sections:
        stype = sec.get("type", "other")
        text = sec.get("text", "")
        if not text:
            continue
        all_parts.append(text)

        if stype == "abstract":
            ps.abstract = text
        elif stype == "methods":
            methods_parts.append(text)
        elif stype == "results":
            results_parts.append(text)
        elif stype == "introduction":
            intro_parts.append(text)
        elif stype == "discussion":
            discussion_parts.append(text)

    ps.methods = " ".join(methods_parts)
    ps.results = " ".join(results_parts)
    ps.introduction = " ".join(intro_parts)
    ps.discussion = " ".join(discussion_parts)
    ps.full_text = " ".join(all_parts)

    # Title from metadata
    if metadata:
        ps.title = metadata.get("title", "")
        if not ps.abstract:
            ps.abstract = metadata.get("abstract", "")

    return ps


def from_pubmed_dict(paper: Dict) -> PaperSections:
    """Build PaperSections from a scraper-style dict (DB row or JSON record)."""
    return PaperSections(
        title=paper.get("title", "") or "",
        abstract=paper.get("abstract", "") or "",
        methods=paper.get("methods", "") or "",
        full_text=paper.get("full_text", "") or "",
        metadata=paper,
    )


def from_pdf(pdf_path: str, grobid_url: str = "http://localhost:8070") -> PaperSections:
    """Parse a PDF via GROBID into PaperSections."""
    parser = GrobidParser(grobid_url)
    if not parser.is_available():
        logger.warning("GROBID not available at %s", grobid_url)
        return PaperSections()

    tei = parser.parse_pdf_raw(pdf_path)
    if not tei:
        return PaperSections()

    metadata = parser.extract_metadata(tei)
    sections = parser.parse_pdf(pdf_path)
    return from_sections_list(sections, metadata)


def from_pmc(pmc_id: str) -> PaperSections:
    """Fetch and parse a PMC full-text article."""
    xml_text = fetch_pmc_fulltext(pmc_id)
    if not xml_text:
        return PaperSections()
    sections = extract_pmc_sections(xml_text)
    return from_sections_list(sections)
