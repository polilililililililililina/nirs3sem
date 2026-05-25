from PIL import Image
import numpy as np


THRESHOLD = 0.5


def save_mask(prediction, output_path: str):
    mask = (
        prediction[0, ..., 0] > THRESHOLD
    ).astype(np.uint8) * 255

    image = Image.fromarray(mask)

    image.save(output_path)