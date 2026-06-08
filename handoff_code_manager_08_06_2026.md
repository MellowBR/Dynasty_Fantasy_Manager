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

**M18 — Timestamps no fuso do usuário** (~11 sites) — ⚠️ localhost, pendente smoke em prod (cliente BRT)
- **Causa-raiz (F1):** naive UTC armazenado, ~10 sites formatando inline, **sem fonte central**; servidor mandava
  string pré-formatada → fuso destruído antes do browser. 1 ponto client-side tentava converter mas estava
  bugado (ISO naive sem `Z` → `new Date` lia como local).
- **Fix (F2) — fonte única (1 por modo de render):** `timeutil.utc_iso(dt)` (naive-UTC → ISO `Z`) usado por
  `to_dict`/rotas + filtro Jinja → macro `local_dt` (emite `<time class="js-localtime" datetime="…Z">`);
  **formatação humana só no cliente** via `formatLocalDT(iso,fmt)` (`base.html`), aplicada por `applyLocalTimes()`
  no load e chamada direto pelo JS dinâmico.
- **Sites:** card/rodapé de sync, snapshot F8 (`utcfromtimestamp`), ESPN import, banner ESPN do cap projector,
  lottery audit, lista de trades, modal de trade, proposta create/expired, **link de proposta (antes bugado)**.
- **Armazenamento intacto** (`utcnow` naive, sem migração). **Campos mortos preservados** (salary history +
  `AuctionLog.created_at`) — amarração com WV1.
- **Validação localhost:** `00:25 naive`→`2026-06-08T00:25:00Z`; `<time …Z>` no admin/rodapé; banco mantém UTC;
  páginas 200; `/api/trades/by_tx`→ISO `Z`. Tests 48/48.
- **Próximo:** smoke em prod com cliente BRT (00:25 UTC → 21:25 do dia anterior) → ✅.

## Desbloqueado
- **DP1** (board de planejamento de cap pré-draft) — o store do E2 existe → **F1/F2 podem seguir**
  (o board é justamente pré-draft).

## Backlog 🔲 (próxima sessão)
| Item | Nota |
|------|------|
| **DP1** | Board pré-draft (rookies: `espn_ref_value` + salário projetado + simulação de cap; projeção≠contrato). Desbloqueado. Prioridade a definir |
| **E2 (fechar ✅)** | Após validar o store em prod (import) e a aplicação no rookie draft real (~ago) |
| **E2-risk (approximate-confirm)** | Risco residual acima — fix do fuzzy oferecendo rookie como match de veterano. Candidato a item |
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
