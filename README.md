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
- [Backend: архитектура приложения](#backend-архитектура-приложения)
- [API Reference](#api-reference)
- [База данных](#база-данных)
- [Фронтенд](#фронтенд)
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
               │     │  Backend    │← FastAPI (health + POST /leads + admin CRUD)
               │     │  :8000      │   (core, models, schemas, routes)
               │     └────┬────────┘
               │          │
               │     ┌────▼────────┐
               │     │ PostgreSQL  │← База данных (leads, lead_behavior, services)
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
| **PostgreSQL** | — (внутренн.) | Хранение заявок, поведения и услуг              |
| **Backend**    | — (внутренн.) | FastAPI API (health, services, leads, admin CRUD)|
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

## 🎨 Фронтенд

Страница заявки в элитном стиле (белая тема, шрифт Inter, анимации):

- **Hero-секция** — представление бизнеса (градиент, бейдж, заголовок)
- **Секции формы** — разделены линиями, анимация появления
- **Динамическая подгрузка услуг** — `GET /api/services` → select с продуктами
- **Ползунок бюджета** — один ползунок, шаг 1000 ₽, диапазон подстраивается под выбранную услугу
- **Сбор метрик поведения** — время на странице, клики, зависания курсора, возвраты, глубина скролла, UTM, тех-информация
- **Единый пакет** — `{lead: {...}, behavior: {...}}` → `POST /api/leads`

### Swagger UI

Доступен через nginx: `http://<IP-сервера>:8088/api/docs`

Для работы Swagger UI добавлена директива `root_path="/api"` в FastAPI — все пути в OpenAPI spec будут содержать `/api/...`, что позволяет корректно генерировать запросы через nginx-прокси.

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
│       ├── main.py         # Точка входа, api_router, lifespan
│       ├── core/
│       │   ├── __init__.py
│       │   └── db.py       # Движок SQLAlchemy, SessionLocal, Base, get_db
│       ├── models/
│       │   ├── __init__.py
│       │   ├── service.py  # Service + CRUD (услуги, диапазоны цен)
│       │   └── lead.py     # Lead + LeadBehavior (1:1) + CRUD
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── service.py  # ServiceCreate/Update/Out
│       │   └── lead.py     # LeadPackage/LeadOut/BehaviorOut
│       └── routes/
│           ├── __init__.py
│           ├── public.py   # GET /health, GET /services
│           ├── leads.py    # POST/GET/DELETE /leads
│           └── admin.py    # CRUD /admin/services
│
├── registry/
│   ├── auth/               # htpasswd (создаёт setup.sh)
│   └── data/               # Volume для образов Registry
│
└── scripts/                # Вспомогательные скрипты (по необходимости)
```

## 🏛 Backend: архитектура приложения

Backend реализован по классической слоистой архитектуре FastAPI:

```
main.py (точка входа)
  └── api_router (объединяет роуты)
        ├── public.py   ← GET /health, GET /services
        ├── leads.py    ← POST/GET/DELETE /leads
        └── admin.py    ← CRUD /admin/services
              ↑
         Схемы (schemas/)
              ↑
         Модели (models/) — SQLAlchemy + CRUD-функции
              ↑
         Ядро (core/) — движок БД, get_db
```

**Ядро (`core/db.py`)**
- Подключение к PostgreSQL через `DATABASE_URL` (из docker-compose)
- Движок `create_engine`, `SessionLocal`, базовый класс `Base`
- Зависимость `get_db()` для FastAPI

**Модели (`models/`)**
- `service.py` — таблица `services` (услуги + диапазоны цен), CRUD-функции `create_service`, `list_services`, `update_service`, `delete_service`
- `lead.py` — таблица `leads` (заявки) + `lead_behavior` (поведение 1:1), CRUD-функции `create_lead_with_behavior`, `list_leads`, `delete_lead`
- Каждая модель содержит SQL-код для создания таблицы в докстринге

**Схемы (`schemas/`)**
- Pydantic-схемы для валидации входящих данных и форматирования ответов
- `LeadPackage` — единый пакет `{lead: {...}, behavior: {...}}`

**Роуты (`routes/`)**
- `public.py` — публичные эндпоинты для фронтенда
- `leads.py` — приём заявок единым пакетом, чтение, удаление
- `admin.py` — CRUD услуг (для администратора через Swagger)

**Миграция** — при старте `main.py` переименовывает старую MVP-таблицу `leads` в `leads_legacy_v1` и создаёт новые таблицы через `Base.metadata.create_all()`.

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

Все эндпоинты доступны через nginx по префиксу `/api/`.

### `GET /api/health`

Проверка живости backend.

**Response (200):**
```json
{"status": "ok"}
```

### `GET /api/services`

Список активных услуг — фронтенд строит интерфейс по этому списку.

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Полировка",
    "description": "Полировка кузова",
    "price_min": 5000,
    "price_max": 15000,
    "is_active": true,
    "created_at": "2026-10-20T12:59:59Z"
  }
]
```

### `POST /api/leads`

Создание заявки единым пакетом: данные формы + поведение пользователя.

**Body:**
```json
{
  "lead": {
    "contact": "+79001234567",
    "first_name": "Иван",
    "last_name": "Петров",
    "middle_name": "Иванович",
    "niche": "Автосервис",
    "company_size": "small",
    "role": "employee",
    "budget": "5000–15000 ₽",
    "product_interest": "Полировка",
    "deadline": "до конца квартала",
    "contact_channel": "telegram",
    "contact_time": "будни 10–18",
    "comment": "Тест"
  },
  "behavior": {
    "time_on_page_seconds": 120,
    "clicks_count": 42,
    "cursor_idle_seconds": 15,
    "cursor_hover_stalls": 8,
    "returns_count": 2,
    "scroll_depth_percent": 85,
    "user_agent": "Mozilla/5.0...",
    "referrer": "https://google.com",
    "utm_source": "yandex",
    "utm_medium": "cpc",
    "screen_width": 1920,
    "screen_height": 1080,
    "timezone": "Europe/Moscow"
  }
}
```

**Response (201):**
```json
{
  "id": 1,
  "contact": "+79001234567",
  "first_name": "Иван",
  "last_name": "Петров",
  "niche": "Автосервис",
  "budget": "5000–15000 ₽",
  "behavior": {
    "lead_id": 1,
    "time_on_page_seconds": 120,
    "clicks_count": 42,
    "returns_count": 2,
    "scroll_depth_percent": 85
  },
  "created_at": "2026-10-20T12:59:59Z"
}
```

### `GET /api/leads`

Список заявок (новые первыми).

**Query parameters:** `skip=0`, `limit=100`

### `GET /api/leads/{lead_id}`

Заявка по ID, включая поведение.

### `DELETE /api/leads/{lead_id}`

Удаление заявки (поведение удаляется по CASCADE).

### `POST /api/admin/services`

Создание услуги (через Swagger UI).

**Body:**
```json
{
  "name": "Керамика",
  "description": "Керамическое покрытие",
  "price_min": 20000,
  "price_max": 60000
}
```

### `GET /api/admin/services`

Список всех услуг (включая отключённые, если `include_inactive=true`).

### `PATCH /api/admin/services/{service_id}`

Частичное обновление услуги.

### `DELETE /api/admin/services/{service_id}`

Удаление услуги.

---

## 📊 База данных

**Таблица `leads` — заявки клиентов:**

| Колонка         | Тип         | Описание                |
|-----------------|-------------|-------------------------|
| id              | SERIAL      | Первичный ключ          |
| first_name      | TEXT        | Имя                     |
| last_name       | TEXT        | Фамилия                 |
| middle_name     | TEXT        | Отчество                |
| contact         | TEXT        | Телефон / email         |
| business_info   | TEXT        | Информация о бизнесе    |
| niche           | TEXT        | Ниша бизнеса            |
| company_size    | TEXT        | Размер компании         |
| role            | TEXT        | Сотрудник / Руководитель|
| task_type       | TEXT        | Тип задачи              |
| product_interest| TEXT        | Интересующий продукт    |
| budget          | TEXT        | Бюджет (строка)         |
| deadline        | TEXT        | Срок результата         |
| contact_channel | TEXT        | Способ связи            |
| contact_time    | TEXT        | Удобное время связи     |
| comment         | TEXT        | Комментарий             |
| created_at      | TIMESTAMPTZ | Дата создания           |

**Таблица `lead_behavior` — поведение пользователя (1:1 с Lead):**

| Колонка               | Тип         | Описание                  |
|-----------------------|-------------|---------------------------|
| lead_id               | INTEGER PK  | FK на leads.id (CASCADE)  |
| time_on_page_seconds  | INTEGER     | Время на странице (сек)   |
| clicks_count          | INTEGER     | Количество кликов         |
| cursor_idle_seconds   | INTEGER     | Время бездействия курсора |
| cursor_hover_stalls   | INTEGER     | Зависания курсора         |
| returns_count         | INTEGER     | Возвраты на страницу      |
| scroll_depth_percent  | INTEGER     | Глубина скролла (%)       |
| user_agent            | TEXT        | Браузер                   |
| referrer              | TEXT        | Источник                  |
| utm_source            | TEXT        | UTM source                |
| utm_medium            | TEXT        | UTM medium                |
| utm_campaign          | TEXT        | UTM campaign              |
| screen_width          | INTEGER     | Ширина экрана             |
| screen_height         | INTEGER     | Высота экрана             |
| timezone              | TEXT        | Часовой пояс              |
| recorded_at           | TIMESTAMPTZ | Запись                    |

**Таблица `services` — услуги (админ-данные):**

| Колонка     | Тип         | Описание              |
|-------------|-------------|-----------------------|
| id          | SERIAL      | Первичный ключ        |
| name        | TEXT UNIQUE | Название услуги       |
| description | TEXT        | Описание              |
| price_min   | INTEGER     | Минимальная цена      |
| price_max   | INTEGER     | Максимальная цена     |
| is_active   | BOOLEAN     | Активна/неактивна     |
| created_at  | TIMESTAMPTZ | Дата создания         |

**SQL для просмотра:**
```sql
-- Заявки с поведением
SELECT l.id, l.first_name, l.last_name, l.niche, l.budget,
       b.time_on_page_seconds, b.clicks_count, b.returns_count
FROM leads l
LEFT JOIN lead_behavior b ON l.id = b.lead_id
ORDER BY l.created_at DESC;

-- Услуги
SELECT id, name, price_min, price_max, is_active
FROM services ORDER BY id;
```

---

## 🆘 Контакты

- Документация Koda: https://docs.kodacode.ru
- Сообщество Telegram: https://t.me/kodacommunity
