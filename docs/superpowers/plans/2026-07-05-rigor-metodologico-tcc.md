# Aumento de Rigor Metodológico do TCC "Detecção de Anomalias Hidrometeorológicas com Prophet" — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir os riscos metodológicos e de engenharia identificados na anamnese crítica de 2026-07-05 (ver conversa/relatório associado) sem alterar o método central do TCC — detecção de anomalias hidrometeorológicas na RMR via intervalo de incerteza do Prophet, validada contra eventos históricos e limiares da APAC. Este plano **adiciona rigor** (reprodutibilidade, baselines de comparação, validação cruzada temporal, diagnóstico de calibração, honestidade estatística sobre o tamanho da amostra de eventos, validação cruzada de fonte de dados) e **não substitui** a abordagem já implementada pelo plano anterior (`docs/superpowers/plans/2026-07-04-conclusao-tcc-prophet.md`, Features 1-6, já concluído).

**Architecture:** Continuação do mesmo pipeline modular `src/data` → `src/models` → `src/evaluation`, consumido por notebooks apenas para orquestração/visualização. Toda lógica nova é testável via `pytest` antes de qualquer célula de notebook a consumir. Nenhum módulo novo dependende de dado externo não disponível no ambiente (ERA5-Land já baixado, fixture do CEMADEN já existente); a única exceção é a Task 12.1, que é pesquisa bibliográfica manual, não codificável por um agente.

**Tech Stack:** Mesmo do plano anterior (Python 3.12, pandas, xarray, prophet + cmdstanpy, statsmodels, scipy, pytest) — **nenhuma dependência nova é necessária além das já presentes em `requirements.txt`**, com exceção de `requests`, `ipykernel` e `nbformat` (Task 7.3), que já estão instaladas no `.venv` mas nunca foram declaradas.

## Global Constraints

- **Escopo geográfico permanece exclusivamente a RMR.** Nenhuma task deste plano introduz outra região — mesma restrição do plano anterior (ver `src/evaluation/known_events.py`, `REGION_FILES` em `src/run_pipeline.py`).
- **Não fabricar dados históricos.** Qualquer evento novo adicionado a `KNOWN_EXTREME_EVENTS` (Task 12.1) precisa de fonte bibliográfica real e verificável (Defesa Civil-PE, CEMADEN, INMET/BDMEP, artigos científicos, arquivo de jornal). Um agente autônomo não deve inventar eventos ou datas — a Task 12.1 é explicitamente marcada como não-codável e requer pausa para pesquisa humana.
- **Reprodutibilidade por padrão.** Toda chamada a `fit_prophet_model`/`generate_forecast` cujo resultado alimente números citados no texto do TCC (notebooks 02, 03, `run_pipeline.py`) deve passar `seed` explicitamente (Task 7.1). Não é aceitável reportar uma métrica no texto do TCC sem que ela seja reprodutível ao reexecutar o notebook.
- **Não apagar nem reexecutar `dados/raw/` (8,6 GB, ERA5-Land já baixado).** A Task 8.1 corrige `src/data/download.py` prospectivamente (para reexecuções futuras ou expansão do período), mas não exige novo download nem invalida `dados/processed/serie_prophet_rmr_2020_2025.csv` já commitado.
- Ambiente: `.venv` na raiz do projeto (`/mnt/c/Users/lucca/development/projects/tcc/tcc_mba/hydrometeorological-anomalies-prophet/.venv`), Python 3.12. **Nota:** `.venv/bin/jupyter-execute` está com um shebang quebrado (aponta para um worktree já removido) — não usar esse binário; use `nbclient`/`nbformat` importados diretamente em Python (ver Tasks 7.2, 9.4, 10.3, 11.3, 13.2), que funcionam normalmente.
- Toda dependência nova vai em `requirements.txt` — nunca `pip install` sem registrar.
- Formato canônico `ds`/`y` mantido em toda função nova.
- Testes novos espelham a estrutura de `src/` em `tests/`, com fixtures sintéticas pequenas (reaproveitar `tests/conftest.py`: `tiny_precip_dataset`, `tiny_prophet_df`) — nunca dados reais de `dados/raw/`.
- Commits pequenos e frequentes, um por tarefa concluída.

---

## Feature 7 — Fundação de reprodutibilidade e empacotamento

Sem isso, nenhuma métrica reportada no texto do TCC é garantidamente reproduzível, e o projeto não instala de forma limpa em uma máquina nova — pré-requisito para qualquer outra feature deste plano que gere números citáveis.

### Task 7.1: Fixar seed determinística no ajuste e na previsão do Prophet

O Prophet usa duas fontes de aleatoriedade independentes: o otimizador MAP do `cmdstanpy` (controlado por `model.fit(df, seed=...)`) e a simulação do intervalo de incerteza em `Prophet.sample_model`, que usa `np.random.normal` diretamente — **não** é coberta pelo `seed` do `cmdstanpy`. Fixar só uma das duas ainda deixa `yhat_lower`/`yhat_upper` (e portanto quais dias são marcados como anomalia) não-reprodutíveis. Isso foi confirmado empiricamente: com o mesmo `seed` de fit, `yhat` é idêntico entre execuções, mas `yhat_lower`/`yhat_upper` variam — e só ficam idênticos fixando também `np.random.seed(seed)` antes de `model.predict(...)`.

**Files:**
- Modify: `src/models/prophet_model.py`
- Test: `tests/models/test_prophet_model.py`

**Interfaces:**
- Modifica: `fit_prophet_model(df, interval_width=0.95, seed: Optional[int] = None, **prophet_kwargs) -> Prophet`
- Modifica: `generate_forecast(model, df, seed: Optional[int] = None) -> pd.DataFrame`
- Consumido por: `src/run_pipeline.py`, `src/evaluation/sensitivity.py`, `src/evaluation/backtesting.py` (Task 10.2) — todos devem passar `seed` explícito ao chamar essas duas funções para números que vão ao texto do TCC.

- [ ] **Step 1: Escrever o teste de reprodutibilidade**

Adicione ao final de `tests/models/test_prophet_model.py`:

```python
def test_fit_and_forecast_are_reproducible_with_same_seed(tiny_prophet_df):
    from src.models.prophet_model import generate_forecast

    model_a = fit_prophet_model(tiny_prophet_df, seed=42)
    forecast_a = generate_forecast(model_a, tiny_prophet_df[["ds"]], seed=42)

    model_b = fit_prophet_model(tiny_prophet_df, seed=42)
    forecast_b = generate_forecast(model_b, tiny_prophet_df[["ds"]], seed=42)

    pd.testing.assert_frame_equal(forecast_a, forecast_b)


def test_forecast_without_seed_is_not_guaranteed_reproducible_but_runs(tiny_prophet_df):
    model = fit_prophet_model(tiny_prophet_df)
    forecast = generate_forecast(model, tiny_prophet_df[["ds"]])

    assert len(forecast) == len(tiny_prophet_df)
```

- [ ] **Step 2: Rodar e confirmar falha no primeiro teste (assinatura ainda não aceita `seed`)**

```bash
.venv/bin/python -m pytest tests/models/test_prophet_model.py -v
```
Expected: `TypeError: fit_prophet_model() got an unexpected keyword argument 'seed'`.

- [ ] **Step 3: Adicionar o parâmetro `seed` a `fit_prophet_model` e `generate_forecast`**

Em `src/models/prophet_model.py`, adicione `Optional` e `numpy` aos imports e ajuste as duas funções:

```python
"""Ajuste do modelo Prophet sobre séries diárias de precipitação."""

import logging
from typing import Optional, Tuple

import numpy as np
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


def fit_prophet_model(
    df: pd.DataFrame,
    interval_width: float = 0.95,
    seed: Optional[int] = None,
    **prophet_kwargs,
) -> Prophet:
    """Ajusta um modelo Prophet sobre a série de treino.

    Args:
        df: DataFrame de treino, colunas `ds` e `y`.
        interval_width: Largura do intervalo de incerteza (ex.: 0.95 = 95%).
        seed: Semente do otimizador MAP do `cmdstanpy`. Necessária para que o
            ajuste (`model.params`) seja reproduzível entre execuções — mas
            não é suficiente sozinha: ver o parâmetro `seed` de
            `generate_forecast` para a semente que cobre a simulação do
            intervalo de incerteza.
        **prophet_kwargs: Argumentos adicionais repassados ao construtor do Prophet
            (ex.: `yearly_seasonality`, `weekly_seasonality`).

    Returns:
        Instância de `Prophet` já ajustada (`.fit()` chamado).
    """
    model = Prophet(interval_width=interval_width, **prophet_kwargs)
    if seed is not None:
        model.fit(df, seed=seed)
    else:
        model.fit(df)
    return model


def generate_forecast(model: Prophet, df: pd.DataFrame, seed: Optional[int] = None) -> pd.DataFrame:
    """Gera previsões (com intervalo de incerteza) para as datas de `df`.

    Args:
        model: Modelo Prophet já ajustado.
        df: DataFrame com a coluna `ds` (datas para prever; pode cobrir treino+teste).
        seed: Semente do gerador de números aleatórios do NumPy usado internamente
            pelo Prophet (`sample_model`) para simular `yhat_lower`/`yhat_upper`.
            O `seed` passado a `fit_prophet_model` NÃO cobre esta etapa — sem
            fixar esta semente também, o intervalo de incerteza (e portanto
            quais dias são marcados como anomalia) varia a cada execução mesmo
            com o mesmo `seed` de ajuste.

    Returns:
        DataFrame com colunas `ds`, `yhat`, `yhat_lower`, `yhat_upper`.
    """
    if seed is not None:
        np.random.seed(seed)
    raw_forecast = model.predict(df[["ds"]])
    return raw_forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/models/test_prophet_model.py -v
```
Expected: `5 passed`.

- [ ] **Step 5: Propagar `seed=42` explícito em `src/run_pipeline.py`**

Em `src/run_pipeline.py`, altere:

```python
    model = fit_prophet_model(train)
    forecast = generate_forecast(model, df[["ds"]])
```

para:

```python
    model = fit_prophet_model(train, seed=42)
    forecast = generate_forecast(model, df[["ds"]], seed=42)
```

- [ ] **Step 6: Rodar a suíte completa e confirmar que nada quebrou**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: todos os testes passam (a Task 6.1 do plano anterior já usa `monkeypatch` para `load_processed_series`, então não é afetada pelo `seed`).

- [ ] **Step 7: Commit**

```bash
git add src/models/prophet_model.py tests/models/test_prophet_model.py src/run_pipeline.py
git commit -m "fix: fixar seed do Prophet (fit + simulacao de incerteza) para reprodutibilidade"
```

### Task 7.2: Corrigir caminho absoluto hardcoded no notebook 01

`notebooks/01_pre_processing_data.ipynb` carrega o CSV com um caminho absoluto (`/home/ubuntu/dev/projects/tcc/...`) que nem sequer corresponde ao caminho real do projeto (`/mnt/c/Users/lucca/development/projects/tcc/...`, ver Global Constraints). Os notebooks 02 e 03 já usam o padrão correto (`PROJECT_ROOT` calculado em runtime); esta task alinha o notebook 01 ao mesmo padrão.

**Files:**
- Modify: `notebooks/01_pre_processing_data.ipynb`

**Interfaces:**
- Nenhuma interface de `src/` — edição de notebook via `nbformat`.

- [ ] **Step 1: Confirmar o conteúdo atual das células-alvo**

```bash
.venv/bin/python -c "
import json
nb = json.load(open('notebooks/01_pre_processing_data.ipynb'))
print(repr(''.join(nb['cells'][2]['source'])))
print('---')
print(repr(''.join(nb['cells'][6]['source'])))
"
```
Expected: a célula 2 termina em `from statsmodels.tsa.seasonal import seasonal_decompose` e a célula 6 é `df_raw = pd.read_csv("/home/ubuntu/dev/projects/tcc/tcc_mba/hydrometeorological-anomalies-prophet/dados/processed/serie_prophet_rmr_2020_2025.csv")`. Se o conteúdo divergir disso, pare e ajuste os índices/strings do Step 2 antes de prosseguir.

- [ ] **Step 2: Corrigir as duas células via `nbformat`**

```bash
.venv/bin/python - <<'EOF'
import nbformat

path = "notebooks/01_pre_processing_data.ipynb"
nb = nbformat.read(path, as_version=4)

OLD_IMPORTS = (
    "# General Libs\n"
    "import numpy as np\n"
    "import pandas as pd\n"
    "import seaborn as sns\n"
    "from scipy import stats\n"
    "import matplotlib.pyplot as plt\n"
    "\n"
    "# Configs libs\n"
    "import ipytest\n"
    "import warnings\n"
    "from IPython.display import display\n"
    "\n"
    "# Others\n"
    "from statsmodels.tsa.seasonal import seasonal_decompose"
)
NEW_IMPORTS = (
    "# General Libs\n"
    "import sys\n"
    "from pathlib import Path\n"
    "\n"
    "import numpy as np\n"
    "import pandas as pd\n"
    "import seaborn as sns\n"
    "from scipy import stats\n"
    "import matplotlib.pyplot as plt\n"
    "\n"
    "# Configs libs\n"
    "import ipytest\n"
    "import warnings\n"
    "from IPython.display import display\n"
    "\n"
    "# Others\n"
    "from statsmodels.tsa.seasonal import seasonal_decompose\n"
    "\n"
    "# Torna o pacote `src` importavel independente do diretorio de execucao do kernel\n"
    "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == \"notebooks\" else Path.cwd()\n"
    "if str(PROJECT_ROOT) not in sys.path:\n"
    "    sys.path.append(str(PROJECT_ROOT))"
)

OLD_LOAD = (
    'df_raw = pd.read_csv("/home/ubuntu/dev/projects/tcc/tcc_mba/'
    'hydrometeorological-anomalies-prophet/dados/processed/serie_prophet_rmr_2020_2025.csv")'
)
NEW_LOAD = 'df_raw = pd.read_csv(PROJECT_ROOT / "dados" / "processed" / "serie_prophet_rmr_2020_2025.csv")'

replaced = {"imports": False, "load": False}
for cell in nb.cells:
    if cell.cell_type != "code":
        continue
    source = "".join(cell.source) if isinstance(cell.source, list) else cell.source
    if source.strip() == OLD_IMPORTS.strip():
        cell.source = NEW_IMPORTS
        replaced["imports"] = True
    elif source.strip() == OLD_LOAD.strip():
        cell.source = NEW_LOAD
        replaced["load"] = True

assert all(replaced.values()), f"Celula(s) nao encontrada(s): {replaced}"
nbformat.write(nb, path)
print("OK:", replaced)
EOF
```
Expected: `OK: {'imports': True, 'load': True}`.

- [ ] **Step 3: Confirmar que o notebook ainda é um JSON válido e executa até a célula corrigida**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

path = "notebooks/01_pre_processing_data.ipynb"
nb = nbformat.read(path, as_version=4)
client = NotebookClient(nb, timeout=300, kernel_name="python3")
client.execute()
nbformat.write(nb, path)
print("Notebook 01 executado e salvo com sucesso.")
EOF
```
Expected: `Notebook 01 executado e salvo com sucesso.` (sem exceção). Isso executa o notebook inteiro — se alguma célula gerar erro por motivos não relacionados a esta task (ex.: warning tratado como erro), investigue antes de prosseguir, mas não é esperado dado que a única mudança foi de caminho de arquivo.

- [ ] **Step 4: Commit**

```bash
git add notebooks/01_pre_processing_data.ipynb
git commit -m "fix: substituir caminho absoluto hardcoded do notebook 01 por PROJECT_ROOT"
```

### Task 7.3: Declarar dependências faltantes em `requirements.txt`

`src/data/download_inmet.py` importa `requests`, e os notebooks só rodam porque `ipykernel`/`nbformat` estão instalados no `.venv` — nenhuma das três está em `requirements.txt`. Um `pip install -r requirements.txt` limpo instala um ambiente que não consegue rodar os notebooks nem o cliente INMET (mesmo que este último seja removido na Task 13.3, a dependência já é usada por `tests/data/test_download_inmet.py` até lá).

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Confirmar as versões já instaladas no `.venv`**

```bash
.venv/bin/pip freeze | grep -iE "^(requests|ipykernel|nbformat)=="
```
Expected: `requests==2.33.1`, `ipykernel==7.2.0`, `nbformat==5.10.4` (ou versões próximas — use os valores reais retornados aqui no Step 2, não os desta task, caso divirjam).

- [ ] **Step 2: Adicionar as três linhas a `requirements.txt`**

Acrescente ao final do arquivo (mantendo os valores exatos obtidos no Step 1):

```
requests==2.33.1
ipykernel==7.2.0
nbformat==5.10.4
```

- [ ] **Step 3: Validar instalação limpa em um ambiente novo**

```bash
python3.12 -m venv /tmp/tcc-verify-env-rigor
/tmp/tcc-verify-env-rigor/bin/pip install -r requirements.txt
/tmp/tcc-verify-env-rigor/bin/python -c "import requests, ipykernel, nbformat; print('ok')"
```
Expected: `ok`, sem erro de instalação.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: declarar dependencias requests/ipykernel/nbformat ja usadas mas nao registradas"
```

### Task 7.4: Empacotar `src` como pacote instalável e simplificar imports dos notebooks

Hoje `src` não é um pacote instalável (sem `pyproject.toml`, sem `src/__init__.py`, sem `src/data/__init__.py`) — os imports `from src.X import Y` só funcionam por acidente de o pytest/notebook rodar com a raiz do repo no `sys.path` (nos notebooks, via manipulação manual de `sys.path` célula a célula). Empacotar remove essa fragilidade.

**Files:**
- Create: `pyproject.toml`, `src/__init__.py`, `src/data/__init__.py`
- Modify: `notebooks/02_prophet_modeling.ipynb`, `notebooks/03_validation.ipynb` (remover o bloco de `sys.path.append`, mantendo `PROJECT_ROOT` só para localizar arquivos de dados)

**Interfaces:**
- Nenhuma função nova — mudança de empacotamento/instalação.

- [ ] **Step 1: Criar `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "hydrometeorological-anomalies-prophet"
version = "0.1.0"
description = "TCC MBA Data Science e Analytics (USP/ESALQ): deteccao de anomalias hidrometeorologicas com Prophet na RMR"
requires-python = ">=3.12"

[tool.setuptools.packages.find]
include = ["src*"]
```

- [ ] **Step 2: Criar os `__init__.py` faltantes**

```bash
touch src/__init__.py src/data/__init__.py
```

- [ ] **Step 3: Instalar o pacote em modo editável**

```bash
.venv/bin/pip install -e .
```
Expected: `Successfully installed hydrometeorological-anomalies-prophet-0.1.0`.

- [ ] **Step 4: Verificar que o import funciona a partir de qualquer diretório**

```bash
cd /tmp && /mnt/c/Users/lucca/development/projects/tcc/tcc_mba/hydrometeorological-anomalies-prophet/.venv/bin/python -c "
from src.models.prophet_model import fit_prophet_model
from src.data.preprocess import deaccumulate_precipitation
print('ok')
"
cd /mnt/c/Users/lucca/development/projects/tcc/tcc_mba/hydrometeorological-anomalies-prophet
```
Expected: `ok`, executado a partir de `/tmp` (fora da raiz do projeto).

- [ ] **Step 5: Rodar a suíte de testes para confirmar que nada quebrou com o pacote instalado**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: todos os testes continuam passando.

- [ ] **Step 6: Simplificar o bloco de imports dos notebooks 02 e 03 (remover `sys.path.append`, manter `PROJECT_ROOT`)**

```bash
.venv/bin/python - <<'EOF'
import nbformat

OLD_BLOCK = (
    "import sys\n"
    "import warnings\n"
    "from pathlib import Path\n"
    "\n"
    "warnings.filterwarnings(\"ignore\")\n"
    "\n"
    "import numpy as np\n"
    "import pandas as pd\n"
    "import matplotlib.pyplot as plt\n"
    "\n"
    "# Torna o pacote `src` importável independente do diretório de execução do kernel\n"
    "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == \"notebooks\" else Path.cwd()\n"
    "if str(PROJECT_ROOT) not in sys.path:\n"
    "    sys.path.append(str(PROJECT_ROOT))"
)

NEW_BLOCK = (
    "import warnings\n"
    "from pathlib import Path\n"
    "\n"
    "warnings.filterwarnings(\"ignore\")\n"
    "\n"
    "import numpy as np\n"
    "import pandas as pd\n"
    "import matplotlib.pyplot as plt\n"
    "\n"
    "# `src` é um pacote instalado (pip install -e .); PROJECT_ROOT só é usado\n"
    "# para localizar arquivos de dados em `dados/`, não mais para sys.path.\n"
    "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == \"notebooks\" else Path.cwd()"
)

for path in ["notebooks/02_prophet_modeling.ipynb", "notebooks/03_validation.ipynb"]:
    nb = nbformat.read(path, as_version=4)
    found = False
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        source = "".join(cell.source) if isinstance(cell.source, list) else cell.source
        if source.strip() == OLD_BLOCK.strip():
            cell.source = NEW_BLOCK
            found = True
            break
    assert found, f"Bloco de imports nao encontrado em {path}"
    nbformat.write(nb, path)
    print(f"OK: {path}")
EOF
```
Expected: `OK: notebooks/02_prophet_modeling.ipynb` e `OK: notebooks/03_validation.ipynb`.

- [ ] **Step 7: Executar os dois notebooks ponta-a-ponta para confirmar que os imports simplificados funcionam**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

for path in ["notebooks/02_prophet_modeling.ipynb", "notebooks/03_validation.ipynb"]:
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="python3")
    client.execute()
    nbformat.write(nb, path)
    print(f"Executado e salvo: {path}")
EOF
```
Expected: ambos executam sem exceção.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/__init__.py src/data/__init__.py notebooks/02_prophet_modeling.ipynb notebooks/03_validation.ipynb
git commit -m "feat: empacotar src como pacote instalavel e remover sys.path hack dos notebooks"
```

---

## Feature 8 — Eficiência do download de dados brutos

### Task 8.1: Restringir a área de download do ERA5-Land à bounding box da RMR

`src/data/download.py` baixa `AREA_BRAZIL` (todo o Brasil, hora a hora, 6 anos — os 8,6 GB já em `dados/raw/`), mas `src/data/preprocess.py` só usa uma caixa de ~40x40 km da RMR. Esta correção é **prospectiva**: não reprocessa nem apaga os dados já baixados, apenas evita o mesmo desperdício em reexecuções futuras (ex.: expansão de período, nova instalação do projeto).

**Files:**
- Modify: `src/data/download.py`
- Test: `tests/data/test_download.py`

**Interfaces:**
- Modifica: constante `AREA_BRAZIL` → `AREA_RMR` (bounding box da RMR com margem de 0,5° para não cortar pixels na borda do recorte de `preprocess.py`).

- [ ] **Step 1: Escrever o teste de coerência entre a área de download e o filtro de `preprocess.py`**

Adicione ao final de `tests/data/test_download.py`:

```python
import inspect

from src.data.download import AREA_RMR
from src.data.preprocess import main as preprocess_main


def test_area_rmr_covers_preprocess_bounding_box():
    defaults = inspect.signature(preprocess_main).parameters
    lat_north = defaults["lat_north"].default
    lat_south = defaults["lat_south"].default
    lon_west = defaults["lon_west"].default
    lon_east = defaults["lon_east"].default

    north, west, south, east = AREA_RMR  # formato CDS: [Norte, Oeste, Sul, Leste]

    assert north >= lat_north
    assert south <= lat_south
    assert west <= lon_west
    assert east >= lon_east
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/data/test_download.py -v
```
Expected: `ImportError: cannot import name 'AREA_RMR'`.

- [ ] **Step 3: Substituir `AREA_BRAZIL` por `AREA_RMR` em `src/data/download.py`**

Troque:

```python
# Área geográfica: [Norte, Oeste, Sul, Leste] - Brasil
AREA_BRAZIL: List[float] = [5.0, -75.0, -35.0, -34.0]
```

por:

```python
# Área geográfica: [Norte, Oeste, Sul, Leste] - RMR, com margem de 0.5°
# em torno da caixa usada por `src.data.preprocess.main` (lat -7.9/-8.3,
# lon -35.2/-34.8), para garantir que os pixels da borda do recorte não
# sejam cortados por diferenças de alinhamento de grade do ERA5-Land.
AREA_RMR: List[float] = [-7.4, -35.7, -8.8, -34.3]
```

E, dentro de `main()`, troque `area=AREA_BRAZIL` por `area=AREA_RMR`.

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/data/test_download.py -v
```
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/data/download.py tests/data/test_download.py
git commit -m "fix: restringir area de download do ERA5-Land a bounding box da RMR"
```

---

## Feature 9 — Baselines de comparação para a detecção de anomalias

Sem um baseline, não há como argumentar quantitativamente que o Prophet é uma escolha melhor que uma heurística simples — risco direto de banca ("por que não um Z-score?"). Os três baselines abaixo reaproveitam técnicas já usadas como EDA no notebook 01 (Z-score, IQR, resíduo de decomposição), agora formalizadas em `src/` e avaliadas com a mesma `evaluate_anomalies` usada para o Prophet.

### Task 9.1: Detector baseline por Z-score

**Files:**
- Create: `src/models/baselines.py`
- Test: `tests/models/test_baselines.py`

**Interfaces:**
- Produz: `flag_anomalies_zscore(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame`, mesmo contrato de saída de `flag_anomalies` (colunas `ds`, `y`, `is_anomaly`, `severity`), para ser avaliado por `evaluate_anomalies` sem adaptação.

- [ ] **Step 1: Escrever o teste**

```python
# tests/models/test_baselines.py
import pandas as pd
import pytest

from src.models.baselines import flag_anomalies_zscore


def test_flag_anomalies_zscore_marks_extreme_point_only():
    normal_values = [
        5.612, 4.233, 5.125, 4.83, 4.864, 4.935, 4.394, 4.93, 4.74, 5.997,
        5.068, 4.894, 4.916, 4.8, 4.683, 4.883, 5.145, 4.928, 5.287, 4.94,
        5.007, 5.464, 5.164, 4.848, 4.945, 5.162, 5.581, 4.919, 4.927,
    ]
    df = pd.DataFrame({
        "ds": pd.date_range("2022-01-01", periods=30, freq="D"),
        "y": normal_values + [50.0],
    })

    result = flag_anomalies_zscore(df, threshold=3.0)

    assert result["is_anomaly"].tolist() == [False] * 29 + [True]
    assert result["severity"].iloc[-1] > 0
    assert result["severity"].iloc[0] == 0.0
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/models/test_baselines.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.models.baselines'`.

- [ ] **Step 3: Implementar `src/models/baselines.py` (Z-score)**

```python
"""Detectores baseline de anomalias, usados como comparação para o Prophet.

Cada função recebe uma série (ds, y) e devolve o mesmo contrato de
`src.models.anomaly_detection.flag_anomalies`: colunas `ds`, `y`, `is_anomaly`
(bool) e `severity` (float >= 0), para serem avaliadas com a mesma
`src.evaluation.metrics.evaluate_anomalies` usada para o Prophet.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def flag_anomalies_zscore(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    """Marca como anomalia todo ponto com |z-score| acima de `threshold`.

    Args:
        df: DataFrame com colunas `ds`, `y`.
        threshold: Limiar de desvios-padrão (padrão: 3.0).

    Returns:
        Cópia de `df` com colunas adicionais `is_anomaly` e `severity`.
    """
    result = df.copy()
    mean, std = result["y"].mean(), result["y"].std()
    z = (result["y"] - mean) / std
    result["is_anomaly"] = z.abs() > threshold
    result["severity"] = (z.abs() - threshold).clip(lower=0) * std
    logger.info(
        "Z-score: %d anomalias detectadas em %d dias (threshold=%.1f)",
        result["is_anomaly"].sum(), len(result), threshold,
    )
    return result
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/models/test_baselines.py -v
```
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/models/baselines.py tests/models/test_baselines.py
git commit -m "feat: baseline de deteccao de anomalias por z-score"
```

### Task 9.2: Detector baseline por IQR

**Files:**
- Modify: `src/models/baselines.py`
- Test: `tests/models/test_baselines.py`

**Interfaces:**
- Produz: `flag_anomalies_iqr(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame`, mesmo contrato de `flag_anomalies_zscore`. Só marca a cauda superior (precipitação é limitada em zero — mesma justificativa física já usada em `flag_anomalies`).

- [ ] **Step 1: Escrever o teste**

Adicione a `tests/models/test_baselines.py`:

```python
from src.models.baselines import flag_anomalies_iqr


def test_flag_anomalies_iqr_marks_only_upper_tail():
    df = pd.DataFrame({
        "ds": pd.date_range("2022-01-01", periods=8, freq="D"),
        "y": [1.0, 2.0, 2.0, 3.0, 2.0, 3.0, 2.0, 40.0],
    })

    result = flag_anomalies_iqr(df, k=1.5)

    assert result["is_anomaly"].iloc[-1] == True
    assert result["is_anomaly"].iloc[:-1].sum() == 0
    assert result["severity"].iloc[-1] > 0
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/models/test_baselines.py -v
```
Expected: `ImportError: cannot import name 'flag_anomalies_iqr'`.

- [ ] **Step 3: Implementar `flag_anomalies_iqr`**

Adicione ao final de `src/models/baselines.py`:

```python
def flag_anomalies_iqr(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """Marca como anomalia todo ponto acima de `Q3 + k * IQR` (cauda superior).

    Só o limite superior é usado: a precipitação diária é limitada em zero e
    o regime de seca não produz valores "anormalmente baixos" fisicamente
    (mesma justificativa usada em `flag_anomalies` para o Prophet).

    Args:
        df: DataFrame com colunas `ds`, `y`.
        k: Multiplicador do IQR (padrão: 1.5, convenção clássica de Tukey).

    Returns:
        Cópia de `df` com colunas adicionais `is_anomaly` e `severity`.
    """
    result = df.copy()
    q1, q3 = result["y"].quantile(0.25), result["y"].quantile(0.75)
    upper_bound = q3 + k * (q3 - q1)
    result["is_anomaly"] = result["y"] > upper_bound
    result["severity"] = (result["y"] - upper_bound).clip(lower=0)
    logger.info(
        "IQR: %d anomalias detectadas em %d dias (limite=%.2f mm)",
        result["is_anomaly"].sum(), len(result), upper_bound,
    )
    return result
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/models/test_baselines.py -v
```
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/models/baselines.py tests/models/test_baselines.py
git commit -m "feat: baseline de deteccao de anomalias por IQR"
```

### Task 9.3: Detector baseline por resíduo de decomposição STL

**Files:**
- Modify: `src/models/baselines.py`
- Test: `tests/models/test_baselines.py`

**Interfaces:**
- Produz: `flag_anomalies_stl_residual(df: pd.DataFrame, period: int = 365, threshold: float = 3.0) -> pd.DataFrame`, mesmo contrato dos baselines anteriores. Exige `len(df) >= 2 * period` (requisito da própria STL) e série sem gaps de data.

- [ ] **Step 1: Escrever o teste**

Adicione a `tests/models/test_baselines.py`:

```python
from src.models.baselines import flag_anomalies_stl_residual


def test_flag_anomalies_stl_residual_marks_point_off_seasonal_pattern(tiny_prophet_df):
    injected = tiny_prophet_df.copy()
    injected.loc[50, "y"] = injected["y"].max() + 100  # pico artificial fora do padrão sazonal

    result = flag_anomalies_stl_residual(injected, period=10, threshold=3.0)

    injected_date = injected.loc[50, "ds"]
    assert bool(result.loc[result["ds"] == injected_date, "is_anomaly"].iloc[0]) is True
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/models/test_baselines.py -v
```
Expected: `ImportError: cannot import name 'flag_anomalies_stl_residual'`.

- [ ] **Step 3: Implementar `flag_anomalies_stl_residual`**

Adicione `from statsmodels.tsa.seasonal import STL` aos imports de `src/models/baselines.py` e, ao final do arquivo:

```python
def flag_anomalies_stl_residual(df: pd.DataFrame, period: int = 365, threshold: float = 3.0) -> pd.DataFrame:
    """Marca como anomalia todo ponto cujo resíduo da decomposição STL tenha
    |z-score| acima de `threshold` (mesma técnica aplicada como EDA no notebook 01).

    Args:
        df: DataFrame com colunas `ds`, `y`, sem gaps de data (a STL exige
            índice temporal regular) e com pelo menos `2 * period` linhas.
        period: Período sazonal em dias (padrão: 365, ciclo anual — use um
            valor menor em séries curtas de teste, ver `2 * period <= len(df)`).
        threshold: Limiar de desvios-padrão do resíduo (padrão: 3.0).

    Returns:
        Cópia de `df` (ordenada por `ds`) com colunas adicionais `is_anomaly`
        e `severity`.
    """
    result = df.sort_values("ds").reset_index(drop=True).copy()
    indexed = result.set_index("ds")["y"]
    stl_result = STL(indexed, period=period, robust=True).fit()
    resid = stl_result.resid
    z = (resid - resid.mean()) / resid.std()

    result["is_anomaly"] = z.abs().values > threshold
    result["severity"] = ((z.abs() - threshold).clip(lower=0) * resid.std()).values
    logger.info(
        "STL residual: %d anomalias detectadas em %d dias (threshold=%.1f)",
        result["is_anomaly"].sum(), len(result), threshold,
    )
    return result
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/models/test_baselines.py -v
```
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/models/baselines.py tests/models/test_baselines.py
git commit -m "feat: baseline de deteccao de anomalias por residuo de decomposicao STL"
```

### Task 9.4: Notebook 03 — tabela comparativa Prophet vs. baselines

**Files:**
- Modify: `notebooks/03_validation.ipynb`

**Interfaces:**
- Consome: `flag_anomalies_zscore`, `flag_anomalies_iqr`, `flag_anomalies_stl_residual` (Tasks 9.1-9.3), `evaluate_anomalies` (já existente), `flagged` (carregado do notebook 02).

- [ ] **Step 1: Adicionar célula markdown de seção**

```markdown
# 6. Comparação com Baselines Mais Simples

O Prophet é comparado abaixo contra três detectores baseline univariados — Z-score,
IQR (cauda superior) e resíduo de decomposição STL — todos avaliados com a mesma
`evaluate_anomalies` usada para o Prophet (Seção 2), sobre o mesmo catálogo de
eventos conhecidos. Isso permite responder quantitativamente se a complexidade
adicional do Prophet (sazonalidade aprendida, tendência, MCMC/MAP) se traduz em
desempenho de detecção melhor que heurísticas simples de EDA.
```

- [ ] **Step 2: Adicionar célula de código com a comparação**

```python
from src.models.baselines import flag_anomalies_zscore, flag_anomalies_iqr, flag_anomalies_stl_residual

serie = flagged[["ds", "y"]].copy()

baseline_results = {
    "prophet": flagged,
    "zscore": flag_anomalies_zscore(serie),
    "iqr": flag_anomalies_iqr(serie),
    "stl_residual": flag_anomalies_stl_residual(serie, period=365),
}

comparacao = []
for nome, resultado in baseline_results.items():
    metrics = evaluate_anomalies(resultado, KNOWN_EXTREME_EVENTS, tolerance_days=1)
    comparacao.append({"metodo": nome, "n_anomalias": int(resultado["is_anomaly"].sum()), **metrics})

comparacao_df = pd.DataFrame(comparacao).set_index("metodo")
comparacao_df
```

- [ ] **Step 3: Adicionar célula markdown de discussão (preencher após rodar o Step 2)**

```markdown
Preencher esta célula, após rodar a comparação acima, com: qual método teve o
melhor F1; se o Prophet superou os baselines simples e em que medida; e se
algum baseline capturou os dois eventos de maio/2022 que o Prophet não
capturou (23-24/05, ver discussão da Seção 5 do notebook). Reportar os números
reais da tabela `comparacao_df`, não estimativas.
```

- [ ] **Step 4: Executar o notebook ponta-a-ponta e confirmar que a nova seção roda sem erro**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

path = "notebooks/03_validation.ipynb"
nb = nbformat.read(path, as_version=4)
client = NotebookClient(nb, timeout=600, kernel_name="python3")
client.execute()
nbformat.write(nb, path)
print("Notebook 03 executado e salvo com sucesso.")
EOF
```
Expected: `Notebook 03 executado e salvo com sucesso.`

- [ ] **Step 5: Preencher manualmente a célula de discussão do Step 3 com os números reais obtidos**

- [ ] **Step 6: Commit**

```bash
git add notebooks/03_validation.ipynb
git commit -m "feat: comparar Prophet com baselines de z-score, IQR e residuo STL no notebook 03"
```

---

## Feature 10 — Validação cruzada temporal (rolling-origin backtesting)

Um único split treino/teste (últimos 180 dias) não garante que as métricas reportadas sejam estáveis — podem ser um acaso de qual janela caiu no teste. Rolling-origin backtesting roda o pipeline completo em múltiplas origens de treino crescentes, cada uma avaliada **apenas** na sua própria janela de teste (nunca misturando com o treino, ao contrário do `run_full_pipeline` atual — ver Task 11.2 para a discussão dessa mistura).

### Task 10.1: Gerar folds de rolling-origin

**Files:**
- Create: `src/evaluation/backtesting.py`
- Test: `tests/evaluation/test_backtesting.py`

**Interfaces:**
- Produz: `rolling_origin_splits(df: pd.DataFrame, initial_train_days: int, test_size_days: int, step_days: int) -> List[Tuple[pd.DataFrame, pd.DataFrame]]`.

- [ ] **Step 1: Escrever o teste**

```python
# tests/evaluation/test_backtesting.py
from src.evaluation.backtesting import rolling_origin_splits


def test_rolling_origin_splits_generates_expected_number_of_folds(tiny_prophet_df):
    folds = rolling_origin_splits(tiny_prophet_df, initial_train_days=60, test_size_days=10, step_days=10)

    assert len(folds) == 4
    for train, test in folds:
        assert train["ds"].max() < test["ds"].min()
        assert len(test) == 10
    assert [len(train) for train, _ in folds] == [60, 70, 80, 90]
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/evaluation/test_backtesting.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.evaluation.backtesting'`.

- [ ] **Step 3: Implementar `rolling_origin_splits`**

```python
"""Validação cruzada temporal (rolling-origin / backtesting) do pipeline de
detecção de anomalias — mede se as métricas de `evaluate_anomalies` são
estáveis entre diferentes janelas de teste, em vez de depender de um único
split fixo (`train_test_split_temporal`)."""

import logging
from typing import List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def rolling_origin_splits(
    df: pd.DataFrame, initial_train_days: int, test_size_days: int, step_days: int
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """Gera janelas de treino/teste com origem de treino crescente (rolling-origin).

    Cada fold usa todos os dados desde o início da série até um ponto de corte
    crescente como treino, e os `test_size_days` dias seguintes como teste —
    nunca embaralhando a ordem temporal (mesmo princípio de
    `train_test_split_temporal`, repetido em múltiplas origens).

    Args:
        df: DataFrame ordenado por `ds`, colunas `ds` e `y`.
        initial_train_days: Tamanho (em dias) do treino do primeiro fold.
        test_size_days: Tamanho (em dias) da janela de teste de cada fold.
        step_days: Quantos dias a origem de treino avança a cada fold.

    Returns:
        Lista de tuplas `(train_df, test_df)`, uma por fold.
    """
    df_sorted = df.sort_values("ds").reset_index(drop=True)
    n = len(df_sorted)
    folds = []
    train_end = initial_train_days
    while train_end < n:
        test_end = min(train_end + test_size_days, n)
        train = df_sorted.iloc[:train_end].reset_index(drop=True)
        test = df_sorted.iloc[train_end:test_end].reset_index(drop=True)
        if len(test) == 0:
            break
        folds.append((train, test))
        train_end += step_days
    logger.info(
        "Rolling-origin: %d folds gerados (treino inicial=%d dias, passo=%d dias)",
        len(folds), initial_train_days, step_days,
    )
    return folds
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/evaluation/test_backtesting.py -v
```
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/evaluation/backtesting.py tests/evaluation/test_backtesting.py
git commit -m "feat: gerar folds de rolling-origin para validacao cruzada temporal"
```

### Task 10.2: Rodar o pipeline completo em cada fold

**Files:**
- Modify: `src/evaluation/backtesting.py`
- Test: `tests/evaluation/test_backtesting.py`

**Interfaces:**
- Consome: `rolling_origin_splits` (Task 10.1), `fit_prophet_model`, `generate_forecast` (com `seed`, Task 7.1), `flag_anomalies`, `evaluate_anomalies`.
- Produz: `run_rolling_origin_backtest(df, known_events, initial_train_days, test_size_days, step_days, interval_width=0.95, seed=42) -> pd.DataFrame`, uma linha por fold.

- [ ] **Step 1: Escrever o teste**

Adicione a `tests/evaluation/test_backtesting.py`:

```python
from src.evaluation.backtesting import run_rolling_origin_backtest

EVENTS = [
    {"name": "Evento A", "region": "rmr", "start_date": "2020-03-15", "end_date": "2020-03-15", "source": "teste"},
]


def test_run_rolling_origin_backtest_returns_one_row_per_fold(tiny_prophet_df):
    result = run_rolling_origin_backtest(
        tiny_prophet_df, known_events=EVENTS,
        initial_train_days=60, test_size_days=10, step_days=10,
    )

    assert len(result) == 4
    assert {"fold", "train_days", "precision", "recall", "f1", "false_positive_rate"}.issubset(result.columns)
    assert list(result["train_days"]) == [60, 70, 80, 90]
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/evaluation/test_backtesting.py -v
```
Expected: `ImportError: cannot import name 'run_rolling_origin_backtest'`.

- [ ] **Step 3: Implementar `run_rolling_origin_backtest`**

Adicione ao topo de `src/evaluation/backtesting.py` (após os imports existentes):

```python
from src.models.prophet_model import fit_prophet_model, generate_forecast
from src.models.anomaly_detection import flag_anomalies
from src.evaluation.metrics import evaluate_anomalies
```

E, ao final do arquivo:

```python
def run_rolling_origin_backtest(
    df: pd.DataFrame,
    known_events: List[dict],
    initial_train_days: int,
    test_size_days: int,
    step_days: int,
    interval_width: float = 0.95,
    seed: int = 42,
) -> pd.DataFrame:
    """Roda o pipeline completo (ajuste + detecção + avaliação) em cada fold
    de `rolling_origin_splits`, avaliando cada fold **apenas** na sua própria
    janela de teste (nunca no treino usado para ajustar aquele fold).

    Args:
        df: Série completa (ds, y).
        known_events: Eventos conhecidos, no formato de `KNOWN_EXTREME_EVENTS`.
        initial_train_days: Ver `rolling_origin_splits`.
        test_size_days: Ver `rolling_origin_splits`.
        step_days: Ver `rolling_origin_splits`.
        interval_width: Largura do intervalo de incerteza do Prophet.
        seed: Semente fixa (ajuste e simulação de incerteza) para que os folds
            sejam comparáveis entre si sem ruído de aleatoriedade do Prophet.

    Returns:
        DataFrame com uma linha por fold: `fold`, `train_days`, `test_start`,
        `test_end`, `precision`, `recall`, `f1`, `false_positive_rate`.
    """
    folds = rolling_origin_splits(df, initial_train_days, test_size_days, step_days)
    rows = []
    for i, (train, test) in enumerate(folds):
        model = fit_prophet_model(train, interval_width=interval_width, seed=seed)
        forecast = generate_forecast(model, test[["ds"]], seed=seed)
        flagged = flag_anomalies(test, forecast)
        metrics = evaluate_anomalies(flagged, known_events, tolerance_days=1)
        rows.append({
            "fold": i,
            "train_days": len(train),
            "test_start": test["ds"].min(),
            "test_end": test["ds"].max(),
            **metrics,
        })
        logger.info(
            "Fold %d: treino=%d dias, teste=%s a %s -> %s",
            i, len(train), test["ds"].min().date(), test["ds"].max().date(), metrics,
        )

    return pd.DataFrame(rows)
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/evaluation/test_backtesting.py -v
```
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/evaluation/backtesting.py tests/evaluation/test_backtesting.py
git commit -m "feat: rodar pipeline completo por fold de rolling-origin backtesting"
```

### Task 10.3: Notebook 03 — seção de estabilidade entre folds

**Files:**
- Modify: `notebooks/03_validation.ipynb`

**Interfaces:**
- Consome: `run_rolling_origin_backtest` (Task 10.2), `df_raw` (série completa recarregada), `KNOWN_EXTREME_EVENTS`.

- [ ] **Step 1: Adicionar célula markdown de seção**

```markdown
# 7. Estabilidade das Métricas: Validação Cruzada Temporal (Rolling-Origin)

A Seção 2 avalia o Prophet contra um único split treino/teste (últimos 180 dias
de `serie_prophet_rmr_2020_2025.csv`) — não há garantia de que o desempenho
reportado ali seja estável ou um acaso de qual janela caiu no teste. Esta seção
roda o pipeline completo (ajuste + detecção + avaliação) em múltiplas origens de
treino crescentes, cada fold avaliado **apenas** na sua própria janela de teste
(nunca misturando com o treino daquele fold), via
`src.evaluation.backtesting.run_rolling_origin_backtest`.
```

- [ ] **Step 2: Adicionar célula de código**

```python
from src.evaluation.backtesting import run_rolling_origin_backtest

df_completo = pd.read_csv(PROJECT_ROOT / "dados" / "processed" / "serie_prophet_rmr_2020_2025.csv")
df_completo["ds"] = pd.to_datetime(df_completo["ds"])

backtest_df = run_rolling_origin_backtest(
    df_completo,
    known_events=KNOWN_EXTREME_EVENTS,
    initial_train_days=len(df_completo) - 5 * 180,  # 5 folds de 180 dias de teste cada
    test_size_days=180,
    step_days=180,
    seed=42,
)
backtest_df
```

- [ ] **Step 3: Adicionar célula de visualização da estabilidade**

```python
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(backtest_df["fold"], backtest_df["precision"], marker="o", label="precision")
ax.plot(backtest_df["fold"], backtest_df["recall"], marker="o", label="recall")
ax.plot(backtest_df["fold"], backtest_df["f1"], marker="o", label="f1")
ax.set_xlabel("Fold (origem de treino crescente)")
ax.set_ylabel("Métrica")
ax.set_title("Estabilidade das métricas entre folds de rolling-origin backtesting")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()
```

- [ ] **Step 4: Adicionar célula markdown de discussão (preencher após rodar os Steps 2-3)**

```markdown
Preencher esta célula, após rodar o backtesting acima, com: se as métricas
variam muito entre folds (instabilidade) ou são consistentes; se algum fold
específico (ex.: o que inclui maio/2022 no teste) domina o resultado
reportado na Seção 2; e se isso muda a leitura qualitativa da Seção 5 sobre o
desempenho do Prophet. Reportar os números reais de `backtest_df`, não
estimativas. Nota: com poucos eventos conhecidos por fold, algumas linhas de
`backtest_df` terão `recall`/`precision` = 0/0 (sem evento na janela daquele
fold) — não interpretar isso como falha do modelo, apenas ausência de
ground truth naquele recorte temporal.
```

- [ ] **Step 5: Executar o notebook ponta-a-ponta**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

path = "notebooks/03_validation.ipynb"
nb = nbformat.read(path, as_version=4)
client = NotebookClient(nb, timeout=900, kernel_name="python3")
client.execute()
nbformat.write(nb, path)
print("Notebook 03 executado e salvo com sucesso.")
EOF
```
Expected: `Notebook 03 executado e salvo com sucesso.` (pode demorar alguns minutos — 5 ajustes de Prophet).

- [ ] **Step 6: Preencher manualmente a célula de discussão do Step 4 com os números reais**

- [ ] **Step 7: Commit**

```bash
git add notebooks/03_validation.ipynb
git commit -m "feat: validacao cruzada temporal (rolling-origin) no notebook 03"
```

---

## Feature 11 — Diagnóstico de calibração estatística (circularidade do critério de anomalia)

Usar o próprio intervalo de confiança do Prophet como critério de anomalia é parcialmente tautológico: por construção, um modelo bem calibrado já deixa `1 - interval_width` dos pontos fora do intervalo, tenha ou não ocorrido um evento real. Esta feature formaliza essa checagem em vez de deixá-la como discussão puramente qualitativa.

### Task 11.1: Checagem de calibração (taxa observada vs. nominal)

**Files:**
- Create: `src/evaluation/calibration.py`
- Test: `tests/evaluation/test_calibration.py`

**Interfaces:**
- Produz: `check_interval_calibration(flagged: pd.DataFrame, interval_width: float) -> Dict[str, float]`.

- [ ] **Step 1: Escrever o teste**

```python
# tests/evaluation/test_calibration.py
import pandas as pd
import pytest

from src.evaluation.calibration import check_interval_calibration


def test_check_interval_calibration_matches_nominal_rate_when_well_calibrated():
    flagged = pd.DataFrame({
        "ds": pd.date_range("2022-01-01", periods=200, freq="D"),
        "is_anomaly": [i % 20 == 0 for i in range(200)],  # 10/200 = 5% flagged
    })

    result = check_interval_calibration(flagged, interval_width=0.95)

    assert result["n_days"] == 200
    assert result["n_anomalies"] == 10
    assert result["observed_rate"] == pytest.approx(0.05)
    assert result["nominal_rate"] == pytest.approx(0.05)
    assert result["p_value"] > 0.05  # não deve rejeitar H0: bem calibrado
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/evaluation/test_calibration.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.evaluation.calibration'`.

- [ ] **Step 3: Implementar `check_interval_calibration`**

```python
"""Diagnóstico de calibração estatística do critério de anomalia do Prophet.

Ao marcar como anomalia todo ponto fora do intervalo de confiança de
`interval_width` (ex.: 95%), o critério é parcialmente tautológico: um modelo
bem calibrado já deixa, por construção, aproximadamente `1 - interval_width`
dos pontos fora do intervalo, tenha ocorrido ou não um evento hidrometeorológico
extremo real. Este módulo formaliza essa checagem, comparando a taxa observada
de exceção do intervalo com a taxa nominal esperada, em vez de deixar essa
discussão apenas qualitativa no texto do TCC.
"""

import logging
from typing import Dict

import pandas as pd
from scipy.stats import binomtest

logger = logging.getLogger(__name__)


def check_interval_calibration(flagged: pd.DataFrame, interval_width: float) -> Dict[str, float]:
    """Compara a taxa observada de anomalias com a taxa nominal esperada.

    Args:
        flagged: DataFrame com coluna `is_anomaly` (saída de `flag_anomalies`).
        interval_width: Largura do intervalo de incerteza usado para gerar
            `flagged` (ex.: 0.95). A taxa nominal de exceção esperada sob um
            modelo bem calibrado é `1 - interval_width`.

    Returns:
        Dicionário com `n_days`, `n_anomalies`, `observed_rate`,
        `nominal_rate` (`1 - interval_width`) e `p_value` do teste binomial
        bicaudal (H0: taxa observada == taxa nominal).
    """
    n_days = len(flagged)
    n_anomalies = int(flagged["is_anomaly"].sum())
    nominal_rate = 1 - interval_width
    observed_rate = n_anomalies / n_days if n_days > 0 else 0.0

    test_result = binomtest(n_anomalies, n_days, nominal_rate, alternative="two-sided")

    logger.info(
        "Calibração: observado=%.4f nominal=%.4f p-valor=%.4f (n=%d dias, %d anomalias)",
        observed_rate, nominal_rate, test_result.pvalue, n_days, n_anomalies,
    )

    return {
        "n_days": n_days,
        "n_anomalies": n_anomalies,
        "observed_rate": observed_rate,
        "nominal_rate": nominal_rate,
        "p_value": test_result.pvalue,
    }
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/evaluation/test_calibration.py -v
```
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/evaluation/calibration.py tests/evaluation/test_calibration.py
git commit -m "feat: diagnostico de calibracao estatistica do intervalo de confianca do Prophet"
```

### Task 11.2: Separar estatísticas in-sample (treino) de out-of-sample (teste)

`run_full_pipeline` e o notebook 02 geram o forecast sobre `df` inteiro (treino+teste) e chamam `flag_anomalies` sobre ele — anomalias "detectadas" dentro do período de treino não são detecção no sentido preditivo, pois o Prophet foi ajustado usando exatamente esses mesmos dias. Esta task não muda esse comportamento (ele é intencional para revisitar eventos históricos, ver célula markdown da Seção 3 do notebook 02), mas adiciona uma ferramenta para não apresentar as duas populações como uma taxa única.

**Files:**
- Modify: `src/evaluation/calibration.py`
- Test: `tests/evaluation/test_calibration.py`

**Interfaces:**
- Produz: `summarize_anomalies_by_period(flagged: pd.DataFrame, cutoff_date) -> pd.DataFrame`.

- [ ] **Step 1: Escrever o teste**

Adicione a `tests/evaluation/test_calibration.py`:

```python
from src.evaluation.calibration import summarize_anomalies_by_period


def test_summarize_anomalies_by_period_splits_train_and_test():
    flagged = pd.DataFrame({
        "ds": pd.date_range("2022-01-01", periods=10, freq="D"),
        "is_anomaly": [False, False, True, False, False, False, True, True, False, False],
    })
    cutoff = pd.Timestamp("2022-01-06")  # primeiros 6 dias = in_sample

    result = summarize_anomalies_by_period(flagged, cutoff)

    in_sample = result.loc[result["period"] == "in_sample"].iloc[0]
    out_of_sample = result.loc[result["period"] == "out_of_sample"].iloc[0]
    assert in_sample["n_days"] == 6
    assert in_sample["n_anomalies"] == 1
    assert out_of_sample["n_days"] == 4
    assert out_of_sample["n_anomalies"] == 2
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/evaluation/test_calibration.py -v
```
Expected: `ImportError: cannot import name 'summarize_anomalies_by_period'`.

- [ ] **Step 3: Implementar `summarize_anomalies_by_period`**

Adicione `import pandas as pd` (já presente) e, ao final de `src/evaluation/calibration.py`:

```python
def summarize_anomalies_by_period(flagged: pd.DataFrame, cutoff_date) -> pd.DataFrame:
    """Resume contagem e taxa de anomalias separadamente para o período de
    treino (in-sample, `ds <= cutoff_date`) e de teste (out-of-sample,
    `ds > cutoff_date`) do Prophet.

    Uma anomalia detectada dentro do período de treino não é, no sentido
    preditivo, uma "detecção": o Prophet foi ajustado usando exatamente esses
    mesmos dias, então o intervalo de incerteza já "viu" aquele valor. Separar
    as duas populações evita apresentar taxas de anomalia in-sample e
    out-of-sample como se fossem uma medida única e comparável.

    Args:
        flagged: DataFrame com colunas `ds`, `is_anomaly`.
        cutoff_date: Última data do período de treino (`train['ds'].max()`);
            dias com `ds <= cutoff_date` são in-sample, os demais são
            out-of-sample.

    Returns:
        DataFrame com uma linha por período (`in_sample`, `out_of_sample`),
        colunas `period`, `n_days`, `n_anomalies`, `rate`.
    """
    df = flagged.copy()
    df["period"] = df["ds"].apply(lambda d: "in_sample" if d <= cutoff_date else "out_of_sample")

    rows = []
    for period, group in df.groupby("period"):
        n_days = len(group)
        n_anomalies = int(group["is_anomaly"].sum())
        rows.append({
            "period": period,
            "n_days": n_days,
            "n_anomalies": n_anomalies,
            "rate": n_anomalies / n_days if n_days > 0 else 0.0,
        })
    return pd.DataFrame(rows).sort_values("period", ascending=False).reset_index(drop=True)
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/evaluation/test_calibration.py -v
```
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/evaluation/calibration.py tests/evaluation/test_calibration.py
git commit -m "feat: separar estatisticas de anomalia in-sample e out-of-sample"
```

### Task 11.3: Notebook 02/03 — seção de calibração e discussão da circularidade

**Files:**
- Modify: `notebooks/02_prophet_modeling.ipynb`, `notebooks/03_validation.ipynb`

**Interfaces:**
- Consome: `check_interval_calibration`, `summarize_anomalies_by_period` (Tasks 11.1-11.2).

- [ ] **Step 1: Adicionar ao notebook 02, logo após a Seção 3 (Forecast e Detecção de Anomalias), uma célula markdown de seção**

```markdown
## 3.1 - Diagnóstico de Calibração e Separação In-Sample / Out-of-Sample

O critério de anomalia usado acima (fora do intervalo de `interval_width`) é
parcialmente tautológico: um modelo bem calibrado já deixa, por construção,
aproximadamente `1 - interval_width` dos pontos fora do intervalo — com ou sem
evento real. Esta subseção mede se a taxa observada de anomalias diverge
significativamente da taxa nominal esperada, e separa a contagem de anomalias
entre o período de treino (in-sample — o Prophet "viu" esses dados no ajuste)
e o período de teste (out-of-sample — avaliação preditiva genuína).
```

- [ ] **Step 2: Adicionar célula de código no notebook 02**

```python
from src.evaluation.calibration import check_interval_calibration, summarize_anomalies_by_period

calibracao = check_interval_calibration(flagged, interval_width=0.95)
print(calibracao)

resumo_periodo = summarize_anomalies_by_period(flagged, cutoff_date=train["ds"].max())
resumo_periodo
```

- [ ] **Step 3: Adicionar célula markdown de discussão no notebook 02 (preencher após rodar o Step 2)**

```markdown
Preencher esta célula, após rodar o diagnóstico acima, com: a taxa observada
de anomalias está estatisticamente próxima da taxa nominal (`p_value` alto,
não rejeita H0) ou diverge significativamente? Se estiver próxima, isso é
evidência de que boa parte do "sinal" de 2,65% de anomalias é esperado por
calibração, não necessariamente eventos extremos reais — o que não invalida
o método, mas exige cautela ao interpretar o volume bruto de anomalias como
"eventos detectados". Reportar também a diferença de taxa entre
`resumo_periodo` in-sample vs. out-of-sample.
```

- [ ] **Step 4: Adicionar a mesma diagnose ao notebook 03 (reaproveitando `flagged` persistido), em uma nova seção antes da Seção 5 (Discussão)**

```markdown
## 4.3 - Diagnóstico de Calibração (ver Notebook 02, Seção 3.1)
```

```python
from src.evaluation.calibration import check_interval_calibration

calibracao = check_interval_calibration(flagged, interval_width=0.95)
calibracao
```

- [ ] **Step 5: Executar os dois notebooks ponta-a-ponta**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

for path in ["notebooks/02_prophet_modeling.ipynb", "notebooks/03_validation.ipynb"]:
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="python3")
    client.execute()
    nbformat.write(nb, path)
    print(f"Executado e salvo: {path}")
EOF
```
Expected: ambos executam sem exceção.

- [ ] **Step 6: Preencher manualmente as células de discussão com os números reais**

- [ ] **Step 7: Commit**

```bash
git add notebooks/02_prophet_modeling.ipynb notebooks/03_validation.ipynb
git commit -m "feat: diagnostico de calibracao e separacao in-sample/out-of-sample nos notebooks 02 e 03"
```

---

## Feature 12 — Ground truth: poder estatístico e expansão do catálogo de eventos

Apenas 2 dos 8 eventos catalogados caem dentro da janela 2020-2025 da série modelada (9 dias-evento no total, com tolerância de 1 dia) — poder estatístico baixíssimo para as métricas centrais do TCC (precision=0,069, recall=0,444, F1=0,119 no estado atual). Esta feature ataca isso de duas formas: expandindo o catálogo com pesquisa bibliográfica real (Task 12.1) e reportando a incerteza amostral explicitamente em vez de tratar os pontos estimados como precisos (Task 12.3).

### Task 12.1: [PESQUISA MANUAL — NÃO CODÁVEL] Expandir o catálogo de eventos extremos dentro de 2020-2025

> **Nota para o executor deste plano (humano ou agente):** esta task **não pode ser concluída por um agente autônomo sem acesso a fontes externas confiáveis**. Não invente eventos, datas ou fontes — um catálogo de ground truth fabricado é pior do que um catálogo pequeno porém honesto, e compromete a integridade do TCC. Se esta task não puder ser concluída, **pule para a Task 12.2** e documente a limitação no texto do TCC (ver checklist da Feature 14).

**Files:**
- Modify: `src/evaluation/known_events.py`
- Modify: `tests/evaluation/test_known_events.py` (ajustar `len(KNOWN_EXTREME_EVENTS) >= N` conforme o número final)

**Fontes a consultar (na ordem sugerida):**
1. Defesa Civil de Pernambuco / Defesa Civil do Recife — boletins e decretos de situação de emergência, 2020-2025.
2. CEMADEN — histórico de alertas emitidos para municípios da RMR (Recife, Olinda, Jaboatão dos Guararapes, Camaragibe), 2020-2025.
3. APAC — boletins de aviso meteorológico arquivados (além dos dois eventos de maio/2022 já usados em `docs/apac_metodologia.md`).
4. INMET/BDMEP — série histórica da estação da Várzea (Recife) ou de outra estação automática da RMR, para os anos 2020-2025 (não é o cliente `download_inmet.py`, que está bloqueado por autenticação — ver Task 13.3; o BDMEP tem exportação manual via `https://bdmep.inmet.gov.br/`).
5. Hemeroteca digital (jornais JC, Diario de Pernambuco) para eventos com repercussão noticiada, 2020-2025.

- [ ] **Step 1: Para cada evento novo encontrado, registrar name, region ("rmr"), start_date, end_date e source com citação verificável** (mesmo padrão já usado nos 8 eventos existentes em `src/evaluation/known_events.py`).

- [ ] **Step 2: Adicionar os eventos a `KNOWN_EXTREME_EVENTS`**, mantendo a ordenação cronológica do arquivo.

- [ ] **Step 3: Atualizar o teste de contagem mínima em `tests/evaluation/test_known_events.py`**

```python
def test_known_events_have_required_fields_and_valid_dates():
    required_keys = {"name", "region", "start_date", "end_date", "source"}
    assert len(KNOWN_EXTREME_EVENTS) >= 8  # ajustar para o novo total, nunca diminuir
    ...
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

```bash
.venv/bin/python -m pytest tests/evaluation/test_known_events.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/evaluation/known_events.py tests/evaluation/test_known_events.py
git commit -m "feat: ampliar catalogo de eventos extremos da RMR dentro da janela 2020-2025"
```

### Task 12.2: Extrair e testar `events_within_range` (elimina lógica duplicada do notebook 03)

O notebook 03 já filtra `KNOWN_EXTREME_EVENTS` para os que caem dentro do período da série (`eventos_no_periodo`, célula da Seção 4) — essa lógica está inline no notebook, não testada, e será reusada pela Task 12.1 sempre que o catálogo crescer. Extraí-la para `src/evaluation/known_events.py` a torna testável e elimina duplicação.

**Files:**
- Modify: `src/evaluation/known_events.py`
- Modify: `tests/evaluation/test_known_events.py`
- Modify: `notebooks/03_validation.ipynb` (substituir a list comprehension inline pela chamada à função)

**Interfaces:**
- Produz: `events_within_range(events: List[dict], start: pd.Timestamp, end: pd.Timestamp) -> List[dict]`.

- [ ] **Step 1: Escrever o teste**

Adicione a `tests/evaluation/test_known_events.py`:

```python
import pandas as pd

from src.evaluation.known_events import events_within_range

SAMPLE_EVENTS = [
    {"name": "Dentro", "region": "rmr", "start_date": "2022-05-25", "end_date": "2022-05-25", "source": "teste"},
    {"name": "Antes da janela", "region": "rmr", "start_date": "1970-08-10", "end_date": "1970-08-11", "source": "teste"},
    {"name": "Parcialmente sobreposto", "region": "rmr", "start_date": "2019-12-30", "end_date": "2020-01-02", "source": "teste"},
]


def test_events_within_range_keeps_only_overlapping_events():
    result = events_within_range(SAMPLE_EVENTS, pd.Timestamp("2020-01-01"), pd.Timestamp("2025-12-31"))

    names = {event["name"] for event in result}
    assert names == {"Dentro", "Parcialmente sobreposto"}
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/evaluation/test_known_events.py -v
```
Expected: `ImportError: cannot import name 'events_within_range'`.

- [ ] **Step 3: Implementar `events_within_range`**

Adicione ao final de `src/evaluation/known_events.py`:

```python
import pandas as pd


def events_within_range(events: List[ExtremeEvent], start: pd.Timestamp, end: pd.Timestamp) -> List[ExtremeEvent]:
    """Filtra eventos que se sobrepõem, mesmo que parcialmente, ao intervalo [start, end].

    Usado para restringir visualizações a eventos com dados observados/previstos
    correspondentes (ex.: a série 2020-2025 não cobre eventos de décadas
    anteriores) — nunca para descartar eventos da avaliação quantitativa, que é
    feita por `evaluate_anomalies` sobre o catálogo completo.

    Args:
        events: Lista de eventos no formato de `KNOWN_EXTREME_EVENTS`.
        start: Início do intervalo de referência (ex.: primeira data da série modelada).
        end: Fim do intervalo de referência (ex.: última data da série modelada).

    Returns:
        Sublista de `events` cujo [start_date, end_date] se sobrepõe a [start, end].
    """
    return [
        event for event in events
        if pd.Timestamp(event["end_date"]) >= start and pd.Timestamp(event["start_date"]) <= end
    ]
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/evaluation/test_known_events.py -v
```
Expected: todos os testes do arquivo passam.

- [ ] **Step 5: Substituir a list comprehension inline do notebook 03 pela chamada à função**

```bash
.venv/bin/python - <<'EOF'
import nbformat

path = "notebooks/03_validation.ipynb"
nb = nbformat.read(path, as_version=4)

OLD_IMPORT = "from src.evaluation.known_events import KNOWN_EXTREME_EVENTS"
NEW_IMPORT = "from src.evaluation.known_events import KNOWN_EXTREME_EVENTS, events_within_range"

OLD_FILTER_MARKER = "eventos_no_periodo = [\n    event for event in KNOWN_EXTREME_EVENTS"
NEW_FILTER = (
    "serie_inicio, serie_fim = flagged['ds'].min(), flagged['ds'].max()\n"
    "eventos_no_periodo = events_within_range(KNOWN_EXTREME_EVENTS, serie_inicio, serie_fim)"
)

changed = {"import": False, "filter": False}
for cell in nb.cells:
    if cell.cell_type != "code":
        continue
    source = "".join(cell.source) if isinstance(cell.source, list) else cell.source
    if OLD_IMPORT in source and not changed["import"]:
        cell.source = source.replace(OLD_IMPORT, NEW_IMPORT)
        changed["import"] = True
    if OLD_FILTER_MARKER in source and not changed["filter"]:
        lines = source.split("\n")
        start_idx = next(i for i, line in enumerate(lines) if line.startswith("serie_inicio"))
        end_idx = next(i for i, line in enumerate(lines) if i >= start_idx and line.strip() == "]") + 1
        new_lines = lines[:start_idx] + NEW_FILTER.split("\n") + lines[end_idx:]
        cell.source = "\n".join(new_lines)
        changed["filter"] = True

assert all(changed.values()), f"Bloco(s) nao encontrado(s): {changed}"
nbformat.write(nb, path)
print("OK:", changed)
EOF
```
Expected: `OK: {'import': True, 'filter': True}`.

- [ ] **Step 6: Executar o notebook 03 ponta-a-ponta e confirmar que o gráfico da Seção 4 continua correto**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

path = "notebooks/03_validation.ipynb"
nb = nbformat.read(path, as_version=4)
client = NotebookClient(nb, timeout=900, kernel_name="python3")
client.execute()
nbformat.write(nb, path)
print("Notebook 03 executado e salvo com sucesso.")
EOF
```
Expected: `Notebook 03 executado e salvo com sucesso.`

- [ ] **Step 7: Commit**

```bash
git add src/evaluation/known_events.py tests/evaluation/test_known_events.py notebooks/03_validation.ipynb
git commit -m "refactor: extrair events_within_range de logica inline do notebook 03"
```

### Task 12.3: Intervalos de confiança de Wilson para precision/recall

**Files:**
- Modify: `src/evaluation/metrics.py`
- Test: `tests/evaluation/test_metrics.py`

**Interfaces:**
- Produz: `evaluate_anomalies_with_confidence(flagged, known_events, tolerance_days=1, confidence=0.95) -> Dict[str, float]` — superconjunto de `evaluate_anomalies`, com `precision_ci_lower`, `precision_ci_upper`, `recall_ci_lower`, `recall_ci_upper`, `n_event_days`, `low_statistical_power`.

- [ ] **Step 1: Escrever o teste**

Adicione a `tests/evaluation/test_metrics.py` (reaproveitando o `EVENTS` já definido no arquivo):

```python
from src.evaluation.metrics import evaluate_anomalies_with_confidence


def test_evaluate_anomalies_with_confidence_flags_low_power_with_few_events():
    flagged = pd.DataFrame({
        "ds": pd.to_datetime(["2022-05-24", "2022-05-25", "2022-05-26", "2022-05-27"]),
        "is_anomaly": [False, True, False, True],
    })

    result = evaluate_anomalies_with_confidence(flagged, EVENTS, tolerance_days=0)

    assert result["n_event_days"] == 1
    assert result["low_statistical_power"] is True
    assert 0.0 <= result["recall_ci_lower"] <= result["recall"] <= result["recall_ci_upper"] <= 1.0
    assert 0.0 <= result["precision_ci_lower"] <= result["precision"] <= result["precision_ci_upper"] <= 1.0
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/evaluation/test_metrics.py -v
```
Expected: `ImportError: cannot import name 'evaluate_anomalies_with_confidence'`.

- [ ] **Step 3: Implementar `evaluate_anomalies_with_confidence`**

Adicione `from statsmodels.stats.proportion import proportion_confint` aos imports de `src/evaluation/metrics.py`, uma constante de módulo e a função ao final do arquivo:

```python
MIN_EVENT_DAYS_FOR_RELIABLE_ESTIMATE = 30


def evaluate_anomalies_with_confidence(
    flagged: pd.DataFrame,
    known_events: List[dict],
    tolerance_days: int = 1,
    confidence: float = 0.95,
) -> Dict[str, float]:
    """Como `evaluate_anomalies`, mas acrescenta intervalos de confiança de
    Wilson para `precision` e `recall`, e um aviso explícito de baixo poder
    estatístico quando o número de dias-evento é pequeno.

    Com poucos dias-evento (ex.: 9, como o catálogo de eventos dentro da janela
    2020-2025 da RMR produz atualmente), `precision`/`recall` têm incerteza de
    amostragem enorme — reportar só o ponto estimado sem o intervalo de
    confiança pode ser lido, incorretamente, como uma medida precisa.

    Args:
        flagged: Ver `evaluate_anomalies`.
        known_events: Ver `evaluate_anomalies`.
        tolerance_days: Ver `evaluate_anomalies`.
        confidence: Nível de confiança dos intervalos (padrão: 0.95).

    Returns:
        Dicionário de `evaluate_anomalies` acrescido de `precision_ci_lower`,
        `precision_ci_upper`, `recall_ci_lower`, `recall_ci_upper`,
        `n_event_days` e `low_statistical_power` (bool, `True` quando
        `n_event_days < MIN_EVENT_DAYS_FOR_RELIABLE_ESTIMATE`).
    """
    metrics = evaluate_anomalies(flagged, known_events, tolerance_days=tolerance_days)

    tp = metrics["true_positives"]
    fp = metrics["false_positives"]
    fn = metrics["false_negatives"]
    n_event_days = tp + fn
    n_flagged_days = tp + fp

    alpha = 1 - confidence
    if n_flagged_days > 0:
        precision_ci = proportion_confint(tp, n_flagged_days, alpha=alpha, method="wilson")
    else:
        precision_ci = (0.0, 0.0)
    if n_event_days > 0:
        recall_ci = proportion_confint(tp, n_event_days, alpha=alpha, method="wilson")
    else:
        recall_ci = (0.0, 0.0)

    metrics.update({
        "precision_ci_lower": precision_ci[0],
        "precision_ci_upper": precision_ci[1],
        "recall_ci_lower": recall_ci[0],
        "recall_ci_upper": recall_ci[1],
        "n_event_days": n_event_days,
        "low_statistical_power": n_event_days < MIN_EVENT_DAYS_FOR_RELIABLE_ESTIMATE,
    })
    return metrics
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/evaluation/test_metrics.py -v
```
Expected: `2 passed`.

- [ ] **Step 5: Adicionar ao notebook 03, na Seção 2 (Métricas de Avaliação), a versão com intervalo de confiança**

```bash
.venv/bin/python - <<'EOF'
import nbformat

path = "notebooks/03_validation.ipynb"
nb = nbformat.read(path, as_version=4)

OLD_IMPORT = "from src.evaluation.metrics import evaluate_anomalies"
NEW_IMPORT = "from src.evaluation.metrics import evaluate_anomalies, evaluate_anomalies_with_confidence"

changed = False
for cell in nb.cells:
    if cell.cell_type != "code":
        continue
    source = "".join(cell.source) if isinstance(cell.source, list) else cell.source
    if OLD_IMPORT in source and not changed:
        cell.source = source.replace(OLD_IMPORT, NEW_IMPORT)
        changed = True

assert changed, "Import de evaluate_anomalies nao encontrado"
nbformat.write(nb, path)
print("OK: import atualizado")
EOF
```

Depois, adicione manualmente uma célula de código logo após a célula que roda `evaluate_anomalies(flagged, ...)` na Seção 2:

```python
metrics_com_ic = evaluate_anomalies_with_confidence(flagged, KNOWN_EXTREME_EVENTS, tolerance_days=1)
pd.DataFrame([metrics_com_ic])
```

E uma célula markdown logo abaixo:

```markdown
**Leitura dos intervalos de confiança.** Os pontos estimados de `precision` e
`recall` reportados acima (e discutidos na Seção 5) vêm acompanhados de
intervalos de confiança de Wilson de 95%. Com `n_event_days` pequeno, esses
intervalos são largos — o que deve ser lido explicitamente como um limite do
tamanho da amostra de ground truth, não como imprecisão do método de detecção
em si (ver também Task 12.1 sobre expansão do catálogo).
```

- [ ] **Step 6: Executar o notebook 03 ponta-a-ponta**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

path = "notebooks/03_validation.ipynb"
nb = nbformat.read(path, as_version=4)
client = NotebookClient(nb, timeout=900, kernel_name="python3")
client.execute()
nbformat.write(nb, path)
print("Notebook 03 executado e salvo com sucesso.")
EOF
```
Expected: `Notebook 03 executado e salvo com sucesso.`

- [ ] **Step 7: Commit**

```bash
git add src/evaluation/metrics.py tests/evaluation/test_metrics.py notebooks/03_validation.ipynb
git commit -m "feat: intervalos de confianca de Wilson para precision/recall com poucos eventos"
```

---

## Feature 13 — Validação cruzada de fonte (ERA5-Land vs. CEMADEN) e resolução de código órfão

O projeto depende de uma única fonte (reanálise ERA5-Land) sem cross-check contra dado observado — risco conceitual central da anamnese. `src/data/load_cemaden.py` e `src/data/harmonize.py` já existem e são testados, mas nunca foram usados pelo pipeline real; `src/data/download_inmet.py` está confirmadamente quebrado (a própria documentação do módulo registra 404/token inválido contra a API real do INMET). Esta feature finalmente utiliza os dois primeiros e remove o terceiro.

### Task 13.1: Comparar ERA5-Land com uma fonte observacional nos dias de sobreposição

**Files:**
- Create: `src/evaluation/source_comparison.py`
- Test: `tests/evaluation/test_source_comparison.py`

**Interfaces:**
- Consome: DataFrames `(ds, y)` no mesmo formato produzido por `src.data.preprocess` e `src.data.load_cemaden.load_cemaden_csv`.
- Produz: `compare_sources(era5: pd.DataFrame, observed: pd.DataFrame) -> Dict[str, float]`.

- [ ] **Step 1: Escrever o teste**

```python
# tests/evaluation/test_source_comparison.py
import pandas as pd
import pytest

from src.evaluation.source_comparison import compare_sources


def test_compare_sources_computes_bias_and_correlation():
    era5 = pd.DataFrame({
        "ds": pd.to_datetime(["2022-05-25", "2022-05-26", "2022-05-27"]),
        "y": [40.0, 20.0, 5.0],
    })
    observed = pd.DataFrame({
        "ds": pd.to_datetime(["2022-05-25", "2022-05-26", "2022-05-27"]),
        "y": [45.4, 18.0, 6.0],
    })

    result = compare_sources(era5, observed)

    assert result["n_overlapping_days"] == 3
    expected_bias = ((40.0 - 45.4) + (20.0 - 18.0) + (5.0 - 6.0)) / 3
    assert result["mean_bias_mm"] == pytest.approx(expected_bias)
    assert -1.0 <= result["pearson_r"] <= 1.0


def test_compare_sources_handles_insufficient_overlap():
    era5 = pd.DataFrame({"ds": pd.to_datetime(["2022-05-25"]), "y": [40.0]})
    observed = pd.DataFrame({"ds": pd.to_datetime(["2022-06-01"]), "y": [10.0]})

    result = compare_sources(era5, observed)

    assert result["n_overlapping_days"] == 0
    assert result["pearson_r"] is None
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/evaluation/test_source_comparison.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.evaluation.source_comparison'`.

- [ ] **Step 3: Implementar `src/evaluation/source_comparison.py`**

```python
"""Comparação entre a série ERA5-Land (usada no pipeline principal) e uma
fonte observacional (CEMADEN), nos dias em que ambas têm dado disponível —
mitiga a dependência de uma única fonte de reanálise para a definição do que
conta como "chuva real"."""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compare_sources(era5: pd.DataFrame, observed: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Compara duas séries (ds, y) nos dias em que ambas têm valor não-nulo.

    Args:
        era5: Série (ds, y) da fonte de reanálise (ERA5-Land).
        observed: Série (ds, y) de uma fonte observacional (ex.: CEMADEN).

    Returns:
        Dicionário com `n_overlapping_days`, `pearson_r`, `mean_bias_mm`
        (média de `era5.y - observed.y`) e `rmse_mm`. As três últimas chaves
        são `None` se houver menos de 2 dias de sobreposição.
    """
    merged = era5.merge(observed, on="ds", how="inner", suffixes=("_era5", "_observed"))
    merged = merged.dropna(subset=["y_era5", "y_observed"])
    n = len(merged)

    if n < 2:
        logger.warning(
            "Apenas %d dia(s) de sobreposição entre ERA5-Land e a fonte observacional "
            "— sem dado suficiente para comparação estatística.", n,
        )
        return {"n_overlapping_days": n, "pearson_r": None, "mean_bias_mm": None, "rmse_mm": None}

    diff = merged["y_era5"] - merged["y_observed"]
    pearson_r = merged["y_era5"].corr(merged["y_observed"])
    mean_bias = float(diff.mean())
    rmse = float(np.sqrt((diff ** 2).mean()))

    logger.info(
        "Comparação ERA5 vs. observado: %d dias, r=%.3f, viés médio=%.2f mm, RMSE=%.2f mm",
        n, pearson_r, mean_bias, rmse,
    )
    return {"n_overlapping_days": n, "pearson_r": pearson_r, "mean_bias_mm": mean_bias, "rmse_mm": rmse}
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/evaluation/test_source_comparison.py -v
```
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/evaluation/source_comparison.py tests/evaluation/test_source_comparison.py
git commit -m "feat: comparar ERA5-Land com fonte observacional (CEMADEN) nos dias de sobreposicao"
```

### Task 13.2: Notebook 03 — seção opcional de cross-check com CEMADEN

Esta seção só roda se um export manual do CEMADEN existir localmente — o CEMADEN não tem API programática estável (ver docstring de `src/data/load_cemaden.py`), então a obtenção do CSV é necessariamente manual e fora do controle deste plano. A seção é escrita para degradar graciosamente (aviso claro, sem erro) quando o arquivo não existir.

**Files:**
- Modify: `notebooks/03_validation.ipynb`

**Interfaces:**
- Consome: `load_cemaden_csv` (já existente), `harmonize_sources` (já existente, nunca antes usado pelo pipeline), `compare_sources` (Task 13.1).

- [ ] **Step 1: Adicionar célula markdown de seção (antes da Seção 5, Discussão)**

```markdown
## 4.4 - Validação Cruzada de Fonte: ERA5-Land vs. CEMADEN (quando disponível)

O pipeline principal usa exclusivamente ERA5-Land (reanálise, não pluviômetro).
Reanálises são conhecidas por subestimar chuva convectiva tropical localizada —
exatamente o fenômeno que este TCC define como "anomalia". Esta seção compara,
nos dias em que houver exportação manual do CEMADEN disponível em
`dados/raw/cemaden/export_rmr.csv`, a série ERA5-Land usada no pipeline com a
série observacional do CEMADEN. **Instruções para obter o export:** acessar
http://www2.cemaden.gov.br, filtrar estações/pluviômetros dentro da RMR
(Recife e municípios vizinhos) e exportar o CSV no formato documentado em
`src/data/load_cemaden.py` (colunas `codEstacao`, `municipio`, `datahora`,
`valorMedida`, separador `;`), salvando em `dados/raw/cemaden/export_rmr.csv`.
Se o arquivo não existir, a célula abaixo apenas registra um aviso e a seção
é pulada — nenhuma outra parte do notebook depende deste cross-check.
```

- [ ] **Step 2: Adicionar célula de código**

```python
from src.data.load_cemaden import load_cemaden_csv
from src.data.harmonize import harmonize_sources
from src.evaluation.source_comparison import compare_sources

cemaden_export_path = PROJECT_ROOT / "dados" / "raw" / "cemaden" / "export_rmr.csv"

if cemaden_export_path.exists():
    cemaden_df = load_cemaden_csv(cemaden_export_path)
    era5_df = flagged[["ds", "y"]]

    comparacao_fontes = compare_sources(era5_df, cemaden_df)
    print("Comparação ERA5-Land vs. CEMADEN:", comparacao_fontes)

    harmonizado = harmonize_sources(
        {"cemaden": cemaden_df, "era5": era5_df}, priority=["cemaden", "era5"]
    )
    print(f"Série harmonizada (prioridade CEMADEN > ERA5-Land): {harmonizado['source'].value_counts().to_dict()}")
else:
    print(
        f"Export do CEMADEN não encontrado em {cemaden_export_path}. "
        "Cross-check de fonte pulado — ver instruções na célula markdown acima "
        "para gerar o export manualmente."
    )
```

- [ ] **Step 3: Adicionar célula markdown de discussão (preencher manualmente se o export existir; caso contrário, registrar a limitação)**

```markdown
Se a célula acima encontrou o export do CEMADEN: preencher com o viés médio,
RMSE e correlação observados, e discutir se o ERA5-Land sub ou superestima a
chuva na RMR em relação ao CEMADEN. Se não encontrou: registrar explicitamente
que a validação cruzada de fonte não foi possível dentro do prazo do TCC por
falta de export manual do CEMADEN, e que isso é uma limitação conhecida (ver
checklist da Feature 14) — não deletar esta seção nem fingir que a comparação
foi feita.
```

- [ ] **Step 4: Executar o notebook 03 ponta-a-ponta (deve rodar tanto com quanto sem o export do CEMADEN)**

```bash
.venv/bin/python - <<'EOF'
import nbformat
from nbclient import NotebookClient

path = "notebooks/03_validation.ipynb"
nb = nbformat.read(path, as_version=4)
client = NotebookClient(nb, timeout=900, kernel_name="python3")
client.execute()
nbformat.write(nb, path)
print("Notebook 03 executado e salvo com sucesso.")
EOF
```
Expected: `Notebook 03 executado e salvo com sucesso.`, com a célula do Step 2 imprimindo a mensagem de "export não encontrado" (comportamento esperado se o CSV real do CEMADEN não tiver sido obtido ainda).

- [ ] **Step 5: Commit**

```bash
git add notebooks/03_validation.ipynb
git commit -m "feat: secao opcional de cross-check ERA5-Land vs CEMADEN no notebook 03"
```

### Task 13.3: Remover o cliente INMET não-funcional (código órfão)

`src/data/download_inmet.py` documenta, no próprio docstring, que a rota `/estacao/dados/...` retorna 404 e a rota alternativa exige um token de API que o projeto não possui — o módulo nunca foi (e não pode ser, sem um token) validado contra a API real, e não é usado por nenhum outro módulo além do seu próprio teste de contrato hipotético. Mantê-lo no repositório sugere, incorretamente, que o INMET é uma fonte ativa do pipeline.

**Files:**
- Delete: `src/data/download_inmet.py`, `tests/data/test_download_inmet.py`

- [ ] **Step 1: Confirmar que nenhum outro módulo importa `download_inmet`**

```bash
grep -rn "download_inmet\|fetch_inmet_station\|parse_inmet_response" --include="*.py" --include="*.ipynb" src/ tests/ notebooks/
```
Expected: só ocorrências dentro de `src/data/download_inmet.py` e `tests/data/test_download_inmet.py` (os dois arquivos a remover). Se algo mais aparecer, pare e investigue antes de remover.

- [ ] **Step 2: Remover os dois arquivos**

```bash
git rm src/data/download_inmet.py tests/data/test_download_inmet.py
```

- [ ] **Step 3: Rodar a suíte completa e confirmar que nada quebrou**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: todos os testes restantes passam (uma a menos que antes: sem o teste de `download_inmet`).

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: remover cliente INMET nao-funcional (bloqueado por autenticacao, nunca usado pelo pipeline)"
```

> **Nota de decisão:** se um token de API do INMET for obtido futuramente, `src/data/download_inmet.py` pode ser recuperado do histórico do git (`git log --all --full-history -- src/data/download_inmet.py`) e revalidado contra a API real antes de ser reintegrado — esta remoção não é uma afirmação de que o INMET nunca poderá ser usado, só de que código não-testável contra a API real não deve permanecer no pipeline principal.

---

## Feature 14 — Checklist de fechamento (não-código, bloqueante para a redação do TCC)

Estas tarefas não produzem código testável por `pytest`, mas são bloqueantes para a defesa e devem ser rastreadas junto com o restante do plano.

- [ ] Confirmar que a Task 12.1 (expansão do catálogo de eventos) foi concluída ou, se não foi, redigir explicitamente a limitação de poder estatístico do ground truth na seção de limitações do TCC, citando os intervalos de confiança de Wilson da Task 12.3 como evidência quantitativa dessa limitação (ex.: recall = 0,444 com IC de Wilson de 95% em [0,19; 0,73]).
- [ ] Redigir, no texto do TCC, a discussão da circularidade estatística do critério de anomalia (Feature 11) — deixar explícito que parte do volume de anomalias é esperado por calibração, e não necessariamente eventos extremos reais.
- [ ] Redigir a comparação Prophet vs. baselines (Feature 9) como parte da justificativa metodológica de por que o Prophet foi escolhido (ou não) em relação a alternativas mais simples.
- [ ] Redigir a discussão de estabilidade entre folds do rolling-origin backtesting (Feature 10) — se as métricas da Seção 2 do notebook 03 são representativas ou dependem da janela de teste escolhida.
- [ ] Se a Task 13.2 (cross-check CEMADEN) não puder ser concluída por falta de export manual, documentar explicitamente essa limitação e a dependência de fonte única (ERA5-Land) na seção de limitações do TCC.
- [ ] Confirmar com a orientadora se a remoção do cliente INMET (Task 13.3) precisa ser mencionada no texto (ex.: como "tentativa não bem-sucedida", nota de transparência metodológica) ou se basta não citá-lo.
- [ ] Gerar as figuras finais das novas seções (comparação com baselines, estabilidade de folds, calibração, cross-check de fonte) em alta resolução para o texto do TCC.
- [ ] Revisão final do texto e preparação de slides para a defesa, incorporando as novas seções de rigor metodológico como resposta proativa às perguntas mais prováveis da banca.

---

## Self-Review desta versão do plano

- **Cobertura das negativas da anamnese de 2026-07-05:**
  - Ground truth com poder estatístico baixo → Feature 12 (expansão do catálogo + IC de Wilson).
  - Circularidade estatística do critério de anomalia → Feature 11 (diagnóstico de calibração + separação in-sample/out-of-sample).
  - Ausência de baseline de comparação → Feature 9 (Z-score, IQR, STL residual).
  - Único split treino/teste sem validação cruzada → Feature 10 (rolling-origin backtesting).
  - Dependência de fonte única de reanálise + código órfão do INMET/CEMADEN/harmonize → Feature 13 (cross-check CEMADEN finalmente ativado, INMET removido com decisão documentada).
  - Reprodutibilidade (seed do Prophet/cmdstanpy) → Task 7.1 (cobrindo tanto o `seed` do `cmdstanpy` quanto o `np.random.seed` da simulação de incerteza, ambos confirmados necessários).
  - Ineficiência de download (Brasil inteiro para recortar RMR) → Task 8.1.
  - Empacotamento frágil (sem `pyproject.toml`, sem `__init__.py`, `sys.path` hack) → Task 7.4.
  - Dependência não declarada (`requests`) e dependências de notebook não declaradas (`ipykernel`, `nbformat`) → Task 7.3.
  - Caminho absoluto hardcoded no notebook 01 → Task 7.2.
  - Todos os 12 pontos negativos da anamnese têm uma task correspondente; nenhum ficou sem tratamento.

- **Placeholder scan:** nenhuma task usa "TBD"/"implementar depois"/"adicionar tratamento de erro apropriado". As únicas células de notebook com "preencher após rodar" são explicitamente interpretativas (discussão textual que depende de números gerados em tempo de execução, não código) — mesmo padrão já usado no plano anterior (Tasks 3.4, 4.4). A Task 12.1 é a única exceção deliberada, marcada como não-codável por exigir pesquisa bibliográfica externa; isso é uma decisão de integridade científica, não uma lacuna de planejamento.

- **Consistência de tipos e assinaturas:** `fit_prophet_model(df, interval_width=0.95, seed=None, **kwargs)` e `generate_forecast(model, df, seed=None)` (Task 7.1) são usados com essa assinatura exata em `src/run_pipeline.py` (Step 5 da Task 7.1) e em `src/evaluation/backtesting.py` (Task 10.2). Todos os detectores baseline (`flag_anomalies_zscore`, `flag_anomalies_iqr`, `flag_anomalies_stl_residual`) devolvem exatamente `ds`, `y`, `is_anomaly`, `severity` — o mesmo contrato de `flag_anomalies` — e por isso são consumidos por `evaluate_anomalies` sem adaptação na Task 9.4. `evaluate_anomalies_with_confidence` (Task 12.3) é um superconjunto estrito de `evaluate_anomalies` (mesmas chaves + 6 novas), preservando compatibilidade com quem já consome só as chaves originais.

- **Validação empírica prévia:** ao contrário de uma revisão só de código, cada comportamento não-óbvio deste plano foi executado e confirmado no ambiente real antes de ser escrito — reprodutibilidade do Prophet com/sem `np.random.seed` (Task 7.1), mecânica da STL com `period` pequeno (Task 9.3), intervalos de Wilson e teste binomial com os números reais do projeto (Tasks 11.1, 12.3), geração de folds de rolling-origin (Task 10.1-10.2) e execução de notebook via `nbclient` sem depender do binário `jupyter-execute` (que está com o shebang quebrado neste ambiente, ver Global Constraints).

- **Nenhuma dependência nova além das três (`requests`, `ipykernel`, `nbformat`) da Task 7.3** — `statsmodels` (STL, Wilson) e `scipy` (teste binomial) já estão em `requirements.txt` desde o plano anterior.
