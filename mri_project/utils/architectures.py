"""
architectures.py — четыре архитектуры сегментации для сравнительного исследования.

  1. build_unet        — улучшенный U-Net (базовый, описан ранее)
  2. build_attention_unet — U-Net с Attention Gates
  3. build_resunet     — ResUNet (остаточные блоки вместо обычных conv-блоков)
  4. build_unetpp      — U-Net++ (вложенная структура с dense-соединениями)

Все модели принимают одинаковый вход (H, W, 3) и возвращают маску (H, W, 1).
"""

import tensorflow as tf
from tensorflow.keras import backend as K
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Conv2D, MaxPooling2D, Conv2DTranspose,
    concatenate, BatchNormalization, Dropout,
    Activation, Add, Multiply, Lambda,
)


# ════════════════════════════════════════════════════════════
#  Общие вспомогательные блоки
# ════════════════════════════════════════════════════════════

def _conv_bn_relu(x, filters, kernel=3, dropout=0.0):
    """Conv → BN → ReLU (→ optional Dropout)"""
    x = Conv2D(filters, kernel, padding="same", kernel_initializer="he_normal")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)
    if dropout > 0:
        x = Dropout(dropout)(x)
    return x


def _double_conv(x, filters, dropout=0.0):
    """Двойная свёртка с BN/ReLU — базовый блок U-Net."""
    x = _conv_bn_relu(x, filters)
    x = _conv_bn_relu(x, filters, dropout=dropout)
    return x


# ════════════════════════════════════════════════════════════
#  1. U-Net  (улучшенный базовый)
# ════════════════════════════════════════════════════════════

def build_unet(img_h=256, img_w=256, img_c=3, name="UNet"):
    """
    U-Net с 4 уровнями, BatchNorm, Dropout(0.3) в bottleneck,
    Conv2DTranspose вместо UpSampling2D.
    """
    inp = Input((img_h, img_w, img_c))

    # Encoder
    c1 = _double_conv(inp, 16);  p1 = MaxPooling2D(2)(c1)
    c2 = _double_conv(p1,  32);  p2 = MaxPooling2D(2)(c2)
    c3 = _double_conv(p2,  64);  p3 = MaxPooling2D(2)(c3)
    c4 = _double_conv(p3, 128);  p4 = MaxPooling2D(2)(c4)

    # Bottleneck
    c5 = _double_conv(p4, 256, dropout=0.3)

    # Decoder
    u6 = Conv2DTranspose(128, 2, strides=2, padding="same")(c5)
    c6 = _double_conv(concatenate([u6, c4]), 128)

    u7 = Conv2DTranspose(64, 2, strides=2, padding="same")(c6)
    c7 = _double_conv(concatenate([u7, c3]), 64)

    u8 = Conv2DTranspose(32, 2, strides=2, padding="same")(c7)
    c8 = _double_conv(concatenate([u8, c2]), 32)

    u9 = Conv2DTranspose(16, 2, strides=2, padding="same")(c8)
    c9 = _double_conv(concatenate([u9, c1]), 16)

    out = Conv2D(1, 1, activation="sigmoid")(c9)
    return Model(inp, out, name=name)


# ════════════════════════════════════════════════════════════
#  2. Attention U-Net
# ════════════════════════════════════════════════════════════

def _attention_gate(g, s, filters):
    """
    Attention Gate (Oktay et al., 2018).
    g — вектор гейта из декодировщика (более глубокий уровень)
    s — skip-connection из энкодировщика
    Возвращает взвешенный s: модель фокусируется только на
    релевантных пространственных позициях.
    """
    # Приводим размеры: g может быть меньше s по пространству
    Wg = Conv2D(filters, 1, padding="same", kernel_initializer="he_normal")(g)
    Wg = BatchNormalization()(Wg)

    Ws = Conv2D(filters, 1, padding="same", kernel_initializer="he_normal")(s)
    Ws = BatchNormalization()(Ws)

    psi = Activation("relu")(Add()([Wg, Ws]))
    psi = Conv2D(1, 1, padding="same", kernel_initializer="he_normal")(psi)
    psi = BatchNormalization()(psi)
    psi = Activation("sigmoid")(psi)      # attention map ∈ [0, 1]

    return Multiply()([s, psi])           # взвешиваем skip-connection


def build_attention_unet(img_h=256, img_w=256, img_c=3, name="Attention_UNet"):
    """
    Attention U-Net:
      — skip-соединения пропущены через Attention Gate
      — модель автоматически подавляет нерелевантный фон
      — особенно эффективна для мелких опухолей
    """
    inp = Input((img_h, img_w, img_c))

    # Encoder
    c1 = _double_conv(inp, 16);  p1 = MaxPooling2D(2)(c1)
    c2 = _double_conv(p1,  32);  p2 = MaxPooling2D(2)(c2)
    c3 = _double_conv(p2,  64);  p3 = MaxPooling2D(2)(c3)
    c4 = _double_conv(p3, 128);  p4 = MaxPooling2D(2)(c4)

    # Bottleneck
    c5 = _double_conv(p4, 256, dropout=0.3)

    # Decoder с Attention Gates
    u6 = Conv2DTranspose(128, 2, strides=2, padding="same")(c5)
    a6 = _attention_gate(g=u6, s=c4, filters=64)
    c6 = _double_conv(concatenate([u6, a6]), 128)

    u7 = Conv2DTranspose(64, 2, strides=2, padding="same")(c6)
    a7 = _attention_gate(g=u7, s=c3, filters=32)
    c7 = _double_conv(concatenate([u7, a7]), 64)

    u8 = Conv2DTranspose(32, 2, strides=2, padding="same")(c7)
    a8 = _attention_gate(g=u8, s=c2, filters=16)
    c8 = _double_conv(concatenate([u8, a8]), 32)

    u9 = Conv2DTranspose(16, 2, strides=2, padding="same")(c8)
    a9 = _attention_gate(g=u9, s=c1, filters=8)
    c9 = _double_conv(concatenate([u9, a9]), 16)

    out = Conv2D(1, 1, activation="sigmoid")(c9)
    return Model(inp, out, name=name)


# ════════════════════════════════════════════════════════════
#  3. ResUNet
# ════════════════════════════════════════════════════════════

def _residual_block(x, filters, dropout=0.0):
    """
    Остаточный блок (He et al., 2016):
      shortcut = 1×1 Conv для согласования размерностей
      основная ветвь: Conv → BN → ReLU → Conv → BN
      выход: сумма основной ветви и shortcut → ReLU
    Остаточные связи решают проблему затухающих градиентов
    и позволяют строить более глубокие сети без потери качества.
    """
    shortcut = Conv2D(filters, 1, padding="same",
                      kernel_initializer="he_normal")(x)
    shortcut = BatchNormalization()(shortcut)

    x = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    x = Conv2D(filters, 3, padding="same", kernel_initializer="he_normal")(x)
    x = BatchNormalization()(x)

    if dropout > 0:
        x = Dropout(dropout)(x)

    x = Add()([x, shortcut])
    x = Activation("relu")(x)
    return x


def build_resunet(img_h=256, img_w=256, img_c=3, name="ResUNet"):
    """
    ResUNet: U-Net с остаточными блоками вместо обычных double-conv.
    Лучше оптимизируется на глубоких сетях, быстрее сходится.
    """
    inp = Input((img_h, img_w, img_c))

    # Encoder (остаточные блоки)
    c1 = _residual_block(inp, 16);  p1 = MaxPooling2D(2)(c1)
    c2 = _residual_block(p1,  32);  p2 = MaxPooling2D(2)(c2)
    c3 = _residual_block(p2,  64);  p3 = MaxPooling2D(2)(c3)
    c4 = _residual_block(p3, 128);  p4 = MaxPooling2D(2)(c4)

    # Bottleneck
    c5 = _residual_block(p4, 256, dropout=0.3)

    # Decoder (остаточные блоки)
    u6 = Conv2DTranspose(128, 2, strides=2, padding="same")(c5)
    c6 = _residual_block(concatenate([u6, c4]), 128)

    u7 = Conv2DTranspose(64, 2, strides=2, padding="same")(c6)
    c7 = _residual_block(concatenate([u7, c3]), 64)

    u8 = Conv2DTranspose(32, 2, strides=2, padding="same")(c7)
    c8 = _residual_block(concatenate([u8, c2]), 32)

    u9 = Conv2DTranspose(16, 2, strides=2, padding="same")(c8)
    c9 = _residual_block(concatenate([u9, c1]), 16)

    out = Conv2D(1, 1, activation="sigmoid")(c9)
    return Model(inp, out, name=name)


# ════════════════════════════════════════════════════════════
#  4. U-Net++  (вложенная архитектура)
# ════════════════════════════════════════════════════════════

def build_unetpp(img_h=256, img_w=256, img_c=3, name="UNetPP"):
    """
    U-Net++ (Zhou et al., 2018): вложенные dense skip-соединения.

    Обозначение X^{i,j}: i — глубина (уровень пулинга), j — ширина (номер узла).
    Каждый узел X^{i,j} получает на вход:
      - все предыдущие узлы того же уровня глубины: X^{i,0..j-1}
      - апсэмплинг из X^{i+1,j-1}
    Это позволяет агрегировать признаки разных масштабов
    и делает архитектуру менее зависимой от выбора глубины.
    """
    inp = Input((img_h, img_w, img_c))
    nb_filter = [16, 32, 64, 128, 256]

    # ── Уровень 0 (исходное разрешение) ─────────────────────
    x00 = _double_conv(inp,               nb_filter[0])
    p0  = MaxPooling2D(2)(x00)

    x10 = _double_conv(p0,                nb_filter[1])
    p1  = MaxPooling2D(2)(x10)

    x20 = _double_conv(p1,                nb_filter[2])
    p2  = MaxPooling2D(2)(x20)

    x30 = _double_conv(p2,                nb_filter[3])
    p3  = MaxPooling2D(2)(x30)

    x40 = _double_conv(p3, nb_filter[4], dropout=0.3)   # bottleneck

    # ── Уровень j=1 (первый шаг декодирования) ──────────────
    u01 = Conv2DTranspose(nb_filter[0], 2, strides=2, padding="same")(x10)
    x01 = _double_conv(concatenate([x00, u01]), nb_filter[0])

    u11 = Conv2DTranspose(nb_filter[1], 2, strides=2, padding="same")(x20)
    x11 = _double_conv(concatenate([x10, u11]), nb_filter[1])

    u21 = Conv2DTranspose(nb_filter[2], 2, strides=2, padding="same")(x30)
    x21 = _double_conv(concatenate([x20, u21]), nb_filter[2])

    u31 = Conv2DTranspose(nb_filter[3], 2, strides=2, padding="same")(x40)
    x31 = _double_conv(concatenate([x30, u31]), nb_filter[3])

    # ── Уровень j=2 ──────────────────────────────────────────
    u02 = Conv2DTranspose(nb_filter[0], 2, strides=2, padding="same")(x11)
    x02 = _double_conv(concatenate([x00, x01, u02]), nb_filter[0])

    u12 = Conv2DTranspose(nb_filter[1], 2, strides=2, padding="same")(x21)
    x12 = _double_conv(concatenate([x10, x11, u12]), nb_filter[1])

    u22 = Conv2DTranspose(nb_filter[2], 2, strides=2, padding="same")(x31)
    x22 = _double_conv(concatenate([x20, x21, u22]), nb_filter[2])

    # ── Уровень j=3 ──────────────────────────────────────────
    u03 = Conv2DTranspose(nb_filter[0], 2, strides=2, padding="same")(x12)
    x03 = _double_conv(concatenate([x00, x01, x02, u03]), nb_filter[0])

    u13 = Conv2DTranspose(nb_filter[1], 2, strides=2, padding="same")(x22)
    x13 = _double_conv(concatenate([x10, x11, x12, u13]), nb_filter[1])

    # ── Уровень j=4 (финальный) ───────────────────────────────
    u04 = Conv2DTranspose(nb_filter[0], 2, strides=2, padding="same")(x13)
    x04 = _double_conv(concatenate([x00, x01, x02, x03, u04]), nb_filter[0])

    out = Conv2D(1, 1, activation="sigmoid")(x04)
    return Model(inp, out, name=name)


# ════════════════════════════════════════════════════════════
#  Реестр архитектур
# ════════════════════════════════════════════════════════════

ARCHITECTURES = {
    "unet":          build_unet,
    "attention_unet": build_attention_unet,
    "resunet":       build_resunet,
    "unetpp":        build_unetpp,
}


def get_model(name: str, img_h=256, img_w=256, img_c=3):
    """
    Возвращает несобранную модель по имени.
    Пример: model = get_model("attention_unet")
    """
    key = name.lower().replace("-", "_").replace("+", "p")
    if key not in ARCHITECTURES:
        raise ValueError(f"Неизвестная архитектура: {name}. "
                         f"Доступны: {list(ARCHITECTURES.keys())}")
    return ARCHITECTURES[key](img_h=img_h, img_w=img_w, img_c=img_c)
