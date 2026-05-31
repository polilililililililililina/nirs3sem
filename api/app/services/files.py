import os
from typing import Optional


def delete_file_if_exists(path: Optional[str]) -> None:
    if path and os.path.isfile(path):
        os.remove(path)


def delete_scan_files(scan: dict) -> None:
    delete_file_if_exists(scan.get("file_path"))
    delete_file_if_exists(scan.get("result"))
    delete_file_if_exists(scan.get("heatmap_path"))
    delete_file_if_exists(scan.get("heatmap_raw_path"))
    delete_file_if_exists(scan.get("dicom_path"))
