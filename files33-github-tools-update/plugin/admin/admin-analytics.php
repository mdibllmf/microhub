<?php
/**
 * MicroHub Analytics Dashboard
 *
 * Admin-only page showing visitor metrics, engagement data, and bot protection stats.
 * Only visible to users with manage_options capability.
 */

if (!defined('ABSPATH')) exit;

// Register the analytics admin page
add_action('admin_menu', 'mh_analytics_add_menu');

function mh_analytics_add_menu() {
    add_submenu_page(
        'microhub-settings',
        'Site Analytics',
        'Site Analytics',
        'manage_options',
        'microhub-analytics',
        'mh_analytics_page'
    );
}

/**
 * Analytics dashboard page
 */
function mh_analytics_page() {
    if (!current_user_can('manage_options')) {
        wp_die(__('You do not have permission to access this page.'));
    }

    // Get date range from query param
    $days = isset($_GET['days']) ? absint($_GET['days']) : 30;
    if (!in_array($days, array(7, 14, 30, 60, 90))) $days = 30;

    // Ensure tables exist
    global $wpdb;
    $views_table = $wpdb->prefix . 'mh_page_views';
    if ($wpdb->get_var("SHOW TABLES LIKE '$views_table'") !== $views_table) {
        echo '<div class="wrap"><h1>Site Analytics</h1>';
        echo '<div class="notice notice-warning"><p>Analytics tables have not been created yet. ';
        echo 'Please deactivate and reactivate the MicroHub plugin to create them, or ';
        echo '<a href="' . esc_url(admin_url('admin.php?page=microhub-analytics&mh_create_tables=1')) . '">click here to create them now</a>.</p></div></div>';

        if (isset($_GET['mh_create_tables'])) {
            require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-activator.php';
            MicroHub_Activator::activate();
            echo '<div class="notice notice-success"><p>Tables created successfully! <a href="' . esc_url(admin_url('admin.php?page=microhub-analytics')) . '">Refresh page</a></p></div>';
        }
        return;
    }

    // Fetch all data
    $total_visitors = MicroHub_Tracking::get_visitor_count($days);
    $total_views = MicroHub_Tracking::get_pageview_count($days);
    $avg_duration = MicroHub_Tracking::get_avg_duration($days);
    $daily_data = MicroHub_Tracking::get_daily_views($days);
    $top_pages = MicroHub_Tracking::get_top_pages($days);
    $top_referrers = MicroHub_Tracking::get_top_referrers($days);
    $tag_usage = MicroHub_Tracking::get_tag_usage($days);
    $link_clicks = MicroHub_Tracking::get_link_clicks($days);
    $search_queries = MicroHub_Tracking::get_search_queries($days);
    $filter_usage = MicroHub_Tracking::get_filter_usage($days);
    $bot_stats = MicroHub_Tracking::get_bot_stats($days);
    $total_blocks = MicroHub_Tracking::get_total_bot_blocks($days);

    // Format avg duration
    $avg_mins = floor($avg_duration / 60);
    $avg_secs = round($avg_duration % 60);
    $avg_formatted = $avg_mins > 0 ? $avg_mins . 'm ' . $avg_secs . 's' : $avg_secs . 's';

    // Prepare chart data
    $chart_labels = array();
    $chart_views = array();
    $chart_visitors = array();
    foreach ($daily_data as $row) {
        $chart_labels[] = date('M j', strtotime($row->date));
        $chart_views[] = (int)$row->views;
        $chart_visitors[] = (int)$row->visitors;
    }

    ?>
    <div class="wrap mh-analytics-wrap">
        <h1>MicroHub Site Analytics</h1>

        <!-- Date Range Selector -->
        <div class="mh-analytics-controls" style="margin: 15px 0;">
            <?php
            $ranges = array(7 => '7 days', 14 => '14 days', 30 => '30 days', 60 => '60 days', 90 => '90 days');
            foreach ($ranges as $d => $label) :
                $url = add_query_arg('days', $d, admin_url('admin.php?page=microhub-analytics'));
                $active = ($d === $days) ? 'button-primary' : 'button-secondary';
            ?>
                <a href="<?php echo esc_url($url); ?>" class="button <?php echo $active; ?>"><?php echo $label; ?></a>
            <?php endforeach; ?>
        </div>

        <!-- Overview Cards -->
        <div class="mh-stats-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px;">
            <div class="mh-stat-card" style="background: #fff; border: 1px solid #c3c4c7; border-left: 4px solid #2271b1; padding: 20px; border-radius: 4px;">
                <div style="font-size: 32px; font-weight: 700; color: #1d2327;"><?php echo number_format($total_visitors); ?></div>
                <div style="color: #646970; font-size: 14px; margin-top: 5px;">Unique Visitors</div>
            </div>
            <div class="mh-stat-card" style="background: #fff; border: 1px solid #c3c4c7; border-left: 4px solid #00a32a; padding: 20px; border-radius: 4px;">
                <div style="font-size: 32px; font-weight: 700; color: #1d2327;"><?php echo number_format($total_views); ?></div>
                <div style="color: #646970; font-size: 14px; margin-top: 5px;">Page Views</div>
            </div>
            <div class="mh-stat-card" style="background: #fff; border: 1px solid #c3c4c7; border-left: 4px solid #dba617; padding: 20px; border-radius: 4px;">
                <div style="font-size: 32px; font-weight: 700; color: #1d2327;"><?php echo esc_html($avg_formatted); ?></div>
                <div style="color: #646970; font-size: 14px; margin-top: 5px;">Avg. Time on Page</div>
            </div>
            <div class="mh-stat-card" style="background: #fff; border: 1px solid #c3c4c7; border-left: 4px solid #d63638; padding: 20px; border-radius: 4px;">
                <div style="font-size: 32px; font-weight: 700; color: #1d2327;"><?php echo number_format($total_blocks); ?></div>
                <div style="color: #646970; font-size: 14px; margin-top: 5px;">Bots Blocked</div>
            </div>
        </div>

        <!-- Traffic Chart -->
        <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; margin-bottom: 25px; border-radius: 4px;">
            <h2 style="margin-top: 0;">Traffic Overview</h2>
            <canvas id="mh-traffic-chart" height="80"></canvas>
        </div>

        <!-- Two-column layout -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">

            <!-- Top Pages -->
            <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; border-radius: 4px;">
                <h2 style="margin-top: 0;">Top Pages</h2>
                <?php if (empty($top_pages)) : ?>
                    <p style="color: #646970;">No page view data yet.</p>
                <?php else : ?>
                    <table class="widefat striped" style="border: 0;">
                        <thead>
                            <tr>
                                <th>Page</th>
                                <th style="width:60px; text-align:right;">Views</th>
                                <th style="width:70px; text-align:right;">Visitors</th>
                                <th style="width:70px; text-align:right;">Avg Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($top_pages as $page) :
                                $d = (int)$page->avg_duration;
                                $dm = floor($d / 60);
                                $ds = $d % 60;
                                $dt = $dm > 0 ? $dm . 'm ' . $ds . 's' : $ds . 's';
                            ?>
                            <tr>
                                <td>
                                    <strong><?php echo esc_html($page->page_title ?: $page->page_url); ?></strong>
                                    <div style="color:#646970; font-size:12px;"><?php echo esc_html(substr($page->page_url, 0, 60)); ?></div>
                                </td>
                                <td style="text-align:right;"><?php echo number_format($page->views); ?></td>
                                <td style="text-align:right;"><?php echo number_format($page->visitors); ?></td>
                                <td style="text-align:right;"><?php echo esc_html($dt); ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>

            <!-- Top Referrers -->
            <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; border-radius: 4px;">
                <h2 style="margin-top: 0;">Top Referrers</h2>
                <?php if (empty($top_referrers)) : ?>
                    <p style="color: #646970;">No referrer data yet.</p>
                <?php else : ?>
                    <table class="widefat striped" style="border: 0;">
                        <thead>
                            <tr>
                                <th>Source</th>
                                <th style="width:80px; text-align:right;">Visits</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($top_referrers as $ref) :
                                $domain = wp_parse_url($ref->referrer, PHP_URL_HOST) ?: $ref->referrer;
                            ?>
                            <tr>
                                <td>
                                    <strong><?php echo esc_html($domain); ?></strong>
                                    <div style="color:#646970; font-size:12px;"><?php echo esc_html(substr($ref->referrer, 0, 80)); ?></div>
                                </td>
                                <td style="text-align:right;"><?php echo number_format($ref->visits); ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div>

        <!-- Tag Usage & Link Clicks -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">

            <!-- Tag/Taxonomy Usage -->
            <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; border-radius: 4px;">
                <h2 style="margin-top: 0;">Tag & Taxonomy Usage</h2>
                <p style="color: #646970; font-size: 13px;">Which tags visitors click on most (techniques, microscopes, organisms, etc.)</p>
                <?php if (empty($tag_usage)) : ?>
                    <p style="color: #646970;">No tag click data yet.</p>
                <?php else : ?>
                    <table class="widefat striped" style="border: 0;">
                        <thead>
                            <tr>
                                <th>Tag</th>
                                <th style="width:80px; text-align:right;">Clicks</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($tag_usage as $tag) : ?>
                            <tr>
                                <td><code><?php echo esc_html($tag->event_value); ?></code></td>
                                <td style="text-align:right;"><?php echo number_format($tag->clicks); ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>

            <!-- Link Clicks -->
            <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; border-radius: 4px;">
                <h2 style="margin-top: 0;">Link Clicks</h2>
                <p style="color: #646970; font-size: 13px;">Internal and outbound links visitors follow</p>
                <?php if (empty($link_clicks)) : ?>
                    <p style="color: #646970;">No link click data yet.</p>
                <?php else : ?>
                    <table class="widefat striped" style="border: 0;">
                        <thead>
                            <tr>
                                <th>Link</th>
                                <th style="width:80px; text-align:right;">Clicks</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($link_clicks as $link) : ?>
                            <tr>
                                <td>
                                    <strong><?php echo esc_html($link->event_value ?: '(no text)'); ?></strong>
                                    <div style="color:#646970; font-size:12px; word-break:break-all;"><?php echo esc_html(substr($link->event_target, 0, 80)); ?></div>
                                </td>
                                <td style="text-align:right;"><?php echo number_format($link->clicks); ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div>

        <!-- Search Queries & Filter Usage -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">

            <!-- Search Queries -->
            <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; border-radius: 4px;">
                <h2 style="margin-top: 0;">Search Queries</h2>
                <?php if (empty($search_queries)) : ?>
                    <p style="color: #646970;">No search data yet.</p>
                <?php else : ?>
                    <table class="widefat striped" style="border: 0;">
                        <thead>
                            <tr>
                                <th>Query</th>
                                <th style="width:80px; text-align:right;">Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($search_queries as $q) : ?>
                            <tr>
                                <td><?php echo esc_html($q->event_value); ?></td>
                                <td style="text-align:right;"><?php echo number_format($q->count); ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>

            <!-- Filter Usage -->
            <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; border-radius: 4px;">
                <h2 style="margin-top: 0;">Filter Usage</h2>
                <p style="color: #646970; font-size: 13px;">Which dropdown filters visitors use most</p>
                <?php if (empty($filter_usage)) : ?>
                    <p style="color: #646970;">No filter usage data yet.</p>
                <?php else : ?>
                    <table class="widefat striped" style="border: 0;">
                        <thead>
                            <tr>
                                <th>Filter</th>
                                <th>Value</th>
                                <th style="width:70px; text-align:right;">Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($filter_usage as $f) : ?>
                            <tr>
                                <td><code><?php echo esc_html($f->filter_name); ?></code></td>
                                <td><?php echo esc_html($f->event_value); ?></td>
                                <td style="text-align:right;"><?php echo number_format($f->count); ?></td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div>

        <!-- Bot Protection Stats -->
        <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; margin-bottom: 25px; border-radius: 4px;">
            <h2 style="margin-top: 0;">Bot Protection</h2>
            <p style="color: #646970; font-size: 13px;">Background bot detection is active. Bad bots are blocked automatically.</p>

            <?php if (empty($bot_stats)) : ?>
                <p style="color: #646970;">No bots blocked in this period.</p>
            <?php else : ?>
                <table class="widefat striped" style="max-width: 500px; border: 0;">
                    <thead>
                        <tr>
                            <th>Block Reason</th>
                            <th style="width:100px; text-align:right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php
                        $reason_labels = array(
                            'bad_ua'             => 'Bad User Agent (scraper/bot)',
                            'empty_ua'           => 'Empty User Agent',
                            'rate_limit'         => 'Rate Limit Exceeded',
                            'honeypot'           => 'Honeypot Triggered',
                            'suspicious_pattern' => 'Suspicious URL Pattern',
                        );
                        foreach ($bot_stats as $bs) : ?>
                        <tr>
                            <td><?php echo esc_html($reason_labels[$bs->reason] ?? $bs->reason); ?></td>
                            <td style="text-align:right;"><?php echo number_format($bs->blocks); ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>

        <!-- Data Management -->
        <div style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; border-radius: 4px;">
            <h2 style="margin-top: 0;">Data Management</h2>
            <p style="color: #646970;">Analytics data is automatically cleaned up after 90 days. You can also clear it manually.</p>

            <?php if (isset($_POST['mh_clear_analytics']) && check_admin_referer('mh_clear_analytics_nonce')) :
                $wpdb->query("TRUNCATE TABLE {$wpdb->prefix}mh_page_views");
                $wpdb->query("TRUNCATE TABLE {$wpdb->prefix}mh_tracking_events");
                $wpdb->query("TRUNCATE TABLE {$wpdb->prefix}mh_bot_blocks");
            ?>
                <div class="notice notice-success"><p>All analytics data has been cleared.</p></div>
            <?php endif; ?>

            <form method="post" action="">
                <?php wp_nonce_field('mh_clear_analytics_nonce'); ?>
                <input type="submit" name="mh_clear_analytics" class="button" style="color: #d63638; border-color: #d63638;"
                       value="Clear All Analytics Data"
                       onclick="return confirm('Are you sure? This will delete all tracking data permanently.');" />
            </form>
        </div>
    </div>

    <!-- Chart.js from CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script>
    (function() {
        var ctx = document.getElementById('mh-traffic-chart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: <?php echo wp_json_encode($chart_labels); ?>,
                datasets: [
                    {
                        label: 'Page Views',
                        data: <?php echo wp_json_encode($chart_views); ?>,
                        borderColor: '#2271b1',
                        backgroundColor: 'rgba(34, 113, 177, 0.1)',
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3
                    },
                    {
                        label: 'Unique Visitors',
                        data: <?php echo wp_json_encode($chart_visitors); ?>,
                        borderColor: '#00a32a',
                        backgroundColor: 'rgba(0, 163, 42, 0.1)',
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: { position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } }
                }
            }
        });
    })();
    </script>

    <style>
    .mh-analytics-wrap h2 { font-size: 16px; font-weight: 600; }
    .mh-analytics-wrap .widefat td, .mh-analytics-wrap .widefat th { padding: 8px 10px; }
    @media (max-width: 960px) {
        .mh-stats-grid { grid-template-columns: repeat(2, 1fr) !important; }
    }
    </style>
    <?php
}
