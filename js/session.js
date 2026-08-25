/**
 * Показывает логин в шапке.
 * @param {string} username
 */
function showHeaderUsername(username) {
  const usernameEl = document.getElementById('headerUsername');
  if (!usernameEl || !username) {
    return;
  }

  usernameEl.textContent = username;
  usernameEl.removeAttribute('hidden');
}

/**
 * Загружает логин: сначала из sessionStorage, затем подтверждает через /api/me.
 */
async function initHeaderUsername() {
  const usernameEl = document.getElementById('headerUsername');
  if (!usernameEl) {
    return;
  }

  const cachedUsername = readAuthUsername();
  if (cachedUsername) {
    showHeaderUsername(cachedUsername);
  }

  try {
    const response = await apiFetch('/api/me');
    if (!response.ok) {
      clearAuthUsername();
      usernameEl.hidden = true;
      usernameEl.textContent = '';
      return;
    }

    const data = await response.json();
    if (typeof data.username !== 'string' || !data.username.trim()) {
      return;
    }

    saveAuthUsername(data.username);
    showHeaderUsername(data.username);
  } catch (error) {
    console.error('Не удалось загрузить профиль:', error);
  }
}

function bootHeaderUsername() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeaderUsername, { once: true });
    return;
  }
  initHeaderUsername();
}

bootHeaderUsername();
window.addEventListener('pageshow', initHeaderUsername);
