import os
import uuid

import numpy as np

from app.ai.services.dicom_loader import load_dicom_volume, predict_volume, volume_stats
from app.ai.services.gradcam import generate_gradcam_overlay
from app.ai.services.model import get_inference_model
from app.ai.services.postprocess import save_mask
from app.ai.services.preprocess import preprocess_image


OUTPUT_DIR = "storage/output"
HEATMAP_DIR = "storage/heatmaps"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HEATMAP_DIR, exist_ok=True)


def _normalize_prediction(raw_prediction) -> np.ndarray:
    prediction = raw_prediction
    if isinstance(prediction, list):
        prediction = prediction[0]
    return np.asarray(prediction)


def _metrics_from_prediction(prediction: np.ndarray) -> tuple[float, bool]:
    """Как в исходной системе: confidence = max вероятности маски."""
    confidence = float(np.max(prediction))
    tumor_detected = confidence > 0.5
    return round(confidence, 4), tumor_detected


def _save_heatmap_pair(keras_model, image_batch, input_path: str) -> dict:
    heatmap_id = uuid.uuid4()
    overlay_path = os.path.join(HEATMAP_DIR, f"{heatmap_id}_overlay.png")
    raw_path = os.path.join(HEATMAP_DIR, f"{heatmap_id}_raw.png")
    try:
        return generate_gradcam_overlay(
            keras_model,
            image_batch,
            input_path,
            overlay_path,
            raw_path,
        )
    except Exception:
        return {"heatmap_path": None, "heatmap_raw_path": None}


def predict_scan(input_path: str) -> dict:
    image = preprocess_image(input_path)
    keras_model = get_inference_model()

    raw = keras_model.predict(image, verbose=0)
    prediction = _normalize_prediction(raw)

    output_filename = f"{uuid.uuid4()}.png"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    save_mask(prediction, output_path)

    confidence, tumor_detected = _metrics_from_prediction(prediction)
    heatmap_paths = _save_heatmap_pair(keras_model, image, input_path)

    return {
        "result_path": output_path,
        "confidence": confidence,
        "tumor_detected": tumor_detected,
        **heatmap_paths,
    }


def predict_scan_volume(dicom_folder: str, preview_png_path: str) -> dict:
    volume, _paths = load_dicom_volume(dicom_folder)
    keras_model = get_inference_model()

    masks = predict_volume(keras_model, volume, batch_size=8)
    stats = volume_stats(masks)
    idx = stats["max_slice_idx"]

    from app.ai.services.dicom_loader import save_rgb_array_as_png

    os.makedirs(os.path.dirname(preview_png_path) or ".", exist_ok=True)
    save_rgb_array_as_png(volume[idx], preview_png_path)

    slice_batch = np.expand_dims(volume[idx], axis=0)
    raw = keras_model.predict(slice_batch, verbose=0)
    prediction = _normalize_prediction(raw)

    output_filename = f"{uuid.uuid4()}.png"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    save_mask(prediction, output_path)

    confidence, tumor_detected = _metrics_from_prediction(prediction)
    heatmap_paths = _save_heatmap_pair(keras_model, slice_batch, preview_png_path)

    return {
        "result_path": output_path,
        "confidence": confidence,
        "tumor_detected": tumor_detected,
        "volume_stats": stats,
        "n_slices": stats["n_slices"],
        "representative_slice_idx": idx,
        "preview_path": preview_png_path,
        **heatmap_paths,
    }
