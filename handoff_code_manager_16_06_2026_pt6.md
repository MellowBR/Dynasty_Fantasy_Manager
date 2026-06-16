# Handoff — Sessão OFF26-1-F1 (16/06/2026 pt6)

## Natureza

**Diagnose read-only** (MAN-OFF26-1-F1) da janela de keepers/cuts selada. Zero mutação de
código/DB/schema. Achados absorvidos em `improvements.md` (seção OFF26-1 → subseção F1),
**não só neste handoff** (regra MAN-METH-REG). `salary_engine_test` rodado só como sanity
(48/48), nada alterado.

## Terreno verificado (com evidência de código)

- **Budget canônico = fonte única pós-F10:** `salary_engine.draft_budget` (salary_engine.py:216-236);
  porta `POST /api/cap_projector/<team>/budget` (salary.py:114-179, `@login_required`),
  body `{kept_ids:[Player.id], rookie_sids:[sid]}`. Cobre keep-subconjunto + já calcula 8.3.4
  (`insufficient_budget`). Réplica JS removida (DP2 matou `/simulate`); cliente só exibe.
- **M8/LotteryAudit (models.py:785-819) é molde** da peça snapshot+canônica+replace:
  transfere `is_canonical`/`previous_audit_id`/`reason`/`result_hash`/`executed_*`/blob JSON;
  NÃO transfere `random_seed`/`weights_json`/`pool_json`. As declarações editáveis pré-lock
  são storage SEPARADO que congela no snapshot no lock.
- **Identidade:** chave de declaração = `Player.id` (o que `kept_ids` já usa). Roster =
  `filter_by(team_id, is_dropped=False)`.
- **Autorização:** `@login_required`/`@admin_required` (auth.py:101-112), `User.team_id`+
  `team_rel`, `inject_user_team` (app.py:115-121).
- **Offseason:** passo 6 "Definir Keepers / Cortes" é placeholder (`_get_step_statuses`,
  `"done": False` hardcoded, sem flag/backing) — slot da janela. `offseason_step` nunca escrito.

## Gaps críticos revelados (a F2 fecha)

1. **Sigilo-mesmo-de-admin é 100% NOVO e contradiz o modelo aberto atual** — hoje qualquer
   logado lê o roster de qualquer time; nenhum escopo por-owner existe. Sigilo recai sobre a
   **declaração**, não o roster (já público).
2. **Base do budget × timing do rollover:** a porta projeta via `project_next_salary`
   (contract_year+1). Passo 6 é **pós-rollover** (passo 4 já incrementou contract_year +
   valorizou salary) → consumir como está **projeta 2× (duplo)**. Arbitrar base.
3. **IR/K-DEF:** `active_salary()` exclui IR (models.py:96-100); `draft_budget` conta IR e
   K/DEF (salary_engine.py:218). Barra de cap × budget da janela divergiriam.
4. **8.3.4 é soft** (só alerta, nunca trava) — janela travar = enforcement novo.
5. Storage editável/privado por-owner (≠ snapshot do lock); endpoint só-contagem "8/12" sem
   vazar conteúdo; backing do passo 6 (flag + status); caminho admin "supre time ausente"
   com exceção à regra cega.

## Decisões de produto NÃO arbitradas (para o owner, antes da F2)

1. Janela roda **pré** ou **pós** rollover? (define a base do budget — corrente vs. projetado)
2. 8.3.4 **trava** a declaração inválida ou só **alerta**?
3. IR conta no budget de keeper? K/DEF conta?
4. `needs_review` (jogador Sleeper-sync) é elegível como keeper?
5. A porta de budget precisa de escopo por-owner, ou aceita-se por o roster já ser público?

## Estado

- Read-only confirmado: **zero escrita** em DB/schema/endpoint; nenhum arquivo de código
  tocado. Só docs: `improvements.md` (subseção F1 em OFF26-1) + este handoff.
- Sem push. Exceção de commit docs-only (agrupar com pt5 + edição OFF26-8 se ainda não
  commitados — pt5/OFF26-8 já commitados em `6b73141`; este ciclo F1 é commit docs-only novo).
- `salary_engine_test`: 48/48 (sanity, nada alterado).
