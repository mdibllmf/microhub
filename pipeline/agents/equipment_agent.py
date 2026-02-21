"""
Equipment extraction agent -- microscope brands, models, and related hardware.

Uses a hybrid regex + dictionary approach since no pre-trained NER model
exists for laboratory equipment.  Pattern matching follows the convention
of manufacturer name followed by alphanumeric model identifier.

Also detects reagent suppliers (separated from microscope brands in v5.2).

All equipment extractions (lasers, objectives, detectors, filters) include
brand/vendor metadata for specificity.
"""

import re
from typing import Dict, List, Optional, Set

from .base_agent import BaseAgent, Extraction
from ..confidence import get_confidence

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
    "asi", "pco", "fei", "3i", "jeol",
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
    """

    name = "equipment"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        # Extract brands first — needed for proximity-based brand detection
        brand_exts = self._match_brands(text, section)
        results.extend(brand_exts)
        results.extend(self._match_models(text, section))
        results.extend(self._match_objectives(text, section, brand_exts))
        results.extend(self._match_lasers(text, section, brand_exts))
        results.extend(self._match_detectors(text, section, brand_exts))
        results.extend(self._match_filters(text, section, brand_exts))
        results.extend(self._match_reagent_suppliers(text, section))
        return self._deduplicate(results)

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
    def _match_models(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for pattern, name_fn, brand in MODEL_PATTERNS:
            for m in pattern.finditer(text):
                canonical = name_fn(m)
                conf = get_confidence("MICROSCOPE_MODEL", section)
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
