<?php
/**
 * Admin import page for bulk importing papers from Excel or JSON
 * Updated to support Excel files (.xlsx) and new category structure from scraper v2.0
 *
 * Categories now properly separated:
 * - Microscopy Techniques (lab work: STED, Confocal, TIRF, etc.)
 * - Microscope Brands (manufacturers: Zeiss, Leica, Nikon, etc.)
 * - Microscope Models (specific systems: LSM 880, SP8, A1R, etc.)
 * - Image Analysis Software (processing: ImageJ, Fiji, CellProfiler, etc.)
 * - Image Acquisition Software (microscope control: ZEN, NIS-Elements, etc.)
 * - Organisms (model organisms)
 * - Protocol Sources (protocols.io, Bio-protocol, JoVE, etc.)
 * - Data Repositories (GitHub, Zenodo, Figshare, etc.)
 * - RRIDs and RORs
 */

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

/**
 * Import page content
 */
function microhub_import_page() {
    // Handle import
    if (isset($_POST['microhub_import']) && check_admin_referer('microhub_import_nonce')) {
        microhub_process_import();
    }
    ?>

    <div class="wrap">
        <h1><?php _e('Import Papers', 'microhub'); ?></h1>

        <p><?php _e('Upload an Excel (.xlsx) or JSON file containing papers to import. Excel is recommended for easier handling.', 'microhub'); ?></p>

        <form method="post" action="" enctype="multipart/form-data">
            <?php wp_nonce_field('microhub_import_nonce'); ?>

            <table class="form-table">
                <tr>
                    <th scope="row"><label for="import_file"><?php _e('Import File', 'microhub'); ?></label></th>
                    <td>
                        <input type="file" name="import_file" id="import_file" accept=".xlsx,.xls,.json" required />
                        <p class="description"><?php _e('Upload microhub_papers.xlsx (recommended) or papers_export.json', 'microhub'); ?></p>
                    </td>
                </tr>

                <tr>
                    <th scope="row"><?php _e('Import Options', 'microhub'); ?></th>
                    <td>
                        <label>
                            <input type="checkbox" name="skip_existing" value="1" checked />
                            <?php _e('Skip papers that already exist (based on PMID or DOI)', 'microhub'); ?>
                        </label>
                        <br />
                        <label>
                            <input type="checkbox" name="update_existing" value="1" />
                            <?php _e('Update existing papers with new data', 'microhub'); ?>
                        </label>
                    </td>
                </tr>

                <tr>
                    <th scope="row"><label for="post_status"><?php _e('Post Status', 'microhub'); ?></label></th>
                    <td>
                        <select name="post_status" id="post_status">
                            <option value="publish"><?php _e('Published', 'microhub'); ?></option>
                            <option value="draft"><?php _e('Draft', 'microhub'); ?></option>
                            <option value="pending"><?php _e('Pending Review', 'microhub'); ?></option>
                        </select>
                    </td>
                </tr>
            </table>

            <p class="submit">
                <input type="submit" name="microhub_import" class="button button-primary" value="<?php _e('Import Papers', 'microhub'); ?>" />
            </p>
        </form>

        <hr />

        <h2><?php _e('Category Definitions', 'microhub'); ?></h2>
        <table class="widefat">
            <thead>
                <tr>
                    <th><?php _e('Category', 'microhub'); ?></th>
                    <th><?php _e('Description', 'microhub'); ?></th>
                    <th><?php _e('Examples', 'microhub'); ?></th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Microscopy Techniques</strong></td>
                    <td>Lab work/methods required to do microscopy</td>
                    <td>STED, Confocal, TIRF, Two-Photon, Cryo-EM, FRET, FLIM</td>
                </tr>
                <tr>
                    <td><strong>Microscope Brands</strong></td>
                    <td>Microscope manufacturers</td>
                    <td>Zeiss, Leica, Nikon, Olympus, Andor, PerkinElmer</td>
                </tr>
                <tr>
                    <td><strong>Microscope Models</strong></td>
                    <td>Specific microscope systems</td>
                    <td>LSM 880, SP8, A1R, FV3000, Dragonfly, Airyscan</td>
                </tr>
                <tr>
                    <td><strong>Image Analysis Software</strong></td>
                    <td>Software for image processing and analysis</td>
                    <td>ImageJ, Fiji, CellProfiler, Imaris, Cellpose, StarDist</td>
                </tr>
                <tr>
                    <td><strong>Image Acquisition Software</strong></td>
                    <td>Software that controls microscopes and collects images</td>
                    <td>ZEN, NIS-Elements, LAS X, MetaMorph, MicroManager</td>
                </tr>
                <tr>
                    <td><strong>Organisms</strong></td>
                    <td>Model organisms studied</td>
                    <td>Mouse, Human, Zebrafish, Drosophila, C. elegans</td>
                </tr>
                <tr>
                    <td><strong>Protocol Sources</strong></td>
                    <td>Sources for protocols referenced in papers</td>
                    <td>protocols.io, Bio-protocol, JoVE, Nature Protocols</td>
                </tr>
                <tr>
                    <td><strong>Data Repositories</strong></td>
                    <td>Where data/code is stored</td>
                    <td>GitHub, Zenodo, Figshare, IDR, BioImage Archive, EMPIAR</td>
                </tr>
            </tbody>
        </table>

        <hr />

        <h2><?php _e('Excel Column Mapping', 'microhub'); ?></h2>
        <p><?php _e('The Excel exporter creates files with these columns (pipe-separated for taxonomies):', 'microhub'); ?></p>
        <table class="widefat">
            <thead>
                <tr>
                    <th><?php _e('Excel Column', 'microhub'); ?></th>
                    <th><?php _e('WordPress Field', 'microhub'); ?></th>
                    <th><?php _e('Type', 'microhub'); ?></th>
                </tr>
            </thead>
            <tbody>
                <tr><td>post_title</td><td>Post Title</td><td>Core</td></tr>
                <tr><td>post_content</td><td>Abstract</td><td>Core</td></tr>
                <tr><td>methods</td><td>Methods Section</td><td>Meta</td></tr>
                <tr><td>pmid</td><td>PubMed ID</td><td>Meta</td></tr>
                <tr><td>doi</td><td>DOI</td><td>Meta</td></tr>
                <tr><td>microscopy_techniques</td><td>Microscopy Techniques</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>microscope_brands</td><td>Microscope Brands</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>microscope_models</td><td>Microscope Models</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>image_analysis_software</td><td>Image Analysis Software</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>image_acquisition_software</td><td>Image Acquisition Software</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>organisms</td><td>Organisms</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>protocols</td><td>Protocol Sources</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>repositories</td><td>Data Repositories</td><td>Taxonomy (pipe-separated)</td></tr>
                <tr><td>rrids</td><td>RRIDs</td><td>Meta (JSON)</td></tr>
                <tr><td>rors</td><td>RORs</td><td>Meta (JSON)</td></tr>
            </tbody>
        </table>

        <hr />

        <h2><?php _e('Requirements for Excel Import', 'microhub'); ?></h2>
        <p><?php _e('Excel import requires the PhpSpreadsheet library. Install it via:', 'microhub'); ?></p>
        <pre><code>cd wp-content/plugins/microhub
composer require phpoffice/phpspreadsheet</code></pre>
        <p><?php _e('If PhpSpreadsheet is not installed, use JSON import instead.', 'microhub'); ?></p>

    </div>

    <?php
}

/**
 * Process the import
 */
function microhub_process_import() {
    // Check file upload
    if (!isset($_FILES['import_file']) || $_FILES['import_file']['error'] !== UPLOAD_ERR_OK) {
        echo '<div class="notice notice-error"><p>' . __('Error uploading file.', 'microhub') . '</p></div>';
        return;
    }

    // Increase memory and time limits for large imports
    @ini_set('memory_limit', '512M');
    set_time_limit(0);

    $file_path = $_FILES['import_file']['tmp_name'];
    $file_name = $_FILES['import_file']['name'];
    $file_ext = strtolower(pathinfo($file_name, PATHINFO_EXTENSION));

    $skip_existing = isset($_POST['skip_existing']);
    $update_existing = isset($_POST['update_existing']);
    $post_status = isset($_POST['post_status']) ? sanitize_text_field($_POST['post_status']) : 'publish';

    // Determine file type and process accordingly
    if ($file_ext === 'xlsx' || $file_ext === 'xls') {
        $result = microhub_import_excel($file_path, $skip_existing, $update_existing, $post_status);
    } elseif ($file_ext === 'json') {
        $result = microhub_import_json($file_path, $skip_existing, $update_existing, $post_status);
    } else {
        echo '<div class="notice notice-error"><p>' . __('Unsupported file type. Please upload .xlsx or .json file.', 'microhub') . '</p></div>';
        return;
    }

    // Display results
    echo '<div class="notice notice-success"><p>';
    echo sprintf(__('Import complete! Imported: %d, Updated: %d, Skipped: %d, Errors: %d', 'microhub'),
        $result['imported'], $result['updated'], $result['skipped'], $result['errors']);
    echo '</p>';
    if (!empty($result['stats'])) {
        echo '<p><strong>' . __('Data Imported:', 'microhub') . '</strong><br>';
        echo sprintf(__('Protocols: %d, Repositories: %d, GitHub: %d, RRIDs: %d, RORs: %d', 'microhub'),
            $result['stats']['protocols'] ?? 0,
            $result['stats']['repositories'] ?? 0,
            $result['stats']['github'] ?? 0,
            $result['stats']['rrids'] ?? 0,
            $result['stats']['rors'] ?? 0);
        echo '</p>';
    }
    echo '</div>';
}

/**
 * Import from Excel file
 */
function microhub_import_excel($file_path, $skip_existing, $update_existing, $post_status) {
    // Check if PhpSpreadsheet is available
    $autoload_path = MICROHUB_PLUGIN_DIR . 'vendor/autoload.php';
    if (!file_exists($autoload_path)) {
        echo '<div class="notice notice-error"><p>' . __('PhpSpreadsheet not installed. Please run: composer require phpoffice/phpspreadsheet', 'microhub') . '</p></div>';
        return array('imported' => 0, 'updated' => 0, 'skipped' => 0, 'errors' => 1, 'stats' => array());
    }

    require_once $autoload_path;

    $imported = 0;
    $updated = 0;
    $skipped = 0;
    $errors = 0;
    $stats = array(
        'protocols' => 0,
        'repositories' => 0,
        'github' => 0,
        'rrids' => 0,
        'rors' => 0,
    );

    try {
        $spreadsheet = \PhpOffice\PhpSpreadsheet\IOFactory::load($file_path);
        $worksheet = $spreadsheet->getActiveSheet();
        $highestRow = $worksheet->getHighestRow();
        $highestColumn = $worksheet->getHighestColumn();
        $highestColumnIndex = \PhpOffice\PhpSpreadsheet\Cell\Coordinate::columnIndexFromString($highestColumn);

        // Get headers from row 1
        $headers = array();
        for ($col = 1; $col <= $highestColumnIndex; $col++) {
            $headers[$col] = $worksheet->getCellByColumnAndRow($col, 1)->getValue();
        }

        echo '<div class="notice notice-info"><p>' . sprintf(__('Processing %d rows...', 'microhub'), $highestRow - 1) . '</p></div>';
        flush();
        ob_flush();

        global $wpdb;

        // Process rows in batches
        $batch_size = 50;

        for ($row = 2; $row <= $highestRow; $row++) {
            // Start transaction every batch
            if (($row - 2) % $batch_size === 0) {
                $wpdb->query('START TRANSACTION');
            }

            $row_data = array();
            for ($col = 1; $col <= $highestColumnIndex; $col++) {
                $header = $headers[$col];
                if ($header) {
                    $row_data[$header] = $worksheet->getCellByColumnAndRow($col, $row)->getValue();
                }
            }

            try {
                $result = microhub_import_paper_v2($row_data, $skip_existing, $update_existing, $post_status, $stats);

                if ($result === 'imported') {
                    $imported++;
                } elseif ($result === 'updated') {
                    $updated++;
                } elseif ($result === 'skipped') {
                    $skipped++;
                }
            } catch (Exception $e) {
                $errors++;
                error_log('MicroHub import error row ' . $row . ': ' . $e->getMessage());
            }

            // Commit every batch
            if (($row - 1) % $batch_size === 0 || $row === $highestRow) {
                $wpdb->query('COMMIT');

                // Progress update
                if ($row % 500 === 0) {
                    echo '<script>console.log("Processed ' . $row . ' rows...");</script>';
                    flush();
                    ob_flush();
                    set_time_limit(300);
                }
            }
        }

    } catch (Exception $e) {
        echo '<div class="notice notice-error"><p>' . __('Error reading Excel file: ', 'microhub') . $e->getMessage() . '</p></div>';
        $errors++;
    }

    return array(
        'imported' => $imported,
        'updated' => $updated,
        'skipped' => $skipped,
        'errors' => $errors,
        'stats' => $stats,
    );
}

/**
 * Import from JSON file (legacy support)
 */
function microhub_import_json($file_path, $skip_existing, $update_existing, $post_status) {
    $imported = 0;
    $updated = 0;
    $skipped = 0;
    $errors = 0;
    $stats = array(
        'protocols' => 0,
        'repositories' => 0,
        'github' => 0,
        'rrids' => 0,
        'rors' => 0,
    );

    $json_content = file_get_contents($file_path);
    $papers = json_decode($json_content, true);

    if (!$papers || !is_array($papers)) {
        echo '<div class="notice notice-error"><p>' . __('Invalid JSON format.', 'microhub') . '</p></div>';
        return array('imported' => 0, 'updated' => 0, 'skipped' => 0, 'errors' => 1, 'stats' => array());
    }

    unset($json_content);

    echo '<div class="notice notice-info"><p>' . sprintf(__('Processing %d papers...', 'microhub'), count($papers)) . '</p></div>';
    flush();
    ob_flush();

    global $wpdb;
    $batch_size = 50;

    foreach ($papers as $index => $paper) {
        if ($index % $batch_size === 0) {
            $wpdb->query('START TRANSACTION');
        }

        try {
            $result = microhub_import_paper_v2($paper, $skip_existing, $update_existing, $post_status, $stats);

            if ($result === 'imported') {
                $imported++;
            } elseif ($result === 'updated') {
                $updated++;
            } elseif ($result === 'skipped') {
                $skipped++;
            }
        } catch (Exception $e) {
            $errors++;
            error_log('MicroHub import error: ' . $e->getMessage());
        }

        if (($index + 1) % $batch_size === 0 || $index === count($papers) - 1) {
            $wpdb->query('COMMIT');
            set_time_limit(300);
        }
    }

    return array(
        'imported' => $imported,
        'updated' => $updated,
        'skipped' => $skipped,
        'errors' => $errors,
        'stats' => $stats,
    );
}

/**
 * Import a single paper with new v2.0 category structure
 */
function microhub_import_paper_v2($data, $skip_existing, $update_existing, $post_status, &$stats) {
    // Get identifiers
    $pmid = isset($data['pmid']) ? sanitize_text_field($data['pmid']) : '';
    $doi = isset($data['doi']) ? sanitize_text_field($data['doi']) : '';

    // Check if paper already exists
    $existing = null;

    if ($pmid) {
        $existing = get_posts(array(
            'post_type' => 'mh_paper',
            'meta_key' => '_mh_pubmed_id',
            'meta_value' => $pmid,
            'posts_per_page' => 1,
        ));
    }

    if (!$existing && $doi) {
        $existing = get_posts(array(
            'post_type' => 'mh_paper',
            'meta_key' => '_mh_doi',
            'meta_value' => $doi,
            'posts_per_page' => 1,
        ));
    }

    if ($existing && !empty($existing)) {
        if ($skip_existing && !$update_existing) {
            return 'skipped';
        }
        $post_id = $existing[0]->ID;
        $is_update = true;
    } else {
        $is_update = false;
    }

    // Get title - check both post_title and title
    $title = '';
    if (!empty($data['post_title'])) {
        $title = $data['post_title'];
    } elseif (!empty($data['title'])) {
        $title = $data['title'];
    }

    if (empty($title)) {
        return 'skipped'; // No title, skip
    }

    // Get content/abstract - check both post_content and abstract
    $content = '';
    if (!empty($data['post_content'])) {
        $content = $data['post_content'];
    } elseif (!empty($data['abstract'])) {
        $content = $data['abstract'];
    }

    // Create or update post
    $post_data = array(
        'post_type' => 'mh_paper',
        'post_title' => sanitize_text_field($title),
        'post_content' => wp_kses_post($content),
        'post_status' => $post_status,
    );

    if ($is_update) {
        $post_data['ID'] = $post_id;
        wp_update_post($post_data);
    } else {
        $post_id = wp_insert_post($post_data);
    }

    if (is_wp_error($post_id)) {
        throw new Exception('Failed to create post');
    }

    // Save core metadata
    update_post_meta($post_id, '_mh_doi', $doi);
    update_post_meta($post_id, '_mh_pubmed_id', $pmid);

    $meta_fields = array(
        'pmc_id' => '_mh_pmc_id',
        'authors' => '_mh_authors',
        'journal' => '_mh_journal',
        'year' => '_mh_publication_year',
        'doi_url' => '_mh_doi_url',
        'pubmed_url' => '_mh_pubmed_url',
        'pdf_url' => '_mh_pdf_url',
        'github_url' => '_mh_github_url',
        'citation_count' => '_mh_citation_count',
        'priority_score' => '_mh_priority_score',
        'methods' => '_mh_methods',
    );

    foreach ($meta_fields as $data_key => $meta_key) {
        if (isset($data[$data_key]) && $data[$data_key] !== '') {
            $value = $data[$data_key];
            if (in_array($data_key, array('year', 'citation_count', 'priority_score'))) {
                $value = intval($value);
            } elseif (in_array($data_key, array('doi_url', 'pubmed_url', 'pdf_url', 'github_url'))) {
                $value = esc_url_raw($value);
            } else {
                $value = sanitize_text_field($value);
            }
            update_post_meta($post_id, $meta_key, $value);

            if ($data_key === 'github_url' && $value) {
                $stats['github']++;
            }
        }
    }

    // Handle protocols (JSON or pipe-separated)
    if (!empty($data['protocols'])) {
        $protocols = microhub_parse_field($data['protocols']);
        if (!empty($protocols)) {
            // Extract protocol sources for taxonomy
            $protocol_sources = array();
            if (is_array($protocols) && isset($protocols[0]) && is_array($protocols[0])) {
                // Array of objects
                foreach ($protocols as $p) {
                    if (isset($p['source'])) {
                        $protocol_sources[] = $p['source'];
                    } elseif (isset($p['name'])) {
                        $protocol_sources[] = $p['name'];
                    }
                }
                update_post_meta($post_id, '_mh_protocols', wp_json_encode($protocols));
            } else {
                // Simple array or pipe-separated
                $protocol_sources = $protocols;
            }
            wp_set_object_terms($post_id, array_unique($protocol_sources), 'mh_protocol_source');
            $stats['protocols'] += count($protocol_sources);
        }
    }

    // Handle protocols_urls
    if (!empty($data['protocols_urls'])) {
        update_post_meta($post_id, '_mh_protocols_urls', sanitize_text_field($data['protocols_urls']));
    }

    // Handle repositories (JSON or pipe-separated)
    if (!empty($data['repositories'])) {
        $repositories = microhub_parse_field($data['repositories']);
        if (!empty($repositories)) {
            $repo_names = array();
            if (is_array($repositories) && isset($repositories[0]) && is_array($repositories[0])) {
                foreach ($repositories as $r) {
                    if (isset($r['name'])) {
                        $repo_names[] = $r['name'];
                    }
                }
                update_post_meta($post_id, '_mh_repositories', wp_json_encode($repositories));
            } else {
                $repo_names = $repositories;
            }
            wp_set_object_terms($post_id, array_unique($repo_names), 'mh_repository');
            $stats['repositories'] += count($repo_names);
        }
    }

    // Handle RRIDs
    if (!empty($data['rrids'])) {
        $rrids = microhub_parse_field($data['rrids']);
        if (!empty($rrids)) {
            if (is_array($rrids) && isset($rrids[0]) && is_array($rrids[0])) {
                update_post_meta($post_id, '_mh_rrids', wp_json_encode($rrids));
            } else {
                update_post_meta($post_id, '_mh_rrids', wp_json_encode($rrids));
            }
            $stats['rrids'] += count($rrids);
        }
    }

    // Handle RRIDs URLs
    if (!empty($data['rrids_urls'])) {
        update_post_meta($post_id, '_mh_rrids_urls', sanitize_text_field($data['rrids_urls']));
    }

    // Handle RORs
    if (!empty($data['rors'])) {
        $rors = microhub_parse_field($data['rors']);
        if (!empty($rors)) {
            update_post_meta($post_id, '_mh_rors', wp_json_encode($rors));
            $stats['rors'] += count($rors);
        }
    }

    // Set taxonomies from pipe-separated or JSON fields

    // Microscopy Techniques
    if (!empty($data['microscopy_techniques'])) {
        $techniques = microhub_parse_taxonomy_field($data['microscopy_techniques']);
        if (!empty($techniques)) {
            wp_set_object_terms($post_id, $techniques, 'mh_technique');
        }
    }

    // Microscope Brands
    if (!empty($data['microscope_brands'])) {
        $brands = microhub_parse_taxonomy_field($data['microscope_brands']);
        if (!empty($brands)) {
            wp_set_object_terms($post_id, $brands, 'mh_microscope_brand');
            // Also set legacy taxonomy for compatibility
            wp_set_object_terms($post_id, $brands, 'mh_microscope', true);
        }
    }

    // Microscope Models
    if (!empty($data['microscope_models'])) {
        $models = microhub_parse_taxonomy_field($data['microscope_models']);
        if (!empty($models)) {
            wp_set_object_terms($post_id, $models, 'mh_microscope_model');
            // Also set legacy taxonomy for compatibility
            wp_set_object_terms($post_id, $models, 'mh_microscope', true);
        }
    }

    // Image Analysis Software
    if (!empty($data['image_analysis_software'])) {
        $analysis_sw = microhub_parse_taxonomy_field($data['image_analysis_software']);
        if (!empty($analysis_sw)) {
            wp_set_object_terms($post_id, $analysis_sw, 'mh_analysis_software');
            // Also set legacy taxonomy for compatibility
            wp_set_object_terms($post_id, $analysis_sw, 'mh_software', true);
        }
    }

    // Image Acquisition Software
    if (!empty($data['image_acquisition_software'])) {
        $acq_sw = microhub_parse_taxonomy_field($data['image_acquisition_software']);
        if (!empty($acq_sw)) {
            wp_set_object_terms($post_id, $acq_sw, 'mh_acquisition_software');
            // Also set legacy taxonomy for compatibility
            wp_set_object_terms($post_id, $acq_sw, 'mh_software', true);
        }
    }

    // Organisms
    if (!empty($data['organisms'])) {
        $organisms = microhub_parse_taxonomy_field($data['organisms']);
        if (!empty($organisms)) {
            wp_set_object_terms($post_id, $organisms, 'mh_organism');
        }
    }

    // Legacy support: also check 'tags', 'techniques', 'software' fields
    if (!empty($data['tags'])) {
        $tags = microhub_parse_taxonomy_field($data['tags']);
        if (!empty($tags)) {
            wp_set_object_terms($post_id, $tags, 'mh_technique', true);
        }
    }

    if (!empty($data['techniques'])) {
        $techniques = microhub_parse_taxonomy_field($data['techniques']);
        if (!empty($techniques)) {
            wp_set_object_terms($post_id, $techniques, 'mh_technique', true);
        }
    }

    if (!empty($data['software'])) {
        $software = microhub_parse_taxonomy_field($data['software']);
        if (!empty($software)) {
            wp_set_object_terms($post_id, $software, 'mh_analysis_software', true);
            wp_set_object_terms($post_id, $software, 'mh_software', true);
        }
    }

    // Set flags
    update_post_meta($post_id, '_mh_has_protocols', !empty($data['has_protocols']) ? 1 : 0);
    update_post_meta($post_id, '_mh_has_github', !empty($data['has_github']) ? 1 : 0);
    update_post_meta($post_id, '_mh_has_data', !empty($data['has_data']) ? 1 : 0);

    return $is_update ? 'updated' : 'imported';
}

/**
 * Parse a field that could be JSON array, pipe-separated string, or simple value
 */
function microhub_parse_field($value) {
    if (empty($value)) {
        return array();
    }

    // If already an array, return it
    if (is_array($value)) {
        return $value;
    }

    // Try JSON decode
    $decoded = json_decode($value, true);
    if (is_array($decoded)) {
        return $decoded;
    }

    // Try pipe-separated
    if (strpos($value, '|') !== false) {
        return array_filter(array_map('trim', explode('|', $value)));
    }

    // Return as single-item array
    return array(trim($value));
}

/**
 * Parse taxonomy field (pipe-separated or JSON array of strings)
 */
function microhub_parse_taxonomy_field($value) {
    if (empty($value)) {
        return array();
    }

    // If already an array, sanitize and return
    if (is_array($value)) {
        return array_filter(array_map('sanitize_text_field', $value));
    }

    // Try JSON decode (for arrays of strings)
    $decoded = json_decode($value, true);
    if (is_array($decoded)) {
        return array_filter(array_map('sanitize_text_field', $decoded));
    }

    // Try pipe-separated
    if (strpos($value, '|') !== false) {
        return array_filter(array_map('sanitize_text_field', array_map('trim', explode('|', $value))));
    }

    // Return as single-item array
    $trimmed = trim($value);
    return $trimmed ? array(sanitize_text_field($trimmed)) : array();
}
