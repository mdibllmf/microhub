"""
Sample preparation method extraction agent.

Detects fixation methods, tissue clearing techniques, embedding,
staining/labeling methods, cell culture, and other preparation
techniques from microscopy papers.
"""

import re
from typing import Dict, List

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Sample preparation patterns → canonical names
# ======================================================================

SAMPLE_PREP_PATTERNS: Dict[str, tuple] = {
    # Fixation
    "Fixation": (re.compile(r"\b(?:fix(?:ed|ation|ative)|(?:4%?\s*)?paraformaldehyde|(?:4%?\s*)?PFA)\b", re.I), 0.8),
    "PFA Fixation": (re.compile(r"\b(?:(?:4%?\s*)?PFA\s+fix|paraformaldehyde\s+fix|(?:4%?\s*)?PFA\b)", re.I), 0.85),
    "Methanol Fixation": (re.compile(r"\b(?:methanol\s+fix|ice[- ]?cold\s+methanol|MeOH\s+fix)\b", re.I), 0.85),
    "Glutaraldehyde": (re.compile(r"\bglutaraldehyde\b", re.I), 0.9),

    # Tissue clearing
    # CLARITY requires tissue-clearing context to avoid matching the common
    # English word (e.g. "with greater clarity").  Must appear near clearing-
    # related terms or be explicitly described as a protocol/method.
    "CLARITY": (re.compile(
        r"\bCLARITY\b(?=.{0,60}(?:clear|tissue|brain|organ|hydrogel|protocol|method|label|immunostain|mouse|sample|intact|transparen))"
        r"|(?:clear|tissue|brain|organ|hydrogel|protocol|method|transparen)\w*.{0,60}\bCLARITY\b"
        r"|\bCLARITY[- ]?(?:protocol|method|clearing|based|optimized|compatible)\b"
        r"|\b(?:modified|optimized|adapted)\s+CLARITY\b"
        r"|\bCLARITY\s+SPIM\b",
        re.I | re.S,
    ), 0.95),
    "CUBIC": (re.compile(r"\bCUBIC\b"), 0.9),
    "iDISCO": (re.compile(r"\biDISCO\+?\b"), 0.95),
    "3DISCO": (re.compile(r"\b3DISCO\b"), 0.95),
    "uDISCO": (re.compile(r"\buDISCO\b"), 0.95),
    "SHIELD": (re.compile(r"\bSHIELD\b(?=.{0,50}(?:clear|tissue|brain|protocol))", re.I | re.S), 0.85),
    "Tissue Clearing": (re.compile(r"\b(?:tissue|optical)\s+clearing\b", re.I), 0.9),
    "PACT": (re.compile(r"\bPACT\b(?=.{0,30}(?:clear|tissue|brain|protocol))", re.I | re.S), 0.85),
    "PEGASOS": (re.compile(r"\bPEGASOS\b", re.I), 0.95),
    "eFLASH": (re.compile(r"\beFLASH\b"), 0.95),

    # Embedding & sectioning
    "OCT Embedding": (re.compile(r"\bOCT\s+(?:embed|compound|medium|block)\b", re.I), 0.85),
    "Paraffin Embedding": (re.compile(r"\bparaffin\s+(?:embed|section|block)\b", re.I), 0.85),
    "Cryosectioning": (re.compile(r"\b(?:cryosection|cryostat|cryo[- ]?section)\b", re.I), 0.9),
    "Vibratome": (re.compile(r"\bvibratome\b", re.I), 0.9),
    "Microtome": (re.compile(r"\bmicrotome\b", re.I), 0.9),
    "Ultramicrotome": (re.compile(r"\b(?:ultramicrotome|ultra[- ]?thin\s+section)\b", re.I), 0.9),

    # Staining / labeling
    "Immunostaining": (re.compile(r"\b(?:immunostain|immuno[- ]?stain)\w*\b", re.I), 0.9),
    "Immunofluorescence": (re.compile(r"\b(?:immunofluorescen\w*|IF\s+staining)\b", re.I), 0.9),
    "Immunohistochemistry": (re.compile(r"\b(?:immunohistochemist\w*|IHC)\b", re.I), 0.85),
    "H&E": (re.compile(r"\b(?:H\s*&\s*E|hematoxylin\s+(?:and\s+)?eosin)\b", re.I), 0.9),
    "FISH": (re.compile(r"\b(?:fluorescen\w+\s+in\s+situ\s+hybridi[sz]\w+|FISH\s+(?:experiment|probe|signal|stain|label))\b", re.I), 0.85),
    "smFISH": (re.compile(r"\bsmFISH\b"), 0.95),
    "RNAscope": (re.compile(r"\bRNAscope\b", re.I), 0.95),
    "MERFISH": (re.compile(r"\bMERFISH\b", re.I), 0.95),
    "seqFISH": (re.compile(r"\bseqFISH\b", re.I), 0.95),
    "In Situ Hybridization": (re.compile(r"\bin\s+situ\s+hybridi[sz]\w+\b", re.I), 0.85),
    "TUNEL": (re.compile(r"\bTUNEL\b"), 0.9),

    # Cell handling
    "Cell Culture": (re.compile(r"\bcell\s+cultur\w*\b", re.I), 0.8),
    "Primary Culture": (re.compile(r"\bprimary\s+(?:cell\s+)?cultur\w*\b", re.I), 0.85),
    "Transfection": (re.compile(r"\btransfect\w+\b", re.I), 0.85),
    "Transduction": (re.compile(r"\btransduc\w+\b", re.I), 0.8),
    "Lipofection": (re.compile(r"\b(?:lipofect\w+|lipofectamine)\b", re.I), 0.9),
    "Electroporation": (re.compile(r"\belectroporat\w+\b", re.I), 0.9),
    "Lentiviral": (re.compile(r"\blentivir\w+\b", re.I), 0.85),
    "Adenoviral": (re.compile(r"\badenovir\w+\b", re.I), 0.85),
    "AAV": (re.compile(r"\b(?:AAV\d*|adeno[- ]?associated\s+virus)\b", re.I), 0.85),
    "CRISPR": (re.compile(r"\bCRISPR\b"), 0.9),
    "Knockdown": (re.compile(r"\b(?:knockdown|knock[- ]?down|siRNA|shRNA)\b", re.I), 0.85),
    "Knockout": (re.compile(r"\b(?:knockout|knock[- ]?out)\b", re.I), 0.85),
    "Live Imaging": (re.compile(r"\blive[- ]?(?:cell\s+)?imaging\b", re.I), 0.85),

    # Mounting & preparation
    "Permeabilization": (re.compile(r"\bpermeabili[sz]\w+\b", re.I), 0.85),
    "Blocking": (re.compile(r"\bblock(?:ing)?\s+(?:buffer|solution|step|with)\b", re.I), 0.7),
    "Antigen Retrieval": (re.compile(r"\bantigen\s+retrieval\b", re.I), 0.9),
    "Whole Mount": (re.compile(r"\bwhole[- ]?mount\b", re.I), 0.85),
    "Flat Mount": (re.compile(r"\bflat[- ]?mount\b", re.I), 0.85),
    "Monolayer": (re.compile(r"\bmonolayer\b", re.I), 0.7),

    # 3D cultures — specific organoid/spheroid types
    "Brain Organoid": (re.compile(r"\b(?:brain|cerebral)\s+organoid\w*\b", re.I), 0.95),
    "Kidney Organoid": (re.compile(r"\b(?:kidney|renal)\s+organoid\w*\b", re.I), 0.95),
    "Intestinal Organoid": (re.compile(r"\b(?:intestin\w*|gut|colon|colonic)\s+organoid\w*\b", re.I), 0.95),
    "Liver Organoid": (re.compile(r"\b(?:liver|hepatic)\s+organoid\w*\b", re.I), 0.95),
    "Lung Organoid": (re.compile(r"\b(?:lung|pulmonary|airway)\s+organoid\w*\b", re.I), 0.95),
    "Cardiac Organoid": (re.compile(r"\b(?:cardiac|heart)\s+organoid\w*\b", re.I), 0.95),
    "Retinal Organoid": (re.compile(r"\b(?:retinal|retina)\s+organoid\w*\b", re.I), 0.95),
    "Tumor Organoid": (re.compile(r"\b(?:tumor|tumour|cancer)\s+organoid\w*\b", re.I), 0.95),
    "Pancreatic Organoid": (re.compile(r"\bpancreat\w+\s+organoid\w*\b", re.I), 0.95),
    "Prostate Organoid": (re.compile(r"\bprostat\w+\s+organoid\w*\b", re.I), 0.95),
    "Mammary Organoid": (re.compile(r"\b(?:mammary|breast)\s+organoid\w*\b", re.I), 0.95),
    "Gastric Organoid": (re.compile(r"\b(?:gastric|stomach)\s+organoid\w*\b", re.I), 0.95),
    # Generic organoid/spheroid (catch-all for untyped mentions)
    "Organoid": (re.compile(r"\borganoid\w*\b", re.I), 0.9),
    "Tumor Spheroid": (re.compile(r"\b(?:tumor|tumour|cancer)\s+spheroid\w*\b", re.I), 0.95),
    "Spheroid": (re.compile(r"\bspheroid\w*\b", re.I), 0.9),
    "3D Culture": (re.compile(r"\b3D\s+(?:cell\s+)?cultur\w*\b", re.I), 0.85),
    "Co-culture": (re.compile(r"\bco[- ]?cultur\w*\b", re.I), 0.85),

    # Expansion microscopy (both technique and prep)
    "Expansion Microscopy": (re.compile(r"\bexpansion\s+microscop\w*\b", re.I), 0.9),
}


# Negative context for CLARITY — disqualify matches that are
# the common English word, not the tissue-clearing protocol
_CLARITY_NEGATIVE = re.compile(
    r"(?:for|with|of|improved?|greater|more|less|optical|visual|provide|"
    r"ensure|enhance|image|spatial|lack(?:s|ing)?)\s+clarity",
    re.I,
)


class SamplePrepAgent(BaseAgent):
    """Extract sample preparation methods from text."""

    name = "sample_prep"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        for canonical, (pattern, base_conf) in SAMPLE_PREP_PATTERNS.items():
            for m in pattern.finditer(text):
                # Extra check for CLARITY: reject if the surrounding text
                # is using the common English word, not the protocol
                if canonical == "CLARITY":
                    start = max(0, m.start() - 30)
                    context = text[start:m.end() + 20]
                    if _CLARITY_NEGATIVE.search(context):
                        continue

                conf = base_conf
                if section in ("methods", "materials"):
                    conf = min(conf + 0.1, 1.0)
                results.append(Extraction(
                    text=m.group(0),
                    label="SAMPLE_PREPARATION",
                    start=m.start(),
                    end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))
        return self._deduplicate(results)
