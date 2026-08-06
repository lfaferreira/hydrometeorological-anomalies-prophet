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


def test_mask_by_polygon_crops_to_bbox_and_masks_points_outside_polygon():
    # forma em "L": para lon em [0.4,0.9] o poligono cobre lat completo
    # [0.4,1.6]; para lon em [0.9,1.6] so cobre lat [0.4,0.9] -- garante
    # pontos dentro da caixa delimitadora (usada no pre-filtro) que ainda
    # assim ficam fora do poligono, testando mascaramento e recorte
    # separadamente.
    l_shape = Polygon([
        (0.4, 0.4), (0.4, 1.6), (0.9, 1.6), (0.9, 0.9), (1.6, 0.9), (1.6, 0.4),
    ])

    lats = [0.0, 0.5, 1.0, 1.5, 2.0]
    lons = [0.0, 0.5, 1.0, 1.5, 2.0]
    data = np.ones((1, len(lats), len(lons)))
    ds = xr.Dataset(
        {"tp": (["valid_time", "latitude", "longitude"], data)},
        coords={"valid_time": [0], "latitude": lats, "longitude": lons},
    )

    masked = mask_by_polygon(ds, l_shape, margin=0.0)

    # o recorte (crop) elimina pontos fora da caixa delimitadora do
    # poligono ([0.4,1.6]): 0.0 e 2.0 nao devem sequer existir na saida.
    assert list(masked["latitude"].values) == [0.5, 1.0, 1.5]
    assert list(masked["longitude"].values) == [0.5, 1.0, 1.5]

    valid = masked["tp"].isel(valid_time=0).notnull()
    # dentro da caixa recortada (3x3=9 pontos), so os que realmente caem
    # dentro do poligono em L continuam validos -- 5 dos 9.
    assert int(valid.sum()) == 5
    assert bool(valid.sel(latitude=0.5, longitude=0.5)) is True
    assert bool(valid.sel(latitude=1.5, longitude=0.5)) is True
    assert bool(valid.sel(latitude=1.0, longitude=1.0)) is False
    assert bool(valid.sel(latitude=1.5, longitude=1.5)) is False
