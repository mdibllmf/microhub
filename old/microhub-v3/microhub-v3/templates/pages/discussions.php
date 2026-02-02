<?php
/**
 * Discussions Page Template for MicroHub
 * Forum-style discussions with topics and replies
 */

// Get discussions page URL
$discussions_url = mh_get_page_url('discussions');

// Handle new topic submission
$topic_created = false;
$topic_error = '';

if (isset($_POST['mh_create_topic']) && wp_verify_nonce($_POST['mh_topic_nonce'], 'mh_create_topic')) {
    $author_name = sanitize_text_field($_POST['topic_author']);
    $author_email = sanitize_email($_POST['topic_email']);
    $topic_title = sanitize_text_field($_POST['topic_title']);
    $topic_content = sanitize_textarea_field($_POST['topic_content']);
    $topic_category = sanitize_text_field($_POST['topic_category']);
    
    if (empty($author_name) || empty($topic_title) || empty($topic_content)) {
        $topic_error = 'Please fill in all required fields.';
    } else {
        $topic_data = array(
            'post_title' => $topic_title,
            'post_content' => $topic_content,
            'post_status' => 'publish',
            'post_type' => 'mh_discussion',
            'meta_input' => array(
                '_mh_discussion_author' => $author_name,
                '_mh_discussion_email' => $author_email,
                '_mh_discussion_category' => $topic_category,
                '_mh_discussion_views' => 0,
            ),
        );
        
        $topic_id = wp_insert_post($topic_data);
        if ($topic_id) {
            $topic_created = true;
        } else {
            $topic_error = 'Error creating topic. Please try again.';
        }
    }
}

// Handle reply submission
if (isset($_POST['mh_post_reply']) && wp_verify_nonce($_POST['mh_reply_nonce'], 'mh_post_reply')) {
    $reply_author = sanitize_text_field($_POST['reply_author']);
    $reply_content = sanitize_textarea_field($_POST['reply_content']);
    $topic_id = intval($_POST['topic_id']);
    
    if (!empty($reply_author) && !empty($reply_content) && $topic_id) {
        $comment_data = array(
            'comment_post_ID' => $topic_id,
            'comment_author' => $reply_author,
            'comment_content' => $reply_content,
            'comment_type' => 'mh_reply',
            'comment_approved' => 1,
        );
        wp_insert_comment($comment_data);
    }
}

// Get discussions
$paged = max(1, get_query_var('paged'));
$category_filter = isset($_GET['category']) ? sanitize_text_field($_GET['category']) : '';

$args = array(
    'post_type' => 'mh_discussion',
    'posts_per_page' => 15,
    'paged' => $paged,
    'orderby' => 'modified',
    'order' => 'DESC',
);

if ($category_filter) {
    $args['meta_query'] = array(
        array(
            'key' => '_mh_discussion_category',
            'value' => $category_filter,
        ),
    );
}

$discussions = new WP_Query($args);

// View single topic?
$view_topic = isset($_GET['topic']) ? intval($_GET['topic']) : 0;
if ($view_topic) {
    $topic = get_post($view_topic);
    if ($topic && $topic->post_type === 'mh_discussion') {
        // Increment view count
        $views = intval(get_post_meta($view_topic, '_mh_discussion_views', true));
        update_post_meta($view_topic, '_mh_discussion_views', $views + 1);
    } else {
        $view_topic = 0;
    }
}

$categories = array(
    'general' => '💬 General Discussion',
    'techniques' => '🔬 Techniques & Methods',
    'equipment' => '🔧 Equipment & Setup',
    'software' => '💻 Software & Analysis',
    'troubleshooting' => '🔍 Troubleshooting',
    'careers' => '👔 Careers & Training',
    'papers' => '📄 Paper Discussion',
);
?>
<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>
    <div class="mh-page-container mh-discussions-page">
        <header class="mh-page-header">
            <h1>💬 Discussion Forum</h1>
            <p class="mh-subtitle">Connect with the microscopy community</p>
        </header>

        <?php if ($view_topic && $topic) : ?>
            <!-- Single Topic View -->
            <div class="mh-topic-view">
                <a href="<?php echo esc_url($discussions_url); ?>" class="mh-back-link">← Back to Discussions</a>
                
                <article class="mh-topic-main">
                    <header class="mh-topic-header">
                        <span class="mh-topic-category"><?php echo esc_html($categories[get_post_meta($view_topic, '_mh_discussion_category', true)] ?? '💬 General'); ?></span>
                        <h2><?php echo esc_html($topic->post_title); ?></h2>
                        <div class="mh-topic-meta">
                            <span class="author">👤 <?php echo esc_html(get_post_meta($view_topic, '_mh_discussion_author', true) ?: 'Anonymous'); ?></span>
                            <span class="date">📅 <?php echo human_time_diff(strtotime($topic->post_date), current_time('timestamp')); ?> ago</span>
                            <span class="views">👁️ <?php echo number_format(get_post_meta($view_topic, '_mh_discussion_views', true)); ?> views</span>
                            <span class="replies">💬 <?php echo get_comments_number($view_topic); ?> replies</span>
                        </div>
                    </header>
                    
                    <div class="mh-topic-content">
                        <?php echo wpautop(esc_html($topic->post_content)); ?>
                    </div>
                </article>

                <!-- Replies -->
                <section class="mh-replies-section">
                    <h3>Replies</h3>
                    
                    <?php
                    $replies = get_comments(array(
                        'post_id' => $view_topic,
                        'status' => 'approve',
                        'order' => 'ASC',
                    ));
                    
                    if ($replies) :
                        foreach ($replies as $reply) :
                            $initials = strtoupper(substr($reply->comment_author, 0, 2));
                    ?>
                        <div class="mh-reply">
                            <div class="mh-reply-avatar"><?php echo $initials; ?></div>
                            <div class="mh-reply-content">
                                <div class="mh-reply-meta">
                                    <span class="author"><?php echo esc_html($reply->comment_author); ?></span>
                                    <span class="date"><?php echo human_time_diff(strtotime($reply->comment_date), current_time('timestamp')); ?> ago</span>
                                </div>
                                <div class="mh-reply-text">
                                    <?php echo wpautop(esc_html($reply->comment_content)); ?>
                                </div>
                            </div>
                        </div>
                    <?php 
                        endforeach;
                    else :
                    ?>
                        <p class="mh-no-replies">No replies yet. Be the first to respond!</p>
                    <?php endif; ?>

                    <!-- Reply Form -->
                    <div class="mh-reply-form-container">
                        <h4>Post a Reply</h4>
                        <form method="post" class="mh-reply-form">
                            <?php wp_nonce_field('mh_post_reply', 'mh_reply_nonce'); ?>
                            <input type="hidden" name="topic_id" value="<?php echo $view_topic; ?>">
                            
                            <div class="mh-form-group">
                                <label for="reply_author">Your Name <span class="required">*</span></label>
                                <input type="text" id="reply_author" name="reply_author" required placeholder="Enter your name">
                            </div>
                            
                            <div class="mh-form-group">
                                <label for="reply_content">Your Reply <span class="required">*</span></label>
                                <textarea id="reply_content" name="reply_content" rows="4" required placeholder="Share your thoughts..."></textarea>
                            </div>
                            
                            <button type="submit" name="mh_post_reply" class="mh-submit-btn">Post Reply</button>
                        </form>
                    </div>
                </section>
            </div>

        <?php else : ?>
            <!-- Discussion List View -->
            
            <?php if ($topic_created) : ?>
                <div class="mh-success-notice">
                    ✅ Your topic has been created successfully!
                </div>
            <?php endif; ?>

            <div class="mh-discussions-layout">
                <!-- Sidebar with categories and new topic -->
                <aside class="mh-discussions-sidebar">
                    <div class="mh-sidebar-card">
                        <h3>📂 Categories</h3>
                        <ul class="mh-category-list">
                            <li><a href="<?php echo esc_url($discussions_url); ?>" class="<?php echo !$category_filter ? 'active' : ''; ?>">All Topics</a></li>
                            <?php foreach ($categories as $slug => $name) : ?>
                                <li><a href="<?php echo add_query_arg('category', $slug, esc_url($discussions_url)); ?>" class="<?php echo $category_filter === $slug ? 'active' : ''; ?>"><?php echo esc_html($name); ?></a></li>
                            <?php endforeach; ?>
                        </ul>
                    </div>

                    <div class="mh-sidebar-card mh-new-topic-card">
                        <h3>✏️ Start a Discussion</h3>
                        
                        <?php if ($topic_error) : ?>
                            <div class="mh-error-notice"><?php echo esc_html($topic_error); ?></div>
                        <?php endif; ?>
                        
                        <form method="post" class="mh-new-topic-form">
                            <?php wp_nonce_field('mh_create_topic', 'mh_topic_nonce'); ?>
                            
                            <div class="mh-form-group">
                                <label for="topic_author">Your Name <span class="required">*</span></label>
                                <input type="text" id="topic_author" name="topic_author" required placeholder="Enter your name">
                            </div>
                            
                            <div class="mh-form-group">
                                <label for="topic_email">Email (optional)</label>
                                <input type="email" id="topic_email" name="topic_email" placeholder="For notifications">
                            </div>
                            
                            <div class="mh-form-group">
                                <label for="topic_category">Category</label>
                                <select id="topic_category" name="topic_category">
                                    <?php foreach ($categories as $slug => $name) : ?>
                                        <option value="<?php echo esc_attr($slug); ?>"><?php echo esc_html($name); ?></option>
                                    <?php endforeach; ?>
                                </select>
                            </div>
                            
                            <div class="mh-form-group">
                                <label for="topic_title">Topic Title <span class="required">*</span></label>
                                <input type="text" id="topic_title" name="topic_title" required placeholder="What's your question?">
                            </div>
                            
                            <div class="mh-form-group">
                                <label for="topic_content">Description <span class="required">*</span></label>
                                <textarea id="topic_content" name="topic_content" rows="4" required placeholder="Provide details..."></textarea>
                            </div>
                            
                            <button type="submit" name="mh_create_topic" class="mh-submit-btn">Create Topic</button>
                        </form>
                    </div>
                </aside>

                <!-- Main content - topic list -->
                <main class="mh-discussions-main">
                    <div class="mh-topics-header">
                        <h2><?php echo $category_filter ? esc_html($categories[$category_filter] ?? 'Topics') : 'Recent Discussions'; ?></h2>
                        <span class="mh-topic-count"><?php echo number_format($discussions->found_posts); ?> topics</span>
                    </div>

                    <?php if ($discussions->have_posts()) : ?>
                        <div class="mh-topics-list">
                            <?php while ($discussions->have_posts()) : $discussions->the_post(); 
                                $topic_author = get_post_meta(get_the_ID(), '_mh_discussion_author', true) ?: 'Anonymous';
                                $topic_cat = get_post_meta(get_the_ID(), '_mh_discussion_category', true);
                                $views = get_post_meta(get_the_ID(), '_mh_discussion_views', true);
                                $replies = get_comments_number();
                            ?>
                                <article class="mh-topic-item">
                                    <div class="mh-topic-avatar">
                                        <?php echo strtoupper(substr($topic_author, 0, 2)); ?>
                                    </div>
                                    <div class="mh-topic-info">
                                        <h3><a href="<?php echo add_query_arg('topic', get_the_ID(), esc_url($discussions_url)); ?>"><?php the_title(); ?></a></h3>
                                        <div class="mh-topic-meta">
                                            <span class="category"><?php echo esc_html($categories[$topic_cat] ?? '💬'); ?></span>
                                            <span class="author">by <?php echo esc_html($topic_author); ?></span>
                                            <span class="date"><?php echo human_time_diff(get_the_time('U'), current_time('timestamp')); ?> ago</span>
                                        </div>
                                    </div>
                                    <div class="mh-topic-stats">
                                        <div class="stat">
                                            <span class="number"><?php echo number_format($replies); ?></span>
                                            <span class="label">replies</span>
                                        </div>
                                        <div class="stat">
                                            <span class="number"><?php echo number_format($views); ?></span>
                                            <span class="label">views</span>
                                        </div>
                                    </div>
                                </article>
                            <?php endwhile; ?>
                        </div>

                        <!-- Pagination -->
                        <div class="mh-pagination">
                            <?php
                            echo paginate_links(array(
                                'total' => $discussions->max_num_pages,
                                'current' => $paged,
                                'prev_text' => '← Prev',
                                'next_text' => 'Next →',
                            ));
                            ?>
                        </div>
                    <?php else : ?>
                        <div class="mh-no-topics">
                            <span class="icon">💬</span>
                            <h3>No discussions yet</h3>
                            <p>Be the first to start a discussion! Use the form on the left to create a new topic.</p>
                            
                            <div class="mh-starter-topics" style="margin-top: 30px; text-align: left;">
                                <h4 style="color: #e6edf3; margin-bottom: 15px;">💡 Suggested Topics to Start:</h4>
                                <ul style="color: #8b949e; list-style: disc; padding-left: 25px;">
                                    <li style="margin-bottom: 8px;">What's the best confocal microscope for live cell imaging?</li>
                                    <li style="margin-bottom: 8px;">How do you optimize STED for deep tissue imaging?</li>
                                    <li style="margin-bottom: 8px;">Recommended settings for two-photon calcium imaging?</li>
                                    <li style="margin-bottom: 8px;">Best deconvolution software for spinning disk data?</li>
                                    <li style="margin-bottom: 8px;">Tips for expansion microscopy sample preparation</li>
                                </ul>
                            </div>
                        </div>
                    <?php endif; wp_reset_postdata(); ?>
                </main>
            </div>
        <?php endif; ?>
    </div>
</div>

<style>
.mh-discussions-page {
    max-width: 1200px;
}

.mh-discussions-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 30px;
}

@media (max-width: 900px) {
    .mh-discussions-layout {
        grid-template-columns: 1fr;
    }
}

.mh-sidebar-card {
    background: #161b22;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #30363d;
}

.mh-sidebar-card h3 {
    color: #e6edf3;
    font-size: 1.1rem;
    margin-bottom: 15px;
}

.mh-category-list {
    list-style: none !important;
    padding: 0 !important;
}

.mh-category-list li {
    margin-bottom: 5px;
}

.mh-category-list a {
    display: block;
    padding: 10px 12px;
    color: #8b949e;
    border-radius: 6px;
    transition: all 0.2s;
}

.mh-category-list a:hover,
.mh-category-list a.active {
    background: #21262d;
    color: #e6edf3;
}

.mh-topics-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.mh-topics-header h2 {
    color: #e6edf3;
    font-size: 1.3rem;
}

.mh-topic-count {
    color: #8b949e;
    font-size: 0.9rem;
}

.mh-topics-list {
    background: #161b22;
    border-radius: 12px;
    border: 1px solid #30363d;
    overflow: hidden;
}

.mh-topic-item {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid #21262d;
    gap: 15px;
}

.mh-topic-item:last-child {
    border-bottom: none;
}

.mh-topic-item:hover {
    background: #1c2128;
}

.mh-topic-avatar {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    background: linear-gradient(135deg, #238636, #2ea043);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: 600;
    font-size: 0.9rem;
    flex-shrink: 0;
}

.mh-topic-info {
    flex: 1;
    min-width: 0;
}

.mh-topic-info h3 {
    font-size: 1rem;
    margin-bottom: 5px;
}

.mh-topic-info h3 a {
    color: #e6edf3;
}

.mh-topic-info h3 a:hover {
    color: #58a6ff;
}

.mh-topic-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 0.8rem;
    color: #8b949e;
}

.mh-topic-stats {
    display: flex;
    gap: 20px;
    flex-shrink: 0;
}

.mh-topic-stats .stat {
    text-align: center;
}

.mh-topic-stats .number {
    display: block;
    font-size: 1.1rem;
    font-weight: 600;
    color: #e6edf3;
}

.mh-topic-stats .label {
    font-size: 0.75rem;
    color: #8b949e;
}

/* Single Topic View */
.mh-back-link {
    display: inline-block;
    color: #58a6ff;
    margin-bottom: 20px;
}

.mh-topic-main {
    background: #161b22;
    border-radius: 12px;
    padding: 25px;
    border: 1px solid #30363d;
    margin-bottom: 30px;
}

.mh-topic-header {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #30363d;
}

.mh-topic-category {
    display: inline-block;
    background: #21262d;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.8rem;
    color: #8b949e;
    margin-bottom: 10px;
}

.mh-topic-header h2 {
    color: #e6edf3;
    font-size: 1.5rem;
    margin-bottom: 10px;
}

.mh-topic-header .mh-topic-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    font-size: 0.85rem;
    color: #8b949e;
}

.mh-topic-content {
    color: #c9d1d9;
    line-height: 1.7;
}

.mh-replies-section {
    background: #161b22;
    border-radius: 12px;
    padding: 25px;
    border: 1px solid #30363d;
}

.mh-replies-section h3 {
    color: #e6edf3;
    margin-bottom: 20px;
}

.mh-reply {
    display: flex;
    gap: 15px;
    padding: 15px 0;
    border-bottom: 1px solid #21262d;
}

.mh-reply-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #30363d;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8b949e;
    font-weight: 600;
    font-size: 0.8rem;
    flex-shrink: 0;
}

.mh-reply-content {
    flex: 1;
}

.mh-reply-meta {
    display: flex;
    gap: 10px;
    font-size: 0.85rem;
    margin-bottom: 8px;
}

.mh-reply-meta .author {
    color: #e6edf3;
    font-weight: 500;
}

.mh-reply-meta .date {
    color: #8b949e;
}

.mh-reply-text {
    color: #c9d1d9;
    line-height: 1.6;
}

.mh-reply-form-container {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #30363d;
}

.mh-reply-form-container h4 {
    color: #e6edf3;
    margin-bottom: 15px;
}

/* Forms */
.mh-new-topic-form .mh-form-group,
.mh-reply-form .mh-form-group {
    margin-bottom: 15px;
}

.mh-new-topic-form label,
.mh-reply-form label {
    display: block;
    color: #e6edf3;
    font-size: 0.9rem;
    margin-bottom: 6px;
}

.required {
    color: #f85149;
}

.mh-new-topic-form input,
.mh-new-topic-form select,
.mh-new-topic-form textarea,
.mh-reply-form input,
.mh-reply-form textarea {
    width: 100%;
    padding: 10px 12px;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    font-family: inherit;
    font-size: 0.95rem;
}

.mh-new-topic-form input:focus,
.mh-new-topic-form select:focus,
.mh-new-topic-form textarea:focus,
.mh-reply-form input:focus,
.mh-reply-form textarea:focus {
    outline: none;
    border-color: #58a6ff;
}

.mh-submit-btn {
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #238636, #2ea043);
    border: none;
    border-radius: 6px;
    color: #fff;
    font-weight: 600;
    cursor: pointer;
}

.mh-submit-btn:hover {
    background: linear-gradient(135deg, #2ea043, #3fb950);
}

.mh-no-topics {
    text-align: center;
    padding: 60px 20px;
    background: #161b22;
    border-radius: 12px;
    border: 1px solid #30363d;
}

.mh-no-topics .icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 15px;
}

.mh-no-topics h3 {
    color: #e6edf3;
    margin-bottom: 10px;
}

.mh-no-topics p {
    color: #8b949e;
}

.mh-success-notice {
    background: rgba(46, 160, 67, 0.15);
    border: 1px solid #238636;
    color: #3fb950;
    padding: 15px 20px;
    border-radius: 6px;
    margin-bottom: 20px;
}

.mh-error-notice {
    background: rgba(248, 81, 73, 0.1);
    border: 1px solid #f85149;
    color: #f85149;
    padding: 10px 15px;
    border-radius: 6px;
    margin-bottom: 15px;
    font-size: 0.9rem;
}

.mh-no-replies {
    color: #8b949e;
    text-align: center;
    padding: 30px;
}
</style>
