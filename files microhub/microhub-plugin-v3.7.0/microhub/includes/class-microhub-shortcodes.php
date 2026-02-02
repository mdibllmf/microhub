<?php
/**
 * MicroHub Shortcodes v2.1
 * Enhanced with AI chat, discussions, protocols, GitHub
 */

class MicroHub_Shortcodes {

    public function init() {
        // Main shortcodes
        add_shortcode('microhub_search_page', array($this, 'search_page_shortcode'));
        add_shortcode('microhub_papers', array($this, 'papers_shortcode'));
        add_shortcode('microhub_stats', array($this, 'stats_shortcode'));
        add_shortcode('microhub_featured', array($this, 'featured_shortcode'));
        add_shortcode('microhub_paper', array($this, 'single_paper_shortcode'));
        add_shortcode('microhub_forum', array($this, 'forum_shortcode'));
        add_shortcode('microhub_upload_protocol', array($this, 'upload_protocol_shortcode'));
        add_shortcode('microhub_upload_paper', array($this, 'upload_paper_shortcode'));
        
        // Page shortcodes
        add_shortcode('microhub_about', array($this, 'about_page_shortcode'));
        add_shortcode('microhub_contact', array($this, 'contact_page_shortcode'));
        add_shortcode('microhub_discussions', array($this, 'discussions_page_shortcode'));
        add_shortcode('microhub_protocols', array($this, 'protocols_page_shortcode'));
    }

    /**
     * Render navigation bar
     */
    private function render_navigation() {
        $current_url = trailingslashit(get_permalink());
        
        $nav_items = array(
            array('url' => home_url('/microhub/'), 'label' => 'ðŸ”¬ Search', 'icon' => ''),
            array('url' => home_url('/discussions/'), 'label' => 'ðŸ’¬ Discussions', 'icon' => ''),
            array('url' => home_url('/upload-protocol/'), 'label' => 'ðŸ“¤ Upload', 'icon' => ''),
            array('url' => home_url('/about/'), 'label' => 'â„¹ï¸ About', 'icon' => ''),
            array('url' => home_url('/contact/'), 'label' => 'ðŸ“§ Contact', 'icon' => ''),
        );
        
        $html = '<nav class="mh-main-nav">';
        $html .= '<div class="mh-nav-inner">';
        $html .= '<a href="' . home_url('/microhub/') . '" class="mh-nav-logo">ðŸ”¬ MicroHub</a>';
        $html .= '<ul class="mh-nav-links">';
        
        foreach ($nav_items as $item) {
            $is_active = (trailingslashit($item['url']) === $current_url) ? ' active' : '';
            $html .= '<li><a href="' . esc_url($item['url']) . '" class="mh-nav-link' . $is_active . '">' . esc_html($item['label']) . '</a></li>';
        }
        
        $html .= '</ul>';
        $html .= '</div>';
        $html .= '</nav>';
        
        return $html;
    }

    /**
     * Main Search Page with all features
     */
    public function search_page_shortcode($atts) {
        $atts = shortcode_atts(array(
            'title' => 'Microscopy Research Repository',
            'subtitle' => 'Search and explore microscopy research papers with enriched metadata',
        ), $atts);

        // Get statistics
        $total_papers = wp_count_posts('mh_paper')->publish;
        $techniques_count = wp_count_terms('mh_technique');
        $microscopes_count = wp_count_terms('mh_microscope');
        $organisms_count = wp_count_terms('mh_organism');
        $software_count = wp_count_terms('mh_software');

        // Get featured papers (top 2 by citations)
        $featured_papers = get_posts(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => 2,
            'meta_key' => '_mh_citation_count',
            'orderby' => 'meta_value_num',
            'order' => 'DESC',
        ));

        ob_start();
        ?>
        <div class="microhub-wrapper">
            <?php echo $this->render_navigation(); ?>
            
            <!-- HEADER: Hero + Search -->
            <header class="mh-site-header">
                <!-- Compact Hero Section -->
                <section class="mh-hero">
                    <div class="mh-hero-inner">
                        <div class="mh-hero-content">
                            <div class="mh-hero-text">
                                <h1><?php echo esc_html($atts['title']); ?></h1>
                                <p><?php echo esc_html($atts['subtitle']); ?></p>
                                
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
                                        <span class="mh-hero-stat-number"><?php echo number_format($microscopes_count); ?></span>
                                        <span class="mh-hero-stat-label">Microscopes</span>
                                    </div>
                                    <div class="mh-hero-stat">
                                        <span class="mh-hero-stat-number"><?php echo number_format($organisms_count); ?></span>
                                        <span class="mh-hero-stat-label">Organisms</span>
                                    </div>
                                    <div class="mh-hero-stat">
                                        <span class="mh-hero-stat-number"><?php echo number_format($software_count); ?></span>
                                        <span class="mh-hero-stat-label">Software</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Featured Papers -->
                            <div class="mh-featured-papers">
                                <?php foreach ($featured_papers as $paper) : 
                                    $citations = get_post_meta($paper->ID, '_mh_citation_count', true);
                                    $authors = get_post_meta($paper->ID, '_mh_authors', true);
                                    $journal = get_post_meta($paper->ID, '_mh_journal', true);
                                    $year = get_post_meta($paper->ID, '_mh_publication_year', true);
                                    $techniques = wp_get_post_terms($paper->ID, 'mh_technique', array('fields' => 'names'));
                                ?>
                                <div class="mh-featured-paper">
                                    <span class="mh-featured-badge">ðŸ† Featured Paper</span>
                                    <h3 class="mh-featured-title">
                                        <a href="<?php echo get_permalink($paper->ID); ?>"><?php echo esc_html($paper->post_title); ?></a>
                                    </h3>
                                    <div class="mh-featured-meta">
                                        <?php if ($authors) echo esc_html(wp_trim_words($authors, 6)); ?>
                                        <?php if ($journal) echo ' â€¢ ' . esc_html($journal); ?>
                                        <?php if ($year) echo ' â€¢ ' . esc_html($year); ?>
                                    </div>
                                    <div class="mh-featured-stats">
                                        <span>ðŸ“Š <?php echo number_format($citations); ?> citations</span>
                                        <?php if (!empty($techniques)) : ?>
                                            <span>ðŸ”¬ <?php echo esc_html($techniques[0]); ?></span>
                                        <?php endif; ?>
                                    </div>
                                </div>
                                <?php endforeach; ?>
                            </div>
                        </div>
                    </div>
                </section>

            <!-- Search Section - Part of Header -->
            <section class="mh-search-section mh-no-box">
                <div class="mh-search-header">
                    <h2>Find Research Papers</h2>
                    <p>Search by title, author, abstract, DOI, or filter by category</p>
                </div>
                
                <!-- Main Search -->
                <div class="mh-search-main">
                    <div class="mh-search-input-wrap">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="m21 21-4.35-4.35"/>
                        </svg>
                        <input type="text" 
                               id="mh-search-input" 
                               class="mh-search-input" 
                               placeholder="Search papers by title, author, DOI..." />
                    </div>
                    <button type="button" class="mh-search-btn" id="mh-search-btn">Search Papers</button>
                </div>

                <!-- Filter Grid -->
                <div class="mh-filter-grid">
                    <div class="mh-filter-item">
                        <label>Technique</label>
                        <select id="mh-filter-technique" data-filter="technique">
                            <option value="">All Techniques</option>
                            <optgroup label="Light Microscopy">
                                <option value="confocal">Confocal</option>
                                <option value="spinning-disk">Spinning Disk</option>
                                <option value="two-photon">Two-Photon / Multiphoton</option>
                                <option value="light-sheet">Light Sheet / SPIM</option>
                                <option value="tirf">TIRF</option>
                                <option value="widefield">Widefield</option>
                                <option value="fluorescence">Fluorescence</option>
                                <option value="live-cell">Live Cell Imaging</option>
                                <option value="intravital">Intravital Microscopy</option>
                            </optgroup>
                            <optgroup label="Super-Resolution">
                                <option value="sted">STED</option>
                                <option value="storm">STORM</option>
                                <option value="palm">PALM</option>
                                <option value="sim">SIM (Structured Illumination)</option>
                                <option value="airyscan">Airyscan</option>
                                <option value="super-resolution">Super-Resolution (Other)</option>
                                <option value="expansion">Expansion Microscopy</option>
                                <option value="minflux">MINFLUX</option>
                            </optgroup>
                            <optgroup label="Electron Microscopy">
                                <option value="tem">TEM</option>
                                <option value="sem">SEM</option>
                                <option value="cryo-em">Cryo-EM</option>
                                <option value="cryo-et">Cryo-ET</option>
                                <option value="fib-sem">FIB-SEM</option>
                                <option value="correlative">Correlative (CLEM)</option>
                            </optgroup>
                            <optgroup label="Specialized Techniques">
                                <option value="fret">FRET</option>
                                <option value="flim">FLIM</option>
                                <option value="frap">FRAP</option>
                                <option value="fcs">FCS</option>
                                <option value="calcium-imaging">Calcium Imaging</option>
                                <option value="optogenetics">Optogenetics</option>
                                <option value="photomanipulation">Photomanipulation</option>
                                <option value="single-molecule">Single Molecule</option>
                            </optgroup>
                            <optgroup label="High-Throughput">
                                <option value="high-content">High-Content Screening</option>
                                <option value="whole-slide">Whole Slide Imaging</option>
                                <option value="automated">Automated Microscopy</option>
                            </optgroup>
                            <optgroup label="Image Analysis">
                                <option value="image-analysis">Image Analysis</option>
                                <option value="segmentation">Segmentation</option>
                                <option value="machine-learning">Machine Learning / Deep Learning</option>
                                <option value="deconvolution">Deconvolution</option>
                                <option value="tracking">Object Tracking</option>
                                <option value="colocalization">Colocalization</option>
                                <option value="3d-reconstruction">3D Reconstruction</option>
                            </optgroup>
                            <optgroup label="Software">
                                <option value="imagej">ImageJ / Fiji</option>
                                <option value="cellprofiler">CellProfiler</option>
                                <option value="cellpose">Cellpose</option>
                                <option value="stardist">StarDist</option>
                                <option value="ilastik">Ilastik</option>
                                <option value="imaris">Imaris</option>
                                <option value="napari">Napari</option>
                                <option value="qupath">QuPath</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="mh-filter-item">
                        <label>Microscope</label>
                        <select id="mh-filter-microscope" data-filter="microscope">
                            <option value="">All Microscopes</option>
                            <optgroup label="Zeiss">
                                <option value="zeiss-lsm-880">Zeiss LSM 880</option>
                                <option value="zeiss-lsm-980">Zeiss LSM 980</option>
                                <option value="zeiss-lsm-900">Zeiss LSM 900</option>
                                <option value="zeiss-airyscan">Zeiss Airyscan</option>
                                <option value="zeiss-elyra">Zeiss Elyra</option>
                                <option value="zeiss-lightsheet">Zeiss Lightsheet</option>
                                <option value="zeiss">Zeiss (Other)</option>
                            </optgroup>
                            <optgroup label="Leica">
                                <option value="leica-sp8">Leica SP8</option>
                                <option value="leica-stellaris">Leica Stellaris</option>
                                <option value="leica-sted">Leica STED</option>
                                <option value="leica-thunder">Leica Thunder</option>
                                <option value="leica">Leica (Other)</option>
                            </optgroup>
                            <optgroup label="Nikon">
                                <option value="nikon-a1">Nikon A1</option>
                                <option value="nikon-ti2">Nikon Ti2</option>
                                <option value="nikon-storm">Nikon N-STORM</option>
                                <option value="nikon-sim">Nikon N-SIM</option>
                                <option value="nikon">Nikon (Other)</option>
                            </optgroup>
                            <optgroup label="Olympus / Evident">
                                <option value="olympus-fv3000">Olympus FV3000</option>
                                <option value="olympus-spinsr">Olympus SpinSR</option>
                                <option value="olympus">Olympus (Other)</option>
                            </optgroup>
                            <optgroup label="Other">
                                <option value="andor-dragonfly">Andor Dragonfly</option>
                                <option value="yokogawa-csu">Yokogawa CSU</option>
                                <option value="perkinelmer-opera">PerkinElmer Opera</option>
                                <option value="bruker">Bruker</option>
                                <option value="3i">3i / Intelligent Imaging</option>
                                <option value="custom-built">Custom Built</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="mh-filter-item">
                        <label>Organism</label>
                        <select id="mh-filter-organism" data-filter="organism">
                            <option value="">All Organisms</option>
                            <optgroup label="Mammals">
                                <option value="mouse">Mouse</option>
                                <option value="rat">Rat</option>
                                <option value="human">Human</option>
                                <option value="primate">Primate</option>
                            </optgroup>
                            <optgroup label="Model Organisms">
                                <option value="zebrafish">Zebrafish</option>
                                <option value="drosophila">Drosophila</option>
                                <option value="c-elegans">C. elegans</option>
                                <option value="xenopus">Xenopus</option>
                            </optgroup>
                            <optgroup label="Other">
                                <option value="yeast">Yeast</option>
                                <option value="bacteria">Bacteria</option>
                                <option value="plant">Plant</option>
                                <option value="cell-culture">Cell Culture</option>
                                <option value="organoid">Organoid</option>
                                <option value="tissue">Tissue Section</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="mh-filter-item">
                        <label>Software</label>
                        <select id="mh-filter-software" data-filter="software">
                            <option value="">All Software</option>
                            <optgroup label="Image Analysis">
                                <option value="imagej">ImageJ</option>
                                <option value="fiji">Fiji</option>
                                <option value="cellprofiler">CellProfiler</option>
                                <option value="imaris">Imaris</option>
                                <option value="ilastik">ilastik</option>
                                <option value="qupath">QuPath</option>
                            </optgroup>
                            <optgroup label="Deep Learning">
                                <option value="cellpose">Cellpose</option>
                                <option value="stardist">StarDist</option>
                                <option value="deepcell">DeepCell</option>
                                <option value="napari">napari</option>
                            </optgroup>
                            <optgroup label="Specialized">
                                <option value="trackmate">TrackMate</option>
                                <option value="arivis">Arivis</option>
                                <option value="huygens">Huygens</option>
                                <option value="aivia">Aivia</option>
                            </optgroup>
                        </select>
                    </div>
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
                </div>

                <!-- Quick Filters -->
                <div class="mh-quick-filters">
                    <span class="mh-quick-label">Quick filters:</span>
                    <button type="button" class="mh-quick-btn" data-filter="foundational">ðŸ† Foundational Papers</button>
                    <button type="button" class="mh-quick-btn" data-filter="high_impact">â­ High Impact</button>
                    <button type="button" class="mh-quick-btn" data-filter="has_protocols">ðŸ“‹ Has Protocols <span class="mh-badge-count" id="count-protocols">-</span></button>
                    <button type="button" class="mh-quick-btn" data-filter="has_github">ðŸ’» GitHub <span class="mh-badge-count" id="count-github">-</span></button>
                    <button type="button" class="mh-quick-btn" data-filter="has_repositories">ðŸ’¾ Has Data <span class="mh-badge-count" id="count-repos">-</span></button>
                    <span class="mh-clear-all" id="mh-clear-filters">âœ• Clear all filters</span>
                </div>
            </section>
            </header>
            <!-- END HEADER -->

            <!-- MAIN BODY: Papers + Sidebar -->
            <main class="mh-site-body">
            <!-- Results Section with Sidebar -->
            <section class="mh-results-section">
                <div class="mh-results-main">
                    <div class="mh-results-header">
                        <div class="mh-results-count">
                            Showing <strong id="mh-showing">0</strong> of <strong id="mh-total">0</strong> papers
                        </div>
                        <div class="mh-results-sort">
                            <label>Sort by:</label>
                            <select id="mh-sort">
                                <option value="citations-desc">Citations (High to Low)</option>
                                <option value="citations-asc">Citations (Low to High)</option>
                                <option value="year-desc">Year (Newest)</option>
                                <option value="year-asc">Year (Oldest)</option>
                                <option value="title-asc">Title (A-Z)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Papers Grid -->
                    <div id="mh-papers-grid" class="mh-papers-grid">
                        <div class="mh-loading">
                            <div class="mh-spinner"></div>
                            <p>Loading papers...</p>
                        </div>
                    </div>

                    <!-- Pagination -->
                    <div id="mh-pagination" class="mh-pagination"></div>
                </div>

                <!-- Sidebar -->
                <aside class="mh-sidebar">
                    <!-- GitHub Code Widget -->
                    <div class="mh-sidebar-widget">
                        <h3><span class="icon">ðŸ’»</span> Code Repositories</h3>
                        <ul class="mh-github-list" id="mh-github-workflows">
                            <li class="mh-loading" style="padding: 10px; text-align: center; color: #8b949e;">Loading...</li>
                        </ul>
                    </div>

                    <!-- Data Repositories Widget (Zenodo, Figshare, IDR, etc.) -->
                    <div class="mh-sidebar-widget">
                        <h3><span class="icon">ðŸ’¾</span> Data Repositories</h3>
                        <ul class="mh-data-repos-list" id="mh-data-repos">
                            <li class="mh-loading" style="padding: 10px; text-align: center; color: #8b949e;">Loading...</li>
                        </ul>
                    </div>

                    <!-- Recent Protocols Widget -->
                    <div class="mh-sidebar-widget">
                        <h3><span class="icon">ðŸ“‹</span> Recent Protocols</h3>
                        <ul class="mh-protocol-list" id="mh-recent-protocols">
                            <li class="mh-loading" style="padding: 10px; text-align: center; color: #8b949e;">Loading...</li>
                        </ul>
                        <a href="<?php echo esc_url(mh_get_page_url('upload-protocol')); ?>" class="mh-view-all" style="display: block; text-align: center; padding: 10px; color: #f78166; font-size: 0.85rem;">+ Upload Protocol</a>
                    </div>

                    <!-- Imaging Facilities Widget -->
                    <div class="mh-sidebar-widget">
                        <h3><span class="icon">ðŸ›ï¸</span> Imaging Facilities</h3>
                        <ul class="mh-facility-list" id="mh-facilities">
                            <li class="mh-loading" style="padding: 10px; text-align: center; color: #8b949e;">Loading...</li>
                        </ul>
                    </div>

                    <!-- Quick Stats -->
                    <div class="mh-sidebar-widget">
                        <h3><span class="icon">ðŸ“Š</span> Repository Stats</h3>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">Total Papers</span>
                            <span class="mh-stat-value"><?php echo number_format($total_papers); ?></span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">With Protocols</span>
                            <span class="mh-stat-value" id="stat-protocols">-</span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">With Code</span>
                            <span class="mh-stat-value" id="stat-github">-</span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">With Datasets</span>
                            <span class="mh-stat-value" id="stat-repos">-</span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">With Facilities</span>
                            <span class="mh-stat-value" id="stat-facilities">-</span>
                        </div>
                    </div>

                    <!-- Discussions Link -->
                    <div class="mh-sidebar-widget">
                        <h3><span class="icon">ðŸ’¬</span> Community</h3>
                        <a href="<?php echo esc_url(mh_get_page_url('discussions')); ?>" class="mh-community-link">
                            <span class="link-icon">ðŸ—£ï¸</span>
                            <span>Discussion Forum</span>
                        </a>
                        <a href="<?php echo esc_url(mh_get_page_url('upload-protocol')); ?>" class="mh-community-link">
                            <span class="link-icon">ðŸ“¤</span>
                            <span>Upload Protocol</span>
                        </a>
                        <a href="<?php echo esc_url(mh_get_page_url('upload-paper')); ?>" class="mh-community-link">
                            <span class="link-icon">ðŸ“„</span>
                            <span>Submit Paper</span>
                        </a>
                    </div>
                </aside>
            </section>
            </main>
            <!-- END MAIN BODY -->

            <!-- AI Chat Widget -->
            <?php echo $this->render_ai_chat_widget(); ?>
        </div>
        <?php
        return ob_get_clean();
    }

    /**
     * Render AI Chat Widget (Microsoft Copilot Studio)
     */
    private function render_ai_chat_widget() {
        $copilot_url = get_option('microhub_copilot_bot_url', '');
        $copilot_name = get_option('microhub_copilot_bot_name', 'MicroHub Assistant');
        
        if (!$copilot_url) {
            return ''; // Don't show widget if Copilot not configured
        }
        
        ob_start();
        ?>
        <!-- AI Chat Toggle -->
        <div class="mh-ai-chat-toggle" id="mh-ai-toggle">
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
            </svg>
        </div>

        <!-- AI Chat Panel (Copilot Iframe) -->
        <div class="mh-ai-chat-panel" id="mh-ai-panel">
            <div class="mh-ai-chat-header">
                <h4><?php echo esc_html($copilot_name); ?></h4>
                <button class="mh-ai-chat-close" id="mh-ai-close">x</button>
            </div>
            <div class="mh-ai-chat-iframe-container">
                <iframe 
                    id="mh-copilot-iframe"
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
     * Discussion Forum Shortcode
     */
    public function forum_shortcode($atts) {
        $atts = shortcode_atts(array(
            'category' => '',
        ), $atts);

        // Get discussions (using a custom post type or comments)
        $discussions = get_posts(array(
            'post_type' => 'mh_discussion',
            'posts_per_page' => 20,
            'orderby' => 'date',
            'order' => 'DESC',
        ));

        ob_start();
        ?>
        <div class="microhub-wrapper">
            <section class="mh-forum-section">
                <div class="mh-forum-header">
                    <h2>ðŸ’¬ Discussion Forum</h2>
                    <?php if (is_user_logged_in()) : ?>
                        <button class="mh-forum-new-btn" onclick="document.getElementById('mh-new-topic-form').style.display='block'">
                            âž• New Discussion
                        </button>
                    <?php endif; ?>
                </div>

                <!-- New Topic Form (hidden by default) -->
                <?php if (is_user_logged_in()) : ?>
                <div id="mh-new-topic-form" style="display: none; margin-bottom: 24px;">
                    <div class="mh-upload-section" style="max-width: 100%;">
                        <h2>Start a New Discussion</h2>
                        <form class="mh-upload-form" method="post" action="">
                            <?php wp_nonce_field('mh_new_discussion', 'mh_discussion_nonce'); ?>
                            <div class="mh-form-group">
                                <label>Topic Title</label>
                                <input type="text" name="discussion_title" required placeholder="What would you like to discuss?" />
                            </div>
                            <div class="mh-form-group">
                                <label>Category</label>
                                <select name="discussion_category">
                                    <option value="general">General Discussion</option>
                                    <option value="techniques">Techniques & Methods</option>
                                    <option value="protocols">Protocols</option>
                                    <option value="equipment">Equipment & Software</option>
                                    <option value="troubleshooting">Troubleshooting</option>
                                    <option value="papers">Paper Discussion</option>
                                </select>
                            </div>
                            <div class="mh-form-group">
                                <label>Message</label>
                                <textarea name="discussion_content" required placeholder="Share your thoughts, questions, or insights..."></textarea>
                            </div>
                            <button type="submit" class="mh-submit-btn">Post Discussion</button>
                        </form>
                    </div>
                </div>
                <?php endif; ?>

                <!-- Discussion Topics -->
                <div class="mh-forum-topics">
                    <?php if ($discussions) : ?>
                        <?php foreach ($discussions as $topic) : 
                            $author = get_user_by('id', $topic->post_author);
                            $replies = get_comments(array('post_id' => $topic->ID, 'count' => true));
                            $category = get_post_meta($topic->ID, '_mh_discussion_category', true);
                            $icons = array(
                                'general' => 'ðŸ’¬',
                                'techniques' => 'ðŸ”¬',
                                'protocols' => 'ðŸ“‹',
                                'equipment' => 'âš™ï¸',
                                'troubleshooting' => 'ðŸ”§',
                                'papers' => 'ðŸ“„',
                            );
                        ?>
                        <div class="mh-forum-topic">
                            <div class="mh-forum-topic-icon"><?php echo $icons[$category] ?? 'ðŸ’¬'; ?></div>
                            <div class="mh-forum-topic-content">
                                <h3 class="mh-forum-topic-title">
                                    <a href="<?php echo get_permalink($topic->ID); ?>"><?php echo esc_html($topic->post_title); ?></a>
                                </h3>
                                <div class="mh-forum-topic-meta">
                                    Started by <?php echo esc_html($author->display_name ?? 'Anonymous'); ?> â€¢ 
                                    <?php echo human_time_diff(get_the_time('U', $topic), current_time('timestamp')); ?> ago
                                </div>
                            </div>
                            <div class="mh-forum-topic-stats">
                                <span>ðŸ’¬ <?php echo $replies; ?> replies</span>
                                <span>ðŸ‘ <?php echo get_post_meta($topic->ID, '_mh_views', true) ?: 0; ?> views</span>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    <?php else : ?>
                        <div class="mh-no-results">
                            <h3>No discussions yet</h3>
                            <p>Be the first to start a conversation!</p>
                        </div>
                    <?php endif; ?>
                </div>
            </section>
        </div>
        <?php
        return ob_get_clean();
    }

    /**
     * Protocol Upload Shortcode
     */
    public function upload_protocol_shortcode($atts) {
        if (!is_user_logged_in()) {
            return '<div class="microhub-wrapper"><div class="mh-upload-section"><p style="color: #8b949e; text-align: center;">Please <a href="' . wp_login_url(get_permalink()) . '" style="color: #58a6ff;">log in</a> to upload a protocol.</p></div></div>';
        }

        // Handle form submission
        if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['mh_protocol_nonce'])) {
            if (wp_verify_nonce($_POST['mh_protocol_nonce'], 'mh_upload_protocol')) {
                $this->handle_protocol_upload();
            }
        }

        ob_start();
        ?>
        <div class="microhub-wrapper">
            <section class="mh-upload-section">
                <h2>ðŸ“‹ Upload Protocol</h2>
                <p>Share your microscopy protocols with the community. Well-documented protocols help advance science!</p>

                <form class="mh-upload-form" method="post" enctype="multipart/form-data">
                    <?php wp_nonce_field('mh_upload_protocol', 'mh_protocol_nonce'); ?>
                    
                    <div class="mh-form-group">
                        <label>Protocol Title *</label>
                        <input type="text" name="protocol_title" required placeholder="e.g., Live-cell STED imaging of mitochondria" />
                    </div>

                    <div class="mh-form-row">
                        <div class="mh-form-group">
                            <label>Technique</label>
                            <select name="protocol_technique">
                                <option value="">Select technique...</option>
                                <?php 
                                $techniques = get_terms(array('taxonomy' => 'mh_technique', 'hide_empty' => false, 'number' => 50));
                                foreach ($techniques as $tech) {
                                    echo '<option value="' . esc_attr($tech->slug) . '">' . esc_html($tech->name) . '</option>';
                                }
                                ?>
                            </select>
                        </div>
                        <div class="mh-form-group">
                            <label>Microscope</label>
                            <select name="protocol_microscope">
                                <option value="">Select microscope...</option>
                                <?php 
                                $microscopes = get_terms(array('taxonomy' => 'mh_microscope', 'hide_empty' => false, 'number' => 50));
                                foreach ($microscopes as $mic) {
                                    echo '<option value="' . esc_attr($mic->slug) . '">' . esc_html($mic->name) . '</option>';
                                }
                                ?>
                            </select>
                        </div>
                    </div>

                    <div class="mh-form-group">
                        <label>Protocol Description *</label>
                        <textarea name="protocol_description" required placeholder="Provide a detailed description of your protocol including materials, steps, and tips..."></textarea>
                    </div>

                    <div class="mh-form-group">
                        <label>GitHub Repository (optional)</label>
                        <input type="url" name="protocol_github" placeholder="https://github.com/username/repo" />
                    </div>

                    <div class="mh-form-group">
                        <label>protocols.io Link (optional)</label>
                        <input type="url" name="protocol_io_link" placeholder="https://www.protocols.io/..." />
                    </div>

                    <div class="mh-form-group">
                        <label>Related Paper DOI (optional)</label>
                        <input type="text" name="protocol_doi" placeholder="10.1234/example.doi" />
                    </div>

                    <div class="mh-form-group">
                        <label>Upload Protocol File (PDF, DOCX, or MD)</label>
                        <div class="mh-dropzone" onclick="document.getElementById('protocol-file').click()">
                            <div class="mh-dropzone-icon">ðŸ“„</div>
                            <div class="mh-dropzone-text">
                                <strong>Click to upload</strong> or drag and drop<br>
                                PDF, DOCX, or Markdown (max 10MB)
                            </div>
                        </div>
                        <input type="file" id="protocol-file" name="protocol_file" accept=".pdf,.docx,.md,.markdown" style="display: none;" />
                    </div>

                    <button type="submit" class="mh-submit-btn">ðŸ“¤ Upload Protocol</button>
                </form>
            </section>
        </div>
        <?php
        return ob_get_clean();
    }

    /**
     * Paper Upload Shortcode
     */
    public function upload_paper_shortcode($atts) {
        if (!is_user_logged_in()) {
            return '<div class="microhub-wrapper"><div class="mh-upload-section"><p style="color: #8b949e; text-align: center;">Please <a href="' . wp_login_url(get_permalink()) . '" style="color: #58a6ff;">log in</a> to submit a paper.</p></div></div>';
        }

        ob_start();
        ?>
        <div class="microhub-wrapper">
            <section class="mh-upload-section">
                <h2>ðŸ“„ Submit Paper</h2>
                <p>Add a microscopy research paper to the repository. Papers with protocols and GitHub links are prioritized!</p>

                <form class="mh-upload-form" method="post">
                    <?php wp_nonce_field('mh_submit_paper', 'mh_paper_nonce'); ?>
                    
                    <div class="mh-form-group">
                        <label>Paper DOI *</label>
                        <input type="text" name="paper_doi" required placeholder="10.1234/example.doi" />
                        <small style="color: #8b949e;">We'll automatically fetch paper details from the DOI</small>
                    </div>

                    <div class="mh-form-group">
                        <label>GitHub Repository (if available)</label>
                        <input type="url" name="paper_github" placeholder="https://github.com/username/repo" />
                    </div>

                    <div class="mh-form-group">
                        <label>Protocol Link (protocols.io, etc.)</label>
                        <input type="url" name="paper_protocol" placeholder="https://www.protocols.io/..." />
                    </div>

                    <div class="mh-form-group">
                        <label>Data Repository (Zenodo, Figshare, etc.)</label>
                        <input type="url" name="paper_data" placeholder="https://zenodo.org/..." />
                    </div>

                    <div class="mh-form-group">
                        <label>Imaging Facility (if mentioned)</label>
                        <input type="text" name="paper_facility" placeholder="Name of imaging facility" />
                    </div>

                    <div class="mh-form-group">
                        <label>Additional Notes</label>
                        <textarea name="paper_notes" placeholder="Any additional context about this paper..."></textarea>
                    </div>

                    <button type="submit" class="mh-submit-btn">ðŸ“¤ Submit Paper</button>
                </form>
            </section>
        </div>
        <?php
        return ob_get_clean();
    }

    /**
     * Handle protocol upload
     */
    private function handle_protocol_upload() {
        $title = sanitize_text_field($_POST['protocol_title']);
        $description = sanitize_textarea_field($_POST['protocol_description']);
        
        $post_id = wp_insert_post(array(
            'post_title' => $title,
            'post_content' => $description,
            'post_type' => 'mh_protocol',
            'post_status' => 'pending',
            'post_author' => get_current_user_id(),
        ));

        if ($post_id && !is_wp_error($post_id)) {
            // Save meta
            if (!empty($_POST['protocol_technique'])) {
                wp_set_object_terms($post_id, $_POST['protocol_technique'], 'mh_technique');
            }
            if (!empty($_POST['protocol_microscope'])) {
                wp_set_object_terms($post_id, $_POST['protocol_microscope'], 'mh_microscope');
            }
            if (!empty($_POST['protocol_github'])) {
                update_post_meta($post_id, '_mh_github_url', esc_url($_POST['protocol_github']));
            }
            if (!empty($_POST['protocol_io_link'])) {
                update_post_meta($post_id, '_mh_protocol_io_link', esc_url($_POST['protocol_io_link']));
            }
            if (!empty($_POST['protocol_doi'])) {
                update_post_meta($post_id, '_mh_related_doi', sanitize_text_field($_POST['protocol_doi']));
            }

            // Handle file upload
            if (!empty($_FILES['protocol_file']['name'])) {
                require_once(ABSPATH . 'wp-admin/includes/file.php');
                $uploaded = wp_handle_upload($_FILES['protocol_file'], array('test_form' => false));
                if (isset($uploaded['url'])) {
                    update_post_meta($post_id, '_mh_protocol_file', $uploaded['url']);
                }
            }

            echo '<div style="background: #238636; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">âœ… Protocol submitted successfully! It will be reviewed and published soon.</div>';
        }
    }

    /**
     * Stats shortcode
     */
    public function stats_shortcode($atts) {
        global $wpdb;
        
        $total_papers = wp_count_posts('mh_paper')->publish;
        $techniques_count = wp_count_terms('mh_technique');
        $microscopes_count = wp_count_terms('mh_microscope');
        
        $protocols_count = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != ''");
        $github_count = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''");

        ob_start();
        ?>
        <div class="mh-sidebar-widget">
            <h3>ðŸ“Š Repository Statistics</h3>
            <div class="mh-stat-row">
                <span class="mh-stat-label">Total Papers</span>
                <span class="mh-stat-value"><?php echo number_format($total_papers); ?></span>
            </div>
            <div class="mh-stat-row">
                <span class="mh-stat-label">Techniques</span>
                <span class="mh-stat-value"><?php echo number_format($techniques_count); ?></span>
            </div>
            <div class="mh-stat-row">
                <span class="mh-stat-label">With Protocols</span>
                <span class="mh-stat-value"><?php echo number_format($protocols_count); ?></span>
            </div>
            <div class="mh-stat-row">
                <span class="mh-stat-label">GitHub Connected</span>
                <span class="mh-stat-value"><?php echo number_format($github_count); ?></span>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }

    /**
     * Featured papers shortcode
     */
    public function featured_shortcode($atts) {
        $atts = shortcode_atts(array('count' => 3), $atts);
        
        $papers = get_posts(array(
            'post_type' => 'mh_paper',
            'posts_per_page' => intval($atts['count']),
            'meta_key' => '_mh_citation_count',
            'orderby' => 'meta_value_num',
            'order' => 'DESC',
        ));

        ob_start();
        echo '<div class="mh-papers-grid" style="padding: 20px;">';
        foreach ($papers as $paper) {
            echo $this->render_paper_card($paper->ID);
        }
        echo '</div>';
        return ob_get_clean();
    }

    /**
     * Papers shortcode
     */
    public function papers_shortcode($atts) {
        $atts = shortcode_atts(array(
            'technique' => '',
            'limit' => 12,
        ), $atts);

        $args = array(
            'post_type' => 'mh_paper',
            'posts_per_page' => intval($atts['limit']),
            'meta_key' => '_mh_citation_count',
            'orderby' => 'meta_value_num',
            'order' => 'DESC',
        );

        if ($atts['technique']) {
            $args['tax_query'] = array(array(
                'taxonomy' => 'mh_technique',
                'field' => 'slug',
                'terms' => $atts['technique'],
            ));
        }

        $papers = get_posts($args);

        ob_start();
        echo '<div class="microhub-wrapper"><div class="mh-papers-grid" style="padding: 20px;">';
        foreach ($papers as $paper) {
            echo $this->render_paper_card($paper->ID);
        }
        echo '</div></div>';
        return ob_get_clean();
    }

    /**
     * Single paper shortcode
     */
    public function single_paper_shortcode($atts) {
        $atts = shortcode_atts(array('id' => 0), $atts);
        if (!$atts['id']) return '';
        return $this->render_paper_card(intval($atts['id']));
    }

    /**
     * Render paper card
     */
    private function render_paper_card($post_id) {
        $doi = get_post_meta($post_id, '_mh_doi', true);
        $pubmed_id = get_post_meta($post_id, '_mh_pubmed_id', true);
        $authors = get_post_meta($post_id, '_mh_authors', true);
        $journal = get_post_meta($post_id, '_mh_journal', true);
        $year = get_post_meta($post_id, '_mh_publication_year', true);
        $citations = get_post_meta($post_id, '_mh_citation_count', true);
        $abstract = get_post_meta($post_id, '_mh_abstract', true);
        $github_url = get_post_meta($post_id, '_mh_github_url', true);
        $facility = get_post_meta($post_id, '_mh_facility', true);
        
        $protocols = json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array();
        $repos = json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array();
        $rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array();
        
        $techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'names'));
        $microscopes = wp_get_post_terms($post_id, 'mh_microscope', array('fields' => 'names'));
        
        $comments_count = get_comments_number($post_id);

        // Badge
        $badge_class = 'standard';
        $badge_text = number_format($citations) . ' citations';
        if ($citations >= 100) {
            $badge_class = 'foundational';
            $badge_text = 'ðŸ† Foundational';
        } elseif ($citations >= 50) {
            $badge_class = 'high-impact';
            $badge_text = 'â­ High Impact';
        }

        ob_start();
        ?>
        <article class="mh-paper-card">
            <div class="mh-card-top">
                <span class="mh-card-badge <?php echo $badge_class; ?>"><?php echo $badge_text; ?></span>
                <span class="mh-card-citations"><strong><?php echo number_format($citations); ?></strong> citations</span>
            </div>
            
            <h3 class="mh-card-title">
                <a href="<?php echo get_permalink($post_id); ?>"><?php echo get_the_title($post_id); ?></a>
            </h3>
            
            <div class="mh-card-meta">
                <?php if ($authors) : ?>
                    <div class="mh-card-authors"><?php echo esc_html(wp_trim_words($authors, 8)); ?></div>
                <?php endif; ?>
                <div class="mh-card-publication">
                    <?php if ($journal) : ?><span><?php echo esc_html($journal); ?></span><?php endif; ?>
                    <?php if ($year) : ?><span><?php echo esc_html($year); ?></span><?php endif; ?>
                </div>
            </div>

            <?php if ($abstract) : ?>
                <p class="mh-card-abstract"><?php echo esc_html(wp_trim_words($abstract, 25)); ?></p>
            <?php endif; ?>

            <div class="mh-card-tags">
                <?php foreach (array_slice($techniques, 0, 2) as $tech) : ?>
                    <span class="mh-card-tag technique"><?php echo esc_html($tech); ?></span>
                <?php endforeach; ?>
                <?php foreach (array_slice($microscopes, 0, 1) as $mic) : ?>
                    <span class="mh-card-tag microscope">ðŸ”¬ <?php echo esc_html($mic); ?></span>
                <?php endforeach; ?>
            </div>

            <div class="mh-card-enrichment">
                <?php if (!empty($protocols)) : ?>
                    <span class="mh-enrichment-item protocols">ðŸ“‹ <?php echo count($protocols); ?> Protocol<?php echo count($protocols) > 1 ? 's' : ''; ?></span>
                <?php endif; ?>
                <?php if ($github_url) : ?>
                    <span class="mh-enrichment-item github">ðŸ’» GitHub</span>
                <?php endif; ?>
                <?php if (!empty($repos)) : ?>
                    <span class="mh-enrichment-item repositories">ðŸ’¾ Data</span>
                <?php endif; ?>
                <?php if ($facility) : ?>
                    <span class="mh-enrichment-item facility">ðŸ›ï¸ Facility</span>
                <?php endif; ?>
            </div>

            <div class="mh-card-footer">
                <div class="mh-card-links">
                    <?php if ($doi) : ?>
                        <a href="https://doi.org/<?php echo esc_attr($doi); ?>" class="mh-card-link doi" target="_blank">DOI</a>
                    <?php endif; ?>
                    <?php if ($pubmed_id) : ?>
                        <a href="https://pubmed.ncbi.nlm.nih.gov/<?php echo esc_attr($pubmed_id); ?>/" class="mh-card-link pubmed" target="_blank">PubMed</a>
                    <?php endif; ?>
                    <?php if ($github_url) : ?>
                        <a href="<?php echo esc_url($github_url); ?>" class="mh-card-link github" target="_blank">GitHub</a>
                    <?php endif; ?>
                </div>
                <div class="mh-card-actions">
                    <span class="mh-card-action" data-paper-id="<?php echo $post_id; ?>">ðŸ’¬ <?php echo $comments_count; ?></span>
                    <span class="mh-card-action mh-ai-discuss" data-title="<?php echo esc_attr(get_the_title($post_id)); ?>">ðŸ¤– Ask AI</span>
                </div>
            </div>
        </article>
        <?php
        return ob_get_clean();
    }

    /**
     * About Page Shortcode
     */
    public function about_page_shortcode($atts) {
        ob_start();
        include MICROHUB_PLUGIN_DIR . 'templates/pages/about.php';
        return ob_get_clean();
    }

    /**
     * Contact Page Shortcode
     */
    public function contact_page_shortcode($atts) {
        ob_start();
        include MICROHUB_PLUGIN_DIR . 'templates/pages/contact.php';
        return ob_get_clean();
    }

    /**
     * Discussions Page Shortcode
     */
    public function discussions_page_shortcode($atts) {
        ob_start();
        include MICROHUB_PLUGIN_DIR . 'templates/pages/discussions.php';
        return ob_get_clean();
    }

    /**
     * Protocols Page Shortcode
     */
    public function protocols_page_shortcode($atts) {
        ob_start();
        include MICROHUB_PLUGIN_DIR . 'templates/pages/protocols.php';
        return ob_get_clean();
    }
}
