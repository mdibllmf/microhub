#!/usr/bin/env python3
"""
MICROHUB PAPER SCRAPER v5.0 - COMPREHENSIVE EDITION WITH AFFILIATIONS
======================================================================
Based on v4.1 with ADDED:
- AUTHOR AFFILIATIONS extraction (critical for institution identification)

Complete paper collection with:
- CITATION COUNTS from multiple sources (Semantic Scholar, CrossRef)
- Full text via PMC API
- Complete methods sections
- Figure metadata
- ALL protocols and repositories with URL VALIDATION (including OMERO)
- Comprehensive tag extraction including fluorophores
- Deduplication and cleanup
- AUTHOR AFFILIATIONS (NEW in v5.0)

Usage:
  python microhub_scraper_v5.py                      # Full scrape
  python microhub_scraper_v5.py --limit 1000         # Limited papers
  python microhub_scraper_v5.py --priority-only      # Only high-value papers
  python microhub_scraper_v5.py --full-text-only     # Only papers with full text
  python microhub_scraper_v5.py --fetch-citations    # Update citations for existing papers

CHANGES IN v5.0:
- Added AUTHOR AFFILIATIONS extraction from PubMed XML
- Affiliations stored in 'affiliations' field (JSON array)
- This enables accurate institution extraction in the cleanup script
  (extracts from affiliations, not random text mentions)
"""

import sqlite3
import requests
import json
import time
import re
import logging
import argparse
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, quote
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================================
# LLM ENRICHMENT CONFIGURATION (Optional - expensive, disabled by default)
# ============================================================================
LLM_MODEL = "claude-haiku-4-5-20250929"
LLM_RATE_LIMIT_DELAY = 1.0  # Seconds between API calls
LLM_MIN_TAGS_REQUIRED = 5  # Minimum tags to keep paper (skip if fewer)

# ============================================================================
# API RETRY CONFIGURATION
# ============================================================================
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # Base delay in seconds (will be multiplied exponentially)
RETRY_MAX_DELAY = 30.0  # Maximum delay between retries

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS - Text Cleaning & Retry Logic
# ============================================================================

def retry_with_backoff(func):
    """
    Decorator that retries a function with exponential backoff on failure.
    Handles network errors, timeouts, and rate limiting.
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.Timeout as e:
                last_exception = e
                delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                logger.debug(f"Timeout in {func.__name__}, retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s")
                time.sleep(delay)
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                logger.debug(f"Connection error in {func.__name__}, retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s")
                time.sleep(delay)
            except requests.exceptions.HTTPError as e:
                # Don't retry 4xx errors (except 429 rate limit)
                if e.response is not None and 400 <= e.response.status_code < 500:
                    if e.response.status_code == 429:  # Rate limited
                        delay = min(RETRY_BASE_DELAY * (2 ** (attempt + 2)), RETRY_MAX_DELAY)
                        logger.warning(f"Rate limited in {func.__name__}, waiting {delay:.1f}s")
                        time.sleep(delay)
                        last_exception = e
                        continue
                    raise  # Don't retry other 4xx errors
                last_exception = e
                delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                time.sleep(delay)
            except Exception as e:
                # For unexpected errors, log and don't retry
                logger.debug(f"Unexpected error in {func.__name__}: {e}")
                raise

        # All retries exhausted
        logger.warning(f"All {MAX_RETRIES} retries exhausted for {func.__name__}")
        if last_exception:
            raise last_exception
        return None

    return wrapper


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    - Remove HTML entities
    - Normalize whitespace
    - Remove control characters
    - Strip leading/trailing whitespace
    """
    if not text:
        return ''

    import html

    # Decode HTML entities (e.g., &amp; -> &, &lt; -> <)
    text = html.unescape(text)

    # Remove control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Normalize whitespace (multiple spaces/tabs -> single space)
    text = re.sub(r'[ \t]+', ' ', text)

    # Normalize newlines (multiple -> single)
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def normalize_doi(doi: str) -> Optional[str]:
    """Normalize DOI to standard format."""
    if not doi:
        return None

    doi = doi.strip().lower()

    # Remove common prefixes
    prefixes = ['https://doi.org/', 'http://doi.org/', 'doi:', 'doi.org/']
    for prefix in prefixes:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]

    # Basic validation - DOI should start with 10.
    if not doi.startswith('10.'):
        return None

    return doi


def validate_pmid(pmid: str) -> Optional[str]:
    """Validate and normalize PMID."""
    if not pmid:
        return None

    # Remove any non-numeric characters
    pmid = re.sub(r'\D', '', str(pmid))

    # PMID should be numeric and reasonable length
    if not pmid or len(pmid) > 10:
        return None

    return pmid


def extract_year(text: str) -> Optional[int]:
    """Extract a valid publication year from text."""
    if not text:
        return None

    # Look for 4-digit years between 1900 and current year + 1
    from datetime import datetime
    current_year = datetime.now().year

    matches = re.findall(r'\b(19\d{2}|20\d{2})\b', str(text))
    for match in matches:
        year = int(match)
        if 1900 <= year <= current_year + 1:
            return year

    return None


# ============================================================================
# DATABASE SCHEMA - COMPREHENSIVE (with affiliations added in v5.0)
# ============================================================================

DB_INIT = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=60000;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=MEMORY;
"""

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pmid TEXT UNIQUE,
    doi TEXT,
    pmc_id TEXT,
    title TEXT NOT NULL,
    authors TEXT,
    journal TEXT,
    year INTEGER,
    abstract TEXT,
    methods TEXT,
    full_text TEXT,

    -- AFFILIATIONS (NEW in v5.0) - Critical for institution extraction
    affiliations TEXT DEFAULT '[]',

    -- URLs
    doi_url TEXT,
    pubmed_url TEXT,
    pmc_url TEXT,
    pdf_url TEXT,

    -- Protocols and repositories (JSON arrays)
    protocols TEXT DEFAULT '[]',
    repositories TEXT DEFAULT '[]',
    github_url TEXT,
    supplementary_materials TEXT DEFAULT '[]',

    -- Resource identifiers (JSON arrays)
    rrids TEXT DEFAULT '[]',
    rors TEXT DEFAULT '[]',

    -- Equipment (JSON arrays)
    microscope_brands TEXT DEFAULT '[]',
    microscope_models TEXT DEFAULT '[]',

    -- Facility
    facility TEXT,

    -- Figures (JSON array)
    figures TEXT DEFAULT '[]',
    figure_count INTEGER DEFAULT 0,

    -- COMPREHENSIVE CATEGORIZED TAGS (JSON arrays)
    microscopy_techniques TEXT DEFAULT '[]',
    image_analysis_software TEXT DEFAULT '[]',
    image_acquisition_software TEXT DEFAULT '[]',
    organisms TEXT DEFAULT '[]',
    sample_preparation TEXT DEFAULT '[]',
    fluorophores TEXT DEFAULT '[]',
    antibodies TEXT DEFAULT '[]',
    cell_lines TEXT DEFAULT '[]',
    imaging_modalities TEXT DEFAULT '[]',
    staining_methods TEXT DEFAULT '[]',
    
    -- Additional scientific fields
    lasers TEXT DEFAULT '[]',
    detectors TEXT DEFAULT '[]',
    objectives TEXT DEFAULT '[]',
    filters TEXT DEFAULT '[]',
    embedding_methods TEXT DEFAULT '[]',
    fixation_methods TEXT DEFAULT '[]',
    mounting_media TEXT DEFAULT '[]',

    -- Legacy fields for compatibility
    techniques TEXT DEFAULT '[]',
    software TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    microscope_brand TEXT,

    -- CITATIONS - CRITICAL!
    citation_count INTEGER DEFAULT 0,
    citation_source TEXT,
    citations_updated_at TIMESTAMP,
    
    -- Semantic Scholar data
    semantic_scholar_id TEXT,
    influential_citation_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enriched_at TIMESTAMP,
    validated_at TIMESTAMP,
    full_text_fetched_at TIMESTAMP,

    -- Flags
    has_protocols BOOLEAN DEFAULT 0,
    has_github BOOLEAN DEFAULT 0,
    has_data BOOLEAN DEFAULT 0,
    has_full_text BOOLEAN DEFAULT 0,
    has_figures BOOLEAN DEFAULT 0,
    has_affiliations BOOLEAN DEFAULT 0,
    links_validated BOOLEAN DEFAULT 0,
    priority_score INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_pmid ON papers(pmid);
CREATE INDEX IF NOT EXISTS idx_papers_pmc ON papers(pmc_id);
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_citations ON papers(citation_count DESC);
CREATE INDEX IF NOT EXISTS idx_papers_priority ON papers(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_papers_has_protocols ON papers(has_protocols);
CREATE INDEX IF NOT EXISTS idx_papers_has_github ON papers(has_github);
CREATE INDEX IF NOT EXISTS idx_papers_has_full_text ON papers(has_full_text);
CREATE INDEX IF NOT EXISTS idx_papers_has_figures ON papers(has_figures);
CREATE INDEX IF NOT EXISTS idx_papers_has_affiliations ON papers(has_affiliations);

CREATE TABLE IF NOT EXISTS figures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER,
    figure_label TEXT,
    figure_title TEXT,
    caption TEXT,
    image_url TEXT,
    thumbnail_url TEXT,
    file_name TEXT,
    position INTEGER,
    figure_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);

CREATE INDEX IF NOT EXISTS idx_figures_paper ON figures(paper_id);

CREATE TABLE IF NOT EXISTS scrape_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT,
    found INTEGER,
    saved INTEGER,
    skipped INTEGER,
    full_text_fetched INTEGER DEFAULT 0,
    citations_fetched INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS url_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    status_code INTEGER,
    is_valid BOOLEAN,
    redirect_url TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- GITHUB TOOLS TRACKING - Track repos referenced across multiple papers
-- ============================================================================

CREATE TABLE IF NOT EXISTS github_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_url TEXT UNIQUE NOT NULL,           -- Normalized URL: https://github.com/owner/repo
    owner TEXT NOT NULL,                     -- GitHub owner/org
    repo_name TEXT NOT NULL,                 -- Repository name
    full_name TEXT NOT NULL,                 -- owner/repo
    description TEXT,                        -- Repo description from GitHub API
    
    -- GitHub API metrics (updated periodically)
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    open_issues INTEGER DEFAULT 0,
    watchers INTEGER DEFAULT 0,
    
    -- Activity metrics
    last_commit_date TIMESTAMP,             -- Date of last commit
    created_date TIMESTAMP,                 -- Repo creation date
    last_release_date TIMESTAMP,            -- Date of last release
    last_release_tag TEXT,                   -- Tag of last release
    default_branch TEXT DEFAULT 'main',
    license TEXT,
    language TEXT,                           -- Primary language
    topics TEXT DEFAULT '[]',               -- JSON array of GitHub topics
    
    -- Computed health score
    health_score INTEGER DEFAULT 0,          -- 0-100 composite score
    is_archived BOOLEAN DEFAULT 0,
    is_fork BOOLEAN DEFAULT 0,
    
    -- MicroHub-specific tracking
    paper_count INTEGER DEFAULT 0,           -- Number of papers referencing this tool
    citing_paper_count INTEGER DEFAULT 0,    -- Papers that cite/use it (not the original)
    original_paper_id INTEGER,               -- The paper that introduced this tool (if known)
    total_citations_of_papers INTEGER DEFAULT 0,  -- Sum of citations of papers using this tool
    
    -- Categorization
    tool_type TEXT,                          -- 'analysis', 'acquisition', 'pipeline', 'library', 'plugin', 'other'
    microscopy_relevance TEXT DEFAULT '[]',  -- JSON array of relevant techniques
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    github_checked_at TIMESTAMP             -- Last GitHub API check
);

CREATE INDEX IF NOT EXISTS idx_github_tools_full_name ON github_tools(full_name);
CREATE INDEX IF NOT EXISTS idx_github_tools_paper_count ON github_tools(paper_count DESC);
CREATE INDEX IF NOT EXISTS idx_github_tools_stars ON github_tools(stars DESC);
CREATE INDEX IF NOT EXISTS idx_github_tools_health ON github_tools(health_score DESC);

-- Junction table: which papers reference which GitHub tools
CREATE TABLE IF NOT EXISTS paper_github_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL,
    github_tool_id INTEGER NOT NULL,
    relationship TEXT DEFAULT 'uses',        -- 'introduces', 'uses', 'extends', 'benchmarks'
    context TEXT,                            -- Extracted sentence mentioning the tool
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (github_tool_id) REFERENCES github_tools(id),
    UNIQUE(paper_id, github_tool_id)
);

CREATE INDEX IF NOT EXISTS idx_pgt_paper ON paper_github_tools(paper_id);
CREATE INDEX IF NOT EXISTS idx_pgt_tool ON paper_github_tools(github_tool_id);
"""


# ============================================================================
# DATA REPOSITORIES - Updated with OMERO
# ============================================================================

REPOSITORY_PATTERNS = {
    'GitHub': (r'github\.com/([\w-]+/[\w.-]+?)(?:\.git|/(?:issues|wiki|releases|blob|tree|pull|actions|discussions)|$|\s|[,;)\]])', 'https://github.com/{}'),
    'GitLab': (r'gitlab\.com/([\w-]+/[\w.-]+?)(?:\.git|/(?:issues|wiki|releases|blob|tree|merge)|$|\s|[,;)\]])', 'https://gitlab.com/{}'),
    'Zenodo': (r'(?:zenodo\.org/records?/|10\.5281/zenodo\.)(\d+)', 'https://zenodo.org/record/{}'),
    'Figshare': (r'(?:figshare\.com/\S+/|10\.6084/m9\.figshare\.)(\d+)', 'https://figshare.com/articles/dataset/{}'),
    'Dryad': (r'(?:datadryad\.org/stash/dataset/doi:|10\.5061/dryad\.)([\w]+)', 'https://datadryad.org/stash/dataset/doi:10.5061/dryad.{}'),
    'OSF': (r'osf\.io/([\w]{5,})', 'https://osf.io/{}'),
    
    # OMERO - Added in v4.1
    'OMERO': (r'(?:omero\.[\w.]+/(?:webclient|webgateway|figure)/?\??(?:show=)?(?:dataset|image|project|screen|plate|well)[-=]?)(\d+)', 'https://idr.openmicroscopy.org/webclient/?show=image-{}'),
    'OMERO Public': (r'(?:publicomero|omero-[\w]+)\.[\w.]+/webclient/\?show=(\w+-\d+)', 'https://idr.openmicroscopy.org/webclient/?show={}'),
    
    # IDR (Image Data Resource - uses OMERO)
    'IDR': (r'(idr\d{4,})', 'https://idr.openmicroscopy.org/search/?query=Name:{}'),
    'IDR Image': (r'idr\.openmicroscopy\.org/webclient/\?show=image-(\d+)', 'https://idr.openmicroscopy.org/webclient/?show=image-{}'),
    'IDR Dataset': (r'idr\.openmicroscopy\.org/webclient/\?show=dataset-(\d+)', 'https://idr.openmicroscopy.org/webclient/?show=dataset-{}'),
    'IDR Project': (r'idr\.openmicroscopy\.org/webclient/\?show=project-(\d+)', 'https://idr.openmicroscopy.org/webclient/?show=project-{}'),
    
    'BioImage Archive': (r'(S-B(?:IAD|SST)\d+)', 'https://www.ebi.ac.uk/biostudies/bioimages/studies/{}'),
    'EMPIAR': (r'(EMPIAR-\d+)', 'https://www.ebi.ac.uk/empiar/{}'),
    'EMDB': (r'(EMD-\d+)', 'https://www.ebi.ac.uk/emdb/{}'),
    'PDB': (r'(?:rcsb\.org/structure/|pdb id:?\s*)(\w{4})', 'https://www.rcsb.org/structure/{}'),
    'Code Ocean': (r'codeocean\.com/capsule/([\w]+)', 'https://codeocean.com/capsule/{}'),
    'Mendeley Data': (r'(?:data\.mendeley\.com/datasets/|10\.17632/)([\w]+)', 'https://data.mendeley.com/datasets/{}'),
    'BioStudies': (r'(S-[\w]+-?\d+)', 'https://www.ebi.ac.uk/biostudies/studies/{}'),
    'SRA': (r'(SRR\d{6,}|SRP\d{6,}|PRJNA\d+)', 'https://www.ncbi.nlm.nih.gov/sra/{}'),
    'GEO': (r'(GSE\d+|GSM\d+)', 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={}'),
    'ArrayExpress': (r'(E-MTAB-\d+)', 'https://www.ebi.ac.uk/arrayexpress/experiments/{}'),
    'PRIDE': (r'(PXD\d+)', 'https://www.ebi.ac.uk/pride/archive/projects/{}'),
    
    # SSBD (Systems Science of Biological Dynamics)
    'SSBD': (r'ssbd\.riken\.jp/[\w/]*(\d+)', 'https://ssbd.riken.jp/database/{}'),
    
    # Electron Microscopy Public Image Archive
    'EMIAP': (r'(EMIAP-\d+)', 'https://www.ebi.ac.uk/emiap/{}'),
}


# ============================================================================
# FLUOROPHORES AND DYES - Comprehensive (including genetically encoded)
# ============================================================================

FLUOROPHORES = {
    # ===== NUCLEAR DYES =====
    'DAPI': [r'\bdapi\b'],
    'Hoechst 33342': ['hoechst 33342', 'hoechst33342'],
    'Hoechst 33258': ['hoechst 33258', 'hoechst33258'],
    'DRAQ5': ['draq5'],
    'DRAQ7': ['draq7'],
    'TO-PRO-3': ['to-pro-3', 'topro-3'],
    'SYTOX Green': ['sytox green'],
    'SYTOX Blue': ['sytox blue'],
    'SYTOX Orange': ['sytox orange'],
    'Propidium Iodide': ['propidium iodide', r'\bpi\b.*nuclear'],
    'Acridine Orange': ['acridine orange'],
    'SYTO': [r'\bsyto\s*\d+'],
    
    # ===== MEMBRANE/CYTOSKELETON =====
    'Phalloidin': ['phalloidin'],
    'WGA': [r'\bwga\b', 'wheat germ agglutinin'],
    # DiI, DiO, DiD, DiR - FULL MOLECULAR NAMES ONLY to avoid false positives
    # These short acronyms match too many common words (did, dio, etc.)
    'DiI': [
        r"1,1'-dioctadecyl-3,3,3',3'-tetramethylindocarbocyanine",
        r'dioctadecyl[- ]?tetramethyl[- ]?indocarbocyanine',
    ],
    'DiO': [
        r"3,3'-dioctadecyloxacarbocyanine",
        r'dioctadecyloxacarbocyanine',
    ],
    'DiD': [
        r"1,1'-dioctadecyl-3,3,3',3'-tetramethylindodicarbocyanine",
        r'dioctadecyl[- ]?tetramethyl[- ]?indodicarbocyanine',
    ],
    'DiR': [
        r"1,1'-dioctadecyl-3,3,3',3'-tetramethylindotricarbocyanine",
        r'dioctadecyl[- ]?tetramethyl[- ]?indotricarbocyanine',
    ],
    'CellMask': ['cellmask'],
    'FM Dyes': ['fm 1-43', 'fm 4-64', 'fm1-43', 'fm4-64', 'fm dye'],
    
    # ===== ORGANELLE TRACKERS =====
    'MitoTracker Green': ['mitotracker green'],
    'MitoTracker Red': ['mitotracker red', 'mitotracker cmxros'],
    'MitoTracker Deep Red': ['mitotracker deep red'],
    'MitoTracker Orange': ['mitotracker orange'],
    'LysoTracker Green': ['lysotracker green'],
    'LysoTracker Red': ['lysotracker red'],
    'LysoTracker Blue': ['lysotracker blue'],
    'LysoTracker Deep Red': ['lysotracker deep red'],
    'ER-Tracker Green': ['er-tracker green', 'ertracker green'],
    'ER-Tracker Red': ['er-tracker red', 'ertracker red'],
    'ER-Tracker Blue': ['er-tracker blue'],
    'Golgi-Tracker': ['golgi tracker', 'golgitracker'],
    'Tubulin Tracker': ['tubulin tracker', 'tubulintracker'],
    'CellROX': ['cellrox'],
    'TMRM': [r'\btmrm\b', 'tetramethylrhodamine methyl'],
    'TMRE': [r'\btmre\b', 'tetramethylrhodamine ethyl'],
    'JC-1': ['jc-1', 'jc1'],
    
    # ===== ALEXA FLUOR SERIES =====
    'Alexa 350': ['alexa.*350', 'alexa fluor 350', 'af350'],
    'Alexa 405': ['alexa.*405', 'alexa fluor 405', 'af405'],
    'Alexa 430': ['alexa.*430', 'alexa fluor 430'],
    'Alexa 488': ['alexa.*488', 'alexa fluor 488', 'af488'],
    'Alexa 514': ['alexa.*514', 'alexa fluor 514'],
    'Alexa 532': ['alexa.*532', 'alexa fluor 532'],
    'Alexa 546': ['alexa.*546', 'alexa fluor 546', 'af546'],
    'Alexa 555': ['alexa.*555', 'alexa fluor 555', 'af555'],
    'Alexa 568': ['alexa.*568', 'alexa fluor 568', 'af568'],
    'Alexa 594': ['alexa.*594', 'alexa fluor 594', 'af594'],
    'Alexa 610': ['alexa.*610', 'alexa fluor 610'],
    'Alexa 633': ['alexa.*633', 'alexa fluor 633', 'af633'],
    'Alexa 647': ['alexa.*647', 'alexa fluor 647', 'af647'],
    'Alexa 660': ['alexa.*660', 'alexa fluor 660'],
    'Alexa 680': ['alexa.*680', 'alexa fluor 680', 'af680'],
    'Alexa 700': ['alexa.*700', 'alexa fluor 700', 'af700'],
    'Alexa 750': ['alexa.*750', 'alexa fluor 750', 'af750'],
    'Alexa 790': ['alexa.*790', 'alexa fluor 790'],
    
    # ===== GREEN FLUORESCENT PROTEINS =====
    'GFP': [r'\bgfp\b', 'green fluorescent protein'],
    'EGFP': [r'\begfp\b', 'enhanced gfp', 'enhanced green fluorescent'],
    'eGFP': [r'\begfp\b'],
    'sfGFP': ['sfgfp', 'superfolder gfp'],
    'mGFP': ['mgfp', 'membrane gfp'],
    'mEGFP': ['megfp'],
    'AcGFP': ['acgfp'],
    'ZsGreen': ['zsgreen'],
    'Clover': [r'\bclover\b.*fluorescent'],
    'mClover': ['mclover', 'mclover3'],
    'mNeonGreen': ['mneongreen', 'mneon'],
    'NeonGreen': ['neongreen'],
    'mWasabi': ['mwasabi'],
    'Emerald': [r'\bemerald\b.*gfp'],
    
    # ===== RED FLUORESCENT PROTEINS =====
    'RFP': [r'\brfp\b', 'red fluorescent protein'],
    'mCherry': ['mcherry'],
    'tdTomato': ['tdtomato', 'td-tomato'],
    'dsRed': ['dsred', 'ds-red'],
    'mRFP': ['mrfp', 'mrfp1'],
    'TagRFP': ['tagrfp'],
    'TagRFP-T': ['tagrfp-t'],
    'mScarlet': ['mscarlet', 'mscarlet-i', 'mscarlet-h'],
    'mRuby': ['mruby', 'mruby2', 'mruby3'],
    'mKate': ['mkate', 'mkate2'],
    'mKO': ['mko', 'kusabira orange'],
    'mOrange': ['morange', 'morange2'],
    'mStrawberry': ['mstrawberry'],
    'mApple': ['mapple'],
    'mPlum': ['mplum'],
    'mRaspberry': ['mraspberry'],
    'mGrape': ['mgrape'],
    'mCherry2': ['mcherry2'],
    'FusionRed': ['fusionred'],
    'DsRed-Express': ['dsred-express', 'dsred express'],
    'DsRed-Monomer': ['dsred-monomer', 'dsred monomer'],
    
    # ===== CYAN FLUORESCENT PROTEINS =====
    'CFP': [r'\bcfp\b', 'cyan fluorescent protein'],
    'eCFP': ['ecfp', 'enhanced cfp'],
    'mCerulean': ['mcerulean', 'cerulean'],
    'mCerulean3': ['mcerulean3', 'cerulean3'],
    'mTurquoise': ['mturquoise', 'mturquoise2'],
    'SCFP': ['scfp'],
    'Cyan': [r'\bcyan\b.*fluorescent'],
    'AmCyan': ['amcyan'],
    
    # ===== YELLOW FLUORESCENT PROTEINS =====
    'YFP': [r'\byfp\b', 'yellow fluorescent protein'],
    'eYFP': ['eyfp', 'enhanced yfp'],
    'Venus': [r'\bvenus\b.*fluorescent', r'\bvenus\b.*protein'],
    'Citrine': ['citrine'],
    'YPet': ['ypet'],
    'mVenus': ['mvenus'],
    'SYFP': ['syfp', 'syfp2'],
    'mBanana': ['mbanana'],
    'PhiYFP': ['phiyfp'],
    
    # ===== BLUE FLUORESCENT PROTEINS =====
    'BFP': [r'\bbfp\b', 'blue fluorescent protein'],
    'eBFP': ['ebfp', 'ebfp2', 'enhanced bfp'],
    'mTagBFP': ['mtagbfp', 'mtagbfp2'],
    'TagBFP': ['tagbfp'],
    'Azurite': ['azurite'],
    'SBFP': ['sbfp', 'sbfp2'],
    'mKalama1': ['mkalama1'],
    
    # ===== FAR-RED / INFRARED FLUORESCENT PROTEINS =====
    'mKate2': ['mkate2'],
    'mCardinal': ['mcardinal'],
    'mMaroon': ['mmaroon'],
    'mNeptune': ['mneptune', 'mneptune2'],
    'iRFP': ['irfp', 'irfp670', 'irfp682', 'irfp702', 'irfp713', 'irfp720'],
    'miRFP': ['mirfp', 'mirfp670', 'mirfp703', 'mirfp720'],
    'smURFP': ['smurfp'],
    'IFP': [r'\bifp\b', 'infrared fluorescent'],
    
    # ===== PHOTOACTIVATABLE / PHOTOCONVERTIBLE =====
    'PA-GFP': ['pa-gfp', 'pagfp', 'photoactivatable gfp'],
    'PS-CFP2': ['ps-cfp2', 'pscfp2'],
    'Dendra': ['dendra', 'dendra2'],
    'Dronpa': ['dronpa'],
    'mEos': ['meos', 'meos2', 'meos3', 'meos4'],
    'mMaple': ['mmaple', 'mmaple2', 'mmaple3'],
    'Kaede': ['kaede'],
    'KikGR': ['kikgr'],
    'mClavGR2': ['mclavgr2'],
    'mIrisFP': ['mirisfp'],
    'Padron': ['padron'],
    'rsEGFP': ['rsegfp', 'rsegfp2'],
    'Dreiklang': ['dreiklang'],
    'mGeos': ['mgeos'],
    
    # ===== CALCIUM INDICATORS =====
    'GCaMP': ['gcamp'],
    'GCaMP3': ['gcamp3'],
    'GCaMP5': ['gcamp5'],
    'GCaMP6s': ['gcamp6s', 'gcamp6-s'],
    'GCaMP6m': ['gcamp6m', 'gcamp6-m'],
    'GCaMP6f': ['gcamp6f', 'gcamp6-f'],
    'GCaMP7s': ['gcamp7s', 'gcamp7-s'],
    'GCaMP7f': ['gcamp7f', 'gcamp7-f'],
    'GCaMP8s': ['gcamp8s', 'gcamp8-s'],
    'GCaMP8m': ['gcamp8m', 'gcamp8-m'],
    'GCaMP8f': ['gcamp8f', 'gcamp8-f'],
    'jGCaMP7': ['jgcamp7', 'jgcamp7s', 'jgcamp7f', 'jgcamp7b', 'jgcamp7c'],
    'jGCaMP8': ['jgcamp8', 'jgcamp8s', 'jgcamp8m', 'jgcamp8f'],
    'RCaMP': ['rcamp', 'rcamp1', 'rcamp2'],
    'jRCaMP': ['jrcamp', 'jrcamp1a', 'jrcamp1b'],
    'jRGECO': ['jrgeco', 'jrgeco1a', 'jrgeco1b'],
    'R-GECO': ['r-geco', 'rgeco'],
    'R-CaMP2': ['r-camp2', 'rcamp2'],
    'Fura-2': ['fura-2', 'fura2'],
    'Fluo-4': ['fluo-4', 'fluo4'],
    'Fluo-8': ['fluo-8', 'fluo8'],
    'Cal-520': ['cal-520', 'cal520'],
    'Cal-590': ['cal-590', 'cal590'],
    'Oregon Green BAPTA': ['oregon green bapta', 'ogb-1', 'ogb1'],
    'Rhod-2': ['rhod-2', 'rhod2'],
    'Indo-1': ['indo-1', 'indo1'],
    'Calcium Green': ['calcium green'],
    'Calcium Orange': ['calcium orange'],
    'Calcium Crimson': ['calcium crimson'],
    'X-Rhod-1': ['x-rhod-1', 'xrhod1'],
    
    # ===== VOLTAGE INDICATORS =====
    'ASAP1': ['asap1'],
    'ASAP2': ['asap2'],
    'ASAP3': ['asap3'],
    'Voltron': ['voltron', 'voltron1', 'voltron2'],
    'Archon1': ['archon1'],
    'Archon2': ['archon2'],
    'QuasAr': ['quasar', 'quasar1', 'quasar2', 'quasar3'],
    'Ace2N': ['ace2n'],
    'VARNAM': ['varnam'],
    'ArcLight': ['arclight'],
    'MacQ': ['macq'],
    'SomArchon': ['somarchon'],
    'paQuasAr': ['paquasar'],
    'FlicR1': ['flicr1'],
    
    # ===== NEUROTRANSMITTER SENSORS =====
    'iGluSnFR': ['iglusnfr', 'sf-iglusnfr'],
    'dLight': ['dlight', 'dlight1'],
    'GRAB-DA': ['grab-da', 'grabda'],
    'GRAB-NE': ['grab-ne', 'grabne'],
    'GRAB-5HT': ['grab-5ht', 'grab5ht'],
    'GRAB-ACh': ['grab-ach', 'grabach'],
    'GACh': ['gach'],
    'iAChSnFR': ['iachsnfr'],
    'iSeroSnFR': ['iserosnfr'],
    'FLEX sensors': ['flex sensor'],
    
    # ===== CYANINE DYES =====
    'Cy2': [r'\bcy2\b'],
    'Cy3': [r'\bcy3\b'],
    'Cy3.5': ['cy3.5'],
    'Cy5': [r'\bcy5\b'],
    'Cy5.5': ['cy5.5'],
    'Cy7': [r'\bcy7\b'],
    
    # ===== OTHER SYNTHETIC DYES =====
    'FITC': [r'\bfitc\b', 'fluorescein isothiocyanate'],
    'TRITC': [r'\btritc\b', 'tetramethylrhodamine'],
    'Texas Red': ['texas red', 'texasred'],
    'Rhodamine': ['rhodamine'],
    'Rhodamine 6G': ['rhodamine 6g'],
    'Rhodamine B': ['rhodamine b'],
    'Rhodamine 123': ['rhodamine 123'],
    'DyLight': ['dylight'],
    'CF Dye': ['cf dye', r'cf\s*\d{3}'],
    'CF488': ['cf488', 'cf 488'],
    'CF555': ['cf555', 'cf 555'],
    'CF568': ['cf568', 'cf 568'],
    'CF594': ['cf594', 'cf 594'],
    'CF633': ['cf633', 'cf 633'],
    'CF647': ['cf647', 'cf 647'],
    'CF680': ['cf680', 'cf 680'],
    'ATTO 488': ['atto 488', 'atto488'],
    'ATTO 532': ['atto 532', 'atto532'],
    'ATTO 565': ['atto 565', 'atto565'],
    'ATTO 590': ['atto 590', 'atto590'],
    'ATTO 594': ['atto 594', 'atto594'],
    'ATTO 633': ['atto 633', 'atto633'],
    'ATTO 647N': ['atto 647n', 'atto647n'],
    'ATTO 655': ['atto 655', 'atto655'],
    'ATTO 680': ['atto 680', 'atto680'],
    'ATTO 700': ['atto 700', 'atto700'],
    'Janelia Fluor 549': ['janelia fluor 549', 'jf549', 'jf 549'],
    'Janelia Fluor 646': ['janelia fluor 646', 'jf646', 'jf 646'],
    'Janelia Fluor 585': ['janelia fluor 585', 'jf585'],
    'Janelia Fluor 669': ['janelia fluor 669', 'jf669'],
    'SiR': ['sir-actin', 'sir-tubulin', 'sir-dna', 'silicon rhodamine', 'sir-'],
    'BODIPY': ['bodipy'],
    'Coumarin': ['coumarin'],
    'Pacific Blue': ['pacific blue'],
    'Pacific Orange': ['pacific orange'],
    'Pacific Green': ['pacific green'],
    'Marina Blue': ['marina blue'],
    'eFluor': ['efluor'],
    
    # ===== BRILLIANT VIOLET =====
    'BV421': ['bv421', 'brilliant violet 421'],
    'BV510': ['bv510', 'brilliant violet 510'],
    'BV605': ['bv605', 'brilliant violet 605'],
    'BV650': ['bv650', 'brilliant violet 650'],
    'BV711': ['bv711', 'brilliant violet 711'],
    'BV785': ['bv785', 'brilliant violet 785'],
    
    # ===== CONJUGATES =====
    'PE': [r'\bpe\b.*conjugat', 'phycoerythrin', r'pe-cy'],
    'PE-Cy5': ['pe-cy5'],
    'PE-Cy7': ['pe-cy7'],
    'APC': [r'\bapc\b.*conjugat', 'allophycocyanin'],
    'APC-Cy7': ['apc-cy7'],
    'PerCP': ['percp'],
    'PerCP-Cy5.5': ['percp-cy5.5'],
    
    # ===== CLICK CHEMISTRY =====
    'EdU': [r'\bedu\b', '5-ethynyl-2'],
    'BrdU': [r'\bbrdu\b', 'bromodeoxyuridine'],
    'Click-iT': ['click-it'],
    
    # ===== BIMOLECULAR FLUORESCENCE =====
    'Split-GFP': ['split-gfp', 'split gfp', 'gfp1-10', 'gfp11'],
    'BiFC': ['bifc', 'bimolecular fluorescence'],
    
    # ===== FRET PAIRS =====
    'CFP-YFP FRET': ['cfp.*yfp.*fret', 'yfp.*cfp.*fret'],
    'mTurquoise-Venus': ['mturquoise.*venus', 'venus.*mturquoise'],
    'Cerulean-Venus': ['cerulean.*venus'],
}


# ============================================================================
# MICROSCOPY TECHNIQUES - Complete list
# ============================================================================

MICROSCOPY_TECHNIQUES = {
    # Super-resolution - ONLY full expansions, NO abbreviations
    'STED': ['stimulated emission depletion'],
    'STORM': ['stochastic optical reconstruction microscopy'],
    'PALM': ['photoactivated localization microscopy'],
    'dSTORM': ['direct stochastic optical reconstruction'],
    'SIM': ['structured illumination microscopy'],
    'SMLM': ['single molecule localization microscopy'],
    'Super-Resolution': ['super-resolution microscopy', 'super resolution microscopy', 'nanoscopy'],
    'DNA-PAINT': ['dna-paint', 'points accumulation for imaging in nanoscale topography'],
    'MINFLUX': ['minflux nanoscopy', 'minimal photon fluxes'],
    'Expansion Microscopy': ['expansion microscopy'],
    'RESOLFT': ['reversible saturable optical fluorescence transitions'],
    'SOFI': ['super-resolution optical fluctuation imaging'],

    # Confocal & Light microscopy
    'Confocal': ['confocal microscopy', 'confocal laser scanning', 'laser scanning confocal microscopy'],
    'Two-Photon': ['two-photon microscopy', 'two photon microscopy', 'multiphoton microscopy'],
    'Three-Photon': ['three-photon microscopy', 'three photon microscopy'],
    'Light Sheet': ['light sheet microscopy', 'light-sheet microscopy', 'selective plane illumination microscopy'],
    'Lattice Light Sheet': ['lattice light sheet microscopy', 'lattice lightsheet microscopy'],
    'MesoSPIM': ['mesospim'],
    'Spinning Disk': ['spinning disk confocal', 'spinning-disk confocal'],
    'TIRF': ['total internal reflection fluorescence microscopy', 'total internal reflection fluorescence'],
    'Airyscan': ['airyscan microscopy', 'airyscan imaging'],
    'Widefield': ['widefield microscopy', 'wide-field microscopy', 'widefield fluorescence'],
    'Epifluorescence': ['epifluorescence microscopy', 'epi-fluorescence microscopy'],
    'Brightfield': ['brightfield microscopy', 'bright-field microscopy'],
    'Phase Contrast': ['phase contrast microscopy', 'phase-contrast microscopy'],
    'DIC': ['differential interference contrast microscopy', 'differential interference contrast'],
    'Darkfield': ['darkfield microscopy', 'dark-field microscopy'],

    # Electron Microscopy - ONLY full expansions
    'Cryo-EM': ['cryo-electron microscopy', 'cryogenic electron microscopy', 'cryo electron microscopy'],
    'Cryo-ET': ['cryo-electron tomography', 'cryogenic electron tomography'],
    'TEM': ['transmission electron microscopy'],
    'SEM': ['scanning electron microscopy'],
    'FIB-SEM': ['focused ion beam scanning electron microscopy', 'focused ion beam-scanning electron microscopy'],
    'Array Tomography': ['array tomography'],
    'Serial Block-Face SEM': ['serial block-face scanning electron microscopy', 'serial block face sem'],
    'Volume EM': ['volume electron microscopy'],
    'Immuno-EM': ['immuno-electron microscopy', 'immunoelectron microscopy'],
    'Negative Stain EM': ['negative stain electron microscopy', 'negative-stain electron microscopy'],

    # Functional imaging - ONLY full expansions
    'FRET': ['fluorescence resonance energy transfer', 'förster resonance energy transfer', 'forster resonance energy transfer'],
    'FLIM': ['fluorescence lifetime imaging microscopy', 'fluorescence lifetime imaging'],
    'FRAP': ['fluorescence recovery after photobleaching'],
    'FLIP': ['fluorescence loss in photobleaching'],
    'FCS': ['fluorescence correlation spectroscopy'],
    'FCCS': ['fluorescence cross-correlation spectroscopy'],
    'Calcium Imaging': ['calcium imaging'],
    'Voltage Imaging': ['voltage imaging', 'voltage-sensitive imaging'],
    'Optogenetics': ['optogenetics', 'optogenetic stimulation', 'optogenetic manipulation'],

    # Other techniques
    'Live Cell Imaging': ['live cell imaging', 'live-cell imaging'],
    'Intravital': ['intravital microscopy', 'intravital imaging'],
    'High-Content Screening': ['high-content screening', 'high content imaging'],
    'Deconvolution': ['deconvolution microscopy'],
    'Optical Sectioning': ['optical sectioning'],
    'Z-Stack': ['z-stack imaging', 'z-stack acquisition'],
    '3D Imaging': ['three-dimensional imaging', '3d microscopy'],
    '4D Imaging': ['four-dimensional imaging', '4d microscopy'],
    'Single Molecule': ['single molecule imaging', 'single-molecule imaging', 'single molecule microscopy'],
    'Single Particle': ['single particle analysis', 'single particle reconstruction'],
    'Holographic': ['holographic microscopy', 'digital holographic microscopy'],
    'OCT': ['optical coherence tomography'],
    'Photoacoustic': ['photoacoustic microscopy', 'photoacoustic imaging'],
    'AFM': ['atomic force microscopy'],
    'CLEM': ['correlative light and electron microscopy', 'correlative light-electron microscopy'],
    'Raman': ['raman microscopy', 'raman imaging'],
    'CARS': ['coherent anti-stokes raman scattering microscopy'],
    'SRS': ['stimulated raman scattering microscopy', 'stimulated raman scattering imaging'],
    'Second Harmonic': ['second harmonic generation microscopy', 'second harmonic imaging'],
    'Polarization': ['polarization microscopy', 'polarized light microscopy'],
    'Fluorescence Microscopy': ['fluorescence microscopy'],
    'Immunofluorescence': ['immunofluorescence microscopy', 'immunofluorescence staining'],
}


# ============================================================================
# IMAGE ANALYSIS SOFTWARE - Comprehensive
# ============================================================================

IMAGE_ANALYSIS_SOFTWARE = {
    # Open source
    'Fiji': ['fiji', r'\bimagej\b', 'image j'],
    'ImageJ': [r'\bimagej\b', 'image j', 'imagej2'],
    'CellProfiler': ['cellprofiler', 'cell profiler'],
    'ilastik': ['ilastik'],
    'QuPath': ['qupath'],
    'napari': ['napari'],
    'Icy': [r'\bicy\b.*software', r'\bicy\b.*analysis'],
    'OMERO': ['omero'],
    'BioImage Suite': ['bioimage suite'],
    'Vaa3D': ['vaa3d'],
    'BigDataViewer': ['bigdataviewer', 'big data viewer'],
    
    # Deep Learning
    'StarDist': ['stardist'],
    'Cellpose': ['cellpose'],
    'DeepCell': ['deepcell'],
    'NucleiSegNet': ['nucleisegnet'],
    'U-Net': ['u-net', 'unet'],
    'Mask R-CNN': ['mask r-cnn', 'mask rcnn'],
    'YOLOv': ['yolo'],
    'segment-anything': ['segment anything', 'sam model'],
    
    # Commercial
    'Imaris': ['imaris'],
    'Amira': ['amira'],
    'Arivis': ['arivis'],
    'Huygens': ['huygens'],
    'Volocity': ['volocity'],
    'NIS-Elements': ['nis-elements', 'nis elements'],
    'ZEN': ['zen blue', 'zen black', r'\bzen\b.*software', r'\bzen\b.*analysis'],
    'LAS X': ['las x', 'las-x', 'lasx'],
    'MetaMorph': ['metamorph'],
    'SlideBook': ['slidebook'],
    'CellSens': ['cellsens'],
    'HALO': [r'\bhalo\b.*analysis', 'halo ai'],
    'inForm': [r'\binform\b\s+(?:software|tissue|analysis\s+software|2\.\d|cell\s+analysis)', r'inForm\s+\d', r'\(inForm\)', r'Akoya.*\binform\b', r'\binform\b.*Akoya', r'\binform\b.*(?:phenotyp|tissue\s+finder|cell\s+segmentation)'],
    'Definiens': ['definiens'],
    'Visiopharm': ['visiopharm'],
    
    # Specialized
    'TrackMate': ['trackmate'],
    'MorphoGraphX': ['morphographx'],
    'IMOD': [r'\bimod\b'],
    'Chimera': [r'\bchimera\b(?!x)(?:\s+(?:software|visualization|molecular|structure|dock))', 'chimerax', r'ucsf\s*chimera'],
    'ChimeraX': ['chimerax'],
    'PyMOL': ['pymol'],
    'Dragonfly': ['dragonfly.*software'],
    'Aivia': ['aivia'],
    'MATLAB': ['matlab'],
    'Python': ['python.*image', 'scikit-image', 'skimage'],
    'R': [r'\bR\s+(?:software|package|statistical|programming|studio|version\s+\d)', r'\bR\b.*\b(?:ggplot|dplyr|tidyverse|cran|bioconductor)\b', r'(?:using|with|in)\s+R\s+(?:v\d|\()', 'bioconductor', r'R/Bioconductor'],
    
    # Deconvolution
    'AutoQuant': ['autoquant'],
    'DeconvolutionLab': ['deconvolutionlab'],
    'SVI Huygens': ['svi huygens'],
    
    # EM specific
    'RELION': ['relion'],
    'cryoSPARC': ['cryosparc'],
    'EMAN2': ['eman2'],
    'Scipion': ['scipion'],
    'SerialEM': ['serialem'],
    'Digital Micrograph': ['digital micrograph', 'gatan'],
}


# ============================================================================
# SAMPLE PREPARATION
# ============================================================================

SAMPLE_PREPARATION = {
    # Tissue Clearing
    'CLARITY': [r'\bclarity\b.*(?:clear|protocol|tissue|brain|organ|method|technique)', r'clarity-(?:based|optimized|compatible)', r'\bclarity\b.*transparent'],
    'iDISCO': ['idisco', 'idisco+'],
    'CUBIC': [r'\bcubic\b\s*(?:clear|protocol|reagent|method|technique|mount)', r'cubic-(?:based|optimized|compatible|r|l|x)', r'\bcubic\b\s+(?:transparent|brain\s+clear|organ\s+clear)'],
    'uDISCO': ['udisco'],
    '3DISCO': ['3disco'],
    'SHIELD': ['shield.*tissue', 'shield.*clearing'],
    'PACT': [r'\bpact\b.*clearing'],
    'PEGASOS': ['pegasos'],
    'eFLASH': ['eflash'],
    'Tissue Clearing': ['tissue clearing', 'optical clearing'],
    
    # Sectioning
    'Cryosectioning': ['cryosection', 'cryostat', 'frozen section'],
    'Vibratome': ['vibratome', 'vibrating microtome'],
    'Microtome': ['microtome'],
    'Ultramicrotome': ['ultramicrotome', 'ultra-microtome'],
    'Paraffin Embedding': ['paraffin.*section', 'paraffin.*embed', 'ffpe'],
    
    # Mounting
    'Whole Mount': ['whole mount', 'wholemount'],
    'Flat Mount': ['flat mount', 'flatmount'],
    
    # Histology
    'Immunohistochemistry': ['immunohistochemistry', r'\bihc\b'],
    'Immunofluorescence': ['immunofluorescence', r'\bif\b.*stain', 'immuno-fluorescence'],
    'H&E': ['h&e', 'hematoxylin.*eosin'],
    'TUNEL': ['tunel'],
    'In Situ Hybridization': ['in situ hybrid'],
    'FISH': [r'\bfish\b.*hybrid', 'fluorescence in situ'],
    'smFISH': ['smfish', 'single molecule fish'],
    'RNAscope': ['rnascope'],
    'MERFISH': ['merfish'],
    'seqFISH': ['seqfish'],
    
    # Cell culture
    'Cell Culture': ['cell culture', 'cultured cells'],
    'Primary Culture': ['primary culture', 'primary cells'],
    'Organoid': ['organoid'],
    'Spheroid': ['spheroid'],
    '3D Culture': ['3d culture', '3-d culture'],
    'Monolayer': ['monolayer'],
    'Co-culture': ['co-culture', 'coculture'],
    
    # Transfection/Transduction
    'Transfection': ['transfection', 'transfected'],
    'Transduction': ['transduction', 'transduced'],
    'Lentiviral': ['lentivir'],
    'Adenoviral': ['adenovir'],
    'AAV': [r'\baav\b', 'adeno-associated'],
    'Electroporation': ['electroporation'],
    'Lipofection': ['lipofection', 'lipofectamine'],
    
    # Gene editing
    'CRISPR': ['crispr', 'cas9', 'genome edit', 'gene edit'],
    'Knockdown': ['knockdown', 'knock-down', 'sirna', 'shrna'],
    'Knockout': ['knockout', 'knock-out'],
    
    # Sample prep
    'Fixation': ['fixation', 'fixed'],
    'PFA Fixation': ['pfa', 'paraformaldehyde'],
    'Glutaraldehyde': ['glutaraldehyde'],
    'Methanol Fixation': ['methanol.*fix'],
    'Permeabilization': ['permeabiliz'],
    'Blocking': ['blocking.*serum', 'blocking.*bsa'],
    'Antigen Retrieval': ['antigen retrieval', 'epitope retrieval'],
}


# ============================================================================
# ORGANISMS
# ============================================================================

# ORGANISMS - ONLY Latin names to avoid false positives from antibody mentions
# Common names like "mouse", "rabbit", "goat" often appear as antibody sources
# Latin names are reliable indicators of actual model organisms
ORGANISM_KEYWORDS = {
    'Mouse': [r'mus\s*musculus', r'm\.\s*musculus'],
    'Human': [r'homo\s*sapiens', r'h\.\s*sapiens'],
    'Rat': [r'rattus\s*norvegicus', r'r\.\s*norvegicus'],
    'Zebrafish': [r'danio\s*rerio', r'd\.\s*rerio'],
    'Drosophila': [r'drosophila\s*melanogaster', r'd\.\s*melanogaster'],
    'C. elegans': [r'caenorhabditis\s*elegans', r'c\.\s*elegans'],
    'Xenopus': [r'xenopus\s*laevis', r'xenopus\s*tropicalis', r'x\.\s*laevis', r'x\.\s*tropicalis'],
    'Chicken': [r'gallus\s*gallus', r'g\.\s*gallus'],
    'Pig': [r'sus\s*scrofa', r's\.\s*scrofa'],
    'Monkey': [r'macaca\s*mulatta', r'macaca\s*fascicularis', r'm\.\s*mulatta', r'm\.\s*fascicularis'],
    'Rabbit': [r'oryctolagus\s*cuniculus', r'o\.\s*cuniculus'],
    'Dog': [r'canis\s*familiaris', r'canis\s*lupus\s*familiaris', r'c\.\s*familiaris'],
    'Yeast': [r'saccharomyces\s*cerevisiae', r's\.\s*cerevisiae', r'schizosaccharomyces\s*pombe', r's\.\s*pombe'],
    'E. coli': [r'escherichia\s*coli', r'e\.\s*coli'],
    'Arabidopsis': [r'arabidopsis\s*thaliana', r'a\.\s*thaliana'],
    'Tobacco': [r'nicotiana\s*tabacum', r'nicotiana\s*benthamiana', r'n\.\s*tabacum', r'n\.\s*benthamiana'],
    'Maize': [r'zea\s*mays', r'z\.\s*mays'],
    'Rice': [r'oryza\s*sativa', r'o\.\s*sativa'],
    'Nematode': [r'caenorhabditis', r'c\.\s*elegans', r'c\.\s*briggsae'],
    'Fruit Fly': [r'drosophila\s*melanogaster', r'd\.\s*melanogaster'],
    'Frog': [r'xenopus\s*laevis', r'xenopus\s*tropicalis'],
    # Keep organoid/spheroid as they are specific terms
    'Organoid': [r'\borganoid\b'],
    'Spheroid': [r'\bspheroid\b'],
}


# ============================================================================
# CELL LINES
# ============================================================================

CELL_LINE_KEYWORDS = {
    'HeLa': [r'\bhela\b'],
    'HEK293': ['hek293', 'hek-293', 'hek 293'],
    'HEK293T': ['hek293t', '293t'],
    'U2OS': ['u2os', 'u-2 os'],
    'COS-7': ['cos-7', 'cos7'],
    'CHO': [r'\bcho\b.*cell'],
    'NIH 3T3': ['nih 3t3', 'nih3t3', '3t3'],
    'MCF7': ['mcf7', 'mcf-7'],
    'A549': ['a549'],
    'MDCK': ['mdck'],
    'Vero': [r'\bvero\b'],
    'PC12': ['pc12', 'pc-12'],
    'SH-SY5Y': ['sh-sy5y', 'shsy5y'],
    'iPSC': ['ipsc', 'induced pluripotent'],
    'ESC': [r'\besc\b', 'embryonic stem'],
    'MEF': [r'\bmef\b', 'mouse embryonic fibroblast'],
    'Primary Neurons': ['primary neuron', 'cultured neuron'],
    'Primary Hepatocytes': ['primary hepatocyte'],
    'Primary Cardiomyocytes': ['primary cardiomyocyte'],
}


# ============================================================================
# PROTOCOL SOURCES
# ============================================================================

PROTOCOL_PATTERNS = {
    'protocols.io': [
        r'(https?://(?:www\.)?protocols\.io/view/[\w-]+)',
        r'(https?://(?:www\.)?protocols\.io/[\w/-]+)',
        r'(dx\.doi\.org/10\.17504/protocols\.io\.[\w]+)',
    ],
    'Bio-protocol': [
        r'(https?://(?:www\.)?bio-protocol\.org/e\d+)',
        r'(https?://en\.bio-protocol\.org/[\w/-]+)',
    ],
    'JoVE': [
        r'(https?://(?:www\.)?jove\.com/(?:video|t|v)/\d+)',
        r'(https?://(?:www\.)?jove\.com/[\w/-]+)',
    ],
    'Nature Protocols': [
        r'(https?://(?:www\.)?nature\.com/nprot/[\w/-]+)',
        r'(https?://(?:www\.)?nature\.com/articles/nprot[\w.-]+)',
        r'(https?://(?:www\.)?nature\.com/articles/s41596[\w.-]+)',
    ],
    'STAR Protocols': [
        r'(https?://(?:www\.)?cell\.com/star-protocols/[\w/-]+)',
        r'(https?://(?:www\.)?sciencedirect\.com/science/article/pii/S2666166[\w]+)',
    ],
    'Current Protocols': [
        r'(https?://(?:www\.)?currentprotocols\.com/[\w/-]+)',
        r'(https?://onlinelibrary\.wiley\.com/doi/[\w./]+/cp[\w.]+)',
    ],
    'Cold Spring Harbor Protocols': [
        r'(https?://cshprotocols\.cshlp\.org/[\w/-]+)',
    ],
    'Methods in Molecular Biology': [
        r'(https?://link\.springer\.com/protocol/[\w./-]+)',
    ],
    'MethodsX': [
        r'(https?://(?:www\.)?sciencedirect\.com/science/article/pii/S2215[\w]+)',
    ],
}


# ============================================================================
# RRID PATTERNS
# ============================================================================

RRID_PATTERNS = [
    (r'RRID:\s*(AB_\d+)', 'antibody'),
    (r'RRID:\s*(SCR_\d+)', 'software'),
    (r'RRID:\s*(CVCL_[\w]+)', 'cell_line'),
    (r'RRID:\s*(Addgene_\d+)', 'plasmid'),
    (r'RRID:\s*(IMSR_[\w:]+)', 'organism'),
    (r'RRID:\s*(BDSC_\d+)', 'organism'),
    (r'RRID:\s*(ZFIN_[\w-]+)', 'organism'),
    (r'RRID:\s*(WB-STRAIN_[\w]+)', 'organism'),
    (r'RRID:\s*(MGI_[\w]+)', 'organism'),
    (r'RRID:\s*(MMRRC_[\w]+)', 'organism'),
    (r'RRID:\s*(ZIRC_[\w]+)', 'organism'),
    (r'RRID:\s*(DGRC_[\w]+)', 'organism'),
    (r'RRID:\s*(CGC_[\w]+)', 'organism'),
]


# ============================================================================
# ROR PATTERNS - Research Organization Registry
# ROR IDs are exactly 9 characters starting with 0, e.g., 052gg0110
# ============================================================================

ROR_PATTERNS = [
    # Standard ROR format: https://ror.org/0xxxxxxxx (starts with 0)
    r'ror\.org/(0[0-9a-z]{8})',
    r'ROR[:\s]+(0[0-9a-z]{8})',
    # Full URL format
    r'https?://ror\.org/(0[0-9a-z]{8})',
]


# ============================================================================
# ANTIBODY PATTERNS - Common antibody formats
# ============================================================================

ANTIBODY_PATTERNS = [
    # Company catalog numbers
    r'(?:Abcam|abcam)\s*[:#]?\s*(ab\d+)',
    r'(?:Cell\s*Signaling|CST)\s*[:#]?\s*(\d{4,5}[A-Z]?)',
    r'(?:Santa\s*Cruz)\s*[:#]?\s*(sc-\d+)',
    r'(?:Sigma|Sigma-Aldrich)\s*[:#]?\s*([A-Z]\d{4})',
    r'(?:Invitrogen|Thermo)\s*[:#]?\s*([A-Z]{2}-?\d{4,6})',
    r'(?:BD\s*Biosciences|BD)\s*[:#]?\s*(\d{6})',
    r'(?:BioLegend)\s*[:#]?\s*(\d{6})',
    r'(?:R&D\s*Systems)\s*[:#]?\s*((?:MAB|AF)\d+)',
    # Generic antibody mentions with catalog numbers
    r'(?:catalog|cat\.?\s*(?:no\.?|#)?)\s*[:#]?\s*([A-Za-z]{1,3}[-]?\d{4,8})',
    # Clone names (common format)
    r'(?:clone\s+)([A-Z0-9]{2,10}[-/][A-Z0-9]{1,5})',
]


# ============================================================================
# MICROSCOPE BRANDS - Actual microscope/imaging equipment manufacturers
# ============================================================================

MICROSCOPE_BRANDS = {
    'Zeiss': ['zeiss', 'carl zeiss'],
    'Leica': ['leica'],
    'Nikon': ['nikon'],
    'Olympus': ['olympus'],
    'Evident (Olympus)': ['evident'],
    'JEOL': ['jeol'],
    'Bruker': ['bruker'],
    'Andor': ['andor'],
    'Hamamatsu': ['hamamatsu'],
    'Yokogawa': ['yokogawa'],
    'Visitech': ['visitech'],
    'Till Photonics': ['till photonics'],
    '3i (Intelligent Imaging)': ['3i ', 'intelligent imaging'],
    'LaVision BioTec': ['lavision'],
    'Luxendo': ['luxendo'],
    'Applied Scientific Instrumentation': ['asi ', 'applied scientific'],
    'Prior': ['prior scientific'],
    'Sutter': ['sutter instrument'],
    'Coherent': ['coherent'],
    'Spectra-Physics': ['spectra-physics', 'spectra physics'],
    'Newport': ['newport'],
    'Thorlabs': ['thorlabs'],
    'Edmund Optics': ['edmund optics'],
    'Chroma': [r'\bchroma\b(?!tin|tograph|tic)', r'chroma\s+technology', r'chroma\s+filter', r'chroma\s+et\b'],
    'Semrock': ['semrock'],
    'Photometrics': ['photometrics'],
    'PCO': [r'\bpco\b'],
    'QImaging': ['qimaging'],
    'Roper': ['roper scientific'],
    'Princeton Instruments': ['princeton instruments'],
    'Abberior': ['abberior'],
    'PicoQuant': ['picoquant'],
    'Becker & Hickl': ['becker.*hickl', 'b&h'],
}


# ============================================================================
# REAGENT SUPPLIERS - Companies that sell reagents, not microscope equipment
# ============================================================================

REAGENT_SUPPLIERS = {
    'Thermo Fisher': ['thermo fisher', 'thermofisher', 'life technologies', 'invitrogen', 'gibco', 'molecular probes'],
    'PerkinElmer': ['perkinelmer', 'perkin elmer'],
    'Molecular Devices': ['molecular devices'],
    'Miltenyi': ['miltenyi biotec', r'\bmiltenyi\b'],
    'Sigma-Aldrich': ['sigma-aldrich', 'sigma aldrich', r'\bsigma\b.*(?:catalog|cat\.?\s*#|product|aldrich)'],
    'Merck': [r'\bmerck\b.*(?:millipore|chemicals?|reagent)', 'emd millipore'],
    'Abcam': [r'\babcam\b'],
    'Cell Signaling Technology': ['cell signaling technology', r'\bcst\b.*(?:antibod|catalog)'],
    'Bio-Rad': ['bio-rad', 'biorad'],
    'Roche': [r'\broche\b.*(?:diagnos|applied|reagent|lightcycler)'],
    'Qiagen': ['qiagen'],
    'New England Biolabs': ['new england biolabs', r'\bneb\b.*(?:enzyme|kit|reagent)'],
    'Takara Bio': ['takara bio', 'clontech'],
    'BD Biosciences': ['bd biosciences', 'becton dickinson'],
    'Jackson ImmunoResearch': ['jackson immunoresearch'],
    'Vector Laboratories': ['vector laboratories'],
    'Santa Cruz Biotechnology': ['santa cruz biotechnology'],
    'Enzo Life Sciences': ['enzo life sciences'],
    'Tocris': [r'\btocris\b'],
    'Corning': [r'\bcorning\b.*(?:flask|plate|dish|matrigel|transwell)'],
    'R&D Systems': ['r&d systems'],
    'BioLegend': ['biolegend'],
    'Promega': ['promega'],
    'Agilent': ['agilent'],
}


# ============================================================================
# MICROSCOPE MODELS
# ============================================================================

MICROSCOPE_MODELS = {
    # Zeiss
    'LSM 510': ['lsm 510', 'lsm510'],
    'LSM 700': ['lsm 700', 'lsm700'],
    'LSM 710': ['lsm 710', 'lsm710'],
    'LSM 780': ['lsm 780', 'lsm780'],
    'LSM 800': ['lsm 800', 'lsm800'],
    'LSM 880': ['lsm 880', 'lsm880'],
    'LSM 900': ['lsm 900', 'lsm900'],
    'LSM 980': ['lsm 980', 'lsm980'],
    'Elyra': ['elyra'],
    'Elyra 7': ['elyra 7'],
    'Lightsheet Z.1': ['lightsheet z.1', 'lightsheet z1'],
    'Lightsheet 7': ['lightsheet 7'],
    'Celldiscoverer 7': ['celldiscoverer'],
    'Axio Observer': ['axio observer'],
    'Axio Imager': ['axio imager'],
    'Axiovert': ['axiovert'],
    'Axioskop': ['axioskop'],
    'Observer 7': ['observer 7', 'observer.z1'],
    
    # Leica
    'SP5': ['sp5', 'tcs sp5'],
    'SP8': ['sp8', 'tcs sp8', 'stellaris'],
    'Stellaris': ['stellaris 5', 'stellaris 8'],
    'STED 3X': ['sted 3x'],
    'THUNDER': ['thunder imager'],
    'DMi8': ['dmi8'],
    'DM6': ['dm6'],
    'DM IL': ['dm il'],
    
    # Nikon
    'A1': ['nikon a1', 'a1r', 'a1 confocal'],
    'AX': ['nikon ax'],
    'Ti': ['ti-e', 'ti2', 'eclipse ti'],
    'Ti2': ['ti2-e', 'ti2-a'],
    'N-SIM': ['n-sim', 'nsim'],
    'N-STORM': ['n-storm', 'nstorm'],
    'CSU-W1': ['csu-w1'],
    'CSU-X1': ['csu-x1'],
    
    # Olympus
    'FV1000': ['fv1000', 'fv 1000', 'fluoview 1000'],
    'FV1200': ['fv1200', 'fv 1200'],
    'FV3000': ['fv3000', 'fv 3000', 'fluoview 3000'],
    'SpinSR': ['spinsr'],
    'IX73': ['ix73'],
    'IX83': ['ix83'],
    'BX63': ['bx63'],
    'VS120': ['vs120'],
    
    # Electron Microscopes
    'Titan': ['titan krios', 'titan halo'],
    'Glacios': ['glacios'],
    'Talos': ['talos'],
    'Tecnai': ['tecnai'],
    'CM200': ['cm200'],
    'JEM-1400': ['jem-1400', 'jem1400'],
    'JEM-2100': ['jem-2100', 'jem2100'],
    
    # Light Sheet specific
    'MesoSPIM': ['mesospim'],
    'diSPIM': ['dispim', 'di-spim'],
    'iSPIM': ['ispim'],
    'OpenSPIM': ['openspim'],
    'UltraMicroscope': ['ultramicroscope'],
    'SmartSPIM': ['smartspim'],
}


# ============================================================================
# IMAGE ACQUISITION SOFTWARE
# ============================================================================

IMAGE_ACQUISITION_SOFTWARE = {
    'ZEN': [r'\bzen\b.*acquisition', r'\bzen\b.*capture', 'zen blue', 'zen black'],
    'NIS-Elements': ['nis-elements', 'nis elements'],
    'LAS X': ['las x', 'las-x', 'lasx', 'leica.*las'],
    'MetaMorph': ['metamorph'],
    'SlideBook': ['slidebook'],
    'CellSens': ['cellsens'],
    'MicroManager': ['micro-manager', 'micromanager', r'Î¼manager'],
    'Volocity Acquisition': ['volocity.*acquisition'],
    'FluoView': ['fluoview.*software'],
    'Prairie View': ['prairie.*view'],
    'ScanImage': ['scanimage'],
    'ThorImage': ['thorimage'],
    'Imspector': ['imspector'],
    'SymPhoTime': ['symphotime'],
    'HCImage': ['hcimage'],
    'CellReporterXpress': ['cellreporterxpress'],
    'Harmony': ['harmony.*software'],
    'Columbus': ['columbus.*software'],
    'Opera Phenix': ['opera phenix'],
    'ImageXpress': ['imagexpress'],
    'IN Cell': ['in cell.*analyzer'],
    'ArrayScan': ['arrayscan'],
}


# ============================================================================
# SCRAPER CLASS
# ============================================================================

class MicroHubScraperV5:
    """Paper scraper with CITATIONS, full text, AFFILIATIONS, and comprehensive extraction."""

    def __init__(self, db_path: str = 'microhub.db', email: str = None,
                 llm_enrich: bool = False, llm_api_key: str = None):
        self.db_path = db_path
        self.email = email or 'microhub@example.com'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'MicroHub/5.0 (Microscopy Database; mailto:{self.email})'
        })

        # LLM enrichment settings
        self.llm_enrich = llm_enrich
        self.llm_api_key = llm_api_key

        # Deduplication sets
        self.known_dois: Set[str] = set()
        self.known_pmids: Set[str] = set()
        self.seen_urls: Set[str] = set()  # For URL deduplication

        # Stats
        self.stats = {
            'found': 0,
            'duplicates_skipped': 0,
            'saved': 0,
            'errors': 0,
            'api_calls': 0,
            'full_text_fetched': 0,
            'citations_fetched': 0,
            'with_methods': 0,
            'with_figures': 0,
            'with_protocols': 0,
            'with_github': 0,
            'with_repos': 0,
            'with_rrids': 0,
            'with_rors': 0,
            'with_antibodies': 0,
            'with_affiliations': 0,  # NEW in v5.0
            'llm_enriched': 0,
            'skipped_no_tags': 0,
        }

        self._init_db()
        self._load_known()

    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        conn.executescript(DB_INIT)
        conn.executescript(DB_SCHEMA)
        
        # Add missing columns if they don't exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(papers)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        new_cols = [
            ('citation_source', 'TEXT'),
            ('citations_updated_at', 'TIMESTAMP'),
            ('semantic_scholar_id', 'TEXT'),
            ('influential_citation_count', 'INTEGER DEFAULT 0'),
            ('cell_lines', 'TEXT DEFAULT "[]"'),
            ('imaging_modalities', 'TEXT DEFAULT "[]"'),
            ('staining_methods', 'TEXT DEFAULT "[]"'),
            ('lasers', 'TEXT DEFAULT "[]"'),
            ('detectors', 'TEXT DEFAULT "[]"'),
            ('objectives', 'TEXT DEFAULT "[]"'),
            ('filters', 'TEXT DEFAULT "[]"'),
            ('embedding_methods', 'TEXT DEFAULT "[]"'),
            ('fixation_methods', 'TEXT DEFAULT "[]"'),
            ('mounting_media', 'TEXT DEFAULT "[]"'),
            ('affiliations', 'TEXT DEFAULT "[]"'),  # NEW in v5.0
            ('has_affiliations', 'BOOLEAN DEFAULT 0'),  # NEW in v5.0
        ]
        
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE papers ADD COLUMN {col_name} {col_type}")
                except:
                    pass
        
        conn.commit()
        conn.close()

    def _get_conn(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.execute("PRAGMA busy_timeout = 60000")
        return conn

    def _load_known(self):
        """Load known DOIs and PMIDs."""
        conn = self._get_conn()
        
        cursor = conn.execute("SELECT doi FROM papers WHERE doi IS NOT NULL")
        self.known_dois = {row[0].lower() for row in cursor if row[0]}
        
        cursor = conn.execute("SELECT pmid FROM papers WHERE pmid IS NOT NULL")
        self.known_pmids = {row[0] for row in cursor if row[0]}
        
        conn.close()
        logger.info(f"Loaded {len(self.known_dois):,} DOIs, {len(self.known_pmids):,} PMIDs")

    def _is_duplicate(self, doi: str, pmid: str) -> bool:
        """Check if paper already exists."""
        if doi and doi.lower() in self.known_dois:
            return True
        if pmid and pmid in self.known_pmids:
            return True
        return False

    # ========== CITATION FETCHING (with retry logic) ==========

    def fetch_citations_semantic_scholar(self, doi: str = None, pmid: str = None) -> Dict:
        """Fetch citation count from Semantic Scholar API with retry logic."""
        try:
            if doi:
                url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
            elif pmid:
                url = f"https://api.semanticscholar.org/graph/v1/paper/PMID:{pmid}"
            else:
                return {}

            params = {'fields': 'citationCount,influentialCitationCount,paperId'}

            # Manual retry with exponential backoff
            for attempt in range(MAX_RETRIES):
                try:
                    response = self.session.get(url, params=params, timeout=15)
                    self.stats['api_calls'] += 1
                    time.sleep(0.1)  # Rate limit: 100 requests per 5 minutes

                    if response.status_code == 200:
                        data = response.json()
                        return {
                            'citation_count': data.get('citationCount', 0),
                            'influential_citation_count': data.get('influentialCitationCount', 0),
                            'semantic_scholar_id': data.get('paperId'),
                            'source': 'semantic_scholar',
                        }
                    elif response.status_code == 404:
                        return {}
                    elif response.status_code == 429:  # Rate limited
                        delay = min(RETRY_BASE_DELAY * (2 ** (attempt + 2)), RETRY_MAX_DELAY)
                        logger.debug(f"Semantic Scholar rate limited, waiting {delay:.1f}s")
                        time.sleep(delay)
                        continue
                    else:
                        return {}

                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < MAX_RETRIES - 1:
                        delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                        logger.debug(f"Semantic Scholar retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s")
                        time.sleep(delay)
                    else:
                        logger.debug(f"Semantic Scholar failed after {MAX_RETRIES} retries: {e}")
                        return {}

            return {}

        except Exception as e:
            logger.debug(f"Semantic Scholar error: {e}")
            return {}

    def fetch_crossref_full_metadata(self, doi: str) -> Dict:
        """
        Fetch comprehensive metadata from CrossRef API.

        Extracts:
        - Citation count
        - Links (data repositories, GitHub, etc.)
        - Subjects/categories
        - Funder information
        - License
        - Abstract (if available)
        """
        if not doi:
            return {}

        for attempt in range(MAX_RETRIES):
            try:
                url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
                headers = {'User-Agent': f'MicroHub/5.0 (mailto:{self.email})'}

                response = self.session.get(url, headers=headers, timeout=15)
                self.stats['api_calls'] += 1
                time.sleep(0.05)  # Polite rate limiting

                if response.status_code == 200:
                    data = response.json()
                    message = data.get('message', {})

                    result = {
                        'citation_count': message.get('is-referenced-by-count', 0),
                        'source': 'crossref',
                    }

                    # Extract links - data repositories, GitHub, etc.
                    links = message.get('link', [])
                    extracted_links = []
                    github_urls = []
                    data_repos = []

                    for link in links:
                        link_url = link.get('URL', '')
                        content_type = link.get('content-type', '')

                        if link_url:
                            extracted_links.append({
                                'url': link_url,
                                'type': content_type,
                            })

                            # Check for GitHub
                            if 'github.com' in link_url.lower():
                                github_urls.append(link_url)

                            # Check for data repositories
                            data_repo_domains = [
                                'zenodo.org', 'figshare.com', 'dryad', 'osf.io',
                                'dataverse', 'mendeley', 'ebi.ac.uk', 'ncbi.nlm.nih.gov/geo',
                                'biostudies', 'empiar', 'idr.openmicroscopy'
                            ]
                            if any(domain in link_url.lower() for domain in data_repo_domains):
                                data_repos.append(link_url)

                    # Extract from reference/relation fields
                    relations = message.get('relation', {})
                    for rel_type, rel_items in relations.items():
                        if isinstance(rel_items, list):
                            for item in rel_items:
                                item_url = item.get('id', '') if isinstance(item, dict) else str(item)
                                if item_url.startswith('http'):
                                    if 'github.com' in item_url.lower():
                                        github_urls.append(item_url)
                                    elif any(d in item_url.lower() for d in ['zenodo', 'figshare', 'dryad', 'osf.io', 'dataverse']):
                                        data_repos.append(item_url)

                    # Check resource link
                    resource_link = message.get('resource', {})
                    if isinstance(resource_link, dict):
                        primary_url = resource_link.get('primary', {}).get('URL', '')
                        if primary_url:
                            extracted_links.append({'url': primary_url, 'type': 'primary'})

                    if github_urls:
                        result['github_urls'] = list(set(github_urls))
                    if data_repos:
                        result['data_repositories'] = list(set(data_repos))
                    if extracted_links:
                        result['links'] = extracted_links

                    # Extract subjects/categories
                    subjects = message.get('subject', [])
                    if subjects:
                        result['subjects'] = subjects

                    # Extract funder information
                    funders = message.get('funder', [])
                    if funders:
                        result['funders'] = [
                            {
                                'name': f.get('name', ''),
                                'doi': f.get('DOI', ''),
                                'award': f.get('award', []),
                            }
                            for f in funders
                        ]

                    # Extract license
                    licenses = message.get('license', [])
                    if licenses:
                        result['license'] = licenses[0].get('URL', '')

                    # Extract abstract if available
                    abstract = message.get('abstract', '')
                    if abstract:
                        # Clean HTML tags
                        abstract = re.sub(r'<[^>]+>', '', abstract)
                        result['abstract'] = abstract

                    return result

                elif response.status_code == 429:  # Rate limited
                    delay = min(RETRY_BASE_DELAY * (2 ** (attempt + 2)), RETRY_MAX_DELAY)
                    logger.debug(f"CrossRef rate limited, waiting {delay:.1f}s")
                    time.sleep(delay)
                    continue
                return {}

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    logger.debug(f"CrossRef retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s")
                    time.sleep(delay)
                else:
                    logger.debug(f"CrossRef failed after {MAX_RETRIES} retries: {e}")
                    return {}

            except Exception as e:
                logger.debug(f"CrossRef error: {e}")
                return {}

        return {}

    def fetch_citations_crossref(self, doi: str) -> Dict:
        """Fetch citation count from CrossRef API (wrapper for backward compatibility)."""
        result = self.fetch_crossref_full_metadata(doi)
        return {
            'citation_count': result.get('citation_count', 0),
            'source': result.get('source'),
        }
    
    def fetch_citations(self, doi: str = None, pmid: str = None) -> Dict:
        """Fetch citations from best available source."""
        # Try Semantic Scholar first (better data)
        result = self.fetch_citations_semantic_scholar(doi, pmid)
        if result and result.get('citation_count', 0) > 0:
            self.stats['citations_fetched'] += 1
            return result
        
        # Fall back to CrossRef
        if doi:
            result = self.fetch_citations_crossref(doi)
            if result and result.get('citation_count', 0) > 0:
                self.stats['citations_fetched'] += 1
                return result
        
        return {'citation_count': 0, 'source': None}

    # ========== URL VALIDATION ==========
    
    def validate_url(self, url: str, timeout: int = 10) -> bool:
        """Check if a URL is valid and accessible."""
        if not url or not url.startswith('http'):
            return False
            
        # Skip validation for known-good domains
        trusted_domains = [
            'github.com', 'zenodo.org', 'figshare.com', 'protocols.io',
            'doi.org', 'nature.com', 'cell.com', 'nih.gov', 'ncbi.nlm.nih.gov',
            'ebi.ac.uk', 'openmicroscopy.org', 'gitlab.com', 'osf.io',
        ]
        
        parsed = urlparse(url)
        if any(d in parsed.netloc for d in trusted_domains):
            return True
        
        # Actually check unknown URLs
        try:
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except:
            return False

    def normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates."""
        if not url:
            return ''

        # Remove trailing slashes, .git, etc.
        url = url.rstrip('/')
        url = re.sub(r'\.git$', '', url)
        url = re.sub(r'#.*$', '', url)  # Remove fragments
        url = re.sub(r'\?.*$', '', url)  # Remove query params for dedup

        return url.lower()

    def _extract_github_full_name(self, url: str) -> Optional[str]:
        """Extract owner/repo from GitHub URL."""
        if not url:
            return None

        # Match patterns like github.com/owner/repo
        match = re.search(r'github\.com/([^/]+)/([^/\s?#]+)', url, re.IGNORECASE)
        if match:
            owner = match.group(1)
            repo = match.group(2).rstrip('.git')
            # Skip non-repo paths
            if owner.lower() in ('topics', 'search', 'explore', 'settings', 'notifications'):
                return None
            return f"{owner}/{repo}"
        return None

    # ========== EXTRACTION METHODS ==========
    
    def extract_from_patterns(self, text: str, patterns_dict: Dict) -> List[str]:
        """Extract matches from text using pattern dictionary."""
        if not text:
            return []
        text_lower = text.lower()
        found = []
        for name, patterns in patterns_dict.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    found.append(name)
                    break
        return list(set(found))

    def extract_microscopy_techniques(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, MICROSCOPY_TECHNIQUES)

    def extract_microscope_brands(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, MICROSCOPE_BRANDS)

    def extract_reagent_suppliers(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, REAGENT_SUPPLIERS)

    def extract_microscope_models(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, MICROSCOPE_MODELS)

    def extract_image_analysis_software(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, IMAGE_ANALYSIS_SOFTWARE)

    def extract_image_acquisition_software(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, IMAGE_ACQUISITION_SOFTWARE)

    def extract_sample_preparation(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, SAMPLE_PREPARATION)

    def extract_fluorophores(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, FLUOROPHORES)

    def extract_organisms(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, ORGANISM_KEYWORDS)

    def extract_cell_lines(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, CELL_LINE_KEYWORDS)

    def extract_protocols(self, text: str) -> List[Dict]:
        """Extract protocol references with URL validation."""
        protocols = []
        seen_urls = set()

        for source, patterns in PROTOCOL_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    url = match.group(1) if match.groups() else match.group(0)
                    
                    if not url.startswith('http'):
                        continue
                    
                    # Normalize and dedupe
                    norm_url = self.normalize_url(url)
                    if norm_url in seen_urls:
                        continue
                    seen_urls.add(norm_url)
                    
                    # Clean up URL
                    url = url.rstrip('.,;:)')
                    
                    protocols.append({
                        'source': source,
                        'url': url,
                        'name': source,
                    })

        return protocols

    def extract_repositories(self, text: str) -> Tuple[List[Dict], Optional[str]]:
        """Extract data repository links with deduplication."""
        repos = []
        github_url = None
        seen_urls = set()

        for name, (pattern, template) in REPOSITORY_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                captured = match.group(1)
                
                # Clean up captured value
                captured = captured.rstrip('.,;:)')
                
                # Build URL
                if name == 'GitHub' or name == 'GitLab':
                    # Clean repo path
                    repo_path = captured.rstrip('/')
                    url = template.format(repo_path)
                else:
                    url = template.format(captured)
                
                # Normalize and dedupe
                norm_url = self.normalize_url(url)
                if norm_url in seen_urls:
                    continue
                seen_urls.add(norm_url)
                
                if name == 'GitHub' and not github_url:
                    github_url = url
                
                repos.append({
                    'name': name,
                    'url': url,
                    'id': captured,
                })

        return repos, github_url

    def extract_rrids(self, text: str) -> List[Dict]:
        """Extract RRIDs."""
        rrids = []
        seen = set()

        for pattern, rtype in RRID_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                rrid_id = f"RRID:{match.group(1)}"
                if rrid_id not in seen:
                    seen.add(rrid_id)
                    rrids.append({
                        'id': rrid_id,
                        'type': rtype,
                        'url': f'https://scicrunch.org/resolver/{rrid_id}',
                    })

        return rrids

    def extract_rors(self, text: str) -> List[Dict]:
        """Extract ROR (Research Organization Registry) identifiers."""
        rors = []
        seen = set()

        for pattern in ROR_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                ror_id = match.group(1)
                if ror_id not in seen:
                    seen.add(ror_id)
                    rors.append({
                        'id': ror_id,
                        'url': f'https://ror.org/{ror_id}',
                        'source': 'fulltext',
                    })

        return rors

    def extract_antibodies(self, text: str, rrids: List[Dict] = None) -> List[Dict]:
        """Extract antibody information from text and RRIDs."""
        antibodies = []
        seen = set()

        # First, extract antibody RRIDs if provided
        if rrids:
            for rrid in rrids:
                if rrid.get('type') == 'antibody':
                    ab_id = rrid.get('id', '')
                    if ab_id and ab_id not in seen:
                        seen.add(ab_id)
                        antibodies.append({
                            'id': ab_id,
                            'source': 'RRID',
                            'url': rrid.get('url', ''),
                        })

        # Extract antibodies from text patterns
        for pattern in ANTIBODY_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                ab_id = match.group(1)
                if ab_id and ab_id not in seen:
                    seen.add(ab_id)
                    # Try to determine source from context
                    context = text[max(0, match.start()-50):match.end()+50].lower()
                    source = 'unknown'
                    if 'abcam' in context:
                        source = 'Abcam'
                    elif 'cell signaling' in context or 'cst' in context:
                        source = 'Cell Signaling'
                    elif 'santa cruz' in context:
                        source = 'Santa Cruz'
                    elif 'sigma' in context:
                        source = 'Sigma-Aldrich'
                    elif 'invitrogen' in context or 'thermo' in context:
                        source = 'Invitrogen/Thermo'
                    elif 'bd bio' in context:
                        source = 'BD Biosciences'
                    elif 'biolegend' in context:
                        source = 'BioLegend'
                    elif 'r&d' in context:
                        source = 'R&D Systems'

                    antibodies.append({
                        'id': ab_id,
                        'source': source,
                        'url': '',
                    })

        return antibodies

    # ========== GITHUB TOOL TRACKING ==========

    def extract_all_github_urls(self, text: str) -> List[Dict]:
        """Extract ALL GitHub URLs from text with context about how they're referenced."""
        github_refs = []
        seen_repos = set()
        
        # Match github.com/owner/repo patterns
        pattern = r'(?:https?://)?github\.com/([\w.-]+)/([\w.-]+?)(?:\.git|/(?:issues|wiki|releases|blob|tree|pull|actions|discussions|archive|raw|commit|compare)[\w/.-]*|/?\s|/?\)|/?,|/?;|/?$)'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            owner = match.group(1).rstrip('.')
            repo = match.group(2).rstrip('.')
            full_name = f"{owner}/{repo}".lower()
            
            # Skip common false positives
            if owner.lower() in ('topics', 'features', 'about', 'pricing', 'login', 'signup', 'explore', 'marketplace', 'settings', 'notifications'):
                continue
            if repo.lower() in ('issues', 'pulls', 'actions', 'projects', 'wiki', 'security', 'pulse', 'community'):
                continue
            
            if full_name in seen_repos:
                continue
            seen_repos.add(full_name)
            
            # Extract surrounding context (sentence mentioning the tool)
            start = max(0, match.start() - 150)
            end = min(len(text), match.end() + 150)
            context = text[start:end].strip()
            # Clean to approximate sentence
            context = re.sub(r'^.*?(?<=[.!?]\s)', '', context)
            context = re.sub(r'(?<=[.!?])\s.*$', '', context)
            
            # Determine relationship based on context
            relationship = self._classify_github_relationship(context, full_name)
            
            url = f"https://github.com/{owner}/{repo}"
            github_refs.append({
                'url': url,
                'owner': owner,
                'repo_name': repo,
                'full_name': f"{owner}/{repo}",
                'relationship': relationship,
                'context': context[:300] if context else '',
            })
        
        return github_refs

    def _classify_github_relationship(self, context: str, repo_name: str) -> str:
        """Classify how a paper relates to a GitHub tool based on context."""
        ctx_lower = context.lower()
        
        # Signals the paper introduces/presents the tool
        introduce_signals = [
            'we developed', 'we present', 'we introduce', 'we created',
            'we built', 'we designed', 'we implemented', 'our tool',
            'our software', 'our package', 'our pipeline', 'our framework',
            'is available at', 'source code is available', 'code is available',
            'can be downloaded from', 'freely available at',
            'we release', 'we open-source',
        ]
        
        # Signals the paper extends/builds upon the tool
        extend_signals = [
            'we extended', 'we modified', 'we adapted', 'we forked',
            'building on', 'built upon', 'extension of', 'based on.*github',
        ]
        
        # Signals the paper benchmarks/compares tools
        benchmark_signals = [
            'we compared', 'we benchmarked', 'we evaluated', 'we tested',
            'comparison of', 'benchmark', 'performance of',
        ]
        
        for signal in introduce_signals:
            if re.search(signal, ctx_lower):
                return 'introduces'
        
        for signal in extend_signals:
            if re.search(signal, ctx_lower):
                return 'extends'
                
        for signal in benchmark_signals:
            if re.search(signal, ctx_lower):
                return 'benchmarks'
        
        return 'uses'

    def fetch_github_repo_metrics(self, repo_url: str, github_token: str = None) -> Optional[Dict]:
        """Fetch repository metrics from the GitHub API."""
        # Extract owner/repo from URL
        match = re.search(r'github\.com/([\w.-]+)/([\w.-]+)', repo_url)
        if not match:
            return None
        
        owner = match.group(1)
        repo = match.group(2).rstrip('.git')
        
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        try:
            # Main repo info
            resp = self.session.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 404:
                return {'exists': False, 'owner': owner, 'repo_name': repo}
            
            if resp.status_code == 403:
                # Rate limited
                logger.warning(f"GitHub API rate limited for {owner}/{repo}")
                return None
                
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            
            metrics = {
                'exists': True,
                'owner': owner,
                'repo_name': repo,
                'full_name': data.get('full_name', f'{owner}/{repo}'),
                'description': (data.get('description') or '')[:500],
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'open_issues': data.get('open_issues_count', 0),
                'watchers': data.get('subscribers_count', 0),
                'created_date': data.get('created_at'),
                'last_push_date': data.get('pushed_at'),
                'default_branch': data.get('default_branch', 'main'),
                'license': data.get('license', {}).get('spdx_id') if data.get('license') else None,
                'language': data.get('language'),
                'topics': data.get('topics', []),
                'is_archived': data.get('archived', False),
                'is_fork': data.get('fork', False),
                'homepage': data.get('homepage', ''),
            }
            
            # Try to get latest release
            try:
                release_resp = self.session.get(
                    f'https://api.github.com/repos/{owner}/{repo}/releases/latest',
                    headers=headers,
                    timeout=10
                )
                if release_resp.status_code == 200:
                    release = release_resp.json()
                    metrics['last_release_date'] = release.get('published_at')
                    metrics['last_release_tag'] = release.get('tag_name')
            except:
                pass
            
            # Try to get last commit date
            try:
                commits_resp = self.session.get(
                    f'https://api.github.com/repos/{owner}/{repo}/commits',
                    headers=headers,
                    params={'per_page': 1},
                    timeout=10
                )
                if commits_resp.status_code == 200:
                    commits = commits_resp.json()
                    if commits:
                        metrics['last_commit_date'] = commits[0].get('commit', {}).get('committer', {}).get('date')
            except:
                pass
            
            # Compute health score
            metrics['health_score'] = self._compute_github_health_score(metrics)
            
            time.sleep(0.5)  # Be kind to GitHub API
            return metrics
            
        except Exception as e:
            logger.warning(f"Error fetching GitHub metrics for {owner}/{repo}: {e}")
            return None

    def _compute_github_health_score(self, metrics: Dict) -> int:
        """Compute a 0-100 health score for a GitHub repository."""
        score = 0
        
        # Existence (if archived or doesn't exist, heavily penalize)
        if not metrics.get('exists', True):
            return 0
        if metrics.get('is_archived', False):
            return max(10, score)  # Archived repos get max 10
        
        # Stars (up to 25 points) - logarithmic scale
        stars = metrics.get('stars', 0)
        if stars >= 1000: score += 25
        elif stars >= 500: score += 22
        elif stars >= 100: score += 18
        elif stars >= 50: score += 14
        elif stars >= 10: score += 10
        elif stars >= 1: score += 5
        
        # Recent activity (up to 30 points)
        last_commit = metrics.get('last_commit_date')
        if last_commit:
            try:
                commit_date = datetime.fromisoformat(last_commit.replace('Z', '+00:00'))
                days_since = (datetime.now(commit_date.tzinfo) - commit_date).days
                if days_since < 30: score += 30
                elif days_since < 90: score += 25
                elif days_since < 180: score += 20
                elif days_since < 365: score += 15
                elif days_since < 730: score += 8
                else: score += 2
            except:
                pass
        
        # Has releases (up to 10 points)
        if metrics.get('last_release_date'):
            score += 10
        
        # Has license (5 points)
        if metrics.get('license'):
            score += 5
        
        # Has description (5 points)
        if metrics.get('description'):
            score += 5
        
        # Forks indicate community usage (up to 10 points)
        forks = metrics.get('forks', 0)
        if forks >= 100: score += 10
        elif forks >= 50: score += 8
        elif forks >= 10: score += 5
        elif forks >= 1: score += 3
        
        # Not a fork (5 points for original repos)
        if not metrics.get('is_fork', False):
            score += 5
        
        # Homepage/docs (5 points)
        if metrics.get('homepage'):
            score += 5
        
        # Topics/tags (5 points)
        if metrics.get('topics'):
            score += 5
        
        return min(100, score)

    def track_github_tool(self, paper_id: int, github_ref: Dict, github_token: str = None):
        """Register a GitHub tool reference from a paper into the tracking tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        repo_url = self.normalize_url(github_ref['url'])
        full_name = github_ref['full_name'].lower()
        
        try:
            # Check if tool already exists
            cursor.execute("SELECT id, paper_count FROM github_tools WHERE full_name = ?", (full_name,))
            row = cursor.fetchone()
            
            if row:
                tool_id = row[0]
                # Update paper count
                cursor.execute("""
                    UPDATE github_tools 
                    SET paper_count = paper_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (tool_id,))
            else:
                # Insert new tool
                cursor.execute("""
                    INSERT INTO github_tools (repo_url, owner, repo_name, full_name, paper_count)
                    VALUES (?, ?, ?, ?, 1)
                """, (github_ref['url'], github_ref['owner'], github_ref['repo_name'], full_name))
                tool_id = cursor.lastrowid
            
            # Record the paper-tool relationship
            relationship = github_ref.get('relationship', 'uses')
            context = github_ref.get('context', '')
            
            cursor.execute("""
                INSERT OR IGNORE INTO paper_github_tools (paper_id, github_tool_id, relationship, context)
                VALUES (?, ?, ?, ?)
            """, (paper_id, tool_id, relationship, context))
            
            # If this paper introduces the tool, mark it
            if relationship == 'introduces':
                cursor.execute("""
                    UPDATE github_tools SET original_paper_id = ? WHERE id = ? AND original_paper_id IS NULL
                """, (paper_id, tool_id))
            
            conn.commit()
            return tool_id
            
        except Exception as e:
            logger.warning(f"Error tracking GitHub tool {full_name}: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def update_github_tool_metrics(self, github_token: str = None, limit: int = 100):
        """Batch update GitHub API metrics for tracked tools. Run periodically."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get tools that haven't been checked recently (or ever)
        cursor.execute("""
            SELECT id, repo_url, full_name FROM github_tools 
            WHERE github_checked_at IS NULL 
               OR github_checked_at < datetime('now', '-7 days')
            ORDER BY paper_count DESC
            LIMIT ?
        """, (limit,))
        
        tools = cursor.fetchall()
        logger.info(f"Updating GitHub metrics for {len(tools)} tools...")
        
        updated = 0
        for tool_id, repo_url, full_name in tools:
            metrics = self.fetch_github_repo_metrics(repo_url, github_token)
            if not metrics:
                continue
            
            cursor.execute("""
                UPDATE github_tools SET
                    description = COALESCE(?, description),
                    stars = ?,
                    forks = ?,
                    open_issues = ?,
                    watchers = ?,
                    last_commit_date = ?,
                    created_date = ?,
                    last_release_date = ?,
                    last_release_tag = ?,
                    default_branch = ?,
                    license = ?,
                    language = ?,
                    topics = ?,
                    health_score = ?,
                    is_archived = ?,
                    is_fork = ?,
                    github_checked_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                metrics.get('description'),
                metrics.get('stars', 0),
                metrics.get('forks', 0),
                metrics.get('open_issues', 0),
                metrics.get('watchers', 0),
                metrics.get('last_commit_date'),
                metrics.get('created_date'),
                metrics.get('last_release_date'),
                metrics.get('last_release_tag'),
                metrics.get('default_branch', 'main'),
                metrics.get('license'),
                metrics.get('language'),
                json.dumps(metrics.get('topics', [])),
                metrics.get('health_score', 0),
                metrics.get('is_archived', False),
                metrics.get('is_fork', False),
                tool_id,
            ))
            
            updated += 1
            if updated % 10 == 0:
                conn.commit()
                logger.info(f"  Updated {updated}/{len(tools)} tools...")
        
        # Update citing paper counts and total citations
        cursor.execute("""
            UPDATE github_tools SET
                citing_paper_count = (
                    SELECT COUNT(*) FROM paper_github_tools pgt
                    WHERE pgt.github_tool_id = github_tools.id
                    AND pgt.relationship != 'introduces'
                ),
                total_citations_of_papers = (
                    SELECT COALESCE(SUM(p.citation_count), 0) 
                    FROM paper_github_tools pgt
                    JOIN papers p ON p.id = pgt.paper_id
                    WHERE pgt.github_tool_id = github_tools.id
                )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Updated GitHub metrics for {updated} tools")

    def get_top_github_tools(self, limit: int = 50) -> List[Dict]:
        """Get the most-referenced GitHub tools with health metrics."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                gt.*,
                (SELECT GROUP_CONCAT(p.title, '|||') 
                 FROM paper_github_tools pgt 
                 JOIN papers p ON p.id = pgt.paper_id 
                 WHERE pgt.github_tool_id = gt.id 
                 ORDER BY p.citation_count DESC 
                 LIMIT 5) as top_papers
            FROM github_tools gt
            WHERE gt.paper_count > 0
            ORDER BY gt.paper_count DESC, gt.stars DESC
            LIMIT ?
        """, (limit,))
        
        tools = []
        for row in cursor.fetchall():
            tool = dict(row)
            tool['topics'] = json.loads(tool.get('topics') or '[]')
            tool['top_papers'] = (tool.get('top_papers') or '').split('|||')[:5]
            tools.append(tool)
        
        conn.close()
        return tools

    # ========== LLM TAG ENRICHMENT ==========

    def call_anthropic_api(self, prompt: str, api_key: str) -> Optional[str]:
        """
        Call the Anthropic API with the given prompt.
        Returns the response text or None on error.
        """
        try:
            import anthropic
        except ImportError:
            logger.error("anthropic package not installed. Run: pip install anthropic")
            return None

        try:
            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model=LLM_MODEL,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            logger.debug(f"Anthropic API error: {e}")
            return None

    def extract_tags_with_llm(self, title: str, abstract: str, api_key: str) -> Optional[Dict]:
        """
        Use Claude to extract microscopy tags from title and abstract.
        Returns dict with tag categories or None if extraction fails.

        CRITICAL: Only tags things ACTUALLY USED in the study, not cited/mentioned.
        """
        if not abstract or len(abstract.strip()) < 50:
            return None

        # Build list of valid tags from our patterns
        valid_techniques = list(MICROSCOPY_TECHNIQUES.keys())
        valid_organisms = list(ORGANISM_KEYWORDS.keys())
        valid_fluorophores = list(FLUOROPHORES.keys())[:60]  # Limit to save tokens
        valid_sample_prep = list(SAMPLE_PREPARATION.keys())
        valid_cell_lines = list(CELL_LINE_KEYWORDS.keys())

        prompt = f"""Analyze this scientific paper and extract microscopy-related tags.

CRITICAL RULES:
1. ONLY tag things that were ACTUALLY USED in the paper's experiments
2. DO NOT tag things that are merely cited, mentioned in background, or compared against
3. If a paper says "unlike STED microscopy, our approach uses confocal" - tag "Confocal" NOT "STED"
4. If a paper says "previous work used two-photon imaging, here we developed..." - only tag the new method
5. Only use tags from the provided lists - do not invent new tags
6. When uncertain, do NOT include the tag

VALID TAGS (use these exact values only):

TECHNIQUES: {', '.join(valid_techniques[:40])}

ORGANISMS: {', '.join(valid_organisms)}

FLUOROPHORES: {', '.join(valid_fluorophores)}

SAMPLE_PREPARATION: {', '.join(valid_sample_prep[:30])}

CELL_LINES: {', '.join(valid_cell_lines)}

PAPER TO ANALYZE:
Title: {title}
Abstract: {abstract[:2000]}

RESPOND WITH ONLY VALID JSON (no markdown, no explanation):
{{
  "microscopy_techniques": ["tag1", "tag2"],
  "organisms": ["tag1"],
  "fluorophores": ["tag1", "tag2"],
  "sample_preparation": ["tag1"],
  "cell_lines": []
}}

Use empty arrays [] for categories with no applicable tags."""

        response = self.call_anthropic_api(prompt, api_key)
        if not response:
            return None

        # Parse response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split('\n')
            lines = [l for l in lines if not l.strip().startswith('```')]
            response = '\n'.join(lines)

        try:
            result = json.loads(response)

            # Validate tags against our known values
            validated = {}

            if 'microscopy_techniques' in result:
                validated['microscopy_techniques'] = [
                    t for t in result['microscopy_techniques']
                    if t in MICROSCOPY_TECHNIQUES
                ]

            if 'organisms' in result:
                validated['organisms'] = [
                    o for o in result['organisms']
                    if o in ORGANISM_KEYWORDS
                ]

            if 'fluorophores' in result:
                validated['fluorophores'] = [
                    f for f in result['fluorophores']
                    if f in FLUOROPHORES
                ]

            if 'sample_preparation' in result:
                validated['sample_preparation'] = [
                    s for s in result['sample_preparation']
                    if s in SAMPLE_PREPARATION
                ]

            if 'cell_lines' in result:
                validated['cell_lines'] = [
                    c for c in result['cell_lines']
                    if c in CELL_LINE_KEYWORDS
                ]

            return validated

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse LLM response: {e}")
            return None

    def merge_tags(self, existing: List[str], new: List[str]) -> List[str]:
        """Merge tag lists without duplicates (case-insensitive)."""
        if not new:
            return existing or []

        existing = existing or []
        existing_lower = {t.lower() for t in existing}
        merged = list(existing)

        for tag in new:
            if tag.lower() not in existing_lower:
                merged.append(tag)
                existing_lower.add(tag.lower())

        return merged

    def count_tags(self, paper: Dict) -> int:
        """Count total tags across key categories."""
        count = 0
        for field in ['microscopy_techniques', 'organisms', 'fluorophores',
                      'sample_preparation', 'cell_lines']:
            tags = paper.get(field, [])
            if isinstance(tags, list):
                count += len(tags)
        return count

    def has_minimum_tags(self, paper: Dict, min_tags: int = 1) -> bool:
        """Check if paper has minimum required tags."""
        return self.count_tags(paper) >= min_tags

    def calculate_priority(self, paper: Dict) -> int:
        """Calculate priority score."""
        score = 0

        # Citations are very important
        citations = paper.get('citation_count', 0)
        if citations > 1000:
            score += 100
        elif citations > 500:
            score += 75
        elif citations > 100:
            score += 50
        elif citations > 50:
            score += 30
        elif citations > 10:
            score += 15

        # Full text
        if paper.get('has_full_text'):
            score += 20

        # Protocols
        if paper.get('protocols'):
            score += len(paper['protocols']) * 50

        # GitHub
        if paper.get('github_url'):
            score += 40

        # Data repositories
        if paper.get('repositories'):
            score += len(paper['repositories']) * 30

        # RRIDs
        if paper.get('rrids'):
            score += len(paper['rrids']) * 10

        # Figures
        if paper.get('figures'):
            score += min(len(paper['figures']) * 5, 30)

        # Methods
        if paper.get('methods') and len(paper.get('methods', '')) > 500:
            score += 15

        # Techniques
        if paper.get('microscopy_techniques'):
            score += len(paper['microscopy_techniques']) * 5

        # Affiliations (NEW in v5.0) - papers with affiliations are more valuable
        if paper.get('affiliations'):
            score += 10

        return score

    # ========== PMC FULL TEXT ==========

    def fetch_pmc_full_text(self, pmc_id: str) -> Optional[Dict]:
        """Fetch full text from PMC."""
        if not pmc_id:
            return None

        pmc_id = pmc_id.replace('PMC', '')

        try:
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                'db': 'pmc',
                'id': pmc_id,
                'rettype': 'xml',
            }

            response = self.session.get(url, params=params, timeout=60)
            self.stats['api_calls'] += 1
            time.sleep(0.34)

            if response.status_code != 200:
                return None

            root = ET.fromstring(response.content)
            article = root.find('.//article')
            if article is None:
                return None

            result = {
                'methods': '',
                'full_text': '',
                'figures': [],
                'supplementary': [],
            }

            # Extract methods
            methods_sections = []
            for sec in article.findall('.//sec'):
                sec_type = sec.get('sec-type', '').lower()
                title_elem = sec.find('title')
                title = title_elem.text.lower() if title_elem is not None and title_elem.text else ''

                if any(m in sec_type or m in title for m in ['method', 'material', 'procedure', 'experimental', 'protocol']):
                    methods_text = self._extract_text_from_element(sec)
                    if methods_text:
                        methods_sections.append(methods_text)

            result['methods'] = '\n\n'.join(methods_sections)

            # Extract full text - from content sections only (not metadata)
            full_text_parts = []
            
            # Get title
            title_group = article.find('.//title-group')
            if title_group is not None:
                article_title = title_group.find('article-title')
                if article_title is not None:
                    title_text = self._extract_text_from_element(article_title)
                    if title_text:
                        full_text_parts.append(title_text)
            
            # Get abstract
            abstract_elem = article.find('.//abstract')
            if abstract_elem is not None:
                abstract_text = self._extract_text_from_element(abstract_elem)
                if abstract_text:
                    full_text_parts.append(abstract_text)
            
            # Get body content (main article text)
            body = article.find('.//body')
            if body is not None:
                body_text = self._extract_text_from_element(body)
                if body_text:
                    full_text_parts.append(body_text)
            
            # Get back matter (acknowledgments, author notes, etc.) but skip references
            back = article.find('.//back')
            if back is not None:
                # Acknowledgments
                ack = back.find('.//ack')
                if ack is not None:
                    ack_text = self._extract_text_from_element(ack)
                    if ack_text:
                        full_text_parts.append(ack_text)
                
                # Author notes
                notes = back.find('.//notes')
                if notes is not None:
                    notes_text = self._extract_text_from_element(notes)
                    if notes_text:
                        full_text_parts.append(notes_text)
                
                # Funding
                funding = back.find('.//funding-group')
                if funding is not None:
                    funding_text = self._extract_text_from_element(funding)
                    if funding_text:
                        full_text_parts.append(funding_text)
            
            # Get figure and table captions for tag extraction
            for fig in article.findall('.//fig'):
                caption = fig.find('.//caption')
                if caption is not None:
                    caption_text = self._extract_text_from_element(caption)
                    if caption_text:
                        full_text_parts.append(caption_text)
            
            for table in article.findall('.//table-wrap'):
                caption = table.find('.//caption')
                if caption is not None:
                    caption_text = self._extract_text_from_element(caption)
                    if caption_text:
                        full_text_parts.append(caption_text)
            
            result['full_text'] = ' '.join(full_text_parts)

            # Extract figures
            for fig in article.findall('.//fig'):
                figure_data = self._parse_figure(fig, pmc_id)
                if figure_data:
                    result['figures'].append(figure_data)

            for fig_group in article.findall('.//fig-group'):
                for fig in fig_group.findall('.//fig'):
                    figure_data = self._parse_figure(fig, pmc_id)
                    if figure_data:
                        result['figures'].append(figure_data)

            # Extract supplementary
            for supp in article.findall('.//supplementary-material'):
                supp_data = self._parse_supplementary(supp)
                if supp_data:
                    result['supplementary'].append(supp_data)

            self.stats['full_text_fetched'] += 1
            return result

        except Exception as e:
            logger.debug(f"PMC fetch error for {pmc_id}: {e}")
            return None

    def _extract_text_from_element(self, elem) -> str:
        """Extract all text from XML element."""
        texts = []
        for text in elem.itertext():
            text = text.strip()
            if text:
                texts.append(text)
        return ' '.join(texts)

    def _parse_figure(self, fig_elem, pmc_id: str) -> Optional[Dict]:
        """Parse figure element from PMC XML."""
        try:
            fig_id = fig_elem.get('id', '')

            label_elem = fig_elem.find('label')
            label = label_elem.text if label_elem is not None and label_elem.text else ''

            title_elem = fig_elem.find('caption/title')
            title = self._extract_text_from_element(title_elem) if title_elem is not None else ''

            caption_elem = fig_elem.find('caption')
            caption = ''
            if caption_elem is not None:
                caption_parts = []
                for p in caption_elem.findall('p'):
                    caption_parts.append(self._extract_text_from_element(p))
                caption = ' '.join(caption_parts)

            graphic = fig_elem.find('.//graphic')
            image_url = None
            if graphic is not None:
                xlink_href = graphic.get('{http://www.w3.org/1999/xlink}href')
                if xlink_href:
                    image_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/bin/{xlink_href}"
                    if not image_url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff')):
                        image_url += '.jpg'

            if not (label or title or caption):
                return None

            return {
                'id': fig_id,
                'label': label,
                'title': title,
                'caption': caption,
                'image_url': image_url,
            }

        except Exception:
            return None

    def _parse_supplementary(self, supp_elem) -> Optional[Dict]:
        """Parse supplementary material element."""
        try:
            supp_id = supp_elem.get('id', '')

            label_elem = supp_elem.find('label')
            label = label_elem.text if label_elem is not None and label_elem.text else ''

            caption_elem = supp_elem.find('caption')
            caption = self._extract_text_from_element(caption_elem) if caption_elem is not None else ''

            media = supp_elem.find('.//media')
            url = None
            if media is not None:
                xlink_href = media.get('{http://www.w3.org/1999/xlink}href')
                if xlink_href:
                    url = xlink_href

            return {
                'id': supp_id,
                'label': label,
                'caption': caption,
                'url': url,
            }

        except Exception:
            return None

    # ========== PUBMED API ==========

    def search_pubmed(self, query: str, max_results: int = 10000) -> List[str]:
        """Search PubMed."""
        pmids = []
        batch_size = 500
        retstart = 0

        logger.info(f"  Searching: {query[:70]}...")

        while len(pmids) < max_results:
            try:
                url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                params = {
                    'db': 'pubmed',
                    'term': query,
                    'retmax': batch_size,
                    'retstart': retstart,
                    'retmode': 'json',
                    'sort': 'relevance',
                }

                response = self.session.get(url, params=params, timeout=30)
                self.stats['api_calls'] += 1
                time.sleep(0.34)

                if response.status_code != 200:
                    break

                data = response.json()
                result = data.get('esearchresult', {})
                id_list = result.get('idlist', [])

                if not id_list:
                    break

                pmids.extend(id_list)
                retstart += batch_size

                total = int(result.get('count', 0))

                if len(id_list) < batch_size or len(pmids) >= min(total, max_results):
                    break

            except Exception as e:
                logger.error(f"Search error: {e}")
                break

        self.stats['found'] += len(pmids)
        return pmids[:max_results]

    def fetch_papers(self, pmids: List[str], fetch_full_text: bool = True, fetch_cites: bool = True) -> List[Dict]:
        """Fetch paper details with full extraction and citations."""
        papers = []
        batch_size = 100

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i+batch_size]

            try:
                url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                params = {
                    'db': 'pubmed',
                    'id': ','.join(batch),
                    'retmode': 'xml',
                }

                response = self.session.get(url, params=params, timeout=60)
                self.stats['api_calls'] += 1
                time.sleep(0.34)

                if response.status_code != 200:
                    continue

                root = ET.fromstring(response.content)

                for article in root.findall('.//PubmedArticle'):
                    paper = self._parse_article(article, fetch_full_text, fetch_cites)
                    if paper:
                        papers.append(paper)

            except Exception as e:
                logger.error(f"Fetch error: {e}")
                continue

        return papers

    def _parse_article(self, article, fetch_full_text: bool = True, fetch_cites: bool = True) -> Optional[Dict]:
        """Parse PubMed article XML with complete extraction, text cleaning, and AFFILIATIONS."""
        try:
            # PMID - validate
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else None
            pmid = validate_pmid(pmid)
            if not pmid:
                return None

            # DOI - normalize
            doi = None
            for aid in article.findall('.//ArticleId'):
                if aid.get('IdType') == 'doi':
                    doi = normalize_doi(aid.text)
                    break

            # Check duplicate
            if self._is_duplicate(doi, pmid):
                self.stats['duplicates_skipped'] += 1
                return None

            # Title - clean text
            title_elem = article.find('.//ArticleTitle')
            title = ''.join(title_elem.itertext()).strip() if title_elem is not None else ''
            title = clean_text(title)
            if not title:
                return None

            # Abstract - clean text
            abstract = ''
            for sec in article.findall('.//AbstractText'):
                label = sec.get('Label', '')
                text = ''.join(sec.itertext()).strip()
                if label:
                    abstract += f"{label}: {text} "
                else:
                    abstract += f"{text} "
            abstract = clean_text(abstract)

            # Methods from abstract
            methods_from_abstract = ''
            for sec in article.findall('.//AbstractText'):
                label = sec.get('Label', '').upper()
                if any(m in label for m in ['METHOD', 'MATERIAL', 'PROCEDURE', 'PROTOCOL']):
                    methods_from_abstract += ''.join(sec.itertext()).strip() + ' '
            methods_from_abstract = clean_text(methods_from_abstract)

            # Year
            year = None
            pub_date = article.find('.//PubDate/Year')
            if pub_date is not None:
                try:
                    year = int(pub_date.text)
                except:
                    pass

            # ==========================================
            # AUTHORS WITH AFFILIATIONS - NEW in v5.0!
            # ==========================================
            authors = []
            affiliations = []
            affiliation_set = set()
            
            for author in article.findall('.//Author'):
                lastname = author.find('LastName')
                forename = author.find('ForeName')
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name += f" {forename.text}"
                    authors.append(name)
                
                # Extract author affiliations - CRITICAL for institution extraction!
                for aff in author.findall('.//AffiliationInfo/Affiliation'):
                    if aff.text and aff.text not in affiliation_set:
                        affiliation_set.add(aff.text)
                        affiliations.append(aff.text)
            
            # Also check for standalone Affiliation elements
            medline_citation = article.find('.//MedlineCitation')
            if medline_citation is not None:
                for aff in medline_citation.findall('.//AffiliationInfo/Affiliation'):
                    if aff.text and aff.text not in affiliation_set:
                        affiliation_set.add(aff.text)
                        affiliations.append(aff.text)

            # Journal
            journal_elem = article.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else ''

            # PMC ID
            pmc_id = None
            for aid in article.findall('.//ArticleId'):
                if aid.get('IdType') == 'pmc':
                    pmc_id = aid.text
                    break

            # Full text data
            full_methods = methods_from_abstract
            full_text = ''
            figures = []
            supplementary = []

            # FETCH FULL TEXT
            if fetch_full_text and pmc_id:
                pmc_data = self.fetch_pmc_full_text(pmc_id)
                if pmc_data:
                    if pmc_data.get('methods') and len(pmc_data['methods']) > len(full_methods):
                        full_methods = pmc_data['methods']
                    full_text = pmc_data.get('full_text', '')
                    figures = pmc_data.get('figures', [])
                    supplementary = pmc_data.get('supplementary', [])

            # FETCH CITATIONS
            citation_count = 0
            influential_citations = 0
            citation_source = None
            semantic_scholar_id = None
            crossref_github_urls = []
            crossref_data_repos = []
            crossref_abstract = ''

            if fetch_cites:
                cite_data = self.fetch_citations(doi, pmid)
                citation_count = cite_data.get('citation_count', 0)
                influential_citations = cite_data.get('influential_citation_count', 0)
                citation_source = cite_data.get('source')
                semantic_scholar_id = cite_data.get('semantic_scholar_id')

                # ENHANCED: Get full CrossRef metadata for GitHub/data repository links
                if doi:
                    crossref_full = self.fetch_crossref_full_metadata(doi)
                    crossref_github_urls = crossref_full.get('github_urls', [])
                    crossref_data_repos = crossref_full.get('data_repositories', [])
                    crossref_abstract = crossref_full.get('abstract', '')

                    # Use CrossRef abstract if PubMed abstract is empty/short
                    if crossref_abstract and len(crossref_abstract) > len(abstract):
                        abstract = crossref_abstract

            # Combined text for extraction
            extraction_text = f"{title} {abstract} {full_methods} {full_text}"

            # Extract ALL categories
            microscopy_techniques = self.extract_microscopy_techniques(extraction_text)
            microscope_brands = self.extract_microscope_brands(extraction_text)
            reagent_suppliers = self.extract_reagent_suppliers(extraction_text)
            microscope_models = self.extract_microscope_models(extraction_text)
            image_analysis_software = self.extract_image_analysis_software(extraction_text)
            image_acquisition_software = self.extract_image_acquisition_software(extraction_text)
            sample_preparation = self.extract_sample_preparation(extraction_text)
            fluorophores = self.extract_fluorophores(extraction_text)
            organisms = self.extract_organisms(extraction_text)
            cell_lines = self.extract_cell_lines(extraction_text)
            protocols = self.extract_protocols(extraction_text)
            repositories, github_url = self.extract_repositories(extraction_text)

            # Merge CrossRef data repositories with extracted ones
            if crossref_data_repos:
                for repo_url in crossref_data_repos:
                    if not any(repo_url.lower() in (r.get('url', '') or r).lower() for r in repositories):
                        repo_type = 'Unknown'
                        if 'zenodo' in repo_url.lower():
                            repo_type = 'Zenodo'
                        elif 'figshare' in repo_url.lower():
                            repo_type = 'Figshare'
                        elif 'dryad' in repo_url.lower():
                            repo_type = 'Dryad'
                        elif 'osf.io' in repo_url.lower():
                            repo_type = 'OSF'
                        elif 'ebi.ac.uk' in repo_url.lower():
                            if 'biostudies' in repo_url.lower():
                                repo_type = 'BioStudies'
                            elif 'empiar' in repo_url.lower():
                                repo_type = 'EMPIAR'
                        repositories.append({'name': repo_type, 'url': repo_url})
                        logger.debug(f"Added CrossRef repository: {repo_url}")

            # Extract ALL GitHub URLs for tool tracking (more comprehensive than repositories)
            github_tool_refs = self.extract_all_github_urls(extraction_text)

            # Merge CrossRef GitHub URLs
            if crossref_github_urls:
                for gh_url in crossref_github_urls:
                    # Add to github_url if not set
                    if not github_url:
                        github_url = gh_url
                    # Add to tool refs if not already there
                    gh_full_name = self._extract_github_full_name(gh_url)
                    if gh_full_name and not any(gh_full_name.lower() in str(t).lower() for t in github_tool_refs):
                        github_tool_refs.append({
                            'full_name': gh_full_name,
                            'url': gh_url,
                            'relationship': 'crossref_linked',
                        })
                        logger.debug(f"Added CrossRef GitHub: {gh_url}")
            
            rrids = self.extract_rrids(extraction_text)
            rors = self.extract_rors(extraction_text)
            antibodies = self.extract_antibodies(extraction_text, rrids)

            # Build URLs
            doi_url = f"https://doi.org/{doi}" if doi else None
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/" if pmc_id else None

            # Build paper dict
            paper = {
                'pmid': pmid,
                'doi': doi,
                'pmc_id': pmc_id,
                'title': title,
                'abstract': abstract,
                'methods': full_methods,
                'full_text': full_text[:100000] if full_text else None,
                'authors': ', '.join(authors),
                'journal': journal,
                'year': year,

                # AFFILIATIONS - NEW in v5.0!
                'affiliations': affiliations,

                # URLs
                'doi_url': doi_url,
                'pubmed_url': pubmed_url,
                'pmc_url': pmc_url,

                # CITATIONS - CRITICAL!
                'citation_count': citation_count,
                'influential_citation_count': influential_citations,
                'citation_source': citation_source,
                'semantic_scholar_id': semantic_scholar_id,

                # Categorized tags
                'microscopy_techniques': microscopy_techniques,
                'microscope_brands': microscope_brands,
                'reagent_suppliers': reagent_suppliers,
                'microscope_models': microscope_models,
                'image_analysis_software': image_analysis_software,
                'image_acquisition_software': image_acquisition_software,
                'sample_preparation': sample_preparation,
                'fluorophores': fluorophores,
                'organisms': organisms,
                'cell_lines': cell_lines,

                # Resources
                'protocols': protocols,
                'repositories': repositories,
                'github_url': github_url,
                'github_tools': github_tool_refs,  # All GitHub repos referenced
                'rrids': rrids,
                'rors': rors,
                'antibodies': antibodies,
                'supplementary_materials': supplementary,

                # Figures
                'figures': figures,
                'figure_count': len(figures),

                # Flags
                'has_full_text': bool(full_text),
                'has_figures': len(figures) > 0,
                'has_protocols': len(protocols) > 0,
                'has_github': bool(github_url),
                'has_data': len(repositories) > 0,
                'has_rrids': len(rrids) > 0,
                'has_rors': len(rors) > 0,
                'has_affiliations': len(affiliations) > 0,  # NEW in v5.0

                # Legacy fields
                'techniques': microscopy_techniques,
                'software': image_analysis_software + image_acquisition_software,
                'microscope_brand': ', '.join(microscope_brands) if microscope_brands else None,
            }

            # Calculate priority
            paper['priority_score'] = self.calculate_priority(paper)

            # LLM ENRICHMENT - If enabled and paper has sparse tags
            if self.llm_enrich and self.llm_api_key:
                tag_count_before = self.count_tags(paper)

                # Use LLM if regex found few tags
                if tag_count_before < 3 and abstract:
                    llm_tags = self.extract_tags_with_llm(title, abstract, self.llm_api_key)

                    if llm_tags:
                        # Merge LLM tags with regex-extracted tags
                        paper['microscopy_techniques'] = self.merge_tags(
                            paper['microscopy_techniques'], llm_tags.get('microscopy_techniques', [])
                        )
                        paper['organisms'] = self.merge_tags(
                            paper['organisms'], llm_tags.get('organisms', [])
                        )
                        paper['fluorophores'] = self.merge_tags(
                            paper['fluorophores'], llm_tags.get('fluorophores', [])
                        )
                        paper['sample_preparation'] = self.merge_tags(
                            paper['sample_preparation'], llm_tags.get('sample_preparation', [])
                        )
                        paper['cell_lines'] = self.merge_tags(
                            paper['cell_lines'], llm_tags.get('cell_lines', [])
                        )

                        # Update legacy fields
                        paper['techniques'] = paper['microscopy_techniques']

                        tag_count_after = self.count_tags(paper)
                        if tag_count_after > tag_count_before:
                            self.stats['llm_enriched'] += 1
                            logger.debug(f"LLM enriched paper {pmid}: {tag_count_before} -> {tag_count_after} tags")

                    # Rate limit for LLM API
                    time.sleep(LLM_RATE_LIMIT_DELAY)

            # Check minimum tags requirement (skip papers with insufficient tags)
            # This applies to ALL papers, not just LLM-enriched ones
            if not self.has_minimum_tags(paper, LLM_MIN_TAGS_REQUIRED):
                self.stats['skipped_no_tags'] += 1
                logger.debug(f"Skipping paper {pmid}: only {self.count_tags(paper)} tags (need {LLM_MIN_TAGS_REQUIRED})")
                return None

            # Update stats
            if full_methods and len(full_methods) > 200:
                self.stats['with_methods'] += 1
            if figures:
                self.stats['with_figures'] += 1
            if protocols:
                self.stats['with_protocols'] += 1
            if github_url:
                self.stats['with_github'] += 1
            if repositories:
                self.stats['with_repos'] += 1
            if rrids:
                self.stats['with_rrids'] += 1
            if rors:
                self.stats['with_rors'] += 1
            if antibodies:
                self.stats['with_antibodies'] += 1
            if affiliations:
                self.stats['with_affiliations'] += 1  # NEW in v5.0

            return paper

        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None

    # ========== DATABASE ==========

    def save_paper(self, paper: Dict) -> Optional[int]:
        """Save paper with all data including affiliations."""
        max_retries = 5

        for attempt in range(max_retries):
            conn = None
            try:
                conn = self._get_conn()

                # Convert lists to JSON
                json_fields = [
                    'microscopy_techniques', 'microscope_brands', 'microscope_models',
                    'image_analysis_software', 'image_acquisition_software',
                    'sample_preparation', 'fluorophores', 'organisms', 'cell_lines',
                    'protocols', 'repositories', 'rrids', 'rors', 'antibodies',
                    'supplementary_materials', 'figures', 'techniques', 'software',
                    'affiliations', 'github_tools',  # v5.0+ fields
                ]

                for field in json_fields:
                    if field in paper and isinstance(paper[field], list):
                        paper[field] = json.dumps(paper[field])

                cursor = conn.execute("""
                    INSERT INTO papers (
                        pmid, doi, pmc_id, title, abstract, methods, full_text,
                        authors, journal, year,
                        affiliations,
                        doi_url, pubmed_url, pmc_url,
                        citation_count, influential_citation_count, citation_source, semantic_scholar_id,
                        microscopy_techniques, microscope_brands, microscope_models,
                        image_analysis_software, image_acquisition_software,
                        sample_preparation, fluorophores, organisms, cell_lines,
                        protocols, repositories, github_url, rrids, rors, antibodies,
                        supplementary_materials, figures, figure_count,
                        techniques, software, microscope_brand,
                        has_full_text, has_figures, has_protocols, has_github, has_data, has_affiliations,
                        priority_score, enriched_at, citations_updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, datetime('now'), datetime('now')
                    )
                """, (
                    paper.get('pmid'), paper.get('doi'), paper.get('pmc_id'),
                    paper.get('title'), paper.get('abstract'), paper.get('methods'), paper.get('full_text'),
                    paper.get('authors'), paper.get('journal'), paper.get('year'),
                    paper.get('affiliations', '[]'),  # NEW in v5.0
                    paper.get('doi_url'), paper.get('pubmed_url'), paper.get('pmc_url'),
                    paper.get('citation_count', 0), paper.get('influential_citation_count', 0),
                    paper.get('citation_source'), paper.get('semantic_scholar_id'),
                    paper.get('microscopy_techniques', '[]'), paper.get('microscope_brands', '[]'),
                    paper.get('microscope_models', '[]'),
                    paper.get('image_analysis_software', '[]'), paper.get('image_acquisition_software', '[]'),
                    paper.get('sample_preparation', '[]'), paper.get('fluorophores', '[]'),
                    paper.get('organisms', '[]'), paper.get('cell_lines', '[]'),
                    paper.get('protocols', '[]'), paper.get('repositories', '[]'),
                    paper.get('github_url'), paper.get('rrids', '[]'),
                    paper.get('rors', '[]'), paper.get('antibodies', '[]'),
                    paper.get('supplementary_materials', '[]'),
                    paper.get('figures', '[]'), paper.get('figure_count', 0),
                    paper.get('techniques', '[]'), paper.get('software', '[]'),
                    paper.get('microscope_brand'),
                    paper.get('has_full_text', False), paper.get('has_figures', False),
                    paper.get('has_protocols', False), paper.get('has_github', False),
                    paper.get('has_data', False), paper.get('has_affiliations', False),  # NEW in v5.0
                    paper.get('priority_score', 0),
                ))

                conn.commit()
                paper_id = cursor.lastrowid

                # Track known
                if paper.get('doi'):
                    self.known_dois.add(paper['doi'].lower())
                if paper.get('pmid'):
                    self.known_pmids.add(paper['pmid'])

                self.stats['saved'] += 1
                conn.close()
                return paper_id

            except sqlite3.IntegrityError:
                if conn:
                    conn.close()
                return None
            except sqlite3.OperationalError as e:
                if 'locked' in str(e) and attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                if conn:
                    conn.close()
                return None
            except Exception as e:
                self.stats['errors'] += 1
                logger.debug(f"Save error: {e}")
                if conn:
                    conn.close()
                return None

        return None

    # ========== UPDATE CITATIONS FOR EXISTING ==========

    def update_citations_for_existing(self, limit: int = None):
        """Update citation counts for papers that don't have them."""
        conn = self._get_conn()
        
        query = """
            SELECT id, doi, pmid FROM papers 
            WHERE citation_count = 0 OR citations_updated_at IS NULL
            ORDER BY priority_score DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = conn.execute(query)
        papers = cursor.fetchall()
        conn.close()
        
        logger.info(f"Updating citations for {len(papers)} papers...")
        
        updated = 0
        for paper_id, doi, pmid in papers:
            cite_data = self.fetch_citations(doi, pmid)
            
            if cite_data.get('citation_count', 0) > 0:
                conn = self._get_conn()
                conn.execute("""
                    UPDATE papers SET 
                        citation_count = ?,
                        influential_citation_count = ?,
                        citation_source = ?,
                        semantic_scholar_id = ?,
                        citations_updated_at = datetime('now')
                    WHERE id = ?
                """, (
                    cite_data.get('citation_count', 0),
                    cite_data.get('influential_citation_count', 0),
                    cite_data.get('source'),
                    cite_data.get('semantic_scholar_id'),
                    paper_id
                ))
                conn.commit()
                conn.close()
                updated += 1
            
            if updated % 100 == 0:
                logger.info(f"  Updated {updated} papers...")
            
            time.sleep(0.1)  # Rate limiting
        
        logger.info(f"Updated citations for {updated} papers")

    # ========== QUERIES ==========

    def get_all_queries(self) -> List[Tuple[str, int]]:
        """Get comprehensive search queries."""
        queries = []

        # Priority 1: Protocol sources
        protocol_queries = [
            ('protocols.io[All Fields] AND microscopy', 30000),
            ('Bio-protocol[Journal] AND microscopy', 20000),
            ('JoVE[Journal] AND microscopy', 30000),
            ('Nature Protocols[Journal] AND microscopy', 20000),
            ('STAR Protocols[Journal] AND microscopy', 10000),
            ('Current Protocols[Journal] AND microscopy', 15000),
        ]
        queries.extend(protocol_queries)

        # Priority 2: Data repositories
        repo_queries = [
            ('github[All Fields] AND microscopy', 30000),
            ('gitlab[All Fields] AND microscopy', 10000),
            ('zenodo[All Fields] AND microscopy', 20000),
            ('"IDR"[All Fields] AND imaging', 10000),
            ('EMPIAR[All Fields]', 10000),
            ('"BioImage Archive"[All Fields]', 5000),
        ]
        queries.extend(repo_queries)

        # Priority 3: Super-resolution
        superres = [
            ('STED[Title/Abstract] AND microscopy', 15000),
            ('STORM[Title/Abstract] AND microscopy', 15000),
            ('PALM[Title/Abstract] AND microscopy', 10000),
            ('dSTORM[Title/Abstract]', 8000),
            ('"structured illumination"[Title/Abstract]', 15000),
            ('"single molecule localization"[Title/Abstract]', 12000),
            ('DNA-PAINT[Title/Abstract]', 5000),
            ('MINFLUX[Title/Abstract]', 2000),
            ('"expansion microscopy"[Title/Abstract]', 8000),
            ('"super-resolution"[Title/Abstract] AND microscopy', 25000),
        ]
        queries.extend(superres)

        # Priority 4: Confocal
        confocal = [
            ('"confocal microscopy"[Title/Abstract]', 50000),
            ('"laser scanning confocal"[Title/Abstract]', 20000),
            ('spinning disk[Title/Abstract] AND microscopy', 15000),
            ('Airyscan[Title/Abstract]', 5000),
        ]
        queries.extend(confocal)

        # Priority 5: Light sheet
        lightsheet = [
            ('"light sheet"[Title/Abstract]', 20000),
            ('SPIM[Title/Abstract] AND microscopy', 10000),
            ('"selective plane illumination"[Title/Abstract]', 8000),
            ('"lattice light sheet"[Title/Abstract]', 5000),
            ('mesoSPIM[Title/Abstract]', 1000),
        ]
        queries.extend(lightsheet)

        # Priority 6: Electron microscopy
        em = [
            ('cryo-EM[Title/Abstract]', 30000),
            ('cryo-ET[Title/Abstract]', 15000),
            ('"electron tomography"[Title/Abstract]', 15000),
            ('FIB-SEM[Title/Abstract]', 10000),
            ('"serial block-face"[Title/Abstract]', 5000),
            ('"volume EM"[Title/Abstract]', 5000),
        ]
        queries.extend(em)

        # Priority 7: Multiphoton
        multiphoton = [
            ('"two-photon"[Title/Abstract] AND microscopy', 25000),
            ('"multiphoton"[Title/Abstract] AND microscopy', 20000),
            ('"three-photon"[Title/Abstract]', 5000),
        ]
        queries.extend(multiphoton)

        # Priority 8: Functional imaging
        functional = [
            ('FRET[Title/Abstract] AND microscopy', 20000),
            ('FLIM[Title/Abstract]', 15000),
            ('FRAP[Title/Abstract] AND microscopy', 15000),
            ('"calcium imaging"[Title/Abstract]', 30000),
            ('GCaMP[Title/Abstract]', 20000),
            ('"voltage imaging"[Title/Abstract]', 10000),
            ('optogenetics[Title/Abstract] AND imaging', 20000),
        ]
        queries.extend(functional)

        # Priority 9: Live cell
        live = [
            ('"live cell imaging"[Title/Abstract]', 30000),
            ('"live-cell microscopy"[Title/Abstract]', 15000),
            ('"time-lapse microscopy"[Title/Abstract]', 20000),
            ('"intravital microscopy"[Title/Abstract]', 15000),
        ]
        queries.extend(live)

        # Priority 10: Analysis
        analysis = [
            ('"deep learning"[Abstract] AND microscopy', 25000),
            ('"machine learning"[Abstract] AND microscopy', 25000),
            ('"cell segmentation"[Title/Abstract]', 25000),
            ('ImageJ[Title/Abstract]', 30000),
            ('Fiji[Title/Abstract] AND imaging', 20000),
            ('CellProfiler[Title/Abstract]', 10000),
            ('ilastik[Title/Abstract]', 5000),
            ('StarDist[Title/Abstract]', 3000),
            ('Cellpose[Title/Abstract]', 5000),
        ]
        queries.extend(analysis)

        # Priority 11: Tissue clearing
        clearing = [
            ('"tissue clearing"[Title/Abstract]', 12000),
            ('CLARITY[Title/Abstract] AND brain', 10000),
            ('iDISCO[Title/Abstract]', 6000),
            ('CUBIC[Title/Abstract] AND clearing', 5000),
        ]
        queries.extend(clearing)

        # Priority 12: Basic techniques
        basic = [
            ('"fluorescence microscopy"[Title/Abstract]', 50000),
            ('"immunofluorescence"[Title/Abstract]', 40000),
            ('"widefield microscopy"[Title/Abstract]', 15000),
            ('TIRF[Title/Abstract] AND microscopy', 15000),
        ]
        queries.extend(basic)

        return queries

    # ========== RUN ==========

    def run(self, limit: int = None, priority_only: bool = False,
            full_text_only: bool = False, fetch_citations: bool = True):
        """Run scraper with complete extraction."""
        logger.info("=" * 70)
        logger.info("MICROHUB PAPER SCRAPER v5.0 - WITH AFFILIATIONS")
        logger.info("=" * 70)
        logger.info("Features: Full text + CITATIONS + Complete tags + AFFILIATIONS")
        logger.info(f"Minimum tags required: {LLM_MIN_TAGS_REQUIRED} (papers with fewer will be skipped)")
        if self.llm_enrich:
            logger.info(f"LLM ENRICHMENT ENABLED (model: {LLM_MODEL})")
        logger.info("")

        queries = self.get_all_queries()

        if priority_only:
            keywords = ['protocol', 'github', 'zenodo', 'figshare', 'idr', 'empiar', 'bioimage', 'gitlab']
            queries = [q for q in queries if any(k in q[0].lower() for k in keywords)]
            logger.info(f"Priority mode: {len(queries)} queries")

        logger.info(f"Total queries: {len(queries)}")

        total_saved = 0
        query_count = 0

        for query, max_results in queries:
            query_count += 1

            if limit and total_saved >= limit:
                break

            remaining = (limit - total_saved) if limit else max_results
            actual_max = min(max_results, remaining)

            logger.info(f"\n[{query_count}/{len(queries)}] {query[:60]}...")

            pmids = self.search_pubmed(query, actual_max)
            if not pmids:
                logger.info("  No results")
                continue

            new_pmids = [p for p in pmids if p not in self.known_pmids]
            if not new_pmids:
                logger.info(f"  All {len(pmids)} already in database")
                continue

            logger.info(f"  Found {len(pmids)}, {len(new_pmids)} new")

            papers = self.fetch_papers(new_pmids, fetch_full_text=True, fetch_cites=fetch_citations)

            if full_text_only:
                papers = [p for p in papers if p.get('has_full_text')]

            saved_this_query = 0
            for paper in papers:
                paper_id = self.save_paper(paper)
                if paper_id:
                    saved_this_query += 1
                    total_saved += 1
                    
                    # Track GitHub tool references
                    github_tools = paper.get('github_tools', [])
                    if isinstance(github_tools, str):
                        try:
                            github_tools = json.loads(github_tools)
                        except:
                            github_tools = []
                    for ref in github_tools:
                        self.track_github_tool(paper_id, ref)

                if limit and total_saved >= limit:
                    break

            logger.info(f"  Saved {saved_this_query}, total: {total_saved}")

            # Log progress
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO scrape_log (query, found, saved, skipped, citations_fetched) VALUES (?, ?, ?, ?, ?)",
                (query, len(pmids), saved_this_query, len(pmids) - saved_this_query, self.stats['citations_fetched'])
            )
            conn.commit()
            conn.close()

        # Final stats
        logger.info("\n" + "=" * 70)
        logger.info("SCRAPING COMPLETE - v5.0 WITH AFFILIATIONS")
        logger.info("=" * 70)
        logger.info(f"Queries run: {query_count}")
        logger.info(f"Papers found: {self.stats['found']:,}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates_skipped']:,}")
        logger.info(f"Skipped (<{LLM_MIN_TAGS_REQUIRED} tags): {self.stats['skipped_no_tags']:,}")
        logger.info(f"Papers saved: {self.stats['saved']:,}")
        logger.info(f"  With citations: {self.stats['citations_fetched']:,}")
        logger.info(f"  With full text: {self.stats['full_text_fetched']:,}")
        logger.info(f"  With methods: {self.stats['with_methods']:,}")
        logger.info(f"  With figures: {self.stats['with_figures']:,}")
        logger.info(f"  With protocols: {self.stats['with_protocols']:,}")
        logger.info(f"  With GitHub: {self.stats['with_github']:,}")
        logger.info(f"  With data repos: {self.stats['with_repos']:,}")
        logger.info(f"  With RRIDs: {self.stats['with_rrids']:,}")
        logger.info(f"  With RORs: {self.stats['with_rors']:,}")
        logger.info(f"  With antibodies: {self.stats['with_antibodies']:,}")
        logger.info(f"  With affiliations: {self.stats['with_affiliations']:,}")  # NEW in v5.0
        if self.llm_enrich:
            logger.info(f"LLM enriched: {self.stats['llm_enriched']:,}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"API calls: {self.stats['api_calls']:,}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='MicroHub Scraper v5.0 - With Affiliations')
    parser.add_argument('--db', default='microhub.db', help='Database path')
    parser.add_argument('--email', help='Email for API access')
    parser.add_argument('--limit', type=int, help='Limit total papers')
    parser.add_argument('--priority-only', action='store_true', help='Only high-priority sources')
    parser.add_argument('--full-text-only', action='store_true', help='Only save papers with full text')
    parser.add_argument('--no-citations', action='store_true', help='Skip citation fetching (faster)')
    parser.add_argument('--update-citations', action='store_true', help='Update citations for existing papers')
    parser.add_argument('--update-limit', type=int, help='Limit papers for citation update')

    # LLM enrichment arguments
    parser.add_argument('--llm-enrich', action='store_true',
                        help='Enable LLM enrichment for tag extraction (uses Claude Haiku)')
    parser.add_argument('--llm-api-key', type=str, default=None,
                        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')

    # GitHub tool tracking arguments
    parser.add_argument('--update-github-tools', action='store_true',
                        help='Update GitHub API metrics for tracked tools (stars, commits, health)')
    parser.add_argument('--github-token', type=str, default=None,
                        help='GitHub personal access token (or set GITHUB_TOKEN env var). Increases rate limit from 60 to 5000 req/hr')
    parser.add_argument('--github-limit', type=int, default=100,
                        help='Max tools to update per run (default: 100)')

    args = parser.parse_args()

    # Handle LLM API key
    llm_api_key = None
    if args.llm_enrich:
        llm_api_key = args.llm_api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not llm_api_key:
            print("Error: LLM enrichment requires an API key.")
            print("Set ANTHROPIC_API_KEY environment variable or use --llm-api-key")
            import sys
            sys.exit(1)

    # Handle GitHub token
    github_token = args.github_token or os.environ.get('GITHUB_TOKEN')

    scraper = MicroHubScraperV5(
        db_path=args.db,
        email=args.email,
        llm_enrich=args.llm_enrich,
        llm_api_key=llm_api_key
    )

    if args.update_github_tools:
        logger.info("Updating GitHub tool metrics...")
        scraper.update_github_tool_metrics(
            github_token=github_token,
            limit=args.github_limit
        )
        # Print top tools
        top = scraper.get_top_github_tools(limit=20)
        if top:
            logger.info(f"\nTop {len(top)} GitHub tools by paper count:")
            for t in top:
                health = f"health={t['health_score']}" if t.get('health_score') else 'no metrics'
                stars = t.get('stars', 0)
                archived = ' [ARCHIVED]' if t.get('is_archived') else ''
                logger.info(f"  {t['full_name']} - {t['paper_count']} papers, ★{stars}, {health}{archived}")
    elif args.update_citations:
        scraper.update_citations_for_existing(limit=args.update_limit)
    else:
        scraper.run(
            limit=args.limit,
            priority_only=args.priority_only,
            full_text_only=args.full_text_only,
            fetch_citations=not args.no_citations
        )


if __name__ == '__main__':
    main()