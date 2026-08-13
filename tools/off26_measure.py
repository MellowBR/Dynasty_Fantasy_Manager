# -*- coding: utf-8 -*-
"""off26_measure.py — medição da família OFF26 no backlog ativo (item O6).

É o instrumento da F1 do O6 (MAN-O6-F1, 13/08/2026), persistido para a
re-medição do gate: **pós-26/08 (fechamento + sync final da campanha 2026),
rodar este script e comparar com os números do parecer** (seção O6 — ativo
473,7 KB; família = 13 seções / 236,3 KB = 49,9%; projeção do split 245,5 KB).
A comparabilidade exige o mesmo instrumento, não uma reimplementação.

Mede, sobre `improvements.md` (ou o caminho passado em argv[1]):
  - tamanho total do ativo;
  - seções ### OFF26-* (bloco até o próximo heading nível <=3): bytes + status;
  - narrativa reancorada sob OFF26-20 e bloco de contexto `## Offseason 2026`;
  - rows OFF26 do Status Rápido por status;
  - projeção do split (o que sairia / o que restaria);
  - maiores seções não-OFF26 e as encravadas no bloco da campanha;
  - cross-refs [[...]] que virariam cross-file.

Read-only, stdlib apenas. Blocos opcionais (fixture pré-O5, narrativa) são
pulados com aviso se a âncora não existir mais — esperado após o sunset.

Uso:    python tools/off26_measure.py [caminho/para/improvements.md]
"""
import io
import os
import re
import sys
from collections import Counter

def fe(t):
    for ch in t:
        if ch == "\U0001F532": return "🔲"
        if ch == "⚠": return "⚠️"
        if ch == "✅": return "✅"
    return None

def load(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.readlines()

def blocks(lines):
    """Blocos de seção ### (até o próximo heading nível <=3)."""
    marks = [i for i, l in enumerate(lines) if l.startswith("### ") or
             (l.startswith("## ") and not l.startswith("###"))]
    out = []
    for k, i in enumerate(marks):
        if not lines[i].startswith("### "):
            continue
        end = marks[k + 1] if k + 1 < len(marks) else len(lines)
        m = re.match(r"###\s+([A-Za-z0-9][A-Za-z0-9-]*)", lines[i])
        sid = m.group(1) if m else "?"
        size = sum(len(l.encode("utf-8")) for l in lines[i:end])
        st = None
        for b in lines[i + 1:end]:
            if b.strip():
                st = fe(b)
                break
        out.append((sid, i + 1, end, size, st, lines[i].rstrip()[:70]))
    return out

def main(argv):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = argv[1] if len(argv) > 1 else os.path.join(repo_root, "improvements.md")
    if not os.path.isfile(path):
        print("off26_measure: arquivo não encontrado: %s" % path)
        return 2

    lines = load(path)
    total = sum(len(l.encode("utf-8")) for l in lines)
    print("ATIVO: %s" % path)
    print("  %d bytes (%.1f KB) / %d linhas" % (total, total / 1024.0, len(lines)))

    bl = blocks(lines)
    off = [b for b in bl if b[0].startswith("OFF26")]
    non = [b for b in bl if not b[0].startswith("OFF26")]

    print()
    print("== SECOES ### OFF26-* (bloco ate proximo heading <=3) ==")
    for sid, i, end, size, st, h in off:
        print("  %-10s %-3s linhas %5d-%-5d %7.1f KB" % (sid, st or "?", i, end, size / 1024.0))
    soff = sum(b[3] for b in off)
    pct = 100.0 * soff / total if total else 0.0
    print("  TOTAL: %d secoes, %d bytes (%.1f KB) = %.1f%% do ativo"
          % (len(off), soff, soff / 1024.0, pct))
    print("  por status:", dict(Counter(b[4] for b in off)))

    # narrativa reancorada dentro do OFF26-20 (âncora some quando o item migrar)
    try:
        i_f1b = next(i for i, l in enumerate(lines) if l.startswith("#### F1B (MAN-OFF26-20"))
        i_ux = next(i for i, l in enumerate(lines) if l.startswith("## Itens UX"))
        narr = sum(len(l.encode("utf-8")) for l in lines[i_f1b:i_ux])
        print("  (dentro do OFF26-20: narrativa reancorada F1B..CLOSE = %.1f KB)" % (narr / 1024.0))
    except StopIteration:
        print("  (narrativa F1B..CLOSE nao encontrada — esperado se OFF26-20 ja migrou)")

    # bloco de contexto '## Offseason 2026' fora de secao
    hb = 0
    try:
        i_h = next(i for i, l in enumerate(lines) if l.startswith("## Offseason 2026"))
        i_h_end = next(i for i in range(i_h + 1, len(lines)) if lines[i].startswith("### "))
        hb = sum(len(l.encode("utf-8")) for l in lines[i_h:i_h_end])
        print("  (bloco de contexto '## Offseason 2026' fora de secao: %.1f KB, linhas %d-%d)"
              % (hb / 1024.0, i_h + 1, i_h_end))
    except StopIteration:
        print("  (bloco '## Offseason 2026' nao encontrado — esperado se ja aposentado)")

    # Status Rapido: rows OFF26 (split de celulas trata \| escapado)
    sr_off = []
    in_sr = False
    for ln in lines:
        if ln.startswith("## Status R"):
            in_sr = True
            continue
        if in_sr and ln.startswith("## "):
            break
        if in_sr and ln.startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", ln.strip())]
            if len(cells) >= 5 and cells[1].replace("**", "").strip() not in ("ID", "") \
               and not set(cells[1]) <= set("-: "):
                rid = cells[1].replace("**", "").strip()
                if rid.startswith("OFF26"):
                    sr_off.append((rid, fe(cells[-2])))
    print()
    print("== ROWS OFF26 no Status Rapido ==")
    print("  total:", len(sr_off), "| por status:", dict(Counter(s for _, s in sr_off)))
    det = set(b[0] for b in off)
    print("  rows OFF26 SEM secao no ativo (migradas/stub):",
          sorted(r for r, s in sr_off if r not in det))

    rest = total - soff - hb
    print()
    print("== PROJECAO DO SPLIT (secoes OFF26 + bloco de contexto) ==")
    print("  sairia: %.1f KB | restaria no ativo: %.1f KB"
          % ((soff + hb) / 1024.0, rest / 1024.0))

    print()
    print("== TOP 10 secoes nao-OFF26 por bytes ==")
    for sid, i, end, size, st, h in sorted(non, key=lambda b: -b[3])[:10]:
        print("  %-14s %-3s %7.1f KB" % (sid, st or "?", size / 1024.0))

    # secoes nao-OFF26 fisicamente dentro do bloco da campanha
    try:
        i_h = next(i for i, l in enumerate(lines) if l.startswith("## Offseason 2026"))
        i_ux = next((i for i, l in enumerate(lines) if l.startswith("## Itens UX")), len(lines))
        inside = [b for b in non if i_h < b[1] < i_ux]
        print()
        print("== Secoes nao-OFF26 fisicamente dentro do bloco '## Offseason 2026' ==")
        for sid, i, end, size, st, h in inside:
            print("  %-14s %-3s %7.1f KB  linhas %d-%d" % (sid, st or "?", size / 1024.0, i, end))
    except StopIteration:
        pass

    # cross-refs [[...]] que virariam cross-file
    off_ranges = [(b[1] - 1, b[2]) for b in off]
    def in_off(idx):
        return any(a <= idx < e for a, e in off_ranges)
    total_refs = out_refs = in_refs_out = 0
    for i, l in enumerate(lines):
        for m in re.findall(r"\[\[([A-Za-z0-9-]+)\]\]", l):
            total_refs += 1
            if m.startswith("OFF26") and not in_off(i):
                out_refs += 1
            if not m.startswith("OFF26") and in_off(i):
                in_refs_out += 1
    print()
    print("== CROSS-REFS [[...]] ==")
    print("  total no ativo: %d | [[OFF26-*]] de FORA dos blocos: %d | "
          "[[nao-OFF26]] de DENTRO: %d | cross-file no split: %d"
          % (total_refs, out_refs, in_refs_out, out_refs + in_refs_out))

    # fixture pre-O5 (opcional — conferencia historica da baseline externa)
    bk = os.path.join(repo_root, "improvements_backup_pre_O5_2026-08-13.md")
    if os.path.isfile(bk):
        lb = load(bk)
        offb = [b for b in blocks(lb) if b[0].startswith("OFF26")]
        print()
        print("== FIXTURE PRE-O5 (referencia historica) ==")
        print("  secoes OFF26 pre-O5: %d, %.1f KB"
              % (len(offb), sum(b[3] for b in offb) / 1024.0))
    return 0

if __name__ == "__main__":
    try:  # console Windows redirecionado pode estar em cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main(sys.argv))
