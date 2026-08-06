"""Guarda de regressão da Etapa 1 (congelamento de objetivo e claims): impede
que o objetivo declarado do projeto e o documento de escopo voltem a afirmar
capacidades de previsão, alerta antecipado ou modelagem de risco de inundação
que o pipeline não implementa (ver docs/escopo_e_limitacoes.md)."""

from pathlib import Path

import nbformat

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FROZEN_OBJECTIVE = (
    "avaliar se um modelo Prophet é capaz de identificar retrospectivamente "
    "anomalias de precipitação média diária na Região Metropolitana do "
    "Recife (RMR), comparando seu desempenho com métodos climatológicos "
    "simples e com eventos extremos documentados"
)

# Frase específica da moldura antiga (aplicação a "inundação urbana") que não
# deve reaparecer no README — não confundir com o item 3 do catálogo de
# não-objetivos de docs/escopo_e_limitacoes.md, que legitimamente *nega*
# "risco de inundação" e por isso não pode ser testado como frase proibida.
FORBIDDEN_README_PHRASES = ["inundação urbana"]

REQUIRED_ESCOPO_NON_GOALS = [
    "não é um sistema de previsão",
    "não emite alerta antecipado",
    "não modela risco de inundação",
    "não é benchmark de acurácia",
]

NOTEBOOK_NAMES = [
    "01_pre_processing_data.ipynb",
    "02_prophet_modeling.ipynb",
    "03_validation.ipynb",
]


def test_readme_states_frozen_retrospective_objective():
    content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert FROZEN_OBJECTIVE in content


def test_readme_does_not_claim_flood_risk_application():
    content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in FORBIDDEN_README_PHRASES:
        assert phrase not in content, f"README.md ainda contém a frase de overreach: {phrase!r}"


def test_escopo_e_limitacoes_doc_exists_and_lists_non_goals():
    path = PROJECT_ROOT / "docs" / "escopo_e_limitacoes.md"
    assert path.exists(), "docs/escopo_e_limitacoes.md precisa existir (deliverable da Etapa 1)"
    content = path.read_text(encoding="utf-8").lower()
    for phrase in REQUIRED_ESCOPO_NON_GOALS:
        assert phrase in content, f"docs/escopo_e_limitacoes.md não menciona: {phrase!r}"


def test_notebooks_have_scope_disclaimer_banner():
    for name in NOTEBOOK_NAMES:
        nb = nbformat.read(PROJECT_ROOT / "notebooks" / name, as_version=4)
        first_cell = nb.cells[0]
        source = "".join(first_cell.source) if isinstance(first_cell.source, list) else first_cell.source
        assert first_cell.cell_type == "markdown", f"{name}: primeira célula deveria ser markdown"
        assert "docs/escopo_e_limitacoes.md" in source, f"{name}: banner não referencia docs/escopo_e_limitacoes.md"
        assert "provisóri" in source.lower(), f"{name}: banner não avisa que números são provisórios"
