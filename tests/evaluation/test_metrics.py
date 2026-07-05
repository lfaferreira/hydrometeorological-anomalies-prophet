import pytest
import pandas as pd

from src.evaluation.metrics import evaluate_anomalies

EVENTS = [
    {"name": "Evento A", "region": "rmr", "start_date": "2022-05-25", "end_date": "2022-05-25", "source": "teste"},
]


def test_evaluate_anomalies_computes_expected_confusion_matrix():
    flagged = pd.DataFrame({
        "ds": pd.to_datetime(["2022-05-24", "2022-05-25", "2022-05-26", "2022-05-27"]),
        "is_anomaly": [False, True, False, True],
    })

    result = evaluate_anomalies(flagged, EVENTS, tolerance_days=0)

    # 25/05 é TP (evento real + anomalia detectada); 27/05 é FP (anomalia sem evento);
    # 24 e 26 são TN (sem evento, sem anomalia)
    assert result["true_positives"] == 1
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 0
    assert result["true_negatives"] == 2
    assert result["precision"] == pytest.approx(0.5)
    assert result["recall"] == pytest.approx(1.0)
