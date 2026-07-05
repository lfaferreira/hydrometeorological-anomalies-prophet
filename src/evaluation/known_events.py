"""Eventos hidrometeorológicos extremos historicamente documentados na Região
Metropolitana do Recife (RMR), usados como ground truth para validar as
anomalias detectadas pelo Prophet.

Fonte: docs/apac_metodologia.md (eventos de 25 e 28 de maio de 2022, Silva et al.,
2023). Escopo geográfico deste plano é exclusivamente a RMR — nenhum evento de
outra região deve ser adicionado aqui.
"""

from typing import List, TypedDict


class ExtremeEvent(TypedDict):
    name: str
    region: str
    start_date: str
    end_date: str
    source: str


KNOWN_EXTREME_EVENTS: List[ExtremeEvent] = [
    {
        "name": "Chuvas extremas de 25 de maio de 2022",
        "region": "rmr",
        "start_date": "2022-05-23",
        "end_date": "2022-05-25",
        "source": "Silva et al., 2023 (via docs/apac_metodologia.md, seção 17)",
    },
    {
        "name": "Chuvas extremas de 28 de maio de 2022",
        "region": "rmr",
        "start_date": "2022-05-27",
        "end_date": "2022-05-29",
        "source": "Silva et al., 2023 (via docs/apac_metodologia.md, seção 18)",
    },
]
