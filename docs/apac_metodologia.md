# 📁 BASE DE CONSULTA: apac_motodologia.md

## 📌 1. METADADOS E CONTEXTO
- **Título Original**: "Análise completa do trabalho e dos mecanismos de classificação da APAC" (documento de análise que tem como objeto o artigo científico **"Previsão de extremos de chuva em Pernambuco: os eventos de maio de 2022"**, de Silva et al.)
- **Autor(es) / Remetente**: Documento-fonte primário: Silva, T. L. V. *et al.*, publicado na *Revista Brasileira de Geografia Física*, v. 16, n. 1, p. 646–671, 2023, por profissionais ligados à **Agência Pernambucana de Águas e Clima (APAC)**. O arquivo em si é uma análise/síntese derivada desse artigo, combinada com consulta ao site oficial da APAC e à documentação da WMO.
- **Data de Criação/Última Modificação**: Artigo original de 2023; consulta ao site oficial da APAC e da WMO realizada em **4 de julho de 2026** (data citada nas referências).
- **Tipo de Arquivo**: Markdown (.md) — documento de análise textual/estrutural.
- **Propósito Declarado**: Separar rigorosamente o que está documentado no artigo científico, o que consta atualmente no site oficial da APAC, e o que é síntese estrutural do mecanismo, sem preencher lacunas com critérios próprios.

## 🔍 2. RESUMO EXECUTIVO (TL;DR)
- O artigo analisado estuda a previsão dos eventos extremos de chuva de **25 e 28 de maio de 2022** em Pernambuco e a **metodologia operacional** da Sala de Situação da APAC para emissão de avisos.
- O mecanismo é um **processo multicritério supervisionado por meteorologistas**, não um classificador automático baseado só em milímetros.
- Existem **três eixos de classificação**: magnitude da chuva (6 categorias), probabilidade (5 classes qualitativas, sem percentuais) e impacto (5 classes).
- A **classificação de chuva** (Tabela 1, adaptada de Guedes e Silva, 2020) vai de "Sem chuva" (<2mm) a "Forte" (>100mm), com uma **lacuna matemática exatamente em 100 mm**, não coberta por nenhum intervalo.
- A **matriz de decisão** (Figura 3, p. 651) cruza probabilidade × impacto e gera 5 classes de gravidade: Baixo, Moderado-baixo, Moderado, Moderado-alto, Alto.
- **Não há regra automática** ligando célula da matriz a nível de aviso — a decisão final é operacional/meteorológica.
- Existem **três níveis de aviso**: Estado de Observação (amarelo), Estado de Atenção (laranja), Estado de Alerta (vermelho), descritos na Figura 4.
- O processo de decisão integra: modelos globais (GEM, GEPS, GFS, ICON), Ensemble 3GI, modelos regionais (ETA, WRF), satélite GOES-16, radar, pluviômetros, e conhecimento dos erros históricos dos modelos.
- O **WRF** foi ajustado para superestimar chuva (vantagem em extremos, mas mais falsos alarmes); o **Ensemble 3GI** suaviza extremos por ser média aritmética.
- O evento de **25/05** mostrou escalonamento progressivo (Observação → Atenção → Alerta); o de **28/05** teve emissão direta de Alerta antecipado.
- Há **diferenças documentadas** entre a metodologia do artigo de 2022 e a "Matriz Resumida" atualmente publicada no site oficial da APAC (ex.: Observação usa 24h no artigo vs. 3h/4 postos no site atual).
- A metodologia se relaciona com as diretrizes de **previsão baseada em impactos da WMO** (WMO-No. 1150).
- O documento aponta **inconsistências internas** explícitas: lacuna dos 100mm, divergência de termos entre Figura 4 e texto, e uma inconsistência editorial na Figura 28 (legenda "Atenção" vs. conteúdo "Alerta").
- O autor da análise **não funde** as versões (artigo vs. site atual) e recomenda definir explicitamente qual fonte normativa usar antes de qualquer automação/reprodução computacional.

## 🧭 3. ÍNDICE NAVEGÁVEL (Table of Contents)
1. [O que o trabalho realmente estuda](#1-o-que-o-trabalho-realmente-estuda)
2. [Estrutura geral do mecanismo de decisão da APAC](#2-estrutura-geral-do-mecanismo-de-decisão-da-apac)
3. [Primeira classificação: categorias de chuva](#3-primeira-classificação-categorias-de-chuva-associadas-aos-intervalos-prováveis-de-ocorrência)
4. [Segunda classificação: probabilidade de ocorrência](#4-segunda-classificação-probabilidade-de-ocorrência)
5. [Terceira classificação: impactos](#5-terceira-classificação-impactos)
6. [A matriz de decisões dos avisos meteorológicos](#6-a-matriz-de-decisões-dos-avisos-meteorológicos-da-apac)
7. [Como a matriz deve ser lida](#7-como-a-matriz-deve-ser-lida)
8. [O que a matriz não faz](#8-o-que-a-matriz-não-faz-segundo-o-documento)
9. [Fluxograma dos níveis de aviso](#9-fluxograma-dos-níveis-de-aviso-meteorológico-da-apac)
10. [Fluxograma transcrito estruturado](#10-o-fluxograma-transcrito-de-forma-estruturada)
11. [Divergência Figura 4 vs. texto](#11-um-ponto-importante-a-figura-4-e-o-texto-explicativo-não-usam-exatamente-a-mesma-formulação)
12. [O mecanismo operacional completo (Etapas 1–6)](#12-o-mecanismo-operacional-completo-descrito-no-artigo)
13. [A regra real: não é "modelo → alerta"](#13-a-regra-real-descrita-pelo-estudo-não-é-modelo--alerta)
14. [Por que a APAC não usa um único modelo](#14-por-que-a-apac-não-usa-um-único-modelo-como-verdade)
15. [Papel do Ensemble 3GI](#15-o-papel-específico-do-ensemble-3gi)
16. [Papel do WRF](#16-o-papel-específico-do-wrf)
17. [Aplicação ao evento de 25/05/2022](#17-aplicação-do-mecanismo-ao-evento-de-25-de-maio-de-2022)
18. [Aplicação ao evento de 28/05/2022](#18-aplicação-ao-evento-de-28-de-maio-de-2022)
19. [Diferença entre decisão de 25 e 28 de maio](#19-diferença-entre-a-decisão-de-25-e-a-de-28-de-maio)
20. [O que a APAC afirma no site oficial atual](#20-o-que-a-apac-afirma-atualmente-em-seu-site-oficial)
21. [Diferenças artigo 2022 vs. site atual](#21-há-diferenças-entre-o-artigo-de-2022-e-a-página-oficial-atual-da-apac)
22. [Relação com a WMO](#22-como-a-metodologia-da-apac-se-relaciona-com-a-recomendação-da-wmo)
23. [Inconsistências e pontos de cautela](#23-inconsistências-e-pontos-que-exigem-cautela-na-leitura-do-documento)
24. [Síntese final do mecanismo analítico](#24-síntese-final-do-mecanismo-analítico-da-apac)
- [Referências utilizadas](#referências-utilizadas)

## 📊 4. EXTRAÇÃO ESTRUTURAL E DE DADOS

### 4.1. Hierarquia de Conteúdo

> **Objetivo central do artigo**: avaliar como modelos operacionais representaram os eventos de 25 e 28/05/2022 e descrever a metodologia decisória da Sala de Situação.

- **Região de interesse**: leste de Pernambuco — RMR, Zona da Mata Norte, Zona da Mata Sul.
- **Natureza do mecanismo**: *"processo multicritério e supervisionado por meteorologistas"*, combinando 11 fatores (chuva prevista, convergência/divergência de modelos, confiabilidade dos modelos, sistema meteorológico, satélite, radar, pluviômetros, impactos potenciais, vulnerabilidade, erros históricos, experiência operacional).
- **Conclusão central dos autores**: análise subjetiva dos meteorologistas superou abordagem puramente determinística nos casos estudados.

**Fluxo lógico geral (síntese estrutural, não regra nova):**
> previsões numéricas e observações → classificação da chuva → avaliação da probabilidade → avaliação dos impactos → matriz de decisão → avaliação da previsão → nível de aviso → monitoramento contínuo e possível escalonamento

**Cadeia operacional completa (Seção 13):**
```text
MODELOS GLOBAIS + MODELOS REGIONAIS + ENSEMBLE + CAMPOS ATMOSFÉRICOS +
SATÉLITE + RADAR + PLUVIÔMETROS + CONHECIMENTO DOS ERROS DOS MODELOS +
VULNERABILIDADE E IMPACTOS
        ↓
AVALIAÇÃO DOS METEOROLOGISTAS
        ↓
CLASSIFICAÇÃO DE PROBABILIDADE E IMPACTO
        ↓
MATRIZ DE DECISÃO
        ↓
NÍVEL DE AVISO
        ↓
MONITORAMENTO CONTÍNUO
        ↓
MANUTENÇÃO, RENOVAÇÃO OU ESCALONAMENTO
```

### 4.2. Tabelas e Matrizes

**Tabela 1 — Classificação de chuva (Guedes e Silva, 2020), p. 650**

| Categoria | Acumulado em 24h |
|---|---:|
| Sem chuva | < 2 mm |
| Fraca | 2 mm ≤ chuva < 10 mm |
| Fraca a moderada | 10 mm ≤ chuva < 30 mm |
| Moderada | 30 mm ≤ chuva < 50 mm |
| Moderada a forte | 50 mm ≤ chuva < 100 mm |
| Forte | > 100 mm |

⚠️ **Nota crítica**: exatamente **100 mm** não pertence a nenhum intervalo (não coberto pelo "<100" nem pelo ">100").

**Tabela — 5 classes de probabilidade (Figura 3, p. 651)**

| Classe | Definição |
|---|---|
| Muito improvável | Sem convergência de modelos para chuva intensa |
| Improvável | Um ou outro modelo prevê chuva intensa isoladamente |
| Possível | Modelo pouco confiável indica chuva intensa generalizada; demais divergem |
| Provável | Modelos de boa confiabilidade preveem chuva intensa generalizada |
| Muito provável | Todos convergem + sistema monitorado + confirmado por satélite/radar |

**Tabela — 5 categorias de impacto (p. 650)**

| Impacto | Definição |
|---|---|
| Negligível | Sem alteração no dia a dia |
| Baixo | Danos localizados (alagamentos, trânsito) |
| Moderado | Alagamentos mais generalizados, trânsito mais grave |
| Significante | Deslizamentos, alagamentos generalizados, mais de um município |
| Severo | Evento extremo: enchentes, quedas de barreiras, dano à infraestrutura |

**Matriz de decisão completa (Figura 3, p. 651) — Probabilidade × Impacto**

| Probabilidade ↓ / Impacto → | Negligível | Baixo | Moderado | Significante | Severo |
|---|---|---|---|---|---|
| **Muito provável** | Moderado-baixo | Moderado | Moderado-alto | Alto | Alto |
| **Provável** | Baixo | Moderado-baixo | Moderado | Moderado-alto | Alto |
| **Possível** | Baixo | Moderado-baixo | Moderado | Moderado-alto | Moderado-alto |
| **Improvável** | Baixo | Moderado-baixo | Moderado-baixo | Moderado | Moderado-alto |
| **Muito improvável** | Baixo | Baixo | Moderado-baixo | Moderado | Moderado |

**Escala de cor da matriz:**

| Classe resultante | Cor |
|---|---|
| Baixo | Verde escuro |
| Moderado-baixo | Verde claro |
| Moderado | Amarelo |
| Moderado-alto | Laranja |
| Alto | Vermelho |

**Fluxograma dos 3 níveis de aviso (Figura 4, p. 652)**

```text
                          AVALIAÇÃO DA PREVISÃO
                                   |
             ┌─────────────────────┼─────────────────────┐
             v                     v                     v
    ESTADO DE OBSERVAÇÃO   ESTADO DE ATENÇÃO     ESTADO DE ALERTA
    Chuva > 30 mm          Chuva > 50 mm          Chuva > 100 mm
    Mínimo 4 postos        Probabilidades altas   Probabilidades altíssimas
    Risco moderado         Riscos moderados       Riscos altos
    Prob. média-alta       a altos                Eventos excepcionais
```

**Comparação Figura 4 vs. texto explicativo:**

| Nível | Figura 4 | Texto explicativo |
|---|---|---|
| Observação | >30mm; mín. 4 postos; prob. média-alta | >30mm/24h; possível a provável; impacto moderado |
| Atenção | >50mm; prob. alta; risco moderado-alto; evento generalizado | >50mm; possível a provável; impacto moderado-significante |
| Alerta | >100mm; prob. altíssima; risco alto; evento generalizado/excepcional | evento extremo/excepcional; provável a muito provável; impacto significante-severo |

**Modelos utilizados operacionalmente:**

| Categoria | Modelos |
|---|---|
| Globais | GEM, GEPS, GFS, ICON |
| Ensemble | Ensemble 3GI = média aritmética de GFS+GEM+GEPS+ICON |
| Regionais | ETA, WRF |
| Observação | Satélite GOES-16, Radar meteorológico, Pluviômetros |

**Rodadas de previsão:** 00 UTC (até 3 dias) e 12 UTC (até 48h).

**Comparação artigo 2022 vs. site oficial atual (Seção 21):**

| Elemento | Artigo (2022) | Site oficial atual |
|---|---|---|
| Observação | >30mm/24h; possível a provável; impacto moderado | Chuva prevista/observada; matriz resumida: >30mm em 3h, mín. 4 postos |
| Atenção | >50mm; possível a provável; impactos moderados-significantes | Possibilidade moderada; chuva moderada a forte >50mm |
| Alerta | Evento extremo/excepcional; provável a muito provável; significante-severo; figura usa >100mm | Possibilidade alta; chuva forte próxima ou acima de 100mm |

**"Matriz Resumida de critérios para Aviso Meteorológico" (site oficial atual da APAC):**

| Tipo | Possibilidade | Intensidade |
|---|---|---|
| Alerta Meteorológico | Alta | Forte, próximo ou acima de 100 mm |
| Estado de Atenção | Moderada | Moderada a forte, maior que 50 mm |
| Estado de Observação / Informe de Chuvas | Observada | Chuva >30mm em 3h, mín. 4 postos |

**Timeline do evento de 25/05/2022:**

| Fase | Data | Ação | Evidências-chave |
|---|---|---|---|
| 1 — Observação | 23/05 (tarde) | Emissão de Estado de Observação | Sistema em acompanhamento desde 23–24/05 |
| 2 — Atenção | 24/05 | Atualização para Estado de Atenção (Zona da Mata + RMR) | Escoamento atmosférico, instabilidade, modelos, satélite, prob. >50mm alta |
| 3 — Alerta | noite de 24→25/05 | Elevação para Estado de Alerta | Radar: 11–64 mm/h; WRF projetava até 200mm |

**Timeline do evento de 28/05/2022:**

| Data | Ação |
|---|---|
| 27/05 (manhã/8h) | Emissão direta de Estado de Alerta para todo litoral, válido até 28/05 (regionais >200mm; globais até 100mm; sinal forte no Ensemble 3GI) |
| 28/05 | Renovação do Alerta, válido até 29/05 |

**Comparação dos dois eventos:**

| Evento | Processo decisório |
|---|---|
| 25 de maio | Observação → Atenção → Alerta (escalonamento progressivo) |
| 28 de maio | Alerta antecipado → renovação (sem passar por todos os níveis) |

### 4.3. Glossário e Definições

| Termo / Sigla | Definição / Contexto | Onde aparece (ref.) |
|---|---|---|
| **APAC** | Agência Pernambucana de Águas e Clima | Todo o documento |
| **RMR** | Região Metropolitana do Recife | Seção 1, 5.1, 17 |
| **Sala de Situação** | Estrutura operacional da APAC responsável pela tomada de decisão sobre avisos | Seção 1 |
| **Ensemble 3GI** | Média aritmética entre GFS, GEM, GEPS e ICON, usada para convergência de localização de chuva | Seção 12 (Etapa 2), 15 |
| **GEM, GEPS, GFS, ICON** | Modelos numéricos globais de previsão do tempo usados operacionalmente | Seção 12 (Etapa 2) |
| **ETA, WRF** | Modelos regionais usados para refinamento espacial | Seção 12 (Etapa 3) |
| **GOES-16** | Satélite geoestacionário usado para monitorar deslocamento/formação de sistemas | Seção 12 (Etapa 6) |
| **Estado de Observação** | Nível 1 de aviso — amarelo; chuva >30mm/24h (artigo) | Seção 9.1 |
| **Estado de Atenção** | Nível 2 de aviso — laranja; chuva >50mm (artigo) | Seção 9.2 |
| **Estado de Alerta** | Nível 3 de aviso — vermelho; chuva >100mm (artigo) | Seção 9.3 |
| **WMO** | World Meteorological Organization (Organização Meteorológica Mundial); referência para previsão baseada em impactos (WMO-No. 1150) | Seção 22 |
| **Previsão baseada em impactos** | Abordagem que desloca o foco de "o que o tempo será" para "o que o tempo fará"; considera probabilidade e severidade dos impactos | Seção 22 |

## 🧠 5. INSIGHTS, INFERÊNCIAS E RELAÇÕES

- **Relação de causalidade central**: quanto maior a convergência entre modelos + maior a confiabilidade desses modelos + maior a confirmação observacional (satélite/radar), maior a classe qualitativa de probabilidade atribuída ao evento.
- **Independência dos dois eixos da matriz**: *o resultado da matriz não depende exclusivamente da probabilidade* — um evento de probabilidade baixa mas impacto severo ainda gera classe relevante (ex.: Improvável × Severo = Moderado-alto). Isso é uma inferência estrutural direta da matriz, não uma afirmação textual explícita do artigo.
- **Ambiguidade intencional do Ensemble 3GI**: por ser uma média aritmética, ele sistematicamente *suaviza extremos*, o que sugere que, em cenários de chuva muito intensa, o Ensemble tende a subestimar magnitude — mas ainda serve como indicador de área de risco.
- **Trade-off do ajuste do WRF**: o ajuste para superestimar precipitação implica um trade-off explícito entre sensibilidade a eventos extremos (vantagem) e aumento de falsos alarmes em chuvas fracas (desvantagem) — *é possível inferir que a APAC aceita esse trade-off porque os custos de subestimar um evento extremo (como os de maio/2022) são considerados maiores que os custos operacionais de falsos alarmes*.
- **Padrão de decisão não linear**: a comparação entre os eventos de 25 e 28 de maio mostra que *o processo decisório não é sequencial obrigatório* — dependendo do peso das evidências acumuladas, a APAC pode pular direto para o nível mais alto (28/05), sugerindo que a matriz/fluxo é uma heurística e não uma máquina de estados rígida.
- **Divergência de terminologia como sintoma, não como erro isolado**: as pequenas diferenças entre Figura 4 e texto explicativo, e entre artigo e site atual, sugerem que a metodologia da APAC *evoluiu ou foi resumida ao longo do tempo* sem que as diferentes versões tenham sido formalmente reconciliadas em documentação pública unificada.
- **Premissa oculta**: o artigo assume implicitamente que a experiência dos meteorologistas e o conhecimento acumulado sobre os erros dos modelos são superiores à confiança cega em qualquer modelo individual — essa é a premissa que justifica todo o desenho "multicritério supervisionado", em vez de um sistema puramente automatizado.

## ⚠️ 6. PONTOS DE ATENÇÃO, CONTRADIÇÕES E RISCOS

- **Lacuna matemática em 100 mm**: a Tabela 1 não classifica o valor exato de 100 mm (nem "moderada a forte" nem "forte" o cobrem). O documento **não corrige** essa lacuna por conta própria.
- **Inconsistência terminológica Figura 4 vs. texto**: Figura usa "probabilidades média-alta"; texto usa "Possível a Provável" — termos próximos, mas não idênticos.
- **Artigo (2022) ≠ site oficial atual (2026)**: critérios de Observação diferem — 24h no artigo vs. 30mm em 3h/mínimo 4 postos no site atual. As duas fontes **devem ser tratadas separadamente**, sem fusão.
- **Ausência de percentuais**: nenhuma das 5 classes de probabilidade (muito improvável → muito provável) tem correspondência numérica em percentual publicada no artigo. Qualquer conversão seria informação nova, não documentada.
- **Ausência de regra automática célula→aviso**: não é possível afirmar "Moderado-alto = Atenção" ou "Alto = Alerta" como regra fixa; a decisão sempre integra fatores adicionais (observações, dinâmica atmosférica, erros dos modelos, experiência, vulnerabilidade, evolução do evento).
- **Inconsistência editorial na Figura 28**: o texto e as imagens do artigo mostram "Estado de Alerta" para o evento do dia 28, mas a legenda da figura está transcrita como "Avisos meteorológicos de Estado de Atenção" — contradição entre legenda, texto e imagem, **sem explicação no artigo**.
- **Risco para uso futuro**: o documento alerta explicitamente que, para modelagem, automação ou reprodução computacional do processo, **as versões (artigo 2022 vs. site atual) não devem ser fundidas** sem definir qual será a fonte normativa de verdade.

## 🎯 7. AÇÕES, DECISÕES E PRÓXIMOS PASSOS

- [ ] Definir explicitamente qual documento normativo (artigo de 2022 vs. matriz resumida do site atual da APAC) será tratado como fonte de verdade antes de qualquer automação (Responsável implícito: equipe/pesquisador que for modelar o processo)
- [ ] Investigar e esclarecer a lacuna matemática do valor 100 mm na Tabela 1 (Responsável implícito: autores do artigo original / APAC)
- [ ] Reconciliar formalmente as diferenças terminológicas entre Figura 4 e texto explicativo do artigo (Responsável implícito: autores do artigo)
- [ ] Esclarecer a inconsistência editorial da legenda da Figura 28 (Estado de Atenção vs. Estado de Alerta) (Responsável implícito: autores/editoria da revista)
- [ ] Não tratar as classes qualitativas de probabilidade como equivalentes a percentuais sem fonte adicional (Responsável implícito: qualquer usuário futuro dos dados)

## 📎 8. ANEXOS E TRANSCRIÇÕES CRUAS (Raw Data)

> "A metodologia da APAC descrita no artigo não é um classificador automático baseado apenas em milímetros de chuva. É um processo de decisão meteorológica multicritério, probabilístico-categórico, baseado em impactos e continuamente atualizado por observações em tempo real."

> "a matriz é uma ferramenta estruturada de decisão, mas a decisão final permanece operacional e meteorológica."

> Tabela 1 (intervalos de chuva): "moderada a forte: 50 mm ≤ chuva < 100 mm; forte: chuva > 100 mm" — lacuna matemática em exatamente 100 mm.

> Matriz Resumida do site oficial: "Alerta Meteorológico — Alta — Forte, próximo ou acima de 100 mm."

## ❓ Perguntas que ficaram em aberto
- Qual é a classificação correta para chuva exatamente igual a 100 mm na Tabela 1 original?
- Existe algum documento normativo posterior (não localizado nas fontes consultadas) que substitua formalmente a matriz/regras de 2022?
- Qual é a explicação oficial para a divergência entre a legenda da Figura 28 e o conteúdo real (Atenção vs. Alerta)?
- Existe algum critério numérico (percentual) interno da APAC para as 5 classes de probabilidade, mesmo que não publicado no artigo?

---

**Confiança da Extração: 97%** — o conteúdo é textual e bem estruturado (sem OCR, sem tabelas corrompidas); a margem de incerteza refere-se apenas a ambiguidades já assinaladas pelo próprio documento-fonte (ex.: lacuna dos 100mm, divergências terminológicas entre artigo e site atual), que foram preservadas sem correção, conforme a metodologia do próprio documento original.
