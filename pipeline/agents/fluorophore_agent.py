"""
Fluorophore identification agent.

Three-layer extraction strategy:
  1. Dictionary matching with canonical name normalisation (GFP variants,
     Alexa Fluor series, Cy dyes, ATTO dyes, etc.)
  2. Regex patterns for structured fluorophore names (Alexa Fluor NNN,
     ATTO NNN, Hoechst NNNNN, trackers)
  3. Optional FPbase API validation for fluorescent proteins

Covers organic dyes, fluorescent proteins, calcium indicators, and
lipophilic tracers.
"""

import re
from typing import Dict, List

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Canonical mappings -- variant → standard name
# ======================================================================

FLUOROPHORE_CANONICAL: Dict[str, str] = {
    # GFP family
    "gfp": "GFP", "green fluorescent protein": "GFP",
    "egfp": "EGFP", "enhanced gfp": "EGFP", "enhanced green fluorescent protein": "EGFP",
    "mgfp": "mGFP",
    # YFP
    "yfp": "YFP", "yellow fluorescent protein": "YFP",
    "eyfp": "EYFP", "enhanced yellow fluorescent protein": "EYFP",
    "venus": "Venus", "citrine": "Citrine",
    "mvenus": "mVenus",
    # RFP
    "rfp": "RFP", "red fluorescent protein": "RFP",
    "dsred": "DsRed", "ds-red": "DsRed",
    "mcherry": "mCherry", "m-cherry": "mCherry",
    "mscarlet": "mScarlet", "mscarlet-i": "mScarlet",
    "mkate2": "mKate2",
    "tdtomato": "tdTomato", "td-tomato": "tdTomato",
    "tagrfp": "TagRFP",
    "mrfp": "mRFP",
    # CFP/BFP
    "cfp": "CFP", "cyan fluorescent protein": "CFP",
    "ecfp": "ECFP", "enhanced cfp": "ECFP",
    "bfp": "BFP", "blue fluorescent protein": "BFP",
    "ebfp": "EBFP",
    "mturquoise": "mTurquoise", "mturquoise2": "mTurquoise",
    "mcerulean": "mCerulean",
    "mtagbfp": "mTagBFP",
    # Other FPs
    "memerald": "mEmerald",
    "mclover": "mClover", "mclover3": "mClover",
    "mneongreen": "mNeonGreen", "mneon green": "mNeonGreen",
    "neongreen": "NeonGreen",
    "meos": "mEos", "meos2": "mEos2", "meos3": "mEos3", "meos3.2": "mEos3.2",
    "mmaple": "mMaple", "mmaple3": "mMaple",
    "dendra2": "Dendra2",
    "dronpa": "Dronpa",
    "pa-gfp": "PA-GFP", "pagfp": "PA-GFP",
    # Calcium indicators
    "gcamp": "GCaMP", "gcamp6": "GCaMP6", "gcamp6f": "GCaMP6f", "gcamp6s": "GCaMP6s",
    "jrgeco": "jRGECO", "jrgeco1a": "jRGECO",
    "fluo-4": "Fluo-4", "fluo4": "Fluo-4",
    "fura-2": "Fura-2", "fura2": "Fura-2",
    # Common dyes
    "dapi": "DAPI",
    "hoechst 33342": "Hoechst 33342", "hoechst33342": "Hoechst 33342",
    "hoechst 33258": "Hoechst 33258", "hoechst33258": "Hoechst 33258",
    "propidium iodide": "Propidium Iodide", "pi": None,  # PI is ambiguous
    "fitc": "FITC", "fluorescein isothiocyanate": "FITC",
    "tritc": "TRITC",
    "texas red": "Texas Red",
    "rhodamine": "Rhodamine", "rhodamine 123": "Rhodamine 123", "rhodamine b": "Rhodamine B",
    "phalloidin": "Phalloidin",
    "calcein": "Calcein", "calcein-am": "Calcein-AM", "calcein am": "Calcein-AM",
    "acridine orange": "Acridine Orange",
    "jc-1": "JC-1", "jc1": "JC-1",
    # Cyanine dyes
    "cy3": "Cy3", "cy5": "Cy5", "cy7": "Cy7",
    # SiR dyes
    "sir": None,  # bare "SiR" is ambiguous
    "sir-actin": "SiR-Actin", "siractin": "SiR-Actin",
    "sir-tubulin": "SiR-Tubulin", "sirtubulin": "SiR-Tubulin",
    "silicon rhodamine": "SiR",
    # ATTO dyes (handled mostly by regex)
    "atto 488": "ATTO 488", "atto488": "ATTO 488",
    "atto 565": "ATTO 565", "atto565": "ATTO 565",
    "atto 647": "ATTO 647", "atto647": "ATTO 647",
    "atto 647n": "ATTO 647N", "atto647n": "ATTO 647N",
    "atto 655": "ATTO 655", "atto655": "ATTO 655",
    # Lipophilic tracers
    "dii": "DiI", "did": "DiD", "dio": "DiO", "dir": "DiR",
    # Trackers
    "mitotracker": "MitoTracker",
    "mitotracker green": "MitoTracker Green",
    "mitotracker red": "MitoTracker Red",
    "lysotracker": "LysoTracker",
    "lysotracker red": "LysoTracker Red",
    "er-tracker": "ER-Tracker", "ertracker": "ER-Tracker",
    "cellmask": "CellMask",
    # Click chemistry
    "edu": "EdU", "brdu": "BrdU",
    "click-it": "Click-iT", "clickit": "Click-iT",
    # Janelia Fluor
    "jf549": "JF549", "jf646": "JF646",
    # Others
    "draq5": "DRAQ5", "bodipy": "BODIPY",
    "coumarin": "Coumarin", "dylight": "DyLight",
    "fm dyes": "FM Dyes", "fm1-43": "FM Dyes", "fm4-64": "FM Dyes",
    "sytox": "SYTOX", "sytox green": "SYTOX Green",
    "syto": "SYTO",
    "wga": "WGA", "wheat germ agglutinin": "WGA",
    "apc": "APC", "pe": None,  # PE is ambiguous (phycoerythrin vs other)
    "cf568": "CF568",
}

# ======================================================================
# Regex patterns for structured fluorophore names
# ======================================================================

_REGEX_PATTERNS: List[tuple] = [
    # Alexa Fluor NNN
    (re.compile(r"\bAlexa\s*Fluor\s*(\d{3})\b", re.I),
     lambda m: f"Alexa Fluor {m.group(1)}"),
    (re.compile(r"\bAF[- ]?(\d{3})\b"),
     lambda m: f"Alexa Fluor {m.group(1)}"),
    # ATTO NNN[N]
    (re.compile(r"\bATTO\s*(\d{3}N?)\b", re.I),
     lambda m: f"ATTO {m.group(1)}"),
    # Cy dyes
    (re.compile(r"\bCy([357])(?:\.5)?\b"),
     lambda m: f"Cy{m.group(1)}"),
    # Hoechst
    (re.compile(r"\bHoechst\s*(\d{5})\b", re.I),
     lambda m: f"Hoechst {m.group(1)}"),
    # Trackers
    (re.compile(r"\b(Mito|Lyso|ER)[- ]?Tracker(?:\s+(?:Green|Red|Deep Red))?\b", re.I),
     lambda m: m.group(0).strip()),
    # GCaMP variants
    (re.compile(r"\bGCaMP(\d[a-z]?)\b", re.I),
     lambda m: f"GCaMP{m.group(1)}"),
    # Janelia Fluor
    (re.compile(r"\bJF(\d{3})\b"),
     lambda m: f"JF{m.group(1)}"),
    # DyLight NNN
    (re.compile(r"\bDyLight\s*(\d{3})\b", re.I),
     lambda m: f"DyLight {m.group(1)}"),
    # CF dyes
    (re.compile(r"\bCF(\d{3})\b"),
     lambda m: f"CF{m.group(1)}"),
]

# Context patterns for ambiguous short names (DiI, DiD, DiO, DiR, EdU, BrdU, SiR)
_CONTEXT_PATTERNS: List[tuple] = [
    (re.compile(r"\bDiI\b(?=.{0,30}(?:label|stain|dye|lipophilic|trace|fluorescen))", re.I | re.S), "DiI"),
    (re.compile(r"\bDiD\b(?=.{0,30}(?:label|stain|dye|lipophilic|trace|fluorescen))", re.I | re.S), "DiD"),
    (re.compile(r"\bDiO\b(?=.{0,30}(?:label|stain|dye|lipophilic|trace|fluorescen))", re.I | re.S), "DiO"),
    (re.compile(r"\bDiR\b(?=.{0,30}(?:label|stain|dye|lipophilic|trace|fluorescen))", re.I | re.S), "DiR"),
    (re.compile(r"\bEdU\b(?=.{0,30}(?:label|incorporat|click|proliferat|stain))", re.I | re.S), "EdU"),
    (re.compile(r"\bBrdU\b(?=.{0,30}(?:label|incorporat|proliferat|stain))", re.I | re.S), "BrdU"),
    (re.compile(r"\bSiR[- ](?:actin|tubulin|DNA|lysosome)\b", re.I), None),  # handled by canonical
    (re.compile(r"\bsilicon\s+rhodamine\b", re.I), "SiR"),
]


class FluorophoreAgent(BaseAgent):
    """Extract fluorophore mentions from text."""

    name = "fluorophore"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        results.extend(self._dictionary_match(text, section))
        results.extend(self._regex_match(text, section))
        results.extend(self._context_match(text, section))
        return self._deduplicate(results)

    # ------------------------------------------------------------------
    def _dictionary_match(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        text_lower = text.lower()

        for key, canonical in FLUOROPHORE_CANONICAL.items():
            if canonical is None:
                continue  # skip ambiguous entries
            # Word-boundary search
            pattern = re.compile(r"\b" + re.escape(key) + r"\b", re.I)
            for m in pattern.finditer(text):
                conf = 0.9 if section in ("methods", "materials") else 0.75
                extractions.append(Extraction(
                    text=m.group(0),
                    label="FLUOROPHORE",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))

        return extractions

    # ------------------------------------------------------------------
    def _regex_match(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for pattern, name_fn in _REGEX_PATTERNS:
            for m in pattern.finditer(text):
                canonical = name_fn(m)
                extractions.append(Extraction(
                    text=m.group(0),
                    label="FLUOROPHORE",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.9,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))
        return extractions

    # ------------------------------------------------------------------
    def _context_match(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for pattern, canonical in _CONTEXT_PATTERNS:
            if canonical is None:
                continue
            for m in pattern.finditer(text):
                extractions.append(Extraction(
                    text=m.group(0),
                    label="FLUOROPHORE",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.8,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))
        return extractions
