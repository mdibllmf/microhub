#!/usr/bin/env python3
"""
Fix and validate data repository links in cleaned export JSON files.

Scans all papers for repository entries and ensures:
  1. Every repository has a valid, well-formed URL
  2. Accession-only entries get proper URLs generated
  3. DOI-based references are expanded to full URLs
  4. Duplicate repositories are removed
  5. Repository names are normalized to canonical forms
  6. URLs that are bare DOIs or accession IDs are converted to full URLs
  7. Broken/malformed URLs are flagged or repaired

Usage:
    python fix_repo_links.py                                  # default dirs
    python fix_repo_links.py --input-dir cleaned_export/      # custom input
    python fix_repo_links.py --output-dir fixed_export/       # custom output (default: overwrite)
    python fix_repo_links.py --dry-run                        # preview changes
    python fix_repo_links.py --input cleaned_export/chunk_1.json  # single file
    python fix_repo_links.py --validate                       # also HTTP-check URLs
"""

import argparse
import glob
import json
import logging
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, quote

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Rate limit for HTTP validation (requests per second)
HTTP_REQUEST_DELAY = 0.5

# ======================================================================
# Canonical repository names — normalize variant spellings
# ======================================================================

_NAME_ALIASES = {
    "zenodo": "Zenodo",
    "figshare": "Figshare",
    "dryad": "Dryad",
    "datadryad": "Dryad",
    "data dryad": "Dryad",
    "osf": "OSF",
    "open science framework": "OSF",
    "code ocean": "Code Ocean",
    "codeocean": "Code Ocean",
    "mendeley data": "Mendeley Data",
    "mendeley": "Mendeley Data",
    "empiar": "EMPIAR",
    "emdb": "EMDB",
    "pdb": "PDB",
    "rcsb": "PDB",
    "rcsb pdb": "PDB",
    "bioimage archive": "BioImage Archive",
    "idr": "IDR",
    "image data resource": "IDR",
    "omero": "OMERO",
    "ssbd": "SSBD",
    "geo": "GEO",
    "gene expression omnibus": "GEO",
    "sra": "SRA",
    "sequence read archive": "SRA",
    "arrayexpress": "ArrayExpress",
    "array express": "ArrayExpress",
    "ena": "ENA",
    "european nucleotide archive": "ENA",
    "pride": "PRIDE",
    "proteomexchange": "ProteomeXchange",
    "biostudies": "BioStudies",
    "dataverse": "Dataverse",
    "gigadb": "GigaDB",
    "hugging face": "Hugging Face",
    "huggingface": "Hugging Face",
    "dandi": "DANDI",
    "dandi archive": "DANDI",
    "neuromorpho": "NeuroMorpho",
    "openneuro": "OpenNeuro",
    "open neuro": "OpenNeuro",
    "synapse": "Synapse",
    "sciencedb": "ScienceDB",
    "science data bank": "ScienceDB",
    "cell image library": "Cell Image Library",
    "biomodels": "BioModels",
    "bioimage model zoo": "BioImage Model Zoo",
    "jcb dataviewer": "JCB DataViewer",
    "flowrepository": "FlowRepository",
    "metabolights": "MetaboLights",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "aws open data": "AWS Open Data",
    "bioproject": "BioProject",
    "repository": "Repository",
    "data repository": "Repository",
    "unknown": "Repository",
}

# ======================================================================
# URL detection from domain
# ======================================================================

_DOMAIN_TO_NAME = {
    "zenodo.org": "Zenodo",
    "figshare.com": "Figshare",
    "datadryad.org": "Dryad",
    "osf.io": "OSF",
    "codeocean.com": "Code Ocean",
    "data.mendeley.com": "Mendeley Data",
    "ebi.ac.uk/empiar": "EMPIAR",
    "ebi.ac.uk/emdb": "EMDB",
    "rcsb.org": "PDB",
    "bioimage-archive.ebi.ac.uk": "BioImage Archive",
    "ebi.ac.uk/biostudies/BioImages": "BioImage Archive",
    "idr.openmicroscopy.org": "IDR",
    "ebi.ac.uk/biostudies": "BioStudies",
    "ncbi.nlm.nih.gov/geo": "GEO",
    "ncbi.nlm.nih.gov/sra": "SRA",
    "ncbi.nlm.nih.gov/bioproject": "BioProject",
    "ebi.ac.uk/arrayexpress": "ArrayExpress",
    "ebi.ac.uk/biostudies/arrayexpress": "ArrayExpress",
    "ebi.ac.uk/ena": "ENA",
    "ebi.ac.uk/pride": "PRIDE",
    "dandiarchive.org": "DANDI",
    "openneuro.org": "OpenNeuro",
    "neuromorpho.org": "NeuroMorpho",
    "synapse.org": "Synapse",
    "sciencedb.cn": "ScienceDB",
    "sciencedb.com": "ScienceDB",
    "cellimagelibrary.org": "Cell Image Library",
    "ebi.ac.uk/biomodels": "BioModels",
    "bioimage.io": "BioImage Model Zoo",
    "jcb-dataviewer.rupress.org": "JCB DataViewer",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "bitbucket.org": "Bitbucket",
    "huggingface.co": "Hugging Face",
    "gigadb.org": "GigaDB",
    "registry.opendata.aws": "AWS Open Data",
    "flowrepository.org": "FlowRepository",
    "ebi.ac.uk/metabolights": "MetaboLights",
}

# ======================================================================
# DOI prefix → repository
# ======================================================================

_DOI_PREFIX_TO_NAME = {
    "10.5281": "Zenodo",
    "10.6084": "Figshare",
    "10.5061": "Dryad",
    "10.17605": "OSF",
    "10.5524": "GigaDB",
    "10.17632": "Mendeley Data",
    "10.7910": "Dataverse",
    "10.7303": "DANDI",
    "10.18112": "OpenNeuro",
    "10.15468": "GBIF",
    "10.6019": "MetaboLights",
}

_DOI_PREFIX_TO_URL = {
    "10.5281": "https://doi.org/{doi}",
    "10.6084": "https://doi.org/{doi}",
    "10.5061": "https://doi.org/{doi}",
    "10.17605": "https://doi.org/{doi}",
    "10.5524": "https://doi.org/{doi}",
    "10.17632": "https://doi.org/{doi}",
    "10.7910": "https://doi.org/{doi}",
    "10.7303": "https://doi.org/{doi}",
    "10.18112": "https://doi.org/{doi}",
}

# ======================================================================
# Accession ID patterns and URL templates
# ======================================================================

ACCESSION_PATTERNS = {
    "EMPIAR": re.compile(r"\bEMPIAR[- ]?(\d+)\b", re.I),
    "EMDB": re.compile(r"\bEMD[- ]?(\d{4,})\b", re.I),
    "GEO": re.compile(r"\b(GSE\d{3,})\b", re.I),
    "SRA": re.compile(r"\b(SR[APXR]\d{6,})\b", re.I),
    "BioProject": re.compile(r"\b(PRJNA\d+)\b", re.I),
    "ArrayExpress": re.compile(r"\b(E-[A-Z]{4}-\d+)\b", re.I),
    "BioImage Archive": re.compile(r"\b(S-BIAD\d+)\b", re.I),
    "BioStudies": re.compile(r"\b(S-BSST\d+)\b", re.I),
    "IDR": re.compile(r"\b(idr\d{4})\b", re.I),
    "PRIDE": re.compile(r"\b(PXD\d{6,})\b", re.I),
    "ENA": re.compile(r"\b(PRJ[A-Z]{2}\d+)\b", re.I),
    "DANDI": re.compile(r"\bDANDI[: ]?(\d+)\b", re.I),
    "OpenNeuro": re.compile(r"\b(ds\d{6})\b", re.I),
    "Synapse": re.compile(r"\b(syn\d{6,})\b", re.I),
    "Cell Image Library": re.compile(r"\bCIL[: ]?(\d+)\b", re.I),
    "BioModels": re.compile(r"\b(BIOMD\d+|MODEL\d+)\b", re.I),
    "PDB": re.compile(r"\b(\d[A-Za-z0-9]{3})\b"),
}

ACCESSION_URL_TEMPLATES = {
    "EMPIAR": "https://www.ebi.ac.uk/empiar/EMPIAR-{id}",
    "EMDB": "https://www.ebi.ac.uk/emdb/EMD-{id}",
    "PDB": "https://www.rcsb.org/structure/{id}",
    "GEO": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={id}",
    "SRA": "https://www.ncbi.nlm.nih.gov/sra/{id}",
    "BioProject": "https://www.ncbi.nlm.nih.gov/bioproject/{id}",
    "ArrayExpress": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/{id}",
    "BioImage Archive": "https://www.ebi.ac.uk/biostudies/BioImages/studies/{id}",
    "BioStudies": "https://www.ebi.ac.uk/biostudies/studies/{id}",
    "IDR": "https://idr.openmicroscopy.org/search/?query=Name:{id}",
    "PRIDE": "https://www.ebi.ac.uk/pride/archive/projects/{id}",
    "ENA": "https://www.ebi.ac.uk/ena/browser/view/{id}",
    "DANDI": "https://dandiarchive.org/dandiset/{id}",
    "OpenNeuro": "https://openneuro.org/datasets/{id}",
    "Synapse": "https://www.synapse.org/#!Synapse:{id}",
    "Cell Image Library": "http://www.cellimagelibrary.org/images/{id}",
    "BioModels": "https://www.ebi.ac.uk/biomodels/{id}",
}

# Zenodo-specific URL patterns for normalization
_ZENODO_RECORD_RE = re.compile(r"zenodo\.org/(?:record|records)/(\d+)", re.I)
_ZENODO_DOI_RE = re.compile(r"10\.5281/zenodo\.(\d+)", re.I)

# General DOI pattern
_DOI_PATTERN = re.compile(r"\b(10\.\d{4,}/[^\s,;\"'}\]]+)\b")

# Bare DOI URL (just a DOI without http prefix)
_BARE_DOI = re.compile(r"^10\.\d{4,}/\S+$")


class RepoLinkFixer:
    """Validates and fixes data repository links in paper JSON."""

    def __init__(self, validate_http: bool = False):
        self.validate_http = validate_http
        self._session = None
        self._last_request_time = 0.0
        self.stats = {
            "papers_processed": 0,
            "papers_with_repos": 0,
            "repos_total": 0,
            "repos_fixed_url": 0,
            "repos_fixed_name": 0,
            "repos_generated_url": 0,
            "repos_removed_empty": 0,
            "repos_removed_duplicate": 0,
            "repos_url_validated_ok": 0,
            "repos_url_validated_fail": 0,
            "repos_bare_doi_fixed": 0,
            "repos_accession_url_added": 0,
        }

    def _get_session(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "MicroHub-RepoFixer/1.0 (academic research tool)",
            })
        return self._session

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < HTTP_REQUEST_DELAY:
            time.sleep(HTTP_REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _detect_name_from_url(self, url: str) -> str:
        """Determine canonical repository name from URL."""
        if not url:
            return ""
        url_lower = url.lower()

        # Check full domain+path patterns first (more specific)
        for pattern, name in _DOMAIN_TO_NAME.items():
            if pattern in url_lower:
                return name

        # Check DOI prefixes
        doi_match = _DOI_PATTERN.search(url)
        if doi_match:
            doi = doi_match.group(1)
            for prefix, name in _DOI_PREFIX_TO_NAME.items():
                if doi.startswith(prefix):
                    return name

        # Broad domain checks
        if "dataverse" in url_lower:
            return "Dataverse"

        return ""

    def _normalize_name(self, name: str) -> str:
        """Normalize a repository name to its canonical form."""
        if not name:
            return ""
        key = name.strip().lower()
        return _NAME_ALIASES.get(key, name.strip())

    def _fix_url(self, url: str, name: str, accession: str) -> Optional[str]:
        """Fix or generate a repository URL.

        Returns the fixed URL, or None if it cannot be determined.
        """
        if not url and not accession:
            return None

        # If URL is just a bare DOI (no http prefix), wrap it
        if url and _BARE_DOI.match(url.strip()):
            self.stats["repos_bare_doi_fixed"] += 1
            return f"https://doi.org/{url.strip()}"

        # If URL is missing scheme, add https
        if url and not url.startswith("http"):
            # Check if it looks like a domain
            if "." in url and "/" in url:
                url = f"https://{url}"
            elif url.startswith("doi.org/"):
                url = f"https://{url}"

        # Normalize Zenodo URLs
        if url:
            zenodo_match = _ZENODO_RECORD_RE.search(url)
            if zenodo_match:
                record_id = zenodo_match.group(1)
                url = f"https://zenodo.org/records/{record_id}"

        # If still no URL, try to generate from accession + name
        if not url and accession and name:
            canonical_name = self._normalize_name(name)
            template = ACCESSION_URL_TEMPLATES.get(canonical_name)
            if template:
                # Extract the ID from the accession
                pattern = ACCESSION_PATTERNS.get(canonical_name)
                if pattern:
                    m = pattern.search(accession)
                    if m:
                        acc_id = m.group(1) if m.lastindex else m.group(0)
                        url = template.format(id=acc_id)
                        self.stats["repos_accession_url_added"] += 1

        # If still no URL but have an accession that looks like a DOI
        if not url and accession:
            if _BARE_DOI.match(accession.strip()):
                url = f"https://doi.org/{accession.strip()}"
                self.stats["repos_bare_doi_fixed"] += 1

        return url if url else None

    def _extract_accession_from_url(self, url: str, name: str) -> str:
        """Try to extract an accession ID from a URL."""
        if not url:
            return ""
        canonical_name = self._normalize_name(name) if name else self._detect_name_from_url(url)
        if not canonical_name:
            return ""
        pattern = ACCESSION_PATTERNS.get(canonical_name)
        if pattern:
            m = pattern.search(url)
            if m:
                return m.group(0)
        return ""

    def _validate_url_http(self, url: str) -> bool:
        """HTTP HEAD check if a URL is reachable."""
        if not self.validate_http or not url:
            return True  # Skip validation
        try:
            session = self._get_session()
            self._rate_limit()
            resp = session.head(url, timeout=15, allow_redirects=True)
            return resp.status_code < 400
        except Exception:
            return False

    def fix_repo(self, repo: dict) -> Optional[dict]:
        """Fix a single repository entry.

        Returns the fixed repo dict, or None if it should be removed.
        """
        if not isinstance(repo, dict):
            return None

        url = str(repo.get("url") or "").strip()
        name = str(repo.get("name") or repo.get("type") or "").strip()
        accession = str(
            repo.get("accession_id") or repo.get("accession") or
            repo.get("identifier") or repo.get("id") or ""
        ).strip()
        source = str(repo.get("source") or "").strip()
        validation_status = str(repo.get("validation_status") or "").strip()

        # Detect and normalize the name
        detected_name = self._detect_name_from_url(url)
        if detected_name:
            canonical_name = detected_name
        elif name:
            canonical_name = self._normalize_name(name)
        else:
            canonical_name = "Repository"

        # Track if name changed
        if canonical_name != name and name:
            self.stats["repos_fixed_name"] += 1

        # Fix the URL
        fixed_url = self._fix_url(url, canonical_name, accession)

        # If we still have no URL and no accession, this entry is useless
        if not fixed_url and not accession:
            self.stats["repos_removed_empty"] += 1
            return None

        # Track URL fixes
        if fixed_url and fixed_url != url and url:
            self.stats["repos_fixed_url"] += 1
        elif fixed_url and not url:
            self.stats["repos_generated_url"] += 1

        # Try to extract accession from URL if missing
        if not accession and fixed_url:
            accession = self._extract_accession_from_url(fixed_url, canonical_name)

        # HTTP validation (optional)
        if self.validate_http and fixed_url:
            if self._validate_url_http(fixed_url):
                self.stats["repos_url_validated_ok"] += 1
                validation_status = "confirmed"
            else:
                self.stats["repos_url_validated_fail"] += 1
                validation_status = "dead"

        result = {
            "name": canonical_name,
            "url": fixed_url or "",
        }
        if accession:
            result["accession_id"] = accession
        if source:
            result["source"] = source
        if validation_status:
            result["validation_status"] = validation_status

        return result

    def _normalize_url_for_dedup(self, url: str) -> str:
        """Normalize a URL for deduplication."""
        if not url:
            return ""
        url = url.lower().strip().rstrip("/")
        # Remove www
        url = re.sub(r"^https?://(www\.)?", "", url)
        # Remove trailing query params that are just tracking
        url = re.sub(r"[?&]utm_\w+=[^&]*", "", url)
        return url

    def fix_paper_repos(self, paper: dict, dry_run: bool = False) -> Tuple[int, int]:
        """Fix all repository links for a single paper.

        Returns (fixes_made, repos_removed).
        """
        self.stats["papers_processed"] += 1

        repos = paper.get("repositories")
        if not repos or not isinstance(repos, list):
            return 0, 0

        self.stats["papers_with_repos"] += 1
        self.stats["repos_total"] += len(repos)

        fixed_repos = []
        seen_urls = set()
        fixes_made = 0
        removed = 0

        for repo in repos:
            fixed = self.fix_repo(repo)
            if fixed is None:
                removed += 1
                continue

            # Deduplicate by normalized URL
            norm_url = self._normalize_url_for_dedup(fixed.get("url", ""))
            if norm_url and norm_url in seen_urls:
                self.stats["repos_removed_duplicate"] += 1
                removed += 1
                continue
            if norm_url:
                seen_urls.add(norm_url)

            # Check if anything changed
            orig_url = str(repo.get("url") or "").strip()
            orig_name = str(repo.get("name") or "").strip()
            if fixed["url"] != orig_url or fixed["name"] != orig_name:
                fixes_made += 1

            fixed_repos.append(fixed)

        if not dry_run:
            paper["repositories"] = fixed_repos

            # Also update image_repositories if present
            if "image_repositories" in paper:
                image_repo_keywords = (
                    "empiar", "idr", "bioimage", "biostudies",
                    "image data resource", "ssbd", "omero",
                    "cell image library", "zenodo",
                )
                paper["image_repositories"] = [
                    r for r in fixed_repos
                    if isinstance(r, dict) and any(
                        kw in (r.get("name") or r.get("url") or "").lower()
                        for kw in image_repo_keywords
                    )
                ]

            # Update boolean flags
            paper["has_data"] = bool(fixed_repos)
            paper["has_datasets"] = _has_dataset_repositories(fixed_repos)

        return fixes_made, removed


def _has_dataset_repositories(repositories: list) -> bool:
    """Check if any repositories indicate a real dataset (not just code)."""
    dataset_sources = {"datacite", "openaire", "crossref-relation", "text_pattern", "data_availability_mining"}
    for repo in repositories or []:
        if not isinstance(repo, dict):
            continue
        source = str(repo.get("source") or "").strip().lower()
        if source in dataset_sources:
            return True
        url = str(repo.get("url") or "")
        if url and any(hint in url.lower() for hint in ("zenodo", "figshare", "dryad", "datadryad", "osf.io", "doi.org/10.")):
            return True
    return False


def process_papers(
    papers: list,
    fixer: RepoLinkFixer,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """Process a list of papers, fixing repository links.

    Returns (total_fixes, total_removed).
    """
    total_fixes = 0
    total_removed = 0

    for paper in papers:
        pmid = paper.get("pmid") or paper.get("doi") or paper.get("id") or "?"
        fixes, removed = fixer.fix_paper_repos(paper, dry_run=dry_run)

        if fixes > 0 or removed > 0:
            if dry_run:
                logger.info(
                    "  [DRY-RUN] %s: %d fix(es), %d removed",
                    pmid, fixes, removed,
                )
                # Show details
                for repo in paper.get("repositories", []):
                    if isinstance(repo, dict):
                        logger.info(
                            "    %s: %s",
                            repo.get("name", "?"),
                            repo.get("url", "(no URL)"),
                        )
            else:
                logger.debug("  %s: %d fix(es), %d removed", pmid, fixes, removed)

            total_fixes += fixes
            total_removed += removed

    return total_fixes, total_removed


def main():
    parser = argparse.ArgumentParser(
        description="Fix and validate data repository links in export JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_repo_links.py                              # process cleaned_export/
  python fix_repo_links.py --input-dir cleaned_export/  # explicit input dir
  python fix_repo_links.py --dry-run                    # preview without writing
  python fix_repo_links.py --output-dir fixed_export/   # write to separate dir
  python fix_repo_links.py -i cleaned_export/chunk_1.json  # single file
  python fix_repo_links.py --validate                   # also HTTP-check URLs (slow)
""",
    )
    parser.add_argument(
        "--input", "-i",
        help="Single input JSON file to process",
    )
    parser.add_argument(
        "--input-dir",
        help="Input directory containing JSON files (default: cleaned_export/)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: overwrite input files in place)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="HTTP-check each repository URL (slow, requires network)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed debug output",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve input files
    if args.input:
        input_path = args.input
        if not os.path.isabs(input_path):
            input_path = os.path.join(SCRIPT_DIR, input_path)
        input_files = [input_path]
    else:
        input_dir = args.input_dir
        if input_dir:
            if not os.path.isabs(input_dir):
                input_dir = os.path.join(SCRIPT_DIR, input_dir)
        else:
            input_dir = os.path.join(SCRIPT_DIR, "cleaned_export")

        if not os.path.isdir(input_dir):
            logger.error("Input directory not found: %s", input_dir)
            logger.error("Run the pipeline first, or specify --input-dir")
            sys.exit(1)

        input_files = sorted(glob.glob(os.path.join(input_dir, "*_chunk_*.json")))
        if not input_files:
            input_files = sorted(glob.glob(os.path.join(input_dir, "*.json")))

    if not input_files:
        logger.error("No JSON files found!")
        sys.exit(1)

    # Resolve output directory
    out_dir = None
    if args.output_dir:
        out_dir = args.output_dir
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(SCRIPT_DIR, out_dir)
        os.makedirs(out_dir, exist_ok=True)

    logger.info("=" * 60)
    logger.info("FIX REPOSITORY LINKS — Validate & Repair")
    logger.info("=" * 60)
    logger.info("Input files:    %d", len(input_files))
    logger.info("Output:         %s", out_dir or "overwrite in place")
    logger.info("Dry run:        %s", "yes" if args.dry_run else "no")
    logger.info("HTTP validate:  %s", "yes" if args.validate else "no")
    logger.info("")

    fixer = RepoLinkFixer(validate_http=args.validate)
    total_papers = 0
    total_fixes = 0
    total_removed = 0

    for input_file in input_files:
        logger.info("Processing: %s", os.path.basename(input_file))

        with open(input_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        fixes, removed = process_papers(papers, fixer, dry_run=args.dry_run)
        total_fixes += fixes
        total_removed += removed
        total_papers += len(papers)

        # Write output
        if not args.dry_run:
            if out_dir:
                out_file = os.path.join(out_dir, os.path.basename(input_file))
            else:
                out_file = input_file

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(papers, f, indent=2, ensure_ascii=False, default=str)

            logger.info("  -> wrote %s", os.path.basename(out_file))

    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info("Papers processed:          %d", fixer.stats["papers_processed"])
    logger.info("Papers with repositories:  %d", fixer.stats["papers_with_repos"])
    logger.info("Total repo entries:        %d", fixer.stats["repos_total"])
    logger.info("")
    logger.info("FIXES APPLIED:")
    logger.info("  URLs fixed/normalized:   %d", fixer.stats["repos_fixed_url"])
    logger.info("  URLs generated (new):    %d", fixer.stats["repos_generated_url"])
    logger.info("  Bare DOIs wrapped:       %d", fixer.stats["repos_bare_doi_fixed"])
    logger.info("  Accession URLs added:    %d", fixer.stats["repos_accession_url_added"])
    logger.info("  Names normalized:        %d", fixer.stats["repos_fixed_name"])
    logger.info("")
    logger.info("REMOVALS:")
    logger.info("  Empty entries removed:   %d", fixer.stats["repos_removed_empty"])
    logger.info("  Duplicates removed:      %d", fixer.stats["repos_removed_duplicate"])
    logger.info("")

    if args.validate:
        logger.info("HTTP VALIDATION:")
        logger.info("  URLs OK:                 %d", fixer.stats["repos_url_validated_ok"])
        logger.info("  URLs failed:             %d", fixer.stats["repos_url_validated_fail"])
        logger.info("")

    if args.dry_run:
        logger.info("DRY RUN — no files were modified.")
    else:
        logger.info("Done! Repository links have been updated.")


if __name__ == "__main__":
    main()
