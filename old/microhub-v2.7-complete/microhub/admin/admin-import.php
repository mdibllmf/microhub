<?php
/**
 * Admin import page for bulk importing papers from JSON
 * Enhanced to handle ALL enriched data: protocols, repositories, RRIDs, microscopes
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

        <p><?php _e('Upload a JSON file containing papers to import. The JSON file should be exported from the Python scraper with enrichment data.', 'microhub'); ?></p>

        <form method="post" action="" enctype="multipart/form-data">
            <?php wp_nonce_field('microhub_import_nonce'); ?>

            <table class="form-table">
                <tr>
                    <th scope="row"><label for="json_file"><?php _e('JSON File', 'microhub'); ?></label></th>
                    <td>
                        <input type="file" name="json_file" id="json_file" accept=".json" required />
                        <p class="description"><?php _e('Upload the papers_export.json file (supports chunked files)', 'microhub'); ?></p>
                    </td>
                </tr>

                <tr>
                    <th scope="row"><?php _e('Import Options', 'microhub'); ?></th>
                    <td>
                        <label>
                            <input type="checkbox" name="skip_existing" value="1" checked />
                            <?php _e('Skip papers that already exist (based on DOI)', 'microhub'); ?>
                        </label>
                        <br />
                        <label>
                            <input type="checkbox" name="update_existing" value="1" />
                            <?php _e('Update existing papers with new enrichment data', 'microhub'); ?>
                        </label>
                    </td>
                </tr>
            </table>

            <p class="submit">
                <input type="submit" name="microhub_import" class="button button-primary" value="<?php _e('Import Papers', 'microhub'); ?>" />
            </p>
        </form>

        <hr />

        <h2><?php _e('Import Instructions', 'microhub'); ?></h2>

        <ol>
            <li><?php _e('Run the Python export script: <code>python export_for_wordpress.py</code>', 'microhub'); ?></li>
            <li><?php _e('Upload the generated <code>papers_export.json</code> file using the form above', 'microhub'); ?></li>
            <li><?php _e('Click "Import Papers" and wait for the process to complete', 'microhub'); ?></li>
            <li><?php _e('Large imports may take several minutes. Do not close this page.', 'microhub'); ?></li>
        </ol>

        <h3><?php _e('Supported Enrichment Data', 'microhub'); ?></h3>
        <ul>
            <li><strong>Protocols:</strong> protocols.io, Bio-protocol, JoVE, Nature Protocols, STAR Protocols</li>
            <li><strong>Repositories:</strong> IDR, BioImage Archive, EMPIAR, Zenodo, GitHub, Figshare, Dryad</li>
            <li><strong>RRIDs:</strong> Antibodies, Software, Cell Lines, Plasmids, Model Organisms</li>
            <li><strong>Microscopes:</strong> Brand and model detection (Zeiss, Leica, Nikon, Olympus, etc.)</li>
            <li><strong>Link Validation:</strong> DOI, PubMed, PDF link status</li>
        </ul>

        <h3><?php _e('Expected JSON Format', 'microhub'); ?></h3>
        <pre><code>[
  {
    "title": "Paper Title",
    "doi": "10.1234/example",
    "pmid": "12345678",
    "authors": "Smith J, Doe J",
    "journal": "Nature Methods",
    "year": 2023,
    "citation_count": 150,
    "abstract": "Paper abstract...",
    "pdf_url": "https://doi.org/10.1234/example",
    "tags": ["Confocal", "Live Cell", "Zeiss"],
    "meta_data": {
      "primary_technique": "Confocal",
      "animal_model": "mouse",
      "last_author": "Smith J"
    },
    "microscope": {
      "name": "Zeiss LSM 880",
      "brand": "Zeiss",
      "model": "LSM 880"
    },
    "protocols": [
      {"name": "protocols.io", "url": "https://protocols.io/view/..."}
    ],
    "repositories": [
      {"name": "IDR", "url": "https://idr.openmicroscopy.org/...", "accession_id": "idr0001"}
    ],
    "rrids": [
      {"id": "RRID:AB_123456", "type": "antibody"}
    ],
    "github_url": "https://github.com/user/repo",
    "facility": "Stanford Imaging Core"
  }
]</code></pre>
        <p><em>Note: Both "citation_count" and "citations" field names are supported.</em></p>
    </div>

    <?php
}

/**
 * Process the import - optimized for 300K+ papers
 * Uses streaming JSON parsing and batch database operations
 */
function microhub_process_import() {
    // Check file upload
    if (!isset($_FILES['json_file']) || $_FILES['json_file']['error'] !== UPLOAD_ERR_OK) {
        echo '<div class="notice notice-error"><p>' . __('Error uploading file.', 'microhub') . '</p></div>';
        return;
    }

    // Increase memory and time limits for large imports
    @ini_set('memory_limit', '512M');
    set_time_limit(0);

    $file_path = $_FILES['json_file']['tmp_name'];
    $file_size = filesize($file_path);

    $skip_existing = isset($_POST['skip_existing']);
    $update_existing = isset($_POST['update_existing']);

    $imported = 0;
    $skipped = 0;
    $updated = 0;
    $errors = 0;
    $batch_size = 100;

    // Track enrichment stats
    $enrichment_stats = array(
        'protocols' => 0,
        'repositories' => 0,
        'rrids' => 0,
        'microscopes' => 0,
        'github' => 0,
        'facilities' => 0,
    );

    // For large files (>50MB), use streaming parser
    if ($file_size > 50 * 1024 * 1024) {
        echo '<div class="notice notice-info"><p>' . __('Large file detected. Using streaming import...', 'microhub') . '</p></div>';
        flush();
        ob_flush();

        $result = microhub_stream_import($file_path, $skip_existing, $update_existing, $enrichment_stats);
        $imported = $result['imported'];
        $skipped = $result['skipped'];
        $updated = $result['updated'];
        $errors = $result['errors'];
    } else {
        // Standard import for smaller files
        $json_content = file_get_contents($file_path);
        $papers = json_decode($json_content, true);

        if (!$papers || !is_array($papers)) {
            echo '<div class="notice notice-error"><p>' . __('Invalid JSON format.', 'microhub') . '</p></div>';
            return;
        }

        // Free memory
        unset($json_content);

        // Process in batches for better performance
        $total = count($papers);
        $batches = array_chunk($papers, $batch_size);

        // Free original array
        unset($papers);

        echo '<div class="notice notice-info"><p>' . sprintf(__('Processing %d papers in %d batches...', 'microhub'), $total, count($batches)) . '</p></div>';
        flush();
        ob_flush();

        foreach ($batches as $batch_index => $batch) {
            // Start transaction for batch
            global $wpdb;
            $wpdb->query('START TRANSACTION');

            foreach ($batch as $paper) {
                try {
                    $result = microhub_import_paper($paper, $skip_existing, $update_existing, $enrichment_stats);

                    if ($result === 'imported') {
                        $imported++;
                    } elseif ($result === 'skipped') {
                        $skipped++;
                    } elseif ($result === 'updated') {
                        $updated++;
                    }
                } catch (Exception $e) {
                    $errors++;
                    error_log('MicroHub import error: ' . $e->getMessage());
                }
            }

            // Commit batch
            $wpdb->query('COMMIT');

            // Progress update every 10 batches
            if ($batch_index % 10 === 0) {
                $progress = round((($batch_index + 1) * $batch_size / $total) * 100);
                echo '<script>console.log("Import progress: ' . $progress . '%");</script>';
                flush();
                ob_flush();

                // Reset time limit
                set_time_limit(300);
            }

            // Free memory
            unset($batch);
        }
    }

    echo '<div class="notice notice-success"><p>';
    echo sprintf(__('Import complete! Imported: %d, Updated: %d, Skipped: %d, Errors: %d', 'microhub'),
        $imported, $updated, $skipped, $errors);
    echo '</p>';
    echo '<p><strong>' . __('Enrichment Data Imported:', 'microhub') . '</strong><br>';
    echo sprintf(__('Protocols: %d, Repositories: %d, GitHub: %d, Facilities: %d, RRIDs: %d, Microscopes: %d', 'microhub'),
        $enrichment_stats['protocols'], $enrichment_stats['repositories'],
        $enrichment_stats['github'] ?? 0, $enrichment_stats['facilities'] ?? 0,
        $enrichment_stats['rrids'], $enrichment_stats['microscopes']);
    echo '</p></div>';
}

/**
 * Stream import for very large files (>50MB)
 * Parses JSON line by line to avoid memory issues
 */
function microhub_stream_import($file_path, $skip_existing, $update_existing, &$enrichment_stats) {
    $imported = 0;
    $skipped = 0;
    $updated = 0;
    $errors = 0;

    global $wpdb;

    // Open file for streaming
    $handle = fopen($file_path, 'r');
    if (!$handle) {
        return array('imported' => 0, 'skipped' => 0, 'updated' => 0, 'errors' => 1);
    }

    $buffer = '';
    $in_array = false;
    $depth = 0;
    $batch = array();
    $batch_size = 50;

    while (!feof($handle)) {
        $chunk = fread($handle, 8192);
        $buffer .= $chunk;

        // Process complete JSON objects from buffer
        while (true) {
            // Skip leading whitespace and commas
            $buffer = ltrim($buffer, " \t\n\r,");

            // Check for array start
            if (!$in_array && substr($buffer, 0, 1) === '[') {
                $in_array = true;
                $buffer = substr($buffer, 1);
                continue;
            }

            // Check for array end
            if ($in_array && substr($buffer, 0, 1) === ']') {
                break 2; // End of file
            }

            // Find complete JSON object
            if (substr($buffer, 0, 1) !== '{') {
                break;
            }

            // Count braces to find complete object
            $depth = 0;
            $end = -1;
            $in_string = false;
            $escape = false;

            for ($i = 0; $i < strlen($buffer); $i++) {
                $char = $buffer[$i];

                if ($escape) {
                    $escape = false;
                    continue;
                }

                if ($char === '\\') {
                    $escape = true;
                    continue;
                }

                if ($char === '"') {
                    $in_string = !$in_string;
                    continue;
                }

                if (!$in_string) {
                    if ($char === '{') $depth++;
                    if ($char === '}') $depth--;

                    if ($depth === 0) {
                        $end = $i;
                        break;
                    }
                }
            }

            if ($end === -1) {
                break; // Need more data
            }

            // Extract and parse JSON object
            $json_str = substr($buffer, 0, $end + 1);
            $buffer = substr($buffer, $end + 1);

            $paper = json_decode($json_str, true);
            if ($paper) {
                $batch[] = $paper;

                // Process batch
                if (count($batch) >= $batch_size) {
                    $wpdb->query('START TRANSACTION');

                    foreach ($batch as $p) {
                        try {
                            $result = microhub_import_paper($p, $skip_existing, $update_existing, $enrichment_stats);
                            if ($result === 'imported') $imported++;
                            elseif ($result === 'skipped') $skipped++;
                            elseif ($result === 'updated') $updated++;
                        } catch (Exception $e) {
                            $errors++;
                        }
                    }

                    $wpdb->query('COMMIT');
                    $batch = array();

                    // Reset time limit
                    set_time_limit(300);

                    // Progress update
                    $processed = $imported + $skipped + $updated + $errors;
                    if ($processed % 1000 === 0) {
                        echo '<script>console.log("Processed: ' . $processed . ' papers");</script>';
                        flush();
                        ob_flush();
                    }
                }
            } else {
                $errors++;
            }
        }
    }

    // Process remaining batch
    if (!empty($batch)) {
        $wpdb->query('START TRANSACTION');
        foreach ($batch as $p) {
            try {
                $result = microhub_import_paper($p, $skip_existing, $update_existing, $enrichment_stats);
                if ($result === 'imported') $imported++;
                elseif ($result === 'skipped') $skipped++;
                elseif ($result === 'updated') $updated++;
            } catch (Exception $e) {
                $errors++;
            }
        }
        $wpdb->query('COMMIT');
    }

    fclose($handle);

    return array(
        'imported' => $imported,
        'skipped' => $skipped,
        'updated' => $updated,
        'errors' => $errors
    );
}

/**
 * Import a single paper with ALL enrichment data
 */
function microhub_import_paper($data, $skip_existing, $update_existing, &$enrichment_stats) {
    $doi = sanitize_text_field($data['doi']);

    // Check if paper already exists
    $existing = get_posts(array(
        'post_type' => 'mh_paper',
        'meta_key' => '_mh_doi',
        'meta_value' => $doi,
        'posts_per_page' => 1,
    ));

    if ($existing) {
        if ($skip_existing && !$update_existing) {
            return 'skipped';
        }
        $post_id = $existing[0]->ID;
        $is_update = true;
    } else {
        $is_update = false;
    }

    // Create or update post
    $post_data = array(
        'post_type' => 'mh_paper',
        'post_title' => sanitize_text_field($data['title']),
        'post_status' => 'publish',
        'post_content' => '',
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
    update_post_meta($post_id, '_mh_pubmed_id', isset($data['pmid']) ? sanitize_text_field($data['pmid']) : '');
    update_post_meta($post_id, '_mh_authors', isset($data['authors']) ? sanitize_text_field($data['authors']) : '');
    update_post_meta($post_id, '_mh_journal', isset($data['journal']) ? sanitize_text_field($data['journal']) : '');
    update_post_meta($post_id, '_mh_publication_year', isset($data['year']) ? intval($data['year']) : 0);
    
    // Handle citation count - check both field names
    $citation_count = 0;
    if (isset($data['citations'])) {
        $citation_count = intval($data['citations']);
    } elseif (isset($data['citation_count'])) {
        $citation_count = intval($data['citation_count']);
    }
    update_post_meta($post_id, '_mh_citation_count', $citation_count);
    
    update_post_meta($post_id, '_mh_abstract', isset($data['abstract']) ? sanitize_textarea_field($data['abstract']) : '');
    update_post_meta($post_id, '_mh_pdf_url', isset($data['pdf_url']) ? esc_url_raw($data['pdf_url']) : '');
    update_post_meta($post_id, '_mh_paper_url', isset($data['paper_url']) ? esc_url_raw($data['paper_url']) : '');

    // Save microscope info
    if (!empty($data['microscope']) && is_array($data['microscope'])) {
        update_post_meta($post_id, '_mh_microscope', sanitize_text_field($data['microscope']['name']));
        update_post_meta($post_id, '_mh_microscope_brand', sanitize_text_field($data['microscope']['brand']));
        update_post_meta($post_id, '_mh_microscope_model', sanitize_text_field($data['microscope']['model']));
        $enrichment_stats['microscopes']++;
    }

    // Save protocols (JSON array)
    if (!empty($data['protocols']) && is_array($data['protocols'])) {
        $protocols = array_map(function($p) {
            // Get URL - handle case where URL might be in name field
            $url = isset($p['url']) ? trim($p['url']) : '';
            $name = isset($p['name']) ? trim($p['name']) : '';
            
            // If URL is empty but name looks like a URL, swap them
            if (empty($url) && $name && (strpos($name, 'http') === 0 || strpos($name, 'protocols.io') !== false || strpos($name, '.com') !== false || strpos($name, '.org') !== false)) {
                $url = $name;
                $name = 'Protocol';
            }
            
            // Ensure URL has scheme
            if ($url && strpos($url, 'http') !== 0) {
                $url = 'https://' . ltrim($url, '/');
            }
            
            return array(
                'name' => sanitize_text_field($name ?: 'Protocol'),
                'url' => esc_url_raw($url),
                'source' => isset($p['source']) ? sanitize_text_field($p['source']) : 'fulltext',
            );
        }, $data['protocols']);
        
        // Filter out protocols with empty URLs
        $protocols = array_filter($protocols, function($p) {
            return !empty($p['url']);
        });
        
        if (!empty($protocols)) {
            update_post_meta($post_id, '_mh_protocols', wp_json_encode(array_values($protocols)));
            $enrichment_stats['protocols'] += count($protocols);
        }
    }

    // Save repositories (JSON array) - check both field names
    $repos_data = null;
    if (!empty($data['repositories']) && is_array($data['repositories'])) {
        $repos_data = $data['repositories'];
    } elseif (!empty($data['image_repositories']) && is_array($data['image_repositories'])) {
        $repos_data = $data['image_repositories'];
    }
    if ($repos_data) {
        $repositories = array_map(function($r) {
            // Get URL
            $url = isset($r['url']) ? trim($r['url']) : '';
            $name = isset($r['name']) ? trim($r['name']) : 'Unknown';
            
            // If URL is empty but name looks like a URL, swap them
            if (empty($url) && $name && (strpos($name, 'http') === 0 || strpos($name, 'zenodo') !== false || strpos($name, 'figshare') !== false)) {
                $url = $name;
                $name = 'Repository';
            }
            
            // Ensure URL has scheme
            if ($url && strpos($url, 'http') !== 0) {
                $url = 'https://' . ltrim($url, '/');
            }
            
            return array(
                'name' => sanitize_text_field($name),
                'url' => esc_url_raw($url),
                'accession_id' => sanitize_text_field($r['accession_id'] ?? ''),
            );
        }, $repos_data);
        
        // Filter out repos with empty URLs
        $repositories = array_filter($repositories, function($r) {
            return !empty($r['url']);
        });
        
        if (!empty($repositories)) {
            update_post_meta($post_id, '_mh_repositories', wp_json_encode(array_values($repositories)));
            $enrichment_stats['repositories'] += count($repositories);
        }
    }

    // Save RRIDs (JSON array)
    if (!empty($data['rrids']) && is_array($data['rrids'])) {
        $rrids = array_map(function($r) {
            return array(
                'id' => sanitize_text_field($r['id']),
                'type' => sanitize_text_field($r['type']),
                'url' => isset($r['url']) ? esc_url_raw($r['url']) : 'https://scicrunch.org/resolver/' . $r['id'],
            );
        }, $data['rrids']);
        update_post_meta($post_id, '_mh_rrids', wp_json_encode($rrids));
        $enrichment_stats['rrids'] += count($rrids);
    }

    // Save GitHub URL (check multiple possible field names)
    $github_url = '';
    if (!empty($data['github_url'])) {
        $github_url = $data['github_url'];
    } elseif (!empty($data['github'])) {
        $github_url = $data['github'];
    } elseif (!empty($data['code_repository'])) {
        $github_url = $data['code_repository'];
    } elseif (!empty($data['meta_data']['github'])) {
        $github_url = $data['meta_data']['github'];
    }
    if ($github_url) {
        update_post_meta($post_id, '_mh_github_url', esc_url_raw($github_url));
        $enrichment_stats['github'] = ($enrichment_stats['github'] ?? 0) + 1;
    }

    // Save facility info
    $facility = '';
    if (!empty($data['facility'])) {
        $facility = $data['facility'];
    } elseif (!empty($data['imaging_facility'])) {
        $facility = $data['imaging_facility'];
    } elseif (!empty($data['meta_data']['facility'])) {
        $facility = $data['meta_data']['facility'];
    }
    if ($facility) {
        update_post_meta($post_id, '_mh_facility', sanitize_text_field($facility));
        $enrichment_stats['facilities'] = ($enrichment_stats['facilities'] ?? 0) + 1;
    }

    // Save figure URLs (for thumbnails)
    if (!empty($data['figure_urls']) && is_array($data['figure_urls'])) {
        $figure_urls = array_map('esc_url_raw', $data['figure_urls']);
        update_post_meta($post_id, '_mh_figure_urls', wp_json_encode($figure_urls));
        // Use first figure as thumbnail URL
        if (!empty($figure_urls[0])) {
            update_post_meta($post_id, '_mh_thumbnail_url', esc_url_raw($figure_urls[0]));
        }
    }

    // Save link validation status (JSON object)
    if (!empty($data['link_status']) && is_array($data['link_status'])) {
        update_post_meta($post_id, '_mh_link_status', wp_json_encode($data['link_status']));
    }

    // Save additional metadata
    if (!empty($data['meta_data']) && is_array($data['meta_data'])) {
        if (!empty($data['meta_data']['primary_technique'])) {
            update_post_meta($post_id, '_mh_primary_technique', sanitize_text_field($data['meta_data']['primary_technique']));
        }
        if (!empty($data['meta_data']['animal_model'])) {
            update_post_meta($post_id, '_mh_animal_model', sanitize_text_field($data['meta_data']['animal_model']));
        }
        if (!empty($data['meta_data']['last_author'])) {
            update_post_meta($post_id, '_mh_last_author', sanitize_text_field($data['meta_data']['last_author']));
        }
    }

    // Also check top-level fields (export script puts these at top level)
    if (!empty($data['primary_technique'])) {
        update_post_meta($post_id, '_mh_primary_technique', sanitize_text_field($data['primary_technique']));
    }
    if (!empty($data['animal_model'])) {
        update_post_meta($post_id, '_mh_animal_model', sanitize_text_field($data['animal_model']));
    }
    if (!empty($data['last_author'])) {
        update_post_meta($post_id, '_mh_last_author', sanitize_text_field($data['last_author']));
    }
    if (!empty($data['pmc_id'])) {
        update_post_meta($post_id, '_mh_pmc_id', sanitize_text_field($data['pmc_id']));
    }

    // Set taxonomies from tags
    if (!empty($data['tags'])) {
        wp_set_object_terms($post_id, $data['tags'], 'mh_technique');
    }

    // Set organism taxonomy - check both locations
    $animal = '';
    if (!empty($data['animal_model'])) {
        $animal = $data['animal_model'];
    } elseif (!empty($data['meta_data']['animal_model'])) {
        $animal = $data['meta_data']['animal_model'];
    }
    if ($animal) {
        wp_set_object_terms($post_id, array($animal), 'mh_organism');
    }

    // Set microscope taxonomy
    if (!empty($data['microscope']['brand'])) {
        wp_set_object_terms($post_id, array($data['microscope']['brand']), 'mh_microscope');
    }

    // Set software taxonomy
    if (!empty($data['software']) && is_array($data['software'])) {
        wp_set_object_terms($post_id, $data['software'], 'mh_software');
    }

    // Also handle organisms array if present
    if (!empty($data['organisms']) && is_array($data['organisms'])) {
        wp_set_object_terms($post_id, $data['organisms'], 'mh_organism');
    }

    // Also handle techniques array if present (in addition to tags)
    if (!empty($data['techniques']) && is_array($data['techniques'])) {
        wp_set_object_terms($post_id, $data['techniques'], 'mh_technique', true); // true = append
    }

    return $is_update ? 'updated' : 'imported';
}
