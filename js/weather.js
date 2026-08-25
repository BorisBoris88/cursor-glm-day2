const WEATHER_ICONS = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌦️', 53: '🌦️', 55: '🌧️',
  61: '🌧️', 63: '🌧️', 65: '🌧️',
  71: '🌨️', 73: '🌨️', 75: '❄️',
  80: '🌦️', 81: '🌧️', 82: '⛈️',
  95: '⛈️', 96: '⛈️', 99: '⛈️',
};

function initWeatherWidget() {
  const widget = document.getElementById('weatherWidget');
  const tempEl = document.getElementById('weatherTemp');
  const iconEl = document.getElementById('weatherIcon');
  if (!widget || !tempEl || !iconEl) return;

  widget.dataset.tooltip = 'Данные обновляются в реальном времени';
  widget.tabIndex = 0;

  async function loadWeather() {
    try {
      const response = await apiFetch('/api/weather');
      if (!response.ok) throw new Error('Ошибка загрузки /api/weather');

      const data = await response.json();
      const temp = Math.round(data.temperature);
      const code = data.weather_code;

      tempEl.textContent = `${temp}°C`;
      iconEl.textContent = WEATHER_ICONS[code] || '🌡️';
      widget.classList.remove('weather-widget--loading', 'weather-widget--error');
    } catch (error) {
      tempEl.textContent = 'нет данных';
      iconEl.textContent = '⚠️';
      widget.classList.remove('weather-widget--loading');
      widget.classList.add('weather-widget--error');
      console.error(error);
    }
  }

  loadWeather();
}

initWeatherWidget();
