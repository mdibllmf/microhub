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
    
    // Handle test import of single paper
    if (isset($_POST['test_import_paper']) && check_admin_referer('microhub_test_import_nonce')) {
        microhub_test_single_import();
    }
    
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
        
        <h2>🔬 v4.1 Meta Fields (for Theme Advanced Filters)</h2>
        <?php
        // Check v4.1 meta fields
        $v41_meta_fields = array(
            '_mh_fluorophores' => 'Fluorophores',
            '_mh_sample_preparation' => 'Sample Preparation',
            '_mh_cell_lines' => 'Cell Lines',
            '_mh_microscope_brands' => 'Microscope Brands',
            '_mh_microscope_models' => 'Microscope Models',
            '_mh_image_analysis_software' => 'Analysis Software',
            '_mh_image_acquisition_software' => 'Acquisition Software',
            '_mh_figures' => 'Figures',
            '_mh_methods' => 'Methods',
            '_mh_full_text' => 'Full Text',
            '_mh_imaging_modalities' => 'Imaging Modalities',
            '_mh_staining_methods' => 'Staining Methods',
        );
        
        $v41_stats = array();
        foreach ($v41_meta_fields as $key => $label) {
            $count = $wpdb->get_var($wpdb->prepare(
                "SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} 
                 WHERE meta_key = %s AND meta_value != '' AND meta_value != '[]' AND meta_value IS NOT NULL",
                $key
            ));
            $v41_stats[$key] = array('label' => $label, 'count' => intval($count));
        }
        
        // Check corresponding taxonomies
        $taxonomy_counts = array(
            'mh_fluorophore' => 'Fluorophores (taxonomy)',
            'mh_sample_prep' => 'Sample Prep (taxonomy)',
            'mh_cell_line' => 'Cell Lines (taxonomy)',
        );
        ?>
        <table class="widefat striped" style="max-width: 800px;">
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Meta Key</th>
                    <th>Papers with Data</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($v41_stats as $key => $data) : ?>
                <tr style="<?php echo $data['count'] == 0 ? 'background: #f8d7da;' : ($data['count'] > 100 ? 'background: #d4edda;' : ''); ?>">
                    <td><strong><?php echo esc_html($data['label']); ?></strong></td>
                    <td><code><?php echo esc_html($key); ?></code></td>
                    <td><?php echo number_format($data['count']); ?></td>
                    <td>
                        <?php if ($data['count'] == 0) : ?>
                            ❌ Missing - Theme filters won't work
                        <?php elseif ($data['count'] < 50) : ?>
                            ⚠️ Low count
                        <?php else : ?>
                            ✅ OK
                        <?php endif; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        
        <h3>📊 Taxonomy vs Meta Field Comparison</h3>
        <p>If taxonomy has data but meta field is empty, use the migration tool below.</p>
        <table class="widefat striped" style="max-width: 600px;">
            <thead>
                <tr>
                    <th>Taxonomy</th>
                    <th>Papers Tagged</th>
                    <th>Corresponding Meta</th>
                    <th>Meta Count</th>
                </tr>
            </thead>
            <tbody>
                <?php
                $taxonomy_meta_map = array(
                    'mh_fluorophore' => '_mh_fluorophores',
                    'mh_sample_prep' => '_mh_sample_preparation',
                    'mh_cell_line' => '_mh_cell_lines',
                    'mh_microscope' => '_mh_microscope_brands',
                    'mh_analysis_software' => '_mh_image_analysis_software',
                    'mh_acquisition_software' => '_mh_image_acquisition_software',
                );
                foreach ($taxonomy_meta_map as $tax => $meta) :
                    $tax_count = 0;
                    if (taxonomy_exists($tax)) {
                        $tax_count = $wpdb->get_var($wpdb->prepare(
                            "SELECT COUNT(DISTINCT tr.object_id) FROM {$wpdb->term_relationships} tr
                             JOIN {$wpdb->term_taxonomy} tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
                             WHERE tt.taxonomy = %s",
                            $tax
                        ));
                    }
                    $meta_count = $v41_stats[$meta]['count'] ?? 0;
                ?>
                <tr style="<?php echo ($tax_count > 0 && $meta_count == 0) ? 'background: #fff3cd;' : ''; ?>">
                    <td><code><?php echo esc_html($tax); ?></code></td>
                    <td><?php echo number_format($tax_count); ?></td>
                    <td><code><?php echo esc_html($meta); ?></code></td>
                    <td><?php echo number_format($meta_count); ?>
                        <?php if ($tax_count > 0 && $meta_count == 0) : ?>
                            <strong style="color: #856404;">← Needs migration!</strong>
                        <?php endif; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        
        <hr>
        
        <h2>🔄 Migration Tool: Taxonomy → Meta Fields</h2>
        <p>This will copy data from taxonomies to meta fields so the theme's advanced filters work.</p>

        <?php
        // Handle migration
        if (isset($_POST['migrate_taxonomy_to_meta']) && check_admin_referer('microhub_migrate_nonce')) {
            $force_update = !empty($_POST['force_update']);
            $migrated = microhub_migrate_taxonomy_to_meta($force_update);

            // Auto-clear filter cache after migration
            delete_transient('mh_filter_options');
            delete_transient('mh_stats');
            global $wpdb;
            $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_mh_%' OR option_name LIKE '_transient_timeout_mh_%'");

            echo '<div class="notice notice-success"><p>✅ Migration complete! ' . esc_html($migrated) . ' papers updated. Filter cache automatically cleared.</p></div>';
        }

        // Handle cache clear
        if (isset($_POST['clear_theme_cache']) && check_admin_referer('microhub_cache_nonce')) {
            delete_transient('mh_filter_options');
            delete_transient('mh_stats');
            // Clear any other theme caches
            global $wpdb;
            $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_mh_%' OR option_name LIKE '_transient_timeout_mh_%'");
            echo '<div class="notice notice-success"><p>✅ Theme cache cleared!</p></div>';
        }
        ?>

        <form method="post" style="display: inline-block; margin-right: 20px;">
            <?php wp_nonce_field('microhub_migrate_nonce'); ?>
            <label style="margin-right: 10px;">
                <input type="checkbox" name="force_update" value="1">
                Force update (overwrite existing meta)
            </label>
            <button type="submit" name="migrate_taxonomy_to_meta" class="button button-primary">
                🔄 Migrate Taxonomy Data to Meta Fields
            </button>
        </form>

        <form method="post" style="display: inline-block;">
            <?php wp_nonce_field('microhub_cache_nonce'); ?>
            <button type="submit" name="clear_theme_cache" class="button button-secondary">
                🗑️ Clear Theme Filter Cache
            </button>
        </form>

        <p style="margin-top: 15px; color: #666;">
            <strong>Note:</strong> Cache is now automatically cleared after migration. Use "Clear Theme Filter Cache" to manually refresh filter options.
        </p>
        
        <hr>
        
        <h2>🧪 Test Single Paper Import</h2>
        <p>Paste a single paper JSON object to test the import and see exactly what gets saved:</p>
        
        <form method="post">
            <?php wp_nonce_field('microhub_test_import_nonce'); ?>
            <textarea name="test_paper_json" rows="10" style="width: 100%; max-width: 800px; font-family: monospace; font-size: 12px;" placeholder='Paste a single paper JSON object here, e.g.:
{
  "doi": "10.1234/test",
  "title": "Test Paper",
  "fluorophores": ["GFP", "mCherry"],
  "sample_preparation": ["fixation"],
  "cell_lines": ["HeLa"]
}'></textarea>
            <br><br>
            <button type="submit" name="test_import_paper" class="button button-primary">
                🧪 Test Import This Paper
            </button>
        </form>
        
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
            <li><a href="<?php echo rest_url('microhub/v1/github-tools'); ?>" target="_blank">💻 GitHub Tools API (sorted by citations)</a></li>
            <li><a href="<?php echo rest_url('microhub/v1/data-repos'); ?>" target="_blank">💾 Data Repositories API</a></li>
            <li><a href="<?php echo rest_url('microhub/v1/facilities'); ?>" target="_blank">🏛️ Facilities API</a></li>
        </ul>
        <p style="color: #666;">If any endpoint returns empty [], your data may not be imported correctly.</p>
    </div>
    <?php
}

/**
 * Migrate taxonomy terms to meta fields for theme compatibility
 * @param bool $force_update If true, overwrites existing meta values
 */
function microhub_migrate_taxonomy_to_meta($force_update = false) {
    global $wpdb;

    $taxonomy_meta_map = array(
        'mh_fluorophore' => '_mh_fluorophores',
        'mh_sample_prep' => '_mh_sample_preparation',
        'mh_cell_line' => '_mh_cell_lines',
        'mh_microscope' => '_mh_microscope_brands',
        'mh_microscope_model' => '_mh_microscope_models',
        'mh_analysis_software' => '_mh_image_analysis_software',
        'mh_acquisition_software' => '_mh_image_acquisition_software',
    );

    $migrated = 0;

    foreach ($taxonomy_meta_map as $taxonomy => $meta_key) {
        if (!taxonomy_exists($taxonomy)) {
            continue;
        }

        // Get all papers with this taxonomy
        $papers = get_posts(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => -1,
            'fields' => 'ids',
            'tax_query' => array(
                array(
                    'taxonomy' => $taxonomy,
                    'operator' => 'EXISTS',
                ),
            ),
        ));

        foreach ($papers as $post_id) {
            // Get taxonomy terms
            $terms = wp_get_object_terms($post_id, $taxonomy, array('fields' => 'names'));

            if (!empty($terms) && !is_wp_error($terms)) {
                // Get current meta value
                $existing = get_post_meta($post_id, $meta_key, true);
                $existing_array = json_decode($existing, true);

                // Update if force_update is true OR if meta is empty/invalid
                if ($force_update || empty($existing_array) || !is_array($existing_array)) {
                    // Merge existing values with taxonomy terms if not forcing
                    if (!$force_update && is_array($existing_array) && !empty($existing_array)) {
                        $terms = array_unique(array_merge($existing_array, $terms));
                    }
                    update_post_meta($post_id, $meta_key, wp_json_encode(array_values($terms)));
                    $migrated++;
                }
            }
        }
    }

    return $migrated;
}

/**
 * Test import of a single paper to debug issues
 */
function microhub_test_single_import() {
    if (empty($_POST['test_paper_json'])) {
        echo '<div class="notice notice-error"><p>Please paste a JSON object.</p></div>';
        return;
    }
    
    $json = stripslashes($_POST['test_paper_json']);
    $data = json_decode($json, true);
    
    if (!$data) {
        echo '<div class="notice notice-error"><p>Invalid JSON: ' . json_last_error_msg() . '</p></div>';
        return;
    }
    
    echo '<div class="notice notice-info" style="padding: 15px;">';
    echo '<h3>🧪 Test Import Results</h3>';
    
    // Show what was parsed
    echo '<h4>1. Parsed JSON Data:</h4>';
    echo '<pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">';
    
    $fields_to_check = array(
        'doi', 'title', 'pmid', 'fluorophores', 'sample_preparation', 'cell_lines',
        'microscope_brands', 'microscope_models', 'image_analysis_software',
        'image_acquisition_software', 'organisms', 'techniques', 'tags'
    );
    
    foreach ($fields_to_check as $field) {
        $value = isset($data[$field]) ? $data[$field] : 'NOT SET';
        if (is_array($value)) {
            $value = empty($value) ? '[] (empty array)' : json_encode($value);
        }
        echo esc_html($field) . ': ' . esc_html($value) . "\n";
    }
    echo '</pre>';
    
    // Check if DOI exists
    if (empty($data['doi'])) {
        echo '<p style="color: red;">❌ No DOI provided - cannot import.</p>';
        echo '</div>';
        return;
    }
    
    // Check for existing paper
    $existing = get_posts(array(
        'post_type' => 'mh_paper',
        'meta_key' => '_mh_doi',
        'meta_value' => $data['doi'],
        'posts_per_page' => 1,
    ));
    
    if ($existing) {
        $post_id = $existing[0]->ID;
        echo '<h4>2. Existing Paper Found:</h4>';
        echo '<p>Post ID: ' . $post_id . ' - <a href="' . get_edit_post_link($post_id) . '" target="_blank">Edit</a></p>';
        
        // Show current meta values
        echo '<h4>3. Current Meta Values (before update):</h4>';
        echo '<pre style="background: #fff3cd; padding: 10px;">';
        $meta_keys = array(
            '_mh_fluorophores', '_mh_sample_preparation', '_mh_cell_lines',
            '_mh_microscope_brands', '_mh_image_analysis_software'
        );
        foreach ($meta_keys as $key) {
            $val = get_post_meta($post_id, $key, true);
            echo esc_html($key) . ': ' . esc_html($val ?: '(empty)') . "\n";
        }
        echo '</pre>';
        
        // Show current taxonomy terms
        echo '<h4>4. Current Taxonomy Terms:</h4>';
        echo '<pre style="background: #d4edda; padding: 10px;">';
        $taxonomies = array(
            'mh_fluorophore', 'mh_sample_prep', 'mh_cell_line', 'mh_microscope'
        );
        foreach ($taxonomies as $tax) {
            if (taxonomy_exists($tax)) {
                $terms = wp_get_object_terms($post_id, $tax, array('fields' => 'names'));
                echo esc_html($tax) . ': ' . (is_array($terms) ? implode(', ', $terms) : '(none)') . "\n";
            } else {
                echo esc_html($tax) . ': TAXONOMY NOT REGISTERED!\n';
            }
        }
        echo '</pre>';
    } else {
        echo '<h4>2. No Existing Paper Found</h4>';
        echo '<p>Will create new paper with DOI: ' . esc_html($data['doi']) . '</p>';
        $post_id = null;
    }
    
    // Now do the actual import
    echo '<h4>5. Performing Import...</h4>';
    
    $enrichment_stats = array(
        'protocols' => 0, 'repositories' => 0, 'rrids' => 0,
        'microscopes' => 0, 'github' => 0, 'facilities' => 0,
    );
    
    // Call the import function
    $result = microhub_import_paper($data, false, true, $enrichment_stats);
    
    echo '<p>Import result: <strong>' . esc_html($result) . '</strong></p>';
    
    // Get the post ID (might be new)
    if (!$post_id) {
        $new_post = get_posts(array(
            'post_type' => 'mh_paper',
            'meta_key' => '_mh_doi',
            'meta_value' => $data['doi'],
            'posts_per_page' => 1,
        ));
        if ($new_post) {
            $post_id = $new_post[0]->ID;
        }
    }
    
    if ($post_id) {
        // Show meta values after import
        echo '<h4>6. Meta Values AFTER Import:</h4>';
        echo '<pre style="background: #d1ecf1; padding: 10px;">';
        $meta_keys = array(
            '_mh_fluorophores', '_mh_sample_preparation', '_mh_cell_lines',
            '_mh_microscope_brands', '_mh_microscope_models',
            '_mh_image_analysis_software', '_mh_image_acquisition_software'
        );
        foreach ($meta_keys as $key) {
            $val = get_post_meta($post_id, $key, true);
            $status = !empty($val) && $val !== '[]' ? '✅' : '❌';
            echo $status . ' ' . esc_html($key) . ': ' . esc_html($val ?: '(empty)') . "\n";
        }
        echo '</pre>';
        
        // Show taxonomy terms after import
        echo '<h4>7. Taxonomy Terms AFTER Import:</h4>';
        echo '<pre style="background: #d4edda; padding: 10px;">';
        $taxonomies = array(
            'mh_fluorophore', 'mh_sample_prep', 'mh_cell_line', 
            'mh_microscope', 'mh_analysis_software'
        );
        foreach ($taxonomies as $tax) {
            if (taxonomy_exists($tax)) {
                $terms = wp_get_object_terms($post_id, $tax, array('fields' => 'names'));
                $status = !empty($terms) && !is_wp_error($terms) ? '✅' : '❌';
                echo $status . ' ' . esc_html($tax) . ': ' . (is_array($terms) ? implode(', ', $terms) : '(none)') . "\n";
            } else {
                echo '❌ ' . esc_html($tax) . ': TAXONOMY NOT REGISTERED!\n';
            }
        }
        echo '</pre>';
        
        echo '<p><a href="' . get_permalink($post_id) . '" target="_blank" class="button">View Paper</a> ';
        echo '<a href="' . get_edit_post_link($post_id) . '" target="_blank" class="button">Edit Paper</a></p>';
    }
    
    echo '</div>';
}
