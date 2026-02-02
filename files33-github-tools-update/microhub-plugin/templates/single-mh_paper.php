<?php
/**
 * Single Paper Template v2.1
 * With comments, GitHub, protocols, facilities
 */
get_header();

$post_id = get_the_ID();
$doi = get_post_meta($post_id, '_mh_doi', true);
$pubmed_id = get_post_meta($post_id, '_mh_pubmed_id', true);
$authors = get_post_meta($post_id, '_mh_authors', true);
$journal = get_post_meta($post_id, '_mh_journal', true);
$year = get_post_meta($post_id, '_mh_publication_year', true);
$citations = get_post_meta($post_id, '_mh_citation_count', true);
$abstract = get_post_meta($post_id, '_mh_abstract', true);
$pdf_url = get_post_meta($post_id, '_mh_pdf_url', true);
$github_url = get_post_meta($post_id, '_mh_github_url', true);
$facility = get_post_meta($post_id, '_mh_facility', true);
// $full_text is no longer stored to save database space

$protocols = json_decode(get_post_meta($post_id, '_mh_protocols', true), true) ?: array();
$repos = json_decode(get_post_meta($post_id, '_mh_repositories', true), true) ?: array();
$rrids = json_decode(get_post_meta($post_id, '_mh_rrids', true), true) ?: array();
$rors = json_decode(get_post_meta($post_id, '_mh_rors', true), true) ?: array();
$references = json_decode(get_post_meta($post_id, '_mh_references', true), true) ?: array();
$github_tools = json_decode(get_post_meta($post_id, '_mh_github_tools', true), true) ?: array();

$techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'names'));
$microscopes = wp_get_post_terms($post_id, 'mh_microscope', array('fields' => 'names'));
$organisms = wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'names'));
?>

<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>
    <article class="mh-single-paper">
        <!-- Paper Header -->
        <header class="mh-paper-header">
            <div class="mh-paper-header-inner">
                <?php if ($citations >= 100) : ?>
                    <span class="mh-badge foundational">🏆 Foundational Paper</span>
                <?php elseif ($citations >= 50) : ?>
                    <span class="mh-badge high-impact">⭐ High Impact</span>
                <?php endif; ?>
                
                <h1><?php the_title(); ?></h1>
                
                <?php if ($authors) : ?>
                    <p class="mh-paper-authors"><?php echo esc_html($authors); ?></p>
                <?php endif; ?>
                
                <div class="mh-paper-meta">
                    <?php if ($journal) : ?>
                        <span class="mh-meta-item">📰 <?php echo esc_html($journal); ?></span>
                    <?php endif; ?>
                    <?php if ($year) : ?>
                        <span class="mh-meta-item">📅 <?php echo esc_html($year); ?></span>
                    <?php endif; ?>
                    <?php if ($citations) : ?>
                        <span class="mh-meta-item">📊 <?php echo number_format($citations); ?> citations</span>
                    <?php endif; ?>
                </div>
                
                <div class="mh-paper-links">
                    <?php if ($doi) : ?>
                        <a href="https://doi.org/<?php echo esc_attr($doi); ?>" class="mh-btn doi" target="_blank">DOI</a>
                    <?php endif; ?>
                    <?php if ($pubmed_id) : ?>
                        <a href="https://pubmed.ncbi.nlm.nih.gov/<?php echo esc_attr($pubmed_id); ?>/" class="mh-btn pubmed" target="_blank">PubMed</a>
                    <?php endif; ?>
                    <?php if ($pdf_url) : ?>
                        <a href="<?php echo esc_url($pdf_url); ?>" class="mh-btn pdf" target="_blank">PDF</a>
                    <?php endif; ?>
                    <?php if ($github_url) : ?>
                        <a href="<?php echo esc_url($github_url); ?>" class="mh-btn github" target="_blank">💻 GitHub</a>
                    <?php endif; ?>
                </div>
            </div>
        </header>
        
        <div class="mh-paper-content">
            <div class="mh-paper-main">
                <!-- Abstract -->
                <?php if ($abstract) : ?>
                <section class="mh-paper-section">
                    <h2>Abstract</h2>
                    <p><?php echo esc_html($abstract); ?></p>
                </section>
                <?php endif; ?>
                
                <!-- Techniques & Methods -->
                <?php if (!empty($techniques) || !empty($microscopes)) : ?>
                <section class="mh-paper-section">
                    <h2>Methods</h2>
                    <div class="mh-tags-grid">
                        <?php foreach ($techniques as $tech) : ?>
                            <a href="<?php echo get_term_link($tech, 'mh_technique'); ?>" class="mh-tag technique"><?php echo esc_html($tech); ?></a>
                        <?php endforeach; ?>
                        <?php foreach ($microscopes as $mic) : ?>
                            <a href="<?php echo get_term_link($mic, 'mh_microscope'); ?>" class="mh-tag microscope">🔬 <?php echo esc_html($mic); ?></a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Protocols -->
                <?php if (!empty($protocols)) : ?>
                <section class="mh-paper-section">
                    <h2>📋 Protocols</h2>
                    <div class="mh-protocol-list">
                        <?php foreach ($protocols as $protocol) : ?>
                            <a href="<?php echo esc_url($protocol['url'] ?? '#'); ?>" class="mh-protocol-item" target="_blank">
                                <span class="icon">📄</span>
                                <span class="name"><?php echo esc_html($protocol['name'] ?? 'View Protocol'); ?></span>
                                <span class="source"><?php echo esc_html($protocol['source'] ?? 'protocols.io'); ?></span>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- GitHub / Code -->
                <?php if (!empty($github_tools) || $github_url) : ?>
                <section class="mh-paper-section">
                    <h2>💻 Code & Software</h2>
                    
                    <?php if (!empty($github_tools)) : ?>
                    <div class="mh-github-tools-list">
                        <?php foreach ($github_tools as $tool) :
                            $tool_url = !empty($tool['url']) ? $tool['url'] : 'https://github.com/' . $tool['full_name'];
                            $health = intval($tool['health_score'] ?? 0);
                            $is_archived = !empty($tool['is_archived']);
                            if ($is_archived) { $health_class = 'archived'; $health_label = 'Archived'; }
                            elseif ($health >= 70) { $health_class = 'active'; $health_label = 'Active'; }
                            elseif ($health >= 40) { $health_class = 'moderate'; $health_label = 'Moderate'; }
                            elseif ($health > 0) { $health_class = 'low'; $health_label = 'Low Activity'; }
                            else { $health_class = 'unknown'; $health_label = ''; }
                            
                            $rel = $tool['relationship'] ?? 'uses';
                            $rel_labels = array('introduces' => '🆕 Introduced here', 'uses' => '🔧 Used', 'extends' => '🔀 Extended', 'benchmarks' => '📊 Benchmarked');
                            $rel_label = $rel_labels[$rel] ?? '🔧 Used';
                        ?>
                        <a href="<?php echo esc_url($tool_url); ?>" class="mh-github-tool-card health-<?php echo $health_class; ?>" target="_blank" rel="noopener">
                            <div class="mh-ght-header">
                                <strong class="mh-ght-name"><?php echo esc_html($tool['full_name']); ?></strong>
                                <?php if ($health_label) : ?>
                                    <span class="mh-ght-health <?php echo $health_class; ?>"><?php echo $health_label; ?></span>
                                <?php endif; ?>
                            </div>
                            <?php if (!empty($tool['description'])) : ?>
                                <p class="mh-ght-desc"><?php echo esc_html(wp_trim_words($tool['description'], 20, '...')); ?></p>
                            <?php endif; ?>
                            <div class="mh-ght-metrics">
                                <span class="mh-ght-rel <?php echo esc_attr($rel); ?>"><?php echo $rel_label; ?></span>
                                <?php if (!empty($tool['stars'])) : ?>
                                    <span>⭐ <?php echo number_format(intval($tool['stars'])); ?></span>
                                <?php endif; ?>
                                <?php if (!empty($tool['forks'])) : ?>
                                    <span>🍴 <?php echo number_format(intval($tool['forks'])); ?></span>
                                <?php endif; ?>
                                <?php if (!empty($tool['language'])) : ?>
                                    <span>📝 <?php echo esc_html($tool['language']); ?></span>
                                <?php endif; ?>
                            </div>
                            <?php if (!empty($tool['topics']) && is_array($tool['topics'])) : ?>
                                <div class="mh-ght-topics">
                                    <?php foreach (array_slice($tool['topics'], 0, 5) as $topic) : ?>
                                        <span class="mh-ght-topic"><?php echo esc_html($topic); ?></span>
                                    <?php endforeach; ?>
                                </div>
                            <?php endif; ?>
                        </a>
                        <?php endforeach; ?>
                    </div>
                    <?php elseif ($github_url) : ?>
                    <a href="<?php echo esc_url($github_url); ?>" class="mh-github-card" target="_blank">
                        <span class="icon">📂</span>
                        <div class="info">
                            <strong>GitHub Repository</strong>
                            <span><?php echo esc_html(preg_replace('/^https?:\/\/(www\.)?github\.com\//', '', $github_url)); ?></span>
                        </div>
                        <span class="arrow">→</span>
                    </a>
                    <?php endif; ?>
                </section>
                <?php endif; ?>
                
                <!-- Repositories -->
                <?php if (!empty($repos)) : ?>
                <section class="mh-paper-section">
                    <h2>💾 Data Repositories</h2>
                    <div class="mh-repo-list">
                        <?php foreach ($repos as $repo) : 
                            $url = $repo['url'] ?? '#';
                            
                            // Handle both formats: name/type
                            $repo_name = '';
                            if (!empty($repo['name']) && strtolower($repo['name']) !== 'unknown') {
                                $repo_name = $repo['name'];
                            } elseif (!empty($repo['type']) && strtolower($repo['type']) !== 'unknown') {
                                $repo_name = $repo['type'];
                            }
                            
                            // If still no name, detect from URL
                            if (empty($repo_name) && $url && $url !== '#') {
                                if (strpos($url, 'zenodo') !== false) {
                                    $repo_name = 'Zenodo';
                                } elseif (strpos($url, 'figshare') !== false) {
                                    $repo_name = 'Figshare';
                                } elseif (strpos($url, 'github') !== false) {
                                    $repo_name = 'GitHub';
                                } elseif (strpos($url, 'dryad') !== false) {
                                    $repo_name = 'Dryad';
                                } elseif (strpos($url, 'osf.io') !== false) {
                                    $repo_name = 'OSF';
                                } elseif (strpos($url, 'dataverse') !== false) {
                                    $repo_name = 'Dataverse';
                                } elseif (strpos($url, 'mendeley') !== false) {
                                    $repo_name = 'Mendeley Data';
                                } elseif (strpos($url, 'synapse') !== false) {
                                    $repo_name = 'Synapse';
                                } elseif (strpos($url, 'ebi.ac.uk') !== false || strpos($url, 'empiar') !== false) {
                                    $repo_name = 'EMPIAR';
                                } elseif (strpos($url, 'ncbi') !== false || strpos($url, 'geo') !== false) {
                                    $repo_name = 'GEO/NCBI';
                                } else {
                                    $repo_name = 'Data Repository';
                                }
                            }
                            
                            if (empty($repo_name)) {
                                $repo_name = 'Data Repository';
                            }
                            
                            // Get ID from various fields
                            $repo_id = '';
                            if (!empty($repo['identifier'])) {
                                $repo_id = $repo['identifier'];
                            } elseif (!empty($repo['accession_id'])) {
                                $repo_id = $repo['accession_id'];
                            } elseif (!empty($repo['id'])) {
                                $repo_id = $repo['id'];
                            }
                        ?>
                            <a href="<?php echo esc_url($url); ?>" class="mh-repo-item" target="_blank">
                                <span><?php echo esc_html($repo_name); ?></span>
                                <?php if ($repo_id) : ?>
                                    <span class="mh-repo-id"><?php echo esc_html($repo_id); ?></span>
                                <?php endif; ?>
                            </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Full Text removed - no longer stored to save database space -->
                <!-- Abstract is displayed above with tag highlighting instead -->
                
                <!-- References -->
                <?php if (!empty($references)) : ?>
                <section class="mh-paper-section mh-references-section">
                    <h2>📚 References</h2>
                    <ol class="mh-reference-list">
                        <?php foreach ($references as $idx => $ref) : 
                            $num = isset($ref['num']) ? $ref['num'] : ($idx + 1);
                            $text = isset($ref['text']) ? $ref['text'] : '';
                            $ref_doi = isset($ref['doi']) ? $ref['doi'] : '';
                            $pmid = isset($ref['pmid']) ? $ref['pmid'] : '';
                            $url = isset($ref['url']) ? $ref['url'] : '';
                            
                            $link = '';
                            if ($ref_doi) {
                                $link = 'https://doi.org/' . $ref_doi;
                            } elseif ($pmid) {
                                $link = 'https://pubmed.ncbi.nlm.nih.gov/' . $pmid;
                            } elseif ($url) {
                                $link = $url;
                            }
                        ?>
                            <li id="ref-<?php echo esc_attr($num); ?>" class="mh-reference-item">
                                <span class="mh-ref-text"><?php echo esc_html($text); ?></span>
                                <?php if ($link) : ?>
                                    <a href="<?php echo esc_url($link); ?>" class="mh-ref-external-link" target="_blank" rel="noopener">
                                        <?php if ($ref_doi) : ?>
                                            <span class="mh-ref-doi">DOI</span>
                                        <?php elseif ($pmid) : ?>
                                            <span class="mh-ref-pmid">PubMed</span>
                                        <?php else : ?>
                                            <span>🔗</span>
                                        <?php endif; ?>
                                    </a>
                                <?php endif; ?>
                            </li>
                        <?php endforeach; ?>
                    </ol>
                </section>
                <?php endif; ?>
                
                <!-- Facility -->
                <?php if ($facility) : ?>
                <section class="mh-paper-section">
                    <h2>🏛️ Imaging Facility</h2>
                    <div class="mh-facility-card">
                        <span class="icon">🏛️</span>
                        <span class="name"><?php echo esc_html($facility); ?></span>
                    </div>
                </section>
                <?php endif; ?>
                
                <!-- Comments Section -->
                <section class="mh-paper-section mh-comments-section">
                    <div class="mh-comments-header">
                        <h2>💬 Discussion</h2>
                        <span class="mh-comments-count"><?php echo get_comments_number(); ?> comments</span>
                    </div>
                    
                    <?php if (comments_open()) : ?>
                        <div class="mh-comments-list">
                            <?php
                            $comments = get_comments(array(
                                'post_id' => $post_id,
                                'status' => 'approve',
                                'order' => 'ASC',
                            ));
                            
                            if ($comments) :
                                foreach ($comments as $comment) :
                                    $initials = strtoupper(substr($comment->comment_author, 0, 2));
                            ?>
                                <div class="mh-comment">
                                    <div class="mh-comment-avatar"><?php echo $initials; ?></div>
                                    <div class="mh-comment-content">
                                        <div class="mh-comment-meta">
                                            <span class="mh-comment-author"><?php echo esc_html($comment->comment_author); ?></span>
                                            <span class="mh-comment-date"><?php echo human_time_diff(strtotime($comment->comment_date), current_time('timestamp')); ?> ago</span>
                                        </div>
                                        <div class="mh-comment-text"><?php echo wpautop(esc_html($comment->comment_content)); ?></div>
                                    </div>
                                </div>
                            <?php 
                                endforeach;
                            else :
                            ?>
                                <p class="mh-no-comments">No comments yet. Be the first to start a discussion!</p>
                            <?php endif; ?>
                        </div>
                        
                        <!-- Comment Form - Open to all with name required -->
                        <div class="mh-comment-form">
                            <h4>Leave a Comment</h4>
                            <form method="post" action="<?php echo site_url('/wp-comments-post.php'); ?>">
                                <?php if (!is_user_logged_in()) : ?>
                                    <div class="mh-form-row">
                                        <div class="mh-form-group">
                                            <label for="author">Your Name <span class="required">*</span></label>
                                            <input type="text" name="author" id="author" required placeholder="Enter your name">
                                        </div>
                                        <div class="mh-form-group">
                                            <label for="email">Email <span class="optional">(optional)</span></label>
                                            <input type="email" name="email" id="email" placeholder="For notifications only">
                                        </div>
                                    </div>
                                <?php else : 
                                    $current_user = wp_get_current_user();
                                ?>
                                    <p class="mh-logged-in-as">
                                        Commenting as <strong><?php echo esc_html($current_user->display_name); ?></strong>
                                    </p>
                                <?php endif; ?>
                                
                                <div class="mh-form-group">
                                    <label for="comment">Your Comment <span class="required">*</span></label>
                                    <textarea name="comment" id="comment" rows="4" required placeholder="Share your thoughts about this paper..."></textarea>
                                </div>
                                
                                <input type="hidden" name="comment_post_ID" value="<?php echo $post_id; ?>" />
                                <?php wp_nonce_field('unfiltered-html-comment'); ?>
                                <button type="submit" class="mh-submit-btn">Post Comment</button>
                            </form>
                        </div>
                    <?php endif; ?>
                </section>
            </div>
            
            <!-- Sidebar -->
            <aside class="mh-paper-sidebar">
                <!-- Related Papers -->
                <div class="mh-sidebar-widget">
                    <h3>Related Papers</h3>
                    <?php
                    $related = get_posts(array(
                        'post_type' => 'mh_paper',
                        'posts_per_page' => 5,
                        'post__not_in' => array($post_id),
                        'tax_query' => array(
                            'relation' => 'OR',
                            array(
                                'taxonomy' => 'mh_technique',
                                'field' => 'slug',
                                'terms' => wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'slugs')),
                            ),
                        ),
                    ));
                    
                    if ($related) :
                        foreach ($related as $paper) :
                    ?>
                        <a href="<?php echo get_permalink($paper->ID); ?>" class="mh-related-item">
                            <?php echo esc_html(wp_trim_words($paper->post_title, 10)); ?>
                        </a>
                    <?php 
                        endforeach;
                    else :
                    ?>
                        <p style="color: #8b949e; font-size: 0.85rem;">No related papers found.</p>
                    <?php endif; ?>
                </div>
                
                <!-- Organisms -->
                <?php if (!empty($organisms)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>🧬 Organisms</h3>
                    <div class="mh-tag-list">
                        <?php foreach ($organisms as $org) : ?>
                            <a href="<?php echo get_term_link($org, 'mh_organism'); ?>" class="mh-tag organism"><?php echo esc_html($org); ?></a>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>
                
                <!-- RRIDs -->
                <?php if (!empty($rrids)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>🔬 Resources (RRIDs)</h3>
                    <div class="mh-rrid-list">
                        <?php foreach ($rrids as $rrid) : ?>
                            <div class="mh-rrid-item">
                                <span class="type"><?php echo esc_html($rrid['type'] ?? 'Resource'); ?></span>
                                <span class="id"><?php echo esc_html($rrid['id'] ?? ''); ?></span>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>
                
                <!-- RORs (Research Organization Registry) -->
                <?php if (!empty($rors)) : ?>
                <div class="mh-sidebar-widget">
                    <h3>🏛️ Research Organizations (ROR)</h3>
                    <div class="mh-ror-list">
                        <?php foreach ($rors as $ror) : 
                            $ror_id = is_array($ror) ? ($ror['id'] ?? '') : $ror;
                            $ror_url = is_array($ror) ? ($ror['url'] ?? 'https://ror.org/' . $ror_id) : 'https://ror.org/' . $ror;
                            if ($ror_id) :
                        ?>
                            <a href="<?php echo esc_url($ror_url); ?>" class="mh-ror-item" target="_blank" rel="noopener">
                                <span class="ror-icon">🏛</span>
                                <span class="ror-id"><?php echo esc_html($ror_id); ?></span>
                            </a>
                        <?php endif; endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>
            </aside>
        </div>
    </article>
    
    <!-- AI Chat Widget (Microsoft Copilot) -->
    <?php 
    $copilot_url = get_option('microhub_copilot_bot_url', '');
    $copilot_name = get_option('microhub_copilot_bot_name', 'MicroHub Assistant');
    if ($copilot_url) : 
    ?>
    <div class="mh-ai-chat-toggle" id="mh-ai-toggle">
        <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
        </svg>
    </div>
    
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
    <?php endif; ?>
</div>

<style>
/* Single Paper Styles */
.mh-single-paper {
    max-width: 1400px;
    margin: 0 auto;
}

.mh-paper-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    padding: 40px 24px;
    border-bottom: 1px solid #30363d;
}

.mh-paper-header-inner {
    max-width: 900px;
}

.mh-paper-header h1 {
    color: #e6edf3;
    font-size: 1.75rem;
    line-height: 1.3;
    margin: 10px 0;
}

.mh-paper-authors {
    color: #8b949e;
    font-size: 0.95rem;
    margin-bottom: 16px;
}

.mh-paper-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 20px;
}

.mh-meta-item {
    color: #8b949e;
    font-size: 0.9rem;
}

.mh-paper-links {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.mh-btn {
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
}

.mh-btn.doi { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-btn.pubmed { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.mh-btn.pdf { background: rgba(247, 129, 102, 0.15); color: #f78166; }
.mh-btn.github { background: rgba(110, 118, 129, 0.15); color: #e6edf3; }

.mh-paper-content {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 24px;
    padding: 24px;
    background: #0d1117;
}

.mh-paper-section {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.mh-paper-section h2 {
    color: #e6edf3;
    font-size: 1.1rem;
    margin: 0 0 16px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #30363d;
}

.mh-paper-section p {
    color: #8b949e;
    line-height: 1.6;
}

.mh-tags-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.mh-tag {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
}

.mh-tag.technique { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
.mh-tag.microscope { background: rgba(163, 113, 247, 0.15); color: #a371f7; }
.mh-tag.organism { background: rgba(63, 185, 80, 0.15); color: #3fb950; }

.mh-protocol-list, .mh-repo-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-protocol-item, .mh-repo-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
    color: #e6edf3;
    transition: all 0.2s;
}

.mh-protocol-item:hover, .mh-repo-item:hover {
    background: #30363d;
}

.mh-github-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: #21262d;
    border-radius: 8px;
    color: #e6edf3;
    transition: all 0.2s;
}

.mh-github-card:hover {
    background: #30363d;
}

.mh-github-card .icon {
    font-size: 2rem;
}

.mh-github-card .info {
    flex: 1;
}

.mh-github-card .info strong {
    display: block;
    margin-bottom: 4px;
}

.mh-github-card .info span {
    color: #8b949e;
    font-size: 0.85rem;
}

/* GitHub Tools Cards (enriched per-paper tools) */
.mh-github-tools-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.mh-github-tool-card {
    display: block;
    padding: 16px;
    background: #21262d;
    border: 1px solid #30363d;
    border-left: 4px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
    text-decoration: none;
    transition: all 0.2s;
}
.mh-github-tool-card:hover {
    background: #30363d;
    border-color: var(--primary, #58a6ff);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.mh-github-tool-card.health-active { border-left-color: #3fb950; }
.mh-github-tool-card.health-moderate { border-left-color: #d29922; }
.mh-github-tool-card.health-low { border-left-color: #f85149; }
.mh-github-tool-card.health-archived { border-left-color: #6e7681; opacity: 0.8; }
.mh-ght-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
}
.mh-ght-name { font-size: 1rem; color: #58a6ff; word-break: break-word; }
.mh-ght-health {
    font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; padding: 3px 10px; border-radius: 12px;
    white-space: nowrap; flex-shrink: 0;
}
.mh-ght-health.active { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
.mh-ght-health.moderate { background: rgba(210, 153, 34, 0.15); color: #d29922; }
.mh-ght-health.low { background: rgba(248, 81, 73, 0.15); color: #f85149; }
.mh-ght-health.archived { background: rgba(110, 118, 129, 0.15); color: #6e7681; }
.mh-ght-desc { font-size: 0.85rem; color: #8b949e; margin: 0 0 8px; line-height: 1.4; }
.mh-ght-metrics { display: flex; flex-wrap: wrap; gap: 10px; font-size: 0.8rem; color: #8b949e; margin-bottom: 8px; }
.mh-ght-rel { font-weight: 600; padding: 1px 8px; border-radius: 8px; font-size: 0.72rem; }
.mh-ght-rel.introduces { background: rgba(163, 113, 247, 0.15); color: #a371f7; }
.mh-ght-rel.uses { background: rgba(88, 166, 255, 0.1); color: #58a6ff; }
.mh-ght-rel.extends { background: rgba(35, 134, 54, 0.15); color: #3fb950; }
.mh-ght-rel.benchmarks { background: rgba(210, 153, 34, 0.1); color: #d29922; }
.mh-ght-topics { display: flex; flex-wrap: wrap; gap: 4px; }
.mh-ght-topic {
    font-size: 0.7rem; background: rgba(88, 166, 255, 0.08); color: #58a6ff;
    padding: 1px 8px; border-radius: 10px; border: 1px solid rgba(88, 166, 255, 0.2);
}

.mh-facility-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #21262d;
    border-radius: 6px;
    color: #e6edf3;
}

/* Comments */
.mh-comments-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #30363d;
}

.mh-comments-count {
    background: #58a6ff;
    color: white;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 0.8rem;
}

.mh-comment {
    display: flex;
    gap: 12px;
    padding: 16px;
    background: #0d1117;
    border-radius: 8px;
    margin-bottom: 12px;
}

.mh-comment-avatar {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #58a6ff, #a371f7);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.85rem;
    flex-shrink: 0;
}

.mh-comment-content {
    flex: 1;
}

.mh-comment-meta {
    display: flex;
    gap: 10px;
    margin-bottom: 6px;
}

.mh-comment-author {
    font-weight: 600;
    color: #e6edf3;
    font-size: 0.9rem;
}

.mh-comment-date {
    font-size: 0.8rem;
    color: #8b949e;
}

.mh-comment-text {
    color: #8b949e;
    font-size: 0.9rem;
    line-height: 1.5;
}

.mh-comment-actions {
    display: flex;
    gap: 16px;
    margin-top: 8px;
}

.mh-comment-action {
    font-size: 0.8rem;
    color: #8b949e;
    cursor: pointer;
}

.mh-comment-action:hover {
    color: #58a6ff;
}

.mh-comment-form textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #30363d;
    border-radius: 8px;
    background: #0d1117;
    color: #e6edf3;
    font-size: 0.9rem;
    resize: vertical;
    min-height: 80px;
    margin-bottom: 10px;
}

.mh-comment-form button {
    padding: 8px 20px;
    background: #58a6ff;
    border: none;
    border-radius: 6px;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

.mh-no-comments, .mh-login-prompt {
    color: #8b949e;
    font-size: 0.9rem;
    text-align: center;
    padding: 20px;
}

.mh-login-prompt a {
    color: #58a6ff;
}

/* Sidebar */
.mh-paper-sidebar {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.mh-sidebar-widget {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
}

.mh-sidebar-widget h3 {
    color: #e6edf3;
    font-size: 0.9rem;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #30363d;
}

.mh-related-item {
    display: block;
    padding: 8px;
    color: #58a6ff;
    font-size: 0.85rem;
    border-bottom: 1px solid #21262d;
}

.mh-related-item:hover {
    background: #21262d;
}

.mh-tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.mh-rrid-item {
    padding: 8px;
    background: #21262d;
    border-radius: 6px;
    margin-bottom: 8px;
    font-size: 0.85rem;
}

.mh-rrid-item .type {
    color: #8b949e;
    display: block;
    font-size: 0.75rem;
}

.mh-rrid-item .id {
    color: #e6edf3;
}

/* ROR Styles */
.mh-ror-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-ror-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
    border-radius: 8px;
    color: #bee3f8;
    text-decoration: none;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    border: 1px solid #2b6cb0;
}

.mh-ror-item:hover {
    background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
    color: #fff;
    transform: translateX(4px);
}

.mh-ror-item .ror-icon {
    font-size: 1rem;
}

.mh-ror-item .ror-id {
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 0.8rem;
}

@media (max-width: 900px) {
    .mh-paper-content {
        grid-template-columns: 1fr;
    }
}
</style>

<?php get_footer(); ?>
