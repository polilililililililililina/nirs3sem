from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, date
from typing import Optional
import re
from enum import Enum


class UserRole(str, Enum):
    user = "user"
    doctor = "doctor"
    admin = "admin"


# Полная модель пользователя (БД)
class User(BaseModel):
    _id: str
    email: EmailStr
    password: str
    name: str
    role: UserRole = UserRole.user
    surname: Optional[str] = None
    middlename: Optional[str] = None
    birthday: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    avatar_url: Optional[str] = None
    clinic_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Что отдаём клиенту
class UserResponse(BaseModel):
    _id: str
    email: EmailStr
    name: str
    role: UserRole = UserRole.user
    surname: Optional[str] = None
    middlename: Optional[str] = None
    birthday: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    clinic_id: Optional[str] = None
    clinic_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Что можно редактировать
class UpdateUserSchema(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    middlename: Optional[str] = None
    birthday: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    clinic_id: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):

        if value is None:
            return value

        cleaned = re.sub(r"\D", "", value)

        if len(cleaned) < 10:
            raise ValueError(
                "Некорректный номер телефона"
            )

        return value