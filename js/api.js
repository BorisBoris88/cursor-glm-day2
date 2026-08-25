/**
 * Собирает URL API: с диска — localhost, с сервера — относительный путь.
 * @param {string} path путь вида /api/weather
 * @returns {string}
 */
function apiUrl(path) {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (location.protocol === 'file:') {
    return `http://localhost:8080${normalized}`;
  }
  return normalized;
}

/**
 * fetch к API с передачей сессионной куки.
 * @param {string} path путь вида /api/weather
 * @param {RequestInit} [options]
 * @returns {Promise<Response>}
 */
function apiFetch(path, options = {}) {
  return fetch(apiUrl(path), {
    credentials: 'same-origin',
    ...options,
  });
}

const AUTH_USERNAME_STORAGE_KEY = 'auth_username';

/**
 * Сохраняет логин для мгновенного показа в шапке после редиректа.
 * @param {string} username
 */
function saveAuthUsername(username) {
  sessionStorage.setItem(AUTH_USERNAME_STORAGE_KEY, username);
}

/**
 * @returns {string | null}
 */
function readAuthUsername() {
  return sessionStorage.getItem(AUTH_USERNAME_STORAGE_KEY);
}

function clearAuthUsername() {
  sessionStorage.removeItem(AUTH_USERNAME_STORAGE_KEY);
}
