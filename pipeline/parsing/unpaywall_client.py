"""
Unpaywall OA discovery client -- Tier 2 of the three-tier waterfall strategy.

When a paper lacks a PMCID (no Europe PMC full text), Unpaywall finds
open-access PDF URLs using DOIs.  The API returns OA location details
including version metadata (publishedVersion, acceptedVersion, etc.)
and OA status classification (gold, green, hybrid, bronze, closed).

Rate limits: 100,000 calls/day per email address.

Usage:
    from pipeline.parsing.unpaywall_client import UnpaywallClient
    client = UnpaywallClient(email="you@example.com")
    result = client.lookup("10.1038/s41592-019-0358-2")
    if result and result["pdf_url"]:
        pdf_content = client.download_pdf(result["pdf_url"])
"""

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
_REQUEST_DELAY = 0.1  # generous; 100K/day ≈ 1.15/sec


class UnpaywallClient:
    """Look up open-access PDFs via the Unpaywall API."""

    def __init__(self, email: str = "microhub@example.com"):
        """
        Parameters
        ----------
        email : str
            Email address for the Unpaywall API (required, used for rate
            limit tracking by Unpaywall).
        """
        self.email = email
        self._last_call = 0.0
        self._cache: Dict[str, Optional[Dict]] = {}

    def lookup(self, doi: str) -> Optional[Dict[str, Any]]:
        """Look up OA availability for a DOI.

        Returns
        -------
        dict or None
            Dict with keys:
            - is_oa (bool): Whether any OA version exists
            - oa_status (str): gold, green, hybrid, bronze, or closed
            - pdf_url (str or None): Best OA PDF URL
            - pdf_version (str): publishedVersion, acceptedVersion, etc.
            - landing_page (str): Publisher/repository landing page
            - host_type (str): publisher or repository
            - license (str or None): License identifier
            - journal_name (str): Journal name
            - title (str): Paper title
            - year (int or None): Publication year
        """
        if not HAS_REQUESTS or not doi:
            return None

        doi = self._clean_doi(doi)
        if not doi:
            return None

        if doi in self._cache:
            return self._cache[doi]

        result = self._fetch(doi)
        self._cache[doi] = result
        return result

    def find_pdf_url(self, doi: str) -> Optional[str]:
        """Convenience: return just the best OA PDF URL, or None."""
        result = self.lookup(doi)
        if result and result.get("pdf_url"):
            return result["pdf_url"]
        return None

    def download_pdf(self, url: str, timeout: int = 60) -> Optional[bytes]:
        """Download PDF content from a URL.

        Returns raw bytes, or None on failure.
        """
        if not HAS_REQUESTS or not url:
            return None

        self._rate_limit()
        try:
            resp = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": "MicroHub/6.0 (mailto:microhub@example.com)"},
                allow_redirects=True,
            )
            self._last_call = time.time()
            if resp.status_code == 200 and len(resp.content) > 1000:
                # Basic PDF validation
                if resp.content[:5] == b"%PDF-":
                    return resp.content
                # Some servers return HTML error pages
                logger.debug("Downloaded content is not a PDF: %s", url)
            return None
        except Exception as exc:
            logger.debug("PDF download error from %s: %s", url, exc)
            return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch(self, doi: str) -> Optional[Dict[str, Any]]:
        """Query Unpaywall API for a DOI."""
        self._rate_limit()
        try:
            resp = requests.get(
                f"{_UNPAYWALL_BASE}/{quote(doi, safe='')}",
                params={"email": self.email},
                timeout=15,
            )
            self._last_call = time.time()

            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                logger.warning("Unpaywall rate limited")
                return None
            if resp.status_code != 200:
                logger.debug("Unpaywall HTTP %d for %s", resp.status_code, doi)
                return None

            data = resp.json()
            return self._parse_response(data)

        except Exception as exc:
            logger.debug("Unpaywall error for %s: %s", doi, exc)
            return None

    @staticmethod
    def _parse_response(data: Dict) -> Dict[str, Any]:
        """Parse Unpaywall API response into a clean dict."""
        best_oa = data.get("best_oa_location") or {}

        return {
            "is_oa": data.get("is_oa", False),
            "oa_status": data.get("oa_status", "closed"),
            "pdf_url": best_oa.get("url_for_pdf"),
            "pdf_version": best_oa.get("version", ""),
            "landing_page": best_oa.get("url_for_landing_page", ""),
            "host_type": best_oa.get("host_type", ""),
            "license": best_oa.get("license"),
            "journal_name": data.get("journal_name", ""),
            "title": data.get("title", ""),
            "year": data.get("year"),
            "doi": data.get("doi", ""),
        }

    def _rate_limit(self):
        elapsed = time.time() - self._last_call
        if elapsed < _REQUEST_DELAY:
            time.sleep(_REQUEST_DELAY - elapsed)

    @staticmethod
    def _clean_doi(doi: str) -> str:
        doi = (doi or "").strip()
        for prefix in ["https://doi.org/", "http://doi.org/", "doi:", "DOI:"]:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix):]
        return doi.strip()
