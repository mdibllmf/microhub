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
    r"|nature\.com/nprot[\w/.-]*"
    r"|cell\.com/star-protocols[\w/.-]*"
    r"|currentprotocols\.[\w/.-]+"
    r"|cshprotocols\.[\w/.-]+"
    r")",
    re.IGNORECASE,
)

# Protocol DOI patterns -- identify protocol papers by their DOI prefix
PROTOCOL_DOI_PATTERNS = [
    re.compile(r"\b10\.1038/nprot\b"),           # Nature Protocols
    re.compile(r"\b10\.3791/\d+\b"),             # JoVE
    re.compile(r"\b10\.1016/j\.xpro\b"),         # STAR Protocols
    re.compile(r"\b10\.21769/BioProtoc\b"),      # Bio-protocol
    re.compile(r"\b10\.1002/cpz\d?\b"),          # Current Protocols
    re.compile(r"\b10\.1002/cphy\b"),            # Current Protocols
    re.compile(r"\b10\.1101/pdb\b"),             # Cold Spring Harbor Protocols
]

# Protocol journal patterns -- identify protocol papers by journal name
PROTOCOL_JOURNAL_PATTERNS = [
    re.compile(r"\bnat\.?\s*protoc", re.I),
    re.compile(r"\bj\.?\s*vis\.?\s*exp\b", re.I),
    re.compile(r"\bcurr\.?\s*protoc", re.I),
    re.compile(r"\bmethods\s+mol\.?\s*biol\b", re.I),
    re.compile(r"\bcsh\s+protocols?\b", re.I),
    re.compile(r"\bmethods\s*x\b", re.I),
    re.compile(r"\bstar\s+protocols?\b", re.I),
    re.compile(r"\bjournal\s+of\s+biological\s+methods\b", re.I),
    re.compile(r"\bdetailed\s+protocol\b", re.I),
    re.compile(r"\bstep[- ]by[- ]step\s+protocol\b", re.I),
    re.compile(r"\boptimized\s+protocol\b", re.I),
    re.compile(r"\bimproved\s+protocol\b", re.I),
]

# ======================================================================
# Repository patterns
# ======================================================================

REPOSITORY_PATTERNS: Dict[str, tuple] = {
    # --- Code repositories ---
    "GitHub": (re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w.-]+/[\w.-]+", re.I), 0.95),
    "GitLab": (re.compile(r"(?:https?://)?(?:www\.)?gitlab\.com/[\w.-]+/[\w.-]+", re.I), 0.95),
    "Bitbucket": (re.compile(r"(?:https?://)?(?:www\.)?bitbucket\.org/[\w.-]+/[\w.-]+", re.I), 0.95),

    # --- Data repositories ---
    # Zenodo: match URLs, DOI-based URLs, and bare DOI references (10.5281/zenodo.NNN)
    "Zenodo": (re.compile(
        r"(?:https?://)?(?:www\.)?zenodo\.org/(?:record|records|doi|api)/[\w./]+"
        r"|(?:https?://)?doi\.org/10\.5281/zenodo\.\d+"
        r"|\b10\.5281/zenodo\.\d+"
        r"|\bzenodo\.\d{4,}\b",
        re.I,
    ), 0.95),
    # Figshare: match URLs and DOI references (10.6084/m9.figshare.NNN)
    "Figshare": (re.compile(
        r"(?:https?://)?(?:www\.)?figshare\.com/[\w./]+"
        r"|(?:https?://)?doi\.org/10\.6084/m9\.figshare\.\d+"
        r"|\b10\.6084/m9\.figshare\.\d+",
        re.I,
    ), 0.95),
    # Dryad: match URLs and DOI references (10.5061/dryad.xxx)
    "Dryad": (re.compile(
        r"(?:https?://)?(?:www\.)?datadryad\.org/[\w./]+"
        r"|(?:https?://)?doi\.org/10\.5061/dryad\.[\w.]+"
        r"|\b10\.5061/dryad\.[\w.]+",
        re.I,
    ), 0.95),
    "OSF": (re.compile(r"(?:https?://)?osf\.io/[\w]+", re.I), 0.9),
    "Code Ocean": (re.compile(
        r"\bCode\s+Ocean\b|(?:https?://)?codeocean\.com/[\w./]*",
        re.I,
    ), 0.9),
    "Mendeley Data": (re.compile(
        r"\bMendeley\s+Data\b|(?:https?://)?data\.mendeley\.com/[\w./]*",
        re.I,
    ), 0.9),

    # --- Structural biology ---
    "EMPIAR": (re.compile(r"\bEMPIAR[- ]?\d+\b|(?:https?://)?(?:www\.)?ebi\.ac\.uk/empiar/[\w./]+", re.I), 0.95),
    "EMDB": (re.compile(r"\bEMD[- ]?\d{4,}\b|(?:https?://)?(?:www\.)?ebi\.ac\.uk/emdb/[\w./]+", re.I), 0.95),
    "PDB": (re.compile(r"\bPDB(?:\s+(?:ID|accession|code|entry))?\s*[:# ]?\s*\d[A-Za-z0-9]{3}\b", re.I), 0.85),

    # --- BioImaging repositories ---
    "BioImage Archive": (re.compile(
        r"\bBioImage\s+Archive\b|"
        r"(?:https?://)?(?:www\.)?bioimage-archive\.ebi\.ac\.uk/[\w./]+|"
        r"\bS-BIAD\d+\b",
        re.I,
    ), 0.95),
    "IDR": (re.compile(
        r"\bImage\s+Data\s+Resource\b|\bidr\d{4}\b|"
        r"(?:https?://)?idr\.openmicroscopy\.org/[\w./]*",
        re.I,
    ), 0.9),
    "OMERO": (re.compile(
        # OMERO URLs — any openmicroscopy.org URL (not just /omero path)
        r"(?:https?://)?(?:[\w.-]+\.)?openmicroscopy\.org(?:/[\w./]*)?"
        r"|(?:https?://)?[\w.-]+/omero/(?:webclient|api|webgateway)[\w./]*"
        # OMERO with context words AFTER (server, repository, platform, etc.)
        r"|\bOMERO\b(?=.{0,40}(?:server|repositor|public|database|instance|"
        r"gallery|platform|client|image\s*manage))"
        # "OMERO" + component (OMERO.web, OMERO.figure, OMERO Plus)
        r"|\bOMERO\s*[.]?\s*(?:web|figure|Plus|insight|cli|server)\b"
        # OMERO with availability context after
        r"|\bOMERO\b(?=.{0,50}(?:https?://|available|deposited|hosted|stored|accessible))"
        # Availability context before OMERO (e.g., "deposited in OMERO", "via OMERO")
        r"|(?:available|deposited|hosted|stored|accessible|uploaded|shared|import\w*"
        r"|saving|saved|manage\w*)\s+(?:in|on|via|through|at|to|into)\s+OMERO\b"
        # OMERO Public / OMERO server with preceding article
        r"|\b(?:an?|the)\s+OMERO\s+(?:server|instance|database)\b",
        re.I | re.S,
    ), 0.85),
    "SSBD": (re.compile(
        r"\bSSBD\b(?=.{0,30}(?:database|repositor|available))|"
        r"(?:https?://)?ssbd\.riken\.jp/[\w./]*",
        re.I | re.S,
    ), 0.85),

    # --- Electron Microscopy Public Image Archive ---
    "EMIAP": (re.compile(
        r"\bEMIAP[- ]?\d+\b|"
        r"(?:https?://)?(?:www\.)?ebi\.ac\.uk/emiap/[\w./]+",
        re.I,
    ), 0.95),

    # --- Genomics / transcriptomics ---
    "GEO": (re.compile(
        r"\bGSE\d{3,}\b|Gene\s+Expression\s+Omnibus|"
        r"(?:https?://)?(?:www\.)?ncbi\.nlm\.nih\.gov/geo/[\w./]+",
        re.I,
    ), 0.9),
    "SRA": (re.compile(r"\bSR[APXR]\d{6,}\b|Sequence\s+Read\s+Archive", re.I), 0.9),
    "ArrayExpress": (re.compile(
        r"\bArrayExpress\b|E-MTAB-\d+|"
        r"(?:https?://)?(?:www\.)?ebi\.ac\.uk/arrayexpress/[\w./]+",
        re.I,
    ), 0.9),
    "ENA": (re.compile(
        r"\bEuropean\s+Nucleotide\s+Archive\b|"
        r"\bENA\b(?=.{0,20}(?:accession|project))|"
        r"\bPRJE[A-Z]\d{5,}\b",
        re.I | re.S,
    ), 0.9),

    # --- Proteomics ---
    "PRIDE": (re.compile(r"\bPRIDE\b(?=.{0,20}(?:database|archive|accession))|PXD\d{6,}", re.I | re.S), 0.85),
    "ProteomeXchange": (re.compile(r"\bProteomeXchange\b", re.I), 0.85),

    # --- Multi-purpose ---
    "BioStudies": (re.compile(r"\bBioStudies\b|S-BSST\d+", re.I), 0.9),
    "Dataverse": (re.compile(
        r"(?:https?://)?(?:[\w.-]+\.)?dataverse\.[\w./]+|"
        r"\bDataverse\b(?=.{0,20}(?:dataset|repositor|available))",
        re.I | re.S,
    ), 0.85),
    "Hugging Face": (re.compile(
        r"(?:https?://)?huggingface\.co/[\w.-]+/[\w.-]+",
        re.I,
    ), 0.9),

    # --- Neuroscience repositories ---
    "DANDI": (re.compile(
        r"(?:https?://)?dandiarchive\.org/[\w./]+"
        r"|\bDANDI:\d+\b|\bDANDI\s+Archive\b",
        re.I,
    ), 0.9),
    "NeuroMorpho": (re.compile(
        r"(?:https?://)?neuromorpho\.org/[\w./]+"
        r"|\bNeuroMorpho\b",
        re.I,
    ), 0.9),
    "OpenNeuro": (re.compile(
        r"(?:https?://)?openneuro\.org/[\w./]+"
        r"|\bds\d{6}\b"
        r"|\bOpenNeuro\b",
        re.I,
    ), 0.9),

    # --- Synapse (Sage Bionetworks) ---
    "Synapse": (re.compile(
        r"(?:https?://)?(?:www\.)?synapse\.org/[\w#./]+"
        r"|\bsyn\d{6,}\b",
        re.I,
    ), 0.9),

    # --- ScienceDB / Science Data Bank ---
    "ScienceDB": (re.compile(
        r"(?:https?://)?(?:www\.)?sciencedb\.(?:cn|com)/[\w./]+"
        r"|\bScience\s+Data\s+Bank\b",
        re.I,
    ), 0.85),

    # --- Cloud storage with data ---
    "AWS Open Data": (re.compile(
        r"(?:https?://)?registry\.opendata\.aws/[\w/.-]+",
        re.I,
    ), 0.85),
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

_ROR_PATTERNS = [
    re.compile(r"(?:https?://)?ror\.org/(0[a-z0-9]{8})\b", re.I),
    re.compile(r"\bROR\s*:\s*(0[a-z0-9]{8})\b", re.I),
    re.compile(r"\bROR\s+ID\s*:\s*(0[a-z0-9]{8})\b", re.I),
    re.compile(r"\(ROR:\s*(0[a-z0-9]{8})\)", re.I),
    re.compile(r"doi\.org/10\.(?:ror|ROR)/(0[a-z0-9]{8})", re.I),
]

# ======================================================================
# GitHub URL extraction
# ======================================================================

_GITHUB_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([\w.-]+/[\w.-]+)", re.I
)


# ======================================================================
# Fallback: generic data-repository URL pattern
# Catches any URL containing a known data-repository domain
# ======================================================================

_DATA_URL_FALLBACK = re.compile(
    r"https?://"
    r"(?:[\w.-]+\.)*"
    r"(?:zenodo|figshare|dryad|datadryad|osf|omero|openmicroscopy|synapse|"
    r"dandiarchive|bioimage-archive|idr|dataverse|huggingface|"
    r"codeocean|openneuro|neuromorpho|sciencedb|empiar)"
    r"(?:\.[\w]+)+"
    r"(?:/[\w./%-]*)?",
    re.I,
)

_URL_DOMAIN_TO_NAME = {
    "zenodo": "Zenodo",
    "figshare": "Figshare",
    "dryad": "Dryad",
    "datadryad": "Dryad",
    "osf": "OSF",
    "omero": "OMERO",
    "openmicroscopy": "OMERO",
    "synapse": "Synapse",
    "dandiarchive": "DANDI",
    "bioimage-archive": "BioImage Archive",
    "idr": "IDR",
    "dataverse": "Dataverse",
    "huggingface": "Hugging Face",
    "codeocean": "Code Ocean",
    "openneuro": "OpenNeuro",
    "neuromorpho": "NeuroMorpho",
    "sciencedb": "ScienceDB",
    "empiar": "EMPIAR",
}


def _url_to_repo_name(url: str) -> str:
    """Determine repository name from a URL domain."""
    url_lower = url.lower()
    for domain, name in _URL_DOMAIN_TO_NAME.items():
        if domain in url_lower:
            return name
    return ""


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
                matched = m.group(0).rstrip(".,;)")

                # Construct proper URL from the match
                if matched.startswith("http"):
                    meta["url"] = matched
                elif matched.startswith("10."):
                    # Bare DOI reference → construct doi.org URL
                    meta["url"] = f"https://doi.org/{matched}"
                elif "/" in matched:
                    meta["url"] = f"https://{matched}"

                extractions.append(Extraction(
                    text=matched,
                    label="REPOSITORY",
                    start=m.start(), end=m.end(),
                    confidence=base_conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata=meta,
                ))

        # Fallback: scan for any URL containing a known data repo domain
        for m in _DATA_URL_FALLBACK.finditer(text):
            url = m.group(0)
            # Skip if already captured by specific patterns above
            if any(e.metadata.get("url", "").rstrip("/") == url.rstrip("/")
                   for e in extractions):
                continue
            # Determine repo name from domain
            name = _url_to_repo_name(url)
            if name:
                extractions.append(Extraction(
                    text=url,
                    label="REPOSITORY",
                    start=m.start(), end=m.end(),
                    confidence=0.8,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": name, "url": url},
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
        for pattern in _ROR_PATTERNS:
            for m in pattern.finditer(text):
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
