"""
Europe PMC full-text fetcher -- Tier 1 of the three-tier waterfall strategy.

Europe PMC provides pre-parsed JATS XML with explicit section tags for
9+ million full-text articles (6.5M+ open access), eliminating the need
for PDF processing entirely.

Features:
  - Full-text XML retrieval via REST API (no API key required)
  - Section-level search with 17 pre-defined categories (98% F-score)
  - Annotations API for pre-computed entity mentions (genes, chemicals, etc.)
  - PMCID <-> DOI <-> PMID identifier mapping

Usage:
    from pipeline.parsing.europepmc_fetcher import EuropePMCFetcher
    fetcher = EuropePMCFetcher()
    sections = fetcher.fetch_fulltext_sections("PMC1234567")
    annotations = fetcher.fetch_annotations("PMC1234567")
"""

import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Europe PMC REST API base
_EPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"

# Rate limiting -- Europe PMC has no formal limit but recommends reasonable use
_REQUEST_DELAY = 0.2


def _retry_get(url: str, params: Dict = None, retries: int = 3,
               timeout: int = 30, accept: str = None) -> Optional["requests.Response"]:
    """GET with exponential backoff."""
    if not HAS_REQUESTS:
        return None
    headers = {}
    if accept:
        headers["Accept"] = accept
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                time.sleep(2 ** (attempt + 2))
                continue
            logger.debug("HTTP %d from %s", resp.status_code, url)
        except requests.RequestException as exc:
            logger.debug("Request error: %s", exc)
            time.sleep(2 ** attempt)
    return None


# Section type classification from JATS sec-type attributes
_JATS_SECTION_TYPE_MAP = {
    "methods": "methods",
    "materials": "methods",
    "materials|methods": "methods",
    "materials and methods": "methods",
    "experimental": "methods",
    "procedures": "methods",
    "results": "results",
    "results and discussion": "results",
    "intro": "introduction",
    "introduction": "introduction",
    "background": "introduction",
    "discussion": "discussion",
    "conclusions": "discussion",
    "supplementary-material": "supplementary",
    "data-availability": "data_availability",
    "data availability": "data_availability",
}

# Heading-based fallback classification
_HEADING_PATTERNS = {
    "methods": re.compile(
        r"method|material|experimental|procedure|microscopy|imaging|"
        r"sample\s+prep|staining|immunofluorescence|cell\s+culture",
        re.I,
    ),
    "results": re.compile(r"result|finding", re.I),
    "introduction": re.compile(r"introduction|background", re.I),
    "discussion": re.compile(r"discussion|conclusion|summary", re.I),
    "data_availability": re.compile(
        r"data\s+(?:and\s+(?:code|software)\s+)?availability|"
        r"code\s+availability|accession\s+(?:codes?|numbers?)",
        re.I,
    ),
    "figures": re.compile(r"figure|fig\.|table", re.I),
    "references": re.compile(r"references?|bibliography|works\s+cited", re.I),
}


class EuropePMCFetcher:
    """Fetch and parse full-text articles from Europe PMC."""

    def __init__(self):
        self._last_call = 0.0

    def _rate_limit(self):
        elapsed = time.time() - self._last_call
        if elapsed < _REQUEST_DELAY:
            time.sleep(_REQUEST_DELAY - elapsed)

    # ------------------------------------------------------------------
    # Full-text retrieval
    # ------------------------------------------------------------------

    def fetch_fulltext_xml(self, pmc_id: str) -> Optional[str]:
        """Fetch JATS XML full text from Europe PMC.

        Parameters
        ----------
        pmc_id : str
            PMC identifier (e.g., "PMC1234567" or "1234567").

        Returns
        -------
        str or None
            Raw JATS XML string, or None if unavailable.
        """
        pmc_id = self._normalize_pmcid(pmc_id)
        if not pmc_id:
            return None

        self._rate_limit()
        resp = _retry_get(f"{_EPMC_BASE}/{pmc_id}/fullTextXML")
        self._last_call = time.time()

        if resp is None:
            return None
        return resp.text

    def fetch_fulltext_sections(self, pmc_id: str) -> List[Dict[str, str]]:
        """Fetch and parse full-text JATS XML into section dicts.

        Returns a list of dicts with keys: heading, text, type.
        Section types: abstract, methods, results, introduction,
        discussion, data_availability, figures, other.
        """
        xml_text = self.fetch_fulltext_xml(pmc_id)
        if not xml_text:
            return []
        return self.parse_jats_xml(xml_text)

    @staticmethod
    def parse_jats_xml(xml_text: str) -> List[Dict[str, str]]:
        """Parse JATS XML into structured section dicts."""
        sections: List[Dict[str, str]] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Failed to parse JATS XML")
            return sections

        # Abstract
        for abstract in root.findall(".//abstract"):
            text = _recursive_text(abstract).strip()
            if text:
                sections.append({
                    "heading": "Abstract",
                    "text": text,
                    "type": "abstract",
                })

        # Body sections -- use sec-type attribute first, then heading heuristic
        for sec in root.findall(".//body//sec"):
            heading_el = sec.find("title")
            heading = _element_text(heading_el) if heading_el is not None else ""

            # Collect paragraph text (skip nested <sec> elements)
            paragraphs = []
            for p in sec.findall("p"):
                t = _recursive_text(p).strip()
                if t:
                    paragraphs.append(t)
            if not paragraphs:
                continue

            # Determine section type
            sec_type = sec.get("sec-type", "")
            section_type = _JATS_SECTION_TYPE_MAP.get(
                sec_type.lower(), _classify_heading(heading)
            )

            sections.append({
                "heading": heading,
                "text": " ".join(paragraphs),
                "type": section_type,
            })

        # Figure captions
        fig_captions = []
        for fig in root.findall(".//fig"):
            caption = fig.find("caption")
            if caption is not None:
                text = _recursive_text(caption).strip()
                if text:
                    label_el = fig.find("label")
                    label = _element_text(label_el) if label_el is not None else ""
                    fig_captions.append(f"{label} {text}".strip())
        if fig_captions:
            sections.append({
                "heading": "Figure Captions",
                "text": " ".join(fig_captions),
                "type": "figures",
            })

        # Table captions
        table_captions = []
        for table_wrap in root.findall(".//table-wrap"):
            caption = table_wrap.find("caption")
            if caption is not None:
                text = _recursive_text(caption).strip()
                if text:
                    label_el = table_wrap.find("label")
                    label = _element_text(label_el) if label_el is not None else ""
                    table_captions.append(f"{label} {text}".strip())
        if table_captions:
            sections.append({
                "heading": "Table Captions",
                "text": " ".join(table_captions),
                "type": "figures",  # treat same as figures
            })

        return sections

    # ------------------------------------------------------------------
    # Annotations API
    # ------------------------------------------------------------------

    def fetch_annotations(self, pmc_id: str,
                          types: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch text-mined annotations from Europe PMC Annotations API.

        Parameters
        ----------
        pmc_id : str
            PMC identifier.
        types : list of str, optional
            Annotation types to filter (e.g., ["Gene_Proteins", "Chemicals",
            "Diseases", "Organisms"]).

        Returns
        -------
        list of dict
            Annotation dicts with keys: type, text, section, database_id.
        """
        pmc_id = self._normalize_pmcid(pmc_id)
        if not pmc_id:
            return []

        params = {"articleIds": f"PMC:{pmc_id.replace('PMC', '')}", "format": "JSON"}
        if types:
            params["type"] = ",".join(types)

        self._rate_limit()
        resp = _retry_get(f"{_EPMC_BASE}/annotations", params=params)
        self._last_call = time.time()

        if resp is None:
            return []

        try:
            raw = resp.json()
        except Exception:
            return []

        annotations = []
        for ann_list in raw if isinstance(raw, list) else [raw]:
            for ann in ann_list.get("annotations", []) if isinstance(ann_list, dict) else []:
                annotations.append({
                    "type": ann.get("type", ""),
                    "text": ann.get("exact", ""),
                    "section": ann.get("section", ""),
                    "database_id": ann.get("uri", ""),
                    "prefix": ann.get("prefix", ""),
                    "postfix": ann.get("postfix", ""),
                })
        return annotations

    # ------------------------------------------------------------------
    # Search API
    # ------------------------------------------------------------------

    def search(self, query: str, *, result_type: str = "core",
               page_size: int = 25, cursor_mark: str = "*") -> Dict[str, Any]:
        """Search Europe PMC with optional section-level queries.

        Supports queries like: METHODS:"confocal microscopy"

        Parameters
        ----------
        query : str
            Europe PMC search query.
        result_type : str
            "core" for full metadata + abstract, "lite" for basic metadata.
        page_size : int
            Results per page (max 1000).
        cursor_mark : str
            Cursor for pagination ("*" for first page).

        Returns
        -------
        dict with keys: results (list), next_cursor (str or None), hit_count (int)
        """
        self._rate_limit()
        resp = _retry_get(
            f"{_EPMC_BASE}/search",
            params={
                "query": query,
                "resultType": result_type,
                "pageSize": min(page_size, 1000),
                "cursorMark": cursor_mark,
                "format": "json",
            },
        )
        self._last_call = time.time()

        if resp is None:
            return {"results": [], "next_cursor": None, "hit_count": 0}

        try:
            data = resp.json()
        except Exception:
            return {"results": [], "next_cursor": None, "hit_count": 0}

        result_list = data.get("resultList", {}).get("result", [])
        next_cursor = data.get("nextCursorMark")
        hit_count = int(data.get("hitCount", 0))

        return {
            "results": result_list,
            "next_cursor": next_cursor,
            "hit_count": hit_count,
        }

    # ------------------------------------------------------------------
    # Identifier mapping
    # ------------------------------------------------------------------

    def lookup_identifiers(self, *, doi: str = None, pmid: str = None,
                           pmc_id: str = None) -> Dict[str, Optional[str]]:
        """Map between DOI, PMID, and PMCID using Europe PMC search.

        Returns dict with keys: doi, pmid, pmc_id (each may be None).
        """
        query_parts = []
        if doi:
            query_parts.append(f'DOI:"{doi}"')
        elif pmid:
            query_parts.append(f"EXT_ID:{pmid} SRC:MED")
        elif pmc_id:
            pmc_num = pmc_id.replace("PMC", "").strip()
            query_parts.append(f"PMCID:PMC{pmc_num}")
        else:
            return {"doi": None, "pmid": None, "pmc_id": None}

        result = self.search(" ".join(query_parts), result_type="lite", page_size=1)
        if not result["results"]:
            return {"doi": doi, "pmid": pmid, "pmc_id": pmc_id}

        paper = result["results"][0]
        return {
            "doi": paper.get("doi") or doi,
            "pmid": paper.get("pmid") or pmid,
            "pmc_id": paper.get("pmcid") or pmc_id,
        }

    def has_fulltext(self, pmc_id: str) -> bool:
        """Check if Europe PMC has full text available for a PMCID."""
        pmc_id = self._normalize_pmcid(pmc_id)
        if not pmc_id:
            return False
        pmc_num = pmc_id.replace("PMC", "")
        result = self.search(f"PMCID:PMC{pmc_num}", result_type="lite", page_size=1)
        if result["results"]:
            return result["results"][0].get("hasTextMinedTerms", "N") == "Y" or \
                   result["results"][0].get("inEPMC", "N") == "Y"
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_pmcid(pmc_id: str) -> Optional[str]:
        """Normalize PMC ID to 'PMC1234567' format."""
        if not pmc_id:
            return None
        pmc_id = str(pmc_id).strip()
        if not pmc_id.upper().startswith("PMC"):
            pmc_id = f"PMC{pmc_id}"
        return pmc_id.upper()


# ======================================================================
# XML helpers
# ======================================================================

def _element_text(el: Optional[ET.Element]) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def _recursive_text(el: ET.Element) -> str:
    return "".join(el.itertext())


def _classify_heading(heading: str) -> str:
    """Classify a section heading into a standard type."""
    for stype, pattern in _HEADING_PATTERNS.items():
        if pattern.search(heading):
            return stype
    return "other"
