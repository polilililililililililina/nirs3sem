"""
dicom_loader.py — загрузка и предобработка DICOM-файлов (.dcm).

Поддерживает:
  • Одиночный .dcm файл → один срез
  • Папка с .dcm файлами → весь объём (все срезы), отсортированный по позиции
  • Экспорт срезов в PNG для дальнейшего обучения / визуализации

Зависимость: pip install pydicom
"""

import os
import numpy as np
from PIL import Image

from app.ai.services.preprocess import IMG_HEIGHT, IMG_WIDTH

DEFAULT_SLICE_SIZE = (IMG_WIDTH, IMG_HEIGHT)


def _require_pydicom():
    try:
        import pydicom
        return pydicom
    except ImportError:
        raise ImportError(
            "Для работы с DICOM установите pydicom:\n"
            "  pip install pydicom"
        )


# ── Нормализация одного 2D-среза ────────────────────────────

def normalize_slice(arr: np.ndarray) -> np.ndarray:
    """
    Нормализует 2D-массив пикселей в диапазон [0, 1].
    Применяет window-level нормализацию (min-max по срезу).
    """
    arr = arr.astype(np.float32)
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-6:          # плоский срез (воздух / артефакт)
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def apply_window(arr: np.ndarray, wc: float, ww: float) -> np.ndarray:
    """
    Оконная нормализация (Window Center / Window Width) —
    стандартный способ отображения МРТ/КТ в клинических системах.

    Args:
        arr : массив HU-значений (или произвольных пикселей)
        wc  : центр окна (Window Center)
        ww  : ширина окна (Window Width)
    """
    lo = wc - ww / 2
    hi = wc + ww / 2
    arr = np.clip(arr, lo, hi)
    return (arr - lo) / (hi - lo + 1e-6)


# ── Чтение одного .dcm файла ────────────────────────────────

DICOM_EXTENSIONS = (".dcm", ".dicom")

_SKIP_DIR_NAMES = {"__macosx", ".ds_store"}


def is_dicom_file(filename: str) -> bool:
    lower = filename.lower()
    return lower.endswith(DICOM_EXTENSIONS)


def _has_dicom_magic(path: str) -> bool:
    try:
        if os.path.getsize(path) < 132:
            return False
        with open(path, "rb") as handle:
            handle.seek(128)
            return handle.read(4) == b"DICM"
    except OSError:
        return False


def is_dicom_path(path: str) -> bool:
    name = os.path.basename(path)
    if name.startswith("._") or name in (".ds_store",):
        return False
    if name.lower().endswith(DICOM_EXTENSIONS):
        return True
    return _has_dicom_magic(path)


def find_dicom_file_paths(root: str) -> list[str]:
    """Рекурсивно находит DICOM-файлы (.dcm, .dicom или без расширения с маркером DICM)."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d.lower() not in _SKIP_DIR_NAMES and not d.startswith(".")
        ]
        for name in filenames:
            if name.startswith("._"):
                continue
            path = os.path.join(dirpath, name)
            if is_dicom_path(path):
                found.append(path)
    return sorted(found)


def save_rgb_array_as_png(arr: np.ndarray, output_path: str) -> str:
    """Сохраняет float32 RGB-массив (H, W, 3) в PNG."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    image = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode="RGB")
    image.save(output_path, format="PNG")
    return output_path


def dicom_to_png(
    dicom_path: str,
    output_path: str,
    size: tuple[int, int] = DEFAULT_SLICE_SIZE,
    use_window: bool = False,
) -> str:
    """Конвертирует один DICOM-срез в PNG (препроцессинг как при обучении)."""
    arr = read_dicom_slice(dicom_path, size=size, use_window=use_window)
    return save_rgb_array_as_png(arr, output_path)


def read_dicom_slice(
    path: str,
    size: tuple[int, int] = DEFAULT_SLICE_SIZE,
    use_window: bool = False,
) -> np.ndarray:
    """
    Читает один DICOM-срез и возвращает нормализованный массив (H, W, 3).

    Args:
        path       : путь к .dcm файлу
        size       : целевой размер (W, H)
        use_window : использовать Window Center/Width из метаданных DICOM
    Returns:
        float32 массив формы (H, W, 3), значения [0, 1]
    """
    pydicom = _require_pydicom()
    ds = pydicom.dcmread(path)

    # Получаем пиксельный массив с применением RescaleSlope/Intercept
    pixel = ds.pixel_array.astype(np.float32)
    if hasattr(ds, "RescaleSlope") and hasattr(ds, "RescaleIntercept"):
        pixel = pixel * float(ds.RescaleSlope) + float(ds.RescaleIntercept)

    if use_window and hasattr(ds, "WindowCenter") and hasattr(ds, "WindowWidth"):
        wc = float(ds.WindowCenter) if not isinstance(ds.WindowCenter, pydicom.multival.MultiValue) \
             else float(ds.WindowCenter[0])
        ww = float(ds.WindowWidth)  if not isinstance(ds.WindowWidth,  pydicom.multival.MultiValue) \
             else float(ds.WindowWidth[0])
        pixel = apply_window(pixel, wc, ww)
    else:
        pixel = normalize_slice(pixel)

    # Конвертируем в PIL для ресайза, затем в RGB
    img_pil = Image.fromarray((pixel * 255).astype(np.uint8), mode="L")
    img_pil = img_pil.resize(size, Image.BILINEAR)
    img_rgb = img_pil.convert("RGB")
    return np.array(img_rgb, dtype=np.float32) / 255.0


# ── Сортировка срезов по позиции ────────────────────────────

def _slice_position(ds) -> float:
    """
    Возвращает позицию среза для корректной сортировки объёма.
    Приоритет: ImagePositionPatient[2] > SliceLocation > InstanceNumber.
    """
    pydicom = _require_pydicom()
    if hasattr(ds, "ImagePositionPatient"):
        return float(ds.ImagePositionPatient[2])
    if hasattr(ds, "SliceLocation"):
        return float(ds.SliceLocation)
    if hasattr(ds, "InstanceNumber"):
        return float(ds.InstanceNumber)
    return 0.0


# ── Загрузка всего объёма из папки ─────────────────────────

def load_dicom_volume(
    folder: str,
    size: tuple[int, int] = DEFAULT_SLICE_SIZE,
    use_window: bool = False,
    skip_empty: bool = True,
    empty_threshold: float = 0.01,
) -> tuple[np.ndarray, list[str]]:
    """
    Загружает все .dcm файлы из папки как упорядоченный объём.

    Args:
        folder          : путь к папке с .dcm файлами
        size            : целевой размер каждого среза (W, H)
        use_window      : применять Window Center/Width из метаданных
        skip_empty      : пропускать «пустые» срезы (воздух / шум)
        empty_threshold : доля ненулевых пикселей ниже которой срез считается пустым
    Returns:
        volume  : float32 массив (N, H, W, 3)  — N отобранных срезов
        paths   : список путей к файлам в том же порядке
    """
    pydicom = _require_pydicom()

    dcm_files = find_dicom_file_paths(folder)
    if not dcm_files:
        raise FileNotFoundError(
            f"В папке {folder} не найдено DICOM-файлов (.dcm / .dicom / без расширения)"
        )

    # Читаем метаданные для сортировки
    datasets = []
    for path in dcm_files:
        try:
            ds = pydicom.dcmread(path, stop_before_pixels=True)
            datasets.append((path, ds))
        except Exception as e:
            print(f"  ⚠ Пропускаем {path}: {e}")

    # Сортируем по позиции в пространстве
    datasets.sort(key=lambda x: _slice_position(x[1]))

    slices, valid_paths = [], []
    for path, _ in datasets:
        try:
            arr = read_dicom_slice(path, size=size, use_window=use_window)

            if skip_empty:
                nonzero_ratio = np.count_nonzero(arr) / arr.size
                if nonzero_ratio < empty_threshold:
                    continue                         # пропускаем пустой срез

            slices.append(arr)
            valid_paths.append(path)
        except Exception as e:
            print(f"  ⚠ Ошибка чтения {path}: {e}")

    if not slices:
        raise ValueError("Не удалось загрузить ни одного среза из папки")

    volume = np.stack(slices, axis=0)               # (N, H, W, 3)
    return volume, valid_paths


# ── Экспорт срезов в PNG ────────────────────────────────────

def export_slices_to_png(
    volume: np.ndarray,
    output_dir: str,
    prefix: str = "slice",
) -> list[str]:
    """
    Сохраняет все срезы объёма как PNG-файлы.

    Args:
        volume     : float32 массив (N, H, W, 3)
        output_dir : папка для сохранения
        prefix     : префикс имён файлов
    Returns:
        список путей к сохранённым файлам
    """
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    for i, arr in enumerate(volume):
        img = Image.fromarray((arr * 255).astype(np.uint8), mode="RGB")
        path = os.path.join(output_dir, f"{prefix}_{i:04d}.png")
        img.save(path)
        saved.append(path)
    print(f"💾 Сохранено {len(saved)} срезов в {output_dir}")
    return saved


# ── Предсказание по всему объёму ───────────────────────────

def predict_volume(
    model,
    volume: np.ndarray,
    batch_size: int = 8,
    threshold: float = 0.5,
) -> np.ndarray:
    """
    Прогоняет все срезы объёма через модель сегментации.

    Args:
        model      : обученная Keras-модель
        volume     : float32 массив (N, H, W, 3)
        batch_size : размер батча при инференсе
        threshold  : порог бинаризации предсказания
    Returns:
        masks : uint8 массив (N, H, W) — бинарные маски
    """
    n = len(volume)
    masks = []
    for start in range(0, n, batch_size):
        batch = volume[start:start + batch_size]
        preds = model.predict(batch, verbose=0)
        if isinstance(preds, list):
            preds = preds[0]
        preds = np.asarray(preds)
        binary = (preds[..., 0] > threshold).astype(np.uint8)
        masks.append(binary)

    masks = np.concatenate(masks, axis=0)           # (N, H, W)
    return masks


# ── Статистика по объёму ────────────────────────────────────

def volume_stats(masks: np.ndarray) -> dict:
    """
    Вычисляет статистику поражённых областей по всему объёму.

    Returns:
        dict с ключами:
          n_slices         — всего срезов
          n_positive       — срезов с обнаруженной патологией
          total_area_frac  — доля поражённых пикселей от общего объёма
          max_slice_idx    — индекс среза с максимальной площадью поражения
          per_slice_area   — список долей для каждого среза
    """
    per_slice = [m.sum() / m.size for m in masks]
    n_pos = sum(1 for a in per_slice if a > 0)
    total = np.mean(per_slice)
    max_idx = int(np.argmax(per_slice))
    return {
        "n_slices":        len(masks),
        "n_positive":      n_pos,
        "total_area_frac": float(total),
        "max_slice_idx":   max_idx,
        "per_slice_area":  per_slice,
    }


# ── Формирование текстового заключения ─────────────────────

def generate_volume_conclusion(stats: dict) -> str:
    """
    Генерирует текстовое заключение по результатам анализа объёма.
    """
    frac = stats["total_area_frac"] * 100
    n_pos = stats["n_positive"]
    n_all = stats["n_slices"]
    max_i = stats["max_slice_idx"]

    if frac < 0.5:
        verdict = "Патологических областей не обнаружено"
    elif frac < 3.0:
        verdict = "Выявлены небольшие области, требующие внимания"
    elif frac < 10.0:
        verdict = "Обнаружены патологические изменения умеренной степени"
    else:
        verdict = "Обнаружены выраженные патологические изменения"

    return (
        f"{verdict}. "
        f"Проанализировано {n_all} срезов, патология выявлена на {n_pos} срезах "
        f"({n_pos/n_all*100:.1f}%). "
        f"Средняя площадь поражения: {frac:.2f}%. "
        f"Наибольшая площадь — срез №{max_i + 1}."
    )


# ── Быстрый пример использования ───────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование: python dicom_loader.py <папка_с_dcm или файл.dcm>")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isdir(path):
        volume, paths = load_dicom_volume(path, size=(256, 256))
        export_slices_to_png(volume, output_dir="dicom_export")
    else:
        arr = read_dicom_slice(path, size=(256, 256))
        print(f"Срез загружен: shape={arr.shape}, min={arr.min():.3f}, max={arr.max():.3f}")
        img = Image.fromarray((arr * 255).astype(np.uint8))
        img.save("dicom_slice.png")
        print("Сохранён как dicom_slice.png")
