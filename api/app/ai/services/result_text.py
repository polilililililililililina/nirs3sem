from typing import Optional

from app.ai.services.dicom_loader import generate_volume_conclusion

ANOMALY_RESULT_DESC = (
    "Обнаружены признаки возможной аномалии. "
    "Результат носит вспомогательный характер и не является медицинским диагнозом."
)

NORMAL_RESULT_DESC = (
    "Признаков аномалии не выявлено. "
    "Результат носит вспомогательный характер."
)

DISCLAIMER = (
    " Результат носит вспомогательный характер и не является медицинским диагнозом."
)


def build_result_desc(
    tumor_detected: bool,
    volume_stats: Optional[dict] = None,
) -> str:
    if volume_stats:
        return generate_volume_conclusion(volume_stats) + DISCLAIMER

    if tumor_detected:
        return ANOMALY_RESULT_DESC
    return NORMAL_RESULT_DESC
