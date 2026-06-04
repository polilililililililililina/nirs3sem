# Модуль ИИ

## Продакшен (API)

**U-Net:** `app/ai/models/unet_brain_mri_final.keras` — загружается в `services/model.py`.

Поддержка **DICOM** (`.dcm`, ZIP) через `dicom_loader`.

## Обучение AA-UNet (эксперименты, не используется API по умолчанию)

Из каталога `api/` (с активированным venv):

```bash
python -m app.ai.train.train_aa_unet
python -m app.ai.train.train_aa_unet --epochs 30 --batch_size 8

# Остановка при достижении Dice ≥ 90% на валидации
python -m app.ai.train.train_aa_unet --target_dice 90

# Остановка при точности ≥ 92%
python -m app.ai.train.train_aa_unet --target_accuracy 92
```

Порог можно задать долей (`0.9`) или процентами (`90`).

По умолчанию также работает **EarlyStopping** по `val_loss` (patience 8 эпох без улучшения).

Датасет: `app/ai/datasets/` (`X_train`, `Y_train`, `X_val`, `Y_val`).

Результат: `app/ai/models/aa_unet_brain_mri_final.keras` (и чекпоинт `aa_unet_best.keras`).

## Сравнение архитектур (только терминал, для исследования)

```bash
python -m app.ai.train.compare_architectures
python -m app.ai.train.compare_architectures --epochs 20 --models unet attention_unet resunet unetpp
```

Артефакты: `app/ai/train/outputs/comparison_results/` (`metrics.csv`, графики).

## Инференс в API

Сервис загружает `unet_brain_mri_final.keras` при первом анализе (`app/ai/services/model.py`).

## DICOM

- `POST /scans/upload-dicom` — один файл `.dcm` (конвертация через `dicom_loader`)
- `POST /scans/upload-dicom-zip` — ZIP с папкой `.dcm` (лимит `MAX_DICOM_ZIP_MB`, по умолчанию 200)

Объём обрабатывается в worker; для UI сохраняется репрезентативный срез и маска.
