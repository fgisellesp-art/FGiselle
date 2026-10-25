# O que mudou em relação às skills originais

Base de comparação: o commit `82d5d5c` guarda o `assessor/SKILL.md` exatamente como foi recebido. `git diff 82d5d5c -- assessor/SKILL.md` mostra cada alteração.

## assessor/SKILL.md (editado)

| Onde | Alteração |
|---|---|
| Regra 5 | Passa a exigir verificação pelo PFN, em vez de "confira número e conteúdo" sem dizer contra quê |
| Regra 6 | Súmula, tema, enunciado e acórdão também só entram se constarem do Livro de Autoridades |
| Regras 19 a 24 (novas) | 19 Livro de Autoridades · 20 aderência (tema, comando, condições) · 21 falha fechada e resumo de busca ≠ literal · 22 granularidade e vigência · 23 congelamento após a auditoria · 24 proibição de "entendimento pacífico" e doutrina sem fonte |
| Seção "Protocolo de Fundamentação Normativa (PFN)" (nova) | Níveis N3/N2/N0, ordem "verificar antes de escrever", hierarquia de fontes, Livro, teste de aderência, marcadores, Tabela de Fontes Jurídicas, caso de referência anonimizado |
| Fase 3 | Parágrafo "Fundamentação" mandando aplicar o PFN antes de redigir |
| Fase 4, checklist | Item novo "Livro de Autoridades e verificador" antes do item "Fundamentos legais" |
| Fase 4, fecho | A frase "Auditoria: todas as referências conferidas" só pode ser usada com a Tabela de Fontes Jurídicas toda em N3 e sem marcador pendente; a nota passa a trazer contagem |
| Protocolo de Jurisprudência | "Fonte confiável" remete à hierarquia do PFN; pesquisa passa de "autorizada" a "obrigatória"; cinco dados do mesmo registro; tese entre aspas copiada; escopo ampliado (TJ, turmas recursais, FONAJE, CJF, Informativos, CGJ, CNJ); situação atual (cancelada, superada, modulada); acórdão isolado não é precedente vinculante |
| Modelo de Decisão | `Nos termos do art. [...]` trocado por referência ao Livro / marcador `[FUNDAMENTO LEGAL A CONFIRMAR ...]` |
| Lembrete final | Uma frase acrescentada |

Nada mais foi alterado: as regras 1 a 4 e 7 a 18, o protocolo de leitura MCP ANA (L1 a L11), as Fases 0 a 2, o estilo e o modelo de despacho estão como no original.

## inovajur-anti-alucinacao (não editado; adendo à parte)

O rodapé da skill reserva os direitos ao autor. Por isso o `SKILL.md` original **não** foi copiado nem alterado. O arquivo `ADENDO-OPERACIONAL-2.md` é texto novo, para ser anexado ao final do `SKILL.md` da Inovajur, no mesmo formato do Adendo Operacional que ela já tem. Ele estende o Pilar I à minuta do próprio gabinete, cria o vício 7 na taxonomia (conteúdo atribuído ao dispositivo que o texto não contém) e o Teste de Aderência.

## Arquivos novos

- `assessor/scripts/verificar_citacoes.py` (cópia idêntica em `inovajur-anti-alucinacao/scripts/`)
- `assessor/references/livro_autoridades_modelo.md` e `prompt_verificador_independente.md` (cópias idênticas em `inovajur-anti-alucinacao/references/`)
- `testes/` com o trecho do caso real (sem número de processo nem dados das partes), um texto sintético e um Livro de teste

## Pendências conhecidas

- **Nenhum texto de dispositivo foi carregado.** Neste ambiente os sites oficiais (Planalto, Câmara, LexML, STJ, STF, TJMA) estavam bloqueados e o Lawstronaut exigia nova autenticação. O Livro de Autoridades pré-carregado, com as normas mais usadas na vara única, precisa ser montado onde essas fontes estejam acessíveis.
- O verificador é mecânico. Ele não prova que uma norma existe nem que diz o que a minuta afirma.
- O único alias numérico de lei embutido no script (Lei 13.105/2015 = CPC) foi confirmado por resultado de busca nesta sessão; os demais diplomas são reconhecidos por sigla ou nome.
- Não li a skill `escrita-autentica`; a regra 23 trata da interação, mas vale conferir o texto dela.
