"""
API-based enrichment for the cleanup step (step 3).

Ports the critical enrichment logic from the original cleanup_and_retag.py:
  - GitHub API:           Repository metadata, health scores, activity metrics
  - Semantic Scholar API: Citation updates, fields of study
  - CrossRef API:         Additional data repositories via links & DOI relations

These APIs supplement the scraper's extraction — the scraper may not always
find everything, and this module fills in the gaps during cleanup.

Usage in 3_clean.py:
    from pipeline.enrichment import enrich_paper
    enrich_paper(paper)      # mutates paper in-place
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency: requests
# ---------------------------------------------------------------------------
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# API keys from environment
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

# Rate-limiting helpers
_last_github_call = 0.0
_last_s2_call = 0.0
_GITHUB_DELAY = 0.5      # seconds between GitHub API calls
_S2_DELAY = 0.3           # seconds between S2 API calls


# ======================================================================
# Public API
# ======================================================================

def enrich_paper(paper: Dict, *, fetch_github: bool = True,
                 fetch_citations: bool = True,
                 fetch_crossref_repos: bool = True) -> Dict:
    """Enrich a single paper dict with API data.  Mutates in-place.

    Fills in missing data without overwriting existing non-empty values.
    """
    if not HAS_REQUESTS:
        logger.debug("requests not available — skipping API enrichment")
        return paper

    # 1. GitHub tool enrichment (stars, forks, health score, activity)
    if fetch_github:
        _enrich_github_tools(paper)

    # 2. Citation metrics from Semantic Scholar
    if fetch_citations:
        _enrich_citations(paper)

    # 3. Additional data repositories from CrossRef
    if fetch_crossref_repos:
        _enrich_crossref_repos(paper)

    return paper


# ======================================================================
# GitHub API enrichment
# ======================================================================

def _enrich_github_tools(paper: Dict) -> None:
    """Fetch missing metadata for each github tool."""
    tools = paper.get("github_tools")
    if not tools or not isinstance(tools, list):
        return

    updated = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue

        full_name = tool.get("full_name") or ""
        if not full_name or "/" not in full_name:
            updated.append(tool)
            continue

        # Only fetch if key data is missing
        needs_fetch = (
            not tool.get("description")
            or not tool.get("language")
            or tool.get("health_score", 0) == 0
        )

        if needs_fetch:
            metrics = _fetch_github_metadata(full_name)
            if metrics:
                # Merge: only fill in missing fields, never overwrite existing
                for key, val in metrics.items():
                    if key == "health_score":
                        tool[key] = val  # always update score
                    elif not tool.get(key) and val:
                        tool[key] = val
        updated.append(tool)

    paper["github_tools"] = updated

    # Ensure github_url is set (prefer 'introduces' relationship)
    if not paper.get("github_url") and updated:
        introduces = [t for t in updated if t.get("relationship") == "introduces"]
        if introduces:
            paper["github_url"] = introduces[0].get("url")
        else:
            paper["github_url"] = updated[0].get("url")


def _fetch_github_metadata(full_name: str) -> Optional[Dict]:
    """Fetch repository metadata from the GitHub API."""
    global _last_github_call

    full_name = full_name.strip().rstrip("/").removesuffix(".git")

    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Rate limiting
    elapsed = time.time() - _last_github_call
    if elapsed < _GITHUB_DELAY:
        time.sleep(_GITHUB_DELAY - elapsed)

    try:
        resp = requests.get(
            f"https://api.github.com/repos/{full_name}",
            headers=headers, timeout=15,
        )
        _last_github_call = time.time()

        if resp.status_code == 404:
            return {"exists": False, "full_name": full_name}
        if resp.status_code == 403:
            logger.warning("GitHub API rate limited for %s", full_name)
            return None
        if resp.status_code != 200:
            return None

        data = resp.json()
        metrics = {
            "exists": True,
            "full_name": data.get("full_name", full_name),
            "description": (data.get("description") or "")[:500],
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "language": data.get("language") or "",
            "license": (data.get("license") or {}).get("spdx_id", ""),
            "topics": data.get("topics", []),
            "is_archived": data.get("archived", False),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "pushed_at": data.get("pushed_at", ""),
            "homepage": data.get("homepage", ""),
        }

        # Latest release
        try:
            rr = requests.get(
                f"https://api.github.com/repos/{full_name}/releases/latest",
                headers=headers, timeout=10,
            )
            if rr.status_code == 200:
                rel = rr.json()
                metrics["last_release"] = rel.get("tag_name", "")
                metrics["last_release_date"] = rel.get("published_at", "")
        except Exception:
            pass

        # Last commit date
        try:
            cr = requests.get(
                f"https://api.github.com/repos/{full_name}/commits",
                headers=headers, params={"per_page": 1}, timeout=10,
            )
            if cr.status_code == 200:
                commits = cr.json()
                if commits:
                    metrics["last_commit_date"] = (
                        commits[0].get("commit", {})
                        .get("committer", {}).get("date", "")
                    )
        except Exception:
            pass

        metrics["health_score"] = compute_github_health_score(metrics)
        return metrics

    except Exception as exc:
        logger.warning("Error fetching GitHub metadata for %s: %s", full_name, exc)
        return None


def compute_github_health_score(metrics: Dict) -> int:
    """Compute a 0-100 health score for a GitHub repository."""
    if not metrics.get("exists", True):
        return 0
    if metrics.get("is_archived", False):
        return 10

    score = 0

    # Stars (up to 25 points)
    stars = metrics.get("stars", 0)
    if stars >= 1000: score += 25
    elif stars >= 500: score += 22
    elif stars >= 100: score += 18
    elif stars >= 50: score += 14
    elif stars >= 10: score += 10
    elif stars >= 1: score += 5

    # Recent activity (up to 30 points)
    last_commit = metrics.get("last_commit_date", "") or metrics.get("pushed_at", "")
    if last_commit:
        try:
            commit_date = datetime.fromisoformat(last_commit.replace("Z", "+00:00"))
            now = datetime.now(commit_date.tzinfo) if commit_date.tzinfo else datetime.now()
            days_since = (now - commit_date).days
            if days_since <= 30: score += 30
            elif days_since <= 90: score += 25
            elif days_since <= 180: score += 20
            elif days_since <= 365: score += 12
            elif days_since <= 730: score += 5
        except Exception:
            pass

    # Forks (up to 15 points)
    forks = metrics.get("forks", 0)
    if forks >= 100: score += 15
    elif forks >= 50: score += 12
    elif forks >= 10: score += 8
    elif forks >= 1: score += 3

    # Metadata quality (up to 25 points)
    if metrics.get("description"): score += 5
    if metrics.get("license"): score += 5
    if metrics.get("topics"): score += 5
    if metrics.get("last_release"): score += 10

    return min(100, score)


# ======================================================================
# Semantic Scholar citation enrichment
# ======================================================================

def _enrich_citations(paper: Dict) -> None:
    """Update citation count from Semantic Scholar if current value is stale."""
    doi = paper.get("doi")
    pmid = paper.get("pmid")
    if not doi and not pmid:
        return

    current_count = paper.get("citation_count", 0) or 0

    s2_data = _fetch_semantic_scholar(doi=doi, pmid=pmid)
    if not s2_data:
        return

    s2_citations = s2_data.get("citation_count", 0)
    s2_influential = s2_data.get("influential_citation_count", 0)
    s2_id = s2_data.get("paper_id", "")

    # Update if S2 has more citations (fresher data)
    if s2_citations > current_count:
        paper["citation_count"] = s2_citations
        paper["citation_source"] = "semantic_scholar"

    # Always update influential count and S2 ID if we got them
    if s2_influential and not paper.get("influential_citation_count"):
        paper["influential_citation_count"] = s2_influential
    if s2_id and not paper.get("semantic_scholar_id"):
        paper["semantic_scholar_id"] = s2_id

    # Store fields of study for potential tag validation
    fields = s2_data.get("fields_of_study", [])
    if fields and not paper.get("fields_of_study"):
        paper["fields_of_study"] = fields


def _fetch_semantic_scholar(doi: str = None, pmid: str = None) -> Optional[Dict]:
    """Fetch paper metadata from the Semantic Scholar API."""
    global _last_s2_call

    if not doi and not pmid:
        return None

    base_url = "https://api.semanticscholar.org/graph/v1"
    fields = "paperId,citationCount,influentialCitationCount,fieldsOfStudy,s2FieldsOfStudy"

    headers = {}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY

    identifiers = []
    if doi:
        doi_clean = doi.strip()
        for prefix in ["https://doi.org/", "http://doi.org/", "doi:"]:
            if doi_clean.lower().startswith(prefix.lower()):
                doi_clean = doi_clean[len(prefix):]
        identifiers.append(f"DOI:{doi_clean}")
    if pmid:
        identifiers.append(f"PMID:{str(pmid).strip()}")

    for ident in identifiers:
        resp = _s2_request_with_retry(
            f"{base_url}/paper/{ident}",
            params={"fields": fields},
            headers=headers,
        )
        if resp is not None:
            data = resp.json()
            # Parse fields of study
            fields_of_study = data.get("fieldsOfStudy", []) or []
            s2_fields = data.get("s2FieldsOfStudy", []) or []
            if s2_fields:
                cats = list(dict.fromkeys(
                    item["category"] for item in s2_fields
                    if isinstance(item, dict) and item.get("category")
                ))
                if cats:
                    fields_of_study = cats

            return {
                "paper_id": data.get("paperId", ""),
                "citation_count": data.get("citationCount", 0),
                "influential_citation_count": data.get("influentialCitationCount", 0),
                "fields_of_study": fields_of_study,
            }

    return None


def _s2_request_with_retry(url: str, params: Dict, headers: Dict,
                           max_retries: int = 3) -> Optional["requests.Response"]:
    """Semantic Scholar request with exponential backoff on 429."""
    global _last_s2_call

    for attempt in range(max_retries + 1):
        # Rate limiting
        elapsed = time.time() - _last_s2_call
        if elapsed < _S2_DELAY:
            time.sleep(_S2_DELAY - elapsed)

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            _last_s2_call = time.time()

            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                if attempt < max_retries:
                    delay = 2 ** (attempt + 1)
                    logger.warning("Semantic Scholar rate limited, retrying in %ds...", delay)
                    time.sleep(delay)
                    continue
                logger.warning("Semantic Scholar rate limited, retries exhausted")
                return None
            if resp.status_code == 404:
                return None
            logger.debug("Semantic Scholar returned %d", resp.status_code)
            return None

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                time.sleep(2 ** (attempt + 1))
                continue
            return None
        except requests.exceptions.ConnectionError:
            if attempt < max_retries:
                time.sleep(2 ** (attempt + 1))
                continue
            return None

    return None


# ======================================================================
# CrossRef data repository discovery
# ======================================================================

def _enrich_crossref_repos(paper: Dict) -> None:
    """Find additional data repositories via CrossRef metadata."""
    doi = paper.get("doi")
    if not doi:
        return

    crossref_repos = _find_data_via_crossref(doi)
    if not crossref_repos:
        return

    existing = paper.get("repositories") or []
    if isinstance(existing, str):
        try:
            existing = json.loads(existing)
        except (json.JSONDecodeError, TypeError):
            existing = []

    # Merge: add CrossRef repos not already present
    existing_urls = {
        (r.get("url") or "").lower().rstrip("/")
        for r in existing if isinstance(r, dict)
    }

    for repo in crossref_repos:
        url = (repo.get("url") or "").lower().rstrip("/")
        if url and url not in existing_urls:
            existing.append(repo)
            existing_urls.add(url)

    paper["repositories"] = existing
    paper["has_data"] = bool(existing)


def _find_data_via_crossref(doi: str) -> List[Dict]:
    """Use CrossRef API to find data repository links for a paper."""
    doi_clean = doi.strip()
    for prefix in ["https://doi.org/", "http://doi.org/", "doi:"]:
        if doi_clean.lower().startswith(prefix.lower()):
            doi_clean = doi_clean[len(prefix):]

    try:
        resp = requests.get(
            f"https://api.crossref.org/works/{quote(doi_clean, safe='')}",
            headers={"User-Agent": "MicroHub/6.0 (mailto:support@microhub.io)"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []

        message = resp.json().get("message", {})
        repos: List[Dict] = []

        # Check 'link' field for data repositories
        data_domains = [
            "zenodo.org", "figshare.com", "dryad", "osf.io",
            "dataverse", "mendeley", "ebi.ac.uk", "ncbi.nlm.nih.gov/geo",
            "biostudies", "bioimage-archive", "empiar", "idr.openmicroscopy",
        ]
        domain_name_map = {
            "zenodo": "Zenodo",
            "figshare": "Figshare",
            "bioimage-archive": "BioImage Archive",
            "biostudies": "BioStudies",
            "empiar": "EMPIAR",
            "idr.openmicroscopy": "IDR",
            "datadryad": "Dryad",
            "osf.io": "OSF",
            "dataverse": "Dataverse",
            "mendeley": "Mendeley Data",
            "ncbi.nlm.nih.gov/geo": "GEO",
        }

        for link in message.get("link", []):
            link_url = link.get("URL", "")
            if not link_url:
                continue
            if any(d in link_url.lower() for d in data_domains):
                name = "Data Repository"
                for key, label in domain_name_map.items():
                    if key in link_url.lower():
                        name = label
                        break
                repos.append({
                    "url": link_url,
                    "name": name,
                    "source": "crossref",
                })

        # Check 'relation' field for related datasets (DataCite DOIs)
        for rel_type, items in message.get("relation", {}).items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_id = item.get("id", "")
                id_type = item.get("id-type", "")
                if id_type == "doi" and item_id:
                    if not item_id.startswith("http"):
                        item_id = f"https://doi.org/{item_id}"
                    repos.append({
                        "url": item_id,
                        "name": "Dataset (DOI)",
                        "source": "crossref-relation",
                    })

        # Also update citation count from CrossRef if available
        # (captured separately by _enrich_citations via S2)

        return repos

    except Exception:
        return []
