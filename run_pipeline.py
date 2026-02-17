#!/usr/bin/env python3
"""
MicroHub Multi-Agent NLP Pipeline v6.0
=======================================

Main entry point for the microscopy paper metadata extraction pipeline.

Architecture:
  GROBID / PubMed Parser  →  Specialized Extraction Agents  →  Validation  →  JSON Export

Modes:
  scrape     - Scrape new papers from PubMed and extract metadata
  enrich     - Re-run agents on existing DB data for better tag extraction
  export     - Export DB to WordPress-compatible JSON (identical format)
  validate   - Validate exported JSON against master tag dictionary

Usage:
  python run_pipeline.py export                          # Export all (default)
  python run_pipeline.py export --enrich                 # Re-run agents then export
  python run_pipeline.py export --chunk-size 500         # 500 papers per file
  python run_pipeline.py export --output-dir cleaned_export  # Output to cleaned_export/
  python run_pipeline.py scrape --limit 100              # Scrape 100 new papers
  python run_pipeline.py validate                        # Validate existing exports

CRITICAL: JSON output format is identical to v5.1 to prevent WordPress upload issues.
"""

import argparse
import logging
import os
import sys
import glob
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Script directory for default paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def cmd_export(args):
    """Export papers from DB to chunked JSON for WordPress."""
    from pipeline.export.json_exporter import JsonExporter
    from pipeline.orchestrator import PipelineOrchestrator

    db_path = args.db or os.path.join(SCRIPT_DIR, "microhub.db")
    output = args.output or os.path.join(SCRIPT_DIR, "microhub_papers_v5.json")

    # If output-dir specified, place output there
    if args.output_dir:
        out_dir = args.output_dir
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(SCRIPT_DIR, out_dir)
        os.makedirs(out_dir, exist_ok=True)
        output = os.path.join(out_dir, os.path.basename(output))

    enricher = None
    if args.enrich:
        logger.info("Agent enrichment enabled -- tags will be refreshed")
        dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
        enricher = PipelineOrchestrator(
            tag_dictionary_path=dict_path if os.path.exists(dict_path) else None
        )

    exporter = JsonExporter(db_path=db_path)
    exporter.export(
        output_path=output,
        limit=args.limit,
        full_text_only=args.full_text_only,
        with_citations_only=args.with_citations,
        min_citations=args.min_citations,
        methods_only=args.methods_only,
        chunk_size=args.chunk_size,
        enricher=enricher,
    )


def cmd_scrape(args):
    """Scrape papers from PubMed -- delegates to the backup scraper for now."""
    backup_scraper = os.path.join(SCRIPT_DIR, "backup", "microhub_scraper.py")
    if os.path.exists(backup_scraper):
        logger.info("Delegating to backup scraper: %s", backup_scraper)
        # Forward all arguments
        import subprocess
        cmd = [sys.executable, backup_scraper]
        if args.limit:
            cmd += ["--limit", str(args.limit)]
        subprocess.run(cmd, check=True)
    else:
        logger.error("Scraper not found. Expected at: %s", backup_scraper)
        sys.exit(1)


def cmd_cleanup(args):
    """Run cleanup and re-tagging on exported JSON files.

    This is the final step that produces the cleaned_export/ files
    ready for WordPress import.
    """
    from pipeline.export.json_exporter import JsonExporter
    from pipeline.orchestrator import PipelineOrchestrator

    # Find input JSON files
    if args.input:
        input_path = args.input
        if not os.path.isabs(input_path):
            input_path = os.path.join(SCRIPT_DIR, input_path)
        input_files = [input_path]
    else:
        pattern = os.path.join(SCRIPT_DIR, "microhub_papers_v*_chunk_*.json")
        input_files = sorted(glob.glob(pattern))
        if not input_files:
            pattern = os.path.join(SCRIPT_DIR, "*_chunk_*.json")
            input_files = sorted(glob.glob(pattern))

    if not input_files:
        logger.error("No JSON files found to clean!")
        sys.exit(1)

    # Output directory
    out_dir = args.output_dir or "cleaned_export"
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(SCRIPT_DIR, out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Optionally set up enricher for re-running agents
    enricher = None
    if args.enrich:
        dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
        enricher = PipelineOrchestrator(
            tag_dictionary_path=dict_path if os.path.exists(dict_path) else None
        )

    logger.info("=" * 60)
    logger.info("MICROHUB CLEANUP v6.0 - AGENT PIPELINE")
    logger.info("=" * 60)
    logger.info("Input files: %d", len(input_files))
    logger.info("Output dir:  %s", out_dir)

    total_papers = 0
    for input_file in input_files:
        logger.info("Processing: %s", input_file)
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

            # Apply protocol classification
            from pipeline.export.json_exporter import is_protocol_paper, get_protocol_type
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
        logger.info("  Saved %d papers to %s", len(cleaned), out_file)

    logger.info("")
    logger.info("=" * 60)
    logger.info("CLEANUP COMPLETE: %d papers processed", total_papers)
    logger.info("=" * 60)


def cmd_validate(args):
    """Validate exported JSON files."""
    from pipeline.validation.tag_validator import TagValidator

    dict_path = os.path.join(SCRIPT_DIR, "MASTER_TAG_DICTIONARY.json")
    validator = TagValidator(dict_path)

    # Find files to validate
    target_dir = args.input_dir or os.path.join(SCRIPT_DIR, "cleaned_export")
    if not os.path.isabs(target_dir):
        target_dir = os.path.join(SCRIPT_DIR, target_dir)

    files = sorted(glob.glob(os.path.join(target_dir, "*.json")))
    if not files:
        logger.error("No JSON files found in %s", target_dir)
        sys.exit(1)

    logger.info("Validating %d files in %s", len(files), target_dir)

    total_papers = 0
    total_issues = 0
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        issues = 0
        for paper in papers:
            # Check required fields
            for field in ["title", "doi", "pmid"]:
                if not paper.get(field):
                    issues += 1

            # Validate tag categories
            for category, field in [
                ("microscopy_techniques", "microscopy_techniques"),
                ("microscope_brands", "microscope_brands"),
                ("fluorophores", "fluorophores"),
                ("organisms", "organisms"),
                ("cell_lines", "cell_lines"),
                ("sample_preparation", "sample_preparation"),
            ]:
                values = paper.get(field, [])
                if isinstance(values, list):
                    for v in values:
                        if not validator.is_valid(category, v):
                            issues += 1

        total_papers += len(papers)
        total_issues += issues
        logger.info("  %s: %d papers, %d issues", os.path.basename(fp), len(papers), issues)

    logger.info("")
    logger.info("Validation complete: %d papers, %d issues", total_papers, total_issues)


def main():
    parser = argparse.ArgumentParser(
        description="MicroHub Multi-Agent NLP Pipeline v6.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline command")

    # ---- export ----
    p_export = subparsers.add_parser("export", help="Export DB to WordPress JSON")
    p_export.add_argument("--db", help="Database path (default: microhub.db)")
    p_export.add_argument("--output", "-o", help="Output filename")
    p_export.add_argument("--output-dir", help="Output directory")
    p_export.add_argument("--limit", type=int, help="Limit papers")
    p_export.add_argument("--full-text-only", action="store_true")
    p_export.add_argument("--with-citations", action="store_true")
    p_export.add_argument("--min-citations", type=int, default=0)
    p_export.add_argument("--methods-only", action="store_true")
    p_export.add_argument("--chunk-size", type=int, default=500)
    p_export.add_argument("--enrich", action="store_true",
                          help="Re-run agent pipeline for fresh tag extraction")

    # ---- scrape ----
    p_scrape = subparsers.add_parser("scrape", help="Scrape new papers from PubMed")
    p_scrape.add_argument("--limit", type=int, help="Limit papers")

    # ---- cleanup ----
    p_cleanup = subparsers.add_parser("cleanup", help="Clean and re-tag exported JSON")
    p_cleanup.add_argument("--input", "-i", help="Input JSON file")
    p_cleanup.add_argument("--output-dir", default="cleaned_export")
    p_cleanup.add_argument("--enrich", action="store_true",
                           help="Re-run agent pipeline during cleanup")

    # ---- validate ----
    p_validate = subparsers.add_parser("validate", help="Validate exported JSON")
    p_validate.add_argument("--input-dir", help="Directory to validate")

    args = parser.parse_args()

    if args.command == "export":
        cmd_export(args)
    elif args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)
    elif args.command == "validate":
        cmd_validate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
