# MRI Analyzer

Веб-сервис для AI-анализа МРТ-изображений: FastAPI backend + Next.js frontend + MongoDB.

## Структура

```
api/        — Python backend (FastAPI)
frontend/   — Next.js frontend
```

## Запуск

### Backend

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Настроить api/.env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# Настроить frontend/.env
npm run dev
```

### MongoDB

Убедитесь, что MongoDB запущена и переменные `MONGO_URL`, `DB_NAME` заданы в `api/.env`.

## Переменные окружения

### api/.env

```
MONGO_URL=mongodb://localhost:27017
DB_NAME=mri_analyzer
SECRET_KEY=your-secret-key
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USER=
SMTP_PASSWORD=
FRONTEND_URL=http://localhost:3000
INPUT_DIR=storage/input
OUTPUT_DIR=storage/output
AVATAR_DIR=storage/avatars
```

### frontend/.env

```
API_HOST=http://localhost:8000
SOCKET=ws://localhost:8000
```

## Создание администратора

1. Зарегистрируйте пользователя через UI или API (`POST /auth/register`).
2. В MongoDB назначьте роль `admin`:

```javascript
db.users.updateOne(
  { email: "admin@example.com" },
  { $set: { role: "admin" } }
)
```

Доступные роли: `user`, `doctor`, `admin`.

## API документация

После запуска backend: [http://localhost:8000/docs](http://localhost:8000/docs)

## Маршруты frontend

| Путь | Описание |
|------|----------|
| `/` | Главная — загрузка и анализ МРТ |
| `/login` | Вход / регистрация |
| `/profile` | Профиль пользователя |
| `/history` | История анализов |
| `/knowledge` | База знаний |
| `/compare` | Сравнение анализов |
| `/admin` | Панель администратора |
