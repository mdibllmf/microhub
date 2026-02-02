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
        // Core classes - required
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-post-types.php';
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-taxonomies.php';
        require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-meta-boxes.php';
        
        // Admin pages - only in admin
        if (is_admin()) {
            require_once MICROHUB_PLUGIN_DIR . 'admin/admin-settings.php';
            require_once MICROHUB_PLUGIN_DIR . 'admin/admin-import.php';
        }
    }
    
    private function init_hooks() {
        // Initialize components on init
        add_action('init', array($this, 'init_components'), 0);
        
        // Enqueue scripts and styles
        add_action('wp_enqueue_scripts', array($this, 'enqueue_frontend_assets'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        
        // Template loading - with proper checks
        add_filter('single_template', array($this, 'load_single_template'));
        add_filter('archive_template', array($this, 'load_archive_template'));
        
        // Activation hook
        register_activation_hook(__FILE__, array($this, 'activate'));
    }
    
    public function activate() {
        // Register post types and taxonomies first
        $this->init_components();
        
        // Flush rewrite rules
        flush_rewrite_rules();
    }
    
    public function init_components() {
        // Post types
        $post_types = new MicroHub_Post_Types();
        $post_types->register_post_types();
        
        // Taxonomies
        $taxonomies = new MicroHub_Taxonomies();
        $taxonomies->register_taxonomies();
        
        // Meta boxes (only in admin)
        if (is_admin()) {
            $meta_boxes = new MicroHub_Meta_Boxes();
            $meta_boxes->init();
        }
    }
    
    public function enqueue_frontend_assets() {
        wp_enqueue_style(
            'microhub-frontend',
            MICROHUB_PLUGIN_URL . 'assets/css/microhub-frontend.css',
            array(),
            MICROHUB_VERSION
        );
    }
    
    public function enqueue_admin_assets($hook) {
        // Only on MicroHub admin pages or paper/protocol edit pages
        $screen = get_current_screen();
        if ($screen && (strpos($hook, 'microhub') !== false || 
            in_array($screen->post_type, array('mh_paper', 'mh_protocol')))) {
            
            wp_enqueue_style(
                'microhub-admin',
                MICROHUB_PLUGIN_URL . 'assets/css/microhub-admin.css',
                array(),
                MICROHUB_VERSION
            );
        }
    }
    
    public function load_single_template($template) {
        global $post;
        
        // Check if post exists and is the correct type
        if (!$post || !is_object($post)) {
            return $template;
        }
        
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
}

// Initialize the plugin
function microhub_init() {
    return MicroHub::get_instance();
}
add_action('plugins_loaded', 'microhub_init');

/**
 * Helper function to render navigation
 */
function mh_render_nav() {
    ob_start();
    ?>
    <nav class="mh-nav">
        <div class="mh-nav-brand">
            <a href="<?php echo esc_url(home_url('/papers/')); ?>">🔬 MicroHub</a>
        </div>
        <div class="mh-nav-links">
            <a href="<?php echo esc_url(home_url('/papers/')); ?>">Papers</a>
            <a href="<?php echo esc_url(home_url('/technique/')); ?>">Techniques</a>
            <a href="<?php echo esc_url(home_url('/organism/')); ?>">Organisms</a>
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
