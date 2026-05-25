import os
import uuid
import numpy as np

from app.ai.services.model import model
from app.ai.services.preprocess import preprocess_image
from app.ai.services.postprocess import save_mask


OUTPUT_DIR = "storage/output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def predict_scan(input_path: str):
    image = preprocess_image(input_path)

    prediction = model.predict(image)

    output_filename = f"{uuid.uuid4()}.png"

    output_path = os.path.join(
        OUTPUT_DIR,
        output_filename
    )

    save_mask(prediction, output_path)

    confidence = float(np.max(prediction))

    tumor_detected = confidence > 0.5

    return {
        "result_path": output_path,
        "confidence": round(confidence, 4),
        "tumor_detected": tumor_detected,
    }