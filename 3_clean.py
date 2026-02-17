#!/usr/bin/env python3
"""
Step 3 — Clean and re-tag exported JSON files.

Reads the chunked JSON from step 2, applies protocol classification, syncs
field aliases, sets boolean flags, strips full_text, and writes final
WordPress-ready files.

    python 3_clean.py                                     # defaults
    python 3_clean.py --input-dir raw_export/             # read from step 2 output
    python 3_clean.py --output-dir cleaned_export/        # write here
    python 3_clean.py --enrich                            # re-run agents during cleanup

Input:  raw_export/*_chunk_*.json   (from step 2)
Output: cleaned_export/*_chunk_*.json (ready for step 4 and WordPress)
"""

import argparse
import glob
import json
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
        description="Step 3 — Clean and re-tag exported JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", help="Single input JSON file")
    parser.add_argument("--input-dir", help="Input directory (default: raw_export/)")
    parser.add_argument("--output-dir", default="cleaned_export",
                        help="Output directory (default: cleaned_export/)")
    parser.add_argument("--enrich", action="store_true",
                        help="Re-run agent pipeline during cleanup")

    args = parser.parse_args()

    from pipeline.export.json_exporter import is_protocol_paper, get_protocol_type
    from pipeline.normalization import normalize_tags
    from pipeline.orchestrator import PipelineOrchestrator

    # --- Resolve input files ---
    if args.input:
        input_path = args.input
        if not os.path.isabs(input_path):
            input_path = os.path.join(SCRIPT_DIR, input_path)
        input_files = [input_path]
    else:
        input_dir = args.input_dir or "raw_export"
        if not os.path.isabs(input_dir):
            input_dir = os.path.join(SCRIPT_DIR, input_dir)
        # Try several naming patterns
        input_files = sorted(glob.glob(os.path.join(input_dir, "*_chunk_*.json")))
        if not input_files:
            input_files = sorted(glob.glob(os.path.join(input_dir, "*.json")))

    if not input_files:
        logger.error("No JSON files found! Run step 2 first.")
        sys.exit(1)

    # --- Resolve output directory ---
    out_dir = args.output_dir
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(SCRIPT_DIR, out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # --- Optional agent enrichment ---
    enricher = None
    if args.enrich:
        dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
        enricher = PipelineOrchestrator(
            tag_dictionary_path=dict_path if os.path.exists(dict_path) else None
        )

    logger.info("=" * 60)
    logger.info("STEP 3 — CLEAN (re-tag + finalize JSON)")
    logger.info("=" * 60)
    logger.info("Input files: %d", len(input_files))
    logger.info("Output dir:  %s", out_dir)
    logger.info("Enrich:      %s", "yes" if args.enrich else "no")
    logger.info("")

    total_papers = 0

    for input_file in input_files:
        logger.info("Processing: %s", os.path.basename(input_file))

        with open(input_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        cleaned = []
        for paper in papers:
            # Optionally re-run agents
            if enricher is not None:
                agent_results = enricher.process_paper(paper)
                for key, val in agent_results.items():
                    if key.startswith("_"):
                        continue
                    if isinstance(val, (list, dict)) and val:
                        paper[key] = val
                    elif isinstance(val, str) and val:
                        paper[key] = val

            # Normalize tag names (scraper variants → canonical forms)
            normalize_tags(paper)

            # Protocol classification
            paper["is_protocol"] = is_protocol_paper(paper) or bool(paper.get("protocols"))
            if is_protocol_paper(paper):
                paper["post_type"] = "mh_protocol"
                paper["protocol_type"] = get_protocol_type(paper)
            else:
                paper["post_type"] = "mh_paper"
                paper["protocol_type"] = None

            # Sync aliases
            paper["techniques"] = paper.get("microscopy_techniques", [])
            paper["tags"] = paper.get("microscopy_techniques", [])
            paper["software"] = list(set(
                (paper.get("image_analysis_software") or []) +
                (paper.get("image_acquisition_software") or [])
            ))

            # Boolean flags
            paper["has_full_text"] = False
            paper["has_protocols"] = bool(paper.get("protocols")) or paper.get("is_protocol", False)
            paper["has_github"] = bool(paper.get("github_url"))
            paper["has_github_tools"] = bool(paper.get("github_tools"))
            paper["has_data"] = bool(paper.get("repositories"))
            paper["has_rrids"] = bool(paper.get("rrids"))
            paper["has_rors"] = bool(paper.get("rors"))
            paper["has_fluorophores"] = bool(paper.get("fluorophores"))
            paper["has_cell_lines"] = bool(paper.get("cell_lines"))
            paper["has_sample_prep"] = bool(paper.get("sample_preparation"))
            paper["has_antibody_sources"] = bool(paper.get("antibody_sources"))
            paper["has_methods"] = bool(paper.get("methods") and len(str(paper.get("methods", ""))) > 100)
            paper["has_institutions"] = bool(paper.get("institutions"))
            paper["has_facility"] = paper["has_institutions"]
            paper["has_affiliations"] = bool(paper.get("affiliations"))

            # Remove full_text from output
            paper.pop("full_text", None)

            cleaned.append(paper)

        # Write output
        out_file = os.path.join(out_dir, os.path.basename(input_file))
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False, default=str)

        total_papers += len(cleaned)
        logger.info("  → %d papers → %s", len(cleaned), os.path.basename(out_file))

    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 3 COMPLETE: %d papers cleaned", total_papers)
    logger.info("=" * 60)
    logger.info("Next step: python 4_validate.py --input-dir %s", out_dir)


if __name__ == "__main__":
    main()
