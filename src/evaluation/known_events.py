"""Eventos hidrometeorológicos extremos historicamente documentados na Região
Metropolitana do Recife (RMR), usados como ground truth para validar as
anomalias detectadas pelo Prophet.

Fontes:
- docs/apac_metodologia.md (eventos de 25 e 28 de maio de 2022, Silva et al., 2023).
- Anjos et al., 2024 — "Resgate histórico dos eventos extremos de precipitação e
  seus impactos no município do Recife-PE", Revista Brasileira de Climatologia,
  v. 34, jan./jun. 2024, DOI: 10.55761/abclima.v34i20.16937. Artigo consultado na
  íntegra (PDF obtido em https://ojs.ufgd.edu.br/rbclima/article/view/16937). Os
  quatro maiores eventos diários de chuva da série histórica do INMET (1962-2021)
  para a estação da Várzea, Recife, estão descritos na Tabela 1 e no Quadro 1 do
  artigo; os episódios de 30/05/1966 e 19/07/1975 são citados no texto (seção de
  Resultados e Discussões) como eventos de grande impacto na memória da população,
  com registro fotográfico e documental (jornais da Hemeroteca Digital Brasil).

Escopo geográfico deste plano é exclusivamente a RMR — nenhum evento de outra
região deve ser adicionado aqui.
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
    {
        "name": "Chuvas extremas de 12 de junho de 1965",
        "region": "rmr",
        "start_date": "1965-06-12",
        "end_date": "1965-06-13",
        "source": (
            "Anjos et al., 2024 (Tabela 1 / Quadro 1) — maior registro diário de "
            "176,4 mm na estação INMET da Várzea; 2 mortes e mais de 300 mil "
            "desabrigados em Recife, segundo Diário de Pernambuco, 13/06/1965"
        ),
    },
    {
        "name": "Cheia do Rio Beberibe de 11 de agosto de 1970",
        "region": "rmr",
        "start_date": "1970-08-10",
        "end_date": "1970-08-11",
        "source": (
            "Anjos et al., 2024 (Tabela 1 / Quadro 1) — maior registro diário da "
            "série histórica INMET 1962-2021 (335,8 mm; 151,7 mm entre 18h de "
            "10/08 e 14h30 de 11/08); 84 a 96 mortos e mais de 15 mil "
            "desabrigados em Recife, segundo Diário de Pernambuco, 12/08/1970"
        ),
    },
    {
        "name": "Enchente de 19 de julho de 1975",
        "region": "rmr",
        "start_date": "1975-07-18",
        "end_date": "1975-07-19",
        "source": (
            "Anjos et al., 2024 (Resultados e Discussões, Figura 7) — 80% da "
            "cidade coberta pelas águas e mais de 50 mortos, segundo Diário de "
            "Pernambuco, 18-19/07/1975; nota: evento de impacto humano/"
            "hidrológico, não necessariamente com totais diários de chuva "
            "excepcionais comparados aos demais eventos da Tabela 1"
        ),
    },
    {
        "name": "Chuvas extremas de 24 de maio de 1986",
        "region": "rmr",
        "start_date": "1986-05-24",
        "end_date": "1986-05-24",
        "source": (
            "Anjos et al., 2024 (Tabela 1 / Quadro 1) — registro diário de "
            "235 mm na estação INMET da Várzea; alagamentos nos bairros de "
            "Boa Viagem e no Centro do Recife, segundo Diário de Pernambuco, "
            "24/05/1986"
        ),
    },
    {
        "name": "Chuvas extremas de 1 de agosto de 2000",
        "region": "rmr",
        "start_date": "2000-07-30",
        "end_date": "2000-08-01",
        "source": (
            "Anjos et al., 2024 (Tabela 1 / Quadro 1) — registro diário de "
            "185,9 mm em 01/08 (mais de 300 mm acumulados em 3 dias a partir de "
            "30/07); 22 mortos, 100 feridos, mais de 60 mil desabrigados e mais "
            "de 100 deslizamentos de barreiras na RMR"
        ),
    },
    {
        "name": "Enchente de 30 de maio de 1966",
        "region": "rmr",
        "start_date": "1966-05-30",
        "end_date": "1966-05-30",
        "source": (
            "Anjos et al., 2024 (Resultados e Discussões, Figura 7A) — citado "
            "como um dos episódios de grande impacto na memória da população "
            "recifense, com registro fotográfico da Avenida Caxangá tomada "
            "pelas águas; nota: evento de impacto humano/hidrológico, não "
            "necessariamente com totais diários de chuva excepcionais comparados "
            "aos demais eventos da Tabela 1"
        ),
    },
]
