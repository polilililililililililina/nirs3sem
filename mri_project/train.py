"""
train.py — обучение U-Net на датасете МРТ головного мозга.

Запуск:
    python train.py
    python train.py --epochs 30 --batch_size 8 --img_size 128
"""

import os
import sys
import random
import argparse
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard,
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ── Воспроизводимость ────────────────────────────────────────
SEED = 42
os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

# ── Импорт из utils ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from utils import build_unet, bce_dice_loss, dice_coef, iou_metric


# ── CLI-аргументы ────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Обучение U-Net для сегментации МРТ")
    p.add_argument("--data_dir",    default="data",    help="Корневая папка с данными")
    p.add_argument("--models_dir",  default="models",  help="Куда сохранять веса модели")
    p.add_argument("--img_size",    type=int, default=256)
    p.add_argument("--batch_size",  type=int, default=16)
    p.add_argument("--epochs",      type=int, default=50)
    p.add_argument("--lr",          type=float, default=1e-4)
    return p.parse_args()


# ── Загрузка данных ──────────────────────────────────────────
def load_images(folder, size, grayscale=False):
    """Загружает все изображения из папки, ресайзит и нормализует."""
    images = []
    fnames = sorted(f for f in os.listdir(folder)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif")))
    if not fnames:
        raise FileNotFoundError(f"В папке {folder} нет изображений!")

    for fname in fnames:
        path = os.path.join(folder, fname)
        mode = "L" if grayscale else "RGB"
        img  = Image.open(path).convert(mode).resize((size, size), Image.BILINEAR)
        images.append(np.array(img, dtype=np.float32) / 255.0)

    return np.array(images)


def prepare_data(data_dir, img_size):
    print("📂 Загрузка данных...")
    X_train = load_images(os.path.join(data_dir, "X_train"), img_size)
    y_train = load_images(os.path.join(data_dir, "y_train"), img_size, grayscale=True)
    X_val   = load_images(os.path.join(data_dir, "X_val"),   img_size)
    y_val   = load_images(os.path.join(data_dir, "y_val"),   img_size, grayscale=True)

    # (N, H, W) → (N, H, W, 1)
    y_train = y_train[..., np.newaxis]
    y_val   = y_val[..., np.newaxis]

    # Бинаризация масок (после ресайза могут быть промежуточные значения)
    y_train = (y_train > 0.5).astype(np.float32)
    y_val   = (y_val   > 0.5).astype(np.float32)

    print(f"  X_train: {X_train.shape}  y_train: {y_train.shape}")
    print(f"  X_val:   {X_val.shape}    y_val:   {y_val.shape}")
    return X_train, y_train, X_val, y_val


# ── Аугментация ──────────────────────────────────────────────
def augmented_generator(X, y, batch_size, seed=SEED):
    """
    Совместная аугментация: одни и те же трансформации применяются
    синхронно к изображению и маске (одинаковый seed).
    """
    aug_args = dict(
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1,
        horizontal_flip=True,
        fill_mode="reflect",
    )
    img_gen  = ImageDataGenerator(**aug_args)
    mask_gen = ImageDataGenerator(**aug_args)

    img_flow  = img_gen.flow(X, batch_size=batch_size, seed=seed)
    mask_flow = mask_gen.flow(y, batch_size=batch_size, seed=seed)

    for x_b, y_b in zip(img_flow, mask_flow):
        yield x_b, y_b


# ── Графики ──────────────────────────────────────────────────
def plot_and_save_history(history, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    metrics = [
        ("loss",       "Функция потерь (BCE+Dice)"),
        ("dice_coef",  "Dice Coefficient"),
        ("iou_metric", "IoU (Jaccard)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, (metric, title) in zip(axes, metrics):
        ax.plot(history.history.get(metric,          []), label="train")
        ax.plot(history.history.get(f"val_{metric}", []), label="val")
        ax.set_title(title)
        ax.set_xlabel("Эпоха")
        ax.legend()
        ax.grid(True)
    plt.tight_layout()
    path = os.path.join(save_dir, "training_history.png")
    plt.savefig(path, dpi=150)
    plt.show()
    print(f"📊 График сохранён: {path}")


def visualize_predictions(X_val, y_val, predictions, save_dir, n=5, threshold=0.5):
    """Сохраняет сравнение: оригинал | GT маска | предсказание | наложение."""
    os.makedirs(save_dir, exist_ok=True)
    indices = random.sample(range(len(X_val)), min(n, len(X_val)))

    for idx in indices:
        pred_bin = (predictions[idx, ..., 0] > threshold).astype(np.uint8)
        gt       =  y_val[idx, ..., 0]
        img      =  X_val[idx]

        overlay = img.copy()
        overlay[..., 1] = np.clip(overlay[..., 1] + gt       * 0.4, 0, 1)
        overlay[..., 0] = np.clip(overlay[..., 0] + pred_bin * 0.4, 0, 1)

        dice_val = (2 * np.sum(gt * pred_bin) + 1e-6) / (
                    np.sum(gt) + np.sum(pred_bin) + 1e-6)

        fig, axes = plt.subplots(1, 4, figsize=(18, 5))
        fig.suptitle(f"Снимок #{idx}  |  Dice = {dice_val:.3f}", fontsize=13)
        for ax, data, title in zip(
            axes,
            [img, gt, pred_bin, overlay],
            ["МРТ", "Маска (GT)", "Предсказание", "Наложение"],
        ):
            ax.imshow(data, cmap="gray" if data.ndim == 2 else None)
            ax.set_title(title)
            ax.axis("off")

        plt.tight_layout()
        path = os.path.join(save_dir, f"pred_{idx:04d}.png")
        plt.savefig(path, dpi=120)
        plt.close()

    print(f"🖼️  Примеры предсказаний сохранены в: {save_dir}")


# ── Главная функция ──────────────────────────────────────────
def main():
    args = parse_args()
    os.makedirs(args.models_dir, exist_ok=True)

    # Данные
    X_train, y_train, X_val, y_val = prepare_data(args.data_dir, args.img_size)

    # Модель
    model = build_unet(args.img_size, args.img_size, 3)
    model.summary()

    model.compile(
        optimizer=Adam(learning_rate=args.lr),
        loss=bce_dice_loss,
        metrics=["accuracy", dice_coef, iou_metric],
    )

    best_model_path = os.path.join(args.models_dir, "best_unet.keras")

    callbacks = [
        EarlyStopping(
            monitor="val_loss", patience=8,
            restore_best_weights=True, verbose=1
        ),
        ReduceLROnPlateau(
            monitor="val_loss", factor=0.5,
            patience=4, min_lr=1e-7, verbose=1
        ),
        ModelCheckpoint(
            best_model_path, monitor="val_loss",
            save_best_only=True, verbose=1
        ),
        TensorBoard(log_dir="logs", histogram_freq=0),
    ]

    # Обучение
    print("\n🚀 Начало обучения...")
    steps_per_epoch = max(1, len(X_train) // args.batch_size)

    history = model.fit(
        augmented_generator(X_train, y_train, args.batch_size),
        steps_per_epoch=steps_per_epoch,
        epochs=args.epochs,
        validation_data=(X_val, y_val),
        callbacks=callbacks,
    )

    # Оценка
    print("\n── Метрики на валидации ──────────────────────────")
    results = model.evaluate(X_val, y_val, return_dict=True)
    for k, v in results.items():
        print(f"  {k:20s}: {v:.4f}")

    # Сохранение финальной модели
    final_path = os.path.join(args.models_dir, "unet_final.keras")
    model.save(final_path)
    print(f"\n✅ Модель сохранена: {final_path}")

    # Визуализации
    plot_and_save_history(history, save_dir="results")
    predictions = model.predict(X_val)
    visualize_predictions(X_val, y_val, predictions, save_dir="results/predictions")


if __name__ == "__main__":
    main()
