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
