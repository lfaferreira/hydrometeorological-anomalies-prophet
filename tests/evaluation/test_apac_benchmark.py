import pandas as pd

from src.evaluation.apac_benchmark import classify_apac_level, compare_with_prophet


def test_classify_apac_level_uses_documented_thresholds():
    assert classify_apac_level(10.0) == "sem_aviso"
    assert classify_apac_level(30.1) == "observacao"
    assert classify_apac_level(50.1) == "atencao"
    assert classify_apac_level(100.0) == "alerta"  # decisão de implementação: fecha a lacuna dos 100mm


def test_compare_with_prophet_adds_apac_level_column():
    flagged = pd.DataFrame({
        "ds": pd.to_datetime(["2022-05-24", "2022-05-25"]),
        "y": [10.0, 150.0],
        "is_anomaly": [False, True],
    })

    result = compare_with_prophet(flagged)

    assert list(result["apac_level"]) == ["sem_aviso", "alerta"]
