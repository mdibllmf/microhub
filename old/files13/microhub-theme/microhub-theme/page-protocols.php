<?php
/**
 * Page Template for Protocols
 * WordPress automatically uses this for pages with slug "protocols"
 * Full filtering and search matching the homepage experience
 */
get_header();

// Check if plugin is active
if (!function_exists('mh_plugin_active') || !mh_plugin_active()) {
    ?>
    <div class="mh-container" style="padding: 80px 20px; text-align: center;">
        <h1>📋 Protocols</h1>
        <p style="color: var(--text-muted); margin: 20px 0;">The MicroHub plugin is required for full functionality.</p>
    </div>
    <?php
    get_footer();
    return;
}

// Get stats
$protocol_paper_count = 0;
$protocol_papers_query = new WP_Query(array(
    'post_type' => 'mh_paper',
    'posts_per_page' => -1,
    'fields' => 'ids',
    'meta_query' => array(
        array('key' => '_mh_is_protocol', 'value' => '1', 'compare' => '=')
    )
));
$protocol_paper_count = $protocol_papers_query->found_posts;

$imported_count = wp_count_posts('mh_protocol')->publish ?? 0;
$total_protocols = $protocol_paper_count + $imported_count;

$api_base = rest_url('microhub-theme/v1');

// Get filter options from database
$filter_options = array(
    'techniques' => array(),
    'microscopes' => array(),
    'organisms' => array(),
    'software' => array(),
);

if (taxonomy_exists('mh_technique')) {
    $terms = get_terms(array('taxonomy' => 'mh_technique', 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
    if (!is_wp_error($terms)) {
        $filter_options['techniques'] = $terms;
    }
}

if (taxonomy_exists('mh_microscope')) {
    $terms = get_terms(array('taxonomy' => 'mh_microscope', 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
    if (!is_wp_error($terms)) {
        $filter_options['microscopes'] = $terms;
    }
}

if (taxonomy_exists('mh_organism')) {
    $terms = get_terms(array('taxonomy' => 'mh_organism', 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
    if (!is_wp_error($terms)) {
        $filter_options['organisms'] = $terms;
    }
}

if (taxonomy_exists('mh_software')) {
    $terms = get_terms(array('taxonomy' => 'mh_software', 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
    if (!is_wp_error($terms)) {
        $filter_options['software'] = $terms;
    }
}

// Get meta-based filter options
$meta_filter_options = function_exists('mh_get_all_filter_options') ? mh_get_all_filter_options() : array(
    'fluorophores' => array(),
    'sample_preparation' => array(),
    'cell_lines' => array(),
    'microscope_brands' => array(),
    'image_analysis_software' => array(),
);

// Get protocol sources
$sources = array();
global $wpdb;
$source_results = $wpdb->get_col("SELECT DISTINCT meta_value FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocol_type' AND meta_value != ''");
foreach ($source_results as $src) {
    if (!empty($src)) $sources[$src] = $src;
}
ksort($sources);
?>

<!-- Compact Hero -->
<section class="mh-hero-compact">
    <div class="mh-container">
        <h1>📋 Protocols</h1>
        <p>Search <?php echo number_format($total_protocols); ?> microscopy protocols</p>
    </div>
</section>

<!-- Search Section -->
<section class="mh-search-section">
    <div class="mh-container">
        <!-- Main Search Bar -->
        <div class="mh-search-bar">
            <div class="mh-search-input-wrapper">
                <svg class="mh-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                <input type="text" id="mh-search-input" placeholder="Search by title, author, technique, abstract...">
            </div>
            <button type="button" id="mh-search-btn" class="mh-search-button">Search</button>
        </div>

        <!-- Filter Row -->
        <div class="mh-filter-row">
            <div class="mh-filter-item">
                <select id="filter-technique" data-filter="technique">
                    <option value="">All Techniques (<?php echo count($filter_options['techniques']); ?>)</option>
                    <?php foreach ($filter_options['techniques'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-microscope" data-filter="microscope">
                    <option value="">All Microscopes (<?php echo count($filter_options['microscopes']); ?>)</option>
                    <?php foreach ($filter_options['microscopes'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-organism" data-filter="organism">
                    <option value="">All Organisms (<?php echo count($filter_options['organisms']); ?>)</option>
                    <?php foreach ($filter_options['organisms'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-software" data-filter="software">
                    <option value="">All Software (<?php echo count($filter_options['software']); ?>)</option>
                    <?php foreach ($filter_options['software'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-year" data-filter="year">
                    <option value="">All Years</option>
                    <option value="2024-2025">2024-2025</option>
                    <option value="2020-2023">2020-2023</option>
                    <option value="2015-2019">2015-2019</option>
                    <option value="2010-2014">2010-2014</option>
                    <option value="before-2010">Before 2010</option>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-source" data-filter="source">
                    <option value="">All Sources</option>
                    <option value="JoVE">JoVE</option>
                    <option value="Nature Protocols">Nature Protocols</option>
                    <option value="STAR Protocols">STAR Protocols</option>
                    <option value="protocols.io">protocols.io</option>
                    <option value="Bio-protocol">Bio-protocol</option>
                    <?php foreach ($sources as $src): ?>
                    <?php if (!in_array($src, array('JoVE', 'Nature Protocols', 'STAR Protocols', 'protocols.io', 'Bio-protocol'))): ?>
                    <option value="<?php echo esc_attr($src); ?>"><?php echo esc_html($src); ?></option>
                    <?php endif; ?>
                    <?php endforeach; ?>
                </select>
            </div>
        </div>
        
        <!-- Advanced Filters Row -->
        <div class="mh-filter-row mh-filter-row-advanced" id="advanced-filters" style="display: none;">
            <div class="mh-filter-item">
                <select id="filter-fluorophore" data-filter="fluorophore">
                    <option value="">All Fluorophores (<?php echo count($meta_filter_options['fluorophores']); ?>)</option>
                    <?php foreach ($meta_filter_options['fluorophores'] as $fluor => $count): ?>
                    <option value="<?php echo esc_attr($fluor); ?>"><?php echo esc_html($fluor); ?> (<?php echo $count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-sample-prep" data-filter="sample_prep">
                    <option value="">All Sample Prep (<?php echo count($meta_filter_options['sample_preparation']); ?>)</option>
                    <?php foreach ($meta_filter_options['sample_preparation'] as $prep => $count): ?>
                    <option value="<?php echo esc_attr($prep); ?>"><?php echo esc_html($prep); ?> (<?php echo $count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-cell-line" data-filter="cell_line">
                    <option value="">All Cell Lines (<?php echo count($meta_filter_options['cell_lines']); ?>)</option>
                    <?php foreach ($meta_filter_options['cell_lines'] as $cell => $count): ?>
                    <option value="<?php echo esc_attr($cell); ?>"><?php echo esc_html($cell); ?> (<?php echo $count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-brand" data-filter="brand">
                    <option value="">All Brands (<?php echo count($meta_filter_options['microscope_brands']); ?>)</option>
                    <?php foreach ($meta_filter_options['microscope_brands'] as $brand => $count): ?>
                    <option value="<?php echo esc_attr($brand); ?>"><?php echo esc_html($brand); ?> (<?php echo $count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-citations" data-filter="citations">
                    <option value="">Any Citations</option>
                    <option value="100">100+ (Foundational)</option>
                    <option value="50">50+ (High Impact)</option>
                    <option value="25">25+</option>
                    <option value="10">10+</option>
                </select>
            </div>
        </div>
        
        <!-- Toggle Advanced Filters Button -->
        <div class="mh-advanced-toggle">
            <button type="button" id="toggle-advanced-filters" class="mh-toggle-btn">
                <span class="toggle-text">Show Advanced Filters</span>
                <svg class="toggle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </button>
        </div>

        <!-- Quick Filters -->
        <div class="mh-quick-filters">
            <span class="mh-quick-label">Quick:</span>
            <button type="button" class="mh-quick-btn" data-filter="foundational">🏆 Foundational</button>
            <button type="button" class="mh-quick-btn" data-filter="high_impact">⭐ High Impact</button>
            <button type="button" class="mh-quick-btn" data-filter="has_figures">📊 With Figures</button>
            <button type="button" class="mh-quick-btn" data-filter="has_github">💻 With Code</button>
            <button type="button" id="mh-clear-filters" class="mh-clear-btn">✕ Clear</button>
        </div>
    </div>
</section>

<!-- Results Section -->
<section class="mh-results-section">
    <div class="mh-container">
        <div class="mh-results-header">
            <div class="mh-results-info">
                Showing <strong id="mh-showing">0</strong> of <strong id="mh-total"><?php echo $total_protocols; ?></strong> protocols
            </div>
            <div class="mh-results-sort">
                <select id="mh-sort">
                    <option value="citations-desc">Most Cited</option>
                    <option value="year-desc">Newest</option>
                    <option value="year-asc">Oldest</option>
                    <option value="title-asc">Title A-Z</option>
                </select>
            </div>
        </div>

        <!-- Stats Bar -->
        <div class="mh-protocol-stats-bar">
            <div class="mh-stat-item">
                <span class="stat-icon">📄</span>
                <span class="stat-num"><?php echo number_format($protocol_paper_count); ?></span>
                <span class="stat-label">Protocol Papers</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">📋</span>
                <span class="stat-num"><?php echo number_format($imported_count); ?></span>
                <span class="stat-label">Imported Protocols</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">🔬</span>
                <span class="stat-num"><?php echo count($filter_options['techniques']); ?></span>
                <span class="stat-label">Techniques</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">🧬</span>
                <span class="stat-num"><?php echo count($filter_options['organisms']); ?></span>
                <span class="stat-label">Organisms</span>
            </div>
        </div>

        <!-- Protocols Grid -->
        <div id="mh-protocols-grid" class="mh-papers-grid">
            <div class="mh-loading-indicator">
                <div class="mh-spinner"></div>
                <p>Loading protocols...</p>
            </div>
        </div>
        
        <!-- Pagination -->
        <div id="mh-pagination" class="mh-pagination"></div>
    </div>
</section>

<style>
/* Core Layout */
.mh-hero-compact { padding: 40px 20px; text-align: center; background: linear-gradient(180deg, var(--bg-card, #161b22) 0%, var(--bg, #0d1117) 100%); border-bottom: 1px solid var(--border, #30363d); }
.mh-hero-compact h1 { font-size: 2rem; margin: 0 0 8px 0; color: var(--text, #c9d1d9); }
.mh-hero-compact p { color: var(--text-muted, #8b949e); margin: 0; font-size: 1.1rem; }
.mh-container { max-width: 1400px; margin: 0 auto; padding: 0 20px; }

/* Search Section */
.mh-search-section { padding: 24px 0; background: var(--bg-card, #161b22); border-bottom: 1px solid var(--border, #30363d); }
.mh-search-bar { display: flex; gap: 12px; margin-bottom: 20px; }
.mh-search-input-wrapper { flex: 1; position: relative; }
.mh-search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 20px; height: 20px; color: var(--text-muted, #8b949e); }
.mh-search-input-wrapper input { width: 100%; padding: 12px 14px 12px 44px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 8px; color: var(--text, #c9d1d9); font-size: 1rem; }
.mh-search-input-wrapper input:focus { outline: none; border-color: var(--primary, #58a6ff); }
.mh-search-button { padding: 12px 24px; background: var(--primary, #58a6ff); color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.mh-search-button:hover { background: var(--primary-hover, #79b8ff); }

/* Filter Rows */
.mh-filter-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
.mh-filter-item select { padding: 8px 12px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); font-size: 0.85rem; min-width: 140px; cursor: pointer; }
.mh-filter-item select:focus { outline: none; border-color: var(--primary, #58a6ff); }

/* Advanced Filters Toggle */
.mh-advanced-toggle { margin-bottom: 16px; }
.mh-toggle-btn { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: transparent; border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text-muted, #8b949e); cursor: pointer; font-size: 0.85rem; }
.mh-toggle-btn:hover { border-color: var(--primary, #58a6ff); color: var(--primary, #58a6ff); }
.mh-toggle-btn.active .toggle-icon { transform: rotate(180deg); }

/* Quick Filters */
.mh-quick-filters { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.mh-quick-label { color: var(--text-muted, #8b949e); font-size: 0.85rem; font-weight: 500; }
.mh-quick-btn { padding: 6px 12px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 20px; color: var(--text-muted, #8b949e); cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }
.mh-quick-btn:hover { border-color: var(--primary, #58a6ff); color: var(--primary, #58a6ff); }
.mh-quick-btn.active { background: var(--primary, #58a6ff); border-color: var(--primary, #58a6ff); color: #fff; }
.mh-quick-btn span { background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 10px; margin-left: 4px; font-size: 0.75rem; }
.mh-clear-btn { padding: 6px 12px; background: transparent; border: 1px solid var(--border, #30363d); border-radius: 20px; color: var(--text-light, #6e7681); cursor: pointer; font-size: 0.8rem; }
.mh-clear-btn:hover { border-color: #f85149; color: #f85149; }

/* Results Section */
.mh-results-section { padding: 24px 0 60px; }
.mh-results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.mh-results-info { color: var(--text-muted, #8b949e); font-size: 0.9rem; }
.mh-results-info strong { color: var(--text, #c9d1d9); }
.mh-results-sort select { padding: 8px 12px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); font-size: 0.85rem; }

/* Stats Bar */
.mh-protocol-stats-bar { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 24px; padding: 16px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; }
.mh-stat-item { display: flex; align-items: center; gap: 8px; }
.mh-stat-item .stat-icon { font-size: 1.25rem; }
.mh-stat-item .stat-num { font-weight: 700; color: var(--primary, #58a6ff); font-size: 1.1rem; }
.mh-stat-item .stat-label { color: var(--text-muted, #8b949e); font-size: 0.85rem; }

/* Papers/Protocols Grid */
.mh-papers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }

/* Loading */
.mh-loading-indicator { grid-column: 1 / -1; text-align: center; padding: 60px 20px; }
.mh-spinner { width: 40px; height: 40px; border: 3px solid var(--border, #30363d); border-top-color: var(--primary, #58a6ff); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* No Results */
.mh-no-results { grid-column: 1 / -1; text-align: center; padding: 60px 20px; background: var(--bg-card, #161b22); border-radius: 8px; }
.mh-no-results h3 { margin: 0 0 8px 0; color: var(--text, #c9d1d9); }
.mh-no-results p { color: var(--text-muted, #8b949e); margin: 0; }

/* Protocol Card */
.mh-protocol-card { background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; transition: border-color 0.2s, transform 0.2s; }
.mh-protocol-card:hover { border-color: var(--primary, #58a6ff); transform: translateY(-2px); }
.mh-protocol-card.protocol_paper { border-left: 3px solid var(--primary, #58a6ff); }
.mh-protocol-card.imported { border-left: 3px solid #56d364; }

/* Card Header */
.mh-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 10px; }
.mh-card-source { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.mh-card-source.jove { background: #1e3a5f; color: #58a6ff; }
.mh-card-source.nature { background: #2d1f3d; color: #a371f7; }
.mh-card-source.star { background: #3d2f1f; color: #f0883e; }
.mh-card-source.protocols-io { background: #1f3d2d; color: #56d364; }
.mh-card-source.bio-protocol { background: #3d1f2d; color: #f778ba; }
.mh-card-source.community { background: #2d3d1f; color: #a5d6a7; }
.mh-card-source.other { background: var(--bg-hover, #21262d); color: var(--text-muted, #8b949e); }
.mh-card-badge { font-size: 0.7rem; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
.mh-card-badge.foundational { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; }
.mh-card-badge.high-impact { background: linear-gradient(135deg, #58a6ff, #a371f7); color: #fff; }
.mh-card-badge.standard { background: var(--bg-hover, #21262d); color: var(--text-muted, #8b949e); }

/* Card Title */
.mh-card-title { font-size: 1rem; font-weight: 600; line-height: 1.4; margin: 0 0 8px 0; }
.mh-card-title a { color: var(--text, #c9d1d9); text-decoration: none; }
.mh-card-title a:hover { color: var(--primary, #58a6ff); }

/* Card Meta */
.mh-card-meta { font-size: 0.8rem; color: var(--text-muted, #8b949e); margin-bottom: 10px; line-height: 1.4; }
.mh-card-year { color: var(--text-light, #6e7681); }
.mh-card-journal { font-style: italic; }

/* Card Abstract */
.mh-card-abstract { font-size: 0.85rem; color: var(--text-light, #8b949e); line-height: 1.5; margin-bottom: 12px; flex: 1; }

/* Card Tags */
.mh-card-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.mh-card-tag { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 500; }
.mh-card-tag.technique { background: #1e3a5f; color: #58a6ff; }
.mh-card-tag.microscope { background: #3d2f1f; color: #f0883e; }
.mh-card-tag.organism { background: #1f3d2d; color: #56d364; }
.mh-card-tag.software { background: #2d1f3d; color: #a371f7; }
.mh-card-tag.fluorophore { background: #3d1f2d; color: #f778ba; }
.mh-card-tag.sample-prep { background: #2d3d1f; color: #a5d6a7; }
.mh-card-tag.cell-line { background: #3d3d1f; color: #d4a72c; }

/* Card Enrichment */
.mh-card-enrichment { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.mh-enrichment-item { font-size: 0.75rem; color: var(--text-muted, #8b949e); display: flex; align-items: center; gap: 4px; }

/* Card Links */
.mh-card-links { display: flex; flex-wrap: wrap; gap: 8px; padding-top: 12px; border-top: 1px solid var(--border, #30363d); margin-top: auto; }
.mh-card-link { font-size: 0.75rem; padding: 4px 10px; background: var(--bg-hover, #21262d); border-radius: 4px; color: var(--text-muted, #8b949e); text-decoration: none; }
.mh-card-link:hover { background: var(--primary, #58a6ff); color: #fff; }
.mh-card-link.doi { color: #f0883e; }
.mh-card-link.pubmed { color: #56d364; }
.mh-card-link.github { color: #a371f7; }
.mh-card-link.external { color: var(--primary, #58a6ff); }

/* Pagination */
.mh-pagination { display: flex; justify-content: center; gap: 8px; margin-top: 30px; flex-wrap: wrap; }
.mh-pagination button { padding: 8px 14px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); cursor: pointer; font-size: 0.9rem; }
.mh-pagination button:hover:not(:disabled) { background: var(--primary, #58a6ff); border-color: var(--primary, #58a6ff); color: #fff; }
.mh-pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
.mh-pagination button.active { background: var(--primary, #58a6ff); border-color: var(--primary, #58a6ff); color: #fff; }

/* Responsive */
@media (max-width: 768px) {
    .mh-search-bar { flex-direction: column; }
    .mh-filter-row { flex-direction: column; }
    .mh-filter-item select { width: 100%; }
    .mh-papers-grid { grid-template-columns: 1fr; }
    .mh-protocol-stats-bar { flex-direction: column; gap: 12px; }
    .mh-results-header { flex-direction: column; align-items: flex-start; }
}
</style>

<script>
(function() {
    const apiBase = '<?php echo esc_js($api_base); ?>';
    const searchInput = document.getElementById('mh-search-input');
    const searchBtn = document.getElementById('mh-search-btn');
    const sortSelect = document.getElementById('mh-sort');
    const protocolsGrid = document.getElementById('mh-protocols-grid');
    const paginationEl = document.getElementById('mh-pagination');
    const showingEl = document.getElementById('mh-showing');
    const totalEl = document.getElementById('mh-total');
    const clearBtn = document.getElementById('mh-clear-filters');
    const toggleBtn = document.getElementById('toggle-advanced-filters');
    const advancedFilters = document.getElementById('advanced-filters');
    
    let currentPage = 1;
    let perPage = 24;
    let activeFilters = {};
    
    // Initialize
    searchProtocols();
    
    // Event listeners
    searchBtn.addEventListener('click', () => { currentPage = 1; searchProtocols(); });
    searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { currentPage = 1; searchProtocols(); } });
    sortSelect.addEventListener('change', () => { currentPage = 1; searchProtocols(); });
    
    // Toggle advanced filters
    if (toggleBtn && advancedFilters) {
        toggleBtn.addEventListener('click', () => {
            const isHidden = advancedFilters.style.display === 'none';
            advancedFilters.style.display = isHidden ? 'flex' : 'none';
            toggleBtn.classList.toggle('active', isHidden);
            toggleBtn.querySelector('.toggle-text').textContent = isHidden ? 'Hide Advanced Filters' : 'Show Advanced Filters';
        });
    }
    
    // Filter dropdowns
    document.querySelectorAll('[data-filter]').forEach(select => {
        select.addEventListener('change', () => {
            const filter = select.dataset.filter;
            activeFilters[filter] = select.value;
            currentPage = 1;
            searchProtocols();
        });
    });
    
    // Quick filter buttons
    document.querySelectorAll('.mh-quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            btn.classList.toggle('active');
            activeFilters[filter] = btn.classList.contains('active');
            currentPage = 1;
            searchProtocols();
        });
    });
    
    // Clear filters
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        document.querySelectorAll('[data-filter]').forEach(s => { if (s.tagName === 'SELECT') s.value = ''; });
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        activeFilters = {};
        currentPage = 1;
        if (advancedFilters) advancedFilters.style.display = 'none';
        if (toggleBtn) {
            toggleBtn.classList.remove('active');
            toggleBtn.querySelector('.toggle-text').textContent = 'Show Advanced Filters';
        }
        searchProtocols();
    });
    
    // Search protocols
    function searchProtocols() {
        protocolsGrid.innerHTML = '<div class="mh-loading-indicator"><div class="mh-spinner"></div><p>Loading protocols...</p></div>';
        
        const params = new URLSearchParams();
        params.set('page', currentPage);
        params.set('per_page', perPage);
        
        const search = searchInput.value.trim();
        if (search) params.set('search', search);
        
        const sort = sortSelect.value;
        if (sort === 'citations-desc') { params.set('orderby', 'citations'); params.set('order', 'desc'); }
        else if (sort === 'year-desc') { params.set('orderby', 'year'); params.set('order', 'desc'); }
        else if (sort === 'year-asc') { params.set('orderby', 'year'); params.set('order', 'asc'); }
        else if (sort === 'title-asc') { params.set('orderby', 'title'); params.set('order', 'asc'); }
        
        // Taxonomy filters
        if (activeFilters.technique) params.set('technique', activeFilters.technique);
        if (activeFilters.microscope) params.set('microscope', activeFilters.microscope);
        if (activeFilters.organism) params.set('organism', activeFilters.organism);
        if (activeFilters.software) params.set('software', activeFilters.software);
        if (activeFilters.source) params.set('source', activeFilters.source);
        
        // Year filter
        if (activeFilters.year) {
            if (activeFilters.year === '2024-2025') params.set('year_min', 2024);
            else if (activeFilters.year === '2020-2023') { params.set('year_min', 2020); params.set('year_max', 2023); }
            else if (activeFilters.year === '2015-2019') { params.set('year_min', 2015); params.set('year_max', 2019); }
            else if (activeFilters.year === '2010-2014') { params.set('year_min', 2010); params.set('year_max', 2014); }
            else if (activeFilters.year === 'before-2010') params.set('year_max', 2009);
        }
        
        // Advanced filters
        if (activeFilters.citations) params.set('citations_min', activeFilters.citations);
        if (activeFilters.fluorophore) params.set('fluorophore', activeFilters.fluorophore);
        if (activeFilters.sample_prep) params.set('sample_prep', activeFilters.sample_prep);
        if (activeFilters.cell_line) params.set('cell_line', activeFilters.cell_line);
        if (activeFilters.brand) params.set('brand', activeFilters.brand);
        
        // Quick filters
        if (activeFilters.foundational) params.set('citations_min', 100);
        if (activeFilters.high_impact) params.set('citations_min', 50);
        if (activeFilters.has_figures) params.set('has_figures', true);
        if (activeFilters.has_github) params.set('has_github', true);
        
        fetch(apiBase + '/protocols?' + params.toString())
            .then(res => res.json())
            .then(data => {
                renderProtocols(data.protocols || []);
                renderPagination(data.total || 0, data.pages || 1);
                showingEl.textContent = (data.protocols || []).length;
                totalEl.textContent = formatNumber(data.total || 0);
            })
            .catch(err => {
                protocolsGrid.innerHTML = '<div class="mh-no-results"><h3>Error loading protocols</h3><p>Please try again.</p></div>';
            });
    }
    
    // Render protocols
    function renderProtocols(protocols) {
        if (!protocols.length) {
            protocolsGrid.innerHTML = '<div class="mh-no-results"><h3>No protocols found</h3><p>Try adjusting your search or filters.</p></div>';
            return;
        }
        
        protocolsGrid.innerHTML = protocols.map(p => createProtocolCard(p)).join('');
    }
    
    // Create protocol card
    function createProtocolCard(protocol) {
        const citations = parseInt(protocol.citations) || 0;
        let badgeClass = 'standard';
        let badgeText = citations > 0 ? formatNumber(citations) + ' citations' : '';
        
        if (citations >= 100) { badgeClass = 'foundational'; badgeText = '🏆 Foundational'; }
        else if (citations >= 50) { badgeClass = 'high-impact'; badgeText = '⭐ High Impact'; }
        
        const sourceClass = getSourceClass(protocol.source);
        
        // Tags
        let tagsHtml = '';
        if (protocol.techniques?.length) {
            tagsHtml += protocol.techniques.slice(0, 2).map(t => `<span class="mh-card-tag technique">${escapeHtml(t)}</span>`).join('');
        }
        if (protocol.microscopes?.length) {
            tagsHtml += `<span class="mh-card-tag microscope">🔬 ${escapeHtml(protocol.microscopes[0])}</span>`;
        }
        if (protocol.organisms?.length) {
            tagsHtml += protocol.organisms.slice(0, 2).map(o => `<span class="mh-card-tag organism">${escapeHtml(o)}</span>`).join('');
        }
        if (protocol.software?.length) {
            tagsHtml += `<span class="mh-card-tag software">${escapeHtml(protocol.software[0])}</span>`;
        }
        if (protocol.fluorophores?.length) {
            tagsHtml += `<span class="mh-card-tag fluorophore">${escapeHtml(protocol.fluorophores[0])}</span>`;
        }
        if (protocol.sample_preparation?.length) {
            tagsHtml += `<span class="mh-card-tag sample-prep">${escapeHtml(protocol.sample_preparation[0])}</span>`;
        }
        if (protocol.cell_lines?.length) {
            tagsHtml += `<span class="mh-card-tag cell-line">${escapeHtml(protocol.cell_lines[0])}</span>`;
        }
        
        // Enrichment badges
        let enrichmentHtml = '';
        const items = [];
        if (protocol.has_figures || protocol.figure_count > 0) items.push(`<span class="mh-enrichment-item">📊 ${protocol.figure_count || 'Figs'}</span>`);
        if (protocol.github_url) items.push(`<span class="mh-enrichment-item">💻 Code</span>`);
        if (protocol.microscope_brands?.length) items.push(`<span class="mh-enrichment-item" title="${escapeHtml(protocol.microscope_brands.slice(0,3).join(', '))}">🏭 ${protocol.microscope_brands.length}</span>`);
        if (items.length) enrichmentHtml = `<div class="mh-card-enrichment">${items.join('')}</div>`;
        
        // Authors
        let metaHtml = '';
        if (protocol.authors?.length) {
            metaHtml = escapeHtml(protocol.authors.slice(0, 3).join(', '));
            if (protocol.authors.length > 3) metaHtml += ' et al.';
        }
        if (protocol.year) {
            metaHtml += metaHtml ? ` <span class="mh-card-year">(${protocol.year})</span>` : `<span class="mh-card-year">${protocol.year}</span>`;
        }
        if (protocol.journal) {
            metaHtml += ` • <span class="mh-card-journal">${escapeHtml(protocol.journal)}</span>`;
        }
        
        // Links
        let linksHtml = '';
        if (protocol.doi) linksHtml += `<a href="https://doi.org/${escapeHtml(protocol.doi)}" class="mh-card-link doi" target="_blank">DOI</a>`;
        if (protocol.pubmed_id) linksHtml += `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(protocol.pubmed_id)}/" class="mh-card-link pubmed" target="_blank">PubMed</a>`;
        if (protocol.github_url) linksHtml += `<a href="${escapeHtml(protocol.github_url)}" class="mh-card-link github" target="_blank">GitHub</a>`;
        if (protocol.external_url && protocol.type !== 'protocol_paper') {
            linksHtml += `<a href="${escapeHtml(protocol.external_url)}" class="mh-card-link external" target="_blank">View Protocol ↗</a>`;
        }
        
        return `
            <article class="mh-protocol-card ${protocol.type}">
                <div class="mh-card-header">
                    <span class="mh-card-source ${sourceClass}">${escapeHtml(protocol.source)}</span>
                    ${badgeText ? `<span class="mh-card-badge ${badgeClass}">${badgeText}</span>` : ''}
                </div>
                <h3 class="mh-card-title">
                    <a href="${escapeHtml(protocol.permalink)}">${escapeHtml(protocol.title)}</a>
                </h3>
                ${metaHtml ? `<div class="mh-card-meta">${metaHtml}</div>` : ''}
                ${protocol.abstract ? `<p class="mh-card-abstract">${escapeHtml(protocol.abstract)}</p>` : ''}
                ${tagsHtml ? `<div class="mh-card-tags">${tagsHtml}</div>` : ''}
                ${enrichmentHtml}
                ${linksHtml ? `<div class="mh-card-links">${linksHtml}</div>` : ''}
            </article>
        `;
    }
    
    // Get source class
    function getSourceClass(source) {
        if (!source) return 'other';
        const s = source.toLowerCase();
        if (s.includes('jove')) return 'jove';
        if (s.includes('nature')) return 'nature';
        if (s.includes('star')) return 'star';
        if (s.includes('protocols.io')) return 'protocols-io';
        if (s.includes('bio-protocol')) return 'bio-protocol';
        if (s.includes('community')) return 'community';
        return 'other';
    }
    
    // Render pagination
    function renderPagination(total, totalPages) {
        if (totalPages <= 1) {
            paginationEl.innerHTML = '';
            return;
        }
        
        let html = '';
        html += `<button ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">← Prev</button>`;
        
        const maxVisible = 5;
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        if (end - start < maxVisible - 1) start = Math.max(1, end - maxVisible + 1);
        
        if (start > 1) {
            html += `<button data-page="1">1</button>`;
            if (start > 2) html += `<button disabled>...</button>`;
        }
        
        for (let i = start; i <= end; i++) {
            html += `<button ${i === currentPage ? 'class="active"' : ''} data-page="${i}">${i}</button>`;
        }
        
        if (end < totalPages) {
            if (end < totalPages - 1) html += `<button disabled>...</button>`;
            html += `<button data-page="${totalPages}">${totalPages}</button>`;
        }
        
        html += `<button ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">Next →</button>`;
        
        paginationEl.innerHTML = html;
        
        paginationEl.querySelectorAll('button[data-page]').forEach(btn => {
            btn.addEventListener('click', () => {
                currentPage = parseInt(btn.dataset.page);
                searchProtocols();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }
    
    // Utilities
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    function formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }
})();
</script>

<?php get_footer(); ?>
