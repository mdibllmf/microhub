<?php
/**
 * Protocols Page Template - Full Search Interface
 * Visually identical to front-page.php
 */
get_header();

// Check if plugin is active
if (!function_exists('mh_plugin_active') || !mh_plugin_active()) {
    ?>
    <div class="mh-container" style="padding: 80px 20px; text-align: center;">
        <h1>📋 Protocols</h1>
        <p style="color: var(--text-muted); margin: 20px 0;">The MicroHub plugin is required for full functionality.</p>
        <p style="color: var(--text-muted);">Please activate the MicroHub plugin to access the protocol search.</p>
    </div>
    <?php
    get_footer();
    return;
}

$stats = mh_get_stats();
$api_base = rest_url('microhub-theme/v1');

// Get actual filter options from database
$filter_options = array(
    'techniques' => array(),
    'microscopes' => array(),
    'organisms' => array(),
    'software' => array(),
    'institutions' => array(),
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

// Institutions (uses mh_facility taxonomy for backward compatibility)
if (taxonomy_exists('mh_facility')) {
    $terms = get_terms(array('taxonomy' => 'mh_facility', 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
    if (!is_wp_error($terms)) {
        $filter_options['institutions'] = $terms;
    }
}

// Equipment & Reagent taxonomies
$equipment_taxonomies = array(
    'reagent_suppliers' => 'mh_reagent_supplier',
    'general_software' => 'mh_general_software',
    'lasers' => 'mh_laser',
    'detectors' => 'mh_detector',
    'objectives' => 'mh_objective',
    'filters' => 'mh_filter',
);
foreach ($equipment_taxonomies as $key => $taxonomy) {
    $filter_options[$key] = array();
    if (taxonomy_exists($taxonomy)) {
        $terms = get_terms(array('taxonomy' => $taxonomy, 'hide_empty' => true, 'orderby' => 'count', 'order' => 'DESC'));
        if (!is_wp_error($terms)) {
            $filter_options[$key] = $terms;
        }
    }
}

// Get meta-based filter options (fluorophores, sample prep, cell lines, etc.)
$meta_filter_options = mh_get_all_filter_options();
?>

<!-- Compact Hero -->
<section class="mh-hero-compact">
    <div class="mh-container">
        <h1>📋 Protocols</h1>
        <p>Search <?php echo number_format($stats['with_protocols']); ?> microscopy protocols</p>
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
                <input type="text" id="mh-search-input" placeholder="Search by title, author, DOI, abstract...">
            </div>
            <button type="button" id="mh-search-btn" class="mh-search-button">Search</button>
        </div>


        <!-- Filter Row - Dynamically populated from database -->
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
                <select id="filter-citations" data-filter="citations">
                    <option value="">Any Citations</option>
                    <option value="100">100+ (Foundational)</option>
                    <option value="50">50+ (High Impact)</option>
                    <option value="25">25+</option>
                    <option value="10">10+</option>
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
                <select id="filter-analysis-sw" data-filter="analysis_software">
                    <option value="">Analysis Software (<?php echo count($meta_filter_options['image_analysis_software']); ?>)</option>
                    <?php foreach ($meta_filter_options['image_analysis_software'] as $sw => $count): ?>
                    <option value="<?php echo esc_attr($sw); ?>"><?php echo esc_html($sw); ?> (<?php echo $count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-institution" data-filter="institution">
                    <option value="">All Institutions (<?php echo count($filter_options['institutions']); ?>)</option>
                    <?php foreach ($filter_options['institutions'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-reagent-supplier" data-filter="reagent_supplier">
                    <option value="">All Suppliers (<?php echo count($filter_options['reagent_suppliers']); ?>)</option>
                    <?php foreach ($filter_options['reagent_suppliers'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-general-software" data-filter="general_software">
                    <option value="">General Software (<?php echo count($filter_options['general_software']); ?>)</option>
                    <?php foreach ($filter_options['general_software'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-laser" data-filter="laser">
                    <option value="">All Lasers (<?php echo count($filter_options['lasers']); ?>)</option>
                    <?php foreach ($filter_options['lasers'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-detector" data-filter="detector">
                    <option value="">All Detectors (<?php echo count($filter_options['detectors']); ?>)</option>
                    <?php foreach ($filter_options['detectors'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-objective" data-filter="objective">
                    <option value="">All Objectives (<?php echo count($filter_options['objectives']); ?>)</option>
                    <?php foreach ($filter_options['objectives'] as $term): ?>
                    <option value="<?php echo esc_attr($term->slug); ?>"><?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)</option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="mh-filter-item">
                <select id="filter-optical-filter" data-filter="optical_filter">
                    <option value="">All Filters (<?php echo count($filter_options['filters']); ?>)</option>
                    <?php foreach ($filter_options['filters'] as $term): ?>
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
            <button type="button" class="mh-quick-btn" data-filter="has_github">💻 GitHub <span id="count-github"><?php echo $stats['with_github']; ?></span></button>
            <button type="button" class="mh-quick-btn" data-filter="has_repositories">💾 Data <span id="count-repos"><?php echo $stats['with_repositories']; ?></span></button>
            <button type="button" class="mh-quick-btn" data-filter="has_figures">📊 Figures <span id="count-figures"><?php echo $stats['with_figures']; ?></span></button>
            <button type="button" class="mh-quick-btn" data-filter="has_rrids">🏷️ RRIDs <span id="count-rrids"><?php echo $stats['with_rrids']; ?></span></button>
            <button type="button" id="mh-clear-filters" class="mh-clear-btn">✕ Clear</button>
        </div>
    </div>
</section>

<!-- Results Section with Sidebar -->
<section class="mh-results-section">
    <div class="mh-container">
        <div class="mh-results-header">
            <div class="mh-results-info">
                Showing <strong id="mh-showing">0</strong> of <strong id="mh-total"><?php echo $stats['with_protocols']; ?></strong> protocols
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
                <div id="mh-papers-grid" class="mh-papers-grid">
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
            $protocol_papers = mh_get_recent_protocol_papers(8);
            // Get institutions
            $institutions = mh_get_institutions(10);
            ?>
            <aside class="mh-sidebar">
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

<!-- Stats Bar -->
<section class="mh-stats-bar">
    <div class="mh-container">
        <div class="mh-stats-row">
            <div class="mh-stat-item">
                <span class="num"><?php echo number_format($stats['papers']); ?></span>
                <span class="lbl">Papers</span>
            </div>
            <div class="mh-stat-item">
                <span class="num"><?php echo number_format($stats['with_protocols']); ?></span>
                <span class="lbl">Protocols</span>
            </div>
            <div class="mh-stat-item">
                <span class="num"><?php echo number_format($stats['techniques']); ?></span>
                <span class="lbl">Techniques</span>
            </div>
            <div class="mh-stat-item">
                <span class="num"><?php echo number_format($stats['with_github']); ?></span>
                <span class="lbl">With Code</span>
            </div>
            <div class="mh-stat-item">
                <span class="num"><?php echo number_format($stats['with_repositories']); ?></span>
                <span class="lbl">Data Repos</span>
            </div>
            <div class="mh-stat-item">
                <span class="num"><?php echo number_format($stats['with_rrids']); ?></span>
                <span class="lbl">RRIDs</span>
            </div>
            <div class="mh-stat-item">
                <span class="num"><?php echo number_format($stats['microscopes']); ?></span>
                <span class="lbl">Microscopes</span>
            </div>
        </div>
    </div>
</section>

<style>
/* Compact Hero */
.mh-hero-compact {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-dark));
    padding: 24px 0;
    text-align: center;
    border-bottom: 1px solid var(--border);
}
.mh-hero-compact h1 { font-size: 1.75rem; margin-bottom: 4px; }
.mh-hero-compact p { color: var(--text-muted); margin: 0; }

/* Search Section */
.mh-search-section {
    background: var(--bg-card);
    padding: 24px 0;
    border-bottom: 1px solid var(--border);
}

.mh-search-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}

.mh-search-input-wrapper {
    flex: 1;
    position: relative;
}

.mh-search-icon {
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    color: var(--text-muted);
}

#mh-search-input {
    width: 100%;
    padding: 14px 14px 14px 48px;
    background: var(--bg-dark);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 1rem;
}

#mh-search-input:focus {
    outline: none;
    border-color: var(--primary);
}

.mh-search-button {
    padding: 14px 32px;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
}

.mh-search-button:hover {
    background: #4a94e8;
}

/* Filter Row */
.mh-filter-row {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}

@media (max-width: 1024px) {
    .mh-filter-row { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 640px) {
    .mh-filter-row { grid-template-columns: repeat(2, 1fr); }
    .mh-search-bar { flex-direction: column; }
}

.mh-filter-item select {
    width: 100%;
    padding: 10px 12px;
    background: var(--bg-dark);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 0.9rem;
    cursor: pointer;
}

.mh-filter-item select:focus {
    outline: none;
    border-color: var(--primary);
}

/* Advanced Filters Row */
.mh-filter-row-advanced {
    background: rgba(59, 130, 246, 0.05);
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    border: 1px solid rgba(59, 130, 246, 0.1);
    grid-template-columns: repeat(5, 1fr);
}

@media (max-width: 1024px) {
    .mh-filter-row-advanced { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 640px) {
    .mh-filter-row-advanced { grid-template-columns: repeat(2, 1fr); }
}

.mh-advanced-toggle {
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
}

.mh-toggle-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-muted);
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
}

.mh-toggle-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
}

.mh-toggle-btn.active {
    color: var(--primary);
    border-color: var(--primary);
}

.mh-toggle-btn.active .toggle-icon {
    transform: rotate(180deg);
}

.toggle-icon {
    transition: transform 0.2s;
}

/* Quick Filters */
.mh-quick-filters {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
}

.mh-quick-label {
    color: var(--text-muted);
    font-size: 0.85rem;
    font-weight: 500;
}

.mh-quick-btn {
    padding: 6px 14px;
    background: var(--bg-dark);
    border: 1px solid var(--border);
    border-radius: 20px;
    color: var(--text-muted);
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
}

.mh-quick-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
}

.mh-quick-btn.active {
    background: var(--primary);
    border-color: var(--primary);
    color: white;
}

.mh-quick-btn span {
    background: rgba(255,255,255,0.2);
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 0.75rem;
    margin-left: 4px;
}

.mh-clear-btn {
    padding: 6px 14px;
    background: transparent;
    border: none;
    color: var(--danger);
    font-size: 0.85rem;
    cursor: pointer;
}

.mh-clear-btn:hover {
    text-decoration: underline;
}

/* Results Section */
.mh-results-section {
    padding: 32px 0;
}

.mh-results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 12px;
}

.mh-results-info {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.mh-results-sort select {
    padding: 8px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 0.9rem;
}

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

/* Papers Grid */
.mh-papers-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    min-height: 400px;
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
    background: var(--bg-card);
    border: 1px solid var(--border);
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
    color: var(--text);
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
}

.mh-sidebar-widget h3 .icon {
    font-size: 1rem;
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
    border-bottom: 1px solid var(--border);
}

.mh-protocol-item:last-child,
.mh-institution-item:last-child {
    border-bottom: none;
}

.mh-protocol-item .protocol-link,
.mh-institution-item .institution-link {
    display: block;
    color: var(--text);
    text-decoration: none;
    font-size: 0.85rem;
    line-height: 1.4;
    transition: color 0.2s;
}

.mh-protocol-item .protocol-link:hover,
.mh-institution-item .institution-link:hover {
    color: var(--primary);
}

.mh-institution-item .institution-link.active {
    color: var(--primary);
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
    color: var(--text-muted);
    margin-top: 2px;
}

.mh-empty-item {
    color: var(--text-muted);
    font-size: 0.85rem;
    font-style: italic;
}

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

@media (max-width: 640px) { 
    .mh-papers-grid { grid-template-columns: 1fr; }
    .mh-sidebar-widget { min-width: 100%; }
}

.mh-loading-indicator {
    grid-column: 1 / -1;
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.mh-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Paper Card */
.mh-paper-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
}

.mh-paper-card:hover {
    border-color: var(--primary);
    transform: translateY(-2px);
}

.mh-card-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 8px;
    width: fit-content;
}

.mh-card-badge.foundational { background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #1f2937; }
.mh-card-badge.high-impact { background: linear-gradient(135deg, #a78bfa, #8b5cf6); color: white; }
.mh-card-badge.standard { background: var(--bg-hover); color: var(--text-muted); }

.mh-card-title {
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 8px;
}

.mh-card-title a { color: var(--text); }
.mh-card-title a:hover { color: var(--primary); }

.mh-card-authors {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 4px;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
}

.mh-card-authors .mh-author-link {
    color: var(--text-muted);
    text-decoration: none;
}

.mh-card-authors .mh-author-link:hover {
    color: var(--primary);
    text-decoration: underline;
}

.mh-card-authors .mh-last-author {
    color: var(--primary);
    font-weight: 500;
}

.mh-card-authors .mh-author-sep {
    color: var(--text-muted);
}

.mh-card-meta {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 12px;
}

.mh-card-meta span { margin-right: 12px; }

.mh-card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 12px;
}

.mh-card-tag {
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 500;
    color: white;
}

.mh-card-tag.technique { background: var(--tag-technique); }
.mh-card-tag.microscope { background: var(--tag-microscope); }
.mh-card-tag.software { background: var(--tag-software); }

.mh-card-enrichment {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 0.8rem;
}

.mh-enrichment-item {
    color: var(--text-muted);
}

.mh-enrichment-item.protocols { color: var(--secondary); }
.mh-enrichment-item.github { color: var(--text-light); }
.mh-enrichment-item.rrids { color: #a371f7; }
.mh-enrichment-item.figures { color: #38bdf8; }
.mh-enrichment-item.fluor { color: #3fb950; }
.mh-enrichment-item.sample-prep { color: #f0883e; }
.mh-enrichment-item.cell-line { color: #d2a8ff; }

.mh-card-footer {
    margin-top: auto;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.mh-card-links {
    display: flex;
    gap: 6px;
}

.mh-card-link {
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    text-decoration: none;
    color: white;
}

.mh-card-link.doi { background: #1f6feb; }
.mh-card-link.pubmed { background: #326599; }
.mh-card-link.github { background: #24292f; }
.mh-card-link:hover { opacity: 0.9; }

/* Stats Bar */
.mh-stats-bar {
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    padding: 24px 0;
}

.mh-stats-row {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 32px;
}

.mh-stat-item {
    text-align: center;
}

.mh-stat-item .num {
    display: block;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
}

.mh-stat-item .lbl {
    display: block;
    font-size: 0.85rem;
    color: var(--text-muted);
}

/* Pagination */
.mh-pagination {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 32px;
}

.mh-pagination button {
    padding: 8px 14px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    cursor: pointer;
}

.mh-pagination button:hover:not(:disabled) {
    background: var(--bg-hover);
}

.mh-pagination button.active {
    background: var(--primary);
    border-color: var(--primary);
    color: white;
}

.mh-pagination button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.mh-no-results {
    grid-column: 1 / -1;
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.mh-no-results h3 { margin-bottom: 8px; color: var(--text); }

/* Card header row for badges */
.mh-card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    gap: 8px;
}

/* Source badges */
.mh-card-source {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.mh-card-source.jove { background: #1e3a5f; color: #58a6ff; }
.mh-card-source.nature-protocols { background: #2d1f3d; color: #a371f7; }
.mh-card-source.star-protocols { background: #3d2f1f; color: #f0883e; }
.mh-card-source.protocols-io { background: #1f3d2d; color: #56d364; }
.mh-card-source.bio-protocol { background: #3d1f2d; color: #f778ba; }
.mh-card-source.protocol-journal { background: #1f2d3d; color: #58a6ff; }
.mh-card-source { background: var(--bg-hover); color: var(--text-muted); }

/* Protocol type cards */
.mh-paper-card.protocol_paper { border-left: 3px solid var(--primary); }
.mh-paper-card.imported { border-left: 3px solid #56d364; }
</style>

<script>
// Global function for institution filtering (called from sidebar links)
function filterByInstitution(institutionSlug) {
    if (window.mhFilterByInstitution) {
        window.mhFilterByInstitution(institutionSlug);
    }
}

(function() {
    const apiBase = <?php echo json_encode($api_base); ?>;
    
    let currentPage = 1;
    let activeFilters = {};
    let searchTimeout = null;
    const perPage = 24;
    
    window.mhFilterByInstitution = function(institutionSlug) {
        activeFilters = { institution: institutionSlug };
        currentPage = 1;
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('[data-filter]').forEach(s => s.value = '');
        document.querySelectorAll('.institution-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.institution === institutionSlug) link.classList.add('active');
        });
        searchProtocols();
    };
    
    window.searchByAuthor = function(authorName) {
        activeFilters = { author: authorName };
        currentPage = 1;
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('[data-filter]').forEach(s => s.value = '');
        const searchInput = document.getElementById('mh-search-input');
        if (searchInput) {
            searchInput.value = '';
            searchInput.placeholder = 'Filtering by: ' + authorName;
        }
        searchProtocols();
    };
    
    const searchInput = document.getElementById('mh-search-input');
    const searchBtn = document.getElementById('mh-search-btn');
    const papersGrid = document.getElementById('mh-papers-grid');
    const pagination = document.getElementById('mh-pagination');
    const showingEl = document.getElementById('mh-showing');
    const totalEl = document.getElementById('mh-total');
    const sortSelect = document.getElementById('mh-sort');
    const clearBtn = document.getElementById('mh-clear-filters');
    const advancedFilters = document.getElementById('advanced-filters');
    const toggleBtn = document.getElementById('toggle-advanced-filters');
    
    searchProtocols();
    
    if (toggleBtn && advancedFilters) {
        toggleBtn.addEventListener('click', () => {
            const isHidden = advancedFilters.style.display === 'none';
            advancedFilters.style.display = isHidden ? 'flex' : 'none';
            toggleBtn.querySelector('.toggle-text').textContent = isHidden ? 'Hide Advanced Filters' : 'Show Advanced Filters';
            toggleBtn.classList.toggle('active', isHidden);
        });
    }
    
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => { currentPage = 1; searchProtocols(); }, 400);
    });
    
    searchBtn.addEventListener('click', () => { currentPage = 1; searchProtocols(); });
    searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') { currentPage = 1; searchProtocols(); } });
    
    document.querySelectorAll('[data-filter]').forEach(select => {
        select.addEventListener('change', () => {
            const filter = select.dataset.filter;
            const value = select.value;
            if (value) activeFilters[filter] = value;
            else delete activeFilters[filter];
            currentPage = 1;
            searchProtocols();
        });
    });
    
    document.querySelectorAll('.mh-quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            if (btn.classList.contains('active')) {
                btn.classList.remove('active');
                delete activeFilters[filter];
            } else {
                document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
                delete activeFilters.foundational; delete activeFilters.high_impact;
                delete activeFilters.has_github; delete activeFilters.has_repositories;
                delete activeFilters.has_figures; delete activeFilters.has_rrids;
                btn.classList.add('active');
                activeFilters[filter] = true;
            }
            currentPage = 1;
            searchProtocols();
        });
    });
    
    sortSelect.addEventListener('change', () => { currentPage = 1; searchProtocols(); });
    
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.placeholder = 'Search by title, author, DOI, abstract...';
        document.querySelectorAll('[data-filter]').forEach(s => { if (s.tagName === 'SELECT') s.value = ''; });
        document.querySelectorAll('.mh-quick-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.institution-link').forEach(link => link.classList.remove('active'));
        activeFilters = {};
        currentPage = 1;
        if (advancedFilters) advancedFilters.style.display = 'none';
        if (toggleBtn) {
            toggleBtn.classList.remove('active');
            const toggleText = toggleBtn.querySelector('.toggle-text');
            if (toggleText) toggleText.textContent = 'Show Advanced Filters';
        }
        searchProtocols();
    });
    
    function searchProtocols() {
        papersGrid.innerHTML = '<div class="mh-loading-indicator"><div class="mh-spinner"></div><p>Loading protocols...</p></div>';
        
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
        
        if (activeFilters.technique) params.set('technique', activeFilters.technique);
        if (activeFilters.microscope) params.set('microscope', activeFilters.microscope);
        if (activeFilters.organism) params.set('organism', activeFilters.organism);
        if (activeFilters.software) params.set('software', activeFilters.software);
        if (activeFilters.institution) params.set('facility', activeFilters.institution);
        
        if (activeFilters.year) {
            if (activeFilters.year === '2024-2025') params.set('year_min', 2024);
            else if (activeFilters.year === '2020-2023') { params.set('year_min', 2020); params.set('year_max', 2023); }
            else if (activeFilters.year === '2015-2019') { params.set('year_min', 2015); params.set('year_max', 2019); }
            else if (activeFilters.year === '2010-2014') { params.set('year_min', 2010); params.set('year_max', 2014); }
            else if (activeFilters.year === 'before-2010') params.set('year_max', 2009);
        }
        
        if (activeFilters.citations) params.set('citations_min', activeFilters.citations);
        if (activeFilters.foundational) params.set('citations_min', 100);
        if (activeFilters.high_impact) params.set('citations_min', 50);
        if (activeFilters.has_github) params.set('has_github', true);
        if (activeFilters.has_figures) params.set('has_figures', true);
        if (activeFilters.has_repositories) params.set('has_repositories', true);
        if (activeFilters.has_rrids) params.set('has_rrids', true);
        if (activeFilters.fluorophore) params.set('fluorophore', activeFilters.fluorophore);
        if (activeFilters.sample_prep) params.set('sample_prep', activeFilters.sample_prep);
        if (activeFilters.cell_line) params.set('cell_line', activeFilters.cell_line);
        if (activeFilters.brand) params.set('brand', activeFilters.brand);
        if (activeFilters.author) params.set('author', activeFilters.author);
        
        // Use the /protocols endpoint which returns protocol papers (_mh_is_protocol = 1)
        fetch(apiBase + '/protocols?' + params.toString())
            .then(res => res.json())
            .then(data => {
                renderProtocols(data.protocols || []);
                renderPagination(data.total || 0, data.pages || 1);
                showingEl.textContent = (data.protocols || []).length;
                totalEl.textContent = formatNumber(data.total || 0);
            })
            .catch(err => {
                papersGrid.innerHTML = '<div class="mh-no-results"><h3>Error loading protocols</h3><p>Please try again.</p></div>';
            });
    }
    
    function renderProtocols(papers) {
        if (!papers.length) {
            papersGrid.innerHTML = '<div class="mh-no-results"><h3>No protocols found</h3><p>Try adjusting your search or filters.</p></div>';
            return;
        }
        papersGrid.innerHTML = papers.map(paper => createCard(paper)).join('');
    }
    
    function createCard(protocol) {
        const citations = parseInt(protocol.citations) || 0;
        let badgeClass = 'standard', badgeText = formatNumber(citations) + ' citations';
        if (citations >= 100) { badgeClass = 'foundational'; badgeText = '🏆 Foundational'; }
        else if (citations >= 50) { badgeClass = 'high-impact'; badgeText = '⭐ High Impact'; }
        
        let tagsHtml = '';
        // Handle both old string format and new object format {name, url}
        const getTagName = (t) => typeof t === 'object' ? t.name : t;
        const getTagUrl = (t) => typeof t === 'object' ? t.url : null;
        if (protocol.techniques?.length) {
            tagsHtml += protocol.techniques.slice(0, 2).map(t => {
                const name = getTagName(t);
                const url = getTagUrl(t);
                return url
                    ? `<a href="${escapeHtml(url)}" class="mh-card-tag technique">${escapeHtml(name)}</a>`
                    : `<span class="mh-card-tag technique">${escapeHtml(name)}</span>`;
            }).join('');
        }
        if (protocol.microscopes?.length) {
            const m = protocol.microscopes[0];
            const name = getTagName(m);
            const url = getTagUrl(m);
            tagsHtml += url
                ? `<a href="${escapeHtml(url)}" class="mh-card-tag microscope">🔬 ${escapeHtml(name)}</a>`
                : `<span class="mh-card-tag microscope">🔬 ${escapeHtml(name)}</span>`;
        }
        
        let enrichmentHtml = '';
        const items = [];
        if (protocol.protocols?.length) items.push(`<span class="mh-enrichment-item protocols">📋 ${protocol.protocols.length}</span>`);
        if (protocol.github_url) items.push(`<span class="mh-enrichment-item github">💻 Code</span>`);
        if (protocol.repositories?.length) items.push(`<span class="mh-enrichment-item">💾 Data</span>`);
        if (protocol.has_figures || protocol.figure_count > 0) items.push(`<span class="mh-enrichment-item figures">📊 ${protocol.figure_count || 'Figs'}</span>`);
        if (protocol.fluorophores?.length) items.push(`<span class="mh-enrichment-item fluor">🧬 ${protocol.fluorophores.length}</span>`);
        if (protocol.sample_preparation?.length) items.push(`<span class="mh-enrichment-item sample-prep">🧫 ${protocol.sample_preparation.length}</span>`);
        if (protocol.cell_lines?.length) items.push(`<span class="mh-enrichment-item cell-line">🔬 ${protocol.cell_lines.length}</span>`);
        if (protocol.rrids?.length) items.push(`<span class="mh-enrichment-item rrids">🏷️ ${protocol.rrids.length}</span>`);
        if (items.length) enrichmentHtml = `<div class="mh-card-enrichment">${items.join('')}</div>`;
        
        let linksHtml = '';
        if (protocol.doi) linksHtml += `<a href="https://doi.org/${escapeHtml(protocol.doi)}" class="mh-card-link doi" target="_blank">DOI</a>`;
        if (protocol.pubmed_id) linksHtml += `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(protocol.pubmed_id)}/" class="mh-card-link pubmed" target="_blank">PubMed</a>`;
        if (protocol.github_url) linksHtml += `<a href="${escapeHtml(protocol.github_url)}" class="mh-card-link github" target="_blank">GitHub</a>`;
        
        // Authors is already an array in protocol data
        let authorsHtml = '';
        const authorsList = protocol.authors || [];
        if (authorsList.length > 0) {
            const firstAuthor = authorsList[0];
            const lastAuthor = authorsList.length > 1 ? authorsList[authorsList.length - 1] : null;
            authorsHtml = `<div class="mh-card-authors">`;
            authorsHtml += `<a href="#" class="mh-author-link" onclick="searchByAuthor('${escapeHtml(firstAuthor)}'); return false;">${escapeHtml(firstAuthor)}</a>`;
            if (lastAuthor && lastAuthor !== firstAuthor) {
                authorsHtml += authorsList.length > 2 ? `<span class="mh-author-sep"> ... </span>` : `<span class="mh-author-sep">, </span>`;
                authorsHtml += `<a href="#" class="mh-author-link mh-last-author" onclick="searchByAuthor('${escapeHtml(lastAuthor)}'); return false;">${escapeHtml(lastAuthor)}</a>`;
            }
            authorsHtml += `</div>`;
        }
        
        // Source badge for protocol type
        let sourceHtml = '';
        if (protocol.source) {
            const sourceClass = protocol.source.toLowerCase().replace(/[^a-z]/g, '-');
            sourceHtml = `<span class="mh-card-source ${sourceClass}">${escapeHtml(protocol.source)}</span>`;
        }
        
        return `
            <article class="mh-paper-card ${protocol.type || ''}">
                <div class="mh-card-header-row">
                    ${sourceHtml}
                    <span class="mh-card-badge ${badgeClass}">${badgeText}</span>
                </div>
                <h3 class="mh-card-title"><a href="${escapeHtml(protocol.permalink)}">${escapeHtml(protocol.title)}</a></h3>
                ${authorsHtml}
                <div class="mh-card-meta">
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
    
    function renderPagination(total, totalPages) {
        if (totalPages <= 1) { pagination.innerHTML = ''; return; }
        let html = `<button ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">← Prev</button>`;
        const pages = [];
        if (totalPages <= 7) { for (let i = 1; i <= totalPages; i++) pages.push(i); }
        else {
            if (currentPage <= 4) pages.push(1, 2, 3, 4, 5, '...', totalPages);
            else if (currentPage >= totalPages - 3) pages.push(1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
            else pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
        }
        pages.forEach(page => {
            if (page === '...') html += '<span style="padding: 8px; color: var(--text-muted);">...</span>';
            else html += `<button data-page="${page}" class="${page === currentPage ? 'active' : ''}">${page}</button>`;
        });
        html += `<button ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">Next →</button>`;
        pagination.innerHTML = html;
        pagination.querySelectorAll('button:not(:disabled)').forEach(btn => {
            btn.addEventListener('click', () => {
                currentPage = parseInt(btn.dataset.page);
                searchProtocols();
                window.scrollTo({ top: document.querySelector('.mh-results-section').offsetTop - 100, behavior: 'smooth' });
            });
        });
    }
    
    function formatNumber(num) {
        if (!num) return '0';
        num = parseInt(num);
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toLocaleString();
    }
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
</script>

<?php get_footer(); ?>
