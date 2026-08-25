function initAliasesWidget() {
  const main = document.querySelector('main');
  const hackBtn = document.getElementById('hackBtn');
  if (!main || !hackBtn) return;

  const listContainer = document.createElement('div');
  listContainer.id = 'aliases-list';
  main.appendChild(listContainer);

  async function fetchHackerAliases() {
    const response = await apiFetch('/api/hackers');
    if (!response.ok) {
      throw new Error('Ошибка загрузки /api/hackers');
    }
    const data = await response.json();
    return data.aliases;
  }

  function showAliasesList(aliases) {
    if (!Array.isArray(aliases)) return;

    listContainer.replaceChildren();
    const card = document.createElement('div');
    card.className = 'aliases-card';

    const title = document.createElement('div');
    title.className = 'aliases-card__title';
    title.textContent = 'Новые алиасы хакеров:';

    const list = document.createElement('ul');
    list.className = 'aliases-card__list';
    for (const alias of aliases) {
      const item = document.createElement('li');
      item.className = 'aliases-card__item';
      item.textContent = String(alias);
      list.appendChild(item);
    }

    card.append(title, list);
    listContainer.appendChild(card);
    listContainer.style.opacity = '0';
    listContainer.style.pointerEvents = 'none';
    void listContainer.offsetWidth;
    listContainer.style.opacity = '1';
    listContainer.style.pointerEvents = 'auto';
  }

  hackBtn.addEventListener('click', async function () {
    const btn = this;
    btn.disabled = true;
    btn.textContent = 'Взлом...';
    btn.classList.remove('hacked');
    listContainer.style.opacity = '0';

    try {
      const aliases = await fetchHackerAliases();
      showAliasesList(aliases);
      btn.textContent = 'Доступ получен';
      btn.classList.add('hacked');
    } catch (error) {
      btn.textContent = 'Ошибка доступа';
      btn.disabled = false;
      console.error(error);
    }
  });
}

initAliasesWidget();
