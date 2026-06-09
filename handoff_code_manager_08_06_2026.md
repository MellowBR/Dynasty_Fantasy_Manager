# Handoff — Fantasy Manager — 08/06/2026

Estado pós-trabalho de 05–08/06. **git = local = project knowledge** (tudo commitado e pushado em `main`).
Este handoff é o input de início da próxima sessão; o `improvements.md` (Status Rápido + seções) e o
`manager_devplan.md` (Log de Decisões) têm o detalhe completo.

## Concluído ✅
| Item | Resumo |
|------|--------|
| **M15** | Lottery 6 seeds (7º com 1 bolinha, pool 96), fonte única `DEFAULT_LOTTERY_WEIGHTS`, retrocompat por `len(pool_json)` |
| **M15-FIX** | Editor de pesos reativo (render single-source JS) + legenda `/picks` audit-first |
| **M16** | Lottery só define R1; R2/R3 = standings invertido (corrige ordem + valores dynasty) |
| **OFF26-3** | Importador de drafts de liga fantasma (rookie linear / FA auction) + **helper canônico `record_acquisition`** (única porta de criação de contrato; `/auction` refatorado, exceto `bulk_register`=F9) |
| **E1** | Import ESPN robusto end-to-end — **validado em produção** (upload → review 300, sem 500). Upload manual + degradação graciosa + estado de review em FS gravável + parser 299→300 + `pdfminer.six` no requirements (E1-FIX) |
| **M18** | Timestamps no fuso do usuário — **validado em produção** (sync 11:47 BRT → "11:47", não 14:47 UTC). Fonte única `timeutil.utc_iso` (ISO `Z`) + macro `local_dt` + JS `formatLocalDT`; ~11 sites; armazenamento UTC mantido |
| **E4-b** | Saneamento de `sleeper_id` — **executado e verificado em produção** (rota admin "🧹 Limpar Órfãos Duplicados": 2 órfãos-duplicata removidos, 278 players, 0 sid nulo, canônicos intactos; backup `dynasty_prod_backup_2026-06-09_pre-E4b.db`). Guard (dedup-por-sid + `needs_review` no import_csv) fecha a causa-raiz. Seed ainda tem os 2 (latente) |

## Em andamento ⚠️
**E2 — store de valores ESPN de rookie** (`rookie_espn_value`, keyed por `sleeper_id`)
- **Implementado e validado (12/12, localhost):** população no confirm do import (resolve not_found
  **+ approximate-skipped** → `sleeper_id` via pool global do Sleeper, nome+team, Brown-safe);
  consumo no OFF26-3 (rookie criado → `floor(ESPN×1.2)` via `year1_salary`); limpeza pós-draft.
- **Por que ⚠️ e não ✅:** o **store é validável em prod já** (rodar um import → conferir o store),
  mas a **aplicação no draft** só tem e2e no **rookie draft real (~agosto, regras 8.2.7/8.2.2)**.
  Regra "✅ só após prod".
- **Escopo cheio foi possível** porque o OFF26-3 já estava ✅ (criação de rookie idempotente por `sleeper_id`).

### Achado do E2-F2 + RISCO RESIDUAL CONHECIDO (registrar)
- **Achado:** rookies podem cair em **`approximate`** por falso-positivo de fuzzy — ex.: **"Carnell Tate"
  ~ "Darnell Mooney" (sim 0.665)**. **Mitigação aplicada:** o store captura também o approximate-skipped
  (13 rookies de valor vs 9 só de not_found).
- **⚠️ RISCO RESIDUAL (classe do incidente "Brown"):** se o admin **CONFIRMAR** um desses matches falsos
  no review, o valor ESPN do rookie **contamina o `espn_ref_value` de um veterano real** (ex.: Mooney
  receberia o valor do Carnell Tate). A mitigação só cobre o caso *skip*, não o *confirm errado*.
- **Fix limpo (próxima sessão):** não oferecer como fuzzy-match contra veterano do DB uma entrada que já
  resolve para o `sleeper_id` de um rookie (ou rebaixar/sinalizar esses candidatos no review).
  **Candidato a item próprio** (ver backlog).

**M17 — Personalização por usuário logado** (8 surfaces) — ⚠️ localhost, pendente smoke em prod
- **Causa-raiz (F1):** 8 surfaces assumiam "my team" fixo (`MY_TEAM_NAME`/flag `is_my_team`) → sempre o time
  do admin. **Fix (F2):** context processor `inject_user_team` (`app.py`) vira **fonte única server-side**
  (`g_user_team` = `current_user.team_rel`; `g_user_team_cap` = `active_salary()`). Réplica JS do chip
  (`loadCapChip`) e literal "Cangaceiros da Colina" removidos; chip renderizado server-side.
- **Surfaces:** home default+fallback, chip valor+título, cap projector, tag "EU" (dropdown desktop+mobile),
  `league-card-mine`+EU (League Hub), 🏆 (header roster). Fallback team NULL → estado neutro.
- **Flag `is_my_team` vira só dado** (escrita pelo sync/`record_acquisition`/`/api/teams` — não tocada);
  deixou de ser fonte de "time do usuário". Import morto `MY_TEAM_NAME` removido de `trades.py`/`roster.py`.
- **Validação localhost 8/8** (test_client): Michel(8)→chip `$183/$200`, Erico(5)→Cangaceiros, sem-time→neutro,
  cap projector pré-seleciona certo, cosméticos no time do usuário, sem `teams.find`/`loadCapChip`. Tests 48/48.
- **Próximo:** smoke em prod (login real dos owners) → ✅.

**E2-RISK — Fuzzy oferece rookie como match de veterano (classe "Brown")** — ⚠️ localhost, pendente smoke prod
- **Re-escopo (F1+F1B):** hazard nasce no `match_players` (fuzzy contra roster local); agravante = review **pré-seleciona o veterano** + JS trata valor truthy como resolvido → **confirm sem interação** grava valor do rookie no `espn_ref_value` do veterano. F1B descartou a unificação `espn_ref_value` por `sleeper_id` como fix (é redesenho → virou **[[E4]]**). Owner optou pelo **híbrido**: mínimo de tela agora, matcher no E4.
- **Fix (F2) — só camada de tela:** `espn_review.html` — `<select>` inicia **NEUTRO** (sem pré-select do best_player); o gate existente (`updateStatus`→`btn.disabled`) já bloqueia confirm até toda approximate ter escolha explícita. Não toca matcher/engine/ESPNValue/schema.
- **Validação localhost:** sem pré-select; confirm sem ação não altera veterano (32.4→32.4); resolução explícita grava (32.4→48.0). Tests 48/48.
- **Próximo:** smoke em prod com import ESPN real → ✅.

**E4-a — Matcher do import ESPN resolve por `sleeper_id` (raiz do "Brown")** — ⚠️ localhost, pendente smoke prod
- **Raiz que o F2 do E2-RISK só paliou na tela.** `match_players` ganhou `sid_resolver` injetável: identidade por
  **sleeper_id** contra o pool global (Brown-safe nome+team, reusa `_build_pool_index`/`_resolve_entry_sid` —
  extraídos do `_resolve_not_found_to_store` do E2). sid→Player = matched por id; sid→não-rosterado = not_found
  (store, **nunca match de vet**); sem sid limpo = igualdade exata ou review. Sem auto-match por similaridade no
  modo resolver; modo legado preservado.
- **Não toca** `salary_engine`/schema/armazenamento (escrita segue `Player.espn_ref_value` via id; store canônico
  é E4-c). Reversível.
- **Validação localhost (pool real):** Tate→not_found (sid 13279), Mooney intacto; vet→matched por id; typo→review;
  sobrenome isolado não resolve; idempotente; confirm grava 60.0. Tests 48/48.
- **Próximo:** smoke prod com import real → ✅. Em seguida E4-b (saneamento dos 2 sleeper_id nulos).

**E4-c-1 — Fundação do store canônico de valor ESPN** — ⚠️ localhost; **backfill PROD pendente (boot pós-deploy)**
- **Aditivo/reversível** (o destrutivo é E4-c-2). Tabela `espn_value_store (sleeper_id,season)[raw,adjusted,is_final]`
  via `db.create_all()`; backfill da coluna por **Migration 7** (season 2026 prelim, idempotente); **helper único
  `set_espn_value`** (store + materializa coluna) nos 8 escritores; badge PROV repontada ao store. Engine intocada
  (lê a coluna; nunca lookup). `ESPNValue`/`RookieEspnValue` intactos.
- **Validação localhost 10/10:** backfill 248 == value-bearing c/ sid; store==coluna (Marquise Brown 60); DST `'IND'`
  ok; badge lê do store; idempotente; páginas 200. Tests 48/48.
- **⚠️ PASSO PROD:** backup `/data` antes do deploy → push → boot roda Migration 7 (log `backfilled N rows`) →
  conferir `SELECT COUNT(*) FROM espn_value_store` ≈ 248 + spot-check. **E4-c-1 → ✅ só após isso.**
- **Próximo:** DP1 (lê o store) perto do draft; E4-c-2 (DROP ESPNValue + generalizar RookieEspnValue) quando convier.

## Desbloqueado
- **DP1** (board de planejamento de cap pré-draft) — **store canônico chega no E4-c-1** → F1/F2 do DP1 seguem
  após o backfill em prod (lê o store por `(sleeper_id, season)`).

## Backlog 🔲 (próxima sessão)
| Item | Nota |
|------|------|
| **DP1** | Board pré-draft (rookies: `espn_ref_value` + salário projetado + simulação de cap; projeção≠contrato). **Bloqueado por E4-c-1** (lê o store canônico). Prioridade a definir |
| **E2 (fechar ✅)** | Após validar o store em prod (import) e a aplicação no rookie draft real (~ago) |
| **E4-c-1** | ⚠️ implementado (localhost 10/10); **pendente backfill no boot de PROD** — ver "Em andamento" acima |
| **E4-c-2** | Limpeza (destrutivo/isolado): DROP ESPNValue + generalizar RookieEspnValue. Higiene após E4-c-1; não bloqueia DP1 |
| **E4** (guarda-chuva) | E4-a (⚠️ smoke) / E4-b (✅ prod) / E4-c → sub-fatiado em E4-c-1 (agora) + E4-c-2 (higiene). F1 design + F1 migração concluídas |
| **OFF26-1 / -2 / -4 / -5** | Pacote offseason: janela selada de keepers/cuts → keeper sheet → auditoria pré-leilão → runbook Cowork |
| **F9-F2** | Consolidar `bulk_register` no `record_acquisition` (F9-F1/F1B: 0 dano em prod → refatoração apenas) |
| **F10** | `draft_budget` replicado em JS no cap_projector → cliente consome endpoint canônico (idealmente antes do OFF26-1) |
| **WV1** | Salário de aquisição via waiver sem drop tratado como FA (waiver de jogador nunca dropado → regra de FA); toca `record_acquisition` + histórico. REG feito, F1 pendente |
| **F9-F1B obs (3)** | (a) `salary_history` legada/morta (lida por ninguém; `/salary_history` usa PlayerHistory); (b) aquisições feitas pelo Manager **não emitem PlayerHistory** (só sync/F8a forma a história) — relevante p/ OFF26-3; (c) **seed ≠ produção / sem backup automatizado** |

## Nota de produção / backup
- **Seed (git) ≠ produção (disco persistente do Render).** O `dynasty.db` versionado é seed (~abril);
  os dados vivos acumulam no disco do Render (`init_data.py` semeia só no 1º deploy, nunca sobrescreve).
- A cópia de prod recebida em 07/06 (`~/Downloads/dynasty_prod.db`) serviu à auditoria do F9-F1B e
  **vale guardar como backup nomeado** (ex.: `dynasty_prod_backup_2026-06-07.db`) — hoje não há rotina de backup.
- Auditoria F9-F1B (contra prod): **0 dano** de `bulk_register` (auction_log vazio → /auction nunca usado em
  prod; história vive em PlayerHistory/F8a). `salary_history` vazia em prod é inócua (legada).

## Deploys da sessão (todos em `main`/Render)
M15 `09f3b0a` · M15-FIX `43636d4` · M16 `51795d9` · docs `c81662d` · OFF26-3 `378b842` · E1 `b36f6a8` ·
E1-FIX `3c1b93f` · docs-sync `15dac5f` · E2-F2 `28217a0`.
