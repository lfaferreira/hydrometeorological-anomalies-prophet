# Etapa 1 — Congelar Objetivo e Claims — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Congelar o objetivo declarado do projeto na moldura de detecção retrospectiva de anomalias (não previsão, não alerta antecipado, não risco de inundação), reescrevendo o objetivo em `README.md` e criando `docs/escopo_e_limitacoes.md` como registro vivo do que o trabalho não é e do que ainda está pendente de correção nas etapas seguintes.

**Architecture:** Mudança puramente documental (README, novo documento de escopo, nota de contexto em `docs/projeto_de_pesquisa.md`, banner de aviso nos três notebooks). Nenhum módulo de `src/` é alterado nesta etapa — a auditoria e correção da série (Etapa 2) e a avaliação out-of-sample (Etapa 3) vêm depois e podem invalidar números, mas não o objetivo aqui congelado. Um teste de regressão (`tests/test_scope_documentation.py`) impede que a linguagem de "previsão"/"alerta antecipado"/"inundação urbana" volte a aparecer como capacidade do sistema nos documentos declarativos do projeto.

**Tech Stack:** Python 3.12, `nbformat` (edição de notebooks, já instalado no `.venv` conforme confirmado na auditoria — nenhuma dependência nova), `pytest`.

## Global Constraints

- **Não editar `docs/projeto_de_pesquisa.md` como se reescrevesse a proposta original.** Esse arquivo é um resumo do PDF formalmente submetido ao curso — é registro histórico. Esta etapa só pode **adicionar uma nota de contexto** apontando para `docs/escopo_e_limitacoes.md`; não pode alterar a extração do conteúdo original.
- **Não reescrever a prosa de discussão dos notebooks 02/03 nesta etapa.** Os números atuais (58 anomalias, precisão 0,069 etc.) serão inteiramente regerados pela Etapa 2 (auditoria da série) e Etapa 3 (backtesting out-of-sample); reescrever a interpretação desses números agora seria trabalho descartado. Esta etapa só adiciona um banner de aviso no topo de cada notebook apontando para `docs/escopo_e_limitacoes.md` — a reescrita de conclusões é explicitamente Etapa 10.
- **Escopo geográfico permanece exclusivamente a RMR** — mesma restrição de `docs/superpowers/plans/2026-07-05-rigor-metodologico-tcc.md`.
- Ambiente: `.venv` na raiz do projeto. Use `.venv/bin/python -m pytest ...` (não `.venv/bin/pytest` diretamente — o binário tem shebang quebrado neste ambiente, mesma observação já registrada no plano de 2026-07-05).
- Commits pequenos e frequentes, um por task concluída.

---

## Task 1: Congelar o objetivo em `README.md` e criar `docs/escopo_e_limitacoes.md`

**Files:**
- Create: `tests/test_scope_documentation.py`
- Modify: `README.md`
- Create: `docs/escopo_e_limitacoes.md`
- Modify: `docs/projeto_de_pesquisa.md`

**Interfaces:**
- Nenhuma função de `src/` — mudança documental testada por leitura direta de arquivo.
- Produz: constantes `FROZEN_OBJECTIVE` e `FORBIDDEN_OVERREACH_PHRASES` em `tests/test_scope_documentation.py`, reaproveitadas pela Task 2.

- [ ] **Step 1: Escrever os testes de regressão (devem falhar antes das mudanças)**

Crie `tests/test_scope_documentation.py`:

```python
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
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
.venv/bin/python -m pytest tests/test_scope_documentation.py -v
```

Expected: `test_readme_states_frozen_retrospective_objective` FAIL (frase ainda não está no README), `test_readme_does_not_claim_flood_risk_application` PASS (a frase antiga ainda está lá, então nada a reportar ainda — na verdade este teste também deve FALHAR agora, já que a frase proibida `"inundação urbana"` ainda está presente em `README.md:4`), `test_escopo_e_limitacoes_doc_exists_and_lists_non_goals` FAIL (`FileNotFoundError`/`AssertionError`, arquivo não existe), `test_notebooks_have_scope_disclaimer_banner` FAIL (banner ainda não existe — ver Task 2). Confirme que pelo menos os três primeiros falham antes de prosseguir.

- [ ] **Step 3: Reescrever o cabeçalho de `README.md`**

Troque as linhas 1-4 atuais:

```markdown
# hydrometeorological-anomalies-prophet

TCC (MBA Data Science e Analytics — USP/ESALQ): detecção de anomalias em séries
hidrometeorológicas com Prophet, aplicada a eventos extremos de inundação urbana no Brasil.
```

por:

```markdown
# hydrometeorological-anomalies-prophet

TCC (MBA Data Science e Analytics — USP/ESALQ). Objetivo congelado (ver
`docs/escopo_e_limitacoes.md`): avaliar se um modelo Prophet é capaz de
identificar retrospectivamente anomalias de precipitação média diária na
Região Metropolitana do Recife (RMR), comparando seu desempenho com métodos
climatológicos simples e com eventos extremos documentados.

Este projeto **não** prevê chuva, **não** emite alerta antecipado e **não**
modela risco de inundação — ver
[`docs/escopo_e_limitacoes.md`](docs/escopo_e_limitacoes.md) para o escopo
completo e as limitações conhecidas.
```

- [ ] **Step 4: Criar `docs/escopo_e_limitacoes.md`**

```markdown
# Escopo e Limitações

> Documento vivo: cada etapa do plano de correção metodológica
> (`docs/superpowers/plans/`) deve atualizar a tabela de limitações abaixo ao
> ser concluída. Última atualização: 2026-08-05 (Etapa 1 — congelamento de
> objetivo e claims).

## Objetivo congelado

Avaliar se um modelo Prophet é capaz de identificar retrospectivamente
anomalias de precipitação média diária na Região Metropolitana do Recife
(RMR), comparando seu desempenho com métodos climatológicos simples e com
eventos extremos documentados.

Qualquer afirmação no restante deste repositório que descreva o projeto de
forma diferente desta frase — em especial usando os termos "previsão",
"alerta antecipado" ou "risco de inundação" como capacidade do sistema — é
imprecisa e deve ser corrigida para esta linguagem.

## O que este trabalho não é

- **Não é um sistema de previsão de chuva.** O Prophet é ajustado apenas com
  a data (`ds`); não há preditor meteorológico prospectivo algum. A
  "detecção" compara o valor `y` já observado com o intervalo que o modelo
  gerou para aquele dia — é diagnóstico retrospectivo, não prognóstico.
- **Não emite alerta antecipado.** Não há nenhum mecanismo que sinalize uma
  anomalia antes do dia em que a precipitação ocorreu.
- **Não modela risco de inundação.** Não há nível de rio, vazão, umidade
  antecedente do solo, topografia, capacidade de drenagem, maré ou
  vulnerabilidade socioeconômica — apenas precipitação média diária de uma
  área da RMR. Precipitação anômala não é sinônimo de risco de inundação.
- **Não é benchmark de acurácia contra a APAC.** A comparação com os níveis
  simplificados da APAC (ver Etapa 7 do plano de correção) é uma análise
  exploratória de concordância entre categorias, não uma medição de
  acurácia — os critérios são incompatíveis por construção (suporte
  espacial, janela temporal, natureza prospectiva vs. retrospectiva; ver
  `docs/apac_metodologia.md`).
- **Não funde INMET/CEMADEN como fontes principais.** Essas fontes são
  usadas apenas como validação externa (correlação, viés, RMSE) da série
  ERA5-Land — nunca fundidas por prioridade de fonte, o que criaria
  descontinuidades artificiais que o Prophet leria como anomalia (ver
  Etapa 9 do plano de correção).
- **Não cobre outra região além da RMR.** Nenhuma etapa do plano de correção
  introduz outra região.

## Limitações atuais, pendentes de correção pelo plano de correção metodológica

| # | Limitação | Etapa que resolve | Status |
|---|---|---|---|
| 1 | Métricas centrais (precisão, recall, F1) são calculadas com o forecast gerado sobre a série inteira (treino+teste) — in-sample, não preditivo | Etapa 3 | Pendente |
| 2 | Os dois eventos de maio/2022 formam um bloco de 9 dias correlacionados, contados como observações independentes | Etapas 5/6 | Pendente |
| 3 | Precisão não identificável: os falsos positivos misturam eventos reais não catalogados, chuva sem impacto e alarmes espúrios | Etapa 6 | Pendente (pode permanecer não identificável mesmo após a Etapa 6 — ver nota abaixo) |
| 4 | Comparação com a APAC incompatível por construção (limiar diário retrospectivo vs. observação prospectiva em 3h/4 postos; nível "alerta" ≥100mm inalcançável na série, máximo histórico ~89,96mm) | Etapa 7 | Pendente |
| 5 | Bounding box (não polígono da RMR) usado para a média espacial | Etapa 2 | Pendente |
| 6 | Sem ajuste de fuso horário — agregação diária em UTC, não `America/Recife` | Etapa 2 | Pendente |
| 7 | De-acumulação horária do ERA5-Land nunca validada manualmente contra o NetCDF bruto | Etapa 2 | Pendente |
| 8 | Holdout (05/07/2025–31/12/2025) não cobre um ciclo chuvoso completo da RMR | Etapa 3 | Pendente |
| 9 | Sem baseline de comparação (só o Prophet existe em `src/models`) | Etapa 4 | Pendente |
| 10 | "Análise de sensibilidade" e "robustez a gaps" atuais (`src/evaluation/sensitivity.py`, `tests/models/test_robustness.py`) são smoke tests de software, não evidência empírica | Etapa 5 | Pendente |
| 11 | Seed do Prophet não fixada de forma reprodutível (fit **e** predict) | Etapa 8 | Já planejado em `docs/superpowers/plans/2026-07-05-rigor-metodologico-tcc.md` (Task 7.1), ainda não executado |
| 12 | Sem CI, sem lockfile/`pyproject.toml`, `sys.path` manipulado em notebooks, caminho absoluto hardcoded no notebook 01 | Etapa 8 | Parcialmente planejado em `docs/superpowers/plans/2026-07-05-rigor-metodologico-tcc.md` (Tasks 7.2–7.4); CI (GitHub Actions) ainda não planejado |

Nota sobre o item 3: mesmo após a Etapa 6 (expansão e qualificação do
catálogo), a precisão pode permanecer não identificável se o catálogo
continuar incompleto — isso deve ser reportado como tal no texto final do
TCC, nunca apresentado como uma precisão medida com confiança.

## Como interpretar números publicados antes da Etapa 10

Qualquer número, tabela ou figura em notebooks, `README.md` ou nos módulos de
`src/` anterior à conclusão da Etapa 10 (regeração final dos resultados) é
**provisório** — construído sob a série, o split e o critério de avaliação
ainda não corrigidos pelas Etapas 2–9. Não citar esses números no texto final
do TCC; usar apenas os artefatos gerados após a Etapa 10.
```

- [ ] **Step 5: Adicionar nota de contexto em `docs/projeto_de_pesquisa.md` (sem alterar a extração original)**

Insira, entre a linha 8 (`- **Propósito Declarado**: ...`) e a linha 10 (`## 🔍 2. RESUMO EXECUTIVO (TL;DR)`) o seguinte bloco (mantendo a linha em branco existente entre elas):

```markdown
> **Nota de escopo (2026-08-05):** este documento resume o PDF do projeto de
> pesquisa **originalmente submetido** e é preservado aqui como registro
> histórico — não é editado para refletir decisões metodológicas
> posteriores. O escopo e as limitações **atuais** do projeto, após a
> auditoria metodológica de 2026-08, estão em
> [`docs/escopo_e_limitacoes.md`](escopo_e_limitacoes.md); em particular, a
> moldura de "inundação urbana" e "previsão" do projeto original foi
> restrita, na execução, a detecção retrospectiva de anomalias de
> precipitação média diária na RMR.
```

- [ ] **Step 6: Rodar os três primeiros testes e confirmar sucesso**

```bash
.venv/bin/python -m pytest tests/test_scope_documentation.py -v -k "not notebook"
```

Expected: `test_readme_states_frozen_retrospective_objective`, `test_readme_does_not_claim_flood_risk_application` e `test_escopo_e_limitacoes_doc_exists_and_lists_non_goals` PASS. `test_notebooks_have_scope_disclaimer_banner` continua FAIL (Task 2 ainda não executada) — esperado.

- [ ] **Step 7: Commit**

```bash
git add tests/test_scope_documentation.py README.md docs/escopo_e_limitacoes.md docs/projeto_de_pesquisa.md
git commit -m "docs: congelar objetivo do TCC em deteccao retrospectiva e criar escopo_e_limitacoes.md"
```

---

## Task 2: Banner de aviso de escopo nos três notebooks

**Files:**
- Modify: `notebooks/01_pre_processing_data.ipynb`, `notebooks/02_prophet_modeling.ipynb`, `notebooks/03_validation.ipynb`
- Modify: `tests/test_scope_documentation.py` (teste já escrito na Task 1, Step 1 — `test_notebooks_have_scope_disclaimer_banner`; nesta task ele passa a ficar verde)

**Interfaces:**
- Consome: nenhuma função de `src/`; edição via `nbformat` (mesmo padrão usado em `docs/superpowers/plans/2026-07-05-rigor-metodologico-tcc.md`, Tasks 7.2/7.4).

- [ ] **Step 1: Confirmar que o teste do banner ainda falha (baseline antes da mudança)**

```bash
.venv/bin/python -m pytest tests/test_scope_documentation.py::test_notebooks_have_scope_disclaimer_banner -v
```

Expected: FAIL (`AssertionError`, célula 0 atual é `# 0. Imports and Initial Configs`, sem referência a `docs/escopo_e_limitacoes.md`).

- [ ] **Step 2: Inserir a célula de banner como nova célula 0 em cada notebook**

```bash
.venv/bin/python - <<'EOF'
import nbformat

BANNER = (
    "> **Escopo e limitações:** este notebook faz parte de um trabalho de "
    "detecção **retrospectiva** de anomalias de precipitação média diária "
    "na RMR via Prophet — não é um sistema de previsão de chuva, não emite "
    "alerta antecipado e não modela risco de inundação. Números e figuras "
    "deste notebook anteriores à conclusão da Etapa 10 do plano de correção "
    "metodológica são **provisórios** e não devem ser citados no texto "
    "final do TCC. Ver `docs/escopo_e_limitacoes.md` para o escopo "
    "completo e as limitações conhecidas."
)

paths = [
    "notebooks/01_pre_processing_data.ipynb",
    "notebooks/02_prophet_modeling.ipynb",
    "notebooks/03_validation.ipynb",
]

for path in paths:
    nb = nbformat.read(path, as_version=4)
    banner_cell = nbformat.v4.new_markdown_cell(BANNER)
    nb.cells.insert(0, banner_cell)
    nbformat.write(nb, path)
    print(f"OK: {path}")
EOF
```

Expected: `OK: notebooks/01_pre_processing_data.ipynb`, `OK: notebooks/02_prophet_modeling.ipynb`, `OK: notebooks/03_validation.ipynb`.

- [ ] **Step 3: Validar que os três notebooks continuam JSON válido (sem executar — o notebook 01 ainda tem o caminho absoluto quebrado que só será corrigido pela Task 7.2 do plano de 2026-07-05, fora do escopo desta etapa)**

```bash
.venv/bin/python - <<'EOF'
import nbformat

for path in [
    "notebooks/01_pre_processing_data.ipynb",
    "notebooks/02_prophet_modeling.ipynb",
    "notebooks/03_validation.ipynb",
]:
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)
    print(f"Valido: {path}")
EOF
```

Expected: `Valido: ...` para os três, sem exceção de `nbformat.validate`.

- [ ] **Step 4: Rodar a suíte completa de `tests/test_scope_documentation.py` e confirmar sucesso total**

```bash
.venv/bin/python -m pytest tests/test_scope_documentation.py -v
```

Expected: `4 passed`.

- [ ] **Step 5: Rodar a suíte completa do projeto para confirmar que nada mais quebrou**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: todos os testes passam (esta etapa não toca `src/`, então nenhuma regressão é esperada fora do arquivo novo).

- [ ] **Step 6: Commit**

```bash
git add notebooks/01_pre_processing_data.ipynb notebooks/02_prophet_modeling.ipynb notebooks/03_validation.ipynb tests/test_scope_documentation.py
git commit -m "docs: adicionar banner de escopo e limitacoes nos notebooks 01-03"
```

---

## Self-Review

- **Cobertura da Etapa 1 do prompt original:** "Reescrever objetivo, resumo, título de seções e conclusões" → Task 1 (README) + Task 2 (banners nos notebooks, sem reescrever a prosa de conclusões ainda — justificado nos Global Constraints, já que os números serão regerados nas Etapas 2-3 e a reescrita de conclusões é Etapa 10). "Produzir `docs/escopo_e_limitacoes.md` listando o que o trabalho não é" → Task 1, Step 4, cobre os 6 pontos de "o que não é" e os 12 pontos da anamnese como limitações pendentes rastreadas por etapa.
- **Placeholder scan:** nenhum "TBD"/"preencher depois" — todo conteúdo de `docs/escopo_e_limitacoes.md`, `README.md` e do banner dos notebooks está escrito por extenso nos Steps, não descrito.
- **Consistência:** `FROZEN_OBJECTIVE` e `FORBIDDEN_README_PHRASES` definidos na Task 1 são exatamente os usados nos testes da Task 1; `test_notebooks_have_scope_disclaimer_banner` é escrito na Task 1 (Step 1, já que faz parte do mesmo arquivo de teste) mas só passa a ficar verde na Task 2 — deixado explícito no Step 2/Step 4 de cada task para não confundir o executor.
- **Dependência do restante do plano:** as Etapas 2+ (auditoria da série, out-of-sample, baselines, etc.) ainda precisam de planos próprios — não cobertos aqui. `docs/escopo_e_limitacoes.md` foi desenhado como documento vivo justamente para ser atualizado (tabela de status) conforme cada etapa seguinte for planejada e executada.
