# Análise de fatores associados ao engajamento em vídeos do YouTube utilizando metadados públicos

## Descrição do projeto

Este projeto tem como objetivo investigar **fatores associados ao engajamento em vídeos do YouTube** utilizando **apenas metadados públicos disponibilizados pela API da plataforma**. A proposta central é construir uma base de dados de vídeos de um nicho específico e analisar, de forma exploratória e preditiva, quais características dos vídeos e dos canais estão mais relacionadas ao engajamento da audiência.

A motivação do trabalho está na possibilidade de compreender, a partir de variáveis simples e acessíveis, se é viável **prever o nível de engajamento de um vídeo** sem recorrer a dados mais complexos, como transcrições, processamento intensivo de linguagem natural ou análise aprofundada de comentários.

---

## Problema de pesquisa

**É possível prever se um vídeo terá alto ou baixo engajamento utilizando apenas metadados públicos disponibilizados pela API do YouTube?**

---

## Objetivo

Construir uma base de dados contendo vídeos de um nicho específico e avaliar quais características estão mais associadas ao engajamento dos usuários.

De forma mais específica, o projeto busca:

* coletar metadados públicos de vídeos do YouTube;
* organizar uma base de dados estruturada para análise;
* explorar a relação entre atributos dos vídeos/canais e o engajamento;
* formular um problema de **classificação binária** para distinguir vídeos com **alto engajamento** e **baixo engajamento**;
* comparar modelos de aprendizado de máquina supervisionado para essa tarefa.

---

## Escopo do dataset

A base de dados será construída a partir de vídeos de um nicho específico do YouTube. Para cada vídeo, serão coletadas variáveis públicas disponíveis na API, incluindo:

* **visualizações**
* **likes**
* **comentários**
* **duração**
* **data de publicação**
* **tamanho do título**
* **tamanho da descrição**
* **quantidade de tags**
* **número de inscritos do canal**

### Delimitações do trabalho

Para manter o escopo viável e focado em metadados estruturados:

* haverá **pouca utilização de comentários**;
* **não serão utilizadas transcrições** dos vídeos;
* **não será aplicado NLP pesado** nesta etapa inicial do projeto.

---

## Formulação do problema de aprendizado de máquina

O problema será modelado como uma tarefa de **classificação binária**, em que cada vídeo será classificado em uma de duas categorias:

* **alto engajamento**
* **baixo engajamento**

A definição operacional dessas classes poderá ser feita a partir de uma métrica de engajamento derivada de interações públicas do vídeo (por exemplo, combinação entre likes, comentários e visualizações), com posterior binarização segundo um critério estatístico ou limiar definido no estudo.

---

## Modelos a serem avaliados

Serão avaliados, em uma comparação inicial, os seguintes algoritmos de classificação:

* **Logistic Regression**
* **Random Forest**
* **XGBoost** *(caso seja incluído na etapa experimental)*

A proposta é realizar uma **comparação simples entre modelos**, priorizando interpretabilidade e desempenho preditivo.

---

## Métricas de avaliação

Os modelos serão avaliados por meio das seguintes métricas:

* **Accuracy**
* **Precision**
* **Recall**
* **F1-Score**

Essas métricas permitirão analisar não apenas a acurácia global do classificador, mas também sua capacidade de identificar corretamente vídeos de alto ou baixo engajamento.

---

## Etapas previstas do projeto

O fluxo geral do projeto pode ser resumido nas seguintes etapas:

1. **Definição do nicho de vídeos** a ser analisado;
2. **Coleta de dados** via API do YouTube;
3. **Construção e limpeza da base de dados**;
4. **Análise exploratória dos dados (EDA)**;
5. **Definição da variável-alvo de engajamento**;
6. **Treinamento e comparação dos modelos de classificação**;
7. **Avaliação dos resultados** e interpretação dos fatores mais associados ao engajamento.

---

## Resultados esperados

Espera-se, ao final do projeto:

* construir uma **base de dados de vídeos do YouTube** organizada para análise;
* identificar quais metadados possuem maior associação com o engajamento da audiência;
* verificar se variáveis simples, públicas e estruturadas são suficientes para sustentar um modelo preditivo de engajamento;
* fornecer uma análise exploratória que ajude a compreender padrões de desempenho de vídeos dentro de um nicho específico.

---

## Possíveis extensões futuras

Caso os resultados da etapa inicial sejam promissores, o projeto poderá ser estendido para investigar questões mais complexas, como:

### 1. Sentimento dos comentários

> **O sentimento dos comentários melhora a predição de engajamento?**

Nessa extensão, comentários poderiam ser incorporados como fonte adicional de informação, com técnicas de análise de sentimento.

### 2. Tópicos latentes em vídeos de alto engajamento

> **Com modelos derivados do BERT, existem tópicos latentes associados a vídeos de alto engajamento?**

Essa etapa abriria espaço para o uso de abordagens mais avançadas de NLP, incluindo embeddings e modelos baseados em transformadores para análise textual de títulos, descrições, comentários ou transcrições.

---

## Síntese

Em essência, este projeto propõe a **construção de uma base de dados de vídeos do YouTube** e a realização de uma **análise exploratória e preditiva dos fatores associados ao engajamento da audiência**, utilizando exclusivamente **metadados públicos** em sua versão inicial. O foco está em verificar até que ponto atributos simples de vídeos e canais conseguem explicar ou prever padrões de engajamento, servindo como base para extensões futuras com técnicas mais sofisticadas de análise textual.

---
