const LOGIN_API_PATH = '/api/login';
const REGISTER_API_PATH = '/api/register';
const LOGIN_DENIED_MESSAGE = 'Доступ запрещен';
const LOGIN_RATE_LIMIT_MESSAGE = 'Слишком много попыток входа. Попробуйте позже.';
const LOGIN_BLOCK_UNTIL_KEY = 'login_blocked_until';
const LOGIN_FAIL_COUNT_KEY = 'login_fail_count';
const LOGIN_FAIL_COUNT_TS_KEY = 'login_fail_count_at';
const LOGIN_FAIL_MAX = 3;
const LOGIN_FAIL_WINDOW_MS = 60_000;
const LOGIN_BLOCK_MS = 60_000;

let loginRateLimitTimerId = null;

/**
 * Читает поле error из JSON-ответа API.
 * @param {Response} response
 * @param {string} fallback
 * @returns {Promise<string>}
 */
async function readApiErrorMessage(response, fallback) {
  try {
    const data = await response.json();
    if (typeof data.error === 'string' && data.error.trim()) {
      return data.error.trim();
    }
  } catch (error) {
    console.error(error);
  }
  return fallback;
}

function pruneLegacyLoginStorage() {
  sessionStorage.removeItem('login_failed_at');
}

function readFailCountState() {
  pruneLegacyLoginStorage();
  try {
    const rawCount = sessionStorage.getItem(LOGIN_FAIL_COUNT_KEY);
    const rawTs = sessionStorage.getItem(LOGIN_FAIL_COUNT_TS_KEY);
    if (!rawCount || !rawTs) {
      return { count: 0, startedAt: 0 };
    }
    const count = Number(rawCount);
    const startedAt = Number(rawTs);
    if (!Number.isFinite(count) || !Number.isFinite(startedAt)) {
      return { count: 0, startedAt: 0 };
    }
    if (Date.now() - startedAt >= LOGIN_FAIL_WINDOW_MS) {
      sessionStorage.removeItem(LOGIN_FAIL_COUNT_KEY);
      sessionStorage.removeItem(LOGIN_FAIL_COUNT_TS_KEY);
      return { count: 0, startedAt: 0 };
    }
    return { count, startedAt };
  } catch (error) {
    console.error(error);
    return { count: 0, startedAt: 0 };
  }
}

function recordLoginFailureClient() {
  const state = readFailCountState();
  const count = state.count + 1;
  const startedAt = state.count === 0 ? Date.now() : state.startedAt;
  sessionStorage.setItem(LOGIN_FAIL_COUNT_KEY, String(count));
  sessionStorage.setItem(LOGIN_FAIL_COUNT_TS_KEY, String(startedAt));
  if (count >= LOGIN_FAIL_MAX) {
    setLoginBlockedForMs(LOGIN_BLOCK_MS);
  }
  return count;
}

function clearLoginFailureTimes() {
  pruneLegacyLoginStorage();
  sessionStorage.removeItem(LOGIN_FAIL_COUNT_KEY);
  sessionStorage.removeItem(LOGIN_FAIL_COUNT_TS_KEY);
  clearLoginBlockedUntil();
}

function getLoginBlockedUntil() {
  pruneLegacyLoginStorage();
  const raw = sessionStorage.getItem(LOGIN_BLOCK_UNTIL_KEY);
  if (!raw) {
    return 0;
  }
  const until = Number(raw);
  if (!Number.isFinite(until) || Date.now() >= until) {
    sessionStorage.removeItem(LOGIN_BLOCK_UNTIL_KEY);
    return 0;
  }
  return until;
}

function setLoginBlockedForMs(durationMs) {
  sessionStorage.setItem(
    LOGIN_BLOCK_UNTIL_KEY,
    String(Date.now() + durationMs)
  );
}

function clearLoginBlockedUntil() {
  sessionStorage.removeItem(LOGIN_BLOCK_UNTIL_KEY);
}

function getLoginBlockSecondsLeft() {
  const until = getLoginBlockedUntil();
  if (!until) {
    return 0;
  }
  return Math.max(1, Math.ceil((until - Date.now()) / 1000));
}

function isLoginRateLimitedClient() {
  return getLoginBlockSecondsLeft() > 0;
}

function buildRateLimitMessage() {
  const secondsLeft = getLoginBlockSecondsLeft();
  if (secondsLeft <= 0) {
    return LOGIN_RATE_LIMIT_MESSAGE;
  }
  return `Слишком много попыток входа. Повторите через ${secondsLeft} сек.`;
}

/**
 * Показывает ошибку входа без сдвига карточки.
 * @param {HTMLElement} errorEl
 * @param {string} message
 * @param {boolean} rateLimited
 */
function showLoginError(errorEl, message, rateLimited) {
  errorEl.textContent = message;
  errorEl.classList.toggle('login-form__error--rate-limit', rateLimited);
  errorEl.hidden = false;
}

function hideLoginError(errorEl) {
  errorEl.hidden = true;
  errorEl.classList.remove('login-form__error--rate-limit');
}

/**
 * Обновляет таймер блокировки на форме входа.
 * @param {HTMLElement} errorEl
 */
function refreshLoginRateLimitUi(errorEl) {
  if (!errorEl) {
    return;
  }
  if (!isLoginRateLimitedClient()) {
    stopLoginRateLimitTimer();
    if (errorEl.classList.contains('login-form__error--rate-limit')) {
      hideLoginError(errorEl);
    }
    return;
  }
  showLoginError(errorEl, buildRateLimitMessage(), true);
}

function stopLoginRateLimitTimer() {
  if (loginRateLimitTimerId !== null) {
    window.clearInterval(loginRateLimitTimerId);
    loginRateLimitTimerId = null;
  }
}

/**
 * Запускает обратный отсчёт до разблокировки.
 * @param {HTMLElement} errorEl
 */
function startLoginRateLimitTimer(errorEl) {
  refreshLoginRateLimitUi(errorEl);
  if (!isLoginRateLimitedClient()) {
    return;
  }
  stopLoginRateLimitTimer();
  loginRateLimitTimerId = window.setInterval(() => {
    refreshLoginRateLimitUi(errorEl);
  }, 1000);
}

/**
 * Переключает вкладки «Вход» и «Регистрация».
 */
function initAuthTabs() {
  const loginTab = document.getElementById('loginTab');
  const registerTab = document.getElementById('registerTab');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const loginHint = document.getElementById('loginHint');
  const loginError = document.getElementById('loginError');
  const registerError = document.getElementById('registerError');

  if (!loginTab || !registerTab || !loginForm || !registerForm || !loginHint) {
    return;
  }

  function showLogin() {
    loginTab.classList.add('login-form__tab--active');
    registerTab.classList.remove('login-form__tab--active');
    loginTab.setAttribute('aria-selected', 'true');
    registerTab.setAttribute('aria-selected', 'false');
    loginForm.hidden = false;
    loginForm.classList.remove('login-form__body--hidden');
    registerForm.hidden = true;
    registerForm.classList.add('login-form__body--hidden');
    loginHint.textContent = 'Введите учётные данные для входа в неоновый сектор.';
    loginError.textContent = LOGIN_DENIED_MESSAGE;
    loginError.classList.remove('login-form__error--rate-limit');
    loginError.hidden = true;
    registerError.hidden = true;
    startLoginRateLimitTimer(loginError);
  }

  function showRegister() {
    registerTab.classList.add('login-form__tab--active');
    loginTab.classList.remove('login-form__tab--active');
    registerTab.setAttribute('aria-selected', 'true');
    loginTab.setAttribute('aria-selected', 'false');
    registerForm.hidden = false;
    registerForm.classList.remove('login-form__body--hidden');
    loginForm.hidden = true;
    loginForm.classList.add('login-form__body--hidden');
    loginHint.textContent = 'Создайте новый аккаунт для доступа к NeonShadow.';
    loginError.hidden = true;
    registerError.hidden = true;
    stopLoginRateLimitTimer();
  }

  loginTab.addEventListener('click', showLogin);
  registerTab.addEventListener('click', showRegister);
}

/**
 * Отправляет учётные данные на /api/login и обрабатывает ответ.
 */
function initLogin() {
  const formEl = document.getElementById('loginForm');
  const usernameEl = document.getElementById('loginInput');
  const passwordEl = document.getElementById('passwordInput');
  const errorEl = document.getElementById('loginError');
  const submitBtn = document.getElementById('loginSubmitBtn');

  if (!formEl || !usernameEl || !passwordEl || !errorEl || !submitBtn) {
    return;
  }

  startLoginRateLimitTimer(errorEl);

  formEl.addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = usernameEl.value.trim();
    const password = passwordEl.value;

    if (!username || !password) {
      return;
    }

    if (isLoginRateLimitedClient()) {
      startLoginRateLimitTimer(errorEl);
      return;
    }

    hideLoginError(errorEl);
    submitBtn.disabled = true;

    try {
      const response = await apiFetch(LOGIN_API_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        clearLoginFailureTimes();
        saveAuthUsername(username);
        window.location.href = '/';
        return;
      }

      if (response.status === 401) {
        recordLoginFailureClient();
      } else if (response.status === 429) {
        setLoginBlockedForMs(LOGIN_BLOCK_MS);
        sessionStorage.removeItem(LOGIN_FAIL_COUNT_KEY);
        sessionStorage.removeItem(LOGIN_FAIL_COUNT_TS_KEY);
      }

      if (response.status === 401 || response.status === 429) {
        const rateLimited =
          response.status === 429 || isLoginRateLimitedClient();
        if (rateLimited) {
          startLoginRateLimitTimer(errorEl);
        } else {
          const message = await readApiErrorMessage(
            response,
            LOGIN_DENIED_MESSAGE
          );
          showLoginError(errorEl, message, false);
        }
        return;
      }

      showLoginError(errorEl, 'Не удалось выполнить вход', false);
    } catch (error) {
      console.error('Ошибка входа:', error);
      showLoginError(
        errorEl,
        'Сервер недоступен. Проверьте, что запущен python server.py',
        false
      );
    } finally {
      submitBtn.disabled = false;
    }
  });
}

/**
 * Регистрирует пользователя через POST /api/register.
 */
function initRegister() {
  const formEl = document.getElementById('registerForm');
  const errorEl = document.getElementById('registerError');
  const submitBtn = document.getElementById('registerSubmitBtn');

  if (!formEl || !errorEl || !submitBtn) {
    return;
  }

  formEl.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorEl.hidden = true;

    const username = formEl.username.value.trim();
    const password = formEl.password.value;

    if (!username || !password) {
      return;
    }

    submitBtn.disabled = true;

    try {
      const response = await apiFetch(REGISTER_API_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        clearLoginFailureTimes();
        saveAuthUsername(username);
        window.location.href = '/';
        return;
      }

      if (response.status === 409) {
        errorEl.textContent = 'Логин уже занят';
      } else {
        errorEl.textContent = 'Не удалось зарегистрироваться';
      }
      errorEl.hidden = false;
    } catch (error) {
      console.error('Ошибка регистрации:', error);
      errorEl.textContent = 'Не удалось зарегистрироваться';
      errorEl.hidden = false;
    } finally {
      submitBtn.disabled = false;
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initAuthTabs();
  initLogin();
  initRegister();
});
