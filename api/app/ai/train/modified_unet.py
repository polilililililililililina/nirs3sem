"""
AA-UNet (ASPP-Attention U-Net) — модифицированная архитектура для сегментации МРТ.
"""

import os
import random

import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import Callback, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.metrics import BinaryAccuracy
from tensorflow.keras.layers import (
    Activation,
    Add,
    AvgPool2D,
    BatchNormalization,
    Conv2D,
    Conv2DTranspose,
    Dense,
    Dropout,
    GlobalAveragePooling2D,
    Input,
    MaxPooling2D,
    Multiply,
    Reshape,
    UpSampling2D,
    concatenate,
)
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from app.ai.custom_layers import ResizeToReference
from app.ai.services.metrics import bce_dice_loss, dice_coef, iou_metric

FINAL_MODEL_FILENAME = "aa_unet_brain_mri_final.keras"
BEST_CHECKPOINT_FILENAME = "aa_unet_best.keras"

_MAIN_METRICS = [
    BinaryAccuracy(threshold=0.5, name="accuracy"),
    dice_coef,
    iou_metric,
]


def _normalize_metric_threshold(value: float | None) -> float | None:
    """Принимает 0.92 или 92 (проценты) — возвращает долю 0–1."""
    if value is None:
        return None
    if value > 1.0:
        return value / 100.0
    return value


_METRIC_MONITOR = {
    "accuracy": "val_main_output_accuracy",
    "dice": "val_main_output_dice_coef",
    "iou": "val_main_output_iou_metric",
}


class StopWhenMetricReached(Callback):
    """Останавливает обучение, когда метрика на валидации достигла порога."""

    def __init__(self, monitor: str, target: float, metric_label: str):
        self.monitor = monitor
        self.target = target
        self.metric_label = metric_label

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        current = logs.get(self.monitor)
        if current is None:
            return
        if current >= self.target:
            self.model.stop_training = True
            print(
                f"\n✓ Остановка: {self.metric_label} на валидации "
                f"{current * 100:.2f}% ≥ цели {self.target * 100:.2f}%"
            )


class EpochMetricsPrinter(Callback):
    """Выводит точность, Dice и IoU в процентах после каждой эпохи."""

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        def pair(train_key: str, val_key: str) -> str:
            train_v = logs.get(train_key)
            val_v = logs.get(val_key)
            if train_v is None and val_v is None:
                return "—"
            chunks = []
            if train_v is not None:
                chunks.append(f"обуч. {train_v * 100:.2f}%")
            if val_v is not None:
                chunks.append(f"вал. {val_v * 100:.2f}%")
            return ", ".join(chunks)

        print(
            f"\n── Эпоха {epoch + 1} ── "
            f"Точность: {pair('main_output_accuracy', 'val_main_output_accuracy')} │ "
            f"Dice: {pair('main_output_dice_coef', 'val_main_output_dice_coef')} │ "
            f"IoU: {pair('main_output_iou_metric', 'val_main_output_iou_metric')}"
        )


def _training_metrics():
    return {
        "main_output": _MAIN_METRICS,
        "ds2_output": [
            BinaryAccuracy(threshold=0.5, name="accuracy"),
            dice_coef,
        ],
        "ds3_output": [
            BinaryAccuracy(threshold=0.5, name="accuracy"),
            dice_coef,
        ],
    }


def _bn_relu(x):
    return Activation("relu")(BatchNormalization()(x))


def _conv_bn_relu(x, filters, kernel=3, dilation=1):
    return _bn_relu(
        Conv2D(
            filters,
            kernel,
            padding="same",
            dilation_rate=dilation,
            kernel_initializer="he_normal",
        )(x)
    )


def _residual_block(x, filters, dropout=0.0):
    shortcut = Conv2D(filters, 1, padding="same", kernel_initializer="he_normal")(x)
    shortcut = BatchNormalization()(shortcut)

    x = _conv_bn_relu(x, filters)
    x = _conv_bn_relu(x, filters)
    if dropout > 0:
        x = Dropout(dropout)(x)

    return Activation("relu")(Add()([x, shortcut]))


def _squeeze_excitation(x, ratio=8):
    filters = x.shape[-1]
    se = GlobalAveragePooling2D()(x)
    se = Reshape((1, 1, filters))(se)
    se = Dense(
        max(1, filters // ratio),
        activation="relu",
        kernel_initializer="he_normal",
    )(se)
    se = Dense(filters, activation="sigmoid", kernel_initializer="he_normal")(se)
    return Multiply()([x, se])


def _aspp_block(x, filters):
    b1 = _conv_bn_relu(x, filters, kernel=1)

    b2 = _conv_bn_relu(x, filters, dilation=6)
    b3 = _conv_bn_relu(x, filters, dilation=12)
    b4 = _conv_bn_relu(x, filters, dilation=18)

    b5 = GlobalAveragePooling2D()(x)
    b5 = Reshape((1, 1, x.shape[-1]))(b5)
    b5 = _conv_bn_relu(b5, filters, kernel=1)
    b5 = ResizeToReference(name="resize_to_reference")([b5, x])

    out = concatenate([b1, b2, b3, b4, b5])
    out = _conv_bn_relu(out, filters, kernel=1)
    out = Dropout(0.2)(out)
    return out


def _attention_gate_se(g, s, filters):
    Wg = _bn_relu(
        Conv2D(filters, 1, padding="same", kernel_initializer="he_normal")(g)
    )
    Ws = _bn_relu(
        Conv2D(filters, 1, padding="same", kernel_initializer="he_normal")(s)
    )

    psi = Conv2D(
        1,
        1,
        padding="same",
        kernel_initializer="he_normal",
    )(Activation("relu")(Add()([Wg, Ws])))
    psi = Activation("sigmoid")(BatchNormalization()(psi))

    attended = Multiply()([s, psi])
    attended = _squeeze_excitation(attended)
    return attended


def build_aa_unet(
    img_h: int = 256,
    img_w: int = 256,
    img_c: int = 3,
    deep_supervision: bool = True,
    name: str = "AA_UNet",
):
    inp = Input((img_h, img_w, img_c), name="input_img")

    c1 = _residual_block(inp, 32)
    c1 = _squeeze_excitation(c1)
    p1 = MaxPooling2D(2)(c1)

    c2 = _residual_block(p1, 64)
    c2 = _squeeze_excitation(c2)
    p2 = MaxPooling2D(2)(c2)

    c3 = _residual_block(p2, 128)
    c3 = _squeeze_excitation(c3)
    p3 = MaxPooling2D(2)(c3)

    c4 = _residual_block(p3, 256)
    c4 = _squeeze_excitation(c4)
    p4 = MaxPooling2D(2)(c4)

    c5 = _aspp_block(p4, 512)

    u6 = Conv2DTranspose(256, 2, strides=2, padding="same")(c5)
    a6 = _attention_gate_se(g=u6, s=c4, filters=128)
    c6 = _residual_block(concatenate([u6, a6]), 256)

    u7 = Conv2DTranspose(128, 2, strides=2, padding="same")(c6)
    a7 = _attention_gate_se(g=u7, s=c3, filters=64)
    c7 = _residual_block(concatenate([u7, a7]), 128)

    u8 = Conv2DTranspose(64, 2, strides=2, padding="same")(c7)
    a8 = _attention_gate_se(g=u8, s=c2, filters=32)
    c8 = _residual_block(concatenate([u8, a8]), 64)

    u9 = Conv2DTranspose(32, 2, strides=2, padding="same")(c8)
    a9 = _attention_gate_se(g=u9, s=c1, filters=16)
    c9 = _residual_block(concatenate([u9, a9]), 32)

    main_out = Conv2D(1, 1, activation="sigmoid", name="main_output")(c9)

    if not deep_supervision:
        return Model(inp, main_out, name=name)

    # Имена выходов — на последнем слое ветки (Keras берёт name с финального тензора)
    ds3 = Conv2D(1, 1)(c7)
    ds3 = UpSampling2D(size=(4, 4), interpolation="bilinear")(ds3)
    ds3 = Activation("sigmoid", name="ds3_output")(ds3)

    ds2 = Conv2D(1, 1)(c8)
    ds2 = UpSampling2D(size=(2, 2), interpolation="bilinear")(ds2)
    ds2 = Activation("sigmoid", name="ds2_output")(ds2)

    return Model(inp, [main_out, ds2, ds3], name=name)


def ds_loss_weights():
    return {"main_output": 1.0, "ds2_output": 0.4, "ds3_output": 0.2}


def ds_losses(loss_fn):
    return {
        "main_output": loss_fn,
        "ds2_output": loss_fn,
        "ds3_output": loss_fn,
    }


def train_aa_unet(
    X_train,
    y_train,
    X_val,
    y_val,
    img_size=256,
    epochs=50,
    batch_size=8,
    lr=1e-4,
    models_dir=None,
    seed=42,
    target_accuracy: float | None = None,
    target_dice: float | None = None,
    target_iou: float | None = None,
):
    """
    Полный цикл обучения AA-UNet с deep supervision.
    Сохраняет aa_unet_best.keras и aa_unet_brain_mri_final.keras в models_dir.
    """
    if models_dir is None:
        models_dir = os.path.join(os.path.dirname(__file__), "..", "models")

    models_dir = os.path.abspath(models_dir)
    os.makedirs(models_dir, exist_ok=True)

    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

    model_train = build_aa_unet(
        img_size, img_size, 3, deep_supervision=True, name="AA_UNet_train"
    )
    model_train.compile(
        optimizer=Adam(learning_rate=lr),
        loss=ds_losses(bce_dice_loss),
        loss_weights=ds_loss_weights(),
        metrics=_training_metrics(),
    )
    model_train.summary(expand_nested=False)

    aug = dict(
        rotation_range=20,
        width_shift_range=0.15,
        height_shift_range=0.15,
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode="reflect",
    )
    ig = ImageDataGenerator(**aug).flow(X_train, batch_size=batch_size, seed=seed)
    mg = ImageDataGenerator(**aug).flow(y_train, batch_size=batch_size, seed=seed)

    def gen_with_ds():
        for xb, yb in zip(ig, mg):
            yield xb, {"main_output": yb, "ds2_output": yb, "ds3_output": yb}

    ckpt = os.path.join(models_dir, BEST_CHECKPOINT_FILENAME)
    callbacks = [EpochMetricsPrinter()]

    labels = {"accuracy": "Точность", "dice": "Dice", "iou": "IoU"}
    stop_targets = {
        "accuracy": _normalize_metric_threshold(target_accuracy),
        "dice": _normalize_metric_threshold(target_dice),
        "iou": _normalize_metric_threshold(target_iou),
    }
    for name, threshold in stop_targets.items():
        if threshold is None:
            continue
        callbacks.append(
            StopWhenMetricReached(
                monitor=_METRIC_MONITOR[name],
                target=threshold,
                metric_label=labels[name],
            )
        )
        print(
            f"Остановка при достижении {labels[name]} ≥ "
            f"{threshold * 100:.2f}% на валидации"
        )

    callbacks.extend([
        EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            min_lr=1e-7,
            verbose=1,
        ),
        ModelCheckpoint(ckpt, monitor="val_loss", save_best_only=True, verbose=1),
    ])

    steps = max(1, len(X_train) // batch_size)
    history = model_train.fit(
        gen_with_ds(),
        steps_per_epoch=steps,
        epochs=epochs,
        validation_data=(
            X_val,
            {"main_output": y_val, "ds2_output": y_val, "ds3_output": y_val},
        ),
        callbacks=callbacks,
        verbose=1,
    )

    print("\n── Метрики на валидации (основной выход) ──")
    for key in (
        "val_main_output_accuracy",
        "val_main_output_dice_coef",
        "val_main_output_iou_metric",
    ):
        if key in history.history:
            label = key.replace("val_main_output_", "").replace("_", " ").title()
            value = history.history[key][-1]
            print(f"  {label:12s}: {value * 100:.2f}%")

    model_infer = build_aa_unet(
        img_size, img_size, 3, deep_supervision=False, name="AA_UNet"
    )
    for layer in model_infer.layers:
        try:
            src = model_train.get_layer(layer.name)
            layer.set_weights(src.get_weights())
        except Exception:
            pass

    infer_path = os.path.join(models_dir, FINAL_MODEL_FILENAME)
    model_infer.save(infer_path)
    print(f"\nМодель для инференса сохранена: {infer_path}")

    return model_infer, history
