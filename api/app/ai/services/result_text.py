ANOMALY_RESULT_DESC = (
    "Обнаружены признаки возможной аномалии. "
    "Результат носит вспомогательный характер и не является медицинским диагнозом."
)

NORMAL_RESULT_DESC = (
    "Признаков аномалии не выявлено. "
    "Результат носит вспомогательный характер."
)


def build_result_desc(tumor_detected: bool) -> str:
    if tumor_detected:
        return ANOMALY_RESULT_DESC
    return NORMAL_RESULT_DESC
