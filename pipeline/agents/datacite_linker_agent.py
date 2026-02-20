"""
DataCite + OpenAIRE dataset-publication linker agent.

Discovers paper-dataset links through two complementary approaches:
  1. DataCite REST API: Resolves DataCite DOIs (Zenodo, Figshare, Dryad)
     and traverses relatedIdentifiers for bidirectional paper-dataset links.
  2. OpenAIRE ScholeXplorer: Aggregates ~40M dataset-publication links
     from DataCite, Crossref, and institutional repositories.

Also applies regex patterns to data availability statements for
biomedical-specific accession formats (EMPIAR, EMDB, PDB, GEO, SRA, etc.).

Usage:
    from pipeline.agents.datacite_linker_agent import DataCiteLinkerAgent
    agent = DataCiteLinkerAgent()
    links = agent.find_dataset_links(doi="10.1038/...", text="...")
"""

import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional, Set
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_DATACITE_BASE = "https://api.datacite.org"
_SCHOLEXPLORER_BASE = "https://api.scholexplorer.openaire.eu/v2/Links"

# DataCite DOI prefixes for major data repositories
_DATACITE_PREFIXES = {
    "10.5281": "Zenodo",
    "10.6084": "Figshare",
    "10.5061": "Dryad",
    "10.5524": "GigaDB",
    "10.17632": "Mendeley Data",
    "10.7910": "Dataverse",
    "10.48550": "arXiv",
}

# Biomedical-specific accession patterns
_ACCESSION_PATTERNS = [
    # EMPIAR: Electron Microscopy Public Image Archive
    (re.compile(r"\b(EMPIAR[- ]?\d{5,})\b", re.I), "EMPIAR",
     "https://www.ebi.ac.uk/empiar/entry/{id}"),
    # EMDB: Electron Microscopy Data Bank
    (re.compile(r"\b(EMD[- ]?\d{4,})\b", re.I), "EMDB",
     "https://www.ebi.ac.uk/emdb/entry/{id}"),
    # GEO: Gene Expression Omnibus
    (re.compile(r"\b(GSE\d{4,})\b"), "GEO",
     "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={id}"),
    # SRA: Sequence Read Archive (project)
    (re.compile(r"\b(SRP\d{6,})\b"), "SRA",
     "https://www.ncbi.nlm.nih.gov/sra/?term={id}"),
    # SRA run
    (re.compile(r"\b(SRR\d{6,})\b"), "SRA",
     "https://www.ncbi.nlm.nih.gov/sra/?term={id}"),
    # SRA experiment
    (re.compile(r"\b(SRX\d{6,})\b"), "SRA",
     "https://www.ncbi.nlm.nih.gov/sra/?term={id}"),
    # BioProject
    (re.compile(r"\b(PRJNA\d{4,})\b"), "BioProject",
     "https://www.ncbi.nlm.nih.gov/bioproject/{id}"),
    # BioImage Archive (must come before BioStudies -- S-BIAD is a subset of S-B*)
    (re.compile(r"\b(S-BIAD\d+)\b"), "BioImage Archive",
     "https://www.ebi.ac.uk/biostudies/BioImages/studies/{id}"),
    # BioStudies (general pattern, after BioImage Archive)
    (re.compile(r"\b(S-B[A-Z]{2,4}\d+)\b"), "BioStudies",
     "https://www.ebi.ac.uk/biostudies/studies/{id}"),
    # ArrayExpress
    (re.compile(r"\b(E-[A-Z]{4}-\d+)\b"), "ArrayExpress",
     "https://www.ebi.ac.uk/arrayexpress/experiments/{id}"),
    # ProteomeXchange / PRIDE
    (re.compile(r"\b(PXD\d{6,})\b"), "ProteomeXchange",
     "https://www.ebi.ac.uk/pride/archive/projects/{id}"),
    # dbGaP
    (re.compile(r"\b(phs\d{6,})\b"), "dbGaP",
     "https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id={id}"),
    # IDR
    (re.compile(r"\b(idr\d{4,})\b", re.I), "IDR",
     "https://idr.openmicroscopy.org/search/?query=Name:{id}"),
]

# PDB is handled separately due to high false-positive rate
_PDB_PATTERN = re.compile(r"\b(\d[A-Za-z0-9]{3})\b")

# Relation types that indicate a dataset link
_DATASET_RELATIONS = {
    "IsSupplementTo", "IsReferencedBy", "IsCitedBy",
    "IsPartOf", "HasPart", "IsVersionOf",
    "IsDerivedFrom", "IsSourceOf", "IsIdenticalTo",
}


class DataCiteLinkerAgent:
    """Discover dataset links through DataCite, OpenAIRE, and text patterns."""

    name = "datacite_linker"

    def __init__(self):
        self._last_call = 0.0
        self._delay = 0.3
        self._lock = threading.Lock()

    def find_dataset_links(self, *, doi: str = None,
                           text: str = None) -> List[Dict[str, Any]]:
        """Find all dataset links for a paper.

        Parameters
        ----------
        doi : str, optional
            Paper DOI for API-based discovery.
        text : str, optional
            Data availability statement or full text for pattern matching.

        Returns
        -------
        list of dict
            Each dict has keys: accession, repository, url, source, relation_type.
        """
        links: List[Dict[str, Any]] = []
        seen: Set[str] = set()

        # 1. DataCite: Resolve DOI and check relatedIdentifiers
        if doi:
            dc_links = self._query_datacite(doi)
            for link in dc_links:
                key = link.get("accession", link.get("url", "")).lower()
                if key and key not in seen:
                    seen.add(key)
                    links.append(link)

        # 2. OpenAIRE ScholeXplorer: Find dataset-publication links
        if doi:
            scholex_links = self._query_scholexplorer(doi)
            for link in scholex_links:
                key = link.get("accession", link.get("url", "")).lower()
                if key and key not in seen:
                    seen.add(key)
                    links.append(link)

        # 3. Text-based accession detection
        if text:
            text_links = self._extract_accessions(text)
            for link in text_links:
                key = link.get("accession", "").lower()
                if key and key not in seen:
                    seen.add(key)
                    links.append(link)

        return links

    # ------------------------------------------------------------------
    # DataCite API
    # ------------------------------------------------------------------

    def _query_datacite(self, doi: str) -> List[Dict[str, Any]]:
        """Query DataCite for a DOI's related datasets."""
        if not HAS_REQUESTS:
            return []

        doi = self._clean_doi(doi)
        if not doi:
            return []

        self._rate_limit()
        try:
            resp = requests.get(
                f"{_DATACITE_BASE}/dois/{quote(doi, safe='')}",
                timeout=15,
            )

            if resp.status_code != 200:
                return []

            data = resp.json().get("data", {})
            attrs = data.get("attributes", {})

            links: List[Dict[str, Any]] = []

            # Check if this DOI itself is a dataset
            resource_type = (attrs.get("types", {}).get(
                "resourceTypeGeneral", ""
            )).lower()

            if resource_type == "dataset":
                links.append({
                    "accession": doi,
                    "repository": self._repo_from_doi_prefix(doi),
                    "url": f"https://doi.org/{doi}",
                    "source": "datacite",
                    "relation_type": "self_dataset",
                    "title": attrs.get("titles", [{}])[0].get("title", "")
                    if attrs.get("titles") else "",
                })

            # Traverse relatedIdentifiers
            for rel in attrs.get("relatedIdentifiers", []):
                rel_type = rel.get("relationType", "")
                rel_id = rel.get("relatedIdentifier", "")
                rel_id_type = rel.get("relatedIdentifierType", "")

                if not rel_id or not rel_type:
                    continue

                if rel_type in _DATASET_RELATIONS:
                    url = rel_id
                    if rel_id_type.upper() == "DOI" and not rel_id.startswith("http"):
                        url = f"https://doi.org/{rel_id}"
                    elif rel_id_type.upper() == "URL":
                        pass  # already a URL
                    elif rel_id_type.upper() == "PMID":
                        url = f"https://pubmed.ncbi.nlm.nih.gov/{rel_id}"

                    links.append({
                        "accession": rel_id,
                        "repository": self._repo_from_doi_prefix(rel_id)
                        if rel_id_type.upper() == "DOI" else "Unknown",
                        "url": url,
                        "source": "datacite",
                        "relation_type": rel_type,
                    })

            return links

        except Exception as exc:
            logger.debug("DataCite error for %s: %s", doi, exc)
            return []

    # ------------------------------------------------------------------
    # OpenAIRE ScholeXplorer
    # ------------------------------------------------------------------

    def _query_scholexplorer(self, doi: str) -> List[Dict[str, Any]]:
        """Query OpenAIRE ScholeXplorer for dataset-publication links."""
        if not HAS_REQUESTS:
            return []

        doi = self._clean_doi(doi)
        if not doi:
            return []

        self._rate_limit()
        try:
            resp = requests.get(
                _SCHOLEXPLORER_BASE,
                params={
                    "sourcePid": doi,
                    "sourcePidType": "doi",
                    "targetType": "dataset",
                    "page": 0,
                    "size": 50,
                },
                timeout=15,
            )

            if resp.status_code != 200:
                return []

            data = resp.json()
            links: List[Dict[str, Any]] = []

            for result in data.get("result", []):
                target = result.get("target", {})
                target_type = target.get("objectType", "").lower()
                if target_type != "dataset":
                    continue

                identifiers = target.get("identifiers", [])
                target_id = ""
                for ident in identifiers:
                    if isinstance(ident, dict):
                        target_id = ident.get("identifier", "")
                        break

                target_title = (target.get("title") or "")
                publisher = (target.get("publisher", []) or [])
                pub_name = publisher[0].get("name", "") if publisher else ""

                if target_id:
                    url = target_id
                    if not url.startswith("http"):
                        url = f"https://doi.org/{target_id}"

                    links.append({
                        "accession": target_id,
                        "repository": pub_name or self._repo_from_doi_prefix(target_id),
                        "url": url,
                        "source": "scholexplorer",
                        "relation_type": result.get("linkProvider", [{}])[0].get(
                            "name", "link") if result.get("linkProvider") else "link",
                        "title": target_title,
                    })

            return links

        except Exception as exc:
            logger.debug("ScholeXplorer error for %s: %s", doi, exc)
            return []

    # ------------------------------------------------------------------
    # Text-based accession extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_accessions(text: str) -> List[Dict[str, Any]]:
        """Extract biomedical repository accession IDs from text."""
        links: List[Dict[str, Any]] = []
        seen: Set[str] = set()

        for pattern, repo_name, url_template in _ACCESSION_PATTERNS:
            for m in pattern.finditer(text):
                accession = m.group(1)
                # Normalize: remove spaces/hyphens for consistency
                normalized = accession.replace(" ", "").replace("-", "-")
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)

                url = url_template.format(id=normalized)
                links.append({
                    "accession": normalized,
                    "repository": repo_name,
                    "url": url,
                    "source": "text_pattern",
                    "relation_type": "mentioned",
                })

        return links

    # ------------------------------------------------------------------
    # DOI classification
    # ------------------------------------------------------------------

    def is_dataset_doi(self, doi: str) -> bool:
        """Check if a DOI belongs to a known dataset repository."""
        doi = self._clean_doi(doi)
        if not doi:
            return False

        # Check known DataCite prefixes
        for prefix in _DATACITE_PREFIXES:
            if doi.startswith(prefix):
                return True

        # Query DataCite to check resourceTypeGeneral
        if HAS_REQUESTS:
            self._rate_limit()
            try:
                resp = requests.get(
                    f"{_DATACITE_BASE}/dois/{quote(doi, safe='')}",
                    timeout=10,
                )
                if resp.status_code == 200:
                    resource_type = (
                        resp.json()
                        .get("data", {})
                        .get("attributes", {})
                        .get("types", {})
                        .get("resourceTypeGeneral", "")
                    )
                    return resource_type.lower() == "dataset"
            except Exception:
                pass

        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _repo_from_doi_prefix(doi: str) -> str:
        """Identify repository from DOI prefix."""
        doi = (doi or "").strip()
        for prefix, name in _DATACITE_PREFIXES.items():
            if doi.startswith(prefix):
                return name
        return "Unknown"

    def _rate_limit(self):
        with self._lock:
            elapsed = time.time() - self._last_call
            if elapsed < self._delay:
                time.sleep(self._delay - elapsed)
            self._last_call = time.time()

    @staticmethod
    def _clean_doi(doi: str) -> str:
        doi = (doi or "").strip()
        for prefix in ["https://doi.org/", "http://doi.org/", "doi:", "DOI:"]:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix):]
        return doi.strip()
