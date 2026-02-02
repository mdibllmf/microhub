<?php
/**
 * Protocols Page Template for MicroHub v4.2
 * Matches the papers home page layout exactly
 */

// Get filter parameters
$search = isset($_GET['search']) ? sanitize_text_field($_GET['search']) : '';
$source_filter = isset($_GET['source']) ? sanitize_text_field($_GET['source']) : '';
$technique_filter = isset($_GET['technique']) ? sanitize_text_field($_GET['technique']) : '';
$paged = max(1, get_query_var('paged'));

// Get protocols URL
$protocols_url = function_exists('mh_get_page_url') ? mh_get_page_url('protocols') : home_url('/protocols/');

global $wpdb;

$protocols = array();

// =============================================================================
// 1. PROTOCOL JOURNAL PAPERS (JoVE, Nature Protocols, STAR Protocols, etc.)
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

    if ($source_filter && stripos($source, $source_filter) === false) {
        continue;
    }

    $techniques = wp_get_object_terms($post->ID, 'mh_technique', array('fields' => 'names'));
    $organisms = wp_get_object_terms($post->ID, 'mh_organism', array('fields' => 'names'));
    $microscopes = wp_get_object_terms($post->ID, 'mh_microscope', array('fields' => 'names'));

    $doi = get_post_meta($post->ID, '_mh_doi', true);
    $doi_url = get_post_meta($post->ID, '_mh_doi_url', true);
    if (!$doi_url && $doi) $doi_url = 'https://doi.org/' . $doi;

    $authors = get_post_meta($post->ID, '_mh_authors', true);
    $year = get_post_meta($post->ID, '_mh_publication_year', true);
    if (!$year) $year = get_post_meta($post->ID, '_mh_year', true);
    $citations = get_post_meta($post->ID, '_mh_citation_count', true);
    $abstract = get_post_meta($post->ID, '_mh_abstract', true);
    $github_url = get_post_meta($post->ID, '_mh_github_url', true);
    $facility = get_post_meta($post->ID, '_mh_facility', true);
    $repos = json_decode(get_post_meta($post->ID, '_mh_repositories', true), true) ?: array();
    $protocol_list = json_decode(get_post_meta($post->ID, '_mh_protocols', true), true) ?: array();

    $protocols[] = array(
        'id' => $post->ID,
        'title' => $post->post_title,
        'url' => get_permalink($post->ID),
        'external_url' => $doi_url ?: '',
        'source' => $source,
        'paper_id' => $post->ID,
        'paper_title' => null,
        'date' => $post->post_date,
        'type' => 'protocol_paper',
        'techniques' => is_array($techniques) ? $techniques : array(),
        'organisms' => is_array($organisms) ? $organisms : array(),
        'microscopes' => is_array($microscopes) ? $microscopes : array(),
        'authors' => $authors,
        'year' => $year,
        'citations' => $citations,
        'abstract' => $abstract ?: wp_trim_words($post->post_content, 30, '...'),
        'github_url' => $github_url,
        'facility' => $facility,
        'repos' => $repos,
        'protocols' => $protocol_list,
    );
}

// =============================================================================
// 2. USER-UPLOADED & IMPORTED PROTOCOLS (mh_protocol post type)
// =============================================================================
$uploaded_args = array(
    'post_type' => 'mh_protocol',
    'posts_per_page' => -1,
    'post_status' => 'publish',
);

if ($search) {
    $uploaded_args['s'] = $search;
}

if ($technique_filter) {
    $uploaded_args['tax_query'] = array(
        array(
            'taxonomy' => 'mh_technique',
            'field' => 'slug',
            'terms' => $technique_filter,
        )
    );
}

$uploaded_protocols = get_posts($uploaded_args);

foreach ($uploaded_protocols as $post) {
    $source = get_post_meta($post->ID, '_mh_protocol_type', true);
    if (empty($source)) {
        $source = get_post_meta($post->ID, '_mh_protocol_source', true);
    }
    if (empty($source)) {
        $protocol_type_terms = wp_get_object_terms($post->ID, 'mh_protocol_type', array('fields' => 'names'));
        if (!is_wp_error($protocol_type_terms) && !empty($protocol_type_terms)) {
            $source = $protocol_type_terms[0];
        }
    }
    if (empty($source)) {
        $source = 'Community';
    }

    if ($source_filter && stripos($source, $source_filter) === false) {
        continue;
    }

    $doi = get_post_meta($post->ID, '_mh_doi', true);
    $doi_url = get_post_meta($post->ID, '_mh_doi_url', true);
    $proto_url = '';
    $external_url = '';

    if (!empty($doi)) {
        $external_url = $doi_url ?: 'https://doi.org/' . $doi;
        $proto_url = get_permalink($post->ID);
    } else {
        $proto_url = get_post_meta($post->ID, '_mh_protocol_url', true);
        if (empty($proto_url)) {
            $proto_url = get_permalink($post->ID);
        }
        $external_url = $proto_url;
    }

    $techniques = wp_get_object_terms($post->ID, 'mh_technique', array('fields' => 'names'));
    $organisms = wp_get_object_terms($post->ID, 'mh_organism', array('fields' => 'names'));
    $microscopes = wp_get_object_terms($post->ID, 'mh_microscope', array('fields' => 'names'));

    $authors = get_post_meta($post->ID, '_mh_authors', true);
    $year = get_post_meta($post->ID, '_mh_publication_year', true);
    if (!$year) $year = get_post_meta($post->ID, '_mh_year', true);
    $citations = get_post_meta($post->ID, '_mh_citation_count', true);
    $github_url = get_post_meta($post->ID, '_mh_github_url', true);
    $facility = get_post_meta($post->ID, '_mh_facility', true);
    $repos = json_decode(get_post_meta($post->ID, '_mh_repositories', true), true) ?: array();
    $protocol_list = json_decode(get_post_meta($post->ID, '_mh_protocols', true), true) ?: array();

    $abstract = get_post_meta($post->ID, '_mh_abstract', true);
    if (empty($abstract)) {
        $abstract = $post->post_content;
    }

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
        'external_url' => $external_url,
        'source' => $source,
        'paper_id' => $linked_paper_id,
        'paper_title' => $linked_paper_title,
        'date' => $post->post_date,
        'type' => 'uploaded',
        'techniques' => is_array($techniques) ? $techniques : array(),
        'organisms' => is_array($organisms) ? $organisms : array(),
        'microscopes' => is_array($microscopes) ? $microscopes : array(),
        'authors' => $authors,
        'year' => $year,
        'citations' => $citations,
        'abstract' => wp_trim_words($abstract, 30, '...'),
        'github_url' => $github_url,
        'facility' => $facility,
        'repos' => $repos,
        'protocols' => $protocol_list,
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

        if ($source_filter && stripos($source, $source_filter) === false) {
            continue;
        }

        if ($search) {
            $search_lower = strtolower($search);
            if (strpos(strtolower($proto_name), $search_lower) === false &&
                strpos(strtolower($paper->post_title), $search_lower) === false) {
                continue;
            }
        }

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
            'authors' => null,
            'year' => null,
            'citations' => null,
            'abstract' => null,
            'github_url' => null,
            'facility' => null,
            'repos' => array(),
            'protocols' => array(),
        );
    }
}

// Sort: protocol papers first (by citations), then uploaded, then linked
usort($protocols, function($a, $b) {
    // Protocol papers first
    if ($a['type'] === 'protocol_paper' && $b['type'] !== 'protocol_paper') return -1;
    if ($a['type'] !== 'protocol_paper' && $b['type'] === 'protocol_paper') return 1;

    // Then by citations
    $a_cit = intval($a['citations'] ?? 0);
    $b_cit = intval($b['citations'] ?? 0);
    if ($a_cit !== $b_cit) return $b_cit - $a_cit;

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
$github_count = count(array_filter($protocols, function($p) { return !empty($p['github_url']); }));
$facility_count = count(array_filter($protocols, function($p) { return !empty($p['facility']); }));

// Get recent protocols for sidebar
$recent_protocols = array_slice($protocols, 0, 5);

// Get GitHub repos from protocols
$github_repos = array();
foreach ($protocols as $proto) {
    if (!empty($proto['github_url'])) {
        $github_repos[] = array(
            'url' => $proto['github_url'],
            'title' => $proto['title'],
            'id' => $proto['id'],
        );
    }
}
$github_repos = array_slice($github_repos, 0, 5);

// Get data repositories
$data_repos = array();
foreach ($protocols as $proto) {
    if (!empty($proto['repos'])) {
        foreach ($proto['repos'] as $repo) {
            $data_repos[] = array(
                'url' => $repo['url'] ?? '',
                'name' => $repo['name'] ?? $repo['type'] ?? 'Data',
                'paper_title' => $proto['title'],
            );
        }
    }
}
$data_repos = array_slice($data_repos, 0, 5);

// Get facilities
$facilities = array();
foreach ($protocols as $proto) {
    if (!empty($proto['facility'])) {
        if (!isset($facilities[$proto['facility']])) {
            $facilities[$proto['facility']] = 0;
        }
        $facilities[$proto['facility']]++;
    }
}
arsort($facilities);
$facilities = array_slice($facilities, 0, 5, true);
?>
<div class="microhub-wrapper">
    <?php if (function_exists('mh_render_nav')) echo mh_render_nav(); ?>

    <!-- HEADER: Hero + Search (matching papers page) -->
    <header class="mh-site-header">
        <!-- Hero Section -->
        <section class="mh-hero">
            <div class="mh-hero-inner">
                <div class="mh-hero-content">
                    <div class="mh-hero-text">
                        <h1>Microscopy Protocols</h1>
                        <p>Browse and search microscopy protocols from journals, community uploads, and linked resources</p>

                        <div class="mh-hero-stats">
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($total); ?></span>
                                <span class="mh-hero-stat-label">Protocols</span>
                            </div>
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($protocol_paper_count); ?></span>
                                <span class="mh-hero-stat-label">Papers</span>
                            </div>
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($uploaded_count); ?></span>
                                <span class="mh-hero-stat-label">Community</span>
                            </div>
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($linked_count); ?></span>
                                <span class="mh-hero-stat-label">Linked</span>
                            </div>
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($github_count); ?></span>
                                <span class="mh-hero-stat-label">GitHub</span>
                            </div>
                        </div>
                    </div>

                    <!-- Featured Protocols -->
                    <div class="mh-featured-papers">
                        <?php
                        $featured = array_slice(array_filter($protocols, function($p) {
                            return $p['type'] === 'protocol_paper' && intval($p['citations'] ?? 0) >= 50;
                        }), 0, 2);
                        foreach ($featured as $proto) :
                        ?>
                        <div class="mh-featured-paper">
                            <span class="mh-featured-badge">Featured Protocol</span>
                            <h3 class="mh-featured-title">
                                <a href="<?php echo esc_url($proto['url']); ?>"><?php echo esc_html(wp_trim_words($proto['title'], 12)); ?></a>
                            </h3>
                            <div class="mh-featured-meta">
                                <?php if ($proto['authors']) echo esc_html(wp_trim_words($proto['authors'], 6)); ?>
                                <?php if ($proto['year']) echo ' &bull; ' . esc_html($proto['year']); ?>
                            </div>
                            <div class="mh-featured-stats">
                                <?php if ($proto['citations']) : ?>
                                    <span><?php echo number_format($proto['citations']); ?> citations</span>
                                <?php endif; ?>
                                <?php if (!empty($proto['techniques'])) : ?>
                                    <span><?php echo esc_html($proto['techniques'][0]); ?></span>
                                <?php endif; ?>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>
            </div>
        </section>

        <!-- Search Section -->
        <section class="mh-search-section mh-no-box">
            <div class="mh-search-header">
                <h2>Find Protocols</h2>
                <p>Search by title, technique, source, or browse by category</p>
            </div>

            <!-- Main Search -->
            <form method="get" action="<?php echo esc_url($protocols_url); ?>" class="mh-search-main">
                <div class="mh-search-input-wrap">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.35-4.35"/>
                    </svg>
                    <input type="text"
                           name="search"
                           class="mh-search-input"
                           placeholder="Search protocols by title, technique..."
                           value="<?php echo esc_attr($search); ?>" />
                </div>
                <button type="submit" class="mh-search-btn">Search Protocols</button>
            </form>

            <!-- Filter Grid -->
            <form method="get" action="<?php echo esc_url($protocols_url); ?>" class="mh-filter-grid">
                <?php if ($search) : ?>
                    <input type="hidden" name="search" value="<?php echo esc_attr($search); ?>">
                <?php endif; ?>

                <div class="mh-filter-item">
                    <label>Source</label>
                    <select name="source" onchange="this.form.submit()">
                        <option value="">All Sources</option>
                        <?php foreach ($sources as $src) : ?>
                            <option value="<?php echo esc_attr($src); ?>" <?php selected($source_filter, $src); ?>><?php echo esc_html($src); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="mh-filter-item">
                    <label>Technique</label>
                    <select name="technique" onchange="this.form.submit()">
                        <option value="">All Techniques</option>
                        <?php if (!is_wp_error($all_techniques)) : foreach ($all_techniques as $tech) : ?>
                            <option value="<?php echo esc_attr($tech->slug); ?>" <?php selected($technique_filter, $tech->slug); ?>>
                                <?php echo esc_html($tech->name); ?> (<?php echo $tech->count; ?>)
                            </option>
                        <?php endforeach; endif; ?>
                    </select>
                </div>
                <div class="mh-filter-item">
                    <label>&nbsp;</label>
                    <?php if ($search || $source_filter || $technique_filter) : ?>
                        <a href="<?php echo esc_url($protocols_url); ?>" class="mh-clear-link" style="display:block; padding:6px 12px; background:#21262d; border-radius:5px; text-align:center; color:#8b949e;">Clear Filters</a>
                    <?php endif; ?>
                </div>
            </form>

            <!-- Quick Filters -->
            <div class="mh-quick-filters">
                <span class="mh-quick-label">Quick filters:</span>
                <a href="<?php echo add_query_arg('source', 'JoVE', $protocols_url); ?>" class="mh-quick-btn <?php echo $source_filter === 'JoVE' ? 'active' : ''; ?>">JoVE</a>
                <a href="<?php echo add_query_arg('source', 'Nature Protocols', $protocols_url); ?>" class="mh-quick-btn <?php echo $source_filter === 'Nature Protocols' ? 'active' : ''; ?>">Nature Protocols</a>
                <a href="<?php echo add_query_arg('source', 'STAR Protocols', $protocols_url); ?>" class="mh-quick-btn <?php echo $source_filter === 'STAR Protocols' ? 'active' : ''; ?>">STAR Protocols</a>
                <a href="<?php echo add_query_arg('source', 'protocols.io', $protocols_url); ?>" class="mh-quick-btn <?php echo $source_filter === 'protocols.io' ? 'active' : ''; ?>">protocols.io</a>
                <a href="<?php echo add_query_arg('source', 'Community', $protocols_url); ?>" class="mh-quick-btn <?php echo $source_filter === 'Community' ? 'active' : ''; ?>">Community</a>
                <?php if ($search || $source_filter || $technique_filter) : ?>
                    <a href="<?php echo esc_url($protocols_url); ?>" class="mh-clear-all">Clear all filters</a>
                <?php endif; ?>
            </div>
        </section>
    </header>

    <!-- MAIN BODY: Protocols + Sidebar (matching papers page) -->
    <main class="mh-site-body">
        <section class="mh-results-section">
            <div class="mh-results-main">
                <div class="mh-results-header">
                    <div class="mh-results-count">
                        Showing <strong><?php echo count($protocols_page); ?></strong> of <strong><?php echo number_format($total); ?></strong> protocols
                    </div>
                    <div class="mh-results-sort">
                        <label>Sort by:</label>
                        <select id="mh-sort">
                            <option value="citations-desc">Citations (High to Low)</option>
                            <option value="year-desc">Year (Newest)</option>
                            <option value="title-asc">Title (A-Z)</option>
                        </select>
                    </div>
                </div>

                <?php if (empty($protocols_page)) : ?>
                    <div class="mh-no-results">
                        <h3>No protocols found</h3>
                        <p>Try adjusting your search or filter criteria.</p>
                    </div>
                <?php else : ?>
                    <!-- Protocols Grid (matching paper cards) -->
                    <div class="mh-papers-grid">
                        <?php foreach ($protocols_page as $proto) :
                            $citations = intval($proto['citations'] ?? 0);
                            $badge_class = 'standard';
                            $badge_text = $citations ? number_format($citations) . ' citations' : $proto['source'];
                            if ($citations >= 100) {
                                $badge_class = 'foundational';
                                $badge_text = 'Foundational';
                            } elseif ($citations >= 50) {
                                $badge_class = 'high-impact';
                                $badge_text = 'High Impact';
                            }
                        ?>
                            <article class="mh-paper-card">
                                <div class="mh-card-top">
                                    <span class="mh-card-badge <?php echo $badge_class; ?>"><?php echo esc_html($badge_text); ?></span>
                                    <?php if ($citations) : ?>
                                        <span class="mh-card-citations"><strong><?php echo number_format($citations); ?></strong> citations</span>
                                    <?php else : ?>
                                        <span class="mh-card-citations"><?php echo esc_html($proto['source']); ?></span>
                                    <?php endif; ?>
                                </div>

                                <h3 class="mh-card-title">
                                    <a href="<?php echo esc_url($proto['url']); ?>"><?php echo esc_html($proto['title']); ?></a>
                                </h3>

                                <div class="mh-card-meta">
                                    <?php if ($proto['authors']) : ?>
                                        <div class="mh-card-authors"><?php echo esc_html(wp_trim_words($proto['authors'], 8)); ?></div>
                                    <?php endif; ?>
                                    <div class="mh-card-publication">
                                        <?php if ($proto['source']) : ?><span><?php echo esc_html($proto['source']); ?></span><?php endif; ?>
                                        <?php if ($proto['year']) : ?><span><?php echo esc_html($proto['year']); ?></span><?php endif; ?>
                                    </div>
                                </div>

                                <?php if ($proto['abstract']) : ?>
                                    <p class="mh-card-abstract"><?php echo esc_html(wp_trim_words($proto['abstract'], 25)); ?></p>
                                <?php endif; ?>

                                <div class="mh-card-tags">
                                    <?php foreach (array_slice($proto['techniques'], 0, 2) as $tech) : ?>
                                        <span class="mh-card-tag technique"><?php echo esc_html($tech); ?></span>
                                    <?php endforeach; ?>
                                    <?php foreach (array_slice($proto['microscopes'], 0, 1) as $mic) : ?>
                                        <span class="mh-card-tag microscope"><?php echo esc_html($mic); ?></span>
                                    <?php endforeach; ?>
                                    <?php foreach (array_slice($proto['organisms'], 0, 1) as $org) : ?>
                                        <span class="mh-card-tag organism"><?php echo esc_html($org); ?></span>
                                    <?php endforeach; ?>
                                </div>

                                <div class="mh-card-enrichment">
                                    <?php if (!empty($proto['protocols'])) : ?>
                                        <span class="mh-enrichment-item protocols"><?php echo count($proto['protocols']); ?> Protocol<?php echo count($proto['protocols']) > 1 ? 's' : ''; ?></span>
                                    <?php endif; ?>
                                    <?php if ($proto['github_url']) : ?>
                                        <span class="mh-enrichment-item github">GitHub</span>
                                    <?php endif; ?>
                                    <?php if (!empty($proto['repos'])) : ?>
                                        <span class="mh-enrichment-item repositories">Data</span>
                                    <?php endif; ?>
                                    <?php if ($proto['facility']) : ?>
                                        <span class="mh-enrichment-item facility">Facility</span>
                                    <?php endif; ?>
                                    <?php if ($proto['paper_title']) : ?>
                                        <span class="mh-enrichment-item protocols">Linked Paper</span>
                                    <?php endif; ?>
                                </div>

                                <div class="mh-card-footer">
                                    <div class="mh-card-links">
                                        <?php if ($proto['external_url'] && $proto['external_url'] !== $proto['url']) : ?>
                                            <a href="<?php echo esc_url($proto['external_url']); ?>" class="mh-card-link doi" target="_blank">Source</a>
                                        <?php endif; ?>
                                        <?php if ($proto['github_url']) : ?>
                                            <a href="<?php echo esc_url($proto['github_url']); ?>" class="mh-card-link github" target="_blank">GitHub</a>
                                        <?php endif; ?>
                                        <?php if ($proto['paper_id'] && $proto['paper_title']) : ?>
                                            <a href="<?php echo get_permalink($proto['paper_id']); ?>" class="mh-card-link pubmed">View Paper</a>
                                        <?php endif; ?>
                                    </div>
                                    <div class="mh-card-actions">
                                        <span class="mh-card-action"><?php echo esc_html($proto['type'] === 'protocol_paper' ? 'Full Paper' : ($proto['type'] === 'uploaded' ? 'Community' : 'Linked')); ?></span>
                                    </div>
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
                                'prev_text' => '&larr; Previous',
                                'next_text' => 'Next &rarr;',
                            ));
                            ?>
                        </div>
                    <?php endif; ?>
                <?php endif; ?>
            </div>

            <!-- Sidebar (matching papers page) -->
            <aside class="mh-sidebar">
                <!-- GitHub Repositories Widget -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">💻</span> Code Repositories</h3>
                    <ul class="mh-github-list">
                        <?php if (!empty($github_repos)) : ?>
                            <?php foreach ($github_repos as $repo) : ?>
                                <li class="mh-repo-item">
                                    <a href="<?php echo esc_url($repo['url']); ?>" class="repo-link" target="_blank">
                                        <svg class="github-icon" viewBox="0 0 16 16" fill="currentColor">
                                            <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                                        </svg>
                                        <?php echo esc_html(wp_trim_words($repo['title'], 6)); ?>
                                    </a>
                                </li>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <li class="mh-empty-item">No GitHub repositories found</li>
                        <?php endif; ?>
                    </ul>
                </div>

                <!-- Data Repositories Widget -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">💾</span> Data Repositories</h3>
                    <ul class="mh-data-repos-list">
                        <?php if (!empty($data_repos)) : ?>
                            <?php foreach ($data_repos as $repo) : ?>
                                <li class="mh-data-repo-item">
                                    <a href="<?php echo esc_url($repo['url']); ?>" class="repo-link" target="_blank">
                                        <?php echo esc_html($repo['name']); ?>
                                    </a>
                                    <span class="paper-ref"><?php echo esc_html(wp_trim_words($repo['paper_title'], 5)); ?></span>
                                </li>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <li class="mh-empty-item">No data repositories found</li>
                        <?php endif; ?>
                    </ul>
                </div>

                <!-- Recent Protocols Widget -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">📋</span> Recent Protocols</h3>
                    <ul class="mh-protocol-list">
                        <?php foreach ($recent_protocols as $proto) : ?>
                            <li class="mh-protocol-item">
                                <a href="<?php echo esc_url($proto['url']); ?>" class="protocol-link">
                                    <span class="protocol-icon"></span>
                                    <?php echo esc_html(wp_trim_words($proto['title'], 6)); ?>
                                </a>
                                <span class="source"><?php echo esc_html($proto['source']); ?></span>
                            </li>
                        <?php endforeach; ?>
                    </ul>
                    <a href="<?php echo function_exists('mh_get_page_url') ? esc_url(mh_get_page_url('upload-protocol')) : '#'; ?>" class="mh-view-all" style="display: block; text-align: center; padding: 10px; color: #f78166; font-size: 0.85rem;">+ Upload Protocol</a>
                </div>

                <!-- Imaging Facilities Widget -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">🏛️</span> Imaging Facilities</h3>
                    <ul class="mh-facility-list">
                        <?php if (!empty($facilities)) : ?>
                            <?php foreach ($facilities as $name => $count) : ?>
                                <li class="mh-facility-item">
                                    <span class="facility-link"><?php echo esc_html($name); ?></span>
                                    <span class="count">(<?php echo $count; ?>)</span>
                                </li>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <li class="mh-empty-item">No facilities found</li>
                        <?php endif; ?>
                    </ul>
                </div>

                <!-- Quick Stats -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">📊</span> Protocol Stats</h3>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Total Protocols</span>
                        <span class="mh-stat-value"><?php echo number_format($total); ?></span>
                    </div>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Protocol Papers</span>
                        <span class="mh-stat-value"><?php echo number_format($protocol_paper_count); ?></span>
                    </div>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Community</span>
                        <span class="mh-stat-value"><?php echo number_format($uploaded_count); ?></span>
                    </div>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">With Code</span>
                        <span class="mh-stat-value"><?php echo number_format($github_count); ?></span>
                    </div>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">With Facilities</span>
                        <span class="mh-stat-value"><?php echo number_format($facility_count); ?></span>
                    </div>
                </div>

                <!-- Community Links -->
                <div class="mh-sidebar-widget">
                    <h3><span class="icon">💬</span> Community</h3>
                    <a href="<?php echo function_exists('mh_get_page_url') ? esc_url(mh_get_page_url('discussions')) : '#'; ?>" class="mh-community-link">
                        <span class="link-icon">🗣️</span>
                        <span>Discussion Forum</span>
                    </a>
                    <a href="<?php echo function_exists('mh_get_page_url') ? esc_url(mh_get_page_url('upload-protocol')) : '#'; ?>" class="mh-community-link">
                        <span class="link-icon">📤</span>
                        <span>Upload Protocol</span>
                    </a>
                    <a href="<?php echo function_exists('mh_get_page_url') ? esc_url(mh_get_page_url('upload-paper')) : '#'; ?>" class="mh-community-link">
                        <span class="link-icon">📄</span>
                        <span>Submit Paper</span>
                    </a>
                </div>
            </aside>
        </section>
    </main>
</div>
