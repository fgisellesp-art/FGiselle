#!/usr/bin/env python3
"""verificar_citacoes.py - verificador mecanico de citacoes juridicas em minutas.

O QUE FAZ
  Extrai de uma minuta todas as citacoes (artigos, leis, sumulas, temas,
  processos paradigma, numeros CNJ, resolucoes/provimentos/enunciados) e as
  confronta com o Livro de Autoridades da sessao e, opcionalmente, com a versao
  anterior ja auditada.

O QUE NAO FAZ
  Nao prova que uma norma existe nem que ela diz o que a minuta afirma. Isso
  exige o texto literal de fonte oficial e leitura. O script pega o que e
  mecanico: numero CNJ com digito invalido, citacao fora do Livro, citacao nova
  depois da auditoria, diploma nao identificado, marcadores pendentes,
  afirmacoes genericas ("jurisprudencia pacifica") e atribuicao de conteudo a
  dispositivo ("o art. X prega que o juiz deve ...") que precisa ser conferida
  contra o texto literal.

USO
  verificar_citacoes.py MINUTA.txt [--acervo livro/] [--livro LIVRO.md] [--anterior VERSAO.txt] [--json]

  --acervo aponta para a pasta gerada por livro/construir_livro.py (texto oficial
  extraido por programa). Com ela, artigo inexistente, revogado ou com paragrafo/
  inciso/alinea que nao existe vira BLOQUEIO, e cada frase que atribui conteudo a
  dispositivo vem acompanhada do texto oficial para confronto.

SAIDA
  Relatorio em Markdown no stdout. Codigo de saida: 0 sem bloqueios,
  1 com bloqueios, 2 erro de uso.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- diplomas
SIGLAS = {"CPC", "CPP", "CP", "CC", "CF", "CDC", "ECA", "CLT", "CTN", "CTB",
          "LEP", "LINDB", "CPPM", "CPM"}
NOMES = {
    r"c[óo]digo\s+de\s+processo\s+civil": "CPC",
    r"c[óo]digo\s+de\s+processo\s+penal": "CPP",
    r"c[óo]digo\s+penal(?!\s+militar)": "CP",
    r"c[óo]digo\s+civil": "CC",
    r"constitui[çc][ãa]o\s+federal": "CF",
    r"c[óo]digo\s+de\s+defesa\s+do\s+consumidor": "CDC",
    r"estatuto\s+da\s+crian[çc]a\s+e\s+do\s+adolescente": "ECA",
    r"c[óo]digo\s+tribut[áa]rio\s+nacional": "CTN",
    r"c[óo]digo\s+de\s+tr[âa]nsito\s+brasileiro": "CTB",
    r"lei\s+maria\s+da\s+penha": "LMP",
    r"lei\s+dos\s+juizados\s+especiais": "L9099",
    r"lei\s+de\s+alimentos": "L5478",
    r"estatuto\s+d[ao]\s+(?:pessoa\s+)?idos[ao]": "EPI",
    r"lei\s+de\s+drogas": "LD",
    r"lei\s+de\s+execu[çc][ãa]o\s+penal": "LEP",
}
# Unico alias numerico fixado: confirmado na sessao de 25/10/2026 (resultado de
# busca sobre a Camara/Planalto). Demais leis ficam pelo proprio numero.
LEI_ALIAS = {"13105/2015": "CPC"}

SIGLA_RE = re.compile(r"\b(" + "|".join(sorted(SIGLAS, key=len, reverse=True)) + r")\b")
NOME_RE = re.compile("(" + "|".join(NOMES) + ")", re.I)
LEI_RE = re.compile(
    r"\b(?:Lei(?:\s+Complementar)?|Decreto-Lei|Decreto)\s+(?:Federal\s+|Estadual\s+)?"
    r"n?[º°o.]*\s*(\d[\d\.]*)\s*/\s*(\d{2,4})", re.I)


def canon_lei(num, ano, prefixo):
    num = num.replace(".", "")
    chave = f"{num}/{ano}"
    if prefixo.lower().startswith("lei") and "complementar" not in prefixo.lower():
        if chave in LEI_ALIAS:
            return LEI_ALIAS[chave]
    return f"{prefixo.strip()} {num}/{ano}"


def achar_diploma(texto, ini, fim, raio=110):
    """Diploma mais proximo: primeiro depois do artigo, depois antes."""
    depois = texto[fim:fim + raio].split("\n\n")[0]
    antes = texto[max(0, ini - raio):ini].split("\n\n")[-1]
    for janela, inverter in ((depois, False), (antes, True)):
        achados = []
        for m in SIGLA_RE.finditer(janela):
            achados.append((m.start(), m.group(1)))
        for m in NOME_RE.finditer(janela):
            for padrao, sigla in NOMES.items():
                if re.fullmatch(padrao, m.group(1), re.I):
                    achados.append((m.start(), sigla))
                    break
        for m in LEI_RE.finditer(janela):
            prefixo = re.match(r"[A-Za-zÀ-ú\- ]+?(?=\s+(?:Federal|Estadual|n|\d))", m.group(0))
            achados.append((m.start(), canon_lei(m.group(1), m.group(2),
                                                 prefixo.group(0) if prefixo else "Lei")))
        if achados:
            achados.sort(key=lambda x: x[0], reverse=inverter)
            return achados[0][1]
    return None


# ------------------------------------------------------------------ artigos
ARTIGO_INI = re.compile(r"\b(?:arts?\.|artigos?)\s*", re.I)
NUM = re.compile(r"\d[\d\.]*(?:-[A-Z])?(?=[^\d\w]|$|º|°)")
ROMANOS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def romano_valido(s):
    if not s or any(c not in ROMANOS for c in s):
        return False
    total, prev = 0, 0
    for c in reversed(s):
        v = ROMANOS[c]
        total += v if v >= prev else -v
        prev = max(prev, v)
    return 0 < total <= 60 and s != "CC"


SUB_RE = re.compile(
    r"\s*,?\s*(?:"
    r"(?P<par>§§?\s*\d+[º°]?(?:-[A-Z])?)"
    r"|(?P<pu>par[áa]grafo\s+[úu]nico)"
    r"|(?P<caput>caput)"
    r"|(?:inc(?:iso)?s?\.?\s+)(?P<inc1>[IVXLC]+)\b"
    r"|(?<=,)\s*(?P<inc2>[IVXLC]+)\b"
    r"|al[íi]neas?\s+[\"“]?(?P<ali>[a-z])[\"”]?"
    r")", re.I)


def parse_artigos(texto):
    """Gera dicts {art, subs, ini, fim}. Expande intervalos simples ('647 a 658')."""
    saida = []
    for m in ARTIGO_INI.finditer(texto):
        pos = m.end()
        ini = m.start()
        pendente_intervalo = None
        while True:
            n = NUM.match(texto, pos)
            if not n:
                break
            art = n.group(0).rstrip(".").replace(".", "")
            pos = n.end()
            if texto[pos:pos + 1] in ("º", "°"):
                pos += 1
            subs = []
            while True:
                s = SUB_RE.match(texto, pos)
                if not s or s.end() == pos:
                    break
                tok = next((v for k, v in s.groupdict().items() if v), None)
                if tok and (not (s.group("inc1") or s.group("inc2")) or
                            romano_valido((s.group("inc1") or s.group("inc2")).upper())):
                    subs.append(re.sub(r"\s+", " ", tok.strip()).lower())
                    pos = s.end()
                else:
                    break
            if pendente_intervalo and art.isdigit() and pendente_intervalo.isdigit():
                a, b = int(pendente_intervalo), int(art)
                if 0 < b - a <= 60:
                    for k in range(a + 1, b):
                        saida.append({"art": str(k), "subs": [], "ini": ini, "fim": pos,
                                      "intervalo": True})
            pendente_intervalo = None
            saida.append({"art": art, "subs": subs, "ini": ini, "fim": pos})
            sep = re.match(r"\s*(,|\be\b|\bou\b|\ba\b|\bao\b|\bà\b)\s*(?=\d)", texto[pos:], re.I)
            if not sep:
                break
            if sep.group(1).lower() in ("a", "ao", "à"):
                pendente_intervalo = art
            pos += sep.end()
    return saida


# ---------------------------------------------------------- demais citacoes
ORGAOS = r"STF|STJ|TST|TSE|TNU|TJ[A-Z]{2}|TRF\s?\d|TRT\s?\d+|TCU|TCE[A-Z]{0,2}"
SUMULA_RE = re.compile(
    r"S[úu]mulas?\s+(?P<vinc>Vinculante\s+)?(?:n[º°o.]*\s*)?(?P<n>\d[\d\.]*)"
    r"(?:\s*/\s*|\s+d[oa]s?\s+)?(?P<orgao>" + ORGAOS + r")?", re.I)
TEMA_RE = re.compile(
    r"Tema(?:\s+Repetitivo|\s+de\s+Repercuss[ãa]o\s+Geral|\s+RG)?\s+(?:n[º°o.]*\s*)?"
    r"(?P<n>\d[\d\.]*)(?:\s*(?:/|d[oa]\s+|-\s*)(?P<orgao>" + ORGAOS + r"))?", re.I)
PROC_RE = re.compile(
    r"\b(?P<cl>REsp|AREsp|EREsp|AgInt|AgRg|EDcl|RE|ARE|HC|RHC|ADI|ADC|ADPF|RMS|Rcl|IRDR|IAC)"
    r"\s*(?:n[º°o.]*\s*)?(?P<n>\d[\d\.\-]*\d(?:/[A-Z]{2})?)")
NORMA_RE = re.compile(
    r"(?P<tipo>Resolu[çc][ãa]o|Provimento|Portaria|Recomenda[çc][ãa]o|Enunciado|"
    r"Instru[çc][ãa]o\s+Normativa)(?P<resto>[^.;\n]{0,40}?\d[\d\.]*"
    r"(?:\s*/\s*\d{2,4})?(?:\s*[-/]\s*[A-Z]{2,6})?)", re.I)
CNJ_RE = re.compile(r"\b(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})\b")
CNJ_CRU_RE = re.compile(r"(?<!\d)(\d{20})(?!\d)")

GENERICAS = [
    (r"jurisprud[êe]ncia\s+(?:\w+\s+){0,2}(?:pac[íi]fica|dominante|consolidada|majorit[áa]ria|firmada|remansosa)",
     "jurisprudência 'pacífica/dominante' sem citação"),
    (r"entendimento\s+(?:\w+\s+){0,2}(?:pac[íi]fico|consolidado|majorit[áa]rio|dominante|firmado)",
     "'entendimento pacífico/consolidado' sem citação"),
    (r"tribunais\s+(?:superiores\s+)?t[êe]m\s+(?:decidido|entendido)", "'tribunais têm decidido' sem citação"),
    (r"\b(?:segundo|conforme|para)\s+a\s+doutrina\b|doutrina\s+(?:majorit[áa]ria|pac[íi]fica|especializada)|\bleciona\b",
     "doutrina invocada sem autor/obra verificados"),
    (r"\bpacificou[-\s]se\b|\bconsolidou[-\s]se\b|\bpacificado\s+(?:no|pelo)\b",
     "'pacificado/consolidado' sem citação"),
]
VERBOS_ATRIBUICAO = re.compile(
    r"\b(prev[êe]|determina|estabelece|disp[õo]e|imp[õo]e|exige|autoriza|veda|pro[íi]be|assegura|"
    r"garante|reconhece|obriga|permite|faculta|define|prescreve)\s+(?:expressamente\s+)?que\b", re.I)
FIM_FRASE = re.compile(r"(?<=[A-Za-zÀ-ú\d\)º°])\.\s+(?=[A-ZÀ-Ú])")
CONDICAO = re.compile(r"\b(desde\s+que|salvo|exceto|somente\s+se|apenas\s+se|contanto\s+que)\b", re.I)
MARCADOR_RE = re.compile(
    r"\[(?:JURISPRUD[ÊE]NCIA|FUNDAMENTO\s+LEGAL|DISPOSITIVO|FATO|DOCUMENTO|DADO|QUALIFICA[ÇC][ÃA]O|"
    r"STATUS|VERIFICAR|A\s+CONFIRMAR)[^\]]*\]", re.I)
PLACEHOLDER_RE = re.compile(r"\[\s*(?:\.\.\.|…)\s*\]")


def cnj_dv_ok(seq, dv, ano, j, tr, org):
    base = f"{seq}{ano}{j}{tr}{org}00"
    return int(dv) == 98 - (int(base) % 97)


def norm_espaco(s):
    return re.sub(r"\s+", " ", s).strip()


def trecho(texto, ini, fim, raio=70):
    return norm_espaco(texto[max(0, ini - raio):fim + raio])


def extrair(texto):
    """Lista de citacoes: dict(tipo, chave, exibicao, ini, fim, subs, avisos)."""
    cits = []
    for a in parse_artigos(texto):
        dip = achar_diploma(texto, a["ini"], a["fim"])
        chave = f"{dip}:art:{a['art']}" if dip else f"?:art:{a['art']}"
        cits.append({"tipo": "artigo", "chave": chave, "ini": a["ini"], "fim": a["fim"],
                     "exibicao": f"art. {a['art']}" + (", " + ", ".join(x.upper() if re.fullmatch("[ivxlc]+", x) else x for x in a["subs"]) if a["subs"] else "")
                                 + (f" {dip}" if dip else " (diploma NÃO identificado)"),
                     "subs": a["subs"], "diploma": dip, "intervalo": a.get("intervalo", False)})
    for m in SUMULA_RE.finditer(texto):
        orgao = (m.group("orgao") or ("STF" if m.group("vinc") else "?")).upper().replace(" ", "")
        cits.append({"tipo": "súmula", "chave": f"SUMULA:{orgao}:{m.group('n').replace('.', '')}",
                     "ini": m.start(), "fim": m.end(), "subs": [],
                     "exibicao": f"Súmula {'Vinculante ' if m.group('vinc') else ''}{m.group('n')}/{orgao}"})
    for m in TEMA_RE.finditer(texto):
        orgao = (m.group("orgao") or "?").upper().replace(" ", "")
        cits.append({"tipo": "tema", "chave": f"TEMA:{orgao}:{m.group('n').replace('.', '')}",
                     "ini": m.start(), "fim": m.end(), "subs": [],
                     "exibicao": f"Tema {m.group('n')}/{orgao}"})
    for m in PROC_RE.finditer(texto):
        cits.append({"tipo": "processo", "chave": f"PROC:{m.group('cl')}:{m.group('n')}",
                     "ini": m.start(), "fim": m.end(), "subs": [],
                     "exibicao": f"{m.group('cl')} {m.group('n')}"})
    for m in NORMA_RE.finditer(texto):
        k = norm_espaco(m.group(0)).lower()
        cits.append({"tipo": "norma", "chave": f"NORMA:{k}", "ini": m.start(), "fim": m.end(),
                     "subs": [], "exibicao": norm_espaco(m.group(0))})
    for m in LEI_RE.finditer(texto):
        prefixo = re.match(r"[A-Za-zÀ-ú\- ]+?(?=\s+(?:Federal|Estadual|n|\d))", m.group(0))
        c = canon_lei(m.group(1), m.group(2), prefixo.group(0) if prefixo else "Lei")
        cits.append({"tipo": "lei", "chave": f"LEI:{c}", "ini": m.start(), "fim": m.end(),
                     "subs": [], "exibicao": norm_espaco(m.group(0))})
    cits.sort(key=lambda c: c["ini"])
    return cits


# -------------------------------------------------------------------- livro
def ler_livro(caminho):
    """Le tabela Markdown. Retorna (chaves_N3, subs_por_chave, linhas_nao_N3)."""
    n3, subs, outros = set(), {}, []
    cab = None
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        if not linha.strip().startswith("|"):
            continue
        cel = [c.strip() for c in linha.strip().strip("|").split("|")]
        baixo = [c.lower() for c in cel]
        if cab is None:
            if any("citação" in c or "citacao" in c for c in baixo) and any("nível" in c or "nivel" in c for c in baixo):
                cab = {"cit": next(i for i, c in enumerate(baixo) if "cita" in c),
                       "niv": next(i for i, c in enumerate(baixo) if "nível" in c or "nivel" in c)}
            continue
        if set("".join(cel)) <= set("-: "):
            continue
        if len(cel) <= max(cab.values()):
            continue
        nivel = cel[cab["niv"]].upper().replace(" ", "")
        cs = extrair(cel[cab["cit"]])
        if not cs:
            outros.append((cel[cab["cit"]], nivel, "linha sem citação reconhecível"))
            continue
        for c in cs:
            if nivel.startswith("N3"):
                n3.add(c["chave"])
                subs.setdefault(c["chave"], set()).update(c["subs"])
            else:
                outros.append((cel[cab["cit"]], nivel, "não é N3"))
    return n3, subs, outros


# ------------------------------------------------------------------- acervo
def carregar_acervo(pasta):
    """Le livro/<SIGLA>.json gerados por construir_livro.py. Chaveia por sigla e por lei."""
    acervo = {}
    for arq in sorted(Path(pasta).glob("*.json")):
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
            meta, arts = d["meta"], d["artigos"]
        except (KeyError, ValueError):
            continue
        reg = {"meta": meta, "arts": {a["art"]: a for a in arts}}
        chaves = {meta["sigla"]}
        m = LEI_RE.search(meta.get("titulo", ""))
        if m:
            prefixo = re.match(r"[A-Za-zÀ-ú\- ]+?(?=\s+(?:Federal|Estadual|n|\d))", m.group(0))
            chaves.add(canon_lei(m.group(1), m.group(2), prefixo.group(0) if prefixo else "Lei"))
        for k in chaves:
            acervo[k] = reg
    return acervo


def sub_existe(linhas, sub):
    sub = sub.strip()
    if sub == "caput":
        return True
    if sub.startswith("par") and "nico" in sub:
        return any(re.match(r"par[áa]grafo\s+[úu]nico", l, re.I) for l in linhas)
    m = re.match(r"§§?\s*(\d+)", sub)
    if m:
        return any(re.match(rf"§\s*{m.group(1)}\s*[º°o]?(?!\d)", l) for l in linhas)
    if re.fullmatch(r"[ivxlc]+", sub, re.I):
        return any(re.match(rf"{sub.upper()}\s*[-–—]", l) for l in linhas)
    if re.fullmatch(r"[a-z]", sub):
        return any(re.match(rf"{sub}\s*\)", l) for l in linhas)
    return True


# --------------------------------------------------------------------- main
def analisar(texto, livro=None, anterior=None, acervo=None):
    bloq, atenc, info = [], [], []
    cits = extrair(texto)
    literais = []

    # acervo oficial (texto literal extraido por programa)
    if acervo:
        for c in cits:
            if c["tipo"] != "artigo" or c["diploma"] not in acervo:
                continue
            reg = acervo[c["diploma"]]
            fonte = f"{reg['meta']['sigla']}, baixado em {reg['meta']['baixado_em']}"
            num = c["chave"].split(":art:")[1]
            art = reg["arts"].get(num)
            if not art:
                bloq.append(("INEXISTENTE", c["exibicao"], f"artigo NÃO existe no texto oficial ({fonte})"))
                continue
            linhas = art["texto"]
            if re.search(r"\((?:Revogad|Vetad)", linhas[0]) and len(linhas) == 1:
                bloq.append(("REVOGADO", c["exibicao"], f"no texto atualizado consta: «{linhas[0][:160]}» ({fonte}); conferir a vigência na data do fato"))
            faltam = [x for x in c["subs"] if not sub_existe(linhas[1:], x)]
            if faltam:
                bloq.append(("SUBDIVISÃO", c["exibicao"], f"não existe neste artigo: {', '.join(faltam)} ({fonte})"))
                continue
            c["acervo_ok"] = True
            c["literal"] = (fonte, linhas)

    # numeros CNJ
    for m in CNJ_RE.finditer(texto):
        if not cnj_dv_ok(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)):
            bloq.append(("CNJ", m.group(0), "dígito verificador INVÁLIDO (módulo 97): número digitado errado ou inventado"))
    for m in CNJ_CRU_RE.finditer(texto):
        s = m.group(1)
        if not cnj_dv_ok(s[:7], s[7:9], s[9:13], s[13], s[14:16], s[16:20]):
            atenc.append(("CNJ", s, "sequência de 20 dígitos sem pontuação com DV inválido"))

    # livro
    n3 = subs_livro = None
    if livro:
        n3, subs_livro, nao_n3 = ler_livro(livro)
        for txt, niv, why in nao_n3:
            info.append(("LIVRO", txt, f"{why} (nível '{niv}') — não autoriza citação"))
        for c in cits:
            if c["tipo"] == "artigo" and not c["diploma"]:
                bloq.append(("DIPLOMA", c["exibicao"], "diploma não identificado perto do artigo: citar o diploma por extenso/sigla"))
                continue
            if c.get("acervo_ok"):
                continue
            if c["tipo"] in ("lei",) and acervo and c["chave"].split(":", 1)[1] in acervo:
                continue
            if c["tipo"] in ("lei",) and c["chave"] not in n3:
                bloq.append(("LIVRO", c["exibicao"], "lei citada que não consta do Livro como N3"))
                continue
            if c["tipo"] != "lei" and c["chave"] not in n3:
                bloq.append(("LIVRO", c["exibicao"], "citação que não consta do Livro como N3 (não verificada em texto literal)"))
                continue
            if c["tipo"] == "artigo" and c["subs"]:
                if not set(c["subs"]) <= subs_livro.get(c["chave"], set()):
                    atenc.append(("GRANULARIDADE", c["exibicao"],
                                  "o Livro não registra o §/inciso/alínea citado; conferir o nível exato no texto literal"))
            if c["tipo"] == "artigo" and c.get("intervalo"):
                atenc.append(("INTERVALO", c["exibicao"], "artigo incluído por intervalo ('arts. X a Y'): conferir que o Livro cobre cada um"))
    elif acervo:
        for c in cits:
            if c["tipo"] == "artigo" and not c["diploma"]:
                bloq.append(("DIPLOMA", c["exibicao"], "diploma não identificado perto do artigo: citar o diploma por extenso/sigla"))
            elif c["tipo"] == "artigo" and not c.get("acervo_ok") and c["diploma"] not in acervo:
                bloq.append(("FORA DO ACERVO", c["exibicao"], "diploma fora do acervo oficial e sem Livro: verificar em fonte oficial"))
            elif c["tipo"] in ("súmula", "tema", "processo", "norma"):
                atenc.append(("PRECEDENTE/NORMA", c["exibicao"], "não coberto pelo acervo de leis: verificar no Banco Nacional de Precedentes ou na fonte oficial e registrar no Livro"))
    else:
        info.append(("LIVRO", "-", "nenhum Livro informado (--livro): citações NÃO foram confrontadas com autoridades verificadas"))

    # versao anterior
    if anterior:
        antes = {c["chave"] for c in extrair(anterior)}
        agora = {c["chave"] for c in cits}
        for k in sorted(agora - antes):
            nome = next(c["exibicao"] for c in cits if c["chave"] == k)
            bloq.append(("NOVA", nome, "citação ausente da versão auditada: exige nova auditoria"))
        for k in sorted(antes - agora):
            info.append(("REMOVIDA", k, "citação existia na versão anterior e saiu desta"))

    # atribuicao de conteudo a dispositivo
    for c in cits:
        if c["tipo"] != "artigo":
            continue
        janela = texto[c["fim"]:c["fim"] + 220].split("\n")[0]
        corte = FIM_FRASE.search(janela)
        if corte:
            janela = janela[:corte.start() + 1]
        v = VERBOS_ATRIBUICAO.search(janela)
        if v:
            frase = janela
            conds = CONDICAO.findall(frase)
            msg = (f"a minuta diz que o dispositivo '{v.group(1)} que ...'. Conferir CADA comando, requisito"
                   f"{' e exceção (' + ', '.join(sorted(set(x.lower() for x in conds))) + ')' if conds else ''}"
                   " contra o texto literal e confirmar que o TEMA do dispositivo é o do caso (regra 20)")
            atenc.append(("ATRIBUIÇÃO", c["exibicao"] + " :: «" + norm_espaco(texto[c["ini"]:c["fim"] + v.end() + 90]) + "…»", msg))
            if c.get("literal"):
                literais.append((c["exibicao"], norm_espaco(frase), c["literal"]))

    # genericas
    for padrao, rotulo in GENERICAS:
        for m in re.finditer(padrao, texto, re.I):
            atenc.append(("GENÉRICA", trecho(texto, m.start(), m.end(), 40), rotulo))

    marcadores = [norm_espaco(m.group(0)) for m in MARCADOR_RE.finditer(texto)]
    placeholders = len(PLACEHOLDER_RE.findall(texto))
    if placeholders:
        atenc.append(("PLACEHOLDER", f"{placeholders}x '[...]'", "lacuna de modelo não preenchida nem convertida em marcador"))

    return {"citacoes": cits, "bloqueios": bloq, "atencao": atenc, "info": info, "literais": literais, "acervo_usado": bool(acervo),
            "marcadores": marcadores, "livro_usado": bool(livro), "n3": n3}


def relatorio(res):
    L = ["# Verificação mecânica de citações", "",
         "> Esta verificação é MECÂNICA. Ela não prova que a norma existe nem que diz o que a minuta afirma.",
         "> Cada item 'ATRIBUIÇÃO' exige leitura do texto literal do dispositivo.", ""]
    por_tipo = {}
    for c in res["citacoes"]:
        por_tipo.setdefault(c["tipo"], set()).add(c["chave"])
    L.append("## Resumo (copiar para a nota final da auditoria)")
    L.append("")
    if por_tipo:
        L.append("- Citações distintas: " + "; ".join(f"{t}: {len(v)}" for t, v in sorted(por_tipo.items())))
    else:
        L.append("- Nenhuma citação reconhecida.")
    L.append(f"- Confrontadas com o Livro: {'sim' if res['livro_usado'] else 'NÃO (sem --livro)'}")
    L.append(f"- Confrontadas com o acervo oficial: {'sim' if res.get('acervo_usado') else 'NÃO (sem --acervo)'}")
    L.append(f"- Bloqueios: {len(res['bloqueios'])} | Atenções: {len(res['atencao'])} | Marcadores pendentes: {len(res['marcadores'])}")
    L.append("")
    for titulo, itens in (("Bloqueios (a minuta NÃO pode ser entregue como pronta)", res["bloqueios"]),
                          ("Atenções (conferir antes de entregar)", res["atencao"]),
                          ("Informações", res["info"])):
        if itens:
            L.append(f"## {titulo}")
            L.append("")
            L.append("| Tipo | Item | Observação |")
            L.append("|---|---|---|")
            for t, i, o in itens:
                L.append(f"| {t} | {i.replace('|', '/')} | {o} |")
            L.append("")
    if res["marcadores"]:
        L.append("## Marcadores pendentes (devem chegar visíveis ao usuário)")
        L.append("")
        for m in res["marcadores"]:
            L.append(f"- {m}")
        L.append("")
    if res.get("literais"):
        L.append("## Confronto: o que a minuta diz × texto oficial")
        L.append("")
        for exib, frase, (fonte, linhas) in res["literais"]:
            L.append(f"### {exib}")
            L.append("")
            L.append(f"**Minuta:** «{frase}»")
            L.append("")
            L.append(f"**Texto oficial ({fonte}):**")
            L.append("")
            L += [f"> {t}" for t in linhas]
            L.append("")
            L.append("Conferir: o tema é o mesmo? Cada comando está no texto? Alguma condição foi acrescentada ou omitida?")
            L.append("")
    L.append("## Citações extraídas")
    L.append("")
    for c in res["citacoes"]:
        L.append(f"- [{c['tipo']}] {c['exibicao']}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Verificador mecânico de citações jurídicas.")
    ap.add_argument("minuta")
    ap.add_argument("--livro", help="Livro de Autoridades (tabela Markdown)")
    ap.add_argument("--anterior", help="versão anterior já auditada, para detectar citação nova")
    ap.add_argument("--acervo", help="pasta com o texto oficial extraído (livro/*.json de construir_livro.py)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        texto = Path(a.minuta).read_text(encoding="utf-8")
        ant = Path(a.anterior).read_text(encoding="utf-8") if a.anterior else None
        acervo = carregar_acervo(a.acervo) if a.acervo else None
        res = analisar(texto, a.livro, ant, acervo)
    except (OSError, UnicodeDecodeError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    if a.json:
        res = dict(res, n3=sorted(res["n3"]) if res["n3"] else None,
                   literais=[[e, f, list(l)] for e, f, l in res["literais"]],
                   citacoes=[{k: v for k, v in c.items() if k in ("tipo", "chave", "exibicao")} for c in res["citacoes"]])
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(relatorio(res))
    return 1 if res["bloqueios"] else 0


if __name__ == "__main__":
    sys.exit(main())
