<?php
/**
 * Page Template for Facilities
 * WordPress automatically uses this for pages with slug "facilities"
 * Lists all microscopy facilities with their associated paper counts
 */
get_header();

// Check if plugin is active
if (!function_exists('mh_plugin_active') || !mh_plugin_active()) {
    ?>
    <div class="mh-container" style="padding: 80px 20px; text-align: center;">
        <h1>🏛️ Facilities</h1>
        <p style="color: var(--text-muted); margin: 20px 0;">The MicroHub plugin is required for full functionality.</p>
    </div>
    <?php
    get_footer();
    return;
}

// Get search/filter parameters
$search = isset($_GET['search']) ? sanitize_text_field($_GET['search']) : '';
$sort = isset($_GET['sort']) ? sanitize_text_field($_GET['sort']) : 'count';

// Get all facilities from taxonomy
$facility_args = array(
    'taxonomy' => 'mh_facility',
    'hide_empty' => true,
    'orderby' => $sort === 'name' ? 'name' : 'count',
    'order' => $sort === 'name' ? 'ASC' : 'DESC',
);

if ($search) {
    $facility_args['name__like'] = $search;
}

$facilities = array();
if (taxonomy_exists('mh_facility')) {
    $terms = get_terms($facility_args);
    if (!is_wp_error($terms)) {
        foreach ($terms as $term) {
            $website = get_term_meta($term->term_id, 'facility_website', true);
            $location = get_term_meta($term->term_id, 'facility_location', true);
            $description = term_description($term->term_id, 'mh_facility');
            
            $facilities[] = array(
                'id' => $term->term_id,
                'name' => $term->name,
                'slug' => $term->slug,
                'count' => intval($term->count),
                'url' => get_term_link($term),
                'website' => $website ?: '',
                'location' => $location ?: '',
                'description' => $description ?: '',
            );
        }
    }
}

$total_facilities = count($facilities);
$total_papers = array_sum(array_column($facilities, 'count'));

// Get techniques that facilities work with
$technique_counts = array();
if (taxonomy_exists('mh_technique')) {
    $all_techniques = get_terms(array(
        'taxonomy' => 'mh_technique',
        'hide_empty' => true,
        'orderby' => 'count',
        'order' => 'DESC',
        'number' => 20,
    ));
    if (!is_wp_error($all_techniques)) {
        $technique_counts = $all_techniques;
    }
}
?>

<!-- Hero -->
<section class="mh-hero-compact">
    <div class="mh-container">
        <h1>🏛️ Facilities</h1>
        <p>Browse <?php echo number_format($total_facilities); ?> microscopy core facilities</p>
    </div>
</section>

<!-- Search Section -->
<section class="mh-search-section">
    <div class="mh-container">
        <form method="get" action="" class="mh-search-bar">
            <div class="mh-search-input-wrapper">
                <svg class="mh-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                <input type="text" name="search" id="mh-search-input" placeholder="Search facilities by name..." value="<?php echo esc_attr($search); ?>">
            </div>
            <button type="submit" class="mh-search-button">Search</button>
        </form>
        
        <div class="mh-filter-row">
            <div class="mh-filter-item">
                <select name="sort" id="mh-sort" onchange="this.form.submit()">
                    <option value="count" <?php selected($sort, 'count'); ?>>Most Papers</option>
                    <option value="name" <?php selected($sort, 'name'); ?>>Name A-Z</option>
                </select>
            </div>
            <?php if ($search): ?>
                <a href="<?php echo esc_url(remove_query_arg('search')); ?>" class="mh-clear-btn">✕ Clear Search</a>
            <?php endif; ?>
        </div>
    </div>
</section>

<!-- Results Section -->
<section class="mh-results-section">
    <div class="mh-container">
        <!-- Stats Bar -->
        <div class="mh-facility-stats-bar">
            <div class="mh-stat-item">
                <span class="stat-icon">🏛️</span>
                <span class="stat-num"><?php echo number_format($total_facilities); ?></span>
                <span class="stat-label">Facilities</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">📄</span>
                <span class="stat-num"><?php echo number_format($total_papers); ?></span>
                <span class="stat-label">Associated Papers</span>
            </div>
            <div class="mh-stat-item">
                <span class="stat-icon">🔬</span>
                <span class="stat-num"><?php echo count($technique_counts); ?>+</span>
                <span class="stat-label">Techniques</span>
            </div>
        </div>

        <?php if ($search): ?>
            <div class="mh-results-info" style="margin-bottom: 20px;">
                Showing <?php echo count($facilities); ?> facilities matching "<strong><?php echo esc_html($search); ?></strong>"
            </div>
        <?php endif; ?>

        <?php if (empty($facilities)): ?>
            <div class="mh-no-results">
                <span class="icon">🏛️</span>
                <h3>No facilities found</h3>
                <p><?php echo $search ? 'Try a different search term.' : 'No facilities have been added yet.'; ?></p>
            </div>
        <?php else: ?>
            <div class="mh-facilities-grid">
                <?php foreach ($facilities as $facility): ?>
                    <article class="mh-facility-card">
                        <div class="mh-facility-header">
                            <div class="mh-facility-icon">🏛️</div>
                            <div class="mh-facility-meta">
                                <span class="mh-facility-papers"><?php echo number_format($facility['count']); ?> papers</span>
                            </div>
                        </div>
                        
                        <h3 class="mh-facility-name">
                            <a href="<?php echo esc_url($facility['url']); ?>">
                                <?php echo esc_html($facility['name']); ?>
                            </a>
                        </h3>
                        
                        <?php if ($facility['location']): ?>
                            <div class="mh-facility-location">
                                📍 <?php echo esc_html($facility['location']); ?>
                            </div>
                        <?php endif; ?>
                        
                        <?php if ($facility['description']): ?>
                            <p class="mh-facility-description">
                                <?php echo wp_trim_words(wp_strip_all_tags($facility['description']), 25, '...'); ?>
                            </p>
                        <?php endif; ?>
                        
                        <div class="mh-facility-actions">
                            <a href="<?php echo esc_url($facility['url']); ?>" class="mh-btn mh-btn-sm mh-btn-primary">
                                View Papers →
                            </a>
                            <?php if ($facility['website']): ?>
                                <a href="<?php echo esc_url($facility['website']); ?>" class="mh-btn mh-btn-sm mh-btn-secondary" target="_blank" rel="noopener">
                                    Website ↗
                                </a>
                            <?php endif; ?>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
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
.mh-search-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.mh-search-input-wrapper { flex: 1; position: relative; }
.mh-search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 20px; height: 20px; color: var(--text-muted, #8b949e); }
.mh-search-input-wrapper input { width: 100%; padding: 12px 14px 12px 44px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 8px; color: var(--text, #c9d1d9); font-size: 1rem; }
.mh-search-input-wrapper input:focus { outline: none; border-color: var(--primary, #58a6ff); }
.mh-search-button { padding: 12px 24px; background: var(--primary, #58a6ff); color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.mh-search-button:hover { background: var(--primary-hover, #79b8ff); }

/* Filter Row */
.mh-filter-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.mh-filter-item select { padding: 8px 12px; background: var(--bg, #0d1117); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); font-size: 0.9rem; cursor: pointer; }
.mh-clear-btn { padding: 8px 14px; background: transparent; border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text-light, #6e7681); cursor: pointer; font-size: 0.85rem; text-decoration: none; }
.mh-clear-btn:hover { border-color: #f85149; color: #f85149; }

/* Results Section */
.mh-results-section { padding: 24px 0 60px; }
.mh-results-info { color: var(--text-muted, #8b949e); font-size: 0.9rem; }
.mh-results-info strong { color: var(--text, #c9d1d9); }

/* Stats Bar */
.mh-facility-stats-bar { display: flex; flex-wrap: wrap; gap: 24px; margin-bottom: 24px; padding: 20px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; }
.mh-stat-item { display: flex; align-items: center; gap: 10px; }
.mh-stat-item .stat-icon { font-size: 1.5rem; }
.mh-stat-item .stat-num { font-weight: 700; color: var(--primary, #58a6ff); font-size: 1.25rem; }
.mh-stat-item .stat-label { color: var(--text-muted, #8b949e); font-size: 0.9rem; }

/* Facilities Grid */
.mh-facilities-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }

/* Facility Card */
.mh-facility-card { background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; padding: 24px; display: flex; flex-direction: column; transition: border-color 0.2s, transform 0.2s; }
.mh-facility-card:hover { border-color: var(--primary, #58a6ff); transform: translateY(-2px); }

.mh-facility-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.mh-facility-icon { font-size: 2rem; background: linear-gradient(135deg, var(--primary, #58a6ff), #a371f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.mh-facility-meta { text-align: right; }
.mh-facility-papers { display: inline-block; padding: 4px 10px; background: var(--bg-hover, #21262d); border-radius: 20px; font-size: 0.8rem; color: var(--primary, #58a6ff); font-weight: 600; }

.mh-facility-name { font-size: 1.15rem; font-weight: 600; margin: 0 0 8px 0; line-height: 1.3; }
.mh-facility-name a { color: var(--text, #c9d1d9); text-decoration: none; }
.mh-facility-name a:hover { color: var(--primary, #58a6ff); }

.mh-facility-location { font-size: 0.85rem; color: var(--text-muted, #8b949e); margin-bottom: 10px; }

.mh-facility-description { font-size: 0.9rem; color: var(--text-light, #8b949e); line-height: 1.5; margin: 0 0 16px 0; flex: 1; }

.mh-facility-actions { display: flex; gap: 10px; margin-top: auto; padding-top: 16px; border-top: 1px solid var(--border, #30363d); }
.mh-btn { display: inline-block; padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; font-weight: 500; text-decoration: none; cursor: pointer; border: none; transition: all 0.2s; }
.mh-btn-sm { padding: 6px 12px; font-size: 0.8rem; }
.mh-btn-primary { background: var(--primary, #58a6ff); color: #fff; }
.mh-btn-primary:hover { background: var(--primary-hover, #79b8ff); }
.mh-btn-secondary { background: var(--bg-hover, #21262d); color: var(--text, #c9d1d9); border: 1px solid var(--border, #30363d); }
.mh-btn-secondary:hover { background: var(--border, #30363d); }

/* No Results */
.mh-no-results { text-align: center; padding: 60px 20px; background: var(--bg-card, #161b22); border-radius: 8px; }
.mh-no-results .icon { font-size: 3rem; display: block; margin-bottom: 16px; }
.mh-no-results h3 { margin: 0 0 8px 0; color: var(--text, #c9d1d9); }
.mh-no-results p { color: var(--text-muted, #8b949e); margin: 0; }

/* Responsive */
@media (max-width: 768px) {
    .mh-search-bar { flex-direction: column; }
    .mh-facilities-grid { grid-template-columns: 1fr; }
    .mh-facility-stats-bar { flex-direction: column; gap: 16px; }
    .mh-facility-actions { flex-direction: column; }
    .mh-btn { text-align: center; }
}
</style>

<?php get_footer(); ?>
