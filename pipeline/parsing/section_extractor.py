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
from .scihub_fetcher import fetch_fulltext_via_scihub

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
    # Figure captions — rich source of equipment/technique info
    figures: str = ""
    # Data/Code availability statements — contain repository links
    data_availability: str = ""
    # Raw section list for agents that want heading-level granularity
    sections: List[Dict[str, str]] = field(default_factory=list)
    # Metadata carried through from the source
    metadata: Dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    def all_text(self) -> str:
        """Concatenate all meaningful text (for whole-document agents)."""
        parts = [self.title, self.abstract, self.methods, self.results,
                 self.introduction, self.discussion, self.figures,
                 self.data_availability]
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
    figure_parts: List[str] = []
    data_avail_parts: List[str] = []
    all_parts: List[str] = []

    for sec in sections:
        stype = sec.get("type", "other")
        text = sec.get("text", "")
        if not text:
            continue
        # Skip references/bibliography sections to avoid tagging
        # entities mentioned in citation titles and author names
        if stype in ("references", "bibliography"):
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
        elif stype == "figures":
            figure_parts.append(text)
        elif stype == "data_availability":
            data_avail_parts.append(text)

    ps.methods = " ".join(methods_parts)
    ps.results = " ".join(results_parts)
    ps.introduction = " ".join(intro_parts)
    ps.discussion = " ".join(discussion_parts)
    ps.figures = " ".join(figure_parts)
    ps.data_availability = " ".join(data_avail_parts)
    ps.full_text = " ".join(all_parts)

    # Title from metadata
    if metadata:
        ps.title = metadata.get("title", "")
        if not ps.abstract:
            ps.abstract = metadata.get("abstract", "")

    return ps


def from_pubmed_dict(paper: Dict) -> PaperSections:
    """Build PaperSections from a scraper-style dict (DB row or JSON record).

    If the paper has a DOI but no full text, attempts to retrieve it
    via SciHub as a last-resort fallback (for tag extraction only —
    the SciHub text is never stored or displayed).
    """
    full_text = paper.get("full_text", "") or ""
    figures = ""
    data_availability = ""

    # SciHub fallback: if we have a DOI but no full text, try to fetch it
    if not full_text and paper.get("doi"):
        scihub_text = fetch_fulltext_via_scihub(paper["doi"])
        if scihub_text:
            full_text = scihub_text
            logger.info(
                "SciHub fallback: retrieved full text for DOI %s (%d chars)",
                paper["doi"], len(scihub_text),
            )

    # Extract figure captions and data availability BEFORE stripping references
    if full_text:
        figures = _extract_figure_captions(full_text)
        data_availability = _extract_data_availability(full_text)

    # Strip references/bibliography to avoid tagging entities in citations
    full_text_clean = strip_references(full_text) if full_text else ""

    return PaperSections(
        title=paper.get("title", "") or "",
        abstract=paper.get("abstract", "") or "",
        methods=paper.get("methods", "") or "",
        full_text=full_text_clean,
        figures=figures,
        data_availability=data_availability,
        metadata=paper,
    )


# ======================================================================
# Heuristic extraction from full text
# ======================================================================

# Figure caption patterns — extract "Figure 1. ..." or "Fig. 1: ..."
_FIGURE_CAPTION_RE = re.compile(
    r"(?:^|\n)\s*(?:(?:Supplementary\s+)?Fig(?:ure|\.)\s*(?:S?\d+)[\.:]\s*)"
    r"(.+?)(?=\n\s*(?:(?:Supplementary\s+)?Fig(?:ure|\.)\s*(?:S?\d+)|$))",
    re.IGNORECASE | re.DOTALL,
)

# Data/Code availability section headings
_DATA_AVAIL_RE = re.compile(
    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:"
    r"data\s+(?:and\s+(?:code|software|materials?)\s+)?availability"
    r"|code\s+availability"
    r"|data\s+(?:access|deposition|sharing)"
    r"|(?:availability\s+of\s+(?:data|code|materials?))"
    r"|accession\s+(?:codes?|numbers?)"
    r")\s*\n",
    re.IGNORECASE,
)


def _extract_figure_captions(text: str) -> str:
    """Extract figure captions from full text using regex."""
    captions = []
    for m in _FIGURE_CAPTION_RE.finditer(text):
        caption = m.group(0).strip()
        # Limit individual caption length (avoid grabbing full paragraphs)
        if len(caption) < 2000:
            captions.append(caption)
    return " ".join(captions)


def _extract_data_availability(text: str) -> str:
    """Extract Data Availability section from full text."""
    m = _DATA_AVAIL_RE.search(text)
    if not m:
        return ""

    start = m.end()
    # Take text until next section heading or end
    _next_heading = re.compile(
        r"\n\s*(?:\d+\.?\s*)?(?:acknowledge?ments?|references?|funding|"
        r"supplementary|author\s+contributions?|competing\s+interests?|"
        r"conflict\s+of\s+interest)\s*\n",
        re.IGNORECASE,
    )
    end_m = _next_heading.search(text, start)
    end = end_m.start() if end_m else min(start + 2000, len(text))
    return text[start:end].strip()


# Patterns to detect the start of References/Bibliography section
_REFERENCES_START_RE = re.compile(
    r"\n\s*(?:\d+\.?\s*)?(?:references?|bibliography|works\s+cited|literature\s+cited)\s*\n",
    re.IGNORECASE,
)


def strip_references(text: str) -> str:
    """Remove the References/Bibliography section from the end of full text.

    This prevents brand names, acronyms, and other entities mentioned
    in citation titles/author names from being incorrectly tagged.
    """
    if not text:
        return text
    m = _REFERENCES_START_RE.search(text)
    if m:
        return text[:m.start()].rstrip()
    return text


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
