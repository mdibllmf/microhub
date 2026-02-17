# MicroHub Data Pipeline Misalignment Report

**Generated:** 2026-01-05
**Components Analyzed:**
- `microhub_scraper.py` (v5.0)
- `cleanup_and_retag.py` (v3.1)
- `microhub_export_json_v4.1.py` (v5.1)
- `files27/microhub-plugin-v4.2/microhub-plugin/admin/admin-import.php`
- `files27/microhub-plugin-v4.2/microhub-plugin/includes/class-microhub-taxonomies.php`

---

## Summary

| Category | Status | Issues Found |
|----------|--------|--------------|
| Microscopy Techniques | Good | None |
| Microscope Brands | Good | None |
| Microscope Models | Minor | Cleanup script missing canonical mappings |
| Image Analysis Software | Good | None |
| Image Acquisition Software | Minor | Not extracted by cleanup script |
| Fluorophores | Good | None |
| Organisms | Good | None |
| Cell Lines | Good | None |
| Sample Preparation | Good | None |
| Institutions/Facilities | Good | Working correctly with v3.1 fix |
| Protocol Detection | Good | Working correctly |
| Repositories | Good | None |
| RRIDs | Good | None |
| RORs | Good | Looked up from institution names |

**Overall Status:** Pipeline is well-aligned. Minor improvements suggested below.

---

## 1. Tags in Scraper NOT Being Normalized in Cleanup

### Image Acquisition Software
**Issue:** The scraper extracts `IMAGE_ACQUISITION_SOFTWARE` but the cleanup script doesn't have a separate canonical mapping for it.

**Scraper (`microhub_scraper.py` lines ~1222-1245):**
```python
IMAGE_ACQUISITION_SOFTWARE = {
    'ZEN': [...],
    'NIS-Elements': [...],
    'LAS X': [...],
    ...
}
```

**Cleanup:** Uses `SOFTWARE_CANONICAL` which covers analysis software but not all acquisition software.

**Impact:** Low - most acquisition software overlaps with analysis software names.

**Fix:** Add acquisition software entries to `SOFTWARE_CANONICAL` in cleanup_and_retag.py if needed.

---

### Microscope Models
**Issue:** The scraper has comprehensive `MICROSCOPE_MODELS` dictionary but cleanup doesn't have a canonical mapping for models.

**Impact:** Low - model names are generally unique and don't need normalization.

**Recommendation:** No action required unless case-sensitivity issues arise.

---

## 2. Normalized Tags NOT Being Exported in JSON

**Status:** All normalized tags ARE being exported correctly.

The export script (`microhub_export_json_v4.1.py`) exports all tag categories:
- `microscopy_techniques` ✓
- `microscope_brands` ✓
- `microscope_models` ✓
- `image_analysis_software` ✓
- `image_acquisition_software` ✓
- `fluorophores` ✓
- `organisms` ✓
- `cell_lines` ✓
- `sample_preparation` ✓
- `institutions` ✓
- `affiliations` ✓
- `protocols` ✓
- `repositories` ✓
- `rrids` ✓
- `rors` ✓

---

## 3. JSON Fields NOT Being Imported into WordPress

**Status:** All major fields ARE being imported correctly.

The import script (`admin-import.php`) handles:

| JSON Field | WP Taxonomy | WP Meta Key | Status |
|------------|-------------|-------------|--------|
| `microscopy_techniques` | `mh_technique` | - | ✓ |
| `microscope_brands` | `mh_microscope` | `_mh_microscope_brands` | ✓ |
| `microscope_models` | `mh_microscope_model` | `_mh_microscope_models` | ✓ |
| `image_analysis_software` | `mh_analysis_software` | `_mh_image_analysis_software` | ✓ |
| `image_acquisition_software` | `mh_acquisition_software` | `_mh_image_acquisition_software` | ✓ |
| `fluorophores` | `mh_fluorophore` | `_mh_fluorophores` | ✓ |
| `organisms` | `mh_organism` | - | ✓ |
| `cell_lines` | `mh_cell_line` | `_mh_cell_lines` | ✓ |
| `sample_preparation` | `mh_sample_prep` | `_mh_sample_preparation` | ✓ |
| `institutions` | `mh_facility` | `_mh_institutions` | ✓ |
| `protocols` | - | `_mh_protocols` | ✓ |
| `repositories` | - | `_mh_repositories` | ✓ |
| `rrids` | - | `_mh_rrids` | ✓ |
| `rors` | - | `_mh_rors` | ✓ |
| `protocol_type` | `mh_protocol_type` | `_mh_protocol_type` | ✓ |

---

## 4. WordPress Taxonomies with NO Corresponding Scraper Extraction

**Status:** All registered taxonomies have data sources.

| WordPress Taxonomy | Scraper Source | Status |
|--------------------|----------------|--------|
| `mh_technique` | `MICROSCOPY_TECHNIQUES` | ✓ |
| `mh_microscope` | `MICROSCOPE_BRANDS` | ✓ |
| `mh_microscope_model` | `MICROSCOPE_MODELS` | ✓ |
| `mh_organism` | `ORGANISM_KEYWORDS` | ✓ |
| `mh_software` | Legacy, redirects to analysis/acquisition | ✓ |
| `mh_analysis_software` | `IMAGE_ANALYSIS_SOFTWARE` | ✓ |
| `mh_acquisition_software` | `IMAGE_ACQUISITION_SOFTWARE` | ✓ |
| `mh_sample_prep` | `SAMPLE_PREPARATION` | ✓ |
| `mh_fluorophore` | `FLUOROPHORES` | ✓ |
| `mh_cell_line` | `CELL_LINE_KEYWORDS` | ✓ |
| `mh_facility` | `INSTITUTION_PATTERNS` + `KNOWN_INSTITUTIONS` | ✓ |
| `mh_protocol_type` | `PROTOCOL_JOURNALS` | ✓ |

---

## 5. Mismatched Field Names Between Components

### Resolved Issues

#### Citation Count
- Scraper uses: `citation_count`
- Export uses: Both `citation_count` and `citations` (alias)
- Import handles: Both `citations` and `citation_count`
- **Status:** ✓ Resolved - import checks both field names

#### PMC ID
- Scraper uses: `pmc_id`
- Export uses: `pmc_id`
- Import uses: Stored in `_mh_pmc_id` (but only from top-level field)
- **Status:** ✓ Working

#### PMID
- Scraper uses: `pmid`
- Export uses: `pmid`
- Import stores as: `_mh_pubmed_id`
- **Status:** ✓ Working

---

## 6. Protocol Detection Alignment

### Protocol Journals List
All three components now have aligned protocol journal detection:

**Scraper (`PROTOCOL_PATTERNS` + is_protocol logic):**
- JoVE, Nature Protocols, STAR Protocols, Bio-protocol
- Current Protocols, Methods in Molecular Biology
- Cold Spring Harbor Protocols, MethodsX

**Cleanup (`PROTOCOL_JOURNALS` patterns):**
- Same list with regex patterns

**Import (`protocol_journal_map`):**
- Same list with string matching

**Status:** ✓ Aligned

### Protocol Detection Flow
1. Scraper extracts protocol URLs from text via `PROTOCOL_PATTERNS`
2. Cleanup identifies protocol papers via `PROTOCOL_JOURNALS` patterns
3. Cleanup sets `is_protocol`, `protocol_type`, `post_type`
4. Export preserves these fields
5. Import sets `mh_protocol_type` taxonomy and `_mh_is_protocol` meta

---

## 7. Institution/Facility Extraction

### Current Implementation (v3.1)
**Status:** ✓ Fixed and working correctly

**Cleanup script behavior:**
- Extracts institutions from `affiliations` field ONLY
- Does NOT extract from abstract, methods, or full_text
- Uses `KNOWN_INSTITUTIONS` dictionary for canonical names
- Looks up ROR IDs from `INSTITUTION_ROR_IDS`

**Data Flow:**
1. Scraper extracts `affiliations` from PubMed XML (author affiliations)
2. Cleanup extracts `institutions` from affiliations only
3. Export includes both `affiliations` and `institutions`
4. Import sets `mh_facility` taxonomy from institutions

---

## 8. URL Generation Consistency

### DOI URLs
- Scraper: `https://doi.org/{doi}` via `normalize_doi()`
- Export: Stored as `doi_url`
- Import: Stored in `_mh_doi` (raw DOI, not URL)
- Theme should generate: `https://doi.org/` + DOI

### PubMed URLs
- Scraper: `https://pubmed.ncbi.nlm.nih.gov/{pmid}/`
- Stored in: `pubmed_url`
- **Status:** ✓ Consistent

### PMC URLs
- Scraper: `https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/`
- Stored in: `pmc_url`
- **Status:** ✓ Consistent

---

## 9. Recommendations

### High Priority

None - pipeline is well-aligned.

### Medium Priority

1. **Add acquisition software to cleanup canonical mapping**
   - File: `cleanup_and_retag.py`
   - Add entries for acquisition-specific software to `SOFTWARE_CANONICAL`

### Low Priority

1. **Consider adding microscope model canonical mapping**
   - Only needed if case inconsistencies are found in data

2. **Document the full data flow**
   - Create a flowchart showing scraper → cleanup → export → import → display

---

## 10. Field Name Quick Reference

| Data Point | Scraper DB Column | Cleanup Field | Export JSON | WP Meta Key | WP Taxonomy |
|------------|-------------------|---------------|-------------|-------------|-------------|
| Paper title | title | title | title | post_title | - |
| DOI | doi | doi | doi | _mh_doi | - |
| PMID | pmid | pmid | pmid | _mh_pubmed_id | - |
| PMC ID | pmc_id | pmc_id | pmc_id | _mh_pmc_id | - |
| Year | year | year | year | _mh_publication_year | - |
| Citations | citation_count | citation_count | citation_count, citations | _mh_citation_count | - |
| Abstract | abstract | abstract | abstract | _mh_abstract | - |
| Techniques | microscopy_techniques | microscopy_techniques | microscopy_techniques | - | mh_technique |
| Brands | microscope_brands | microscope_brands | microscope_brands | _mh_microscope_brands | mh_microscope |
| Models | microscope_models | microscope_models | microscope_models | _mh_microscope_models | mh_microscope_model |
| Analysis SW | image_analysis_software | image_analysis_software | image_analysis_software | _mh_image_analysis_software | mh_analysis_software |
| Acquisition SW | image_acquisition_software | - | image_acquisition_software | _mh_image_acquisition_software | mh_acquisition_software |
| Fluorophores | fluorophores | fluorophores | fluorophores | _mh_fluorophores | mh_fluorophore |
| Organisms | organisms | organisms | organisms | - | mh_organism |
| Cell Lines | cell_lines | cell_lines | cell_lines | _mh_cell_lines | mh_cell_line |
| Sample Prep | sample_preparation | sample_preparation | sample_preparation | _mh_sample_preparation | mh_sample_prep |
| Affiliations | affiliations | affiliations | affiliations | _mh_affiliations | - |
| Institutions | - | institutions | institutions | _mh_institutions | mh_facility |
| Protocols | protocols | protocols | protocols | _mh_protocols | - |
| Protocol Type | - | protocol_type | protocol_type | _mh_protocol_type | mh_protocol_type |
| Is Protocol | - | is_protocol | is_protocol | _mh_is_protocol | - |
| Repositories | repositories | repositories | repositories | _mh_repositories | - |
| GitHub URL | github_url | github_url | github_url | _mh_github_url | - |
| RRIDs | rrids | rrids | rrids | _mh_rrids | - |
| RORs | rors | rors | rors | _mh_rors | - |

---

## Conclusion

The MicroHub data pipeline is **well-aligned** across all components. The v3.1 cleanup script fix correctly addresses the institution extraction issue. All major tag categories flow properly from scraper through cleanup, export, import, and display.

The pipeline supports:
- 60+ microscopy techniques
- 40+ microscope brands
- 50+ microscope models
- 55+ software packages
- 110+ fluorophores
- 20+ organisms
- 20+ cell lines
- 50+ sample preparation methods
- Protocol detection from 10+ journal types
- 20+ repository types
- RRID and ROR identifier extraction
- Institution extraction from author affiliations
