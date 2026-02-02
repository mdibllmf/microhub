# MicroHub Theme v3.3

Complete WordPress theme for the MicroHub microscopy research platform.

## Features

- **Paper Display**: Full support for all plugin metadata (DOI, PubMed, citations, authors, journal, etc.)
- **Clickable Authors**: Authors are clickable links that show all papers by that author
- **Last Author Highlighting**: Last authors are visually highlighted on paper pages
- **Dynamic Filters**: Filter dropdowns populated directly from your database taxonomy terms
- **Advanced Filter Dropdowns**: Filter by fluorophores, sample preparation, cell lines, microscope brands, and analysis software
- **Protocols**: Display protocols from protocols.io, Nature Protocols, Bio-protocol, etc.
- **GitHub Integration**: Code repository cards with direct links
- **Data Repositories**: Links to Zenodo, Figshare, IDR, OMERO, EMPIAR, BioImage Archive
- **RRIDs**: Research Resource Identifiers with SciCrunch links and quick filter
- **Fluorophores**: Display fluorescent proteins, dyes, and indicators with color-coded tags
- **Sample Preparation**: Show tissue clearing, sectioning, and other prep methods
- **Cell Lines**: Display cell line information
- **Figures**: Display paper figures with thumbnails and captions
- **Methods Section**: Show full methods text with expandable view
- **Facility Info**: Imaging facility display
- **Gemini AI Chat**: Global AI assistant on all pages
- **Responsive Design**: Mobile-first, dark theme
- **Editable Page Templates**: Edit page content directly in WordPress

## Requirements

- WordPress 5.8+
- MicroHub Plugin (active)
- Gemini API key (optional, for AI chat)

## Installation

1. Upload `microhub-theme.zip` via Appearance → Themes → Add New → Upload Theme
2. Click "Activate"
3. Keep the MicroHub plugin active

## What's New in v3.3

### Advanced Filter Dropdowns
New collapsible "Advanced Filters" section with dropdowns for:
- **Fluorophores**: Filter by GFP, mCherry, GCaMP, Alexa dyes, and 100+ fluorescent markers
- **Sample Preparation**: Filter by CLARITY, iDISCO, cryosectioning, organoid culture, etc.
- **Cell Lines**: Filter by HeLa, HEK293, U2OS, primary cultures, iPSCs, etc.
- **Microscope Brands**: Filter by Zeiss, Leica, Nikon, Olympus, etc.
- **Analysis Software**: Filter by Fiji, CellProfiler, Imaris, RELION, etc.

### Enhanced Paper Cards
Paper cards now show badges with tooltips for:
- 🧬 Fluorophores count (with list on hover)
- 🧫 Sample preparation methods count
- 🔬 Cell lines count
- 📊 Figure count

## What's New in v3.2

### Comprehensive Metadata Support
Full support for all scraper v4.1 fields:
- **Fluorophores & Dyes**: Color-coded display of GFP, mCherry, Alexa dyes, calcium indicators, etc.
- **Sample Preparation**: Tissue clearing (CLARITY, iDISCO, CUBIC), sectioning, cell culture methods
- **Cell Lines**: HeLa, HEK293, U2OS, primary cultures, iPSCs, etc.
- **Figures**: Thumbnail grid with captions and links to full images
- **Methods**: Full methods text with expandable view for long sections
- **Equipment**: Microscope brands and models with color-coded tags

### New Quick Filters
- 📊 Figures - papers with figure metadata
- 🔬 Fluorophores indicator on paper cards

### OMERO Support
Data repositories now include OMERO links:
- OMERO webclient links
- IDR (Image Data Resource) images, datasets, projects
- SSBD database links

### Enhanced Paper Cards
Paper cards now show:
- Figure count badge
- Fluorophore count badge
- All existing badges (protocols, GitHub, data, RRIDs)

## What's New in v3.1

### Dynamic Filter Dropdowns
Filter dropdowns now automatically populate from your database:
- Shows only techniques/microscopes/organisms/software that exist in your data
- Displays paper counts for each filter option
- Filters work reliably because they use actual taxonomy slugs

### Improved Search API
The theme now uses its own REST API endpoint for reliable filtering:
- All taxonomy filters work correctly
- RRID, Protocol, and GitHub quick filters work properly
- Better search across title, authors, DOI, and abstract

### Fixed Quick Filters
- 🏆 Foundational (100+ citations) ✓
- ⭐ High Impact (50+ citations) ✓
- 📋 Protocols - now shows accurate count ✓
- 💻 GitHub - now shows accurate count ✓
- 💾 Data - repositories filter ✓
- 📊 Figures - papers with figures ✓
- 🏷️ RRIDs - now filters correctly and shows count ✓

## Configuration

### Gemini AI Chat
The theme uses the MicroHub plugin's Gemini integration. Configure the API key in:
1. Go to **MicroHub → Settings** in WordPress admin
2. Enter your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
3. The AI chat will appear on all pages (paper pages get context-aware suggestions)

**Note:** The theme does NOT have its own settings page - it uses the plugin's API endpoint at `/wp-json/microhub/v1/ai-chat`

### Page Templates

Create pages and assign templates. **Content is fully editable in WordPress editor!**

#### About Page
1. Create a new page named "About"
2. In Page Attributes, select "About Page" template
3. Add your content using the WordPress block editor:
   - Introduction text
   - Mission statement
   - Team information
   - Any custom content
4. The template automatically adds: Stats, Techniques, Contact CTA

#### Contact Page
1. Create a new page named "Contact"
2. Select "Contact Page" template
3. Add sidebar content in the editor (will appear in left sidebar):
   - Contact information
   - Office hours
   - FAQ items
4. Contact form is automatically included

#### Discussions Page
1. Create a new page named "Discussions"
2. Select "Discussions Page" template
3. Add introduction content in the editor
4. Recent paper discussions are automatically displayed

#### Custom Pages
- Use the default page template for any other pages
- Content is fully styled and supports:
  - Headings (H2, H3, H4)
  - Paragraphs, lists, tables
  - Images with captions
  - Code blocks
  - WordPress Gutenberg blocks (columns, buttons, etc.)

### Homepage
1. Go to Settings → Reading
2. Select "A static page"
3. Set "Homepage" to your front page

### Navigation Menu
1. Go to Appearance → Menus
2. Create menu, assign to "Primary Menu"
3. Add pages: Papers, Protocols, Discussions, About, Contact

## Author Features

### Clickable Authors
All author names throughout the theme are clickable and will show all papers by that author.

### Last Author Highlighting
On paper pages, the last author (typically the corresponding author) is highlighted and prominently displayed.

### Author Search
When clicking an author name, users see:
- Author summary card with total papers and citations
- All papers where that author appears
- Sorted by citation count

## Search Filters

The homepage search filters are **dynamically populated from your database**. Each dropdown shows:
- Only taxonomy terms that exist in your imported data
- Paper counts for each option
- Terms sorted by popularity (most papers first)

### Taxonomy Filters
- **Techniques**: All techniques in your `mh_technique` taxonomy
- **Microscopes**: All microscopes in your `mh_microscope` taxonomy
- **Organisms**: All organisms in your `mh_organism` taxonomy
- **Software**: All software in your `mh_software` taxonomy

### Other Filters
- **Year**: 2024-2025, 2020-2023, 2015-2019, 2010-2014, Before 2010
- **Citations**: 100+, 50+, 25+, 10+

### Quick Filters
- 🏆 Foundational (100+ citations)
- ⭐ High Impact (50+ citations)
- 📋 Protocols (shows count)
- 💻 GitHub (shows count)
- 🏷️ RRIDs (shows count)

## Theme Files

```
microhub-theme/
├── style.css              # Main styles
├── functions.php          # Theme functions & helpers
├── header.php             # Site header
├── footer.php             # Site footer
├── front-page.php         # Homepage with search
├── single-mh_paper.php    # Single paper template
├── archive-mh_paper.php   # Paper archive
├── taxonomy.php           # Taxonomy archive
├── search.php             # Search results (supports author search)
├── page.php               # Default page (editable)
├── index.php              # Fallback
├── 404.php                # Error page
├── page-templates/
│   ├── about.php          # About page (editable)
│   ├── contact.php        # Contact page (editable)
│   └── discussions.php    # Discussions (editable)
├── template-parts/
│   └── gemini-chat.php    # AI chat widget
└── assets/
    └── js/
        └── main.js        # JavaScript
```

## Helper Functions

```php
// Get all paper metadata
$meta = mh_get_paper_meta($post_id);

// Display paper badge (Foundational/High Impact)
mh_paper_badge($citations);

// Display paper meta (journal, year, citations)
mh_display_paper_meta($meta);

// Display paper links (DOI, PubMed, PDF, GitHub)
mh_display_paper_links($meta);

// Display taxonomy tags
mh_display_paper_tags($post_id);

// Display clickable authors with links
mh_display_clickable_authors($authors_string, $max_display, $show_last_author);

// Get last author from string
$last = mh_get_last_author($authors_string);

// Get first author from string
$first = mh_get_first_author($authors_string);

// Parse authors into array
$authors = mh_parse_authors($authors_string);

// Generate author search URL
$url = mh_author_search_url($author_name);

// Display protocols section
mh_display_protocols($protocols);

// Display GitHub section
mh_display_github($url);

// Display data repositories
mh_display_repositories($repositories);

// Display RRIDs
mh_display_rrids($rrids);

// Display facility
mh_display_facility($facility);

// Get page URLs
$urls = mh_get_page_urls();

// Get statistics
$stats = mh_get_stats();

// Format large numbers
mh_format_number($num); // Returns "1.2K", "5M", etc.

// Truncate text
mh_truncate_text($text, $words);
```

## Plugin Meta Fields Supported

- `_mh_doi`
- `_mh_pubmed_id`
- `_mh_authors`
- `_mh_journal`
- `_mh_publication_year`
- `_mh_citation_count`
- `_mh_abstract`
- `_mh_pdf_url`
- `_mh_github_url`
- `_mh_microscope_details`
- `_mh_facility`
- `_mh_protocols` (JSON array)
- `_mh_repositories` (JSON array)
- `_mh_rrids` (JSON array)

## Taxonomies Supported

- `mh_technique` (green tags)
- `mh_microscope` (blue tags)
- `mh_organism` (purple tags)
- `mh_software` (orange tags)

## Editing Tips

### About Page Content Example
```
Our mission is to make microscopy research more accessible...

## What We Offer
- Research papers with full metadata
- Detailed protocols
- Code and data links

## Our Team
Meet the people behind MicroHub...
```

### Contact Page Sidebar Example
```
## Get In Touch
Have questions? We're here to help!

## Office Hours
Monday-Friday: 9am-5pm EST

## FAQ
**How do I submit a paper?**
Use the contact form below...
```

## License

GPL v2 or later
