"""Detecção de anomalias a partir do intervalo de incerteza do Prophet."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def flag_anomalies(actual: pd.DataFrame, forecast: pd.DataFrame) -> pd.DataFrame:
    """Marca como anomalia todo ponto observado fora do intervalo de incerteza previsto.

    Args:
        actual: DataFrame observado, colunas `ds`, `y`.
        forecast: DataFrame previsto, colunas `ds`, `yhat`, `yhat_lower`, `yhat_upper`.

    Returns:
        DataFrame mesclado por `ds` com as colunas de entrada mais `is_anomaly` (bool)
        e `severity` (float >= 0: quanto `y` ultrapassa o limite do intervalo mais
        próximo; 0 quando não é anomalia).
    """
    merged = actual.merge(forecast, on="ds", how="inner")

    below = merged["y"] < merged["yhat_lower"]
    above = merged["y"] > merged["yhat_upper"]
    merged["is_anomaly"] = below | above

    severity_below = (merged["yhat_lower"] - merged["y"]).clip(lower=0)
    severity_above = (merged["y"] - merged["yhat_upper"]).clip(lower=0)
    merged["severity"] = np.maximum(severity_below, severity_above)

    logger.info("%d anomalias detectadas em %d dias", merged["is_anomaly"].sum(), len(merged))
    return merged
