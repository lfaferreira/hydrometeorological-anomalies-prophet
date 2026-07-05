import numpy as np
import pandas as pd

from src.data.harmonize import harmonize_sources


def test_harmonize_sources_prefers_first_priority_and_fills_gaps():
    era5 = pd.DataFrame({"ds": pd.to_datetime(["2022-05-25", "2022-05-26"]), "y": [40.0, 20.0]})
    inmet = pd.DataFrame({"ds": pd.to_datetime(["2022-05-25", "2022-05-26"]), "y": [np.nan, 22.0]})

    result = harmonize_sources({"inmet": inmet, "era5": era5}, priority=["inmet", "era5"])

    row_25 = result.loc[result["ds"] == pd.Timestamp("2022-05-25")].iloc[0]
    row_26 = result.loc[result["ds"] == pd.Timestamp("2022-05-26")].iloc[0]

    # 25/05: INMET é NaN -> cai para ERA5
    assert row_25["y"] == 40.0
    assert row_25["source"] == "era5"
    # 26/05: INMET tem valor -> usa INMET
    assert row_26["y"] == 22.0
    assert row_26["source"] == "inmet"
