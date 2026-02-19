#!/usr/bin/env python3
"""
MicroHub Multi-Agent NLP Pipeline v6.0
=======================================

Convenience dispatcher — delegates to the 4 numbered pipeline scripts.

The pipeline has 4 distinct steps, each with its own script:

    1_scrape.py   — Scrape papers from PubMed/PMC into the SQLite DB.
                    Long-running, hits external APIs.  Run on its own
                    while steps 2-4 process previously scraped data.

    2_export.py   — Export DB to chunked JSON (raw_export/).
                    Raw dump only — no enrichment.

    3_clean.py    — Clean, enrich, re-tag JSON, set flags, strip full_text.
                    Runs all agents by default (RORs, repos, software, etc.).
                    Produces WordPress-ready files (cleaned_export/).

    4_validate.py — Validate cleaned JSON against MASTER_TAG_DICTIONARY.

Typical workflow (scraper runs in background):

    python 1_scrape.py --limit 500 &       # background
    python 2_export.py                     # raw DB dump → raw_export/
    python 3_clean.py                      # enrich + clean → cleaned_export/
    python 4_validate.py                   # check cleaned_export/

This file still works as a unified entry point for backward compatibility:

    python run_pipeline.py scrape --limit 100
    python run_pipeline.py export
    python run_pipeline.py cleanup
    python run_pipeline.py validate
"""

import argparse
import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _delegate(script_name: str, extra_args: list):
    """Run one of the numbered scripts, forwarding extra CLI arguments."""
    script = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script):
        logger.error("Script not found: %s", script)
        sys.exit(1)
    result = subprocess.run([sys.executable, script] + extra_args)
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="MicroHub Pipeline v6.0 — unified dispatcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Preferred usage (individual scripts):
    python 1_scrape.py [--limit N] [--priority-only] ...
    python 2_export.py [--chunk-size 500] ...
    python 3_clean.py  [--input-dir raw_export/] [--no-enrich] ...
    python 4_validate.py [--input-dir cleaned_export/] [--strict]
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline step")

    # ---- scrape ----
    p_scrape = subparsers.add_parser(
        "scrape", help="Step 1: Scrape papers (delegates to 1_scrape.py)")
    p_scrape.add_argument("--limit", type=int, help="Limit papers")
    p_scrape.add_argument("extra", nargs=argparse.REMAINDER,
                          help="Additional args forwarded to 1_scrape.py")

    # ---- export ----
    p_export = subparsers.add_parser(
        "export", help="Step 2: Export DB to JSON (delegates to 2_export.py)")
    p_export.add_argument("--db", help="Database path")
    p_export.add_argument("--output", "-o", help="Output filename")
    p_export.add_argument("--output-dir", help="Output directory")
    p_export.add_argument("--limit", type=int, help="Limit papers")
    p_export.add_argument("--full-text-only", action="store_true")
    p_export.add_argument("--with-citations", action="store_true")
    p_export.add_argument("--min-citations", type=int, default=0)
    p_export.add_argument("--methods-only", action="store_true")
    p_export.add_argument("--chunk-size", type=int, default=500)

    # ---- cleanup ----
    p_cleanup = subparsers.add_parser(
        "cleanup", help="Step 3: Clean & re-tag JSON (delegates to 3_clean.py)")
    p_cleanup.add_argument("--input", "-i", help="Input JSON file")
    p_cleanup.add_argument("--input-dir", help="Input directory")
    p_cleanup.add_argument("--output-dir", default="cleaned_export")
    p_cleanup.add_argument("--no-enrich", action="store_true",
                           help="Skip agent pipeline (NOT recommended)")
    p_cleanup.add_argument("--skip-api", action="store_true",
                           help="Skip GitHub/S2/CrossRef API enrichment")

    # ---- validate ----
    p_validate = subparsers.add_parser(
        "validate", help="Step 4: Validate JSON (delegates to 4_validate.py)")
    p_validate.add_argument("--input-dir", help="Directory to validate")
    p_validate.add_argument("--strict", action="store_true",
                            help="Exit 1 on any issue")

    args = parser.parse_args()

    if args.command == "scrape":
        fwd = []
        if args.limit:
            fwd += ["--limit", str(args.limit)]
        fwd += getattr(args, "extra", [])
        _delegate("1_scrape.py", fwd)

    elif args.command == "export":
        fwd = []
        if args.db:
            fwd += ["--db", args.db]
        if args.output:
            fwd += ["--output", args.output]
        if args.output_dir:
            fwd += ["--output-dir", args.output_dir]
        if args.limit:
            fwd += ["--limit", str(args.limit)]
        if args.full_text_only:
            fwd.append("--full-text-only")
        if args.with_citations:
            fwd.append("--with-citations")
        if args.min_citations:
            fwd += ["--min-citations", str(args.min_citations)]
        if args.methods_only:
            fwd.append("--methods-only")
        if args.chunk_size != 500:
            fwd += ["--chunk-size", str(args.chunk_size)]
        _delegate("2_export.py", fwd)

    elif args.command == "cleanup":
        fwd = []
        if args.input:
            fwd += ["--input", args.input]
        if args.input_dir:
            fwd += ["--input-dir", args.input_dir]
        if args.output_dir != "cleaned_export":
            fwd += ["--output-dir", args.output_dir]
        if args.no_enrich:
            fwd.append("--no-enrich")
        if args.skip_api:
            fwd.append("--skip-api")
        _delegate("3_clean.py", fwd)

    elif args.command == "validate":
        fwd = []
        if args.input_dir:
            fwd += ["--input-dir", args.input_dir]
        if args.strict:
            fwd.append("--strict")
        _delegate("4_validate.py", fwd)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
