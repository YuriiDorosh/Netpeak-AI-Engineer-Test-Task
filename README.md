# Netpeak-AI-Engineer-Test-Task# AI Request Classifier

Сервіс для автоматичної класифікації та структурування внутрішніх запитів до AI-команди.  
Приймає CSV-файл із запитами у вільній формі, обробляє кожен через локальну LLM і повертає `output.json` + `report.md`.

**Стек:** Python 3.12 · FastAPI · llama.cpp (Qwen2.5-3B-Instruct Q4_K_M) · Docker Compose · nginx

---

## Швидкий старт

### 1. Завантажити модель (≈ 2 GB, одноразово)

```bash
make download-model
```

Модель збережеться у `./models/` і ніколи не потрапить у git (`.gitignore`).

### 2. Збудувати та запустити

```bash
make build
make up
```

Після старту відкрий у браузері:

| | URL |
|---|---|
| UI | http://localhost/ |
| Swagger | http://localhost/docs |

> **Перший запуск займає ~30–60 секунд** — llama.cpp завантажує модель у RAM.  
> FastAPI не стартує до тих пір, поки `llm` не пройде healthcheck (`depends_on: condition: service_healthy`).

### 3. Обробити файл

**Через UI:** перейди на http://localhost/, завантаж CSV, натисни «Обробити».

**Через Makefile:**
```bash
make process FILE=input_requests.csv
```

**Через curl:**
```bash
# Завантажити файл
JOB_ID=$(curl -s -X POST http://localhost/api/upload \
  -F "file=@input_requests.csv" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

# Моніторити статус
curl http://localhost/api/jobs/$JOB_ID

# Скачати результати
curl -O http://localhost/api/jobs/$JOB_ID/output.json
curl -O http://localhost/api/jobs/$JOB_ID/report.md
```

---

## Змінні середовища

Скопіюй `.env.example` → `.env` і за потреби змін:

| Змінна | За замовчуванням | Опис |
|---|---|---|
| `LLAMA_CPP_URL` | `http://llm:8080` | URL llama.cpp сервера (внутрішній) |
| `MODEL_FILENAME` | `qwen2.5-3b-instruct-q4_k_m.gguf` | Назва GGUF-файлу у `./models/` |
| `LLM_THREADS` | `4` | Кількість CPU-потоків для llama.cpp |
| `PORT` | `80` | Зовнішній порт nginx |

---

## Команди Makefile

```
make download-model   завантажити Qwen2.5-3B GGUF (~2 GB)
make build            збудувати Docker-образи
make up               запустити всі сервіси (detached)
make down             зупинити контейнери
make logs             слідкувати за логами
make ps               статус сервісів
make process FILE=…   завантажити CSV і отримати job_id
make clean            видалити зупинені контейнери
```

---

## Архітектура

```
Browser / curl
      │
   nginx:80
   ├── / → static HTML (index.html)
   ├── /docs → FastAPI Swagger
   └── /api/ → FastAPI:8000
                   │
                   ├── POST /api/upload      → створює job, запускає фонову задачу
                   ├── GET  /api/jobs/{id}   → статус + результат
                   ├── GET  /api/jobs/{id}/output.json
                   └── GET  /api/jobs/{id}/report.md
                                │
                          llm:8080 (llama.cpp server, OpenAI-compatible API)
                                │
                         ./models/*.gguf (volume mount)
```

**Async flow:**  
`POST /upload` повертає `job_id` негайно (HTTP 202). Обробка йде у `BackgroundTask`.  
Кожен рядок CSV класифікується послідовно (Semaphore(1) — CPU inference однопотоковий).  
Клієнт поллінгує `GET /jobs/{id}` кожні 1.5 с; UI показує прогрес у реальному часі.

**Structured output:**  
Запити до llama.cpp надсилаються з `response_format.type = json_schema` + Pydantic JSON Schema.  
Це змушує модель генерувати граматично валідний JSON на рівні токенів.  
Якщо сервер повертає 422 (старіша збірка без json_schema), автоматично переключається на `json_object` режим.  
Pydantic — фінальний рубіж валідації. До 2 спроб на рядок; при невдачі рядок позначається як `error`.

---

## Схема виводу

```json
{
  "id": "REQ-001",
  "channel": "Slack",
  "timestamp": "2026-06-08 09:14",
  "raw_text": "...",
  "analysis": {
    "category": "автоматизація",
    "target_department": "маркетинг",
    "priority": "medium",
    "short_summary": "Автоматизувати щотижневий звіт по Google Ads.",
    "requested_actions": ["Вивантажувати CSV з Google Ads", "Копіювати метрики в таблицю автоматично"],
    "needs_clarification": false,
    "confidence_score": 0.92
  }
}
```

Поле `confidence_score` додано понад мінімум завдання: модель самостійно оцінює впевненість у класифікації.  
Це дозволяє downstream-сервісам (наприклад, Telegram-дайджест) окремо помічати граничні випадки без повторного запуску пайплайну.

---

## Dev-режим (без Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pre-commit && pre-commit install

# Запустити llama.cpp окремо (або через docker compose up llm)
export LLAMA_CPP_URL=http://localhost:8080

uvicorn src.main:app --reload
```
