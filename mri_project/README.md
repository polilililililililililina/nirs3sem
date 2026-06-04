# MRI Brain Segmentation — полный проект

Проект для магистерской ВКР: сегментация МРТ головного мозга  
на основе методов глубокого обучения.

---

## Структура проекта

```
mri_project/
├── utils/
│   ├── losses.py           # Dice Loss, BCE+Dice, IoU
│   ├── model.py            # Базовый U-Net
│   ├── architectures.py    # U-Net, Attention U-Net, ResUNet, U-Net++
│   ├── modified_unet.py    # AA-UNet (научная новизна)
│   └── dicom_loader.py     # Загрузка и обработка DICOM-файлов
├── data/
│   ├── X_train/            # Обучающие МРТ-снимки (PNG/JPG)
│   ├── y_train/            # Маски сегментации
│   ├── X_val/              # Валидационные снимки
│   └── y_val/              # Валидационные маски
├── models/                 # Сохранённые веса моделей
├── results/                # Графики и предсказания
├── comparison_results/     # Результаты сравнения архитектур
├── train.py                # Обучение базового U-Net
├── compare_architectures.py # Сравнение 4 архитектур
└── requirements.txt
```

---

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Обучение базового U-Net

```bash
python train.py
python train.py --epochs 30 --batch_size 8 --img_size 128
```

### 3. Сравнительное исследование архитектур (научная новизна)

```bash
python compare_architectures.py
python compare_architectures.py --epochs 20 --models unet attention_unet resunet unetpp
```

Результаты сохраняются в `comparison_results/`:
- `metrics.csv` — таблица метрик
- `training_curves.png` — кривые обучения
- `metrics_bar.png` — столбчатая диаграмма
- `radar_chart.png` — радарная диаграмма
- `predictions_grid.png` — сетка предсказаний

### 4. Обучение модифицированного AA-UNet

```python
from utils import train_aa_unet
model, history = train_aa_unet(X_train, y_train, X_val, y_val, epochs=50)
```

---

## Работа с DICOM-файлами

### Один срез

```python
from utils.dicom_loader import read_dicom_slice
arr = read_dicom_slice("scan.dcm", size=(256, 256))
# arr: float32 (256, 256, 3)
```

### Весь объём (все срезы)

```python
from utils.dicom_loader import (
    load_dicom_volume, predict_volume,
    volume_stats, generate_volume_conclusion
)

# Загрузка всех срезов из папки
volume, paths = load_dicom_volume("patient_001/", size=(256, 256))
# volume: (N, 256, 256, 3)

# Предсказание
import tensorflow as tf
model = tf.keras.models.load_model("models/best_unet.keras", ...)
masks = predict_volume(model, volume, batch_size=8)

# Статистика и заключение
stats = volume_stats(masks)
conclusion = generate_volume_conclusion(stats)
print(conclusion)
```

### Экспорт срезов в PNG

```bash
python utils/dicom_loader.py /path/to/dicom_folder
```

---

## Архитектуры

| Название              | Особенности                                  |
|-----------------------|----------------------------------------------|
| U-Net                 | Базовая, BatchNorm, Conv2DTranspose          |
| Attention U-Net       | Skip-connections через Attention Gate        |
| ResUNet               | Остаточные блоки вместо double-conv          |
| U-Net++               | Вложенные dense skip-connections             |
| **AA-UNet** (наш)     | ASPP + SE-блоки + Attention + Deep Supervision |

---

## Научная новизна (AA-UNet)

**Предложена архитектура AA-UNet**, объединяющая:

1. **Residual Block** — стабильный градиентный поток
2. **Squeeze-and-Excitation** (SE) — внимание по каналам
3. **ASPP** — мультимасштабный контекст (dilation 6/12/18)
4. **Attention Gate + SE** на skip-соединениях
5. **Deep Supervision** — вспомогательные выходы для лучшего обучения

```
Формулировка для диплома:
«Разработана модифицированная архитектура AA-UNet, объединяющая
блок атрибутивной пирамидальной свёртки (ASPP) для захвата
мультимасштабного контекста, механизм пространственного внимания
с SE-блоками для подавления нерелевантного фона и стратегию
глубокого надзора (deep supervision) для улучшения обучения на
ограниченных датасетах медицинских изображений.»
```

---

## Метрики

- **Dice Coefficient (F1)** — основная метрика, перекрытие масок
- **IoU (Jaccard)** — отношение пересечения к объединению
- **Precision** — точность: доля верных положительных предсказаний
- **Recall** — полнота: доля найденных патологических пикселей

---

## Датасет

Рекомендуется **BRISC2025** (Kaggle):  
https://www.kaggle.com/datasets/briscdataset/brisc2025

Структура данных должна соответствовать:
```
data/X_train/  — МРТ-снимки (RGB, PNG/JPG)
data/y_train/  — бинарные маски (Grayscale, PNG)
data/X_val/    — валидационные снимки
data/y_val/    — валидационные маски
```
