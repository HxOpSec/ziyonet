(function () {
  const root = document.getElementById('adminContent');

  function authToken() {
    return localStorage.getItem('adminToken');
  }

  function showLogin() {
    root.innerHTML = `
      <h2>Вход</h2>
      <form id="loginForm" class="form-grid">
        <input name="username" placeholder="Логин" required />
        <input name="password" type="password" placeholder="Пароль" required />
        <button class="btn primary" type="submit">Войти</button>
      </form>`;

    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = new FormData(e.target);
      try {
        const data = await Api.login({
          username: form.get('username'),
          password: form.get('password'),
        });
        localStorage.setItem('adminToken', data.access_token);
        toast('Успешный вход');
        showBooks();
      } catch (err) {
        toast(err.message, 'err');
      }
    });
  }

  async function showBooks() {
    if (!authToken()) return showLogin();

    let books = [];
    try {
      const data = await Api.getBooks({ page: 1, per_page: 100, sort_by: 'title', order: 'asc' });
      books = data.items;
    } catch (err) {
      toast(err.message, 'err');
    }

    root.innerHTML = `
      <h2>Управление книгами</h2>
      <form id="bookForm" class="form-grid">
        <input name="title" placeholder="Название" required />
        <input name="author" placeholder="Автор" required />
        <input name="isbn" placeholder="ISBN" />
        <input name="category" placeholder="Категория" />
        <input name="year" type="number" placeholder="Год" />
        <input name="copies_total" type="number" placeholder="Всего экземпляров" value="1" />
        <input name="copies_available" type="number" placeholder="Доступно" value="1" />
        <textarea name="description" placeholder="Описание"></textarea>
        <button class="btn primary" type="submit">Добавить книгу</button>
      </form>
      <div class="table-wrap mt-md">
        <table>
          <thead><tr><th>ID</th><th>Название</th><th>Автор</th><th>Год</th><th>Доступно</th><th>Действия</th></tr></thead>
          <tbody id="booksTable"></tbody>
        </table>
      </div>`;

    const tbody = document.getElementById('booksTable');
    tbody.innerHTML = books
      .map(
        (b) => `<tr>
          <td>${b.id}</td><td>${escapeHtml(b.title)}</td><td>${escapeHtml(b.author)}</td><td>${b.year || '—'}</td><td>${b.copies_available}</td>
          <td>
            <button class="btn ghost" data-edit="${b.id}">Изменить</button>
            <button class="btn danger" data-delete="${b.id}">Удалить</button>
          </td>
        </tr>`
      )
      .join('');

    document.getElementById('bookForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = new FormData(e.target);
      const payload = Object.fromEntries(form.entries());
      payload.year = payload.year ? Number(payload.year) : null;
      payload.copies_total = Number(payload.copies_total || 1);
      payload.copies_available = Number(payload.copies_available || 1);
      try {
        await Api.createBook(payload);
        toast('Книга добавлена');
        showBooks();
      } catch (err) {
        toast(err.message, 'err');
      }
    });

    tbody.addEventListener('click', async (e) => {
      const id = e.target.getAttribute('data-delete');
      if (id) {
        if (!confirm('Удалить книгу?')) return;
        try {
          await Api.deleteBook(id);
          toast('Книга удалена');
          showBooks();
        } catch (err) {
          toast(err.message, 'err');
        }
      }

      const editId = e.target.getAttribute('data-edit');
      if (editId) {
        const title = prompt('Новое название');
        if (!title) return;
        try {
          await Api.updateBook(editId, { title });
          toast('Книга обновлена');
          showBooks();
        } catch (err) {
          toast(err.message, 'err');
        }
      }
    });
  }

  async function showStats() {
    if (!authToken()) return showLogin();
    try {
      const [stats, usage, popular] = await Promise.all([Api.stats(), Api.aiUsage(), Api.popularBooks()]);
      root.innerHTML = `
        <h2>Статистика</h2>
        <div class="row gap-md wrap">
          <div class="card-stat"><h3>${stats.books_total}</h3><p>Книг</p></div>
          <div class="card-stat"><h3>${stats.ai_requests_total}</h3><p>ИИ запросов</p></div>
          <div class="card-stat"><h3>${stats.users_total}</h3><p>Админов</p></div>
        </div>
        <h3 class="mt-md">Популярные книги</h3>
        <ul>${popular.map((p) => `<li>${escapeHtml(p.title)} — ${p.asks}</li>`).join('')}</ul>
        <h3 class="mt-md">Использование ИИ</h3>
        <ul>${usage.map((u) => `<li>${u.day}: fast=${u.fast_count}, deep=${u.deep_count}, avg=${Math.round(u.avg_response_time_ms)}ms</li>`).join('')}</ul>
        <div class="row gap-sm mt-md">
          <a class="btn ghost" href="/api/analytics/export/csv" target="_blank">Экспорт CSV</a>
          <a class="btn ghost" href="/api/analytics/export/pdf" target="_blank">Экспорт PDF</a>
        </div>`;
    } catch (err) {
      toast(err.message, 'err');
    }
  }

  document.querySelectorAll('[data-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      if (tab === 'login') showLogin();
      if (tab === 'books') showBooks();
      if (tab === 'stats') showStats();
    });
  });

  document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('adminToken');
    toast('Вы вышли');
    showLogin();
  });

  if (authToken()) showBooks();
  else showLogin();
})();
