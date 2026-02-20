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
    # === EXISTING IMMORTALIZED LINES ===
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

    # === NEW IMMORTALIZED LINES ===
    "Human T-cell Leukemia Jurkat": (re.compile(r"\bJurkat\b"), 0.95),
    "Human Chronic Myelogenous Leukemia K562": (re.compile(r"\bK[- ]?562\b"), 0.95),
    "Human Hepatocellular Carcinoma HepG2": (re.compile(r"\bHep\s*G[- ]?2\b", re.I), 0.95),
    "Human Colorectal Adenocarcinoma Caco-2": (re.compile(r"\bCaco[- ]?2\b", re.I), 0.95),
    "Human Umbilical Vein Endothelial Cell": (re.compile(r"\bHUVEC\w*\b"), 0.95),
    "Human Colorectal Adenocarcinoma HT-29": (re.compile(r"\bHT[- ]?29\b"), 0.95),
    "Human Colorectal Carcinoma HCT116": (re.compile(r"\bHCT[- ]?116\b"), 0.95),
    "Human Breast Adenocarcinoma MDA-MB-231": (re.compile(r"\bMDA[- ]?MB[- ]?231\b", re.I), 0.95),
    "Human Acute Monocytic Leukemia THP-1": (re.compile(r"\bTHP[- ]?1\b"), 0.95),
    "Human Promyelocytic Leukemia HL-60": (re.compile(r"\bHL[- ]?60\b"), 0.95),
    "Mouse Neuroblastoma Neuro-2a": (re.compile(r"\b(?:Neuro[- ]?2[Aa]|N2[Aa])\b"), 0.95),
    "Mouse Myoblast C2C12": (re.compile(r"\bC2C12\b"), 0.95),
    "Mouse Fibroblast L929": (re.compile(r"\bL[- ]?929\b"), 0.95),
    "Baby Hamster Kidney BHK-21": (re.compile(r"\bBHK[- ]?21\b"), 0.95),
    "Human Colorectal Adenocarcinoma DLD-1": (re.compile(r"\bDLD[- ]?1\b"), 0.95),
    "Human Colorectal Adenocarcinoma SW480": (re.compile(r"\bSW[- ]?480\b"), 0.95),
    "Human Breast Carcinoma SK-BR-3": (re.compile(r"\bSK[- ]?BR[- ]?3\b", re.I), 0.95),
    "Human Pancreatic Carcinoma PANC-1": (re.compile(r"\bPANC[- ]?1\b"), 0.95),
    "Human Mammary Epithelial MCF-10A": (re.compile(r"\bMCF[- ]?10A\b", re.I), 0.95),
    "Human Fetal Lung Fibroblast IMR-90": (re.compile(r"\bIMR[- ]?90\b"), 0.95),
    "Human Fetal Lung Fibroblast WI-38": (re.compile(r"\bWI[- ]?38\b"), 0.95),
    "Human Foreskin Fibroblast BJ": (re.compile(r"\bBJ\b(?=\s*(?:cell|fibroblas|human|line|cultur))", re.I), 0.80),
    "Mouse Mammary Carcinoma 4T1": (re.compile(r"\b4T1\b"), 0.95),
    "Mouse Lewis Lung Carcinoma LLC": (re.compile(r"\bLLC\b(?=\s*(?:cell|tumor|lung))", re.I), 0.80),
    "Mouse Melanoma B16": (re.compile(r"\bB16(?:[- ]?F10)?\b"), 0.90),
    "Mouse Colon Carcinoma CT26": (re.compile(r"\bCT[- ]?26\b"), 0.95),
    "Mouse Macrophage RAW 264.7": (re.compile(r"\bRAW\s*264\.?7\b", re.I), 0.95),
    "Human Cervical Carcinoma SiHa": (re.compile(r"\bSiHa\b"), 0.95),
    "Human Retinal Pigment Epithelium ARPE-19": (re.compile(r"\bARPE[- ]?19\b"), 0.95),
    "Human Embryonic Kidney Lenti-X 293T": (re.compile(r"\bLenti[- ]?X\s*293\s*T\b", re.I), 0.95),
    "Rat Glioma C6": (re.compile(r"\bC6\b(?=\s*(?:cell|glioma|rat|line))", re.I), 0.80),
    "Dog Kidney MDCK-II": (re.compile(r"\bMDCK[- ]?II\b"), 0.95),
    "Human Prostate Cancer PC-3": (re.compile(r"\bPC[- ]?3\b(?=\s*(?:cell|prostat|line))?"), 0.90),
    "Human Prostate Cancer LNCaP": (re.compile(r"\bLNCaP\b", re.I), 0.95),
    "Human Glioblastoma U-87 MG": (re.compile(r"\bU[- ]?87\s*MG?\b", re.I), 0.95),
    "Human Glioblastoma U-251 MG": (re.compile(r"\bU[- ]?251\s*MG?\b", re.I), 0.95),
    "Human Non-Small Cell Lung Cancer NCI-H460": (re.compile(r"\bNCI[- ]?H460\b"), 0.95),
    "Human T Lymphoblast CCRF-CEM": (re.compile(r"\bCCRF[- ]?CEM\b"), 0.95),

    # === NEW PRIMARY CELL TYPES ===
    "Primary T Cells": (re.compile(r"\b(?:primary\s+)?(?:CD[48]\+?\s+)?T[- ]?cell\w*\b", re.I), 0.80),
    "Primary B Cells": (re.compile(r"\b(?:primary\s+)?B[- ]?cell\w*\b(?=.{0,30}(?:sort|isol|cultur|purif|stimulat|activ))", re.I | re.S), 0.75),
    "Primary Natural Killer Cells": (re.compile(r"\b(?:primary\s+)?(?:NK|natural\s+killer)\s*cell\w*\b", re.I), 0.85),
    "Primary Macrophages": (re.compile(r"\b(?:primary\s+)?(?:bone\s+marrow[- ]derived\s+)?macrophage\w*\b", re.I), 0.85),
    "Primary Dendritic Cells": (re.compile(r"\b(?:primary\s+)?(?:bone\s+marrow[- ]derived\s+)?dendritic\s+cell\w*\b", re.I), 0.85),
    "Primary Neutrophils": (re.compile(r"\b(?:primary\s+)?neutrophil\w*\b", re.I), 0.85),
    "Primary Fibroblasts": (re.compile(r"\b(?:primary\s+)?(?:dermal\s+|skin\s+|cardiac\s+|lung\s+)?fibroblast\w*\b(?!.*(?:NIH|3T3|MEF|L929|IMR|WI-38|BJ))", re.I), 0.75),
    "Primary Keratinocytes": (re.compile(r"\b(?:primary\s+)?keratinocyte\w*\b", re.I), 0.85),
    "Primary Endothelial Cells": (re.compile(r"\b(?:primary\s+)?(?:vascular\s+|pulmonary\s+|brain\s+)?endothelial\s+cell\w*\b(?!.*HUVEC)", re.I), 0.80),
    "Primary Astrocytes": (re.compile(r"\b(?:primary\s+)?astrocyte\w*\b", re.I), 0.85),
    "Primary Microglia": (re.compile(r"\b(?:primary\s+)?microglia\w*\b", re.I), 0.90),
    "Primary Oligodendrocytes": (re.compile(r"\b(?:primary\s+)?oligodendrocyte\w*\b", re.I), 0.85),
    "Primary Epithelial Cells": (re.compile(r"\b(?:primary\s+)?(?:bronchial\s+|mammary\s+|renal\s+|intestinal\s+)?epithelial\s+cell\w*\b", re.I), 0.75),
    "Primary Mesenchymal Stem Cells": (re.compile(r"\b(?:MSC\w*\b(?=.{0,20}(?:cell|mesenchym|stem|stromal|bone))|mesenchymal\s+(?:stem|stromal)\s+cell\w*)\b", re.I | re.S), 0.85),
    "Neural Stem Cells": (re.compile(r"\b(?:NSC\w*\b(?=.{0,20}(?:cell|neural|stem|neuro))|neural\s+(?:stem|progenitor)\s+cell\w*)\b", re.I | re.S), 0.85),
    "Hematopoietic Stem Cells": (re.compile(r"\b(?:HSC\w*\b(?=.{0,20}(?:cell|hematop|stem|bone\s*marrow))|hematopoietic\s+stem\s+cell\w*)\b", re.I | re.S), 0.85),
    "Primary Monocytes": (re.compile(r"\b(?:primary\s+)?monocyte\w*\b", re.I), 0.85),
    "Primary Osteoblasts": (re.compile(r"\b(?:primary\s+)?osteoblast\w*\b", re.I), 0.85),
    "Primary Osteoclasts": (re.compile(r"\b(?:primary\s+)?osteoclast\w*\b", re.I), 0.85),
    "Primary Chondrocytes": (re.compile(r"\b(?:primary\s+)?chondrocyte\w*\b", re.I), 0.85),
    "Primary Podocytes": (re.compile(r"\b(?:primary\s+)?podocyte\w*\b", re.I), 0.90),
    "Primary Schwann Cells": (re.compile(r"\b(?:primary\s+)?[Ss]chwann\s+cell\w*\b", re.I), 0.90),
    "Primary Muscle Satellite Cells": (re.compile(r"\b(?:primary\s+)?(?:muscle\s+)?satellite\s+cell\w*\b", re.I), 0.85),
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
