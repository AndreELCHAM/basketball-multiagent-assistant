/**
 * Chat Module
 * Renders messages, handles markdown, sources, images, and league prompts.
 */

const Chat = (() => {
    const messagesContainer = () => document.getElementById('messagesContainer');
    const messagesWrapper = () => document.getElementById('messagesWrapper');

    /**
     * Render a user message bubble.
     */
    function addUserMessage(text) {
        const container = messagesContainer();
        const msgEl = document.createElement('div');
        msgEl.className = 'message user';
        msgEl.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-body">
                <div class="message-content">${_escapeHtml(text)}</div>
            </div>
        `;
        container.appendChild(msgEl);
        _scrollToBottom();
    }

    /**
     * Render an assistant message bubble with optional sources & images.
     */
    function addAssistantMessage(data) {
        const container = messagesContainer();

        // Remove any loading indicator
        _removeLoading();

        const msgEl = document.createElement('div');
        msgEl.className = 'message assistant';

        // Determine badge type
        let badge = '';
        if (data.mcp_results && Object.keys(data.mcp_results).length > 0) {
            if (data.mcp_results.risk_level) {
                badge = '<span class="mcp-badge suspension">⚠️ Suspension Analysis</span>';
            } else if (data.mcp_results.game_score !== undefined) {
                badge = '<span class="mcp-badge performance">🏅 Performance Score</span>';
            }
        } else if (data.web_results && data.web_results.status === 'ok') {
            badge = '<span class="mcp-badge web">🌐 Live Data</span>';
        } else if (data.chunks && data.chunks.length > 0) {
            badge = '<span class="mcp-badge rag">📖 Rulebook</span>';
        }

        // Format answer with simple markdown
        const formattedAnswer = _formatMarkdown(data.answer || 'No response received.');

        // Sources
        let sourcesHtml = '';
        if (data.chunks && data.chunks.length > 0) {
            const sourceChips = data.chunks.slice(0, 5).map(c => {
                const league = c.metadata?.league || '?';
                const section = c.metadata?.article_or_section || 'Unknown';
                const score = c.score ? `${(c.score * 100).toFixed(0)}%` : '';
                return `<span class="source-chip"><span class="league-tag">${_escapeHtml(league)}</span> ${_escapeHtml(section)} ${score}</span>`;
            }).join('');

            sourcesHtml = `
                <div class="message-sources">
                    <button class="sources-toggle" onclick="Chat.toggleSources(this)">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        ${data.chunks.length} source${data.chunks.length > 1 ? 's' : ''}
                    </button>
                    <div class="sources-list">${sourceChips}</div>
                </div>
            `;
        }

        // Images
        let imagesHtml = '';
        if (data.image_paths && data.image_paths.length > 0) {
            const imgs = data.image_paths.map(p => {
                // Convert to API image URL
                const parts = p.split('/');
                const league = parts[parts.length - 2] || '';
                const filename = parts[parts.length - 1] || '';
                return `<img src="/api/images/${league}/${filename}" alt="Rulebook diagram" loading="lazy">`;
            }).join('');
            imagesHtml = `<div class="message-images">${imgs}</div>`;
        }

        msgEl.innerHTML = `
            <div class="message-avatar">🏀</div>
            <div class="message-body">
                <div class="message-content">
                    ${badge}
                    ${formattedAnswer}
                </div>
                ${imagesHtml}
                ${sourcesHtml}
            </div>
        `;

        container.appendChild(msgEl);
        _scrollToBottom();
    }

    /**
     * Show loading indicator.
     */
    function showLoading() {
        const container = messagesContainer();
        const loadEl = document.createElement('div');
        loadEl.className = 'message assistant loading';
        loadEl.id = 'loadingIndicator';
        loadEl.innerHTML = `
            <div class="message-avatar">🏀</div>
            <div class="message-body">
                <div class="message-content">
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                    Thinking...
                </div>
            </div>
        `;
        container.appendChild(loadEl);
        _scrollToBottom();
    }

    /**
     * Show league selection modal.
     */
    function showLeaguePrompt(message, options, onSelect) {
        const modal = document.getElementById('leagueModal');
        const promptText = document.getElementById('leaguePromptText');
        const optionsContainer = document.getElementById('leagueOptions');

        promptText.textContent = message || 'Which league is your question about?';

        optionsContainer.innerHTML = options.map(opt =>
            `<button class="league-btn" data-league="${_escapeHtml(opt)}">${_escapeHtml(opt)}</button>`
        ).join('');

        // Attach click handlers
        optionsContainer.querySelectorAll('.league-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const league = btn.dataset.league;
                modal.style.display = 'none';
                if (onSelect) onSelect(league);
            });
        });

        modal.style.display = 'block';
    }

    /**
     * Hide league selection modal.
     */
    function hideLeaguePrompt() {
        document.getElementById('leagueModal').style.display = 'none';
    }

    /**
     * Toggle sources visibility.
     */
    function toggleSources(btn) {
        const list = btn.nextElementSibling;
        const isVisible = list.classList.contains('visible');
        list.classList.toggle('visible');
        btn.classList.toggle('expanded');
    }

    /**
     * Clear all messages from the chat.
     */
    function clearMessages() {
        messagesContainer().innerHTML = '';
        hideLeaguePrompt();
    }

    /**
     * Render a full conversation history (when loading a thread).
     */
    function renderHistory(messages) {
        clearMessages();
        for (const msg of messages) {
            if (msg.role === 'user') {
                addUserMessage(msg.content);
            } else if (msg.role === 'assistant') {
                addAssistantMessage({
                    answer: msg.content,
                    chunks: [],
                    image_paths: [],
                    response_type: msg.response_type || 'answer',
                });
            }
        }
    }

    // ── Internal Helpers ──────────────────────────────────────────────

    function _removeLoading() {
        const el = document.getElementById('loadingIndicator');
        if (el) el.remove();
    }

    function _scrollToBottom() {
        const wrapper = messagesWrapper();
        if (wrapper) {
            requestAnimationFrame(() => {
                wrapper.scrollTop = wrapper.scrollHeight;
            });
        }
    }

    function _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function _formatMarkdown(text) {
        // Simple markdown formatting (no external dependency)
        let html = _escapeHtml(text);

        // Code blocks (```)
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

        // Inline code (`)
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Bold (**text**)
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic (*text*)
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Headers (### → h3, ## → h2, # → h1)
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // Blockquotes
        html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

        // Unordered lists
        html = html.replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
        // Prevent nested <ul> tags
        html = html.replace(/<\/ul>\s*<ul>/g, '');

        // Numbered lists
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        // Wrap in paragraph if not already wrapped
        if (!html.startsWith('<')) {
            html = `<p>${html}</p>`;
        }

        return html;
    }

    return {
        addUserMessage,
        addAssistantMessage,
        showLoading,
        showLeaguePrompt,
        hideLeaguePrompt,
        toggleSources,
        clearMessages,
        renderHistory,
    };
})();
