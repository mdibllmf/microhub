# MicroHub WordPress Plugin v3.0

A comprehensive microscopy paper database with full text access, figures, protocols, and data repositories.

## What's New in v3.0

### Full Text Access
- Accesses complete papers via PubMed Central (not just abstracts)
- Extracts full Methods sections from papers
- Captures figure images and captions

### New Taxonomies
- **Microscopy Techniques** - STED, STORM, Confocal, Light Sheet, etc.
- **Microscope Brands** - Zeiss, Leica, Nikon, Olympus, etc.
- **Microscope Models** - LSM 880, SP8, A1R, etc.
- **Analysis Software** - Fiji, CellProfiler, Imaris, StarDist, etc.
- **Acquisition Software** - ZEN, NIS-Elements, MetaMorph, etc.
- **Sample Preparation** - Tissue clearing, FISH, cryosectioning, etc.
- **Fluorophores** - DAPI, Alexa dyes, GFP, mCherry, etc.
- **Organisms** - Mouse, Human, Zebrafish, Drosophila, etc.
- **Protocol Sources** - protocols.io, Bio-protocol, JoVE, etc.
- **Data Repositories** - Zenodo, Figshare, IDR, EMPIAR, etc.

### New Fields
- Full methods text
- Figure images and captions
- Supplementary materials
- PMC URL for open access
- Antibodies/RRIDs

## Installation

1. Upload the `microhub` folder to `/wp-content/plugins/`
2. Activate the plugin through the 'Plugins' menu in WordPress
3. Go to **MicroHub > Settings** to configure

### For Excel Import (Optional)
To import Excel files, install PhpSpreadsheet:
```bash
cd /path/to/wordpress
composer require phpoffice/phpspreadsheet
```

Or use JSON format for imports (no additional dependencies).

## Importing Papers

### From the v3 Scraper (Excel)
1. Run the scraper: `python microhub_scraper_v3.py`
2. Export to Excel: `python microhub_export_excel_v3.py`
3. Go to **MicroHub > Import Papers** in WordPress
4. Upload the Excel file and configure import options
5. Click "Import Papers"

### Import Options
- **Skip existing papers** - Don't reimport papers already in database
- **Update existing** - Update papers with new data
- **Full text only** - Only import papers with full text available
- **With figures only** - Only import papers that have figures

## Excel Column Mapping

| Excel Column | WordPress Field | Type |
|-------------|-----------------|------|
| Title | post_title | Required |
| Abstract | _mh_abstract | Text |
| Methods | _mh_methods | Text |
| PMID | _mh_pubmed_id | Text |
| DOI | _mh_doi | Text |
| PMC ID | _mh_pmc_id | Text |
| Authors | _mh_authors | Text |
| Journal | _mh_journal + taxonomy | Text |
| Year | _mh_publication_year | Number |
| Citations | _mh_citation_count | Number |
| Microscopy Techniques | mh_technique taxonomy | Pipe-separated |
| Microscope Brands | mh_microscope_brand taxonomy | Pipe-separated |
| Microscope Models | mh_microscope_model taxonomy | Pipe-separated |
| Image Analysis Software | mh_analysis_software taxonomy | Pipe-separated |
| Image Acquisition Software | mh_acquisition_software taxonomy | Pipe-separated |
| Sample Preparation | mh_sample_prep taxonomy | Pipe-separated |
| Fluorophores | mh_fluorophore taxonomy | Pipe-separated |
| Organisms | mh_organism taxonomy | Pipe-separated |
| Protocols | _mh_protocols | JSON |
| Repositories | _mh_repositories | JSON |
| RRIDs | _mh_rrids | JSON |
| Figure URLs | _mh_figures | JSON |
| GitHub URL | _mh_github_url | URL |

## REST API

The plugin provides a REST API for accessing paper data:

### Endpoints

- `GET /wp-json/microhub/v1/papers` - List papers
- `GET /wp-json/microhub/v1/papers/{id}` - Get single paper
- `GET /wp-json/microhub/v1/taxonomy/{taxonomy}` - Get taxonomy terms
- `GET /wp-json/microhub/v1/stats` - Get statistics

### Query Parameters

```
/wp-json/microhub/v1/papers?
  search=confocal
  &technique=confocal
  &organism=mouse
  &has_full_text=1
  &has_figures=1
  &has_protocols=1
  &per_page=20
  &page=1
```

## Shortcodes

```php
// Paper browser with filters
[microhub_papers]

// Paper count statistics
[microhub_stats]

// Featured papers
[microhub_featured limit="5"]

// Papers by technique
[microhub_by_technique technique="confocal" limit="10"]
```

## Template Customization

Override templates by copying to your theme:
- `single-mh_paper.php` - Single paper view
- `archive-mh_paper.php` - Paper archive/browse

## Support

For issues or feature requests, please contact the development team.

## License

GPL v2 or later
