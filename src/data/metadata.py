"""Registro de metadados de proveniência do processamento da série de
precipitação — período coberto, produto/variável de origem, extensão
espacial usada e hash dos arquivos brutos consumidos, para que qualquer
número publicado seja rastreável até os DADOS que o geraram.

Limitação conhecida: nenhum identificador do código (commit git, versão do
pacote) é registrado aqui, então a proveniência cobre a entrada, não a
transformação — reproduzir um número exige saber, por fora, em que commit a
série foi gerada. Fechar essa lacuna é item da Etapa 8 (reprodutibilidade e
engenharia) do plano de correção."""

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
