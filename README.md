# MicroHub Paper Scraper v1.2

A comprehensive paper collection system for microscopy research.

## Key Fixes in v1.2

- **Database Locking Fixed**: Uses WAL mode and proper retry logic
- **Comprehensive Searches**: All microscopy categories covered
- **Software Detection**: 30+ image analysis tools detected
- **Microscope Brands**: All major brands (Zeiss, Leica, Nikon, Olympus, etc.)

## Installation

```bash
pip install requests aiohttp certifi
```

## Quick Start

```bash
# Quick test (100 papers)
python run_pipeline.py --quick

# Full pipeline (takes hours)
python run_pipeline.py

# Check stats
python run_pipeline.py --stats
```

## Individual Commands

```bash
# Scrape only (all categories)
python microhub_scraper.py

# Scrape with limit
python microhub_scraper.py --limit 10000

# Priority sources only (protocols, github, data)
python microhub_scraper.py --priority-only

# Enrich papers
python microhub_enrich.py

# Export for WordPress
python microhub_export.py -o papers.json
python microhub_export.py --enriched-only -o enriched_papers.json
```

## Search Categories

### Protocols & Code (Highest Priority)
- protocols.io, Bio-protocol, Nature Protocols, JoVE, STAR Protocols
- GitHub, GitLab
- Zenodo, Figshare, Dryad, IDR, EMPIAR, BioImage Archive

### Image Analysis Software (30+ tools)
- ImageJ, Fiji, CellProfiler, Imaris, ilastik, QuPath, napari
- StarDist, Cellpose, DeepCell, ZeroCostDL4Mic
- Metamorph, Volocity, OMERO, Icy
- Vendor: ZEN, LAS X, NIS-Elements

### Microscope Brands (All Major)
- Zeiss: LSM, Airyscan, Elyra, Axio, Lightsheet
- Leica: SP5/SP8, Stellaris, Thunder, TCS
- Nikon: A1R, Ti-E/Ti2, N-SIM, N-STORM
- Olympus: FV1000/FV3000, IX83, SpinSR
- Andor, PerkinElmer, Yokogawa
- Thermo Fisher/FEI (EM): Titan, Krios, Glacios
- JEOL

### Techniques
- Super-resolution: STED, STORM, PALM, SIM, Expansion
- Electron: Cryo-EM, Cryo-ET, TEM, SEM, FIB-SEM
- Advanced: Confocal, Two-photon, Light sheet, TIRF
- Functional: FRET, FLIM, FRAP, Calcium imaging
- Live cell, High-content screening

### Image Analysis Methods
- Deep learning, Machine learning, CNN, U-Net
- Cell/nucleus segmentation
- Tracking, Colocalization, Deconvolution, 3D reconstruction

## Output

Papers are exported as JSON with:
- Paper metadata (title, authors, journal, year, abstract)
- Identifiers (DOI, PMID, PMC ID)
- Citations count
- Techniques detected
- Software detected
- Microscope brand
- Organisms
- Protocols (with URLs)
- GitHub URL
- Data repositories (with URLs)
- RRIDs
- Priority score

## Files

```
microhub_scraper.py   - Paper collection (PubMed API)
microhub_enrich.py    - Add protocols/repos/citations
microhub_export.py    - Export to WordPress JSON
run_pipeline.py       - Run complete pipeline
```
