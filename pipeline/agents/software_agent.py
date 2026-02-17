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
    "fiji": "Fiji",
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
    "omero": "OMERO",
    "dragonfly": "Dragonfly",
    "amira": "Amira",
    "huygens": "Huygens",
    "icy": "Icy",
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
    "pymol": "PyMOL",
    "neurolucida": "Neurolucida",
    "halo": "HALO",
    "inform": "inForm",
    "autoquant": "AutoQuant",
    "digital micrograph": "Digital Micrograph",
    "imod": "IMOD",
    "eman2": "EMAN2",
    "relion": "RELION",
    "cryosparc": "cryoSPARC",
    "cryo-sparc": "cryoSPARC",
    "scipion": "Scipion",
    "serialem": "SerialEM",
    "vaa3d": "Vaa3D",
    "aivia": "Aivia",
    "sam": "SAM",
    "segment anything": "SAM",
    "mask r-cnn": "Mask R-CNN",
    "mask rcnn": "Mask R-CNN",
    "u-net": "U-Net",
    "unet": "U-Net",
    "yolov": "YOLOv",
    "yolo": "YOLOv",
    "scikit-image": "scikit-image",
    "skimage": "scikit-image",
}

# ======================================================================
# Image acquisition software
# ======================================================================

IMAGE_ACQUISITION_SOFTWARE: Dict[str, str] = {
    "zen": None,  # ZEN needs context (too short and common)
    "zen blue": "ZEN",
    "zen black": "ZEN",
    "zeiss zen": "ZEN",
    "las x": "LAS X",
    "las af": "LAS X",
    "leica las": "LAS X",
    "nis-elements": "NIS-Elements",
    "nis elements": "NIS-Elements",
    "metamorph": "MetaMorph",
    "slidebook": "SlideBook",
    "volocity": "Volocity",
    "volocity acquisition": "Volocity Acquisition",
    "harmony": "Harmony",
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
    "in cell": "IN Cell",
    "opera phenix": "Opera Phenix",
    "columbus": "Columbus",
    "arrayscan": "ArrayScan",
}

# Context pattern for "ZEN" to avoid matching the word "zen"
_ZEN_CONTEXT = re.compile(
    r"\bZEN\b(?=\s*(?:blue|black|software|lite|desk|pro|imaging|acquisition"
    r"|2\.\d|3\.\d|microscop))",
    re.IGNORECASE,
)
_ZEN_BRAND_CONTEXT = re.compile(r"\b(?:Zeiss|Carl Zeiss)\b.{0,50}\bZEN\b", re.I | re.S)

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
