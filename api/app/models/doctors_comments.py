from pydantic import BaseModel, Field
from datetime import datetime


class DoctorsComments(BaseModel):
    id: str = Field(alias="_id")
    scan_id: str
    author_id: str
    author_name: str
    message: str
    created_at: datetime

    model_config = {
        "populate_by_name": True
    }