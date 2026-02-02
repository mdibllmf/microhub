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
            'thumbnail_url' => $thumbnail_url,
            'figure_urls' => $figure_urls_json ? json_decode($figure_urls_json, true) : array(),
            'techniques' => wp_get_post_terms($id, 'mh_technique', array('fields' => 'names')),
            'microscopes' => wp_get_post_terms($id, 'mh_microscope', array('fields' => 'names')),
            'organisms' => wp_get_post_terms($id, 'mh_organism', array('fields' => 'names')),
            'software' => wp_get_post_terms($id, 'mh_software', array('fields' => 'names')),
            'protocols' => $protocols_json ? json_decode($protocols_json, true) : array(),
            'repositories' => $repos_json ? json_decode($repos_json, true) : array(),
            'rrids' => $rrids_json ? json_decode($rrids_json, true) : array(),
            'comments_count' => get_comments_number($id),
        );
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
     * Smart AI Chat - Uses paper database and built-in knowledge
     * Checks custom training data first, then falls back to built-in responses
     */
    public function ai_chat($request) {
        $message = sanitize_text_field($request->get_param('message'));
        $context = sanitize_text_field($request->get_param('context'));

        if (!$message) {
            return new WP_Error('invalid_message', 'Message is required', array('status' => 400));
        }

        $msg_lower = strtolower($message);
        $response = array(
            'reply' => '',
            'papers' => array(),
            'type' => 'text'
        );

        // FIRST: Check custom training data
        $custom_response = $this->check_custom_training($msg_lower);
        if ($custom_response) {
            $response['reply'] = $custom_response['reply'];
            $response['type'] = $custom_response['type'];
            // Add related papers if it was a technique or software question
            if ($custom_response['type'] === 'technique' || $custom_response['type'] === 'software') {
                $response['papers'] = $this->get_related_papers($msg_lower, 3);
            }
            return $response;
        }

        // THEN: Use built-in responses
        // Detect intent and generate response
        if ($this->is_greeting($msg_lower)) {
            $response['reply'] = $this->get_greeting_response();
        }
        elseif ($this->is_paper_search($msg_lower)) {
            $response = $this->search_papers_for_chat($message);
            $response['type'] = 'papers';
        }
        elseif ($this->is_technique_question($msg_lower)) {
            $response['reply'] = $this->get_technique_response($msg_lower);
            $response['papers'] = $this->get_related_papers($msg_lower, 3);
            $response['type'] = 'technique';
        }
        elseif ($this->is_software_question($msg_lower)) {
            $response['reply'] = $this->get_software_response($msg_lower);
            $response['type'] = 'software';
        }
        elseif ($this->is_protocol_question($msg_lower)) {
            $response['reply'] = $this->get_protocol_response($msg_lower);
            $response['papers'] = $this->get_papers_with_protocols($msg_lower, 3);
            $response['type'] = 'protocol';
        }
        elseif ($this->is_comparison_question($msg_lower)) {
            $response['reply'] = $this->get_comparison_response($msg_lower);
            $response['type'] = 'comparison';
        }
        elseif ($this->is_recommendation_question($msg_lower)) {
            $response['reply'] = $this->get_recommendation_response($msg_lower);
            $response['type'] = 'recommendation';
        }
        elseif ($this->is_stats_question($msg_lower)) {
            $response['reply'] = $this->get_stats_response();
            $response['type'] = 'stats';
        }
        else {
            // Default: try to find relevant papers
            $response = $this->search_papers_for_chat($message);
            if (empty($response['papers'])) {
                $response['reply'] = $this->get_help_response();
            }
            $response['type'] = 'search';
        }

        return $response;
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
    }        return $response;
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
        
        return "**MicroHub Database Statistics:**\n\n" .
            "- **Total papers:** " . number_format($total_papers) . "\n" .
            "- **Techniques covered:** " . number_format($techniques) . "\n" .
            "- **Papers with protocols:** " . number_format($with_protocols) . "\n" .
            "- **Papers with GitHub code:** " . number_format($with_github) . "\n\n" .
            "You can search all papers using the search page, or ask me to find papers on specific topics!";
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
