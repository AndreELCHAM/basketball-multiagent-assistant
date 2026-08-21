/**
 * API Client Module
 * Handles all HTTP communication with the System A backend.
 */

const API = (() => {
    const BASE_URL = '/api';

    async function _fetch(url, options = {}) {
        const response = await fetch(`${BASE_URL}${url}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });

        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error');
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        return response.json();
    }

    /**
     * Send a chat message. Creates a new thread if threadId is not provided.
     * Returns the full ChatResponse.
     */
    async function sendMessage(query, threadId = null, league = null) {
        const body = { query };
        if (threadId) body.thread_id = threadId;
        if (league) body.league = league;

        return _fetch('/chat', {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    /**
     * List all saved threads (most recent first).
     */
    async function listThreads() {
        const data = await _fetch('/threads');
        return data.threads || [];
    }

    /**
     * Get full thread detail including all messages.
     */
    async function getThread(threadId) {
        return _fetch(`/threads/${threadId}`);
    }

    /**
     * Delete a thread.
     */
    async function deleteThread(threadId) {
        return _fetch(`/threads/${threadId}`, { method: 'DELETE' });
    }

    /**
     * Health check.
     */
    async function healthCheck() {
        return _fetch('/health');
    }

    return { sendMessage, listThreads, getThread, deleteThread, healthCheck };
})();
