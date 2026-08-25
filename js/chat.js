const MESSAGES_API_PATH = '/api/messages';

const CHAT_USERNAME = 'Neo';

function initChat() {
  const toggleBtn = document.getElementById('chatToggle');
  const panel = document.getElementById('chatPanel');
  const closeBtn = document.getElementById('chatClose');
  const messagesEl = document.getElementById('chatMessages');
  const inputEl = document.getElementById('chatInput');
  const formEl = document.getElementById('chatForm');

  function openChat() {
    panel.classList.add('chat-panel--open');
    toggleBtn.classList.add('chat-toggle--hidden');
    inputEl.focus();
  }

  function closeChat() {
    panel.classList.remove('chat-panel--open');
    toggleBtn.classList.remove('chat-toggle--hidden');
  }

  function addMessage(text, type, animate) {
    const msg = document.createElement('div');
    msg.className = `chat-message chat-message--${type}`;
    if (animate) {
      msg.classList.add('chat-message--appear');
    }
    msg.textContent = text;
    messagesEl.appendChild(msg);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return msg;
  }

  /**
   * GET /api/messages — рисует сообщения из базы в окне чата.
   */
  async function loadMessages() {
    const response = await apiFetch(MESSAGES_API_PATH);
    if (!response.ok) {
      throw new Error('Ошибка загрузки /api/messages');
    }

    const data = await response.json();
    const messages = Array.isArray(data.messages) ? data.messages : [];

    messagesEl.replaceChildren();
    for (const message of messages) {
      const type = message.username === CHAT_USERNAME ? 'user' : 'bot';
      addMessage(message.text, type, false);
    }
  }

  /**
   * POST нового сообщения, затем снова загружает ленту с сервера.
   */
  async function handleUserMessage(text) {
    const trimmed = text.trim();
    if (!trimmed) return;

    try {
      const response = await apiFetch(MESSAGES_API_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: CHAT_USERNAME, text: trimmed }),
      });
      if (!response.ok) {
        throw new Error('Ошибка отправки /api/messages');
      }

      inputEl.value = '';
      const payload = await response.json();
      const created = Array.isArray(payload.messages) ? payload.messages : [];
      for (const message of created) {
        const type = message.username === CHAT_USERNAME ? 'user' : 'bot';
        addMessage(message.text, type, true);
      }
    } catch (error) {
      console.error(error);
    }
  }

  toggleBtn.addEventListener('click', openChat);
  closeBtn.addEventListener('click', closeChat);

  formEl.addEventListener('submit', (e) => {
    e.preventDefault();
    handleUserMessage(inputEl.value);
  });

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleUserMessage(inputEl.value);
    }
  });

  loadMessages().catch((error) => {
    console.error(error);
  });
}

initChat();
