<?php
/**
 * Plugin Name: MicroHub - Microscopy Research Repository
 * Plugin URI: https://github.com/mdibllmf/microhub
 * Description: Professional microscopy research paper repository with AI chat, protocols, GitHub integration, and community discussions.
 * Version: 3.3.0
 * Author: MicroHub Team
 * License: GPL-2.0+
 * Text Domain: microhub
 */

if (!defined('WPINC')) {
    die;
}

define('MICROHUB_VERSION', '3.3.0');
define('MICROHUB_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('MICROHUB_PLUGIN_URL', plugin_dir_url(__FILE__));

// Activation
function activate_microhub() {
    require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-activator.php';
    MicroHub_Activator::activate();
    flush_rewrite_rules();
}
register_activation_hook(__FILE__, 'activate_microhub');

// Deactivation
function deactivate_microhub() {
    require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-deactivator.php';
    MicroHub_Deactivator::deactivate();
}
register_deactivation_hook(__FILE__, 'deactivate_microhub');

// Load classes
require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-post-types.php';
require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-taxonomies.php';
require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-meta-boxes.php';
require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-api.php';
require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-shortcodes.php';
require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-modular-shortcodes.php';
require_once MICROHUB_PLUGIN_DIR . 'includes/navigation-helper.php';

if (is_admin()) {
    require_once MICROHUB_PLUGIN_DIR . 'admin/admin-settings.php';
    require_once MICROHUB_PLUGIN_DIR . 'admin/admin-import.php';
    require_once MICROHUB_PLUGIN_DIR . 'admin/admin-diagnostics.php';
    require_once MICROHUB_PLUGIN_DIR . 'admin/admin-review.php';
    require_once MICROHUB_PLUGIN_DIR . 'admin/admin-ai-training.php';
    require_once MICROHUB_PLUGIN_DIR . 'admin/admin-ai-knowledge.php';
}

// Initialize plugin
function run_microhub() {
    $post_types = new MicroHub_Post_Types();
    $post_types->init();

    $taxonomies = new MicroHub_Taxonomies();
    $taxonomies->init();

    $meta_boxes = new MicroHub_Meta_Boxes();
    $meta_boxes->init();

    $api = new MicroHub_API();
    $api->init();

    $shortcodes = new MicroHub_Shortcodes();
    $shortcodes->init();

    add_action('wp_enqueue_scripts', 'microhub_enqueue_scripts');
    add_action('admin_enqueue_scripts', 'microhub_admin_enqueue_scripts');
    add_filter('single_template', 'microhub_single_template');
    add_filter('archive_template', 'microhub_archive_template');
    add_filter('comments_open', 'microhub_enable_paper_comments', 10, 2);
    
    // Allow guest comments on MicroHub papers (name required, email optional)
    add_filter('pre_comment_approved', 'microhub_allow_guest_comments', 10, 2);
    add_filter('preprocess_comment', 'microhub_preprocess_comment');
}
add_action('plugins_loaded', 'run_microhub');

// Enable comments on papers and discussions
function microhub_enable_paper_comments($open, $post_id) {
    $post = get_post($post_id);
    if ($post && in_array($post->post_type, array('mh_paper', 'mh_discussion'))) {
        return true;
    }
    return $open;
}

// Allow comments without email for MicroHub papers and discussions
function microhub_allow_guest_comments($approved, $commentdata) {
    $post = get_post($commentdata['comment_post_ID']);
    if ($post && in_array($post->post_type, array('mh_paper', 'mh_discussion'))) {
        // Check if there's an author name
        if (empty($commentdata['comment_author'])) {
            return new WP_Error('require_name', 'Please enter your name to post a comment.');
        }
        // Auto-approve if name is provided
        return 1;
    }
    return $approved;
}

// Preprocess comment to allow empty email
function microhub_preprocess_comment($commentdata) {
    $post = get_post($commentdata['comment_post_ID']);
    if ($post && in_array($post->post_type, array('mh_paper', 'mh_discussion'))) {
        // If email is empty, set a placeholder to bypass WordPress validation
        if (empty($commentdata['comment_author_email'])) {
            $commentdata['comment_author_email'] = '';
        }
    }
    return $commentdata;
}

// Templates
function microhub_single_template($template) {
    global $post;
    if ($post && $post->post_type === 'mh_paper') {
        $custom = MICROHUB_PLUGIN_DIR . 'templates/single-mh_paper.php';
        if (file_exists($custom)) return $custom;
    }
    return $template;
}

function microhub_archive_template($template) {
    if (is_post_type_archive('mh_paper') || is_tax('mh_technique') || is_tax('mh_microscope') || is_tax('mh_organism') || is_tax('mh_software')) {
        $custom = MICROHUB_PLUGIN_DIR . 'templates/archive-mh_paper.php';
        if (file_exists($custom)) return $custom;
    }
    return $template;
}

// Enqueue frontend assets
function microhub_enqueue_scripts() {
    global $post;
    
    $should_load = is_post_type_archive('mh_paper') || 
                   is_singular('mh_paper') ||
                   is_singular('mh_protocol') ||
                   is_singular('mh_discussion') ||
                   is_tax('mh_technique') || 
                   is_tax('mh_microscope') || 
                   is_tax('mh_organism');
    
    if (!$should_load && is_a($post, 'WP_Post')) {
        $shortcodes = array('microhub_search_page', 'microhub_papers', 'microhub_featured', 'microhub_stats', 'microhub_forum', 'microhub_upload_protocol', 'microhub_upload_paper');
        foreach ($shortcodes as $sc) {
            if (has_shortcode($post->post_content, $sc)) {
                $should_load = true;
                break;
            }
        }
    }
    
    if ($should_load) {
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

        wp_localize_script('microhub-frontend', 'microhubData', array(
            'apiBase' => rest_url('microhub/v1'),
            'nonce' => wp_create_nonce('wp_rest'),
            'ajaxurl' => admin_url('admin-ajax.php'),
            'copilotUrl' => get_option('microhub_copilot_bot_url', ''),
            'copilotName' => get_option('microhub_copilot_bot_name', 'MicroHub Assistant'),
        ));
    }
}

// Admin assets
function microhub_admin_enqueue_scripts($hook) {
    global $post_type;
    if (strpos($hook, 'microhub') === false && !in_array($post_type, array('mh_paper', 'mh_protocol', 'mh_discussion'))) return;
    
    wp_enqueue_style('microhub-admin', MICROHUB_PLUGIN_URL . 'assets/css/microhub-admin.css', array(), MICROHUB_VERSION);
    wp_enqueue_script('microhub-admin', MICROHUB_PLUGIN_URL . 'assets/js/microhub-admin.js', array('jquery'), MICROHUB_VERSION, true);
}

// Settings are handled in admin/admin-settings.php
