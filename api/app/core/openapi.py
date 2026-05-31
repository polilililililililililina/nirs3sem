from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


OPENAPI_TAGS = [
    {
        "name": "Auth",
        "description": "Регистрация, аутентификация и восстановление пароля.",
    },
    {
        "name": "Users",
        "description": "Профиль текущего пользователя и аватар.",
    },
    {
        "name": "Scans",
        "description": "Загрузка МРТ, анализ, история, комментарии врачей и WebSocket-статусы.",
    },
    {
        "name": "Knowledge",
        "description": "База знаний: статьи, автоподбор и импорт.",
    },
    {
        "name": "Clinics",
        "description": "Публичный список клиник для профиля пользователя.",
    },
    {
        "name": "Admin",
        "description": "Администрирование пользователей и клиник.",
    },
]


def configure_openapi(app: FastAPI) -> None:
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )

        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Access token, полученный через POST /auth/login или POST /auth/refresh.",
            }
        }

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
