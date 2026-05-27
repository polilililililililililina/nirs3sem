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
    user_id: Optional[str] = None
    is_guest: bool
    result: Optional[str] = None
    result_desc: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    confidence: Optional[float] = None
    tumor_detected: Optional[bool] = None

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