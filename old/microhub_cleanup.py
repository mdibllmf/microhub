#!/usr/bin/env python3
"""
MICROHUB TAG CLEANUP SCRIPT
===========================
Run this AFTER the main scraper to clean up over-tagged papers.

Usage:
  python microhub_cleanup.py                     # Clean all papers
  python microhub_cleanup.py --limit 1000        # Clean first 1000
  python microhub_cleanup.py --high-citation     # Only papers with 50+ citations
  python microhub_cleanup.py --dry-run           # Preview changes without saving

What it fixes:
  - Removes techniques mentioned in negative context ("unlike STED", "previous studies used AFM")
  - Filters antibody source species from organisms (rabbit, goat, etc.)
  - Prioritizes Methods section for tag extraction
"""

import sqlite3
import json
import re
import argparse
import logging
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# NEGATIVE CONTEXT PATTERNS
# ============================================================================

NEGATIVE_CONTEXT_PATTERNS = [
    # Comparison phrases
    r'(?:compared?\s+to|in\s+contrast\s+to|unlike|versus|vs\.?)\s+',
    r'(?:rather\s+than|instead\s+of|alternative\s+to)\s+',
    
    # Literature/background phrases
    r'(?:previous(?:ly)?|prior|earlier)\s+(?:studies?|work|reports?|papers?|methods?)\s+',
    r'(?:previous(?:ly)?|prior|earlier)\s+\w+\s+(?:have|has)\s+(?:used|employed|applied)',
    r'(?:has|have)\s+been\s+(?:used|employed|applied|demonstrated)\s+(?:by|in)\s+(?:others?|previous)',
    r'(?:traditionally|conventionally|typically|commonly)\s+(?:used?|employed?|applied?)',
    r'(?:other|alternative|different)\s+(?:methods?|techniques?|approaches?)\s+(?:such\s+as|like|including)',
    r'(?:studies?|work|papers?)\s+(?:have|has)\s+(?:used|employed|applied|demonstrated)',
    r'(?:researchers?|groups?|labs?|authors?)\s+(?:have|has)\s+(?:used|employed|applied)',
    
    # Limitation/alternative phrases  
    r'(?:limitations?\s+of|drawbacks?\s+of|disadvantages?\s+of)',
    r'(?:although|while|whereas)\s+\w+\s+(?:can|could|may|might)\s+be\s+used',
    r'(?:but|however)\s+(?:these|this|such)\s+(?:methods?|techniques?|approaches?)\s+(?:are|is|require)',
    r'(?:labor[\s-]?intensive|time[\s-]?consuming|expensive|difficult|challenging)\b',
    
    # Future/hypothetical phrases
    r'(?:could\s+be|might\s+be|may\s+be)\s+(?:used|applied|employed)',
    r'(?:future\s+(?:studies?|work|research)|in\s+the\s+future)',
    
    # Citation context
    r'\(\s*\d+\s*[,;]\s*\d+\s*\)',
    r'(?:reviewed?\s+(?:in|by)|see\s+also|for\s+review)',
]

NEGATIVE_PATTERNS_COMPILED = [re.compile(p, re.IGNORECASE) for p in NEGATIVE_CONTEXT_PATTERNS]


# ============================================================================
# ANTIBODY PATTERNS
# ============================================================================

ANTIBODY_PATTERNS = [
    # "anti-rabbit", "anti-mouse", etc. - THE MOST COMMON FORMAT
    r'anti-?(?:rabbit|mouse|rat|goat|donkey|chicken|guinea\s*pig)\b',
    
    # "rabbit anti-X", "rabbit polyclonal", "rabbit IgG"
    r'(?:rabbit|mouse|rat|goat|donkey|chicken|guinea\s*pig)\s+(?:anti-?\w*|polyclonal|monoclonal|IgG|IgM|primary|secondary)',
    
    # "rabbit antibody", "rabbit serum"
    r'(?:rabbit|mouse|rat|goat|donkey|chicken|guinea\s*pig)\s+(?:anti-?\w+\s+)?(?:antibod(?:y|ies)|serum|antiserum)',
    
    # "raised in rabbit", "from rabbit"
    r'(?:raised\s+in|from)\s+(?:rabbit|mouse|rat|goat|donkey|chicken|guinea\s*pig)',
    
    # "rabbit origin"
    r'(?:rabbit|mouse|rat|goat|donkey|chicken|guinea\s*pig)\s+origin',
    
    # "secondary antibody from rabbit"
    r'secondary\s+(?:antibod(?:y|ies))?\s*(?:from|raised\s+in)?\s*(?:rabbit|mouse|rat|goat|donkey|chicken)',
    
    # "goat anti-rabbit" (secondary antibody context)
    r'(?:rabbit|mouse|rat|goat|donkey|chicken|guinea\s*pig)\s+anti-?(?:rabbit|mouse|rat|goat|donkey|chicken|guinea\s*pig)',
    
    # "Alexa-conjugated anti-rabbit", "HRP-conjugated anti-mouse"
    r'(?:alexa|hrp|fitc|cy\d|dylight|irdye)[-\s]?(?:conjugated|labeled)?\s*anti-?(?:rabbit|mouse|rat|goat|donkey|chicken)',
]

ANTIBODY_PATTERNS_COMPILED = [re.compile(p, re.IGNORECASE) for p in ANTIBODY_PATTERNS]

ANTIBODY_SOURCE_SPECIES = {'rabbit', 'goat', 'donkey', 'guinea pig', 'chicken'}


# ============================================================================
# TECHNIQUE PATTERNS (for re-validation)
# ============================================================================

TECHNIQUE_PATTERNS = {
    'STED': [r'\bsted\b', r'stimulated emission depletion'],
    'STORM': [r'\bstorm\b', r'stochastic optical reconstruction'],
    'PALM': [r'\bpalm\b', r'photoactivated localization'],
    'dSTORM': [r'\bdstorm\b', r'd-storm'],
    'SIM': [r'structured illumination', r'\bsim\b.*microscop'],
    'SMLM': [r'\bsmlm\b', r'single molecule localization'],
    'Super-Resolution': [r'super-resolution', r'super resolution', r'nanoscopy'],
    'DNA-PAINT': [r'dna-paint', r'paint microscopy'],
    'MINFLUX': [r'minflux'],
    'Expansion Microscopy': [r'expansion microscopy', r'\bexm\b'],
    'RESOLFT': [r'resolft'],
    'SOFI': [r'\bsofi\b'],
    'Confocal': [r'confocal', r'\bclsm\b', r'laser scanning confocal'],
    'Two-Photon': [r'two-photon', r'two photon', r'2-photon', r'multiphoton'],
    'Three-Photon': [r'three-photon', r'three photon', r'3-photon'],
    'Light Sheet': [r'light sheet', r'light-sheet', r'\bspim\b', r'selective plane illumination'],
    'Lattice Light Sheet': [r'lattice light sheet', r'lls microscopy'],
    'MesoSPIM': [r'mesospim'],
    'Spinning Disk': [r'spinning disk', r'spinning-disk'],
    'TIRF': [r'\btirf\b', r'total internal reflection'],
    'Airyscan': [r'airyscan'],
    'Widefield': [r'widefield', r'wide-field'],
    'Epifluorescence': [r'epifluorescence'],
    'Brightfield': [r'brightfield', r'bright-field'],
    'Phase Contrast': [r'phase contrast'],
    'DIC': [r'\bdic\b', r'differential interference contrast'],
    'Darkfield': [r'darkfield', r'dark-field'],
    'Cryo-EM': [r'cryo-em', r'cryo-electron', r'cryoem'],
    'Cryo-ET': [r'cryo-et', r'cryo-tomography', r'electron tomography'],
    'TEM': [r'transmission electron microscopy', r'\btem\b.*microscop'],
    'SEM': [r'scanning electron microscopy', r'\bsem\b.*microscop'],
    'FIB-SEM': [r'fib-sem', r'focused ion beam'],
    'Array Tomography': [r'array tomography'],
    'Serial Block-Face SEM': [r'serial block-face', r'sbfsem'],
    'Volume EM': [r'volume em', r'volume electron'],
    'Immuno-EM': [r'immuno-em', r'immunoelectron'],
    'Negative Stain EM': [r'negative stain'],
    'FRET': [r'\bfret\b', r'fluorescence resonance energy transfer'],
    'FLIM': [r'\bflim\b', r'fluorescence lifetime'],
    'FRAP': [r'\bfrap\b', r'fluorescence recovery after photobleaching'],
    'FLIP': [r'\bflip\b', r'fluorescence loss in photobleaching'],
    'FCS': [r'\bfcs\b', r'fluorescence correlation spectroscopy'],
    'FCCS': [r'\bfccs\b'],
    'Calcium Imaging': [r'calcium imaging', r'ca2\+ imaging'],
    'Voltage Imaging': [r'voltage imaging'],
    'Optogenetics': [r'optogenetics'],
    'Live Cell Imaging': [r'live cell', r'live-cell', r'time-lapse'],
    'Intravital': [r'intravital', r'in vivo imaging'],
    'High-Content Screening': [r'high-content', r'high content'],
    'Deconvolution': [r'deconvolution'],
    'Optical Sectioning': [r'optical sectioning'],
    'Z-Stack': [r'z-stack', r'z stack', r'z-series'],
    '3D Imaging': [r'3d imaging', r'three-dimensional imaging'],
    '4D Imaging': [r'4d imaging'],
    'Single Molecule': [r'single molecule', r'single-molecule'],
    'Single Particle': [r'single particle', r'single-particle'],
    'Holographic': [r'holographic'],
    'OCT': [r'optical coherence tomography', r'\boct\b'],
    'Photoacoustic': [r'photoacoustic'],
    'AFM': [r'atomic force microscopy', r'\bafm\b'],
    'CLEM': [r'\bclem\b', r'correlative light', r'correlative microscopy'],
    'Raman': [r'raman microscopy', r'raman imaging'],
    'CARS': [r'cars microscopy'],
    'SRS': [r'\bsrs\b', r'stimulated raman'],
    'Second Harmonic': [r'second harmonic', r'\bshg\b'],
    'Polarization': [r'polarization microscopy'],
    'Fluorescence Microscopy': [r'fluorescence microscopy'],
    'Immunofluorescence': [r'immunofluorescence'],
}


ORGANISM_PATTERNS = {
    'mouse': [r'\bmouse\b', r'\bmice\b', r'\bmurine\b'],
    'human': [r'\bhuman\b', r'\bpatient\b'],
    'rat': [r'\brat\b', r'\brattus\b'],
    'zebrafish': [r'\bzebrafish\b', r'\bdanio\s*rerio\b'],
    'drosophila': [r'\bdrosophila\b', r'\bfruit\s*fly\b'],
    'c.elegans': [r'\bc\.\s*elegans\b', r'\bcaenorhabditis\b'],
    'xenopus': [r'\bxenopus\b'],
    'Chicken': [r'\bchicken\b', r'\bchick\b', r'\bgallus\b'],
    'Pig': [r'\bpig\b', r'\bporcine\b'],
    'Monkey': [r'\bmonkey\b', r'\bmacaque\b', r'\bprimate\b'],
    'Rabbit': [r'\brabbit\b', r'\boryctolagus\b'],
    'Dog': [r'\bdog\b', r'\bcanine\b'],
    'yeast': [r'\byeast\b', r'\bsaccharomyces\b'],
    'E. coli': [r'\be\.\s*coli\b', r'\bescherichia\b'],
    'Bacteria': [r'\bbacteria\b', r'\bbacterial\b'],
    'arabidopsis': [r'\barabidopsis\b'],
    'Plant': [r'\bplant\s*cell\b', r'\bplant\s*tissue\b'],
    'Tobacco': [r'\btobacco\b'],
    'Maize': [r'\bmaize\b', r'\bzea\s*mays\b'],
    'Organoid': [r'\borganoid\b'],
    'Spheroid': [r'\bspheroid\b'],
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_methods_section(full_text: str) -> str:
    """Extract Methods section from full text."""
    if not full_text:
        return ""
    
    methods_headers = [
        r'(?:^|\n)\s*(?:materials?\s+and\s+)?methods?\s*(?:\n|$)',
        r'(?:^|\n)\s*experimental\s+(?:procedures?|methods?|section)\s*(?:\n|$)',
        r'(?:^|\n)\s*(?:star\s+)?methods?\s*(?:\n|$)',
        r'(?:^|\n)\s*procedures?\s*(?:\n|$)',
    ]
    
    end_headers = [
        r'(?:^|\n)\s*results?\s*(?:\n|$)',
        r'(?:^|\n)\s*discussion\s*(?:\n|$)',
        r'(?:^|\n)\s*conclusions?\s*(?:\n|$)',
        r'(?:^|\n)\s*acknowledg(?:e)?ments?\s*(?:\n|$)',
        r'(?:^|\n)\s*references?\s*(?:\n|$)',
    ]
    
    text_lower = full_text.lower()
    
    start_pos = None
    for pattern in methods_headers:
        match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
        if match:
            start_pos = match.end()
            break
    
    if start_pos is None:
        return ""
    
    end_pos = len(full_text)
    remaining_text = text_lower[start_pos:]
    
    for pattern in end_headers:
        match = re.search(pattern, remaining_text, re.IGNORECASE | re.MULTILINE)
        if match:
            end_pos = start_pos + match.start()
            break
    
    return full_text[start_pos:end_pos].strip()


def is_negative_context(text: str, match_start: int, match_end: int) -> bool:
    """Check if match is in negative/comparative context."""
    context_before = text[max(0, match_start - 200):match_start]
    
    # Find sentence start for broader context
    context_sentence_start = max(0, match_start - 300)
    for i in range(match_start - 1, context_sentence_start, -1):
        if i < len(text) and text[i] in '.!?\n':
            context_sentence_start = i + 1
            break
    
    context_sentence = text[context_sentence_start:match_start]
    
    for pattern in NEGATIVE_PATTERNS_COMPILED:
        if pattern.search(context_before[-120:] if len(context_before) > 120 else context_before):
            return True
        if pattern.search(context_sentence):
            return True
    
    return False


def is_antibody_context(text: str, species: str, match_start: int, match_end: int) -> bool:
    """Check if species mention is in antibody context."""
    if species.lower() not in ANTIBODY_SOURCE_SPECIES:
        return False
    
    # Use larger context window (100 chars each side)
    context_start = max(0, match_start - 100)
    context_end = min(len(text), match_end + 100)
    context = text[context_start:context_end]
    
    for pattern in ANTIBODY_PATTERNS_COMPILED:
        if pattern.search(context):
            return True
    
    return False


def find_technique_in_text(text: str, technique: str, patterns: List[str]) -> List[Tuple[int, int]]:
    """Find all occurrences of a technique in text."""
    matches = []
    text_lower = text.lower()
    
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            matches.append((match.start(), match.end()))
    
    return matches


def find_organism_in_text(text: str, organism: str, patterns: List[str]) -> List[Tuple[int, int]]:
    """Find all occurrences of an organism in text."""
    matches = []
    text_lower = text.lower()
    
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            matches.append((match.start(), match.end()))
    
    return matches


# ============================================================================
# MAIN CLEANUP FUNCTIONS
# ============================================================================

def clean_techniques(techniques: List[str], all_text: str, methods_text: str) -> Tuple[List[str], List[str]]:
    """
    Clean technique tags.
    
    Returns:
        Tuple of (kept_techniques, removed_techniques)
    """
    if not techniques:
        return [], []
    
    kept = []
    removed = []
    
    for technique in techniques:
        patterns = TECHNIQUE_PATTERNS.get(technique, [])
        if not patterns:
            # Unknown technique, keep it
            kept.append(technique)
            continue
        
        # Check if it appears in methods section (high confidence)
        if methods_text:
            methods_matches = find_technique_in_text(methods_text, technique, patterns)
            if methods_matches:
                kept.append(technique)
                continue
        
        # Check full text with negative context detection
        all_matches = find_technique_in_text(all_text, technique, patterns)
        
        if not all_matches:
            # Not actually found (shouldn't happen, but safety check)
            removed.append(technique)
            continue
        
        # Check if ALL matches are in negative context
        all_negative = True
        for start, end in all_matches:
            if not is_negative_context(all_text, start, end):
                all_negative = False
                break
        
        if all_negative:
            removed.append(technique)
        else:
            kept.append(technique)
    
    return kept, removed


def clean_organisms(organisms: List[str], all_text: str, methods_text: str) -> Tuple[List[str], List[str]]:
    """
    Clean organism tags.
    
    Returns:
        Tuple of (kept_organisms, removed_organisms)
    """
    if not organisms:
        return [], []
    
    kept = []
    removed = []
    
    for organism in organisms:
        patterns = ORGANISM_PATTERNS.get(organism, [])
        if not patterns:
            kept.append(organism)
            continue
        
        # Check methods section first
        if methods_text:
            methods_matches = find_organism_in_text(methods_text, organism, patterns)
            non_antibody_in_methods = False
            for start, end in methods_matches:
                if not is_antibody_context(methods_text, organism, start, end):
                    non_antibody_in_methods = True
                    break
            
            if non_antibody_in_methods:
                kept.append(organism)
                continue
        
        # Check full text
        all_matches = find_organism_in_text(all_text, organism, patterns)
        
        if not all_matches:
            removed.append(organism)
            continue
        
        # For antibody source species, require non-antibody context
        if organism.lower() in ANTIBODY_SOURCE_SPECIES:
            has_non_antibody = False
            for start, end in all_matches:
                if not is_antibody_context(all_text, organism, start, end):
                    has_non_antibody = True
                    break
            
            if has_non_antibody:
                kept.append(organism)
            else:
                removed.append(organism)
        else:
            kept.append(organism)
    
    return kept, removed


def process_paper(paper: Dict) -> Dict:
    """
    Process a single paper and return cleaned tags.
    
    Args:
        paper: Dict with id, title, abstract, methods, full_text, 
               microscopy_techniques, organisms
    
    Returns:
        Dict with original and cleaned tags
    """
    title = paper.get('title', '') or ''
    abstract = paper.get('abstract', '') or ''
    methods = paper.get('methods', '') or ''
    full_text = paper.get('full_text', '') or ''
    
    # Build text sources
    all_text = f"{title} {abstract} {methods} {full_text}"
    methods_text = methods if methods else extract_methods_section(full_text)
    
    # Get original tags
    orig_techniques = paper.get('microscopy_techniques', [])
    orig_organisms = paper.get('organisms', [])
    
    if isinstance(orig_techniques, str):
        orig_techniques = json.loads(orig_techniques) if orig_techniques else []
    if isinstance(orig_organisms, str):
        orig_organisms = json.loads(orig_organisms) if orig_organisms else []
    
    # Clean tags
    kept_tech, removed_tech = clean_techniques(orig_techniques, all_text, methods_text)
    kept_org, removed_org = clean_organisms(orig_organisms, all_text, methods_text)
    
    return {
        'id': paper.get('id'),
        'title': title[:80],
        'original_techniques': orig_techniques,
        'cleaned_techniques': kept_tech,
        'removed_techniques': removed_tech,
        'original_organisms': orig_organisms,
        'cleaned_organisms': kept_org,
        'removed_organisms': removed_org,
        'techniques_changed': set(orig_techniques) != set(kept_tech),
        'organisms_changed': set(orig_organisms) != set(kept_org),
    }


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_papers(db_path: str, limit: int = None, high_citation: bool = False, 
               min_tags: int = 3) -> List[Dict]:
    """Fetch papers from database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    query = """
        SELECT id, title, abstract, methods, full_text, 
               microscopy_techniques, organisms, citation_count
        FROM papers 
        WHERE (microscopy_techniques IS NOT NULL AND microscopy_techniques != '[]')
           OR (organisms IS NOT NULL AND organisms != '[]')
    """
    
    if high_citation:
        query += " AND citation_count >= 50"
    
    query += " ORDER BY citation_count DESC"
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor = conn.execute(query)
    papers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Filter to papers that potentially need cleaning (only if min_tags > 0)
    if min_tags > 0:
        filtered = []
        for p in papers:
            tech = json.loads(p.get('microscopy_techniques', '[]') or '[]')
            orgs = json.loads(p.get('organisms', '[]') or '[]')
            
            # Include if has enough technique tags
            if len(tech) >= min_tags:
                filtered.append(p)
                continue
            
            # Also include if has potential antibody source species
            antibody_species = {'Rabbit', 'Goat', 'Donkey', 'Guinea Pig', 'Chicken', 
                              'rabbit', 'goat', 'donkey', 'guinea pig', 'chicken'}
            if any(org in antibody_species for org in orgs):
                filtered.append(p)
                
        papers = filtered
    # When min_tags=0, process all papers (no filtering)
    
    return papers


def update_paper_tags(db_path: str, paper_id: int, techniques: List[str], organisms: List[str]):
    """Update paper tags in database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        UPDATE papers 
        SET microscopy_techniques = ?,
            techniques = ?,
            organisms = ?,
            updated_at = datetime('now')
        WHERE id = ?
    """, (
        json.dumps(techniques),
        json.dumps(techniques),  # Also update legacy field
        json.dumps(organisms),
        paper_id
    ))
    conn.commit()
    conn.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='MicroHub Tag Cleanup Script')
    parser.add_argument('--db', default='microhub.db', help='Database path')
    parser.add_argument('--limit', type=int, help='Limit papers to process')
    parser.add_argument('--high-citation', action='store_true', help='Only papers with 50+ citations')
    parser.add_argument('--min-tags', type=int, default=0, help='Only papers with N+ technique tags (0 = all papers)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
    parser.add_argument('--verbose', action='store_true', help='Show all changes')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("MICROHUB TAG CLEANUP")
    logger.info("=" * 60)
    
    # Load papers
    logger.info(f"Loading papers from {args.db}...")
    papers = get_papers(
        args.db, 
        limit=args.limit, 
        high_citation=args.high_citation,
        min_tags=args.min_tags
    )
    logger.info(f"Found {len(papers)} papers to process")
    
    if not papers:
        logger.info("No papers to process")
        return
    
    # Process papers
    stats = {
        'processed': 0,
        'techniques_cleaned': 0,
        'organisms_cleaned': 0,
        'tags_removed': 0,
        'unchanged': 0,
    }
    
    for i, paper in enumerate(papers):
        result = process_paper(paper)
        stats['processed'] += 1
        
        changed = result['techniques_changed'] or result['organisms_changed']
        
        if changed:
            if result['techniques_changed']:
                stats['techniques_cleaned'] += 1
                stats['tags_removed'] += len(result['removed_techniques'])
            
            if result['organisms_changed']:
                stats['organisms_cleaned'] += 1
                stats['tags_removed'] += len(result['removed_organisms'])
            
            if args.verbose or args.dry_run:
                logger.info(f"\n[{i+1}] {result['title']}...")
                if result['removed_techniques']:
                    logger.info(f"  Techniques removed: {result['removed_techniques']}")
                    logger.info(f"  Techniques kept: {result['cleaned_techniques']}")
                if result['removed_organisms']:
                    logger.info(f"  Organisms removed: {result['removed_organisms']}")
                    logger.info(f"  Organisms kept: {result['cleaned_organisms']}")
            
            # Update database
            if not args.dry_run:
                update_paper_tags(
                    args.db,
                    result['id'],
                    result['cleaned_techniques'],
                    result['cleaned_organisms']
                )
        else:
            stats['unchanged'] += 1
        
        # Progress
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i+1}/{len(papers)} papers...")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("CLEANUP COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Papers processed: {stats['processed']}")
    logger.info(f"Papers with techniques cleaned: {stats['techniques_cleaned']}")
    logger.info(f"Papers with organisms cleaned: {stats['organisms_cleaned']}")
    logger.info(f"Total tags removed: {stats['tags_removed']}")
    logger.info(f"Papers unchanged: {stats['unchanged']}")
    
    if args.dry_run:
        logger.info("\n*** DRY RUN - No changes saved ***")


if __name__ == '__main__':
    main()