<?php
/**
 * MicroHub Visitor Tracking
 *
 * Tracks page views, session duration, tag usage, and link clicks.
 * All data is privacy-friendly: IPs are hashed, no cookies store personal info.
 * Only visible to admins (manage_options capability).
 */

if (!defined('ABSPATH')) exit;

class MicroHub_Tracking {

    public function init() {
        // Record page view on frontend
        add_action('wp_footer', array($this, 'record_page_view'));

        // AJAX endpoints for frontend tracking
        add_action('wp_ajax_mh_track_event', array($this, 'ajax_track_event'));
        add_action('wp_ajax_nopriv_mh_track_event', array($this, 'ajax_track_event'));
        add_action('wp_ajax_mh_track_duration', array($this, 'ajax_track_duration'));
        add_action('wp_ajax_nopriv_mh_track_duration', array($this, 'ajax_track_duration'));
        add_action('wp_ajax_mh_heartbeat', array($this, 'ajax_heartbeat'));
        add_action('wp_ajax_nopriv_mh_heartbeat', array($this, 'ajax_heartbeat'));

        // Enqueue tracking script on all frontend pages
        add_action('wp_enqueue_scripts', array($this, 'enqueue_tracking_script'));

        // Daily cleanup of old data (keep 90 days)
        add_action('mh_tracking_cleanup', array($this, 'cleanup_old_data'));
        if (!wp_next_scheduled('mh_tracking_cleanup')) {
            wp_schedule_event(time(), 'daily', 'mh_tracking_cleanup');
        }
    }

    /**
     * Enqueue tracking JavaScript on all frontend pages
     */
    public function enqueue_tracking_script() {
        if (is_admin()) return;

        wp_enqueue_script(
            'microhub-tracking',
            MICROHUB_PLUGIN_URL . 'assets/js/tracking.js',
            array('jquery'),
            MICROHUB_VERSION,
            true
        );

        $post_id = 0;
        $post_type = '';
        if (is_singular()) {
            global $post;
            if ($post) {
                $post_id = $post->ID;
                $post_type = $post->post_type;
            }
        }

        wp_localize_script('microhub-tracking', 'mhTracking', array(
            'ajaxurl'   => admin_url('admin-ajax.php'),
            'nonce'     => wp_create_nonce('mh_tracking_nonce'),
            'postId'    => $post_id,
            'postType'  => $post_type,
            'sessionId' => $this->get_session_id(),
        ));
    }

    /**
     * Get or create a session ID (stored in a simple non-personal cookie)
     */
    private function get_session_id() {
        if (isset($_COOKIE['mh_sid'])) {
            return sanitize_text_field($_COOKIE['mh_sid']);
        }
        $sid = wp_generate_password(32, false);
        // Cookie lasts 30 minutes
        if (!headers_sent()) {
            setcookie('mh_sid', $sid, time() + 1800, COOKIEPATH, COOKIE_DOMAIN, is_ssl(), true);
        }
        return $sid;
    }

    /**
     * Hash an IP address for privacy
     */
    private function hash_ip($ip) {
        $salt = defined('AUTH_SALT') ? AUTH_SALT : 'mh_default_salt';
        return hash('sha256', $ip . $salt . date('Y-m'));
    }

    /**
     * Get the visitor's real IP
     */
    private function get_visitor_ip() {
        $headers = array('HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'REMOTE_ADDR');
        foreach ($headers as $header) {
            if (!empty($_SERVER[$header])) {
                $ip = $_SERVER[$header];
                if (strpos($ip, ',') !== false) {
                    $ip = trim(explode(',', $ip)[0]);
                }
                if (filter_var($ip, FILTER_VALIDATE_IP)) {
                    return $ip;
                }
            }
        }
        return '0.0.0.0';
    }

    /**
     * Record a page view via inline script in footer
     */
    public function record_page_view() {
        if (is_admin() || current_user_can('manage_options')) return;

        global $wpdb, $post;

        $ip = $this->get_visitor_ip();
        $ip_hash = $this->hash_ip($ip);
        $ua = isset($_SERVER['HTTP_USER_AGENT']) ? sanitize_text_field($_SERVER['HTTP_USER_AGENT']) : '';
        $session_id = $this->get_session_id();

        // Check if this is a bot (quick check here; full guard runs separately)
        $is_bot = MicroHub_Bot_Guard::is_bot_ua($ua) ? 1 : 0;

        $page_url = isset($_SERVER['REQUEST_URI']) ? esc_url_raw($_SERVER['REQUEST_URI']) : '';
        $page_title = is_singular() && $post ? $post->post_title : wp_title('', false);
        $post_id = is_singular() && $post ? $post->ID : 0;
        $post_type = is_singular() && $post ? $post->post_type : '';
        $referrer = isset($_SERVER['HTTP_REFERER']) ? esc_url_raw($_SERVER['HTTP_REFERER']) : '';

        $table = $wpdb->prefix . 'mh_page_views';
        $wpdb->insert($table, array(
            'session_id' => $session_id,
            'page_url'   => substr($page_url, 0, 500),
            'page_title' => substr($page_title, 0, 255),
            'post_id'    => $post_id,
            'post_type'  => $post_type,
            'referrer'   => substr($referrer, 0, 500),
            'user_agent' => substr($ua, 0, 500),
            'ip_hash'    => $ip_hash,
            'is_bot'     => $is_bot,
            'duration'   => 0,
        ), array('%s', '%s', '%s', '%d', '%s', '%s', '%s', '%s', '%d', '%d'));
    }

    /**
     * AJAX: Track an interaction event (tag click, link click, search, filter)
     */
    public function ajax_track_event() {
        check_ajax_referer('mh_tracking_nonce', 'nonce');

        global $wpdb;

        $session_id  = sanitize_text_field($_POST['session_id'] ?? '');
        $event_type  = sanitize_text_field($_POST['event_type'] ?? '');
        $event_target = esc_url_raw($_POST['event_target'] ?? '');
        $event_value = sanitize_text_field($_POST['event_value'] ?? '');
        $post_id     = absint($_POST['post_id'] ?? 0);

        if (empty($session_id) || empty($event_type)) {
            wp_send_json_error('Missing data');
        }

        $allowed_types = array(
            'tag_click', 'link_click', 'outbound_link', 'search',
            'filter_change', 'paper_view', 'protocol_view', 'discussion_view',
            'download', 'chat_open', 'pagination',
        );

        if (!in_array($event_type, $allowed_types)) {
            wp_send_json_error('Invalid event type');
        }

        $ip = $this->get_visitor_ip();
        $ip_hash = $this->hash_ip($ip);
        $ua = isset($_SERVER['HTTP_USER_AGENT']) ? sanitize_text_field($_SERVER['HTTP_USER_AGENT']) : '';
        $is_bot = MicroHub_Bot_Guard::is_bot_ua($ua) ? 1 : 0;

        $table = $wpdb->prefix . 'mh_tracking_events';
        $wpdb->insert($table, array(
            'session_id'   => $session_id,
            'event_type'   => $event_type,
            'event_target' => substr($event_target, 0, 500),
            'event_value'  => substr($event_value, 0, 255),
            'post_id'      => $post_id,
            'ip_hash'      => $ip_hash,
            'is_bot'       => $is_bot,
        ), array('%s', '%s', '%s', '%s', '%d', '%s', '%d'));

        wp_send_json_success();
    }

    /**
     * AJAX: Update session duration for a page view
     */
    public function ajax_track_duration() {
        check_ajax_referer('mh_tracking_nonce', 'nonce');

        global $wpdb;

        $session_id = sanitize_text_field($_POST['session_id'] ?? '');
        $duration   = absint($_POST['duration'] ?? 0);
        $page_url   = esc_url_raw($_POST['page_url'] ?? '');

        if (empty($session_id) || $duration < 1) {
            wp_send_json_error('Missing data');
        }

        // Cap duration at 30 minutes to avoid stale tabs
        $duration = min($duration, 1800);

        $table = $wpdb->prefix . 'mh_page_views';
        $wpdb->query($wpdb->prepare(
            "UPDATE $table SET duration = %d WHERE session_id = %s AND page_url = %s ORDER BY id DESC LIMIT 1",
            $duration, $session_id, $page_url
        ));

        wp_send_json_success();
    }

    /**
     * AJAX: Heartbeat to keep session alive
     */
    public function ajax_heartbeat() {
        check_ajax_referer('mh_tracking_nonce', 'nonce');
        wp_send_json_success(array('alive' => true));
    }

    /**
     * Clean up data older than 90 days
     */
    public function cleanup_old_data() {
        global $wpdb;

        $cutoff = date('Y-m-d H:i:s', strtotime('-90 days'));

        $wpdb->query($wpdb->prepare(
            "DELETE FROM {$wpdb->prefix}mh_page_views WHERE created_at < %s", $cutoff
        ));
        $wpdb->query($wpdb->prepare(
            "DELETE FROM {$wpdb->prefix}mh_tracking_events WHERE created_at < %s", $cutoff
        ));
        $wpdb->query($wpdb->prepare(
            "DELETE FROM {$wpdb->prefix}mh_bot_blocks WHERE created_at < %s", $cutoff
        ));
    }

    // =========================================================================
    // Query helpers for the admin dashboard
    // =========================================================================

    /**
     * Get total human visitors for a date range
     */
    public static function get_visitor_count($days = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_page_views';
        return (int) $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(DISTINCT ip_hash) FROM $table WHERE is_bot = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)",
            $days
        ));
    }

    /**
     * Get total page views for a date range (humans only)
     */
    public static function get_pageview_count($days = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_page_views';
        return (int) $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(*) FROM $table WHERE is_bot = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)",
            $days
        ));
    }

    /**
     * Get average session duration (humans only)
     */
    public static function get_avg_duration($days = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_page_views';
        return (float) $wpdb->get_var($wpdb->prepare(
            "SELECT AVG(duration) FROM $table WHERE is_bot = 0 AND duration > 0 AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)",
            $days
        ));
    }

    /**
     * Get daily pageview data for chart
     */
    public static function get_daily_views($days = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_page_views';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT DATE(created_at) as date, COUNT(*) as views, COUNT(DISTINCT ip_hash) as visitors
             FROM $table WHERE is_bot = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY DATE(created_at) ORDER BY date ASC",
            $days
        ));
    }

    /**
     * Get top pages
     */
    public static function get_top_pages($days = 30, $limit = 20) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_page_views';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT page_url, page_title, COUNT(*) as views, COUNT(DISTINCT ip_hash) as visitors, AVG(duration) as avg_duration
             FROM $table WHERE is_bot = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY page_url, page_title ORDER BY views DESC LIMIT %d",
            $days, $limit
        ));
    }

    /**
     * Get top referrers
     */
    public static function get_top_referrers($days = 30, $limit = 20) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_page_views';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT referrer, COUNT(*) as visits
             FROM $table WHERE is_bot = 0 AND referrer != '' AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY referrer ORDER BY visits DESC LIMIT %d",
            $days, $limit
        ));
    }

    /**
     * Get tag/taxonomy usage events
     */
    public static function get_tag_usage($days = 30, $limit = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_tracking_events';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT event_value, COUNT(*) as clicks
             FROM $table WHERE is_bot = 0 AND event_type = 'tag_click' AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY event_value ORDER BY clicks DESC LIMIT %d",
            $days, $limit
        ));
    }

    /**
     * Get outbound link clicks
     */
    public static function get_link_clicks($days = 30, $limit = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_tracking_events';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT event_target, event_value, COUNT(*) as clicks
             FROM $table WHERE is_bot = 0 AND event_type IN ('link_click','outbound_link') AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY event_target, event_value ORDER BY clicks DESC LIMIT %d",
            $days, $limit
        ));
    }

    /**
     * Get search queries
     */
    public static function get_search_queries($days = 30, $limit = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_tracking_events';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT event_value, COUNT(*) as count
             FROM $table WHERE is_bot = 0 AND event_type = 'search' AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY event_value ORDER BY count DESC LIMIT %d",
            $days, $limit
        ));
    }

    /**
     * Get filter usage
     */
    public static function get_filter_usage($days = 30, $limit = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_tracking_events';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT event_target as filter_name, event_value, COUNT(*) as count
             FROM $table WHERE is_bot = 0 AND event_type = 'filter_change' AND created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY event_target, event_value ORDER BY count DESC LIMIT %d",
            $days, $limit
        ));
    }

    /**
     * Get bot block stats
     */
    public static function get_bot_stats($days = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_bot_blocks';
        return $wpdb->get_results($wpdb->prepare(
            "SELECT reason, COUNT(*) as blocks
             FROM $table WHERE created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)
             GROUP BY reason ORDER BY blocks DESC",
            $days
        ));
    }

    /**
     * Get total bot blocks
     */
    public static function get_total_bot_blocks($days = 30) {
        global $wpdb;
        $table = $wpdb->prefix . 'mh_bot_blocks';
        return (int) $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(*) FROM $table WHERE created_at >= DATE_SUB(NOW(), INTERVAL %d DAY)",
            $days
        ));
    }
}
