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
    "intelligent imaging innovations": "3i (Intelligent Imaging)",
    "3i intelligent imaging": "3i (Intelligent Imaging)",
    "3i (intelligent imaging)": "3i (Intelligent Imaging)",
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
    "olympus life science": "Olympus",
    "motic": "Motic",
    "leica biosystems": "Leica",
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

# Additional patterns that need context to avoid false positives
_BRAND_CONTEXT_PATTERNS = [
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
}

# Context patterns for reagent suppliers (e.g. "Sigma-Aldrich, St. Louis")
_REAGENT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in REAGENT_SUPPLIERS) + r")\b",
    re.IGNORECASE,
)


# ======================================================================
# Objective lens patterns
# ======================================================================

# Matches "60x/1.4 NA oil", "100x 1.49NA", "40× 0.95 NA", etc.
_OBJECTIVE_FULL_RE = re.compile(
    r"(\d{1,3})\s*[x×X]\s*/?\s*(\d+\.?\d*)\s*(?:NA|N\.A\.)"
    r"(?:\s+(oil|water|silicone|glycerol|air|dry|multi[- ]?immersion))?"
    r"(?:\s+(?:objective|lens))?",
    re.IGNORECASE,
)

# Matches standalone "Plan Apo 60x" or "Apo TIRF 100x"
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
# Laser patterns
# ======================================================================

_LASER_WAVELENGTH_RE = re.compile(
    r"(\d{3,4})\s*[-–]?\s*nm\s*(?:laser|excitation|line|diode|DPSS)?",
    re.IGNORECASE,
)

_LASER_TYPE_RE = re.compile(
    r"\b(argon|krypton|HeNe|He-Ne|diode|DPSS|Ti[:-]?Sapph(?:ire)?|"
    r"femtosecond|picosecond|pulsed|CW|multiphoton|two[- ]?photon|"
    r"Mai\s*Tai|Chameleon|InSight|Coherent)\s*(?:laser)?",
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
# Detector patterns
# ======================================================================

DETECTOR_PATTERNS = [
    (re.compile(r"\bPMT\b"), "PMT"),
    (re.compile(r"\bGaAsP\b", re.I), "GaAsP"),
    (re.compile(r"\bHyD\b(?:\s*[SX])?", re.I), "HyD"),
    (re.compile(r"\bsCMOS\b", re.I), "sCMOS"),
    (re.compile(r"\bEMCCD\b", re.I), "EMCCD"),
    (re.compile(r"\bCCD\b(?!\s*camera\s+phone)", re.I), "CCD"),
    (re.compile(r"\bAPD\b"), "APD"),
    (re.compile(r"\bSPAD\b"), "SPAD"),
    (re.compile(r"\bMCP\b(?=.{0,20}(?:detector|channel|plate))", re.I | re.S), "MCP"),
    # Camera models used as detectors
    (re.compile(r"\bORCA[- ]?(?:Flash|Fusion|Quest|Spark)\s*\w*\b", re.I), None),
    (re.compile(r"\biXon\s*\w*\b", re.I), None),
    (re.compile(r"\bZyla\s*\w*\b", re.I), None),
    (re.compile(r"\bSona\s*\w*\b", re.I), None),
    (re.compile(r"\bNeo\s+\d\.\d\b", re.I), None),
    (re.compile(r"\bKinetix\b", re.I), None),
    (re.compile(r"\bPrime\s*(?:BSI|95B)\b", re.I), None),
]

# ======================================================================
# Filter patterns
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

_FILTER_SET_RE = re.compile(
    r"\b(?:(?:Chroma|Semrock)\s+)?(?:ET|FF|BrightLine)\s*\d{3,4}/\d{1,3}\b",
    re.IGNORECASE,
)


class EquipmentAgent(BaseAgent):
    """Extract microscope brands, models, objectives, lasers, detectors, filters."""

    name = "equipment"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        results.extend(self._match_brands(text, section))
        results.extend(self._match_models(text, section))
        results.extend(self._match_objectives(text, section))
        results.extend(self._match_lasers(text, section))
        results.extend(self._match_detectors(text, section))
        results.extend(self._match_filters(text, section))
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
                conf = get_confidence("MICROSCOPE_BRAND", section)
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
    def _match_objectives(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []

        for m in _OBJECTIVE_FULL_RE.finditer(text):
            mag = m.group(1)
            na = m.group(2)
            immersion = (m.group(3) or "").lower()
            canonical = f"{mag}x/{na} NA"
            if immersion:
                canonical += f" {immersion}"
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="OBJECTIVE",
                start=m.start(), end=m.end(),
                confidence=get_confidence("OBJECTIVE", section),
                source_agent=self.name,
                section=section or "",
                metadata={
                    "canonical": canonical,
                    "magnification": f"{mag}x",
                    "na": na,
                    "immersion": immersion or "unknown",
                },
            ))

        for m in _OBJECTIVE_TYPE_RE.finditer(text):
            mag = m.group(1)
            canonical = f"{m.group(0).strip()}"
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="OBJECTIVE",
                start=m.start(), end=m.end(),
                confidence=get_confidence("OBJECTIVE", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical, "magnification": f"{mag}x"},
            ))

        return extractions

    # ------------------------------------------------------------------
    def _match_lasers(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        seen_wavelengths: Set[str] = set()

        for m in _LASER_WAVELENGTH_RE.finditer(text):
            wl = m.group(1)
            if wl not in _COMMON_LASER_LINES:
                continue
            if wl in seen_wavelengths:
                continue
            seen_wavelengths.add(wl)

            canonical = f"{wl} nm laser"
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="LASER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("LASER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical, "wavelength_nm": wl},
            ))

        for m in _LASER_TYPE_RE.finditer(text):
            canonical = m.group(0).strip()
            extractions.append(Extraction(
                text=canonical,
                label="LASER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("LASER", section) * 0.9,
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical},
            ))

        return extractions

    # ------------------------------------------------------------------
    def _match_detectors(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []

        for pattern, canonical_override in DETECTOR_PATTERNS:
            for m in pattern.finditer(text):
                matched = m.group(0).strip()
                canonical = canonical_override or matched
                extractions.append(Extraction(
                    text=matched,
                    label="DETECTOR",
                    start=m.start(), end=m.end(),
                    confidence=get_confidence("DETECTOR", section),
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        return extractions

    # ------------------------------------------------------------------
    def _match_filters(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []

        for m in _FILTER_RE.finditer(text):
            center = m.group(1)
            width = m.group(2)
            canonical = f"{center}/{width} bandpass"
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": canonical, "center_nm": center, "bandwidth_nm": width},
            ))

        for m in _DICHROIC_RE.finditer(text):
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": m.group(0).strip(), "type": "dichroic"},
            ))

        for m in _FILTER_SET_RE.finditer(text):
            extractions.append(Extraction(
                text=m.group(0).strip(),
                label="FILTER",
                start=m.start(), end=m.end(),
                confidence=get_confidence("FILTER", section),
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": m.group(0).strip(), "type": "filter_set"},
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
