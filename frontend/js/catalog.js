window.Catalog = (() => {
  const BOOKS_CACHE_TTL_MS = 5 * 60 * 1000;

  const state = {
    page: 1,
    per_page: 20,
    q: '',
    category: '',
    year: '',
    available: '',
    sort_by: 'created_at',
    order: 'desc',
    total: 0,
    books: [],
    favorites: new Set(JSON.parse(localStorage.getItem('favorites') || '[]')),
  };

  function persistFavorites() {
    localStorage.setItem('favorites', JSON.stringify([...state.favorites]));
  }

  function bookCard(book) {
    const fav = state.favorites.has(book.id) ? '★' : '☆';
    return `
      <article class="book-card scale-on-hover">
        <img loading="lazy" src="${book.cover_url || 'https://placehold.co/240x320?text=No+Cover'}" alt="cover" />
        <div class="book-body">
          <h3>${escapeHtml(book.title)}</h3>
          <p>${escapeHtml(book.author)}</p>
          <p class="muted">${book.year || '—'} · ${escapeHtml(book.category || 'Без категории')}</p>
          <p class="clamp">${escapeHtml(book.description || 'Нет описания')}</p>
          <div class="row gap-sm">
            <button class="btn ghost" data-preview="${book.id}">Быстрый просмотр</button>
            <button class="btn ghost" data-favorite="${book.id}">${fav}</button>
            <a class="btn primary" href="/book-detail.html?id=${book.id}">Открыть</a>
          </div>
        </div>
      </article>`;
  }

  function openPreview(book) {
    const modal = document.getElementById('quickModal');
    const body = document.getElementById('modalBody');
    body.innerHTML = `
      <h3>${escapeHtml(book.title)}</h3>
      <p><b>Автор:</b> ${escapeHtml(book.author)}</p>
      <p><b>ISBN:</b> ${escapeHtml(book.isbn || '—')}</p>
      <p><b>Категория:</b> ${escapeHtml(book.category || '—')}</p>
      <p>${escapeHtml(book.description || 'Нет описания')}</p>`;
    modal.classList.remove('hidden');
  }

  function bindGrid() {
    const grid = document.getElementById('booksGrid');
    grid.addEventListener('click', (e) => {
      const previewId = e.target.getAttribute('data-preview');
      const favoriteId = e.target.getAttribute('data-favorite');
      if (previewId) {
        const book = state.books.find((b) => String(b.id) === String(previewId));
        if (book) openPreview(book);
      }
      if (favoriteId) {
        const id = Number(favoriteId);
        if (state.favorites.has(id)) state.favorites.delete(id);
        else state.favorites.add(id);
        persistFavorites();
        renderGrid();
      }
    });
  }

  function renderGrid() {
    const grid = document.getElementById('booksGrid');
    if (!state.books.length) {
      grid.innerHTML = '<div class="skeleton">Книги не найдены</div>';
      return;
    }
    grid.innerHTML = state.books.map(bookCard).join('');
  }

  function updatePagination() {
    const totalPages = Math.max(1, Math.ceil(state.total / state.per_page));
    document.getElementById('pageInfo').textContent = `Страница ${state.page} из ${totalPages}`;
    document.getElementById('prevPage').disabled = state.page <= 1;
    document.getElementById('nextPage').disabled = state.page >= totalPages;
  }

  async function loadBooks() {
    const cacheKey = `books_cache:${JSON.stringify(state)}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      const value = JSON.parse(cached);
      if (Date.now() - value.time < BOOKS_CACHE_TTL_MS) {
        state.books = value.data.items;
        state.total = value.data.total;
        renderGrid();
        updatePagination();
        fillBookContext();
      }
    }

    document.getElementById('booksGrid').innerHTML = '<div class="skeleton pulse">Загрузка книг...</div>';
    try {
      // Фильтруем пустые параметры
      const params = {
        page: state.page,
        per_page: state.per_page,
        sort_by: state.sort_by,
        order: state.order,
      };
      if (state.q && state.q.trim()) params.q = state.q.trim();
      if (state.category && state.category.trim()) params.category = state.category.trim();
      if (state.year && state.year !== "") params.year = state.year;
      if (state.available && state.available !== "") params.available = state.available;

      const data = await Api.getBooks(params);
      state.books = data.items;
      state.total = data.total;
      localStorage.setItem(cacheKey, JSON.stringify({ time: Date.now(), data }));
      renderGrid();
      updatePagination();
      fillBookContext();
      fillCategories();
    } catch (e) {
      toast(e.message, 'err');
    }
  }

  function fillBookContext() {
    const select = document.getElementById('bookContextSelect');
    const current = select.value;
    const options = ['<option value="">Без контекста книги</option>'];
    state.books.forEach((b) => options.push(`<option value="${b.id}">${escapeHtml(b.title)}</option>`));
    select.innerHTML = options.join('');
    select.value = current;
  }

  function fillCategories() {
    const select = document.getElementById('categoryFilter');
    const existing = new Set([...select.options].map((o) => o.value));
    state.books.forEach((b) => {
      if (b.category && !existing.has(b.category)) {
        const opt = document.createElement('option');
        opt.value = b.category;
        opt.textContent = b.category;
        select.appendChild(opt);
      }
    });
  }

  function bindFilters() {
    const debounced = debounce(() => {
      state.page = 1;
      state.q = document.getElementById('searchInput').value.trim();
      state.category = document.getElementById('categoryFilter').value;
      state.year = document.getElementById('yearFilter').value;
      state.available = document.getElementById('availabilityFilter').value;
      state.sort_by = document.getElementById('sortBy').value;
      state.order = document.getElementById('orderBy').value;
      loadBooks();
    }, 300);

    ['searchInput', 'categoryFilter', 'yearFilter', 'availabilityFilter', 'sortBy', 'orderBy'].forEach((id) => {
      document.getElementById(id).addEventListener('input', debounced);
      document.getElementById(id).addEventListener('change', debounced);
    });

    document.getElementById('prevPage').addEventListener('click', () => {
      if (state.page > 1) {
        state.page -= 1;
        loadBooks();
      }
    });

    document.getElementById('nextPage').addEventListener('click', () => {
      state.page += 1;
      loadBooks();
    });

    document.getElementById('modalClose').addEventListener('click', () => {
      document.getElementById('quickModal').classList.add('hidden');
    });
  }

  return {
    init() {
      bindGrid();
      bindFilters();
      loadBooks();
    },
    getState() {
      return state;
    },
  };
})();
