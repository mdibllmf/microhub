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
    # Bare FP names → canonical prefixed form
    "Cyan": "CFP",
    "Clover": "mClover",
    "Emerald": "mEmerald",
    "Ruby": "mRuby",
    "Turquoise": "mTurquoise",
    "Cerulean": "mCerulean",
    "Scarlet": "mScarlet",
    "Neon Green": "mNeonGreen",
    # Incomplete names → canonical
    "mKate": "mKate2",
    "Dendra": "Dendra2",
    "mEos": "mEos2",
    "Archon": "Archon1",
    # Janelia Fluor long forms → short canonical
    "Janelia Fluor 549": "JF549",
    "Janelia Fluor 585": "JF585",
    "Janelia Fluor 646": "JF646",
    "Janelia Fluor 669": "JF669",
    # GCaMP variants not in master dict → closest canonical
    "GCaMP3": "GCaMP",
    "GCaMP5": "GCaMP",
    "GCaMP5G": "GCaMP",
    "GCaMP2": "GCaMP",
    "jGCaMP7b": "jGCaMP7",
    "jGCaMP7c": "jGCaMP7",
    "jGCaMP8f": "GCaMP8f",
    "jGCaMP8m": "GCaMP8m",
    "jGCaMP8s": "GCaMP8s",
}

TECHNIQUE_RENAMES: Dict[str, str] = {
    # Old acronym-based canonical names → full names
    "STED": "Stimulated Emission Depletion Microscopy",
    "TEM": "Transmission Electron Microscopy",
    "SEM": "Scanning Electron Microscopy",
    "SIM": "Structured Illumination Microscopy",
    "STORM": "Stochastic Optical Reconstruction Microscopy",
    "dSTORM": "Direct Stochastic Optical Reconstruction Microscopy",
    "PALM": "Photoactivated Localization Microscopy",
    "SMLM": "Single-Molecule Localization Microscopy",
    "FLIM": "Fluorescence Lifetime Imaging Microscopy",
    "FRAP": "Fluorescence Recovery After Photobleaching",
    "FRET": "Förster Resonance Energy Transfer",
    "FCS": "Fluorescence Correlation Spectroscopy",
    "FCCS": "Fluorescence Cross-Correlation Spectroscopy",
    "CARS": "Coherent Anti-Stokes Raman Scattering",
    "SRS": "Stimulated Raman Scattering",
    "SHG": "Second Harmonic Generation",
    "Second Harmonic": "Second Harmonic Generation",
    "AFM": "Atomic Force Microscopy",
    "CLEM": "Correlative Light and Electron Microscopy",
    "OCT": "Optical Coherence Tomography",
    "TIRF": "Total Internal Reflection Fluorescence Microscopy",
    "FIB-SEM": "Focused Ion Beam Scanning Electron Microscopy",
    "FLIP": "Fluorescence Loss in Photobleaching",
    "Serial Block-Face SEM": "Serial Block-Face Scanning Electron Microscopy",
    "DIC": "Differential Interference Contrast Microscopy",
    "Cryo-EM": "Cryo-Electron Microscopy",
    "Cryo-ET": "Cryo-Electron Tomography",
    "Immuno-EM": "Immuno-Electron Microscopy",
    "Negative Stain EM": "Negative Stain Electron Microscopy",
    "Volume EM": "Volume Electron Microscopy",
    "DNA-PAINT": "DNA Points Accumulation for Imaging in Nanoscale Topography",
    "MINFLUX": "Minimal Photon Fluxes Microscopy",
    "RESOLFT": "Reversible Saturable Optical Fluorescence Transitions Microscopy",
    "SOFI": "Super-Resolution Optical Fluctuation Imaging",
    "Confocal": "Confocal Laser Scanning Microscopy",
    "Light Sheet": "Light Sheet Fluorescence Microscopy",
    "Lattice Light Sheet": "Lattice Light Sheet Microscopy",
    "Spinning Disk": "Spinning Disk Confocal Microscopy",
    "Widefield": "Widefield Fluorescence Microscopy",
    "Epifluorescence": "Epifluorescence Microscopy",
    "Brightfield": "Brightfield Microscopy",
    "Darkfield": "Darkfield Microscopy",
    "Phase Contrast": "Phase Contrast Microscopy",
    "Polarization": "Polarization Microscopy",
    "Holographic": "Holographic Microscopy",
    "Photoacoustic": "Photoacoustic Microscopy",
    "Raman": "Raman Microscopy",
    "Intravital": "Intravital Microscopy",
    "Two-Photon": "Two-Photon Excitation Microscopy",
    "Multiphoton": "Multiphoton Microscopy",
    "Three-Photon": "Three-Photon Microscopy",
    "Super-Resolution": "Super-Resolution Microscopy",
    "Airyscan": "Airyscan Microscopy",
    "MesoSPIM": "MesoSPIM Light Sheet Microscopy",
    "Single Molecule": "Single-Molecule Imaging",
    "Single Particle": "Single-Particle Analysis",
    "Z-Stack": "Z-Stack Imaging",
    "Deconvolution": "Deconvolution Microscopy",
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

# ======================================================================
# Organism grouping map
# ======================================================================
# Maps all variant forms (common names, abbreviations, old canonical forms)
# to the full scientific (Latin binomial) name.  Both the organism_agent
# and the scraper may produce any of these — this map collapses them.

ORGANISM_RENAMES: Dict[str, str] = {
    # Common names → scientific name
    "Mouse": "Mus musculus",
    "Mice": "Mus musculus",
    "Murine": "Mus musculus",
    "Human": "Homo sapiens",
    "Patient": "Homo sapiens",
    "Rat": "Rattus norvegicus",
    "Rats": "Rattus norvegicus",
    "Zebrafish": "Danio rerio",
    "Drosophila": "Drosophila melanogaster",
    "Fruit Fly": "Drosophila melanogaster",
    "Fruit flies": "Drosophila melanogaster",
    "C. elegans": "Caenorhabditis elegans",
    "Nematode": "Caenorhabditis elegans",
    "Worm": "Caenorhabditis elegans",
    "Xenopus": "Xenopus laevis",
    "Frog": "Xenopus laevis",
    "Chicken": "Gallus gallus",
    "Chick": "Gallus gallus",
    "Pig": "Sus scrofa",
    "Porcine": "Sus scrofa",
    "Dog": "Canis lupus familiaris",
    "Canine": "Canis lupus familiaris",
    "Monkey": "Macaca mulatta",
    "Primate": "Macaca mulatta",
    "Macaque": "Macaca mulatta",
    "Rabbit": "Oryctolagus cuniculus",
    "Yeast": "Saccharomyces cerevisiae",
    "E. coli": "Escherichia coli",
    "Arabidopsis": "Arabidopsis thaliana",
    "Tobacco": "Nicotiana tabacum",
    "Maize": "Zea mays",
    "Corn": "Zea mays",
    "Rice": "Oryza sativa",
    # Abbreviated forms → scientific name
    "D. melanogaster": "Drosophila melanogaster",
    "D. rerio": "Danio rerio",
    "M. musculus": "Mus musculus",
    "H. sapiens": "Homo sapiens",
    "R. norvegicus": "Rattus norvegicus",
    "X. laevis": "Xenopus laevis",
    "X. tropicalis": "Xenopus tropicalis",
    "A. thaliana": "Arabidopsis thaliana",
    "S. cerevisiae": "Saccharomyces cerevisiae",
    "S. pombe": "Schizosaccharomyces pombe",
    "G. gallus": "Gallus gallus",
    "S. scrofa": "Sus scrofa",
    "C. familiaris": "Canis lupus familiaris",
    "M. mulatta": "Macaca mulatta",
    "M. fascicularis": "Macaca fascicularis",
    "O. cuniculus": "Oryctolagus cuniculus",
    "N. tabacum": "Nicotiana tabacum",
    "N. benthamiana": "Nicotiana benthamiana",
    "Z. mays": "Zea mays",
    "O. sativa": "Oryza sativa",
    # Full Latin names that need species-level normalization
    "Canis familiaris": "Canis lupus familiaris",
    "Callithrix jacchus": "Callithrix jacchus",
}

# ======================================================================
# Cell line rename map (old acronym-based → full names)
# ======================================================================

CELL_LINE_RENAMES: Dict[str, str] = {
    "HeLa": "HeLa (Henrietta Lacks)",
    "HEK293": "Human Embryonic Kidney 293",
    "HEK293T": "Human Embryonic Kidney 293T",
    "U2OS": "Human Osteosarcoma U2OS",
    "COS-7": "African Green Monkey Kidney COS-7",
    "A549": "Human Lung Adenocarcinoma A549",
    "MCF7": "Human Breast Adenocarcinoma MCF-7",
    "MCF-7": "Human Breast Adenocarcinoma MCF-7",
    "NIH 3T3": "NIH 3T3 Mouse Fibroblast",
    "CHO": "Chinese Hamster Ovary",
    "MDCK": "Madin-Darby Canine Kidney",
    "Vero": "Vero (African Green Monkey Kidney)",
    "SH-SY5Y": "Human Neuroblastoma SH-SY5Y",
    "PC12": "Rat Pheochromocytoma PC-12",
    "PC-12": "Rat Pheochromocytoma PC-12",
    "MEF": "Mouse Embryonic Fibroblast",
    "iPSC": "Induced Pluripotent Stem Cell",
    "ESC": "Embryonic Stem Cell",
}

# Tags that are NOT valid organisms and should be removed entirely
_INVALID_ORGANISMS = {
    "Organoid", "organoid",
    "Spheroid", "spheroid",
    "Plant", "plant",
    "Plant cell", "plant cell",
    "Plant tissue", "plant tissue",
    "Bacteria", "bacteria",
    "Bacterial", "bacterial",
    # Taxonomic classifications that slip in from PubTator
    "Bacteria Latreille et al. 1825",
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
    _apply(paper, "cell_lines", CELL_LINE_RENAMES)

    # Remove invalid organism tags and deduplicate after renames
    _clean_organisms(paper)

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


def _clean_organisms(paper: Dict) -> None:
    """Remove invalid organism tags and deduplicate after rename grouping."""
    organisms = paper.get("organisms")
    if not organisms or not isinstance(organisms, list):
        return

    seen = set()
    result = []
    for org in organisms:
        # Remove invalid/non-organism entries
        if org in _INVALID_ORGANISMS:
            continue
        # Case-insensitive dedup (after renaming, "Mouse" and "mouse" → same)
        key = org.lower()
        if key not in seen:
            seen.add(key)
            result.append(org)

    paper["organisms"] = result


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
    """Aggressively filter and group laser tags.

    Only brand-specific laser SYSTEM MODELS are kept (e.g. "Coherent
    Chameleon", "Spectra-Physics Mai Tai", "Toptica iBeam", "NKT SuperK").

    Removes:
    - Generic laser types (two-photon, multiphoton, pulsed, CW, diode, etc.)
    - Wavelength-only lasers ("488 nm laser") even with brand prefix
    - Brand-only lasers ("Coherent laser") without specific model
    """
    lasers = paper.get("lasers")
    if not lasers or not isinstance(lasers, list):
        return

    # Patterns for tags that should be REMOVED
    _WL_LASER_RE = re.compile(r"^\d{3,4}\s*nm\s*(?:laser)?$", re.I)
    _BRAND_WL_RE = re.compile(r"^[\w\s&()-]+\s+\d{3,4}\s*nm\s*(?:laser)?$", re.I)
    _GENERIC_TYPE_RE = re.compile(
        r"^(?:[\w\s&()-]+\s+)?"
        r"(?:two[- ]?photon|multiphoton|femtosecond|picosecond|pulsed|CW|"
        r"diode|DPSS|Ti[:-]?Sapph(?:ire)?|argon|krypton|HeNe|He-Ne|"
        r"solid[- ]?state|gas|fiber|supercontinuum)"
        r"(?:\s*laser)?$",
        re.I,
    )
    # Standalone single-word generic terms (catch bare "gas", "diode", etc.)
    _BARE_GENERIC_RE = re.compile(
        r"^(?:gas|diode|DPSS|fiber|argon|krypton|pulsed|CW|laser|"
        r"solid[- ]?state|supercontinuum|femtosecond|picosecond)$",
        re.I,
    )
    # Brand-only entries without a specific model name (e.g., "Coherent laser")
    _BRAND_ONLY_RE = re.compile(
        r"^(?:Coherent|Spectra[- ]?Physics|Toptica|Cobolt|Oxxius|NKT|"
        r"Melles\s+Griot|MPB|Luigs)\s*(?:laser|Photonics)?$",
        re.I,
    )

    filtered = []
    for laser in lasers:
        if isinstance(laser, str):
            laser = {"canonical": laser}
        canonical = laser.get("canonical", "").strip()

        # Skip empty
        if not canonical:
            continue
        # Remove generic wavelength-only lasers (with or without brand)
        if _WL_LASER_RE.match(canonical) or _BRAND_WL_RE.match(canonical):
            continue
        # Remove generic laser type tags
        if _GENERIC_TYPE_RE.match(canonical):
            continue
        # Remove bare generic terms ("gas", "diode", etc.)
        if _BARE_GENERIC_RE.match(canonical):
            continue
        # Remove brand-only entries without a model
        if _BRAND_ONLY_RE.match(canonical):
            continue
        # Remove if canonical equals the laser type metadata (e.g., canonical="gas")
        laser_type = laser.get("type", "")
        if laser_type and canonical.lower().strip() == laser_type.lower().strip():
            continue
        # Remove very short canonicals (likely junk)
        if len(canonical.strip()) < 4:
            continue
        filtered.append(laser)

    # Group remaining lasers by brand+canonical (dedup same model)
    groups: Dict[str, List[Dict]] = {}
    for laser in filtered:
        canonical = laser.get("canonical", "")
        key = canonical.lower().strip()
        groups.setdefault(key, []).append(laser)

    # For each group, keep the most specific entry
    result = []
    for key, entries in groups.items():
        best = max(entries, key=lambda e: (
            1 if e.get("brand") else 0,
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

    # Build case-insensitive lookup for the rename map
    lower_map = {k.lower(): v for k, v in rename_map.items()}

    seen = set()
    result = []
    for v in values:
        # Try exact rename first, then case-insensitive
        canonical = rename_map.get(v)
        if canonical is None:
            canonical = lower_map.get(v.lower(), v)
        # Extra per-value normalization
        if extra_fn is not None:
            canonical = extra_fn(canonical)
        # Deduplicate (e.g., both "Alexa 488" and "Alexa Fluor 488" in same list)
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)

    paper[field] = result
