from tensorflow.keras.models import load_model

from app.ai.services.metrics import (
    dice_coef,
    dice_loss,
    bce_dice_loss,
    iou_metric
)

MODEL_PATH = "app/ai/models/unet_brain_mri_final.keras"

model = load_model(
    MODEL_PATH,
    custom_objects={
        "dice_coef": dice_coef,
        "dice_loss": dice_loss,
        "bce_dice_loss": bce_dice_loss,
        "iou_metric": iou_metric,
    }
)