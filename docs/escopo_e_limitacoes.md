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

## Roteiro das Etapas do Plano de Correção (1–10)

1. Congelar objetivo e claims (este documento e o objetivo em `README.md`).
2. Auditar e reconstruir a série (fuso horário, de-acumulação, máscara/percentil espacial da RMR).
3. Previsões exclusivamente out-of-sample (backtesting rolling-origin com origem expansiva).
4. Baselines climatológicos e de persistência, avaliados no mesmo protocolo do Prophet.
5. Redesenhar a avaliação (métricas por evento, clusterização de janelas sobrepostas, cobertura empírica do intervalo).
6. Expandir e qualificar o catálogo de eventos extremos (schema com tipo de evento, fonte, confiança).
7. Refazer a comparação com a APAC como análise exploratória de concordância, não benchmark.
8. Reprodutibilidade e engenharia (seed do Prophet, `pyproject.toml`, lockfile, CI).
9. INMET e CEMADEN como validação externa (correlação, viés, RMSE) do ERA5-Land — nunca fusão por prioridade de fonte.
10. Congelar números finais e reescrever a narrativa dos notebooks e do texto do TCC.

Cada etapa concluída deve ter seu próprio plano em `docs/superpowers/plans/`
e atualizar a tabela de limitações abaixo.

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
- **Ainda não usa INMET/CEMADEN, nem os funde por prioridade de fonte.**
  Nenhuma etapa executada do pipeline hoje consome essas fontes — não há
  código de correlação, viés ou RMSE contra a série ERA5-Land em `src/` ou
  `tests/`. Quando isso for implementado (Etapa 9), será apenas como
  validação externa, nunca fundido por prioridade de fonte (o que criaria
  descontinuidades artificiais que o Prophet leria como anomalia).
  `src/data/harmonize.py` já implementa fusão por prioridade de fonte, mas
  não está conectado a `src/run_pipeline.py` nem a nenhum notebook — deve
  ser removido ou re-escopado quando a Etapa 9 for planejada.
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
