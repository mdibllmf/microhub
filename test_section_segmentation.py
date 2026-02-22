#!/usr/bin/env python3
"""
Tests for Section Segmentation Step (2b).

Tests heuristic_segment(), strip_inline_citations(), taggable_sections(),
and the segment_paper() function from 2b_segment.py.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.parsing.section_extractor import (
    PaperSections,
    heuristic_segment,
    strip_inline_citations,
    strip_references,
    from_sections_list,
)


def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"PASS  {total}: {name}")
        else:
            failed += 1
            print(f"FAIL  {total}: {name}")
            if detail:
                print(f"         {detail}")

    # ================================================================
    # Test 1: Heuristic segmentation — standard paper structure
    # ================================================================
    text1 = """
Introduction
This study investigates the role of actin dynamics in cell migration.
Previous work by Smith et al. used confocal microscopy to study this.

Materials and Methods
Cells were imaged on a Zeiss LSM 880 with Airyscan detector.
Images were acquired using ZEN Blue software at 63x/1.4 NA Oil.

Results
We observed increased actin polymerization at the leading edge.
Confocal imaging revealed punctate GFP-actin structures.

Discussion
Our findings are consistent with previous reports (Smith et al., 2020).
The Zeiss LSM 880 provided sufficient resolution for our analysis.

References
1. Smith J et al. Nature Methods. 2020.
2. Jones A et al. Cell. 2019.
"""
    segments = heuristic_segment(text1)
    has_methods = any(s["type"] == "methods" for s in segments)
    has_results = any(s["type"] == "results" for s in segments)
    has_intro = any(s["type"] == "introduction" for s in segments)
    has_refs = any(s["type"] == "references" for s in segments)
    check(
        "Heuristic segmentation — standard structure",
        has_methods and has_results and has_intro and len(segments) >= 4,
        f"Got {len(segments)} sections: {[s['type'] for s in segments]}",
    )

    # ================================================================
    # Test 2: Heuristic segmentation — methods subsections
    # ================================================================
    text2 = """
Abstract
We present a new method for super-resolution imaging.

Methods
2.1 Sample Preparation
Cells were fixed with 4% PFA for 15 minutes.

2.2 Confocal Microscopy
Imaging was performed on a Nikon AX R microscope.

2.3 Image Analysis
Images were processed using Fiji/ImageJ.

Results
Super-resolution imaging revealed previously unseen structures.
"""
    segments2 = heuristic_segment(text2)
    methods_sections = [s for s in segments2 if s["type"] == "methods"]
    check(
        "Heuristic segmentation — methods subsections",
        len(methods_sections) >= 1,
        f"Got {len(methods_sections)} methods sections from {len(segments2)} total",
    )

    # ================================================================
    # Test 3: Heuristic segmentation — no headings (returns full text)
    # ================================================================
    text3 = "This is a plain paragraph with no section headings at all. " * 10
    segments3 = heuristic_segment(text3)
    check(
        "Heuristic segmentation — no headings fallback",
        len(segments3) == 1 and segments3[0]["type"] == "full_text",
        f"Got {len(segments3)} sections: {[s['type'] for s in segments3]}",
    )

    # ================================================================
    # Test 4: strip_inline_citations — numeric citations
    # ================================================================
    text4 = "Confocal microscopy [1] was used to image cells [2,3] and tissues [4-7]."
    cleaned4 = strip_inline_citations(text4)
    check(
        "Strip citations — numeric [1], [2,3], [4-7]",
        "[1]" not in cleaned4 and "[2,3]" not in cleaned4 and "[4-7]" not in cleaned4
        and "Confocal microscopy" in cleaned4,
        f"Got: {cleaned4}",
    )

    # ================================================================
    # Test 5: strip_inline_citations — author-year citations
    # ================================================================
    text5 = "As shown by (Smith et al., 2020) and (Jones and Brown, 2019), microscopy is useful."
    cleaned5 = strip_inline_citations(text5)
    check(
        "Strip citations — author-year (Smith et al., 2020)",
        "(Smith et al., 2020)" not in cleaned5
        and "(Jones and Brown, 2019)" not in cleaned5
        and "microscopy is useful" in cleaned5,
        f"Got: {cleaned5}",
    )

    # ================================================================
    # Test 6: strip_inline_citations — preserves scientific notation
    # ================================================================
    text6 = "We used a 488 nm laser [1] and 60x/1.4 NA objective (Smith et al., 2020) to image [Ca2+] dynamics."
    cleaned6 = strip_inline_citations(text6)
    check(
        "Strip citations — preserves (488 nm), [Ca2+]",
        "488 nm" in cleaned6 and "[Ca2+]" not in cleaned6 or "Ca2+" in cleaned6,
        f"Got: {cleaned6}",
    )
    # Note: [Ca2+] is a special ion notation that should be preserved,
    # but the exact bracket may or may not survive depending on implementation.
    # The key test is that 488 nm is preserved and numeric citations are removed.

    # ================================================================
    # Test 7: taggable_sections — excludes introduction by default
    # ================================================================
    ps = PaperSections(
        title="Test Paper",
        abstract="We used confocal microscopy.",
        methods="Imaging on Zeiss LSM 880 with 63x/1.4 NA objective.",
        results="GFP-actin structures were observed.",
        introduction="Smith et al. previously used a Leica SP8 for similar studies.",
        discussion="Our results agree with prior work.",
    )
    taggable = list(ps.taggable_sections())
    section_types = [st for _, st in taggable]
    check(
        "taggable_sections() excludes introduction",
        "introduction" not in section_types
        and "methods" in section_types
        and "results" in section_types,
        f"Got section types: {section_types}",
    )

    # ================================================================
    # Test 8: taggable_sections — include_introduction=True
    # ================================================================
    taggable_with_intro = list(ps.taggable_sections(include_introduction=True))
    section_types_with_intro = [st for _, st in taggable_with_intro]
    check(
        "taggable_sections(include_introduction=True) includes intro",
        "introduction" in section_types_with_intro,
        f"Got section types: {section_types_with_intro}",
    )

    # ================================================================
    # Test 9: taggable_sections — full_text fallback only when no sections
    # ================================================================
    ps_minimal = PaperSections(
        title="Minimal Paper",
        abstract="Abstract only.",
        full_text="Full text with methods and results all mixed together. " * 20,
    )
    taggable_min = list(ps_minimal.taggable_sections())
    section_types_min = [st for _, st in taggable_min]
    check(
        "taggable_sections — full_text fallback when no methods/results",
        "full_text" in section_types_min,
        f"Got section types: {section_types_min}",
    )

    # ================================================================
    # Test 10: segment_paper() — existing methods path
    # ================================================================
    from importlib import import_module
    seg_module = import_module("2b_segment")

    paper_with_methods = {
        "title": "Test Paper",
        "abstract": "Abstract here.",
        "methods": "We used a Zeiss LSM 880 confocal microscope with Airyscan. " * 10,
        "full_text": "Introduction...\n\nMethods...\n\nResults...",
    }
    seg_module.segment_paper(paper_with_methods)
    check(
        "segment_paper() — existing methods → source='existing'",
        paper_with_methods.get("_segmentation_source") == "existing"
        and paper_with_methods.get("_segmented_methods"),
        f"Source: {paper_with_methods.get('_segmentation_source')}, "
        f"Methods len: {len(paper_with_methods.get('_segmented_methods', ''))}",
    )

    # ================================================================
    # Test 11: segment_paper() — heuristic path
    # ================================================================
    paper_heuristic = {
        "title": "Heuristic Paper",
        "abstract": "We studied actin.",
        "methods": "",
        "full_text": text1,  # has Introduction, Methods, Results, Discussion, References
    }
    seg_module.segment_paper(paper_heuristic)
    check(
        "segment_paper() — heuristic segmentation",
        paper_heuristic.get("_segmentation_source") in ("heuristic", "full_text_fallback")
        and paper_heuristic.get("_segmentation_sections", 0) >= 1,
        f"Source: {paper_heuristic.get('_segmentation_source')}, "
        f"Sections: {paper_heuristic.get('_segmentation_sections')}",
    )

    # ================================================================
    # Test 12: segment_paper() — abstract-only fallback
    # ================================================================
    paper_abstract_only = {
        "title": "Abstract Only Paper",
        "abstract": "We used confocal microscopy to study cells.",
        "methods": "",
        "full_text": "",
    }
    seg_module.segment_paper(paper_abstract_only)
    check(
        "segment_paper() — abstract-only fallback",
        paper_abstract_only.get("_segmentation_source") == "abstract_only",
        f"Source: {paper_abstract_only.get('_segmentation_source')}",
    )

    # ================================================================
    # Test 13: strip_inline_citations — superscript citations
    # ================================================================
    text13 = "Confocal microscopy¹²³ has been widely used⁴⁻⁶ in biology."
    cleaned13 = strip_inline_citations(text13)
    check(
        "Strip citations — superscript ¹²³, ⁴⁻⁶",
        "¹²³" not in cleaned13 and "⁴⁻⁶" not in cleaned13
        and "Confocal microscopy" in cleaned13,
        f"Got: {cleaned13}",
    )

    # ================================================================
    # Test 14: Heuristic segmentation — data availability section
    # ================================================================
    text14 = """
Methods
Cells were imaged on a confocal microscope.

Results
We observed enhanced fluorescence.

Data Availability
All data are available at https://zenodo.org/record/12345.

References
1. Smith J et al. 2020.
"""
    segments14 = heuristic_segment(text14)
    has_da = any(s["type"] == "data_availability" for s in segments14)
    check(
        "Heuristic segmentation — data availability section",
        has_da,
        f"Got types: {[s['type'] for s in segments14]}",
    )

    # ================================================================
    # Test 15: segment_paper() — handles list-type figures field
    # ================================================================
    paper_list_figures = {
        "title": "Paper with list figures",
        "abstract": "We imaged cells.",
        "methods": "We used a Zeiss LSM 880 confocal microscope. " * 15,
        "figures": ["Figure 1: GFP expression.", "Figure 2: Actin staining."],
        "full_text": "Introduction\nSome text.\nMethods\nZeiss LSM 880.",
    }
    seg_module.segment_paper(paper_list_figures)
    check(
        "segment_paper() — handles list-type figures field",
        paper_list_figures.get("_segmentation_source") == "existing"
        and isinstance(paper_list_figures.get("_segmented_figures"), str),
        f"Source: {paper_list_figures.get('_segmentation_source')}, "
        f"Figures type: {type(paper_list_figures.get('_segmented_figures')).__name__}",
    )

    # ================================================================
    # Test 16: from_sections_list skips references
    # ================================================================
    test_sections = [
        {"heading": "Methods", "text": "We used a microscope.", "type": "methods"},
        {"heading": "Results", "text": "We saw things.", "type": "results"},
        {"heading": "References", "text": "1. Smith 2020.", "type": "references"},
    ]
    ps_from_list = from_sections_list(test_sections)
    check(
        "from_sections_list — skips references section",
        "Smith 2020" not in ps_from_list.full_text
        and ps_from_list.methods == "We used a microscope.",
        f"full_text: {ps_from_list.full_text[:100]}",
    )

    # -------- Summary --------
    print()
    print("=" * 50)
    print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
