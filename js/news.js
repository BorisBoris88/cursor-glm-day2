/**
 * Разрешает только http/https со схемой и хостом — не javascript:/data:.
 * @param {string} url
 * @returns {boolean}
 */
function isSafeHttpUrl(url) {
  try {
    const parsed = new URL(url);
    return (
      (parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
      Boolean(parsed.hostname)
    );
  } catch (error) {
    return false;
  }
}

/**
 * Разрешает только http/https со схемой и хостом — не javascript:/data:.
 * @param {string} url
 * @returns {boolean}
 */
function isSafeHttpUrl(url) {
  try {
    const parsed = new URL(url);
    return (
      (parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
      Boolean(parsed.hostname)
    );
  } catch (error) {
    return false;
  }
}

const NEWS_CACHE_STORAGE_KEY = 'news_articles_cache';
const NEWS_CACHE_TTL_MS = 30_000;

/**
 * Читает ленту из sessionStorage, если она младше TTL.
 * @returns {Array<{id: number, title: string, url: string}> | null}
 */
function readStoredNews() {
  try {
    const raw = sessionStorage.getItem(NEWS_CACHE_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (
      !parsed ||
      !Array.isArray(parsed.articles) ||
      typeof parsed.timestamp !== 'number'
    ) {
      return null;
    }
    if (Date.now() - parsed.timestamp >= NEWS_CACHE_TTL_MS) {
      return null;
    }
    return parsed.articles;
  } catch (error) {
    console.error(error);
    return null;
  }
}

/**
 * Сохраняет ленту в sessionStorage.
 * @param {Array<{id: number, title: string, url: string}>} articles
 */
function writeStoredNews(articles) {
  try {
    sessionStorage.setItem(
      NEWS_CACHE_STORAGE_KEY,
      JSON.stringify({ articles, timestamp: Date.now() })
    );
  } catch (error) {
    console.error(error);
  }
}

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
    const cached = readStoredNews();
    if (cached) {
      return cached;
    }

    const response = await apiFetch('/api/news');
    if (!response.ok) {
      throw new Error('Ошибка загрузки /api/news');
    }
    const data = await response.json();
    const articles = data.articles;
    if (Array.isArray(articles)) {
      writeStoredNews(articles);
    }
    return articles;
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

      card.append(title);
      if (isSafeHttpUrl(article.url)) {
        const link = document.createElement('a');
        link.className = 'news-card__link';
        link.href = article.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = 'Читать на Hacker News →';
        card.append(link);
      }

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
