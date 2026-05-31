import os
import uuid

import numpy as np

from app.ai.services.gradcam import generate_gradcam_overlay
from app.ai.services.model import model
from app.ai.services.postprocess import save_mask
from app.ai.services.preprocess import preprocess_image


OUTPUT_DIR = "storage/output"
HEATMAP_DIR = "storage/heatmaps"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HEATMAP_DIR, exist_ok=True)


def predict_scan(input_path: str):
    image = preprocess_image(input_path)

    prediction = model.predict(image, verbose=0)

    output_filename = f"{uuid.uuid4()}.png"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    save_mask(prediction, output_path)

    confidence = float(np.max(prediction))
    tumor_detected = confidence > 0.5

    heatmap_id = uuid.uuid4()
    overlay_path = os.path.join(HEATMAP_DIR, f"{heatmap_id}_overlay.png")
    raw_path = os.path.join(HEATMAP_DIR, f"{heatmap_id}_raw.png")

    heatmap_paths = {"heatmap_path": None, "heatmap_raw_path": None}

    try:
        heatmap_paths = generate_gradcam_overlay(
            model,
            image,
            input_path,
            overlay_path,
            raw_path,
        )
    except Exception:
        pass

    return {
        "result_path": output_path,
        "confidence": round(confidence, 4),
        "tumor_detected": tumor_detected,
        **heatmap_paths,
    }
