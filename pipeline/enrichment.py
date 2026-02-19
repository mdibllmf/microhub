"""
API-based enrichment for the cleanup step (step 3).

Ports the critical enrichment logic from the original cleanup_and_retag.py:
  - GitHub API:           Repository metadata, health scores, activity metrics
  - Semantic Scholar API: Citation updates, fields of study  (batch endpoint)
  - CrossRef API:         Additional data repositories via links & DOI relations

API keys are loaded from:
  1. Environment variables  (GITHUB_TOKEN, SEMANTIC_SCHOLAR_API_KEY)
  2. .env file in the project root

Usage in 3_clean.py:
    from pipeline.enrichment import Enricher
    enricher = Enricher()                   # loads keys from env / .env
    enricher.enrich_batch(papers)           # batch S2 + per-paper GH/CrossRef
"""

import json
import logging
import os
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

# Project root (one level up from pipeline/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env_file() -> Dict[str, str]:
    """Load key=value pairs from .env file in project root."""
    env_path = os.path.join(_PROJECT_ROOT, ".env")
    vals: Dict[str, str] = {}
    if not os.path.exists(env_path):
        return vals
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                value = value.strip().strip("'\"")
                vals[key.strip()] = value
    return vals


def _get_key(name: str) -> Optional[str]:
    """Get API key from environment or .env file."""
    val = os.environ.get(name)
    if val:
        return val
    return _load_env_file().get(name)


# ======================================================================
# Enricher class — manages API state and batch operations
# ======================================================================

class Enricher:
    """Stateful API enricher with rate limiting and batch support."""

    # S2 batch endpoint accepts up to 500 IDs per request
    S2_BATCH_SIZE = 500

    def __init__(self):
        self.github_token = _get_key("GITHUB_TOKEN")
        self.s2_api_key = _get_key("SEMANTIC_SCHOLAR_API_KEY")

        self._last_github_call = 0.0
        self._last_s2_call = 0.0
        self._github_delay = 0.5   # seconds between GH API calls
        # S2 free tier: 1 req/sec.  With key: 10 req/sec.
        self._s2_delay = 1.2 if not self.s2_api_key else 0.15

        # Track rate-limit state to avoid hammering after exhaustion
        self._s2_exhausted = False
        self._gh_exhausted = False

        if not self.github_token:
            logger.info("No GITHUB_TOKEN found — GitHub API calls will be "
                        "limited to 60/hour.  Set GITHUB_TOKEN in .env for 5000/hour.")
        if not self.s2_api_key:
            logger.info("No SEMANTIC_SCHOLAR_API_KEY found — S2 API calls will be "
                        "heavily rate-limited.  Set SEMANTIC_SCHOLAR_API_KEY in .env.")

    # ------------------------------------------------------------------
    # Public: batch enrichment (called from 3_clean.py)
    # ------------------------------------------------------------------

    def enrich_batch(self, papers: List[Dict], *,
                     fetch_github: bool = True,
                     fetch_citations: bool = True,
                     fetch_crossref_repos: bool = True) -> None:
        """Enrich a list of papers.  Mutates each paper in-place.

        Uses S2 batch endpoint for citations (500 papers per request),
        then per-paper GitHub and CrossRef calls only where needed.
        """
        if not HAS_REQUESTS:
            logger.warning("requests library not installed — skipping API enrichment")
            return

        # 1. Batch citation enrichment via Semantic Scholar
        if fetch_citations and not self._s2_exhausted:
            self._batch_enrich_citations(papers)

        # 2. Per-paper GitHub + CrossRef (only where needed)
        for paper in papers:
            if fetch_github and not self._gh_exhausted:
                self._enrich_github_tools(paper)
            if fetch_crossref_repos:
                self._enrich_crossref_repos(paper)

    # ------------------------------------------------------------------
    # Semantic Scholar — batch endpoint
    # ------------------------------------------------------------------

    def _batch_enrich_citations(self, papers: List[Dict]) -> None:
        """Update citations for all papers using S2 batch POST endpoint."""
        # Build list of papers that need citation updates, with their S2 IDs
        to_enrich: List[Dict] = []
        for paper in papers:
            doi = paper.get("doi")
            pmid = paper.get("pmid")
            if not doi and not pmid:
                continue
            # Build identifier — prefer DOI
            if doi:
                doi_clean = doi.strip()
                for prefix in ["https://doi.org/", "http://doi.org/", "doi:"]:
                    if doi_clean.lower().startswith(prefix.lower()):
                        doi_clean = doi_clean[len(prefix):]
                ident = f"DOI:{doi_clean}"
            else:
                ident = f"PMID:{str(pmid).strip()}"
            to_enrich.append({"paper": paper, "id": ident})

        if not to_enrich:
            return

        logger.info("  S2 batch: looking up citations for %d papers...", len(to_enrich))

        # Process in batches of 500
        for batch_start in range(0, len(to_enrich), self.S2_BATCH_SIZE):
            batch = to_enrich[batch_start:batch_start + self.S2_BATCH_SIZE]
            ids = [item["id"] for item in batch]

            result = self._s2_batch_request(ids)
            if result is None:
                # Rate limited or error — stop trying S2 for this run
                logger.warning("  S2 batch failed — skipping remaining citation lookups")
                self._s2_exhausted = True
                return

            # Map results back to papers
            for item, s2_data in zip(batch, result):
                if s2_data is None:
                    continue  # Paper not found in S2
                paper = item["paper"]
                self._apply_s2_data(paper, s2_data)

            done = min(batch_start + self.S2_BATCH_SIZE, len(to_enrich))
            logger.info("  S2 batch: %d / %d done", done, len(to_enrich))

    def _s2_batch_request(self, ids: List[str]) -> Optional[List[Optional[Dict]]]:
        """POST to S2 /paper/batch endpoint. Returns list aligned with input IDs."""
        url = "https://api.semanticscholar.org/graph/v1/paper/batch"
        fields = "paperId,citationCount,influentialCitationCount,fieldsOfStudy,s2FieldsOfStudy"

        headers = {"Content-Type": "application/json"}
        if self.s2_api_key:
            headers["x-api-key"] = self.s2_api_key

        for attempt in range(4):
            # Rate limiting
            elapsed = time.time() - self._last_s2_call
            if elapsed < self._s2_delay:
                time.sleep(self._s2_delay - elapsed)

            try:
                resp = requests.post(
                    url,
                    params={"fields": fields},
                    json={"ids": ids},
                    headers=headers,
                    timeout=30,
                )
                self._last_s2_call = time.time()

                if resp.status_code == 200:
                    return resp.json()  # list of dicts (or null for not-found)

                if resp.status_code == 429:
                    if attempt < 3:
                        delay = 2 ** (attempt + 1)  # 2, 4, 8s
                        logger.warning("  S2 batch rate limited (429), retrying in %ds...", delay)
                        time.sleep(delay)
                        continue
                    logger.warning("  S2 batch rate limited, retries exhausted")
                    return None

                logger.debug("  S2 batch returned %d", resp.status_code)
                return None

            except requests.exceptions.Timeout:
                if attempt < 3:
                    time.sleep(2 ** (attempt + 1))
                    continue
                return None
            except requests.exceptions.ConnectionError:
                if attempt < 3:
                    time.sleep(2 ** (attempt + 1))
                    continue
                return None

        return None

    @staticmethod
    def _apply_s2_data(paper: Dict, s2_data: Dict) -> None:
        """Apply Semantic Scholar data to a paper dict."""
        current_count = paper.get("citation_count", 0) or 0
        s2_citations = s2_data.get("citationCount", 0) or 0
        s2_influential = s2_data.get("influentialCitationCount", 0) or 0
        s2_id = s2_data.get("paperId", "")

        if s2_citations > current_count:
            paper["citation_count"] = s2_citations
            paper["citation_source"] = "semantic_scholar"

        if s2_influential and not paper.get("influential_citation_count"):
            paper["influential_citation_count"] = s2_influential
        if s2_id and not paper.get("semantic_scholar_id"):
            paper["semantic_scholar_id"] = s2_id

        # Fields of study
        fields_of_study = s2_data.get("fieldsOfStudy", []) or []
        s2_fields = s2_data.get("s2FieldsOfStudy", []) or []
        if s2_fields:
            cats = list(dict.fromkeys(
                item["category"] for item in s2_fields
                if isinstance(item, dict) and item.get("category")
            ))
            if cats:
                fields_of_study = cats
        if fields_of_study and not paper.get("fields_of_study"):
            paper["fields_of_study"] = fields_of_study

    # ------------------------------------------------------------------
    # GitHub API enrichment
    # ------------------------------------------------------------------

    def _enrich_github_tools(self, paper: Dict) -> None:
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
                metrics = self._fetch_github_metadata(full_name)
                if metrics is None and not self._gh_exhausted:
                    pass  # transient error, keep going
                elif metrics is not None:
                    for key, val in metrics.items():
                        if key == "health_score":
                            tool[key] = val
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

    def _fetch_github_metadata(self, full_name: str) -> Optional[Dict]:
        """Fetch repository metadata from the GitHub API."""
        full_name = full_name.strip().rstrip("/")
        if full_name.endswith(".git"):
            full_name = full_name[:-4]

        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        # Rate limiting
        elapsed = time.time() - self._last_github_call
        if elapsed < self._github_delay:
            time.sleep(self._github_delay - elapsed)

        try:
            resp = requests.get(
                f"https://api.github.com/repos/{full_name}",
                headers=headers, timeout=15,
            )
            self._last_github_call = time.time()

            if resp.status_code == 404:
                return {"exists": False, "full_name": full_name}
            if resp.status_code == 403:
                logger.warning("GitHub API rate limited — stopping GitHub calls for this run")
                self._gh_exhausted = True
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

    # ------------------------------------------------------------------
    # CrossRef data repository discovery
    # ------------------------------------------------------------------

    def _enrich_crossref_repos(self, paper: Dict) -> None:
        """Find additional data repositories via CrossRef metadata."""
        doi = paper.get("doi")
        if not doi:
            return

        crossref_repos = self._find_data_via_crossref(doi)
        if not crossref_repos:
            return

        existing = paper.get("repositories") or []
        if isinstance(existing, str):
            try:
                existing = json.loads(existing)
            except (json.JSONDecodeError, TypeError):
                existing = []

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

    @staticmethod
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

            data_domains = [
                "zenodo.org", "figshare.com", "dryad", "osf.io",
                "dataverse", "mendeley", "ebi.ac.uk", "ncbi.nlm.nih.gov/geo",
                "biostudies", "bioimage-archive", "empiar", "idr.openmicroscopy",
                "openmicroscopy.org", "codeocean.com", "ssbd.riken.jp",
                "10.5281/zenodo", "10.6084/m9.figshare", "10.5061/dryad",
                "10.17605/OSF.IO",
                "rcsb.org", "github.com", "gitlab.com", "bitbucket.org",
                "cellimagelibrary.org", "bioimage.io",
                "ncbi.nlm.nih.gov/sra", "ncbi.nlm.nih.gov/bioproject",
                "dandiarchive.org", "openneuro.org", "neuromorpho.org",
                "synapse.org", "jcb-dataviewer.rupress.org",
            ]
            domain_name_map = {
                "zenodo": "Zenodo",
                "figshare": "Figshare",
                "bioimage-archive": "BioImage Archive",
                "biostudies": "BioStudies",
                "empiar": "EMPIAR",
                "idr.openmicroscopy": "IDR",
                "openmicroscopy.org": "OMERO",
                "datadryad": "Dryad",
                "osf.io": "OSF",
                "dataverse": "Dataverse",
                "mendeley": "Mendeley Data",
                "ncbi.nlm.nih.gov/geo": "GEO",
                "ncbi.nlm.nih.gov/sra": "SRA",
                "ncbi.nlm.nih.gov/bioproject": "SRA",
                "codeocean": "Code Ocean",
                "ssbd.riken": "SSBD",
                "10.5281/zenodo": "Zenodo",
                "10.6084/m9.figshare": "Figshare",
                "10.5061/dryad": "Dryad",
                "10.17605/OSF.IO": "OSF",
                "rcsb.org": "PDB",
                "github.com": "GitHub",
                "gitlab.com": "GitLab",
                "bitbucket.org": "Bitbucket",
                "cellimagelibrary": "Cell Image Library",
                "bioimage.io": "BioImage Model Zoo",
                "dandiarchive": "DANDI",
                "openneuro": "OpenNeuro",
                "neuromorpho": "NeuroMorpho",
                "synapse.org": "Synapse",
                "jcb-dataviewer": "JCB DataViewer",
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

            return repos

        except Exception:
            return []


# ======================================================================
# Health score computation (standalone)
# ======================================================================

def compute_github_health_score(metrics: Dict) -> int:
    """Compute a 0-100 health score for a GitHub repository."""
    if not metrics.get("exists", True):
        return 0
    if metrics.get("is_archived", False):
        return 10

    score = 0

    stars = metrics.get("stars", 0)
    if stars >= 1000: score += 25
    elif stars >= 500: score += 22
    elif stars >= 100: score += 18
    elif stars >= 50: score += 14
    elif stars >= 10: score += 10
    elif stars >= 1: score += 5

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

    forks = metrics.get("forks", 0)
    if forks >= 100: score += 15
    elif forks >= 50: score += 12
    elif forks >= 10: score += 8
    elif forks >= 1: score += 3

    if metrics.get("description"): score += 5
    if metrics.get("license"): score += 5
    if metrics.get("topics"): score += 5
    if metrics.get("last_release"): score += 10

    return min(100, score)
