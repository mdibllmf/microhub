<?php
/**
 * Single Discussion Template
 * Displays a single discussion with replies and comment form
 */
get_header();

// Get discussion data
$author_name = get_post_meta(get_the_ID(), '_mh_author_name', true) ?: 'Anonymous';
$author_email = get_post_meta(get_the_ID(), '_mh_author_email', true);
$category_key = get_post_meta(get_the_ID(), '_mh_category', true) ?: 'qa';

// Category info
$categories = array(
    'techniques' => array('icon' => '🔬', 'name' => 'Techniques'),
    'software' => array('icon' => '💻', 'name' => 'Software'),
    'protocols' => array('icon' => '📋', 'name' => 'Protocols'),
    'qa' => array('icon' => '❓', 'name' => 'Q&A'),
    'announcements' => array('icon' => '📢', 'name' => 'Announcements'),
    'ideas' => array('icon' => '💡', 'name' => 'Ideas'),
);

$cat_info = isset($categories[$category_key]) ? $categories[$category_key] : $categories['qa'];
$initials = strtoupper(substr($author_name, 0, 2));

// Get replies
$replies = get_comments(array(
    'post_id' => get_the_ID(),
    'status' => 'approve',
    'orderby' => 'comment_date',
    'order' => 'ASC',
));

// Handle reply submission
$reply_submitted = false;
$reply_error = '';

if (isset($_POST['mh_submit_reply']) && wp_verify_nonce($_POST['mh_reply_nonce'], 'mh_submit_reply')) {
    $reply_content = sanitize_textarea_field($_POST['reply_content']);
    $reply_author = sanitize_text_field($_POST['reply_author']);
    $reply_email = sanitize_email($_POST['reply_email']);
    
    if (empty($reply_content) || empty($reply_author) || empty($reply_email)) {
        $reply_error = 'Please fill in all required fields.';
    } elseif (!is_email($reply_email)) {
        $reply_error = 'Please enter a valid email address.';
    } else {
        $comment_data = array(
            'comment_post_ID' => get_the_ID(),
            'comment_content' => $reply_content,
            'comment_author' => $reply_author,
            'comment_author_email' => $reply_email,
            'comment_approved' => 1, // Auto-approve
        );
        
        $comment_id = wp_insert_comment($comment_data);
        
        if ($comment_id) {
            $reply_submitted = true;
            // Refresh replies
            $replies = get_comments(array(
                'post_id' => get_the_ID(),
                'status' => 'approve',
                'orderby' => 'comment_date',
                'order' => 'ASC',
            ));
        } else {
            $reply_error = 'Error posting reply. Please try again.';
        }
    }
}
?>

<div class="mh-single-discussion">
    <div class="mh-discussion-nav">
        <a href="<?php echo esc_url(mh_get_page_url('discussions')); ?>" class="mh-back-link">
            ← Back to Discussions
        </a>
    </div>

    <?php while (have_posts()) : the_post(); ?>
        <article class="mh-discussion-article">
            <!-- Discussion Header -->
            <header class="mh-discussion-header">
                <span class="mh-discussion-category-badge">
                    <?php echo $cat_info['icon']; ?> <?php echo esc_html($cat_info['name']); ?>
                </span>
                <h1 class="mh-discussion-title"><?php the_title(); ?></h1>
                <div class="mh-discussion-meta">
                    <div class="mh-author-info">
                        <span class="mh-author-avatar"><?php echo esc_html($initials); ?></span>
                        <span class="mh-author-name"><?php echo esc_html($author_name); ?></span>
                    </div>
                    <span class="mh-post-date">
                        Posted <?php echo human_time_diff(get_the_time('U'), current_time('timestamp')); ?> ago
                    </span>
                    <span class="mh-reply-count">
                        💬 <?php echo count($replies); ?> <?php echo count($replies) === 1 ? 'reply' : 'replies'; ?>
                    </span>
                </div>
            </header>

            <!-- Discussion Content -->
            <div class="mh-discussion-body">
                <?php the_content(); ?>
            </div>
        </article>

        <!-- Replies Section -->
        <section class="mh-replies-section">
            <h2>💬 Replies (<?php echo count($replies); ?>)</h2>
            
            <?php if ($reply_submitted): ?>
                <div class="mh-success-message">
                    <strong>✓ Reply posted!</strong> Your reply has been added to the discussion.
                </div>
            <?php endif; ?>
            
            <?php if ($reply_error): ?>
                <div class="mh-error-message">
                    <strong>Error:</strong> <?php echo esc_html($reply_error); ?>
                </div>
            <?php endif; ?>

            <?php if ($replies): ?>
                <div class="mh-replies-list">
                    <?php foreach ($replies as $index => $reply): 
                        $reply_initials = strtoupper(substr($reply->comment_author, 0, 2));
                    ?>
                        <div class="mh-reply-card" id="reply-<?php echo $reply->comment_ID; ?>">
                            <div class="mh-reply-number">#<?php echo $index + 1; ?></div>
                            <div class="mh-reply-avatar"><?php echo esc_html($reply_initials); ?></div>
                            <div class="mh-reply-content">
                                <div class="mh-reply-header">
                                    <span class="mh-reply-author"><?php echo esc_html($reply->comment_author); ?></span>
                                    <span class="mh-reply-date"><?php echo human_time_diff(strtotime($reply->comment_date), current_time('timestamp')); ?> ago</span>
                                </div>
                                <div class="mh-reply-text">
                                    <?php echo nl2br(esc_html($reply->comment_content)); ?>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php else: ?>
                <div class="mh-no-replies">
                    <p>No replies yet. Be the first to respond!</p>
                </div>
            <?php endif; ?>

            <!-- Reply Form -->
            <div class="mh-reply-form-section">
                <h3>📝 Post a Reply</h3>
                <form method="post" action="" class="mh-reply-form">
                    <?php wp_nonce_field('mh_submit_reply', 'mh_reply_nonce'); ?>
                    
                    <div class="mh-form-row">
                        <label for="reply_content">Your Reply *</label>
                        <textarea name="reply_content" id="reply_content" rows="5" required placeholder="Share your thoughts, ask follow-up questions, or provide helpful information..."></textarea>
                    </div>
                    
                    <div class="mh-form-row-inline">
                        <div class="mh-form-row">
                            <label for="reply_author">Your Name *</label>
                            <input type="text" name="reply_author" id="reply_author" required placeholder="Your name">
                        </div>
                        <div class="mh-form-row">
                            <label for="reply_email">Email *</label>
                            <input type="email" name="reply_email" id="reply_email" required placeholder="your@email.com">
                            <small class="mh-form-help">Email will not be displayed publicly</small>
                        </div>
                    </div>
                    
                    <div class="mh-form-actions">
                        <button type="submit" name="mh_submit_reply" class="mh-btn mh-btn-primary">
                            Post Reply
                        </button>
                    </div>
                </form>
            </div>
        </section>
    <?php endwhile; ?>
</div>

<style>
.mh-single-discussion {
    max-width: 900px;
    margin: 0 auto;
    padding: 24px;
}

/* Navigation */
.mh-discussion-nav {
    margin-bottom: 24px;
}
.mh-back-link {
    color: var(--text-muted, #8b949e);
    text-decoration: none;
    font-size: 0.9rem;
}
.mh-back-link:hover {
    color: var(--primary, #58a6ff);
}

/* Discussion Article */
.mh-discussion-article {
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 12px;
    padding: 32px;
    margin-bottom: 32px;
}
.mh-discussion-category-badge {
    display: inline-block;
    padding: 6px 12px;
    background: var(--bg-hover, #21262d);
    border-radius: 20px;
    font-size: 0.85rem;
    color: var(--text-muted, #8b949e);
    margin-bottom: 16px;
}
.mh-discussion-title {
    font-size: 1.75rem;
    margin: 0 0 16px 0;
    color: var(--text, #c9d1d9);
    line-height: 1.3;
}
.mh-discussion-meta {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border, #30363d);
    margin-bottom: 20px;
}
.mh-author-info {
    display: flex;
    align-items: center;
    gap: 10px;
}
.mh-author-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary, #58a6ff), #a371f7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    color: #fff;
}
.mh-author-name {
    font-weight: 600;
    color: var(--text, #c9d1d9);
}
.mh-post-date,
.mh-reply-count {
    color: var(--text-light, #6e7681);
    font-size: 0.9rem;
}
.mh-reply-count {
    color: var(--primary, #58a6ff);
}
.mh-discussion-body {
    color: var(--text-light, #8b949e);
    line-height: 1.7;
    font-size: 1rem;
}
.mh-discussion-body p {
    margin-bottom: 16px;
}

/* Replies Section */
.mh-replies-section {
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 12px;
    padding: 32px;
}
.mh-replies-section h2 {
    margin: 0 0 24px 0;
    font-size: 1.25rem;
    color: var(--text, #c9d1d9);
}

/* Messages */
.mh-success-message {
    background: #1f3d2d;
    border: 1px solid #56d364;
    color: #56d364;
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}
.mh-error-message {
    background: #3d1f1f;
    border: 1px solid #f85149;
    color: #f85149;
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}

/* Replies List */
.mh-replies-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 32px;
}
.mh-reply-card {
    display: flex;
    gap: 16px;
    padding: 20px;
    background: var(--bg-hover, #21262d);
    border-radius: 8px;
    position: relative;
}
.mh-reply-number {
    position: absolute;
    top: 8px;
    right: 12px;
    font-size: 0.75rem;
    color: var(--text-light, #6e7681);
}
.mh-reply-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--border, #30363d);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-muted, #8b949e);
    flex-shrink: 0;
}
.mh-reply-content {
    flex: 1;
    min-width: 0;
}
.mh-reply-header {
    display: flex;
    gap: 12px;
    margin-bottom: 8px;
    align-items: center;
}
.mh-reply-author {
    font-weight: 600;
    color: var(--text, #c9d1d9);
}
.mh-reply-date {
    color: var(--text-light, #6e7681);
    font-size: 0.85rem;
}
.mh-reply-text {
    color: var(--text-light, #8b949e);
    line-height: 1.6;
}

/* No Replies */
.mh-no-replies {
    text-align: center;
    padding: 40px;
    color: var(--text-muted, #8b949e);
    background: var(--bg-hover, #21262d);
    border-radius: 8px;
    margin-bottom: 32px;
}

/* Reply Form */
.mh-reply-form-section {
    border-top: 1px solid var(--border, #30363d);
    padding-top: 24px;
}
.mh-reply-form-section h3 {
    margin: 0 0 20px 0;
    font-size: 1.1rem;
    color: var(--text, #c9d1d9);
}
.mh-reply-form {
    background: var(--bg-hover, #21262d);
    border-radius: 8px;
    padding: 24px;
}
.mh-form-row {
    margin-bottom: 16px;
}
.mh-form-row label {
    display: block;
    margin-bottom: 6px;
    color: var(--text-muted, #8b949e);
    font-size: 0.9rem;
}
.mh-form-row input,
.mh-form-row textarea {
    width: 100%;
    padding: 12px 14px;
    background: var(--bg-card, #161b22);
    border: 1px solid var(--border, #30363d);
    border-radius: 6px;
    color: var(--text, #c9d1d9);
    font-size: 0.95rem;
    font-family: inherit;
}
.mh-form-row input:focus,
.mh-form-row textarea:focus {
    outline: none;
    border-color: var(--primary, #58a6ff);
}
.mh-form-help {
    display: block;
    margin-top: 4px;
    font-size: 0.8rem;
    color: var(--text-light, #6e7681);
}
.mh-form-row-inline {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
.mh-form-actions {
    margin-top: 20px;
}
.mh-btn {
    padding: 12px 24px;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    font-size: 0.95rem;
}
.mh-btn-primary {
    background: var(--primary, #58a6ff);
    color: #fff;
}
.mh-btn-primary:hover {
    background: var(--primary-hover, #79b8ff);
}

/* Responsive */
@media (max-width: 768px) {
    .mh-single-discussion {
        padding: 16px;
    }
    .mh-discussion-article,
    .mh-replies-section {
        padding: 20px;
    }
    .mh-discussion-title {
        font-size: 1.4rem;
    }
    .mh-discussion-meta {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
    .mh-form-row-inline {
        grid-template-columns: 1fr;
    }
    .mh-reply-card {
        flex-direction: column;
    }
}
</style>

<?php get_footer(); ?>
