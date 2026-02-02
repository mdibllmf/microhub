<?php
/**
 * Plugin Name: MicroHub Paper Importer
 * Plugin URI: https://mdibl.org/microhub
 * Description: Import microscopy papers from Excel files exported by MicroHub scraper
 * Version: 2.0
 * Author: MDIBL
 * License: GPL v2 or later
 *
 * INSTALLATION:
 * 1. Upload this folder to wp-content/plugins/
 * 2. Activate the plugin in WordPress
 * 3. Go to Tools > MicroHub Import
 * 4. Upload your Excel file
 *
 * REQUIREMENTS:
 * - PHP 7.4+
 * - PhpSpreadsheet library (installed via Composer)
 *
 * To install PhpSpreadsheet:
 * cd wp-content/plugins/microhub-importer
 * composer require phpoffice/phpspreadsheet
 */

if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('MICROHUB_VERSION', '2.0');
define('MICROHUB_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('MICROHUB_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Main plugin class
 */
class MicroHub_Importer {

    private static $instance = null;

    // Custom post type name
    const POST_TYPE = 'microhub_paper';

    // Taxonomies
    const TAX_TECHNIQUES = 'microscopy_techniques';
    const TAX_BRANDS = 'microscope_brands';
    const TAX_MODELS = 'microscope_models';
    const TAX_ANALYSIS_SOFTWARE = 'image_analysis_software';
    const TAX_ACQUISITION_SOFTWARE = 'image_acquisition_software';
    const TAX_ORGANISMS = 'organisms';
    const TAX_PROTOCOLS = 'protocol_sources';
    const TAX_REPOSITORIES = 'repository_sources';

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_action('init', array($this, 'register_post_type'));
        add_action('init', array($this, 'register_taxonomies'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_scripts'));
        add_action('wp_ajax_microhub_import', array($this, 'ajax_import'));
    }

    /**
     * Register the custom post type
     */
    public function register_post_type() {
        $labels = array(
            'name'               => 'MicroHub Papers',
            'singular_name'      => 'Paper',
            'menu_name'          => 'MicroHub Papers',
            'add_new'            => 'Add New Paper',
            'add_new_item'       => 'Add New Paper',
            'edit_item'          => 'Edit Paper',
            'new_item'           => 'New Paper',
            'view_item'          => 'View Paper',
            'search_items'       => 'Search Papers',
            'not_found'          => 'No papers found',
            'not_found_in_trash' => 'No papers found in trash',
        );

        $args = array(
            'labels'             => $labels,
            'public'             => true,
            'publicly_queryable' => true,
            'show_ui'            => true,
            'show_in_menu'       => true,
            'query_var'          => true,
            'rewrite'            => array('slug' => 'papers'),
            'capability_type'    => 'post',
            'has_archive'        => true,
            'hierarchical'       => false,
            'menu_position'      => 5,
            'menu_icon'          => 'dashicons-welcome-learn-more',
            'supports'           => array('title', 'editor', 'custom-fields', 'thumbnail'),
            'show_in_rest'       => true,
        );

        register_post_type(self::POST_TYPE, $args);
    }

    /**
     * Register all taxonomies
     */
    public function register_taxonomies() {
        // Microscopy Techniques
        $this->register_taxonomy(
            self::TAX_TECHNIQUES,
            'Microscopy Techniques',
            'Microscopy Technique',
            true
        );

        // Microscope Brands
        $this->register_taxonomy(
            self::TAX_BRANDS,
            'Microscope Brands',
            'Microscope Brand',
            true
        );

        // Microscope Models
        $this->register_taxonomy(
            self::TAX_MODELS,
            'Microscope Models',
            'Microscope Model',
            true
        );

        // Image Analysis Software
        $this->register_taxonomy(
            self::TAX_ANALYSIS_SOFTWARE,
            'Image Analysis Software',
            'Analysis Software',
            true
        );

        // Image Acquisition Software
        $this->register_taxonomy(
            self::TAX_ACQUISITION_SOFTWARE,
            'Image Acquisition Software',
            'Acquisition Software',
            true
        );

        // Organisms
        $this->register_taxonomy(
            self::TAX_ORGANISMS,
            'Organisms',
            'Organism',
            true
        );

        // Protocol Sources
        $this->register_taxonomy(
            self::TAX_PROTOCOLS,
            'Protocol Sources',
            'Protocol Source',
            false
        );

        // Repository Sources
        $this->register_taxonomy(
            self::TAX_REPOSITORIES,
            'Repository Sources',
            'Repository Source',
            false
        );
    }

    /**
     * Helper to register a taxonomy
     */
    private function register_taxonomy($taxonomy, $plural, $singular, $hierarchical = true) {
        $labels = array(
            'name'              => $plural,
            'singular_name'     => $singular,
            'search_items'      => "Search $plural",
            'all_items'         => "All $plural",
            'parent_item'       => $hierarchical ? "Parent $singular" : null,
            'parent_item_colon' => $hierarchical ? "Parent $singular:" : null,
            'edit_item'         => "Edit $singular",
            'update_item'       => "Update $singular",
            'add_new_item'      => "Add New $singular",
            'new_item_name'     => "New $singular Name",
            'menu_name'         => $plural,
        );

        $args = array(
            'hierarchical'      => $hierarchical,
            'labels'            => $labels,
            'show_ui'           => true,
            'show_admin_column' => true,
            'query_var'         => true,
            'rewrite'           => array('slug' => sanitize_title($plural)),
            'show_in_rest'      => true,
        );

        register_taxonomy($taxonomy, self::POST_TYPE, $args);
    }

    /**
     * Add admin menu page
     */
    public function add_admin_menu() {
        add_management_page(
            'MicroHub Import',
            'MicroHub Import',
            'manage_options',
            'microhub-import',
            array($this, 'render_admin_page')
        );
    }

    /**
     * Enqueue admin scripts
     */
    public function enqueue_admin_scripts($hook) {
        if ($hook !== 'tools_page_microhub-import') {
            return;
        }

        wp_enqueue_style('microhub-admin', MICROHUB_PLUGIN_URL . 'css/admin.css', array(), MICROHUB_VERSION);
        wp_enqueue_script('microhub-admin', MICROHUB_PLUGIN_URL . 'js/admin.js', array('jquery'), MICROHUB_VERSION, true);
        wp_localize_script('microhub-admin', 'microhub_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce'    => wp_create_nonce('microhub_import'),
        ));
    }

    /**
     * Render admin page
     */
    public function render_admin_page() {
        ?>
        <div class="wrap">
            <h1>MicroHub Paper Importer</h1>

            <div class="microhub-import-container">
                <div class="microhub-section">
                    <h2>Import from Excel File</h2>
                    <p>Upload an Excel file (.xlsx) exported from the MicroHub scraper.</p>

                    <form id="microhub-import-form" enctype="multipart/form-data">
                        <?php wp_nonce_field('microhub_import', 'microhub_nonce'); ?>

                        <table class="form-table">
                            <tr>
                                <th scope="row"><label for="excel_file">Excel File</label></th>
                                <td>
                                    <input type="file" name="excel_file" id="excel_file" accept=".xlsx,.xls" required>
                                    <p class="description">Select the microhub_papers.xlsx file</p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row"><label for="batch_size">Batch Size</label></th>
                                <td>
                                    <input type="number" name="batch_size" id="batch_size" value="100" min="10" max="500">
                                    <p class="description">Number of papers to import per batch (lower = slower but more stable)</p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row"><label for="skip_existing">Skip Existing</label></th>
                                <td>
                                    <input type="checkbox" name="skip_existing" id="skip_existing" checked>
                                    <label for="skip_existing">Skip papers that already exist (matched by PMID or DOI)</label>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row"><label for="post_status">Post Status</label></th>
                                <td>
                                    <select name="post_status" id="post_status">
                                        <option value="publish">Published</option>
                                        <option value="draft">Draft</option>
                                        <option value="pending">Pending Review</option>
                                    </select>
                                </td>
                            </tr>
                        </table>

                        <p class="submit">
                            <button type="submit" class="button button-primary" id="start-import">Start Import</button>
                        </p>
                    </form>
                </div>

                <div class="microhub-section" id="import-progress" style="display: none;">
                    <h2>Import Progress</h2>
                    <div class="progress-bar-container">
                        <div class="progress-bar" id="progress-bar"></div>
                    </div>
                    <div id="progress-text">Preparing...</div>
                    <div id="import-log"></div>
                </div>

                <div class="microhub-section">
                    <h2>Database Statistics</h2>
                    <?php $this->render_stats(); ?>
                </div>

                <div class="microhub-section">
                    <h2>Field Mapping Guide</h2>
                    <table class="widefat">
                        <thead>
                            <tr>
                                <th>Excel Column</th>
                                <th>WordPress Field</th>
                                <th>Type</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>post_title</td><td>Post Title</td><td>Core</td></tr>
                            <tr><td>post_content</td><td>Post Content (Abstract)</td><td>Core</td></tr>
                            <tr><td>methods</td><td>Methods (Custom Field)</td><td>Meta</td></tr>
                            <tr><td>pmid</td><td>PubMed ID</td><td>Meta</td></tr>
                            <tr><td>doi</td><td>DOI</td><td>Meta</td></tr>
                            <tr><td>microscopy_techniques</td><td>Microscopy Techniques</td><td>Taxonomy</td></tr>
                            <tr><td>microscope_brands</td><td>Microscope Brands</td><td>Taxonomy</td></tr>
                            <tr><td>microscope_models</td><td>Microscope Models</td><td>Taxonomy</td></tr>
                            <tr><td>image_analysis_software</td><td>Image Analysis Software</td><td>Taxonomy</td></tr>
                            <tr><td>image_acquisition_software</td><td>Image Acquisition Software</td><td>Taxonomy</td></tr>
                            <tr><td>organisms</td><td>Organisms</td><td>Taxonomy</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <?php
    }

    /**
     * Render database statistics
     */
    private function render_stats() {
        global $wpdb;

        $total_papers = wp_count_posts(self::POST_TYPE);
        $published = isset($total_papers->publish) ? $total_papers->publish : 0;
        $draft = isset($total_papers->draft) ? $total_papers->draft : 0;

        // Count papers with protocols
        $with_protocols = $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = 'has_protocols' AND meta_value = '1'"
        ));

        // Count papers with GitHub
        $with_github = $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = 'has_github' AND meta_value = '1'"
        ));

        ?>
        <table class="widefat">
            <tbody>
                <tr><td>Published Papers</td><td><strong><?php echo number_format($published); ?></strong></td></tr>
                <tr><td>Draft Papers</td><td><strong><?php echo number_format($draft); ?></strong></td></tr>
                <tr><td>With Protocols</td><td><strong><?php echo number_format($with_protocols ?: 0); ?></strong></td></tr>
                <tr><td>With GitHub</td><td><strong><?php echo number_format($with_github ?: 0); ?></strong></td></tr>
            </tbody>
        </table>
        <?php
    }

    /**
     * AJAX handler for import
     */
    public function ajax_import() {
        check_ajax_referer('microhub_import', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied');
        }

        // Handle file upload
        if (!empty($_FILES['excel_file'])) {
            $uploaded = wp_handle_upload($_FILES['excel_file'], array('test_form' => false));

            if (isset($uploaded['error'])) {
                wp_send_json_error('Upload error: ' . $uploaded['error']);
            }

            // Store file path in transient for batch processing
            set_transient('microhub_import_file', $uploaded['file'], HOUR_IN_SECONDS);
            set_transient('microhub_import_row', 2, HOUR_IN_SECONDS); // Start from row 2 (after header)

            wp_send_json_success(array(
                'status' => 'started',
                'message' => 'File uploaded, starting import...',
            ));
        }

        // Process batch
        $file = get_transient('microhub_import_file');
        $current_row = get_transient('microhub_import_row');
        $batch_size = isset($_POST['batch_size']) ? intval($_POST['batch_size']) : 100;
        $skip_existing = isset($_POST['skip_existing']) && $_POST['skip_existing'] === 'true';
        $post_status = isset($_POST['post_status']) ? sanitize_text_field($_POST['post_status']) : 'publish';

        if (!$file || !file_exists($file)) {
            wp_send_json_error('Import file not found. Please upload again.');
        }

        // Load PhpSpreadsheet
        require_once MICROHUB_PLUGIN_DIR . 'vendor/autoload.php';

        try {
            $spreadsheet = \PhpOffice\PhpSpreadsheet\IOFactory::load($file);
            $worksheet = $spreadsheet->getActiveSheet();
            $highestRow = $worksheet->getHighestRow();

            // Get headers from row 1
            $headers = array();
            $highestColumn = $worksheet->getHighestColumn();
            $highestColumnIndex = \PhpOffice\PhpSpreadsheet\Cell\Coordinate::columnIndexFromString($highestColumn);

            for ($col = 1; $col <= $highestColumnIndex; $col++) {
                $headers[$col] = $worksheet->getCellByColumnAndRow($col, 1)->getValue();
            }

            // Process batch
            $imported = 0;
            $skipped = 0;
            $errors = 0;
            $end_row = min($current_row + $batch_size - 1, $highestRow);

            for ($row = $current_row; $row <= $end_row; $row++) {
                $row_data = array();
                for ($col = 1; $col <= $highestColumnIndex; $col++) {
                    $header = $headers[$col];
                    $row_data[$header] = $worksheet->getCellByColumnAndRow($col, $row)->getValue();
                }

                $result = $this->import_paper($row_data, $skip_existing, $post_status);

                if ($result === 'imported') {
                    $imported++;
                } elseif ($result === 'skipped') {
                    $skipped++;
                } else {
                    $errors++;
                }
            }

            // Update progress
            $next_row = $end_row + 1;
            set_transient('microhub_import_row', $next_row, HOUR_IN_SECONDS);

            $progress = round(($next_row - 2) / ($highestRow - 1) * 100, 1);
            $complete = $next_row > $highestRow;

            if ($complete) {
                // Clean up
                delete_transient('microhub_import_file');
                delete_transient('microhub_import_row');
                @unlink($file);
            }

            wp_send_json_success(array(
                'status' => $complete ? 'complete' : 'processing',
                'progress' => $progress,
                'imported' => $imported,
                'skipped' => $skipped,
                'errors' => $errors,
                'current_row' => $next_row,
                'total_rows' => $highestRow,
                'message' => $complete ? 'Import complete!' : "Processed rows $current_row to $end_row",
            ));

        } catch (Exception $e) {
            wp_send_json_error('Error reading Excel file: ' . $e->getMessage());
        }
    }

    /**
     * Import a single paper
     */
    private function import_paper($data, $skip_existing, $post_status) {
        $pmid = isset($data['pmid']) ? sanitize_text_field($data['pmid']) : '';
        $doi = isset($data['doi']) ? sanitize_text_field($data['doi']) : '';

        // Check if exists
        if ($skip_existing && ($pmid || $doi)) {
            global $wpdb;
            $exists = false;

            if ($pmid) {
                $exists = $wpdb->get_var($wpdb->prepare(
                    "SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = 'pmid' AND meta_value = %s LIMIT 1",
                    $pmid
                ));
            }

            if (!$exists && $doi) {
                $exists = $wpdb->get_var($wpdb->prepare(
                    "SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = 'doi' AND meta_value = %s LIMIT 1",
                    $doi
                ));
            }

            if ($exists) {
                return 'skipped';
            }
        }

        // Create post
        $post_data = array(
            'post_title'   => isset($data['post_title']) ? sanitize_text_field($data['post_title']) : '',
            'post_content' => isset($data['post_content']) ? wp_kses_post($data['post_content']) : '',
            'post_status'  => $post_status,
            'post_type'    => self::POST_TYPE,
        );

        $post_id = wp_insert_post($post_data);

        if (is_wp_error($post_id)) {
            return 'error';
        }

        // Add meta fields
        $meta_fields = array(
            'pmid', 'doi', 'pmc_id', 'authors', 'journal', 'year',
            'doi_url', 'pubmed_url', 'github_url', 'citation_count', 'priority_score',
            'methods', 'protocols_urls', 'repositories_urls', 'rrids_urls',
            'has_protocols', 'has_github', 'has_data',
        );

        foreach ($meta_fields as $field) {
            if (isset($data[$field]) && $data[$field] !== '') {
                update_post_meta($post_id, $field, sanitize_text_field($data[$field]));
            }
        }

        // Add taxonomies (pipe-separated)
        $taxonomy_fields = array(
            'microscopy_techniques' => self::TAX_TECHNIQUES,
            'microscope_brands' => self::TAX_BRANDS,
            'microscope_models' => self::TAX_MODELS,
            'image_analysis_software' => self::TAX_ANALYSIS_SOFTWARE,
            'image_acquisition_software' => self::TAX_ACQUISITION_SOFTWARE,
            'organisms' => self::TAX_ORGANISMS,
            'protocols' => self::TAX_PROTOCOLS,
            'repositories' => self::TAX_REPOSITORIES,
        );

        foreach ($taxonomy_fields as $field => $taxonomy) {
            if (isset($data[$field]) && $data[$field] !== '') {
                $terms = array_map('trim', explode('|', $data[$field]));
                $terms = array_filter($terms);

                if (!empty($terms)) {
                    wp_set_object_terms($post_id, $terms, $taxonomy);
                }
            }
        }

        return 'imported';
    }
}

// Initialize plugin
add_action('plugins_loaded', function() {
    MicroHub_Importer::get_instance();
});

// Activation hook
register_activation_hook(__FILE__, function() {
    MicroHub_Importer::get_instance()->register_post_type();
    MicroHub_Importer::get_instance()->register_taxonomies();
    flush_rewrite_rules();
});

// Deactivation hook
register_deactivation_hook(__FILE__, function() {
    flush_rewrite_rules();
});
