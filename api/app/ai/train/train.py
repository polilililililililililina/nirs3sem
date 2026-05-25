import tensorflow as tf
import numpy as np
import random
import os

from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
    ModelCheckpoint,
)

from app.ai.train.model import unet_model
from app.ai.train.dataset import load_images

from app.ai.services.metrics import (
    dice_coef,
    iou_metric,
    bce_dice_loss,
)


SEED = 42

os.environ["PYTHONHASHSEED"] = str(SEED)

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

X_train = load_images("data/X_train")
y_train = load_images(
    "data/y_train",
    grayscale=True
)

X_val = load_images("data/X_val")
y_val = load_images(
    "data/y_val",
    grayscale=True
)

y_train = y_train[..., np.newaxis]
y_val = y_val[..., np.newaxis]

y_train = (
    y_train > 0.5
).astype(np.float32)

y_val = (
    y_val > 0.5
).astype(np.float32)

model = unet_model()

model.compile(
    optimizer=Adam(learning_rate=1e-4),
    loss=bce_dice_loss,
    metrics=[
        "accuracy",
        dice_coef,
        iou_metric,
    ],
)

callbacks = [
    EarlyStopping(
        monitor="val_loss",
        patience=8,
        restore_best_weights=True,
    ),

    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=4,
        min_lr=1e-7,
    ),

    ModelCheckpoint(
        "app/ai/models/unet_brain_mri_final.keras",
        monitor="val_loss",
        save_best_only=True,
    ),
]

model.fit(
    X_train,
    y_train,
    validation_data=(X_val, y_val),
    epochs=50,
    batch_size=16,
    callbacks=callbacks,
)

print("Model saved")