const LOGIN_API_PATH = '/api/login';
const REGISTER_API_PATH = '/api/register';

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
    loginError.hidden = true;
    registerError.hidden = true;
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
  }

  loginTab.addEventListener('click', showLogin);
  registerTab.addEventListener('click', showRegister);
}

/**
 * Отправляет учётные данные на /api/login и обрабатывает ответ.
 */
function initLogin() {
  const formEl = document.getElementById('loginForm');
  const errorEl = document.getElementById('loginError');
  const submitBtn = formEl?.querySelector('.login-form__submit');

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
      const response = await apiFetch(LOGIN_API_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        saveAuthUsername(username);
        window.location.href = '/';
        return;
      }

      if (response.status === 401) {
        errorEl.hidden = false;
      }
    } catch (error) {
      console.error('Ошибка входа:', error);
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
  const submitBtn = formEl?.querySelector('.login-form__submit');

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
