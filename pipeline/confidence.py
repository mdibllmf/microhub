"""
Section-entity confidence matrix for the extraction pipeline.

Centralizes the confidence scores that all agents use, based on which
section of the paper an entity was found in.  This replaces the ad-hoc
per-agent confidence adjustments with a single source of truth.

The matrix encodes domain knowledge:
  - Techniques/equipment in Methods are highly reliable (0.95)
  - Entities in Introduction/Discussion are likely background references (0.30)
  - Title mentions of organisms are near-certain study subjects (0.95)
  - Figure captions are surprisingly rich for equipment info (0.85)

Usage:
    from pipeline.confidence import get_confidence
    conf = get_confidence("MICROSCOPY_TECHNIQUE", "methods")  # → 0.95
"""

from typing import Dict

# Section × Entity-type → confidence score
# Rows: entity labels used by agents
# Columns: section types from PaperSections

CONFIDENCE_MATRIX: Dict[str, Dict[str, float]] = {
    "MICROSCOPY_TECHNIQUE": {
        "title": 0.90,
        "abstract": 0.75,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.85,
        "discussion": 0.30,
        "introduction": 0.30,
        "figures": 0.80,
        "data_availability": 0.20,
        "full_text": 0.70,
    },
    "MICROSCOPE_BRAND": {
        "title": 0.85,
        "abstract": 0.70,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.80,
        "discussion": 0.30,
        "introduction": 0.30,
        "figures": 0.85,
        "data_availability": 0.20,
        "full_text": 0.70,
    },
    "MICROSCOPE_MODEL": {
        "title": 0.85,
        "abstract": 0.70,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.80,
        "discussion": 0.30,
        "introduction": 0.30,
        "figures": 0.85,
        "data_availability": 0.20,
        "full_text": 0.70,
    },
    "OBJECTIVE": {
        "title": 0.80,
        "abstract": 0.65,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.75,
        "discussion": 0.25,
        "introduction": 0.25,
        "figures": 0.85,
        "data_availability": 0.20,
        "full_text": 0.70,
    },
    "LASER": {
        "title": 0.80,
        "abstract": 0.65,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.75,
        "discussion": 0.25,
        "introduction": 0.25,
        "figures": 0.85,
        "data_availability": 0.20,
        "full_text": 0.70,
    },
    "DETECTOR": {
        "title": 0.80,
        "abstract": 0.65,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.75,
        "discussion": 0.25,
        "introduction": 0.25,
        "figures": 0.85,
        "data_availability": 0.20,
        "full_text": 0.70,
    },
    "FILTER": {
        "title": 0.75,
        "abstract": 0.60,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.70,
        "discussion": 0.25,
        "introduction": 0.25,
        "figures": 0.85,
        "data_availability": 0.20,
        "full_text": 0.65,
    },
    "FLUOROPHORE": {
        "title": 0.85,
        "abstract": 0.75,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.85,
        "discussion": 0.40,
        "introduction": 0.40,
        "figures": 0.85,
        "data_availability": 0.20,
        "full_text": 0.75,
    },
    "ORGANISM": {
        "title": 0.95,
        "abstract": 0.80,
        "methods": 0.90,
        "materials": 0.90,
        "results": 0.80,
        "discussion": 0.25,
        "introduction": 0.25,
        "figures": 0.70,
        "data_availability": 0.20,
        "full_text": 0.65,
    },
    "CELL_LINE": {
        "title": 0.90,
        "abstract": 0.80,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.85,
        "discussion": 0.35,
        "introduction": 0.35,
        "figures": 0.80,
        "data_availability": 0.20,
        "full_text": 0.70,
    },
    "SAMPLE_PREPARATION": {
        "title": 0.80,
        "abstract": 0.70,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.75,
        "discussion": 0.30,
        "introduction": 0.30,
        "figures": 0.75,
        "data_availability": 0.20,
        "full_text": 0.65,
    },
    "SOFTWARE": {
        "title": 0.85,
        "abstract": 0.70,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.80,
        "discussion": 0.35,
        "introduction": 0.35,
        "figures": 0.75,
        "data_availability": 0.30,
        "full_text": 0.70,
    },
    "IMAGE_ANALYSIS_SOFTWARE": {
        "title": 0.85,
        "abstract": 0.70,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.80,
        "discussion": 0.35,
        "introduction": 0.35,
        "figures": 0.75,
        "data_availability": 0.30,
        "full_text": 0.70,
    },
    "IMAGE_ACQUISITION_SOFTWARE": {
        "title": 0.85,
        "abstract": 0.70,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.80,
        "discussion": 0.35,
        "introduction": 0.35,
        "figures": 0.75,
        "data_availability": 0.30,
        "full_text": 0.70,
    },
    "GENERAL_SOFTWARE": {
        "title": 0.85,
        "abstract": 0.70,
        "methods": 0.95,
        "materials": 0.95,
        "results": 0.80,
        "discussion": 0.35,
        "introduction": 0.35,
        "figures": 0.75,
        "data_availability": 0.30,
        "full_text": 0.70,
    },
    "ANTIBODY_SOURCE": {
        "title": 0.60,
        "abstract": 0.55,
        "methods": 0.90,
        "materials": 0.90,
        "results": 0.65,
        "discussion": 0.25,
        "introduction": 0.25,
        "figures": 0.60,
        "data_availability": 0.20,
        "full_text": 0.60,
    },
    "REAGENT_SUPPLIER": {
        "title": 0.60,
        "abstract": 0.55,
        "methods": 0.90,
        "materials": 0.90,
        "results": 0.65,
        "discussion": 0.25,
        "introduction": 0.25,
        "figures": 0.60,
        "data_availability": 0.20,
        "full_text": 0.60,
    },
}

# Default confidence for entity types not in the matrix
_DEFAULT_SECTION_SCORES = {
    "title": 0.85,
    "abstract": 0.70,
    "methods": 0.95,
    "materials": 0.95,
    "results": 0.80,
    "discussion": 0.30,
    "introduction": 0.30,
    "figures": 0.80,
    "data_availability": 0.20,
    "full_text": 0.70,
}

# Minimum threshold — entities below this are extracted but flagged
DEFAULT_MIN_CONFIDENCE = 0.5


def get_confidence(entity_label: str, section: str) -> float:
    """Look up confidence for an entity type in a given section.

    Parameters
    ----------
    entity_label : str
        The label used by the agent (e.g., "MICROSCOPY_TECHNIQUE").
    section : str
        The section type (e.g., "methods", "abstract", "figures").

    Returns
    -------
    float
        Confidence score between 0.0 and 1.0.
    """
    section = (section or "full_text").lower()
    # Normalize "materials" → "methods" synonym
    if section in ("materials", "materials_and_methods"):
        section = "methods"

    scores = CONFIDENCE_MATRIX.get(entity_label, _DEFAULT_SECTION_SCORES)
    return scores.get(section, scores.get("full_text", 0.70))
