#!/usr/bin/env python3
"""
Step 4 — Validate cleaned JSON against the master tag dictionary.

Reads the final JSON from step 3 and checks every paper for:
  - Required fields (title, doi, pmid)
  - Tag values that exist in MASTER_TAG_DICTIONARY.json
  - Summary statistics

    python 4_validate.py                                # defaults
    python 4_validate.py --input-dir cleaned_export/    # validate specific dir
    python 4_validate.py --strict                       # exit 1 on any issue

Input:  cleaned_export/*.json   (from step 3)
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
        description="Step 4 — Validate cleaned JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input-dir",
                        help="Directory to validate (default: cleaned_export/)")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if any issues found")

    args = parser.parse_args()

    from pipeline.validation.tag_validator import TagValidator

    dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
    validator = TagValidator(dict_path)

    # --- Find files ---
    target_dir = args.input_dir or "cleaned_export"
    if not os.path.isabs(target_dir):
        target_dir = os.path.join(SCRIPT_DIR, target_dir)

    files = sorted(glob.glob(os.path.join(target_dir, "*.json")))
    if not files:
        logger.error("No JSON files found in %s", target_dir)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("STEP 4 — VALIDATE")
    logger.info("=" * 60)
    logger.info("Directory: %s", target_dir)
    logger.info("Files:     %d", len(files))
    logger.info("")

    # Tag categories to validate
    tag_categories = [
        ("microscopy_techniques", "microscopy_techniques"),
        ("microscope_brands", "microscope_brands"),
        ("microscope_models", "microscope_models"),
        ("fluorophores", "fluorophores"),
        ("organisms", "organisms"),
        ("cell_lines", "cell_lines"),
        ("sample_preparation", "sample_preparation"),
        ("image_analysis_software", "image_analysis_software"),
        ("image_acquisition_software", "image_acquisition_software"),
        ("general_software", "general_software"),
        ("reagent_suppliers", "reagent_suppliers"),
        ("antibody_sources", "antibody_sources"),
    ]

    total_papers = 0
    total_issues = 0
    missing_fields = {"title": 0, "doi": 0, "pmid": 0}
    invalid_tags = {}

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        file_issues = 0
        for paper in papers:
            # Check required fields
            for field in ["title", "doi", "pmid"]:
                if not paper.get(field):
                    file_issues += 1
                    missing_fields[field] += 1

            # Validate tag categories
            for category, field in tag_categories:
                values = paper.get(field, [])
                if isinstance(values, list):
                    for v in values:
                        if not validator.is_valid(category, v):
                            file_issues += 1
                            invalid_tags.setdefault(category, {})
                            invalid_tags[category][v] = invalid_tags[category].get(v, 0) + 1

        total_papers += len(papers)
        total_issues += file_issues

        status = "OK" if file_issues == 0 else f"{file_issues} issues"
        logger.info("  %s: %d papers — %s", os.path.basename(fp), len(papers), status)

    # --- Summary ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info("Total papers:  %d", total_papers)
    logger.info("Total issues:  %d", total_issues)
    logger.info("")

    if any(missing_fields.values()):
        logger.info("Missing required fields:")
        for field, count in missing_fields.items():
            if count > 0:
                logger.info("  %-10s  %d papers", field, count)
        logger.info("")

    if invalid_tags:
        logger.info("Invalid tag values (top occurrences):")
        for category, values in sorted(invalid_tags.items()):
            top = sorted(values.items(), key=lambda x: -x[1])[:5]
            logger.info("  %s:", category)
            for v, count in top:
                logger.info("    %-30s  (%d)", v, count)
        logger.info("")

    if total_issues == 0:
        logger.info("All papers passed validation.")
    else:
        logger.info("%d issues found across %d papers.", total_issues, total_papers)

    if args.strict and total_issues > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
