"""
Архитектура улучшенного U-Net для сегментации МРТ головного мозга.
"""

from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Conv2D, MaxPooling2D, Conv2DTranspose,
    concatenate, BatchNormalization, Dropout, Activation,
)


def conv_block(x, filters, dropout_rate=0.0):
    """
    Базовый блок: Conv → BN → ReLU → Conv → BN → ReLU → [Dropout].
    He-инициализация оптимальна для ReLU-сетей.
    """
    x = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    x = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    if dropout_rate > 0:
        x = Dropout(dropout_rate)(x)
    return x


def build_unet(img_h=256, img_w=256, img_c=3):
    """
    U-Net v2:
      • 4 уровня кодировщика (было 2)
      • BatchNorm в каждом блоке
      • Dropout(0.3) в узком месте (bottleneck)
      • Conv2DTranspose — обучаемый апсэмплинг (было UpSampling2D)
    """
    inputs = Input((img_h, img_w, img_c), name="input")

    # ── Кодировщик ──────────────────────────────────────────
    c1 = conv_block(inputs, 16);          p1 = MaxPooling2D(2)(c1)
    c2 = conv_block(p1,     32);          p2 = MaxPooling2D(2)(c2)
    c3 = conv_block(p2,     64);          p3 = MaxPooling2D(2)(c3)
    c4 = conv_block(p3,    128);          p4 = MaxPooling2D(2)(c4)

    # ── Bottleneck ──────────────────────────────────────────
    c5 = conv_block(p4, 256, dropout_rate=0.3)

    # ── Декодировщик ────────────────────────────────────────
    u6 = Conv2DTranspose(128, 2, strides=2, padding="same")(c5)
    c6 = conv_block(concatenate([u6, c4]), 128)

    u7 = Conv2DTranspose(64, 2, strides=2, padding="same")(c6)
    c7 = conv_block(concatenate([u7, c3]), 64)

    u8 = Conv2DTranspose(32, 2, strides=2, padding="same")(c7)
    c8 = conv_block(concatenate([u8, c2]), 32)

    u9 = Conv2DTranspose(16, 2, strides=2, padding="same")(c8)
    c9 = conv_block(concatenate([u9, c1]), 16)

    outputs = Conv2D(1, 1, activation="sigmoid", name="output")(c9)

    return Model(inputs, outputs, name="UNet_v2")
