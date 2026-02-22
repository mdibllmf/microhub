#!/usr/bin/env python3
"""
build_microscope_kb.py — Compile a structured microscopy equipment knowledge base.

Creates a JSON lookup database mapping microscope models → associated metadata
(brand, software, techniques, laser lines, detectors, objectives, etc.).

This fills a gap: no public structured database of microscope hardware exists.
The closest community effort (Micro-Meta App / 4DN-BINA-OME) documents
individual lab instruments but provides no comprehensive product catalog.

The resulting microscope_kb.json enables the MicroHub pipeline to:
  1. Infer missing tags (e.g., paper mentions "LSM 880" → tag "ZEN" software)
  2. Validate equipment co-occurrence (Zeiss software on Nikon scope = suspicious)
  3. Link model families to techniques (Elyra → SIM/PALM/STORM)

Data sources:
  - Manufacturer product pages (Zeiss, Leica, Nikon, Olympus/Evident)
  - Published microscopy metadata standards (4DN-BINA-OME)
  - Community knowledge (image.sc, BINA working groups)

Output: microscope_kb/microscope_kb.json
        microscope_kb/brand_software_map.json
        microscope_kb/model_aliases.json

Usage:
    python build_microscope_kb.py                  # build all files
    python build_microscope_kb.py --output-dir .   # custom output directory
    python build_microscope_kb.py --validate       # validate against MASTER_TAG_DICTIONARY
"""

import argparse
import json
import os
import sys
from datetime import date
from typing import Any, Dict, List, Optional


# =====================================================================
# CORE KNOWLEDGE BASE — Microscope Systems
# =====================================================================
# Each entry maps a model identifier to its full metadata.
# Fields:
#   brand:          Canonical manufacturer name
#   model:          Full model name (display string)
#   aliases:        Text patterns that refer to this system
#   category:       confocal | widefield | super_resolution | light_sheet |
#                   spinning_disk | multiphoton | electron | mesoscope | other
#   software:       List of associated acquisition/analysis software
#   techniques:     List of microscopy techniques this system supports
#   laser_lines:    Common laser wavelengths (nm) available/compatible
#   detectors:      Detector types/models typically used
#   objectives:     Notable objective series compatible
#   discontinued:   True if no longer manufactured
#   successor:      Model that replaced this one (if discontinued)
#   notes:          Free-text notes
# =====================================================================

MICROSCOPE_SYSTEMS: List[Dict[str, Any]] = [

    # ==================================================================
    # ZEISS — Confocal
    # ==================================================================
    {
        "brand": "Zeiss",
        "model": "LSM 980",
        "aliases": ["LSM980", "LSM 980", "Zeiss 980"],
        "category": "confocal",
        "software": ["ZEN", "ZEN Blue"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Airyscan Microscopy",
            "Fluorescence Microscopy", "Live Cell Imaging",
            "Fluorescence Lifetime Imaging Microscopy",
            "Fluorescence Recovery After Photobleaching",
            "Fluorescence Correlation Spectroscopy",
            "Förster Resonance Energy Transfer"
        ],
        "laser_lines": [405, 445, 488, 514, 561, 594, 633, 639, 730],
        "detectors": ["Airyscan 2", "GaAsP-PMT", "MA-PMT"],
        "objectives": ["Plan-Apochromat", "C-Apochromat", "LD LCI Plan-Apochromat"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Flagship confocal with Airyscan 2 multiplex for 4x/8x faster super-res"
    },
    {
        "brand": "Zeiss",
        "model": "LSM 900",
        "aliases": ["LSM900", "LSM 900", "Zeiss 900"],
        "category": "confocal",
        "software": ["ZEN", "ZEN Blue"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Airyscan Microscopy",
            "Fluorescence Microscopy", "Live Cell Imaging"
        ],
        "laser_lines": [405, 445, 488, 514, 561, 594, 633],
        "detectors": ["Airyscan 2", "GaAsP-PMT"],
        "objectives": ["Plan-Apochromat", "C-Apochromat"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Compact confocal with Airyscan 2, smaller footprint than LSM 980"
    },
    {
        "brand": "Zeiss",
        "model": "LSM 880",
        "aliases": ["LSM880", "LSM 880", "Zeiss 880"],
        "category": "confocal",
        "software": ["ZEN", "ZEN Black", "ZEN Blue"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Airyscan Microscopy",
            "Fluorescence Microscopy", "Live Cell Imaging",
            "Fluorescence Lifetime Imaging Microscopy",
            "Fluorescence Correlation Spectroscopy",
            "Förster Resonance Energy Transfer",
            "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 445, 458, 488, 514, 543, 561, 594, 633, 730],
        "detectors": ["Airyscan", "GaAsP-PMT", "BiG.2", "QUASAR"],
        "objectives": ["Plan-Apochromat", "C-Apochromat", "LD C-Apochromat"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "LSM 980",
        "notes": "First Airyscan system; NLO option for multiphoton"
    },
    {
        "brand": "Zeiss",
        "model": "LSM 800",
        "aliases": ["LSM800", "LSM 800", "Zeiss 800"],
        "category": "confocal",
        "software": ["ZEN", "ZEN Blue"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Airyscan Microscopy",
            "Fluorescence Microscopy"
        ],
        "laser_lines": [405, 488, 561, 640],
        "detectors": ["Airyscan", "GaAsP-PMT"],
        "objectives": ["Plan-Apochromat"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "LSM 900",
        "notes": "Entry-level confocal with Airyscan"
    },
    {
        "brand": "Zeiss",
        "model": "LSM 780",
        "aliases": ["LSM780", "LSM 780", "Zeiss 780"],
        "category": "confocal",
        "software": ["ZEN", "ZEN Black"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Fluorescence Lifetime Imaging Microscopy",
            "Fluorescence Correlation Spectroscopy",
            "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 445, 458, 488, 514, 543, 561, 594, 633],
        "detectors": ["GaAsP-PMT", "QUASAR", "BiG"],
        "objectives": ["Plan-Apochromat", "C-Apochromat"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "LSM 880",
        "notes": "QUASAR 34-channel spectral detector; NLO multiphoton option"
    },
    {
        "brand": "Zeiss",
        "model": "LSM 710",
        "aliases": ["LSM710", "LSM 710", "Zeiss 710"],
        "category": "confocal",
        "software": ["ZEN", "ZEN Black"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Fluorescence Correlation Spectroscopy"
        ],
        "laser_lines": [405, 445, 458, 488, 514, 543, 561, 594, 633],
        "detectors": ["PMT", "spectral detector"],
        "objectives": ["Plan-Apochromat", "EC Plan-Neofluar"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "LSM 780",
        "notes": "Spectral detection introduced in this generation"
    },
    {
        "brand": "Zeiss",
        "model": "LSM 700",
        "aliases": ["LSM700", "LSM 700", "Zeiss 700"],
        "category": "confocal",
        "software": ["ZEN", "ZEN Black"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy"
        ],
        "laser_lines": [405, 488, 555, 639],
        "detectors": ["PMT"],
        "objectives": ["Plan-Apochromat", "EC Plan-Neofluar"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "LSM 800",
        "notes": "Solid-state laser-only compact confocal"
    },
    {
        "brand": "Zeiss",
        "model": "LSM 510",
        "aliases": ["LSM510", "LSM 510", "LSM 510 META", "Zeiss 510"],
        "category": "confocal",
        "software": ["LSM Image Browser", "ZEN"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Multiphoton Microscopy"
        ],
        "laser_lines": [351, 364, 405, 458, 477, 488, 514, 543, 561, 633],
        "detectors": ["PMT", "META detector"],
        "objectives": ["Plan-Apochromat", "Plan-Neofluar"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "LSM 710",
        "notes": "Long-lived workhorse; META variant had spectral detector"
    },

    # ==================================================================
    # ZEISS — Super-Resolution
    # ==================================================================
    {
        "brand": "Zeiss",
        "model": "Elyra 7",
        "aliases": ["Elyra 7", "Elyra7", "Zeiss Elyra 7"],
        "category": "super_resolution",
        "software": ["ZEN", "ZEN Black"],
        "techniques": [
            "Structured Illumination Microscopy",
            "Photoactivated Localization Microscopy",
            "Single-Molecule Localization Microscopy",
            "Super-Resolution Microscopy",
            "Total Internal Reflection Fluorescence Microscopy",
            "Lattice Light Sheet Microscopy"
        ],
        "laser_lines": [405, 488, 561, 642],
        "detectors": ["sCMOS", "EMCCD", "sCMOS PCO.edge"],
        "objectives": ["Plan-Apochromat 63x/1.4", "alpha Plan-Apochromat 100x/1.46"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Lattice SIM with optical sectioning; combines SIM + SMLM + TIRF"
    },
    {
        "brand": "Zeiss",
        "model": "Elyra",
        "aliases": ["Elyra PS.1", "Elyra S.1", "Zeiss Elyra"],
        "category": "super_resolution",
        "software": ["ZEN", "ZEN Black"],
        "techniques": [
            "Structured Illumination Microscopy",
            "Photoactivated Localization Microscopy",
            "Single-Molecule Localization Microscopy",
            "Super-Resolution Microscopy",
            "Total Internal Reflection Fluorescence Microscopy"
        ],
        "laser_lines": [405, 488, 561, 642],
        "detectors": ["EMCCD", "sCMOS"],
        "objectives": ["Plan-Apochromat 63x/1.4", "alpha Plan-Apochromat 100x/1.46"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Elyra 7",
        "notes": "First-gen SIM/PALM/STORM platform"
    },

    # ==================================================================
    # ZEISS — Light Sheet
    # ==================================================================
    {
        "brand": "Zeiss",
        "model": "Lightsheet 7",
        "aliases": ["Lightsheet 7", "Lightsheet7", "Zeiss Lightsheet 7", "LS7"],
        "category": "light_sheet",
        "software": ["ZEN", "ZEN Blue"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy", "Live Cell Imaging",
            "3D Imaging", "4D Imaging"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 638],
        "detectors": ["sCMOS (dual)"],
        "objectives": ["Detection: 5x, 20x, 50x; Illumination: 5x, 10x"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Tilt illumination with pivot scanning"
    },
    {
        "brand": "Zeiss",
        "model": "Lightsheet Z.1",
        "aliases": ["Lightsheet Z.1", "Z.1", "Zeiss Z.1", "LSFM Z.1"],
        "category": "light_sheet",
        "software": ["ZEN", "ZEN Black"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy", "Live Cell Imaging",
            "3D Imaging", "4D Imaging"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 638],
        "detectors": ["sCMOS (dual)", "PCO.edge"],
        "objectives": ["W Plan-Apochromat 20x/1.0"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Lightsheet 7",
        "notes": "First commercial dual-illumination light sheet"
    },

    # ==================================================================
    # ZEISS — Widefield Platforms
    # ==================================================================
    {
        "brand": "Zeiss",
        "model": "Celldiscoverer 7",
        "aliases": ["Celldiscoverer 7", "CD7", "Zeiss CD7"],
        "category": "widefield",
        "software": ["ZEN", "ZEN Blue"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Live Cell Imaging",
            "Phase Contrast Microscopy", "High-Content Screening",
            "Spinning Disk Confocal Microscopy"
        ],
        "laser_lines": [385, 420, 470, 505, 530, 567, 590, 625, 735],
        "detectors": ["Axiocam 712 mono", "Axiocam 305 color"],
        "objectives": ["Plan-Apochromat 5x-50x autocorr"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Automated box microscope; optional LSM 900 or spinning disk add-on"
    },
    {
        "brand": "Zeiss",
        "model": "Axio Observer",
        "aliases": ["Axio Observer", "Axio Observer 7", "AxioObserver",
                    "Axio Observer.Z1", "Observer Z1", "Observer 7"],
        "category": "widefield",
        "software": ["ZEN", "ZEN Blue", "ZEN Pro"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy",
            "Live Cell Imaging"
        ],
        "laser_lines": [],
        "detectors": ["Axiocam series", "various sCMOS"],
        "objectives": ["Plan-Apochromat", "Plan-Neofluar", "EC Plan-Neofluar"],
        "filter_sets": ["DAPI", "GFP", "Cy3", "Cy5", "Filter Set 49", "Filter Set 38 HE", "Filter Set 43 HE"],
        "discontinued": False,
        "successor": None,
        "notes": "Inverted research microscope platform; base for LSM and spinning disk"
    },
    {
        "brand": "Zeiss",
        "model": "Axio Imager",
        "aliases": ["Axio Imager", "Axio Imager.Z2", "Axio Imager.M2", "AxioImager"],
        "category": "widefield",
        "software": ["ZEN", "ZEN Blue", "ZEN Pro"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Brightfield Microscopy", "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy",
            "Polarization Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["Axiocam series"],
        "objectives": ["Plan-Apochromat", "EC Plan-Neofluar", "N-Achroplan"],
        "filter_sets": ["Filter Set 49", "Filter Set 38 HE", "Filter Set 43 HE", "Filter Set 50"],
        "discontinued": False,
        "successor": None,
        "notes": "Upright research microscope for pathology, neuroscience, materials"
    },
    {
        "brand": "Zeiss",
        "model": "Axiovert",
        "aliases": ["Axiovert 200", "Axiovert 200M", "Axiovert 135", "Axiovert 100"],
        "category": "widefield",
        "software": ["AxioVision", "ZEN"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy", "Live Cell Imaging"
        ],
        "laser_lines": [],
        "detectors": ["AxioCam series"],
        "objectives": ["Plan-Neofluar", "Plan-Apochromat"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Axio Observer",
        "notes": "Legacy inverted platform; widely referenced in older literature"
    },
    {
        "brand": "Zeiss",
        "model": "Axioskop",
        "aliases": ["Axioskop", "Axioskop 2", "Axioskop 40"],
        "category": "widefield",
        "software": ["AxioVision", "ZEN"],
        "techniques": [
            "Brightfield Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["AxioCam series"],
        "objectives": ["Plan-Neofluar", "Achroplan"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Axio Imager",
        "notes": "Legacy upright; very common in older papers"
    },

    # ==================================================================
    # LEICA — Confocal
    # ==================================================================
    {
        "brand": "Leica",
        "model": "Stellaris",
        "aliases": ["STELLARIS", "Stellaris 5", "Stellaris 8", "Leica Stellaris",
                    "STELLARIS 5", "STELLARIS 8"],
        "category": "confocal",
        "software": ["Leica Application Suite X", "LAS X"],
        "techniques": [
            "Confocal Laser Scanning Microscopy",
            "Fluorescence Lifetime Imaging Microscopy",
            "Fluorescence Microscopy", "Live Cell Imaging",
            "Fluorescence Correlation Spectroscopy",
            "Stimulated Emission Depletion Microscopy",
            "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 440, 470, 488, 514, 543, 561, 594, 633, 730],
        "detectors": ["HyD S", "HyD R", "HyD X", "Power HyD"],
        "objectives": ["HC PL APO", "HC PL FLUOTAR"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Current flagship; White Light Laser (WLL) for tunable excitation 440-790nm; FLIM built-in"
    },
    {
        "brand": "Leica",
        "model": "SP8",
        "aliases": ["SP8", "TCS SP8", "Leica SP8", "SP8 STED", "SP8 FALCON",
                    "SP8 DIVE", "SP8 LIGHTNING", "TCS SP8 STED 3X",
                    "SP8 MP", "SP8 DLS"],
        "category": "confocal",
        "software": ["Leica Application Suite X", "LAS X"],
        "techniques": [
            "Confocal Laser Scanning Microscopy",
            "Fluorescence Microscopy", "Live Cell Imaging",
            "Stimulated Emission Depletion Microscopy",
            "Fluorescence Lifetime Imaging Microscopy",
            "Multiphoton Microscopy",
            "Fluorescence Correlation Spectroscopy",
            "Digital Light Sheet Microscopy"
        ],
        "laser_lines": [405, 458, 476, 488, 496, 514, 543, 561, 594, 633],
        "detectors": ["HyD", "HyD SMD", "PMT"],
        "objectives": ["HC PL APO", "HC PL FLUOTAR", "HC FLUOTAR L"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Stellaris",
        "notes": "Modular platform with many variants: STED 3X, FALCON (FLIM), DIVE (multiphoton), LIGHTNING (decon)"
    },
    {
        "brand": "Leica",
        "model": "SP5",
        "aliases": ["SP5", "TCS SP5", "Leica SP5", "SP5 II", "SP5 MP", "SP5 STED"],
        "category": "confocal",
        "software": ["Leica Application Suite", "LAS AF"],
        "techniques": [
            "Confocal Laser Scanning Microscopy",
            "Fluorescence Microscopy",
            "Multiphoton Microscopy",
            "Stimulated Emission Depletion Microscopy"
        ],
        "laser_lines": [405, 458, 476, 488, 496, 514, 543, 561, 594, 633],
        "detectors": ["HyD", "PMT"],
        "objectives": ["HCX PL APO", "HCX PL FLUOTAR"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "SP8",
        "notes": "Introduced HyD detectors; widely deployed, huge install base"
    },

    # ==================================================================
    # LEICA — Super-Resolution
    # ==================================================================
    {
        "brand": "Leica",
        "model": "STED 3X",
        "aliases": ["STED 3X", "TCS SP8 STED 3X", "Leica STED", "Leica STED 3X"],
        "category": "super_resolution",
        "software": ["Leica Application Suite X", "LAS X"],
        "techniques": [
            "Stimulated Emission Depletion Microscopy",
            "Super-Resolution Microscopy",
            "Confocal Laser Scanning Microscopy"
        ],
        "laser_lines": [405, 488, 561, 633, 592, 660, 775],
        "detectors": ["HyD SMD", "HyD"],
        "objectives": ["HC PL APO 100x/1.40 OIL STED WHITE"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Stellaris",
        "notes": "3D STED with depletion lasers at 592, 660 and 775nm"
    },
    {
        "brand": "Leica",
        "model": "THUNDER",
        "aliases": ["THUNDER", "THUNDER Imager", "Leica THUNDER"],
        "category": "widefield",
        "software": ["Leica Application Suite X", "LAS X"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Deconvolution Microscopy",
            "Live Cell Imaging", "3D Imaging"
        ],
        "laser_lines": [],
        "detectors": ["Leica DFC9000 GTC", "K8"],
        "objectives": ["HC PL APO", "HC PL FLUOTAR"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Computational clearing (instant deconvolution) for widefield"
    },

    # ==================================================================
    # LEICA — Widefield Platforms
    # ==================================================================
    {
        "brand": "Leica",
        "model": "DMi8",
        "aliases": ["DMi8", "DM i8", "Leica DMi8"],
        "category": "widefield",
        "software": ["Leica Application Suite X", "LAS X"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy",
            "Live Cell Imaging", "Total Internal Reflection Fluorescence Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["Leica DFC series", "Hamamatsu ORCA"],
        "objectives": ["HC PL APO", "HC PL FLUOTAR", "HC PL FL L"],
        "filter_sets": ["A4", "L5", "N3", "Y5", "CY5", "TX2"],
        "discontinued": False,
        "successor": None,
        "notes": "Inverted platform; base for SP8/Stellaris, STED, TIRF"
    },
    {
        "brand": "Leica",
        "model": "DM6",
        "aliases": ["DM6", "DM6 B", "DM6 FS", "DM6 M", "Leica DM6"],
        "category": "widefield",
        "software": ["Leica Application Suite X", "LAS X"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Brightfield Microscopy", "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["Leica DFC series"],
        "objectives": ["HC PL APO", "HI PLAN"],
        "filter_sets": ["A4", "L5", "N3", "Y5"],
        "discontinued": False,
        "successor": None,
        "notes": "Upright automated research microscope"
    },

    # ==================================================================
    # NIKON — Confocal
    # ==================================================================
    {
        "brand": "Nikon",
        "model": "AX",
        "aliases": ["AX", "AX R", "AXR", "Nikon AX", "Nikon AXR", "AX R with NSPARC"],
        "category": "confocal",
        "software": ["NIS-Elements", "NIS-Elements C"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Live Cell Imaging", "Super-Resolution Microscopy",
            "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 445, 488, 514, 561, 594, 640],
        "detectors": ["NSPARC (multi-element)", "GaAsP-PMT", "PMT"],
        "objectives": ["CFI Plan Apochromat Lambda D", "CFI Apochromat LWD Lambda S"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Current flagship with 8K resonant scanning; NSPARC for super-res"
    },
    {
        "brand": "Nikon",
        "model": "A1",
        "aliases": ["A1", "A1R", "A1 HD25", "A1R HD25", "Nikon A1",
                    "Nikon A1R", "A1R+", "A1 MP+", "C2+"],
        "category": "confocal",
        "software": ["NIS-Elements", "NIS-Elements C"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Live Cell Imaging", "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 445, 488, 514, 561, 594, 640],
        "detectors": ["GaAsP-PMT", "PMT", "spectral detector"],
        "objectives": ["CFI Plan Apochromat Lambda", "CFI Plan Fluor"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "AX",
        "notes": "R variant has resonant scanner for fast imaging"
    },
    {
        "brand": "Nikon",
        "model": "C2+",
        "aliases": ["C2", "C2+", "C2si", "Nikon C2"],
        "category": "confocal",
        "software": ["NIS-Elements", "NIS-Elements C"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy"
        ],
        "laser_lines": [405, 488, 561, 640],
        "detectors": ["PMT"],
        "objectives": ["CFI Plan Apochromat Lambda", "CFI Plan Fluor"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "AX",
        "notes": "Entry-level confocal; C2si variant has spectral imaging"
    },

    # ==================================================================
    # NIKON — Super-Resolution
    # ==================================================================
    {
        "brand": "Nikon",
        "model": "N-SIM",
        "aliases": ["N-SIM", "N-SIM S", "N-SIM E", "NSIM", "Nikon SIM",
                    "Nikon N-SIM"],
        "category": "super_resolution",
        "software": ["NIS-Elements", "NIS-Elements AR"],
        "techniques": [
            "Structured Illumination Microscopy", "Super-Resolution Microscopy",
            "Total Internal Reflection Fluorescence Microscopy",
            "Live Cell Imaging"
        ],
        "laser_lines": [405, 488, 561, 640],
        "detectors": ["EMCCD", "sCMOS"],
        "objectives": ["CFI SR HP Apochromat TIRF 100x", "CFI Apochromat TIRF 60x"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "N-SIM S has high-speed SIM; combines with STORM"
    },
    {
        "brand": "Nikon",
        "model": "N-STORM",
        "aliases": ["N-STORM", "NSTORM", "Nikon STORM", "Nikon N-STORM"],
        "category": "super_resolution",
        "software": ["NIS-Elements", "NIS-Elements AR"],
        "techniques": [
            "Stochastic Optical Reconstruction Microscopy",
            "Direct Stochastic Optical Reconstruction Microscopy",
            "Single-Molecule Localization Microscopy",
            "Super-Resolution Microscopy",
            "Total Internal Reflection Fluorescence Microscopy"
        ],
        "laser_lines": [405, 488, 561, 647],
        "detectors": ["EMCCD", "sCMOS"],
        "objectives": ["CFI SR HP Apochromat TIRF 100x"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Combines with N-SIM for multimodal super-res"
    },

    # ==================================================================
    # NIKON — Widefield Platforms
    # ==================================================================
    {
        "brand": "Nikon",
        "model": "Ti2",
        "aliases": ["Ti2", "Ti2-E", "Ti2-A", "Ti2-U", "Eclipse Ti2",
                    "Nikon Ti2"],
        "category": "widefield",
        "software": ["NIS-Elements"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy",
            "Live Cell Imaging",
            "Total Internal Reflection Fluorescence Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["Nikon DS-Qi2", "various sCMOS/EMCCD"],
        "objectives": ["CFI Plan Apochromat Lambda D", "CFI Plan Fluor"],
        "filter_sets": ["DAPI-5060C", "FITC-5050A", "TRITC-5040C", "Cy5-4040C"],
        "discontinued": False,
        "successor": None,
        "notes": "25mm FOV inverted platform; base for A1/AX, N-SIM, N-STORM, CSU spinning disk"
    },
    {
        "brand": "Nikon",
        "model": "Ti",
        "aliases": ["Ti", "Ti-E", "Ti-S", "Ti-U", "Eclipse Ti", "Nikon Ti"],
        "category": "widefield",
        "software": ["NIS-Elements"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy",
            "Live Cell Imaging"
        ],
        "laser_lines": [],
        "detectors": ["various CCD/sCMOS"],
        "objectives": ["CFI Plan Apochromat Lambda", "CFI Plan Fluor"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Ti2",
        "notes": "Hugely popular inverted platform; Ti-E = fully motorized"
    },

    # ==================================================================
    # OLYMPUS / EVIDENT — Confocal
    # ==================================================================
    {
        "brand": "Olympus",
        "model": "FV3000",
        "aliases": ["FV3000", "FV3000RS", "FLUOVIEW FV3000",
                    "Olympus FV3000", "Evident FV3000"],
        "category": "confocal",
        "software": ["FluoView", "cellSens"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Live Cell Imaging", "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 594, 640],
        "detectors": ["SilVIR (high-sensitivity GaAsP)", "PMT"],
        "objectives": ["UPLSAPO", "UPLXAPO", "UCPLFLN"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "RS variant has resonant+galvano dual scanner; TruSpectral detection"
    },
    {
        "brand": "Olympus",
        "model": "FV1200",
        "aliases": ["FV1200", "FV1200MPE", "FLUOVIEW FV1200",
                    "Olympus FV1200"],
        "category": "confocal",
        "software": ["FluoView"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 440, 458, 488, 515, 543, 559, 635],
        "detectors": ["GaAsP-PMT", "PMT"],
        "objectives": ["UPLSAPO", "UPLFL"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "FV3000",
        "notes": "SIM scanner for simultaneous stimulation/imaging"
    },
    {
        "brand": "Olympus",
        "model": "FV1000",
        "aliases": ["FV1000", "FV1000MPE", "FLUOVIEW FV1000",
                    "Olympus FV1000"],
        "category": "confocal",
        "software": ["FluoView"],
        "techniques": [
            "Confocal Laser Scanning Microscopy", "Fluorescence Microscopy",
            "Multiphoton Microscopy"
        ],
        "laser_lines": [405, 440, 458, 488, 515, 543, 559, 635],
        "detectors": ["PMT", "spectral detector"],
        "objectives": ["UPLSAPO", "PLAPON", "UPLFL"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "FV1200",
        "notes": "Enormous install base; still widely referenced"
    },

    # ==================================================================
    # OLYMPUS / EVIDENT — Widefield
    # ==================================================================
    {
        "brand": "Olympus",
        "model": "IX83",
        "aliases": ["IX83", "Olympus IX83", "Evident IX83"],
        "category": "widefield",
        "software": ["cellSens", "MetaMorph", "MicroManager"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy",
            "Live Cell Imaging",
            "Total Internal Reflection Fluorescence Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["Hamamatsu ORCA-Flash", "Andor cameras"],
        "objectives": ["UPLSAPO", "UPLXAPO", "UCPLFLN", "PLAPON"],
        "filter_sets": ["U-FGFP", "U-FMCHE", "U-FUW", "U-FBNA", "U-FBW"],
        "discontinued": False,
        "successor": None,
        "notes": "Fully motorized inverted; base for confocal, spinning disk, TIRF"
    },
    {
        "brand": "Olympus",
        "model": "IX73",
        "aliases": ["IX73", "Olympus IX73"],
        "category": "widefield",
        "software": ["cellSens", "MetaMorph", "MicroManager"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Epifluorescence Microscopy",
            "Phase Contrast Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["various CCD/sCMOS"],
        "objectives": ["UPLSAPO", "UCPLFLN", "PLAPON"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Semi-motorized inverted; more affordable than IX83"
    },
    {
        "brand": "Olympus",
        "model": "BX63",
        "aliases": ["BX63", "Olympus BX63", "BX63F"],
        "category": "widefield",
        "software": ["cellSens"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Brightfield Microscopy",
            "Phase Contrast Microscopy",
            "Differential Interference Contrast Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["DP74", "DP80"],
        "objectives": ["UPLSAPO", "UPLFL", "PlanC N"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Motorized upright for histology and fluorescence"
    },
    {
        "brand": "Olympus",
        "model": "SpinSR",
        "aliases": ["SpinSR", "SpinSR10", "IXplore SpinSR",
                    "Olympus SpinSR"],
        "category": "spinning_disk",
        "software": ["cellSens", "Olympus Spin"],
        "techniques": [
            "Spinning Disk Confocal Microscopy", "Super-Resolution Microscopy",
            "Live Cell Imaging", "3D Imaging"
        ],
        "laser_lines": [405, 445, 488, 514, 561, 594, 640],
        "detectors": ["sCMOS", "EMCCD"],
        "objectives": ["UPLSAPO 60x/1.35 SIL", "UPLXAPO 60x/1.42"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Spinning disk with optical super-resolution (SoRa technology)"
    },
    {
        "brand": "Olympus",
        "model": "VS120",
        "aliases": ["VS120", "Olympus VS120", "VS120-L100"],
        "category": "other",
        "software": ["OlyVIA", "cellSens"],
        "techniques": [
            "Brightfield Microscopy", "Widefield Fluorescence Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["CCD"],
        "objectives": ["UPLSAPO", "UPLFL"],
        "filter_sets": [],
        "discontinued": True,
        "successor": "VS200",
        "notes": "Slide scanner for whole-slide imaging"
    },

    # ==================================================================
    # YOKOGAWA / 3i — Spinning Disk
    # ==================================================================
    {
        "brand": "Yokogawa",
        "model": "CSU-W1",
        "aliases": ["CSU-W1", "CSUW1", "Yokogawa W1", "CSU-W1 SoRa"],
        "category": "spinning_disk",
        "software": ["SlideBook", "MetaMorph", "MicroManager", "NIS-Elements",
                     "Leica Application Suite X", "ZEN"],
        "techniques": [
            "Spinning Disk Confocal Microscopy", "Live Cell Imaging",
            "3D Imaging", "Super-Resolution Microscopy"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 594, 640, 685],
        "detectors": ["EMCCD", "sCMOS (attached camera varies)"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Dual spinning disk (50µm and 25µm pinholes); SoRa super-res option; mounted on host microscope body"
    },
    {
        "brand": "Yokogawa",
        "model": "CSU-X1",
        "aliases": ["CSU-X1", "CSUX1", "Yokogawa X1"],
        "category": "spinning_disk",
        "software": ["SlideBook", "MetaMorph", "MicroManager", "NIS-Elements",
                     "Leica Application Suite X", "Volocity"],
        "techniques": [
            "Spinning Disk Confocal Microscopy", "Live Cell Imaging",
            "3D Imaging"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 594, 640],
        "detectors": ["EMCCD", "sCMOS"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": True,
        "successor": "CSU-W1",
        "notes": "Most widely deployed spinning disk; 5000rpm or 10000rpm"
    },

    # ==================================================================
    # ABBERIOR — STED
    # ==================================================================
    {
        "brand": "Abberior",
        "model": "STEDYCON",
        "aliases": ["STEDYCON", "Abberior STEDYCON"],
        "category": "super_resolution",
        "software": ["Imspector"],
        "techniques": [
            "Stimulated Emission Depletion Microscopy",
            "Super-Resolution Microscopy",
            "Confocal Laser Scanning Microscopy"
        ],
        "laser_lines": [405, 488, 561, 640, 775],
        "detectors": ["APD (avalanche photodiode)"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Compact STED module that attaches to existing microscope body"
    },
    {
        "brand": "Abberior",
        "model": "Facility Line",
        "aliases": ["Facility Line", "Abberior Facility Line", "Abberior STED"],
        "category": "super_resolution",
        "software": ["Imspector"],
        "techniques": [
            "Stimulated Emission Depletion Microscopy",
            "Super-Resolution Microscopy",
            "Confocal Laser Scanning Microscopy",
            "Fluorescence Lifetime Imaging Microscopy"
        ],
        "laser_lines": [405, 440, 473, 488, 510, 532, 561, 580, 594, 615, 640, 660, 775],
        "detectors": ["APD", "SPAD array"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Dedicated STED system with pulsed STED at 775nm; MINFLUX option"
    },

    # ==================================================================
    # LIGHT SHEET — Community / Open-Source
    # ==================================================================
    {
        "brand": "Luxendo",
        "model": "MuVi SPIM",
        "aliases": ["MuVi SPIM", "MuVi-SPIM", "Luxendo MuVi"],
        "category": "light_sheet",
        "software": ["Luxendo software"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy", "Live Cell Imaging",
            "3D Imaging", "4D Imaging"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 638],
        "detectors": ["sCMOS"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Multi-view SPIM for developmental biology"
    },
    {
        "brand": "LaVision BioTec",
        "model": "UltraMicroscope",
        "aliases": ["UltraMicroscope", "UltraMicroscope II",
                    "UltraMicroscope Blaze", "LaVision UltraMicroscope"],
        "category": "light_sheet",
        "software": ["ImspectorPro", "Imaris"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy",
            "3D Imaging", "Optical Sectioning"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 594, 640, 785],
        "detectors": ["sCMOS (Andor/Hamamatsu)"],
        "objectives": ["LVMI-Fluor 1.3x-12x zoom"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Optimized for cleared tissue imaging (CLARITY, iDISCO, CUBIC, etc)"
    },
    {
        "brand": "3i (Intelligent Imaging)",
        "model": "Marianas",
        "aliases": ["Marianas", "3i Marianas", "Intelligent Imaging Marianas"],
        "category": "widefield",
        "software": ["SlideBook"],
        "techniques": [
            "Widefield Fluorescence Microscopy", "Live Cell Imaging",
            "Spinning Disk Confocal Microscopy",
            "Total Internal Reflection Fluorescence Microscopy"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 594, 640],
        "detectors": ["EMCCD", "sCMOS"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Turnkey imaging system; typically Zeiss Axio Observer base"
    },
    {
        "brand": "Community",
        "model": "MesoSPIM",
        "aliases": ["mesoSPIM", "MesoSPIM", "meso-SPIM"],
        "category": "light_sheet",
        "software": ["mesoSPIM-control", "Python"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy",
            "MesoSPIM Light Sheet Microscopy",
            "3D Imaging"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 594, 638],
        "detectors": ["sCMOS (Hamamatsu ORCA)"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Open-source mesoscale SPIM for cleared tissue"
    },
    {
        "brand": "Community",
        "model": "diSPIM",
        "aliases": ["diSPIM", "ASI diSPIM"],
        "category": "light_sheet",
        "software": ["MicroManager"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy",
            "Live Cell Imaging", "3D Imaging", "4D Imaging"
        ],
        "laser_lines": [405, 445, 488, 561, 640],
        "detectors": ["sCMOS"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Dual-view inverted SPIM by ASI; isotropic resolution via dual-view fusion"
    },
    {
        "brand": "Community",
        "model": "OpenSPIM",
        "aliases": ["OpenSPIM", "Open SPIM"],
        "category": "light_sheet",
        "software": ["MicroManager"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy",
            "Live Cell Imaging", "3D Imaging"
        ],
        "laser_lines": [],
        "detectors": ["sCMOS or CCD (user-configured)"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Open-source light sheet build; parts list and wiki at openspim.org"
    },
    {
        "brand": "LifeCanvas",
        "model": "SmartSPIM",
        "aliases": ["SmartSPIM", "LifeCanvas SmartSPIM"],
        "category": "light_sheet",
        "software": ["SmartSPIM software"],
        "techniques": [
            "Light Sheet Fluorescence Microscopy",
            "3D Imaging"
        ],
        "laser_lines": [405, 445, 488, 561, 594, 639, 785],
        "detectors": ["sCMOS"],
        "objectives": ["3.6x/0.2", "15x/0.4"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Automated whole-organ imaging of cleared tissue"
    },

    # ==================================================================
    # ELECTRON MICROSCOPY — Thermo Fisher / FEI
    # ==================================================================
    {
        "brand": "FEI",
        "model": "Titan",
        "aliases": ["Titan", "Titan Krios", "Titan Halo", "FEI Titan",
                    "Thermo Fisher Titan Krios"],
        "category": "electron",
        "software": ["EPU", "SerialEM", "Leginon"],
        "techniques": [
            "Cryo-Electron Microscopy", "Single-Particle Analysis",
            "Cryo-Electron Tomography", "Transmission Electron Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["Falcon 4i", "K3 (Gatan)", "CETA-D"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Gold standard for cryo-EM SPA; 300kV; autoloader"
    },
    {
        "brand": "FEI",
        "model": "Glacios",
        "aliases": ["Glacios", "Glacios 2", "FEI Glacios",
                    "Thermo Fisher Glacios"],
        "category": "electron",
        "software": ["EPU", "SerialEM"],
        "techniques": [
            "Cryo-Electron Microscopy", "Single-Particle Analysis",
            "Transmission Electron Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["Falcon 4i", "CETA-D"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "200kV cryo-EM for screening and data collection"
    },
    {
        "brand": "FEI",
        "model": "Talos",
        "aliases": ["Talos", "Talos Arctica", "Talos L120C", "FEI Talos",
                    "Thermo Fisher Talos"],
        "category": "electron",
        "software": ["EPU", "SerialEM", "MAPS"],
        "techniques": [
            "Cryo-Electron Microscopy", "Transmission Electron Microscopy",
            "Cryo-Electron Tomography"
        ],
        "laser_lines": [],
        "detectors": ["Falcon III", "Falcon 4", "CETA"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "200kV; Arctica for cryo-EM, L120C for room-temperature TEM"
    },
    {
        "brand": "FEI",
        "model": "Tecnai",
        "aliases": ["Tecnai", "Tecnai G2", "Tecnai F20", "Tecnai F30",
                    "Tecnai Spirit", "FEI Tecnai"],
        "category": "electron",
        "software": ["TIA", "SerialEM"],
        "techniques": [
            "Transmission Electron Microscopy",
            "Cryo-Electron Microscopy", "Electron Tomography"
        ],
        "laser_lines": [],
        "detectors": ["Eagle CCD", "Ultrascan CCD", "Falcon"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": True,
        "successor": "Talos",
        "notes": "Workhorse TEM; Spirit at 120kV, F20 at 200kV, F30 at 300kV"
    },
    {
        "brand": "FEI",
        "model": "Helios",
        "aliases": ["Helios", "Helios NanoLab", "Helios G4", "FEI Helios"],
        "category": "electron",
        "software": ["MAPS", "Auto Slice and View"],
        "techniques": [
            "Focused Ion Beam Scanning Electron Microscopy",
            "Scanning Electron Microscopy",
            "Correlative Light and Electron Microscopy",
            "Volume Electron Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["ETD", "TLD", "ICE", "STEM"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Dual-beam FIB-SEM for serial sectioning and cryo-FIB"
    },

    # ==================================================================
    # ELECTRON MICROSCOPY — JEOL
    # ==================================================================
    {
        "brand": "JEOL",
        "model": "JEM-1400",
        "aliases": ["JEM-1400", "JEM-1400Plus", "JEM-1400Flash", "JEOL 1400"],
        "category": "electron",
        "software": ["JEOL TEM Center", "SerialEM"],
        "techniques": [
            "Transmission Electron Microscopy",
            "Negative Stain Electron Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["JEOL OneView", "Gatan cameras"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "120kV TEM; Flash variant for cryo screening"
    },
    {
        "brand": "JEOL",
        "model": "JEM-2100",
        "aliases": ["JEM-2100", "JEM-2100F", "JEM-2100Plus", "JEOL 2100"],
        "category": "electron",
        "software": ["JEOL TEM Center", "SerialEM", "Digital Micrograph"],
        "techniques": [
            "Transmission Electron Microscopy",
            "Cryo-Electron Microscopy",
            "Electron Tomography"
        ],
        "laser_lines": [],
        "detectors": ["Gatan OneView", "Gatan Ultrascan"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "200kV analytical TEM"
    },
    {
        "brand": "JEOL",
        "model": "CRYO ARM",
        "aliases": ["CRYO ARM", "CRYO ARM 200", "CRYO ARM 300",
                    "JEOL CRYO ARM", "JEM-Z200FSC", "JEM-Z300FSC"],
        "category": "electron",
        "software": ["JEOL JADAS", "SerialEM"],
        "techniques": [
            "Cryo-Electron Microscopy", "Single-Particle Analysis",
            "Cryo-Electron Tomography"
        ],
        "laser_lines": [],
        "detectors": ["K3 (Gatan)", "DE-64"],
        "objectives": [],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Cold FEG cryo-EM; competitor to Titan Krios"
    },

    # ==================================================================
    # HIGH-CONTENT SCREENING
    # ==================================================================
    {
        "brand": "PerkinElmer",
        "model": "Opera Phenix",
        "aliases": ["Opera Phenix", "Opera Phenix Plus", "PerkinElmer Opera",
                    "Operetta", "Operetta CLS"],
        "category": "spinning_disk",
        "software": ["Harmony", "Columbus"],
        "techniques": [
            "High-Content Screening", "Spinning Disk Confocal Microscopy",
            "Fluorescence Microscopy", "Live Cell Imaging"
        ],
        "laser_lines": [375, 405, 445, 488, 520, 561, 594, 640, 730],
        "detectors": ["sCMOS (x4 cameras)", "high-NA spinning disk"],
        "objectives": ["20x water, 40x water, 63x water"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "High-content confocal plate imager; Harmony for analysis"
    },
    {
        "brand": "Molecular Devices",
        "model": "ImageXpress",
        "aliases": ["ImageXpress", "ImageXpress Micro", "ImageXpress Confocal",
                    "ImageXpress Pico", "IXM"],
        "category": "widefield",
        "software": ["MetaXpress"],
        "techniques": [
            "High-Content Screening", "Widefield Fluorescence Microscopy",
            "Confocal Laser Scanning Microscopy"
        ],
        "laser_lines": [375, 405, 445, 475, 520, 561, 594, 640],
        "detectors": ["sCMOS"],
        "objectives": ["Plan Fluor 10x-60x"],
        "filter_sets": ["DAPI", "FITC", "TRITC", "Texas Red", "Cy5"],
        "discontinued": False,
        "successor": None,
        "notes": "Automated multiwell plate imaging; Confocal variant has spinning disk"
    },

    # ==================================================================
    # MULTIPHOTON — DEDICATED
    # ==================================================================
    {
        "brand": "Bruker",
        "model": "Ultima Investigator",
        "aliases": ["Ultima Investigator", "Ultima 2Pplus", "Bruker Ultima",
                    "Prairie Ultima"],
        "category": "multiphoton",
        "software": ["Prairie View"],
        "techniques": [
            "Two-Photon Excitation Microscopy", "Multiphoton Microscopy",
            "Three-Photon Microscopy", "Live Cell Imaging",
            "Calcium Imaging", "Intravital Microscopy",
            "Second Harmonic Generation"
        ],
        "laser_lines": [],
        "detectors": ["GaAsP-PMT", "multi-alkali PMT"],
        "objectives": ["Nikon 16x/0.8 WI", "Olympus 25x/1.05 WI"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Requires tunable fs laser (e.g., Coherent Chameleon, Spectra-Physics MaiTai/InSight)"
    },
    {
        "brand": "Thorlabs",
        "model": "Bergamo",
        "aliases": ["Bergamo", "Bergamo II", "Thorlabs Bergamo"],
        "category": "multiphoton",
        "software": ["ThorImage"],
        "techniques": [
            "Two-Photon Excitation Microscopy", "Multiphoton Microscopy",
            "Calcium Imaging", "Intravital Microscopy",
            "Second Harmonic Generation"
        ],
        "laser_lines": [],
        "detectors": ["GaAsP-PMT"],
        "objectives": ["Nikon 16x/0.8 WI", "Olympus 25x/1.05 WI"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Modular multiphoton platform for in vivo neuroscience"
    },

    # ==================================================================
    # EVIDENT — Latest
    # ==================================================================
    {
        "brand": "Olympus",
        "model": "FV4000",
        "aliases": ["FV4000", "FLUOVIEW FV4000", "FV4000MPE",
                    "Evident FV4000", "Olympus FV4000"],
        "category": "confocal",
        "software": ["cellSens", "FluoView"],
        "techniques": [
            "Confocal Laser Scanning Microscopy",
            "Super-Resolution Microscopy",
            "Multiphoton Microscopy",
            "Fluorescence Lifetime Imaging Microscopy"
        ],
        "laser_lines": [405, 445, 488, 515, 561, 594, 640],
        "detectors": ["SilVIR (4 GaAsP)", "PMT"],
        "objectives": ["UPLXAPO", "UPLSAPO"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Next-gen Olympus/Evident confocal with TruResolution"
    },

    # ==================================================================
    # SLIDE SCANNERS
    # ==================================================================
    {
        "brand": "Hamamatsu",
        "model": "NanoZoomer",
        "aliases": ["NanoZoomer", "NanoZoomer S360", "NanoZoomer S60",
                    "NanoZoomer S210", "NanoZoomer XR",
                    "Hamamatsu NanoZoomer"],
        "category": "other",
        "software": ["NDP.view", "NDP.serve"],
        "techniques": [
            "Brightfield Microscopy", "Widefield Fluorescence Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["TDI line sensor"],
        "objectives": ["20x/0.75", "40x/0.75"],
        "filter_sets": ["DAPI", "FITC", "TRITC", "Cy5"],
        "discontinued": False,
        "successor": None,
        "notes": "Whole-slide imaging scanner for digital pathology"
    },
    {
        "brand": "Leica",
        "model": "Aperio",
        "aliases": ["Aperio", "Aperio AT2", "Aperio CS2", "Aperio GT 450",
                    "Aperio VERSA", "Leica Aperio"],
        "category": "other",
        "software": ["Aperio ImageScope", "Leica Application Suite X"],
        "techniques": [
            "Brightfield Microscopy", "Widefield Fluorescence Microscopy"
        ],
        "laser_lines": [],
        "detectors": ["line-scan camera"],
        "objectives": ["20x", "40x"],
        "filter_sets": [],
        "discontinued": False,
        "successor": None,
        "notes": "Widely used clinical/research slide scanner"
    },

]


# =====================================================================
# BRAND → SOFTWARE MAPPING
# For inferring software when only brand is detected
# =====================================================================

BRAND_SOFTWARE_MAP: Dict[str, Dict[str, Any]] = {
    "Zeiss": {
        "acquisition": ["ZEN", "ZEN Blue", "ZEN Black"],
        "legacy_acquisition": ["AxioVision", "LSM Image Browser"],
        "analysis": ["ZEN", "arivis"],
        "notes": "ZEN Blue = newer, ZEN Black = legacy LSM systems"
    },
    "Leica": {
        "acquisition": ["Leica Application Suite X", "LAS X"],
        "legacy_acquisition": ["Leica Application Suite", "LAS AF"],
        "analysis": ["Leica Application Suite X", "Aivia"],
        "notes": "LAS X replaced LAS AF circa 2015"
    },
    "Nikon": {
        "acquisition": ["NIS-Elements", "NIS-Elements C", "NIS-Elements AR"],
        "legacy_acquisition": ["NIS-Elements"],
        "analysis": ["NIS-Elements", "NIS-Elements AR"],
        "notes": "C = confocal module, AR = advanced research"
    },
    "Olympus": {
        "acquisition": ["FluoView", "cellSens"],
        "legacy_acquisition": ["FluoView"],
        "analysis": ["cellSens"],
        "notes": "FluoView for confocal, cellSens for widefield; Evident branding since 2022"
    },
    "Evident (Olympus)": {
        "acquisition": ["FluoView", "cellSens"],
        "legacy_acquisition": ["FluoView"],
        "analysis": ["cellSens"],
        "notes": "Olympus life science division rebranded as Evident"
    },
    "Andor": {
        "acquisition": ["iQ", "Fusion"],
        "legacy_acquisition": ["iQ"],
        "analysis": ["Imaris"],
        "notes": "Andor cameras often controlled by host software (NIS, MetaMorph, etc)"
    },
    "Yokogawa": {
        "acquisition": ["SlideBook", "MetaMorph", "MicroManager",
                       "NIS-Elements", "Leica Application Suite X", "ZEN"],
        "legacy_acquisition": [],
        "analysis": [],
        "notes": "Spinning disk unit controlled by host microscope software"
    },
    "3i (Intelligent Imaging)": {
        "acquisition": ["SlideBook"],
        "legacy_acquisition": ["SlideBook"],
        "analysis": ["SlideBook"],
        "notes": "3i systems always use SlideBook"
    },
    "PerkinElmer": {
        "acquisition": ["Harmony", "Volocity Acquisition"],
        "legacy_acquisition": ["Volocity"],
        "analysis": ["Columbus", "Harmony"],
        "notes": "Harmony for Opera/Operetta; Volocity for older UltraVIEW"
    },
    "Molecular Devices": {
        "acquisition": ["MetaXpress"],
        "legacy_acquisition": ["MetaMorph"],
        "analysis": ["MetaXpress"],
        "notes": "MetaMorph was also widely used as generic acquisition software"
    },
    "Bruker": {
        "acquisition": ["Prairie View"],
        "legacy_acquisition": ["Prairie View"],
        "analysis": [],
        "notes": "Prairie Technologies acquired by Bruker; multiphoton systems"
    },
    "Thorlabs": {
        "acquisition": ["ThorImage"],
        "legacy_acquisition": [],
        "analysis": [],
        "notes": "Bergamo multiphoton uses ThorImage"
    },
    "Abberior": {
        "acquisition": ["Imspector"],
        "legacy_acquisition": [],
        "analysis": ["Imspector"],
        "notes": "Imspector for all Abberior STED systems"
    },
    "LaVision BioTec": {
        "acquisition": ["ImspectorPro"],
        "legacy_acquisition": [],
        "analysis": ["Imaris"],
        "notes": "Now owned by Miltenyi Biotec"
    },
    "FEI": {
        "acquisition": ["EPU", "SerialEM", "MAPS"],
        "legacy_acquisition": ["TIA"],
        "analysis": ["cryoSPARC", "RELION"],
        "notes": "Now Thermo Fisher Scientific; EPU for cryo-EM automation"
    },
    "JEOL": {
        "acquisition": ["JEOL JADAS", "SerialEM"],
        "legacy_acquisition": ["JEOL TEM Center"],
        "analysis": ["cryoSPARC", "RELION"],
        "notes": "CRYO ARM systems use JADAS for automated acquisition"
    },
    "Hamamatsu": {
        "acquisition": ["HCImage", "NDP.view"],
        "legacy_acquisition": ["HCImage"],
        "analysis": ["NDP.view", "NDP.serve"],
        "notes": "Camera maker; NanoZoomer slide scanners use NDP software"
    },
    "PicoQuant": {
        "acquisition": ["SymPhoTime"],
        "legacy_acquisition": [],
        "analysis": ["SymPhoTime"],
        "notes": "FLIM/FCS hardware and software"
    },
    "Becker & Hickl": {
        "acquisition": ["SPCImage"],
        "legacy_acquisition": [],
        "analysis": ["SPCImage"],
        "notes": "TCSPC-based FLIM hardware"
    },
}


# =====================================================================
# COMMON LASER SYSTEMS (for detecting laser brand → microscope brand links)
# =====================================================================

LASER_SYSTEMS: List[Dict[str, Any]] = [
    {
        "brand": "Coherent",
        "model": "Chameleon",
        "aliases": ["Chameleon", "Chameleon Ultra", "Chameleon Vision",
                    "Chameleon Discovery", "Coherent Chameleon"],
        "type": "tunable_fs",
        "wavelength_range": "680-1080nm (Ultra), 680-1300nm (Discovery)",
        "typical_use": ["Two-Photon Excitation Microscopy", "Multiphoton Microscopy",
                       "Three-Photon Microscopy", "Second Harmonic Generation"],
        "notes": "Most common multiphoton laser; Discovery NX has dual output"
    },
    {
        "brand": "Spectra-Physics",
        "model": "MaiTai",
        "aliases": ["MaiTai", "Mai Tai", "MaiTai DeepSee", "MaiTai HP",
                    "Spectra-Physics MaiTai"],
        "type": "tunable_fs",
        "wavelength_range": "690-1040nm",
        "typical_use": ["Two-Photon Excitation Microscopy", "Multiphoton Microscopy"],
        "notes": "DeepSee variant has built-in GDD compensation"
    },
    {
        "brand": "Spectra-Physics",
        "model": "InSight",
        "aliases": ["InSight", "InSight X3", "InSight X3+",
                    "Spectra-Physics InSight"],
        "type": "tunable_fs",
        "wavelength_range": "680-1300nm + fixed 1045nm",
        "typical_use": ["Two-Photon Excitation Microscopy", "Multiphoton Microscopy",
                       "Three-Photon Microscopy"],
        "notes": "Dual-output OPO-based system"
    },
    {
        "brand": "Toptica",
        "model": "iChrome",
        "aliases": ["iChrome", "iChrome MLE", "Toptica iChrome"],
        "type": "multi_line",
        "wavelength_range": "405-640nm (selectable lines)",
        "typical_use": ["Confocal Laser Scanning Microscopy",
                       "Fluorescence Microscopy"],
        "notes": "Multi-laser engine for confocal/widefield"
    },
    {
        "brand": "Cobolt",
        "model": "Skyra",
        "aliases": ["Skyra", "Cobolt Skyra"],
        "type": "multi_line",
        "wavelength_range": "405, 488, 561, 640nm",
        "typical_use": ["Confocal Laser Scanning Microscopy",
                       "Super-Resolution Microscopy"],
        "notes": "Compact multi-line laser; now HÜBNER Photonics"
    },
    {
        "brand": "NKT Photonics",
        "model": "SuperK",
        "aliases": ["SuperK", "SuperK Extreme", "SuperK FIANIUM",
                    "NKT SuperK", "white light laser"],
        "type": "supercontinuum",
        "wavelength_range": "400-2400nm",
        "typical_use": ["Confocal Laser Scanning Microscopy",
                       "Fluorescence Microscopy"],
        "notes": "White light laser / supercontinuum; used in Leica WLL systems"
    },
]


# =====================================================================
# OUTPUT BUILDERS
# =====================================================================

def build_microscope_kb() -> Dict[str, Any]:
    """Build the main knowledge base JSON structure."""
    # Build model lookup (key = lowercase model name)
    model_lookup = {}
    for sys_entry in MICROSCOPE_SYSTEMS:
        key = sys_entry["model"].lower().replace(" ", "_")
        model_lookup[key] = sys_entry

        # Also index by aliases
        for alias in sys_entry.get("aliases", []):
            alias_key = alias.lower().replace(" ", "_").replace(".", "")
            if alias_key not in model_lookup:
                model_lookup[alias_key] = sys_entry

    # Build alias → canonical model mapping
    alias_map = {}
    for sys_entry in MICROSCOPE_SYSTEMS:
        canonical = sys_entry["model"]
        for alias in sys_entry.get("aliases", []):
            alias_map[alias.lower()] = canonical

    # Build technique → models mapping
    technique_models = {}
    for sys_entry in MICROSCOPE_SYSTEMS:
        for tech in sys_entry.get("techniques", []):
            technique_models.setdefault(tech, []).append({
                "brand": sys_entry["brand"],
                "model": sys_entry["model"]
            })

    # Build software → brands/models mapping
    software_models = {}
    for sys_entry in MICROSCOPE_SYSTEMS:
        for sw in sys_entry.get("software", []):
            software_models.setdefault(sw, []).append({
                "brand": sys_entry["brand"],
                "model": sys_entry["model"]
            })

    # Summary statistics
    brands_counted = {}
    categories = {}
    for sys_entry in MICROSCOPE_SYSTEMS:
        b = sys_entry["brand"]
        c = sys_entry["category"]
        brands_counted[b] = brands_counted.get(b, 0) + 1
        categories[c] = categories.get(c, 0) + 1

    return {
        "_metadata": {
            "version": "1.0",
            "created": str(date.today()),
            "description": (
                "Microscopy equipment knowledge base for MicroHub pipeline. "
                "Maps microscope models to brands, software, techniques, lasers, "
                "and detectors for tag inference and validation."
            ),
            "total_systems": len(MICROSCOPE_SYSTEMS),
            "total_aliases": len(alias_map),
            "brands": brands_counted,
            "categories": categories,
            "sources": [
                "Manufacturer product pages (Zeiss, Leica, Nikon, Olympus/Evident)",
                "4DN-BINA-OME Microscopy Metadata specifications",
                "Community knowledge (image.sc, BINA)",
                "Published microscopy methods literature"
            ]
        },
        "systems": MICROSCOPE_SYSTEMS,
        "alias_to_canonical": alias_map,
        "brand_software_map": BRAND_SOFTWARE_MAP,
        "laser_systems": LASER_SYSTEMS,
        "technique_to_models": technique_models,
        "software_to_models": software_models,
    }


def build_model_aliases() -> Dict[str, List[str]]:
    """Build a flat alias → canonical mapping for fast regex-free lookup."""
    result = {}
    for sys_entry in MICROSCOPE_SYSTEMS:
        canonical = f"{sys_entry['brand']} {sys_entry['model']}"
        aliases = sys_entry.get("aliases", [])
        result[canonical] = aliases
    return result


def validate_against_master_dict(kb: Dict, master_dict_path: str) -> List[str]:
    """Check that KB models and software align with MASTER_TAG_DICTIONARY."""
    issues = []

    if not os.path.exists(master_dict_path):
        issues.append(f"MASTER_TAG_DICTIONARY not found at {master_dict_path}")
        return issues

    with open(master_dict_path, "r") as f:
        master = json.load(f)

    # Check models
    valid_models = set(master.get("microscope_models", {}).get("all_valid_values", []))
    kb_models = set()
    for sys_entry in kb["systems"]:
        kb_models.add(sys_entry["model"])

    missing_from_master = kb_models - valid_models
    if missing_from_master:
        issues.append(
            f"Models in KB but not in MASTER_TAG_DICTIONARY.microscope_models: "
            f"{sorted(missing_from_master)}"
        )

    missing_from_kb = valid_models - kb_models
    if missing_from_kb:
        issues.append(
            f"Models in MASTER_TAG_DICTIONARY but not in KB: "
            f"{sorted(missing_from_kb)}"
        )

    # Check brands
    valid_brands = set(master.get("microscope_brands", {}).get("all_valid_values", []))
    kb_brands = set(s["brand"] for s in kb["systems"])
    missing_brands = kb_brands - valid_brands - {"Community", "LifeCanvas"}  # Expected additions
    if missing_brands:
        issues.append(
            f"Brands in KB but not in MASTER_TAG_DICTIONARY.microscope_brands: "
            f"{sorted(missing_brands)}"
        )

    # Check software
    valid_software = set(
        master.get("image_analysis_software", {}).get("all_valid_values", []) +
        master.get("image_acquisition_software", {}).get("all_valid_values", [])
    )
    kb_software = set()
    for sys_entry in kb["systems"]:
        kb_software.update(sys_entry.get("software", []))
    for brand_data in kb.get("brand_software_map", {}).values():
        kb_software.update(brand_data.get("acquisition", []))
        kb_software.update(brand_data.get("legacy_acquisition", []))
        kb_software.update(brand_data.get("analysis", []))

    new_software = kb_software - valid_software
    if new_software:
        issues.append(
            f"Software in KB not in MASTER_TAG_DICTIONARY (may need adding): "
            f"{sorted(new_software)}"
        )

    return issues


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Build microscopy equipment knowledge base for MicroHub"
    )
    parser.add_argument(
        "--output-dir", default="microscope_kb",
        help="Output directory (default: microscope_kb)"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate against MASTER_TAG_DICTIONARY.json"
    )
    parser.add_argument(
        "--master-dict",
        default=os.path.join(os.path.dirname(__file__), "MASTER_TAG_DICTIONARY.json"),
        help="Path to MASTER_TAG_DICTIONARY.json"
    )
    args = parser.parse_args()

    # Build KB
    print("Building microscopy equipment knowledge base...")
    kb = build_microscope_kb()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Write main KB
    kb_path = os.path.join(args.output_dir, "microscope_kb.json")
    with open(kb_path, "w") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    print(f"  → {kb_path} ({len(kb['systems'])} systems, {len(kb['alias_to_canonical'])} aliases)")

    # Write brand→software map (useful standalone)
    bsm_path = os.path.join(args.output_dir, "brand_software_map.json")
    with open(bsm_path, "w") as f:
        json.dump(BRAND_SOFTWARE_MAP, f, indent=2)
    print(f"  → {bsm_path} ({len(BRAND_SOFTWARE_MAP)} brands)")

    # Write alias lookup
    aliases = build_model_aliases()
    alias_path = os.path.join(args.output_dir, "model_aliases.json")
    with open(alias_path, "w") as f:
        json.dump(aliases, f, indent=2)
    print(f"  → {alias_path} ({sum(len(v) for v in aliases.values())} total aliases)")

    # Write laser systems
    laser_path = os.path.join(args.output_dir, "laser_systems.json")
    with open(laser_path, "w") as f:
        json.dump(LASER_SYSTEMS, f, indent=2)
    print(f"  → {laser_path} ({len(LASER_SYSTEMS)} laser systems)")

    # Summary
    meta = kb["_metadata"]
    print(f"\nSummary:")
    print(f"  Systems:    {meta['total_systems']}")
    print(f"  Aliases:    {meta['total_aliases']}")
    print(f"  Brands:     {meta['brands']}")
    print(f"  Categories: {meta['categories']}")

    # Validate
    if args.validate:
        print("\nValidating against MASTER_TAG_DICTIONARY...")
        issues = validate_against_master_dict(kb, args.master_dict)
        if issues:
            print(f"  Found {len(issues)} issue(s):")
            for issue in issues:
                print(f"  ⚠  {issue}")
        else:
            print("  ✓ All good!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
