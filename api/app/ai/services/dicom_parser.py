"""Обратная совместимость: используйте app.ai.services.dicom_loader."""

from app.ai.services.dicom_loader import dicom_to_png, is_dicom_file

__all__ = ["dicom_to_png", "is_dicom_file"]
