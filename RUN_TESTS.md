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

## Ожидаемые результаты

- **Покрытие**: ≥80% (core logic)
- **Линт**: 0 ошибок (ruff, black)
- **Типизация**: mypy --strict, 0 ошибок
- **Тесты**: все зелёные (unit + integration + e2e)

## Примеры вывода

### Успешные тесты

```
================================ test session starts =================================
platform win32 -- Python 3.11.0, pytest-7.4.3, pluggy-1.3.0
collected 15 items

tests/unit/test_providers.py ...                                               [ 20%]
tests/unit/test_notification_service.py ....                                   [ 46%]
tests/unit/test_retry.py ..                                                    [ 60%]
tests/integration/test_api.py .....                                            [ 93%]
tests/e2e/test_full_flow.py .                                                  [100%]

---------- coverage: platform win32, python 3.11.0 -----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/__init__.py                             1      0   100%
src/config.py                              42      2    95%   67-68
src/database.py                            35      3    91%   ...
src/services/notification.py             128      8    94%   ...
---------------------------------------------------------------------
TOTAL                                     645     45    93%

================================ 15 passed in 2.34s ==================================
```

### Успешный линтинг

```
$ ruff check src/ tests/
All checks passed!

$ black --check src/ tests/
All done! ✨ 🍰 ✨
44 files would be left unchanged.

$ mypy src/
Success: no issues found in 18 source files
```

## Отладка тестов

### Запустить один тест с verbose

```bash
pytest tests/unit/test_notification_service.py::test_create_and_send_notification_success -vv
```

### Показать print-вывод

```bash
pytest tests/unit/ -s
```

### Остановиться на первой ошибке

```bash
pytest --maxfail=1
```

### Запустить только failed тесты (после предыдущего прогона)

```bash
pytest --lf
```

## Troubleshooting

### Redis недоступен

Если тесты падают с ошибкой подключения к Redis:

```bash
# Запустить Redis локально
redis-server

# Или через Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Import errors

Убедитесь, что PYTHONPATH включает корень проекта:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

Или установите проект в editable режиме:

```bash
pip install -e .
```
