# -*- coding: utf-8 -*-
"""backlog_audit.py — auditor poka-yoke do backlog ativo (item O5, 13/08/2026).

Valida o invariante estrutural de `improvements.md` (o backlog ATIVO do esquema
de três arquivos do O3) e falha com exit code != 0 apontando cada violação.

Invariantes (a regra O3, agora verificada por máquina em vez de disciplina):
  V1  nenhuma seção `###` com status ✅ no ativo (✅ migra ao archive no fechamento);
  V2  toda seção `###` tem emoji de status reconhecível (🔲/⚠️/✅) no heading ou
      nas primeiras linhas do corpo — "1 seção ### = 1 item com emoji";
  V3  todo ID de seção detalhada existe no Status Rápido;
  V4  toda row 🔲/⚠️ do Status Rápido tem seção detalhada (vice-versa do V3);
  V5  toda row do Status Rápido tem emoji de status reconhecível;
  V6  IDs únicos (entre seções `###` e entre rows do Status Rápido).

Classificação: "primeiro emoji da célula vence" (precedente O3) — vale para a
célula Status da tabela e para a janela de leitura da seção. Divergência de
emoji seção × Status Rápido é AVISO (não falha): pode ser legítima (ex.: fatia
fechada dentro de item aberto) e a arbitragem é humana.

Uso:    python tools/backlog_audit.py [caminho/para/improvements.md]
        (default: improvements.md na raiz do repo, irmã de tools/)

Read-only por construção: o arquivo é aberto apenas para leitura; nada é
corrigido automaticamente. Zero dependências fora da stdlib.
"""
import io
import os
import re
import sys

EMOJI_TODO = "\U0001F532"   # 🔲
EMOJI_WARN = "⚠"       # ⚠ (️ variation selector opcional)
EMOJI_DONE = "✅"       # ✅

STATUS_NAME = {EMOJI_TODO: "🔲", EMOJI_WARN: "⚠️", EMOJI_DONE: "✅"}

# quantas linhas não-vazias do corpo participam da janela de status da seção
STATUS_WINDOW = 3

SECTION_ID_RE = re.compile(
    r"^###\s+(?:[^A-Za-z0-9]*\s)?([A-Za-z0-9][A-Za-z0-9-]*)"
)
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")  # pipes escapados (\|) não separam célula


def first_status(text):
    """Primeiro emoji de status no texto — 'primeiro emoji vence' (O3)."""
    for ch in text:
        if ch in STATUS_NAME:
            return ch
    return None


def parse_status_rapido(lines):
    """Rows da tabela entre '## Status Rápido' e o próximo '## '.

    Devolve lista de (linha, id, status_emoji_ou_None)."""
    rows = []
    in_table = False
    for lineno, ln in enumerate(lines, 1):
        if ln.startswith("## Status R"):
            in_table = True
            continue
        if in_table and ln.startswith("## "):
            break
        if not in_table or not ln.startswith("|"):
            continue
        cells = [c.strip() for c in CELL_SPLIT_RE.split(ln.strip())]
        if len(cells) < 5:
            continue
        raw_id = cells[1].replace("**", "").strip()
        if not raw_id or raw_id == "ID" or set(raw_id) <= set("-: "):
            continue  # header / divisor
        rows.append((lineno, raw_id, first_status(cells[-2])))
    return rows


def parse_sections(lines):
    """Seções de nível exatamente ### (itens). #### e ##### são sub-blocos.

    Devolve lista de (linha, id_ou_None, status_emoji_ou_None, heading)."""
    marks = [
        (i, ln.rstrip("\n"))
        for i, ln in enumerate(lines, 1)
        if ln.startswith("### ")
    ]
    out = []
    for i, heading in marks:
        m = SECTION_ID_RE.match(heading)
        sec_id = m.group(1) if m else None
        status = first_status(heading)
        if status is None:
            seen = 0
            for body_ln in lines[i:]:
                if body_ln.startswith("#"):
                    break  # próximo heading (qualquer nível) encerra a janela
                if not body_ln.strip():
                    continue
                status = first_status(body_ln)
                seen += 1
                if status is not None or seen >= STATUS_WINDOW:
                    break
        out.append((i, sec_id, status, heading))
    return out


def audit(path):
    with io.open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    rows = parse_status_rapido(lines)
    sections = parse_sections(lines)

    violations = []
    warnings = []

    row_ids = {}
    for lineno, rid, status in rows:
        if rid in row_ids:
            violations.append(
                "V6 linha %d: ID duplicado no Status Rápido: %s (1ª na linha %d)"
                % (lineno, rid, row_ids[rid])
            )
        else:
            row_ids[rid] = lineno
        if status is None:
            violations.append(
                "V5 linha %d: row do Status Rápido sem emoji de status: %s"
                % (lineno, rid)
            )

    sec_ids = {}
    row_status = {rid: st for _, rid, st in rows}
    for lineno, sid, status, heading in sections:
        label = sid if sid else heading[:60]
        if status is None:
            violations.append(
                "V2 linha %d: seção ### sem emoji de status: %s" % (lineno, label)
            )
        elif status == EMOJI_DONE:
            violations.append(
                "V1 linha %d: seção ### com status ✅ no ativo (deveria estar no "
                "archive): %s" % (lineno, label)
            )
        if sid is None:
            violations.append(
                "V3 linha %d: seção ### sem ID reconhecível: %s"
                % (lineno, heading[:60])
            )
            continue
        if sid in sec_ids:
            violations.append(
                "V6 linha %d: ID de seção duplicado: %s (1ª na linha %d)"
                % (lineno, sid, sec_ids[sid])
            )
        else:
            sec_ids[sid] = lineno
        if sid not in row_status:
            violations.append(
                "V3 linha %d: seção %s não tem row no Status Rápido" % (lineno, sid)
            )
        elif status is not None and row_status[sid] is not None \
                and status != row_status[sid]:
            warnings.append(
                "AVISO linha %d: emoji da seção %s (%s) difere do Status Rápido (%s)"
                % (lineno, sid, STATUS_NAME[status], STATUS_NAME[row_status[sid]])
            )

    for lineno, rid, status in rows:
        if status in (EMOJI_TODO, EMOJI_WARN) and rid not in sec_ids:
            violations.append(
                "V4 linha %d: row %s do Status Rápido (%s) sem seção detalhada "
                "no ativo" % (lineno, rid, STATUS_NAME[status])
            )

    return rows, sections, violations, warnings


def main(argv):
    if len(argv) > 1:
        path = argv[1]
    else:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(repo_root, "improvements.md")

    if not os.path.isfile(path):
        print("backlog_audit: arquivo não encontrado: %s" % path)
        return 2

    rows, sections, violations, warnings = audit(path)

    print("backlog_audit: %s" % path)
    print("  rows no Status Rápido: %d | seções ###: %d" % (len(rows), len(sections)))

    for w in warnings:
        print("  " + w)

    if violations:
        print("  FALHOU — %d violação(ões):" % len(violations))
        for v in violations:
            print("    " + v)
        return 1

    print("  OK — invariante estrutural íntegro (0 violações, %d aviso(s))."
          % len(warnings))
    return 0


if __name__ == "__main__":
    try:  # console Windows redirecionado pode estar em cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main(sys.argv))
