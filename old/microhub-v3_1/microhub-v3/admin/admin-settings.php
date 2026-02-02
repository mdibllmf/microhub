<?php
/**
 * MicroHub Admin Settings
 */

if (!defined('ABSPATH')) {
    exit;
}

// Add admin menu
add_action('admin_menu', 'microhub_add_admin_menu');

function microhub_add_admin_menu() {
    add_menu_page(
        __('MicroHub', 'microhub'),
        __('MicroHub', 'microhub'),
        'manage_options',
        'microhub-settings',
        'microhub_settings_page',
        'dashicons-microscope',
        30
    );
    
    add_submenu_page(
        'microhub-settings',
        __('Settings', 'microhub'),
        __('Settings', 'microhub'),
        'manage_options',
        'microhub-settings',
        'microhub_settings_page'
    );
}

function microhub_settings_page() {
    global $wpdb;
    
    // Handle delete all papers
    if (isset($_POST['microhub_delete_all_papers']) && check_admin_referer('microhub_delete_papers_nonce')) {
        $confirm = isset($_POST['confirm_delete']) && $_POST['confirm_delete'] === 'DELETE';
        if ($confirm) {
            $paper_ids = get_posts(array(
                'post_type' => 'mh_paper',
                'posts_per_page' => -1,
                'fields' => 'ids',
                'post_status' => 'any',
            ));
            
            $deleted = 0;
            foreach ($paper_ids as $id) {
                wp_delete_post($id, true);
                $deleted++;
            }
            
            echo '<div class="notice notice-success"><p>' . sprintf(__('Deleted %d papers.', 'microhub'), $deleted) . '</p></div>';
        }
    }
    
    // Get stats
    $total_papers = wp_count_posts('mh_paper')->publish;
    $total_protocols = wp_count_posts('mh_protocol')->publish;
    
    $with_full_text = $wpdb->get_var(
        "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_has_full_text' AND meta_value = '1'"
    );
    
    $with_figures = $wpdb->get_var(
        "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_has_figures' AND meta_value = '1'"
    );
    
    $with_protocols = $wpdb->get_var(
        "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_has_protocols' AND meta_value = '1'"
    );
    
    $with_github = $wpdb->get_var(
        "SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''"
    );
    ?>
    <div class="wrap">
        <h1><?php _e('MicroHub Settings', 'microhub'); ?></h1>
        
        <div class="card" style="max-width: 600px; padding: 20px;">
            <h2><?php _e('Database Statistics', 'microhub'); ?></h2>
            <table class="widefat" style="max-width: 400px;">
                <tr><td>Total Papers:</td><td><strong><?php echo number_format($total_papers); ?></strong></td></tr>
                <tr><td>Total Protocols:</td><td><strong><?php echo number_format($total_protocols); ?></strong></td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td>With Full Text:</td><td><?php echo number_format($with_full_text); ?></td></tr>
                <tr><td>With Figures:</td><td><?php echo number_format($with_figures); ?></td></tr>
                <tr><td>With Protocols:</td><td><?php echo number_format($with_protocols); ?></td></tr>
                <tr><td>With GitHub:</td><td><?php echo number_format($with_github); ?></td></tr>
            </table>
        </div>
        
        <div class="card" style="max-width: 600px; padding: 20px; margin-top: 20px;">
            <h2><?php _e('Taxonomy Statistics', 'microhub'); ?></h2>
            <table class="widefat" style="max-width: 400px;">
                <tr><td>Techniques:</td><td><?php echo wp_count_terms('mh_technique'); ?></td></tr>
                <tr><td>Microscope Brands:</td><td><?php echo wp_count_terms('mh_microscope_brand'); ?></td></tr>
                <tr><td>Analysis Software:</td><td><?php echo wp_count_terms('mh_analysis_software'); ?></td></tr>
                <tr><td>Organisms:</td><td><?php echo wp_count_terms('mh_organism'); ?></td></tr>
                <tr><td>Journals:</td><td><?php echo wp_count_terms('mh_journal'); ?></td></tr>
            </table>
        </div>
        
        <div class="card" style="max-width: 600px; padding: 20px; margin-top: 20px; border-color: #dc3545;">
            <h2 style="color: #dc3545;"><?php _e('Danger Zone', 'microhub'); ?></h2>
            <p><?php _e('Delete all papers from the database. This action cannot be undone.', 'microhub'); ?></p>
            <form method="post">
                <?php wp_nonce_field('microhub_delete_papers_nonce'); ?>
                <p>
                    <label for="confirm_delete">
                        <?php _e('Type DELETE to confirm:', 'microhub'); ?>
                    </label>
                    <input type="text" name="confirm_delete" id="confirm_delete" style="width: 100px;" />
                </p>
                <input type="submit" name="microhub_delete_all_papers" class="button button-secondary" 
                       value="<?php _e('Delete All Papers', 'microhub'); ?>" 
                       onclick="return confirm('Are you sure you want to delete ALL papers?');" />
            </form>
        </div>
    </div>
    <?php
}
