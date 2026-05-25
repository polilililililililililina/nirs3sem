from PIL import Image
import numpy as np


IMG_WIDTH = 256
IMG_HEIGHT = 256


def preprocess_image(path: str):
    image = (
        Image.open(path)
        .convert("RGB")
        .resize((IMG_WIDTH, IMG_HEIGHT))
    )

    image = np.array(image, dtype=np.float32) / 255.0

    image = np.expand_dims(image, axis=0)

    return image