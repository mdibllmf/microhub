"""
Software extraction agent -- image analysis and acquisition software.

Separates image analysis software (ImageJ, Fiji, CellProfiler, etc.)
from image acquisition software (ZEN, LAS X, NIS-Elements, etc.)
and general-purpose software (MATLAB, Python, R, etc.).
"""

import re
from typing import Dict, List

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Image analysis software
# ======================================================================

IMAGE_ANALYSIS_SOFTWARE: Dict[str, str] = {
    "imagej": "ImageJ",
    "fiji/imagej": "Fiji",
    "cellprofiler": "CellProfiler",
    "cell profiler": "CellProfiler",
    "imaris": "Imaris",
    "ilastik": "ilastik",
    "qupath": "QuPath",
    "napari": "napari",
    "cellpose": "Cellpose",
    "stardist": "StarDist",
    "deepcell": "DeepCell",
    "dragonfly ors": "Dragonfly",
    "amira": "Amira",
    "huygens": "Huygens",
    "trackmate": "TrackMate",
    "thunderstorm": "ThunderSTORM",
    "deconvolutionlab": "DeconvolutionLab",
    "deconvolution lab": "DeconvolutionLab",
    "bio-formats": "Bio-Formats",
    "bioformats": "Bio-Formats",
    "bigdataviewer": "BigDataViewer",
    "big data viewer": "BigDataViewer",
    "chimerax": "ChimeraX",
    "ucsf chimera": "UCSF Chimera",
    "chimera": "UCSF Chimera",  # bare chimera (ChimeraX handled separately)
    "pymol": "PyMOL",
    "neurolucida": "Neurolucida",
    "halo image analysis": "HALO",
    "indica labs halo": "HALO",
    "inform": "inForm",
    "autoquant": "AutoQuant",
    "digital micrograph": "Digital Micrograph",
    "gatan": "Digital Micrograph",
    "imod": "IMOD",
    "eman2": "EMAN2", "eman": "EMAN2",
    "relion": "RELION",
    "cryosparc": "cryoSPARC",
    "cryo-sparc": "cryoSPARC",
    "scipion": "Scipion",
    "serialem": "SerialEM",
    "vaa3d": "Vaa3D",
    "aivia": "Aivia",
    "segment anything model": "SAM", "segment anything": "SAM", "segment-anything": "SAM",
    "mask r-cnn": "Mask R-CNN",
    "mask rcnn": "Mask R-CNN",
    "u-net": "U-Net",
    "unet": "U-Net",
    "yolov": "YOLOv",
    "yolo": "YOLOv",
    "scikit-image": "scikit-image",
    "skimage": "scikit-image",
    "arivis": "Arivis",
}

# ======================================================================
# Image acquisition software
# ======================================================================

IMAGE_ACQUISITION_SOFTWARE: Dict[str, str] = {
    "zen": None,  # ZEN needs context (too short and common)
    "zen blue": "ZEN",
    "zen black": "ZEN",
    "zeiss zen": "ZEN",
    "leica las x": "LAS X",
    "leica las af": "LAS X",
    "leica las": "LAS X",
    "leica application suite x": "LAS X",
    "leica application suite": "LAS X",
    "las af": "LAS X",
    "nis-elements": "NIS-Elements",
    "nis elements": "NIS-Elements",
    "metamorph": "MetaMorph",
    "slidebook": "SlideBook",
    "volocity": "Volocity",
    "volocity acquisition": "Volocity Acquisition",
    "harmony software": "Harmony",
    "perkinelmer harmony": "Harmony",
    "cellsens": "CellSens",
    "cell sens": "CellSens",
    "fluoview": "FluoView",
    "prairie view": "Prairie View",
    "scanimage": "ScanImage",
    "scan image": "ScanImage",
    "micromanager": "MicroManager",
    "micro-manager": "MicroManager",
    "thorimage": "ThorImage",
    "symphotime": "SymPhoTime",
    "imspector": "Imspector",
    "hcimage": "HCImage",
    "imagexpress": "ImageXpress",
    "cellreporterxpress": "CellReporterXpress",
    "in cell analyzer": "IN Cell",
    "in cell 1000": "IN Cell",
    "in cell 2000": "IN Cell",
    "in cell 2200": "IN Cell",
    "in cell 6000": "IN Cell",
    "in cell 6500": "IN Cell",
    "ge in cell": "IN Cell",
    "ge healthcare in cell": "IN Cell",
    "cytiva in cell": "IN Cell",
    "opera phenix": "Opera Phenix",
    "columbus image analysis": "Columbus",
    "perkinelmer columbus": "Columbus",
    "arrayscan": "ArrayScan",
}

# Context pattern for "ZEN" to avoid matching the word "zen"
_ZEN_CONTEXT = re.compile(
    r"\bZEN\b(?=\s*(?:blue|black|software|lite|desk|pro|imaging|acquisition"
    r"|2\.\d|3\.\d|microscop))",
    re.IGNORECASE,
)
_ZEN_BRAND_CONTEXT = re.compile(r"\b(?:Zeiss|Carl Zeiss)\b.{0,50}\bZEN\b", re.I | re.S)

# Context pattern for "IN Cell" to avoid matching generic "in cell" phrases
_IN_CELL_CONTEXT = re.compile(
    r"\b(?:GE|GE\s+Healthcare|Cytiva)\s+IN\s+Cell\b"
    r"|\bIN\s+Cell\s+(?:Analyzer|Investigator|imaging|system|platform|\d{4})\b"
    r"|\bIN\s+Cell\b(?=.{0,30}(?:high[- ]?content|screening|imager|system))",
    re.IGNORECASE | re.DOTALL,
)

# Context patterns for ambiguous software names
_AMBIGUOUS_ANALYSIS_PATTERNS = [
    # SAM — "Segment Anything" model; bare "SAM" is too common (name/abbreviation)
    (re.compile(
        r"\bSAM\b(?=.{0,30}(?:segment|mask|model|instance|predict|inference))"
        r"|\bSAM\s+(?:model|segmentation|predictor|mask)\b"
        r"|\b(?:Meta|facebook)\s+SAM\b",
        re.I | re.S,
    ), "SAM"),
    # HALO — Indica Labs image analysis; bare "HALO" matches the word/game
    (re.compile(
        r"\bHALO\b(?=.{0,40}(?:patholog|image|analy|quantif|Indica|software|platform|module))"
        r"|\bIndica\s+Labs\s+HALO\b"
        r"|\bHALO\s+(?:software|platform|AI|module)\b",
        re.I | re.S,
    ), "HALO"),
    # Dragonfly — ORS Dragonfly 3D visualization; bare matches the insect
    (re.compile(
        r"\bDragonfly\b(?=.{0,40}(?:ORS|3D|visuali[sz]|render|image|software|reconstruct|volume))"
        r"|\bORS\s+Dragonfly\b"
        r"|\bDragonfly\s+(?:software|ORS|version|v?\d)\b",
        re.I | re.S,
    ), "Dragonfly"),
    # Icy — bioimage analysis; bare "icy" matches common adjective
    (re.compile(
        r"\bIcy\b(?=.{0,40}(?:bioimage|plugin|image\s+analy|software|platform|spot\s+detect|active\s+contour))"
        r"|\bIcy\s+(?:software|plugin|bioimage|platform)\b"
        r"|\bde\s+Chaumont.{0,30}\bIcy\b",
        re.I | re.S,
    ), "Icy"),
    # Fiji — ImageJ distribution; bare matches country name
    (re.compile(
        r"\bFiji\b(?=.{0,30}(?:ImageJ|macro|plugin|script|software|image\s+analy|processing|measure))"
        r"|\bFiji/ImageJ\b|\bImageJ/Fiji\b"
        r"|\bFiji\s+(?:software|macro|plugin|script|version|v?\d)\b",
        re.I | re.S,
    ), "Fiji"),
    # Harmony — PerkinElmer HCS software; bare matches common word
    (re.compile(
        r"\bHarmony\b(?=.{0,40}(?:PerkinElmer|high[- ]?content|screening|HCS|software|Opera|image\s+analy))"
        r"|\bPerkinElmer\s+Harmony\b"
        r"|\bHarmony\s+(?:software|version|v?\d)\b",
        re.I | re.S,
    ), "Harmony"),
    # Columbus — PerkinElmer image analysis; bare matches city/explorer
    (re.compile(
        r"\bColumbus\b(?=.{0,40}(?:PerkinElmer|image|analy|screen|software|platform|server))"
        r"|\bPerkinElmer\s+Columbus\b"
        r"|\bColumbus\s+(?:software|image|server|platform)\b",
        re.I | re.S,
    ), "Columbus"),
]

# ======================================================================
# General-purpose software
# ======================================================================

GENERAL_SOFTWARE: Dict[str, str] = {
    "matlab": "MATLAB",
    "python": "Python",
    "r statistical": "R",
    "rstudio": "R",
    "r software": "R",
    "graphpad prism": "GraphPad Prism",
    "prism": None,  # too ambiguous alone
    "origin": None,  # too ambiguous
    "spss": "SPSS",
    "igor pro": "Igor Pro",
    "julia": "Julia",
    "java": "Java",
    "c++": "C++",
    "knime": "KNIME",
    "sas": "SAS",
    "microsoft excel": "Excel",
    "excel": "Excel",
}

# R needs context to avoid matching single-letter occurrences
_R_CONTEXT = re.compile(
    r"\b(?:R\s+(?:software|statistical|package|version|programming|script|code|environment)"
    r"|R/Bioconductor"
    r"|(?:using|with|in)\s+R\s+(?:\(|v\d|version))\b",
    re.IGNORECASE,
)


class SoftwareAgent(BaseAgent):
    """Extract image analysis, acquisition, and general software mentions."""

    name = "software"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        results.extend(self._match_analysis(text, section))
        results.extend(self._match_acquisition(text, section))
        results.extend(self._match_general(text, section))
        return self._deduplicate(results)

    # ------------------------------------------------------------------
    def _match_analysis(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for key, canonical in IMAGE_ANALYSIS_SOFTWARE.items():
            pattern = re.compile(r"\b" + re.escape(key) + r"\b", re.I)
            for m in pattern.finditer(text):
                conf = 0.9 if section in ("methods", "materials") else 0.7
                extractions.append(Extraction(
                    text=m.group(0),
                    label="IMAGE_ANALYSIS_SOFTWARE",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        # Context-requiring ambiguous software names (SAM, HALO, Dragonfly,
        # Icy, Fiji, Harmony, Columbus) — these common words need nearby
        # imaging/software context to avoid false positives.
        for ctx_pattern, canonical in _AMBIGUOUS_ANALYSIS_PATTERNS:
            for m in ctx_pattern.finditer(text):
                conf = 0.85 if section in ("methods", "materials") else 0.7
                extractions.append(Extraction(
                    text=m.group(0),
                    label="IMAGE_ANALYSIS_SOFTWARE",
                    start=m.start(), end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        return extractions

    # ------------------------------------------------------------------
    def _match_acquisition(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for key, canonical in IMAGE_ACQUISITION_SOFTWARE.items():
            if canonical is None:
                continue  # needs context
            pattern = re.compile(r"\b" + re.escape(key) + r"\b", re.I)
            for m in pattern.finditer(text):
                conf = 0.85 if section in ("methods", "materials") else 0.65
                extractions.append(Extraction(
                    text=m.group(0),
                    label="IMAGE_ACQUISITION_SOFTWARE",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        # Handle "ZEN" with context
        for m in _ZEN_CONTEXT.finditer(text):
            extractions.append(Extraction(
                text=m.group(0).split()[0],
                label="IMAGE_ACQUISITION_SOFTWARE",
                start=m.start(), end=m.start() + 3,
                confidence=0.85, source_agent=self.name,
                section=section or "",
                metadata={"canonical": "ZEN"},
            ))
        for m in _ZEN_BRAND_CONTEXT.finditer(text):
            idx = text.upper().find("ZEN", m.start())
            if idx >= 0:
                extractions.append(Extraction(
                    text="ZEN",
                    label="IMAGE_ACQUISITION_SOFTWARE",
                    start=idx, end=idx + 3,
                    confidence=0.8, source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": "ZEN"},
                ))

        # Handle "IN Cell" with context (avoid matching generic "in cell" phrases)
        for m in _IN_CELL_CONTEXT.finditer(text):
            extractions.append(Extraction(
                text=m.group(0),
                label="IMAGE_ACQUISITION_SOFTWARE",
                start=m.start(), end=m.end(),
                confidence=0.85, source_agent=self.name,
                section=section or "",
                metadata={"canonical": "IN Cell"},
            ))

        return extractions

    # ------------------------------------------------------------------
    def _match_general(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for key, canonical in GENERAL_SOFTWARE.items():
            if canonical is None:
                continue
            pattern = re.compile(r"\b" + re.escape(key) + r"\b", re.I)
            for m in pattern.finditer(text):
                extractions.append(Extraction(
                    text=m.group(0),
                    label="GENERAL_SOFTWARE",
                    start=m.start(), end=m.end(),
                    confidence=0.7,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        # R with context
        for m in _R_CONTEXT.finditer(text):
            extractions.append(Extraction(
                text="R",
                label="GENERAL_SOFTWARE",
                start=m.start(), end=m.start() + 1,
                confidence=0.8, source_agent=self.name,
                section=section or "",
                metadata={"canonical": "R"},
            ))

        return extractions
