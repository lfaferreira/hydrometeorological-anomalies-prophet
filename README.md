# hydrometeorological-anomalies-prophet

TCC (MBA Data Science e Analytics — USP/ESALQ): detecção de anomalias em séries
hidrometeorológicas com Prophet, aplicada a eventos extremos de inundação urbana no Brasil.

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