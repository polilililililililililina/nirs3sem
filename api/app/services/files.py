import os
import shutil
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
    delete_file_if_exists(scan.get("dicom_zip_path"))

    dicom_folder = scan.get("dicom_folder")
    if dicom_folder and os.path.isdir(dicom_folder):
        shutil.rmtree(dicom_folder, ignore_errors=True)

    scan_dir = scan.get("input_dir")
    if scan_dir and os.path.isdir(scan_dir):
        shutil.rmtree(scan_dir, ignore_errors=True)
