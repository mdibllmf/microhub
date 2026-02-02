<?php
/**
 * Register meta boxes for paper metadata fields
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
        add_meta_box(
            'microhub_paper_details',
            __('Paper Details', 'microhub'),
            array($this, 'render_paper_details_meta_box'),
            'mh_paper',
            'normal',
            'high'
        );
    }
    
    /**
     * Render paper details meta box
     */
    public function render_paper_details_meta_box($post) {
        // Add nonce for security
        wp_nonce_field('microhub_save_meta_box_data', 'microhub_meta_box_nonce');
        
        // Get existing values
        $doi = get_post_meta($post->ID, '_mh_doi', true);
        $pubmed_id = get_post_meta($post->ID, '_mh_pubmed_id', true);
        $authors = get_post_meta($post->ID, '_mh_authors', true);
        $journal = get_post_meta($post->ID, '_mh_journal', true);
        $publication_year = get_post_meta($post->ID, '_mh_publication_year', true);
        $citation_count = get_post_meta($post->ID, '_mh_citation_count', true);
        $abstract = get_post_meta($post->ID, '_mh_abstract', true);
        $pdf_url = get_post_meta($post->ID, '_mh_pdf_url', true);
        $microscope_details = get_post_meta($post->ID, '_mh_microscope_details', true);
        ?>
        
        <table class="form-table">
            <tr>
                <th><label for="mh_doi"><?php _e('DOI', 'microhub'); ?></label></th>
                <td>
                    <input type="text" id="mh_doi" name="mh_doi" value="<?php echo esc_attr($doi); ?>" class="regular-text" />
                    <p class="description"><?php _e('Digital Object Identifier (e.g., 10.1038/s41586-019-1716-z)', 'microhub'); ?></p>
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_pubmed_id"><?php _e('PubMed ID', 'microhub'); ?></label></th>
                <td>
                    <input type="text" id="mh_pubmed_id" name="mh_pubmed_id" value="<?php echo esc_attr($pubmed_id); ?>" class="regular-text" />
                    <p class="description"><?php _e('PubMed identifier (e.g., 31748745)', 'microhub'); ?></p>
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_authors"><?php _e('Authors', 'microhub'); ?></label></th>
                <td>
                    <input type="text" id="mh_authors" name="mh_authors" value="<?php echo esc_attr($authors); ?>" class="large-text" />
                    <p class="description"><?php _e('Comma-separated list of authors', 'microhub'); ?></p>
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_journal"><?php _e('Journal', 'microhub'); ?></label></th>
                <td>
                    <input type="text" id="mh_journal" name="mh_journal" value="<?php echo esc_attr($journal); ?>" class="regular-text" />
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_publication_year"><?php _e('Publication Year', 'microhub'); ?></label></th>
                <td>
                    <input type="number" id="mh_publication_year" name="mh_publication_year" value="<?php echo esc_attr($publication_year); ?>" min="1900" max="2100" />
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_citation_count"><?php _e('Citation Count', 'microhub'); ?></label></th>
                <td>
                    <input type="number" id="mh_citation_count" name="mh_citation_count" value="<?php echo esc_attr($citation_count); ?>" min="0" />
                    <p class="description"><?php _e('Number of times this paper has been cited', 'microhub'); ?></p>
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_abstract"><?php _e('Abstract', 'microhub'); ?></label></th>
                <td>
                    <textarea id="mh_abstract" name="mh_abstract" rows="8" class="large-text"><?php echo esc_textarea($abstract); ?></textarea>
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_pdf_url"><?php _e('PDF URL', 'microhub'); ?></label></th>
                <td>
                    <input type="url" id="mh_pdf_url" name="mh_pdf_url" value="<?php echo esc_attr($pdf_url); ?>" class="large-text" />
                    <p class="description"><?php _e('Direct link to the paper PDF', 'microhub'); ?></p>
                </td>
            </tr>
            
            <tr>
                <th><label for="mh_microscope_details"><?php _e('Microscope Details', 'microhub'); ?></label></th>
                <td>
                    <textarea id="mh_microscope_details" name="mh_microscope_details" rows="4" class="large-text"><?php echo esc_textarea($microscope_details); ?></textarea>
                    <p class="description"><?php _e('Details about microscopes used in the study', 'microhub'); ?></p>
                </td>
            </tr>
        </table>
        
        <?php
    }
    
    /**
     * Save meta box data
     */
    public function save_meta_boxes($post_id) {
        // Check if nonce is set
        if (!isset($_POST['microhub_meta_box_nonce'])) {
            return;
        }
        
        // Verify nonce
        if (!wp_verify_nonce($_POST['microhub_meta_box_nonce'], 'microhub_save_meta_box_data')) {
            return;
        }
        
        // Check if autosave
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }
        
        // Check user permissions
        if (!current_user_can('edit_post', $post_id)) {
            return;
        }
        
        // Save meta fields
        $fields = array(
            'mh_doi' => '_mh_doi',
            'mh_pubmed_id' => '_mh_pubmed_id',
            'mh_authors' => '_mh_authors',
            'mh_journal' => '_mh_journal',
            'mh_publication_year' => '_mh_publication_year',
            'mh_citation_count' => '_mh_citation_count',
            'mh_abstract' => '_mh_abstract',
            'mh_pdf_url' => '_mh_pdf_url',
            'mh_microscope_details' => '_mh_microscope_details',
        );
        
        foreach ($fields as $field_name => $meta_key) {
            if (isset($_POST[$field_name])) {
                // Use appropriate sanitization based on field type
                if ($field_name === 'mh_abstract' || $field_name === 'mh_microscope_details') {
                    $value = sanitize_textarea_field($_POST[$field_name]);
                } else {
                    $value = sanitize_text_field($_POST[$field_name]);
                }
                update_post_meta($post_id, $meta_key, $value);
            }
        }
    }
}
