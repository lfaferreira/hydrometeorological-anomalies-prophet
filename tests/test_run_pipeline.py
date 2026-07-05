import pandas as pd

from src.run_pipeline import run_full_pipeline


def test_run_full_pipeline_returns_metrics_dict(monkeypatch, tiny_prophet_df):
    monkeypatch.setattr(
        "src.run_pipeline.load_processed_series",
        lambda region: tiny_prophet_df,
    )

    result = run_full_pipeline(region="rmr")

    assert {"precision", "recall", "f1", "false_positive_rate"}.issubset(result.keys())
