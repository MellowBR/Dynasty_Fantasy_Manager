# Handoff — Sessão OFF26-2-F1 (16/06/2026 pt9)

## Natureza

**Diagnose read-only** (MAN-OFF26-2-F1) da keeper sheet exportável, sobre o OFF26-1 F2
recém-commitado (`2c243d4`), roster e a porta de budget. **Zero mutação** de código/DB/
schema/endpoint. Achados absorvidos em `improvements.md` (seção OFF26-2 → subseção F1), não
só aqui (MAN-METH-REG).

## Terreno verificado (com evidência)

- **Snapshot revelado:** `CutWindowAudit` (models.py:854); `declarations` =
  `[{team_id, team_name, cut_ids, cut_names, num_cuts, declared}]`. **CONGELA SÓ A DECISÃO
  DE CORTE — não salário, não budget.** Acesso: `filter_by(season, is_canonical=True)` /
  `GET /api/cuts/audit`. **Season = `get_current_season()` direto** (pós-rollover; não +1).
- **Keepers = roster live (`filter_by(team_id, is_dropped=False)`) − `cut_ids` do snapshot**,
  chave `Player.id`. Fonte MISTA (roster live + cuts frozen) → coerente só com roster estável
  pós-lock.
- **Salário canônico = `p.salary`** (valorizado pós-rollover). A janela usou budget
  **não-projetado** (D9); a sheet usa o **mesmo `p.salary`**, nunca `project_next_salary`.
- **Budget de FA:** consumir `POST /api/cap_projector/<team>/budget` com **`projected:false`**
  + `kept_ids = roster − cuts` (a mesma chamada da janela). Nunca recalcular.
- **Gate de existência:** snapshot canônico presente (`_window_locked` / `revealed:true`).
- **Export precedente:** NÃO há CSV/print/clipboard-de-dados; existe JSON por time + tabelas
  Jinja server-side + 1 clipboard (link de trade). `pandas`+`openpyxl` disponíveis.

## Réplica

Fonte única confirmada: budget = `draft_budget` (via porta); salário = `p.salary`. Nenhuma 2ª
derivação. A sheet **consome**, não recalcula.

## Refutação de premissas (resumo)

- *falsa*: "snapshot congela salário/budget" → congela só cortes; sheet deriva live.
- *deslocamento*: "keeper = roster − cortes" → fonte mista (roster live + cuts frozen).
- *correta*: budget não-projetado bate com o lock (D9).
- *perda*: snapshot tem `declared` (proveniência) — proposta silente.
- *deslocamento*: keepers incluem IR (conta no budget, D11) — decidir se sinaliza.

## Decisões de produto NÃO arbitradas (p/ o owner)

1. Formato de export: página imprimível vs. CSV vs. clipboard TSV.
2. Por-time individual vs. **consolidada** (12 times — Cowork monta a liga toda; OFF26-4 quer
   todos).
3. Qual número é o "budget de FA": `usable_draft_budget` (reserva $1/slot) vs. `raw_budget`.
4. Sheet inclui slots vazios / 8.3.4 / flag IR / status `declared`?

## Gaps que a F2 fecha (curto)

Keepers = roster live − `cut_ids` do snapshot (documentar premissa de estabilidade); salário
= `p.salary`; budget consumido em `projected:false` (nunca recalcular); gate por snapshot
canônico; escolher formato de export; surfacing de `declared`/IR/qual budget; por-time vs.
consolidada.

## Estado

- Read-only confirmado: nenhum arquivo de código tocado. Só docs: `improvements.md` (subseção
  F1 em OFF26-2) + este handoff. `salary_engine_test` não precisou rodar (sem toque em lógica).
- Sem push. Commit docs-only deste ciclo F1 quando o owner quiser.
