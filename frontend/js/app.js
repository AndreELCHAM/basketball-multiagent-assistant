/**
 * App Controller
 * Main application logic — ties together API, Chat, and Sidebar modules.
 * Manages thread state, message sending, and UI transitions.
 */

const App = (() => {
    let _currentThreadId = null;
    let _isProcessing = false;
    let _pendingLeagueQuery = null;   // Stored query when league prompt is active

    // ── Initialization ────────────────────────────────────────────────

    function init() {
        // Initialize sidebar
        Sidebar.init({
            onThreadSelect: _loadThread,
            onThreadDelete: _deleteThread,
        });

        // Load existing threads
        Sidebar.loadThreads();

        // Check system health
        _checkHealth();

        // Event listeners
        document.getElementById('newChatBtn').addEventListener('click', _newChat);
        document.getElementById('sendBtn').addEventListener('click', _handleSend);

        const input = document.getElementById('queryInput');
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                _handleSend();
            }
        });

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 150) + 'px';
        });

        // Feature cards on welcome screen
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('click', () => {
                const query = card.dataset.query;
                if (query) {
                    input.value = query;
                    input.style.height = 'auto';
                    input.style.height = Math.min(input.scrollHeight, 150) + 'px';
                    _handleSend();
                }
            });
        });

        // Mobile sidebar toggle
        document.getElementById('sidebarToggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });

        // Close sidebar on mobile when clicking main content
        document.getElementById('mainContent').addEventListener('click', () => {
            document.getElementById('sidebar').classList.remove('open');
        });
    }

    // ── Chat Actions ──────────────────────────────────────────────────

    async function _handleSend() {
        if (_isProcessing) return;

        const input = document.getElementById('queryInput');
        const query = input.value.trim();
        if (!query) return;

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Ensure chat view is active
        _showChatView();

        // Add user message to UI
        Chat.addUserMessage(query);

        // Show loading
        Chat.showLoading();
        _setProcessing(true);

        try {
            const response = await API.sendMessage(query, _currentThreadId);

            // Update thread ID (important for new chats)
            _currentThreadId = response.thread_id;

            // Update sidebar
            const title = query.substring(0, 80) + (query.length > 80 ? '...' : '');
            Sidebar.upsertThread(_currentThreadId, title);
            Sidebar.setActive(_currentThreadId);

            // Update chat header
            document.getElementById('chatTitle').textContent = title;

            // Handle response based on type
            if (response.response_type === 'league_prompt') {
                _handleLeaguePrompt(response, query);
            } else {
                Chat.addAssistantMessage(response);
            }

        } catch (error) {
            Chat.addAssistantMessage({
                answer: `⚠️ Error: ${error.message}\n\nPlease check that the backend is running and try again.`,
                chunks: [],
                image_paths: [],
                response_type: 'error',
            });
        } finally {
            _setProcessing(false);
        }
    }

    function _handleLeaguePrompt(response, originalQuery) {
        // Store the original query for re-submission with league
        _pendingLeagueQuery = originalQuery;

        // Show the assistant's league prompt message
        Chat.addAssistantMessage({
            answer: response.answer || response.human_input_message || 'Which league is your question about?',
            chunks: [],
            image_paths: [],
            response_type: 'league_prompt',
        });

        // Show league selection modal
        const options = response.human_input_options || ['NBA', 'FIBA', 'NCAA', 'FIBA_3x3'];
        Chat.showLeaguePrompt(
            response.human_input_message || 'Select a league:',
            options,
            (selectedLeague) => _handleLeagueSelection(selectedLeague)
        );
    }

    async function _handleLeagueSelection(league) {
        Chat.hideLeaguePrompt();

        // Show user's selection as a message
        Chat.addUserMessage(league);

        // Show loading
        Chat.showLoading();
        _setProcessing(true);

        try {
            // Send the league selection — API will re-run the original query with league
            const response = await API.sendMessage(league, _currentThreadId, league);

            _currentThreadId = response.thread_id;
            Chat.addAssistantMessage(response);

        } catch (error) {
            Chat.addAssistantMessage({
                answer: `⚠️ Error: ${error.message}`,
                chunks: [],
                image_paths: [],
                response_type: 'error',
            });
        } finally {
            _setProcessing(false);
            _pendingLeagueQuery = null;
        }
    }

    // ── Thread Management ─────────────────────────────────────────────

    function _newChat() {
        _currentThreadId = null;
        _pendingLeagueQuery = null;

        Chat.clearMessages();
        Sidebar.clearActive();
        _showWelcomeView();

        document.getElementById('queryInput').focus();

        // Close mobile sidebar
        document.getElementById('sidebar').classList.remove('open');
    }

    async function _loadThread(threadId) {
        if (threadId === _currentThreadId) return;

        try {
            const thread = await API.getThread(threadId);
            _currentThreadId = threadId;

            _showChatView();
            document.getElementById('chatTitle').textContent = thread.title || 'Chat';

            // Render conversation history
            Chat.renderHistory(thread.messages || []);

            Sidebar.setActive(threadId);

            // Close mobile sidebar
            document.getElementById('sidebar').classList.remove('open');

        } catch (error) {
            console.error('Failed to load thread:', error);
        }
    }

    async function _deleteThread(threadId) {
        try {
            await API.deleteThread(threadId);
            Sidebar.removeThread(threadId);

            // If we deleted the active thread, go to welcome
            if (threadId === _currentThreadId) {
                _newChat();
            }
        } catch (error) {
            console.error('Failed to delete thread:', error);
        }
    }

    // ── UI State ──────────────────────────────────────────────────────

    function _showWelcomeView() {
        document.getElementById('welcomeScreen').style.display = 'flex';
        document.getElementById('chatContainer').style.display = 'none';
    }

    function _showChatView() {
        document.getElementById('welcomeScreen').style.display = 'none';
        document.getElementById('chatContainer').style.display = 'flex';
    }

    function _setProcessing(processing) {
        _isProcessing = processing;
        const btn = document.getElementById('sendBtn');
        btn.disabled = processing;
    }

    async function _checkHealth() {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        try {
            const health = await API.healthCheck();
            statusDot.className = 'status-dot online';
            statusText.textContent = 'System Online';
        } catch {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'System Offline';
        }
    }

    return { init };
})();

// ── Bootstrap ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', App.init);
