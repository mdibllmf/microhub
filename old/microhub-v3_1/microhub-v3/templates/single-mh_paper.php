<?php
/**
 * Single Paper Template v3.0
 */

if (!defined('ABSPATH')) {
    exit;
}

get_header();

$post_id = get_the_ID();

// Basic meta
$doi = get_post_meta($post_id, '_mh_doi', true);
$pubmed_id = get_post_meta($post_id, '_mh_pubmed_id', true);
$pmc_id = get_post_meta($post_id, '_mh_pmc_id', true);
$authors = get_post_meta($post_id, '_mh_authors', true);
$journal = get_post_meta($post_id, '_mh_journal', true);
$year = get_post_meta($post_id, '_mh_publication_year', true);
$citations = get_post_meta($post_id, '_mh_citation_count', true);
$abstract = get_post_meta($post_id, '_mh_abstract', true);
$methods = get_post_meta($post_id, '_mh_methods', true);
$github_url = get_post_meta($post_id, '_mh_github_url', true);

// Flags
$has_full_text = get_post_meta($post_id, '_mh_has_full_text', true);
$has_figures = get_post_meta($post_id, '_mh_has_figures', true);

// Resources (JSON)
$protocols = json_decode(get_post_meta($post_id, '_mh_protocols', true), true);
$repos = json_decode(get_post_meta($post_id, '_mh_repositories', true), true);
$figures = json_decode(get_post_meta($post_id, '_mh_figures', true), true);

if (!is_array($protocols)) $protocols = array();
if (!is_array($repos)) $repos = array();
if (!is_array($figures)) $figures = array();

// Taxonomies
$techniques = wp_get_post_terms($post_id, 'mh_technique', array('fields' => 'names'));
$microscope_brands = wp_get_post_terms($post_id, 'mh_microscope_brand', array('fields' => 'names'));
$analysis_software = wp_get_post_terms($post_id, 'mh_analysis_software', array('fields' => 'names'));
$organisms = wp_get_post_terms($post_id, 'mh_organism', array('fields' => 'names'));

if (is_wp_error($techniques)) $techniques = array();
if (is_wp_error($microscope_brands)) $microscope_brands = array();
if (is_wp_error($analysis_software)) $analysis_software = array();
if (is_wp_error($organisms)) $organisms = array();
?>

<div class="microhub-wrapper">
    <?php if (function_exists('mh_render_nav')) echo mh_render_nav(); ?>
    
    <article class="mh-single-paper">
        <header class="mh-paper-header">
            <div class="mh-badges">
                <?php if ($citations >= 100) : ?>
                    <span class="mh-badge foundational">🏆 Foundational</span>
                <?php elseif ($citations >= 50) : ?>
                    <span class="mh-badge high-impact">⭐ High Impact</span>
                <?php endif; ?>
                
                <?php if ($has_full_text) : ?>
                    <span class="mh-badge full-text">📄 Full Text</span>
                <?php endif; ?>
                
                <?php if (!empty($figures)) : ?>
                    <span class="mh-badge has-figures">🖼️ <?php echo count($figures); ?> Figures</span>
                <?php endif; ?>
            </div>
            
            <h1><?php the_title(); ?></h1>
            
            <?php if ($authors) : ?>
                <p class="mh-authors"><?php echo esc_html($authors); ?></p>
            <?php endif; ?>
            
            <div class="mh-meta">
                <?php if ($journal) : ?>
                    <span>📰 <?php echo esc_html($journal); ?></span>
                <?php endif; ?>
                <?php if ($year) : ?>
                    <span>📅 <?php echo esc_html($year); ?></span>
                <?php endif; ?>
                <?php if ($citations) : ?>
                    <span>📊 <?php echo number_format($citations); ?> citations</span>
                <?php endif; ?>
            </div>
            
            <div class="mh-links">
                <?php if ($doi) : ?>
                    <a href="https://doi.org/<?php echo esc_attr($doi); ?>" class="mh-btn doi" target="_blank">DOI</a>
                <?php endif; ?>
                <?php if ($pubmed_id) : ?>
                    <a href="https://pubmed.ncbi.nlm.nih.gov/<?php echo esc_attr($pubmed_id); ?>/" class="mh-btn pubmed" target="_blank">PubMed</a>
                <?php endif; ?>
                <?php if ($pmc_id) : ?>
                    <a href="https://www.ncbi.nlm.nih.gov/pmc/articles/<?php echo esc_attr($pmc_id); ?>/" class="mh-btn pmc" target="_blank">PMC</a>
                <?php endif; ?>
                <?php if ($github_url) : ?>
                    <a href="<?php echo esc_url($github_url); ?>" class="mh-btn github" target="_blank">💻 GitHub</a>
                <?php endif; ?>
            </div>
        </header>
        
        <div class="mh-content">
            <?php if ($abstract) : ?>
            <section class="mh-section">
                <h2>Abstract</h2>
                <p><?php echo nl2br(esc_html($abstract)); ?></p>
            </section>
            <?php endif; ?>
            
            <?php if ($methods) : ?>
            <section class="mh-section">
                <h2>Methods</h2>
                <div class="mh-methods"><?php echo wpautop(esc_html($methods)); ?></div>
            </section>
            <?php endif; ?>
            
            <?php if (!empty($techniques)) : ?>
            <section class="mh-section">
                <h2>Microscopy Techniques</h2>
                <div class="mh-tags">
                    <?php foreach ($techniques as $tech) : ?>
                        <span class="mh-tag technique"><?php echo esc_html($tech); ?></span>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php endif; ?>
            
            <?php if (!empty($microscope_brands)) : ?>
            <section class="mh-section">
                <h2>Microscopes</h2>
                <div class="mh-tags">
                    <?php foreach ($microscope_brands as $brand) : ?>
                        <span class="mh-tag microscope"><?php echo esc_html($brand); ?></span>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php endif; ?>
            
            <?php if (!empty($analysis_software)) : ?>
            <section class="mh-section">
                <h2>Software</h2>
                <div class="mh-tags">
                    <?php foreach ($analysis_software as $sw) : ?>
                        <span class="mh-tag software"><?php echo esc_html($sw); ?></span>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php endif; ?>
            
            <?php if (!empty($organisms)) : ?>
            <section class="mh-section">
                <h2>Organisms</h2>
                <div class="mh-tags">
                    <?php foreach ($organisms as $org) : ?>
                        <span class="mh-tag organism"><?php echo esc_html($org); ?></span>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php endif; ?>
            
            <?php if (!empty($protocols)) : ?>
            <section class="mh-section">
                <h2>Protocols</h2>
                <div class="mh-resources">
                    <?php foreach ($protocols as $p) : ?>
                        <?php if (!empty($p['url'])) : ?>
                        <a href="<?php echo esc_url($p['url']); ?>" class="mh-resource" target="_blank">
                            📋 <?php echo esc_html($p['source'] ?? $p['name'] ?? 'Protocol'); ?>
                        </a>
                        <?php endif; ?>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php endif; ?>
            
            <?php if (!empty($repos)) : ?>
            <section class="mh-section">
                <h2>Data Repositories</h2>
                <div class="mh-resources">
                    <?php foreach ($repos as $r) : ?>
                        <?php if (!empty($r['url'])) : ?>
                        <a href="<?php echo esc_url($r['url']); ?>" class="mh-resource" target="_blank">
                            💾 <?php echo esc_html($r['name'] ?? 'Repository'); ?>
                        </a>
                        <?php endif; ?>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php endif; ?>
        </div>
    </article>
</div>

<style>
.microhub-wrapper { max-width: 1200px; margin: 0 auto; padding: 20px; }
.mh-single-paper { background: #0d1117; color: #e6edf3; border-radius: 8px; overflow: hidden; }
.mh-paper-header { background: #161b22; padding: 30px; border-bottom: 1px solid #30363d; }
.mh-badges { display: flex; gap: 8px; margin-bottom: 15px; flex-wrap: wrap; }
.mh-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.mh-badge.foundational { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; }
.mh-badge.high-impact { background: linear-gradient(135deg, #58a6ff, #a371f7); color: #fff; }
.mh-badge.full-text { background: #238636; color: #fff; }
.mh-badge.has-figures { background: #8957e5; color: #fff; }
.mh-paper-header h1 { font-size: 1.8rem; margin: 0 0 15px 0; color: #e6edf3; }
.mh-authors { color: #8b949e; margin-bottom: 15px; }
.mh-meta { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; color: #8b949e; }
.mh-links { display: flex; gap: 10px; flex-wrap: wrap; }
.mh-btn { display: inline-block; padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; text-decoration: none; }
.mh-btn.doi { background: #238636; color: #fff; }
.mh-btn.pubmed { background: #1f6feb; color: #fff; }
.mh-btn.pmc { background: #388bfd; color: #fff; }
.mh-btn.github { background: #21262d; color: #e6edf3; border: 1px solid #30363d; }
.mh-content { padding: 30px; }
.mh-section { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
.mh-section h2 { font-size: 1.1rem; margin: 0 0 15px 0; color: #e6edf3; padding-bottom: 10px; border-bottom: 1px solid #30363d; }
.mh-methods { max-height: 300px; overflow-y: auto; }
.mh-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.mh-tag { display: inline-block; padding: 5px 12px; background: #21262d; border: 1px solid #30363d; border-radius: 20px; font-size: 0.85rem; }
.mh-tag.technique { border-color: #58a6ff; }
.mh-tag.microscope { border-color: #f78166; }
.mh-tag.software { border-color: #a371f7; }
.mh-tag.organism { border-color: #3fb950; }
.mh-resources { display: flex; flex-wrap: wrap; gap: 10px; }
.mh-resource { display: inline-block; padding: 8px 16px; background: #21262d; border-radius: 6px; color: #58a6ff; text-decoration: none; }
.mh-resource:hover { background: #30363d; }
</style>

<?php get_footer(); ?>
