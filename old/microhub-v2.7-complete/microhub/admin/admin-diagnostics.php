<?php
/**
 * MicroHub Diagnostic Tool
 * Checks data integrity and shows what fields are populated
 */

add_action('admin_menu', 'microhub_add_diagnostic_menu');

function microhub_add_diagnostic_menu() {
    add_submenu_page(
        'microhub-settings',
        __('Diagnostics', 'microhub'),
        __('Diagnostics', 'microhub'),
        'manage_options',
        'microhub-diagnostics',
        'microhub_diagnostic_page'
    );
}

function microhub_diagnostic_page() {
    global $wpdb;
    
    // Get counts
    $total_papers = wp_count_posts('mh_paper')->publish;
    
    // Check enrichment data
    $with_protocols = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != '' AND meta_value != '[]' AND meta_value != 'null'");
    $with_github = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''");
    $with_repos = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_repositories' AND meta_value != '' AND meta_value != '[]' AND meta_value != 'null'");
    $with_rrids = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_rrids' AND meta_value != '' AND meta_value != '[]' AND meta_value != 'null'");
    $with_facility = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_facility' AND meta_value != ''");
    $with_abstract = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_abstract' AND meta_value != ''");
    $with_doi = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_doi' AND meta_value != ''");
    
    // Get sample papers with enrichment
    $sample_with_protocols = $wpdb->get_results("
        SELECT p.ID, p.post_title, pm.meta_value 
        FROM {$wpdb->posts} p 
        JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id 
        WHERE pm.meta_key = '_mh_protocols' 
        AND pm.meta_value != '' 
        AND pm.meta_value != '[]'
        AND p.post_type = 'mh_paper'
        LIMIT 5
    ");
    
    $sample_with_github = $wpdb->get_results("
        SELECT p.ID, p.post_title, pm.meta_value 
        FROM {$wpdb->posts} p 
        JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id 
        WHERE pm.meta_key = '_mh_github_url' 
        AND pm.meta_value != ''
        AND p.post_type = 'mh_paper'
        LIMIT 5
    ");
    
    // Get sample paper to show all meta
    $sample_paper = get_posts(array(
        'post_type' => 'mh_paper',
        'posts_per_page' => 1,
        'meta_key' => '_mh_citation_count',
        'orderby' => 'meta_value_num',
        'order' => 'DESC',
    ));
    
    // Check what meta keys exist for papers
    $all_meta_keys = $wpdb->get_col("
        SELECT DISTINCT pm.meta_key 
        FROM {$wpdb->postmeta} pm
        JOIN {$wpdb->posts} p ON pm.post_id = p.ID
        WHERE p.post_type = 'mh_paper'
        AND pm.meta_key LIKE '_mh_%'
        ORDER BY pm.meta_key
    ");
    
    // Citation stats
    $with_citations = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_citation_count' AND meta_value != '' AND meta_value != '0' AND CAST(meta_value AS UNSIGNED) > 0");
    $avg_citations = $wpdb->get_var("SELECT AVG(CAST(meta_value AS UNSIGNED)) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_citation_count' AND meta_value != '' AND CAST(meta_value AS UNSIGNED) > 0");
    $max_citations = $wpdb->get_var("SELECT MAX(CAST(meta_value AS UNSIGNED)) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_citation_count'");
    ?>
    
    <div class="wrap">
        <h1>🔍 MicroHub Diagnostics</h1>
        <p>This page helps diagnose data import issues and shows what fields are populated.</p>
        
        <h2>📊 Data Summary</h2>
        <table class="widefat striped" style="max-width: 600px;">
            <tbody>
                <tr>
                    <td><strong>Total Papers</strong></td>
                    <td><?php echo number_format($total_papers); ?></td>
                    <td>✅</td>
                </tr>
                <tr>
                    <td><strong>With DOI</strong></td>
                    <td><?php echo number_format($with_doi); ?></td>
                    <td><?php echo $with_doi > 0 ? '✅' : '⚠️'; ?></td>
                </tr>
                <tr>
                    <td><strong>With Abstract</strong></td>
                    <td><?php echo number_format($with_abstract); ?></td>
                    <td><?php echo $with_abstract > 0 ? '✅' : '⚠️'; ?></td>
                </tr>
                <tr style="background: #d4edda;">
                    <td><strong>With Citations</strong></td>
                    <td><?php echo number_format($with_citations); ?> papers</td>
                    <td><?php echo $with_citations > 0 ? '✅' : '❌ Missing'; ?></td>
                </tr>
                <tr style="background: #d4edda;">
                    <td><strong>Citation Stats</strong></td>
                    <td>Avg: <?php echo number_format($avg_citations, 1); ?> / Max: <?php echo number_format($max_citations); ?></td>
                    <td><?php echo $max_citations > 0 ? '✅' : '⚠️'; ?></td>
                </tr>
                <tr style="background: #fff3cd;">
                    <td><strong>With Protocols</strong></td>
                    <td><?php echo number_format($with_protocols); ?></td>
                    <td><?php echo $with_protocols > 0 ? '✅' : '❌ Missing'; ?></td>
                </tr>
                <tr style="background: #fff3cd;">
                    <td><strong>With GitHub URL</strong></td>
                    <td><?php echo number_format($with_github); ?></td>
                    <td><?php echo $with_github > 0 ? '✅' : '❌ Missing'; ?></td>
                </tr>
                <tr style="background: #fff3cd;">
                    <td><strong>With Repositories</strong></td>
                    <td><?php echo number_format($with_repos); ?></td>
                    <td><?php echo $with_repos > 0 ? '✅' : '❌ Missing'; ?></td>
                </tr>
                <tr>
                    <td><strong>With RRIDs</strong></td>
                    <td><?php echo number_format($with_rrids); ?></td>
                    <td><?php echo $with_rrids > 0 ? '✅' : '⚠️'; ?></td>
                </tr>
                <tr>
                    <td><strong>With Facility</strong></td>
                    <td><?php echo number_format($with_facility); ?></td>
                    <td><?php echo $with_facility > 0 ? '✅' : '⚠️'; ?></td>
                </tr>
            </tbody>
        </table>
        
        <hr>
        
        <h2>🔑 Meta Keys Found in Database</h2>
        <p>These are the meta keys that exist for papers:</p>
        <pre style="background: #f1f1f1; padding: 15px; max-width: 600px; overflow-x: auto;"><?php 
        foreach ($all_meta_keys as $key) {
            $count = $wpdb->get_var($wpdb->prepare(
                "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = %s AND meta_value != ''",
                $key
            ));
            echo esc_html($key) . " → " . number_format($count) . " papers\n";
        }
        ?></pre>
        
        <hr>
        
        <h2>📋 Sample Papers with Protocols</h2>
        <?php if ($sample_with_protocols) : ?>
            <table class="widefat striped" style="max-width: 100%;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Protocols</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($sample_with_protocols as $paper) : 
                        $protocols = json_decode($paper->meta_value, true);
                    ?>
                    <tr>
                        <td><?php echo $paper->ID; ?></td>
                        <td><?php echo esc_html(wp_trim_words($paper->post_title, 8)); ?></td>
                        <td>
                            <?php if (is_array($protocols)) : ?>
                                <?php foreach ($protocols as $proto) : ?>
                                    <div style="margin-bottom: 5px; padding: 5px; background: #f9f9f9; border-radius: 3px;">
                                        <strong><?php echo esc_html($proto['name'] ?? 'Unknown'); ?></strong><br>
                                        <?php if (!empty($proto['url'])) : ?>
                                            <a href="<?php echo esc_url($proto['url']); ?>" target="_blank" style="word-break: break-all; font-size: 11px;">
                                                <?php echo esc_html($proto['url']); ?>
                                            </a>
                                            <?php 
                                            // Check if URL is valid
                                            $url_check = filter_var($proto['url'], FILTER_VALIDATE_URL);
                                            echo $url_check ? ' ✅' : ' ❌ Invalid URL';
                                            ?>
                                        <?php else : ?>
                                            <span style="color: red;">❌ No URL!</span>
                                        <?php endif; ?>
                                    </div>
                                <?php endforeach; ?>
                            <?php else : ?>
                                <span style="color: orange;">⚠️ Invalid JSON: <?php echo esc_html(substr($paper->meta_value, 0, 100)); ?></span>
                            <?php endif; ?>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else : ?>
            <div class="notice notice-warning" style="max-width: 600px;">
                <p><strong>No papers with protocols found!</strong></p>
                <p>Your JSON export may not include the <code>protocols</code> field, or it may be using a different field name.</p>
            </div>
        <?php endif; ?>
        
        <hr>
        
        <h2>💻 Sample Papers with GitHub</h2>
        <?php if ($sample_with_github) : ?>
            <table class="widefat striped" style="max-width: 800px;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>GitHub URL</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($sample_with_github as $paper) : ?>
                    <tr>
                        <td><?php echo $paper->ID; ?></td>
                        <td><?php echo esc_html(wp_trim_words($paper->post_title, 10)); ?></td>
                        <td><a href="<?php echo esc_url($paper->meta_value); ?>" target="_blank"><?php echo esc_html($paper->meta_value); ?></a>
                        <?php echo filter_var($paper->meta_value, FILTER_VALIDATE_URL) ? ' ✅' : ' ❌'; ?>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else : ?>
            <div class="notice notice-warning" style="max-width: 600px;">
                <p><strong>No papers with GitHub URLs found!</strong></p>
                <p>Your JSON export may not include the <code>github_url</code> field.</p>
            </div>
        <?php endif; ?>
        
        <hr>
        
        <h2>💾 Sample Papers with Data Repositories</h2>
        <?php 
        $sample_with_repos = $wpdb->get_results("
            SELECT p.ID, p.post_title, pm.meta_value 
            FROM {$wpdb->posts} p 
            JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id 
            WHERE pm.meta_key = '_mh_repositories' 
            AND pm.meta_value != '' 
            AND pm.meta_value != '[]'
            AND p.post_type = 'mh_paper'
            LIMIT 5
        ");
        if ($sample_with_repos) : ?>
            <table class="widefat striped" style="max-width: 100%;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Repositories</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($sample_with_repos as $paper) : 
                        $repos = json_decode($paper->meta_value, true);
                    ?>
                    <tr>
                        <td><?php echo $paper->ID; ?></td>
                        <td><?php echo esc_html(wp_trim_words($paper->post_title, 8)); ?></td>
                        <td>
                            <?php if (is_array($repos)) : ?>
                                <?php foreach ($repos as $repo) : ?>
                                    <div style="margin-bottom: 5px; padding: 5px; background: #f9f9f9; border-radius: 3px;">
                                        <strong><?php echo esc_html($repo['name'] ?? 'Unknown'); ?></strong>
                                        <?php if (!empty($repo['accession_id'])) : ?>
                                            (<?php echo esc_html($repo['accession_id']); ?>)
                                        <?php endif; ?><br>
                                        <?php if (!empty($repo['url'])) : ?>
                                            <a href="<?php echo esc_url($repo['url']); ?>" target="_blank" style="word-break: break-all; font-size: 11px;">
                                                <?php echo esc_html($repo['url']); ?>
                                            </a>
                                            <?php echo filter_var($repo['url'], FILTER_VALIDATE_URL) ? ' ✅' : ' ❌ Invalid'; ?>
                                        <?php else : ?>
                                            <span style="color: red;">❌ No URL!</span>
                                        <?php endif; ?>
                                    </div>
                                <?php endforeach; ?>
                            <?php else : ?>
                                <span style="color: orange;">⚠️ Invalid JSON</span>
                            <?php endif; ?>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else : ?>
            <div class="notice notice-warning" style="max-width: 600px;">
                <p><strong>No papers with data repositories found!</strong></p>
            </div>
        <?php endif; ?>
        
        <hr>
        
        <h2>🏛️ Sample Papers with Facilities</h2>
        <?php 
        $sample_with_facilities = $wpdb->get_results("
            SELECT p.ID, p.post_title, pm.meta_value 
            FROM {$wpdb->posts} p 
            JOIN {$wpdb->postmeta} pm ON p.ID = pm.post_id 
            WHERE pm.meta_key = '_mh_facility' 
            AND pm.meta_value != ''
            AND p.post_type = 'mh_paper'
            LIMIT 5
        ");
        if ($sample_with_facilities) : ?>
            <table class="widefat striped" style="max-width: 800px;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Facility</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($sample_with_facilities as $paper) : ?>
                    <tr>
                        <td><?php echo $paper->ID; ?></td>
                        <td><?php echo esc_html(wp_trim_words($paper->post_title, 10)); ?></td>
                        <td><?php echo esc_html($paper->meta_value); ?></td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        <?php else : ?>
            <div class="notice notice-warning" style="max-width: 600px;">
                <p><strong>No papers with Facility data found!</strong></p>
                <p>Your JSON export may not include the <code>facility</code> field.</p>
            </div>
        <?php endif; ?>
        
        <hr>
        
        <h2>📄 Sample Paper - All Meta Data</h2>
        <?php if ($sample_paper) : 
            $paper = $sample_paper[0];
            $all_meta = get_post_meta($paper->ID);
        ?>
            <h4><?php echo esc_html($paper->post_title); ?> (ID: <?php echo $paper->ID; ?>)</h4>
            <table class="widefat striped" style="max-width: 800px;">
                <thead>
                    <tr>
                        <th>Meta Key</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($all_meta as $key => $values) : 
                        if (strpos($key, '_mh_') === 0) :
                    ?>
                    <tr>
                        <td><code><?php echo esc_html($key); ?></code></td>
                        <td><code style="font-size: 11px; word-break: break-all;"><?php 
                            $val = $values[0];
                            if (strlen($val) > 300) {
                                echo esc_html(substr($val, 0, 300)) . '...';
                            } else {
                                echo esc_html($val);
                            }
                        ?></code></td>
                    </tr>
                    <?php endif; endforeach; ?>
                </tbody>
            </table>
        <?php else : ?>
            <p>No papers found.</p>
        <?php endif; ?>
        
        <hr>
        
        <h2>📝 Expected JSON Format for Import</h2>
        <p>Your scraper JSON should include these fields for full enrichment:</p>
        <pre style="background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; max-width: 800px; overflow-x: auto;">
{
  "title": "Paper Title",
  "doi": "10.1234/example",
  "pmid": "12345678",
  "authors": "Smith J, Doe J",
  "journal": "Nature Methods",
  "year": 2023,
  "citations": 150,
  "abstract": "Paper abstract...",
  "pdf_url": "https://example.com/paper.pdf",
  
  <span style="color: #4ec9b0;">// GitHub - try these field names:</span>
  "github_url": "https://github.com/user/repo",
  <span style="color: #6a9955;">// OR "github": "https://github.com/..."</span>
  <span style="color: #6a9955;">// OR "code_repository": "https://github.com/..."</span>
  
  <span style="color: #4ec9b0;">// Protocols - must be an array:</span>
  "protocols": [
    {"name": "Protocol Name", "url": "https://protocols.io/view/..."}
  ],
  
  <span style="color: #4ec9b0;">// Repositories - must be an array:</span>
  "repositories": [
    {"name": "Zenodo", "url": "https://zenodo.org/...", "accession_id": "123"}
  ],
  
  <span style="color: #4ec9b0;">// Facility:</span>
  "facility": "Harvard Imaging Core"
}
        </pre>
        
        <hr>
        
        <h2>🔧 Quick Fix: Re-import with Update</h2>
        <p>If your data is missing fields, you can:</p>
        <ol>
            <li>Update your Python scraper to include the missing fields</li>
            <li>Re-export to JSON</li>
            <li>Go to <a href="<?php echo admin_url('admin.php?page=microhub-import'); ?>">Import Papers</a></li>
            <li>Check "Update existing papers with new enrichment data"</li>
            <li>Upload the new JSON file</li>
        </ol>
        
        <h2>🧪 Test API Endpoints</h2>
        <p>Click these to verify the REST API is working:</p>
        <ul>
            <li><a href="<?php echo rest_url('microhub/v1/papers?per_page=1'); ?>" target="_blank">📄 Papers API</a></li>
            <li><a href="<?php echo rest_url('microhub/v1/enrichment-stats'); ?>" target="_blank">📊 Enrichment Stats API</a></li>
            <li><a href="<?php echo rest_url('microhub/v1/protocols'); ?>" target="_blank">📋 Protocols API</a></li>
            <li><a href="<?php echo rest_url('microhub/v1/github-repos'); ?>" target="_blank">💻 GitHub Repos API</a></li>
            <li><a href="<?php echo rest_url('microhub/v1/data-repos'); ?>" target="_blank">💾 Data Repositories API</a></li>
            <li><a href="<?php echo rest_url('microhub/v1/facilities'); ?>" target="_blank">🏛️ Facilities API</a></li>
        </ul>
        <p style="color: #666;">If any endpoint returns empty [], your data may not be imported correctly.</p>
    </div>
    <?php
}
