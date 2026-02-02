# MicroHub WordPress Plugin v3.0

A comprehensive microscopy paper database with full text access, figures, protocols, and data repositories.

## Installation

1. Upload the `microhub-v3` folder to `/wp-content/plugins/`
2. Rename it to `microhub`
3. Activate the plugin through the 'Plugins' menu in WordPress
4. Go to **MicroHub > Settings** to view statistics

### For Excel Import
To import Excel files, install PhpSpreadsheet:
```bash
cd /path/to/wordpress
composer require phpoffice/phpspreadsheet
```

Or use JSON format (no additional dependencies).

## Importing Papers

1. Go to **MicroHub > Import Papers**
2. Upload your Excel (.xlsx) or JSON file
3. Configure import options
4. Click "Import Papers"

## Supported Taxonomies

- Microscopy Techniques
- Microscope Brands
- Microscope Models  
- Analysis Software
- Sample Preparation
- Fluorophores
- Organisms
- Protocol Sources
- Data Repositories
- Journals

## Excel Column Names

The importer recognizes these column names (case-insensitive):

- `title` - Paper title (required)
- `abstract` - Paper abstract
- `methods` - Methods section
- `doi` - Digital Object Identifier
- `pmid` or `pubmed_id` - PubMed ID
- `pmc_id` - PubMed Central ID
- `authors` - Author list
- `journal` - Journal name
- `year` - Publication year
- `citations` - Citation count
- `github_url` - GitHub repository URL
- `microscopy_techniques` - Pipe-separated techniques
- `microscope_brands` - Pipe-separated brands
- `analysis_software` - Pipe-separated software
- `sample_preparation` - Pipe-separated methods
- `fluorophores` - Pipe-separated fluorophores
- `organisms` - Pipe-separated organisms

## License

GPL v2 or later
