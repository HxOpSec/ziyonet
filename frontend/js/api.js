const API_BASE = 'http://127.0.0.1:8000/api';

const Api = {
  async request(path, options = {}) {
    const token = localStorage.getItem('adminToken');
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(data.detail || 'Request failed');
    }
    if (res.status === 204) return null;
    const type = res.headers.get('content-type') || '';
    return type.includes('application/json') ? res.json() : res.text();
  },

  getBooks(params = {}) {
    const q = new URLSearchParams(params).toString();
    const path = q ? `/books?${q}` : '/books';
    return this.request(path);
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
    return this.request('/chat', { method: 'POST', body: JSON.stringify(payload) });
  },

  aiUsage() {
    return this.request('/analytics/ai-usage');
  },

  popularBooks() {
    return this.request('/analytics/popular-books');
  },
};

window.Api = Api;
