"""
Equipment extraction agent -- microscope brands, models, and related hardware.

Uses a hybrid regex + dictionary approach since no pre-trained NER model
exists for laboratory equipment.  Pattern matching follows the convention
of manufacturer name followed by alphanumeric model identifier.

Also detects reagent suppliers (separated from microscope brands in v5.2).
"""

import re
from typing import Dict, List, Set

from .base_agent import BaseAgent, Extraction

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
    "andor": "Andor",
    "andor technology": "Andor",
    "yokogawa": "Yokogawa",
    "perkinelmer": "PerkinElmer",
    "perkin elmer": "PerkinElmer",
    "hamamatsu": "Hamamatsu",
    "hamamatsu photonics": "Hamamatsu",
    "jeol": "JEOL",
    "thermo fisher": "Thermo Fisher",
    "thermofisher": "Thermo Fisher",
    "fei": "Thermo Fisher",
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
    "lavision biotec": "LaVision BioTec",
    "lavision": "LaVision BioTec",
    "luxendo": "Luxendo",
    "molecular devices": "Molecular Devices",
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
}

# Additional patterns that need context to avoid false positives
_BRAND_CONTEXT_PATTERNS = [
    # "Prior Scientific" vs the word "prior"
    (re.compile(r"\bPrior\s+Scientific\b", re.I), "Prior Scientific"),
    # "ASI" needs microscopy context
    (re.compile(r"\bASI\s+(?:stage|controller|MS-?\d|Tiger)", re.I), "ASI"),
    # "3i" needs context
    (re.compile(r"\b3i\s+(?:Marianas|SlideBook|spinning)", re.I), "3i (Intelligent Imaging)"),
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

    # Electron microscope models
    (re.compile(r"\bTitan\s*(?:Krios)?\b", re.I), lambda m: "Titan", "Thermo Fisher"),
    (re.compile(r"\bGlacios\b", re.I), lambda m: "Glacios", "Thermo Fisher"),
    (re.compile(r"\bTalos\b", re.I), lambda m: "Talos", "Thermo Fisher"),
    (re.compile(r"\bTecnai\b", re.I), lambda m: "Tecnai", "Thermo Fisher"),
    (re.compile(r"\bCM200\b"), lambda m: "CM200", "Thermo Fisher"),
    (re.compile(r"\bJEM-?(?:1400|2100)\b"), lambda m: m.group(0), "JEOL"),

    # SPIM systems (these are specific microscope systems)
    (re.compile(r"\bMesoSPIM\b", re.I), lambda m: "MesoSPIM", None),
    (re.compile(r"\bdiSPIM\b", re.I), lambda m: "diSPIM", None),
    (re.compile(r"\biSPIM\b"), lambda m: "iSPIM", None),
    (re.compile(r"\bOpenSPIM\b", re.I), lambda m: "OpenSPIM", None),
    (re.compile(r"\bUltraMicroscope\b", re.I), lambda m: "UltraMicroscope", None),
    (re.compile(r"\bSmartSPIM\b", re.I), lambda m: "SmartSPIM", None),
]

# ======================================================================
# Reagent suppliers (separated from microscope brands in v5.2)
# ======================================================================

REAGENT_SUPPLIERS: Dict[str, str] = {
    "invitrogen": "Invitrogen",
    "thermo fisher scientific": "Thermo Fisher Scientific",
    "sigma-aldrich": "Sigma-Aldrich",
    "sigma aldrich": "Sigma-Aldrich",
    "merck": "Merck",
    "abcam": "Abcam",
    "cell signaling": "Cell Signaling Technology",
    "cell signaling technology": "Cell Signaling Technology",
    "bio-rad": "Bio-Rad",
    "biorad": "Bio-Rad",
    "jackson immunoresearch": "Jackson ImmunoResearch",
    "life technologies": "Life Technologies",
    "santa cruz": "Santa Cruz Biotechnology",
    "bd biosciences": "BD Biosciences",
    "millipore": "Millipore",
    "emd millipore": "Millipore",
    "corning": "Corning",
    "ibidi": "ibidi",
    "mattek": "MatTek",
    "lonza": "Lonza",
    "gibco": "Gibco",
    "promega": "Promega",
    "new england biolabs": "New England Biolabs",
    "neb": "New England Biolabs",
    "takara": "Takara Bio",
    "roche": "Roche",
    "dako": "Dako",
    "agilent": "Agilent",
    "vector laboratories": "Vector Laboratories",
    "biotium": "Biotium",
    "tocris": "Tocris",
    "addgene": "Addgene",
}

# Context patterns for reagent suppliers (e.g. "Sigma-Aldrich, St. Louis")
_REAGENT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in REAGENT_SUPPLIERS) + r")\b",
    re.IGNORECASE,
)


class EquipmentAgent(BaseAgent):
    """Extract microscope brands, models, and reagent suppliers."""

    name = "equipment"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        results.extend(self._match_brands(text, section))
        results.extend(self._match_models(text, section))
        results.extend(self._match_reagent_suppliers(text, section))
        return self._deduplicate(results)

    # ------------------------------------------------------------------
    def _match_brands(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        text_lower = text.lower()

        for key, canonical in MICROSCOPE_BRANDS.items():
            # Avoid false-positive "prior" in normal text
            if key == "prior":
                continue  # handled by context patterns below
            idx = text_lower.find(key)
            if idx != -1:
                conf = 0.9 if section in ("methods", "materials") else 0.7
                extractions.append(Extraction(
                    text=text[idx:idx + len(key)],
                    label="MICROSCOPE_BRAND",
                    start=idx,
                    end=idx + len(key),
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

        return extractions

    # ------------------------------------------------------------------
    def _match_models(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for pattern, name_fn, brand in MODEL_PATTERNS:
            for m in pattern.finditer(text):
                canonical = name_fn(m)
                conf = 0.9 if section in ("methods", "materials") else 0.75
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
                confidence=0.8,
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical},
            ))
        return extractions
