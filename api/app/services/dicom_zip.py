import os
import zipfile

from app.ai.services.dicom_loader import find_dicom_file_paths


class UnsafeZipError(ValueError):
    pass


_SKIP_DIR_NAMES = {"__macosx", ".ds_store"}


def safe_extract_zip(zip_path: str, dest_dir: str) -> None:
    """Распаковывает ZIP с защитой от path traversal."""
    os.makedirs(dest_dir, exist_ok=True)
    dest_abs = os.path.abspath(dest_dir)

    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue

            relative = member.filename.replace("\\", "/").lstrip("/")
            if not relative or relative.startswith("__MACOSX/"):
                continue

            target = os.path.abspath(os.path.join(dest_dir, relative))
            if not target.startswith(dest_abs + os.sep) and target != dest_abs:
                raise UnsafeZipError("Архив содержит небезопасные пути")

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with archive.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())


def count_dicom_files(folder: str) -> int:
    return len(find_dicom_file_paths(folder))
