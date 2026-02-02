<?php
/**
 * MicroHub Admin Review Interface
 * Provides easy paper review, editing, and bulk management
 */

// Add review submenu
add_action('admin_menu', 'microhub_add_review_menu');

function microhub_add_review_menu() {
    add_submenu_page(
        'microhub-settings',
        __('Review Papers', 'microhub'),
        __('Review Papers', 'microhub'),
        'manage_options',
        'microhub-review',
        'microhub_review_page'
    );
    
    add_submenu_page(
        'microhub-settings',
        __('Bulk Edit', 'microhub'),
        __('Bulk Edit', 'microhub'),
        'manage_options',
        'microhub-bulk-edit',
        'microhub_bulk_edit_page'
    );
}

/**
 * Main Review Page
 */
function microhub_review_page() {
    // Handle actions
    if (isset($_POST['microhub_save_paper']) && check_admin_referer('microhub_edit_paper')) {
        microhub_save_paper_edits();
    }
    
    $paged = isset($_GET['paged']) ? max(1, intval($_GET['paged'])) : 1;
    $per_page = 20;
    $filter = isset($_GET['filter']) ? sanitize_text_field($_GET['filter']) : '';
    $search = isset($_GET['s']) ? sanitize_text_field($_GET['s']) : '';
    
    // Build query
    $args = array(
        'post_type' => 'mh_paper',
        'posts_per_page' => $per_page,
        'paged' => $paged,
        'post_status' => 'any',
    );
    
    if ($search) {
        $args['s'] = $search;
    }
    
    // Apply filters
    if ($filter === 'no_techniques') {
        $args['tax_query'] = array(
            array(
                'taxonomy' => 'mh_technique',
                'operator' => 'NOT EXISTS',
            ),
        );
    } elseif ($filter === 'no_software') {
        $args['tax_query'] = array(
            array(
                'taxonomy' => 'mh_software',
                'operator' => 'NOT EXISTS',
            ),
        );
    } elseif ($filter === 'no_organisms') {
        $args['tax_query'] = array(
            array(
                'taxonomy' => 'mh_organism',
                'operator' => 'NOT EXISTS',
            ),
        );
    } elseif ($filter === 'no_microscope') {
        $args['tax_query'] = array(
            array(
                'taxonomy' => 'mh_microscope',
                'operator' => 'NOT EXISTS',
            ),
        );
    } elseif ($filter === 'needs_review') {
        $args['meta_query'] = array(
            array(
                'key' => '_mh_needs_review',
                'value' => '1',
            ),
        );
    }
    
    $query = new WP_Query($args);
    ?>
    
    <div class="wrap microhub-review-page">
        <h1><?php _e('Review Papers', 'microhub'); ?></h1>
        
        <style>
            .microhub-review-page { max-width: 1400px; }
            .mh-review-filters { background: #fff; padding: 15px; margin: 20px 0; border: 1px solid #ccd0d4; border-radius: 4px; }
            .mh-review-filters form { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
            .mh-filter-group { display: flex; gap: 8px; }
            .mh-filter-btn { text-decoration: none; padding: 6px 12px; background: #f0f0f1; border-radius: 4px; color: #50575e; }
            .mh-filter-btn.active, .mh-filter-btn:hover { background: #2271b1; color: #fff; }
            .mh-paper-card { background: #fff; border: 1px solid #ccd0d4; border-radius: 4px; margin: 15px 0; padding: 20px; }
            .mh-paper-card.needs-review { border-left: 4px solid #dba617; }
            .mh-paper-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }
            .mh-paper-title { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
            .mh-paper-title a { color: #1d2327; text-decoration: none; }
            .mh-paper-title a:hover { color: #2271b1; }
            .mh-paper-actions { display: flex; gap: 8px; }
            .mh-paper-meta { color: #646970; font-size: 13px; margin-bottom: 10px; }
            .mh-paper-tags { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
            .mh-tag { display: inline-block; padding: 3px 10px; border-radius: 3px; font-size: 12px; }
            .mh-tag.technique { background: rgba(34, 113, 177, 0.1); color: #2271b1; }
            .mh-tag.software { background: rgba(255, 166, 87, 0.15); color: #b36200; }
            .mh-tag.organism { background: rgba(63, 185, 80, 0.15); color: #1a7f37; }
            .mh-tag.microscope { background: rgba(163, 113, 247, 0.15); color: #7c3aed; }
            .mh-tag.empty { background: #fef3cd; color: #856404; font-style: italic; }
            .mh-edit-panel { background: #f6f7f7; padding: 15px; margin-top: 15px; border-radius: 4px; display: none; }
            .mh-edit-panel.active { display: block; }
            .mh-edit-row { display: grid; grid-template-columns: 150px 1fr; gap: 10px; margin-bottom: 12px; align-items: start; }
            .mh-edit-row label { font-weight: 500; padding-top: 5px; }
            .mh-edit-row input[type="text"], .mh-edit-row textarea { width: 100%; }
            .mh-edit-row textarea { min-height: 80px; }
            .mh-checkbox-group { display: flex; flex-wrap: wrap; gap: 10px; }
            .mh-checkbox-group label { font-weight: normal; display: flex; align-items: center; gap: 5px; }
            .mh-stats-bar { background: #f0f6fc; padding: 15px 20px; border-radius: 4px; margin-bottom: 20px; display: flex; gap: 30px; flex-wrap: wrap; }
            .mh-stat-item { text-align: center; }
            .mh-stat-value { font-size: 24px; font-weight: 600; color: #2271b1; }
            .mh-stat-label { font-size: 12px; color: #646970; }
        </style>
        
        <!-- Statistics Bar -->
        <div class="mh-stats-bar">
            <?php
            $total = wp_count_posts('mh_paper')->publish;
            $with_techniques = microhub_count_papers_with_taxonomy('mh_technique');
            $with_software = microhub_count_papers_with_taxonomy('mh_software');
            $with_organisms = microhub_count_papers_with_taxonomy('mh_organism');
            $with_microscopes = microhub_count_papers_with_taxonomy('mh_microscope');
            ?>
            <div class="mh-stat-item">
                <div class="mh-stat-value"><?php echo number_format($total); ?></div>
                <div class="mh-stat-label">Total Papers</div>
            </div>
            <div class="mh-stat-item">
                <div class="mh-stat-value"><?php echo number_format($with_techniques); ?></div>
                <div class="mh-stat-label">With Techniques</div>
            </div>
            <div class="mh-stat-item">
                <div class="mh-stat-value"><?php echo number_format($with_software); ?></div>
                <div class="mh-stat-label">With Software</div>
            </div>
            <div class="mh-stat-item">
                <div class="mh-stat-value"><?php echo number_format($with_organisms); ?></div>
                <div class="mh-stat-label">With Organisms</div>
            </div>
            <div class="mh-stat-item">
                <div class="mh-stat-value"><?php echo number_format($with_microscopes); ?></div>
                <div class="mh-stat-label">With Microscopes</div>
            </div>
        </div>
        
        <!-- Filters -->
        <div class="mh-review-filters">
            <form method="get">
                <input type="hidden" name="page" value="microhub-review" />
                
                <input type="search" name="s" value="<?php echo esc_attr($search); ?>" placeholder="Search papers..." class="regular-text" />
                
                <div class="mh-filter-group">
                    <a href="<?php echo admin_url('admin.php?page=microhub-review'); ?>" class="mh-filter-btn <?php echo !$filter ? 'active' : ''; ?>">All</a>
                    <a href="<?php echo admin_url('admin.php?page=microhub-review&filter=no_techniques'); ?>" class="mh-filter-btn <?php echo $filter === 'no_techniques' ? 'active' : ''; ?>">Missing Techniques</a>
                    <a href="<?php echo admin_url('admin.php?page=microhub-review&filter=no_software'); ?>" class="mh-filter-btn <?php echo $filter === 'no_software' ? 'active' : ''; ?>">Missing Software</a>
                    <a href="<?php echo admin_url('admin.php?page=microhub-review&filter=no_organisms'); ?>" class="mh-filter-btn <?php echo $filter === 'no_organisms' ? 'active' : ''; ?>">Missing Organisms</a>
                    <a href="<?php echo admin_url('admin.php?page=microhub-review&filter=no_microscope'); ?>" class="mh-filter-btn <?php echo $filter === 'no_microscope' ? 'active' : ''; ?>">Missing Microscope</a>
                </div>
                
                <input type="submit" class="button" value="Search" />
            </form>
        </div>
        
        <!-- Results -->
        <div class="mh-review-results">
            <p class="description">
                Showing <?php echo number_format($query->found_posts); ?> papers
                <?php if ($filter) : ?>
                    (filtered: <?php echo esc_html(str_replace('_', ' ', $filter)); ?>)
                <?php endif; ?>
            </p>
            
            <?php if ($query->have_posts()) : ?>
                <?php while ($query->have_posts()) : $query->the_post(); 
                    $post_id = get_the_ID();
                    $techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'names'));
                    $software = wp_get_post_terms($post_id, 'mh_software', array('fields' => 'names'));
                    $organisms = wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'names'));
                    $microscopes = wp_get_post_terms($post_id, 'mh_microscope', array('fields' => 'names'));
                    $needs_review = get_post_meta($post_id, '_mh_needs_review', true);
                    $doi = get_post_meta($post_id, '_mh_doi', true);
                    $journal = get_post_meta($post_id, '_mh_journal', true);
                    $year = get_post_meta($post_id, '_mh_publication_year', true);
                    $citations = get_post_meta($post_id, '_mh_citation_count', true);
                ?>
                
                <div class="mh-paper-card <?php echo $needs_review ? 'needs-review' : ''; ?>" id="paper-<?php echo $post_id; ?>">
                    <div class="mh-paper-header">
                        <h3 class="mh-paper-title">
                            <a href="<?php the_permalink(); ?>" target="_blank"><?php the_title(); ?></a>
                        </h3>
                        <div class="mh-paper-actions">
                            <a href="<?php echo get_edit_post_link(); ?>" class="button button-small">Full Edit</a>
                            <button type="button" class="button button-small mh-quick-edit-btn" data-id="<?php echo $post_id; ?>">Quick Edit</button>
                        </div>
                    </div>
                    
                    <div class="mh-paper-meta">
                        <?php if ($journal) : ?><strong><?php echo esc_html($journal); ?></strong> Â· <?php endif; ?>
                        <?php if ($year) : ?><?php echo esc_html($year); ?> Â· <?php endif; ?>
                        <?php if ($citations) : ?><?php echo number_format($citations); ?> citations Â· <?php endif; ?>
                        <?php if ($doi) : ?><a href="https://doi.org/<?php echo esc_attr($doi); ?>" target="_blank">DOI</a><?php endif; ?>
                    </div>
                    
                    <div class="mh-paper-tags">
                        <strong>Techniques:</strong>
                        <?php if ($techniques) : ?>
                            <?php foreach ($techniques as $t) : ?>
                                <span class="mh-tag technique"><?php echo esc_html($t); ?></span>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <span class="mh-tag empty">None tagged</span>
                        <?php endif; ?>
                    </div>
                    
                    <div class="mh-paper-tags">
                        <strong>Software:</strong>
                        <?php if ($software) : ?>
                            <?php foreach ($software as $s) : ?>
                                <span class="mh-tag software"><?php echo esc_html($s); ?></span>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <span class="mh-tag empty">None tagged</span>
                        <?php endif; ?>
                    </div>
                    
                    <div class="mh-paper-tags">
                        <strong>Organisms:</strong>
                        <?php if ($organisms) : ?>
                            <?php foreach ($organisms as $o) : ?>
                                <span class="mh-tag organism"><?php echo esc_html($o); ?></span>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <span class="mh-tag empty">None tagged</span>
                        <?php endif; ?>
                    </div>
                    
                    <div class="mh-paper-tags">
                        <strong>Microscopes:</strong>
                        <?php if ($microscopes) : ?>
                            <?php foreach ($microscopes as $m) : ?>
                                <span class="mh-tag microscope"><?php echo esc_html($m); ?></span>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <span class="mh-tag empty">None tagged</span>
                        <?php endif; ?>
                    </div>
                    
                    <!-- Quick Edit Panel -->
                    <div class="mh-edit-panel" id="edit-panel-<?php echo $post_id; ?>">
                        <form method="post" action="">
                            <?php wp_nonce_field('microhub_edit_paper'); ?>
                            <input type="hidden" name="paper_id" value="<?php echo $post_id; ?>" />
                            
                            <div class="mh-edit-row">
                                <label>Techniques</label>
                                <input type="text" name="techniques" value="<?php echo esc_attr(implode(', ', $techniques)); ?>" placeholder="Confocal, STED, Light Sheet..." />
                                <p class="description">Comma-separated list of techniques</p>
                            </div>
                            
                            <div class="mh-edit-row">
                                <label>Software</label>
                                <input type="text" name="software" value="<?php echo esc_attr(implode(', ', $software)); ?>" placeholder="ImageJ, Fiji, CellProfiler..." />
                            </div>
                            
                            <div class="mh-edit-row">
                                <label>Organisms</label>
                                <input type="text" name="organisms" value="<?php echo esc_attr(implode(', ', $organisms)); ?>" placeholder="Mouse, Human, Zebrafish..." />
                            </div>
                            
                            <div class="mh-edit-row">
                                <label>Microscopes</label>
                                <input type="text" name="microscopes" value="<?php echo esc_attr(implode(', ', $microscopes)); ?>" placeholder="Zeiss, Nikon, Leica..." />
                            </div>
                            
                            <div class="mh-edit-row">
                                <label></label>
                                <div>
                                    <button type="submit" name="microhub_save_paper" class="button button-primary">Save Changes</button>
                                    <button type="button" class="button mh-cancel-edit">Cancel</button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
                
                <?php endwhile; ?>
                
                <!-- Pagination -->
                <div class="tablenav bottom">
                    <div class="tablenav-pages">
                        <?php
                        $total_pages = $query->max_num_pages;
                        $base_url = admin_url('admin.php?page=microhub-review');
                        if ($filter) $base_url .= '&filter=' . $filter;
                        if ($search) $base_url .= '&s=' . urlencode($search);
                        
                        echo paginate_links(array(
                            'base' => $base_url . '%_%',
                            'format' => '&paged=%#%',
                            'current' => $paged,
                            'total' => $total_pages,
                            'prev_text' => '&laquo;',
                            'next_text' => '&raquo;',
                        ));
                        ?>
                    </div>
                </div>
                
            <?php else : ?>
                <p>No papers found matching your criteria.</p>
            <?php endif; ?>
            
            <?php wp_reset_postdata(); ?>
        </div>
        
        <script>
        jQuery(document).ready(function($) {
            // Toggle quick edit panel
            $('.mh-quick-edit-btn').on('click', function() {
                var id = $(this).data('id');
                $('#edit-panel-' + id).toggleClass('active');
            });
            
            // Cancel edit
            $('.mh-cancel-edit').on('click', function() {
                $(this).closest('.mh-edit-panel').removeClass('active');
            });
        });
        </script>
    </div>
    <?php
}

/**
 * Count papers with a specific taxonomy
 */
function microhub_count_papers_with_taxonomy($taxonomy) {
    global $wpdb;
    
    $count = $wpdb->get_var($wpdb->prepare("
        SELECT COUNT(DISTINCT p.ID) 
        FROM {$wpdb->posts} p
        INNER JOIN {$wpdb->term_relationships} tr ON p.ID = tr.object_id
        INNER JOIN {$wpdb->term_taxonomy} tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
        WHERE p.post_type = 'mh_paper' 
        AND p.post_status = 'publish'
        AND tt.taxonomy = %s
    ", $taxonomy));
    
    return intval($count);
}

/**
 * Save paper edits
 */
function microhub_save_paper_edits() {
    $post_id = intval($_POST['paper_id']);
    
    if (!$post_id || !current_user_can('edit_post', $post_id)) {
        return;
    }
    
    // Update techniques
    if (isset($_POST['techniques'])) {
        $techniques = array_map('trim', explode(',', sanitize_text_field($_POST['techniques'])));
        $techniques = array_filter($techniques);
        wp_set_object_terms($post_id, $techniques, 'mh_technique');
    }
    
    // Update software
    if (isset($_POST['software'])) {
        $software = array_map('trim', explode(',', sanitize_text_field($_POST['software'])));
        $software = array_filter($software);
        wp_set_object_terms($post_id, $software, 'mh_software');
    }
    
    // Update organisms
    if (isset($_POST['organisms'])) {
        $organisms = array_map('trim', explode(',', sanitize_text_field($_POST['organisms'])));
        $organisms = array_filter($organisms);
        wp_set_object_terms($post_id, $organisms, 'mh_organism');
    }
    
    // Update microscopes
    if (isset($_POST['microscopes'])) {
        $microscopes = array_map('trim', explode(',', sanitize_text_field($_POST['microscopes'])));
        $microscopes = array_filter($microscopes);
        wp_set_object_terms($post_id, $microscopes, 'mh_microscope');
    }
    
    // Clear needs review flag
    delete_post_meta($post_id, '_mh_needs_review');
    
    echo '<div class="notice notice-success"><p>Paper updated successfully!</p></div>';
}

/**
 * Bulk Edit Page
 */
function microhub_bulk_edit_page() {
    // Handle bulk actions
    if (isset($_POST['microhub_bulk_action']) && check_admin_referer('microhub_bulk_edit')) {
        microhub_process_bulk_action();
    }
    ?>
    
    <div class="wrap">
        <h1><?php _e('Bulk Edit Papers', 'microhub'); ?></h1>
        
        <style>
            .mh-bulk-section { background: #fff; border: 1px solid #ccd0d4; border-radius: 4px; padding: 20px; margin: 20px 0; }
            .mh-bulk-section h2 { margin-top: 0; }
            .mh-form-row { margin-bottom: 15px; }
            .mh-form-row label { display: block; font-weight: 500; margin-bottom: 5px; }
        </style>
        
        <!-- Add Terms to Multiple Papers -->
        <div class="mh-bulk-section">
            <h2>Add Tags to Papers by Search</h2>
            <p class="description">Add taxonomy terms to all papers matching a search query.</p>
            
            <form method="post">
                <?php wp_nonce_field('microhub_bulk_edit'); ?>
                <input type="hidden" name="bulk_action" value="add_terms" />
                
                <div class="mh-form-row">
                    <label>Search Query (matches title/abstract)</label>
                    <input type="text" name="search_query" class="large-text" placeholder="e.g., confocal microscopy" required />
                </div>
                
                <div class="mh-form-row">
                    <label>Taxonomy to Update</label>
                    <select name="taxonomy">
                        <option value="mh_technique">Techniques</option>
                        <option value="mh_software">Software</option>
                        <option value="mh_organism">Organisms</option>
                        <option value="mh_microscope">Microscopes</option>
                    </select>
                </div>
                
                <div class="mh-form-row">
                    <label>Terms to Add (comma-separated)</label>
                    <input type="text" name="terms" class="large-text" placeholder="e.g., Confocal, Live Cell" required />
                </div>
                
                <div class="mh-form-row">
                    <label>
                        <input type="checkbox" name="append" value="1" checked />
                        Append to existing terms (uncheck to replace)
                    </label>
                </div>
                
                <button type="submit" name="microhub_bulk_action" class="button button-primary">Preview Changes</button>
            </form>
        </div>
        
        <!-- Rename/Merge Terms -->
        <div class="mh-bulk-section">
            <h2>Rename or Merge Terms</h2>
            <p class="description">Rename a term or merge multiple terms into one.</p>
            
            <form method="post">
                <?php wp_nonce_field('microhub_bulk_edit'); ?>
                <input type="hidden" name="bulk_action" value="rename_term" />
                
                <div class="mh-form-row">
                    <label>Taxonomy</label>
                    <select name="taxonomy">
                        <option value="mh_technique">Techniques</option>
                        <option value="mh_software">Software</option>
                        <option value="mh_organism">Organisms</option>
                        <option value="mh_microscope">Microscopes</option>
                    </select>
                </div>
                
                <div class="mh-form-row">
                    <label>Old Term Name(s) - comma-separated for merging</label>
                    <input type="text" name="old_terms" class="large-text" placeholder="e.g., AFM, Atomic Force Microscopy" required />
                </div>
                
                <div class="mh-form-row">
                    <label>New Term Name</label>
                    <input type="text" name="new_term" class="regular-text" placeholder="e.g., AFM" required />
                </div>
                
                <button type="submit" name="microhub_bulk_action" class="button button-primary">Merge/Rename Terms</button>
            </form>
        </div>
        
        <!-- Current Terms Overview -->
        <div class="mh-bulk-section">
            <h2>Current Terms Overview</h2>
            
            <?php
            $taxonomies = array(
                'mh_technique' => 'Techniques',
                'mh_software' => 'Software',
                'mh_organism' => 'Organisms',
                'mh_microscope' => 'Microscopes',
            );
            
            foreach ($taxonomies as $tax_name => $tax_label) :
                $terms = get_terms(array('taxonomy' => $tax_name, 'hide_empty' => false, 'number' => 50, 'orderby' => 'count', 'order' => 'DESC'));
            ?>
                <h3><?php echo esc_html($tax_label); ?> (<?php echo count($terms); ?> terms)</h3>
                <p>
                    <?php foreach ($terms as $term) : ?>
                        <span style="display: inline-block; margin: 2px; padding: 2px 8px; background: #f0f0f1; border-radius: 3px; font-size: 12px;">
                            <?php echo esc_html($term->name); ?> (<?php echo $term->count; ?>)
                        </span>
                    <?php endforeach; ?>
                </p>
            <?php endforeach; ?>
        </div>
    </div>
    <?php
}

/**
 * Process bulk actions
 */
function microhub_process_bulk_action() {
    $action = sanitize_text_field($_POST['bulk_action']);
    
    if ($action === 'add_terms') {
        $search = sanitize_text_field($_POST['search_query']);
        $taxonomy = sanitize_key($_POST['taxonomy']);
        $terms = array_map('trim', explode(',', sanitize_text_field($_POST['terms'])));
        $append = isset($_POST['append']);
        
        // Find matching papers
        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => -1,
            's' => $search,
            'fields' => 'ids',
        );
        
        $paper_ids = get_posts($args);
        $count = count($paper_ids);
        
        if ($count > 0) {
            foreach ($paper_ids as $post_id) {
                wp_set_object_terms($post_id, $terms, $taxonomy, $append);
            }
            echo '<div class="notice notice-success"><p>Updated ' . $count . ' papers with terms: ' . esc_html(implode(', ', $terms)) . '</p></div>';
        } else {
            echo '<div class="notice notice-warning"><p>No papers found matching: ' . esc_html($search) . '</p></div>';
        }
        
    } elseif ($action === 'rename_term') {
        $taxonomy = sanitize_key($_POST['taxonomy']);
        $old_terms = array_map('trim', explode(',', sanitize_text_field($_POST['old_terms'])));
        $new_term = sanitize_text_field($_POST['new_term']);
        
        // Get or create new term
        $new_term_obj = term_exists($new_term, $taxonomy);
        if (!$new_term_obj) {
            $new_term_obj = wp_insert_term($new_term, $taxonomy);
        }
        
        if (is_wp_error($new_term_obj)) {
            echo '<div class="notice notice-error"><p>Error creating term: ' . $new_term_obj->get_error_message() . '</p></div>';
            return;
        }
        
        $new_term_id = is_array($new_term_obj) ? $new_term_obj['term_id'] : $new_term_obj;
        $total_moved = 0;
        
        foreach ($old_terms as $old_term_name) {
            $old_term = get_term_by('name', $old_term_name, $taxonomy);
            
            if ($old_term && $old_term->term_id != $new_term_id) {
                // Get all posts with old term
                $posts = get_posts(array(
                    'post_type' => 'mh_paper',
                    'posts_per_page' => -1,
                    'tax_query' => array(
                        array(
                            'taxonomy' => $taxonomy,
                            'field' => 'term_id',
                            'terms' => $old_term->term_id,
                        ),
                    ),
                    'fields' => 'ids',
                ));
                
                // Move posts to new term
                foreach ($posts as $post_id) {
                    wp_remove_object_terms($post_id, $old_term->term_id, $taxonomy);
                    wp_set_object_terms($post_id, array($new_term_id), $taxonomy, true);
                    $total_moved++;
                }
                
                // Delete old term
                wp_delete_term($old_term->term_id, $taxonomy);
            }
        }
        
        echo '<div class="notice notice-success"><p>Merged ' . count($old_terms) . ' terms into "' . esc_html($new_term) . '". Updated ' . $total_moved . ' papers.</p></div>';
    }
}
