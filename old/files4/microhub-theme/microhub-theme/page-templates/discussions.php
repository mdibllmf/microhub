<?php
/**
 * Template Name: Discussions Page
 * 
 * This template displays recent discussions/comments on papers.
 * Edit the page content in WordPress: Pages → Discussions → Edit
 * The page content will appear as an introduction section.
 */
get_header();

// Get recent comments on papers
$recent_comments = get_comments(array(
    'post_type' => 'mh_paper',
    'status' => 'approve',
    'number' => 20
));

// Get discussion categories/topics from page content or default
$categories = array(
    array('icon' => '🔬', 'name' => 'Techniques', 'desc' => 'Discuss imaging methods'),
    array('icon' => '💻', 'name' => 'Software', 'desc' => 'Analysis tools & plugins'),
    array('icon' => '📋', 'name' => 'Protocols', 'desc' => 'Methods & workflows'),
    array('icon' => '❓', 'name' => 'Q&A', 'desc' => 'Ask the community'),
    array('icon' => '📢', 'name' => 'Announcements', 'desc' => 'News & updates'),
    array('icon' => '💡', 'name' => 'Ideas', 'desc' => 'Feature requests')
);
?>

<div class="mh-page-header">
    <h1><?php the_title(); ?></h1>
    <?php if (has_excerpt()): ?>
        <p class="mh-page-subtitle"><?php echo get_the_excerpt(); ?></p>
    <?php else: ?>
        <p class="mh-page-subtitle">Join the microscopy community conversation</p>
    <?php endif; ?>
</div>

<div class="mh-container">
    <!-- Page Introduction from WordPress Editor -->
    <?php if (have_posts()): while (have_posts()): the_post(); ?>
        <?php if (get_the_content()): ?>
        <section class="mh-about-section mh-page-content" style="margin-bottom: 32px;">
            <?php the_content(); ?>
        </section>
        <?php endif; ?>
    <?php endwhile; endif; ?>

    <div class="mh-discussions-layout">
        <!-- Categories Sidebar -->
        <aside class="mh-discussions-sidebar">
            <div class="mh-sidebar-widget">
                <h3>📁 Categories</h3>
                <ul class="mh-category-list">
                    <?php foreach ($categories as $cat): ?>
                    <li class="mh-category-item">
                        <span class="mh-cat-icon"><?php echo $cat['icon']; ?></span>
                        <div>
                            <strong><?php echo esc_html($cat['name']); ?></strong>
                            <small><?php echo esc_html($cat['desc']); ?></small>
                        </div>
                    </li>
                    <?php endforeach; ?>
                </ul>
            </div>
            
            <div class="mh-sidebar-widget">
                <h3>📊 Stats</h3>
                <div class="mh-stats-list">
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Total Comments</span>
                        <span class="mh-stat-value"><?php echo wp_count_comments()->approved; ?></span>
                    </div>
                    <div class="mh-stat-row">
                        <span class="mh-stat-label">Papers with Discussion</span>
                        <span class="mh-stat-value">
                            <?php
                            $papers_with_comments = get_posts(array(
                                'post_type' => 'mh_paper',
                                'posts_per_page' => -1,
                                'fields' => 'ids',
                                'comment_count' => array('value' => 0, 'compare' => '>')
                            ));
                            echo count($papers_with_comments);
                            ?>
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="mh-sidebar-widget">
                <h3>🔗 Quick Links</h3>
                <ul style="display: flex; flex-direction: column; gap: 8px;">
                    <li><a href="<?php echo home_url('/'); ?>">Browse Papers</a></li>
                    <li><a href="<?php echo esc_url(mh_get_page_urls()['contact']); ?>">Contact Us</a></li>
                    <li><a href="https://github.com/microhub" target="_blank">GitHub</a></li>
                </ul>
            </div>
        </aside>
        
        <!-- Main Content -->
        <div class="mh-discussions-main">
            <h2 style="margin-bottom: 24px;">💬 Recent Discussions</h2>
            
            <?php if ($recent_comments): ?>
                <?php foreach ($recent_comments as $comment): 
                    $post = get_post($comment->comment_post_ID);
                    $initials = strtoupper(substr($comment->comment_author, 0, 2));
                ?>
                <div class="mh-topic-card">
                    <div class="mh-comment" style="margin-bottom: 0;">
                        <div class="mh-comment-avatar"><?php echo esc_html($initials); ?></div>
                        <div class="mh-comment-content">
                            <div class="mh-comment-meta">
                                <span class="mh-comment-author"><?php echo esc_html($comment->comment_author); ?></span>
                                <span class="mh-comment-date"><?php echo human_time_diff(strtotime($comment->comment_date), current_time('timestamp')); ?> ago</span>
                            </div>
                            <div class="mh-comment-text"><?php echo wp_trim_words($comment->comment_content, 30); ?></div>
                            <div class="mh-comment-paper" style="margin-top: 8px;">
                                <a href="<?php echo get_permalink($post); ?>" style="font-size: 0.85rem; color: var(--primary);">
                                    📄 <?php echo esc_html($post->post_title); ?>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                <?php endforeach; ?>
            <?php else: ?>
                <div class="mh-about-section" style="text-align: center; padding: 48px;">
                    <p style="color: var(--text-muted); margin-bottom: 16px;">No discussions yet. Be the first to start a conversation!</p>
                    <a href="<?php echo get_post_type_archive_link('mh_paper'); ?>" class="mh-btn mh-btn-primary">Browse Papers</a>
                </div>
            <?php endif; ?>
        </div>
    </div>
</div>

<style>
/* Page content styling */
.mh-page-content h2 { font-size: 1.25rem; margin-top: 24px; margin-bottom: 16px; }
.mh-page-content p { color: var(--text-light); line-height: 1.7; }

/* Discussions specific styles */
.mh-discussions-sidebar { display: flex; flex-direction: column; gap: 24px; }
.mh-category-list { display: flex; flex-direction: column; gap: 8px; }
.mh-category-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: var(--bg-hover); border-radius: 8px; cursor: pointer; }
.mh-category-item:hover { background: var(--border); }
.mh-cat-icon { font-size: 1.5rem; }
.mh-category-item strong { display: block; font-size: 0.9rem; }
.mh-category-item small { color: var(--text-muted); font-size: 0.8rem; }
</style>

<?php get_footer(); ?>
