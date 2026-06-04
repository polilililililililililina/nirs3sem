from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class ScanStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    error = "error"


class Scan(BaseModel):
    id: str = Field(alias="_id", description="UUID анализа")
    filename: str = Field(description="Имя загруженного файла")
    file_path: str = Field(description="Путь к исходному изображению на сервере")
    status: ScanStatus = Field(description="Статус обработки: queued, processing, done, error")
    user_id: Optional[str] = Field(default=None, description="ID владельца (null для гостя)")
    is_guest: bool = Field(description="Гостевая загрузка без авторизации")
    result: Optional[str] = Field(default=None, description="Путь к маске сегментации")
    result_desc: Optional[str] = Field(default=None, description="Текстовое описание результата")
    source_type: Optional[str] = Field(
        default="image",
        description="image, dicom или dicom_zip",
    )
    n_slices: Optional[int] = Field(
        default=None,
        description="Число срезов (для dicom_zip)",
    )
    representative_slice_idx: Optional[int] = Field(
        default=None,
        description="Индекс среза с макс. площадью поражения",
    )
    heatmap_path: Optional[str] = Field(default=None, description="Grad-CAM overlay")
    heatmap_raw_path: Optional[str] = Field(default=None, description="Grad-CAM heatmap")
    doctor_verified: Optional[bool] = Field(default=None, description="Верификация врачом")
    created_at: datetime = Field(description="Дата создания")
    updated_at: Optional[datetime] = Field(default=None, description="Дата обновления")
    confidence: Optional[float] = Field(default=None, description="Уверенность модели (0–1)")
    tumor_detected: Optional[bool] = Field(default=None, description="Обнаружена ли аномалия")

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


class CommentCreate(BaseModel):
    message: str = Field(description="Текст комментария врача", examples=["Рекомендую повторное исследование"])


class ConclusionCreate(BaseModel):
    text: str = Field(description="Текст экспертного заключения", examples=["Признаки объёмного образования..."])


class VerifyScanBody(BaseModel):
    verified: bool = Field(description="true — подтвердить результат ИИ, false — не согласен")
