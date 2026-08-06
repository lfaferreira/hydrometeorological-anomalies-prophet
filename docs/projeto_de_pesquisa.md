# 📁 BASE DE CONSULTA: projeto_de_pesquisa_lfaf.pdf

## 📌 1. METADADOS E CONTEXTO
- **Título Original**: "Detecção de anomalias em séries temporais hidrometeorológicas com Prophet: uma aplicação a eventos extremos de inundação urbana no Brasil."
- **Autor(es) / Remetente**: **Aluno(a)**: Lucas Fernando Alves Ferreira. **Orientador(a)**: Gabrielle Maria Romeiro Lombardi.
- **Data de Criação/Última Modificação**: Não há data explícita de criação no documento; o cronograma abrange **02/2026 a 11/2026**, o que situa a produção/entrega do projeto em 2026.
- **Tipo de Arquivo**: PDF — Projeto de Pesquisa (etapa preliminar de Trabalho de Conclusão de Curso — TCC).
- **Propósito Declarado**: Documento formal de projeto de pesquisa do **MBA Data Science e Analytics (MBA USP/ESALQ)**, propondo investigar o uso do modelo **Prophet** para detecção de anomalias em séries hidrometeorológicas associadas a inundações urbanas no Brasil.

> **Nota de escopo (2026-08-05):** este documento resume o PDF do projeto de
> pesquisa **originalmente submetido** e é preservado aqui como registro
> histórico — não é editado para refletir decisões metodológicas
> posteriores. O escopo e as limitações **atuais** do projeto, após a
> auditoria metodológica de 2026-08, estão em
> [`docs/escopo_e_limitacoes.md`](escopo_e_limitacoes.md); em particular, a
> moldura de "inundação urbana" e "previsão" do projeto original foi
> restrita, na execução, a detecção retrospectiva de anomalias de
> precipitação média diária na RMR.

## 🔍 2. RESUMO EXECUTIVO (TL;DR)
- Projeto de TCC do curso **MBA Data Science e Analytics (MBA USP/ESALQ)**, autor **Lucas Fernando Alves Ferreira**, orientação de **Gabrielle Maria Romeiro Lombardi**.
- Tema: usar o modelo **Prophet** (Meta) para **detectar anomalias** em séries temporais hidrometeorológicas ligadas a **inundações urbanas** no Brasil.
- **Problema/motivação**: eventos extremos (chuvas, enchentes, alagamentos) estão mais frequentes em áreas urbanas vulneráveis; exemplos citados: **Recife/2022** e **Rio Grande do Sul/2024**.
- **Lacuna identificada na literatura**: falta de aplicação de modelos **interpretáveis** (como Prophet) especificamente para **detecção de anomalias** em inundação urbana — a maioria dos estudos foca em previsão ou em modelos complexos (ex.: LSTM).
- **Questão de pesquisa**: *"em que medida o modelo Prophet pode ser utilizado para detectar anomalias em séries temporais hidrometeorológicas associadas a eventos extremos de inundação urbana no Brasil?"*
- **Vantagens do Prophet destacadas**: modelo aditivo (tendência + sazonalidade + efeitos específicos), lida com dados faltantes e mudanças estruturais, é mais parcimonioso/interpretável que LSTM, com menor custo computacional.
- **Método de detecção de anomalias**: comparação entre valores observados e **intervalo de incerteza** estimado pelo Prophet — pontos fora dos limites superior/inferior são sinalizados como anomalias.
- **Fontes de dados planejadas**: **ERA5-Land** (base climática histórica) e estações meteorológicas (**INMET**, **CEMADEN**).
- **Validação planejada**: cruzamento das anomalias detectadas com registros históricos de desastres documentados na literatura (Anjos et al., 2024; Magalhães Filho et al., 2024).
- **Resultados preliminares esperados** (ainda não obtidos): boa representação de tendência/sazonalidade pelo Prophet, identificação de desvios significativos, e correspondência inicial entre anomalias e eventos históricos.
- **Cronograma**: 10 blocos de atividades distribuídos de **fevereiro a novembro de 2026**, culminando na defesa.
- **Base bibliográfica**: 5 referências citadas, todas de 2022–2024, cobrindo eventos extremos no Brasil e o uso do Prophet.

## 🧭 3. ÍNDICE NAVEGÁVEL (Table of Contents)
1. [Introdução](#41-hierarquia-de-conteúdo)
2. [Material e Métodos](#41-hierarquia-de-conteúdo)
3. [Resultados Preliminares](#41-hierarquia-de-conteúdo)
4. [Cronograma de Atividades](#42-tabelas-e-matrizes)
5. [Referências](#43-glossário-e-definições)

*(Documento curto, de 4 páginas, com estrutura linear — seções mapeadas diretamente nos títulos originais do texto.)*

## 📊 4. EXTRAÇÃO ESTRUTURAL E DE DADOS

### 4.1. Hierarquia de Conteúdo

**Ficha do projeto**
- Aluno(a): **Lucas Fernando Alves Ferreira**
- Orientador(a): **Gabrielle Maria Romeiro Lombardi**
- Curso: **MBA Data Science e Analytics**
- Título: *"Detecção de anomalias em séries temporais hidrometeorológicas com Prophet: uma aplicação a eventos extremos de inundação urbana no Brasil."*

**Introdução** (p.1–2)
> Eventos hidrometeorológicos extremos, como chuvas intensas, enchentes e alagamentos, têm se tornado cada vez mais frequentes no Brasil, especialmente em áreas urbanas caracterizadas por alta vulnerabilidade socioambiental (Silva Junior et al., 2022).

- Causas apontadas: **crescimento urbano desordenado** + **ocupação de áreas de risco** + **insuficiência de sistemas de drenagem** (Aragão e Duarte, 2023) → intensificam danos e riscos.
- Casos empíricos citados: **chuvas intensas em Recife (2022)**; **enchentes no Rio Grande do Sul (2024)** — ambos evidenciando limitações na capacidade de resposta/antecipação (Anjos et al., 2024; Magalhães Filho et al., 2024).
- Panorama metodológico: modelos estatísticos tradicionais vs. **LSTM** (bom para dependências temporais complexas, mas custoso e pouco interpretável) (Lima e Santos, 2024).
- Modelo proposto: **Prophet** (Meta) — modelo aditivo (tendência + sazonalidade + efeitos específicos), lida com dados faltantes e mudanças estruturais (Lima e Santos, 2024).
- Mecanismo de detecção de anomalias via Prophet: comparação de valores observados vs. **intervalos de incerteza** estimados pelo modelo (Lima e Santos, 2024).
- **Lacuna de pesquisa**: falta de estudos aplicando modelos interpretáveis (Prophet) especificamente à **detecção de anomalias** em inundação urbana — maioria da literatura foca em previsão ou modelos complexos.
- **Questão de pesquisa** (citação literal, <15 palavras teria que ser cortada — parafraseado): o estudo busca entender até que ponto o Prophet consegue identificar anomalias em séries hidrometeorológicas ligadas a inundações urbanas brasileiras.

**Material e Métodos** (p.2)
- Bases de dados: **ERA5-Land** (histórica climática) + estações **INMET** e **CEMADEN** (usadas em Anjos et al., 2024).
- Metodologia: processamento das séries → aplicação do **Prophet** para ajuste de curvas de **tendência** e **sazonalidade**.
- Detecção de anomalias: decomposição da série (tendência + sazonalidade) (Lima e Santos, 2024); pontos fora dos limites do intervalo de incerteza = anomalias.
- Validação: comparação dos sinais de anomalia com registros históricos de desastres da literatura (Anjos et al., 2024; Magalhães Filho et al., 2024).

**Resultados Preliminares** (p.2–3)
- Expectativa: Prophet representará satisfatoriamente tendência/sazonalidade das séries.
- Expectativa: identificação de desvios significativos associados a precipitação/inundação.
- Expectativa: correspondência inicial entre anomalias detectadas e eventos historicamente registrados — evidenciando viabilidade do Prophet como ferramenta interpretável e eficiente para monitoramento/gestão de risco.

*(Nota: esta seção é inteiramente prospectiva — o projeto ainda não executou a análise; são expectativas, não resultados obtidos.)*

## 🧠 5. INSIGHTS, INFERÊNCIAS E RELAÇÕES

- **Relação de causalidade proposta pelo projeto**: crescimento urbano desordenado + ocupação de áreas de risco + drenagem insuficiente → amplifica danos de eventos hidrometeorológicos extremos. Essa cadeia causal é apresentada como consenso da literatura citada, não como achado do próprio autor.
- **Trade-off metodológico central do projeto**: *é possível inferir* que a escolha do Prophet em vez de LSTM reflete uma priorização deliberada de **interpretabilidade e eficiência computacional** sobre desempenho bruto em padrões complexos — coerente com o público-alvo do estudo (gestão de risco e políticas públicas, que exigem transparência decisória).
- **Lacuna como justificativa central**: a lacuna identificada (falta de estudos de detecção de anomalias com modelos interpretáveis para inundação urbana) é o principal argumento de originalidade do projeto — ainda que a mesma lacuna seja sustentada por poucas referências (5 no total), o que é normal em projeto de pesquisa (fase preliminar), mas relevante notar.
- **Natureza prospectiva dos "Resultados Preliminares"**: a seção usa linguagem no futuro/condicional ("espera-se verificar", "poderão indicar", "espera-se ainda observar") — *isso indica que a seção descreve hipóteses/expectativas metodológicas, não resultados empíricos já obtidos*. Isso é esperado em um Projeto de Pesquisa (etapa anterior à execução do TCC), mas é uma distinção importante para quem for reutilizar este documento.
- **Dependência de dados externos como risco potencial**: o projeto depende de bases públicas (ERA5-Land, INMET, CEMADEN) cuja qualidade, granularidade e completude não são discutidas no documento — *pode ser um ponto de atenção metodológico não coberto explicitamente pelo texto*.

## ⚠️ 6. PONTOS DE ATENÇÃO, CONTRADIÇÕES E RISCOS

- **Ausência de detalhamento estatístico da validação**: o projeto menciona "confrontar" anomalias com registros históricos de desastres, mas não especifica **métricas de avaliação** (ex.: precisão, recall, F1, taxa de falso positivo) — método de validação ainda não operacionalizado.
- **Resultados preliminares são hipóteses, não dados**: como apontado nos insights, a seção "Resultados Preliminares" não contém nenhum resultado real — é puramente expectativa, o que é natural na fase de *projeto de pesquisa*, mas não deve ser confundido com resultados do TCC final.
- **Poucas referências-base (5 no total)**: a fundamentação teórica repousa fortemente em apenas duas referências para o núcleo metodológico (Lima e Santos, 2024, citada para quase todos os aspectos técnicos do Prophet) — risco de dependência excessiva de uma única fonte para a justificativa metodológica central.
- **Cronograma sem margem de contingência aparente**: todas as fases estão encadeadas sem meses de reserva explícitos para atrasos (ex.: dificuldades de acesso a dados do CEMADEN/INMET), o que é um risco operacional comum em TCCs com dados públicos.
- **Escopo geográfico amplo, mas exemplos concentrados**: o projeto menciona "Brasil" no título e na questão de pesquisa, mas os exemplos empíricos citados na introdução se concentram em **Recife (PE)** e **Rio Grande do Sul** — não fica explícito no documento se a aplicação final cobrirá essas duas regiões especificamente ou terá abrangência nacional mais ampla.

## 📎 7. ANEXOS E TRANSCRIÇÕES CRUAS (Raw Data)

> "em que medida o modelo Prophet pode ser utilizado para detectar anomalias em séries temporais hidrometeorológicas associadas a eventos extremos de inundação urbana no Brasil?"

**Referências bibliográficas completas (transcrição literal por serem dados de citação, não texto autoral):**

- Anjos, L.S.; Anjos, R.S.; Luna, V.F.; Wanderley, L.S.A.; Nóbrega, R.S. 2024. Resgate histórico dos eventos extremos de precipitação e seus impactos no município do Recife-PE. Revista Brasileira de Climatologia. 34(20):335-359. doi: 10.55761/abclima.v34i20.16937.
- Lima, M.; Santos, I.M. 2024. Avaliação do modelo de previsão Prophet como ferramenta para preenchimento de falha de dados em séries climáticas. In: Escola Regional de Informática de Mato Grosso (ERI-MT), 13., 2024, Alto Araguaia/MT. Anais [...]. Porto Alegre: Sociedade Brasileira de Computação. p. 31-36. ISSN: 2447-5386. doi: 10.5753/eri-mt.2024.245806.
- Magalhães Filho, F.J.C. et al. 2024. Enchentes e inundações no Rio Grande do Sul em 2024: impactos e desafios para a gestão integrada de políticas públicas no saneamento básico. Boletim Regional Urbano e Ambiental. 33:23-32. doi: 10.38116/brua33art1.
- Silva Junior, R.S.; Gama, M.C.C.; Silva, E.H.L.; Mariano, G.L.; Oliveira Junior, J.F.; Silva, L.S.O.; Cardoso, K.R.A. 2022. Avaliação de eventos extremos de precipitação, associados a desastres naturais. Revista Brasileira de Geografia Física. 15(6):2755-2767. doi: 10.26848/rbgf.v15.6.p2755-2767.
- Silva, M.L.A.; Duarte, C.C. 2023. Dinâmica climática, eventos extremos e impactos associados no município do Jaboatão dos Guararapes, Pernambuco, Brasil. Revista Brasileira de Geografia Física. 16(2):818-836. doi: 10.26848/rbgf.v16.2.p818-836.
