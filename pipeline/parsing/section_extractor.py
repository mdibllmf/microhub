"""
Unified section extractor that works with multiple input formats.

Supports:
  - Europe PMC JATS XML (Tier 1 — preferred, pre-parsed with section tags)
  - GROBID TEI XML (via GrobidParser)
  - PMC NXML full-text (via pubmed_parser)
  - Unpaywall + GROBID (Tier 2 — OA PDF discovery + PDF processing)
  - Plain text with heuristic section detection
  - Pre-parsed PubMed metadata dicts

Implements a three-tier waterfall strategy for full-text acquisition:
  Tier 1: Europe PMC JATS XML (no PDF processing needed)
  Tier 2: Unpaywall OA PDF → GROBID processing
  Tier 3: Abstract-only fallback

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
from .europepmc_fetcher import EuropePMCFetcher
from .unpaywall_client import UnpaywallClient

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

    def taggable_sections(self, *, include_introduction: bool = False):
        """Yield (text, section_type) pairs for sections safe to tag.

        Excludes introduction by default (introduction mentions entities
        from OTHER papers, causing over-tagging).  Also excludes full_text
        when structured sections are available.
        """
        if self.title:
            yield self.title, "title"
        if self.abstract:
            yield self.abstract, "abstract"
        if self.methods:
            yield self.methods, "methods"
        if self.results:
            yield self.results, "results"
        if include_introduction and self.introduction:
            yield self.introduction, "introduction"
        if self.discussion:
            yield self.discussion, "discussion"
        if self.figures:
            yield self.figures, "figures"
        if self.data_availability:
            yield self.data_availability, "data_availability"
        # Only yield full_text if we have NO structured sections at all
        if (not self.methods and not self.results
                and self.full_text
                and self.full_text != self.abstract):
            yield self.full_text, "full_text"


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

    Full text should already be present in the paper dict — the scraper
    (1_scrape.py) is responsible for fetching it via the three-tier waterfall.
    """
    full_text = paper.get("full_text", "") or ""
    figures = ""
    # Use existing data_availability from the paper dict (e.g., from step 2)
    # and also extract from full_text if available
    data_availability = paper.get("data_availability", "") or ""

    # Extract figure captions and data availability BEFORE stripping references
    if full_text:
        figures = _extract_figure_captions(full_text)
        extracted_da = _extract_data_availability(full_text)
        if extracted_da:
            # Merge: append extracted text if it adds content
            if data_availability:
                # Avoid duplicating if they're basically the same text
                if extracted_da.strip() not in data_availability:
                    data_availability = data_availability + "\n\n" + extracted_da
            else:
                data_availability = extracted_da

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
    r"|code\s+(?:and\s+data\s+)?availability"
    r"|data\s+(?:access|deposition|sharing)"
    r"|(?:availability\s+of\s+(?:data|code|materials?))"
    r"|accession\s+(?:codes?|numbers?)"
    r"|resource\s+availability"
    r"|data\s+and\s+resource\s+sharing"
    r"|materials?\s+availability"
    r"|supplementary\s+(?:data|information|materials?)\s+availability"
    r"|data\s+(?:repositor(?:y|ies)|archiv\w*)"
    r"|associated\s+content"
    r"|related\s+(?:data|datasets?)"
    r"|data\s+records?"
    r"|data\s+statement"
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
    """Extract Data Availability and Code Availability sections from full text.

    Finds ALL matching sections (data availability, code availability, etc.)
    and concatenates them.  This ensures code availability is captured even
    when it appears as a separate section from data availability.
    """
    _next_heading = re.compile(
        r"\n\s*(?:\d+\.?\s*)?(?:acknowledge?ments?|references?|funding|"
        r"supplementary|author\s+contributions?|competing\s+interests?|"
        r"conflict\s+of\s+interest|ethics\s+(?:statement|approval)|"
        r"extended\s+data|reporting\s+summary|online\s+methods|"
        r"additional\s+information|key\s+resources?\s+table|"
        r"star\s+methods|(?:experimental|materials?\s+and)\s+methods?"
        # Also terminate at the NEXT data/code availability heading so
        # separate "Data availability" and "Code availability" sections
        # don't bleed into each other
        r"|data\s+(?:and\s+(?:code|software|materials?)\s+)?availability"
        r"|code\s+(?:and\s+data\s+)?availability"
        r"|(?:availability\s+of\s+(?:data|code|materials?))"
        r"|accession\s+(?:codes?|numbers?))\s*\n",
        re.IGNORECASE,
    )

    parts = []
    for m in _DATA_AVAIL_RE.finditer(text):
        start = m.end()
        end_m = _next_heading.search(text, start)
        end = end_m.start() if end_m else min(start + 3000, len(text))
        chunk = text[start:end].strip()
        if chunk:
            parts.append(chunk)

    return "\n\n".join(parts)


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


# ======================================================================
# Inline citation stripping
# ======================================================================

# Numeric citations: [1], [1,2], [1-5], [1, 3, 7-9]
_NUMERIC_CITATION_RE = re.compile(
    r"\[(?:\d+(?:\s*[-–—]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–—]\s*\d+)?)*)\]"
)

# Author-year citations: (Smith et al., 2020), (Smith and Jones, 2019),
# (Smith, 2020; Jones et al., 2021), (Smith 2020)
_AUTHOR_YEAR_CITATION_RE = re.compile(
    r"\(\s*(?:[A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))?)"
    r"(?:\s*,?\s*\d{4}[a-z]?)"
    r"(?:\s*;\s*(?:[A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))?)"
    r"(?:\s*,?\s*\d{4}[a-z]?))*\s*\)"
)

# Superscript-style: text¹ or text¹⁻³ or text¹˒²˒³
_SUPERSCRIPT_CITATION_RE = re.compile(
    r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+(?:[⁻˒,][⁰¹²³⁴⁵⁶⁷⁸⁹]+)*"
)

# Protect patterns — things that LOOK like citations but are scientific
# (488 nm), (60x/1.4 NA), [Ca2+], [K+], [Na+], (pH 7.4), (n = 5)
_PROTECTED_BRACKET_RE = re.compile(
    r"\["
    r"(?:[A-Z][a-z]?\d*[+\-−])"  # ions like Ca2+, K+, Na+
    r"|(?:\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\s*"
    r"(?:nm|µm|μm|mm|cm|mM|µM|μM|nM|kDa|Da|mg|µg|µl|mL|ml|°C|K|s|ms|min|hr?|Hz|kHz|MHz|GHz|V|mV|kV|A|mA|W|mW))"  # units
    r"\]"
)
_PROTECTED_PAREN_RE = re.compile(
    r"\("
    r"(?:\d+(?:\.\d+)?\s*(?:nm|µm|μm|mm|cm|mM|µM|μM|nM|kDa|Da|mg|µg|µl|mL|ml|°C|K|s|ms|min|hr?|Hz|kHz|MHz|GHz|V|mV|kV|A|mA|W|mW))"
    r"|(?:\d+[xX]/\d+(?:\.\d+)?\s*(?:NA|Oil|oil|Water|water|Air|air))"  # objectives
    r"|(?:n\s*=\s*\d+)"  # sample sizes
    r"|(?:pH?\s*\d+(?:\.\d+)?)"  # pH values
    r"|(?:P?\s*[<>=]+\s*\d)"  # p-values
    r"|(?:Fig(?:ure|\.)\s*\w)"  # figure refs
    r"|(?:Table\s*\w)"  # table refs
    r"\)"
)


def strip_inline_citations(text: str) -> str:
    """Remove inline citations while preserving scientific notation.

    Strips:
      - Numeric: [1], [1,2], [1-5], [1, 3, 7-9]
      - Author-year: (Smith et al., 2020), (Smith and Jones, 2019)
      - Superscript: ¹²³

    Preserves:
      - Ion concentrations: [Ca2+], [K+]
      - Measurements: (488 nm), (60x/1.4 NA)
      - Sample sizes: (n = 5)
      - pH values: (pH 7.4)
      - P-values: (P < 0.05)
      - Figure/Table references: (Fig. 1), (Table 2)
    """
    if not text:
        return text

    # Step 1: protect scientific brackets/parens with placeholders
    protected = {}
    counter = [0]

    def _protect(m):
        key = f"\x00PROT{counter[0]}\x00"
        protected[key] = m.group(0)
        counter[0] += 1
        return key

    text = _PROTECTED_BRACKET_RE.sub(_protect, text)
    text = _PROTECTED_PAREN_RE.sub(_protect, text)

    # Step 2: strip citations
    text = _NUMERIC_CITATION_RE.sub("", text)
    text = _AUTHOR_YEAR_CITATION_RE.sub("", text)
    text = _SUPERSCRIPT_CITATION_RE.sub("", text)

    # Step 3: restore protected tokens
    for key, val in protected.items():
        text = text.replace(key, val)

    # Clean up double spaces left by removal
    text = re.sub(r"  +", " ", text)
    return text


# ======================================================================
# Heuristic section segmentation from full text
# ======================================================================

# Heading detection regex: matches typical section headings
_HEADING_RE = re.compile(
    r"(?:^|\n)\s*"
    r"(?:(?:\d+\.?(?:\d+\.?)*)\s+)?"  # optional numbering: 1., 2.1, etc.
    r"("
    # Core section headings
    r"abstract|introduction|background"
    r"|(?:materials?\s+and\s+)?methods?"
    r"|experimental\s+(?:procedures?|section|methods?|design)"
    r"|(?:materials?\s+and\s+methods?)"
    r"|(?:methods?\s+and\s+materials?)"
    r"|results?\s+(?:and\s+discussion)?"
    r"|results?"
    r"|discussion"
    r"|conclusions?"
    r"|summary"
    r"|acknowledge?ments?"
    r"|references?|bibliography|works\s+cited|literature\s+cited"
    r"|(?:supplementary|supporting)\s+(?:information|data|materials?|methods?|figures?|tables?)"
    r"|(?:data|code)\s+(?:and\s+(?:code|data)\s+)?availability"
    r"|(?:availability\s+of\s+(?:data|code|materials?))"
    r"|accession\s+(?:codes?|numbers?)"
    r"|resource\s+availability"
    r"|author\s+contributions?"
    r"|competing\s+interests?"
    r"|conflict\s+of\s+interests?"
    r"|ethics\s+(?:statement|approval|declaration)"
    r"|funding\s*(?:information|sources?|statement)?"
    r"|(?:key\s+resources?\s+table)"
    r"|(?:star|lead\s+contact)\s+methods?"
    r"|(?:online|extended)\s+methods?"
    r"|figure\s+legends?"
    r"|(?:additional|extended)\s+(?:data|information)"
    r"|(?:reporting\s+summary)"
    r"|image\s+(?:acquisition|analysis|processing)"
    r"|microscopy"
    r"|(?:sample|specimen)\s+preparation"
    r"|(?:cell|tissue)\s+culture"
    r"|(?:statistical|data)\s+analysis"
    r"|immunofluorescence\s*(?:staining|microscopy)?"
    r"|immunohistochemistry"
    r"|western\s+blot(?:ting)?"
    r"|(?:confocal|fluorescence|electron|light)\s+microscopy"
    r")"
    r"\s*(?:\n|$)",
    re.IGNORECASE,
)

# Map heading text to section type
_HEADING_TYPE_MAP = {
    "abstract": "abstract",
    "introduction": "introduction",
    "background": "introduction",
    "methods": "methods",
    "method": "methods",
    "materials and methods": "methods",
    "methods and materials": "methods",
    "material and methods": "methods",
    "materials and method": "methods",
    "experimental procedures": "methods",
    "experimental procedure": "methods",
    "experimental section": "methods",
    "experimental methods": "methods",
    "experimental method": "methods",
    "experimental design": "methods",
    "online methods": "methods",
    "extended methods": "methods",
    "star methods": "methods",
    "lead contact methods": "methods",
    "image acquisition": "methods",
    "image analysis": "methods",
    "image processing": "methods",
    "microscopy": "methods",
    "sample preparation": "methods",
    "specimen preparation": "methods",
    "cell culture": "methods",
    "tissue culture": "methods",
    "statistical analysis": "methods",
    "data analysis": "methods",
    "immunofluorescence": "methods",
    "immunofluorescence staining": "methods",
    "immunofluorescence microscopy": "methods",
    "immunohistochemistry": "methods",
    "western blotting": "methods",
    "western blot": "methods",
    "confocal microscopy": "methods",
    "fluorescence microscopy": "methods",
    "electron microscopy": "methods",
    "light microscopy": "methods",
    "results": "results",
    "results and discussion": "results",
    "result": "results",
    "discussion": "discussion",
    "conclusions": "discussion",
    "conclusion": "discussion",
    "summary": "discussion",
    "acknowledgements": "acknowledgements",
    "acknowledgments": "acknowledgements",
    "acknowledgement": "acknowledgements",
    "acknowledgment": "acknowledgements",
    "references": "references",
    "reference": "references",
    "bibliography": "references",
    "works cited": "references",
    "literature cited": "references",
    "author contributions": "other",
    "author contribution": "other",
    "competing interests": "other",
    "conflict of interests": "other",
    "conflict of interest": "other",
    "ethics statement": "other",
    "ethics approval": "other",
    "ethics declaration": "other",
    "funding": "other",
    "funding information": "other",
    "funding sources": "other",
    "funding source": "other",
    "funding statement": "other",
    "key resources table": "methods",
    "figure legends": "figures",
    "figure legend": "figures",
    "additional data": "other",
    "additional information": "other",
    "extended data": "other",
    "reporting summary": "other",
    "supplementary information": "supplementary",
    "supplementary data": "supplementary",
    "supplementary materials": "supplementary",
    "supplementary material": "supplementary",
    "supplementary methods": "methods",
    "supplementary figures": "figures",
    "supplementary tables": "other",
    "supporting information": "supplementary",
    "supporting data": "supplementary",
    "supporting materials": "supplementary",
    "supporting material": "supplementary",
    "supporting methods": "methods",
    "supporting figures": "figures",
    "supporting tables": "other",
    "data availability": "data_availability",
    "code availability": "data_availability",
    "data and code availability": "data_availability",
    "code and data availability": "data_availability",
    "availability of data": "data_availability",
    "availability of code": "data_availability",
    "availability of materials": "data_availability",
    "accession codes": "data_availability",
    "accession code": "data_availability",
    "accession numbers": "data_availability",
    "accession number": "data_availability",
    "resource availability": "data_availability",
}


def _classify_heading(heading: str) -> str:
    """Classify a heading string into a section type."""
    # Strip numbering and whitespace
    clean = re.sub(r"^\d+\.?\s*(?:\d+\.?\s*)*", "", heading.strip()).strip()
    clean_lower = clean.lower()

    # Exact match
    if clean_lower in _HEADING_TYPE_MAP:
        return _HEADING_TYPE_MAP[clean_lower]

    # Partial match: check if any key is contained in the heading
    for key, stype in _HEADING_TYPE_MAP.items():
        if key in clean_lower:
            return stype

    return "other"


def heuristic_segment(text: str) -> List[Dict[str, str]]:
    """Segment full text into sections using heading detection heuristics.

    Returns a list of {heading, text, type} dicts, similar to what
    GROBID or Europe PMC parsers produce.  Falls back to a single
    'full_text' section if no headings are detected.
    """
    if not text:
        return []

    headings = list(_HEADING_RE.finditer(text))

    if not headings:
        # No headings found — return full text as a single section
        return [{"heading": "", "text": text, "type": "full_text"}]

    sections = []

    # Text before the first heading (if any) — treat as preamble/abstract
    if headings[0].start() > 50:
        preamble = text[:headings[0].start()].strip()
        if preamble:
            sections.append({
                "heading": "",
                "text": preamble,
                "type": "other",
            })

    for i, m in enumerate(headings):
        heading_text = m.group(1).strip()
        section_type = _classify_heading(heading_text)

        # Section body: from end of this heading to start of next heading
        body_start = m.end()
        if i + 1 < len(headings):
            body_end = headings[i + 1].start()
        else:
            body_end = len(text)

        body = text[body_start:body_end].strip()
        if body:
            sections.append({
                "heading": heading_text,
                "text": body,
                "type": section_type,
            })

    return sections


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


def from_europe_pmc(pmc_id: str, metadata: Dict = None) -> PaperSections:
    """Fetch and parse via Europe PMC JATS XML (Tier 1).

    Europe PMC provides pre-parsed JATS XML with explicit section tags,
    covering 9M+ full-text articles.  This is the preferred source
    because it eliminates PDF processing entirely.
    """
    fetcher = EuropePMCFetcher()
    sections = fetcher.fetch_fulltext_sections(pmc_id)
    if not sections:
        logger.debug("Europe PMC: no full text for %s", pmc_id)
        return PaperSections()

    ps = from_sections_list(sections, metadata)
    logger.info("Europe PMC: parsed %d sections from %s", len(sections), pmc_id)
    return ps


def from_unpaywall_pdf(doi: str, metadata: Dict = None,
                       grobid_url: str = "http://localhost:8070",
                       email: str = "microhub@example.com") -> PaperSections:
    """Discover OA PDF via Unpaywall + parse with GROBID (Tier 2).

    For articles without PMCIDs, Unpaywall finds open-access PDF URLs.
    GROBID processes these PDFs into structured TEI XML.
    """
    client = UnpaywallClient(email=email)
    pdf_url = client.find_pdf_url(doi)
    if not pdf_url:
        logger.debug("Unpaywall: no OA PDF for DOI %s", doi)
        return PaperSections()

    # Download and parse with GROBID
    pdf_content = client.download_pdf(pdf_url)
    if not pdf_content:
        logger.debug("Unpaywall: failed to download PDF from %s", pdf_url)
        return PaperSections()

    parser = GrobidParser(grobid_url)
    if not parser.is_available():
        logger.warning("GROBID not available at %s for Unpaywall PDF", grobid_url)
        return PaperSections()

    # Write to temporary file for GROBID
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_content)
        tmp_path = f.name

    try:
        tei = parser.parse_pdf_raw(tmp_path)
        if not tei:
            return PaperSections()
        grobid_meta = parser.extract_metadata(tei)
        sections = parser.parse_pdf(tmp_path)
        if metadata:
            grobid_meta.update({k: v for k, v in metadata.items() if v})
        ps = from_sections_list(sections, grobid_meta)
        logger.info("Unpaywall+GROBID: parsed %d sections for DOI %s",
                     len(sections), doi)
        return ps
    finally:
        os.unlink(tmp_path)


def three_tier_waterfall(paper: Dict,
                         grobid_url: str = "http://localhost:8070",
                         email: str = "microhub@example.com") -> PaperSections:
    """Three-tier waterfall strategy for full-text acquisition.

    Tier 1: Europe PMC JATS XML (preferred — pre-parsed, no PDF needed)
    Tier 2: Unpaywall OA PDF discovery + GROBID processing
    Tier 3: Abstract-only fallback (from paper dict)

    Parameters
    ----------
    paper : dict
        Paper dict with at minimum: title, abstract.
        May also have: pmc_id, doi, full_text, methods.
    grobid_url : str
        GROBID service URL for Tier 2 PDF processing.
    email : str
        Email for Unpaywall API.

    Returns
    -------
    PaperSections
        Best available parsed sections.
    """
    pmc_id = paper.get("pmc_id", "") or ""
    doi = paper.get("doi", "") or ""
    metadata = paper

    # Tier 1: Europe PMC JATS XML
    if pmc_id:
        ps = from_europe_pmc(pmc_id, metadata)
        if ps.has_methods or ps.full_text:
            return ps
        # Fallback to NCBI PMC
        ps = from_pmc(pmc_id)
        if ps.has_methods or ps.full_text:
            if metadata:
                ps.metadata = metadata
                ps.title = ps.title or metadata.get("title", "")
                ps.abstract = ps.abstract or metadata.get("abstract", "")
            return ps

    # Tier 2: Unpaywall + GROBID
    if doi:
        ps = from_unpaywall_pdf(doi, metadata, grobid_url, email)
        if ps.has_methods or ps.full_text:
            return ps

    # Tier 3: Abstract-only fallback
    logger.debug("Waterfall: falling back to abstract-only for %s",
                 doi or pmc_id or paper.get("title", "?")[:50])
    return from_pubmed_dict(paper)
