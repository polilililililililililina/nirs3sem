import os

import numpy as np
import pydicom
from PIL import Image


def _normalize_pixel_array(pixel_array: np.ndarray) -> np.ndarray:
    pixel_array = pixel_array.astype(np.float32)

    if pixel_array.max() > pixel_array.min():
        pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min())

    return (pixel_array * 255).astype(np.uint8)


def dicom_to_png(dicom_path: str, output_path: str) -> str:
    dataset = pydicom.dcmread(dicom_path)

    if not hasattr(dataset, "pixel_array"):
        raise ValueError("DICOM файл не содержит изображение")

    pixel_array = dataset.pixel_array

    if getattr(dataset, "PhotometricInterpretation", "") == "MONOCHROME1":
        pixel_array = np.max(pixel_array) - pixel_array

    if hasattr(dataset, "RescaleSlope") and hasattr(dataset, "RescaleIntercept"):
        pixel_array = pixel_array * float(dataset.RescaleSlope) + float(dataset.RescaleIntercept)

    if pixel_array.ndim == 3:
        image = Image.fromarray(pixel_array.astype(np.uint8)).convert("RGB")
    else:
        normalized = _normalize_pixel_array(pixel_array)
        image = Image.fromarray(normalized).convert("RGB")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path, format="PNG")

    return output_path


def is_dicom_file(filename: str) -> bool:
    return filename.lower().endswith(".dcm")
