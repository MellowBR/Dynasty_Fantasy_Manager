# Handoff — Sessão OFF26-2 F2 / implementação (16/06/2026 pt11)

## Natureza

**Implementação** (MAN-OFF26-2) da keeper sheet consolidada, sobre a Spec final (REFINE) e o
terreno (F1). **Leitora — não muta nada.** Item marcado **⚠️** — e2e localhost verde, aguarda
smoke prod (como o OFF26-1, depende de janela revelada numa season real pós-rollover).

## O que foi construído (tudo em routes/cuts.py + 1 template novo)

- **`_build_keeper_sheet(season)`** — `keepers = roster_live (is_dropped=False) − cut_ids` do
  snapshot canônico (`CutWindowAudit`, season = `get_current_season()`); salário = `p.salary`
  (não re-derivar); budget de FA = `usable_draft_budget` via o **único** `draft_budget` com
  base corrente (= `projected:false` da porta; precedente `draft_import.py`, **sem aritmética
  nova**). Status `declared` (default-zero / owner / admin-supplied).
- Rotas: `GET /cuts/keeper_sheet` (página), `GET /api/cuts/keeper_sheet` (JSON),
  `GET /api/cuts/keeper_sheet.csv` (download — `csv` stdlib + `Content-Disposition`).
- `templates/keeper_sheet.html` (novo) — tabela 12 times + aviso de fonte mista com
  **timestamp do lock** (D2) + CSV + pré-condição (D9). Links em `cuts.html` e `offseason.html`.

## Verificação (e2e localhost 20/20 + salary_engine 48/48)

- keepers = roster − cortes; Bravo default-zero mantém todos; Charlie admin-supplied. ✅
- `fa_budget` (sheet) == `usable_draft_budget` da porta `projected:false` (130==130; usa
  `p.salary`, não `raw_budget`). ✅
- Paridade tabela × CSV (linhas == total keepers; CSV carrega budget+status). ✅
- Sem snapshot → página 200 comunica pré-condição; JSON `revealed:false`. ✅
- Sem mutação de Player ao gerar sheet/CSV. ✅
- Réplica: grep confirma zero aritmética de cap (só `draft_budget(...)["usable_draft_budget"]`).
  Invariante F10 mantida. ✅

## Cadeia (lembrar)

- **OFF26-4** compara a config real da liga fantasma **contra esta sheet** → consumir
  `/api/cuts/keeper_sheet` (JSON) como base de diff.
- **OFF26-7** (dry run E2E): revelação OFF26-1 → keeper sheet (CSV) → Cowork transcreve →
  OFF26-4 audita. Sheet pressupõe snapshot revelado (E4-a + rollover + janela locked antes).

## A registrar (já feito)

- improvements.md: Status Rápido OFF26-2 → ⚠️; seção ganhou subseção **F2** (arquivos,
  validações, cadeia OFF26-4/7).

## Estado

- Código tocado: `routes/cuts.py`, `templates/keeper_sheet.html` (novo), `templates/cuts.html`,
  `templates/offseason.html`. Docs: `improvements.md` + este handoff. Script e2e removido.
- Sem push. Commit (código+docs) pode agrupar com F1/REFINE pendentes (pt9, pt10).
- **Smoke prod pendente** (vira ✅): janela revelada real → abrir `/cuts/keeper_sheet` →
  conferir por time → baixar CSV → validar paridade.
