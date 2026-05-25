import os
import numpy as np

from PIL import Image


IMG_WIDTH = 256
IMG_HEIGHT = 256


def load_images(
    folder,
    grayscale=False
):
    images = []

    for filename in sorted(os.listdir(folder)):
        path = os.path.join(folder, filename)

        mode = "L" if grayscale else "RGB"

        image = (
            Image.open(path)
            .convert(mode)
            .resize((IMG_WIDTH, IMG_HEIGHT))
        )

        image = np.array(
            image,
            dtype=np.float32
        ) / 255.0

        images.append(image)

    return np.array(images)