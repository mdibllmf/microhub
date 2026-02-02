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
$reply_posted = false;
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
        $comment_id = wp_insert_comment($comment_data);
        
        if ($comment_id) {
            $redirect_url = add_query_arg(array(
                'topic' => $topic_id,
                'reply_posted' => '1'
            ), $discussions_url);
            wp_safe_redirect($redirect_url);
            exit;
        }
    }
}

$reply_posted = isset($_GET['reply_posted']) && $_GET['reply_posted'] === '1';

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
$topic = null;
if ($view_topic) {
    $topic = get_post($view_topic);
    if ($topic && $topic->post_type === 'mh_discussion') {
        $views = intval(get_post_meta($view_topic, '_mh_discussion_views', true));
        update_post_meta($view_topic, '_mh_discussion_views', $views + 1);
    } else {
        $view_topic = 0;
        $topic = null;
    }
}

$categories = array(
    'general' => 'General Discussion',
    'techniques' => 'Techniques and Methods',
    'equipment' => 'Equipment and Setup',
    'software' => 'Software and Analysis',
    'troubleshooting' => 'Troubleshooting',
    'careers' => 'Careers and Training',
    'papers' => 'Paper Discussion',
);
?>
<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>
    <div class="mh-page-container mh-discussions-page">
        <header class="mh-page-header">
            <h1>Discussion Forum</h1>
            <p class="mh-subtitle">Connect with the microscopy community</p>
        </header>

        <?php if ($view_topic && $topic) : ?>
            <!-- Single Topic View -->
            <div class="mh-topic-view">
                <a href="<?php echo esc_url($discussions_url); ?>" class="mh-back-link">Back to Discussions</a>
                
                <article class="mh-topic-main">
                    <header class="mh-topic-header">
                        <?php 
                        $cat_key = get_post_meta($view_topic, '_mh_discussion_category', true);
                        $cat_label = isset($categories[$cat_key]) ? $categories[$cat_key] : 'General';
                        ?>
                        <span class="mh-topic-category"><?php echo esc_html($cat_label); ?></span>
                        <h2><?php echo esc_html($topic->post_title); ?></h2>
                        <div class="mh-topic-meta">
                            <span class="author"><?php echo esc_html(get_post_meta($view_topic, '_mh_discussion_author', true) ? get_post_meta($view_topic, '_mh_discussion_author', true) : 'Anonymous'); ?></span>
                            <span class="date"><?php echo human_time_diff(strtotime($topic->post_date), current_time('timestamp')); ?> ago</span>
                            <span class="views"><?php echo number_format(get_post_meta($view_topic, '_mh_discussion_views', true)); ?> views</span>
                            <span class="replies"><?php echo get_comments_number($view_topic); ?> replies</span>
                        </div>
                    </header>
                    
                    <div class="mh-topic-content">
                        <?php echo wpautop(esc_html($topic->post_content)); ?>
                    </div>
                </article>

                <!-- Replies -->
                <section class="mh-replies-section">
                    <h3>Replies</h3>
                    
                    <?php if ($reply_posted) : ?>
                        <div class="mh-success-notice">
                            Your reply has been posted successfully!
                        </div>
                    <?php endif; ?>
                    
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
                            <div class="mh-reply-avatar"><?php echo esc_html($initials); ?></div>
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
                        <form method="post" action="<?php echo esc_url(add_query_arg('topic', $view_topic, $discussions_url)); ?>" class="mh-reply-form">
                            <?php wp_nonce_field('mh_post_reply', 'mh_reply_nonce'); ?>
                            <input type="hidden" name="topic_id" value="<?php echo intval($view_topic); ?>">
                            
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
                    Your topic has been created successfully!
                </div>
            <?php endif; ?>

            <div class="mh-discussions-layout">
                <!-- Sidebar with categories and new topic -->
                <aside class="mh-discussions-sidebar">
                    <div class="mh-sidebar-card">
                        <h3>Categories</h3>
                        <ul class="mh-category-list">
                            <li><a href="<?php echo esc_url($discussions_url); ?>" class="<?php echo !$category_filter ? 'active' : ''; ?>">All Topics</a></li>
                            <?php foreach ($categories as $slug => $name) : ?>
                                <li><a href="<?php echo add_query_arg('category', $slug, esc_url($discussions_url)); ?>" class="<?php echo $category_filter === $slug ? 'active' : ''; ?>"><?php echo esc_html($name); ?></a></li>
                            <?php endforeach; ?>
                        </ul>
                    </div>

                    <div class="mh-sidebar-card mh-new-topic-card">
                        <h3>Start a Discussion</h3>
                        
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
                                <input type="text" id="topic_title" name="topic_title" required placeholder="What is your question?">
                            </div>
                            
                            <div class="mh-form-group">
                                <label for="topic_content">Details <span class="required">*</span></label>
                                <textarea id="topic_content" name="topic_content" rows="5" required placeholder="Provide more details..."></textarea>
                            </div>
                            
                            <button type="submit" name="mh_create_topic" class="mh-submit-btn">Create Topic</button>
                        </form>
                    </div>
                </aside>

                <!-- Main content - Topics list -->
                <main class="mh-discussions-main">
                    <div class="mh-topics-header">
                        <h2><?php echo $category_filter ? esc_html($categories[$category_filter]) : 'All Topics'; ?></h2>
                        <span class="mh-topic-count"><?php echo $discussions->found_posts; ?> topics</span>
                    </div>

                    <?php if ($discussions->have_posts()) : ?>
                        <div class="mh-topics-list">
                            <?php while ($discussions->have_posts()) : $discussions->the_post(); 
                                $author = get_post_meta(get_the_ID(), '_mh_discussion_author', true);
                                if (empty($author)) $author = 'Anonymous';
                                $cat_key = get_post_meta(get_the_ID(), '_mh_discussion_category', true);
                                $cat_label = isset($categories[$cat_key]) ? $categories[$cat_key] : 'General';
                                $views = intval(get_post_meta(get_the_ID(), '_mh_discussion_views', true));
                                $replies = get_comments_number();
                                $initials = strtoupper(substr($author, 0, 2));
                            ?>
                                <div class="mh-topic-item">
                                    <div class="mh-topic-avatar"><?php echo esc_html($initials); ?></div>
                                    <div class="mh-topic-info">
                                        <h3><a href="<?php echo add_query_arg('topic', get_the_ID(), $discussions_url); ?>"><?php the_title(); ?></a></h3>
                                        <div class="mh-topic-meta">
                                            <span class="category"><?php echo esc_html($cat_label); ?></span>
                                            <span class="author">by <?php echo esc_html($author); ?></span>
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
                                </div>
                            <?php endwhile; ?>
                        </div>

                        <!-- Pagination -->
                        <?php if ($discussions->max_num_pages > 1) : ?>
                            <div class="mh-pagination" style="margin-top: 20px; text-align: center;">
                                <?php
                                echo paginate_links(array(
                                    'total' => $discussions->max_num_pages,
                                    'current' => $paged,
                                    'prev_text' => 'Previous',
                                    'next_text' => 'Next',
                                ));
                                ?>
                            </div>
                        <?php endif; ?>

                    <?php else : ?>
                        <div class="mh-no-topics">
                            <span class="icon">💬</span>
                            <h3>No discussions yet</h3>
                            <p>Be the first to start a conversation!</p>
                        </div>
                    <?php endif; ?>
                    <?php wp_reset_postdata(); ?>
                </main>
            </div>
        <?php endif; ?>
    </div>
</div>
