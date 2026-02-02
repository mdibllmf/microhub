<?php
/**
 * MicroHub Meta Boxes v3.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class MicroHub_Meta_Boxes {
    
    public function init() {
        add_action('add_meta_boxes', array($this, 'add_meta_boxes'));
        add_action('save_post', array($this, 'save_meta_boxes'), 10, 2);
    }
    
    public function add_meta_boxes() {
        add_meta_box(
            'microhub_paper_details',
            __('Paper Details', 'microhub'),
            array($this, 'render_paper_details'),
            'mh_paper',
            'normal',
            'high'
        );
        
        add_meta_box(
            'microhub_paper_resources',
            __('Resources', 'microhub'),
            array($this, 'render_resources'),
            'mh_paper',
            'normal',
            'default'
        );
        
        add_meta_box(
            'microhub_paper_status',
            __('Status', 'microhub'),
            array($this, 'render_status'),
            'mh_paper',
            'side',
            'default'
        );
    }
    
    public function render_paper_details($post) {
        wp_nonce_field('microhub_save_meta', 'microhub_meta_nonce');
        
        $fields = array(
            'doi' => get_post_meta($post->ID, '_mh_doi', true),
            'pubmed_id' => get_post_meta($post->ID, '_mh_pubmed_id', true),
            'pmc_id' => get_post_meta($post->ID, '_mh_pmc_id', true),
            'authors' => get_post_meta($post->ID, '_mh_authors', true),
            'journal' => get_post_meta($post->ID, '_mh_journal', true),
            'year' => get_post_meta($post->ID, '_mh_publication_year', true),
            'citations' => get_post_meta($post->ID, '_mh_citation_count', true),
            'priority' => get_post_meta($post->ID, '_mh_priority_score', true),
            'abstract' => get_post_meta($post->ID, '_mh_abstract', true),
            'methods' => get_post_meta($post->ID, '_mh_methods', true),
            'github_url' => get_post_meta($post->ID, '_mh_github_url', true),
            'pdf_url' => get_post_meta($post->ID, '_mh_pdf_url', true),
            'pmc_url' => get_post_meta($post->ID, '_mh_pmc_url', true),
        );
        ?>
        <style>
            .mh-meta-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 15px; }
            .mh-meta-full { grid-column: span 2; }
            .mh-meta-field label { display: block; font-weight: 600; margin-bottom: 5px; }
            .mh-meta-field input[type="text"],
            .mh-meta-field input[type="number"],
            .mh-meta-field input[type="url"],
            .mh-meta-field textarea { width: 100%; }
        </style>
        
        <div class="mh-meta-grid">
            <div class="mh-meta-field">
                <label for="mh_doi">DOI</label>
                <input type="text" id="mh_doi" name="mh_doi" value="<?php echo esc_attr($fields['doi']); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pubmed_id">PubMed ID</label>
                <input type="text" id="mh_pubmed_id" name="mh_pubmed_id" value="<?php echo esc_attr($fields['pubmed_id']); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pmc_id">PMC ID</label>
                <input type="text" id="mh_pmc_id" name="mh_pmc_id" value="<?php echo esc_attr($fields['pmc_id']); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_journal">Journal</label>
                <input type="text" id="mh_journal" name="mh_journal" value="<?php echo esc_attr($fields['journal']); ?>" />
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_authors">Authors</label>
                <input type="text" id="mh_authors" name="mh_authors" value="<?php echo esc_attr($fields['authors']); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_year">Year</label>
                <input type="number" id="mh_year" name="mh_year" value="<?php echo esc_attr($fields['year']); ?>" min="1900" max="2100" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_citations">Citations</label>
                <input type="number" id="mh_citations" name="mh_citations" value="<?php echo esc_attr($fields['citations']); ?>" min="0" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_priority">Priority Score</label>
                <input type="number" id="mh_priority" name="mh_priority" value="<?php echo esc_attr($fields['priority']); ?>" min="0" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_github_url">GitHub URL</label>
                <input type="url" id="mh_github_url" name="mh_github_url" value="<?php echo esc_attr($fields['github_url']); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pdf_url">PDF URL</label>
                <input type="url" id="mh_pdf_url" name="mh_pdf_url" value="<?php echo esc_attr($fields['pdf_url']); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pmc_url">PMC URL</label>
                <input type="url" id="mh_pmc_url" name="mh_pmc_url" value="<?php echo esc_attr($fields['pmc_url']); ?>" />
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_abstract">Abstract</label>
                <textarea id="mh_abstract" name="mh_abstract" rows="5"><?php echo esc_textarea($fields['abstract']); ?></textarea>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_methods">Methods</label>
                <textarea id="mh_methods" name="mh_methods" rows="6"><?php echo esc_textarea($fields['methods']); ?></textarea>
            </div>
        </div>
        <?php
    }
    
    public function render_resources($post) {
        $protocols = get_post_meta($post->ID, '_mh_protocols', true);
        $repositories = get_post_meta($post->ID, '_mh_repositories', true);
        $rrids = get_post_meta($post->ID, '_mh_rrids', true);
        $figures = get_post_meta($post->ID, '_mh_figures', true);
        ?>
        <div class="mh-meta-grid">
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_protocols">Protocols (JSON)</label>
                <textarea id="mh_protocols" name="mh_protocols" rows="3"><?php echo esc_textarea($protocols); ?></textarea>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_repositories">Repositories (JSON)</label>
                <textarea id="mh_repositories" name="mh_repositories" rows="3"><?php echo esc_textarea($repositories); ?></textarea>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_rrids">RRIDs (JSON)</label>
                <textarea id="mh_rrids" name="mh_rrids" rows="3"><?php echo esc_textarea($rrids); ?></textarea>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_figures">Figures (JSON)</label>
                <textarea id="mh_figures" name="mh_figures" rows="3"><?php echo esc_textarea($figures); ?></textarea>
            </div>
        </div>
        <?php
    }
    
    public function render_status($post) {
        $has_full_text = get_post_meta($post->ID, '_mh_has_full_text', true);
        $has_figures = get_post_meta($post->ID, '_mh_has_figures', true);
        $has_protocols = get_post_meta($post->ID, '_mh_has_protocols', true);
        $has_github = get_post_meta($post->ID, '_mh_has_github', true);
        $has_data = get_post_meta($post->ID, '_mh_has_data', true);
        ?>
        <p>
            <label>
                <input type="checkbox" name="mh_has_full_text" value="1" <?php checked($has_full_text, 1); ?> />
                Has Full Text
            </label>
        </p>
        <p>
            <label>
                <input type="checkbox" name="mh_has_figures" value="1" <?php checked($has_figures, 1); ?> />
                Has Figures
            </label>
        </p>
        <p>
            <label>
                <input type="checkbox" name="mh_has_protocols" value="1" <?php checked($has_protocols, 1); ?> />
                Has Protocols
            </label>
        </p>
        <p>
            <label>
                <input type="checkbox" name="mh_has_github" value="1" <?php checked($has_github, 1); ?> />
                Has GitHub
            </label>
        </p>
        <p>
            <label>
                <input type="checkbox" name="mh_has_data" value="1" <?php checked($has_data, 1); ?> />
                Has Data Repository
            </label>
        </p>
        <?php
    }
    
    public function save_meta_boxes($post_id, $post) {
        // Check nonce
        if (!isset($_POST['microhub_meta_nonce']) || !wp_verify_nonce($_POST['microhub_meta_nonce'], 'microhub_save_meta')) {
            return;
        }
        
        // Check autosave
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }
        
        // Check post type
        if ($post->post_type !== 'mh_paper') {
            return;
        }
        
        // Check permissions
        if (!current_user_can('edit_post', $post_id)) {
            return;
        }
        
        // Text fields
        $text_fields = array(
            'mh_doi' => '_mh_doi',
            'mh_pubmed_id' => '_mh_pubmed_id',
            'mh_pmc_id' => '_mh_pmc_id',
            'mh_authors' => '_mh_authors',
            'mh_journal' => '_mh_journal',
        );
        
        foreach ($text_fields as $field => $meta_key) {
            if (isset($_POST[$field])) {
                update_post_meta($post_id, $meta_key, sanitize_text_field($_POST[$field]));
            }
        }
        
        // Number fields
        if (isset($_POST['mh_year'])) {
            update_post_meta($post_id, '_mh_publication_year', intval($_POST['mh_year']));
        }
        if (isset($_POST['mh_citations'])) {
            update_post_meta($post_id, '_mh_citation_count', intval($_POST['mh_citations']));
        }
        if (isset($_POST['mh_priority'])) {
            update_post_meta($post_id, '_mh_priority_score', intval($_POST['mh_priority']));
        }
        
        // URL fields
        $url_fields = array(
            'mh_github_url' => '_mh_github_url',
            'mh_pdf_url' => '_mh_pdf_url',
            'mh_pmc_url' => '_mh_pmc_url',
        );
        
        foreach ($url_fields as $field => $meta_key) {
            if (isset($_POST[$field])) {
                update_post_meta($post_id, $meta_key, esc_url_raw($_POST[$field]));
            }
        }
        
        // Textarea fields
        if (isset($_POST['mh_abstract'])) {
            update_post_meta($post_id, '_mh_abstract', sanitize_textarea_field($_POST['mh_abstract']));
        }
        if (isset($_POST['mh_methods'])) {
            update_post_meta($post_id, '_mh_methods', sanitize_textarea_field($_POST['mh_methods']));
        }
        
        // JSON fields
        $json_fields = array('mh_protocols', 'mh_repositories', 'mh_rrids', 'mh_figures');
        foreach ($json_fields as $field) {
            if (isset($_POST[$field])) {
                $value = sanitize_textarea_field($_POST[$field]);
                if (!empty($value)) {
                    // Validate JSON
                    $decoded = json_decode($value);
                    if (json_last_error() === JSON_ERROR_NONE) {
                        update_post_meta($post_id, '_' . $field, $value);
                    }
                } else {
                    update_post_meta($post_id, '_' . $field, '');
                }
            }
        }
        
        // Checkbox fields
        $checkboxes = array(
            'mh_has_full_text' => '_mh_has_full_text',
            'mh_has_figures' => '_mh_has_figures',
            'mh_has_protocols' => '_mh_has_protocols',
            'mh_has_github' => '_mh_has_github',
            'mh_has_data' => '_mh_has_data',
        );
        
        foreach ($checkboxes as $field => $meta_key) {
            $value = isset($_POST[$field]) ? 1 : 0;
            update_post_meta($post_id, $meta_key, $value);
        }
    }
}
