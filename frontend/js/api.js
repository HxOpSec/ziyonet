const API_BASE = 'http://127.0.0.1:8000/api';
const REQUEST_TIMEOUT_MS = 95000;

function sanitizeInput(value, maxLen = 1000) {
    if (value === null || value === undefined) return '';
    return String(value)
        .slice(0, maxLen)
        .replace(/[<>"'`\\]/g, '')
        .replace(/[\u0000-\u001F\u007F]/g, '')
        .trim();
}

function toQuery(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value === null || value === undefined) return;
        if (typeof value === 'string') {
            const cleaned = sanitizeInput(value, 300);
            if (!cleaned) return;
            query.append(key, cleaned);
            return;
        }
        query.append(key, String(value));
    });
    const q = query.toString();
    return q ? `?${q}` : '';
}

const Api = {
    async request(path, options = {}) {
        const token = localStorage.getItem('adminToken');
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        };
        if (token) headers.Authorization = `Bearer ${token}`;

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
        let res;
        try {
            res = await fetch(`${API_BASE}${path}`, { ...options, headers, signal: controller.signal });
        } catch (err) {
            if (err?.name === 'AbortError') {
                throw new Error('Сервер отвечает слишком долго. Попробуйте ещё раз.');
            }
            throw new Error('Не удалось подключиться к серверу.');
        } finally {
            clearTimeout(timer);
        }
        if (!res.ok) {
            const data = await res.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(data.detail || 'Request failed');
        }
        if (res.status === 204) return null;
        const type = res.headers.get('content-type') || '';
        return type.includes('application/json') ? res.json() : res.text();
    },

    getBooks(params = {}) {
        const q = toQuery(params);
        return this.request(`/books${q}`);
    },

    getBook(id) {
        return this.request(`/books/${id}`);
    },

    createBook(payload) {
        return this.request('/books', { method: 'POST', body: JSON.stringify(payload) });
    },

    updateBook(id, payload) {
        return this.request(`/books/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
    },

    deleteBook(id) {
        return this.request(`/books/${id}`, { method: 'DELETE' });
    },

    login(payload) {
        return this.request('/admin/login', { method: 'POST', body: JSON.stringify(payload) });
    },

    stats() {
        return this.request('/admin/stats');
    },

    logs() {
        return this.request('/admin/logs');
    },

    chat(payload) {
        const safePayload = {
            message: sanitizeInput(payload.message, 1000),
            mode: payload.mode === 'deep' ? 'deep' : 'fast',
            book_id: Number.isInteger(payload.book_id) ? payload.book_id : null,
        };
        return this.request('/chat', { method: 'POST', body: JSON.stringify(safePayload) });
    },

    aiUsage() {
        return this.request('/analytics/ai-usage');
    },

    popularBooks() {
        return this.request('/analytics/popular-books');
    },
};

window.Api = Api;
