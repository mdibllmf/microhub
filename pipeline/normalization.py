"""
Tag normalization for step 3 (clean).

Maps scraper-style tag values to canonical forms expected by
MASTER_TAG_DICTIONARY.json.  Applied in 3_clean.py *before*
validation so the output JSON contains only canonical names.

Two kinds of fix:
  1. Exact renames  — "Alexa 488" → "Alexa Fluor 488"
  2. Regex renames  — "Alexa NNN" → "Alexa Fluor NNN" (catch-all)
"""

import re
from typing import Dict, List

# ======================================================================
# Exact rename maps:  { old_value: new_canonical }
# ======================================================================

FLUOROPHORE_RENAMES: Dict[str, str] = {
    # Alexa shortforms → Alexa Fluor
    "Alexa 350": "Alexa Fluor 350",
    "Alexa 405": "Alexa Fluor 405",
    "Alexa 430": "Alexa Fluor 430",
    "Alexa 488": "Alexa Fluor 488",
    "Alexa 514": "Alexa Fluor 514",
    "Alexa 532": "Alexa Fluor 532",
    "Alexa 546": "Alexa Fluor 546",
    "Alexa 555": "Alexa Fluor 555",
    "Alexa 568": "Alexa Fluor 568",
    "Alexa 594": "Alexa Fluor 594",
    "Alexa 610": "Alexa Fluor 610",
    "Alexa 633": "Alexa Fluor 633",
    "Alexa 647": "Alexa Fluor 647",
    "Alexa 660": "Alexa Fluor 660",
    "Alexa 680": "Alexa Fluor 680",
    "Alexa 700": "Alexa Fluor 700",
    "Alexa 750": "Alexa Fluor 750",
    "Alexa 790": "Alexa Fluor 790",
    # Case mismatches
    "eGFP": "EGFP",
    "dsRed": "DsRed",
    "eCFP": "ECFP",
    "eYFP": "EYFP",
    "eBFP": "EBFP",
    # Name mismatches
    "Cyan": "CFP",
    "mKate": "mKate2",
    "Dendra": "Dendra2",
    "Emerald": "mEmerald",
    "Janelia Fluor 549": "JF549",
    "Janelia Fluor 646": "JF646",
    "Janelia Fluor 585": "JF585",
    "Janelia Fluor 669": "JF669",
}

TECHNIQUE_RENAMES: Dict[str, str] = {
    "Second Harmonic": "SHG",
}

BRAND_RENAMES: Dict[str, str] = {
    "Applied Scientific Instrumentation": "ASI",
    "Prior": "Prior Scientific",
}

SOFTWARE_RENAMES: Dict[str, str] = {
    "segment-anything": "SAM",
    "Chimera": "UCSF Chimera",
    "SVI Huygens": "Huygens",
}

ORGANISM_RENAMES: Dict[str, str] = {
    "Nematode": "C. elegans",
    "Fruit Fly": "Drosophila",
    "Frog": "Xenopus",
}

# Regex-based catch-all for Alexa shortforms the exact map might miss
_ALEXA_RE = re.compile(r"^Alexa\s+(\d{3})$")


# ======================================================================
# Public API
# ======================================================================

def normalize_tags(paper: Dict) -> Dict:
    """Normalize all tag fields in a paper dict, in-place.

    Returns the same dict (mutated).
    """
    _apply(paper, "fluorophores", FLUOROPHORE_RENAMES, _normalize_fluoro)
    _apply(paper, "microscopy_techniques", TECHNIQUE_RENAMES)
    _apply(paper, "microscope_brands", BRAND_RENAMES)
    _apply(paper, "image_analysis_software", SOFTWARE_RENAMES)
    _apply(paper, "organisms", ORGANISM_RENAMES)

    # Structured equipment normalization (objectives, lasers)
    _normalize_objectives(paper)
    _normalize_lasers(paper)

    return paper


# ======================================================================
# Internals
# ======================================================================

# Regex to parse objective canonical strings into components
_OBJECTIVE_PARSE_RE = re.compile(
    r"(?:(\w[\w\s&()]*?)\s+)?"       # optional brand
    r"(?:([\w\s-]+?)\s+)?"           # optional prefix (HC PL APO, etc.)
    r"(\d{1,3})\s*[x×X]"            # magnification
    r"(?:\s*/?\s*(\d+\.?\d*)\s*NA)?" # optional NA
    r"(?:\s+(oil|water|silicone|glycerol|air|dry|multi[- ]?immersion))?",  # optional immersion
    re.IGNORECASE,
)


def _normalize_objectives(paper: Dict) -> None:
    """Group duplicate objectives by matching magnification+NA+immersion.

    Different textual representations of the same objective (e.g.,
    '60x/1.4 NA oil' and 'Nikon 60x/1.4 NA oil') are merged into
    the most specific (branded) canonical form.
    """
    objectives = paper.get("objectives")
    if not objectives or not isinstance(objectives, list):
        return

    # Group by normalized key: (magnification, na, immersion)
    groups: Dict[str, List[Dict]] = {}
    for obj in objectives:
        if isinstance(obj, str):
            obj = {"canonical": obj}
        canonical = obj.get("canonical", "")
        mag = obj.get("magnification", "")
        na = obj.get("na", "")
        immersion = obj.get("immersion", "unknown")

        # Parse from canonical if fields missing
        if not mag and canonical:
            m = re.search(r"(\d{1,3})\s*[x×X]", canonical)
            if m:
                mag = f"{m.group(1)}x"
        if not na and canonical:
            m = re.search(r"(\d+\.?\d*)\s*NA", canonical)
            if m:
                na = m.group(1)

        # Build grouping key
        key = f"{mag}|{na}|{immersion}".lower()
        groups.setdefault(key, []).append(obj)

    # For each group, keep the most specific entry (longest canonical = most detail)
    result = []
    seen_keys = set()
    for key, entries in groups.items():
        if key in seen_keys:
            continue
        seen_keys.add(key)
        # Prefer branded entries, then longest canonical
        best = max(entries, key=lambda e: (
            1 if e.get("brand") else 0,
            len(e.get("canonical", "")),
        ))
        result.append(best)

    paper["objectives"] = result


def _normalize_lasers(paper: Dict) -> None:
    """Group duplicate lasers and remove generic wavelength-only tags.

    - Removes lasers like '488 nm laser' that have no brand/model info.
    - Groups lasers with the same brand+model into a single entry.
    """
    lasers = paper.get("lasers")
    if not lasers or not isinstance(lasers, list):
        return

    # Filter out generic wavelength-only lasers (e.g. "488 nm laser")
    # These are not useful for users searching for specific equipment
    _WL_ONLY_RE = re.compile(r"^\d{3,4}\s*nm\s*laser$", re.I)
    filtered = []
    for laser in lasers:
        if isinstance(laser, str):
            laser = {"canonical": laser}
        canonical = laser.get("canonical", "")
        brand = laser.get("brand", "")
        # Remove generic wavelength-only lasers without brand
        if not brand and _WL_ONLY_RE.match(canonical):
            continue
        filtered.append(laser)

    # Group by brand+model (or brand+canonical if no model)
    groups: Dict[str, List[Dict]] = {}
    for laser in filtered:
        canonical = laser.get("canonical", "")
        brand = laser.get("brand", "")
        model = laser.get("model", "")
        laser_type = laser.get("type", "")
        # Build grouping key
        if brand and model:
            key = f"{brand}|{model}".lower()
        elif brand and laser_type:
            key = f"{brand}|{laser_type}".lower()
        else:
            key = canonical.lower()
        groups.setdefault(key, []).append(laser)

    # For each group, keep the most specific entry
    result = []
    seen_keys = set()
    for key, entries in groups.items():
        if key in seen_keys:
            continue
        seen_keys.add(key)
        best = max(entries, key=lambda e: (
            1 if e.get("brand") else 0,
            1 if e.get("model") else 0,
            len(e.get("canonical", "")),
        ))
        result.append(best)

    paper["lasers"] = result


def _normalize_fluoro(value: str) -> str:
    """Extra normalization for fluorophores beyond exact renames."""
    m = _ALEXA_RE.match(value)
    if m:
        return f"Alexa Fluor {m.group(1)}"
    return value


def _apply(
    paper: Dict,
    field: str,
    rename_map: Dict[str, str],
    extra_fn=None,
) -> None:
    """Apply rename map (and optional extra function) to a list field."""
    values = paper.get(field)
    if not values or not isinstance(values, list):
        return

    seen = set()
    result = []
    for v in values:
        # Exact rename
        canonical = rename_map.get(v, v)
        # Extra per-value normalization
        if extra_fn is not None:
            canonical = extra_fn(canonical)
        # Deduplicate (e.g., both "Alexa 488" and "Alexa Fluor 488" in same list)
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)

    paper[field] = result
