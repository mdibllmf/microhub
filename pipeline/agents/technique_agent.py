"""
Microscopy technique extraction agent.

Detects 60+ microscopy techniques using strict pattern matching.
Following v3.7 rules:
  - Abbreviations (STED, TEM, SIM, etc.) require IMMEDIATE microscopy context
    or their FULL expansion to avoid false positives.
  - Standalone abbreviations are NOT matched.
  - All canonical names use the FULL expanded form, never acronyms.
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
#
# All canonical names are FULL NAMES, never acronyms.
# ======================================================================

# Full expansion patterns -- always high confidence
_EXPANSION_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bstimulated\s+emission\s+depletion\b", re.I), "Stimulated Emission Depletion Microscopy"),
    (re.compile(r"\btransmission\s+electron\s+microscop\w*\b", re.I), "Transmission Electron Microscopy"),
    (re.compile(r"\bscanning\s+electron\s+microscop\w*\b", re.I), "Scanning Electron Microscopy"),
    (re.compile(r"\bstructured\s+illumination\s+microscop\w*\b", re.I), "Structured Illumination Microscopy"),
    (re.compile(r"\bstochastic\s+optical\s+reconstruction\s+microscop\w*\b", re.I), "Stochastic Optical Reconstruction Microscopy"),
    (re.compile(r"\bdirect\s+stochastic\s+optical\s+reconstruction\b", re.I), "Direct Stochastic Optical Reconstruction Microscopy"),
    (re.compile(r"\bphoto[- ]?activated\s+localization\s+microscop\w*\b", re.I), "Photoactivated Localization Microscopy"),
    (re.compile(r"\bsingle[- ]?molecule\s+localization\s+microscop\w*\b", re.I), "Single-Molecule Localization Microscopy"),
    (re.compile(r"\bfluorescence\s+lifetime\s+imaging\b", re.I), "Fluorescence Lifetime Imaging Microscopy"),
    (re.compile(r"\bfluorescence\s+recovery\s+after\s+photobleaching\b", re.I), "Fluorescence Recovery After Photobleaching"),
    (re.compile(r"\bf(?:o|ö)rster\s+resonance\s+energy\s+transfer\b", re.I), "Förster Resonance Energy Transfer"),
    (re.compile(r"\bfluorescence\s+resonance\s+energy\s+transfer\b", re.I), "Förster Resonance Energy Transfer"),
    (re.compile(r"\bfluorescence\s+correlation\s+spectroscop\w*\b", re.I), "Fluorescence Correlation Spectroscopy"),
    (re.compile(r"\bfluorescence\s+cross[- ]?correlation\s+spectroscop\w*\b", re.I), "Fluorescence Cross-Correlation Spectroscopy"),
    (re.compile(r"\bcoherent\s+anti[- ]?stokes\s+raman\b", re.I), "Coherent Anti-Stokes Raman Scattering"),
    (re.compile(r"\bstimulated\s+raman\s+scattering\b", re.I), "Stimulated Raman Scattering"),
    (re.compile(r"\bsecond\s+harmonic\s+generation\b", re.I), "Second Harmonic Generation"),
    (re.compile(r"\batomic\s+force\s+microscop\w*\b", re.I), "Atomic Force Microscopy"),
    (re.compile(r"\bcorrelative\s+light\s+(?:and\s+)?electron\s+microscop\w*\b", re.I), "Correlative Light and Electron Microscopy"),
    (re.compile(r"\boptical\s+coherence\s+tomograph\w*\b", re.I), "Optical Coherence Tomography"),
    (re.compile(r"\btotal\s+internal\s+reflection\s+fluorescen\w*\b", re.I), "Total Internal Reflection Fluorescence Microscopy"),
    (re.compile(r"\bfocused\s+ion\s+beam[- ]?scanning\s+electron\b", re.I), "Focused Ion Beam Scanning Electron Microscopy"),
    (re.compile(r"\bfluorescence\s+loss\s+in\s+photobleaching\b", re.I), "Fluorescence Loss in Photobleaching"),
    (re.compile(r"\bserial\s+block[- ]?face\s+(?:scanning\s+)?electron\b", re.I), "Serial Block-Face Scanning Electron Microscopy"),
    (re.compile(r"\blight[- ]?sheet\s+(?:fluorescence\s+)?microscop\w*\b", re.I), "Light Sheet Fluorescence Microscopy"),
    (re.compile(r"\blattice\s+light[- ]?sheet\b", re.I), "Lattice Light Sheet Microscopy"),
    (re.compile(r"\bselective\s+plane\s+illumination\s+microscop\w*\b", re.I), "Light Sheet Fluorescence Microscopy"),
    (re.compile(r"\bsuper[- ]?resolution\s+microscop\w*\b", re.I), "Super-Resolution Microscopy"),
    (re.compile(r"\bexpansion\s+microscop\w*\b", re.I), "Expansion Microscopy"),
    (re.compile(r"\bconfocal\s+(?:laser\s+scanning\s+)?microscop\w*\b", re.I), "Confocal Laser Scanning Microscopy"),
    (re.compile(r"\blaser\s+scanning\s+confocal\s+microscop\w*\b", re.I), "Confocal Laser Scanning Microscopy"),
    (re.compile(r"\bfluorescence\s+microscop\w*\b", re.I), "Fluorescence Microscopy"),
    (re.compile(r"\btwo[- ]?photon\s+(?:excitation\s+)?microscop\w*\b", re.I), "Two-Photon Excitation Microscopy"),
    (re.compile(r"\b2[- ]?photon\s+(?:excitation\s+)?microscop\w*\b", re.I), "Two-Photon Excitation Microscopy"),
    (re.compile(r"\bmultiphoton\s+microscop\w*\b", re.I), "Multiphoton Microscopy"),
    (re.compile(r"\bthree[- ]?photon\s+microscop\w*\b", re.I), "Three-Photon Microscopy"),
    (re.compile(r"\b3[- ]?photon\s+microscop\w*\b", re.I), "Three-Photon Microscopy"),
    (re.compile(r"\bspinning\s+dis[ck]\s+(?:confocal\s+)?microscop\w*\b", re.I), "Spinning Disk Confocal Microscopy"),
    (re.compile(r"\bwidefield\s+(?:fluorescence\s+)?microscop\w*\b", re.I), "Widefield Fluorescence Microscopy"),
    (re.compile(r"\bwide[- ]?field\s+(?:fluorescence\s+)?microscop\w*\b", re.I), "Widefield Fluorescence Microscopy"),
    (re.compile(r"\bepifluorescen\w+\s+microscop\w*\b", re.I), "Epifluorescence Microscopy"),
    (re.compile(r"\bepi[- ]?fluorescen\w+\s+microscop\w*\b", re.I), "Epifluorescence Microscopy"),
    (re.compile(r"\bbrightfield\s+microscop\w*\b", re.I), "Brightfield Microscopy"),
    (re.compile(r"\bbright[- ]?field\s+microscop\w*\b", re.I), "Brightfield Microscopy"),
    (re.compile(r"\bdark[- ]?field\s+microscop\w*\b", re.I), "Darkfield Microscopy"),
    (re.compile(r"\bphase[- ]?contrast\s+microscop\w*\b", re.I), "Phase Contrast Microscopy"),
    (re.compile(r"\bdifferential\s+interference\s+contrast\b", re.I), "Differential Interference Contrast Microscopy"),
    (re.compile(r"\bdarkfield\s+microscop\w*\b", re.I), "Darkfield Microscopy"),
    (re.compile(r"\bpolarization\s+microscop\w*\b", re.I), "Polarization Microscopy"),
    (re.compile(r"\bholographic\s+microscop\w*\b", re.I), "Holographic Microscopy"),
    (re.compile(r"\bphotoacoustic\s+microscop\w*\b", re.I), "Photoacoustic Microscopy"),
    (re.compile(r"\braman\s+microscop\w*\b", re.I), "Raman Microscopy"),
    (re.compile(r"\bintravital\s+(?:two[- ]?photon\s+)?microscop\w*\b", re.I), "Intravital Microscopy"),
    (re.compile(r"\bcalcium\s+imaging\b", re.I), "Calcium Imaging"),
    (re.compile(r"\bvoltage\s+imaging\b", re.I), "Voltage Imaging"),
    (re.compile(r"\blive[- ]?cell\s+imaging\b", re.I), "Live Cell Imaging"),
    (re.compile(r"\bhigh[- ]?content\s+screening\b", re.I), "High-Content Screening"),
    (re.compile(r"\boptogenetic\w*\b", re.I), "Optogenetics"),
    (re.compile(r"\belectron\s+tomograph\w*\b", re.I), "Electron Tomography"),
    (re.compile(r"\barray\s+tomograph\w*\b", re.I), "Array Tomography"),
    (re.compile(r"\bvolume\s+(?:electron\s+)?microscop\w*\b", re.I), "Volume Electron Microscopy"),
    (re.compile(r"\bcryo[- ]?electron\s+microscop\w*\b", re.I), "Cryo-Electron Microscopy"),
    (re.compile(r"\bcryo[- ]?electron\s+tomograph\w*\b", re.I), "Cryo-Electron Tomography"),
    (re.compile(r"\bnegative\s+stain(?:ing)?\s+(?:electron\s+)?microscop\w*\b", re.I), "Negative Stain Electron Microscopy"),
    (re.compile(r"\bimmuno[- ]?electron\s+microscop\w*\b", re.I), "Immuno-Electron Microscopy"),
    (re.compile(r"\bimmunofluorescen\w*\b", re.I), "Immunofluorescence Microscopy"),
    (re.compile(r"\bsingle[- ]?molecule\s+(?:fluorescence\s+)?imaging\b", re.I), "Single-Molecule Imaging"),
    (re.compile(r"\bsingle[- ]?particle\s+(?:cryo[- ]?em|analysis|reconstruction)\b", re.I), "Single-Particle Analysis"),
    (re.compile(r"\bDNA[- ]?PAINT\b"), "DNA Points Accumulation for Imaging in Nanoscale Topography"),
    (re.compile(r"\bpoints\s+accumulation\s+for\s+imaging\s+in\s+nanoscale\s+topography\b", re.I), "DNA Points Accumulation for Imaging in Nanoscale Topography"),
    (re.compile(r"\bMINFLUX\b"), "Minimal Photon Fluxes Microscopy"),
    (re.compile(r"\bminflux\s+nanoscop\w*\b", re.I), "Minimal Photon Fluxes Microscopy"),
    (re.compile(r"\bminimal\s+photon\s+flux\b", re.I), "Minimal Photon Fluxes Microscopy"),
    (re.compile(r"\bRESOLFT\b"), "Reversible Saturable Optical Fluorescence Transitions Microscopy"),
    (re.compile(r"\breversible\s+saturable\s+optical\s+fluorescence\s+transitions\b", re.I), "Reversible Saturable Optical Fluorescence Transitions Microscopy"),
    (re.compile(r"\bSOFI\b"), "Super-Resolution Optical Fluctuation Imaging"),
    (re.compile(r"\bsuper[- ]?resolution\s+optical\s+fluctuation\s+imaging\b", re.I), "Super-Resolution Optical Fluctuation Imaging"),
    (re.compile(r"\bnanoscopy\b", re.I), "Super-Resolution Microscopy"),
    (re.compile(r"\btime[- ]?lapse\s+(?:microscop\w*|imaging)\b", re.I), "Live Cell Imaging"),
    (re.compile(r"\btimelapse\s+(?:microscop\w*|imaging)\b", re.I), "Live Cell Imaging"),
    (re.compile(r"\bairyscan\s+(?:microscop\w*|imaging)\b", re.I), "Airyscan Microscopy"),
    (re.compile(r"\b3D\s+imaging\b", re.I), "3D Imaging"),
    (re.compile(r"\b4D\s+imaging\b", re.I), "4D Imaging"),
    (re.compile(r"\bZ[- ]?stack\w*\b", re.I), "Z-Stack Imaging"),
    (re.compile(r"\boptical\s+section\w*\b", re.I), "Optical Sectioning"),
    (re.compile(r"\bdeconvolution\b", re.I), "Deconvolution Microscopy"),
]

# Abbreviation patterns requiring IMMEDIATE microscopy context
_ABBREV_CONTEXT: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bSTED\s+(?:microscop\w+|imaging|nanoscop\w+)\b", re.I), "Stimulated Emission Depletion Microscopy"),
    (re.compile(r"\bTEM\s+(?:microscop\w+|imaging|grid|section|analysis)\b", re.I), "Transmission Electron Microscopy"),
    (re.compile(r"\bSEM\s+(?:microscop\w+|imaging|image\w*|analysis|micrograph)\b", re.I), "Scanning Electron Microscopy"),
    (re.compile(r"\bSIM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "Structured Illumination Microscopy"),
    (re.compile(r"\bSTORM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "Stochastic Optical Reconstruction Microscopy"),
    (re.compile(r"\bdSTORM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "Direct Stochastic Optical Reconstruction Microscopy"),
    (re.compile(r"\bPALM\s+(?:microscop\w+|imaging|image\w*)\b", re.I), "Photoactivated Localization Microscopy"),
    (re.compile(r"\bFLIM\s+(?:microscop\w+|imaging|image\w*|data|measurement)\b", re.I), "Fluorescence Lifetime Imaging Microscopy"),
    (re.compile(r"\bFRAP\s+(?:experiment\w*|assay|analysis|recovery|measurement)\b", re.I), "Fluorescence Recovery After Photobleaching"),
    (re.compile(r"\bFRET\s+(?:experiment\w*|assay|measurement|efficiency|signal|pair|imaging|microscop\w+)\b", re.I), "Förster Resonance Energy Transfer"),
    (re.compile(r"\bFCS\s+(?:measurement|experiment|data|curve|autocorrelation)\b", re.I), "Fluorescence Correlation Spectroscopy"),
    (re.compile(r"\bAFM\s+(?:microscop\w+|imaging|image\w*|measurement|cantilever|tip)\b", re.I), "Atomic Force Microscopy"),
    (re.compile(r"\bCLEM\s+(?:microscop\w+|imaging|workflow|approach)\b", re.I), "Correlative Light and Electron Microscopy"),
    (re.compile(r"\bOCT\s+(?:imaging|image\w*|scan\w*|system)\b", re.I), "Optical Coherence Tomography"),
    (re.compile(r"\bTIRF\s+(?:microscop\w+|imaging|image\w*|illumination)\b", re.I), "Total Internal Reflection Fluorescence Microscopy"),
    (re.compile(r"\bFIB[- ]?SEM\b", re.I), "Focused Ion Beam Scanning Electron Microscopy"),
    (re.compile(r"\bcryo[- ]?EM\b", re.I), "Cryo-Electron Microscopy"),
    (re.compile(r"\bcryo[- ]?ET\b", re.I), "Cryo-Electron Tomography"),
    (re.compile(r"\bSMLM\b", re.I), "Single-Molecule Localization Microscopy"),
    (re.compile(r"\bSHG\s+(?:microscop\w+|imaging|signal)\b", re.I), "Second Harmonic Generation"),
    (re.compile(r"\bCARS\s+(?:microscop\w+|imaging|signal|spectroscop\w+)\b", re.I), "Coherent Anti-Stokes Raman Scattering"),
    (re.compile(r"\bSRS\s+(?:microscop\w+|imaging|signal)\b", re.I), "Stimulated Raman Scattering"),
    (re.compile(r"\bDIC\s+(?:microscop\w+|imaging|image\w*|optic\w*)\b", re.I), "Differential Interference Contrast Microscopy"),
    (re.compile(r"\bFLIP\s+(?:experiment|assay|imaging)\b", re.I), "Fluorescence Loss in Photobleaching"),
    (re.compile(r"\bconfocal\b", re.I), "Confocal Laser Scanning Microscopy"),
    (re.compile(r"\bCLSM\b"), "Confocal Laser Scanning Microscopy"),
    (re.compile(r"\bLSCM\b"), "Confocal Laser Scanning Microscopy"),
    (re.compile(r"\bspinning\s+dis[ck]\b", re.I), "Spinning Disk Confocal Microscopy"),
    (re.compile(r"\blight[- ]?sheet\b", re.I), "Light Sheet Fluorescence Microscopy"),
    (re.compile(r"\bLSFM\b"), "Light Sheet Fluorescence Microscopy"),
    (re.compile(r"\bSPIM\b(?=\s*(?:microscop|imaging|system|setup))", re.I), "Light Sheet Fluorescence Microscopy"),
    (re.compile(r"\bAiryscan\b", re.I), "Airyscan Microscopy"),
    (re.compile(r"\bMesoSPIM\b", re.I), "MesoSPIM Light Sheet Microscopy"),
    (re.compile(r"\bTIRFM\b", re.I), "Total Internal Reflection Fluorescence Microscopy"),
    (re.compile(r"\bFIBSEM\b", re.I), "Focused Ion Beam Scanning Electron Microscopy"),
    (re.compile(r"\bSBFSEM\b", re.I), "Serial Block-Face Scanning Electron Microscopy"),
    (re.compile(r"\bSBF[- ]?SEM\b", re.I), "Serial Block-Face Scanning Electron Microscopy"),
    (re.compile(r"\bcryoEM\b", re.I), "Cryo-Electron Microscopy"),
    (re.compile(r"\bcryoET\b", re.I), "Cryo-Electron Tomography"),
    (re.compile(r"\bimmunoEM\b", re.I), "Immuno-Electron Microscopy"),
    (re.compile(r"\bExM\b", re.I), "Expansion Microscopy"),
    (re.compile(r"\bHCS\b(?=\s*(?:screen|imaging|system|assay|platform))", re.I), "High-Content Screening"),
    (re.compile(r"\bd[- ]?STORM\b"), "Direct Stochastic Optical Reconstruction Microscopy"),
    (re.compile(r"\bholograph\w+\b", re.I), "Holographic Microscopy"),
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
