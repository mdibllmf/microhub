<?php
/**
 * Admin settings page
 */

// Add admin menu
add_action('admin_menu', 'microhub_add_admin_menu');

function microhub_add_admin_menu() {
    add_menu_page(
        __('MicroHub Settings', 'microhub'),
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

/**
 * Settings page content
 */
function microhub_settings_page() {
    global $wpdb;
    
    // Handle delete all papers
    if (isset($_POST['microhub_delete_all_papers']) && check_admin_referer('microhub_delete_papers_nonce')) {
        $confirm = isset($_POST['confirm_delete']) && $_POST['confirm_delete'] === 'DELETE';
        if ($confirm) {
            // Get all paper IDs
            $paper_ids = get_posts(array(
                'post_type' => 'mh_paper',
                'posts_per_page' => -1,
                'fields' => 'ids',
                'post_status' => 'any',
            ));
            
            $deleted = 0;
            foreach ($paper_ids as $id) {
                wp_delete_post($id, true); // Force delete, skip trash
                $deleted++;
            }
            
            // Also clean up orphaned terms
            $wpdb->query("DELETE FROM {$wpdb->term_relationships} WHERE object_id NOT IN (SELECT ID FROM {$wpdb->posts})");
            
            echo '<div class="notice notice-success"><p><strong>' . sprintf(__('%d papers deleted successfully!', 'microhub'), $deleted) . '</strong></p></div>';
        } else {
            echo '<div class="notice notice-error"><p>' . __('Please type DELETE to confirm.', 'microhub') . '</p></div>';
        }
    }
    
    // Handle delete all taxonomies
    if (isset($_POST['microhub_reset_taxonomies']) && check_admin_referer('microhub_delete_papers_nonce')) {
        $taxonomies = array('mh_technique', 'mh_microscope', 'mh_organism', 'mh_software');
        foreach ($taxonomies as $tax) {
            $terms = get_terms(array('taxonomy' => $tax, 'hide_empty' => false, 'fields' => 'ids'));
            foreach ($terms as $term_id) {
                wp_delete_term($term_id, $tax);
            }
        }
        echo '<div class="notice notice-success"><p>' . __('All taxonomy terms deleted!', 'microhub') . '</p></div>';
    }
    
    // Save settings
    if (isset($_POST['microhub_save_settings']) && check_admin_referer('microhub_settings_nonce')) {
        update_option('microhub_enable_submissions', isset($_POST['enable_submissions']) ? 1 : 0);
        update_option('microhub_require_approval', isset($_POST['require_approval']) ? 1 : 0);
        update_option('microhub_papers_per_page', intval($_POST['papers_per_page']));
        
        // Save Gemini API key
        if (isset($_POST['gemini_api_key'])) {
            update_option('microhub_gemini_api_key', sanitize_text_field($_POST['gemini_api_key']));
        }
        
        echo '<div class="notice notice-success"><p>' . __('Settings saved successfully.', 'microhub') . '</p></div>';
    }
    
    $enable_submissions = get_option('microhub_enable_submissions', 1);
    $require_approval = get_option('microhub_require_approval', 1);
    $papers_per_page = get_option('microhub_papers_per_page', 20);
    $gemini_api_key = get_option('microhub_gemini_api_key', '');
    
    // Get enrichment counts
    $with_protocols = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != '' AND meta_value != '[]'");
    $with_github = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''");
    $with_repos = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_repositories' AND meta_value != '' AND meta_value != '[]'");
    $with_facility = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_facility' AND meta_value != ''");
    ?>
    
    <div class="wrap">
        <h1><?php _e('MicroHub Settings', 'microhub'); ?></h1>
        
        <form method="post" action="">
            <?php wp_nonce_field('microhub_settings_nonce'); ?>
            
            <h2><?php _e('AI Assistant (Gemini)', 'microhub'); ?></h2>
            <table class="form-table">
                <tr>
                    <th scope="row"><?php _e('Gemini API Key', 'microhub'); ?></th>
                    <td>
                        <input type="password" name="gemini_api_key" value="<?php echo esc_attr($gemini_api_key); ?>" class="regular-text" />
                        <p class="description">
                            <?php _e('Enter your FREE Google Gemini API key to enable the AI chat assistant.', 'microhub'); ?><br>
                            <strong><?php _e('Free tier: 1,500 requests/day - more than enough!', 'microhub'); ?></strong><br>
                            <a href="https://aistudio.google.com/app/apikey" target="_blank"><?php _e('Get your FREE API key here →', 'microhub'); ?></a>
                        </p>
                        <?php if ($gemini_api_key): ?>
                            <p><span class="dashicons dashicons-yes-alt" style="color: green;"></span> <?php _e('API key configured - AI chat is active!', 'microhub'); ?></p>
                        <?php else: ?>
                            <p><span class="dashicons dashicons-warning" style="color: orange;"></span> <?php _e('No API key - add one to enable AI chat', 'microhub'); ?></p>
                        <?php endif; ?>
                    </td>
                </tr>
            </table>
            
            <h2><?php _e('General Settings', 'microhub'); ?></h2>
            <table class="form-table">
                <tr>
                    <th scope="row"><?php _e('Enable User Submissions', 'microhub'); ?></th>
                    <td>
                        <label>
                            <input type="checkbox" name="enable_submissions" value="1" <?php checked($enable_submissions, 1); ?> />
                            <?php _e('Allow logged-in users to submit papers', 'microhub'); ?>
                        </label>
                    </td>
                </tr>
                
                <tr>
                    <th scope="row"><?php _e('Require Admin Approval', 'microhub'); ?></th>
                    <td>
                        <label>
                            <input type="checkbox" name="require_approval" value="1" <?php checked($require_approval, 1); ?> />
                            <?php _e('Submitted papers require admin approval before publishing', 'microhub'); ?>
                        </label>
                    </td>
                </tr>
                
                <tr>
                    <th scope="row"><?php _e('Papers Per Page', 'microhub'); ?></th>
                    <td>
                        <input type="number" name="papers_per_page" value="<?php echo esc_attr($papers_per_page); ?>" min="1" max="100" />
                        <p class="description"><?php _e('Number of papers to display per page in archives', 'microhub'); ?></p>
                    </td>
                </tr>
            </table>
            
            <p class="submit">
                <input type="submit" name="microhub_save_settings" class="button button-primary" value="<?php _e('Save Settings', 'microhub'); ?>" />
            </p>
        </form>
        
        <hr />
        
        <h2><?php _e('📄 MicroHub Pages', 'microhub'); ?></h2>
        <p><?php _e('MicroHub creates the following pages automatically. Click the button below to create any missing pages.', 'microhub'); ?></p>
        
        <?php
        // Handle page creation
        if (isset($_POST['microhub_create_pages']) && check_admin_referer('microhub_create_pages_nonce')) {
            require_once MICROHUB_PLUGIN_DIR . 'includes/class-microhub-activator.php';
            MicroHub_Activator::activate();
            echo '<div class="notice notice-success"><p>' . __('Pages created/updated successfully!', 'microhub') . '</p></div>';
        }
        
        $pages_info = array(
            'microhub' => array('title' => 'MicroHub (Main)', 'shortcode' => '[microhub_search_page]'),
            'about' => array('title' => 'About', 'shortcode' => '[microhub_about]'),
            'contact' => array('title' => 'Contact', 'shortcode' => '[microhub_contact]'),
            'discussions' => array('title' => 'Discussions', 'shortcode' => '[microhub_discussions]'),
            'upload-protocol' => array('title' => 'Upload Protocol', 'shortcode' => '[microhub_upload_protocol]'),
            'upload-paper' => array('title' => 'Submit Paper', 'shortcode' => '[microhub_upload_paper]'),
        );
        ?>
        
        <table class="widefat" style="max-width: 700px;">
            <thead>
                <tr>
                    <th><?php _e('Page', 'microhub'); ?></th>
                    <th><?php _e('Shortcode', 'microhub'); ?></th>
                    <th><?php _e('Status', 'microhub'); ?></th>
                    <th><?php _e('Link', 'microhub'); ?></th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($pages_info as $slug => $info) : 
                    $page = get_page_by_path($slug);
                    $exists = !empty($page);
                ?>
                <tr>
                    <td><strong><?php echo esc_html($info['title']); ?></strong></td>
                    <td><code><?php echo esc_html($info['shortcode']); ?></code></td>
                    <td>
                        <?php if ($exists) : ?>
                            <span style="color: green;">✅ <?php _e('Created', 'microhub'); ?></span>
                        <?php else : ?>
                            <span style="color: orange;">⚠️ <?php _e('Missing', 'microhub'); ?></span>
                        <?php endif; ?>
                    </td>
                    <td>
                        <?php if ($exists) : ?>
                            <a href="<?php echo get_permalink($page->ID); ?>" target="_blank"><?php _e('View', 'microhub'); ?> →</a>
                        <?php else : ?>
                            —
                        <?php endif; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        
        <form method="post" action="" style="margin-top: 15px;">
            <?php wp_nonce_field('microhub_create_pages_nonce'); ?>
            <input type="submit" name="microhub_create_pages" class="button button-secondary" value="<?php _e('Create Missing Pages', 'microhub'); ?>" />
        </form>
        
        <hr />
        
        <h2><?php _e('Repository Statistics', 'microhub'); ?></h2>
        
        <table class="widefat" style="max-width: 500px;">
            <tbody>
                <tr>
                    <td><strong><?php _e('Total Papers', 'microhub'); ?></strong></td>
                    <td><?php echo number_format(wp_count_posts('mh_paper')->publish); ?></td>
                </tr>
                <tr>
                    <td><strong><?php _e('With Protocols', 'microhub'); ?></strong></td>
                    <td><?php echo number_format($with_protocols); ?></td>
                </tr>
                <tr>
                    <td><strong><?php _e('With GitHub', 'microhub'); ?></strong></td>
                    <td><?php echo number_format($with_github); ?></td>
                </tr>
                <tr>
                    <td><strong><?php _e('With Data Repositories', 'microhub'); ?></strong></td>
                    <td><?php echo number_format($with_repos); ?></td>
                </tr>
                <tr>
                    <td><strong><?php _e('With Facilities', 'microhub'); ?></strong></td>
                    <td><?php echo number_format($with_facility); ?></td>
                </tr>
                <tr>
                    <td><strong><?php _e('Techniques', 'microhub'); ?></strong></td>
                    <td><?php echo number_format(wp_count_terms('mh_technique')); ?></td>
                </tr>
                <tr>
                    <td><strong><?php _e('Microscopes', 'microhub'); ?></strong></td>
                    <td><?php echo number_format(wp_count_terms('mh_microscope')); ?></td>
                </tr>
                <tr>
                    <td><strong><?php _e('Organisms', 'microhub'); ?></strong></td>
                    <td><?php echo number_format(wp_count_terms('mh_organism')); ?></td>
                </tr>
            </tbody>
        </table>
        
        <hr />
        
        <h2 style="color: #d63638;"><?php _e('⚠️ Data Management', 'microhub'); ?></h2>
        <p><?php _e('Use these options to reset your MicroHub data for a fresh start.', 'microhub'); ?></p>
        
        <form method="post" action="" style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; max-width: 500px; margin-bottom: 20px;">
            <?php wp_nonce_field('microhub_delete_papers_nonce'); ?>
            
            <h3 style="margin-top: 0; color: #d63638;">🗑️ Delete All Papers</h3>
            <p><?php _e('This will permanently delete ALL papers from your database. This action cannot be undone!', 'microhub'); ?></p>
            <p>
                <label>
                    <?php _e('Type DELETE to confirm:', 'microhub'); ?><br>
                    <input type="text" name="confirm_delete" placeholder="DELETE" style="margin-top: 5px;" />
                </label>
            </p>
            <p>
                <input type="submit" name="microhub_delete_all_papers" class="button" style="background: #d63638; border-color: #d63638; color: #fff;" value="<?php _e('Delete All Papers', 'microhub'); ?>" onclick="return confirm('Are you absolutely sure? This will delete ALL papers!');" />
            </p>
        </form>
        
        <form method="post" action="" style="background: #fff; border: 1px solid #c3c4c7; padding: 20px; max-width: 500px;">
            <?php wp_nonce_field('microhub_delete_papers_nonce'); ?>
            
            <h3 style="margin-top: 0; color: #dba617;">🏷️ Reset Taxonomy Terms</h3>
            <p><?php _e('Delete all technique, microscope, organism, and software terms. Papers will remain but lose their category assignments.', 'microhub'); ?></p>
            <p>
                <input type="submit" name="microhub_reset_taxonomies" class="button" style="background: #dba617; border-color: #dba617; color: #fff;" value="<?php _e('Reset All Terms', 'microhub'); ?>" onclick="return confirm('Delete all taxonomy terms?');" />
            </p>
        </form>
    </div>
    
    <?php
}
