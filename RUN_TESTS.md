# Запуск тестов и проверок качества

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Тесты

### Все тесты с покрытием

```bash
pytest -v --cov=src --cov-report=term-missing --cov-report=html
```

Отчёт о покрытии: `htmlcov/index.html`

### Только unit-тесты

```bash
pytest tests/unit/ -v
```

### Только integration-тесты

```bash
pytest tests/integration/ -v
```

### E2E тесты

```bash
pytest tests/e2e/ -v
```

## Линтинг

### Ruff (быстрая проверка)

```bash
ruff check src/ tests/
```

### Black (форматирование)

```bash
# Проверить без изменений
black --check src/ tests/

# Применить форматирование
black src/ tests/
```

### Mypy (типизация, строгая проверка)

```bash
mypy src/
```

## Makefile (упрощённые команды)

### Все тесты

```bash
make test
```

### Линт (ruff + mypy)

```bash
make lint
```

### Форматирование (black + ruff --fix)

```bash
make format
```

### Запуск локально

```bash
# API
make run

# Worker (отдельный терминал)
make run-worker
```

### Docker Compose

```bash
# Запустить всё (API + Worker + Redis)
make docker-up

# Остановить
make docker-down

# Логи
make docker-logs
```

## CI/CD (GitLab)

Pipeline в `.gitlab-ci.yml`:

1. **lint_and_test**: ruff, black, mypy, pytest (с Redis service)
2. **docker_build**: сборка и push образа
3. **deploy_staging**: деплой в staging (опционально)
4. **deploy_production**: деплой в prod (manual, только для тегов)

## Результаты (ожидаемые)

- **Покрытие**: ≥80% (core logic)
- **Линт**: 0 ошибок (ruff, black)
- **Типизация**: mypy --strict, 0 ошибок
- **Тесты**: все зелёные (unit + integration + e2e)

