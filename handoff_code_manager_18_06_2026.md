# Handoff — Sessão MAN-OFF26-4-F1 (18/06/2026)

## Natureza

Diagnose **read-only** (MAN-OFF26-4-F1) — terreno da futura auditoria de keepers
pré-leilão (OFF26-4). Nenhum código alterado, nenhuma escrita no banco/Sleeper, nenhuma
mudança de schema. OFF26-4 permanece **🔲**. Só docs: achados na seção OFF26-4 de
`improvements.md` + log no `manager_devplan.md` + este handoff. Modelo: Opus (Fable
indisponível desde 13/06 — política vigente Opus para tudo).

## Pergunta

Mapear, contra o código atual, o terreno para a auditoria comparar a keeper sheet
(OFF26-2) com a config real da liga **fantasma** (sala separada, permanente) lida via
Sleeper API read-only — antes de o leilão começar.

## Vereditos centrais (com evidência)

1. **League ID = constante hard-coded** (`models.py:15 LEAGUE_ID`); `sync_sleeper.run_sync`
   usa em todas as chamadas. Assume uma só liga. **Precedente para ler outra:**
   `draft_import.py` (OFF26-3) recebe `draft_id` do admin e deriva
   `league_id = draft.get("league_id")` via `ss._get` (URL arbitrária, `sync_sleeper.py:35`).
   Caminho limpo = parâmetro/AppConfig novo, não constante. → **decisão de produto**.

2. **GAP MAIOR — pré-draft não é lido.** Todo consumo de `/draft/{id}/picks` exige
   `status=="complete"` (`draft_import.py:94`; `_classify_draft` `sync_sleeper.py:733`).
   As designações de keeper de board (SET KEEPERS, OFF26-6) **não são lidas em lugar
   nenhum**. O que a API expõe pré-draft (is_keeper / amount antes de complete?) é
   **empírico → probe na F2**, não assertável do código. **Bloqueador.**

3. **Ponte de owner ✅** — `Team.sleeper_owner_id` populado todo sync
   (`sync_sleeper.py:157,167`); casamento já existe em `_team_by_roster`
   (`draft_import.py:48`). **Ressalva:** `Team.name` ainda é mutado pelo sync e
   exibido/ordenado na sheet (`cuts.py:405`) — casar **só por owner_id**, nunca por nome.

4. **Ponte de jogador — NÃO.** `/api/cuts/keeper_sheet` emite só `{id local, name,
   position, salary}` (`cuts.py:420-423`); grep confirma `sleeper_player_id` ausente em
   `routes/cuts.py`. Resolução via `Player.sleeper_player_id` /
   `player_lookup.find_player_by_sleeper_id` (Brown-safe). → incluir na sheet ou re-query.

5. **Budget — auditoria CALCULA ambos os lados ✅.** Lado Manager pronto na sheet
   (`fa_budget`, `cuts.py:418` → `draft_budget(...)["usable_draft_budget"]`).
   **REFUTAÇÃO:** `fa_budget` = `usable_draft_budget` (`$200 − Σ keepers − $1/slot vazio`,
   `salary_engine.py:221-224`) ≠ budget de auction do Sleeper (`raw_budget` = `$200 −
   Σ keepers`). Comparar Σ salários de keeper ou `raw_budget`, **não** `fa_budget`.
   → **decisão de produto**.

6. **Réplica:** `salary_engine.draft_budget` é porta única (`cuts.py:392`,
   `draft_import.py:77`, `salary.py:186`); sem réplica client-side (`keeper_sheet.html` só
   renderiza server-side). Diff Manager×Sleeper é greenfield. Recomendo **extrair
   `_team_by_roster`** (hoje em `draft_import.py`) para helper compartilhado em vez de
   recriar.

## Premissas refutadas (resumo)

- "Manager conhece o league ID" → verdade, mas constante única, não config (gap design).
- "ler config = ler roster" → falso; pré-draft não é lido (perda não-intencional, gap maior).
- sheet sem `sleeper_player_id` (perda não-intencional, corrigível).
- `fa_budget` ≠ budget de auction Sleeper (deslocamento — escolher base de comparação).
- `Team.name` mutável exibido na sheet (robustez — casar por owner_id).

## Próxima fase

**Opus, modo REFINE** — 2 decisões de produto (parametrização do league/draft id;
base de comparação do budget) + 1 probe empírico bloqueador (o que a API expõe pré-draft).

## Arquivos tocados (docs-only)

- `improvements.md` — bloco "Diagnose F1" na entrada OFF26-4 (status 🔲 intocado).
- `manager_devplan.md` — entrada de log MAN-OFF26-4-F1 + linha "Última atualização".
- `handoff_code_manager_18_06_2026.md` — este arquivo.
