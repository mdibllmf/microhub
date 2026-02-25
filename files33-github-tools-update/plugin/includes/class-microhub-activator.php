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
                'title' => 'Upload Protocol',
                'slug' => 'upload-protocol',
                'content' => '[microhub_upload_protocol]',
            ),
            array(
                'title' => 'Submit Paper',
                'slug' => 'upload-paper',
                'content' => '[microhub_upload_paper]',
            ),
            array(
                'title' => 'GitHub Tools',
                'slug' => 'github-tools',
                'content' => '', // Uses page-github-tools.php template automatically
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
     * Create custom database tables for analytics tracking
     */
    private static function create_tables() {
        global $wpdb;

        $charset_collate = $wpdb->get_charset_collate();

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');

        // Page views table - tracks individual visits
        $table_visits = $wpdb->prefix . 'mh_page_views';
        $sql_visits = "CREATE TABLE $table_visits (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            session_id varchar(64) NOT NULL,
            page_url varchar(500) NOT NULL,
            page_title varchar(255) DEFAULT '',
            post_id bigint(20) unsigned DEFAULT 0,
            post_type varchar(50) DEFAULT '',
            referrer varchar(500) DEFAULT '',
            user_agent varchar(500) DEFAULT '',
            ip_hash varchar(64) NOT NULL,
            country varchar(10) DEFAULT '',
            is_bot tinyint(1) DEFAULT 0,
            duration int(11) DEFAULT 0,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_session (session_id),
            KEY idx_created (created_at),
            KEY idx_post (post_id),
            KEY idx_bot (is_bot)
        ) $charset_collate;";
        dbDelta($sql_visits);

        // Events table - tracks interactions (tag clicks, link clicks, searches)
        $table_events = $wpdb->prefix . 'mh_tracking_events';
        $sql_events = "CREATE TABLE $table_events (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            session_id varchar(64) NOT NULL,
            event_type varchar(50) NOT NULL,
            event_target varchar(500) DEFAULT '',
            event_value varchar(255) DEFAULT '',
            post_id bigint(20) unsigned DEFAULT 0,
            ip_hash varchar(64) NOT NULL,
            is_bot tinyint(1) DEFAULT 0,
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_session (session_id),
            KEY idx_event_type (event_type),
            KEY idx_created (created_at)
        ) $charset_collate;";
        dbDelta($sql_events);

        // Bot blocks table - logs blocked requests
        $table_blocks = $wpdb->prefix . 'mh_bot_blocks';
        $sql_blocks = "CREATE TABLE $table_blocks (
            id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
            ip_hash varchar(64) NOT NULL,
            user_agent varchar(500) DEFAULT '',
            reason varchar(100) NOT NULL,
            page_url varchar(500) DEFAULT '',
            created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_created (created_at),
            KEY idx_ip (ip_hash)
        ) $charset_collate;";
        dbDelta($sql_blocks);

        update_option('mh_tracking_db_version', '1.0');
    }
}
