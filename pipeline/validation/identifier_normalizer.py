"""
Identifier normalizer — ensures consistency of DOIs, RRIDs, RORs,
repository URLs, and accession numbers across the entire dataset.

Problems this solves:
  - DOI variants: "10.1234/foo", "doi:10.1234/foo", "https://doi.org/10.1234/foo"
  - RRID variants: "RRID:AB_123", "RRID: AB_123", "rrid:ab_123"
  - ROR variants: "https://ror.org/0xxx", "ror.org/0xxx", "ROR: 0xxx"
  - Repository URLs: trailing slashes, .git suffix, http vs https, www prefix
  - Accession IDs: "EMPIAR-10234" vs "EMPIAR 10234" vs "EMPIAR10234"

Usage:
    normalizer = IdentifierNormalizer()
    normalizer.normalize_paper(paper)  # mutates in-place
"""

import re
from typing import Any, Dict, List, Optional


class IdentifierNormalizer:
    """Canonicalize all identifiers in a paper dict."""

    def normalize_paper(self, paper: Dict[str, Any]) -> None:
        """Normalize all identifiers in a paper.  Mutates in-place."""
        self._normalize_doi(paper)
        self._normalize_pmid(paper)
        self._normalize_rrids(paper)
        self._normalize_rors(paper)
        self._normalize_repositories(paper)
        self._normalize_github_tools(paper)
        self._normalize_accession_ids(paper)

    # ------------------------------------------------------------------
    # DOI
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_doi(paper: Dict) -> None:
        """Normalize DOI to bare form: 10.xxxx/yyyy"""
        doi = paper.get("doi")
        if not doi or not isinstance(doi, str):
            return

        doi = doi.strip()
        for prefix in [
            "https://doi.org/", "http://doi.org/",
            "https://dx.doi.org/", "http://dx.doi.org/",
            "doi:", "DOI:",
        ]:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix):]
                break

        # Remove trailing periods, commas, spaces
        doi = doi.rstrip(" .,;")
        paper["doi"] = doi

    # ------------------------------------------------------------------
    # PMID
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_pmid(paper: Dict) -> None:
        """Normalize PMID to bare numeric string."""
        pmid = paper.get("pmid")
        if not pmid:
            return

        pmid = str(pmid).strip()
        for prefix in ["PMID:", "PMID ", "pmid:", "pmid "]:
            if pmid.startswith(prefix):
                pmid = pmid[len(prefix):]
                break

        pmid = pmid.strip()
        if pmid.isdigit():
            paper["pmid"] = pmid
        else:
            # Extract digits only
            digits = re.search(r"\d+", pmid)
            if digits:
                paper["pmid"] = digits.group(0)

    # ------------------------------------------------------------------
    # RRIDs
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_rrids(paper: Dict) -> None:
        """Normalize RRID entries to consistent format."""
        rrids = paper.get("rrids")
        if not rrids or not isinstance(rrids, list):
            return

        seen = set()
        normalized = []
        for rrid_entry in rrids:
            if not isinstance(rrid_entry, dict):
                continue

            rrid_id = rrid_entry.get("id", "")
            if not rrid_id:
                continue

            # Strip and normalize
            rrid_id = rrid_id.strip()
            # Ensure RRID: prefix
            if not rrid_id.upper().startswith("RRID:"):
                rrid_id = f"RRID:{rrid_id}"

            # Normalize format: "RRID:" then the code with no spaces
            m = re.match(
                r"RRID\s*:\s*((?:AB|SCR|CVCL|IMSR|BDSC|ZFIN|WB-STRAIN|"
                r"MGI|MMRRC|ZIRC|DGRC|CGC|Addgene)_\d+)",
                rrid_id, re.I,
            )
            if m:
                code = m.group(1)
                # Capitalize prefix
                prefix, num = code.split("_", 1)
                prefix = prefix.upper() if prefix != "Addgene" else "Addgene"
                canonical_id = f"RRID:{prefix}_{num}"

                if canonical_id in seen:
                    continue
                seen.add(canonical_id)

                rrid_entry["id"] = canonical_id
                rrid_entry["url"] = f"https://scicrunch.org/resolver/{canonical_id}"

                # Ensure type is set
                TYPE_MAP = {
                    "AB": "antibody", "SCR": "software",
                    "CVCL": "cell_line", "ADDGENE": "plasmid",
                }
                if not rrid_entry.get("type"):
                    rrid_entry["type"] = TYPE_MAP.get(prefix.upper(), "resource")

                normalized.append(rrid_entry)

        paper["rrids"] = normalized

    # ------------------------------------------------------------------
    # RORs
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_rors(paper: Dict) -> None:
        """Normalize ROR entries to consistent format."""
        rors = paper.get("rors")
        if not rors or not isinstance(rors, list):
            return

        seen = set()
        normalized = []
        for ror_entry in rors:
            if not isinstance(ror_entry, dict):
                continue

            ror_id = ror_entry.get("id", "")
            if not ror_id:
                continue

            # Extract the 9-character ROR ID
            ror_id = ror_id.strip()
            m = re.search(r"(0[a-z0-9]{8})", ror_id, re.I)
            if not m:
                continue

            canonical_id = m.group(1).lower()
            if canonical_id in seen:
                continue
            seen.add(canonical_id)

            ror_entry["id"] = canonical_id
            ror_entry["url"] = f"https://ror.org/{canonical_id}"
            normalized.append(ror_entry)

        paper["rors"] = normalized

    # ------------------------------------------------------------------
    # Repository URLs
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_repositories(paper: Dict) -> None:
        """Normalize repository entries: URLs and names."""
        repos = paper.get("repositories")
        if not repos or not isinstance(repos, list):
            return

        seen_urls = set()
        normalized = []

        for repo in repos:
            if not isinstance(repo, dict):
                continue

            url = repo.get("url", "")
            if not url:
                normalized.append(repo)
                continue

            # Normalize URL
            url = url.strip().rstrip("/")
            # Force https
            if url.startswith("http://"):
                url = "https://" + url[7:]
            # Add scheme if missing
            if not url.startswith("https://"):
                url = "https://" + url
            # Remove www.
            url = re.sub(r"https://www\.", "https://", url)
            # Remove trailing .git
            if url.endswith(".git"):
                url = url[:-4]
            # Remove fragment
            url = url.split("#")[0].rstrip("/")

            # Canonical name from domain
            name = repo.get("name", "")
            if not name:
                name = _infer_repo_name(url)
                if name:
                    repo["name"] = name

            # Deduplicate
            url_key = url.lower()
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)

            repo["url"] = url
            normalized.append(repo)

        paper["repositories"] = normalized

    # ------------------------------------------------------------------
    # GitHub tools
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_github_tools(paper: Dict) -> None:
        """Normalize github_tools entries."""
        tools = paper.get("github_tools")
        if not tools or not isinstance(tools, list):
            return

        seen = set()
        normalized = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue

            full_name = tool.get("full_name", "")
            if full_name:
                # Normalize: lowercase owner/repo, strip .git, whitespace
                full_name = full_name.strip().rstrip("/")
                if full_name.endswith(".git"):
                    full_name = full_name[:-4]
                tool["full_name"] = full_name

                # Ensure URL matches full_name
                tool["url"] = f"https://github.com/{full_name}"

                # Deduplicate (case-insensitive)
                key = full_name.lower()
                if key in seen:
                    continue
                seen.add(key)

            normalized.append(tool)

        paper["github_tools"] = normalized

    # ------------------------------------------------------------------
    # Accession IDs (EMPIAR, EMDB, PDB, GEO, etc.)
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_accession_ids(paper: Dict) -> None:
        """Normalize accession IDs found in repositories."""
        repos = paper.get("repositories")
        if not repos or not isinstance(repos, list):
            return

        for repo in repos:
            if not isinstance(repo, dict):
                continue

            name = (repo.get("name") or "").lower()
            url = repo.get("url", "")

            # Normalize EMPIAR IDs
            if "empiar" in name or "empiar" in url.lower():
                m = re.search(r"EMPIAR[- ]?(\d+)", url, re.I)
                if m:
                    accession = f"EMPIAR-{m.group(1)}"
                    repo["accession"] = accession

            # Normalize EMDB IDs
            if "emdb" in name or "emdb" in url.lower():
                m = re.search(r"EMD[- ]?(\d{4,})", url, re.I)
                if m:
                    repo["accession"] = f"EMD-{m.group(1)}"

            # Normalize PDB IDs
            if "pdb" in name:
                m = re.search(r"(\d[A-Za-z0-9]{3})", url)
                if m:
                    repo["accession"] = m.group(1).upper()

            # Normalize GEO IDs
            if "geo" in name or "ncbi.nlm.nih.gov/geo" in url.lower():
                m = re.search(r"(GSE\d+)", url, re.I)
                if m:
                    repo["accession"] = m.group(1).upper()


# ======================================================================
# Helpers
# ======================================================================

# Map URL domains to canonical repository names
_DOMAIN_TO_NAME = {
    "zenodo.org": "Zenodo",
    "figshare.com": "Figshare",
    "datadryad.org": "Dryad",
    "osf.io": "OSF",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "codeocean.com": "Code Ocean",
    "data.mendeley.com": "Mendeley Data",
    "ebi.ac.uk/empiar": "EMPIAR",
    "ebi.ac.uk/emdb": "EMDB",
    "ebi.ac.uk/biostudies": "BioStudies",
    "bioimage-archive.ebi.ac.uk": "BioImage Archive",
    "idr.openmicroscopy.org": "IDR",
    "rcsb.org": "PDB",
    "ncbi.nlm.nih.gov/geo": "GEO",
    "ncbi.nlm.nih.gov/sra": "SRA",
    "ebi.ac.uk/arrayexpress": "ArrayExpress",
    "proteomecentral": "PRIDE",
}


def _infer_repo_name(url: str) -> str:
    """Infer repository name from URL domain."""
    url_lower = url.lower()
    for domain, name in _DOMAIN_TO_NAME.items():
        if domain in url_lower:
            return name
    return ""
