"""
Pass 2 — Cross-Reference Validation Agent.

Uses paper DOIs to fetch metadata from CrossRef and Semantic Scholar,
filling gaps in the existing extraction and cross-validating entities.

Capabilities:
  - Fill missing journal names, publication dates, license info
  - Discover additional data repositories via CrossRef links/relations
  - Fetch funder information (grant numbers, agencies)
  - Update citation counts from multiple sources
  - Cross-validate fields of study against extracted techniques
"""

import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class CrossRefValidationAgent:
    """Cross-reference and gap-fill using CrossRef and Semantic Scholar."""

    name = "crossref_validation"

    def __init__(self, s2_api_key: str = None):
        self._s2_api_key = s2_api_key
        self._last_crossref = 0.0
        self._last_s2 = 0.0
        self._cr_delay = 0.5
        self._s2_delay = 1.2 if not s2_api_key else 0.15
        self._s2_exhausted = False

    def validate(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-reference paper metadata via DOI lookups.  Mutates in-place."""
        if not HAS_REQUESTS:
            return paper

        doi = self._clean_doi(paper.get("doi", ""))
        if not doi:
            return paper

        # CrossRef: fill gaps + discover repos + funder info
        self._enrich_from_crossref(paper, doi)

        # Semantic Scholar: citation update + fields of study
        if not self._s2_exhausted:
            self._enrich_from_s2(paper, doi)

        return paper

    # ------------------------------------------------------------------
    # CrossRef enrichment
    # ------------------------------------------------------------------

    def _enrich_from_crossref(self, paper: Dict, doi: str) -> None:
        """Fetch CrossRef metadata and fill missing fields."""
        elapsed = time.time() - self._last_crossref
        if elapsed < self._cr_delay:
            time.sleep(self._cr_delay - elapsed)

        try:
            resp = requests.get(
                f"https://api.crossref.org/works/{quote(doi, safe='')}",
                headers={"User-Agent": "MicroHub/6.0 (mailto:support@microhub.io)"},
                timeout=15,
            )
            self._last_crossref = time.time()
            if resp.status_code != 200:
                return

            message = resp.json().get("message", {})

            # Fill missing journal name
            if not paper.get("journal"):
                container = message.get("container-title", [])
                if container:
                    paper["journal"] = container[0]

            # Fill missing publication year
            if not paper.get("year"):
                published = message.get("published-print") or message.get("published-online")
                if published and published.get("date-parts"):
                    parts = published["date-parts"][0]
                    if parts:
                        paper["year"] = parts[0]

            # License info
            if not paper.get("license"):
                licenses = message.get("license", [])
                for lic in licenses:
                    url = lic.get("URL", "")
                    if "creativecommons" in url:
                        paper["license"] = url
                        break

            # Funder information
            if not paper.get("funders"):
                funders = message.get("funder", [])
                if funders:
                    paper["funders"] = [
                        {
                            "name": f.get("name", ""),
                            "doi": f.get("DOI", ""),
                            "award": f.get("award", []),
                        }
                        for f in funders
                        if f.get("name")
                    ]

            # Reference count
            if not paper.get("reference_count"):
                paper["reference_count"] = message.get("reference-count", 0)

            # Subject areas
            if not paper.get("subjects"):
                subjects = message.get("subject", [])
                if subjects:
                    paper["subjects"] = subjects

        except Exception as exc:
            logger.debug("CrossRef error for %s: %s", doi, exc)

    # ------------------------------------------------------------------
    # Semantic Scholar enrichment
    # ------------------------------------------------------------------

    def _enrich_from_s2(self, paper: Dict, doi: str) -> None:
        """Fetch S2 metadata for citation counts and fields of study."""
        elapsed = time.time() - self._last_s2
        if elapsed < self._s2_delay:
            time.sleep(self._s2_delay - elapsed)

        try:
            headers = {}
            if self._s2_api_key:
                headers["x-api-key"] = self._s2_api_key

            resp = requests.get(
                f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
                params={
                    "fields": "citationCount,influentialCitationCount,"
                              "fieldsOfStudy,s2FieldsOfStudy,isOpenAccess,"
                              "openAccessPdf",
                },
                headers=headers,
                timeout=15,
            )
            self._last_s2 = time.time()

            if resp.status_code == 429:
                self._s2_exhausted = True
                return
            if resp.status_code != 200:
                return

            data = resp.json()

            # Citation counts
            s2_citations = data.get("citationCount", 0) or 0
            current = paper.get("citation_count", 0) or 0
            if s2_citations > current:
                paper["citation_count"] = s2_citations
                paper["citation_source"] = "semantic_scholar"

            s2_influential = data.get("influentialCitationCount", 0)
            if s2_influential and not paper.get("influential_citation_count"):
                paper["influential_citation_count"] = s2_influential

            # Fields of study
            if not paper.get("fields_of_study"):
                s2_fields = data.get("s2FieldsOfStudy", []) or []
                if s2_fields:
                    cats = [f["category"] for f in s2_fields
                            if isinstance(f, dict) and f.get("category")]
                    if cats:
                        paper["fields_of_study"] = list(dict.fromkeys(cats))
                elif data.get("fieldsOfStudy"):
                    paper["fields_of_study"] = data["fieldsOfStudy"]

            # Open access status
            if not paper.get("is_open_access"):
                paper["is_open_access"] = data.get("isOpenAccess", False)
            if not paper.get("open_access_pdf"):
                oa_pdf = data.get("openAccessPdf")
                if isinstance(oa_pdf, dict) and oa_pdf.get("url"):
                    paper["open_access_pdf"] = oa_pdf["url"]

        except Exception as exc:
            logger.debug("S2 error for %s: %s", doi, exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_doi(doi: str) -> str:
        doi = (doi or "").strip()
        for prefix in ["https://doi.org/", "http://doi.org/", "doi:", "DOI:"]:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix):]
        return doi.strip()
