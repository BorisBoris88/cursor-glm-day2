const MESSAGES_API_PATH = '/api/messages';
const BOT_USERNAME = 'Bot';
/** Схлопывает серию Enter/submit в одну отправку. */
const SEND_DEBOUNCE_MS = 400;
/** Минимальный интервал между успешными отправками. */
const SEND_MIN_INTERVAL_MS = 2000;

function initChat() {
  const toggleBtn = document.getElementById('chatToggle');
  const panel = document.getElementById('chatPanel');
  const closeBtn = document.getElementById('chatClose');
  const messagesEl = document.getElementById('chatMessages');
  const inputEl = document.getElementById('chatInput');
  const formEl = document.getElementById('chatForm');

  let sendDebounceTimer = null;
  let lastSentAt = 0;
  let isSending = false;

  /** Прокручивает ленту к последнему сообщению. */
  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  /** После открытия панели — дождаться layout и анимации, затем вниз. */
  function scrollToBottomAfterOpen() {
    requestAnimationFrame(() => {
      scrollToBottom();
      requestAnimationFrame(scrollToBottom);
    });
    window.setTimeout(scrollToBottom, 280);
  }

  function openChat() {
    panel.classList.add('chat-panel--open');
    toggleBtn.classList.add('chat-toggle--hidden');
    scrollToBottomAfterOpen();
    inputEl.focus();
  }

  function closeChat() {
    panel.classList.remove('chat-panel--open');
    toggleBtn.classList.remove('chat-toggle--hidden');
  }

  /** Свои пузыри — все человеческие сообщения, бот — только Bot. */
  function messageType(username) {
    const name = typeof username === 'string' ? username.trim().toLowerCase() : '';
    return name === BOT_USERNAME.toLowerCase() ? 'bot' : 'user';
  }

  function addMessage(text, type, animate) {
    const msg = document.createElement('div');
    msg.className =
      type === 'user'
        ? 'chat-message chat-message--user'
        : 'chat-message chat-message--bot';

    if (animate) {
      msg.classList.add('chat-message--appear');
    }
    msg.textContent = text;
    messagesEl.appendChild(msg);
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
      const type = messageType(message.username);
      addMessage(message.text, type, false);
    }
    scrollToBottom();
  }

  /**
   * POST нового сообщения на сервер.
   */
  async function handleUserMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || isSending) {
      return;
    }

    isSending = true;
    try {
      const response = await apiFetch(MESSAGES_API_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: trimmed }),
      });
      if (!response.ok) {
        throw new Error('Ошибка отправки /api/messages');
      }

      inputEl.value = '';
      lastSentAt = Date.now();
      const payload = await response.json();
      const created = Array.isArray(payload.messages) ? payload.messages : [];
      for (const message of created) {
        const type = messageType(message.username);
        addMessage(message.text, type, true);
      }
      scrollToBottom();
    } catch (error) {
      console.error(error);
    } finally {
      isSending = false;
    }
  }

  /** Отправляет текст из поля, если прошёл throttle после последней удачной отправки. */
  function flushScheduledSend() {
    const trimmed = inputEl.value.trim();
    if (!trimmed) {
      return;
    }
    if (isSending) {
      return;
    }
    if (Date.now() - lastSentAt < SEND_MIN_INTERVAL_MS) {
      return;
    }
    handleUserMessage(trimmed);
  }

  /**
   * Планирует отправку: серия Enter/submit → одна попытка после паузы.
   */
  function scheduleSend() {
    if (!inputEl.value.trim()) {
      return;
    }

    if (sendDebounceTimer !== null) {
      clearTimeout(sendDebounceTimer);
    }

    sendDebounceTimer = window.setTimeout(() => {
      sendDebounceTimer = null;
      flushScheduledSend();
    }, SEND_DEBOUNCE_MS);
  }

  toggleBtn.addEventListener('click', openChat);
  closeBtn.addEventListener('click', closeChat);

  formEl.addEventListener('submit', (e) => {
    e.preventDefault();
    scheduleSend();
  });

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      scheduleSend();
    }
  });

  loadMessages().catch((error) => {
    console.error(error);
  });
}

initChat();
