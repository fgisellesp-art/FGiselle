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
