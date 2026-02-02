<?php
/**
 * Template Name: Contact Page
 * 
 * This template displays a contact form with editable sidebar content.
 * Edit the page content in WordPress: Pages → Contact → Edit
 * The page content will appear in the sidebar area.
 */
get_header();

// Handle form submission
$form_status = '';
if (isset($_POST['mh_contact_submit'])) {
    if (wp_verify_nonce($_POST['mh_contact_nonce'], 'mh_contact_action')) {
        $name = sanitize_text_field($_POST['mh_name'] ?? '');
        $email = sanitize_email($_POST['mh_email'] ?? '');
        $subject = sanitize_text_field($_POST['mh_subject'] ?? '');
        $message = sanitize_textarea_field($_POST['mh_message'] ?? '');
        
        if (!empty($name) && !empty($email) && !empty($message)) {
            $admin_email = get_option('admin_email');
            $email_subject = '[MicroHub] ' . ($subject ?: 'Contact Form') . ' from ' . $name;
            $email_body = "Name: $name\nEmail: $email\nSubject: $subject\n\nMessage:\n$message";
            
            if (wp_mail($admin_email, $email_subject, $email_body, array("Reply-To: $email"))) {
                $form_status = 'success';
            } else {
                $form_status = 'error';
            }
        } else {
            $form_status = 'error';
        }
    }
}

$subjects = array(
    'General Inquiry',
    'Paper Submission',
    'Protocol Upload',
    'Bug Report',
    'Feature Request',
    'Collaboration',
    'Data Request',
    'Other'
);
?>

<div class="mh-page-header">
    <h1><?php the_title(); ?></h1>
    <?php if (has_excerpt()): ?>
        <p class="mh-page-subtitle"><?php echo get_the_excerpt(); ?></p>
    <?php else: ?>
        <p class="mh-page-subtitle">We'd love to hear from you</p>
    <?php endif; ?>
</div>

<div class="mh-container">
    <div class="mh-contact-layout">
        <!-- Info Sidebar - Content from WordPress Editor -->
        <div>
            <?php if (have_posts()): while (have_posts()): the_post(); ?>
                <?php if (get_the_content()): ?>
                <div class="mh-info-card mh-page-content">
                    <?php the_content(); ?>
                </div>
                <?php else: ?>
                <!-- Default content if page is empty -->
                <div class="mh-info-card">
                    <h3>📬 Get In Touch</h3>
                    <p style="color: var(--text-light);">Have a question about MicroHub? Want to contribute a paper or protocol? We're here to help!</p>
                </div>
                
                <div class="mh-info-card">
                    <h3>💡 Common Topics</h3>
                    <ul>
                        <li>Submitting papers to the database</li>
                        <li>Uploading protocols</li>
                        <li>Reporting bugs or issues</li>
                        <li>Feature requests</li>
                        <li>Collaboration opportunities</li>
                    </ul>
                </div>
                <?php endif; ?>
            <?php endwhile; endif; ?>
            
            <div class="mh-info-card">
                <h3>🔗 Quick Links</h3>
                <ul>
                    <li><a href="https://github.com/microhub" target="_blank">GitHub Repository</a></li>
                    <li><a href="<?php echo esc_url(mh_get_page_urls()['discussions']); ?>">Community Discussions</a></li>
                    <li><a href="<?php echo esc_url(mh_get_page_urls()['about']); ?>">About MicroHub</a></li>
                </ul>
            </div>
        </div>
        
        <!-- Contact Form -->
        <div class="mh-contact-form-container">
            <?php if ($form_status === 'success'): ?>
                <div class="mh-success-notice">
                    ✅ Thank you for your message! We'll get back to you soon.
                </div>
            <?php elseif ($form_status === 'error'): ?>
                <div class="mh-error-notice">
                    ❌ There was an error sending your message. Please try again.
                </div>
            <?php endif; ?>
            
            <form method="post" class="mh-about-section">
                <h3 style="margin-bottom: 20px;">Send us a Message</h3>
                <?php wp_nonce_field('mh_contact_action', 'mh_contact_nonce'); ?>
                
                <div class="mh-form-row">
                    <div class="mh-form-group">
                        <label for="mh_name">Name <span class="required">*</span></label>
                        <input type="text" id="mh_name" name="mh_name" required placeholder="Your name">
                    </div>
                    <div class="mh-form-group">
                        <label for="mh_email">Email <span class="required">*</span></label>
                        <input type="email" id="mh_email" name="mh_email" required placeholder="your@email.com">
                    </div>
                </div>
                
                <div class="mh-form-group">
                    <label for="mh_subject">Subject</label>
                    <select id="mh_subject" name="mh_subject">
                        <option value="">Select a topic...</option>
                        <?php foreach ($subjects as $subject): ?>
                            <option value="<?php echo esc_attr($subject); ?>"><?php echo esc_html($subject); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                
                <div class="mh-form-group">
                    <label for="mh_message">Message <span class="required">*</span></label>
                    <textarea id="mh_message" name="mh_message" rows="6" required placeholder="How can we help you?"></textarea>
                </div>
                
                <button type="submit" name="mh_contact_submit" class="mh-submit-btn">Send Message</button>
            </form>
        </div>
    </div>
</div>

<style>
/* Page content styling */
.mh-page-content h3 { font-size: 1.1rem; margin-bottom: 16px; }
.mh-page-content p { color: var(--text-light); line-height: 1.7; margin-bottom: 12px; }
.mh-page-content ul { margin: 0; }
.mh-page-content ul li { padding: 8px 0; color: var(--text-light); border-bottom: 1px solid var(--border); }
.mh-page-content ul li:last-child { border-bottom: none; }
.mh-page-content a { color: var(--primary); }
</style>

<?php get_footer(); ?>
