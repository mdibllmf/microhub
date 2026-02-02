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
     * AI Chat proxy (for Gemini API)
     */
    public function ai_chat($request) {
        $message = sanitize_text_field($request->get_param('message'));
        $context = sanitize_text_field($request->get_param('context'));

        if (!$message) {
            return new WP_Error('invalid_message', 'Message is required', array('status' => 400));
        }

        // Get API key from settings
        $api_key = get_option('microhub_gemini_api_key', '');

        if (!$api_key || strlen(trim($api_key)) < 10) {
            // Return a helpful fallback response with flag
            return array(
                'reply' => $this->get_fallback_ai_response($message),
                'fallback' => true,
                'debug' => 'No API key configured'
            );
        }

        // Build the system instruction
        $system_instruction = 'You are a helpful microscopy research assistant for MicroHub. Help users understand microscopy techniques, find papers, and answer questions about imaging methods, protocols, and data analysis. Be concise, helpful, and accurate. Format responses with markdown for readability.';
        
        if ($context) {
            $system_instruction .= ' ' . $context;
        }

        // Call Gemini API (using gemini-2.0-flash for best results)
        $api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' . $api_key;
        
        $response = wp_remote_post($api_url, array(
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode(array(
                'system_instruction' => array(
                    'parts' => array(
                        array('text' => $system_instruction)
                    )
                ),
                'contents' => array(
                    array(
                        'role' => 'user',
                        'parts' => array(
                            array('text' => $message),
                        ),
                    ),
                ),
                'generationConfig' => array(
                    'temperature' => 0.7,
                    'maxOutputTokens' => 2048,
                ),
            )),
            'timeout' => 30,
        ));

        if (is_wp_error($response)) {
            error_log('MicroHub Gemini Error: ' . $response->get_error_message());
            return array(
                'reply' => $this->get_fallback_ai_response($message),
                'fallback' => true,
                'debug' => 'Connection error: ' . $response->get_error_message()
            );
        }

        $status_code = wp_remote_retrieve_response_code($response);
        $body = json_decode(wp_remote_retrieve_body($response), true);

        // Log any errors for debugging
        if ($status_code !== 200) {
            error_log('MicroHub Gemini API Error: Status ' . $status_code . ' - ' . print_r($body, true));
            $error_msg = isset($body['error']['message']) ? $body['error']['message'] : 'API returned status ' . $status_code;
            return array(
                'reply' => $this->get_fallback_ai_response($message),
                'fallback' => true,
                'debug' => $error_msg
            );
        }

        // Extract reply from response
        $reply = '';
        if (isset($body['candidates'][0]['content']['parts'][0]['text'])) {
            $reply = $body['candidates'][0]['content']['parts'][0]['text'];
        } elseif (isset($body['error'])) {
            error_log('MicroHub Gemini Error: ' . print_r($body['error'], true));
            return array(
                'reply' => $this->get_fallback_ai_response($message),
                'fallback' => true,
                'debug' => 'API error in response'
            );
        } else {
            return array(
                'reply' => $this->get_fallback_ai_response($message),
                'fallback' => true,
                'debug' => 'Unexpected response format'
            );
        }

        return array('reply' => $reply, 'fallback' => false);
    }

    /**
     * Fallback AI response
     */
    private function get_fallback_ai_response($message) {
        $msg = strtolower($message);

        if (strpos($msg, 'confocal') !== false) {
            return 'Confocal microscopy uses point illumination and a spatial pinhole to eliminate out-of-focus light, producing sharp optical sections. It\'s ideal for 3D imaging of thick specimens. Use the technique filter to find confocal papers!';
        } elseif (strpos($msg, 'fret') !== false) {
            return 'FRET (Förster Resonance Energy Transfer) measures molecular interactions at the nanometer scale. It\'s widely used for studying protein-protein interactions in live cells. Filter by FRET technique to explore relevant papers.';
        } elseif (strpos($msg, 'sted') !== false || strpos($msg, 'super-resolution') !== false) {
            return 'STED microscopy achieves nanometer resolution by using a depletion laser to selectively switch off fluorophores. It\'s a powerful super-resolution technique. Check out our super-resolution papers!';
        } elseif (strpos($msg, 'protocol') !== false) {
            return 'You can find and share protocols in our repository! Use the "Has Protocols" quick filter, or upload your own protocol to help the community.';
        } elseif (strpos($msg, 'github') !== false) {
            return 'Many papers are linked to GitHub repositories with analysis code and workflows. Use the "GitHub" filter to find them, and check the sidebar for recent repositories!';
        }

        return 'I\'m here to help with microscopy research! Ask me about techniques (confocal, STED, FRET), finding papers with protocols or GitHub code, or about imaging methods. What would you like to know?';
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
