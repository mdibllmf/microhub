<?php
/**
 * MicroHub AI Chat Training Admin Page
 * Allows customizing chatbot responses without editing code
 */

if (!defined('ABSPATH')) exit;

class MicroHub_AI_Training {
    
    public function __construct() {
        add_action('admin_menu', array($this, 'add_menu'));
        add_action('admin_init', array($this, 'register_settings'));
        add_action('wp_ajax_mh_save_training', array($this, 'ajax_save_training'));
        add_action('wp_ajax_mh_delete_training', array($this, 'ajax_delete_training'));
        add_action('wp_ajax_mh_test_chat', array($this, 'ajax_test_chat'));
    }
    
    public function add_menu() {
        add_submenu_page(
            'microhub-settings',
            'AI Training',
            'AI Training',
            'manage_options',
            'microhub-ai-training',
            array($this, 'render_page')
        );
    }
    
    public function register_settings() {
        register_setting('microhub_ai_training', 'microhub_ai_qa_pairs');
        register_setting('microhub_ai_training', 'microhub_ai_techniques');
        register_setting('microhub_ai_training', 'microhub_ai_software');
        register_setting('microhub_ai_training', 'microhub_ai_greetings');
        register_setting('microhub_ai_training', 'microhub_ai_bot_name');
        register_setting('microhub_ai_training', 'microhub_ai_bot_personality');
    }
    
    public function render_page() {
        // Get saved data
        $qa_pairs = get_option('microhub_ai_qa_pairs', array());
        $techniques = get_option('microhub_ai_techniques', array());
        $software = get_option('microhub_ai_software', array());
        $greetings = get_option('microhub_ai_greetings', array());
        $bot_name = get_option('microhub_ai_bot_name', 'MicroHub Assistant');
        $bot_personality = get_option('microhub_ai_bot_personality', '');
        
        ?>
        <div class="wrap mh-ai-training">
            <h1>AI Chat Training</h1>
            <p class="description">Customize how the MicroHub AI assistant responds to questions. Your custom training takes priority over built-in responses.</p>
            
            <div class="mh-training-tabs">
                <button class="mh-tab-btn active" data-tab="qa">Q&A Pairs</button>
                <button class="mh-tab-btn" data-tab="techniques">Techniques</button>
                <button class="mh-tab-btn" data-tab="software">Software</button>
                <button class="mh-tab-btn" data-tab="personality">Personality</button>
                <button class="mh-tab-btn" data-tab="test">Test Chat</button>
            </div>
            
            <!-- Q&A Pairs Tab -->
            <div class="mh-tab-content active" id="tab-qa">
                <h2>Custom Q&A Pairs</h2>
                <p class="description">Add question-answer pairs. The bot will use these when it detects matching keywords in user questions.</p>
                
                <div class="mh-qa-list" id="qaList">
                    <?php if (!empty($qa_pairs)): ?>
                        <?php foreach ($qa_pairs as $index => $pair): ?>
                            <div class="mh-qa-item" data-index="<?php echo $index; ?>">
                                <div class="mh-qa-header">
                                    <span class="mh-qa-number">#<?php echo $index + 1; ?></span>
                                    <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                                </div>
                                <div class="mh-qa-field">
                                    <label>Keywords (comma-separated):</label>
                                    <input type="text" class="mh-qa-keywords" value="<?php echo esc_attr($pair['keywords']); ?>" placeholder="e.g., zebrafish, fish, danio">
                                </div>
                                <div class="mh-qa-field">
                                    <label>Question Pattern (optional):</label>
                                    <input type="text" class="mh-qa-question" value="<?php echo esc_attr($pair['question']); ?>" placeholder="e.g., How do I image zebrafish?">
                                </div>
                                <div class="mh-qa-field">
                                    <label>Answer:</label>
                                    <textarea class="mh-qa-answer" rows="4" placeholder="The response the bot should give..."><?php echo esc_textarea($pair['answer']); ?></textarea>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
                
                <button type="button" class="button" id="addQaPair">+ Add Q&A Pair</button>
                <button type="button" class="button button-primary mh-save-btn" data-type="qa">Save Q&A Pairs</button>
            </div>
            
            <!-- Techniques Tab -->
            <div class="mh-tab-content" id="tab-techniques">
                <h2>Custom Technique Descriptions</h2>
                <p class="description">Override or add descriptions for microscopy techniques. These are used when users ask "What is X?" or "Explain X".</p>
                
                <div class="mh-technique-list" id="techniqueList">
                    <?php if (!empty($techniques)): ?>
                        <?php foreach ($techniques as $index => $tech): ?>
                            <div class="mh-technique-item" data-index="<?php echo $index; ?>">
                                <div class="mh-qa-header">
                                    <span class="mh-qa-number">#<?php echo $index + 1; ?></span>
                                    <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                                </div>
                                <div class="mh-qa-field">
                                    <label>Technique Name:</label>
                                    <input type="text" class="mh-tech-name" value="<?php echo esc_attr($tech['name']); ?>" placeholder="e.g., MesoSPIM">
                                </div>
                                <div class="mh-qa-field">
                                    <label>Keywords (comma-separated):</label>
                                    <input type="text" class="mh-tech-keywords" value="<?php echo esc_attr($tech['keywords']); ?>" placeholder="e.g., mesospim, meso-spim, mesosheet">
                                </div>
                                <div class="mh-qa-field">
                                    <label>Description:</label>
                                    <textarea class="mh-tech-description" rows="6" placeholder="Full description of the technique..."><?php echo esc_textarea($tech['description']); ?></textarea>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
                
                <button type="button" class="button" id="addTechnique">+ Add Technique</button>
                <button type="button" class="button button-primary mh-save-btn" data-type="techniques">Save Techniques</button>
            </div>
            
            <!-- Software Tab -->
            <div class="mh-tab-content" id="tab-software">
                <h2>Custom Software Descriptions</h2>
                <p class="description">Add or override descriptions for image analysis software.</p>
                
                <div class="mh-software-list" id="softwareList">
                    <?php if (!empty($software)): ?>
                        <?php foreach ($software as $index => $sw): ?>
                            <div class="mh-software-item" data-index="<?php echo $index; ?>">
                                <div class="mh-qa-header">
                                    <span class="mh-qa-number">#<?php echo $index + 1; ?></span>
                                    <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                                </div>
                                <div class="mh-qa-field">
                                    <label>Software Name:</label>
                                    <input type="text" class="mh-sw-name" value="<?php echo esc_attr($sw['name']); ?>" placeholder="e.g., Amira">
                                </div>
                                <div class="mh-qa-field">
                                    <label>Keywords (comma-separated):</label>
                                    <input type="text" class="mh-sw-keywords" value="<?php echo esc_attr($sw['keywords']); ?>" placeholder="e.g., amira, thermo fisher, 3d visualization">
                                </div>
                                <div class="mh-qa-field">
                                    <label>Description:</label>
                                    <textarea class="mh-sw-description" rows="4" placeholder="Description of the software..."><?php echo esc_textarea($sw['description']); ?></textarea>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
                
                <button type="button" class="button" id="addSoftware">+ Add Software</button>
                <button type="button" class="button button-primary mh-save-btn" data-type="software">Save Software</button>
            </div>
            
            <!-- Personality Tab -->
            <div class="mh-tab-content" id="tab-personality">
                <h2>Bot Personality</h2>
                <p class="description">Customize the bot's name and greeting messages.</p>
                
                <table class="form-table">
                    <tr>
                        <th><label for="botName">Bot Name</label></th>
                        <td>
                            <input type="text" id="botName" class="regular-text" value="<?php echo esc_attr($bot_name); ?>" placeholder="MicroHub Assistant">
                            <p class="description">The name shown in the chat header.</p>
                        </td>
                    </tr>
                    <tr>
                        <th><label for="botPersonality">Personality Notes</label></th>
                        <td>
                            <textarea id="botPersonality" rows="4" class="large-text" placeholder="e.g., Focus on light sheet microscopy, be extra helpful to beginners..."><?php echo esc_textarea($bot_personality); ?></textarea>
                            <p class="description">Notes about how the bot should behave (for your reference).</p>
                        </td>
                    </tr>
                </table>
                
                <h3>Custom Greetings</h3>
                <p class="description">Add custom greeting messages. One will be randomly selected when users say hello.</p>
                
                <div class="mh-greetings-list" id="greetingsList">
                    <?php if (!empty($greetings)): ?>
                        <?php foreach ($greetings as $index => $greeting): ?>
                            <div class="mh-greeting-item" data-index="<?php echo $index; ?>">
                                <textarea class="mh-greeting-text" rows="2"><?php echo esc_textarea($greeting); ?></textarea>
                                <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                            </div>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
                
                <button type="button" class="button" id="addGreeting">+ Add Greeting</button>
                <button type="button" class="button button-primary mh-save-btn" data-type="personality">Save Personality</button>
            </div>
            
            <!-- Test Tab -->
            <div class="mh-tab-content" id="tab-test">
                <h2>Test Your Training</h2>
                <p class="description">Test how the bot responds with your custom training data.</p>
                
                <div class="mh-test-chat">
                    <div class="mh-test-messages" id="testMessages">
                        <div class="mh-test-bot">
                            <p>Hi! Test your training by typing a question below.</p>
                        </div>
                    </div>
                    <div class="mh-test-form">
                        <input type="text" id="testInput" placeholder="Type a test question..." autocomplete="off">
                        <button type="button" id="testSend" class="button button-primary">Send</button>
                    </div>
                </div>
                
                <div class="mh-test-info">
                    <h4>Training Statistics</h4>
                    <ul>
                        <li>Q&A Pairs: <strong><?php echo count($qa_pairs); ?></strong></li>
                        <li>Custom Techniques: <strong><?php echo count($techniques); ?></strong></li>
                        <li>Custom Software: <strong><?php echo count($software); ?></strong></li>
                        <li>Custom Greetings: <strong><?php echo count($greetings); ?></strong></li>
                    </ul>
                </div>
            </div>
            
            <div id="mhTrainingNotice" class="notice" style="display:none;"></div>
        </div>
        
        <style>
            .mh-ai-training { max-width: 900px; }
            .mh-training-tabs { display: flex; gap: 0; margin: 20px 0; border-bottom: 1px solid #ccc; }
            .mh-tab-btn { padding: 10px 20px; background: #f0f0f0; border: 1px solid #ccc; border-bottom: none; cursor: pointer; font-size: 14px; margin-bottom: -1px; }
            .mh-tab-btn.active { background: #fff; border-bottom-color: #fff; font-weight: 600; }
            .mh-tab-btn:hover { background: #e5e5e5; }
            .mh-tab-content { display: none; padding: 20px 0; }
            .mh-tab-content.active { display: block; }
            
            .mh-qa-item, .mh-technique-item, .mh-software-item { 
                background: #f9f9f9; 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                padding: 15px; 
                margin-bottom: 15px; 
            }
            .mh-qa-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
            .mh-qa-number { font-weight: 600; color: #666; }
            .mh-qa-delete { background: #dc3545; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 16px; line-height: 1; }
            .mh-qa-delete:hover { background: #c82333; }
            .mh-qa-field { margin-bottom: 10px; }
            .mh-qa-field label { display: block; font-weight: 500; margin-bottom: 4px; color: #333; }
            .mh-qa-field input, .mh-qa-field textarea { width: 100%; }
            .mh-qa-field textarea { font-family: inherit; }
            
            .mh-greeting-item { display: flex; gap: 10px; margin-bottom: 10px; align-items: flex-start; }
            .mh-greeting-item textarea { flex: 1; }
            .mh-greeting-item .mh-qa-delete { flex-shrink: 0; margin-top: 5px; }
            
            .mh-save-btn { margin-top: 15px; margin-left: 10px; }
            
            .mh-test-chat { 
                background: #1a1a2e; 
                border-radius: 8px; 
                overflow: hidden; 
                max-width: 500px;
                margin: 20px 0;
            }
            .mh-test-messages { 
                padding: 20px; 
                min-height: 200px; 
                max-height: 400px; 
                overflow-y: auto; 
            }
            .mh-test-bot, .mh-test-user { 
                padding: 10px 15px; 
                border-radius: 12px; 
                margin-bottom: 10px; 
                max-width: 85%;
                font-size: 14px;
                line-height: 1.5;
            }
            .mh-test-bot { background: #252542; color: #e2e8f0; }
            .mh-test-bot p { margin: 0; }
            .mh-test-user { background: #6366f1; color: white; margin-left: auto; }
            .mh-test-form { display: flex; gap: 10px; padding: 15px; background: #16162a; }
            .mh-test-form input { flex: 1; padding: 10px 15px; border: 1px solid #444; border-radius: 20px; background: #252542; color: #e2e8f0; }
            .mh-test-form input::placeholder { color: #888; }
            
            .mh-test-info { 
                background: #f0f7ff; 
                border: 1px solid #0073aa; 
                border-radius: 4px; 
                padding: 15px; 
                max-width: 300px;
            }
            .mh-test-info h4 { margin-top: 0; }
            .mh-test-info ul { margin: 0; padding-left: 20px; }
            
            #mhTrainingNotice { margin-top: 20px; }
        </style>
        
        <script>
        jQuery(document).ready(function($) {
            // Tab switching
            $('.mh-tab-btn').on('click', function() {
                $('.mh-tab-btn').removeClass('active');
                $(this).addClass('active');
                $('.mh-tab-content').removeClass('active');
                $('#tab-' + $(this).data('tab')).addClass('active');
            });
            
            // Add Q&A pair
            $('#addQaPair').on('click', function() {
                const index = $('#qaList .mh-qa-item').length;
                const html = `
                    <div class="mh-qa-item" data-index="${index}">
                        <div class="mh-qa-header">
                            <span class="mh-qa-number">#${index + 1}</span>
                            <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                        </div>
                        <div class="mh-qa-field">
                            <label>Keywords (comma-separated):</label>
                            <input type="text" class="mh-qa-keywords" placeholder="e.g., zebrafish, fish, danio">
                        </div>
                        <div class="mh-qa-field">
                            <label>Question Pattern (optional):</label>
                            <input type="text" class="mh-qa-question" placeholder="e.g., How do I image zebrafish?">
                        </div>
                        <div class="mh-qa-field">
                            <label>Answer:</label>
                            <textarea class="mh-qa-answer" rows="4" placeholder="The response the bot should give..."></textarea>
                        </div>
                    </div>
                `;
                $('#qaList').append(html);
            });
            
            // Add Technique
            $('#addTechnique').on('click', function() {
                const index = $('#techniqueList .mh-technique-item').length;
                const html = `
                    <div class="mh-technique-item" data-index="${index}">
                        <div class="mh-qa-header">
                            <span class="mh-qa-number">#${index + 1}</span>
                            <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                        </div>
                        <div class="mh-qa-field">
                            <label>Technique Name:</label>
                            <input type="text" class="mh-tech-name" placeholder="e.g., MesoSPIM">
                        </div>
                        <div class="mh-qa-field">
                            <label>Keywords (comma-separated):</label>
                            <input type="text" class="mh-tech-keywords" placeholder="e.g., mesospim, meso-spim, mesosheet">
                        </div>
                        <div class="mh-qa-field">
                            <label>Description:</label>
                            <textarea class="mh-tech-description" rows="6" placeholder="Full description of the technique..."></textarea>
                        </div>
                    </div>
                `;
                $('#techniqueList').append(html);
            });
            
            // Add Software
            $('#addSoftware').on('click', function() {
                const index = $('#softwareList .mh-software-item').length;
                const html = `
                    <div class="mh-software-item" data-index="${index}">
                        <div class="mh-qa-header">
                            <span class="mh-qa-number">#${index + 1}</span>
                            <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                        </div>
                        <div class="mh-qa-field">
                            <label>Software Name:</label>
                            <input type="text" class="mh-sw-name" placeholder="e.g., Amira">
                        </div>
                        <div class="mh-qa-field">
                            <label>Keywords (comma-separated):</label>
                            <input type="text" class="mh-sw-keywords" placeholder="e.g., amira, thermo fisher, 3d visualization">
                        </div>
                        <div class="mh-qa-field">
                            <label>Description:</label>
                            <textarea class="mh-sw-description" rows="4" placeholder="Description of the software..."></textarea>
                        </div>
                    </div>
                `;
                $('#softwareList').append(html);
            });
            
            // Add Greeting
            $('#addGreeting').on('click', function() {
                const html = `
                    <div class="mh-greeting-item">
                        <textarea class="mh-greeting-text" rows="2" placeholder="Custom greeting message..."></textarea>
                        <button type="button" class="mh-qa-delete" title="Delete">&times;</button>
                    </div>
                `;
                $('#greetingsList').append(html);
            });
            
            // Delete items
            $(document).on('click', '.mh-qa-delete', function() {
                $(this).closest('.mh-qa-item, .mh-technique-item, .mh-software-item, .mh-greeting-item').remove();
            });
            
            // Save data
            $('.mh-save-btn').on('click', function() {
                const type = $(this).data('type');
                let data = { action: 'mh_save_training', type: type, nonce: '<?php echo wp_create_nonce('mh_ai_training'); ?>' };
                
                if (type === 'qa') {
                    data.items = [];
                    $('#qaList .mh-qa-item').each(function() {
                        data.items.push({
                            keywords: $(this).find('.mh-qa-keywords').val(),
                            question: $(this).find('.mh-qa-question').val(),
                            answer: $(this).find('.mh-qa-answer').val()
                        });
                    });
                } else if (type === 'techniques') {
                    data.items = [];
                    $('#techniqueList .mh-technique-item').each(function() {
                        data.items.push({
                            name: $(this).find('.mh-tech-name').val(),
                            keywords: $(this).find('.mh-tech-keywords').val(),
                            description: $(this).find('.mh-tech-description').val()
                        });
                    });
                } else if (type === 'software') {
                    data.items = [];
                    $('#softwareList .mh-software-item').each(function() {
                        data.items.push({
                            name: $(this).find('.mh-sw-name').val(),
                            keywords: $(this).find('.mh-sw-keywords').val(),
                            description: $(this).find('.mh-sw-description').val()
                        });
                    });
                } else if (type === 'personality') {
                    data.bot_name = $('#botName').val();
                    data.bot_personality = $('#botPersonality').val();
                    data.greetings = [];
                    $('#greetingsList .mh-greeting-item').each(function() {
                        const text = $(this).find('.mh-greeting-text').val().trim();
                        if (text) data.greetings.push(text);
                    });
                }
                
                $.post(ajaxurl, data, function(response) {
                    const notice = $('#mhTrainingNotice');
                    if (response.success) {
                        notice.removeClass('notice-error').addClass('notice-success').html('<p>' + response.data + '</p>').show();
                    } else {
                        notice.removeClass('notice-success').addClass('notice-error').html('<p>Error: ' + response.data + '</p>').show();
                    }
                    setTimeout(() => notice.fadeOut(), 3000);
                });
            });
            
            // Test chat
            $('#testSend').on('click', sendTestMessage);
            $('#testInput').on('keypress', function(e) {
                if (e.which === 13) sendTestMessage();
            });
            
            function sendTestMessage() {
                const input = $('#testInput');
                const message = input.val().trim();
                if (!message) return;
                
                // Add user message
                $('#testMessages').append('<div class="mh-test-user">' + escapeHtml(message) + '</div>');
                input.val('');
                
                // Scroll to bottom
                const container = $('#testMessages');
                container.scrollTop(container[0].scrollHeight);
                
                // Send to API
                $.post(ajaxurl, {
                    action: 'mh_test_chat',
                    message: message,
                    nonce: '<?php echo wp_create_nonce('mh_ai_training'); ?>'
                }, function(response) {
                    let reply = response.data.reply || 'No response';
                    reply = reply.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    reply = reply.replace(/\n/g, '<br>');
                    $('#testMessages').append('<div class="mh-test-bot"><p>' + reply + '</p></div>');
                    container.scrollTop(container[0].scrollHeight);
                });
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        });
        </script>
        <?php
    }
    
    public function ajax_save_training() {
        check_ajax_referer('mh_ai_training', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied');
        }
        
        $type = sanitize_text_field($_POST['type']);
        
        switch ($type) {
            case 'qa':
                $items = isset($_POST['items']) ? $_POST['items'] : array();
                $clean_items = array();
                foreach ($items as $item) {
                    if (!empty($item['keywords']) || !empty($item['answer'])) {
                        $clean_items[] = array(
                            'keywords' => sanitize_text_field($item['keywords']),
                            'question' => sanitize_text_field($item['question']),
                            'answer' => wp_kses_post($item['answer'])
                        );
                    }
                }
                update_option('microhub_ai_qa_pairs', $clean_items);
                wp_send_json_success('Saved ' . count($clean_items) . ' Q&A pairs');
                break;
                
            case 'techniques':
                $items = isset($_POST['items']) ? $_POST['items'] : array();
                $clean_items = array();
                foreach ($items as $item) {
                    if (!empty($item['name']) || !empty($item['description'])) {
                        $clean_items[] = array(
                            'name' => sanitize_text_field($item['name']),
                            'keywords' => sanitize_text_field($item['keywords']),
                            'description' => wp_kses_post($item['description'])
                        );
                    }
                }
                update_option('microhub_ai_techniques', $clean_items);
                wp_send_json_success('Saved ' . count($clean_items) . ' techniques');
                break;
                
            case 'software':
                $items = isset($_POST['items']) ? $_POST['items'] : array();
                $clean_items = array();
                foreach ($items as $item) {
                    if (!empty($item['name']) || !empty($item['description'])) {
                        $clean_items[] = array(
                            'name' => sanitize_text_field($item['name']),
                            'keywords' => sanitize_text_field($item['keywords']),
                            'description' => wp_kses_post($item['description'])
                        );
                    }
                }
                update_option('microhub_ai_software', $clean_items);
                wp_send_json_success('Saved ' . count($clean_items) . ' software entries');
                break;
                
            case 'personality':
                update_option('microhub_ai_bot_name', sanitize_text_field($_POST['bot_name']));
                update_option('microhub_ai_bot_personality', sanitize_textarea_field($_POST['bot_personality']));
                $greetings = isset($_POST['greetings']) ? array_map('sanitize_textarea_field', $_POST['greetings']) : array();
                update_option('microhub_ai_greetings', array_filter($greetings));
                wp_send_json_success('Personality settings saved');
                break;
                
            default:
                wp_send_json_error('Unknown type');
        }
    }
    
    public function ajax_test_chat() {
        check_ajax_referer('mh_ai_training', 'nonce');
        
        $message = sanitize_text_field($_POST['message']);
        
        // Use the API endpoint
        $request = new WP_REST_Request('POST', '/microhub/v1/ai-chat');
        $request->set_param('message', $message);
        
        $api = new MicroHub_API();
        $response = $api->ai_chat($request);
        
        wp_send_json_success($response);
    }
}

// Initialize
new MicroHub_AI_Training();
