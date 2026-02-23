"""
Equipment extraction agent -- microscope brands, models, and related hardware.

Uses a hybrid regex + dictionary + knowledge base approach since no pre-trained
NER model exists for laboratory equipment.  Pattern matching follows the
convention of manufacturer name followed by alphanumeric model identifier.

The Microscope Knowledge Base (microscopy_kb/) provides 65+ systems with
518+ aliases, enabling alias-based model detection and brand↔model inference.

Also detects reagent suppliers (separated from microscope brands in v5.2).

All equipment extractions (lasers, objectives, detectors, filters) include
brand/vendor metadata for specificity.
"""

import re
from typing import Dict, List, Optional, Set

from .base_agent import BaseAgent, Extraction
from ..confidence import get_confidence
from ..kb_loader import (
    load_kb, resolve_alias, infer_brand_from_model,
    get_all_aliases, is_ambiguous, has_microscopy_context,
    get_system_category,
)

# ======================================================================
# Microscope brand dictionary -- canonical names
# ======================================================================

MICROSCOPE_BRANDS: Dict[str, str] = {
    # Key = lowercase pattern, Value = canonical display name
    "zeiss": "Zeiss",
    "carl zeiss": "Zeiss",
    "leica": "Leica",
    "leica microsystems": "Leica",
    "nikon": "Nikon",
    "nikon instruments": "Nikon",
    "olympus": "Olympus",
    "evident": "Evident (Olympus)",
    "evident (olympus)": "Evident (Olympus)",
    "evident olympus": "Evident (Olympus)",
    "andor": "Andor",
    "andor technology": "Andor",
    "yokogawa": "Yokogawa",
    "perkinelmer": "PerkinElmer",
    "perkin elmer": "PerkinElmer",
    "hamamatsu": "Hamamatsu",
    "hamamatsu photonics": "Hamamatsu",
    "jeol": "JEOL",
    "fei": "FEI",
    "bruker": "Bruker",
    "coherent": "Coherent",
    "thorlabs": "Thorlabs",
    "sutter": "Sutter",
    "sutter instrument": "Sutter",
    "prior scientific": "Prior Scientific",
    "prior": "Prior Scientific",
    "asi": "ASI",
    "applied scientific instrumentation": "ASI",
    "photometrics": "Photometrics",
    "pco": "PCO",
    "abberior": "Abberior",
    "3i": "3i (Intelligent Imaging)",
    "intelligent imaging": "3i (Intelligent Imaging)",
    "intelligent imaging innovations": "3i (Intelligent Imaging)",
    "3i intelligent imaging": "3i (Intelligent Imaging)",
    "3i (intelligent imaging)": "3i (Intelligent Imaging)",
    "lavision biotec": "LaVision BioTec",
    "lavision": "LaVision BioTec",
    "luxendo": "Luxendo",
    "visitech": "Visitech",
    "becker & hickl": "Becker & Hickl",
    "becker and hickl": "Becker & Hickl",
    "picoquant": "PicoQuant",
    "chroma": "Chroma",
    "semrock": "Semrock",
    "spectra-physics": "Spectra-Physics",
    "spectra physics": "Spectra-Physics",
    "newport": "Newport",
    "edmund optics": "Edmund Optics",
    "qimaging": "QImaging",
    "roper": "Roper",
    "princeton instruments": "Princeton Instruments",
    "photron": "Photron",
    "till photonics": "Till Photonics",
    "miltenyi": "Miltenyi",
    "olympus life science": "Olympus",
    "motic": "Motic",
    "leica biosystems": "Leica",
    "toptica": "Toptica",
    "cobolt": "Cobolt",
    "melles griot": "Melles Griot",
    "oxxius": "Oxxius",
    "mpb communications": "MPB Communications",
    "luigs & neumann": "Luigs & Neumann",
    "luigs and neumann": "Luigs & Neumann",
    # KB v2 additions
    "revvity": "Revvity",
    "thermo fisher": "Thermo Fisher",
    "thermo fisher scientific": "Thermo Fisher",
    "gatan": "Gatan",
    "lifecanvas": "LifeCanvas",
    "life canvas": "LifeCanvas",
    "femtonics": "Femtonics",
    "scientifica": "Scientifica",
    "keyence": "Keyence",
    "3dhistech": "3DHISTECH",
    "oxford nanoimaging": "ONI",
    "nkt photonics": "NKT Photonics",
    "nkt": "NKT Photonics",
    "miltenyi biotec": "Miltenyi Biotec",
    "crestoptics": "CrestOptics",
    "lumencor": "Lumencor",
    "coolled": "CoolLED",
    "molecular devices": "Molecular Devices",
}

# ======================================================================
# Additional Prior Scientific variant patterns (avoid bare "prior")
# ======================================================================
_PRIOR_PATTERNS = [
    re.compile(r"\bPrior\s+Scientific\b", re.I),
    re.compile(r"\bPrior\s+NanoDrive\b", re.I),
    re.compile(r"\bPrior\s+OptiScan\b", re.I),
    re.compile(r"\bPrior\s+(?:motorized\s+)?stage\b", re.I),
    re.compile(r"\bPrior\s+(?:focus|controller)\b", re.I),
    re.compile(r"\bPrior\s+instruments?\b", re.I),
    re.compile(r"\bPrior\s+ProScan\b", re.I),
]

# Short acronyms that MUST NOT be searched directly — they cause false
# positives.  These are matched ONLY via their full expansion or via
# context patterns in _BRAND_CONTEXT_PATTERNS.  The acronym is still the
# canonical display name.
_ACRONYM_ONLY_BRANDS: Set[str] = {
    "asi", "pco", "fei", "3i", "jeol", "oni", "nkt",
}

# Additional patterns that need context to avoid false positives
_BRAND_CONTEXT_PATTERNS = [
    # "ASI" needs microscopy context
    (re.compile(r"\bASI\s+(?:stage|controller|MS-?\d|Tiger)", re.I), "ASI"),
    # "3i" needs context
    (re.compile(r"\b3i\s+(?:Marianas|SlideBook|spinning)", re.I), "3i (Intelligent Imaging)"),
    # "PCO" needs context (common abbreviation)
    (re.compile(r"\bpco\s*\.?\s*(?:edge|panda|dimax|pixelfly|flim|camera)", re.I), "PCO"),
    # "FEI" needs context (electron microscope brand, now owned by Thermo Fisher)
    (re.compile(r"\bFEI\s+(?:Tecnai|Talos|Titan|Helios|Magellan|Quanta|Scios|Verios)", re.I), "FEI"),
    # "JEOL" needs context
    (re.compile(r"\bJEOL\s+(?:JEM|JSM|ARM|JBIC|\d{3,4})", re.I), "JEOL"),
    # "ONI" needs context (Oxford Nanoimaging)
    (re.compile(r"\bONI\s+(?:Nanoimager|EV|microscop)", re.I), "ONI"),
    (re.compile(r"\bOxford\s+Nanoimaging\b", re.I), "ONI"),
    # "NKT" needs context
    (re.compile(r"\bNKT\s+(?:Photonics|SuperK|laser)", re.I), "NKT Photonics"),
]

# ======================================================================
# Microscope model patterns
# ======================================================================

MODEL_PATTERNS: List[tuple] = [
    # Zeiss models
    (re.compile(r"\bLSM\s*(\d{3})\b"), lambda m: f"LSM {m.group(1)}", "Zeiss"),
    (re.compile(r"\bElyra(?:\s+7)?\b"), lambda m: m.group(0).strip(), "Zeiss"),
    (re.compile(r"\bLightsheet\s+(?:Z\.?1|7)\b", re.I), lambda m: m.group(0).strip(), "Zeiss"),
    (re.compile(r"\bCelldiscoverer\s+7\b", re.I), lambda m: "Celldiscoverer 7", "Zeiss"),
    (re.compile(r"\bAxio\s*(?:Observer|Imager|vert|skop)\b", re.I), lambda m: m.group(0).strip(), "Zeiss"),
    (re.compile(r"\bObserver\s+7\b"), lambda m: "Observer 7", "Zeiss"),

    # Leica models
    (re.compile(r"\bSP[58]\b"), lambda m: m.group(0), "Leica"),
    (re.compile(r"\bStellaris\b", re.I), lambda m: "Stellaris", "Leica"),
    (re.compile(r"\bSTED\s+3X\b", re.I), lambda m: "STED 3X", "Leica"),
    (re.compile(r"\bTHUNDER\b"), lambda m: "THUNDER", "Leica"),
    (re.compile(r"\bDMi8\b"), lambda m: "DMi8", "Leica"),
    (re.compile(r"\bDM[6IL]\b"), lambda m: m.group(0), "Leica"),
    (re.compile(r"\bTCS\s+SP\d\b", re.I), lambda m: m.group(0).strip(), "Leica"),

    # Nikon models
    (re.compile(r"\bA1R?\+?\b(?=.*(?:confocal|microscop|nikon))", re.I), lambda m: m.group(0), "Nikon"),
    (re.compile(r"\bAX\s*R?\b(?=.*nikon)", re.I), lambda m: "AX", "Nikon"),
    (re.compile(r"\bTi2?\b(?=.*nikon)", re.I), lambda m: m.group(0), "Nikon"),
    (re.compile(r"\bN-SIM\b"), lambda m: "N-SIM", "Nikon"),
    (re.compile(r"\bN-STORM\b"), lambda m: "N-STORM", "Nikon"),

    # Yokogawa spinning disk units
    (re.compile(r"\bCSU-?(?:W1|X1)\b", re.I), lambda m: m.group(0).upper().replace(" ", "-"), "Yokogawa"),

    # Olympus models
    (re.compile(r"\bFV(\d{4})\b"), lambda m: f"FV{m.group(1)}", "Olympus"),
    (re.compile(r"\bSpinSR\b", re.I), lambda m: "SpinSR", "Olympus"),
    (re.compile(r"\bIX[78]3\b"), lambda m: m.group(0), "Olympus"),
    (re.compile(r"\bBX63\b"), lambda m: "BX63", "Olympus"),
    (re.compile(r"\bVS120\b"), lambda m: "VS120", "Olympus"),

    # Electron microscope models (FEI brand, now owned by Thermo Fisher)
    (re.compile(r"\bTitan\s*(?:Krios)?\b", re.I), lambda m: "Titan", "FEI"),
    (re.compile(r"\bGlacios\b", re.I), lambda m: "Glacios", "FEI"),
    (re.compile(r"\bTalos\b", re.I), lambda m: "Talos", "FEI"),
    (re.compile(r"\bTecnai\b", re.I), lambda m: "Tecnai", "FEI"),
    (re.compile(r"\bCM200\b"), lambda m: "CM200", "FEI"),
    (re.compile(r"\bJEM-?(?:1400|2100)\b"), lambda m: m.group(0), "JEOL"),

    # SPIM systems (these are specific microscope systems)
    (re.compile(r"\bMesoSPIM\b", re.I), lambda m: "MesoSPIM", None),
    (re.compile(r"\bdiSPIM\b", re.I), lambda m: "diSPIM", None),
    (re.compile(r"\biSPIM\b"), lambda m: "iSPIM", None),
    (re.compile(r"\bOpenSPIM\b", re.I), lambda m: "OpenSPIM", None),
    (re.compile(r"\bUltraMicroscope\b", re.I), lambda m: "UltraMicroscope", None),
    (re.compile(r"\bSmartSPIM\b", re.I), lambda m: "SmartSPIM", None),
    (re.compile(r"\bMuVi\s+SPIM\b", re.I), lambda m: "MuVi SPIM", "Luxendo"),
    (re.compile(r"\bctASLM\b", re.I), lambda m: "ctASLM", None),
    (re.compile(r"\bCLARITY\s+SPIM\b", re.I), lambda m: "CLARITY SPIM", None),
    (re.compile(r"\bASOM\b", re.I), lambda m: "ASOM", "ASI"),
    (re.compile(r"\bTCS\s+SP8\s+DLS\b", re.I), lambda m: "TCS SP8 DLS", "Leica"),
    (re.compile(r"\b3i\s+Lattice\s+Light\s+Sheet\b", re.I), lambda m: "3i Lattice Light Sheet", "3i (Intelligent Imaging)"),

    # Zeiss light sheet specific patterns
    (re.compile(r"\bZeiss\s+Lightsheet\b", re.I), lambda m: "Zeiss Lightsheet", "Zeiss"),
    (re.compile(r"\bZ\.?1\b(?=.{0,30}(?:light|zeiss|sheet))", re.I), lambda m: "Z.1", "Zeiss"),

    # ---- KB v2: new Zeiss models ----
    (re.compile(r"\bLattice\s+(?:Light\s*[Ss]heet|SIM)\s+[357]\b", re.I), lambda m: m.group(0).strip(), "Zeiss"),
    (re.compile(r"\bAxioscan\s+7\b", re.I), lambda m: "Axioscan 7", "Zeiss"),
    (re.compile(r"\bCrossbeam\s+\d+\b", re.I), lambda m: m.group(0).strip(), "Zeiss"),
    (re.compile(r"\bGeminiSEM\s+\d+\b", re.I), lambda m: m.group(0).strip(), "Zeiss"),
    (re.compile(r"\bXradia\s+(?:Versa|Ultra)\b", re.I), lambda m: m.group(0).strip(), "Zeiss"),

    # ---- KB v2: new Leica models ----
    (re.compile(r"\bSTELLARIS\s+[58]\b", re.I), lambda m: m.group(0).strip(), "Leica"),
    (re.compile(r"\bSTELLARIS\s+8\s+(?:FALCON|DIVE|STED)\b", re.I), lambda m: m.group(0).strip(), "Leica"),
    (re.compile(r"\bFALCON\b(?=.{0,50}(?:Leica|STELLARIS|FLIM|lifetime))", re.I), lambda m: "FALCON", "Leica"),
    (re.compile(r"\bTauSTED\b", re.I), lambda m: "TauSTED", "Leica"),
    (re.compile(r"\bMica\b(?=.{0,50}(?:Leica|microscop|imaging))", re.I), lambda m: "Mica", "Leica"),
    (re.compile(r"\bAperio\s+(?:GT|AT|CS|VERSA|LV)\s*\d*\b", re.I), lambda m: m.group(0).strip(), "Leica"),

    # ---- KB v2: new Nikon models ----
    (re.compile(r"\bAX\s*R?\s*(?:MP)?\b(?=.{0,30}(?:Nikon|confocal|NSPARC))", re.I), lambda m: "AX R", "Nikon"),
    (re.compile(r"\bNSPARC\b", re.I), lambda m: "NSPARC", "Nikon"),
    (re.compile(r"\bDUX-?(?:VB|ST)\b", re.I), lambda m: m.group(0).upper(), "Nikon"),
    (re.compile(r"\bC2\+?\b(?=.{0,30}(?:Nikon|confocal))", re.I), lambda m: "C2+", "Nikon"),

    # ---- KB v2: new Evident/Olympus models ----
    (re.compile(r"\bFV[45]000\b"), lambda m: m.group(0), "Evident (Olympus)"),
    (re.compile(r"\bIX85\b"), lambda m: "IX85", "Evident (Olympus)"),
    (re.compile(r"\bSpinSR\b(?=.{0,30}(?:IX85|spinning|SoRa))", re.I), lambda m: "SpinSR", "Evident (Olympus)"),
    (re.compile(r"\bSpinXL\b", re.I), lambda m: "SpinXL", "Evident (Olympus)"),
    (re.compile(r"\bSilVIR\b", re.I), lambda m: "SilVIR", "Evident (Olympus)"),
    (re.compile(r"\bVS200\b"), lambda m: "VS200", "Evident (Olympus)"),
    (re.compile(r"\bAPX100\b"), lambda m: "APX100", "Evident (Olympus)"),

    # ---- KB v2: new Andor models ----
    (re.compile(r"\bDragonfly\s*(?:200|400|500|505|600)\b", re.I), lambda m: m.group(0).strip(), "Andor"),
    (re.compile(r"\bBC43\b(?=.{0,30}(?:Andor|confocal|benchtop))", re.I), lambda m: "BC43", "Andor"),

    # ---- KB v2: new spinning disk models ----
    (re.compile(r"\bCSU-?W1\s+SoRa\b", re.I), lambda m: "CSU-W1 SoRa", "Yokogawa"),
    (re.compile(r"\bSoRa\b(?=.{0,30}(?:Yokogawa|CSU|spinning|disk))", re.I), lambda m: "SoRa", "Yokogawa"),
    (re.compile(r"\bCV[78]000\b"), lambda m: m.group(0), "Yokogawa"),
    (re.compile(r"\bCQ1\b(?=.{0,30}(?:Yokogawa|CellVoyager))", re.I), lambda m: "CQ1", "Yokogawa"),

    # ---- KB v2: HCS patterns ----
    (re.compile(r"\bOpera\s+Phenix(?:\s+Plus)?\b", re.I), lambda m: m.group(0).strip(), "Revvity"),
    (re.compile(r"\bOperetta\s+CLS\b", re.I), lambda m: "Operetta CLS", "Revvity"),
    (re.compile(r"\bImageXpress\s+(?:Micro|Pico|Confocal)\b", re.I), lambda m: m.group(0).strip(), "Molecular Devices"),
    (re.compile(r"\bCellInsight\s+CX7\b", re.I), lambda m: "CellInsight CX7", "Thermo Fisher"),

    # ---- KB v2: multiphoton models ----
    (re.compile(r"\bUltima\s+(?:Investigator|2Pplus)\b", re.I), lambda m: m.group(0).strip(), "Bruker"),
    (re.compile(r"\bBergamo\s*(?:II)?\b(?=.{0,30}(?:Thorlabs|multiphoton|two.?photon))", re.I), lambda m: "Bergamo", "Thorlabs"),
    (re.compile(r"\bHyperScope\b(?=.{0,30}(?:Scientifica|multiphoton))", re.I), lambda m: "HyperScope", "Scientifica"),
    (re.compile(r"\bFEMTO3D\b", re.I), lambda m: "FEMTO3D", "Femtonics"),
    (re.compile(r"\bTriM\s*Scope\b", re.I), lambda m: "TriM Scope", "LaVision BioTec"),

    # ---- KB v2: STED models ----
    (re.compile(r"\bSTEDYCON\b", re.I), lambda m: "STEDYCON", "Abberior"),
    (re.compile(r"\bFacility\s+Line\b(?=.{0,30}(?:Abberior|STED))", re.I), lambda m: "Facility Line", "Abberior"),

    # ---- KB v2: EM models ----
    (re.compile(r"\bKrios\s*(?:G[34]i?)?\b", re.I), lambda m: "Titan Krios", "Thermo Fisher"),
    (re.compile(r"\bGlacios\s*2?\b", re.I), lambda m: "Glacios", "Thermo Fisher"),
    (re.compile(r"\bAquilos\s*2?\b", re.I), lambda m: "Aquilos", "Thermo Fisher"),
    (re.compile(r"\bScios\s*2?\b", re.I), lambda m: "Scios", "Thermo Fisher"),
    (re.compile(r"\bHelios\s*(?:5|G4|NanoLab)?\b", re.I), lambda m: m.group(0).strip(), "Thermo Fisher"),
    (re.compile(r"\bApreo\s*2?\b", re.I), lambda m: "Apreo", "Thermo Fisher"),
    (re.compile(r"\bCRYO\s*ARM\b", re.I), lambda m: "CRYO ARM 300", "JEOL"),
    (re.compile(r"\bJEM-?F200\b"), lambda m: "JEM-F200", "JEOL"),

    # ---- KB v2: slide scanner models ----
    (re.compile(r"\bNanoZoomer\s*(?:S\d+|2\.0.HT|XR)?\b", re.I), lambda m: m.group(0).strip(), "Hamamatsu"),
    (re.compile(r"\bPannoramic\s*(?:SCAN|MIDI|250|DESK)?\b", re.I), lambda m: m.group(0).strip(), "3DHISTECH"),
]

# ======================================================================
# Reagent suppliers (separated from microscope brands in v5.2)
# ======================================================================

REAGENT_SUPPLIERS: Dict[str, str] = {
    "invitrogen": "Invitrogen",
    "thermo fisher scientific": "Thermo Fisher Scientific",
    "thermofisher": "Thermo Fisher Scientific",
    "sigma-aldrich": "Sigma-Aldrich",
    "sigma aldrich": "Sigma-Aldrich",
    "sigma": "Sigma-Aldrich",
    "merck": "Merck",
    "emd millipore": "Merck",
    "abcam": "Abcam",
    "cell signaling": "Cell Signaling Technology",
    "cell signaling technology": "Cell Signaling Technology",
    "cst": "Cell Signaling Technology",
    "bio-rad": "Bio-Rad",
    "biorad": "Bio-Rad",
    "bio rad": "Bio-Rad",
    "jackson immunoresearch": "Jackson ImmunoResearch",
    "life technologies": "Life Technologies",
    "molecular probes": "Thermo Fisher Scientific",
    "santa cruz": "Santa Cruz Biotechnology",
    "santa cruz biotechnology": "Santa Cruz Biotechnology",
    "bd biosciences": "BD Biosciences",
    "becton dickinson": "BD Biosciences",
    "millipore": "Millipore",
    "corning": "Corning",
    "ibidi": "ibidi",
    "mattek": "MatTek",
    "lonza": "Lonza",
    "gibco": "Gibco",
    "promega": "Promega",
    "new england biolabs": "New England Biolabs",
    "neb": "New England Biolabs",
    "takara": "Takara Bio",
    "takara bio": "Takara Bio",
    "clontech": "Takara Bio",
    "roche": "Roche",
    "dako": "Dako",
    "agilent": "Agilent",
    "vector laboratories": "Vector Laboratories",
    "biotium": "Biotium",
    "tocris": "Tocris",
    "addgene": "Addgene",
    "enzo life sciences": "Enzo Life Sciences",
    "qiagen": "Qiagen",
    "r&d systems": "R&D Systems",
    "biolegend": "BioLegend",
    "visiopharm": "Visiopharm",
    "definiens": "Definiens",
    "cytiva": "Cytiva",
    "ge healthcare life sciences": "Cytiva",
    "genetex": "GeneTex",
    "novus biologicals": "Novus Biologicals", "novus": "Novus Biologicals",
    "vwr": "VWR", "vwr international": "VWR",
    "ebioscience": "eBioscience",
}

# Context patterns for reagent suppliers (e.g. "Sigma-Aldrich, St. Louis")
_REAGENT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in REAGENT_SUPPLIERS) + r")\b",
    re.IGNORECASE,
)


# ======================================================================
# Objective lens patterns — brand-aware
# ======================================================================

# Objective brand prefix mapping (lens naming conventions identify brand)
_OBJECTIVE_BRAND_MAP = {
    "HC PL APO": "Leica",
    "HC PL FLUOTAR": "Leica",
    "HCX PL APO": "Leica",
    "HCX PL FLUOTAR": "Leica",
    "N PLAN": "Leica",
    "CFI Plan Apo": "Nikon",
    "CFI Plan Fluor": "Nikon",
    "CFI S Plan Fluor": "Nikon",
    "CFI Apo": "Nikon",
    "CFI60": "Nikon",
    "Plan-Apochromat": "Zeiss",
    "Plan-Neofluar": "Zeiss",
    "C-Apochromat": "Zeiss",
    "LD C-Apochromat": "Zeiss",
    "EC Plan-Neofluar": "Zeiss",
    "alpha Plan-Apochromat": "Zeiss",
    "Apo TIRF": "Nikon",
    "UPLSAPO": "Olympus",
    "UPLXAPO": "Olympus",
    "UCPLFLN": "Olympus",
    "UPLAPO": "Olympus",
    "UPlanXApo": "Olympus",
    "UPlanSApo": "Olympus",
    "UPlanFL": "Olympus",
}

# Matches "60x/1.4 NA oil", "100x 1.49NA", "40× 0.95 NA", etc.
_OBJECTIVE_FULL_RE = re.compile(
    r"(\d{1,3})\s*[x×X]\s*/?\s*(\d+\.?\d*)\s*(?:NA|N\.A\.)"
    r"(?:\s+(oil|water|silicone|glycerol|air|dry|multi[- ]?immersion))?"
    r"(?:\s+(?:objective|lens))?",
    re.IGNORECASE,
)

# Matches branded objective names like "HC PL APO 63x" or "CFI Plan Apo 60x"
_OBJECTIVE_BRANDED_RE = re.compile(
    r"\b("
    + "|".join(re.escape(k) for k in sorted(_OBJECTIVE_BRAND_MAP, key=len, reverse=True))
    + r")\s+(\d{1,3})\s*[x×X]"
    r"(?:\s*/?\s*(\d+\.?\d*)\s*(?:NA|N\.A\.))?"
    r"(?:\s+(oil|water|silicone|glycerol|air|dry))?"
    r"(?:\s+(?:objective|lens))?",
    re.IGNORECASE,
)

# Matches standalone "Plan Apo 60x" or "Apo TIRF 100x" (may or may not have brand)
_OBJECTIVE_TYPE_RE = re.compile(
    r"(?:Plan[- ]?(?:Apo(?:chromat)?|Fluor|Neofluar)|"
    r"Apo(?:chromat)?[- ]?(?:TIRF|Lambda)?|"
    r"C[- ]?Apo(?:chromat)?|"
    r"HC\s+PL\s+APO|"
    r"CFI\s+Plan\s+(?:Apo|Fluor))\s+"
    r"(\d{1,3})\s*[x×X]",
    re.IGNORECASE,
)

# ======================================================================
# Laser patterns — brand-specific models
# ======================================================================

# Specific laser system models with known brands
_LASER_SYSTEM_PATTERNS = [
    # Coherent laser systems
    (re.compile(r"\bCoherent\s+Chameleon(?:\s+(?:Ultra|Vision|Discovery))?\b", re.I),
     None, "Coherent", "Ti:Sapphire"),
    (re.compile(r"\bChameleon(?:\s+(?:Ultra|Vision|Discovery))?\b", re.I),
     None, "Coherent", "Ti:Sapphire"),
    (re.compile(r"\bCoherent\s+Genesis\b", re.I), None, "Coherent", "CW"),
    (re.compile(r"\bCoherent\s+(?:Sapphire|Obis|OBIS)\s*\w*\b", re.I), None, "Coherent", "diode"),
    (re.compile(r"\bOBIS\s*\d{3}\b", re.I), None, "Coherent", "diode"),
    (re.compile(r"\bCoherent\s+Verdi\b", re.I), None, "Coherent", "DPSS"),
    (re.compile(r"\bCoherent\s+Innova\b", re.I), None, "Coherent", "gas"),

    # Spectra-Physics laser systems
    (re.compile(r"\bSpectra[- ]?Physics\s+Mai\s*Tai\b", re.I), None, "Spectra-Physics", "Ti:Sapphire"),
    (re.compile(r"\bMai\s*Tai(?:\s+(?:HP|DeepSee|eHP))?\b", re.I), None, "Spectra-Physics", "Ti:Sapphire"),
    (re.compile(r"\bSpectra[- ]?Physics\s+Tsunami\b", re.I), None, "Spectra-Physics", "Ti:Sapphire"),
    (re.compile(r"\bTsunami\b(?=.{0,50}(?:laser|Spectra|Ti:?Sapph))", re.I),
     None, "Spectra-Physics", "Ti:Sapphire"),
    (re.compile(r"\bSpectra[- ]?Physics\s+InSight\b", re.I), None, "Spectra-Physics", "Ti:Sapphire"),
    (re.compile(r"\bInSight\s+(?:DS\+?|X3|DeepSee)\b", re.I), None, "Spectra-Physics", "Ti:Sapphire"),

    # Toptica laser systems
    (re.compile(r"\bToptica\s+iBeam\s*(?:smart)?\b", re.I), None, "Toptica", "diode"),
    (re.compile(r"\biBeam\s*(?:smart)?\s*\d{3}\b", re.I), None, "Toptica", "diode"),
    (re.compile(r"\bToptica\s+(?:FemtoFiber|iChrome)\b", re.I), None, "Toptica", "fiber"),

    # Cobolt laser systems
    (re.compile(r"\bCobolt\s+(?:Calypso|Jive|Mambo|Samba|Blues|Flamenco|Rumba|Twist|Skyra|Bolero)\b", re.I),
     None, "Cobolt", "DPSS"),

    # Melles Griot / CVI
    (re.compile(r"\bMelles\s+Griot\b", re.I), "Melles Griot", "Melles Griot", "gas"),

    # Oxxius
    (re.compile(r"\bOxxius\s+(?:LBX|LCX|LaserBoxx)\b", re.I), None, "Oxxius", "diode"),

    # NKT / SuperK
    (re.compile(r"\bSuperK\s*(?:Extreme|COMPACT|SELECT)?\b", re.I), None, "NKT Photonics", "supercontinuum"),
    (re.compile(r"\bNKT\s+(?:Photonics\s+)?SuperK\b", re.I), None, "NKT Photonics", "supercontinuum"),

    # MPB Communications
    (re.compile(r"\bMPB\s+(?:Communications\s+)?VFL\b", re.I), None, "MPB Communications", "fiber"),

    # Luigs & Neumann
    (re.compile(r"\bLuigs\s+(?:&|and)\s+Neumann\b", re.I), "Luigs & Neumann", "Luigs & Neumann", None),

    # Generic branded laser mentions — require model name (2+ chars) and
    # exclude generic type words (laser, diode, gas, fiber, DPSS, CW)
    (re.compile(
        r"\b(Coherent|Spectra[- ]?Physics|Toptica|Cobolt|Oxxius)\s+"
        r"(?!(?:laser|diode|gas|fiber|DPSS|CW|pulsed|femtosecond)\b)"
        r"(\w{2,})\s*(?:laser)\b",
        re.I,
    ), None, None, None),  # Brand captured in group 1
]

_LASER_WAVELENGTH_RE = re.compile(
    r"(\d{3,4})\s*[-–]?\s*nm\s*(?:laser|excitation|line|diode|DPSS)?",
    re.IGNORECASE,
)

_LASER_TYPE_RE = re.compile(
    r"\b(argon|krypton|HeNe|He-Ne|diode|DPSS|Ti[:-]?Sapph(?:ire)?|"
    r"femtosecond|picosecond|pulsed|CW|multiphoton|two[- ]?photon)\s*(?:laser)?",
    re.IGNORECASE,
)

# Common laser lines used in microscopy
_COMMON_LASER_LINES = {
    "355", "405", "440", "445", "458", "473", "488", "491", "514", "532",
    "543", "552", "555", "561", "568", "594", "633", "638", "640", "647",
    "660", "685", "730", "750", "780", "800", "850", "900", "920", "940",
    "960", "980", "1040", "1064",
}

# ======================================================================
# Detector patterns — with brand associations
# (pattern, canonical_override, brand)
# ======================================================================

DETECTOR_PATTERNS = [
    # Generic detector types (brand from proximity)
    (re.compile(r"\bPMT\b"), "PMT", None),
    (re.compile(r"\bGaAsP\b", re.I), "GaAsP", None),
    (re.compile(r"\bHyD\b(?:\s*[SX])?", re.I), "HyD", "Leica"),
    (re.compile(r"\bsCMOS\b", re.I), "sCMOS", None),
    (re.compile(r"\bEMCCD\b", re.I), "EMCCD", None),
    (re.compile(r"\bCCD\b(?!\s*camera\s+phone)", re.I), "CCD", None),
    (re.compile(r"\bAPD\b"), "APD", None),
    (re.compile(r"\bSPAD\b"), "SPAD", None),
    (re.compile(r"\bMCP\b(?=.{0,20}(?:detector|channel|plate))", re.I | re.S), "MCP", None),
    # Hamamatsu cameras
    (re.compile(r"\bORCA[- ]?Flash\s*\d[\d.]*\b", re.I), None, "Hamamatsu"),
    (re.compile(r"\bORCA[- ]?Fusion(?:\s+BT)?\b", re.I), None, "Hamamatsu"),
    (re.compile(r"\bORCA[- ]?Quest\b", re.I), None, "Hamamatsu"),
    (re.compile(r"\bORCA[- ]?Spark\b", re.I), None, "Hamamatsu"),
    (re.compile(r"\bORCA[- ]?(?:R2|ER|AG|II)\b", re.I), None, "Hamamatsu"),
    (re.compile(r"\bC\d{4,5}-\d+\b(?=.{0,30}(?:Hamamatsu|camera|detector))", re.I), None, "Hamamatsu"),
    # Andor cameras
    (re.compile(r"\biXon\s*(?:Ultra|Life|EM)?\s*\d*\b", re.I), None, "Andor"),
    (re.compile(r"\bZyla\s*\d[\d.]*\b", re.I), None, "Andor"),
    (re.compile(r"\bSona\s*\d[\d.]*\b", re.I), None, "Andor"),
    (re.compile(r"\bNeo\s+\d\.\d\b", re.I), None, "Andor"),
    (re.compile(r"\bMayana\b", re.I), None, "Andor"),
    (re.compile(r"\bBalor\b", re.I), None, "Andor"),
    # Photometrics cameras
    (re.compile(r"\bKinetix\b", re.I), None, "Photometrics"),
    (re.compile(r"\bPrime\s*(?:BSI|95B)\b", re.I), None, "Photometrics"),
    (re.compile(r"\bCoolSNAP\b", re.I), None, "Photometrics"),
    (re.compile(r"\bEvolve\s*\d*\b", re.I), None, "Photometrics"),
    # PCO cameras
    (re.compile(r"\bpco\.edge\s*\d[\d.]*\b", re.I), None, "PCO"),
    (re.compile(r"\bpco\.panda\b", re.I), None, "PCO"),
    # Teledyne cameras
    (re.compile(r"\bTeledyne\s+(?:Photon|FLIR)\b", re.I), None, "Teledyne"),
    # QImaging cameras
    (re.compile(r"\bRetiga\s*(?:R\d|EXi|SRV)\b", re.I), None, "QImaging"),
    # Leica detectors
    (re.compile(r"\bHyD\s+(?:R|S|X|SMD)\b", re.I), None, "Leica"),
    # Zeiss detectors
    (re.compile(r"\bAiryscan(?:\s+2)?\b", re.I), None, "Zeiss"),
    (re.compile(r"\bBiG(?:\.2)?\b(?=.{0,30}(?:Zeiss|detector|GaAsP))", re.I), None, "Zeiss"),
    # ---- KB v2: new detector patterns ----
    # Leica Power HyD family
    (re.compile(r"\bPower\s+HyD\s+[SRXP]\b", re.I), None, "Leica"),
    # Evident SilVIR detector
    (re.compile(r"\bSilVIR\s+detector\b", re.I), "SilVIR", "Evident (Olympus)"),
    # Nikon NSPARC detector
    (re.compile(r"\bNSPARC\s+detector\b", re.I), "NSPARC", "Nikon"),
    # Nikon DUX detectors
    (re.compile(r"\bDUX-?(?:VB|ST)\s*(?:detector)?\b", re.I), None, "Nikon"),
    # Hamamatsu new cameras
    (re.compile(r"\bORCA[- ]?Fire\b", re.I), None, "Hamamatsu"),
    (re.compile(r"\bORCA[- ]?Lightning\b", re.I), None, "Hamamatsu"),
    (re.compile(r"\bORCA[- ]?Quest\s*2\b", re.I), None, "Hamamatsu"),
    # Gatan direct electron detectors
    (re.compile(r"\bGatan\s+K[23]\b", re.I), None, "Gatan"),
    (re.compile(r"\bK3\s+(?:direct\s+electron|camera|detector)\b", re.I), None, "Gatan"),
    # Falcon direct electron detectors
    (re.compile(r"\bFalcon\s*(?:4i?|III|3)\b", re.I), None, "Thermo Fisher"),
    # Photometrics new cameras
    (re.compile(r"\bKinetix\s*\d*\b(?=.{0,30}(?:Photometrics|camera|sCMOS))", re.I), None, "Photometrics"),
    (re.compile(r"\bPrime\s+BSI\s*(?:Express)?\b", re.I), None, "Photometrics"),
]

# ======================================================================
# Filter patterns — with brand detection
# ======================================================================

_FILTER_RE = re.compile(
    r"\b(\d{3,4})\s*/\s*(\d{1,3})\s*(?:nm)?\s*"
    r"(?:band[- ]?pass|BP|emission|excitation|filter)\b",
    re.IGNORECASE,
)

_DICHROIC_RE = re.compile(
    r"\b(?:dichroic|beam\s*splitter|DM)\s*\d{3,4}(?:/\d{3,4})?\b",
    re.IGNORECASE,
)

# Branded filter patterns — captures brand and specific model
_CHROMA_FILTER_RE = re.compile(
    r"\b(?:Chroma\s+)?(?:ET|AT|HQ|ZET|Z)\s*(\d{3,4})\s*/\s*(\d{1,3})\w?\b",
    re.IGNORECASE,
)

_SEMROCK_FILTER_RE = re.compile(
    r"\b(?:Semrock\s+)?(?:FF|BrightLine|Di)\s*(\d{2,4})\s*[-/]\s*(\w+)\b",
    re.IGNORECASE,
)

# Filter cubes/sets with brand
_FILTER_CUBE_RE = re.compile(
    r"\b(?:(Zeiss|Leica|Nikon|Olympus|Chroma|Semrock)\s+)?"
    r"(?:filter\s+(?:cube|set|block)|cube)\s*#?\s*(\d{1,3})\b",
    re.IGNORECASE,
)

# Zeiss-specific filter sets
_ZEISS_FILTER_RE = re.compile(
    r"\b(?:Zeiss\s+)?Filter\s+Set\s+(\d{1,3})\b",
    re.IGNORECASE,
)


class EquipmentAgent(BaseAgent):
    """Extract microscope brands, models, objectives, lasers, detectors, filters.

    All equipment extractions include brand/vendor metadata when it can be
    determined from the text, naming conventions, or nearby brand mentions.

    The Microscope Knowledge Base provides alias-based model detection
    (catching models the hardcoded regex patterns miss) and brand inference.
    """

    name = "equipment"

    def __init__(self):
        self.kb = load_kb()
        self._kb_alias_re = self._compile_alias_patterns()

    def _compile_alias_patterns(self) -> Optional[re.Pattern]:
        """Build a single compiled regex from all KB aliases for broad model detection.

        Aliases are sorted longest-first to prevent partial matches.
        Short or ambiguous aliases are excluded from the broad regex —
        they are handled separately with context checks.
        """
        all_aliases = get_all_aliases()
        if not all_aliases:
            return None

        # Collect unique aliases, skip short/ambiguous ones
        alias_set: Set[str] = set()
        for alias_lower in all_aliases:
            if len(alias_lower) < 3:
                continue
            if is_ambiguous(alias_lower):
                continue
            alias_set.add(alias_lower)

        if not alias_set:
            return None

        # Sort longest-first
        sorted_aliases = sorted(alias_set, key=len, reverse=True)
        # Build alternation pattern with word boundaries
        escaped = [re.escape(a) for a in sorted_aliases]
        pattern_str = r"\b(?:" + "|".join(escaped) + r")\b"
        try:
            return re.compile(pattern_str, re.IGNORECASE)
        except re.error:
            return None

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        # Extract brands first — needed for proximity-based brand detection
        brand_exts = self._match_brands(text, section)
        results.extend(brand_exts)
        model_exts = self._match_models(text, section)
        results.extend(model_exts)
        # KB-powered alias matching (second pass for models the regex missed)
        results.extend(self._match_kb_aliases(text, section, model_exts))
        results.extend(self._match_objectives(text, section, brand_exts))
        results.extend(self._match_lasers(text, section, brand_exts))
        results.extend(self._match_detectors(text, section, brand_exts))
        results.extend(self._match_filters(text, section, brand_exts))
        results.extend(self._match_reagent_suppliers(text, section))
        # KB-powered inference (brand from model, etc.)
        results = self._kb_inference(results, text, section)
        return self._deduplicate(results)

    # ------------------------------------------------------------------
    # KB-powered alias matching
    # ------------------------------------------------------------------

    def _match_kb_aliases(self, text: str, section: str = None,
                          existing_models: List[Extraction] = None) -> List[Extraction]:
        """Match KB aliases against text to detect models the regex patterns miss.

        Skips aliases that overlap with already-detected models (from _match_models).
        """
        if not self._kb_alias_re:
            return []

        # Build set of character ranges already covered by regex model matches
        covered: Set[int] = set()
        for ext in (existing_models or []):
            if ext.start >= 0 and ext.end >= 0:
                covered.update(range(ext.start, ext.end))

        all_aliases = get_all_aliases()
        extractions: List[Extraction] = []
        seen_canonicals: Set[str] = set()

        # Also track canonicals already found by regex
        for ext in (existing_models or []):
            seen_canonicals.add(ext.canonical().lower())

        for m in self._kb_alias_re.finditer(text):
            # Skip if overlapping with existing model extraction
            if any(pos in covered for pos in range(m.start(), m.end())):
                continue

            matched_lower = m.group(0).lower()
            canonical = all_aliases.get(matched_lower)
            if not canonical:
                continue

            # Skip if we already have this canonical model
            if canonical.lower() in seen_canonicals:
                continue

            # Look up the system in KB for brand info and full display name
            system = resolve_alias(matched_lower)
            if not system:
                # Cannot resolve to a full KB system — skip
                continue
            brand = system.get("brand")
            # Override canonical with full display name (brand + model + category)
            canonical = self._build_full_name(system)

            conf = get_confidence("MICROSCOPE_MODEL", section)
            # Slightly lower confidence for KB alias matches vs direct regex
            conf *= 0.95

            meta: Dict = {"canonical": canonical, "source": "kb_alias"}
            if brand:
                meta["brand"] = brand

            extractions.append(Extraction(
                text=m.group(0),
                label="MICROSCOPE_MODEL",
                start=m.start(),
                end=m.end(),
                confidence=conf,
                source_agent=self.name,
                section=section or "",
                metadata=meta,
            ))
            seen_canonicals.add(canonical.lower())

        return extractions

    # ------------------------------------------------------------------
    # KB-powered inference
    # ------------------------------------------------------------------

    def _kb_inference(self, extractions: List[Extraction],
                      text: str, section: str = None) -> List[Extraction]:
        """Use KB to infer missing brand metadata from detected models."""
        # 1. For each detected model, fill in brand if missing
        for ext in extractions:
            if ext.label == "MICROSCOPE_MODEL" and not ext.metadata.get("brand"):
                brand = infer_brand_from_model(ext.canonical())
                if brand:
                    ext.metadata["brand"] = brand

        # 2. If we found a model but the corresponding brand is missing
        #    from extractions, synthesize a brand extraction
        found_brands = {e.canonical() for e in extractions
                        if e.label == "MICROSCOPE_BRAND"}
        for ext in extractions:
            if ext.label == "MICROSCOPE_MODEL":
                brand = ext.metadata.get("brand") or infer_brand_from_model(ext.canonical())
                if brand and brand not in found_brands:
                    extractions.append(Extraction(
                        text=brand,
                        label="MICROSCOPE_BRAND",
                        start=ext.start,
                        end=ext.end,
                        confidence=ext.confidence * 0.95,
                        source_agent=self.name,
                        section=section or "",
                        metadata={"canonical": brand,
                                  "inferred_from": ext.canonical()},
                    ))
                    found_brands.add(brand)

        return extractions

    # ------------------------------------------------------------------
    # Brand proximity detection
    # ------------------------------------------------------------------

    # Brands that make objective lenses (subset of MICROSCOPE_BRANDS)
    _OBJECTIVE_MAKERS = {
        "Zeiss", "Leica", "Nikon", "Olympus", "Evident (Olympus)",
        "Mitutoyo", "Thorlabs",
    }

    @staticmethod
    def _find_nearby_brand(
        pos: int,
        brand_exts: List[Extraction],
        max_distance: int = 200,
        allowed_brands: set = None,
    ) -> Optional[str]:
        """Find the nearest brand mention within max_distance characters.

        Parameters
        ----------
        pos : int
            Character position in the text to search around.
        brand_exts : list
            Brand extractions from _match_brands.
        max_distance : int
            Maximum character distance to search.
        allowed_brands : set, optional
            If provided, only return brands in this set.

        Returns the canonical brand name if found, else None.
        """
        best_brand = None
        best_dist = max_distance + 1
        for ext in brand_exts:
            if ext.label != "MICROSCOPE_BRAND":
                continue
            canonical = ext.canonical()
            if allowed_brands and canonical not in allowed_brands:
                continue
            dist = min(abs(pos - ext.start), abs(pos - ext.end))
            if dist < best_dist:
                best_dist = dist
                best_brand = canonical
        return best_brand if best_dist <= max_distance else None

    # ------------------------------------------------------------------
    def _match_brands(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []

        for key, canonical in MICROSCOPE_BRANDS.items():
            # Avoid false-positive "prior" in normal text
            if key == "prior":
                continue  # handled by context patterns below
            # Skip short acronyms — they are matched ONLY via full
            # expansion or via _BRAND_CONTEXT_PATTERNS
            if key in _ACRONYM_ONLY_BRANDS:
                continue
            # Use word-boundary regex to avoid substring matches
            pattern = re.compile(r"\b" + re.escape(key) + r"\b", re.I)
            m = pattern.search(text)
            if m:
                conf = get_confidence("MICROSCOPE_BRAND", section)
                extractions.append(Extraction(
                    text=m.group(0),
                    label="MICROSCOPE_BRAND",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        # Context-requiring patterns
        for pattern, canonical in _BRAND_CONTEXT_PATTERNS:
            for m in pattern.finditer(text):
                extractions.append(Extraction(
                    text=m.group(0),
                    label="MICROSCOPE_BRAND",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.85,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        # Prior Scientific context patterns (avoid bare "prior")
        for pattern in _PRIOR_PATTERNS:
            for m in pattern.finditer(text):
                extractions.append(Extraction(
                    text=m.group(0),
                    label="MICROSCOPE_BRAND",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.85,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": "Prior Scientific"},
                ))

        return extractions

    # ------------------------------------------------------------------
    # Category → human-readable suffix for full microscope display names
    _CATEGORY_DISPLAY: Dict[str, str] = {
        "confocal": "Confocal",
        "super_resolution": "Super-Resolution",
        "light_sheet": "Light Sheet",
        "spinning_disk": "Spinning Disk",
        "multiphoton": "Multiphoton",
        "electron": "Electron Microscope",
        "slide_scanner": "Slide Scanner",
        "high_content_screening": "High-Content Screening",
        # "widefield" and "other" are omitted — widefield bodies (Ti, IX83)
        # are used with various accessories so the category is not helpful.
    }

    def _build_full_name(self, system: Dict) -> str:
        """Build a full descriptive name from a KB system dict.

        Example: {"brand": "Leica", "model": "SP8", "category": "confocal"}
        → "Leica SP8 Confocal"
        """
        base = f"{system['brand']} {system['model']}"
        cat = system.get("category", "")
        suffix = self._CATEGORY_DISPLAY.get(cat, "")
        if suffix and suffix.lower() not in base.lower():
            return f"{base} {suffix}"
        return base

    def _match_models(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for pattern, name_fn, brand in MODEL_PATTERNS:
            for m in pattern.finditer(text):
                short_name = name_fn(m)
                conf = get_confidence("MICROSCOPE_MODEL", section)

                # Resolve short name → full canonical via KB system lookup.
                # Try multiple forms: bare short name, "Brand ShortName"
                system = resolve_alias(short_name)
                if not system and brand:
                    system = resolve_alias(f"{brand} {short_name}")

                if system:
                    # Build full display name: "Brand Model Category"
                    canonical = self._build_full_name(system)
                    brand = brand or system.get("brand")
                elif brand:
                    # Not in KB but brand is known — use "Brand Model"
                    if not short_name.lower().startswith(brand.lower()):
                        canonical = f"{brand} {short_name}"
                    else:
                        canonical = short_name
                else:
                    # No KB entry AND no brand — skip bare short names
                    continue

                meta: Dict = {"canonical": canonical}
                if brand:
                    meta["brand"] = brand
                extractions.append(Extraction(
                    text=m.group(0),
                    label="MICROSCOPE_MODEL",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata=meta,
                ))
        return extractions

    # ------------------------------------------------------------------
    def _match_objectives(self, text: str, section: str = None,
                          brand_exts: List[Extraction] = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        brand_exts = brand_exts or []
        # Track positions covered by branded matches to avoid duplicates
        covered_ranges: List[tuple] = []

        # 1. Branded objectives (HC PL APO 63x/1.4 NA oil, CFI Plan Apo 60x, etc.)
        for m in _OBJECTIVE_BRANDED_RE.finditer(text):
            prefix = m.group(1).strip()
            mag = m.group(2)
            na = m.group(3) or ""
            immersion = (m.group(4) or "").lower()
            brand = _OBJECTIVE_BRAND_MAP.get(prefix, "")

            # Build canonical: "Brand Prefix Magx/NA immersion"
            canonical = f"{brand} {prefix} {mag}x" if brand else f"{prefix} {mag}x"
            if na:
                canonical += f"/{na} NA"
            if immersion:
                canonical += f" {immersion}"

            meta = {
                "canonical": canonical,
                "magnification": f"{mag}x",
                "brand": brand,
            }
            if na:
                meta["na"] = na
            if immersion:
                meta["immersion"] = immersion

            covered_ranges.append((m.start(), m.end()))
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="OBJECTIVE",
                start=m.start(), end=m.end(),
                confidence=get_confidence("OBJECTIVE", section),
                source_agent=self.name,
                section=section or "",
                metadata=meta,
            ))

        # 2. Full spec objectives (60x/1.4 NA oil) — skip if already covered
        for m in _OBJECTIVE_FULL_RE.finditer(text):
            # Skip if this match overlaps with a branded objective
            if any(s <= m.start() <= e or s <= m.end() <= e
                   for s, e in covered_ranges):
                continue

            mag = m.group(1)
            na = m.group(2)
            immersion = (m.group(3) or "").lower()

            # Try to find brand from nearby text
            brand = self._find_nearby_brand(
                    m.start(), brand_exts, max_distance=150,
                    allowed_brands=self._OBJECTIVE_MAKERS)

            canonical = f"{brand} {mag}x/{na} NA" if brand else f"{mag}x/{na} NA"
            if immersion:
                canonical += f" {immersion}"

            meta = {
                "canonical": canonical,
                "magnification": f"{mag}x",
                "na": na,
                "immersion": immersion or "unknown",
            }
            if brand:
                meta["brand"] = brand

            covered_ranges.append((m.start(), m.end()))
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="OBJECTIVE",
                start=m.start(), end=m.end(),
                confidence=get_confidence("OBJECTIVE", section),
                source_agent=self.name,
                section=section or "",
                metadata=meta,
            ))

        # 3. Type-based objectives (Plan Apo 60x) — skip if already covered
        for m in _OBJECTIVE_TYPE_RE.finditer(text):
            if any(s <= m.start() <= e or s <= m.end() <= e
                   for s, e in covered_ranges):
                continue

            mag = m.group(1)
            matched_text = m.group(0).strip()

            # Determine brand from prefix
            brand = None
            for prefix, prefix_brand in _OBJECTIVE_BRAND_MAP.items():
                if matched_text.lower().startswith(prefix.lower()):
                    brand = prefix_brand
                    break

            # Fallback: nearby brand
            if not brand:
                brand = self._find_nearby_brand(
                    m.start(), brand_exts, max_distance=150,
                    allowed_brands=self._OBJECTIVE_MAKERS)

            canonical = f"{brand} {matched_text}" if brand else matched_text

            meta = {"canonical": canonical, "magnification": f"{mag}x"}
            if brand:
                meta["brand"] = brand

            extractions.append(Extraction(
                text=matched_text,
                label="OBJECTIVE",
                start=m.start(), end=m.end(),
                confidence=get_confidence("OBJECTIVE", section),
                source_agent=self.name,
                section=section or "",
                metadata=meta,
            ))

        return extractions

    # ------------------------------------------------------------------
    def _match_lasers(self, text: str, section: str = None,
                      brand_exts: List[Extraction] = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        brand_exts = brand_exts or []
        seen_canonicals: Set[str] = set()

        # 1. Specific laser system models (highest priority — these ARE the brand)
        for entry in _LASER_SYSTEM_PATTERNS:
            pattern, canonical_override, brand, laser_type = entry
            for m in pattern.finditer(text):
                matched = m.group(0).strip()
                canonical = canonical_override or matched

                # For generic branded pattern, extract brand from group
                if brand is None and m.lastindex and m.lastindex >= 1:
                    raw_brand = m.group(1).strip()
                    brand = MICROSCOPE_BRANDS.get(raw_brand.lower(), raw_brand)

                # Build canonical: "Brand Model"
                if brand and not canonical.lower().startswith(brand.lower()):
                    canonical = f"{brand} {canonical}"

                if canonical.lower() in seen_canonicals:
                    continue
                seen_canonicals.add(canonical.lower())

                meta = {"canonical": canonical}
                if brand:
                    meta["brand"] = brand
                if laser_type:
                    meta["type"] = laser_type

                extractions.append(Extraction(
                    text=matched,
                    label="LASER",
                    start=m.start(), end=m.end(),
                    confidence=get_confidence("LASER", section),
                    source_agent=self.name,
                    section=section or "",
                    metadata=meta,
                ))

        # NOTE: Generic laser type mentions (argon, Ti:Sapphire, two-photon,
        # pulsed, diode, CW, etc.) and wavelength-only lasers (488 nm laser)
        # are intentionally NOT extracted.  Only brand-specific laser system
        # models (Coherent Chameleon, Mai Tai, OBIS, iBeam, SuperK, etc.) are
        # useful tags for finding specific equipment.

        return extractions

    # ------------------------------------------------------------------
    def _match_detectors(self, text: str, section: str = None,
                         brand_exts: List[Extraction] = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        brand_exts = brand_exts or []

        for pattern, canonical_override, brand in DETECTOR_PATTERNS:
            for m in pattern.finditer(text):
                matched = m.group(0).strip()

                # Determine brand: from pattern, from nearby context, or None
                det_brand = brand
                if not det_brand:
                    det_brand = self._find_nearby_brand(
                        m.start(), brand_exts, max_distance=150
                    )

                # Build canonical with brand
                base = canonical_override or matched
                if det_brand and not base.lower().startswith(det_brand.lower()):
                    canonical = f"{det_brand} {base}"
                else:
                    canonical = base

                meta = {"canonical": canonical}
                if det_brand:
                    meta["brand"] = det_brand
                # Include detector type for generic matches
                if canonical_override:
                    meta["type"] = canonical_override

                extractions.append(Extraction(
                    text=matched,
                    label="DETECTOR",
                    start=m.start(), end=m.end(),
                    confidence=get_confidence("DETECTOR", section),
                    source_agent=self.name,
                    section=section or "",
                    metadata=meta,
                ))

        return extractions

    # ------------------------------------------------------------------
    def _match_filters(self, text: str, section: str = None,
                       brand_exts: List[Extraction] = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        brand_exts = brand_exts or []

        # 1. Chroma-branded filters (ET525/50, AT488/6x, etc.)
        for m in _CHROMA_FILTER_RE.finditer(text):
            matched = " ".join(m.group(0).split())  # collapse whitespace/newlines
            # If text explicitly says "Chroma", it's captured in the match
            brand = "Chroma" if "chroma" in matched.lower() else None
            if not brand:
                # Check if "Chroma" is nearby
                brand = self._find_nearby_brand(
                    m.start(), brand_exts, max_distance=150)
                # ET/AT/ZET prefixes are Chroma-specific
                prefix = matched.split()[0] if " " in matched else matched[:2]
                if prefix.upper() in ("ET", "AT", "ZET", "Z", "HQ"):
                    brand = brand or "Chroma"

            canonical = f"{brand} {matched}" if brand and brand.lower() not in matched.lower() else matched

            extractions.append(Extraction(
                text=matched,
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical, "brand": brand or "", "type": "bandpass"},
            ))

        # 2. Semrock-branded filters (FF, BrightLine, Di)
        for m in _SEMROCK_FILTER_RE.finditer(text):
            matched = " ".join(m.group(0).split())
            brand = "Semrock" if "semrock" in matched.lower() else None
            if not brand:
                brand = self._find_nearby_brand(
                    m.start(), brand_exts, max_distance=150)
                prefix = matched.split()[0] if " " in matched else matched[:2]
                if prefix.upper() in ("FF", "DI") or "BrightLine" in matched:
                    brand = brand or "Semrock"

            canonical = f"{brand} {matched}" if brand and brand.lower() not in matched.lower() else matched

            extractions.append(Extraction(
                text=matched,
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical, "brand": brand or "", "type": "filter_set"},
            ))

        # 3. Filter cubes/sets with brand
        for m in _FILTER_CUBE_RE.finditer(text):
            brand = m.group(1) or ""
            cube_num = m.group(2)
            if not brand:
                brand = self._find_nearby_brand(m.start(), brand_exts, max_distance=100) or ""

            canonical = f"{brand} Filter Set {cube_num}" if brand else f"Filter Set {cube_num}"

            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical.strip(), "brand": brand, "type": "filter_cube"},
            ))

        # 4. Zeiss filter sets
        for m in _ZEISS_FILTER_RE.finditer(text):
            set_num = m.group(1)
            brand = "Zeiss" if "zeiss" in m.group(0).lower() else ""
            if not brand:
                brand = self._find_nearby_brand(m.start(), brand_exts, max_distance=100) or ""
            canonical = f"{brand} Filter Set {set_num}" if brand else f"Filter Set {set_num}"

            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical.strip(), "brand": brand, "type": "filter_set"},
            ))

        # 5. Generic bandpass spec (525/50 bandpass) — with brand from proximity
        for m in _FILTER_RE.finditer(text):
            center = m.group(1)
            width = m.group(2)
            brand = self._find_nearby_brand(m.start(), brand_exts, max_distance=100) or ""

            if brand:
                canonical = f"{brand} {center}/{width} bandpass"
            else:
                canonical = f"{center}/{width} bandpass"

            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={
                    "canonical": canonical, "brand": brand,
                    "center_nm": center, "bandwidth_nm": width, "type": "bandpass",
                },
            ))

        # 6. Dichroics — with brand from proximity
        for m in _DICHROIC_RE.finditer(text):
            brand = self._find_nearby_brand(m.start(), brand_exts, max_distance=100) or ""
            matched = m.group(0).strip()
            if brand:
                canonical = f"{brand} {matched}"
            else:
                canonical = matched

            extractions.append(Extraction(
                text=matched,
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical, "brand": brand, "type": "dichroic"},
            ))

        return extractions

    # ------------------------------------------------------------------
    def _match_reagent_suppliers(self, text: str,
                                 section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for m in _REAGENT_PATTERN.finditer(text):
            canonical = REAGENT_SUPPLIERS.get(m.group(1).lower(), m.group(1))
            extractions.append(Extraction(
                text=m.group(0),
                label="REAGENT_SUPPLIER",
                start=m.start(),
                end=m.end(),
                confidence=get_confidence("REAGENT_SUPPLIER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical},
            ))
        return extractions
