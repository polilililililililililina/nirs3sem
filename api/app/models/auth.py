from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if len(value) < 8:
            raise ValueError(
                "Пароль должен содержать минимум 8 символов"
            )

        if not re.search(r"[A-Za-z]", value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну букву"
            )

        if not re.search(r"\d", value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну цифру"
            )

        return value


class LoginSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):

        if len(value.strip()) == 0:
            raise ValueError("Пароль не может быть пустым")

        return value


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str):

        if len(value) < 8:
            raise ValueError(
                "Пароль должен содержать минимум 8 символов"
            )

        if not re.search(r"[A-Za-z]", value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну букву"
            )

        if not re.search(r"\d", value):
            raise ValueError(
                "Пароль должен содержать хотя бы одну цифру"
            )

        return value