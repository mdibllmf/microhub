<?php
/**
 * MicroHub Bot Guard
 *
 * Background bot detection and rate limiting.
 * Transparent to real users - no CAPTCHAs or visible challenges.
 * Uses User-Agent analysis, rate limiting, and honeypot traps.
 */

if (!defined('ABSPATH')) exit;

class MicroHub_Bot_Guard {

    /** Known bot user-agent patterns */
    private static $bot_patterns = array(
        'bot', 'crawl', 'spider', 'slurp', 'scraper', 'fetch',
        'curl', 'wget', 'python-requests', 'python-urllib', 'httpx',
        'go-http-client', 'java/', 'libwww', 'httpclient',
        'scrapy', 'phantomjs', 'headlesschrome', 'selenium',
        'puppeteer', 'playwright', 'mechanize', 'aiohttp',
        'zgrab', 'masscan', 'nikto', 'sqlmap', 'nmap',
        'dirbuster', 'gobuster', 'wpscan', 'nuclei',
        'semrush', 'ahrefs', 'mj12bot', 'dotbot', 'petalbot',
        'bytespider', 'dataforseo', 'claudebot', 'gptbot',
        'ccbot', 'yandexbot', 'baiduspider',
    );

    /** Allowed bots (search engines we want to let through) */
    private static $allowed_bots = array(
        'googlebot', 'bingbot', 'duckduckbot', 'facebot',
        'twitterbot', 'linkedinbot', 'slackbot', 'whatsapp',
        'telegrambot', 'applebot',
    );

    /** Rate limit: max requests per IP per minute */
    const RATE_LIMIT = 60;

    /** Rate limit window in seconds */
    const RATE_WINDOW = 60;

    public function init() {
        // Run bot check early on every frontend request
        add_action('template_redirect', array($this, 'check_request'), 1);

        // Add honeypot trap in footer (hidden from humans, visible to bots)
        add_action('wp_footer', array($this, 'render_honeypot'));

        // AJAX endpoint for honeypot trigger
        add_action('wp_ajax_mh_hp_check', array($this, 'honeypot_triggered'));
        add_action('wp_ajax_nopriv_mh_hp_check', array($this, 'honeypot_triggered'));
    }

    /**
     * Check if a user-agent string looks like a bot
     */
    public static function is_bot_ua($ua) {
        if (empty($ua)) return true;

        $ua_lower = strtolower($ua);

        // Allow known good bots
        foreach (self::$allowed_bots as $good) {
            if (strpos($ua_lower, $good) !== false) {
                return false;
            }
        }

        // Check against known bad patterns
        foreach (self::$bot_patterns as $pattern) {
            if (strpos($ua_lower, $pattern) !== false) {
                return true;
            }
        }

        // No JS engine string usually means not a real browser
        $browser_markers = array('mozilla', 'chrome', 'safari', 'firefox', 'edge', 'opera');
        $has_browser = false;
        foreach ($browser_markers as $marker) {
            if (strpos($ua_lower, $marker) !== false) {
                $has_browser = true;
                break;
            }
        }

        return !$has_browser;
    }

    /**
     * Main request check - runs on every frontend page load
     */
    public function check_request() {
        if (is_admin() || current_user_can('manage_options') || wp_doing_ajax() || wp_doing_cron()) {
            return;
        }

        $ua = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '';
        $ip = $this->get_visitor_ip();

        // 1. Check for empty/missing user agent
        if (empty($ua)) {
            $this->log_block($ip, $ua, 'empty_ua');
            $this->soft_block();
            return;
        }

        // 2. Check for known bad bots
        if (self::is_bot_ua($ua)) {
            // Check if it's a known good bot
            $ua_lower = strtolower($ua);
            $is_good_bot = false;
            foreach (self::$allowed_bots as $good) {
                if (strpos($ua_lower, $good) !== false) {
                    $is_good_bot = true;
                    break;
                }
            }

            if (!$is_good_bot) {
                $this->log_block($ip, $ua, 'bad_ua');
                $this->soft_block();
                return;
            }
        }

        // 3. Rate limiting
        if ($this->is_rate_limited($ip)) {
            $this->log_block($ip, $ua, 'rate_limit');
            $this->rate_limit_response();
            return;
        }

        // 4. Check for suspicious request patterns
        if ($this->has_suspicious_patterns()) {
            $this->log_block($ip, $ua, 'suspicious_pattern');
            $this->soft_block();
            return;
        }
    }

    /**
     * Check if an IP has exceeded the rate limit
     */
    private function is_rate_limited($ip) {
        $ip_hash = $this->hash_ip($ip);
        $transient_key = 'mh_rl_' . substr($ip_hash, 0, 16);

        $data = get_transient($transient_key);
        if ($data === false) {
            set_transient($transient_key, array('count' => 1, 'start' => time()), self::RATE_WINDOW);
            return false;
        }

        $data['count']++;
        set_transient($transient_key, $data, self::RATE_WINDOW);

        return $data['count'] > self::RATE_LIMIT;
    }

    /**
     * Check for suspicious request patterns
     */
    private function has_suspicious_patterns() {
        $uri = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '';

        // Common attack patterns
        $bad_patterns = array(
            'wp-config', '.env', '.git', 'xmlrpc.php',
            'eval(', 'base64_decode', 'UNION SELECT',
            '../', '..\\', '%00', '<script',
            'wp-admin/install.php', 'wp-admin/setup-config.php',
        );

        $uri_lower = strtolower($uri);
        foreach ($bad_patterns as $pattern) {
            if (strpos($uri_lower, strtolower($pattern)) !== false) {
                return true;
            }
        }

        return false;
    }

    /**
     * Soft block: return 403 for bad bots
     */
    private function soft_block() {
        status_header(403);
        nocache_headers();
        echo '<!DOCTYPE html><html><head><title>Access Denied</title></head><body><h1>403 Forbidden</h1></body></html>';
        exit;
    }

    /**
     * Rate limit response: return 429
     */
    private function rate_limit_response() {
        status_header(429);
        nocache_headers();
        header('Retry-After: 60');
        echo '<!DOCTYPE html><html><head><title>Too Many Requests</title></head><body><h1>429 Too Many Requests</h1><p>Please slow down.</p></body></html>';
        exit;
    }

    /**
     * Render honeypot trap (invisible to real users)
     */
    public function render_honeypot() {
        if (is_admin()) return;
        ?>
        <div aria-hidden="true" style="position:absolute;left:-9999px;top:-9999px;width:1px;height:1px;overflow:hidden;">
            <a href="#" id="mh-hp-link" tabindex="-1">Site resources</a>
            <form id="mh-hp-form" method="post" action="<?php echo esc_url(admin_url('admin-ajax.php')); ?>">
                <input type="hidden" name="action" value="mh_hp_check" />
                <input type="text" name="mh_hp_field" id="mh-hp-field" tabindex="-1" autocomplete="off" />
            </form>
        </div>
        <?php
    }

    /**
     * Honeypot triggered - a bot clicked/filled the hidden element
     */
    public function honeypot_triggered() {
        $ip = $this->get_visitor_ip();
        $ua = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '';
        $this->log_block($ip, $ua, 'honeypot');

        // Block this IP for 1 hour
        $ip_hash = $this->hash_ip($ip);
        set_transient('mh_blocked_' . substr($ip_hash, 0, 16), true, HOUR_IN_SECONDS);

        wp_send_json_error('Blocked', 403);
    }

    /**
     * Log a bot block to the database
     */
    private function log_block($ip, $ua, $reason) {
        global $wpdb;

        $table = $wpdb->prefix . 'mh_bot_blocks';

        // Check if table exists before inserting
        if ($wpdb->get_var("SHOW TABLES LIKE '$table'") !== $table) {
            return;
        }

        $wpdb->insert($table, array(
            'ip_hash'    => $this->hash_ip($ip),
            'user_agent' => substr(sanitize_text_field($ua), 0, 500),
            'reason'     => $reason,
            'page_url'   => substr(esc_url_raw($_SERVER['REQUEST_URI'] ?? ''), 0, 500),
        ), array('%s', '%s', '%s', '%s'));
    }

    /**
     * Hash IP for privacy
     */
    private function hash_ip($ip) {
        $salt = defined('AUTH_SALT') ? AUTH_SALT : 'mh_default_salt';
        return hash('sha256', $ip . $salt . date('Y-m'));
    }

    /**
     * Get real visitor IP
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
}
