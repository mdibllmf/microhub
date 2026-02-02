<?php
/**
 * Protocols Page Template for MicroHub
 * Browse protocols from protocol journals, linked protocols, and community uploads
 */

// Get filter parameters
$search = isset($_GET['search']) ? sanitize_text_field($_GET['search']) : '';
$source_filter = isset($_GET['source']) ? sanitize_text_field($_GET['source']) : '';
$technique_filter = isset($_GET['technique']) ? sanitize_text_field($_GET['technique']) : '';
$paged = max(1, get_query_var('paged'));

// Get protocols URL
$protocols_url = mh_get_page_url('protocols');

global $wpdb;

$protocols = array();

// =============================================================================
// 1. PROTOCOL JOURNAL PAPERS (JoVE, Nature Protocols, STAR Protocols, etc.)
// These are mh_paper posts with _mh_is_protocol = 1
// =============================================================================
$protocol_papers_args = array(
    'post_type' => 'mh_paper',
    'posts_per_page' => -1,
    'post_status' => 'publish',
    'meta_query' => array(
        array(
            'key' => '_mh_is_protocol',
            'value' => '1',
            'compare' => '='
        )
    )
);

if ($search) {
    $protocol_papers_args['s'] = $search;
}

// Technique filter
if ($technique_filter) {
    $protocol_papers_args['tax_query'] = array(
        array(
            'taxonomy' => 'mh_technique',
            'field' => 'slug',
            'terms' => $technique_filter,
        )
    );
}

$protocol_papers = get_posts($protocol_papers_args);

foreach ($protocol_papers as $post) {
    $protocol_type = get_post_meta($post->ID, '_mh_protocol_type', true);
    $source = $protocol_type ?: 'Protocol Journal';
    
    // Apply source filter
    if ($source_filter && stripos($source, $source_filter) === false) {
        continue;
    }
    
    // Get taxonomies for this paper
    $techniques = wp_get_object_terms($post->ID, 'mh_technique', array('fields' => 'names'));
    $organisms = wp_get_object_terms($post->ID, 'mh_organism', array('fields' => 'names'));
    $microscopes = wp_get_object_terms($post->ID, 'mh_microscope', array('fields' => 'names'));
    
    // Get DOI for external link
    $doi = get_post_meta($post->ID, '_mh_doi', true);
    $external_url = $doi ? "https://doi.org/{$doi}" : '';
    
    // Get authors
    $authors = get_post_meta($post->ID, '_mh_authors', true);
    $author_list = array();
    if ($authors) {
        $authors_arr = json_decode($authors, true);
        if (is_array($authors_arr)) {
            $author_list = array_slice(array_column($authors_arr, 'name'), 0, 3);
        }
    }
    
    // Get year
    $year = get_post_meta($post->ID, '_mh_year', true);
    
    $protocols[] = array(
        'id' => $post->ID,
        'title' => $post->post_title,
        'url' => get_permalink($post->ID),
        'external_url' => $external_url,
        'source' => $source,
        'paper_id' => $post->ID,
        'paper_title' => null, // It IS the paper
        'date' => $post->post_date,
        'type' => 'protocol_paper',
        'techniques' => is_array($techniques) ? $techniques : array(),
        'organisms' => is_array($organisms) ? $organisms : array(),
        'microscopes' => is_array($microscopes) ? $microscopes : array(),
        'authors' => $author_list,
        'year' => $year,
        'abstract' => wp_trim_words($post->post_content, 30, '...'),
    );
}

// =============================================================================
// 2. USER-UPLOADED PROTOCOLS (mh_protocol post type)
// =============================================================================
$uploaded_args = array(
    'post_type' => 'mh_protocol',
    'posts_per_page' => -1,
    'post_status' => 'publish',
);

if ($search) {
    $uploaded_args['s'] = $search;
}

$uploaded_protocols = get_posts($uploaded_args);

foreach ($uploaded_protocols as $post) {
    $source = get_post_meta($post->ID, '_mh_protocol_source', true);
    if (empty($source)) {
        $source = 'Community';
    }
    
    if ($source_filter && stripos($source, $source_filter) === false) {
        continue;
    }
    
    $proto_url = get_post_meta($post->ID, '_mh_protocol_url', true);
    if (empty($proto_url)) {
        $proto_url = get_permalink($post->ID);
    }
    
    // Get linked paper if exists
    $linked_paper_id = get_post_meta($post->ID, '_mh_linked_paper', true);
    $linked_paper_title = null;
    if ($linked_paper_id) {
        $linked_paper = get_post($linked_paper_id);
        if ($linked_paper) {
            $linked_paper_title = $linked_paper->post_title;
        }
    }
    
    $protocols[] = array(
        'id' => $post->ID,
        'title' => $post->post_title,
        'url' => $proto_url,
        'external_url' => $proto_url,
        'source' => $source,
        'paper_id' => $linked_paper_id,
        'paper_title' => $linked_paper_title,
        'date' => $post->post_date,
        'type' => 'uploaded',
        'techniques' => array(),
        'organisms' => array(),
        'microscopes' => array(),
        'authors' => array(),
        'year' => null,
        'abstract' => wp_trim_words($post->post_content, 30, '...'),
    );
}

// =============================================================================
// 3. PROTOCOL URLs LINKED FROM PAPERS (_mh_protocols meta)
// =============================================================================
$paper_protocols_query = "
    SELECT p.ID, p.post_title, pm.meta_value 
    FROM {$wpdb->postmeta} pm
    JOIN {$wpdb->posts} p ON pm.post_id = p.ID
    WHERE pm.meta_key = '_mh_protocols' 
    AND pm.meta_value != '' 
    AND pm.meta_value != '[]'
    AND p.post_status = 'publish'
    AND p.post_type = 'mh_paper'
";

$paper_results = $wpdb->get_results($paper_protocols_query);

foreach ($paper_results as $paper) {
    $paper_protos = json_decode($paper->meta_value, true);
    if (!is_array($paper_protos)) continue;
    
    foreach ($paper_protos as $proto) {
        $proto_name = isset($proto['name']) ? $proto['name'] : 'Protocol';
        $proto_url = isset($proto['url']) ? $proto['url'] : '';
        
        if (empty($proto_url)) continue;
        
        // Detect source from URL
        $source = 'Other';
        $url_lower = strtolower($proto_url);
        
        if (strpos($url_lower, 'protocols.io') !== false) {
            $source = 'protocols.io';
        } elseif (strpos($url_lower, 'bio-protocol') !== false) {
            $source = 'Bio-protocol';
        } elseif (strpos($url_lower, 'jove.com') !== false) {
            $source = 'JoVE';
        } elseif (strpos($url_lower, 'nature.com/nprot') !== false) {
            $source = 'Nature Protocols';
        } elseif (strpos($url_lower, 'star-protocols') !== false) {
            $source = 'STAR Protocols';
        }
        
        // Apply source filter
        if ($source_filter && stripos($source, $source_filter) === false) {
            continue;
        }
        
        // Apply search filter
        if ($search) {
            $search_lower = strtolower($search);
            if (strpos(strtolower($proto_name), $search_lower) === false && 
                strpos(strtolower($paper->post_title), $search_lower) === false) {
                continue;
            }
        }
        
        // Get paper's techniques for filtering
        $paper_techniques = wp_get_object_terms($paper->ID, 'mh_technique', array('fields' => 'names'));
        if ($technique_filter) {
            $paper_tech_slugs = wp_get_object_terms($paper->ID, 'mh_technique', array('fields' => 'slugs'));
            if (!in_array($technique_filter, $paper_tech_slugs)) {
                continue;
            }
        }
        
        $protocols[] = array(
            'id' => null,
            'title' => $proto_name,
            'url' => $proto_url,
            'external_url' => $proto_url,
            'source' => $source,
            'paper_id' => $paper->ID,
            'paper_title' => $paper->post_title,
            'date' => null,
            'type' => 'paper_linked',
            'techniques' => is_array($paper_techniques) ? $paper_techniques : array(),
            'organisms' => array(),
            'microscopes' => array(),
            'authors' => array(),
            'year' => null,
            'abstract' => null,
        );
    }
}

// Sort: protocol papers first, then by source, then by title
usort($protocols, function($a, $b) {
    // Protocol papers first
    if ($a['type'] === 'protocol_paper' && $b['type'] !== 'protocol_paper') return -1;
    if ($a['type'] !== 'protocol_paper' && $b['type'] === 'protocol_paper') return 1;
    
    // Then by source
    $source_cmp = strcmp($a['source'], $b['source']);
    if ($source_cmp !== 0) return $source_cmp;
    
    return strcmp($a['title'], $b['title']);
});

// Get unique sources for filter dropdown
$sources = array_unique(array_column($protocols, 'source'));
sort($sources);

// Get techniques for filter dropdown
$all_techniques = get_terms(array(
    'taxonomy' => 'mh_technique',
    'hide_empty' => true,
    'orderby' => 'count',
    'order' => 'DESC',
    'number' => 30,
));

// Pagination
$per_page = 20;
$total = count($protocols);
$total_pages = ceil($total / $per_page);
$offset = ($paged - 1) * $per_page;
$protocols_page = array_slice($protocols, $offset, $per_page);

// Count by type for stats
$protocol_paper_count = count(array_filter($protocols, function($p) { return $p['type'] === 'protocol_paper'; }));
$linked_count = count(array_filter($protocols, function($p) { return $p['type'] === 'paper_linked'; }));
$uploaded_count = count(array_filter($protocols, function($p) { return $p['type'] === 'uploaded'; }));

// Helper function for source badge class
if (!function_exists('mh_protocol_source_class')) {
    function mh_protocol_source_class($source) {
        $source_lower = strtolower($source);
        if (strpos($source_lower, 'protocols.io') !== false) return 'protocols-io';
        if (strpos($source_lower, 'bio-protocol') !== false) return 'bio-protocol';
        if (strpos($source_lower, 'jove') !== false) return 'jove';
        if (strpos($source_lower, 'nature') !== false) return 'nature';
        if (strpos($source_lower, 'star') !== false) return 'star';
        if (strpos($source_lower, 'community') !== false) return 'community';
        return 'other';
    }
}
?>
<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>
    <div class="mh-page-container mh-protocols-page">
        <header class="mh-page-header">
            <h1>📋 Protocols</h1>
            <p class="mh-subtitle">Browse <?php echo number_format($total); ?> microscopy protocols</p>
        </header>

        <!-- Stats Summary -->
        <div class="mh-protocol-stats">
            <div class="mh-stat-badge">
                <span class="stat-number"><?php echo $protocol_paper_count; ?></span>
                <span class="stat-label">Protocol Papers</span>
            </div>
            <div class="mh-stat-badge">
                <span class="stat-number"><?php echo $linked_count; ?></span>
                <span class="stat-label">Linked Protocols</span>
            </div>
            <div class="mh-stat-badge">
                <span class="stat-number"><?php echo $uploaded_count; ?></span>
                <span class="stat-label">Community</span>
            </div>
        </div>

        <!-- Filters -->
        <div class="mh-protocols-filters">
            <form method="get" action="<?php echo esc_url($protocols_url); ?>" class="mh-filter-form">
                <input type="text" name="search" placeholder="Search protocols..." value="<?php echo esc_attr($search); ?>" class="mh-search-input">
                
                <select name="source" class="mh-filter-select">
                    <option value="">All Sources</option>
                    <?php foreach ($sources as $src) : ?>
                        <option value="<?php echo esc_attr($src); ?>" <?php selected($source_filter, $src); ?>><?php echo esc_html($src); ?></option>
                    <?php endforeach; ?>
                </select>
                
                <select name="technique" class="mh-filter-select">
                    <option value="">All Techniques</option>
                    <?php if (!is_wp_error($all_techniques)) : foreach ($all_techniques as $tech) : ?>
                        <option value="<?php echo esc_attr($tech->slug); ?>" <?php selected($technique_filter, $tech->slug); ?>>
                            <?php echo esc_html($tech->name); ?> (<?php echo $tech->count; ?>)
                        </option>
                    <?php endforeach; endif; ?>
                </select>
                
                <button type="submit" class="mh-submit-btn">Search</button>
                
                <?php if ($search || $source_filter || $technique_filter) : ?>
                    <a href="<?php echo esc_url($protocols_url); ?>" class="mh-clear-link">✕ Clear</a>
                <?php endif; ?>
            </form>
        </div>

        <?php if (empty($protocols_page)) : ?>
            <div class="mh-no-results">
                <span class="icon">📋</span>
                <h3>No protocols found</h3>
                <p>Try adjusting your search or filter criteria.</p>
            </div>
        <?php else : ?>
            <!-- Protocols List -->
            <div class="mh-protocols-list">
                <?php foreach ($protocols_page as $proto) : ?>
                    <article class="mh-protocol-card <?php echo esc_attr($proto['type']); ?>">
                        <div class="mh-protocol-header">
                            <span class="mh-protocol-source <?php echo esc_attr(mh_protocol_source_class($proto['source'])); ?>">
                                <?php echo esc_html($proto['source']); ?>
                            </span>
                            
                            <?php if ($proto['type'] === 'protocol_paper') : ?>
                                <span class="mh-protocol-type-badge paper">📄 Full Paper</span>
                            <?php elseif ($proto['type'] === 'paper_linked') : ?>
                                <span class="mh-protocol-type-badge linked">🔗 Linked</span>
                            <?php else : ?>
                                <span class="mh-protocol-type-badge community">👥 Community</span>
                            <?php endif; ?>
                        </div>
                        
                        <h3 class="mh-protocol-title">
                            <a href="<?php echo esc_url($proto['url']); ?>" <?php echo $proto['type'] !== 'protocol_paper' ? 'target="_blank" rel="noopener"' : ''; ?>>
                                <?php echo esc_html($proto['title']); ?>
                            </a>
                        </h3>
                        
                        <?php if (!empty($proto['authors'])) : ?>
                            <div class="mh-protocol-authors">
                                <?php echo esc_html(implode(', ', $proto['authors'])); ?>
                                <?php if ($proto['year']) : ?>
                                    <span class="mh-protocol-year">(<?php echo esc_html($proto['year']); ?>)</span>
                                <?php endif; ?>
                            </div>
                        <?php endif; ?>
                        
                        <?php if (!empty($proto['abstract'])) : ?>
                            <p class="mh-protocol-abstract"><?php echo esc_html($proto['abstract']); ?></p>
                        <?php endif; ?>
                        
                        <!-- Tags -->
                        <?php if (!empty($proto['techniques']) || !empty($proto['organisms']) || !empty($proto['microscopes'])) : ?>
                            <div class="mh-protocol-tags">
                                <?php foreach (array_slice($proto['techniques'], 0, 3) as $tech) : ?>
                                    <span class="mh-tag technique"><?php echo esc_html($tech); ?></span>
                                <?php endforeach; ?>
                                <?php foreach (array_slice($proto['organisms'], 0, 2) as $org) : ?>
                                    <span class="mh-tag organism"><?php echo esc_html($org); ?></span>
                                <?php endforeach; ?>
                                <?php foreach (array_slice($proto['microscopes'], 0, 2) as $mic) : ?>
                                    <span class="mh-tag microscope"><?php echo esc_html($mic); ?></span>
                                <?php endforeach; ?>
                            </div>
                        <?php endif; ?>
                        
                        <!-- Footer with links -->
                        <div class="mh-protocol-footer">
                            <?php if ($proto['paper_title']) : ?>
                                <a href="<?php echo get_permalink($proto['paper_id']); ?>" class="mh-paper-link">
                                    📄 From: <?php echo esc_html(wp_trim_words($proto['paper_title'], 8)); ?>
                                </a>
                            <?php endif; ?>
                            
                            <?php if ($proto['external_url'] && $proto['type'] === 'protocol_paper') : ?>
                                <a href="<?php echo esc_url($proto['external_url']); ?>" target="_blank" rel="noopener" class="mh-external-link">
                                    View at Publisher ↗
                                </a>
                            <?php endif; ?>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>

            <!-- Pagination -->
            <?php if ($total_pages > 1) : ?>
                <div class="mh-pagination">
                    <?php
                    $base_url = $protocols_url;
                    if ($search) $base_url = add_query_arg('search', $search, $base_url);
                    if ($source_filter) $base_url = add_query_arg('source', $source_filter, $base_url);
                    if ($technique_filter) $base_url = add_query_arg('technique', $technique_filter, $base_url);
                    
                    echo paginate_links(array(
                        'base' => add_query_arg('paged', '%#%', $base_url),
                        'format' => '',
                        'current' => $paged,
                        'total' => $total_pages,
                        'prev_text' => '← Previous',
                        'next_text' => 'Next →',
                    ));
                    ?>
                </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
</div>

<style>
/* Protocol Stats */
.mh-protocol-stats {
    display: flex;
    gap: 20px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}
.mh-stat-badge {
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 8px;
    padding: 16px 24px;
    text-align: center;
}
.mh-stat-badge .stat-number {
    display: block;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--primary, #58a6ff);
}
.mh-stat-badge .stat-label {
    font-size: 0.85rem;
    color: var(--text-muted, #8b949e);
}

/* Filters */
.mh-protocols-filters {
    margin-bottom: 24px;
}
.mh-filter-form {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
}
.mh-search-input, .mh-filter-select {
    padding: 10px 14px;
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 6px;
    color: var(--text, #c9d1d9);
    font-size: 0.9rem;
}
.mh-search-input {
    min-width: 200px;
    flex: 1;
}
.mh-filter-select {
    min-width: 150px;
}
.mh-submit-btn {
    padding: 10px 20px;
    background: var(--primary, #58a6ff);
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
}
.mh-submit-btn:hover {
    background: var(--primary-hover, #79b8ff);
}
.mh-clear-link {
    color: var(--text-muted, #8b949e);
    text-decoration: none;
    padding: 10px;
}
.mh-clear-link:hover {
    color: var(--text, #c9d1d9);
}

/* Protocol Cards */
.mh-protocols-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.mh-protocol-card {
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 8px;
    padding: 20px;
    transition: border-color 0.2s;
}
.mh-protocol-card:hover {
    border-color: var(--primary, #58a6ff);
}
.mh-protocol-card.protocol_paper {
    border-left: 3px solid var(--primary, #58a6ff);
}

.mh-protocol-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.mh-protocol-source {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}
.mh-protocol-source.jove { background: #1e3a5f; color: #58a6ff; }
.mh-protocol-source.nature { background: #2d1f3d; color: #a371f7; }
.mh-protocol-source.star { background: #3d2f1f; color: #f0883e; }
.mh-protocol-source.protocols-io { background: #1f3d2d; color: #56d364; }
.mh-protocol-source.bio-protocol { background: #3d1f2d; color: #f778ba; }
.mh-protocol-source.community { background: #2d3d1f; color: #a5d6a7; }
.mh-protocol-source.other { background: #2d2d2d; color: #8b949e; }

.mh-protocol-type-badge {
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
    background: var(--bg-hover, #21262d);
    color: var(--text-muted, #8b949e);
}
.mh-protocol-type-badge.paper { color: var(--primary, #58a6ff); }
.mh-protocol-type-badge.linked { color: #f0883e; }
.mh-protocol-type-badge.community { color: #56d364; }

.mh-protocol-title {
    font-size: 1.1rem;
    margin: 0 0 8px 0;
    line-height: 1.4;
}
.mh-protocol-title a {
    color: var(--text, #c9d1d9);
    text-decoration: none;
}
.mh-protocol-title a:hover {
    color: var(--primary, #58a6ff);
}

.mh-protocol-authors {
    font-size: 0.85rem;
    color: var(--text-muted, #8b949e);
    margin-bottom: 8px;
}
.mh-protocol-year {
    color: var(--text-light, #6e7681);
}

.mh-protocol-abstract {
    font-size: 0.9rem;
    color: var(--text-light, #8b949e);
    line-height: 1.5;
    margin: 10px 0;
}

.mh-protocol-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 12px 0;
}
.mh-tag {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    background: var(--bg-hover, #21262d);
    color: var(--text-muted, #8b949e);
}
.mh-tag.technique { background: #1e3a5f; color: #58a6ff; }
.mh-tag.organism { background: #1f3d2d; color: #56d364; }
.mh-tag.microscope { background: #3d2f1f; color: #f0883e; }

.mh-protocol-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--border, #30363d);
    flex-wrap: wrap;
    gap: 10px;
}
.mh-paper-link {
    font-size: 0.85rem;
    color: var(--text-muted, #8b949e);
    text-decoration: none;
}
.mh-paper-link:hover {
    color: var(--primary, #58a6ff);
}
.mh-external-link {
    font-size: 0.85rem;
    color: var(--primary, #58a6ff);
    text-decoration: none;
}
.mh-external-link:hover {
    text-decoration: underline;
}

/* No Results */
.mh-no-results {
    text-align: center;
    padding: 60px 20px;
    background: var(--bg-card, #161b22);
    border-radius: 8px;
}
.mh-no-results .icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 16px;
}
.mh-no-results h3 {
    margin: 0 0 8px 0;
    color: var(--text, #c9d1d9);
}
.mh-no-results p {
    color: var(--text-muted, #8b949e);
    margin: 0;
}

/* Pagination */
.mh-pagination {
    margin-top: 30px;
    text-align: center;
}
.mh-pagination .page-numbers {
    display: inline-block;
    padding: 8px 14px;
    margin: 0 4px;
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 6px;
    color: var(--text, #c9d1d9);
    text-decoration: none;
}
.mh-pagination .page-numbers.current,
.mh-pagination .page-numbers:hover {
    background: var(--primary, #58a6ff);
    border-color: var(--primary, #58a6ff);
    color: #fff;
}

/* Responsive */
@media (max-width: 768px) {
    .mh-filter-form {
        flex-direction: column;
    }
    .mh-search-input, .mh-filter-select, .mh-submit-btn {
        width: 100%;
    }
    .mh-protocol-stats {
        flex-direction: column;
    }
    .mh-stat-badge {
        flex: 1;
    }
}
</style>
