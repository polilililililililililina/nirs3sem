from pydantic import BaseModel, Field
from datetime import datetime


class StudyReport(BaseModel):
    id: str = Field(alias="_id")
    scan_id: str
    doctor_id: str
    doctor_name: str
    text: str
    created_at: datetime

    model_config = {
        "populate_by_name": True
    }