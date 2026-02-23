"""
API-based enrichment for the cleanup step (step 3).

Ports the critical enrichment logic from the original cleanup_and_retag.py:
  - OpenAlex API:         First-call enrichment (institutions, topics, citations, OA)
  - GitHub API:           Repository metadata, health scores, activity metrics
  - Semantic Scholar API: Citation updates, fields of study  (batch endpoint)
  - CrossRef API:         Additional data repositories via links & DOI relations
  - DataCite + OpenAIRE:  Dataset-publication link discovery
  - ROR v2 API:           Dynamic institution affiliation matching

API keys are loaded from:
  1. Environment variables  (GITHUB_TOKEN, SEMANTIC_SCHOLAR_API_KEY, OPENALEX_API_KEY)
  2. .env file in the project root

Usage in 3_clean.py:
    from pipeline.enrichment import Enricher
    enricher = Enricher()                   # loads keys from env / .env
    enricher.enrich_batch(papers)           # batch OA + S2 + per-paper GH/CrossRef
"""

import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def __init__(self, max_workers: int = 4, ror_local_path: Optional[str] = None,
                 local_lookup=None):
        self.github_token = _get_key("GITHUB_TOKEN")
        self.s2_api_key = _get_key("SEMANTIC_SCHOLAR_API_KEY")
        self.openalex_email = _get_key("OPENALEX_EMAIL") or "microhub@example.com"
        self.openalex_api_key = _get_key("OPENALEX_API_KEY")
        self.ror_client_id = _get_key("ROR_CLIENT_ID")
        self._ror_local_path = ror_local_path
        self._local_lookup = local_lookup

        self._last_github_call = 0.0
        self._last_s2_call = 0.0
        self._github_delay = 0.5   # seconds between GH API calls
        # S2 free tier: 1 req/sec.  With key: 10 req/sec.
        self._s2_delay = 1.2 if not self.s2_api_key else 0.15

        # Track rate-limit state to avoid hammering after exhaustion
        self._s2_exhausted = False
        self._gh_exhausted = False

        # Lazy-initialize optional agents
        self._openalex_agent = None
        self._datacite_agent = None
        self._ror_client = None

        # Parallel enrichment
        self._max_workers = max(1, max_workers)
        self._github_lock = threading.Lock()
        self._init_lock = threading.Lock()

        if not self.github_token:
            logger.info("No GITHUB_TOKEN found — GitHub API calls will be "
                        "limited to 60/hour.  Set GITHUB_TOKEN in .env for 5000/hour.")
        if not self.s2_api_key:
            logger.info("No SEMANTIC_SCHOLAR_API_KEY found — S2 API calls will be "
                        "heavily rate-limited.  Set SEMANTIC_SCHOLAR_API_KEY in .env.")

    @property
    def openalex_agent(self):
        """Lazy-initialize OpenAlex agent."""
        if self._openalex_agent is None:
            from .agents.openalex_agent import OpenAlexAgent
            self._openalex_agent = OpenAlexAgent(
                email=self.openalex_email,
                api_key=self.openalex_api_key,
            )
        return self._openalex_agent

    @property
    def datacite_agent(self):
        """Lazy-initialize DataCite linker agent (thread-safe)."""
        if self._datacite_agent is None:
            with self._init_lock:
                if self._datacite_agent is None:
                    from .agents.datacite_linker_agent import DataCiteLinkerAgent
                    self._datacite_agent = DataCiteLinkerAgent()
        return self._datacite_agent

    @property
    def ror_client(self):
        """Lazy-initialize ROR v2 client (thread-safe)."""
        if self._ror_client is None:
            with self._init_lock:
                if self._ror_client is None:
                    from .validation.ror_v2_client import RORv2Client
                    self._ror_client = RORv2Client(
                        client_id=self.ror_client_id,
                        local_path=self._ror_local_path,
                        local_lookup=self._local_lookup,
                    )
        return self._ror_client

    @property
    def crossref_agent(self):
        """Lazy-initialize CrossRef validation agent (thread-safe)."""
        if not hasattr(self, "_crossref_agent") or self._crossref_agent is None:
            with self._init_lock:
                if not hasattr(self, "_crossref_agent") or self._crossref_agent is None:
                    from .agents.crossref_agent import CrossRefValidationAgent
                    self._crossref_agent = CrossRefValidationAgent(
                        s2_api_key=self.s2_api_key
                    )
        return self._crossref_agent

    @property
    def doi_linker_agent(self):
        """Lazy-initialize DOI-Repository linker agent (thread-safe)."""
        if not hasattr(self, "_doi_linker_agent") or self._doi_linker_agent is None:
            with self._init_lock:
                if not hasattr(self, "_doi_linker_agent") or self._doi_linker_agent is None:
                    from .agents.doi_linker_agent import DOILinkerAgent
                    self._doi_linker_agent = DOILinkerAgent(
                        github_token=self.github_token
                    )
        return self._doi_linker_agent

    # ------------------------------------------------------------------
    # Public: batch enrichment (called from 3_clean.py)
    # ------------------------------------------------------------------

    def enrich_batch(self, papers: List[Dict], *,
                     fetch_openalex: bool = True,
                     fetch_github: bool = True,
                     fetch_citations: bool = True,
                     fetch_crossref_repos: bool = True,
                     fetch_datacite: bool = True,
                     fetch_ror: bool = True,
                     fetch_crossref_metadata: bool = True,
                     validate_repo_dois: bool = True) -> None:
        """Enrich a list of papers.  Mutates each paper in-place.

        Pipeline order follows the recommended architecture:
          1. OpenAlex first-call enrichment (institutions, topics, citations, OA)
          2. Semantic Scholar batch citations (supplemental, 500/request)
          3. Per-paper GitHub, CrossRef, DataCite, ROR (where needed)
        """
        if not HAS_REQUESTS:
            logger.warning("requests library not installed — skipping API enrichment")
            return

        # 1. OpenAlex first-call enrichment (free singleton lookups)
        if fetch_openalex:
            self._batch_enrich_openalex(papers)

        # 2. Batch citation enrichment via Semantic Scholar (supplemental)
        if fetch_citations and not self._s2_exhausted:
            self._batch_enrich_citations(papers)

        # 3. Per-paper GitHub + CrossRef + DataCite + ROR — parallel workers
        any_per_paper = (
            (fetch_github and not self._gh_exhausted)
            or fetch_crossref_repos or fetch_datacite or fetch_ror
            or fetch_crossref_metadata or validate_repo_dois
        )
        if any_per_paper and papers:
            def _enrich_one(paper):
                if fetch_github and not self._gh_exhausted:
                    self._enrich_github_tools(paper)
                if fetch_crossref_repos:
                    self._enrich_crossref_repos(paper)
                if fetch_crossref_metadata:
                    self._enrich_crossref_metadata(paper)
                if fetch_datacite:
                    self._enrich_datacite(paper)
                if fetch_ror:
                    self._enrich_ror_affiliations(paper)
                if validate_repo_dois:
                    self._validate_repo_dois(paper)

            if self._max_workers <= 1:
                for paper in papers:
                    _enrich_one(paper)
            else:
                logger.info("  Per-paper API enrichment: %d papers × %d workers",
                            len(papers), self._max_workers)
                with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                    futs = {pool.submit(_enrich_one, p): p for p in papers}
                    done_count = 0
                    for fut in as_completed(futs):
                        done_count += 1
                        try:
                            fut.result()
                        except Exception as exc:
                            pmid = futs[fut].get("pmid", "?")
                            logger.warning("  Enrichment error for PMID %s: %s",
                                           pmid, exc)
                        if done_count % 50 == 0 or done_count == len(futs):
                            logger.info("  Per-paper enrichment: %d / %d done",
                                        done_count, len(futs))

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

    def _github_rate_wait(self):
        """Thread-safe rate limit wait for GitHub API."""
        with self._github_lock:
            elapsed = time.time() - self._last_github_call
            if elapsed < self._github_delay:
                time.sleep(self._github_delay - elapsed)
            self._last_github_call = time.time()

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

        # Set validation_status on each tool (from GitHubHealthAgent logic)
        for tool in updated:
            if isinstance(tool, dict):
                if tool.get("exists") is False:
                    tool["validation_status"] = "dead"
                elif tool.get("is_archived"):
                    tool["validation_status"] = "archived"
                elif tool.get("health_score", 0) > 0:
                    tool["validation_status"] = "active"

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

        self._github_rate_wait()

        try:
            resp = requests.get(
                f"https://api.github.com/repos/{full_name}",
                headers=headers, timeout=15,
            )

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
                self._github_rate_wait()
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
                self._github_rate_wait()
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

    # ------------------------------------------------------------------
    # OpenAlex first-call enrichment
    # ------------------------------------------------------------------

    def _batch_enrich_openalex(self, papers: List[Dict]) -> None:
        """Enrich papers using OpenAlex API (first-call enrichment).

        OpenAlex provides institution resolution (ROR), topics, citations,
        OA status, and referenced works in a single API call per paper.
        Singleton lookups are free.
        """
        dois = []
        doi_to_papers: Dict[str, List[Dict]] = {}
        for paper in papers:
            doi = paper.get("doi")
            if doi:
                doi_clean = self._clean_doi_str(doi)
                if doi_clean:
                    dois.append(doi_clean)
                    doi_to_papers.setdefault(doi_clean, []).append(paper)

        if not dois:
            return

        logger.info("  OpenAlex: enriching %d papers...", len(dois))

        # Batch in groups of 50
        for i in range(0, len(dois), 50):
            batch = dois[i:i + 50]
            try:
                results = self.openalex_agent.enrich_batch(batch)
            except Exception as exc:
                logger.warning("  OpenAlex batch error: %s", exc)
                continue

            for doi_key, oa_data in results.items():
                for paper in doi_to_papers.get(doi_key, []):
                    self._apply_openalex_data(paper, oa_data)

        done = len(dois)
        logger.info("  OpenAlex: enriched %d papers", done)

    @staticmethod
    def _apply_openalex_data(paper: Dict, oa_data: Dict) -> None:
        """Apply OpenAlex data to a paper dict."""
        # Citations — use OpenAlex if higher than existing
        oa_citations = oa_data.get("cited_by_count", 0) or 0
        current = paper.get("citation_count", 0) or 0
        if oa_citations > current:
            paper["citation_count"] = oa_citations
            paper["citation_source"] = "openalex"

        # FWCI (Field-Weighted Citation Impact)
        fwci = oa_data.get("fwci")
        if fwci is not None:
            paper["fwci"] = fwci

        # OA status
        if oa_data.get("is_oa") and not paper.get("oa_status"):
            paper["oa_status"] = oa_data.get("oa_status", "")
            paper["oa_url"] = oa_data.get("oa_url", "")

        # OpenAlex ID
        if oa_data.get("openalex_id") and not paper.get("openalex_id"):
            paper["openalex_id"] = oa_data["openalex_id"]

        # PMC ID (if we didn't have it)
        if oa_data.get("pmcid") and not paper.get("pmc_id"):
            paper["pmc_id"] = oa_data["pmcid"]

        # Topics (4-level hierarchy)
        topics = oa_data.get("topics", [])
        if topics and not paper.get("openalex_topics"):
            paper["openalex_topics"] = topics

        # Institutions with ROR IDs
        institutions = oa_data.get("institutions", [])
        if institutions and not paper.get("openalex_institutions"):
            paper["openalex_institutions"] = institutions
            # Also populate ROR IDs if not already present
            existing_rors = paper.get("rors") or []
            seen_rors = {r.get("id", "").lower() for r in existing_rors if isinstance(r, dict)}
            for inst in institutions:
                ror_id = inst.get("ror_id", "")
                if ror_id and ror_id.lower() not in seen_rors:
                    existing_rors.append({
                        "id": ror_id,
                        "url": f"https://ror.org/{ror_id}" if not ror_id.startswith("http") else ror_id,
                        "name": inst.get("name", ""),
                        "source": "openalex",
                    })
                    seen_rors.add(ror_id.lower())
            if existing_rors:
                paper["rors"] = existing_rors

        # Fields of study (from OpenAlex topics)
        if topics and not paper.get("fields_of_study"):
            fields = list(dict.fromkeys(
                t.get("field", "") for t in topics if t.get("field")
            ))
            if fields:
                paper["fields_of_study"] = fields

    # ------------------------------------------------------------------
    # DataCite + OpenAIRE dataset linking
    # ------------------------------------------------------------------

    def _enrich_datacite(self, paper: Dict) -> None:
        """Discover dataset links via DataCite and OpenAIRE."""
        doi = paper.get("doi")
        data_avail = paper.get("data_availability", "") or ""
        if not doi and not data_avail:
            return

        try:
            links = self.datacite_agent.find_dataset_links(
                doi=doi, text=data_avail
            )
        except Exception as exc:
            logger.debug("DataCite error for %s: %s", doi, exc)
            return

        if not links:
            return

        existing = paper.get("repositories") or []
        if isinstance(existing, str):
            try:
                existing = json.loads(existing)
            except (json.JSONDecodeError, TypeError):
                existing = []

        existing_urls = set()
        existing_accessions = set()
        for r in existing:
            if isinstance(r, dict):
                url = (r.get("url") or "").lower().rstrip("/")
                if url:
                    existing_urls.add(url)
                acc = (r.get("accession") or "").lower()
                name = (r.get("name") or "").lower()
                if acc:
                    existing_accessions.add(f"{name}:{acc}")
                    existing_accessions.add(acc)

        for link in links:
            link_url = (link.get("url") or "").lower().rstrip("/")
            link_acc = (link.get("accession") or "").lower()
            link_repo = (link.get("repository") or "").lower()

            # Skip if URL already exists
            if link_url and link_url in existing_urls:
                continue
            # Skip if accession already exists (with or without repo prefix)
            if link_acc and (link_acc in existing_accessions
                            or f"{link_repo}:{link_acc}" in existing_accessions):
                continue

            existing.append({
                "name": link.get("repository", "Dataset"),
                "url": link.get("url", ""),
                "accession": link.get("accession", ""),
                "source": link.get("source", "datacite"),
            })
            if link_url:
                existing_urls.add(link_url)
            if link_acc:
                existing_accessions.add(link_acc)
                existing_accessions.add(f"{link_repo}:{link_acc}")

        paper["repositories"] = existing
        paper["has_data"] = bool(existing)

    # ------------------------------------------------------------------
    # ROR v2 dynamic affiliation matching
    # ------------------------------------------------------------------

    def _enrich_ror_affiliations(self, paper: Dict) -> None:
        """Match paper affiliations to ROR IDs using the ROR v2 API."""
        affiliations = paper.get("affiliations")
        if not affiliations:
            return

        if isinstance(affiliations, str):
            affiliations = [affiliations]
        if not isinstance(affiliations, list):
            return

        existing_rors = paper.get("rors") or []
        seen_rors = {r.get("id", "").lower() for r in existing_rors if isinstance(r, dict)}

        for aff in affiliations:
            if not isinstance(aff, str) or not aff.strip():
                continue
            try:
                match = self.ror_client.match_affiliation(aff)
            except Exception:
                continue

            if match and match.get("ror_id") and match["ror_id"].lower() not in seen_rors:
                existing_rors.append({
                    "id": match["ror_id"],
                    "url": match.get("ror_url", ""),
                    "name": match.get("name", ""),
                    "country": match.get("country", ""),
                    "source": "ror_v2_affiliation",
                })
                seen_rors.add(match["ror_id"].lower())

        if existing_rors:
            paper["rors"] = existing_rors

    # ------------------------------------------------------------------
    # CrossRef metadata gap-filling (via CrossRefValidationAgent)
    # ------------------------------------------------------------------

    def _enrich_crossref_metadata(self, paper: Dict) -> None:
        """Fill metadata gaps (journal, year, license, funders) via CrossRef.

        Delegates to CrossRefValidationAgent which also queries S2 for
        citation counts and fields of study.
        """
        doi = paper.get("doi")
        if not doi:
            return
        try:
            self.crossref_agent.validate(paper)
        except Exception as exc:
            logger.debug("CrossRef metadata error for %s: %s", doi, exc)

    # ------------------------------------------------------------------
    # DOI-Repository link validation (via DOILinkerAgent)
    # ------------------------------------------------------------------

    def _validate_repo_dois(self, paper: Dict) -> None:
        """Validate repository URLs against paper DOIs.

        Delegates to DOILinkerAgent which checks Zenodo, Figshare, GitHub,
        Dryad for DOI cross-references and URL liveness.
        """
        repos = paper.get("repositories")
        if not repos or not isinstance(repos, list):
            return
        doi = paper.get("doi")
        if not doi:
            return
        try:
            self.doi_linker_agent.validate(paper)
        except Exception as exc:
            logger.debug("DOI linker error for %s: %s", doi, exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_doi_str(doi: str) -> str:
        """Clean a DOI string."""
        doi = (doi or "").strip()
        for prefix in ["https://doi.org/", "http://doi.org/", "doi:", "DOI:"]:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix):]
        return doi.strip()

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
