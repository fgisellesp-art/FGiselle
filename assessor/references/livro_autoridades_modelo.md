# Livro de Autoridades da sessão

Uma linha por dispositivo ou precedente que a minuta pretende citar. A minuta só pode citar o que estiver aqui com nível **N3**.

- **N3**: texto literal obtido de fonte oficial na sessão (URL ou ferramenta, mais a data da consulta) ou colado/anexado pelo usuário.
- **N2**: indício (resumo de busca, fonte secundária, ferramenta que parafraseia). Não autoriza a citação.
- **N0**: não verificado (memória ou consulta que falhou). Não autoriza a citação.

Regras de preenchimento:

1. A coluna "Citação" traz o dispositivo exatamente como aparecerá na minuta, incluindo o nível citado (caput, parágrafo, inciso, alínea). Ex.: `art. 731, parágrafo único, do CPC`; `Súmula 54/STJ`; `Tema 1.234/STJ`.
2. A coluna "Texto literal conferido" traz o trecho copiado da fonte, entre aspas, e nunca uma paráfrase.
3. Registre a redação vigente na data do fato ou do ato, e não a que se lembra.
4. Para precedente, registre os cinco dados (tribunal, número, relator, data, tese) copiados do mesmo registro oficial.
5. Linha em N2 ou N0 pode ficar no Livro para lembrar a pendência, mas o verificador não a aceita como autorização.

O verificador (`scripts/verificar_citacoes.py --livro`) lê a primeira tabela que tiver as colunas "Citação" e "Nível".

| # | Citação | Nível | Fonte e data da consulta | Texto literal conferido |
|---|---|---|---|---|
