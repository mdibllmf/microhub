# MicroHub Complete Data Flow

## Overview
This document explains how data flows from the Python scraper → JSON → WordPress Plugin → Theme Display.

---

## 1. SCRAPER OUTPUT (v5 Format)

The scraper produces JSON with these tag arrays:

```json
{
  "title": "Paper Title",
  "microscopy_techniques": ["Confocal", "STED", "Super-Resolution"],
  "microscope_brands": ["Zeiss", "Leica"],
  "microscope_models": ["LSM 880"],
  "image_analysis_software": ["Fiji", "ImageJ"],
  "fluorophores": ["GFP", "mCherry"],
  "organisms": ["Mouse", "Human"],
  "cell_lines": ["HeLa", "U2OS"],
  "sample_preparation": ["PFA fixation", "Immunostaining"],
  "full_text": "...",
  ...
}
```

---

## 2. PLUGIN IMPORT (admin-import.php)

The plugin stores data in TWO places for maximum compatibility:

### A. WordPress Taxonomies (for filtering/archives)

| JSON Field | Taxonomy | Slug |
|------------|----------|------|
| `microscopy_techniques` | `mh_technique` | /technique/sted/ |
| `microscope_brands` | `mh_microscope` | /microscope/zeiss/ |
| `microscope_models` | `mh_microscope_model` | /microscope-model/lsm-880/ |
| `image_analysis_software` | `mh_analysis_software` + `mh_software` | /software/fiji/ |
| `organisms` | `mh_organism` | /organism/mouse/ |
| `fluorophores` | `mh_fluorophore` | /fluorophore/gfp/ |
| `cell_lines` | `mh_cell_line` | /cell-line/hela/ |
| `sample_preparation` | `mh_sample_prep` | /sample-prep/pfa-fixation/ |

### B. Post Meta (JSON for theme/backup)

| JSON Field | Meta Key |
|------------|----------|
| `microscope_brands` | `_mh_microscope_brands` |
| `microscope_models` | `_mh_microscope_models` |
| `image_analysis_software` | `_mh_image_analysis_software` |
| `fluorophores` | `_mh_fluorophores` |
| `cell_lines` | `_mh_cell_lines` |
| `sample_preparation` | `_mh_sample_preparation` |
| `full_text` | `_mh_full_text` |
| `methods` | `_mh_methods` |
| `rrids` | `_mh_rrids` |
| `antibodies` | `_mh_antibodies` |

---

## 3. THEME TAG COLLECTION (functions.php → mh_get_paper_tags)

The theme collects tags from ALL sources:

```php
// Check ALL 10 taxonomies
$taxonomy_to_css = array(
    'mh_technique'           => 'technique',
    'mh_microscope'          => 'microscope',
    'mh_organism'            => 'organism',
    'mh_software'            => 'software',
    'mh_microscope_model'    => 'microscope',
    'mh_analysis_software'   => 'software',
    'mh_acquisition_software'=> 'software',
    'mh_sample_prep'         => 'sample_prep',
    'mh_fluorophore'         => 'fluorophore',
    'mh_cell_line'           => 'cell_line',
);

// Also check meta fields as backup
$meta_to_css = array(
    '_mh_fluorophores'             => 'fluorophore',
    '_mh_cell_lines'               => 'cell_line',
    '_mh_sample_preparation'       => 'sample_prep',
    '_mh_microscope_brands'        => 'microscope',
    ...
);
```

---

## 4. THEME DISPLAY (style.css)

### CSS Class Mapping

| Tag Type | CSS Class | Color |
|----------|-----------|-------|
| Technique | `.mh-text-tag-technique` | Green |
| Microscope | `.mh-text-tag-microscope` | Blue |
| Organism | `.mh-text-tag-organism` | Purple |
| Software | `.mh-text-tag-software` | Orange |
| Fluorophore | `.mh-text-tag-fluorophore` | Teal |
| Sample Prep | `.mh-text-tag-sample_prep` | Yellow |
| Cell Line | `.mh-text-tag-cell_line` | Pink |
| RRID | `.mh-text-tag-rrid` | Purple |
| Antibody | `.mh-text-tag-antibody` | Red |

---

## 5. FULL TEXT HIGHLIGHTING (functions.php → mh_highlight_tags_in_text)

```php
// For each tag found in the paper
foreach ($tags as $tag) {
    // Generate CSS class: mh-text-tag mh-text-tag-{type}
    $class = 'mh-text-tag mh-text-tag-' . $tag['taxonomy'];
    
    // Create HTML span
    $html = '<span class="' . $class . '">' . $tag['name'] . '</span>';
    
    // Replace in text using placeholder system
    // (prevents nested/broken replacements)
}
```

---

## 6. COMMON ISSUES & FIXES

### Issue: Tags not highlighting
**Cause**: Theme only checked 4 taxonomies, plugin registers 10
**Fix**: Updated `mh_get_paper_tags` to check all 10 taxonomies

### Issue: Raw HTML showing in text
**Cause**: Tag names in URLs caused nested replacements
**Fix**: Two-pass placeholder system in `mh_highlight_tags_in_text`

### Issue: "Technique Microscope Organism Software" header
**Cause**: Garbage text in scraped full_text
**Fix**: Cleanup pattern in theme before display

### Issue: Tags not in sidebar
**Cause**: Only showing 4 taxonomy types
**Fix**: Added Fluorophores, Cell Lines, Sample Prep, Brands to sidebar

---

## 7. INSTALLATION ORDER

1. **Install Plugin** (microhub-plugin-v3_5.zip)
   - Registers all 10 taxonomies
   - Enables JSON import

2. **Install Theme** (microhub-theme-v4_2.zip)
   - Provides display templates
   - Tag highlighting CSS

3. **Import Data** (MicroHub → Import)
   - Upload cleaned JSON
   - Creates posts with taxonomy terms + meta

4. **Verify**
   - Check paper page shows all tag types in sidebar
   - Check full text highlights tags in colors

---

## 8. FILE VERSIONS

| Component | Version | File |
|-----------|---------|------|
| Plugin | 3.5.0 | microhub-plugin-v3_5.zip |
| Theme | 4.2.0 | microhub-theme-v4_2.zip |
| Scraper | 5.4 | microhub_scraper_v5_4.zip |
