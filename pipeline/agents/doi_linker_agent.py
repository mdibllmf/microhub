"""
Pass 2 — DOI-Repository Linker Agent.

Validates that extracted repository/data URLs actually belong to the paper
by cross-referencing the paper's DOI with repository metadata.

Validation methods:
  - Zenodo:   Query API → check related_identifiers for paper DOI
  - Figshare: Query API → check related DOIs
  - GitHub:   Check README/CITATION.cff for paper DOI
  - OMERO:    Check if public OMERO URLs resolve
  - General:  HTTP HEAD check for URL liveness

Each repository link gets a validation_status:
  - "confirmed"   — DOI match found in repository metadata
  - "probable"     — URL is live and repo looks related
  - "unconfirmed"  — URL is live but no DOI link found
  - "dead"         — URL returns 404 or connection error
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class DOILinkerAgent:
    """Validate repository URLs against paper DOIs."""

    name = "doi_linker"

    def __init__(self, github_token: str = None):
        self._github_token = github_token
        self._last_call = 0.0
        self._delay = 0.5

    def validate(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all repository links in a paper.  Mutates in-place."""
        if not HAS_REQUESTS:
            return paper

        doi = self._clean_doi(paper.get("doi", ""))
        repos = paper.get("repositories")
        if not repos or not isinstance(repos, list):
            return paper

        for repo in repos:
            if not isinstance(repo, dict):
                continue
            url = repo.get("url", "")
            name = (repo.get("name") or "").lower()
            if not url:
                continue

            status = "unconfirmed"

            if doi:
                # Try DOI-specific validation per repository type
                if "zenodo" in url.lower():
                    status = self._validate_zenodo(url, doi)
                elif "figshare" in url.lower():
                    status = self._validate_figshare(url, doi)
                elif "github.com" in url.lower():
                    status = self._validate_github_doi(url, doi)
                elif "dryad" in url.lower():
                    status = self._validate_dryad(url, doi)

            # If no DOI match, at least check URL is alive
            if status == "unconfirmed":
                if self._url_is_live(url):
                    status = "probable"
                else:
                    status = "dead"

            repo["validation_status"] = status

        paper["repositories"] = repos
        return paper

    # ------------------------------------------------------------------
    # Zenodo validation
    # ------------------------------------------------------------------

    def _validate_zenodo(self, url: str, paper_doi: str) -> str:
        """Check if a Zenodo record references the paper's DOI."""
        # Extract Zenodo record ID from URL
        m = re.search(r"zenodo\.org/(?:record|records)/(\d+)", url, re.I)
        if not m:
            # Try DOI-based Zenodo URL
            m = re.search(r"zenodo\.org/doi/10\.5281/zenodo\.(\d+)", url, re.I)
        if not m:
            return "unconfirmed"

        record_id = m.group(1)
        self._rate_limit()
        try:
            resp = requests.get(
                f"https://zenodo.org/api/records/{record_id}",
                timeout=15,
            )
            self._last_call = time.time()
            if resp.status_code != 200:
                return "unconfirmed"

            data = resp.json()
            related = data.get("metadata", {}).get("related_identifiers", [])
            for rel in related:
                rel_id = rel.get("identifier", "")
                if paper_doi.lower() in rel_id.lower():
                    return "confirmed"

            # Check description for DOI mention
            desc = data.get("metadata", {}).get("description", "")
            if paper_doi.lower() in desc.lower():
                return "confirmed"

            return "probable"  # Record exists but no DOI link

        except Exception:
            return "unconfirmed"

    # ------------------------------------------------------------------
    # Figshare validation
    # ------------------------------------------------------------------

    def _validate_figshare(self, url: str, paper_doi: str) -> str:
        """Check if a Figshare item references the paper's DOI."""
        # Extract article ID
        m = re.search(r"figshare\.com/articles/\w+/(\d+)", url, re.I)
        if not m:
            return "unconfirmed"

        article_id = m.group(1)
        self._rate_limit()
        try:
            resp = requests.get(
                f"https://api.figshare.com/v2/articles/{article_id}",
                timeout=15,
            )
            self._last_call = time.time()
            if resp.status_code != 200:
                return "unconfirmed"

            data = resp.json()
            # Check references
            refs = data.get("references", [])
            for ref in refs:
                if isinstance(ref, str) and paper_doi.lower() in ref.lower():
                    return "confirmed"

            # Check related materials
            for rm in data.get("related_materials", []):
                if paper_doi.lower() in (rm.get("identifier", "") or "").lower():
                    return "confirmed"

            return "probable"

        except Exception:
            return "unconfirmed"

    # ------------------------------------------------------------------
    # GitHub DOI validation
    # ------------------------------------------------------------------

    def _validate_github_doi(self, url: str, paper_doi: str) -> str:
        """Check if a GitHub repo's README or CITATION.cff references the paper DOI."""
        m = re.search(r"github\.com/([\w.-]+/[\w.-]+)", url, re.I)
        if not m:
            return "unconfirmed"

        full_name = m.group(1).rstrip("/")
        if full_name.endswith(".git"):
            full_name = full_name[:-4]

        headers = {"Accept": "application/vnd.github.v3.raw"}
        if self._github_token:
            headers["Authorization"] = f"token {self._github_token}"

        # Check CITATION.cff first (most reliable)
        for filepath in ["CITATION.cff", "CITATION.bib", "README.md"]:
            self._rate_limit()
            try:
                resp = requests.get(
                    f"https://api.github.com/repos/{full_name}/contents/{filepath}",
                    headers=headers,
                    timeout=10,
                )
                self._last_call = time.time()
                if resp.status_code == 200:
                    content = resp.text
                    if paper_doi.lower() in content.lower():
                        return "confirmed"
            except Exception:
                continue

        # Repo exists but no DOI reference found
        self._rate_limit()
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{full_name}",
                headers=headers,
                timeout=10,
            )
            self._last_call = time.time()
            if resp.status_code == 200:
                return "probable"
            elif resp.status_code == 404:
                return "dead"
        except Exception:
            pass

        return "unconfirmed"

    # ------------------------------------------------------------------
    # Dryad validation
    # ------------------------------------------------------------------

    def _validate_dryad(self, url: str, paper_doi: str) -> str:
        """Check if a Dryad dataset references the paper DOI."""
        self._rate_limit()
        try:
            # Dryad API uses the dataset DOI
            m = re.search(r"doi\.org/(10\.\d+/dryad\.\w+)", url, re.I)
            if not m:
                m = re.search(r"datadryad\.org/stash/dataset/doi:(10\.\d+/dryad\.\w+)", url, re.I)
            if not m:
                return "unconfirmed"

            dataset_doi = m.group(1)
            resp = requests.get(
                f"https://datadryad.org/api/v2/datasets/doi%3A{dataset_doi}",
                timeout=15,
            )
            self._last_call = time.time()
            if resp.status_code != 200:
                return "unconfirmed"

            data = resp.json()
            related_works = data.get("relatedWorks", [])
            for work in related_works:
                if paper_doi.lower() in (work.get("identifier", "") or "").lower():
                    return "confirmed"

            return "probable"

        except Exception:
            return "unconfirmed"

    # ------------------------------------------------------------------
    # Generic URL liveness check
    # ------------------------------------------------------------------

    def _url_is_live(self, url: str) -> bool:
        """Quick HEAD request to check if URL returns 200."""
        self._rate_limit()
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            self._last_call = time.time()
            return resp.status_code < 400
        except Exception:
            return False

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

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
