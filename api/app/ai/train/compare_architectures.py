"""
compare_architectures.py — сравнительное исследование архитектур сегментации.

Только для запуска из терминала (не используется в HTTP/worker).

Запуск из каталога api:
    python -m app.ai.train.compare_architectures
    python -m app.ai.train.compare_architectures --epochs 20 --img_size 128
"""

import os
import random
import sys
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image

import tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import precision_score, recall_score

from app.ai.train.architectures import ARCHITECTURES, get_model
from app.ai.services.metrics import bce_dice_loss, dice_coef, iou_metric

_TRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DATA_DIR = os.path.abspath(os.path.join(_TRAIN_DIR, "..", "datasets"))
_DEFAULT_OUT_DIR = os.path.abspath(
    os.path.join(_TRAIN_DIR, "outputs", "comparison_results")
)

# ── Воспроизводимость ─────────────────────────────────────────────────────────
SEED = 42
os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Сравнение архитектур сегментации МРТ")
    p.add_argument("--data_dir", default=_DEFAULT_DATA_DIR)
    p.add_argument("--out_dir", default=_DEFAULT_OUT_DIR)
    p.add_argument("--img_size",   type=int,   default=256)
    p.add_argument("--batch_size", type=int,   default=8)
    p.add_argument("--epochs",     type=int,   default=30)
    p.add_argument("--lr",         type=float, default=1e-4)
    p.add_argument("--threshold",  type=float, default=0.5)
    p.add_argument(
        "--models",
        nargs="+",
        default=list(ARCHITECTURES.keys()),
        help="Список архитектур для сравнения"
    )
    return p.parse_args()


# ── Загрузка данных ───────────────────────────────────────────────────────────
def load_images(folder, size, grayscale=False):
    fnames = sorted(f for f in os.listdir(folder)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif")))
    if not fnames:
        raise FileNotFoundError(f"Нет изображений в {folder}")
    imgs = []
    for fn in fnames:
        mode = "L" if grayscale else "RGB"
        img = Image.open(os.path.join(folder, fn)).convert(mode).resize(
            (size, size), Image.BILINEAR)
        imgs.append(np.array(img, dtype=np.float32) / 255.0)
    return np.array(imgs)


def prepare_data(data_dir, img_size):
    X_tr = load_images(os.path.join(data_dir, "X_train"), img_size)
    y_tr = load_images(os.path.join(data_dir, "Y_train"), img_size, grayscale=True)
    X_v = load_images(os.path.join(data_dir, "X_val"), img_size)
    y_v = load_images(os.path.join(data_dir, "Y_val"), img_size, grayscale=True)

    y_tr = (y_tr[..., np.newaxis] > 0.5).astype(np.float32)
    y_v  = (y_v [..., np.newaxis] > 0.5).astype(np.float32)
    return X_tr, y_tr, X_v, y_v


def augmented_gen(X, y, batch_size):
    kw = dict(rotation_range=15, width_shift_range=0.1,
              height_shift_range=0.1, zoom_range=0.1,
              horizontal_flip=True, fill_mode="reflect")
    ig = ImageDataGenerator(**kw).flow(X, batch_size=batch_size, seed=SEED)
    mg = ImageDataGenerator(**kw).flow(y, batch_size=batch_size, seed=SEED)
    for xb, yb in zip(ig, mg):
        yield xb, yb


# ── Полные метрики (numpy) ────────────────────────────────────────────────────
def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                    threshold: float = 0.5) -> dict:
    """
    Вычисляет Dice, IoU, Precision, Recall по всей валидационной выборке.
    y_true, y_pred: (N, H, W, 1) или (N, H, W), значения [0,1].
    """
    yt = (y_true.flatten() > threshold).astype(np.uint8)
    yp = (y_pred.flatten() > threshold).astype(np.uint8)

    smooth = 1e-6
    inter  = np.sum(yt * yp)
    union  = np.sum(yt) + np.sum(yp)

    dice = (2 * inter + smooth) / (union + smooth)
    iou  = (inter + smooth) / (np.sum(yt) + np.sum(yp) - inter + smooth)
    prec = precision_score(yt, yp, zero_division=0)
    rec  = recall_score(yt, yp, zero_division=0)
    f1   = 2 * prec * rec / (prec + rec + smooth)

    return {"dice": float(dice), "iou": float(iou),
            "precision": float(prec), "recall": float(rec), "f1": float(f1)}


# ── Обучение одной модели ─────────────────────────────────────────────────────
def train_one(model_name, args, X_tr, y_tr, X_v, y_v) -> dict:
    print(f"\n{'='*60}")
    print(f"  Обучение: {model_name.upper()}")
    print(f"{'='*60}")

    model = get_model(model_name, img_h=args.img_size,
                      img_w=args.img_size, img_c=3)
    model.compile(
        optimizer=Adam(args.lr),
        loss=bce_dice_loss,
        metrics=["accuracy", dice_coef, iou_metric],
    )
    print(f"  Параметров: {model.count_params():,}")

    ckpt_path = os.path.join(args.out_dir, "weights", f"{model_name}_best.keras")
    os.makedirs(os.path.dirname(ckpt_path), exist_ok=True)

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=7,
                      restore_best_weights=True, verbose=0),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                          patience=3, min_lr=1e-7, verbose=0),
        ModelCheckpoint(ckpt_path, monitor="val_loss",
                        save_best_only=True, verbose=0),
    ]

    steps = max(1, len(X_tr) // args.batch_size)
    history = model.fit(
        augmented_gen(X_tr, y_tr, args.batch_size),
        steps_per_epoch=steps,
        epochs=args.epochs,
        validation_data=(X_v, y_v),
        callbacks=callbacks,
        verbose=1,
    )

    # Предсказание и полные метрики
    preds = model.predict(X_v, verbose=0)
    metrics = compute_metrics(y_v, preds, threshold=args.threshold)
    metrics["params"] = model.count_params()
    metrics["best_val_loss"] = float(min(history.history["val_loss"]))
    metrics["epochs_trained"] = len(history.history["loss"])

    print(f"\n  ✅ {model_name} | "
          f"Dice={metrics['dice']:.4f} | "
          f"IoU={metrics['iou']:.4f} | "
          f"Prec={metrics['precision']:.4f} | "
          f"Rec={metrics['recall']:.4f}")

    return {"metrics": metrics, "history": history.history, "preds": preds}


# ── Таблица результатов (текст) ───────────────────────────────────────────────
def print_results_table(results: dict):
    names   = list(results.keys())
    headers = ["Архитектура", "Dice", "IoU", "Precision", "Recall", "Params (M)", "Эпох"]
    widths  = [18, 8, 8, 10, 8, 12, 7]

    sep = "+" + "+".join("-" * w for w in widths) + "+"
    row_fmt = "|" + "|".join(f" {{:<{w-1}}}" for w in widths) + "|"

    print("\n" + sep)
    print(row_fmt.format(*headers))
    print(sep)

    best_dice = max(results[n]["metrics"]["dice"] for n in names)

    for name in names:
        m = results[name]["metrics"]
        marker = " ★" if m["dice"] == best_dice else ""
        print(row_fmt.format(
            name + marker,
            f"{m['dice']:.4f}",
            f"{m['iou']:.4f}",
            f"{m['precision']:.4f}",
            f"{m['recall']:.4f}",
            f"{m['params']/1e6:.2f}M",
            str(m["epochs_trained"]),
        ))
    print(sep)


# ── Графики ───────────────────────────────────────────────────────────────────
def plot_training_curves(results: dict, out_dir: str):
    """Кривые обучения (loss + dice) для всех архитектур на одном графике."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    styles = ["-", "--", "-.", ":"]

    for i, (name, res) in enumerate(results.items()):
        h = res["history"]
        ls = styles[i % len(styles)]
        axes[0].plot(h["val_loss"],      label=name, linestyle=ls, linewidth=2)
        axes[1].plot(h["val_dice_coef"], label=name, linestyle=ls, linewidth=2)

    for ax, title, ylabel in zip(
        axes,
        ["Функция потерь (val)", "Dice Coefficient (val)"],
        ["BCE + Dice Loss", "Dice"],
    ):
        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Эпоха")
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, alpha=0.4)

    plt.suptitle("Сравнение архитектур — динамика обучения", fontsize=16, y=1.01)
    plt.tight_layout()
    path = os.path.join(out_dir, "training_curves.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"📊 График кривых обучения: {path}")


def plot_metrics_bar(results: dict, out_dir: str):
    """Столбчатая диаграмма всех метрик."""
    names   = list(results.keys())
    metrics = ["dice", "iou", "precision", "recall"]
    labels  = ["Dice", "IoU", "Precision", "Recall"]
    colors  = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

    x = np.arange(len(names))
    width = 0.2

    fig, ax = plt.subplots(figsize=(14, 7))
    for i, (metric, label, color) in enumerate(zip(metrics, labels, colors)):
        vals = [results[n]["metrics"][metric] for n in names]
        bars = ax.bar(x + i * width, vals, width, label=label, color=color, alpha=0.85)
        # подписи значений
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.005,
                    f"{v:.3f}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(names, fontsize=12)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Значение метрики")
    ax.set_title("Сравнение архитектур по метрикам сегментации", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.4)

    plt.tight_layout()
    path = os.path.join(out_dir, "metrics_bar.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"📊 Столбчатая диаграмма: {path}")


def plot_radar(results: dict, out_dir: str):
    """Радарная диаграмма (spider chart) для визуального сравнения."""
    from matplotlib.patches import FancyArrowPatch
    metrics = ["dice", "iou", "precision", "recall"]
    labels  = ["Dice", "IoU", "Precision", "Recall"]
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})

    for (name, res), color in zip(results.items(), colors):
        vals = [res["metrics"][m] for m in metrics]
        vals += vals[:1]
        ax.plot(angles, vals, "o-", linewidth=2, label=name, color=color)
        ax.fill(angles, vals, alpha=0.1, color=color)

    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=13)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=9)
    ax.set_title("Сравнение архитектур (радарная диаграмма)",
                 fontsize=14, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1))
    ax.grid(True, alpha=0.4)

    plt.tight_layout()
    path = os.path.join(out_dir, "radar_chart.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"📊 Радарная диаграмма: {path}")


def plot_predictions_grid(results: dict, X_v, y_v, out_dir, n_samples=4):
    """
    Сетка предсказаний: строки — архитектуры, столбцы — примеры снимков.
    Позволяет визуально оценить качество масок каждой модели.
    """
    sample_ids = random.sample(range(len(X_v)), min(n_samples, len(X_v)))
    arch_names = list(results.keys())
    n_arch = len(arch_names)

    fig = plt.figure(figsize=(4 * n_samples + 1, 3 * (n_arch + 2)))
    gs  = gridspec.GridSpec(n_arch + 2, n_samples, figure=fig, hspace=0.05, wspace=0.05)

    for col, idx in enumerate(sample_ids):
        # Оригинал
        ax = fig.add_subplot(gs[0, col])
        ax.imshow(X_v[idx])
        ax.axis("off")
        if col == 0:
            ax.set_ylabel("Оригинал", fontsize=11, rotation=90, labelpad=40)

        # Ground Truth
        ax = fig.add_subplot(gs[1, col])
        ax.imshow(y_v[idx, ..., 0], cmap="gray")
        ax.axis("off")
        if col == 0:
            ax.set_ylabel("GT Mask", fontsize=11, rotation=90, labelpad=40)

        # Предсказания каждой модели
        for row, name in enumerate(arch_names):
            ax = fig.add_subplot(gs[row + 2, col])
            pred = (results[name]["preds"][idx, ..., 0] > 0.5).astype(np.float32)
            ax.imshow(pred, cmap="gray")
            ax.axis("off")
            if col == 0:
                ax.set_ylabel(name, fontsize=11, rotation=90, labelpad=40)

    fig.suptitle("Сравнение предсказаний архитектур", fontsize=14, y=1.005)
    plt.tight_layout()
    path = os.path.join(out_dir, "predictions_grid.png")
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.show()
    print(f"📊 Сетка предсказаний: {path}")


# ── Сохранение результатов ────────────────────────────────────────────────────
def save_results(results: dict, out_dir: str):
    """Сохраняет метрики в JSON для последующего использования."""
    export = {}
    for name, res in results.items():
        export[name] = res["metrics"]

    path = os.path.join(out_dir, "metrics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Метрики сохранены: {path}")

    # CSV для удобства
    csv_path = os.path.join(out_dir, "metrics.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("architecture,dice,iou,precision,recall,f1,params,epochs\n")
        for name, res in results.items():
            m = res["metrics"]
            f.write(f"{name},{m['dice']:.4f},{m['iou']:.4f},"
                    f"{m['precision']:.4f},{m['recall']:.4f},{m['f1']:.4f},"
                    f"{m['params']},{m['epochs_trained']}\n")
    print(f"💾 CSV: {csv_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    print(f"📂 Загрузка данных из {args.data_dir}...")
    X_tr, y_tr, X_v, y_v = prepare_data(args.data_dir, args.img_size)
    print(f"  Train: {X_tr.shape}, Val: {X_v.shape}")

    results = {}
    for model_name in args.models:
        res = train_one(model_name, args, X_tr, y_tr, X_v, y_v)
        results[model_name] = res

    # Итоговая таблица
    print("\n" + "=" * 60)
    print("  ИТОГОВАЯ ТАБЛИЦА МЕТРИК")
    print("=" * 60)
    print_results_table(results)

    # Графики
    plot_training_curves(results, args.out_dir)
    plot_metrics_bar(results, args.out_dir)
    plot_radar(results, args.out_dir)
    plot_predictions_grid(results, X_v, y_v, args.out_dir)

    # Сохранение
    save_results(results, args.out_dir)

    # Вывод лучшей архитектуры
    best = max(results, key=lambda n: results[n]["metrics"]["dice"])
    print(f"\n🏆 Лучшая архитектура по Dice Score: {best.upper()} "
          f"(Dice={results[best]['metrics']['dice']:.4f})")


if __name__ == "__main__":
    if __package__ is None:
        api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        sys.path.insert(0, api_dir)
    main()
