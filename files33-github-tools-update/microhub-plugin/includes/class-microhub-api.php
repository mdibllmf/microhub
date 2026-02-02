<?php
/**
 * MicroHub REST API v2.1
 * Enhanced with GitHub, protocols, facilities, AI chat
 */

class MicroHub_API {

    public function init() {
        add_action('rest_api_init', array($this, 'register_routes'));
    }

    public function register_routes() {
        $namespace = 'microhub/v1';

        // Papers
        register_rest_route($namespace, '/papers', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_papers'),
            'permission_callback' => '__return_true',
        ));

        register_rest_route($namespace, '/papers/(?P<id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_paper'),
            'permission_callback' => '__return_true',
        ));

        // Taxonomies
        register_rest_route($namespace, '/taxonomies/(?P<taxonomy>[a-z_]+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_taxonomy_terms'),
            'permission_callback' => '__return_true',
        ));

        // Stats
        register_rest_route($namespace, '/stats', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_stats'),
            'permission_callback' => '__return_true',
        ));

        register_rest_route($namespace, '/enrichment-stats', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_enrichment_stats'),
            'permission_callback' => '__return_true',
        ));

        // NEW: Protocols
        register_rest_route($namespace, '/protocols', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_protocols'),
            'permission_callback' => '__return_true',
        ));

        // NEW: GitHub repos
        register_rest_route($namespace, '/github-repos', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_github_repos'),
            'permission_callback' => '__return_true',
        ));

        // NEW: GitHub tools (aggregated with health metrics for tools page)
        register_rest_route($namespace, '/github-tools', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_github_tools'),
            'permission_callback' => '__return_true',
        ));

        // NEW: Data repositories (Zenodo, Figshare, etc.)
        register_rest_route($namespace, '/data-repos', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_data_repositories'),
            'permission_callback' => '__return_true',
        ));

        // NEW: Facilities
        register_rest_route($namespace, '/facilities', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_facilities'),
            'permission_callback' => '__return_true',
        ));

        // NEW: AI Chat proxy
        register_rest_route($namespace, '/ai-chat', array(
            'methods' => 'POST',
            'callback' => array($this, 'ai_chat'),
            'permission_callback' => '__return_true',
        ));

        // NEW: Comments
        register_rest_route($namespace, '/papers/(?P<id>\d+)/comments', array(
            'methods' => array('GET', 'POST'),
            'callback' => array($this, 'handle_comments'),
            'permission_callback' => '__return_true',
        ));

        // Submission
        register_rest_route($namespace, '/papers/submit', array(
            'methods' => 'POST',
            'callback' => array($this, 'submit_paper'),
            'permission_callback' => function() {
                return is_user_logged_in();
            },
        ));
    }

    /**
     * Get papers with filtering
     */
    public function get_papers($request) {
        $page = max(1, intval($request->get_param('page') ?: 1));
        $per_page = min(100, max(1, intval($request->get_param('per_page') ?: 24)));

        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => $per_page,
            'paged' => $page,
            'post_status' => 'publish',
        );

        // Search
        $search = $request->get_param('search');
        if ($search) {
            $args['s'] = sanitize_text_field($search);
        }

        // Meta query
        $meta_query = array('relation' => 'AND');

        // Year filters
        $year_min = $request->get_param('year_min');
        $year_max = $request->get_param('year_max');
        if ($year_min) {
            $meta_query[] = array(
                'key' => '_mh_publication_year',
                'value' => intval($year_min),
                'compare' => '>=',
                'type' => 'NUMERIC',
            );
        }
        if ($year_max) {
            $meta_query[] = array(
                'key' => '_mh_publication_year',
                'value' => intval($year_max),
                'compare' => '<=',
                'type' => 'NUMERIC',
            );
        }

        // Citations filter
        $citations_min = $request->get_param('citations_min');
        if ($citations_min) {
            $meta_query[] = array(
                'key' => '_mh_citation_count',
                'value' => intval($citations_min),
                'compare' => '>=',
                'type' => 'NUMERIC',
            );
        }

        // Enrichment filters
        if ($request->get_param('has_protocols')) {
            $meta_query[] = array(
                'key' => '_mh_protocols',
                'value' => '',
                'compare' => '!=',
            );
        }

        if ($request->get_param('has_repositories')) {
            $meta_query[] = array(
                'key' => '_mh_repositories',
                'value' => '',
                'compare' => '!=',
            );
        }

        if ($request->get_param('has_github')) {
            $meta_query[] = array(
                'key' => '_mh_github_url',
                'value' => '',
                'compare' => '!=',
            );
        }

        if (count($meta_query) > 1) {
            $args['meta_query'] = $meta_query;
        }

        // Taxonomy filters
        $tax_query = array('relation' => 'AND');

        if ($request->get_param('technique')) {
            $tax_query[] = array(
                'taxonomy' => 'mh_technique',
                'field' => 'slug',
                'terms' => sanitize_text_field($request->get_param('technique')),
            );
        }

        if ($request->get_param('microscope')) {
            $tax_query[] = array(
                'taxonomy' => 'mh_microscope',
                'field' => 'slug',
                'terms' => sanitize_text_field($request->get_param('microscope')),
            );
        }

        if ($request->get_param('organism')) {
            $tax_query[] = array(
                'taxonomy' => 'mh_organism',
                'field' => 'slug',
                'terms' => sanitize_text_field($request->get_param('organism')),
            );
        }

        // Software filter
        if ($request->get_param('software')) {
            $tax_query[] = array(
                'taxonomy' => 'mh_software',
                'field' => 'slug',
                'terms' => sanitize_text_field($request->get_param('software')),
            );
        }

        // Facility filter
        if ($request->get_param('facility')) {
            $tax_query[] = array(
                'taxonomy' => 'mh_facility',
                'field' => 'slug',
                'terms' => sanitize_text_field($request->get_param('facility')),
            );
        }

        if (count($tax_query) > 1) {
            $args['tax_query'] = $tax_query;
        }

        // Sorting (default: citations desc)
        $args['meta_key'] = '_mh_citation_count';
        $args['orderby'] = 'meta_value_num';
        $args['order'] = 'DESC';

        $query = new WP_Query($args);
        $papers = array();

        foreach ($query->posts as $post) {
            $papers[] = $this->format_paper($post);
        }

        return array(
            'papers' => $papers,
            'total' => $query->found_posts,
            'pages' => $query->max_num_pages,
            'page' => $page,
        );
    }

    /**
     * Format paper for API response
     */
    private function format_paper($post) {
        $id = $post->ID;
        
        $protocols_json = get_post_meta($id, '_mh_protocols', true);
        $repos_json = get_post_meta($id, '_mh_repositories', true);
        $rrids_json = get_post_meta($id, '_mh_rrids', true);
        $figure_urls_json = get_post_meta($id, '_mh_figure_urls', true);
        $thumbnail_url = get_post_meta($id, '_mh_thumbnail_url', true);
        $github_tools_json = get_post_meta($id, '_mh_github_tools', true);

        return array(
            'id' => $id,
            'title' => $post->post_title,
            'permalink' => get_permalink($id),
            'doi' => get_post_meta($id, '_mh_doi', true),
            'pubmed_id' => get_post_meta($id, '_mh_pubmed_id', true),
            'authors' => get_post_meta($id, '_mh_authors', true),
            'journal' => get_post_meta($id, '_mh_journal', true),
            'year' => get_post_meta($id, '_mh_publication_year', true),
            'citations' => get_post_meta($id, '_mh_citation_count', true),
            'abstract' => get_post_meta($id, '_mh_abstract', true),
            'pdf_url' => get_post_meta($id, '_mh_pdf_url', true),
            'github_url' => get_post_meta($id, '_mh_github_url', true),
            'facility' => get_post_meta($id, '_mh_facility', true),
            'facility_url' => get_post_meta($id, '_mh_facility_url', true),
            'facilities' => wp_get_post_terms($id, 'mh_facility', array('fields' => 'names')),
            'thumbnail_url' => $thumbnail_url,
            'figure_urls' => $figure_urls_json ? json_decode($figure_urls_json, true) : array(),
            'techniques' => $this->format_terms(wp_get_post_terms($id, 'mh_technique')),
            'microscopes' => $this->format_terms(wp_get_post_terms($id, 'mh_microscope')),
            'organisms' => $this->format_terms(wp_get_post_terms($id, 'mh_organism')),
            'software' => $this->format_terms(wp_get_post_terms($id, 'mh_software')),
            'protocols' => $protocols_json ? json_decode($protocols_json, true) : array(),
            'repositories' => $repos_json ? json_decode($repos_json, true) : array(),
            'rrids' => $rrids_json ? json_decode($rrids_json, true) : array(),
            'github_tools' => $github_tools_json ? json_decode($github_tools_json, true) : array(),
            'comments_count' => get_comments_number($id),
        );
    }

    /**
     * Format taxonomy terms with URLs for clickable tags
     */
    private function format_terms($terms) {
        if (is_wp_error($terms) || empty($terms)) {
            return array();
        }

        $formatted = array();
        foreach ($terms as $term) {
            $formatted[] = array(
                'name' => $term->name,
                'slug' => $term->slug,
                'url' => get_term_link($term),
                'count' => $term->count,
            );
        }
        return $formatted;
    }

    /**
     * Get single paper
     */
    public function get_paper($request) {
        $id = intval($request->get_param('id'));
        $post = get_post($id);

        if (!$post || $post->post_type !== 'mh_paper') {
            return new WP_Error('not_found', 'Paper not found', array('status' => 404));
        }

        return $this->format_paper($post);
    }

    /**
     * Get taxonomy terms
     */
    public function get_taxonomy_terms($request) {
        $taxonomy = 'mh_' . sanitize_key($request->get_param('taxonomy'));
        
        if (!taxonomy_exists($taxonomy)) {
            return new WP_Error('invalid_taxonomy', 'Taxonomy not found', array('status' => 404));
        }

        $terms = get_terms(array(
            'taxonomy' => $taxonomy,
            'hide_empty' => true,
            'number' => 100,
        ));

        if (is_wp_error($terms)) {
            return array();
        }

        return array_map(function($term) {
            return array(
                'id' => $term->term_id,
                'name' => $term->name,
                'slug' => $term->slug,
                'count' => $term->count,
            );
        }, $terms);
    }

    /**
     * Get stats
     */
    public function get_stats() {
        return array(
            'total_papers' => wp_count_posts('mh_paper')->publish,
            'techniques_count' => wp_count_terms('mh_technique'),
            'microscopes_count' => wp_count_terms('mh_microscope'),
            'organisms_count' => wp_count_terms('mh_organism'),
            'software_count' => wp_count_terms('mh_software'),
        );
    }

    /**
     * Get enrichment stats
     */
    public function get_enrichment_stats() {
        global $wpdb;

        $protocols = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != '' AND meta_value != '[]'");
        $repos = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_repositories' AND meta_value != '' AND meta_value != '[]'");
        $rrids = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_rrids' AND meta_value != '' AND meta_value != '[]'");
        $github = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''");
        $github_tools = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_tools' AND meta_value != '' AND meta_value != '[]'");
        $facilities = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_facility' AND meta_value != ''");
        $microscopes = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_microscope_name' AND meta_value != ''");
        
        // Count papers with software taxonomy
        $software = $wpdb->get_var("
            SELECT COUNT(DISTINCT tr.object_id) 
            FROM {$wpdb->term_relationships} tr
            JOIN {$wpdb->term_taxonomy} tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
            WHERE tt.taxonomy = 'mh_software'
        ");

        return array(
            'papers_with_protocols' => intval($protocols),
            'papers_with_repositories' => intval($repos),
            'papers_with_rrids' => intval($rrids),
            'papers_with_github' => intval($github),
            'papers_with_github_tools' => intval($github_tools),
            'papers_with_facilities' => intval($facilities),
            'papers_with_microscopes' => intval($microscopes),
            'papers_with_software' => intval($software),
        );
    }

    /**
     * Get protocols - includes both user-uploaded and paper-linked protocols
     */
    public function get_protocols($request) {
        global $wpdb;
        $per_page = min(50, max(1, intval($request->get_param('per_page') ?: 10)));
        
        $protocols = array();
        
        // 1. Get user-uploaded protocols (mh_protocol post type)
        $uploaded_protocols = get_posts(array(
            'post_type' => 'mh_protocol',
            'posts_per_page' => $per_page,
            'post_status' => 'publish',
            'orderby' => 'date',
            'order' => 'DESC',
        ));
        
        foreach ($uploaded_protocols as $post) {
            $protocols[] = array(
                'id' => $post->ID,
                'title' => $post->post_title,
                'permalink' => get_permalink($post->ID),
                'source' => get_post_meta($post->ID, '_mh_protocol_source', true) ?: 'Community Upload',
                'type' => 'uploaded',
            );
        }
        
        // 2. Get protocols linked from papers (_mh_protocols meta)
        $paper_protocols = $wpdb->get_results("
            SELECT p.ID, p.post_title, pm.meta_value 
            FROM {$wpdb->postmeta} pm
            JOIN {$wpdb->posts} p ON p.ID = pm.post_id
            WHERE pm.meta_key = '_mh_protocols' 
            AND pm.meta_value != '' 
            AND pm.meta_value != '[]'
            AND p.post_status = 'publish'
            AND p.post_type = 'mh_paper'
            ORDER BY p.post_date DESC
            LIMIT " . ($per_page * 3)
        );
        
        foreach ($paper_protocols as $row) {
            $protocol_data = json_decode($row->meta_value, true);
            if (!$protocol_data || !is_array($protocol_data)) continue;
            
            foreach ($protocol_data as $proto) {
                if (empty($proto['url'])) continue;
                
                // Use paper title as the display title, protocol source as subtitle
                $paper_title = $row->post_title;
                $short_title = strlen($paper_title) > 60 ? substr($paper_title, 0, 57) . '...' : $paper_title;
                
                $protocols[] = array(
                    'id' => $row->ID,
                    'title' => $short_title,
                    'permalink' => get_permalink($row->ID),  // Link to paper page, not external URL
                    'protocol_url' => esc_url($proto['url']),  // Direct protocol link
                    'source' => $proto['name'] ?: 'Protocol',  // e.g., "Nature Protocols"
                    'paper_id' => $row->ID,
                    'type' => 'paper_linked',
                );
            }
        }
        
        // Sort by newest first and limit
        return array_slice($protocols, 0, $per_page);
    }

    /**
     * Get GitHub repos associated with papers
     */
    /**
     * Get GitHub repositories for sidebar
     */
    public function get_github_repos($request) {
        global $wpdb;

        $github_urls = $wpdb->get_results("
            SELECT DISTINCT pm.meta_value as url, p.post_title as paper_title, p.ID as paper_id, p.post_date
            FROM {$wpdb->postmeta} pm
            JOIN {$wpdb->posts} p ON p.ID = pm.post_id
            WHERE pm.meta_key = '_mh_github_url' 
            AND pm.meta_value != ''
            AND pm.meta_value LIKE '%github.com%'
            AND p.post_status = 'publish'
            AND p.post_type = 'mh_paper'
            ORDER BY p.post_date DESC
            LIMIT 20
        ");

        $repos = array();
        foreach ($github_urls as $row) {
            $url = $row->url;
            // Extract repo name from URL
            preg_match('/github\.com\/([^\/]+\/[^\/\?\#]+)/', $url, $matches);
            $name = isset($matches[1]) ? $matches[1] : basename($url);
            // Clean up name
            $name = preg_replace('/\.git$/', '', $name);
            
            $repos[] = array(
                'url' => esc_url($url),
                'name' => $name,
                'paper_title' => $row->paper_title,
                'paper_id' => $row->paper_id,
                'paper_url' => get_permalink($row->paper_id),
            );
        }

        return $repos;
    }

    /**
     * Get GitHub tools ranked by usage across papers with health metrics.
     * Aggregates _mh_github_tools meta across all papers for the GitHub Tools page.
     */
    public function get_github_tools($request) {
        global $wpdb;
        
        $sort = sanitize_text_field($request->get_param('sort') ?: 'paper_count');
        $limit = min(2000, max(1, intval($request->get_param('limit') ?: 100)));
        $min_papers = max(1, intval($request->get_param('min_papers') ?: 1));
        $show_archived = $request->get_param('show_archived') ? true : false;
        
        // Gather all github_tools meta from papers (also get citation_count)
        $rows = $wpdb->get_results("
            SELECT p.ID as paper_id, p.post_title, pm.meta_value as tools_json,
                   COALESCE((SELECT meta_value FROM {$wpdb->postmeta} WHERE post_id = p.ID AND meta_key = '_mh_citation_count' LIMIT 1), 0) as citation_count
            FROM {$wpdb->postmeta} pm
            JOIN {$wpdb->posts} p ON p.ID = pm.post_id
            WHERE pm.meta_key = '_mh_github_tools'
            AND pm.meta_value != '' AND pm.meta_value != '[]'
            AND p.post_status = 'publish'
            AND p.post_type = 'mh_paper'
        ");
        
        // Aggregate tools across papers
        $tools_aggregate = array();
        
        foreach ($rows as $row) {
            $tools = json_decode($row->tools_json, true);
            if (!is_array($tools)) continue;
            
            foreach ($tools as $tool) {
                $full_name = strtolower($tool['full_name'] ?? '');
                if (empty($full_name)) continue;
                
                if (!isset($tools_aggregate[$full_name])) {
                    $tools_aggregate[$full_name] = array(
                        'full_name' => $tool['full_name'],
                        'url' => $tool['url'] ?? '',
                        'description' => $tool['description'] ?? '',
                        'stars' => intval($tool['stars'] ?? 0),
                        'forks' => intval($tool['forks'] ?? 0),
                        'open_issues' => intval($tool['open_issues'] ?? 0),
                        'last_commit_date' => $tool['last_commit_date'] ?? '',
                        'last_release' => $tool['last_release'] ?? '',
                        'health_score' => intval($tool['health_score'] ?? 0),
                        'is_archived' => !empty($tool['is_archived']),
                        'language' => $tool['language'] ?? '',
                        'license' => $tool['license'] ?? '',
                        'topics' => $tool['topics'] ?? array(),
                        'paper_count' => 0,
                        'total_citations' => 0,
                        'papers_introducing' => 0,
                        'papers_using' => 0,
                        'papers_extending' => 0,
                        'papers_benchmarking' => 0,
                        'paper_titles' => array(),
                        'paper_ids' => array(),
                    );
                }
                
                $tools_aggregate[$full_name]['paper_count']++;
                $tools_aggregate[$full_name]['total_citations'] += intval($row->citation_count);
                $tools_aggregate[$full_name]['paper_titles'][] = $row->post_title;
                $tools_aggregate[$full_name]['paper_ids'][] = intval($row->paper_id);
                
                // Track relationship types
                $rel = $tool['relationship'] ?? 'uses';
                if ($rel === 'introduces') $tools_aggregate[$full_name]['papers_introducing']++;
                elseif ($rel === 'extends') $tools_aggregate[$full_name]['papers_extending']++;
                elseif ($rel === 'benchmarks') $tools_aggregate[$full_name]['papers_benchmarking']++;
                else $tools_aggregate[$full_name]['papers_using']++;
                
                // Keep best metadata - prefer non-empty values
                if (empty($tools_aggregate[$full_name]['description']) && !empty($tool['description'])) {
                    $tools_aggregate[$full_name]['description'] = $tool['description'];
                }
                if (empty($tools_aggregate[$full_name]['language']) && !empty($tool['language'])) {
                    $tools_aggregate[$full_name]['language'] = $tool['language'];
                }
                if (empty($tools_aggregate[$full_name]['license']) && !empty($tool['license'])) {
                    $tools_aggregate[$full_name]['license'] = $tool['license'];
                }
                if (empty($tools_aggregate[$full_name]['topics']) && !empty($tool['topics'])) {
                    $tools_aggregate[$full_name]['topics'] = $tool['topics'];
                }

                // Keep latest metrics (higher values likely more current)
                if (intval($tool['stars'] ?? 0) > $tools_aggregate[$full_name]['stars']) {
                    $tools_aggregate[$full_name]['stars'] = intval($tool['stars']);
                    $tools_aggregate[$full_name]['forks'] = intval($tool['forks'] ?? 0);
                    $tools_aggregate[$full_name]['open_issues'] = intval($tool['open_issues'] ?? 0);
                    $tools_aggregate[$full_name]['health_score'] = intval($tool['health_score'] ?? 0);
                    $tools_aggregate[$full_name]['last_commit_date'] = $tool['last_commit_date'] ?? '';
                    $tools_aggregate[$full_name]['last_release'] = $tool['last_release'] ?? '';
                    $tools_aggregate[$full_name]['is_archived'] = !empty($tool['is_archived']);
                }
            }
        }
        
        // Filter
        $tools_aggregate = array_filter($tools_aggregate, function($t) use ($min_papers, $show_archived) {
            if ($t['paper_count'] < $min_papers) return false;
            if (!$show_archived && $t['is_archived']) return false;
            return true;
        });
        
        // Trim paper_titles to top 5
        foreach ($tools_aggregate as &$t) {
            $t['paper_titles'] = array_slice($t['paper_titles'], 0, 5);
            $t['paper_ids'] = array_slice($t['paper_ids'], 0, 5);
        }
        unset($t);
        
        // Sort
        $tools_list = array_values($tools_aggregate);
        usort($tools_list, function($a, $b) use ($sort) {
            if ($sort === 'citations') return $b['total_citations'] - $a['total_citations'];
            if ($sort === 'stars') return $b['stars'] - $a['stars'];
            if ($sort === 'health') return $b['health_score'] - $a['health_score'];
            return $b['paper_count'] - $a['paper_count'];
        });
        
        return array(
            'tools' => array_slice($tools_list, 0, $limit),
            'total' => count($tools_list),
        );
    }

    /**
     * Get data repositories (Zenodo, Figshare, IDR, EMPIAR, etc.) for sidebar
     */
    public function get_data_repositories($request) {
        global $wpdb;

        $repos_data = $wpdb->get_results("
            SELECT p.ID, p.post_title, pm.meta_value, p.post_date
            FROM {$wpdb->postmeta} pm
            JOIN {$wpdb->posts} p ON p.ID = pm.post_id
            WHERE pm.meta_key = '_mh_repositories' 
            AND pm.meta_value != ''
            AND pm.meta_value != '[]'
            AND p.post_status = 'publish'
            AND p.post_type = 'mh_paper'
            ORDER BY p.post_date DESC
            LIMIT 50
        ");

        $all_repos = array();
        foreach ($repos_data as $row) {
            $repos = json_decode($row->meta_value, true);
            if (!is_array($repos)) continue;
            
            foreach ($repos as $repo) {
                if (empty($repo['url'])) continue;
                // Skip GitHub - it has its own section
                if (stripos($repo['url'], 'github.com') !== false) continue;
                
                $all_repos[] = array(
                    'name' => $repo['name'] ?? 'Repository',
                    'url' => esc_url($repo['url']),
                    'accession_id' => $repo['accession_id'] ?? '',
                    'paper_title' => $row->post_title,
                    'paper_id' => $row->ID,
                    'paper_url' => get_permalink($row->ID),
                );
            }
        }

        // Limit to 15 unique repos
        return array_slice($all_repos, 0, 15);
    }

    /**
     * Get facilities for sidebar
     */
    public function get_facilities($request) {
        global $wpdb;

        $facilities = $wpdb->get_results("
            SELECT DISTINCT pm.meta_value as name, COUNT(*) as paper_count
            FROM {$wpdb->postmeta} pm
            JOIN {$wpdb->posts} p ON p.ID = pm.post_id
            WHERE pm.meta_key = '_mh_facility'
            AND pm.meta_value != ''
            AND p.post_status = 'publish'
            AND p.post_type = 'mh_paper'
            GROUP BY pm.meta_value
            ORDER BY paper_count DESC
            LIMIT 15
        ");

        $base_url = home_url('/');
        return array_map(function($row) use ($base_url) {
            // Create search URL for this facility
            $search_url = add_query_arg('facility', urlencode($row->name), $base_url);
            return array(
                'name' => $row->name,
                'paper_count' => intval($row->paper_count),
                'search_url' => $search_url,
            );
        }, $facilities);
    }

    /**
     * Smart AI Chat - Searches knowledge base first, then papers
     * Provides dynamic, contextual responses
     */
    public function ai_chat($request) {
        $message = sanitize_text_field($request->get_param('message'));
        $context = sanitize_text_field($request->get_param('context'));

        if (!$message) {
            return new WP_Error('invalid_message', 'Message is required', array('status' => 400));
        }

        // Check if Anthropic API key is configured
        $api_key = get_option('microhub_anthropic_api_key', '');
        
        if (!empty($api_key)) {
            // Use Anthropic API
            return $this->ai_chat_anthropic($message, $api_key);
        }
        
        // Fall back to rules-based system if no API key
        return $this->ai_chat_fallback($message, $context);
    }
    
    /**
     * AI Chat using Anthropic API with rich paper context
     */
    private function ai_chat_anthropic($message, $api_key) {
        $response = array(
            'reply' => '',
            'papers' => array(),
            'type' => 'ai'
        );
        
        // ============================================
        // GATHER ALL AVAILABLE CONTEXT
        // ============================================
        
        // 1. Search for relevant papers with FULL details
        $papers = $this->search_papers_for_ai($message);
        $paper_context = $this->build_paper_context_for_ai($papers);
        
        // 2. Get knowledge base entries (uploaded documents)
        $kb_results = $this->search_knowledge_base(strtolower($message), 5);
        $kb_context = '';
        if (!empty($kb_results)) {
            $kb_context = "\n\n" . str_repeat("=", 60) . "\n";
            $kb_context .= "## KNOWLEDGE BASE DOCUMENTS\n";
            $kb_context .= "These are custom documents uploaded by the site administrator:\n";
            $kb_context .= str_repeat("=", 60) . "\n\n";
            foreach ($kb_results as $kb) {
                $kb_context .= "### " . $kb['title'] . "\n";
                $kb_context .= $kb['content'] . "\n\n";  // Include full content, not just excerpt
            }
        }
        
        // 3. Get custom training data (Q&A pairs, techniques, software)
        $training_context = $this->get_custom_training_context($message);
        
        // 4. Get site statistics for context
        $stats_context = $this->get_site_stats_context();
        
        // ============================================
        // BUILD SYSTEM PROMPT
        // ============================================
        $system_prompt = "You are the MicroHub Assistant, an expert microscopy research consultant with FULL ACCESS to the MicroHub database.

## SITE OVERVIEW
{$stats_context}

## YOUR CAPABILITIES
You have access to:
1. **Paper Database** - Thousands of microscopy research papers with full metadata
2. **Knowledge Base** - Custom documents uploaded by the administrator
3. **Custom Training** - Specific Q&A pairs, technique descriptions, and software info

## PRIORITY ORDER FOR ANSWERING
1. FIRST: Check if there's a custom Q&A or training response that matches
2. SECOND: Use papers from the database - cite them specifically
3. THIRD: Use knowledge base documents
4. FOURTH: Use your general microscopy expertise

## CITATION REQUIREMENTS - ALWAYS FOLLOW
When using information from papers:
- Cite by exact title: \"Based on '[Paper Title]' (Author et al., Year, Journal)\"
- Include DOI when available
- Reference specific details (microscopes, techniques, organisms)
- Mention linked protocols if available

## RESPONSE FORMAT FOR PROTOCOLS

### Recommended Protocol
**Based on:** \"[Paper Title]\" ([Author] et al., [Year], [Journal])
**DOI:** [doi]

**Technique:** [from paper]
**Microscope:** [brand/model from paper]
**Organisms/Samples:** [from paper]
**Fluorophores:** [from paper]

**Sample Preparation:**
[Specific steps with concentrations, times, temperatures]

**Imaging Parameters:**
[Settings from paper or general recommendations]

**Analysis:**
[Software and workflow]

## WHEN DATA IS LIMITED
If papers don't have complete protocols:
1. State what IS available from the database
2. Provide general guidance based on your expertise
3. Suggest the user check the full paper or search MicroHub

## INTERACTION STYLE
- Be helpful and specific
- Ask clarifying questions if needed (microscope model, organism, etc.)
- Always cite your sources
- Be honest about limitations" . $training_context . $paper_context . $kb_context;

        // ============================================
        // CALL ANTHROPIC API
        // ============================================
        $api_response = wp_remote_post('https://api.anthropic.com/v1/messages', array(
            'timeout' => 60,
            'headers' => array(
                'Content-Type' => 'application/json',
                'x-api-key' => $api_key,
                'anthropic-version' => '2023-06-01',
            ),
            'body' => json_encode(array(
                'model' => 'claude-sonnet-4-20250514',
                'max_tokens' => 4000,
                'system' => $system_prompt,
                'messages' => array(
                    array('role' => 'user', 'content' => $message)
                )
            ))
        ));
        
        if (is_wp_error($api_response)) {
            error_log('MicroHub AI Chat Error: ' . $api_response->get_error_message());
            $response['reply'] = "I'm having trouble connecting right now. Please try again.";
            $response['papers'] = $this->simplify_papers_for_response($papers);
            return $response;
        }
        
        $body = json_decode(wp_remote_retrieve_body($api_response), true);
        
        if (isset($body['content'][0]['text'])) {
            $response['reply'] = $body['content'][0]['text'];
            $response['papers'] = $this->simplify_papers_for_response($papers);
        } else {
            if (isset($body['error']['message'])) {
                error_log('MicroHub AI Chat API Error: ' . $body['error']['message']);
            }
            $response['reply'] = "I couldn't process that request. Please try rephrasing your question.";
            $response['papers'] = $this->simplify_papers_for_response($papers);
        }
        
        return $response;
    }
    
    /**
     * Get custom training data context for AI
     */
    private function get_custom_training_context($message) {
        $context = '';
        $msg_lower = strtolower($message);
        
        // Get Q&A pairs
        $qa_pairs = get_option('microhub_ai_qa_pairs', array());
        $matching_qa = array();
        
        if (!empty($qa_pairs)) {
            foreach ($qa_pairs as $pair) {
                if (empty($pair['keywords'])) continue;
                
                $keywords = array_map('trim', explode(',', strtolower($pair['keywords'])));
                foreach ($keywords as $keyword) {
                    if (strlen($keyword) >= 3 && strpos($msg_lower, $keyword) !== false) {
                        $matching_qa[] = $pair;
                        break;
                    }
                }
            }
        }
        
        // Get technique descriptions
        $techniques = get_option('microhub_ai_techniques', array());
        $matching_techniques = array();
        
        if (!empty($techniques)) {
            foreach ($techniques as $tech) {
                $name_lower = strtolower($tech['name'] ?? '');
                $keywords = array_map('trim', explode(',', strtolower($tech['keywords'] ?? '')));
                
                if ($name_lower && strpos($msg_lower, $name_lower) !== false) {
                    $matching_techniques[] = $tech;
                } else {
                    foreach ($keywords as $keyword) {
                        if (strlen($keyword) >= 3 && strpos($msg_lower, $keyword) !== false) {
                            $matching_techniques[] = $tech;
                            break;
                        }
                    }
                }
            }
        }
        
        // Get software descriptions
        $software = get_option('microhub_ai_software', array());
        $matching_software = array();
        
        if (!empty($software)) {
            foreach ($software as $sw) {
                $name_lower = strtolower($sw['name'] ?? '');
                $keywords = array_map('trim', explode(',', strtolower($sw['keywords'] ?? '')));
                
                if ($name_lower && strpos($msg_lower, $name_lower) !== false) {
                    $matching_software[] = $sw;
                } else {
                    foreach ($keywords as $keyword) {
                        if (strlen($keyword) >= 3 && strpos($msg_lower, $keyword) !== false) {
                            $matching_software[] = $sw;
                            break;
                        }
                    }
                }
            }
        }
        
        // Build context from matching training data
        if (!empty($matching_qa) || !empty($matching_techniques) || !empty($matching_software)) {
            $context .= "\n\n" . str_repeat("=", 60) . "\n";
            $context .= "## CUSTOM TRAINING DATA (HIGH PRIORITY)\n";
            $context .= "The administrator has provided these specific responses:\n";
            $context .= str_repeat("=", 60) . "\n\n";
            
            if (!empty($matching_qa)) {
                $context .= "### Predefined Q&A Responses:\n";
                foreach ($matching_qa as $qa) {
                    $context .= "**Keywords:** {$qa['keywords']}\n";
                    if (!empty($qa['question'])) {
                        $context .= "**Question Pattern:** {$qa['question']}\n";
                    }
                    $context .= "**RECOMMENDED RESPONSE:**\n{$qa['answer']}\n\n";
                }
            }
            
            if (!empty($matching_techniques)) {
                $context .= "### Technique Descriptions:\n";
                foreach ($matching_techniques as $tech) {
                    $context .= "**{$tech['name']}**\n";
                    $context .= "{$tech['description']}\n\n";
                }
            }
            
            if (!empty($matching_software)) {
                $context .= "### Software Descriptions:\n";
                foreach ($matching_software as $sw) {
                    $context .= "**{$sw['name']}**\n";
                    $context .= "{$sw['description']}\n\n";
                }
            }
        }
        
        return $context;
    }
    
    /**
     * Get site statistics for AI context
     */
    private function get_site_stats_context() {
        $paper_count = wp_count_posts('mh_paper');
        $total_papers = isset($paper_count->publish) ? $paper_count->publish : 0;
        
        $protocol_count = wp_count_posts('mh_protocol');
        $total_protocols = isset($protocol_count->publish) ? $protocol_count->publish : 0;
        
        // Get taxonomy counts
        $techniques = wp_count_terms('mh_technique');
        $organisms = wp_count_terms('mh_organism');
        $software = wp_count_terms('mh_software');
        
        // Get knowledge base count
        global $wpdb;
        $kb_table = $wpdb->prefix . 'mh_knowledge';
        $kb_count = 0;
        if ($wpdb->get_var("SHOW TABLES LIKE '$kb_table'") === $kb_table) {
            $kb_count = $wpdb->get_var("SELECT COUNT(*) FROM $kb_table");
        }
        
        // Get GitHub tools count
        $github_tools_papers = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_tools' AND meta_value != '' AND meta_value != '[]'");
        
        $stats = "MicroHub Database contains:
- {$total_papers} research papers
- {$total_protocols} protocols
- " . (is_wp_error($techniques) ? 0 : $techniques) . " microscopy techniques
- " . (is_wp_error($organisms) ? 0 : $organisms) . " organisms/model systems
- " . (is_wp_error($software) ? 0 : $software) . " software tools
- Papers with enriched GitHub tool data: " . intval($github_tools_papers) . "
- {$kb_count} knowledge base documents";
        
        return $stats;
    }
    
    /**
     * Search papers comprehensively for AI context
     * Searches across titles, abstracts, and all taxonomies
     */
    private function search_papers_for_ai($query) {
        global $wpdb;
        
        // Extract meaningful search terms
        $search = preg_replace('/\b(find|search|papers?|about|show|me|the|for|on|using|with|how|do|i|can|you|help|protocol|method|what|is|are|best|good|recommend)\b/i', '', $query);
        $search = trim(preg_replace('/\s+/', ' ', $search));
        
        if (strlen($search) < 2) {
            $search = $query; // Fall back to original query
        }
        
        $papers = array();
        $found_ids = array();
        
        // Extract individual keywords for taxonomy matching
        $keywords = array_filter(explode(' ', strtolower($search)), function($w) {
            return strlen($w) >= 3;
        });
        
        // ============================================
        // STRATEGY 1: Search by taxonomy terms (most reliable)
        // ============================================
        $taxonomies_to_search = array(
            'mh_technique' => 3,    // weight: 3 (most important)
            'mh_organism' => 2,
            'mh_software' => 2,
            'mh_fluorophore' => 2,
            'mh_sample_prep' => 2,
            'mh_microscope' => 2,
            'mh_cell_line' => 1,
        );
        
        $taxonomy_post_ids = array();
        
        foreach ($taxonomies_to_search as $taxonomy => $weight) {
            if (!taxonomy_exists($taxonomy)) continue;
            
            // Search for matching terms
            $terms = get_terms(array(
                'taxonomy' => $taxonomy,
                'search' => $search,
                'hide_empty' => true,
                'number' => 10
            ));
            
            // Also try individual keywords
            if (empty($terms) || is_wp_error($terms)) {
                foreach ($keywords as $keyword) {
                    $keyword_terms = get_terms(array(
                        'taxonomy' => $taxonomy,
                        'search' => $keyword,
                        'hide_empty' => true,
                        'number' => 5
                    ));
                    if (!is_wp_error($keyword_terms) && !empty($keyword_terms)) {
                        $terms = array_merge($terms ?: array(), $keyword_terms);
                    }
                }
            }
            
            if (!is_wp_error($terms) && !empty($terms)) {
                $term_ids = wp_list_pluck($terms, 'term_id');
                
                // Get posts with these terms
                $term_posts = get_posts(array(
                    'post_type' => 'mh_paper',
                    'posts_per_page' => 20,
                    'fields' => 'ids',
                    'tax_query' => array(
                        array(
                            'taxonomy' => $taxonomy,
                            'field' => 'term_id',
                            'terms' => $term_ids
                        )
                    )
                ));
                
                foreach ($term_posts as $pid) {
                    if (!isset($taxonomy_post_ids[$pid])) {
                        $taxonomy_post_ids[$pid] = 0;
                    }
                    $taxonomy_post_ids[$pid] += $weight;
                }
            }
        }
        
        // ============================================
        // STRATEGY 2: Search in title and abstract (text search)
        // ============================================
        $text_search_ids = array();
        
        // WordPress default search (title + content)
        $text_query = new WP_Query(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => 15,
            's' => $search,
            'post_status' => 'publish',
            'fields' => 'ids'
        ));
        
        if ($text_query->have_posts()) {
            foreach ($text_query->posts as $pid) {
                $text_search_ids[$pid] = 2; // weight: 2
            }
        }
        
        // Also search in abstract meta field directly
        $abstract_results = $wpdb->get_col($wpdb->prepare(
            "SELECT post_id FROM {$wpdb->postmeta} 
             WHERE meta_key = '_mh_abstract' 
             AND meta_value LIKE %s 
             LIMIT 15",
            '%' . $wpdb->esc_like($search) . '%'
        ));
        
        foreach ($abstract_results as $pid) {
            if (!isset($text_search_ids[$pid])) {
                $text_search_ids[$pid] = 0;
            }
            $text_search_ids[$pid] += 2;
        }
        
        // ============================================
        // STRATEGY 3: Search microscope brand/model
        // ============================================
        $microscope_keywords = array('zeiss', 'leica', 'nikon', 'olympus', 'evident', 'confocal', 'lsm', 'sp8', 'a1r', 'sted', 'spinning disk', 'light sheet', 'lightsheet');
        $search_lower = strtolower($search);
        
        foreach ($microscope_keywords as $mk) {
            if (strpos($search_lower, $mk) !== false) {
                $brand_results = $wpdb->get_col($wpdb->prepare(
                    "SELECT post_id FROM {$wpdb->postmeta} 
                     WHERE (meta_key = '_mh_microscope_brand' OR meta_key = '_mh_microscope_model' OR meta_key = '_mh_microscope')
                     AND LOWER(meta_value) LIKE %s 
                     LIMIT 10",
                    '%' . $wpdb->esc_like($mk) . '%'
                ));
                
                foreach ($brand_results as $pid) {
                    if (!isset($taxonomy_post_ids[$pid])) {
                        $taxonomy_post_ids[$pid] = 0;
                    }
                    $taxonomy_post_ids[$pid] += 3; // high weight for microscope match
                }
            }
        }
        
        // ============================================
        // COMBINE AND RANK RESULTS
        // ============================================
        $all_scores = array();
        
        foreach ($taxonomy_post_ids as $pid => $score) {
            $all_scores[$pid] = ($all_scores[$pid] ?? 0) + $score;
        }
        
        foreach ($text_search_ids as $pid => $score) {
            $all_scores[$pid] = ($all_scores[$pid] ?? 0) + $score;
        }
        
        // Add citation count as a factor
        foreach ($all_scores as $pid => $score) {
            $citations = (int) get_post_meta($pid, '_mh_citation_count', true);
            if ($citations > 100) $all_scores[$pid] += 2;
            elseif ($citations > 50) $all_scores[$pid] += 1;
        }
        
        // Sort by score (highest first)
        arsort($all_scores);
        
        // Take top 10 results
        $top_ids = array_slice(array_keys($all_scores), 0, 10);
        
        // ============================================
        // FETCH FULL PAPER DATA
        // ============================================
        foreach ($top_ids as $post_id) {
            $post = get_post($post_id);
            if (!$post || $post->post_status !== 'publish') continue;
            
            $paper = array(
                'id' => $post_id,
                'title' => $post->post_title,
                'url' => get_permalink($post_id),
                'doi' => get_post_meta($post_id, '_mh_doi', true),
                'pmid' => get_post_meta($post_id, '_mh_pubmed_id', true),
                'authors' => get_post_meta($post_id, '_mh_authors', true),
                'journal' => get_post_meta($post_id, '_mh_journal', true),
                'year' => get_post_meta($post_id, '_mh_publication_year', true),
                'citation_count' => get_post_meta($post_id, '_mh_citation_count', true),
                'abstract' => get_post_meta($post_id, '_mh_abstract', true),
                'methods' => get_post_meta($post_id, '_mh_methods', true),
                'microscope_brand' => get_post_meta($post_id, '_mh_microscope_brand', true),
                'microscope_model' => get_post_meta($post_id, '_mh_microscope_model', true),
                'search_score' => $all_scores[$post_id] ?? 0,
            );
            
            // Get taxonomies
            $techniques = wp_get_object_terms($post_id, 'mh_technique', array('fields' => 'names'));
            $paper['techniques'] = is_array($techniques) && !is_wp_error($techniques) ? $techniques : array();
            
            $organisms = wp_get_object_terms($post_id, 'mh_organism', array('fields' => 'names'));
            $paper['organisms'] = is_array($organisms) && !is_wp_error($organisms) ? $organisms : array();
            
            $software = wp_get_object_terms($post_id, 'mh_software', array('fields' => 'names'));
            $paper['software'] = is_array($software) && !is_wp_error($software) ? $software : array();
            
            $fluorophores = wp_get_object_terms($post_id, 'mh_fluorophore', array('fields' => 'names'));
            $paper['fluorophores'] = is_array($fluorophores) && !is_wp_error($fluorophores) ? $fluorophores : array();
            
            $sample_prep = wp_get_object_terms($post_id, 'mh_sample_prep', array('fields' => 'names'));
            $paper['sample_preparation'] = is_array($sample_prep) && !is_wp_error($sample_prep) ? $sample_prep : array();
            
            $cell_lines = wp_get_object_terms($post_id, 'mh_cell_line', array('fields' => 'names'));
            $paper['cell_lines'] = is_array($cell_lines) && !is_wp_error($cell_lines) ? $cell_lines : array();
            
            // Get JSON meta fields
            $protocols_json = get_post_meta($post_id, '_mh_protocols', true);
            $paper['protocols'] = $protocols_json ? json_decode($protocols_json, true) : array();
            
            $repos_json = get_post_meta($post_id, '_mh_repositories', true);
            $paper['repositories'] = $repos_json ? json_decode($repos_json, true) : array();
            
            // GitHub tools (enriched repo data from scraper v5.1+)
            $github_tools_json = get_post_meta($post_id, '_mh_github_tools', true);
            $paper['github_tools'] = $github_tools_json ? json_decode($github_tools_json, true) : array();
            $paper['github_url'] = get_post_meta($post_id, '_mh_github_url', true);
            
            $papers[] = $paper;
        }
        
        // If no results, try a broader search
        if (empty($papers) && !empty($keywords)) {
            // Try just the first keyword
            $fallback_query = new WP_Query(array(
                'post_type' => 'mh_paper',
                'posts_per_page' => 5,
                's' => $keywords[0],
                'post_status' => 'publish',
                'orderby' => 'meta_value_num',
                'meta_key' => '_mh_citation_count',
                'order' => 'DESC'
            ));
            
            if ($fallback_query->have_posts()) {
                while ($fallback_query->have_posts()) {
                    $fallback_query->the_post();
                    $post_id = get_the_ID();
                    
                    $paper = array(
                        'id' => $post_id,
                        'title' => get_the_title(),
                        'url' => get_permalink(),
                        'doi' => get_post_meta($post_id, '_mh_doi', true),
                        'pmid' => get_post_meta($post_id, '_mh_pubmed_id', true),
                        'authors' => get_post_meta($post_id, '_mh_authors', true),
                        'journal' => get_post_meta($post_id, '_mh_journal', true),
                        'year' => get_post_meta($post_id, '_mh_publication_year', true),
                        'citation_count' => get_post_meta($post_id, '_mh_citation_count', true),
                        'abstract' => get_post_meta($post_id, '_mh_abstract', true),
                        'methods' => get_post_meta($post_id, '_mh_methods', true),
                        'microscope_brand' => get_post_meta($post_id, '_mh_microscope_brand', true),
                        'microscope_model' => get_post_meta($post_id, '_mh_microscope_model', true),
                        'search_score' => 1,
                    );
                    
                    $techniques = wp_get_object_terms($post_id, 'mh_technique', array('fields' => 'names'));
                    $paper['techniques'] = is_array($techniques) && !is_wp_error($techniques) ? $techniques : array();
                    
                    $organisms = wp_get_object_terms($post_id, 'mh_organism', array('fields' => 'names'));
                    $paper['organisms'] = is_array($organisms) && !is_wp_error($organisms) ? $organisms : array();
                    
                    $software = wp_get_object_terms($post_id, 'mh_software', array('fields' => 'names'));
                    $paper['software'] = is_array($software) && !is_wp_error($software) ? $software : array();
                    
                    $fluorophores = wp_get_object_terms($post_id, 'mh_fluorophore', array('fields' => 'names'));
                    $paper['fluorophores'] = is_array($fluorophores) && !is_wp_error($fluorophores) ? $fluorophores : array();
                    
                    $sample_prep = wp_get_object_terms($post_id, 'mh_sample_prep', array('fields' => 'names'));
                    $paper['sample_preparation'] = is_array($sample_prep) && !is_wp_error($sample_prep) ? $sample_prep : array();
                    
                    $cell_lines = wp_get_object_terms($post_id, 'mh_cell_line', array('fields' => 'names'));
                    $paper['cell_lines'] = is_array($cell_lines) && !is_wp_error($cell_lines) ? $cell_lines : array();
                    
                    $protocols_json = get_post_meta($post_id, '_mh_protocols', true);
                    $paper['protocols'] = $protocols_json ? json_decode($protocols_json, true) : array();
                    
                    $repos_json = get_post_meta($post_id, '_mh_repositories', true);
                    $paper['repositories'] = $repos_json ? json_decode($repos_json, true) : array();
                    
                    // GitHub tools (enriched repo data from scraper v5.1+)
                    $github_tools_json = get_post_meta($post_id, '_mh_github_tools', true);
                    $paper['github_tools'] = $github_tools_json ? json_decode($github_tools_json, true) : array();
                    $paper['github_url'] = get_post_meta($post_id, '_mh_github_url', true);
                    
                    $papers[] = $paper;
                }
                wp_reset_postdata();
            }
        }
        
        return $papers;
    }
    
    /**
     * Build detailed paper context for AI prompt
     */
    private function build_paper_context_for_ai($papers) {
        if (empty($papers)) {
            return "\n\n## PAPERS FOUND: NONE
No papers matched your search query. This could mean:
1. Try different search terms (e.g., 'confocal HeLa cells' instead of 'cell imaging')
2. The technique/organism combination may not be in the database yet
3. Ask the user to try the MicroHub search page for more options

You can still provide general guidance based on your microscopy knowledge, but make it clear you don't have specific paper citations for this query.";
        }
        
        $context = "\n\n" . str_repeat("=", 60) . "\n";
        $context .= "## PAPERS FROM MICROHUB DATABASE (" . count($papers) . " results)\n";
        $context .= "IMPORTANT: Use these papers to provide cited, specific guidance.\n";
        $context .= str_repeat("=", 60) . "\n\n";
        
        foreach ($papers as $i => $paper) {
            $num = $i + 1;
            $context .= str_repeat("-", 50) . "\n";
            $context .= "### PAPER {$num}: {$paper['title']}\n";
            $context .= str_repeat("-", 50) . "\n";
            
            // Citation info - formatted for easy citing
            $first_author = 'Unknown';
            if ($paper['authors']) {
                $authors_parts = preg_split('/[,;]/', $paper['authors']);
                $first_author = trim($authors_parts[0]);
                if (count($authors_parts) > 1) $first_author .= ' et al.';
            }
            
            $context .= "**For citing:** \"{$paper['title']}\" ({$first_author}";
            if ($paper['year']) $context .= ", {$paper['year']}";
            if ($paper['journal']) $context .= ", {$paper['journal']}";
            $context .= ")\n";
            
            if ($paper['doi']) $context .= "**DOI:** {$paper['doi']}\n";
            if ($paper['url']) $context .= "**MicroHub URL:** {$paper['url']}\n";
            if ($paper['citation_count']) $context .= "**Times Cited:** {$paper['citation_count']}\n";
            
            $context .= "\n**METADATA FROM PAPER:**\n";
            
            // Techniques and methods
            if (!empty($paper['techniques'])) {
                $context .= "• Techniques: " . implode(', ', $paper['techniques']) . "\n";
            }
            
            // Equipment
            if (!empty($paper['microscope_brand']) || !empty($paper['microscope_model'])) {
                $microscope = trim(($paper['microscope_brand'] ?? '') . ' ' . ($paper['microscope_model'] ?? ''));
                $context .= "• Microscope: {$microscope}\n";
            }
            
            // Organisms
            if (!empty($paper['organisms'])) {
                $context .= "• Organisms: " . implode(', ', $paper['organisms']) . "\n";
            }
            
            // Cell lines
            if (!empty($paper['cell_lines'])) {
                $context .= "• Cell Lines: " . implode(', ', $paper['cell_lines']) . "\n";
            }
            
            // Fluorophores
            if (!empty($paper['fluorophores'])) {
                $context .= "• Fluorophores: " . implode(', ', $paper['fluorophores']) . "\n";
            }
            
            // Sample prep
            if (!empty($paper['sample_preparation'])) {
                $context .= "• Sample Prep: " . implode(', ', $paper['sample_preparation']) . "\n";
            }
            
            // Software
            if (!empty($paper['software'])) {
                $context .= "• Software: " . implode(', ', $paper['software']) . "\n";
            }
            
            // Abstract (this is key for method details)
            if (!empty($paper['abstract'])) {
                $abstract = trim($paper['abstract']);
                // Include more of the abstract since it often contains method details
                $abstract = substr($abstract, 0, 1200);
                $context .= "\n**ABSTRACT (contains method details):**\n{$abstract}";
                if (strlen($paper['abstract']) > 1200) $context .= "...";
                $context .= "\n";
            }
            
            // Methods section if available - VERY valuable
            if (!empty($paper['methods'])) {
                $methods = trim($paper['methods']);
                $methods = substr($methods, 0, 1000);
                $context .= "\n**METHODS SECTION EXCERPT:**\n{$methods}";
                if (strlen($paper['methods']) > 1000) $context .= "...";
                $context .= "\n";
            }
            
            // Linked protocols - HIGHLY valuable for users
            if (!empty($paper['protocols']) && is_array($paper['protocols'])) {
                $context .= "\n**LINKED PROTOCOLS (direct links for user):**\n";
                foreach (array_slice($paper['protocols'], 0, 3) as $protocol) {
                    $name = isset($protocol['name']) ? $protocol['name'] : 'Protocol';
                    $url = isset($protocol['url']) ? $protocol['url'] : '';
                    if ($url) $context .= "  → {$name}: {$url}\n";
                }
            }
            
            // Data repositories
            if (!empty($paper['repositories']) && is_array($paper['repositories'])) {
                $context .= "\n**DATA/CODE REPOSITORIES:**\n";
                foreach (array_slice($paper['repositories'], 0, 3) as $repo) {
                    $name = isset($repo['name']) ? $repo['name'] : 'Repository';
                    $url = isset($repo['url']) ? $repo['url'] : '';
                    if ($url) $context .= "  → {$name}: {$url}\n";
                }
            }
            
            // GitHub Tools (enriched repo data)
            if (!empty($paper['github_tools']) && is_array($paper['github_tools'])) {
                $context .= "\n**GITHUB TOOLS (enriched metadata):**\n";
                foreach (array_slice($paper['github_tools'], 0, 5) as $tool) {
                    $name = isset($tool['full_name']) ? $tool['full_name'] : 'Unknown';
                    $url = isset($tool['url']) ? $tool['url'] : '';
                    $stars = isset($tool['stars']) ? number_format(intval($tool['stars'])) : '0';
                    $lang = isset($tool['language']) ? $tool['language'] : '';
                    $rel = isset($tool['relationship']) ? $tool['relationship'] : 'uses';
                    $health = intval($tool['health_score'] ?? 0);
                    $health_label = $health >= 70 ? 'Active' : ($health >= 40 ? 'Moderate' : 'Low');
                    if (!empty($tool['is_archived'])) $health_label = 'Archived';
                    $context .= "  → {$name} ({$rel}) - ⭐{$stars}";
                    if ($lang) $context .= ", {$lang}";
                    $context .= ", Health: {$health_label}";
                    if ($url) $context .= " - {$url}";
                    $context .= "\n";
                }
            } elseif (!empty($paper['github_url'])) {
                $context .= "\n**GITHUB:** {$paper['github_url']}\n";
            }
            
            $context .= "\n";
        }
        
        $context .= str_repeat("=", 60) . "\n";
        $context .= "END OF PAPER DATA - Now provide your response using these sources.\n";
        $context .= str_repeat("=", 60) . "\n";
        
        return $context;
    }
    
    /**
     * Simplify papers for response (don't need full data for frontend)
     */
    private function simplify_papers_for_response($papers) {
        $simple = array();
        foreach ($papers as $paper) {
            $simple[] = array(
                'id' => $paper['id'],
                'title' => $paper['title'],
                'url' => $paper['url'],
                'authors' => $paper['authors'],
                'year' => $paper['year'],
                'journal' => $paper['journal'],
                'doi' => $paper['doi']
            );
        }
        return $simple;
    }
    
    /**
     * Fallback rules-based AI chat (when no API key)
     */
    private function ai_chat_fallback($message, $context) {
        $msg_lower = strtolower(trim($message));
        $response = array(
            'reply' => '',
            'papers' => array(),
            'type' => 'text'
        );

        // Handle greetings specially
        if ($this->is_greeting($msg_lower)) {
            $response['reply'] = $this->get_greeting_response();
            return $response;
        }

        // Handle stats questions
        if ($this->is_stats_question($msg_lower)) {
            $response['reply'] = $this->get_stats_response();
            $response['type'] = 'stats';
            return $response;
        }

        // SEARCH KNOWLEDGE BASE FIRST
        $kb_results = $this->search_knowledge_base($msg_lower);
        
        // ALSO SEARCH PAPERS
        $paper_results = $this->search_papers_smart($message);
        
        // COMBINE RESULTS INTO RESPONSE
        $response = $this->build_smart_response($message, $kb_results, $paper_results);
        
        return $response;
    }

    /**
     * Search the knowledge base
     */
    private function search_knowledge_base($query, $limit = 3) {
        global $wpdb;
        
        $table = $wpdb->prefix . 'mh_knowledge';
        
        // Check if table exists
        if ($wpdb->get_var("SHOW TABLES LIKE '$table'") !== $table) {
            return array();
        }
        
        $entries = $wpdb->get_results("SELECT * FROM $table");
        if (empty($entries)) return array();
        
        $query_words = array_filter(preg_split('/\s+/', $query), function($w) {
            return strlen($w) >= 3 && !in_array($w, array('the', 'and', 'for', 'what', 'how', 'can', 'you', 'tell', 'about', 'explain', 'describe', 'does', 'mean', 'with', 'use', 'using', 'between', 'difference'));
        });
        
        if (empty($query_words)) {
            $query_words = preg_split('/\s+/', $query);
        }
        
        $scored = array();
        
        foreach ($entries as $entry) {
            $score = 0;
            $content_lower = strtolower($entry->content);
            $title_lower = strtolower($entry->title);
            $keywords_lower = strtolower($entry->keywords);
            
            // Full phrase match
            if (strpos($content_lower, $query) !== false) $score += 10;
            if (strpos($title_lower, $query) !== false) $score += 15;
            
            // Word matches
            foreach ($query_words as $word) {
                if (strpos($title_lower, $word) !== false) $score += 5;
                if (strpos($keywords_lower, $word) !== false) $score += 4;
                $count = substr_count($content_lower, $word);
                $score += min($count, 5);
            }
            
            if ($score > 0) {
                $scored[] = array(
                    'title' => $entry->title,
                    'content' => $entry->content,
                    'score' => $score,
                    'excerpt' => $this->get_smart_excerpt($entry->content, $query_words)
                );
            }
        }
        
        usort($scored, function($a, $b) { return $b['score'] - $a['score']; });
        
        return array_slice($scored, 0, $limit);
    }

    /**
     * Get a smart excerpt around matching content
     */
    private function get_smart_excerpt($content, $query_words, $length = 400) {
        $content = strip_tags($content);
        $content = preg_replace('/\s+/', ' ', $content);
        
        // Try to find a paragraph or section with the query words
        $paragraphs = preg_split('/\n\n+/', $content);
        
        $best_para = '';
        $best_score = 0;
        
        foreach ($paragraphs as $para) {
            $para_lower = strtolower($para);
            $score = 0;
            
            foreach ($query_words as $word) {
                if (strpos($para_lower, $word) !== false) {
                    $score += substr_count($para_lower, $word);
                }
            }
            
            if ($score > $best_score && strlen($para) > 50) {
                $best_score = $score;
                $best_para = $para;
            }
        }
        
        if (empty($best_para)) {
            $best_para = $content;
        }
        
        // Trim to length
        if (strlen($best_para) > $length) {
            // Try to break at sentence
            $trimmed = substr($best_para, 0, $length);
            $last_period = strrpos($trimmed, '.');
            if ($last_period && $last_period > $length * 0.5) {
                $trimmed = substr($trimmed, 0, $last_period + 1);
            } else {
                $trimmed .= '...';
            }
            $best_para = $trimmed;
        }
        
        return trim($best_para);
    }

    /**
     * Smart paper search
     */
    private function search_papers_smart($query) {
        // Extract meaningful search terms
        $search = preg_replace('/\b(find|search|papers?|about|show|me|the|for|on|using|with)\b/i', '', $query);
        $search = trim(preg_replace('/\s+/', ' ', $search));
        
        if (strlen($search) < 2) return array();
        
        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => 5,
            's' => $search,
            'post_status' => 'publish',
        );
        
        $papers_query = new WP_Query($args);
        $papers = array();
        
        if ($papers_query->have_posts()) {
            while ($papers_query->have_posts()) {
                $papers_query->the_post();
                $papers[] = array(
                    'id' => get_the_ID(),
                    'title' => get_the_title(),
                    'url' => get_permalink(),
                    'authors' => get_post_meta(get_the_ID(), '_mh_authors', true),
                    'year' => get_post_meta(get_the_ID(), '_mh_year', true),
                );
            }
            wp_reset_postdata();
        }
        
        return $papers;
    }

    /**
     * Build a smart response combining knowledge and papers
     */
    private function build_smart_response($query, $kb_results, $papers) {
        $response = array(
            'reply' => '',
            'papers' => $papers,
            'type' => 'smart'
        );
        
        // If we have good knowledge base results
        if (!empty($kb_results) && $kb_results[0]['score'] >= 5) {
            $top = $kb_results[0];
            
            // Use the excerpt as the main response
            $response['reply'] = $top['excerpt'];
            
            // If there's a second good result, mention it
            if (count($kb_results) > 1 && $kb_results[1]['score'] >= 3) {
                // Don't add more text, keep it clean
            }
            
            // Add papers if relevant
            if (!empty($papers)) {
                $response['reply'] .= "\n\nI also found some related papers in our database:";
            }
            
            return $response;
        }
        
        // If we have papers but no knowledge
        if (!empty($papers) && empty($kb_results)) {
            $response['reply'] = "I found **" . count($papers) . " papers** that might help:";
            $response['type'] = 'papers';
            return $response;
        }
        
        // If we have both but knowledge is weak
        if (!empty($kb_results) && !empty($papers)) {
            $response['reply'] = $kb_results[0]['excerpt'];
            if (!empty($papers)) {
                $response['reply'] .= "\n\nHere are some related papers:";
            }
            return $response;
        }
        
        // Nothing found - give helpful response
        $response['reply'] = $this->get_helpful_fallback($query);
        $response['type'] = 'fallback';
        
        return $response;
    }

    /**
     * Helpful fallback when nothing found
     */
    private function get_helpful_fallback($query) {
        $suggestions = array(
            "I don't have specific information about that yet. You can:\n\n- Try rephrasing your question\n- Search for papers using the search page\n- Ask about a specific microscopy technique",
            "I'm not sure about that. Try asking about:\n\n- Microscopy techniques (confocal, STED, light sheet)\n- Image analysis software (Fiji, Cellpose, Imaris)\n- Sample preparation methods",
            "I couldn't find information on that topic. I can help with:\n\n- Explaining microscopy methods\n- Finding relevant research papers\n- Recommending analysis tools",
        );
        
        return $suggestions[array_rand($suggestions)];
    }

    /**
     * Check custom training data for a matching response
     */
    private function check_custom_training($msg_lower) {
        // Check custom Q&A pairs first
        $qa_pairs = get_option('microhub_ai_qa_pairs', array());
        foreach ($qa_pairs as $pair) {
            if (empty($pair['keywords']) && empty($pair['answer'])) continue;
            
            $keywords = array_map('trim', explode(',', strtolower($pair['keywords'])));
            $match_count = 0;
            foreach ($keywords as $keyword) {
                if (!empty($keyword) && strpos($msg_lower, $keyword) !== false) {
                    $match_count++;
                }
            }
            // Match if at least one keyword found
            if ($match_count > 0) {
                return array(
                    'reply' => $pair['answer'],
                    'type' => 'custom_qa'
                );
            }
        }

        // Check custom techniques
        $techniques = get_option('microhub_ai_techniques', array());
        if ($this->is_technique_question($msg_lower)) {
            foreach ($techniques as $tech) {
                $keywords = array_map('trim', explode(',', strtolower($tech['keywords'])));
                $keywords[] = strtolower($tech['name']); // Also match the name
                
                foreach ($keywords as $keyword) {
                    if (!empty($keyword) && strpos($msg_lower, $keyword) !== false) {
                        return array(
                            'reply' => "**" . $tech['name'] . "**\n\n" . $tech['description'],
                            'type' => 'technique'
                        );
                    }
                }
            }
        }

        // Check custom software
        $software = get_option('microhub_ai_software', array());
        if ($this->is_software_question($msg_lower)) {
            foreach ($software as $sw) {
                $keywords = array_map('trim', explode(',', strtolower($sw['keywords'])));
                $keywords[] = strtolower($sw['name']);
                
                foreach ($keywords as $keyword) {
                    if (!empty($keyword) && strpos($msg_lower, $keyword) !== false) {
                        return array(
                            'reply' => "**" . $sw['name'] . "**\n\n" . $sw['description'],
                            'type' => 'software'
                        );
                    }
                }
            }
        }

        return null; // No custom match found
    }

    /**
     * Intent detection functions
     */
    private function is_greeting($msg) {
        $greetings = array('hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', 'greetings');
        foreach ($greetings as $g) {
            if (strpos($msg, $g) === 0 || $msg === $g) return true;
        }
        return false;
    }

    private function is_paper_search($msg) {
        $patterns = array('find paper', 'search for', 'look for', 'papers about', 'papers on', 'show me papers', 'find studies', 'research on', 'publications about');
        foreach ($patterns as $p) {
            if (strpos($msg, $p) !== false) return true;
        }
        return false;
    }

    private function is_technique_question($msg) {
        $patterns = array('what is', 'how does', 'explain', 'tell me about', 'how do', 'what are');
        $techniques = array('confocal', 'sted', 'palm', 'storm', 'light sheet', 'two-photon', '2-photon', 'fluorescence', 'electron', 'sem', 'tem', 'cryo', 'super-resolution', 'tirf', 'fret', 'flim', 'sim', 'spinning disk', 'widefield', 'deconvolution', 'expansion');
        
        foreach ($patterns as $p) {
            if (strpos($msg, $p) !== false) {
                foreach ($techniques as $t) {
                    if (strpos($msg, $t) !== false) return true;
                }
            }
        }
        return false;
    }

    private function is_software_question($msg) {
        $keywords = array('software', 'fiji', 'imagej', 'imaris', 'matlab', 'python', 'cellpose', 'ilastik', 'qupath', 'napari', 'analysis tool', 'image analysis', 'program', 'segmentation software');
        foreach ($keywords as $k) {
            if (strpos($msg, $k) !== false) return true;
        }
        return false;
    }

    private function is_protocol_question($msg) {
        $keywords = array('protocol', 'sample prep', 'preparation', 'how to prepare', 'staining', 'fixation', 'mounting', 'clearing', 'immunofluorescence', 'labeling');
        foreach ($keywords as $k) {
            if (strpos($msg, $k) !== false) return true;
        }
        return false;
    }

    private function is_comparison_question($msg) {
        $patterns = array('difference between', 'compare', 'vs', 'versus', 'better', 'which is', 'or');
        foreach ($patterns as $p) {
            if (strpos($msg, $p) !== false) return true;
        }
        return false;
    }

    private function is_recommendation_question($msg) {
        $patterns = array('recommend', 'should i use', 'best for', 'which technique', 'what technique', 'suggest', 'ideal for', 'suitable for');
        foreach ($patterns as $p) {
            if (strpos($msg, $p) !== false) return true;
        }
        return false;
    }

    private function is_stats_question($msg) {
        $patterns = array('how many papers', 'how many studies', 'statistics', 'total papers', 'database size', 'what do you have');
        foreach ($patterns as $p) {
            if (strpos($msg, $p) !== false) return true;
        }
        return false;
    }

    /**
     * Response generators
     */
    private function get_greeting_response() {
        // Check for custom greetings first
        $custom_greetings = get_option('microhub_ai_greetings', array());
        if (!empty($custom_greetings)) {
            return $custom_greetings[array_rand($custom_greetings)];
        }
        
        // Fall back to default greetings
        $bot_name = get_option('microhub_ai_bot_name', 'MicroHub Assistant');
        $greetings = array(
            "Hello! I'm the " . $bot_name . ". I can help you find microscopy papers, explain imaging techniques, and answer questions about methods and protocols. What would you like to know?",
            "Hi there! Welcome to MicroHub. I'm here to help with your microscopy research questions. You can ask me about techniques, find papers, or get protocol guidance. How can I help?",
            "Hey! I'm your microscopy research assistant. Ask me about confocal, STED, light sheet, or any other technique. I can also help you find relevant papers!"
        );
        return $greetings[array_rand($greetings)];
    }

    private function get_help_response() {
        return "I can help you with:\n\n" .
               "**Find Papers** - Ask me to find papers about specific techniques or topics\n" .
               "**Explain Techniques** - Ask about confocal, STED, light sheet, two-photon, etc.\n" .
               "**Compare Methods** - Ask me to compare different microscopy approaches\n" .
               "**Software Advice** - Get recommendations for image analysis tools\n" .
               "**Protocol Guidance** - Learn about sample preparation methods\n\n" .
               "Try asking: \"Find papers about STED microscopy\" or \"What is light sheet microscopy?\"";
    }

    private function get_technique_response($msg) {
        $techniques = array(
            'confocal' => array(
                'name' => 'Confocal Microscopy',
                'description' => "**Confocal microscopy** uses point illumination and a pinhole aperture to eliminate out-of-focus light, creating sharp optical sections.\n\n" .
                    "**Key advantages:**\n" .
                    "- Excellent for 3D imaging of thick samples (up to ~100µm)\n" .
                    "- Great for colocalization studies with multiple fluorophores\n" .
                    "- Can perform z-stacks for 3D reconstruction\n" .
                    "- Widely available and well-established\n\n" .
                    "**Best for:** Fixed and live cell imaging, tissue sections, colocalization studies"
            ),
            'sted' => array(
                'name' => 'STED Microscopy',
                'description' => "**STED (Stimulated Emission Depletion)** is a super-resolution technique that achieves resolution beyond the diffraction limit.\n\n" .
                    "**How it works:** A donut-shaped depletion laser selectively switches off fluorophores around the excitation spot, effectively shrinking the point spread function.\n\n" .
                    "**Resolution:** ~30-80nm (vs ~200nm for confocal)\n\n" .
                    "**Best for:** Imaging synapses, cytoskeleton details, protein clusters, and nanoscale structures"
            ),
            'light sheet' => array(
                'name' => 'Light Sheet Microscopy',
                'description' => "**Light sheet microscopy** illuminates samples with a thin sheet of light perpendicular to the detection axis.\n\n" .
                    "**Key advantages:**\n" .
                    "- Very low phototoxicity - ideal for long-term live imaging\n" .
                    "- Fast acquisition of large volumes\n" .
                    "- Excellent for cleared tissues and whole organisms\n\n" .
                    "**Best for:** Developmental biology, organoids, cleared tissues, long-term live imaging"
            ),
            'two-photon' => array(
                'name' => 'Two-Photon Microscopy',
                'description' => "**Two-photon microscopy** uses infrared light and nonlinear excitation for deep tissue imaging.\n\n" .
                    "**Key advantages:**\n" .
                    "- Deep tissue penetration (500µm - 1mm)\n" .
                    "- Reduced photodamage and photobleaching\n" .
                    "- Intrinsic optical sectioning\n\n" .
                    "**Best for:** In vivo brain imaging, deep tissue imaging, live animal studies"
            ),
            '2-photon' => array(
                'name' => 'Two-Photon Microscopy',
                'description' => "**Two-photon microscopy** uses infrared light and nonlinear excitation for deep tissue imaging.\n\n" .
                    "**Key advantages:**\n" .
                    "- Deep tissue penetration (500µm - 1mm)\n" .
                    "- Reduced photodamage and photobleaching\n" .
                    "- Intrinsic optical sectioning\n\n" .
                    "**Best for:** In vivo brain imaging, deep tissue imaging, live animal studies"
            ),
            'palm' => array(
                'name' => 'PALM (Photoactivated Localization Microscopy)',
                'description' => "**PALM** achieves super-resolution by localizing individual photoactivatable fluorescent proteins.\n\n" .
                    "**How it works:** Stochastically activates sparse subsets of fluorophores, precisely localizes them, then repeats to build up a super-resolved image.\n\n" .
                    "**Resolution:** ~20-50nm\n\n" .
                    "**Best for:** Single molecule studies, protein organization, membrane structure"
            ),
            'storm' => array(
                'name' => 'STORM (Stochastic Optical Reconstruction Microscopy)',
                'description' => "**STORM** uses photoswitchable dyes for single-molecule localization super-resolution imaging.\n\n" .
                    "**How it works:** Similar to PALM but uses organic dyes that can be switched between fluorescent and dark states.\n\n" .
                    "**Resolution:** ~20-50nm\n\n" .
                    "**Best for:** Multicolor super-resolution, cytoskeleton imaging, chromatin structure"
            ),
            'fret' => array(
                'name' => 'FRET (Förster Resonance Energy Transfer)',
                'description' => "**FRET** measures molecular interactions at nanometer distances by detecting energy transfer between fluorophores.\n\n" .
                    "**How it works:** When donor and acceptor fluorophores are within ~10nm, excited donor transfers energy to acceptor.\n\n" .
                    "**Best for:** Protein-protein interactions, conformational changes, biosensor imaging"
            ),
            'flim' => array(
                'name' => 'FLIM (Fluorescence Lifetime Imaging)',
                'description' => "**FLIM** measures the fluorescence decay time rather than intensity.\n\n" .
                    "**Key advantages:**\n" .
                    "- Independent of fluorophore concentration\n" .
                    "- Sensitive to molecular environment (pH, ion concentration)\n" .
                    "- Can be combined with FRET (FLIM-FRET)\n\n" .
                    "**Best for:** Metabolic imaging, FRET measurements, environmental sensing"
            ),
            'tirf' => array(
                'name' => 'TIRF (Total Internal Reflection Fluorescence)',
                'description' => "**TIRF** illuminates only a thin (~100nm) layer at the coverslip surface using evanescent waves.\n\n" .
                    "**Key advantages:**\n" .
                    "- Excellent signal-to-noise for surface events\n" .
                    "- Very thin optical section\n" .
                    "- Great for single molecule studies\n\n" .
                    "**Best for:** Membrane dynamics, vesicle fusion, single molecule tracking"
            ),
            'spinning disk' => array(
                'name' => 'Spinning Disk Confocal',
                'description' => "**Spinning disk confocal** uses a rotating disk with multiple pinholes for fast confocal imaging.\n\n" .
                    "**Key advantages:**\n" .
                    "- Much faster than point-scanning confocal\n" .
                    "- Lower phototoxicity\n" .
                    "- Good for live cell imaging\n\n" .
                    "**Best for:** Fast live cell imaging, high-speed 3D acquisition"
            ),
            'expansion' => array(
                'name' => 'Expansion Microscopy',
                'description' => "**Expansion microscopy** physically enlarges biological specimens by embedding them in a swellable polymer.\n\n" .
                    "**How it works:** Samples are embedded in a gel that expands ~4x when hydrated, effectively increasing resolution.\n\n" .
                    "**Key advantages:**\n" .
                    "- Achieves super-resolution on conventional microscopes\n" .
                    "- Compatible with standard fluorophores\n" .
                    "- Good for large-scale imaging\n\n" .
                    "**Best for:** Nanoscale imaging without specialized equipment, connectomics"
            ),
            'sem' => array(
                'name' => 'SEM (Scanning Electron Microscopy)',
                'description' => "**SEM** scans a focused electron beam across the sample surface to create detailed topographic images.\n\n" .
                    "**Resolution:** ~1-10nm\n\n" .
                    "**Key features:**\n" .
                    "- Excellent depth of field\n" .
                    "- Surface topology imaging\n" .
                    "- Can be combined with EDX for elemental analysis\n\n" .
                    "**Best for:** Surface structure, materials science, cell surface features"
            ),
            'tem' => array(
                'name' => 'TEM (Transmission Electron Microscopy)',
                'description' => "**TEM** transmits electrons through thin samples to reveal internal ultrastructure.\n\n" .
                    "**Resolution:** ~0.1-0.2nm (atomic scale possible)\n\n" .
                    "**Key features:**\n" .
                    "- Highest resolution imaging available\n" .
                    "- Reveals internal cellular structure\n" .
                    "- Requires thin sections (~70-100nm)\n\n" .
                    "**Best for:** Ultrastructure, organelle morphology, virus structure"
            ),
            'cryo' => array(
                'name' => 'Cryo-Electron Microscopy',
                'description' => "**Cryo-EM** images samples preserved at cryogenic temperatures without chemical fixation.\n\n" .
                    "**Key advantages:**\n" .
                    "- Preserves native structure\n" .
                    "- No staining artifacts\n" .
                    "- Can achieve near-atomic resolution\n\n" .
                    "**Best for:** Protein structure determination, macromolecular complexes, native cell architecture"
            ),
            'super-resolution' => array(
                'name' => 'Super-Resolution Microscopy',
                'description' => "**Super-resolution microscopy** refers to techniques that overcome the ~200nm diffraction limit of light.\n\n" .
                    "**Main techniques:**\n" .
                    "- **STED:** Uses depletion laser (~30-80nm resolution)\n" .
                    "- **PALM/STORM:** Single molecule localization (~20-50nm)\n" .
                    "- **SIM:** Structured illumination (~100nm, 2x improvement)\n\n" .
                    "**Best for:** Nanoscale cellular structures, protein organization, chromatin imaging"
            ),
        );

        foreach ($techniques as $key => $info) {
            if (strpos($msg, $key) !== false) {
                return $info['description'];
            }
        }

        return "I can explain many microscopy techniques including confocal, STED, PALM, STORM, light sheet, two-photon, TIRF, FLIM, expansion microscopy, and electron microscopy. Which one would you like to learn about?";
    }

    private function get_software_response($msg) {
        $software = array(
            'fiji' => "**Fiji/ImageJ** is the most widely used open-source image analysis platform.\n\n" .
                "**Key features:**\n" .
                "- Huge plugin ecosystem\n" .
                "- Macro scripting for automation\n" .
                "- Supports almost all image formats\n" .
                "- Active community support\n\n" .
                "**Best for:** General image processing, measurements, batch processing\n" .
                "**Website:** fiji.sc",
            'imagej' => "**Fiji/ImageJ** is the most widely used open-source image analysis platform.\n\n" .
                "**Key features:**\n" .
                "- Huge plugin ecosystem\n" .
                "- Macro scripting for automation\n" .
                "- Supports almost all image formats\n\n" .
                "**Best for:** General image processing, measurements, batch processing",
            'cellpose' => "**Cellpose** is a deep learning-based cell segmentation tool.\n\n" .
                "**Key features:**\n" .
                "- Works out-of-the-box for many cell types\n" .
                "- Can be fine-tuned on your data\n" .
                "- GPU accelerated\n" .
                "- Python-based with GUI available\n\n" .
                "**Best for:** Cell and nucleus segmentation\n" .
                "**Website:** cellpose.org",
            'ilastik' => "**ilastik** uses interactive machine learning for image classification and segmentation.\n\n" .
                "**Key features:**\n" .
                "- User-friendly GUI\n" .
                "- Train classifiers by painting examples\n" .
                "- Object tracking capabilities\n\n" .
                "**Best for:** Pixel classification, object segmentation, tracking",
            'imaris' => "**Imaris** is a commercial 3D/4D visualization and analysis platform.\n\n" .
                "**Key features:**\n" .
                "- Excellent 3D rendering\n" .
                "- Surface and spot detection\n" .
                "- Tracking and lineage analysis\n" .
                "- Filament tracing\n\n" .
                "**Best for:** 3D visualization, tracking, complex analysis",
            'qupath' => "**QuPath** is open-source software for digital pathology and whole slide images.\n\n" .
                "**Key features:**\n" .
                "- Handles very large images efficiently\n" .
                "- Built-in cell detection\n" .
                "- Machine learning classification\n" .
                "- Biomarker analysis\n\n" .
                "**Best for:** Pathology, tissue analysis, whole slide imaging",
            'napari' => "**napari** is a modern Python-based multi-dimensional image viewer.\n\n" .
                "**Key features:**\n" .
                "- Fast rendering of large datasets\n" .
                "- Plugin ecosystem\n" .
                "- Great for developers\n" .
                "- Supports nD data\n\n" .
                "**Best for:** Large data visualization, Python workflows",
        );

        foreach ($software as $key => $info) {
            if (strpos($msg, $key) !== false) {
                return $info;
            }
        }

        // General software question
        return "**Popular image analysis software:**\n\n" .
            "**Free/Open-source:**\n" .
            "- **Fiji/ImageJ** - General purpose, huge plugin ecosystem\n" .
            "- **Cellpose** - AI-powered cell segmentation\n" .
            "- **ilastik** - Interactive machine learning\n" .
            "- **QuPath** - Digital pathology\n" .
            "- **napari** - Python-based viewer\n\n" .
            "**Commercial:**\n" .
            "- **Imaris** - 3D visualization and analysis\n" .
            "- **Huygens** - Deconvolution\n" .
            "- **Aivia** - AI-assisted analysis\n\n" .
            "What type of analysis do you need? I can give more specific recommendations.";
    }

    private function get_protocol_response($msg) {
        if (strpos($msg, 'clearing') !== false || strpos($msg, 'clarity') !== false) {
            return "**Tissue Clearing Protocols:**\n\n" .
                "Popular methods include:\n" .
                "- **CLARITY** - Lipid removal with hydrogel embedding\n" .
                "- **iDISCO** - Organic solvent-based, good for immunostaining\n" .
                "- **CUBIC** - Aqueous-based, preserves fluorescent proteins\n" .
                "- **uDISCO** - Whole-body clearing possible\n\n" .
                "The best method depends on your sample and labeling strategy. Would you like me to find papers with specific clearing protocols?";
        }
        if (strpos($msg, 'immunofluorescence') !== false || strpos($msg, 'immunostain') !== false) {
            return "**Immunofluorescence Protocol Tips:**\n\n" .
                "**Key steps:**\n" .
                "1. **Fixation** - PFA (4%) for most applications, methanol for some antigens\n" .
                "2. **Permeabilization** - Triton X-100 (0.1-0.5%) or saponin\n" .
                "3. **Blocking** - BSA, serum, or commercial blockers\n" .
                "4. **Primary antibody** - Optimize concentration and incubation time\n" .
                "5. **Secondary antibody** - Match to primary species\n" .
                "6. **Mounting** - Use anti-fade mounting medium\n\n" .
                "Would you like me to find papers with specific IF protocols?";
        }
        if (strpos($msg, 'live cell') !== false || strpos($msg, 'live imaging') !== false) {
            return "**Live Cell Imaging Tips:**\n\n" .
                "**Environmental control:**\n" .
                "- Temperature: 37°C for mammalian cells\n" .
                "- CO2: 5% for buffered media\n" .
                "- Humidity: Prevent evaporation\n\n" .
                "**Minimize phototoxicity:**\n" .
                "- Use lowest laser power possible\n" .
                "- Reduce exposure time\n" .
                "- Consider spinning disk or light sheet\n" .
                "- Use photostable fluorophores\n\n" .
                "Would you like recommendations for specific live imaging applications?";
        }

        return "I can help with protocols for:\n\n" .
            "- **Sample fixation** - PFA, glutaraldehyde, methanol\n" .
            "- **Immunofluorescence** - Staining and labeling\n" .
            "- **Tissue clearing** - CLARITY, iDISCO, CUBIC\n" .
            "- **Live cell imaging** - Environmental control, reducing phototoxicity\n" .
            "- **Mounting** - Media selection for different applications\n\n" .
            "What type of sample preparation do you need help with?";
    }

    private function get_comparison_response($msg) {
        if ((strpos($msg, 'confocal') !== false && strpos($msg, 'widefield') !== false) ||
            (strpos($msg, 'confocal') !== false && strpos($msg, 'wide-field') !== false)) {
            return "**Confocal vs Widefield Microscopy:**\n\n" .
                "| Feature | Widefield | Confocal |\n" .
                "|---------|-----------|----------|\n" .
                "| Optical sectioning | No | Yes |\n" .
                "| Out-of-focus light | Present | Rejected |\n" .
                "| Speed | Fast | Slower |\n" .
                "| Phototoxicity | Lower | Higher |\n" .
                "| Best for | Thin samples | Thick samples, 3D |\n\n" .
                "**Use widefield** for: thin samples, fast imaging, low phototoxicity needs\n" .
                "**Use confocal** for: thick samples, 3D imaging, colocalization";
        }
        if (strpos($msg, 'confocal') !== false && strpos($msg, 'light sheet') !== false) {
            return "**Confocal vs Light Sheet Microscopy:**\n\n" .
                "| Feature | Confocal | Light Sheet |\n" .
                "|---------|----------|-------------|\n" .
                "| Phototoxicity | Moderate | Very low |\n" .
                "| Speed | Slower | Very fast |\n" .
                "| Sample size | Small-medium | Large OK |\n" .
                "| Resolution | High | Moderate |\n" .
                "| Long-term imaging | Limited | Excellent |\n\n" .
                "**Use confocal** for: high resolution, smaller samples\n" .
                "**Use light sheet** for: large samples, long-term live imaging, cleared tissue";
        }
        if (strpos($msg, 'sted') !== false && strpos($msg, 'palm') !== false ||
            strpos($msg, 'sted') !== false && strpos($msg, 'storm') !== false) {
            return "**STED vs PALM/STORM:**\n\n" .
                "| Feature | STED | PALM/STORM |\n" .
                "|---------|------|------------|\n" .
                "| Resolution | 30-80nm | 20-50nm |\n" .
                "| Speed | Fast | Slow (minutes) |\n" .
                "| Live imaging | Yes | Difficult |\n" .
                "| Fluorophore choice | Limited | Wide |\n" .
                "| Equipment cost | Very high | High |\n\n" .
                "**Use STED** for: live super-resolution, faster imaging\n" .
                "**Use PALM/STORM** for: highest resolution, single molecule studies";
        }

        return "I can compare various microscopy techniques. Try asking:\n" .
            "- \"Difference between confocal and widefield\"\n" .
            "- \"Compare confocal and light sheet\"\n" .
            "- \"STED vs PALM/STORM\"\n" .
            "- \"Two-photon vs confocal for deep imaging\"\n\n" .
            "What techniques would you like me to compare?";
    }

    private function get_recommendation_response($msg) {
        if (strpos($msg, 'live cell') !== false || strpos($msg, 'live imaging') !== false) {
            return "**Recommendations for live cell imaging:**\n\n" .
                "**Best techniques:**\n" .
                "1. **Spinning disk confocal** - Fast, gentle, good for most applications\n" .
                "2. **Light sheet** - Very gentle, excellent for long-term imaging\n" .
                "3. **Widefield + deconvolution** - Simple and effective for thin samples\n" .
                "4. **TIRF** - Best for membrane/surface events\n\n" .
                "**Key considerations:**\n" .
                "- Minimize light exposure\n" .
                "- Use bright, photostable fluorophores\n" .
                "- Environmental control (temp, CO2, humidity)";
        }
        if (strpos($msg, 'deep tissue') !== false || strpos($msg, 'thick tissue') !== false || strpos($msg, 'deep imaging') !== false) {
            return "**Recommendations for deep tissue imaging:**\n\n" .
                "1. **Two-photon microscopy** - Best for live deep imaging (up to 1mm)\n" .
                "2. **Light sheet + clearing** - Great for fixed, cleared samples\n" .
                "3. **Confocal + clearing** - Good for moderate depth with clearing\n\n" .
                "**Tips:**\n" .
                "- Use far-red/NIR fluorophores for better penetration\n" .
                "- Consider tissue clearing for fixed samples\n" .
                "- Use glycerol or silicone objectives for refractive index matching";
        }
        if (strpos($msg, 'super-resolution') !== false || strpos($msg, 'nanoscale') !== false) {
            return "**Super-resolution technique recommendations:**\n\n" .
                "- **STED:** Best for live imaging, faster acquisition\n" .
                "- **PALM/STORM:** Highest resolution, single molecule quantification\n" .
                "- **SIM:** Good balance of speed and resolution improvement\n" .
                "- **Expansion microscopy:** Super-resolution on regular microscopes\n\n" .
                "**Consider:**\n" .
                "- Do you need live imaging? → STED or fast SIM\n" .
                "- Maximum resolution needed? → PALM/STORM\n" .
                "- Limited budget? → Expansion microscopy";
        }

        return "I can recommend techniques for:\n\n" .
            "- **Live cell imaging** - Spinning disk, light sheet, widefield\n" .
            "- **Deep tissue** - Two-photon, light sheet with clearing\n" .
            "- **Super-resolution** - STED, PALM/STORM, SIM, expansion\n" .
            "- **3D imaging** - Confocal, light sheet\n" .
            "- **Fast imaging** - Spinning disk, widefield, resonant scanning\n\n" .
            "What application do you need a recommendation for?";
    }

    private function get_stats_response() {
        global $wpdb;
        
        $total_papers = wp_count_posts('mh_paper')->publish;
        
        // Get technique counts
        $techniques = wp_count_terms('mh_technique');
        
        // Get papers with protocols
        $with_protocols = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != '' AND meta_value != '[]'");
        
        // Get papers with GitHub
        $with_github = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''");
        
        // Get papers with GitHub tools (enriched)
        $with_github_tools = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_tools' AND meta_value != '' AND meta_value != '[]'");
        
        return "**MicroHub Database Statistics:**\n\n" .
            "- **Total papers:** " . number_format($total_papers) . "\n" .
            "- **Techniques covered:** " . number_format($techniques) . "\n" .
            "- **Papers with protocols:** " . number_format($with_protocols) . "\n" .
            "- **Papers with GitHub code:** " . number_format($with_github) . "\n" .
            "- **Papers with GitHub tools (enriched):** " . number_format($with_github_tools) . "\n\n" .
            "You can search all papers using the search page, or visit the GitHub Tools page for an overview of open-source tools used across the database!";
    }

    /**
     * Search papers for chat response
     */
    private function search_papers_for_chat($query) {
        $search_terms = preg_replace('/\b(find|search|papers?|about|on|the|for|me|show|studies|research|publications?)\b/i', '', $query);
        $search_terms = trim(preg_replace('/\s+/', ' ', $search_terms));
        
        if (strlen($search_terms) < 2) {
            return array(
                'reply' => "What topic would you like me to search for? Try asking about a specific technique, method, or subject.",
                'papers' => array()
            );
        }
        
        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => 5,
            's' => $search_terms,
            'post_status' => 'publish',
        );
        
        $papers_query = new WP_Query($args);
        $papers = array();
        
        if ($papers_query->have_posts()) {
            while ($papers_query->have_posts()) {
                $papers_query->the_post();
                $papers[] = array(
                    'id' => get_the_ID(),
                    'title' => get_the_title(),
                    'url' => get_permalink(),
                    'authors' => get_post_meta(get_the_ID(), '_mh_authors', true),
                    'year' => get_post_meta(get_the_ID(), '_mh_year', true),
                    'journal' => get_post_meta(get_the_ID(), '_mh_journal', true),
                );
            }
            wp_reset_postdata();
        }
        
        if (!empty($papers)) {
            $reply = "I found **" . count($papers) . " papers** about \"" . esc_html($search_terms) . "\":\n\n";
            foreach ($papers as $i => $paper) {
                $reply .= ($i + 1) . ". **" . $paper['title'] . "**";
                if ($paper['year']) $reply .= " (" . $paper['year'] . ")";
                $reply .= "\n";
            }
            $reply .= "\nClick on any paper below to view details, or refine your search.";
        } else {
            $reply = "I couldn't find papers matching \"" . esc_html($search_terms) . "\". Try:\n" .
                "- Using different keywords\n" .
                "- Searching for a technique name (confocal, STED, etc.)\n" .
                "- Being more specific or more general";
        }
        
        return array(
            'reply' => $reply,
            'papers' => $papers
        );
    }

    /**
     * Get related papers for a technique
     */
    private function get_related_papers($msg, $limit = 3) {
        $techniques = array('confocal', 'sted', 'palm', 'storm', 'light sheet', 'two-photon', 'tirf', 'fret', 'flim', 'sem', 'tem', 'cryo', 'expansion', 'spinning disk');
        
        $search_term = '';
        foreach ($techniques as $tech) {
            if (strpos($msg, $tech) !== false) {
                $search_term = $tech;
                break;
            }
        }
        
        if (!$search_term) return array();
        
        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => $limit,
            's' => $search_term,
            'post_status' => 'publish',
        );
        
        $papers_query = new WP_Query($args);
        $papers = array();
        
        if ($papers_query->have_posts()) {
            while ($papers_query->have_posts()) {
                $papers_query->the_post();
                $papers[] = array(
                    'id' => get_the_ID(),
                    'title' => get_the_title(),
                    'url' => get_permalink(),
                    'year' => get_post_meta(get_the_ID(), '_mh_year', true),
                );
            }
            wp_reset_postdata();
        }
        
        return $papers;
    }

    /**
     * Get papers with protocols
     */
    private function get_papers_with_protocols($msg, $limit = 3) {
        global $wpdb;
        
        $paper_ids = $wpdb->get_col("
            SELECT DISTINCT post_id 
            FROM {$wpdb->postmeta} 
            WHERE meta_key = '_mh_protocols' 
            AND meta_value != '' 
            AND meta_value != '[]'
            LIMIT $limit
        ");
        
        if (empty($paper_ids)) return array();
        
        $papers = array();
        foreach ($paper_ids as $id) {
            $papers[] = array(
                'id' => $id,
                'title' => get_the_title($id),
                'url' => get_permalink($id),
                'year' => get_post_meta($id, '_mh_year', true),
            );
        }
        
        return $papers;
    }

    /**
     * Legacy fallback response (kept for compatibility)
     */
    private function get_fallback_ai_response($message) {
        return $this->get_help_response();
    }

    /**
     * Handle comments
     */
    public function handle_comments($request) {
        $paper_id = intval($request->get_param('id'));

        if ($request->get_method() === 'POST') {
            if (!is_user_logged_in()) {
                return new WP_Error('unauthorized', 'Please log in to comment', array('status' => 401));
            }

            $content = sanitize_textarea_field($request->get_param('content'));
            if (!$content) {
                return new WP_Error('invalid_content', 'Comment content is required', array('status' => 400));
            }

            $user = wp_get_current_user();
            $comment_id = wp_insert_comment(array(
                'comment_post_ID' => $paper_id,
                'comment_content' => $content,
                'comment_author' => $user->display_name,
                'comment_author_email' => $user->user_email,
                'user_id' => $user->ID,
                'comment_approved' => 1,
            ));

            return array('success' => true, 'comment_id' => $comment_id);
        }

        // GET comments
        $comments = get_comments(array(
            'post_id' => $paper_id,
            'status' => 'approve',
            'order' => 'DESC',
        ));

        return array_map(function($comment) {
            return array(
                'id' => $comment->comment_ID,
                'author' => $comment->comment_author,
                'content' => $comment->comment_content,
                'date' => $comment->comment_date,
            );
        }, $comments);
    }

    /**
     * Submit paper
     */
    public function submit_paper($request) {
        $doi = sanitize_text_field($request->get_param('doi'));
        if (!$doi) {
            return new WP_Error('invalid_doi', 'DOI is required', array('status' => 400));
        }

        // Check if DOI already exists
        global $wpdb;
        $existing = $wpdb->get_var($wpdb->prepare(
            "SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = '_mh_doi' AND meta_value = %s LIMIT 1",
            $doi
        ));

        if ($existing) {
            return new WP_Error('duplicate', 'This paper already exists', array('status' => 409));
        }

        // Create post
        $post_id = wp_insert_post(array(
            'post_type' => 'mh_paper',
            'post_title' => 'Paper: ' . $doi,
            'post_status' => 'pending',
            'post_author' => get_current_user_id(),
        ));

        if ($post_id) {
            update_post_meta($post_id, '_mh_doi', $doi);
            
            if ($request->get_param('github')) {
                update_post_meta($post_id, '_mh_github_url', esc_url($request->get_param('github')));
            }
            if ($request->get_param('protocol')) {
                update_post_meta($post_id, '_mh_protocols', json_encode(array(array('url' => esc_url($request->get_param('protocol'))))));
            }
            if ($request->get_param('data')) {
                update_post_meta($post_id, '_mh_repositories', json_encode(array(array('url' => esc_url($request->get_param('data'))))));
            }
            if ($request->get_param('facility')) {
                update_post_meta($post_id, '_mh_facility', sanitize_text_field($request->get_param('facility')));
            }

            return array('success' => true, 'id' => $post_id);
        }

        return new WP_Error('failed', 'Failed to create paper', array('status' => 500));
    }
}
