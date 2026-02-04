<?php
/**
 * MicroHub Theme Functions
 */

// Theme Setup
function mh_theme_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', array('search-form', 'comment-form', 'comment-list'));
    
    register_nav_menus(array(
        'primary' => 'Primary Menu',
        'footer' => 'Footer Menu'
    ));
}
add_action('after_setup_theme', 'mh_theme_setup');

// Enqueue Scripts and Styles
function mh_enqueue_assets() {
    wp_enqueue_style('google-fonts', 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap', array(), null);
    wp_enqueue_style('mh-style', get_stylesheet_uri(), array(), '4.3.0');
    
    wp_enqueue_script('mh-main', get_template_directory_uri() . '/assets/js/main.js', array(), '4.3.0', true);
    wp_localize_script('mh-main', 'microhubAjax', array(
        'ajaxurl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('microhub_nonce'),
        'restUrl' => rest_url('microhub-theme/v1'),  // Theme's own API
        'aiChatUrl' => rest_url('microhub/v1/ai-chat')  // Plugin's AI chat endpoint
    ));
}
add_action('wp_enqueue_scripts', 'mh_enqueue_assets');

// Register Sidebars
function mh_register_sidebars() {
    register_sidebar(array(
        'name' => 'Paper Sidebar',
        'id' => 'sidebar-paper',
        'before_widget' => '<div class="mh-sidebar-widget">',
        'after_widget' => '</div>',
        'before_title' => '<h3>',
        'after_title' => '</h3>'
    ));
    
    for ($i = 1; $i <= 4; $i++) {
        register_sidebar(array(
            'name' => "Footer Column $i",
            'id' => "footer-$i",
            'before_widget' => '<div class="mh-footer-widget">',
            'after_widget' => '</div>',
            'before_title' => '<h4>',
            'after_title' => '</h4>'
        ));
    }
}
add_action('widgets_init', 'mh_register_sidebars');

// ============================================
// THEME REST API FOR PAPER SEARCH
// ============================================

/**
 * Register custom REST API endpoints
 */
function mh_theme_register_rest_routes() {
    // Protocols endpoint
    register_rest_route('microhub-theme/v1', '/protocols', array(
        'methods' => 'GET',
        'callback' => 'mh_theme_search_protocols',
        'permission_callback' => '__return_true',
        'args' => array(
            'search' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'technique' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'microscope' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'organism' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'software' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'fluorophore' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'sample_prep' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'cell_line' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'brand' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'source' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'year_min' => array('type' => 'integer', 'sanitize_callback' => 'absint'),
            'year_max' => array('type' => 'integer', 'sanitize_callback' => 'absint'),
            'citations_min' => array('type' => 'integer', 'sanitize_callback' => 'absint'),
            'has_github' => array('type' => 'boolean'),
            'has_figures' => array('type' => 'boolean'),
            'orderby' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'order' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'page' => array('type' => 'integer', 'default' => 1, 'sanitize_callback' => 'absint'),
            'per_page' => array('type' => 'integer', 'default' => 24, 'sanitize_callback' => 'absint'),
        )
    ));
    
    // Papers endpoint
    register_rest_route('microhub-theme/v1', '/papers', array(
        'methods' => 'GET',
        'callback' => 'mh_theme_search_papers',
        'permission_callback' => '__return_true',
        'args' => array(
            'search' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'technique' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'microscope' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'organism' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'software' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'fluorophore' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'sample_prep' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'cell_line' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'institution' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'facility' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'), // Backward compat
            'brand' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'analysis_software' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'year_min' => array('type' => 'integer', 'sanitize_callback' => 'absint'),
            'year_max' => array('type' => 'integer', 'sanitize_callback' => 'absint'),
            'citations_min' => array('type' => 'integer', 'sanitize_callback' => 'absint'),
            'has_protocols' => array('type' => 'boolean'),
            'has_github' => array('type' => 'boolean'),
            'has_rrids' => array('type' => 'boolean'),
            'has_repositories' => array('type' => 'boolean'),
            'has_figures' => array('type' => 'boolean'),
            'orderby' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'order' => array('type' => 'string', 'sanitize_callback' => 'sanitize_text_field'),
            'page' => array('type' => 'integer', 'default' => 1, 'sanitize_callback' => 'absint'),
            'per_page' => array('type' => 'integer', 'default' => 24, 'sanitize_callback' => 'absint'),
        )
    ));
}
add_action('rest_api_init', 'mh_theme_register_rest_routes');

/**
 * Helper: Get taxonomy terms with URLs for API responses
 */
function mh_get_terms_with_urls($post_id, $taxonomy) {
    if (!taxonomy_exists($taxonomy)) {
        return array();
    }
    $terms = wp_get_object_terms($post_id, $taxonomy);
    if (is_wp_error($terms) || empty($terms)) {
        return array();
    }
    $result = array();
    foreach ($terms as $term) {
        $url = get_term_link($term);
        $result[] = array(
            'name' => $term->name,
            'slug' => $term->slug,
            'url' => !is_wp_error($url) ? $url : home_url('/?s=' . urlencode($term->name)),
        );
    }
    return $result;
}

/**
 * Search protocols (protocol papers + mh_protocol posts) with all filters
 */
function mh_theme_search_protocols($request) {
    if (!mh_plugin_active()) {
        return new WP_REST_Response(array('protocols' => array(), 'total' => 0, 'pages' => 0), 200);
    }
    
    $page = max(1, $request->get_param('page'));
    $per_page = min(100, max(1, $request->get_param('per_page') ?: 24));
    $search = $request->get_param('search');
    $source_filter = $request->get_param('source');
    
    $all_protocols = array();
    
    // =========================================================================
    // 1. PROTOCOL PAPERS (mh_paper with _mh_is_protocol = 1)
    // =========================================================================
    $paper_args = array(
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
    
    // Search
    if (!empty($search)) {
        $paper_args['s'] = $search;
    }
    
    // Taxonomy filters
    $tax_query = array('relation' => 'AND');
    $has_tax = false;
    
    $technique = $request->get_param('technique');
    if (!empty($technique) && taxonomy_exists('mh_technique')) {
        $tax_query[] = array('taxonomy' => 'mh_technique', 'field' => 'slug', 'terms' => $technique);
        $has_tax = true;
    }
    
    $microscope = $request->get_param('microscope');
    if (!empty($microscope) && taxonomy_exists('mh_microscope')) {
        $tax_query[] = array('taxonomy' => 'mh_microscope', 'field' => 'slug', 'terms' => $microscope);
        $has_tax = true;
    }
    
    $organism = $request->get_param('organism');
    if (!empty($organism) && taxonomy_exists('mh_organism')) {
        $tax_query[] = array('taxonomy' => 'mh_organism', 'field' => 'slug', 'terms' => $organism);
        $has_tax = true;
    }
    
    $software = $request->get_param('software');
    if (!empty($software) && taxonomy_exists('mh_software')) {
        $tax_query[] = array('taxonomy' => 'mh_software', 'field' => 'slug', 'terms' => $software);
        $has_tax = true;
    }
    
    if ($has_tax) {
        $paper_args['tax_query'] = $tax_query;
    }
    
    // Meta filters
    $meta_query = array('relation' => 'AND');
    $meta_query[] = array('key' => '_mh_is_protocol', 'value' => '1', 'compare' => '=');
    
    $year_min = $request->get_param('year_min');
    $year_max = $request->get_param('year_max');
    if ($year_min || $year_max) {
        if ($year_min && $year_max) {
            $meta_query[] = array('key' => '_mh_publication_year', 'value' => array($year_min, $year_max), 'compare' => 'BETWEEN', 'type' => 'NUMERIC');
        } elseif ($year_min) {
            $meta_query[] = array('key' => '_mh_publication_year', 'value' => $year_min, 'compare' => '>=', 'type' => 'NUMERIC');
        } else {
            $meta_query[] = array('key' => '_mh_publication_year', 'value' => $year_max, 'compare' => '<=', 'type' => 'NUMERIC');
        }
    }
    
    $citations_min = $request->get_param('citations_min');
    if ($citations_min) {
        $meta_query[] = array('key' => '_mh_citation_count', 'value' => $citations_min, 'compare' => '>=', 'type' => 'NUMERIC');
    }
    
    $author_filter = $request->get_param('author');
    if (!empty($author_filter)) {
        $meta_query[] = array('key' => '_mh_authors', 'value' => $author_filter, 'compare' => 'LIKE');
    }
    
    $fluorophore = $request->get_param('fluorophore');
    if (!empty($fluorophore)) {
        $meta_query[] = array('key' => '_mh_fluorophores', 'value' => $fluorophore, 'compare' => 'LIKE');
    }
    
    $sample_prep = $request->get_param('sample_prep');
    if (!empty($sample_prep)) {
        $meta_query[] = array('key' => '_mh_sample_preparation', 'value' => $sample_prep, 'compare' => 'LIKE');
    }
    
    $cell_line = $request->get_param('cell_line');
    if (!empty($cell_line)) {
        $meta_query[] = array('key' => '_mh_cell_lines', 'value' => $cell_line, 'compare' => 'LIKE');
    }
    
    $brand = $request->get_param('brand');
    if (!empty($brand)) {
        $meta_query[] = array('key' => '_mh_microscope_brands', 'value' => $brand, 'compare' => 'LIKE');
    }
    
    if ($request->get_param('has_github')) {
        $meta_query[] = array('key' => '_mh_github_url', 'value' => '', 'compare' => '!=');
    }
    
    if ($request->get_param('has_figures')) {
        $meta_query[] = array('key' => '_mh_figures', 'value' => '[]', 'compare' => '!=');
    }
    
    $paper_args['meta_query'] = $meta_query;
    
    $protocol_papers = get_posts($paper_args);
    
    foreach ($protocol_papers as $post) {
        $protocol_type = get_post_meta($post->ID, '_mh_protocol_type', true) ?: 'Protocol Journal';
        
        if ($source_filter && stripos($protocol_type, $source_filter) === false) {
            continue;
        }
        
        // Get taxonomy terms with URLs for clickable tags
        $techniques = mh_get_terms_with_urls($post->ID, 'mh_technique');
        $organisms = mh_get_terms_with_urls($post->ID, 'mh_organism');
        $microscopes = mh_get_terms_with_urls($post->ID, 'mh_microscope');
        $software_terms = mh_get_terms_with_urls($post->ID, 'mh_software');

        $doi = get_post_meta($post->ID, '_mh_doi', true);

        // Parse authors - handle both string and JSON array formats
        $authors = get_post_meta($post->ID, '_mh_authors', true);
        $author_list = array();
        if ($authors) {
            $authors_arr = json_decode($authors, true);
            if (is_array($authors_arr)) {
                $author_list = array_slice(array_column($authors_arr, 'name'), 0, 5);
            } else {
                // If not JSON, treat as comma-separated string
                $author_list = array_slice(array_map('trim', preg_split('/[,;]/', $authors)), 0, 5);
            }
        }

        $all_protocols[] = array(
            'id' => $post->ID,
            'title' => $post->post_title,
            'permalink' => get_permalink($post->ID),
            'external_url' => $doi ? "https://doi.org/{$doi}" : '',
            'source' => $protocol_type,
            'type' => 'protocol_paper',
            'doi' => $doi,
            'pubmed_id' => get_post_meta($post->ID, '_mh_pubmed_id', true),
            'authors' => $author_list,
            'journal' => get_post_meta($post->ID, '_mh_journal', true),
            'year' => get_post_meta($post->ID, '_mh_publication_year', true),
            'citations' => intval(get_post_meta($post->ID, '_mh_citation_count', true)),
            'abstract' => wp_trim_words(get_post_meta($post->ID, '_mh_abstract', true), 40, '...'),
            'github_url' => get_post_meta($post->ID, '_mh_github_url', true),
            'repositories' => json_decode(get_post_meta($post->ID, '_mh_repositories', true), true) ?: array(),
            'rrids' => json_decode(get_post_meta($post->ID, '_mh_rrids', true), true) ?: array(),
            'protocols' => json_decode(get_post_meta($post->ID, '_mh_protocols', true), true) ?: array(),
            'techniques' => $techniques,
            'organisms' => $organisms,
            'microscopes' => $microscopes,
            'software' => $software_terms,
            'fluorophores' => json_decode(get_post_meta($post->ID, '_mh_fluorophores', true), true) ?: array(),
            'sample_preparation' => json_decode(get_post_meta($post->ID, '_mh_sample_preparation', true), true) ?: array(),
            'cell_lines' => json_decode(get_post_meta($post->ID, '_mh_cell_lines', true), true) ?: array(),
            'microscope_brands' => json_decode(get_post_meta($post->ID, '_mh_microscope_brands', true), true) ?: array(),
            'figures' => json_decode(get_post_meta($post->ID, '_mh_figures', true), true) ?: array(),
            'figure_count' => intval(get_post_meta($post->ID, '_mh_figure_count', true)),
            'has_figures' => !empty(get_post_meta($post->ID, '_mh_figures', true)) && get_post_meta($post->ID, '_mh_figures', true) !== '[]',
        );
    }
    
    // =========================================================================
    // 2. IMPORTED PROTOCOLS (mh_protocol post type)
    // =========================================================================
    $proto_args = array(
        'post_type' => 'mh_protocol',
        'posts_per_page' => -1,
        'post_status' => 'publish',
    );
    
    if (!empty($search)) {
        $proto_args['s'] = $search;
    }
    
    // Reuse taxonomy filters for mh_protocol
    if ($has_tax) {
        $proto_args['tax_query'] = $tax_query;
    }
    
    // Build meta query for mh_protocol (similar structure)
    $proto_meta_query = array('relation' => 'AND');
    
    if ($year_min || $year_max) {
        if ($year_min && $year_max) {
            $proto_meta_query[] = array('key' => '_mh_year', 'value' => array($year_min, $year_max), 'compare' => 'BETWEEN', 'type' => 'NUMERIC');
        } elseif ($year_min) {
            $proto_meta_query[] = array('key' => '_mh_year', 'value' => $year_min, 'compare' => '>=', 'type' => 'NUMERIC');
        } else {
            $proto_meta_query[] = array('key' => '_mh_year', 'value' => $year_max, 'compare' => '<=', 'type' => 'NUMERIC');
        }
    }
    
    if (!empty($fluorophore)) {
        $proto_meta_query[] = array('key' => '_mh_fluorophores', 'value' => $fluorophore, 'compare' => 'LIKE');
    }
    
    if (!empty($sample_prep)) {
        $proto_meta_query[] = array('key' => '_mh_sample_preparation', 'value' => $sample_prep, 'compare' => 'LIKE');
    }
    
    if (!empty($cell_line)) {
        $proto_meta_query[] = array('key' => '_mh_cell_lines', 'value' => $cell_line, 'compare' => 'LIKE');
    }
    
    if (!empty($brand)) {
        $proto_meta_query[] = array('key' => '_mh_microscope_brands', 'value' => $brand, 'compare' => 'LIKE');
    }
    
    if (count($proto_meta_query) > 1) {
        $proto_args['meta_query'] = $proto_meta_query;
    }
    
    $imported_protocols = get_posts($proto_args);
    
    foreach ($imported_protocols as $post) {
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
        $proto_url = '';
        $external_url = '';
        
        if (!empty($doi)) {
            $external_url = "https://doi.org/{$doi}";
            $proto_url = get_permalink($post->ID);
        } else {
            $proto_url = get_post_meta($post->ID, '_mh_protocol_url', true);
            if (empty($proto_url)) {
                $proto_url = get_permalink($post->ID);
            }
            $external_url = $proto_url;
        }
        
        // Get taxonomy terms with URLs for clickable tags
        $techniques = mh_get_terms_with_urls($post->ID, 'mh_technique');
        $organisms = mh_get_terms_with_urls($post->ID, 'mh_organism');
        $microscopes = mh_get_terms_with_urls($post->ID, 'mh_microscope');
        $software_terms = mh_get_terms_with_urls($post->ID, 'mh_software');

        // Get authors - try multiple formats
        $authors = get_post_meta($post->ID, '_mh_authors', true);
        $author_list = array();
        if ($authors) {
            $authors_arr = json_decode($authors, true);
            if (is_array($authors_arr)) {
                // Check if it's array of objects with 'name' key
                if (!empty($authors_arr) && isset($authors_arr[0]['name'])) {
                    $author_list = array_slice(array_column($authors_arr, 'name'), 0, 5);
                } elseif (!empty($authors_arr) && is_string($authors_arr[0])) {
                    // It's already an array of strings
                    $author_list = array_slice($authors_arr, 0, 5);
                }
            }
        }
        
        // Get additional data for imported protocols
        $figures = json_decode(get_post_meta($post->ID, '_mh_figures', true), true) ?: array();
        $figure_count = intval(get_post_meta($post->ID, '_mh_figure_count', true));
        $has_figures = !empty($figures) || $figure_count > 0;
        $github_url = get_post_meta($post->ID, '_mh_github_url', true);
        $repositories = json_decode(get_post_meta($post->ID, '_mh_repositories', true), true) ?: array();
        $rrids = json_decode(get_post_meta($post->ID, '_mh_rrids', true), true) ?: array();
        $protocols_linked = json_decode(get_post_meta($post->ID, '_mh_protocols', true), true) ?: array();
        $journal = get_post_meta($post->ID, '_mh_journal', true);
        $citations = intval(get_post_meta($post->ID, '_mh_citation_count', true));
        
        $all_protocols[] = array(
            'id' => $post->ID,
            'title' => $post->post_title,
            'permalink' => $proto_url,
            'external_url' => $external_url,
            'source' => $source,
            'type' => 'imported',
            'doi' => $doi,
            'pubmed_id' => get_post_meta($post->ID, '_mh_pubmed_id', true),
            'authors' => $author_list,
            'journal' => $journal,
            'year' => get_post_meta($post->ID, '_mh_year', true),
            'citations' => $citations,
            'abstract' => wp_trim_words(get_post_meta($post->ID, '_mh_abstract', true) ?: $post->post_content, 40, '...'),
            'github_url' => $github_url,
            'repositories' => $repositories,
            'rrids' => $rrids,
            'protocols' => $protocols_linked,
            'techniques' => $techniques,
            'organisms' => $organisms,
            'microscopes' => $microscopes,
            'software' => $software_terms,
            'fluorophores' => json_decode(get_post_meta($post->ID, '_mh_fluorophores', true), true) ?: array(),
            'sample_preparation' => json_decode(get_post_meta($post->ID, '_mh_sample_preparation', true), true) ?: array(),
            'cell_lines' => json_decode(get_post_meta($post->ID, '_mh_cell_lines', true), true) ?: array(),
            'microscope_brands' => json_decode(get_post_meta($post->ID, '_mh_microscope_brands', true), true) ?: array(),
            'figures' => $figures,
            'figure_count' => $figure_count,
            'has_figures' => $has_figures,
        );
    }
    
    // Sort protocols
    $orderby = $request->get_param('orderby') ?: 'citations';
    $order = strtolower($request->get_param('order') ?: 'desc');
    
    usort($all_protocols, function($a, $b) use ($orderby, $order) {
        $val_a = $val_b = 0;
        
        if ($orderby === 'citations') {
            $val_a = $a['citations'];
            $val_b = $b['citations'];
        } elseif ($orderby === 'year') {
            $val_a = intval($a['year']);
            $val_b = intval($b['year']);
        } elseif ($orderby === 'title') {
            return $order === 'asc' ? strcmp($a['title'], $b['title']) : strcmp($b['title'], $a['title']);
        }
        
        return $order === 'asc' ? $val_a - $val_b : $val_b - $val_a;
    });
    
    // Paginate
    $total = count($all_protocols);
    $total_pages = ceil($total / $per_page);
    $offset = ($page - 1) * $per_page;
    $protocols_page = array_slice($all_protocols, $offset, $per_page);
    
    return new WP_REST_Response(array(
        'protocols' => $protocols_page,
        'total' => $total,
        'pages' => $total_pages,
        'page' => $page,
    ), 200);
}

/**
 * Search papers with all filters
 */
function mh_theme_search_papers($request) {
    if (!mh_plugin_active()) {
        return new WP_REST_Response(array('papers' => array(), 'total' => 0, 'pages' => 0), 200);
    }
    
    $page = max(1, $request->get_param('page'));
    $per_page = min(100, max(1, $request->get_param('per_page') ?: 24));
    
    // Build query args
    $args = array(
        'post_type' => 'mh_paper',
        'posts_per_page' => $per_page,
        'paged' => $page,
        'post_status' => 'publish',
    );
    
    // Search query - search in title, content, and custom fields
    $search = $request->get_param('search');
    if (!empty($search)) {
        global $wpdb;
        $search_term = '%' . $wpdb->esc_like($search) . '%';
        
        // Find post IDs that match in meta fields (authors, DOI, abstract, journal)
        $meta_matches = $wpdb->get_col($wpdb->prepare(
            "SELECT DISTINCT post_id FROM {$wpdb->postmeta} 
            WHERE meta_key IN ('_mh_authors', '_mh_doi', '_mh_abstract', '_mh_journal') 
            AND meta_value LIKE %s",
            $search_term
        ));
        
        // Find post IDs that match in facility taxonomy
        $facility_matches = array();
        if (taxonomy_exists('mh_facility')) {
            $facility_terms = get_terms(array(
                'taxonomy' => 'mh_facility',
                'hide_empty' => true,
                'name__like' => $search,
            ));
            if (!is_wp_error($facility_terms) && !empty($facility_terms)) {
                $term_ids = wp_list_pluck($facility_terms, 'term_id');
                $facility_post_ids = get_objects_in_term($term_ids, 'mh_facility');
                if (!is_wp_error($facility_post_ids)) {
                    $facility_matches = $facility_post_ids;
                }
            }
        }
        
        // Combine all matches
        $all_meta_matches = array_unique(array_merge($meta_matches, $facility_matches));
        
        if (!empty($all_meta_matches)) {
            // Use post__in combined with search, or just post__in if no title match needed
            // We'll do a two-part approach: regular search + meta matches
            $args['s'] = $search;
            
            // Add a filter to include meta matches in results
            add_filter('posts_where', function($where, $query) use ($all_meta_matches, $wpdb) {
                if (!empty($all_meta_matches)) {
                    $ids_string = implode(',', array_map('intval', $all_meta_matches));
                    $where = preg_replace(
                        '/\(\s*' . preg_quote($wpdb->posts, '/') . '\.post_title/',
                        '((' . $wpdb->posts . '.ID IN (' . $ids_string . ')) OR (' . $wpdb->posts . '.post_title',
                        $where,
                        1
                    );
                    // Close the extra parenthesis
                    if (strpos($where, '.ID IN (') !== false) {
                        $where = preg_replace('/\)\s*\)\s*$/', ')))', $where);
                    }
                }
                return $where;
            }, 10, 2);
        } else {
            $args['s'] = $search;
        }
    }
    
    // Taxonomy filters
    $tax_query = array('relation' => 'AND');
    $has_tax_filter = false;
    
    // Helper function to find matching term
    $find_term = function($taxonomy, $search_value) {
        if (!taxonomy_exists($taxonomy)) return null;
        
        // Try exact slug match first
        $term = get_term_by('slug', $search_value, $taxonomy);
        if ($term) return $term;
        
        // Try with different slug variations
        $variations = array(
            $search_value,
            str_replace('-', ' ', $search_value),
            str_replace('_', '-', $search_value),
            str_replace(' ', '-', $search_value),
            strtolower($search_value),
        );
        
        foreach ($variations as $variant) {
            $term = get_term_by('slug', $variant, $taxonomy);
            if ($term) return $term;
            
            $term = get_term_by('name', $variant, $taxonomy);
            if ($term) return $term;
        }
        
        // Try partial match in term names
        $terms = get_terms(array(
            'taxonomy' => $taxonomy,
            'hide_empty' => false,
            'name__like' => str_replace('-', ' ', $search_value),
        ));
        if (!empty($terms) && !is_wp_error($terms)) {
            return $terms[0];
        }
        
        // Try partial match in slugs
        $all_terms = get_terms(array('taxonomy' => $taxonomy, 'hide_empty' => false));
        if (!is_wp_error($all_terms)) {
            $search_lower = strtolower(str_replace('-', '', $search_value));
            foreach ($all_terms as $t) {
                $slug_clean = strtolower(str_replace('-', '', $t->slug));
                $name_clean = strtolower(str_replace(' ', '', $t->name));
                if (strpos($slug_clean, $search_lower) !== false || 
                    strpos($name_clean, $search_lower) !== false ||
                    strpos($search_lower, $slug_clean) !== false) {
                    return $t;
                }
            }
        }
        
        return null;
    };
    
    // Technique filter
    $technique = $request->get_param('technique');
    if (!empty($technique) && taxonomy_exists('mh_technique')) {
        $term = $find_term('mh_technique', $technique);
        if ($term) {
            $tax_query[] = array(
                'taxonomy' => 'mh_technique',
                'field' => 'term_id',
                'terms' => $term->term_id,
            );
            $has_tax_filter = true;
        }
    }
    
    // Microscope filter
    $microscope = $request->get_param('microscope');
    if (!empty($microscope) && taxonomy_exists('mh_microscope')) {
        $term = $find_term('mh_microscope', $microscope);
        if ($term) {
            $tax_query[] = array(
                'taxonomy' => 'mh_microscope',
                'field' => 'term_id',
                'terms' => $term->term_id,
            );
            $has_tax_filter = true;
        }
    }
    
    // Organism filter
    $organism = $request->get_param('organism');
    if (!empty($organism) && taxonomy_exists('mh_organism')) {
        $term = $find_term('mh_organism', $organism);
        if ($term) {
            $tax_query[] = array(
                'taxonomy' => 'mh_organism',
                'field' => 'term_id',
                'terms' => $term->term_id,
            );
            $has_tax_filter = true;
        }
    }
    
    // Software filter
    $software = $request->get_param('software');
    if (!empty($software) && taxonomy_exists('mh_software')) {
        $term = $find_term('mh_software', $software);
        if ($term) {
            $tax_query[] = array(
                'taxonomy' => 'mh_software',
                'field' => 'term_id',
                'terms' => $term->term_id,
            );
            $has_tax_filter = true;
        }
    }
    
    // Institution filter (uses mh_facility taxonomy for backward compatibility)
    $institution = $request->get_param('institution');
    if (!$institution) {
        $institution = $request->get_param('facility'); // Backward compatibility
    }
    if (!empty($institution) && taxonomy_exists('mh_facility')) {
        $term = $find_term('mh_facility', $institution);
        if ($term) {
            $tax_query[] = array(
                'taxonomy' => 'mh_facility',
                'field' => 'term_id',
                'terms' => $term->term_id,
            );
            $has_tax_filter = true;
        }
    }
    
    if ($has_tax_filter) {
        $args['tax_query'] = $tax_query;
    }
    
    // Meta queries
    $meta_query = array('relation' => 'AND');
    $has_meta_filter = false;
    
    // Year filter
    $year_min = $request->get_param('year_min');
    $year_max = $request->get_param('year_max');
    if ($year_min) {
        $meta_query[] = array(
            'key' => '_mh_publication_year',
            'value' => $year_min,
            'compare' => '>=',
            'type' => 'NUMERIC'
        );
        $has_meta_filter = true;
    }
    if ($year_max) {
        $meta_query[] = array(
            'key' => '_mh_publication_year',
            'value' => $year_max,
            'compare' => '<=',
            'type' => 'NUMERIC'
        );
        $has_meta_filter = true;
    }
    
    // Citation filter
    $citations_min = $request->get_param('citations_min');
    if ($citations_min) {
        $meta_query[] = array(
            'key' => '_mh_citation_count',
            'value' => $citations_min,
            'compare' => '>=',
            'type' => 'NUMERIC'
        );
        $has_meta_filter = true;
    }
    
    // Author filter - search only in authors field
    $author_filter = $request->get_param('author');
    if (!empty($author_filter)) {
        $meta_query[] = array(
            'key' => '_mh_authors',
            'value' => $author_filter,
            'compare' => 'LIKE'
        );
        $has_meta_filter = true;
    }
    
    // Has protocols filter - check has_protocols flag OR non-empty protocols JSON
    if ($request->get_param('has_protocols')) {
        $meta_query[] = array(
            'relation' => 'OR',
            array(
                'key' => '_mh_has_protocols',
                'value' => '1',
                'compare' => '='
            ),
            array(
                'key' => '_mh_protocols',
                'value' => '"url"',  // JSON with url field
                'compare' => 'LIKE'
            )
        );
        $has_meta_filter = true;
    }
    
    // Has GitHub filter
    if ($request->get_param('has_github')) {
        $meta_query[] = array(
            'relation' => 'OR',
            array(
                'key' => '_mh_has_github',
                'value' => '1',
                'compare' => '='
            ),
            array(
                'key' => '_mh_github_url',
                'value' => '',
                'compare' => '!='
            )
        );
        $has_meta_filter = true;
    }
    
    // Has RRIDs filter - check has_rrids flag OR non-empty RRIDs JSON
    if ($request->get_param('has_rrids')) {
        $meta_query[] = array(
            'relation' => 'OR',
            array(
                'key' => '_mh_has_rrids',
                'value' => '1',
                'compare' => '='
            ),
            array(
                'key' => '_mh_rrids',
                'value' => '"id"',  // JSON with id field
                'compare' => 'LIKE'
            )
        );
        $has_meta_filter = true;
    }
    
    // Has data repositories filter - check has_data flag OR non-empty repos JSON
    if ($request->get_param('has_repositories')) {
        $meta_query[] = array(
            'relation' => 'OR',
            array(
                'key' => '_mh_has_data',
                'value' => '1',
                'compare' => '='
            ),
            array(
                'key' => '_mh_repositories',
                'value' => '"url"',  // JSON with url field
                'compare' => 'LIKE'
            )
        );
        $has_meta_filter = true;
    }
    
    // Has figures filter
    if ($request->get_param('has_figures')) {
        $meta_query[] = array(
            'key' => '_mh_figures',
            'value' => '[]',
            'compare' => '!='
        );
        $meta_query[] = array(
            'key' => '_mh_figures',
            'value' => '',
            'compare' => '!='
        );
        $has_meta_filter = true;
    }
    
    // has_full_text filter removed - full text is no longer stored
    
    // Fluorophore filter - search in JSON array
    $fluorophore = $request->get_param('fluorophore');
    if ($fluorophore) {
        $meta_query[] = array(
            'key' => '_mh_fluorophores',
            'value' => $fluorophore,
            'compare' => 'LIKE'
        );
        $has_meta_filter = true;
    }
    
    // Sample preparation filter
    $sample_prep = $request->get_param('sample_prep');
    if ($sample_prep) {
        $meta_query[] = array(
            'key' => '_mh_sample_preparation',
            'value' => $sample_prep,
            'compare' => 'LIKE'
        );
        $has_meta_filter = true;
    }
    
    // Cell line filter
    $cell_line = $request->get_param('cell_line');
    if ($cell_line) {
        $meta_query[] = array(
            'key' => '_mh_cell_lines',
            'value' => $cell_line,
            'compare' => 'LIKE'
        );
        $has_meta_filter = true;
    }
    
    // Brand filter
    $brand = $request->get_param('brand');
    if ($brand) {
        $meta_query[] = array(
            'key' => '_mh_microscope_brands',
            'value' => $brand,
            'compare' => 'LIKE'
        );
        $has_meta_filter = true;
    }
    
    // Analysis software filter
    $analysis_software = $request->get_param('analysis_software');
    if ($analysis_software) {
        $meta_query[] = array(
            'key' => '_mh_image_analysis_software',
            'value' => $analysis_software,
            'compare' => 'LIKE'
        );
        $has_meta_filter = true;
    }
    
    if ($has_meta_filter) {
        $args['meta_query'] = $meta_query;
    }
    
    // Sorting
    $orderby = $request->get_param('orderby') ?: 'citations';
    $order = strtoupper($request->get_param('order') ?: 'DESC');
    if (!in_array($order, array('ASC', 'DESC'))) $order = 'DESC';
    
    switch ($orderby) {
        case 'citations':
            $args['meta_key'] = '_mh_citation_count';
            $args['orderby'] = 'meta_value_num';
            $args['order'] = $order;
            break;
        case 'year':
            $args['meta_key'] = '_mh_publication_year';
            $args['orderby'] = 'meta_value_num';
            $args['order'] = $order;
            break;
        case 'title':
            $args['orderby'] = 'title';
            $args['order'] = $order;
            break;
        default:
            $args['meta_key'] = '_mh_citation_count';
            $args['orderby'] = 'meta_value_num';
            $args['order'] = 'DESC';
    }
    
    // Run query
    $query = new WP_Query($args);
    
    // Build response
    $papers = array();
    if ($query->have_posts()) {
        while ($query->have_posts()) {
            $query->the_post();
            $id = get_the_ID();
            
            // Get all metadata
            $protocols = json_decode(get_post_meta($id, '_mh_protocols', true), true) ?: array();
            $repositories = json_decode(get_post_meta($id, '_mh_repositories', true), true) ?: array();
            $rrids = json_decode(get_post_meta($id, '_mh_rrids', true), true) ?: array();
            
            // Get taxonomy terms with URLs for clickable tags
            $techniques = array();
            if (taxonomy_exists('mh_technique')) {
                $terms = get_the_terms($id, 'mh_technique');
                if ($terms && !is_wp_error($terms)) {
                    foreach ($terms as $term) {
                        $url = get_term_link($term);
                        $techniques[] = array(
                            'name' => $term->name,
                            'slug' => $term->slug,
                            'url' => !is_wp_error($url) ? $url : home_url('/?s=' . urlencode($term->name)),
                        );
                    }
                }
            }

            $microscopes = array();
            if (taxonomy_exists('mh_microscope')) {
                $terms = get_the_terms($id, 'mh_microscope');
                if ($terms && !is_wp_error($terms)) {
                    foreach ($terms as $term) {
                        $url = get_term_link($term);
                        $microscopes[] = array(
                            'name' => $term->name,
                            'slug' => $term->slug,
                            'url' => !is_wp_error($url) ? $url : home_url('/?s=' . urlencode($term->name)),
                        );
                    }
                }
            }

            $organisms = array();
            if (taxonomy_exists('mh_organism')) {
                $terms = get_the_terms($id, 'mh_organism');
                if ($terms && !is_wp_error($terms)) {
                    foreach ($terms as $term) {
                        $url = get_term_link($term);
                        $organisms[] = array(
                            'name' => $term->name,
                            'slug' => $term->slug,
                            'url' => !is_wp_error($url) ? $url : home_url('/?s=' . urlencode($term->name)),
                        );
                    }
                }
            }

            $software = array();
            if (taxonomy_exists('mh_software')) {
                $terms = get_the_terms($id, 'mh_software');
                if ($terms && !is_wp_error($terms)) {
                    foreach ($terms as $term) {
                        $url = get_term_link($term);
                        $software[] = array(
                            'name' => $term->name,
                            'slug' => $term->slug,
                            'url' => !is_wp_error($url) ? $url : home_url('/?s=' . urlencode($term->name)),
                        );
                    }
                }
            }
            
            $papers[] = array(
                'id' => $id,
                'title' => get_the_title(),
                'permalink' => get_permalink(),
                'doi' => get_post_meta($id, '_mh_doi', true),
                'pubmed_id' => get_post_meta($id, '_mh_pubmed_id', true),
                'authors' => get_post_meta($id, '_mh_authors', true),
                'journal' => get_post_meta($id, '_mh_journal', true),
                'year' => get_post_meta($id, '_mh_publication_year', true),
                'citations' => intval(get_post_meta($id, '_mh_citation_count', true)),
                'abstract' => get_post_meta($id, '_mh_abstract', true),
                'github_url' => get_post_meta($id, '_mh_github_url', true),
                'pdf_url' => get_post_meta($id, '_mh_pdf_url', true),
                'techniques' => $techniques,
                'microscopes' => $microscopes,
                'organisms' => $organisms,
                'software' => $software,
                'protocols' => $protocols,
                'repositories' => $repositories,
                'rrids' => $rrids,
                // New fields
                'fluorophores' => json_decode(get_post_meta($id, '_mh_fluorophores', true), true) ?: array(),
                'sample_preparation' => json_decode(get_post_meta($id, '_mh_sample_preparation', true), true) ?: array(),
                'cell_lines' => json_decode(get_post_meta($id, '_mh_cell_lines', true), true) ?: array(),
                'microscope_brands' => json_decode(get_post_meta($id, '_mh_microscope_brands', true), true) ?: array(),
                'image_analysis_software' => json_decode(get_post_meta($id, '_mh_image_analysis_software', true), true) ?: array(),
                'figures' => json_decode(get_post_meta($id, '_mh_figures', true), true) ?: array(),
                'figure_count' => intval(get_post_meta($id, '_mh_figure_count', true)),
                'has_full_text' => false, // Full text no longer stored
                'has_figures' => !empty(get_post_meta($id, '_mh_figures', true)) && get_post_meta($id, '_mh_figures', true) !== '[]',
            );
        }
    }
    wp_reset_postdata();
    
    return new WP_REST_Response(array(
        'papers' => $papers,
        'total' => $query->found_posts,
        'pages' => $query->max_num_pages,
        'page' => $page,
        'per_page' => $per_page,
    ), 200);
}

/**
 * Get available filter options from database
 */
function mh_theme_register_filters_route() {
    register_rest_route('microhub-theme/v1', '/filters', array(
        'methods' => 'GET',
        'callback' => 'mh_theme_get_filters',
        'permission_callback' => '__return_true',
    ));
}
add_action('rest_api_init', 'mh_theme_register_filters_route');

function mh_theme_get_filters() {
    $filters = array(
        'techniques' => array(),
        'microscopes' => array(),
        'organisms' => array(),
        'software' => array(),
    );
    
    // Get techniques
    if (taxonomy_exists('mh_technique')) {
        $terms = get_terms(array(
            'taxonomy' => 'mh_technique',
            'hide_empty' => true,
            'orderby' => 'count',
            'order' => 'DESC',
        ));
        if (!is_wp_error($terms)) {
            foreach ($terms as $term) {
                $filters['techniques'][] = array(
                    'slug' => $term->slug,
                    'name' => $term->name,
                    'count' => $term->count,
                );
            }
        }
    }
    
    // Get microscopes
    if (taxonomy_exists('mh_microscope')) {
        $terms = get_terms(array(
            'taxonomy' => 'mh_microscope',
            'hide_empty' => true,
            'orderby' => 'count',
            'order' => 'DESC',
        ));
        if (!is_wp_error($terms)) {
            foreach ($terms as $term) {
                $filters['microscopes'][] = array(
                    'slug' => $term->slug,
                    'name' => $term->name,
                    'count' => $term->count,
                );
            }
        }
    }
    
    // Get organisms
    if (taxonomy_exists('mh_organism')) {
        $terms = get_terms(array(
            'taxonomy' => 'mh_organism',
            'hide_empty' => true,
            'orderby' => 'count',
            'order' => 'DESC',
        ));
        if (!is_wp_error($terms)) {
            foreach ($terms as $term) {
                $filters['organisms'][] = array(
                    'slug' => $term->slug,
                    'name' => $term->name,
                    'count' => $term->count,
                );
            }
        }
    }
    
    // Get software
    if (taxonomy_exists('mh_software')) {
        $terms = get_terms(array(
            'taxonomy' => 'mh_software',
            'hide_empty' => true,
            'orderby' => 'count',
            'order' => 'DESC',
        ));
        if (!is_wp_error($terms)) {
            foreach ($terms as $term) {
                $filters['software'][] = array(
                    'slug' => $term->slug,
                    'name' => $term->name,
                    'count' => $term->count,
                );
            }
        }
    }
    
    return new WP_REST_Response($filters, 200);
}

// ============================================
// CHECK IF PLUGIN IS ACTIVE
// ============================================

/**
 * Check if MicroHub plugin is active
 */
function mh_plugin_active() {
    return post_type_exists('mh_paper');
}

/**
 * Show admin notice if plugin is not active
 */
function mh_admin_notice() {
    if (!mh_plugin_active()) {
        echo '<div class="notice notice-warning"><p><strong>MicroHub Theme:</strong> The MicroHub plugin is required for full functionality. Please activate the MicroHub plugin.</p></div>';
    }
}
add_action('admin_notices', 'mh_admin_notice');

// ============================================
// HELPER FUNCTIONS FOR PLUGIN DATA
// ============================================

/**
 * Get all paper metadata - COMPREHENSIVE
 */
function mh_get_paper_meta($post_id = null) {
    if (!$post_id) $post_id = get_the_ID();
    
    return array(
        // Basic info
        'doi' => get_post_meta($post_id, '_mh_doi', true),
        'pubmed_id' => get_post_meta($post_id, '_mh_pubmed_id', true),
        'pmc_id' => get_post_meta($post_id, '_mh_pmc_id', true),
        'authors' => get_post_meta($post_id, '_mh_authors', true),
        'journal' => get_post_meta($post_id, '_mh_journal', true),
        'year' => get_post_meta($post_id, '_mh_publication_year', true),
        'citations' => get_post_meta($post_id, '_mh_citation_count', true),
        'abstract' => get_post_meta($post_id, '_mh_abstract', true),
        
        // Content (full_text no longer stored to save space)
        'methods' => get_post_meta($post_id, '_mh_methods', true),
        'full_text' => '', // No longer stored
        
        // URLs
        'pdf_url' => get_post_meta($post_id, '_mh_pdf_url', true),
        'github_url' => get_post_meta($post_id, '_mh_github_url', true),
        'doi_url' => get_post_meta($post_id, '_mh_doi_url', true),
        'pubmed_url' => get_post_meta($post_id, '_mh_pubmed_url', true),
        'pmc_url' => get_post_meta($post_id, '_mh_pmc_url', true),
        
        // Equipment
        'microscope_details' => get_post_meta($post_id, '_mh_microscope_details', true),
        'microscope_brands' => json_decode(get_post_meta($post_id, '_mh_microscope_brands', true), true) ?: array(),
        'microscope_models' => json_decode(get_post_meta($post_id, '_mh_microscope_models', true), true) ?: array(),
        
        // Institutions (uses facility fields for backward compatibility)
        'institution' => get_post_meta($post_id, '_mh_facility', true),
        'institutions' => json_decode(get_post_meta($post_id, '_mh_institutions', true), true) ?: 
                         (taxonomy_exists('mh_facility') ? wp_get_post_terms($post_id, 'mh_facility', array('fields' => 'names')) : array()),
        'facility' => get_post_meta($post_id, '_mh_facility', true), // Backward compat
        'facility_url' => get_post_meta($post_id, '_mh_facility_url', true),
        'facilities' => taxonomy_exists('mh_facility') ? wp_get_post_terms($post_id, 'mh_facility', array('fields' => 'names')) : array(),
        
        // Resources
        'protocols' => json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array(),
        'repositories' => json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array(),
        'rrids' => json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array(),
        'rors' => json_decode(get_post_meta($post_id, '_mh_rors', true), true) ?: array(),
        'supplementary_materials' => json_decode(get_post_meta($post_id, '_mh_supplementary_materials', true), true) ?: array(),
        
        // GitHub Tools (enriched repo data from scraper v5.1+)
        'github_tools' => json_decode(get_post_meta($post_id, '_mh_github_tools', true), true) ?: array(),
        
        // Figures
        'figures' => json_decode(get_post_meta($post_id, '_mh_figures', true), true) ?: array(),
        'figure_count' => intval(get_post_meta($post_id, '_mh_figure_count', true)),
        
        // Categorized tags
        'microscopy_techniques' => json_decode(get_post_meta($post_id, '_mh_microscopy_techniques', true), true) ?: array(),
        'image_analysis_software' => json_decode(get_post_meta($post_id, '_mh_image_analysis_software', true), true) ?: array(),
        'image_acquisition_software' => json_decode(get_post_meta($post_id, '_mh_image_acquisition_software', true), true) ?: array(),
        'organisms' => json_decode(get_post_meta($post_id, '_mh_organisms', true), true) ?: array(),
        'antibody_sources' => json_decode(get_post_meta($post_id, '_mh_antibody_sources', true), true) ?: array(),
        'sample_preparation' => json_decode(get_post_meta($post_id, '_mh_sample_preparation', true), true) ?: array(),
        'fluorophores' => json_decode(get_post_meta($post_id, '_mh_fluorophores', true), true) ?: array(),
        'cell_lines' => json_decode(get_post_meta($post_id, '_mh_cell_lines', true), true) ?: array(),
        
        // Tag extraction metadata
        'tag_source' => get_post_meta($post_id, '_mh_tag_source', true),
        
        // Flags
        'has_full_text' => false, // No longer stored
        'has_figures' => get_post_meta($post_id, '_mh_has_figures', true),
        'has_protocols' => get_post_meta($post_id, '_mh_has_protocols', true),
        'has_github' => get_post_meta($post_id, '_mh_has_github', true),
        'has_github_tools' => get_post_meta($post_id, '_mh_has_github_tools', true),
        'has_data' => get_post_meta($post_id, '_mh_has_data', true),
        'has_rors' => !empty(json_decode(get_post_meta($post_id, '_mh_rors', true), true)),
    );
}

/**
 * Display paper badge (Foundational/High Impact)
 */
function mh_paper_badge($citations = null) {
    if ($citations === null) {
        $citations = get_post_meta(get_the_ID(), '_mh_citation_count', true);
    }
    $citations = intval($citations);
    
    if ($citations >= 100) {
        echo '<span class="mh-badge mh-badge-foundational">⭐ Foundational</span>';
    } elseif ($citations >= 50) {
        echo '<span class="mh-badge mh-badge-high-impact">🔥 High Impact</span>';
    }
}

/**
 * Display paper meta (journal, year, citations)
 */
function mh_display_paper_meta($meta = null) {
    if (!$meta) $meta = mh_get_paper_meta();
    
    echo '<div class="mh-paper-meta">';
    if ($meta['journal']) {
        echo '<span class="mh-meta-item">📖 ' . esc_html($meta['journal']) . '</span>';
    }
    if ($meta['year']) {
        echo '<span class="mh-meta-item">📅 ' . esc_html($meta['year']) . '</span>';
    }
    if ($meta['citations']) {
        echo '<span class="mh-meta-item">📊 ' . number_format(intval($meta['citations'])) . ' citations</span>';
    }
    echo '</div>';
}

/**
 * Display paper links (DOI, PubMed, PDF, GitHub)
 */
function mh_display_paper_links($meta = null) {
    if (!$meta) $meta = mh_get_paper_meta();
    
    echo '<div class="mh-paper-links">';
    if ($meta['doi']) {
        echo '<a href="https://doi.org/' . esc_attr($meta['doi']) . '" class="mh-btn mh-btn-doi" target="_blank">DOI</a>';
    }
    if ($meta['pubmed_id']) {
        echo '<a href="https://pubmed.ncbi.nlm.nih.gov/' . esc_attr($meta['pubmed_id']) . '" class="mh-btn mh-btn-pubmed" target="_blank">PubMed</a>';
    }
    if ($meta['pdf_url']) {
        echo '<a href="' . esc_url($meta['pdf_url']) . '" class="mh-btn mh-btn-pdf" target="_blank">PDF</a>';
    }
    if ($meta['github_url']) {
        echo '<a href="' . esc_url($meta['github_url']) . '" class="mh-btn mh-btn-github" target="_blank">GitHub</a>';
    }
    echo '</div>';
}

/**
 * Display paper tags (all taxonomies)
 */
function mh_display_paper_tags($post_id = null) {
    if (!$post_id) $post_id = get_the_ID();
    
    $taxonomies = array(
        'mh_technique' => 'technique',
        'mh_microscope' => 'microscope',
        'mh_organism' => 'organism',
        'mh_software' => 'software'
    );
    
    echo '<div class="mh-tags">';
    foreach ($taxonomies as $tax => $class) {
        if (!taxonomy_exists($tax)) continue;
        
        $terms = get_the_terms($post_id, $tax);
        if ($terms && !is_wp_error($terms)) {
            foreach ($terms as $term) {
                $link = get_term_link($term);
                if (!is_wp_error($link)) {
                    echo '<a href="' . esc_url($link) . '" class="mh-tag mh-tag-' . $class . '">' . esc_html($term->name) . '</a>';
                }
            }
        }
    }
    echo '</div>';
}

/**
 * Display protocols section
 */
function mh_display_protocols($protocols = null) {
    if ($protocols === null) {
        $protocols = json_decode(get_post_meta(get_the_ID(), '_mh_protocols', true), true) ?: array();
    }
    
    if (empty($protocols)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>📋 Protocols</h2>';
    echo '<div class="mh-protocol-list">';
    
    foreach ($protocols as $protocol) {
        $name = isset($protocol['name']) ? $protocol['name'] : 'Protocol';
        $url = isset($protocol['url']) ? $protocol['url'] : '#';
        $source = isset($protocol['source']) ? $protocol['source'] : 'Protocol';
        
        echo '<a href="' . esc_url($url) . '" class="mh-protocol-item" target="_blank">';
        echo '<span class="mh-protocol-icon">📄</span>';
        echo '<span class="mh-protocol-name">' . esc_html($name) . '</span>';
        echo '<span class="mh-protocol-source">' . esc_html($source) . '</span>';
        echo '<span class="mh-protocol-arrow">→</span>';
        echo '</a>';
    }
    
    echo '</div>';
    echo '</div>';
}

/**
 * Display GitHub section
 */
function mh_display_github($url = null, $github_tools = null) {
    if ($url === null) {
        $url = get_post_meta(get_the_ID(), '_mh_github_url', true);
    }
    if ($github_tools === null) {
        $github_tools = json_decode(get_post_meta(get_the_ID(), '_mh_github_tools', true), true) ?: array();
    }
    
    if (empty($url) && empty($github_tools)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>💻 Code & Software</h2>';
    
    // If we have enriched github_tools data, show rich cards
    if (!empty($github_tools)) {
        echo '<div class="mh-github-tools-list">';
        foreach ($github_tools as $tool) {
            $tool_url = !empty($tool['url']) ? $tool['url'] : 'https://github.com/' . ($tool['full_name'] ?? '');
            $health = intval($tool['health_score'] ?? 0);
            $is_archived = !empty($tool['is_archived']);
            
            if ($is_archived) { $health_class = 'archived'; $health_label = 'Archived'; }
            elseif ($health >= 70) { $health_class = 'active'; $health_label = 'Active'; }
            elseif ($health >= 40) { $health_class = 'moderate'; $health_label = 'Moderate'; }
            elseif ($health > 0) { $health_class = 'low'; $health_label = 'Low Activity'; }
            else { $health_class = 'unknown'; $health_label = ''; }
            
            $rel = $tool['relationship'] ?? 'uses';
            $rel_labels = array('introduces' => '🆕 Introduced here', 'uses' => '🔧 Used', 'extends' => '🔀 Extended', 'benchmarks' => '📊 Benchmarked');
            $rel_label = $rel_labels[$rel] ?? '🔧 Used';
            
            echo '<a href="' . esc_url($tool_url) . '" class="mh-github-tool-card health-' . $health_class . '" target="_blank" rel="noopener">';
            echo '<div class="mh-ght-header">';
            echo '<strong class="mh-ght-name">' . esc_html($tool['full_name'] ?? '') . '</strong>';
            if ($health_label) {
                echo '<span class="mh-ght-health ' . $health_class . '">' . $health_label . '</span>';
            }
            echo '</div>';
            if (!empty($tool['description'])) {
                echo '<p class="mh-ght-desc">' . esc_html(wp_trim_words($tool['description'], 20, '...')) . '</p>';
            }
            echo '<div class="mh-ght-metrics">';
            echo '<span class="mh-ght-rel ' . esc_attr($rel) . '">' . $rel_label . '</span>';
            if (!empty($tool['stars'])) {
                echo '<span>⭐ ' . number_format(intval($tool['stars'])) . '</span>';
            }
            if (!empty($tool['forks'])) {
                echo '<span>🍴 ' . number_format(intval($tool['forks'])) . '</span>';
            }
            if (!empty($tool['language'])) {
                echo '<span>📝 ' . esc_html($tool['language']) . '</span>';
            }
            echo '</div>';
            if (!empty($tool['topics']) && is_array($tool['topics'])) {
                echo '<div class="mh-ght-topics">';
                foreach (array_slice($tool['topics'], 0, 5) as $topic) {
                    echo '<span class="mh-ght-topic">' . esc_html($topic) . '</span>';
                }
                echo '</div>';
            }
            echo '</a>';
        }
        echo '</div>';
    } elseif (!empty($url)) {
        // Fallback: simple link card when no enriched tools available
        $repo_name = preg_replace('/^https?:\/\/(www\.)?github\.com\//', '', $url);
        $repo_name = rtrim($repo_name, '/');
        
        echo '<a href="' . esc_url($url) . '" class="mh-github-card" target="_blank">';
        echo '<span class="mh-github-icon">🐙</span>';
        echo '<div class="mh-github-info">';
        echo '<strong>GitHub Repository</strong>';
        echo '<span>' . esc_html($repo_name) . '</span>';
        echo '</div>';
        echo '<span class="mh-github-arrow">→</span>';
        echo '</a>';
    }
    
    echo '</div>';
}

/**
 * Display data repositories section
 */
function mh_display_repositories($repositories = null) {
    if ($repositories === null) {
        $repositories = json_decode(get_post_meta(get_the_ID(), '_mh_repositories', true), true) ?: array();
    }
    
    if (empty($repositories)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>🗄️ Data Repositories</h2>';
    echo '<div class="mh-repo-list">';
    
    foreach ($repositories as $repo) {
        $url = isset($repo['url']) ? $repo['url'] : '#';
        
        // Handle both formats: name/type and id/identifier/accession_id
        $name = '';
        if (isset($repo['name']) && !empty($repo['name']) && strtolower($repo['name']) !== 'unknown') {
            $name = $repo['name'];
        } elseif (isset($repo['type']) && !empty($repo['type']) && strtolower($repo['type']) !== 'unknown') {
            $name = $repo['type'];
        }
        
        // If still no name (or was "Unknown"), detect from URL
        if (empty($name) && $url && $url !== '#') {
            if (strpos($url, 'zenodo') !== false) {
                $name = 'Zenodo';
            } elseif (strpos($url, 'figshare') !== false) {
                $name = 'Figshare';
            } elseif (strpos($url, 'github') !== false) {
                $name = 'GitHub';
            } elseif (strpos($url, 'dryad') !== false) {
                $name = 'Dryad';
            } elseif (strpos($url, 'osf.io') !== false) {
                $name = 'OSF';
            } elseif (strpos($url, 'dataverse') !== false) {
                $name = 'Dataverse';
            } elseif (strpos($url, 'mendeley') !== false) {
                $name = 'Mendeley Data';
            } elseif (strpos($url, 'synapse') !== false) {
                $name = 'Synapse';
            } elseif (strpos($url, 'ebi.ac.uk') !== false || strpos($url, 'empiar') !== false) {
                $name = 'EMPIAR';
            } elseif (strpos($url, 'ncbi') !== false || strpos($url, 'geo') !== false) {
                $name = 'GEO/NCBI';
            } elseif (strpos($url, 'arrayexpress') !== false) {
                $name = 'ArrayExpress';
            } elseif (strpos($url, 'proteomexchange') !== false || strpos($url, 'pride') !== false) {
                $name = 'ProteomeXchange';
            } else {
                $name = 'Data Repository';
            }
        }
        
        // Final fallback
        if (empty($name)) {
            $name = 'Data Repository';
        }
        
        // Get ID from various possible fields
        $id = '';
        if (isset($repo['id']) && !empty($repo['id'])) {
            $id = $repo['id'];
        } elseif (isset($repo['identifier']) && !empty($repo['identifier'])) {
            $id = $repo['identifier'];
        } elseif (isset($repo['accession_id']) && !empty($repo['accession_id'])) {
            $id = $repo['accession_id'];
        }
        
        echo '<a href="' . esc_url($url) . '" class="mh-repo-item" target="_blank">';
        echo esc_html($name);
        if ($id) {
            echo ' <span class="mh-repo-id">' . esc_html($id) . '</span>';
        }
        echo '</a>';
    }
    
    echo '</div>';
    echo '</div>';
}

/**
 * Display RRIDs section
 */
function mh_display_rrids($rrids = null) {
    if ($rrids === null) {
        $rrids = json_decode(get_post_meta(get_the_ID(), '_mh_rrids', true), true) ?: array();
    }
    
    if (empty($rrids)) return;
    
    echo '<div class="mh-rrid-list">';
    foreach ($rrids as $rrid) {
        $rrid_clean = is_array($rrid) ? (isset($rrid['id']) ? $rrid['id'] : '') : $rrid;
        if ($rrid_clean) {
            echo '<a href="https://scicrunch.org/resolver/' . esc_attr($rrid_clean) . '" class="mh-rrid-tag" target="_blank">' . esc_html($rrid_clean) . '</a>';
        }
    }
    echo '</div>';
}

/**
 * Display RORs (Research Organization Registry identifiers)
 */
function mh_display_rors($rors = null) {
    if ($rors === null) {
        $rors = json_decode(get_post_meta(get_the_ID(), '_mh_rors', true), true) ?: array();
    }
    
    if (empty($rors)) return;
    
    echo '<div class="mh-ror-list">';
    foreach ($rors as $ror) {
        // Handle both object format and simple string format
        $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
        $ror_url = is_array($ror) ? ($ror['url'] ?? 'https://ror.org/' . $ror_id) : 'https://ror.org/' . $ror;
        
        if ($ror_id) {
            echo '<a href="' . esc_url($ror_url) . '" class="mh-ror-tag" target="_blank" rel="noopener">';
            echo '<span class="ror-icon">🏛️</span>';
            echo '<span class="ror-id">' . esc_html($ror_id) . '</span>';
            echo '</a>';
        }
    }
    echo '</div>';
}

/**
 * Get all tags for a paper (for highlighting in full text)
 * Checks ALL registered taxonomies + meta fields for complete coverage
 */
function mh_get_paper_tags($post_id = null) {
    if (!$post_id) $post_id = get_the_ID();
    
    $tags = array();
    $seen = array(); // Track duplicates by lowercase name
    
    // Map ALL taxonomies to CSS class types
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
    
    // Get terms from ALL taxonomies
    foreach ($taxonomy_to_css as $taxonomy => $css_type) {
        if (!taxonomy_exists($taxonomy)) continue;
        
        $terms = get_the_terms($post_id, $taxonomy);
        if ($terms && !is_wp_error($terms)) {
            foreach ($terms as $term) {
                $key = strtolower($term->name);
                if (isset($seen[$key])) continue;
                $seen[$key] = true;
                
                $tags[] = array(
                    'name' => $term->name,
                    'slug' => $term->slug,
                    'taxonomy' => $css_type,
                    'url' => get_term_link($term)
                );
            }
        }
    }
    
    // Also check meta fields (fallback for any missed data)
    $meta_to_css = array(
        '_mh_fluorophores'             => 'fluorophore',
        '_mh_cell_lines'               => 'cell_line',
        '_mh_sample_preparation'       => 'sample_prep',
        '_mh_microscope_brands'        => 'microscope',
        '_mh_microscope_models'        => 'microscope',
        '_mh_image_analysis_software'  => 'software',
        '_mh_image_acquisition_software' => 'software',
    );
    
    foreach ($meta_to_css as $meta_key => $css_type) {
        $values = json_decode(get_post_meta($post_id, $meta_key, true), true);
        if (!empty($values) && is_array($values)) {
            foreach ($values as $value) {
                if (!is_string($value)) continue;
                $key = strtolower($value);
                if (isset($seen[$key])) continue;
                $seen[$key] = true;
                
                $tags[] = array(
                    'name' => $value,
                    'slug' => sanitize_title($value),
                    'taxonomy' => $css_type,
                    'url' => null
                );
            }
        }
    }
    
    // Get RRIDs from meta (special object format)
    $rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true);
    if (!empty($rrids) && is_array($rrids)) {
        foreach ($rrids as $rrid) {
            if (is_array($rrid) && isset($rrid['id'])) {
                $key = strtolower($rrid['id']);
                if (isset($seen[$key])) continue;
                $seen[$key] = true;
                
                $tags[] = array(
                    'name' => $rrid['id'],
                    'slug' => sanitize_title($rrid['id']),
                    'taxonomy' => 'rrid',
                    'url' => isset($rrid['url']) ? $rrid['url'] : null
                );
            }
        }
    }
    
    // Get antibodies from meta (special object format)
    $antibodies = json_decode(get_post_meta($post_id, '_mh_antibodies', true), true);
    if (!empty($antibodies) && is_array($antibodies)) {
        foreach ($antibodies as $ab) {
            if (is_array($ab) && isset($ab['id'])) {
                $key = strtolower($ab['id']);
                if (isset($seen[$key])) continue;
                $seen[$key] = true;
                
                $tags[] = array(
                    'name' => $ab['id'],
                    'slug' => sanitize_title($ab['id']),
                    'taxonomy' => 'antibody',
                    'url' => isset($ab['url']) ? $ab['url'] : null
                );
            }
        }
    }
    
    return $tags;
}

/**
 * Highlight tags in text with clickable links
 */
function mh_highlight_tags_in_text($text, $tags) {
    if (empty($text) || empty($tags)) return $text;
    
    // Sort tags by length (longest first) to avoid partial matches
    usort($tags, function($a, $b) {
        return strlen($b['name']) - strlen($a['name']);
    });
    
    // Two-pass system: first replace with placeholders, then replace placeholders with HTML
    $placeholders = array();
    
    foreach ($tags as $tag) {
        $name = $tag['name'];
        // Skip very short tags that might cause false positives
        if (strlen($name) < 3) continue;
        
        // Create unique placeholder
        $placeholder = '___MHTAG_' . md5($name . $tag['taxonomy']) . '___';
        
        // Determine tag class based on taxonomy type
        $type = $tag['taxonomy'];
        $class = 'mh-text-tag mh-text-tag-' . $type;
        
        // Create the HTML replacement (NO URL to avoid nested replacement issues)
        $html = '<span class="' . esc_attr($class) . '">' . esc_html($name) . '</span>';
        
        // Store placeholder mapping
        $placeholders[$placeholder] = $html;
        
        // Replace tag name with placeholder (word boundary match)
        $pattern = '/\b' . preg_quote($name, '/') . '\b/i';
        $text = preg_replace($pattern, $placeholder, $text, 1); // Only replace first occurrence per tag
    }
    
    // Second pass: replace all placeholders with actual HTML
    foreach ($placeholders as $placeholder => $html) {
        $text = str_replace($placeholder, $html, $text);
    }
    
    return $text;
}

/**
 * Display abstract with tag highlighting
 * This replaces the full text display - now shows abstract with highlighted tags
 */
function mh_display_abstract_with_tags($post_id = null) {
    if (!$post_id) $post_id = get_the_ID();
    
    $abstract = get_post_meta($post_id, '_mh_abstract', true);
    if (empty($abstract)) return;
    
    // Clean any garbage text from scraped data
    $garbage_patterns = array(
        '/^Technique\s+Microscope\s+Organism\s+Software\s*/i',
        '/Technique\s+Microscope\s+Organism\s+Software\s*/i',
        '/^pmc-status-\S+\s*/i',
        '/^pmc-prop-\S+\s*/i',
        '/pmc-status-\S+/i',
        '/pmc-prop-\S+/i',
    );
    foreach ($garbage_patterns as $pattern) {
        $abstract = preg_replace($pattern, '', $abstract);
    }
    $abstract = trim($abstract);
    
    if (empty($abstract)) return;
    
    // Get tags for highlighting
    $tags = mh_get_paper_tags($post_id);
    
    // Highlight tags in abstract
    $highlighted_abstract = mh_highlight_tags_in_text(esc_html($abstract), $tags);
    
    // Add tag legend if there are highlighted tags
    $has_tags = !empty($tags);
    
    ?>
    <section class="mh-paper-section mh-abstract-section">
        <div class="mh-abstract-header">
            <h2>📝 Abstract</h2>
            <?php if ($has_tags): ?>
            <div class="mh-tag-legend">
                <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-technique">Technique</span></span>
                <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-microscope">Microscope</span></span>
                <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-organism">Organism</span></span>
                <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-software">Software</span></span>
                <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-fluorophore">Fluorophore</span></span>
            </div>
            <?php endif; ?>
        </div>
        <div class="mh-abstract-content">
            <p><?php echo $highlighted_abstract; ?></p>
        </div>
    </section>
    <?php
}

/**
 * Link reference citations in text to reference list
 * Handles formats: [1], [1,2], [1-3], (Smith et al., 2020), etc.
 */
function mh_link_references_in_text($text, $references) {
    if (empty($text) || empty($references)) return $text;
    
    // Build reference lookup by number
    $ref_lookup = array();
    foreach ($references as $idx => $ref) {
        $num = isset($ref['num']) ? $ref['num'] : ($idx + 1);
        $ref_lookup[$num] = $idx;
    }
    
    // Link numbered citations like [1], [2,3], [1-5]
    $text = preg_replace_callback(
        '/\[(\d+(?:\s*[-,]\s*\d+)*)\]/',
        function($matches) use ($ref_lookup) {
            $nums = $matches[1];
            $parts = preg_split('/\s*[,]\s*/', $nums);
            $linked_parts = array();
            
            foreach ($parts as $part) {
                // Handle ranges like 1-5
                if (preg_match('/(\d+)\s*-\s*(\d+)/', $part, $range)) {
                    $range_links = array();
                    for ($i = intval($range[1]); $i <= intval($range[2]); $i++) {
                        if (isset($ref_lookup[$i])) {
                            $range_links[] = '<a href="#ref-' . $i . '" class="mh-ref-link">' . $i . '</a>';
                        } else {
                            $range_links[] = $i;
                        }
                    }
                    $linked_parts[] = implode('-', $range_links);
                } else {
                    $num = intval($part);
                    if (isset($ref_lookup[$num])) {
                        $linked_parts[] = '<a href="#ref-' . $num . '" class="mh-ref-link">' . $num . '</a>';
                    } else {
                        $linked_parts[] = $num;
                    }
                }
            }
            
            return '[' . implode(', ', $linked_parts) . ']';
        },
        $text
    );
    
    // Link superscript citations like ¹, ², ¹⁻³
    $superscripts = array('⁰'=>0, '¹'=>1, '²'=>2, '³'=>3, '⁴'=>4, '⁵'=>5, '⁶'=>6, '⁷'=>7, '⁸'=>8, '⁹'=>9);
    $text = preg_replace_callback(
        '/([⁰¹²³⁴⁵⁶⁷⁸⁹]+)/',
        function($matches) use ($ref_lookup, $superscripts) {
            $super = $matches[1];
            $num = '';
            foreach (mb_str_split($super) as $char) {
                if (isset($superscripts[$char])) {
                    $num .= $superscripts[$char];
                }
            }
            $num = intval($num);
            if (isset($ref_lookup[$num])) {
                return '<a href="#ref-' . $num . '" class="mh-ref-link mh-ref-super">' . $super . '</a>';
            }
            return $super;
        },
        $text
    );
    
    return $text;
}

/**
 * Display full text section with highlighted tags and linked references
 * Splits content into collapsible section boxes
 */
function mh_display_full_text($post_id = null) {
    if (!$post_id) $post_id = get_the_ID();
    
    $full_text = get_post_meta($post_id, '_mh_full_text', true);
    if (empty($full_text)) return;
    
    // IMMEDIATELY clean garbage text from scraped data
    $garbage_patterns = array(
        '/^Technique\s+Microscope\s+Organism\s+Software\s*/i',
        '/Technique\s+Microscope\s+Organism\s+Software\s*/i',  // Also remove if not at start
        '/^pmc-status-\S+\s*/i',
        '/^pmc-prop-\S+\s*/i',
        '/pmc-status-\S+/i',
        '/pmc-prop-\S+/i',
    );
    foreach ($garbage_patterns as $pattern) {
        $full_text = preg_replace($pattern, '', $full_text);
    }
    $full_text = trim($full_text);
    
    // Get tags and references
    $tags = mh_get_paper_tags($post_id);
    $references = json_decode(get_post_meta($post_id, '_mh_references', true), true);
    if (!is_array($references)) $references = array();
    
    // Section definitions with icons
    $section_defs = array(
        'Abstract' => array('icon' => '📝', 'color' => 'purple'),
        'Summary' => array('icon' => '📝', 'color' => 'purple'),
        'Introduction' => array('icon' => '📖', 'color' => 'blue'),
        'Background' => array('icon' => '📖', 'color' => 'blue'),
        'Methods' => array('icon' => '🔬', 'color' => 'green'),
        'Materials and Methods' => array('icon' => '🔬', 'color' => 'green'),
        'Material and methods' => array('icon' => '🔬', 'color' => 'green'),
        'Experimental' => array('icon' => '🔬', 'color' => 'green'),
        'Results' => array('icon' => '📊', 'color' => 'orange'),
        'Discussion' => array('icon' => '💬', 'color' => 'yellow'),
        'Conclusion' => array('icon' => '✅', 'color' => 'teal'),
        'Conclusions' => array('icon' => '✅', 'color' => 'teal'),
        'Acknowledgements' => array('icon' => '🙏', 'color' => 'gray'),
        'Acknowledgments' => array('icon' => '🙏', 'color' => 'gray'),
        'References' => array('icon' => '📚', 'color' => 'gray'),
        'Data Availability' => array('icon' => '📁', 'color' => 'gray'),
        'Author Contributions' => array('icon' => '👥', 'color' => 'gray'),
        'Funding' => array('icon' => '💰', 'color' => 'gray'),
        'Supplementary' => array('icon' => '📎', 'color' => 'gray'),
    );
    
    // First, try to add line breaks before section headers if they're inline
    // This handles text like "...end of intro. Methods The methods section..."
    $header_names = array_keys($section_defs);
    foreach ($header_names as $header) {
        // Add line breaks before/after section headers that appear inline
        // Look for patterns like: ". Methods " or ") Results " (punctuation + Header + space)
        $full_text = preg_replace(
            '/([.!?)]\s*)(' . preg_quote($header, '/') . ')(\s+[A-Z])/i',
            "$1\n\n$2\n\n$3",
            $full_text
        );
    }
    
    // Build regex pattern for all section headers (now on their own lines)
    $pattern = '/^(' . implode('|', array_map('preg_quote', $header_names)) . ')\s*$/mi';
    
    // Split text by section headers
    $parts = preg_split($pattern, $full_text, -1, PREG_SPLIT_DELIM_CAPTURE);
    
    // Build sections array
    $sections = array();
    $current_section = null;
    
    for ($i = 0; $i < count($parts); $i++) {
        $part = trim($parts[$i]);
        if (empty($part)) continue;
        
        // Check if this part is a header
        $is_header = false;
        foreach ($header_names as $header) {
            if (strcasecmp($part, $header) === 0) {
                $is_header = true;
                $current_section = $header;
                if (!isset($sections[$header])) {
                    $sections[$header] = array(
                        'title' => $header,
                        'icon' => $section_defs[$header]['icon'],
                        'color' => $section_defs[$header]['color'],
                        'content' => ''
                    );
                }
                break;
            }
        }
        
        if (!$is_header) {
            if ($current_section !== null) {
                $sections[$current_section]['content'] .= $part;
            } else {
                // Content before first header
                if (!isset($sections['_intro'])) {
                    $sections = array_merge(array('_intro' => array(
                        'title' => 'Overview',
                        'icon' => '📄',
                        'color' => 'blue',
                        'content' => ''
                    )), $sections);
                }
                $sections['_intro']['content'] .= $part;
            }
        }
    }
    
    // If no sections found, show as single block
    if (empty($sections)) {
        $sections['_full'] = array(
            'title' => 'Full Text',
            'icon' => '📄',
            'color' => 'blue',
            'content' => $full_text
        );
    }
    
    // Remove References section if we have parsed references
    if (!empty($references) && isset($sections['References'])) {
        unset($sections['References']);
    }
    
    ?>
    <section class="mh-paper-section mh-full-text-section">
        <div class="mh-full-text-header">
            <h2>📄 Full Text</h2>
            <div class="mh-full-text-controls">
                <button type="button" class="mh-btn mh-btn-sm" id="mh-toggle-highlights">
                    <span class="highlight-on">Hide Highlights</span>
                    <span class="highlight-off" style="display:none;">Show Highlights</span>
                </button>
                <button type="button" class="mh-btn mh-btn-sm" id="mh-expand-all">
                    <span class="expand-text">Expand All</span>
                    <span class="collapse-text" style="display:none;">Collapse All</span>
                </button>
            </div>
        </div>
        
        <div class="mh-tag-legend">
            <span class="mh-legend-label">Tags:</span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-technique">Technique</span></span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-microscope">Microscope</span></span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-organism">Organism</span></span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-software">Software</span></span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-fluorophore">Fluorophore</span></span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-cell_line">Cell Line</span></span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-sample_prep">Sample Prep</span></span>
            <span class="mh-legend-item"><span class="mh-text-tag mh-text-tag-microscope_brand">Brand</span></span>
        </div>
        
        <div class="mh-sections-wrapper" id="mh-full-text-content">
            <?php foreach ($sections as $key => $section) : 
                if (empty(trim($section['content']))) continue;
                
                // Process content - create proper paragraphs
                $raw_content = trim($section['content']);
                $content = esc_html($raw_content);
                
                // Detect paragraph breaks: 
                // - Double newlines
                // - Period followed by 2+ spaces and capital letter (sentence boundaries that are actually paragraphs)
                // - Common section starters
                $content = preg_replace('/\n\s*\n/', "\n\n", $content); // Normalize double newlines
                
                // Split into paragraphs
                $paragraphs = preg_split('/\n\n+/', $content);
                $processed_paragraphs = array();
                
                foreach ($paragraphs as $para) {
                    $para = trim($para);
                    if (empty($para)) continue;
                    
                    // Apply highlighting and linking
                    $para = mh_highlight_tags_in_text($para, $tags);
                    $para = mh_link_references_in_text($para, $references);
                    
                    // Wrap in paragraph tag
                    $processed_paragraphs[] = '<p class="mh-paragraph">' . $para . '</p>';
                }
                
                $content = implode("\n", $processed_paragraphs);
                
                // If no paragraphs detected, just process the whole thing
                if (empty($processed_paragraphs)) {
                    $content = esc_html($section['content']);
                    $content = nl2br($content);
                    $content = mh_highlight_tags_in_text($content, $tags);
                    $content = mh_link_references_in_text($content, $references);
                }
                
                $section_id = sanitize_title($section['title']);
            ?>
            <div class="mh-text-section mh-section-<?php echo esc_attr($section['color']); ?>" id="section-<?php echo esc_attr($section_id); ?>">
                <div class="mh-text-section-header" data-toggle="section">
                    <span class="mh-section-icon"><?php echo $section['icon']; ?></span>
                    <h3><?php echo esc_html($section['title']); ?></h3>
                    <span class="mh-section-arrow">▼</span>
                </div>
                <div class="mh-text-section-body">
                    <?php echo $content; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </section>
    <?php
}

/**
 * Display references section
 */
function mh_display_references($post_id = null) {
    if (!$post_id) $post_id = get_the_ID();
    
    $references = json_decode(get_post_meta($post_id, '_mh_references', true), true) ?: array();
    if (empty($references)) return;
    
    ?>
    <section class="mh-paper-section mh-references-section">
        <h2>📚 References</h2>
        <ol class="mh-reference-list">
            <?php foreach ($references as $idx => $ref) : 
                $num = isset($ref['num']) ? $ref['num'] : ($idx + 1);
                $text = isset($ref['text']) ? $ref['text'] : '';
                $doi = isset($ref['doi']) ? $ref['doi'] : '';
                $pmid = isset($ref['pmid']) ? $ref['pmid'] : '';
                $url = isset($ref['url']) ? $ref['url'] : '';
                
                // Build link
                $link = '';
                if ($doi) {
                    $link = 'https://doi.org/' . $doi;
                } elseif ($pmid) {
                    $link = 'https://pubmed.ncbi.nlm.nih.gov/' . $pmid;
                } elseif ($url) {
                    $link = $url;
                }
            ?>
                <li id="ref-<?php echo esc_attr($num); ?>" class="mh-reference-item">
                    <span class="mh-ref-text"><?php echo esc_html($text); ?></span>
                    <?php if ($link) : ?>
                        <a href="<?php echo esc_url($link); ?>" class="mh-ref-external-link" target="_blank" rel="noopener">
                            <?php if ($doi) : ?>
                                <span class="mh-ref-doi">DOI</span>
                            <?php elseif ($pmid) : ?>
                                <span class="mh-ref-pmid">PubMed</span>
                            <?php else : ?>
                                <span class="mh-ref-link-icon">🔗</span>
                            <?php endif; ?>
                        </a>
                    <?php endif; ?>
                </li>
            <?php endforeach; ?>
        </ol>
    </section>
    <?php
}
function mh_display_facility($facility = null) {
    $post_id = get_the_ID();
    
    // Get institutions (new field) or fall back to facility (old field)
    $institutions = json_decode(get_post_meta($post_id, '_mh_institutions', true), true);
    if (empty($institutions)) {
        $institutions = json_decode(get_post_meta($post_id, '_mh_facilities', true), true);
    }
    if (empty($institutions) && $facility) {
        $institutions = is_array($facility) ? $facility : [$facility];
    }
    if (empty($institutions)) {
        $facility = get_post_meta($post_id, '_mh_facility', true);
        if ($facility) {
            $institutions = [$facility];
        }
    }
    
    if (empty($institutions)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>🏛️ Research Institutions</h2>';
    echo '<div class="mh-institutions-list">';
    foreach ($institutions as $institution) {
        if (empty($institution)) continue;
        echo '<div class="mh-institution-card">';
        echo '<span class="mh-institution-icon">🏛️</span>';
        echo '<span class="mh-institution-name">' . esc_html($institution) . '</span>';
        echo '</div>';
    }
    echo '</div>';
    echo '</div>';
}

/**
 * Display fluorophores section
 */
function mh_display_fluorophores($fluorophores = null) {
    if ($fluorophores === null) {
        $fluorophores = json_decode(get_post_meta(get_the_ID(), '_mh_fluorophores', true), true) ?: array();
    }
    
    if (empty($fluorophores)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>🔬 Fluorophores &amp; Dyes</h2>';
    echo '<div class="mh-tag-cloud mh-fluorophores">';
    foreach ($fluorophores as $fluor) {
        $class = 'mh-fluor-tag';
        // Color code by type
        if (preg_match('/gfp|egfp|green|neon|clover|emerald/i', $fluor)) {
            $class .= ' mh-fluor-green';
        } elseif (preg_match('/mcherry|rfp|tomato|dsred|mruby|scarlet|red/i', $fluor)) {
            $class .= ' mh-fluor-red';
        } elseif (preg_match('/cfp|cerulean|turquoise|cyan/i', $fluor)) {
            $class .= ' mh-fluor-cyan';
        } elseif (preg_match('/yfp|venus|citrine|yellow/i', $fluor)) {
            $class .= ' mh-fluor-yellow';
        } elseif (preg_match('/bfp|blue|dapi|hoechst/i', $fluor)) {
            $class .= ' mh-fluor-blue';
        } elseif (preg_match('/alexa|647|cy5|far.?red|infrared|irfp/i', $fluor)) {
            $class .= ' mh-fluor-farred';
        } elseif (preg_match('/gcamp|calcium|camp|geco/i', $fluor)) {
            $class .= ' mh-fluor-indicator';
        }
        echo '<span class="' . esc_attr($class) . '">' . esc_html($fluor) . '</span>';
    }
    echo '</div>';
    echo '</div>';
}

/**
 * Display sample preparation section
 */
function mh_display_sample_preparation($sample_prep = null) {
    if ($sample_prep === null) {
        $sample_prep = json_decode(get_post_meta(get_the_ID(), '_mh_sample_preparation', true), true) ?: array();
    }
    
    if (empty($sample_prep)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>🧪 Sample Preparation</h2>';
    echo '<div class="mh-tag-cloud mh-sample-prep">';
    foreach ($sample_prep as $prep) {
        $class = 'mh-prep-tag';
        // Categorize by type
        if (preg_match('/clarity|disco|cubic|clearing/i', $prep)) {
            $class .= ' mh-prep-clearing';
        } elseif (preg_match('/section|microtome|cryostat/i', $prep)) {
            $class .= ' mh-prep-sectioning';
        } elseif (preg_match('/culture|organoid|spheroid/i', $prep)) {
            $class .= ' mh-prep-culture';
        } elseif (preg_match('/transfect|transduc|viral|aav|lenti/i', $prep)) {
            $class .= ' mh-prep-genetic';
        } elseif (preg_match('/fish|rnascope|hybrid/i', $prep)) {
            $class .= ' mh-prep-fish';
        }
        echo '<span class="' . esc_attr($class) . '">' . esc_html($prep) . '</span>';
    }
    echo '</div>';
    echo '</div>';
}

/**
 * Display cell lines section
 */
function mh_display_cell_lines($cell_lines = null) {
    if ($cell_lines === null) {
        $cell_lines = json_decode(get_post_meta(get_the_ID(), '_mh_cell_lines', true), true) ?: array();
    }
    
    if (empty($cell_lines)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>🧫 Cell Lines</h2>';
    echo '<div class="mh-tag-cloud mh-cell-lines">';
    foreach ($cell_lines as $cell) {
        echo '<span class="mh-cell-tag">' . esc_html($cell) . '</span>';
    }
    echo '</div>';
    echo '</div>';
}

/**
 * Display figures section
 */
function mh_display_figures($figures = null) {
    if ($figures === null) {
        $figures = json_decode(get_post_meta(get_the_ID(), '_mh_figures', true), true) ?: array();
    }
    
    if (empty($figures)) return;
    
    echo '<div class="mh-paper-section mh-figures-section">';
    echo '<h2>📊 Figures</h2>';
    echo '<div class="mh-figures-grid">';
    
    foreach ($figures as $index => $fig) {
        $label = isset($fig['label']) ? $fig['label'] : 'Figure ' . ($index + 1);
        $title = isset($fig['title']) ? $fig['title'] : '';
        $caption = isset($fig['caption']) ? $fig['caption'] : '';
        $image_url = isset($fig['image_url']) ? $fig['image_url'] : '';
        
        echo '<div class="mh-figure-card">';
        
        if ($image_url) {
            echo '<div class="mh-figure-image">';
            echo '<a href="' . esc_url($image_url) . '" target="_blank">';
            echo '<img src="' . esc_url($image_url) . '" alt="' . esc_attr($label) . '" loading="lazy">';
            echo '</a>';
            echo '</div>';
        }
        
        echo '<div class="mh-figure-content">';
        echo '<h4 class="mh-figure-label">' . esc_html($label) . '</h4>';
        if ($title) {
            echo '<p class="mh-figure-title">' . esc_html($title) . '</p>';
        }
        if ($caption) {
            $caption_short = strlen($caption) > 200 ? substr($caption, 0, 200) . '...' : $caption;
            echo '<p class="mh-figure-caption">' . esc_html($caption_short) . '</p>';
        }
        echo '</div>';
        
        echo '</div>';
    }
    
    echo '</div>';
    echo '</div>';
}

/**
 * Display methods section
 */
function mh_display_methods($methods = null) {
    if ($methods === null) {
        $methods = get_post_meta(get_the_ID(), '_mh_methods', true);
    }
    
    if (empty($methods)) return;
    
    echo '<div class="mh-paper-section mh-methods-section">';
    echo '<h2>📋 Methods</h2>';
    echo '<div class="mh-methods-content">';
    
    // If methods is very long, show excerpt with expand option
    if (strlen($methods) > 2000) {
        $excerpt = substr($methods, 0, 1500);
        $excerpt = substr($excerpt, 0, strrpos($excerpt, ' ')); // End on word boundary
        
        echo '<div class="mh-methods-excerpt">' . nl2br(esc_html($excerpt)) . '...</div>';
        echo '<details class="mh-methods-full">';
        echo '<summary>Show full methods section</summary>';
        echo '<div class="mh-methods-text">' . nl2br(esc_html($methods)) . '</div>';
        echo '</details>';
    } else {
        echo '<div class="mh-methods-text">' . nl2br(esc_html($methods)) . '</div>';
    }
    
    echo '</div>';
    echo '</div>';
}

/**
 * Display microscope equipment section
 */
function mh_display_equipment($meta = null) {
    if ($meta === null) {
        $meta = mh_get_paper_meta();
    }
    
    $brands = isset($meta['microscope_brands']) ? $meta['microscope_brands'] : array();
    $models = isset($meta['microscope_models']) ? $meta['microscope_models'] : array();
    $details = isset($meta['microscope_details']) ? $meta['microscope_details'] : '';
    
    if (empty($brands) && empty($models) && empty($details)) return;
    
    echo '<div class="mh-paper-section">';
    echo '<h2>🔬 Microscope Equipment</h2>';
    
    if (!empty($brands)) {
        echo '<div class="mh-equipment-brands">';
        echo '<strong>Brands:</strong> ';
        echo '<span class="mh-tag-cloud">';
        foreach ($brands as $brand) {
            echo '<span class="mh-brand-tag">' . esc_html($brand) . '</span>';
        }
        echo '</span>';
        echo '</div>';
    }
    
    if (!empty($models)) {
        echo '<div class="mh-equipment-models">';
        echo '<strong>Models:</strong> ';
        echo '<span class="mh-tag-cloud">';
        foreach ($models as $model) {
            echo '<span class="mh-model-tag">' . esc_html($model) . '</span>';
        }
        echo '</span>';
        echo '</div>';
    }
    
    if ($details) {
        echo '<div class="mh-equipment-details">';
        echo '<p>' . esc_html($details) . '</p>';
        echo '</div>';
    }
    
    echo '</div>';
}

/**
 * Display acquisition software section
 */
function mh_display_acquisition_software($software = null) {
    if ($software === null) {
        $software = json_decode(get_post_meta(get_the_ID(), '_mh_image_acquisition_software', true), true) ?: array();
    }
    
    if (empty($software)) return;
    
    echo '<div class="mh-software-section">';
    echo '<strong>Acquisition:</strong> ';
    foreach ($software as $sw) {
        echo '<span class="mh-software-tag mh-acq-software">' . esc_html($sw) . '</span>';
    }
    echo '</div>';
}

/**
 * Display analysis software section
 */
function mh_display_analysis_software($software = null) {
    if ($software === null) {
        $software = json_decode(get_post_meta(get_the_ID(), '_mh_image_analysis_software', true), true) ?: array();
    }
    
    if (empty($software)) return;
    
    echo '<div class="mh-software-section">';
    echo '<strong>Analysis:</strong> ';
    foreach ($software as $sw) {
        echo '<span class="mh-software-tag mh-analysis-software">' . esc_html($sw) . '</span>';
    }
    echo '</div>';
}

/**
 * Get page URLs for navigation
 */
function mh_get_page_urls() {
    return array(
        'papers' => get_post_type_archive_link('mh_paper') ?: home_url('/papers/'),
        'protocols' => home_url('/protocols/'),
        'github_tools' => get_page_by_path('github-tools') ? get_permalink(get_page_by_path('github-tools')) : home_url('/github-tools/'),
        'discussions' => get_page_by_path('discussions') ? get_permalink(get_page_by_path('discussions')) : home_url('/discussions/'),
        'about' => get_page_by_path('about') ? get_permalink(get_page_by_path('about')) : home_url('/about/'),
        'contact' => get_page_by_path('contact') ? get_permalink(get_page_by_path('contact')) : home_url('/contact/')
    );
}

/**
 * Get database statistics
 */
function mh_get_stats() {
    $stats = array(
        'papers' => 0,
        'techniques' => 0,
        'microscopes' => 0,
        'software' => 0,
        'organisms' => 0,
        'with_protocols' => 0,
        'with_github' => 0,
        'with_repositories' => 0,
        'with_rrids' => 0,
        'with_figures' => 0,
        'with_full_text' => 0,
        'with_fluorophores' => 0
    );
    
    // Check if plugin is active
    if (!mh_plugin_active()) {
        return $stats;
    }
    
    $paper_counts = wp_count_posts('mh_paper');
    $stats['papers'] = isset($paper_counts->publish) ? $paper_counts->publish : 0;
    
    // Taxonomy counts - check if taxonomy exists first
    if (taxonomy_exists('mh_technique')) {
        $count = wp_count_terms(array('taxonomy' => 'mh_technique', 'hide_empty' => false));
        $stats['techniques'] = is_wp_error($count) ? 0 : $count;
    }
    if (taxonomy_exists('mh_microscope')) {
        $count = wp_count_terms(array('taxonomy' => 'mh_microscope', 'hide_empty' => false));
        $stats['microscopes'] = is_wp_error($count) ? 0 : $count;
    }
    if (taxonomy_exists('mh_software')) {
        $count = wp_count_terms(array('taxonomy' => 'mh_software', 'hide_empty' => false));
        $stats['software'] = is_wp_error($count) ? 0 : $count;
    }
    if (taxonomy_exists('mh_organism')) {
        $count = wp_count_terms(array('taxonomy' => 'mh_organism', 'hide_empty' => false));
        $stats['organisms'] = is_wp_error($count) ? 0 : $count;
    }
    
    // Count papers with protocols - includes BOTH protocol URLs AND papers from protocol journals
    global $wpdb;
    $protocols_count = $wpdb->get_var(
        "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} 
         WHERE meta_key = '_mh_has_protocols' 
         AND meta_value = '1'"
    );
    $stats['with_protocols'] = intval($protocols_count);
    
    // Count papers with GitHub - use direct SQL
    $github_count = $wpdb->get_var(
        "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} 
         WHERE meta_key = '_mh_github_url' 
         AND meta_value != '' 
         AND meta_value IS NOT NULL"
    );
    $stats['with_github'] = intval($github_count);
    
    // Count papers with data repositories - use direct SQL
    $repos_count = $wpdb->get_var(
        "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} 
         WHERE meta_key = '_mh_repositories' 
         AND meta_value != '' 
         AND meta_value != '[]'
         AND meta_value IS NOT NULL"
    );
    $stats['with_repositories'] = intval($repos_count);
    
    // Count papers with RRIDs
    $rrids_count = $wpdb->get_var(
        "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} 
         WHERE meta_key = '_mh_rrids' 
         AND meta_value != '' 
         AND meta_value != '[]'
         AND meta_value IS NOT NULL"
    );
    $stats['with_rrids'] = intval($rrids_count);
    
    // Count papers with figures
    $figures_count = $wpdb->get_var(
        "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} 
         WHERE meta_key = '_mh_figures' 
         AND meta_value != '' 
         AND meta_value != '[]'
         AND meta_value IS NOT NULL"
    );
    $stats['with_figures'] = intval($figures_count);
    
    // Full text no longer stored - always 0
    $stats['with_full_text'] = 0;
    
    // Count papers with fluorophores
    $fluor_count = $wpdb->get_var(
        "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} 
         WHERE meta_key = '_mh_fluorophores' 
         AND meta_value != '' 
         AND meta_value != '[]'
         AND meta_value IS NOT NULL"
    );
    $stats['with_fluorophores'] = intval($fluor_count);
    
    return $stats;
}

/**
 * Get unique values from a JSON meta field for filter dropdowns
 * Returns array of value => count pairs sorted by count descending
 */
function mh_get_meta_filter_options($meta_key, $limit = 50) {
    global $wpdb;
    
    // Get all non-empty values for this meta key
    $results = $wpdb->get_col($wpdb->prepare(
        "SELECT meta_value FROM {$wpdb->postmeta} pm
         INNER JOIN {$wpdb->posts} p ON pm.post_id = p.ID
         WHERE pm.meta_key = %s 
         AND pm.meta_value != '' 
         AND pm.meta_value != '[]'
         AND pm.meta_value IS NOT NULL
         AND p.post_status = 'publish'
         AND p.post_type = 'mh_paper'",
        $meta_key
    ));
    
    if (empty($results)) {
        return array();
    }
    
    // Parse JSON and count occurrences
    $counts = array();
    foreach ($results as $json_value) {
        $values = json_decode($json_value, true);
        if (is_array($values)) {
            foreach ($values as $value) {
                if (is_string($value) && !empty(trim($value))) {
                    $clean_value = trim($value);
                    if (!isset($counts[$clean_value])) {
                        $counts[$clean_value] = 0;
                    }
                    $counts[$clean_value]++;
                }
            }
        }
    }
    
    // Sort by count descending
    arsort($counts);
    
    // Limit results
    return array_slice($counts, 0, $limit, true);
}

/**
 * Get all filter options for the front page (cached)
 */
function mh_get_all_filter_options() {
    // Try cache first
    $cache_key = 'mh_filter_options';
    $cached = get_transient($cache_key);
    if ($cached !== false) {
        return $cached;
    }
    
    $options = array(
        'fluorophores' => mh_get_meta_filter_options('_mh_fluorophores', 100),
        'sample_preparation' => mh_get_meta_filter_options('_mh_sample_preparation', 50),
        'cell_lines' => mh_get_meta_filter_options('_mh_cell_lines', 50),
        'microscope_brands' => mh_get_meta_filter_options('_mh_microscope_brands', 30),
        'microscope_models' => mh_get_meta_filter_options('_mh_microscope_models', 50),
        'image_analysis_software' => mh_get_meta_filter_options('_mh_image_analysis_software', 50),
        'image_acquisition_software' => mh_get_meta_filter_options('_mh_image_acquisition_software', 30),
    );
    
    // Cache for 1 hour
    set_transient($cache_key, $options, HOUR_IN_SECONDS);
    
    return $options;
}

/**
 * Format number with K/M suffix
 */
function mh_format_number($num) {
    if ($num >= 1000000) {
        return round($num / 1000000, 1) . 'M';
    } elseif ($num >= 1000) {
        return round($num / 1000, 1) . 'K';
    }
    return number_format($num);
}

/**
 * Truncate text
 */
function mh_truncate_text($text, $words = 30) {
    return wp_trim_words($text, $words, '...');
}

/**
 * Parse authors string and return array of individual authors
 */
function mh_parse_authors($authors_string) {
    if (empty($authors_string)) return array();
    
    // Common separators: comma, semicolon, " and ", "&"
    // First replace " and " and "&" with comma
    $normalized = preg_replace('/\s+and\s+|\s*&\s*/i', ', ', $authors_string);
    
    // Split by comma or semicolon
    $authors = preg_split('/[,;]\s*/', $normalized);
    
    // Clean up each author name
    $authors = array_map('trim', $authors);
    $authors = array_filter($authors, function($a) {
        return !empty($a) && strlen($a) > 1;
    });
    
    return array_values($authors);
}

/**
 * Get the last author from authors string
 */
function mh_get_last_author($authors_string) {
    $authors = mh_parse_authors($authors_string);
    if (empty($authors)) return '';
    return end($authors);
}

/**
 * Get the first author from authors string
 */
function mh_get_first_author($authors_string) {
    $authors = mh_parse_authors($authors_string);
    if (empty($authors)) return '';
    return reset($authors);
}

/**
 * Generate author search URL
 */
function mh_author_search_url($author_name) {
    return add_query_arg(array(
        'post_type' => 'mh_paper',
        's' => $author_name,
        'search_field' => 'author'
    ), home_url('/'));
}

/**
 * Display clickable authors with links
 */
function mh_display_clickable_authors($authors_string, $max_display = 5, $show_last_author = true) {
    $authors = mh_parse_authors($authors_string);
    if (empty($authors)) return;
    
    $total = count($authors);
    $last_author = end($authors);
    
    echo '<div class="mh-authors-list">';
    
    if ($total <= $max_display) {
        // Show all authors
        foreach ($authors as $i => $author) {
            $is_last = ($author === $last_author);
            $class = $is_last ? 'mh-author-link mh-last-author' : 'mh-author-link';
            echo '<a href="' . esc_url(mh_author_search_url($author)) . '" class="' . $class . '">' . esc_html($author) . '</a>';
            if ($i < $total - 1) echo '<span class="mh-author-sep">, </span>';
        }
    } else {
        // Show first few + last author
        $display_count = $show_last_author ? $max_display - 1 : $max_display;
        for ($i = 0; $i < $display_count && $i < $total; $i++) {
            echo '<a href="' . esc_url(mh_author_search_url($authors[$i])) . '" class="mh-author-link">' . esc_html($authors[$i]) . '</a>';
            echo '<span class="mh-author-sep">, </span>';
        }
        
        $hidden_count = $total - $display_count - ($show_last_author ? 1 : 0);
        if ($hidden_count > 0) {
            echo '<span class="mh-authors-more">... +' . $hidden_count . ' more ... </span>';
        }
        
        if ($show_last_author && $last_author) {
            echo '<a href="' . esc_url(mh_author_search_url($last_author)) . '" class="mh-author-link mh-last-author">' . esc_html($last_author) . '</a>';
        }
    }
    
    echo '</div>';
}

/**
 * Get papers by author
 */
function mh_get_papers_by_author($author_name, $limit = 10) {
    if (empty($author_name)) return array();
    
    return new WP_Query(array(
        'post_type' => 'mh_paper',
        'posts_per_page' => $limit,
        'meta_query' => array(
            array(
                'key' => '_mh_authors',
                'value' => $author_name,
                'compare' => 'LIKE'
            )
        ),
        'meta_key' => '_mh_citation_count',
        'orderby' => 'meta_value_num',
        'order' => 'DESC'
    ));
}

// ============================================
// ============================================
// AI CHAT - USES COPILOT
// ============================================
// The theme uses Copilot for AI chat functionality
// Configure in MicroHub plugin settings (MicroHub → Settings)

/**
 * Check if Copilot is configured (uses plugin's setting)
 */
function mh_is_copilot_configured() {
    $copilot_url = get_option('microhub_copilot_bot_url', '');
    return !empty($copilot_url);
}

// Legacy function for backwards compatibility
function mh_is_gemini_configured() {
    return mh_is_copilot_configured();
}

// ============================================
// QUERY MODIFICATIONS
// ============================================

// Default sort papers by citation count
function mh_modify_paper_query($query) {
    if (!mh_plugin_active()) return;
    
    if (!is_admin() && $query->is_main_query()) {
        // Handle author search
        if (is_search() && isset($_GET['search_field']) && $_GET['search_field'] === 'author') {
            $query->set('post_type', 'mh_paper');
            $search_term = get_search_query();
            $query->set('s', ''); // Clear default search
            $query->set('meta_query', array(
                array(
                    'key' => '_mh_authors',
                    'value' => $search_term,
                    'compare' => 'LIKE'
                )
            ));
            $query->set('meta_key', '_mh_citation_count');
            $query->set('orderby', 'meta_value_num');
            $query->set('order', 'DESC');
        }
        
        // Default paper archive sort
        if (is_post_type_archive('mh_paper')) {
            if (!isset($_GET['orderby'])) {
                $query->set('meta_key', '_mh_citation_count');
                $query->set('orderby', 'meta_value_num');
                $query->set('order', 'DESC');
            }
        }
    }
}
add_action('pre_get_posts', 'mh_modify_paper_query');

// Contact form handler
function mh_handle_contact_form() {
    if (!isset($_POST['mh_contact_submit']) || !wp_verify_nonce($_POST['mh_contact_nonce'], 'mh_contact_action')) {
        return;
    }
    
    $name = sanitize_text_field($_POST['mh_name'] ?? '');
    $email = sanitize_email($_POST['mh_email'] ?? '');
    $subject = sanitize_text_field($_POST['mh_subject'] ?? '');
    $message = sanitize_textarea_field($_POST['mh_message'] ?? '');
    
    if (empty($name) || empty($email) || empty($message)) {
        return 'error';
    }
    
    $admin_email = get_option('admin_email');
    $email_subject = '[MicroHub Contact] ' . ($subject ?: 'New Message') . ' from ' . $name;
    $email_body = "Name: $name\nEmail: $email\nSubject: $subject\n\nMessage:\n$message";
    
    wp_mail($admin_email, $email_subject, $email_body, array("Reply-To: $email"));
    
    return 'success';
}

// ============================================
// PROTOCOL AND FACILITY HELPER FUNCTIONS
// ============================================

/**
 * Get recent protocol papers (papers from protocol journals like JoVE, Nature Protocols)
 * Checks both mh_protocol post type AND mh_protocol_type taxonomy
 */
function mh_get_recent_protocol_papers($limit = 8) {
    if (!mh_plugin_active()) return array();

    // Check cache first - 10 minute cache
    $cache_key = 'mh_recent_protocols_' . $limit;
    $cached = get_transient($cache_key);
    if ($cached !== false) {
        return $cached;
    }

    $protocol_papers = array();

    // First, try getting mh_protocol post type
    $protocols = get_posts(array(
        'post_type' => 'mh_protocol',
        'posts_per_page' => $limit,
        'post_status' => 'publish',
        'orderby' => 'date',
        'order' => 'DESC',
    ));
    
    foreach ($protocols as $post) {
        $protocol_type = '';
        $terms = get_the_terms($post->ID, 'mh_protocol_type');
        if ($terms && !is_wp_error($terms)) {
            $protocol_type = $terms[0]->name;
        }
        if (!$protocol_type) {
            $protocol_type = get_post_meta($post->ID, '_mh_protocol_type', true) ?: 'Protocol';
        }
        
        $protocol_papers[] = array(
            'id' => $post->ID,
            'title' => $post->post_title,
            'permalink' => get_permalink($post->ID),
            'source' => $protocol_type,
        );
    }
    
    // Also get papers with mh_protocol_type taxonomy (papers from protocol journals)
    if (count($protocol_papers) < $limit && taxonomy_exists('mh_protocol_type')) {
        $remaining = $limit - count($protocol_papers);
        $existing_ids = wp_list_pluck($protocol_papers, 'id');
        
        $papers_with_protocol_type = get_posts(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => $remaining,
            'post_status' => 'publish',
            'post__not_in' => $existing_ids ?: array(0),
            'tax_query' => array(
                array(
                    'taxonomy' => 'mh_protocol_type',
                    'operator' => 'EXISTS',
                ),
            ),
            'orderby' => 'date',
            'order' => 'DESC',
        ));
        
        foreach ($papers_with_protocol_type as $post) {
            $protocol_type = '';
            $terms = get_the_terms($post->ID, 'mh_protocol_type');
            if ($terms && !is_wp_error($terms)) {
                $protocol_type = $terms[0]->name;
            }
            if (!$protocol_type) {
                $protocol_type = get_post_meta($post->ID, '_mh_protocol_type', true) ?: 'Protocol';
            }
            
            $protocol_papers[] = array(
                'id' => $post->ID,
                'title' => $post->post_title,
                'permalink' => get_permalink($post->ID),
                'source' => $protocol_type,
            );
        }
    }
    
    // Fallback: check _mh_is_protocol meta
    if (count($protocol_papers) < $limit) {
        $remaining = $limit - count($protocol_papers);
        $existing_ids = wp_list_pluck($protocol_papers, 'id');
        
        $papers_with_flag = get_posts(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => $remaining,
            'post_status' => 'publish',
            'post__not_in' => $existing_ids ?: array(0),
            'meta_query' => array(
                array(
                    'key' => '_mh_is_protocol',
                    'value' => '1',
                    'compare' => '=',
                ),
            ),
            'orderby' => 'date',
            'order' => 'DESC',
        ));
        
        foreach ($papers_with_flag as $post) {
            $journal = get_post_meta($post->ID, '_mh_journal', true);
            $source = mh_detect_protocol_source($journal);
            
            $protocol_papers[] = array(
                'id' => $post->ID,
                'title' => $post->post_title,
                'permalink' => get_permalink($post->ID),
                'source' => $source ?: 'Protocol',
            );
        }
    }
    
    $result = array_slice($protocol_papers, 0, $limit);

    // Cache for 10 minutes
    set_transient($cache_key, $result, 10 * MINUTE_IN_SECONDS);

    return $result;
}

/**
 * Detect protocol source from journal name
 */
function mh_detect_protocol_source($journal) {
    if (empty($journal)) return '';
    $journal_lower = strtolower($journal);
    
    $mapping = array(
        'jove' => 'JoVE',
        'journal of visualized' => 'JoVE',
        'nature protocols' => 'Nature Protocols',
        'nat protoc' => 'Nature Protocols',
        'bio-protocol' => 'Bio-protocol',
        'star protocols' => 'STAR Protocols',
        'current protocols' => 'Current Protocols',
        'methods in molecular biology' => 'Methods Mol Biol',
        'cold spring harbor' => 'CSH Protocols',
        'methodsx' => 'MethodsX',
    );
    
    foreach ($mapping as $pattern => $source) {
        if (stripos($journal_lower, $pattern) !== false) {
            return $source;
        }
    }
    
    return '';
}

/**
 * Get facilities with paper counts
 */
/**
 * Get institutions (research organizations where papers originated)
 * Uses mh_facility taxonomy for backward compatibility
 */
function mh_get_institutions($limit = 10) {
    if (!mh_plugin_active()) return array();

    // Check cache first - 10 minute cache
    $cache_key = 'mh_institutions_' . $limit;
    $cached = get_transient($cache_key);
    if ($cached !== false) {
        return $cached;
    }

    $institutions = array();

    // First try to get from taxonomy (uses mh_facility for backward compatibility)
    if (taxonomy_exists('mh_facility')) {
        $terms = get_terms(array(
            'taxonomy' => 'mh_facility',
            'orderby' => 'count',
            'order' => 'DESC',
            'number' => $limit,
            'hide_empty' => true,
        ));
        
        if (!is_wp_error($terms) && !empty($terms)) {
            foreach ($terms as $term) {
                // Get website URL from term meta if available
                $website = get_term_meta($term->term_id, 'institution_website', true);
                if (!$website) {
                    $website = get_term_meta($term->term_id, 'facility_website', true);
                }
                
                $institutions[] = array(
                    'name' => $term->name,
                    'slug' => $term->slug,
                    'count' => intval($term->count),
                    'url' => get_term_link($term),
                    'website' => $website ?: '',
                );
            }
            set_transient($cache_key, $institutions, 10 * MINUTE_IN_SECONDS);
            return $institutions;
        }
    }

    // Fallback to meta-based query
    global $wpdb;
    
    $results = $wpdb->get_results($wpdb->prepare("
        SELECT meta_value as institution, COUNT(*) as count
        FROM {$wpdb->postmeta} pm
        JOIN {$wpdb->posts} p ON pm.post_id = p.ID
        WHERE pm.meta_key = '_mh_facility'
        AND pm.meta_value != ''
        AND p.post_status = 'publish'
        AND p.post_type IN ('mh_paper', 'mh_protocol')
        GROUP BY meta_value
        ORDER BY count DESC
        LIMIT %d
    ", $limit));
    
    foreach ($results as $row) {
        $institutions[] = array(
            'name' => $row->institution,
            'slug' => sanitize_title($row->institution),
            'count' => intval($row->count),
            'url' => '',
            'website' => '',
        );
    }

    set_transient($cache_key, $institutions, 10 * MINUTE_IN_SECONDS);
    return $institutions;
}

// Backward compatibility alias
function mh_get_facilities($limit = 10) {
    return mh_get_institutions($limit);
}

/**
 * Get recent protocol URLs from papers (not protocol papers, but papers linking to protocols)
 */
function mh_get_recent_protocol_urls($limit = 8) {
    if (!mh_plugin_active()) return array();
    
    global $wpdb;
    
    $results = $wpdb->get_results($wpdb->prepare("
        SELECT p.ID, p.post_title, pm.meta_value as protocols_json
        FROM {$wpdb->postmeta} pm
        JOIN {$wpdb->posts} p ON pm.post_id = p.ID
        WHERE pm.meta_key = '_mh_protocols'
        AND pm.meta_value != ''
        AND pm.meta_value != '[]'
        AND p.post_status = 'publish'
        ORDER BY p.post_date DESC
        LIMIT %d
    ", $limit * 2)); // Get more to account for filtering
    
    $protocols = array();
    foreach ($results as $row) {
        $paper_protocols = json_decode($row->protocols_json, true);
        if (!is_array($paper_protocols)) continue;
        
        foreach ($paper_protocols as $protocol) {
            if (empty($protocol['url'])) continue;
            
            $source = '';
            $url = $protocol['url'];
            
            // Detect source from URL
            if (stripos($url, 'protocols.io') !== false) $source = 'protocols.io';
            elseif (stripos($url, 'jove.com') !== false) $source = 'JoVE';
            elseif (stripos($url, 'bio-protocol.org') !== false) $source = 'Bio-protocol';
            elseif (stripos($url, 'nature.com/nprot') !== false) $source = 'Nature Protocols';
            elseif (stripos($url, 'cell.com/star-protocols') !== false) $source = 'STAR Protocols';
            elseif (!empty($protocol['name'])) $source = $protocol['name'];
            else $source = 'Protocol';
            
            $protocols[] = array(
                'title' => $row->post_title,
                'url' => $url,
                'source' => $source,
                'paper_id' => $row->ID,
            );
            
            if (count($protocols) >= $limit) break;
        }
        
        if (count($protocols) >= $limit) break;
    }
    
    return array_slice($protocols, 0, $limit);
}

/**
 * Get ROR organizations from papers
 */
function mh_get_ror_organizations($limit = 10) {
    if (!mh_plugin_active()) return array();
    
    global $wpdb;
    
    $results = $wpdb->get_results($wpdb->prepare("
        SELECT pm.meta_value as rors_json, COUNT(*) as count
        FROM {$wpdb->postmeta} pm
        JOIN {$wpdb->posts} p ON pm.post_id = p.ID
        WHERE pm.meta_key = '_mh_rors'
        AND pm.meta_value != ''
        AND pm.meta_value != '[]'
        AND p.post_status = 'publish'
        GROUP BY pm.meta_value
        LIMIT %d
    ", $limit * 3));
    
    $rors = array();
    $seen_ids = array();
    
    foreach ($results as $row) {
        $ror_list = json_decode($row->rors_json, true);
        if (!is_array($ror_list)) continue;
        
        foreach ($ror_list as $ror) {
            if (empty($ror['id'])) continue;
            if (isset($seen_ids[$ror['id']])) {
                $rors[$seen_ids[$ror['id']]]['count'] += intval($row->count);
                continue;
            }
            
            $seen_ids[$ror['id']] = count($rors);
            $rors[] = array(
                'id' => $ror['id'],
                'url' => $ror['url'] ?? "https://ror.org/{$ror['id']}",
                'count' => intval($row->count),
            );
            
            if (count($rors) >= $limit) break;
        }
        
        if (count($rors) >= $limit) break;
    }
    
    // Sort by count
    usort($rors, function($a, $b) { return $b['count'] - $a['count']; });
    
    return array_slice($rors, 0, $limit);
}

/**
 * Get newest papers by publication date
 */
function mh_get_newest_papers($limit = 8) {
    if (!mh_plugin_active()) return array();

    // Check cache first - 10 minute cache
    $cache_key = 'mh_newest_papers_' . $limit;
    $cached = get_transient($cache_key);
    if ($cached !== false) {
        return $cached;
    }

    $papers = get_posts(array(
        'post_type' => 'mh_paper',
        'post_status' => 'publish',
        'posts_per_page' => $limit,
        'meta_key' => '_mh_publication_year',
        'orderby' => 'meta_value_num',
        'order' => 'DESC',
    ));

    $results = array();
    foreach ($papers as $paper) {
        $results[] = array(
            'id' => $paper->ID,
            'title' => $paper->post_title,
            'permalink' => get_permalink($paper->ID),
            'year' => get_post_meta($paper->ID, '_mh_publication_year', true),
        );
    }

    set_transient($cache_key, $results, 10 * MINUTE_IN_SECONDS);
    return $results;
}

/**
 * Get papers that have ROR identifiers
 */
function mh_get_papers_with_rors($limit = 8) {
    if (!mh_plugin_active()) return array();

    // Check cache first - 10 minute cache
    $cache_key = 'mh_papers_with_rors_' . $limit;
    $cached = get_transient($cache_key);
    if ($cached !== false) {
        return $cached;
    }

    global $wpdb;

    $results = $wpdb->get_results($wpdb->prepare("
        SELECT p.ID, p.post_title, pm.meta_value as rors_json
        FROM {$wpdb->posts} p
        JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id
        WHERE p.post_type = 'mh_paper'
        AND p.post_status = 'publish'
        AND pm.meta_key = '_mh_rors'
        AND pm.meta_value != ''
        AND pm.meta_value != '[]'
        ORDER BY p.post_date DESC
        LIMIT %d
    ", $limit));

    $papers = array();
    foreach ($results as $row) {
        $rors = json_decode($row->rors_json, true);
        $ror_count = is_array($rors) ? count($rors) : 0;

        $papers[] = array(
            'id' => $row->ID,
            'title' => $row->post_title,
            'permalink' => get_permalink($row->ID),
            'ror_count' => $ror_count,
        );
    }

    set_transient($cache_key, $papers, 10 * MINUTE_IN_SECONDS);
    return $papers;
}

/**
 * Clear sidebar caches when papers are added/updated
 * This ensures sidebars update with new content
 */
function mh_clear_sidebar_caches($post_id) {
    $post_type = get_post_type($post_id);
    if (!in_array($post_type, array('mh_paper', 'mh_protocol'))) {
        return;
    }

    // Clear all sidebar-related transients
    delete_transient('mh_newest_papers_8');
    delete_transient('mh_papers_with_rors_8');
    delete_transient('mh_recent_protocols_8');
    delete_transient('mh_institutions_10');
    delete_transient('mh_filter_options');

    // Clear for common limit values
    for ($i = 5; $i <= 15; $i++) {
        delete_transient('mh_newest_papers_' . $i);
        delete_transient('mh_papers_with_rors_' . $i);
        delete_transient('mh_recent_protocols_' . $i);
        delete_transient('mh_institutions_' . $i);
    }
}
add_action('save_post', 'mh_clear_sidebar_caches');
add_action('delete_post', 'mh_clear_sidebar_caches');
add_action('trashed_post', 'mh_clear_sidebar_caches');
