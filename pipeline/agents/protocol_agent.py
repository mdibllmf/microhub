"""
Protocol and repository detection agent.

Detects:
  - Protocol references (protocols.io, Nature Protocols, JoVE, etc.)
  - Data repositories (Zenodo, GitHub, Figshare, EMPIAR, IDR, OMERO, etc.)
  - RRIDs (Research Resource Identifiers)
  - ROR IDs (Research Organization Registry)
  - GitHub repository URLs
"""

import re
from typing import Dict, List

from .base_agent import BaseAgent, Extraction

# ======================================================================
# Protocol patterns
# ======================================================================

PROTOCOL_PATTERNS: Dict[str, tuple] = {
    "protocols.io": (re.compile(r"\bprotocols?\.io\b", re.I), 0.95),
    "Bio-protocol": (re.compile(r"\bBio[- ]?protocol\b", re.I), 0.9),
    "Nature Protocols": (re.compile(r"\bNature\s+Protocol\w*\b", re.I), 0.95),
    "STAR Protocols": (re.compile(r"\bSTAR\s+Protocol\w*\b", re.I), 0.95),
    "JoVE": (re.compile(r"\bJoVE\b|Journal\s+of\s+Visualized\s+Experiments", re.I), 0.9),
    "Current Protocols": (re.compile(r"\bCurrent\s+Protocol\w*\b", re.I), 0.9),
    "Methods in Molecular Biology": (re.compile(r"\bMethods\s+in\s+Molecular\s+Biology\b", re.I), 0.9),
    "Methods in Enzymology": (re.compile(r"\bMethods\s+in\s+Enzymology\b", re.I), 0.9),
    "Cold Spring Harbor Protocols": (re.compile(r"\bCold\s+Spring\s+Harbor\s+Protocol\w*\b", re.I), 0.95),
    "MethodsX": (re.compile(r"\bMethodsX\b", re.I), 0.9),
    "Biotechniques": (re.compile(r"\bBiotechniques\b", re.I), 0.85),
    "Protocol Exchange": (re.compile(r"\bProtocol\s+Exchange\b", re.I), 0.9),
}

# Protocol URL patterns
_PROTOCOL_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:"
    r"protocols\.io/[\w/.-]+"
    r"|dx\.doi\.org/10\.\d+/[\w.-]+"  # DOI-based protocol refs
    r"|bio-protocol\.org/[\w/.-]+"
    r"|jove\.com/[\w/.-]+"
    r")",
    re.IGNORECASE,
)

# ======================================================================
# Repository patterns
# ======================================================================

REPOSITORY_PATTERNS: Dict[str, tuple] = {
    "GitHub": (re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w.-]+/[\w.-]+", re.I), 0.95),
    "GitLab": (re.compile(r"(?:https?://)?(?:www\.)?gitlab\.com/[\w.-]+/[\w.-]+", re.I), 0.95),
    "Zenodo": (re.compile(r"(?:https?://)?(?:www\.)?zenodo\.org/(?:record|doi)/[\w./]+", re.I), 0.95),
    "Figshare": (re.compile(r"(?:https?://)?(?:www\.)?figshare\.com/[\w./]+", re.I), 0.95),
    "Dryad": (re.compile(r"(?:https?://)?(?:www\.)?datadryad\.org/[\w./]+", re.I), 0.95),
    "EMPIAR": (re.compile(r"\bEMPIAR[- ]?\d+\b|(?:https?://)?(?:www\.)?ebi\.ac\.uk/empiar/[\w./]+", re.I), 0.95),
    "EMDB": (re.compile(r"\bEMD[- ]?\d{4,}\b|(?:https?://)?(?:www\.)?ebi\.ac\.uk/emdb/[\w./]+", re.I), 0.95),
    "PDB": (re.compile(r"\bPDB(?:\s+(?:ID|accession|code|entry))?\s*[:# ]?\s*\d[A-Za-z0-9]{3}\b", re.I), 0.85),
    "BioImage Archive": (re.compile(r"\bBioImage\s+Archive\b|(?:https?://)?(?:www\.)?bioimage-archive\.ebi\.ac\.uk/[\w./]+", re.I), 0.95),
    "IDR": (re.compile(r"\bImage\s+Data\s+Resource\b|\bidr\d{4}\b|(?:https?://)?idr\.openmicroscopy\.org/[\w./]+", re.I), 0.9),
    "OMERO": (re.compile(r"\bOMERO\b(?=.{0,30}(?:server|repositor|public|database|instance))", re.I | re.S), 0.8),
    "GEO": (re.compile(r"\bGSE\d{3,}\b|Gene\s+Expression\s+Omnibus", re.I), 0.9),
    "SRA": (re.compile(r"\bSR[APXR]\d{6,}\b|Sequence\s+Read\s+Archive", re.I), 0.9),
    "ArrayExpress": (re.compile(r"\bArrayExpress\b|E-MTAB-\d+", re.I), 0.9),
    "PRIDE": (re.compile(r"\bPRIDE\b|PXD\d{6,}", re.I), 0.85),
    "OSF": (re.compile(r"(?:https?://)?osf\.io/[\w]+", re.I), 0.9),
    "Code Ocean": (re.compile(r"\bCode\s+Ocean\b|codeocean\.com", re.I), 0.9),
    "Mendeley Data": (re.compile(r"\bMendeley\s+Data\b|data\.mendeley\.com", re.I), 0.9),
    "BioStudies": (re.compile(r"\bBioStudies\b|S-BSST\d+", re.I), 0.9),
    "SSBD": (re.compile(r"\bSSBD\b(?=.{0,20}(?:database|repositor))", re.I | re.S), 0.8),
}

# ======================================================================
# RRID patterns
# ======================================================================

_RRID_PATTERN = re.compile(
    r"\bRRID\s*:\s*((?:AB|SCR|CVCL|IMSR|BDSC|ZFIN|WB-STRAIN|MGI|MMRRC|ZIRC|DGRC|CGC|Addgene)_\d+)\b",
    re.IGNORECASE,
)

_RRID_TYPE_MAP = {
    "AB": "antibody",
    "SCR": "software",
    "CVCL": "cell_line",
    "Addgene": "plasmid",
}

# ======================================================================
# ROR patterns
# ======================================================================

_ROR_URL_PATTERN = re.compile(r"(?:https?://)?ror\.org/(0[a-z0-9]{8})\b", re.I)

# ======================================================================
# GitHub URL extraction
# ======================================================================

_GITHUB_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([\w.-]+/[\w.-]+)", re.I
)


class ProtocolAgent(BaseAgent):
    """Extract protocol references, data repositories, RRIDs, and RORs."""

    name = "protocol"

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        results: List[Extraction] = []
        results.extend(self._match_protocols(text, section))
        results.extend(self._match_repositories(text, section))
        results.extend(self._match_rrids(text, section))
        results.extend(self._match_rors(text, section))
        results.extend(self._match_github_urls(text, section))
        results.extend(self._match_protocol_urls(text, section))
        return self._deduplicate(results)

    # ------------------------------------------------------------------
    def _match_protocols(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for canonical, (pattern, base_conf) in PROTOCOL_PATTERNS.items():
            for m in pattern.finditer(text):
                extractions.append(Extraction(
                    text=m.group(0),
                    label="PROTOCOL",
                    start=m.start(), end=m.end(),
                    confidence=base_conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": canonical},
                ))
        return extractions

    # ------------------------------------------------------------------
    def _match_repositories(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for repo_type, (pattern, base_conf) in REPOSITORY_PATTERNS.items():
            for m in pattern.finditer(text):
                meta = {"canonical": repo_type}
                # Extract URL if it looks like a URL
                matched = m.group(0)
                if "/" in matched:
                    url = matched if matched.startswith("http") else f"https://{matched}"
                    meta["url"] = url
                extractions.append(Extraction(
                    text=matched,
                    label="REPOSITORY",
                    start=m.start(), end=m.end(),
                    confidence=base_conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata=meta,
                ))
        return extractions

    # ------------------------------------------------------------------
    def _match_rrids(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for m in _RRID_PATTERN.finditer(text):
            rrid_id = m.group(1)
            prefix = rrid_id.split("_")[0]
            rrid_type = _RRID_TYPE_MAP.get(prefix, "organism")
            extractions.append(Extraction(
                text=f"RRID:{rrid_id}",
                label="RRID",
                start=m.start(), end=m.end(),
                confidence=0.95,
                source_agent=self.name,
                section=section or "",
                metadata={
                    "canonical": f"RRID:{rrid_id}",
                    "rrid_id": rrid_id,
                    "rrid_type": rrid_type,
                    "url": f"https://scicrunch.org/resolver/RRID:{rrid_id}",
                },
            ))
        return extractions

    # ------------------------------------------------------------------
    def _match_rors(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for m in _ROR_URL_PATTERN.finditer(text):
            ror_id = m.group(1)
            extractions.append(Extraction(
                text=m.group(0),
                label="ROR",
                start=m.start(), end=m.end(),
                confidence=0.95,
                source_agent=self.name,
                section=section or "",
                metadata={
                    "canonical": ror_id,
                    "url": f"https://ror.org/{ror_id}",
                },
            ))
        return extractions

    # ------------------------------------------------------------------
    def _match_github_urls(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for m in _GITHUB_URL_PATTERN.finditer(text):
            full_name = m.group(1)
            url = f"https://github.com/{full_name}"
            extractions.append(Extraction(
                text=m.group(0),
                label="GITHUB_URL",
                start=m.start(), end=m.end(),
                confidence=0.95,
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": url, "full_name": full_name, "url": url},
            ))
        return extractions

    # ------------------------------------------------------------------
    def _match_protocol_urls(self, text: str, section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        for m in _PROTOCOL_URL_PATTERN.finditer(text):
            url = m.group(0)
            if not url.startswith("http"):
                url = f"https://{url}"
            extractions.append(Extraction(
                text=m.group(0),
                label="PROTOCOL_URL",
                start=m.start(), end=m.end(),
                confidence=0.9,
                source_agent=self.name,
                section=section or "",
                metadata={"canonical": url, "url": url},
            ))
        return extractions
