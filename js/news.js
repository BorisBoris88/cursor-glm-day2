function initNewsFeed() {
  const feed = document.getElementById('newsFeed');
  const list = document.getElementById('newsList');
  const status = document.getElementById('newsStatus');
  if (!feed || !list || !status) return;

  /**
   * Запрашивает топ статей Hacker News.
   * @returns {Promise<Array<{id: number, title: string, url: string}>>}
   */
  async function fetchNews() {
    const response = await apiFetch('/api/news');
    if (!response.ok) {
      throw new Error('Ошибка загрузки /api/news');
    }
    const data = await response.json();
    return data.articles;
  }

  /**
   * Рисует карточки новостей: заголовок и внешняя ссылка.
   * @param {Array<{id: number, title: string, url: string}>} articles
   */
  function renderNewsCards(articles) {
    list.replaceChildren();
    feed.classList.remove('news-feed--loading', 'news-feed--error');

    if (!Array.isArray(articles) || articles.length === 0) {
      feed.classList.add('news-feed--error');
      status.textContent = 'Лента пуста';
      return;
    }

    articles.forEach((article, index) => {
      if (!article || typeof article.title !== 'string' || typeof article.url !== 'string') {
        return;
      }

      const card = document.createElement('article');
      card.className = 'news-card';
      card.style.setProperty('--news-card-delay', `${index * 90}ms`);

      const title = document.createElement('h3');
      title.className = 'news-card__title';
      title.textContent = article.title;

      const link = document.createElement('a');
      link.className = 'news-card__link';
      link.href = article.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'Читать на Hacker News →';

      card.append(title, link);
      list.appendChild(card);
    });
  }

  async function loadNews() {
    try {
      const articles = await fetchNews();
      renderNewsCards(articles);
    } catch (error) {
      feed.classList.remove('news-feed--loading');
      feed.classList.add('news-feed--error');
      status.textContent = 'Новости недоступны';
      console.error(error);
    }
  }

  loadNews();
}

initNewsFeed();
