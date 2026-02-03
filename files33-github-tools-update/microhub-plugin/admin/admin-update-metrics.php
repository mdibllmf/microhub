<?php
/**
 * MicroHub Update Metrics Admin Page
 *
 * Allows updating citation counts and GitHub metrics for existing papers
 * without re-importing everything.
 */

if (!defined('ABSPATH')) exit;

// Register the admin page
add_action('admin_menu', function() {
    add_submenu_page(
        'microhub-settings',
        'Update Metrics',
        'Update Metrics',
        'manage_options',
        'microhub-update-metrics',
        'microhub_update_metrics_page'
    );
});

// AJAX handler for updating citations
add_action('wp_ajax_microhub_update_citations', 'microhub_ajax_update_citations');
function microhub_ajax_update_citations() {
    check_ajax_referer('microhub_update_metrics_nonce', 'nonce');

    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied');
    }

    $paper_id = intval($_POST['paper_id'] ?? 0);
    if (!$paper_id) {
        wp_send_json_error('Invalid paper ID');
    }

    $doi = get_post_meta($paper_id, '_mh_doi', true);
    $pubmed_id = get_post_meta($paper_id, '_mh_pubmed_id', true);
    $current_citations = intval(get_post_meta($paper_id, '_mh_citation_count', true));

    if (!$doi && !$pubmed_id) {
        wp_send_json_error('Paper has no DOI or PubMed ID');
    }

    // Try Semantic Scholar
    $new_citations = microhub_fetch_citations_semantic_scholar($doi, $pubmed_id);

    // Fallback to CrossRef
    if ($new_citations === null && $doi) {
        $new_citations = microhub_fetch_citations_crossref($doi);
    }

    if ($new_citations !== null) {
        update_post_meta($paper_id, '_mh_citation_count', $new_citations);
        update_post_meta($paper_id, '_mh_citations_updated', current_time('mysql'));

        wp_send_json_success(array(
            'old_citations' => $current_citations,
            'new_citations' => $new_citations,
            'changed' => $new_citations !== $current_citations,
        ));
    } else {
        wp_send_json_error('Could not fetch citations from API');
    }
}

// AJAX handler for updating GitHub metrics
add_action('wp_ajax_microhub_update_github', 'microhub_ajax_update_github');
function microhub_ajax_update_github() {
    check_ajax_referer('microhub_update_metrics_nonce', 'nonce');

    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied');
    }

    $paper_id = intval($_POST['paper_id'] ?? 0);
    if (!$paper_id) {
        wp_send_json_error('Invalid paper ID');
    }

    $github_tools_json = get_post_meta($paper_id, '_mh_github_tools', true);
    $github_tools = json_decode($github_tools_json, true) ?: array();

    if (empty($github_tools)) {
        wp_send_json_error('Paper has no GitHub tools');
    }

    $updated_count = 0;
    foreach ($github_tools as &$tool) {
        $full_name = $tool['full_name'] ?? '';
        if (!$full_name) continue;

        $metrics = microhub_fetch_github_metrics($full_name);
        if (!$metrics) continue;

        // Update metrics
        $tool['stars'] = $metrics['stars'] ?? $tool['stars'] ?? 0;
        $tool['forks'] = $metrics['forks'] ?? $tool['forks'] ?? 0;
        $tool['open_issues'] = $metrics['open_issues'] ?? $tool['open_issues'] ?? 0;
        $tool['health_score'] = $metrics['health_score'] ?? $tool['health_score'] ?? 0;
        $tool['is_archived'] = $metrics['is_archived'] ?? $tool['is_archived'] ?? false;
        $tool['last_commit_date'] = $metrics['last_commit_date'] ?? $tool['last_commit_date'] ?? '';
        $tool['last_release'] = $metrics['last_release'] ?? $tool['last_release'] ?? '';

        // Fill in missing data
        if (empty($tool['description']) && !empty($metrics['description'])) {
            $tool['description'] = $metrics['description'];
        }
        if (empty($tool['language']) && !empty($metrics['language'])) {
            $tool['language'] = $metrics['language'];
        }
        if (empty($tool['license']) && !empty($metrics['license'])) {
            $tool['license'] = $metrics['license'];
        }
        if (empty($tool['topics']) && !empty($metrics['topics'])) {
            $tool['topics'] = $metrics['topics'];
        }

        $updated_count++;

        // Small delay between GitHub API calls
        usleep(500000); // 0.5 seconds
    }

    if ($updated_count > 0) {
        update_post_meta($paper_id, '_mh_github_tools', wp_json_encode($github_tools));
        update_post_meta($paper_id, '_mh_github_updated', current_time('mysql'));
    }

    wp_send_json_success(array(
        'tools_updated' => $updated_count,
        'total_tools' => count($github_tools),
    ));
}

// AJAX handler for batch updates
add_action('wp_ajax_microhub_batch_update', 'microhub_ajax_batch_update');
function microhub_ajax_batch_update() {
    check_ajax_referer('microhub_update_metrics_nonce', 'nonce');

    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied');
    }

    $update_type = sanitize_text_field($_POST['update_type'] ?? 'citations');
    $offset = intval($_POST['offset'] ?? 0);
    $batch_size = intval($_POST['batch_size'] ?? 10);

    // Get papers
    $args = array(
        'post_type' => 'mh_paper',
        'post_status' => 'publish',
        'posts_per_page' => $batch_size,
        'offset' => $offset,
        'fields' => 'ids',
    );

    // Filter based on update type
    if ($update_type === 'citations') {
        $args['meta_query'] = array(
            'relation' => 'OR',
            array('key' => '_mh_doi', 'compare' => 'EXISTS'),
            array('key' => '_mh_pubmed_id', 'compare' => 'EXISTS'),
        );
    } elseif ($update_type === 'github') {
        $args['meta_query'] = array(
            array(
                'key' => '_mh_github_tools',
                'value' => '[]',
                'compare' => '!=',
            ),
        );
    }

    $paper_ids = get_posts($args);
    $total = wp_count_posts('mh_paper')->publish;

    $results = array(
        'processed' => 0,
        'updated' => 0,
        'errors' => 0,
    );

    foreach ($paper_ids as $paper_id) {
        try {
            if ($update_type === 'citations') {
                $result = microhub_update_single_citations($paper_id);
            } else {
                $result = microhub_update_single_github($paper_id);
            }

            $results['processed']++;
            if ($result) {
                $results['updated']++;
            }
        } catch (Exception $e) {
            $results['errors']++;
        }

        // Rate limiting
        if ($update_type === 'citations') {
            usleep(1000000); // 1 second
        } else {
            usleep(500000); // 0.5 seconds
        }
    }

    wp_send_json_success(array(
        'results' => $results,
        'offset' => $offset,
        'next_offset' => $offset + count($paper_ids),
        'total' => $total,
        'done' => count($paper_ids) < $batch_size,
    ));
}

/**
 * Update citations for a single paper
 */
function microhub_update_single_citations($paper_id) {
    $doi = get_post_meta($paper_id, '_mh_doi', true);
    $pubmed_id = get_post_meta($paper_id, '_mh_pubmed_id', true);
    $current = intval(get_post_meta($paper_id, '_mh_citation_count', true));

    if (!$doi && !$pubmed_id) return false;

    $new = microhub_fetch_citations_semantic_scholar($doi, $pubmed_id);
    if ($new === null && $doi) {
        $new = microhub_fetch_citations_crossref($doi);
    }

    if ($new !== null && $new !== $current) {
        update_post_meta($paper_id, '_mh_citation_count', $new);
        update_post_meta($paper_id, '_mh_citations_updated', current_time('mysql'));
        return true;
    }

    return false;
}

/**
 * Update GitHub metrics for a single paper
 */
function microhub_update_single_github($paper_id) {
    $github_tools_json = get_post_meta($paper_id, '_mh_github_tools', true);
    $github_tools = json_decode($github_tools_json, true) ?: array();

    if (empty($github_tools)) return false;

    $updated = false;
    foreach ($github_tools as &$tool) {
        $full_name = $tool['full_name'] ?? '';
        if (!$full_name) continue;

        $metrics = microhub_fetch_github_metrics($full_name);
        if (!$metrics) continue;

        $old_stars = $tool['stars'] ?? 0;
        $tool['stars'] = $metrics['stars'] ?? $old_stars;
        $tool['forks'] = $metrics['forks'] ?? $tool['forks'] ?? 0;
        $tool['open_issues'] = $metrics['open_issues'] ?? $tool['open_issues'] ?? 0;
        $tool['health_score'] = $metrics['health_score'] ?? $tool['health_score'] ?? 0;
        $tool['is_archived'] = $metrics['is_archived'] ?? false;
        $tool['last_commit_date'] = $metrics['last_commit_date'] ?? '';
        $tool['last_release'] = $metrics['last_release'] ?? '';

        if (empty($tool['description'])) $tool['description'] = $metrics['description'] ?? '';
        if (empty($tool['language'])) $tool['language'] = $metrics['language'] ?? '';
        if (empty($tool['license'])) $tool['license'] = $metrics['license'] ?? '';
        if (empty($tool['topics'])) $tool['topics'] = $metrics['topics'] ?? array();

        if ($tool['stars'] !== $old_stars) $updated = true;

        usleep(500000);
    }

    if ($updated) {
        update_post_meta($paper_id, '_mh_github_tools', wp_json_encode($github_tools));
        update_post_meta($paper_id, '_mh_github_updated', current_time('mysql'));
    }

    return $updated;
}

/**
 * Fetch citations from Semantic Scholar API
 */
function microhub_fetch_citations_semantic_scholar($doi, $pubmed_id) {
    $api_key = get_option('microhub_semantic_scholar_api_key', '');
    $headers = array('Accept' => 'application/json');
    if ($api_key) {
        $headers['x-api-key'] = $api_key;
    }

    // Try DOI first
    if ($doi) {
        $url = "https://api.semanticscholar.org/graph/v1/paper/DOI:" . urlencode($doi) . "?fields=citationCount";
        $response = wp_remote_get($url, array('headers' => $headers, 'timeout' => 15));

        if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
            $data = json_decode(wp_remote_retrieve_body($response), true);
            if (isset($data['citationCount'])) {
                return intval($data['citationCount']);
            }
        }
    }

    // Try PubMed ID
    if ($pubmed_id) {
        $url = "https://api.semanticscholar.org/graph/v1/paper/PMID:" . urlencode($pubmed_id) . "?fields=citationCount";
        $response = wp_remote_get($url, array('headers' => $headers, 'timeout' => 15));

        if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
            $data = json_decode(wp_remote_retrieve_body($response), true);
            if (isset($data['citationCount'])) {
                return intval($data['citationCount']);
            }
        }
    }

    return null;
}

/**
 * Fetch citations from CrossRef API
 */
function microhub_fetch_citations_crossref($doi) {
    if (!$doi) return null;

    $url = "https://api.crossref.org/works/" . urlencode($doi);
    $response = wp_remote_get($url, array(
        'timeout' => 15,
        'headers' => array(
            'User-Agent' => 'MicroHub/1.0 (WordPress Plugin)'
        )
    ));

    if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
        $data = json_decode(wp_remote_retrieve_body($response), true);
        if (isset($data['message']['is-referenced-by-count'])) {
            return intval($data['message']['is-referenced-by-count']);
        }
    }

    return null;
}

/**
 * Fetch GitHub repository metrics
 */
function microhub_fetch_github_metrics($full_name) {
    if (!$full_name || strpos($full_name, '/') === false) {
        return null;
    }

    $github_token = get_option('microhub_github_token', '');
    $headers = array('Accept' => 'application/vnd.github.v3+json');
    if ($github_token) {
        $headers['Authorization'] = 'token ' . $github_token;
    }

    // Main repo info
    $url = "https://api.github.com/repos/" . urlencode($full_name);
    $response = wp_remote_get($url, array('headers' => $headers, 'timeout' => 15));

    if (is_wp_error($response)) {
        return null;
    }

    $code = wp_remote_retrieve_response_code($response);
    if ($code === 404) {
        return array('exists' => false, 'is_archived' => true);
    }
    if ($code !== 200) {
        return null;
    }

    $data = json_decode(wp_remote_retrieve_body($response), true);

    $metrics = array(
        'exists' => true,
        'full_name' => $data['full_name'] ?? $full_name,
        'description' => substr($data['description'] ?? '', 0, 500),
        'stars' => intval($data['stargazers_count'] ?? 0),
        'forks' => intval($data['forks_count'] ?? 0),
        'open_issues' => intval($data['open_issues_count'] ?? 0),
        'language' => $data['language'] ?? '',
        'license' => isset($data['license']['spdx_id']) ? $data['license']['spdx_id'] : '',
        'topics' => $data['topics'] ?? array(),
        'is_archived' => $data['archived'] ?? false,
        'pushed_at' => $data['pushed_at'] ?? '',
    );

    // Get last commit
    $commits_url = "https://api.github.com/repos/" . urlencode($full_name) . "/commits?per_page=1";
    $commits_response = wp_remote_get($commits_url, array('headers' => $headers, 'timeout' => 10));
    if (!is_wp_error($commits_response) && wp_remote_retrieve_response_code($commits_response) === 200) {
        $commits = json_decode(wp_remote_retrieve_body($commits_response), true);
        if (!empty($commits[0]['commit']['committer']['date'])) {
            $metrics['last_commit_date'] = $commits[0]['commit']['committer']['date'];
        }
    }

    // Get latest release
    $release_url = "https://api.github.com/repos/" . urlencode($full_name) . "/releases/latest";
    $release_response = wp_remote_get($release_url, array('headers' => $headers, 'timeout' => 10));
    if (!is_wp_error($release_response) && wp_remote_retrieve_response_code($release_response) === 200) {
        $release = json_decode(wp_remote_retrieve_body($release_response), true);
        $metrics['last_release'] = $release['tag_name'] ?? '';
        $metrics['last_release_date'] = $release['published_at'] ?? '';
    }

    // Compute health score
    $metrics['health_score'] = microhub_compute_github_health_score($metrics);

    return $metrics;
}

/**
 * Compute GitHub repository health score
 */
function microhub_compute_github_health_score($metrics) {
    if (empty($metrics['exists'])) return 0;
    if (!empty($metrics['is_archived'])) return 10;

    $score = 0;

    // Stars (up to 25)
    $stars = $metrics['stars'] ?? 0;
    if ($stars >= 1000) $score += 25;
    elseif ($stars >= 500) $score += 22;
    elseif ($stars >= 100) $score += 18;
    elseif ($stars >= 50) $score += 14;
    elseif ($stars >= 10) $score += 10;
    elseif ($stars >= 1) $score += 5;

    // Activity (up to 30)
    $last_commit = $metrics['last_commit_date'] ?? $metrics['pushed_at'] ?? '';
    if ($last_commit) {
        try {
            $commit_time = strtotime($last_commit);
            $days_ago = (time() - $commit_time) / 86400;
            if ($days_ago <= 30) $score += 30;
            elseif ($days_ago <= 90) $score += 25;
            elseif ($days_ago <= 180) $score += 20;
            elseif ($days_ago <= 365) $score += 12;
            elseif ($days_ago <= 730) $score += 5;
        } catch (Exception $e) {}
    }

    // Forks (up to 15)
    $forks = $metrics['forks'] ?? 0;
    if ($forks >= 100) $score += 15;
    elseif ($forks >= 50) $score += 12;
    elseif ($forks >= 10) $score += 8;
    elseif ($forks >= 1) $score += 3;

    // Extras
    if (!empty($metrics['description'])) $score += 5;
    if (!empty($metrics['license'])) $score += 5;
    if (!empty($metrics['topics'])) $score += 5;
    if (!empty($metrics['last_release'])) $score += 10;

    return min(100, $score);
}

/**
 * Render the admin page
 */
function microhub_update_metrics_page() {
    global $wpdb;

    // Handle settings save
    if (isset($_POST['save_api_keys']) && check_admin_referer('microhub_api_keys_nonce')) {
        if (isset($_POST['github_token'])) {
            update_option('microhub_github_token', sanitize_text_field($_POST['github_token']));
        }
        if (isset($_POST['semantic_scholar_api_key'])) {
            update_option('microhub_semantic_scholar_api_key', sanitize_text_field($_POST['semantic_scholar_api_key']));
        }
        echo '<div class="notice notice-success"><p>API keys saved!</p></div>';
    }

    // Get statistics
    $total_papers = wp_count_posts('mh_paper')->publish;
    $papers_with_doi = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_doi' AND meta_value != ''");
    $papers_with_github = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_tools' AND meta_value != '' AND meta_value != '[]'");

    $github_token = get_option('microhub_github_token', '');
    $semantic_scholar_key = get_option('microhub_semantic_scholar_api_key', '');

    $nonce = wp_create_nonce('microhub_update_metrics_nonce');
    ?>
    <div class="wrap">
        <h1>🔄 Update Metrics</h1>
        <p>Update citation counts and GitHub metrics for your papers without re-importing everything.</p>

        <!-- API Keys Section -->
        <div class="card" style="max-width: 800px; margin-bottom: 20px;">
            <h2>🔑 API Keys (Optional)</h2>
            <p>API keys allow higher rate limits and better performance.</p>
            <form method="post">
                <?php wp_nonce_field('microhub_api_keys_nonce'); ?>
                <table class="form-table">
                    <tr>
                        <th>GitHub Token</th>
                        <td>
                            <input type="password" name="github_token" value="<?php echo esc_attr($github_token); ?>" class="regular-text" />
                            <p class="description">
                                Without token: 60 requests/hour. With token: 5,000 requests/hour.<br>
                                <a href="https://github.com/settings/tokens" target="_blank">Create a GitHub token</a> (no scopes needed for public repos)
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <th>Semantic Scholar API Key</th>
                        <td>
                            <input type="password" name="semantic_scholar_api_key" value="<?php echo esc_attr($semantic_scholar_key); ?>" class="regular-text" />
                            <p class="description">
                                Optional. Higher rate limits for citation lookups.<br>
                                <a href="https://www.semanticscholar.org/product/api" target="_blank">Request API access</a>
                            </p>
                        </td>
                    </tr>
                </table>
                <p><input type="submit" name="save_api_keys" class="button button-primary" value="Save API Keys" /></p>
            </form>
        </div>

        <!-- Statistics -->
        <div class="card" style="max-width: 800px; margin-bottom: 20px;">
            <h2>📊 Current Data</h2>
            <table class="widefat" style="max-width: 400px;">
                <tr><td>Total Papers</td><td><strong><?php echo number_format($total_papers); ?></strong></td></tr>
                <tr><td>Papers with DOI (can update citations)</td><td><strong><?php echo number_format($papers_with_doi); ?></strong></td></tr>
                <tr><td>Papers with GitHub Tools</td><td><strong><?php echo number_format($papers_with_github); ?></strong></td></tr>
            </table>
        </div>

        <!-- Batch Update Section -->
        <div class="card" style="max-width: 800px; margin-bottom: 20px;">
            <h2>🔄 Batch Update</h2>
            <p>Update metrics for all papers. This runs in batches to avoid timeouts.</p>

            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <div>
                    <h3>📊 Update Citations</h3>
                    <p>Fetch latest citation counts from Semantic Scholar and CrossRef.</p>
                    <button type="button" id="btn-batch-citations" class="button button-primary">
                        Start Citation Update
                    </button>
                </div>
                <div>
                    <h3>💻 Update GitHub Metrics</h3>
                    <p>Fetch latest stars, forks, and activity from GitHub.</p>
                    <button type="button" id="btn-batch-github" class="button button-primary">
                        Start GitHub Update
                    </button>
                </div>
            </div>

            <div id="batch-progress" style="display: none; background: #f0f0f1; padding: 15px; border-radius: 4px;">
                <div style="margin-bottom: 10px;">
                    <strong id="progress-text">Processing...</strong>
                </div>
                <div style="background: #ddd; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div id="progress-bar" style="background: #2271b1; height: 100%; width: 0%; transition: width 0.3s;"></div>
                </div>
                <div id="progress-stats" style="margin-top: 10px; font-size: 13px; color: #666;"></div>
            </div>
        </div>

        <!-- Single Paper Update -->
        <div class="card" style="max-width: 800px;">
            <h2>🎯 Update Single Paper</h2>
            <p>Update metrics for a specific paper by ID.</p>
            <div style="display: flex; gap: 10px; align-items: flex-end;">
                <div>
                    <label for="single-paper-id"><strong>Paper ID:</strong></label><br>
                    <input type="number" id="single-paper-id" class="regular-text" placeholder="Enter paper post ID" style="width: 150px;" />
                </div>
                <button type="button" id="btn-single-citations" class="button">Update Citations</button>
                <button type="button" id="btn-single-github" class="button">Update GitHub</button>
            </div>
            <div id="single-result" style="margin-top: 15px;"></div>
        </div>
    </div>

    <script>
    jQuery(document).ready(function($) {
        const nonce = '<?php echo $nonce; ?>';
        const ajaxUrl = '<?php echo admin_url('admin-ajax.php'); ?>';

        // Batch updates
        let batchRunning = false;

        function runBatchUpdate(updateType, offset = 0) {
            if (!batchRunning) return;

            $.post(ajaxUrl, {
                action: 'microhub_batch_update',
                nonce: nonce,
                update_type: updateType,
                offset: offset,
                batch_size: 10
            }, function(response) {
                if (response.success) {
                    const data = response.data;
                    const progress = Math.min(100, Math.round((data.next_offset / data.total) * 100));

                    $('#progress-bar').css('width', progress + '%');
                    $('#progress-text').text('Processing... ' + data.next_offset + ' / ' + data.total);
                    $('#progress-stats').html(
                        'Processed: ' + data.results.processed +
                        ' | Updated: ' + data.results.updated +
                        ' | Errors: ' + data.results.errors
                    );

                    if (!data.done && batchRunning) {
                        runBatchUpdate(updateType, data.next_offset);
                    } else {
                        batchRunning = false;
                        $('#progress-text').text('Complete!');
                        $('#btn-batch-citations, #btn-batch-github').prop('disabled', false);
                    }
                } else {
                    batchRunning = false;
                    $('#progress-text').text('Error: ' + response.data);
                    $('#btn-batch-citations, #btn-batch-github').prop('disabled', false);
                }
            }).fail(function() {
                batchRunning = false;
                $('#progress-text').text('Request failed');
                $('#btn-batch-citations, #btn-batch-github').prop('disabled', false);
            });
        }

        $('#btn-batch-citations').click(function() {
            if (batchRunning) return;
            if (!confirm('Update citations for all papers? This may take a while.')) return;

            batchRunning = true;
            $(this).prop('disabled', true);
            $('#btn-batch-github').prop('disabled', true);
            $('#batch-progress').show();
            $('#progress-bar').css('width', '0%');
            $('#progress-text').text('Starting citation update...');
            $('#progress-stats').text('');

            runBatchUpdate('citations', 0);
        });

        $('#btn-batch-github').click(function() {
            if (batchRunning) return;
            if (!confirm('Update GitHub metrics for all papers? This may take a while.')) return;

            batchRunning = true;
            $(this).prop('disabled', true);
            $('#btn-batch-citations').prop('disabled', true);
            $('#batch-progress').show();
            $('#progress-bar').css('width', '0%');
            $('#progress-text').text('Starting GitHub update...');
            $('#progress-stats').text('');

            runBatchUpdate('github', 0);
        });

        // Single paper updates
        $('#btn-single-citations').click(function() {
            const paperId = $('#single-paper-id').val();
            if (!paperId) {
                alert('Please enter a paper ID');
                return;
            }

            $('#single-result').html('<em>Updating citations...</em>');

            $.post(ajaxUrl, {
                action: 'microhub_update_citations',
                nonce: nonce,
                paper_id: paperId
            }, function(response) {
                if (response.success) {
                    const d = response.data;
                    if (d.changed) {
                        $('#single-result').html('<div class="notice notice-success inline"><p>Citations updated: ' + d.old_citations + ' → ' + d.new_citations + '</p></div>');
                    } else {
                        $('#single-result').html('<div class="notice notice-info inline"><p>No change. Citations: ' + d.new_citations + '</p></div>');
                    }
                } else {
                    $('#single-result').html('<div class="notice notice-error inline"><p>Error: ' + response.data + '</p></div>');
                }
            });
        });

        $('#btn-single-github').click(function() {
            const paperId = $('#single-paper-id').val();
            if (!paperId) {
                alert('Please enter a paper ID');
                return;
            }

            $('#single-result').html('<em>Updating GitHub metrics...</em>');

            $.post(ajaxUrl, {
                action: 'microhub_update_github',
                nonce: nonce,
                paper_id: paperId
            }, function(response) {
                if (response.success) {
                    const d = response.data;
                    $('#single-result').html('<div class="notice notice-success inline"><p>Updated ' + d.tools_updated + ' of ' + d.total_tools + ' GitHub tools</p></div>');
                } else {
                    $('#single-result').html('<div class="notice notice-error inline"><p>Error: ' + response.data + '</p></div>');
                }
            });
        });
    });
    </script>

    <style>
    .card { background: white; border: 1px solid #ccd0d4; padding: 20px; box-shadow: 0 1px 1px rgba(0,0,0,0.04); }
    .card h2 { margin-top: 0; }
    .notice.inline { margin: 0; }
    </style>
    <?php
}
