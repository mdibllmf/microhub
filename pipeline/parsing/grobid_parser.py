"""
GROBID-based PDF parser for section-aware document processing.

Converts PDFs into structured section-tagged text via a running GROBID
service (Docker recommended).  Falls back gracefully when GROBID is
unavailable.

Usage::

    parser = GrobidParser("http://localhost:8070")
    sections = parser.parse_pdf("/path/to/paper.pdf")
    # sections = [{"heading": "Methods", "text": "...", "type": "methods"}, ...]
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# Heading patterns mapped to canonical section types
_SECTION_PATTERNS = {
    "methods": re.compile(
        r"method|material|experimental|procedure|microscopy|imaging|protocol",
        re.IGNORECASE,
    ),
    "results": re.compile(r"result|finding|observation", re.IGNORECASE),
    "introduction": re.compile(r"introduction|background", re.IGNORECASE),
    "discussion": re.compile(r"discussion|conclusion|summary", re.IGNORECASE),
    "abstract": re.compile(r"abstract", re.IGNORECASE),
    "acknowledgements": re.compile(r"acknowledg|funding|support", re.IGNORECASE),
    "references": re.compile(r"reference|bibliography", re.IGNORECASE),
}


def _classify_heading(heading: str) -> str:
    """Return a canonical section type for a heading string."""
    for section_type, pattern in _SECTION_PATTERNS.items():
        if pattern.search(heading):
            return section_type
    return "other"


class GrobidParser:
    """Parse PDFs into structured sections via GROBID REST API."""

    def __init__(self, grobid_url: str = "http://localhost:8070"):
        self.grobid_url = grobid_url.rstrip("/")

    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        """Check whether the GROBID service is reachable."""
        if not HAS_REQUESTS:
            return False
        try:
            resp = requests.get(f"{self.grobid_url}/api/isalive", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    def parse_pdf(self, pdf_path: str) -> List[Dict[str, str]]:
        """Send a PDF to GROBID and return structured sections.

        Returns a list of dicts, each with keys ``heading``, ``text``,
        and ``type`` (one of the canonical section labels above).
        """
        if not HAS_REQUESTS:
            logger.warning("requests library not installed -- cannot call GROBID")
            return []
        if not HAS_BS4:
            logger.warning("beautifulsoup4 not installed -- cannot parse GROBID TEI")
            return []

        tei_xml = self._call_grobid(pdf_path)
        if not tei_xml:
            return []
        return self._parse_tei(tei_xml)

    # ------------------------------------------------------------------
    def parse_pdf_raw(self, pdf_path: str) -> Optional[str]:
        """Return the raw TEI XML string from GROBID."""
        return self._call_grobid(pdf_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_grobid(self, pdf_path: str) -> Optional[str]:
        try:
            with open(pdf_path, "rb") as f:
                resp = requests.post(
                    f"{self.grobid_url}/api/processFulltextDocument",
                    files={"input": f},
                    data={"segmentSentences": "1"},
                    timeout=120,
                )
            if resp.status_code == 200:
                return resp.text
            logger.warning("GROBID returned status %d", resp.status_code)
        except Exception as exc:
            logger.warning("GROBID call failed: %s", exc)
        return None

    def _parse_tei(self, tei_xml: str) -> List[Dict[str, str]]:
        """Extract sections from GROBID TEI XML."""
        soup = BeautifulSoup(tei_xml, "lxml")
        sections: List[Dict[str, str]] = []

        # Extract abstract
        abstract_el = soup.find("abstract")
        if abstract_el:
            text = " ".join(
                p.get_text(separator=" ", strip=True)
                for p in abstract_el.find_all("p")
            )
            if text:
                sections.append(
                    {"heading": "Abstract", "text": text, "type": "abstract"}
                )

        # Extract body sections
        body = soup.find("body")
        if not body:
            return sections

        for div in body.find_all("div"):
            head = div.find("head")
            heading = head.get_text(strip=True) if head else ""
            text = " ".join(
                p.get_text(separator=" ", strip=True) for p in div.find_all("p")
            )
            if not text:
                continue
            section_type = _classify_heading(heading) if heading else "other"
            sections.append(
                {"heading": heading, "text": text, "type": section_type}
            )

        return sections

    # ------------------------------------------------------------------
    def extract_metadata(self, tei_xml: str) -> Dict:
        """Pull title, authors, DOI, etc. from GROBID TEI header."""
        if not HAS_BS4:
            return {}
        soup = BeautifulSoup(tei_xml, "lxml")
        meta: Dict = {}

        title_el = soup.find("title", attrs={"type": "main"})
        if title_el:
            meta["title"] = title_el.get_text(strip=True)

        # Authors
        authors = []
        for author in soup.find_all("author"):
            persname = author.find("persname")
            if persname:
                forename = persname.find("forename")
                surname = persname.find("surname")
                name_parts = []
                if surname:
                    name_parts.append(surname.get_text(strip=True))
                if forename:
                    name_parts.append(forename.get_text(strip=True))
                if name_parts:
                    authors.append(" ".join(name_parts))
        if authors:
            meta["authors"] = ", ".join(authors)

        # DOI
        doi_el = soup.find("idno", attrs={"type": "DOI"})
        if doi_el:
            meta["doi"] = doi_el.get_text(strip=True)

        return meta
