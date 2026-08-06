# Etapa 2 — Auditar e Reconstruir a Série — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir a semântica temporal e espacial da série de precipitação da RMR antes de qualquer modelagem: alinhar `valid_time` ao fuso `America/Recife` (e a um bug de rotulagem de janela de acumulação descoberto durante a auditoria), substituir o bounding box por uma máscara do polígono oficial da RMR, adicionar máximo espacial e percentis altos, registrar metadados de proveniência, validar manualmente a de-acumulação em 3 dias amostrais reais, e regenerar a série processada 2020-2025 a partir do pipeline corrigido.

**Architecture:** Mudanças concentradas em `src/data/preprocess.py` (funções puras, uma responsabilidade cada) mais dois módulos novos (`src/data/rmr_polygon.py`, `src/data/metadata.py`). Nenhuma mudança em `src/models` ou `src/evaluation` — esta etapa termina na regeneração de `dados/processed/`, não toca Prophet. Testes rápidos usam fixtures sintéticas (como já é convenção no projeto); a validação de sanidade (Task 5) e a regeração final (Task 6) usam os arquivos NetCDF reais já baixados em `dados/raw/` (8,6 GB, local, sem novo download), com skip gracioso se ausentes.

**Tech Stack:** Mesmo do projeto (Python, pandas, xarray, netCDF4) mais `geobr`/`geopandas`/`shapely`/`pyproj`/`pyogrio` (novas, só para a máscara espacial — usam o backend `pyogrio`, que traz binários GDAL pré-compilados, evitando a dependência de `gdal-config` do sistema que bloqueia `fiona`/Cartopy/earthkit-plots neste ambiente).

## Descoberta feita durante o planejamento desta etapa (premissa, não tarefa em aberto)

A validação manual exigida pelo Etapa 2 do escopo (`docs/escopo_e_limitacoes.md`, item 7) já foi feita durante o planejamento, usando os arquivos reais de `dados/raw/`, e encontrou um **segundo bug**, distinto do gap de fuso horário já documentado: o ERA5-Land rotula cada passo horário acumulado de `tp` com o `valid_time` do **fim** da janela de acumulação (convenção ECMWF), não do início. Confirmado empiricamente em `dados/raw/precipitacao_2020_01.nc`: para qualquer dia D, o reset do acumulador (diff negativo entre passos consecutivos) ocorre no passo `D 01:00`, nunca em `D 00:00` — ou seja, o valor rotulado `D 00:00` é, na verdade, o incremento acumulado entre `D-1 23:00` e `D 00:00`, pertencente ao dia anterior. O `ds.resample({time_dim: "1D"}).sum()` atual, que agrupa diretamente pelo `valid_time` bruto, portanto inclui a última hora do dia ANTERIOR e descarta a última hora do dia CORRENTE em todo total diário — um viés sistemático medido em ~10-25% nos dias chuvosos amostrados (25/05/2022, 15/08/2023), desprezível no dia seco amostrado (02/01/2020). Esta etapa corrige isso (Task 1) como parte da mesma correção de alinhamento temporal, já que ambas as correções (relabel -1h e fuso -3h) precisam ser aplicadas ao mesmo índice `valid_time` antes do resample.

## Global Constraints

- **Esta etapa pode alterar todos os números publicados até agora.** `dados/processed/serie_prophet_rmr_2020_2025.csv` será sobrescrito com valores corrigidos ao final (Task 6). Nenhum resultado anterior a esta etapa deve ser reaproveitado depois dela — consistente com o aviso já registrado em `docs/escopo_e_limitacoes.md`.
- **`dados/processed/flagged_prophet_rmr_2020_2025.csv` (saída do Prophet do notebook 02) fica stale após esta etapa** — foi gerado sobre a série não corrigida. Esta etapa não o regenera (regenerar exigiria reajustar o Prophet, fora do escopo de auditoria de série) nem o apaga; a Task 6 apenas registra esse fato em `docs/escopo_e_limitacoes.md`. Reajustar o Prophet é trabalho da Etapa 3.
- **Nenhum notebook é reexecutado nesta etapa.** A reescrita de números/conclusões nos notebooks é Etapa 10. Esta etapa só toca `src/data/` e `dados/processed/`.
- **`America/Recife` não observa horário de verão desde 2019** — confirmado (`pandas.DatetimeIndex(...).tz_localize("UTC").tz_convert("America/Recife")` produz offset fixo `-03:00` para toda a janela 2020-2025, verificado para `2020-01-01`, `2022-06-15` e `2025-12-31`). Ainda assim, a conversão deve usar `zoneinfo`/`tz_convert` (nunca subtração hardcoded de 3 horas), para não depender dessa premissa silenciosamente e para que o código continue correto se a janela de dados for estendida no futuro.
- **Fonte oficial do polígono da RMR: `geobr.read_metro_area(year=2018)`, filtrado por `name_metro == "Rm Recife"`.** Verificado: retorna 15 municípios (Recife, Olinda, Jaboatão dos Guararapes, Camaragibe, São Lourenço da Mata, Paulista, Cabo de Santo Agostinho, Igarassu, Itapissuma, Ilha de Itamaracá, Abreu e Lima, Araçoiaba, Moreno, Ipojuca, Goiana), com base legal (`Lei Complementar 014` federal de 1973 e leis complementares estaduais posteriores) explícita por município na própria coluna `legislation` do GeoDataFrame — não usar uma lista de municípios hardcoded à mão.
- **O polígono da RMR (bounds aproximados lat -8,61 a -7,46, lon -35,27 a -34,81) é MAIOR que o bounding box atual (lat -8,3 a -7,9, lon -35,2 a -34,8)** — o bbox atual exclui partes reais da RMR (ex.: região de Goiana, ao norte). Isso é uma correção metodológica real, não só estética.
- **Novas dependências vão em `requirements.txt`, pinadas nas versões verificadas neste planejamento**: `geobr==1.0.0`, `geopandas==1.1.4`, `shapely==2.1.2`, `pyproj==3.7.2`, `pyogrio==0.13.0`, `duckdb==1.5.5`, `html5lib==1.1`, `lxml==6.1.1`, `pyarrow==25.0.0`, `rapidfuzz==3.14.5`. **Nota:** o próprio `geobr==1.0.0` declara limites mais conservadores (`geopandas<=1.1.2`, `shapely<=2.1.0`); usamos versões mais novas porque são as únicas com wheel pré-compilado para o Python 3.14 deste sandbox de execução — testadas e funcionando de ponta a ponta (chamada real a `geobr.read_metro_area`, dados corretos retornados). Em Python 3.12 (ambiente alvo do projeto, `pyproject.toml`), o resultado deve ser equivalente; se o executor deste plano encontrar um conflito real de versões em 3.12, ajustar os pins e documentar a mudança.
- **Testes rápidos nunca usam `dados/raw/` real** (convenção já estabelecida em `tests/conftest.py` — fixtures sintéticas `tiny_precip_dataset`, `tiny_prophet_df`). As únicas exceções são a Task 5 (validação de sanidade) e a Task 6 (regeração final), que **exigem** dados reais por definição — ambas devem verificar a existência dos arquivos em `dados/raw/` e pular graciosamente (`pytest.skip`) se ausentes, para não quebrar uma instalação limpa do repositório.
- Formato canônico `ds`/`y` mantido em `dados/processed/serie_prophet_rmr_2020_2025.csv` (consumido pelo Prophet) — as novas estatísticas espaciais (máximo, p90, p95) vão em um arquivo **separado**, `dados/processed/serie_estatisticas_espaciais_rmr_2020_2025.csv`, para não quebrar esse contrato.
- Ambiente: `.venv` no worktree desta etapa (ver Etapa 1 para o padrão — Python 3.14 é o único disponível neste sandbox; o projeto pina 3.12 em `pyproject.toml`, mas nada nesta etapa depende de uma feature exclusiva de 3.12). Use `.venv/bin/python -m pytest ...`.
- Commits pequenos e frequentes, um por task concluída.

---

## Task 1: Corrigir alinhamento temporal (relabel de `valid_time` + fuso `America/Recife`) antes da agregação diária

**Files:**
- Modify: `src/data/preprocess.py`
- Test: `tests/data/test_preprocess.py`

**Interfaces:**
- Produz: `align_valid_time_to_accumulation_window(da: xr.DataArray, time_dim: str = "valid_time") -> xr.DataArray`
- Produz: `to_local_time(da: xr.DataArray, tz: str = "America/Recife", time_dim: str = "valid_time") -> xr.DataArray`
- Modifica: `compute_daily_areal_precipitation(...)` para aplicar as duas funções acima, nessa ordem, entre `deaccumulate_precipitation` e `.resample(...)`.
- Consumido por: Task 3 (`compute_daily_spatial_stats`, que compartilha a mesma preparação), Task 5 (teste de sanidade), Task 6 (regeração final).

- [ ] **Step 1: Escrever os testes (devem falhar antes da implementação)**

Adicione ao final de `tests/data/test_preprocess.py`:

```python
import pandas as pd


def test_align_valid_time_to_accumulation_window_shifts_back_one_hour():
    times = pd.date_range("2020-01-01 01:00", periods=3, freq="h")
    da = xr.DataArray([1.0, 2.0, 3.0], dims=["valid_time"], coords={"valid_time": times})

    aligned = align_valid_time_to_accumulation_window(da)

    expected_times = pd.date_range("2020-01-01 00:00", periods=3, freq="h")
    np.testing.assert_array_equal(aligned["valid_time"].values, expected_times.values)
    np.testing.assert_allclose(aligned.values, [1.0, 2.0, 3.0])


def test_to_local_time_converts_utc_to_america_recife_fixed_offset():
    times = pd.to_datetime(["2020-01-01T03:00", "2022-06-15T12:00", "2025-12-31T23:00"])
    da = xr.DataArray([1.0, 2.0, 3.0], dims=["valid_time"], coords={"valid_time": times})

    local = to_local_time(da)

    expected = pd.to_datetime(["2020-01-01T00:00", "2022-06-15T09:00", "2025-12-31T20:00"])
    np.testing.assert_array_equal(local["valid_time"].values, expected.values)


def test_compute_daily_areal_precipitation_applies_time_alignment_before_resampling():
    # 26h de dados: passo 00:00 (fim do ciclo anterior, deve ir para o dia anterior
    # apos o relabel -1h) + 24h de um novo ciclo (reset em 01:00) + 1h extra do dia
    # seguinte (fecha o ciclo do dia do meio).
    times = pd.date_range("2020-01-01 00:00", periods=26, freq="h")
    # acumulado (m): [alto = fim do ciclo anterior, reset baixo, sobe 24h, reset de novo]
    cumulative = [0.010] + [0.0002 * i for i in range(1, 24)] + [0.0002 * 24, 0.0001]
    lat, lon = [-8.0, -8.05], [-35.0, -34.95]
    data = np.tile(np.array(cumulative).reshape(26, 1, 1), (1, len(lat), len(lon)))
    ds = xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], data)},
        coords={"valid_time": times, "latitude": lat, "longitude": lon},
    )

    series = compute_daily_areal_precipitation(ds)

    # apos relabel -1h e conversao para America/Recife (-3h), o dia local
    # 2019-12-31 (UTC-3) deve conter o passo bruto 00:00 (fim do ciclo anterior,
    # 10mm) e nao deve misturar o novo ciclo com reset em 01:00 UTC.
    assert pd.Timestamp("2019-12-31") in series.index
    assert series.loc[pd.Timestamp("2019-12-31")] == pytest.approx(10.0, abs=0.5)
```

Adicione os imports necessários no topo do arquivo (`pandas as pd` já é usado; adicione `align_valid_time_to_accumulation_window, to_local_time` ao import existente de `src.data.preprocess`).

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/data/test_preprocess.py -v
```
Expected: `ImportError: cannot import name 'align_valid_time_to_accumulation_window'` (e, apos corrigir o import, falhas de `NameError`/`AttributeError` nos três testes novos).

- [ ] **Step 3: Implementar as duas funções e integrá-las em `compute_daily_areal_precipitation`**

Adicione a `src/data/preprocess.py`, logo após `deaccumulate_precipitation` (antes de `compute_daily_areal_precipitation`):

```python
def align_valid_time_to_accumulation_window(da: xr.DataArray, time_dim: str = "valid_time") -> xr.DataArray:
    """Corrige o rótulo temporal de uma variável acumulada do ERA5-Land.

    O ERA5-Land rotula cada passo horário acumulado com o `valid_time` do
    FINAL da janela de acumulação (convenção ECMWF), não do início. Ex.: o
    valor rotulado `2020-01-02T00:00` é, na verdade, o incremento acumulado
    entre `2020-01-01T23:00` e `2020-01-02T00:00` — ou seja, pertence ao dia
    01/01, não ao dia 02/01. Confirmado empiricamente em
    `dados/raw/precipitacao_2020_01.nc`: para qualquer dia D, o reset do
    acumulador (diff negativo entre passos consecutivos) ocorre no passo
    `D 01:00`, nunca em `D 00:00` — logo `D 00:00` ainda é o último passo
    do ciclo de D-1.

    Sem esta correção, um `resample("1D")` direto sobre `valid_time` inclui
    a última hora do dia ANTERIOR e descarta a última hora do dia CORRENTE
    em cada total diário — um viés sistemático medido em ~10-25% nos dias
    chuvosos amostrados (ver tests/data/test_deaccumulation_sanity.py).

    Args:
        da: DataArray já de-acumulado (ver `deaccumulate_precipitation`),
            com `valid_time` na convenção original do ERA5-Land (rótulo =
            fim da janela).
        time_dim: Nome da dimensão temporal.

    Returns:
        DataArray com `valid_time` deslocado -1h, agora rotulado pelo
        INÍCIO da hora que o valor representa.
    """
    shifted = da.copy()
    shifted[time_dim] = shifted[time_dim] - pd.Timedelta(hours=1)
    return shifted


def to_local_time(da: xr.DataArray, tz: str = "America/Recife", time_dim: str = "valid_time") -> xr.DataArray:
    """Converte o índice temporal (UTC, sem tzinfo) de um DataArray para um fuso local.

    O ERA5-Land reporta `valid_time` em UTC, sem tzinfo explícito. A RMR
    está em `America/Recife` (UTC-3, sem horário de verão desde 2019 — toda
    a janela modelada, 2020-2025, usa o mesmo offset fixo, mas a conversão
    é feita via `zoneinfo`/`tz_convert` em vez de um deslocamento
    hardcoded, para não depender dessa premissa silenciosamente).

    Args:
        da: DataArray com `valid_time` em UTC (naive, sem tzinfo).
        tz: Fuso horário IANA de destino.
        time_dim: Nome da dimensão temporal.

    Returns:
        DataArray com `valid_time` convertido para `tz` e depois com o
        tzinfo removido (mantendo o dtype naive datetime64 exigido por
        `xr.Dataset.resample`), para que o `resample("1D")` subsequente
        agrupe por dia de calendário LOCAL, não UTC.
    """
    localized = (
        pd.DatetimeIndex(da[time_dim].values)
        .tz_localize("UTC")
        .tz_convert(tz)
        .tz_localize(None)
    )
    shifted = da.copy()
    shifted[time_dim] = localized
    return shifted
```

Em `compute_daily_areal_precipitation`, altere:

```python
    logger.info("De-acumulando passos horários de '%s'", precip_var)
    ds[precip_var] = deaccumulate_precipitation(ds[precip_var], time_dim=time_dim)

    logger.info("Agregando temporalmente para total diário por pixel")
    daily_pixel = ds.resample({time_dim: "1D"}).sum(skipna=False)
```

para:

```python
    logger.info("De-acumulando passos horários de '%s'", precip_var)
    ds[precip_var] = deaccumulate_precipitation(ds[precip_var], time_dim=time_dim)

    logger.info("Corrigindo rótulo de janela de acumulação e convertendo para America/Recife")
    ds[precip_var] = align_valid_time_to_accumulation_window(ds[precip_var], time_dim=time_dim)
    ds[precip_var] = to_local_time(ds[precip_var], time_dim=time_dim)

    logger.info("Agregando temporalmente para total diário (calendário local) por pixel")
    daily_pixel = ds.resample({time_dim: "1D"}).sum(skipna=False)
```

Atualize também a docstring de `compute_daily_areal_precipitation` (lista de "Passos") para incluir os dois novos passos entre a de-acumulação e a agregação temporal.

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/data/test_preprocess.py -v
```
Expected: todos os testes do arquivo passam (os 2 pré-existentes + os 3 novos).

- [ ] **Step 5: Commit**

```bash
git add src/data/preprocess.py tests/data/test_preprocess.py
git commit -m "fix: corrigir rotulo de janela de acumulacao do valid_time e converter para America/Recife antes do resample diario"
```

---

## Task 2: Substituir bounding box pela máscara do polígono oficial da RMR

**Files:**
- Create: `src/data/rmr_polygon.py`
- Test: `tests/data/test_rmr_polygon.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produz: `get_rmr_polygon(year: int = 2018) -> shapely.geometry.base.BaseGeometry`
- Produz: `mask_by_polygon(ds: xr.Dataset, polygon: BaseGeometry, lat_dim: str = "latitude", lon_dim: str = "longitude", margin: float = 0.15) -> xr.Dataset`
- Consumido por: Task 6 (`main()` de `preprocess.py` passa a chamar estas duas funções em vez de `filter_by_bounding_box`).

- [ ] **Step 1: Adicionar as novas dependências a `requirements.txt`**

Acrescente ao final do arquivo:

```
geobr==1.0.0
geopandas==1.1.4
shapely==2.1.2
pyproj==3.7.2
pyogrio==0.13.0
duckdb==1.5.5
html5lib==1.1
lxml==6.1.1
pyarrow==25.0.0
rapidfuzz==3.14.5
```

- [ ] **Step 2: Instalar as dependências no `.venv` do worktree**

```bash
.venv/bin/python -m pip install geobr==1.0.0 geopandas==1.1.4 shapely==2.1.2 pyproj==3.7.2 pyogrio==0.13.0 duckdb==1.5.5 html5lib==1.1 lxml==6.1.1 pyarrow==25.0.0 rapidfuzz==3.14.5
```
Expected: instalação sem erro de compilação (todas têm wheel pré-compilado para este ambiente). Se a instalação falhar tentando compilar `shapely` a partir do código-fonte, o pip resolveu uma versão diferente da pinada — pare e reporte, não tente contornar com `--no-build-isolation` ou flags similares.

- [ ] **Step 3: Escrever os testes**

Crie `tests/data/test_rmr_polygon.py`:

```python
import numpy as np
import pytest
import xarray as xr
from shapely.geometry import Polygon

from src.data.rmr_polygon import get_rmr_polygon, mask_by_polygon


def test_get_rmr_polygon_returns_rm_recife_with_expected_bounds():
    polygon = get_rmr_polygon(year=2018)

    minx, miny, maxx, maxy = polygon.bounds
    # bounds verificados manualmente durante o planejamento desta task
    # (geobr.read_metro_area(year=2018), name_metro == "Rm Recife", 15 municípios)
    assert minx == pytest.approx(-35.2659685, abs=0.01)
    assert miny == pytest.approx(-8.6093568, abs=0.01)
    assert maxx == pytest.approx(-34.8069033, abs=0.01)
    assert maxy == pytest.approx(-7.4620094, abs=0.01)


def test_mask_by_polygon_keeps_only_cells_inside_polygon():
    # quadrado 2x2 graus, [0,0]-[2,2]; a malha do dataset cobre uma area maior
    square = Polygon([(0.4, 0.4), (0.4, 1.6), (1.6, 1.6), (1.6, 0.4)])

    lats = [0.0, 0.5, 1.0, 1.5, 2.0]
    lons = [0.0, 0.5, 1.0, 1.5, 2.0]
    data = np.ones((1, len(lats), len(lons)))
    ds = xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], data)},
        coords={"valid_time": [0], "latitude": lats, "longitude": lons},
    )

    masked = mask_by_polygon(ds, square, margin=0.0)

    valid = masked["tp"].isel(valid_time=0).notnull()
    # pontos estritamente dentro do quadrado [0.4,1.6]x[0.4,1.6]: (0.5,0.5),
    # (0.5,1.0), (0.5,1.5), (1.0,0.5), (1.0,1.0), (1.0,1.5), (1.5,0.5),
    # (1.5,1.0), (1.5,1.5) -> 9 pontos
    assert int(valid.sum()) == 9
    assert bool(valid.sel(latitude=0.0, longitude=0.0, method="nearest")) is False
```

- [ ] **Step 4: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/data/test_rmr_polygon.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.data.rmr_polygon'`.

- [ ] **Step 5: Implementar `src/data/rmr_polygon.py`**

```python
"""Polígono oficial da Região Metropolitana do Recife (RMR), usado para
recortar espacialmente a grade do ERA5-Land em vez de um bounding box
retangular (que inclui/exclui área real da RMR por não seguir os limites
municipais)."""

import logging

import geobr
import numpy as np
import xarray as xr
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep

logger = logging.getLogger(__name__)

METRO_AREA_NAME = "Rm Recife"


def get_rmr_polygon(year: int = 2018) -> BaseGeometry:
    """Obtém o polígono oficial da Região Metropolitana do Recife via geobr.

    Usa `geobr.read_metro_area`, que reflete a composição legal da RMR
    (base legal por município disponível na coluna `legislation` do
    GeoDataFrame retornado) — não uma lista de municípios definida à mão.

    Args:
        year: Ano de referência da malha de áreas metropolitanas do geobr.

    Returns:
        Geometria (Polygon ou MultiPolygon) da união de todos os
        municípios que compõem a RMR nesse ano de referência.

    Raises:
        ValueError: Se `name_metro == "Rm Recife"` não for encontrado
            nos dados retornados pelo geobr.
    """
    logger.info("Baixando/lendo malha de áreas metropolitanas do geobr (year=%d)", year)
    gdf = geobr.read_metro_area(year=year)
    rmr = gdf[gdf["name_metro"] == METRO_AREA_NAME]
    if rmr.empty:
        raise ValueError(f"'{METRO_AREA_NAME}' não encontrada em geobr.read_metro_area(year={year})")
    logger.info("RMR: %d município(s) encontrados", len(rmr))
    return rmr.geometry.union_all()


def mask_by_polygon(
    ds: xr.Dataset,
    polygon: BaseGeometry,
    lat_dim: str = "latitude",
    lon_dim: str = "longitude",
    margin: float = 0.15,
) -> xr.Dataset:
    """Recorta um dataset para os pixels cujo centro cai dentro de `polygon`.

    Pré-filtra pela caixa delimitadora do polígono (mais uma margem, para
    não cortar pixels de borda por alinhamento de grade) antes do teste
    ponto-a-ponto, para manter o custo baixo em grades regulares.

    Args:
        ds: Dataset xarray com coordenadas de latitude e longitude.
        polygon: Geometria de referência (ver `get_rmr_polygon`).
        lat_dim: Nome da dimensão de latitude.
        lon_dim: Nome da dimensão de longitude.
        margin: Margem (graus) adicionada ao redor da caixa delimitadora do
            polígono antes do pré-filtro.

    Returns:
        Dataset com os pixels fora do polígono marcados como NaN (mesma
        forma do recorte pré-filtrado; use `.dropna(..., how="all")` no
        chamador se quiser também remover linhas/colunas totalmente vazias).
    """
    minx, miny, maxx, maxy = polygon.bounds
    logger.info("Pré-filtrando pela caixa delimitadora do polígono (+margem %.2f)", margin)
    region = ds.sel({
        lat_dim: slice(maxy + margin, miny - margin),
        lon_dim: slice(minx - margin, maxx + margin),
    })

    lats = region[lat_dim].values
    lons = region[lon_dim].values
    prepared = prep(polygon)
    mask = np.array([[prepared.contains(Point(lon, lat)) for lon in lons] for lat in lats])
    logger.info("Máscara do polígono: %d de %d pixels dentro da RMR", mask.sum(), mask.size)

    mask_da = xr.DataArray(mask, dims=[lat_dim, lon_dim], coords={lat_dim: lats, lon_dim: lons})
    return region.where(mask_da)
```

- [ ] **Step 6: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/data/test_rmr_polygon.py -v
```
Expected: `2 passed`. O primeiro teste faz uma chamada real ao geobr (rede) — se falhar por indisponibilidade de rede, reporte isso especificamente (não é um bug de código) em vez de tentar contornar.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt src/data/rmr_polygon.py tests/data/test_rmr_polygon.py
git commit -m "feat: mascara do poligono oficial da RMR via geobr, substituindo bounding box"
```

---

## Task 3: Calcular máximo espacial e percentis altos (p90/p95) além da média areal

**Files:**
- Modify: `src/data/preprocess.py`
- Test: `tests/data/test_preprocess.py`

**Interfaces:**
- Produz: `compute_daily_spatial_stats(ds: xr.Dataset, precip_var: str = "tp", time_dim: str = "valid_time", scale_factor: float = 1000.0, percentiles: tuple = (0.9, 0.95)) -> pd.DataFrame`, colunas `mean`, `max`, `p90`, `p95`, índice `ds` (datas).
- Refatora: extrai a preparação comum (escala + de-acumulação + alinhamento temporal) de `compute_daily_areal_precipitation` para uma função privada `_daily_pixel_totals`, reaproveitada por ambas.

- [ ] **Step 1: Escrever o teste**

Adicione a `tests/data/test_preprocess.py`:

```python
def test_compute_daily_spatial_stats_returns_mean_max_and_percentiles(tiny_precip_dataset):
    stats = compute_daily_spatial_stats(tiny_precip_dataset)

    assert list(stats.columns) == ["mean", "max", "p90", "p95"]
    assert len(stats) == 2
    # o maximo espacial nunca pode ser menor que a media espacial no mesmo dia
    assert (stats["max"] >= stats["mean"]).all()
    assert (stats["p95"] >= stats["p90"]).all()
    assert (stats["max"] >= stats["p95"]).all()
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/data/test_preprocess.py -v
```
Expected: `ImportError: cannot import name 'compute_daily_spatial_stats'`. Ajuste o import no topo do teste para incluir `compute_daily_spatial_stats`.

- [ ] **Step 3: Refatorar `compute_daily_areal_precipitation` e implementar `compute_daily_spatial_stats`**

Substitua a implementação de `compute_daily_areal_precipitation` (a função inteira) por:

```python
def _daily_pixel_totals(
    ds: xr.Dataset,
    precip_var: str = "tp",
    time_dim: str = "valid_time",
    scale_factor: float = 1000.0,
) -> xr.DataArray:
    """Prepara o total diário por pixel: escala, de-acumula e alinha o tempo.

    Passos compartilhados por `compute_daily_areal_precipitation` e
    `compute_daily_spatial_stats` — mantidos em uma única função para que
    as duas nunca divirjam na definição de "total diário".

    Args:
        ds: Dataset com variável de precipitação e coordenadas espaciais.
        precip_var: Nome da variável de precipitação.
        time_dim: Nome da dimensão temporal.
        scale_factor: Fator para converter os dados originais para mm.

    Returns:
        DataArray com total diário (calendário local `America/Recife`) por
        pixel, dimensões (`ds`-como-dia, latitude, longitude).
    """
    logger.info("Convertendo '%s' para mm (fator %.1f)", precip_var, scale_factor)
    ds = ds.copy()
    ds[precip_var] = ds[precip_var] * scale_factor

    logger.info("De-acumulando passos horários de '%s'", precip_var)
    ds[precip_var] = deaccumulate_precipitation(ds[precip_var], time_dim=time_dim)

    logger.info("Corrigindo rótulo de janela de acumulação e convertendo para America/Recife")
    ds[precip_var] = align_valid_time_to_accumulation_window(ds[precip_var], time_dim=time_dim)
    ds[precip_var] = to_local_time(ds[precip_var], time_dim=time_dim)

    logger.info("Agregando temporalmente para total diário (calendário local) por pixel")
    return ds.resample({time_dim: "1D"}).sum(skipna=False)[precip_var]


def compute_daily_areal_precipitation(
    ds: xr.Dataset,
    precip_var: str = "tp",
    time_dim: str = "valid_time",
    scale_factor: float = 1000.0
) -> pd.Series:
    """Calcula a precipitação média diária sobre a área de estudo.

    Passos:
        1. Converte a variável de precipitação para milímetros (fator de escala).
        2. De-acumula os passos horários (ver `deaccumulate_precipitation`).
        3. Corrige o rótulo de janela de acumulação e converte para
           `America/Recife` (ver `align_valid_time_to_accumulation_window`,
           `to_local_time`).
        4. Agrega temporalmente para total diário (calendário local) em cada pixel.
        5. Calcula a média espacial sobre as dimensões lat/lon, ignorando NaNs.

    Args:
        ds: Dataset com variável de precipitação e coordenadas espaciais.
        precip_var: Nome da variável de precipitação.
        time_dim: Nome da dimensão temporal.
        scale_factor: Fator para converter os dados originais para mm.
            (Ex: dados originais em m -> *1000 = mm)

    Returns:
        Série pandas com índice temporal (dias locais) e valores médios
        diários de precipitação (mm).
    """
    daily_pixel = _daily_pixel_totals(ds, precip_var, time_dim, scale_factor)

    logger.info("Calculando média espacial (média de todos os pixels da região)")
    area_mean = daily_pixel.mean(dim=["latitude", "longitude"], skipna=True)

    series = area_mean.to_pandas()
    series = series.dropna()
    logger.info("Série temporal gerada com %d pontos (após remoção de NaNs)", len(series))
    return series


def compute_daily_spatial_stats(
    ds: xr.Dataset,
    precip_var: str = "tp",
    time_dim: str = "valid_time",
    scale_factor: float = 1000.0,
    percentiles: tuple = (0.9, 0.95),
) -> pd.DataFrame:
    """Calcula média, máximo e percentis altos da precipitação diária sobre a área.

    A média areal (usada como `y` do Prophet) atenua extremos localizados —
    esta função complementa com o máximo espacial e percentis altos (p90,
    p95) do dia, que preservam informação sobre picos de chuva concentrados
    em parte da RMR mesmo quando a média do dia é modesta.

    Args:
        ds: Dataset com variável de precipitação e coordenadas espaciais.
        precip_var: Nome da variável de precipitação.
        time_dim: Nome da dimensão temporal.
        scale_factor: Fator para converter os dados originais para mm.
        percentiles: Percentis altos (0-1) a calcular, além de média e máximo.

    Returns:
        DataFrame indexado por dia (local), colunas `mean`, `max`, e uma
        coluna `p{int(q*100)}` por percentil em `percentiles` (ex.: `p90`,
        `p95` para o padrão).
    """
    daily_pixel = _daily_pixel_totals(ds, precip_var, time_dim, scale_factor)

    stats = {
        "mean": daily_pixel.mean(dim=["latitude", "longitude"], skipna=True).to_pandas(),
        "max": daily_pixel.max(dim=["latitude", "longitude"], skipna=True).to_pandas(),
    }
    for q in percentiles:
        label = f"p{int(round(q * 100))}"
        stats[label] = daily_pixel.quantile(q, dim=["latitude", "longitude"], skipna=True).to_pandas()

    df = pd.DataFrame(stats).dropna(how="all")
    logger.info("Estatísticas espaciais diárias geradas com %d linhas", len(df))
    return df
```

**Nota:** o bloco acima **substitui inteiramente** a versão de `compute_daily_areal_precipitation` deixada pela Task 1 (que tinha a chamada a `align_valid_time_to_accumulation_window`/`to_local_time` embutida diretamente no corpo da função) — ao colar este Step 3 por cima, essa lógica migra para dentro de `_daily_pixel_totals` automaticamente, sem duplicação. Não é necessário editar nada manualmente além de substituir a função como indicado.

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/data/test_preprocess.py -v
```
Expected: todos os testes do arquivo passam.

- [ ] **Step 5: Commit**

```bash
git add src/data/preprocess.py tests/data/test_preprocess.py
git commit -m "feat: calcular maximo espacial e percentis p90/p95 alem da media areal"
```

---

## Task 4: Registrar metadados do processamento (período, produto, extensão espacial, variáveis, hash dos arquivos)

**Files:**
- Create: `src/data/metadata.py`
- Test: `tests/data/test_metadata.py`

**Interfaces:**
- Produz: `compute_file_hash(path: Path, chunk_size: int = 8_388_608) -> str`
- Produz: `build_processing_metadata(raw_files: list[Path], period_start: str, period_end: str, spatial_extent: dict, dataset_name: str = "reanalysis-era5-land", variable: str = "total_precipitation") -> dict`
- Produz: `write_metadata(metadata: dict, output_path: Path) -> None`

- [ ] **Step 1: Escrever os testes**

Crie `tests/data/test_metadata.py`:

```python
import hashlib
import json

from src.data.metadata import build_processing_metadata, compute_file_hash, write_metadata


def test_compute_file_hash_matches_hashlib_reference(tmp_path):
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(b"conteudo de teste" * 1000)

    result = compute_file_hash(file_path)

    expected = hashlib.sha256(file_path.read_bytes()).hexdigest()
    assert result == expected


def test_build_processing_metadata_includes_all_required_fields(tmp_path):
    raw_file = tmp_path / "precipitacao_2020_01.nc"
    raw_file.write_bytes(b"dado falso de teste")

    metadata = build_processing_metadata(
        raw_files=[raw_file],
        period_start="2020-01-01",
        period_end="2025-12-31",
        spatial_extent={"type": "rmr_metro_area_polygon", "name_metro": "Rm Recife"},
    )

    assert metadata["dataset"] == "reanalysis-era5-land"
    assert metadata["variable"] == "total_precipitation"
    assert metadata["period"] == {"start": "2020-01-01", "end": "2025-12-31"}
    assert metadata["spatial_extent"]["name_metro"] == "Rm Recife"
    assert len(metadata["raw_files"]) == 1
    assert metadata["raw_files"][0]["filename"] == "precipitacao_2020_01.nc"
    assert len(metadata["raw_files"][0]["sha256"]) == 64
    assert "generated_at" in metadata


def test_write_metadata_writes_valid_json(tmp_path):
    metadata = {"dataset": "reanalysis-era5-land", "period": {"start": "2020-01-01", "end": "2025-12-31"}}
    output_path = tmp_path / "metadata.json"

    write_metadata(metadata, output_path)

    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded == metadata
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/data/test_metadata.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.data.metadata'`.

- [ ] **Step 3: Implementar `src/data/metadata.py`**

```python
"""Registro de metadados de proveniência do processamento da série de
precipitação — período coberto, produto/variável de origem, extensão
espacial usada e hash dos arquivos brutos consumidos, para que qualquer
número publicado seja rastreável até os dados e o código que o geraram."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def compute_file_hash(path: Path, chunk_size: int = 8_388_608) -> str:
    """Calcula o hash SHA-256 de um arquivo, lendo em blocos (não carrega tudo em memória).

    Args:
        path: Caminho do arquivo.
        chunk_size: Tamanho do bloco de leitura, em bytes (padrão: 8 MiB).

    Returns:
        Hash SHA-256 em hexadecimal.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_processing_metadata(
    raw_files: List[Path],
    period_start: str,
    period_end: str,
    spatial_extent: Dict,
    dataset_name: str = "reanalysis-era5-land",
    variable: str = "total_precipitation",
) -> Dict:
    """Monta o dicionário de metadados de um run de processamento.

    Args:
        raw_files: Lista dos arquivos NetCDF brutos consumidos.
        period_start: Primeira data coberta pela série processada (ISO 8601).
        period_end: Última data coberta pela série processada (ISO 8601).
        spatial_extent: Descrição da extensão espacial usada (ex.: saída de
            `get_rmr_polygon` resumida em um dict — tipo, fonte, bounds).
        dataset_name: Nome do dataset de origem no CDS.
        variable: Nome da variável extraída do dataset de origem.

    Returns:
        Dicionário serializável em JSON com `generated_at`, `dataset`,
        `variable`, `period`, `spatial_extent` e `raw_files` (nome + hash
        SHA-256 de cada arquivo bruto consumido).
    """
    logger.info("Calculando hash de %d arquivo(s) bruto(s)", len(raw_files))
    raw_file_entries = [
        {"filename": path.name, "sha256": compute_file_hash(path)}
        for path in sorted(raw_files)
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_name,
        "variable": variable,
        "period": {"start": period_start, "end": period_end},
        "spatial_extent": spatial_extent,
        "raw_files": raw_file_entries,
    }


def write_metadata(metadata: Dict, output_path: Path) -> None:
    """Escreve os metadados em um arquivo JSON legível.

    Args:
        metadata: Dicionário de metadados (ver `build_processing_metadata`).
        output_path: Caminho do arquivo `.json` de saída.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info("Metadados salvos em: %s", output_path)
```

- [ ] **Step 4: Rodar e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/data/test_metadata.py -v
```
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/data/metadata.py tests/data/test_metadata.py
git commit -m "feat: registrar metadados de proveniencia do processamento (periodo, produto, extensao espacial, hash)"
```

---

## Task 5: Teste de sanidade — reconstrução manual independente em 3 dias amostrais reais

**Files:**
- Create: `tests/data/test_deaccumulation_sanity.py`

**Interfaces:**
- Consome: `dados/raw/precipitacao_2020_01.nc`, `dados/raw/precipitacao_2022_05.nc`, `dados/raw/precipitacao_2023_08.nc` (reais, locais — já presentes neste ambiente); `compute_daily_areal_precipitation`, `filter_by_bounding_box` (de `src.data.preprocess`).

Este teste é deliberadamente **independente** das funções `align_valid_time_to_accumulation_window`/`to_local_time`/`deaccumulate_precipitation` do pipeline: reimplementa a lógica manualmente com aritmética direta em numpy, para que a comparação com a saída do pipeline seja uma checagem de fato independente, não um teste da função contra si mesma. Os valores esperados abaixo foram verificados durante o planejamento desta task rodando exatamente este código contra os arquivos reais.

- [ ] **Step 1: Criar o teste**

Crie `tests/data/test_deaccumulation_sanity.py`:

```python
"""Teste de sanidade (Etapa 2, item 'validar manualmente a de-acumulação'):
reconstrói o total diário de precipitação a partir do NetCDF bruto, com
aritmética independente das funções de `src.data.preprocess`, e compara com
a saída do pipeline para 3 dias amostrais reais (um dia comum, um evento
extremo documentado, um dia seco).

Requer os arquivos NetCDF brutos em dados/raw/ (não versionados no git,
~8.6GB, já presentes neste ambiente de desenvolvimento) — pula
graciosamente se ausentes, para não quebrar uma instalação limpa.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.data.preprocess import compute_daily_areal_precipitation, filter_by_bounding_box

RAW_DIR = Path("dados/raw")
BBOX = {"lat_min": -8.3, "lat_max": -7.9, "lon_min": -35.2, "lon_max": -34.8}

# (arquivo, data, total independente reconstruido manualmente em mm --
# verificado durante o planejamento desta task, ver docs/superpowers/plans/
# 2026-08-06-etapa2-auditar-reconstruir-serie.md)
SAMPLE_DAYS = [
    ("precipitacao_2020_01.nc", "2020-01-02", 1.2388696670532227),
    ("precipitacao_2022_05.nc", "2022-05-25", 16.959760665893555),
    ("precipitacao_2023_08.nc", "2023-08-15", 0.3845314681529999),
]


def _require_raw_file(filename: str) -> Path:
    path = RAW_DIR / filename
    if not path.exists():
        pytest.skip(f"Arquivo bruto {path} ausente — teste de sanidade requer dados/raw/ local")
    return path


def _independent_manual_reconstruction(nc_file: Path, date_str: str) -> float:
    """Reconstrução manual do total diário, sem chamar nenhuma função de
    src.data.preprocess — usada como referência independente."""
    ds = xr.open_dataset(nc_file)
    region = ds.sel(
        latitude=slice(BBOX["lat_max"], BBOX["lat_min"]),
        longitude=slice(BBOX["lon_min"], BBOX["lon_max"]),
    )
    tp_m = region["tp"]

    raw = tp_m.values
    increments = np.empty_like(raw)
    increments[0] = raw[0]
    diffs = raw[1:] - raw[:-1]
    reset = diffs < 0
    increments[1:] = np.where(reset, raw[1:], diffs)
    increments_mm = increments * 1000.0

    times_end_label = pd.DatetimeIndex(tp_m["valid_time"].values)
    times_start_label_utc = times_end_label - pd.Timedelta(hours=1)
    times_local = times_start_label_utc.tz_localize("UTC").tz_convert("America/Recife").tz_localize(None)

    day = pd.Timestamp(date_str)
    day_mask = (times_local >= day) & (times_local < day + pd.Timedelta(days=1))
    assert day_mask.sum() == 24, f"esperado 24 passos horarios para {date_str}, obtido {day_mask.sum()}"

    daily_pixel_total = increments_mm[day_mask].sum(axis=0)
    return float(np.nanmean(daily_pixel_total))


@pytest.mark.parametrize("filename,date_str,expected_mm", SAMPLE_DAYS)
def test_pipeline_matches_independent_manual_reconstruction(filename, date_str, expected_mm):
    nc_path = _require_raw_file(filename)

    # 1. a reconstrucao manual independente bate com o valor verificado no planejamento
    manual_total = _independent_manual_reconstruction(nc_path, date_str)
    assert manual_total == pytest.approx(expected_mm, abs=1e-6)

    # 2. a saida do pipeline real (compute_daily_areal_precipitation) bate com a
    #    reconstrucao manual independente -- validacao cruzada de ponta a ponta
    ds = xr.open_dataset(nc_path)
    region = filter_by_bounding_box(ds, **BBOX)
    series = compute_daily_areal_precipitation(region)

    pipeline_value = float(series.loc[pd.Timestamp(date_str)])
    assert pipeline_value == pytest.approx(expected_mm, abs=1e-4)
```

- [ ] **Step 2: Rodar e confirmar sucesso (requer Task 1 já implementada — o pipeline precisa já ter a correção de alinhamento temporal)**

```bash
.venv/bin/python -m pytest tests/data/test_deaccumulation_sanity.py -v
```
Expected: `3 passed` (um por dia amostral), se `dados/raw/precipitacao_2020_01.nc`, `precipitacao_2022_05.nc` e `precipitacao_2023_08.nc` estiverem presentes. Se ausentes: `3 skipped`, com a razão do skip visível no output — isso também é um resultado aceitável (não é falha), mas deve ser reportado explicitamente, nunca confundido com sucesso.

- [ ] **Step 3: Commit**

```bash
git add tests/data/test_deaccumulation_sanity.py
git commit -m "test: sanidade da de-acumulacao com reconstrucao manual independente em 3 dias amostrais reais"
```

---

## Task 6: Reprocessar a série completa 2020-2025 com o pipeline corrigido

**Files:**
- Modify: `src/data/preprocess.py` (função `main`)
- Modify: `docs/escopo_e_limitacoes.md`
- Regenerate: `dados/processed/serie_prophet_rmr_2020_2025.csv`
- Create: `dados/processed/serie_estatisticas_espaciais_rmr_2020_2025.csv`
- Create: `dados/processed/metadata.json`

**Interfaces:**
- Consome: `get_rmr_polygon`, `mask_by_polygon` (Task 2), `compute_daily_areal_precipitation`, `compute_daily_spatial_stats` (Tasks 1/3), `build_processing_metadata`, `write_metadata` (Task 4).
- Requer os 72 arquivos reais em `dados/raw/` (já presentes, sem novo download) — se ausentes, esta task não pode ser executada; pare e reporte em vez de gerar dados parciais/sintéticos.

- [ ] **Step 1: Atualizar `main()` em `src/data/preprocess.py` para usar a máscara do polígono, as estatísticas espaciais e o registro de metadados**

Substitua a função `main` inteira por:

```python
def main(
    raw_data_dir: Path = Path("dados/raw"),
    processed_data_dir: Path = Path("dados/processed"),
    metro_area_year: int = 2018,
    file_pattern: str = "precipitacao_*.nc"
) -> Optional[Path]:
    """Pipeline principal de processamento.

    Args:
        raw_data_dir: Diretório com arquivos NetCDF brutos.
        processed_data_dir: Diretório onde os artefatos processados serão salvos.
        metro_area_year: Ano de referência da malha de área metropolitana
            do geobr usada para o polígono da RMR (ver `get_rmr_polygon`).
        file_pattern: Padrão para localizar os arquivos NetCDF.

    Returns:
        Caminho do CSV Prophet (`ds`, `y`) gerado, ou None em caso de erro.
        Também escreve `serie_estatisticas_espaciais_rmr_2020_2025.csv`
        (mean/max/p90/p95) e `metadata.json` no mesmo diretório.
    """
    # imports locais para nao exigir geobr/geopandas em quem so usa as
    # funcoes de agregacao temporal (Tasks 1/3) sem a mascara espacial
    from src.data.metadata import build_processing_metadata, write_metadata
    from src.data.rmr_polygon import get_rmr_polygon, mask_by_polygon

    try:
        configure_directories(raw_data_dir, processed_data_dir)

        raw_files = sorted(raw_data_dir.glob(file_pattern))
        if not raw_files:
            raise FileNotFoundError(f"Nenhum arquivo encontrado com o padrão '{raw_data_dir / file_pattern}'")

        ds_full = load_netcdf_data(raw_data_dir, file_pattern)

        polygon = get_rmr_polygon(year=metro_area_year)
        ds_region = mask_by_polygon(ds_full, polygon)

        precipitation_series = compute_daily_areal_precipitation(ds_region)
        prophet_df = prepare_prophet_dataframe(precipitation_series)

        spatial_stats_df = compute_daily_spatial_stats(ds_region)
        spatial_stats_df.index.name = "ds"

        output_file = processed_data_dir / "serie_prophet_rmr_2020_2025.csv"
        save_to_csv(prophet_df, output_file)

        stats_file = processed_data_dir / "serie_estatisticas_espaciais_rmr_2020_2025.csv"
        spatial_stats_df.reset_index().to_csv(stats_file, index=False)
        logger.info("Estatísticas espaciais salvas em: %s", stats_file)

        minx, miny, maxx, maxy = polygon.bounds
        metadata = build_processing_metadata(
            raw_files=raw_files,
            period_start=str(prophet_df["ds"].min().date()),
            period_end=str(prophet_df["ds"].max().date()),
            spatial_extent={
                "type": "rmr_metro_area_polygon",
                "source": f"geobr.read_metro_area(year={metro_area_year})",
                "name_metro": "Rm Recife",
                "bounds": [minx, miny, maxx, maxy],
            },
        )
        write_metadata(metadata, processed_data_dir / "metadata.json")

        return output_file

    except FileNotFoundError as e:
        logger.error(e)
    except KeyError as e:
        logger.error("Variável ou coordenada ausente no dataset: %s", e)
    except Exception as e:
        logger.exception("Erro inesperado durante o processamento: %s", e)

    return None
```

Adicione `from src.data.preprocess import compute_daily_spatial_stats` junto aos demais imports do módulo (já deve estar acessível, pois é definida no mesmo arquivo — apenas confirme que `compute_daily_spatial_stats` está definida acima de `main` no arquivo).

- [ ] **Step 2: Rodar o reprocessamento completo sobre os 72 arquivos reais**

```bash
time .venv/bin/python -c "
from pathlib import Path
from src.data.preprocess import main
result = main(raw_data_dir=Path('dados/raw'), processed_data_dir=Path('dados/processed'))
print('Resultado:', result)
"
```
Expected: conclui sem exceção em poucos minutos (o núcleo do processamento — abrir os 72 arquivos, recortar pela RMR e computar a série — foi cronometrado em ~19s durante o planejamento desta task; o hash SHA-256 dos 72 arquivos, ~8,6GB no total, deve adicionar mais alguns segundos a dezenas de segundos). `Resultado: dados/processed/serie_prophet_rmr_2020_2025.csv`.

- [ ] **Step 3: Verificar os artefatos gerados**

```bash
.venv/bin/python -c "
import pandas as pd, json

serie = pd.read_csv('dados/processed/serie_prophet_rmr_2020_2025.csv', parse_dates=['ds'])
print('serie_prophet: linhas=%d, colunas=%s, min=%.4f, max=%.4f' % (
    len(serie), list(serie.columns), serie['y'].min(), serie['y'].max()))
assert list(serie.columns) == ['ds', 'y']
assert serie['y'].isna().sum() == 0

stats = pd.read_csv('dados/processed/serie_estatisticas_espaciais_rmr_2020_2025.csv', parse_dates=['ds'])
print('estatisticas: linhas=%d, colunas=%s' % (len(stats), list(stats.columns)))
assert list(stats.columns) == ['ds', 'mean', 'max', 'p90', 'p95']
assert (stats['max'] >= stats['mean']).all()

with open('dados/processed/metadata.json') as f:
    meta = json.load(f)
print('metadata: dataset=%s, periodo=%s, n_raw_files=%d' % (
    meta['dataset'], meta['period'], len(meta['raw_files'])))
assert len(meta['raw_files']) == 72
assert meta['spatial_extent']['name_metro'] == 'Rm Recife'
print('OK: todos os artefatos validados')
"
```
Expected: `OK: todos os artefatos validados`, sem `AssertionError`.

- [ ] **Step 4: Atualizar `docs/escopo_e_limitacoes.md` — marcar os itens resolvidos e registrar a descoberta do bug de rótulo de janela**

Na tabela de limitações, altere as linhas dos itens 5, 6 e 7 (bounding box, fuso horário, de-acumulação não validada) de `Pendente` para `Resolvido na Etapa 2 (commit <hash do Step 6>)`. Adicione uma nova linha à tabela, logo após a linha do item 7:

```markdown
| 7b | [Descoberto na Etapa 2] `valid_time` do ERA5-Land rotulava o FIM da janela de acumulação, não o início — cada total diário incluía a última hora do dia anterior e descartava a própria última hora. Corrigido junto com o ajuste de fuso horário. | Etapa 2 | Resolvido na Etapa 2 (commit <hash do Step 6>) |
```

Substitua `<hash do Step 6>` pelo hash real do commit desta task (curto, 7 caracteres) nos dois lugares acima.

Adicione também, na seção "Limitações atuais", uma nota logo abaixo da tabela:

```markdown
**Nota (Etapa 2):** `dados/processed/flagged_prophet_rmr_2020_2025.csv` (saída do
Prophet gerada no notebook 02) ficou desatualizado após a correção da série
nesta etapa — foi calculado sobre a série anterior, não corrigida. Será
regenerado quando o Prophet for reajustado (Etapa 3); não deve ser citado
no texto final do TCC até lá.
```

- [ ] **Step 5: Rodar a suíte de testes de `src/data/` para confirmar que nada quebrou**

```bash
.venv/bin/python -m pytest tests/data/ -v
```
Expected: todos os testes passam (incluindo os de `test_deaccumulation_sanity.py`, que devem passar de verdade agora, não pular, já que os dados reais estão presentes).

- [ ] **Step 6: Commit**

```bash
git add src/data/preprocess.py dados/processed/serie_prophet_rmr_2020_2025.csv dados/processed/serie_estatisticas_espaciais_rmr_2020_2025.csv docs/escopo_e_limitacoes.md
git commit -m "data: reprocessar serie 2020-2025 com poligono da RMR, fuso America/Recife e correcao de rotulo de janela de acumulacao"
```

**Nota:** `dados/processed/metadata.json` é gerado localmente mas não listado no `git add` acima — decidir junto ao autor se metadados de proveniência devem ser versionados (útil para reprodutibilidade) ou ficar fora do controle de versão (o arquivo é pequeno, não há razão técnica forte para excluí-lo; se o autor preferir versioná-lo, adicionar `dados/processed/metadata.json` ao commit acima).

---

## Self-Review

- **Cobertura da Etapa 2 do prompt original:**
  - "Definir o dia em America/Recife... documentando a escolha" → Task 1 (`to_local_time`, com docstring explicando a ausência de horário de verão e o uso de `zoneinfo`/`tz_convert`).
  - "Validar manualmente a de-acumulação... reconstruindo o total a partir do NetCDF bruto e comparando com o CSV final. Registrar em teste de sanidade" → Task 5, com reconstrução independente (sem chamar as funções do pipeline) em 3 dias reais, e descoberta de um bug real (rótulo de janela de acumulação) documentada como premissa desta etapa e corrigida na Task 1.
  - "Substituir o bounding box por máscara do polígono da RMR" → Task 2, via `geobr.read_metro_area`, fonte oficial e legalmente referenciada.
  - "Produzir, além da média areal, o máximo espacial e um percentil espacial alto (p90/p95)" → Task 3.
  - "Registrar metadados do download: período, versão do produto, coordenadas, variáveis e hash do arquivo" → Task 4 + Task 6 (aplicado ao run real).
  - "Esta etapa pode alterar todos os números posteriores. Nenhum resultado anterior deve ser reaproveitado depois dela" → Global Constraints + Task 6 Step 4 (nota explícita sobre `flagged_prophet_rmr_2020_2025.csv` ficar stale).
- **Placeholder scan:** nenhuma task usa "TBD"/"preencher depois". Todos os valores numéricos citados nos testes (bounds do polígono, totais dos 3 dias amostrais, tempo de execução) foram verificados rodando o código real contra os dados reais durante o planejamento, não estimados.
- **Consistência de tipos e assinaturas:** `_daily_pixel_totals` (Task 3) é a única função que aplica escala + de-acumulação + alinhamento temporal, reaproveitada por `compute_daily_areal_precipitation` (existente, contrato preservado: retorna `pd.Series`) e `compute_daily_spatial_stats` (nova: retorna `pd.DataFrame` com colunas `mean`/`max`/`p90`/`p95`) — os dois nunca podem divergir na definição de "total diário" porque compartilham a mesma preparação. `get_rmr_polygon`/`mask_by_polygon` (Task 2) são consumidas exatamente com essa assinatura em `main()` (Task 6). `build_processing_metadata`/`write_metadata` (Task 4) idem.
- **Dependência entre tasks:** Task 3 reimplementa trechos de código que a Task 1 já inseriu em `compute_daily_areal_precipitation` — o Step 3 da Task 3 inclui uma nota explícita instruindo a remover a duplicação ao consolidar em `_daily_pixel_totals`, para quem executar as tasks em sequência (o caso normal) não ficar com código duplicado.
