# Blindagem das skills assessor e Inovajur contra citação inventada

Objetivo: reduzir o risco de a minuta citar lei, artigo, súmula, tema ou precedente que não existe, ou que existe mas não diz o que a minuta afirma.

## Por que a barreira anterior falhava

1. Lei e artigo não tinham protocolo próprio (a jurisprudência tinha). A regra 5 dizia apenas "confira número e conteúdo".
2. A auditoria era autodeclaração do mesmo modelo que redigiu, sem evidência por item.
3. Verificava-se depois de escrever, de memória, e não antes.
4. Só se checava se o artigo **existia**. O erro típico é o artigo existir e a minuta atribuir a ele o que ele não diz.
5. Falha de consulta caía na memória, sem regra de "falha fechada".
6. A Inovajur auditava as fontes das partes, não as da minuta do gabinete.

## O que há aqui

| Arquivo | Para quê |
|---|---|
| `assessor/SKILL.md` | Skill assessor com as regras 19 a 24 e o Protocolo de Fundamentação Normativa |
| `inovajur-anti-alucinacao/ADENDO-OPERACIONAL-2.md` | Texto a anexar ao final da skill Inovajur |
| `escrita-autentica/` | Skill de estilo ajustada para não inventar especificidade nem mexer em citação |
| `*/scripts/verificar_citacoes.py` | Verificador mecânico de citações |
| `*/references/` | Modelo do Livro de Autoridades e prompt do verificador independente |
| `livro/` | Acervo oficial: texto literal de cada artigo de 10 diplomas, extraído por programa da Câmara dos Deputados |
| `CHANGELOG-blindagem.md` | Lista exata do que mudou e das pendências |
| `testes/` | Casos de teste do verificador |

## Como instalar

1. Substitua o `SKILL.md` do assessor pelo desta pasta e copie `scripts/` e `references/` para a pasta da skill.
2. Substitua o `SKILL.md` e o `references/padroes-ia.md` da escrita-autentica pelos desta pasta.
3. Na Inovajur, anexe `ADENDO-OPERACIONAL-2.md` ao final do `SKILL.md` e copie `scripts/verificar_citacoes.py` e `references/`.

## Como testar o verificador

```
python3 assessor/scripts/verificar_citacoes.py testes/caso_real_art731.txt --livro testes/livro_teste.md
python3 assessor/scripts/verificar_citacoes.py testes/sintetico_variado.txt --livro testes/livro_teste.md
```

O primeiro caso mostra o ponto central: com o art. 731 no Livro como verificado, a checagem de existência passa, e o alerta de **atribuição de conteúdo** é o que sinaliza a frase a conferir.

## Acervo oficial (`livro/`)

Texto literal, artigo por artigo, extraído por programa (`livro/construir_livro.py`) das páginas de texto atualizado da Câmara dos Deputados. Cada arquivo traz no cabeçalho a URL, a data e hora do download e o SHA-256 do HTML de origem, guardado em `livro/_html/`.

| Sigla | Diploma | Artigos |
|---|---|---|
| CPC | Lei 13.105/2015 | 1 a 1.072 |
| CPP | Decreto-Lei 3.689/1941 | 1 a 811 |
| CP | Decreto-Lei 2.848/1940 | 1 a 361 |
| CC | Lei 10.406/2002 | 1 a 2.046 |
| CF | Constituição de 1988 (+ ADCT, com prefixo `ADCT-`) | 1 a 250; ADCT 1 a 138 |
| ECA | Lei 8.069/1990 | 1 a 267 |
| LMP | Lei 11.340/2006 | 1 a 46 |
| L9099 | Lei 9.099/1995 | 1 a 97 |
| CDC | Lei 8.078/1990 | 1 a 119 |
| L5478 | Lei 5.478/1968 | 1 a 29 |

Conferências feitas: sequência numérica completa em todos (incluindo artigos com letra, como 359-M-A); cabeçalho de cada página confere com o diploma; o art. 731 do CPC bate palavra por palavra com o texto colado pela usuária. Duas irregularidades do próprio original ficaram registradas no Livro, sem correção silenciosa: "Art. l97" no CP (letra l) e "Art 1.636" no CC (sem ponto).

Para atualizar: `python3 livro/construir_livro.py` (todos) ou `python3 livro/construir_livro.py CPC` (um). Para incluir outro diploma, acrescente a URL "normaatualizada" da Câmara em `livro/fontes.json`.

Limite: compilação da Câmara, não o Diário Oficial. O Planalto recusa conexões vindas do servidor em nuvem.

Uso com o verificador:

```
python3 assessor/scripts/verificar_citacoes.py MINUTA.txt --acervo livro
```
