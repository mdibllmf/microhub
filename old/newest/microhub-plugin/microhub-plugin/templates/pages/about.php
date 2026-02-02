<?php
/**
 * About Page Template for MicroHub
 */

// Get page URLs
$urls = mh_get_all_urls();
?>
<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>
    <div class="mh-page-container">
        <header class="mh-page-header">
            <h1>About MicroHub</h1>
            <p class="mh-subtitle">The Comprehensive Microscopy Research Repository</p>
        </header>

        <section class="mh-about-section">
            <h2>🔬 Our Mission</h2>
            <p>MicroHub is dedicated to advancing microscopy research by providing a centralized, searchable database of microscopy papers, protocols, and resources. We believe that open access to research methods accelerates scientific discovery.</p>
        </section>

        <section class="mh-about-section">
            <h2>📊 What We Offer</h2>
            <div class="mh-features-grid">
                <div class="mh-feature-card">
                    <span class="icon">📄</span>
                    <h3>Research Papers</h3>
                    <p>Access thousands of microscopy research papers with enriched metadata, citation counts, and direct links to full text.</p>
                </div>
                <div class="mh-feature-card">
                    <span class="icon">📋</span>
                    <h3>Protocols</h3>
                    <p>Find detailed protocols from protocols.io, Nature Protocols, Bio-protocol, and community contributions.</p>
                </div>
                <div class="mh-feature-card">
                    <span class="icon">💾</span>
                    <h3>Data Repositories</h3>
                    <p>Links to image data in Zenodo, Figshare, IDR, EMPIAR, BioImage Archive, and more.</p>
                </div>
                <div class="mh-feature-card">
                    <span class="icon">💻</span>
                    <h3>Code & Software</h3>
                    <p>GitHub repositories, analysis scripts, and software tools referenced in publications.</p>
                </div>
                <div class="mh-feature-card">
                    <span class="icon">🔬</span>
                    <h3>Microscope Info</h3>
                    <p>Equipment details including brand, model, and imaging facility information.</p>
                </div>
                <div class="mh-feature-card">
                    <span class="icon">🤖</span>
                    <h3>AI Assistant</h3>
                    <p>Ask questions about microscopy techniques and get intelligent answers powered by Microsoft Copilot.</p>
                </div>
            </div>
        </section>

        <section class="mh-about-section">
            <h2>🔍 Techniques We Cover</h2>
            <div class="mh-technique-list">
                <?php
                $techniques = array(
                    'Confocal Microscopy', 'Two-Photon Microscopy', 'Light Sheet Microscopy',
                    'STED (Super-Resolution)', 'STORM/PALM', 'SIM (Structured Illumination)',
                    'Electron Microscopy (TEM/SEM)', 'Cryo-EM', 'FRET', 'FRAP', 'FLIM',
                    'Live Cell Imaging', 'Fluorescence Microscopy', 'Phase Contrast',
                    'DIC Microscopy', 'AFM', 'Expansion Microscopy', 'Lattice Light Sheet'
                );
                foreach ($techniques as $tech) {
                    echo '<span class="mh-tech-tag">' . esc_html($tech) . '</span>';
                }
                ?>
            </div>
        </section>

        <section class="mh-about-section">
            <h2>📈 Repository Statistics</h2>
            <?php
            global $wpdb;
            $total_papers = wp_count_posts('mh_paper')->publish;
            $techniques_count = wp_count_terms('mh_technique');
            $microscopes_count = wp_count_terms('mh_microscope');
            $with_protocols = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_protocols' AND meta_value != '' AND meta_value != '[]'");
            $with_github = $wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$wpdb->postmeta} WHERE meta_key = '_mh_github_url' AND meta_value != ''");
            ?>
            <div class="mh-stats-grid">
                <div class="mh-stat-card">
                    <span class="number"><?php echo number_format($total_papers); ?></span>
                    <span class="label">Research Papers</span>
                </div>
                <div class="mh-stat-card">
                    <span class="number"><?php echo number_format($techniques_count); ?></span>
                    <span class="label">Techniques</span>
                </div>
                <div class="mh-stat-card">
                    <span class="number"><?php echo number_format($microscopes_count); ?></span>
                    <span class="label">Microscopes</span>
                </div>
                <div class="mh-stat-card">
                    <span class="number"><?php echo number_format($with_protocols); ?></span>
                    <span class="label">With Protocols</span>
                </div>
                <div class="mh-stat-card">
                    <span class="number"><?php echo number_format($with_github); ?></span>
                    <span class="label">With Code</span>
                </div>
            </div>
        </section>

        <section class="mh-about-section">
            <h2>🤝 Contributing</h2>
            <p>MicroHub is a community resource. You can contribute by:</p>
            <ul class="mh-contribute-list">
                <li>📤 <a href="<?php echo esc_url($urls['upload-protocol']); ?>">Uploading protocols</a> you've developed</li>
                <li>📄 <a href="<?php echo esc_url($urls['upload-paper']); ?>">Submitting papers</a> we may have missed</li>
                <li>💬 <a href="<?php echo esc_url($urls['discussions']); ?>">Joining discussions</a> and sharing expertise</li>
                <li>🐛 Reporting issues or suggesting improvements</li>
            </ul>
        </section>

        <section class="mh-about-section">
            <h2>📧 Contact Us</h2>
            <p>Have questions, suggestions, or want to collaborate? <a href="<?php echo esc_url($urls['contact']); ?>">Get in touch</a> with our team.</p>
        </section>
    </div>
</div>

<style>
.mh-page-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 40px 20px;
}

.mh-page-header {
    text-align: center;
    margin-bottom: 50px;
}

.mh-page-header h1 {
    color: #e6edf3;
    font-size: 2.5rem;
    margin-bottom: 10px;
}

.mh-subtitle {
    color: #8b949e;
    font-size: 1.2rem;
}

.mh-about-section {
    background: #161b22;
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 30px;
    border: 1px solid #30363d;
}

.mh-about-section h2 {
    color: #e6edf3;
    font-size: 1.5rem;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.mh-about-section p {
    color: #c9d1d9;
    line-height: 1.7;
}

.mh-features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.mh-feature-card {
    background: #21262d;
    border-radius: 8px;
    padding: 20px;
    border: 1px solid #30363d;
}

.mh-feature-card .icon {
    font-size: 2rem;
    display: block;
    margin-bottom: 10px;
}

.mh-feature-card h3 {
    color: #e6edf3;
    font-size: 1.1rem;
    margin-bottom: 10px;
}

.mh-feature-card p {
    color: #8b949e;
    font-size: 0.9rem;
    margin: 0;
}

.mh-technique-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.mh-tech-tag {
    background: #238636;
    color: #fff;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
}

.mh-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 20px;
}

.mh-stat-card {
    background: #21262d;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    border: 1px solid #30363d;
}

.mh-stat-card .number {
    display: block;
    font-size: 2rem;
    font-weight: bold;
    color: #58a6ff;
}

.mh-stat-card .label {
    color: #8b949e;
    font-size: 0.9rem;
}

.mh-contribute-list {
    list-style: none !important;
    padding: 0 !important;
}

.mh-contribute-list li {
    padding: 10px 0;
    color: #c9d1d9;
    border-bottom: 1px solid #30363d;
}

.mh-contribute-list li:last-child {
    border-bottom: none;
}

.mh-contribute-list a {
    color: #58a6ff;
}

.mh-contribute-list a:hover {
    text-decoration: underline;
}
</style>
