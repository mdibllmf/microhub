#!/usr/bin/env python3
"""
Step 2b — Section Segmentation.

Reads the chunked JSON from step 2 (which preserves full_text), segments
each paper's full text into structured sections, strips inline citations
and references, and writes section-annotated JSON for step 3.

This step solves systematic over-tagging: without segmentation, the
entire full_text (including introduction, literature review, and
references) is fed to extraction agents, causing entities merely
REFERENCED in other papers to be tagged as if THIS paper used them.

Segmentation priority:
  1. Existing structured sections (methods, results already present)
  2. Heuristic heading-based segmentation of full_text
  3. Abstract-only fallback

    python 2b_segment.py                                  # defaults
    python 2b_segment.py --input-dir raw_export/          # custom input
    python 2b_segment.py --output-dir segmented_export/   # custom output
    python 2b_segment.py --no-strip-citations             # keep inline citations
    python 2b_segment.py --include-introduction           # don't exclude introduction

Input:  raw_export/*_chunk_*.json         (from step 2)
Output: segmented_export/*_chunk_*.json   (for step 3)
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


def segment_paper(paper, *, strip_citations=True, include_introduction=False):
    """Segment a single paper dict, adding _segmented_* fields.

    Priority order:
      1. Existing structured sections (methods/results already present
         from Europe PMC, GROBID, or step 1)
      2. Heuristic heading-based segmentation of full_text
      3. Abstract-only fallback (no segmentation possible)

    Adds these fields to the paper dict:
      _segmented_methods:   str — methods text (citation-stripped)
      _segmented_results:   str — results text (citation-stripped)
      _segmented_discussion: str — discussion text (citation-stripped)
      _segmented_figures:   str — figure captions (citation-stripped)
      _segmented_data_availability: str — data/code availability
      _segmentation_source: str — how segmentation was achieved
      _segmentation_sections: int — number of sections detected

    Returns the paper dict (modified in place).
    """
    from pipeline.parsing.section_extractor import (
        heuristic_segment,
        strip_inline_citations,
        strip_references,
        _extract_figure_captions,
        _extract_data_availability,
        from_sections_list,
    )

    full_text = paper.get("full_text", "") or ""
    existing_methods = paper.get("methods", "") or ""
    existing_abstract = paper.get("abstract", "") or ""

    source = "none"
    num_sections = 0

    # Helper to optionally strip citations
    def _clean(text):
        if not text:
            return ""
        # Handle list values (e.g. figures stored as list in JSON)
        if isinstance(text, list):
            text = " ".join(str(t) for t in text if t)
        if not isinstance(text, str):
            text = str(text)
        if strip_citations:
            text = strip_inline_citations(text)
        return text.strip()

    # ---- Strategy 1: Use existing structured sections ----
    if existing_methods and len(existing_methods) > 100:
        # Already have methods from JATS/GROBID — use as-is
        paper["_segmented_methods"] = _clean(existing_methods)
        paper["_segmented_results"] = _clean(paper.get("results", "") or "")
        paper["_segmented_discussion"] = _clean(paper.get("discussion", "") or "")

        # Still extract figures and data_availability from full_text if available
        if full_text:
            if not paper.get("_segmented_figures"):
                paper["_segmented_figures"] = _clean(
                    paper.get("figures", "") or _extract_figure_captions(full_text)
                )
            if not paper.get("_segmented_data_availability"):
                paper["_segmented_data_availability"] = _clean(
                    paper.get("data_availability", "") or _extract_data_availability(full_text)
                )
        else:
            paper["_segmented_figures"] = _clean(paper.get("figures", "") or "")
            paper["_segmented_data_availability"] = _clean(
                paper.get("data_availability", "") or ""
            )

        source = "existing"
        # Count how many sections we have
        num_sections = sum(1 for f in [
            paper.get("_segmented_methods"),
            paper.get("_segmented_results"),
            paper.get("_segmented_discussion"),
            paper.get("_segmented_figures"),
            paper.get("_segmented_data_availability"),
        ] if f)

    # ---- Strategy 2: Heuristic segmentation of full_text ----
    elif full_text and len(full_text) > 200:
        # Strip references first
        text_clean = strip_references(full_text)

        # Run heuristic segmentation
        segments = heuristic_segment(text_clean)
        num_sections = len(segments)

        if num_sections > 1:
            # Build PaperSections from heuristic segments
            ps = from_sections_list(segments, paper)

            paper["_segmented_methods"] = _clean(ps.methods)
            paper["_segmented_results"] = _clean(ps.results)
            paper["_segmented_discussion"] = _clean(ps.discussion)
            paper["_segmented_figures"] = _clean(
                ps.figures or _extract_figure_captions(full_text)
            )
            paper["_segmented_data_availability"] = _clean(
                ps.data_availability or _extract_data_availability(full_text)
            )

            # If heuristic found methods, also update top-level methods
            # so downstream agents get proper section data
            if ps.methods and len(ps.methods) > 100:
                paper["methods"] = ps.methods

            source = "heuristic"
        else:
            # Heuristic couldn't find headings — use full text as methods fallback
            paper["_segmented_methods"] = _clean(text_clean)
            paper["_segmented_results"] = ""
            paper["_segmented_discussion"] = ""
            paper["_segmented_figures"] = _clean(_extract_figure_captions(full_text))
            paper["_segmented_data_availability"] = _clean(
                _extract_data_availability(full_text)
            )
            source = "full_text_fallback"
            num_sections = 1

    # ---- Strategy 3: Abstract-only fallback ----
    else:
        paper["_segmented_methods"] = ""
        paper["_segmented_results"] = ""
        paper["_segmented_discussion"] = ""
        paper["_segmented_figures"] = ""
        paper["_segmented_data_availability"] = _clean(
            paper.get("data_availability", "") or ""
        )
        source = "abstract_only"

    paper["_segmentation_source"] = source
    paper["_segmentation_sections"] = num_sections

    return paper


def main():
    parser = argparse.ArgumentParser(
        description="Step 2b — Section Segmentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input-dir",
                        help="Input directory (default: raw_export/)")
    parser.add_argument("--output-dir", default="segmented_export",
                        help="Output directory (default: segmented_export/)")
    parser.add_argument("--no-strip-citations", action="store_true",
                        help="Do not strip inline citations")
    parser.add_argument("--include-introduction", action="store_true",
                        help="Include introduction in taggable sections")

    args = parser.parse_args()

    # --- Resolve input files ---
    input_dir = args.input_dir
    if input_dir:
        if not os.path.isabs(input_dir):
            input_dir = os.path.join(SCRIPT_DIR, input_dir)
    else:
        # Auto-detect: prefer raw_export/
        raw_export_dir = os.path.join(SCRIPT_DIR, "raw_export")
        if os.path.isdir(raw_export_dir) and glob.glob(os.path.join(raw_export_dir, "*.json")):
            input_dir = raw_export_dir
        else:
            input_dir = SCRIPT_DIR

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

    strip_citations = not args.no_strip_citations

    logger.info("=" * 60)
    logger.info("STEP 2b — SECTION SEGMENTATION")
    logger.info("=" * 60)
    logger.info("Input files:      %d", len(input_files))
    logger.info("Output dir:       %s", out_dir)
    logger.info("Strip citations:  %s", "yes" if strip_citations else "no")
    logger.info("Incl. intro:      %s", "yes" if args.include_introduction else "no")
    logger.info("")

    total_papers = 0
    stats = {
        "existing": 0,
        "heuristic": 0,
        "full_text_fallback": 0,
        "abstract_only": 0,
        "none": 0,
    }

    for input_file in input_files:
        logger.info("Processing: %s", os.path.basename(input_file))

        with open(input_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        if not isinstance(papers, list):
            papers = [papers]

        for paper in papers:
            segment_paper(
                paper,
                strip_citations=strip_citations,
                include_introduction=args.include_introduction,
            )
            source = paper.get("_segmentation_source", "none")
            stats[source] = stats.get(source, 0) + 1

        # Write output
        out_file = os.path.join(out_dir, os.path.basename(input_file))
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=2, ensure_ascii=False, default=str)

        total_papers += len(papers)
        logger.info("  → %d papers → %s", len(papers), os.path.basename(out_file))

    logger.info("")
    logger.info("=" * 60)
    logger.info("STEP 2b COMPLETE: %d papers segmented", total_papers)
    logger.info("=" * 60)
    logger.info("")
    logger.info("SEGMENTATION STATISTICS:")
    logger.info("  Existing sections:    %d", stats["existing"])
    logger.info("  Heuristic segmented:  %d", stats["heuristic"])
    logger.info("  Full-text fallback:   %d", stats["full_text_fallback"])
    logger.info("  Abstract-only:        %d", stats["abstract_only"])
    logger.info("")
    logger.info("Next step: python 3_clean.py --input-dir %s", out_dir)


if __name__ == "__main__":
    main()
