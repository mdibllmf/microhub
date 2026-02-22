"""
Microscope Knowledge Base loader — singleton module for KB data.

Loads all KB JSON files once at import time and provides lookup functions
for alias resolution, brand inference, technique inference, and software
mapping.  Used by equipment_agent.py, software_agent.py, and orchestrator.py.

The KB directory is ``microscopy_kb/`` at the project root.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_KB_DIR = os.path.join(_PROJECT_ROOT, "microscopy_kb")

# ======================================================================
# Module-level singleton state (loaded once)
# ======================================================================

_kb: Optional[Dict] = None


def load_kb(kb_dir: str = None) -> Dict:
    """Load all KB files.  Returns dict with keys:
    systems, aliases, brand_software, lasers, alias_to_canonical, canonical_to_system.

    Results are cached — subsequent calls return the same dict.
    """
    global _kb
    if _kb is not None:
        return _kb

    kb_dir = kb_dir or _DEFAULT_KB_DIR
    _kb = {
        "systems": [],
        "aliases": {},          # canonical → [alias, ...]
        "brand_software": {},   # brand → {acquisition, analysis, ...}
        "lasers": [],
        # Derived indexes
        "alias_to_canonical": {},   # lowercase alias → "Brand Model"
        "canonical_to_system": {},  # "Brand Model" → system dict
    }

    # 1. microscope_kb.json
    systems_path = os.path.join(kb_dir, "microscope_kb.json")
    if os.path.isfile(systems_path):
        try:
            with open(systems_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _kb["systems"] = data.get("systems", [])
            logger.info("KB: loaded %d systems from microscope_kb.json",
                        len(_kb["systems"]))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("KB: failed to load microscope_kb.json: %s", exc)

    # 2. model_aliases.json
    aliases_path = os.path.join(kb_dir, "model_aliases.json")
    if os.path.isfile(aliases_path):
        try:
            with open(aliases_path, "r", encoding="utf-8") as f:
                _kb["aliases"] = json.load(f)
            logger.info("KB: loaded %d alias groups from model_aliases.json",
                        len(_kb["aliases"]))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("KB: failed to load model_aliases.json: %s", exc)

    # 3. brand_software_map.json
    sw_path = os.path.join(kb_dir, "brand_software_map.json")
    if os.path.isfile(sw_path):
        try:
            with open(sw_path, "r", encoding="utf-8") as f:
                _kb["brand_software"] = json.load(f)
            logger.info("KB: loaded %d brand→software mappings",
                        len(_kb["brand_software"]))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("KB: failed to load brand_software_map.json: %s", exc)

    # 4. laser_systems.json
    laser_path = os.path.join(kb_dir, "laser_systems.json")
    if os.path.isfile(laser_path):
        try:
            with open(laser_path, "r", encoding="utf-8") as f:
                _kb["lasers"] = json.load(f)
            logger.info("KB: loaded %d laser systems", len(_kb["lasers"]))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("KB: failed to load laser_systems.json: %s", exc)

    # Build derived indexes
    _build_indexes(_kb)

    return _kb


def _build_indexes(kb: Dict) -> None:
    """Build fast lookup indexes from raw KB data."""

    # canonical_to_system: "Brand Model" → system dict (from microscope_kb.json)
    for sys in kb["systems"]:
        canonical = f"{sys['brand']} {sys['model']}"
        kb["canonical_to_system"][canonical.lower()] = sys
        # Also index by bare model
        kb["canonical_to_system"][sys["model"].lower()] = sys

    # alias_to_canonical: lowercase alias → "Brand Model" (from model_aliases.json)
    for canonical, alias_list in kb["aliases"].items():
        canonical_lower = canonical.lower()
        kb["alias_to_canonical"][canonical_lower] = canonical
        for alias in alias_list:
            kb["alias_to_canonical"][alias.lower()] = canonical
            # Also add stripped version (no spaces/hyphens) for fuzzy matching
            stripped = re.sub(r"[\s\-]+", "", alias.lower())
            if stripped != alias.lower():
                kb["alias_to_canonical"][stripped] = canonical


# ======================================================================
# Ambiguous aliases — common English words that need microscopy context
# ======================================================================

_AMBIGUOUS_ALIASES: Set[str] = {
    "fire", "fusion", "lightning", "spark", "quest", "neo", "sona",
    "evolve", "prime", "edge", "talos", "titan", "discovery", "thunder",
    "mica", "vivo", "mom", "ax", "ti",
}

# Context words that indicate microscopy equipment
_MICROSCOPY_CONTEXT_RE = re.compile(
    r"\b(?:microscop|confocal|camera|detector|system|imaging|fluorescen|"
    r"objective|laser|sCMOS|EMCCD|two.?photon|multiphoton|"
    r"super.?resolution|light.?sheet|spinning.?disk|"
    r"Zeiss|Leica|Nikon|Olympus|Evident|Andor|Hamamatsu|"
    r"Yokogawa|Bruker|Thorlabs|Abberior|PerkinElmer|Revvity|"
    r"Photometrics|PCO|FEI|JEOL|Thermo\s+Fisher)\b",
    re.IGNORECASE,
)


def _is_ambiguous_alias(alias_lower: str) -> bool:
    """Check if an alias is a common English word that needs context."""
    return alias_lower in _AMBIGUOUS_ALIASES


# ======================================================================
# Public lookup functions
# ======================================================================

def resolve_alias(text: str) -> Optional[Dict]:
    """Given free text like 'LSM 880' or 'Stellaris 8', return the full
    system dict from microscope_kb.json, or None.

    Matching strategies (in order):
    1. Exact match in alias_to_canonical (lowercased)
    2. Fuzzy: strip whitespace/punctuation (e.g. "LSM880" → "LSM 880")
    3. Substring: try brand+model combos
    """
    kb = load_kb()
    text_lower = text.strip().lower()

    # 1. Exact match
    canonical = kb["alias_to_canonical"].get(text_lower)
    if canonical:
        system = kb["canonical_to_system"].get(canonical.lower())
        if system:
            return system

    # 2. Fuzzy: strip spaces/hyphens
    stripped = re.sub(r"[\s\-]+", "", text_lower)
    canonical = kb["alias_to_canonical"].get(stripped)
    if canonical:
        system = kb["canonical_to_system"].get(canonical.lower())
        if system:
            return system

    # 3. Substring: iterate systems and check if text matches brand+model
    for sys in kb["systems"]:
        full_name = f"{sys['brand']} {sys['model']}".lower()
        if full_name in text_lower or text_lower in full_name:
            return sys

    return None


def infer_brand_from_model(model: str) -> Optional[str]:
    """Given a model name, return the canonical brand."""
    kb = load_kb()
    model_lower = model.strip().lower()

    # Check alias_to_canonical first
    canonical = kb["alias_to_canonical"].get(model_lower)
    if canonical:
        # Canonical format is "Brand Model" — extract brand
        system = kb["canonical_to_system"].get(canonical.lower())
        if system:
            return system.get("brand")

    # Check stripped version
    stripped = re.sub(r"[\s\-]+", "", model_lower)
    canonical = kb["alias_to_canonical"].get(stripped)
    if canonical:
        system = kb["canonical_to_system"].get(canonical.lower())
        if system:
            return system.get("brand")

    # Direct system lookup
    system = kb["canonical_to_system"].get(model_lower)
    if system:
        return system.get("brand")

    return None


def infer_techniques_from_system(model: str) -> List[str]:
    """Given a model name, return techniques it supports."""
    kb = load_kb()
    model_lower = model.strip().lower()

    # Try alias lookup
    canonical = kb["alias_to_canonical"].get(model_lower)
    if canonical:
        system = kb["canonical_to_system"].get(canonical.lower())
        if system:
            return system.get("techniques", [])

    # Direct lookup
    system = kb["canonical_to_system"].get(model_lower)
    if system:
        return system.get("techniques", [])

    return []


def infer_software_from_brand(brand: str) -> Dict:
    """Given a brand, return {acquisition: [...], analysis: [...]}."""
    kb = load_kb()
    entry = kb["brand_software"].get(brand, {})
    return {
        "acquisition": entry.get("acquisition", []),
        "analysis": entry.get("analysis", []),
    }


def infer_brand_from_software(software: str) -> Optional[str]:
    """Given software like 'ZEN Blue', return 'Zeiss'. Given 'LAS X', return 'Leica'."""
    kb = load_kb()
    software_lower = software.strip().lower()

    for brand, mapping in kb["brand_software"].items():
        all_sw = (
            mapping.get("acquisition", []) +
            mapping.get("legacy_acquisition", []) +
            mapping.get("analysis", [])
        )
        for sw in all_sw:
            if sw.lower() == software_lower:
                return brand

    return None


def get_system_category(model: str) -> Optional[str]:
    """Return category like 'confocal', 'super_resolution', 'light_sheet', etc."""
    kb = load_kb()
    model_lower = model.strip().lower()

    canonical = kb["alias_to_canonical"].get(model_lower)
    if canonical:
        system = kb["canonical_to_system"].get(canonical.lower())
        if system:
            return system.get("category")

    system = kb["canonical_to_system"].get(model_lower)
    if system:
        return system.get("category")

    return None


def get_all_aliases() -> Dict[str, str]:
    """Return the full alias_to_canonical dict (lowercase alias → canonical)."""
    kb = load_kb()
    return kb["alias_to_canonical"]


def get_all_canonical_models() -> List[str]:
    """Return all canonical model names from the KB (e.g. for MASTER_TAG_DICTIONARY)."""
    kb = load_kb()
    models = set()
    for sys in kb["systems"]:
        models.add(sys["model"])
    return sorted(models)


def get_all_brands() -> Set[str]:
    """Return all unique brands from the KB."""
    kb = load_kb()
    return {sys["brand"] for sys in kb["systems"]}


def is_ambiguous(alias: str) -> bool:
    """Check if an alias is ambiguous (common English word)."""
    return _is_ambiguous_alias(alias.strip().lower())


def has_microscopy_context(text: str, pos: int, window: int = 200) -> bool:
    """Check if there is microscopy context within *window* chars of *pos*."""
    start = max(0, pos - window)
    end = min(len(text), pos + window)
    snippet = text[start:end]
    return bool(_MICROSCOPY_CONTEXT_RE.search(snippet))
