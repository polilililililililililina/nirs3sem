from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class ClinicCreate(BaseModel):
    name: str
    address: Optional[str] = None
    description: Optional[str] = None


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None


class ClinicResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = {
        "populate_by_name": True
    }


class AdminUserResponse(BaseModel):
    _id: str
    email: str
    name: Optional[str] = None
    surname: Optional[str] = None
    middlename: Optional[str] = None
    role: UserRole
    clinic_id: Optional[str] = None
    clinic_name: Optional[str] = None
    created_at: datetime


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    pagination: Pagination


class RoleUpdate(BaseModel):
    role: UserRole
