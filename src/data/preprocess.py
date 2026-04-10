"""Processamento de dados de precipitação de arquivos NetCDF para uso no Prophet.

Este módulo carrega múltiplos arquivos NetCDF, filtra uma região de interesse,
agrega espacial e temporalmente os dados e gera um CSV pronto para modelagem
com o Facebook Prophet.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import xarray as xr

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def configure_directories(raw_dir: Path, processed_dir: Path) -> None:
    """Garante que os diretórios necessários existam.

    Args:
        raw_dir: Diretório onde estão os arquivos brutos NetCDF.
        processed_dir: Diretório onde os dados processados serão salvos.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Diretórios configurados: raw='%s', processed='%s'", raw_dir, processed_dir)


def load_netcdf_data(raw_dir: Path, file_pattern: str = "precipitacao_*.nc") -> xr.Dataset:
    """Carrega múltiplos arquivos NetCDF combinando por coordenadas.

    Args:
        raw_dir: Diretório contendo os arquivos.
        file_pattern: Padrão de nome dos arquivos (curinga '*' permitido).

    Returns:
        Dataset xarray combinado.

    Raises:
        FileNotFoundError: Se nenhum arquivo corresponder ao padrão.
    """
    pattern = raw_dir / file_pattern
    files = sorted(raw_dir.glob(file_pattern))

    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado com o padrão '{pattern}'")

    logger.info("Carregando %d arquivo(s) NetCDF: %s", len(files), [f.name for f in files])
    # Converte para string para evitar problemas de Path com open_mfdataset
    ds = xr.open_mfdataset(str(pattern), combine="by_coords")
    logger.info("Dataset carregado. Dimensões: %s", dict(ds.dims))
    return ds


def filter_by_bounding_box(
    ds: xr.Dataset,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    lat_dim: str = "latitude",
    lon_dim: str = "longitude"
) -> xr.Dataset:
    """Filtra o dataset por uma caixa delimitadora (bounding box).

    Args:
        ds: Dataset xarray com coordenadas de latitude e longitude.
        lat_min: Latitude mínima (sul).
        lat_max: Latitude máxima (norte).
        lon_min: Longitude mínima (oeste).
        lon_max: Longitude máxima (leste).
        lat_dim: Nome da dimensão de latitude.
        lon_dim: Nome da dimensão de longitude.

    Returns:
        Dataset recortado espacialmente.
    """
    logger.info("Filtrando região: lat=[%s, %s], lon=[%s, %s]", lat_min, lat_max, lon_min, lon_max)
    region = ds.sel(
        {lat_dim: slice(lat_max, lat_min), lon_dim: slice(lon_min, lon_max)}
    )
    logger.info("Novas dimensões após filtro: %s", dict(region.dims))
    return region


def compute_daily_areal_precipitation(
    ds: xr.Dataset,
    precip_var: str = "tp",
    time_dim: str = "valid_time",
    scale_factor: float = 1000.0
) -> pd.Series:
    """Calcula a precipitação média diária sobre a área de estudo.

    Passos:
        1. Converte a variável de precipitação para milímetros (fator de escala).
        2. Agrega temporalmente para total diário em cada pixel.
        3. Calcula a média espacial sobre as dimensões lat/lon, ignorando NaNs.

    Args:
        ds: Dataset com variável de precipitação e coordenadas espaciais.
        precip_var: Nome da variável de precipitação.
        time_dim: Nome da dimensão temporal.
        scale_factor: Fator para converter os dados originais para mm.
            (Ex: dados originais em m -> *1000 = mm)

    Returns:
        Série pandas com índice temporal e valores médios diários de precipitação (mm).
    """
    logger.info("Convertendo '%s' para mm (fator %.1f)", precip_var, scale_factor)
    ds[precip_var] = ds[precip_var] * scale_factor

    logger.info("Agregando temporalmente para total diário por pixel")
    daily_pixel = ds.resample({time_dim: "1D"}).sum(skipna=False)

    logger.info("Calculando média espacial (média de todos os pixels da região)")
    area_mean = daily_pixel.mean(dim=["latitude", "longitude"], skipna=True)

    # Converte para DataFrame e depois para Series para facilitar limpeza
    series = area_mean[precip_var].to_pandas()
    series = series.dropna()
    logger.info("Série temporal gerada com %d pontos (após remoção de NaNs)", len(series))
    return series


def prepare_prophet_dataframe(series: pd.Series, time_name: str = "ds", value_name: str = "y") -> pd.DataFrame:
    """Converte uma série temporal no formato exigido pelo Facebook Prophet.

    Args:
        series: Série com índice temporal e valores numéricos.
        time_name: Nome da coluna de tempo no DataFrame de saída.
        value_name: Nome da coluna de valores no DataFrame de saída.

    Returns:
        DataFrame com colunas 'ds' (datas) e 'y' (valores).
    """
    df = series.reset_index()
    df.columns = [time_name, value_name]
    logger.info("DataFrame Prophet criado com %d linhas", len(df))
    return df


def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Salva o DataFrame em um arquivo CSV.

    Args:
        df: DataFrame a ser salvo.
        output_path: Caminho completo do arquivo de saída.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Dados salvos com sucesso em: %s", output_path)


def main(
    raw_data_dir: Path = Path("dados/raw"),
    processed_data_dir: Path = Path("dados/processed"),
    lat_north: float = -7.9,
    lat_south: float = -8.3,
    lon_west: float = -35.2,
    lon_east: float = -34.8,
    file_pattern: str = "precipitacao_*.nc"
) -> Optional[Path]:
    """Pipeline principal de processamento.

    Args:
        raw_data_dir: Diretório com arquivos NetCDF brutos.
        processed_data_dir: Diretório onde o CSV será salvo.
        lat_north: Latitude norte (máxima) da região.
        lat_south: Latitude sul (mínima) da região.
        lon_west: Longitude oeste (mínima) da região.
        lon_east: Longitude leste (máxima) da região.
        file_pattern: Padrão para localizar os arquivos NetCDF.

    Returns:
        Caminho do arquivo CSV gerado ou None em caso de erro.
    """
    try:
        configure_directories(raw_data_dir, processed_data_dir)

        ds_full = load_netcdf_data(raw_data_dir, file_pattern)

        # Ajusta a ordem dos argumentos: lat_max (north), lat_min (south)
        ds_region = filter_by_bounding_box(
            ds_full,
            lat_min=lat_south,
            lat_max=lat_north,
            lon_min=lon_west,
            lon_max=lon_east
        )

        precipitation_series = compute_daily_areal_precipitation(ds_region)

        prophet_df = prepare_prophet_dataframe(precipitation_series)

        output_file = processed_data_dir / "serie_prophet_rmr_2020_2025.csv"
        save_to_csv(prophet_df, output_file)

        return output_file

    except FileNotFoundError as e:
        logger.error(e)
    except KeyError as e:
        logger.error("Variável ou coordenada ausente no dataset: %s", e)
    except Exception as e:
        logger.exception("Erro inesperado durante o processamento: %s", e)

    return None


if __name__ == "__main__":
    output_path = main()
    if output_path:
        print(f"Sucesso! Arquivo gerado: {output_path}")
    else:
        print("Falha no processamento. Verifique os logs para mais detalhes.")