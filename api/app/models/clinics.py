from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Clinic(BaseModel):
    id: str = Field(alias="_id")

    name: str
    address: Optional[str] = None
    description: Optional[str] = None

    created_at: datetime

    model_config = {
        "populate_by_name": True
    }