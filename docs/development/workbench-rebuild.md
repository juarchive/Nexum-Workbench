# Reconstrução do Nexum Scientific Workbench

## Proposta

O Nexum deve permitir investigar uma pergunta química, escolher um modelo, conferir o resultado e reproduzir a análise no mesmo projeto. O trabalho começa pelo contrato científico de cada ferramenta e segue até o gráfico, o histórico e a exportação.

A reconstrução será feita por fluxos completos. A implementação atual serve de referência para abrir projetos existentes, comparar resultados e identificar comportamentos que precisam mudar. Cada fluxo novo entra na bancada após cumprir seus critérios de aceitação.

## Experiência de ponta a ponta

1. Criar um projeto, escrever a pergunta e identificar se a entrada foi medida, importada ou simulada.
2. Buscar a ferramenta pelo problema, pela técnica ou pela grandeza que se deseja calcular.
3. Informar os dados com unidades e selecionar um modelo cujas hipóteses se apliquem ao caso.
4. Conferir o valor, os gráficos, os limites do modelo e os diagnósticos que sustentam o resultado.
5. Registrar o resultado no projeto, reabrir a sessão e exportar o método e as evidências usadas.

A tela inicial mantém os atalhos de tarefa e a paisagem por trás do vidro. Nas telas de análise, as entradas, os eixos, as unidades e os avisos de validade têm prioridade visual.

## Ordem de implementação

| Etapa | Entrega verificável | Critério de saída |
| --- | --- | --- |
| 1. Cálculo e validade | Gases ideais, pH, titulação e Beer–Lambert com referências independentes | Valores, unidades, domínio e comportamento nos limites verificados pela entrada usada no aplicativo |
| 2. Projeto e rastreabilidade | Caderno que liga entradas, método, versão e resultado | Reabrir um projeto e recuperar a origem dos dados, as hipóteses, os parâmetros e os resultados |
| 3. Dados e metrologia | Importação, calibração e tratamento de séries | Dados brutos preservados, transformações registradas e incerteza avaliada quando houver dados suficientes |
| 4. Modelos avançados | Equilíbrio, cinética, termodinâmica, eletroquímica e processos | Diagnósticos verificáveis, casos de não convergência e comparações adequadas a cada modelo |
| 5. Estruturas e experimentos | Busca molecular, visualização, medições e protocolos | Origem identificável, medições reprodutíveis e quadros coerentes com o estado calculado |
| 6. Distribuição | Pacotes desktop, exemplos e documentação | Fluxos completos exercitados na instalação e na atualização em Linux, Windows e macOS |

## Critérios científicos por ferramenta

- Registrar a equação, as grandezas, as unidades, as constantes, as hipóteses, o domínio e a referência.
- Comparar com uma solução analítica, um benchmark independente ou medições publicadas adequadas ao modelo. Registrar a origem do valor esperado e a tolerância antes de corrigir o cálculo.
- Exercitar um caso nominal, casos de fronteira e entradas inválidas. Conferir resíduos, conservação ou invariantes quando fizerem parte do problema.
- Registrar separadamente exatidão numérica, validade física do modelo e concordância com medições. Quando houver dados reais, documentar condições de medição, incerteza e discrepâncias.
- Conferir se resultado, gráfico, histórico e exportação correspondem às mesmas entradas e unidades. Se as entradas mudarem, o resultado anterior deve ser invalidado ou identificado com os parâmetros que o produziram.

## Primeiro recorte

A suíte já contém referências independentes para pH de base forte, pressão por gás ideal e Beer–Lambert. A etapa inicial verifica as quatro incógnitas do gás ideal, rejeita entradas não finitas e compara o pH e a curva de uma titulação forte–forte antes, durante e após a equivalência. A prova de ácido acético com NaOH compara cinco pontos com um polinômio independente de alta precisão e com os valores calculados da [tabela 14.2 do OpenStax](https://openstax.org/books/chemistry-2e/pages/14-7-acid-base-titrations). Também verifica os balanços de matéria e carga e a reabertura da sessão com entradas, hipóteses, resultado e gráfico. A mesma titulação agora passa pelo registro no projeto de laboratório, reabertura do arquivo e exportação HTML, com entradas, hipóteses, pH, curva e marcador de equivalência. A comparação com medições experimentais continua em aberto.

A [matriz de validação](../science/validation-matrix.md) e a [auditoria dos modelos](../science/model-audit.md) registram a cobertura e as limitações já identificadas.

## Ampliação Android e usabilidade — 2026-11-06

Escopo solicitado: desktop completo e APK distribuível. A conclusão exige que cada ferramenta tenha finalidade compreensível, entradas com unidades, exemplo identificado, interpretação, limites e evidências de validação. A autoria permanece Davi P. Souza.

Implementado nesta etapa: guia contextual nas 43 calculadoras desktop; fronteira JSON compartilhada com Android; cliente móvel offline com formulários, cálculos em segundo plano, gráficos, caderno local e exportação; pipeline de APK com testes no emulador e assinatura obrigatória para release.

Correções adicionais: fórmulas não ignoram caracteres desconhecidos, cargas, índices zero ou delimitadores incompatíveis; entradas não finitas são recusadas em campos antes vulneráveis de constantes, especiação e Nernst.

Não concluído: rebuild visual e funcional de todas as telas desktop; integração móvel dos módulos de laboratório, estruturas e experimentos; validação experimental de cada modelo; inspeção visual do Android; testes em aparelho físico; releases assinadas. Pipeline configurado não é evidência de build aprovado.

| Área | Evidência atual | Critério ainda aberto |
| --- | --- | --- |
| Calculadoras | Casos de referência existentes e teste de transporte das 43 ferramentas | Ampliar referências independentes e revisão de usabilidade |
| Desktop | Guias adicionados ao formulário compartilhado | Inspeção GTK de cada fluxo e visual de todas as páginas |
| Android | Código do cliente e testes de instrumentação | Compilar, instalar, exercitar UI e recuperar registros |
| Dados e laboratório | Implementação desktop existente | Auditoria integral, incertezas e fluxos móveis |
| Estruturas e experimentos | Implementação desktop existente | Validar significado físico, navegação e versão móvel |
| Distribuição | Workflows desktop e Android | Builds verificados e assinatura Android configurada |
