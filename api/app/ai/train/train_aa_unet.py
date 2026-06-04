"""
Обучение AA-UNet на датасете МРТ.

Запуск из каталога api:
    python -m app.ai.train.train_aa_unet
    python -m app.ai.train.train_aa_unet --epochs 30 --batch_size 8
"""

import argparse
import os
import random
import sys

import numpy as np
import tensorflow as tf

from app.ai.train.dataset import load_images
from app.ai.train.modified_unet import FINAL_MODEL_FILENAME, train_aa_unet

SEED = 42

_AI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATASET_DIR = os.path.join(_AI_ROOT, "datasets")
DEFAULT_MODELS_DIR = os.path.join(_AI_ROOT, "models")


def parse_args():
    p = argparse.ArgumentParser(description="Обучение AA-UNet для сегментации МРТ")
    p.add_argument(
        "--data_dir",
        default=DEFAULT_DATASET_DIR,
        help="Каталог с X_train, Y_train, X_val, Y_val",
    )
    p.add_argument(
        "--models_dir",
        default=DEFAULT_MODELS_DIR,
        help="Каталог для сохранения весов",
    )
    p.add_argument("--img_size", type=int, default=256)
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument(
        "--target_accuracy",
        type=float,
        default=None,
        help="Остановить обучение при точности на val (0.92 или 92)",
    )
    p.add_argument(
        "--target_dice",
        type=float,
        default=None,
        help="Остановить обучение при Dice на val (0.90 или 90)",
    )
    p.add_argument(
        "--target_iou",
        type=float,
        default=None,
        help="Остановить обучение при IoU на val (0.85 или 85)",
    )
    return p.parse_args()


def prepare_data(data_dir: str, img_size: int):
    def _load(split_x: str, split_y: str, grayscale_y: bool = True):
        x_path = os.path.join(data_dir, split_x)
        y_path = os.path.join(data_dir, split_y)
        if not os.path.isdir(x_path):
            raise FileNotFoundError(f"Не найдена папка: {x_path}")
        if not os.path.isdir(y_path):
            raise FileNotFoundError(f"Не найдена папка: {y_path}")
        return load_images(x_path), load_images(y_path, grayscale=grayscale_y)

    print(f"Загрузка данных из {data_dir}...")
    X_train, y_train = _load("X_train", "Y_train")
    X_val, y_val = _load("X_val", "Y_val")

    y_train = y_train[..., np.newaxis]
    y_val = y_val[..., np.newaxis]
    y_train = (y_train > 0.5).astype(np.float32)
    y_val = (y_val > 0.5).astype(np.float32)

    print(f"  X_train: {X_train.shape}  Y_train: {y_train.shape}")
    print(f"  X_val:   {X_val.shape}  Y_val:   {y_val.shape}")
    return X_train, y_train, X_val, y_val


def main():
    args = parse_args()

    os.environ["PYTHONHASHSEED"] = str(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)

    X_train, y_train, X_val, y_val = prepare_data(args.data_dir, args.img_size)

    train_aa_unet(
        X_train,
        y_train,
        X_val,
        y_val,
        img_size=args.img_size,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        models_dir=args.models_dir,
        seed=SEED,
        target_accuracy=args.target_accuracy,
        target_dice=args.target_dice,
        target_iou=args.target_iou,
    )

    final_path = os.path.join(args.models_dir, FINAL_MODEL_FILENAME)
    print(f"Готово. Файл для API: {final_path}")


if __name__ == "__main__":
    if __package__ is None:
        api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        sys.path.insert(0, api_dir)
    main()
