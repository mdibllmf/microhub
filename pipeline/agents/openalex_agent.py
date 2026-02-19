"""
OpenAlex enrichment agent -- first-call enrichment for any paper.

A single OpenAlex lookup by DOI returns institution resolution (ROR IDs),
author disambiguation, topic classification (4-level hierarchy), citation
counts, FWCI, OA status, and referenced works.  Singleton lookups cost
zero credits under the free tier.

OpenAlex covers 240M+ works with 98.6% coverage of PubMed content.
All data is CC0-licensed.

Usage:
    from pipeline.agents.openalex_agent import OpenAlexAgent
    agent = OpenAlexAgent(email="you@example.com")
    metadata = agent.enrich_paper(doi="10.1038/s41592-019-0358-2")
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

_OPENALEX_BASE = "https://api.openalex.org"
_REQUEST_DELAY = 0.1  # singleton lookups are free; be polite


class OpenAlexAgent:
    """Enrich papers using the OpenAlex API.

    Provides institution resolution (ROR), topic classification,
    citation counts, OA status, and referenced works in a single call.
    """

    name = "openalex"

    def __init__(self, email: str = "microhub@example.com",
                 api_key: str = None):
        """
        Parameters
        ----------
        email : str
            Polite pool email for OpenAlex API.
        api_key : str, optional
            OpenAlex API key (required since Feb 2026 for list queries;
            singleton lookups still free without key).
        """
        self.email = email
        self.api_key = api_key
        self._last_call = 0.0
        self._cache: Dict[str, Optional[Dict]] = {}

    # ------------------------------------------------------------------
    # Main enrichment entry point
    # ------------------------------------------------------------------

    def enrich_paper(self, *, doi: str = None, pmid: str = None,
                     openalex_id: str = None) -> Optional[Dict[str, Any]]:
        """Look up a single paper and return enriched metadata.

        Parameters
        ----------
        doi : str, optional
        pmid : str, optional
        openalex_id : str, optional
            Any one identifier suffices.

        Returns
        -------
        dict or None
            Enriched metadata dict with keys:
            - openalex_id, doi, pmid, pmcid
            - title, publication_year, type
            - citation_count, cited_by_count, fwci
            - oa_status, oa_url
            - institutions (list of dicts with name, ror_id, country)
            - authors (list of dicts with name, orcid, institution)
            - topics (list of dicts with name, field, subfield, domain)
            - referenced_works (list of OpenAlex IDs)
            - related_works (list of OpenAlex IDs)
        """
        cache_key = doi or pmid or openalex_id or ""
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._fetch_work(doi=doi, pmid=pmid, openalex_id=openalex_id)
        if data is None:
            self._cache[cache_key] = None
            return None

        result = self._parse_work(data)
        self._cache[cache_key] = result
        return result

    def enrich_batch(self, dois: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch lookup multiple DOIs using pipe-separated filter.

        Parameters
        ----------
        dois : list of str
            Up to 50 DOIs per batch.

        Returns
        -------
        dict mapping DOI -> enrichment data
        """
        results: Dict[str, Dict[str, Any]] = {}
        if not HAS_REQUESTS or not dois:
            return results

        # Check cache first
        uncached = []
        for doi in dois:
            clean = self._clean_doi(doi)
            if clean in self._cache:
                if self._cache[clean] is not None:
                    results[clean] = self._cache[clean]
            else:
                uncached.append(clean)

        if not uncached:
            return results

        # Batch in groups of 50
        for i in range(0, len(uncached), 50):
            batch = uncached[i:i + 50]
            filter_str = "|".join(batch)

            self._rate_limit()
            params = {
                "filter": f"doi:{filter_str}",
                "select": ("id,doi,ids,title,publication_year,type,"
                           "cited_by_count,fwci,"
                           "open_access,authorships,topics,"
                           "referenced_works,related_works"),
                "per_page": 50,
                "mailto": self.email,
            }
            if self.api_key:
                params["api_key"] = self.api_key

            try:
                resp = requests.get(
                    f"{_OPENALEX_BASE}/works",
                    params=params,
                    timeout=30,
                )
                self._last_call = time.time()

                if resp.status_code != 200:
                    logger.debug("OpenAlex batch HTTP %d", resp.status_code)
                    continue

                data = resp.json()
                for work in data.get("results", []):
                    parsed = self._parse_work(work)
                    work_doi = self._clean_doi(parsed.get("doi", ""))
                    if work_doi:
                        results[work_doi] = parsed
                        self._cache[work_doi] = parsed

            except Exception as exc:
                logger.debug("OpenAlex batch error: %s", exc)

        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_work(self, *, doi: str = None, pmid: str = None,
                    openalex_id: str = None) -> Optional[Dict]:
        """Fetch a single work from OpenAlex."""
        if not HAS_REQUESTS:
            return None

        if doi:
            url = f"{_OPENALEX_BASE}/works/doi:{quote(self._clean_doi(doi), safe='')}"
        elif pmid:
            url = f"{_OPENALEX_BASE}/works/pmid:{pmid.strip()}"
        elif openalex_id:
            url = f"{_OPENALEX_BASE}/works/{openalex_id}"
        else:
            return None

        self._rate_limit()
        try:
            params = {"mailto": self.email}
            if self.api_key:
                params["api_key"] = self.api_key

            resp = requests.get(url, params=params, timeout=15)
            self._last_call = time.time()

            if resp.status_code == 404:
                return None
            if resp.status_code != 200:
                logger.debug("OpenAlex HTTP %d for %s", resp.status_code, url)
                return None

            return resp.json()

        except Exception as exc:
            logger.debug("OpenAlex error: %s", exc)
            return None

    @staticmethod
    def _parse_work(data: Dict) -> Dict[str, Any]:
        """Parse an OpenAlex Work object into a clean enrichment dict."""
        # IDs
        ids = data.get("ids", {})
        result: Dict[str, Any] = {
            "openalex_id": data.get("id", ""),
            "doi": ids.get("doi", data.get("doi", "")),
            "pmid": ids.get("pmid", ""),
            "pmcid": ids.get("pmcid", ""),
            "title": data.get("title", ""),
            "publication_year": data.get("publication_year"),
            "type": data.get("type", ""),
        }

        # Clean DOI
        doi_val = result["doi"] or ""
        if doi_val.startswith("https://doi.org/"):
            result["doi"] = doi_val[len("https://doi.org/"):]

        # Citations
        result["cited_by_count"] = data.get("cited_by_count", 0)
        result["fwci"] = data.get("fwci")

        # Open access
        oa = data.get("open_access", {})
        result["oa_status"] = oa.get("oa_status", "closed")
        result["oa_url"] = oa.get("oa_url", "")
        result["is_oa"] = oa.get("is_oa", False)

        # Authors and institutions
        authors = []
        institutions = []
        seen_ror: set = set()

        for authorship in data.get("authorships", []):
            author_info = authorship.get("author", {})
            author = {
                "name": author_info.get("display_name", ""),
                "orcid": author_info.get("orcid", ""),
            }

            # Institutions from authorships
            for inst in authorship.get("institutions", []):
                ror_id = inst.get("ror", "")
                if ror_id and ror_id not in seen_ror:
                    seen_ror.add(ror_id)
                    institutions.append({
                        "name": inst.get("display_name", ""),
                        "ror_id": ror_id,
                        "country_code": inst.get("country_code", ""),
                        "type": inst.get("type", ""),
                    })

                if not author.get("institution"):
                    author["institution"] = inst.get("display_name", "")

            authors.append(author)

        result["authors"] = authors
        result["institutions"] = institutions

        # Topics (4-level hierarchy: Domain > Field > Subfield > Topic)
        topics = []
        for topic in data.get("topics", []):
            topics.append({
                "name": topic.get("display_name", ""),
                "score": topic.get("score", 0),
                "domain": (topic.get("domain", {}) or {}).get("display_name", ""),
                "field": (topic.get("field", {}) or {}).get("display_name", ""),
                "subfield": (topic.get("subfield", {}) or {}).get("display_name", ""),
            })
        result["topics"] = topics

        # Referenced and related works
        result["referenced_works"] = data.get("referenced_works", [])
        result["related_works"] = data.get("related_works", [])

        return result

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
