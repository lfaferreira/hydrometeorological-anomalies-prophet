"""
Script para download de dados de precipitação do ERA5-Land via CDS usando earthkit-data.
Os arquivos brutos são salvos em 'dados/raw/' no formato NetCDF, um por ano.
"""
import sys
import calendar
from pathlib import Path
import logging
import earthkit.data as ekd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

# Período de interesse
ANO_INICIO = 2020
ANO_FIM = 2025

# Área geográfica: [Norte, Oeste, Sul, Leste] do Brasil (aproximado)
AREA_BRASIL = [5.0, -75.0, -35.0, -34.0]

# Dataset ERA5-Land no CDS
DATASET = "reanalysis-era5-land"
VARIAVEL = "total_precipitation"

# Diretório de saída (relativo à raiz do projeto)
RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "dados" / "raw"

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def criar_diretorio_saida():
    """Cria o diretório de saída, se não existir."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Diretório de saída: {RAW_DATA_DIR}")

def baixar_mes(ano, mes):
    """
    Baixa os dados de precipitação para um ano inteiro e salva em NetCDF.
    Divide em meses para evitar requisições muito grandes e junta depois.
    """
    arquivo_nc = RAW_DATA_DIR / f"precipitacao_{ano}_{mes:02d}.nc"
    
    if arquivo_nc.exists():
        logger.info(f"Arquivo {arquivo_nc.name} já existe. Pulando.")
        return

    logger.info(f"Baixando {ano}-{mes:02d}...")
    
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    dias_validos = [f"{d:02d}" for d in range(1, ultimo_dia_do_mes + 1)]

    request = {
        "variable": VARIAVEL,
        "year": str(ano),
        "month": f"{mes:02d}",
        "day": dias_validos,
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": AREA_BRASIL,
        "format": "netcdf",
    }

    try:
        data = ekd.from_source("cds", DATASET, request)
        
        data.save(str(arquivo_nc)) 
        
        logger.info(f"Arquivo NetCDF salvo com sucesso: {arquivo_nc.name}")
        
    except Exception as e:
        logger.error(f"Falha no download {ano}-{mes:02d}: {e}")
        if arquivo_nc.exists(): 
            arquivo_nc.unlink()
        raise

def baixar_periodo():
    """Executa o download para todos os anos do período definido."""
    logger.info(f"Iniciando download para o período {ANO_INICIO}-{ANO_FIM}.")
    criar_diretorio_saida()
    
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        for mes in range(1, 13):
            try:
                baixar_mes(ano, mes)
            except KeyboardInterrupt:
                logger.warning("Download interrompido pelo usuário.")
                sys.exit(1)
            except Exception:
                logger.error(f"Erro ao baixar {ano}-{mes:02d}. Continuando para o próximo mês...")
                continue
                
    logger.info("Todos os downloads foram processados.")

# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    baixar_periodo()