from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class ScanStatus(str, Enum):
    processing = "processing"
    done = "done"
    error = "error"
    queued = "queued"


class Scan(BaseModel):
    id: str = Field(alias="_id")
    filename: str
    file_path: str
    status: ScanStatus
    owner_id: Optional[str] = None
    patient_name: Optional[str] = None
    is_guest: bool
    ai_conclusion_path: Optional[str] = None
    ai_desc: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    confidence: Optional[float] = None
    tumor_detected: Optional[bool] = None
    clinic_id: Optional[str] = None
    doctor_comment: Optional[str] = None
    expert_conclusion: Optional[str] = None

    model_config = {
        "populate_by_name": True
    }


class Pagination(BaseModel):
    page: int
    limit: int
    total: int

class ScanListResponse(BaseModel):
    items: list[Scan]
    pagination: Pagination