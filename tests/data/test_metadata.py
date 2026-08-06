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
