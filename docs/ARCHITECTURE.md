# Arquitetura — Cash Flow Intelligence v0.4

## Contrato de dados

`CashObservation` preserva data, saldo de abertura, entradas, saídas, saldo de fechamento e origem. A origem é obrigatória (`synthetic` ou `uploaded`) para impedir que um dado demonstrativo seja apresentado como real.

## Avaliação temporal

A série é ordenada por data. Os últimos 28 registros nunca participam do ajuste: são teste. A referência é a média dos quatro últimos registros com o mesmo dia da semana. O modelo combina essa sazonalidade com tendência dos últimos 14 dias.

## Incerteza

O intervalo é formado pelos percentis 10 e 90 dos resíduos de teste. A cobertura do intervalo é publicada juntamente com MAE, RMSE e WAPE. Portanto, o intervalo descreve comportamento observado no holdout, não garantia probabilística universal.

## Cenários

O endpoint de cenários parte da trajetória prevista e aplica alterações explícitas de recebimentos, saídas e evento pontual. A resposta tem `kind=scenario_simulation` e um disclaimer próprio; ela não é reclassificada como previsão.

## Segurança decisória

O sistema não executa pagamentos, resgates, transferências ou recomendações de investimento. Qualquer uso operacional deve manter aprovação humana e trilha de auditoria.
