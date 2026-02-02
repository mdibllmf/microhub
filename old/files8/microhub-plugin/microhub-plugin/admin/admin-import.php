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
            <li><?php _e('Run the MicroHub scraper: <code>python microhub_scraper.py --email your@email.com</code>', 'microhub'); ?></li>
            <li><?php _e('Export to JSON: <code>python microhub_scraper.py --export papers.json</code>', 'microhub'); ?></li>
            <li><?php _e('Upload the JSON file using the form above', 'microhub'); ?></li>
            <li><?php _e('Click "Import Papers" and wait for the process to complete', 'microhub'); ?></li>
        </ol>

        <h3><?php _e('Supported Tag Categories', 'microhub'); ?></h3>
        <ul>
            <li><strong>Techniques:</strong> Confocal, STED, PALM, STORM, Light-Sheet, Cryo-EM, SIM, TIRF, FRAP, FRET, etc.</li>
            <li><strong>Microscope Brands:</strong> Zeiss, Leica, Nikon, Olympus, Evident, Thermo Fisher, JEOL, etc.</li>
            <li><strong>Software:</strong> Fiji, ImageJ, CellProfiler, Imaris, napari, RELION, U-Net, etc.</li>
            <li><strong>Fluorophores:</strong> GFP, EGFP, mCherry, tdTomato, Alexa Fluor series, DAPI, Hoechst, etc.</li>
            <li><strong>Organisms:</strong> Mouse, Human, Zebrafish, Drosophila, C. elegans, Yeast, etc.</li>
            <li><strong>Cell Lines:</strong> HeLa, HEK293, U2OS, COS-7, CHO, iPSC, etc.</li>
            <li><strong>Sample Prep:</strong> PFA fixation, Immunostaining, Tissue clearing, CLARITY, Expansion, etc.</li>
            <li><strong>Protocols:</strong> protocols.io, Bio-protocol, JoVE, Nature Protocols, STAR Protocols</li>
            <li><strong>Repositories:</strong> IDR, Zenodo, GitHub, Figshare, EMPIAR, BioImage Archive</li>
            <li><strong>RRIDs:</strong> Antibodies (AB_), Software (SCR_), Cell Lines (CVCL_), Plasmids (Addgene_)</li>
        </ul>

        <h3><?php _e('Expected JSON Format (v5 Scraper)', 'microhub'); ?></h3>
        <pre style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:8px;overflow-x:auto;font-size:12px;"><code>[
  {
    "title": "Paper Title",
    "doi": "10.1234/example",
    "pmid": "12345678",
    "pmcid": "PMC1234567",
    "authors": "Smith J, Doe J",
    "journal": "Nature Methods",
    "year": 2023,
    "citation_count": 150,
    "abstract": "Paper abstract...",
    "full_text": "Full paper text if available...",
    "methods": "Methods section text...",
    
    <span style="color:#6a9955">// Tag Arrays (v5 format)</span>
    "microscopy_techniques": ["Confocal", "STED", "Super-Resolution"],
    "microscope_brands": ["Zeiss", "Leica"],
    "microscope_models": ["LSM 880", "SP8"],
    "image_analysis_software": ["Fiji", "ImageJ", "CellProfiler"],
    "fluorophores": ["GFP", "mCherry", "Alexa Fluor 488"],
    "organisms": ["Mouse", "Human"],
    "cell_lines": ["HeLa", "U2OS"],
    "sample_preparation": ["PFA fixation", "Immunostaining"],
    
    <span style="color:#6a9955">// Enrichment Data</span>
    "protocols": [
      {"name": "protocols.io", "url": "https://protocols.io/view/..."}
    ],
    "repositories": [
      {"name": "Zenodo", "url": "https://zenodo.org/...", "accession_id": "10.5281/..."}
    ],
    "rrids": [
      {"id": "RRID:AB_123456", "type": "antibody", "url": "https://..."}
    ],
    "antibodies": [
      {"id": "ab12345", "vendor": "Abcam", "url": "https://..."}
    ],
    "figures": [
      {"id": "fig1", "caption": "Figure 1 caption..."}
    ],
    "references": [
      {"num": 1, "text": "Reference text...", "doi": "10.1234/ref"}
    ]
  }
]</code></pre>
        <p><em><?php _e('Note: Both v3/v4/v5 scraper formats are supported. Legacy fields like "tags" and "microscope.brand" also work.', 'microhub'); ?></em></p>
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
        'protocols' => 0,          // Protocol URLs linked in papers
        'protocol_papers' => 0,    // Papers FROM protocol journals (JoVE, Nature Protocols, etc.)
        'repositories' => 0,
        'rrids' => 0,
        'rors' => 0,
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
    echo sprintf(__('Protocol URLs: %d, Protocol Papers: %d, Repositories: %d, GitHub: %d, Facilities: %d, RRIDs: %d, RORs: %d, Microscopes: %d', 'microhub'),
        $enrichment_stats['protocols'], $enrichment_stats['protocol_papers'] ?? 0, $enrichment_stats['repositories'],
        $enrichment_stats['github'] ?? 0, $enrichment_stats['facilities'] ?? 0,
        $enrichment_stats['rrids'], $enrichment_stats['rors'] ?? 0, $enrichment_stats['microscopes']);
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

    // Check if paper already exists (check BOTH post types)
    $existing = get_posts(array(
        'post_type' => array('mh_paper', 'mh_protocol'),
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

    // ============================================
    // DETERMINE POST TYPE FROM JSON DATA
    // The Python cleanup script sets post_type and protocol_type
    // ============================================
    $post_type = 'mh_paper'; // Default
    $protocol_type = null;
    
    // Check if JSON specifies post_type (from Python cleanup script)
    if (!empty($data['post_type']) && $data['post_type'] === 'mh_protocol') {
        $post_type = 'mh_protocol';
        $protocol_type = !empty($data['protocol_type']) ? sanitize_text_field($data['protocol_type']) : null;
    }
    // Also check is_protocol flag
    elseif (!empty($data['is_protocol'])) {
        $post_type = 'mh_paper'; // Keep as paper but will tag with protocol_type
        $protocol_type = !empty($data['protocol_type']) ? sanitize_text_field($data['protocol_type']) : null;
    }
    
    // Fallback: detect protocol journals by name if not already set
    if (!$protocol_type) {
        $journal = isset($data['journal']) ? strtolower($data['journal']) : '';
        $protocol_journal_map = array(
            'jove' => 'JoVE',
            'journal of visualized experiments' => 'JoVE',
            'j. vis. exp' => 'JoVE',
            'nature protocols' => 'Nature Protocols',
            'nat protoc' => 'Nature Protocols',
            'nat. protoc' => 'Nature Protocols',
            'bio-protocol' => 'Bio-protocol',
            'bio protocol' => 'Bio-protocol',
            'bioprotocol' => 'Bio-protocol',
            'star protocols' => 'STAR Protocols',
            'current protocols' => 'Current Protocols',
            'curr protoc' => 'Current Protocols',
            'cold spring harbor protocols' => 'Cold Spring Harbor Protocols',
            'cold spring harb protoc' => 'Cold Spring Harbor Protocols',
            'csh protocols' => 'Cold Spring Harbor Protocols',
            'methods in molecular biology' => 'Methods in Molecular Biology',
            'methods mol biol' => 'Methods in Molecular Biology',
            'methods in enzymology' => 'Methods in Enzymology',
            'meth enzymol' => 'Methods in Enzymology',
            'methodsx' => 'MethodsX',
            'methods x' => 'MethodsX',
            'protocol exchange' => 'Protocol Exchange',
            'biotechniques' => 'Biotechniques',
        );
        
        foreach ($protocol_journal_map as $pattern => $type) {
            if (stripos($journal, $pattern) !== false) {
                $protocol_type = $type;
                break;
            }
        }
    }

    // Create or update post
    $post_data = array(
        'post_type' => $post_type,
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
            update_post_meta($post_id, '_mh_has_protocols', '1');
            $enrichment_stats['protocols'] += count($protocols);
        }
    }
    
    // Also check has_protocols flag from JSON data
    if (!empty($data['has_protocols'])) {
        update_post_meta($post_id, '_mh_has_protocols', '1');
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
            
            // Get name - check both 'name' and 'type' fields (scraper uses 'type')
            $name = '';
            if (isset($r['name']) && !empty(trim($r['name']))) {
                $name = trim($r['name']);
            } elseif (isset($r['type']) && !empty(trim($r['type']))) {
                $name = trim($r['type']);
            }
            
            // Get accession ID - check both 'accession_id' and 'identifier' fields
            $accession_id = '';
            if (isset($r['accession_id']) && !empty(trim($r['accession_id']))) {
                $accession_id = trim($r['accession_id']);
            } elseif (isset($r['identifier']) && !empty(trim($r['identifier']))) {
                $accession_id = trim($r['identifier']);
            }
            
            // If URL is empty but name looks like a URL, swap them
            if (empty($url) && $name && (strpos($name, 'http') === 0 || strpos($name, 'zenodo') !== false || strpos($name, 'figshare') !== false)) {
                $url = $name;
                $name = 'Repository';
            }
            
            // If still no name, try to detect from URL
            if (empty($name) && $url) {
                if (strpos($url, 'zenodo') !== false) {
                    $name = 'Zenodo';
                } elseif (strpos($url, 'figshare') !== false) {
                    $name = 'Figshare';
                } elseif (strpos($url, 'github') !== false) {
                    $name = 'GitHub';
                } elseif (strpos($url, 'dryad') !== false) {
                    $name = 'Dryad';
                } elseif (strpos($url, 'osf.io') !== false) {
                    $name = 'OSF';
                } elseif (strpos($url, 'dataverse') !== false) {
                    $name = 'Dataverse';
                } elseif (strpos($url, 'mendeley') !== false) {
                    $name = 'Mendeley Data';
                } elseif (strpos($url, 'synapse') !== false) {
                    $name = 'Synapse';
                } elseif (strpos($url, 'ebi.ac.uk') !== false || strpos($url, 'empiar') !== false) {
                    $name = 'EMPIAR';
                } else {
                    $name = 'Data Repository';
                }
            }
            
            // Ensure URL has scheme
            if ($url && strpos($url, 'http') !== 0) {
                $url = 'https://' . ltrim($url, '/');
            }
            
            return array(
                'name' => sanitize_text_field($name),
                'url' => esc_url_raw($url),
                'accession_id' => sanitize_text_field($accession_id),
            );
        }, $repos_data);
        
        // Filter out repos with empty URLs
        $repositories = array_filter($repositories, function($r) {
            return !empty($r['url']);
        });
        
        if (!empty($repositories)) {
            update_post_meta($post_id, '_mh_repositories', wp_json_encode(array_values($repositories)));
            update_post_meta($post_id, '_mh_has_data', '1');
            $enrichment_stats['repositories'] += count($repositories);
        }
    }
    // Also check has_data flag from JSON data
    if (!empty($data['has_data'])) {
        update_post_meta($post_id, '_mh_has_data', '1');
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
        update_post_meta($post_id, '_mh_has_rrids', '1');
        $enrichment_stats['rrids'] += count($rrids);
    }
    // Also check has_rrids flag from JSON data
    if (!empty($data['has_rrids'])) {
        update_post_meta($post_id, '_mh_has_rrids', '1');
    }

    // Save RORs - Research Organization Registry identifiers (JSON array)
    if (!empty($data['rors']) && is_array($data['rors'])) {
        $rors = array_map(function($r) {
            // Handle both object format and simple string format
            if (is_array($r)) {
                return array(
                    'id' => sanitize_text_field($r['id'] ?? ''),
                    'url' => isset($r['url']) ? esc_url_raw($r['url']) : 'https://ror.org/' . ($r['id'] ?? ''),
                    'source' => sanitize_text_field($r['source'] ?? 'unknown'),
                );
            } else {
                // Simple string format (just the ID)
                $ror_id = sanitize_text_field($r);
                return array(
                    'id' => $ror_id,
                    'url' => 'https://ror.org/' . $ror_id,
                    'source' => 'unknown',
                );
            }
        }, $data['rors']);
        // Filter out empty entries
        $rors = array_filter($rors, function($r) { return !empty($r['id']); });
        if (!empty($rors)) {
            update_post_meta($post_id, '_mh_rors', wp_json_encode(array_values($rors)));
            $enrichment_stats['rors'] = ($enrichment_stats['rors'] ?? 0) + count($rors);
        }
    }

    // Save antibody sources (species used for antibodies, not model organisms)
    if (!empty($data['antibody_sources']) && is_array($data['antibody_sources'])) {
        $antibody_sources = array_map('sanitize_text_field', $data['antibody_sources']);
        update_post_meta($post_id, '_mh_antibody_sources', wp_json_encode($antibody_sources));
    }

    // Save antibodies (JSON array of antibody identifiers)
    if (!empty($data['antibodies']) && is_array($data['antibodies'])) {
        $antibodies = array_map(function($ab) {
            // Handle both object format and simple string format
            if (is_array($ab)) {
                return array(
                    'id' => sanitize_text_field($ab['id'] ?? ''),
                    'source' => sanitize_text_field($ab['source'] ?? 'unknown'),
                    'url' => isset($ab['url']) ? esc_url_raw($ab['url']) : '',
                );
            } else {
                return array(
                    'id' => sanitize_text_field($ab),
                    'source' => 'unknown',
                    'url' => '',
                );
            }
        }, $data['antibodies']);
        // Filter out empty entries
        $antibodies = array_filter($antibodies, function($ab) { return !empty($ab['id']); });
        if (!empty($antibodies)) {
            update_post_meta($post_id, '_mh_antibodies', wp_json_encode(array_values($antibodies)));
            $enrichment_stats['antibodies'] = ($enrichment_stats['antibodies'] ?? 0) + count($antibodies);
        }
    }

    // Save tag extraction source (methods vs title_abstract)
    if (!empty($data['tag_source'])) {
        update_post_meta($post_id, '_mh_tag_source', sanitize_text_field($data['tag_source']));
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
        update_post_meta($post_id, '_mh_has_github', '1');
        $enrichment_stats['github'] = ($enrichment_stats['github'] ?? 0) + 1;
    }
    // Also check has_github flag from JSON data
    if (!empty($data['has_github'])) {
        update_post_meta($post_id, '_mh_has_github', '1');
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

    // v3 scraper fields - microscopy techniques
    if (!empty($data['microscopy_techniques']) && is_array($data['microscopy_techniques'])) {
        wp_set_object_terms($post_id, $data['microscopy_techniques'], 'mh_technique', true);
    }

    // v3 scraper fields - microscope brands
    if (!empty($data['microscope_brands']) && is_array($data['microscope_brands'])) {
        wp_set_object_terms($post_id, $data['microscope_brands'], 'mh_microscope', true);
        // Also save as JSON meta for theme compatibility
        update_post_meta($post_id, '_mh_microscope_brands', wp_json_encode($data['microscope_brands']));
    }

    // v3 scraper fields - microscope models
    if (!empty($data['microscope_models']) && is_array($data['microscope_models'])) {
        wp_set_object_terms($post_id, $data['microscope_models'], 'mh_microscope_model');
        // Also save as JSON meta for theme compatibility
        update_post_meta($post_id, '_mh_microscope_models', wp_json_encode($data['microscope_models']));
    }

    // v3 scraper fields - image analysis software
    if (!empty($data['image_analysis_software']) && is_array($data['image_analysis_software'])) {
        wp_set_object_terms($post_id, $data['image_analysis_software'], 'mh_analysis_software');
        // Also add to general software taxonomy for backwards compatibility
        wp_set_object_terms($post_id, $data['image_analysis_software'], 'mh_software', true);
        // Also save as JSON meta for theme compatibility
        update_post_meta($post_id, '_mh_image_analysis_software', wp_json_encode($data['image_analysis_software']));
    }

    // v3 scraper fields - image acquisition software
    if (!empty($data['image_acquisition_software']) && is_array($data['image_acquisition_software'])) {
        wp_set_object_terms($post_id, $data['image_acquisition_software'], 'mh_acquisition_software');
        // Also add to general software taxonomy for backwards compatibility
        wp_set_object_terms($post_id, $data['image_acquisition_software'], 'mh_software', true);
        // Also save as JSON meta for theme compatibility
        update_post_meta($post_id, '_mh_image_acquisition_software', wp_json_encode($data['image_acquisition_software']));
    }

    // v3 scraper fields - sample preparation
    if (!empty($data['sample_preparation']) && is_array($data['sample_preparation'])) {
        wp_set_object_terms($post_id, $data['sample_preparation'], 'mh_sample_prep');
        // Also save as JSON meta for theme compatibility
        update_post_meta($post_id, '_mh_sample_preparation', wp_json_encode($data['sample_preparation']));
    }

    // v3 scraper fields - fluorophores
    if (!empty($data['fluorophores']) && is_array($data['fluorophores'])) {
        wp_set_object_terms($post_id, $data['fluorophores'], 'mh_fluorophore');
        // Also save as JSON meta for theme compatibility
        update_post_meta($post_id, '_mh_fluorophores', wp_json_encode($data['fluorophores']));
    }

    // v4 scraper fields - cell lines
    if (!empty($data['cell_lines']) && is_array($data['cell_lines'])) {
        wp_set_object_terms($post_id, $data['cell_lines'], 'mh_cell_line');
        // Also save as JSON meta for theme compatibility
        update_post_meta($post_id, '_mh_cell_lines', wp_json_encode($data['cell_lines']));
    }

    // ============================================
    // APPLY PROTOCOL TYPE TAXONOMY
    // Uses $protocol_type determined at post creation time
    // ============================================
    if (!empty($protocol_type)) {
        // Set the protocol type taxonomy on the post
        wp_set_object_terms($post_id, $protocol_type, 'mh_protocol_type');
        
        // Set the is_protocol flag
        update_post_meta($post_id, '_mh_is_protocol', '1');
        
        // IMPORTANT: Papers from protocol journals ARE protocols!
        // Set has_protocols so they show up in the Protocols filter
        update_post_meta($post_id, '_mh_has_protocols', '1');
        
        // Store the protocol type as meta too
        update_post_meta($post_id, '_mh_protocol_type', $protocol_type);
        
        // Track for stats
        if (!isset($enrichment_stats['protocol_papers'])) {
            $enrichment_stats['protocol_papers'] = 0;
        }
        $enrichment_stats['protocol_papers']++;
    }
    // ============================================
    // END PROTOCOL TYPE TAXONOMY
    // ============================================

    // ============================================
    // KNOWLEDGE BASE ENHANCED TAGGING
    // Use uploaded knowledge documents to suggest additional tags
    // ============================================
    if (function_exists('mh_get_tag_suggestions')) {
        $title = !empty($data['title']) ? $data['title'] : '';
        $abstract = !empty($data['abstract']) ? $data['abstract'] : '';
        
        if ($title || $abstract) {
            // Get existing tags to avoid duplicates
            $existing_techniques = wp_get_object_terms($post_id, 'mh_technique', array('fields' => 'names'));
            $existing_software = wp_get_object_terms($post_id, 'mh_software', array('fields' => 'names'));
            $existing_microscopes = wp_get_object_terms($post_id, 'mh_microscope', array('fields' => 'names'));
            $existing_all = array_merge(
                is_array($existing_techniques) ? $existing_techniques : array(),
                is_array($existing_software) ? $existing_software : array(),
                is_array($existing_microscopes) ? $existing_microscopes : array()
            );
            
            // Get suggestions from knowledge base
            $suggestions = mh_get_tag_suggestions($title, $abstract, $existing_all);
            
            // Apply suggested techniques
            if (!empty($suggestions['techniques'])) {
                wp_set_object_terms($post_id, $suggestions['techniques'], 'mh_technique', true);
                if (!isset($enrichment_stats['kb_techniques'])) {
                    $enrichment_stats['kb_techniques'] = 0;
                }
                $enrichment_stats['kb_techniques'] += count($suggestions['techniques']);
            }
            
            // Apply suggested software
            if (!empty($suggestions['software'])) {
                wp_set_object_terms($post_id, $suggestions['software'], 'mh_software', true);
                if (!isset($enrichment_stats['kb_software'])) {
                    $enrichment_stats['kb_software'] = 0;
                }
                $enrichment_stats['kb_software'] += count($suggestions['software']);
            }
            
            // Apply suggested microscopes
            if (!empty($suggestions['microscopes'])) {
                wp_set_object_terms($post_id, $suggestions['microscopes'], 'mh_microscope', true);
                if (!isset($enrichment_stats['kb_microscopes'])) {
                    $enrichment_stats['kb_microscopes'] = 0;
                }
                $enrichment_stats['kb_microscopes'] += count($suggestions['microscopes']);
            }
            
            // Apply suggested fluorophores
            if (!empty($suggestions['fluorophores'])) {
                wp_set_object_terms($post_id, $suggestions['fluorophores'], 'mh_fluorophore', true);
            }
            
            // Apply suggested organisms
            if (!empty($suggestions['organisms'])) {
                wp_set_object_terms($post_id, $suggestions['organisms'], 'mh_organism', true);
            }
        }
    }
    // ============================================
    // END KNOWLEDGE BASE ENHANCED TAGGING
    // ============================================

    // v4.1 scraper fields - figures (full objects with captions)
    if (!empty($data['figures']) && is_array($data['figures'])) {
        update_post_meta($post_id, '_mh_figures', wp_json_encode($data['figures']));
        update_post_meta($post_id, '_mh_figure_count', count($data['figures']));
    } elseif (!empty($data['figure_count'])) {
        update_post_meta($post_id, '_mh_figure_count', intval($data['figure_count']));
    }

    // v4.1 scraper fields - methods section
    if (!empty($data['methods'])) {
        update_post_meta($post_id, '_mh_methods', sanitize_textarea_field($data['methods']));
    }

    // v4.1 scraper fields - full text
    if (!empty($data['full_text'])) {
        update_post_meta($post_id, '_mh_full_text', $data['full_text']);
        update_post_meta($post_id, '_mh_has_full_text', '1');
    }
    
    // References (JSON array)
    if (!empty($data['references']) && is_array($data['references'])) {
        $references = array_map(function($ref) {
            return array(
                'num' => isset($ref['num']) ? intval($ref['num']) : null,
                'text' => isset($ref['text']) ? sanitize_textarea_field($ref['text']) : '',
                'doi' => isset($ref['doi']) ? sanitize_text_field($ref['doi']) : '',
                'pmid' => isset($ref['pmid']) ? sanitize_text_field($ref['pmid']) : '',
                'url' => isset($ref['url']) ? esc_url_raw($ref['url']) : '',
            );
        }, $data['references']);
        update_post_meta($post_id, '_mh_references', wp_json_encode($references));
    }

    // v4.1 scraper fields - additional microscopy details
    if (!empty($data['imaging_modalities']) && is_array($data['imaging_modalities'])) {
        update_post_meta($post_id, '_mh_imaging_modalities', wp_json_encode($data['imaging_modalities']));
    }
    if (!empty($data['staining_methods']) && is_array($data['staining_methods'])) {
        update_post_meta($post_id, '_mh_staining_methods', wp_json_encode($data['staining_methods']));
    }
    if (!empty($data['lasers']) && is_array($data['lasers'])) {
        update_post_meta($post_id, '_mh_lasers', wp_json_encode($data['lasers']));
    }
    if (!empty($data['detectors']) && is_array($data['detectors'])) {
        update_post_meta($post_id, '_mh_detectors', wp_json_encode($data['detectors']));
    }
    if (!empty($data['objectives']) && is_array($data['objectives'])) {
        update_post_meta($post_id, '_mh_objectives', wp_json_encode($data['objectives']));
    }
    if (!empty($data['filters']) && is_array($data['filters'])) {
        update_post_meta($post_id, '_mh_filters', wp_json_encode($data['filters']));
    }
    if (!empty($data['embedding_methods']) && is_array($data['embedding_methods'])) {
        update_post_meta($post_id, '_mh_embedding_methods', wp_json_encode($data['embedding_methods']));
    }
    if (!empty($data['fixation_methods']) && is_array($data['fixation_methods'])) {
        update_post_meta($post_id, '_mh_fixation_methods', wp_json_encode($data['fixation_methods']));
    }
    if (!empty($data['mounting_media']) && is_array($data['mounting_media'])) {
        update_post_meta($post_id, '_mh_mounting_media', wp_json_encode($data['mounting_media']));
    }

    // v4 scraper fields - influential citation count
    if (isset($data['influential_citation_count'])) {
        update_post_meta($post_id, '_mh_influential_citations', intval($data['influential_citation_count']));
    }

    // v4 scraper fields - citation source
    if (!empty($data['citation_source'])) {
        update_post_meta($post_id, '_mh_citation_source', sanitize_text_field($data['citation_source']));
    }

    // v4 scraper fields - semantic scholar ID
    if (!empty($data['semantic_scholar_id'])) {
        update_post_meta($post_id, '_mh_semantic_scholar_id', sanitize_text_field($data['semantic_scholar_id']));
    }

    return $is_update ? 'updated' : 'imported';
}
