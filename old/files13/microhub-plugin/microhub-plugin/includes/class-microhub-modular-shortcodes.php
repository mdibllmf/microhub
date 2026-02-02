<?php
/**
 * MicroHub Modular Shortcodes
 * Separate shortcodes for each section to allow flexible template building
 * 
 * Available Shortcodes:
 * [microhub_hero] - Hero section with title, subtitle, and stats
 * [microhub_search_bar] - Search input field
 * [microhub_filters] - Filter dropdowns
 * [microhub_quick_filters] - Quick filter buttons
 * [microhub_results_grid] - Papers results grid
 * [microhub_pagination] - Pagination controls
 * [microhub_stats_bar] - Statistics display
 * [microhub_taxonomy_cloud] - Tag cloud for any taxonomy
 * [microhub_featured_papers] - Featured papers section
 * [microhub_recent_papers] - Recent papers list
 * [microhub_ai_chat] - AI chat widget
 * [microhub_upload_form] - Paper/protocol upload form
 */

class MicroHub_Modular_Shortcodes {
    
    public function init() {
        // Hero & Navigation
        add_shortcode('microhub_hero', array($this, 'hero_shortcode'));
        add_shortcode('microhub_navigation', array($this, 'navigation_shortcode'));
        
        // Search Components
        add_shortcode('microhub_search_bar', array($this, 'search_bar_shortcode'));
        add_shortcode('microhub_filters', array($this, 'filters_shortcode'));
        add_shortcode('microhub_quick_filters', array($this, 'quick_filters_shortcode'));
        
        // Results
        add_shortcode('microhub_results_grid', array($this, 'results_grid_shortcode'));
        add_shortcode('microhub_pagination', array($this, 'pagination_shortcode'));
        
        // Stats & Data
        add_shortcode('microhub_stats_bar', array($this, 'stats_bar_shortcode'));
        add_shortcode('microhub_stats_cards', array($this, 'stats_cards_shortcode'));
        add_shortcode('microhub_enrichment_stats', array($this, 'enrichment_stats_shortcode'));
        
        // Content Sections
        add_shortcode('microhub_taxonomy_cloud', array($this, 'taxonomy_cloud_shortcode'));
        add_shortcode('microhub_featured_papers', array($this, 'featured_papers_shortcode'));
        add_shortcode('microhub_recent_papers', array($this, 'recent_papers_shortcode'));
        add_shortcode('microhub_top_cited', array($this, 'top_cited_shortcode'));
        
        // Interactive
        add_shortcode('microhub_ai_chat', array($this, 'ai_chat_shortcode'));
        add_shortcode('microhub_upload_form', array($this, 'upload_form_shortcode'));
        
        // Wrapper
        add_shortcode('microhub_container', array($this, 'container_shortcode'));
    }
    
    /**
     * Container wrapper for MicroHub components
     */
    public function container_shortcode($atts, $content = null) {
        $atts = shortcode_atts(array(
            'class' => '',
            'id' => '',
        ), $atts);
        
        $id_attr = $atts['id'] ? ' id="' . esc_attr($atts['id']) . '"' : '';
        $classes = 'microhub-wrapper ' . esc_attr($atts['class']);
        
        return '<div class="' . $classes . '"' . $id_attr . '>' . do_shortcode($content) . '</div>';
    }
    
    /**
     * Hero Section
     * [microhub_hero title="..." subtitle="..." show_stats="yes" show_featured="yes"]
     */
    public function hero_shortcode($atts) {
        $atts = shortcode_atts(array(
            'title' => 'MicroHub',
            'subtitle' => 'Microscopy Research Repository',
            'show_stats' => 'yes',
            'show_featured' => 'no',
            'background' => '',
        ), $atts);
        
        $total_papers = wp_count_posts('mh_paper')->publish;
        $techniques_count = wp_count_terms('mh_technique');
        $microscopes_count = wp_count_terms('mh_microscope');
        $organisms_count = wp_count_terms('mh_organism');
        $software_count = wp_count_terms('mh_software');
        
        $style = $atts['background'] ? ' style="background-image: url(' . esc_url($atts['background']) . ');"' : '';
        
        ob_start();
        ?>
        <section class="mh-hero"<?php echo $style; ?>>
            <div class="mh-hero-inner">
                <div class="mh-hero-content">
                    <div class="mh-hero-text">
                        <h1><?php echo esc_html($atts['title']); ?></h1>
                        <p><?php echo esc_html($atts['subtitle']); ?></p>
                        
                        <?php if ($atts['show_stats'] === 'yes') : ?>
                        <div class="mh-hero-stats">
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($total_papers); ?></span>
                                <span class="mh-hero-stat-label">Papers</span>
                            </div>
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($techniques_count); ?></span>
                                <span class="mh-hero-stat-label">Techniques</span>
                            </div>
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($software_count); ?></span>
                                <span class="mh-hero-stat-label">Software</span>
                            </div>
                            <div class="mh-hero-stat">
                                <span class="mh-hero-stat-number"><?php echo number_format($organisms_count); ?></span>
                                <span class="mh-hero-stat-label">Organisms</span>
                            </div>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Navigation
     * [microhub_navigation]
     */
    public function navigation_shortcode($atts) {
        return microhub_render_navigation();
    }
    
    /**
     * Search Bar
     * [microhub_search_bar placeholder="..." button_text="..."]
     */
    public function search_bar_shortcode($atts) {
        $atts = shortcode_atts(array(
            'placeholder' => 'Search papers by title, author, technique, DOI...',
            'button_text' => 'Search',
            'show_button' => 'yes',
        ), $atts);
        
        ob_start();
        ?>
        <div class="mh-search-section">
            <div class="mh-search-box">
                <input type="text" 
                       id="mh-search-input" 
                       class="mh-search-input" 
                       placeholder="<?php echo esc_attr($atts['placeholder']); ?>" />
                <?php if ($atts['show_button'] === 'yes') : ?>
                <button type="button" id="mh-search-btn" class="mh-search-btn">
                    <?php echo esc_html($atts['button_text']); ?>
                </button>
                <?php endif; ?>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Filter Dropdowns
     * [microhub_filters show="technique,software,organism,microscope,year,citations"]
     */
    public function filters_shortcode($atts) {
        $atts = shortcode_atts(array(
            'show' => 'technique,software,organism,microscope,year,citations',
            'layout' => 'horizontal', // horizontal or vertical
        ), $atts);
        
        $filters = array_map('trim', explode(',', $atts['show']));
        $layout_class = $atts['layout'] === 'vertical' ? 'mh-filters-vertical' : 'mh-filters-horizontal';
        
        ob_start();
        ?>
        <div class="mh-filters-section <?php echo esc_attr($layout_class); ?>">
            <div class="mh-filters-grid">
                
                <?php if (in_array('technique', $filters)) : ?>
                <div class="mh-filter-item">
                    <label>Technique</label>
                    <select id="mh-filter-technique" data-filter="technique">
                        <option value="">All Techniques</option>
                        <?php echo $this->get_taxonomy_options('mh_technique'); ?>
                    </select>
                </div>
                <?php endif; ?>
                
                <?php if (in_array('software', $filters)) : ?>
                <div class="mh-filter-item">
                    <label>Software</label>
                    <select id="mh-filter-software" data-filter="software">
                        <option value="">All Software</option>
                        <?php echo $this->get_taxonomy_options('mh_software'); ?>
                    </select>
                </div>
                <?php endif; ?>
                
                <?php if (in_array('organism', $filters)) : ?>
                <div class="mh-filter-item">
                    <label>Organism</label>
                    <select id="mh-filter-organism" data-filter="organism">
                        <option value="">All Organisms</option>
                        <?php echo $this->get_taxonomy_options('mh_organism'); ?>
                    </select>
                </div>
                <?php endif; ?>
                
                <?php if (in_array('microscope', $filters)) : ?>
                <div class="mh-filter-item">
                    <label>Microscope</label>
                    <select id="mh-filter-microscope" data-filter="microscope">
                        <option value="">All Microscopes</option>
                        <?php echo $this->get_taxonomy_options('mh_microscope'); ?>
                    </select>
                </div>
                <?php endif; ?>
                
                <?php if (in_array('year', $filters)) : ?>
                <div class="mh-filter-item">
                    <label>Year</label>
                    <select id="mh-filter-year" data-filter="year">
                        <option value="">All Years</option>
                        <option value="2024-2025">2024-2025</option>
                        <option value="2020-2023">2020-2023</option>
                        <option value="2015-2019">2015-2019</option>
                        <option value="2010-2014">2010-2014</option>
                        <option value="before-2010">Before 2010</option>
                    </select>
                </div>
                <?php endif; ?>
                
                <?php if (in_array('citations', $filters)) : ?>
                <div class="mh-filter-item">
                    <label>Min Citations</label>
                    <select id="mh-filter-citations" data-filter="citations">
                        <option value="">Any</option>
                        <option value="100">100+ (Foundational)</option>
                        <option value="50">50+ (High Impact)</option>
                        <option value="25">25+</option>
                        <option value="10">10+</option>
                    </select>
                </div>
                <?php endif; ?>
                
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Quick Filter Buttons
     * [microhub_quick_filters show="foundational,high_impact,has_protocols,has_github,has_data"]
     */
    public function quick_filters_shortcode($atts) {
        $atts = shortcode_atts(array(
            'show' => 'foundational,high_impact,has_protocols,has_github,has_data',
            'show_clear' => 'yes',
        ), $atts);
        
        $filters = array_map('trim', explode(',', $atts['show']));
        
        ob_start();
        ?>
        <div class="mh-quick-filters">
            <span class="mh-quick-label">Quick filters:</span>
            
            <?php if (in_array('foundational', $filters)) : ?>
            <button type="button" class="mh-quick-btn" data-filter="foundational">🏆 Foundational Papers</button>
            <?php endif; ?>
            
            <?php if (in_array('high_impact', $filters)) : ?>
            <button type="button" class="mh-quick-btn" data-filter="high_impact">⭐ High Impact</button>
            <?php endif; ?>
            
            <?php if (in_array('has_protocols', $filters)) : ?>
            <button type="button" class="mh-quick-btn" data-filter="has_protocols">📋 Has Protocols <span class="mh-badge-count" id="count-protocols">-</span></button>
            <?php endif; ?>
            
            <?php if (in_array('has_github', $filters)) : ?>
            <button type="button" class="mh-quick-btn" data-filter="has_github">💻 GitHub <span class="mh-badge-count" id="count-github">-</span></button>
            <?php endif; ?>
            
            <?php if (in_array('has_data', $filters)) : ?>
            <button type="button" class="mh-quick-btn" data-filter="has_repositories">💾 Has Data <span class="mh-badge-count" id="count-repos">-</span></button>
            <?php endif; ?>
            
            <?php if ($atts['show_clear'] === 'yes') : ?>
            <span class="mh-clear-all" id="mh-clear-filters">✕ Clear all filters</span>
            <?php endif; ?>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Results Grid
     * [microhub_results_grid per_page="24" layout="grid"]
     */
    public function results_grid_shortcode($atts) {
        $atts = shortcode_atts(array(
            'per_page' => 24,
            'layout' => 'grid', // grid or list
            'id' => 'mh-papers-grid',
        ), $atts);
        
        ob_start();
        ?>
        <div class="mh-results-section">
            <div class="mh-results-header">
                <div class="mh-results-count">
                    <span id="mh-results-count">Loading...</span> papers
                </div>
                <div class="mh-results-sort">
                    <select id="mh-sort-select">
                        <option value="citations">Most Cited</option>
                        <option value="recent">Most Recent</option>
                        <option value="title">Title A-Z</option>
                    </select>
                </div>
            </div>
            <div id="<?php echo esc_attr($atts['id']); ?>" class="mh-papers-grid mh-layout-<?php echo esc_attr($atts['layout']); ?>" data-per-page="<?php echo intval($atts['per_page']); ?>">
                <div class="mh-loading">
                    <div class="mh-spinner"></div>
                    <p>Loading papers...</p>
                </div>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Pagination
     * [microhub_pagination]
     */
    public function pagination_shortcode($atts) {
        ob_start();
        ?>
        <div class="mh-pagination" id="mh-pagination">
            <!-- Populated by JavaScript -->
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Statistics Bar
     * [microhub_stats_bar layout="horizontal"]
     */
    public function stats_bar_shortcode($atts) {
        $atts = shortcode_atts(array(
            'layout' => 'horizontal', // horizontal or cards
            'show' => 'papers,techniques,software,organisms,microscopes',
        ), $atts);
        
        $stats = array(
            'papers' => array('value' => wp_count_posts('mh_paper')->publish, 'label' => 'Papers', 'icon' => '📄'),
            'techniques' => array('value' => wp_count_terms('mh_technique'), 'label' => 'Techniques', 'icon' => '🔬'),
            'software' => array('value' => wp_count_terms('mh_software'), 'label' => 'Software', 'icon' => '💻'),
            'organisms' => array('value' => wp_count_terms('mh_organism'), 'label' => 'Organisms', 'icon' => '🧬'),
            'microscopes' => array('value' => wp_count_terms('mh_microscope'), 'label' => 'Microscopes', 'icon' => '🔭'),
        );
        
        $show = array_map('trim', explode(',', $atts['show']));
        
        ob_start();
        ?>
        <div class="mh-stats-bar mh-stats-<?php echo esc_attr($atts['layout']); ?>">
            <?php foreach ($show as $key) : ?>
                <?php if (isset($stats[$key])) : $stat = $stats[$key]; ?>
                <div class="mh-stat-item">
                    <span class="mh-stat-icon"><?php echo $stat['icon']; ?></span>
                    <span class="mh-stat-value"><?php echo number_format($stat['value']); ?></span>
                    <span class="mh-stat-label"><?php echo esc_html($stat['label']); ?></span>
                </div>
                <?php endif; ?>
            <?php endforeach; ?>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Stats Cards
     * [microhub_stats_cards columns="4"]
     */
    public function stats_cards_shortcode($atts) {
        $atts = shortcode_atts(array(
            'columns' => '4',
        ), $atts);
        
        global $wpdb;
        
        $total = wp_count_posts('mh_paper')->publish;
        $protocols = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != '' AND meta_value != '[]'");
        $github = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''");
        $repos = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_repositories' AND meta_value != '' AND meta_value != '[]'");
        
        ob_start();
        ?>
        <div class="mh-stats-cards" style="display: grid; grid-template-columns: repeat(<?php echo intval($atts['columns']); ?>, 1fr); gap: 20px;">
            <div class="mh-stat-card">
                <div class="mh-stat-card-value"><?php echo number_format($total); ?></div>
                <div class="mh-stat-card-label">Total Papers</div>
            </div>
            <div class="mh-stat-card">
                <div class="mh-stat-card-value"><?php echo number_format($protocols); ?></div>
                <div class="mh-stat-card-label">With Protocols</div>
            </div>
            <div class="mh-stat-card">
                <div class="mh-stat-card-value"><?php echo number_format($github); ?></div>
                <div class="mh-stat-card-label">With GitHub</div>
            </div>
            <div class="mh-stat-card">
                <div class="mh-stat-card-value"><?php echo number_format($repos); ?></div>
                <div class="mh-stat-card-label">With Data Repos</div>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Enrichment Stats
     * [microhub_enrichment_stats]
     */
    public function enrichment_stats_shortcode($atts) {
        global $wpdb;
        
        $stats = array(
            'protocols' => $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != '' AND meta_value != '[]'"),
            'github' => $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''"),
            'repositories' => $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_repositories' AND meta_value != '' AND meta_value != '[]'"),
            'rrids' => $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_rrids' AND meta_value != '' AND meta_value != '[]'"),
        );
        
        ob_start();
        ?>
        <div class="mh-enrichment-stats">
            <h3>Data Enrichment</h3>
            <div class="mh-enrichment-grid">
                <div class="mh-enrichment-item">
                    <span class="mh-enrichment-icon">📋</span>
                    <span class="mh-enrichment-value"><?php echo number_format($stats['protocols']); ?></span>
                    <span class="mh-enrichment-label">Papers with Protocols</span>
                </div>
                <div class="mh-enrichment-item">
                    <span class="mh-enrichment-icon">💻</span>
                    <span class="mh-enrichment-value"><?php echo number_format($stats['github']); ?></span>
                    <span class="mh-enrichment-label">Papers with GitHub</span>
                </div>
                <div class="mh-enrichment-item">
                    <span class="mh-enrichment-icon">💾</span>
                    <span class="mh-enrichment-value"><?php echo number_format($stats['repositories']); ?></span>
                    <span class="mh-enrichment-label">Papers with Data Repos</span>
                </div>
                <div class="mh-enrichment-item">
                    <span class="mh-enrichment-icon">🏷️</span>
                    <span class="mh-enrichment-value"><?php echo number_format($stats['rrids']); ?></span>
                    <span class="mh-enrichment-label">Papers with RRIDs</span>
                </div>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Taxonomy Cloud
     * [microhub_taxonomy_cloud taxonomy="mh_technique" limit="30" show_count="yes"]
     */
    public function taxonomy_cloud_shortcode($atts) {
        $atts = shortcode_atts(array(
            'taxonomy' => 'mh_technique',
            'limit' => 30,
            'show_count' => 'yes',
            'title' => '',
            'orderby' => 'count', // count, name
            'link' => 'yes',
        ), $atts);
        
        $terms = get_terms(array(
            'taxonomy' => $atts['taxonomy'],
            'hide_empty' => true,
            'number' => intval($atts['limit']),
            'orderby' => $atts['orderby'],
            'order' => 'DESC',
        ));
        
        if (empty($terms) || is_wp_error($terms)) {
            return '';
        }
        
        // Get taxonomy label
        $tax_obj = get_taxonomy($atts['taxonomy']);
        $title = $atts['title'] ?: ($tax_obj ? $tax_obj->labels->name : '');
        
        // Determine tag class based on taxonomy
        $tag_class = str_replace('mh_', '', $atts['taxonomy']);
        
        ob_start();
        ?>
        <div class="mh-taxonomy-cloud">
            <?php if ($title) : ?>
            <h3><?php echo esc_html($title); ?></h3>
            <?php endif; ?>
            <div class="mh-cloud-tags">
                <?php foreach ($terms as $term) : ?>
                    <?php if ($atts['link'] === 'yes') : ?>
                    <a href="<?php echo esc_url(get_term_link($term)); ?>" class="mh-cloud-tag <?php echo esc_attr($tag_class); ?>">
                        <?php echo esc_html($term->name); ?>
                        <?php if ($atts['show_count'] === 'yes') : ?>
                        <span class="mh-tag-count">(<?php echo $term->count; ?>)</span>
                        <?php endif; ?>
                    </a>
                    <?php else : ?>
                    <span class="mh-cloud-tag <?php echo esc_attr($tag_class); ?>" data-slug="<?php echo esc_attr($term->slug); ?>">
                        <?php echo esc_html($term->name); ?>
                        <?php if ($atts['show_count'] === 'yes') : ?>
                        <span class="mh-tag-count">(<?php echo $term->count; ?>)</span>
                        <?php endif; ?>
                    </span>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Featured Papers
     * [microhub_featured_papers count="3" min_citations="100"]
     */
    public function featured_papers_shortcode($atts) {
        $atts = shortcode_atts(array(
            'count' => 3,
            'min_citations' => 50,
            'title' => 'Featured Papers',
            'layout' => 'cards', // cards or list
        ), $atts);
        
        $papers = get_posts(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => intval($atts['count']),
            'meta_key' => '_mh_citation_count',
            'orderby' => 'meta_value_num',
            'order' => 'DESC',
            'meta_query' => array(
                array(
                    'key' => '_mh_citation_count',
                    'value' => intval($atts['min_citations']),
                    'compare' => '>=',
                    'type' => 'NUMERIC',
                ),
            ),
        ));
        
        if (empty($papers)) {
            return '';
        }
        
        ob_start();
        ?>
        <div class="mh-featured-section">
            <?php if ($atts['title']) : ?>
            <h3><?php echo esc_html($atts['title']); ?></h3>
            <?php endif; ?>
            <div class="mh-featured-papers mh-layout-<?php echo esc_attr($atts['layout']); ?>">
                <?php foreach ($papers as $paper) : 
                    $citations = get_post_meta($paper->ID, '_mh_citation_count', true);
                    $journal = get_post_meta($paper->ID, '_mh_journal', true);
                    $year = get_post_meta($paper->ID, '_mh_publication_year', true);
                    $techniques = wp_get_post_terms($paper->ID, 'mh_technique', array('fields' => 'names'));
                ?>
                <div class="mh-featured-card">
                    <div class="mh-featured-badge">🏆 <?php echo number_format($citations); ?> citations</div>
                    <h4><a href="<?php echo get_permalink($paper->ID); ?>"><?php echo esc_html($paper->post_title); ?></a></h4>
                    <div class="mh-featured-meta">
                        <?php if ($journal) : ?><?php echo esc_html($journal); ?><?php endif; ?>
                        <?php if ($year) : ?> (<?php echo esc_html($year); ?>)<?php endif; ?>
                    </div>
                    <?php if ($techniques) : ?>
                    <div class="mh-featured-tags">
                        <?php foreach (array_slice($techniques, 0, 3) as $tech) : ?>
                        <span class="mh-tag technique"><?php echo esc_html($tech); ?></span>
                        <?php endforeach; ?>
                    </div>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Recent Papers
     * [microhub_recent_papers count="5"]
     */
    public function recent_papers_shortcode($atts) {
        $atts = shortcode_atts(array(
            'count' => 5,
            'title' => 'Recently Added',
        ), $atts);
        
        $papers = get_posts(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => intval($atts['count']),
            'orderby' => 'date',
            'order' => 'DESC',
        ));
        
        if (empty($papers)) {
            return '';
        }
        
        ob_start();
        ?>
        <div class="mh-recent-section">
            <?php if ($atts['title']) : ?>
            <h3><?php echo esc_html($atts['title']); ?></h3>
            <?php endif; ?>
            <ul class="mh-recent-list">
                <?php foreach ($papers as $paper) : 
                    $journal = get_post_meta($paper->ID, '_mh_journal', true);
                ?>
                <li>
                    <a href="<?php echo get_permalink($paper->ID); ?>"><?php echo esc_html($paper->post_title); ?></a>
                    <?php if ($journal) : ?><span class="mh-recent-journal"><?php echo esc_html($journal); ?></span><?php endif; ?>
                </li>
                <?php endforeach; ?>
            </ul>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Top Cited Papers
     * [microhub_top_cited count="10" taxonomy="mh_technique" term="confocal"]
     */
    public function top_cited_shortcode($atts) {
        $atts = shortcode_atts(array(
            'count' => 10,
            'taxonomy' => '',
            'term' => '',
            'title' => 'Top Cited Papers',
        ), $atts);
        
        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => intval($atts['count']),
            'meta_key' => '_mh_citation_count',
            'orderby' => 'meta_value_num',
            'order' => 'DESC',
        );
        
        if ($atts['taxonomy'] && $atts['term']) {
            $args['tax_query'] = array(
                array(
                    'taxonomy' => $atts['taxonomy'],
                    'field' => 'slug',
                    'terms' => $atts['term'],
                ),
            );
        }
        
        $papers = get_posts($args);
        
        if (empty($papers)) {
            return '';
        }
        
        ob_start();
        ?>
        <div class="mh-top-cited-section">
            <?php if ($atts['title']) : ?>
            <h3><?php echo esc_html($atts['title']); ?></h3>
            <?php endif; ?>
            <ol class="mh-top-cited-list">
                <?php foreach ($papers as $paper) : 
                    $citations = get_post_meta($paper->ID, '_mh_citation_count', true);
                ?>
                <li>
                    <a href="<?php echo get_permalink($paper->ID); ?>"><?php echo esc_html($paper->post_title); ?></a>
                    <span class="mh-citation-badge"><?php echo number_format($citations); ?> citations</span>
                </li>
                <?php endforeach; ?>
            </ol>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * AI Chat Widget (Microsoft Copilot Studio)
     * [microhub_ai_chat position="floating"]
     */
    public function ai_chat_shortcode($atts) {
        $copilot_url = get_option('microhub_copilot_bot_url', '');
        $copilot_name = get_option('microhub_copilot_bot_name', 'MicroHub Assistant');
        
        if (!$copilot_url) {
            return '<div class="mh-ai-not-configured"><p>AI assistant is not configured. Please set up Copilot Studio in MicroHub settings.</p></div>';
        }
        
        $atts = shortcode_atts(array(
            'position' => 'inline', // inline or floating
            'title' => $copilot_name,
            'height' => '500px',
        ), $atts);
        
        ob_start();
        ?>
        <div class="mh-ai-chat mh-chat-<?php echo esc_attr($atts['position']); ?>" id="mh-ai-chat">
            <div class="mh-chat-header">
                <h4><?php echo esc_html($atts['title']); ?></h4>
                <?php if ($atts['position'] === 'floating') : ?>
                <button type="button" class="mh-chat-toggle">-</button>
                <?php endif; ?>
            </div>
            <div class="mh-chat-iframe-container" style="height: <?php echo esc_attr($atts['height']); ?>;">
                <iframe 
                    src="<?php echo esc_url($copilot_url); ?>"
                    frameborder="0"
                    style="width: 100%; height: 100%; border: none;"
                    allow="microphone *"
                ></iframe>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Upload Form
     * [microhub_upload_form type="paper"]
     */
    public function upload_form_shortcode($atts) {
        $atts = shortcode_atts(array(
            'type' => 'paper', // paper or protocol
            'title' => 'Submit a Paper',
        ), $atts);
        
        if (!is_user_logged_in()) {
            return '<div class="mh-login-required"><p>Please <a href="' . wp_login_url(get_permalink()) . '">log in</a> to submit content.</p></div>';
        }
        
        ob_start();
        ?>
        <div class="mh-upload-form">
            <h3><?php echo esc_html($atts['title']); ?></h3>
            <form id="mh-submit-form" method="post">
                <?php wp_nonce_field('mh_submit_' . $atts['type']); ?>
                <input type="hidden" name="submit_type" value="<?php echo esc_attr($atts['type']); ?>" />
                
                <div class="mh-form-field">
                    <label>DOI or PubMed ID</label>
                    <input type="text" name="identifier" placeholder="e.g., 10.1038/nmeth.1234 or PMID:12345678" required />
                </div>
                
                <div class="mh-form-field">
                    <label>Techniques (comma-separated)</label>
                    <input type="text" name="techniques" placeholder="e.g., Confocal, STED, Live Cell" />
                </div>
                
                <div class="mh-form-field">
                    <label>Additional Notes</label>
                    <textarea name="notes" placeholder="Any additional information about this paper..."></textarea>
                </div>
                
                <button type="submit" class="mh-submit-btn">Submit</button>
            </form>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Helper: Get taxonomy options for dropdowns
     */
    private function get_taxonomy_options($taxonomy) {
        $terms = get_terms(array(
            'taxonomy' => $taxonomy,
            'hide_empty' => true,
            'number' => 100,
            'orderby' => 'count',
            'order' => 'DESC',
        ));
        
        if (empty($terms) || is_wp_error($terms)) {
            return '';
        }
        
        $output = '';
        foreach ($terms as $term) {
            $output .= sprintf(
                '<option value="%s">%s (%d)</option>',
                esc_attr($term->slug),
                esc_html($term->name),
                $term->count
            );
        }
        
        return $output;
    }
}

// Initialize if this file is loaded
if (class_exists('MicroHub_Modular_Shortcodes')) {
    $mh_modular = new MicroHub_Modular_Shortcodes();
    $mh_modular->init();
}
