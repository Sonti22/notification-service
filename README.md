# Notification Service

**Production-ready notification delivery service with fallback (Email → SMS → Telegram).**

## Features

- **Multi-channel delivery**: Email, SMS, Telegram with automatic fallback.
- **Retry with exponential backoff**: Max 3 attempts, Redis-backed queue.
- **REST API**: FastAPI (async), JSON, structured logs.
- **Observability**: Correlation IDs, health checks, ready for Prometheus.
- **Type-safe**: Full type hints, mypy --strict.
- **Tested**: Unit, integration, e2e (pytest, ≥80% coverage).

## Quick Start

### Local (Docker Compose)

```bash
# Clone and enter
git clone <repo-url> notification-service
cd notification-service

# Start all services (API + Redis + Worker)
docker-compose up --build

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Send a notification

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "message": "Hello from notification service!",
    "channels": ["email", "sms", "telegram"]
  }'

# Response:
# {
#   "id": "uuid",
#   "status": "pending",
#   "created_at": "2025-10-27T12:00:00Z"
# }
```

### Check status

```bash
curl http://localhost:8000/api/v1/notifications/{id}

# Response:
# {
#   "id": "uuid",
#   "status": "sent",
#   "channel_used": "email",
#   "attempts": [...]
# }
```

## Development

### Prerequisites

- Python 3.11+
- Redis (or Docker)
- (Optional) PostgreSQL

### Setup

```bash
# Create venv
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Run Redis (if not Docker)
redis-server

# Migrate DB (SQLite by default)
python -m src.database

# Run API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run worker (separate terminal)
python -m src.services.retry
```

### Testing

```bash
# All tests + coverage
make test

# Lint + type check
make lint

# Format
make format
```

## Configuration

Environment variables (see `.env.example`):

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Database (SQLite default, set for Postgres)
DATABASE_URL=sqlite+aiosqlite:///./notifications.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/notifications

# Redis
REDIS_URL=redis://localhost:6379/0

# Retry
MAX_RETRY_ATTEMPTS=3
RETRY_BACKOFF_BASE=2  # seconds

# Providers (real credentials or leave empty for mocks)
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

## Architecture

```
┌─────────┐      POST /notifications      ┌──────────────┐
│ Client  │─────────────────────────────>│   FastAPI    │
└─────────┘                               │   (API)      │
                                          └───────┬──────┘
                                                  │
                     ┌────────────────────────────┼────────────────┐
                     │                            │                │
                     ▼                            ▼                ▼
              ┌─────────────┐            ┌──────────────┐  ┌──────────┐
              │  SQLite/PG  │            │    Redis     │  │  Retry   │
              │  (delivery  │            │  (queue)     │  │  Worker  │
              │   log)      │            └──────────────┘  └─────┬────┘
              └─────────────┘                                     │
                                                                  │
                     ┌────────────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  NotificationService │
          │  (Fallback logic)    │
          └───────────┬──────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼              ▼
   ┌────────┐   ┌────────┐    ┌──────────┐
   │ Email  │   │  SMS   │    │ Telegram │
   │Provider│   │Provider│    │ Provider │
   └────────┘   └────────┘    └──────────┘
```

### Fallback Strategy

1. Try **Email** (SMTP).
2. If failed → try **SMS** (Twilio).
3. If failed → try **Telegram** (Bot API).
4. If all failed → mark as `failed`, enqueue for retry.
5. Retry with exponential backoff (2^attempt seconds).

### Key Components

- **FastAPI app** (`src/main.py`): REST endpoints, middleware (correlation_id, logging).
- **NotificationService** (`src/services/notification.py`): orchestrates fallback, logs attempts.
- **Providers** (`src/services/providers/`): Email/SMS/Telegram implementations (mock by default, real via env).
- **Retry Worker** (`src/services/retry.py`): consumes Redis Stream, retries failed deliveries.
- **Database** (`src/database.py`, `src/models/orm.py`): SQLAlchemy async, stores delivery history.

## Testing

- **Unit** (`tests/unit/`): Mocked providers, service logic.
- **Integration** (`tests/integration/`): Real API calls, in-memory DB.
- **E2E** (`tests/e2e/`): Full stack with Redis + SQLite.

```bash
pytest -v --cov=src --cov-report=html
```

Coverage report: `htmlcov/index.html`

## CI/CD

`.gitlab-ci.yml` stages:

1. **lint_and_test**: ruff, black, mypy, pytest.
2. **docker_build**: Build & push image.
3. **deploy** (optional): K8s/Nomad deployment.

## Deployment

### Docker

```bash
docker build -t notification-service:latest .
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite+aiosqlite:///./notifications.db \
  -e REDIS_URL=redis://redis:6379/0 \
  notification-service:latest
```

### Kubernetes (example)

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

## Roadmap

- [ ] Prometheus metrics (`/metrics`).
- [ ] Rate limiting (per user/IP).
- [ ] Template support (Jinja2 for Email/SMS).
- [ ] Webhooks (callback on delivery status).
- [ ] Admin UI (view/retry/cancel notifications).

## License

MIT (see [LICENSE](LICENSE))

