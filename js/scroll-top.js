/**
 * Кнопка «Наверх»: показывается после прокрутки, поднимается над открытым чатом.
 */
function initScrollTop() {
  const button = document.getElementById('scrollTopBtn');
  const chatPanel = document.getElementById('chatPanel');
  if (!button) {
    return;
  }

  const showAfterPx = 320;
  const gapPx = 12;
  const defaultBottomPx = 92;

  function updateVisibility() {
    const visible = window.scrollY > showAfterPx;
    button.hidden = !visible;
    button.classList.toggle('scroll-top--hidden', !visible);
  }

  /** Сдвигает кнопку над панелью чата или в угол под шапкой на мобильном. */
  function syncPositionWithChat() {
    if (!chatPanel || button.hidden) {
      button.style.bottom = '';
      button.style.top = '';
      button.classList.remove('scroll-top--above-chat');
      document.body.classList.remove('chat-open');
      return;
    }

    const isChatOpen = chatPanel.classList.contains('chat-panel--open');
    document.body.classList.toggle('chat-open', isChatOpen);

    if (!isChatOpen) {
      button.style.bottom = '';
      button.style.top = '';
      button.classList.remove('scroll-top--above-chat');
      return;
    }

    button.classList.add('scroll-top--above-chat');
    const panelRect = chatPanel.getBoundingClientRect();
    const isFullscreenChat =
      window.matchMedia('(max-width: 767px)').matches &&
      panelRect.height >= window.innerHeight * 0.85;

    if (isFullscreenChat) {
      button.style.bottom = 'auto';
      button.style.top = '4.5rem';
      return;
    }

    button.style.top = 'auto';
    const offsetFromBottom = Math.max(
      window.innerHeight - panelRect.top + gapPx,
      defaultBottomPx
    );
    button.style.bottom = `${offsetFromBottom}px`;
  }

  function scheduleChatSync() {
    syncPositionWithChat();
    window.setTimeout(syncPositionWithChat, 280);
  }

  function refresh() {
    updateVisibility();
    syncPositionWithChat();
  }

  button.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  window.addEventListener('scroll', refresh, { passive: true });
  window.addEventListener('resize', syncPositionWithChat, { passive: true });

  if (chatPanel) {
    const observer = new MutationObserver(scheduleChatSync);
    observer.observe(chatPanel, {
      attributes: true,
      attributeFilter: ['class'],
    });
  }

  refresh();
}

document.addEventListener('DOMContentLoaded', initScrollTop);
