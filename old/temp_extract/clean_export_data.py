#!/usr/bin/env python3
"""
MicroHub Data Cleaning Script
Properly categorizes: techniques, software, organisms, microscopes
Run this BEFORE importing to WordPress

Usage: python clean_export_data.py input.json output.json
"""

import json
import re
import sys
from pathlib import Path

# =============================================================================
# CATEGORY DEFINITIONS
# =============================================================================

# MICROSCOPY TECHNIQUES - actual imaging methods
TECHNIQUES = {
    # Fluorescence - Basic
    'confocal', 'laser scanning confocal', 'lscm',
    'spinning disk', 'spinning disk confocal', 'csu',
    'widefield', 'epifluorescence',
    'deconvolution',
    
    # Fluorescence - Advanced
    'two-photon', '2-photon', 'multiphoton', 'multi-photon',
    'three-photon', '3-photon',
    'light sheet', 'lightsheet', 'spim', 'lsfm', 'selective plane illumination',
    'lattice light sheet', 'lattice lightsheet',
    'diSPIM', 'iSPIM',
    'tirf', 'tirfm', 'total internal reflection',
    
    # Super-Resolution
    'sted', 'stimulated emission depletion',
    'palm', 'photoactivated localization', 'fpalm',
    'storm', 'stochastic optical reconstruction', 'dstorm',
    'sim', 'structured illumination', 'n-sim', 'nsim',
    'smlm', 'single molecule localization',
    'minflux',
    'resolft',
    'expansion microscopy', 'exm',
    'airyscan',
    'ism', 'image scanning microscopy',
    
    # Spectroscopy/Functional
    'flim', 'fluorescence lifetime',
    'fret', 'forster resonance', 'förster resonance',
    'frap', 'fluorescence recovery',
    'fcs', 'fluorescence correlation',
    'cars', 'coherent anti-stokes raman',
    'srs', 'stimulated raman',
    'raman', 'raman microscopy', 'raman spectroscopy',
    
    # Live/Functional Imaging
    'calcium imaging', 'calcium indicator', 'gcamp',
    'voltage imaging', 'voltage indicator',
    'optogenetics', 'optogenetic',
    'live cell', 'live-cell', 'time-lapse', 'timelapse',
    'in vivo', 'intravital', 'intravital microscopy',
    
    # Electron Microscopy
    'electron microscopy',
    'tem', 'transmission electron microscopy',
    'sem', 'scanning electron microscopy',
    'cryo-em', 'cryo em', 'cryoem', 'cryo-electron microscopy',
    'cryo-et', 'cryo electron tomography',
    'fib-sem', 'focused ion beam',
    'sbem', 'serial block face', 'sbf-sem',
    'array tomography',
    'correlative', 'clem', 'correlative light and electron',
    'immuno-em', 'immunoelectron',
    
    # Other Microscopy
    'afm', 'atomic force microscopy',
    'oct', 'optical coherence tomography',
    'photoacoustic', 'photoacoustic microscopy', 'pam',
    'holographic', 'holography', 'digital holographic', 'dhm',
    'phase contrast', 'dic', 'differential interference contrast',
    'polarization', 'polarized light',
    'darkfield', 'dark field',
    'brightfield', 'bright field',
    
    # High-Throughput
    'high-content', 'high content', 'hcs',
    'high-throughput', 'high throughput',
    'automated microscopy',
    'plate reader imaging',
    
    # Special
    'adaptive optics', 'ao',
    'label-free', 'label free',
    'second harmonic', 'shg',
    'third harmonic', 'thg',
    'autofluorescence',
    'bioluminescence',
    'chemiluminescence',
    
    # Flow/Cytometry
    'flow cytometry', 'facs',
    'mass cytometry', 'cytof',
    'imaging flow cytometry',
    'cyclic immunofluorescence', 'cycif',
    
    # Spatial Omics
    'spatial transcriptomics',
    'merfish', 'seqfish',
    'codex',
    'visium',
    '10x genomics',
}

# SOFTWARE/IMAGE ANALYSIS TOOLS
SOFTWARE = {
    # Open Source - General
    'imagej', 'fiji', 'imagej2',
    'cellprofiler',
    'qupath',
    'napari',
    'icy',
    'bioimage.io',
    
    # Deep Learning
    'cellpose',
    'stardist',
    'deepcell',
    'ilastik',
    'u-net', 'unet',
    'segment anything', 'sam',
    'omnipose',
    'mesmer',
    
    # Tracking/Analysis
    'trackmate',
    'imaris',
    'arivis',
    'huygens',
    'aivia',
    'amira',
    'neurolucida',
    'neuron',
    
    # Programming Languages (for image analysis)
    'python',
    'matlab',
    'r',
    'julia',
    
    # Specific Analysis
    'cellranger',
    'scanpy',
    'seurat',
    'squidpy',
    
    # Data Management
    'omero',
    'bioformats',
    'zarr',
    'n5',
    
    # Visualization
    'visual', 'visua', 'vaa3d',
    'neuroglancer',
    'bigdataviewer',
    'elastix',
    
    # Commercial Suites
    'zen', 'zen blue', 'zen black',
    'las x', 'las af',
    'nis-elements', 'nis elements',
    'cellsens',
    'metamorph',
    'volocity',
    'slidebook',
    'harmony',
    'columbus',
    'operetta',
}

# ORGANISMS/MODEL SYSTEMS
ORGANISMS = {
    # Mammals
    'mouse', 'mus musculus', 'murine',
    'rat', 'rattus',
    'human', 'homo sapiens',
    'primate', 'macaque', 'monkey',
    'pig', 'porcine', 'sus scrofa',
    'rabbit',
    'hamster',
    'guinea pig',
    
    # Model Organisms
    'zebrafish', 'danio rerio',
    'drosophila', 'fruit fly', 'd. melanogaster',
    'c. elegans', 'caenorhabditis elegans', 'nematode', 'worm',
    'xenopus', 'frog',
    
    # Microorganisms
    'yeast', 'saccharomyces', 's. cerevisiae', 's. pombe',
    'e. coli', 'escherichia coli', 'bacteria',
    'bacillus',
    
    # Plants
    'arabidopsis', 'plant',
    
    # Cell Systems
    'cell line', 'cell culture',
    'organoid', 'organoids',
    'spheroid', 'spheroids',
    'tissue', 'tissue section',
    'primary cells',
    'stem cells', 'ipsc', 'ips cells',
    'hela',
    'hek293', 'hek-293',
    'cho',
    'nih3t3', '3t3',
}

# MICROSCOPE MANUFACTURERS AND THEIR PRODUCTS
MICROSCOPE_BRANDS = {
    # Nikon
    'nikon': {
        'brand': 'Nikon',
        'models': ['ti', 'ti-e', 'ti2', 'ti2-e', 'a1', 'a1r', 'a1+', 'ax', 'axr', 
                   'n-sim', 'n-sim s', 'n-sim e', 'n-storm', 'nis', 'c2', 'c2+',
                   'eclipse', 'te2000', 'crest', 'w1', 'sri', 'apo tirf']
    },
    # Zeiss
    'zeiss': {
        'brand': 'Zeiss',
        'models': ['lsm', 'lsm 710', 'lsm 780', 'lsm 880', 'lsm 900', 'lsm 980',
                   'elyra', 'elyra 7', 'airyscan', 'airyscan 2',
                   'axio', 'axio observer', 'axio imager', 'axio scan',
                   'lightsheet z.1', 'lightsheet 7', 'lattice lightsheet',
                   'celldiscoverer', 'cell discoverer',
                   'axioscan', 'axiovert', 'primovert',
                   'gemini', 'crossbeam', 'libra', 'sigma']
    },
    # Leica
    'leica': {
        'brand': 'Leica',
        'models': ['sp5', 'sp8', 'stellaris', 'stellaris 5', 'stellaris 8',
                   'sted 3x', 'tau-sted', 'falcon',
                   'thunder', 'dmi8', 'dmi6000',
                   'tcs', 'confocal',
                   'em', 'em gp2', 'uc7', 'vt1200']
    },
    # Olympus (now Evident)
    'olympus': {
        'brand': 'Olympus',
        'models': ['fv', 'fv1000', 'fv3000', 'fluoview',
                   'ix83', 'ix73', 'ix81', 'ix71',
                   'bx', 'bx63', 'bx53',
                   'vs200', 'slideview',
                   'spinsr', 'ixplore',
                   'cellsens']
    },
    # Evident (formerly Olympus Life Science)
    'evident': {
        'brand': 'Evident',
        'models': ['ixplore', 'spinsr', 'fv4000']
    },
    # Bruker/Luxendo
    'bruker': {
        'brand': 'Bruker',
        'models': ['luxendo', 'muvispim', 'inspex', 'vutara', 'ultima']
    },
    # Andor
    'andor': {
        'brand': 'Andor',
        'models': ['dragonfly', 'revolution', 'ixon', 'zyla', 'sona',
                   'bc43', 'mosaic']
    },
    # GE Healthcare / Cytiva
    'ge': {
        'brand': 'GE Healthcare',
        'models': ['deltavision', 'omx', 'in cell', 'incell', 'amersham']
    },
    'cytiva': {
        'brand': 'Cytiva',
        'models': ['deltavision', 'omx']
    },
    # PerkinElmer
    'perkinelmer': {
        'brand': 'PerkinElmer',
        'models': ['opera', 'operetta', 'phenix', 'ultraview', 'vectra']
    },
    # Molecular Devices
    'molecular devices': {
        'brand': 'Molecular Devices',
        'models': ['imagexpress', 'metaxpress', 'spectramax']
    },
    # Thermo Fisher / FEI
    'thermo': {
        'brand': 'Thermo Fisher',
        'models': ['glacios', 'krios', 'titan', 'talos', 'aquilos',
                   'cellinsight', 'evos', 'high content']
    },
    'fei': {
        'brand': 'FEI/Thermo Fisher',
        'models': ['glacios', 'krios', 'titan', 'talos', 'tecnai', 'nova', 'helios']
    },
    # JEOL
    'jeol': {
        'brand': 'JEOL',
        'models': ['jem', 'jsm', 'cryo-arm']
    },
    # Hitachi
    'hitachi': {
        'brand': 'Hitachi',
        'models': ['su', 'su9000', 's-4800', 'regulus']
    },
    # 3i (Intelligent Imaging Innovations)
    '3i': {
        'brand': '3i',
        'models': ['marianas', 'vivo', 'slidebook']
    },
    # Yokogawa
    'yokogawa': {
        'brand': 'Yokogawa',
        'models': ['csu', 'csu-x1', 'csu-w1', 'cv8000', 'cq1']
    },
    # Visitech
    'visitech': {
        'brand': 'VisiTech',
        'models': ['vt-ispim', 'vt-infinity']
    },
    # Abberior
    'abberior': {
        'brand': 'Abberior',
        'models': ['sted', 'expert line', 'facility line']
    },
    # PicoQuant
    'picoquant': {
        'brand': 'PicoQuant',
        'models': ['microtime', 'luminosa', 'flim']
    },
    # Miltenyi
    'miltenyi': {
        'brand': 'Miltenyi',
        'models': ['macsquant', 'ultramicroscope']
    },
    # LaVision BioTec
    'lavision': {
        'brand': 'LaVision BioTec',
        'models': ['ultramicroscope', 'trim-scope']
    },
    # Photron
    'photron': {
        'brand': 'Photron',
        'models': ['fastcam', 'nova']
    },
}

# Keywords that indicate a Nikon system specifically
NIKON_INDICATORS = ['n-sim', 'nsim', 'ti-e', 'ti2-e', 'ti2', 'a1r', 'a1', 'nis-elements', 'n-storm']
ZEISS_INDICATORS = ['lsm', 'airyscan', 'elyra', 'zen', 'axio', 'celldiscoverer']
LEICA_INDICATORS = ['sp5', 'sp8', 'stellaris', 'falcon', 'thunder', 'las x']
OLYMPUS_INDICATORS = ['fv1000', 'fv3000', 'fluoview', 'ix83', 'ix73', 'cellsens']

# =============================================================================
# NORMALIZATION MAPPINGS
# =============================================================================

TECHNIQUE_NORMALIZATION = {
    'confocal microscopy': 'Confocal',
    'confocal': 'Confocal',
    'laser scanning confocal': 'Confocal',
    'lscm': 'Confocal',
    'spinning disk': 'Spinning Disk',
    'spinning disk confocal': 'Spinning Disk',
    'widefield': 'Widefield',
    'epifluorescence': 'Widefield',
    'two-photon': 'Two-Photon',
    '2-photon': 'Two-Photon',
    'multiphoton': 'Two-Photon',
    'light sheet': 'Light Sheet',
    'lightsheet': 'Light Sheet',
    'spim': 'Light Sheet',
    'lsfm': 'Light Sheet',
    'tirf': 'TIRF',
    'tirfm': 'TIRF',
    'sted': 'STED',
    'palm': 'PALM',
    'storm': 'STORM',
    'dstorm': 'STORM',
    'sim': 'SIM',
    'structured illumination': 'SIM',
    'n-sim': 'SIM',
    'smlm': 'Single Molecule Localization',
    'flim': 'FLIM',
    'fret': 'FRET',
    'frap': 'FRAP',
    'fcs': 'FCS',
    'cars': 'CARS',
    'srs': 'SRS',
    'raman': 'Raman',
    'calcium imaging': 'Calcium Imaging',
    'voltage imaging': 'Voltage Imaging',
    'optogenetics': 'Optogenetics',
    'live cell': 'Live Cell',
    'live-cell': 'Live Cell',
    'in vivo': 'In Vivo',
    'intravital': 'In Vivo',
    'tem': 'TEM',
    'transmission electron': 'TEM',
    'sem': 'SEM',
    'scanning electron': 'SEM',
    'cryo-em': 'Cryo-EM',
    'cryo em': 'Cryo-EM',
    'fib-sem': 'FIB-SEM',
    'correlative': 'Correlative',
    'clem': 'Correlative',
    'afm': 'AFM',
    'oct': 'OCT',
    'photoacoustic': 'Photoacoustic',
    'holographic': 'Holographic',
    'high-content': 'High-Content',
    'high content': 'High-Content',
    'adaptive optics': 'Adaptive Optics',
    'expansion microscopy': 'Expansion Microscopy',
    'airyscan': 'Airyscan',
}

SOFTWARE_NORMALIZATION = {
    'imagej': 'ImageJ',
    'fiji': 'Fiji',
    'cellprofiler': 'CellProfiler',
    'qupath': 'QuPath',
    'napari': 'napari',
    'cellpose': 'Cellpose',
    'stardist': 'StarDist',
    'deepcell': 'DeepCell',
    'ilastik': 'ilastik',
    'trackmate': 'TrackMate',
    'imaris': 'Imaris',
    'arivis': 'Arivis',
    'huygens': 'Huygens',
    'aivia': 'Aivia',
    'amira': 'Amira',
    'neurolucida': 'Neurolucida',
    'python': 'Python',
    'matlab': 'MATLAB',
    'r': 'R',
    'omero': 'OMERO',
    'zen': 'ZEN',
    'nis-elements': 'NIS-Elements',
    'las x': 'LAS X',
    'metamorph': 'MetaMorph',
    'volocity': 'Volocity',
    'slidebook': 'SlideBook',
}

ORGANISM_NORMALIZATION = {
    'mouse': 'Mouse',
    'mus musculus': 'Mouse',
    'murine': 'Mouse',
    'rat': 'Rat',
    'rattus': 'Rat',
    'human': 'Human',
    'homo sapiens': 'Human',
    'zebrafish': 'Zebrafish',
    'danio rerio': 'Zebrafish',
    'drosophila': 'Drosophila',
    'fruit fly': 'Drosophila',
    'c. elegans': 'C. elegans',
    'caenorhabditis elegans': 'C. elegans',
    'nematode': 'C. elegans',
    'xenopus': 'Xenopus',
    'frog': 'Xenopus',
    'yeast': 'Yeast',
    'saccharomyces': 'Yeast',
    'e. coli': 'E. coli',
    'escherichia coli': 'E. coli',
    'bacteria': 'Bacteria',
    'cell line': 'Cell Line',
    'cell culture': 'Cell Line',
    'organoid': 'Organoid',
    'tissue': 'Tissue',
    'primary cells': 'Primary Cells',
    'plant': 'Plant',
    'arabidopsis': 'Arabidopsis',
    'primate': 'Primate',
    'macaque': 'Primate',
}

# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================

def detect_techniques(text):
    """Extract microscopy techniques from text"""
    if not text:
        return []
    
    text_lower = text.lower()
    found = set()
    
    for technique in TECHNIQUES:
        # Use word boundaries for short terms
        if len(technique) <= 4:
            pattern = r'\b' + re.escape(technique) + r'\b'
            if re.search(pattern, text_lower):
                normalized = TECHNIQUE_NORMALIZATION.get(technique, technique.title())
                found.add(normalized)
        else:
            if technique in text_lower:
                normalized = TECHNIQUE_NORMALIZATION.get(technique, technique.title())
                found.add(normalized)
    
    return list(found)

def detect_software(text):
    """Extract software/image analysis tools from text"""
    if not text:
        return []
    
    text_lower = text.lower()
    found = set()
    
    for software in SOFTWARE:
        if len(software) <= 2:
            pattern = r'\b' + re.escape(software) + r'\b'
            if re.search(pattern, text_lower):
                normalized = SOFTWARE_NORMALIZATION.get(software, software.title())
                found.add(normalized)
        else:
            if software in text_lower:
                normalized = SOFTWARE_NORMALIZATION.get(software, software)
                found.add(normalized)
    
    return list(found)

def detect_organisms(text):
    """Extract organisms/model systems from text"""
    if not text:
        return []
    
    text_lower = text.lower()
    found = set()
    
    for organism in ORGANISMS:
        # Use word boundaries to avoid partial matches
        if len(organism) <= 3:
            pattern = r'\b' + re.escape(organism) + r'\b'
        else:
            pattern = r'\b' + re.escape(organism)
        
        if re.search(pattern, text_lower, re.IGNORECASE):
            normalized = ORGANISM_NORMALIZATION.get(organism.lower(), organism.title())
            found.add(normalized)
    
    return list(found)

def detect_microscope(text):
    """Extract microscope brand and model from text"""
    if not text:
        return {'brand': '', 'model': ''}
    
    text_lower = text.lower()
    
    # Check for brand indicators first
    brand = ''
    model = ''
    
    # Nikon detection
    for indicator in NIKON_INDICATORS:
        if indicator in text_lower:
            brand = 'Nikon'
            model = indicator.upper().replace('NSIM', 'N-SIM')
            break
    
    # Zeiss detection
    if not brand:
        for indicator in ZEISS_INDICATORS:
            if indicator in text_lower:
                brand = 'Zeiss'
                # Try to get specific model
                if 'lsm 980' in text_lower:
                    model = 'LSM 980'
                elif 'lsm 900' in text_lower:
                    model = 'LSM 900'
                elif 'lsm 880' in text_lower:
                    model = 'LSM 880'
                elif 'lsm 780' in text_lower:
                    model = 'LSM 780'
                elif 'lsm' in text_lower:
                    model = 'LSM'
                elif 'airyscan' in text_lower:
                    model = 'Airyscan'
                elif 'elyra' in text_lower:
                    model = 'Elyra'
                break
    
    # Leica detection
    if not brand:
        for indicator in LEICA_INDICATORS:
            if indicator in text_lower:
                brand = 'Leica'
                if 'stellaris' in text_lower:
                    model = 'Stellaris'
                elif 'sp8' in text_lower:
                    model = 'SP8'
                elif 'sp5' in text_lower:
                    model = 'SP5'
                break
    
    # Olympus detection
    if not brand:
        for indicator in OLYMPUS_INDICATORS:
            if indicator in text_lower:
                brand = 'Olympus'
                if 'fv3000' in text_lower:
                    model = 'FV3000'
                elif 'fv1000' in text_lower:
                    model = 'FV1000'
                break
    
    # Generic brand detection
    if not brand:
        for brand_key, brand_info in MICROSCOPE_BRANDS.items():
            if brand_key in text_lower:
                brand = brand_info['brand']
                # Try to find model
                for m in brand_info['models']:
                    if m.lower() in text_lower:
                        model = m.upper() if len(m) <= 4 else m.title()
                        break
                break
    
    return {'brand': brand, 'model': model}

# =============================================================================
# MAIN CLEANING FUNCTION
# =============================================================================

def clean_paper(paper):
    """Clean and properly categorize a single paper's tags"""
    
    # Combine all text for detection
    full_text = ' '.join([
        paper.get('title', ''),
        paper.get('abstract', ''),
        ' '.join(paper.get('tags', [])),
        ' '.join(paper.get('techniques', [])),
        ' '.join(paper.get('software', [])),
        ' '.join(paper.get('organisms', [])),
    ])
    
    # Detect all categories
    techniques = detect_techniques(full_text)
    software = detect_software(full_text)
    organisms = detect_organisms(full_text)
    microscope = detect_microscope(full_text)
    
    # Also check existing microscope field
    if paper.get('microscope'):
        existing_micro = paper['microscope']
        if isinstance(existing_micro, dict):
            micro_text = f"{existing_micro.get('brand', '')} {existing_micro.get('model', '')}"
            detected = detect_microscope(micro_text)
            if detected['brand'] and not microscope['brand']:
                microscope = detected
    
    # Update paper with clean data
    paper['techniques'] = list(set(techniques))
    paper['software'] = list(set(software))
    paper['organisms'] = list(set(organisms))
    paper['microscope'] = microscope
    
    # Clean up old tags field - keep only techniques
    paper['tags'] = paper['techniques']
    
    return paper

def clean_export(input_file, output_file):
    """Clean entire export file"""
    print(f"Reading {input_file}...")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} papers")
    print("Cleaning data...")
    
    # Statistics
    stats = {
        'techniques': set(),
        'software': set(),
        'organisms': set(),
        'microscope_brands': set(),
        'papers_with_techniques': 0,
        'papers_with_software': 0,
        'papers_with_organisms': 0,
        'papers_with_microscopes': 0,
    }
    
    cleaned_data = []
    for i, paper in enumerate(data):
        if i % 100 == 0:
            print(f"  Processing {i}/{len(data)}...")
        
        cleaned = clean_paper(paper)
        cleaned_data.append(cleaned)
        
        # Update stats
        for t in cleaned.get('techniques', []):
            stats['techniques'].add(t)
        for s in cleaned.get('software', []):
            stats['software'].add(s)
        for o in cleaned.get('organisms', []):
            stats['organisms'].add(o)
        if cleaned.get('microscope', {}).get('brand'):
            stats['microscope_brands'].add(cleaned['microscope']['brand'])
        
        if cleaned.get('techniques'):
            stats['papers_with_techniques'] += 1
        if cleaned.get('software'):
            stats['papers_with_software'] += 1
        if cleaned.get('organisms'):
            stats['papers_with_organisms'] += 1
        if cleaned.get('microscope', {}).get('brand'):
            stats['papers_with_microscopes'] += 1
    
    # Write output
    print(f"\nWriting cleaned data to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(cleaned_data, f, indent=2)
    
    # Print statistics
    print("\n" + "="*60)
    print("CLEANING COMPLETE")
    print("="*60)
    print(f"\nTotal papers: {len(cleaned_data)}")
    print(f"\nTechniques found ({len(stats['techniques'])}):")
    for t in sorted(stats['techniques']):
        print(f"  - {t}")
    
    print(f"\nSoftware found ({len(stats['software'])}):")
    for s in sorted(stats['software']):
        print(f"  - {s}")
    
    print(f"\nOrganisms found ({len(stats['organisms'])}):")
    for o in sorted(stats['organisms']):
        print(f"  - {o}")
    
    print(f"\nMicroscope brands found ({len(stats['microscope_brands'])}):")
    for b in sorted(stats['microscope_brands']):
        print(f"  - {b}")
    
    print(f"\nPapers with techniques: {stats['papers_with_techniques']}")
    print(f"Papers with software: {stats['papers_with_software']}")
    print(f"Papers with organisms: {stats['papers_with_organisms']}")
    print(f"Papers with microscopes: {stats['papers_with_microscopes']}")
    
    return cleaned_data

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python clean_export_data.py input.json output.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    clean_export(input_file, output_file)
