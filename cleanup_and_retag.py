#!/usr/bin/env python3
"""
MicroHub Paper Cleanup and Re-tagging Script v3.2
Cleans up JSON data, extracts missing tags, and normalizes tag variants.

CHANGES in v3.2:
- GITHUB TOOLS: Properly preserves and validates github_tools data from scraper v5.1+
  Each paper can have a list of detailed GitHub repo references with metrics
  (stars, forks, health_score, language, license, topics, relationship type)
- github_url is auto-populated from github_tools if missing (prefers 'introduces' relationship)
- has_github_tools boolean flag added for filtering
- github_tools are deduplicated by full_name and validated for required fields
- Stats tracking now includes github_tools count

CHANGES in v3.1:
- INSTITUTION EXTRACTION FIX: Now ONLY extracts from author affiliations field
  NOT from abstract/methods/full_text (which caused false positives from citations)
- ROR ID LOOKUP: Added database of ~70 major institutions with their ROR IDs
  ROR IDs are looked up from institution names (not found in paper text)
- Old facility data is NOT merged - always uses freshly extracted institutions
- This should fix issues like "Stanford paper showing MIT"

CHANGES in v3:
- Tags are still extracted from full text (title + abstract + methods + full_text)
- full_text field is REMOVED from output to save database space
- Website will display abstract with tag highlighting instead
- has_full_text is always False
- INSTITUTIONS: Now extracts research institutions where authors are from
  (universities, research institutes, hospitals) instead of imaging facilities
- Supports multiple institutions per paper (for collaborations)
- Stores in 'institutions' field (with 'facilities' kept for backward compatibility)

FIXES from v2:
- Removed simple 'prior' -> 'Prior' mapping that caused over-tagging
- Made Prior Scientific patterns more specific to avoid matching "prior to"
- Similar fixes for other ambiguous terms

IMPORTANT: For institution extraction to work, the scraper must populate
the 'affiliations' or 'author_affiliations' field with author affiliation data.
"""

import json
import re
import sys
from typing import List, Dict, Set, Optional

# ============================================================================
# CANONICAL MAPPINGS - Normalize variants to standard forms
# ============================================================================

FLUOROPHORE_CANONICAL = {
    # GFP variants -> canonical
    'gfp': 'GFP',
    'green fluorescent protein': 'GFP',
    'egfp': 'EGFP',
    'enhanced gfp': 'EGFP',
    'enhanced green fluorescent protein': 'EGFP',
    'eGFP': 'EGFP',
    'e-gfp': 'EGFP',
    
    # YFP variants
    'yfp': 'YFP',
    'yellow fluorescent protein': 'YFP',
    'eyfp': 'EYFP',
    'enhanced yfp': 'EYFP',
    'enhanced yellow fluorescent protein': 'EYFP',
    
    # RFP variants
    'rfp': 'RFP',
    'red fluorescent protein': 'RFP',
    'dsred': 'DsRed',
    'ds-red': 'DsRed',
    
    # CFP variants
    'cfp': 'CFP',
    'cyan fluorescent protein': 'CFP',
    'ecfp': 'ECFP',
    'enhanced cfp': 'ECFP',
    
    # BFP variants
    'bfp': 'BFP',
    'blue fluorescent protein': 'BFP',
    'ebfp': 'EBFP',
    
    # Alexa Fluor - normalize all to "Alexa Fluor XXX" format
    'alexa 350': 'Alexa Fluor 350',
    'alexa fluor 350': 'Alexa Fluor 350',
    'af350': 'Alexa Fluor 350',
    'alexa 405': 'Alexa Fluor 405',
    'alexa fluor 405': 'Alexa Fluor 405',
    'af405': 'Alexa Fluor 405',
    'alexa 430': 'Alexa Fluor 430',
    'alexa fluor 430': 'Alexa Fluor 430',
    'af430': 'Alexa Fluor 430',
    'alexa 488': 'Alexa Fluor 488',
    'alexa fluor 488': 'Alexa Fluor 488',
    'af488': 'Alexa Fluor 488',
    'alexa 514': 'Alexa Fluor 514',
    'alexa fluor 514': 'Alexa Fluor 514',
    'af514': 'Alexa Fluor 514',
    'alexa 532': 'Alexa Fluor 532',
    'alexa fluor 532': 'Alexa Fluor 532',
    'af532': 'Alexa Fluor 532',
    'alexa 546': 'Alexa Fluor 546',
    'alexa fluor 546': 'Alexa Fluor 546',
    'af546': 'Alexa Fluor 546',
    'alexa 555': 'Alexa Fluor 555',
    'alexa fluor 555': 'Alexa Fluor 555',
    'af555': 'Alexa Fluor 555',
    'alexa 568': 'Alexa Fluor 568',
    'alexa fluor 568': 'Alexa Fluor 568',
    'af568': 'Alexa Fluor 568',
    'alexa 594': 'Alexa Fluor 594',
    'alexa fluor 594': 'Alexa Fluor 594',
    'af594': 'Alexa Fluor 594',
    'alexa 610': 'Alexa Fluor 610',
    'alexa fluor 610': 'Alexa Fluor 610',
    'af610': 'Alexa Fluor 610',
    'alexa 633': 'Alexa Fluor 633',
    'alexa fluor 633': 'Alexa Fluor 633',
    'af633': 'Alexa Fluor 633',
    'alexa 647': 'Alexa Fluor 647',
    'alexa fluor 647': 'Alexa Fluor 647',
    'af647': 'Alexa Fluor 647',
    'alexa 660': 'Alexa Fluor 660',
    'alexa fluor 660': 'Alexa Fluor 660',
    'af660': 'Alexa Fluor 660',
    'alexa 680': 'Alexa Fluor 680',
    'alexa fluor 680': 'Alexa Fluor 680',
    'af680': 'Alexa Fluor 680',
    'alexa 700': 'Alexa Fluor 700',
    'alexa fluor 700': 'Alexa Fluor 700',
    'af700': 'Alexa Fluor 700',
    'alexa 750': 'Alexa Fluor 750',
    'alexa fluor 750': 'Alexa Fluor 750',
    'af750': 'Alexa Fluor 750',
    'alexa 790': 'Alexa Fluor 790',
    'alexa fluor 790': 'Alexa Fluor 790',
    'af790': 'Alexa Fluor 790',
    
    # ATTO dyes
    'atto 488': 'ATTO 488',
    'atto488': 'ATTO 488',
    'atto 565': 'ATTO 565',
    'atto565': 'ATTO 565',
    'atto 647': 'ATTO 647',
    'atto647': 'ATTO 647',
    'atto 647n': 'ATTO 647N',
    'atto647n': 'ATTO 647N',
    'atto 655': 'ATTO 655',
    'atto655': 'ATTO 655',
    
    # Cy dyes
    'cy3': 'Cy3',
    'cyanine 3': 'Cy3',
    'cyanine3': 'Cy3',
    'cy5': 'Cy5',
    'cyanine 5': 'Cy5',
    'cyanine5': 'Cy5',
    'cy7': 'Cy7',
    'cyanine 7': 'Cy7',
    
    # Hoechst variants
    'hoechst': 'Hoechst 33342',
    'hoechst 33342': 'Hoechst 33342',
    'hoechst 33258': 'Hoechst 33258',
    
    # mEos variants
    'meos': 'mEos',
    'meos2': 'mEos2',
    'meos3': 'mEos3',
    'meos3.2': 'mEos3.2',
    'meos 3.2': 'mEos3.2',
    
    # Other common ones
    'dapi': 'DAPI',
    'fitc': 'FITC',
    'tritc': 'TRITC',
    'texas red': 'Texas Red',
    'texasred': 'Texas Red',
    'propidium iodide': 'Propidium Iodide',
    'pi': 'Propidium Iodide',
    'mitotracker': 'MitoTracker',
    'mitotracker red': 'MitoTracker Red',
    'mitotracker green': 'MitoTracker Green',
    'lysotracker': 'LysoTracker',
    'lysotracker red': 'LysoTracker Red',
    'er-tracker': 'ER-Tracker',
    'ertracker': 'ER-Tracker',
    'phalloidin': 'Phalloidin',
    'rhodamine': 'Rhodamine',
    'rhodamine b': 'Rhodamine B',
    'rhodamine 123': 'Rhodamine 123',
    'bodipy': 'BODIPY',
    'calcein': 'Calcein',
    'calcein am': 'Calcein-AM',
    'fluo-4': 'Fluo-4',
    'fluo4': 'Fluo-4',
    'fura-2': 'Fura-2',
    'fura2': 'Fura-2',
    'gcamp': 'GCaMP',
    'gcamp6': 'GCaMP6',
    'gcamp6f': 'GCaMP6f',
    'gcamp6s': 'GCaMP6s',
    'mcherry': 'mCherry',
    'tdtomato': 'tdTomato',
    'td-tomato': 'tdTomato',
    'mscarlet': 'mScarlet',
    'mneongreen': 'mNeonGreen',
    'memerald': 'mEmerald',
    'mturquoise': 'mTurquoise',
    'mturquoise2': 'mTurquoise2',
    'mcerulean': 'mCerulean',
    'mvenus': 'mVenus',
    'pa-gfp': 'PA-GFP',
    'pagfp': 'PA-GFP',
    'dendra': 'Dendra2',
    'dendra2': 'Dendra2',
    'dio': 'DiO',
    'dii': 'DiI',
    'did': 'DiD',
    'dir': 'DiR',
    'wga': 'WGA',
    'wheat germ agglutinin': 'WGA',
    'sytox': 'SYTOX',
    'sytox green': 'SYTOX Green',
    'draq5': 'DRAQ5',
    'jc-1': 'JC-1',
    'jc1': 'JC-1',
    'sir': 'SiR',
    'sir-actin': 'SiR-Actin',
    'sir-tubulin': 'SiR-Tubulin',
    'janelia fluor 549': 'JF549',
    'jf549': 'JF549',
    'janelia fluor 646': 'JF646',
    'jf646': 'JF646',
    'cf568': 'CF568',
    'cf dye': 'CF Dye',
    'dylight': 'DyLight',
    'edu': 'EdU',
    'brdu': 'BrdU',
    'click-it': 'Click-iT',
    'cellmask': 'CellMask',
    'fm dyes': 'FM Dyes',
    'fm 1-43': 'FM 1-43',
    'fm 4-64': 'FM 4-64',
    'acridine orange': 'Acridine Orange',
    'coumarin': 'Coumarin',
    'pe': 'PE',
    'apc': 'APC',
    'tagrfp': 'TagRFP',
    'mrfp': 'mRFP',
    'citrine': 'Citrine',
    'venus': 'Venus',
    'neongeen': 'NeonGreen',
    'neongreen': 'NeonGreen',
    'dronpa': 'Dronpa',
    'mgfp': 'mGFP',
    'syto': 'SYTO',
}

MICROSCOPE_BRAND_CANONICAL = {
    # Olympus/Evident merger
    'olympus': 'Olympus',
    'evident': 'Evident (Olympus)',
    'evident olympus': 'Evident (Olympus)',
    'evident (olympus)': 'Evident (Olympus)',
    
    # 3i variants
    '3i': '3i (Intelligent Imaging)',
    'intelligent imaging innovations': '3i (Intelligent Imaging)',
    '3i intelligent imaging': '3i (Intelligent Imaging)',
    '3i (intelligent imaging)': '3i (Intelligent Imaging)',
    
    # Standard brands
    'zeiss': 'Zeiss',
    'carl zeiss': 'Zeiss',
    'leica': 'Leica',
    'leica microsystems': 'Leica',
    'nikon': 'Nikon',
    'thermo fisher': 'Thermo Fisher',
    'thermofisher': 'Thermo Fisher',
    'fei': 'Thermo Fisher',
    'fei company': 'Thermo Fisher',
    'jeol': 'JEOL',
    'bruker': 'Bruker',
    'andor': 'Andor',
    'hamamatsu': 'Hamamatsu',
    'perkinelmer': 'PerkinElmer',
    'perkin elmer': 'PerkinElmer',
    'molecular devices': 'Molecular Devices',
    'yokogawa': 'Yokogawa',
    'visitech': 'Visitech',
    'abberior': 'Abberior',
    'picoquant': 'PicoQuant',
    'thorlabs': 'Thorlabs',
    'photron': 'Photron',
    'luxendo': 'Luxendo',
    'lavision': 'LaVision BioTec',
    'lavision biotec': 'LaVision BioTec',
    'photometrics': 'Photometrics',
    'pco': 'PCO',
    'coherent': 'Coherent',
    'spectra-physics': 'Spectra-Physics',
    'spectra physics': 'Spectra-Physics',
    'newport': 'Newport',
    'sutter': 'Sutter',
    'edmund optics': 'Edmund Optics',
    'roper': 'Roper',
    'till photonics': 'Till Photonics',
    'becker & hickl': 'Becker & Hickl',
    'becker hickl': 'Becker & Hickl',
    'princeton instruments': 'Princeton Instruments',
    'qimaging': 'QImaging',
    # FIXED: Removed simple 'prior' mapping - was causing "prior to" to be tagged
    # Now only specific company name variants are mapped
    'prior scientific': 'Prior Scientific',
    'prior stage': 'Prior Scientific',
    'prior proscan': 'Prior Scientific',
    'applied scientific instrumentation': 'ASI',
    'asi': 'ASI',
    'semrock': 'Semrock',
    'chroma': 'Chroma',
    'miltenyi': 'Miltenyi',
}

SOFTWARE_CANONICAL = {
    # Fiji/ImageJ
    'fiji': 'Fiji',
    'imagej': 'ImageJ',
    'image j': 'ImageJ',
    'imagej2': 'ImageJ',
    
    # Python ecosystem
    'python': 'Python',
    'scikit-image': 'scikit-image',
    'skimage': 'scikit-image',
    'scipy': 'SciPy',
    'numpy': 'NumPy',
    'napari': 'napari',
    'cellpose': 'Cellpose',
    'stardist': 'StarDist',
    'deepcell': 'DeepCell',
    
    # Commercial
    'imaris': 'Imaris',
    'arivis': 'Arivis',
    'halo': 'HALO',
    'qupath': 'QuPath',
    'volocity': 'Volocity',
    'metamorph': 'MetaMorph',
    'nis-elements': 'NIS-Elements',
    'nis elements': 'NIS-Elements',
    'zen': 'ZEN',
    'zen blue': 'ZEN',
    'zen black': 'ZEN',
    'las x': 'LAS X',
    'lasx': 'LAS X',
    'leica las x': 'LAS X',
    'amira': 'Amira',
    'dragonfly': 'Dragonfly',
    'huygens': 'Huygens',
    'svi huygens': 'Huygens',
    'autoquant': 'AutoQuant',
    'cellsens': 'CellSens',
    'fluoview': 'FluoView',
    'harmony': 'Harmony',
    'columbus': 'Columbus',
    
    # Open source / academic
    'cellprofiler': 'CellProfiler',
    'icy': 'Icy',
    'ilastik': 'ilastik',
    'omero': 'OMERO',
    'bio-formats': 'Bio-Formats',
    'bioformats': 'Bio-Formats',
    'trackmate': 'TrackMate',
    'micromanager': 'MicroManager',
    'micro-manager': 'MicroManager',
    
    # Deep learning
    'u-net': 'U-Net',
    'unet': 'U-Net',
    'mask r-cnn': 'Mask R-CNN',
    'mask rcnn': 'Mask R-CNN',
    'yolov': 'YOLOv',
    'yolo': 'YOLOv',
    'segment-anything': 'SAM',
    'sam': 'SAM',
    
    # EM software
    'relion': 'RELION',
    'cryosparc': 'cryoSPARC',
    'eman2': 'EMAN2',
    'eman': 'EMAN2',
    'imod': 'IMOD',
    'serialem': 'SerialEM',
    'chimera': 'UCSF Chimera',
    'ucsf chimera': 'UCSF Chimera',
    'chimerax': 'ChimeraX',
    'pymol': 'PyMOL',
    'digital micrograph': 'Digital Micrograph',
    'gatan': 'Digital Micrograph',
    
    # Analysis
    'matlab': 'MATLAB',
    'r': 'R',
    'r statistical': 'R',
    'inform': 'inForm',
    'vaa3d': 'Vaa3D',
    'neurolucida': 'Neurolucida',
    'thunderstorm': 'ThunderSTORM',
    'deconvolutionlab': 'DeconvolutionLab',
    'bigdataviewer': 'BigDataViewer',
    'scipion': 'Scipion',
}

TECHNIQUE_CANONICAL = {
    # SMLM variants
    'smlm': 'SMLM',
    'single molecule localization': 'SMLM',
    'palm': 'PALM',
    'photoactivated localization': 'PALM',
    'storm': 'STORM',
    'stochastic optical reconstruction': 'STORM',
    'dstorm': 'dSTORM',
    'd-storm': 'dSTORM',
    'direct storm': 'dSTORM',
    
    # SIM variants
    'sim': 'SIM',
    'structured illumination': 'SIM',
    
    # STED variants
    'sted': 'STED',
    'stimulated emission depletion': 'STED',
    'resolft': 'RESOLFT',
    'minflux': 'MINFLUX',
    
    # Light sheet variants
    'light sheet': 'Light Sheet',
    'light-sheet': 'Light Sheet',
    'lsfm': 'Light Sheet',
    'spim': 'Light Sheet',
    'selective plane illumination': 'Light Sheet',
    'lattice light sheet': 'Lattice Light Sheet',
    'lattice light-sheet': 'Lattice Light Sheet',
    'mesospim': 'MesoSPIM',
    
    # Confocal variants
    'confocal': 'Confocal',
    'clsm': 'Confocal',
    'lscm': 'Confocal',
    'spinning disk': 'Spinning Disk',
    'spinning disc': 'Spinning Disk',
    'airyscan': 'Airyscan',
    
    # Multiphoton
    'two-photon': 'Two-Photon',
    'two photon': 'Two-Photon',
    '2-photon': 'Two-Photon',
    '2p': 'Two-Photon',
    'multiphoton': 'Multiphoton',
    'multi-photon': 'Multiphoton',
    'three-photon': 'Three-Photon',
    'three photon': 'Three-Photon',
    '3-photon': 'Three-Photon',
    
    # TIRF
    'tirf': 'TIRF',
    'tirfm': 'TIRF',
    'total internal reflection': 'TIRF',
    
    # EM techniques
    'sem': 'SEM',
    'scanning electron': 'SEM',
    'tem': 'TEM',
    'transmission electron': 'TEM',
    'cryo-em': 'Cryo-EM',
    'cryoem': 'Cryo-EM',
    'cryo em': 'Cryo-EM',
    'cryo-electron microscopy': 'Cryo-EM',
    'cryo-et': 'Cryo-ET',
    'cryoet': 'Cryo-ET',
    'cryo electron tomography': 'Cryo-ET',
    'fib-sem': 'FIB-SEM',
    'fibsem': 'FIB-SEM',
    'focused ion beam': 'FIB-SEM',
    'serial block-face': 'Serial Block-Face SEM',
    'sbfsem': 'Serial Block-Face SEM',
    'sbf-sem': 'Serial Block-Face SEM',
    'volume em': 'Volume EM',
    'array tomography': 'Array Tomography',
    'immuno-em': 'Immuno-EM',
    'immunoem': 'Immuno-EM',
    'negative stain': 'Negative Stain EM',
    
    # Other microscopy
    'afm': 'AFM',
    'atomic force': 'AFM',
    'phase contrast': 'Phase Contrast',
    'dic': 'DIC',
    'differential interference contrast': 'DIC',
    'brightfield': 'Brightfield',
    'bright field': 'Brightfield',
    'bright-field': 'Brightfield',
    'darkfield': 'Darkfield',
    'dark field': 'Darkfield',
    'dark-field': 'Darkfield',
    'widefield': 'Widefield',
    'wide field': 'Widefield',
    'wide-field': 'Widefield',
    'epifluorescence': 'Epifluorescence',
    'epi-fluorescence': 'Epifluorescence',
    
    # Functional imaging
    'frap': 'FRAP',
    'fluorescence recovery': 'FRAP',
    'flip': 'FLIP',
    'fluorescence loss': 'FLIP',
    'fret': 'FRET',
    'forster resonance': 'FRET',
    'förster resonance': 'FRET',
    'fluorescence resonance energy transfer': 'FRET',
    'flim': 'FLIM',
    'fluorescence lifetime': 'FLIM',
    'fcs': 'FCS',
    'fluorescence correlation spectroscopy': 'FCS',
    'fccs': 'FCCS',
    
    # Special techniques
    'super-resolution': 'Super-Resolution',
    'super resolution': 'Super-Resolution',
    'nanoscopy': 'Super-Resolution',
    'expansion microscopy': 'Expansion Microscopy',
    'exm': 'Expansion Microscopy',
    'clem': 'CLEM',
    'correlative light electron': 'CLEM',
    'intravital': 'Intravital',
    'live cell imaging': 'Live Cell Imaging',
    'live-cell imaging': 'Live Cell Imaging',
    'time-lapse': 'Live Cell Imaging',
    'timelapse': 'Live Cell Imaging',
    'calcium imaging': 'Calcium Imaging',
    'voltage imaging': 'Voltage Imaging',
    'optogenetics': 'Optogenetics',
    
    # Other
    'deconvolution': 'Deconvolution',
    'z-stack': 'Z-Stack',
    'zstack': 'Z-Stack',
    'z stack': 'Z-Stack',
    '3d imaging': '3D Imaging',
    'three-dimensional imaging': '3D Imaging',
    '4d imaging': '4D Imaging',
    'optical sectioning': 'Optical Sectioning',
    'single molecule': 'Single Molecule',
    'single-molecule': 'Single Molecule',
    'single particle': 'Single Particle',
    'single-particle': 'Single Particle',
    'high-content screening': 'High-Content Screening',
    'high content screening': 'High-Content Screening',
    'hcs': 'High-Content Screening',
    'immunofluorescence': 'Immunofluorescence',
    'raman': 'Raman',
    'cars': 'CARS',
    'coherent anti-stokes': 'CARS',
    'srs': 'SRS',
    'stimulated raman': 'SRS',
    'shg': 'SHG',
    'second harmonic': 'SHG',
    'second harmonic generation': 'SHG',
    'oct': 'OCT',
    'optical coherence tomography': 'OCT',
    'holographic': 'Holographic',
    'holography': 'Holographic',
    'photoacoustic': 'Photoacoustic',
    'electron tomography': 'Electron Tomography',
    'sofi': 'SOFI',
    'dna-paint': 'DNA-PAINT',
    'dna paint': 'DNA-PAINT',
    'polarization': 'Polarization',
}

ORGANISM_CANONICAL = {
    'mouse': 'Mouse',
    'mice': 'Mouse',
    'murine': 'Mouse',
    'mus musculus': 'Mouse',
    'human': 'Human',
    'patient': 'Human',
    'homo sapiens': 'Human',
    'rat': 'Rat',
    'rattus': 'Rat',
    'rattus norvegicus': 'Rat',
    'zebrafish': 'Zebrafish',
    'danio rerio': 'Zebrafish',
    'drosophila': 'Drosophila',
    'fruit fly': 'Drosophila',
    'd. melanogaster': 'Drosophila',
    'drosophila melanogaster': 'Drosophila',
    'c. elegans': 'C. elegans',
    'caenorhabditis elegans': 'C. elegans',
    'caenorhabditis': 'C. elegans',
    'xenopus': 'Xenopus',
    'xenopus laevis': 'Xenopus',
    'chicken': 'Chicken',
    'chick': 'Chicken',
    'gallus': 'Chicken',
    'gallus gallus': 'Chicken',
    'pig': 'Pig',
    'porcine': 'Pig',
    'sus scrofa': 'Pig',
    'monkey': 'Monkey',
    'macaque': 'Monkey',
    'primate': 'Monkey',
    'rabbit': 'Rabbit',
    'oryctolagus': 'Rabbit',
    'dog': 'Dog',
    'canine': 'Dog',
    'yeast': 'Yeast',
    'saccharomyces': 'Yeast',
    's. cerevisiae': 'Yeast',
    'saccharomyces cerevisiae': 'Yeast',
    's. pombe': 'Yeast',
    'e. coli': 'E. coli',
    'escherichia coli': 'E. coli',
    'escherichia': 'E. coli',
    'bacteria': 'Bacteria',
    'bacterial': 'Bacteria',
    'arabidopsis': 'Arabidopsis',
    'arabidopsis thaliana': 'Arabidopsis',
    'plant': 'Plant',
    'plant cell': 'Plant',
    'plant tissue': 'Plant',
    'tobacco': 'Tobacco',
    'nicotiana': 'Tobacco',
    'maize': 'Maize',
    'zea mays': 'Maize',
    'corn': 'Maize',
    'organoid': 'Organoid',
    'spheroid': 'Spheroid',
}

CELL_LINE_CANONICAL = {
    'hela': 'HeLa',
    'hek293': 'HEK293',
    'hek 293': 'HEK293',
    'hek-293': 'HEK293',
    'hek293t': 'HEK293T',
    'hek 293t': 'HEK293T',
    '293t': 'HEK293T',
    'u2os': 'U2OS',
    'u-2 os': 'U2OS',
    'u2-os': 'U2OS',
    'cos-7': 'COS-7',
    'cos7': 'COS-7',
    'cho': 'CHO',
    'cho cell': 'CHO',
    'nih 3t3': 'NIH 3T3',
    'nih3t3': 'NIH 3T3',
    '3t3': 'NIH 3T3',
    'mcf7': 'MCF7',
    'mcf-7': 'MCF7',
    'a549': 'A549',
    'mdck': 'MDCK',
    'vero': 'Vero',
    'pc12': 'PC12',
    'pc-12': 'PC12',
    'sh-sy5y': 'SH-SY5Y',
    'shsy5y': 'SH-SY5Y',
    'ipsc': 'iPSC',
    'induced pluripotent': 'iPSC',
    'esc': 'ESC',
    'embryonic stem': 'ESC',
    'mef': 'MEF',
    'mouse embryonic fibroblast': 'MEF',
    'primary neuron': 'Primary Neurons',
    'cultured neuron': 'Primary Neurons',
    'primary neurons': 'Primary Neurons',
    'primary cardiomyocytes': 'Primary Cardiomyocytes',
    'primary hepatocytes': 'Primary Hepatocytes',
}

SAMPLE_PREP_CANONICAL = {
    'fixation': 'Fixation',
    'pfa': 'PFA Fixation',
    'pfa fixation': 'PFA Fixation',
    'paraformaldehyde': 'PFA Fixation',
    '4% pfa': 'PFA Fixation',
    'glutaraldehyde': 'Glutaraldehyde',
    'methanol fixation': 'Methanol Fixation',
    'methanol fix': 'Methanol Fixation',
    'cryosection': 'Cryosectioning',
    'cryosectioning': 'Cryosectioning',
    'cryo-section': 'Cryosectioning',
    'vibratome': 'Vibratome',
    'microtome': 'Microtome',
    'ultramicrotome': 'Ultramicrotome',
    'paraffin embedding': 'Paraffin Embedding',
    'paraffin embed': 'Paraffin Embedding',
    'oct embedding': 'OCT Embedding',
    'oct compound': 'OCT Embedding',
    'tissue clearing': 'Tissue Clearing',
    'clarity': 'CLARITY',
    'idisco': 'iDISCO',
    'udisco': 'uDISCO',
    '3disco': '3DISCO',
    'cubic': 'CUBIC',
    'shield': 'SHIELD',
    'expansion': 'Expansion Microscopy',
    'expansion microscopy': 'Expansion Microscopy',
    'immunostaining': 'Immunostaining',
    'immunostain': 'Immunostaining',
    'immunofluorescence': 'Immunofluorescence',
    'if staining': 'Immunofluorescence',
    'immunohistochemistry': 'Immunohistochemistry',
    'ihc': 'Immunohistochemistry',
    'fish': 'FISH',
    'fluorescence in situ': 'FISH',
    'smfish': 'smFISH',
    'single-molecule fish': 'smFISH',
    'rnascope': 'RNAscope',
    'live imaging': 'Live Imaging',
    'live-cell imaging': 'Live Imaging',
    'live cell imaging': 'Live Imaging',
    'permeabilization': 'Permeabilization',
    'permeabiliz': 'Permeabilization',
    'blocking': 'Blocking',
    'blocking buffer': 'Blocking',
    'blocking solution': 'Blocking',
    'antigen retrieval': 'Antigen Retrieval',
    'cell culture': 'Cell Culture',
    'transfection': 'Transfection',
    'lipofection': 'Lipofection',
    'electroporation': 'Electroporation',
    'transduction': 'Transduction',
    'lentiviral': 'Lentiviral',
    'adenoviral': 'Adenoviral',
    'aav': 'AAV',
    'knockdown': 'Knockdown',
    'knockout': 'Knockout',
    'crispr': 'CRISPR',
    'monolayer': 'Monolayer',
    'co-culture': 'Co-culture',
    'coculture': 'Co-culture',
    'primary culture': 'Primary Culture',
    '3d culture': '3D Culture',
    'spheroid': 'Spheroid',
    'organoid': 'Organoid',
    'whole mount': 'Whole Mount',
    'flat mount': 'Flat Mount',
    'h&e': 'H&E',
    'hematoxylin': 'H&E',
    'tunel': 'TUNEL',
    'in situ hybridization': 'In Situ Hybridization',
}


# ============================================================================
# TAG DICTIONARIES - Comprehensive patterns for extraction
# ============================================================================

MICROSCOPY_TECHNIQUES = {
    'Confocal': [r'\bconfocal\b', r'\bclsm\b', r'\blscm\b'],
    'Two-Photon': [r'\btwo.?photon\b', r'\b2.?photon\b', r'\b2p\s+microscop'],
    'Three-Photon': [r'\bthree.?photon\b', r'\b3.?photon\b'],
    'Multiphoton': [r'\bmultiphoton\b', r'\bmulti.?photon\b'],
    'STED': [r'\bsted\b', r'stimulated emission depletion'],
    'PALM': [r'\bpalm\b(?!.*tree)', r'photoactivated localization'],
    'STORM': [r'\bstorm\b(?!.*weather)', r'stochastic optical reconstruction'],
    'dSTORM': [r'\bdstorm\b', r'\bd.?storm\b', r'direct\s+storm'],
    'SIM': [r'\bsim\b(?!ulation)', r'structured illumination'],
    'Light Sheet': [r'\blight.?sheet\b', r'\blsfm\b', r'\bspim\b', r'selective plane illumination'],
    'Lattice Light Sheet': [r'lattice\s+light.?sheet'],
    'MesoSPIM': [r'\bmesospim\b'],
    'Spinning Disk': [r'\bspinning\s*dis[ck]\b'],
    'Airyscan': [r'\bairyscan\b'],
    'TIRF': [r'\btirf\b', r'\btirfm\b', r'total internal reflection'],
    'FRAP': [r'\bfrap\b', r'fluorescence recovery after photobleaching'],
    'FLIP': [r'\bflip\b(?!ped)', r'fluorescence loss in photobleaching'],
    'FRET': [r'\bfret\b', r'förster resonance', r'forster resonance', r'fluorescence resonance energy transfer'],
    'FLIM': [r'\bflim\b', r'fluorescence lifetime'],
    'FCS': [r'\bfcs\b', r'fluorescence correlation spectroscopy'],
    'FCCS': [r'\bfccs\b', r'fluorescence cross.?correlation'],
    'Super-Resolution': [r'\bsuper.?resolution\b', r'\bnanoscopy\b'],
    'Expansion Microscopy': [r'\bexpansion\s+microscopy\b', r'\bexm\b'],
    'Cryo-EM': [r'\bcryo.?em\b', r'\bcryo.?electron\s+microscop'],
    'Cryo-ET': [r'\bcryo.?et\b', r'cryo.?electron tomography'],
    'SEM': [r'\bsem\b(?!antic)', r'scanning electron microscop'],
    'TEM': [r'\btem\b(?!p)', r'transmission electron microscop'],
    'FIB-SEM': [r'\bfib.?sem\b', r'focused ion beam'],
    'Serial Block-Face SEM': [r'serial block.?face', r'\bsbf.?sem\b'],
    'Volume EM': [r'\bvolume\s+em\b', r'\bvem\b'],
    'AFM': [r'\bafm\b', r'atomic force microscop'],
    'Phase Contrast': [r'\bphase\s*contrast\b'],
    'DIC': [r'\bdic\b(?!tion)', r'differential interference contrast'],
    'Brightfield': [r'\bbright.?field\b'],
    'Darkfield': [r'\bdark.?field\b'],
    'Fluorescence Microscopy': [r'\bfluorescence\s+microscop', r'\bfluorescent\s+microscop'],
    'Widefield': [r'\bwide.?field\b'],
    'Epifluorescence': [r'\bepi.?fluorescence\b'],
    'Deconvolution': [r'\bdeconvolution\b'],
    'Live Cell Imaging': [r'\blive.?cell\s+imag', r'\btime.?lapse\b', r'\btimelapse\b'],
    'Intravital': [r'\bintravital\b'],
    'Single Molecule': [r'\bsingle.?molecule\b'],
    'SMLM': [r'\bsmlm\b', r'single.?molecule localization'],
    'High-Content Screening': [r'\bhigh.?content\b', r'\bhcs\b'],
    'Z-Stack': [r'\bz.?stack\b'],
    '3D Imaging': [r'\b3d\s+imag', r'\bthree.?dimensional\s+imag'],
    '4D Imaging': [r'\b4d\s+imag', r'\bfour.?dimensional\s+imag'],
    'Optical Sectioning': [r'\boptical\s+sectioning\b'],
    'Raman': [r'\braman\s+microscop', r'\braman\s+spectroscop', r'\braman\s+imag'],
    'CARS': [r'\bcars\b(?!$)', r'coherent anti.?stokes'],
    'SRS': [r'\bsrs\b', r'stimulated raman'],
    'SHG': [r'\bshg\b', r'second harmonic generation'],
    'Second Harmonic': [r'second harmonic(?!\s+generation)'],
    'OCT': [r'\boct\b(?!ober)', r'optical coherence tomography'],
    'Holographic': [r'\bholograph'],
    'Photoacoustic': [r'\bphotoacoustic\b'],
    'Electron Tomography': [r'\belectron\s+tomograph'],
    'Single Particle': [r'\bsingle.?particle\b'],
    'Immunofluorescence': [r'\bimmunofluorescence\b'],
    'CLEM': [r'\bclem\b', r'correlative light.{1,20}electron'],
    'Immuno-EM': [r'\bimmuno.?em\b', r'immuno.?electron'],
    'Negative Stain EM': [r'negative stain'],
    'Array Tomography': [r'\barray tomography\b'],
    'MINFLUX': [r'\bminflux\b'],
    'RESOLFT': [r'\bresolft\b'],
    'SOFI': [r'\bsofi\b', r'super.?resolution optical fluctuation'],
    'DNA-PAINT': [r'\bdna.?paint\b'],
    'Polarization': [r'\bpolarization\s+microscop'],
    'Calcium Imaging': [r'\bcalcium\s+imag'],
    'Voltage Imaging': [r'\bvoltage\s+imag'],
    'Optogenetics': [r'\boptogenetic'],
}

IMAGE_ANALYSIS_SOFTWARE = {
    'Fiji': [r'\bfiji\b'],
    'ImageJ': [r'\bimagej\b', r'\bimage\s*j\b'],
    'CellProfiler': [r'\bcellprofiler\b'],
    'Imaris': [r'\bimaris\b'],
    'Arivis': [r'\barivis\b'],
    'HALO': [r'\bhalo\b.*(?:patholog|ai|software)', r'\bhalo\s+ai\b'],
    'QuPath': [r'\bqupath\b'],
    'Icy': [r'\bicy\b.*(?:software|platform|plugin)', r'\bicy\s+platform\b'],
    'ilastik': [r'\bilastik\b'],
    'napari': [r'\bnapari\b'],
    'ZEN': [r'\bzen\b.*(?:software|blue|black|zeiss)', r'\bzen\s+(?:blue|black)\b'],
    'NIS-Elements': [r'\bnis.?elements\b'],
    'LAS X': [r'\blas\s*x\b', r'\bleica\s+las'],
    'MetaMorph': [r'\bmetamorph\b'],
    'Volocity': [r'\bvolocity\b'],
    'Huygens': [r'\bhuygens\b'],
    'Amira': [r'\bamira\b.*(?:software|3d|visual)'],
    'Dragonfly': [r'\bdragonfly\b.*(?:software|ors)'],
    'OMERO': [r'\bomero\b'],
    'Bio-Formats': [r'\bbio.?formats\b'],
    'Cellpose': [r'\bcellpose\b'],
    'StarDist': [r'\bstardist\b'],
    'DeepCell': [r'\bdeepcell\b'],
    'Python': [r'\bpython\b'],
    'MATLAB': [r'\bmatlab\b'],
    'R': [r'\br\s+(?:software|package|statistical|programming)', r'\br\s+\(', r'using\s+r\b', r'\br\s+version'],
    'scikit-image': [r'\bscikit.?image\b', r'\bskimage\b'],
    'U-Net': [r'\bu.?net\b'],
    'RELION': [r'\brelion\b'],
    'cryoSPARC': [r'\bcryosparc\b'],
    'EMAN2': [r'\beman2?\b'],
    'IMOD': [r'\bimod\b'],
    'SerialEM': [r'\bserialem\b'],
    'UCSF Chimera': [r'\bchimera\b.*ucsf', r'\bucsf\s+chimera\b', r'\bchimera\b(?!x)'],
    'ChimeraX': [r'\bchimerax\b'],
    'PyMOL': [r'\bpymol\b'],
    'Mask R-CNN': [r'\bmask\s*r.?cnn\b'],
    'YOLOv': [r'\byolov?\d*\b', r'\byolo\b'],
    'SAM': [r'\bsegment.?anything\b', r'\bsam\b.*(?:model|segment)'],
    'ThunderSTORM': [r'\bthunderstorm\b'],
    'Vaa3D': [r'\bvaa3d\b'],
    'Neurolucida': [r'\bneurolucida\b'],
    'TrackMate': [r'\btrackmate\b'],
    'MicroManager': [r'\bmicro.?manager\b'],
    'inForm': [r'\binform\b.*(?:software|analysis|akoya)'],
    'Digital Micrograph': [r'\bdigital\s*micrograph\b', r'\bgatan\b.*software'],
    'CellSens': [r'\bcellsens\b'],
    'FluoView': [r'\bfluoview\b'],
    'Harmony': [r'\bharmony\b.*(?:software|perkin)'],
    'Columbus': [r'\bcolumbus\b.*(?:software|perkin)'],
    'AutoQuant': [r'\bautoquant\b'],
    'DeconvolutionLab': [r'\bdeconvolutionlab\b'],
    'BigDataViewer': [r'\bbigdataviewer\b'],
    'Scipion': [r'\bscipion\b'],
    'SlideBook': [r'\bslidebook\b'],
    'Aivia': [r'\baivia\b'],
    'Dragonfly': [r'\bdragonfly\b'],
}

MICROSCOPE_BRANDS = {
    'Zeiss': [r'\bzeiss\b', r'\bcarl zeiss\b'],
    'Leica': [r'\bleica\b'],
    'Nikon': [r'\bnikon\b'],
    'Olympus': [r'\bolympus\b'],
    'Evident (Olympus)': [r'\bevident\b.*(?:microscop|olympus)'],
    'Thermo Fisher': [r'\bthermo\s*fisher\b', r'\bfei\s+(?:company|tecnai|talos|titan|helios|quanta|verios|scios)'],
    'JEOL': [r'\bjeol\b'],
    'Bruker': [r'\bbruker\b'],
    'Andor': [r'\bandor\b'],
    'Hamamatsu': [r'\bhamamatsu\b'],
    'PerkinElmer': [r'\bperkin\s*elmer\b'],
    'Molecular Devices': [r'\bmolecular\s+devices\b'],
    'Yokogawa': [r'\byokogawa\b'],
    '3i (Intelligent Imaging)': [r'\b3i\b.*(?:imaging|marianas|slidebook)', r'intelligent imaging innovations'],
    'Visitech': [r'\bvisitech\b'],
    'Abberior': [r'\babberior\b'],
    'PicoQuant': [r'\bpicoquant\b'],
    'Thorlabs': [r'\bthorlabs\b'],
    'Photron': [r'\bphotron\b'],
    'Luxendo': [r'\bluxendo\b'],
    'LaVision BioTec': [r'\blavision\b'],
    'Photometrics': [r'\bphotometrics\b'],
    'PCO': [r'\bpco\b.*(?:camera|edge|panda)'],
    'Coherent': [r'\bcoherent\b.*(?:laser|chameleon)'],
    'Spectra-Physics': [r'\bspectra.?physics\b'],
    'Newport': [r'\bnewport\b.*(?:optic|stage)'],
    'Sutter': [r'\bsutter\b.*(?:instrument|micropipette)'],
    'ASI': [r'\basi\b.*(?:stage|imaging)', r'applied scientific instrumentation'],
    'Semrock': [r'\bsemrock\b'],
    'Chroma': [r'\bchroma\b.*(?:filter|technology)'],
    'Miltenyi': [r'\bmiltenyi\b'],
    'Edmund Optics': [r'\bedmund\s+optics\b'],
    'Roper': [r'\broper\b.*(?:scientific|camera)'],
    'Till Photonics': [r'\btill photonics\b'],
    'Becker & Hickl': [r'\bbecker\s*(?:&|and)?\s*hickl\b'],
    'Princeton Instruments': [r'\bprinceton instruments\b'],
    'QImaging': [r'\bqimaging\b'],
    # FIXED: Prior Scientific - more specific patterns to avoid matching "prior to"
    # Only match when followed by company-specific terms
    'Prior Scientific': [
        r'\bprior\s+scientific\b',
        r'\bprior\s+proscan\b',
        r'\bprior\s+nanodrive\b',
        r'\bprior\s+optiscan\b',
        r'\bprior\s+(?:motorized\s+)?stage\b',
        r'\bprior\s+(?:focus|controller)\b',
        r'\bprior\s+instruments?\b',
    ],
}

FLUOROPHORES = {
    'GFP': [r'\bgfp\b(?!.*enhanced)', r'\bgreen fluorescent protein\b(?!.*enhanced)'],
    'EGFP': [r'\begfp\b', r'\beGFP\b', r'\benhanced\s+(?:green\s+)?(?:fluorescent\s+)?(?:protein\s+)?gfp\b', r'\benhanced green fluorescent protein\b'],
    'mNeonGreen': [r'\bmneongreen\b', r'\bm-?neongreen\b'],
    'mClover': [r'\bmclover\d*\b'],
    'mEmerald': [r'\bmemerald\b'],
    'YFP': [r'\byfp\b(?!.*enhanced)', r'\byellow fluorescent protein\b'],
    'EYFP': [r'\beyfp\b', r'\benhanced\s+yfp\b'],
    'mVenus': [r'\bmvenus\b'],
    'Venus': [r'\bvenus\b(?!.*planet)'],
    'Citrine': [r'\bcitrine\b'],
    'RFP': [r'\brfp\b', r'\bred fluorescent protein\b'],
    'mCherry': [r'\bmcherry\b'],
    'tdTomato': [r'\btd.?tomato\b'],
    'mScarlet': [r'\bmscarlet\b'],
    'mKate2': [r'\bmkate2?\b'],
    'DsRed': [r'\bds.?red\b'],
    'TagRFP': [r'\btagrfp\b'],
    'mRFP': [r'\bmrfp\b'],
    'CFP': [r'\bcfp\b', r'\bcyan fluorescent protein\b'],
    'ECFP': [r'\becfp\b'],
    'mCerulean': [r'\bmcerulean\d*\b'],
    'mTurquoise': [r'\bmturquoise\d*\b'],
    'BFP': [r'\bbfp\b', r'\bblue fluorescent protein\b'],
    'EBFP': [r'\bebfp\b'],
    'mTagBFP': [r'\bmtagbfp\b'],
    'Alexa Fluor 350': [r'\balexa\s*(?:fluor)?\s*350\b', r'\baf350\b'],
    'Alexa Fluor 405': [r'\balexa\s*(?:fluor)?\s*405\b', r'\baf405\b'],
    'Alexa Fluor 430': [r'\balexa\s*(?:fluor)?\s*430\b', r'\baf430\b'],
    'Alexa Fluor 488': [r'\balexa\s*(?:fluor)?\s*488\b', r'\baf488\b'],
    'Alexa Fluor 514': [r'\balexa\s*(?:fluor)?\s*514\b', r'\baf514\b'],
    'Alexa Fluor 532': [r'\balexa\s*(?:fluor)?\s*532\b', r'\baf532\b'],
    'Alexa Fluor 546': [r'\balexa\s*(?:fluor)?\s*546\b', r'\baf546\b'],
    'Alexa Fluor 555': [r'\balexa\s*(?:fluor)?\s*555\b', r'\baf555\b'],
    'Alexa Fluor 568': [r'\balexa\s*(?:fluor)?\s*568\b', r'\baf568\b'],
    'Alexa Fluor 594': [r'\balexa\s*(?:fluor)?\s*594\b', r'\baf594\b'],
    'Alexa Fluor 610': [r'\balexa\s*(?:fluor)?\s*610\b', r'\baf610\b'],
    'Alexa Fluor 633': [r'\balexa\s*(?:fluor)?\s*633\b', r'\baf633\b'],
    'Alexa Fluor 647': [r'\balexa\s*(?:fluor)?\s*647\b', r'\baf647\b'],
    'Alexa Fluor 660': [r'\balexa\s*(?:fluor)?\s*660\b', r'\baf660\b'],
    'Alexa Fluor 680': [r'\balexa\s*(?:fluor)?\s*680\b', r'\baf680\b'],
    'Alexa Fluor 700': [r'\balexa\s*(?:fluor)?\s*700\b', r'\baf700\b'],
    'Alexa Fluor 750': [r'\balexa\s*(?:fluor)?\s*750\b', r'\baf750\b'],
    'Alexa Fluor 790': [r'\balexa\s*(?:fluor)?\s*790\b', r'\baf790\b'],
    'Cy3': [r'\bcy3\b', r'\bcyanine\s*3\b'],
    'Cy5': [r'\bcy5\b', r'\bcyanine\s*5\b'],
    'Cy7': [r'\bcy7\b', r'\bcyanine\s*7\b'],
    'DAPI': [r'\bdapi\b'],
    'Hoechst 33342': [r'\bhoechst\s*33342\b', r'\bhoechst\b(?!\s*33258)'],
    'Hoechst 33258': [r'\bhoechst\s*33258\b'],
    'DRAQ5': [r'\bdraq5\b'],
    'SYTOX': [r'\bsytox\b'],
    'SYTOX Green': [r'\bsytox\s+green\b'],
    'SYTO': [r'\bsyto\b'],
    'Propidium Iodide': [r'\bpropidium\s+iodide\b', r'\bpi\s+stain'],
    'MitoTracker': [r'\bmitotracker\b(?!\s+(?:red|green))'],
    'MitoTracker Red': [r'\bmitotracker\s+red\b'],
    'MitoTracker Green': [r'\bmitotracker\s+green\b'],
    'LysoTracker': [r'\blysotracker\b(?!\s+red)'],
    'LysoTracker Red': [r'\blysotracker\s+red\b'],
    'ER-Tracker': [r'\ber.?tracker\b'],
    'Phalloidin': [r'\bphalloidin\b'],
    'WGA': [r'\bwga\b', r'\bwheat germ agglutinin\b'],
    'BODIPY': [r'\bbodipy\b'],
    'DiI': [r'\bdii\b(?!d)'],
    'DiO': [r'\bdio\b(?!d)'],
    'DiD': [r'\bdid\b'],
    'DiR': [r'\bdir\b'],
    'Fluo-4': [r'\bfluo.?4\b'],
    'Fura-2': [r'\bfura.?2\b'],
    'GCaMP': [r'\bgcamp\b(?!\d)'],
    'GCaMP6': [r'\bgcamp6\b'],
    'GCaMP6f': [r'\bgcamp6f\b'],
    'GCaMP6s': [r'\bgcamp6s\b'],
    'jRGECO': [r'\bjrgeco\b'],
    'Calcein': [r'\bcalcein\b(?!\s*am)'],
    'Calcein-AM': [r'\bcalcein.?am\b'],
    'FITC': [r'\bfitc\b'],
    'TRITC': [r'\btritc\b'],
    'Texas Red': [r'\btexas\s+red\b'],
    'Rhodamine': [r'\brhodamine\b(?!\s+(?:b|123))'],
    'Rhodamine B': [r'\brhodamine\s*b\b'],
    'Rhodamine 123': [r'\brhodamine\s*123\b'],
    'ATTO 488': [r'\batto\s*488\b'],
    'ATTO 565': [r'\batto\s*565\b'],
    'ATTO 647': [r'\batto\s*647\b(?!n)'],
    'ATTO 647N': [r'\batto\s*647\s*n\b'],
    'ATTO 655': [r'\batto\s*655\b'],
    'mEos': [r'\bmeos\b(?!\d)'],
    'mEos2': [r'\bmeos2\b'],
    'mEos3': [r'\bmeos3\b'],
    'mEos3.2': [r'\bmeos\s*3\.2\b'],
    'Dendra2': [r'\bdendra2?\b'],
    'mMaple': [r'\bmmaple\d*\b'],
    'PA-GFP': [r'\bpa.?gfp\b'],
    'Dronpa': [r'\bdronpa\b'],
    'SiR': [r'\bsir\b(?!.*tubulin|.*actin)', r'\bsilicon rhodamine\b'],
    'SiR-Actin': [r'\bsir.?actin\b'],
    'SiR-Tubulin': [r'\bsir.?tubulin\b'],
    'JF549': [r'\bjf\s*549\b', r'\bjanelia\s+fluor\s*549\b'],
    'JF646': [r'\bjf\s*646\b', r'\bjanelia\s+fluor\s*646\b'],
    'CF568': [r'\bcf\s*568\b'],
    'CF Dye': [r'\bcf\s+dye\b'],
    'DyLight': [r'\bdylight\b'],
    'EdU': [r'\bedu\b'],
    'BrdU': [r'\bbrdu\b'],
    'Click-iT': [r'\bclick.?it\b'],
    'CellMask': [r'\bcellmask\b'],
    'FM Dyes': [r'\bfm\s+dye\b', r'\bfm\s*(?:1-43|4-64)\b'],
    'Acridine Orange': [r'\bacridine\s+orange\b'],
    'Coumarin': [r'\bcoumarin\b'],
    'PE': [r'\bpe\b(?!.*phycoerythrin)', r'\bphycoerythrin\b'],
    'APC': [r'\bapc\b(?!.*allophycocyanin)', r'\ballophycocyanin\b'],
    'JC-1': [r'\bjc.?1\b'],
    'NeonGreen': [r'\bneongreen\b'],
    'mGFP': [r'\bmgfp\b'],
}

ORGANISMS = {
    'Mouse': [r'\bmouse\b', r'\bmice\b', r'\bmurine\b', r'\bmus\s*musculus\b'],
    'Human': [r'\bhuman\b', r'\bpatient\b', r'\bhomo\s*sapiens\b'],
    'Rat': [r'\brat\b', r'\brattus\b'],
    'Zebrafish': [r'\bzebrafish\b', r'\bdanio\s*rerio\b'],
    'Drosophila': [r'\bdrosophila\b', r'\bfruit\s*fly\b', r'\bd\.\s*melanogaster\b'],
    'C. elegans': [r'\bc\.\s*elegans\b', r'\bcaenorhabditis\b'],
    'Xenopus': [r'\bxenopus\b'],
    'Chicken': [r'\bchicken\b', r'\bchick\s+embryo\b', r'\bgallus\b'],
    'Pig': [r'\bpig\b(?!ment)', r'\bporcine\b', r'\bsus\s*scrofa\b'],
    'Monkey': [r'\bmonkey\b', r'\bmacaque\b', r'\bprimate\b(?!.*non)'],
    'Rabbit': [r'\brabbit\b', r'\boryctolagus\b'],
    'Dog': [r'\bdog\b', r'\bcanine\b'],
    'Yeast': [r'\byeast\b', r'\bsaccharomyces\b', r'\bs\.\s*cerevisiae\b', r'\bs\.\s*pombe\b'],
    'E. coli': [r'\be\.\s*coli\b', r'\bescherichia\b'],
    'Bacteria': [r'\bbacteria\b', r'\bbacterial\b'],
    'Arabidopsis': [r'\barabidopsis\b'],
    'Plant': [r'\bplant\s+cell\b', r'\bplant\s+tissue\b'],
    'Tobacco': [r'\btobacco\b', r'\bnicotiana\b'],
    'Maize': [r'\bmaize\b', r'\bzea\s+mays\b', r'\bcorn\b'],
    'Organoid': [r'\borganoid\b'],
    'Spheroid': [r'\bspheroid\b'],
}

CELL_LINES = {
    'HeLa': [r'\bhela\b'],
    'HEK293': [r'\bhek\s*293\b(?!t)', r'\bhek293\b(?!t)'],
    'HEK293T': [r'\bhek\s*293\s*t\b', r'\b293t\b'],
    'U2OS': [r'\bu2\s*os\b', r'\bu-?2\s*os\b'],
    'COS-7': [r'\bcos.?7\b'],
    'CHO': [r'\bcho\s+cell\b', r'\bcho\s+line\b'],
    'NIH 3T3': [r'\bnih\s*3t3\b', r'\b3t3\s+cell\b'],
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
    'Primary Cardiomyocytes': [r'\bprimary cardiomyocyte\b'],
    'Primary Hepatocytes': [r'\bprimary hepatocyte\b'],
}

SAMPLE_PREPARATION = {
    'Fixation': [r'\bfixation\b', r'\bfixed\s+(?:cell|tissue|sample)'],
    'PFA Fixation': [r'\bpfa\b', r'\bparaformaldehyde\b', r'\b4%\s+pfa\b'],
    'Glutaraldehyde': [r'\bglutaraldehyde\b'],
    'Methanol Fixation': [r'\bmethanol\s+fix'],
    'Cryosectioning': [r'\bcryosection\b', r'\bcryo.?section\b'],
    'Vibratome': [r'\bvibratome\b'],
    'Microtome': [r'\bmicrotome\b'],
    'Ultramicrotome': [r'\bultramicrotome\b'],
    'Paraffin Embedding': [r'\bparaffin\s+embed'],
    'OCT Embedding': [r'\boct\s+embed', r'\boct\s+compound\b'],
    'Tissue Clearing': [r'\btissue\s+clearing\b'],
    'CLARITY': [r'\bclarity\b'],
    'iDISCO': [r'\bidisco\b'],
    'uDISCO': [r'\budisco\b'],
    '3DISCO': [r'\b3disco\b'],
    'CUBIC': [r'\bcubic\b.*clear'],
    'SHIELD': [r'\bshield\b.*(?:tissue|clearing)'],
    'Expansion Microscopy': [r'\bexpansion\s+microscop'],
    'Immunostaining': [r'\bimmunostain'],
    'Immunofluorescence': [r'\bimmunofluorescence\b', r'\bif\s+staining\b'],
    'Immunohistochemistry': [r'\bimmunohistochemistry\b', r'\bihc\b'],
    'FISH': [r'\bfish\b.*hybridization', r'\bfluorescence in situ\b'],
    'smFISH': [r'\bsmfish\b', r'\bsingle.?molecule fish\b'],
    'RNAscope': [r'\brnascope\b'],
    'Live Imaging': [r'\blive\s+imaging\b', r'\blive.?cell\s+imaging\b'],
    'Permeabilization': [r'\bpermeabiliz'],
    'Blocking': [r'\bblocking\s+(?:buffer|solution)\b'],
    'Antigen Retrieval': [r'\bantigen\s+retrieval\b'],
    'Cell Culture': [r'\bcell\s+culture\b'],
    'Transfection': [r'\btransfection\b'],
    'Lipofection': [r'\blipofection\b', r'\blipofectamine\b'],
    'Electroporation': [r'\belectroporation\b'],
    'Transduction': [r'\btransduction\b'],
    'Lentiviral': [r'\blentivir'],
    'Adenoviral': [r'\badenovir'],
    'AAV': [r'\baav\b', r'\badeno.?associated\s+virus\b'],
    'Knockdown': [r'\bknockdown\b', r'\bsirna\b', r'\bshrna\b'],
    'Knockout': [r'\bknockout\b'],
    'CRISPR': [r'\bcrispr\b'],
    'Monolayer': [r'\bmonolayer\b'],
    'Co-culture': [r'\bco.?culture\b'],
    'Primary Culture': [r'\bprimary\s+culture\b'],
    '3D Culture': [r'\b3d\s+culture\b'],
    'Spheroid': [r'\bspheroid\b'],
    'Organoid': [r'\borganoid\b'],
    'Whole Mount': [r'\bwhole\s*mount\b'],
    'Flat Mount': [r'\bflat\s*mount\b'],
    'H&E': [r'\bh\s*&\s*e\b', r'\bhematoxylin\s+(?:and\s+)?eosin\b'],
    'TUNEL': [r'\btunel\b'],
    'In Situ Hybridization': [r'\bin\s+situ\s+hybridization\b'],
}

PROTOCOL_PATTERNS = {
    'protocols.io': r'(https?://(?:www\.)?protocols\.io/[\w/.-]+)',
    'Bio-protocol': r'(https?://(?:www\.)?bio-protocol\.org/[\w/.-]+)',
    'JoVE': r'(https?://(?:www\.)?jove\.com/[\w/.-]+)',
    'Nature Protocols': r'(https?://(?:www\.)?nature\.com/(?:nprot|articles/(?:nprot|s41596))[\w/.-]+)',
    'STAR Protocols': r'(https?://(?:www\.)?cell\.com/star-protocols/[\w/.-]+)',
    'Current Protocols': r'(https?://(?:www\.)?currentprotocols\.com/[\w/.-]+)',
    'Cold Spring Harbor Protocols': r'(https?://(?:www\.)?cshprotocols\.cshlp\.org/[\w/.-]+)',
    'Methods in Molecular Biology': r'(https?://(?:www\.)?link\.springer\.com/protocol/[\w/.-]+)',
}

# Journal patterns for identifying protocol papers
PROTOCOL_JOURNALS = [
    r'\bnature\s+protocols?\b',
    r'\bnat\.?\s*protoc',
    r'\bjove\b',
    r'\bjournal\s+of\s+visualized\s+experiments\b',
    r'\bj\.\s*vis\.\s*exp\b',
    r'\bstar\s+protocols?\b',
    r'\bbio.?protocol\b',
    r'\bcurrent\s+protocols?\b',
    r'\bcurr\.?\s*protoc',
    r'\bcurrent\s+protocols?\s+in\s+\w+',
    r'\bmethods\s+in\s+molecular\s+biology\b',
    r'\bmethods\s+mol\.?\s*biol\b',
    r'\bmmb\b.*springer',
    r'\bspringer\s+protocols?\b',
    r'\bmethods\s+in\s+enzymology\b',
    r'\bmeth\.?\s*enzymol',
    r'\bcold\s+spring\s+harbor\s+protocols?\b',
    r'\bcsh\s+protocols?\b',
    r'\bcshprotocols\b',
    r'\bprotocol\s+exchange\b',
    r'\bmethodsx\b',
    r'\bmethods\s*x\b',
    r'\banalytical\s+biochemistry\b.*method',
    r'\bjournal\s+of\s+biological\s+methods\b',
    r'\bj\.\s*biol\.\s*methods\b',
    r'\bbiotechniques\b',
    r'^methods$',
    r'\bmethods\s*\(\s*san\s+diego\b',
    r'\bmethods\s*\(\s*elsevier\b',
    r'\bjournal\s+of\s+microscopy\b.*protocol',
    r'\bmicroscopy\s+research\s+and\s+technique\b.*protocol',
    r'\bdetailed\s+protocol\b',
    r'\bstep.by.step\s+protocol\b',
    r'\boptimized\s+protocol\b',
    r'\bimproved\s+protocol\b',
]

ROR_PATTERNS = [
    # ROR IDs are 9 alphanumeric characters starting with 0
    # Examples: 03vek6s52 (Harvard), 05a0ya142 (MIT), 00hj8s172 (Stanford)
    (r'https?://ror\.org/(0[a-z0-9]{8})', 'url'),
    (r'\bROR[:\s]+?(0[a-z0-9]{8})\b', 'text'),
    (r'\bror[:\s]+?(0[a-z0-9]{8})\b', 'text'),
    (r'\bROR:\s*(0[a-z0-9]{8})\b', 'text'),
    (r'\(ROR:\s*(0[a-z0-9]{8})\)', 'text'),
    # Sometimes written with spaces or dashes
    (r'\bROR\s*ID[:\s]+?(0[a-z0-9]{8})\b', 'text'),
    # In DOI format
    (r'doi\.org/10\.(?:ror|ROR)/(0[a-z0-9]{8})', 'doi'),
]

# ============================================================================
# INSTITUTION EXTRACTION PATTERNS
# These extract research institutions where authors are from (not imaging facilities)
# ============================================================================

# Patterns to identify institution types
INSTITUTION_PATTERNS = [
    # Universities
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+University)\b',
    r'\b(University\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)\b',
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+(?:State\s+)?University)\b',
    r'\b(Universit[éèy]\s+(?:de\s+|di\s+)?[A-Z][A-Za-z\'\-àéèêë]+(?:\s+[A-Z][A-Za-z\'\-àéèêë]+)*)\b',
    r'\b(Universität\s+[A-Z][A-Za-zäöüß\'\-]+(?:\s+[A-Z][A-Za-zäöüß\'\-]+)*)\b',
    
    # Institutes and Research Centers
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+Institute(?:\s+(?:of|for)\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)?)\b',
    r'\b(Institute\s+(?:of|for)\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)\b',
    r'\b(Max\s+Planck\s+Institute(?:\s+(?:of|for)\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)?)\b',
    r'\b(National\s+Institutes?\s+of\s+Health|NIH)\b',
    r'\b(Research\s+Institute(?:\s+(?:of|for)\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)?)\b',
    
    # Medical Centers and Hospitals
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+(?:Medical\s+(?:Center|School|College)|Hospital|Health\s+(?:Center|System)))\b',
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+Children\'?s?\s+Hospital)\b',
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+Cancer\s+(?:Center|Institute|Hospital))\b',
    
    # Colleges
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+College(?:\s+of\s+[A-Z][A-Za-z\'\-]+)?)\b',
    
    # Labs and Centers
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+(?:National\s+)?Laboratory)\b',
    r'\b([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+Research\s+Center)\b',
]

# Known major research institutions - canonical names with locations
KNOWN_INSTITUTIONS = {
    # Major US Universities
    'harvard': 'Harvard University',
    'harvard university': 'Harvard University',
    'harvard medical school': 'Harvard Medical School',
    'mit': 'Massachusetts Institute of Technology',
    'massachusetts institute of technology': 'Massachusetts Institute of Technology',
    'stanford': 'Stanford University',
    'stanford university': 'Stanford University',
    'caltech': 'California Institute of Technology',
    'california institute of technology': 'California Institute of Technology',
    'yale': 'Yale University',
    'yale university': 'Yale University',
    'princeton': 'Princeton University',
    'princeton university': 'Princeton University',
    'columbia': 'Columbia University',
    'columbia university': 'Columbia University',
    'uc berkeley': 'University of California, Berkeley',
    'university of california berkeley': 'University of California, Berkeley',
    'university of california, berkeley': 'University of California, Berkeley',
    'berkeley': 'University of California, Berkeley',
    'ucla': 'University of California, Los Angeles',
    'university of california los angeles': 'University of California, Los Angeles',
    'ucsf': 'University of California, San Francisco',
    'university of california san francisco': 'University of California, San Francisco',
    'ucsd': 'University of California, San Diego',
    'university of california san diego': 'University of California, San Diego',
    'uc san diego': 'University of California, San Diego',
    'johns hopkins': 'Johns Hopkins University',
    'johns hopkins university': 'Johns Hopkins University',
    'upenn': 'University of Pennsylvania',
    'university of pennsylvania': 'University of Pennsylvania',
    'penn': 'University of Pennsylvania',
    'uchicago': 'University of Chicago',
    'university of chicago': 'University of Chicago',
    'northwestern': 'Northwestern University',
    'northwestern university': 'Northwestern University',
    'duke': 'Duke University',
    'duke university': 'Duke University',
    'washington university': 'Washington University in St. Louis',
    'washington university in st. louis': 'Washington University in St. Louis',
    'wustl': 'Washington University in St. Louis',
    'university of washington': 'University of Washington',
    'uw': 'University of Washington',
    'cornell': 'Cornell University',
    'cornell university': 'Cornell University',
    'nyu': 'New York University',
    'new york university': 'New York University',
    'university of michigan': 'University of Michigan',
    'umich': 'University of Michigan',
    'michigan': 'University of Michigan',
    'university of wisconsin': 'University of Wisconsin-Madison',
    'uw madison': 'University of Wisconsin-Madison',
    'ut austin': 'University of Texas at Austin',
    'university of texas austin': 'University of Texas at Austin',
    'ut southwestern': 'UT Southwestern Medical Center',
    'ut southwestern medical center': 'UT Southwestern Medical Center',
    'md anderson': 'MD Anderson Cancer Center',
    'md anderson cancer center': 'MD Anderson Cancer Center',
    'mayo clinic': 'Mayo Clinic',
    'scripps research': 'Scripps Research Institute',
    'scripps': 'Scripps Research Institute',
    
    # Major US Research Institutes
    'nih': 'National Institutes of Health',
    'national institutes of health': 'National Institutes of Health',
    'broad institute': 'Broad Institute',
    'whitehead institute': 'Whitehead Institute',
    'cold spring harbor': 'Cold Spring Harbor Laboratory',
    'cold spring harbor laboratory': 'Cold Spring Harbor Laboratory',
    'cshl': 'Cold Spring Harbor Laboratory',
    'salk institute': 'Salk Institute',
    'janelia': 'HHMI Janelia Research Campus',
    'janelia research campus': 'HHMI Janelia Research Campus',
    'allen institute': 'Allen Institute',
    'stowers institute': 'Stowers Institute',
    'rockefeller university': 'Rockefeller University',
    'rockefeller': 'Rockefeller University',
    
    # UK Universities and Institutes
    'oxford': 'University of Oxford',
    'university of oxford': 'University of Oxford',
    'cambridge': 'University of Cambridge',
    'university of cambridge': 'University of Cambridge',
    'imperial college': 'Imperial College London',
    'imperial college london': 'Imperial College London',
    'ucl': 'University College London',
    'university college london': 'University College London',
    'kings college london': "King's College London",
    "king's college london": "King's College London",
    'edinburgh': 'University of Edinburgh',
    'university of edinburgh': 'University of Edinburgh',
    'manchester': 'University of Manchester',
    'university of manchester': 'University of Manchester',
    'mrc laboratory of molecular biology': 'MRC Laboratory of Molecular Biology',
    'mrc lmb': 'MRC Laboratory of Molecular Biology',
    'francis crick': 'Francis Crick Institute',
    'francis crick institute': 'Francis Crick Institute',
    'crick institute': 'Francis Crick Institute',
    'wellcome sanger': 'Wellcome Sanger Institute',
    'sanger institute': 'Wellcome Sanger Institute',
    
    # European Institutions
    'embl': 'European Molecular Biology Laboratory',
    'european molecular biology laboratory': 'European Molecular Biology Laboratory',
    'max planck': 'Max Planck Institute',
    'eth zurich': 'ETH Zurich',
    'eth zürich': 'ETH Zurich',
    'epfl': 'EPFL Lausanne',
    'karolinska': 'Karolinska Institute',
    'karolinska institute': 'Karolinska Institute',
    'pasteur': 'Institut Pasteur',
    'institut pasteur': 'Institut Pasteur',
    'curie': 'Institut Curie',
    'institut curie': 'Institut Curie',
    'cnrs': 'CNRS',
    'inserm': 'INSERM',
    
    # Asian/Pacific Institutions  
    'university of tokyo': 'University of Tokyo',
    'tokyo university': 'University of Tokyo',
    'kyoto university': 'Kyoto University',
    'riken': 'RIKEN',
    'national university of singapore': 'National University of Singapore',
    'nus': 'National University of Singapore',
    'tsinghua': 'Tsinghua University',
    'tsinghua university': 'Tsinghua University',
    'peking university': 'Peking University',
    'chinese academy of sciences': 'Chinese Academy of Sciences',
    'cas': 'Chinese Academy of Sciences',
    'university of melbourne': 'University of Melbourne',
    'university of sydney': 'University of Sydney',
    'australian national university': 'Australian National University',
    'anu': 'Australian National University',
    
    # Canadian Institutions
    'university of toronto': 'University of Toronto',
    'uoft': 'University of Toronto',
    'mcgill': 'McGill University',
    'mcgill university': 'McGill University',
    'university of british columbia': 'University of British Columbia',
    'ubc': 'University of British Columbia',
    'sick kids': 'SickKids Research Institute',
    'sickkids': 'SickKids Research Institute',
}

# ROR (Research Organization Registry) IDs for known institutions
# These are looked up based on institution name since ROR IDs aren't in paper text
INSTITUTION_ROR_IDS = {
    'Harvard University': '03vek6s52',
    'Harvard Medical School': '03vek6s52',
    'Massachusetts Institute of Technology': '042nb2s44',
    'Stanford University': '00f54p054',
    'California Institute of Technology': '05dxps055',
    'Yale University': '03v76x132',
    'Princeton University': '00hx57361',
    'Columbia University': '00hj8s172',
    'University of California, Berkeley': '01an7q238',
    'University of California, Los Angeles': '046rm7j60',
    'University of California, San Francisco': '043mz5j54',
    'University of California, San Diego': '0168r3w48',
    'Johns Hopkins University': '00za53h95',
    'University of Pennsylvania': '00b30xv10',
    'University of Chicago': '024mw5h28',
    'Northwestern University': '000e0be47',
    'Duke University': '00py81415',
    'Washington University in St. Louis': '01yc7t268',
    'University of Washington': '00cvxb145',
    'Cornell University': '05bnh6r87',
    'New York University': '0190ak572',
    'University of Michigan': '00jmfr291',
    'University of Wisconsin-Madison': '01y2jtd41',
    'University of Texas at Austin': '00hj54h04',
    'UT Southwestern Medical Center': '00a4bsz29',
    'MD Anderson Cancer Center': '04twxam07',
    'Mayo Clinic': '02qp3tb03',
    'Scripps Research Institute': '02dxx6824',
    'National Institutes of Health': '01cwqze88',
    'Broad Institute': '05a0ya142',
    'Whitehead Institute': '00x0k6167',
    'Cold Spring Harbor Laboratory': '02qz8b764',
    'Salk Institute': '03xez1567',
    'HHMI Janelia Research Campus': '013sk6x84',
    'Allen Institute': '03cpe7c52',
    'Stowers Institute': '00h0r6t62',
    'Rockefeller University': '0420db125',
    'University of Oxford': '052gg0110',
    'University of Cambridge': '013meh722',
    'Imperial College London': '041kmwe10',
    'University College London': '02jx3x895',
    "King's College London": '0220mzb33',
    'University of Edinburgh': '01nrxwf90',
    'University of Manchester': '027m9bs27',
    'MRC Laboratory of Molecular Biology': '00tw3jy02',
    'Francis Crick Institute': '042fqyp44',
    'Wellcome Sanger Institute': '05cy4wa09',
    'European Molecular Biology Laboratory': '03mstc592',
    'Max Planck Society': '01hhn8329',
    'ETH Zurich': '05a28rw58',
    'EPFL Lausanne': '02s376052',
    'Karolinska Institute': '056d84691',
    'Institut Pasteur': '0495fxg12',
    'Institut Curie': '04t0gwh46',
    'CNRS': '02feahw73',
    'INSERM': '02vjkv261',
    'University of Tokyo': '057zh3y96',
    'Kyoto University': '02kpeqv85',
    'RIKEN': '01sjwvz98',
    'National University of Singapore': '01tgyzw49',
    'Tsinghua University': '03cve4549',
    'Peking University': '02v51f717',
    'Chinese Academy of Sciences': '034t30j35',
    'University of Melbourne': '01ej9dk98',
    'University of Sydney': '0384j8v12',
    'Australian National University': '019wvm592',
    'University of Toronto': '03dbr7087',
    'McGill University': '01pxwe438',
    'University of British Columbia': '03rmrcq20',
    'SickKids Research Institute': '04374qe70',
}

# Phrases that indicate acknowledgments rather than author affiliations
ACKNOWLEDGMENT_EXCLUSIONS = [
    r'\bwe\s+(?:thank|acknowledge|are\s+grateful\s+to)\s+',
    r'\bthanks?\s+(?:to|go\s+to)\s+',
    r'\backnowledge(?:s|d)?\s+',
    r'\bgrateful\s+to\s+',
    r'\bfunded\s+by\s+',
    r'\bsupported\s+by\s+a?\s*(?:grant|fellowship|award)\s+',
    r'\bprovided\s+by\s+',
    r'\bgenerous(?:ly)?\s+(?:provided|shared|contributed)\s+',
    r'\bcourtesy\s+of\s+',
    r'\bgift\s+from\s+',
]

REPOSITORY_PATTERNS = {
    'Zenodo': r'(https?://(?:www\.)?zenodo\.org/record[s]?/\d+)',
    'Figshare': r'(https?://(?:www\.)?figshare\.com/articles/[\w/.-]+)',
    'GitHub': r'(https?://(?:www\.)?github\.com/[\w-]+/[\w.-]+)',
    'Dryad': r'(https?://(?:www\.)?datadryad\.org/[\w/.-]+)',
    'OSF': r'(https?://osf\.io/[\w]+)',
    'EMPIAR': r'(https?://(?:www\.)?ebi\.ac\.uk/empiar/[\w/.-]+)',
    'BioStudies': r'(https?://(?:www\.)?ebi\.ac\.uk/biostudies/[\w/.-]+)',
    'IDR': r'(https?://idr\.openmicroscopy\.org/[\w/.-]+)',
    'BioImage Archive': r'(https?://(?:www\.)?ebi\.ac\.uk/bioimage-archive/[\w/.-]+)',
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
    (r'(?:Invitrogen)[:\s#]*(\w+-\d+)', 'Invitrogen'),
    (r'(?:Thermo\s*Fisher)[:\s#]*(\w+-\d+)', 'Thermo Fisher'),
]


# ============================================================================
# NORMALIZATION FUNCTIONS
# ============================================================================

def normalize_tag(tag: str, canonical_map: Dict[str, str]) -> str:
    """Normalize a tag to its canonical form."""
    tag_lower = tag.lower().strip()
    if tag_lower in canonical_map:
        return canonical_map[tag_lower]
    canonical_values = set(canonical_map.values())
    if tag in canonical_values:
        return tag
    return tag


def normalize_tag_list(tags: List[str], canonical_map: Dict[str, str]) -> List[str]:
    """Normalize a list of tags, removing duplicates after normalization."""
    if not tags:
        return []
    normalized = []
    seen = set()
    for tag in tags:
        norm_tag = normalize_tag(tag, canonical_map)
        norm_lower = norm_tag.lower()
        if norm_lower not in seen:
            normalized.append(norm_tag)
            seen.add(norm_lower)
    return normalized


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

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


def extract_rors(text: str) -> List[Dict]:
    """Extract ROR (Research Organization Registry) IDs from text.
    
    ROR IDs are 9 alphanumeric characters starting with 0.
    Examples: 03vek6s52, 05a0ya142, 00hj8s172
    """
    if not text:
        return []
    
    found = []
    seen = set()
    
    for pattern, source_type in ROR_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            ror_id = match.group(1).lower()  # Normalize to lowercase
            # Validate: 9 chars, starts with 0, alphanumeric
            if ror_id and len(ror_id) == 9 and ror_id[0] == '0' and ror_id.isalnum():
                if ror_id not in seen:
                    seen.add(ror_id)
                    found.append({
                        'id': ror_id,
                        'url': f'https://ror.org/{ror_id}',
                        'source': source_type,
                    })
    
    return found


def extract_institutions(paper: Dict) -> List[str]:
    """Extract research institutions where the paper originated from.
    
    IMPORTANT: Only extracts from author affiliations field to avoid false positives.
    We do NOT extract from abstract/methods/full_text because institutions mentioned
    there are often from citations or references, not the paper's origin.
    
    Returns all unique institutions found (supports multi-institutional collaborations).
    """
    found = []
    seen = set()
    
    def normalize_institution(name: str) -> str:
        """Normalize institution name to canonical form."""
        if not name:
            return ''
        
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        name = name.strip(' ,.')
        
        # Check against known institutions for canonical name
        name_lower = name.lower()
        if name_lower in KNOWN_INSTITUTIONS:
            return KNOWN_INSTITUTIONS[name_lower]
        
        # Check if any known institution is mentioned in the name
        for search_term, canonical_name in KNOWN_INSTITUTIONS.items():
            if len(search_term) > 3 and search_term in name_lower:
                return canonical_name
        
        return name
    
    def add_institution(name: str):
        """Add institution to list if not already present."""
        name = normalize_institution(name)
        if not name or len(name) < 5:
            return
        
        name_lower = name.lower()
        
        # Skip generic terms that aren't real institutions
        skip_terms = ['department of', 'school of', 'faculty of', 'division of', 
                      'center for', 'centre for', 'program in', 'laboratory of',
                      'institute for', 'unit of']
        if any(name_lower.startswith(term) for term in skip_terms):
            # But if it contains a known university, extract that
            for search_term, canonical_name in KNOWN_INSTITUTIONS.items():
                if len(search_term) > 5 and search_term in name_lower:
                    name = canonical_name
                    name_lower = name.lower()
                    break
            else:
                return  # Skip if no known institution found
        
        if name_lower not in seen:
            seen.add(name_lower)
            found.append(name)
    
    def extract_institution_from_affiliation(aff_text: str):
        """Extract institution from an affiliation string."""
        if not aff_text:
            return
        
        aff_lower = aff_text.lower()
        
        # First, check for known institutions
        for search_term, canonical_name in KNOWN_INSTITUTIONS.items():
            if len(search_term) > 3 and search_term in aff_lower:
                add_institution(canonical_name)
                return  # Found a match, don't need to continue
        
        # Try to extract university/institute names with patterns
        patterns = [
            # "University of X" pattern
            r'(University\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)',
            # "X University" pattern  
            r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+University)',
            # "X Institute" pattern
            r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+Institute(?:\s+(?:of|for)\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*)?)',
            # "X Medical Center/School" pattern
            r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+(?:Medical\s+(?:Center|School|College)|Hospital))',
            # "X College" pattern
            r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*\s+College)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, aff_text)
            if match:
                add_institution(match.group(1))
                return
    
    # ==========================================
    # ONLY extract from affiliations - NOT from abstract/methods/full_text
    # This prevents false positives from cited institutions
    # ==========================================
    
    # 1. Check affiliations field (primary source)
    affiliations = paper.get('affiliations', [])
    if isinstance(affiliations, str):
        try:
            affiliations = json.loads(affiliations)
        except:
            # It's a string, might be comma-separated
            affiliations = [a.strip() for a in affiliations.split(';') if a.strip()]
            if len(affiliations) == 1:
                affiliations = [a.strip() for a in affiliations[0].split(',') if a.strip()]
    
    if isinstance(affiliations, list):
        for aff in affiliations:
            if isinstance(aff, dict):
                aff_name = aff.get('name', '') or aff.get('institution', '') or aff.get('affiliation', '') or aff.get('org', '')
                extract_institution_from_affiliation(aff_name)
            elif isinstance(aff, str):
                extract_institution_from_affiliation(aff)
    
    # 2. Check author_affiliations field (some scrapers use this)
    author_affs = paper.get('author_affiliations', [])
    if isinstance(author_affs, str):
        try:
            author_affs = json.loads(author_affs)
        except:
            author_affs = [author_affs]
    
    if isinstance(author_affs, list):
        for aff in author_affs:
            if isinstance(aff, dict):
                aff_name = aff.get('affiliation', '') or aff.get('institution', '') or aff.get('name', '')
                extract_institution_from_affiliation(aff_name)
            elif isinstance(aff, str):
                extract_institution_from_affiliation(aff)
    
    # 3. Check authors field for embedded affiliations
    authors = paper.get('authors', [])
    if isinstance(authors, list):
        for author in authors:
            if isinstance(author, dict):
                # Check for affiliation in author dict
                aff = author.get('affiliation', '') or author.get('affiliations', '') or author.get('institution', '')
                if isinstance(aff, list):
                    for a in aff:
                        if isinstance(a, str):
                            extract_institution_from_affiliation(a)
                        elif isinstance(a, dict):
                            extract_institution_from_affiliation(a.get('name', '') or a.get('institution', ''))
                elif isinstance(aff, str):
                    extract_institution_from_affiliation(aff)
    
    # Deduplicate: prefer more specific names
    final_institutions = []
    for inst in found:
        inst_lower = inst.lower()
        
        # Skip if this is a substring of an already-found institution
        is_substring = False
        for existing in final_institutions:
            existing_lower = existing.lower()
            if inst_lower in existing_lower and inst_lower != existing_lower:
                is_substring = True
                break
        
        if is_substring:
            continue
        
        # Remove any existing institutions that are substrings of this one
        final_institutions = [
            existing for existing in final_institutions
            if existing.lower() not in inst_lower or existing.lower() == inst_lower
        ]
        final_institutions.append(inst)

    return final_institutions


# Keep extract_facilities as alias for backward compatibility
def extract_facilities(text: str) -> List[str]:
    """Deprecated - use extract_institutions instead."""
    return []


def is_protocol_paper(paper: Dict) -> bool:
    """Check if a paper is from a protocol journal or is a protocol paper."""
    journal = str(paper.get('journal', '') or '').lower()
    source = str(paper.get('source', '') or '').lower()
    title = str(paper.get('title', '') or '').lower()
    doi = str(paper.get('doi', '') or '').lower()
    
    combined = f"{journal} {source} {title}"
    
    for pattern in PROTOCOL_JOURNALS:
        if re.search(pattern, combined, re.IGNORECASE):
            return True
    
    protocol_doi_patterns = [
        r'10\.1038/nprot',
        r'10\.1038/s41596',
        r'10\.3791/',
        r'10\.1016/j\.xpro',
        r'10\.21769/bioprotoc',
        r'10\.1002/cp',
        r'10\.1007/978-1-',
        r'10\.1016/bs\.mie',
        r'10\.1101/pdb\.prot',
        r'10\.1016/j\.mex',
    ]
    
    for pattern in protocol_doi_patterns:
        if re.search(pattern, doi, re.IGNORECASE):
            return True
    
    return False


def get_protocol_type(paper: Dict) -> Optional[str]:
    """Determine the type/source of protocol for categorization."""
    journal = str(paper.get('journal', '') or '').lower()
    doi = str(paper.get('doi', '') or '').lower()
    
    type_mapping = [
        (r'nature\s+protocols?|10\.1038/nprot|10\.1038/s41596', 'Nature Protocols'),
        (r'jove|journal\s+of\s+visualized|10\.3791/', 'JoVE'),
        (r'star\s+protocols?|10\.1016/j\.xpro', 'STAR Protocols'),
        (r'bio.?protocol|10\.21769/bioprotoc', 'Bio-protocol'),
        (r'current\s+protocols?|10\.1002/cp', 'Current Protocols'),
        (r'methods\s+in\s+molecular\s+biology|10\.1007/978-1-', 'Methods in Molecular Biology'),
        (r'methods\s+in\s+enzymology|10\.1016/bs\.mie', 'Methods in Enzymology'),
        (r'cold\s+spring\s+harbor|cshprotocols|10\.1101/pdb', 'Cold Spring Harbor Protocols'),
        (r'methodsx|methods\s*x|10\.1016/j\.mex', 'MethodsX'),
        (r'protocol\s+exchange', 'Protocol Exchange'),
        (r'biotechniques', 'Biotechniques'),
    ]
    
    combined = f"{journal} {doi}"
    for pattern, protocol_type in type_mapping:
        if re.search(pattern, combined, re.IGNORECASE):
            return protocol_type
    
    return None


def merge_lists(existing: List, new: List) -> List:
    """Merge two lists, removing duplicates."""
    if not existing:
        existing = []
    if not new:
        return existing
    
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
        existing_set = set(str(x).lower() for x in existing)
        for item in new:
            if str(item).lower() not in existing_set:
                existing.append(item)
                existing_set.add(str(item).lower())
    
    return existing


def clean_github_tools(paper: Dict) -> List[Dict]:
    """
    Validate, deduplicate, and normalize github_tools from the scraper/export.
    
    The scraper extracts GitHub URLs from paper text and the export enriches them
    with metrics from the GitHub API (stars, forks, health_score, etc.).
    This function preserves that data while ensuring consistency.
    
    Expected input per tool (from export):
        full_name, url, description, stars, forks, open_issues,
        last_commit_date, last_release, health_score, is_archived,
        language, license, topics, paper_count, citing_paper_count,
        relationship (introduces/uses/extends/benchmarks)
    
    Returns a cleaned list of github_tool dicts.
    """
    tools = paper.get('github_tools', [])
    
    # Handle string-encoded JSON (sometimes happens in export/import round-trips)
    if isinstance(tools, str):
        try:
            tools = json.loads(tools)
        except (json.JSONDecodeError, TypeError):
            tools = []
    
    if not isinstance(tools, list):
        return []
    
    cleaned = []
    seen_names = set()
    
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        
        # full_name is the unique key (e.g., "owner/repo")
        full_name = str(tool.get('full_name', '') or '').strip()
        if not full_name:
            # Try to derive from url
            url = str(tool.get('url', '') or '')
            match = re.search(r'github\.com/([\w.-]+/[\w.-]+)', url)
            if match:
                full_name = match.group(1).rstrip('.')
            else:
                continue  # Skip entries with no identifiable repo
        
        # Normalize: strip trailing .git, lowercase for dedup check
        full_name = re.sub(r'\.git$', '', full_name)
        dedup_key = full_name.lower()
        
        if dedup_key in seen_names:
            continue
        seen_names.add(dedup_key)
        
        # Ensure url is present and well-formed
        url = str(tool.get('url', '') or '').strip()
        if not url or 'github.com' not in url:
            url = f"https://github.com/{full_name}"
        
        # Validate relationship type
        relationship = str(tool.get('relationship', 'uses') or 'uses').lower().strip()
        if relationship not in ('introduces', 'uses', 'extends', 'benchmarks'):
            relationship = 'uses'
        
        # Ensure topics is a list
        topics = tool.get('topics', [])
        if isinstance(topics, str):
            try:
                topics = json.loads(topics)
            except (json.JSONDecodeError, TypeError):
                topics = []
        if not isinstance(topics, list):
            topics = []
        topics = [str(t).strip() for t in topics if t]
        
        cleaned.append({
            'full_name': full_name,
            'url': url,
            'description': str(tool.get('description', '') or '').strip(),
            'stars': int(tool.get('stars', 0) or 0),
            'forks': int(tool.get('forks', 0) or 0),
            'open_issues': int(tool.get('open_issues', 0) or 0),
            'last_commit_date': str(tool.get('last_commit_date', '') or '').strip(),
            'last_release': str(tool.get('last_release', '') or '').strip(),
            'health_score': int(tool.get('health_score', 0) or 0),
            'is_archived': bool(tool.get('is_archived', False)),
            'language': str(tool.get('language', '') or '').strip(),
            'license': str(tool.get('license', '') or '').strip(),
            'topics': topics,
            'paper_count': int(tool.get('paper_count', 0) or 0),
            'citing_paper_count': int(tool.get('citing_paper_count', 0) or 0),
            'relationship': relationship,
        })
    
    return cleaned


def clean_paper(paper: Dict) -> Dict:
    """Clean and re-tag a single paper."""
    
    # Get full_text for tag extraction, but we won't store it
    full_text = str(paper.get('full_text', '') or '')
    
    # Clean garbage patterns
    garbage_patterns = [
        r'^Technique\s+Microscope\s+Organism\s+Software\s*',
        r'^pmc-status-\S+\s*',
        r'^pmc-prop-\S+\s*',
        r'pmc-status-\w+\s+\w+\s+pmc-',
        r'pmc-license-\S+\s*',
    ]
    for pattern in garbage_patterns:
        full_text = re.sub(pattern, '', full_text, flags=re.IGNORECASE | re.MULTILINE)
    
    for field in ['abstract', 'methods']:
        text = str(paper.get(field, '') or '')
        for pattern in garbage_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        paper[field] = text.strip()
    
    # Extract tags from ALL text sources (title + abstract + methods + full_text)
    # This ensures comprehensive tagging even though we don't store full_text
    text_parts = [
        str(paper.get('title', '') or ''),
        str(paper.get('abstract', '') or ''),
        str(paper.get('methods', '') or ''),
        full_text,  # Use for extraction but don't store
    ]
    combined_text = ' '.join(text_parts)
    
    raw_techniques = extract_tags(combined_text, MICROSCOPY_TECHNIQUES)
    raw_software = extract_tags(combined_text, IMAGE_ANALYSIS_SOFTWARE)
    raw_brands = extract_tags(combined_text, MICROSCOPE_BRANDS)
    raw_fluorophores = extract_tags(combined_text, FLUOROPHORES)
    raw_organisms = extract_tags(combined_text, ORGANISMS)
    raw_cell_lines = extract_tags(combined_text, CELL_LINES)
    raw_sample_prep = extract_tags(combined_text, SAMPLE_PREPARATION)
    
    paper['microscopy_techniques'] = normalize_tag_list(
        merge_lists(paper.get('microscopy_techniques', []), raw_techniques),
        TECHNIQUE_CANONICAL
    )
    
    paper['image_analysis_software'] = normalize_tag_list(
        merge_lists(paper.get('image_analysis_software', []), raw_software),
        SOFTWARE_CANONICAL
    )
    
    paper['microscope_brands'] = normalize_tag_list(
        merge_lists(paper.get('microscope_brands', []), raw_brands),
        MICROSCOPE_BRAND_CANONICAL
    )
    
    paper['fluorophores'] = normalize_tag_list(
        merge_lists(paper.get('fluorophores', []), raw_fluorophores),
        FLUOROPHORE_CANONICAL
    )
    
    paper['organisms'] = normalize_tag_list(
        merge_lists(paper.get('organisms', []), raw_organisms),
        ORGANISM_CANONICAL
    )
    
    paper['cell_lines'] = normalize_tag_list(
        merge_lists(paper.get('cell_lines', []), raw_cell_lines),
        CELL_LINE_CANONICAL
    )
    
    paper['sample_preparation'] = normalize_tag_list(
        merge_lists(paper.get('sample_preparation', []), raw_sample_prep),
        SAMPLE_PREP_CANONICAL
    )
    
    paper['protocols'] = merge_lists(
        paper.get('protocols', []),
        extract_urls(combined_text, PROTOCOL_PATTERNS)
    )
    
    paper['repositories'] = merge_lists(
        paper.get('repositories', []),
        extract_urls(combined_text, REPOSITORY_PATTERNS)
    )
    
    # ==========================================
    # GITHUB TOOLS - Clean and validate detailed repo data (scraper v5.1+)
    # ==========================================
    paper['github_tools'] = clean_github_tools(paper)
    
    # If we have github_tools but no github_url, derive it from the tools
    # Prefer a tool the paper "introduces" (the paper's own tool), otherwise use first tool
    if not paper.get('github_url') and paper['github_tools']:
        introduced = [t for t in paper['github_tools'] if t['relationship'] == 'introduces']
        if introduced:
            paper['github_url'] = introduced[0]['url']
        else:
            paper['github_url'] = paper['github_tools'][0]['url']
    
    paper['rrids'] = merge_lists(
        paper.get('rrids', []),
        extract_rrids(combined_text)
    )
    
    paper['antibodies'] = merge_lists(
        paper.get('antibodies', []),
        extract_antibodies(combined_text)
    )
    
    new_rors = extract_rors(combined_text)
    existing_rors = paper.get('rors', [])
    if existing_rors:
        existing_rors = [
            r for r in existing_rors
            if isinstance(r, dict) and str(r.get('id', '')).startswith('0')
        ]
    paper['rors'] = merge_lists(existing_rors, new_rors)
    
    # Extract institutions (research institutions where authors are from)
    # This replaces the old facility extraction
    # IMPORTANT: We do NOT merge with old facility data because it was often incorrect
    # (picking up random institution mentions from text instead of author affiliations)
    new_institutions = extract_institutions(paper)
    
    # Only use newly extracted institutions - don't carry over old bad data
    all_institutions = new_institutions
    
    # Look up ROR IDs for known institutions
    ror_ids_from_institutions = []
    for inst in all_institutions:
        if inst in INSTITUTION_ROR_IDS:
            ror_id = INSTITUTION_ROR_IDS[inst]
            ror_ids_from_institutions.append({
                'id': ror_id,
                'url': f'https://ror.org/{ror_id}',
                'source': 'institution_lookup',
                'institution': inst,
            })
    
    # Merge ROR IDs from institutions with any found in text
    existing_rors = paper.get('rors', [])
    if existing_rors:
        existing_rors = [
            r for r in existing_rors
            if isinstance(r, dict) and str(r.get('id', '')).startswith('0')
        ]
    
    # Combine and deduplicate ROR IDs
    all_rors = existing_rors + ror_ids_from_institutions
    seen_ror_ids = set()
    paper['rors'] = []
    for ror in all_rors:
        if isinstance(ror, dict) and ror.get('id') and ror['id'] not in seen_ror_ids:
            seen_ror_ids.add(ror['id'])
            paper['rors'].append(ror)
    
    paper['institutions'] = all_institutions
    # Keep 'facilities' for backward compatibility but point to institutions
    paper['facilities'] = all_institutions
    # Primary institution (first one) for display
    paper['facility'] = all_institutions[0] if all_institutions else ''
    paper['imaging_facility'] = ''  # Clear old field
    
    paper['techniques'] = paper['microscopy_techniques']
    paper['tags'] = paper['microscopy_techniques']
    
    paper['software'] = list(set(
        (paper.get('image_analysis_software') or []) + 
        (paper.get('image_acquisition_software') or [])
    ))
    
    paper['is_protocol'] = is_protocol_paper(paper) or bool(paper.get('protocols'))
    
    if is_protocol_paper(paper):
        paper['post_type'] = 'mh_protocol'
        paper['protocol_type'] = get_protocol_type(paper)
    else:
        paper['post_type'] = 'mh_paper'
        paper['protocol_type'] = None
    
    # Full text is no longer stored - always false
    paper['has_full_text'] = False
    paper['has_protocols'] = bool(paper.get('protocols')) or paper.get('is_protocol', False)
    paper['has_github'] = bool(paper.get('github_url'))
    paper['has_github_tools'] = bool(paper.get('github_tools'))
    paper['has_data'] = bool(paper.get('repositories'))
    paper['has_rrids'] = bool(paper.get('rrids'))
    paper['has_rors'] = bool(paper.get('rors'))
    paper['has_fluorophores'] = bool(paper.get('fluorophores'))
    paper['has_cell_lines'] = bool(paper.get('cell_lines'))
    paper['has_sample_prep'] = bool(paper.get('sample_preparation'))
    paper['has_methods'] = bool(paper.get('methods') and len(str(paper.get('methods', ''))) > 100)
    paper['has_institutions'] = bool(paper.get('institutions'))
    paper['has_facility'] = paper['has_institutions']  # Backward compatibility
    
    # REMOVE full_text from output to save database space
    # Tags were already extracted above, so we don't need it anymore
    if 'full_text' in paper:
        del paper['full_text']
    
    return paper


def process_file(input_file: str, output_file: str) -> Dict:
    """Process a single JSON file and return statistics."""
    
    print(f"\nLoading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    if not isinstance(papers, list):
        papers = [papers]
    
    print(f"Processing {len(papers)} papers...")
    
    fields_to_track = [
        'microscopy_techniques', 'microscope_brands', 'image_analysis_software',
        'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
        'protocols', 'repositories', 'rrids', 'rors', 'antibodies', 'institutions',
        'github_tools', 'is_protocol'
    ]
    
    stats_before = {f: sum(1 for p in papers if p.get(f)) for f in fields_to_track}
    
    for i, paper in enumerate(papers):
        papers[i] = clean_paper(paper)
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(papers)} papers...")
    
    stats_after = {f: sum(1 for p in papers if p.get(f)) for f in fields_to_track}
    
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    return {'papers': len(papers), 'before': stats_before, 'after': stats_after}


def main():
    import glob
    import os
    import argparse
    
    # Always work in the script's directory, not the current working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    parser = argparse.ArgumentParser(description='Clean and re-tag MicroHub JSON files with normalization')
    parser.add_argument('--input', '-i', help='Input JSON file (default: all chunk files in script directory)')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--pattern', default='microhub_papers_v*_chunk_*.json',
                        help='Glob pattern to find JSON files')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite input files instead of creating new ones')
    parser.add_argument('--output-dir', default='cleaned_export',
                        help='Output directory for cleaned files')
    
    args = parser.parse_args()
    
    if args.input:
        # If input file is specified, make it absolute if it's not already
        if not os.path.isabs(args.input):
            args.input = os.path.join(script_dir, args.input)
        input_files = [args.input]
    else:
        # Search for JSON files in the script's directory
        pattern_path = os.path.join(script_dir, args.pattern)
        input_files = sorted(glob.glob(pattern_path))
        if not input_files:
            input_files = sorted(glob.glob(os.path.join(script_dir, '*_chunk_*.json')))
        if not input_files:
            input_files = sorted(glob.glob(os.path.join(script_dir, 'microhub*.json')))
    
    if not input_files:
        print(f"No JSON files found in {script_dir}!")
        print("Use --input to specify a file or --pattern for a glob pattern.")
        sys.exit(1)
    
    print("=" * 60)
    print("MICROHUB CLEANUP AND RE-TAGGING v3.2")
    print("With tag normalization, GitHub tools, and institution fixes")
    print("=" * 60)
    print(f"Script directory: {script_dir}")
    print(f"Found {len(input_files)} JSON file(s)")
    
    if not args.overwrite:
        # Make output directory relative to script directory
        if not os.path.isabs(args.output_dir):
            args.output_dir = os.path.join(script_dir, args.output_dir)
        os.makedirs(args.output_dir, exist_ok=True)
        print(f"Output directory: {args.output_dir}")
    else:
        print("Mode: Overwriting input files")
    
    fields_to_track = [
        'microscopy_techniques', 'microscope_brands', 'image_analysis_software',
        'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
        'protocols', 'repositories', 'rrids', 'rors', 'antibodies', 'institutions',
        'github_tools', 'is_protocol'
    ]
    total_before = {f: 0 for f in fields_to_track}
    total_after = {f: 0 for f in fields_to_track}
    total_papers = 0
    
    for input_file in input_files:
        if args.overwrite:
            output_file = input_file
        elif args.output and len(input_files) == 1:
            output_file = args.output
        else:
            base = os.path.basename(input_file)
            output_file = os.path.join(args.output_dir, base)
        
        result = process_file(input_file, output_file)
        total_papers += result['papers']
        for f in fields_to_track:
            total_before[f] += result['before'][f]
            total_after[f] += result['after'][f]
    
    print("\n" + "=" * 60)
    print("FINAL STATISTICS - ALL FILES")
    print("=" * 60)
    print(f"Total papers processed: {total_papers:,}")
    print(f"\n{'Field':<25} {'Before':>8} {'After':>8} {'Change':>8}")
    print("-" * 55)
    for f in fields_to_track:
        change = total_after[f] - total_before[f]
        sign = '+' if change >= 0 else ''
        print(f"{f:<25} {total_before[f]:>8,} {total_after[f]:>8,} {sign}{change:>7,}")
    
    print("\n" + "=" * 60)
    print("FEATURES IN THIS VERSION (v3.2)")
    print("=" * 60)
    print("1. GitHub Tools: Validates and deduplicates github_tools data")
    print("   Preserves stars, forks, health_score, language, topics, etc.")
    print("   Auto-populates github_url from tools if missing")
    print("2. Prior Scientific: Only matches specific company name variants")
    print("   Prevents 'prior to treatment' from being tagged as a brand")
    print("3. Institutions: Extracted ONLY from author affiliations")
    print("   ROR IDs looked up from institution names")
    
    print("\nDone!")


if __name__ == '__main__':
    main()
