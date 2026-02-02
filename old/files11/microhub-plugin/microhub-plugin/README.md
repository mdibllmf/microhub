# MicroHub v3.0.0 - Comprehensive Metadata Update

## What's New in v3.0

### Enhanced Import for Scraper v4.1 Data
The importer now fully supports all fields from the Python scraper v4.1:

**New Metadata Fields:**
- **Fluorophores** - GFP, mCherry, GCaMP, Alexa dyes, calcium indicators, voltage sensors (200+ detected)
- **Sample Preparation** - CLARITY, iDISCO, cryosectioning, organoid culture, transfection methods
- **Cell Lines** - HeLa, HEK293, U2OS, primary cultures, iPSCs, etc.
- **Figures** - Full figure metadata with captions and image URLs
- **Methods** - Complete methods section text from PMC full text
- **Full Text** - Full article text when available from PMC

**Additional Microscopy Details:**
- Imaging modalities
- Staining methods
- Lasers, detectors, objectives, filters
- Embedding methods, fixation methods, mounting media

### Dual Storage System
All categorized data is now stored as BOTH:
1. **WordPress Taxonomies** - For native filtering and archive pages
2. **JSON Meta Fields** - For theme compatibility and advanced filtering

This ensures the data works with both the plugin's built-in features AND the MicroHub Theme v3.3's advanced filters.

### Theme Compatibility
Works seamlessly with MicroHub Theme v3.3 which provides:
- Advanced filter dropdowns for fluorophores, sample prep, cell lines, brands, software
- Color-coded fluorophore tags on paper pages
- Figure grids with thumbnails
- Expandable methods sections

---

## What's New in v2.7

### 1. Admin Review Interface
**Location:** WordPress Admin → MicroHub → Review Papers

- **Quick Review Dashboard** - See all papers with their taxonomy tags at a glance
- **Filter by Missing Data** - Find papers missing techniques, software, organisms, or microscopes
- **Quick Edit** - Edit tags directly from the review page without loading full editor
- **Statistics Bar** - See coverage stats for each taxonomy type

### 2. Bulk Edit Tools
**Location:** WordPress Admin → MicroHub → Bulk Edit

- **Add Tags by Search** - Add taxonomy terms to all papers matching a search query
- **Rename/Merge Terms** - Fix duplicate terms (e.g., merge "AFM" and "Atomic Force Microscopy")
- **Terms Overview** - See all current terms and their usage counts

### 3. Modular Shortcodes
Build your own page layouts using individual components:

```
[microhub_hero title="MicroHub" subtitle="Research Repository" show_stats="yes"]
[microhub_search_bar placeholder="Search papers..."]
[microhub_filters show="technique,software,organism,microscope,year"]
[microhub_quick_filters show="foundational,high_impact,has_protocols,has_github"]
[microhub_results_grid per_page="24" layout="grid"]
[microhub_pagination]
[microhub_stats_bar layout="horizontal"]
[microhub_taxonomy_cloud taxonomy="mh_technique" limit="30"]
[microhub_featured_papers count="3" min_citations="100"]
[microhub_recent_papers count="5"]
[microhub_top_cited count="10"]
[microhub_ai_chat position="inline"]
```

### 4. Data Cleaning Script
**File:** `clean_export_data.py`

Run this BEFORE importing to WordPress to properly categorize:
- **Techniques** - Only actual microscopy methods (Confocal, STED, etc.)
- **Software** - Image analysis tools (ImageJ, CellProfiler, etc.)
- **Organisms** - Model systems (Mouse, Human, Zebrafish, etc.)
- **Microscopes** - Correct brand attribution (Nikon, Zeiss, Leica, etc.)

```bash
python clean_export_data.py papers_export.json papers_cleaned.json
```

---

## Complete Shortcode Reference

### Hero Section
`[microhub_hero title="" subtitle="" show_stats="yes" background=""]`

### Search Bar
`[microhub_search_bar placeholder="Search papers..." button_text="Search"]`

### Filters
`[microhub_filters show="technique,software,organism,microscope,year,citations" layout="horizontal"]`

### Quick Filters
`[microhub_quick_filters show="foundational,high_impact,has_protocols,has_github,has_data"]`

### Results Grid
`[microhub_results_grid per_page="24" layout="grid"]`

### Pagination
`[microhub_pagination]`

### Statistics
`[microhub_stats_bar show="papers,techniques,software,organisms,microscopes"]`
`[microhub_stats_cards columns="4"]`
`[microhub_enrichment_stats]`

### Taxonomy Cloud
`[microhub_taxonomy_cloud taxonomy="mh_technique" limit="30" show_count="yes"]`

### Paper Lists
`[microhub_featured_papers count="3" min_citations="100"]`
`[microhub_recent_papers count="5"]`
`[microhub_top_cited count="10"]`

### Interactive
`[microhub_ai_chat position="inline"]`
`[microhub_upload_form type="paper"]`

---

## Microscope Brand Detection

| Detected Term | Correct Brand | Model |
|---------------|---------------|-------|
| N-SIM | Nikon | N-SIM |
| Ti-E | Nikon | Ti-E |
| LSM 880 | Zeiss | LSM 880 |
| Airyscan | Zeiss | Airyscan |
| SP8 | Leica | SP8 |
| Stellaris | Leica | Stellaris |
| FV3000 | Olympus | FV3000 |
| DeltaVision | GE Healthcare | DeltaVision |

---

## Installation

1. Delete existing `microhub` folder in `/wp-content/plugins/`
2. Upload and extract `microhub-v2.7-complete.zip`
3. Clean your export data: `python clean_export_data.py input.json output.json`
4. Re-import using MicroHub → Import Papers
5. Use MicroHub → Review Papers to check and edit tags
6. Use MicroHub → Bulk Edit to merge duplicate terms
