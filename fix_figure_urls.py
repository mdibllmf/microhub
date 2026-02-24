#!/usr/bin/env python3
"""
Fix broken PMC figure image URLs in cleaned export JSON files.

PMC migrated to cdn.ncbi.nlm.nih.gov/pmc/blobs/... URLs, breaking the
old /pmc/articles/PMC{id}/bin/{filename} pattern. This script:

  1. Reads cleaned export JSON files
  2. For each paper with PMC figures, fetches the live article page
  3. Extracts the actual CDN image URLs from the page HTML
  4. Matches them to figure objects by filename
  5. Writes updated JSON files

Usage:
    python fix_figure_urls.py                                  # default dirs
    python fix_figure_urls.py --input-dir cleaned_export/      # custom input
    python fix_figure_urls.py --output-dir fixed_export/       # custom output (default: overwrite)
    python fix_figure_urls.py --dry-run                        # preview changes
    python fix_figure_urls.py --input cleaned_export/chunk_1.json  # single file
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
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# NCBI requests: max 3/second without API key, we use 0.4s gap to be safe
NCBI_REQUEST_DELAY = 0.4

# Regex to match broken PMC /bin/ URLs
PMC_BIN_PATTERN = re.compile(
    r"https?://(?:www\.)?ncbi\.nlm\.nih\.gov/pmc/articles/PMC(\d+)/bin/(.+)"
)
# Also match the new domain variant (which 404s for /bin/)
PMC_BIN_PATTERN_NEW = re.compile(
    r"https?://pmc\.ncbi\.nlm\.nih\.gov/articles/PMC(\d+)/bin/(.+)"
)

# Extract filename stem from a URL path
FILENAME_STEM_RE = re.compile(r"([^/]+?)(?:\.\w{2,5})?$")

# Match CDN blob URLs on the article page
CDN_IMG_PATTERN = re.compile(
    r"https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^\"'\s]+"
)


class PMCFigureResolver:
    """Resolves broken PMC figure URLs by scraping live article pages."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "MicroHub-FigureFixer/1.0 (academic research tool)",
        })
        # Cache: pmcid -> {filename_stem: cdn_url}
        self._cache: Dict[str, Dict[str, str]] = {}
        self._last_request_time = 0.0
        self.stats = {
            "pages_fetched": 0,
            "pages_failed": 0,
            "urls_fixed": 0,
            "urls_already_ok": 0,
            "urls_unresolvable": 0,
        }

    def _rate_limit(self):
        """Enforce NCBI rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < NCBI_REQUEST_DELAY:
            time.sleep(NCBI_REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _fetch_article_images(self, pmc_id: str) -> Dict[str, str]:
        """Fetch a PMC article page and extract CDN image URLs.

        Returns a dict mapping filename stems to full CDN URLs.
        """
        if pmc_id in self._cache:
            return self._cache[pmc_id]

        url = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/"
        self._rate_limit()

        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            self.stats["pages_fetched"] += 1
        except requests.RequestException as e:
            logger.warning("  Failed to fetch PMC%s: %s", pmc_id, e)
            self.stats["pages_failed"] += 1
            self._cache[pmc_id] = {}
            return {}

        # Extract all CDN blob URLs from the page
        cdn_urls = CDN_IMG_PATTERN.findall(resp.text)

        # Build filename-stem -> CDN URL mapping
        mapping: Dict[str, str] = {}
        for cdn_url in cdn_urls:
            # Clean up any trailing quotes or HTML artifacts
            cdn_url = cdn_url.split('"')[0].split("'")[0].split(")")[0]
            # Extract the filename from the CDN URL
            # Pattern: cdn.ncbi.nlm.nih.gov/pmc/blobs/{h1}/{pmcid}/{h2}/{filename}
            parts = cdn_url.rstrip("/").split("/")
            if len(parts) >= 2:
                filename = parts[-1]
                stem = _filename_stem(filename)
                if stem:
                    mapping[stem] = cdn_url

        self._cache[pmc_id] = mapping
        return mapping

    def resolve_url(self, image_url: str) -> Optional[str]:
        """Try to resolve a broken PMC /bin/ URL to a working CDN URL.

        Returns the fixed URL, or None if not resolvable.
        """
        # Check if it's a PMC /bin/ URL
        match = PMC_BIN_PATTERN.match(image_url) or PMC_BIN_PATTERN_NEW.match(image_url)
        if not match:
            return None  # Not a PMC URL, skip

        pmc_id = match.group(1)
        filename = match.group(2)
        stem = _filename_stem(filename)

        if not stem:
            return None

        # Fetch article page and get CDN URLs
        mapping = self._fetch_article_images(pmc_id)
        if not mapping:
            return None

        # Try exact stem match first
        if stem in mapping:
            return mapping[stem]

        # Try case-insensitive match
        stem_lower = stem.lower()
        for key, url in mapping.items():
            if key.lower() == stem_lower:
                return url

        # Try partial match (stem contained in key or vice versa)
        for key, url in mapping.items():
            if stem_lower in key.lower() or key.lower() in stem_lower:
                return url

        return None


def _filename_stem(filename: str) -> str:
    """Extract the stem of a filename (without extension)."""
    match = FILENAME_STEM_RE.match(filename)
    if match:
        return match.group(1)
    return filename


def _is_pmc_bin_url(url: str) -> bool:
    """Check if a URL matches the broken PMC /bin/ pattern."""
    return bool(PMC_BIN_PATTERN.match(url) or PMC_BIN_PATTERN_NEW.match(url))


def _is_likely_broken(url: str) -> bool:
    """Heuristic check for URLs that are likely broken."""
    if _is_pmc_bin_url(url):
        return True
    return False


def process_papers(
    papers: List[dict],
    resolver: PMCFigureResolver,
    dry_run: bool = False,
) -> int:
    """Process a list of papers, fixing broken figure URLs.

    Returns the number of URLs fixed.
    """
    fixed_count = 0

    for paper in papers:
        figures = paper.get("figures")
        if not figures or not isinstance(figures, list):
            continue

        pmid = paper.get("pmid", paper.get("doi", "?"))
        paper_fixed = 0

        for fig in figures:
            if not isinstance(fig, dict):
                continue

            image_url = fig.get("image_url", "") or fig.get("url", "")
            if not image_url:
                continue

            if not _is_likely_broken(image_url):
                resolver.stats["urls_already_ok"] += 1
                continue

            new_url = resolver.resolve_url(image_url)
            if new_url and new_url != image_url:
                label = fig.get("label", fig.get("id", "?"))
                if dry_run:
                    logger.info("  [DRY-RUN] %s %s:", pmid, label)
                    logger.info("    OLD: %s", image_url)
                    logger.info("    NEW: %s", new_url)
                else:
                    fig["image_url"] = new_url
                    logger.debug("  Fixed %s %s", pmid, label)
                fixed_count += 1
                paper_fixed += 1
                resolver.stats["urls_fixed"] += 1
            else:
                resolver.stats["urls_unresolvable"] += 1
                logger.debug("  Could not resolve: %s", image_url)

        # Also update figure_urls list if present
        if not dry_run and paper_fixed > 0:
            figure_urls = []
            for fig in figures:
                if isinstance(fig, dict):
                    url = fig.get("image_url") or fig.get("url", "")
                    if url:
                        figure_urls.append(url)
            if figure_urls:
                paper["figure_urls"] = figure_urls
                # Update thumbnail if it was from a PMC /bin/ URL
                if paper.get("thumbnail_url") and _is_pmc_bin_url(paper["thumbnail_url"]):
                    paper["thumbnail_url"] = figure_urls[0]

        if paper_fixed > 0:
            logger.info("  PMID %s: fixed %d figure URL(s)", pmid, paper_fixed)

    return fixed_count


def main():
    parser = argparse.ArgumentParser(
        description="Fix broken PMC figure image URLs in export JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_figure_urls.py                              # process cleaned_export/
  python fix_figure_urls.py --input-dir cleaned_export/  # explicit input dir
  python fix_figure_urls.py --dry-run                    # preview without writing
  python fix_figure_urls.py --output-dir fixed_export/   # write to separate dir
  python fix_figure_urls.py -i cleaned_export/chunk_1.json  # single file
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
    logger.info("FIX FIGURE URLs — PMC /bin/ → CDN blob resolver")
    logger.info("=" * 60)
    logger.info("Input files:  %d", len(input_files))
    logger.info("Output:       %s", out_dir or "overwrite in place")
    logger.info("Dry run:      %s", "yes" if args.dry_run else "no")
    logger.info("")

    resolver = PMCFigureResolver()
    total_papers = 0
    total_figures = 0
    total_pmc_figures = 0
    total_fixed = 0

    for input_file in input_files:
        logger.info("Processing: %s", os.path.basename(input_file))

        with open(input_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        # Count figures before processing
        for p in papers:
            figs = p.get("figures", [])
            if isinstance(figs, list):
                total_figures += len(figs)
                for fig in figs:
                    if isinstance(fig, dict):
                        url = fig.get("image_url", "") or fig.get("url", "")
                        if _is_pmc_bin_url(url):
                            total_pmc_figures += 1

        fixed = process_papers(papers, resolver, dry_run=args.dry_run)
        total_fixed += fixed
        total_papers += len(papers)

        # Write output
        if not args.dry_run:
            if out_dir:
                out_file = os.path.join(out_dir, os.path.basename(input_file))
            else:
                out_file = input_file

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(papers, f, indent=2, ensure_ascii=False, default=str)

            logger.info("  → wrote %s", os.path.basename(out_file))

    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info("Papers processed:     %d", total_papers)
    logger.info("Total figures:        %d", total_figures)
    logger.info("PMC /bin/ figures:     %d", total_pmc_figures)
    logger.info("URLs fixed:           %d", resolver.stats["urls_fixed"])
    logger.info("URLs already OK:      %d", resolver.stats["urls_already_ok"])
    logger.info("URLs unresolvable:    %d", resolver.stats["urls_unresolvable"])
    logger.info("PMC pages fetched:    %d", resolver.stats["pages_fetched"])
    logger.info("PMC pages failed:     %d", resolver.stats["pages_failed"])
    logger.info("")

    if resolver.stats["urls_unresolvable"] > 0:
        logger.warning(
            "%d URLs could not be resolved (article page may not have images, "
            "or paper is not in PMC Open Access subset).",
            resolver.stats["urls_unresolvable"],
        )

    if args.dry_run:
        logger.info("DRY RUN — no files were modified.")
    else:
        logger.info("Done! Figure URLs have been updated.")


if __name__ == "__main__":
    main()
