#!/usr/bin/env python3
"""
MicroHub Paper Cleanup and Re-tagging Script v2 (FIXED)
Cleans up JSON data, extracts missing tags, and normalizes tag variants.

FIXES in this version:
- Removed simple 'prior' -> 'Prior' mapping that caused over-tagging
- Made Prior Scientific patterns more specific to avoid matching "prior to"
- Similar fixes for other ambiguous terms
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
    (r'https?://ror\.org/(0[a-z0-9]{6}\d{2})', 'url'),
    (r'\bror[:\s]+?(0[a-z0-9]{6}\d{2})\b', 'text'),
    (r'\bROR[:\s]+?(0[a-z0-9]{6}\d{2})\b', 'text'),
    (r'doi\.org/10\.(?:ror|ROR)/(0[a-z0-9]{6}\d{2})', 'doi'),
]

FACILITY_PATTERNS = [
    # Specific facility at institution patterns - requires full context
    (r'([A-Z][A-Za-z\s&]+(?:University|Institute|Medical Center|Hospital))\s+(?:Imaging|Microscopy|EM|Confocal|Light\s+Microscopy)\s+(?:Core|Facility|Center|Centre|Unit)', 'institution_facility'),
    # Named imaging facilities with full name
    (r'((?:[A-Z][a-z]+\s+){1,3}(?:Imaging|Microscopy|Bioimaging)\s+(?:Core|Facility|Center|Centre|Unit|Platform|Resource))\s+(?:at\s+)?(?:the\s+)?([A-Z][A-Za-z\s&]+(?:University|Institute|Center|Hospital))', 'named_at_institution'),
    # NIH intramural facilities
    (r'\b((?:NIH|NCI|NHLBI|NINDS|NICHD|NEI|NIAID|NIBIB)\s+(?:Intramural\s+)?[A-Za-z\s]+(?:Imaging|Microscopy)\s+(?:Core|Facility|Center))\b', 'nih'),
    # S10 grant funded facilities (often specific)
    (r'S10\s*(?:OD|RR)\d+[^.]*?(?:supported?\s+)?(?:the\s+)?([A-Z][A-Za-z\s]+(?:Imaging|Microscopy)\s+(?:Core|Facility|Center|System))', 's10'),
]

# Comprehensive list of known microscopy facilities with specific names
# Format: (search_pattern, canonical_name)
KNOWN_FACILITIES_DETAILED = [
    # HHMI / Janelia - be specific about the connection
    ('janelia research campus', 'HHMI Janelia Research Campus'),
    ('janelia farm', 'HHMI Janelia Research Campus'),
    ('hhmi janelia', 'HHMI Janelia Research Campus'),
    ('howard hughes medical institute janelia', 'HHMI Janelia Research Campus'),
    ('janelia advanced imaging center', 'Janelia Advanced Imaging Center'),
    
    # Max Planck Institutes - with locations
    ('max planck institute of neurobiology', 'Max Planck Institute of Neurobiology (Martinsried)'),
    ('max planck institute for neurobiology', 'Max Planck Institute of Neurobiology (Martinsried)'),
    ('mpi neurobiology', 'Max Planck Institute of Neurobiology (Martinsried)'),
    ('max planck institute for medical research', 'Max Planck Institute for Medical Research (Heidelberg)'),
    ('max planck institute of biochemistry', 'Max Planck Institute of Biochemistry (Martinsried)'),
    ('mpi biochemistry', 'Max Planck Institute of Biochemistry (Martinsried)'),
    ('max planck institute of molecular cell biology', 'Max Planck Institute of Molecular Cell Biology and Genetics (Dresden)'),
    ('mpi-cbg', 'Max Planck Institute of Molecular Cell Biology and Genetics (Dresden)'),
    ('max planck institute for biophysics', 'Max Planck Institute for Biophysics (Frankfurt)'),
    ('max planck institute of biophysical chemistry', 'Max Planck Institute for Multidisciplinary Sciences (Göttingen)'),
    ('mpi göttingen', 'Max Planck Institute for Multidisciplinary Sciences (Göttingen)'),
    ('max planck institute for brain research', 'Max Planck Institute for Brain Research (Frankfurt)'),
    ('max planck florida', 'Max Planck Florida Institute for Neuroscience'),
    
    # Allen Institute facilities
    ('allen institute for brain science', 'Allen Institute for Brain Science (Seattle)'),
    ('allen institute for cell science', 'Allen Institute for Cell Science (Seattle)'),
    ('allen cell explorer', 'Allen Institute for Cell Science (Seattle)'),
    
    # EMBL facilities with locations
    ('embl heidelberg', 'EMBL Heidelberg'),
    ('embl imaging centre', 'EMBL Imaging Centre (Heidelberg)'),
    ('embl grenoble', 'EMBL Grenoble'),
    ('embl rome', 'EMBL Rome'),
    ('embl barcelona', 'EMBL Barcelona'),
    ('embl ebi', 'EMBL-EBI (Hinxton)'),
    ('almf embl', 'EMBL Advanced Light Microscopy Facility'),
    
    # UK facilities
    ('mrc laboratory of molecular biology', 'MRC Laboratory of Molecular Biology (Cambridge)'),
    ('mrc lmb', 'MRC Laboratory of Molecular Biology (Cambridge)'),
    ('francis crick institute', 'Francis Crick Institute (London)'),
    ('crick institute', 'Francis Crick Institute (London)'),
    ('diamond light source', 'Diamond Light Source (Harwell)'),
    ('rosalind franklin institute', 'Rosalind Franklin Institute (Harwell)'),
    
    # Major US research institutes
    ('broad institute', 'Broad Institute (Cambridge)'),
    ('whitehead institute', 'Whitehead Institute (Cambridge)'),
    ('cold spring harbor laboratory', 'Cold Spring Harbor Laboratory'),
    ('cshl', 'Cold Spring Harbor Laboratory'),
    ('salk institute', 'Salk Institute for Biological Studies (La Jolla)'),
    ('scripps research', 'Scripps Research (La Jolla)'),
    ('stowers institute', 'Stowers Institute for Medical Research (Kansas City)'),
    ('van andel institute', 'Van Andel Institute (Grand Rapids)'),
    
    # University core facilities - specific names
    ('harvard center for biological imaging', 'Harvard Center for Biological Imaging'),
    ('hcbi harvard', 'Harvard Center for Biological Imaging'),
    ('nikon imaging center harvard', 'Nikon Imaging Center at Harvard Medical School'),
    ('stanford cell sciences imaging facility', 'Stanford Cell Sciences Imaging Facility'),
    ('stanford csif', 'Stanford Cell Sciences Imaging Facility'),
    ('mit koch institute', 'Koch Institute for Integrative Cancer Research (MIT)'),
    ('ucsf center for advanced light microscopy', 'UCSF Center for Advanced Light Microscopy'),
    ('ucsf nikon imaging center', 'UCSF Nikon Imaging Center'),
    ('yale west campus imaging core', 'Yale West Campus Imaging Core'),
    ('yale school of medicine imaging', 'Yale Center for Cellular and Molecular Imaging'),
    ('uc berkeley imaging facility', 'UC Berkeley Biological Imaging Facility'),
    ('princeton imaging core', 'Princeton Confocal/Light Microscopy Core'),
    ('caltech biological imaging center', 'Caltech Biological Imaging Facility'),
    ('columbia zuckerman institute imaging', 'Zuckerman Institute Cellular Imaging Platform (Columbia)'),
    ('rockefeller university imaging', 'Rockefeller University Bio-Imaging Resource Center'),
    ('nyu langone microscopy', 'NYU Langone Microscopy Laboratory'),
    ('ucla crump imaging', 'UCLA Crump Institute Preclinical Imaging'),
    ('ucla advanced light microscopy', 'UCLA Advanced Light Microscopy/Spectroscopy'),
    ('upenn cell and developmental biology imaging', 'UPenn CDB Imaging Core'),
    ('uchicago integrated light microscopy', 'UChicago Integrated Light Microscopy Core'),
    ('northwestern center for advanced microscopy', 'Northwestern Center for Advanced Microscopy'),
    ('washington university hope center', 'Washington University Hope Center Alafi Neuroimaging'),
    ('duke light microscopy core', 'Duke Light Microscopy Core Facility'),
    ('johns hopkins microscopy', 'Johns Hopkins Microscopy Facility'),
    ('mayo clinic microscopy', 'Mayo Clinic Microscopy and Cell Analysis Core'),
    
    # European facilities
    ('institut pasteur', 'Institut Pasteur (Paris)'),
    ('pasteur imaging', 'Institut Pasteur Photonic BioImaging'),
    ('imba vienna', 'IMBA Vienna BioOptics'),
    ('ist austria', 'IST Austria Imaging Facility'),
    ('biozentrum basel imaging', 'Biozentrum Imaging Core Facility (Basel)'),
    ('eth scopem', 'ETH ScopeM (Zurich)'),
    ('epfl bioimaging', 'EPFL BioImaging and Optics Platform'),
    ('epfl imaging', 'EPFL BioImaging and Optics Platform'),
    ('dkfz light microscopy', 'DKFZ Light Microscopy Facility (Heidelberg)'),
    ('karolinska imaging', 'Karolinska Institutet Live Cell Imaging'),
    ('leiden microscopy', 'Leiden University Medical Center Imaging'),
    ('vib bioimaging', 'VIB BioImaging Core (Leuven)'),
    ('hubrecht imaging', 'Hubrecht Imaging Centre (Utrecht)'),
    
    # Asian/Australian facilities  
    ('riken center for biosystems dynamics', 'RIKEN Center for Biosystems Dynamics Research'),
    ('riken bdr', 'RIKEN Center for Biosystems Dynamics Research'),
    ('national institute for basic biology', 'NIBB Imaging Facility (Okazaki)'),
    ('singapore bioimaging consortium', 'Singapore Bioimaging Consortium'),
    ('a*star microscopy', 'A*STAR Microscopy Platform'),
    ('monash micro imaging', 'Monash Micro Imaging'),
    ('wehi imaging', 'WEHI Centre for Dynamic Imaging'),
    
    # NIH intramural facilities
    ('nih intramural', 'NIH Intramural Research Program'),
    ('nci ccr', 'NCI Center for Cancer Research'),
    ('nhlbi light microscopy', 'NHLBI Light Microscopy Core'),
    ('ninds light imaging', 'NINDS Light Imaging Facility'),
    ('nichd microscopy', 'NICHD Microscopy and Imaging Core'),
]

# Simple list for backward compatibility - uses canonical names from above
KNOWN_FACILITIES = list(set([name for _, name in KNOWN_FACILITIES_DETAILED]))

# Phrases that indicate acknowledgments rather than where work was done
ACKNOWLEDGMENT_EXCLUSIONS = [
    r'\bwe\s+(?:thank|acknowledge|are\s+grateful\s+to)\s+',
    r'\bthanks?\s+(?:to|go\s+to)\s+',
    r'\backnowledge(?:s|d)?\s+',
    r'\bgrateful\s+to\s+',
    r'\bfunded\s+by\s+',
    r'\bsupported\s+by\s+a?\s*(?:grant|fellowship|award)\s+',
    r'\bdata\s+(?:was|were)\s+(?:collected|obtained|acquired)\s+by\s+',
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
    """Extract ROR (Research Organization Registry) IDs from text."""
    if not text:
        return []
    
    found = []
    seen = set()
    
    for pattern, source_type in ROR_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            ror_id = match.group(1)
            if ror_id and len(ror_id) == 9 and ror_id.startswith('0'):
                if ror_id not in seen:
                    seen.add(ror_id)
                    found.append({
                        'id': ror_id,
                        'url': f'https://ror.org/{ror_id}',
                        'source': source_type,
                    })
    
    return found


def extract_facilities(text: str) -> List[str]:
    """Extract imaging facility mentions from text with improved specificity.
    
    This version:
    - Uses detailed facility patterns with location info
    - Filters out acknowledgment phrases (we thank, funded by, etc.)
    - Matches known facilities with canonical names
    - Avoids generic/vague facility mentions
    """
    if not text:
        return []
    
    found = []
    seen = set()
    text_lower = text.lower()
    
    # Check if the text appears to be primarily acknowledgments
    # If facility mention is in an acknowledgment context, be more careful
    def is_acknowledgment_context(text_segment: str) -> bool:
        """Check if text segment is in an acknowledgment context."""
        segment_lower = text_segment.lower()
        for pattern in ACKNOWLEDGMENT_EXCLUSIONS:
            if re.search(pattern, segment_lower):
                return True
        return False
    
    # First pass: Look for known facilities with detailed patterns
    for search_pattern, canonical_name in KNOWN_FACILITIES_DETAILED:
        if search_pattern in text_lower:
            # Find the position and check surrounding context
            pos = text_lower.find(search_pattern)
            # Get context (100 chars before the match)
            start_context = max(0, pos - 100)
            context = text_lower[start_context:pos + len(search_pattern) + 50]
            
            # Skip if this appears to be in an acknowledgment context
            if is_acknowledgment_context(context):
                # Only skip for generic mentions, still include if it says "performed at" etc.
                if not re.search(r'(?:performed|conducted|acquired|imaged|collected)\s+(?:at|in|using)', context):
                    continue
            
            canonical_lower = canonical_name.lower()
            if canonical_lower not in seen:
                seen.add(canonical_lower)
                found.append(canonical_name)
    
    # Second pass: Use regex patterns for facilities not in known list
    for pattern, pattern_type in FACILITY_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Get the full match and any captured groups
            if match.groups():
                if len(match.groups()) >= 2:
                    # Pattern captured facility name and institution separately
                    facility_name = match.group(1).strip()
                    institution = match.group(2).strip() if match.group(2) else ''
                    facility = f"{facility_name} ({institution})" if institution else facility_name
                else:
                    facility = match.group(1).strip()
            else:
                facility = match.group(0).strip()
            
            facility = re.sub(r'\s+', ' ', facility)
            facility = facility.strip(' ,.')
            
            # Skip short/generic matches
            if len(facility) < 20:
                continue
            
            # Check context for acknowledgment phrases
            match_start = match.start()
            context_start = max(0, match_start - 100)
            context = text[context_start:match_start + len(match.group(0)) + 20]
            
            if is_acknowledgment_context(context):
                # Check if it's describing where work was done vs thanking
                if not re.search(r'(?:performed|conducted|acquired|imaged|collected|carried\s+out)\s+(?:at|in|using)', context.lower()):
                    continue
            
            # Skip overly generic terms
            generic_terms = [
                'the imaging', 'imaging core', 'microscopy core', 'imaging facility',
                'the facility', 'core facility', 'light microscopy', 'electron microscopy',
                'confocal microscopy', 'imaging center', 'microscopy facility',
                'advanced imaging', 'bioimaging core', 'imaging platform'
            ]
            facility_lower = facility.lower()
            if any(facility_lower == term or facility_lower == f"the {term}" for term in generic_terms):
                continue
            
            # Skip if starts with acknowledgment-related words
            skip_starts = ['thank', 'acknowledge', 'grateful', 'supported', 'funded', 'provided']
            if any(facility_lower.startswith(word) for word in skip_starts):
                continue
            
            if facility_lower not in seen:
                seen.add(facility_lower)
                found.append(facility)
    
    # Deduplicate: prefer more specific names over generic ones
    final_facilities = []
    for fac in found:
        fac_lower = fac.lower()
        
        # Skip if this is a substring of an already-found facility
        is_substring = False
        for existing in final_facilities:
            existing_lower = existing.lower()
            # If current facility name is contained within an existing one, skip it
            if fac_lower in existing_lower and fac_lower != existing_lower:
                is_substring = True
                break
        
        if is_substring:
            continue
        
        # Remove any existing facilities that are substrings of this one
        final_facilities = [
            existing for existing in final_facilities
            if existing.lower() not in fac_lower or existing.lower() == fac_lower
        ]
        final_facilities.append(fac)
    
    return final_facilities


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


def clean_paper(paper: Dict) -> Dict:
    """Clean and re-tag a single paper."""
    
    full_text = str(paper.get('full_text', '') or '')
    
    garbage_patterns = [
        r'^Technique\s+Microscope\s+Organism\s+Software\s*',
        r'^pmc-status-\S+\s*',
        r'^pmc-prop-\S+\s*',
        r'pmc-status-\w+\s+\w+\s+pmc-',
        r'pmc-license-\S+\s*',
    ]
    for pattern in garbage_patterns:
        full_text = re.sub(pattern, '', full_text, flags=re.IGNORECASE | re.MULTILINE)
    
    paper['full_text'] = full_text.strip()
    
    for field in ['abstract', 'methods']:
        text = str(paper.get(field, '') or '')
        for pattern in garbage_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        paper[field] = text.strip()
    
    text_parts = [
        str(paper.get('title', '') or ''),
        str(paper.get('abstract', '') or ''),
        str(paper.get('methods', '') or ''),
        str(paper.get('full_text', '') or ''),
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
    
    acknowledgments = str(paper.get('acknowledgments', '') or '')
    facilities_text = f"{combined_text} {acknowledgments}"
    new_facilities = extract_facilities(facilities_text)
    existing_facility = paper.get('facility') or paper.get('imaging_facility') or ''
    
    if new_facilities:
        if not existing_facility:
            paper['facility'] = new_facilities[0]
            paper['imaging_facility'] = new_facilities[0]
        paper['facilities'] = new_facilities
    elif existing_facility:
        paper['facilities'] = [existing_facility]
    
    if paper.get('rors'):
        paper['rors'] = [
            r for r in paper['rors']
            if isinstance(r, dict) and str(r.get('id', '')).startswith('0')
        ]
    
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
    
    paper['has_full_text'] = bool(paper.get('full_text') and len(str(paper.get('full_text', ''))) > 100)
    paper['has_protocols'] = bool(paper.get('protocols')) or paper.get('is_protocol', False)
    paper['has_github'] = bool(paper.get('github_url'))
    paper['has_data'] = bool(paper.get('repositories'))
    paper['has_rrids'] = bool(paper.get('rrids'))
    paper['has_rors'] = bool(paper.get('rors'))
    paper['has_fluorophores'] = bool(paper.get('fluorophores'))
    paper['has_cell_lines'] = bool(paper.get('cell_lines'))
    paper['has_sample_prep'] = bool(paper.get('sample_preparation'))
    paper['has_methods'] = bool(paper.get('methods') and len(str(paper.get('methods', ''))) > 100)
    paper['has_facility'] = bool(paper.get('facility') or paper.get('facilities'))
    
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
        'protocols', 'repositories', 'rrids', 'rors', 'antibodies', 'facilities', 'is_protocol'
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
    
    parser = argparse.ArgumentParser(description='Clean and re-tag MicroHub JSON files with normalization')
    parser.add_argument('--input', '-i', help='Input JSON file (default: all chunk files)')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--pattern', default='microhub_papers_v*_chunk_*.json',
                        help='Glob pattern to find JSON files')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite input files instead of creating new ones')
    parser.add_argument('--output-dir', default='cleaned_export',
                        help='Output directory for cleaned files')
    
    args = parser.parse_args()
    
    if args.input:
        input_files = [args.input]
    else:
        input_files = sorted(glob.glob(args.pattern))
        if not input_files:
            input_files = sorted(glob.glob('*_chunk_*.json'))
        if not input_files:
            input_files = sorted(glob.glob('microhub*.json'))
    
    if not input_files:
        print("No JSON files found! Use --input to specify a file or --pattern for a glob pattern.")
        sys.exit(1)
    
    print("=" * 60)
    print("MICROHUB CLEANUP AND RE-TAGGING v2 (FIXED)")
    print("With tag normalization and Prior Scientific fix")
    print("=" * 60)
    print(f"Found {len(input_files)} JSON file(s)")
    
    if not args.overwrite:
        os.makedirs(args.output_dir, exist_ok=True)
        print(f"Output directory: {args.output_dir}")
    else:
        print("Mode: Overwriting input files")
    
    fields_to_track = [
        'microscopy_techniques', 'microscope_brands', 'image_analysis_software',
        'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
        'protocols', 'repositories', 'rrids', 'rors', 'antibodies', 'facilities', 'is_protocol'
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
    print("FIXES IN THIS VERSION")
    print("=" * 60)
    print("1. Prior Scientific: Removed simple 'prior' -> 'Prior' mapping")
    print("   Now only matches 'Prior Scientific', 'Prior stage', etc.")
    print("   Prevents 'prior to treatment' from being tagged as a brand")
    
    print("\nDone!")


if __name__ == '__main__':
    main()
