# Handoff — Code Manager — 12/06/2026

> Ponte temporária entre sessões. **Fonte de verdade = `manager_devplan.md`** (log) +
> `improvements.md`/`improvements_archive.md` (backlog). Este handoff é descartável após leitura.

## Resumo da sessão

Sessão **F11** (Fable 5, conforme política de modelos): verificação retroativa em prod (Etapa 1,
read-only) + fix Opção A (Etapa 2). Um item movido 🔲 → ⚠️ localhost. Commit único código+docs.

## O que foi feito

- **F11 Etapa 1 ✅ — prod LIMPO.** Queries forenses read-only executadas pelo owner no Render Shell
  contra `/data/dynasty.db`. Números: `salary_history` = **0 linhas** (nenhum rollover jamais aplicado
  na história da liga — contratos vivos vieram do CSV bootstrap, classe F12); 0 lotes, 0 duplicatas;
  **0 assinaturas `"Season rollover"` no `sync_log`** (marcador exclusivo do caminho admin — nunca
  usado); 0 contract_year fora de 1..4; config consistente (`current_season=2025`,
  `rollover_done=false`, `season_locked=true`). **Sem corrupção → repair desnecessário**, item de
  repair NÃO aberto. A janela de risco estava aberta (1º rollover iminente nesta offseason).
- **Grep por 3º caminho (pré-fix, obrigatório):** confirmados **só os 2 catalogados** pela AUD1
  (admin + offseason). Escritas de `SalaryHistory(`: models.py:396 (record_acquisition) + os 2
  rollovers; nada em templates/JS além de admin.html:285 e offseason.html:724.
- **F11 Etapa 2 ⚠️ localhost — Opção A aplicada.** Removidos: `POST /api/admin/rollover/apply`
  (routes/admin.py, substituído por comentário-guard), botão "⚡ Aplicar Rollover" +
  `confirmRollover()` + `#rollover-result` (templates/admin.html), comentário stale "CURRENT_SEASON
  is a constant" (estava dentro do endpoint removido). **Preview mantido** (read-only, função pura,
  independente do caminho removido); card virou "Season Rollover (preview)" com link para
  `/offseason`. **Offseason 100% intocado.**
- **Validação:** grep pós-fix = exatamente **1 caminho de escrita** de rollover
  (offseason.py:675-683); 0 referências órfãs; py_compile + Jinja parse OK;
  `salary_engine_test.py` **48/48**.

## Estado dos bancos

Prod (`/data/dynasty.db`): **intocado** (Etapa 1 foi 100% read-only, sem backup necessário).
Local: intocado pela sessão (queries read-only de validação de sintaxe contra o seed).

## Próximos passos

1. **Smoke F11 em prod** (owner): deploy → `/admin` sem o botão Aplicar, preview funcional →
   `/offseason` Step 4 com gates intactos. Aí **F11 ⚠️ → ✅** + migrar a seção pro archive (regra O3).
2. **F10 (Fable)** — ficou de fora desta sessão para manter o commit F11 atômico; janela Fable
   até 22/06.
3. **DOC1 + F12 (Opus)** — sessão Opus própria. Nota: o achado "salary_history vazio em prod"
   desta sessão é evidência adicional para o F12 (CSV bootstrap não gera history).
4. **E4-d (Opus)** — antes da FA auction.
5. **M19 (Opus)** — carona em sessão Opus futura.
6. **M20 (Opus)** — bloqueado até M17 ✅ (smoke prod com import ESPN real).

## Pendências de owner

- **Smoke F11 em prod** (item 1 acima) — destrava o ✅.
- **Re-upload no Project Knowledge (Claude.ai):** `improvements.md` e `manager_devplan.md`
  (alterados nesta sessão).
- Arquivos não-commitados pré-existentes (não desta sessão): `.sleeper_players_cache.json`,
  `AGENTS.md`, handoffs antigos — decisão de commit/descarte fica com o owner.
