<?php
/**
 * MicroHub Admin Import v3.0
 */

if (!defined('ABSPATH')) {
    exit;
}

// Add import submenu
add_action('admin_menu', 'microhub_add_import_menu');

function microhub_add_import_menu() {
    add_submenu_page(
        'microhub-settings',
        __('Import Papers', 'microhub'),
        __('Import Papers', 'microhub'),
        'manage_options',
        'microhub-import',
        'microhub_import_page'
    );
}

function microhub_import_page() {
    // Handle import
    if (isset($_POST['microhub_import']) && check_admin_referer('microhub_import_nonce')) {
        microhub_process_import();
    }
    ?>
    <div class="wrap">
        <h1><?php _e('Import Papers', 'microhub'); ?></h1>
        
        <div class="notice notice-info">
            <p><strong>Supported formats:</strong> Excel (.xlsx) or JSON (.json)</p>
        </div>
        
        <form method="post" enctype="multipart/form-data">
            <?php wp_nonce_field('microhub_import_nonce'); ?>
            
            <table class="form-table">
                <tr>
                    <th scope="row"><label for="import_file">Import File</label></th>
                    <td>
                        <input type="file" name="import_file" id="import_file" accept=".xlsx,.json" required />
                    </td>
                </tr>
                <tr>
                    <th scope="row">Options</th>
                    <td>
                        <label>
                            <input type="checkbox" name="skip_existing" value="1" checked />
                            Skip existing papers (by DOI/PMID)
                        </label>
                        <br />
                        <label>
                            <input type="checkbox" name="update_existing" value="1" />
                            Update existing papers
                        </label>
                    </td>
                </tr>
            </table>
            
            <p class="submit">
                <input type="submit" name="microhub_import" class="button button-primary" value="Import Papers" />
            </p>
        </form>
        
        <hr />
        
        <h2>Expected Columns</h2>
        <p>The importer supports these Excel/JSON columns:</p>
        <ul style="columns: 3;">
            <li>Title (required)</li>
            <li>Abstract</li>
            <li>Methods</li>
            <li>DOI</li>
            <li>PMID</li>
            <li>PMC ID</li>
            <li>Authors</li>
            <li>Journal</li>
            <li>Year</li>
            <li>Citations</li>
            <li>GitHub URL</li>
            <li>Microscopy Techniques (pipe-separated)</li>
            <li>Microscope Brands (pipe-separated)</li>
            <li>Analysis Software (pipe-separated)</li>
            <li>Sample Preparation (pipe-separated)</li>
            <li>Fluorophores (pipe-separated)</li>
            <li>Organisms (pipe-separated)</li>
        </ul>
    </div>
    <?php
}

function microhub_process_import() {
    if (!isset($_FILES['import_file']) || $_FILES['import_file']['error'] !== UPLOAD_ERR_OK) {
        echo '<div class="notice notice-error"><p>Error uploading file.</p></div>';
        return;
    }
    
    @ini_set('memory_limit', '512M');
    set_time_limit(0);
    
    $file_path = $_FILES['import_file']['tmp_name'];
    $file_name = $_FILES['import_file']['name'];
    $file_ext = strtolower(pathinfo($file_name, PATHINFO_EXTENSION));
    
    $skip_existing = isset($_POST['skip_existing']);
    $update_existing = isset($_POST['update_existing']);
    
    $stats = array('imported' => 0, 'updated' => 0, 'skipped' => 0, 'errors' => 0);
    
    if ($file_ext === 'json') {
        $stats = microhub_import_json($file_path, $skip_existing, $update_existing);
    } elseif ($file_ext === 'xlsx') {
        $stats = microhub_import_excel($file_path, $skip_existing, $update_existing);
    } else {
        echo '<div class="notice notice-error"><p>Unsupported file format.</p></div>';
        return;
    }
    
    echo '<div class="notice notice-success">';
    echo '<p><strong>Import Complete!</strong></p>';
    echo '<p>Imported: ' . $stats['imported'] . ' | Updated: ' . $stats['updated'] . ' | Skipped: ' . $stats['skipped'] . ' | Errors: ' . $stats['errors'] . '</p>';
    echo '</div>';
}

function microhub_import_json($file_path, $skip_existing, $update_existing) {
    $stats = array('imported' => 0, 'updated' => 0, 'skipped' => 0, 'errors' => 0);
    
    $json = file_get_contents($file_path);
    $papers = json_decode($json, true);
    
    if (!$papers || !is_array($papers)) {
        $stats['errors'] = 1;
        return $stats;
    }
    
    foreach ($papers as $paper) {
        $result = microhub_import_paper($paper, $skip_existing, $update_existing);
        $stats[$result]++;
    }
    
    return $stats;
}

function microhub_import_excel($file_path, $skip_existing, $update_existing) {
    $stats = array('imported' => 0, 'updated' => 0, 'skipped' => 0, 'errors' => 0);
    
    // Check for PhpSpreadsheet
    if (!class_exists('PhpOffice\PhpSpreadsheet\IOFactory')) {
        $autoload_paths = array(
            ABSPATH . 'vendor/autoload.php',
            WP_CONTENT_DIR . '/vendor/autoload.php',
            dirname(__FILE__) . '/../vendor/autoload.php',
        );
        
        foreach ($autoload_paths as $path) {
            if (file_exists($path)) {
                require_once $path;
                break;
            }
        }
    }
    
    if (!class_exists('PhpOffice\PhpSpreadsheet\IOFactory')) {
        echo '<div class="notice notice-error"><p>PhpSpreadsheet not installed. Use: <code>composer require phpoffice/phpspreadsheet</code> or use JSON format.</p></div>';
        return $stats;
    }
    
    try {
        $reader = \PhpOffice\PhpSpreadsheet\IOFactory::createReaderForFile($file_path);
        $reader->setReadDataOnly(true);
        $spreadsheet = $reader->load($file_path);
        $data = $spreadsheet->getActiveSheet()->toArray();
        
        if (empty($data)) {
            return $stats;
        }
        
        $headers = array_map('strtolower', array_map('trim', $data[0]));
        
        for ($i = 1; $i < count($data); $i++) {
            $row = $data[$i];
            $paper = array();
            
            foreach ($headers as $col => $header) {
                $paper[$header] = isset($row[$col]) ? $row[$col] : '';
            }
            
            $result = microhub_import_paper($paper, $skip_existing, $update_existing);
            $stats[$result]++;
        }
        
    } catch (Exception $e) {
        echo '<div class="notice notice-error"><p>Excel Error: ' . esc_html($e->getMessage()) . '</p></div>';
        $stats['errors']++;
    }
    
    return $stats;
}

function microhub_import_paper($data, $skip_existing, $update_existing) {
    global $wpdb;
    
    // Get title
    $title = '';
    foreach (array('title', 'post_title', 'paper_title') as $key) {
        if (!empty($data[$key])) {
            $title = trim($data[$key]);
            break;
        }
    }
    
    if (empty($title)) {
        return 'errors';
    }
    
    // Get DOI and PMID
    $doi = isset($data['doi']) ? trim($data['doi']) : '';
    $pmid = isset($data['pmid']) ? trim($data['pmid']) : (isset($data['pubmed_id']) ? trim($data['pubmed_id']) : '');
    
    // Check for existing
    $existing_id = null;
    if ($doi) {
        $existing_id = $wpdb->get_var($wpdb->prepare(
            "SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = '_mh_doi' AND meta_value = %s LIMIT 1",
            $doi
        ));
    }
    if (!$existing_id && $pmid) {
        $existing_id = $wpdb->get_var($wpdb->prepare(
            "SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = '_mh_pubmed_id' AND meta_value = %s LIMIT 1",
            $pmid
        ));
    }
    
    if ($existing_id) {
        if ($skip_existing && !$update_existing) {
            return 'skipped';
        }
        if (!$update_existing) {
            return 'skipped';
        }
    }
    
    // Prepare post data
    $abstract = '';
    foreach (array('abstract', 'post_content') as $key) {
        if (!empty($data[$key])) {
            $abstract = $data[$key];
            break;
        }
    }
    
    $post_data = array(
        'post_title' => sanitize_text_field($title),
        'post_content' => wp_kses_post($abstract),
        'post_type' => 'mh_paper',
        'post_status' => 'publish',
    );
    
    if ($existing_id && $update_existing) {
        $post_data['ID'] = $existing_id;
        $post_id = wp_update_post($post_data);
        $is_update = true;
    } else {
        $post_id = wp_insert_post($post_data);
        $is_update = false;
    }
    
    if (!$post_id || is_wp_error($post_id)) {
        return 'errors';
    }
    
    // Save meta
    if ($doi) update_post_meta($post_id, '_mh_doi', $doi);
    if ($pmid) update_post_meta($post_id, '_mh_pubmed_id', $pmid);
    
    $meta_mappings = array(
        'pmc_id' => '_mh_pmc_id',
        'pmc id' => '_mh_pmc_id',
        'authors' => '_mh_authors',
        'journal' => '_mh_journal',
        'year' => '_mh_publication_year',
        'publication_year' => '_mh_publication_year',
        'citations' => '_mh_citation_count',
        'citation_count' => '_mh_citation_count',
        'priority' => '_mh_priority_score',
        'priority_score' => '_mh_priority_score',
        'abstract' => '_mh_abstract',
        'methods' => '_mh_methods',
        'github_url' => '_mh_github_url',
        'github url' => '_mh_github_url',
    );
    
    foreach ($meta_mappings as $field => $meta_key) {
        if (!empty($data[$field])) {
            if (in_array($meta_key, array('_mh_publication_year', '_mh_citation_count', '_mh_priority_score'))) {
                update_post_meta($post_id, $meta_key, intval($data[$field]));
            } else {
                update_post_meta($post_id, $meta_key, sanitize_text_field($data[$field]));
            }
        }
    }
    
    // Taxonomy mappings (pipe-separated)
    $taxonomy_mappings = array(
        'microscopy_techniques' => 'mh_technique',
        'microscopy techniques' => 'mh_technique',
        'techniques' => 'mh_technique',
        'microscope_brands' => 'mh_microscope_brand',
        'microscope brands' => 'mh_microscope_brand',
        'brands' => 'mh_microscope_brand',
        'microscope_models' => 'mh_microscope_model',
        'microscope models' => 'mh_microscope_model',
        'analysis_software' => 'mh_analysis_software',
        'image_analysis_software' => 'mh_analysis_software',
        'image analysis software' => 'mh_analysis_software',
        'sample_preparation' => 'mh_sample_prep',
        'sample preparation' => 'mh_sample_prep',
        'fluorophores' => 'mh_fluorophore',
        'organisms' => 'mh_organism',
    );
    
    foreach ($taxonomy_mappings as $field => $taxonomy) {
        if (!empty($data[$field])) {
            $terms = array_filter(array_map('trim', explode('|', $data[$field])));
            if (!empty($terms)) {
                wp_set_object_terms($post_id, $terms, $taxonomy);
            }
        }
    }
    
    // Set journal taxonomy
    if (!empty($data['journal'])) {
        wp_set_object_terms($post_id, array(trim($data['journal'])), 'mh_journal');
    }
    
    // Set flags
    $has_full_text = !empty($data['has_full_text']) || !empty($data['has full text']);
    $has_figures = !empty($data['has_figures']) || !empty($data['has figures']) || !empty($data['figure_count']);
    $has_protocols = !empty($data['has_protocols']) || !empty($data['has protocols']) || !empty($data['protocols']);
    $has_github = !empty($data['github_url']) || !empty($data['github url']);
    
    update_post_meta($post_id, '_mh_has_full_text', $has_full_text ? 1 : 0);
    update_post_meta($post_id, '_mh_has_figures', $has_figures ? 1 : 0);
    update_post_meta($post_id, '_mh_has_protocols', $has_protocols ? 1 : 0);
    update_post_meta($post_id, '_mh_has_github', $has_github ? 1 : 0);
    
    return $is_update ? 'updated' : 'imported';
}
