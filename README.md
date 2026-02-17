# MicroHub Multi-Agent NLP Pipeline v6.0

A production-ready pipeline for extracting structured metadata from microscopy
research papers, built on specialized extraction agents with confidence scoring
and conflict resolution.

## Architecture

```
PDF / PubMed Article
       │
       ▼
┌─────────────────────┐
│  Section-Aware      │  GROBID (PDF) or PubMed/PMC API
│  Document Parser    │  Splits into: title, abstract, methods, results, etc.
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Extraction Agents  │  9 specialized agents run per-section:
│  ├─ Technique       │  - 60+ microscopy techniques (strict context matching)
│  ├─ Equipment       │  - 37 microscope brands, 47 models, reagent suppliers
│  ├─ Fluorophore     │  - 130+ fluorophores (FPbase + dictionary + regex)
│  ├─ Organism        │  - Latin names only (antibody source filtering)
│  ├─ Software        │  - Analysis, acquisition, and general software
│  ├─ Sample Prep     │  - Fixation, clearing, embedding, staining, culture
│  ├─ Cell Line       │  - 19 common cell lines
│  ├─ Protocol        │  - Protocols, repositories, RRIDs, RORs, GitHub
│  └─ Institution     │  - From affiliations only (with ROR ID lookup)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Validation Layer   │  FPbase API, NCBI Taxonomy, SciCrunch RRID,
│                     │  Master Tag Dictionary
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  JSON Exporter      │  IDENTICAL output format to v5.1
│  (WordPress-ready)  │  Protocol classification, chunked files
└─────────────────────┘
```

## Quick Start

```bash
pip install -r requirements.txt

# Export from existing database
python run_pipeline.py export

# Export with agent-based re-tagging
python run_pipeline.py export --enrich

# Clean and finalize for WordPress
python run_pipeline.py cleanup

# Validate exported JSON
python run_pipeline.py validate
```

## Commands

| Command    | Description |
|------------|-------------|
| `export`   | Export DB to chunked JSON for WordPress import |
| `cleanup`  | Clean and re-tag exported JSON (final step) |
| `scrape`   | Scrape new papers from PubMed |
| `validate` | Validate JSON against master tag dictionary |

### Export Options

```bash
python run_pipeline.py export --chunk-size 500       # Papers per file (default)
python run_pipeline.py export --enrich               # Re-run agents for fresh tags
python run_pipeline.py export --full-text-only        # Only papers with full text
python run_pipeline.py export --with-citations        # Only papers with citations
python run_pipeline.py export --min-citations 10      # Minimum citation count
python run_pipeline.py export --methods-only           # Only methods-extracted tags
python run_pipeline.py export --output-dir cleaned_export
```

## Project Structure

```
microhub/
├── run_pipeline.py              # Main entry point
├── MASTER_TAG_DICTIONARY.json   # Central taxonomy reference
├── requirements.txt
│
├── pipeline/                    # Multi-agent NLP pipeline
│   ├── orchestrator.py          # Wires agents together, conflict resolution
│   ├── parsing/
│   │   ├── grobid_parser.py     # GROBID PDF → structured sections
│   │   ├── pubmed_parser.py     # PubMed/PMC API parsing
│   │   └── section_extractor.py # Unified section interface
│   ├── agents/
│   │   ├── base_agent.py        # BaseAgent ABC + Extraction dataclass
│   │   ├── technique_agent.py   # Microscopy techniques (60+)
│   │   ├── equipment_agent.py   # Microscope brands/models + reagent suppliers
│   │   ├── fluorophore_agent.py # Fluorophores (130+ with FPbase)
│   │   ├── organism_agent.py    # Organisms (Latin names + context)
│   │   ├── software_agent.py    # Analysis/acquisition/general software
│   │   ├── sample_prep_agent.py # Sample preparation methods
│   │   ├── cell_line_agent.py   # Cell line identification
│   │   ├── protocol_agent.py    # Protocols, repos, RRIDs, RORs
│   │   └── institution_agent.py # Institution extraction + ROR lookup
│   ├── validation/
│   │   ├── tag_validator.py     # Master tag dictionary validation
│   │   ├── fpbase_validator.py  # FPbase API validation
│   │   ├── taxonomy_validator.py# NCBI Taxonomy validation
│   │   └── scicrunch_validator.py # SciCrunch RRID validation
│   └── export/
│       └── json_exporter.py     # WordPress-compatible JSON export
│
└── backup/                      # Previous pipeline versions (v5.x)
    ├── microhub_scraper.py
    ├── cleanup_and_retag.py
    ├── microhub_export_json_v4_1.py
    ├── update_metrics.py
    ├── validate_microhub_data.py
    └── test_microhub_pipeline.py
```

## JSON Output Format

The exported JSON is **identical** to the v5.1 format to prevent WordPress
upload issues. Each paper includes 80+ fields covering:

- Identifiers (DOI, PMID, PMC ID, Semantic Scholar ID)
- Paper metadata (title, abstract, authors, journal, year)
- Affiliations and institutions (with ROR IDs)
- Citation counts (Semantic Scholar, CrossRef)
- Microscopy techniques, brands, models
- Image analysis and acquisition software
- Fluorophores, organisms, cell lines
- Sample preparation methods
- Protocols, repositories, RRIDs
- GitHub tools with metrics
- Boolean flags for filtering
- Protocol classification (is_protocol, post_type, protocol_type)

## Environment Variables

```bash
GITHUB_TOKEN=...              # GitHub API (5000 req/hr vs 60/hr)
SEMANTIC_SCHOLAR_API_KEY=...  # Optional higher rate limits
```
