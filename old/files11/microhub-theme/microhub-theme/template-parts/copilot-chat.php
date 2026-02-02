<?php
/**
 * MicroHub AI Chat Widget
 * Built-in intelligent chat that uses the paper database
 * No external API required - works for everyone
 */

$bot_name = get_option('microhub_ai_bot_name', 'MicroHub Assistant');
?>

<div class="mh-ai-chat">
    <button class="mh-ai-toggle" id="aiChatToggle">
        <svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
            <circle cx="8" cy="10" r="1.5"/>
            <circle cx="12" cy="10" r="1.5"/>
            <circle cx="16" cy="10" r="1.5"/>
        </svg>
        <span>Ask AI</span>
    </button>
    
    <div class="mh-ai-panel" id="aiChatPanel">
        <div class="mh-ai-header">
            <div class="mh-ai-header-info">
                <div class="mh-ai-avatar">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                    </svg>
                </div>
                <h4><?php echo esc_html($bot_name); ?></h4>
            </div>
            <button class="mh-ai-close" id="aiChatClose">&times;</button>
        </div>
        
        <div class="mh-ai-messages" id="aiChatMessages">
            <div class="mh-ai-message mh-ai-bot">
                <div class="mh-ai-message-content">
                    <p>Hi! I'm the MicroHub Assistant. I can help you:</p>
                    <ul>
                        <li><strong>Find papers</strong> about specific techniques</li>
                        <li><strong>Explain</strong> microscopy methods</li>
                        <li><strong>Compare</strong> different approaches</li>
                        <li><strong>Recommend</strong> techniques for your needs</li>
                    </ul>
                    <p>What would you like to know?</p>
                </div>
            </div>
        </div>
        
        <div class="mh-ai-suggestions" id="aiChatSuggestions">
            <button class="mh-ai-suggestion" data-query="What is confocal microscopy?">Confocal basics</button>
            <button class="mh-ai-suggestion" data-query="Find papers about STED">Find STED papers</button>
            <button class="mh-ai-suggestion" data-query="Best technique for live cell imaging?">Live cell imaging</button>
            <button class="mh-ai-suggestion" data-query="What software should I use for image analysis?">Analysis software</button>
        </div>
        
        <form class="mh-ai-form" id="aiChatForm">
            <input type="text" id="aiChatInput" placeholder="Ask about microscopy..." autocomplete="off">
            <button type="submit" id="aiChatSubmit">
                <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
            </button>
        </form>
    </div>
</div>

<style>
.mh-ai-chat {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 99999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.mh-ai-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 50px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    transition: all 0.3s ease;
}

.mh-ai-toggle:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5);
}

.mh-ai-toggle svg {
    width: 20px;
    height: 20px;
}

.mh-ai-panel {
    position: absolute;
    bottom: 70px;
    right: 0;
    width: 400px;
    height: 550px;
    background: #1a1a2e;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    display: none;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
}

.mh-ai-panel.active {
    display: flex;
}

.mh-ai-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 18px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    flex-shrink: 0;
}

.mh-ai-header-info {
    display: flex;
    align-items: center;
    gap: 10px;
}

.mh-ai-avatar {
    width: 32px;
    height: 32px;
    background: rgba(255,255,255,0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.mh-ai-header h4 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
}

.mh-ai-close {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 24px;
    line-height: 1;
    opacity: 0.8;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
}

.mh-ai-close:hover {
    opacity: 1;
    background: rgba(255,255,255,0.2);
}

.mh-ai-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.mh-ai-message {
    max-width: 85%;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.mh-ai-bot {
    align-self: flex-start;
}

.mh-ai-user {
    align-self: flex-end;
}

.mh-ai-message-content {
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.5;
}

.mh-ai-bot .mh-ai-message-content {
    background: #252542;
    color: #e2e8f0;
    border-bottom-left-radius: 4px;
}

.mh-ai-user .mh-ai-message-content {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border-bottom-right-radius: 4px;
}

.mh-ai-message-content p {
    margin: 0 0 8px 0;
}

.mh-ai-message-content p:last-child {
    margin-bottom: 0;
}

.mh-ai-message-content ul {
    margin: 8px 0;
    padding-left: 20px;
}

.mh-ai-message-content li {
    margin: 4px 0;
}

.mh-ai-message-content strong {
    color: #a5b4fc;
}

.mh-ai-user .mh-ai-message-content strong {
    color: white;
}

/* Paper results */
.mh-ai-papers {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mh-ai-paper {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 8px;
    padding: 10px 12px;
    text-decoration: none;
    color: #e2e8f0;
    transition: all 0.2s;
    display: block;
}

.mh-ai-paper:hover {
    background: rgba(99, 102, 241, 0.2);
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateX(4px);
}

.mh-ai-paper-title {
    font-weight: 600;
    font-size: 13px;
    color: #a5b4fc;
    margin-bottom: 4px;
    display: block;
}

.mh-ai-paper-meta {
    font-size: 11px;
    color: #94a3b8;
}

/* Suggestions */
.mh-ai-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 10px 16px;
    background: #16162a;
    border-top: 1px solid rgba(255,255,255,0.05);
}

.mh-ai-suggestion {
    padding: 6px 12px;
    background: #252542;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    font-size: 12px;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s;
}

.mh-ai-suggestion:hover {
    background: #6366f1;
    color: white;
    border-color: #6366f1;
}

/* Form */
.mh-ai-form {
    display: flex;
    padding: 12px;
    background: #16162a;
    border-top: 1px solid rgba(255,255,255,0.05);
    gap: 8px;
}

.mh-ai-form input {
    flex: 1;
    padding: 12px 16px;
    background: #252542;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px;
    color: #e2e8f0;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}

.mh-ai-form input:focus {
    border-color: #6366f1;
}

.mh-ai-form input::placeholder {
    color: #64748b;
}

.mh-ai-form button {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.mh-ai-form button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

.mh-ai-form button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
}

/* Typing indicator */
.mh-ai-typing {
    display: flex;
    gap: 4px;
    padding: 12px 16px;
}

.mh-ai-typing span {
    width: 8px;
    height: 8px;
    background: #6366f1;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
}

.mh-ai-typing span:nth-child(2) {
    animation-delay: 0.2s;
}

.mh-ai-typing span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-8px); opacity: 1; }
}

/* Mobile */
@media (max-width: 480px) {
    .mh-ai-panel {
        width: calc(100vw - 32px);
        height: 70vh;
        right: -8px;
    }
    
    .mh-ai-toggle span:last-child {
        display: none;
    }
    
    .mh-ai-toggle {
        padding: 14px;
        border-radius: 50%;
    }
}
</style>

<script>
(function() {
    const toggle = document.getElementById('aiChatToggle');
    const panel = document.getElementById('aiChatPanel');
    const close = document.getElementById('aiChatClose');
    const form = document.getElementById('aiChatForm');
    const input = document.getElementById('aiChatInput');
    const messages = document.getElementById('aiChatMessages');
    const suggestions = document.getElementById('aiChatSuggestions');
    const submitBtn = document.getElementById('aiChatSubmit');
    
    if (!toggle || !panel) return;
    
    // Get API URL from WordPress
    const apiUrl = typeof MicroHub !== 'undefined' ? MicroHub.restUrl + 'microhub/v1/ai-chat' : '/wp-json/microhub/v1/ai-chat';
    
    // Toggle panel
    toggle.addEventListener('click', function() {
        panel.classList.toggle('active');
        if (panel.classList.contains('active')) {
            input.focus();
        }
    });
    
    // Close panel
    close.addEventListener('click', function() {
        panel.classList.remove('active');
    });
    
    // Escape key closes
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && panel.classList.contains('active')) {
            panel.classList.remove('active');
        }
    });
    
    // Suggestion buttons
    suggestions.addEventListener('click', function(e) {
        if (e.target.classList.contains('mh-ai-suggestion')) {
            const query = e.target.dataset.query;
            input.value = query;
            form.dispatchEvent(new Event('submit'));
        }
    });
    
    // Submit form
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = input.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, 'user');
        input.value = '';
        input.disabled = true;
        submitBtn.disabled = true;
        
        // Hide suggestions after first message
        suggestions.style.display = 'none';
        
        // Show typing indicator
        const typingId = showTyping();
        
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            removeTyping(typingId);
            
            // Add bot response
            if (data.reply) {
                addMessage(data.reply, 'bot', data.papers || []);
            } else {
                addMessage("Sorry, I couldn't process that. Try asking about microscopy techniques or searching for papers!", 'bot');
            }
        } catch (err) {
            removeTyping(typingId);
            addMessage("Connection error. Please try again.", 'bot');
            console.error('Chat error:', err);
        }
        
        input.disabled = false;
        submitBtn.disabled = false;
        input.focus();
    });
    
    function addMessage(text, type, papers) {
        const div = document.createElement('div');
        div.className = 'mh-ai-message mh-ai-' + type;
        
        let content = '<div class="mh-ai-message-content">';
        content += formatMessage(text);
        
        // Add paper results if present
        if (papers && papers.length > 0) {
            content += '<div class="mh-ai-papers">';
            papers.forEach(function(paper) {
                content += '<a href="' + escapeHtml(paper.url) + '" class="mh-ai-paper" target="_blank">';
                content += '<span class="mh-ai-paper-title">' + escapeHtml(paper.title) + '</span>';
                if (paper.year || paper.authors) {
                    content += '<span class="mh-ai-paper-meta">';
                    if (paper.year) content += paper.year;
                    if (paper.year && paper.authors) content += ' - ';
                    if (paper.authors) content += escapeHtml(paper.authors.substring(0, 50)) + (paper.authors.length > 50 ? '...' : '');
                    content += '</span>';
                }
                content += '</a>';
            });
            content += '</div>';
        }
        
        content += '</div>';
        div.innerHTML = content;
        
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    }
    
    function formatMessage(text) {
        // Escape HTML first
        let html = escapeHtml(text);
        
        // Convert markdown-like formatting
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert bullet points
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Convert line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        
        // Wrap in paragraph if needed
        if (!html.startsWith('<')) {
            html = '<p>' + html + '</p>';
        }
        
        return html;
    }
    
    function showTyping() {
        const div = document.createElement('div');
        div.className = 'mh-ai-message mh-ai-bot';
        div.id = 'typing-' + Date.now();
        div.innerHTML = '<div class="mh-ai-message-content"><div class="mh-ai-typing"><span></span><span></span><span></span></div></div>';
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div.id;
    }
    
    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
</script>
