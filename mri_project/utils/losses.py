"""
Кастомные функции потерь и метрики для сегментации МРТ.
Импортируются и в train.py, и в app.py — без дублирования.
"""

import tensorflow as tf
from tensorflow.keras import backend as K


def dice_coef(y_true, y_pred, smooth=1e-6):
    """Dice / F1 — основная метрика для несбалансированных масок."""
    y_true_f = K.flatten(K.cast(y_true, tf.float32))
    y_pred_f = K.flatten(K.cast(y_pred, tf.float32))
    intersection = K.sum(y_true_f * y_pred_f)
    return (2.0 * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)


def dice_loss(y_true, y_pred):
    return 1.0 - dice_coef(y_true, y_pred)


def bce_dice_loss(y_true, y_pred):
    """Комбинированная функция потерь: Binary Crossentropy + Dice Loss."""
    bce = tf.keras.losses.binary_crossentropy(y_true, y_pred)
    return bce + dice_loss(y_true, y_pred)


def iou_metric(y_true, y_pred, smooth=1e-6):
    """Intersection over Union (Jaccard Index)."""
    y_true_f = K.flatten(K.cast(y_true, tf.float32))
    y_pred_f = K.flatten(K.cast(y_pred, tf.float32))
    intersection = K.sum(y_true_f * y_pred_f)
    union = K.sum(y_true_f) + K.sum(y_pred_f) - intersection
    return (intersection + smooth) / (union + smooth)


# Словарь для передачи в load_model(custom_objects=...)
CUSTOM_OBJECTS = {
    "bce_dice_loss": bce_dice_loss,
    "dice_coef":     dice_coef,
    "iou_metric":    iou_metric,
}
