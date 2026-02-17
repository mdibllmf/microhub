#!/usr/bin/env python3
"""
Step 2 — Export papers from the SQLite database to chunked JSON.

Reads the DB populated by step 1 and writes WordPress-compatible JSON files.
Optionally re-runs the agent pipeline (--enrich) for fresh tag extraction.

    python 2_export.py                             # export all papers
    python 2_export.py --enrich                    # re-run agents for fresh tags
    python 2_export.py --output-dir raw_export/    # custom output directory
    python 2_export.py --chunk-size 500            # 500 papers per file
    python 2_export.py --limit 1000                # only first 1000 papers
    python 2_export.py --full-text-only            # only papers with full text
    python 2_export.py --methods-only              # only methods-extracted tags
    python 2_export.py --min-citations 5           # min 5 citations

Output:
    <output-dir>/microhub_papers_v5_chunk_1.json
    <output-dir>/microhub_papers_v5_chunk_2.json
    ...
    <output-dir>/microhub_papers_v5_github_tools.json
"""

import argparse
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(
        description="Step 2 — Export DB to chunked JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", help="Database path (default: microhub.db)")
    parser.add_argument("--output", "-o", help="Output base filename")
    parser.add_argument("--output-dir", help="Output directory (default: raw_export/)")
    parser.add_argument("--limit", type=int, help="Limit papers exported")
    parser.add_argument("--full-text-only", action="store_true",
                        help="Only papers with full text")
    parser.add_argument("--with-citations", action="store_true",
                        help="Only papers with citations")
    parser.add_argument("--min-citations", type=int, default=0,
                        help="Minimum citation count")
    parser.add_argument("--methods-only", action="store_true",
                        help="Only methods-extracted tags")
    parser.add_argument("--chunk-size", type=int, default=500,
                        help="Papers per JSON file (default: 500)")
    parser.add_argument("--enrich", action="store_true",
                        help="Re-run agent pipeline for fresh tag extraction")

    args = parser.parse_args()

    from pipeline.export.json_exporter import JsonExporter
    from pipeline.orchestrator import PipelineOrchestrator

    db_path = args.db or os.path.join(SCRIPT_DIR, "microhub.db")
    output = args.output or "microhub_papers_v5.json"

    # Output directory
    out_dir = args.output_dir or "raw_export"
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(SCRIPT_DIR, out_dir)
    os.makedirs(out_dir, exist_ok=True)
    output = os.path.join(out_dir, os.path.basename(output))

    # Optional agent enrichment
    enricher = None
    if args.enrich:
        logger.info("Agent enrichment enabled — tags will be refreshed")
        dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
        enricher = PipelineOrchestrator(
            tag_dictionary_path=dict_path if os.path.exists(dict_path) else None
        )

    logger.info("=" * 60)
    logger.info("STEP 2 — EXPORT (DB → chunked JSON)")
    logger.info("=" * 60)
    logger.info("Database:   %s", db_path)
    logger.info("Output dir: %s", out_dir)
    logger.info("Chunk size: %d", args.chunk_size)
    logger.info("Enrich:     %s", "yes" if args.enrich else "no")
    logger.info("")

    exporter = JsonExporter(db_path=db_path)
    count = exporter.export(
        output_path=output,
        limit=args.limit,
        full_text_only=args.full_text_only,
        with_citations_only=args.with_citations,
        min_citations=args.min_citations,
        methods_only=args.methods_only,
        chunk_size=args.chunk_size,
        enricher=enricher,
    )

    logger.info("")
    logger.info("Done. %d papers exported to %s", count, out_dir)
    logger.info("Next step: python 3_clean.py --input-dir %s", out_dir)


if __name__ == "__main__":
    main()
