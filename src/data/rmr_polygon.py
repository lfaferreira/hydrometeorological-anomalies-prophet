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


def _bounds_slice(coord_values: np.ndarray, lo: float, hi: float) -> slice:
    """Monta um `slice(lo, hi)` respeitando a ordem (crescente ou decrescente)
    da coordenada, já que o `.sel` do xarray exige que os limites do slice
    sigam a mesma direção do índice (ERA5-Land usa latitude decrescente;
    grades sintéticas em testes costumam ser crescentes)."""
    if len(coord_values) >= 2 and coord_values[0] > coord_values[-1]:
        return slice(hi, lo)
    return slice(lo, hi)


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
        lat_dim: _bounds_slice(ds[lat_dim].values, miny - margin, maxy + margin),
        lon_dim: _bounds_slice(ds[lon_dim].values, minx - margin, maxx + margin),
    })

    lats = region[lat_dim].values
    lons = region[lon_dim].values
    prepared = prep(polygon)
    mask = np.array([[prepared.contains(Point(lon, lat)) for lon in lons] for lat in lats])
    logger.info("Máscara do polígono: %d de %d pixels dentro da RMR", mask.sum(), mask.size)

    mask_da = xr.DataArray(mask, dims=[lat_dim, lon_dim], coords={lat_dim: lats, lon_dim: lons})
    return region.where(mask_da)
