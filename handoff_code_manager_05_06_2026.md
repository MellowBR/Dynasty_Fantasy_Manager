# Handoff — Fantasy Manager — 05/06/2026

Sessão de lottery + abertura do pacote Offseason 2026 (OFF26).

## Concluído nesta data (pushed)
| Commit | Item | Resumo |
|--------|------|--------|
| 09f3b0a | **M15** | Lottery 6 seeds (7º com 1 bolinha, pool 96), fonte única `DEFAULT_LOTTERY_WEIGHTS`, retrocompat por `len(pool_json)` |
| 43636d4 | **M15-FIX** | Editor de pesos reativo (render single-source JS) + legenda `/picks` audit-first |
| 51795d9 | **M16** | Lottery só define R1; R2/R3 = standings invertido (corrige ordem + valores dynasty) |
| c81662d | docs | Sync vision/CLAUDE/improvements com o lottery atual |

## Concluído nesta data (commit OFF26-3 F2 — ver git log)
**OFF26-3 — Importador de drafts de liga fantasma** ✅
- **Helper canônico de aquisição** `models.record_acquisition()` (Player+SalaryHistory+AuctionLog atômico, salário via `year1_salary`). `/auction` (FA/rookie/excel) refatorado para usá-lo. Idempotência por `[ref:...]` em `AuctionLog.notes` (`acquisition_already_recorded()`).
- **Importador** `routes/draft_import.py` (10º blueprint): fluxo único 2 modos (linear→rookie / auction→FA), preview→confirm, match por `sleeper_player_id`, idempotente, cap soft. Página `/draft_import`.
- Validação 12/12 contra drafts reais 2025 (cópia temp; produção intocada).

## Estado do pacote OFF26 (improvements.md)
| ID | Item | Status | Dep. | Próximo |
|----|------|--------|------|---------|
| OFF26-1 | Janela de keepers/cuts selada | 🔲 | — | **candidato a F1** (fundação; destrava 2 e 4). Deve nascer consumindo o budget/salário canônico |
| OFF26-2 | Keeper sheet exportável | 🔲 | OFF26-1 | após OFF26-1 |
| OFF26-3 | Importador de drafts | ✅ 05/06 | — | feito |
| OFF26-4 | Auditoria de keepers pré-leilão | 🔲 | 1, 2 | após 1+2 |
| OFF26-5 | Runbook Cowork (doc) | 🔲 | 2, 4 | doc |

## Itens laterais descobertos (da diagnose OFF26-3-F1)
| ID | Item | Status | Nota |
|----|------|--------|------|
| F9 | `bulk_register` cria jogadores sem SalaryHistory | 🔲 Alta | **exige F1 de avaliação de dano** antes do fix; o helper canônico já existe para consolidá-lo |
| F10 | `draft_budget` replicado em JS no cap_projector | 🔲 Média | cliente deve consumir endpoint canônico; idealmente antes do OFF26-1 |

## Notas para a próxima sessão
- O **helper canônico de aquisição existe** — F9 e OFF26-1 devem consumi-lo (não criar réplica).
- 2025 teve **6 sessões de FA auction** + drafts junk (lances anômalos): o importador é escopado a 1 `draft_id` e o preview permite rejeitar.
- Check pós-deploy do M16: no `/picks` de produção, pick 13 (abre R2) deve ser o 12º colocado.
- `dynasty.db` real nunca foi tocado nas validações (todas em cópia temporária + API read-only).
