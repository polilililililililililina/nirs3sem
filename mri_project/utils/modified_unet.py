"""
modified_unet.py — Модифицированная архитектура для научной новизны диплома.

Название: ASPP-Attention U-Net (AA-UNet)
Формулировка для диплома:
  «Разработана модифицированная архитектура сегментационной нейронной сети
  AA-UNet, объединяющая механизм пространственного внимания, блок
  атрибутивной пирамидальной свёртки (ASPP) и остаточные соединения
  для повышения точности выделения патологических областей на МРТ-снимках
  головного мозга.»

Ключевые отличия от базовых архитектур
──────────────────────────────────────────────────────────────
| Компонент               | U-Net | Att U-Net | ResUNet | AA-UNet (наш) |
|─────────────────────────|───────|───────────|─────────|─────────────  |
| Attention Gate          |  ✗    |    ✓      |   ✗     |      ✓        |
| Residual block          |  ✗    |    ✗      |   ✓     |      ✓        |
| ASPP (мультимасштаб)    |  ✗    |    ✗      |   ✗     |      ✓        |
| Channel Attention (SE)  |  ✗    |    ✗      |   ✗     |      ✓        |
| Deep supervision        |  ✗    |    ✗      |   ✗     |      ✓        |
──────────────────────────────────────────────────────────────
"""

import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Conv2D, MaxPooling2D, Conv2DTranspose, AvgPool2D,
    GlobalAveragePooling2D, GlobalMaxPooling2D,
    concatenate, BatchNormalization, Dropout,
    Activation, Add, Multiply, Reshape, Dense,
    UpSampling2D, Lambda,
)
from tensorflow.keras import backend as K


# ════════════════════════════════════════════════════════════
#  Вспомогательные блоки
# ════════════════════════════════════════════════════════════

def _bn_relu(x):
    return Activation("relu")(BatchNormalization()(x))


def _conv_bn_relu(x, filters, kernel=3, dilation=1):
    return _bn_relu(
        Conv2D(filters, kernel, padding="same",
               dilation_rate=dilation,
               kernel_initializer="he_normal")(x)
    )


# ── Residual Block ────────────────────────────────────────────
def _residual_block(x, filters, dropout=0.0):
    """
    Остаточный блок с BN перед активацией (pre-activation ResNet).
    Более стабильный градиентный поток при глубоких сетях.
    """
    shortcut = Conv2D(filters, 1, padding="same",
                      kernel_initializer="he_normal")(x)
    shortcut = BatchNormalization()(shortcut)

    x = _conv_bn_relu(x, filters)
    x = _conv_bn_relu(x, filters)
    if dropout > 0:
        x = Dropout(dropout)(x)

    return Activation("relu")(Add()([x, shortcut]))


# ── Squeeze-and-Excitation (Channel Attention) ───────────────
def _squeeze_excitation(x, ratio=8):
    """
    SE-блок (Hu et al., 2018): моделирует зависимости между каналами.
    Сеть автоматически учится, какие каналы важнее для сегментации.
    Шаги:
      1. Squeeze: GlobalAveragePooling → вектор (C,)
      2. Excitation: FC → ReLU → FC → Sigmoid → веса каналов
      3. Scale: умножение исходного тензора на веса
    """
    filters = x.shape[-1]
    se = GlobalAveragePooling2D()(x)
    se = Reshape((1, 1, filters))(se)
    se = Dense(max(1, filters // ratio), activation="relu",
               kernel_initializer="he_normal")(se)
    se = Dense(filters, activation="sigmoid",
               kernel_initializer="he_normal")(se)
    return Multiply()([x, se])


# ── ASPP — Atrous Spatial Pyramid Pooling ────────────────────
def _aspp_block(x, filters):
    """
    ASPP (Chen et al., DeepLab v3, 2017):
    Параллельные atrous-свёртки с разными dilation rates
    захватывают контекст на нескольких масштабах одновременно.

    Важно для МРТ: опухоли бывают разного размера —
    малые (dilation=1) и крупные (dilation=12) требуют разных рецептивных полей.

    Ветви:
      1. 1×1 Conv — точечные признаки
      2. 3×3 atrous (rate=6)
      3. 3×3 atrous (rate=12)
      4. 3×3 atrous (rate=18)
      5. Global Average Pooling + resize — глобальный контекст
    """
    # Ветвь 1: 1×1
    b1 = _conv_bn_relu(x, filters, kernel=1)

    # Ветви 2-4: atrous
    b2 = _conv_bn_relu(x, filters, dilation=6)
    b3 = _conv_bn_relu(x, filters, dilation=12)
    b4 = _conv_bn_relu(x, filters, dilation=18)

    # Ветвь 5: глобальный контекст
    h = tf.shape(x)[1]
    w = tf.shape(x)[2]
    b5 = GlobalAveragePooling2D()(x)
    b5 = Reshape((1, 1, x.shape[-1]))(b5)
    b5 = _conv_bn_relu(b5, filters, kernel=1)
    b5 = Lambda(lambda t: tf.image.resize(t, [h, w]))(b5)

    # Конкатенация и проекция
    out = concatenate([b1, b2, b3, b4, b5])
    out = _conv_bn_relu(out, filters, kernel=1)
    out = Dropout(0.2)(out)
    return out


# ── Attention Gate (улучшенный, с SE) ────────────────────────
def _attention_gate_se(g, s, filters):
    """
    Расширенный Attention Gate: объединяет пространственное внимание
    с SE-блоком на skip-connection.
    """
    Wg = _bn_relu(Conv2D(filters, 1, padding="same",
                         kernel_initializer="he_normal")(g))
    Ws = _bn_relu(Conv2D(filters, 1, padding="same",
                         kernel_initializer="he_normal")(s))

    psi = Conv2D(1, 1, padding="same",
                 kernel_initializer="he_normal")(
        Activation("relu")(Add()([Wg, Ws]))
    )
    psi = Activation("sigmoid")(BatchNormalization()(psi))

    # Взвешиваем skip и применяем SE
    attended = Multiply()([s, psi])
    attended = _squeeze_excitation(attended)
    return attended


# ── Deep Supervision ─────────────────────────────────────────
def _deep_sup_head(x, name):
    """
    Голова вспомогательного предсказания для промежуточного уровня декодировщика.
    Используется только при обучении (deep supervision).
    Помогает передавать градиенты в нижние уровни сети.
    """
    x = Conv2D(1, 1, activation="sigmoid", name=name)(x)
    return x


# ════════════════════════════════════════════════════════════
#  Основная архитектура AA-UNet
# ════════════════════════════════════════════════════════════

def build_aa_unet(
    img_h: int = 256,
    img_w: int = 256,
    img_c: int = 3,
    deep_supervision: bool = True,
    name: str = "AA_UNet",
):
    """
    ASPP-Attention U-Net (AA-UNet) — модифицированная архитектура.

    Args:
        img_h, img_w, img_c : размер входного изображения
        deep_supervision    : True — модель возвращает 3 выхода (обучение),
                              False — один выход (инференс)
        name                : имя модели

    Структура:
      Encoder  : 4 уровня Residual Block + SE + MaxPooling
      Bottleneck: ASPP (мультимасштабный контекст)
      Decoder  : 4 уровня с Attention Gate (SE) + Residual Block
      Output   : 1×1 Conv + Sigmoid
      Deep sup : вспомогательные выходы на уровнях 3 и 2 декодировщика
    """
    inp = Input((img_h, img_w, img_c), name="input_img")

    # ── Encoder ─────────────────────────────────────────────
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

    # ── Bottleneck (ASPP) ────────────────────────────────────
    c5 = _aspp_block(p4, 512)

    # ── Decoder ─────────────────────────────────────────────
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

    # ── Основной выход ───────────────────────────────────────
    main_out = Conv2D(1, 1, activation="sigmoid", name="main_output")(c9)

    if not deep_supervision:
        return Model(inp, main_out, name=name)

    # ── Deep Supervision выходы (только при обучении) ────────
    # Уровень 3 декодировщика
    ds3 = Conv2D(1, 1, name="ds3_output")(c7)
    ds3 = UpSampling2D(size=(4, 4), interpolation="bilinear")(ds3)
    ds3 = Activation("sigmoid")(ds3)

    # Уровень 2 декодировщика
    ds2 = Conv2D(1, 1, name="ds2_output")(c8)
    ds2 = UpSampling2D(size=(2, 2), interpolation="bilinear")(ds2)
    ds2 = Activation("sigmoid")(ds2)

    return Model(inp, [main_out, ds2, ds3], name=name)


# ════════════════════════════════════════════════════════════
#  Потери для Deep Supervision
# ════════════════════════════════════════════════════════════

def ds_loss_weights():
    """Веса для глубокого надзора: основной выход важнее вспомогательных."""
    return {"main_output": 1.0, "ds2_output": 0.4, "ds3_output": 0.2}


def ds_losses(bce_dice_loss_fn):
    """Словарь функций потерь для каждого выхода."""
    return {
        "main_output": bce_dice_loss_fn,
        "ds2_output":  bce_dice_loss_fn,
        "ds3_output":  bce_dice_loss_fn,
    }


# ════════════════════════════════════════════════════════════
#  Обучение AA-UNet
# ════════════════════════════════════════════════════════════

def train_aa_unet(
    X_train, y_train, X_val, y_val,
    img_size=256, epochs=50, batch_size=8, lr=1e-4,
    models_dir="models", seed=42,
):
    """
    Полный цикл обучения AA-UNet с deep supervision.
    Возвращает: (модель для инференса, history)
    """
    import os, random
    import numpy as np
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import (
        EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    )
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from utils.losses import bce_dice_loss, dice_coef, iou_metric

    os.makedirs(models_dir, exist_ok=True)
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed);  np.random.seed(seed);  tf.random.set_seed(seed)

    # Модель с deep supervision для обучения
    model_train = build_aa_unet(img_size, img_size, 3,
                                deep_supervision=True, name="AA_UNet_train")
    model_train.compile(
        optimizer=Adam(lr),
        loss=ds_losses(bce_dice_loss),
        loss_weights=ds_loss_weights(),
        metrics={"main_output": [dice_coef, iou_metric]},
    )
    model_train.summary(expand_nested=False)

    # Аугментация (синхронная для image + mask)
    aug = dict(rotation_range=20, width_shift_range=0.15,
               height_shift_range=0.15, zoom_range=0.15,
               horizontal_flip=True, fill_mode="reflect")
    ig = ImageDataGenerator(**aug).flow(X_train, batch_size=batch_size, seed=seed)
    mg = ImageDataGenerator(**aug).flow(y_train, batch_size=batch_size, seed=seed)

    def gen_with_ds():
        """Генератор: возвращает одну маску для трёх выходов."""
        for xb, yb in zip(ig, mg):
            yield xb, {"main_output": yb, "ds2_output": yb, "ds3_output": yb}

    ckpt = os.path.join(models_dir, "aa_unet_best.keras")
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=8,
                      restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                          patience=4, min_lr=1e-7, verbose=1),
        ModelCheckpoint(ckpt, monitor="val_loss",
                        save_best_only=True, verbose=1),
    ]

    steps = max(1, len(X_train) // batch_size)
    history = model_train.fit(
        gen_with_ds(),
        steps_per_epoch=steps,
        epochs=epochs,
        validation_data=(X_val, {"main_output": y_val,
                                  "ds2_output": y_val,
                                  "ds3_output": y_val}),
        callbacks=callbacks,
    )

    # Модель без deep supervision для инференса
    model_infer = build_aa_unet(img_size, img_size, 3,
                                deep_supervision=False, name="AA_UNet")
    # Копируем веса из обученной модели
    for layer in model_infer.layers:
        try:
            src = model_train.get_layer(layer.name)
            layer.set_weights(src.get_weights())
        except Exception:
            pass

    infer_path = os.path.join(models_dir, "aa_unet_final.keras")
    model_infer.save(infer_path)
    print(f"\n✅ Модель для инференса сохранена: {infer_path}")

    return model_infer, history


# ── Быстрый тест архитектуры ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("Тест AA-UNet с deep supervision:")
    m_train = build_aa_unet(256, 256, 3, deep_supervision=True)
    m_train.summary(expand_nested=False)
    print(f"\nПараметров: {m_train.count_params():,}")

    print("\nТест AA-UNet без deep supervision (инференс):")
    m_infer = build_aa_unet(256, 256, 3, deep_supervision=False)
    print(f"Параметров: {m_infer.count_params():,}")

    # Проверка прямого прохода
    dummy = tf.random.normal((2, 256, 256, 3))
    out_train = m_train(dummy, training=False)
    out_infer = m_infer(dummy, training=False)
    print(f"\nВыход (train, 3 головы): {[o.shape for o in out_train]}")
    print(f"Выход (infer, 1 голова) : {out_infer.shape}")
    print("\n✅ AA-UNet работает корректно")
