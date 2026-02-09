<?php
/**
 * MicroHub Update Metrics Admin Page
 *
 * Allows updating citation counts, GitHub metrics, and data cleanup for existing papers
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

// ============================================
// FLUOROPHORE FULL NAMES FOR VERIFICATION
// ============================================
define('MH_FLUOROPHORE_FULL_NAMES', array(
    'GFP' => array('green fluorescent protein', 'gfp'),
    'EGFP' => array('enhanced green fluorescent protein', 'egfp'),
    'mEGFP' => array('monomeric enhanced green fluorescent protein', 'monomeric egfp', 'megfp'),
    'eGFP' => array('enhanced green fluorescent protein', 'egfp'),
    'YFP' => array('yellow fluorescent protein', 'yfp'),
    'EYFP' => array('enhanced yellow fluorescent protein', 'eyfp'),
    'CFP' => array('cyan fluorescent protein', 'cfp'),
    'ECFP' => array('enhanced cyan fluorescent protein', 'ecfp'),
    'BFP' => array('blue fluorescent protein', 'bfp'),
    'mCherry' => array('mcherry', 'monomeric cherry'),
    'tdTomato' => array('tdtomato', 'tandem dimer tomato'),
    'RFP' => array('red fluorescent protein', 'rfp', 'dsred'),
    'mRFP' => array('monomeric red fluorescent protein', 'mrfp'),
    'mKate' => array('mkate', 'mkate2'),
    'mScarlet' => array('mscarlet'),
    'mNeonGreen' => array('mneongreen', 'mng'),
    'mTurquoise' => array('mturquoise', 'mturquoise2'),
    'Cerulean' => array('cerulean'),
    'Venus' => array('venus fluorescent'),
    'Citrine' => array('citrine fluorescent'),
    'TagRFP' => array('tagrfp'),
    'DAPI' => array('dapi', "4',6-diamidino-2-phenylindole", '4,6-diamidino-2-phenylindole'),
    'Hoechst' => array('hoechst 33342', 'hoechst 33258', 'hoechst stain'),
    'DRAQ5' => array('draq5'),
    'SYTOX' => array('sytox green', 'sytox blue', 'sytox orange'),
    'Alexa Fluor 488' => array('alexa fluor 488', 'alexa488', 'af488'),
    'Alexa Fluor 546' => array('alexa fluor 546', 'alexa546', 'af546'),
    'Alexa Fluor 555' => array('alexa fluor 555', 'alexa555', 'af555'),
    'Alexa Fluor 568' => array('alexa fluor 568', 'alexa568', 'af568'),
    'Alexa Fluor 594' => array('alexa fluor 594', 'alexa594', 'af594'),
    'Alexa Fluor 633' => array('alexa fluor 633', 'alexa633', 'af633'),
    'Alexa Fluor 647' => array('alexa fluor 647', 'alexa647', 'af647'),
    'Alexa Fluor 680' => array('alexa fluor 680', 'alexa680', 'af680'),
    'Alexa Fluor 750' => array('alexa fluor 750', 'alexa750', 'af750'),
    'Cy3' => array('cy3', 'cyanine 3'),
    'Cy5' => array('cy5', 'cyanine 5'),
    'Cy5.5' => array('cy5.5', 'cyanine 5.5'),
    'Cy7' => array('cy7', 'cyanine 7'),
    'FITC' => array('fitc', 'fluorescein isothiocyanate', 'fluorescein'),
    'TRITC' => array('tritc', 'tetramethylrhodamine isothiocyanate'),
    'Rhodamine' => array('rhodamine', 'rhodamine b', 'rhodamine 6g'),
    'Texas Red' => array('texas red'),
    'PE' => array('phycoerythrin', 'r-phycoerythrin'),
    'APC' => array('allophycocyanin'),
    'PerCP' => array('peridinin chlorophyll protein', 'percp'),
    'Pacific Blue' => array('pacific blue'),
    'ATTO 488' => array('atto 488', 'atto488'),
    'ATTO 550' => array('atto 550', 'atto550'),
    'ATTO 565' => array('atto 565', 'atto565'),
    'ATTO 647N' => array('atto 647n', 'atto647n'),
    'CF dyes' => array('cf488', 'cf555', 'cf568', 'cf594', 'cf633', 'cf647', 'cf680'),
    'DyLight' => array('dylight 488', 'dylight 550', 'dylight 594', 'dylight 633', 'dylight 650'),
    'Fluo-4' => array('fluo-4', 'fluo4'),
    'Fura-2' => array('fura-2', 'fura2'),
    'Indo-1' => array('indo-1', 'indo1'),
    'Calcein' => array('calcein', 'calcein-am'),
    'Propidium Iodide' => array('propidium iodide', 'pi stain'),
    'Ethidium Bromide' => array('ethidium bromide'),
    'Acridine Orange' => array('acridine orange'),
    'MitoTracker' => array('mitotracker', 'mitotracker green', 'mitotracker red'),
    'LysoTracker' => array('lysotracker', 'lysotracker green', 'lysotracker red'),
    'ER-Tracker' => array('er-tracker', 'ertracker'),
    'CellTracker' => array('celltracker', 'cell tracker'),
    'FM dyes' => array('fm1-43', 'fm4-64', 'fm dye'),
    'DiI' => array('dii', 'diic18', '1,1-dioctadecyl'),
    'DiO' => array('dio', 'dioc18'),
    'DiD' => array('did', 'didc18'),
    'Quantum Dots' => array('quantum dot', 'qdot', 'qd525', 'qd565', 'qd605', 'qd655', 'qd705'),
    'SNAP-tag' => array('snap-tag', 'snap tag'),
    'Halo-tag' => array('halo-tag', 'halotag', 'halo tag'),
    'FlAsH' => array('flash', 'flash-edt2'),
    'ReAsH' => array('reash'),
    'SiR' => array('sir-actin', 'sir-tubulin', 'sir-dna', 'silicon rhodamine'),
    'JF dyes' => array('jf549', 'jf646', 'janelia fluor'),
    'mEos' => array('meos', 'meos2', 'meos3', 'meos4'),
    'Dendra' => array('dendra', 'dendra2'),
    'mMaple' => array('mmaple', 'mmaple3'),
    'PA-GFP' => array('pa-gfp', 'photoactivatable gfp'),
    'Kaede' => array('kaede'),
    'Dronpa' => array('dronpa'),
    'rsEGFP' => array('rsegfp', 'reversibly switchable egfp'),
));

// ============================================
// MICROSCOPE BRANDS (legitimate equipment manufacturers)
// ============================================
define('MH_MICROSCOPE_BRANDS', array(
    'Zeiss', 'Carl Zeiss', 'ZEISS',
    'Leica', 'Leica Microsystems',
    'Nikon', 'Nikon Instruments',
    'Olympus', 'Evident', // Olympus rebranded to Evident
    'JEOL',
    'FEI', 'Thermo Fisher Scientific FEI', // FEI is microscopy, but Thermo Fisher general is not
    'Hitachi', 'Hitachi High-Tech',
    'Bruker',
    'JPK', 'JPK Instruments',
    'Asylum Research', 'Oxford Instruments',
    'Park Systems',
    'Veeco',
    'NT-MDT',
    'Andor', 'Andor Technology',
    'Hamamatsu', 'Hamamatsu Photonics',
    'PCO', 'pco.edge',
    'Photometrics',
    'QImaging',
    'STED Abberior', 'Abberior',
    'PicoQuant',
    'Becker & Hickl',
    'ISS',
    'Intelligent Imaging Innovations', '3i',
    'Vutara',
    'ONI', 'Oxford Nanoimaging',
    'Nanolive',
    'Phase Focus',
    'Lyncee Tec',
    'CrestOptics',
    'Visitech',
    'Yokogawa', // spinning disk
    'Perkin Elmer', 'PerkinElmer', // Opera systems are microscopes
    'Molecular Devices', // ImageXpress
    'GE Healthcare', // DeltaVision (now Cytiva)
    'Applied Precision',
    'Visiopharm',
    'Fianium', // lasers
    'Coherent', // lasers
    'Spectra-Physics',
    'MPB Communications',
    'NKT Photonics',
    'Toptica',
    'Thorlabs',
    'Newport',
    'Prior Scientific',
    'ASI', 'Applied Scientific Instrumentation',
    'Mad City Labs',
    'Physik Instrumente', 'PI',
    'Sutter Instrument',
    'Lumencor',
    'CoolLED',
    'Lumenera',
    'Point Grey', 'FLIR', // cameras
    'Allied Vision',
    'Basler',
    'IDS',
    'iXon', // Andor camera line
    'EMCCD',
    'sCMOS',
));

// Brands that are NOT microscope brands (reagent suppliers, general equipment)
define('MH_NON_MICROSCOPE_BRANDS', array(
    'Thermo Fisher', 'ThermoFisher', 'Thermo Fisher Scientific', 'Thermo Scientific', 'Invitrogen', 'Life Technologies', 'Gibco', 'Applied Biosystems',
    'Sigma', 'Sigma-Aldrich', 'Merck', 'MilliporeSigma', 'EMD Millipore',
    'Bio-Rad', 'BioRad',
    'Qiagen',
    'Promega',
    'New England Biolabs', 'NEB',
    'Roche', 'Roche Diagnostics',
    'Abcam',
    'Cell Signaling Technology', 'CST',
    'Santa Cruz', 'Santa Cruz Biotechnology',
    'BD', 'BD Biosciences', 'Becton Dickinson',
    'R&D Systems',
    'BioLegend',
    'Jackson ImmunoResearch',
    'Vector Laboratories',
    'Dako', 'Agilent Dako',
    'Eppendorf',
    'Corning', 'Corning Life Sciences',
    'Greiner', 'Greiner Bio-One',
    'VWR',
    'Fisher Scientific', // different from Thermo Fisher microscopy
    'Agilent',
    'Waters',
    'Beckman Coulter',
    'GE Healthcare Life Sciences', 'Cytiva',
    'Sartorius',
    'Illumina',
    'PacBio', 'Pacific Biosciences',
    'Oxford Nanopore',
    '10x Genomics',
    'Lonza',
    'Takara', 'Takara Bio', 'Clontech',
    'IDT', 'Integrated DNA Technologies',
    'Eurofins',
    'GenScript',
    'Addgene', // not a brand but often listed
    'ATCC',
));

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

// ============================================
// LINK VERIFICATION AND CLEANUP
// ============================================

add_action('wp_ajax_microhub_verify_links', 'microhub_ajax_verify_links');
function microhub_ajax_verify_links() {
    check_ajax_referer('microhub_update_metrics_nonce', 'nonce');
    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied');
    }

    $paper_id = intval($_POST['paper_id'] ?? 0);
    if (!$paper_id) {
        wp_send_json_error('Invalid paper ID');
    }

    $results = array(
        'doi' => null,
        'pubmed' => null,
        'github' => array(),
        'repositories' => array(),
        'fixed' => 0,
        'removed' => 0,
    );

    // Check DOI link
    $doi = get_post_meta($paper_id, '_mh_doi', true);
    if ($doi) {
        $doi_valid = microhub_verify_doi($doi);
        $results['doi'] = array('value' => $doi, 'valid' => $doi_valid);
        if (!$doi_valid) {
            // Try to fix DOI format
            $fixed_doi = microhub_fix_doi_format($doi);
            if ($fixed_doi && $fixed_doi !== $doi && microhub_verify_doi($fixed_doi)) {
                update_post_meta($paper_id, '_mh_doi', $fixed_doi);
                $results['doi']['fixed'] = $fixed_doi;
                $results['fixed']++;
            }
        }
    }

    // Check PubMed ID
    $pubmed_id = get_post_meta($paper_id, '_mh_pubmed_id', true);
    if ($pubmed_id) {
        $pubmed_valid = microhub_verify_pubmed($pubmed_id);
        $results['pubmed'] = array('value' => $pubmed_id, 'valid' => $pubmed_valid);
    }

    // Check GitHub tools
    $github_tools_json = get_post_meta($paper_id, '_mh_github_tools', true);
    $github_tools = json_decode($github_tools_json, true) ?: array();
    $updated_github_tools = array();

    foreach ($github_tools as $tool) {
        $full_name = $tool['full_name'] ?? '';
        if (!$full_name) continue;

        $status = microhub_verify_github_repo($full_name);
        $tool_result = array('name' => $full_name, 'status' => $status);

        if ($status === 'valid') {
            $updated_github_tools[] = $tool;
            $tool_result['action'] = 'kept';
        } elseif ($status === 'moved') {
            // Try to get new location
            $new_name = microhub_get_github_redirect($full_name);
            if ($new_name) {
                $tool['full_name'] = $new_name;
                $tool['url'] = 'https://github.com/' . $new_name;
                $updated_github_tools[] = $tool;
                $tool_result['action'] = 'updated';
                $tool_result['new_name'] = $new_name;
                $results['fixed']++;
            } else {
                $tool_result['action'] = 'removed';
                $results['removed']++;
            }
        } else {
            // Invalid/not found - remove
            $tool_result['action'] = 'removed';
            $results['removed']++;
        }

        $results['github'][] = $tool_result;
        usleep(300000); // Rate limit
    }

    if (count($updated_github_tools) !== count($github_tools)) {
        update_post_meta($paper_id, '_mh_github_tools', wp_json_encode($updated_github_tools));
    }

    // Check data repositories
    $repos_json = get_post_meta($paper_id, '_mh_repositories', true);
    $repos = json_decode($repos_json, true) ?: array();
    $updated_repos = array();

    foreach ($repos as $repo) {
        $url = $repo['url'] ?? (is_string($repo) ? $repo : '');
        if (!$url) continue;

        $valid = microhub_verify_url($url);
        $repo_result = array('url' => $url, 'valid' => $valid);

        if ($valid) {
            $updated_repos[] = $repo;
            $repo_result['action'] = 'kept';
        } else {
            $repo_result['action'] = 'removed';
            $results['removed']++;
        }

        $results['repositories'][] = $repo_result;
        usleep(200000);
    }

    if (count($updated_repos) !== count($repos)) {
        update_post_meta($paper_id, '_mh_repositories', wp_json_encode($updated_repos));
    }

    wp_send_json_success($results);
}

/**
 * Verify DOI exists via CrossRef
 */
function microhub_verify_doi($doi) {
    if (empty($doi)) return false;

    // Clean DOI
    $doi = trim($doi);
    $doi = preg_replace('/^https?:\/\/(dx\.)?doi\.org\//', '', $doi);

    $url = "https://api.crossref.org/works/" . urlencode($doi);
    $response = wp_remote_head($url, array(
        'timeout' => 10,
        'headers' => array('User-Agent' => 'MicroHub/1.0 (WordPress Plugin)')
    ));

    if (is_wp_error($response)) return false;
    return wp_remote_retrieve_response_code($response) === 200;
}

/**
 * Fix common DOI format issues
 */
function microhub_fix_doi_format($doi) {
    $doi = trim($doi);

    // Remove URL prefix
    $doi = preg_replace('/^https?:\/\/(dx\.)?doi\.org\//', '', $doi);

    // Fix double-encoded characters
    $doi = str_replace('%2F', '/', $doi);

    // Remove trailing punctuation
    $doi = rtrim($doi, '.,;:');

    return $doi;
}

/**
 * Verify PubMed ID exists
 */
function microhub_verify_pubmed($pmid) {
    if (empty($pmid)) return false;

    $pmid = preg_replace('/[^0-9]/', '', $pmid);
    if (empty($pmid)) return false;

    $url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=" . urlencode($pmid) . "&retmode=json";
    $response = wp_remote_get($url, array('timeout' => 10));

    if (is_wp_error($response)) return false;
    if (wp_remote_retrieve_response_code($response) !== 200) return false;

    $data = json_decode(wp_remote_retrieve_body($response), true);
    return isset($data['result'][$pmid]);
}

/**
 * Verify GitHub repository exists
 */
function microhub_verify_github_repo($full_name) {
    if (empty($full_name) || strpos($full_name, '/') === false) return 'invalid';

    $github_token = get_option('microhub_github_token', '');
    $headers = array('Accept' => 'application/vnd.github.v3+json');
    if ($github_token) {
        $headers['Authorization'] = 'token ' . $github_token;
    }

    $url = "https://api.github.com/repos/" . $full_name;
    $response = wp_remote_get($url, array('headers' => $headers, 'timeout' => 10));

    if (is_wp_error($response)) return 'error';

    $code = wp_remote_retrieve_response_code($response);
    if ($code === 200) return 'valid';
    if ($code === 301 || $code === 302) return 'moved';
    if ($code === 404) return 'not_found';

    return 'error';
}

/**
 * Get GitHub redirect location for moved repos
 */
function microhub_get_github_redirect($full_name) {
    $github_token = get_option('microhub_github_token', '');
    $headers = array('Accept' => 'application/vnd.github.v3+json');
    if ($github_token) {
        $headers['Authorization'] = 'token ' . $github_token;
    }

    $url = "https://api.github.com/repos/" . $full_name;
    $response = wp_remote_get($url, array(
        'headers' => $headers,
        'timeout' => 10,
        'redirection' => 0
    ));

    if (is_wp_error($response)) return null;

    // Check for redirect
    $code = wp_remote_retrieve_response_code($response);
    if ($code === 301) {
        $location = wp_remote_retrieve_header($response, 'location');
        if ($location && preg_match('/github\.com\/repos\/([^\/]+\/[^\/]+)/', $location, $m)) {
            return $m[1];
        }
    }

    // Also check if response contains new full_name
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (isset($data['full_name']) && $data['full_name'] !== $full_name) {
        return $data['full_name'];
    }

    return null;
}

/**
 * Verify generic URL is accessible
 */
function microhub_verify_url($url) {
    if (empty($url)) return false;

    $response = wp_remote_head($url, array(
        'timeout' => 10,
        'redirection' => 3,
        'headers' => array('User-Agent' => 'MicroHub/1.0 (WordPress Plugin)')
    ));

    if (is_wp_error($response)) return false;

    $code = wp_remote_retrieve_response_code($response);
    return $code >= 200 && $code < 400;
}

// ============================================
// FLUOROPHORE TAG VERIFICATION
// ============================================

add_action('wp_ajax_microhub_verify_tags', 'microhub_ajax_verify_tags');
function microhub_ajax_verify_tags() {
    check_ajax_referer('microhub_update_metrics_nonce', 'nonce');
    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied');
    }

    $paper_id = intval($_POST['paper_id'] ?? 0);
    if (!$paper_id) {
        wp_send_json_error('Invalid paper ID');
    }

    // Get paper content to search
    $title = get_the_title($paper_id);
    $abstract = get_post_meta($paper_id, '_mh_abstract', true);
    $content = get_post_field('post_content', $paper_id);

    $searchable_text = strtolower($title . ' ' . $abstract . ' ' . $content);

    $results = array(
        'fluorophores' => array(),
        'removed' => 0,
        'kept' => 0,
    );

    // Check fluorophores
    $fluorophores_json = get_post_meta($paper_id, '_mh_fluorophores', true);
    $fluorophores = json_decode($fluorophores_json, true) ?: array();

    // Also check taxonomy
    $fluor_terms = wp_get_object_terms($paper_id, 'mh_fluorophore', array('fields' => 'names'));
    if (!is_wp_error($fluor_terms) && !empty($fluor_terms)) {
        $fluorophores = array_unique(array_merge($fluorophores, $fluor_terms));
    }

    $verified_fluorophores = array();

    foreach ($fluorophores as $fluor) {
        $fluor_name = is_array($fluor) ? ($fluor['name'] ?? '') : $fluor;
        if (empty($fluor_name)) continue;

        $is_valid = microhub_verify_fluorophore_in_text($fluor_name, $searchable_text);

        $fluor_result = array(
            'name' => $fluor_name,
            'valid' => $is_valid,
            'action' => $is_valid ? 'kept' : 'removed',
        );

        if ($is_valid) {
            $verified_fluorophores[] = $fluor;
            $results['kept']++;
        } else {
            $results['removed']++;
        }

        $results['fluorophores'][] = $fluor_result;
    }

    // Update meta if changed
    if (count($verified_fluorophores) !== count($fluorophores)) {
        update_post_meta($paper_id, '_mh_fluorophores', wp_json_encode($verified_fluorophores));

        // Also update taxonomy terms
        if (taxonomy_exists('mh_fluorophore')) {
            $term_names = array_map(function($f) {
                return is_array($f) ? ($f['name'] ?? '') : $f;
            }, $verified_fluorophores);
            wp_set_object_terms($paper_id, array_filter($term_names), 'mh_fluorophore');
        }
    }

    wp_send_json_success($results);
}

/**
 * Verify fluorophore appears in text using full name patterns
 */
function microhub_verify_fluorophore_in_text($fluorophore_name, $text) {
    $fluor_lower = strtolower(trim($fluorophore_name));
    $text_lower = strtolower($text);

    // Check exact match first
    if (strpos($text_lower, $fluor_lower) !== false) {
        return true;
    }

    // Check known full names
    $full_names = MH_FLUOROPHORE_FULL_NAMES;

    // Find matching entry
    foreach ($full_names as $key => $patterns) {
        $key_lower = strtolower($key);
        if ($fluor_lower === $key_lower || in_array($fluor_lower, array_map('strtolower', $patterns))) {
            // Check all patterns for this fluorophore
            foreach ($patterns as $pattern) {
                if (strpos($text_lower, strtolower($pattern)) !== false) {
                    return true;
                }
            }
            // Also check the key itself
            if (strpos($text_lower, $key_lower) !== false) {
                return true;
            }
        }
    }

    return false;
}

// ============================================
// BRAND CLASSIFICATION CLEANUP
// ============================================

add_action('wp_ajax_microhub_clean_brands', 'microhub_ajax_clean_brands');
function microhub_ajax_clean_brands() {
    check_ajax_referer('microhub_update_metrics_nonce', 'nonce');
    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied');
    }

    $paper_id = intval($_POST['paper_id'] ?? 0);
    if (!$paper_id) {
        wp_send_json_error('Invalid paper ID');
    }

    $results = array(
        'brands' => array(),
        'removed' => 0,
        'kept' => 0,
        'reclassified' => 0,
    );

    // Get microscope brands from meta
    $brands_json = get_post_meta($paper_id, '_mh_microscope_brands', true);
    $brands = json_decode($brands_json, true) ?: array();

    // Also check taxonomy
    $brand_terms = wp_get_object_terms($paper_id, 'mh_brand', array('fields' => 'names'));
    if (!is_wp_error($brand_terms) && !empty($brand_terms)) {
        $brands = array_unique(array_merge($brands, $brand_terms));
    }

    $valid_microscope_brands = array();
    $reagent_suppliers = array();

    $microscope_brand_list = MH_MICROSCOPE_BRANDS;
    $non_microscope_list = MH_NON_MICROSCOPE_BRANDS;

    foreach ($brands as $brand) {
        $brand_name = is_array($brand) ? ($brand['name'] ?? '') : $brand;
        if (empty($brand_name)) continue;

        $is_microscope_brand = microhub_is_microscope_brand($brand_name, $microscope_brand_list);
        $is_reagent_supplier = microhub_is_non_microscope_brand($brand_name, $non_microscope_list);

        $brand_result = array(
            'name' => $brand_name,
            'is_microscope_brand' => $is_microscope_brand,
            'is_reagent_supplier' => $is_reagent_supplier,
        );

        if ($is_microscope_brand && !$is_reagent_supplier) {
            $valid_microscope_brands[] = $brand_name;
            $brand_result['action'] = 'kept';
            $results['kept']++;
        } elseif ($is_reagent_supplier) {
            $reagent_suppliers[] = $brand_name;
            $brand_result['action'] = 'reclassified_to_supplier';
            $results['reclassified']++;
        } else {
            // Unknown - remove from microscope brands
            $brand_result['action'] = 'removed';
            $results['removed']++;
        }

        $results['brands'][] = $brand_result;
    }

    // Update microscope brands meta
    update_post_meta($paper_id, '_mh_microscope_brands', wp_json_encode($valid_microscope_brands));

    // Store reagent suppliers separately
    $existing_suppliers = json_decode(get_post_meta($paper_id, '_mh_reagent_suppliers', true), true) ?: array();
    $all_suppliers = array_unique(array_merge($existing_suppliers, $reagent_suppliers));
    update_post_meta($paper_id, '_mh_reagent_suppliers', wp_json_encode($all_suppliers));

    // Update taxonomy terms
    if (taxonomy_exists('mh_brand')) {
        wp_set_object_terms($paper_id, $valid_microscope_brands, 'mh_brand');
    }

    $results['valid_brands'] = $valid_microscope_brands;
    $results['reagent_suppliers'] = $all_suppliers;

    wp_send_json_success($results);
}

/**
 * Check if brand is a legitimate microscope brand
 */
function microhub_is_microscope_brand($brand_name, $brand_list) {
    $brand_lower = strtolower(trim($brand_name));

    foreach ($brand_list as $known_brand) {
        if (strtolower($known_brand) === $brand_lower) {
            return true;
        }
        // Partial match for variations
        if (stripos($brand_lower, strtolower($known_brand)) !== false ||
            stripos(strtolower($known_brand), $brand_lower) !== false) {
            return true;
        }
    }

    return false;
}

/**
 * Check if brand is a reagent/general supplier (not microscope brand)
 */
function microhub_is_non_microscope_brand($brand_name, $non_brand_list) {
    $brand_lower = strtolower(trim($brand_name));

    foreach ($non_brand_list as $non_brand) {
        if (strtolower($non_brand) === $brand_lower) {
            return true;
        }
        // Check for partial matches
        if (stripos($brand_lower, strtolower($non_brand)) !== false) {
            return true;
        }
    }

    return false;
}

// ============================================
// BATCH CLEANUP HANDLERS
// ============================================

add_action('wp_ajax_microhub_batch_cleanup', 'microhub_ajax_batch_cleanup');
function microhub_ajax_batch_cleanup() {
    check_ajax_referer('microhub_update_metrics_nonce', 'nonce');
    if (!current_user_can('manage_options')) {
        wp_send_json_error('Permission denied');
    }

    $cleanup_type = sanitize_text_field($_POST['cleanup_type'] ?? 'links');
    $offset = intval($_POST['offset'] ?? 0);
    $batch_size = intval($_POST['batch_size'] ?? 10);

    // Get papers
    $args = array(
        'post_type' => array('mh_paper', 'mh_protocol'),
        'post_status' => 'publish',
        'posts_per_page' => $batch_size,
        'offset' => $offset,
        'fields' => 'ids',
    );

    $paper_ids = get_posts($args);
    $total = wp_count_posts('mh_paper')->publish + wp_count_posts('mh_protocol')->publish;

    $results = array(
        'processed' => 0,
        'fixed' => 0,
        'removed' => 0,
    );

    foreach ($paper_ids as $paper_id) {
        if ($cleanup_type === 'links') {
            $r = microhub_cleanup_links_single($paper_id);
        } elseif ($cleanup_type === 'tags') {
            $r = microhub_cleanup_tags_single($paper_id);
        } elseif ($cleanup_type === 'brands') {
            $r = microhub_cleanup_brands_single($paper_id);
        } else {
            continue;
        }

        $results['processed']++;
        $results['fixed'] += $r['fixed'] ?? 0;
        $results['removed'] += $r['removed'] ?? 0;

        usleep(200000); // Rate limit
    }

    wp_send_json_success(array(
        'results' => $results,
        'offset' => $offset,
        'next_offset' => $offset + count($paper_ids),
        'total' => $total,
        'done' => count($paper_ids) < $batch_size,
    ));
}

function microhub_cleanup_links_single($paper_id) {
    $results = array('fixed' => 0, 'removed' => 0);

    // Verify GitHub tools
    $github_tools_json = get_post_meta($paper_id, '_mh_github_tools', true);
    $github_tools = json_decode($github_tools_json, true) ?: array();
    $updated_tools = array();

    foreach ($github_tools as $tool) {
        $full_name = $tool['full_name'] ?? '';
        if (!$full_name) continue;

        $status = microhub_verify_github_repo($full_name);
        if ($status === 'valid') {
            $updated_tools[] = $tool;
        } elseif ($status === 'moved') {
            $new_name = microhub_get_github_redirect($full_name);
            if ($new_name) {
                $tool['full_name'] = $new_name;
                $tool['url'] = 'https://github.com/' . $new_name;
                $updated_tools[] = $tool;
                $results['fixed']++;
            } else {
                $results['removed']++;
            }
        } else {
            $results['removed']++;
        }
        usleep(300000);
    }

    if (count($updated_tools) !== count($github_tools)) {
        update_post_meta($paper_id, '_mh_github_tools', wp_json_encode($updated_tools));
    }

    return $results;
}

function microhub_cleanup_tags_single($paper_id) {
    $results = array('fixed' => 0, 'removed' => 0);

    $title = get_the_title($paper_id);
    $abstract = get_post_meta($paper_id, '_mh_abstract', true);
    $content = get_post_field('post_content', $paper_id);
    $searchable_text = strtolower($title . ' ' . $abstract . ' ' . $content);

    $fluorophores_json = get_post_meta($paper_id, '_mh_fluorophores', true);
    $fluorophores = json_decode($fluorophores_json, true) ?: array();
    $verified = array();

    foreach ($fluorophores as $fluor) {
        $name = is_array($fluor) ? ($fluor['name'] ?? '') : $fluor;
        if (empty($name)) continue;

        if (microhub_verify_fluorophore_in_text($name, $searchable_text)) {
            $verified[] = $fluor;
        } else {
            $results['removed']++;
        }
    }

    if (count($verified) !== count($fluorophores)) {
        update_post_meta($paper_id, '_mh_fluorophores', wp_json_encode($verified));
    }

    return $results;
}

function microhub_cleanup_brands_single($paper_id) {
    $results = array('fixed' => 0, 'removed' => 0);

    $brands_json = get_post_meta($paper_id, '_mh_microscope_brands', true);
    $brands = json_decode($brands_json, true) ?: array();
    $valid_brands = array();
    $reagent_suppliers = array();

    foreach ($brands as $brand) {
        $name = is_array($brand) ? ($brand['name'] ?? '') : $brand;
        if (empty($name)) continue;

        if (microhub_is_microscope_brand($name, MH_MICROSCOPE_BRANDS) &&
            !microhub_is_non_microscope_brand($name, MH_NON_MICROSCOPE_BRANDS)) {
            $valid_brands[] = $name;
        } elseif (microhub_is_non_microscope_brand($name, MH_NON_MICROSCOPE_BRANDS)) {
            $reagent_suppliers[] = $name;
            $results['fixed']++;
        } else {
            $results['removed']++;
        }
    }

    update_post_meta($paper_id, '_mh_microscope_brands', wp_json_encode($valid_brands));

    $existing_suppliers = json_decode(get_post_meta($paper_id, '_mh_reagent_suppliers', true), true) ?: array();
    $all_suppliers = array_unique(array_merge($existing_suppliers, $reagent_suppliers));
    if (!empty($all_suppliers)) {
        update_post_meta($paper_id, '_mh_reagent_suppliers', wp_json_encode($all_suppliers));
    }

    return $results;
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
            <h2>🔄 Batch Update Metrics</h2>
            <p>Update metrics for all papers. This runs in batches to avoid timeouts.</p>

            <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
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

        <!-- Data Cleanup Section -->
        <div class="card" style="max-width: 800px; margin-bottom: 20px;">
            <h2>🧹 Data Cleanup & Verification</h2>
            <p>Verify and clean up data across all papers. Uses CrossRef and APIs to verify accuracy.</p>

            <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px; padding: 15px; background: #f9f9f9; border-radius: 8px;">
                    <h3 style="margin-top: 0;">🔗 Fix Broken Links</h3>
                    <p style="font-size: 13px; color: #666;">Verify DOIs, GitHub repos, and data repository links. Updates moved repos and removes dead links.</p>
                    <button type="button" id="btn-batch-links" class="button button-primary">
                        Start Link Cleanup
                    </button>
                </div>
                <div style="flex: 1; min-width: 200px; padding: 15px; background: #f9f9f9; border-radius: 8px;">
                    <h3 style="margin-top: 0;">🧬 Verify Fluorophore Tags</h3>
                    <p style="font-size: 13px; color: #666;">Checks that fluorophore names actually appear in paper text. Removes incorrect tags.</p>
                    <button type="button" id="btn-batch-tags" class="button button-primary">
                        Start Tag Verification
                    </button>
                </div>
                <div style="flex: 1; min-width: 200px; padding: 15px; background: #f9f9f9; border-radius: 8px;">
                    <h3 style="margin-top: 0;">🏭 Clean Brand Classification</h3>
                    <p style="font-size: 13px; color: #666;">Removes non-microscope brands (ThermoFisher, Sigma, etc.) and keeps only equipment manufacturers.</p>
                    <button type="button" id="btn-batch-brands" class="button button-primary">
                        Start Brand Cleanup
                    </button>
                </div>
            </div>

            <div id="cleanup-progress" style="display: none; background: #f0f0f1; padding: 15px; border-radius: 4px;">
                <div style="margin-bottom: 10px;">
                    <strong id="cleanup-progress-text">Processing...</strong>
                </div>
                <div style="background: #ddd; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div id="cleanup-progress-bar" style="background: #46b450; height: 100%; width: 0%; transition: width 0.3s;"></div>
                </div>
                <div id="cleanup-progress-stats" style="margin-top: 10px; font-size: 13px; color: #666;"></div>
            </div>
        </div>

        <!-- Single Paper Update -->
        <div class="card" style="max-width: 800px;">
            <h2>🎯 Update Single Paper</h2>
            <p>Update metrics or run cleanup for a specific paper by ID.</p>
            <div style="display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap;">
                <div>
                    <label for="single-paper-id"><strong>Paper ID:</strong></label><br>
                    <input type="number" id="single-paper-id" class="regular-text" placeholder="Enter paper post ID" style="width: 150px;" />
                </div>
                <button type="button" id="btn-single-citations" class="button">Update Citations</button>
                <button type="button" id="btn-single-github" class="button">Update GitHub</button>
                <button type="button" id="btn-single-links" class="button">Verify Links</button>
                <button type="button" id="btn-single-tags" class="button">Verify Tags</button>
                <button type="button" id="btn-single-brands" class="button">Clean Brands</button>
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

        // Cleanup batch updates
        let cleanupRunning = false;

        function runCleanupBatch(cleanupType, offset = 0) {
            if (!cleanupRunning) return;

            $.post(ajaxUrl, {
                action: 'microhub_batch_cleanup',
                nonce: nonce,
                cleanup_type: cleanupType,
                offset: offset,
                batch_size: 10
            }, function(response) {
                if (response.success) {
                    const data = response.data;
                    const progress = Math.min(100, Math.round((data.next_offset / data.total) * 100));

                    $('#cleanup-progress-bar').css('width', progress + '%');
                    $('#cleanup-progress-text').text('Processing... ' + data.next_offset + ' / ' + data.total);
                    $('#cleanup-progress-stats').html(
                        'Processed: ' + data.results.processed +
                        ' | Fixed/Updated: ' + data.results.fixed +
                        ' | Removed: ' + data.results.removed
                    );

                    if (!data.done && cleanupRunning) {
                        runCleanupBatch(cleanupType, data.next_offset);
                    } else {
                        cleanupRunning = false;
                        $('#cleanup-progress-text').text('Complete!');
                        $('#btn-batch-links, #btn-batch-tags, #btn-batch-brands').prop('disabled', false);
                    }
                } else {
                    cleanupRunning = false;
                    $('#cleanup-progress-text').text('Error: ' + response.data);
                    $('#btn-batch-links, #btn-batch-tags, #btn-batch-brands').prop('disabled', false);
                }
            }).fail(function() {
                cleanupRunning = false;
                $('#cleanup-progress-text').text('Request failed');
                $('#btn-batch-links, #btn-batch-tags, #btn-batch-brands').prop('disabled', false);
            });
        }

        $('#btn-batch-links').click(function() {
            if (cleanupRunning || batchRunning) return;
            if (!confirm('Verify all links and fix/remove broken ones? This uses external APIs and may take a while.')) return;

            cleanupRunning = true;
            $(this).prop('disabled', true);
            $('#btn-batch-tags, #btn-batch-brands').prop('disabled', true);
            $('#cleanup-progress').show();
            $('#cleanup-progress-bar').css('width', '0%');
            $('#cleanup-progress-text').text('Starting link verification...');
            $('#cleanup-progress-stats').text('');

            runCleanupBatch('links', 0);
        });

        $('#btn-batch-tags').click(function() {
            if (cleanupRunning || batchRunning) return;
            if (!confirm('Verify all fluorophore tags against paper content? Incorrect tags will be removed.')) return;

            cleanupRunning = true;
            $(this).prop('disabled', true);
            $('#btn-batch-links, #btn-batch-brands').prop('disabled', true);
            $('#cleanup-progress').show();
            $('#cleanup-progress-bar').css('width', '0%');
            $('#cleanup-progress-text').text('Starting tag verification...');
            $('#cleanup-progress-stats').text('');

            runCleanupBatch('tags', 0);
        });

        $('#btn-batch-brands').click(function() {
            if (cleanupRunning || batchRunning) return;
            if (!confirm('Clean brand classification? Non-microscope brands (ThermoFisher, Sigma, etc.) will be reclassified.')) return;

            cleanupRunning = true;
            $(this).prop('disabled', true);
            $('#btn-batch-links, #btn-batch-tags').prop('disabled', true);
            $('#cleanup-progress').show();
            $('#cleanup-progress-bar').css('width', '0%');
            $('#cleanup-progress-text').text('Starting brand cleanup...');
            $('#cleanup-progress-stats').text('');

            runCleanupBatch('brands', 0);
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

        // Single paper cleanup buttons
        $('#btn-single-links').click(function() {
            const paperId = $('#single-paper-id').val();
            if (!paperId) {
                alert('Please enter a paper ID');
                return;
            }

            $('#single-result').html('<em>Verifying links...</em>');

            $.post(ajaxUrl, {
                action: 'microhub_verify_links',
                nonce: nonce,
                paper_id: paperId
            }, function(response) {
                if (response.success) {
                    const d = response.data;
                    let html = '<div class="notice notice-success inline"><p>Link verification complete. Fixed: ' + d.fixed + ', Removed: ' + d.removed + '</p>';
                    if (d.doi) {
                        html += '<p>DOI: ' + d.doi.value + ' - ' + (d.doi.valid ? '✓ Valid' : '✗ Invalid') + (d.doi.fixed ? ' (fixed to: ' + d.doi.fixed + ')' : '') + '</p>';
                    }
                    if (d.github && d.github.length > 0) {
                        html += '<p>GitHub repos: ' + d.github.map(g => g.name + ' (' + g.action + ')').join(', ') + '</p>';
                    }
                    html += '</div>';
                    $('#single-result').html(html);
                } else {
                    $('#single-result').html('<div class="notice notice-error inline"><p>Error: ' + response.data + '</p></div>');
                }
            });
        });

        $('#btn-single-tags').click(function() {
            const paperId = $('#single-paper-id').val();
            if (!paperId) {
                alert('Please enter a paper ID');
                return;
            }

            $('#single-result').html('<em>Verifying fluorophore tags...</em>');

            $.post(ajaxUrl, {
                action: 'microhub_verify_tags',
                nonce: nonce,
                paper_id: paperId
            }, function(response) {
                if (response.success) {
                    const d = response.data;
                    let html = '<div class="notice notice-success inline"><p>Tag verification complete. Kept: ' + d.kept + ', Removed: ' + d.removed + '</p>';
                    if (d.fluorophores && d.fluorophores.length > 0) {
                        html += '<ul style="margin: 10px 0;">';
                        d.fluorophores.forEach(f => {
                            html += '<li>' + f.name + ': ' + (f.valid ? '✓ Verified' : '✗ Removed - not found in text') + '</li>';
                        });
                        html += '</ul>';
                    }
                    html += '</div>';
                    $('#single-result').html(html);
                } else {
                    $('#single-result').html('<div class="notice notice-error inline"><p>Error: ' + response.data + '</p></div>');
                }
            });
        });

        $('#btn-single-brands').click(function() {
            const paperId = $('#single-paper-id').val();
            if (!paperId) {
                alert('Please enter a paper ID');
                return;
            }

            $('#single-result').html('<em>Cleaning brand classification...</em>');

            $.post(ajaxUrl, {
                action: 'microhub_clean_brands',
                nonce: nonce,
                paper_id: paperId
            }, function(response) {
                if (response.success) {
                    const d = response.data;
                    let html = '<div class="notice notice-success inline"><p>Brand cleanup complete. Kept: ' + d.kept + ', Reclassified: ' + d.reclassified + ', Removed: ' + d.removed + '</p>';
                    if (d.brands && d.brands.length > 0) {
                        html += '<ul style="margin: 10px 0;">';
                        d.brands.forEach(b => {
                            let status = b.action === 'kept' ? '✓ Microscope brand' :
                                        b.action === 'reclassified_to_supplier' ? '→ Moved to reagent suppliers' : '✗ Removed';
                            html += '<li>' + b.name + ': ' + status + '</li>';
                        });
                        html += '</ul>';
                    }
                    if (d.valid_brands && d.valid_brands.length > 0) {
                        html += '<p><strong>Valid microscope brands:</strong> ' + d.valid_brands.join(', ') + '</p>';
                    }
                    if (d.reagent_suppliers && d.reagent_suppliers.length > 0) {
                        html += '<p><strong>Reagent suppliers:</strong> ' + d.reagent_suppliers.join(', ') + '</p>';
                    }
                    html += '</div>';
                    $('#single-result').html(html);
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
