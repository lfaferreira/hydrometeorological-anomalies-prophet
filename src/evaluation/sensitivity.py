"""Análise de sensibilidade da detecção de anomalias ao parâmetro `interval_width`
do Prophet — mede o trade-off entre precisão e recall conforme o intervalo de
incerteza é alargado ou estreitado."""

import logging
from typing import List

import pandas as pd

from src.models.prophet_model import fit_prophet_model, generate_forecast
from src.models.anomaly_detection import flag_anomalies
from src.evaluation.metrics import evaluate_anomalies

logger = logging.getLogger(__name__)


def run_interval_width_sensitivity(
    train: pd.DataFrame,
    full_df: pd.DataFrame,
    known_events: List[dict],
    widths: List[float],
) -> pd.DataFrame:
    """Roda o pipeline completo de detecção + avaliação para cada `interval_width`.

    Args:
        train: DataFrame de treino (ds, y).
        full_df: DataFrame completo (treino+teste) sobre o qual gerar o forecast.
        known_events: Eventos conhecidos, no formato de `KNOWN_EXTREME_EVENTS`.
        widths: Lista de larguras de intervalo de incerteza a testar (ex.: [0.8, 0.9, 0.95]).

    Returns:
        DataFrame com uma linha por `interval_width` e as métricas resultantes.
    """
    rows = []
    for width in widths:
        model = fit_prophet_model(train, interval_width=width)
        forecast = generate_forecast(model, full_df[["ds"]])
        flagged = flag_anomalies(full_df, forecast)
        metrics = evaluate_anomalies(flagged, known_events, tolerance_days=1)
        rows.append({"interval_width": width, "n_anomalies": int(flagged["is_anomaly"].sum()), **metrics})
        logger.info("interval_width=%.2f -> %s", width, metrics)

    return pd.DataFrame(rows)
