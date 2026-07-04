from src.data.download import build_filename


def test_build_filename_matches_existing_raw_data_convention():
    assert build_filename(2020, 1) == "precipitacao_2020_01.nc"
    assert build_filename(2025, 12) == "precipitacao_2025_12.nc"
