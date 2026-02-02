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
    'facilities' => array(),
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

if (taxonomy_exists('mh_facility')) {
    $terms = get_terms(array('taxonomy' => 'mh_facility', 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
    if (!is_wp_error($terms)) {
        $filter_options['facilities'] = $terms;
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
            <div class="mh-filter-item">
                <select id="filter-facility" data-filter="facility">
                    <option value="">All Facilities (<?php echo count($filter_options['facilities']); ?>)</option>
                    <?php foreach ($filter_options['facilities'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
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

<!-- Results Section with Sidebar -->
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

        <!-- Main Content with Sidebar -->
        <div class="mh-main-layout">
            <!-- Protocols Grid (Left) -->
            <div class="mh-papers-column">
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

            <!-- Sidebar (Right) -->
            <?php
            // Get recent protocol papers (from protocol journals)
            $protocol_papers = function_exists('mh_get_recent_protocol_papers') ? mh_get_recent_protocol_papers(8) : array();
            // Get institutions
            $institutions = function_exists('mh_get_institutions') ? mh_get_institutions(10) : array();
            ?>
            <aside class="mh-sidebar">
                <!-- Protocol Stats Widget -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">📊</span> Protocol Stats</h3>
                    <div class="mh-stats-list">
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">Protocol Papers</span>
                            <span class="mh-stat-value"><?php echo number_format($protocol_paper_count); ?></span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">Imported</span>
                            <span class="mh-stat-value"><?php echo number_format($imported_count); ?></span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">Techniques</span>
                            <span class="mh-stat-value"><?php echo count($filter_options['techniques']); ?></span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">Organisms</span>
                            <span class="mh-stat-value"><?php echo count($filter_options['organisms']); ?></span>
                        </div>
                    </div>
                </div>

                <!-- Recent Protocols Widget -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">📋</span> Recent Protocols</h3>
                    <?php if (!empty($protocol_papers)) : ?>
                    <ul class="mh-protocol-list">
                        <?php foreach ($protocol_papers as $paper) : ?>
                        <li class="mh-protocol-item">
                            <a href="<?php echo esc_url($paper['permalink']); ?>" class="protocol-link">
                                <?php echo esc_html(wp_trim_words($paper['title'], 8)); ?>
                            </a>
                            <span class="source"><?php echo esc_html($paper['source']); ?></span>
                        </li>
                        <?php endforeach; ?>
                    </ul>
                    <?php else : ?>
                    <p class="mh-empty-item">No protocol papers found</p>
                    <?php endif; ?>
                </div>

                <!-- Research Institutions Widget -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">🏛️</span> Research Institutions</h3>
                    <?php if (!empty($institutions)) : ?>
                    <ul class="mh-institution-list">
                        <?php foreach ($institutions as $institution) :
                            $institution_slug = isset($institution['slug']) ? $institution['slug'] : sanitize_title($institution['name']);
                        ?>
                        <li class="mh-institution-item">
                            <a href="#" class="institution-link" data-institution="<?php echo esc_attr($institution_slug); ?>" onclick="filterByInstitution('<?php echo esc_js($institution_slug); ?>'); return false;">
                                <?php echo esc_html(wp_trim_words($institution['name'], 6)); ?>
                            </a>
                            <?php if (!empty($institution['website'])) : ?>
                            <a href="<?php echo esc_url($institution['website']); ?>" class="institution-website" target="_blank" title="Visit institution website">🔗</a>
                            <?php endif; ?>
                            <?php if ($institution['count'] > 0) : ?>
                            <span class="count">(<?php echo $institution['count']; ?> papers)</span>
                            <?php endif; ?>
                        </li>
                        <?php endforeach; ?>
                    </ul>
                    <?php else : ?>
                    <p class="mh-empty-item">No institutions listed</p>
                    <?php endif; ?>
                </div>
            </aside>
        </div>
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
.mh-protocol-card, .mh-paper-card { background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; transition: border-color 0.2s, transform 0.2s; }
.mh-protocol-card:hover, .mh-paper-card:hover { border-color: var(--primary, #58a6ff); transform: translateY(-2px); }
.mh-protocol-card.protocol_paper, .mh-paper-card.protocol_paper { border-left: 3px solid var(--primary, #58a6ff); }
.mh-protocol-card.imported { border-left: 3px solid #56d364; }

/* Card Header */
.mh-card-header, .mh-card-header-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 10px; }
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
.mh-card-meta span { margin-right: 12px; }
.mh-card-year { color: var(--text-light, #6e7681); }
.mh-card-journal { font-style: italic; }

/* Source label in meta */
.mh-card-source-label { padding: 2px 6px; border-radius: 3px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; margin-right: 8px; }
.mh-card-source-label.jove { background: #1e3a5f; color: #58a6ff; }
.mh-card-source-label.nature { background: #2d1f3d; color: #a371f7; }
.mh-card-source-label.star { background: #3d2f1f; color: #f0883e; }
.mh-card-source-label.protocols-io { background: #1f3d2d; color: #56d364; }
.mh-card-source-label.bio-protocol { background: #3d1f2d; color: #f778ba; }
.mh-card-source-label.community { background: #2d3d1f; color: #a5d6a7; }
.mh-card-source-label.other { background: var(--bg-hover, #21262d); color: var(--text-muted, #8b949e); }

/* Card Abstract */
.mh-card-abstract { font-size: 0.85rem; color: var(--text-light, #8b949e); line-height: 1.5; margin-bottom: 12px; flex: 1; }

/* Card Tags - match homepage exactly */
.mh-card-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
.mh-card-tag { padding: 3px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 500; color: white; }
.mh-card-tag.technique { background: var(--tag-technique, #1e6091); }
.mh-card-tag.microscope { background: var(--tag-microscope, #9d4edd); }
.mh-card-tag.software { background: var(--tag-software, #0891b2); }
.mh-card-tag.organism { background: #059669; }
.mh-card-tag.fluorophore { background: #db2777; }
.mh-card-tag.sample-prep { background: #ea580c; }
.mh-card-tag.cell-line { background: #7c3aed; }
.mh-card-tag.brand { background: #475569; }

/* Card Enrichment - match homepage exactly */
.mh-card-enrichment { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; font-size: 0.8rem; }
.mh-enrichment-item { color: var(--text-muted, #8b949e); }
.mh-enrichment-item.protocols { color: #3b82f6; }
.mh-enrichment-item.github { color: #a3a3a3; }
.mh-enrichment-item.rrids { color: #a371f7; }
.mh-enrichment-item.figures { color: #38bdf8; }
.mh-enrichment-item.fluor { color: #3fb950; }
.mh-enrichment-item.sample-prep { color: #f0883e; }
.mh-enrichment-item.cell-line { color: #d2a8ff; }

/* Card Links */
.mh-card-links { display: flex; flex-wrap: wrap; gap: 8px; padding-top: 12px; border-top: 1px solid var(--border, #30363d); margin-top: auto; }
.mh-card-link { font-size: 0.75rem; padding: 4px 10px; background: var(--bg-hover, #21262d); border-radius: 4px; color: var(--text-muted, #8b949e); text-decoration: none; }
.mh-card-link:hover { background: var(--primary, #58a6ff); color: #fff; }

/* Card Authors */
.mh-card-authors { font-size: 0.85rem; color: var(--text-muted, #8b949e); margin-bottom: 8px; }
.mh-card-authors .mh-author-link { color: var(--text-muted, #8b949e); text-decoration: none; transition: color 0.2s; }
.mh-card-authors .mh-author-link:hover { color: var(--primary, #58a6ff); text-decoration: underline; }
.mh-card-authors .mh-last-author { font-weight: 500; }
.mh-card-authors .mh-author-sep { color: var(--text-light, #6e7681); }

/* Card Footer */
.mh-card-footer { margin-top: auto; }
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

/* Main Layout with Sidebar */
.mh-main-layout {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 32px;
    align-items: start;
}

.mh-papers-column {
    min-width: 0;
}

/* Sidebar */
.mh-sidebar {
    position: sticky;
    top: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.mh-sidebar-widget {
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 12px;
    padding: 16px;
}

.mh-sidebar-widget h3 {
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text, #c9d1d9);
    border-bottom: 1px solid var(--border, #30363d);
    padding-bottom: 10px;
}

.mh-sidebar-widget h3 .icon {
    font-size: 1rem;
}

/* Stats List in Sidebar */
.mh-stats-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
}

.mh-stat-label {
    color: var(--text-muted, #8b949e);
}

.mh-stat-value {
    color: var(--primary, #58a6ff);
    font-weight: 600;
}

.mh-protocol-list,
.mh-institution-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.mh-protocol-item,
.mh-institution-item {
    padding: 8px 0;
    border-bottom: 1px solid var(--border, #30363d);
}

.mh-protocol-item:last-child,
.mh-institution-item:last-child {
    border-bottom: none;
}

.mh-protocol-item .protocol-link,
.mh-institution-item .institution-link {
    display: block;
    color: var(--text, #c9d1d9);
    text-decoration: none;
    font-size: 0.85rem;
    line-height: 1.4;
    transition: color 0.2s;
}

.mh-protocol-item .protocol-link:hover,
.mh-institution-item .institution-link:hover {
    color: var(--primary, #58a6ff);
}

.mh-institution-item .institution-link.active {
    color: var(--primary, #58a6ff);
    font-weight: 600;
}

.mh-institution-item {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
}

.mh-institution-item .institution-link {
    flex: 1;
}

.mh-institution-item .institution-website {
    font-size: 0.75rem;
    text-decoration: none;
    opacity: 0.6;
    transition: opacity 0.2s;
}

.mh-institution-item .institution-website:hover {
    opacity: 1;
}

.mh-protocol-item .source,
.mh-institution-item .count {
    display: block;
    font-size: 0.75rem;
    color: var(--text-muted, #8b949e);
    margin-top: 2px;
}

.mh-empty-item {
    color: var(--text-muted, #8b949e);
    font-size: 0.85rem;
    font-style: italic;
}

/* Responsive */
@media (max-width: 1200px) {
    .mh-main-layout {
        grid-template-columns: 1fr 280px;
        gap: 24px;
    }
}

@media (max-width: 1024px) {
    .mh-main-layout {
        grid-template-columns: 1fr;
    }
    .mh-sidebar {
        position: static;
        flex-direction: row;
        flex-wrap: wrap;
    }
    .mh-sidebar-widget {
        flex: 1;
        min-width: 280px;
    }
    .mh-papers-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .mh-search-bar { flex-direction: column; }
    .mh-filter-row { flex-direction: column; }
    .mh-filter-item select { width: 100%; }
    .mh-papers-grid { grid-template-columns: 1fr; }
    .mh-sidebar-widget { min-width: 100%; }
    .mh-results-header { flex-direction: column; align-items: flex-start; }
}
</style>

<script>
// Global function for institution filtering (called from sidebar links)
function filterByInstitution(institutionSlug) {
    // Access the activeFilters via the IIFE scope workaround
    if (window.mhFilterByInstitution) {
        window.mhFilterByInstitution(institutionSlug);
    }
}

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

    // Expose institution filter function globally
    window.mhFilterByInstitution = function(institutionSlug) {
        // Clear other filters but keep institution
        activeFilters = { facility: institutionSlug };
        currentPage = 1;

        // Update UI to show we're filtering
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('[data-filter]').forEach(s => { if (s.tagName === 'SELECT') s.value = ''; });

        // Highlight the active institution in sidebar
        document.querySelectorAll('.institution-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.institution === institutionSlug) {
                link.classList.add('active');
            }
        });

        searchProtocols();
    };

    // Expose author search function globally
    window.searchByAuthor = function(authorName) {
        // Clear filters and set author filter
        activeFilters = { author: authorName };
        currentPage = 1;
        
        // Update UI
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('[data-filter]').forEach(s => { if (s.tagName === 'SELECT') s.value = ''; });
        
        // Clear the search input (we're using author filter, not search)
        if (searchInput) {
            searchInput.value = '';
            searchInput.placeholder = 'Filtering by: ' + authorName;
        }
        
        // Scroll to top of results
        const searchSection = document.querySelector('.mh-search-section');
        if (searchSection) {
            window.scrollTo({ top: searchSection.offsetTop - 20, behavior: 'smooth' });
        }
        
        searchProtocols();
    };
    
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
        searchInput.placeholder = 'Search protocols by title, author, technique...';
        document.querySelectorAll('[data-filter]').forEach(s => { if (s.tagName === 'SELECT') s.value = ''; });
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        // Clear institution links in sidebar
        document.querySelectorAll('.institution-link').forEach(link => link.classList.remove('active'));
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
        if (activeFilters.facility) params.set('facility', activeFilters.facility);
        
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
        if (activeFilters.author) params.set('author', activeFilters.author);
        
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
    
    // Create protocol card - matches homepage paper card layout exactly
    function createProtocolCard(protocol) {
        const citations = parseInt(protocol.citations) || 0;
        let badgeClass = 'standard';
        let badgeText = formatNumber(citations) + ' citations';
        
        if (citations >= 100) { badgeClass = 'foundational'; badgeText = '🏆 Foundational'; }
        else if (citations >= 50) { badgeClass = 'high-impact'; badgeText = '⭐ High Impact'; }
        
        // Tags - same as homepage
        let tagsHtml = '';
        if (protocol.techniques?.length) {
            tagsHtml += protocol.techniques.slice(0, 2).map(t => 
                `<span class="mh-card-tag technique">${escapeHtml(t)}</span>`
            ).join('');
        }
        if (protocol.microscopes?.length) {
            tagsHtml += `<span class="mh-card-tag microscope">🔬 ${escapeHtml(protocol.microscopes[0])}</span>`;
        }
        if (protocol.organisms?.length) {
            tagsHtml += protocol.organisms.slice(0, 1).map(o => 
                `<span class="mh-card-tag organism">${escapeHtml(o)}</span>`
            ).join('');
        }
        if (protocol.microscope_brands?.length) {
            tagsHtml += `<span class="mh-card-tag brand">🏭 ${escapeHtml(protocol.microscope_brands[0])}</span>`;
        }
        
        // Enrichment badges - same as homepage
        let enrichmentHtml = '';
        const items = [];
        if (protocol.protocols?.length) items.push(`<span class="mh-enrichment-item protocols">📋 ${protocol.protocols.length}</span>`);
        if (protocol.github_url) items.push(`<span class="mh-enrichment-item github">💻 Code</span>`);
        if (protocol.repositories?.length) items.push(`<span class="mh-enrichment-item">💾 Data</span>`);
        if (protocol.has_figures || protocol.figure_count > 0) items.push(`<span class="mh-enrichment-item figures">📊 ${protocol.figure_count || 'Figs'}</span>`);
        if (protocol.fluorophores?.length) items.push(`<span class="mh-enrichment-item fluor" title="${escapeHtml(protocol.fluorophores.slice(0,3).join(', '))}">🧬 ${protocol.fluorophores.length}</span>`);
        if (protocol.sample_preparation?.length) items.push(`<span class="mh-enrichment-item sample-prep" title="${escapeHtml(protocol.sample_preparation.slice(0,3).join(', '))}">🧫 ${protocol.sample_preparation.length}</span>`);
        if (protocol.cell_lines?.length) items.push(`<span class="mh-enrichment-item cell-line" title="${escapeHtml(protocol.cell_lines.join(', '))}">🔬 ${protocol.cell_lines.length}</span>`);
        if (protocol.rrids?.length) items.push(`<span class="mh-enrichment-item rrids">🏷️ ${protocol.rrids.length}</span>`);
        if (items.length) enrichmentHtml = `<div class="mh-card-enrichment">${items.join('')}</div>`;
        
        // Links - same as homepage
        let linksHtml = '';
        if (protocol.doi) linksHtml += `<a href="https://doi.org/${escapeHtml(protocol.doi)}" class="mh-card-link doi" target="_blank">DOI</a>`;
        if (protocol.pubmed_id) linksHtml += `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(protocol.pubmed_id)}/" class="mh-card-link pubmed" target="_blank">PubMed</a>`;
        if (protocol.github_url) linksHtml += `<a href="${escapeHtml(protocol.github_url)}" class="mh-card-link github" target="_blank">GitHub</a>`;
        
        // Parse authors - handle both array and string formats
        let authorsHtml = '';
        let authorsList = [];
        if (protocol.authors) {
            if (Array.isArray(protocol.authors)) {
                authorsList = protocol.authors;
            } else if (typeof protocol.authors === 'string') {
                authorsList = parseAuthors(protocol.authors);
            }
        }
        
        if (authorsList.length > 0) {
            const firstAuthor = authorsList[0];
            const lastAuthor = authorsList.length > 1 ? authorsList[authorsList.length - 1] : null;
            
            authorsHtml = `<div class="mh-card-authors">`;
            authorsHtml += `<a href="#" class="mh-author-link" data-author="${escapeHtml(firstAuthor)}" onclick="searchByAuthor(this.dataset.author); return false;">${escapeHtml(firstAuthor)}</a>`;
            
            if (lastAuthor && lastAuthor !== firstAuthor) {
                if (authorsList.length > 2) {
                    authorsHtml += `<span class="mh-author-sep"> ... </span>`;
                } else {
                    authorsHtml += `<span class="mh-author-sep">, </span>`;
                }
                authorsHtml += `<a href="#" class="mh-author-link mh-last-author" data-author="${escapeHtml(lastAuthor)}" onclick="searchByAuthor(this.dataset.author); return false;">${escapeHtml(lastAuthor)}</a>`;
            }
            authorsHtml += `</div>`;
        }
        
        // Source badge for protocols (small label)
        const sourceClass = getSourceClass(protocol.source);
        const sourceLabel = protocol.source ? `<span class="mh-card-source-label ${sourceClass}">${escapeHtml(protocol.source)}</span>` : '';
        
        return `
            <article class="mh-paper-card">
                <span class="mh-card-badge ${badgeClass}">${badgeText}</span>
                <h3 class="mh-card-title"><a href="${escapeHtml(protocol.permalink)}">${escapeHtml(protocol.title)}</a></h3>
                ${authorsHtml}
                <div class="mh-card-meta">
                    ${sourceLabel}
                    ${protocol.journal ? `<span>${escapeHtml(protocol.journal)}</span>` : ''}
                    ${protocol.year ? `<span>${protocol.year}</span>` : ''}
                    <span>${formatNumber(citations)} citations</span>
                </div>
                ${tagsHtml ? `<div class="mh-card-tags">${tagsHtml}</div>` : ''}
                ${enrichmentHtml}
                <div class="mh-card-footer">
                    <div class="mh-card-links">${linksHtml}</div>
                </div>
            </article>
        `;
    }
    
    // Parse authors string into array (same as homepage)
    function parseAuthors(authorsString) {
        if (!authorsString) return [];
        let normalized = authorsString.replace(/\s+and\s+|\s*&\s*/gi, ', ');
        let authors = normalized.split(/[,;]\s*/);
        return authors.map(a => a.trim()).filter(a => a && a.length > 1);
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
