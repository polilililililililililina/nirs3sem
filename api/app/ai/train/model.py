from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input,
    Conv2D,
    MaxPooling2D,
    BatchNormalization,
    Activation,
    Dropout,
    Conv2DTranspose,
    concatenate,
)


def conv_block(x, filters, dropout_rate=0.0):
    x = Conv2D(
        filters,
        3,
        padding="same",
        kernel_initializer="he_normal"
    )(x)

    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    x = Conv2D(
        filters,
        3,
        padding="same",
        kernel_initializer="he_normal"
    )(x)

    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    if dropout_rate > 0:
        x = Dropout(dropout_rate)(x)

    return x


def unet_model(
    img_h=256,
    img_w=256,
    img_c=3
):
    inputs = Input((img_h, img_w, img_c))

    c1 = conv_block(inputs, 16)
    p1 = MaxPooling2D(2)(c1)

    c2 = conv_block(p1, 32)
    p2 = MaxPooling2D(2)(c2)

    c3 = conv_block(p2, 64)
    p3 = MaxPooling2D(2)(c3)

    c4 = conv_block(p3, 128)
    p4 = MaxPooling2D(2)(c4)

    c5 = conv_block(p4, 256, dropout_rate=0.3)

    u6 = Conv2DTranspose(
        128,
        2,
        strides=2,
        padding="same"
    )(c5)

    u6 = concatenate([u6, c4])

    c6 = conv_block(u6, 128)

    u7 = Conv2DTranspose(
        64,
        2,
        strides=2,
        padding="same"
    )(c6)

    u7 = concatenate([u7, c3])

    c7 = conv_block(u7, 64)

    u8 = Conv2DTranspose(
        32,
        2,
        strides=2,
        padding="same"
    )(c7)

    u8 = concatenate([u8, c2])

    c8 = conv_block(u8, 32)

    u9 = Conv2DTranspose(
        16,
        2,
        strides=2,
        padding="same"
    )(c8)

    u9 = concatenate([u9, c1])

    c9 = conv_block(u9, 16)

    outputs = Conv2D(
        1,
        1,
        activation="sigmoid"
    )(c9)

    return Model(inputs, outputs)