import logging
import os

from tensorflow.keras.models import load_model

from app.ai.services.metrics import CUSTOM_OBJECTS

logger = logging.getLogger(__name__)

_AI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(_AI_ROOT, "models", "unet_brain_mri_final.keras")

_inference_model = None


def get_inference_model():
    """Загружает исходную U-Net при первом обращении."""
    global _inference_model

    if _inference_model is not None:
        return _inference_model

    if not os.path.isfile(MODEL_PATH):
        msg = (
            f"Файл модели не найден: {MODEL_PATH}. "
            "Поместите unet_brain_mri_final.keras в api/app/ai/models/"
        )
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info("Загрузка U-Net: %s", MODEL_PATH)
    _inference_model = load_model(MODEL_PATH, custom_objects=CUSTOM_OBJECTS)
    return _inference_model


class _LazyModelProxy:
    def __getattr__(self, name):
        return getattr(get_inference_model(), name)


model = _LazyModelProxy()
