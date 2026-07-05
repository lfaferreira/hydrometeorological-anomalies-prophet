"""Harmonização de múltiplas fontes de precipitação em uma única série diária."""

import logging
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def harmonize_sources(sources: Dict[str, pd.DataFrame], priority: List[str]) -> pd.DataFrame:
    """Combina séries (ds, y) de múltiplas fontes, respeitando uma ordem de prioridade.

    Para cada data, usa o valor da primeira fonte da lista `priority` que não for NaN.

    Args:
        sources: Mapa nome_da_fonte -> DataFrame com colunas `ds`, `y`.
        priority: Ordem de preferência das fontes (mais confiável primeiro).

    Returns:
        DataFrame com colunas `ds`, `y`, `source` (nome da fonte efetivamente usada).
    """
    indexed = {name: df.set_index("ds")["y"] for name, df in sources.items()}
    all_dates = sorted(set().union(*(s.index for s in indexed.values())))

    rows = []
    for date in all_dates:
        chosen_source, chosen_value = None, None
        for name in priority:
            series = indexed.get(name)
            if series is not None and date in series.index and pd.notna(series.loc[date]):
                chosen_source, chosen_value = name, series.loc[date]
                break
        rows.append({"ds": date, "y": chosen_value, "source": chosen_source})

    result = pd.DataFrame(rows)
    logger.info(
        "Harmonizadas %d fontes em %d dias; %d dias sem nenhuma fonte válida",
        len(sources), len(result), result["y"].isna().sum(),
    )
    return result
