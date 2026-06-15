# Платформа психологических курсов (Django)

Веб-приложение для прохождения курсов и кабинета психолога. Поддерживается запуск как **Telegram Mini App** (Web App).

## Быстрый старт (разработка)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # при необходимости отредактируйте
python manage.py migrate
python manage.py runserver
```

Откройте http://127.0.0.1:8000/

## Telegram Mini App

### Требования Telegram

1. **HTTPS** — Mini App открывается только по защищённому URL.
2. **Токен бота** — для проверки подписи `initData` (без токена приложение работает, но пользователь Telegram не привязывается автоматически).
3. В [@BotFather](https://t.me/BotFather):
   - `/newbot` или выберите существующего бота;
   - **Bot Settings → Menu Button → Configure menu button** — укажите URL: `https://ваш-домен/` (тот же, что `TELEGRAM_MINI_APP_URL`);
   - либо **/setmenubutton** и URL Web App.

### Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

| Переменная | Назначение |
|------------|------------|
| `TELEGRAM_BOT_TOKEN` | Токен от BotFather |
| `TELEGRAM_BOT_USERNAME` | Имя бота без `@` (для документации) |
| `TELEGRAM_MINI_APP_URL` | Публичный HTTPS-URL приложения |
| `DJANGO_ALLOWED_HOSTS` | Домен(ы) сервера |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://ваш-домен` |

### Что сделано в проекте

- Подключён [Telegram Web App SDK](https://core.telegram.org/bots/webapps);
- Страницы для учеников (`/`, курсы, уроки) открываются во iframe Telegram (`frame-ancestors`, снятие `X-Frame-Options`);
- Проверка `initData` на сервере, привязка ответов к `telegram_user_id`;
- Адаптация под тему Telegram, кнопка «Назад», safe-area;
- Кабинет психолога (`/psych/`) и админка **не** предназначены для Mini App (остаются обычным веб-входом).

### Деплой в Docker

```bash
cp .env.example .env
# отредактируйте .env (DEBUG=false, домен, токен бота)

docker compose up --build -d
```

Приложение слушает порт **8000**. Перед продакшеном поставьте reverse-proxy (nginx, Caddy, Traefik) с TLS и проксируйте на `web:8000`. Пример заголовка для Django:

```
X-Forwarded-Proto: https
```

Медиафайлы (`media/`) смонтированы в volume `media_data`; для продакшена их также можно отдавать через nginx.

### Деплой на Railway

1. В сервисе добавьте **Volume** с mount path `/app/media` — иначе загруженные фото пропадут после перезапуска контейнера.
2. Переменные окружения: `DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` (PostgreSQL).
3. Медиа отдаются самим Django (`DJANGO_SERVE_MEDIA=true` по умолчанию). Для больших нагрузок позже можно подключить S3/R2.

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `DJANGO_MEDIA_ROOT` | `/app/media` | Папка загрузок (должна совпадать с volume) |
| `DJANGO_SERVE_MEDIA` | `true` | Раздавать `/media/` в production |

### Локальная проверка Mini App

Полноценный тест возможен только по HTTPS. Варианты:

- туннель [ngrok](https://ngrok.com/) / [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/);
- деплой на VPS с сертификатом Let's Encrypt.

Укажите полученный HTTPS-URL в BotFather и в `TELEGRAM_MINI_APP_URL`.

## Структура URL

| Путь | Описание |
|------|----------|
| `/` | Список психологов (точка входа Mini App) |
| `/course/<id>/` | Курс |
| `/lesson/<id>/` | Урок (тесты, игры) |
| `/psych/` | Кабинет психолога (вне Mini App) |
| `/api/telegram/init/` | POST — сохранение сессии после проверки initData |

## Сбор статики

```bash
python manage.py collectstatic --noinput
```

В Docker `collectstatic` выполняется при старте контейнера.
