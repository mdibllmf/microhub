#!/usr/bin/env python3
"""
MicroHub Paper Cleanup and Re-tagging Script
Cleans up JSON data and extracts missing tags from text content.
"""

import json
import re
import sys
from typing import List, Dict, Set, Optional

# ============================================================================
# TAG DICTIONARIES - Comprehensive patterns for extraction
# ============================================================================

MICROSCOPY_TECHNIQUES = {
    'Confocal': [r'\bconfocal\b'],
    'Two-Photon': [r'\btwo.?photon\b', r'\b2.?photon\b', r'\bmultiphoton\b'],
    'STED': [r'\bsted\b', r'stimulated emission depletion'],
    'PALM': [r'\bpalm\b', r'photoactivated localization'],
    'STORM': [r'\bstorm\b', r'stochastic optical reconstruction'],
    'SIM': [r'\bsim\b', r'structured illumination'],
    'Light-Sheet': [r'\blight.?sheet\b', r'\blsfm\b', r'\bspim\b'],
    'Lattice Light-Sheet': [r'lattice\s+light.?sheet'],
    'Spinning Disk': [r'\bspinning\s*disk\b'],
    'TIRF': [r'\btirf\b', r'total internal reflection'],
    'FRAP': [r'\bfrap\b', r'fluorescence recovery'],
    'FRET': [r'\bfret\b', r'förster resonance', r'fluorescence resonance energy transfer'],
    'FLIM': [r'\bflim\b', r'fluorescence lifetime'],
    'FCS': [r'\bfcs\b', r'fluorescence correlation spectroscopy'],
    'Super-Resolution': [r'\bsuper.?resolution\b', r'\bnanoscopy\b'],
    'Expansion Microscopy': [r'\bexpansion\s+microscopy\b', r'\bexm\b'],
    'Cryo-EM': [r'\bcryo.?em\b', r'\bcryo.?electron\b'],
    'Cryo-ET': [r'\bcryo.?et\b', r'cryo.?electron tomography'],
    'SEM': [r'\bsem\b', r'scanning electron microscop'],
    'TEM': [r'\btem\b', r'transmission electron microscop'],
    'AFM': [r'\bafm\b', r'atomic force microscop'],
    'Phase Contrast': [r'\bphase\s*contrast\b'],
    'DIC': [r'\bdic\b', r'differential interference contrast'],
    'Brightfield': [r'\bbright.?field\b'],
    'Fluorescence Microscopy': [r'\bfluorescence\s+microscop'],
    'Widefield': [r'\bwide.?field\b'],
    'Deconvolution': [r'\bdeconvolution\b'],
    'Live Cell Imaging': [r'\blive.?cell\s+imaging\b', r'\btime.?lapse\b'],
    'Intravital': [r'\bintravital\b'],
    'Multiphoton': [r'\bmultiphoton\b'],
    'Single Molecule': [r'\bsingle.?molecule\b', r'\bsmlm\b'],
    'High-Content Screening': [r'\bhigh.?content\b', r'\bhcs\b'],
    'Z-Stack': [r'\bz.?stack\b'],
    '3D Imaging': [r'\b3d\s+imag', r'\bthree.?dimensional\s+imag'],
    'Raman': [r'\braman\b'],
    'CARS': [r'\bcars\b', r'coherent anti.?stokes'],
    'SHG': [r'\bshg\b', r'second harmonic generation'],
    'OCT': [r'\boct\b', r'optical coherence tomography'],
    'Holographic': [r'\bholograph'],
    'Electron Tomography': [r'\belectron\s+tomograph'],
    'Single Particle': [r'\bsingle.?particle\b'],
}

IMAGE_ANALYSIS_SOFTWARE = {
    'Fiji': [r'\bfiji\b'],
    'ImageJ': [r'\bimagej\b'],
    'CellProfiler': [r'\bcellprofiler\b'],
    'Imaris': [r'\bimaris\b'],
    'Arivis': [r'\barivis\b'],
    'HALO': [r'\bhalo\b.*patholog', r'\bhalo\s+ai\b'],
    'QuPath': [r'\bqupath\b'],
    'Icy': [r'\bicy\b.*software', r'\bicy\s+platform\b'],
    'Ilastik': [r'\bilastik\b'],
    'napari': [r'\bnapari\b'],
    'ZEN': [r'\bzen\b.*software', r'\bzen\s+blue\b', r'\bzen\s+black\b'],
    'NIS-Elements': [r'\bnis.?elements\b'],
    'MetaMorph': [r'\bmetamorph\b'],
    'Volocity': [r'\bvolocity\b'],
    'Huygens': [r'\bhuygens\b'],
    'Amira': [r'\bamira\b'],
    'Dragonfly': [r'\bdragonfly\b.*software'],
    'OMERO': [r'\bomero\b'],
    'Bio-Formats': [r'\bbio.?formats\b'],
    'CellPose': [r'\bcellpose\b'],
    'StarDist': [r'\bstardist\b'],
    'DeepCell': [r'\bdeepcell\b'],
    'Python': [r'\bpython\b'],
    'MATLAB': [r'\bmatlab\b'],
    'R': [r'\br\s+software\b', r'\br\s+package\b', r'\br\s+statistical\b'],
    'scikit-image': [r'\bscikit.?image\b', r'\bskimage\b'],
    'U-Net': [r'\bu.?net\b'],
    'RELION': [r'\brelion\b'],
    'cryoSPARC': [r'\bcryosparc\b'],
    'EMAN2': [r'\beman2?\b'],
    'IMOD': [r'\bimod\b'],
    'SerialEM': [r'\bserialem\b'],
    'Chimera': [r'\bchimera\b.*ucsf', r'\bucsf\s+chimera\b'],
    'ChimeraX': [r'\bchimerax\b'],
    'PyMOL': [r'\bpymol\b'],
    'Mask R-CNN': [r'\bmask\s*r.?cnn\b'],
    'ThunderSTORM': [r'\bthunderstorm\b'],
    'Vaa3D': [r'\bvaa3d\b'],
    'Neurolucida': [r'\bneurolucida\b'],
}

MICROSCOPE_BRANDS = {
    'Zeiss': [r'\bzeiss\b', r'\bcarl zeiss\b'],
    'Leica': [r'\bleica\b'],
    'Nikon': [r'\bnikon\b'],
    'Olympus': [r'\bolympus\b'],
    'Evident': [r'\bevident\b.*microscop'],
    'Thermo Fisher': [r'\bthermo\s*fisher\b', r'\bfei\s+company\b'],
    'JEOL': [r'\bjeol\b'],
    'Bruker': [r'\bbruker\b'],
    'Andor': [r'\bandor\b'],
    'Hamamatsu': [r'\bhamamatsu\b'],
    'PerkinElmer': [r'\bperkin\s*elmer\b'],
    'Molecular Devices': [r'\bmolecular\s+devices\b'],
    'Yokogawa': [r'\byokogawa\b'],
    '3i': [r'\b3i\b.*imaging', r'intelligent imaging innovations'],
    'Visitech': [r'\bvisitech\b'],
    'Abberior': [r'\babberior\b'],
    'PicoQuant': [r'\bpicoquant\b'],
    'Thorlabs': [r'\bthorlabs\b'],
    'Photron': [r'\bphotron\b'],
    'Luxendo': [r'\bluxendo\b'],
    'LaVision BioTec': [r'\blavision\b'],
}

FLUOROPHORES = {
    'GFP': [r'\bgfp\b', r'\bgreen fluorescent protein\b'],
    'EGFP': [r'\begfp\b', r'\benhanced gfp\b'],
    'mNeonGreen': [r'\bmneongreen\b'],
    'mClover': [r'\bmclover\b'],
    'YFP': [r'\byfp\b', r'\byellow fluorescent protein\b'],
    'EYFP': [r'\beyfp\b'],
    'mVenus': [r'\bmvenus\b'],
    'RFP': [r'\brfp\b', r'\bred fluorescent protein\b'],
    'mCherry': [r'\bmcherry\b'],
    'tdTomato': [r'\btdtomato\b'],
    'mScarlet': [r'\bmscarlet\b'],
    'mKate2': [r'\bmkate2?\b'],
    'CFP': [r'\bcfp\b', r'\bcyan fluorescent protein\b'],
    'mCerulean': [r'\bmcerulean\b'],
    'mTurquoise': [r'\bmturquoise\b'],
    'BFP': [r'\bbfp\b', r'\bblue fluorescent protein\b'],
    'mTagBFP': [r'\bmtagbfp\b'],
    'Alexa Fluor 488': [r'\balexa\s*fluor?\s*488\b', r'\baf488\b'],
    'Alexa Fluor 555': [r'\balexa\s*fluor?\s*555\b', r'\baf555\b'],
    'Alexa Fluor 568': [r'\balexa\s*fluor?\s*568\b', r'\baf568\b'],
    'Alexa Fluor 594': [r'\balexa\s*fluor?\s*594\b', r'\baf594\b'],
    'Alexa Fluor 647': [r'\balexa\s*fluor?\s*647\b', r'\baf647\b'],
    'Cy3': [r'\bcy3\b', r'\bcyanine\s*3\b'],
    'Cy5': [r'\bcy5\b', r'\bcyanine\s*5\b'],
    'DAPI': [r'\bdapi\b'],
    'Hoechst': [r'\bhoechst\b'],
    'DRAQ5': [r'\bdraq5\b'],
    'SYTOX': [r'\bsytox\b'],
    'Propidium Iodide': [r'\bpropidium\s+iodide\b', r'\bpi\s+stain'],
    'MitoTracker': [r'\bmitotracker\b'],
    'LysoTracker': [r'\blysotracker\b'],
    'ER-Tracker': [r'\ber.?tracker\b'],
    'Phalloidin': [r'\bphalloidin\b'],
    'WGA': [r'\bwga\b', r'\bwheat germ agglutinin\b'],
    'BODIPY': [r'\bbodipy\b'],
    'DiI': [r'\bdii\b'],
    'DiO': [r'\bdio\b'],
    'Fluo-4': [r'\bfluo.?4\b'],
    'Fura-2': [r'\bfura.?2\b'],
    'GCaMP': [r'\bgcamp\b'],
    'jRGECO': [r'\bjrgeco\b'],
    'Calcein': [r'\bcalcein\b'],
    'FITC': [r'\bfitc\b'],
    'TRITC': [r'\btritc\b'],
    'Texas Red': [r'\btexas\s+red\b'],
    'Rhodamine': [r'\brhodamine\b'],
    'ATTO 488': [r'\batto\s*488\b'],
    'ATTO 565': [r'\batto\s*565\b'],
    'ATTO 647': [r'\batto\s*647\b'],
    'mEos': [r'\bmeos\b'],
    'Dendra2': [r'\bdendra2?\b'],
    'mMaple': [r'\bmmaple\b'],
    'PA-GFP': [r'\bpa.?gfp\b'],
    'mEmerald': [r'\bmemerald\b'],
}

ORGANISMS = {
    'Mouse': [r'\bmouse\b', r'\bmice\b', r'\bmurine\b', r'\bmus\s*musculus\b'],
    'Human': [r'\bhuman\b', r'\bpatient\b', r'\bhomo\s*sapiens\b'],
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
    'Organoid': [r'\borganoid\b'],
    'Spheroid': [r'\bspheroid\b'],
}

CELL_LINES = {
    'HeLa': [r'\bhela\b'],
    'HEK293': [r'\bhek\s*293\b', r'\bhek293\b'],
    'HEK293T': [r'\bhek\s*293t\b', r'\b293t\b'],
    'U2OS': [r'\bu2os\b', r'\bu.?2\s*os\b'],
    'COS-7': [r'\bcos.?7\b'],
    'CHO': [r'\bcho\s+cell\b'],
    'NIH 3T3': [r'\bnih\s*3t3\b', r'\b3t3\b'],
    'MCF7': [r'\bmcf.?7\b'],
    'A549': [r'\ba549\b'],
    'MDCK': [r'\bmdck\b'],
    'Vero': [r'\bvero\b.*cell'],
    'PC12': [r'\bpc.?12\b'],
    'SH-SY5Y': [r'\bsh.?sy5y\b'],
    'iPSC': [r'\bipsc\b', r'\binduced pluripotent\b'],
    'ESC': [r'\besc\b.*cell', r'\bembryonic stem\b'],
    'MEF': [r'\bmef\b', r'\bmouse embryonic fibroblast\b'],
    'Primary Neurons': [r'\bprimary neuron\b', r'\bcultured neuron\b'],
}

SAMPLE_PREPARATION = {
    'PFA Fixation': [r'\bpfa\b', r'\bparaformaldehyde\b'],
    'Glutaraldehyde': [r'\bglutaraldehyde\b'],
    'Methanol Fixation': [r'\bmethanol\s+fix'],
    'Cryosection': [r'\bcryosection\b', r'\bcryo.?section\b'],
    'Vibratome': [r'\bvibratome\b'],
    'Microtome': [r'\bmicrotome\b'],
    'Paraffin Embedding': [r'\bparaffin\s+embed'],
    'OCT Embedding': [r'\boct\s+embed', r'\boct\s+compound\b'],
    'Tissue Clearing': [r'\btissue\s+clearing\b'],
    'CLARITY': [r'\bclarity\b'],
    'iDISCO': [r'\bidisco\b'],
    'uDISCO': [r'\budisco\b'],
    'CUBIC': [r'\bcubic\b.*clear'],
    'Expansion': [r'\bexpansion\s+microscop'],
    'Immunostaining': [r'\bimmunostain'],
    'Immunofluorescence': [r'\bimmunofluorescence\b', r'\bif\s+staining\b'],
    'Immunohistochemistry': [r'\bimmunohistochemistry\b', r'\bihc\b'],
    'FISH': [r'\bfish\b.*hybridization', r'\bfluorescence in situ\b'],
    'smFISH': [r'\bsmfish\b', r'\bsingle.?molecule fish\b'],
    'Live Imaging': [r'\blive\s+imaging\b', r'\blive.?cell\s+imaging\b'],
    'Permeabilization': [r'\bpermeabiliz'],
    'Blocking': [r'\bblocking\s+buffer\b', r'\bblocking\s+solution\b'],
    'Antigen Retrieval': [r'\bantigen\s+retrieval\b'],
}

PROTOCOL_PATTERNS = {
    'protocols.io': r'(https?://(?:www\.)?protocols\.io/[\w/.-]+)',
    'Bio-protocol': r'(https?://(?:www\.)?bio-protocol\.org/[\w/.-]+)',
    'JoVE': r'(https?://(?:www\.)?jove\.com/[\w/.-]+)',
    'Nature Protocols': r'(https?://(?:www\.)?nature\.com/(?:nprot|articles/(?:nprot|s41596))[\w/.-]+)',
    'STAR Protocols': r'(https?://(?:www\.)?cell\.com/star-protocols/[\w/.-]+)',
}

REPOSITORY_PATTERNS = {
    'Zenodo': r'(https?://(?:www\.)?zenodo\.org/record[s]?/\d+)',
    'Figshare': r'(https?://(?:www\.)?figshare\.com/articles/[\w/.-]+)',
    'GitHub': r'(https?://(?:www\.)?github\.com/[\w-]+/[\w.-]+)',
    'Dryad': r'(https?://(?:www\.)?datadryad\.org/[\w/.-]+)',
    'OSF': r'(https?://osf\.io/[\w]+)',
    'EMPIAR': r'(https?://(?:www\.)?ebi\.ac\.uk/empiar/[\w/.-]+)',
    'BioStudies': r'(https?://(?:www\.)?ebi\.ac\.uk/biostudies/[\w/.-]+)',
    'IDR': r'(https?://idr\.openmicroscopy\.org/[\w/.-]+)',
}

RRID_PATTERNS = [
    (r'RRID:\s*(AB_\d+)', 'antibody'),
    (r'RRID:\s*(SCR_\d+)', 'software'),
    (r'RRID:\s*(CVCL_[\w]+)', 'cell_line'),
    (r'RRID:\s*(Addgene_\d+)', 'plasmid'),
    (r'RRID:\s*(IMSR_[\w:]+)', 'organism'),
    (r'RRID:\s*(ZFIN_[\w-]+)', 'organism'),
    (r'RRID:\s*(MGI_[\w]+)', 'organism'),
]

ANTIBODY_PATTERNS = [
    (r'(?:Abcam|abcam)[:\s#]*(\bab\d+)', 'Abcam'),
    (r'(?:Cell\s*Signaling|CST)[:\s#]*(\d{4,5})', 'Cell Signaling'),
    (r'(?:Santa\s*Cruz)[:\s#]*(sc-\d+)', 'Santa Cruz'),
    (r'(?:Sigma|Sigma-Aldrich)[:\s#]*([A-Z]\d{4})', 'Sigma'),
    (r'(?:BD\s*Biosciences|BD)[:\s#]*(\d{6})', 'BD Biosciences'),
    (r'(?:BioLegend)[:\s#]*(\d{6})', 'BioLegend'),
]


def extract_tags(text: str, patterns: Dict[str, List[str]]) -> List[str]:
    """Extract tags from text using patterns."""
    if not text:
        return []
    
    text_lower = text.lower()
    found = []
    
    for tag_name, tag_patterns in patterns.items():
        for pattern in tag_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.append(tag_name)
                break
    
    return found


def extract_urls(text: str, patterns: Dict[str, str]) -> List[Dict]:
    """Extract URLs matching patterns."""
    if not text:
        return []
    
    found = []
    seen = set()
    
    for name, pattern in patterns.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            url = match.group(1) if match.groups() else match.group(0)
            if url not in seen:
                seen.add(url)
                found.append({'name': name, 'url': url})
    
    return found


def extract_rrids(text: str) -> List[Dict]:
    """Extract RRIDs from text."""
    if not text:
        return []
    
    found = []
    seen = set()
    
    for pattern, rtype in RRID_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            rrid_id = f"RRID:{match.group(1)}"
            if rrid_id not in seen:
                seen.add(rrid_id)
                found.append({
                    'id': rrid_id,
                    'type': rtype,
                    'url': f'https://scicrunch.org/resolver/{rrid_id}'
                })
    
    return found


def extract_antibodies(text: str) -> List[Dict]:
    """Extract antibodies from text."""
    if not text:
        return []
    
    found = []
    seen = set()
    
    for pattern, source in ANTIBODY_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            ab_id = match.group(1)
            if ab_id not in seen:
                seen.add(ab_id)
                found.append({'id': ab_id, 'source': source})
    
    return found


def merge_lists(existing: List, new: List) -> List:
    """Merge two lists, removing duplicates."""
    if not existing:
        existing = []
    if not new:
        return existing
    
    # Handle list of dicts
    if new and isinstance(new[0], dict):
        existing_ids = set()
        for item in existing:
            if isinstance(item, dict):
                existing_ids.add(item.get('id', item.get('url', item.get('name', str(item)))))
            else:
                existing_ids.add(str(item))
        
        for item in new:
            item_id = item.get('id', item.get('url', item.get('name', str(item))))
            if item_id not in existing_ids:
                existing.append(item)
                existing_ids.add(item_id)
    else:
        # Handle list of strings
        existing_set = set(str(x).lower() for x in existing)
        for item in new:
            if str(item).lower() not in existing_set:
                existing.append(item)
                existing_set.add(str(item).lower())
    
    return existing


def clean_paper(paper: Dict) -> Dict:
    """Clean and re-tag a single paper."""
    
    # Build combined text for extraction
    text_parts = [
        str(paper.get('title', '') or ''),
        str(paper.get('abstract', '') or ''),
        str(paper.get('methods', '') or ''),
        str(paper.get('full_text', '') or ''),
    ]
    combined_text = ' '.join(text_parts)
    
    # Extract and merge tags
    paper['microscopy_techniques'] = merge_lists(
        paper.get('microscopy_techniques', []),
        extract_tags(combined_text, MICROSCOPY_TECHNIQUES)
    )
    
    paper['image_analysis_software'] = merge_lists(
        paper.get('image_analysis_software', []),
        extract_tags(combined_text, IMAGE_ANALYSIS_SOFTWARE)
    )
    
    paper['microscope_brands'] = merge_lists(
        paper.get('microscope_brands', []),
        extract_tags(combined_text, MICROSCOPE_BRANDS)
    )
    
    paper['fluorophores'] = merge_lists(
        paper.get('fluorophores', []),
        extract_tags(combined_text, FLUOROPHORES)
    )
    
    paper['organisms'] = merge_lists(
        paper.get('organisms', []),
        extract_tags(combined_text, ORGANISMS)
    )
    
    paper['cell_lines'] = merge_lists(
        paper.get('cell_lines', []),
        extract_tags(combined_text, CELL_LINES)
    )
    
    paper['sample_preparation'] = merge_lists(
        paper.get('sample_preparation', []),
        extract_tags(combined_text, SAMPLE_PREPARATION)
    )
    
    # Extract protocols and repositories
    paper['protocols'] = merge_lists(
        paper.get('protocols', []),
        extract_urls(combined_text, PROTOCOL_PATTERNS)
    )
    
    paper['repositories'] = merge_lists(
        paper.get('repositories', []),
        extract_urls(combined_text, REPOSITORY_PATTERNS)
    )
    
    # Extract RRIDs and antibodies
    paper['rrids'] = merge_lists(
        paper.get('rrids', []),
        extract_rrids(combined_text)
    )
    
    paper['antibodies'] = merge_lists(
        paper.get('antibodies', []),
        extract_antibodies(combined_text)
    )
    
    # Remove bad RORs (those not starting with 0)
    if paper.get('rors'):
        paper['rors'] = [
            r for r in paper['rors']
            if isinstance(r, dict) and str(r.get('id', '')).startswith('0')
        ]
    
    # Update techniques/tags fields for compatibility
    paper['techniques'] = paper['microscopy_techniques']
    paper['tags'] = paper['microscopy_techniques']
    
    # Update software field
    paper['software'] = list(set(
        (paper.get('image_analysis_software') or []) + 
        (paper.get('image_acquisition_software') or [])
    ))
    
    # Update flags
    paper['has_full_text'] = bool(paper.get('full_text') and len(str(paper.get('full_text', ''))) > 100)
    paper['has_protocols'] = bool(paper.get('protocols'))
    paper['has_github'] = bool(paper.get('github_url'))
    paper['has_data'] = bool(paper.get('repositories'))
    paper['has_rrids'] = bool(paper.get('rrids'))
    paper['has_rors'] = bool(paper.get('rors'))
    paper['has_fluorophores'] = bool(paper.get('fluorophores'))
    paper['has_cell_lines'] = bool(paper.get('cell_lines'))
    paper['has_sample_prep'] = bool(paper.get('sample_preparation'))
    paper['has_methods'] = bool(paper.get('methods') and len(str(paper.get('methods', ''))) > 100)
    
    return paper


def main():
    if len(sys.argv) < 2:
        print("Usage: python cleanup_and_retag.py <input.json> [output.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.json', '_cleaned.json')
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        papers = json.load(f)
    
    print(f"Processing {len(papers)} papers...")
    
    # Track statistics
    stats_before = {}
    stats_after = {}
    
    fields_to_track = [
        'microscopy_techniques', 'microscope_brands', 'image_analysis_software',
        'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
        'protocols', 'repositories', 'rrids', 'antibodies'
    ]
    
    for field in fields_to_track:
        stats_before[field] = sum(1 for p in papers if p.get(field))
    
    # Process each paper
    for i, paper in enumerate(papers):
        papers[i] = clean_paper(paper)
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(papers)} papers...")
    
    for field in fields_to_track:
        stats_after[field] = sum(1 for p in papers if p.get(field))
    
    # Print statistics
    print(f"\n=== TAG STATISTICS ===")
    print(f"{'Field':<25} {'Before':>8} {'After':>8} {'Added':>8}")
    print("-" * 55)
    for field in fields_to_track:
        before = stats_before[field]
        after = stats_after[field]
        added = after - before
        print(f"{field:<25} {before:>8} {after:>8} {added:>+8}")
    
    # Save output
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print("Done!")


if __name__ == '__main__':
    main()