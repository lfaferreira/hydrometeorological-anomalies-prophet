# hydrometeorological-anomalies-prophet

TCC (MBA Data Science e Analytics — USP/ESALQ). Objetivo congelado (ver `docs/escopo_e_limitacoes.md`): avaliar se um modelo Prophet é capaz de identificar retrospectivamente anomalias de precipitação média diária na Região Metropolitana do Recife (RMR), comparando seu desempenho com métodos climatológicos simples e com eventos extremos documentados

Este projeto **não** prevê chuva, **não** emite alerta antecipado e **não**
modela risco de inundação — ver
[`docs/escopo_e_limitacoes.md`](docs/escopo_e_limitacoes.md) para o escopo
completo e as limitações conhecidas.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pipeline

1. `python src/data/download.py` — baixa precipitação ERA5-Land (CDS) em `dados/raw/`.
2. `python src/data/preprocess.py` — gera série diária agregada em `dados/processed/`.
3. `notebooks/01_pre_processing_data.ipynb` — EDA.
4. `notebooks/02_prophet_modeling.ipynb` — modelagem Prophet e detecção de anomalias.
5. `notebooks/03_validation.ipynb` — validação contra eventos históricos e limiares da APAC.

## Testes

```bash
.venv/bin/pytest tests/ -v
```