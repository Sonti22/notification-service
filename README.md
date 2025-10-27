# Сервис Уведомлений

**Production-ready сервис доставки уведомлений с каскадной отправкой (Email → SMS → Telegram).**

## Возможности

- **Мультиканальная доставка**: Email, SMS, Telegram с автоматическим переключением при сбое.
- **Повторные попытки с экспоненциальной задержкой**: Максимум 3 попытки, очередь в Redis.
- **REST API**: FastAPI (async), JSON, структурированные логи.
- **Наблюдаемость**: Correlation ID, health checks, готовность к Prometheus.
- **Типобезопасность**: Полные type hints, mypy --strict.
- **Протестировано**: Unit, integration, e2e тесты (pytest, покрытие ≥80%).

## Быстрый старт

### Локально (Docker Compose)

```bash
# Клонировать и войти
git clone https://github.com/Sonti22/notification-service.git
cd notification-service

# Запустить все сервисы (API + Redis + Worker)
docker-compose up --build

# API доступен на http://localhost:8000
# Документация на http://localhost:8000/docs
```

### Отправить уведомление

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "message": "Привет от сервиса уведомлений!",
    "channels": ["email", "sms", "telegram"]
  }'

# Ответ:
# {
#   "id": "uuid",
#   "status": "pending",
#   "created_at": "2025-10-27T12:00:00Z"
# }
```

### Проверить статус

```bash
curl http://localhost:8000/api/v1/notifications/{id}

# Ответ:
# {
#   "id": "uuid",
#   "status": "sent",
#   "channel_used": "email",
#   "attempts": [...]
# }
```

## Разработка

### Требования

- Python 3.11+
- Redis (или Docker)
- (Опционально) PostgreSQL

### Настройка

```bash
# Создать виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить Redis (если не Docker)
redis-server

# Инициализировать БД (SQLite по умолчанию)
python -m src.database

# Запустить API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Запустить worker (отдельный терминал)
python -m src.services.retry
```

### Тестирование

```bash
# Все тесты + покрытие
make test

# Линтинг + проверка типов
make lint

# Форматирование
make format
```

## Конфигурация

Переменные окружения (см. `env.example`):

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# База данных (SQLite по умолчанию, для Postgres укажите свой URL)
DATABASE_URL=sqlite+aiosqlite:///./notifications.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/notifications

# Redis
REDIS_URL=redis://localhost:6379/0

# Повторные попытки
MAX_RETRY_ATTEMPTS=3
RETRY_BACKOFF_BASE=2  # секунды

# Провайдеры (реальные credentials или оставьте пустыми для моков)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

TELEGRAM_BOT_TOKEN=
```

## Архитектура

```
┌─────────┐      POST /notifications      ┌──────────────┐
│ Клиент  │─────────────────────────────>│   FastAPI    │
└─────────┘                               │   (API)      │
                                          └───────┬──────┘
                                                  │
                     ┌────────────────────────────┼────────────────┐
                     │                            │                │
                     ▼                            ▼                ▼
              ┌─────────────┐            ┌──────────────┐  ┌──────────┐
              │  SQLite/PG  │            │    Redis     │  │  Retry   │
              │  (лог       │            │  (очередь)   │  │  Worker  │
              │ доставки)   │            └──────────────┘  └─────┬────┘
              └─────────────┘                                     │
                                                                  │
                     ┌────────────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  NotificationService │
          │  (Логика fallback)   │
          └───────────┬──────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼              ▼
   ┌────────┐   ┌────────┐    ┌──────────┐
   │ Email  │   │  SMS   │    │ Telegram │
   │Provider│   │Provider│    │ Provider │
   └────────┘   └────────┘    └──────────┘
```

### Стратегия каскадной отправки (Fallback)

1. Попытка **Email** (SMTP).
2. Если не удалось → попытка **SMS** (Twilio).
3. Если не удалось → попытка **Telegram** (Bot API).
4. Если все не удались → статус `failed`, добавление в очередь повторов.
5. Повтор с экспоненциальной задержкой (2^попытка секунд).

### Ключевые компоненты

- **FastAPI приложение** (`src/main.py`): REST endpoints, middleware (correlation_id, логирование).
- **NotificationService** (`src/services/notification.py`): управляет fallback, логирует попытки.
- **Провайдеры** (`src/services/providers/`): реализации Email/SMS/Telegram (моки по умолчанию, реальные через env).
- **Retry Worker** (`src/services/retry.py`): обрабатывает Redis Stream, повторяет неудачные доставки.
- **База данных** (`src/database.py`, `src/models/orm.py`): SQLAlchemy async, хранит историю доставок.

## Тестирование

- **Unit** (`tests/unit/`): Замоканные провайдеры, логика сервисов.
- **Integration** (`tests/integration/`): Реальные API-вызовы, in-memory БД.
- **E2E** (`tests/e2e/`): Полный стек с Redis + SQLite.

```bash
pytest -v --cov=src --cov-report=html
```

Отчёт о покрытии: `htmlcov/index.html`

## CI/CD

Этапы `.gitlab-ci.yml`:

1. **lint_and_test**: ruff, black, mypy, pytest.
2. **docker_build**: Сборка и push образа.
3. **deploy** (опционально): Развертывание в K8s/Nomad.

## Развертывание

### Docker

```bash
docker build -t notification-service:latest .
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite+aiosqlite:///./notifications.db \
  -e REDIS_URL=redis://redis:6379/0 \
  notification-service:latest
```

### Kubernetes (пример)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: notification-service:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-creds
              key: url
        - name: REDIS_URL
          value: redis://redis-service:6379/0
```

## Дорожная карта

- [ ] Метрики Prometheus (`/metrics`).
- [ ] Rate limiting (на пользователя/IP).
- [ ] Поддержка шаблонов (Jinja2 для Email/SMS).
- [ ] Webhooks (callback при изменении статуса).
- [ ] Admin UI (просмотр/повтор/отмена уведомлений).

## Лицензия

MIT (см. [LICENSE](LICENSE))

