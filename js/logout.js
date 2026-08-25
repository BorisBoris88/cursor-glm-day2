/**
 * Выход: POST /api/logout, сброс куки, переход на login.html.
 */
function initLogout() {
  const logoutBtn = document.getElementById('logoutBtn');
  if (!logoutBtn) {
    return;
  }

  logoutBtn.addEventListener('click', async () => {
    logoutBtn.disabled = true;

    try {
      const response = await apiFetch('/api/logout', { method: 'POST' });
      if (response.ok) {
        clearAuthUsername();
        window.location.href = 'login.html';
        return;
      }
      console.error('Ошибка выхода: HTTP', response.status);
    } catch (error) {
      console.error('Ошибка выхода:', error);
    } finally {
      logoutBtn.disabled = false;
    }
  });
}

document.addEventListener('DOMContentLoaded', initLogout);
