# Handoff — Code Manager — 12/06/2026 (pt2: sessão F10)

> Ponte temporária entre sessões. **Fonte de verdade = `manager_devplan.md`** (log) +
> `improvements.md`/`improvements_archive.md` (backlog). Este handoff é descartável após leitura.
> Substitui o `handoff_code_manager_12_06_2026.md` (sessão F11, mesma data).

## Resumo da sessão

Sessão **F10** (Fable 5) com 3 tarefas de abertura. **F11 fechado ✅** (smoke prod OK, seção no
archive), **F11-FIX-UX** registrado e aplicado (⚠️), **F9** com corroboração viva, **F10 ⚠️
localhost** (réplica JS de `draft_budget` eliminada). Commit único código+docs; push com o owner.

## O que foi feito

- **F11 ✅** — smoke de prod passou (273 jogadores no preview, 0 renovações, cap $2187→$2310;
  Step 4 do offseason bloqueado por gate). Status Rápido flipado; seção migrada **verbatim** para
  `improvements_archive.md` (script com asserts, regra O3).
- **F11-FIX-UX ⚠️** (sub-item novo, carona) — microcopy de owner nos 2 cards do /admin: card
  "Season Rollover (preview)" com o texto aprovado (prévia × aplicação real na etapa Season
  Rollover da página de **Intertemporada**, link /offseason, condições de liberação) + passo 2 do
  "Ordem do Fluxo Pré-Temporada" na mesma terminologia (sem nº de step, sem season hardcoded).
- **F9** — adicionada corroboração da forense F11: `salary_history` = 0 **no disco vivo**
  (12/06; a F1B auditara cópia de 07/06) → nenhuma aquisição jamais passou por
  `record_acquisition` em prod. Urgência elevada: **fechar F9 antes da FA auction 2026**.
- **F10 ⚠️ localhost** — premissa "basta consumir o payload atual" **refutada** (GET calcula
  sobre salário atual do roster inteiro; summary precisa do subconjunto keep/corte com
  `next_salary`). Novo `POST /api/cap_projector/<team>/budget` (kept_ids → `draft_budget`
  canônico sobre `project_next_salary` dos mantidos + `cap_pct`/`shortfall` de display).
  `updateSummary` virou POST+display: consts `SALARY_CAP`/`MAX_ROSTER` deletadas, zero agregação
  de cap em JS, guard de sequência, mensagens com `b.salary_cap`. Endpoint DP1 **intocado**.
- **Grep de réplicas: zero novas → zero itens novos.** Literais "$200" de display
  (base.html/trades.html) = decisão consciente documentada na seção F10; agregações server-side
  de "cap usado" ≠ regra de budget; draft_import.py já consome o canônico.

## Validação

Test client (não-admin temporário, removido após): payload × canônico **idêntico** em 4 cenários
de keep/corte; paridade com o summary antigo; 404 p/ time inexistente; regressão DP1 (cenário
vazio == budget atual; **2 picks +$58** reproduzido com store re-semeado e limpo: $46→$55,
$3→$3); **nada escrito**. Greps: zero aritmética de budget no template. Jinja parse OK
(cap_projector + admin). `salary_engine_test.py` **48/48**.

## Estado dos bancos

Prod: intocado. Local: intocado ao final (usuário e rookies temporários de teste criados e
removidos na própria validação; boot do app re-rodou `run_import` como sempre — classe F12).

## Próximos passos

1. **Push + deploy + smoke F10/F11-FIX-UX** (owner): /cap_projector — summary com valores
   corretos, toggles keep/corte atualizando, board DP1 funcionando; /admin — 2 cards com a
   microcopy nova e link Intertemporada. Aí **F10 e F11-FIX-UX ⚠️ → ✅** (F10: migrar seção p/
   archive no fechamento).
2. **DOC1 + F12 (Opus)** — sessão própria. A evidência "salary_history=0 vivo" desta sessão soma
   ao F12.
3. **F9 (urgência elevada)** — **antes da FA auction 2026** (F2 = rotear `bulk_register` por
   `record_acquisition` + remover hack `_noop`; sem backfill, veredito F1B).
4. **E4-d (Opus)** — antes da FA auction.
5. **M19 (Opus)** — carona futura. **M20** — bloqueado até M17 ✅.
6. **OFF26-1** — desbloqueado pelo F10 para nascer consumindo o canônico (era a dependência).

## Pendências de owner

- Push (gatilho de deploy) + smoke do item 1.
- **Re-upload no Project Knowledge:** `improvements.md`, `improvements_archive.md`,
  `manager_devplan.md`.
- Arquivos não-commitados pré-existentes (não desta sessão): `.sleeper_players_cache.json`,
  `AGENTS.md`, handoffs antigos — decisão de commit/descarte com o owner.
