# MicroHub Codebase Guide

A comprehensive guide to every file in the MicroHub project — a pipeline that scrapes microscopy papers from PubMed/PMC, extracts structured metadata (techniques, equipment, software, organisms, etc.), validates it against authoritative databases, and exports WordPress-compatible JSON for the MicroHub website.

---

## High-Level Architecture

The pipeline runs in **4 numbered steps**, each a standalone Python script:

```
1_scrape.py  ->  2_export.py  ->  2b_segment.py  ->  3_clean.py
   |                |                 |                 |
   v                v                 v                 v
 SQLite DB     Raw JSON chunks   Segmented JSON    Final cleaned JSON
(PubMed data)  (DB to flat files) (section-split)  (tagged, enriched,
                                                    validated, WordPress-ready)
```

### External APIs Called

| API | Where Used | Purpose |
|-----|-----------|---------|
| **PubMed E-utilities** | `1_scrape.py`, `pubmed_parser.py` | Search and fetch paper metadata/XML |
| **Europe PMC** | `europepmc_fetcher.py` | Tier 1 full-text JATS XML retrieval |
| **Unpaywall** | `unpaywall_client.py` | Tier 2 open-access PDF URL discovery |
| **GROBID** | `grobid_parser.py` | PDF to structured TEI XML parsing (local service) |
| **SciHub** | `scihub_fetcher.py` | Last-resort full-text fallback |
| **OpenAlex** | `openalex_agent.py`, `enrichment.py` | Institution/ROR, topics, citations, OA status |
| **Semantic Scholar** | `enrichment.py`, `crossref_agent.py` | Citation counts, fields of study |
| **CrossRef** | `crossref_agent.py` | Journal metadata, funders, data repository links |
| **GitHub** | `enrichment.py`, `github_health_agent.py` | Repository health scores, stars, activity |
| **DataCite** | `datacite_linker_agent.py` | Dataset-publication link discovery |
| **OpenAIRE ScholeXplorer** | `datacite_linker_agent.py` | 40M+ dataset-publication links |
| **PubTator 3.0** | `pubtator_agent.py` | Pre-computed NER (species, chemicals, cell lines) |
| **ROR v2** | `ror_v2_client.py` | Institution affiliation to ROR ID matching |
| **SciCrunch** | `scicrunch_validator.py`, `rrid_validation_agent.py` | RRID validation |
| **FPbase** | `fpbase_validator.py`, `fpbase/_query.py` | Fluorescent protein validation/spectral data |
| **Cellosaurus** | `cellosaurus_client.py` | Cell line validation/accession IDs |
| **NCBI Taxonomy** | `taxonomy_validator.py` | Organism to TaxID validation |
| **EBI OLS4** | `ontology_normalizer.py` | Technique to FBbi ontology term mapping |
| **Ollama** | `ollama_agent.py` | Local LLM cross-checking of regex results (optional) |

---

## Step-by-Step Pipeline Scripts

### `1_scrape.py` -- Step 1: Scrape and Acquire Full Text

**Goal:** Populate a SQLite database with microscopy papers from PubMed, then fetch their full text.

**Two phases:**
- **Phase A** -- Runs the legacy scraper (`backup/microhub_scraper.py`) which searches PubMed for microscopy-related papers, fetches metadata, and stores everything in `microhub.db`.
- **Phase B** -- Full-text acquisition using a three-tier waterfall strategy:
  1. **Europe PMC JATS XML** (best -- pre-parsed section tags)
  2. **Unpaywall OA PDF into GROBID** (convert PDF to structured text)
  3. **SciHub DOI fallback** (last resort)

**Key function:**
- `acquire_fulltext(db_path, limit, use_scihub_fallback)` -- Queries the DB for papers missing full text, tries each tier in order, updates the `full_text` and `methods` columns.

**API calls:** PubMed E-utilities, Europe PMC REST, Unpaywall, GROBID (local), SciHub

---

### `2_export.py` -- Step 2: Export DB to JSON

**Goal:** Dump the SQLite database into chunked JSON files for downstream processing.

**What it does:**
- Reads papers from `microhub.db`
- Writes WordPress-compatible JSON in chunks (default 500 papers per file)
- Outputs to `raw_export/` directory
- This is a **raw dump** -- no enrichment or re-tagging happens here

**Key function:**
- `main()` -- Parses CLI args, instantiates `JsonExporter`, calls `exporter.export()`.

---

### `2b_segment.py` -- Step 2b: Section Segmentation

**Goal:** Split each paper's `full_text` into structured sections (methods, results, discussion, figures, data availability) so that extraction agents only process relevant sections -- preventing systematic over-tagging.

**Why this exists:** Without segmentation, entities merely *mentioned* in an introduction or literature review get tagged as if the paper actually *used* them.

**Key function:**
- `segment_paper(paper, strip_citations, include_introduction)` -- Adds `_segmented_methods`, `_segmented_results`, `_segmented_discussion`, `_segmented_figures`, `_segmented_data_availability` fields. Uses three strategies in order:
  1. Existing structured sections (from Europe PMC/GROBID)
  2. Heuristic heading-based segmentation of full_text
  3. Abstract-only fallback

Also strips inline citation markers (`[1]`, `(Smith et al., 2020)`) and reference lists to prevent false positives.

---

### `3_clean.py` -- Step 3: Tag, Enrich, Validate and Finalize

**Goal:** The main processing step. Takes raw/segmented JSON and runs the full pipeline: agent-based extraction, role classification, normalization, API enrichment, and finalization.

**Sub-stages in order:**
1. **Section segmentation** -- calls `segment_paper()` if not already done
2. **Agent extraction** -- instantiates `PipelineOrchestrator`, runs all agents per paper
3. **Role classification** -- filters REFERENCED vs USED entities
4. **Normalization** -- `normalize_tags()` canonicalizes all tag values
5. **Tag validation** -- checks against `MASTER_TAG_DICTIONARY.json`
6. **API enrichment** -- OpenAlex, Semantic Scholar, GitHub, CrossRef, DataCite, ROR v2
7. **Finalization** -- protocol classification, boolean flags (`is_open_access`, `has_dataset`, `is_protocol`), field stripping

**Key helper functions:**
- `_boolish(value)` -- Converts various truthy formats to Python bool
- `_is_open_access_value(paper)` -- Checks OA status from multiple fields
- `_has_dataset_repositories(paper)` -- Detects dataset repos by source or URL patterns
- Natural-language data-availability patterns -- Regex for "deposited in Zenodo" style prose

**API calls:** All of the above (OpenAlex, S2, GitHub, CrossRef, DataCite, ROR, PubTator, SciCrunch, FPbase, Cellosaurus, NCBI Taxonomy, OLS4)

---

## Pipeline Core (`pipeline/`)

### `pipeline/orchestrator.py` -- Pipeline Orchestrator

**Goal:** Central controller that wires all extraction agents together and processes a single paper end-to-end.

**Class: `PipelineOrchestrator`**
- **`__init__(...)`** -- Instantiates all agents (technique, equipment, fluorophore, organism, software, sample_prep, cell_line, protocol, institution), supplemental agents (PubTator, Ollama), validators (tag dictionary, API, identifier, ROR, ontology), and the role classifier.
- **`process_paper(paper_dict)`** -- Main entry point. Parses the paper into `PaperSections`, runs each agent's `analyze()` on the appropriate sections, merges extractions, applies role classification, validates against the tag dictionary, normalizes identifiers, and assembles the WordPress-compatible output dict.

**Key design decisions:**
- Section-aware: agents receive only relevant sections (Methods for equipment, Title+Abstract for organisms)
- Role classification prevents over-tagging (USED vs REFERENCED vs COMPARED vs NEGATED)
- Local-first validation: uses downloaded lookup tables before falling back to APIs

---

### `pipeline/enrichment.py` -- API Enrichment Engine

**Goal:** Post-extraction enrichment using external APIs.

**Class: `Enricher`**
- Loads API keys from `.env` or environment variables
- **`enrich_batch(papers)`** -- Batch enrichment: OpenAlex + Semantic Scholar batch calls first, then per-paper GitHub/CrossRef/DataCite
- Enrichment targets: institution ROR IDs, citation counts, FWCI, OA status, referenced works, GitHub repo health scores, funder information, dataset links

**API calls:** OpenAlex, Semantic Scholar (batch endpoint), GitHub, CrossRef, DataCite, OpenAIRE

---

### `pipeline/normalization.py` -- Tag Normalization

**Goal:** Map all scraper-produced tag values to canonical forms before validation.

**Key rename dictionaries:**
- `FLUOROPHORE_RENAMES` -- "Alexa 488" to "Alexa Fluor 488", "eGFP" to "EGFP", etc.
- `TECHNIQUE_RENAMES` -- "STED" to "Stimulated Emission Depletion Microscopy" (acronyms to full names)
- `BRAND_RENAMES` -- "Applied Scientific Instrumentation" to "ASI"
- `MODEL_RENAMES` -- "LSM 880" to "Zeiss LSM 880 Confocal" (275+ mappings from bare model names to "Brand Model [Category]" format)
- `SOFTWARE_RENAMES` -- "segment-anything" to "SAM"
- `ORGANISM_RENAMES` -- "Mouse" to "Mus musculus" (all common names to Latin binomial)
- `CELL_LINE_RENAMES` -- "HeLa" to "HeLa (Henrietta Lacks)" (acronyms to full descriptive names)
- `SAMPLE_PREP_RENAMES` -- "CLARITY" to full expansion, "AAV" to "Adeno-Associated Virus"

**Key functions:**
- `normalize_tags(paper)` -- Applies all rename maps to a paper dict, in-place
- `_normalize_objectives(paper)` -- Deduplicates objectives by magnification+NA+immersion
- `_normalize_lasers(paper)` -- Aggressively filters generic laser types, keeps only brand-specific models
- `_clean_organisms(paper)` -- Removes invalid organisms ("Organoid", "Plant"), deduplicates

---

### `pipeline/confidence.py` -- Section-Entity Confidence Matrix

**Goal:** Centralized confidence scores based on *where* in the paper an entity was found.

**Core data structure:** `CONFIDENCE_MATRIX` -- a dict of entity_type to section to confidence_score (0.0-1.0).

**Domain knowledge encoded:**
- Methods section: 0.95 confidence (most reliable for techniques/equipment)
- Introduction/Discussion: 0.25-0.30 (likely background references)
- Title: 0.80-0.95 (depends on entity type; organisms in titles are near-certain)
- Figure captions: 0.75-0.85 (surprisingly rich for equipment info)

**Key function:**
- `get_confidence(entity_label, section)` -- Look up confidence for any entity type in any section.

---

### `pipeline/role_classifier.py` -- Over-Tagging Prevention

**Goal:** Prevent the most common failure in biomedical NLP: tagging every mentioned entity regardless of whether it was actually used.

**4-stage architecture:**

| Stage | What It Does |
|-------|-------------|
| 1. Section weighting | Methods=1.0, Results=0.85, Discussion=0.30, Introduction=0.20 |
| 2. Linguistic signals | Detects usage verbs ("we used X"), reference patterns ("X is commonly used"), citation proximity, negation ("we did not use X"), comparison ("unlike X") |
| 3. Role classification | Assigns USED, REFERENCED, COMPARED, NEGATED, or AMBIGUOUS |
| 4. Document consolidation | One USED in Methods outweighs multiple REFERENCED elsewhere |

**Key classes/functions:**
- `EntityRole` enum -- USED, REFERENCED, COMPARED, NEGATED, AMBIGUOUS
- `ClassifiedExtraction` dataclass -- extraction + role + confidence + signals
- `RoleClassifier.classify_extraction(...)` -- Classify a single mention
- `RoleClassifier.consolidate_roles(...)` -- Document-level dedup and promotion
- `RoleClassifier.filter_used_entities(...)` -- Keep only USED with sufficient confidence
- `RoleClassifier.validate_tagging_distribution(...)` -- Checks for over-tagging (>30% from intro/discussion = warning)

---

### `pipeline/kb_loader.py` -- Microscope Knowledge Base Loader

**Goal:** Singleton module that loads microscopy equipment KB data and provides lookup functions.

**Loads from `microscopy_kb/`:**
- `microscope_kb.json` -- 65+ microscope systems with brand, model, category, techniques, etc.
- `model_aliases.json` -- 518+ aliases (e.g., "LSM 880" to "Zeiss LSM 880")
- `brand_software_map.json` -- Maps brands to their acquisition/analysis software
- `laser_systems.json` -- Laser system specifications

**Key functions:**
- `resolve_alias(text)` -- "LSM 880" to full system dict (exact, fuzzy, substring matching)
- `infer_brand_from_model(model)` -- "SP8" to "Leica"
- `infer_techniques_from_system(model)` -- "Elyra 7" to ["SIM", "PALM", "STORM"]
- `infer_software_from_brand(brand)` -- "Zeiss" to {"acquisition": ["ZEN Blue"], "analysis": [...]}
- `infer_brand_from_software(software)` -- "ZEN Blue" to "Zeiss"
- `is_ambiguous(alias)` -- Checks if alias is a common English word ("fire", "thunder", "mica")
- `has_microscopy_context(text, pos)` -- Checks for microscopy keywords near a position

---

## Extraction Agents (`pipeline/agents/`)

All agents inherit from `BaseAgent` and implement `analyze(text, section) -> List[Extraction]`.

### `base_agent.py` -- Abstract Base

- `Extraction` dataclass -- text, label, start/end offsets, confidence, source_agent, section, metadata
- `BaseAgent.analyze()` -- Abstract method all agents implement
- `BaseAgent._deduplicate()` -- Removes duplicate canonical forms, keeping highest-confidence

### `technique_agent.py` -- Microscopy Technique Extraction

**Detects 60+ microscopy techniques** using strict pattern matching. Abbreviations (STED, TEM, SIM) require immediate microscopy context or their full expansion to avoid false positives. All canonical names use full expanded forms.

Two pattern layers:
1. **Full expansion patterns** -- "stimulated emission depletion" to "Stimulated Emission Depletion Microscopy" (always high confidence)
2. **Abbreviation patterns** -- "STED microscopy" only matches when followed by "microscopy"/"imaging"/"nanoscopy"

### `equipment_agent.py` -- Microscope Brands, Models and Hardware

**Hybrid regex + dictionary + knowledge base approach** for extracting laboratory equipment (no pre-trained NER model exists for this).

Detects:
- **Microscope brands** -- Zeiss, Leica, Nikon, Olympus, Andor, etc. (30+ brands)
- **Microscope models** -- Via KB alias resolution (518+ aliases)
- **Objectives** -- Parsed into structured format (magnification, NA, immersion, brand)
- **Lasers** -- Brand + model extraction (Coherent Chameleon, etc.)
- **Detectors** -- Camera models (Hamamatsu ORCA, Andor iXon, etc.)
- **Filters** -- Emission/excitation filter sets
- **Reagent suppliers** -- Separated from microscope brands (Thermo Fisher, Sigma, etc.)

**Uses `kb_loader` for alias resolution and brand inference (no external API)**

### `fluorophore_agent.py` -- Fluorophore Identification

**Three-layer extraction:**
1. Dictionary matching -- 100+ fluorophores with canonical name normalization (GFP variants, Alexa Fluor, Cy dyes, ATTO dyes, etc.)
2. Regex patterns -- Structured names: "Alexa Fluor NNN", "ATTO NNN", "Hoechst NNNNN"
3. FPbase API validation -- Optional live validation for fluorescent proteins

### `organism_agent.py` -- Organism/Species Recognition

**Strict rule: ONLY Latin names trigger extraction.** Common names ("mouse", "rat") are never matched to prevent false positives from antibody descriptions ("anti-rat", "rabbit polyclonal"). Canonical names always use full scientific binomial (e.g., "Mus musculus").

### `software_agent.py` -- Software Extraction

Separates three categories:
- **Image analysis software** -- ImageJ, Fiji, CellProfiler, Imaris, ilastik, QuPath, napari, etc.
- **Image acquisition software** -- ZEN, LAS X, NIS-Elements, MetaMorph, SlideBook, etc.
- **General-purpose software** -- MATLAB, Python, R, Prism, etc.

### `sample_prep_agent.py` -- Sample Preparation Methods

Detects fixation, tissue clearing (CLARITY, iDISCO, CUBIC), embedding, sectioning, staining/labeling, FISH variants, cell culture techniques. All canonical names use full expanded forms.

### `cell_line_agent.py` -- Cell Line Identification

Detects 50+ cell lines with full descriptive canonical names: "HeLa (Henrietta Lacks)", "Human Embryonic Kidney 293T", etc. Includes immortalized lines, primary cultures, and stem cells.

### `protocol_agent.py` -- Protocol and Repository Detection

Detects:
- **Protocols** -- protocols.io, Nature Protocols, JoVE, STAR Protocols, etc.
- **Data repositories** -- Zenodo, GitHub, Figshare, EMPIAR, IDR, OMERO, etc.
- **RRIDs** -- Research Resource Identifiers (AB_, SCR_, CVCL_, Addgene_)
- **ROR IDs** -- Research Organization Registry identifiers
- **GitHub URLs** -- Extracted and validated

### `institution_agent.py` -- Institution Extraction

Extracts institutions **only from author affiliation strings** (not paper body text). Maps to ROR IDs where known. Pre-loaded dictionary of 50+ major research institutions with ROR IDs.

**API calls:** ROR v2 API (live affiliation matching as fallback)

### `pubtator_agent.py` -- PubTator NER Supplementation

**API call:** NCBI PubTator 3.0 API -- retrieves pre-computed NER annotations for papers with PMIDs. Covers species, chemicals, cell lines, genes, diseases, mutations across 36M+ PubMed abstracts. Supplements regex agents and provides database IDs.

### `ollama_agent.py` -- LLM Cross-Checking (Optional)

Connects to a local Ollama instance to verify/supplement regex results by having a local LLM read the Methods section. Two modes: VERIFY (flag false positives) and EXTRACT (find missed entities). Uses JSON-constrained output and validates suggestions against `MASTER_TAG_DICTIONARY.json`. Gracefully degrades if Ollama is unavailable.

### `openalex_agent.py` -- OpenAlex Enrichment

**API call:** OpenAlex REST API -- A single lookup by DOI returns institution resolution (ROR IDs), author disambiguation, topic classification (4-level hierarchy), citation counts, FWCI, OA status, and referenced works. 240M+ works, CC0-licensed.

### `crossref_agent.py` -- CrossRef + Semantic Scholar Validation

**API calls:** CrossRef API + Semantic Scholar API -- Fills missing journal names, publication dates, license info. Discovers additional data repositories via CrossRef links/relations. Fetches funder information and citation counts.

### `datacite_linker_agent.py` -- Dataset-Publication Linking

**API calls:** DataCite REST API + OpenAIRE ScholeXplorer -- Discovers paper-dataset links. DataCite resolves DOIs (Zenodo, Figshare, Dryad) and traverses `relatedIdentifiers`. OpenAIRE aggregates 40M+ links. Also applies regex for biomedical accession patterns (EMPIAR, EMDB, PDB, GEO, SRA).

### `doi_linker_agent.py` -- Repository URL Validation

Validates extracted repository URLs against paper DOIs:
- **Zenodo:** API query, check `related_identifiers`
- **Figshare:** API query, check related DOIs
- **GitHub:** Check README/CITATION.cff for paper DOI
- **General:** HTTP HEAD liveness check

Assigns validation status: confirmed, probable, unconfirmed, or dead.

### `github_health_agent.py` -- GitHub Repo Health

**API call:** GitHub API -- Checks repo existence, fetches stars/forks/last commit/license/archived status, computes health scores, detects dead/archived repos. Wraps the existing `enrichment.py` logic.

### `rrid_validation_agent.py` -- RRID Validation

**API call:** SciCrunch resolver -- Validates RRIDs against registry, enriches with resource names/types. Cross-references: if RRID resolves to antibody, checks the paper mentions target protein; if software, checks against software tags.

---

## Parsing Modules (`pipeline/parsing/`)

### `section_extractor.py` -- Unified Section Extractor

Central module for acquiring and structuring paper text.

**`PaperSections` dataclass** -- Normalized representation with fields: title, abstract, methods, results, introduction, discussion, full_text, figures, data_availability, sections list.

**Three-tier waterfall strategy:**
1. Europe PMC JATS XML (no PDF processing needed)
2. Unpaywall OA PDF into GROBID processing
3. Abstract-only fallback

**Key functions:**
- `three_tier_waterfall(pmid, pmc_id, doi)` returns `PaperSections`
- `from_pubmed_dict(paper_dict)` returns `PaperSections`
- `heuristic_segment(full_text)` -- Regex-based section detection using heading patterns
- `strip_inline_citations(text)` -- Removes `[1]`, `(Smith et al., 2020)` patterns
- `strip_references(text)` -- Removes the References/Bibliography section entirely

### `europepmc_fetcher.py` -- Europe PMC Fetcher (Tier 1)

**API call:** Europe PMC REST API -- Fetches pre-parsed JATS XML with explicit section tags for 9M+ full-text articles. No API key required. Also provides annotations API for pre-computed entity mentions and PMCID/DOI/PMID mapping.

### `unpaywall_client.py` -- Unpaywall Client (Tier 2)

**API call:** Unpaywall API -- When no PMCID exists, looks up open-access PDF URLs using DOIs. Returns OA location details (version, OA status classification). Rate limit: 100K calls/day.

### `grobid_parser.py` -- GROBID PDF Parser

**API call:** GROBID service (local Docker) -- Converts PDFs into structured section-tagged TEI XML. Parses sections using heading pattern matching (methods, results, introduction, discussion, figures). Falls back gracefully when GROBID is unavailable.

### `pubmed_parser.py` -- PubMed/PMC Parser

**API call:** PubMed E-utilities (efetch) -- Extracts structured sections, metadata, and author affiliations from PubMed XML and PMC NXML full-text articles. Handles the PubMed search workflow used by the scraper.

### `scihub_fetcher.py` -- SciHub Fallback

Last-resort full-text fetcher. Retrieved text is used only for tag extraction (not stored or displayed). Tries multiple SciHub mirrors. Silently returns None if unavailable.

---

## Validation Modules (`pipeline/validation/`)

### `tag_validator.py` -- Master Tag Dictionary Validation

Validates all extracted values against `MASTER_TAG_DICTIONARY.json`. Ensures only canonical tag values make it to export. Provides fuzzy matching for near-misses.

### `api_validator.py` -- Multi-API Validation

Validates tags against authoritative external databases:
- **FPbase** -- fluorescent proteins/dyes
- **SciCrunch** -- RRIDs (antibodies, software, cell lines, plasmids)
- **ROR** -- research organizations
- **NCBI Taxonomy** -- organism names to TaxIDs

All validators are optional -- if an API is unreachable, tags pass through unchanged.

### `identifier_normalizer.py` -- Identifier Canonicalization

Normalizes DOIs, RRIDs, ROR IDs, repository URLs, and accession numbers:
- DOI: strips prefixes to bare `10.xxxx/yyyy`
- RRID: standardizes spacing/casing to `RRID:AB_123456`
- ROR: normalizes URL variants to bare ID
- Repos: normalizes trailing slashes, `.git`, http/https, www
- Accessions: "EMPIAR-10234" vs "EMPIAR 10234" to canonical format

### `ror_v2_client.py` -- ROR v2 API Client

**API call:** ROR v2 API -- Accepts messy affiliation strings, returns best institution match with ROR ID. Uses single-search mode for precision. Validates ROR IDs with checksum. Handles merged/deprecated records.

### `ontology_normalizer.py` -- FBbi Ontology Mapping

**API call:** EBI OLS4 API -- Maps microscopy technique names to FBbi (Biological Imaging methods) ontology term IDs. Maintains a pre-built static mapping plus live API fallback.

### `scicrunch_validator.py` -- SciCrunch RRID Validation

**API call:** SciCrunch API -- Validates RRIDs and retrieves metadata (instrument names, antibody targets, software names). Results are cached.

### `fpbase_validator.py` -- FPbase Fluorescent Protein Validation

**API call:** FPbase API -- Validates fluorophore names and retrieves spectral properties (excitation/emission maxima, quantum yield). Supports local-first validation via `fpbase_name_lookup.json`.

### `cellosaurus_client.py` -- Cellosaurus Cell Line Validation

**API call:** Cellosaurus REST API -- Validates cell line names, retrieves species of origin, disease, cross-references, and Cellosaurus accession IDs (CVCL_xxxx). Covers approximately 150K cell lines.

### `taxonomy_validator.py` -- NCBI Taxonomy Validation

**API call:** NCBI Taxonomy API + PubTator -- Validates organism names against NCBI Taxonomy IDs. Supports local-first validation via `names.dmp`. Pre-mapped dictionary for 17 common organisms.

---

## Export (`pipeline/export/`)

### `json_exporter.py` -- WordPress JSON Exporter

Reads from the SQLite database, optionally re-runs the agent pipeline, and writes chunked JSON files in the exact format WordPress expects. Every field, alias, and boolean flag is preserved identically to prevent upload issues.

**Key features:**
- Protocol classification (Nature Protocols, JoVE, etc.)
- OA status detection
- Dataset repository flagging
- Ambiguous plate reader brand filtering
- Image repository hint detection

---

## Helper / Utility Scripts

### `local_lookup.py` -- Offline Lookup Tables

Pre-downloaded reference databases for offline/local-first validation. Eliminates API calls for common lookups. Covers FPbase proteins, Cellosaurus cell lines, NCBI taxonomy, ROR institutions, FBbi ontology terms.

### `download_lookup_data.py` -- Lookup Data Downloader

Downloads and prepares all local lookup tables from their sources (FPbase, Cellosaurus, NCBI, ROR, FBbi). Run once to set up offline validation.

### `fix_figure_urls.py` -- Figure URL Fixer

Post-processing utility that fixes or updates figure image URLs in the exported JSON.

### `test_kb_integration.py` -- KB Integration Tests

Test suite that validates the knowledge base integration: checks that aliases resolve correctly, brands infer properly, and techniques map as expected.

---

## Knowledge Base Builders

### `microscopy_kb/build_microscope_kb.py` -- Equipment KB Builder

Compiles a structured microscopy equipment knowledge base from scratch. Outputs:
- `microscope_kb.json` -- 65+ systems with brand, model, category, techniques, detectors, objectives
- `brand_software_map.json` -- Brand to acquisition/analysis software mappings
- `model_aliases.json` -- 518+ model aliases for fuzzy matching

### `fpbase/_query.py` -- FPbase GraphQL Export

Exports all FPbase fluorescent proteins via their GraphQL API. Retrieves name, aliases, spectral properties (excitation/emission maxima, quantum yield, extinction coefficient), chromophore info.

### `fbbi_ontology/_parse_obo.py` -- FBbi Ontology Parser

Parses the FBbi OBO (Open Biomedical Ontology) file into a JSON lookup table. Extracts term IDs, names, synonyms, hierarchical relationships.

---

## Data Flow Summary

```
PubMed Search
    |
    v
1_scrape.py ------> microhub.db (SQLite)
    |                  Papers with: title, abstract, DOI, PMID, full_text
    |
    v
2_export.py ------> raw_export/*_chunk_*.json
    |                  Raw DB dump in WordPress format
    |
    v
2b_segment.py ----> segmented_export/*_chunk_*.json
    |                  Papers with _segmented_methods, _segmented_results, etc.
    |
    v
3_clean.py -------> cleaned_export/*_chunk_*.json
                       |
                       |-- Agent extraction (9 regex agents + PubTator + optional Ollama)
                       |-- Role classification (USED vs REFERENCED filtering)
                       |-- Tag normalization (canonical forms)
                       |-- Tag validation (MASTER_TAG_DICTIONARY.json)
                       |-- API enrichment (OpenAlex, S2, GitHub, CrossRef, DataCite, ROR)
                       |-- Identifier normalization (DOIs, RRIDs, RORs, URLs)
                       |-- Ontology mapping (FBbi terms)
                       |-- Finalization (booleans, protocol classification, field cleanup)
```

## Per-Paper Output Fields

The final JSON for each paper includes:

| Field | Source |
|-------|--------|
| `title`, `abstract`, `doi`, `pmid`, `pmc_id` | PubMed/scraper |
| `microscopy_techniques` | technique_agent |
| `microscope_brands`, `microscope_models` | equipment_agent |
| `objectives`, `lasers`, `detectors`, `filters` | equipment_agent |
| `fluorophores` | fluorophore_agent |
| `organisms` | organism_agent |
| `cell_lines` | cell_line_agent |
| `image_analysis_software`, `image_acquisition_software` | software_agent |
| `sample_preparation` | sample_prep_agent |
| `protocols`, `repositories`, `rrids` | protocol_agent |
| `institutions`, `ror_ids` | institution_agent + ROR v2 |
| `github_tools` | github_health_agent |
| `citation_count`, `fwci` | OpenAlex/S2 |
| `is_open_access`, `oa_status` | Unpaywall/OpenAlex |
| `is_protocol` | Protocol classification |
| `has_dataset` | DataCite/OpenAIRE + text mining |
| `fbbi_ids` | ontology_normalizer |
| `tag_source` | "methods" or "title_abstract" |
