# 📦 Сайт для обработки заказов (Module 9, Case 3)

**MVP** — единый веб-стек для приёма и обработки заявок от «тёплых» клиентов.

## 📋 Оглавление

- [Архитектура](#архитектура)
- [Стек технологий](#стек-технологий)
- [Сервисы](#сервисы)
- [Быстрый старт](#быстрый-старт)
- [Детальная настройка](#детальная-настройка)
- [Цикл автодеплоя](#цикл-автодеплоя)
- [Безопасность](#безопасность)
- [Структура проекта](#структура-проекта)
- [Переменные окружения](#переменные-окружения)
- [Устранение неполадок](#устранение-неполадок)
- [Требования](#требования)

---

## 🏗 Архитектура

```
                    Интернет
                         │
                    ┌────▼────┐
                    │  Traefik│ (хостовый reverse-proxy, порт 80/443)
                    └────┬────┘
                         │
                    ┌────▼────┐
              ┌─────│  Nginx  │← Единственная точка входа в приложение
              │     │  :8088  │   (статика + прокси /api/ → backend)
              │     └────┬────┘
              │          │
              │     ┌────▼────────┐
              │     │  Frontend   │← index.html (форма заявки)
              │     │  (HTML/CSS/ │
              │     │   JS)       │
              │     └────┬────────┘
              │          │ proxy /api/ → backend:8000
              │     ┌────▼────────┐
              │     │  Backend    │← FastAPI (health + POST /leads)
              │     │  :8000      │
              │     └────┬────────┘
              │          │
              │     ┌────▼────────┐
              │     │ PostgreSQL  │← База данных (таблица leads)
              │     │  :5432      │
              │     └─────────────┘
              │
              │ internal network (backend_net)
              │ ┌──────────────┐  ┌──────────────┐
              │ │  Registry    │  │  Watchtower  │
              │ │  :5000       │  │  :8080       │
              │ └──────────────┘  └──────────────┘
              │
              └── external network (external_net)
                  ┌──────────────┐
                  │   pgAdmin    │← Веб-панель БД :5050
                  └──────────────┘
```

**Ключевой принцип — «докеризованный монолит»:** всё работает на одном виртуальном сервере, изолировано в Docker-сетях, внешняя точка входа — только Nginx.

---

## 🛠 Стек технологий

| Компонент     | Технология                          |
|---------------|-------------------------------------|
| Frontend      | HTML + CSS + vanilla JavaScript     |
| Backend       | Python 3.12 + FastAPI + SQLAlchemy  |
| База данных   | PostgreSQL 16 (Alpine)              |
| Админка БД    | pgAdmin 4                           |
| Reverse-proxy | Nginx 1.27 (Alpine)                 |
| Registry      | Docker Registry v2                  |
| Автодеплой    | Watchtower                          |
| Оркестрация   | Docker Compose v2                   |

---

## 📦 Сервисы

| Сервис         | Порт снаружи | Назначение                                       |
|----------------|---------------|--------------------------------------------------|
| **Nginx**      | 8088          | Статика фронта + прокси `/api/*` на backend       |
| **PostgreSQL** | — (внутренн.) | Хранение заявок                                 |
| **Backend**    | — (внутренн.) | FastAPI API (`/health`, `/leads`)                |
| **pgAdmin**    | 5050          | Веб-панель для просмотра БД                      |
| **Registry**   | 5000          | Локальный Docker Registry (для push образов)     |
| **Watchtower** | — (внутренн.) | Автоматическое обновление backend из Registry    |

---

## 🚀 Быстрый старт

### 1. Подготовка

```bash
cd ~/projects/module_9_case_3_site_for_orders
```

### 2. Запуск

```bash
bash setup.sh
```

Скрипт выполнит:
- Проверку Docker и docker compose
- Добавление текущего пользователя в группу `docker` (требуется перелогин)
- Генерацию `htpasswd` для Registry
- Сборку и запуск всех сервисов (`docker compose up -d --build`)

### 3. Проверка

| Сервис    | URL                                         |
|-----------|---------------------------------------------|
| Фронтенд  | `http://<IP-сервера>:8088`                   |
| pgAdmin   | `http://<IP-сервера>:5050`                   |
| Registry  | `http://<IP-сервера>:5000/v2/_catalog`       |

---

## 🔧 Детальная настройка

### Переменные окружения (.env)

Файл `.env` содержит все креды. Не коммитите в публичный репозиторий.

```bash
> ⚠️ Реальные значения паролей хранятся в файле `.env` на сервере
> и **не публикуются**. Ниже — шаблон; сгенерируйте свои пароли командой:
> `openssl rand -hex 16`

```bash
# --- Nginx ---
NGINX_PORT=8088          # Порт Nginx снаружи (по умолчанию 8088)

# --- PostgreSQL ---
POSTGRES_USER=orders_user
POSTGRES_PASSWORD=<СГЕНЕРИРУЙТЕ: openssl rand -hex 16>
POSTGRES_DB=orders_db

# --- pgAdmin ---
PGADMIN_EMAIL=admin@orders.com
PGADMIN_PASSWORD=<СГЕНЕРИРУЙТЕ: openssl rand -hex 12>

# --- Docker Registry ---
REGISTRY_USER=registry
REGISTRY_PASSWORD=<СГЕНЕРИРУЙТЕ: openssl rand -hex 12>
REGISTRY_PORT=5000
REGISTRY_HOST=<IP-или-домен-сервера>:5000   # Хост для тегирования образов

# --- Watchtower ---
WATCHTOWER_INTERVAL=300      # Интервал проверки (сек)
WATCHTOWER_CLEANUP=true
```
```

> **Примечание:** Если на сервере освободить порт 80, измените `NGINX_PORT=80`.

### Подключение к pgAdmin

1. Откройте `http://<IP>:5050`
2. Логин: `admin@orders.com`, пароль: значение `PGADMIN_PASSWORD` из `.env`
3. **Register → Server:**
   - Host: `postgres`
   - Port: `5432`
   - Maintenance db: `orders_db`
   - Username: `orders_user`
   - Password: значение `POSTGRES_PASSWORD` из `.env`

### Доступ к Registry

**Проверка каталога (curl):**
```bash
curl.exe -u registry:<REGISTRY_PASSWORD из .env> \
  http://<IP-сервера>:5000/v2/_catalog
# → {"repositories":[]}
```

**Проверка в браузере:**
```
http://<IP-сервера>:5000/v2/          # → 200 OK (пустая страница)
http://<IP-сервера>:5000/v2/_catalog  # → 401 (нужен Basic Auth)
```
> Браузеры не показывают окно Basic Auth на HTTP — используйте curl.

---

## 🔄 Цикл автодеплоя

### 1. Настройка Docker Desktop (локальная машина)

**Docker Engine → Settings → daemon.json:**
```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "insecure-registries": ["<IP-сервера>:5000"]
}
```
→ Apply & Restart

### 2. Login

```bash
docker login <IP-сервера>:5000
# Username: registry
# Password: значение REGISTRY_PASSWORD из .env
```

### 3. Build → Push

```bash
# Собираем backend
cd ~/projects/module_9_case_3_site_for_orders
docker compose up -d --build backend

# Тегирование (образ уже имеет имя registry)
# В docker-compose.yml backend: image: ${REGISTRY_HOST}/orders-backend:latest
# docker compose up сам тегует образ как <IP-сервера>:5000/orders-backend:latest

# Push на сервер
docker push <IP-сервера>:5000/orders-backend:latest
```

### 4. Автообновление

Watchtower проверяет Registry каждые `WATCHTOWER_INTERVAL` секунд (по умолчанию 300).
При обнаружении нового образа `orders-backend:latest` он:
1. Скачивает новый образ из Registry
2. Пересоздаёт контейнер `orders_backend`
3. Nginx автоматически начинает проксировать на новый IP

---

## 🛡 Безопасность

### Сетевые隔离

```
backend_net (internal: true)
├── postgres:5432          ← только от backend
├── backend:8000           ← только от nginx
├── registry:5000          ← только от watchtower
├── pgadmin:80             ← порт 5050 наружу
└── watchtower:8080        ← только к docker.sock

external_net
├── registry:5000          ← порт 5000 наружу (docker push)
├── pgadmin:80             ← порт 5050 наружу

frontend
├── nginx:80               ← порт 8088 наружу
```

### Политики

1. **Postgres и backend не имеют публикуемых портов** — доступ только через Docker DNS внутри `backend_net`
2. **Nginx — единственная точка входа** — весь трафик `frontend → backend` идёт через него
3. **Watchtower не видит сеть наружу** — только docker.sock и registry по внутренней сети
4. **pgAdmin и Registry** — открыты по требованию администратора, не являются частью внешнего API

### Данные

- Все данные клиентов хранятся внутри контура
- База данных — только через Backend
- Нет утечек наружу через контейнеры

---

## 📁 Структура проекта

```
module_9_case_3_site_for_orders/
├── docker-compose.yml      # Описание всех сервисов
├── .env                    # Переменные окружения (скрыть!)
├── setup.sh                # Первичная настройка
├── technical_requirements.md
│
├── nginx/
│   ├── Dockerfile          # Образ nginx:1.27-alpine
│   ├── nginx.conf          # Статика + proxy /api/ → backend:8000
│   └── html/
│       └── index.html      # Форма заявки + JS-агрегация метрик
│
├── backend/
│   ├── Dockerfile          # python:3.12-slim + uvicorn
│   ├── requirements.txt    # fastapi, sqlalchemy, psycopg3, pydantic
│   └── app/
│       ├── __init__.py
│       └── main.py         # /health + POST /api/leads
│
├── registry/
│   ├── auth/               # htpasswd (создаёт setup.sh)
│   └── data/               # Volume для образов Registry
│
└── scripts/                # Вспомогательные скрипты (по необходимости)
```

---

## ❓ Устранение неполадок

### 1. `permission denied while trying to connect to the docker API`

```bash
sudo usermod -aG docker dev
# Переподключитесь к SSH/VS Code
```

### 2. Backend возвращает 502/504 после обновления образа

Это нормальное поведение без Docker DNS resolver. В текущей конфигурации nginx настроен на `resolver 127.0.0.11` — IP backend'а переопределяется каждые 10 секунд.

### 3. Watchtower падает с `client version 1.25 is too old`

Добавьте в `docker-compose.yml` для watchtower:
```yaml
environment:
  DOCKER_API_VERSION: "1.40"
```

### 4. pgAdmin не запускается (`admin@orders.local` error)

`.local` домен зарезервирован RFC 2606. Используйте `.com` или `.ru` в `PGADMIN_EMAIL`.

### 5. `docker push` не проходит (timeout)

Добавьте insecure-registry в Docker Desktop:
```json
"insecure-registries": ["<IP-сервера>:5000"]
```

### 6. Nginx не резолвит имя backend

Убедитесь, что оба сервиса в одной Docker-сети и nginx использует `resolver 127.0.0.11`.

---

## 📋 Требования

- Docker 29.0+
- Docker Compose v2
- 2 vCPU, 2 GB RAM минимум
- Порт 8088 свободен на хосте
- Порт 5000 свободен на хосте
- Порт 5050 свободен на хосте
- SSH-доступ к серверу

---

## 📝 API Reference

### `GET /health` (через nginx: `/api/health`)

Проверка живости backend.

**Response:**
```json
{"status": "ok"}
```

### `POST /api/leads`

Создание заявки.

**Body:**
```json
{
  "contact": "+79001234567",
  "business": "Интернет-магазин",
  "budget": "100-300k",
  "channel": "telegram",
  "comment": "Нужен редизайн до 1 ноября",
  "metrics": {
    "referrer": "https://google.com",
    "utm": { "source": "cpc", "medium": "yandex" },
    "landing": "https://site.com/landing",
    "submitted_at": "2026-10-20T10:00:00Z"
  },
  "tech": {
    "user_agent": "Mozilla/5.0...",
    "language": "ru",
    "screen": { "w": 1920, "h": 1080 },
    "timezone": "Europe/Moscow"
  }
}
```

**Response (200):**
```json
{"ok": true, "message": "Lead saved"}
```

**Response (500):**
```json
{"detail": "DB error: ..."}
```

---

## 📊 База данных

**Таблица `leads`:**

| Колонка    | Тип        | Описание                    |
|------------|------------|-----------------------------|
| id         | SERIAL     | Автоинкремент               |
| contact    | TEXT       | Телефон / email             |
| business   | TEXT       | Информация о бизнесе        |
| budget     | TEXT       | Бюджет                      |
| channel    | TEXT       | Канал связи                 |
| comment    | TEXT       | Комментарий                 |
| metrics    | JSONB      | UTM, реферер, тайминг       |
| tech       | JSONB      | UA, экран, язык, TZ         |
| created_at | TIMESTAMPTZ| Дата создания               |

**SQL для просмотра:**
```sql
SELECT id, contact, budget, channel, created_at
FROM leads ORDER BY created_at DESC;
```

---

## 🆘 Контакты

- Документация Koda: https://docs.kodacode.ru
- Сообщество Telegram: https://t.me/kodacommunity
