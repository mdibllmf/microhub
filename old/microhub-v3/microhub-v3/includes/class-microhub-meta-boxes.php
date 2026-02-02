<?php
/**
 * MicroHub Meta Boxes v3.0
 * Register meta boxes for paper metadata including new v3 fields
 */

class MicroHub_Meta_Boxes {
    
    public function init() {
        add_action('add_meta_boxes', array($this, 'add_meta_boxes'));
        add_action('save_post', array($this, 'save_meta_boxes'));
    }
    
    /**
     * Add meta boxes
     */
    public function add_meta_boxes() {
        // Basic Details
        add_meta_box(
            'microhub_paper_details',
            __('📄 Paper Details', 'microhub'),
            array($this, 'render_paper_details_meta_box'),
            'mh_paper',
            'normal',
            'high'
        );
        
        // Links & Identifiers
        add_meta_box(
            'microhub_paper_links',
            __('🔗 Links & Identifiers', 'microhub'),
            array($this, 'render_links_meta_box'),
            'mh_paper',
            'normal',
            'high'
        );
        
        // Resources (Protocols, Repositories, Code)
        add_meta_box(
            'microhub_paper_resources',
            __('📋 Resources', 'microhub'),
            array($this, 'render_resources_meta_box'),
            'mh_paper',
            'normal',
            'default'
        );
        
        // Figures
        add_meta_box(
            'microhub_paper_figures',
            __('🖼️ Figures', 'microhub'),
            array($this, 'render_figures_meta_box'),
            'mh_paper',
            'normal',
            'default'
        );
        
        // Status Sidebar
        add_meta_box(
            'microhub_paper_status',
            __('📊 Paper Status', 'microhub'),
            array($this, 'render_status_meta_box'),
            'mh_paper',
            'side',
            'default'
        );
    }
    
    /**
     * Render paper details meta box
     */
    public function render_paper_details_meta_box($post) {
        wp_nonce_field('microhub_save_meta_box_data', 'microhub_meta_box_nonce');
        
        $doi = get_post_meta($post->ID, '_mh_doi', true);
        $pubmed_id = get_post_meta($post->ID, '_mh_pubmed_id', true);
        $pmc_id = get_post_meta($post->ID, '_mh_pmc_id', true);
        $authors = get_post_meta($post->ID, '_mh_authors', true);
        $journal = get_post_meta($post->ID, '_mh_journal', true);
        $publication_year = get_post_meta($post->ID, '_mh_publication_year', true);
        $citation_count = get_post_meta($post->ID, '_mh_citation_count', true);
        $priority_score = get_post_meta($post->ID, '_mh_priority_score', true);
        $abstract = get_post_meta($post->ID, '_mh_abstract', true);
        $methods = get_post_meta($post->ID, '_mh_methods', true);
        ?>
        
        <style>
            .mh-meta-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .mh-meta-full { grid-column: span 2; }
            .mh-meta-field label { display: block; font-weight: 600; margin-bottom: 5px; }
            .mh-meta-field input[type="text"],
            .mh-meta-field input[type="number"],
            .mh-meta-field input[type="url"],
            .mh-meta-field textarea { width: 100%; }
            .mh-meta-field textarea { min-height: 100px; }
            .mh-meta-field .description { color: #666; font-size: 12px; margin-top: 3px; }
        </style>
        
        <div class="mh-meta-grid">
            <div class="mh-meta-field">
                <label for="mh_doi"><?php _e('DOI', 'microhub'); ?></label>
                <input type="text" id="mh_doi" name="mh_doi" value="<?php echo esc_attr($doi); ?>" />
                <p class="description">e.g., 10.1038/s41586-019-1716-z</p>
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pubmed_id"><?php _e('PubMed ID', 'microhub'); ?></label>
                <input type="text" id="mh_pubmed_id" name="mh_pubmed_id" value="<?php echo esc_attr($pubmed_id); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pmc_id"><?php _e('PMC ID', 'microhub'); ?></label>
                <input type="text" id="mh_pmc_id" name="mh_pmc_id" value="<?php echo esc_attr($pmc_id); ?>" />
                <p class="description">For open access full text (e.g., PMC1234567)</p>
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_journal"><?php _e('Journal', 'microhub'); ?></label>
                <input type="text" id="mh_journal" name="mh_journal" value="<?php echo esc_attr($journal); ?>" />
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_authors"><?php _e('Authors', 'microhub'); ?></label>
                <input type="text" id="mh_authors" name="mh_authors" value="<?php echo esc_attr($authors); ?>" />
                <p class="description">Comma-separated list of authors</p>
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_publication_year"><?php _e('Publication Year', 'microhub'); ?></label>
                <input type="number" id="mh_publication_year" name="mh_publication_year" value="<?php echo esc_attr($publication_year); ?>" min="1900" max="2100" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_citation_count"><?php _e('Citation Count', 'microhub'); ?></label>
                <input type="number" id="mh_citation_count" name="mh_citation_count" value="<?php echo esc_attr($citation_count); ?>" min="0" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_priority_score"><?php _e('Priority Score', 'microhub'); ?></label>
                <input type="number" id="mh_priority_score" name="mh_priority_score" value="<?php echo esc_attr($priority_score); ?>" min="0" />
                <p class="description">Auto-calculated based on enrichment</p>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_abstract"><?php _e('Abstract', 'microhub'); ?></label>
                <textarea id="mh_abstract" name="mh_abstract" rows="6"><?php echo esc_textarea($abstract); ?></textarea>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_methods"><?php _e('Methods Section', 'microhub'); ?></label>
                <textarea id="mh_methods" name="mh_methods" rows="8"><?php echo esc_textarea($methods); ?></textarea>
                <p class="description">Full methods text extracted from the paper (if available)</p>
            </div>
        </div>
        
        <?php
    }
    
    /**
     * Render links meta box
     */
    public function render_links_meta_box($post) {
        $doi_url = get_post_meta($post->ID, '_mh_doi_url', true);
        $pubmed_url = get_post_meta($post->ID, '_mh_pubmed_url', true);
        $pmc_url = get_post_meta($post->ID, '_mh_pmc_url', true);
        $pdf_url = get_post_meta($post->ID, '_mh_pdf_url', true);
        $github_url = get_post_meta($post->ID, '_mh_github_url', true);
        $facility = get_post_meta($post->ID, '_mh_facility', true);
        ?>
        
        <div class="mh-meta-grid">
            <div class="mh-meta-field">
                <label for="mh_doi_url"><?php _e('DOI URL', 'microhub'); ?></label>
                <input type="url" id="mh_doi_url" name="mh_doi_url" value="<?php echo esc_attr($doi_url); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pubmed_url"><?php _e('PubMed URL', 'microhub'); ?></label>
                <input type="url" id="mh_pubmed_url" name="mh_pubmed_url" value="<?php echo esc_attr($pubmed_url); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pmc_url"><?php _e('PMC URL (Full Text)', 'microhub'); ?></label>
                <input type="url" id="mh_pmc_url" name="mh_pmc_url" value="<?php echo esc_attr($pmc_url); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_pdf_url"><?php _e('PDF URL', 'microhub'); ?></label>
                <input type="url" id="mh_pdf_url" name="mh_pdf_url" value="<?php echo esc_attr($pdf_url); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_github_url"><?php _e('GitHub URL', 'microhub'); ?></label>
                <input type="url" id="mh_github_url" name="mh_github_url" value="<?php echo esc_attr($github_url); ?>" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_facility"><?php _e('Imaging Facility', 'microhub'); ?></label>
                <input type="text" id="mh_facility" name="mh_facility" value="<?php echo esc_attr($facility); ?>" />
            </div>
        </div>
        
        <?php
    }
    
    /**
     * Render resources meta box (protocols, repositories, RRIDs)
     */
    public function render_resources_meta_box($post) {
        $protocols = get_post_meta($post->ID, '_mh_protocols', true);
        $repositories = get_post_meta($post->ID, '_mh_repositories', true);
        $rrids = get_post_meta($post->ID, '_mh_rrids', true);
        $supplementary = get_post_meta($post->ID, '_mh_supplementary_materials', true);
        ?>
        
        <div class="mh-meta-grid">
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_protocols"><?php _e('Protocols (JSON)', 'microhub'); ?></label>
                <textarea id="mh_protocols" name="mh_protocols" rows="4"><?php echo esc_textarea($protocols); ?></textarea>
                <p class="description">JSON array of protocol objects with 'source' and 'url' keys</p>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_repositories"><?php _e('Data Repositories (JSON)', 'microhub'); ?></label>
                <textarea id="mh_repositories" name="mh_repositories" rows="4"><?php echo esc_textarea($repositories); ?></textarea>
                <p class="description">JSON array of repository objects with 'name' and 'url' keys</p>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_rrids"><?php _e('RRIDs (JSON)', 'microhub'); ?></label>
                <textarea id="mh_rrids" name="mh_rrids" rows="4"><?php echo esc_textarea($rrids); ?></textarea>
                <p class="description">JSON array of RRID objects with 'id', 'type', and 'url' keys</p>
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_supplementary_materials"><?php _e('Supplementary Materials (JSON)', 'microhub'); ?></label>
                <textarea id="mh_supplementary_materials" name="mh_supplementary_materials" rows="3"><?php echo esc_textarea($supplementary); ?></textarea>
            </div>
        </div>
        
        <?php
    }
    
    /**
     * Render figures meta box
     */
    public function render_figures_meta_box($post) {
        $figures = get_post_meta($post->ID, '_mh_figures', true);
        $figure_count = get_post_meta($post->ID, '_mh_figure_count', true);
        $thumbnail_url = get_post_meta($post->ID, '_mh_thumbnail_url', true);
        ?>
        
        <div class="mh-meta-grid">
            <div class="mh-meta-field">
                <label for="mh_figure_count"><?php _e('Figure Count', 'microhub'); ?></label>
                <input type="number" id="mh_figure_count" name="mh_figure_count" value="<?php echo esc_attr($figure_count); ?>" min="0" />
            </div>
            
            <div class="mh-meta-field">
                <label for="mh_thumbnail_url"><?php _e('Thumbnail URL', 'microhub'); ?></label>
                <input type="url" id="mh_thumbnail_url" name="mh_thumbnail_url" value="<?php echo esc_attr($thumbnail_url); ?>" />
            </div>
            
            <div class="mh-meta-field mh-meta-full">
                <label for="mh_figures"><?php _e('Figures (JSON)', 'microhub'); ?></label>
                <textarea id="mh_figures" name="mh_figures" rows="6"><?php echo esc_textarea($figures); ?></textarea>
                <p class="description">JSON array of figure objects with 'image_url', 'label', 'title', and 'caption' keys</p>
            </div>
        </div>
        
        <?php
        // Preview figures if available
        if ($figures) {
            $figures_array = json_decode($figures, true);
            if (!empty($figures_array) && is_array($figures_array)) {
                echo '<div style="margin-top: 15px;"><strong>Figure Preview:</strong></div>';
                echo '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px;">';
                foreach (array_slice($figures_array, 0, 4) as $fig) {
                    if (!empty($fig['image_url'])) {
                        echo '<div style="width: 100px; height: 100px; overflow: hidden; border-radius: 4px; background: #f0f0f0;">';
                        echo '<img src="' . esc_url($fig['image_url']) . '" style="width: 100%; height: 100%; object-fit: cover;" loading="lazy" />';
                        echo '</div>';
                    }
                }
                echo '</div>';
            }
        }
    }
    
    /**
     * Render status sidebar meta box
     */
    public function render_status_meta_box($post) {
        $has_full_text = get_post_meta($post->ID, '_mh_has_full_text', true);
        $has_figures = get_post_meta($post->ID, '_mh_has_figures', true);
        $has_protocols = get_post_meta($post->ID, '_mh_has_protocols', true);
        $has_github = get_post_meta($post->ID, '_mh_has_github', true);
        $has_data = get_post_meta($post->ID, '_mh_has_data', true);
        ?>
        
        <style>
            .mh-status-item { padding: 8px 0; border-bottom: 1px solid #eee; }
            .mh-status-item:last-child { border-bottom: none; }
            .mh-status-yes { color: #46b450; }
            .mh-status-no { color: #dc3232; }
        </style>
        
        <div class="mh-status-list">
            <div class="mh-status-item">
                <label>
                    <input type="checkbox" name="mh_has_full_text" value="1" <?php checked($has_full_text, 1); ?> />
                    <?php _e('Has Full Text', 'microhub'); ?>
                </label>
            </div>
            
            <div class="mh-status-item">
                <label>
                    <input type="checkbox" name="mh_has_figures" value="1" <?php checked($has_figures, 1); ?> />
                    <?php _e('Has Figures', 'microhub'); ?>
                </label>
            </div>
            
            <div class="mh-status-item">
                <label>
                    <input type="checkbox" name="mh_has_protocols" value="1" <?php checked($has_protocols, 1); ?> />
                    <?php _e('Has Protocols', 'microhub'); ?>
                </label>
            </div>
            
            <div class="mh-status-item">
                <label>
                    <input type="checkbox" name="mh_has_github" value="1" <?php checked($has_github, 1); ?> />
                    <?php _e('Has GitHub', 'microhub'); ?>
                </label>
            </div>
            
            <div class="mh-status-item">
                <label>
                    <input type="checkbox" name="mh_has_data" value="1" <?php checked($has_data, 1); ?> />
                    <?php _e('Has Data Repository', 'microhub'); ?>
                </label>
            </div>
        </div>
        
        <?php
    }
    
    /**
     * Save meta box data
     */
    public function save_meta_boxes($post_id) {
        // Check nonce
        if (!isset($_POST['microhub_meta_box_nonce'])) {
            return;
        }
        
        if (!wp_verify_nonce($_POST['microhub_meta_box_nonce'], 'microhub_save_meta_box_data')) {
            return;
        }
        
        // Check autosave
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
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
            'mh_facility' => '_mh_facility',
        );
        
        foreach ($text_fields as $field_name => $meta_key) {
            if (isset($_POST[$field_name])) {
                update_post_meta($post_id, $meta_key, sanitize_text_field($_POST[$field_name]));
            }
        }
        
        // Number fields
        $number_fields = array(
            'mh_publication_year' => '_mh_publication_year',
            'mh_citation_count' => '_mh_citation_count',
            'mh_priority_score' => '_mh_priority_score',
            'mh_figure_count' => '_mh_figure_count',
        );
        
        foreach ($number_fields as $field_name => $meta_key) {
            if (isset($_POST[$field_name])) {
                update_post_meta($post_id, $meta_key, intval($_POST[$field_name]));
            }
        }
        
        // URL fields
        $url_fields = array(
            'mh_doi_url' => '_mh_doi_url',
            'mh_pubmed_url' => '_mh_pubmed_url',
            'mh_pmc_url' => '_mh_pmc_url',
            'mh_pdf_url' => '_mh_pdf_url',
            'mh_github_url' => '_mh_github_url',
            'mh_thumbnail_url' => '_mh_thumbnail_url',
        );
        
        foreach ($url_fields as $field_name => $meta_key) {
            if (isset($_POST[$field_name])) {
                update_post_meta($post_id, $meta_key, esc_url_raw($_POST[$field_name]));
            }
        }
        
        // Textarea fields
        $textarea_fields = array(
            'mh_abstract' => '_mh_abstract',
            'mh_methods' => '_mh_methods',
            'mh_protocols' => '_mh_protocols',
            'mh_repositories' => '_mh_repositories',
            'mh_rrids' => '_mh_rrids',
            'mh_figures' => '_mh_figures',
            'mh_supplementary_materials' => '_mh_supplementary_materials',
        );
        
        foreach ($textarea_fields as $field_name => $meta_key) {
            if (isset($_POST[$field_name])) {
                // For JSON fields, validate JSON
                if (in_array($field_name, array('mh_protocols', 'mh_repositories', 'mh_rrids', 'mh_figures', 'mh_supplementary_materials'))) {
                    $value = sanitize_textarea_field($_POST[$field_name]);
                    // Validate JSON
                    if (!empty($value)) {
                        $decoded = json_decode($value);
                        if (json_last_error() === JSON_ERROR_NONE) {
                            update_post_meta($post_id, $meta_key, $value);
                        }
                    } else {
                        update_post_meta($post_id, $meta_key, '');
                    }
                } else {
                    update_post_meta($post_id, $meta_key, sanitize_textarea_field($_POST[$field_name]));
                }
            }
        }
        
        // Checkbox fields
        $checkbox_fields = array(
            'mh_has_full_text' => '_mh_has_full_text',
            'mh_has_figures' => '_mh_has_figures',
            'mh_has_protocols' => '_mh_has_protocols',
            'mh_has_github' => '_mh_has_github',
            'mh_has_data' => '_mh_has_data',
        );
        
        foreach ($checkbox_fields as $field_name => $meta_key) {
            $value = isset($_POST[$field_name]) ? 1 : 0;
            update_post_meta($post_id, $meta_key, $value);
        }
    }
}
