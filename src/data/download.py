"""
Script para download de dados de precipitação do ERA5-Land via CDS usando earthkit-data.
Os arquivos brutos são salvos em 'dados/raw/' no formato NetCDF, um por mês.
"""

import calendar
import logging
import sys
from pathlib import Path
from typing import List, Optional
import earthkit.data as ekd

START_YEAR = 2020
END_YEAR = 2025

# Área geográfica: [Norte, Oeste, Sul, Leste] - Brasil
AREA_BRAZIL: List[float] = [5.0, -75.0, -35.0, -34.0]

DATASET_NAME = "reanalysis-era5-land"
VARIABLE = "total_precipitation"

# Diretório de saída: assume que o script está em um subdiretório do projeto.
# Ajuste conforme sua estrutura. Exemplo: script em src/data/, raw em dados/raw/
RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "dados" / "raw"

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def ensure_directory_exists(directory: Path) -> None:
    """Cria o diretório (e pais necessários) se não existir.

    Args:
        directory: Caminho do diretório a ser criado.
    """
    directory.mkdir(parents=True, exist_ok=True)
    logger.info("Diretório de saída: %s", directory)


def build_cds_request(year: int, month: int, area: List[float]) -> dict:
    """Constrói o dicionário de requisição para o CDS.

    Args:
        year: Ano do download.
        month: Mês do download (1-12).
        area: Lista com [Norte, Oeste, Sul, Leste].

    Returns:
        Dicionário pronto para ser usado em ekd.from_source.
    """
    last_day = calendar.monthrange(year, month)[1]
    days = [f"{d:02d}" for d in range(1, last_day + 1)]
    hours = [f"{h:02d}:00" for h in range(24)]

    return {
        "variable": VARIABLE,
        "year": str(year),
        "month": f"{month:02d}",
        "day": days,
        "time": hours,
        "area": area,
        "format": "netcdf",
    }


def download_monthly_data(year: int, month: int, output_dir: Path, area: List[float]) -> Optional[Path]:
    """Baixa os dados de um mês específico e salva em NetCDF.

    Args:
        year: Ano alvo.
        month: Mês alvo (1-12).
        output_dir: Diretório onde o arquivo será salvo.
        area: Bounding box [Norte, Oeste, Sul, Leste].

    Returns:
        Caminho do arquivo salvo, ou None em caso de falha.

    Raises:
        Exception: Repassa exceções da API do CDS ou de E/S.
    """
    filename = output_dir / f"precipitation_{year}_{month:02d}.nc"

    if filename.exists():
        logger.info("Arquivo %s já existe. Pulando.", filename.name)
        return filename

    logger.info("Baixando %d-%02d...", year, month)
    request = build_cds_request(year, month, area)

    try:
        data = ekd.from_source("cds", DATASET_NAME, request)
        data.save(str(filename))
        logger.info("Arquivo salvo: %s", filename.name)
        return filename
    except Exception as e:
        logger.error("Falha no download %d-%02d: %s", year, month, e)
        # Remove arquivo parcial se existir
        if filename.exists():
            filename.unlink()
        raise

def download_period(
    start_year: int,
    end_year: int,
    output_dir: Path,
    area: List[float],
    stop_on_error: bool = False,
) -> None:
    """Executa o download para todos os meses no intervalo de anos.

    Args:
        start_year: Primeiro ano do período.
        end_year: Último ano (inclusive).
        output_dir: Diretório de destino dos arquivos.
        area: Bounding box geográfica.
        stop_on_error: Se True, interrompe o programa ao primeiro erro.
                       Se False, continua para o próximo mês.
    """
    logger.info("Iniciando download para o período %d-%d.", start_year, end_year)
    ensure_directory_exists(output_dir)

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            try:
                download_monthly_data(year, month, output_dir, area)
            except KeyboardInterrupt:
                logger.warning("Download interrompido pelo usuário.")
                sys.exit(1)
            except Exception as e:
                logger.error("Erro ao baixar %d-%02d: %s", year, month, e)
                if stop_on_error:
                    logger.error("Parando devido a stop_on_error=True")
                    sys.exit(1)
                continue

    logger.info("Todos os downloads foram processados.")


def main() -> None:
    """Função principal que orquestra o download."""
    download_period(
        start_year=START_YEAR,
        end_year=END_YEAR,
        output_dir=RAW_DATA_DIR,
        area=AREA_BRAZIL,
        stop_on_error=False,  # Altere para True se quiser parar no primeiro erro
    )


if __name__ == "__main__":
    main()