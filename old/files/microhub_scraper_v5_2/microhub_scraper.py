#!/usr/bin/env python3
"""
MICROHUB PAPER SCRAPER v4.1 - COMPREHENSIVE EDITION
====================================================
Complete paper collection with:
- CITATION COUNTS from multiple sources (Semantic Scholar, CrossRef)
- Full text via PMC API
- Complete methods sections
- Figure metadata
- ALL protocols and repositories with URL VALIDATION (including OMERO)
- Comprehensive tag extraction including fluorophores
- Deduplication and cleanup

Usage:
  python microhub_scraper_v4.1.py                      # Full scrape
  python microhub_scraper_v4.1.py --limit 1000         # Limited papers
  python microhub_scraper_v4.1.py --priority-only      # Only high-value papers
  python microhub_scraper_v4.1.py --full-text-only     # Only papers with full text
  python microhub_scraper_v4.1.py --fetch-citations    # Update citations for existing papers

CHANGES IN v4.1:
- Added OMERO as a data repository
- Enhanced fluorophore detection
- Added genetically encoded indicators
- Improved figure extraction
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE SCHEMA - COMPREHENSIVE
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
    'DiI': [r'\bdii\b', r'dii[\'"]?\s*(membrane)?'],
    'DiO': [r'\bdio\b', r'dio[\'"]?\s*(membrane)?'],
    'DiD': [r'\bdid\b'],
    'DiR': [r'\bdir\b'],
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
    # Super-resolution
    'STED': ['sted', 'stimulated emission depletion'],
    'STORM': ['storm', 'stochastic optical reconstruction'],
    'PALM': ['palm', 'photoactivated localization'],
    'dSTORM': ['dstorm', 'd-storm', 'direct storm'],
    'SIM': ['structured illumination', r'\bsim\b.*microscop', '3d-sim'],
    'SMLM': ['smlm', 'single molecule localization'],
    'Super-Resolution': ['super-resolution', 'super resolution', 'nanoscopy', 'nanometer resolution'],
    'DNA-PAINT': ['dna-paint', 'paint microscopy'],
    'MINFLUX': ['minflux'],
    'Expansion Microscopy': ['expansion microscopy', r'\bexm\b'],
    'RESOLFT': ['resolft'],
    'SOFI': ['sofi', 'super-resolution optical fluctuation'],

    # Confocal & Light microscopy
    'Confocal': ['confocal', 'clsm', 'laser scanning confocal', 'lscm'],
    'Two-Photon': ['two-photon', 'two photon', '2-photon', '2p microscopy', 'multiphoton'],
    'Three-Photon': ['three-photon', 'three photon', '3-photon', '3p microscopy'],
    'Light Sheet': ['light sheet', 'light-sheet', 'spim', 'selective plane illumination', 'lsfm'],
    'Lattice Light Sheet': ['lattice light sheet', 'lls microscopy', 'lattice lightsheet'],
    'MesoSPIM': ['mesospim', 'meso-spim'],
    'Spinning Disk': ['spinning disk', 'spinning-disk', 'nipkow', 'csu-'],
    'TIRF': ['tirf', 'total internal reflection'],
    'Airyscan': ['airyscan'],
    'Widefield': ['widefield', 'wide-field', 'wide field'],
    'Epifluorescence': ['epifluorescence', 'epi-fluorescence'],
    'Brightfield': ['brightfield', 'bright-field', 'bright field'],
    'Phase Contrast': ['phase contrast', 'phase-contrast'],
    'DIC': [r'\bdic\b', 'differential interference contrast'],
    'Darkfield': ['darkfield', 'dark-field', 'dark field'],

    # Electron Microscopy
    'Cryo-EM': ['cryo-em', 'cryo-electron', 'cryoem', 'cryo electron'],
    'Cryo-ET': ['cryo-et', 'cryo-tomography', 'electron tomography', 'cryoet'],
    'TEM': ['transmission electron microscopy', r'\btem\b.*microscop'],
    'SEM': ['scanning electron microscopy', r'\bsem\b.*microscop'],
    'FIB-SEM': ['fib-sem', 'focused ion beam'],
    'Array Tomography': ['array tomography'],
    'Serial Block-Face SEM': ['serial block-face', 'sbfsem', 'sbf-sem'],
    'Volume EM': ['volume em', 'volume electron'],
    'Immuno-EM': ['immuno-em', 'immunoelectron', 'immuno-electron'],
    'Negative Stain EM': ['negative stain', 'negative-stain'],

    # Functional imaging
    'FRET': ['fret', r'förster resonance', 'fluorescence resonance energy transfer'],
    'FLIM': ['flim', 'fluorescence lifetime'],
    'FRAP': ['frap', 'fluorescence recovery after photobleaching'],
    'FLIP': ['flip', 'fluorescence loss in photobleaching'],
    'FCS': ['fcs', 'fluorescence correlation spectroscopy'],
    'FCCS': ['fccs', 'fluorescence cross-correlation'],
    'Calcium Imaging': ['calcium imaging', 'ca2+ imaging', 'ca imaging'],
    'Voltage Imaging': ['voltage imaging', 'voltage-sensitive'],
    'Optogenetics': ['optogenetics', 'optogenetic'],

    # Other techniques
    'Live Cell Imaging': ['live cell', 'live-cell', 'time-lapse'],
    'Intravital': ['intravital', 'in vivo imaging'],
    'High-Content Screening': ['high-content', 'high content', 'hcs', 'high-throughput imaging'],
    'Deconvolution': ['deconvolution', 'deconvolved'],
    'Optical Sectioning': ['optical sectioning', 'optical section'],
    'Z-Stack': ['z-stack', 'z stack', 'z-series'],
    '3D Imaging': ['3d imaging', '3-d imaging', 'three-dimensional imaging'],
    '4D Imaging': ['4d imaging', '4-d imaging', 'four-dimensional imaging'],
    'Single Molecule': ['single molecule', 'single-molecule'],
    'Single Particle': ['single particle', 'single-particle'],
    'Holographic': ['holographic', 'holography'],
    'OCT': ['optical coherence tomography', r'\boct\b'],
    'Photoacoustic': ['photoacoustic'],
    'AFM': ['atomic force microscopy', r'\bafm\b'],
    'CLEM': ['clem', 'correlative light', 'correlative microscopy'],
    'Raman': ['raman microscopy', 'raman imaging'],
    'CARS': ['cars microscopy', 'coherent anti-stokes'],
    'SRS': ['srs', 'stimulated raman'],
    'Second Harmonic': ['second harmonic', 'shg'],
    'Polarization': ['polarization microscopy', 'polarized light'],
    'Fluorescence Microscopy': ['fluorescence microscopy', 'fluorescent microscopy'],
    'Immunofluorescence': ['immunofluorescence', 'immuno-fluorescence'],
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
    'inForm': ['inform.*analysis'],
    'Definiens': ['definiens'],
    'Visiopharm': ['visiopharm'],
    
    # Specialized
    'TrackMate': ['trackmate'],
    'MorphoGraphX': ['morphographx'],
    'IMOD': [r'\bimod\b'],
    'Chimera': ['chimera', 'chimerax'],
    'PyMOL': ['pymol'],
    'Dragonfly': ['dragonfly.*software'],
    'Aivia': ['aivia'],
    'MATLAB': ['matlab'],
    'Python': ['python.*image', 'scikit-image', 'skimage'],
    'R': [r'\br\b.*analysis', 'bioconductor'],
    
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
    'CLARITY': ['clarity'],
    'iDISCO': ['idisco', 'idisco+'],
    'CUBIC': ['cubic', r'\bcubic\b'],
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

ORGANISM_KEYWORDS = {
    'Mouse': [r'\bmouse\b', r'\bmice\b', r'\bmurine\b', r'mus\s*musculus'],
    'Human': [r'\bhuman\b', r'\bpatient\b', r'homo\s*sapiens'],
    'Rat': [r'\brat\b', r'\brattus\b'],
    'Zebrafish': [r'\bzebrafish\b', r'\bdanio\s*rerio\b'],
    'Drosophila': [r'\bdrosophila\b', r'\bfruit\s*fly\b', r'\bd\.\s*melanogaster\b'],
    'C. elegans': [r'\bc\.\s*elegans\b', r'\bcaenorhabditis\b'],
    'Xenopus': [r'\bxenopus\b'],
    'Chicken': [r'\bchicken\b', r'\bchick\b', r'\bgallus\b'],
    'Pig': [r'\bpig\b', r'\bporcine\b', r'\bsus\s*scrofa\b'],
    'Monkey': [r'\bmonkey\b', r'\bmacaque\b', r'\bprimate\b'],
    'Rabbit': [r'\brabbit\b', r'\boryctolagus\b'],
    'Dog': [r'\bdog\b', r'\bcanine\b'],
    'Yeast': [r'\byeast\b', r'\bsaccharomyces\b', r'\bs\.\s*cerevisiae\b', r'\bs\.\s*pombe\b'],
    'E. coli': [r'\be\.\s*coli\b', r'\bescherichia\b'],
    'Bacteria': [r'\bbacteria\b', r'\bbacterial\b'],
    'Arabidopsis': [r'\barabidopsis\b'],
    'Plant': [r'\bplant\s*cell\b', r'\bplant\s*tissue\b'],
    'Tobacco': [r'\btobacco\b', r'\bnicotiana\b'],
    'Maize': [r'\bmaize\b', r'\bzea\s*mays\b'],
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
# ============================================================================

ROR_PATTERNS = [
    # Standard ROR format: https://ror.org/0xxxx
    r'ror\.org/([0-9a-z]{9})',
    r'ROR[:\s]+([0-9a-z]{9})',
    # Full URL format
    r'https?://ror\.org/([0-9a-z]{9})',
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
# MICROSCOPE BRANDS
# ============================================================================

MICROSCOPE_BRANDS = {
    'Zeiss': ['zeiss', 'carl zeiss'],
    'Leica': ['leica'],
    'Nikon': ['nikon'],
    'Olympus': ['olympus'],
    'Evident (Olympus)': ['evident'],
    'Thermo Fisher': ['thermo fisher', 'thermofisher', 'fei company'],
    'JEOL': ['jeol'],
    'Bruker': ['bruker'],
    'Andor': ['andor'],
    'Hamamatsu': ['hamamatsu'],
    'PerkinElmer': ['perkinelmer', 'perkin elmer'],
    'Molecular Devices': ['molecular devices'],
    'Yokogawa': ['yokogawa'],
    'Visitech': ['visitech'],
    'Till Photonics': ['till photonics'],
    '3i (Intelligent Imaging)': ['3i ', 'intelligent imaging'],
    'LaVision BioTec': ['lavision'],
    'Miltenyi': ['miltenyi', 'ultramicroscope'],
    'Luxendo': ['luxendo'],
    'Applied Scientific Instrumentation': ['asi ', 'applied scientific'],
    'Prior': ['prior scientific'],
    'Sutter': ['sutter instrument'],
    'Coherent': ['coherent'],
    'Spectra-Physics': ['spectra-physics', 'spectra physics'],
    'Newport': ['newport'],
    'Thorlabs': ['thorlabs'],
    'Edmund Optics': ['edmund optics'],
    'Chroma': ['chroma'],
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
    'MicroManager': ['micro-manager', 'micromanager', r'μmanager'],
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

class MicroHubScraperV4:
    """Paper scraper with CITATIONS, full text, and comprehensive extraction."""

    def __init__(self, db_path: str = 'microhub.db', email: str = None):
        self.db_path = db_path
        self.email = email or 'microhub@example.com'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'MicroHub/4.0 (Microscopy Database; mailto:{self.email})'
        })

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

    # ========== CITATION FETCHING ==========
    
    def fetch_citations_semantic_scholar(self, doi: str = None, pmid: str = None) -> Dict:
        """Fetch citation count from Semantic Scholar API."""
        try:
            if doi:
                url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
            elif pmid:
                url = f"https://api.semanticscholar.org/graph/v1/paper/PMID:{pmid}"
            else:
                return {}
            
            params = {'fields': 'citationCount,influentialCitationCount,paperId'}
            
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
            else:
                return {}
                
        except Exception as e:
            logger.debug(f"Semantic Scholar error: {e}")
            return {}
    
    def fetch_citations_crossref(self, doi: str) -> Dict:
        """Fetch citation count from CrossRef API."""
        if not doi:
            return {}
            
        try:
            url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
            headers = {'User-Agent': f'MicroHub/4.0 (mailto:{self.email})'}
            
            response = self.session.get(url, headers=headers, timeout=15)
            self.stats['api_calls'] += 1
            time.sleep(0.05)  # Polite rate limiting
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})
                return {
                    'citation_count': message.get('is-referenced-by-count', 0),
                    'source': 'crossref',
                }
            return {}
            
        except Exception as e:
            logger.debug(f"CrossRef error: {e}")
            return {}
    
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

            # Extract full text - get ALL text for comprehensive tag extraction
            full_text_parts = []
            for elem in article.iter():
                if elem.text:
                    full_text_parts.append(elem.text)
                if elem.tail:
                    full_text_parts.append(elem.tail)
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
        """Parse PubMed article XML with complete extraction."""
        try:
            # PMID
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else None
            if not pmid:
                return None

            # DOI
            doi = None
            for aid in article.findall('.//ArticleId'):
                if aid.get('IdType') == 'doi':
                    doi = aid.text
                    break

            # Check duplicate
            if self._is_duplicate(doi, pmid):
                self.stats['duplicates_skipped'] += 1
                return None

            # Title
            title_elem = article.find('.//ArticleTitle')
            title = ''.join(title_elem.itertext()).strip() if title_elem is not None else ''
            if not title:
                return None

            # Abstract
            abstract = ''
            for sec in article.findall('.//AbstractText'):
                label = sec.get('Label', '')
                text = ''.join(sec.itertext()).strip()
                if label:
                    abstract += f"{label}: {text} "
                else:
                    abstract += f"{text} "
            abstract = abstract.strip()

            # Methods from abstract
            methods_from_abstract = ''
            for sec in article.findall('.//AbstractText'):
                label = sec.get('Label', '').upper()
                if any(m in label for m in ['METHOD', 'MATERIAL', 'PROCEDURE', 'PROTOCOL']):
                    methods_from_abstract += ''.join(sec.itertext()).strip() + ' '
            methods_from_abstract = methods_from_abstract.strip()

            # Year
            year = None
            pub_date = article.find('.//PubDate/Year')
            if pub_date is not None:
                try:
                    year = int(pub_date.text)
                except:
                    pass

            # Authors
            authors = []
            for author in article.findall('.//Author'):
                lastname = author.find('LastName')
                forename = author.find('ForeName')
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name += f" {forename.text}"
                    authors.append(name)

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
            
            if fetch_cites:
                cite_data = self.fetch_citations(doi, pmid)
                citation_count = cite_data.get('citation_count', 0)
                influential_citations = cite_data.get('influential_citation_count', 0)
                citation_source = cite_data.get('source')
                semantic_scholar_id = cite_data.get('semantic_scholar_id')

            # Combined text for extraction
            extraction_text = f"{title} {abstract} {full_methods} {full_text}"

            # Extract ALL categories
            microscopy_techniques = self.extract_microscopy_techniques(extraction_text)
            microscope_brands = self.extract_microscope_brands(extraction_text)
            microscope_models = self.extract_microscope_models(extraction_text)
            image_analysis_software = self.extract_image_analysis_software(extraction_text)
            image_acquisition_software = self.extract_image_acquisition_software(extraction_text)
            sample_preparation = self.extract_sample_preparation(extraction_text)
            fluorophores = self.extract_fluorophores(extraction_text)
            organisms = self.extract_organisms(extraction_text)
            cell_lines = self.extract_cell_lines(extraction_text)
            protocols = self.extract_protocols(extraction_text)
            repositories, github_url = self.extract_repositories(extraction_text)
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

                # Legacy fields
                'techniques': microscopy_techniques,
                'software': image_analysis_software + image_acquisition_software,
                'microscope_brand': ', '.join(microscope_brands) if microscope_brands else None,
            }

            # Calculate priority
            paper['priority_score'] = self.calculate_priority(paper)

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

            return paper

        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None

    # ========== DATABASE ==========

    def save_paper(self, paper: Dict) -> Optional[int]:
        """Save paper with all data."""
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
                ]

                for field in json_fields:
                    if field in paper and isinstance(paper[field], list):
                        paper[field] = json.dumps(paper[field])

                cursor = conn.execute("""
                    INSERT INTO papers (
                        pmid, doi, pmc_id, title, abstract, methods, full_text,
                        authors, journal, year,
                        doi_url, pubmed_url, pmc_url,
                        citation_count, influential_citation_count, citation_source, semantic_scholar_id,
                        microscopy_techniques, microscope_brands, microscope_models,
                        image_analysis_software, image_acquisition_software,
                        sample_preparation, fluorophores, organisms, cell_lines,
                        protocols, repositories, github_url, rrids, rors, antibodies,
                        supplementary_materials, figures, figure_count,
                        techniques, software, microscope_brand,
                        has_full_text, has_figures, has_protocols, has_github, has_data,
                        priority_score, enriched_at, citations_updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, datetime('now'), datetime('now')
                    )
                """, (
                    paper.get('pmid'), paper.get('doi'), paper.get('pmc_id'),
                    paper.get('title'), paper.get('abstract'), paper.get('methods'), paper.get('full_text'),
                    paper.get('authors'), paper.get('journal'), paper.get('year'),
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
                    paper.get('has_data', False),
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
        logger.info("MICROHUB PAPER SCRAPER v4.0 - COMPREHENSIVE EDITION")
        logger.info("=" * 70)
        logger.info("Features: Full text + CITATIONS + Complete tags + URL validation")
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
                if self.save_paper(paper):
                    saved_this_query += 1
                    total_saved += 1

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
        logger.info("SCRAPING COMPLETE - COMPREHENSIVE EDITION")
        logger.info("=" * 70)
        logger.info(f"Queries run: {query_count}")
        logger.info(f"Papers found: {self.stats['found']:,}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates_skipped']:,}")
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
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"API calls: {self.stats['api_calls']:,}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='MicroHub Scraper v4.0 - Comprehensive Edition')
    parser.add_argument('--db', default='microhub.db', help='Database path')
    parser.add_argument('--email', help='Email for API access')
    parser.add_argument('--limit', type=int, help='Limit total papers')
    parser.add_argument('--priority-only', action='store_true', help='Only high-priority sources')
    parser.add_argument('--full-text-only', action='store_true', help='Only save papers with full text')
    parser.add_argument('--no-citations', action='store_true', help='Skip citation fetching (faster)')
    parser.add_argument('--update-citations', action='store_true', help='Update citations for existing papers')
    parser.add_argument('--update-limit', type=int, help='Limit papers for citation update')

    args = parser.parse_args()

    scraper = MicroHubScraperV4(db_path=args.db, email=args.email)
    
    if args.update_citations:
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