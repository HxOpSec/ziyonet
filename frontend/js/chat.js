window.Chat = (() => {
  function addMessage(role, text) {
    const box = document.getElementById('chatMessages');
    const item = document.createElement('div');
    item.className = `chat-msg ${role} slide-up`;
    item.innerHTML = `<p>${escapeHtml(text)}</p>`;
    box.appendChild(item);
    box.scrollTop = box.scrollHeight;
  }

  async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    const mode = document.querySelector('input[name="mode"]:checked').value;
    const book_id = document.getElementById('bookContextSelect').value || null;

    addMessage('user', message);
    input.value = '';
    addMessage('assistant', 'Думаю...');

    try {
      const data = await Api.chat({ message, mode, book_id: book_id ? Number(book_id) : null });
      const box = document.getElementById('chatMessages');
      box.lastElementChild.remove();
      addMessage('assistant', `${data.answer}\n\n(${data.response_time_ms} ms${data.cached ? ', cache' : ''})`);
    } catch (e) {
      const box = document.getElementById('chatMessages');
      box.lastElementChild.remove();
      addMessage('assistant', `Ошибка: ${e.message}`);
    }
  }

  return {
    init() {
      document.getElementById('sendBtn').addEventListener('click', sendMessage);
      document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    },
  };
})();
