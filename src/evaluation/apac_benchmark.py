"""Classificação de chuva diária segundo os limiares operacionais da APAC (matriz
resumida do site oficial, ver docs/apac_metodologia.md, seção 4.2), usada como
benchmark externo para as anomalias detectadas pelo Prophet.

Limiares (fonte: Matriz Resumida de critérios para Aviso Meteorológico da APAC):
    - Observação: chuva > 30 mm
    - Atenção: chuva > 50 mm
    - Alerta: chuva próxima ou acima de 100 mm

A fonte documenta uma lacuna matemática em exatamente 100 mm (não coberta por
nenhum intervalo no artigo original). Aqui, por decisão de implementação (não
extraída da fonte), 100 mm exato é classificado como "alerta".
"""

import pandas as pd

OBSERVACAO_THRESHOLD_MM = 30.0
ATENCAO_THRESHOLD_MM = 50.0
ALERTA_THRESHOLD_MM = 100.0


def classify_apac_level(y: float) -> str:
    """Classifica um valor diário de chuva (mm) segundo os limiares da APAC.

    Args:
        y: Precipitação diária, em mm.

    Returns:
        Um de `"sem_aviso"`, `"observacao"`, `"atencao"`, `"alerta"`.
    """
    if y >= ALERTA_THRESHOLD_MM:
        return "alerta"
    if y > ATENCAO_THRESHOLD_MM:
        return "atencao"
    if y > OBSERVACAO_THRESHOLD_MM:
        return "observacao"
    return "sem_aviso"


def compare_with_prophet(flagged: pd.DataFrame) -> pd.DataFrame:
    """Adiciona a classificação da APAC ao DataFrame de anomalias do Prophet.

    Args:
        flagged: DataFrame com pelo menos as colunas `y` e `is_anomaly` (saída de
            `src.models.anomaly_detection.flag_anomalies`).

    Returns:
        Cópia de `flagged` com a coluna adicional `apac_level`.
    """
    result = flagged.copy()
    result["apac_level"] = result["y"].apply(classify_apac_level)
    return result
