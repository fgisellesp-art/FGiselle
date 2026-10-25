#!/usr/bin/env python3
"""construir_livro.py - monta o Livro de Autoridades a partir do texto oficial.

Baixa a pagina de texto atualizado de cada diploma listado em fontes.json
(portal Legin da Camara dos Deputados) e separa, POR PROGRAMA, o texto literal
de cada artigo. Nada e digitado: o que sai em livro/<SIGLA>.md e livro/<SIGLA>.json
e copia do HTML baixado, com URL, data/hora do download e SHA-256 do arquivo.

USO
  construir_livro.py                 # todos os diplomas de fontes.json
  construir_livro.py CPC ECA         # apenas os indicados
  construir_livro.py --html arq.html --sigla CPC --url URL   # arquivo ja baixado

Limites: o texto atualizado da Camara e compilacao; nao substitui o publicado no
Diario Oficial. Registre a data do download e reconsulte quando o fato ou o ato
for posterior a ela.
"""
import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CABECALHOS = re.compile(r"^(PARTE|LIVRO|T[ÍI]TULO|CAP[ÍI]TULO|Se[çc][ãa]o|Subse[çc][ãa]o)\b")
ARTIGO = re.compile(r"^Art(\.?)\s*(l?\d[\d\.]*)\s*(?:[º°o])?\s*((?:\s*-\s*[A-Z])+)?\s*[\.\-–]?\s*(.*)$")  # grupos: ponto, numero, sufixo, resto
GRUPO = re.compile(r"^Arts\.\s*(\d[\d\.]*)\s*[º°]?\s*a\s*(\d[\d\.]*)\s*[º°]?\s*\.?\s*(.*)$")
ADCT = re.compile(r"^ATO DAS DISPOSI[ÇC][ÕO]ES CONSTITUCIONAIS TRANSIT[ÓO]RIAS$")


def baixar(url, destino):
    subprocess.run(["curl", "-sS", "-L", "-m", "120", "-o", str(destino), url], check=True)
    return destino.read_bytes()


def html_para_linhas(raw):
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            t = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    t = re.sub(r"(?is)<(script|style|head).*?</\1>", "", t)
    t = re.sub(r"[\r\n]+", " ", t)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>|</li>|</tr>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = t.replace("\xa0", " ")
    return [re.sub(r"[ \t]+", " ", l).strip() for l in t.split("\n") if l.strip()]


def separar_artigos(linhas):
    artigos, atual, local = [], None, {}
    nivel = {"PARTE": 0, "LIVRO": 1, "TITULO": 2, "CAPITULO": 3, "SECAO": 4, "SUBSECAO": 5}
    prefixo = ""
    for l in linhas:
        if ADCT.match(l):
            prefixo, local = "ADCT-", {}
            continue
        g = GRUPO.match(l)
        if g:
            a, b = int(g.group(1).replace(".", "")), int(g.group(2).replace(".", ""))
            if 0 < b - a <= 200:
                for n in range(a, b + 1):
                    artigos.append({"art": f"{prefixo}{n}", "localizacao": " > ".join(local.values()),
                                    "texto": [l], "obs": f"artigo incluído em dispositivo agrupado no original ({l.split('.')[0]}...)"})
                atual = artigos[-1]
                continue
        c = CABECALHOS.match(l)
        if c and len(l) < 200 and not ARTIGO.match(l):
            chave = (c.group(1).upper().replace("Í", "I").replace("Ç", "C").replace("Ã", "A"))
            n = nivel.get(chave, 6)
            local = {k: v for k, v in local.items() if nivel.get(k, 6) < n}
            local[chave] = l
            continue
        m = ARTIGO.match(l)
        if m:
            sem_ponto = m.group(1) == ""
            bruto = m.group(2)
            num = bruto.lstrip("l").rstrip(".").replace(".", "")
            if bruto.startswith("l"):
                num = "1" + num
            num = prefixo + num + (m.group(3).replace(" ", "") if m.group(3) else "")
            atual = {"art": num, "localizacao": " > ".join(local.values()), "texto": [l]}
            if sem_ponto:
                atual["obs"] = f"no HTML original consta 'Art {bruto}' (sem ponto após 'Art'); lido como {num}"
            if bruto.startswith("l"):
                atual["obs"] = f"no HTML original consta 'Art. {bruto}' (letra l no lugar do algarismo 1); lido como {num}"
            artigos.append(atual)
        elif atual is not None:
            atual["texto"].append(l)
    return artigos


def gravar(sigla, meta, artigos):
    vistos = {}
    for a in artigos:
        vistos.setdefault(a["art"], 0)
        vistos[a["art"]] += 1
    dup = sorted(k for k, v in vistos.items() if v > 1)
    meta = dict(meta, total_artigos=len(artigos), numeros_repetidos=dup)
    (AQUI / f"{sigla}.json").write_text(
        json.dumps({"meta": meta, "artigos": artigos}, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"# {sigla} — {meta['titulo']}", "",
         f"- Fonte: {meta['url']}",
         f"- Baixado em: {meta['baixado_em']}",
         f"- SHA-256 do HTML: `{meta['sha256']}`",
         f"- Artigos extraídos: {len(artigos)}",
         "- Texto copiado por programa do HTML oficial, sem digitação. Compilação da Câmara: não substitui o Diário Oficial.",
         ""]
    if dup:
        L += [f"- Atenção: números de artigo repetidos no HTML ({', '.join(dup[:20])}). Conferir no original antes de citar.", ""]
    for a in artigos:
        L.append(f"## Art. {a['art']}")
        if a["localizacao"]:
            L.append(f"_{a['localizacao']}_")
        if a.get("obs"):
            L.append(f"**Obs. de extração:** {a['obs']}")
        L.append("")
        L += [f"> {t}" for t in a["texto"]]
        L.append("")
    (AQUI / f"{sigla}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return meta


def processar(sigla, titulo, url, html_local=None):
    cache = AQUI / "_html"
    cache.mkdir(exist_ok=True)
    destino = cache / f"{sigla}.html"
    raw = Path(html_local).read_bytes() if html_local else baixar(url, destino)
    if html_local:
        destino.write_bytes(raw)
    meta = {"sigla": sigla, "titulo": titulo, "url": url,
            "baixado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    artigos = separar_artigos(html_para_linhas(raw))
    if len(artigos) < 5:
        raise RuntimeError(f"{sigla}: só {len(artigos)} artigos extraídos; página errada ou formato inesperado")
    return gravar(sigla, meta, artigos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("siglas", nargs="*")
    ap.add_argument("--html")
    ap.add_argument("--sigla")
    ap.add_argument("--url")
    a = ap.parse_args()
    fontes = json.loads((AQUI / "fontes.json").read_text(encoding="utf-8"))
    if a.html:
        f = fontes.get(a.sigla, {"titulo": a.sigla, "url": a.url})
        alvos = [(a.sigla, f["titulo"], a.url or f["url"], a.html)]
    else:
        alvos = [(s, f["titulo"], f["url"], None) for s, f in fontes.items() if not a.siglas or s in a.siglas]
    erros = 0
    for sigla, titulo, url, local in alvos:
        try:
            m = processar(sigla, titulo, url, local)
            print(f"{sigla}: {m['total_artigos']} artigos | {m['bytes']} bytes | repetidos: {len(m['numeros_repetidos'])}")
        except Exception as e:  # noqa: BLE001 - relatar e seguir para o proximo diploma
            erros += 1
            print(f"{sigla}: ERRO {e}", file=sys.stderr)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
