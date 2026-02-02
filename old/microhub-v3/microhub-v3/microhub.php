<?php
/**
 * Plugin Name: MicroHub
 * Plugin URI: https://microhub.org
 * Description: A comprehensive microscopy paper database with full text access, figures, protocols, and data repositories
 * Version: 3.0.0
 * Author: MicroHub Team
 * License: GPL v2 or later
 * Text Domain: microhub
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('MICROHUB_VERSION', '3.0.0');
define('MICROHUB_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('MICROHUB_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Main MicroHub Class
 */
class MicroHub {
    
    private static $instance = null;
    
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        $this->load_dependencies();
        $this->init_hooks();
    }
    
    private function load_dependencies() {
        // Core classes
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-post-types.php';
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-taxonomies.php';
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-meta-boxes.php';
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-activator.php';
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-deactivator.php';
        
        // Optional: Shortcodes
        if (file_exists(MICROHUB_PLUGIN_DIR . 'includes/class-microhub-shortcodes.php')) {
            require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-shortcodes.php';
        }
        if (file_exists(MICROHUB_PLUGIN_DIR . 'includes/class-microhub-modular-shortcodes.php')) {
            require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-modular-shortcodes.php';
        }
        
        // Optional: API
        if (file_exists(MICROHUB_PLUGIN_DIR . 'includes/class-microhub-api.php')) {
            require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-api.php';
        }
        
        // Optional: Navigation helper
        if (file_exists(MICROHUB_PLUGIN_DIR . 'includes/navigation-helper.php')) {
            require_once MICROHUB_PLUGIN_DIR . 'includes/navigation-helper.php';
        }
        
        // Admin pages
        if (is_admin()) {
            require_once MICROHUB_PLUGIN_DIR . 'admin/admin-settings.php';
            require_once MICROHUB_PLUGIN_DIR . 'admin/admin-import.php';
            if (file_exists(MICROHUB_PLUGIN_DIR . 'admin/admin-review.php')) {
                require_once MICROHUB_PLUGIN_DIR . 'admin/admin-review.php';
            }
            if (file_exists(MICROHUB_PLUGIN_DIR . 'admin/admin-diagnostics.php')) {
                require_once MICROHUB_PLUGIN_DIR . 'admin/admin-diagnostics.php';
            }
        }
    }
    
    private function init_hooks() {
        // Initialize components
        add_action('init', array($this, 'init_components'));
        
        // Activation/Deactivation
        register_activation_hook(__FILE__, array('MicroHub_Activator', 'activate'));
        register_deactivation_hook(__FILE__, array('MicroHub_Deactivator', 'deactivate'));
        
        // Enqueue scripts and styles
        add_action('wp_enqueue_scripts', array($this, 'enqueue_frontend_assets'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        
        // Template loading
        add_filter('single_template', array($this, 'load_single_template'));
        add_filter('archive_template', array($this, 'load_archive_template'));
        
        // REST API
        add_action('rest_api_init', array($this, 'register_rest_routes'));
    }
    
    public function init_components() {
        // Post types
        $post_types = new MicroHub_Post_Types();
        $post_types->init();
        
        // Taxonomies
        $taxonomies = new MicroHub_Taxonomies();
        $taxonomies->init();
        
        // Meta boxes
        $meta_boxes = new MicroHub_Meta_Boxes();
        $meta_boxes->init();
        
        // Shortcodes
        if (class_exists('MicroHub_Shortcodes')) {
            $shortcodes = new MicroHub_Shortcodes();
            $shortcodes->init();
        }
        if (class_exists('MicroHub_Modular_Shortcodes')) {
            $modular_shortcodes = new MicroHub_Modular_Shortcodes();
            $modular_shortcodes->init();
        }
        
        // API
        if (class_exists('MicroHub_API')) {
            $api = new MicroHub_API();
            $api->init();
        }
    }
    
    public function enqueue_frontend_assets() {
        wp_enqueue_style(
            'microhub-frontend',
            MICROHUB_PLUGIN_URL . 'assets/css/microhub-frontend.css',
            array(),
            MICROHUB_VERSION
        );
        
        wp_enqueue_script(
            'microhub-frontend',
            MICROHUB_PLUGIN_URL . 'assets/js/frontend.js',
            array('jquery'),
            MICROHUB_VERSION,
            true
        );
        
        wp_localize_script('microhub-frontend', 'microhub', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('microhub_nonce'),
            'rest_url' => rest_url('microhub/v1/'),
        ));
    }
    
    public function enqueue_admin_assets($hook) {
        // Only on MicroHub admin pages
        if (strpos($hook, 'microhub') !== false || 
            get_post_type() === 'mh_paper' || 
            get_post_type() === 'mh_protocol') {
            
            wp_enqueue_style(
                'microhub-admin',
                MICROHUB_PLUGIN_URL . 'assets/css/microhub-admin.css',
                array(),
                MICROHUB_VERSION
            );
            
            wp_enqueue_script(
                'microhub-admin',
                MICROHUB_PLUGIN_URL . 'assets/js/microhub-admin.js',
                array('jquery'),
                MICROHUB_VERSION,
                true
            );
        }
    }
    
    public function load_single_template($template) {
        global $post;
        
        if ($post->post_type === 'mh_paper') {
            $custom_template = MICROHUB_PLUGIN_DIR . 'templates/single-mh_paper.php';
            if (file_exists($custom_template)) {
                return $custom_template;
            }
        }
        
        return $template;
    }
    
    public function load_archive_template($template) {
        if (is_post_type_archive('mh_paper')) {
            $custom_template = MICROHUB_PLUGIN_DIR . 'templates/archive-mh_paper.php';
            if (file_exists($custom_template)) {
                return $custom_template;
            }
        }
        
        return $template;
    }
    
    public function register_rest_routes() {
        // Paper search endpoint
        register_rest_route('microhub/v1', '/papers', array(
            'methods' => 'GET',
            'callback' => array($this, 'api_get_papers'),
            'permission_callback' => '__return_true',
        ));
        
        // Single paper endpoint
        register_rest_route('microhub/v1', '/papers/(?P<id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'api_get_paper'),
            'permission_callback' => '__return_true',
        ));
        
        // Taxonomy terms endpoint
        register_rest_route('microhub/v1', '/taxonomy/(?P<taxonomy>[a-z_]+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'api_get_taxonomy_terms'),
            'permission_callback' => '__return_true',
        ));
        
        // Statistics endpoint
        register_rest_route('microhub/v1', '/stats', array(
            'methods' => 'GET',
            'callback' => array($this, 'api_get_stats'),
            'permission_callback' => '__return_true',
        ));
    }
    
    public function api_get_papers($request) {
        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => $request->get_param('per_page') ?: 20,
            'paged' => $request->get_param('page') ?: 1,
            'orderby' => 'meta_value_num',
            'order' => 'DESC',
            'meta_key' => '_mh_citation_count',
        );
        
        // Search
        if ($search = $request->get_param('search')) {
            $args['s'] = $search;
        }
        
        // Taxonomy filters
        $tax_query = array();
        
        if ($technique = $request->get_param('technique')) {
            $tax_query[] = array(
                'taxonomy' => 'mh_technique',
                'field' => 'slug',
                'terms' => $technique,
            );
        }
        
        if ($organism = $request->get_param('organism')) {
            $tax_query[] = array(
                'taxonomy' => 'mh_organism',
                'field' => 'slug',
                'terms' => $organism,
            );
        }
        
        if (!empty($tax_query)) {
            $args['tax_query'] = $tax_query;
        }
        
        // Meta filters
        $meta_query = array();
        
        if ($request->get_param('has_full_text')) {
            $meta_query[] = array(
                'key' => '_mh_has_full_text',
                'value' => '1',
            );
        }
        
        if ($request->get_param('has_figures')) {
            $meta_query[] = array(
                'key' => '_mh_has_figures',
                'value' => '1',
            );
        }
        
        if ($request->get_param('has_protocols')) {
            $meta_query[] = array(
                'key' => '_mh_has_protocols',
                'value' => '1',
            );
        }
        
        if (!empty($meta_query)) {
            $args['meta_query'] = $meta_query;
        }
        
        $query = new WP_Query($args);
        
        $papers = array();
        foreach ($query->posts as $post) {
            $papers[] = $this->format_paper_for_api($post->ID);
        }
        
        return new WP_REST_Response(array(
            'papers' => $papers,
            'total' => $query->found_posts,
            'pages' => $query->max_num_pages,
        ), 200);
    }
    
    public function api_get_paper($request) {
        $id = $request->get_param('id');
        $post = get_post($id);
        
        if (!$post || $post->post_type !== 'mh_paper') {
            return new WP_Error('not_found', 'Paper not found', array('status' => 404));
        }
        
        return new WP_REST_Response($this->format_paper_for_api($id, true), 200);
    }
    
    private function format_paper_for_api($post_id, $full = false) {
        $paper = array(
            'id' => $post_id,
            'title' => get_the_title($post_id),
            'url' => get_permalink($post_id),
            'doi' => get_post_meta($post_id, '_mh_doi', true),
            'pmid' => get_post_meta($post_id, '_mh_pubmed_id', true),
            'journal' => get_post_meta($post_id, '_mh_journal', true),
            'year' => get_post_meta($post_id, '_mh_publication_year', true),
            'citations' => (int) get_post_meta($post_id, '_mh_citation_count', true),
            'has_full_text' => (bool) get_post_meta($post_id, '_mh_has_full_text', true),
            'has_figures' => (bool) get_post_meta($post_id, '_mh_has_figures', true),
            'has_protocols' => (bool) get_post_meta($post_id, '_mh_has_protocols', true),
            'techniques' => wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'names')),
            'organisms' => wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'names')),
        );
        
        if ($full) {
            $paper['abstract'] = get_post_meta($post_id, '_mh_abstract', true);
            $paper['methods'] = get_post_meta($post_id, '_mh_methods', true);
            $paper['authors'] = get_post_meta($post_id, '_mh_authors', true);
            $paper['github_url'] = get_post_meta($post_id, '_mh_github_url', true);
            $paper['figures'] = json_decode(get_post_meta($post_id, '_mh_figures', true), true) ?: array();
            $paper['protocols'] = json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array();
            $paper['repositories'] = json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array();
            $paper['rrids'] = json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array();
            $paper['microscope_brands'] = wp_get_post_terms($post_id, 'mh_microscope_brand', array('fields' => 'names'));
            $paper['microscope_models'] = wp_get_post_terms($post_id, 'mh_microscope_model', array('fields' => 'names'));
            $paper['analysis_software'] = wp_get_post_terms($post_id, 'mh_analysis_software', array('fields' => 'names'));
            $paper['sample_preparation'] = wp_get_post_terms($post_id, 'mh_sample_prep', array('fields' => 'names'));
            $paper['fluorophores'] = wp_get_post_terms($post_id, 'mh_fluorophore', array('fields' => 'names'));
        }
        
        return $paper;
    }
    
    public function api_get_taxonomy_terms($request) {
        $taxonomy = $request->get_param('taxonomy');
        
        // Validate taxonomy
        $valid_taxonomies = array(
            'mh_technique', 'mh_microscope_brand', 'mh_microscope_model',
            'mh_analysis_software', 'mh_acquisition_software', 'mh_sample_prep',
            'mh_fluorophore', 'mh_organism', 'mh_protocol_source', 'mh_repository',
            'mh_journal', 'mh_software', 'mh_microscope'
        );
        
        if (!in_array($taxonomy, $valid_taxonomies)) {
            return new WP_Error('invalid_taxonomy', 'Invalid taxonomy', array('status' => 400));
        }
        
        $terms = get_terms(array(
            'taxonomy' => $taxonomy,
            'hide_empty' => $request->get_param('hide_empty') !== 'false',
            'orderby' => 'count',
            'order' => 'DESC',
            'number' => $request->get_param('limit') ?: 100,
        ));
        
        $formatted_terms = array();
        foreach ($terms as $term) {
            $formatted_terms[] = array(
                'id' => $term->term_id,
                'name' => $term->name,
                'slug' => $term->slug,
                'count' => $term->count,
            );
        }
        
        return new WP_REST_Response($formatted_terms, 200);
    }
    
    public function api_get_stats() {
        global $wpdb;
        
        $total_papers = wp_count_posts('mh_paper')->publish;
        
        $with_full_text = $wpdb->get_var(
            "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_has_full_text' AND meta_value = '1'"
        );
        
        $with_figures = $wpdb->get_var(
            "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_has_figures' AND meta_value = '1'"
        );
        
        $with_protocols = $wpdb->get_var(
            "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_has_protocols' AND meta_value = '1'"
        );
        
        $with_github = $wpdb->get_var(
            "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''"
        );
        
        return new WP_REST_Response(array(
            'total_papers' => (int) $total_papers,
            'with_full_text' => (int) $with_full_text,
            'with_figures' => (int) $with_figures,
            'with_protocols' => (int) $with_protocols,
            'with_github' => (int) $with_github,
            'techniques' => wp_count_terms('mh_technique'),
            'organisms' => wp_count_terms('mh_organism'),
            'microscope_brands' => wp_count_terms('mh_microscope_brand'),
            'software' => wp_count_terms('mh_analysis_software'),
        ), 200);
    }
}

// Initialize the plugin
function microhub_init() {
    return MicroHub::get_instance();
}

// Start the plugin
add_action('plugins_loaded', 'microhub_init');

/**
 * Helper function to render navigation
 */
if (!function_exists('mh_render_nav')) {
    function mh_render_nav() {
        ob_start();
        ?>
        <nav class="mh-nav">
            <div class="mh-nav-brand">
                <a href="<?php echo home_url('/papers/'); ?>">🔬 MicroHub</a>
            </div>
            <div class="mh-nav-links">
                <a href="<?php echo home_url('/papers/'); ?>">Papers</a>
                <a href="<?php echo home_url('/technique/'); ?>">Techniques</a>
                <a href="<?php echo home_url('/organism/'); ?>">Organisms</a>
                <a href="<?php echo home_url('/analysis-software/'); ?>">Software</a>
            </div>
        </nav>
        <style>
        .mh-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 30px;
            background: #161b22;
            border-bottom: 1px solid #30363d;
            margin-bottom: 20px;
        }
        .mh-nav-brand a {
            font-size: 1.3rem;
            font-weight: 700;
            color: #e6edf3;
            text-decoration: none;
        }
        .mh-nav-links {
            display: flex;
            gap: 20px;
        }
        .mh-nav-links a {
            color: #8b949e;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .mh-nav-links a:hover {
            color: #58a6ff;
        }
        </style>
        <?php
        return ob_get_clean();
    }
}
