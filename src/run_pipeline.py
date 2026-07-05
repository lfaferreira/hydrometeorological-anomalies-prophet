"""Orquestração ponta-a-ponta: carrega a série processada de uma região, ajusta o
Prophet, detecta anomalias e avalia contra os eventos históricos conhecidos."""

import logging
from pathlib import Path

import pandas as pd

from src.models.prophet_model import fit_prophet_model, generate_forecast, train_test_split_temporal
from src.models.anomaly_detection import flag_anomalies
from src.evaluation.known_events import KNOWN_EXTREME_EVENTS
from src.evaluation.metrics import evaluate_anomalies

logger = logging.getLogger(__name__)

PROCESSED_DATA_DIR = Path(__file__).resolve().parent.parent / "dados" / "processed"

REGION_FILES = {
    "rmr": PROCESSED_DATA_DIR / "serie_prophet_rmr_2020_2025.csv",
}


def load_processed_series(region: str) -> pd.DataFrame:
    """Carrega a série processada (ds, y) de uma região já gerada pelo pipeline de dados."""
    df = pd.read_csv(REGION_FILES[region])
    df["ds"] = pd.to_datetime(df["ds"])
    return df


def run_full_pipeline(region: str = "rmr") -> dict:
    """Roda o pipeline completo para a RMR e retorna as métricas de avaliação.

    Args:
        region: Única chave suportada por este plano é "rmr" (ver Global Constraints).

    Returns:
        Dicionário de métricas, no formato de `evaluate_anomalies`.
    """
    df = load_processed_series(region)
    train, _test = train_test_split_temporal(df, test_size_days=180)
    model = fit_prophet_model(train)
    forecast = generate_forecast(model, df[["ds"]])
    flagged = flag_anomalies(df, forecast)

    region_events = [e for e in KNOWN_EXTREME_EVENTS if e["region"] == region]
    metrics = evaluate_anomalies(flagged, region_events, tolerance_days=1)
    logger.info("Pipeline completo para região '%s': %s", region, metrics)
    return metrics


if __name__ == "__main__":
    print(run_full_pipeline("rmr"))
