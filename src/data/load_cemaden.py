"""Carregamento de exportações manuais de dados pluviométricos do CEMADEN.

O CEMADEN não oferece uma API pública estável para consumo programático; os dados
são obtidos via exportação manual do portal (http://www2.cemaden.gov.br) em CSV
com colunas `codEstacao`, `municipio`, `datahora` e `valorMedida` (mm, por leitura,
tipicamente a cada 10-60 min ou agregada por período conforme a exportação).
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_cemaden_csv(path: Path) -> pd.DataFrame:
    """Lê um CSV exportado do portal do CEMADEN e agrega para total diário.

    Args:
        path: Caminho do CSV exportado (separador ';', coluna `datahora` e `valorMedida`).

    Returns:
        DataFrame no formato Prophet (ds, y), com y = soma diária de `valorMedida`.
    """
    logger.info("Carregando export do CEMADEN: %s", path)
    df = pd.read_csv(path, sep=";")
    df["datahora"] = pd.to_datetime(df["datahora"])
    df["ds"] = df["datahora"].dt.floor("D")
    daily = df.groupby("ds", as_index=False)["valorMedida"].sum()
    daily = daily.rename(columns={"valorMedida": "y"})
    return daily[["ds", "y"]]
