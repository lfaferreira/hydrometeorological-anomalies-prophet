"""Download e parsing de dados diários de estações automáticas do INMET.

API pública (documentada/assumida): https://apitempo.inmet.gov.br/estacao/dados/{inicio}/{fim}/{codigo}
Formato de resposta esperado (a reconfirmar antes de uso em produção): lista de
dicionários com, entre outros campos, `DT_MEDICAO` (data, "YYYY-MM-DD") e `CHUVA`
(precipitação acumulada do dia, em mm, como string ou null).

ATENÇÃO (validação manual feita em 2026-07-04, ver task-2.1-report.md): a rota
acima retorna 404 "E_ROUTE_NOT_FOUND" na API real. A rota equivalente encontrada,
`/token/estacao/dados/{inicio}/{fim}/{codigo}`, existe mas responde
"CHAVE INVÁLIDA!" sem uma chave de API registrada no portal do INMET — ou seja,
o endpoint aparentemente passou a exigir autenticação por token que este projeto
ainda não possui. O código abaixo mantém o contrato assumido no brief da tarefa
(`parse_inmet_response` validado com dados sintéticos), mas `fetch_inmet_station`
NÃO foi validado contra a API real e não deve ser usado para produzir dados do
TCC sem antes: (1) obter um token válido junto ao INMET e (2) confirmar a URL e
o formato de resposta corretos, repetindo os Steps 1-4 do brief se necessário.
"""

import logging
from typing import List, Dict, Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)

INMET_BASE_URL = "https://apitempo.inmet.gov.br/estacao/dados"


def parse_inmet_response(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Converte a resposta bruta da API do INMET para o formato Prophet (ds, y).

    Args:
        records: Lista de registros diários retornados pela API.

    Returns:
        DataFrame com colunas `ds` (datetime) e `y` (float, mm, pode conter NaN).
    """
    df = pd.DataFrame(records)
    df["ds"] = pd.to_datetime(df["DT_MEDICAO"])
    df["y"] = pd.to_numeric(df["CHUVA"], errors="coerce")
    return df[["ds", "y"]].sort_values("ds").reset_index(drop=True)


def fetch_inmet_station(codigo: str, start: str, end: str) -> pd.DataFrame:
    """Baixa e converte o histórico diário de uma estação INMET.

    Args:
        codigo: Código OMM da estação (ex.: "A301" para Recife).
        start: Data inicial, formato "YYYY-MM-DD".
        end: Data final, formato "YYYY-MM-DD".

    Returns:
        DataFrame no formato Prophet (ds, y).

    Nota:
        Ver aviso no topo do módulo: esta rota ainda não foi validada com
        sucesso contra a API real do INMET (endpoint aparentemente exige
        token de autenticação não disponível neste projeto até o momento).
    """
    url = f"{INMET_BASE_URL}/{start}/{end}/{codigo}"
    logger.info("Baixando dados INMET da estação %s (%s a %s)", codigo, start, end)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return parse_inmet_response(response.json())
