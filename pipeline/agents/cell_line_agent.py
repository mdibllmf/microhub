"""
Cell line identification agent.

Detects common cell lines used in microscopy research, including
immortalised lines, primary cultures, and stem cells.

All canonical names use the FULL expanded form, never acronyms.
"""

import re
from typing import Dict, List

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Cell line patterns → canonical full names (no acronyms)
# ======================================================================

CELL_LINE_PATTERNS: Dict[str, tuple] = {
    "HeLa (Henrietta Lacks)": (re.compile(r"\bHeLa\b"), 0.95),
    "Human Embryonic Kidney 293": (re.compile(r"\bHEK[- ]?293(?!T)\b", re.I), 0.95),
    "Human Embryonic Kidney 293T": (re.compile(r"\b(?:HEK[- ]?)?293\s*T\b", re.I), 0.95),
    "Human Osteosarcoma U2OS": (re.compile(r"\bU[- ]?2[- ]?\s*OS\b", re.I), 0.95),
    "African Green Monkey Kidney COS-7": (re.compile(r"\bCOS[- ]?7\b", re.I), 0.95),
    "Human Lung Adenocarcinoma A549": (re.compile(r"\bA549\b"), 0.95),
    "Human Breast Adenocarcinoma MCF-7": (re.compile(r"\bMCF[- ]?7\b", re.I), 0.95),
    "NIH 3T3 Mouse Fibroblast": (re.compile(r"\b(?:NIH[- ]?)?3T3\b(?=\s*(?:cell|line|fibroblas|cultur))?", re.I), 0.9),
    "Chinese Hamster Ovary": (re.compile(r"\bCHO\b(?=\s*(?:cell|line|K1|DG44))", re.I), 0.85),
    "Madin-Darby Canine Kidney": (re.compile(r"\bMDCK\b"), 0.95),
    "Vero (African Green Monkey Kidney)": (re.compile(r"\bVero\b(?=\s*(?:cell|line|E6))", re.I), 0.85),
    "Human Neuroblastoma SH-SY5Y": (re.compile(r"\bSH[- ]?SY5Y\b", re.I), 0.95),
    "Rat Pheochromocytoma PC-12": (re.compile(r"\bPC[- ]?12\b"), 0.9),
    "Mouse Embryonic Fibroblast": (re.compile(r"\b(?:MEFs?\b(?=.{0,20}(?:cell|fibroblas|cultur|embry))|mouse\s+embryonic\s+fibroblast\w*)\b", re.I | re.S), 0.8),
    "Induced Pluripotent Stem Cell": (re.compile(r"\b(?:iPSC\w*|induced\s+pluripotent\s+stem\s+cell\w*)\b", re.I), 0.9),
    "Embryonic Stem Cell": (re.compile(r"\b(?:ESC|embryonic\s+stem\s+cell)\w*\b", re.I), 0.85),
    "Primary Neurons": (re.compile(r"\b(?:primary\s+(?:cortical\s+|hippocampal\s+)?neuron\w*|cultured\s+neuron\w*)\b", re.I), 0.85),
    "Primary Cardiomyocytes": (re.compile(r"\bprimary\s+cardiomyocyte\w*\b", re.I), 0.9),
    "Primary Hepatocytes": (re.compile(r"\bprimary\s+hepatocyte\w*\b", re.I), 0.9),
}


class CellLineAgent(BaseAgent):
    """Extract cell line mentions from text."""

    name = "cell_line"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        for canonical, (pattern, base_conf) in CELL_LINE_PATTERNS.items():
            for m in pattern.finditer(text):
                conf = base_conf
                if section in ("methods", "materials"):
                    conf = min(conf + 0.05, 1.0)
                results.append(Extraction(
                    text=m.group(0),
                    label="CELL_LINE",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))
        return self._deduplicate(results)
