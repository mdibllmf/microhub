<!-- Submit Paper Form Template -->
<div class="microhub-submit-form">
    <h2><?php _e('Submit a Paper', 'microhub'); ?></h2>
    
    <?php
    // Handle form submission - check for POST request
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['submit_nonce']) && wp_verify_nonce($_POST['submit_nonce'], 'microhub_submit_paper')) {
        $title = sanitize_text_field($_POST['paper_title']);
        $doi = sanitize_text_field($_POST['paper_doi']);
        $authors = sanitize_text_field($_POST['paper_authors']);
        $abstract = sanitize_textarea_field($_POST['paper_abstract']);
        
        // Create paper as pending
        $post_id = wp_insert_post(array(
            'post_type' => 'mh_paper',
            'post_title' => $title,
            'post_status' => 'pending',
            'post_author' => get_current_user_id(),
        ));
        
        if ($post_id && !is_wp_error($post_id)) {
            // Save metadata
            update_post_meta($post_id, '_mh_doi', $doi);
            update_post_meta($post_id, '_mh_authors', $authors);
            update_post_meta($post_id, '_mh_abstract', $abstract);
            
            // Set techniques
            if (!empty($_POST['paper_techniques'])) {
                wp_set_object_terms($post_id, array_map('intval', $_POST['paper_techniques']), 'mh_technique');
            }
            
            echo '<div class="success-message">' . __('Thank you! Your paper has been submitted and is pending review.', 'microhub') . '</div>';
        } else {
            echo '<div class="error-message">' . __('Sorry, there was an error submitting your paper. Please try again.', 'microhub') . '</div>';
        }
    }
    ?>
    
    <form id="microhub-paper-submit" method="post">
        <?php wp_nonce_field('microhub_submit_paper', 'submit_nonce'); ?>
        
        <div class="form-field">
            <label for="paper_title"><?php _e('Paper Title *', 'microhub'); ?></label>
            <input type="text" id="paper_title" name="paper_title" required />
        </div>
        
        <div class="form-field">
            <label for="paper_doi"><?php _e('DOI *', 'microhub'); ?></label>
            <input type="text" id="paper_doi" name="paper_doi" required placeholder="10.1038/..." />
            <p class="description"><?php _e('Digital Object Identifier', 'microhub'); ?></p>
        </div>
        
        <div class="form-field">
            <label for="paper_authors"><?php _e('Authors', 'microhub'); ?></label>
            <input type="text" id="paper_authors" name="paper_authors" placeholder="Smith J, Doe J" />
        </div>
        
        <div class="form-field">
            <label for="paper_abstract"><?php _e('Abstract', 'microhub'); ?></label>
            <textarea id="paper_abstract" name="paper_abstract"></textarea>
        </div>
        
        <div class="form-field">
            <label for="paper_techniques"><?php _e('Techniques', 'microhub'); ?></label>
            <select id="paper_techniques" name="paper_techniques[]" multiple>
                <?php
                $techniques = get_terms(array('taxonomy' => 'mh_technique', 'hide_empty' => false));
                foreach ($techniques as $term) {
                    echo '<option value="' . esc_attr($term->term_id) . '">' . esc_html($term->name) . '</option>';
                }
                ?>
            </select>
            <p class="description"><?php _e('Hold Ctrl/Cmd to select multiple', 'microhub'); ?></p>
        </div>
        
        <div class="form-field">
            <button type="submit"><?php _e('Submit Paper', 'microhub'); ?></button>
        </div>
        
        <p class="info-message">
            <?php _e('Your submission will be reviewed by our team before being published.', 'microhub'); ?>
        </p>
    </form>
</div>

<?php
// Handle form submission
if (isset($_POST['submit_nonce']) && wp_verify_nonce($_POST['submit_nonce'], 'microhub_submit_paper')) {
    $title = sanitize_text_field($_POST['paper_title']);
    $doi = sanitize_text_field($_POST['paper_doi']);
    $authors = sanitize_text_field($_POST['paper_authors']);
    $abstract = sanitize_textarea_field($_POST['paper_abstract']);
    
    // Create paper as pending
    $post_id = wp_insert_post(array(
        'post_type' => 'mh_paper',
        'post_title' => $title,
        'post_status' => 'pending',
        'post_author' => get_current_user_id(),
    ));
    
    if ($post_id && !is_wp_error($post_id)) {
        // Save metadata
        update_post_meta($post_id, '_mh_doi', $doi);
        update_post_meta($post_id, '_mh_authors', $authors);
        update_post_meta($post_id, '_mh_abstract', $abstract);
        
        // Set techniques
        if (!empty($_POST['paper_techniques'])) {
            wp_set_object_terms($post_id, array_map('intval', $_POST['paper_techniques']), 'mh_technique');
        }
        
        echo '<div class="success-message">' . __('Thank you! Your paper has been submitted and is pending review.', 'microhub') . '</div>';
    } else {
        echo '<div class="error-message">' . __('Sorry, there was an error submitting your paper. Please try again.', 'microhub') . '</div>';
    }
}
?>
