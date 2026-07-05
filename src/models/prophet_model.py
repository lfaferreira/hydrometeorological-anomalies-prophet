"""Ajuste do modelo Prophet sobre séries diárias de precipitação."""

import logging
from typing import Tuple

import pandas as pd
from prophet import Prophet

logger = logging.getLogger(__name__)


def train_test_split_temporal(df: pd.DataFrame, test_size_days: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Divide a série em treino/teste respeitando a ordem temporal (sem embaralhar).

    Args:
        df: DataFrame ordenado por `ds`, colunas `ds` e `y`.
        test_size_days: Quantidade de dias mais recentes reservados para teste.

    Returns:
        Tupla (treino, teste).
    """
    df_sorted = df.sort_values("ds").reset_index(drop=True)
    split_idx = len(df_sorted) - test_size_days
    train = df_sorted.iloc[:split_idx].reset_index(drop=True)
    test = df_sorted.iloc[split_idx:].reset_index(drop=True)
    logger.info("Split temporal: %d dias de treino, %d dias de teste", len(train), len(test))
    return train, test


def fit_prophet_model(df: pd.DataFrame, interval_width: float = 0.95, **prophet_kwargs) -> Prophet:
    """Ajusta um modelo Prophet sobre a série de treino.

    Args:
        df: DataFrame de treino, colunas `ds` e `y`.
        interval_width: Largura do intervalo de incerteza (ex.: 0.95 = 95%).
        **prophet_kwargs: Argumentos adicionais repassados ao construtor do Prophet
            (ex.: `yearly_seasonality`, `weekly_seasonality`).

    Returns:
        Instância de `Prophet` já ajustada (`.fit()` chamado).
    """
    model = Prophet(interval_width=interval_width, **prophet_kwargs)
    model.fit(df)
    return model


def generate_forecast(model: Prophet, df: pd.DataFrame) -> pd.DataFrame:
    """Gera previsões (com intervalo de incerteza) para as datas de `df`.

    Args:
        model: Modelo Prophet já ajustado.
        df: DataFrame com a coluna `ds` (datas para prever; pode cobrir treino+teste).

    Returns:
        DataFrame com colunas `ds`, `yhat`, `yhat_lower`, `yhat_upper`.
    """
    raw_forecast = model.predict(df[["ds"]])
    return raw_forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
