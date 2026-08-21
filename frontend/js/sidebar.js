/**
 * Sidebar Module
 * Manages chat thread list, search, creation, and deletion.
 */

const Sidebar = (() => {
    const chatListEl = () => document.getElementById('chatList');
    let _threads = [];
    let _activeThreadId = null;
    let _onThreadSelect = null;
    let _onThreadDelete = null;

    /**
     * Initialize sidebar with callbacks.
     */
    function init({ onThreadSelect, onThreadDelete }) {
        _onThreadSelect = onThreadSelect;
        _onThreadDelete = onThreadDelete;

        // Search filter
        document.getElementById('chatSearch').addEventListener('input', (e) => {
            _filterThreads(e.target.value);
        });
    }

    /**
     * Load threads from the API and render them.
     */
    async function loadThreads() {
        try {
            _threads = await API.listThreads();
            _renderThreads(_threads);
        } catch (e) {
            console.warn('Failed to load threads:', e);
            _threads = [];
            _renderThreads([]);
        }
    }

    /**
     * Set the active thread (highlight in sidebar).
     */
    function setActive(threadId) {
        _activeThreadId = threadId;
        _renderThreads(_getFilteredThreads());
    }

    /**
     * Add or update a thread in the list (after a new message).
     */
    function upsertThread(threadId, title) {
        const existing = _threads.find(t => t.thread_id === threadId);
        if (existing) {
            existing.title = title;
            existing.updated_at = new Date().toISOString();
            existing.message_count = (existing.message_count || 0) + 2; // user + assistant
        } else {
            _threads.unshift({
                thread_id: threadId,
                title: title,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                message_count: 2,
            });
        }
        _renderThreads(_getFilteredThreads());
    }

    /**
     * Remove a thread from the list.
     */
    function removeThread(threadId) {
        _threads = _threads.filter(t => t.thread_id !== threadId);
        _renderThreads(_getFilteredThreads());
    }

    /**
     * Clear active state (for new chat).
     */
    function clearActive() {
        _activeThreadId = null;
        _renderThreads(_getFilteredThreads());
    }

    // ── Internal ──────────────────────────────────────────────────────

    function _getFilteredThreads() {
        const searchVal = document.getElementById('chatSearch').value.toLowerCase();
        if (!searchVal) return _threads;
        return _threads.filter(t =>
            t.title && t.title.toLowerCase().includes(searchVal)
        );
    }

    function _filterThreads(searchText) {
        const filtered = searchText
            ? _threads.filter(t => t.title && t.title.toLowerCase().includes(searchText.toLowerCase()))
            : _threads;
        _renderThreads(filtered);
    }

    function _renderThreads(threads) {
        const container = chatListEl();
        if (!threads.length) {
            container.innerHTML = `
                <div style="padding: 24px 16px; text-align: center; color: var(--text-tertiary); font-size: 13px;">
                    No conversations yet.<br>Start a new chat!
                </div>
            `;
            return;
        }

        container.innerHTML = threads.map(t => {
            const isActive = t.thread_id === _activeThreadId;
            const timeStr = _formatTime(t.updated_at);
            const title = t.title || 'Untitled Chat';

            return `
                <div class="chat-item ${isActive ? 'active' : ''}"
                     data-thread-id="${t.thread_id}"
                     onclick="Sidebar._handleSelect('${t.thread_id}')">
                    <span class="chat-item-icon">💬</span>
                    <div class="chat-item-content">
                        <div class="chat-item-title" title="${_escapeAttr(title)}">${_escapeHtml(title)}</div>
                        <div class="chat-item-time">${timeStr}</div>
                    </div>
                    <button class="chat-item-delete"
                            onclick="event.stopPropagation(); Sidebar._handleDelete('${t.thread_id}')"
                            title="Delete chat">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            `;
        }).join('');
    }

    function _handleSelect(threadId) {
        if (_onThreadSelect) _onThreadSelect(threadId);
    }

    function _handleDelete(threadId) {
        if (_onThreadDelete) _onThreadDelete(threadId);
    }

    function _formatTime(isoString) {
        if (!isoString) return '';
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;
            return date.toLocaleDateString();
        } catch {
            return '';
        }
    }

    function _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function _escapeAttr(text) {
        return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    return {
        init,
        loadThreads,
        setActive,
        upsertThread,
        removeThread,
        clearActive,
        // Exposed for onclick handlers in rendered HTML
        _handleSelect,
        _handleDelete,
    };
})();
