"""Métricas de avaliação das anomalias detectadas contra eventos históricos conhecidos."""

import datetime as dt
import logging
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def _event_date_range(event: dict, tolerance_days: int) -> set:
    start = dt.date.fromisoformat(event["start_date"]) - dt.timedelta(days=tolerance_days)
    end = dt.date.fromisoformat(event["end_date"]) + dt.timedelta(days=tolerance_days)
    return {start + dt.timedelta(days=i) for i in range((end - start).days + 1)}


def evaluate_anomalies(flagged: pd.DataFrame, known_events: List[dict], tolerance_days: int = 1) -> Dict[str, float]:
    """Compara anomalias detectadas com eventos históricos conhecidos.

    Um dia conta como "evento real" se cair dentro de [início - tolerance_days,
    fim + tolerance_days] de qualquer evento em `known_events`.

    Args:
        flagged: DataFrame com colunas `ds` e `is_anomaly`.
        known_events: Lista de eventos no formato de `KNOWN_EXTREME_EVENTS`.
        tolerance_days: Margem de dias de tolerância ao redor de cada evento.

    Returns:
        Dicionário com `precision`, `recall`, `f1`, `false_positive_rate` e as
        contagens `true_positives`, `false_positives`, `false_negatives`, `true_negatives`.
    """
    event_days = set()
    for event in known_events:
        event_days |= _event_date_range(event, tolerance_days)

    df = flagged.copy()
    df["date"] = df["ds"].dt.date
    df["is_real_event"] = df["date"].isin(event_days)

    tp = int(((df["is_anomaly"]) & (df["is_real_event"])).sum())
    fp = int(((df["is_anomaly"]) & (~df["is_real_event"])).sum())
    fn = int(((~df["is_anomaly"]) & (df["is_real_event"])).sum())
    tn = int(((~df["is_anomaly"]) & (~df["is_real_event"])).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    logger.info("Avaliação: precision=%.3f recall=%.3f f1=%.3f fpr=%.3f", precision, recall, f1, fpr)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
    }
