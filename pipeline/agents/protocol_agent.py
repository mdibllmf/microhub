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
    # OSF: match URLs, DOI-based references (10.17605/OSF.IO/xxx), and text mentions
    "OSF": (re.compile(
        r"(?:https?://)?osf\.io/[\w]+"
        r"|(?:https?://)?doi\.org/10\.17605/OSF\.IO/[\w]+"
        r"|\b10\.17605/OSF\.IO/[\w]+"
        r"|\bOpen\s+Science\s+Framework\b",
        re.I,
    ), 0.9),
    # Code Ocean: full URLs and text mention
    "Code Ocean": (re.compile(
        r"(?:https?://)?(?:www\.)?codeocean\.com/capsule/[\w/.-]+"
        r"|(?:https?://)?(?:www\.)?codeocean\.com/[\w/.-]+"
        r"|\bCode\s+Ocean\b",
        re.I,
    ), 0.9),
    # Mendeley Data: full URLs and text mention
    "Mendeley Data": (re.compile(
        r"(?:https?://)?data\.mendeley\.com/datasets/[\w/.-]+"
        r"|(?:https?://)?data\.mendeley\.com/[\w/.-]+"
        r"|\bMendeley\s+Data\b",
        re.I,
    ), 0.9),

    # --- Structural biology ---
    "EMPIAR": (re.compile(
        r"\bEMPIAR[- ]?\d+\b"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/empiar/[\w./-]+",
        re.I,
    ), 0.95),
    "EMDB": (re.compile(
        r"\bEMD[- ]?\d{4,}\b"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/emdb/[\w./-]+",
        re.I,
    ), 0.95),
    # PDB: accession codes + RCSB URLs
    "PDB": (re.compile(
        r"\bPDB(?:\s+(?:ID|accession|code|entry))?\s*[:# ]?\s*\d[A-Za-z0-9]{3}\b"
        r"|(?:https?://)?(?:www\.)?rcsb\.org/structure/[\w]+"
        r"|(?:https?://)?(?:www\.)?rcsb\.org/pdb/explore\.do\?[\w=&]+",
        re.I,
    ), 0.85),

    # --- BioImaging repositories ---
    # BioImage Archive: new ebi.ac.uk/biostudies/BioImages domain + old domain + S-BIAD accessions
    "BioImage Archive": (re.compile(
        r"\bBioImage\s+Archive\b"
        r"|(?:https?://)?(?:www\.)?bioimage-archive\.ebi\.ac\.uk/[\w./-]+"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/biostudies/BioImages/[\w./-]+"
        r"|\bS-BIAD\d+\b",
        re.I,
    ), 0.95),
    "IDR": (re.compile(
        r"\bImage\s+Data\s+Resource\b|\bidr\d{4}\b"
        r"|(?:https?://)?idr\.openmicroscopy\.org/[\w./]*",
        re.I,
    ), 0.9),
    "OMERO": (re.compile(
        # OMERO URLs — any openmicroscopy.org URL (not just /omero path)
        r"(?:https?://)?(?:[\w.-]+\.)?openmicroscopy\.org(?:/[\w./]*)?"
        r"|(?:https?://)?[\w.-]+/omero/(?:webclient|api|webgateway)[\w./]*"
        # Institutional OMERO servers (hostname contains "omero")
        r"|(?:https?://)?[\w.-]*omero[\w.-]*\.[\w]+(?:\.[\w]+)+(?:/[\w./]*)?"
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
        r"|\b(?:an?|the)\s+OMERO\s+(?:server|instance|database)\b"
        # OME/OMERO compound reference (e.g., "OME/OMERO ... software used")
        r"|\bOME\s*/\s*OMERO\b"
        # OMERO with "used" or "software" context (e.g., "OMERO ... software used in this paper")
        r"|\bOMERO\b(?=.{0,50}(?:software|used\s+in|used\s+for|used\s+to))",
        re.I | re.S,
    ), 0.85),
    "SSBD": (re.compile(
        r"\bSSBD\b(?=.{0,30}(?:database|repositor|available))"
        r"|(?:https?://)?ssbd\.riken\.jp/[\w./]*",
        re.I | re.S,
    ), 0.85),

    # --- Genomics / transcriptomics ---
    # GEO: accession IDs, text mention, URLs (including query params)
    "GEO": (re.compile(
        r"\bGSE\d{3,}\b"
        r"|\bGene\s+Expression\s+Omnibus\b"
        r"|(?:https?://)?(?:www\.)?ncbi\.nlm\.nih\.gov/geo/query/acc\.cgi\?acc=\w+"
        r"|(?:https?://)?(?:www\.)?ncbi\.nlm\.nih\.gov/geo/[\w./?=&]+",
        re.I,
    ), 0.9),
    # SRA: accession IDs + BioProject PRJNA accessions + URLs
    "SRA": (re.compile(
        r"\bSR[APXR]\d{6,}\b"
        r"|\bPRJNA\d+\b"
        r"|\bSequence\s+Read\s+Archive\b"
        r"|(?:https?://)?(?:www\.)?ncbi\.nlm\.nih\.gov/sra/[\w./?=&]+"
        r"|(?:https?://)?(?:www\.)?ncbi\.nlm\.nih\.gov/bioproject/[\w./?=&]+",
        re.I,
    ), 0.9),
    # ArrayExpress: accession IDs + old and new EBI domains
    "ArrayExpress": (re.compile(
        r"\bArrayExpress\b"
        r"|\bE-[A-Z]{4}-\d+\b"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/arrayexpress/[\w./-]+"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/biostudies/arrayexpress/studies/[\w./-]+",
        re.I,
    ), 0.9),
    # ENA: accession IDs + text mention + EBI URLs
    "ENA": (re.compile(
        r"\bEuropean\s+Nucleotide\s+Archive\b"
        r"|\bENA\b(?=.{0,20}(?:accession|project))"
        r"|\bPRJE[A-Z]\d{5,}\b"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/ena/browser/view/[\w./-]+",
        re.I | re.S,
    ), 0.9),

    # --- Proteomics ---
    # PRIDE: accession IDs + text mention + EBI URLs
    "PRIDE": (re.compile(
        r"\bPRIDE\b(?=.{0,20}(?:database|archive|accession))"
        r"|\bPXD\d{6,}\b"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/pride/archive/projects/[\w./-]+",
        re.I | re.S,
    ), 0.85),
    "ProteomeXchange": (re.compile(r"\bProteomeXchange\b", re.I), 0.85),

    # --- Multi-purpose ---
    # BioStudies: accession IDs + text mention + EBI URLs
    "BioStudies": (re.compile(
        r"\bBioStudies\b"
        r"|\bS-BSST\d+\b"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/biostudies/studies/[\w./-]+",
        re.I,
    ), 0.9),
    "Dataverse": (re.compile(
        r"(?:https?://)?(?:[\w.-]+\.)?dataverse\.[\w./]+"
        r"|\bDataverse\b(?=.{0,20}(?:dataset|repositor|available))",
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

    # --- Cell Image Library ---
    "Cell Image Library": (re.compile(
        r"\bCell\s+Image\s+Library\b"
        r"|(?:https?://)?(?:www\.)?cellimagelibrary\.org/[\w./]+"
        r"|\bCIL[: ]\d+\b",
        re.I,
    ), 0.9),

    # --- BioModels ---
    "BioModels": (re.compile(
        r"\bBioModels?\b(?=.{0,20}(?:database|repositor|accession))"
        r"|\bBIOMD\d+\b|\bMODEL\d+\b"
        r"|(?:https?://)?(?:www\.)?ebi\.ac\.uk/biomodels/[\w./-]+",
        re.I | re.S,
    ), 0.85),

    # --- BioImage Model Zoo ---
    "BioImage Model Zoo": (re.compile(
        r"\bBioImage\s+Model\s+Zoo\b"
        r"|(?:https?://)?bioimage\.io/[\w./#-]+",
        re.I,
    ), 0.9),

    # --- NAOJ / JCB DataViewer ---
    "JCB DataViewer": (re.compile(
        r"\bJCB\s+DataViewer\b"
        r"|(?:https?://)?(?:www\.)?jcb-dataviewer\.rupress\.org/[\w./]+",
        re.I,
    ), 0.9),
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
    r"codeocean|openneuro|neuromorpho|sciencedb|empiar|"
    r"cellimagelibrary|bioimage|biomodels|jcb-dataviewer|"
    r"rcsb|mendeley)"
    r"(?:\.[\w]+)+"
    r"(?:/[\w./%-?=&]*)?",
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
    "cellimagelibrary": "Cell Image Library",
    "bioimage": "BioImage Model Zoo",
    "biomodels": "BioModels",
    "jcb-dataviewer": "JCB DataViewer",
    "rcsb": "PDB",
    "mendeley": "Mendeley Data",
}


def _url_to_repo_name(url: str) -> str:
    """Determine repository name from a URL domain."""
    url_lower = url.lower()
    for domain, name in _URL_DOMAIN_TO_NAME.items():
        if domain in url_lower:
            return name
    return ""


# ======================================================================
# Accession → URL templates
# When a regex matches an accession number (e.g. EMPIAR-10234), these
# templates construct a clickable URL from the matched ID.
# ======================================================================

ACCESSION_URL_TEMPLATES: Dict[str, str] = {
    "EMPIAR": "https://www.ebi.ac.uk/empiar/EMPIAR-{id}",
    "EMDB": "https://www.ebi.ac.uk/emdb/EMD-{id}",
    "PDB": "https://www.rcsb.org/structure/{id}",
    "GEO": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={id}",
    "SRA": "https://www.ncbi.nlm.nih.gov/sra/{id}",
    "BioProject": "https://www.ncbi.nlm.nih.gov/bioproject/{id}",
    "ArrayExpress": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/{id}",
    "BioImage Archive": "https://www.ebi.ac.uk/biostudies/BioImages/studies/{id}",
    "BioStudies": "https://www.ebi.ac.uk/biostudies/studies/{id}",
    "IDR": "https://idr.openmicroscopy.org/search/?query=Name:{id}",
    "PRIDE": "https://www.ebi.ac.uk/pride/archive/projects/{id}",
    "ENA": "https://www.ebi.ac.uk/ena/browser/view/{id}",
    "DANDI": "https://dandiarchive.org/dandiset/{id}",
    "OpenNeuro": "https://openneuro.org/datasets/{id}",
    "Synapse": "https://www.synapse.org/#!Synapse:{id}",
    "Cell Image Library": "http://www.cellimagelibrary.org/images/{id}",
    "BioModels": "https://www.ebi.ac.uk/biomodels/{id}",
}

# Accession ID extractors: given a matched text, extract the bare ID
# to plug into the URL template above
_ACCESSION_ID_EXTRACTORS: Dict[str, re.Pattern] = {
    "EMPIAR": re.compile(r"EMPIAR[- ]?(\d+)", re.I),
    "EMDB": re.compile(r"EMD[- ]?(\d{4,})", re.I),
    "PDB": re.compile(r"(\d[A-Za-z0-9]{3})"),
    "GEO": re.compile(r"(GSE\d{3,})", re.I),
    "SRA": re.compile(r"(SR[APXR]\d{6,}|PRJNA\d+)", re.I),
    "BioProject": re.compile(r"(PRJ[A-Z]{2}\d+)", re.I),
    "ArrayExpress": re.compile(r"(E-[A-Z]{4}-\d+)", re.I),
    "BioImage Archive": re.compile(r"(S-BIAD\d+)", re.I),
    "BioStudies": re.compile(r"(S-[A-Z]{3,4}\d+)", re.I),
    "IDR": re.compile(r"(idr\d{4})", re.I),
    "PRIDE": re.compile(r"(PXD\d{6,})", re.I),
    "ENA": re.compile(r"(PRJ[A-Z]{2}\d+)", re.I),
    "DANDI": re.compile(r"DANDI[: ]?(\d+)", re.I),
    "OpenNeuro": re.compile(r"(ds\d{6})", re.I),
    "Synapse": re.compile(r"(syn\d{6,})", re.I),
    "Cell Image Library": re.compile(r"CIL[: ]?(\d+)", re.I),
    "BioModels": re.compile(r"(BIOMD\d+|MODEL\d+)", re.I),
}


def _accession_to_url(repo_type: str, matched_text: str) -> str:
    """Generate a clickable URL from an accession number match.

    Uses ACCESSION_URL_TEMPLATES and _ACCESSION_ID_EXTRACTORS to turn
    accession-only matches (e.g. 'EMPIAR-10234', 'GSE123456') into
    full URLs like 'https://www.ebi.ac.uk/empiar/EMPIAR-10234'.
    """
    extractor = _ACCESSION_ID_EXTRACTORS.get(repo_type)
    if not extractor:
        return ""
    m = extractor.search(matched_text)
    if not m:
        return ""
    accession_id = m.group(1) if m.lastindex else m.group(0)

    # SRA special case: PRJNA accessions use BioProject URL
    if repo_type == "SRA" and accession_id.upper().startswith("PRJNA"):
        template = ACCESSION_URL_TEMPLATES.get("BioProject", "")
    else:
        template = ACCESSION_URL_TEMPLATES.get(repo_type, "")

    if not template:
        return ""
    return template.format(id=accession_id)


def _resolve_overlaps(extractions: List[Extraction]) -> List[Extraction]:
    """Resolve overlapping repository extractions.

    When two patterns match the same or overlapping text spans (e.g.
    BioImage Archive and BioStudies both matching an S-BIAD ID), keep
    the one with higher confidence (or the more specific name).
    """
    if len(extractions) <= 1:
        return extractions

    # Sort by start position, then by confidence descending
    sorted_exts = sorted(extractions, key=lambda e: (e.start, -e.confidence))

    result: List[Extraction] = []
    for ext in sorted_exts:
        # Check if this extraction overlaps with any already-kept extraction
        overlaps = False
        for kept in result:
            # Two extractions overlap if their spans intersect
            if ext.start < kept.end and ext.end > kept.start:
                overlaps = True
                # If the new one has higher confidence, replace the kept one
                if ext.confidence > kept.confidence:
                    result.remove(kept)
                    result.append(ext)
                break
        if not overlaps:
            result.append(ext)

    return result


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
                elif "/" in matched and not matched[0].isalpha():
                    meta["url"] = f"https://{matched}"
                else:
                    # Accession number (no URL in match) → generate URL
                    url = _accession_to_url(repo_type, matched)
                    if url:
                        meta["url"] = url
                        # Extract the bare accession ID for metadata
                        extractor = _ACCESSION_ID_EXTRACTORS.get(repo_type)
                        if extractor:
                            id_m = extractor.search(matched)
                            if id_m:
                                meta["accession_id"] = id_m.group(1) if id_m.lastindex else id_m.group(0)

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
            url = m.group(0).rstrip(".,;)")
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

        # Resolve overlapping extractions — when two patterns match the
        # same text span, keep the more specific (higher confidence) one
        extractions = _resolve_overlaps(extractions)

        # When the same repository type appears multiple times (e.g., text
        # mention "Gene Expression Omnibus" AND accession "GSE123456"),
        # keep all matches but ensure the URL-bearing one wins in dedup.
        # Re-sort so URL-bearing matches come first (dedup keeps highest confidence,
        # and we bump confidence slightly for URL-bearing matches).
        for ext in extractions:
            if ext.metadata.get("url") and ext.confidence < 1.0:
                ext.confidence = min(ext.confidence + 0.01, 1.0)

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
