<?php
/**
 * Theme Footer
 */
$urls = mh_get_page_urls();
?>
</main>

<footer class="mh-footer">
    <div class="mh-container">
        <div class="mh-footer-widgets">
            <div>
                <h4>🔬 MicroHub</h4>
                <p style="color: var(--text-muted); font-size: 0.9rem;">
                    The open platform for microscopy research papers, protocols, and best practices.
                </p>
            </div>
            <div>
                <h4>Browse</h4>
                <ul>
                    <li><a href="<?php echo esc_url(home_url('/')); ?>">Papers</a></li>
                    <li><a href="<?php echo esc_url($urls['protocols']); ?>">Protocols</a></li>
                    <li><a href="<?php echo esc_url(home_url('/techniques/')); ?>">Techniques</a></li>
                    <li><a href="<?php echo esc_url(home_url('/software/')); ?>">Software</a></li>
                </ul>
            </div>
            <div>
                <h4>Community</h4>
                <ul>
                    <li><a href="<?php echo esc_url($urls['discussions']); ?>">Discussions</a></li>
                    <li><a href="<?php echo esc_url($urls['about']); ?>">About</a></li>
                    <li><a href="<?php echo esc_url($urls['contact']); ?>">Contact</a></li>
                </ul>
            </div>
            <div>
                <h4>Resources</h4>
                <ul>
                    <li><a href="https://github.com/microhub" target="_blank">GitHub</a></li>
                    <li><a href="<?php echo esc_url(home_url('/api/')); ?>">API</a></li>
                    <li><a href="<?php echo esc_url(home_url('/contribute/')); ?>">Contribute</a></li>
                </ul>
            </div>
        </div>
        <div class="mh-footer-attribution">
            <p>Data powered by:</p>
            <ul>
                <li><a href="https://www.semanticscholar.org/" target="_blank" rel="noopener">Semantic Scholar</a> - Citation data</li>
                <li><a href="https://www.crossref.org/" target="_blank" rel="noopener">Crossref</a> - Metadata and citations</li>
                <li><a href="https://docs.github.com/en/rest" target="_blank" rel="noopener">GitHub API</a> - Repository metrics</li>
            </ul>
        </div>
        <div class="mh-footer-bottom">
            &copy; <?php echo date('Y'); ?> MicroHub. Open source microscopy knowledge.
        </div>
    </div>
</footer>

<?php get_template_part('template-parts/copilot-chat'); ?>

<?php wp_footer(); ?>
</body>
</html>
