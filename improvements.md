# improvements.md — Fantasy Manager

> Backlog vivo de melhorias, bugs e features pendentes.
> Atualizado em: 12/06/2026 (sessão F11: **Etapa 1 verificação retroativa em prod ✅ LIMPO** — 0 rollovers jamais aplicados, salary_history vazio, 0 assinaturas admin no SyncLog; **Etapa 2 fix Opção A ⚠️ localhost** — endpoint apply + botão + JS removidos, preview mantido, offseason Step 4 = porta única)
> Atualizado em: 11/06/2026 (sessão AUD1: REG + **F1 executada ✅** — 6 lentes varridas; 6 itens novos: F11 rollover duplicado, F12 import-overwrite local, E4-d matching /auction, M19 validação lottery client-only, M20 descomissionar flag single-user, DOC1 CLAUDE.md startup; 3ª ocorrência do MAN-METH-REG registrada)
> Atualizado em: 10/06/2026 (sessão DP1: F1 diagnose ✅ + **F2 board + simulação multi-pick no backend ⚠️ localhost** — lê `RookieEspnValue` por season, NÃO o canônico; premissa "DP1 lê o store canônico" corrigida; smoke em prod pendente)
> Atualizado em: 09/06/2026 (sessão 08–09/06: M17 + M18 ✅ prod; E2-RISK + E4-a ⚠️ matcher/tela do "Brown"; E4-b ✅ prod (órfãos); E4-c-1 ✅ prod (store canônico ESPN por sleeper_id); WV1/E3/E4-c-2 registrados; DP1 desbloqueado)
> Convenções: 🔲 pendente | ⚠️ parcial | ✅ concluído

---

## Status Rápido

| ID | Item | Prioridade | Status |
|----|------|------------|--------|
| X1 | Acesso multi-usuário (PythonAnywhere + OAuth + permissões) | Alta | ✅ 31/03/2026 |
| X1a | Preparar app para produção (wsgi.py, .env, ProxyFix, python-dotenv) | Alta | ✅ 31/03/2026 |
| X1b | Google OAuth + Flask-Login | Alta | ✅ 31/03/2026 |
| X1c | Tabela `users` no dynasty.db + seed_users.py | Alta | ✅ 31/03/2026 |
| X1d | Decorators `@login_required` / `@admin_required` nas rotas | Alta | ✅ 31/03/2026 |
| S1 | Sync detecta trades do Sleeper e move contratos automaticamente | Alta | ✅ 22/04/2026 |
| T1 | Redesign Trade Manager: simulador multi-owner + link compartilhável | Alta | ✅ 22/04/2026 |
| T2 | Integrar valores dynasty FantasyCalc no preview de trade | Média | ✅ 22/04/2026 |
| Q1 | Script de simulação de temporada (validar salary rollover) | Média | 🔲 |
| M1 | Alerta de cap estourado pós-S1 (preview escalonado + warnings de sync, banner gated por offseason) | Média | ✅ 27/04/2026 |
| M1-FOLLOWUP | Avaliar auto-desativação de offseason mode após FA auction concluído (banner M1 persiste como ruído se admin esquecer de desligar manualmente) | Baixa | 🔲 |
| MAN-S1-FIX | Backfill de previous_league_id reverte estado pós-trades da current league (idempotência cross-season + movimentação cega de Player.team_id em `_sync_trades`) | Alta | ✅ 28/04/2026 |
| M2 | Tela de aprovação em lote de jogadores `needs_review=True` | Média | ✅ 27/04/2026 |
| M3 | Exportar dynasty.db em formato legível para os outros owners | Baixa | 🔲 |
| M4 | Banner de sync desatualizada com timestamp e botão "Sincronizar agora" | Baixa | 🔲 |
| M8 | Auditoria do lottery (seed + página de verificação) + visualização de bolinhas + fluxo em 2 fases | Baixa | ✅ 23/04/2026 |
| M9 | Redesign tela de picks: grid navegável + atalho para trade | Média | ✅ 23/04/2026 |
| M10 | Busca de Jogador: Global + Calculadora (refinado 28/04/2026 — MAN-M10-REFINE) | Média | 🔲 |
| M11 | Teste de auto-containment documental | Média | ✅ 22/04/2026 |
| M12 | Vincular owners a times via tela de admin com lookup do Sleeper | Média | ✅ 22/04/2026 |
| M13 | Página de jogador + "Propor Trade" | Média | ✅ 23/04/2026 |
| M14 | /trades aceitar query params team_a/team_b (pré-requisito M9 + M13) | Média | ✅ 23/04/2026 |
| M15 | Lottery com 6 seeds (inclusão do 7º colocado com 1 bolinha; pool 96) — MAN-M15-REG | Média | ✅ 05/06/2026 |
| M15-FIX | Editor de pesos do lottery: pool/legenda não re-renderizam ao editar + legenda /picks pós-sorteio lê canônico, não o audit | Média | ✅ 05/06/2026 |
| M16 | Lottery aplica ordem sorteada a R2/R3 (deveria ser standings invertido) — corrompe ordem + valores dynasty de R2/R3 — MAN-M16-REG | Alta | ✅ 05/06/2026 |
| OFF26-1 | Janela de keepers/cuts selada no Manager (declaração privada + budget ao vivo + lock e revelação simultânea no deadline, audit padrão M8) — MAN-OFF26-REG | Alta | 🔲 |
| OFF26-2 | Keeper sheet exportável (relatório por time pós-revelação: keepers, salários, budget FA) — insumo do Cowork — MAN-OFF26-REG | Alta | 🔲 |
| OFF26-3 | Importador de drafts de liga fantasma (rookie linear + FA auction via API, match por sleeper_player_id, preview + helper atômico) — MAN-OFF26-REG | Alta | ✅ 05/06/2026 |
| OFF26-4 | Auditoria de keepers pré-leilão (diff keeper sheet × config real da liga fantasma via API read-only) — MAN-OFF26-REG | Média | 🔲 |
| OFF26-5 | Runbook do procedimento Cowork (documentação da transcrição supervisionada da keeper sheet → liga fantasma) — MAN-OFF26-REG | Média | 🔲 (doc) |
| F9 | `bulk_register` (/auction) cria jogadores sem SalaryHistory — risco de dano silencioso já existente (achado de MAN-OFF26-3-F1; exige F1 de avaliação de dano antes do fix) | Alta | 🔲 |
| F10 | `draft_budget` replicado em JS no cap_projector (viola "1 fonte por modo de render", T2-FIX-2; cliente deve consumir endpoint canônico) — achado de MAN-OFF26-3-F1 | Média | 🔲 |
| M17 | Personalização por usuário logado: home + cap widget + 8 surfaces derivam de `current_user.team_rel` (fonte única `inject_user_team`; réplica JS do chip removida) — prompt MAN-M15-REG (ID remapeado: M15 ocupado) | Alta | ⚠️ |
| M18 | Timestamps no fuso do usuário: fonte única (`timeutil.utc_iso` + macro `local_dt` + JS `formatLocalDT`); ~11 sites migrados; armazenamento UTC mantido — prompt MAN-M16-REG (ID remapeado: M16 ocupado) | Média | ✅ 09/06/2026 (validado em prod: sync 11:47 BRT → "11:47", não 14:47 UTC) |
| E1 | Import ESPN robusto end-to-end no Render: upload manual do PDF + degradação graciosa (sem 500) + estado de review em FS gravável + parser 299→300 — MAN-E1-REG/F1/F2/FIX | Alta | ✅ 08/06/2026 (validado em prod: upload → review 300, sem 500) |
| E2 | Camada de dados: store de valores ESPN de rookie keyed por `sleeper_id` (resolve not_found+approx via pool global do Sleeper, nome+team) — consumido pelo salário do rookie draft (OFF26-3) + board DP1; rejeita Sleeper-sync e stub-$1 — MAN-E2 REG/F1/REFINE/F2 | Alta | ⚠️ store implementado + validado em localhost (12/12); store validável em prod via import; aplicação no draft só e2e no rookie draft real (~ago) |
| E3 | Import ESPN upload-only: remover a opção de URL (download inviável em prod — ESPN bloqueia IP do Render); remoção completa UI + fetch server-side + degradação graciosa associada — MAN-E3-REG (vai REG → F2 direto, sem F1) | Baixa/Média | 🔲 |
| E2-RISK | Review do import ESPN oferece rookie como match fuzzy de veterano (falso-positivo "Carnell Tate"~"Darnell Mooney" 0.665) → confirm errado contamina `espn_ref_value` do veterano (classe "Brown"). **F2: default neutro no select + confirm gated (sem confirm-por-inércia); raiz do matcher → E4-a** — MAN-E2RISK-REG/F1/F1B/F2 | Média | ⚠️ (validado localhost; pendente smoke prod com import ESPN) |
| E4 | **Guarda-chuva** — redesenho da camada de valor ESPN (`espn_ref_value` por `sleeper_id`); F1 de design concluída → fatiado em E4-a/b/c — MAN-E4-F1 | — | 🔲 (fatiado) |
| E4-a | Matcher do import ESPN resolve entrada → `sleeper_id` (pool global, nome+team Brown-safe), não fuzzy contra roster; escreve via id; sem schema. Elimina o "Brown" na raiz + troca corrupção→miss. **Absorve o conserto do matcher ex-E2-RISK** — MAN-E4-F1/F2 | Alta | ⚠️ (validado localhost; pendente smoke prod com import real) |
| E4-b | Saneamento de `sleeper_id`: F1 refutou backfill — os 2 nulos (Hollywood Brown=dup de Marquise Brown; Cameron Ward=dup de Cam Ward) são **duplicatas órfãs → DELETE** (+ 1 PlayerHistory stray) via rota admin auditável em PROD; **guard** (dedup-por-sid + `needs_review` no import_csv) p/ a causa-raiz. Sem schema — MAN-E4-F1/E4-b-F1/F2 | Média | ✅ 09/06/2026 (limpeza executada em prod: 2 removidos, 278 players, 0 sid nulo, canônicos intactos) |
| E4-c | **Guarda-chuva** — store canônico de valor ESPN `(sleeper_id, season)`; F1 de migração concluída → sub-fatiado em E4-c-1/E4-c-2 — MAN-E4-c-F1 | — | 🔲 (sub-fatiado) |
| E4-c-1 | Fundação do store (aditivo/reversível): tabela `espn_value_store (sleeper_id,season)[raw,adjusted,is_final]` via `db.create_all()` + backfill da coluna (Migration 7, season 2026 prelim) + helper único `set_espn_value` nos 8 escritores + badge PROV repontada ao store. **Entrega o store ao DP1.** — MAN-E4-c-F1/F2 | Alta | ✅ 09/06/2026 (backfill em prod: 273 linhas, schema ok, store==coluna, coluna intocada) |
| E4-c-2 | Limpeza do store (destrutivo/isolado): DROP ESPNValue (vazio) + generalizar/migrar RookieEspnValue. Único passo irreversível-sem-backup; higiene após E4-c-1; **não bloqueia DP1** — MAN-E4-c-F1 | Baixa (higiene) | 🔲 |
| DP1 | Board de planejamento de cap pré-draft: rookies entrantes com `espn_ref_value` + salário projetado `floor(ESPN×1.2)` + simulação de impacto no cap (projeção, não contrato) — lê o **store canônico** — MAN-DP1-REG | A definir | 🔲 (desbloqueado: E4-c-1 ✅ em prod) |
| WV1 | Salário de aquisição via waiver sem drop tratado como FA (waiver de jogador nunca dropado → regra de salário de FA); toca `record_acquisition` + histórico — MAN-WV1-REG | Média | 🔲 |
| F6 | Remover "keeper" como acquisition_type (migrar → auction_draft) | Média | ✅ 22/04/2026 |
| F8-RESTORE-GAP | /restore deveria chamar backfill_trades automaticamente | Baixa | ✅ 22/04/2026 |
| M5 | Ordenação por posição em todas as telas de roster | Baixa | ✅ 02/04/2026 |
| M6 | Importar resultados de temporada para atualizar ESPN ref values automaticamente | Baixa | 🔲 |
| M7 | Trade Manager: layout mais compacto e janela maior | Baixa | ✅ 02/04/2026 |
| F4 | Fix OAuth callback local (ProxyFix, host, APP_ENV, secret) | Alta | ✅ 02/04/2026 |
| F5 | Auto-seed users no startup a partir de `data/users.csv` | Média | ✅ 02/04/2026 |
| F7 | Fix SalaryHistory duplicado + rewrite 3 Browns + redesign /salary_history narrativo | Alta | ✅ 22/04/2026 |
| F7b | Data migration automática para limpar DB de produção (Render) no próximo boot | Alta | ✅ 22/04/2026 |
| F8 | Reconstruir PlayerHistory a partir da Sleeper API (drafts + transactions chain) | Alta | ⚠️ F8a concluído 22/04/2026 |
| F8a | Core rebuild via Sleeper chain + migration (sleeper_event_ref + UNIQUE) | Alta | ✅ 22/04/2026 |
| F8b | Guard AppConfig.f8_rebuilt em import_csv.py | Alta | ✅ 22/04/2026 |
| F8c | Endpoint admin + UI + ajuste do boot | Alta | ✅ 22/04/2026 |
| F1 | Correção de salários por partial name match (3 Browns bug) | Alta | ✅ 28/03/2026 |
| F2 | Ordenação do Round 1 via `draft_lottery_result` + `season_standings` | Alta | ✅ 28/03/2026 |
| F3 | Histórico inline (accordion) na aba de histórico | Média | ✅ 28/03/2026 |
| O1 | Linkificar nomes de jogadores em todas as telas | Média | ✅ 23/04/2026 |
| O2 | Enriquecer página do jogador: contexto NFL (time + depth chart) + stats históricas + ECR/ADP + schedule | Média | 🔲 |
| L1 | League Hub: visão geral da liga + detalhe por time | Alta | ✅ 23/04/2026 |
| L2 | League Hub season mode: matchups, schedule, standings | Baixa | 🔲 |
| N1 | Redesign navbar: estrutura com dropdowns + acesso rápido aos times | Média | ✅ 23/04/2026 |
| C1 | Cap projector: modo "drop programado" para simular liberações de cap | Média | 🔲 |
| M8-PERM | Lottery: simulação aberta a owners + bloqueio server-side pós-oficial | Média | ✅ 23/04/2026 |
| T2-FIX | Picks Rd2+ sem dynasty value no preview/proposta de trade | Média | ✅ 24/04/2026 |
| T2-FIX-2 | Réplica JS pickFcSid em trades.html (fix estrutural — `/api/picks` pré-resolve dynasty_value) | Alta | ✅ 24/04/2026 |
| IR-CLEANUP | Remover seletor manual de IR no roster (sync Sleeper já é autoritativo) | Baixa | 🔲 |
| UX1 | Redesign tabela de roster em /team/<id>: foto, badge acquisition PT-BR, dynasty inline | Média | ✅ 24/04/2026 |
| UX2 | Acquisition types PT-BR em telas restantes (admin, cap_projector, salary, salary_history) | Baixa | 🔲 (team_detail + roster ✅ via UX1+UX4) |
| UX3 | Fotos de jogadores em telas densas (team_detail, cap_projector) | Baixa | ✅ 24/04/2026 |
| UX4 | Macro compartilhada de linha de roster (HYBRID) — converge layout de /team/<id> e / com densidade estilo FantasyPros | Média | ✅ 24/04/2026 |
| UX4-b | Redesign de densidade e layout da página de detalhe de time (4 camadas + ESPN/Projeção em ambas telas) | Triagem | ✅ 24/04/2026 |
| UX4-c | Aperto visual final de /team/<id> e / (status bar + progress bar nova + espaçamento entre grupos + colgroup denso) | Média | ✅ 24/04/2026 |
| UX4-d | Tabela única de roster com pos inline (elimina cabeçalhos repetidos por posição) | Média | ✅ 24/04/2026 |
| UX4-e | Remover fundo pintado das rows por posição (preservar strip + cor no nome) | Média | ✅ 24/04/2026 |
| UX7 | Tema visual global mais claro (recalibragem da paleta dark) | Média | ✅ 24/04/2026 |
| UX6 | Revisão da largura máxima do container global da aplicação (~700px de ar lateral em monitor 1920px) | Média | 🔲 |
| UX5 | Redesign da seção Picks em detalhe de time (3 tabelas anuais com baixa densidade, coluna Notas vazia) | Média | 🔲 |
| DATA-1 | Badges TRADE e REVISÃO removidos da macro de listagem (info pertence à timeline/admin, não à listagem) | Média | ✅ 24/04/2026 |
| T3 | Valores redraft do FantasyCalc no Trade Manager (modelo 3 — duas barras independentes dynasty + redraft) | Média | ✅ 27/04/2026 |
| T3-FIX-UX | Migrar barras dynasty + redraft de dual-fill (T2 pattern) para delta-pointing + corrigir overflow mobile + redraft no modal preview + descrição de trade em formato "de/para" 2-colunas + alinhamento vertical entre colunas (5 sub-iterações, owner-driven via screenshot mobile) | Média | ✅ 27-28/04/2026 |
| AUD1 | Auditoria estrutural read-only do codebase: 6 lentes de incidentes históricos (F1-only — achados viram itens próprios; Lente 6 = test drive do MAN-METH-REG) — MAN-AUD1-REG/F1 | Alta | ✅ 11/06/2026 (achados absorvidos: F11, F12, E4-d, M19, M20, DOC1) |
| F11 | Rollover de season duplicado e divergente: `/api/admin/rollover/apply` (sem gate de etapas, sem check `rollover_done`, NÃO avança `current_season`) × `/api/offseason/rollover` (gated) — ambos vivos na UI; dupla execução incrementa contratos 2× — achado AUD1 Lente 2 | Alta | ⚠️ 12/06/2026 (prod verificado LIMPO; fix Opção A localhost — ✅ após smoke em prod) |
| F12 | `run_import` sobrescreve salary/contract_year a cada boot com CSV presente (dev local), sem SalaryHistory — reverte silenciosamente rollover/correções locais; coluna `salary_2025` hardcoded — achado AUD1 Lente 2 | Média | 🔲 |
| E4-d | Matching frouxo nas portas do /auction: single-entry FA/rookie matcha player por nome exato sem resolver sid (guard E4-b ausente — classe órfão) + upload Excel matcha Team por substring `%name%` — achado AUD1 Lente 4 | Baixa/Média | 🔲 |
| M19 | Validação de pesos do lottery só existe no client (JS floor/mín-1); `_normalize_weights` aceita float/zero/negativo — POST direto exclui time do pool silenciosamente — achado AUD1 Lente 1 | Baixa | 🔲 |
| M20 | Descomissionar write-side da flag single-user: sync escreve `is_my_team` via `MY_OWNER_ID`; record_acquisition/bulk_register propagam; colunas + to_dict + check_team.py + mapeamento standings (offseason.py:312) — fora do escopo M17 (só consumidores); **bloqueado: depende de M17, hoje ⚠️ (aguardando smoke prod)** — achado AUD1 Lente 3 | Baixa | 🔲 (bloqueado) |
| DOC1 | CLAUDE.md "App Startup Sequence" desatualizada: `init_auth` listado antes de sync/backfill (código: depois, app.py:138) + sync/backfill são condicionais a `fresh_import` (app.py:61), não passos de todo boot — docs-only fix — achado AUD1 Lente 6 | Média (blast radius: doc carregada em toda sessão) | 🔲 |
| O3 | Split do improvements.md: ativo (cabeçalho + Status Rápido completo + seções 🔲/⚠️) + `improvements_archive.md` (seções ✅, movidas verbatim); migração no fim de sessão quando item → ✅ — MAN-O3-REG | Média | ✅ 11/06/2026 |

---

## Itens Pendentes

> **Itens ✅ (concluídos): o detalhe vive em `improvements_archive.md`** (movido verbatim; este arquivo mantém só 🔲/⚠️). O **Status Rápido acima é completo** (todos os IDs, inclusive ✅) — é o namespace e a baseline de dedupe. Regra O3: ao marcar ✅, mover a seção no fechamento da sessão.

---

### Q1 — Script de Simulação de Temporada Completa
🔲 **Pendente** — Prioridade **Média**

**Problema:** O season rollover (passo 4 do offseason, `routes/offseason.py`) aplica VALORIZAÇÃO, incrementa `contract_year`, e renova contratos expirados. Esse processo é irreversível e afeta todos os 278+ jogadores. Hoje não há como validar o resultado antes de rodar em produção.

**Proposta:**
1. Script CLI (`simulate_season.py`) que roda o rollover completo em memória (sem gravar no banco)
2. Input: estado atual do `dynasty.db` + ESPN ref values
3. Output: tabela comparativa por jogador: salary atual → salary projetado, contract_year atual → próximo, renovações, jogadores que seriam cortados por cap
4. Reusar `salary_engine.py` que já é puro (zero DB dependencies): `full_contract_table()`, `project_next_salary()`, `valorization_rule()`
5. Flags opcionais: `--team <nome>` (filtrar por time), `--over-cap-only` (só mostrar times que estouram)

**Uso:** Dev/comissário only. Rodar antes do passo 4 do offseason para validar que nenhum salário ficou absurdo.

---

### M3 — Exportar Estado da Liga para Visualização Externa
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Com X1 os owners passam a ter acesso ao Manager. Mas pode ser útil ter um endpoint `/api/estado` que retorne JSON com rosters, salários e picks — para uso futuro no Optimizer ou para owners que queiram consumir os dados.

**Proposta:** Endpoint GET `/api/estado` retornando JSON read-only. Sem autenticação especial além do `@login_required`. Não expor dados sensíveis (sem `is_admin`, sem emails).

---

### M4 — Banner de Sync Desatualizada
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Quando o Sleeper sync falha no startup (timeout ou API fora), o usuário não tem indicação visual de que os dados podem estar desatualizados.

**Proposta:** Banner visível em todas as páginas com timestamp da última sync e botão "Sincronizar agora". Só exibir quando a sync está desatualizada. Fonte de dados: `SyncLog.query.order_by(SyncLog.synced_at.desc()).first()`.

---

### M6 — Importar Resultados de Temporada para Atualizar ESPN Ref Values
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Hoje a atualização de ESPN ref values é feita manualmente via PDF (passo 3 do offseason workflow, `espn_pdf_parser.py`). O processo exige download manual do PDF, upload no Manager, e matching de nomes.

**Proposta:** Criar pipeline que leia CSVs de stats por temporada (já disponíveis em `data/`: receiving, rushing, passing) e atualize os ESPN ref values automaticamente. Dados brutos já existem — falta o pipeline de processamento.

**Nota:** Os CSVs em `data/` são sementes desse trabalho. Formato e fonte dos dados futuros a definir.

---

### M17 — Personalização por usuário logado (default team + cap widget)
⚠️ **Implementado (F2) — pendente smoke em produção** — Prioridade **Alta** — prompt MAN-M15-REG (ID remapeado: M15 já era o Lottery)

**CONTEXTO**
Feedback de produção do Michel (owner do team_id=8, "Trust the Process") em
07/06/2026, via screenshots no WhatsApp. Com o multi-usuário (X1) ativo e os 12
owners acessando o Manager, surfaces que assumem um único usuário ficaram expostas.

**PROBLEMA / OPORTUNIDADE**
Duas surfaces ignoram o usuário logado e mostram dados do time do admin (Cangaceiros
da Colina): (1) ao abrir o site, o primeiro time exibido é o do Erico, não o do
usuário logado; (2) o widget de cap no topo mostra "$255/$200" — valores do
Cangaceiros — estático para todos os usuários, em vez de puxar o cap do time de quem
logou. Para um app multi-usuário, o estado padrão deve ser centrado no time do
próprio owner.

**DISCUSSÃO**
- O valor $255 do screenshot bate com o active_salary atual do Cangaceiros
  (confirmado pós MAN-S1-FIX), indicando que o widget renderiza o time errado, não
  um valor stale.
- Hipótese de causa raiz comum: resquício do conceito single-user "my team" (flag
  legada em vez de `current_user.team_rel`). M9/M13 já usam o padrão correto
  (`my_team_name = current_user.team_rel.name`), então existe precedente canônico.
- Possível que existam outras surfaces com o mesmo vício além das duas reportadas —
  F1 deve mapear o conjunto completo antes de fechar escopo.

**DECISÕES JÁ TOMADAS**
- Um único item para as duas surfaces (mesma família de causa raiz).
- Padrão alvo: derivar o time padrão de `current_user`, com fallback definido para
  admin/usuário sem time vinculado (comportamento exato a decidir na F1).

**ALTERNATIVAS DESCARTADAS**
- Dois itens separados (um por surface): rejeitado — fix fragmentado arriscaria
  corrigir uma surface e deixar a outra com a mesma raiz.

**QUESTÕES EM ABERTO** (F1)
- De onde vem hoje o "time padrão" da home e o time do cap widget? Mesma fonte?
- Quais outras surfaces assumem "my team" fixo?
- Qual o fallback para usuário sem time vinculado (team_id NULL) e para o admin?
- O cap widget tem réplica de lógica em JS/template além do backend?

**F1 — ACHADOS (diagnose read-only, concluída)**

Confirmada a hipótese de causa raiz: nenhuma surface reportada deriva de
`current_user.team_rel`; todas ancoram no conceito legado single-user
(`MY_TEAM_NAME` em `models.py:12` / flag `Team.is_my_team`), que resolve sempre
para o time do admin (Cangaceiros). O `$255` bate com `active_salary()` real do
Cangaceiros → time errado renderizado, não valor stale.

*Conjunto completo de surfaces com "my team" fixo:*

- **Funcionais** (renderizam dados/estado do time errado):
  1. Home — default do roster: `routes/roster.py:53` (`request.args.get("team", MY_TEAM_NAME)`).
  2. Home — fallback do roster: `routes/roster.py:63` (`Team.query.filter_by(is_my_team=True)`).
  3. Cap widget — chip JS: `templates/base.html:157-167` (`teams.find(t => t.is_my_team)` sobre `/api/teams`).
  4. Cap widget — título: `templates/base.html:71` (string `"Cangaceiros da Colina"` hardcoded).
  5. Cap Projector — pré-seleção: `routes/salary.py:22-25` (`Team.query.filter_by(is_my_team=True)`).
- **Cosméticas** (enfeite visual no time do admin para qualquer usuário):
  6. Tag "EU" no dropdown "Times ▾": `templates/base.html:51` e `:116` (mobile).
  7. League Hub — destaque do card `league-card-mine` + tag "EU": `templates/league.html:12,25`.
  8. Header do roster — prefixo 🏆: `templates/roster.html:15` (`summary.team.is_my_team`).

*Réplica, não fonte única:* a resolução do "meu time" existe em quatro lugares no
padrão legado — rota Python (home + cap projector), JS client-side (chip),
literal hardcoded (título do chip). O cap widget **re-resolve no cliente** (não
consome valor server-side); o server não envia "qual é o time do usuário" ao
template.

*Precedente canônico a replicar:* derivação por `current_user.team_rel` já
coexiste em `/team/<id>` (`routes/league.py:103-110`), banner M1
(`routes/roster.py:89-92`) e picks (`routes/picks.py:81`) — inclusive já tratam
`team_rel is None` como estado neutro.

*Fallback hoje:* as surfaces fixas não quebram com usuário sem time — mostram o
time do admin **por acidente**, não um estado neutro. As surfaces canônicas já
tratam `team_rel is None` (estado neutro / `my_team_name=None`).

*Observação:* `MY_TEAM_NAME` é importado em `routes/trades.py:9` mas **não** usado
para default (pré-seleção é só via query param M14) — import possivelmente morto.

**DECISÕES DE ESCOPO F2 (owner, pós-F1)**
1. **Fallback para usuário sem time vinculado (team_id NULL): estado neutro**
   (sem time, sem cap) — alinhado ao padrão canônico já existente
   (`team_rel is None` → neutro em `/team/<id>` e M1).
2. **Surfaces cosméticas entram na F2 junto com as funcionais** — mesma
   causa-raiz; corrigir num só passo (as 8 surfaces acima).
3. **Cap widget passa a resolução server-side, eliminando a réplica JS** —
   reaproveitar o padrão de context processor já usado na navbar
   (`inject_nav_teams` em `app.py:90-99`).

**F2 — IMPLEMENTAÇÃO (08/06/2026, ⚠️ validado em localhost)**

*Fonte única server-side:* novo context processor `inject_user_team` (`app.py`)
injeta `g_user_team` (= `current_user.team_rel` ou `None`) e `g_user_team_cap`
(= `active_salary()`) em todos os templates. É a única resolução do "time do
usuário" nas surfaces de exibição; replica o precedente canônico (`/team/<id>`,
M1, picks). Usuário sem time → `None` → estado neutro.

*8 surfaces unificadas:*
1. Home default — `roster.py:index` deriva de `current_user.team_rel.name`;
   `?team=` ainda permite ver outro time; fallback robusto cai no próprio time, não
   num time fixo; sem time → neutro (`summary=None`).
2. Home fallback — eliminado `filter_by(is_my_team=True) or teams[0]`.
3. Cap chip valor — renderizado server-side em `base.html` a partir de
   `g_user_team_cap` (réplica JS `loadCapChip` removida).
4. Cap chip título — `title="Cap: {{ g_user_team.name }}"` (literal "Cangaceiros
   da Colina" removido).
5. Cap projector — `salary.py` pré-seleciona `current_user.team_rel`.
6. Tag "EU" dropdown Times (desktop+mobile) — `t.id == g_user_team.id`.
7. League Hub `league-card-mine`+EU — `_build_team_card` recebe `my_team_id` do
   usuário logado; flag legada `team.is_my_team` não é mais lida.
8. Header roster 🏆 — `summary.team.id == g_user_team.id`.

*Limpezas:* import morto `MY_TEAM_NAME` removido de `routes/trades.py` e
`routes/roster.py`; projeção `Team.is_my_team` removida de `inject_nav_teams`
(`app.py`) — agora dado morto na navbar. A flag `is_my_team` permanece como
**dado** escrito pelo sync (schema/`sync_sleeper.py`/`record_acquisition`/
`/api/teams` to_dict) — apenas deixou de ser fonte de "time do usuário".

*Validação localhost (test_client, DB copiado, login via sessão):* 8/8 critérios.
Michel (team 8) → home + chip `$183/$200` "Trust The Process"; Erico (team 5) →
Cangaceiros; usuário sem time → neutro (200, "Sem dados", sem chip); cap projector
pré-seleciona o time certo; `league-card-mine`/🏆 no time do usuário; chip
server-side sem `teams.find`/`loadCapChip`. `salary_engine_test.py` 48/48.
**Pendente:** smoke em produção (login real dos owners).

**DEPENDÊNCIAS**
- Depende de: nenhum item aberto (X1 concluído). Bloqueia: nenhum.

---

### WV1 — Salário de aquisição via waiver sem drop tratado como FA
🔲 **Pendente** — Prioridade **Média** — prompt MAN-WV1-REG (novo: 1º item da série WV/waiver)

**CONTEXTO**
Regra de aquisição emergida em discussão de 08/06/2026 (durante o MAN-M18). A liga
distingue dois caminhos de aquisição fora de draft: **waiver** e **free agency (FA)**.
Um jogador é adquirido via waiver quando **nunca foi dropado por nenhum time**; caso
contrário, via FA. O salário atribuído ao contrato difere conforme o caminho.

Caso ilustrativo (Puka, rookie year): plausível que um rookie não seja draftado no
rookie draft e, após boa performance na semana 1, vire alvo de disputa via waiver.
Como nunca foi dropado por nenhum time, a aquisição se dá por **waiver** — mas o
salário deve ser tratado **como se viesse via FA**, justamente porque não houve drop
prévio.

**PROBLEMA / OPORTUNIDADE**
A lógica atual de criação de contrato (`record_acquisition` → `salary_engine`) resolve
salário por tipo de aquisição, mas a distinção **waiver-sem-drop → salário-como-FA**
ainda não está representada. Sem isso, uma aquisição via waiver de jogador nunca
dropado poderia receber tratamento de salário incorreto quando a regra for
implementada.

**DISCUSSÃO**
- O caminho (waiver vs. FA) depende do **histórico do jogador**: existência ou não de
  drop prévio por algum time.
- Quando não houve drop, o salário segue a regra de **FA** mesmo que o mecanismo de
  aquisição seja waiver.
- A regra toca o helper canônico (`record_acquisition`) e potencialmente o histórico
  (`PlayerHistory` / `AuctionLog`) — relevante para **não remover ainda** campos hoje
  "mortos" no payload (decisão do MAN-M18: preservar `created_at` de `AuctionLog` e do
  salary history, pois podem virar campos vivos aqui).
- Regulamento da liga a confrontar na F1 (cláusulas de waiver/FA e salário associado)
  antes de fechar escopo.

**DECISÕES JÁ TOMADAS**
- Waiver de jogador **nunca dropado** → salário tratado como **FA**.
- Registro agora, implementação adiada (depende do pacote offseason / lógica de
  aquisição).
- Campos de timestamp hoje não exibidos (`AuctionLog`, salary history) **preservados**
  — possíveis consumidores desta regra.

**ALTERNATIVAS DESCARTADAS**
- (a definir na F1)

**QUESTÕES EM ABERTO** (F1)
- Como a aplicação sabe hoje se um jogador foi dropado por algum time (fonte do sinal:
  Sleeper transactions, `PlayerHistory`, flag)?
- O regulamento define salários distintos para waiver vs. FA além do caso sem-drop?
  Quais valores/regras exatas?
- O `record_acquisition` já recebe o tipo de aquisição de uma fonte confiável, ou o
  tipo é inferido?
- Esta regra de salário tem ou terá réplica (JS do cap projector, preview de draft
  import)?

**DEPENDÊNCIAS**
- Depende de: lógica de aquisição / pacote offseason (criação de contrato fora de
  draft).
- Relaciona-se com: **OFF26-3** (importador de drafts), **E2** (salário de rookie),
  **F9** (consolidação em `record_acquisition`).
- Bloqueia: nenhum item aberto hoje.

---

### E2 — Store de valores ESPN de rookie (camada de dados)
⚠️ **Store implementado + validado em localhost (08/06/2026) — aplicação no draft aguarda o rookie draft real** — Prioridade **Alta** — MAN-E2 REG/F1/REFINE/F2

**CONTEXTO**
No smoke test do E1 em produção, o owner notou que rookies da tabela ESPN não foram
"identificados" (ex.: **Carnell Tate** WR/TEN/$12 — citado como "Cornell Tate").

**PROBLEMA / OPORTUNIDADE**
**Não é bug de parse nem de matching** — o parser lê "Carnell Tate, TEN, $12"
corretamente; ele simplesmente **não existe no DB** (rookie 2026; rookies entram só no
rookie draft, passo 5, *depois* do import ESPN, passo 3). O ESPN PPR Top 300 inclui
rookies + FA fora do elenco → caem em **not_found** → o valor ESPN é **descartado**
(E1-VERIFY confirmou: not_found = skip puro). Quando o rookie é criado no rookie draft
(via OFF26-3 ou `/auction`), `salary = floor(ESPN×1.2)` **não tem o valor** → default
**$1** no importador (ou exige digitação manual no `/auction`). Resultado: salários de
rookie errados se a fonte não for resgatada.

**DIMENSIONAMENTO (contra o DB de produção, 08/06/2026):** dos 300 parseados, 71 são
not_found (28 K/DST + **43 skill**). Os skill são majoritariamente **rookies 2026** de
valor relevante — ex.: **Jeremiyah Love RB $46** (rank 12), **Carnell Tate WR $12**,
Makai Lemon, KC Concepcion, Kenyon Sadiq TE, Omar Cooper Jr. Parte são veteranos/FA com
**$0** (Rashod Bateman, Pat Freiermuth, Samaje Perine…) — esses são **inofensivos** (já
virariam $1). O dano concentra-se nos **rookies de alto valor**.

**PROPOSTA (F1 read-only decide a forma):**
- Opções a avaliar: (a) permitir **criar player** a partir de entradas not_found no review
  (stub + espn_ref_value antes do draft); (b) **persistir** os not_found num store de
  valores ESPN pendentes, aplicados quando o player for criado; (c) o importador OFF26-3 /
  `register_rookie` **buscar o valor** num snapshot ESPN ao criar o rookie; (d) manter
  digitação manual como fallback (`register_rookie` já aceita `espn_ref_value`).
- Não auto-criar players sem revisão; preservar os caminhos canônicos de escrita.

**DEPENDÊNCIAS**
- Relaciona-se a **OFF26-3** (importador de rookie precisa do `espn_ref_value` p/ o salário).
- Workaround atual: admin digita o ESPN value no `/auction` ao registrar o rookie.
- Bloqueia: salário correto no **rookie draft 2026** (passo 5).

#### Fase 1 Diagnose ✅ (08/06/2026) — MAN-E2-F1 (read-only, zero writes)

- **(a) Sync cria Player para roster novo? SIM.** `run_sync` (sync_sleeper.py:260-282)
  cria com estado **stub**: `salary=$1, contract_year=1, contract_start_season=CURRENT_SEASON,
  acquisition_type="unknown", espn_ref_value=0, needs_review=True`, linkado por
  `sleeper_player_id`. Em players **existentes nunca toca** salary/contract/acquisition_type
  (linha 242). Match: sleeper_id → nome normalizado (sem fallback de sobrenome — fix 3 Browns).
- **(b) Rookies já rosterados na liga? NÃO — premissa do owner refutada.** Carnell Tate
  (id 13279), Jeremiyah Love (13287), Makai Lemon (13294), KC Concepcion (13298) existem
  no **pool global** do Sleeper (têm id) mas **0 de 4 estão rosterados** (273 rosterados na
  liga, nenhum deles). Rookies só entram em roster **quando draftados** (passo 5). Logo um
  sync agora **NÃO** criaria a row do Carnell Tate.
- **(c) Rookie draft cria ou atribui? Idempotente por sleeper_id.** O importador OFF26-3
  (`draft_import.py`) resolve por `find_player_by_sleeper_id` → **atualiza** se existir,
  **cria** (`record_acquisition(player=None, sleeper_player_id=…)`) se não; idempotente por
  `event_ref`. **Pré-popular um player (stub) com o sleeper_id é SEGURO** — o importador o
  casa por id, sem colisão/duplicata. `register_rookie` (`/auction`) casa por **nome+team**
  → risco pequeno de duplicata se o nome divergir (caminho manual).
- **(d) `floor(ESPN×1.2)`: fonte única, sem réplica.** O **salário** rookie é só
  `salary_engine.year1_salary("rookie_draft",0,espn_adj)` → `_floor(espn_adj)`, consumido por
  `record_acquisition` (importador + `/auction`). O `×1.2` (raw→ajustado) é conversão de
  **boundary** em cada entrada (auction/admin/salary/parser), por design (CLAUDE.md). **Sem
  réplica do cálculo de salário em JS/templates** — só texto de display ("floor(ESPN×1.2)").
- **(e) Ordem sync → ESPN Final → rookie draft fecha o gap? NÃO.** Dois motivos: (1) rookies
  não estão rosterados pré-draft (b) → sync não os traz; (2) **o Sleeper não tem ESPN value**
  (é roster-only) — o valor existe **só no PDF**. A via Sleeper-sync **não fornece** o
  `espn_ref_value`. (Se os rookies estivessem rosterados, não haveria hazard de escrita: sync
  casa por sleeper_id, ESPN import faz upsert por player+season, importador casa por id — tudo
  idempotente. Mas é moot: eles não estão.)

**RECOMENDAÇÃO → solução ESPN-side (via Sleeper-sync NÃO é viável).** Insight aproveitável:
os rookies **existem no pool global do Sleeper com `sleeper_player_id`** (só não rosterados).
Então dá para, no review do import, **mapear cada not_found (nome) → pool global do Sleeper →
`sleeper_player_id`** e, por essa chave: (opção stub) criar um Player stub com `espn_ref_value`,
ou (opção pending-store) persistir o valor ESPN keyed por `sleeper_id`. Em qualquer das duas,
o **importador OFF26-3 casa por `sleeper_id` e aplica idempotentemente** ao criar o rookie no
draft — sem inventar dados (PDF dá nome+valor, pool do Sleeper dá o id canônico). **Disparar
REFINE do E2** para escolher entre *stub no review* × *pending-store* antes de qualquer F2.
Status E2 permanece 🔲.

#### REFINE ✅ (08/06/2026) — MAN-E2-REFINE: re-escopo como camada de dados
A discussão de produto revelou um **segundo consumidor** do valor ESPN de rookie além do
salário no draft: um **board de planejamento de cap pré-draft** ([[DP1]]). Com dois
consumidores, o armazenamento fica decidido.

**Escopo final (contratos fixados; mecânica fica p/ o F2):**
- No import ESPN, cada `not_found` é resolvido para um **`sleeper_player_id`** via o **pool
  global do Sleeper**, usando o **matcher canônico com nome+team** como desambiguador (sem
  substring/sobrenome isolado — risco "Brown").
- O `espn_ref_value` resolvido é persistido num **store de valores keyed por `sleeper_id`**
  (camada de dados; formato exato no F2).
- **Consumidor (a):** o caminho de criação de rookie (**OFF26-3**) lê o store ao materializar
  o rookie no draft e aplica `floor(ESPN×1.2)` **idempotentemente** (casa por `sleeper_id`).
- **Consumidor (b):** o **board de planejamento de cap** ([[DP1]]).
- **Limpeza:** o store é transitório do ciclo de draft — limpar/expirar pós-draft (o contrato
  vivo passa a ser a fonte). Entradas **$0** e **K/DST** são inócuas/fora do foco.

**Rejeitadas:**
- **Via Sleeper-sync** (E2-F1): inviável — rookies não rosterados pré-draft e o Sleeper é
  roster-only (não tem ESPN value).
- **Player stub de $1:** rejeitada — viola "rookie entra só pelo draft", polui roster/cap com
  meio-contratos de $1, e serve mal o board de planejamento.

Próximo: **MAN-E2-F2** (implementar o store + aplicação no draft). E2 permanece 🔲.

#### Fase 2 Implementação ⚠️ (08/06/2026) — MAN-E2-F2
Regulamento **8.2.7**: salário de rookie = ESPN ref × 1,2 — encapsulado no `salary_engine`.

**Camada de dados (`models.py`):** modelo **`RookieEspnValue`** (`uq(sleeper_id, season)`),
criado por `db.create_all()` (sem migration). Helpers: `upsert_rookie_espn` (idempotente),
`rookie_espn_adjusted(sid, season)`, `clear_rookie_espn_store(season=None)`. Guarda
`espn_adjusted` (= raw×1.2, ref value — **não** salário); NÃO é Player (não polui roster/cap).

**População (`routes/admin.py`, no confirm do import):** `_resolve_not_found_to_store`
resolve cada candidato (`not_found` **+ approximate não resolvido a player do DB**) contra o
**pool global do Sleeper** via `_norm_name` + **desambiguação por team** (nome único → ok;
múltiplos → exige team único, senão `ambiguous` e não chuta — **Brown-safe**, sem
substring/sobrenome). Exclui **$0** e **K/DST**. Upsert idempotente (provisório reimportável).
Achado: rookies podem cair em **approximate** por falso-positivo de fuzzy (ex.: "Carnell Tate"
~ "Darnell Mooney" 0.665) — por isso o approximate-skipped também entra no store.

**Consumo no draft (`routes/draft_import.py` / OFF26-3):** ao materializar o rookie (criar
por `sleeper_id`, ou matched sem espn), busca `rookie_espn_adjusted` e passa a
`record_acquisition`, que deriva `floor(ESPN×1.2)` via `year1_salary` — **sem replicar o
cálculo**. Idempotente por `event_ref`. O preview também exibe o salário projetado dos
unmatched a partir do store.

**Limpeza (`routes/offseason.py`):** `toggle_rookie_draft` (marcar concluído) chama
`clear_rookie_espn_store()` — store é transitório do ciclo de draft.

**Validação (08/06/2026) — 12/12** (test_client, temp DB; PDF real + pool read-only):
store populado (Jeremiyah Love sid 13287 → adj **55**; **Carnell Tate 13279 → adj 14**);
re-import upsert sem duplicar; $0/K-DST fora; **Brown-safe** (nome do store == nome do pool
p/ o sid); matched (Bijan 68) intocado e fora do store; rookie criado → salário **floor(55)=55**
via `record_acquisition` (SalaryHistory+AuctionLog); cleanup zera o store; `salary_engine` 48/48.

**Status ⚠️ (não ✅):** o store + resolução + população são **validáveis em prod agora** (rodar
um import e conferir o store); a **aplicação no draft** só tem e2e no **rookie draft real (~ago,
regra 8.2.2)**. Regra "✅ só após prod". **DP1 desbloqueado** — o store existe; F1/F2 do DP1 podem
seguir.

**⚠️ Risco residual conhecido (candidato a item — classe "Brown"):** a mitigação cobre o
approximate-**skipped**, mas se o admin **CONFIRMAR** um match falso de fuzzy (ex.: "Carnell Tate" →
"Darnell Mooney" 0.665), o valor ESPN do rookie **contamina o `espn_ref_value` de um veterano real**.
Fix limpo (próxima sessão): não oferecer como fuzzy-match contra veterano do DB uma entrada que já
resolve para o `sleeper_id` de um rookie (rebaixar/sinalizar esses candidatos no review).

**Arquivos:** `models.py` (modelo + helpers), `routes/admin.py` (resolver + confirm),
`routes/draft_import.py` (consumo), `routes/offseason.py` (limpeza), `CLAUDE.md`.

---

### E3 — Import ESPN upload-only: remover a opção de URL
🔲 **Pendente** — Prioridade **Baixa/Média** — MAN-E3-REG (08/06/2026) — **vai REG → F2 direto (sem F1)**

**CONTEXTO**
O import ESPN (passo 3 do offseason workflow) oferece hoje dois caminhos de entrada:
**upload do PDF** (recomendado) e **download por URL** (alternativa, com degradação
graciosa). O **E1** estabeleceu que o download por URL é **estruturalmente inviável em
produção** — a ESPN bloqueia o IP de datacenter do Render (anti-bot). Como o import é
operação de **prod** (único contexto real de uso pelo admin), a URL nunca funciona lá
e só gera ruído/confusão na UI.

**PROBLEMA / OPORTUNIDADE**
A opção de URL é uma falsa escolha em produção: o owner pode tentá-la, ela falha (cai
na degradação graciosa → flash), e o caminho real continua sendo o upload. Remover a
URL simplifica a UI e elimina código (fetch server-side + a degradação graciosa que
existia **só** para cobrir esse fetch).

**DISCUSSÃO**
- **E1-F1 já isolou** download/parse/match num **único caminho server-side**
  (`routes/admin.py` + `espn_pdf_parser.py`), **sem réplica** em JS/templates. A
  isolação já está diagnosticada → o item pode ir **REG → F2 direto, sem F1**.
- **Nuance:** a URL **funciona em dev/localhost** (E1-F1), mas o import é operação de
  prod — o ganho de manter a URL para dev é **marginal** e não justifica o ruído em
  prod.
- UI atual: "UPLOAD DO PDF (RECOMENDADO)" + "...OU URL DO PDF ESPN PPR (ALTERNATIVA)".

**DECISÃO DE ESCOPO (a confirmar pelo owner na F2)**
- **(a) Remoção completa — RECOMENDADA:** input de URL na UI **+** caminho de download
  server-side **+** a degradação graciosa associada (que existia só para cobrir esse
  fetch). Resultado: import **upload-only**, menos código e superfície de erro.
- **(b) Esconder só a UI**, mantendo o backend de download: descarta menos código e
  preserva a URL para dev, mas deixa caminho morto em prod. Menos limpo.

**ALTERNATIVAS DESCARTADAS**
- Manter ambos como está: rejeitado — a URL é falsa escolha em prod (origem do item).

**DEPENDÊNCIAS**
- Depende de: **[[E1]]** (✅ — upload é o caminho funcional comprovado em prod).
- Relaciona-se com: nada aberto. Bloqueia: nenhum.

---

### E2-RISK — Fuzzy oferece rookie como match de veterano no review (classe "Brown")
⚠️ **Implementado (F2) — validado em localhost; pendente smoke em prod com import ESPN real** — Prioridade **Média** — MAN-E2RISK-REG/F1/F1B/F2 — **RE-ESCOPADO (híbrido): E2-RISK = só o mínimo de tela; conserto do matcher (raiz) → [[E4-a]]**

**F2 — IMPLEMENTAÇÃO (09/06/2026, ⚠️ validado em localhost)**
- **Mudança única (camada de tela):** `templates/espn_review.html` — o `<select>` de cada
  approximate passa a iniciar **NEUTRO** (`<option value="" selected>— selecionar —`);
  removido o `selected` que pré-escolhia o `best_player` (veterano). **Não toca** matcher,
  `salary_engine`, `ESPNValue`, `RookieEspnValue`, sync nem schema.
- **Gate de confirmação (já existente, agora ativado pelo default neutro):**
  `getApproxResolutions` conta select vazio como não-resolvido e `updateStatus()` (no load
  + a cada `change`) desabilita `#btn-confirm` enquanto houver pendência. Confirm só
  habilita quando **toda** approximate tem escolha explícita (match ou "Nenhum (aplicar
  $1)").
- **Caminho de escrita inalterado:** resolução explícita a um veterano ainda grava via
  `_save_espn_value` (a F2 só impede confirm-por-inércia, não muda o que a escrita faz).
- **Validação localhost (test_client, DB copiado):** review renderiza sem pré-select
  (option neutra `selected`, nenhum candidato `selected`); confirm **sem ação** NÃO altera
  o `espn_ref_value` do veterano (32.4→32.4 — Mooney não recebe o valor de Tate); confirm
  com resolução explícita grava normal (32.4→48.0); auto-matched/not_found intactos.
  `salary_engine_test.py` 48/48. **Pendente:** smoke em prod com import ESPN real.

**CONTEXTO**
Achado durante o **[[E2]]**-F2 (08/06/2026), registrado como risco residual no E2 e no
handoff, agora item próprio. No **review do import ESPN**, o matching fuzzy pode
oferecer um **rookie** como candidato de match a um **veterano real do DB** por
falso-positivo de similaridade. Caso observado: **"Carnell Tate"** (rookie) ~
**"Darnell Mooney"** (veterano), similaridade **0.665**. A mitigação do E2 cobre apenas
o caso em que o approximate é **pulado** (skip — o valor do rookie é capturado no store
mesmo assim); **não** cobre o caso em que o admin **confirma** o match falso.

**PROBLEMA / OPORTUNIDADE**
Se o admin confirmar um match falso no review (aceitar "Carnell Tate" → "Darnell
Mooney"), o valor ESPN do rookie **contamina o `espn_ref_value` de um veterano real**
(Mooney receberia o valor de referência do Carnell Tate). É a **classe do incidente
"Brown"** (Marquise / A.J. / Amon-Ra St. Brown com salários trocados por match
parcial). Risco latente de corrupção de dado em prod, dependente de erro humano no
review.

**DISCUSSÃO**
- O hazard é específico do **fluxo de confirmação do review** do import ESPN.
- A entrada problemática é justamente uma que **já resolve para o `sleeper_id` de um
  rookie** (via pool global do Sleeper) — o sistema tem como saber que aquele candidato
  "é rookie" e mesmo assim o oferece como match contra um veterano.
- Fix delineado no E2 (a confirmar/refinar na F1): **não oferecer** como fuzzy-match
  contra veterano do DB uma entrada que já resolve para o `sleeper_id` de um rookie; ou
  **rebaixar/sinalizar** esses candidatos no review para o admin não confirmar por
  engano.

**DECISÕES JÁ TOMADAS**
- Item **próprio** (separado do E2), focado no caminho de **confirm errado** (o *skip*
  já está mitigado).
- O **matching canônico** (exato → case-insensitive → normalizado, sem substring/
  sobrenome isolado) **não muda** — o foco é o que o review *oferece* como candidato
  fuzzy.

**QUESTÕES EM ABERTO** (F1)
- Onde exatamente o review monta a lista de candidatos fuzzy de match contra o DB, e em
  que ponto uma entrada rookie (resolvível a `sleeper_id` no pool) poderia ser
  excluída/sinalizada?
- Essa lógica de "oferecer candidato fuzzy" existe em mais de um lugar (rota, template,
  JS do review)? (réplica)
- O sinal "esta entrada é rookie" (resolve a `sleeper_id` de não-rosterado) está
  disponível no momento em que os candidatos são montados, ou exigiria resolução
  adicional?
- Há outros consumidores do mesmo mecanismo de candidatos fuzzy além do confirm de
  `espn_ref_value`?

**F1 — ACHADOS (diagnose read-only)**
- **Hazard nasce em `match_players`** (`espn_pdf_parser.py`): fuzzy via
  `difflib.SequenceMatcher` **contra o roster local apenas**. Faixa `0.65 ≤ r < 0.82`
  → `approximate` com `candidates[:5]` (qualquer DB player com `r ≥ 0.5`). Tate~Mooney
  cruza 0.665 por **falta de candidato melhor local**.
- **Sem réplica:** a lógica fuzzy é **fonte única server-side** (`match_players`); o
  template `espn_review.html` só renderiza os candidatos no `<select>` e o JS
  (`getApproxResolutions`) lê `sel.value` — **não recomputa nada no cliente**.
- **Sem outros consumidores:** `match_players` tem um único caller
  (`admin.py:610`); `/admin/review` (M2) é código distinto (`needs_review` do sync),
  não candidatos fuzzy.
- **Agravante:** o `<select>` **pré-seleciona o `best_player`** (veterano —
  `espn_review.html:62` `selected if c.player_id == a.player_id`) e o JS trata
  **qualquer `sel.value` truthy como resolvido** → **confirm sem interação** grava o
  valor do rookie no `espn_ref_value` do veterano via `_save_espn_value`
  (`admin.py:746-760`) — **escrita direta no confirm, NÃO passa por
  `record_acquisition`**.

**F1B — ACHADOS (diagnose complementar: `espn_ref_value` por `sleeper_id`?)**
- `espn_ref_value` é lido como **atributo de Player** por `salary_engine`
  (rollover/projeção — **puro, sem DB**), `models`, e templates. Virar "resolvido por
  `sleeper_id`" **violaria a pureza da engine** ou exigiria **materializar no Player de
  qualquer forma** (a coluna não sumiria).
- **Três tabelas de valor ESPN** sob chaves distintas: `Player.espn_ref_value`
  (player), `ESPNValue` (player_id+season, exige Player), `RookieEspnValue`
  (**sleeper_id**+season, hoje transitório). Unificar exige **chave nova
  `sleeper_id+season`** e **inverter o store de transitório→canônico**.
- **`sleeper_id` não é confiável em todo Player** (`import_csv` cria Player sem ele;
  preenchido só quando o sync casa) → **chave de junção furada hoje**.
- **Ganho de segurança lateral:** resolver por id contra o pool (nome+team Brown-safe)
  troca a classe de falha de **"corrupção/escrita errada"** por **"miss/não escreve"**
  (ambíguo → não chuta) — estritamente mais seguro. Ressalva: pode **sub-resolver**
  (miss) onde o roster acertava se o team da entrada estiver stale.
- **Conclusão F1B:** a unificação é correta e elegante, mas é **redesenho de camada de
  dados**, não fix de segurança → F2 no escopo menor; unificação como item à parte.

**RE-ESCOPO + DECISÃO HÍBRIDA (owner, pós-F1B)**
- **E2-RISK passa a ser SOMENTE o mínimo de tela:** remover o **pré-select do veterano**
  no review do import ESPN, de modo que um **confirm sem interação não grave valor em
  veterano** (default seguro). **Não toca** matcher, `salary_engine`, `ESPNValue` nem
  schema. Risco quase nulo, para a corrupção **agora**.
- **O conserto do matcher (resolução por `sleeper_id`) sai do escopo do E2-RISK** e passa
  a fazer parte do item de design da estrutura ESPN — agora a fatia **[[E4-a]]** (o E4
  foi fatiado na F1 de design), onde matcher (resolução por id) e armazenamento
  **convergem para a chave certa**, em vez de mexer no matcher sobre fundação ainda não
  decidida.

**DEPENDÊNCIAS**
- Relaciona-se com: **[[E2]]** (mesma área de resolução de import ESPN), **[[E3]]**
  (limpeza da UI de import ESPN) e **[[E4-a]]** (recebe o conserto do matcher — fecha a
  raiz que o F2 do E2-RISK só paliou).
- Não bloqueia itens abertos.

---

### E4 — Redesenho da camada de valor ESPN (`espn_ref_value` por `sleeper_id`)
🔲 **Pendente (guarda-chuva)** — origem **MAN-E2RISK-F1B**; F1 de design concluída (MAN-E4-F1, 09/06/2026) — **FATIADO em [[E4-a]] (agora) / [[E4-b]] (em seguida) / [[E4-c]] (atrelado a [[DP1]])**

**CONTEXTO**
Surgiu da diagnose **[[E2-RISK]]**-F1B. A proposta do owner: tratar `espn_ref_value`
como **atributo do jogador resolvido por `sleeper_id`** (chave canônica, à prova de
homônimo), com o **uso** variando por status de roster (veterano → referência de
contrato; rookie/FA fora da liga → projeção de salário de draft). Sob esse desenho, o
matcher do import ESPN teria **uma única tarefa — resolver entrada ESPN → `sleeper_id`**
— e os consumidores leriam por id, eliminando o falso-positivo "Brown" **na raiz** (o
valor pousa no jogador certo por id, não por similaridade de nome).

**PROBLEMA / OPORTUNIDADE**
Hoje há **três tabelas de valor ESPN** sob chaves distintas — `Player.espn_ref_value`
(por player), `ESPNValue` (player_id+season, exige Player), `RookieEspnValue`
(sleeper_id+season, transitório). O matcher resolve por **fuzzy contra o roster local**
(origem do hazard E2-RISK). Convergir matcher + armazenamento para a chave certa
(`sleeper_id`) de uma vez é mais limpo do que mexer no matcher sobre fundação ainda não
decidida.

**DISCUSSÃO / RESTRIÇÕES TÉCNICAS (da F1B)**
- **`salary_engine` é puro** (lê `.espn_ref_value` de um objeto, sem DB) → o valor
  precisa continuar **materializado no Player** de qualquer forma; "resolver por
  `sleeper_id`" não elimina a coluna, no máximo a torna um cache/derivado.
- **Unificar exige chave nova `sleeper_id+season`** e **inverter o store** de
  transitório → canônico (persistente), reconciliando com `ESPNValue` (que já é o
  registro por-season com `is_final`).
- **`sleeper_id` tem buracos** (ex.: `import_csv` cria Player sem ele) → a chave de
  junção precisa ser **saneada/garantida** antes de virar canônica.
- **Ganho de segurança:** resolução por id + nome+team Brown-safe troca "corrupção"
  por "miss" (ambíguo → não chuta); ressalva: pode sub-resolver se o team da entrada
  estiver stale.

**DECISÕES JÁ TOMADAS**
- É **item de design próprio** (não o fix de segurança — esse é o mínimo de tela do
  E2-RISK).
- **Recebe o conserto do matcher** (resolução por `sleeper_id`) que saiu do escopo do
  E2-RISK.
- O `salary_engine` **permanece puro** — qualquer desenho preserva o valor materializado
  no Player.

**QUESTÕES EM ABERTO** (F1 deste item)
- Qual a chave/tabela canônica final e como reconciliar as três existentes sem perder
  `is_final`/histórico por season?
- Como sanear `sleeper_id` em Players legados/CSV antes de virar chave de junção?
- O store deixa de ser transitório (persistente) ou continua transitório alimentando um
  Player materializado?

**F1 — ACHADOS (diagnose de design, read-only; snapshot prod 07/06, 280 players)**

Os três receios da F1B foram **desmontados pelos dados**:
- **Não há três fontes vivas disputando.** Só `Player.espn_ref_value` é viva (250/280
  `>0`). **`ESPNValue` está VAZIA em prod** (0 linhas; único leitor = badge PROV do
  cap_projector, que com 0 linhas nunca acende). `RookieEspnValue` é transitória e
  **complementar** (cobre o vão pré-roster que as outras não cobrem — ambas exigem
  `player_id`). Sobreposição ativa: só Player↔ESPNValue (mesmo `adjusted`, escritos
  juntos por `_save_espn_value`), latente porque ESPNValue está vazia.
- **`sleeper_id` já cobre 99,3%** (278/280; **0 duplicatas**). Só **2 nulos**
  ("Hollywood Brown" = apelido de Marquise Brown; "Cameron Ward"), ambos não-rosterados
  e com `nfl_team` vazio. Saneamento é mínimo, **incremental, não pré-requisito atômico**
  (nulos degradam graciosamente = sem valor, como hoje).
- **Pureza do `salary_engine` preservada SEM tocar a engine:** a materialização do valor
  no Player **já existe** (`_save_espn_value` seta `player.espn_ref_value`); muda só a
  **fonte** (store canônico) e o **join** (por `sleeper_id`, não por fuzzy). A engine
  continua lendo `.espn_ref_value` do objeto, nunca faz lookup.

*Modelo-alvo:* chave canônica **`(sleeper_id, season)`**; base = **`RookieEspnValue`
generalizado** (persistente, com `is_final`) que **subsume `ESPNValue`**;
`Player.espn_ref_value` vira **cache materializado**; **`ESPNValue` aposentada** (vazia
→ sem migração de linhas).

*Achado estrutural decisivo:* o **conserto do matcher** (resolver entrada ESPN →
`sleeper_id`) é **independente** da reconciliação e entrega **quase todo o ganho de
segurança sem tocar schema**. A fundação de dados (store canônico) só precisa vir quando
a **leitura pré-roster (DP1)** for priorizada.

*Regressão roster→pool:* a falha vira **miss** (seguro e visível em not_found/review),
**não corrupção**; concentra-se nos 2 nulos e em `team` stale raro.

**FATIAMENTO (priorização da F1)**
- **[[E4-a]] — matcher por id** *(agora; sem schema, reversível, maior retorno/risco)*:
  resolve entrada ESPN → `sleeper_id` contra o pool global, Brown-safe (reusa
  `_load_players_db`/`_norm_name`/desambiguação nome+team); escreve via
  `find_player_by_sleeper_id`; `approximate`/review só para ambiguidade genuína. Entrega
  a eliminação do "Brown" **na raiz** + troca corrupção→miss. **Absorve/substitui o
  conserto do matcher que saíra do [[E2-RISK]].**
- **[[E4-b]] — saneamento de `sleeper_id`** *(em seguida; incremental, sem schema)*:
  backfill dos 2 nulos (com tratamento de apelido) + guard para Players novos.
- **[[E4-c]] — store canônico** *(atrelado a [[DP1]]; único passo com migração,
  data-light)*: generalizar `RookieEspnValue` → store persistente
  `(sleeper_id, season)[raw, adjusted, is_final]`; confirm + rollover escrevem nele;
  materializar `Player.espn_ref_value` a partir dele; badge PROV passa a ler o store;
  **aposentar `ESPNValue`**. Habilita leitura pré-roster (DP1).

**DEPENDÊNCIAS**
- Origem: **[[E2-RISK]]**-F1B. Guarda-chuva dos sub-itens **[[E4-a]]/[[E4-b]]/[[E4-c]]**.
  Relaciona-se com **[[E2]]** (store), **[[E3]]** (UI de import), **[[DP1]]** (E4-c
  habilita a leitura pré-roster). Não bloqueia itens abertos hoje.

---

### E4-a — Matcher do import ESPN resolve por `sleeper_id` (Brown-safe)
⚠️ **Implementado (F2) — validado em localhost; pendente smoke em prod com import real** — Prioridade **Alta** — fatia de **[[E4]]** (MAN-E4-F1/F2) — **absorve o conserto do matcher ex-[[E2-RISK]]; fecha a raiz que o F2 do E2-RISK só paliou**

**F2 — IMPLEMENTAÇÃO (09/06/2026, ⚠️ validado em localhost)**
- **`espn_pdf_parser.match_players(parsed, db_players, sid_resolver=None)`** ganhou o
  parâmetro injetável `sid_resolver`. Em modo resolver, a identidade é por **`sleeper_id`**:
  sid → Player rosterado = **matched por id** (sem review); sid → não-rosterado =
  **not_found** (vai p/ o store no confirm — **nunca oferecido como match de veterano**);
  sem sid limpo = fallback **igualdade exata** de nome (matched) ou **review**
  (approximate). **Sem auto-match silencioso por similaridade** no modo resolver. Modo
  legado (`sid_resolver=None`) **preservado byte-a-byte** (testes/retrocompat).
- **`routes/admin.py`:** extraídos `_build_pool_index()` + `_resolve_entry_sid(entry, idx)`
  (fonte única Brown-safe nome+team, reusada pelo store E2 — `_resolve_not_found_to_store`
  refatorado p/ usá-los). `espn_import_page` constrói o índice do pool e passa
  `sid_resolver` ao matcher; pool indisponível → `None` → fallback gracioso (sem 500).
- **Não toca** `salary_engine` (puro), camada de armazenamento (escrita segue em
  `Player.espn_ref_value` via id — store canônico é [[E4-c]]), nem `SalaryHistory`/
  `PlayerHistory`. **Sem schema.** Reversível (remover o resolver volta ao legado).
- **Validação localhost (test_client + pool real, 11.810 nomes):** caso Tate/Mooney —
  "Carnell Tate" resolve ao sid 13279, vai p/ **not_found**, **não** entra em matched nem
  como candidato de approximate; **Mooney não recebe o valor**. Veterano (Jayden Daniels)
  **matched por sleeper_id**. Typo ("Jayden Daneils") → **review**. Sobrenome isolado
  ("Brown") **não resolve**. 2 nulos (Hollywood Brown, Cameron Ward) degradam sem match
  espúrio. Reimport **idempotente**. Confirm de matched-by-id grava `espn_ref_value`
  (=60.0); review renderiza 200. `salary_engine_test.py` 48/48.
- **Relação com [[E2-RISK]]:** o E2-RISK (default neutro + gate) permanece como a **camada
  de tela**; **E4-a é a raiz** (resolução por id) — juntos, o "Brown" não acontece nem por
  inércia (tela) nem por similaridade contra lista pobre (matcher).
- **Pendente:** smoke em prod com import ESPN real (medir split resolvidos-limpos vs.
  review).

**ESCOPO**
Trocar a resolução de identidade do import ESPN de **fuzzy contra o roster local** (origem
do hazard "Brown", `match_players`) por **resolução da entrada ESPN → `sleeper_id` contra
o pool global do Sleeper**, reusando `_load_players_db` / `_norm_name` / desambiguação
nome+team **Brown-safe** (sem substring/sobrenome) já existente em
`_resolve_not_found_to_store`. Escrita continua em `Player.espn_ref_value` via
`find_player_by_sleeper_id` (sem mudança de schema). `approximate`/review fica só para
**ambiguidade genuína**.

**POR QUÊ AGORA**
Independente da reconciliação de tabelas; entrega a **eliminação do "Brown" na raiz** + a
troca **corrupção→miss** (falha segura/visível). Reversível, sem schema, maior
retorno/risco. Substitui o "conserto do matcher" que saíra do E2-RISK (cujo F2 entregou
só o mínimo de tela).

**INVARIANTES A PRESERVAR**
- `salary_engine` puro (não tocar); idempotência do import/confirm; Brown-safety
  (nome+team, nada de substring); `SalaryHistory`/`PlayerHistory` intactos.

**DEPENDÊNCIAS**
- Fatia de **[[E4]]**. Fecha a raiz do **[[E2-RISK]]** (cujo F2 foi paliativo de tela).
  Não depende de [[E4-b]]/[[E4-c]].

---

### E4-c — Store canônico de valor ESPN por `(sleeper_id, season)`
🔲 **Pendente (guarda-chuva)** — fatia de **[[E4]]**; F1 de migração concluída (MAN-E4-c-F1) — **SUB-FATIADO em [[E4-c-1]] (aditivo/reversível — agora) / [[E4-c-2]] (destrutivo/isolado — higiene)**

**ESCOPO**
Generalizar `RookieEspnValue` → **store persistente** keyed `(sleeper_id, season)` com
`raw + adjusted + is_final` (deixa de ser transitório). Confirm do import + rollover
escrevem nele; **materializar** `Player.espn_ref_value` a partir dele (engine intocada —
lê do objeto); badge PROV (cap_projector) passa a ler o store; **aposentar `ESPNValue`**
(vazia em prod → sem migração de linhas).

**POR QUÊ / QUANDO**
Realiza a visão "valor ESPN como atributo único por `sleeper_id`" e **habilita leitura
pré-roster** ([[DP1]]). É o **único passo com migração** (atômico), mas **data-light**
pelo estado vazio do `ESPNValue`. Só compensa atrelado a um consumidor (DP1) — priorizar
junto.

**INVARIANTES A PRESERVAR**
- `salary_engine` puro (valor materializado no Player, nunca lookup na engine);
  idempotência; `is_final`/semântica provisório-final preservada no store; sem perda de
  histórico por season.

**F1 — ACHADOS (diagnose de migração, read-only; prod pós-E4b)**
- **Estado-alvo confirmado:** **tabela canônica NOVA** `(sleeper_id, season)[raw, adjusted,
  is_final]` via `db.create_all()` (aditivo, **sem ALTER**) — **mais reversível** que
  generalizar o `RookieEspnValue` in-place (que exigiria ALTER p/ `is_final`).
  `Player.espn_ref_value` vira **cache materializado**; `ESPNValue` aposentado;
  `RookieEspnValue` migrado/generalizado **por último**.
- **Backfill seguro:** **248 value-bearing, 100% com sid** (os 2 sem-sid eram os órfãos
  279/280, já deletados no E4-b); **0 sids duplicados** → chave `(sid, season)` segura. A
  coluna é populada **a partir de si mesma** → pós-backfill **coluna == store** (sem
  backfill store→coluna separado).
- **Refactor central (o grosso do E4-c):** os **8 escritores** de `espn_ref_value` passam a
  um **helper único** `set_espn_value` (store upsert **+** materializa a coluna),
  substituindo os `player.espn_ref_value = X` espalhados.
- **Leitores:** **só a badge PROV do cap_projector** é repontada (`ESPNValue`→store, join
  `player_id`→`sleeper_id`); **todos os demais leem a coluna materializada, inalterados**;
  a **engine nunca vira lookup** (pureza de graça).
- **Ordem (1-5), irreversível isolado:** (1) criar tabela, (2) backfill, (3) rotear
  escritores ao helper, (4) repontar badge — **todos reversíveis, sem downtime**; (5) DROP
  `ESPNValue` + generalizar `RookieEspnValue` — **irreversível-sem-backup, isolado no fim**.

**SUB-FATIAMENTO (E4-c vira guarda-chuva)**
- **[[E4-c-1]] — fundação (aditivo/reversível, agora):** passos 1-4. **Já entrega o store ao
  [[DP1]].** Backup antes do backfill; nada destrutivo; a coluna serve os leitores o tempo
  todo.
- **[[E4-c-2]] — limpeza (destrutivo/isolado, higiene):** passo 5. Sem leitor após o
  repontamento → pode esperar.

**DECISÕES DE ESCOPO (owner, pós-F1)**
1. **Season do backfill = 2026**, marcado **preliminar** (a tabela ESPN atual é prévia;
   serve 2026; o import definitivo futuro re-materializa).
2. **Linhas backfilladas:** `adjusted` autoritativo, `raw` **vazio** (não recuperável sem
   perda pelo floor), `is_final=False` (preliminares; o import definitivo completa).
3. **DST incluídas** no store como qualquer jogador (**não filtrar**) — seguem a mesma regra
   de cap/valor da liga. **F2 deve validar** que a chave do store funciona com o **sid de
   texto** das DST (`"IND"`,`"BUF"`…).
4. **Sequência:** **E4-c-1 agora** (constrói a fundação com o contexto fresco); **DP1 logo
   depois**, perto do draft; **E4-c-2 quando convier** (higiene).

**DEPENDÊNCIAS**
- Guarda-chuva de **[[E4-c-1]]/[[E4-c-2]]**. Fatia de **[[E4]]**. **[[E4-c-1]] habilita
  [[DP1]]**. Beneficia-se de **[[E4-b]]** (chave saneada — ✅).

---

### E4-c-2 — Store canônico: limpeza (drop ESPNValue + generalizar RookieEspnValue)
🔲 **Pendente** — Prioridade **Baixa (higiene; quando convier)** — fatia de **[[E4-c]]** (MAN-E4-c-F1) — **único passo destrutivo (irreversível-sem-backup)**

**ESCOPO** (passo 5 da ordem da F1)
- **Dropar `ESPNValue`** (vazio em prod → sem migração de linhas; após confirmar 0 leitores
  pós-repontamento da badge no E4-c-1).
- **Generalizar/retirar `RookieEspnValue`** — migrar suas linhas transitórias p/ o store
  canônico e aposentar a tabela.

**POR QUÊ ISOLADO**
- É o **único ponto irreversível-sem-backup**; sem leitor após o E4-c-1 → **higiene pura**,
  pode esperar. **Backup `/data/dynasty_*.db` antes.**

**DEPENDÊNCIAS**
- Fatia de **[[E4-c]]**. Depende de **[[E4-c-1]]** (badge já repontada). **Não bloqueia
  [[DP1]].**

---

### DP1 — Board de planejamento de cap pré-draft (rookies)
⚠️ **Implementado (F2) — validado em localhost; smoke em prod pendente** — Prioridade **a definir** — MAN-DP1-REG (08/06/2026) / F1 / F2 (10/06/2026) — **F1 ✅ diagnose read-only concluída** (achados absorvidos abaixo); **F2 ✅ board + simulação multi-pick no backend** (validado localhost: `salary_engine_test` 48/48 verde, smoke das rotas OK; ⚠️ → ✅ só após smoke em prod)

**CONTEXTO**
Owners precisam planejar o rookie draft contra o cap: avaliar drops, valorização de contratos
e picks sabendo o valor de referência ESPN dos rookies e o salário que cada um custaria se
draftado. Hoje isso não existe — exige planilha manual; é o gap que o Manager quer preencher.

**DESCRIÇÃO**
Um board que lista os **rookies entrantes** com `espn_ref_value` e o **salário projetado**
(`floor(ESPN×1.2)`), e permite ao owner **simular** o impacto no cap de draftar um rookie numa
pick. **Projeção, não pré-contrato** — o cap real só muda no draft (a simulação não cria
contrato vivo).

**DOMÍNIO / LOCALIZAÇÃO**
Cap (não fantasy points) → mora no **Manager** (cap_projector), acessível a todos os owners —
**não** no Optimizer (estatística, acesso restrito).

**REUSO (sem réplica)**
`floor(ESPN×1.2)` é fonte única no `salary_engine` (`year1_salary`) — reusar, **não** replicar
em JS/template (mesmo princípio do T2-FIX-2 / F10).

**Exemplo de uso:** owner da pick 1.1 avalia Jeremiyah Love (ESPN $46 → projeção ~$55) contra
o próprio cap.

**DEPENDÊNCIAS / FONTE DE DADOS (corrigida na F1/F2 — premissa do REG estava errada)**
- O DP1 **lê `RookieEspnValue` filtrada pela season entrante** (`get_current_season()+1`),
  **não** o store canônico via `espn_store_adjusted`. Motivo empírico: o backfill do
  `EspnValueStore` veio de `SELECT FROM players` (`app.py:390`), ou seja **só rosterados** —
  os rookies não-rosterados nunca entram no canônico hoje; ler o canônico devolveria board
  **vazio** de entrantes. **[[E4-c-2]]** (que subsumiria `RookieEspnValue` no canônico) **não
  bloqueia nem é pré-requisito do DP1** — quando rodar, o read vira troca de 1 linha
  (`rookie_espn_adjusted` → `espn_store_adjusted`). A premissa do REG ("DP1 lê o canônico")
  ficou **corrigida** aqui e na F1 (CORREÇÃO DE PREMISSA, abaixo).

**F1 — ACHADOS (diagnose read-only, MAN-DP1-F1, 09/06/2026; sem alteração de código/schema/DB)**

*Snapshot:* seed local `dynasty.db` está defasado — **não tem** as tabelas `rookie_espn_value`
nem `espn_value_store` (criadas aditivamente no boot via `db.create_all()`; o backfill de 273
linhas vive em **prod**). Logo a validação de **conteúdo** de linha é por código (caminhos de
escrita), não por contagem local; a análise estrutural independe disso.

**VEREDITO Q1 — cabe no modelo atual? → SIM.** Nenhuma nova representação de jogador
não-rosterado é necessária. `RookieEspnValue` (`models.py:448`) **já é** essa representação:
keyed por `(sleeper_id, season)`, deliberadamente **não-Player** (não polui roster/cap), e o
próprio docstring nomeia o DP1 como consumidor. O **stub-$1 segue rejeitado** pelos mesmos
motivos do E2-REFINE — `RookieEspnValue` existe precisamente como a alternativa não-stub; a
conclusão se mantém, não há motivo novo para revisá-la. O board, a simulação e o salário
projetado operam **sem nenhuma row de `player`** (ver Q3/Q4).

**CORREÇÃO DE PREMISSA (decisiva).** A premissa do prompt e a linha de DEPENDÊNCIAS acima
("DP1 lê o store canônico `espn_store_adjusted`") está **empiricamente incorreta para listar
entrantes no estado de hoje (E4-c-2 pendente)**. Evidência de caminho de escrita:
- O **único** escritor de `EspnValueStore` é `set_espn_value` (`models.py:551`), que **exige um
  objeto `player`** (materializa `player.espn_ref_value`). Todos os 8 chamadores passam um
  `Player` existente → o store canônico (273 linhas) contém **só rosterados**.
- Os **entrantes não-rosterados** entram por `_resolve_not_found_to_store` (`admin.py:582`) →
  `upsert_rookie_espn` → **`RookieEspnValue`**, nunca em `EspnValueStore` (não há Player).
- Confirma o achado E4-F1 (linha ~1729): "`RookieEspnValue` é transitória e **complementar** —
  cobre o vão pré-roster que as outras não cobrem".
→ **DP1-F2 deve ler `RookieEspnValue` (`rookie_espn_adjusted` + query por season), NÃO
`espn_store_adjusted`.** Ler só o canônico hoje renderiza board **vazio** de entrantes. A frase
"lê o canônico" é **aspiracional (pós-E4-c-2)**, quando o `RookieEspnValue` for subsumido no
store. Isto é o que faz "E4-c-2 não bloqueia DP1" ser verdadeiro: o DP1 lê a fonte transitória
direto; quando E4-c-2 migrar as linhas, o read vira troca de 1 linha (`rookie_espn_adjusted` →
`espn_store_adjusted`, ambos `adjusted` por sid+season).

**Q2 — fonte da lista de entrantes.** Autoritativa = **`RookieEspnValue` filtrada por `season`**
(alvo = `get_current_season()+1`). O **critério que separa entrante de veterano/FA já está
embutido na construção da tabela**: ela só recebe entradas ESPN `not_found` (sem Player),
skill (K/DST excluídos), valor>0, resolvidas a um `sid` **único** (Brown-safe,
`_resolve_entry_sid` `admin.py:566`). O filtro de season é confiável (coluna + `uq(sid,season)`).
*Janela de dados:* import ESPN → **limpa no fim do rookie draft** (`clear_rookie_espn_store`,
`offseason.py:716`) — exatamente a janela de planejamento pré-draft que o DP1 serve; fora dela o
board é vazio por design. *Nuance:* semanticamente é "entrante ESPN-valorado não-rosterado" (a
classe de rookies + eventual FA não-rosterado no sheet), não estritamente "rookie".
*Gap menor (read-only, sem schema):* não há helper "listar todos os rookies da season" — só o
single `rookie_espn_adjusted`; F2 adiciona uma query `RookieEspnValue.query.filter_by(season=…)`
(leitura, não modelo).

**Q3 — salário projetado `floor(ESPN×1.2)`: fonte única confirmada, SEM réplica.** Canônico =
`salary_engine.year1_salary("rookie_draft", 0, espn_adj)` (`salary_engine.py:63`; rookie →
`_floor(espn_adj)`). O `×1.2` é aplicado na **escrita** do store (`espn_adjusted = raw×1.2`); o
`floor` no `year1_salary`. O board invoca **exatamente como o `draft_import.py:135` já faz**:
`year1_salary("rookie_draft", 0, rookie_espn_adjusted(sid, season))` — `rookie_espn_adjusted` lê
por sid, **sem row de Player**. Consumidores de `year1_salary`/`floor(ESPN×1.2)`: `draft_import`
(135/143/149/259), `record_acquisition` (`models.py:386`), `/api/salary/calculate`
(`full_contract_table`). **Nenhuma réplica JS/template do cálculo de salário** — as strings
`floor(ESPN×1.2)` em `salary.html`/`auction.html` são **texto de ajuda**, não cálculo; o `×1.2`
em `salary.py:46`/`admin.py:173` é a conversão raw→adjusted na entrada (padrão canônico), não
réplica do floor.

**Q4 — simulação de cap: infra reaproveitável + RÉPLICA JS confirmada (débito F10).** Canônico =
`salary_engine.draft_budget(team_players)` (puro: lista de players → dict de budget). O endpoint
`/api/cap_projector/<team>` (`salary.py:64`) já devolve `budget` + `next_salary` por jogador.
**Réplica JS confirmada:** `cap_projector.html` `updateSummary()` (linhas 142-176) **reimplementa
em JS** a agregação de budget (total, remaining, usable, spots, min $1/spot, avisos over-cap) —
duplica `draft_budget()`. É o débito que o F10/T2-FIX-2 sinaliza ("`draft_budget` já replicado em
JS no cap_projector"). A simulação "draftar este rookie → cap fica assim" = somar o
`projected_salary` do rookie ao total dos mantidos e recalcular budget; **se feita em JS encosta
nessa réplica**. Caminho limpo: estender o **backend** a aceitar um salário hipotético e
devolver `draft_budget` (evita ampliar a réplica) — decisão de F2. `draft_budget` lê só
`p.salary`/`p.is_dropped`; o rookie hipotético entra como "+salário", **sem precisar de Player**.

**Q5 — encaixe de tela + acesso.** Mora em **`cap_projector`** (`salary_bp`, rota `/cap_projector`
`salary.py:19`, template `cap_projector.html`) — nova seção/aba na página existente. Acesso:
`@login_required` **apenas**, **sem `@admin_required`** → todos os owners. Time do owner =
`current_user.team_rel` (precedente M17), **já cabeado** em `salary.py:25-27` (pré-seleciona
`my_team`). A simulação reusa o `teamData` já carregado (mantidos do owner) + salário do rookie.
*Pick é só contexto de UX:* a regra 8.2.7 (`year1_salary` rookie) **não depende da pick** — o cap
delta é o salário projetado independentemente do slot; mostrar "suas picks" (modelo `Pick`) é
enriquecimento opcional, não requisito do cálculo.

**ESCOPO PROPOSTO PARA O F2 (a confirmar antes de gerar prompt de IMPL):**
1. Read source = **`RookieEspnValue` por season** (NÃO `espn_store_adjusted`) — +1 query de lista.
2. Salário = `year1_salary("rookie_draft", 0, rookie_espn_adjusted(...))` — fonte única, reuso.
3. Simulação = estender backend p/ budget com salário hipotético (não ampliar a réplica JS).
4. Tela = nova seção em `cap_projector.html`; acesso `@login_required`; time via `current_user`.
5. Réplicas encontradas: **1** — agregação de budget em JS (`updateSummary`, débito F10).
   Salário: **0** réplicas. Decisão de modelo: **cabe no atual, sem nova representação**.

**F2 — IMPLEMENTADO (MAN-DP1-F2, 10/06/2026)** — ⚠️ validado em localhost; smoke em prod pendente.

Board entregue como **nova seção em `cap_projector.html`** ("🏈 Planejamento de Rookie Draft"),
abaixo do projetor existente. Dois endpoints novos em `routes/salary.py` (ambos `@login_required`,
sem admin gate):
- `GET /api/cap_projector/rookies` — lista os entrantes da season-alvo de **`RookieEspnValue`**
  (ordenado por valor), cada um com ESPN ref (raw) e `projected_salary` via
  `year1_salary("rookie_draft", 0, espn_adjusted)` — **fonte única, sem row de Player, sem réplica**
  (mesma invocação do `draft_import.py`).
- `POST /api/cap_projector/simulate` — recebe `{rookie_sids: [...]}`, calcula o budget do cenário
  **no backend** via `draft_budget()` canônico: roster ativo do `current_user.team_rel` (M17, cap
  atual) + os rookies do cenário como "+salário" (objeto transitório em memória — **sem
  materializar Player**, stub-$1 segue rejeitado). Cenário vazio → budget atual, idêntico ao
  `/api/cap_projector`.

**Simulação no backend (não amplia o F10):** a réplica JS de budget (`updateSummary`) ficou
**intocada**; a nova seção lê `keeper_salaries`/`usable_draft_budget` direto da resposta do
backend — **nenhuma agregação de cap em JS** e **0 réplica nova de `×1.2`** no template (grep
confirmado). O F10 (deduplicar `updateSummary`) segue sendo trabalho próprio, fora deste escopo.

**Fora de escopo (explícito):** **persistência de cenário** ("salvar meu plano de draft") — o
cenário vive só no cliente durante a sessão; nada é escrito (validado: `RookieEspnValue` e o cap
do time inalterados após simular). Seria item próprio se priorizado. **Pick é só contexto de UX**:
a regra 8.2.7 não depende do slot, então o board não modela picks (enriquecimento opcional futuro).

**Validação localhost (10/06/2026):** `salary_engine_test.py` 48/48 verde; smoke via test client
(usuário não-admin logado): `GET /cap_projector` 200; rookies de `RookieEspnValue` (canônico vazio
no DB — confirma fonte correta); spot-check `$46→$55` e `$3→$3`; cenário 2 picks → soma `+$58` no
backend; cenário vazio → budget atual sem alteração; nada escrito (store + cap intactos). **Falta:**
smoke em prod (depende de import ESPN da season popular `RookieEspnValue`) → manter ⚠️ até lá.

---

### MAN-METH-REG — Candidato a baseline do DEV_METHODOLOGY: F1 refuta premissas do prompt contra o código
🔲 **Registrado 10/06/2026** — MAN-METH-REG (**registro apenas** — não altera código nem o
`DEV_METHODOLOGY.md`) — **candidato a baseline, NÃO regra vigente** — destino: **consolidação no
`DEV_METHODOLOGY.md` em sessão de revisão de metodologia dedicada** (transversal manager / optimizer
/ predictor).

**Lição transversal de processo** que emergiu duas vezes: a **especificação positiva** de um prompt
(descrever só o que se quer que apareça/aconteça) **omite por silêncio** o que está errado ou vai se
perder. O gap "o que o prompt assume × o que o código diz" e "o que existe hoje × o que a proposta
descreve" só aparece se a F1 for **obrigada a olhá-lo** — não cai das perguntas da diagnose.

**REGRA CANDIDATA (forma a refinar na consolidação):**
> Toda **F1 de consumo/refatoração** (item que **lê** ou **reusa** infra existente) deve listar
> explicitamente, **com evidência do código atual**: (a) as **premissas embutidas no prompt que o
> código contradiz**, e (b) os **campos/comportamentos existentes hoje ausentes na especificação
> proposta** — cada item com **parecer**: `premissa falsa` / `remoção intencional` /
> `perda não-intencional` / `deslocamento`. Não basta responder às perguntas da diagnose; o gap
> assumido×real e existe×proposto é entregável próprio da F1.

**OCORRÊNCIAS QUE SUSTENTAM (mesma família — omissão por silêncio):**
- **[[DP1]]-F1 (09–10/06/2026) — premissa de fonte falsa.** O prompt partiu de "o board lê o store
  canônico via `espn_store_adjusted`", repetida em `improvements.md` e no handoff como fato
  assentado. A F1 **refutou contra o código**: o canônico só contém rosterados (backfill de
  `SELECT FROM players`, `app.py:390`); os entrantes vivem em `RookieEspnValue`. **Seguir a premissa
  teria entregue board vazio em produção.** Foi a refutação da premissa — não a resposta às
  perguntas — que salvou o item.
- **[[UX4-b]] (24/04/2026) — campo existente omitido.** Refatoração de UI especificou o design
  positivo (o que deveria aparecer) mas não listou os campos presentes hoje que **sumiriam** no
  design proposto (ESPN + Projeção no roster). Registrado na época como candidato a baseline; **esta
  entrada absorve e generaliza** aquela nota metodológica (origem em UX4-b, ver seção UX4-b).
- **AUD1-F1 pré-execução (11/06/2026) — premissas do próprio prompt refutadas antes do escopo.**
  O prompt MAN-AUD1-F1 afirmou "JS estático" (falso — `static/` só tem CSS; todo JS é inline nos
  templates) e citou "regra MAN-O2" (inexistente — a regra de absorção imediata é do
  DEV_METHODOLOGY; MAN-O2-REFINE é precedente de refinamento documental, outra coisa). Ambas
  refutadas contra código/docs na análise pré-implementação, **antes de aceitar o escopo** — o
  comportamento que esta regra quer tornar obrigatório, demonstrado espontaneamente e confirmado
  como barato (2 greps). Terceira ocorrência da família.

DP1 = premissa de leitura falsa; UX4-b = campo existente omitido. Ambos só visíveis ao olhar o gap
(assumido × real, existe × proposto) — daí a regra única.

**Relaciona-se a** [[validate_prompt_premises_empirically]] (checar empiricamente premissas críticas
do prompt antes do IMPL) e ao princípio de fonte única (T2-FIX-2 / [[F10]]): a refutação da premissa
na F1 é o momento barato de pegar o gap, antes de o IMPL nascer sobre uma base falsa.

---

### F11 — Rollover de season duplicado e divergente (admin × offseason)
⚠️ **12/06/2026** (prod verificado limpo; fix Opção A validado localhost — ✅ após smoke em prod) —
registrado 11/06/2026, achado AUD1 Lente 2 — Prioridade **Alta**

**Evidência:** dois endpoints aplicam o rollover, ambos vivos na UI: (1) `/api/admin/rollover/apply`
(routes/admin.py:89-130; botão "⚡ Aplicar Rollover" em admin.html:285) e (2) `/api/offseason/rollover`
(routes/offseason.py:653-697; Step 4 do workflow, offseason.html:724). Divergências do lado admin:
**sem gate de etapas** (offseason exige steps 2+3), **sem check `rollover_done`** (re-execução livre),
**não avança `current_season`** nem seta flags — grava SalaryHistory com `season=next_season` deixando
a config da season para trás (estado inconsistente). Comentário stale em admin.py:122-123 afirma
"CURRENT_SEASON in models is a constant — in production you'd persist this in a Settings table",
contradito pelo código atual (`AppConfig.current_season` + `set_config`, usados pelo fluxo offseason).
**Risco:** rodar o rollover do admin após o do offseason (ou 2× o do admin) **incrementa contratos e
salários duas vezes** — corrupção em massa de dados calculados, sem reversão fácil.
**Parecer:** item novo. Proposta: matar a réplica (admin delega ao endpoint canônico do offseason, ou
remove o botão), à la T2-FIX-2/"1 fonte por caminho de escrita". F1 dispensável — diagnose acima já
cobre causa e evidência; F2 direto.

**Etapa 1 — verificação retroativa em prod (12/06/2026): VEREDITO LIMPO.** Queries read-only
executadas pelo owner no Render Shell contra `/data/dynasty.db` (`sqlite3 -readonly`). Números:
**`salary_history` = 0 linhas** (nenhum rollover jamais aplicado em prod — contratos vivos vieram do
CSV bootstrap, que não gera history; classe F12); **0 lotes** de rollover por season (Q2 vazia);
**0 duplicatas** (player, season) com regra de rollover (Q3); **0 assinaturas** `"Season rollover"` no
`sync_log` (Q4 — o botão admin **nunca foi usado**; assinatura exclusiva do caminho admin, que gravava
SyncLog; o offseason não grava); **0 players** ativos com contract_year fora de 1..4 (Q5); config
consistente: `current_season=2025`, `rollover_done=false`, `season_locked=true` — offseason 2026 em
andamento, rollover legitimamente pendente no Step 4. **Sem corrupção; janela de risco estava aberta**
(1º rollover da história da liga é iminente) — fix urgente, repair desnecessário.

**Etapa 2 — fix Opção A (12/06/2026, ⚠️ localhost):** removidos o endpoint `POST /api/admin/rollover/apply`
(routes/admin.py — substituído por comentário-guard apontando a porta única), o botão "⚡ Aplicar
Rollover" + `confirmRollover()` + `#rollover-result` (admin.html), e o comentário stale (vivia dentro
do endpoint removido). **Preview mantido** (`GET /api/admin/rollover/preview` + card "Season Rollover
(preview)"): read-only, usa só a função pura `apply_season_rollover`, zero dependência do caminho
removido; card e step-list do admin agora apontam o apply para o workflow do Offseason (Step 4).
Offseason intocado (gates/flags/semântica idênticos — git diff não toca offseason.py/offseason.html).
**Validação:** grep pós-fix = exatamente 1 caminho de escrita (offseason.py:675-683; models.py:396 é
record_acquisition ano-1, admin.py:882 é edição per-player M2); 0 referências a `rollover/apply`/
`confirmRollover`; Jinja parse OK; `salary_engine_test.py` 48/48. **✅ após smoke em prod:** deploy +
admin sem botão (preview funcional) + offseason Step 4 intacto.

---

### F12 — `run_import` sobrescreve salary/contract a cada boot local, sem history
🔲 **Registrado 11/06/2026** — achado AUD1 Lente 2 — Prioridade **Média** (dev local; prod safe)

**Evidência:** import_csv.py:110-112 — para player existente, `player.salary = salary` +
`player.contract_year = cyr` **incondicionalmente** a cada `run_import()` (todo boot com CSV
presente, app.py:60), **sem criar SalaryHistory**. O guard `f8_rebuilt` (import_csv.py:61-63)
protege só `acquisition_type`/`contract_start_season`. A coluna lida é `salary_2025` (hardcoded,
import_csv.py:90) — snapshot estático de 2025. Em prod o CSV não existe (não está no git) → skip
(WARNING, import_csv.py:54-56). **Risco:** em dev local, rollover/correções feitos in-app são
silenciosamente revertidos ao snapshot 2025 no próximo boot, sem trilha — explica/agrava o
"dynasty.db local diverge do repo" e cria falsos negativos em testes locais de rollover.
**Parecer:** item novo. Candidatos de fix (decidir em F2): guard tipo `csv_imported` one-shot,
ou skip de salary/cyr quando `f8_rebuilt`/flag equivalente — manter CSV como bootstrap, não como
autoridade contínua. Atualizar CLAUDE.md junto ("first run auto-imports" hoje não descreve o código).

---

### E4-d — Matching frouxo nas portas do /auction (single-entry + Excel)
🔲 **Registrado 11/06/2026** — achado AUD1 Lente 4 — Prioridade **Baixa/Média** — família [[E4]]

**Evidência:** (1) single-entry FA/rookie: `Player.name.ilike(player_name)` sem wildcard
(auction.py:50 e 91) — exato case-insensitive, sem resolução nome+team→sid (resolver E4-a/E4-b
existe e não é usado aqui); grafia divergente do Sleeper cria **órfão-duplicata** (classe E4-b, cujo
guard cobriu só import_csv). (2) upload Excel: `Team.name.ilike(f"%{team_name}%")` (auction.py:219) —
**substring** em nome de time; colisão entre times que compartilham palavra atribui contrato ao time
errado. **Parecer:** item novo na família E4 (identidade na porta de aquisição): aplicar o resolver
sid na entrada manual (mesma régua do import) + match exato/escolha explícita para times no Excel.

---

### M19 — Validação de pesos do lottery existe só no client
🔲 **Registrado 11/06/2026** — achado AUD1 Lente 1 — Prioridade **Baixa**

**Evidência:** JS valida peso (inteiro ≥1 via floor, offseason.html:391-405, M15-FIX); o backend
`_normalize_weights` (offseason.py:39-43) só faz `{int(k): float(v)}` — aceita 0, negativo e float
— e `_draw_weighted_lottery` faz `int(weight)` (offseason.py:72): peso ≤0 ou <1 → time
**silenciosamente excluído do pool**. POST direto em `/api/offseason/run_lottery` bypassa o JS.
Mitigantes: `@admin_required` + audit M8 grava weights/pool (detectável a posteriori).
**Parecer:** item novo — espelhar a validação no server (rejeitar peso inválido com 400), mantendo a
fórmula de render no client (decisão M15-FIX preservada).

---

### M20 — Descomissionar write-side da flag single-user (`is_my_team` + constantes)
🔲 **Registrado 11/06/2026** — achado AUD1 Lente 3 — Prioridade **Baixa** — **BLOQUEADO: depende de
[[M17]], que segue ⚠️ aguardando smoke em prod (import ESPN real). Só destrava quando M17 marcar ✅.**

**Evidência:** consumidores user-facing migrados pelo M17 (verificado: roster.html sem flag;
league/team_detail derivam de `current_user`; fonte única `inject_user_team` app.py:115-121), mas o
ciclo de vida da flag segue inteiro: sync **escreve** `team.is_my_team` via `MY_OWNER_ID`
(sync_sleeper.py:161,170) e propaga em moves/trades (254, 275, 593); `record_acquisition` propaga
(models.py:368,380); `bulk_register` propaga (auction.py:145); colunas Team/Player + `to_dict`
(models.py:89,115,137,191); `check_team.py:6` consulta a flag; mapeamento de standings usa
`MY_OWNER_ID`/`MY_TEAM_NAME` (offseason.py:312-313). **Risco:** superfície futura consumir a flag
"viva e correta" por engano, reintroduzindo a classe M17. Fora do escopo original do M17 (F1 mapeou
só consumidores) → ID próprio. **Parecer:** item novo — após M17 ✅ em prod: remover escrita/propagação,
deprecar colunas (manter no schema por compat até migração), migrar check_team.py e o mapeamento de
standings.

---

### DOC1 — CLAUDE.md "App Startup Sequence" desatualizada (docs-only)
🔲 **Registrado 11/06/2026** — achado AUD1 Lente 6 — Prioridade **Média** (blast radius: doc carregada em toda sessão do Code)

**Evidência:** CLAUDE.md lista 10 passos com `init_auth` (8) antes de `run_sync` (9) e
`_backfill_player_history` (10) incondicionais. Código real (app.py): `run_import` (60) →
**`run_sync` e backfill SÓ se `fresh_import`** (app.py:61-82; backfill ainda atrás do guard
`f8_rebuilt`) → context processors → `init_auth` **por último** (app.py:138). **Risco:** sessão
futura assume "sync roda em todo boot" e mis-diagnostica dados stale (premissa falsa classe DP1-F1
no doc de maior propagação). **Parecer:** doc desatualizado → docs-only fix no CLAUDE.md (reescrever
a sequência refletindo condicionalidade e ordem reais). Sem F1 — evidência acima é a diagnose.

---

### MAN-ESPN12 — Onde o fator ×1.2 do ESPN é aplicado (diagnose read-only)
🔲 **F1 registrada 10/06/2026** — MAN-ESPN12-F1 (**diagnose read-only; nada alterado**) —
nenhum item marcado resolvido. Veredito da suspeita central (réplica ×1.2 no client): **negativo**.

**Pergunta-mãe:** o fator ×1.2 (reg. 8.2.7, `floor(ESPN_raw×1.2)`) está replicado fora do backend
(JS/template), violando "single source per render mode"?

**ACHADOS (evidência concreta):**

1. **Onde o ×1.2 é aplicado (backend).** É a conversão de fronteira **raw→adjusted**, aplicada no
   **momento da escrita/entrada**, sempre em Python. **5 sítios** fazem a multiplicação:
   - `espn_pdf_parser.py:129` — `max(1.0, float(int(espn_raw*1.2)))` (import PDF; **com floor**).
   - `routes/admin.py:173` — `set_espn_value(..., espn_raw*1.2, raw=...)` (CSV bulk `/api/admin/espn_bulk`).
   - `routes/auction.py:46,88,136` — `espn_adjusted = espn_raw*1.2` (registro FA/rookie no `/auction`).
   - `routes/salary.py:46` — `espn_adj = espn_raw*1.2` (calculadora `/api/salary/calculate`).
   - `routes/salary.py:280,285,288` — `espn_raw*1.2` (`/api/espn_values/update`, store + log legado).
   O **floor** (adjusted→salário) é separado e **fonte única** em `salary_engine.year1_salary`,
   invocado pela porta canônica `record_acquisition`.

2. **Réplica em JS/template? → NÃO (achado central).** O grep de multiplicação real (`* 1.2` /
   `1.2 *`) retorna **9 hits, todos Python; 0 em template/JS** (não há `.js` separado — todo JS é
   inline nos templates; `static/` só tem CSS). Os `×1.2`/`x1.2` em templates são **texto de ajuda**
   (`auction.html:92`, `salary.html:66/72/78/84`, `admin.html:117`, `espn_import.html:92`) ou
   **rótulo de exibição** (`salary.html:112`: `"$<raw> × 1.2 = $<adjusted>"`, onde **ambos** os
   números vêm do servidor — `espn_adjusted` é computado em `salary.py:46` e a tabela de contrato em
   `full_contract_table`). **Nenhum cálculo no client.**

3. **Origem do valor exibido.** Sempre o valor **computado em Python e servido**. Telas que mostram
   ESPN exibem colunas/campos já gravados (`Player.espn_ref_value`, `espn_raw`/`espn_adjusted` do
   parser/store) ou o retorno da API — **nunca recalculam** a partir do raw. Invariante **preservada**.

4. **Dupla aplicação / omissão.** **Nenhuma dupla aplicação** numa mesma cadeia: cada caminho de
   escrita aplica ×1.2 **uma vez**; o confirm do PDF (`admin.py` → `_save_espn_value`) grava o
   `espn_adjusted` **já produzido pelo parser** (não re-multiplica); a engine **espera adjusted e não
   re-multiplica** (regressão guardada por `salary_engine_test.py:275` — bug histórico de "double
   ×1.2" → $39, hoje $35). **Sem omissão** no caminho de salário (floor via `year1_salary`).

**ACHADOS SECUNDÁRIOS (não são a violação suspeitada, mas reais):**
- **(a) ×1.2 duplicado entre 5 sítios Python** — é débito de **fonte única _no backend_** (constante
  mágica `1.2` + conversão raw→adjusted espalhada por parser + 4 rotas; não há helper único tipo
  `adjust_espn(raw)`). **Distinto** da invariante de render-mode (essa está OK) — é o mesmo espírito
  do [[F10]] aplicado dentro do Python. Risco baixo hoje, mas qualquer mudança no fator toca 5 lugares.
- **(b) Definição divergente de "adjusted" entre caminhos de escrita.** O parser PDF **floora**
  (`int(raw×1.2)` → 55) enquanto os outros 4 sítios gravam o **produto não-floorado** (`raw×1.2` →
  55.2). Mesmo raw → `espn_adjusted`/`espn_ref_value` gravado **55 vs 55.2**. O **salário é idêntico**
  (year1 floora de novo), mas a **valorização** (`0.5×`, `0.8×`) pode divergir **$1** em borda, e a
  **exibição** do adjusted difere. Inconsistência de definição do canônico.
- **(c) Rótulo "ESPN" mistura raw e adjusted na mesma tela.** No `cap_projector`, a coluna "ESPN Ref"
  mostra `espn_ref_value` = **adjusted** para rosterados (`cap_projector.html:158`) e, no board DP1,
  `espn_raw` = **raw** para rookies (`:262`) — **mesmo rótulo, bases diferentes**. Mais amplo:
  formulários de input e o board tratam "ESPN" como raw; telas de roster mostram adjusted. Divergência
  de **exibição** (não de cálculo).

**JUSTIFICA F2?** A suspeita original (réplica no client) **não se confirma** → não há correção
urgente de invariante. Há **débito real** (a/b/c) que pode virar F2 **opcional, baixa prioridade**:
- Escopo mínimo: **centralizar a conversão** num helper único (ex.: `salary_engine.adjust_espn(raw)` —
  com decisão explícita floor× não-floor, fechando (a)+(b)) e **reponteirar os 5 sítios** para ele.
- Escopo opcional: **uniformizar o rótulo "ESPN"** (raw vs adjusted) nas telas (c) — decisão de UX.
Decisão aguarda o owner; **nada implementado nesta fase**.

---

## Offseason 2026 — pacote OFF26 (cuts selados + ligas fantasmas)
🔲 **Registrado 05/06/2026** — MAN-OFF26-REG (registro apenas; nenhuma implementação)

**Contexto do pacote (sessão com o comissário, 05/06/2026):** o formato da liga
(keeper + dynasty + salary cap) não cabe nativamente no Sleeper e a API do Sleeper
é **read-only** — não há como escrever salários/configuração via API. Decisão: o
Sleeper mantém o que faz bem (salas de lance ao vivo, via **ligas fantasmas** —
rookie draft em draft linear e FA Auction em draft auction), e o **Manager** assume
todo o ciclo de decisão e registro (declaração selada de keepers/cuts, keeper sheet,
auditoria da config da liga fantasma, import dos resultados dos drafts). A
transcrição da keeper sheet para o Sleeper é feita via **Cowork + Claude in Chrome**
(procedimento operacional supervisionado, fora do código do Manager).

**Dependências do pacote:** OFF26-1 → OFF26-2 → OFF26-4; OFF26-3 independente e
paralelizável; OFF26-5 é documentação (depende conceitualmente de 2 e 4).
**Prioridades abaixo são triagem inicial — o comissário re-prioriza.**
**Próximos candidatos naturais de F1 (sessões separadas):** OFF26-1 e OFF26-3.

---

### OFF26-1 — Janela de keepers/cuts selada
🔲 **Pendente** — Prioridade **Alta**

**Descrição:** cada owner autenticado vê **apenas o próprio roster** e declara
keepers/cuts no Manager, com budget resultante (`$200 − keepers`) calculado ao vivo
e validação do regulamento (mínimo $1 por slot vazio, item 8.3.4). Declarações
editáveis até o deadline; **sigilo total pré-deadline, inclusive para admins** (que
também são owners); **lock + revelação simultânea** no deadline.

**Motivação:** hoje os cortes acontecem sequencialmente e em público no Sleeper,
vazando informação entre owners (quem corta por último vê o que já foi liberado). A
janela selada elimina o vazamento.

**Escopo resumido:** declaração privada por owner + cálculo de budget ao vivo +
validação 8.3.4 + deadline com lock e revelação simultânea + trilha auditável no
padrão do M8 (lottery audit). Sigilo aplicado mesmo a admins.

**Dependências:** nenhuma. É a **fonte** dos itens OFF26-2 e OFF26-4.

---

### OFF26-2 — Keeper sheet exportável
🔲 **Pendente** — Prioridade **Alta**

**Descrição:** relatório por time gerado a partir da revelação do OFF26-1 — keepers,
salários e budget resultante para o FA Auction.

**Motivação:** é o **insumo** que o Cowork transcreve para a liga fantasma; sem ele,
a transcrição não tem fonte de verdade.

**Escopo resumido:** exportar, por time, a lista de keepers + salário + budget de FA,
derivada da revelação selada.

**Dependências:** depende do **OFF26-1**.

---

### OFF26-4 — Auditoria de keepers pré-leilão
🔲 **Pendente** — Prioridade **Média**

**Descrição:** após a transcrição via Cowork, compara a keeper sheet (OFF26-2) com a
configuração **real** da liga fantasma lida via API read-only, reportando diffs
(keeper ausente, salário divergente, time errado) **antes** do início do leilão.

**Motivação:** a transcrição manual é o ponto de falha; a auditoria pega divergências
antes que o leilão comece sobre uma configuração errada.

**Escopo resumido:** ler config da liga fantasma via API read-only; diff contra a
keeper sheet; relatório de divergências como gate pré-leilão.

**Dependências:** depende de **OFF26-1** e **OFF26-2**.

---

### OFF26-5 — Runbook do procedimento Cowork
🔲 **Pendente** — Prioridade **Média** — **item de documentação (não é código)**

**Descrição:** passo a passo operacional da transcrição supervisionada da keeper
sheet para a liga fantasma via **Cowork + Claude in Chrome**, incluindo pré-requisitos
de acesso (sessão do comissário detentor dos direitos no Sleeper, ou co-comissário),
gravação do workflow na primeira execução para reuso anual, e o gatilho da auditoria
(OFF26-4) ao término.

**Motivação:** o procedimento é supervisionado e anual; um runbook torna-o
reproduzível e reduz dependência de memória entre temporadas.

**Escopo resumido:** documento de runbook (pré-requisitos de acesso → gravação do
workflow → execução → gatilho da auditoria OFF26-4).

**Dependências:** documentação; depende conceitualmente de **OFF26-2** e **OFF26-4**
para fazer sentido completo.

---

### F9 — `bulk_register` cria jogadores sem SalaryHistory
🔲 **Pendente** — Prioridade **Alta** — achado lateral de [[MAN-OFF26-3-F1]] (registrado 05/06/2026)

**Descrição:** o endpoint `POST /api/auction/bulk` (`routes/auction.py:187`
`bulk_register`) cria/atualiza `Player` + `AuctionLog` mas **não grava
`SalaryHistory`** — diferente dos demais caminhos de aquisição (`register_fa_auction`,
`register_rookie`, `upload_excel`), que sempre gravam o histórico. O código ainda
contém um hack inerte (`_noop` + `test_request_context`) sem efeito.

**Motivação:** jogadores registrados em massa ficam sem o registro de histórico
salarial correspondente — inconsistência silenciosa entre `Player.salary` e a
timeline de `SalaryHistory` (que alimenta `/salary_history` e auditorias). É **dano
potencial já existente**, não hipotético, daí prioridade Alta.

**Exige F1 próprio antes do fix** (avaliação de dano), respondendo:
- A rota `bulk_register` foi efetivamente usada em produção?
- Existem hoje jogadores sem `SalaryHistory` decorrentes dela (e quantos)?
- Qual o dano acumulado, se houver, e ele precisa de backfill corretivo?

**Escopo do fix (após o F1):** fazer `bulk_register` passar pelo mesmo caminho
atômico de aquisição dos demais (idealmente o helper canônico criado no F2 do
OFF26-3) + remover o hack `_noop`; eventual backfill dos órfãos conforme o F1.

**Ref. cruzada:** [[MAN-OFF26-3-F1]] (diagnose do importador OFF26-3, achado §3).

#### Fase 1 Diagnose ✅ (05/06/2026) — MAN-F9-F1 (avaliação de dano)
Read-only. Auditoria SQL direta do `dynasty.db` local (representante de produção;
sem subir o app, p/ não acionar `import_csv` no boot). **Achado que reformula o F9.**

**Estado do banco auditado:** `players`=280 (todos ativos), `player_history`=1132,
mas **`salary_history`=0 linhas** e **`auction_log`=0 linhas** (ambas VAZIAS).

- **§1 — Usado em produção? → NÃO há evidência.** `auction_log` está vazio → nenhum
  caminho do fluxo de auction (bulk_register OU os demais) deixou rastro neste DB.
  **Ressalva:** este é o *seed commitado*; o disco persistente do Render (não
  acessível daqui) é a fonte autoritativa de uso ao vivo. Se houver dúvida, **puxar
  o `dynasty.db` de produção** e re-rodar esta auditoria.
- **§2 — Órfãos:** atribuíveis ao bulk_register (fingerprint = `AuctionLog` sem
  `SalaryHistory` irmã por player+season) = **0** (auction_log vazio → lista nominal
  vazia). **Baseline:** 280 players ativos sem nenhuma `SalaryHistory` — mas isso é
  **condição global do DB** (tabela `salary_history` vazia), **não dano do
  bulk_register**: os 280 vêm de `import_csv.py:98` (import do CSV) + sync de roster
  (`sync_sleeper.py:262`), que setam `Player.salary` direto e **não escrevem
  salary_history** (por design — salary_history é camada de aquisição/auditoria).
  Lista completa reproduzível pela query de auditoria; origem = startup 2024 / draft
  2025 / FA, todos via CSV+sync.
- **§3 — Impacto a jusante: o rollover NÃO depende de salary_history.**
  `apply_season_rollover` (salary_engine.py:190-213) lê **`player.salary`** (prev) +
  **`player.espn_ref_value`** — não consulta `salary_history`. Logo os órfãos
  **rolam corretamente** (VALORIZAÇÃO usa Player.salary). **A premissa do prompt
  ("rollover calcula VALORIZAÇÃO a partir do histórico salarial") está refutada
  empiricamente.** Impacto real dos órfãos = **display/auditoria**: `/salary_history`
  mostra timeline vazia e a narrativa de contrato fica incompleta; cálculo de cap usa
  Player.salary (ok).
- **§4 — Réplicas (SIM):** criação de Player **sem** salary_history existe em mais
  de um lugar — `import_csv.py:98` (bulk do CSV) e `sync_sleeper.py:262` (sync de
  roster). Ambos **por design** (membership/seed; salary é Player.salary). O
  `bulk_register` (`routes/auction.py:141`) é o único que cria via **fluxo de
  aquisição** sem salary_history — inconsistente com os irmãos do `/auction`
  (que via `record_acquisition` gravam Player+SalaryHistory+AuctionLog). `admin
  espn_bulk` (admin.py:144) não cria player (atualiza ESPN). Fonte canônica de
  aquisição = `models.record_acquisition` (OFF26-3-F2).
- **§5 — Escopo recomendado do F2: REFATORAÇÃO APENAS** (no estado auditado).
  Como o dano atribuível = 0, F2 do F9 = rotear `bulk_register` pelo
  `record_acquisition` + remover o hack `_noop`/`test_request_context`. **Sem
  backfill** necessário aqui. **Condicional:** confirmar o `dynasty.db` de produção
  ao vivo; SE lá houver `auction_log` de bulk_register sem `SalaryHistory`, esses
  casos são **100% reconstruíveis** a partir do próprio `AuctionLog` (player_id +
  season + value_paid + espn_ref_value_at_time + entry_type → `year1_salary`
  recompõe a SalaryHistory). Nada se perde irrecuperavelmente, pois o bulk_register
  *grava* AuctionLog (só omite SalaryHistory).

**Observação fora do escopo do F9 (candidata a item próprio):** o seed `dynasty.db`
não tem **nenhuma** `salary_history` (0 linhas) — `/salary_history` ficaria vazio p/
todos. Pode ser esperado (seed reconstruído via CSV+chain, sem a camada de aquisição)
ou indicar que o backfill histórico de salary_history nunca foi semeado. Confirmar
contra o disco de prod; se prod também estiver vazio, avaliar um item de **backfill
de salary_history do roster** (separado do F9).

**Não iniciar F2.** Status do F9 permanece 🔲.

#### Fase 1B ✅ (07/06/2026) — MAN-F9-F1B (re-auditoria contra produção)
Cópia do `dynasty.db` de produção fornecida pelo comissário (`integrity_check: ok`).
**As conclusões condicionais da F1 viram definitivas:**

| Contagem | seed (git) | **produção** |
|---|---|---|
| players (total) | 280 | 280 |
| players ativos | 280 | **277** (3 dropados: Emari Demercado, Kareem Hunt, Nick Chubb) |
| player_history | 1132 | **1132** |
| salary_history | 0 | **0** |
| auction_log | 0 | **0** |

- **§1 — bulk_register usado em produção? → NÃO (definitivo).** `auction_log` de produção
  está **vazio** e **0 players ativos** têm qualquer AuctionLog. O fluxo `/auction`
  (bulk_register ou qualquer outro) **nunca foi usado em produção**. As sessões reais de
  FA auction de 2025 **existem**, mas em `PlayerHistory` (fa_auction=54, auction_draft=181,
  rookie_draft=34, trade=118, drop=258, rollover=220, …; 1132 eventos), reconstruídas pelo
  F8a a partir da chain do Sleeper — **não** via a tela do Manager. (A premissa do prompt
  "auction_log de produção deve refletir as FA auctions de 2025" está **refutada**: refletem-se
  em PlayerHistory, não em auction_log.)
- **§3 — Órfãos atribuíveis ao bulk_register: 0** (lista nominal: vazia). auction_log vazio
  → nenhum AuctionLog-sem-SalaryHistory possível.
- **§4 — salary_history em produção: VAZIA (0), confirmado — não era artefato do seed.** Mas
  é **inofensivo**: nada lê `salary_history`. O `/api/salary_history` (`routes/salary.py:122`)
  consome **PlayerHistory**; cap usa `Player.salary`; rollover usa `Player.salary`. A
  `salary_history` é **tabela legada superseded pelo PlayerHistory (F8a)**. **Nenhum backfill
  necessário.** (Se um dia se quisesse popular, PlayerHistory é a fonte — já tem season +
  salary + contract_year por evento.)
- **§5 — Veredito final do F9-F2: REFATORAÇÃO APENAS (sem condicional).** Dano = 0 em produção.
  F2 do F9 = rotear `bulk_register` por `record_acquisition` + remover o hack `_noop`. Sem
  backfill.

**Observações para planejamento (fora do escopo do F9 — candidatas a item próprio):**
1. **`salary_history` é tabela legada/morta** — superseded pelo PlayerHistory, escrita por
   `record_acquisition`/`/auction` mas lida por ninguém. Avaliar deprecar a escrita ou
   alinhar o helper canônico ao PlayerHistory (a tela de histórico lê PlayerHistory).
2. **Acquisitions feitas pelo Manager não aparecem no PlayerHistory** — `record_acquisition`
   grava SalaryHistory+AuctionLog, não PlayerHistory; em produção a história só se forma via
   sync/F8a (chain do Sleeper). Como o fluxo OFF26 (importador) e o `/auction` escrevem no
   Manager, vale avaliar se precisam emitir PlayerHistory para aparecer no `/salary_history`.
3. **Risco seed ≠ produção / sem backup automatizado** — confirmado (seed de abril ≠ disco
   vivo). A cópia recebida hoje serve de backup pontual; avaliar item de rotina de backup +
   refresh do seed.

---

### F10 — `draft_budget` replicado em JavaScript no cap projector
🔲 **Pendente** — Prioridade **Média** — achado lateral de [[MAN-OFF26-3-F1]] (registrado 05/06/2026)

**Descrição:** a lógica canônica de budget de draft existe no backend
(`salary_engine.draft_budget` — `$200 − keepers`, mínimo $1 por slot vazio,
`usable`/`over_cap`/`insufficient`) e está **reimplementada no cliente** em JS, em
`templates/cap_projector.html` (~linhas 150-171: cálculo de `raw_budget`, `usable`
e aviso "Budget insuficiente").

**Motivação:** viola o princípio "1 fonte por modo de render" estabelecido no
**T2-FIX-2** (eliminar réplica de cálculo entre backend e JS). Divergência latente:
qualquer mudança na regra de budget exigiria editar dois lugares.

**Escopo do fix:** o cliente passa a consumir a fonte canônica via endpoint (expor
`draft_budget` por time numa rota e o `cap_projector.html` consome em vez de
recalcular).

**Observação de dependência:** idealmente resolvido **antes do OFF26-1** (janela
selada de keepers/cuts), que calculará budget ao vivo e deve **nascer consumindo o
canônico** — evita criar uma terceira réplica.

**Ref. cruzada:** [[MAN-OFF26-3-F1]] (diagnose do importador OFF26-3, achado §3).

---

### M10 — Busca de Jogador: Global + Calculadora
🔲 **Pendente — refinado 28/04/2026 (MAN-M10-REFINE)** — Prioridade **Média**

**Histórico:** item aberto originalmente como "Autocomplete de Jogador na Calculadora de Salário" (Baixa). Refinado in-place em 28/04/2026 após diagnose MAN-SEARCH-F1 — escopo ampliado para absorver busca global de jogador, prioridade promovida para Média, ID preservado. Calculadora segue como um dos consumidores; não é mais o único.

**Problema (escopo ampliado):**
- (1) **Busca global ausente.** Manager não tem ponto de entrada para chegar à player page (`/player/<id>`, M13) sem antes saber em que time fantasy o jogador está. Os 5 entry points existentes (`templates/roster.html:83,92`, `templates/admin_review.html:43,77`, `templates/salary_history.html:282`, `templates/trades.html:312`) todos pressupõem contexto. Caso de uso real de 28/04/2026: owner queria ver o contrato do Patrick Mahomes e teria que abrir os 12 rosters procurando visualmente.
- (2) **Calculadora de salário sem autocomplete.** `POST /api/salary/calculate` (`routes/salary.py:37-58`) recebe `player_name`, `espn_ref_value`, `contract_year`, `acquisition_type` como input manual. Se o jogador já existe no banco, esses dados estão disponíveis e poderiam ser pré-preenchidos.

**Objetivo (2 consumidores sob mesmo backend):**

- **Consumidor 1 — busca global na navbar.** Input acessível de qualquer tela. Dropdown de matches durante o typing. Ao selecionar um match, navegar para `/player/<id>`. Desktop: input inline na navbar, no slot vazio entre `.nav-links` e `.nav-right` (`templates/base.html:23-93`, `static/style.css:69-156`). Mobile: section nova no topo de `aside.nav-mobile-overlay` (`templates/base.html:97-133`), acima da section "Navegação" — padrão N1 preservado.
- **Consumidor 2 — autocomplete na calculadora de salário.** Substitui o input manual de `player_name` na tela `/salary` por input com dropdown de sugestões. Ao selecionar, preencher automaticamente ESPN ref value, contract year e acquisition type. Escopo original do M10, preservado.

**Backend — endpoint já existe (correção factual do diagnose):**
- `GET /api/player/search?q=<nome>&team_id=<opt>` em `routes/roster.py:312-326`. Singular (não `/api/players/search` plural como sugeria a versão pré-refinamento). Substring match (`Player.name.ilike("%q%")`), filtro opcional por `team_id`, `Player.is_dropped == False`, limit 20. Retorna `[p.to_dict() for p in players]`.
- F2 não precisa criar endpoint do zero. Possíveis ajustes (opcionais): payload reduzido (ver nota sobre `to_dict()` abaixo) e/ou inclusão/exclusão de campos derivados específicos para autocomplete da calculadora.

**Código a reusar (validado pelo diagnose):**
- Padrão de dropdown UI: `team-filter` em `templates/roster.html:51-65, 159-170` + classes em `static/style.css:311-340` (vanilla JS, abs-positioned, sem libs externas). Clonável diretamente para `player-dropdown` / `player-option`.
- Helper JS `renderPlayerNameLink` em `templates/base.html:245` — gera `<a href="/player/${id}" class="player-name">`. Já reusado por `salary_history.html:282` e `trades.html:312`. Disponível para renderização dos resultados, mas avaliar em F1 se vale usar direto ou montar link manual no JS local.
- Padrão debounce: `oninput="loadHistoryDebounced()"` em `templates/salary_history.html:27-31`. Aplicar para reduzir spam de requests durante typing.

**Código que NÃO serve (correção factual do diagnose):**
- `player_lookup.find_player_by_name()` é matching **estrito 4-tier** (exact → case-insensitive → normalized → None) usado em reconciliação de imports Sleeper/CSV (`player_lookup.py:53-122`). **Não serve para autocomplete** — incompatível com prefix typing ("mah" → Mahomes). O endpoint `/api/player/search` já usa `ilike` substring, que é o caminho certo. A versão pré-refinamento do M10 sugeria reusar `find_player_by_name`, premissa incorreta agora corrigida.

**Por que não absorver em O2 (refutação explícita da Opção D do diagnose, baseada nos 3 critérios de MAN-O2-REFINE de 27/04/2026):**
- (a) **Target page diferente:** O2 enriquece o conteúdo de `/player/<id>` (cards de NFL/stats/ADP no template). Busca global atravessa o app via navbar — não é "da página".
- (b) **Fonte de dados diferente:** O2 puxa Sleeper API (`/stats/nfl/...`, `/v1/state/nfl`) + Sleeper players cache. Busca usa apenas DB local (`Player.query.filter`). Zero overlap de fonte.
- (c) **Escopo natural distinto:** "enriquecer página" e "navegar até a página" são verbos diferentes. Absorver em O2 forçaria escopo heterogêneo e travaria O2 atrás da busca, ou inverso.

**Por que não criar item novo (refutação da Opção A — "S1 — Search"):** ID novo seria mais descritivo, mas perderia o histórico do M10 (a calculadora segue sendo um consumidor legítimo) sem ganho técnico. Opção C (refinar in-place) preserva continuidade auditável.

**Notas para F1:**
- `Player.to_dict()` em `models.py:173-197` retorna 21 campos por jogador, incluindo invocação de `is_renewal_candidate()` (método) e `projected_next_salary` (função). Para 20 resultados de busca = ~5KB JSON + 20 invocações por request. F1 avalia se vale criar `Player.to_search_dict()` minimal (~6 campos: `id, name, position, nfl_team, fantasy_team, salary`) ou se 5KB é aceitável. Otimização condicional, não pré-requisito.
- Diagnose qualificou ausência de rate limiting global em endpoints Flask como decisão de plataforma — não absorvida neste item.

**Questões em aberto delegadas a F1:**
- **Breakpoint exato desktop ↔ mobile.** Diagnose sugeriu <768px só overlay; >1024px inline na navbar; faixa intermediária a definir.
- **Layout do dropdown dentro do overlay mobile.** Flow normal (dentro do `aside`, sem `position: absolute`) vs absolute. Define se o dropdown empurra conteúdo do overlay ou flutua sobre ele.
- **`Player.to_search_dict()` minimal vs `to_dict()` completo.** F1 decide com base em medição (5KB × frequência typing) ou simplesmente custo de criar o método.
- **Renderização do link no result item.** Reusar `renderPlayerNameLink` direto vs link manual no JS local — escolha de consistência.
- **Decisão de batching.** 2 consumidores numa única camada vs quebrar (ex: navbar primeiro, calculadora depois). F1 avalia priorizando o gap UX maior (navegação global) primeiro.

---

### F8 — Reconstruir PlayerHistory a partir da Sleeper API
✅ **Concluído (22/04/2026)** — F8a + F8b + F8c. Prioridade **Alta**

**Problema:** `PlayerHistory` tem informação fictícia para qualquer jogador que trocou de mão entre temporadas. O backfill atual (`_backfill_player_history()` em `routes/admin.py:428-503`) e o `import_csv.py` usam snapshot do CSV + estado atual do `Player` para inventar histórico, sem consultar `/drafts/<id>/picks` nem `/transactions/<week>` do Sleeper, que têm a verdade factual.

**Descoberto em:** 22/04/2026, verificando histórico do A.J. Brown (reconciliação do F7) + 3 outros casos apontados pelo owner.

**4 casos verificados via Sleeper API (evidência concreta):**

**1. Brandon Aiyuk (pid=106, sid=6803)**
- DB atual: `auction_draft` 2024 team=ESPN $8, `rollover` 2025 $8
- Verdade Sleeper:
  - 2024 startup auction r5p53 roster=5 (**Cangaceiros**) **$29**
  - 2025 W1 drop free_agent de roster 5
  - 2025 FA auction r6p62 roster=12 (**ESPN FANTASY LEAGUE**) **$8**
- Gap: salary 2024 errado ($8 em vez de $29), team 2024 errado, falta drop + re-auction. `contract_start_season=2024` devia ser 2025.

**2. Brock Bowers (pid=276, sid=11604)**
- DB atual: `keeper` 2024 team=Trust $21 ❌ (não foi keeper)
- Verdade Sleeper:
  - 2024 startup auction r5p57 roster=5 (**Cangaceiros**) $21
  - 2025 W5 trade roster 5→8 (Cangaceiros→Trust The Process) ✅ (capturado pelo S1 hoje)
- Gap: `acquisition_type=keeper` errado (foi `auction_draft`). Team 2024 errado.
- Nota: user lembra que trade foi pelo McBride + outra peça — verificar no payload da trade.

**3. Buffalo Bills DST (pid=47, sid=BUF)**
- DB atual: `rookie_draft` 2024 team=3 peat $1 ❌ (DST não participa de rookie draft)
- Verdade Sleeper:
  - 2024 startup auction r7p78 roster=7 (AlexTheDawg) $1
  - 2024 W5-W6: múltiplos waivers/free_agent entre rosters 7, 5 (e reinserção em 7)
  - 2025 W1 drop de roster 7
  - 2025 FA auction r3p27 roster=3 (Fazenda) $1
  - 2025 W5-W6: mais rotações (3 peat, mongoloides, Fazenda)
- Gap: `acquisition_type` totalmente errado. History tem só 2 rows lineares quando na verdade houve **7 transações**.

**4. C.J. Stroud (pid=162, sid=9758)**
- DB atual: `rookie_draft` 2024 team=mongoloides $1 ❌
- Verdade Sleeper:
  - 2024 startup auction r2p14 roster=5 (**Cangaceiros**) **$19** (user: "preço alto")
  - 2025 W1 drop Cangaceiros; W2 drop Tropa; W3 free_agent para achane
  - 2025 FA auction r4p47 roster=9 (Tropa) $1
  - 2025 W11 trade achane→mongoloides
- Gap: `acquisition_type=rookie_draft` errado, salary 2024 errado ($1 vs $19 real), team 2024 errado, `contract_start_season=2024` devia ser 2025, falta registrar drop/re-auction/trade.

**Causa raiz:**
- `_backfill_player_history()` usa `p.contract_start_season` + `p.fantasy_team` (estado atual) + `p.acquisition_type` do CSV para inventar events. Quando o player trocou de time entre temporadas, tudo isso diverge da história real.
- `acquisition_type='rookie_draft'` foi atribuído indevidamente a vários jogadores que foram FA-auction ou startup-auction (qualquer player com year-1 salary=$1, aparentemente).
- CSV `dynasty_rosters_clean.csv` tem dados stale: campo `team` é snapshot mid-2025 inconsistente; `contract_year_2025=2` + `orig_draft_season=2024` não distingue "contrato mantido desde 2024" vs "re-auctionado em 2025".

**Consequências:**
- Trade Manager pode calcular cap errado via `contract_start_season`
- Auditoria pública (ex: F1 3 Browns bug, F8 aqui) fica comprometida
- Projeção de VALORIZAÇÃO OK (usa `Player.salary` e `Player.contract_year` atuais que batem com realidade)
- UX do `/salary_history` narra eventos falsos (A.J. Brown foi corrigido no F7 mas os 4+ casos acima ainda mostram história fictícia)

**Proposta:**

**F8a — Rebuild via Sleeper chain:**
1. Walk chain: `current_league → previous_league_id → ... → startup_league`
2. Por liga: coletar `drafts` + `drafts/<id>/picks` + `transactions/<week 0..18>`
3. Reconstruir `PlayerHistory` canonicamente por `sleeper_player_id`:
   - Evento `auction_draft`/`rookie_draft`/`fa_auction` derivado de `draft.type` + rodadas + timing (startup auction = draft com N rodadas igual roster size; rookie draft = linear; FA auction = auction pós-rookie com ~8 rodadas)
   - Eventos `fa_waiver`/`trade`/`drop` de transactions (S1 já resolve trades novas; F8 faz backfill retroativo)
   - `team_name` do evento = time no momento do evento (map via roster_id + `Team.sleeper_owner_id`)
   - `salary` do evento: `metadata.amount` do pick (auction) ou regra do salary_engine (waiver/FA = $1, etc.)
4. Corrigir `Player.contract_start_season` + `Player.acquisition_type` quando divergir

**F8b — Revisar uso do CSV:**
- Manter CSV como fonte inicial só para valores que Sleeper não sabe (salary/contract atuais)
- Parar de derivar histórico do CSV — histórico vem exclusivamente da Sleeper chain
- Avaliar deprecar `dynasty_rosters_clean.csv` após F8a estabilizar

**F8c — Backfill one-time em produção:**
- Endpoint admin `POST /api/admin/player_history/rebuild` (`@admin_required`)
- Idempotente via UNIQUE constraint `(sleeper_player_id, season, event_type, team_name)` ou equivalente
- Padrão similar ao `sync_trades/backfill` do S1

**Escopo estimado:** 2-3 sessões. Similar em complexidade a S1+F7 combinados. Requer leitura pesada das convenções Sleeper (draft types, transaction types, metadata fields).

#### F8a — Core rebuild via Sleeper chain ✅ 22/04/2026

**Implementado:**
- Migration 5 em `_run_migrations()` (app.py): adicionou coluna `sleeper_event_ref` TEXT + backfill das 78 trade rows (S1) e 220 rollover rows + pré-limpeza de duplicatas + `CREATE UNIQUE INDEX uq_player_history_event ON player_history(player_id, season, event_type, team_name, sleeper_event_ref)`.
- Funções novas em `sync_sleeper.py`: `_walk_league_chain`, `_classify_draft`, `_collect_draft_events`, `_collect_transaction_events`, `_snapshot_player_history`, `_rebuild_player_history(dry_run=False)`.
- Modelo `F8PlayerBackup` em `models.py` (tabela auxiliar de rollback com `old_contract_start_season` e `old_acquisition_type` por player).

**Decisões de escopo:**
1. **Quintupleto UNIQUE via `sleeper_event_ref`** em vez de quadrupleto simples. Justificativa: quadrupleto `(player_id, season, event_type, team_name)` colapsa casos reais como BUF DST com múltiplos drops/waivers do mesmo time. `sleeper_event_ref` com formato `'tx:<id>' | 'draft:<id>:<pick>' | 'rollover:<season>'` é auditor-friendly.
2. **Heurística de draft validada contra dados reais:** `type=linear → rookie_draft` (não snake — achado da Fase 2); `type=auction + rounds≥20 + primeira liga da chain → auction_draft (startup)`; demais auction → `fa_auction`. 2025 tem 7 drafts complete (6 fa_auctions + 1 rookie linear), não 1 como assumido inicialmente.
3. **Delete-and-rebuild preservando S1 + rollover:** DELETE apenas rows com `sleeper_event_ref IS NULL` (fictícias do `_backfill_player_history`). Preserva 78 trades do S1 e 220 rollover events do F7.
4. **Trades delegadas 100% ao S1:** `_rebuild_player_history` chama `_sync_trades(league_id)` por liga na chain (idempotente via S1 UNIQUE), garantindo cobertura retroativa. `_collect_transaction_events` explicitamente pula `type=trade`.
5. **Reconciliação de Player.acquisition_type só para eventos >= 2025:** protege year-1 salary rules do `salary_engine.py` para contratos vigentes.
6. **Reconciliação usa Trade.trade_date como timestamp real** para trades preservadas do S1 — sem isso, acquisition_type de players tradados em legs tardias (ex: Stroud leg 11) seria overridden por eventos de leg anterior (ex: free_agent leg 3).

**Resultado do rebuild local:**
- `ligas_visitadas: [2024, 2025, 2026]` (2026 é pre_draft, sem events)
- `events_written: 794` | `deleted_legacy: 320` | `players_corrected: 180`
- Total PlayerHistory pós: 1092 rows (vs 578 antes) — 269 draft + 603 tx (trades + waivers + FA + drops) + 220 rollover preservado.
- Snapshot salvo em `data/.player_history_snapshot_20260422_182651.json`.

**4 casos de validação (todos batem com proposta F8 em improvements.md):**

| Pid | Player | ANTES | DEPOIS |
|-----|--------|-------|--------|
| 106 | Aiyuk | 2 rows, acq=auction_draft, start=2024 | 4 rows (auction $29 Cangaceiros 2024 + drop 2025 + fa_auction $8 ESPN 2025 + rollover preservado), acq=fa_auction, start=2025 |
| 276 | Bowers | 2 rows, acq=keeper, start=2024 | 3 rows (auction $21 Cangaceiros 2024 + rollover preservado + trade 2025 preservada), acq=trade, start=2025 |
| 47  | BUF DST | 2 rows, acq=rookie_draft, start=2024 | 8 rows (auction $1 AlexTheDawg 2024 + drop/add 2024 + drop 2025 + fa_auction $1 Fazenda 2025 + drop + fa_waiver 3peat 2025 + rollover preservado), acq=fa_waiver, start=2025 |
| 162 | Stroud | 3 rows, acq=rookie_draft, start=2024 | 7 rows (auction $19 Cangaceiros 2024 + drop 2025 + fa_auction $1 Tropa 2025 + drop 2025 + free_agent achane 2025 + rollover preservado + trade 2025 preservada), acq=trade, start=2025 |

**Validação regression:**
- `python salary_engine_test.py` → 49 testes passam (zero regressões)
- Player.salary e contract_year atuais dos 4 casos inalterados
- Re-run do rebuild → `events_written=0, events_skipped=794` (idempotência confirmada via UNIQUE)

**Warnings aceitos (30 total):**
- 2 players sem sleeper_player_id (Hollywood Brown pid=279, Cameron Ward pid=280) — skip esperado
- 217 sleeper_player_ids sem match no DB local (sample: 10216, 10218, 10223, etc.) — players dropados antes da criação do Manager, não bloqueantes
- Warnings do S1 (pick de season passada drafada) — esperados

**Arquivos modificados:** `models.py` (PlayerHistory.sleeper_event_ref + UniqueConstraint + F8PlayerBackup), `app.py` (Migration 5 em 5 sub-blocos idempotentes), `sync_sleeper.py` (6 funções novas + helper `_count_players_to_correct`).

#### F8c — Endpoint admin + UI + ajuste do boot ✅ 22/04/2026

**Implementado:**
1. **3 endpoints em `routes/admin.py`**:
   - `POST /api/admin/player_history/rebuild` (`@admin_required`) — chama `_rebuild_player_history(dry_run=False)`. Retorna summary JSON.
   - `POST /api/admin/player_history/rebuild?dry_run=1` — simula sem gravar. Retorna `{events_written, events_skipped, warnings, players_corrected, ligas_visitadas, deleted_legacy, dry_run}`.
   - `POST /api/admin/player_history/restore` (`@admin_required`) — restaura último snapshot JSON em `data/`, reverte `Player.contract_start_season` e `acquisition_type` via `f8_player_backup`, limpa backup e flag. Retorna `{success, restored_rows, players_reverted, snapshot}`.
   - Helpers `_latest_snapshot_path()` e `_snapshot_info()` consultam `data/.player_history_snapshot_*.json` via glob — admin_page passa info para o template.

2. **UI card `Histórico Canônico (F8)` em `templates/admin.html`**:
   - Posicionado antes do card "Trades Históricas (Backfill)" pra agrupar ferramentas de backfill canônico.
   - 3 botões: "Simular (dry-run)" (cinza), "Executar Rebuild" (azul), "Restaurar Snapshot" (vermelho, `disabled` se não há snapshot).
   - Banner verde "Rebuild já foi executado neste DB" quando `AppConfig.f8_rebuilt='true'`.
   - Timestamp do último snapshot exposto em small-text abaixo dos botões quando existe.
   - Confirms em JS: rebuild tem confirm mencionando snapshot automático; restore tem confirm explicando reversão.
   - Resultado inline com contagens e warnings truncados (primeiros 3), seguindo padrão do card S1.

3. **EVENT_LABELS + EVENT_BADGES em `templates/salary_history.html`**: adicionados `drop → Dropado` (badge review), `free_agent → Free Agent (add)` (badge trade), `commissioner → Ajuste do comissário` (badge review). `fa_auction` já existia. Os 3 novos tipos são emitidos por `_collect_transaction_events` do F8a e não tinham label — apareciam crus na tela `/salary_history`.

4. **Skip condicional no boot em `app.py`**: dentro do block `if fresh_import:`, antes de chamar `_backfill_player_history()`, verifica `get_config('f8_rebuilt', 'false')`. Se `'true'`, loga `[boot] F8 rebuild já executado — _backfill_player_history ignorado` e skipa. Função em si não removida — continua disponível como legacy para DBs novos.

**Validação (22/04/2026) via Flask test_client com admin mockado:**
- `POST /rebuild?dry_run=1` → 200, summary correto, DB inalterado (PlayerHistory permanece 1092).
- `POST /rebuild` → 200, snapshot criado em `data/`, flag `f8_rebuilt='true'`, `f8_player_backup` com 182 rows.
- `POST /restore` → 200, 1092 rows restauradas do snapshot, 182 players revertidos (Aiyuk/Bowers/BUF/Stroud voltam aos valores do CSV), flag removida, backup zerado.
- Re-rebuild após restore → 200, 182 players novamente corrigidos, idempotência preservada (events_written=0 se nenhum mudou).
- `GET /admin` → 200, card F8 renderizado, banner de flag ativo, botão restore habilitado.
- `python salary_engine_test.py` → 49/49 passam.

**Observação sobre boot skip:** em DB maduro (sem `fresh_import`), o block inteiro de post-sync não executa, então o guard é no-op. O guard só age em DB novo (primeiro deploy Render, dev do zero) que já rodou F8 manualmente antes — cenário raro mas coberto. DBs novos sem F8 (default Render first boot) executam legacy normalmente.

**Arquivos modificados:** `routes/admin.py` (+~90 linhas: imports, helpers, 2 endpoints, snapshot_info passado para template), `templates/admin.html` (+~35 linhas card + ~95 linhas JS), `templates/salary_history.html` (+3 entradas em cada mapa), `app.py` (+5 linhas skip condicional), `manager_vision.md` (+~40 linhas seção Calendário Operacional da Liga).

#### F8-NOTES — Notas legíveis + trade context na timeline ✅ 22/04/2026

**Problema:** Timeline do `/salary_history` exibia strings cruas como `"auction_draft r6p65 (draft 1107510815168729088)"` e `"Trade sleeper_sync tx=1260798906057375745 (...)"` ilegíveis para owners. Trades sem contexto (contraparte + assets).

**Implementado em `routes/roster.py`:**
- Função `_format_event_display(h, trade_by_tx)`: rótulo PT-BR por event_type.
  - `auction_draft`: `Startup Auction · Rd {R}, Pick {P} · ${salary}`
  - `fa_auction`: `FA Auction · Rd {R}, Pick {P} · ${salary}`
  - `rookie_draft`: `Rookie Draft · Rd {R}, Pick {P}`
  - `fa_waiver`: `Waiver Add`  |  `free_agent`: `Free Agent Add`
  - `drop`: `Dropado por {team_name}`
  - `rollover`: `Valorização (Ano {contract_year})`
  - `trade`: `Trade com {counterparty} · {assets_resumidos}` via join com Trade table pelo `sleeper_transaction_id` extraído do `sleeper_event_ref`.
- Round/pick extraídos via regex `r(\d+)p(\d+)` do campo `notes` atual.
- Counterparty de trade: o lado de `Trade.team_a/team_b` que não bate com `h.team_name`.
- Resumo de assets: parseia `Trade.description` em boundaries `;` e trunca com `…` em ~100 chars.
- Prefetch de Trade rows em 1 query `IN(tx_ids)` por request.
- Payload inclui campo novo `display_notes` sem alterar `notes` cru (debugging preservado).

**Template (`templates/salary_history.html`):**
- `renderEventRow` usa `e.display_notes || e.notes` com fallback.
- Coluna `event-amount` removida — display_notes já carrega a info relevante por event_type (evita ruído `$0 · Ano 0` em drops).

#### F8-GAP — Backfill de trades órfãs (restore side-effect) ✅ 22/04/2026

**Problema:** 18 trades de 2024 existiam em `Trade` table mas sem rows em `PlayerHistory`. Investigação mostrou causa raiz: durante testes do F8c, chamadas a `/api/admin/player_history/restore` apagaram `player_history` restaurando o snapshot, mas mantiveram as `Trade` rows criadas pelo run anterior. Re-runs do `_sync_trades` skipam via idempotência de `Trade.sleeper_transaction_id`, então os events nunca foram recriados.

**Implementado em `sync_sleeper.py`:**
- Função `_backfill_missing_trade_history()`: query para Trade rows sem PlayerHistory correspondente, walking da Sleeper chain para resolver qual liga/leg cada tx pertence, criação de rows com `season` real (da liga), idempotente via UNIQUE. NÃO atualiza `Player.team_id/fantasy_team/via_trade` (backfill retroativo só cria rastro histórico).

**Endpoint + UI:**
- `POST /api/admin/player_history/backfill_trades` em `routes/admin.py` (`@admin_required`).
- Botão "🔗 Backfill de Trades Órfãs" no card F8 do `/admin`, entre Rebuild e Restore.

**Validado em dev (22/04/2026):** 18 trades processadas, 40 PlayerHistory events criados. Distinct `tx:` refs em player_history: 29 → 45 (2 tx sobraram órfãs por terem só assets de jogadores já dropados do DB — trades tx=1154533231048630272 e tx=1152430188438040576, esperadas). Casos testados: Tank Dell (agora mostra trade 2024 Pitbull→Cangaceiros), Chase Brown, Ladd McConkey, Chuba Hubbard, D'Andre Swift — todos com timeline completa pós-backfill.

#### F8b — Guard em import_csv.py (AppConfig.f8_rebuilt) ✅ 22/04/2026

**Problema resolvido:** `run_import()` rodava a cada boot e fazia upsert de `acquisition_type` + `contract_start_season` a partir do CSV, revertendo as 180 correções do F8a no próximo boot.

**Implementado:**
1. `_rebuild_player_history(dry_run=False)` em `sync_sleeper.py` agora chama `set_config('f8_rebuilt', 'true')` no fim do path bem-sucedido.
2. `run_import()` em `import_csv.py` lê `get_config('f8_rebuilt', 'false')` no início. Se `true`, log "F8b guard active — skipping acquisition_type and contract_start_season on existing players" e pula essas duas atribuições no update path. Todos os outros campos (salary, contract_year, espn, position, etc.) continuam normais.

**Decisões de escopo:**
- **AppConfig em vez de coluna nova em Player:** flag é estado global do DB ("rebuild já rodou neste banco"), não metadata per-player. `AppConfig` já existe (key/value pattern) e `get_config`/`set_config` são a API canônica — zero schema change.
- **Guard só no update path, não no create path:** player novo adicionado ao CSV pós-F8 (ex: rookie adicionado mid-season) precisa dos valores iniciais do CSV. F8 re-run depois reconcilia se necessário via Sleeper chain.
- **Guard inativo em DB sem a flag:** comportamento original preservado para DBs novos (flag ausente → `false` default → nenhuma proteção). Importante para primeiro deploy em Render quando DB novo é criado.

**Validado (22/04/2026) em 3 cenários:**
1. **Flag setada pelo rebuild:** `_rebuild_player_history(dry_run=False)` → `AppConfig.f8_rebuilt == 'true'` ✓
2. **Reboot preserva correções F8a:** re-importa Flask app com flag ativa → `run_import()` skipa os 2 campos → 4 casos permanecem corrigidos (Aiyuk/Bowers/BUF/Stroud com `acq` e `css` do F8a) ✓
3. **DB sem flag reverte:** deletar AppConfig row + chamar `run_import()` → CSV sobrescreve os 2 campos (Aiyuk volta a `auction_draft 2024`, Bowers a `keeper 2024`, etc.) — comportamento original preservado ✓

**Arquivos modificados:** `sync_sleeper.py` (+2 linhas: `from models import set_config; set_config("f8_rebuilt", "true")` no fim de `_rebuild_player_history`), `import_csv.py` (+4 linhas: import `get_config`, leitura da flag, log condicional, `if not f8_rebuilt` wrap nas duas atribuições).

---

### O2 — Enriquecer Página do Jogador: Contexto NFL + Valor de Campo
🔲 **Pendente** — Prioridade **Média**

**Problema:** A página atual (`player_detail.html`, M13) mostra contrato, salary history e botão "Propor Trade". Faltam duas camadas de contexto: (a) **valor de campo** — pontuações históricas por temporada, posição no ranking/ADP, próximos jogos; e (b) **contexto NFL básico** — time NFL atual visível no header, e posição relativa do jogador entre os jogadores da mesma posição no time NFL (depth chart).

**Origem da observação:**
Caso real DJ Moore (WR) em 27/04/2026 — owner abriu a player page e percebeu ausência completa de contexto NFL: nem o time NFL aparecia no header (apesar de `Player.nfl_team` estar no banco), nem havia indicação de o jogador ser WR1/2/3 do Carolina. Decisão tomada na sessão de planejamento (27/04/2026, decisão A): refinar O2 in-place absorvendo as duas dimensões novas, em vez de abrir item separado (O3). Critérios para refinar e não fragmentar: mesma página alvo (`player_detail.html`), mesma fonte de dados (Sleeper), escopo natural de "enriquecer page do jogador" já existia no item — abrir O3 seria fragmentação artificial.

**Objetivo (5 dimensões, agrupadas):**

*Contexto NFL — dimensões novas, dependem só de campos já presentes no banco/cache:*
- **Time NFL no header:** exibir `Player.nfl_team` no cabeçalho da player page. Hoje o header mostra posição, nome do jogador e dono na liga, sem o time NFL. Trivial — apenas exibir.
- **Depth chart NFL embedded:** listar os jogadores da mesma `Player.position` e do mesmo `Player.nfl_team` ranqueados por `depth_chart_order` do Sleeper players cache (campo já consumido pela aplicação). Permite ao owner avaliar em segundos se o jogador é WR1/2/3 do time NFL sem sair da página.

*Valor de campo — dimensões originais do escopo:*
- **Stats históricas:** buscar da Sleeper API (`/stats/nfl/player/<sleeper_player_id>?season_type=regular&season=<year>`) — pontos totais e média por semana por temporada disponível.
- **ECR/ADP:** usar `adp` e `search_rank` já presentes no Sleeper players cache (`.sleeper_players_cache.json`) — zero request extra. Para ranking ESPN, usar ESPN ref value (`espn_ref_value`) já no banco como proxy de tier.
- **Schedule próximo (consolidado de UX4):** próximas semanas via Sleeper schedule (avaliar fonte exata — `/v1/state/nfl` + matchups por week, ou cache externo).

Apresentar de forma compacta, sem sobrecarregar a página. Referência: FantasyPros (abas Overview, Statistics, Schedule).

**Notas para F1:**
- Item UX4 da rodada de 23/04/2026 foi consolidado aqui em vez de duplicado — escopo virtualmente idêntico (mesma API Sleeper, mesma página alvo).
- F1 deve avaliar se as 5 dimensões cabem numa única camada de implementação ou se vale propor batches (ex: contexto NFL como batch 1 — só template + leitura de cache local; valor de campo como batch 2 — exige fetch Sleeper stats + schedule), considerando densidade da página e prioridade percebida pelo owner.

---

### L2 — League Hub Season Mode: Matchups, Schedule, Standings
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Durante a temporada, a visão de liga precisa incluir resultados semanais, schedule e standings — dados que o Manager ainda não consome.

**Objetivo:**
- Sync de matchups via Sleeper API (`/league/<id>/matchups/<week>`).
- Na vista `/league`: adicionar coluna de record e pontos totais.
- Na vista `/team/<id>`: adicionar aba "Temporada" com schedule semanal e pontuações.
- **Pré-requisito:** L1 concluído. Implementar quando a temporada 2026 começar.

---

### C1 — Cap Projector: Modo "Drop Programado"
🔲 **Pendente** — Prioridade **Média**

**Problema:** O cap projector simula o roster atual. Não há como avaliar o impacto de cortar jogadores ou liberar cap para uma trade sem alterar dados reais.

**Objetivo:** Adicionar no cap projector a possibilidade de marcar jogadores como "drop temporário" — apenas na sessão de simulação, sem alterar o banco. O cap projetado recalcula em tempo real excluindo os jogadores marcados. Útil para:
- Planejar cortes de offseason
- Avaliar se há cap suficiente para receber um jogador numa trade
- Simular cenários antes de propor uma troca

Não persiste nenhuma alteração no banco — é simulação pura, análoga ao que o simulador de trades já faz.

---

### IR-CLEANUP — Remover Seletor Manual de IR no Roster
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** O roster tem um toggle de IR manual (`@admin_required`) que não tem efeito persistente. O sync do Sleeper (`sync_sleeper.py:257`) sobrescreve `Player.is_on_ir` a cada execução de forma autoritativa, lendo o array `reserve` de cada roster da API. Toggle local cria falsa sensação de controle: admin clica, estado muda na UI, próximo sync (boot ou manual) reverte silenciosamente. Confirmado em diagnose MAN-IR-F1: 16 players IR localmente, todos com `sleeper_player_id`, todos provavelmente vindos do `reserve` Sleeper.

**O que remover:**
- Endpoint `POST /api/player/<player_id>/ir` em `routes/roster.py:119-135` (função `toggle_ir`).
- Handler JS `toggleIR(playerId, toIR)` em `templates/roster.html` (busca em `/api/player/<id>/ir`).
- Toggle visual na UI (botão/checkbox que dispara `toggleIR`).

**O que preservar:**
- Campo `Player.is_on_ir` (sync continua escrevendo, modelo intacto).
- Lógica de cap que exclui IR: `models.py:97-99` (`Team.total_active_salary`), `routes/roster.py:70-75` (cap projetado), `routes/admin.py:77-78` (rollover preview).
- Constante `MAX_IR` (informativa — sync respeita o limite via Sleeper).
- Badge `🏥 IR` no roster (visual, lê `p.is_on_ir`, sem alterar nada).

**Pré-condição:** nenhuma — sync já cobre 100% dos casos para players ativos da liga (todos têm `sleeper_player_id` e estão em algum roster Sleeper).

**Validação esperada:** após remoção, 16 players IR continuam IR; sync mantém o número alinhado com Sleeper; cap projector continua ignorando IR no total.

**Caveat de UX:** se quiser preservar capacidade de override em ambiente sem Sleeper (offline ou API fora), avaliar alternativa conservadora — manter o seletor mas adicionar tooltip "Será sobrescrito no próximo sync". Recomendação default é remover (regra do projeto: ações na UI devem ser efetivas ou marcadas claramente como simulação).

---

### UX2 — Acquisition Types PT-BR em Todas as Telas
🔲 **Pendente** — Prioridade **Baixa**

**Problema:** Valores enum como `auction_draft`, `free_agent`, `fa_waiver`, `fa_auction`, `rookie_draft`, `unknown` aparecem em inglês cru em `team_detail.html`, `roster.html` (badge inline), `salary_history.html` (timeline). Termos técnicos do schema vazando para a UI.

**Objetivo:** mapa de tradução PT-BR centralizado, aplicado consistentemente:

| acquisition_type | Label PT-BR |
|------------------|-------------|
| auction_draft | Auction |
| rookie_draft | Rookie Draft |
| fa_waiver | Waiver |
| fa_auction | FA Auction |
| free_agent | Free Agent |
| unknown | — |

**Implementação proposta:**
- Macro Jinja `acquisition_label(acq_type)` em `templates/_macros.html` para contextos server-side.
- Helper JS `acquisitionLabel(t)` em `base.html` (junto com `renderPlayerNameLink`) para JS template strings.
- Aplicar em: `team_detail.html`, `roster.html` (badge inline), `salary_history.html`, `cap_projector.html`, `admin.html` (review_players).

**Pré-requisito:** nenhum.

---

### UX5 — Redesign da Seção Picks em Detalhe de Time
🔲 **Pendente** — Prioridade **Média**

**Problema:** A seção Picks em `/team/<id>` (introduzida em L1, 23/04/2026; intocada por UX1/UX4) renderiza **3 tabelas anuais idênticas** (2026, 2027, 2028) com headers repetidos a cada ano (Round / Origem / Notas). A coluna Origem mostra apenas emojis decorativos + nome do time de origem, a coluna **Notas aparece vazia em todas as ocorrências observadas**, e o layout ocupa espaço vertical significativo com baixa densidade informacional. Tipicamente 3 linhas por ano (Rd1, Rd2, Rd3), 3 anos → 9 linhas úteis espalhadas em 3 tabelas com 3 headers repetidos.

**Referências:** observação visual pós-UX4 (commit `a10fcb6`, 24/04/2026).

**Escopo candidato (a fechar na F1 de UX5):**

Várias direções possíveis, não mutuamente exclusivas:

- **(a) Reestruturação de colunas** — avaliar se Origem e Notas devem continuar como colunas separadas, ou consolidar (ex: "Rd1 via 2024 trade com X"), ou remover campos sem uso (Notas) e adicionar campos com utilidade real (dynasty value da pick, projected_pick, pick number absoluto).
- **(b) Consolidação visual das 3 tabelas** — 1 tabela única com coluna Season + agrupamento, ou grid compacto de cards por round, ou timeline horizontal por ano. Elimina header repetido.
- **(c) Avaliação do modelo de dados por trás** — a coluna Notas está vazia porque o campo nunca é populado na prática? Se sim, vira débito estrutural (remover da UI + avaliar no model). Se populado em casos específicos, documentar e usar.
- **(d) Mudança de paradigma** — tabela → cards ou grid estilo "pick chip" (reusar `.pick-chip` existente do Trade Manager), com seleção visual densa e clickability pra propor trade.

F1 de UX5 mapeia estado atual (frequência de uso de Notas, payload do handler, infra reusável) e decide escopo concreto.

**Infra relacionada reusável:**
- `dynasty_value` por pick já canonizada em **T2-FIX-2** (`/api/picks` pré-resolve via backend). Se UX5 exibir valor dynasty inline, caminho já limpo.
- Classe `.pick-chip` existente (usada em Trade Manager e em M9 grid de picks).
- Helper `pick_sleeper_id` + `resolve_asset_value` canônicos em `dynasty_values.py`.

**Relação com outros items:**
- **Independente de UX2** (PT-BR em outras telas) e **UX4-b** (restauração ESPN+Projeção em roster).
- **Pode impactar contrato do endpoint/handler** (`/team/<id>` em `routes/league.py`) se a F1 decidir adicionar `dynasty_value` ou outros campos derivados ao payload de picks.
- **Sem conflito com UX4** — UX4 redesenhou a seção Roster em `/team/<id>`; UX5 toca seção diferente (Picks) da mesma página.

**Pré-requisito:** nenhum bloqueante.

---

### UX6 — Revisão da Largura Máxima do Container Global da Aplicação
🔲 **Pendente** — Prioridade **Média**

**Problema (sintoma observado):** Análise visual das páginas do Fantasy Manager (24/04/2026, pós-UX4-b) identificou que o conteúdo principal (roster, cap breakdown, picks, trades, etc.) fica espremido no centro da viewport com **margens laterais significativas** — em monitor de ~1920px de largura, ~700px ficam como ar lateral (~350px em cada lado). Referências externas modernas (FantasyPros, apps de produtividade) aproveitam largura maior da viewport em monitores wide.

**Referências:** commits UX4 (`a10fcb6`), UX4-b (`e495453`).

**Escopo (a fechar na F1 de UX6 como investigação aberta):**

- **F1 — diagnose da causa real** (sem presumir): mapear qual conjunto de propriedades CSS do wrapper/container global (incluindo, mas não limitado a, `max-width`, `padding`, estrutura de grid, flexbox, ou wrappers aninhados) produz o comportamento observado. Identificar o(s) seletor(es) envolvidos em `base.html`, `static/style.css`, ou outros. Medir valores atuais. Não assumir qual é a causa antes de inspecionar.

- **F1 — mapeamento cross-tela:** percorrer as 12+ telas (roster, detalhe de time, trades, cap_projector, admin, league hub, picks, auction, offseason, player detail, salary history, salary) e avaliar por tela:
  - Qual largura útil atual ocupa e qual faria sentido
  - Se há componentes com largura fixa (ex: modais, cards centralizados) que poderiam quebrar com mais espaço horizontal
  - Se tabelas densas (cap_projector com 10 colunas, admin review) ganhariam com mais largura

- **F1 — opções com trade-offs:** após identificar a(s) causa(s) real(is), propor caminhos de correção com prós e contras. Não pré-selecionar solução — owner decide entre opções mapeadas.

**Impacto cross-tela:** afeta **todas as páginas do app**. Risco de regressão em layouts específicos que implicitamente assumem a largura atual. F1 precisa mapear amplamente.

**Relação com outros items:**
- **Independente de UX4-c** (densidade localizada em `/team/<id>` e `/`), **UX5** (Picks), **UX2** (PT-BR).
- **Pode reduzir ou eliminar** necessidade de alguns aperfeiçoamentos localizados se liberar largura horizontal suficiente — ex: pressão no colgroup (UX4-c frente 3) pode diminuir se a tabela ganhar mais espaço horizontal.
- **Ordem decidida pelo owner:** UX4-c primeiro, UX6 depois.

**Riscos:**
- Componentes com largura fixa (cards, modais, filtros centrados) podem ficar visualmente desbalanceados com container mais largo — precisa mapear na F1.
- Tabelas longas (cap_projector) podem ganhar com mais espaço mas também podem virar "parede de dados" difícil de scanear — validação visual empírica pós-implementação.
- Telas com poucas colunas (admin users, offseason standings) podem parecer vazias/ilhadas em container muito largo. Padding interno ou constraint de tabela específica resolve.

**Pré-requisito:** nenhum bloqueante.

**Observação estratégica:** este é um dos poucos items do backlog com **escopo cross-app verdadeiro**. Enquanto UX1-UX5 tocaram telas específicas, UX6 muda o framing visual de tudo. Por isso F1 merece cuidado extra — investigação aberta da causa antes de propor soluções, mapeamento amplo antes de qualquer F2, e possivelmente prototipagem em 1 tela específica antes de roll-out.

---
