<?php
/**
 * Contact Page Template for MicroHub
 */

// Get page URLs
$urls = mh_get_all_urls();

// Handle form submission
$message_sent = false;
$error_message = '';

if (isset($_POST['mh_contact_submit']) && wp_verify_nonce($_POST['mh_contact_nonce'], 'mh_contact_form')) {
    $name = sanitize_text_field($_POST['contact_name']);
    $email = sanitize_email($_POST['contact_email']);
    $subject = sanitize_text_field($_POST['contact_subject']);
    $message = sanitize_textarea_field($_POST['contact_message']);
    
    if (empty($name) || empty($email) || empty($message)) {
        $error_message = 'Please fill in all required fields.';
    } elseif (!is_email($email)) {
        $error_message = 'Please enter a valid email address.';
    } else {
        // Get admin email
        $admin_email = get_option('admin_email');
        
        // Send email
        $email_subject = '[MicroHub Contact] ' . ($subject ? $subject : 'New Message');
        $email_body = "Name: $name\n";
        $email_body .= "Email: $email\n";
        $email_body .= "Subject: $subject\n\n";
        $email_body .= "Message:\n$message";
        
        $headers = array(
            'From: ' . $name . ' <' . $email . '>',
            'Reply-To: ' . $email,
        );
        
        if (wp_mail($admin_email, $email_subject, $email_body, $headers)) {
            $message_sent = true;
            
            // Also save to database as a comment/record
            $contact_data = array(
                'post_title' => 'Contact: ' . $subject,
                'post_content' => $message,
                'post_status' => 'private',
                'post_type' => 'mh_contact',
                'meta_input' => array(
                    '_mh_contact_name' => $name,
                    '_mh_contact_email' => $email,
                    '_mh_contact_subject' => $subject,
                ),
            );
            wp_insert_post($contact_data);
        } else {
            $error_message = 'There was an error sending your message. Please try again.';
        }
    }
}
?>
<div class="microhub-wrapper">
    <?php echo mh_render_nav(); ?>
    <div class="mh-page-container mh-contact-page">
        <header class="mh-page-header">
            <h1>Contact Us</h1>
            <p class="mh-subtitle">We'd love to hear from you</p>
        </header>

        <div class="mh-contact-layout">
            <div class="mh-contact-info">
                <div class="mh-info-card">
                    <h3>ðŸ“§ Get In Touch</h3>
                    <p>Have questions about MicroHub? Want to suggest a feature or report an issue? Fill out the form and we'll get back to you as soon as possible.</p>
                </div>
                
                <div class="mh-info-card">
                    <h3>ðŸ’¡ Common Topics</h3>
                    <ul>
                        <li>ðŸ”¬ <strong>Paper Submissions</strong> - Submit papers we may have missed</li>
                        <li>ðŸ“‹ <strong>Protocol Uploads</strong> - Share your protocols with the community</li>
                        <li>ðŸ› <strong>Bug Reports</strong> - Help us improve the platform</li>
                        <li>ðŸ¤ <strong>Collaborations</strong> - Partner with us on research initiatives</li>
                        <li>ðŸ“Š <strong>Data Requests</strong> - Custom data exports or API access</li>
                    </ul>
                </div>

                <div class="mh-info-card">
                    <h3>ðŸ”— Quick Links</h3>
                    <ul>
                        <li><a href="<?php echo esc_url($urls['discussions']); ?>">ðŸ’¬ Discussion Forum</a></li>
                        <li><a href="<?php echo esc_url($urls['upload-protocol']); ?>">ðŸ“¤ Upload Protocol</a></li>
                        <li><a href="<?php echo esc_url($urls['upload-paper']); ?>">ðŸ“„ Submit Paper</a></li>
                        <li><a href="<?php echo esc_url($urls['about']); ?>">â„¹ï¸ About MicroHub</a></li>
                    </ul>
                </div>
            </div>

            <div class="mh-contact-form-container">
                <?php if ($message_sent) : ?>
                    <div class="mh-success-message">
                        <span class="icon">âœ…</span>
                        <h3>Message Sent!</h3>
                        <p>Thank you for contacting us. We'll respond to your inquiry as soon as possible.</p>
                        <a href="<?php echo esc_url($urls['microhub']); ?>" class="mh-btn">Return to Home</a>
                    </div>
                <?php else : ?>
                    <?php if ($error_message) : ?>
                        <div class="mh-error-message">
                            <span class="icon">âš ï¸</span>
                            <?php echo esc_html($error_message); ?>
                        </div>
                    <?php endif; ?>
                    
                    <form method="post" class="mh-contact-form">
                        <?php wp_nonce_field('mh_contact_form', 'mh_contact_nonce'); ?>
                        
                        <div class="mh-form-group">
                            <label for="contact_name">Your Name <span class="required">*</span></label>
                            <input type="text" id="contact_name" name="contact_name" required 
                                   value="<?php echo isset($_POST['contact_name']) ? esc_attr($_POST['contact_name']) : ''; ?>"
                                   placeholder="John Smith">
                        </div>
                        
                        <div class="mh-form-group">
                            <label for="contact_email">Email Address <span class="required">*</span></label>
                            <input type="email" id="contact_email" name="contact_email" required 
                                   value="<?php echo isset($_POST['contact_email']) ? esc_attr($_POST['contact_email']) : ''; ?>"
                                   placeholder="you@university.edu">
                        </div>
                        
                        <div class="mh-form-group">
                            <label for="contact_subject">Subject</label>
                            <select id="contact_subject" name="contact_subject">
                                <option value="">Select a topic...</option>
                                <option value="General Inquiry">General Inquiry</option>
                                <option value="Paper Submission">Paper Submission</option>
                                <option value="Protocol Upload">Protocol Upload</option>
                                <option value="Bug Report">Bug Report</option>
                                <option value="Feature Request">Feature Request</option>
                                <option value="Collaboration">Collaboration</option>
                                <option value="Data Request">Data Request</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        
                        <div class="mh-form-group">
                            <label for="contact_message">Message <span class="required">*</span></label>
                            <textarea id="contact_message" name="contact_message" rows="6" required 
                                      placeholder="How can we help you?"><?php echo isset($_POST['contact_message']) ? esc_textarea($_POST['contact_message']) : ''; ?></textarea>
                        </div>
                        
                        <div class="mh-form-group">
                            <button type="submit" name="mh_contact_submit" class="mh-submit-btn">
                                Send Message
                            </button>
                        </div>
                    </form>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<style>
.mh-contact-page {
    max-width: 1100px;
}

.mh-contact-layout {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 30px;
}

@media (max-width: 768px) {
    .mh-contact-layout {
        grid-template-columns: 1fr;
    }
}

.mh-info-card {
    background: #161b22;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 20px;
    border: 1px solid #30363d;
}

.mh-info-card h3 {
    color: #e6edf3;
    font-size: 1.2rem;
    margin-bottom: 15px;
}

.mh-info-card p {
    color: #8b949e;
    line-height: 1.6;
}

.mh-info-card ul {
    list-style: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

.mh-info-card li {
    padding: 8px 0;
    color: #c9d1d9;
    border-bottom: 1px solid #21262d;
}

.mh-info-card li:last-child {
    border-bottom: none;
}

.mh-info-card a {
    color: #58a6ff;
}

.mh-info-card a:hover {
    text-decoration: underline;
}

.mh-contact-form-container {
    background: #161b22;
    border-radius: 12px;
    padding: 30px;
    border: 1px solid #30363d;
}

.mh-contact-form .mh-form-group {
    margin-bottom: 20px;
}

.mh-contact-form label {
    display: block;
    color: #e6edf3;
    font-weight: 500;
    margin-bottom: 8px;
}

.mh-contact-form .required {
    color: #f85149;
}

.mh-contact-form input,
.mh-contact-form select,
.mh-contact-form textarea {
    width: 100%;
    padding: 12px 15px;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    font-size: 1rem;
    font-family: inherit;
}

.mh-contact-form input:focus,
.mh-contact-form select:focus,
.mh-contact-form textarea:focus {
    outline: none;
    border-color: #58a6ff;
    box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.2);
}

.mh-contact-form input::placeholder,
.mh-contact-form textarea::placeholder {
    color: #6e7681;
}

.mh-submit-btn {
    width: 100%;
    padding: 14px 20px;
    background: linear-gradient(135deg, #238636, #2ea043);
    border: none;
    border-radius: 6px;
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.mh-submit-btn:hover {
    background: linear-gradient(135deg, #2ea043, #3fb950);
    transform: translateY(-1px);
}

.mh-success-message {
    text-align: center;
    padding: 40px 20px;
}

.mh-success-message .icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 15px;
}

.mh-success-message h3 {
    color: #3fb950;
    font-size: 1.5rem;
    margin-bottom: 10px;
}

.mh-success-message p {
    color: #8b949e;
    margin-bottom: 20px;
}

.mh-btn {
    display: inline-block;
    padding: 12px 24px;
    background: #21262d;
    color: #e6edf3;
    border-radius: 6px;
    font-weight: 500;
}

.mh-btn:hover {
    background: #30363d;
}

.mh-error-message {
    background: rgba(248, 81, 73, 0.1);
    border: 1px solid #f85149;
    color: #f85149;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}
</style>
