#!/usr/bin/env python3
"""
MICROHUB PAPER SCRAPER v5.0 - SMART EXTRACTION EDITION
=======================================================
Complete paper collection with:
- SMART TAG EXTRACTION: Methods-first with title+abstract fallback
- ANTIBODY FILTERING: Separates antibody source species from model organisms
- ROR EXTRACTION: Research Organization Registry identifiers
- CITATION COUNTS from multiple sources (Semantic Scholar, CrossRef)
- Full text via PMC API
- Complete methods sections
- Figure metadata
- ALL protocols and repositories with URL VALIDATION
- Comprehensive tag extraction including fluorophores
- Deduplication and cleanup

Usage:
  python microhub_scraper_v5.py                      # Full scrape
  python microhub_scraper_v5.py --limit 1000         # Limited papers
  python microhub_scraper_v5.py --priority-only      # Only high-value papers
  python microhub_scraper_v5.py --full-text-only     # Only papers with full text
  python microhub_scraper_v5.py --fetch-citations    # Update citations for existing papers

CHANGES IN v5.0:
- Smart tag extraction from Methods section (high confidence) or Title+Abstract (reviews)
- Antibody source species separated from model organisms
- ROR (Research Organization Registry) number extraction
- Tag source tracking ('methods' vs 'title_abstract')
- Improved methods section detection for various paper formats
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
    antibody_sources TEXT DEFAULT '[]',
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

    -- Tag extraction metadata
    tag_source TEXT DEFAULT 'unknown',

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
CREATE INDEX IF NOT EXISTS idx_papers_tag_source ON papers(tag_source);

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
    from_methods INTEGER DEFAULT 0,
    from_title_abstract INTEGER DEFAULT 0,
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
# DATA REPOSITORIES
# ============================================================================

REPOSITORY_PATTERNS = {
    'GitHub': (r'github\.com/([\w-]+/[\w.-]+?)(?:\.git|/(?:issues|wiki|releases|blob|tree|pull|actions|discussions)|$|\s|[,;)\]])', 'https://github.com/{}'),
    'GitLab': (r'gitlab\.com/([\w-]+/[\w.-]+?)(?:\.git|/(?:issues|wiki|releases|blob|tree|merge)|$|\s|[,;)\]])', 'https://gitlab.com/{}'),
    'Zenodo': (r'(?:zenodo\.org/records?/|10\.5281/zenodo\.)(\d+)', 'https://zenodo.org/record/{}'),
    'Figshare': (r'(?:figshare\.com/\S+/|10\.6084/m9\.figshare\.)(\d+)', 'https://figshare.com/articles/dataset/{}'),
    'Dryad': (r'(?:datadryad\.org/stash/dataset/doi:|10\.5061/dryad\.)([\w]+)', 'https://datadryad.org/stash/dataset/doi:10.5061/dryad.{}'),
    'OSF': (r'osf\.io/([\w]{5,})', 'https://osf.io/{}'),
    'OMERO': (r'(?:omero\.[\w.]+/(?:webclient|webgateway|figure)/?\??(?:show=)?(?:dataset|image|project|screen|plate|well)[-=]?)(\d+)', 'https://idr.openmicroscopy.org/webclient/?show=image-{}'),
    'OMERO Public': (r'(?:publicomero|omero-[\w]+)\.[\w.]+/webclient/\?show=(\w+-\d+)', 'https://idr.openmicroscopy.org/webclient/?show={}'),
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
    'SSBD': (r'ssbd\.riken\.jp/[\w/]*(\d+)', 'https://ssbd.riken.jp/database/{}'),
}


# ============================================================================
# FLUOROPHORES AND DYES - Comprehensive
# ============================================================================

FLUOROPHORES = {
    # Nuclear dyes
    'DAPI': [r'\bdapi\b'],
    'Hoechst 33342': ['hoechst 33342', 'hoechst33342'],
    'Hoechst 33258': ['hoechst 33258', 'hoechst33258'],
    'DRAQ5': ['draq5'],
    'DRAQ7': ['draq7'],
    'TO-PRO-3': ['to-pro-3', 'topro-3'],
    'SYTOX Green': ['sytox green'],
    'Propidium Iodide': ['propidium iodide'],
    
    # Membrane/Cytoskeleton
    'Phalloidin': ['phalloidin'],
    'WGA': [r'\bwga\b', 'wheat germ agglutinin'],
    'DiI': [r'\bdii\b'],
    'DiO': [r'\bdio\b'],
    'CellMask': ['cellmask'],
    'FM Dyes': ['fm 1-43', 'fm 4-64', 'fm1-43', 'fm4-64'],
    
    # Organelle trackers
    'MitoTracker': ['mitotracker'],
    'LysoTracker': ['lysotracker'],
    'ER-Tracker': ['er-tracker', 'ertracker'],
    
    # Alexa Fluor series
    'Alexa 350': ['alexa.*350', 'af350'],
    'Alexa 405': ['alexa.*405', 'af405'],
    'Alexa 488': ['alexa.*488', 'af488'],
    'Alexa 546': ['alexa.*546', 'af546'],
    'Alexa 555': ['alexa.*555', 'af555'],
    'Alexa 568': ['alexa.*568', 'af568'],
    'Alexa 594': ['alexa.*594', 'af594'],
    'Alexa 633': ['alexa.*633', 'af633'],
    'Alexa 647': ['alexa.*647', 'af647'],
    'Alexa 680': ['alexa.*680', 'af680'],
    'Alexa 750': ['alexa.*750', 'af750'],
    
    # Fluorescent proteins - Green
    'GFP': [r'\bgfp\b', 'green fluorescent protein'],
    'EGFP': [r'\begfp\b', 'enhanced gfp'],
    'sfGFP': ['sfgfp', 'superfolder gfp'],
    'mNeonGreen': ['mneongreen'],
    'mClover': ['mclover'],
    
    # Fluorescent proteins - Red
    'RFP': [r'\brfp\b', 'red fluorescent protein'],
    'mCherry': ['mcherry'],
    'tdTomato': ['tdtomato', 'td-tomato'],
    'dsRed': ['dsred'],
    'mScarlet': ['mscarlet'],
    'mRuby': ['mruby'],
    'mKate': ['mkate'],
    
    # Fluorescent proteins - Other colors
    'CFP': [r'\bcfp\b', 'cyan fluorescent protein'],
    'YFP': [r'\byfp\b', 'yellow fluorescent protein'],
    'BFP': [r'\bbfp\b', 'blue fluorescent protein'],
    'mCerulean': ['mcerulean', 'cerulean'],
    'mTurquoise': ['mturquoise'],
    'Venus': [r'\bvenus\b.*(?:fluorescent|protein)'],
    'Citrine': ['citrine'],
    
    # Far-red/Infrared
    'iRFP': ['irfp'],
    'miRFP': ['mirfp'],
    
    # Photoactivatable/Photoconvertible
    'PA-GFP': ['pa-gfp', 'pagfp'],
    'Dendra': ['dendra'],
    'mEos': ['meos'],
    'mMaple': ['mmaple'],
    'Kaede': ['kaede'],
    
    # Calcium indicators
    'GCaMP': ['gcamp'],
    'jGCaMP': ['jgcamp'],
    'RCaMP': ['rcamp'],
    'jRGECO': ['jrgeco'],
    'Fura-2': ['fura-2', 'fura2'],
    'Fluo-4': ['fluo-4', 'fluo4'],
    'Cal-520': ['cal-520', 'cal520'],
    'Oregon Green BAPTA': ['oregon green bapta', 'ogb-1'],
    
    # Voltage indicators
    'ASAP': ['asap1', 'asap2', 'asap3'],
    'Voltron': ['voltron'],
    'Archon': ['archon'],
    'ArcLight': ['arclight'],
    
    # Cyanine dyes
    'Cy2': [r'\bcy2\b'],
    'Cy3': [r'\bcy3\b'],
    'Cy5': [r'\bcy5\b'],
    'Cy7': [r'\bcy7\b'],
    
    # Other synthetic dyes
    'FITC': [r'\bfitc\b'],
    'TRITC': [r'\btritc\b'],
    'Texas Red': ['texas red'],
    'Rhodamine': ['rhodamine'],
    'ATTO 488': ['atto 488', 'atto488'],
    'ATTO 565': ['atto 565', 'atto565'],
    'ATTO 647N': ['atto 647', 'atto647'],
    'CF Dye': ['cf dye', r'cf\s*\d{3}'],
    'DyLight': ['dylight'],
    
    # SiR dyes
    'SiR-tubulin': ['sir-tubulin'],
    'SiR-actin': ['sir-actin'],
    'SiR-DNA': ['sir-dna'],
    'SiR-Hoechst': ['sir-hoechst'],
}


# ============================================================================
# MICROSCOPY TECHNIQUES
# ============================================================================

MICROSCOPY_TECHNIQUES = {
    # Super-resolution
    'STED': ['sted', 'stimulated emission depletion'],
    'STORM': ['storm', 'stochastic optical reconstruction'],
    'PALM': ['palm', 'photoactivated localization'],
    'dSTORM': ['dstorm', 'd-storm', 'direct storm'],
    'SIM': ['structured illumination', r'\bsim\b.*microscop', '3d-sim'],
    'SMLM': ['smlm', 'single molecule localization'],
    'Super-Resolution': ['super-resolution', 'super resolution', 'nanoscopy'],
    'DNA-PAINT': ['dna-paint', 'paint microscopy'],
    'MINFLUX': ['minflux'],
    'Expansion Microscopy': ['expansion microscopy', r'\bexm\b'],
    'RESOLFT': ['resolft'],
    'SOFI': ['sofi', 'super-resolution optical fluctuation'],

    # Confocal & Light microscopy
    'Confocal': ['confocal', 'clsm', 'laser scanning confocal'],
    'Two-Photon': ['two-photon', 'two photon', '2-photon', 'multiphoton'],
    'Three-Photon': ['three-photon', 'three photon', '3-photon'],
    'Light Sheet': ['light sheet', 'light-sheet', 'spim', 'selective plane illumination'],
    'Lattice Light Sheet': ['lattice light sheet', 'lls microscopy'],
    'MesoSPIM': ['mesospim', 'meso-spim'],
    'Spinning Disk': ['spinning disk', 'spinning-disk', 'nipkow'],
    'TIRF': ['tirf', 'total internal reflection'],
    'Airyscan': ['airyscan'],
    'Widefield': ['widefield', 'wide-field'],
    'Epifluorescence': ['epifluorescence', 'epi-fluorescence'],
    'Brightfield': ['brightfield', 'bright-field'],
    'Phase Contrast': ['phase contrast', 'phase-contrast'],
    'DIC': [r'\bdic\b.*microscop', 'differential interference contrast'],
    'Darkfield': ['darkfield', 'dark-field'],

    # Electron Microscopy
    'Cryo-EM': ['cryo-em', 'cryo-electron', 'cryoem'],
    'Cryo-ET': ['cryo-et', 'cryo-tomography', 'electron tomography'],
    'TEM': ['transmission electron microscopy', r'\btem\b.*microscop'],
    'SEM': ['scanning electron microscopy', r'\bsem\b.*microscop'],
    'FIB-SEM': ['fib-sem', 'focused ion beam'],
    'Array Tomography': ['array tomography'],
    'Serial Block-Face SEM': ['serial block-face', 'sbfsem', 'sbf-sem'],
    'Volume EM': ['volume em', 'volume electron'],
    'Immuno-EM': ['immuno-em', 'immunoelectron'],

    # Functional imaging
    'FRET': ['fret', 'fluorescence resonance energy transfer'],
    'FLIM': ['flim', 'fluorescence lifetime'],
    'FRAP': ['frap', 'fluorescence recovery after photobleaching'],
    'FLIP': ['flip', 'fluorescence loss in photobleaching'],
    'FCS': ['fcs', 'fluorescence correlation spectroscopy'],
    'Calcium Imaging': ['calcium imaging', 'ca2+ imaging'],
    'Voltage Imaging': ['voltage imaging', 'voltage-sensitive'],
    'Optogenetics': ['optogenetics', 'optogenetic'],

    # Other techniques
    'Live Cell Imaging': ['live cell', 'live-cell', 'time-lapse'],
    'Intravital': ['intravital', 'in vivo imaging'],
    'High-Content Screening': ['high-content', 'high content', 'hcs'],
    'Deconvolution': ['deconvolution', 'deconvolved'],
    'Optical Sectioning': ['optical sectioning'],
    'Z-Stack': ['z-stack', 'z stack', 'z-series'],
    '3D Imaging': ['3d imaging', '3-d imaging'],
    'Single Molecule': ['single molecule', 'single-molecule'],
    'Single Particle': ['single particle', 'single-particle'],
    'Holographic': ['holographic', 'holography'],
    'OCT': ['optical coherence tomography'],
    'AFM': ['atomic force microscopy', r'\bafm\b.*microscop'],
    'CLEM': ['clem', 'correlative light', 'correlative microscopy'],
    'Raman': ['raman microscopy', 'raman imaging'],
    'SRS': ['srs', 'stimulated raman'],
    'Second Harmonic': ['second harmonic', 'shg'],
    'Fluorescence Microscopy': ['fluorescence microscopy'],
    'Immunofluorescence': ['immunofluorescence', 'immuno-fluorescence'],
}


# ============================================================================
# IMAGE ANALYSIS SOFTWARE
# ============================================================================

IMAGE_ANALYSIS_SOFTWARE = {
    # Open source
    'Fiji': ['fiji', r'\bimagej\b', 'image j'],
    'ImageJ': [r'\bimagej\b', 'image j'],
    'CellProfiler': ['cellprofiler'],
    'ilastik': ['ilastik'],
    'QuPath': ['qupath'],
    'napari': ['napari'],
    'Icy': [r'\bicy\b.*software', r'\bicy\b.*analysis'],
    'OMERO': ['omero'],
    'Vaa3D': ['vaa3d'],
    'BigDataViewer': ['bigdataviewer'],
    
    # Deep Learning
    'StarDist': ['stardist'],
    'Cellpose': ['cellpose'],
    'DeepCell': ['deepcell'],
    'U-Net': ['u-net', 'unet'],
    'Mask R-CNN': ['mask r-cnn', 'mask rcnn'],
    
    # Commercial
    'Imaris': ['imaris'],
    'Amira': ['amira'],
    'Arivis': ['arivis'],
    'Huygens': ['huygens'],
    'Volocity': ['volocity'],
    'NIS-Elements': ['nis-elements', 'nis elements'],
    'ZEN': ['zen blue', 'zen black', r'\bzen\b.*software'],
    'LAS X': ['las x', 'las-x', 'lasx'],
    'MetaMorph': ['metamorph'],
    'SlideBook': ['slidebook'],
    'CellSens': ['cellsens'],
    
    # Specialized
    'TrackMate': ['trackmate'],
    'IMOD': [r'\bimod\b'],
    'Chimera': ['chimera', 'chimerax'],
    'PyMOL': ['pymol'],
    'MATLAB': ['matlab'],
    'Python': ['python.*image', 'scikit-image', 'skimage'],
    
    # EM specific
    'RELION': ['relion'],
    'cryoSPARC': ['cryosparc'],
    'EMAN2': ['eman2'],
    'SerialEM': ['serialem'],
}


# ============================================================================
# IMAGE ACQUISITION SOFTWARE
# ============================================================================

IMAGE_ACQUISITION_SOFTWARE = {
    'Micro-Manager': ['micro-manager', 'micromanager'],
    'NIS-Elements': ['nis-elements', 'nis elements'],
    'ZEN': ['zen blue', 'zen black', r'\bzen\b.*acquisition'],
    'LAS X': ['las x', 'las-x'],
    'MetaMorph': ['metamorph'],
    'SlideBook': ['slidebook'],
    'Imspector': ['imspector'],
    'Prairie View': ['prairie view'],
    'ScanImage': ['scanimage'],
    'LabVIEW': ['labview'],
}


# ============================================================================
# SAMPLE PREPARATION
# ============================================================================

SAMPLE_PREPARATION = {
    # Tissue Clearing
    'CLARITY': ['clarity'],
    'iDISCO': ['idisco', 'idisco+'],
    'CUBIC': ['cubic'],
    'uDISCO': ['udisco'],
    '3DISCO': ['3disco'],
    'SHIELD': ['shield.*clearing'],
    'PACT': [r'\bpact\b.*clearing'],
    'Tissue Clearing': ['tissue clearing', 'optical clearing'],
    
    # Sectioning
    'Cryosectioning': ['cryosection', 'cryostat', 'frozen section'],
    'Vibratome': ['vibratome'],
    'Microtome': ['microtome'],
    'Ultramicrotome': ['ultramicrotome'],
    'Paraffin Embedding': ['paraffin.*section', 'paraffin.*embed', 'ffpe'],
    
    # Mounting
    'Whole Mount': ['whole mount', 'wholemount'],
    'Flat Mount': ['flat mount', 'flatmount'],
    
    # Histology
    'Immunohistochemistry': ['immunohistochemistry', r'\bihc\b'],
    'H&E': ['h&e', 'hematoxylin.*eosin'],
    'TUNEL': ['tunel'],
    'In Situ Hybridization': ['in situ hybrid'],
    'FISH': [r'\bfish\b.*hybrid', 'fluorescence in situ'],
    'smFISH': ['smfish', 'single molecule fish'],
    'RNAscope': ['rnascope'],
    'MERFISH': ['merfish'],
    
    # Cell culture
    'Cell Culture': ['cell culture', 'cultured cells'],
    'Primary Culture': ['primary culture', 'primary cells'],
    'Organoid': ['organoid'],
    'Spheroid': ['spheroid'],
    '3D Culture': ['3d culture'],
    
    # Transfection/Transduction
    'Transfection': ['transfection', 'transfected'],
    'Transduction': ['transduction', 'transduced'],
    'Lentiviral': ['lentivir'],
    'AAV': [r'\baav\b', 'adeno-associated'],
    'Electroporation': ['electroporation'],
    
    # Gene editing
    'CRISPR': ['crispr', 'cas9'],
    'Knockdown': ['knockdown', 'sirna', 'shrna'],
    'Knockout': ['knockout'],
    
    # Sample prep
    'PFA Fixation': ['pfa', 'paraformaldehyde'],
    'Glutaraldehyde': ['glutaraldehyde'],
    'Methanol Fixation': ['methanol.*fix'],
    'Permeabilization': ['permeabiliz'],
    'Antigen Retrieval': ['antigen retrieval'],
}


# ============================================================================
# ORGANISMS
# ============================================================================

ORGANISM_KEYWORDS = {
    'Mouse': [r'\bmouse\b', r'\bmice\b', r'\bmurine\b', r'mus\s*musculus'],
    'Human': [r'\bhuman\b', r'\bpatient\b', r'homo\s*sapiens'],
    'Rat': [r'\brat\b', r'\brattus\b'],
    'Zebrafish': [r'\bzebrafish\b', r'\bdanio\s*rerio\b'],
    'Drosophila': [r'\bdrosophila\b', r'\bfruit\s*fly\b'],
    'C. elegans': [r'\bc\.\s*elegans\b', r'\bcaenorhabditis\b'],
    'Xenopus': [r'\bxenopus\b'],
    'Chicken': [r'\bchicken\b', r'\bchick\b', r'\bgallus\b'],
    'Pig': [r'\bpig\b', r'\bporcine\b'],
    'Monkey': [r'\bmonkey\b', r'\bmacaque\b', r'\bprimate\b'],
    'Rabbit': [r'\brabbit\b', r'\boryctolagus\b'],
    'Goat': [r'\bgoat\b'],
    'Donkey': [r'\bdonkey\b'],
    'Sheep': [r'\bsheep\b', r'\bovine\b'],
    'Guinea Pig': [r'\bguinea\s*pig\b'],
    'Hamster': [r'\bhamster\b'],
    'Dog': [r'\bdog\b', r'\bcanine\b'],
    'Yeast': [r'\byeast\b', r'\bsaccharomyces\b', r'\bs\.\s*cerevisiae\b'],
    'E. coli': [r'\be\.\s*coli\b', r'\bescherichia\b'],
    'Bacteria': [r'\bbacteria\b', r'\bbacterial\b'],
    'Arabidopsis': [r'\barabidopsis\b'],
    'Plant': [r'\bplant\s*cell\b', r'\bplant\s*tissue\b'],
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
    ],
    'Nature Protocols': [
        r'(https?://(?:www\.)?nature\.com/nprot/[\w/-]+)',
    ],
    'STAR Protocols': [
        r'(https?://(?:www\.)?cell\.com/star-protocols/[\w/-]+)',
    ],
    'Current Protocols': [
        r'(https?://currentprotocols\.onlinelibrary\.wiley\.com/[\w/-]+)',
    ],
    'JoVE': [
        r'(https?://(?:www\.)?jove\.com/t/\d+)',
        r'(https?://(?:www\.)?jove\.com/video/\d+)',
    ],
    'Cold Spring Harbor': [
        r'(https?://cshprotocols\.cshlp\.org/[\w/-]+)',
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
]


# ============================================================================
# ROR PATTERNS (Research Organization Registry)
# ============================================================================

ROR_PATTERNS = [
    # Standard ROR URL format
    (r'ror\.org/(0[a-z0-9]{8})', 'url'),
    # ROR ID mentioned in text
    (r'ROR:\s*(0[a-z0-9]{8})', 'text'),
    (r'ROR\s+(?:ID|identifier):\s*(0[a-z0-9]{8})', 'text'),
    # https://ror.org/XXXXXXXX format
    (r'https?://ror\.org/(0[a-z0-9]{8})', 'url'),
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
    '3i (Intelligent Imaging)': ['3i ', 'intelligent imaging'],
    'LaVision BioTec': ['lavision'],
    'Miltenyi': ['miltenyi', 'ultramicroscope'],
    'Luxendo': ['luxendo'],
    'Thorlabs': ['thorlabs'],
    'Photometrics': ['photometrics'],
    'Abberior': ['abberior'],
    'PicoQuant': ['picoquant'],
}


# ============================================================================
# MICROSCOPE MODELS
# ============================================================================

MICROSCOPE_MODELS = {
    # Zeiss
    'LSM 880': ['lsm 880', 'lsm880'],
    'LSM 980': ['lsm 980', 'lsm980'],
    'LSM 710': ['lsm 710', 'lsm710'],
    'Elyra': ['elyra'],
    'Lightsheet Z.1': ['lightsheet z.1', 'lightsheet.z1'],
    'Lightsheet 7': ['lightsheet 7'],
    'Axio Observer': ['axio observer'],
    'Axio Imager': ['axio imager'],
    
    # Leica
    'SP8': ['sp8', 'sp 8'],
    'SP5': ['sp5', 'sp 5'],
    'Stellaris': ['stellaris'],
    'STED 3X': ['sted 3x'],
    'Thunder': ['thunder imager'],
    'DMi8': ['dmi8', 'dmi 8'],
    
    # Nikon
    'A1R': ['a1r'],
    'Ti2': ['ti2', 'ti-2'],
    'CSU-W1': ['csu-w1'],
    'N-SIM': ['n-sim'],
    'N-STORM': ['n-storm'],
    
    # Olympus/Evident
    'FV3000': ['fv3000', 'fv 3000'],
    'FV1200': ['fv1200', 'fv 1200'],
    'SpinSR10': ['spinsr10'],
    'IXplore': ['ixplore'],
    
    # Light sheet
    'Ultramicroscope': ['ultramicroscope'],
    'MesoSPIM': ['mesospim'],
    'Lattice LightSheet': ['lattice lightsheet'],
    
    # EM
    'Krios': ['krios', 'titan krios'],
    'Glacios': ['glacios'],
    'Talos': ['talos'],
    'Tecnai': ['tecnai'],
}


# ============================================================================
# ANTIBODY SOURCE SPECIES (for filtering from organisms)
# ============================================================================

ANTIBODY_SOURCE_SPECIES = {
    'rabbit', 'goat', 'mouse', 'rat', 'donkey', 
    'chicken', 'sheep', 'guinea pig', 'hamster'
}


# ============================================================================
# SMART TAG EXTRACTION FUNCTIONS
# ============================================================================

def extract_methods_section(full_text: str) -> str:
    """
    Extract only the Materials and Methods section from full text.
    Handles various formats including PMC XML output.
    """
    if not full_text:
        return ''
    
    text_lower = full_text.lower()
    
    # Methods section START patterns
    start_patterns = [
        (r'\n\s*materials?\s+and\s+methods?\s*\n', 0),
        (r'\n\s*methods?\s+and\s+materials?\s*\n', 0),
        (r'\n\s*experimental\s+procedures?\s*\n', 0),
        (r'\n\s*methods?\s*\n(?=\s*[A-Z])', 0),
        (r'\bmethods\s*\n\s*\n', 0),
        (r'\n\s*star\s*\*?\s*methods?\s*\n', 0),
        (r'\bstar\s+methods', 0),
        (r'\n\s*online\s+methods?\s*\n', 0),
        (r'\bonline\s+methods', 0),
        (r'>methods?</title>', 0),
        (r'>materials?\s+and\s+methods?</title>', 0),
        (r'sec-type="methods"', 0),
        (r'(?:cells|animals|mice|samples)\s+were\s+(?:cultured|prepared|fixed|stained)', -50),
        (r'(?:imaging|microscopy)\s+was\s+performed', -50),
    ]
    
    # Methods section END patterns
    end_patterns = [
        r'\n\s*results?\s*\n',
        r'>results?</title>',
        r'\n\s*discussion\s*\n',
        r'>discussion</title>',
        r'\n\s*acknowledgement',
        r'\n\s*references\s*\n',
        r'\n\s*funding\s*\n',
        r'\n\s*author\s+contributions?',
        r'\n\s*data\s+availability',
        r'</sec>\s*<sec',
    ]
    
    # Find methods start
    start_pos = -1
    for pattern, offset in start_patterns:
        match = re.search(pattern, text_lower)
        if match:
            start_pos = max(0, match.end() + offset)
            break
    
    if start_pos == -1:
        return ''
    
    # Find methods end
    end_pos = len(full_text)
    search_text = text_lower[start_pos:]
    
    for pattern in end_patterns:
        match = re.search(pattern, search_text)
        if match:
            candidate = start_pos + match.start()
            if candidate < end_pos and candidate > start_pos + 500:
                end_pos = candidate
    
    # Cap at reasonable length
    end_pos = min(end_pos, start_pos + 50000)
    
    methods_text = full_text[start_pos:end_pos]
    
    # Clean up XML tags if present
    methods_text = re.sub(r'<[^>]+>', ' ', methods_text)
    methods_text = re.sub(r'\s+', ' ', methods_text)
    
    if len(methods_text) < 200:
        return ''
    
    return methods_text.strip()


def is_antibody_context(text: str, species: str, position: int, window: int = 80) -> bool:
    """Check if a species mention is in antibody context."""
    start = max(0, position - window)
    end = min(len(text), position + len(species) + window)
    context = text[start:end].lower()
    species_lower = species.lower()
    
    # Strict patterns - species must be directly part of antibody reference
    strict_patterns = [
        rf'anti-?{species_lower}',
        rf'{species_lower}\s+anti-?\w+',
        rf'anti-?{species_lower}\s+(?:IgG|IgM|IgY|antibod|secondary)',
        rf'{species_lower}\s+(?:polyclonal|monoclonal)',
        rf'raised\s+in\s+{species_lower}',
        rf'1:\d{{2,4}}\s*,?\s*{species_lower}',
        rf'{species_lower}\s*,?\s*1:\d{{2,4}}',
        rf'{species_lower}\s*[,\(]\s*(?:cell\s*signal|abcam|sigma|thermo|invitrogen|santa\s*cruz|millipore|sysy|bio-?rad)',
        rf'{species_lower}\s+IgG',
        rf'{species_lower}\s+(?:serum|antiserum)',
        rf'anti-?{species_lower}\s+(?:alexa|cy\d|fitc|tritc|dylight|atto|conjugat)',
    ]
    
    for pattern in strict_patterns:
        if re.search(pattern, context, re.IGNORECASE):
            return True
    
    return False


def extract_organisms_filtered(text: str, organism_patterns: Dict[str, List[str]]) -> Tuple[List[str], List[str]]:
    """
    Extract organisms, separating true model organisms from antibody sources.
    Returns (model_organisms, antibody_sources)
    """
    if not text:
        return [], []
    
    text_lower = text.lower()
    model_organisms = []
    antibody_sources = []
    
    for organism, patterns in organism_patterns.items():
        organism_lower = organism.lower()
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
            
            if not matches:
                continue
            
            # Check if this is an antibody source species
            if organism_lower in ANTIBODY_SOURCE_SPECIES:
                has_non_antibody_use = False
                has_antibody_use = False
                
                for match in matches:
                    if is_antibody_context(text, organism, match.start()):
                        has_antibody_use = True
                    else:
                        has_non_antibody_use = True
                
                if has_non_antibody_use:
                    model_organisms.append(organism)
                if has_antibody_use and not has_non_antibody_use:
                    antibody_sources.append(organism)
            else:
                model_organisms.append(organism)
            
            break
    
    return list(set(model_organisms)), list(set(antibody_sources))


# ============================================================================
# MAIN SCRAPER CLASS
# ============================================================================

class MicroHubScraperV5:
    """MicroHub Paper Scraper v5.0 with smart tag extraction."""
    
    def __init__(self, db_path: str = 'microhub.db', email: str = None):
        self.db_path = db_path
        self.email = email or os.environ.get('NCBI_EMAIL', 'microhub@example.com')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MicroHubScraper/5.0',
        })
        
        self.known_pmids = set()
        self.known_dois = set()
        
        self.stats = {
            'found': 0,
            'saved': 0,
            'duplicates_skipped': 0,
            'api_calls': 0,
            'errors': 0,
            'with_methods': 0,
            'with_full_text': 0,
            'with_figures': 0,
            'with_protocols': 0,
            'with_github': 0,
            'with_repos': 0,
            'with_rrids': 0,
            'with_rors': 0,
            'citations_fetched': 0,
            'full_text_fetched': 0,
            'from_methods': 0,
            'from_title_abstract': 0,
        }
        
        self._init_db()
        self._load_known_ids()
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def _init_db(self):
        conn = self._get_conn()
        conn.executescript(DB_INIT)
        conn.executescript(DB_SCHEMA)
        conn.commit()
        conn.close()
    
    def _load_known_ids(self):
        conn = self._get_conn()
        cursor = conn.execute("SELECT pmid, doi FROM papers WHERE pmid IS NOT NULL")
        for row in cursor:
            if row[0]:
                self.known_pmids.add(row[0])
            if row[1]:
                self.known_dois.add(row[1].lower())
        conn.close()
        logger.info(f"Loaded {len(self.known_pmids)} known PMIDs")
    
    def _is_duplicate(self, doi: str, pmid: str) -> bool:
        if pmid and pmid in self.known_pmids:
            return True
        if doi and doi.lower() in self.known_dois:
            return True
        return False
    
    # ========== EXTRACTION METHODS ==========
    
    def extract_from_patterns(self, text: str, patterns_dict: Dict) -> List[str]:
        """Extract matches from text using pattern dictionary with word boundaries."""
        if not text:
            return []
        text_lower = text.lower()
        found = []
        for name, patterns in patterns_dict.items():
            for pattern in patterns:
                # Add word boundaries to prevent matching inside other words
                # e.g., 'sted' should not match in 'suggested' or 'nested'
                # If pattern already contains regex special chars, use it as-is
                if any(c in pattern for c in r'\.+*?^$[]{}()|\\'):
                    # Pattern has regex chars, use as-is
                    regex_pattern = pattern
                else:
                    # Simple string pattern - add word boundaries
                    regex_pattern = r'\b' + re.escape(pattern) + r'\b'
                
                if re.search(regex_pattern, text_lower, re.IGNORECASE):
                    found.append(name)
                    break
        return list(set(found))
    
    def extract_tags_smart(self, title: str, abstract: str, methods: str, full_text: str) -> Dict:
        """
        Smart tag extraction:
        - Papers WITH methods → Extract from Methods only (high confidence)
        - Papers WITHOUT methods → Extract from Title + Abstract
        """
        # Try to get methods text
        methods_text = ''
        if methods and len(methods) > 200:
            methods_text = methods
        elif full_text:
            methods_text = extract_methods_section(full_text)
        
        # Determine extraction source
        if methods_text and len(methods_text) >= 200:
            extraction_text = methods_text
            source = 'methods'
        else:
            extraction_text = f"{title} {abstract}"
            source = 'title_abstract'
        
        # Extract techniques
        techniques = self.extract_from_patterns(extraction_text, MICROSCOPY_TECHNIQUES)
        
        # Extract organisms with antibody filtering
        organisms, antibody_sources = extract_organisms_filtered(extraction_text, ORGANISM_KEYWORDS)
        
        # Extract other categories
        software = self.extract_from_patterns(extraction_text, IMAGE_ANALYSIS_SOFTWARE)
        fluorophores = self.extract_from_patterns(extraction_text, FLUOROPHORES)
        sample_prep = self.extract_from_patterns(extraction_text, SAMPLE_PREPARATION)
        cell_lines = self.extract_from_patterns(extraction_text, CELL_LINE_KEYWORDS)
        
        return {
            'microscopy_techniques': techniques,
            'organisms': organisms,
            'antibody_sources': antibody_sources,
            'image_analysis_software': software,
            'fluorophores': fluorophores,
            'sample_preparation': sample_prep,
            'cell_lines': cell_lines,
            'source': source,
            'methods_length': len(methods_text) if source == 'methods' else 0,
        }
    
    def extract_microscope_brands(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, MICROSCOPE_BRANDS)
    
    def extract_microscope_models(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, MICROSCOPE_MODELS)
    
    def extract_image_acquisition_software(self, text: str) -> List[str]:
        return self.extract_from_patterns(text, IMAGE_ACQUISITION_SOFTWARE)
    
    def extract_protocols(self, text: str) -> List[Dict]:
        """Extract protocol references."""
        protocols = []
        seen_urls = set()
        
        for source, patterns in PROTOCOL_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    url = match.group(1) if match.groups() else match.group(0)
                    
                    if not url.startswith('http'):
                        continue
                    
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    
                    url = url.rstrip('.,;:)')
                    
                    protocols.append({
                        'source': source,
                        'url': url,
                        'name': source,
                    })
        
        return protocols
    
    def extract_repositories(self, text: str) -> Tuple[List[Dict], Optional[str]]:
        """Extract data repository links."""
        repos = []
        github_url = None
        seen_urls = set()
        
        for name, (pattern, url_template) in REPOSITORY_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                identifier = match.group(1)
                url = url_template.format(identifier)
                
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                repos.append({
                    'name': name,  # Use 'name' for consistency with import/display
                    'accession_id': identifier,
                    'url': url,
                })
                
                if name == 'GitHub' and not github_url:
                    github_url = url
        
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
        
        for pattern, source_type in ROR_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                ror_id = match.group(1)
                if ror_id not in seen:
                    seen.add(ror_id)
                    rors.append({
                        'id': ror_id,
                        'url': f'https://ror.org/{ror_id}',
                        'source': source_type,
                    })
        
        return rors
    
    def extract_references(self, full_text: str) -> List[Dict]:
        """Extract references section from full text."""
        if not full_text:
            return []
        
        references = []
        
        # Find references section
        ref_section_patterns = [
            r'(?:\n|^)\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY|Literature Cited)\s*\n(.*?)(?:\n\s*(?:Supplementary|Supporting|Appendix|Acknowledgment)|$)',
        ]
        
        ref_text = ''
        for pattern in ref_section_patterns:
            match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
            if match:
                ref_text = match.group(1)
                break
        
        if not ref_text:
            return []
        
        # Parse individual references
        # Pattern 1: Numbered references like "1. Author et al..."
        numbered_refs = re.findall(r'(?:^|\n)\s*(\d+)\.\s+([^\n]+(?:\n(?!\d+\.)[^\n]+)*)', ref_text)
        
        if numbered_refs:
            for num, text in numbered_refs:
                ref_data = {
                    'num': int(num),
                    'text': text.strip().replace('\n', ' '),
                }
                
                # Extract DOI
                doi_match = re.search(r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}/[^\s\]>]+)', text, re.IGNORECASE)
                if doi_match:
                    ref_data['doi'] = doi_match.group(1).rstrip('.')
                    ref_data['url'] = f'https://doi.org/{ref_data["doi"]}'
                
                # Extract PMID
                pmid_match = re.search(r'PMID[:\s]*(\d+)', text, re.IGNORECASE)
                if pmid_match:
                    ref_data['pmid'] = pmid_match.group(1)
                    if 'url' not in ref_data:
                        ref_data['url'] = f'https://pubmed.ncbi.nlm.nih.gov/{ref_data["pmid"]}'
                
                references.append(ref_data)
        else:
            # Pattern 2: Unnumbered references (split by blank lines or author patterns)
            ref_blocks = re.split(r'\n\s*\n', ref_text)
            for idx, block in enumerate(ref_blocks, 1):
                block = block.strip()
                if len(block) < 20:
                    continue
                    
                ref_data = {
                    'num': idx,
                    'text': block.replace('\n', ' '),
                }
                
                # Extract DOI
                doi_match = re.search(r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}/[^\s\]>]+)', block, re.IGNORECASE)
                if doi_match:
                    ref_data['doi'] = doi_match.group(1).rstrip('.')
                    ref_data['url'] = f'https://doi.org/{ref_data["doi"]}'
                
                # Extract PMID
                pmid_match = re.search(r'PMID[:\s]*(\d+)', block, re.IGNORECASE)
                if pmid_match:
                    ref_data['pmid'] = pmid_match.group(1)
                    if 'url' not in ref_data:
                        ref_data['url'] = f'https://pubmed.ncbi.nlm.nih.gov/{ref_data["pmid"]}'
                
                references.append(ref_data)
        
        return references
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        url = url.lower().rstrip('/')
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        return url
    
    def calculate_priority(self, paper: Dict) -> int:
        """Calculate priority score."""
        score = 0
        
        # Citations
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
        
        # High confidence tags (from methods)
        if paper.get('tag_source') == 'methods':
            score += 25
        
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
        
        # RORs
        if paper.get('rors'):
            score += len(paper['rors']) * 5
        
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
            
            # Extract full text
            body = article.find('.//body')
            if body is not None:
                result['full_text'] = self._extract_text_from_element(body)
            
            # Extract figures
            for fig in article.findall('.//fig'):
                fig_data = {
                    'label': '',
                    'title': '',
                    'caption': '',
                }
                
                label = fig.find('label')
                if label is not None and label.text:
                    fig_data['label'] = label.text
                
                caption = fig.find('caption')
                if caption is not None:
                    title_elem = caption.find('title')
                    if title_elem is not None:
                        fig_data['title'] = self._extract_text_from_element(title_elem)
                    fig_data['caption'] = self._extract_text_from_element(caption)
                
                if fig_data['label'] or fig_data['caption']:
                    result['figures'].append(fig_data)
            
            # Extract supplementary materials
            for supp in article.findall('.//supplementary-material'):
                supp_data = {}
                label = supp.find('label')
                if label is not None and label.text:
                    supp_data['label'] = label.text
                caption = supp.find('caption')
                if caption is not None:
                    supp_data['caption'] = self._extract_text_from_element(caption)
                if supp_data:
                    result['supplementary'].append(supp_data)
            
            self.stats['full_text_fetched'] += 1
            return result
            
        except Exception as e:
            logger.debug(f"PMC fetch error for {pmc_id}: {e}")
            return None
    
    def _extract_text_from_element(self, element) -> str:
        """Extract text from XML element."""
        if element is None:
            return ''
        return ' '.join(element.itertext()).strip()
    
    # ========== CITATIONS ==========
    
    def fetch_citations(self, doi: str, pmid: str) -> Dict:
        """Fetch citation count from multiple sources."""
        result = {
            'citation_count': 0,
            'influential_citation_count': 0,
            'source': None,
            'semantic_scholar_id': None,
        }
        
        # Try Semantic Scholar first
        if doi:
            ss_data = self._fetch_semantic_scholar(doi)
            if ss_data and ss_data.get('citation_count', 0) > 0:
                self.stats['citations_fetched'] += 1
                return ss_data
        
        # Try CrossRef
        if doi:
            cr_data = self._fetch_crossref_citations(doi)
            if cr_data and cr_data.get('citation_count', 0) > 0:
                self.stats['citations_fetched'] += 1
                return cr_data
        
        return result
    
    def _fetch_semantic_scholar(self, doi: str) -> Optional[Dict]:
        """Fetch from Semantic Scholar."""
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
            params = {'fields': 'citationCount,influentialCitationCount,paperId'}
            
            response = self.session.get(url, params=params, timeout=10)
            self.stats['api_calls'] += 1
            time.sleep(0.5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'citation_count': data.get('citationCount', 0),
                    'influential_citation_count': data.get('influentialCitationCount', 0),
                    'source': 'semantic_scholar',
                    'semantic_scholar_id': data.get('paperId'),
                }
        except Exception as e:
            logger.debug(f"Semantic Scholar error: {e}")
        
        return None
    
    def _fetch_crossref_citations(self, doi: str) -> Optional[Dict]:
        """Fetch from CrossRef."""
        try:
            url = f"https://api.crossref.org/works/{doi}"
            
            response = self.session.get(url, timeout=10)
            self.stats['api_calls'] += 1
            time.sleep(0.2)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})
                return {
                    'citation_count': message.get('is-referenced-by-count', 0),
                    'influential_citation_count': 0,
                    'source': 'crossref',
                    'semantic_scholar_id': None,
                }
        except Exception as e:
            logger.debug(f"CrossRef error: {e}")
        
        return None
    
    # ========== PUBMED SEARCH ==========
    
    def search_pubmed(self, query: str, max_results: int = 1000) -> List[str]:
        """Search PubMed and return PMIDs."""
        try:
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': min(max_results, 10000),
                'retmode': 'json',
                'email': self.email,
            }
            
            response = self.session.get(url, params=params, timeout=30)
            self.stats['api_calls'] += 1
            time.sleep(0.34)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            self.stats['found'] += len(pmids)
            
            return pmids
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def fetch_papers(self, pmids: List[str], fetch_full_text: bool = True, 
                     fetch_cites: bool = True) -> List[Dict]:
        """Fetch paper details from PubMed."""
        if not pmids:
            return []
        
        papers = []
        
        # Process in batches
        batch_size = 100
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            
            try:
                url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                params = {
                    'db': 'pubmed',
                    'id': ','.join(batch),
                    'rettype': 'xml',
                    'retmode': 'xml',
                    'email': self.email,
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
        
        return papers
    
    def _parse_article(self, article, fetch_full_text: bool = True, 
                       fetch_cites: bool = True) -> Optional[Dict]:
        """Parse PubMed article XML with smart tag extraction."""
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
            
            # SMART TAG EXTRACTION
            tags = self.extract_tags_smart(title, abstract, full_methods, full_text)
            
            microscopy_techniques = tags['microscopy_techniques']
            organisms = tags['organisms']
            antibody_sources = tags['antibody_sources']
            image_analysis_software = tags['image_analysis_software']
            fluorophores = tags['fluorophores']
            sample_preparation = tags['sample_preparation']
            cell_lines = tags['cell_lines']
            tag_source = tags['source']
            
            # Update stats
            if tag_source == 'methods':
                self.stats['from_methods'] += 1
            else:
                self.stats['from_title_abstract'] += 1
            
            # Extract from full text (URLs/IDs can appear anywhere)
            extraction_text = f"{title} {abstract} {full_methods} {full_text}"
            
            microscope_brands = self.extract_microscope_brands(extraction_text)
            microscope_models = self.extract_microscope_models(extraction_text)
            image_acquisition_software = self.extract_image_acquisition_software(extraction_text)
            protocols = self.extract_protocols(extraction_text)
            repositories, github_url = self.extract_repositories(extraction_text)
            rrids = self.extract_rrids(extraction_text)
            rors = self.extract_rors(extraction_text)
            references = self.extract_references(full_text) if full_text else []
            
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
                
                # CITATIONS
                'citation_count': citation_count,
                'influential_citation_count': influential_citations,
                'citation_source': citation_source,
                'semantic_scholar_id': semantic_scholar_id,
                
                # Categorized tags (smart extraction)
                'microscopy_techniques': microscopy_techniques,
                'organisms': organisms,
                'antibody_sources': antibody_sources,
                'image_analysis_software': image_analysis_software,
                'fluorophores': fluorophores,
                'sample_preparation': sample_preparation,
                'cell_lines': cell_lines,
                'tag_source': tag_source,
                
                # Equipment (from full text)
                'microscope_brands': microscope_brands,
                'microscope_models': microscope_models,
                'image_acquisition_software': image_acquisition_software,
                
                # Resources
                'protocols': protocols,
                'repositories': repositories,
                'github_url': github_url,
                'rrids': rrids,
                'rors': rors,
                'references': references,
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
            
            return paper
            
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            self.stats['errors'] += 1
            return None
    
    # ========== SAVE ==========
    
    def save_paper(self, paper: Dict) -> bool:
        """Save paper to database."""
        conn = self._get_conn()
        
        try:
            conn.execute("""
                INSERT INTO papers (
                    pmid, doi, pmc_id, title, abstract, methods, full_text,
                    authors, journal, year,
                    doi_url, pubmed_url, pmc_url,
                    citation_count, influential_citation_count, citation_source,
                    semantic_scholar_id, citations_updated_at,
                    microscopy_techniques, organisms, antibody_sources,
                    image_analysis_software, image_acquisition_software,
                    sample_preparation, fluorophores, cell_lines,
                    microscope_brands, microscope_models,
                    protocols, repositories, github_url, rrids, rors,
                    supplementary_materials, figures, figure_count,
                    techniques, software, microscope_brand, tag_source,
                    has_full_text, has_figures, has_protocols, has_github, has_data,
                    priority_score
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, CURRENT_TIMESTAMP,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?
                )
            """, (
                paper['pmid'], paper['doi'], paper['pmc_id'],
                paper['title'], paper['abstract'], paper['methods'], paper['full_text'],
                paper['authors'], paper['journal'], paper['year'],
                paper['doi_url'], paper['pubmed_url'], paper['pmc_url'],
                paper['citation_count'], paper['influential_citation_count'],
                paper['citation_source'], paper['semantic_scholar_id'],
                json.dumps(paper['microscopy_techniques']),
                json.dumps(paper['organisms']),
                json.dumps(paper['antibody_sources']),
                json.dumps(paper['image_analysis_software']),
                json.dumps(paper['image_acquisition_software']),
                json.dumps(paper['sample_preparation']),
                json.dumps(paper['fluorophores']),
                json.dumps(paper['cell_lines']),
                json.dumps(paper['microscope_brands']),
                json.dumps(paper['microscope_models']),
                json.dumps(paper['protocols']),
                json.dumps(paper['repositories']),
                paper['github_url'],
                json.dumps(paper['rrids']),
                json.dumps(paper['rors']),
                json.dumps(paper['supplementary_materials']),
                json.dumps(paper['figures']),
                paper['figure_count'],
                json.dumps(paper['techniques']),
                json.dumps(paper['software']),
                paper['microscope_brand'],
                paper['tag_source'],
                paper['has_full_text'], paper['has_figures'],
                paper['has_protocols'], paper['has_github'], paper['has_data'],
                paper['priority_score'],
            ))
            
            conn.commit()
            
            # Track known IDs
            self.known_pmids.add(paper['pmid'])
            if paper['doi']:
                self.known_dois.add(paper['doi'].lower())
            
            self.stats['saved'] += 1
            conn.close()
            return True
            
        except sqlite3.IntegrityError:
            conn.close()
            return False
        except Exception as e:
            self.stats['errors'] += 1
            logger.debug(f"Save error: {e}")
            conn.close()
            return False
    
    # ========== QUERIES ==========
    
    def get_all_queries(self) -> List[Tuple[str, int]]:
        """Return all search queries with priorities."""
        queries = []
        
        # Priority 1: Protocol sources
        protocol_sources = [
            ('protocols.io[Title/Abstract]', 10000),
            ('bio-protocol[Title/Abstract]', 10000),
            ('star protocols[Title/Abstract]', 5000),
            ('jove[Title/Abstract] AND microscopy', 8000),
        ]
        queries.extend(protocol_sources)
        
        # Priority 2: Data repositories
        data_repos = [
            ('zenodo[Title/Abstract] AND microscopy', 15000),
            ('figshare[Title/Abstract] AND microscopy', 10000),
            ('IDR[Title/Abstract] AND imaging', 5000),
            ('bioimage archive[Title/Abstract]', 5000),
            ('EMPIAR[Title/Abstract]', 10000),
            ('github[Title/Abstract] AND microscopy', 20000),
            ('OMERO[Title/Abstract]', 5000),
        ]
        queries.extend(data_repos)
        
        # Priority 3: Super-resolution
        superres = [
            ('STED[Title/Abstract] AND microscopy', 20000),
            ('STORM[Title/Abstract] AND microscopy', 20000),
            ('PALM[Title/Abstract] AND microscopy', 15000),
            ('SMLM[Title/Abstract]', 10000),
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
            ('"lattice light sheet"[Title/Abstract]', 5000),
            ('mesoSPIM[Title/Abstract]', 1000),
        ]
        queries.extend(lightsheet)
        
        # Priority 6: Electron microscopy
        em = [
            ('cryo-EM[Title/Abstract]', 30000),
            ('cryo-ET[Title/Abstract]', 15000),
            ('FIB-SEM[Title/Abstract]', 10000),
            ('"volume EM"[Title/Abstract]', 5000),
        ]
        queries.extend(em)
        
        # Priority 7: Multiphoton
        multiphoton = [
            ('"two-photon"[Title/Abstract] AND microscopy', 25000),
            ('"multiphoton"[Title/Abstract] AND microscopy', 20000),
        ]
        queries.extend(multiphoton)
        
        # Priority 8: Functional imaging
        functional = [
            ('FRET[Title/Abstract] AND microscopy', 20000),
            ('FLIM[Title/Abstract]', 15000),
            ('FRAP[Title/Abstract] AND microscopy', 15000),
            ('"calcium imaging"[Title/Abstract]', 30000),
            ('GCaMP[Title/Abstract]', 20000),
        ]
        queries.extend(functional)
        
        # Priority 9: Live cell
        live = [
            ('"live cell imaging"[Title/Abstract]', 30000),
            ('"time-lapse microscopy"[Title/Abstract]', 20000),
            ('"intravital microscopy"[Title/Abstract]', 15000),
        ]
        queries.extend(live)
        
        # Priority 10: Analysis tools
        analysis = [
            ('"deep learning"[Abstract] AND microscopy', 25000),
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
        ]
        queries.extend(clearing)
        
        # Priority 12: Basic techniques
        basic = [
            ('"fluorescence microscopy"[Title/Abstract]', 50000),
            ('"immunofluorescence"[Title/Abstract]', 40000),
            ('TIRF[Title/Abstract] AND microscopy', 15000),
        ]
        queries.extend(basic)
        
        return queries
    
    # ========== RUN ==========
    
    def run(self, limit: int = None, priority_only: bool = False,
            full_text_only: bool = False, fetch_citations: bool = True):
        """Run scraper with smart tag extraction."""
        logger.info("=" * 70)
        logger.info("MICROHUB PAPER SCRAPER v5.0 - SMART EXTRACTION EDITION")
        logger.info("=" * 70)
        logger.info("Features: Smart tag extraction + Antibody filtering + ROR support")
        logger.info("")
        
        queries = self.get_all_queries()
        
        if priority_only:
            keywords = ['protocol', 'github', 'zenodo', 'figshare', 'idr', 'empiar']
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
            from_methods = 0
            from_abstract = 0
            
            for paper in papers:
                if self.save_paper(paper):
                    saved_this_query += 1
                    total_saved += 1
                    if paper.get('tag_source') == 'methods':
                        from_methods += 1
                    else:
                        from_abstract += 1
                
                if limit and total_saved >= limit:
                    break
            
            logger.info(f"  Saved {saved_this_query} (methods: {from_methods}, title+abstract: {from_abstract})")
            
            # Log progress
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO scrape_log 
                   (query, found, saved, skipped, citations_fetched, from_methods, from_title_abstract) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (query, len(pmids), saved_this_query, len(pmids) - saved_this_query,
                 self.stats['citations_fetched'], from_methods, from_abstract)
            )
            conn.commit()
            conn.close()
        
        # Final stats
        logger.info("\n" + "=" * 70)
        logger.info("SCRAPING COMPLETE - v5.0 SMART EXTRACTION")
        logger.info("=" * 70)
        logger.info(f"Queries run: {query_count}")
        logger.info(f"Papers found: {self.stats['found']:,}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates_skipped']:,}")
        logger.info(f"Papers saved: {self.stats['saved']:,}")
        logger.info(f"")
        logger.info(f"TAG EXTRACTION SOURCE:")
        logger.info(f"  From methods (high confidence): {self.stats['from_methods']:,}")
        logger.info(f"  From title+abstract (reviews): {self.stats['from_title_abstract']:,}")
        logger.info(f"")
        logger.info(f"ENRICHMENT:")
        logger.info(f"  With citations: {self.stats['citations_fetched']:,}")
        logger.info(f"  With full text: {self.stats['full_text_fetched']:,}")
        logger.info(f"  With methods: {self.stats['with_methods']:,}")
        logger.info(f"  With figures: {self.stats['with_figures']:,}")
        logger.info(f"  With protocols: {self.stats['with_protocols']:,}")
        logger.info(f"  With GitHub: {self.stats['with_github']:,}")
        logger.info(f"  With data repos: {self.stats['with_repos']:,}")
        logger.info(f"  With RRIDs: {self.stats['with_rrids']:,}")
        logger.info(f"  With RORs: {self.stats['with_rors']:,}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"API calls: {self.stats['api_calls']:,}")
        
        return self.stats
    
    def update_citations_for_existing(self, limit: int = None):
        """Update citations for existing papers."""
        logger.info("Updating citations for existing papers...")
        
        conn = self._get_conn()
        query = """
            SELECT id, doi, pmid FROM papers 
            WHERE doi IS NOT NULL 
            AND (citations_updated_at IS NULL OR citations_updated_at < datetime('now', '-7 days'))
            ORDER BY citation_count DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = conn.execute(query)
        papers = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(papers)} papers to update")
        
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
                        citations_updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    cite_data['citation_count'],
                    cite_data['influential_citation_count'],
                    cite_data['source'],
                    cite_data['semantic_scholar_id'],
                    paper_id
                ))
                conn.commit()
                conn.close()
                updated += 1
            
            time.sleep(0.5)
        
        logger.info(f"Updated {updated} papers")


def main():
    parser = argparse.ArgumentParser(description='MicroHub Scraper v5.0 - Smart Extraction Edition')
    parser.add_argument('--db', default='microhub.db', help='Database path')
    parser.add_argument('--email', help='Email for API access')
    parser.add_argument('--limit', type=int, help='Limit total papers')
    parser.add_argument('--priority-only', action='store_true', help='Only high-priority sources')
    parser.add_argument('--full-text-only', action='store_true', help='Only save papers with full text')
    parser.add_argument('--no-citations', action='store_true', help='Skip citation fetching')
    parser.add_argument('--update-citations', action='store_true', help='Update citations for existing papers')
    parser.add_argument('--update-limit', type=int, help='Limit papers for citation update')
    
    args = parser.parse_args()
    
    scraper = MicroHubScraperV5(db_path=args.db, email=args.email)
    
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
