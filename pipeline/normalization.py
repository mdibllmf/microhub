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
    return paper


# ======================================================================
# Internals
# ======================================================================

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
