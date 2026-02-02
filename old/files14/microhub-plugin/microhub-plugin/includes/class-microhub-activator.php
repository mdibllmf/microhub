<?php
/**
 * Plugin activation handler
 */

class MicroHub_Activator {
    
    public static function activate() {
        // Set default options
        self::set_default_options();
        
        // Create MicroHub pages
        self::create_pages();
        
        // Create custom database tables if needed
        self::create_tables();
    }
    
    /**
     * Set default plugin options
     */
    private static function set_default_options() {
        $defaults = array(
            'microhub_enable_submissions' => 1,
            'microhub_require_approval' => 1,
            'microhub_papers_per_page' => 20,
        );
        
        foreach ($defaults as $key => $value) {
            if (get_option($key) === false) {
                add_option($key, $value);
            }
        }
    }
    
    /**
     * Create MicroHub pages on activation
     */
    private static function create_pages() {
        $pages = array(
            array(
                'title' => 'MicroHub',
                'slug' => 'microhub',
                'content' => '[microhub_search_page]',
            ),
            array(
                'title' => 'About MicroHub',
                'slug' => 'about',
                'content' => '[microhub_about]',
            ),
            array(
                'title' => 'Contact Us',
                'slug' => 'contact',
                'content' => '[microhub_contact]',
            ),
            array(
                'title' => 'Discussions',
                'slug' => 'discussions',
                'content' => '', // Uses page-discussions.php template automatically
            ),
            array(
                'title' => 'Protocols',
                'slug' => 'protocols',
                'content' => '', // Uses page-protocols.php template automatically
            ),
            array(
                'title' => 'Facilities',
                'slug' => 'facilities',
                'content' => '', // Uses page-facilities.php template automatically
            ),
            array(
                'title' => 'Upload Protocol',
                'slug' => 'upload-protocol',
                'content' => '[microhub_upload_protocol]',
            ),
            array(
                'title' => 'Submit Paper',
                'slug' => 'upload-paper',
                'content' => '[microhub_upload_paper]',
            ),
        );
        
        foreach ($pages as $page) {
            // Check if page exists
            $existing = get_page_by_path($page['slug']);
            
            if (!$existing) {
                wp_insert_post(array(
                    'post_title' => $page['title'],
                    'post_name' => $page['slug'],
                    'post_content' => $page['content'],
                    'post_status' => 'publish',
                    'post_type' => 'page',
                    'post_author' => 1,
                ));
            }
        }
        
        // Store page IDs in options for reference
        update_option('microhub_pages_created', true);
    }
    
    /**
     * Create custom database tables (if needed for future features)
     */
    private static function create_tables() {
        global $wpdb;
        
        $charset_collate = $wpdb->get_charset_collate();
        
        // Currently no custom tables needed
        // All data is stored using WordPress post types and meta
    }
}
