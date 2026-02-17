"""
Microscopy technique extraction agent.

Detects 60+ microscopy techniques using strict pattern matching.
Following v3.7 rules:
  - Abbreviations (STED, TEM, SIM, etc.) require IMMEDIATE microscopy context
    or their FULL expansion to avoid false positives.
  - Standalone abbreviations are NOT matched.
"""

import re
from typing import Dict, List, Tuple

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Technique patterns -- (compiled_regex, canonical_name, confidence)
#
# Rules from cleanup_and_retag.py v3.7:
#   Abbreviation-only techniques require "microscopy", "imaging",
#   "nanoscopy", or similar immediately following the abbreviation,
#   OR the full expansion must appear in the text.
# ======================================================================

# Full expansion patterns -- always high confidence
_EXPANSION_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bstimulated\s+emission\s+depletion\b", re.I), "STED"),
    (re.compile(r"\btransmission\s+electron\s+microscop\w*\b", re.I), "TEM"),
    (re.compile(r"\bscanning\s+electron\s+microscop\w*\b", re.I), "SEM"),
    (re.compile(r"\bstructured\s+illumination\s+microscop\w*\b", re.I), "SIM"),
    (re.compile(r"\bstochastic\s+optical\s+reconstruction\s+microscop\w*\b", re.I), "STORM"),
    (re.compile(r"\bdirect\s+stochastic\s+optical\s+reconstruction\b", re.I), "dSTORM"),
    (re.compile(r"\bphoto[- ]?activated\s+localization\s+microscop\w*\b", re.I), "PALM"),
    (re.compile(r"\bsingle[- ]?molecule\s+localization\s+microscop\w*\b", re.I), "SMLM"),
    (re.compile(r"\bfluorescence\s+lifetime\s+imaging\b", re.I), "FLIM"),
    (re.compile(r"\bfluorescence\s+recovery\s+after\s+photobleaching\b", re.I), "FRAP"),
    (re.compile(r"\bf(?:o|ö)rster\s+resonance\s+energy\s+transfer\b", re.I), "FRET"),
    (re.compile(r"\bfluorescence\s+resonance\s+energy\s+transfer\b", re.I), "FRET"),
    (re.compile(r"\bfluorescence\s+correlation\s+spectroscop\w*\b", re.I), "FCS"),
    (re.compile(r"\bfluorescence\s+cross[- ]?correlation\s+spectroscop\w*\b", re.I), "FCCS"),
    (re.compile(r"\bcoherent\s+anti[- ]?stokes\s+raman\b", re.I), "CARS"),
    (re.compile(r"\bstimulated\s+raman\s+scattering\b", re.I), "SRS"),
    (re.compile(r"\bsecond\s+harmonic\s+generation\b", re.I), "SHG"),
    (re.compile(r"\batomic\s+force\s+microscop\w*\b", re.I), "AFM"),
    (re.compile(r"\bcorrelative\s+light\s+(?:and\s+)?electron\s+microscop\w*\b", re.I), "CLEM"),
    (re.compile(r"\boptical\s+coherence\s+tomograph\w*\b", re.I), "OCT"),
    (re.compile(r"\btotal\s+internal\s+reflection\s+fluorescen\w*\b", re.I), "TIRF"),
    (re.compile(r"\bfocused\s+ion\s+beam[- ]?scanning\s+electron\b", re.I), "FIB-SEM"),
    (re.compile(r"\bfluorescence\s+loss\s+in\s+photobleaching\b", re.I), "FLIP"),
    (re.compile(r"\bserial\s+block[- ]?face\s+(?:scanning\s+)?electron\b", re.I), "Serial Block-Face SEM"),
    (re.compile(r"\blight[- ]?sheet\s+(?:fluorescence\s+)?microscop\w*\b", re.I), "Light Sheet"),
    (re.compile(r"\blattice\s+light[- ]?sheet\b", re.I), "Lattice Light Sheet"),
    (re.compile(r"\bselective\s+plane\s+illumination\s+microscop\w*\b", re.I), "Light Sheet"),
    (re.compile(r"\bsuper[- ]?resolution\s+microscop\w*\b", re.I), "Super-Resolution"),
    (re.compile(r"\bexpansion\s+microscop\w*\b", re.I), "Expansion Microscopy"),
    (re.compile(r"\bconfocal\s+(?:laser\s+scanning\s+)?microscop\w*\b", re.I), "Confocal"),
    (re.compile(r"\blaser\s+scanning\s+confocal\s+microscop\w*\b", re.I), "Confocal"),
    (re.compile(r"\bfluorescence\s+microscop\w*\b", re.I), "Fluorescence Microscopy"),
    (re.compile(r"\btwo[- ]?photon\s+(?:excitation\s+)?microscop\w*\b", re.I), "Two-Photon"),
    (re.compile(r"\b2[- ]?photon\s+(?:excitation\s+)?microscop\w*\b", re.I), "Two-Photon"),
    (re.compile(r"\bmultiphoton\s+microscop\w*\b", re.I), "Multiphoton"),
    (re.compile(r"\bthree[- ]?photon\s+microscop\w*\b", re.I), "Three-Photon"),
    (re.compile(r"\b3[- ]?photon\s+microscop\w*\b", re.I), "Three-Photon"),
    (re.compile(r"\bspinning\s+dis[ck]\s+(?:confocal\s+)?microscop\w*\b", re.I), "Spinning Disk"),
    (re.compile(r"\bwidefield\s+(?:fluorescence\s+)?microscop\w*\b", re.I), "Widefield"),
    (re.compile(r"\bwide[- ]?field\s+(?:fluorescence\s+)?microscop\w*\b", re.I), "Widefield"),
    (re.compile(r"\bepifluorescen\w+\s+microscop\w*\b", re.I), "Epifluorescence"),
    (re.compile(r"\bepi[- ]?fluorescen\w+\s+microscop\w*\b", re.I), "Epifluorescence"),
    (re.compile(r"\bbrightfield\s+microscop\w*\b", re.I), "Brightfield"),
    (re.compile(r"\bbright[- ]?field\s+microscop\w*\b", re.I), "Brightfield"),
    (re.compile(r"\bdark[- ]?field\s+microscop\w*\b", re.I), "Darkfield"),
    (re.compile(r"\bphase[- ]?contrast\s+microscop\w*\b", re.I), "Phase Contrast"),
    (re.compile(r"\bdifferential\s+interference\s+contrast\b", re.I), "DIC"),
    (re.compile(r"\bdarkfield\s+microscop\w*\b", re.I), "Darkfield"),
    (re.compile(r"\bpolarization\s+microscop\w*\b", re.I), "Polarization"),
    (re.compile(r"\bholographic\s+microscop\w*\b", re.I), "Holographic"),
    (re.compile(r"\bphotoacoustic\s+microscop\w*\b", re.I), "Photoacoustic"),
    (re.compile(r"\braman\s+microscop\w*\b", re.I), "Raman"),
    (re.compile(r"\bintravital\s+(?:two[- ]?photon\s+)?microscop\w*\b", re.I), "Intravital"),
    (re.compile(r"\bcalcium\s+imaging\b", re.I), "Calcium Imaging"),
    (re.compile(r"\bvoltage\s+imaging\b", re.I), "Voltage Imaging"),
    (re.compile(r"\blive[- ]?cell\s+imaging\b", re.I), "Live Cell Imaging"),
    (re.compile(r"\bhigh[- ]?content\s+screening\b", re.I), "High-Content Screening"),
    (re.compile(r"\boptogenetic\w*\b", re.I), "Optogenetics"),
    (re.compile(r"\belectron\s+tomograph\w*\b", re.I), "Electron Tomography"),
    (re.compile(r"\barray\s+tomograph\w*\b", re.I), "Array Tomography"),
    (re.compile(r"\bvolume\s+(?:electron\s+)?microscop\w*\b", re.I), "Volume EM"),
    (re.compile(r"\bcryo[- ]?electron\s+microscop\w*\b", re.I), "Cryo-EM"),
    (re.compile(r"\bcryo[- ]?electron\s+tomograph\w*\b", re.I), "Cryo-ET"),
    (re.compile(r"\bnegative\s+stain(?:ing)?\s+(?:electron\s+)?microscop\w*\b", re.I), "Negative Stain EM"),
    (re.compile(r"\bimmuno[- ]?electron\s+microscop\w*\b", re.I), "Immuno-EM"),
    (re.compile(r"\bimmunofluorescen\w*\b", re.I), "Immunofluorescence"),
    (re.compile(r"\bsingle[- ]?molecule\s+(?:fluorescence\s+)?imaging\b", re.I), "Single Molecule"),
    (re.compile(r"\bsingle[- ]?particle\s+(?:cryo[- ]?em|analysis|reconstruction)\b", re.I), "Single Particle"),
    (re.compile(r"\bDNA[- ]?PAINT\b"), "DNA-PAINT"),
    (re.compile(r"\bpoints\s+accumulation\s+for\s+imaging\s+in\s+nanoscale\s+topography\b", re.I), "DNA-PAINT"),
    (re.compile(r"\bMINFLUX\b"), "MINFLUX"),
    (re.compile(r"\bminflux\s+nanoscop\w*\b", re.I), "MINFLUX"),
    (re.compile(r"\bminimal\s+photon\s+flux\b", re.I), "MINFLUX"),
    (re.compile(r"\bRESOLFT\b"), "RESOLFT"),
    (re.compile(r"\breversible\s+saturable\s+optical\s+fluorescence\s+transitions\b", re.I), "RESOLFT"),
    (re.compile(r"\bSOFI\b"), "SOFI"),
    (re.compile(r"\bsuper[- ]?resolution\s+optical\s+fluctuation\s+imaging\b", re.I), "SOFI"),
    (re.compile(r"\bnanoscopy\b", re.I), "Super-Resolution"),
    (re.compile(r"\btime[- ]?lapse\s+(?:microscop\w*|imaging)\b", re.I), "Live Cell Imaging"),
    (re.compile(r"\btimelapse\s+(?:microscop\w*|imaging)\b", re.I), "Live Cell Imaging"),
    (re.compile(r"\bairyscan\s+(?:microscop\w*|imaging)\b", re.I), "Airyscan"),
    (re.compile(r"\b3D\s+imaging\b", re.I), "3D Imaging"),
    (re.compile(r"\b4D\s+imaging\b", re.I), "4D Imaging"),
    (re.compile(r"\bZ[- ]?stack\w*\b", re.I), "Z-Stack"),
    (re.compile(r"\boptical\s+section\w*\b", re.I), "Optical Sectioning"),
    (re.compile(r"\bdeconvolution\b", re.I), "Deconvolution"),
]

# Abbreviation patterns requiring IMMEDIATE microscopy context
_ABBREV_CONTEXT: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bSTED\s+(?:microscop\w+|imaging|nanoscop\w+)\b", re.I), "STED"),
    (re.compile(r"\bTEM\s+(?:microscop\w+|imaging|grid|section|analysis)\b", re.I), "TEM"),
    (re.compile(r"\bSEM\s+(?:microscop\w+|imaging|image\w*|analysis|micrograph)\b", re.I), "SEM"),
    (re.compile(r"\bSIM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "SIM"),
    (re.compile(r"\bSTORM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "STORM"),
    (re.compile(r"\bdSTORM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "dSTORM"),
    (re.compile(r"\bPALM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "PALM"),
    (re.compile(r"\bFLIM\s+(?:microscop\w+|imaging|image\w*|data|measurement)\b", re.I), "FLIM"),
    (re.compile(r"\bFRAP\s+(?:experiment\w*|assay|analysis|recovery|measurement)\b", re.I), "FRAP"),
    (re.compile(r"\bFRET\s+(?:experiment\w*|assay|measurement|efficiency|signal|pair|imaging|microscop\w+)\b", re.I), "FRET"),
    (re.compile(r"\bFCS\s+(?:measurement|experiment|data|curve|autocorrelation)\b", re.I), "FCS"),
    (re.compile(r"\bAFM\s+(?:microscop\w+|imaging|image\w*|measurement|cantilever|tip)\b", re.I), "AFM"),
    (re.compile(r"\bCLEM\s+(?:microscop\w+|imaging|workflow|approach)\b", re.I), "CLEM"),
    (re.compile(r"\bOCT\s+(?:imaging|image\w*|scan\w*|system)\b", re.I), "OCT"),
    (re.compile(r"\bTIRF\s+(?:microscop\w+|imaging|image\w*|illumination)\b", re.I), "TIRF"),
    (re.compile(r"\bFIB[- ]?SEM\b", re.I), "FIB-SEM"),
    (re.compile(r"\bcryo[- ]?EM\b", re.I), "Cryo-EM"),
    (re.compile(r"\bcryo[- ]?ET\b", re.I), "Cryo-ET"),
    (re.compile(r"\bSMLM\b", re.I), "SMLM"),
    (re.compile(r"\bSHG\s+(?:microscop\w+|imaging|signal)\b", re.I), "SHG"),
    (re.compile(r"\bCARS\s+(?:microscop\w+|imaging|signal|spectroscop\w+)\b", re.I), "CARS"),
    (re.compile(r"\bSRS\s+(?:microscop\w+|imaging|signal)\b", re.I), "SRS"),
    (re.compile(r"\bDIC\s+(?:microscop\w+|imaging|image\w*|optic\w*)\b", re.I), "DIC"),
    (re.compile(r"\bFLIP\s+(?:experiment|assay|imaging)\b", re.I), "FLIP"),
    (re.compile(r"\bconfocal\b", re.I), "Confocal"),
    (re.compile(r"\bCLSM\b"), "Confocal"),
    (re.compile(r"\bLSCM\b"), "Confocal"),
    (re.compile(r"\bspinning\s+dis[ck]\b", re.I), "Spinning Disk"),
    (re.compile(r"\blight[- ]?sheet\b", re.I), "Light Sheet"),
    (re.compile(r"\bLSFM\b"), "Light Sheet"),
    (re.compile(r"\bSPIM\b(?=\s*(?:microscop|imaging|system|setup))", re.I), "Light Sheet"),
    (re.compile(r"\bAiryscan\b", re.I), "Airyscan"),
    (re.compile(r"\bMesoSPIM\b", re.I), "MesoSPIM"),
    (re.compile(r"\bTIRFM\b", re.I), "TIRF"),
    (re.compile(r"\bFIBSEM\b", re.I), "FIB-SEM"),
    (re.compile(r"\bSBFSEM\b", re.I), "Serial Block-Face SEM"),
    (re.compile(r"\bSBF[- ]?SEM\b", re.I), "Serial Block-Face SEM"),
    (re.compile(r"\bcryoEM\b", re.I), "Cryo-EM"),
    (re.compile(r"\bcryoET\b", re.I), "Cryo-ET"),
    (re.compile(r"\bimmunoEM\b", re.I), "Immuno-EM"),
    (re.compile(r"\bExM\b", re.I), "Expansion Microscopy"),
    (re.compile(r"\bHCS\b(?=\s*(?:screen|imaging|system|assay|platform))", re.I), "High-Content Screening"),
    (re.compile(r"\bd[- ]?STORM\b"), "dSTORM"),
    (re.compile(r"\bholograph\w+\b", re.I), "Holographic"),
]


class TechniqueAgent(BaseAgent):
    """Extract microscopy technique mentions from text."""

    name = "technique"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []

        # 1. Full expansion patterns (high confidence)
        for pattern, canonical in _EXPANSION_PATTERNS:
            for m in pattern.finditer(text):
                results.append(Extraction(
                    text=m.group(0),
                    label="MICROSCOPY_TECHNIQUE",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.95,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        # 2. Abbreviation + context patterns
        for pattern, canonical in _ABBREV_CONTEXT:
            for m in pattern.finditer(text):
                conf = 0.85 if section in ("methods", "materials") else 0.7
                results.append(Extraction(
                    text=m.group(0),
                    label="MICROSCOPY_TECHNIQUE",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        return self._deduplicate(results)
