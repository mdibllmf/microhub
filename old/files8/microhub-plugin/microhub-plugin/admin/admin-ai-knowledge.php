<?php
/**
 * MicroHub AI Knowledge Base
 * Upload text files to expand the chatbot's knowledge
 */

if (!defined('ABSPATH')) exit;

class MicroHub_AI_Knowledge {
    
    private $table_name;
    
    public function __construct() {
        global $wpdb;
        $this->table_name = $wpdb->prefix . 'mh_knowledge';
        
        add_action('admin_menu', array($this, 'add_menu'));
        add_action('admin_init', array($this, 'maybe_create_table'));
        add_action('wp_ajax_mh_upload_knowledge', array($this, 'ajax_upload'));
        add_action('wp_ajax_mh_delete_knowledge', array($this, 'ajax_delete'));
        add_action('wp_ajax_mh_search_knowledge', array($this, 'ajax_search'));
    }
    
    public function maybe_create_table() {
        global $wpdb;
        
        if (get_option('mh_knowledge_table_version') === '1.1') {
            return;
        }
        
        $charset_collate = $wpdb->get_charset_collate();
        
        $sql = "CREATE TABLE {$this->table_name} (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            title varchar(255) NOT NULL,
            content longtext NOT NULL,
            category varchar(100) DEFAULT '',
            keywords text,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            FULLTEXT KEY content_search (title, content, keywords)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
        
        update_option('mh_knowledge_table_version', '1.1');
    }
    
    public function add_menu() {
        add_submenu_page(
            'microhub-settings',
            'AI Knowledge Base',
            'AI Knowledge',
            'manage_options',
            'microhub-ai-knowledge',
            array($this, 'render_page')
        );
    }
    
    public function render_page() {
        global $wpdb;
        
        $entries = $wpdb->get_results("SELECT id, title, category, LENGTH(content) as size, created_at FROM {$this->table_name} ORDER BY created_at DESC");
        $total_size = $wpdb->get_var("SELECT SUM(LENGTH(content)) FROM {$this->table_name}");
        $total_entries = count($entries);
        
        ?>
        <div class="wrap mh-knowledge">
            <h1>AI Knowledge Base</h1>
            <p class="description">Upload text files to expand what the chatbot knows. The bot will search this knowledge base to answer questions.</p>
            
            <div class="mh-knowledge-stats">
                <div class="mh-stat">
                    <span class="mh-stat-value"><?php echo $total_entries; ?></span>
                    <span class="mh-stat-label">Documents</span>
                </div>
                <div class="mh-stat">
                    <span class="mh-stat-value"><?php echo $total_size ? size_format($total_size) : '0 KB'; ?></span>
                    <span class="mh-stat-label">Total Size</span>
                </div>
            </div>
            
            <div class="mh-knowledge-grid">
                <div class="mh-upload-section">
                    <h2>Add Knowledge</h2>
                    
                    <div class="mh-upload-tabs">
                        <button class="mh-upload-tab active" data-tab="file">Upload File</button>
                        <button class="mh-upload-tab" data-tab="paste">Paste Text</button>
                        <button class="mh-upload-tab" data-tab="quick">Quick Add</button>
                    </div>
                    
                    <!-- File Upload -->
                    <div class="mh-upload-content active" id="tab-file">
                        <p>Upload .txt files containing information for the chatbot.</p>
                        <div class="mh-dropzone" id="dropzone">
                            <input type="file" id="fileInput" accept=".txt,.md" multiple style="display:none">
                            <p>Drag & drop .txt files here<br>or <a href="#" id="browseFiles">browse</a></p>
                        </div>
                        <div class="mh-upload-options">
                            <label>Category (optional):
                                <input type="text" id="uploadCategory" placeholder="e.g., techniques, software, protocols">
                            </label>
                        </div>
                    </div>
                    
                    <!-- Paste Text -->
                    <div class="mh-upload-content" id="tab-paste">
                        <p>Paste text directly into the knowledge base.</p>
                        <input type="text" id="pasteTitle" placeholder="Title (e.g., STED Microscopy Guide)" class="mh-full-width">
                        <textarea id="pasteContent" rows="10" placeholder="Paste your content here..." class="mh-full-width"></textarea>
                        <div class="mh-upload-options">
                            <label>Category:
                                <input type="text" id="pasteCategory" placeholder="e.g., techniques">
                            </label>
                            <label>Keywords (comma-separated):
                                <input type="text" id="pasteKeywords" placeholder="e.g., sted, super-resolution, nanoscopy">
                            </label>
                        </div>
                        <button class="button button-primary" id="savePaste">Save to Knowledge Base</button>
                    </div>
                    
                    <!-- Quick Add -->
                    <div class="mh-upload-content" id="tab-quick">
                        <p>Quickly add a fact or piece of information.</p>
                        <input type="text" id="quickTitle" placeholder="Topic (e.g., MesoSPIM availability)" class="mh-full-width">
                        <textarea id="quickContent" rows="4" placeholder="Information..." class="mh-full-width"></textarea>
                        <button class="button button-primary" id="saveQuick">Add</button>
                    </div>
                </div>
                
                <div class="mh-entries-section">
                    <h2>Knowledge Entries</h2>
                    
                    <div class="mh-search-box">
                        <input type="text" id="searchKnowledge" placeholder="Search knowledge base...">
                        <button class="button" id="doSearch">Search</button>
                    </div>
                    
                    <div class="mh-entries-list" id="entriesList">
                        <?php if (empty($entries)): ?>
                            <p class="mh-no-entries">No knowledge entries yet. Upload some files to get started!</p>
                        <?php else: ?>
                            <?php foreach ($entries as $entry): ?>
                                <div class="mh-entry" data-id="<?php echo $entry->id; ?>">
                                    <div class="mh-entry-info">
                                        <strong><?php echo esc_html($entry->title); ?></strong>
                                        <?php if ($entry->category): ?>
                                            <span class="mh-entry-cat"><?php echo esc_html($entry->category); ?></span>
                                        <?php endif; ?>
                                        <span class="mh-entry-size"><?php echo size_format($entry->size); ?></span>
                                    </div>
                                    <div class="mh-entry-actions">
                                        <button class="button mh-view-entry">View</button>
                                        <button class="button mh-delete-entry">Delete</button>
                                    </div>
                                </div>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
            
            <div class="mh-test-section">
                <h2>Test Knowledge Search</h2>
                <p class="description">Test how the bot searches your knowledge base.</p>
                <div class="mh-test-input">
                    <input type="text" id="testQuery" placeholder="Ask a question..." class="regular-text">
                    <button class="button button-primary" id="testSearch">Test</button>
                </div>
                <div class="mh-test-results" id="testResults"></div>
            </div>
        </div>
        
        <style>
            .mh-knowledge { max-width: 1200px; }
            .mh-knowledge-stats { display: flex; gap: 20px; margin: 20px 0; }
            .mh-stat { background: #fff; padding: 20px 30px; border-radius: 8px; border: 1px solid #ddd; text-align: center; }
            .mh-stat-value { display: block; font-size: 32px; font-weight: 600; color: #2271b1; }
            .mh-stat-label { color: #666; }
            
            .mh-knowledge-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 20px; }
            .mh-upload-section, .mh-entries-section { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
            
            .mh-upload-tabs { display: flex; gap: 0; margin-bottom: 20px; border-bottom: 1px solid #ddd; }
            .mh-upload-tab { padding: 10px 20px; background: none; border: none; cursor: pointer; border-bottom: 2px solid transparent; }
            .mh-upload-tab.active { border-bottom-color: #2271b1; font-weight: 600; }
            .mh-upload-content { display: none; }
            .mh-upload-content.active { display: block; }
            
            .mh-dropzone { border: 2px dashed #ccc; border-radius: 8px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.2s; }
            .mh-dropzone:hover, .mh-dropzone.dragover { border-color: #2271b1; background: #f0f7ff; }
            .mh-dropzone a { color: #2271b1; }
            
            .mh-upload-options { margin-top: 15px; display: flex; gap: 15px; flex-wrap: wrap; }
            .mh-upload-options label { display: flex; flex-direction: column; gap: 5px; }
            .mh-upload-options input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            
            .mh-full-width { width: 100%; margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            textarea.mh-full-width { font-family: inherit; resize: vertical; }
            
            .mh-search-box { display: flex; gap: 10px; margin-bottom: 15px; }
            .mh-search-box input { flex: 1; padding: 8px 12px; }
            
            .mh-entries-list { max-height: 400px; overflow-y: auto; }
            .mh-entry { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #eee; }
            .mh-entry:hover { background: #f9f9f9; }
            .mh-entry-info { flex: 1; }
            .mh-entry-info strong { display: block; margin-bottom: 4px; }
            .mh-entry-cat { background: #e0e0e0; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-right: 8px; }
            .mh-entry-size { color: #888; font-size: 12px; }
            .mh-entry-actions { display: flex; gap: 5px; }
            .mh-no-entries { color: #888; text-align: center; padding: 30px; }
            
            .mh-test-section { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd; margin-top: 30px; }
            .mh-test-input { display: flex; gap: 10px; margin-bottom: 15px; }
            .mh-test-input input { flex: 1; }
            .mh-test-results { background: #f5f5f5; padding: 15px; border-radius: 4px; min-height: 100px; white-space: pre-wrap; font-family: monospace; font-size: 13px; }
            
            @media (max-width: 900px) {
                .mh-knowledge-grid { grid-template-columns: 1fr; }
            }
        </style>
        
        <script>
        jQuery(document).ready(function($) {
            const nonce = '<?php echo wp_create_nonce('mh_knowledge'); ?>';
            
            // Tab switching
            $('.mh-upload-tab').on('click', function() {
                $('.mh-upload-tab').removeClass('active');
                $(this).addClass('active');
                $('.mh-upload-content').removeClass('active');
                $('#tab-' + $(this).data('tab')).addClass('active');
            });
            
            // Dropzone
            const dropzone = $('#dropzone');
            const fileInput = $('#fileInput');
            
            $('#browseFiles').on('click', function(e) {
                e.preventDefault();
                fileInput.click();
            });
            
            dropzone.on('click', function() { fileInput.click(); });
            
            dropzone.on('dragover', function(e) {
                e.preventDefault();
                $(this).addClass('dragover');
            }).on('dragleave drop', function() {
                $(this).removeClass('dragover');
            });
            
            dropzone.on('drop', function(e) {
                e.preventDefault();
                handleFiles(e.originalEvent.dataTransfer.files);
            });
            
            fileInput.on('change', function() {
                handleFiles(this.files);
            });
            
            function handleFiles(files) {
                const category = $('#uploadCategory').val();
                
                Array.from(files).forEach(file => {
                    if (!file.name.match(/\.(txt|md)$/i)) {
                        alert('Only .txt and .md files are supported');
                        return;
                    }
                    
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        uploadContent(file.name.replace(/\.[^.]+$/, ''), e.target.result, category, '');
                    };
                    reader.readAsText(file);
                });
            }
            
            function uploadContent(title, content, category, keywords) {
                $.post(ajaxurl, {
                    action: 'mh_upload_knowledge',
                    nonce: nonce,
                    title: title,
                    content: content,
                    category: category,
                    keywords: keywords
                }, function(response) {
                    if (response.success) {
                        location.reload();
                    } else {
                        alert('Error: ' + response.data);
                    }
                });
            }
            
            // Save pasted content
            $('#savePaste').on('click', function() {
                const title = $('#pasteTitle').val().trim();
                const content = $('#pasteContent').val().trim();
                const category = $('#pasteCategory').val().trim();
                const keywords = $('#pasteKeywords').val().trim();
                
                if (!title || !content) {
                    alert('Please enter a title and content');
                    return;
                }
                
                uploadContent(title, content, category, keywords);
            });
            
            // Quick add
            $('#saveQuick').on('click', function() {
                const title = $('#quickTitle').val().trim();
                const content = $('#quickContent').val().trim();
                
                if (!title || !content) {
                    alert('Please enter a topic and information');
                    return;
                }
                
                uploadContent(title, content, 'quick', title.toLowerCase());
            });
            
            // Delete entry
            $(document).on('click', '.mh-delete-entry', function() {
                if (!confirm('Delete this entry?')) return;
                
                const id = $(this).closest('.mh-entry').data('id');
                $.post(ajaxurl, {
                    action: 'mh_delete_knowledge',
                    nonce: nonce,
                    id: id
                }, function(response) {
                    if (response.success) {
                        location.reload();
                    }
                });
            });
            
            // Test search
            $('#testSearch').on('click', function() {
                const query = $('#testQuery').val().trim();
                if (!query) return;
                
                $.post(ajaxurl, {
                    action: 'mh_search_knowledge',
                    nonce: nonce,
                    query: query
                }, function(response) {
                    if (response.success) {
                        let html = 'Query: "' + query + '"\n\n';
                        if (response.data.results.length === 0) {
                            html += 'No results found.';
                        } else {
                            response.data.results.forEach((r, i) => {
                                html += '--- Result ' + (i+1) + ' (score: ' + r.score.toFixed(2) + ') ---\n';
                                html += 'Source: ' + r.title + '\n';
                                html += 'Excerpt: ' + r.excerpt + '\n\n';
                            });
                        }
                        html += '\n--- Generated Response ---\n' + response.data.response;
                        $('#testResults').text(html);
                    }
                });
            });
            
            $('#testQuery').on('keypress', function(e) {
                if (e.which === 13) $('#testSearch').click();
            });
        });
        </script>
        <?php
    }
    
    public function ajax_upload() {
        check_ajax_referer('mh_knowledge', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied');
        }
        
        global $wpdb;
        
        $title = sanitize_text_field($_POST['title']);
        $content = wp_kses_post($_POST['content']);
        $category = sanitize_text_field($_POST['category']);
        $keywords = sanitize_text_field($_POST['keywords']);
        
        if (empty($title) || empty($content)) {
            wp_send_json_error('Title and content required');
        }
        
        // Auto-extract keywords from content if not provided
        if (empty($keywords)) {
            $keywords = $this->extract_keywords($content);
        }
        
        $result = $wpdb->insert(
            $this->table_name,
            array(
                'title' => $title,
                'content' => $content,
                'category' => $category,
                'keywords' => $keywords
            ),
            array('%s', '%s', '%s', '%s')
        );
        
        if ($result) {
            wp_send_json_success('Saved');
        } else {
            wp_send_json_error('Database error');
        }
    }
    
    public function ajax_delete() {
        check_ajax_referer('mh_knowledge', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied');
        }
        
        global $wpdb;
        $id = intval($_POST['id']);
        
        $wpdb->delete($this->table_name, array('id' => $id), array('%d'));
        wp_send_json_success('Deleted');
    }
    
    public function ajax_search() {
        check_ajax_referer('mh_knowledge', 'nonce');
        
        $query = sanitize_text_field($_POST['query']);
        $results = $this->search($query);
        $response = $this->generate_response($query, $results);
        
        wp_send_json_success(array(
            'results' => $results,
            'response' => $response
        ));
    }
    
    /**
     * Search the knowledge base
     */
    public function search($query, $limit = 5) {
        global $wpdb;
        
        $query = strtolower(trim($query));
        if (empty($query)) return array();
        
        // Get all entries
        $entries = $wpdb->get_results("SELECT * FROM {$this->table_name}");
        if (empty($entries)) return array();
        
        // Score each entry
        $scored = array();
        $query_words = preg_split('/\s+/', $query);
        
        foreach ($entries as $entry) {
            $score = 0;
            $content_lower = strtolower($entry->content);
            $title_lower = strtolower($entry->title);
            $keywords_lower = strtolower($entry->keywords);
            
            // Exact phrase match (highest score)
            if (strpos($content_lower, $query) !== false) {
                $score += 10;
            }
            if (strpos($title_lower, $query) !== false) {
                $score += 15;
            }
            
            // Individual word matches
            foreach ($query_words as $word) {
                if (strlen($word) < 3) continue;
                
                // Title match
                if (strpos($title_lower, $word) !== false) {
                    $score += 5;
                }
                
                // Keywords match
                if (strpos($keywords_lower, $word) !== false) {
                    $score += 4;
                }
                
                // Content match (count occurrences, cap at 5)
                $count = substr_count($content_lower, $word);
                $score += min($count, 5) * 1;
            }
            
            if ($score > 0) {
                // Find best excerpt
                $excerpt = $this->find_best_excerpt($entry->content, $query_words);
                
                $scored[] = array(
                    'id' => $entry->id,
                    'title' => $entry->title,
                    'category' => $entry->category,
                    'score' => $score,
                    'excerpt' => $excerpt,
                    'content' => $entry->content
                );
            }
        }
        
        // Sort by score
        usort($scored, function($a, $b) {
            return $b['score'] - $a['score'];
        });
        
        return array_slice($scored, 0, $limit);
    }
    
    /**
     * Find the most relevant excerpt from content
     */
    private function find_best_excerpt($content, $query_words, $length = 300) {
        $content = strip_tags($content);
        $sentences = preg_split('/(?<=[.!?])\s+/', $content);
        
        $best_sentence = '';
        $best_score = 0;
        
        foreach ($sentences as $sentence) {
            $score = 0;
            $sentence_lower = strtolower($sentence);
            
            foreach ($query_words as $word) {
                if (strlen($word) >= 3 && strpos($sentence_lower, $word) !== false) {
                    $score++;
                }
            }
            
            if ($score > $best_score) {
                $best_score = $score;
                $best_sentence = $sentence;
            }
        }
        
        if (empty($best_sentence)) {
            $best_sentence = substr($content, 0, $length);
        }
        
        if (strlen($best_sentence) > $length) {
            $best_sentence = substr($best_sentence, 0, $length) . '...';
        }
        
        return trim($best_sentence);
    }
    
    /**
     * Generate a response from search results
     */
    public function generate_response($query, $results) {
        if (empty($results)) {
            return "I don't have specific information about that in my knowledge base. Try asking about microscopy techniques, software, or protocols.";
        }
        
        // Use top result(s) to form response
        $top = $results[0];
        
        // If high confidence match, use the excerpt
        if ($top['score'] >= 10) {
            $response = $top['excerpt'];
            
            // Add source attribution
            if (count($results) > 1) {
                $response .= "\n\n(From: " . $top['title'] . ". I also found related information in: " . $results[1]['title'] . ")";
            } else {
                $response .= "\n\n(Source: " . $top['title'] . ")";
            }
            
            return $response;
        }
        
        // Lower confidence - combine excerpts
        $response = "Based on my knowledge base:\n\n";
        foreach (array_slice($results, 0, 2) as $r) {
            $response .= "**" . $r['title'] . ":** " . $r['excerpt'] . "\n\n";
        }
        
        return $response;
    }
    
    /**
     * Extract keywords from content
     */
    private function extract_keywords($content) {
        // Common microscopy terms to look for
        $terms = array(
            'confocal', 'fluorescence', 'microscopy', 'microscope', 'imaging',
            'sted', 'palm', 'storm', 'light sheet', 'two-photon', 'tirf',
            'fret', 'flim', 'sim', 'expansion', 'super-resolution',
            'fiji', 'imagej', 'cellpose', 'imaris', 'python', 'matlab',
            'deconvolution', 'segmentation', 'tracking', 'analysis',
            'fluorophore', 'antibody', 'staining', 'protocol',
            'zebrafish', 'muscle', 'cell', 'tissue', 'sample'
        );
        
        $content_lower = strtolower($content);
        $found = array();
        
        foreach ($terms as $term) {
            if (strpos($content_lower, $term) !== false) {
                $found[] = $term;
            }
        }
        
        return implode(', ', array_slice($found, 0, 10));
    }
    
    /**
     * TAGGING HELPER: Search knowledge base to identify entities for tagging
     * Called during import to help identify techniques, software, etc.
     * 
     * @param string $text The text to analyze (title + abstract)
     * @param string $category Optional: limit to specific category (techniques, software, microscopes, etc.)
     * @return array Identified entities with confidence scores
     */
    public function identify_entities($text, $category = '') {
        global $wpdb;
        
        $text_lower = strtolower(trim($text));
        if (empty($text_lower)) return array();
        
        // Build query
        $query = "SELECT * FROM {$this->table_name}";
        if (!empty($category)) {
            $query .= $wpdb->prepare(" WHERE category = %s", $category);
        }
        
        $entries = $wpdb->get_results($query);
        if (empty($entries)) return array();
        
        $identified = array();
        
        foreach ($entries as $entry) {
            // Check if any keywords from this entry appear in the text
            $keywords = array_filter(array_map('trim', explode(',', strtolower($entry->keywords))));
            $title_words = array_filter(preg_split('/\s+/', strtolower($entry->title)));
            
            $matches = 0;
            $matched_terms = array();
            
            // Check title as entity name
            if (stripos($text_lower, strtolower($entry->title)) !== false) {
                $matches += 10;
                $matched_terms[] = $entry->title;
            }
            
            // Check keywords
            foreach ($keywords as $keyword) {
                if (strlen($keyword) >= 3 && stripos($text_lower, $keyword) !== false) {
                    $matches += 3;
                    $matched_terms[] = $keyword;
                }
            }
            
            // Check title words (for partial matches)
            foreach ($title_words as $word) {
                if (strlen($word) >= 4 && stripos($text_lower, $word) !== false) {
                    $matches += 1;
                }
            }
            
            if ($matches >= 3) {
                $identified[] = array(
                    'entity' => $entry->title,
                    'category' => $entry->category,
                    'confidence' => min($matches / 10, 1.0),
                    'matched_terms' => array_unique($matched_terms)
                );
            }
        }
        
        // Sort by confidence
        usort($identified, function($a, $b) {
            return $b['confidence'] <=> $a['confidence'];
        });
        
        return $identified;
    }
    
    /**
     * TAGGING HELPER: Get suggested tags for a paper based on knowledge base
     * Returns arrays of suggested techniques, software, etc.
     */
    public function suggest_tags_for_paper($title, $abstract, $existing_tags = array()) {
        $text = $title . ' ' . $abstract;
        
        $suggestions = array(
            'techniques' => array(),
            'software' => array(),
            'microscopes' => array(),
            'fluorophores' => array(),
            'organisms' => array(),
            'protocols' => array(),
        );
        
        // Get all identified entities
        $entities = $this->identify_entities($text);
        
        foreach ($entities as $entity) {
            $category = strtolower($entity['category']);
            
            // Map to our suggestion categories
            if (strpos($category, 'technique') !== false || strpos($category, 'method') !== false) {
                $suggestions['techniques'][] = $entity['entity'];
            } elseif (strpos($category, 'software') !== false || strpos($category, 'tool') !== false) {
                $suggestions['software'][] = $entity['entity'];
            } elseif (strpos($category, 'microscope') !== false || strpos($category, 'instrument') !== false) {
                $suggestions['microscopes'][] = $entity['entity'];
            } elseif (strpos($category, 'fluor') !== false || strpos($category, 'dye') !== false) {
                $suggestions['fluorophores'][] = $entity['entity'];
            } elseif (strpos($category, 'organism') !== false || strpos($category, 'model') !== false) {
                $suggestions['organisms'][] = $entity['entity'];
            } elseif (strpos($category, 'protocol') !== false) {
                $suggestions['protocols'][] = $entity['entity'];
            }
        }
        
        // Remove duplicates and existing tags
        foreach ($suggestions as $key => $values) {
            $suggestions[$key] = array_values(array_diff(array_unique($values), $existing_tags));
        }
        
        return $suggestions;
    }
    
    /**
     * Get singleton instance for use in import
     */
    public static function get_instance() {
        static $instance = null;
        if ($instance === null) {
            $instance = new self();
        }
        return $instance;
    }
}

// Initialize
new MicroHub_AI_Knowledge();

/**
 * Helper function to get knowledge-based tag suggestions
 * Can be called from import: mh_get_tag_suggestions($title, $abstract)
 */
function mh_get_tag_suggestions($title, $abstract, $existing_tags = array()) {
    $kb = MicroHub_AI_Knowledge::get_instance();
    return $kb->suggest_tags_for_paper($title, $abstract, $existing_tags);
}
