<?php
/**
 * Page Template for Discussions
 * WordPress automatically uses this for pages with slug "discussions"
 * No shortcode needed - just create a page with slug "discussions"
 */
get_header();

// Handle new discussion submission
$discussion_submitted = false;
$discussion_error = '';

if (isset($_POST['mh_new_discussion']) && wp_verify_nonce($_POST['mh_discussion_nonce'], 'mh_new_discussion')) {
    $title = sanitize_text_field($_POST['discussion_title']);
    $content = sanitize_textarea_field($_POST['discussion_content']);
    $author_name = sanitize_text_field($_POST['author_name']);
    $author_email = sanitize_email($_POST['author_email']);
    $category = sanitize_text_field($_POST['discussion_category']);
    
    if (empty($title) || empty($content) || empty($author_name) || empty($author_email)) {
        $discussion_error = 'Please fill in all required fields.';
    } elseif (!is_email($author_email)) {
        $discussion_error = 'Please enter a valid email address.';
    } else {
        $post_id = wp_insert_post(array(
            'post_type' => 'mh_discussion',
            'post_title' => $title,
            'post_content' => $content,
            'post_status' => 'publish',
            'comment_status' => 'open',
        ));
        
        if ($post_id && !is_wp_error($post_id)) {
            update_post_meta($post_id, '_mh_author_name', $author_name);
            update_post_meta($post_id, '_mh_author_email', $author_email);
            update_post_meta($post_id, '_mh_category', $category);
            $discussion_submitted = true;
        } else {
            $discussion_error = 'Error creating discussion. Please try again.';
        }
    }
}

$category_filter = isset($_GET['category']) ? sanitize_text_field($_GET['category']) : '';

$categories = array(
    'techniques' => array('icon' => 'ðŸ”¬', 'name' => 'Techniques', 'desc' => 'Discuss imaging methods'),
    'software' => array('icon' => 'ðŸ’»', 'name' => 'Software', 'desc' => 'Analysis tools & plugins'),
    'protocols' => array('icon' => 'ðŸ“‹', 'name' => 'Protocols', 'desc' => 'Methods & workflows'),
    'qa' => array('icon' => 'â“', 'name' => 'Q&A', 'desc' => 'Ask the community'),
    'announcements' => array('icon' => 'ðŸ“¢', 'name' => 'Announcements', 'desc' => 'News & updates'),
    'ideas' => array('icon' => 'ðŸ’¡', 'name' => 'Ideas', 'desc' => 'Feature requests'),
);

$discussion_args = array(
    'post_type' => 'mh_discussion',
    'posts_per_page' => 20,
    'post_status' => 'publish',
    'orderby' => 'modified',
    'order' => 'DESC',
);

if ($category_filter && isset($categories[$category_filter])) {
    $discussion_args['meta_query'] = array(
        array(
            'key' => '_mh_category',
            'value' => $category_filter,
            'compare' => '='
        )
    );
}

$discussions = get_posts($discussion_args);

$recent_paper_comments = get_comments(array(
    'post_type' => 'mh_paper',
    'status' => 'approve',
    'number' => 10
));

$category_counts = array();
foreach ($categories as $key => $cat) {
    $count_args = array(
        'post_type' => 'mh_discussion',
        'posts_per_page' => -1,
        'post_status' => 'publish',
        'fields' => 'ids',
        'meta_query' => array(
            array(
                'key' => '_mh_category',
                'value' => $key,
                'compare' => '='
            )
        )
    );
    $category_counts[$key] = count(get_posts($count_args));
}

$total_discussions = count(get_posts(array('post_type' => 'mh_discussion', 'posts_per_page' => -1, 'fields' => 'ids', 'post_status' => 'publish')));
?>

<div class="mh-discussions-page">
    <div class="mh-page-header">
        <h1>ðŸ’¬ Discussions</h1>
        <p class="mh-subtitle">Join the microscopy community conversation</p>
    </div>

    <div class="mh-container">
        <?php if ($discussion_submitted): ?>
            <div class="mh-success-message">
                <strong>âœ“ Discussion posted!</strong> Your discussion has been added to the community.
            </div>
        <?php endif; ?>
        
        <?php if ($discussion_error): ?>
            <div class="mh-error-message">
                <strong>Error:</strong> <?php echo esc_html($discussion_error); ?>
            </div>
        <?php endif; ?>

        <div class="mh-discussions-layout">
            <aside class="mh-discussions-sidebar">
                <div class="mh-sidebar-widget">
                    <h3>ðŸ“ Categories</h3>
                    <ul class="mh-category-list">
                        <li class="mh-category-item <?php echo empty($category_filter) ? 'active' : ''; ?>">
                            <a href="<?php echo esc_url(remove_query_arg('category')); ?>">
                                <span class="mh-cat-icon">ðŸ“š</span>
                                <div>
                                    <strong>All Discussions</strong>
                                    <small><?php echo $total_discussions; ?> topics</small>
                                </div>
                            </a>
                        </li>
                        <?php foreach ($categories as $key => $cat): ?>
                        <li class="mh-category-item <?php echo $category_filter === $key ? 'active' : ''; ?>">
                            <a href="<?php echo esc_url(add_query_arg('category', $key)); ?>">
                                <span class="mh-cat-icon"><?php echo $cat['icon']; ?></span>
                                <div>
                                    <strong><?php echo esc_html($cat['name']); ?></strong>
                                    <small><?php echo $category_counts[$key]; ?> topics</small>
                                </div>
                            </a>
                        </li>
                        <?php endforeach; ?>
                    </ul>
                </div>
                
                <div class="mh-sidebar-widget">
                    <h3>ðŸ“Š Stats</h3>
                    <div class="mh-stats-list">
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">Total Discussions</span>
                            <span class="mh-stat-value"><?php echo $total_discussions; ?></span>
                        </div>
                        <div class="mh-stat-row">
                            <span class="mh-stat-label">Paper Comments</span>
                            <span class="mh-stat-value"><?php echo wp_count_comments()->approved; ?></span>
                        </div>
                    </div>
                </div>
                
                <div class="mh-sidebar-widget">
                    <h3>ðŸ”— Quick Links</h3>
                    <ul class="mh-quick-links">
                        <li><a href="<?php echo home_url('/'); ?>">Browse Papers</a></li>
                        <li><a href="<?php echo home_url('/protocols/'); ?>">Protocols</a></li>
                        <li><a href="<?php echo home_url('/contact/'); ?>">Contact Us</a></li>
                    </ul>
                </div>
            </aside>
            
            <div class="mh-discussions-main">
                <div class="mh-new-discussion-section">
                    <button type="button" id="mh-toggle-new-discussion" class="mh-btn mh-btn-primary">
                        âœï¸ Start New Discussion
                    </button>
                    
                    <div id="mh-new-discussion-form" class="mh-discussion-form" style="display: none;">
                        <h3>Start a New Discussion</h3>
                        <form method="post" action="">
                            <?php wp_nonce_field('mh_new_discussion', 'mh_discussion_nonce'); ?>
                            
                            <div class="mh-form-row">
                                <label for="discussion_title">Title *</label>
                                <input type="text" name="discussion_title" id="discussion_title" required placeholder="What's your question or topic?">
                            </div>
                            
                            <div class="mh-form-row">
                                <label for="discussion_category">Category</label>
                                <select name="discussion_category" id="discussion_category">
                                    <?php foreach ($categories as $key => $cat): ?>
                                        <option value="<?php echo esc_attr($key); ?>"><?php echo $cat['icon']; ?> <?php echo esc_html($cat['name']); ?></option>
                                    <?php endforeach; ?>
                                </select>
                            </div>
                            
                            <div class="mh-form-row">
                                <label for="discussion_content">Your Message *</label>
                                <textarea name="discussion_content" id="discussion_content" rows="5" required placeholder="Share your thoughts, questions, or ideas..."></textarea>
                            </div>
                            
                            <div class="mh-form-row-inline">
                                <div class="mh-form-row">
                                    <label for="author_name">Your Name *</label>
                                    <input type="text" name="author_name" id="author_name" required placeholder="Your name">
                                </div>
                                <div class="mh-form-row">
                                    <label for="author_email">Email *</label>
                                    <input type="email" name="author_email" id="author_email" required placeholder="your@email.com">
                                </div>
                            </div>
                            
                            <div class="mh-form-actions">
                                <button type="submit" name="mh_new_discussion" class="mh-btn mh-btn-primary">Post Discussion</button>
                                <button type="button" id="mh-cancel-discussion" class="mh-btn mh-btn-secondary">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
                
                <h2 class="mh-section-title">
                    <?php if ($category_filter && isset($categories[$category_filter])): ?>
                        <?php echo $categories[$category_filter]['icon']; ?> <?php echo $categories[$category_filter]['name']; ?> Discussions
                    <?php else: ?>
                        ðŸ’¬ All Discussions
                    <?php endif; ?>
                </h2>
                
                <?php if ($discussions): ?>
                    <div class="mh-discussions-list">
                        <?php foreach ($discussions as $discussion): 
                            $author_name = get_post_meta($discussion->ID, '_mh_author_name', true) ?: 'Anonymous';
                            $cat_key = get_post_meta($discussion->ID, '_mh_category', true) ?: 'qa';
                            $cat_info = isset($categories[$cat_key]) ? $categories[$cat_key] : $categories['qa'];
                            $comment_count = get_comments_number($discussion->ID);
                            $initials = strtoupper(substr($author_name, 0, 2));
                        ?>
                        <div class="mh-discussion-card">
                            <div class="mh-discussion-avatar"><?php echo esc_html($initials); ?></div>
                            <div class="mh-discussion-content">
                                <div class="mh-discussion-header">
                                    <span class="mh-discussion-category" title="<?php echo esc_attr($cat_info['name']); ?>">
                                        <?php echo $cat_info['icon']; ?>
                                    </span>
                                    <h3 class="mh-discussion-title">
                                        <a href="<?php echo get_permalink($discussion->ID); ?>">
                                            <?php echo esc_html($discussion->post_title); ?>
                                        </a>
                                    </h3>
                                </div>
                                <p class="mh-discussion-excerpt"><?php echo esc_html(wp_trim_words($discussion->post_content, 20)); ?></p>
                                <div class="mh-discussion-meta">
                                    <span class="mh-discussion-author"><?php echo esc_html($author_name); ?></span>
                                    <span class="mh-discussion-date"><?php echo human_time_diff(strtotime($discussion->post_date), current_time('timestamp')); ?> ago</span>
                                    <span class="mh-discussion-replies">ðŸ’¬ <?php echo $comment_count; ?> <?php echo $comment_count == 1 ? 'reply' : 'replies'; ?></span>
                                </div>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                <?php else: ?>
                    <div class="mh-no-discussions">
                        <span class="icon">ðŸ’¬</span>
                        <h3>No discussions yet</h3>
                        <p>Be the first to start a conversation!</p>
                    </div>
                <?php endif; ?>
                
                <?php if ($recent_paper_comments && !$category_filter): ?>
                    <h2 class="mh-section-title" style="margin-top: 40px;">ðŸ“„ Recent Paper Comments</h2>
                    <div class="mh-paper-comments-list">
                        <?php foreach ($recent_paper_comments as $comment): 
                            $post = get_post($comment->comment_post_ID);
                            if (!$post) continue;
                            $initials = strtoupper(substr($comment->comment_author, 0, 2));
                        ?>
                        <div class="mh-paper-comment-card">
                            <div class="mh-comment-avatar"><?php echo esc_html($initials); ?></div>
                            <div class="mh-comment-content">
                                <div class="mh-comment-meta">
                                    <span class="mh-comment-author"><?php echo esc_html($comment->comment_author); ?></span>
                                    <span class="mh-comment-date"><?php echo human_time_diff(strtotime($comment->comment_date), current_time('timestamp')); ?> ago</span>
                                </div>
                                <div class="mh-comment-text"><?php echo esc_html(wp_trim_words($comment->comment_content, 25)); ?></div>
                                <div class="mh-comment-paper">
                                    <a href="<?php echo get_permalink($post); ?>">
                                        ðŸ“„ <?php echo esc_html(wp_trim_words($post->post_title, 10)); ?>
                                    </a>
                                </div>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<style>
.mh-discussions-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
.mh-page-header { text-align: center; margin-bottom: 32px; }
.mh-page-header h1 { font-size: 2rem; margin: 0 0 8px 0; color: var(--text, #c9d1d9); }
.mh-subtitle { color: var(--text-muted, #8b949e); margin: 0; }

.mh-discussions-layout { display: grid; grid-template-columns: 280px 1fr; gap: 32px; }

.mh-success-message { background: #1f3d2d; border: 1px solid #56d364; color: #56d364; padding: 16px 20px; border-radius: 8px; margin-bottom: 24px; }
.mh-error-message { background: #3d1f1f; border: 1px solid #f85149; color: #f85149; padding: 16px 20px; border-radius: 8px; margin-bottom: 24px; }

.mh-discussions-sidebar { display: flex; flex-direction: column; gap: 24px; }
.mh-sidebar-widget { background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; padding: 16px; }
.mh-sidebar-widget h3 { margin: 0 0 12px 0; font-size: 0.95rem; color: var(--text, #c9d1d9); }

.mh-category-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.mh-category-item { border-radius: 8px; transition: background 0.2s; }
.mh-category-item a { display: flex; align-items: center; gap: 12px; padding: 12px; text-decoration: none; color: inherit; }
.mh-category-item:hover { background: var(--bg-hover, #21262d); }
.mh-category-item.active { background: var(--primary, #58a6ff); }
.mh-category-item.active a { color: #fff; }
.mh-category-item.active small { color: rgba(255,255,255,0.8); }
.mh-cat-icon { font-size: 1.5rem; }
.mh-category-item strong { display: block; font-size: 0.9rem; }
.mh-category-item small { color: var(--text-muted, #8b949e); font-size: 0.8rem; }

.mh-stats-list { display: flex; flex-direction: column; gap: 8px; }
.mh-stat-row { display: flex; justify-content: space-between; font-size: 0.9rem; }
.mh-stat-label { color: var(--text-muted, #8b949e); }
.mh-stat-value { color: var(--text, #c9d1d9); font-weight: 600; }

.mh-quick-links { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.mh-quick-links a { color: var(--primary, #58a6ff); text-decoration: none; }
.mh-quick-links a:hover { text-decoration: underline; }

.mh-new-discussion-section { margin-bottom: 24px; }
.mh-discussion-form { background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; padding: 24px; margin-top: 16px; }
.mh-discussion-form h3 { margin: 0 0 20px 0; color: var(--text, #c9d1d9); }

.mh-form-row { margin-bottom: 16px; }
.mh-form-row label { display: block; margin-bottom: 6px; color: var(--text-muted, #8b949e); font-size: 0.9rem; }
.mh-form-row input, .mh-form-row textarea, .mh-form-row select { width: 100%; padding: 10px 14px; background: var(--bg-hover, #21262d); border: 1px solid var(--border, #30363d); border-radius: 6px; color: var(--text, #c9d1d9); font-size: 0.95rem; font-family: inherit; }
.mh-form-row input:focus, .mh-form-row textarea:focus, .mh-form-row select:focus { outline: none; border-color: var(--primary, #58a6ff); }
.mh-form-row-inline { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.mh-form-actions { display: flex; gap: 12px; margin-top: 20px; }

.mh-btn { padding: 10px 20px; border-radius: 6px; font-weight: 500; cursor: pointer; border: none; font-size: 0.95rem; }
.mh-btn-primary { background: var(--primary, #58a6ff); color: #fff; }
.mh-btn-primary:hover { background: var(--primary-hover, #79b8ff); }
.mh-btn-secondary { background: var(--bg-hover, #21262d); color: var(--text, #c9d1d9); border: 1px solid var(--border, #30363d); }
.mh-btn-secondary:hover { background: var(--border, #30363d); }

.mh-section-title { margin: 24px 0 16px 0; font-size: 1.25rem; color: var(--text, #c9d1d9); }

.mh-discussions-list { display: flex; flex-direction: column; gap: 12px; }
.mh-discussion-card { display: flex; gap: 16px; padding: 20px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; transition: border-color 0.2s; }
.mh-discussion-card:hover { border-color: var(--primary, #58a6ff); }
.mh-discussion-avatar { width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, var(--primary, #58a6ff), #a371f7); display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; flex-shrink: 0; }
.mh-discussion-content { flex: 1; min-width: 0; }
.mh-discussion-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.mh-discussion-category { font-size: 1.25rem; }
.mh-discussion-title { margin: 0; font-size: 1.1rem; line-height: 1.3; }
.mh-discussion-title a { color: var(--text, #c9d1d9); text-decoration: none; }
.mh-discussion-title a:hover { color: var(--primary, #58a6ff); }
.mh-discussion-excerpt { color: var(--text-muted, #8b949e); font-size: 0.9rem; margin: 0 0 10px 0; line-height: 1.5; }
.mh-discussion-meta { display: flex; gap: 16px; font-size: 0.85rem; color: var(--text-light, #6e7681); }
.mh-discussion-replies { color: var(--primary, #58a6ff); }

.mh-paper-comments-list { display: flex; flex-direction: column; gap: 12px; }
.mh-paper-comment-card { display: flex; gap: 12px; padding: 16px; background: var(--bg-card, #161b22); border: 1px solid var(--border, #30363d); border-radius: 8px; }
.mh-comment-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--bg-hover, #21262d); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.85rem; color: var(--text-muted, #8b949e); flex-shrink: 0; }
.mh-comment-content { flex: 1; }
.mh-comment-meta { display: flex; gap: 12px; margin-bottom: 6px; font-size: 0.85rem; }
.mh-comment-author { font-weight: 600; color: var(--text, #c9d1d9); }
.mh-comment-date { color: var(--text-light, #6e7681); }
.mh-comment-text { color: var(--text-muted, #8b949e); line-height: 1.5; margin-bottom: 8px; }
.mh-comment-paper a { font-size: 0.85rem; color: var(--primary, #58a6ff); text-decoration: none; }
.mh-comment-paper a:hover { text-decoration: underline; }

.mh-no-discussions { text-align: center; padding: 60px 20px; background: var(--bg-card, #161b22); border-radius: 8px; }
.mh-no-discussions .icon { font-size: 3rem; display: block; margin-bottom: 16px; }
.mh-no-discussions h3 { margin: 0 0 8px 0; color: var(--text, #c9d1d9); }
.mh-no-discussions p { color: var(--text-muted, #8b949e); margin: 0; }

@media (max-width: 768px) {
    .mh-discussions-layout { grid-template-columns: 1fr; }
    .mh-discussions-sidebar { order: 2; }
    .mh-discussions-main { order: 1; }
    .mh-form-row-inline { grid-template-columns: 1fr; }
    .mh-discussion-card { flex-direction: column; }
    .mh-discussion-avatar { width: 40px; height: 40px; }
    .mh-discussion-meta { flex-wrap: wrap; gap: 8px; }
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('mh-toggle-new-discussion');
    const form = document.getElementById('mh-new-discussion-form');
    const cancelBtn = document.getElementById('mh-cancel-discussion');
    
    if (toggleBtn && form) {
        toggleBtn.addEventListener('click', function() {
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
            toggleBtn.style.display = form.style.display === 'none' ? 'block' : 'none';
        });
    }
    
    if (cancelBtn && form && toggleBtn) {
        cancelBtn.addEventListener('click', function() {
            form.style.display = 'none';
            toggleBtn.style.display = 'block';
        });
    }
});
</script>

<?php get_footer(); ?>
