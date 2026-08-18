# improvements.md — Fantasy Manager

> Backlog vivo de melhorias, bugs e features pendentes.
> Atualizado em: 19/08/2026-pt2 (sessão **MAN-UX25-b**, código: **a obrigação de corte do [[UX25]] agora é VIVA no cap projector** — a tela onde a decisão de corte é de fato simulada. Item "Roster" na barra sticky, recalculado **pelo POST `/budget` que já roda a cada toggle** (F10 honrado: o servidor conta — ele conhece `is_on_ir`; o JS só exibe; o limite vem no payload = `MAX_ROSTER` do engine, **zero hardcode** no cliente): `X/22 ativos (+K IR) ✓` discreto quando regular, **"· cortar ≥N" em alerta** quando o cenário excede, **contando para baixo** até regularizar; **rookies do cenário ocupam vaga de ativo**; "Spots vazios" mantido com o significado de auction (0 truncado é verdadeiro — o indicador novo desambigua; decisão de menor mudança reportada). Campo `roster` aditivo; **D9/`budget` intocados** (teste prova folha $125 COM o IR e `empty_spots` seguindo truncado). +4 testes (`roster_excess_test` 5→9); smoke na cópia de prod: **Trust 26/22 "cortar ≥4" → toggla 4 → ✓ → volta → reaparece**, rafaelferreirap `+1 IR` fora da conta, Pitbull 22/22 neutro. `template_js_test` obrigatório verde; gate [[O7]] exit 0. [[UX25]] segue ⚠️ — agora Hub + projector fecham juntos no mesmo smoke de prod. Auditor exit 0.)
> Atualizado em: 19/08/2026 (sessão **MAN-UX-NEXT-REG-F2**, código: **[[UX25]] ⚠️ Crítica (20/08)** — *excesso de roster vira obrigação explícita no card do Hub*. O "Slots livres 0" era igual para cheio-exato e ESTOURADO (`max(0, 22−N)` engole o excesso — F1-rápida confirmou o truncamento no engine) e, com os rosters inflados pelos 36 rookies, ninguém via obrigação de corte. **Limite canônico adotado: `MAX_ROSTER=22` ATIVOS, IR fora da conta** (regulamento 1.3, a mesma distinção folha×contagem do [[OFF26-16]]; fonte = a constante do engine, zero literal novo). F2 leitura pura: faixa **"⚠️ Cortar ≥N até 20/08"** + contagem **"X/22 ativos (+K IR)"** como campos NOVOS do card — ⛔ réguas de cap/bid intocadas (teste dedicado prova que o `slots` truncado continua o mesmo), cap negativo segue no alerta próprio, time regular = zero ruído. `roster_excess_test.py` (5, função de card pura); smoke na cópia inflada: 3 cards com obrigação batendo 3/3 com a query, ⭐ **âncora Trust The Process conferida dos DOIS lados** (26 ativos → "cortar ≥4"; o Sleeper AO VIVO devolve os mesmos 26). Gate [[O7]] exit 0 (league.html + style.css). ⚠️ literal "até 20/08" morre com a janela — generalização fica para o pós-cortes. Fica ⚠️ até o smoke de prod ([[PROC1]] — style.css é artefato público conferível). Auditor exit 0.)
> Atualizado em: 18/08/2026-pt4 (sessão **MAN-OPS1-REG-F2**, código, urgente: **[[OPS2]] ⚠️ Alta** — *freeze administrativo de sync* para a janela de operação MANUAL no Sleeper (draft replay do OFF26-30, hoje): entre os drops e o complete um sync fotografaria os 36 como dropados — sujeira em folha/keeper sheet na semana de cortes. Lição [[OFF26-23]] aplicada: **o sistema recusa, não depende da disciplina dos 3 admins**. Flag `sync_frozen` + `POST /api/admin/sync_freeze` (liga/desliga manual, sem TTL por decisão de escopo) + **guarda-helper única** nas DUAS entradas de motor — `run_sync` recusa **antes de qualquer I/O** (zero rede, zero SyncLog) e `_sync_trades` (⭐ mapeamento achou que o backfill chama essa função DIRETO, sem passar pelo run_sync — coberto pelo mesmo helper, nenhuma réplica por porta); botão da navbar → 409 com mensagem acionável no banner existente; card do `/admin` com 🧊 + toggle; boot degrada gracioso. `sync_freeze_test.py` (6, incl. sentinela de rede provando recusa pré-I/O E que destravado a guarda deixa passar; ⭐ a suíte pegou um caso real de teste-de-app: com ctx permanente o flask-login cacheia o user em `g` e o request seguinte recebe objeto detached). Smoke real: congelar → 409 + backfill frozen + card → destravar → sync roda. Gate [[O7]] exit 0. ⚠️ **ID: o prompt veio MAN-OPS1-*, mas OPS1 é a higiene do working tree** — nasceu OPS2, colisão registrada. Smoke de prod = o próprio uso de hoje. Auditor exit 0.)
> Atualizado em: 18/08/2026-pt3 (sessão **MAN-UX23-REG-F1 + MAN-UX23-F2**, diagnose + código na mesma janela: **[[UX23]] ⚠️ Alta** — *o Cap Projector mirava `current+1` sem consciência de fase* e pulou para 2027 no meio da janela da auction 2026 (print do owner: título 2027, banner honesto para a **pergunta errada**, Δ +$0, board DP1 **vazio**, DP2 **ignorando rookie em silêncio**). **F1:** 6 sítios inline, zero helper, zero gate de fase — e a base correta **já existia** (modo D9). **F2 (decisões do owner: sinal por evidência AuctionLog · colunas saem · título explicita o modo):** `planning_target_season()` como fonte única — `current+1` pré-rollover · `current` na janela pós-rollover/pré-auction · `current+1` com **≥3 `fa_auction`** da corrente (⭐ calibração documentada: leilão real entra em lote; 1-2 registros = teste avulso que não pode virar a chave em 20-24/08); os 6 sítios consomem o helper, títulos e `SEASON_PROJ`/`MODE` vêm do servidor, colunas Sal-próximo/Δ saem em modo corrente, POST com `projected:false` (D9 consumido, não criado), tag **"FOLHA CORRENTE · AUCTION 2026"**; banner/badges/DP1/DP2 **voltaram sozinhos** pela mudança do target. `planning_target_test.py` (12, incl. guardas AST anti-réplica e "36 rookie_draft não contam"); smoke estado-de-prod (board 251 = 287−36; budget corrente == régua do Hub) + **fixture pós-24/08 virando a 2027/projetado sozinha**. Gate [[O7]] exit 0; `template_js_test` obrigatório verde. **[[UX24]] 🔲 Baixa registrado de carona** (colunas "Proj 2027" do roster/team_detail — mesma família, superfície informativa). ⚠️ fica ⚠️ até o smoke de prod ([[PROC1]]). Auditor exit 0.)
> Atualizado em: 18/08/2026-pt2 (sessão **MAN-UX21-REG-F2**, código + registro na mesma janela: **[[UX22]] ⚠️ Alta** — *board de picks ganha visão de INVENTÁRIO quando a season não tem ordem*. O vazio era efeito colateral da ocultação do [[OFF26-29]]: 2027/2028 só diziam *"ordem ainda não definida"*, e na semana de trades a página não respondia "quantas picks tenho, de quem, em que rodada" (print do owner). A visão renderiza **posse por rodada** reusando a anatomia de célula do [[UX20]] — dono atual, `via <original>` na trocada, verde de "minha", ⇄ — **sem número de posição** (ordem não se inventa; a lista sai por nome do dono) + **chips de contagem por time** + o aviso antigo encolhido para uma linha; ⭐ como a célula carrega `data-team-name`, **filtro e realce existentes funcionam sem JS novo**; season com ordem → render ordenado intacto (a visão sai sozinha quando `round_centered` ganha rodadas). Leitura pura: lottery/classificação, Lottery Odds, predicado de consumida, schema e sync intocados. `picks_inventory_test.py` (5, incl. ordenado-intacto via fixture de standings); smoke real na cópia do ensaio (72 células = 72 picks, chips 72/72); **gate [[O7]] exercido, exit 0** (diff toca `picks.html`). ⚠️ **ID: o prompt pedia UX21, ocupado** — nasceu UX22, colisão registrada (precedente UX15→UX20). Fica ⚠️ até o smoke de prod ([[PROC1]]). Auditor exit 0.)
> 📁 Entradas anteriores em **`improvements_sessions.md`** (101 fechamentos, movidos verbatim — MAN-UX10-UX11-REG, MAN-UX12-REG/F1/REFINE, MAN-O2-F2-B1/B1-DONE, MAN-M10-F2).
> Registro durável de decisões: log do `manager_devplan.md` + `git log`.
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
| S2 | Sync ingere trocas administrativas de picks (as criadas no Sleeper só para montar a ordem do rookie draft) → dono de pick errado no Manager; recorrência anual a cada montagem de ordem — MAN-S2-REG/F1a/F1b/F2/DONE | Alta | ✅ 02/08/2026 (desconto determinístico `board_mirror.py`: π = S⁻¹∘L derivado das fontes canônicas, bijeção obrigatória, armado por **season** — o rollover desarma sozinho. Smoke prod sobre hash `9b4bcf1` (backup `/data/dynasty_pre_s2_smoke_2026-08-02.db`): as **4 posições convergiram para o alvo da F1b** — pos. 2 = Fazenda sem troca, pos. 5 = 3 peat → Cangaceiros (re-rótulo da trade de 29/07), pos. 3/4 corretas; cruzamento com o board do Sleeper confere (`1.05` via `fernandoxmf`); **2ª execução sem alteração** (idempotência em prod); verify do lottery conferindo; pos. 1 e 6–12 + R2/R3 + futuras intactas. Fatia F2-3 desmembrada como [[S5]]. Detalhe no archive) |
| S5 | Tela que **prescreve** a permutação do board ao co-admin (ex-fatia F2-3 do [[S2]]): hoje a montagem é conhecimento tácito e o desconto assume que ela seguiu π; a tela calcula π, emite a lista de permutações e arma o toggle no mesmo fluxo — **não bloqueia** (o desconto já exige bijeção e desliga em board meio-montado) — MAN-S2-DONE | Média | 🔲 |
| S4 | `PlayerHistory` e `Trade` identificam time **só por nome** (sem chave estável no schema); o nome está **dentro do índice UNIQUE de dedupe** do [[F8]]a → pós-rename o mesmo evento não colide e a **idempotência do histórico cai**; `Trade.team_a/team_b` string também quebra a contraparte no timeline (`roster.py:245-250`) — achado colateral da **S3-F1** | Média | 🔲 |
| S3 | Rename de time no Sleeper quebra o match de picks (`Pick` casada por `original_team_name` string; `Team.name` é renomeado e não cascateia) → sync **criaria picks duplicadas**; classe "Brown" (identidade por string) — MAN-S2-F1a/F1b + MAN-S3-F1/F2/DONE | Alta | ✅ 02/08/2026 (match por **id** nos 2 sítios do sync + join da projeção por `team_id` + nome vira display refrescado no passo 11b + `_resolve_traded_pick_identity` como costura do [[S2]]-F2; **sem schema, sem migração**. Smoke prod sobre hash `89dc08d` (gate PROC1, backup `/data/dynasty_pre_s3_smoke_2026-08-02.db`): `/picks` 12 linhas/temporada e 108 picks, `/league` correto, verify do lottery conferindo, dynasty resolvendo no `/trades`. **Sync religado** e a 1ª execução real ingeriu o rename do time 9 **sem duplicação**, projeção #11 preservada. Detalhe no archive) |
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
| M10 | Busca de Jogador: Global + Calculadora (refinado 28/04/2026 — MAN-M10-REFINE; F2 10/08/2026 — MAN-M10-F2: navbar desktop+mobile e autocomplete da calculadora sobre `createPlayerSearch` único; 27→35 testes) | Média | ✅ 10/08/2026 (**smoke prod aprovado — MAN-ARC-BUSCA-DONE, hash `20b346b`; caso Mahomes morto, validação do Michel. Detalhe no archive**) |
| M11 | Teste de auto-containment documental | Média | ✅ 22/04/2026 |
| M12 | Vincular owners a times via tela de admin com lookup do Sleeper | Média | ✅ 22/04/2026 |
| M13 | Página de jogador + "Propor Trade" | Média | ✅ 23/04/2026 |
| M14 | /trades aceitar query params team_a/team_b (pré-requisito M9 + M13) | Média | ✅ 23/04/2026 |
| M15 | Lottery com 6 seeds (inclusão do 7º colocado com 1 bolinha; pool 96) — MAN-M15-REG | Média | ✅ 05/06/2026 |
| M15-FIX | Editor de pesos do lottery: pool/legenda não re-renderizam ao editar + legenda /picks pós-sorteio lê canônico, não o audit | Média | ✅ 05/06/2026 |
| M16 | Lottery aplica ordem sorteada a R2/R3 (deveria ser standings invertido) — corrompe ordem + valores dynasty de R2/R3 — MAN-M16-REG | Alta | ✅ 05/06/2026 |
| OFF26-1 | Janela de cortes selada no Manager (declaração privada + lock/revelação simultânea admin-manual, snapshot M8) — MAN-OFF26-REG/F1/REFINE/F2/SMOKE/ENSAIO/ETAPA2 | Alta | ✅ 07/08/2026 — mecanismo provado em produção **3×** (ensaio Etapa 1 10/10 · Etapa 2 com 12 declarações, hash `52274d01…` · **smoke da urna, que reusa o mesmo motor**); **porta de declaração APOSENTADA** (cortes de 20/08 vão para o Sleeper). Rotas legadas vivas de propósito = motor da urna + rede de regressão da hierarquia; bloco admin de `/cuts` virou [[OFF26-21]] 🔲 |
| OFF26-2 | Keeper sheet consolidada (12 times; keeper+salário+**IR**+Bid Máximo, tabela+CSV) — insumo do Cowork — MAN-OFF26-REG/F1/REFINE/F2/SMOKE/ETAPA2/MAN-OFF26-10(-SMOKE) | Alta | ✅ 07/08/2026 — **origem reescrita (U7): nasce do SYNC**, keepers = roster vivo, sem gate de snapshot; **provisória × definitiva pelo carimbo do sync** (o estado intermediário — revelado e não sincronizado — grita na tela, e foi conferido no smoke em produção) |
| OFF26-3 | Importador de drafts de liga fantasma (rookie linear + FA auction via API, match por sleeper_player_id, preview + helper atômico) — MAN-OFF26-REG | Alta | ✅ 05/06/2026 |
| OFF26-4 | Auditoria de keepers pré-leilão (diff keeper sheet × config real da liga fantasma via API read-only; **gate de integridade do leilão**) — MAN-OFF26-REG/F1/REFINE/PROBE/OWNERCHECK/F2/META | Média | ⚠️ F2 + 34/34 localhost (48/48 do salary_engine intactos) + board REAL atravessando o núcleo; **smoke PARCIAL prod 03/08** (`d83d2f8`: rota+card+seed do `phantom_league_id` OK; o 4º ponto era inalcançável → F2-META expôs a meta da liga sob bloqueio); **falta smoke com sheet real (só a partir de 20/08)**; cobertura do D6 aberta (2/12 sem coluna) |
| OFF26-5 | Runbook do procedimento Cowork (documentação da transcrição supervisionada da keeper sheet → liga fantasma) — MAN-OFF26-REG/MAN-OFF26-5 | Média | ✅ 17/06/2026 (doc — `runbook_cowork_liga_fantasma.md`; reconciliado c/ OFF26-6: roster espelha real 3WR obrigatório, liga permanente + mapa por `sleeper_owner_id`, setup único × trabalho anual, gatilho OFF26-4) |
| OFF26-6 | PoC de viabilidade do Cowork montando a liga fantasma no Sleeper (validação operacional NÃO-código: roteiro de experimento + registro do resultado; gate antes de confiar a FA auction real ao procedimento) — MAN-OFF26-6-7-REG/PoC | Alta | ✅ 17/06/2026 (op — GATE passou: Cowork cria liga + seta keeper/salário sozinho; decisões: liga PERMANENTE redraft, config espelha real 3WR, mapa por `sleeper_owner_id`; achados → OFF26-4 calcula budget/lê designações) |
| OFF26-7 | Dry run E2E da intertemporada: ensaio da cadeia inteira encadeada, foco nas costuras entre módulos (OFF26-6 ⊂ OFF26-7); depende de OFF26-1/2/4 existirem; decisão em aberto (gate único vs. por etapas) — MAN-OFF26-6-7-REG | Alta | 🔲 (op) |
| OFF26-8 | Agente Cowork aplica os cortes do OFF26-1 no roster real do Sleeper (capability operacional NÃO-código) — MAN-OFF26-8-REG | ~~Média~~ **Baixa** | 🔲 (op) **ESVAZIADO pelo redesenho de 06/08**: os cortes de 20/08 são feitos pelos owners direto no Sleeper (não há lista revelada a aplicar). Resíduo = execução **manual** dos drops revelados pela urna (≤1/time) + conferência do admin antes do sync final |
| OFF26-9 | Acoplamento das fases da intertemporada × dependência do ESPN definitivo: o rollover (e a abertura da janela de cortes OFF26-1) depende mesmo do E4-a (ESPN definitivo, deliberadamente tardio) ou só de rollover + `needs_review` zerado? Suspeita do owner: E4-a entrou nas pré-condições por arrasto, atrasando indevidamente o início da intertemporada — investigação (F1 read-only) + correção de redação/microcopy — MAN-OFF26-PHASE-REG/F1/FIX | Alta | ✅ 17/06/2026 (F1 confirmou: abertura só exige `needs_review` zerado, E4-a por arrasto; FIX separou timing × qualidade de dado na D8/pré-condições/microcopy; **smoke do microcopy do passo 6 em prod conferido** — texto lê bem + layout intacto; detalhe no archive) |
| OFF26-10 | **Late drop = a URNA** (`/late_drop`): um bilhete por time (drop **ou** passo), escolha única, janela por horário do admin, lock+hash+revelação reusando `compute_cut_snapshot_hash`, hierarquia owner>admin, contagem agregada sem individualizar, ⛔ flag de estado própria + **bloqueio mútuo com o rollover**, confirmação **inline** (sem `confirm()` nativo), flag de rookie de 1ª **OFF** por default. Revelação = lista de drops; **execução manual no Sleeper** — MAN-OFF26-10-11-REG/-SPEC/-ETAPA2/-F2/-AJUSTES/**-SMOKE** | Alta | ✅ 07/08/2026 — **smoke em prod aprovado** (owner + Rafa; backup 630.784 B): escape do banner exercitado, depósito **pelo celular** sem pop-up, fechamento automático pelo horário provado por acidente, sigilo cruzado, hierarquia, lock/revelação, sheet provisória com aviso, reset limpo. 64 testes + E2E 42/42 |
| OFF26-11 | Importador (OFF26-3) **não distingue keeper de arremate novo** → ingerir keeper **zera a idade do contrato** (dano silencioso, visível só na renovação). **✅ DECIDIDO pelo owner (06/08): opção A — Manager é fonte única**; keeper sheet definitiva como **lista de exclusão**, importador ingere só arremates; garantia board×sheet = auditoria OFF26-4 **antes** do leilão; **sem reconciliação pós-leilão** — MAN-OFF26-10-11-REG → **-SPEC** → **-F2** | Alta | ⚠️ **F2 08/08/2026: implementado, aguardando o smoke real do leilão de 24/08.** `keeper_exclusion.py` (núcleo puro + IO) é o discriminador único; a lista de exclusão é **CONGELADA** por ato de admin (`AppConfig`, com hash) — derivá-la ao vivo no import inverteria o dano (owner readiciona o arremate na liga real → sync → ele viraria "keeper" e seria **excluído**). Só modo **auction**; linear byte-a-byte idêntico ao HEAD (conferido contra o rookie 2025 real). Sheet ausente/provisória/não-congelada **bloqueia** o import; keeper de outro time, pick sem id e roster não mapeado viram **pendência que bloqueia a confirmação**. Alerta de budget passa a somar só arremates (corrige dupla contagem latente). **36 testes novos; 261 no total, verdes** |
| OFF26-12 | **Keeper em IR conta na reserva de $1?** A **8.3.4** manda reservar `(22 − keepers)` e a **1.3** diz que os 2 IR "não são considerados no total de 22" — a regra **não diz** se keeper em IR entra em "keepers". Manager e Sleeper hoje **contam o IR dentro dos 22** (concordam entre si → auditoria sem falso positivo), mas isso deixa o Manager **até $2 mais permissivo que o regulamento** para time com IR (3 times hoje). **Decisão de REGRA DE LIGA, não de implementação**; se a leitura (b) vencer, o ajuste mexe em `salary_engine.draft_budget` — MAN-OFF26-4-LABELS/SLOTS | Baixa | 🔲 (decisão do owner) |
| OFF26-13 | **Time com mais de 22 keepers não cabe no board** — F1 03/08: o time é o **achane** (24 = **22 ativos + 2 IR**, ambiguidade dissolvida), e **a hipótese "os cortes resolvem sozinhos" está REFUTADA** (ele está em **$195, abaixo do cap** — nada o obriga a cortar; os 2 times acima do cap **cabem** no board). +**5 times em 22 exatos** (folga zero). **T4: o teto de 22 não é validado em lugar nenhum** (`MAX_ROSTER` só divide no `draft_budget`, e o `max(0,…)` **apaga o excedente**), enquanto `MAX_IR` **é** enforçado — assimetria registrada: o regulamento permite **24** (22 + 2 IR, item 1.3) e o board da fantasma comporta **22 designações** (22 rodadas — slot de IR **não é** slot de draft). **1 time está em 24 hoje** (medido ao vivo); se chegar assim em 20/08, **2 keepers ficam EXPOSTOS ao leilão** pelo achado do [[OFF26-4]]. **Segunda causa de time não populável**, ao lado do teto de budget ([[OFF26-10]]) — e **não se resolve com o late drop** (1 drop não tira 2 excedentes). Decisão em aberto: corte adicional obrigatório × exceção administrativa — MAN-OFF26-4-LABELS/SLOTS | Alta | 🔲 |
| OFF26-14 | **Duas contagens de cap convivem — as telas de roster EXCLUEM o salário de IR.** Decisão do owner: **o IR CONTA no cap** → o grupo que exclui está desalinhado da regra, e é o que o owner olha para cortar em 20/08 (`$186/$14` na tela × `$195` na régua do leilão; **3 times, $14** de divergência). **T3 — a réplica está toda no lado errado:** o lado que INCLUI IR tem **1 fonte** (`draft_budget`, [[F10]] preservada); o que EXCLUI tem **6** (`active_salary` + **5 somas inline** em `roster.py:89`, `league.py:22/99`, `admin.py:159/160`). **T5 — keeper sheet e auditoria [[OFF26-4]] consomem o MESMO número (com IR), NÃO divergem** — a cadeia do leilão é coerente; o descompasso é **tela do owner × leilão**. **T2 — sem decisão registrada:** filtro explícito desde o commit inicial, **sem comentário e sem teste**, e o gap **já estava anotado na F1 do [[OFF26-1]]** como "decisão pendente". **T6 — regulamento SILENCIOSO** sobre salário de IR no cap (o 1.3 fala de **contagem**, não de folha; a única exclusão de folha é o 7.1.8, sobre FAAB) → não contradiz nem confirma o owner. ⛔ **T4 — a string "cabe até 24" NÃO existe no código**; não há terceiro teto de roster. Laterais: `Team.total_salary()` é **código morto**, a keeper sheet **não marca quem está em IR**, `reserve_slots` nunca é lido — MAN-OFF26-14-F1 | Alta | ⚠️ **F2 04/08: NÃO unificou — rotulou.** As 7 superfícies passam a exibir **"cap ativo" × "folha total"** quando o time tem IR (achane: **$186 × $195**); 9 times sem IR seguem com **um número só**. `active_salary`, as 5 somas inline e `draft_budget` **intocados** (nenhuma linha de cálculo removida). 48/48 + 34/34. ⚠️ **A F2 foi REVERTIDA pelo [[OFF26-16]]** (decisão do owner: régua única) — o item fecha ✅ pelo smoke de 04/08, com o racional preservado no registro |
| OFF26-15 | **Keeper sheet não marcava quem está em IR** — keeper em IR ocupa designação no board e omiti-lo o **expõe ao leilão** — MAN-OFF26-14-F2 → MAN-OFF26-10 | Alta | ✅ 07/08/2026 — coluna **IR** na tabela, no CSV e no cabeçalho do time (5 marcados no dry-run); coberto pelo smoke da sheet |
| OFF26-16 | **Régua ÚNICA de folha — o IR conta no cap, sempre.** Decisão do owner (04/08) **reverte a F2 do [[OFF26-14]]**: o número sem IR **não media nada**, então rotular as duas réguas deixou de fazer sentido. As **6 fontes** (`active_salary` + 5 somas inline) foram substituídas por **uma**: `salary_engine.roster_salary` (pura, sem DB) → `Team.total_salary()`. `active_salary` **removido** (o nome mentia); chave da API `active_salary` → `salary_total`. O rótulo duplo, o banner aditivo e a legenda da régua do leilão **saíram** das 7 superfícies. Banner de IR virou **informativo de escalação** (nomes, sem aritmética). **Pré-requisito cumprido:** cobertura escrita **antes** (`cap_regua_test.py`, **14 testes**, incl. **guarda anti-réplica** que falha se a soma filtrando IR ou o `active_salary` voltarem). Achane: **$195 usado, $5 restante**; os 9 sem IR **idênticos** — MAN-OFF26-16 | Alta | ✅ 04/08/2026 (smoke consolidado de prod PASSOU nos 6 pontos: roster do achane $195/$5 c/ banner de nomes e tabela sem coluna de acoes; time sem IR inalterado; Cap Projector com `min $3` em 4 spots e `min $0` em 1 spot (fencepost vivo); `/trades` OK com o rename da chave; League Hub coerente com o roster; **sync manual manteve os 5 em IR**) |
| OFF26-17 | `Team.total_salary()` era **código morto** (zero consumidores). A F2 o promoveu a fonte da folha; o [[OFF26-16]] o tornou **a única entrada ORM de salário do sistema** (delega a `salary_engine.roster_salary`), com `active_salary` **removido**. **Resíduo resolvido** — a régua abandonada virou a régua oficial. Fecha junto com o smoke do OFF26-16 — MAN-OFF26-14-F2/MAN-OFF26-16 | Baixa | ✅ 04/08/2026 (fecha junto com o OFF26-16 no smoke consolidado) |
| OFF26-18 | **Fencepost na reserva de $1 do `draft_budget`** — reservava-se $1 por vaga, inclusive **pela vaga que o próprio lance preenche**, deixando o último dólar **impossível de gastar** e o Manager **$1 mais restritivo que o Sleeper** em todo time com ≥1 vaga. Corrigido para `max(0, empty_spots − 1)`; o `max(0, …)` é obrigatório (com 0 vagas a subtração daria **−1** e inflaria o budget). **Fonte única → os 7 consumidores herdaram**, zero réplica criada. Efeito medido: **+$1 nos 6 times com vaga**, **$0 nos 6 sem vaga**. Distinção de leitura da **8.3.4** registrada (texto literal × leitura operacional, que é a que a plataforma implementa). ⚠️ **Conferência aritmética:** o prompt registrou o experimento como "$29 (não $28)"; as contas dão **$29 (antiga)** e **$30 (corrigida)** — as recusas de 02/08 limitavam o teto real a **[29, 31]**, que **não discriminava** as fórmulas. ✅ **FÓRMULA CONFIRMADA POR MEDIÇÃO DIRETA (04/08):** teste decisivo na fantasma — Team 5, **$60 gastos / 16 vagas** → antiga preveria **$124**, corrigida **$125**; **designação de $125 ACEITA** ⇒ **a fórmula rival está falsificada** (aceite acima do teto dela) e a corrigida **acerta o limiar exato**. Sustentação deixou de ser dedutiva. Board reconferido por leitura: 24 designações, coluna 5 com 6 e $60, Gibbs removido — MAN-OFF26-18/-CONF | Alta | ✅ 04/08/2026 (fórmula confirmada por medição direta em 04/08 + **smoke prod OK: `min $3` em 4 spots, `min $0` em 1 spot** — o fencepost está vivo na tela) |
| F9 | `bulk_register` (/auction) cria jogadores sem SalaryHistory — risco de dano silencioso já existente (achado de MAN-OFF26-3-F1; exige F1 de avaliação de dano antes do fix) | Alta | ⚠️ |
| F10 | `draft_budget` replicado em JS no cap_projector (viola "1 fonte por modo de render", T2-FIX-2; cliente deve consumir endpoint canônico) — achado de MAN-OFF26-3-F1 | Média | ✅ 12/06/2026 (réplica eliminada + smoke prod OK: $157/$43/$38/5 spots conferido) |
| M17 | Personalização por usuário logado: home + cap widget + 8 surfaces derivam de `current_user.team_rel` (fonte única `inject_user_team`; réplica JS do chip removida) — prompt MAN-M15-REG (ID remapeado: M15 ocupado) | Alta | ⚠️ |
| M18 | Timestamps no fuso do usuário: fonte única (`timeutil.utc_iso` + macro `local_dt` + JS `formatLocalDT`); ~11 sites migrados; armazenamento UTC mantido — prompt MAN-M16-REG (ID remapeado: M16 ocupado) | Média | ✅ 09/06/2026 (validado em prod: sync 11:47 BRT → "11:47", não 14:47 UTC) |
| E1 | Import ESPN robusto end-to-end no Render: upload manual do PDF + degradação graciosa (sem 500) + estado de review em FS gravável + parser 299→300 — MAN-E1-REG/F1/F2/FIX | Alta | ✅ 08/06/2026 (validado em prod: upload → review 300, sem 500) |
| E2 | Camada de dados: store de valores ESPN de rookie keyed por `sleeper_id` (resolve not_found+approx via pool global do Sleeper, nome+team) — consumido pelo salário do rookie draft (OFF26-3) + board DP1; rejeita Sleeper-sync e stub-$1 — MAN-E2 REG/F1/REFINE/F2 | Alta | ⚠️ store implementado + validado em localhost (12/12); store validável em prod via import; aplicação no draft só e2e no rookie draft real (~ago) |
| E3 | Import ESPN upload-only: remover a opção de URL (download inviável em prod — ESPN bloqueia IP do Render); remoção completa UI + fetch server-side + degradação graciosa associada — MAN-E3-REG/F2 (owner: opção a, remoção completa) | Baixa/Média | ⚠️ F2 localhost (48/48; UI/fetch/constante removidos, guard %PDF do upload preservado) — **aguarda smoke prod** (upload real → review → confirm; gate PROC1) |
| E2-RISK | Review do import ESPN oferece rookie como match fuzzy de veterano (falso-positivo "Carnell Tate"~"Darnell Mooney" 0.665) → confirm errado contamina `espn_ref_value` do veterano (classe "Brown"). **F2: default neutro no select + confirm gated (sem confirm-por-inércia); raiz do matcher → E4-a** — MAN-E2RISK-REG/F1/F1B/F2/DONE | Média | ✅ 23/06/2026 (smoke prod via E4-a: default neutro + gate confirmados, nenhuma escrita por inércia; detalhe no archive) |
| E4 | **Guarda-chuva** — redesenho da camada de valor ESPN (`espn_ref_value` por `sleeper_id`); F1 de design concluída → fatiado em E4-a/b/c — MAN-E4-F1 | — | 🔲 (fatiado) |
| E4-a | Matcher do import ESPN resolve entrada → `sleeper_id` (pool global, nome+team Brown-safe), não fuzzy contra roster; escreve via id; sem schema. Elimina o "Brown" na raiz + troca corrupção→miss. **Absorve o conserto do matcher ex-E2-RISK** — MAN-E4-F1/F2/PRODF1/F2-EixoA/DONE | Alta | ✅ 23/06/2026 (smoke prod do import real: filtro D/ST/K ativo, Eixo A fechado sem regressão skill; split 211/5/84/62; commit 97b90ed; detalhe no archive) |
| E4-b | Saneamento de `sleeper_id`: F1 refutou backfill — os 2 nulos (Hollywood Brown=dup de Marquise Brown; Cameron Ward=dup de Cam Ward) são **duplicatas órfãs → DELETE** (+ 1 PlayerHistory stray) via rota admin auditável em PROD; **guard** (dedup-por-sid + `needs_review` no import_csv) p/ a causa-raiz. Sem schema — MAN-E4-F1/E4-b-F1/F2 | Média | ✅ 09/06/2026 (limpeza executada em prod: 2 removidos, 278 players, 0 sid nulo, canônicos intactos) |
| E4-c | **Guarda-chuva** — store canônico de valor ESPN `(sleeper_id, season)`; F1 de migração concluída → sub-fatiado em E4-c-1/E4-c-2 — MAN-E4-c-F1 | — | 🔲 (sub-fatiado) |
| E4-c-1 | Fundação do store (aditivo/reversível): tabela `espn_value_store (sleeper_id,season)[raw,adjusted,is_final]` via `db.create_all()` + backfill da coluna (Migration 7, season 2026 prelim) + helper único `set_espn_value` nos 8 escritores + badge PROV repontada ao store. **Entrega o store ao DP1.** — MAN-E4-c-F1/F2 | Alta | ✅ 09/06/2026 (backfill em prod: 273 linhas, schema ok, store==coluna, coluna intocada) |
| E4-c-2 | Limpeza do store (destrutivo/isolado): DROP ESPNValue (vazio) + generalizar/migrar RookieEspnValue. Único passo irreversível-sem-backup; higiene após E4-c-1; **não bloqueia DP1** — MAN-E4-c-F1 | Baixa (higiene) | 🔲 |
| E5 | Microcopy stale da tela de review do import ESPN: cabeçalho "Não Encontrados — todos receberão $1" contradiz o pipeline pós-E2 (not_found com valor>0 resolvido a sleeper_id → store, salário `floor(ESPN×1.2)`; "$1" só vale p/ subclasses excluídas). Travou operação real de co-admin em prod. Alinhar comunicação da tela ao pipeline real (destino por classe) — ciclo F1 read-only → F2 — MAN-E5-REG/F1/F2 | Média | ⚠️ F2 localhost (48/48; split server-side de "Não Encontrados" via classificador único; textos stale corrigidos; JS pós-confirm lê `rookie_store`; **comportamento intacto**) — **aguarda smoke prod** (tela de review + confirm com PDF real; gate PROC1: hash live = commit) |
| DP1 | Board de planejamento de cap pré-draft: rookies entrantes com `espn_ref_value` + salário projetado `floor(ESPN×1.2)` + simulação de impacto no cap (projeção, não contrato) — lê o **store canônico** — MAN-DP1-REG | A definir | ⚠️ (F2 implementada 10/06; smoke em prod pendente) |
| DP2 | Cadeia única de planejamento no cap projector: board DP1 parte do cenário keep/corte (não mais roster integral) + summary sticky unificado refletindo cortes + rookies; estende o endpoint canônico do F10 com `rookie_sids` (1 fonte) — MAN-DP2-REG (revisão consciente da base do DP1-F2) | Média | ✅ 15/06/2026 (smoke de prod confirmado) |
| DP3 | Composição da lista do board de rookie draft: hoje lista `RookieEspnValue` (não-rosterados ESPN-valorados, Top-300) → mostra veteranos/rookies de classes antigas e omite rookies fora do Top-300; owner decidiu listar só rookies da classe entrante (D1) via pool global do Sleeper, ESPN quando houver e $1 quando não (D2), só status ativo NFL (D3), snapshot materializado (D4), tela alt. A (D5) — MAN-DP3-REG/F1/REFINE/F2/CLOSE | Alta | ✅ 31/07/2026 (smoke prod OK sobre hash `e12fdef`: captura idempotente 148→0, board ordenado, não-rookies fora, busca/filtro sem reload, cenário na barra fixa; **ressalva**: board mostra classe do snapshot de junho — completude depende do **F13**; detalhe no archive) |
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
| O2 | Enriquecer página do jogador: contexto NFL (time + **link do time da liga** + **idade** + depth chart — 7 dimensões pós-roteamento (b) do [[UX12]]) + stats históricas + ECR/ADP + schedule — MAN-O2-F1/MAN-UX12-REFINE/MAN-O2-F2-B1/**MAN-O2-B1-DONE** | Média | ⚠️ **Batch 1 VALIDADO EM PROD 08/08/2026** (PROC1: hash `2ed0b4a` live; DJ Moore completo, link cruzado Gainwell → franquia dele, validação do Michel; `nfl_context.py` núcleo puro + 19 testes, página nunca faz rede, idade derivada. Ressalva: degradação fora-do-pool **não exercida em prod** — pool de prod mais fresco que o local; coberta por unit test) — **Batch 2 (stats + schedule) pendente** |
| L1 | League Hub: visão geral da liga + detalhe por time | Alta | ✅ 23/04/2026 |
| L2 | League Hub season mode: matchups, schedule, standings | Baixa | 🔲 |
| L4 | **Qual evento reabre a exibição de projeção no ciclo seguinte?** O gate do [[L3]] fecha quando `rollover_done` vira `"true"` — e **nenhum sítio grava `"false"` de volta** (medido na MAN-L3-FIX-F1): `_seed_app_config` só insere chave ausente, o `--reset` do ensaio não toca a flag. Hoje a projeção some no rollover e **não volta sozinha** na intertemporada seguinte. Design pequeno, mas toca `app_config` — **contrato externo consumido pelo Optimizer** — então a decisão (que evento zera: fechar a season? abrir o passo 1? flag própria de exibição?) é do owner — MAN-L3-FIX | Baixa | 🔲 |
| L3 | Projeção de cap por time na `/league` **e no `/team/<id>`** (agregado da season seguinte via valorização × ESPN, antes só no cap_projector time a time) — MAN-L3-F1/MAN-L3/MAN-L3-FIX-F1/MAN-L3-FIX/MAN-L3-FIX-UX/**MAN-L3-FIX-UX2** | A definir | ✅ 13/08/2026 (**smoke visual do owner aprovado** na `/league` e no `/team/<id>`; prod no hash `7883cd9`, [[PROC1]] por artefato servido. Arco de 6 sessões num dia: composição extraída p/ helper único (`compose_budget`, refactor puro provado por medição) → card reorientado a planejamento (3 zonas) → 2 fixes de layout. **Detalhe no archive**, incl. as **3 gerações do instrumento de validação** e as lições que originaram o [[O7]]. Resíduos: [[L4]] · [[UX16]] · [[UX17]]) |
| N1 | Redesign navbar: estrutura com dropdowns + acesso rápido aos times | Média | ✅ 23/04/2026 |
| C1 | Cap projector: modo "drop programado" para simular liberações de cap | Média | 🔲 |
| M8-PERM | Lottery: simulação aberta a owners + bloqueio server-side pós-oficial | Média | ✅ 23/04/2026 |
| T2-FIX | Picks Rd2+ sem dynasty value no preview/proposta de trade | Média | ✅ 24/04/2026 |
| T2-FIX-2 | Réplica JS pickFcSid em trades.html (fix estrutural — `/api/picks` pré-resolve dynasty_value) | Alta | ✅ 24/04/2026 |
| IR-CLEANUP | Remover seletor manual de IR no roster (sync Sleeper já é autoritativo) | Baixa | ⚠️ 04/08/2026 — **executado**. Argumento ficou mais forte com o [[OFF26-16]]: com o IR contando no cap, o toggle passou a **aparentar mexer na folha salarial** sem mexer em nada — de ruído inócuo a **controle enganoso**. Removidos endpoint, handler, os 2 botões e **a coluna `col-actions` inteira** (existia só p/ o toggle → `/` e `/team/<id>` agora têm a mesma forma de tabela) + CSS morto + import órfão de `MAX_IR`. **Preservados** `is_on_ir`, badge 🏥, `MAX_IR`, régua de cap e o banner de escalação (leitura, não controle). **Caveat de UX descartado** com motivo registrado. 5 em IR seguem em IR; 12 valores de cap idênticos. ✅ **smoke prod OK 04/08** — inclusive o **sync manual mantendo os 5 em IR**, que é a prova de que a autoridade do Sleeper funciona sem o toggle |
| OFF26-19 | **Jogador em IR no Ano 4 não aparece como candidato a renovação** — `renewal_candidates` deriva de `active_players` (herança do filtro de IR que o [[OFF26-16]] removeu das telas de cap; sobreviveu por ser pergunta de **contrato**, não de folha). O contrato expiraria **sem decisão registrada** e o salário seguinte sairia errado — dano silencioso, família do [[OFF26-11]]. Perfil de risco é justamente fim de contrato **+** lesão. **Dano hoje: ZERO, verificado** — a liga inteira está em ano 1 (50) e ano 2 (198), **nenhum no Ano 4**; o primeiro só existe depois de **2 rollovers**. Atemporal, porém: não caduca, está adormecido. **Correção exige F1 própria** (toca o fluxo de renovações; verificar se o filtro se repete em outras superfícies de contrato) — MAN-IR-CLEANUP | Baixa | 🔲 |
| OFF26-20 | ⛔ **`fa_waiver` está FORA de `_WAIVER_TYPES`** — os **37** jogadores cujo rótulo diz *"Waiver / Free Agent"* **nunca recebem a regra de waiver** (0,8 × ESPN no ano 2); caem sempre na valorização. **A hipótese "é cicatriz de importação" foi FALSIFICADA: há 5 em Ano 1** (Dike, Noel, Willis, Gadsden, Shough) com a bifurcação **pendente para o rollover de 18/08**. Dano hoje **zero por coincidência** (ESPN provisória = 1.0 ⇒ as duas regras dão $1) — mas **a ESPN definitiva entra em 18/08, o mesmo dia**, e com valor real o erro chega a −$6 em ESPN $20, **selado na sheet de 20/08**. ⚠️ **2º achado, independente e maior: a coluna PROJ do roster não é o que o rollover fará** — `Player.projected_next_salary()` usa `compute_salary_for_year`, que **reconstrói o contrato do zero e descarta o salário armazenado** (viola "o DB é autoridade sobre salário/ano"); diverge do rollover em **26 dos 248**, sempre superestimando, **+$62** no total e **+$18 num só jogador** (Omarion Hampton: tela $44, rollover $26). Os maiores erros são de **rookie**, não de waiver/FA. **Watson explicado:** $4 = `floor(0,8 × 6)` dentro da reconstrução; o rollover fará **$3**. **T5 — 3 funções de "próximo salário"**: as 2 do backend concordam, a da tela não. ⚠️ **F1B (05/08) INVERTEU a conclusão pela arbitragem contra o regulamento:** os **85** têm `drop` **e** reaquisição **REAIS** de 2025 no chain do Sleeper ⇒ pela **6.1** o contrato **recomeçou** (ano 1 em 2025, **ano 2 em 2026**), logo **`contract_start_season` está CERTO e `contract_year=2` está ERRADO**; a **6.8** só salvaria quem foi readquirido pelo **próprio** owner, e **73 foram por time DIFERENTE**. ⛔ **73 contratos receberão a REGRA ERRADA no rollover de 18/08** (valorização em vez de 0,8 × ESPN) e entram **selados** na sheet de 20/08 — e para esses **a TELA acerta e o ROLLOVER erra**; para os 21 rookies é o oposto. ⇒ **corrigir as TRÊS coisas: a tela, o DADO e o enum.** **Causa-raiz do vocabulário:** o rebuild **F8** grava `event_type` **dentro** de `acquisition_type` (`sync_sleeper.py:1217`) — **100%** dos `fa_waiver`/`fa_auction`/`free_agent` nasceram aí e **0%** dos `waiver`/`auction_draft`/`rookie_draft` ⇒ **acidente, não decisão** (e os 17 `waiver` que o owner validou são justamente os que o F8 não tocou). +A tela erra nos **dois sentidos** (Jeanty **−$12**), não "sempre para cima". ⚠️ **F1C (05/08) CORRIGE O CRITÉRIO da F1B: o discriminador é o CANAL de aquisição, não o time.** Regra do owner: **waiver (FAAB) CARREGA o contrato** para qualquer time; **FA (add grátis) entra SEM contrato** e vai a 0,8 × 1,2 × ESPN no ano seguinte. A distinção **nunca se perdeu** — vive em `sync_sleeper.py:911-915`, mapeando o `tx["type"]` da API (`waiver`→`fa_waiver`, `free_agent`→`free_agent`), e o `acquisition_type` bate com o último evento em **100%** dos 85. Censo pelo canal: **32 waiver = CERTOS** (carregam contrato legitimamente), **29 FA = ERRADOS** (é o grupo do prazo), **24 do leilão de 2025 = contagem errada mas SEM efeito em 2026** (valorização dá o mesmo número em qualquer ano ≥2; só pesa na renovação de 2029). ⛔ **"73 errados" CAI → são 29**; delta hoje **+$6**, a ESPN $10 **+$87**, a $20 **+$174** (o rollover **subcobra**). ⛔ **E o achado da F1 sobre `fa_waiver` INVERTE: estar fora de `_WAIVER_TYPES` está CERTO** (waiver carrega contrato ⇒ valorização), assim como `free_agent` estar dentro. Achado novo de sinal trocado: o enum **`waiver`** (17) está **dentro** e não deveria — **impacto 2026 zero** (todos em ano 2 ⇒ `next_yr=3`, a regra não dispara). **T4 — ambiguidade do 1,2 eliminada:** o fator é aplicado na **escrita** (`espn_pdf_parser.py:129`), então `0.80 × espn_ref_value` **já é** 0,8 × 1,2 × raw ✅. **Sobrevivem intactos:** os 21 rookies com tela errada, o Cap Projector × PROJ, e a `salary_history` vazia. **Indeterminado declarado:** os 5 `fa_waiver` em ano 1 (contrato nascido de claim — a 6.6 literal manda 0,8, a regra do owner sugere valorização). ✅ **VERIF (05/08) verificou os 34 nominalmente contra a API** (chain 2026→2025→2024, 1125 txs, 9 drafts; os 173 refs `tx:` resolvem todos): **34/34 abrem em 2025, ZERO em 2024** — a premissa da data **confirmada**. ⛔ **Mas o eixo do erro é OUTRO:** os **29 `free_agent`** têm o **dado** errado (`contract_year=2`→1) e os **5 `fa_waiver`** têm o **dado certo**, expostos pelo **enum** — **os 34 receberão valorização e os 34 deveriam receber 0,8 × ESPN REF, por causas opostas**. ✅ Pôr `fa_waiver` em `_WAIVER_TYPES` alcança **só os 5** (os 32 estão em `cy=2` ⇒ `next_yr=3`). ⛔ **O "+$6" é ilusão do ESPN provisório** (134/248 em ≤ 1.0; definitiva em 18/08): com ESPN real **32/34** divergem e o delta vai a **+$33** (ESPN 4) … **+$168** (20), **subcobrando**. **21 CORRIGIR** (com `tx:` + data), **3 CORRETO** (dado), **10 AMBÍGUO**. ⚠️ **Falsificação parcial: Kenny Gainwell** tem aquisição de **2024-11-27 pelo mesmo owner** que o readquiriu em 2025 — **6.8 literal**, e sob ela **o banco está CERTO**; **Jake Bates** é candidato mais fraco (dono intermediário). ⛔ **Jaylin Noel tinha contrato prévio** (leilão 2025, r2p17 $1, do próprio time) — refuta *"os 5 entraram sem contrato"*. **Aguardando aprovação nominal do owner; correção é prompt separado.** ✅ **CANAL (05/08-pt4) fecha a certeza: Gainwell resolvido pelo canal — `tx:1268069831555424256`, `type: "free_agent"`, sem bid, reconfirmado AO VIVO — e ENTRA: o grupo é 22.** A "6.8 literal" da VERIF cai (6.8 só existe no canal waiver); 21/21 reconfirmados `free_agent` um a um + invariante 225/225 waivers com bid × 661/661 FA sem. Correção = **`contract_year` 2→1, um campo só** ($28→$33 hoje, +$5); ⚠️ **vão canônico:** não há porta para `contract_year` fora do M2 — o prompt de correção a cria no molde M2 (escrita + `PlayerHistory`). **T4 (reconferência do vivo) bloqueada desta máquina — comando sqlite3 pronto no doc para o Render Shell.** — MAN-OFF26-20-F1/-F1B/-F1C/-VERIF/-CANAL | **Alta** | ⚠️ (implementado; resta smoke pós-deploy) |
| OFF26-21 | **Motor legado de `/cuts` perdeu a última função** — o bloco admin (abrir/lock/revelação/suprir) só sobrevivera por ser o **produtor de fallback da keeper sheet**, e o U7 tirou isso dele: virou motor sem consumidor, e é a única porta da UI capaz de abrir a janela grande por engano durante a urna (hoje mitigado por rótulo, não por trava). ⚠️ As **rotas** legadas continuam necessárias (motor da urna + rede de regressão) — o que se discute é a TELA — MAN-OFF26-10-SMOKE | Baixa | 🔲 |
| OFF26-22 | **A auditoria de keepers ([[OFF26-4]]) audita sheet PROVISÓRIA como se fosse definitiva** — `keeper_audit.build_sheet` ainda tem o gate `if not raw.get("revealed")`, mas desde o U7 `_build_keeper_sheet` devolve `revealed: True` **incondicionalmente**: o ramo virou **código morto** e o único bloqueio por falta de insumo morreu com ele. O estágio existe e está calculado — `build_sheet` só o **descarta** (junto com `stage_label`/`sync_timestamp`/`late_drop`). O veredito "liberada" sobre sheet provisória é liberação sobre dado que ainda vai mudar. ⚠️ O importador do [[OFF26-11]] **não** depende disso (lê o selo direto da fonte); o gap é da auditoria. Fix exige propagar `stage` sem mudar o formato que o núcleo puro + as 34 fixtures congeladas consomem — MAN-OFF26-11-F2 (Passo 0) → **MAN-OFF26-22** | Média | ⚠️ **CORRIGIDO 08/08/2026 — opção (b) do owner: roda e DESQUALIFICA o veredito.** Três estados: definitiva = idêntico a hoje · **provisória = `nao_qualificada`** (relatório completo, divergências listadas, **"ABERTURA LIBERADA" impossível**) · indisponível = bloqueio por falta de insumo **revivido** com condição que dispara. O carimbo viaja em `stage_meta` e `run_audit` o **remove antes** do núcleo — **34/34 sem editar teste nem fixture**. ⛔ Nenhuma segunda definição de "definitiva" (a fonte segue sendo `routes/cuts.py`). **Causa estrutural do bug achada:** a camada de leitura **não tinha teste nenhum** — agora tem 25. **286 verdes.** Falta a conferência em prod (PROC1) |
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
| UX8 | Densidade vertical do cap projector: foto **ao lado** do nome (não acima) — recupera densidade em telas 20+ jogadores (decisão owner: opção B, mock 15/06/2026). **F2 ✅ localhost:** flexada `.player-name-cell` (1 regra CSS, classe exclusiva → zero blast radius); "tag malformada" da F1 era falso positivo (artefato de Grep); 48/48 — MAN-UX8-REG/F1/F2 | Baixa/Média | ✅ 15/06/2026 (smoke de prod) |
| DATA-1 | Badges TRADE e REVISÃO removidos da macro de listagem (info pertence à timeline/admin, não à listagem) | Média | ✅ 24/04/2026 |
| T3 | Valores redraft do FantasyCalc no Trade Manager (modelo 3 — duas barras independentes dynasty + redraft) | Média | ✅ 27/04/2026 |
| T3-FIX-UX | Migrar barras dynasty + redraft de dual-fill (T2 pattern) para delta-pointing + corrigir overflow mobile + redraft no modal preview + descrição de trade em formato "de/para" 2-colunas + alinhamento vertical entre colunas (5 sub-iterações, owner-driven via screenshot mobile) | Média | ✅ 27-28/04/2026 |
| AUD1 | Auditoria estrutural read-only do codebase: 6 lentes de incidentes históricos (F1-only — achados viram itens próprios; Lente 6 = test drive do MAN-METH-REG) — MAN-AUD1-REG/F1 | Alta | ✅ 11/06/2026 (achados absorvidos: F11, F12, E4-d, M19, M20, DOC1) |
| PROC1 | Processo: gate de ✅ com smoke de prod exige confirmar que o hash deployado live é o commit validado (não basta commitado/pushado) — casos-âncora E1 + E4-a (927831a×97b90ed) — MAN-PROC1-REG/F1/DONE | Média | ✅ 23/06/2026 (Forma 1: regra afinada no bullet de gate da "Checklist de fim de sessão" do DEV_METHODOLOGY, transversal; robustez extra → PROC2; detalhe no archive) |
| PROC2 | Surfacear o commit deployado (`RENDER_GIT_COMMIT`) em superfície administrativa (provável `/admin`) — robustez além da disciplina do [[PROC1]] (follow-up da ressalva F1; é código). **Repriorizado Baixa → Média em 14/08/2026 (MAN-CLOSE-LOTE-14-08):** a sessão MAN-UX-BID0-F2 **não conseguiu provar o PROC1 por artefato servido** — o diff era só Python + templates autenticados, **nenhum arquivo público mudou** — e a confirmação degradou para **evidência circunstancial de restart**. Este item elimina a classe inteira de lacuna (prova direta, independente de o diff ter tocado arquivo público) — MAN-PROC2 | Média | 🔲 |
| OPS1 | Higiene do working tree local: `dynasty.db` aparece **modificado** a cada sessão (banco vivo de dev versionado como seed), **6 handoffs soltos** na raiz (1 modificado + 5 untracked) e **2 backups pré-[[O5]]** untracked. Decidir, item a item, o que vai para `.gitignore`, o que migra para pasta de archive e o que é **descartado** — o ruído hoje polui todo `git status` e todo diffstat de fim de sessão, que é o instrumento de conferência do push. ⚠️ **Registro apenas — nenhuma ação de limpeza executada** (`dynasty.db` é o artefato consumido pelo `fantasy_optimizer`/`predictor` **e** o seed do 1º deploy no Render: ignorá-lo tem consequência fora do repo e é decisão do owner) — MAN-CLOSE-LOTE-14-08 | Baixa | 🔲 |
| F11 | Rollover de season duplicado e divergente: `/api/admin/rollover/apply` (sem gate de etapas, sem check `rollover_done`, NÃO avança `current_season`) × `/api/offseason/rollover` (gated) — ambos vivos na UI; dupla execução incrementa contratos 2× — achado AUD1 Lente 2 | Alta | ✅ 12/06/2026 (prod LIMPO + fix Opção A + smoke prod OK) |
| F11-FIX-UX | Microcopy do card "Season Rollover (preview)" e do passo 2 do fluxo pré-temporada no /admin: linguagem de owner (prévia × aplicação real na Intertemporada), link p/ /offseason, sem nº de step e sem season hardcoded — carona da sessão F10 (padrão N1-FIX/T3-FIX-UX) | Baixa | ✅ 15/06/2026 (fecha junto com o [[UX9]] — sintoma do passo 2 eliminado pela raiz) |
| UX9 | Passo 2 do card "Ordem do Fluxo Pré-Temporada" (/admin) fragmenta em colunas. **F2 ✅ localhost:** body de cada passo envolto num `<span class="step-body">` (2 flex items: badge+body) → texto+link fluem inline em ordem; estrutural, não comprimento; local, zero blast radius; 48/48. Fecha o done do F11-FIX-UX quando passar em prod — MAN-UX9-REG/F1/F2 | Baixa | ✅ 15/06/2026 (smoke de prod) |
| F12 | `run_import` sobrescreve salary/contract_year a cada boot com CSV presente (dev local), sem SalaryHistory — reverte silenciosamente rollover/correções locais; coluna `salary_2025` hardcoded — achado AUD1 Lente 2 | Média | ✅ 15/06/2026 (bootstrap one-shot via flag `csv_bootstrap_done`; critério dev-local, sem smoke de prod) |
| F13 | Versionamento do cache do pool Sleeper (`.sleeper_players_cache.json`, ~15 MB, trackeado no git): mtime pós-deploy reinicia o TTL de 168h (frescor enganoso), cada refresh commitado incha a história, e em prod a raiz read-only (doutrina E1) faz a gravação do cache falhar silenciosamente → pós-TTL, todo load re-baixa ~15 MB da API. Cache em `dirname(DYNASTY_DB)` (volume, padrão E1) + gitignore + validade por carimbo `fetched_at` no conteúdo (não mtime) — achado colateral do smoke DP3-F2 — MAN-DP3-COMMIT/CLOSE/**F13-F1/F2/CLOSE** | **Alta** (janela: rookie draft ago) | ✅ 31/07/2026 (smoke prod OK sobre hash `2cd8de3`: recaptura = **287** (145 entraram, 142 atualizados, 6 saíram por corte), 2ª captura 0/0 sem novo download; board 287 c/ 12 do import ESPN, 6 valorados; busca/filtro no navegador; detalhe no archive; **pendência**: frescor sobreviver ao 2º deploy → próximo release) |
| F14 | Nomes do board de rookies (DP3) vêm do pool do Sleeper e perderam sufixos de geração (Jr./II/III) presentes na fonte ESPN — cosmético, **não** afeta identidade (resolvida por `sleeper_id`) — achado do smoke MAN-F13-CLOSE | Baixa (cosmético) | 🔲 |
| F15 | **Remover edição manual de picks** (obsoleta pós-[[S2]]) — o PATCH `/api/picks/<id>` e o modal ✎ do board nasceram quando o dono da pick podia divergir no Manager; desde o S2 o sync é autoridade. Achado MAN-UX20-F1: o ✎ aparece para TODOS (gate só server-side), falha silenciosa para não-admin (403 engolido). UI sai de carona no [[UX20]]; backend: conferir consumidores além do board antes de remover — **MAN-PICKEDIT-REG** | Média | 🔲 |
| E4-d | Matching frouxo nas portas do /auction: single-entry FA/rookie matcha player por nome exato sem resolver sid (guard E4-b ausente — classe órfão) + upload Excel matcha Team por substring `%name%` — achado AUD1 Lente 4 | Baixa/Média | 🔲 |
| M19 | Validação de pesos do lottery só existe no client (JS floor/mín-1); `_normalize_weights` aceita float/zero/negativo — POST direto exclui time do pool silenciosamente — achado AUD1 Lente 1 | Baixa | 🔲 |
| M20 | Descomissionar write-side da flag single-user: sync escreve `is_my_team` via `MY_OWNER_ID`; record_acquisition/bulk_register propagam; colunas + to_dict + check_team.py + mapeamento standings (offseason.py:312) — fora do escopo M17 (só consumidores); **bloqueado: depende de M17, hoje ⚠️ (aguardando smoke prod)** — achado AUD1 Lente 3 | Baixa | 🔲 (bloqueado) |
| DOC1 | CLAUDE.md "App Startup Sequence" desatualizada: `init_auth` listado antes de sync/backfill (código: depois, app.py:138) + sync/backfill são condicionais a `fresh_import` (app.py:61), não passos de todo boot — docs-only fix — achado AUD1 Lente 6 | Média (blast radius: doc carregada em toda sessão) | ✅ 12/06/2026 (seção reescrita contra o boot real, passo a passo com âncoras) |
| O3 | Split do improvements.md: ativo (cabeçalho + Status Rápido completo + seções 🔲/⚠️) + `improvements_archive.md` (seções ✅, movidas verbatim); migração no fim de sessão quando item → ✅ — MAN-O3-REG. **Estendido 08/08/2026 (3º arquivo):** o bloco `> Atualizado em:` do cabeçalho tinha chegado a **66 entradas / 114 KB = 22% do arquivo**, duplicando o log de decisões do devplan e o `git log` — o ativo passa a manter as **5 mais recentes** e o resto vive em `improvements_sessions.md` (verbatim). Junto, a **dívida de migração** foi quitada (3 seções ✅ que nunca saíram: OFF26-5, OFF26-6, F8). Ativo: **522 KB → 377 KB (-28%)**, Status Rápido **byte-idêntico**, zero conteúdo perdido — MAN-UX10-UX11-REG | Média | ✅ 11/06/2026 (esquema estendido 08/08/2026) |
| UX10 | **Fotos de jogadores desatualizadas** — alguns jogadores exibem a foto da temporada anterior (exemplo do owner: **David Montgomery**). Cosmético, **sem impacto em dados** (identidade segue por `sleeper_id`). F1 precisa **distinguir as hipóteses antes de qualquer fix**: (a) URL do CDN correta e **cache** (navegador ou CDN) servindo imagem velha; (b) URL **construída** com componente desatualizado (temporada, time) em algum ponto do Manager; (c) fonte da imagem **keyed por algo além do `sleeper_id`**. F1 pergunta também: **a construção da URL de foto existe em mais de um lugar** (templates, JS, Python)? — MAN-UX10-UX11-REG | Baixa | 🔲 |
| UX11 | **Quadro de trades não mostra o time atual do jogador** — F1 por transbordo da MAN-UX12-F1; F2 de carona 10/08 (MAN-UX11-F2): franquia NFL na linha dim do quadro, 1 linha de template, zero backend — MAN-UX10-UX11-REG/UX11-F2 | Média | ✅ 10/08/2026 (**primeira observação em prod no smoke do `20b346b` — MAN-ARC-BUSCA-DONE; ocorrência observation/provenance registrada: checks pré-push não valiam. Detalhe no archive**) |
| UX12 | **Busca de jogador + página de perfil enriquecida** (pedido do co-admin **Michel**) — registrado 08/08 (MAN-UX12-REG) com questão 0 explícita de sobreposição; **F1 08/08 (MAN-UX12-F1, read-only):** 3 dos 7 campos já existiam na página atual, spec do [[M10]] conferida viva, réplica de fonte refutada, F1 do [[UX11]] respondida de carona, [[UX10]] estreitado, depth chart/idade viáveis via pool — recomendação (b) **despachar**, confirmada pelo owner — MAN-UX12-REG/F1/REFINE | Média | ✅ 08/08/2026 (**ROTEADO — despachado em [[M10]] (busca) e [[O2]] (perfil, refinado in-place absorvendo campos 2+5 + F1 do MAN-O2-F1); sem escopo próprio remanescente. Registro + diagnose no archive**) |
| UX13 | **Timeline exibe `event_type` cru `contract_year_correction`** — os demais eventos têm label PT-BR + badge; este cai no fallback (`EVENT_LABELS[e.event_type] \|\| e.event_type`). Causa evidente, sem diagnose: a chave (escrita por `contract_year_correction.py`, OFF26-20-FIX) falta nos **dois** dicionários `EVENT_LABELS` copiados (`player_detail.html` + `salary_history.html` — réplica declarada no próprio comentário do template; o fix toca os dois). Display de 1 linha, **candidato a carona** — MAN-O2-B1-DONE | Baixa | 🔲 |
| UX14 | **Time NFL de dropado com fallback no pool** — perfil do Waller exibe `—` porque `Player.nfl_team` está vazio (sync só atualiza rosterados). Hipótese registrada, NÃO arbitrada: fallback de LEITURA no pool ([[O2]] como precedente), sem persistir; pool sem time → `—` correto (FA real). F1 responde a réplica: entra na fonte única da Q1 da UX12-F1 ou vira 2ª fonte por tela? — MAN-ARC-BUSCA-DONE | Baixa/Média | 🔲 |
| UX16 | **Navbar transborda a viewport a ~860px** (`nav-right` / `btn-sync` / `nav-user-menu` / `nav-user-button`) — achado de carona da [[L3]]-FIX-UX, **pré-existente ao L3 e confirmado idêntico no controle** (mesmo transbordo com o CSS anterior ⇒ não é regressão). Só nessa faixa: a 390px e a partir de 1024px não ocorre. Corrigir **com validação pela sonda geométrica** — é o primeiro cliente natural do [[O7]] — MAN-L3-FIX-UX → MAN-L3-CLOSE-REG → MAN-UX16 → **MAN-CLOSE-LOTE-14-08** | Baixa | ✅ 14/08/2026 (**smoke visual do owner aprovado nas 3 faixas** — desktop, intermediária ~680–860 com hamburger + chip + Sync + avatar contidos, e mobile. Causa medida: a barra desktop precisa de **916px** e o hamburger só entrava em **≤768px** ⇒ **769–944px** transbordava; fix **CSS puro** — colapso passa a **1023px**, 1024+ intocado. ⭐ **1º cliente do gate [[O7]], que fechou o ciclo no sentido INVERSO:** a entrada saiu de `KNOWN_DEFECTS` **por indicação da sonda**, hoje vazio e com suíte **exit 0 sem máscara**. **Detalhe no archive**) |
| UX17 | **Paridade da barra de status: roster próprio × detalhe de time** — `/` mostra só salário usado/restante/% enquanto `/team/<id>` mostra cap atual, resto atual, **cap projetado + PROV**, resto projetado, dynasty, ativos, IR e quebra por posição. A tela que o owner mais abre é a mais pobre. Objetivo: mesma riqueza no roster próprio. **F1 mede antes de assumir** (a [[L3]]-FIX-UX já derrubou uma premissa dessa família — a macro do card **não** era compartilhada): (a) a barra do detalhe é macro compartilhável ou markup próprio? (b) o render de `/` já tem os dados ou precisa do `compose_budget` — e a que custo de query, já que hoje ele não consulta `ESPNImportLog` nem `rollover_done`? (c) gate de fase e tags PROV valem idênticos? Parente do [[UX4]] (tabela já convergida entre as duas telas) — **MAN-L3-CLOSE-REG** | Média | 🔲 |
| UX18 | **Bid Máximo inviável ($0 com vagas abertas) não acende alerta** — e a flag canônica **não captura o estado**. ⛔ **Premissa do prompt REFUTADA por medição:** `insufficient_budget` é `usable < 0`, e o caso do owner (folha 198 · 3 vagas · min $2 · **BID $0**) dá **`False` nas DUAS flags** — ler a flag canônica, como o prompt pedia, deixaria o caso **pior**. Predicado correto medido: `empty_spots > 0 and usable < MIN_SALARY`. **3 limiares divergentes** para a mesma grandeza (cap_projector JS `< 0`/`< 10` · `/league` template `<= 0` ×2 · keeper sheet e auditoria **sem alerta**), nenhum deles correto — e o `<= 0` da liga produz **falso positivo** em roster cheio a $200/0 vagas (caso Miller Time!). ⚠️ **Fix NÃO implementado de propósito:** a restrição do próprio prompt manda reportar antes de criar variação — a flag nova é decisão do owner (recomendação: `salary_engine.draft_budget`, onde `over_cap`/`insufficient_budget` já moram, 1 linha + teste, 7 consumidores herdam) — MAN-UX-BID0/MAN-UX-BID0-F2 → **MAN-CLOSE-LOTE-14-08** | Média | ✅ 14/08/2026 (**smoke do owner aprovado nas DUAS direções** — o alerta acende no cenário simulado do `/cap_projector`, com o banner explicativo, e o card do **Miller Time!** na `/league` deixou de pintar vermelho. Flag canônica `cannot_fill_roster` **aditiva** no `draft_budget` (`empty_spots > 0 and usable < MIN_SALARY`; 9 chaves antigas intactas; **engine 54→62 testes**, com as 3 fronteiras da diagnose); os 4 limiares inline saíram das telas, **amarelos informativos ficam**; auditoria ganha **aviso** no canal existente (⛔ nenhuma 5ª classe; 34 fixtures intactas) e keeper sheet só no **payload** (CSV byte-idêntico). Gate [[O7]] exit 0; **535 testes verdes**. **Detalhe no archive**) |
| UX19 | **Selo PROV falso nas grandezas CORRENTES da `/league` pós-rollover** — `bid_provisional = not espn_final` é calculado contra `season + 1` ([league.py:138](routes/league.py#L138)); assim que o rollover vira a season, a consulta passa a perguntar por uma tabela ESPN de **2027**, que não existe ⇒ `True` — e o ramo pós-rollover da macro recebe `prov=bid_provisional` ([league.html:82](templates/league.html#L82)), marcando **PROV** justamente nos números que acabaram de nascer da tabela DEFINITIVA. ⚠️ Só a `/league`: no `/team/<id>` os dois selos vivem **dentro** do `{% if show_projection %}` ([team_detail.html:52-65](templates/team_detail.html#L52-L65)) e somem junto com a projeção; o `/cap_projector` lê `espn_is_final` por jogador e degrada para `None` (sem selo). Achado de auditoria da MAN-DP-PREFLIGHT-1808 — aparece **em 18/08**, no dia em que o selo deveria sumir. Cosmético (nenhum número muda), mas contradiz o evento do dia na tela de planejamento. Parente do [[L4]] (o outro efeito colateral do gate que só fecha) — MAN-DP-PREFLIGHT-1808/**MAN-OFF26-25** | Baixa | ⚠️ **CORRIGIDO DE CARONA 14/08/2026** no [[OFF26-25]] (decisão do owner: o helper único passa nos 4 sítios, e o UX19 fecha junto). `bid_provisional` passou a ser `show_projection and not espn_final` nas **duas** rotas — o selo qualifica o número **projetado**, e pós-rollover não há projeção para qualificar. Coberto por `cap_projetado_test` (27) + o gate visual do [[O7]]. **Falta a observação em 18/08**, no dia em que a projeção fecha — é a mesma janela do OFF26-25 |
| O7 | **Sonda de validação visual como ferramenta permanente** (`tools/`, molde do [[O5]]): Playwright medindo **colisão / transbordo / overflow** + **assinatura de anatomia** para estruturas repetidas. Nasceu descartável na [[L3]] e pegou **dois** defeitos que suíte de unidade e leitura de HTML não pegam. **F1 decide:** cobertura inicial de páginas, larguras canônicas (incl. a **real de produção** e mobile), como servir as páginas (hoje é `file://` com HTML salvo do test client) e a ancoragem do gate (sessão que toca CSS/template roda a sonda antes do push — precedente do `backlog_audit.py`). Primeiro cliente: [[UX16]] — **MAN-L3-CLOSE-REG** | Média | ✅ 13/08/2026 (`tools/visual_probe/` + gate mecânico no CLAUDE.md; **demonstração bidirecional**: suíte verde `exit 0` em ~20s × controle `--css` pré-FIX-UX `exit 1` com **37 colisões @1280px**. 28 testes do núcleo puro. Mecanismo defeito conhecido × regressão nova se provou na estreia — corrigiu a lista de culpados do [[UX16]] de 4 p/ 5 **pela medição**. **Detalhe no archive**) |
| UX15 | **Jogador pré-selecionado na página de trade** — o botão do perfil ([[M14]]) já leva os dois times; falta o jogador chegar marcado. Refinamento do campo 3 do [[UX12]] (archive); provável F2 direta, a confirmar réplica (quantos caminhos de entrada têm pré-seleção?) — MAN-ARC-BUSCA-DONE | Baixa | 🔲 |
| UX20 | **Board global de picks ilegível quando a ordem do round difere da ordem das linhas** — as linhas são ancoradas por **owner** e as colunas por **round**, com a posição da pick só na badge `#N`; quando a ordem de um round não coincide com a ordem das linhas (caso real 2026: no Round 2 a segunda célula de baixo para cima é a pick **#5**, não a #2), a leitura vertical da coluna induz uma **sequência falsa** e o owner precisa varrer as 12 badges para reconstruir a ordem. **Direções candidatas registradas e NÃO arbitradas** (a escolha é entregável da F1): (a) inverter o eixo (coluna do round ordenada 1→12, célula mostra o dono atual) · (b) toggle "por time" × "por ordem de draft" · (c) visão linear complementar por round (1.01…N.12) sem remover o board · (d) o que a F1 achar superior. F1 pergunta de onde vem a ordem de cada round (projeção do lottery no R1 × critério dos demais — [[M16]]) e **se a marcação do board tem réplica** (outras telas que rendem picks, chips do trade manager, seção Picks do detalhe de time). ⛔ O redesenho **não pode criar leitura própria de ownership** — [[S2]]/`board_mirror` é a fonte canônica. Distinto do [[UX5]] (outra tela, problema de densidade e não de ordem). **F1 17/08 (MAN-UX20-F1, read-only):** ⛔ **premissa central REFUTADA** — as linhas **não** são ancoradas por owner, são ordenadas pelo **`pick_number` projetado do R1** ([picks.py:68](routes/picks.py#L68)) ⇒ o board **já é** a visão "por ordem de draft" **do R1**, e a causa é **R1 × R2/R3** ([[M16]]: sorteio × classificação invertida), divergindo só nas 6 posições do lottery — reprodução mecânica do board 2026 na seção (linha 2 = R2 **#5** ✅ confere; ⚠️ *"de baixo para cima"* estava errado, é de cima para baixo) e **R2 ≡ R3 por construção**. Ordem **já chega estruturada** na rota (re-key puro, zero query nova); ⚠️ **`board_mirror`/[[S2]] não é consumido pelo board** (é sync — a autoridade em render é a linha `Pick`). ⛔ **Janela de observação fecha em 18/08:** pós-rollover `proj` fica **vazio** e o board perde **todas** as badges. Réplica: só o `/trades` compartilha a fonte (e é **mais rico** — `~#` × `#`); `/team/<id>` e a proposta não têm projeção; **órfão já existente**: `/picks/lottery/<season>` é a linear do R1 **sem link a partir do board**. Achados fora da lista: **célula = link de trade** ([[M9]]-FIX), `✎` **sem gate de admin** no template (403 silencioso), "3 rounds" **triplicado** (py/JS/CSS), `resetPick()` morto. **Recomendação (d): (c) enxuta** — rotular a origem da ordem no cabeçalho de cada round (ataca a CAUSA, 1 linha) + bloco linear de 2 ordens + fechar o órfão de navegação; **(a) rejeitada** (o eixo já está invertido para o R1 e uma ordem de linhas não serve aos 3 rounds) — **decisão do owner** **F2 17/08 (MAN-UX20-F2) — direção (e) do owner CONSTRUÍDA:** o board virou **3 colunas lineares por round**, cada uma já na ordem das picks daquele round; célula = **`R.PP`** · **time atual** · **`via <original>`** quando trocada · **⇄** discreto (o link de trade do [[M9]]-FIX preservado, só migrou da célula inteira para o ícone). Cabeçalho **rotula a origem da ordem** (*Sorteio* × *Classificação invertida*) — a peça que ataca a causa. **Clique realça** as picks do time nas 3 colunas (toggle, cor de destaque); o **verde de "minha" continua visível por baixo** (arbitragem do owner: duas cores). Transformação `round_centered` é **re-key puro na rota**, ⛔ `_build_pick_projections` **intocada**. **Sem `✎`** — modal e handlers removidos do cliente (rota PATCH segue viva, é [[F15]]); `resetPick()` morto removido junto. Macro única para os 3 rounds + JS sem o passo fixo de 4 + CSS `.picks-matrix*` **deletado** ⇒ a triplicação do "3 rounds" **caiu para 1 sítio**. Sonda do [[O7]] **reapontada** (`.picks-matrix` não existe mais → `.picks-order-container`). ⚠️ **Um valor da validação do prompt estava errado** (`1.05` é *Trust The Process*, não *Cangaceiros* — banco confere). Smoke de **navegador real** verde (realce 6/6, verde preservado, toggle, filtro, ⇄ sem disparar realce, zero erro de JS); gate [[O7]] exit 0; 10 suítes OK. ⚠️ **Falta smoke de prod** — MAN-UX15-REG/MAN-UX20-F1/**MAN-UX20-F2** **FIX1 17/08 (MAN-UX20-F2-FIX1, CSS puro):** densidade e alinhamento, **medidos em 13 larguras antes de tocar o CSS**. Linha quebrava em 2 (alturas de 65 a 135px) por falta de `min-width: 0` no item flex — sem ele o ellipsis não age; com `nowrap` + ellipsis a altura virou **32px única** e a seção caiu de **953px → 492px** (12 × 3 numa viewport desktop). O **"via" cede espaço antes do nome do time** (`flex: 0 8 auto`) e o `title` da linha guarda o texto inteiro. ⭐ **A causa do desnível NÃO era o cabeçalho** (hipótese refutada: os 3 têm 36px em toda largura) — era o `flex-wrap` derrubando uma coluna inteira para a linha seguinte a partir de 900px; o container virou **grade `repeat(auto-fit, minmax(260px, 1fr))`**, que alinha topos por construção. ⛔ `auto-fit`, **não** `repeat(3, …)`: a triplicação que o F2 quitou não volta. Regressão zero no smoke de navegador, gate [[O7]] exit 0, suítes e auditor verdes **FIX2 17/08 (MAN-UX20-F2-FIX2, CSS puro):** ⚠️ **o drift do owner NÃO reproduz em headless** — medido em ponto flutuante (o FIX1 media arredondado): 31,750px idêntico nas 36 linhas, drift 0,00, em dpr 1/1,25/1,5, e altura **natural** uniforme mesmo nas linhas com emoji. ⇒ corrigido o **mecanismo**, não a instância: `min-height` é **piso, não trava** — quem decidia a altura era o conteúdo, que **difere por coluna** (a distribuição do `via`), e basta outra métrica de fonte para uma linha crescer e o erro **acumular até a 12ª**. Agora `height: 38px` + `box-sizing: border-box` + `overflow: hidden`: nem conteúdo nem estado mexem na altura (medido: normal, `is-mine` e `highlighted` **todas em 38,000px** — estado só muda COR, borda sempre 1px, realce por `box-shadow` que não ocupa layout). Densidade 32 → **38px** com tipografia um passo acima; seção termina em **813px** ⇒ 12 × 3 + cabeçalhos numa viewport de 900px sem rolagem interna. ⭐ **O gate do [[O7]] bloqueou o push com 81 transbordos a 390px** — item de grade tem `min-width: auto` (= min-content) e o `nowrap` virou piso da trilha (370,7px dentro de 358px); fix `min-width: 0` no `.draft-order-column` (o FIX1 pôs nos itens de texto e **faltou no item de grade** — o gate cobriu o vão). Drift 0,00 nas **14 larguras** varridas; regressão zero; suítes e auditor verdes **✅ FECHADO 17/08 (MAN-UX20-DONE): smoke de produção aprovado** sobre o hash live `70a73bf` **conferido antes do smoke** (gate [[PROC1]] cumprido — o diff toca `static/style.css`, artefato público servido). Aprovados: layout de colunas por round, densidade 38px, ⭐ **a linha `.12` das 3 colunas alinhada no navegador onde o drift era observado** (a prova que faltava — o FIX2 travou a altura por construção **sem conseguir reproduzir** o drift localmente), realce + verde de "minha", ⇄ com pré-seleção, filtro, e dados do R1 conferindo com a referência da liga. ⚠️ A divergência local × prod vista no smoke local **não é item aberto**: o `dynasty.db` do repo é **seed defasado**, não espelho do vivo — prod é a superfície canônica e confere. A parte de **UI** do [[F15]] fechou de carona (resta só a rota PATCH de backend); o órfão `/picks/lottery/<season>` **segue sem link** (a direção (e) substituiu a candidata (c) que o previa). Detalhe migrado para o archive ([[O3]]) | Média | ✅ |
| UX21 | **Página do lottery sem porta de entrada a partir do board de picks** — `/picks/lottery/<season>` existe e é **rica** (ordem do R1, pool de bolinhas, hash de auditoria, histórico de re-runs — a camada [[M8]]), mas **não é alcançável por link**: quem não sabe a URL não chega. ⚠️ A assimetria é medida: a tela de auditoria tem *"← Voltar ao Picks"*, então **o caminho de volta existe e o de ida não**. Achado da F1 do [[UX20]] (archive); ficou **deliberadamente fora do escopo** porque a direção (e) escolhida pelo owner substituiu a candidata (c), que o previa — registrado no fechamento MAN-UX20-DONE para não se perder. **Escopo candidato, NÃO arbitrado:** link a partir do board, sendo o candidato natural o **cabeçalho do Round 1** — que o F2 do UX20 já criou e que já rotula *"Sorteio (lottery)"*, ou seja, a infra do link **já existe** e o texto já nomeia o destino; a forma final é decisão de implementação. ⏳ **Timing (consideração do owner, 17/08):** implementar quando o link tiver **destino vivo** — o lottery de 2026 perde relevância no rollover e o de 2027 só nasce com o próximo sorteio. **Sem prazo** — MAN-LOTTERYLINK-REG | Baixa | 🔲 |
| UX22 | **Board de picks vazio quando a season não tem ordem — visão de INVENTÁRIO** — pós-ocultação das consumidas ([[OFF26-29]]), 2027/2028 mostravam só *"ordem ainda não definida"*: a POSSE existe inteira na tabela `Pick`, e na semana mais movimentada de trades a página não respondia *"quantas picks tenho, de quem, em que rodada"* (feedback do owner 18/08, com print). **F2 na mesma janela:** season com picks e SEM ordem renderiza **inventário por rodada** — célula reusa a anatomia do board [[UX20]] (dono atual, `via <original>` na trocada, `data-team-name` ⇒ **filtro e realce funcionam de graça**), **SEM número de posição** (ordem não se inventa; lista sai por nome do dono — alfabética é visivelmente não-draft), chips de **contagem por time** e o aviso antigo **encolhido** para uma linha dentro da visão; season COM ordem → render ordenado intacto (a visão sai de cena sozinha quando `round_centered` ganha as rodadas). Rota = transformação de leitura pura; lottery/classificação e Lottery Odds intocados; consumidas fora por herança do predicado. `picks_inventory_test.py` (5: posse+proveniência, gancho do filtro, contagem×tabela, consumida fora, **ordenado intacto** via fixture de standings); smoke real na cópia do ensaio: 72 células = 72 picks da tabela, chips 72/72, 2 seções de inventário; gate [[O7]] **exercido, exit 0** (diff toca template). ⚠️ **ID: o prompt pedia UX21, ocupado** (porta de entrada do lottery, 17/08) — nasceu UX22, colisão registrada (precedente UX15→UX20) — MAN-UX21-REG-F2 | Alta (semana de trades) | ⚠️ **F2 no ar — smoke prod pendente** (gate [[PROC1]]) |
| UX23 | **Cap Projector mirava `current+1` sem consciência de fase — pulou para 2027 no meio da janela da auction 2026** — pós-rollover o título virou "2027", banner *"ESPN não importados"* (verdade para 2027, **pergunta errada**: 2026 está travada), Δ +$0 em toda linha (re-projeção do já-valorizado contra a MESMA tabela — não é erro de cálculo, é a pergunta errada), **board DP1 VAZIO** (pedia `in_class` de 2027; o store só tem 2026) e **cadeia DP2 ignorando rookie em silêncio** (`adj None` → `continue`). **F1 (18/08):** alvo derivado inline em **6 sítios** (3 rota + 3 template/JS), zero helper, zero gate de fase (a `/league` tem; o projector não); ⭐ a base correta **já existia** — modo D9 `compose_budget(projected=False)`. **F2 (mesma janela; decisões do owner: sinal = evidência AuctionLog, colunas saem, título explicita o modo):** helper único **`planning_target_season()`** em models — `current+1` pré-rollover · `current` pós-rollover com auction pendente · `current+1` com **≥3 `fa_auction`** da corrente (calibração do Code, documentada: leilão real entra em LOTE; 1-2 registros = teste avulso que não pode virar a chave na janela 20-24/08); os 6 sítios consumem o helper (títulos e `SEASON_PROJ` **vêm do servidor**); modo corrente: colunas Sal-próximo/Δ **saem**, POST `/budget` com `projected:false` (D9 — parâmetro que já existia), tag "FOLHA CORRENTE · AUCTION 2026" no título; banner/badges/DP1/DP2 **voltaram sozinhos** pela mudança do target (zero lógica nova). `planning_target_test.py` (12: 3 fases, limiar 2×3, rookie_draft não conta, outra season não conta, payload mode, board de fase, **guardas AST anti-réplica** rota+template). Smoke estado-de-prod: título 2026 + tag, `espn_status=final`, board 251 (287 in_class − 36 draftados), DP2 somando, budget corrente == GET; **fixture pós-24/08 (3 fa_auction): volta a 2027/projetado sozinho**. Gate [[O7]] exit 0; 9 suítes + `template_js_test` verdes — MAN-UX23-REG-F1/**MAN-UX23-F2** | Alta (janela 20-24/08) | ⚠️ **F2 no ar — smoke prod pendente** ([[PROC1]]) |
| UX24 | **Colunas "Proj `current+1`" do roster e do detalhe de time pós-rollover** — carona da F1 do [[UX23]] (mesma família, superfície diferente): [roster.html:130](templates/roster.html#L130) e [team_detail.html:123](templates/team_detail.html#L123) exibem "Proj {{ g_current_season + 1 }}" = **Proj 2027** agora, com a mesma semântica de Δ≈0 (re-projeção do já-valorizado). Menos grave que o projector (coluna informativa, não ferramenta de decisão) e **fora do escopo do UX23-F2 por restrição do prompt**. Candidato natural: mesmas peças do UX23 (`planning_target_season` + esconder/rotular em modo corrente) — ⛔ não arbitrado — MAN-UX23-F2 (registro de carona) | Baixa | 🔲 |
| UX25 | **Hub: excesso de roster invisível — "Slots livres 0" igual para cheio-exato e ESTOURADO** — feedback do owner (19/08): com os rosters inflados pelos 36 rookies, times com jogadores demais não viam obrigação nenhuma de corte antes de 20/08. **F1-rápida (mesma sessão):** truncamento confirmado — `empty_spots = max(0, MAX_ROSTER − N)` em [salary_engine](salary_engine.py) engole o excesso; **limite canônico = `MAX_ROSTER=22` ATIVOS** (regulamento 1.3, IR até 2 **fora da conta** — mesma régua de composição do [[OFF26-16]]; fonte adotada: a constante do engine, zero literal novo; settings do Sleeper corroboram). **F2:** card ganha a faixa **"⚠️ Cortar ≥N jogador(es) até 20/08"** com a contagem visível **"X/22 ativos (+K IR)"** — `cut_needed = max(0, ativos − 22)` como campo NOVO do card ([league.py](routes/league.py)); ⛔ réguas de cap/bid **intocadas** (o `slots` truncado continua o mesmo — teste dedicado prova), cap negativo segue no alerta próprio, time no limite/abaixo = zero ruído. `roster_excess_test.py` (5 — a função de card é pura); smoke na cópia inflada: **3 cards com obrigação (24/22→≥2, 26/22→≥4, 27/22→≥5)** batendo 3/3 com a query; ⭐ **âncora Trust The Process conferida dos DOIS lados: 26 ativos → "cortar ≥4" — e o Sleeper AO VIVO diz os mesmos 26** (MellowBR 22, regular). Gate [[O7]] exit 0 (diff toca league.html + style.css). ⚠️ O literal "até 20/08" morre com a janela — remoção/generalização fica para o pós-cortes. **-b (19/08, MAN-UX25-b): a MESMA obrigação, VIVA no cap projector** — item "Roster" na barra sticky, recalculado **pelo POST `/budget` que já roda a cada toggle** (F10: o servidor conta — ele conhece `is_on_ir` — o JS só exibe; limite vem no payload, zero hardcode): `X/22 ativos (+K IR)` discreto quando regular (✓), **"· cortar ≥N" em alerta** quando o CENÁRIO excede, contando para baixo até regularizar; rookies do cenário **ocupam vaga de ativo**; "Spots vazios" mantido com o significado de auction (0 truncado é verdadeiro; o indicador novo ao lado desambigua — decisão de menor mudança, reportada). Campo `roster` **aditivo** no payload; D9/`budget` intocados (teste prova folha 125 com IR e `empty_spots` seguindo truncado). +4 testes (9 na suíte); smoke Trust na cópia: **26/22 cortar ≥4 → toggla 4 → ✓ → volta → reaparece**; rafaelferreirap `+1 IR` fora da conta; Pitbull 22/22 neutro — MAN-UX-NEXT-REG-F2/**MAN-UX25-b** | **Crítica** (prazo 20/08) | ⚠️ **no ar (Hub + projector) — smoke prod pendente** ([[PROC1]]; o diff toca `style.css`, artefato público conferível) |
| OFF26-23 | **Ano de contrato do rookie 2026 × rollover × passo 5** — pergunta do owner a 7 dias do draft: o rookie entra e PERMANECE Ano 1? **F1 10/08 (MAN-OFF26-23-REG-F1):** a ordem segura existe mas **não é imposta por código** — o `draft_import` não tem gate de `rollover_done`; importar o draft ANTES do rollover incrementaria todo rookie p/ Ano 2 (varredura cega, `offseason.py:686`). **Roteiro seguro da semana entregue na seção** (rollover 18/08 ANTES do import do draft; passo 5 só pós-24/08 — validado: nada o lê além da UI, e o clear precoce zeraria os salários do próprio import). Gainwell = mesma manifestação, raiz distinta (canal, não ordem) — MAN-OFF26-23-REG-F1/-F2/**-FIX** (SyntaxError no JS da /offseason pego pelo smoke do owner — string quebrada na edição gerada; fix de 1 linha + `template_js_test.py` como guarda permanente) | Alta (semana 17→24/08) | ⚠️ 10/08/2026 (**gates + fix no ar — smoke prod pendente**, gate [[PROC1]]) |
| OFF26-24 | **Script de população do board da liga fantasma** — decisão do owner 10/08 (reverte o adiamento p/ 2027): Playwright headed na máquina do owner, perfil dedicado logado, ⛔ guarda de nascença `league_id 1389725099556372481` + ⛔ API interna vetada (a descoberta do `draft_id` usa a API PÚBLICA da liga, a mesma do OFF26-4). **Cowork segue plano A** até o critério: 12/12 em ensaio + auditoria OFF26-4 zerada + zero intervenção + RESET exercido, **até 19/08** — sem isso, 2026 roda Cowork e o script vai a 2027. F1 10/08 (sheet JSON sem sid → export do `build_sheet`); **ensaio 11/08** (spec de seletores; achado: o cliente MENTE — comando via DOM, **verdade via API**); **F2a 11/08 (MAN-OFF26-24-F2a):** `tools/phantom_board/` — núcleo puro + guardas de nascença + `validate` read-only + `designate` ponta a ponta + endpoint `keeper_sheet_export`; 30→35 testes; **-F2a-FIX 11/08**: guarda de identidade refeita POR CONSTRUÇÃO (URL×draft_id derivado — a página do draft não exibe o nome da liga) + espera de login na 1ª vida do perfil (JOIN DRAFT proibido); `validate` já VERDE em execução real (18/18, $176) — MAN-OFF26-24-REG-F1/**-F2a (FECHADA: Cam Ward assentado via API; validate 19/19)/-F2b** (populate por time + --all retomável; idempotência PRIMEIRO — a lição da F2a; bloqueado_teto = resultado; auditoria OFF26-4 como juiz; **FIX8: assentamento ASSÍNCRONO** — lag real da API >5min (Josh Allen) matou o poll bloqueante; reconciliação por time c/ teto 300s + reload no meio (hipótese do cache por visita, telemetria decide) + `assentado_local_api_atrasada`; 87 testes) (**FIX9 12/08:** campanha real — abort de time deixava o MODAL aberto → TimeoutError cru no time seguinte; higiene de estado em TODO abort + verificação defensiva pré-clique + populate sem traceback cru (abort padrão de time E de campanha); anti-homônimo passou a exigir NOME — a busca do Sleeper é fuzzy: "Malik Willis" devolvia Malik Williams ×2 + Hajj-Malik Williams QB, FAs de sigla vazia = linhas REAIS, não artefato; critério 0/2+ intacto; 104 testes) (**FIX10 12/08:** campanha 12/12 — as DUAS caras do teto: além da recusa síncrona §B.3.2, o input CLAMPA silenciosamente ao max bid (digitou 6/4/3/2, gravou 5/1/1/1 = $196 sem aviso); modelo verificado ao dólar `max_bid = 200 − gasto − $1×vagas restantes`; fix = READ-BACK do input pré-SET → clampou = bloqueado_teto DO KEEPER, nada gravado, sheet canônica; conferência aponta divergentes por nome; telemetria: lag puro 8–121s, zero reload — contra a hipótese do cache; **Travis Hunter = único two-way (DB+WR) dos 237 da sheet** → pendência OFF26-24-HUNTER c/ micro-probe manual; 121 testes) (**FIX11 12/08:** probe do owner FECHOU a HUNTER — ele está no pool (rank 167, tabs All+WR, "+" habilitado), rótulo "DB,WR"; o abort real foi a eleição exigindo igualdade de posição; fix = pertencimento (`position_matches`, fonte única): "WR" ∈ "DB,WR", "QB" segue não casando; parse devolve o rótulo íntegro; anti-homônimo intacto; 134 testes) (**GO 12/08:** **critério de 19/08 CUMPRIDO com 7 dias de antecedência** — ciclo limpo: RESET → campanha oficial `185453Z` 12/12, 235 designados + 2 bloqueados declarados (AlexTheDawg; Croskey entrou a $4 de sheet pelo grão do FIX10), 0 falhas, zero intervenção, Hunter designado → auditoria = SÓ os 2 bloqueados, zero salário divergente → RESET final provado, validate 0 picks/237 sheet/3º draft_id derivado; **alocação de owners em Draft Settings→DRAFT ORDER é PERMANENTE** (sobrevive ao RESET; mapa via `draft_order`); ⛔ RANDOMIZE e RESET BUDGETS proibidos junto do START DRAFT; telemetria: 382 assentamentos, zero reload = lag puro; **script = PLANO A de 22/08, Cowork = plano B**) (âncora no #modal[role=alertdialog] real; header “Make Manual Pick for Team N” como identidade; fallback logado) (busca/linhas/preço escopados ao MODAL — a lista de fundo vazava; filtro conferido antes do matching) (parser do anti-homônimo lê o DOM real — newlines/sigla duplicada/injury; critério intacto) (célula por COLUNA do slot, nunca nth global; “Change Player” proibido; handler sem crash) (mapa slot↔owner: cadeia draft_order → slot_to_roster_id×rosters → picks; validate passou a conferir owner de verdade) (hCaptcha recusa o Chromium de teste → launch pelo Chrome real via channel; captcha é resolvido pelo HUMANO, nunca burlado) | Alta (uso real 22/08) | 🔲 (**critério de 19/08 ✅ CUMPRIDO 12/08 — script = PLANO A de 22/08, Cowork = plano B**; fecha ✅ e migra ao archive após a população real de 22/08) |
| OFF26-25 | ⛔ **O rollover não tem gate MECÂNICO de tabela ESPN definitiva** — o passo 4 destrava com `espn_values_updated`, flag **manual** escrita só por `confirm_espn` ([offseason.py:653](routes/offseason.py#L653)) e **agnóstica a QUAL tabela está no banco**; o import ESPN nunca a escreve. ⇒ o rollover **roda sobre a provisória sem recusa**, e como é **once-only** (`rollover_done`) a tabela definitiva que chegasse depois **não corrigiria** os 244 contratos — só a restauração do backup. Achado de auditoria da MAN-DP-PREFLIGHT-1808 (14/08); a **diagnose já existia** ([[OFF26-9]] ✅, archive: *"o rollover pode rodar sobre ESPN preliminar… o gate é satisfeito por um checkbox do admin"*) — o que **não** existe é o poka-yoke. Mesma família do [[OFF26-23]] e mesma diretriz do owner (*ponto de não-retorno não se protege com runbook*): hoje a defesa são **dois `confirm()`** ([offseason.html:735](templates/offseason.html#L735)), que é disciplina. Fix candidato: `_get_step_statuses` exigir `ESPNImportLog(season=current+1, status='final')` no passo 4 (a mesma verdade que a `/league` já lê para o selo PROV). ⚠️ **Não é bloqueador de 18/08** — backup + preview do rollover cobrem operacionalmente — MAN-DP-PREFLIGHT-1808/**MAN-OFF26-25** | Alta (18/08) | ⚠️ **IMPLEMENTADO 14/08/2026 — falta o ciclo real.** **Dupla condição** no passo 4: a flag manual (passo 3, intacta) **E** `models.espn_final_import(current+1)`. ⭐ **O predicado é o import MAIS RECENTE, não "existe algum final"** — reimportar provisória depois da definitiva devolve `espn_ref_value` ao estado provisório e a linha final antiga ficaria no log: *trava que mente é pior que trava nenhuma*. **Recusa dura server-side** (409 `blocked_by="espn_nao_definitiva"`, citando status + data **UTC** + o caminho: reimportar com o checkbox); **once-only tem precedência** na ordem das checagens. Preview do `/admin` passa a exibir a tabela candidata (season/status/data) — último ponto de detecção. **Fonte única**: a consulta saiu de 2 cópias inline da `/league` e serve 5 consumidores; guarda estática anti-réplica + anti-season-literal (por AST). **33 testes novos** (`espn_gate_test.py`) + fixture do `late_drop_test` ajustada (3 testes provavam a urna e passariam a provar o gate errado). ⭐ **Smoke em navegador REAL, bidirecional** (app servindo sobre cópia, sessão por cookie assinado): **17/17 recusando** (passo 4 bloqueado **com a flag true** — a célula exata do item) × **6/6 aceitando** com a definitiva no log. **588 testes verdes**; gate [[O7]] exit 0 |
| OFF26-26 | **Rookie draft 2026 realizado FORA do board do Sleeper (WhatsApp) — incidente, diagnose e reparo one-shot** — 17/08: ESPN definitiva → rollover → draft via WhatsApp, picks inseridas à mão nos rosters → sync criou a classe como **31 stubs** ($1, unknown, needs_review, **css=2025**); 5 nem existiam; draft real ficou `pre_draft` (importador [[OFF26-3]] sem insumo). **F1:** raiz = [sync_sleeper.py:304](sync_sleeper.py#L304) com a constante estagnada (irmão no `/auction` → [[OFF26-28]]); `record_acquisition` cura tudo MENOS `needs_review`; store 2026 íntegro. **FIX (`bcf8a5d`):** `wa_draft_2026_fix.py` one-shot pela porta canônica — preflight Brown-safe com âncoras + estados + guarda de fase, apply idempotente por `wa_draft:2026:<r>.<p>`, auditoria molde OFF26-4 + smoke de escopo. **FIX-b (`d77314b`):** estado "aprovado em review" (caso **Singleton** — aprovação Cat A prévia; ⭐ o preflight ABORTOU no estado imprevisto, validando o desenho). **PROD 18/08:** preflight 36/36 → apply → **AUDITORIA LIMPA 36/36**; backup `/data/dynasty_prod_backup_2026-08-18_wa_draft.db`. Decisões: **FA auction 24/08 VOLTA à fantasma** ([[OFF26-24]] plano A); draft real fica `pre_draft`; picks 2026 mortas por governança (→ [[OFF26-29]]). ⚠️ Trilha nomeada `MAN-OFF26-24-*` pela urgência; ID de backlog = 26 (24 e 25 ocupados — precedente UX15→UX20) — MAN-OFF26-24-REG/F1/FIX/FIX-b | Alta | ✅ 18/08/2026 (auditoria limpa em prod; **detalhe no archive**) |
| OFF26-27 | **Criação de stub no sync usava season ESTAGNADA** — [sync_sleeper.py:304](sync_sleeper.py#L304) carimbava `contract_start_season=CURRENT_SEASON` (constante fixa em 2025) e o rollover só avança o AppConfig ⇒ todo entrante pós-rollover nascia na season errada (a classe 2026 inteira — curada pelo [[OFF26-26]]). **Fix (`bdd3044`, mesma janela do registro):** `stub_season = get_current_season()` lido 1×/sync (hoisted), constante só como fallback DENTRO do helper; zero uso cru restante no módulo; players existentes intocados. `sync_stub_season_test.py` (6): guarda AST no construtor `Player(` + fallback sem AppConfig + pós-rollover acompanha. ⭐ Smoke com `run_sync` REAL contra cópia adaptada reproduziu o incidente como validação: os 36 rookies ausentes do seed recriados como stubs **todos em 2026**, zero existente alterado. Suítes 62+15+64+33 verdes. Fora do escopo (F1): `import_csv` dormente, `AuctionLog` default latente — prompt MAN-OFF26-25 (ID de backlog = 27, colisão com o gate ESPN) | **Crítica** (antes do sync pós-cortes de 20/08) | ⚠️ **fix no ar (`bdd3044`) — smoke prod pendente**: próximo stub criado por sync em prod nascer 2026 (gate [[PROC1]]: conferir hash deployado) |
| OFF26-28 | **`/auction` carimba season 2025 HARDCODED no cliente** — achado irmão da F1 do [[OFF26-26]]: o backend tem default correto (`get_current_season()`), mas o cliente **sempre envia** a season explícita e os campos nascem 2025 — [auction.html:88](templates/auction.html#L88) (`value="2025"`), [:170](templates/auction.html#L170), [:190](templates/auction.html#L190), [:215](templates/auction.html#L215), e o campo FA ([:49](templates/auction.html#L49)) usa `now_year` que a rota **nunca passa** ([auction.py:18-20](routes/auction.py#L18-L20)) ⇒ registro manual hoje carimba `contract_start_season`, `SalaryHistory.season` e `AuctionLog.season` como 2025. ⛔ Relevante para o REGISTRO da FA auction de 24/08 (4 portas do `/auction`). Fix candidato (não arbitrado): rota passa `now_year=get_current_season()` + remover os 3 hardcoded do JS — prompt MAN-OFF26-24-REG (ID = 28; o "26" do prompt colidia) | **Alta** (antes de 24/08) | 🔲 |
| OFF26-29 | **Picks 2026 consumidas seguem VIVAS como ativo tradável no Manager** — draft realizado fora do board ⇒ tabela `Pick` season 2026 intacta. **F1 18/08 (mesma janela, read-only):** 7 consumidores mapeados — o funcional é **`/api/picks` sem filtro** ([picks.py:127](routes/picks.py#L127)) alimentando o simulador/propostas ([trades.html:329](templates/trades.html#L329)); ⛔ **premissa "registrar trade" DESLOCADA** (o Manager não executa trade — só preview/proposta; ativo move via sync/S1) ⇒ exposição real = **planejamento enganoso**; ⛔ **delete REFUTADO como mecanismo**: o critério de deleção do sync é **ano-calendário** (`datetime.now().year`, [sync_sleeper.py:398](sync_sleeper.py#L398)) — as 2026 morreriam só em 01/01/2027 — e o Sleeper ainda lista **21 traded picks 2026** (medido ao vivo) ⇒ `_ensure_default_picks` **recriaria** as deletadas. **Recomendação (F2 ~1 sessão, zero schema/delete):** predicado data-driven `pick consumida = existe AuctionLog(rookie_draft, season da pick)` — mesma evidência do gate do passo 5 — em helper único + filtro no `/api/picks` + selo/ocultar no board e `/team/<id>` (selo × sumiço = decisão do owner); `_sync_trades` intocado (trade real segue espelhando). Governança no Sleeper já aplicada (aviso); ensaio opcional do draft room na fantasma — MAN-OFF26-24-REG/**MAN-OFF26-27-F1** (ID = 29) | Baixa (REG) — F1 sugere reavaliar p/ Média (janela de trades até 24/08) | 🔲 (F1 feita; F2 aguarda decisão) |
| M21 | **Busca cobre o universo Sleeper** — duas fatias: **A — FAs da liga** (**✅ 10/08/2026**, MAN-M21-A + smoke prod MAN-ARC-BUSCA-DONE: badge FA, ordenação rosterado-antes-de-FA, perfil de FA corrigido; âncora **Kamara**, 41 dropados medidos) e **B — universo não-Player** (Média, pós-intertemporada, 🔲; ⚠️ arbitragem importar×federar em aberto p/ F1b; **caso Helm migrado p/ cá** — nunca foi Player, medição Shell 10/08) — MAN-M21-REG/F1a/A/ARC-BUSCA-DONE | A: Alta · B: Média | 🔲 (fatia A ✅ 10/08/2026 · fatia B pendente) |
| MAN-METH-REG | Candidato a baseline do DEV_METHODOLOGY: F1 refuta premissas do prompt contra o código (**registro apenas** — candidato, não regra vigente; destino: consolidação em sessão de revisão de metodologia dedicada, transversal manager/optimizer/predictor) — row criada pelo [[O5]] (a seção detalhada existia sem entrada no namespace) | A definir | 🔲 |
| MAN-METH-2 | **Parecer pré-execução como FASE do fluxo** — formalizar no `DEV_METHODOLOGY.md`: quando o owner solicitar (recomendado para **F2 em caminho crítico**, mutação irreversível e itens que tocam `salary_engine`/schema/contratos), o Code analisa o prompt contra o **código real ANTES de executar** e **aguarda as decisões do owner** — reportando premissas refutadas com evidência, furos de desenho, réplicas que o escopo criaria, decisões em aberto e riscos de calendário. **Caso de referência: MAN-OFF26-25 (14/08/2026)**, onde o parecer pegou um erro factual (`is_final` não existe no `espn_import_log` — o campo é `status`), um **furo de correção** no predicado proposto (*"existe um final"* prova evento e daria **falso OK** no cenário final-seguido-de-provisória) e uma **réplica** que o escopo criaria (3ª cópia de "a definitiva entrou"); o prompt corrigido produziu o fix certo. ⚠️ **Não duplica o [[MAN-METH-REG]]**: aquele é regra de **entregável da F1** (seção de refutação dentro da diagnose); este é **fase que precede e bloqueia a execução**, e cobre o caso em que **não há F1** — o OFF26-25 foi de registro direto a F2. A F2 deste item edita o `DEV_METHODOLOGY.md` (**transversal** manager/optimizer/predictor) e define os critérios de quando a fase é recomendada — MAN-METH-REG-PARECER | Média | 🔲 |
| MAN-ESPN12 | Diagnose read-only: onde o fator ×1.2 do ESPN é aplicado — veredito da suspeita central (réplica ×1.2 no client) **negativo**; débito real (a/b/c) registrado na seção como F2 opcional (helper único `adjust_espn` + reponteirar 5 sítios), decisão aguarda o owner — row criada pelo [[O5]] (a seção detalhada existia sem entrada no namespace) | A definir | 🔲 |
| O5 | Quitação da dívida O3 + auditor poka-yoke do backlog: reancorar sub-seções `###` órfãs, migrar seções ✅ ao archive, `tools/backlog_audit.py` (stdlib, read-only, exit ≠ 0) como **gate do checklist de fim de sessão** — MAN-O5-REG/MAN-O5 | Média | ✅ 13/08/2026 (mesma sessão, precedente O3 de self-aplicação: reorg íntegra por asserts de máquina + auditor demonstrado nos dois sentidos — ativo pós-limpeza exit 0, backup pré-limpeza exit 1 com 83 violações; **zero seções ✅ de item existiam para migrar** — a baseline externa leu marcos ✅ internos de itens abertos; 42 headings reancorados sob o [[OFF26-20]]; detalhe no archive) |
| MAN-AUTH1 | **Login OAuth não oferece seletor de contas Google — usuário com sessão Google não-cadastrada cai em 403 sem saída** — relato do owner (Murilo, WhatsApp, 17/08): no PC do trabalho o clique em login **não pergunta qual conta**; o Google autentica direto com a sessão ativa do navegador (email corporativo, fora do `users.csv`) e a rota devolve **403**. O `/logout` do app **não muda nada** (encerra a sessão Flask, não a do Google), então o usuário fica **preso no loop**: reentrar reautentica a mesma conta errada. Workaround em uso: **aba anônima**. Bug de **UX de autenticação** na camada [[X1b]] (Google OpenID Connect via authlib) — não é permissão nem cadastro (a conta certa existe). ⛔ **Nenhuma direção arbitrada e nada verificado contra o código neste registro** (o parâmetro de autorização, a página do 403 e o alcance do `/logout` são perguntas da F1) — **F1 obrigatória antes de F2**. **F1 17/08 (MAN-AUTH1-F1, read-only):** hipótese **confirmada por medição** — a chamada de [auth.py:61](routes/auth.py#L61) não passa `prompt` nem `login_hint` (authlib só mescla `authorize_params` + kwargs, ambos vazios), e o redirect sai com `client_id·nonce·redirect_uri·response_type·scope·state`. **Sítio único, zero réplicas** (o único link em todo o app é [login.html:8](templates/login.html#L8)). O 403 media pior que o relatado: **sem o email**, sem link de login **e sem link de logout** (a navbar esconde o menu para anônimo), e a única frase acionável — *"fale com o administrador"* — **aponta o remédio errado** (a conta certa existe). **Ciclo de 3 saltos medido:** 403 → *Voltar ao Início* → `/` → 302 `/login` → botão → 403. `/logout` é **inerte por 3 motivos independentes** (o rejeitado **nunca foi logado** — o 403 retorna antes do `login_user`; não tocaria a sessão Google; e o link nem aparece). ⛔ **Premissa "11 owners entram com 1 clique" DESLOCADA:** `remember=True` + `REMEMBER_COOKIE_DURATION` default **365 dias** ⇒ o caminho diário é **zero clique no fluxo OAuth** — forçar o seletor só custa no caminho **frio**. ⛔ Armadilha registrada: **não** levar ao logout do Google (desconectaria a máquina inteira). **F2 17/08 (MAN-AUTH1-F2 — direção A+C do owner):** (**A**) `prompt="select_account"` no sítio único; (**C**) template próprio `login_denied.html` — nomeia **qual** email foi rejeitado, explica em 2 frases que a causa provável é a sessão do navegador, oferece **"Entrar com outra conta"** (que reentra no fluxo e agora abre o seletor) e rebaixa o *"fale com o administrador"* ao **caso residual** correto. ⛔ `error.html` genérico intacto (segue servindo 404/500 e `admin_required`); zero mudança em sessão/cookie/permissões. Smoke **sobre as rotas reais** (cópia do banco, sem rede): `prompt=select_account` na URL do `/login/google`; 403 exibindo email + explicação + botão, **sem** criar sessão para o rejeitado; caminho feliz logando e emitindo o `remember_token` como antes. ⭐ A medição ad-hoc da tela nova (o gate do [[O7]] **não a alcança** — não há rota sem OAuth) **pegou transbordo a 390px** com email corporativo longo, fechado no nascimento — MAN-AUTH1-REG/**MAN-AUTH1-F1**/**MAN-AUTH1-F2** | Média | ⚠️ **F2 no ar — smoke de prod pendente** (gate [[PROC1]]; o smoke real é o próprio Murilo, no PC do trabalho, vendo o seletor) |
| MAN-AUTH2 | **`next` morto no callback OAuth (cheiro de open redirect se populado) + deep link descartado no `unauthorized_handler`** — dois comportamentos da mesma cadeia: (1) [auth.py:36](routes/auth.py#L36) redireciona o anônimo a `/login` **sem preservar o destino** ⇒ quem abre um link profundo cai na home depois de logar (**medido na F1**: `GET /team/1` → `Location: /login`, sem `next`); (2) [auth.py:88](routes/auth.py#L88) lê `request.args.get("next", ...)` no callback, mas **o redirect do Google não carrega esse parâmetro** — o `next` **nunca chega populado** pelo fluxo real ⇒ **código morto**, e se algum dia passasse a chegar seria `next` **não validado** (destino externo aceito sem checagem — cheiro de **open redirect**). ⚠️ **Natureza dupla, e as duas metades são independentes:** limpeza de código morto **com validação defensiva** (higiene, não muda comportamento observável) × **decisão de produto opcional** — restaurar o deep link ponta a ponta **ou** assumir a home como destino fixo e apagar o resto. Achado de **carona da [[MAN-AUTH1]]-F1** (seção *achados fora do escopo*), não registrado na hora por restrição daquele prompt. ⛔ **Nenhuma direção arbitrada** — MAN-AUTH2-REG | Baixa | 🔲 |
| OPS2 | **Freeze administrativo de sync (janela de operação manual no Sleeper)** — durante operação manual nos rosters (caso de estreia: draft replay do OFF26-30, 18/08), um sync fotografaria o estado transitório (36 como dropados) — sujeira em folha/keeper sheet na semana de cortes. Lição [[OFF26-23]]: **o sistema recusa, não depende da disciplina dos 3 admins**. Flag `sync_frozen` (AppConfig, molde das season flags) + `POST /api/admin/sync_freeze` (admin, liga/desliga manual — **sem TTL, sem auto-destrave**, por decisão de escopo) + **guarda-helper única** `sync_freeze_reason()` consultada pelas DUAS entradas de motor: `run_sync` (recusa **antes de qualquer I/O** — zero rede, zero SyncLog) e `_sync_trades` (o backfill chama direto, sem passar pelo run_sync — mapeado e coberto pelo mesmo helper, nenhuma réplica por porta). Botão da navbar recebe **409 com mensagem acionável** (o banner existente a exibe); card do `/admin` ganha estado 🧊 + toggle. Boot do app degrada gracioso (payload com zeros). `sync_freeze_test.py` (6: recusa pré-I/O com sentinela de rede, 2ª entrada, destravado-passa, toggle, 409 da porta, 403 sem admin); smoke real: congelar → botão 409 + backfill frozen → destravar → sync roda. Gate [[O7]] exit 0 (diff toca admin.html). ⚠️ **ID: o prompt veio MAN-OPS1-*, mas OPS1 é a higiene do working tree (14/08)** — nasceu OPS2, colisão registrada — MAN-OPS1-REG-F2 | Alta (uso imediato 18/08) | ⚠️ **no ar — smoke prod = o próprio uso de hoje** (congelar antes da operação do co-admin) |
| O6 | Split do backlog por campanha: `improvements_off26.md` receberia as seções OFF26-* verbatim (pertencimento por prefixo), Status Rápido segue ÚNICO no ativo, auditor valida a união — **rota CANDIDATA, não decidida**. F1 read-only 13/08: família OFF26 = **49,9% do ativo** (236,3 KB / 13 seções, 8🔲/5⚠️, zero ✅); partição por prefixo tem 3 classes de resíduo; ~97% da família tem fechamento previsto 18–24/08 → **recomendação: NÃO executar agora; re-medir pós-26/08** (sunset natural) e decidir com números; **decisões do owner 13/08 (MAN-O6-REFINE):** split adiado (gate = re-medição pós-26/08) · **B implementada** (leitura seletiva no CLAUDE.md — motivação: consumo de token do Code, não navegação humana) · **D aceita** (OFF27 nasce em arquivo de campanha próprio + retrofit do auditor, 1ª sessão pós-campanha) — MAN-O6-REG/MAN-O6-F1/MAN-O6-REFINE | Média | 🔲 (gate: re-medição pós-26/08) |

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
⚠️ **F2 implementado — validado em localhost; aguarda smoke em prod** — Prioridade **Baixa/Média** — MAN-E3-REG (08/06/2026) / F2 (10/07/2026) — **REG → F2 direto (sem F1)**

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

**F2 — IMPLEMENTAÇÃO (10/07/2026, ⚠️ validado em localhost) — decisão owner: opção (a), remoção completa**

*Escopo:* só a porta de entrada; parser/matching/store/confirm/salary_engine/schema intocados.

*`routes/admin.py` (`espn_import_page`):*
- Removido o branch `else` de download por URL (`requests.get` + `raise_for_status` + flash "Erro ao baixar" + flash anti-bot). O POST agora **exige upload**: sem arquivo → flash "Forneça um arquivo PDF (upload)".
- **Guard `%PDF` preservado** (protege upload corrompido → flash, nunca 500); mensagem reescrita p/ o contexto upload-only (sem menção a download por URL).
- Removida a constante morta `ESPN_DEFAULT_URL` e o `default_url` do render do GET.

*`templates/espn_import.html`:* removido o bloco do input de URL; label "Upload do PDF" (sem "recomendado" — não há mais alternativa); subtítulo/tooltip/botão sem menção a URL ("Processar PDF"). Card "Formato Esperado" intacto.

*Validação localhost:* `salary_engine_test` **48/48**; byte-compile de `admin.py` OK; `espn_import.html` parseia (Jinja); grep confirma **zero resquício** de `default_url`/`ESPN_DEFAULT_URL`/`name="url"`/fetch de download no fluxo de import (o `import requests` remanescente é do `offseason.py`, não relacionado). **Pendente:** smoke em prod (upload real → review → confirm; upload inválido → flash sem 500).

**DEPENDÊNCIAS**
- Depende de: **[[E1]]** (✅ — upload é o caminho funcional comprovado em prod).
- Relaciona-se com: **[[E5]]** (mesma UI de import, melhorada nesta sessão). Bloqueia: nenhum.

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
- **⚠️ NOTA DP3 (31/07/2026): reescopo agora desbloqueado (DP3 ✅).** A REFINE do [[DP3]] concluiu
  que a metade "generalizar/migrar `RookieEspnValue`" **colide** com a natureza nova da tabela
  pós-DP3 (membership da classe entrante via `in_class` + valor opcional — semântica sem casa no
  `EspnValueStore`, que é `(sid, season, valor)` puro). Sequenciamento decidido: reescopar **depois
  do DP3** — **o DP3 fechou ✅ em 31/07/2026, então a condição está satisfeita**. Ao reabrir este
  item: manter o DROP do `ESPNValue` legado; a metade RookieEspnValue é reenquadrada/cancelada em
  sessão própria (a tabela agora é membership+valor, não só valor órfão). Escopo acima ainda **não**
  foi reescrito.

---

### E5 — Microcopy do review do import ESPN contradiz o pipeline do store ("todos receberão $1")
⚠️ **F2 implementado — validado em localhost; aguarda smoke em prod** — Prioridade **Média** — MAN-E5-REG (09/07/2026) / F1 / F2 (10/07/2026)

**CONTEXTO**
O review do import ESPN exibe, no cabeçalho da seção "Não Encontrados", o texto
**"todos receberão $1"**. Esse texto é **anterior ao [[E2]]**: desde o **E2-F2**,
entradas `not_found` com valor > 0 resolvidas a `sleeper_id` vão para o store
(`RookieEspnValue`) no confirm, e o salário no rookie draft é **`floor(ESPN×1.2)`** via
fonte única (`year1_salary`), não $1. O caso de validação do E2-F2 foi o próprio
**Jeremiyah Love** (adj 55 → salário $55, não $1). O "$1" só permanece verdadeiro para
as subclasses **excluídas do store** ($0, K/DST, resolução ambígua). O texto stale
comunica falha no **caminho feliz** e **travou uma operação real de co-admin em prod**
(Rafa).

**PROBLEMA / OPORTUNIDADE**
A microcopy orienta a decisão do admin no **momento do confirm** — a superfície de maior
dano para uma divergência docs×código. Ao afirmar "todos receberão $1", contradiz o
pipeline real pós-E2 e faz o admin acreditar que rookies com valor ESPN serão zerados,
quando na verdade vão para o store e recebem `floor(ESPN×1.2)`. Escopo do item: alinhar
a comunicação da tela ao pipeline real — corrigir o microcopy stale e **comunicar o
destino real de cada classe** de "Não Encontrados" (com valor>0 → store; $0 / K-DST /
ambíguo → $1/excluído).

**EVIDÊNCIA**
- Screenshot de prod (09/07/2026, operação real do co-admin Rafa): cabeçalho
  "**Não Encontrados (85) — todos receberão $1**"; **Jeremiyah Love ARI $46** listado.
- Classe do problema: **divergência docs×código** (lente 6 do [[AUD1]]), na superfície
  de maior dano (microcopy que orienta decisão do admin no confirm).

**DISCUSSÃO / QUESTÕES EM ABERTO (F1)**
- Onde vive o texto ("todos receberão $1") — template do review do import ESPN? Há
  réplica?
- O texto deve enumerar o destino por classe (valor>0→store vs. $0/K-DST/ambíguo→$1)?
- A tela distingue hoje visualmente as subclasses de "Não Encontrados", ou lista tudo
  num bloco único?

**F1 — ACHADOS (diagnose read-only, 10/07/2026 — concluída)**

**VEREDITO: problema de TEXTO PURO.** Nenhum bug de comportamento. O pipeline pós-E2 está
correto no código; só a microcopy da tela mente. Escopo do F2 **não** muda.

*1) Inventário de microcopy (todos os textos de destino de valor do fluxo import ESPN):*

| # | Local | Texto | Veredito | Evidência (código) |
|---|-------|-------|----------|--------------------|
| 1 | `espn_review.html:84` | "Não Encontrados — **todos receberão $1**" | **STALE/FALSO** p/ skill valor>0 | `confirm` manda `not_found` p/ `_resolve_not_found_to_store` (admin.py:725,731); nenhum Player recebe $1 |
| 2 | `espn_review.html:70` | opção skip "**Nenhum (aplicar $1)**" | **STALE/FALSO** p/ approximate-skip resolvível | approximate não-resolvido também vai ao store (admin.py:726-729); só cai em $1 se excluído do store |
| 3 | `espn_review.html:190` (JS) | "`${total_notfound}` **com $1**" | **STALE** (superestima) | `total_notfound` = approx-unresolved + `len(not_found)` (admin.py:714,717); parte foi ao store |
| 4 | `espn_review.html:101` | "Ausentes no PDF — **receberão $1**" | **CORRETO** (classe distinta) | `absent` são Players do DB → `_save_espn_value(pid, 0.0, 1.0)` (admin.py:736-738) grava `espn_ref_value=1.0` de fato |
| 5 | `espn_import.html:93` | "Jogadores com **$0 recebem espn_adjusted=$1**" | **CORRETO** | parser: `espn_adjusted = max(1.0, int(raw*1.2))` (espn_pdf_parser.py:129) |
| — | `admin.py:716` | comentário "`# Not found + absent → $1`" | **STALE** (comentário de código, não UI) | contradiz o store logo abaixo; fora do escopo de UI, mas registra a mesma confusão |

*2) Destino REAL por subclasse de "Não Encontrados" (bucket é um MIX; o header achata tudo p/ $1):*

| Subclasse | Vai ao store? | Salário se materializada no draft | Claim "$1"? |
|-----------|---------------|-----------------------------------|-------------|
| Skill, valor>0, sid resolvível | **SIM** (`RookieEspnValue`) | `floor(ESPN×1.2)` via `year1_salary("rookie_draft",...)` = `max(1,int(adj))` | **FALSO** (>$1 p/ valor>0) |
| Valor $0 | Não (`espn_raw<=0` skip, admin.py:552) | $1 (`floor(0)`=max(1,0)) | Verdadeiro |
| K/DST | Não (skip explícito, admin.py:550) | $1 se criado (fora do cap de qualquer forma) | Verdadeiro |
| Ambíguo (sid não único) | Não (`_resolve_entry_sid`→None, admin.py:533,556) | $1 (sem valor no store) | Verdadeiro |
| Pool Sleeper indisponível | Não (resolução falha → todos ambíguos/exceção, admin.py:732) | $1 | Verdadeiro (degradação) |

**Jeremiyah Love (skill, ARI, raw $46, sid resolvível):** classificado **store** → adj `int(46×1.2)=55` → salário **$55** no draft, **NÃO $1**. Idem **Carnell Tate** (raw $12 → adj 14 → **$14**). Ambos sob o header "todos receberão $1" na evidência — exatamente o texto stale.

*3) Existe caminho que aplica $1 a entrada coberta pelo store?* **NÃO.** No confirm, `not_found`/approx-skip **não escrevem Player nenhum** — só `upsert_rookie_espn` no store; `total_notfound` é **contador de exibição**, não escrita. No draft, `draft_import.py:132-135` e `record_acquisition` leem o store (`rookie_espn_adjusted`) → `floor(ESPN×1.2)`. $1 só surge quando o store está vazio p/ o sid (subclasses excluídas) — comportamento correto, não bug.

*4) Réplicas (busca pelo padrão de saída "$1"/"receber"/"not_found"/"com $1" em templates+JS+routes):* a semântica de destino-de-valor do fluxo import ESPN vive em **4 pontos, todos em `espn_review.html`** (linhas 70, 84, 101, 190) — **sem réplica** em outro template, JS externo ou flash de rota. Demais hits de "$1" (salary.html, auction.html, admin_review.html) são regras de salário não relacionadas (waiver/FA ano1, min rookie, default unknown). O único eco fora da UI é o **comentário** `admin.py:716`.

*5) Sinal já pronto p/ o F2 comunicar destino por classe (sem backend novo obrigatório):*
- **Pós-confirm:** a resposta do `/confirm` **já retorna** `rookie_store: {resolved, ambiguous, skipped}` (admin.py:764) — o JS da linha 190 **ignora**. F2 pode mostrar o split real ("X → store de rookie, Y → $1") reusando o que já volta.
- **Pré-confirm (render do review):** o split **não** é computado hoje (a resolução só roda no confirm). As entradas de `not_found` já carregam `name/nfl_team/position/espn_raw`; o classificador é **derivável no render** reusando os helpers **read-only** existentes (`_build_pool_index`/`_resolve_entry_sid`/regra `_resolve_not_found_to_store`) — pequeno acréscimo de backend, decisão do F2.

*Observação (não infla o E5, não é item novo):* o texto #4 (absent→$1) é **CORRETO** mas revela que Players do DB **ausentes do Top-300 têm `espn_ref_value` sobrescrito p/ $1** a cada import (admin.py:738). É comportamento **pré-existente e plausivelmente intencional** (jogador saiu do ranking → valor ~$1); **não** é a classe "store recebe $1" do ponto 3. Registrado como observação p/ ciência do owner; sem criar item até ficar caracterizado como defeito.

*Premissas do prompt contradichas pelo código:* **nenhuma.** Todas as premissas (not_found skill valor>0 → store → `floor(ESPN×1.2)`; "$1" só p/ excluídas; Love como caso feliz) batem com o código.

**F2 — IMPLEMENTAÇÃO (10/07/2026, ⚠️ validado em localhost) — decisão owner: opção (b), tela auto-explicativa; só comunicação, comportamento intacto**

*Classificador único (fonte da decisão store×$1, read-only):* novo `_classify_not_found_entry(entry, idx)` (`routes/admin.py`) retorna `('store', sid)` ou `('excluded', motivo∈{kdst,zero,ambiguous})`. `_resolve_not_found_to_store` foi **refatorado p/ consumi-lo** (contagens `resolved/ambiguous/skipped` idênticas às de antes — predicado preservado byte-a-byte: K/DST→skip, $0→skip, sid None→ambíguo, senão upsert). O mesmo classificador alimenta o split do render → **o texto da tela não pode divergir do que o confirm faz**.

*Split server-side no render (`espn_review_page`):* computa `nf_store` (entrantes que resolvem a sid; cada um com `projected_salary` via **`salary_engine.year1_salary`** — fonte única, sem replicar a conta em template/JS) e `nf_excluded` ($0/K-DST/ambíguo/pool-indisponível). Sem novo caminho de escrita; pool indisponível → tudo em `nf_excluded` (mesma degradação do confirm).

*Textos corrigidos (`templates/espn_review.html`):*
1. Seção "Não Encontrados" agora **dividida por destino**: 🟢 "Entrantes → store de rookie (N)" com texto de salário projetado `floor(ESPN×1.2)` e tag `raw → $proj`; ⚪ "Sem valor aproveitável → $1 (N)" ($0/K-D-ST/ambíguo). Soma dos dois = total de não-encontrados.
2. Opção de skip dos aproximados: "Nenhum (aplicar $1)" → "**Nenhum destes (→ store de rookie, ou $1 se sem valor)**".
3. Resumo pós-confirm (JS): consome `d.rookie_store` → "`resolved` → store de rookie (salário projetado), `ambiguous+skipped` → $1" (era "`total_notfound` com $1", que superestimava).
4. "Ausentes no PDF": header + parágrafo explicitando **regra de liga** (veterano fora do Top-300 → referência $1); **comportamento intacto** (`_save_espn_value(pid, 0.0, 1.0)`).
5. Comentário stale `admin.py:716` reescrito (contador de exibição, não escrita de $1).

*Validação localhost:* `salary_engine_test` **48/48**; ambos os templates parseiam (Jinja); byte-compile de `admin.py` OK; teste sintético do classificador — Jeremiyah Love (adj 55)→store **$55**, Carnell Tate (adj 14)→store **$14**, D/ST→$1 (kdst), $0→$1 (zero), ambíguo→$1; **soma store+excluded = total** (partição correta). **Pendente:** smoke em prod (render do review + confirm com PDF real).

**DEPENDÊNCIAS**
- Relaciona-se com: **[[E2]]** (store — ⚠️), **[[E2-RISK]]** (✅), **[[E4-a]]** (✅ —
  split de referência 211/5/84/62), **[[E3]]** (limpeza da mesma UI de import — 🔲;
  relaciona-se, **não bloqueia**). Não bloqueia itens abertos.

---

### DP1 — Board de planejamento de cap pré-draft (rookies)
⚠️ **Implementado (F2) — validado em localhost; smoke em prod pendente** — Prioridade **a definir** — MAN-DP1-REG (08/06/2026) / F1 / F2 (10/06/2026) — **F1 ✅ diagnose read-only concluída** (achados absorvidos abaixo); **F2 ✅ board + simulação multi-pick no backend** (validado localhost: `salary_engine_test` 48/48 verde, smoke das rotas OK; ⚠️ → ✅ só após smoke em prod)

> **NOTA DE REVISÃO (12/06/2026, ver [[DP2]]):** a base da simulação do DP1-F2 — "roster integral
> com salário ATUAL; cenário vazio = budget atual" (decisão explícita da F2 abaixo) — foi
> **conscientemente revisada pelo DP2**. O fluxo virou uma cadeia só: a simulação de rookies passa a
> partir do **cenário keep/corte** (com salário projetado, base idêntica à do summary do F10), e os
> números de cap/budget/spots passam a viver numa **barra sticky única**. O endpoint `/simulate` do
> DP1-F2 foi **removido** (fundido no `/budget` canônico do F10 estendido com `rookie_sids`). O
> histórico do DP1 abaixo fica como está (registro da decisão original); o comportamento vivo é o do
> DP2.

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

### F14 — Nomes do board de rookies sem sufixo de geração
🔲 **Registrado 31/07/2026** — MAN-F13-CLOSE (achado do smoke; **cosmético, não implementar agora**) — Prioridade **Baixa**

**PROBLEMA / OPORTUNIDADE**
Com o [[DP3]] a lista do board passou a vir do **pool do Sleeper** (via captura), e os nomes
exibidos perderam os **sufixos de geração** (Jr., II, III…) que a fonte ESPN carregava — o
`full_name` do Sleeper às vezes não os traz. **Não afeta identidade** — o board casa e projeta por
`sleeper_player_id` (resolvido no matcher E4-a / captura), não por string de nome; é só o rótulo na
tela. Puramente cosmético.

**CAMINHOS A AVALIAR (não decididos)**
- Preferir o nome da fonte ESPN quando houver (o `RookieEspnValue.name` do import pode ter o sufixo).
- Ou compor o sufixo a partir de outro campo do pool.

**DEPENDÊNCIAS**
- Relaciona-se com: [[DP3]] (board), [[E2]] (store de nome). Bloqueia: nada.

---

### F15 — Remover edição manual de picks (obsoleta pós-S2)
🔲 **Registrado 17/08/2026 (MAN-PICKEDIT-REG)** — Prioridade **Média** — **registro apenas; nenhuma
alteração de código**

**DECISÃO DO OWNER (17/08/2026)**
A funcionalidade de **editar picks manualmente** (via PATCH `/api/picks/<id>` + modal ✎ no board)
deve ser **removida, não escondida**. Ela nasceu na era em que a titularidade de uma pick podia
divergir entre o Sleeper (autoridade temporária) e o Manager (autoridade de projeção). Desde o
[[S2]] o sync é **determinístico**: a permutação administrativa é descontada ao ingerir
`/traded_picks`, e não há caso legítimo de divergência que justifique uma mutação manual paralela —
é risco de inconsistência, não conveniência.

**SINTOMA ORIGINAL (achado MAN-UX20-F1)**
O botão ✎ do board global de picks aparece para **todo usuário** (sem gate de admin no template); a
falha para não-admin é **silenciosa** (`savePick` não trata a resposta de permissão negada — 403 é
engolido). A decisão de remover é mais forte que a de esconder: fecha a questão de raiz.

**ESCOPO EM DUAS PARTES, COM DESTINOS DISTINTOS**

- **UI: ✅ FECHADA de carona na [[UX20]] (17/08/2026, MAN-UX20-F2, validada em prod no
  MAN-UX20-DONE).** O redesenho reconstituiu as células sem o botão, e o cliente perdeu o `✎`, o
  modal `#pick-modal` e os handlers `openPickEdit`/`closePick`/`savePick` — mais o `resetPick()`
  que já era **código morto**. Render medido: **0 ocorrências**. ⇒ o sintoma original (botão
  visível para todos, 403 silencioso) **não existe mais**.

  ⛔ **O que sobra deste item é SÓ o backend** — e o `🔲` no topo se refere a ele. A rota PATCH
  continua viva **de propósito**: removê-la sem a conferência abaixo é que seria o risco.

- **Backend: trabalho próprio** — antes de remover a rota `/api/picks/<id>` (PATCH) e o handler
  `update_pick`, conferir se existe consumidor **além do modal ✎ do board** que a chama:
  - ⏤ Scripts de seed ou migration?
  - ⏤ Testes unitários que a cobertura depende?
  - ⏤ Sync ou importador (draft_import, auction) que use a rota?
  - ⏤ Outro sítio da UI que não o board?

  **Conferência é pré-requisito:** se houver consumidor fora do board, reportar antes de remover —
  a decisão de remover também esse consumidor é do owner, não do item.

**RELAÇÕES**
- [[UX20]] ✅ (o redesenho **já absorveu** a remoção de UI — seção detalhada no
  `improvements_archive.md`; o pré-requisito de UI está **cumprido**).
- [[S2]] (a razão de a funcionalidade ser obsoleta — S2 tornou o sync determinístico).

---

### S5 — Tela que prescreve a permutação do board ao co-admin (ex-fatia F2-3 do S2)
🔲 **Registrado 02/08/2026** — MAN-S2-DONE (fatia **não iniciada**, desmembrada do [[S2]] no
fechamento para não se perder na migração O3) — Prioridade **Média** — família [[S1]] / [[S2]]

**CONTEXTO**
O [[S2]] ✅ entregou o **desconto** da permutação administrativa (`board_mirror.py`): dado que o
board do Sleeper foi montado, o Manager desfaz a ficção ao ler `/traded_picks`. A F1b recomendou
**três** fatias; as duas primeiras estão em produção, esta é a terceira.

**O QUE FALTA**
Hoje a montagem é **conhecimento tácito do co-admin**: ele decide quais picks permutar na UI do
Sleeper, e o owner arma o toggle depois. O desconto assume que a montagem seguiu exatamente
`π = S⁻¹∘L`. A tela fecharia o laço: o Manager **calcula π**, **emite a lista exata de permutações**
a executar no Sleeper, e só então oferece o armamento — passando de "torcer para que a montagem
tenha sido a esperada" para "o Manager prescreveu, logo sabe o que vai ler de volta".

**POR QUE NÃO É URGENTE**
O desconto **já se protege** do caso ruim: `build_permutation` exige **bijeção**, e board
meio-montado desliga o desconto em vez de corromper (ver F2 do S2, no archive). O risco residual é
uma montagem **completa mas diferente** da prevista — possível, mas exigiria o co-admin inventar
outra convenção. A tela elimina esse resíduo e, principalmente, **remove o conhecimento tácito**.

**ESCOPO PROVÁVEL (a refinar em F1)**
- Superfície na intertemporada (passo do lottery) ou no `/admin`, ao lado do toggle já existente.
- Lê π de `board_mirror.build_permutation` — **fonte única já implementada**, sem recomputar.
- Renderiza as permutações como instrução operacional ("mover a pick R1 de X para Y"), no espírito
  do [[OFF26-5]] (runbook do Cowork).
- Idealmente **arma o toggle no mesmo fluxo**, para que declarar "montei" e "está montado" sejam o
  mesmo ato.

**QUESTÕES EM ABERTO** (F1)
- A tela deve **verificar** a montagem depois de feita (comparar `/traded_picks` com π esperado e
  reportar divergência), ou só prescrever? Verificar é mais forte e é barato — a F1a já fez isso
  manualmente.
- Cabe no `/offseason` como sub-passo do lottery, ou é card do `/admin`?
- Vale gerar o runbook em texto copiável (padrão [[OFF26-5]]) para o co-admin seguir fora do app?

**DEPENDÊNCIAS**
- Depende de: [[S2]] ✅ (o `board_mirror.py` já expõe π). **Não bloqueia nada** — o desconto opera
  sem ela. Relaciona-se com [[M16]], [[M8]], [[OFF26-5]].

---

### S4 — Histórico (`PlayerHistory` / `Trade`) sem chave estável de time
🔲 **Registrado 02/08/2026** — MAN-S4-REG (**registro apenas** — nenhum código, nenhum dado do banco
tocado) — Prioridade **Média** — família [[S1]] / [[S3]]; achado colateral da **S3-F1**

**CONTEXTO**
A diagnose do [[S3]] (commit `be16de1`) fechou o match de picks por nome, mas ao varrer a classe
inteira encontrou **dois domínios sem chave estável nenhuma** — não é que a chave exista e não seja
usada (caso do S3), é que **ela não existe no schema**.

**MECANISMO — o nome está dentro da chave de dedupe**
`PlayerHistory` guarda o time só como **`team_name` string** (`models.py:780`); não há `team_id`. E
esse campo participa do **índice UNIQUE** que o [[F8]]a criou para garantir idempotência do rebuild
canônico do histórico (Migration 5, `app.py:361`):

```
UNIQUE (player_id, season, event_type, team_name, sleeper_event_ref)
```

O quinteto foi desenhado para que o mesmo evento, re-ingerido, **colida** e seja descartado. Como o
`team_name` é gravado a partir do nome vivo no momento da escrita
(`models.py:232,237` — `team_name = player.team_rel.name`), um rename de time faz o **mesmo evento**
passar a ser gravado com um valor diferente na quinta posição da chave.

**GATILHO E CONSEQUÊNCIA**
O sync renomeia `Team.name` a partir do Sleeper (`sync_sleeper.py:181-189`). A partir daí, qualquer
re-execução do rebuild/backfill do histórico grava as linhas do time renomeado com o nome **novo** —
que **não colide** com as linhas antigas. **A idempotência do histórico deixa de valer** e os eventos
duplicam silenciosamente. É a mesma família do [[F7]] (SalaryHistory duplicado), com a agravante de o
duplicado aqui ser *legítimo* aos olhos do índice.

**SEGUNDA SUPERFÍCIE — `Trade` também é name-only**
`Trade.team_a` / `Trade.team_b` são strings (sem FK). `routes/roster.py:245-250` resolve a
contraparte de uma trade **comparando strings** entre a linha de `Trade` e o `team_name` da
`PlayerHistory`. Trades antigas guardam o nome velho e o histórico novo guarda o novo → a comparação
falha, cai no ramo `else` e o **timeline do jogador perde a contraparte** da trade.

**DISTINÇÃO EM RELAÇÃO AO [[S3]] — por que não cabia lá**
| | [[S3]] (picks) | **S4** (histórico) |
|---|---|---|
| chave estável no schema | **já existe e já está correta** (`Pick.original_team_id`/`current_team_id`) | **não existe** — `PlayerHistory` e `Trade` só têm nome |
| mudança de schema | **nenhuma** | **inevitável** (coluna nova + FK) |
| migração de dado gravado | **nada a migrar** (ids já corretos) | **necessária** — 1.151 linhas de `PlayerHistory` + 53 de `Trade` a resolver por nome histórico, incluindo nomes que já não existem |
| toca índice/auditoria | não (o [[M8]] fica intacto por construção) | **sim** — mexer no UNIQUE do F8a é mexer na garantia de idempotência do rebuild |
| urgência | **bloqueia o retorno do sync** | não bloqueia — degrada o histórico, não o corrompe hoje |

**CASO CONCRETO PENDENTE**
O rename do time 9 (**"Tropa do Bicampeonato 🏆" → "Tropa do Jarra 🏆"**) já está feito no Sleeper e
**ainda não foi ingerido**. Ele é o gatilho tanto do S3 quanto desta classe: quando o sync voltar a
rodar (após o S3-F2), o nome novo passa a ser gravado no histórico. **Não é urgente como o S3** — o
dano só aparece se o rebuild/backfill do histórico for re-executado depois do rename — mas a partir
daí a proteção do F8a está furada.

**QUESTÕES EM ABERTO** (F1)
- **Desenho da chave estável:** adicionar `team_id` (FK) a `PlayerHistory` e `team_a_id`/`team_b_id`
  a `Trade`, mantendo o nome como snapshot histórico? Ou substituir o nome? *(o nome tem valor
  próprio: registra como o time se chamava à época — remover perderia informação)*
- **Índice UNIQUE do [[F8]]a:** trocar `team_name` por `team_id` no quinteto, ou remover o time da
  chave? Qual das duas preserva a intenção original (múltiplos eventos do mesmo tipo/season/time
  distinguíveis por `sleeper_event_ref`)? Recriar o índice exige migração e **revalidar o rebuild
  canônico** — o F8a é o dono dessa garantia.
- **Migração do histórico gravado:** resolver `team_name → team_id` por lookup em `Team.name`
  funciona para os nomes atuais; e para nomes que **já não existem** (times renomeados antes deste
  fix, ou grafias com espaço duplo/emoji)? Precisa de mapa manual? Quantas linhas ficam órfãs?
- **`Trade`:** a resolução de contraparte em `roster.py:245-250` some com a chave estável, ou exige
  fix próprio?
- **Alcance:** há outros índices, dedupes ou joins que usem `team_name` como chave funcional além
  destes dois? (a S3-F1 mapeou `AuctionLog`, `SeasonStandings` e `DraftLotteryResult` como
  **snapshot de display com `team_id` disponível** — fora do risco)

**DEPENDÊNCIAS**
- Depende de: nada (independente). Relaciona-se com [[S3]] (mesma classe, chave estável ausente em
  vez de ignorada), [[F8]]/[[F8a]] (dono do índice UNIQUE), [[F7]] (precedente de histórico
  duplicado), [[E4-b]] (identidade por string). **Não bloqueia** o [[S2]] nem o [[S3]].

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

⚠️ **Fronteira com o [[MAN-METH-2]] (registrada 14/08/2026):** as duas ocorrências abaixo que
acontecem **antes de executar** (AUD1-F1 pré-execução e MAN-O6-REFINE) são **precedente** do
MAN-METH-2, não deste item. A divisão: **aqui** a regra é sobre o **entregável da F1** — a seção
"REFUTAÇÃO DE PREMISSAS" que as diagnoses passaram a carregar; **lá**, sobre uma **fase que
precede e bloqueia a execução de um prompt de F2**, inclusive quando **não houve F1**. Mesma
lição de fundo (premissa de prompt é hipótese, não ordem), mecanismos distintos.

**Ocorrência adicional (MAN-O6-REFINE, 13/08/2026 — a pedido do owner):** a avaliação prévia do
prompt (antes de executar) refutou uma **restrição embutida** que produziria texto incoerente — a
Parte 4 mandava corrigir "restrito ao emoji divergente", o que geraria `⚠️ **Pendente**` (emoji ×
palavra se contradizendo) nos casos OFF26-4 e F9. Calibragem aprovada pelo owner ANTES da
execução: emoji + palavra de status imediatamente adjacente, nada além. Mesma família das
ocorrências F1: a premissa/restrição do prompt é hipótese a validar contra o efeito real, não
ordem literal.

---

### MAN-METH-2 — Parecer pré-execução como fase do fluxo (F2 em caminho crítico)
🔲 **Registrado 14/08/2026 (MAN-METH-REG-PARECER)** — Prioridade **Média** — **registro apenas:
o `DEV_METHODOLOGY.md` NÃO foi editado nesta sessão** — decisão do owner de adotar a prática como
padrão, tomada sobre o resultado da sessão MAN-OFF26-25 do mesmo dia

**A prática, numa linha:** antes de executar um prompt de **F2**, o Code analisa o prompt **contra
o código real** e **para**, esperando as decisões do owner — em vez de implementar o enunciado à
risca e descobrir os problemas depois, dentro do diff.

**O que o parecer entrega** (forma exercida no caso de referência, a refinar na F2):
1. **Premissas refutadas, com evidência** — arquivo:linha, não impressão.
2. **Furos de desenho** — casos em que o enunciado, implementado como está, produz resultado
   errado (distinto de "premissa falsa": o enunciado pode partir de fato correto e ainda assim
   especificar um mecanismo furado).
3. **Réplicas que o escopo criaria** — o que o item duplicaria de algo já existente.
4. **Decisões em aberto**, com recomendação — o que o prompt deixou para a implementação decidir
   e que na verdade é do owner.
5. **Riscos de calendário** — o que muda por estar perto de uma data crítica.

⭐ **Caso de referência — MAN-OFF26-25 (14/08/2026), o gate mecânico do rollover.** O parecer
produziu, antes de uma linha de código:
- **Erro factual:** o enunciado falava em *"import FINAL (`is_final`)"* no `espn_import_log` — a
  coluna **não existe** ali; o campo é `status` (`'provisional'|'final'`), e `is_final` é de
  `ESPNValue`. Consequência prática: um grep pelo nome errado.
- ⭐ **Furo de CORREÇÃO (o achado que pagou a fase):** o predicado pedido — *"existe um import
  final da season alvo"* — daria **falso OK**. `set_espn_value` sobrescreve `espn_ref_value` em
  toda importação, então reimportar uma provisória **depois** da definitiva devolve o banco ao
  estado provisório enquanto a linha `final` antiga permanece no log. **Uma trava que mente é
  pior que trava nenhuma.** O conserto custou um `order_by` — e teria custado um incidente em
  produção se descoberto depois.
- **Réplica:** o escopo criaria a **3ª e 4ª cópias** da definição *"a tabela definitiva entrou"*,
  contra a convenção do repo ([[OFF26-16]], [[L3]], `keeper_exclusion`). O helper único que saiu
  daí fechou o [[UX19]] **de carona**.
- **4 decisões em aberto** devolvidas ao owner (aposentar × manter a flag manual — respondida com
  grep, inclusive no `fantasy_optimizer`, que **não** a consome; recusa dura × `force`; código de
  status; consequência operacional de o checkbox esquecido virar bloqueio duro).
- **Risco de calendário:** mudança no caminho crítico a 4 dias do evento, no **mesmo arquivo** que
  já brickou uma vez ([[OFF26-23]]-FIX, 10/08) — do que saiu a condição de push "smoke em
  navegador real".

**Escopo da F2 (o que falta decidir e escrever):**
- **Gatilho:** hoje é *"quando o owner solicitar"*. A F2 define os **critérios de recomendação** —
  a lista de partida é F2 em caminho crítico · mutação irreversível · itens que tocam
  `salary_engine`, schema ou contratos. ⚠️ Decidir se algum caso vira **automático** (o Code
  emite o parecer sem pedido) ou se a fase permanece **sempre sob pedido** — é decisão do owner,
  não da implementação.
- **Custo × benefício:** registrar que a fase **gasta uma rodada** e que isso é o preço; e o
  contrapeso — quando o parecer não se justifica (fix mecânico, item pequeno, escopo já medido
  por uma F1 recente).
- **Forma de saída:** as 5 seções acima viram roteiro fixo ou lista de verificação?
- **Transversalidade:** o `DEV_METHODOLOGY.md` serve **manager / optimizer / predictor** — a F2 o
  trata como tal (o caso de referência é do manager, a regra não é).

⚠️ **Não duplica o [[MAN-METH-REG]]** — a fronteira está registrada nos dois itens. Lá, a regra é
sobre o **entregável da F1** (a seção "REFUTAÇÃO DE PREMISSAS" que as diagnoses carregam); aqui, é
uma **fase que precede e bloqueia a execução**, e que cobre o caso em que **não existe F1**: o
OFF26-25 foi de registro (pela auditoria PREFLIGHT) direto a F2, e a regra do MAN-METH-REG não
teria disparado.

**Cross-refs:** [[MAN-METH-REG]] (a regra irmã, com as 2 ocorrências pré-execução que são
precedente deste item), [[OFF26-25]] (o caso de referência), [[UX19]] (fechou de carona por causa
do parecer), [[OFF26-23]] (o precedente de risco de calendário e a diretriz de poka-yoke que o
parecer invocou).

---

### PROC2 — Surfacear o hash deployado (`RENDER_GIT_COMMIT`) no `/admin`
🔲 **Registrado 23/06/2026** — **repriorizado Baixa → Média em 14/08/2026 (MAN-CLOSE-LOTE-14-08)**
— follow-up do [[PROC1]] (ressalva da F1) — **robustez além de disciplina**

**Motivação nova (14/08/2026) — a lacuna que a disciplina sozinha não fecha:** a sessão
**MAN-UX-BID0-F2** ([[UX18]]) **não conseguiu cumprir o [[PROC1]] por artefato servido**. O padrão
que vinha funcionando — baixar o arquivo público e conferir que ele é **byte-idêntico** ao do
commit (foi assim no [[L3]] e no [[UX16]], com o `style.css`) — **não estava disponível**: o diff
daquela sessão era só **Python + templates autenticados**, e **nenhum arquivo público mudou**.
Sem artefato para comparar, a confirmação do deploy degradou para **evidência circunstancial de
restart** (transição de resposta do serviço), que é indício, não prova.

⇒ **A prova por artefato servido é acidental, não estrutural:** ela só existe quando o diff, por
acaso, tocou um arquivo público. Este item torna a prova **direta e independente do conteúdo do
diff** — o commit vivo é lido do próprio app. É por isso que a prioridade subiu.

**Por quê:** o [[PROC1]] ancorou o gate de hash deployado como **regra de disciplina** no
`DEV_METHODOLOGY` (checklist de fim de sessão). A F1 do PROC1 registrou que **gate de
disciplina não é à prova de falha** — o bullet "✅ só em prod" já existia e mesmo assim o
[[E1]] falhou. Este item reduz a fricção que contribuiu para o miss do [[E4-a]] ("abrir o
painel do Render para conferir o hash live").

**Escopo (a refinar em F1/F2):** expor `RENDER_GIT_COMMIT` (env injetada pelo Render) em uma
superfície já existente — provável `/admin` (`routes/admin.py:13`, espelhando o padrão de
`last_sync`/`f8_snapshot`), ~3 linhas — para o owner conferir o hash live **dentro do app**,
sem o painel do Render. Comparação automática live×esperado (bloqueio/alerta) é variante mais
pesada, provavelmente desproporcional ao fluxo solo/trunk — decidir na F1.

**Restrições:** é **código** (não cabia no docs-only do PROC1). Não criar CI/hook nesta fatia
sem decisão explícita.

**Dependências:** complementa o [[PROC1]] (não o bloqueia — a regra de disciplina já vale).

---

### E4-d — Matching frouxo nas portas do /auction (single-entry + Excel)
🔲 **Registrado 11/06/2026 (achado AUD1 Lente 4); F1 diagnose read-only executada 16/06/2026
(MAN-E4-d-F1 — nada alterado, item segue 🔲)** — Prioridade **Baixa/Média** — família [[E4]]

**Registro original (AUD1):** (1) single-entry FA/rookie matcha player por nome exato sem resolver
sid; (2) upload Excel matcha Team por substring `%name%`. A F1 abaixo confirma, quantifica e estende.

#### F1 — Mapa de identidade das 4 portas do `/auction` (read-only)

Helper canônico `record_acquisition` (models.py:340) aceita `player` OU `player_name`+`sleeper_player_id`,
mas **o matching/resolução de identidade é do CHAMADOR** (o helper só escreve). As 4 portas resolvem
identidade ANTES de chamar o helper, e nenhuma passa `sleeper_player_id`:

| Porta | JOGADOR (como resolve) | TIME (como resolve) | Falha de jogador hoje | Falha de time hoje |
|---|---|---|---|---|
| **FA individual** (`register_fa_auction`, auction.py:49-52) | `Player.name.ilike(player_name)` exato-ci, escopado a `team_id`. Sem normalização (acento/sufixo), **sem sid** | `Team.query.filter_by(name=...)` **exato** (l.42) | miss → `player=None` → helper **cria órfão silencioso sem sid** (parece sucesso) | not found → **404 visível** |
| **Rookie individual** (`register_rookie`, auction.py:90-93) | idêntico à FA (exato-ci, team-scoped, sem sid) | `filter_by(name=...)` **exato** (l.84) | igual → **órfão silencioso** | **404 visível** |
| **Bulk** (`bulk_register`, auction.py:141-143; pós-F9) | idêntico (exato-ci, team-scoped, sem sid) | `filter_by(name=...)` **exato** (l.127) | igual → **órfão silencioso** | erro na lista (visível) |
| **Excel** (`upload_excel`, auction.py:217-219) | `find_player_by_name()` (player_lookup — normalizado, **melhor**), mas **sem sid** e **sem escopo de time** | `Team.name.ilike(f"%{team_name}%")` **SUBSTRING** (l.219) | miss → skip + erro visível (**não** cria) | substring casa **time errado em silêncio** |

**Régua canônica existente (referência, não alvo):** resolver `_resolve_entry_sid` (admin.py:520,
Brown-safe: nome+**nfl_team**→sid, ambíguo→None) + `_build_pool_index` (admin.py:500) + lookup
`find_player_by_sleeper_id` (player_lookup.py:53) + guard E4-b (import_csv.py:78-158: nome não casou →
resolve sid → acha Player canônico por sid → atualiza em vez de inserir órfão; cria com sid ou marca
`needs_review`). **`draft_import` já é sid-first** (find_player_by_sleeper_id + passa `sleeper_player_id`
ao helper) — é o **modelo bom** a espelhar.

**A lógica frouxa está replicada em mais de um lugar? — RESPOSTA EXPLÍCITA:**
- **Jogador por nome-sem-sid:** replicado nas **3 portas individuais** (FA/rookie/bulk, `Player.name.ilike`
  cru, idêntico) + Excel (variante melhor via `find_player_by_name`, ainda sem sid). **Tudo dentro de
  `auction.py`** — não vaza para outras rotas de escrita: o único outro chamador de `record_acquisition`
  (`draft_import`) já resolve por sid. `roster.py:332` (`Player.name.ilike('%q%')`) é **busca de UI**, não
  porta de aquisição — fora de escopo.
- **Time por substring `%...%`:** **isolado em 1 linha** — `auction.py:219` (Excel). Grep em todo o
  codebase: nenhuma outra rota usa substring de time (todas as demais usam `filter_by(name=)` exato ou
  `sleeper_owner_id`). **Não há replicação do bug de time.**

**Régua canônica aplicável às portas como está, ou exige adaptação? — EXIGE ADAPTAÇÃO:**
O resolver E4-a desambigua por **NFL team** (`entry['nfl_team']`). Mas os forms do `/auction`
(auction.html) enviam apenas `player_name` (texto livre) + `team_name` = time **fantasy** (select);
o bulk é `nome, time_fantasy, valor, espn`. **Nenhuma porta tem o NFL team nem sleeper_id no input.**
Consequência ao aplicar o resolver name-only:
- Nome **único** no pool Sleeper → `len(cands)==1` resolve o sid com segurança (caminho já existe).
- Nome **ambíguo** (classe Brown) → resolver retorna None (sem NFL team p/ desambiguar) → a porta
  **deve degradar para miss visível / escolha explícita**, nunca criar órfão ou chutar.
  → **Decisão de escopo p/ o owner (ver abaixo):** adicionar campo NFL team ao form, ou aceitar
  resolução name-only (único→sid; ambíguo→needs_review/visível).

**Comportamento de falha — hoje × desejável:**
- FA/rookie/bulk: jogador miss = **órfão silencioso sem sid** (pior caso; semeia a duplicata que um
  sync futuro re-duplica). Desejável: resolver sid → atualizar canônico (guard E4-b); senão criar com
  `needs_review=True` (some no review M2) — nunca órfão invisível.
- Excel: jogador miss já é seguro (skip visível); **time substring = atribuição errada silenciosa** →
  desejável trocar por match exato + miss visível (mesma régua das outras 3 portas).

**Parecer de escopo p/ F2 (sem implementação):**
1. **Time (Excel):** trocar `Team.name.ilike('%...%')` por match exato (`filter_by(name=)`), miss →
   skip+erro visível. Mudança de 1 linha + tratamento de miss; risco baixo, alto retorno. Candidato a
   fatia mínima isolável.
2. **Jogador (4 portas):** unificar a resolução numa única régua sid-first espelhando `draft_import`:
   tentar local → resolver nome(+nfl_team se disponível)→sid → `find_player_by_sleeper_id` → atualizar
   canônico; passar `sleeper_player_id` resolvido ao helper; órfão só como `needs_review`. Reusa
   `_resolve_entry_sid`/`_build_pool_index`/`find_player_by_sleeper_id`/guard E4-b — **sem duplicar** a
   régua. Custo do pool (~15MB) é lazy como no E4-b.

**Decisões de escopo EM ABERTO p/ o owner (antes da F2):**
- **(A) NFL team no form?** Adicionar campo `nfl_team` às telas/bulk do `/auction` (resolução Brown-safe
  completa) **ou** aceitar name-only (mais simples, ambíguos caem em needs_review)?
- **(B) Fatiar?** F2 = só o time do Excel (mínima, 1 linha) + um item separado p/ a unificação sid-first
  das 4 portas, **ou** tudo num F2 só?
- **(C) Prioridade vs. calendário:** a FA auction 2026 é o 1º uso real do `/auction` (ver [[F9]]) — o
  fix de identidade idealmente entra antes do registro em massa real. Owner decide se promove a
  prioridade.

**Decisões do owner pós-F1 (registradas):** resolução name-only com degradação p/ revisão (sem campo
NFL team novo); jogador + time corrigidos juntos; **prioridade elevada a Alta**.

#### F1b — Infra de aliases (time + jogador) (read-only, 16/06/2026)

Pergunta: que infraestrutura de alias já existe antes de a F2 escolher mecanismo. **Veredito central:
não existe NENHUMA infra de alias no sistema** (grep `alias|nickname|abbrev|apelido|Hollywood` em todo
`*.py` → só um comentário em import_csv.py:111 e a docstring do E4-b; zero mapa de dados). O "Brown-safe"
do E4-a resolve o risco de **casar demais** (homônimos reais desambiguados por NFL team), **não** o de
alias/apelido (casar de menos). São problemas distintos.

**TIME — representações existentes (models.py:79-118 + sync_sleeper.py:107-176):**
- `Team.name` (= `metadata.team_name` do Sleeper, ex "Cangaceiros da Colina"), `Team.display_name`
  (**hoje idêntico a `name`** — o sync seta os dois com o mesmo `team_name`; não é alias distinto),
  `Team.owner_name` (= `display_name` do Sleeper = **handle do manager**, ex "MellowBR"),
  `Team.sleeper_owner_id` / `sleeper_roster_id` (IDs estáveis).
- **Não há** campo de abreviação/cidade/apelido, nem mapa de alias. O exemplo "Houston Texans / Houston
  / Texans / HOU" **não tem fonte no sistema**. (`team_abbr` existe no pool de *jogadores* do Sleeper —
  é NFL team, irrelevante p/ time fantasy.)
- **Fonte confiável p/ derivar:** os IDs estáveis (`sleeper_owner_id`/`roster_id`) são a verdade, mas
  **não chegam no input free-text** do `/auction`. Aliases textuais reais já disponíveis p/ reusar:
  `name` + `owner_name` (2 handles distintos). Além disso, um mapa cidade/apelido/abreviação seria
  **dado NOVO curado pelo owner** (não derivável do Sleeper).
- **Nota de escopo:** FA/rookie individuais usam `<select>` (valor canônico exato — sem problema de
  alias). O alias só afeta as portas **free-text**: bulk (textarea) e Excel.

**JOGADOR — o resolver lida com apelidos? NÃO (evidência direta no pool):**
- Inspeção do cache real (`.sleeper_players_cache.json`, 11.578 players) no registro de Marquise Brown
  (sid 5848): campos de nome = só `full_name`='Marquise Brown', `first/last_name`, e `search_full_name`
  ='marquisebrown' (+ search_first/last). **"Hollywood" não aparece em campo nenhum.** O objeto Sleeper
  **não tem campo de apelido/nome alternativo.**
- Logo `_resolve_entry_sid`/`_norm_name` (que casam `_norm_name(input)` contra `full_name` do pool)
  **cobrem:** acento, sufixo (Jr/Sr/II–V), pontuação ('`.-), caixa, espaço. **NÃO cobrem:** apelido /
  nome alternativo (Hollywood↔Marquise) — porque a **fonte (Sleeper) não contém o apelido**.
- **Como o E4-b tratou o Brown:** NÃO resolveu o apelido. `cleanup_orphan_players` (admin.py:356)
  simplesmente **DELETOU** o órfão "Hollywood Brown" (id 279, sem sid/team/SalaryHistory/AuctionLog =
  sem valor). Foi limpeza pós-fato de órfão sem valor, **não** resolução de alias. Nenhum mecanismo
  hoje mapeia apelido→sid.

**Risco de casar demais (mitigação no parecer):**
- TIME: abreviação curta (ex "HOU", ou 1 palavra) colidindo entre times que compartilham palavra =
  **exatamente o bug de substring atual, só relocado**. Mitigar: casar `name`/`owner_name` por
  exato→normalizado primeiro; alias curto só se **único**; ambíguo → escolha explícita.
- JOGADOR: o resolver já retorna None em ambiguidade (≥2 cands sem NFL team único). Adicionar apelido
  por fuzzy **reduziria** a segurança (o E2 já viu falso-positivo Carnell Tate~Darnell Mooney @0.665) →
  apelido só por mapa curado, nunca fuzzy/substring.

**Parecer de mecanismo p/ F2 (sem implementação):**
- **TIME:** resolver input contra handles reais existentes — `name` + `owner_name`, exato→normalizado
  (reusa `_norm_name`), **sem substring**. Aliases que não batem com nenhum dos dois (ex "Houston" p/
  "Houston Texans") → **só** via mapa pequeno curado pelo owner `{team_id: [aliases]}` (dado novo) **ou**
  exigir o `name` canônico no bulk/Excel. Ambíguo/desconhecido → miss visível / escolha, nunca time
  errado silencioso.
- **JOGADOR:** manter o resolver Brown-safe (nome+nfl_team→sid; fallback nome-único) como espinha.
  Apelido **não está no Sleeper** → não há auto-resolução possível; o único caminho robusto é um mapa
  pequeno curado `apelido→sid` (ou apelido→nome canônico) p/ os poucos casos conhecidos (Hollywood→
  Marquise), aplicado como **pré-normalização ANTES** da resolução no pool. Ambíguo → needs_review.

**Decisões de mecanismo EM ABERTO p/ o owner (antes da F2):**
- **(D) Aliases de TIME:** só `name`+`owner_name` (mais simples; "Houston" p/ "Houston Texans" ainda
  cai em miss/escolha) **ou** introduzir mapa curado de alias de time?
- **(E) Apelidos de JOGADOR:** mapa curado pequeno apelido→sid (cobre Hollywood↔Marquise) **ou** aceitar
  que apelido vá p/ needs_review (sem auto-merge)?
- **(F) Fonte de verdade dos mapas (se adotados):** onde vivem (dict estático no código vs. tabela no
  DB) e quem mantém. Implica schema só se for tabela — fora do "sem mudar schema" se for dict.

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

### M1-FOLLOWUP — Auto-desativação do offseason mode pós-FA auction
🔲 **Pendente** — Prioridade **Baixa** — *stub estrutural criado pelo [[O5]] (13/08/2026): o item
sempre viveu só como row do Status Rápido; a seção existe para fechar o invariante "todo 🔲/⚠️ tem
seção detalhada" do auditor.*

**Problema:** com o FA auction concluído, o `offseason_mode` segue ligado até o admin desligar
manualmente — e o banner de cap estourado do [[M1]] (gated por offseason) persiste como ruído.
Avaliar auto-desativação ao concluir o passo 7 (ou lembrete na tela do admin).

---

### F8 — Reconstruir PlayerHistory a partir da Sleeper API
⚠️ **F8a concluído 22/04/2026; item segue ⚠️** — *stub estrutural criado pelo [[O5]] (13/08/2026)*.
O detalhe (F8a/F8-NOTES/F8-GAP, rollback via `F8PlayerBackup`) vive no `improvements_archive.md`
(seção F8) — anomalia histórica à regra "⚠️ nunca migra" do [[O3]]; mantido lá para não duplicar.

---

### OFF26-14 — Duas contagens de cap convivem (telas de roster excluíam salário de IR)
⚠️ **Ver estado na row do Status Rápido** — *stub estrutural criado pelo [[O5]] (13/08/2026)*.
O detalhe vive no `improvements_archive.md` (seção OFF26-14, movida em 04/08/2026 com o arco do
IR no cap — anomalia histórica à regra "⚠️ nunca migra" do [[O3]]; mantida lá para não duplicar).
A régua única do [[OFF26-16]] absorveu o grosso do item (`cap_regua_test.TestSemReplicaDeFolha`
guarda a não-regressão).

---

### IR-CLEANUP — Remover seletor manual de IR no roster
⚠️ **Executado 04/08/2026 — resta o fechamento formal** — *stub estrutural criado pelo [[O5]]
(13/08/2026)*. O detalhe vive no `improvements_archive.md` (seção IR-CLEANUP, movida com o arco
do IR de 04/08 — anomalia histórica à regra "⚠️ nunca migra" do [[O3]]; mantida lá para não
duplicar). O Sleeper é autoridade sobre `is_on_ir`; não há toggle na UI (ver CLAUDE.md).

---

### O6 — Split do backlog por campanha (arquivo próprio para OFF26-*)
🔲 **Registrado 13/08/2026 — F1 read-only CONCLUÍDA na mesma sessão (parecer abaixo); decisões do
owner ABSORVIDAS 13/08 (bloco de decisões no fim da seção) — gate: re-medição da família OFF26
pós-26/08** — MAN-O6-REG/MAN-O6-F1/MAN-O6-REFINE — Prioridade **Média** — **escopo Manager-only**

**Rota candidata (do prompt do owner — NÃO decidida; esta F1 existe para avaliá-la):** novo
`improvements_off26.md` recebe as seções OFF26-* verbatim, pertencimento pelo prefixo do ID sem
julgamento caso a caso; Status Rápido permanece ÚNICO e completo no ativo (namespace + dedupe),
com ponteiro para o arquivo de campanha; `tools/backlog_audit.py` passa a validar a união dos
dois arquivos; regra de migração ao archive inalterada (✅ migra do arquivo onde vive; ⚠️ nunca
migra); sunset natural: campanha encerrada → arquivo esvazia e é aposentado; OFF27 nasceria em
arquivo próprio (promoção transversal fora deste escopo).

#### F1 (MAN-O6-F1, 13/08/2026) — parecer read-only sobre o estado pós-`fa13270`

**1. Medição autoritativa** (working tree; comandos reproduzíveis via script da sessão):
- Ativo: **485.076 bytes (473,7 KB) / 5.967 linhas**.
- Família OFF26-*: **13 seções `###`, 236,3 KB = 49,9% do ativo** — 8🔲 / 5⚠️ / **zero ✅**
  (não há dívida de migração; o peso é todo de item aberto). Por seção: OFF26-4 67,4 ·
  OFF26-20 **61,6** (11,1 do item + **50,5 da narrativa F1B..CLOSE reancorada pelo [[O5]]**) ·
  OFF26-24 40,9 · OFF26-11 17,3 · OFF26-23 17,0 · OFF26-13 11,5 · OFF26-22 8,3 · OFF26-7 3,0 ·
  OFF26-19 2,4 · OFF26-12 2,3 · OFF26-8 2,3 · OFF26-21 1,7 · OFF26-14 (stub) 0,5.
- Fora de seção: bloco de contexto **`## Offseason 2026`** (registro + emenda de premissa) =
  **9,1 KB** que o split por prefixo de `###` **não captura**.
- Status Rápido: 24 rows OFF26 (11 ✅ já com detalhe no archive · 5 ⚠️ · 8 🔲).
- Projeção do split (seções + bloco de contexto): sairiam **245,5 KB**; restariam **228,2 KB**
  no ativo evergreen. Maiores seções remanescentes: M21 30,2 · O2 14,5 · DP1 12,3 · E4-d 11,3 ·
  F9 10,6 KB.

**2. Refutação de premissas (regra candidata [[MAN-METH-REG]] — baseline externa é hipótese):**
| Premissa (prompt/baseline) | Parecer | Medido |
|---|---|---|
| Ativo "~474 KB" | **Confirmada** | 473,7 KB |
| "Sem dívida O3 a quitar" | **Confirmada** | auditor exit 0 em `fa13270`; zero seções ✅ |
| "~12 seções OFF26, ~186 KB pré-O5" | **Confirmada** | fixture pré-O5: 12 seções, 185,3 KB |
| "mais ~45 KB de narrativa reancorada" | **Imprecisa** | 50,4–50,5 KB medidos |
| "Família ≈ metade do ativo" | **Confirmada** | 49,9% |
| "Prefixo particiona sem julgamento caso a caso" | **Falsa como partição limpa** | 3 classes de resíduo (item 3) |
| (implícita) "o Code lê o arquivo inteiro e a campanha polui essa leitura" | **Imprecisa** | a leitura do Code já é seletiva (Status Rápido como índice + Grep por seção — foi assim no O5); o custo real é de leitura HUMANA e de Project Knowledge |
| (implícita) "sem split a campanha continua pesando" | **Falsa no médio prazo** | ~**229,3 dos 236,3 KB (97%)** estão em seções com fechamento amarrado às datas 18–24/08 → sunset natural via regra O3 |

**3. Partição limpa? NÃO — casos-limite (listados, ZERO arbitrados):**
- **(a)** Bloco de contexto `## Offseason 2026` (9,1 KB): é da campanha mas não é seção `###`
  com ID — o critério "prefixo do ID" não o alcança; destino exigiria regra própria.
- **(b)** **5 seções não-OFF26 fisicamente DENTRO do bloco da campanha** (F9 10,6 · M21 30,2 ·
  O2 14,5 · L2 0,6 · C1 0,7 = 56,6 KB, linhas 3262–3972): mover as OFF26 verbatim as deixaria
  órfãs sob um header de campanha esvaziado — o split "sem julgamento" ainda exige reorganização
  física do que fica.
- **(c)** OFF26 de conteúdo evergreen (não expiram com a campanha): [[OFF26-12]] (interpretação
  de regulamento), [[OFF26-19]] (bug de renovação com IR), [[OFF26-21]] (limpeza de motor
  legado) — iriam para um arquivo com sunset previsto sendo itens sem data.
- **(d)** Não-OFF26 de conteúdo de campanha/anual: [[DP1]]/[[F14]] (board do rookie draft),
  [[E5]]/[[E4]] (import ESPN = passo 3 do offseason), fatia B do [[M21]] ("pós-intertemporada");
  e o stub [[OFF26-14]]/[[IR-CLEANUP]] divide o mesmo arco IR entre prefixos distintos.
- **(e)** O stub OFF26-14 (0,5 KB, aponta ao archive): prefixo manda para a campanha, conteúdo
  é ponteiro estrutural do [[O5]].

**4. Referências cruzadas e consumidores:**
- **303 links `[[...]]`** no ativo; **45** apontam a itens OFF26 a partir de FORA dos blocos da
  família e **21** saem de dentro dela para itens de fora → **66 refs virariam cross-file**. Os
  links são convenção de texto (nada quebra mecanicamente), mas Grep/navegação local degradam.
- **Consumidor mecânico: só o auditor** (`tools/backlog_audit.py`, default `improvements.md` —
  nenhum outro script lê o arquivo). Docstrings de `nfl_context.py` e `salary_engine_test.py`
  citam seções como ponteiro de spec (ambas de itens não-OFF26).
- **Ponteiro vivo já stale HOJE:** `runbook_cowork_liga_fantasma.md:377` remete à "seção do
  [[OFF26-10]] em improvements.md" — que migrou ao archive quando o item fechou ✅. A classe
  "ponteiro documental stale" já existe sob o O3 puro; o split a amplia, não a cria.
- **Project Knowledge:** hoje o ciclo de re-upload é `improvements.md` + archive + CLAUDE.md;
  o split adiciona um 4º arquivo recorrente (e handoffs/prompts padrão citam `improvements.md`
  como endereço das seções).

**5. Impacto no auditor (dimensionado, não implementado):** aceitar conjunto de arquivos
(descoberta automática de `improvements_off26.md` se existir); parse de seções sobre a união;
V3/V4 resolvem contra a união; **invariante novo necessário: V7 — mesmo ID com seção em mais de
um arquivo**; opcional (decisão de produto): V8 — pertencimento por prefixo (seção OFF26-* fora
do arquivo de campanha e vice-versa). Rows continuam só no ativo. Ordem de ~30–50 linhas, zero
dependências novas — é o 2º retrofit do contrato do auditor em uma semana de vida.

**6. Timing:** executar AGORA colide com a semana mais crítica do ano (rollover 18/08 · cortes
20/08 · urna + população do board 22/08 · leilão 24/08): as sessões dessas datas são justamente
as que leem as seções OFF26, e o split muda o endereço do insumo delas + o Project Knowledge no
meio da janela — benefício imediato nulo (fora da campanha não há sessão prevista antes de
24/08). **Após 24–26/08** o sunset natural terá levado a maior parte da família ao archive pela
regra O3 vigente, e o split (se ainda fizer sentido) moveria uma fração dos bytes, fora de
qualquer janela crítica.

**7. Alternativas à rota proposta:**
- **A. Não fazer nada + sunset natural (custo zero):** ~229,3 KB dos 236,3 têm fechamento
  previsto na própria campanha; resíduo projetado sem data = **~7 KB** de seções (OFF26-12/19/21
  + stub) + 9,1 KB do bloco de contexto. Mesmo fechamento PARCIAL (só OFF26-4 + OFF26-24 +
  OFF26-20) já remove 169,9 KB (72% da família). Ressalva honesta: previsto ≠ garantido — ⚠️
  pendente de smoke pode se arrastar; por isso a re-medição pós-26/08, não a fé.
- **B. Instrução de leitura seletiva no CLAUDE.md** (1 parágrafo: "Status Rápido é o índice;
  fora da campanha, não ler seções OFF26"): ataca o incômodo de leitura do Code sem mover um
  byte — mas só resolve se o incômodo for do Code, não da leitura humana (questão Q5).
- **C. O split proposto:** mecânica provada (O3/O5, moves verbatim com verificação por máquina),
  porém com os resíduos do item 3, 66 refs cross-file, 4º arquivo no Project Knowledge e
  retrofit do auditor — partes móveis pagas para aliviar um peso que o calendário já está
  prestes a aliviar de graça.
- **D. Padrão só para o FUTURO:** OFF27 nasce em arquivo de campanha próprio (auditor ganha o
  suporte a união quando o arquivo nascer), e OFF26 termina a vida onde está — dá o benefício
  permanente sem retrofit na semana crítica.

**Recomendação (o parecer recomenda; NÃO decide): não executar o split agora.** Re-medir a
família pós-26/08 (fechamento + sync final da campanha) com o mesmo script; se o resíduo OFF26
ainda incomodar, executar aí — com uma fração dos bytes e fora da janela. Se o objetivo
dominante for o padrão de campanhas futuras, a alternativa D entrega isso sem mover OFF26.

**8. Questões em aberto para o owner (o parecer não arbitra):**
1. **Sequência:** aguardar o sunset e re-medir pós-26/08 antes de decidir (recomendado), ou
   valorar a leitura limpa JÁ na semana da campanha a ponto de pagar o risco de timing?
2. **Se split: destino dos casos-limite** — bloco de contexto `## Offseason 2026`, as 5 seções
   não-OFF26 encravadas, os OFF26 evergreen (12/19/21) e o stub OFF26-14: prefixo cego ou
   arbitragem caso a caso (contradizendo a premissa da rota)?
3. **Project Knowledge:** um 4º arquivo recorrente no ciclo de re-upload é aceitável?
4. **OFF27:** nasce em arquivo próprio independentemente do retrofit de OFF26 (alternativa D)?
5. **Natureza do incômodo:** leitura humana do arquivo ou leitura do Code? (Se for só o Code, a
   alternativa B — instrução de leitura seletiva — basta e custa um parágrafo.)

#### Decisões do owner (13/08/2026 — MAN-O6-REFINE; respondem as 5 questões do parecer)

- **(a) Split NÃO será executado agora.** A **re-medição da família OFF26 pós-26/08** decide se
  ele ainda se justifica — **mesmo instrumento da F1, persistido em `tools/off26_measure.py`**
  (comparabilidade exige o mesmo script, não uma reimplementação) — expectativa: sunset de
  ~229 KB via os fechamentos de 18–24/08. **Este é o gate do item; O6 segue 🔲 até lá.**
- **(b) Alternativa B aceita e implementada na mesma sessão:** orientação de leitura seletiva do
  backlog no `CLAUDE.md` (Status Rápido como índice; seções OFF26-* não se carregam fora da
  campanha; verificação estrutural é do `backlog_audit.py`, custo zero de contexto).
- **(c) Alternativa D aceita como decisão:** OFF27 nasce em **arquivo de campanha próprio**;
  execução na **primeira sessão pós-campanha 2026**, junto com o retrofit do auditor para
  múltiplos arquivos (invariante V7) — fora de janela crítica.
- **(d) Motivação registrada:** o incômodo é **consumo silencioso de tokens pelo Code**, não
  navegação humana (resposta à Q5 — é o que seleciona a B como resposta imediata e esvazia a
  urgência do split).

**Observação da varredura de ponteiros (mesma sessão):** a classe "referência a seção de backlog
por arquivo" teve **1 única ocorrência viva** nos runbooks (`runbook_cowork_liga_fantasma.md:377`,
corrigida — referência por ID + nota de que ✅ vive no archive); classe **não recorrente** → a
regra candidata "runbooks referenciam por ID, não por arquivo" não foi registrada (critério do
prompt: só se recorrente).

---

## Offseason 2026 — pacote OFF26 (cuts selados + liga fantasma)
🔲 **Registrado 05/06/2026** — MAN-OFF26-REG (registro apenas; nenhuma implementação)

> **Emenda de premissa (02/08/2026 — MAN-OFF26-10-11-REG):** o parágrafo de contexto abaixo é
> o registro **da época** e carrega uma premissa **factualmente errada** — a de que o rookie
> draft também roda em liga fantasma. O texto original fica **preservado verbatim** (precedente
> de correção de premissa do [[DP1]], que manteve a frase e anexou a correção); a correção está
> no bloco **EMENDA** logo após o parágrafo. Único ajuste no texto histórico: o título da seção,
> que passou de "ligas fantasmas" para "liga fantasma" (ver consequência na emenda).

**Contexto do pacote (sessão com o comissário, 05/06/2026):** o formato da liga
(keeper + dynasty + salary cap) não cabe nativamente no Sleeper e a API do Sleeper
é **read-only** — não há como escrever salários/configuração via API. Decisão: o
Sleeper mantém o que faz bem (salas de lance ao vivo, via **ligas fantasmas** —
rookie draft em draft linear e FA Auction em draft auction), e o **Manager** assume
todo o ciclo de decisão e registro (declaração selada de keepers/cuts, keeper sheet,
auditoria da config da liga fantasma, import dos resultados dos drafts). A
transcrição da keeper sheet para o Sleeper é feita via **Cowork + Claude in Chrome**
(procedimento operacional supervisionado, fora do código do Manager).

**EMENDA — o rookie draft NÃO roda em liga fantasma (02/08/2026, MAN-OFF26-10-11-REG).**
A frase acima ("**ligas fantasmas** — rookie draft em draft linear e FA Auction em draft
auction") é falsa na metade do **rookie draft**, e essa metade **nunca foi justificada item a
item** — entrou por arrasto, colada no motivo real da FA auction. Evidência:
- o importador [[OFF26-3]] foi validado contra o **rookie draft real de 2025**, lido da **chain
  de ligas da liga real** — não de sala separada;
- todo o arco [[S2]]/[[S3]], fechado em 02/08/2026, trata do **board de R1 2026 da liga real**:
  a permutação administrativa de picks, o espelhamento do board e a tela prescritiva pendente
  ([[S5]]) **só fazem sentido ali**.

O motivo pelo qual a **FA auction** exige sala separada é **outro** e **permanece válido**: a
liga real é **dynasty com rosters cheios**, e o auction pressupõe **rosters vazios sendo
preenchidos por lance**, com o cap individual **emergindo** do budget global do auction
consumido pelos keepers designados no board (achado do [[OFF26-6]]).

→ **Consequência a propagar: existe UMA liga fantasma permanente — a da FA auction —, não
duas.** O rookie draft roda na **liga real**. Ajustados por esta emenda: o título desta seção
e a descrição do [[OFF26-7]]. **Ocorrências deixadas intactas de propósito** (registro
histórico / restrição do prompt de registro): a linha do [[OFF26-3]] no Status Rápido e sua
seção no `improvements_archive.md`, ambas rotulando o item como "importador de drafts de liga
fantasma" — o rótulo é artefato de nomeação do item fechado, não premissa viva.

**Dependências do pacote:** OFF26-1 → OFF26-2 → OFF26-4; OFF26-3 independente e
paralelizável; OFF26-5 é documentação (depende conceitualmente de 2 e 4).
**Gaps de intertemporada (REG 02/08/2026):** **OFF26-10** (late drop pós-lock) depende de
**OFF26-1** (é o snapshot que ele altera) e **afeta OFF26-2 e OFF26-4** (sheet e auditoria
derivam do snapshot); **OFF26-11** (keeper × arremate no importador) depende de **OFF26-3**
(✅, é a porta que ingere) e do **mesmo probe empírico que o OFF26-4 aguarda** (o que a API do
Sleeper expõe sobre designações de keeper). **Ambos entram como etapas do OFF26-7.**
**Liga fantasma CRIADA (02/08/2026) — identificadores registrados, board zerado
(MAN-OFF26-IDS-REG):** **Dynasty SB FA Auction** — permanente, Redraft, 12 times, draft
**Auction**, budget **$200**, **22 rodadas**, roster espelhando a real (**3 WR**).

| campo | valor | estabilidade |
|---|---|---|
| **`league_id`** | `1389725099556372481` | **estável** |
| **`draft_id`** (atual) | `1389755381567213568` | ⚠️ **MUDA A CADA RESET** |
| ~~`draft_id` (anterior)~~ | ~~`1389725100684611584`~~ | ☠️ **MORTO** — a URL trava em LOADING |

> ⚠️ **O `draft_id` NÃO é estável (achado MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026).** O **RESET DRAFT
> gerou um draft novo, com id novo** — o valor registrado poucas horas antes pelo
> `MAN-OFF26-IDS-REG` **morreu no mesmo dia**. E a morte é **silenciosa**: a URL antiga **trava
> indefinidamente em LOADING**, não dá erro. **Persistir `draft_id` é armadilha.** O que se guarda
> é o **`league_id`**; o `draft_id` se **deriva** dele a cada uso. Presumivelmente muda também na
> virada de season. Detalhe e incidência sobre a decisão 1 na seção do [[OFF26-4]].

**Os dois são distintos e NÃO deriváveis um do outro por inspeção** — o draft board vive sob id
próprio, a página da liga sob outro (confirmado empiricamente ao ler as duas URLs). Coerente com o
precedente do `draft_import.py`, que recebe o **`draft_id`** e **deriva** o `league_id` do objeto
do draft. **Registrados aqui como DADO, deliberadamente não persistidos** em constante, `AppConfig`
ou coluna: a parametrização do league/draft id é **decisão de produto ainda em aberto** no
[[OFF26-4]] (§1 da sua F1) e não deve ser antecipada por um registro.

**Estado do board (02/08/2026, após a 2ª execução do Cowork):** **populado com dados de teste** —
**Team 3 ($148, 10 keepers)**, **Team 4 ($95, 8)**, **Team 5 ($60, 6)**, totais conferindo. Team 1
e Team 2 foram limpos pelo reset. **Novo RESET DRAFT pendente antes do uso real** — e ele **gerará
novo `draft_id` outra vez**.

**Estado dos owners (03/08/2026):** **convites disparados**, mas os times **ainda são
placeholders** — **`owner_id` nulo**. Consequência registrada na spec do [[OFF26-4]] (**D6**):
enquanto for assim, **a ponte de owner não tem como casar coluna e time**, e a **F2 do OFF26-4 não
pode ser validada contra board de placeholders**.

Achados do experimento manual na sala (feito **antes** do 1º reset): refutação do §5 da F1 do
**OFF26-4**, teto de lance do **OFF26-10** e o indício `is_keeper:false` do **OFF26-11**. Método
de população em 2026: **Cowork** (decisão vigente) — ver [[OFF26-5]].

> ✅ **Janela aberta para os probes pendentes.** O board **está populado agora**, então serve de
> **alvo** ao probe pré-draft do [[OFF26-4]] e à verificação de designações — **desde que
> executados ANTES do próximo reset**. A confirmação **pós-draft** do `is_keeper:false`
> ([[OFF26-11]]) continua exigindo **rodar um draft de teste**.
**Validação operacional (REG 16/06/2026):** OFF26-6 (PoC do Cowork montando a liga) roda
**cedo e isolado** (mecânica pura com dados fake) e é **gate** de OFF26-5/FA auction real;
OFF26-6 é **subconjunto** de OFF26-7 (dry run E2E), que ensaia a cadeia inteira e depende
de OFF26-1/2/4 existirem. OFF26-8 (Cowork aplica os cortes do OFF26-1 no roster real) é
**irmão** de OFF26-6 e também **subconjunto** de OFF26-7 (etapa "aplicar cortes no Sleeper").
**Prioridades abaixo são triagem inicial — o comissário re-prioriza.**
**Próximos candidatos naturais de F1 (sessões separadas):** OFF26-1 e OFF26-3.

#### 📸 Prontidão da intertemporada 2026 — fotografia de 07/08 (MAN-OFF26-10-SMOKE)

**O código da intertemporada está COMPLETO. O que resta é operação.** Os itens do caminho
crítico estão ✅ e smokados em produção; nenhum deles espera desenvolvimento.

| Data | O quê | Onde | Estado |
|---|---|---|---|
| **17/08** | **Rookie draft** (roda na liga REAL) | Sleeper + importador [[OFF26-3]] | ✅ pronto |
| véspera | **Consulta 5/32** aos owners | fora do Manager | operação |
| **18/08** | **ESPN definitiva** + **Season Rollover** | `/offseason` passos 3 e 4 | ✅ pronto — **e é gate da urna** (o agendamento é recusado com `rollover_done` pendente) |
| **20/08** | **Cortes no Sleeper** → **sync** → **keeper sheet PROVISÓRIA** | Sleeper + `/cuts/keeper_sheet` | ✅ [[OFF26-2]] |
| **20→22/08** | **Urna aberta** (um bilhete por time) | `/late_drop` | ✅ [[OFF26-10]] |
| **22/08** | **Revelação** → **execução MANUAL no Sleeper** → **sync final** → **sheet DEFINITIVA** | `/late_drop` + Sleeper + sheet | ✅ — a janela de execução manual está no runbook |
| **22–24/08** | **Cowork transcreve** + **auditoria como GATE** do leilão | [[OFF26-5]] + `/admin/keeper_audit` | ✅ [[OFF26-4]] |
| **24/08** | **FA auction** | liga fantasma | ✅ importador [[OFF26-3]] / [[OFF26-11]] 🔲 na ingestão |

**As duas travas de sequência que agora são código, não instrução:** rollover ⇄ urna (bloqueio
mútuo, MAN-OFF26-10-AJUSTES) e **board 100% populado antes de 24/08** (a auditoria do [[OFF26-4]]
é gate — abrir o leilão com time não populado **expõe os keepers dele**).

**O que continua sendo risco de OPERAÇÃO, não de software:** owner que não executa o drop revelado
(a auditoria acusa — é a rede), sync esquecido antes de transcrever (a sheet mostra o carimbo e o
selo PROVISÓRIA), e a ingestão do leilão misturando keeper com arremate ([[OFF26-11]] 🔲, decidido
mas não implementado).

---

### OFF26-4 — Auditoria de keepers pré-leilão
⚠️ **Parcial** — Prioridade **Média**

**Descrição:** após a transcrição via Cowork, compara a keeper sheet (OFF26-2) com a
configuração **real** da liga fantasma lida via API read-only, reportando diffs
(keeper ausente, salário divergente, time errado) **antes** do início do leilão.

**Motivação:** a transcrição manual é o ponto de falha; a auditoria pega divergências
antes que o leilão comece sobre uma configuração errada.

**Escopo resumido:** ler config da liga fantasma via API read-only; diff contra a
keeper sheet; relatório de divergências como gate pré-leilão.

**Dependências:** depende de **OFF26-1** e **OFF26-2**.


#### Spec final — decisões de produto arbitradas (MAN-OFF26-4-REFINE, 03/08/2026)

Decisões do owner pós-F1, **sincronizadas com a evidência empírica de 02/08** (liga fantasma real).
**Esta spec é a verdade do item.** A F2 lê esta camada; a **F1** e a **ATUALIZAÇÃO EMPÍRICA**
continuam válidas **abaixo, como terreno** — não foram alteradas.

**Natureza do item — gate que roda MAIS DE UMA VEZ.** A auditoria é gate **pré-leilão**: roda
depois da transcrição do board pelo Cowork e antes de abrir o FA auction em **24/08**. Na prática
**roda 3× ou mais** numa janela apertada: após a **1ª leva de população (20/08)**, após o **remendo
do late drop (22/08)** e possivelmente **uma vez final** antes da abertura. Essa repetição sob
prazo é o que decide o **D1**.

> ⛔ **REQUALIFICAÇÃO DA NATUREZA (MAN-OFF26-4-REFINE-PT2, 03/08/2026): isto não é conferência de
> cap — é GATE DE INTEGRIDADE DO LEILÃO.** Ver o bloco **"ACHADO — keeper fora do board é jogador
> leiloável"**, logo abaixo desta spec. Um keeper ausente do board **não é divergência de
> transcrição**: é **um jogador com contrato vigente prestes a ser arrematado por outro time, ao
> vivo, sem forma limpa de desfazer**. Isso reclassifica a severidade da classe correspondente do
> **D5** e transforma a **população completa do board em pré-condição de abertura**, não em
> preparativo.

- **D1 — Parametrização: `AppConfig` para o `league_id`; `draft_id` DERIVADO.** *(arbitrada)*
  O identificador da liga fantasma mora em **`AppConfig`**, configurável pelo admin. **Descartadas:**
  **coluna em `Team`** (é atributo **de liga**, não de time) e **parâmetro por chamada** (molde
  [[OFF26-3]]) — esta última **por motivo operacional**: a auditoria roda **várias vezes numa janela
  de 48 h**, e recolar o id a cada execução é **oportunidade recorrente de colar o errado sob
  pressão de prazo**.
  - ⛔ **Restrição NÃO-NEGOCIÁVEL (evidência de 02/08): persiste-se APENAS o `league_id`.** O
    **`draft_id` muda a cada RESET DRAFT** — o valor registrado em 02/08 **morreu no mesmo dia** —
    e deve ser **derivado do `league_id` a cada uso**. **Nenhuma forma de persistência do
    `draft_id`** (constante, `AppConfig`, coluna, cache).
  - ⚠️ **Requisito de robustez decorrente do modo de falha:** a URL de um draft morto **trava em
    LOADING em vez de dar erro** — a falha é **indistinguível de lentidão**. A derivação precisa de
    **timeout explícito e mensagem própria**; **não pode ficar pendurada**. (Numa janela de 48 h,
    uma auditoria que pendura é pior que uma que falha.)
  - 🔲 **Pendência de terreno que a F2 HERDA:** o caminho **`league_id → draft_id`** existe no
    código (`/league/{lid}/drafts`, `sync_sleeper.py:762`) mas **NUNCA foi exercitado contra a
    fantasma** — e o precedente do `draft_import.py` é a derivação **inversa**. **Confirmar antes
    de construir sobre ele.**

  > **🔧 CORREÇÃO DE PREMISSA (MAN-OFF26-4-REFINE-PT2, 03/08/2026) — os dois sub-bullets acima
  > ficam preservados como registro do que se acreditava, e são corrigidos aqui:**
  >
  > **(1) A "falha silenciosa" NÃO existe pela porta da auditoria.** O probe mediu: um draft morto
  > responde **404 com corpo nulo em ~0,2 s**. **O travamento em LOADING é comportamento do app
  > WEB**, não da API. → O **timeout explícito é rebaixado de MITIGAÇÃO DE RISCO a BOA PRÁTICA** —
  > o modo de falha que o justificava **não existe nesta porta** (e o `_get` do projeto já traz
  > `timeout=15`).
  > **(2) A pendência de terreno está FECHADA:** a derivação **funciona**, e por caminho **mais
  > barato que o previsto** — **o `draft_id` vem no próprio objeto da liga** (`GET /league/{lid}`),
  > em **uma** requisição, sem precisar de `/drafts`.
  >
  > **O ESSENCIAL DO D1 PERMANECE INTACTO: `draft_id` NÃO é persistido.** A correção enfraquece o
  > *requisito acessório*, não a *restrição*.

- **D2 — Base de comparação de budget: `usable_draft_budget`.** *(**resolvida por evidência**, não
  arbitrada)* O **§5 da F1** afirmava que a reserva de **$1 por vaga** era regra interna do Manager,
  inexistente no Sleeper, e concluía pelo **`raw_budget`**. **Refutado por experimento:** o Sleeper
  aplica **a mesma reserva**, fórmula `teto = 200 − gasto − (vagas_restantes − 1)`, **confirmada nos
  dois sentidos**. A base correta é **`usable_draft_budget`** — o número que a **keeper sheet já
  entrega**. (Detalhe do experimento na ATUALIZAÇÃO EMPÍRICA, abaixo.)
  - ⚠️ **Ressalva que a F2 CARREGA — aritmética, não experimento:** o Sleeper reserva sobre as **22
    rodadas configuradas na sala**; a regra **8.3.4** conta slots pelo **regulamento**. **Se as
    contagens divergirem, os limites não coincidem apesar da fórmula idêntica.** **Conferência
    ainda NÃO FEITA** — não depende de novo acesso à plataforma, depende de conferir o regulamento
    contra a config da sala.
  - **📐 Estado da ressalva após o probe (03/08) — METADE FECHADA:**
    - ✅ **Lado da SALA: medido, são 22 slots** — `roster_positions` = `QB, RB, RB, WR, WR, WR, TE,
      FLEX, K, DEF` **+ 12 `BN`**. Não é mais suposição.
    - 🔲 **Lado do REGULAMENTO (8.3.4): SEGUE PENDENTE.**
    - ⚠️ **E agora com um caso CONCRETO, não hipotético:** a **liga real tem slot de IR** (máx. 2)
      e **a fantasma não tem nenhum** — ver o bloco **"Divergência de config real × fantasma (IR)"**
      abaixo. A divergência de contagem entre os dois lados **deixou de ser hipótese**.
    - **Aritmética adicional a conferir (mesma natureza, não é experimento):** a fantasma comporta
      **22 keepers por time**. **Confirmar que nenhum time da liga real pode exceder 22 keepers
      após os cortes.** Improvável dado o cap, **mas não verificado**.

  > **✅ PENDÊNCIA FECHADA (MAN-OFF26-4-LABELS, 03/08/2026) — decisão do D2 INTACTA, só o terreno
  > mudou de status.** A conferência foi feita contra o regulamento: **8.3.4 conta 22**, a sala
  > conta **22**, o Manager conta **22** — **as três coincidem**, e a fórmula da reserva é a mesma.
  > **A ressalva não se concretizou.** Restam duas coisas, ambas registradas em detalhe na seção da
  > F2 (bloco "D2 — CONFERÊNCIA ARITMÉTICA FEITA"): uma **diferença residual de até $2** para times
  > com IR (o regulamento tira o IR dos 22, Manager e Sleeper o mantêm dentro — mas **os dois lados
  > que a auditoria compara concordam entre si**, então **não há falso positivo**), e a
  > **ambiguidade da 8.3.4 devolvida ao owner**. **A aritmética adicional foi respondida: SIM, um
  > time pode exceder** — 24 legais (22+2 IR) contra 22 designações, e **há um time em 24 hoje**.

- **D3 — `sleeper_player_id` na ponte de jogador: DELEGADA à F2, com critério.** *(delegada com
  critério)* A keeper sheet **não expõe** `sleeper_player_id` (§3 da F1). A escolha entre
  **incluí-lo no payload** ou **re-consultar no Manager** fica com a F2, sob critério do owner:
  **preferir o caminho que NÃO TOQUE o [[OFF26-2]]**, que segue **⚠️ aguardando smoke de produção**.
  **Empate em robustez → vence quem não mexe em item pendente de validação.**
  - **Invariante que nenhuma das duas alternativas pode violar:** resolução de identidade **só por
    `sleeper_id`**, **nunca por nome** — precedente do incidente **"Brown"**.

- **D4 — Escopo do relatório: os 12 times de uma vez.** *(arbitrada)* A auditoria é gate da **sala
  inteira**, **não** consulta por time; o relatório cobre **os 12 numa execução**.
  - **Times ainda NÃO POPULADOS** (bloqueados pelo teto de budget, [[OFF26-10]]) aparecem como
    **ESTADO PRÓPRIO**, **distinto de "keeper ausente"**. **Não populado por regra não é divergência
    de transcrição** — confundir os dois produziria alarme falso justamente no cenário que o
    calendário torna **esperado** (times acima do cap aguardando o late drop de 22/08).

- **D5 — Classes de divergência a reportar.** *(arbitrada)*
  1. keeper **presente na sheet e ausente do board**;
  2. **salário divergente**;
  3. keeper **alocado ao time errado**;
  4. jogador **no board que não consta da sheet**;
  5. *(estado separado, não divergência)* **time não populado**.
  - A **severidade** de cada classe fica com a **F2**.

  > **🔧 AJUSTE DO D5 (MAN-OFF26-4-REFINE-PT2, 03/08/2026) — duas mudanças:**
  >
  > **(1) A classe "slot errado" NÃO EXISTE — e não precisa existir.** O probe mediu que
  > **`pick_no` e `round` não indicam vaga de roster** (as designações ocupam picks sequenciais na
  > **ordem de criação**). **Alocação de vaga não é auditável** — e **não faz falta**: a atribuição
  > é **automática por posição**, então não há erro de vaga a cometer. As 4 classes acima **já não
  > incluíam** essa classe; o registro é para que a F2 **não tente inventá-la**.
  >
  > **(2) A classe 1 deixa de ser divergência comum — é a mais grave da lista.** Pelo achado
  > "keeper fora do board é jogador leiloável" (bloco abaixo), **keeper ausente do board = jogador
  > com contrato vigente exposto ao leilão**. **A severidade da classe 1 não é decisão livre da
  > F2:** ela é **bloqueante de abertura**. A F2 decide a severidade **relativa das outras**, não a
  > desta.

- **D6 — Ponte de owner: `sleeper_owner_id`, com helper compartilhado.** *(arbitrada)* Casamento
  **só** por **`Team.sleeper_owner_id`** — **`Team.name` é mutado pelo sync** e **não serve de
  chave** (§4 da F1). **Reaproveitar** o helper de ponte de owner já existente
  (`_team_by_roster`, `draft_import.py:43`) em vez de recriar; **se a extração para local
  compartilhado for necessária, ela é da F2**.
  - ⛔ **Terreno NÃO VERIFICADO — restrição de validação:** a ponte **nunca foi exercitada com
    owners reais na fantasma**. Os **convites foram disparados em 03/08** e os times **ainda são
    placeholders**, cujo **`owner_id` é nulo**. Enquanto for assim, **a auditoria não tem como casar
    coluna e time**. → **A F2 NÃO PODE SER VALIDADA CONTRA BOARD DE PLACEHOLDERS.**

  > **🔧 AJUSTE DO D6 (MAN-OFF26-4-REFINE-PT2, 03/08/2026) — a restrição acima era ampla demais.**
  > O probe confirmou o fato (**`owner_id` nulo em 11 de 12**), mas **deslocou a consequência**: as
  > designações **já vêm chaveadas por `roster_id`**, então **casar designação e coluna NÃO exige
  > owner**. O `owner_id` é necessário **apenas** para a costura `roster_id` ↔ **time do Manager**.
  >
  > **Substituir "não validável contra placeholders" por esta distinção:**
  > - ✅ **CONSTRUÇÃO e validação parcial: LIBERADAS contra placeholders** — leitura de designações,
  >   soma de budget, comparação de salário e presença, todas as classes do D5 **por `roster_id`**.
  > - 🔲 **O que espera os aceites dos convites: só a COSTURA FINAL** `roster_id` ↔ time do Manager
  >   (via `Team.sleeper_owner_id`).
  >
  > **A F2 não está bloqueada — está com uma costura pendente.**

  > **✅ COSTURA CONFERIDA COM OWNERS REAIS (MAN-OFF26-4-OWNERCHECK, 03/08/2026) — leitura
  > read-only, zero escrita dos dois lados.** A "última incógnita do D6" foi **exercitada contra
  > owners de verdade** pela primeira vez.
  >
  > **Resultado: 8 de 8 casaram. Nenhum não-casamento.**
  >
  > | roster | `owner_id` | display (fantasma) | Team do Manager |
  > |---|---|---|---|
  > | 1 | `1130162144764506112` | MellowBR | #5 Cangaceiros da Colina |
  > | 2 | `695859519976210432` | rafadgil | #1 Pitbull do Samba |
  > | 3 | `695859970096328704` | TropadoJarra | #9 Tropa do Bicampeonato 🏆 |
  > | 4 | `205848303030505472` | icarocosta1 | #4 mongoloides |
  > | 5 | `1133812910268010496` | rafaelferreirap | #11 rafaelferreirap |
  > | 6 | `1129822349391470592` | fernandoxmf | #3 Fazenda Pederasta |
  > | 7 | `1131747074137272320` | murilofborges | #6 Miller Time! |
  > | 8 | `1133818177651224576` | LeoFBorges1 | #12 ESPN FANTASY LEAGUE |
  > | 9–12 | *(nulo)* | — | — |
  >
  > **⚠️ Divergência com o estado esperado — 8 owners, não 7.** O prompt esperava **7 aceites**
  > (`MellowBR`, `rafadgil`, `TropadoJarra`, `icarocosta1`, `rafaelferreirap`, `fernandoxmf`,
  > `murilofborges`). A API expôs **8**: `LeoFBorges1` (roster 8) entrou **depois** da leitura de
  > tela do owner. **Divergência benigna e na direção boa** (mais aceites, não menos), mas o
  > registro fica: **a contagem de aceites muda entre uma olhada e a seguinte** — a auditoria da F2
  > tem de **ler, não assumir**.
  >
  > **Robustez do casamento — não depende do banco local.** O conjunto dos 12 `sleeper_owner_id`
  > do Manager é **idêntico** ao conjunto dos 12 `user_id` da liga real lidos ao vivo da API
  > (`manager − real = ∅`, `real − manager = ∅`), e os 8 owners da fantasma são **subconjunto**
  > desse conjunto. Ou seja: o casamento se verifica **contra a API**, não contra o estado do
  > `dynasty.db` de dev — **eventual defasagem do seed não afeta o resultado**. Confirma a
  > propriedade que sustenta o D6: **`owner_id` é identidade de CONTA do Sleeper, não de time nem
  > de liga** — a mesma conta atravessa as duas ligas com o mesmo id.
  >
  > **🔲 D6 SEGUE ABERTO — o mecanismo está confirmado, a cobertura não.** Fecham-se a dúvida sobre
  > *se a chave casa* (casa, 8/8) e a *"última incógnita"* como risco de desenho. Continuam
  > pendentes: **4 rosters com `owner_id` nulo** (9–12), que **nenhuma leitura resolve** — dependem
  > de aceite. E há um caso que a F2 vai encontrar e que **não é achado de auditoria**: **coluna sem
  > owner não é atribuível a time nenhum** — distinto de "time não populado" (D4). Onde isso cai nas
  > classes do D5 é decisão da F2; aqui só fica registrado que **o caso existe e foi observado**.
  > Lembrando que, pelo achado "keeper fora do board é jogador leiloável", **os 4 placeholders já
  > são bloqueantes de abertura por outro motivo** — a costura não é o gargalo.

  > **📌 REFORÇO DA JUSTIFICATIVA (MAN-OFF26-4-OWNERCHECK, 03/08/2026) — não altera a regra.** A
  > regra "casar **só** por `sleeper_owner_id`, nunca por nome" **permanece exatamente como está**.
  > O que muda é a força do *porquê*: são **dois motivos independentes**, não um.
  >
  > **Motivo 1 (já registrado) — instabilidade no tempo:** `Team.name` é **mutado pelo sync**.
  > **Evidência nova de campo:** o Manager guarda `#9 Tropa do Bicampeonato 🏆` enquanto a liga real
  > **hoje** exibe `Tropa do Jarra 🏆`. O nome **já divergiu**, sozinho, sem ninguém tocar no
  > Manager.
  >
  > **Motivo 2 (novo, mais fundamental) — espaços de nome SEPARADOS:** nada vincula o nome que um
  > owner usa na fantasma ao que ele usa na liga real. O nome pode **nascer diferente e permanecer
  > diferente para sempre**, sem mutação nenhuma. Não é uma dessincronização a corrigir — **são dois
  > namespaces**, e casá-los seria erro de categoria, não de atualização.
  >
  > **Evidência de campo (medida, não suposta):**
  > - **`metadata.team_name` é `None` nos 8 owners da fantasma — 8 de 8.** Enquanto ninguém batiza o
  >   time, as colunas exibem **username** (`rafadgil`, `fernandoxmf`), **não nome de time**.
  >   Durante boa parte da preparação **não existe nome de time para casar**: um casamento por nome
  >   não erraria — **não teria com o que trabalhar**.
  > - **Dois Rafas entre os owners reais:** `rafadgil` e `rafaelferreirap`. Colisão por nome é risco
  >   **concreto**, não hipotético.
  > - **`rafaelferreirap` não tem `team_name` nem na liga real** → o Manager guarda o **username**
  >   como `Team.name` (#11). Ou seja: em pelo menos um caso, "nome do time" no Manager **já é um
  >   username**, e cruzá-lo com o username da fantasma daria um acerto **por coincidência de
  >   fallback**, não por identidade — o pior tipo de acerto, porque valida a técnica errada.
  >
  > **Para quem ler isto no futuro:** ver nomes coincidentes nas duas telas **não** autoriza
  > simplificar a regra. A coincidência é acidente do momento; a identidade é o `owner_id`.

- **D7 — Pré-condição de probe (NÃO é passo interno da F2).** *(pré-condição registrada)* Segue
  pendente a questão empírica do **§2 da F1**: **o que a API expõe pré-draft** sobre **designações de
  keeper e salário** — **nada no código lê estado pré-draft hoje**. O probe **exige board populado**.
  - ✅ **Janela ABERTA agora:** o board **está populado** com **Team 3 ($148)**, **Team 4 ($95)** e
    **Team 5 ($60)** — dados de teste, mas **alvo válido**.
  - ⏳ **A janela FECHA no próximo RESET DRAFT**, já **pendente antes do uso real** — e o reset
    **zera o board e troca o `draft_id`** (D1). **Rodar o probe antes.**

**O que esta spec NÃO decide:** severidade das classes do D5 (F2); forma de exposição do
`sleeper_player_id` (D3, F2); extração do helper de owner (D6, F2); e a conferência aritmética da
ressalva do D2. **Status do item permanece 🔲** — a spec não é implementação.

> **Ressalva ao parágrafo acima (PT2, 03/08):** "severidade das classes do D5" passa a valer **só
> para as classes 2-4**. A **severidade da classe 1** (keeper ausente do board) **foi determinada
> pelo achado abaixo** e é **bloqueante de abertura** — não é escolha da F2.

#### F2 — IMPLEMENTAÇÃO (MAN-OFF26-4, 03/08/2026) — ⚠️ código pronto, **aguardando smoke em prod**

**Status do item: 🔲 → ⚠️.** Validado em localhost (**29/29** testes novos + **48/48** do
`salary_engine` intactos) e **exercitado contra o board REAL**, mas **não fecha ✅ sem smoke em
produção** ([[PROC1]]) — e, mais que isso, **sem sheet real, que só existe a partir de 20/08**.

**O que foi construído**

| arquivo | papel |
|---|---|
| `keeper_audit.py` | **núcleo puro** `audit(board, sheet)` (sem DB, sem rede — molde `salary_engine`) + camada de leitura `fetch_board` / `build_sheet` / `run_audit` |
| `keeper_audit_fixtures.py` | **material de teste** congelado (⛔ **não é a sheet real** e nenhum caminho de produção o importa) |
| `keeper_audit_test.py` | 29 testes do núcleo, sem Flask e sem banco |
| `templates/keeper_audit.html` | relatório dos 12 de uma vez; veredito no topo |
| `routes/admin.py` | `/admin/keeper_audit` (página), `/api/admin/keeper_audit` (JSON), `POST /api/admin/phantom_league` (**só** o `league_id`) |
| `app.py` | seed do `phantom_league_id` no `AppConfig` (D1) |

**Decisões que a spec delegou, agora tomadas:**
- **D3 (ponte de jogador):** **re-query**, não payload. `build_sheet` consome
  `_build_keeper_sheet` (fonte única do [[OFF26-2]]) e enriquece com `sleeper_player_id`
  consultando `Player` — **o [[OFF26-2]] não foi tocado**, como o critério do owner mandava.
- **D5 (severidade relativa):** classe 1 **bloqueante** (não era escolha); `time_errado` e
  `salario_divergente` **alta**; `fora_da_sheet` **média**. **A classe "slot errado" não foi
  criada** — e há teste que falha se alguém a criar.
- **Ordenação:** pior primeiro. O gate se lê de cima sob prazo.

**Veredito, não lista.** A tela abre com **ABERTURA LIBERADA / BLOQUEADA** e os motivos. Bloqueiam:
keeper exposto (classe 1), **time não populado**, **time sem coluna**, **coluna órfã** e **keeper
sem identidade resolvível**. **Zero divergências não libera** — 9 times sem board é o cenário em que
todos os keepers deles estão expostos.

##### Divergências entre spec e terreno (relatadas, não resolvidas por conta própria)

1. **D6 mandou reusar `_team_by_roster` — e não há o que reusar.** Aquele helper **consulta o
   banco** por roster; o núcleo puro casa `owner_id` ↔ time **em memória**, com dado que os dois
   lados já carregam. **Não houve réplica nem extração** (a spec previa que a extração *poderia*
   ser da F2): `_team_by_roster` segue sendo a porta do importador, intocada. **A invariante do D6
   — casar só por `sleeper_owner_id` — foi cumprida; o meio previsto é que não se aplicava.**
2. **A spec previa UM estado ("time não populado"); o terreno tem DOIS.** Um time cujo owner **não
   está em coluna nenhuma** (convite não aceito) é caso distinto de coluna vazia: **não é
   auditável nem populável**. Criado o estado **`sem_coluna`** — é a cobertura do D6 aparecendo
   como estado de relatório, não como bug.
3. **"Coluna sem owner" (observada e não classificada) recebeu tratamento próprio, e é o inverso
   do (2).** Vai para um **balde separado** (`orphan_columns`), **nunca** para a conta de
   divergências de um time: **coluna não atribuível não é divergência de ninguém** — e o que
   estiver designado nela **não pode ser conferido contra sheet nenhuma**. Bloqueia a abertura.
   Mesmo balde recebe coluna **com** owner que não corresponda a time do Manager.
4. **A spec não previu keeper sem `sleeper_player_id`.** O Manager admite jogador sem id do
   Sleeper; a identidade **não é resolvível** e **cair para nome está proibido** ("Brown"). Não é
   divergência — é **limite de insumo**: vira aviso, entra na contagem `unresolved_keepers` e
   **bloqueia a abertura por auditoria incompleta**. Silenciar seria pior que acusar.
5. **D2 — `usable_draft_budget` é EXIBIDO, não diferenciado.** A base está correta e vem da sheet,
   mas **budget divergente NÃO virou classe**: qualquer diferença de soma é **consequência** das
   classes 1–4, e transformá-la em achado próprio produziria exatamente a **quarta divergência**
   que a fixture B existe para proibir. O relatório mostra `fa_budget`, Σ sheet e Σ board por time;
   a conferência aritmética do regulamento **segue pendente** (não é código).
6. **A ressalva das 22 rodadas virou verificação automática.** Se a sheet de um time trouxer mais
   keepers que `rounds` do draft, sai **aviso** ("não cabem na sala"). Fecha por medição, a cada
   execução, a aritmética que o D2 deixou pendente do lado da sala — **não** do lado do
   regulamento.
7. **D1 — o timeout já existia.** `ss._get` traz `timeout=15`; nada novo foi preciso. Medido de
   novo hoje: **id morto → erro em 0,21 s**, com mensagem própria citando o RESET DRAFT.

##### Fixtures — o que provam, e o que deliberadamente não provam

- **A (coerente):** board real (24 designações, **$148/$95/$60**, com os **dois DEF de id-sigla**)
  × sheet que o espelha → **zero divergências**, 3 populados, **9 não populados**. **Uma coerência
  extra teve de ser imposta na geração:** os 24 do board estavam **espalhados pelos elencos reais**
  dos outros times (o board veio de lista de teste), e sem removê-los de lá a fixture "coerente"
  acusava **18 falsos `time_errado`**. **O erro era da fixture, não da auditoria** — e a auditoria
  estava certa: aquele jogador **estava** em dois times.
- **B (divergente):** A + **três erros plantados** (salário, keeper removido da sheet, jogador no
  time errado) → **exatamente três achados, um por classe**. O caso do time errado é o que mais
  importa: um diff ingênuo o contaria **duas vezes** ("ausente lá" + "sobrando cá") e produziria
  a quarta divergência.
- **O que a B NÃO cobre:** os três erros pedidos são das classes **2, 3 e 4** — **a classe 1
  (bloqueante) não está entre eles**. Foi criada a fixture dirigida **C** para ela; sem isso a
  classe mais grave ficaria sem teste.
- Mais duas dirigidas: **coluna sem owner** (terreno real de hoje) e **keeper sem `sleeper_id`**
  (com dois Brown, exatamente o caso que um fallback por nome estragaria).
- **Enquadramento ao cap na geração:** artifício de fixture, **não regra de negócio** — e **não
  precisou disparar**: nenhum time excedia $200. Os cortes reais são declarados no [[OFF26-1]].

##### Validação executada (localhost + leitura real)

- **29/29** testes novos; **48/48** do `salary_engine` **intactos** (linha de base preservada).
- **Contra o board REAL, ao vivo:** `fetch_board` derivou o `draft_id` do `league_id`, leu **24
  designações** com `status=pre_draft`, `rounds=22` **lido do draft**, e as **3 colunas sem owner**.
  Cruzado com a fixture A: **0 divergências, 3 `sem_coluna`, 3 colunas órfãs** — o terreno real
  atravessando o núcleo inteiro.
- **Sem sheet real (janela não revelada em localhost): a auditoria diz isso** e devolve **0 times**
  — não acusa 12 times de keeper ausente por falta de insumo. É o caminho que a tela mostra hoje.
- **`draft_id` não é persistido em lugar nenhum** (grep): só existe em variável local, URL e tela.
- **Board intacto, draft não iniciado, nenhuma escrita na plataforma** — só `GET`.
- `git diff` **não toca** `salary_engine`, schema de cortes, `sync_sleeper` nem a keeper sheet.

##### ⚠️ O que fica pendente

- **Smoke em produção ([[PROC1]])** — o item **não fecha ✅** com localhost.
- **A auditoria só terá sheet real a partir de 20/08** (revelação da janela de cortes). Até lá
  **nunca rodou com os dois lados reais** — o lado Manager foi sempre fixture.
- **Cobertura do D6 segue aberta:** hoje **3 dos 12** times não têm coluna (convite não aceito).
  **Foram 4 de manhã e 3 à tarde** — `fertorquato` entrou entre as duas leituras da mesma sessão.
  **Terceira leitura, terceira contagem: a auditoria lê, nunca assume.**
- **Ressalva aritmética do D2 pelo lado do regulamento (8.3.4)** — segue pendente; o lado da sala
  agora é verificado a cada execução.
- **A tela é `@login_required`, não `@admin_required`** — leitura, e a sheet que ela cruza já é
  visível a todos **pós-revelação**. **Não há vazamento de sigilo**: sem snapshot canônico
  revelado, a auditoria não roda.

##### SMOKE PARCIAL em produção (03/08/2026, deploy `d83d2f8`) — 3 de 4 pontos, e o 4º virou correção

**⚠️ Antes de tudo, um achado de processo:** os **10 commits do dia ficaram locais**. O deploy vivo
era o de **02/08** — o smoke só foi possível depois do push. **O auto-deploy dispara no push, e não
havia push.** Sem tentar o smoke, isso teria sido descoberto **em 20/08**.

**Passaram:** a rota responde e renderiza; o card do `/admin` leva à página; o `phantom_league_id`
foi **semeado no `AppConfig` de produção** pelo boot e aparece preenchido.

**⛔ O 4º ponto NÃO ERA ALCANÇÁVEL — e era o único que só produção prova.** A auditoria bloqueia por
ausência de sheet **antes** de qualquer coisa ser exibida, então o bloco de meta (`draft_id`
derivado, `pre_draft`, rodadas) **não renderizava**. A ordem era coerente; a consequência, não:
ficava sem prova que **o Render alcança a API do Sleeper** e que a **derivação funciona de lá**.

> **São modos de falha de AMBIENTE — egress bloqueado, DNS, timeout de plano — e nenhum deles
> aparece em localhost.** Seriam descobertos **em 20/08**: no dia em que a auditoria precisa
> funcionar. **Um buraco de validação, não um bug.**

##### F2-META (MAN-OFF26-4-META, 03/08/2026) — a leitura da liga não depende mais da sheet

**Mudança de borda e apresentação. Núcleo, veredito e classes intocados** (fixtures A/B/C com o
mesmo resultado; **34/34** — 29 antigos + 5 novos — e **48/48** do `salary_engine`).

- **A meta da liga é lida e exibida SEMPRE**, inclusive sob bloqueio por falta de sheet. O
  `run_audit` já lia os dois lados de forma independente — **o que faltava era a meta carregar o
  suficiente e o template renderizá-la fora do `if report.ok`**.
- **Campos:** `draft_id` **com selo "derivado"** ao lado (não guardado), status, **rodadas lidas do
  draft**, **designações no board** e **colunas com dono × sem dono**.
- **Erro de leitura é ESTADO PRÓPRIO do bloco**, distinto do bloqueio por falta de insumo: o
  veredito segue dizendo o que falta de insumo e o bloco diz o que houve com a liga. `league_id`
  inválido → **erro limpo em 0,29 s, HTTP 200**, sem pendurar e sem 500. `run_audit` ganhou guarda
  contra exceção inesperada da rede/parse — **falha de liga nunca derruba a rota**.
- **Motivo de produto, independente do smoke:** antes de a sheet existir, o operador precisa
  conferir que está **apontando para a liga certa**. `league_id` errado no `AppConfig` era **falha
  silenciosa até 20/08**.

**Estado de referência p/ conferir o smoke completo:** liga `1389725099556372481`, draft
`pre_draft`, **22 rodadas**, **24 designações**.

##### ✅ SMOKE DE PRODUÇÃO COMPLETO (03/08/2026, deploy `aec8d8f`) — 4 de 4

O ponto que faltava **fechou**: o serviço no Render **alcança a API do Sleeper** e a **derivação do
`draft_id` funciona de produção** (22 rodadas, 24 designações, 10/12 colunas com dono, `pre_draft`).
**Os modos de falha de ambiente estão descartados** — não é mais coisa a descobrir em 20/08. **O
item segue ⚠️**: falta o smoke com **sheet real**.

##### F2-LABELS (MAN-OFF26-4-LABELS, 03/08/2026) — dois cards com o mesmo nome

O smoke expôs **títulos duplicados**: "Liga fantasma" nomeava tanto a **leitura ao vivo** quanto a
**configuração persistida**. Em 20/08, sob prazo, isso convida a procurar informação no card errado
ou a **salvar onde não se pretendia**. Renomeados para **"Estado da liga fantasma"** (leitura) e
**"ID da liga fantasma"** (configuração). **Só rótulo** — ordem, layout, lógica, rota e payload
intactos; verificado em **5 estados da página** (sem sheet, fixtures A/B/C, erro de liga): nenhum
título repetido em nenhum deles, ordem veredito → estado → configuração preservada.

##### ✅ D2 — CONFERÊNCIA ARITMÉTICA FEITA: as contagens COINCIDEM (a pendência fecha)

Lido do **regulamento** (`data/Regulamento - Dynasty - SB FANTASY FOOTBALL LEAGUE - 12-08-2025.pdf`,
item **8.3.4**, verbatim):

> *"Cada owner deverá draftar o número de jogadores necessários para completar as **22 posições do
> roster**. Para isso deverá ter PELO MENOS $1 disponível no CAP para cada jogador a ser draftado
> **(22 – número de keepers)**"*

| lado | contagem | origem |
|---|---|---|
| **Regulamento 8.3.4** | **22** | texto acima, explícito |
| **Sala fantasma** | **22** | `roster_positions` = 22 **e** `draft.settings.rounds` = 22 |
| **Manager** | **22** | `salary_engine.MAX_ROSTER`; `empty_spots = 22 − num_keepers` |

**Resposta: SIM, coincidem — 22 = 22 = 22, e a fórmula da reserva é a mesma nos três.** O medo do
D2 ("se as contagens divergirem, os limites não coincidem apesar da fórmula idêntica") **não se
concretiza**. **Metade pendente do D2: FECHADA.**

**⚠️ Mas há uma diferença residual, e ela não é de contagem — é de QUEM ENTRA NA CONTA.** O item
**1.3** do regulamento diz: *"2 IR (injuried reserves) – **não são considerados no total de 22**"*.

- **Regulamento:** jogador em IR **fica fora** dos 22 → um time com 20 não-IR + 2 IR ainda **deve
  reservar $2** (faltam 2 para completar as 22).
- **Manager:** conta o IR **dentro** dos 22 (`cuts._team_fa_budget` passa todos os não-dropados;
  `draft_budget` filtra só `is_dropped`) → vê roster **cheio** e reserva **$0**.
- **Sleeper:** o keeper em IR **é designado** e ocupa uma das 22 rodadas → conta **igual ao
  Manager**.

**Efeito prático sobre a auditoria: NENHUM falso positivo.** Os dois lados que a auditoria compara
— Manager e Sleeper — **concordam entre si**. A divergência é **de ambos com o regulamento**, e vale
**até $2** de `usable_draft_budget` a mais para time com IR. Hoje **3 times** têm IR preenchido na
liga real. **Nenhum cálculo foi alterado** — a conferência era de registro.

**🔲 AMBIGUIDADE DEVOLVIDA AO OWNER (é regra de liga, não decisão de implementação):** a **8.3.4 diz
"(22 − número de keepers)" sem dizer se keeper em IR entra nessa contagem.** Com o 1.3, a leitura
natural é que **não entra** — e é justamente essa leitura que produz a diferença de até $2 com o que
Manager e Sleeper fazem hoje. **Duas leituras possíveis:**
- **(a) IR conta como keeper** → o que Manager e Sleeper já fazem; nada muda, e o 1.3 vale só para
  limite de elenco, não para a reserva.
- **(b) IR não conta como keeper** → o Manager está **até $2 permissivo** e a fórmula precisaria
  descontar IR do `num_keepers`. **Isso mexeria no `salary_engine`** — fora do escopo desta sessão e
  **decisão do owner**.

##### ⚠️ ARITMÉTICA ADICIONAL DO D2 — a resposta é SIM, um time PODE exceder o board

O D2 pedia confirmar que "nenhum time da liga real pode exceder 22 keepers". **Pode:** o regulamento
permite **24** (22 + 2 IR, item 1.3) e o board comporta **22 designações** (22 rodadas).

**E não é hipótese: 1 time está em 24 hoje** (roster 10 — 22 não-IR + 2 IR), medido ao vivo na liga
real. Se chegar assim em 20/08, **2 keepers não cabem no board** — e pelo achado "keeper fora do
board é jogador leiloável", **ficam expostos ao leilão**. Os cortes de 20/08 podem resolver, mas
**nada no regulamento obriga** um time a descer de 24 para 22.

> **Encadeia com [[OFF26-10]] e [[OFF26-5]]:** é uma **segunda causa** de time não populável, ao lado
> do teto de budget — e esta **não se resolve com o late drop de 22/08** (1 drop não tira 2
> excedentes). **Registrado como risco, não como solução:** a decisão é do owner.

##### ⛔ PREMISSA REFUTADA — "a fantasma NÃO tem slot de IR" é FALSO (4ª da mesma família)

O probe de 03/08 registrou, como **divergência concreta de config**, que a liga real tem IR e **a
fantasma não** — lido de `roster_positions` (22 = 10 titulares + 12 BN, sem "IR").

**Medição de hoje, decisiva:** `settings.reserve_slots = **2** nas DUAS ligas`, e o campo `reserve`
existe nos rosters das duas. **O `roster_positions` da liga REAL também não lista "IR"** — e ela
tem, com **3 rosters usando** agora. **IR não mora em `roster_positions`; mora em
`settings.reserve_slots`.** A observação era verdadeira; a **procedência**, errada.

- **A "divergência de config real × fantasma" quanto a IR NÃO EXISTE.** As duas salas são
  idênticas nesse ponto.
- **A resolução operacional do owner PERMANECE CORRETA e necessária** — designar o keeper em IR
  normalmente no board —, mas **por outro motivo**: não é que a sala não tenha IR; é que **slot de
  IR não é slot de draft**. O draft tem **22 rodadas**, então **22 designações por time**,
  independentemente dos 2 IR do elenco.
- **Nada do que foi decidido muda. O que muda é o porquê** — e isso importa para quem for reabrir a
  decisão depois.

> **Quarta premissa da mesma família, no mesmo arco:** observação verdadeira, **procedência
> errada** — e de novo **o campo lido não era onde o dado mora**. O teste que a derrubou foi o
> mesmo das outras três: **ir à superfície certa** (aqui, comparar com a liga real, cujo IR ninguém
> duvida).

##### Limitação conhecida (fail-safe, registrada e NÃO corrigida nesta sessão)

Um **timeout parcial** — `/league` responde e `/draft/{id}/picks` não — ocorreu de fato durante os
testes. A leitura degrada para **"0 designações"**, indistinguível de board genuinamente vazio.
**Falha para o lado seguro:** board vazio deixa todos os times "não populados" e o veredito
**BLOQUEADO**; a auditoria **nunca libera** por falta de leitura. **Fica registrado como imprecisão
de rótulo, não risco de gate** — distinguir "0" de "desconhecido" é melhoria, não correção urgente.

**⚠️ E a contagem mudou pela QUARTA vez no mesmo dia:** **7 esperados → 8 → 9 → 10 colunas com
dono** (2 sem dono agora). Quatro leituras, quatro números. **É exatamente por isso que a contagem é
campo do relatório e não constante** — e é o que o bloco novo passa a mostrar ao vivo.

##### ⛔ ACHADO — keeper fora do board é JOGADOR LEILOÁVEL (MAN-OFF26-4-REFINE-PT2, 03/08/2026)

> **É o achado de maior peso de todo o arco OFF26 até aqui, e não existia em nenhum registro do
> pacote.** Emergiu da discussão da divergência de IR com o owner, na sequência do probe.

**O fato.** Um keeper que **não esteja designado no board** é, para o Sleeper, **jogador
disponível**. Qualquer owner pode **nomeá-lo**, e o leilão **processa o lance normalmente** — a
plataforma **não tem como saber** que ele já tem contrato vigente. O resultado é **um jogador com
dono sendo arrematado por outro time, AO VIVO**, e o importador [[OFF26-3]] ingerindo isso depois
**como aquisição legítima**.

**Por que isso muda a natureza do item:**

> **Não é erro de contabilidade que a auditoria corrige depois. É transação inválida em tempo real,
> sem forma limpa de desfazer sem interromper o leilão.**

Toda a modelagem anterior do OFF26-4 tratava divergências como **contabilidade a reconciliar** —
algo que se acha e se conserta. Esta classe **não se conserta**: quando ela se manifesta, o lance
já foi dado, o jogador já mudou de time na sala, e desfazer significa **parar o leilão com 12
owners ao vivo**. → **A auditoria deixa de ser conferência de cap e passa a ser GATE DE INTEGRIDADE
DO LEILÃO.**

**Consequências registradas (não são desenho de solução):**
1. **Severidade da classe 1 do D5** (keeper ausente do board) **não é decisão livre da F2** — é
   **bloqueante de abertura**.
2. **População completa do board é PRÉ-CONDIÇÃO DE ABERTURA do leilão**, não preparativo. **Abrir
   o leilão com qualquer time não populado expõe os keepers desse time.**
3. **Isto encadeia com o [[OFF26-10]]** e é onde o risco fica agudo — ver a propagação registrada
   lá: os times **bloqueados pelo teto** só entram no board **após o late drop (22/08)**, e **até
   lá seus keepers estão expostos**.
4. **Isto encadeia com o [[OFF26-5]]** — o runbook passa a registrar que **board incompleto não é
   estado aceitável** para iniciar o leilão.

**O que este bloco NÃO faz:** não decide *como* a auditoria bloqueia, nem *quem* aperta o botão,
nem se há override de admin. Isso é F2. Aqui está registrado **o risco e a sua força**.

##### Divergência de config real × fantasma — IR (RESOLVIDA pelo owner, 03/08/2026)

**O problema.** A **liga real tem slot de IR** (máx. 2); a **fantasma não tem nenhum**
(`roster_positions` = 22 = 10 titulares + 12 BN, medido no probe). Um keeper em IR na liga real
**não tem slot correspondente na sala** — e o **D5 do [[OFF26-2]]** manda **contar IR normalmente**
no budget de keeper.

**✅ Resolução (owner):** **designar o keeper em IR normalmente no board.** Os excedentes **caem no
banco** (12 vagas de `BN`), e a **atribuição de vaga é automática por posição** — não há o que
escolher. Três efeitos, todos desejáveis:
- o jogador **sai do pool disponível** → **fecha o risco do achado acima para este caso**;
- **consome budget corretamente**;
- **fica visível para a auditoria**.

**❌ Alternativa DESCARTADA:** descontar o valor do keeper em IR do **budget do time** na
configuração do auction. **Motivo do descarte — dois, e o primeiro é decisivo:**
1. **Não resolve o risco do achado acima.** **O problema não é o dinheiro, é a disponibilidade do
   jogador** — descontar budget deixa o keeper **no pool**, leiloável.
2. Tornaria o desconto **invisível para a auditoria** (o budget por time **não é legível pela API**
   — P5 do probe; a auditoria **deriva por soma das designações**, e um desconto fora do board não
   aparece em soma nenhuma).

**Fecha metade da ressalva do D2** (a contagem da sala é **22**); a metade do **regulamento 8.3.4**
segue pendente — ver o D2.

> **⛔ CORREÇÃO DE PREMISSA (MAN-OFF26-4-LABELS, 03/08/2026) — o texto acima fica preservado, mas
> "a fantasma não tem nenhum [slot de IR]" é FALSO.** Medido: `settings.reserve_slots = **2** nas
> duas ligas`. O `roster_positions` da **liga real** também não lista "IR" — e ela tem IR, com 3
> rosters usando. **IR não mora em `roster_positions`; mora em `settings.reserve_slots`.**
> → **A divergência de config real × fantasma quanto a IR NÃO EXISTE** — as salas são idênticas.
> **A resolução do owner (designar o keeper em IR normalmente) PERMANECE CORRETA e necessária**,
> por outro motivo: **slot de IR não é slot de draft**. O draft tem **22 rodadas** → **22
> designações por time**, tenha a sala IR ou não. **A decisão não muda; o porquê muda** — e é o
> porquê que alguém usaria para reabri-la. Detalhe na seção da F2.

##### Armadilhas de implementação para a F2 (medidas no probe)

- **⚠️ `player_id` de DEF é SIGLA, não número** — ex.: `"LAR"` para o L.A. Rams DEF. **Qualquer
  coerção a inteiro quebra em defesas.**
- **⚠️ Duas fontes de contagem de rodadas divergem:** a config **da liga** informa um número
  (`settings.draft_rounds = 3`) e a **do draft** informa outro (`settings.rounds = 22`). **Ler a do
  DRAFT.**

##### Nota de método — a TERCEIRA premissa da mesma família na mesma sessão

As três caíram pelo **mesmo mecanismo**: **observação verdadeira, procedência errada.**

| # | premissa | observação (verdadeira) | procedência (errada) |
|---|---|---|---|
| 1 | "a sigla NFL do Sleeper diverge da sheet" ([[OFF26-5]]) | a sigla **de fato** divergiu | os dados vinham de **lista de teste com temporadas velhas** |
| 2 | "a reserva de $1/vaga é regra só do Manager" (§5 da F1) | a regra **de fato** existe no Manager | concluiu-se sobre o **Sleeper** sem tocar o Sleeper |
| 3 | "a URL de draft morto trava em LOADING" (D1) | o travamento **de fato** ocorre | é comportamento do **app web**, generalizado para a **API** |

> **Padrão a vigiar: comportamento observado numa superfície NÃO vale como propriedade de outra.**
> Web ≠ API; lista de teste ≠ dado de produção; regra do Manager ≠ regra da plataforma. Nos três
> casos a evidência era real e a **inferência de escopo** é que falhou — e nos três a correção veio
> de **tocar a superfície certa**. Quarta família registrada do [[MAN-METH-REG]].

---


#### Diagnose F1 (MAN-OFF26-4-F1, 18/06/2026 — read-only, Opus) — terreno confirmado contra o código

**1. Como apontar para a liga fantasma (league ID).**
- Hoje o league ID é **constante hard-coded**: `models.py:15` `LEAGUE_ID = "1316547584378048512"` (+ `MY_OWNER_ID`, `MY_TEAM_NAME`, `CURRENT_SEASON`). `sync_sleeper.run_sync()` importa e usa `LEAGUE_ID` direto em **todas** as chamadas (`sync_sleeper.py:101,108,123,294,307`). **Assume uma só liga = a real.** Não é parametrizável e não há `AppConfig` de league.
- **Precedente já existente para ler outra liga:** `routes/draft_import.py` (OFF26-3) **não** usa `LEAGUE_ID` — recebe um **`draft_id`** do admin, lê `ss._get(.../draft/{draft_id})` e **deriva** `league_id = draft.get("league_id")` (`draft_import.py:36,101,106`). Ou seja, o caminho mais limpo já é codificado: **parâmetro de chamada (draft_id/league_id passado pelo admin), não constante global.** `ss._get(url)` (`sync_sleeper.py:35`) é o primitivo read-only que aceita URL arbitrária.
- **Opções de terreno (sem decidir — provável REFINE):** (a) parâmetro de chamada (admin cola o `league_id` ou `draft_id` da fantasma, molde OFF26-3); (b) `AppConfig` novo `phantom_league_id` (estado persistido, reusável ano a ano); (c) coluna em Team. Recomendação de terreno: (a)/(b) — a fantasma é **permanente** (OFF26-6), então (b) tem apelo de reuso anual.

**2. Leitura pré-draft da liga fantasma via API.**
- Já reusável: `ss._get` (URL arbitrária), `_team_by_roster(league_id)` (`draft_import.py:43` — lê `/league/{lid}/rosters`, casa por `sleeper_owner_id`), `/league/{lid}/drafts` + `/draft/{did}/picks` (`sync_sleeper.py:762,769`).
- **GAP crítico (designações de keeper pré-draft):** **todo** consumo de `/draft/{id}/picks` no código hoje exige `status == "complete"` (`draft_import.py:94-96`; `_classify_draft` em `sync_sleeper.py:733`). **Nada lê o estado PRÉ-draft.** As designações de keeper de board (SET KEEPERS, achado do OFF26-6) **não são lidas em lugar nenhum** — o código só conhece picks de draft completo. Se a API expõe keepers pré-draft (ex.: `is_keeper`/`metadata.amount` em `/draft/{id}/picks` antes de `complete`, ou no objeto `/draft/{id}`) é **questão empírica** — exige **probe na F2** contra a fantasma real; **não é assertável a partir do código** e não deve ser assumido. Este é o maior gap.
- **GAP de salário do keeper:** no código atual o salário/`amount` vem de `pk.metadata.amount` apenas em picks completos. Para o pré-draft, mesmo gap acima.

**3. Ponte de identidade de jogador — `/api/cuts/keeper_sheet` expõe id canônico? → NÃO.**
- `_build_keeper_sheet` (`routes/cuts.py:420-423`) emite por keeper apenas `{id (Player.id local), name, position, salary}`. **Grep confirma:** `sleeper_player_id` **não aparece** em `routes/cuts.py`. A sheet **não** expõe o id do Sleeper.
- **Caminho de resolução disponível:** `Player.sleeper_player_id` existe e é populado pelo sync (`sync_sleeper.py:238,263` — link por sleeper_id ou nome normalizado). A ponte canônica é `player_lookup.find_player_by_sleeper_id(sid)` (`player_lookup.py:53`, Brown-safe). A auditoria resolve via `Player.query.get(keeper["id"]).sleeper_player_id` ou re-derivando a sheet com o campo incluído. (Decisão de F2: incluir `sleeper_player_id` no payload da sheet vs. re-query.)

**4. Ponte de identidade de owner/time — `sleeper_owner_id` resolve? → SIM.**
- `Team.sleeper_owner_id` (`models.py:84`) é populado **a cada sync** (`sync_sleeper.py:157,167` — sempre setado de `roster.owner_id`, em update e create). O precedente de casamento já existe: `_team_by_roster` faz `Team.query.filter_by(sleeper_owner_id=oid)` (`draft_import.py:48`). Consumível diretamente para casar time do Manager ↔ time da fantasma.
- **Ressalva (nome mutável como chave):** o sync **ainda muta `Team.name`** de fontes do Sleeper (`sync_sleeper.py:148-156`, cascateando `Player.fantasy_team`). O nome **não** é usado como chave de identidade (a chave é `sleeper_owner_id`/`sleeper_roster_id`), mas a keeper sheet **exibe e ordena por `team_name`** (`cuts.py:405`) e a fantasma é uma sala separada — o `team_name` na fantasma **pode divergir** do real. A auditoria deve casar por `sleeper_owner_id`, **nunca** por nome.

**5. Origem do budget no diff — auditoria CALCULA os dois lados? → SIM, confirmado.**
- Lado Manager: a sheet **já entrega** `fa_budget` por time (`cuts.py:418`), fonte canônica `_team_fa_budget → salary_engine.draft_budget(roster)["usable_draft_budget"]` (`cuts.py:387-392`; `salary_engine.py:216-236`). `$200` = `SALARY_CAP` (`salary_engine.py:39`). Não há número pronto no Sleeper pré-draft (achado OFF26-6 confirmado: nada no código lê budget restante da API).
- **REFUTAÇÃO IMPORTANTE (descasamento de fórmula):** o `fa_budget` da sheet é `usable_draft_budget` = `$200 − Σ keeper_salaries − (slots_vazios × $1)` (`salary_engine.py:221-224,233`). O budget de auction que o Sleeper mostraria é `raw_budget` = `$200 − Σ keeper_salaries` (`salary_engine.py:223`), **sem** o desconto `$1/slot vazio` (regra interna do Manager, inexistente no Sleeper). **A auditoria NÃO pode comparar `fa_budget` da sheet contra o budget do Sleeper como like-for-like** — tem de comparar `raw_budget` × budget Sleeper, ou comparar **Σ salários de keeper** dos dois lados (mais robusto). Decisão de produto p/ F2/REFINE.

**6. RÉPLICA (consumo — diff/identidade/budget já replicados?).**
- **Aritmética de budget:** porta única `salary_engine.draft_budget` — consumida por `cuts._team_fa_budget` (`cuts.py:392`), `draft_import._budget_alerts` (`draft_import.py:77`), `salary.py:186`. **Nenhuma réplica client-side:** `keeper_sheet.html` só renderiza `t.fa_budget` server-side (`:39,52`); sem JS de budget. Invariante F10 respeitada — a auditoria **reusa** `draft_budget`, não recria.
- **Ponte de owner:** `_team_by_roster` (`draft_import.py:43`) é o padrão a reusar/extrair — risco de a auditoria **recriar** essa função em vez de fatorar. Recomendo extrair para helper compartilhado em F2.
- **Identidade de jogador:** porta única `player_lookup.find_player_by_sleeper_id`. Sem réplica.
- **Diff/comparação Manager × Sleeper:** **não existe em lugar nenhum** (grep `diff/divergen/audit` em templates só acha o lottery_audit, não-relacionado). Greenfield — nada a recriar por engano aqui.

**7. REFUTAÇÃO DE PREMISSAS (MAN-METH-REG).**
- *(a-falsa)* "o Manager conhece o league ID da liga real" — **verdade**, mas é **constante única hard-coded** (`models.py:15`), não config; ler outra liga é parâmetro novo, não toggle. → **premissa parcialmente falsa / gap de design**.
- *(a-falsa)* premissa implícita "ler a config = ler o roster" — **falsa**: o código só lê picks de draft **completo**; pré-draft (designações de keeper) **não é lido em lugar nenhum**. → **perda não-intencional / gap maior**.
- *(b-ausente)* a sheet **não expõe `sleeper_player_id`** apesar de o Player tê-lo — ausência no enquadramento da ponte de jogador. → **perda não-intencional** (corrigível em F2).
- *(b-ausente)* `fa_budget` (`usable_draft_budget`) ≠ budget de auction do Sleeper (`raw_budget`) — o enquadramento "budget = `$200 − Σ keepers`" bate com `raw_budget`, **não** com o que a sheet entrega. → **deslocamento** (a sheet entrega outro número; auditoria precisa escolher a base de comparação).
- *(b-ausente)* `Team.name` ainda é mutado pelo sync e exibido/ordenado na sheet — risco se a fantasma tiver nomes diferentes. → **premissa de robustez**: casar só por `sleeper_owner_id`.
- *(intencional)* "keeper" removido do vocabulário de aquisição (F6) mas vivo no `draft_budget` como "roster ativo pré-FA" — **remoção intencional**, sem impacto na auditoria.

**Resumo dos gaps p/ F2:** (1) como parametrizar o league/draft id da fantasma (REFINE provável); (2) **probe empírico** do que a API expõe pré-draft (designações + salário de keeper) — bloqueador; (3) incluir `sleeper_player_id` na sheet ou re-query; (4) escolher a base de comparação de budget (`raw_budget`/Σ salários, **não** `fa_budget`); (5) extrair helper de ponte de owner em vez de recriar.

**Modelo recomendado p/ próxima fase: Opus, modo REFINE** — a diagnose revela ≥2 decisões de produto pendentes (parametrização do league id + base de comparação do budget) e 1 bloqueador empírico (o que a API expõe pré-draft) que precisa de probe antes de F2 de implementação.

#### ATUALIZAÇÃO EMPÍRICA (02/08/2026 — MAN-OFF26-10-11-REG): §5 da F1 acima está REFUTADO

> A F1 de 18/06 **permanece preservada verbatim acima** como registro histórico (precedente de
> correção de premissa do [[DP1]]). O que segue **não a reescreve** — corrige-a com evidência
> obtida por **experimento manual na liga fantasma real**, criada em 02/08/2026.

**A premissa refutada.** O §5 afirma que a reserva de **$1 por slot vazio** é "regra interna do
Manager, **inexistente no Sleeper**", e conclui, em negrito, que a auditoria **NÃO** pode comparar
`fa_budget` e deve usar `raw_budget` ou Σ salários. **Falso: o Sleeper aplica a mesma reserva.**

**Fórmula do teto de lance, CONFIRMADA por experimento:**

```
teto = 200 − gasto − (vagas_restantes − 1)
```

Verificação (time com **$150 gastos** e **21 vagas livres** → teto **$29**):

| tentativa | resultado |
|---|---|
| $40 | **rejeitado** — *"The specified slot does not have enough budget."* |
| $33 | **rejeitado** — mesma mensagem |
| $32 | **rejeitado** — mesma mensagem |
| **$29** | **aceito** |

Confirmado **no sentido oposto** (ausência de falso positivo): outro time recebeu **10 keepers
somando $140** (folga de $49) **sem nenhum aviso**.

**Consequência para a auditoria: a base de comparação correta é `usable_draft_budget`** — o
`fa_budget` que a keeper sheet **já entrega** (`cuts.py`, via
`salary_engine.draft_budget(...)["usable_draft_budget"]`), e **não** `raw_budget`. A **decisão de
produto 2** listada no "Resumo dos gaps" ("escolher a base de comparação de budget") passa a
**RESOLVIDA POR EVIDÊNCIA**, não por arbitragem — não há o que decidir: as duas plataformas usam a
mesma fórmula.

**⚠️ Ressalva registrada (conferência aritmética PENDENTE, não é experimento):** o Sleeper reserva
sobre as **22 rodadas do draft** configuradas na sala; a regra **8.3.4** conta slots pelo
**regulamento da liga**. **Se as contagens divergirem, os limites não coincidem apesar de a fórmula
ser idêntica.** Isso é conferência de aritmética contra o regulamento — não precisa de novo
experimento, mas **não foi feita**.

**O que NÃO mudou da F1:** o gap de leitura pré-draft (§2 — nada no código lê o estado pré-draft)
segue de pé, e é o **mesmo probe** que o [[OFF26-11]] aguarda. As pontes de owner (§4) e de jogador
(§3) seguem como descritas.

**Terreno novo para a auditoria (achado do [[OFF26-10]]):** times **acima do teto não conseguem ser
populados no board** — a designação é recusada. Logo a auditoria não é só um diff pós-população:
o Manager pode **calcular antecipadamente quais times ficarão bloqueados**, antes de o Cowork
tentar.

#### Identificadores da liga fantasma (MAN-OFF26-IDS-REG, 02/08/2026) — o gap §1 da F1 tem os dados

O §1 acima levantou "como apontar para a liga fantasma" e listou 3 opções de terreno **sem
decidir**. Os **valores** agora existem — a decisão de **como parametrizá-los**, não:

| campo | valor | estabilidade |
|---|---|---|
| **`league_id`** | `1389725099556372481` | **estável** |
| **`draft_id`** (atual) | `1389755381567213568` | ⚠️ **muda a cada reset** |
| ~~`draft_id` (anterior)~~ | ~~`1389725100684611584`~~ | ☠️ **morto** |

- Liga **Dynasty SB FA Auction** (permanente, Redraft, 12 times, Auction, $200, 22 rodadas, 3 WR).
- **Os dois são distintos e NÃO deriváveis um do outro por inspeção** — lidos das URLs da página da
  liga e do draft board. Reforça o precedente do `draft_import.py` citado no §1: passa-se o
  **`draft_id`** e **deriva-se** o `league_id` do objeto do draft; o caminho inverso não é
  inspecionável.
- **Registrados como DADO, deliberadamente NÃO persistidos** em constante, `AppConfig` ou coluna.
  As **opções (a)/(b)/(c) do §1 seguem abertas** — ter o número não escolhe onde ele mora.

##### ⛔ RESTRIÇÃO DE DESENHO sobre a decisão 1 (MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026)

**O `draft_id` NÃO é estável — evidência direta.** O **RESET DRAFT de 02/08/2026 gerou um draft
novo, com id novo**: o `draft_id` registrado poucas horas antes (`1389725100684611584`) **morreu no
mesmo dia**, e a URL correspondente **trava indefinidamente em LOADING** — **falha silenciosa**,
não erro. Id atual: **`1389755381567213568`**. Presumivelmente muda também **a cada virada de
season**.

**A decisão 1 permanece EM ABERTO — mas o espaço de opções encolheu.** Não estou arbitrando entre
(a) parâmetro por chamada, (b) `AppConfig`, (c) coluna em Team. O que a evidência elimina é um
**atributo transversal a elas**:

> **Qualquer alternativa que PERSISTA `draft_id` está descartada por evidência.** O que se persiste
> (se algo for persistido) é o **`league_id`**, que é estável. O `draft_id` tem de ser **derivado
> do `league_id` a cada uso**.

**Consequência técnica a confirmar na F2/probe:** o precedente do `draft_import.py` é a derivação
no sentido **inverso** (recebe `draft_id` → deriva `league_id`). Aqui é preciso o caminho
`league_id → draft_id`, presumivelmente via `/league/{lid}/drafts` — endpoint **já usado no
código** (`sync_sleeper.py:762`), mas **nunca exercitado contra a fantasma**. **Confirmar
disponibilidade; não assumir.**

**Por que isso é grave além do OFF26-4:** um `draft_id` persistido que morre em silêncio produz
exatamente o pior modo de falha — a auditoria não erra, ela **pendura**. E o momento em que isso
aconteceria é o pior possível: logo após um reset, ou seja, **na virada da intertemporada**.

> ✅ **PRÉ-CONDIÇÃO DO PROBE — atualizada: a janela está ABERTA, mas fecha no próximo reset.** O
> board **está populado** (Team 3/4/5, dados de teste), então o probe bloqueador do §2 — *o que a
> API expõe **pré-draft** (designações + salário de keeper)* — **tem o que ler agora**. Rodar
> **antes do próximo RESET DRAFT**, que já está pendente. A confirmação **pós-draft** do
> `is_keeper:false` ([[OFF26-11]]) continua exigindo **rodar um draft de teste**, o que o board
> populado agora torna possível.


#### PROBE read-only do estado pré-draft (MAN-OFF26-4-PROBE, 03/08/2026) — ✅ o bloqueador do §2 CAIU

> **Probe empírico contra a liga fantasma real** (`Dynasty SB FA Auction`), executado por leitura da
> **API pública read-only** já usada pelo projeto (`api.sleeper.app/v1`, mesmo `BASE_URL` de
> `sync_sleeper._get`). **Zero escrita**; **draft NÃO iniciado**; **nenhum reset**; **board intacto**
> ao fim. Scripts transitórios no scratchpad, **não commitados**.
>
> **Resultado de uma frase: o §2 da F1 — "nada lê o estado pré-draft, e o que a API expõe é questão
> empírica" — está RESOLVIDO. A API expõe TUDO o que a auditoria precisa, com valor.**

**P1 — Derivação `league_id → draft_id`: ✅ FUNCIONA, e por DOIS caminhos.**
- **`GET /league/{lid}` já traz `draft_id` direto** (campo de topo): `"1389755381567213568"` —
  **igual ao vigente**. É **1 request**, não 2.
- **`GET /league/{lid}/drafts`** → lista com **exatamente 1 draft**, o vigente (`status:
  "pre_draft"`, `type: "auction"`, `season: "2026"`, `settings.rounds: 22`, `budget: 200`).
- **O draft morto NÃO aparece na lista** — a pergunta "como distinguir o vigente se vier mais de
  um" **não se coloca hoje**. Se um dia vier, os discriminadores disponíveis são `status` e
  `created`. **Não garantido por contrato** — tratar como `len==1` esperado, não assumido.
- **Pendência herdada do D1: FECHADA.** O caminho existe e responde contra esta liga.

**⛔ P1c — REFUTAÇÃO DE PREMISSA (relevante para o D1): o draft morto NÃO trava na API.**
`GET /draft/1389725100684611584` → **HTTP 404, corpo `null`, em 0,2 s**. Idem `/picks`.
**O "trava em LOADING" é comportamento do app WEB, não da API.** Pela API a distinção morto × vivo
é **limpa e imediata**. → O requisito do D1 de *"timeout explícito e mensagem própria"* **continua
sendo boa prática** (o `_get` do projeto já tem `timeout=15`), mas **não é o mitigador de um modo de
falha silenciosa** — pela porta que a auditoria vai usar, **esse modo de falha não existe**. O que
sobra do D1 é o essencial e **inalterado**: não persistir `draft_id`.

**P2 — Designações pré-draft: ✅ EXPOSTAS.**
- **Superfície:** `GET /draft/{did}/picks` — **a mesma** já usada pelo projeto, **com o draft em
  `status: "pre_draft"`**. Retornou **24 registros** = exatamente as 24 designações do board.
- **Não é preciso endpoint novo nem superfície exótica** — o que impedia era o **gate
  `status == "complete"`** nos consumidores (ver P6), não a API.
- **Shape da pick:** `draft_id`, `draft_slot`, `is_keeper`, `metadata{}`, `pick_no`, `picked_by`,
  `player_id`, `reactions`, `roster_id`, `round`.
- **`metadata`:** `amount`, `first_name`, `last_name`, `player_id`, `position`, `slot`, `sport`,
  `status`, `team`, `number`, `years_exp`, `injury_status`, `news_updated`, `team_abbr`,
  `team_changed_at`.

**P3 — Salário: ✅ LEGÍVEL pré-draft, em `metadata.amount` (STRING).**
**A auditoria pode comparar salário, não só presença.** `amount` vem como **string** (`"40"`) —
coerção é responsabilidade do leitor.

**✅ Caso concreto de verificação — os três totais RECONSTRUÍDOS do payload, exatos:**

| `roster_id` | designações | Σ `amount` | esperado | confere |
|---|---|---|---|---|
| 3 | 10 | **$148** | 10 / $148 | ✅ |
| 4 | 8 | **$95** | 8 / $95 | ✅ |
| 5 | 6 | **$60** | 6 / $60 | ✅ |

Conferência nominal do Team 3 bate 10/10 (L. Jackson QB BAL $40 · B. Robinson RB ATL $35 ·
K. Williams RB LAR $12 · J. Chase WR CIN $30 · D. London WR ATL $14 · **J. Waddle WR DEN $8** ·
B. Bowers TE LV $5 · C. Brown RB CIN $2 · B. Aubrey K DAL $1 · L. Rams DEF LAR $1).
*(O "Waddle = DEN" que a 2ª execução do Cowork estranhou vem **do próprio Sleeper** — reforça o
diagnóstico de que a divergência era **da lista de teste**, não da plataforma; ver [[OFF26-5]].)*

**P4 — Pontes de identidade.**
- **Jogador = `player_id`**, e **casa com `sleeper_player_id`** (ex.: Lamar Jackson `4881`, Bijan
  `9509`). Duplicado em `metadata.player_id`.
- **⚠️ Achado não previsto: DEF tem id NÃO-NUMÉRICO** — `L. Rams` vem com `player_id: "LAR"` (sigla
  do time). Qualquer coerção a `int` **quebra em DEF**. Vale para o D3 e para a F2.
- **Time = `roster_id`** (inteiro, 1-12), redundante em `draft_slot` e `metadata.slot`.
  **`picked_by` vem VAZIO (`""`) em todas as 24** — não serve de ponte.
- **⛔ `owner_id` NULO em 11 dos 12 rosters** — só o `roster_id=1` tem dono
  (`1130162144764506112`, `MellowBR`, o comissário). `/league/{lid}/users` retorna **1 usuário**.
  → **O D6 está CONFIRMADO na prática: a ponte de owner não é exercitável hoje**, e a F2 segue
  **não validável contra placeholders**. **Mas isto NÃO bloqueia a auditoria por `roster_id`** — a
  designação já vem chaveada por roster, e o `roster_id` é estável na liga permanente.

**P5 — Budget por time: ❌ NÃO EXISTE campo na API.**
- `draft.settings.budget = 200` é **global**, não por time.
- `roster.settings` traz só `fpts/wins/losses/ties/total_moves/waiver_budget_used/waiver_position`
  — **nenhum campo de budget de auction**. `roster.players`, `roster.keepers` e `roster.metadata`
  vêm **vazios/nulos** (confirma o achado do [[OFF26-6]]: designação **não** popula roster).
- → **O budget é derivável APENAS por soma das designações** — exatamente o que o §5 da F1 e o D2
  já mandavam. **A UI mostra um campo por time que a API não expõe.**

**P6 — Réplica: SIM, existe, e é dupla.**
- **Dois consumidores** de `/draft/{did}/picks`: `routes/draft_import.py:39` (OFF26-3) e
  `sync_sleeper.py:872` (rebuild do [[F8]]a).
- **A leitura de `metadata.amount` está REPLICADA** nos dois, **com coerções diferentes**:
  `draft_import.py:146` faz `float(amount)`; `sync_sleeper.py:888` faz `int(amount_raw)`. Ambos
  tratam `None`/`""`, mas por caminhos próprios.
- **Ambos gateiam em `status == "complete"`** (`draft_import.py:94`, `sync_sleeper.py:836`) — **é
  ESTE o motivo de "nada ler pré-draft"**, não uma limitação da API. **Confirma o §2 da F1 na
  causa, e o corrige no efeito.**
- **Sem réplica em template/JS:** `draft_import.html:89` só renderiza o que o servidor mandou.
- → **Recomendação de terreno para a F2 (não é desenho):** a auditoria é o **3º** leitor de picks.
  Se ela criar a própria coerção de `amount`, vira a **3ª réplica** — candidato natural a helper
  único, no espírito da invariante do [[F10]].

##### Refutação de premissas (DEV_METHODOLOGY)

**(a) Premissas deste prompt / da spec contraditas pelo observado:**
1. *"a URL de um draft morto trava em LOADING em vez de dar erro — modo de falha silenciosa"* →
   **premissa falsa PARA A API**: `404` + `null` em 0,2 s. Verdadeira só para o app web.
2. *"o caminho `league_id → draft_id` precisa ser confirmado como disponível"* → **disponível, e
   por dois caminhos** — inclusive um mais barato (`league.draft_id`, 1 request) que o previsto
   (`/drafts`).
3. *"a ponte de owner determina se a auditoria pode casar coluna e time"* → **deslocamento**: a
   auditoria **não precisa** de `owner_id` para casar — a designação **já vem com `roster_id`**. O
   `owner_id` é necessário para casar **`roster_id` ↔ time do Manager**, que é outra coisa (e é
   isso que o D6 trava).

**(b) Presentes e não previstos por este prompt:**
4. **`is_keeper: false` em TODAS as 24 designações** — o indício do [[OFF26-11]] **agora tem
   evidência de payload**, na superfície **pré-draft**. **Continua NÃO sendo a confirmação
   definitiva** (que é pós-draft, fora do escopo deste probe), mas o campo **está lá e vale
   `false`**.
5. **`player_id` de DEF é string de sigla (`"LAR"`)**, não numérico (item 4 do P4).
6. **`pick_no`/`round` NÃO indicam vaga de roster.** As 24 designações ocupam `pick_no` 1..24
   sequencialmente (rounds 1 e 2), na **ordem em que foram criadas** — as 10 do Team 3 são
   `pick_no` 1-10, todas `round=1`, apesar de o draft ter 12 times. **Não há informação de qual
   vaga (QB/RB/FLEX/BN) a designação ocupa** — só a **posição do jogador** (`metadata.position`).
   → **Consequência para o D5: não existe classe "slot errado" auditável.** A auditoria pode
   verificar **presença, valor e time**; **não** pode verificar alocação de vaga.
7. **`roster_positions` da fantasma tem 22 entradas:** `QB, RB, RB, WR, WR, WR, TE, FLEX, K, DEF`
   + **12× `BN`**. → **Insumo direto para a ressalva aritmética do D2**: o lado Sleeper da conta é
   **22 slots = 10 titulares + 12 banco**. **A ressalva NÃO está resolvida** — falta o outro lado
   (contagem pelo regulamento 8.3.4) —, mas o número do Sleeper agora está medido, não suposto.
8. **⚠️ A fantasma NÃO tem slot de IR**, enquanto a liga real tem (máx. 2). O runbook manda
   espelhar a liga real e o **D5 do [[OFF26-2]]** diz que **IR conta normalmente** no budget. Se a
   sheet contar IR e a sala não tiver a vaga, **as contagens de slot divergem** — **entra na mesma
   ressalva aritmética do D2**, e é um caso concreto de divergência, não hipotético.
9. **`league.settings.draft_rounds = 3`** enquanto **`draft.settings.rounds = 22`** — dois campos
   homônimos com valores diferentes em níveis diferentes. **A F2 deve ler `rounds` do objeto do
   DRAFT**, não `draft_rounds` da liga.
10. **`league.metadata.copy_from_league_id = "1316547584378048512"`** — a fantasma foi **criada por
    cópia da liga REAL**. Corrobora "config espelha a real" ([[OFF26-6]]) e explica o 3 WR.
11. `league.status = "pre_draft"`, `previous_league_id = null`, `keeper_deadline = "2"`.

##### O que este probe FECHA e o que segue ABERTO na spec D1–D7

| pendência | estado após o probe |
|---|---|
| **D7** — probe exige board populado | ✅ **EXECUTADO** na janela aberta; designações + valores lidos |
| **D1** — `league_id → draft_id` nunca exercitado | ✅ **FECHADA** — funciona, dois caminhos |
| **D1** — modo de falha "trava em LOADING" | ✅ **REFUTADO para a API** (404 limpo) |
| **§2 da F1** — o que a API expõe pré-draft | ✅ **RESOLVIDO** — designação, valor, jogador e roster |
| **D5** — classes de divergência | ⚠️ **AJUSTAR**: presença/valor/time auditáveis; **vaga NÃO** |
| **D2** — ressalva aritmética 22 × 8.3.4 | 🔲 **ABERTA** — lado Sleeper medido (22 = 10+12 BN, **sem IR**); falta o lado do regulamento |
| **D6** — ponte de owner | 🔲 **ABERTA e confirmada como bloqueio de validação** (11/12 `owner_id` nulos) |
| **D3** — `sleeper_player_id` na sheet | 🔲 **ABERTA** (decisão da F2) — mas o probe entrega o dado: id casa, **exceto DEF, que é sigla** |
| **[[OFF26-11]]** — `is_keeper` como discriminador | ⚠️ `false` **confirmado no payload pré-draft**; confirmação **pós-draft** segue pendente |

**Estado ao fim do probe:** board **intacto** (24 designações, 3 times), draft **não iniciado**
(`status: pre_draft`), **nenhuma escrita**, nenhum reset. **A janela do D7 continua aberta** — e
continua fechando no próximo RESET DRAFT.

**Modelo recomendado p/ a próxima fase:** a F2 do OFF26-4 está **desbloqueada do lado da leitura**.
O que ainda a limita é **validação** (D6, placeholders), não **construção**.

---


### OFF26-7 — Dry run end-to-end da intertemporada
🔲 **Registrado 16/06/2026** — MAN-OFF26-6-7-REG — Prioridade **Alta** — **ensaio geral
operacional (não-código)**

**Descrição:** ensaio geral do **processo inteiro encadeado** em ambiente de teste,
exercitando a cadeia completa: **rookie draft de teste → import (OFF26-3) → ESPN
parcial+definitivo (E4-a) → janela selada (OFF26-1) → late drop pós-lock (OFF26-10) →
keeper sheet (OFF26-2) → Cowork popula a liga fantasma permanente (OFF26-6) → auditoria
(OFF26-4) → FA auction de teste → import do resultado, separando keeper de arremate
(OFF26-3 + OFF26-11)**.

> **Emenda (02/08/2026 — MAN-OFF26-10-11-REG), dois ajustes na cadeia acima:**
> (1) **o rookie draft roda na liga real, não em liga fantasma** — a sala separada existe só
> para a **FA auction** (ver bloco EMENDA no registro do pacote); "Cowork monta a liga
> fantasma" virou "**popula**", porque a liga fantasma é **permanente** ([[OFF26-6]]) e o
> trabalho anual é só o board de keepers.
> (2) **duas etapas novas entraram na cadeia** — [[OFF26-10]] (late drop de 22/08, entre o lock
> e a sheet definitiva) e [[OFF26-11]] (importador separando keeper de arremate no import do
> resultado do auction). Ambas são **costuras**, exatamente o objeto deste dry run.

**Motivação:** cada item OFF26 tem validação própria, mas as **COSTURAS** entre eles nunca
foram exercitadas juntas: a keeper sheet sai num formato que o Cowork transcreve? a liga
montada bate com o que a auditoria espera ler? o import reconhece times/jogadores da liga de
teste? O ensaio valida o **formato de handoff entre etapas**, não a lógica interna de cada
peça (já coberta item a item).

**Escopo resumido:** exercitar a cadeia inteira em ambiente de teste com foco nas **interfaces
de handoff** entre módulos; registrar onde uma etapa produz algo que a seguinte não consome
como esperado.

**Relação OFF26-6 ⊂ OFF26-7:** OFF26-6 (Cowork monta) é **uma etapa** dentro do ensaio maior;
pode ser validada **antes e isolada**, mas também é exercitada **dentro** do dry run completo.

**Dependências:** só pode rodar **de verdade** depois que **OFF26-1, OFF26-2 e OFF26-4
existirem** (não se ensaia cadeia cujas peças centrais não foram construídas). OFF26-3 já está
✅; E4-a já existe.

**DECISÃO EM ABERTO (pendente do owner — não arbitrada):** OFF26-7 é um **gate único final**
antes da intertemporada real, **ou** roda **por etapas** conforme as peças (OFF26-1/2/4) ficam
prontas? Registrar a decisão antes de iniciar a F1 do item.

> **Nota registrada (06/08/2026, MAN-OFF26-10-SPEC) — transferência dos arremates para a liga
> real é MANUAL, por cada owner.** Os keepers **já estão** nos rosters reais; movem-se só as
> **adições novas** do leilão (~30–50 na liga toda — rotina de waiver). Linha no checklist
> pós-leilão da cadeia: **"cada owner adiciona seus arremates antes da semana 1; admin confere
> contra o import do Manager"**. Sem item novo — é passo operacional deste dry run/checklist.

---

### OFF26-8 — Cowork aplica os cortes no roster real do Sleeper
🔲 **Registrado 16/06/2026; ESVAZIADO PELO REDESENHO DE 06/08/2026 (MAN-OFF26-1-ETAPA2) —
Prioridade Média → BAIXA** — MAN-OFF26-8-REG — **capability operacional (NÃO é código do
Manager)**

> **Emenda (06–07/08/2026): este item perdeu quase todo o objeto.** Os cortes de 20/08 passam a
> ser feitos **pelos próprios owners, direto no Sleeper** — não existe mais "lista de cortes
> revelada pelo Manager" para o Cowork aplicar. **Sobra um resíduo, e ele é MANUAL por decisão
> do owner:** a **execução dos drops revelados pela urna** em 22/08 (U7 do [[OFF26-10]]) —
> poucos drops (**no máximo 1 por time**), feitos pelo owner/admin, com **conferência do admin**
> de que sumiram dos rosters antes do sync final. **Não há automação a construir aqui**; se
> algum dia voltar, é sobre a lista da urna, não sobre a janela grande.

**Descrição:** a partir da **lista de cortes** revelada pelo OFF26-1 (janela selada),
um agente **Cowork + Claude in Chrome** dirige a UI do Sleeper para **dropar os jogadores
cortados** do roster real de cada time. O OFF26-1 produz a lista auditável de cortes mas
**não os executa em lugar nenhum**; esta é a peça que efetiva esses cortes no Sleeper.

**Motivação:** a API do Sleeper é **read-only** — o Manager nunca escreve lá. Mexer no
roster real (dropar jogadores) só é possível **dirigindo a UI pelo navegador**, mesma
natureza operacional de OFF26-5 (runbook) e OFF26-6 (PoC) — itens `(op)` fora do código
do Manager. Sem esta capability, os cortes revelados pela janela selada ficariam órfãos
entre "decidido no Manager" e "aplicado no Sleeper".

**Escopo resumido:** a partir da lista de cortes do OFF26-1, roteiro operacional do
agente Cowork para dropar cada jogador cortado do roster real do time correspondente na
UI do Sleeper. Registro apenas — sem implementação.

**Dependências:** depende do **OFF26-1** (fonte da lista de cortes selada/revelada).
Conceitualmente próximo de **OFF26-5/OFF26-6** (mesmo procedimento Cowork supervisionado
pelo navegador).

**Relação OFF26-8 ⊂ OFF26-7:** é um **subconjunto operacional** do dry run E2E — entra como
a etapa "aplicar cortes no Sleeper" da cadeia. **Irmão de OFF26-6** (mesma natureza:
validação/procedimento operacional não-código que dirige a UI do Sleeper).

---

### OFF26-21 — Motor legado de `/cuts` perdeu a última função
🔲 **Registrado 07/08/2026 (MAN-OFF26-10-SMOKE)** — Prioridade **Baixa** — **resíduo virado item**,
no precedente do MAN-OFF26-4-SLOTS

**O que é.** O bloco **Admin** da tela `/cuts` (abrir/fechar janela · lock + revelação · suprir por
time) ficou vivo na aposentadoria da porta (MAN-OFF26-1-ETAPA2) por **uma razão explícita e
registrada na época**: era, naquele momento, **o único produtor de keeper sheet** —
`_build_keeper_sheet` exigia um snapshot canônico, e removê-lo antes da F2 deixaria a liga sem
sheet se a F2 escorregasse.

**Por que virou item.** O **U7 tirou essa função dele**: a sheet nasce do sync e não olha mais para
`CutWindowAudit`. O bloco admin passou a ser **motor sem consumidor** — e, pior, é a única porta na
UI capaz de abrir a janela grande por engano durante a urna (hoje mitigado por rótulo "legado" e
por aviso na tela, não por trava).

**O que NÃO muda com a remoção (e é por isso que a prioridade é Baixa):** as **rotas** de
declaração legadas continuam necessárias — são o **motor que a urna reusa** e a **rede de
regressão** da hierarquia owner > admin (7 testes). O que se discute aqui é **a tela**, não o
mecanismo.

**Escopo quando for feito:** remover o bloco admin de `templates/cuts.html` (mantendo a página como
explicação do fluxo), decidir o destino do `POST /api/cuts/admin/open` (a única porta que liga
`cuts_window_open`) e conferir que a suíte da janela segue verde sem tocar em lock/hash/reveal.

**Cross-refs:** [[OFF26-1]] (de onde veio, e por que ficou), [[OFF26-2]] (o U7 que o esvaziou),
[[OFF26-10]] (a urna, que é a porta única de verdade).

---

### OFF26-22 — A auditoria de keepers audita sheet PROVISÓRIA como se fosse definitiva
⚠️ **CORRIGIDO 08/08/2026 (MAN-OFF26-22) — aguardando conferência em produção.** Registrado no
mesmo dia pelo Passo 0 do MAN-OFF26-11-F2 — Prioridade **Média**

#### Correção (08/08/2026, MAN-OFF26-22)

**Decisão de produto do owner: opção (b) — rodar e DESQUALIFICAR o veredito.** A execução sobre
sheet provisória **tem valor** (a auditoria roda 3× ou mais na janela de 20–24/08, e divergências
achadas cedo são divergências corrigidas cedo); o que ela não pode é responder *"posso abrir o
leilão?"*. Três estados no lugar de dois:

| sheet | veredito | `gate_qualified` |
|---|---|---|
| **DEFINITIVA** | `liberada` / `bloqueada` — **idêntico ao de hoje** | `True` só em `liberada` |
| **PROVISÓRIA** | **`nao_qualificada`** — relatório completo, divergências listadas, *"ABERTURA LIBERADA" impossível* | sempre `False` |
| **indisponível** | `bloqueada` por falta de insumo, com a causa real prefixada | sempre `False` |

**Onde a mudança mora:** só na **camada de leitura** (`keeper_audit.build_sheet` + a nova
`keeper_audit.qualify`), que roda **em volta** do núcleo. O núcleo puro, o formato de sheet que ele
consome e as fixtures congeladas estão **intactos** — os 34 testes passam **sem uma edição**.

⛔ **O carimbo viaja por fora da estrutura que o núcleo lê:** `build_sheet` o entrega na chave
`stage_meta`, e `run_audit` **remove** essa chave antes de chamar `audit()`. Há teste que espiona a
chamada e falha se `stage_meta` chegar ao núcleo, e outro que falha se a string `stage` aparecer no
corpo de `audit()`.

⛔ **Nenhuma segunda definição de "definitiva":** `_stage_meta` **consome** o `stage` que a fonte já
emite. Há teste que passa um carimbo cujos timestamps "pareceriam" definitivos com `stage:
provisoria` e exige que valha o da fonte.

##### Passo 0 — verificação de terreno

1. ✅ **Gate morto, confirmado.** `routes/cuts._build_keeper_sheet` devolve `"revealed": True`
   **e** `"available": True` **hardcoded** (linhas 480-481) — o `if not raw.get("revealed")` de
   `build_sheet` nunca dispara desde o U7.
2. ✅ **Estágio descartado na montagem, confirmado.** O `build_sheet` antigo devolvia apenas
   `revealed`, `season`, `lock_timestamp` e `teams`: `stage`, `stage_label`, `sync_timestamp`,
   `late_drop`, `available` e `source` morriam ali.
3. ⚠️ **Premissa do prompt ajustada:** *"sheet ausente permanece com o comportamento atual"* — não
   havia comportamento atual a preservar, porque o ramo era **inalcançável** (`available`
   hardcoded). Ele foi **revivido com uma condição que de fato dispara**: `available` da fonte **E**
   pelo menos um time na sheet. Hoje isso significa "nenhum time cadastrado".
4. ⚠️ **Por que o código morto sobreviveu ao U7:** os 34 testes exercem `audit()` **diretamente**,
   com fixtures — **nenhum** deles chama `build_sheet` ou `run_audit`. A camada de leitura estava
   **inteiramente sem teste**. É a causa estrutural, e ela some agora: `keeper_audit_stage_test.py`
   é o primeiro teste dessa camada.
5. ⚠️ **Resíduo NÃO corrigido (restrição):** a mensagem do `_no_input`, dentro do núcleo puro, ainda
   diz *"A janela de cortes ainda não foi revelada"* — obsoleta desde o U7 (a sheet não vem mais de
   janela nenhuma). Corrigi-la exigiria editar o núcleo. `qualify` **prefixa** a causa real, então o
   operador lê primeiro a frase correta; a obsoleta fica abaixo. Fica registrado como o que é.

##### Passo 0 — a decisão "provisória × definitiva" está replicada?

**Não. Um produtor, N leitores** — e o fix entrou como leitor.

- **Calculada em um único lugar:** `routes/cuts.py:440-445` — `revelação da urna + sync posterior`.
  Grep confirma: nenhum outro sítio reimplementa a regra.
- **Consumida** comparando com o literal `"definitiva"` em 4 sítios: `keeper_exclusion.py` (freeze e
  gate do import), `templates/keeper_sheet.html` (2×) e agora `keeper_audit.STAGE_DEFINITIVA`.
- **`templates/draft_import.html` apenas exibe** `stage_label`/`source_stage` — não decide nada.
- ⚠️ **Colisão de vocabulário, não de lógica:** `routes/league.py:82` fala em "selo PROV" e
  "ESPN **DEFINITIVA**" — é a **tabela ESPN**, outro eixo, sem relação com o estágio da sheet. Não
  confundir ao caçar réplicas.
- **Resíduo menor:** o literal `"definitiva"` está repetido nos 4 leitores. Uma constante
  compartilhada teria de morar no produtor (`routes/cuts.py`) ou no módulo de exclusão — ambos sob
  restrição nesta sessão. Registrado, não feito.

##### Validação (08/08/2026) — 25 testes novos (`keeper_audit_stage_test.py`)

| # | Validação | Resultado |
|---|-----------|-----------|
| V1 | sheet **provisória** (urna revelada, sem sync posterior) | relatório completo, divergências listadas, veredito **`nao_qualificada`**; o motivo cita **os dois carimbos** (quando revelou × qual é o sync) e o que falta |
| V2 | sheet **definitiva**, mesmo insumo | relatório **idêntico campo a campo** ao de antes; as únicas chaves novas são `sheet_stage` e `gate_qualified` |
| V2b | contraste com o **núcleo real** (cenário coerente montado no teste — nenhuma fixture congelada produz `liberada`) | definitiva → **`liberada` + gate**; provisória → **`nao_qualificada`**, com **as mesmas 0 divergências**. Só a autoridade muda |
| V3 | sheet **ausente** (zero times) | bloqueio por falta de insumo **revivido**, com a causa real prefixada; **não** se confunde com provisória |
| V4 | suítes | núcleo da auditoria **34/34 sem editar teste nem fixture** · `salary_engine` **54/54** · exclusão **36/36** · `late_drop` 64 · `janela` 22 · `cap_regua` 14 · `contract_year` 20 · `trilha_fa_proj` 17 · **novos 25** → **286 verdes** |
| V5 | liga fantasma real, só `GET` | `/admin/keeper_audit` **200**, `draft_id` derivado (`1389755381567213568`, `pre_draft`, **24 designações**), sheet **PROVISÓRIA** (urna não revelada), veredito **`nao_qualificada`**, `gate_qualified: false`, "Abertura liberada" **ausente** do HTML. Board intacto |

> **Nota:** a suíte do `salary_engine` são **54** testes, não 48 (o número do prompt vinha
> desatualizado desde o OFF26-18).

⛔ **O que falta para ✅:** conferência em **produção** — abrir `/admin/keeper_audit` no ar e ver o
selo PROVISÓRIA + o veredito de conferência antecipada, e o owner confirmar o hash live (PROC1).
A conferência com sheet **DEFINITIVA** só é possível a partir de 22/08.

**Arquivos:** `keeper_audit.py` (camada de leitura), `keeper_audit_stage_test.py` (novo),
`templates/keeper_audit.html`, `improvements.md`, `manager_devplan.md`, `CLAUDE.md`.

---

##### Registro original (o achado)

**O que é.** `keeper_audit.build_sheet` ainda abre com o gate herdado da origem antiga:

```python
raw = _build_keeper_sheet(season)
if not raw.get("revealed"):
    return {"revealed": False, "season": season}
```

Desde o **U7** ([[OFF26-2]], 07/08/2026) `_build_keeper_sheet` devolve **`revealed: True`
incondicionalmente** — a chave passou a significar "há sheet utilizável", e foi preservada
justamente para não quebrar o contrato que o núcleo puro do [[OFF26-4]] lê. Consequência: **este
ramo nunca dispara**, e com ele morreu o único bloqueio da auditoria por falta de insumo.

**Por que importa.** A auditoria é o **gate de abertura do leilão**, e hoje ela roda igual sobre uma
sheet **PROVISÓRIA** (late drop não revelado, ou revelado e não sincronizado) e sobre a
**DEFINITIVA**. O veredito "liberada" sobre uma sheet provisória é uma **liberação sobre dado que
ainda vai mudar** — e o estágio existe, está calculado, e simplesmente não chega até ela
(`build_sheet` descarta `stage`/`stage_label`/`sync_timestamp`/`late_drop`).

**Nota:** o importador do [[OFF26-11]] **não** depende disso — ele lê o selo direto de
`_build_keeper_sheet` e recusa congelar lista provisória. O gap é **da auditoria**.

**Escopo quando for feito:** decidir se `stage` vira insumo do veredito (bloqueio duro, aviso, ou
só exibição no meta) e propagá-lo por `build_sheet` sem alterar o formato que o núcleo puro
consome — o núcleo e as **fixtures congeladas** (34 testes) não podem mudar de forma.

**Cross-refs:** [[OFF26-4]] (a auditoria), [[OFF26-2]] (o U7 que reescreveu a origem e deixou o
resíduo), [[OFF26-11]] (onde o achado apareceu).

---

### OFF26-11 — Importador distingue keeper de arremate novo
⚠️ **F2 IMPLEMENTADA (08/08/2026, MAN-OFF26-11-F2) — aguardando o smoke real do leilão de 24/08.**
Decisão de produto arbitrada em 06/08 (opção A — Manager é fonte única; sheet como lista de
exclusão) — MAN-OFF26-10-11-REG → **-SPEC** → **-F2** — Prioridade **Alta** (caminho crítico
**24/08**)

#### F2 — implementação (08/08/2026, MAN-OFF26-11-F2)

**Onde o discriminador nasceu:** módulo próprio **`keeper_exclusion.py`**, no molde do
`salary_engine`/`keeper_audit` — **núcleo puro** (`build_index` / `classify_pick` /
`compute_exclusion_hash`: sem DB, sem rede, sem Flask) + camada de IO. **Nenhuma segunda definição
de "quem é keeper"**: a lista vem de `keeper_audit.build_sheet` (o produtor que já enriquece a
sheet com `sleeper_player_id`) e o selo provisória × definitiva vem de
`routes.cuts._build_keeper_sheet` (a fonte única do estágio). O importador só **consulta**.

**Regra única:** pick cujo jogador consta na lista **para o mesmo time do pick** → keeper, não
ingerido. Consta para **outro** time → pendência. Não consta → arremate.

**O congelamento (a decisão dentro da margem que o prompt delegou).** Mecanismo escolhido:
**snapshot explícito com hash**, gravado em `AppConfig["keeper_exclusion_frozen"]` por ato de
admin (`POST /api/draft_import/exclusion/freeze`), recusado enquanto a sheet for PROVISÓRIA ou
houver keeper sem `sleeper_player_id`; re-congelar exige justificativa (molde M8). Descartadas:
**derivar ao vivo** (é o bug — contaminação), **gatear por carimbo de sync** (recusa o import
justamente quando ele é correto, e não distingue o sync do drop do sync que trouxe arremates) e
**snapshotar automático no 1º preview** (congela sem que ninguém tenha declarado o momento — se o
1º preview vier depois da contaminação, congela o erro).
**O que NÃO cobre (declarado, não mitigado):** congelar **tarde** (depois de owners já terem
readicionado arremates) produz lista contaminada — a mitigação é operacional (o snapshot carrega
`sync_timestamp` + `frozen_at`, a tela os exibe, o runbook fixa o momento); keeper que o board não
designou é matéria da auditoria [[OFF26-4]], que roda antes; e um sync tardio pode virar o selo
para DEFINITIVA sem que os drops tenham sido executados — quem prova isso é o operador.

**Bloqueios (nunca degradar para "ingerir tudo"):** sheet indisponível, PROVISÓRIA, não congelada
ou congelada de **outra season** bloqueiam o preview do modo auction, cada uma com mensagem e
`exclusion_state` próprios. **Pendências** (keeper de outro time · pick sem `player_id` · roster
não mapeado a time local) **bloqueiam a confirmação e não têm caminho de resolução** — de
propósito: são exatamente os casos em que o importador precisaria arbitrar de quem é o jogador.

**Escopo por modo:** tudo isso é **exclusivo do modo auction**. O linear (rookie draft na liga
real) não consulta a lista, não bloqueia e mantém "roster não mapeado" como `unmatched` resolvível.

##### Passo 0 — o que o terreno contradisse (premissas do prompt aferidas contra o código)

1. ⛔ **REFUTADA — "o caso canônico só precisa não ser tratado como continuidade".** Ele **não era
   ingerível pela UI**: `player_lookup.find_player_by_sleeper_id` filtra `is_dropped=False`, então
   o jogador dropado na janela cai em `unmatched` com causa "jogador dropado no banco" — e o
   `<select>` do template só oferecia **Pular** e **Criar novo**. A API já aceitava
   `resolutions[sid] = <player_id>`, mas nada na tela o expunha; "criar novo" **duplicaria** o
   Player com o mesmo `sleeper_id` e perderia o histórico. **Corrigido nesta F2:** o preview passa
   a devolver `suggested_player_id`/`suggested_contract_year` para essa causa e a tela oferece
   *"Reativar <nome> (ano 1)"*. Sem isso a validação do caso canônico ($50 → ano 1) era impossível.
2. ⚠️ **PARCIAL — "consumir o produtor já existente da sheet enriquecida".** `keeper_audit.
   build_sheet` produz os keepers com `sleeper_player_id` **mas descarta** `stage`, `stage_label`,
   `available`, `source` e `late_drop` — repassa só `revealed`, `season`, `lock_timestamp` e
   `teams`. Como está, o produtor **não permite** distinguir provisória × definitiva (requisito de
   bloqueio). Solução tomada **sem tocar em nada guardado por restrição**: `keeper_exclusion` lê os
   **dois** produtores (o enriquecido para os keepers, `_build_keeper_sheet` para o selo). Custo: a
   sheet é montada duas vezes num caminho de admin usado uma vez por temporada. A alternativa
   (passthrough aditivo em `build_sheet`) foi descartada por encostar na restrição "não alterar o
   payload consumido pelo núcleo da auditoria".
3. ⚠️ **ACHADO LATERAL — código morto com efeito de gate.** `keeper_audit.build_sheet` ainda tem
   `if not raw.get("revealed"): return {"revealed": False}`, mas desde o U7 `_build_keeper_sheet`
   **sempre** devolve `revealed: True`. Consequência: **a auditoria [[OFF26-4]] nunca mais bloqueia
   por "sem sheet", e o selo PROVISÓRIA não a bloqueia** — ela audita a sheet provisória como se
   fosse definitiva. Não tocado aqui (é superfície da auditoria, sob restrição); **registrado como
   resíduo** — ver [[OFF26-22]].
4. ✅ **CONFIRMADA — `is_keeper` não discrimina.** Leitura ao vivo de 07/08/2026 (só `GET`):
   `league_id 1389725099556372481` → `draft_id 1389755381567213568` derivado, **24 designações**,
   totais **$148 / $95 / $60**, **`is_keeper: false` em 24/24**. ⛔ **Mas o draft está em
   `pre_draft`** — a confirmação **pós-draft continua NÃO OBSERVADA**, e não foi forçada (rodar o
   draft é escrita na plataforma, ato do owner). O discriminador **não lê** o campo: há teste que
   falha se a string `is_keeper` aparecer no corpo do módulo.
5. ✅ **CONFIRMADAS:** `metadata.amount` é string (`"40"`); `record_acquisition` é porta de
   contrato ano 1 (`player.contract_year = 1`, `models.py:385`); identidade só por `sleeper_id` em
   todo o caminho do importador.
6. ℹ️ **`salary_engine_test` são 54 testes, não 48** — o número 48 no prompt e no `CLAUDE.md` estava
   desatualizado desde o OFF26-18.

##### Passo 0 — o que o importador já tinha e a spec não mencionava

- **`acquisition_type` é binário por `dtype == "linear"`**: qualquer draft **não-linear** (inclusive
  `snake`) cai em `auction_draft` e passa a consumir a lista de exclusão. Coincide com os dois modos
  reais da liga; registrado porque não é o mesmo que "gatear em `type == 'auction'`".
- **Store ESPN de rookie (E2)**: `store_espn_adjusted`/`projected_salary` no preview de unmatched —
  preservado intacto.
- **Idempotência por `event_ref`**: keeper excluído **nunca gera `event_ref`**, logo a idempotência
  não o alcança — se um keeper tivesse sido ingerido por engano antes, a exclusão **não desfaz**.
- **`_budget_alerts` somava tudo** — e no caminho novo isso seria **dupla contagem**: o keeper já
  está no roster corrente (base da simulação) e entraria de novo como pick adicionado. Com a
  exclusão, `matched` já vem sem keepers e o alerta passa a somar **só arremates**, sem mudança de
  fórmula. Medido: keeper $40 + arremate $30 no mesmo time → folha simulada **$73** (base $43 +
  arremate $30), bid máximo **$109**; a dupla contagem daria folha **$113**.
- **Resolução keyed por `sleeper_player_id`, não por `pick_no`** (template e `confirm`): dois picks
  do mesmo jogador colidiriam na mesma resolução. Latente, não alcançado por esta entrega.
- **`skip` com justificativa** continua sendo o único pulo — e é **declarado**, não silencioso.

##### Passo 0 — réplicas da lógica (a pergunta explícita do prompt)

Leitura de picks do Sleeper vive em **3 módulos**, com **coerções divergentes do lance**:

| sítio | papel | coerção de `metadata.amount` |
|---|---|---|
| `routes/draft_import.py` (`_read_draft`) | import (**escreve**) | `float(...)`, fallback **1.0** |
| `keeper_audit.py` (`fetch_board`) | board da fantasma (read-only) | string crua → `_to_int(...,0)` |
| `sync_sleeper.py` (`_collect_draft_events`) | backfill F8 de PlayerHistory | `int(...)`, fallback **None** |

**Três fallbacks diferentes para lance ausente (1.0 / 0 / None).** Não unificados: seria mudança de
comportamento em `sync` e na auditoria, ambos fora do escopo e sob restrição. Já era o achado P6 do
probe de 03/08 (candidato a helper único, espírito do [[F10]]) — **segue aberto**.

**Classificação de pick** (linear × auction) existe **só** no importador; `sync_sleeper.
_classify_draft` classifica *drafts*, não picks — vocabulário parecido, propósito distinto.
**Resolução de identidade**: `find_player_by_sleeper_id` no importador, `players_by_sid` inline no
sync (2 sítios), `board_by_sid` no núcleo da auditoria — **nenhum casa por nome** no caminho do
importador. **O fix NÃO precisa alcançar sync nem auditoria:** o sync não escreve salary/contract e
a auditoria é read-only; só o importador cria contrato.

##### Validação (08/08/2026) — 36 testes novos (`keeper_exclusion_test.py`), 261 no total

| # | Validação | Resultado |
|---|-----------|-----------|
| V1 | keeper do mesmo time nos picks | **0 escritas**; `salary`/`contract_year`/`contract_start_season`/`acquisition_type`/`is_dropped` + contagens de `SalaryHistory`/`AuctionLog` **idênticos** antes/depois |
| V2 | caso canônico **$50** (dropado → recomprado pelo mesmo time) | `contract_year` **3 → 1**, salário **$50**, `is_dropped` **True → False**, +1 `SalaryHistory` +1 `AuctionLog` pela porta canônica |
| V3 | keeper de **outro** time entre os picks | **pendência**, confirm **400**, motivo nomeado (`keeper_de_outro_time`, com o time da sheet); **nem o arremate válido do mesmo lote entrou** |
| V4 | DEF com **sigla** (`"LAR"` keeper / `"SEA"` arremate) | classificação correta, sem coerção, **sem falso keeper**; `"SEA"` cai em unmatched com a causa DST de sempre |
| V5 | sheet **provisória** × **ausente/não-congelada** | import bloqueado com **mensagens distintas** (`provisoria` / `nao_congelada` / `season_errada`); **0 escritas** |
| V6 | **contaminação** — arremate readicionado pelo owner e capturado por sync | a sheet **ao vivo** passa a listá-lo como keeper, **a congelada não**: o arremate **continua sendo ingerido**, contrato ano 1 |
| V7 | reimport do mesmo draft | **0 criados**, 1 já importado, contagens inalteradas |
| V8 | **regressão do modo linear** — rookie 2025 real (`1224848075617484800`), cópia temporária do DB | preview do código novo **idêntico ao do HEAD** em todos os campos (33 matched / 3 unmatched / causas / salários / alertas); **0 escritas** |
| V9 | preview não escreve | contagens de `Player`/`SalaryHistory`/`AuctionLog` iguais antes/depois, em 2 execuções |
| V10 | alerta de budget | soma de arremates **$30** × base (roster corrente) **$43** → folha **$73**, bid máximo **$109**; dupla contagem daria **$113** |
| V11 | suítes | `salary_engine` **54/54**, `keeper_audit` **34/34**, `late_drop` **64/64**, `janela_ensaio` **22/22**, `cap_regua` **14/14**, `keeper_exclusion` **36/36** (+ `contract_year` 20/20, `trilha_fa_proj` 17/17) |
| V12 | leitura real da fantasma (só `GET`) | `draft_id` derivado do `league_id`; **24 designações**, `is_keeper` **false** em 24/24; **draft em `pre_draft`** → **pós-draft NÃO OBSERVADO** |

⛔ **O que o smoke de 24/08 ainda precisa provar** (por isso ⚠️ e não ✅): que o board pós-leilão
real traz keepers e arremates na mesma lista de picks e que a exclusão os separa **com os 12 times
de verdade**; que o congelamento aconteceu **no momento certo** do calendário; e o que os picks
**pós-draft** de fato expõem sobre keeper.

**Arquivos:** `keeper_exclusion.py` (novo), `keeper_exclusion_test.py` (novo),
`routes/draft_import.py`, `templates/draft_import.html`, `templates/keeper_sheet.html`,
`runbook_urna_late_drop.md`, `CLAUDE.md`.

---

##### Registro original (antes da F2)

**Descrição:** os keepers **precisam** estar designados no board da liga fantasma — **não é
opcional**: o Sleeper não tem cap por time, e o cap individual **emerge** dos salários dos
keepers consumindo o budget global do auction ([[OFF26-6]]). Logo, quando o auction rodar, os
picks do draft conterão **keepers e arremates misturados**. O importador [[OFF26-3]] escreve
pela **porta canônica de aquisição** (`record_acquisition`), que é porta de **contrato ano 1**
— se ingerir um keeper, **zera a idade de contrato** de um jogador que **nunca saiu do time**.

**Motivação:** **dano silencioso**, com efeito visível só **anos depois**, na renovação (o
contrato de 4 anos reinicia a contagem). Nada no cap do ano corrente denuncia o erro.

**Caso canônico (owner):** jogador com contrato de **$50** é dropado na janela, vai a leilão e é
**recomprado pelo mesmo time por $50**. **Valor idêntico, natureza diferente** — o contrato
antigo **morreu** e nasceu um **contrato ano 1**. Tratar como continuidade é o erro simétrico:
perde-se a distinção nos dois sentidos (keeper tratado como aquisição **e** re-arremate tratado
como continuidade).

**Por que o cenário nunca foi exercitado:** o importador foi validado contra os **drafts reais
de 2025**, cujas salas **não tinham keeper designado no board**. O caminho
board-com-keepers é **novo** em 2026.

**Questão empírica pendente (destino de probe, NÃO suposição):** os picks pós-draft vêm marcados
de forma que permita **separar keeper de arremate** (ex.: flag `is_keeper` / `metadata` no
payload de `/draft/{id}/picks`), ou o discriminador terá de vir da **keeper sheet do próprio
Manager**, usada como **lista de exclusão**? Mesmo probe que o [[OFF26-4]] aguarda (§2 da sua
F1: **nada no código lê o estado pré-draft** hoje).

##### INDÍCIO FORTE — `is_keeper: false` na designação (02/08/2026, experimento manual)

> **Registrado como indício, NÃO como fato assentado.** A verificação definitiva é o que os picks
> expõem **pós-draft**, e isso **ainda não foi observado** — a liga fantasma está em estado de
> teste, com o draft não rodado.
>
> ⚠️ **PRÉ-CONDIÇÃO — atualizada em 02/08/2026 (MAN-OFF26-RUNBOOK-REG-PT2):** o board voltou a
> ficar **populado** (Team 3/4/5, dados de teste da 2ª execução do Cowork), então **existe alvo
> outra vez**. Mas confirmar este indício exige o estado **pós-draft**: é preciso **rodar um draft
> de teste sobre o board populado**, e fazê-lo **antes do próximo RESET DRAFT** (já pendente), que
> zeraria o alvo de novo **e trocaria o `draft_id`**. Pré-condição da diagnose, não passo interno
> dela. Identificadores da sala — e o aviso de que o **`draft_id` muda a cada reset** — no bloco do
> pacote OFF26 e na seção do [[OFF26-4]].

A operação interna disparada ao **designar keeper no board** carrega o campo **`is_keeper` com
valor `false`**: o Sleeper trata a designação como **pick forçado de leilão**, não como keeper.
**Indício corroborante:** a UI **toca o som de lance vencedor** ao designar.

**📈 Reforço de evidência (MAN-OFF26-4-PROBE / -REFINE-PT2, 03/08/2026):** o probe read-only leu as
**24 designações pré-draft pela API** e **todas trazem `is_keeper: false`**. O indício deixa de
apoiar-se só na operação interna observada na UI: **está no payload**. **Continua NÃO sendo a
confirmação definitiva** — essa é **pós-draft** e ficou **fora do escopo** do probe executado.

**Se o indício se confirmar pós-draft, a questão empírica acima já tem resposta:** o campo **não
serve de discriminador**, e o discriminador terá de vir da **keeper sheet do Manager como lista de
exclusão**. Isso **inclina** — sem decidir — a decisão em aberto abaixo para o ramo "Manager é
fonte única da verdade", porque o outro ramo (reconciliar os dois lados) pressupõe que o Sleeper
tenha algo próprio a dizer sobre quem é keeper. **Não arbitrar antes do probe pós-draft.**

**Escopo resumido:** registro apenas. Definir como o importador reconhece, no payload do draft
da liga fantasma, o que é arremate novo (contrato ano 1) e o que é keeper (contrato em
andamento, a **não** re-criar).

**✅ DECISÃO ARBITRADA PELO OWNER (06/08/2026, MAN-OFF26-10-SPEC): opção A — Manager é fonte
única da verdade.** No import pós-leilão, a **keeper sheet definitiva** (a reemitida pela urna,
U7 do [[OFF26-10]]) é **lista de exclusão**: o importador [[OFF26-3]] ingere **apenas os
arremates**. **Keeper encontrado nos picks é ignorado por definição** — a garantia de que o
board confere com a sheet é a **auditoria [[OFF26-4]], que roda ANTES do leilão**. **Sem
reconciliação pós-leilão** — o ramo "segunda auditoria" morre (pressupunha que o Sleeper tivesse
algo próprio a dizer sobre quem é keeper, e o indício `is_keeper:false` aponta que não tem).
A decisão está **fechada como decisão**; **nenhum código neste registro** — o discriminador é a
sheet, que o importador passa a **receber na F2 do item** (escopo separado, prompt próprio).

**Dependências:** depende do **[[OFF26-3]]** (✅ — é a porta que ingere) e da **keeper sheet
definitiva pós-urna** ([[OFF26-10]] U7). O probe pós-draft do `is_keeper` deixa de ser
**bloqueante da decisão** (já arbitrada) — permanece útil como confirmação na F2. Entra como
**etapa do [[OFF26-7]]** (import do resultado do auction). Toca `record_acquisition` **apenas na
leitura** (o que se decide ingerir), não na porta em si.

---

### OFF26-12 — Keeper em IR conta na reserva de $1 da 8.3.4?
🔲 **Pendente** — Prioridade **Baixa** — **decisão de REGRA DE LIGA, não de implementação**
(nasce da conferência aritmética do D2 em `MAN-OFF26-4-LABELS`, 03/08/2026)

**A conferência que originou o item já está feita e fechou o D2:** as contagens de slots
**coincidem** — regulamento **22** (8.3.4: *"completar as 22 posições do roster … (22 − número de
keepers)"*), sala **22** (`roster_positions` e `draft.settings.rounds`), Manager **22**
(`MAX_ROSTER`) — e a fórmula da reserva é a mesma nos três. **Isto aqui é o resíduo.**

**A pergunta que a regra não responde.** O item **1.3** diz que os **2 IR "não são considerados no
total de 22"**. A **8.3.4** manda reservar $1 para cada `(22 − número de keepers)` e **não diz se
keeper em IR entra em "keepers"**.

| leitura | reserva p/ time com 20 não-IR + 2 IR | quem faz assim hoje |
|---|---|---|
| **(a) IR conta como keeper** | $0 (roster cheio: 22) | **Manager e Sleeper** |
| **(b) IR não conta como keeper** | **$2** (faltam 2 p/ completar as 22) | leitura literal do 1.3 |

**Magnitude:** **até $2** por time com IR. Hoje **3 times** têm IR preenchido na liga real.

**Causa:** o Manager passa **todos os não-dropados** para `draft_budget`
(`cuts._team_fa_budget`; `draft_budget` filtra só `is_dropped`), e o Sleeper conta o keeper em IR
porque **ele é designado no board** e ocupa uma das 22 rodadas.

**Efeito prático sobre a auditoria [[OFF26-4]]: NENHUM — não é relevante para o veredito.** Os dois
lados que a auditoria compara **concordam entre si**; não há como isto virar divergência falsa nem
verdadeira no relatório. **É margem entre as plataformas e o regulamento**, não entre os lados
comparados. Por isso a prioridade é **Baixa** apesar de tocar dinheiro.

**Decisão em aberto (owner):** vale (a) ou (b)? Se **(b)**, o ajuste é descontar os jogadores em IR
do `num_keepers` — **mexe em `salary_engine.draft_budget`**, porta canônica consumida por 3 sites
(`cuts`, `draft_import`, `salary`), e **exigiria F1 própria**. Se **(a)**, basta registrar a
interpretação no regulamento para não reabrir.

**Não fazer nada é uma opção defensável:** a diferença é de até $2 num budget de $200, e o
enforcement real do teto é do **Sleeper**, que já faz (a).

---

### OFF26-13 — Time com mais de 22 keepers não cabe no board da fantasma
🔲 **Pendente** — Prioridade **Alta** — mesma conferência (`MAN-OFF26-4-LABELS`, 03/08/2026)

**O fato, medido ao vivo.** O regulamento permite **24 jogadores** (22 de roster + 2 IR que "não são
considerados no total de 22", item 1.3). O board da fantasma comporta **22 designações por time** —
`draft.settings.rounds = 22`, e **slot de IR não é slot de draft** (ver a correção de premissa
abaixo). **Um time está em 24 hoje**: 22 não-IR + 2 IR.

**Consequência, pelo achado do [[OFF26-4]]:** se um time chegar a 20/08 com mais de 22 keepers,
**os excedentes não cabem no board** — e keeper fora do board é **jogador leiloável**. Não é
inconveniência de transcrição: são **contratos vigentes expostos a serem arrematados ao vivo**.

**Por que é item próprio e não emenda:**
- **É segunda causa de time não populável**, distinta do teto de budget ([[OFF26-10]]) — e as duas
  se manifestam do mesmo jeito no relatório da auditoria (`não populado`), mas têm **remédios
  diferentes**.
- **NÃO se resolve com o late drop de 22/08:** o late drop é **1 jogador por time**, e o excedente
  aqui pode ser **2**.
- **Nada no regulamento obriga** um time a descer de 24 para 22 nos cortes de 20/08 — pelo 1.3,
  24 é uma composição **legal**.

**Decisão em aberto (owner):** corte adicional obrigatório para quem exceder 22 antes da
transcrição × exceção administrativa (ex.: o excedente entra depois, com o board já fechado) ×
outra. **Nenhuma delas é de implementação** — todas mudam o que se pede aos owners.

**O que o Manager já pode fazer sem decisão nenhuma:** a auditoria **calcula e mostra** o número de
keepers por time, então **quem vai estourar é pré-calculável** antes de 20/08, do mesmo jeito que o
[[OFF26-10]] pré-calcula os bloqueados pelo teto.

**Cross-refs:** [[OFF26-4]] (achado que dá a gravidade), [[OFF26-10]] (a outra causa de não
populável), [[OFF26-5]] (o runbook registra que board incompleto não é estado aceitável),
[[OFF26-2]] (a sheet é onde a contagem de keepers aparece).

#### Diagnose F1 (MAN-OFF26-13-F1, 03/08/2026 — read-only) — a ocupação dos 12 times

**Instantâneo**, não estado estável: as contagens mudam entre leituras (quatro leituras de owner num
único dia nesta sessão). Zero escrita: só `GET` na API e `sqlite mode=ro`.

##### ✅ T2 — A AMBIGUIDADE ESTÁ DISSOLVIDA: são 22 ativos + 2 IR, não 24 no ativo

**Prova de estrutura, não interpretação:** `roster.reserve` é **subconjunto** de `roster.players`
— verificado nos 3 rosters com IR (`reserve ⊆ players` = True nos três). Logo **`players` já
inclui os de IR**, e "24" nunca foi 24 no ativo.

**O time é o `🕯️🕯️ achane 🕯️🕯️`** (roster 10, owner `gabrieldiinis`): **24 total = 22 ativos + 2
em IR** (Michael Penix $1 e Travis Hunter $8). O `is_on_ir` do Manager **bate exatamente** com o
`reserve` do Sleeper nos 3 times — **não há divergência de marcação**.

> **O alarme "24 no ativo" era falso. O risco, não.** Ver T3.

##### T1 — Distribuição dos 12 (leitura ao vivo da liga real)

| time | roster | total | ativo | IR | designações | cabe em 22? |
|---|---|---|---|---|---|---|
| Pitbull do Samba | 1 | 22 | 22 | 0 | 22 | ✅ (folga 0) |
| 3 peat… of pain 🫠 | 2 | 22 | 22 | 0 | 22 | ✅ (folga 0) |
| Fazenda Pederasta | 3 | 22 | 20 | **2** | 22 | ✅ (folga 0) |
| mongoloides | 4 | 22 | 22 | 0 | 22 | ✅ (folga 0) |
| Cangaceiros da Colina | 5 | 18 | 18 | 0 | 18 | ✅ |
| Miller Time! | 6 | 22 | 22 | 0 | 22 | ✅ (folga 0) |
| AlexTheDawg | 7 | 18 | 18 | 0 | 18 | ✅ |
| Trust The Process | 8 | 21 | 21 | 0 | 21 | ✅ |
| Tropa do Bicampeonato 🏆 | 9 | 19 | 19 | 0 | 19 | ✅ |
| **🕯️🕯️ achane 🕯️🕯️** | **10** | **24** | **22** | **2** | **24** | ⛔ **NÃO (+2)** |
| rafaelferreirap | 11 | 17 | 16 | **1** | 17 | ✅ |
| ESPN FANTASY LEAGUE | 12 | 21 | 21 | 0 | 21 | ✅ |

##### T3 — Designações necessárias: **1 time não cabe, e 5 estão com folga ZERO**

Critério: **toda a posse vira designação** — o IR ocupa vaga de **banco** na sala (o D5 do
[[OFF26-2]] manda contar IR, e o achado do [[OFF26-4]] exige que **todo** keeper esteja no board).

- ⛔ **Excede: 1 time** — `achane`, **24 designações num board de 22 (+2)**.
- ⚠️ **Folga zero: 5 times** (Pitbull, 3 peat, Fazenda, mongoloides, Miller Time) — **qualquer
  aquisição antes de 20/08 os põe na mesma situação**. É o dado que a contagem "só 1 excede"
  esconde.
- **No agregado sobra espaço e isso não ajuda:** 248 designações necessárias para 264 vagas — o
  limite é **por time**, e agregado não compensa.

> **Base do limite (inferência declarada, não teste):** `draft.settings.rounds = 22` dá **22 picks
> por time**. **Não foi testado** se a UI recusa a 23ª designação — testar exigiria tocar o board,
> que está proibido. O limite é lido da estrutura do draft, não observado em comportamento.

##### ⛔ A HIPÓTESE CENTRAL DO ITEM ESTÁ REFUTADA: os cortes de 20/08 NÃO resolvem sozinhos

A suposição registrada era que "quem está acima do teto de roster tende a estar acima do cap
também". **Falso no único caso que existe:**

| time | jogadores | salário total | acima do cap $200? |
|---|---|---|---|
| **achane (o das 24)** | **24** | **$195** | ❌ **NÃO — está abaixo** |
| mongoloides | 22 | $206 | ✅ sim (mas cabe no board) |
| Tropa do Bicampeonato | 19 | $201 | ✅ sim (mas cabe no board) |

**Os dois times acima do cap cabem no board; o time que não cabe está abaixo do cap.** As duas
condições são **independentes**, e no instantâneo de hoje elas estão **anticorrelacionadas**.

> **Consequência direta:** **nada obriga o `achane` a cortar ninguém em 20/08.** Ele fecha a janela
> legal, sob o cap, com 24 — e **2 keepers dele ficam fora do board, expostos ao leilão**. A
> "provável resolução automática" não acontece.

##### T4 — O teto de 22 NÃO é validado em lugar nenhum do código

| constante | onde é definida | onde é **enforçada** |
|---|---|---|
| `MAX_IR = 2` | `models.py:10` (**1 lugar**) | **`routes/roster.py:155`** — bloqueia com 400 "IR cheio" |
| `MAX_ROSTER = 22` | `models.py:9` **e** `salary_engine.py:40` (**2 lugares**) | ⛔ **NENHUM** |

**`MAX_ROSTER` só é usado como divisor**, em `salary_engine.draft_budget:221`
(`empty_spots = max(0, 22 − num_keepers)`) — é aritmética de reserva, **não validação**. E o
`max(0, …)` faz o excedente **desaparecer em silêncio**: com 24 keepers o resultado é 0, idêntico a
um roster exatamente cheio. **Nada distingue "cheio" de "estourado".**

**Caminhos que colocam jogador num time — nenhum confere contagem:**
- `models.record_acquisition:379` (`player.team_id = team.id`) — porta canônica das 4 entradas do
  `/auction` + importador [[OFF26-3]]: **sem checagem**;
- `sync_sleeper.py:285,300,687` — **e aqui é correto não checar**: o Sleeper é autoridade de
  posse, e um roster de 24 **entra no Manager legitimamente**;
- **trades não movem jogador** (`routes/trades.py` é simulador puro — só grava `TradeProposal`);
- `routes/offseason.py:611,617` **não é caminho de jogador** (é `DraftLotteryResult`).

**Achado lateral:** `routes/salary.py:4` **importa `MAX_ROSTER` e nunca o usa** — import morto,
resíduo de uma validação que nunca existiu.

> **A assimetria é a resposta da T4:** o teto **menor e menos consequente** (IR = 2) é enforçado; o
> teto **maior, que hoje expõe keepers ao leilão** (roster = 22), **não é**. E não é bug: o Manager
> foi desenhado para **espelhar** a posse do Sleeper, não para arbitrá-la. **Registrado como
> achado — implementar validação é decisão do owner**, e teria de decidir antes o que fazer quando
> o Sleeper legitimamente entrega 24.

##### T5 — Réplicas: uma constante duplicada e duas contagens de salário coexistindo

1. **`MAX_ROSTER` definido duas vezes** (`models.py:9`, `salary_engine.py:40`) com o mesmo valor.
   `routes/salary.py` importa a de **models**; `draft_budget` usa a de **salary_engine**. Hoje é
   inócuo (mesmo valor, e a de models nem é usada), mas **duas fontes para um número de regra** é
   exatamente o que a invariante [[F10]] evita. **Não corrigido nesta diagnose.**
2. **Duas contagens de "salário usado" convivem, e divergem em times com IR:**
   - **exclui IR** — `models.Team.active_salary:99`, `routes/league.py:22,25`, `routes/admin.py:159`
     (cap bar, League Hub, preview de rollover);
   - **inclui IR** — `salary_engine.draft_budget` via `cuts._team_fa_budget` (budget de keeper,
     por decisão do **D5 do [[OFF26-2]]**).

   **Medido hoje:** divergem em **3 times**, total **$14** — `achane` **$186 × $195 (+$9)**,
   rafaelferreirap +$3, Fazenda +$2.

   > **Não é bug — são perguntas diferentes** ("quanto do cap está comprometido em jogadores que
   > pontuam" × "quanto do cap está comprometido no total"). **É risco de leitura:** o mesmo time
   > exibe **$186 numa tela e $195 noutra**, sem nada explicando a diferença. Sob prazo, em 20/08,
   > é convite a achar que uma das duas está errada. **Registrado, não alterado.**
3. **Tratamento de IR não tem réplica de decisão** — `is_on_ir` é lido em ~15 sites, mas todos
   apenas **filtram/exibem**; a única escrita com regra é o `toggle_ir`, e o sync espelha o Sleeper.

##### Refutação de premissas (MAN-METH-REG)

**(a) Premissas deste prompt contraditas pelo observado:**
1. ⛔ **"O board da fantasma não tem slot de IR."** Já derrubada nesta sessão e **repetida no
   prompt**: `settings.reserve_slots = 2` **nas duas ligas**. **A conclusão do prompt continua
   correta** (24 designações num board de 22), mas **pelo motivo certo**: não é ausência de IR na
   sala — é que **slot de IR não é slot de draft** (o draft tem 22 rodadas). Quinta ocorrência da
   mesma família: observação verdadeira, procedência errada.
2. ⛔ **"A janela de 20/08 provavelmente resolve sozinha, já que quem excede o roster tende a
   exceder o cap."** **Refutado com o dado:** o time das 24 está em **$195, abaixo do cap**; os dois
   times acima do cap **cabem no board**. Anticorrelacionado, não correlacionado.
3. ⚠️ **"Um time em 23 importa tanto quanto um em 24."** Correto — e **não há nenhum em 23**. O que
   o prompt não previu é que **5 times estão em 22 exatos**, que é a mesma fragilidade **sem
   aparecer em contagem nenhuma de excedente**.

**(b) Comportamentos presentes que o prompt não previu:**
1. **`max(0, …)` no `draft_budget` apaga o excedente**: 24 keepers produzem `empty_spots = 0`,
   **indistinguível** de roster exatamente cheio — o Manager **não tem como saber** que estourou,
   nem para avisar.
2. **`MAX_ROSTER` é importado e não usado** em `routes/salary.py` — sinal de validação planejada e
   nunca escrita.
3. **O teto de IR É enforçado** (`MAX_IR`), o de roster não — a assimetria não estava no
   enquadramento.
4. **A marcação de IR do Manager bate 100% com a do Sleeper** hoje (3 times, 5 jogadores) — o
   pressuposto de que a contagem local pudesse estar defasada **não se confirmou**.

##### O que esta diagnose NÃO faz

Não corrige dado, não corta jogador, não implementa validação, não altera cálculo e **não muda o
status do item**. As duas decisões seguem do owner: **(1)** o que fazer com quem chegar em 20/08
acima de 22 (corte adicional obrigatório × exceção administrativa), e **(2)** se o Manager passa a
**avisar** — o que é barato, já que a auditoria [[OFF26-4]] **já conta keepers por time** e poderia
sinalizar antes de 20/08, sem depender da decisão (1).

---

### F9 — `bulk_register` cria jogadores sem SalaryHistory
⚠️ **Parcial** — Prioridade **Alta** — achado lateral de [[MAN-OFF26-3-F1]] (registrado 05/06/2026)

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

**Corroboração ao vivo (12/06/2026, forense do F11):** queries read-only no **banco vivo**
(`/data/dynasty.db`, Render Shell, executadas pelo owner) re-confirmaram `salary_history` = **0
linhas** — a F1B auditara uma **cópia** de 07/06; agora confirmado no disco vivo. Tradução:
**nenhuma aquisição jamais passou pela porta canônica `record_acquisition` em produção** (contratos
vivos = CSV bootstrap + sync). **Eleva a urgência do F9 antes da FA auction 2026:** a auction será
o primeiro uso real do `/auction` em prod e `bulk_register` é a única porta que ainda escreve
inline — fechar o F9 antes garante que o primeiro rastro de aquisição da liga nasça pela porta
única.

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

#### Fase 2 ⚠️ localhost (16/06/2026) — MAN-F9 (refatoração, sem backfill)

`bulk_register` (`routes/auction.py`) deixou de criar contrato inline e passou a consumir a
porta canônica `record_acquisition` — mesma das outras 3 entradas do `/auction`. Cada item
agora gera **Player + SalaryHistory + AuctionLog** atômicos (antes: só Player + AuctionLog,
sem SalaryHistory). Salário nasce de `year1_salary("auction_draft", value_paid, …)` — que é
exatamente o `max(1, int(value_paid))` que o bloco inline calculava, logo **valor inalterado**.

- **Idempotência (nova):** `event_ref = f"bulk:{season}:{team_name}:{player_name}"` + guarda
  `acquisition_already_recorded(ev_ref)` antes de gravar (padrão do importador OFF26-3). O
  inline antigo **não** era idempotente — re-rodar duplicava AuctionLog. Agora a 2ª execução
  não cria nada.
- **Bloco vestigial removido:** classe `_noop` + `test_request_context()`/`app_context()` no-op.
  `grep _noop|test_request_context|app_context|set_espn_value` em `auction.py` → zero.
- **Contrato da rota estável:** resposta segue `{registered, results, errors}`.

**Validação localhost (smoke contra DB temp, test client com admin seedado):**
- BEFORE (0 SH, 0 AL) → RUN1 registra 2 → **(2 SH, 2 AL)**; `registered=2`, salaries `[7, 3]`.
- Paridade: `year1_salary("auction_draft", 7)=7`, `(3)=3` — igual ao gravado.
- RUN2 (mesmas entradas) → `registered=0`, counts **(2, 2)** inalterado (idempotência).
- `salary_engine_test.py` → 48/48.

**Critério de ✅:** smoke em produção (registrar via `/auction` em massa e conferir SalaryHistory).
**Sem push** — gatilho de deploy fica com o owner.

---


### M21 — Busca cobre o universo Sleeper (FAs da liga + não-rosterados)
🔲 **FATIA A ✅ CONCLUÍDA 10/08/2026 (MAN-M21-A → MAN-ARC-BUSCA-DONE; PROC1 cumprido — hash
`20b346b` live, smoke do owner com Kamara/Waller/Detroit); o item segue 🔲 pela fatia B
(Média, pós-intertemporada — F1b não iniciada)** — Registrado 10/08/2026 (MAN-M21-REG); F1a
no mesmo dia (MAN-M21-F1a), recomendação (a) decidida pelo owner

**Pedido do owner (10/08/2026, logo após o smoke do [[M10]]):** a busca deve encontrar **qualquer
jogador do universo Sleeper**, não só os que estão em roster. Dois casos concretos expuseram o gap,
e eles são **de naturezas diferentes** — daí o item nascer partido em duas fatias, com prioridade e
prazo próprios:

| Caso-âncora | Existe como `Player`? | Por que some da busca | Fatia |
|---|---|---|---|
| **Alvin Kamara** — FA da liga (âncora consagrado no fechamento da fatia; o registro original citava Gunnar Helm — ver correção abaixo) | **Sim** (contrato histórico no DB; `/player/<id>` funciona) | O filtro `is_dropped=False` do M10 o excluía — **resolvido pela fatia A** | **A ✅** |
| **Rookies não-drafteados** (classe 2026) e demais não-`Player` — **incluindo o caso Gunnar Helm** | **Não** | Não são linha da tabela `Player`; vivem no `RookieEspnValue` e no pool do Sleeper | **B** |

**Correção do caso Helm (medição do owner, Render Shell, 10/08/2026):** o Gunnar Helm **nunca foi
`Player`** — zero linhas em `players` (`%Helm%`), **zero menções em `player_history`** (nem em
notes) e **zero históricos órfãos** no banco vivo. A lembrança do owner ("existia com contrato
histórico") é de **outra superfície**, não do DB do Manager. O caso migra da fatia A para a
**fatia B**: encontrar o Helm é encontrar um **não-`Player`** do pool. **Achado positivo que fica
como evidência: a integridade do `player_history` está intacta (órfãos = 0, conferido em prod)** —
diagnoses futuras não precisam remedir. A medição completa: **41 dropados** em prod (Kamara $13
com `is_on_ir` stale, Waller sem `nfl_team`, Detroit Lions DEF entre eles).

**Mecanismo do sumiço na fatia A (fato de código, não hipótese):** o sync marca
`is_dropped=True` para jogador que está num time do DB mas **não** no roster do Sleeper daquele
time (`sync_sleeper.py:321-324`) — que é exatamente o estado de um FA da liga. O endpoint
`/api/player/search` filtra `Player.is_dropped == False`, então o jogador continua **existindo e
navegável** (a página de perfil abre por `id`), mas **não é alcançável pela busca**. ⚠️ Nenhuma
medição de produção foi feita neste registro: o `dynasty.db` do git é **seed, não produção** (nele,
37 de 281 Players estão dropados — ordem de grandeza, não o número de prod).

**Por que as duas fatias não são o mesmo item, e por que também não são dois itens:** a fatia A é
**um predicado de query** sobre dados que já existem; a fatia B é **uma decisão de arquitetura de
dados** que pode mudar o significado da tabela `Player`. Compartilham a superfície (a mesma busca,
a mesma lista de resultados, a mesma regra de identidade) — por isso um ID só —, mas ⛔ **a fatia A
não deve esperar a B**, e a B não deve ser resolvida "de carona" na A.

#### Fatia A — FAs da liga na busca (Alta, alvo pré-24/08)

##### F2a — entregue (MAN-M21-A, 10/08/2026; decisão do owner: opção (a) da F1a)

**Medição de produção que precedeu a decisão (owner, Render Shell, 10/08):** **41 dropados** no
banco vivo, incluindo **Alvin Kamara** (RB, $13, `is_on_ir=1` stale), **Darren Waller** (TE,
`nfl_team` vazio) e **Detroit Lions** (DEF, sid sigla). O caso-âncora original (Gunnar Helm)
**não existe em prod** — a investigação fechou no fechamento da fatia (ver correção no topo da
seção): **Helm nunca foi `Player`**, o caso é da fatia B. **O âncora da fatia A é Kamara.** Os
três casos existem também no seed, e foram o material do smoke local.

**O que entrou:**
- **Busca inclui FAs, marcados.** O filtro `is_dropped=False` caiu do endpoint (a F1a provou que
  era inércia da v1.0, sem consumidor a proteger). O payload `to_search_dict()` ganhou
  **`is_dropped`** (+1 campo — o custo previsto), e o `optionInner` da engrenagem única troca a
  franquia pelo **badge "FA"** quando dropado — nos **dois consumidores de graça**, sem fork. O
  badge substitui (não acompanha) a franquia: `fantasy_team_name` de dropado devolve o último time,
  e exibi-lo leria como posse atual.
- **Ordenação adotada (a opção da Q4):** `(prefixo, is_dropped, nome)` — rosterado antes de FA a
  empate de relevância. Mantém o pico pós-20/08 legível dentro do teto de 20.
- **Perfil de FA — os dois "enganosos" da Q2 corrigidos:** `can_propose_trade` agora exige
  `not player.is_dropped` (propor trade de jogador sem dono não tem significado; o `team_id`
  preservado pelo sync é histórico, não posse) e o rótulo do salário vira **"Último salário
  (histórico)"** quando dropado ("atual" prometia vigência de um número que não conta em folha
  nenhuma).
- **Carona do achado menor (coube trivial):** a tag **IR não renderiza para dropado**
  (`is_on_ir and not is_dropped` no template) — o campo fica stale porque o sync só reescreve quem
  está em roster; **o sync não foi tocado**, como a régua do prompt pedia.
- **Autocomplete da calculadora:** FA é selecionável e preenche os 3 campos (o uso pré-auction da
  F1a); o hint exibe "FA" e **"último salário"** no lugar de "salário atual".

**Smoke de PRODUÇÃO aprovado (owner, 10/08/2026, hash `20b346b` — fecha a fatia):** Kamara com
badge FA na busca → perfil com tag "Dropado", **rótulo "Último salário (histórico)"**, **sem**
botão de trade e **sem** tag IR (o stale suprimido); Waller e Detroit Lions sem quebra; rosterado
sem regressão; autocomplete com FA + hint. A fatia A está **✅**; o que resta do M21 é a fatia B.

**Guardas respeitadas:** sync/schema/salary_engine/folha intocados (a fatia **consome** o estado
`is_dropped`, não o redefine); fatia B e a arbitragem importar×federar não tocadas; identidade
segue por `sleeper_player_id` — badge é exibição; engrenagem única preservada (zero fork).

**Testes: `player_search_test.py` 27 → 35.** Os testes de exclusão de dropado viraram testes de
**inclusão marcada**; novos: flag no payload, homônimo rosterado×FA com o rosterado primeiro,
alfabética por bloco, e 6 guardas estáticas (badge substitui franquia, filtro não volta, botão de
trade checa dropado, rótulo histórico presente com o "atual" preservado, tag IR suprimida, hint da
calculadora). Suítes completas verdes (54 + 34 + 25 + 36 + 64 + 22 + 14 + 19 + 35).

**Smoke local (GET-only, cópia do seed — que contém os 3 casos de prod):** Kamara → aparece
`is_dropped=true`, perfil **sem** botão de trade, **com** "Último salário (histórico)", **sem** tag
IR (apesar de `is_on_ir=1` no banco); Waller → renderiza com `nfl_team` vazio (`—`); Detroit Lions
→ DEF dropada com sid sigla, sem erro; DJ Moore → **idêntico ao de antes** (busca sem badge, perfil
com botão de trade e "Salário atual"); mistura "con" → Falcons e McConkey (rosterados) antes de
James Conner (FA). ⚠️ **Não exercido:** interação em navegador (smoke do owner) e o pico real de
40+ FAs pós-20/08 (o comportamento sob pico está coberto por ordenação + teto, não por observação).



**Objetivo declarado:** jogador dropado que **já é `Player`** aparece na busca, **distinguível** de
quem está em roster.

**Valor operacional e prazo:** a **FA auction é 24/08** — consultar contrato/histórico de um FA é
parte da preparação do leilão, e hoje exige saber o `id` e digitar a URL. É a única razão de a
fatia A ser **Alta**; ela **não** está no caminho crítico de nenhum mecanismo (nada bloqueia se
não entrar).

**Questões abertas para a F1a (⛔ registrar, não responder aqui):**
1. **Por que o filtro `is_dropped=False` existe?** Ele veio do endpoint **pré-M10** (a busca o
   herdou junto com a assinatura, sem revisitar). As hipóteses a distinguir: (a) evitar poluir a
   busca padrão com quem saiu da liga; (b) evitar que um FA chegue a superfícies que pressupõem
   dono (o "Propor Trade" do perfil é a suspeita óbvia); (c) nenhuma razão viva — inércia. **A
   resposta condiciona o desenho**: incluir **marcado** ("FA") × incluir **sem distinção** ×
   **toggle**/filtro explícito. ⛔ Não arbitrar antes de responder.
2. **O que o perfil de um FA exibe/oferece que precisa de ajuste?** Concretamente o botão
   "⇄ Propor Trade" ([[M13]]/[[M14]]) — propor trade de jogador sem dono não tem significado. A F1a
   verifica **o que a página faz hoje** com um `Player` dropado antes de propor mudança.
3. **Staleness herdada do [[UX11]]:** um FA **mantém o último time NFL sincronizado** (o sync só
   sobrescreve `nfl_team` com valor truthy). Se a busca passa a listar FAs com time NFL, ela passa
   a exibir esse dado velho com mais frequência — a F1a decide se isso pede rótulo, e ⛔ **sem
   reabrir a decisão do UX11**.
4. **Outras superfícies que consomem o mesmo endpoint** (hoje: barra global e autocomplete da
   calculadora). Um FA faz sentido na calculadora? A F1a responde por consumidor, não em bloco.

#### F1a — diagnose read-only da fatia A (MAN-M21-F1a, 10/08/2026)

Toda evidência é do código no HEAD (`13c9c8c`) e do histórico git; **zero mutação, zero chamada
externa, zero query em produção** (a régua do prompt). O item segue **🔲** — a decisão de desenho
é do owner.

##### Q1 — Arqueologia do filtro: ele nunca protegeu fluxo nenhum

**O endpoint nasceu MORTO na v1.0, já com o filtro dentro.** `GET /api/player/search` existe desde
`f2271ba` (tag `manager-v1.0`) com `Player.is_dropped == False` no corpo — e uma busca por
`player/search` em **todos os commits** de `templates/` e `static/` (`git log --all -S`) encontra
**uma única referência: o próprio M10** (`5e3c403`). Entre a v1.0 e o M10 o endpoint não teve
**nenhum consumidor**; o M10 o adotou herdando a assinatura, como o registro suspeitava.

**Consequência que reordena a fatia:** das 3 hipóteses do registro, (a) "evitar poluir a busca
padrão" e (b) "evitar Propor Trade com FA" **caem por anacronismo** — quando o filtro foi escrito
não existia busca para poluir nem fluxo para proteger. Sobra a **(c) inércia/scaffolding**. Não há
fluxo legado a preservar: **a decisão de incluir FAs é uma decisão só sobre os 2 consumidores do
M10**, sem restrição herdada. Nada quebra se o filtro cair ou virar condicional — os demais sítios
com `is_dropped=False` (roster, league, cuts, urna…) têm **queries próprias** e não passam pelo
endpoint de busca.

##### Q2 — O perfil de um FA, campo a campo

O ponto de partida que o registro não citou: **o perfil já trata o caso pela metade** — a tag
**"Dropado"** existe no header desde o M13 (`player_detail.html:35`), porque o sync **preserva
`team_id`/`fantasy_team` ao dropar** (só liga o flag, `sync_sleeper.py:324`) e o bloco do time
renderiza com a última franquia.

| Campo | O que exibe para um FA hoje | Veredicto |
|---|---|---|
| Franquia no header | **Última franquia** (link p/ `/team/<id>`) + tag **"Dropado"** já existente | **Correto como está** — o par franquia+tag lê naturalmente como "último time" |
| Botão "⇄ Propor Trade" | **Aparece** para FA de outro time — `can_propose_trade` (`routes/roster.py:414-418`) checa `team is not None` e `team_id != meu`, **não checa `is_dropped`** | **Enganoso** — propor trade de jogador sem dono não tem significado; e é inconsistente (FA cujo último time é o meu esconde o botão) |
| "Salário atual" | O salário do **último contrato** — que não conta em folha nenhuma (`roster_salary` filtra `is_dropped`) | **Enganoso pela label** — o número é histórico; "atual" promete vigência |
| "Contrato Ano X/4" | Idem — estado congelado no drop | **Precisa badge-contexto** (histórico, não vigente) |
| Início do contrato · Aquisição · ESPN ref · Dynasty value | Fatos históricos/de mercado | **Corretos como estão** |
| `🏈 nfl_team` | Último time NFL sincronizado | **Correto com a ressalva conhecida** ([[UX11]] — sem tratamento novo) |
| Tag "IR" | `is_on_ir` **stale**: o sync só reescreve o campo de quem está em roster (`sync_sleeper.py:290`) — um dropado que estava no IR mantém a tag | **Precisa limpeza/contexto** (menor; IR de FA não significa nada) |
| Timeline | `PlayerHistory` completo | **Correto** — é histórica por natureza |
| Depth chart (O2) | Pool por sid; FA real da NFL sem time → sem card, sem erro | **Correto** (degradação já coberta) |

##### Q3 — Desenho da inclusão: recomendação (a), incluir sempre com badge

| Opção | Custo na busca global | Custo na calculadora | Parecer |
|---|---|---|---|
| **(a) incluir marcado** ✅ | 1 condicional no `optionInner` + **1 campo novo no payload** (`to_search_dict()` **não expõe `is_dropped`** hoje) — e a sub-linha do FA deve mostrar **"FA"** no lugar da franquia, senão ele **parece rosterado** (`fantasy_team_name` devolve a última franquia) | O mesmo badge no hint. **FA selecionável FAZ sentido**: a calculadora é simulador, e projetar o contrato de um alvo da auction é exatamente o uso pré-24/08 | Único desenho que atende o caso-âncora **e** não mente na lista |
| (b) sem distinção | Zero código a mais — e dano real: a lista exibiria a **franquia antiga como se fosse dono atual** | Idem | Recria no resultado da busca o problema que a tag "Dropado" já resolve no perfil |
| (c) toggle | Maior custo (estado de UI × 3 instâncias) | Idem | **Mata o caso-âncora por default**: quem procura o Helm não sabe que precisa ligar o toggle |

**Opção de ordenação para a F2a (registrar, não decidir):** rosterados antes de FAs dentro do
mesmo grupo de prefixo — 1 `case` a mais no `order_by`, endereça o pico da Q4.

##### Q4 — Interseção com o calendário 17→24/08

- **O pico é real e chega de uma vez:** os cortes de 20/08 acontecem **no Sleeper** e viram
  `is_dropped=True` **no sync seguinte** (a fotografia do OFF26-1) — dezenas de FAs novos entre
  20 e 22/08. Comportamento da busca: o **teto de 20 por query segue válido** (busca é por
  substring digitada, não listagem); o risco é FA acima de rosterado na ordem alfabética, mitigado
  pelo badge (a) e/ou pela ordenação opcional acima.
- **Urna ([[OFF26-10]]): zero interseção.** A urna monta a lista do próprio roster com query
  própria (`late_drop.py:153`) e valida o bilhete recusando dropado (`late_drop.py:176`) — a busca
  não alimenta nem contorna nada do caminho selado.
- **Preparação da auction: é o ganho, não o conflito.** Procurar um cortado e abrir o contrato
  histórico entre 20 e 24/08 é exatamente o valor operacional que fez a fatia ser Alta. E o mundo
  já trata dropado como entidade recomprável: o importador tem o fluxo **"Reativar (ano 1)"**
  (`draft_import.py:64-69`) — incluí-los na busca é coerente, não novidade conceitual.

##### Q5 — Medição em produção (query pronta; ⛔ NÃO executada nesta sessão)

No Render Shell, contra o banco **VIVO** (`/data/dynasty.db`, nunca o seed) — dois SELECTs
read-only:

```bash
sqlite3 /data/dynasty.db "SELECT COUNT(*) AS dropados FROM players WHERE is_dropped=1;"
sqlite3 /data/dynasty.db "SELECT id, name, position, nfl_team, fantasy_team, salary,
  contract_year, is_dropped FROM players WHERE name LIKE '%Helm%';"
```

Nota que reforça a régua "seed ≠ produção": **o seed local não contém Gunnar Helm** (conferido —
zero linhas). O caso-âncora só existe no banco vivo, criado por sync; a medição é do owner.

##### Listas da regra MAN-METH-REG

**(a) Premissas do registro que o código contradiz:**
1. O registro deixou 3 hipóteses vivas para a origem do filtro; a arqueologia **decide**: o filtro
   nasceu na v1.0 dentro de um endpoint **sem nenhum consumidor** — as hipóteses (a) e (b) caem
   por anacronismo, resta (c) inércia. Não há fluxo protegido.
2. O registro tratou "o que o perfil de um FA oferece" como campo aberto homogêneo — o código
   mostra **tratamento parcial existente** (tag "Dropado" no header desde o M13).

**(b) Comportamentos existentes que o escopo do registro omite:**
1. **O drop preserva `team_id`/`fantasy_team`** — na lista de busca um FA **pareceria rosterado**
   pela última franquia; o registro só citou o staleness de `nfl_team` (UX11). É o argumento
   decisivo contra a opção (b).
2. `to_search_dict()` **não expõe `is_dropped`** — qualquer desenho com badge exige +1 campo no
   payload (pequeno, mas é mudança de payload que o registro não previu).
3. `is_on_ir` **stale em dropados** (o sync só reescreve o campo de quem está em roster) — tag IR
   pode sobrar num FA no perfil.
4. O fluxo **"Reativar (ano 1)"** do importador já trata dropados como entidades de 1ª classe —
   precedente de coerência a favor da inclusão.

#### Fatia B — universo não-`Player` (Média, pós-intertemporada; F1b concluída 10/08/2026)

**Objetivo declarado (delimitado pelo owner na F1b):** qualquer jogador do universo Sleeper é
encontrável na busca, com o estado **"Disponível"** marcado e o **valor de referência na linha**
quando houver — mostrar e marcar; sem contrato, sem simulação. Decisão implementar × adiar é do
owner, posterior à diagnose.

**Caso-âncora herdado da fatia A (correção de 10/08):** **Gunnar Helm** — o jogador que o owner
procurou no smoke do M10. A medição no Shell provou que ele **nunca foi `Player`** (zero em
`players`, `player_history` e órfãos); encontrá-lo é exatamente o problema desta fatia.

##### F1b — diagnose read-only da fatia B (MAN-M21-F1b, 10/08/2026)

Produto delimitado pelo owner antes da diagnose: **preparação da FA auction** — encontrar
qualquer jogador do universo Sleeper, ver que está **disponível** e, quando houver, o **valor de
referência na linha**. Mostrar e marcar; sem contrato, sem simulação. Evidência do HEAD
(`500c089`) e do cache/seed locais; **zero mutação, zero chamada externa**. Números de tabela são
do **seed** (ordem de grandeza — conferíveis em prod pelo Shell). A decisão implementar × adiar
é do owner; a fatia segue **🔲**.

###### Q1 — A premissa "os rookies já estão no nosso sistema": meia-verdade com prazo de validade

| Fonte local de não-`Player` | Cobertura (seed) | Chave | Valor | Frescor |
|---|---|---|---|---|
| **`RookieEspnValue`** | **296 linhas** (2026): **287 `in_class`** (a classe capturada via DP3) + 9 fora da classe | `sleeper_player_id` + season (UNIQUE) | `espn_raw`/`espn_adjusted` — **só 15/296 têm valor > 0** hoje; o resto é membership a $1 (valor chega com o import ESPN da temporada) | ⚠️ **TRANSITÓRIO**: `clear_rookie_espn_store()` apaga TUDO quando o admin marca o **passo 5** ("Rookie Draft Done", `offseason.py:733-734`) |
| **`EspnValueStore`** (canônico E4-c) | **277 linhas** (2026) — **só rosterados** (o achado [[DP1]] confirmado por contagem) | `(sleeper_id, season)` | ESPN raw+adjusted | Persistente; escrito pelo confirm do import ESPN |
| **Pool do Sleeper** (cache F13) | ~12.2k entradas | `sid` | **Nenhum valor de mercado** — identidade/contexto (nome, posição, time, `birth_date`, depth chart) | TTL 168h, stale-while-usable ([[O2]]) |
| Board DP1 do cap_projector | Não é fonte própria — **lê** `RookieEspnValue.in_class` menos rosterados | — | — | Herda o transitório |
| `keeper_audit_fixtures` | ⛔ Material de teste congelado — **não é fonte** | — | — | — |

**A meia-verdade:** a **membership** da classe está local (287 sids), mas o **valor** quase não
está (15/296) e a fonte inteira **evapora no passo 5**. Detalhe que redime parte da premissa: o
store também guarda **veteranos não-rosterados do Top-300** (`in_class=False` com valor — caso
real no seed: Calvin Ridley) — o import ESPN já resolve not_found contra o pool e upserta lá
(`admin.py:_resolve_not_found_to_store`).

###### Q2 — Importar × federar: o mapa de consumidores decide sozinho

Efeito de ~12 mil linhas sem contrato na tabela `Player`, consumidor a consumidor:

| Consumidor | Efeito de importar o pool |
|---|---|
| `salary_engine`/folha ([[OFF26-16]]) | Neutro **se** toda linha nascer com `team_id=NULL` — as somas filtram por time. Risco residual em queries `filter_by(is_dropped=False)` sem filtro de time (`admin.py:17` conta "players", `offseason.py:686` roda rollover em **todos**) — **o rollover incrementaria contrato de 12 mil fantasmas** |
| **Import ESPN (3-tier matching)** | **QUEBRA ESTRUTURAL**: com o pool inteiro como Player, todo not_found passa a casar — o fluxo not_found → `RookieEspnValue` (E2/E5) morre por vacuidade |
| **`player_lookup` (Brown-safe)** | Homônimos multiplicam por ~40× o espaço de colisão — o matching estrito passaria a devolver ambiguidade onde hoje resolve |
| `needs_review`/M2 | Sync/criação marcaria **12 mil linhas para revisão** — a tela M2 morre |
| Sync (drop logic) | Neutro (itera só sids atribuídos a times) — mas o pool importado precisaria de manutenção própria (quem atualiza 12k linhas?) |
| Keeper exclusion/sheet ([[OFF26-11]]) | Neutro (partem do roster vivo) |
| Portas do `/auction` + `record_acquisition` | Matching por nome contra a tabela inteira — mesma explosão de homônimos |

**Recomendação: FEDERAR.** O custo real é pequeno e está medido: o `nfl_context` já monta o
índice enxuto do pool **com `full_name` dentro** (`_SLIM_FIELDS`, `nfl_context.py:37`) e
invalidação por `(mtime, size)`; falta (1) uma função de busca por nome sobre esse índice —
normalização de caso/acento já existe em `player_lookup._normalize`, reusável por import — e
(2) a fusão por sid com o resultado do DB no endpoint. Importar exigiria neutralizar
**cada linha** da tabela acima; federar não toca nenhuma. O precedente O2 (ler sem persistir) já
é o padrão da casa. **Decisão é do owner.**

###### Q3 — "Disponível" mora numa consulta única por request

O predicado é da liga: pool-sid ∉ sids de `Player`. **Uma query por request** (não por tecla — o
debounce do M10 já limita): `SELECT sleeper_player_id, is_dropped FROM players` (~280 linhas) vira
um dict em memória; a fusão suprime do resultado-pool quem já é Player (o DB é a linha dele) e
marca o resto **"Disponível"**. Os três estados na engrenagem única: o `optionInner` já bifurca
por `is_dropped` — vira um `switch` de 3 casos sobre um campo `origin`/badge no payload
(rosterado = franquia · FA da liga = badge "FA" · pool = badge "Disponível"). **Comporta sem
fork** — é a mesma extensão que o M21-A fez.

###### Q4 — Valor de referência na linha, por classe (sem fonte nova)

| Classe | Valor exibível | Fonte |
|---|---|---|
| Rookie da classe (287) | `espn_adjusted` quando > 0 (**15 hoje**; mais após o import ESPN da temporada); resto **sem valor** (massa $1 do board) | `RookieEspnValue` |
| Veterano fora da liga que veio no Top-300 | `espn_adjusted` (caso Ridley) | `RookieEspnValue` (`in_class=False`) |
| Veterano fora da liga fora do Top-300 (**caso Gunnar Helm**) | **Sem valor — e está correto assim** | Nenhuma (o canônico só tem rosterados — DP1) |

⚠️ **O prazo de validade contamina a Q4 inteira:** o clear do passo 5 roda **entre 17/08 (draft)
e 24/08 (auction)** — se o admin marcar "Rookie Draft Done" antes da auction, a camada de valor
da busca **evapora exatamente na semana do caso de uso**. Qualquer implementação precisa decidir
isso ANTES (adiar o clear × aceitar linhas sem valor × outra) — registrado como pendência de
desenho, ⛔ não arbitrado aqui.

###### Q5 — Destino do clique: sem navegação no corte mínimo

| Opção | Custo | Parecer |
|---|---|---|
| **(a) Sem clique** (linha informativa) ✅ p/ MVP | Zero — nenhuma rota/página nova | O produto delimitado ("ver que está disponível + valor") **é a própria linha**; navegação não acrescenta nada ao caso de uso |
| (b) Perfil reduzido do pool (`/pool/<sid>`) | Rota + template novos; o conteúdo (idade, depth chart) o `nfl_context` já monta por sid | Reusa muito, mas **cria superfície nova** para manter — e sem contrato/timeline, a página é o card do O2 solto. Fica como evolução SE o uso pedir |
| (c) Deep-link externo (Sleeper) | Baixo | Fora do produto; dependência de URL de terceiro |

Nota de mecânica: pool rows **não têm `Player.id`** — o modo navegação do componente exige
`origin` no payload antes de qualquer clique (hoje o href é `/player/${p.id}`; um pool-hit com
`id` ausente montaria link quebrado — a implementação DEVE tratar, qualquer que seja a opção).

###### Q6 — Fronteiras

**(a) Corte mínimo viável pré-24/08 (nomeado: "busca federada informativa"):** função de busca
por nome no índice do pool (normalização reusada) + fusão por sid com dedupe + badge
"Disponível" + valor do `RookieEspnValue` quando existir + **linha sem clique**. **Fora dele,
explicitamente:** navegação/perfil de pool (Q5b), valores de veterano fora do Top-300, qualquer
persistência, integração com calculadora/cap projector, resolução do timing do clear (pendência
de desenho que o corte precisa DECIDIR mas não resolve por código novo além de um `if`).
**Pré-requisito operacional do corte:** valor de rookie na linha só existe se o import ESPN da
temporada tiver rodado E o passo 5 não tiver sido marcado.

**(b) Fronteira com o redesenho do cap projector (item do owner, a registrar à parte):** a fatia
B **não produz modelo de dado novo** — consome pool + store existentes em leitura. O redesenho
(trades/rookies/drops/auction) pode nascer sem pressupor nada daqui, e nada daqui bloqueia o
redesenho; o único ponto de contato é o `RookieEspnValue`, que ambos leem e **nenhum dos dois
passa a possuir** (o dono segue sendo o ciclo E2/DP3). ⛔ Se o redesenho decidir mexer no timing
do clear, a pendência da Q4 é dele também — registrar o cross-ref quando o item nascer.

###### Listas da regra MAN-METH-REG

**(a) Premissas do pedido que o código contradiz:**
1. **"Os rookies já estão no nosso sistema"** — a membership sim (287), o **valor quase não**
   (15/296) e a fonte é **transitória** (clear no passo 5). Tratar o store como fonte permanente
   da busca seria construir sobre areia — parecer: federar tratando valor como **opcional por
   linha**, nunca como garantido.
2. Premissa implícita "veterano relevante tem valor em algum lugar" — só se veio no Top-300
   (`in_class=False` com valor); o canônico `EspnValueStore` tem **só rosterados** (277,
   contagem bate com o achado DP1). Fora disso, linha sem valor é o estado **correto**.

**(b) Comportamentos existentes que o escopo omite:**
1. ⚠️ **O clear do passo 5 (o maior achado da diagnose):** `clear_rookie_espn_store()` roda no
   toggle "Rookie Draft Done" — **entre o draft (17/08) e a auction (24/08)**. A camada de valor
   que o produto pede pode evaporar na semana do caso de uso. Parecer: pendência de desenho a
   decidir antes de implementar.
2. **Pool rows não têm `Player.id`** — o href do modo navegação quebraria; qualquer corte precisa
   do campo `origin` no payload (parecer: parte do corte mínimo).
3. O import ESPN já upserta **veteranos não-rosterados** no store (o caso Ridley) — a busca ganha
   valor de veterano "de graça" onde o Top-300 alcança; o escopo falava só de rookies.
4. `is_entering_class_member` (critério único da captura DP3) já define "quem é entrante" — a
   fatia B **reusa** a membership capturada, ⛔ sem segunda definição (a guarda do registro vale).

**Questões abertas para a F1b (⛔ registrar, não responder aqui):**

1. **A arbitragem central: importar o pool como `Player` × busca federada em duas fontes.** A
   hipótese do owner — *"deveriam estar na nossa base"* — é **premissa a testar, não spec**. A F1b
   deve mapear **os consumidores da tabela `Player`** e o que ~12 mil linhas sem contrato fariam
   com cada um: `salary_engine`/folha ([[OFF26-16]] — a régua soma o que não é `is_dropped`),
   `keeper_exclusion` e a keeper sheet ([[OFF26-11]]/[[OFF26-2]]), `needs_review` ([[M2]]),
   agregações do League Hub ([[L1]]) e do cap projector, `record_acquisition` e as portas do
   `/auction`. Contra isso, o custo e os limites da **federação** (duas fontes na mesma lista,
   sem persistir). **Precedente relevante:** o Batch 1 do [[O2]] **lê o pool sem persistir nada**
   (`nfl_context.py` — índice em memória, zero schema, zero cache novo) e o [[F13]] fixou onde o
   cache do pool vive e como sua validade é medida. ⛔ Nenhuma das duas opções está escolhida.
2. **Destino do clique num não-`Player`.** Perfil reduzido × board × **sem navegação** (resultado
   informativo). Hoje `/player/<id>` pressupõe linha no DB — o destino define se a fatia B é só
   busca ou também uma página nova.
3. **Identidade e colisão.** Resultados de **duas origens na mesma lista** (se federada); homônimo
   rookie × veterano; ⛔ resolução **sempre por `sleeper_player_id`** — a regra do M10 e o
   precedente Brown valem inteiros, e a lista precisa continuar distinguível (posição + time NFL).
4. **Relação com [[DP1]]/`RookieEspnValue`.** A **classe entrante já tem tratamento próprio** (a
   captura DP3 materializa `in_class`, e o board do cap projector a consome). A F1b decide se a
   fatia B **reusa** essa membership, a ignora, ou a torna redundante — ⛔ sem criar uma segunda
   definição de "quem é entrante".
5. **Escopo do "universo".** Pool inteiro × só skill positions × só ativos. O `is_entering_class_
   member` já tem critério registrado; a busca pode ou não querer o mesmo corte.

#### Notas de registro

- **A engrenagem do [[M10]] é a base — as fatias estendem, não reescrevem.** `createPlayerSearch`
  (componente único), o payload `to_search_dict()`, a ordenação prefixo-primeiro e as guardas de
  identidade continuam valendo; o que muda é **o universo consultado**.
- **A fatia A não bloqueia nem é bloqueada pelo smoke pendente do M10.** São coisas independentes:
  o smoke valida o que já está em produção (hash `5e3c403`); a fatia A é escopo novo. Se o smoke
  reprovar algo, o achado entra no M10 — não aqui.
- **Cross-refs:** [[M10]] (a busca que existe), [[UX11]] (staleness do time NFL), [[O2]]
  (precedente de ler o pool sem persistir), [[DP1]] (entrantes fora do `Player`), [[M13]]/[[M14]]
  (o perfil e o botão de trade que a fatia A precisa examinar), [[OFF26-16]]/[[OFF26-11]]
  (consumidores da tabela `Player` que a F1b tem de mapear).

---

### O2 — Enriquecer Página do Jogador: Contexto NFL + Valor de Campo
⚠️ **Batch 1 VALIDADO EM PRODUÇÃO 08/08/2026 (MAN-O2-F2-B1 → MAN-O2-B1-DONE; gate [[PROC1]]
cumprido — hash `2ed0b4a` live no Render confirmado pelo owner, validação do solicitante
Michel). O item NÃO fecha ✅: Batch 2 (stats históricas + schedule) segue pendente** —
Prioridade **Média** —
**refinado in-place 08/08/2026 (MAN-UX12-REFINE, roteamento (b) do [[UX12]] decidido pelo
owner):** absorve os campos 2 (link p/ página do time) e 5 (idade) vindos do UX12, incorpora a
**F1 consolidada do MAN-O2-F1 (28/04/2026)** — que vivia no
`handoff_code_manager_28_04_2026_pt2.md`, autodeclarado descartável; a regra é diagnose viver
aqui — e corrige a afirmação falsa sobre depth chart refutada pela Q2 da UX12-F1

#### F2 Batch 1 — entregue e VALIDADO EM PROD (MAN-O2-F2-B1 + MAN-O2-B1-DONE, 08/08/2026)

**Smoke de produção aprovado (owner + Michel, hash `2ed0b4a` live — PROC1):**
- **DJ Moore (âncora):** header `🏈 BUF · 29 anos`, chart WR do BUF com destaque por sid,
  franquia linkada — o caso que motivou o item em 27/04 fecha o ciclo.
- **Link cruzado:** Gainwell → página do **ESPN FANTASY LEAGUE** (a franquia *dele*), não a do
  usuário logado — a semântica do link conferida em prod com time ≠ do owner.
- **Validação do solicitante:** Michel (o pedido do [[UX12]] que virou os campos 2/5) conferiu
  e aprovou.

**⚠️ Ressalva — o caminho de degradação NÃO foi exercido em prod.** O smoke local listava
Gainwell entre os **3 rosterados fora do pool**; em produção ele renderizou **completo**
(`TB · 27 anos` + chart RB) — **o pool de prod estava mais fresco que a cópia local** (o cache
é por ambiente; o local era de 31/07). Ocorrência da família *"observação verdadeira,
procedência errada"*: a lista de 3 era fato **do cache local naquele instante**, não
propriedade dos jogadores. A degradação segue coberta pelos testes unitários
(`nfl_context_test.py`: fora do pool, sem birth_date, sem ordem, DEF); **em prod ela não foi
observada** — exercer oportunisticamente se algum rosterado sair do pool.

As 4 dimensões do Batch 1 estão na página (`/player/<id>`): **time NFL no header** (linha nova
`🏈 <time> · <idade> anos`, lendo `Player.nfl_team` — a fonte única da Q1 da UX12-F1), **idade**,
**link do time da liga** (o nome no header virou link p/ `/team/<id>`) e **depth chart do time
NFL** (card próprio, jogador destacado por **sid** — nunca por nome; há dois DJ Moore no pool).

- **`nfl_context.py` novo** — mesma separação do `salary_engine`: núcleo puro (`build_slim_index`
  / `compute_age` / `build_depth_chart` / `assemble_context` — sem DB, sem rede, sem FS;
  **19 testes em `nfl_context_test.py`**) + IO de leitura do pool.
- **Decisões de desenho registradas no módulo:** ⛔ **o caminho de página nunca faz rede** — lê o
  cache do pool no caminho único do F13 (`sync_sleeper._player_cache_path`) e **não dispara
  download**; pool ausente → contexto vazio, página renderiza sem os blocos. Pool **vencido ainda
  serve** (stale-while-usable — depth chart de 8 dias > bloco sumindo; o staleness é a ressalva
  já registrada). Quem renova o pool é o sync (TTL 168h). **Nenhum cache novo em disco** (a nota
  pós-F13 fica satisfeita por vacuidade): índice enxuto em memória de processo, invalidado por
  `(mtime, size)` — mtime só como chave de invalidação, nunca validade (a lição do F13).
- **Idade: derivada em leitura, não persistida** (a F1 deixara a escolha): zero schema, mesma
  freshness do pool; calculada de `birth_date` (não do campo `age`, que envelhece no cache).
- **Degradação conferida com dados reais (smoke local, GET-only):** DJ Moore (âncora) →
  `🏈 BUF · 29 anos` + chart WR do BUF com ele em #1 destacado + link p/ a franquia **dele**
  (`/team/4`), não a do usuário logado; DEF (Atlanta) → sem card, sem erro; **3 rosterados fora
  do pool** (Gainwell, Hollywood Brown, Cameron Ward) → página normal sem idade/chart, sem erro.
- **Guardas respeitadas:** zero coluna nova, zero mudança em folha/cap (54/54 do
  `salary_engine`), Timeline/`PlayerHistory` intocados, nenhuma rota alterada.
- **Suítes:** 19 novos + 54 + 34 + 25 + 36 + 64 + 22 + 14 — todas verdes (as 2 falhas do
  `janela_ensaio_test` em console cp1252 são artefato de encoding pré-existente, 22/22 com
  `PYTHONIOENCODING=utf-8`).

**Problema:** A página atual (`player_detail.html`, M13) mostra contrato, salary history e botão "Propor Trade". Faltam duas camadas de contexto: (a) **valor de campo** — pontuações históricas por temporada, posição no ranking/ADP, próximos jogos; e (b) **contexto NFL básico** — time NFL atual visível no header, e posição relativa do jogador entre os jogadores da mesma posição no time NFL (depth chart).

**Origem da observação (duas, independentes):**
- Caso real DJ Moore (WR) em 27/04/2026 — owner abriu a player page e percebeu ausência completa de contexto NFL: nem o time NFL aparecia no header (apesar de `Player.nfl_team` estar no banco), nem havia indicação de o jogador ser WR1/2/3 do Carolina. Decisão tomada na sessão de planejamento (27/04/2026, decisão A): refinar O2 in-place absorvendo as duas dimensões novas, em vez de abrir item separado (O3). Critérios para refinar e não fragmentar: mesma página alvo (`player_detail.html`), mesma fonte de dados (Sleeper), escopo natural de "enriquecer page do jogador" já existia no item — abrir O3 seria fragmentação artificial.
- **Pedido do co-admin Michel (08/2026, via [[UX12]])** — segundo usuário relatando o mesmo gap de contexto na página do jogador, de forma independente. O UX12 foi **despachado** (roteamento (b), decisão do owner): o perfil vive aqui, a busca vive no [[M10]]. **Requisitos originais e diagnose UX12-F1 no `improvements_archive.md`, seção UX12.**

**Objetivo (7 dimensões, agrupadas):**

*Contexto NFL — dependem só de campos já presentes no banco/cache (Batch 1 da F1):*
- **Time NFL no header:** exibir `Player.nfl_team` no cabeçalho da player page. Hoje o header mostra posição, nome do jogador e dono na liga, sem o time NFL. Trivial — apenas exibir.
- **Link p/ a página do time na liga (ex-campo 2 do UX12):** o nome do time da liga no header é `<strong>` puro (`player_detail.html:26`) — vira link para `/team/<id>` ([[L1]], rota existente). Trivial.
- **Idade (ex-campo 5 do UX12):** não existe em lugar nenhum do Manager hoje. `birth_date`/`age` estão no pool do Sleeper com **94%** de cobertura nos skill com time NFL (conferido no cache local, UX12-F1 Q2). `birth_date` é **imutável** — persistir no sync teria zero staleness; derivar em leitura do pool custa zero schema. Escolha fica para a F2.
- **Depth chart NFL embedded:** listar os jogadores da mesma `Player.position` e do mesmo `Player.nfl_team` ranqueados por `depth_chart_order` do pool do Sleeper. Permite ao owner avaliar em segundos se o jogador é WR1/2/3 do time NFL sem sair da página. **⚠️ Correção (UX12-F1 Q2, 08/08/2026):** este item afirmava que `depth_chart_order` era "campo já consumido pela aplicação" — **falso**, zero consumo em código de produção (grep). O achado real: o dado **está no pool** que o sync já baixa (`depth_chart_order` + `depth_chart_position` em **75%** dos skill com time NFL — QB 73% · RB 71% · WR 62% · TE 64% · K 74% · **DEF 0%**), e **persistir coluna no Player não bastaria** — o depth chart pede os rivais de posição, que em geral **não são Players do DB local** (~280 rosterados vs. 12.204 no pool). O caminho completo é **derivar em leitura do pool** (`_load_players_db()`, TTL 168h — stale conhecido em janela de trades NFL, out–nov). O verbo da F2 muda de "reusar consumo" para "criar o primeiro consumo".

*Valor de campo — dimensões originais do escopo:*
- **Stats históricas:** buscar da Sleeper API (`/stats/nfl/player/<sleeper_player_id>?season_type=regular&season=<year>`) — pontos totais e média por semana por temporada disponível.
- **ECR/ADP:** usar `search_rank` já presente no Sleeper players cache (`.sleeper_players_cache.json`) — zero request extra. **Não há campo ADP real** (F1 de 28/04); `search_rank` é proxy de popularidade de busca. Para ranking ESPN, usar ESPN ref value (`espn_ref_value`) já no banco como proxy de tier.
- **Schedule próximo (consolidado de UX4):** próximas semanas via Sleeper schedule (endpoint correto na F1 abaixo).

Apresentar de forma compacta, sem sobrecarregar a página. Referência: FantasyPros (abas Overview, Statistics, Schedule).

#### F1 consolidada (MAN-O2-F1, 28/04/2026 — absorvida do handoff em 08/08/2026, MAN-UX12-REFINE)

Diagnose read-only executada em 28/04/2026 sobre as 5 dimensões originais; transcrita aqui
verbatim-em-substância do `handoff_code_manager_28_04_2026_pt2.md` (o handoff é descartável; esta
seção passa a ser a fonte). A tabela de disponibilidade abaixo mantém as medições de 28/04 — a
Q2 da UX12-F1 (08/08) as re-conferiu no cache local e elas **batem** (depth chart 75%, idade 94%).

**Disponibilidade por dimensão:**

| Dimensão | Fonte | Cobertura (28/04) | Custo de fetch |
|---|---|---|---|
| Time NFL no header | `Player.nfl_team` (DB local) | 263/280 (94%); 17 sem nfl_team são FAs (Mixon, Allen, Diggs, Njoku, etc.) | Zero |
| Depth chart NFL | Sleeper players cache local (`team`, `position`, `depth_chart_order`) | Em players com time NFL: QB 73%, RB 71%, WR 62%, TE 64%, K 74%, **DEF 0%** | Zero |
| Stats históricas | `GET /stats/nfl/player/{sid}?season_type=regular&season={year}` (**SEM `/v1/`**) | Veteran: 7-8 seasons. Rookie: 1. `null payload` para seasons sem dados (graceful) | ~150-200ms por season, ~1.7KB |
| ECR/ADP | `search_rank` (Sleeper cache) + `Player.espn_ref_value` (DB). **Não há campo ADP real** | search_rank: 70,6% dos com time NFL; ESPN ref: ~100% | Zero |
| Schedule próximo | `GET /schedule/nfl/regular/{year}` (**SEM `/v1/`**) + `/v1/state/nfl` | 272 games/season; 2025: 100%; **2026: 0 games à época (NFL não publicara)** | ~140ms, ~27KB por season |

**Endpoints corretos (correção factual da F1 — premissa pré-refinamento referenciava paths errados):**
- Stats: `https://api.sleeper.app/stats/nfl/player/{sid}?season_type=regular&season={year}` — **sem `/v1/`**. O `/v1/stats/...` retorna `{}` ou 404.
- Schedule: `https://api.sleeper.app/schedule/nfl/regular/{year}` — **sem `/v1/`**. Playoffs: `/schedule/nfl/post/{year}`.
- State: `https://api.sleeper.app/v1/state/nfl` — **com `/v1/`** (dá `season_type`, que define se o schedule é exibível agora).

**Batching recomendado: 2 batches.**
- **Batch 1 (zero fetch externo):** Time NFL no header + link p/ time da liga + idade + depth chart embedded + ECR/ADP (`search_rank` + ESPN ref). Custo trivial; nenhum cache novo; entrega o contexto NFL inteiro (cobre o caso DJ Moore **e** os campos do Michel). Os dois campos ex-UX12 entram aqui — são da mesma classe "banco/cache local, custo zero".
- **Batch 2 (fetch + cache):** Stats históricas + Schedule próximo. Exige 2 helpers novos + 2 cache files; mesmo padrão T2/T3 (TTL 24h, fallback gracioso).

**Escopo das stats históricas:** 5 últimas seasons (rookie + 4 veteran), season-aggregated (o endpoint só dá agregado), tabela compacta (Year / Team / GP / Pts PPR / Rank Overall / Rank Pos). Mid-season trade: payload só tem o team final da season — aceitar com header "Team final". Seasons com `null payload`: pular silenciosamente (não exibir "0 pts"; caso McBride 2022 — o endpoint às vezes retorna `null` mesmo para season ativa, F2 não pode confiar em "se ativo → tem dados").

**Fonte do schedule:** Sleeper `/schedule/nfl/regular/{year}` é a única viável (`/v1/research/*` e `/projections/*` retornam 404/400). Offseason com schedule vazio: ocultar a dimensão ou texto "Schedule X ainda não publicado". Durante a temporada: próximas 3-4 semanas do `Player.nfl_team`.

**Cache strategy:** stats em `.player_stats_cache.json` (keys `"<sid>:<season>"`, TTL 24h; seasons fechadas são imutáveis — nunca refetch com cache válido); schedule em `.nfl_schedule_cache.json` (keys `"<year>:<season_type>"`, TTL 24h em regular/post, 168h para season completa). Padrão de fallback: `dynasty_values.py` (cache stale on API failure). ⚠️ Nota pós-F13 (31/07/2026): caches novos devem seguir o padrão F13 — viver em `dirname(DYNASTY_DB)` com carimbo `fetched_at` dentro do arquivo, não na raiz do app.

**Reuso mapeado:** `_get(url, timeout)` e `_load_players_db()` (TTL 168h) de `sync_sleeper.py` (leitor do pool para depth chart + idade); padrão TTL/fallback de `dynasty_values.py`; ponto de entrada dos dados novos = `routes/roster.py:player_detail()`. **Novo necessário:** `_load_player_stats(sid, seasons)`, `_load_nfl_schedule(year)`, `_get_depth_chart(team, position, players_db, exclude_sid)`; 2 arquivos JSON de cache.

**Observações tangenciais registradas (sem ação):** pool TTL 168h pode ficar stale na janela de trades NFL (out–nov) — afeta o depth chart embedded; `search_rank` não é ADP/ECR real (candidato futuro "ADP-FP", nunca registrado); schedule só dá home/away/date/status; 17 players com `nfl_team` vazio (FAs) — F2 deve testar "fantasy_team setado, nfl_team vazio" (caso Tank Dell).

#### Guardas herdadas do UX12 (invariantes que a F2 respeita)

- **Cap hit / folha ([[OFF26-16]]):** a página já lê as fontes canônicas — `Player.salary` para o hit individual (`player_detail.html:52`); qualquer contexto de folha do time só via `Team.total_salary()` → `salary_engine.roster_salary` (o IR conta). ⛔ Nenhuma soma nova, nenhum filtro de IR.
- **Histórico ([[S4]] 🔲):** a Timeline exibe `PlayerHistory` **como está** — nome de time como snapshot de exibição (mesmo endpoint `/api/player/<id>/history` e mesmo formatador já em produção). Zero acoplamento novo: o risco do S4 é de **escrita** (dedupe pós-rename no índice UNIQUE com `team_name`), não de leitura; o enriquecimento não o piora nem depende dele.
- **Página existente, não página nova (Q5 da UX12-F1):** enriquecer a `/player/<id>` atual — 2 helpers (`player_name_link` + `renderPlayerNameLink`) e 6 links inline apontam para ela; página nova exigiria redirect e re-apontamento sem ganho identificado.

**Notas para F1/F2:**
- Item UX4 da rodada de 23/04/2026 foi consolidado aqui em vez de duplicado — escopo virtualmente idêntico (mesma API Sleeper, mesma página alvo). Idem os campos 2/5 do [[UX12]] em 08/08/2026 (mesma página alvo, mesma classe de fonte).
- A F1 acima já decidiu o batching (2 batches); a densidade da página segue sendo critério da F2 — 7 dimensões numa página que hoje tem 3 cards.

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

### L4 — Qual evento reabre a exibição de projeção no ciclo seguinte?
🔲 **Pendente** — Prioridade **Baixa** — registrado 13/08/2026 (MAN-L3-FIX)

**Problema (medido, não suposto):** o gate do [[L3]] (`_projection_open`) abre enquanto
`rollover_done != "true"`. O rollover grava `"true"`
([routes/offseason.py:707](routes/offseason.py#L707)) e **nenhum sítio do código grava `"false"`
de volta** — `_seed_app_config` só insere chave **ausente**
([app.py:441](app.py#L441)) e o `ensaio_janela_selada --reset` não toca a flag. Logo, depois de
18/08 o bloco de planejamento da `/league` e do `/team/<id>` some e **não reaparece sozinho** na
intertemporada seguinte, quando volta a ser exatamente a informação mais útil da tela.

**Por que não foi decidido junto com o L3:** a flag vive no `app_config`, que é **contrato
externo** (consumido pelo `fantasy_optimizer`); mudar quem escreve `rollover_done` — ou quando —
tem alcance maior que a tela. É decisão do owner, não do implementador.

**Opções a considerar (nenhuma implementada):**
- zerar `rollover_done` no **fechamento da season** (passo 1 do `/offseason`), tratando-o como
  flag de ciclo — é o que o nome sugere, e alinharia o `rollover_blocks_urn` do [[OFF26-10]], que
  já lê a flag como se fosse por-ciclo ([routes/late_drop.py:127](routes/late_drop.py#L127));
- **flag de exibição própria**, deixando `rollover_done` intocado (menor risco para o contrato
  externo, mais uma chave para manter);
- derivar a fase de outro sinal já existente, sem chave nova.

⚠️ **Guarda ativa:** `cap_projetado_test.TestGateSemPromessaFalsa` falha se algum sítio passar a
gravar `rollover_done="false"` **ou** se a docstring do gate voltar a prometer reabertura
automática — quando o L4 for implementado, os dois pontos têm de ser atualizados juntos.

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

### OFF26-23 — Ano de contrato do rookie 2026 × rollover × passo 5
⚠️ **POKA-YOKE IMPLEMENTADO 10/08/2026 (MAN-OFF26-23) — smoke de produção PENDENTE (gate
[[PROC1]])** — Prioridade **Alta (a semana 17→24/08)** — Registrado + F1 no mesmo dia
(MAN-OFF26-23-REG-F1); diretriz do owner: **o sistema recusa a ordem errada, não depende de
disciplina**

**PRE-FLIGHT 14/08 (MAN-DP-PREFLIGHT-1808, read-only) — o que exatamente falta para ✅:** os três
gates estão **no código deployado** (conferido no `HEAD`: `rollover_order_gate` em
[draft_import.py:113](routes/draft_import.py#L113) chamado no `build_preview` `:166`; 409 +
`requires_force` no `toggle_rookie_draft`; backup automático no `clear_rookie_espn_store`) e o
último commit de código — `c8b750f`, do [[UX18]] — teve **smoke do owner aprovado em produção em
14/08**, o que o coloca no ar por descendência. **Falta apenas o exercício in situ**, que a
própria semana produz e que o VERIFY já descreveu: (1) domingo 17/08, com o draft real
**completo** e o rollover ainda pendente, abrir o preview em `/draft_import` → esperar **400
`rollover_pendente`** (preview não escreve — custo zero); (2) segunda 18/08, pós-rollover, o mesmo
preview passar. ⛔ Nenhum outro artefato pendente: o item fecha com essas duas observações.

#### F2 — entregue (MAN-OFF26-23, 10/08/2026): os 3 pontos de não-retorno cercados

**Princípio registrado (diretriz de desenho do owner):** ponto de não-retorno não se protege com
runbook — se a ordem importa, **o sistema recusa a inversão** (poka-yoke). Candidato a baseline do
DEV_METHODOLOGY na próxima consolidação (família [[MAN-METH-REG]]) — registrado, não consolidado.

1. **Gate no importador do draft** (`rollover_order_gate`, `routes/draft_import.py` — núcleo
   puro + chamada no topo do `build_preview`, então **bloqueia preview E confirm**): modo linear
   com `draft_season > current_season` → recusa com mensagem que cita o dano ("todo rookie
   viraria Ano 2") e o que fazer (passo 4). A condição observável é a season — `current_season`
   só avança NO rollover. **Modo auction fora do gate de propósito** (transitivamente gateado:
   sheet congelada ← definitiva ← urna ← `rollover_done`); **import histórico segue permitido**
   (`draft_season <= current` — comportamento antigo).
2. **Gate no passo 5** (`toggle_rookie_draft`): marcar sem NENHUM registro `rookie_draft` na
   season corrente → **409** com `requires_force` e mensagem que explica o que seria apagado (a
   classe nasceria a $1 — o consumidor mais crítico do store é o próprio import, achado da F1).
   Cenário legítimo de pular o import (season sem draft) → **`force: true` explícito**; a UI do
   painel transforma o 409 em confirmação informada (o texto do erro no `confirm()`) — nunca
   silêncio. `undo` não passa pelo gate.
3. **Clear com rede** (`clear_rookie_espn_store`): antes de apagar, grava **backup automático**
   (`rookie_espn_backup_<UTC>.json` em `dirname(DYNASTY_DB)` — o volume persistente, padrão F13,
   carimbo dentro do arquivo) e devolve `(n, path)`; o endpoint reporta o caminho no payload.
   **`restore_rookie_espn_backup(path)` reidrata pela porta única** (`upsert_rookie_espn`,
   valores E membership) — "o clear não tem undo" deixou de ser verdade. ⛔ Camada ADICIONAL:
   não substitui o backup manual pré-operação dos runbooks.

**Guardas respeitadas:** rollover/varredura/salary_engine/fluxo de contrato intocados (há teste
estático de que a varredura não mudou); caminho feliz do import byte-idêntico (gate só dispara na
inversão); once-only do rollover não regrediu (teste).

**Runbooks atualizados:** `runbook_urna_late_drop.md` ganhou a seção **"17→18/08 — a ordem
crítica"** (ESPN → rollover → import → agendar urna; ⛔ dos 3 pontos; passo 5 como último ato
pós-24/08 em seção própria) e o `runbook_cowork_liga_fantasma.md` ganhou a nota cruzada. Os dois
mencionam que **o sistema recusa a inversão**.

**Testes: `poka_yoke_test.py` (15)** — gate do import (4: bloqueia futuro, passa ordem certa,
histórico permitido, auction fora), passo 5 (4: 409 informado sem mutação, caminho feliz, force,
undo livre), clear com rede (3: backup antes do delete com carimbo F13, restore pela porta única
com membership, vazio não cria arquivo), guardas estáticas (4: once-only, gate no preview,
varredura intocada, 409+force presentes). **Suítes completas verdes** (54+35+15+14+19+34+25+36+
64+22).

**Smoke local (app real, cópia do seed, `_read_draft` simulado):** ordem errada → preview e
confirm **400 `rollover_pendente`** com a mensagem acionável; current avançado p/ 2026 → preview
200 sem gate (caminho feliz); passo 5 sem import → **409 `requires_force`** citando o dano. ⚠️
Não exercido: navegador (confirm() do force na UI) e o fluxo real de 18/08 — é o smoke do owner
e a própria semana.

#### VERIFY — a ordem real do gate no preview (MAN-OFF26-23-VERIFY, 10/08/2026, read-only)

**O que o smoke do owner viu (hash `7cf1a23`):** preview com draft_id inexistente devolveu
"Draft não encontrado na API do Sleeper" — não a recusa do gate. Das três leituras possíveis, a
evidência fecha na **(1): ordem correta por necessidade; o relato da entrega ("no topo do
build_preview") era impreciso.**

**A ordem real, passo a passo (`routes/draft_import.py:146-169`):**
1. `_read_draft(draft_id)` — id inexistente → **"não encontrado"** e fim (`:147-149`). É o que o
   owner viu: **sem draft não há season nem tipo para o gate julgar** — a recusa de not-found
   ANTES do gate é o desenho correto, não furo.
2. `status != "complete"` → **"não está completo"** e fim (`:150-152`).
3. `is_rookie` (do `draft.type`) e `season` (do `draft.season`) são extraídos (`:154-161`) — **os
   dois insumos do gate nascem AQUI**, da leitura; por isso o gate não pode vir antes.
4. `_team_by_roster` (`:162` — 1 leitura de API extra antes do gate; custo, não risco — nota
   abaixo).
5. **O gate roda (`:166-169`)** — e o confirm reusa o `build_preview`, então a mesma recusa vale
   nos dois endpoints. **Nada é escrito antes do gate em caminho nenhum** (preview nunca escreve;
   as escritas do confirm vêm muito depois).

**A sequência de domingo (id válido de 2026, completo, rollover pendente):** passos 1-2 passam,
`is_rookie=True`/`season=2026` no 3, gate dispara no 5 → **400 `rollover_pendente`** em preview E
confirm. Nenhuma reordenação necessária. Nota menor registrada (não é fix): mover o gate para
antes do `_team_by_roster` pouparia 1 chamada de API na recusa — micro-otimização, sem efeito de
correção.

**Por que o gate NÃO é exercitável em prod HOJE com draft real:** o único draft linear de 2026 (o
da liga real, 17/08) está `pre_draft` — o check de status (`:150`) dispara **antes** do gate. O
draft de 2025 é `complete` mas `season <= current` → exercita o **bypass** (histórico permitido),
não o gate. **O teste que vale acontece naturalmente domingo à noite:** draft real completo +
rollover ainda pendente → abrir o preview no `/draft_import` → **esperar a recusa
`rollover_pendente`**. Zero efeito colateral (preview não escreve) — é o poka-yoke se provando in
situ, e entra como conferência do roteiro de 17/08. Opcional para hoje: **mock draft** no Sleeper
(linear, season 2026, completar) e usar o id no preview — mock vive fora da liga, preview não
escreve nada.

**Cobertura da suíte, respondida:** a DECISÃO de domingo é `test_classe_de_season_futura_bloqueia`
(exatamente `(True, 2026, 2025)` → recusa, contra o núcleo puro); a FIAÇÃO é
`test_gate_roda_no_preview_e_por_tabela_no_confirm` (estático). A sequência ponta-a-ponta (id
válido + season futura + rollover pendente → 400 nos DOIS endpoints) foi exercida no smoke da F2
contra o app real com `_read_draft` simulado — não vive na suíte porque exigiria mock de rede.
**Parecer opcional registrado (não implementado — sessão read-only):** um caso de endpoint com
`_read_draft` monkeypatchado no `poka_yoke_test` (~10 linhas) fecharia o vão.

#### FIX — SyntaxError no JS inline da /offseason (MAN-OFF26-23-FIX, 10/08/2026)

**O que o smoke do owner pegou (hash `6ecb90e`):** clicar no passo 5 não fazia nada. Console:
`Uncaught SyntaxError: Invalid or unexpected token` + `toggleFlag is not defined` — na edição
gerada do `6ecb90e`, o `\n\n` da mensagem do confirm virou **quebra de linha real** dentro da
string JS; o parse do bloco inteiro morreu e **nenhuma** função da página existia (inclusive os
botões dos passos 3 e 4, de que o 18/08 depende). O gate de servidor estava íntegro — o 409 nunca
chegou a ser requisitado; nada foi gravado. Era exatamente a parte declarada "não exercida em
navegador" na entrega.

- **Fix de 1 linha** (`offseason.html:763` — a string voltou a ter `\n` literal). Varredura dos
  irmãos: **todos os blocos `<script>` de todos os templates** parseados via node — só o
  offseason estava quebrado.
- **Exercido em DOM headless** (não há browser instalável nesta máquina — declarado): todas as
  13 funções de onclick da página definidas; clique no passo 5 sem import → confirmação informada
  **com o texto do dano e a pergunta na mesma caixa**; cancelar → zero segundo POST + feedback
  "Cancelado"; aceitar → repost com `force: true`. Passos 3/4 voltam a responder por construção
  (o bloco parseia inteiro).
- **Guarda permanente: `template_js_test.py` (3 testes)** — parseia o JS inline de TODO template
  (node quando disponível; fallback de heurística de string não terminada — a classe exata do
  incidente — quando não; **nunca silencioso**, o relatório diz qual camada rodou). Provado
  contra a regressão real: o teste **falha no `6ecb90e`** e passa no fix.

**Lição registrada (candidata [[MAN-METH-REG]]):** *poka-yoke silencioso é meio poka-yoke — a
mensagem é parte do mecanismo.* O gate de servidor existia e recusava, mas a camada que
transformava a recusa em decisão informada estava morta, e o conjunto degradou para "botão que
não faz nada". Corolário operacional: JS de template só entra com parse conferido
(`template_js_test.py` agora força isso no baseline) — e edição gerada de template com escapes é
ponto de atenção de revisão.

**Pergunta do owner (10/08, 7 dias do draft):** o rookie drafteado em 2026 entra e **permanece**
com contrato Ano 1? A dúvida é a interação de três mecanismos: aquisição via rookie draft
(`record_acquisition`, Ano 1 por `floor(ESPN×1,2)`), **rollover** (incrementa `contract_year`) e
**passo 5** ("Rookie Draft Done", que roda `clear_rookie_espn_store`). Cross-ref: [[OFF26-9]]
(acoplamento de fases — a família é real), OFF26-20-FIX (caso Gainwell), F1b do [[M21]] (o clear
do passo 5).

#### Q1 — A ordem canônica: existe no desenho, NÃO no código

- O painel implementa a ordem 1→7 com gates reais até o rollover: **passo 4 (rollover) exige
  passos 2+3** (lottery travado + ESPN atualizado) e é **once-only** — reexecução devolve 400
  "Rollover ja foi executado" (`offseason.py:674-675`). A urna exige `rollover_done`
  (`rollover_blocks_urn`, `late_drop.py:135` — escape só pelo banner de ensaio).
- ⛔ **Mas o importador do draft (OFF26-3) NÃO tem gate de `rollover_done`** — nada no código
  impede importar o rookie draft **antes** do rollover. A ordem *rollover → import do draft* é
  **disciplina operacional**, não invariante. O calendário do owner (17/08 draft no Sleeper ·
  18/08 ESPN definitiva + rollover) pressupõe exatamente essa disciplina: o draft ACONTECE dia 17,
  mas o **import para o Manager** é um ato separado — e é ele que cria os contratos.

#### Q2 — O rookie atravessa o rollover? Depende SÓ da ordem do import

**O filtro real da varredura, citado:** `Player.query.filter_by(is_dropped=False)`
(`offseason.py:686`) — **cega a contrato recém-aberto**; não há skip por `contract_start_season`
nem por data. Para cada um, `apply_season_rollover` faz `next_yr = contract_year + 1`
(`salary_engine.py:206`).

- **Import DEPOIS do rollover (a ordem segura):** o rookie nasce Ano 1 na season 2026 e **nada o
  toca até o rollover de 2027** — o once-only garante que o rollover 2026 não roda de novo. ✅
- **Import ANTES do rollover:** cada rookie importado entra na varredura e vira **Ano 2 com
  valorização** no dia seguinte — o Gainwell em massa, para a classe inteira. ⛔ Este é **o ponto
  de não-retorno da semana**.

#### Q3 — Estado de produção: o rollover 2026 ainda NÃO rodou (alta confiança; conferência pronta)

Dois indícios convergem: o seed local (working tree) tem `current_season=2025` +
`rollover_done=false`, e o **smoke da urna em prod (07/08) precisou do escape do banner de
ensaio** — que só existe para contornar o gate `rollover_done` pendente (`rollover_blocks_urn`).
Se o rollover tivesse rodado, o escape seria desnecessário. **Implicação: a janela de risco da Q2
está inteira à frente.** Conferência observável (Render Shell, read-only):

```bash
sqlite3 /data/dynasty.db "SELECT key, value FROM app_config WHERE key IN
  ('current_season','rollover_done','rookie_draft_done','offseason_step','auction_done');"
sqlite3 /data/dynasty.db "SELECT contract_year, COUNT(*) FROM players WHERE is_dropped=0
  GROUP BY contract_year;"
```

`current_season=2025` + `rollover_done=false` confirma; a distribuição de `contract_year` é a
foto de antes (compare depois do rollover: tudo deslocado +1, renovações em 1).

#### Q4 — O passo 5 não gateia NADA além de si mesmo (o plano de segurar o clique é seguro)

Leitores de `rookie_draft_done` no código: **só a UI do painel** (`offseason.py:182,198` — status
do passo) e o próprio toggle. **Nenhum mecanismo entre 17 e 24/08 depende dele marcado**: o
importador (linear e auction) não o lê, o congelamento da exclusão não o lê, a urna não o lê, a
auction não o lê. Efeitos do clique: (1) flag `rookie_draft_done=true`; (2) **o clear do store**
(`clear_rookie_espn_store`) — e reverter **não repopula** (`offseason.py:731-734`).
✅ **O plano "não marcar o passo 5 até pós-24/08" é validado** — custo zero, e evita o achado da
F1b do M21 (o clear evaporaria a camada de valor na semana do caso de uso).

#### Q5 — Gainwell como lente: mesma manifestação, raiz DISTINTA

A correção `2→1` do OFF26-20-FIX tratou **semântica de canal de aquisição**: contratos de
`free_agent` (add grátis) que deviam **recomeçar** e carregavam ano herdado — raiz no vocabulário
do rebuild F8, resolvida caso a caso pelo canal (`tx.type` da API) e reparada pela porta canônica
`contract_year_correction`. **Não era** incremento de rollover sobre contrato recém-aberto. O
risco daqui (ordem de fases) é **outra raiz com o mesmo sintoma** (`contract_year` um acima).
O fix de lá **cobriu a raiz de lá**; a raiz daqui **não tem guarda de código** — o que existe é o
roteiro abaixo. Se o pior acontecer, a porta `contract_year_correction` é o caminho de reparo já
construído (auditável, molde M2).

#### O ROTEIRO SEGURO DA SEMANA (17→24/08)

**Não há conflito entre os dois objetivos** (rookie Ano 1 · store vivo até a auction) — ambos
saem da mesma disciplina de ordem:

| Data | Ação | Guarda |
|---|---|---|
| 17/08 | Rookie draft **no Sleeper** (liga real). ⛔ **NÃO importar ainda** | O import antes do rollover é o ponto de não-retorno (Q2) |
| 18/08 | **Nesta ordem, no mesmo dia:** (1) import ESPN definitiva (passo 3) → (2) **rollover** (passo 4) → (3) **só então** importar o rookie draft (OFF26-3 linear) | O rollover exige passo 3; o import do draft usa o store (`rookie_espn_adjusted` → `floor(ESPN×1,2)`); rookies nascem **Ano 1/2026** e nada os toca até 2027 |
| 18/08+ | Agendar a urna (o gate `rollover_done` agora passa sem escape) | `rollover_blocks_urn` |
| 20/08 | Cortes no Sleeper → sync (sheet provisória) | Fluxo OFF26-1/2 inalterado |
| 22/08 | Urna fecha → revelação → sync (sheet definitiva) → **congelar exclusão** | Fluxo OFF26-10/11 inalterado |
| 24/08 | FA auction na fantasma → **import auction** (gate da sheet congelada) | ⛔ **Passo 5 AINDA não marcado** |
| pós-24/08 | Marcar **passo 5** (clear do store — agora inofensivo) → passo 7 (auction done) | Q4: nada dependia dele; o store já cumpriu os dois papéis (salário do draft + valor na busca, se a fatia B entrar) |

**Pontos de não-retorno marcados:** (1) importar o draft antes do rollover — reparável só via
porta de correção, um a um; (2) marcar o passo 5 antes do **import do draft** — zeraria os
salários da classe para $1 (o import lê o store), reparável só re-importando após repopular o
store; (3) o clear não tem undo (reverter o passo 5 não repopula).

#### Listas da regra MAN-METH-REG

**(a) Premissas do calendário/plano que o código contradiz:**
1. *"A ordem das fases está garantida pelo sistema"* — **não está**: o gate real acaba no passo 4;
   o import do draft roda a qualquer momento. Parecer: um gate `rollover_done` no import linear é
   candidato natural a item de código — **não arbitrado aqui**, decisão do owner.
2. *"Segurar o passo 5 pode travar algo da semana"* (a dúvida implícita do plano) — **refutada por
   grep**: nada lê a flag além da UI do painel.

**(b) Comportamentos existentes que o plano da semana omite:**
1. ⚠️ **O consumidor mais crítico do store é o PRÓPRIO import do draft** (`rookie_espn_adjusted` →
   salário), não a busca/auction que o plano queria proteger — segurar o passo 5 protege os dois,
   mas a ordem "import antes do clear" é ainda mais dura que o plano supunha.
2. O rollover é **once-only** (400 na reexecução) — a família "rollover roda de novo e incrementa
   o rookie" **não existe**; o risco é só de ordem, não de repetição.
3. A urna **exige** `rollover_done` — atrasar o rollover além de ~21/08 empurraria o agendamento
   da urna (o escape de ensaio não é para produção).
4. O passo 4 exige o passo 3 — a ESPN definitiva (18/08) **precede** o rollover por construção; a
   ordem interna do dia 18 (ESPN → rollover → import) sai do próprio painel.

---

### OFF26-24 — Script de população do board da liga fantasma
🔲 **CRITÉRIO DE 19/08 ✅ CUMPRIDO EM 12/08/2026 (MAN-OFF26-24-GO) — ciclo limpo 12/12 +
auditoria + RESET exercido, zero intervenção, 7 dias antes do prazo. Decisão do owner: o
script É O PLANO A da população real de 22/08; Cowork/runbook rebaixado a plano B
(contingência). O item fecha ✅ (e migra ao archive) após a população real de 22/08 — que é o
USO, não o critério.** — F2a/F2b 11/08 + FIX9/10/11 + GO 12/08 — Registrado + F1 em 10/08
(MAN-OFF26-24-REG-F1) — Prioridade **Alta (uso real 22/08)** — decisão do owner (10/08)
**revertendo o adiamento para 2027**: (a) rollback é
trivial e do próprio owner (RESET DRAFT / remoção manual; pior caso = recomeçar, sem dano
possível à liga real); (b) a variância do Cowork (~2h a ~5h; 2ª execução: **58min para 3 times**
por timeouts) ameaça a janela de 48h entre late drop (22/08) e auction (24/08)

**Condições de contorno (do prompt de 10/08 — RESOLVIDAS em 12/08, planos INVERTIDOS pelo GO):**
o Cowork permaneceu plano A até a validação do script, cumprida em 12/08 (antes do prazo de
19/08) — **agora o script é o plano A e o Cowork é a contingência**. As duas proibições seguem
PERMANENTES: ⛔ **API interna não documentada do Sleeper VETADA** (sem contrato, risco de ToS,
expõe a conta do comissário). ⛔ **Nada roda contra a liga real em hipótese alguma** — a guarda
de `league_id` é requisito de nascença.

#### Ensaio de 11/08 (Cowork) — a spec que faltava, e o achado que define a arquitetura

**Executado:** 18 keepers do MellowBR populados no board (draft `1392654933580353536` — fixture
de leitura, o id muda a cada reset), total **$176 conferido por API**; os picks permanecem no
board **de propósito** como fixture viva da validação read-only da F2a. Mapa dos 12 slots
anotado (Team 1=MellowBR … 12=freddupont) — derivado sempre, fixture só confere.

**A spec de seletores (respostas aos 7 itens da F1):** classes **BEM legíveis**; board no
**documento principal (sem iframe)**; **264 células no DOM, sem virtualização**; menu de contexto
= `div.item` com title "Set Player" / desc **"Manually set a player for Team {N}"** (o N confirma
o time); busca = `input[placeholder="Find player Ctrl + U"]` — **há 3 na página, usar o do
modal**; linha de resultado = `.player-rank-item2` com `.position`/`.team` (anti-homônimo pelo
DOM, nunca pixel); "+" = `.draft-button` (desabilitado = classe `disable`); confirmação nasce
**"Assign a player"** e vira **"SET PLAYER"** (`.linear_gradient`). Viewport oscila **1197↔1496,
DPR 0.8** — âncora por seletor/texto, nunca pixel. Interação: **eventos reais de teclado**
obrigatórios — setar `.value` programaticamente **não dispara o filtro** de busca. ⚠️ Único
seletor que o resumo não fixou: a **célula** do board — o comando `probe` do script anota.

**O achado que define a arquitetura — o cliente MENTE:** pós-SET PLAYER o board pode **não
atualizar**, e o toast vermelho **"This pick could not be processed" pode aparecer COM o pick
gravado**. Portanto: **comando via DOM, verdade via API** — assentamento confirmado em
`GET /v1/draft/{draft_id}/picks` (lag ~3s, retry de leitura), nunca pelo board/toast. Redes:
**o servidor rejeita pick duplicado** (re-comando é seguro) e o caso **Caleb** (staging
revertido) → re-comando. As 3 correções de runbook do ensaio (verificação por API · filtro
K/DEF relaxado a fallback · nota Diggs/D.Jones = dado fresco) entraram no
`runbook_cowork_liga_fantasma.md` — que segue plano A.

#### F2a — entregue (MAN-OFF26-24-F2a, 11/08/2026): esqueleto + guardas + 1 designação

**`tools/phantom_board/`** (standalone, fora do app Flask) — mesma separação da casa: **núcleo
puro** (`core.py`: guarda de liga, parse de picks com as armadilhas do OFF26-4 — sid de DEF é
sigla, amount é string —, mapa slot↔owner por `draft_order`, casamento sheet↔picks POR SID com
5 baldes, decisão de assentamento) + IO (`sleeper_api.py`: API pública read-only, o caminho D1;
`board.py`: Playwright) + `cli.py` (3 comandos) + README de execução para o owner.

- **Fundação Playwright:** headed, **perfil persistente dedicado** (`launch_persistent_context`;
  login manual 1×; zero credencial; ⛔ nunca o perfil principal); busca e preço por **teclas
  reais** (`press_sequentially`/`press` — o achado do `.value`); cliques por seletor/texto.
- **Guardas de nascença:** `LEAGUE_ID` hardcoded + `league_guard` roda **antes de abrir o
  browser** (teste estático garante a ordem) + conferência do nome "Dynasty SB FA Auction" na
  página antes do 1º clique + `assert_allowed_click` com a lista de proibições (**START DRAFT /
  RESET DRAFT nunca são clicados**). `draft_id` derivado a cada uso (D1).
- **Camada de verdade:** `fetch_picks`/`fetch_draft`/`fetch_users`; `validate` (read-only, zero
  browser) casa picks vivos × sheet e imprime contagem+total por time — a conferência da F2a é
  os **18 = $176** do MellowBR.
- **`designate` ponta a ponta:** célula→menu (verificação canônica pelo texto "for Team {N}";
  time errado → Escape e varre)→busca→anti-homônimo pelo DOM (posição obrigatória; divergência
  de sigla vira **aviso** — nota Diggs/D.Jones; 0 ou 2+ candidatos abortam)→"+" (nunca o
  nome)→preço (nasce $1; >$1 → Ctrl+A+dígitos)→SET PLAYER→**poll na API até assentar**
  (toast ignorado; duplicata = sucesso; timeout → 1 re-comando; 2º timeout → **aborta barulhento**
  com screenshot + trace + relatório JSON). Relatório JSON nos dois modos (`runs/`).
- **Manager: exposição mínima do parecer Q2** — `GET /api/admin/keeper_sheet_export`
  (`@admin_required`): o pacote do `build_sheet` (sid + owner_id) reshapeado por
  `_sheet_export_payload` (puro, testado). ⛔ `build_sheet`/núcleo da auditoria **intocados**;
  nenhuma segunda definição de keeper — o owner salva a resposta logado e passa o arquivo ao
  script.
- **Testes: `phantom_board_test.py` (30)** — guarda de liga (incl. o id hardcoded), parsing
  (amount string, DEF sigla, lixo não levanta), mapa de slots (fixture do ensaio confere
  formato), casamento (casado/salário divergente/owner divergente/fora da sheet/faltantes/DEF/
  totais), assentamento (4 estados), reshape do endpoint, e **guardas estáticas do driver**
  (proibições consultadas, guarda antes do browser, verdade via API, playwright lazy — o
  `validate` roda sem ele —, teclas reais, "+" nunca o nome). Suítes completas verdes
  (54+35+15+3+**30**+14+19+34+25+36+64+22).
- ⚠️ **Não exercido nesta sessão:** o driver em navegador real (sem browser logado na máquina do
  Code) — **a validação da F2a é do owner**, roteiro em 4 passos no README (`validate` read-only
  18=$176 → `probe` anota o seletor da célula → `designate` de 1 keeper de outro time →
  conferência do abort com league_id errado). De carona, a guarda de liga **já passou contra a
  fantasma real** (o `validate` derivou o draft ao vivo na sanidade de CLI).

##### FIX da guarda de identidade (MAN-OFF26-24-F2a-FIX, 11/08/2026)

**O 1º probe real do owner pegou:** a guarda abortou com "não exibe 'Dynasty SB FA Auction'" —
mas o board CERTO tinha carregado (URL com o draft_id derivado; picks do ensaio visíveis). Causa:
**a página do draft não exibe o nome da liga** (mostra "MellowBR's Draft", "12-team PPR
Auction") — a guarda procurava texto que não existe naquela superfície. E o **`validate` já
estava verde em execução real: 18/18, $176, zero divergências** — meia F2a validada antes do fix.

- **Guarda refeita POR CONSTRUÇÃO** (`core.url_guard`, puro+testado): derivação do `draft_id`
  pela API → navegação → **a URL contém o draft_id derivado** — mismatch/redirect → aborto
  barulhento. O título da página virou **conferência secundária informativa** (logada, não
  gate); teste estático garante que `LEAGUE_NAME` não volta a ser gate no driver. A exigência
  não relaxou — mudou a FONTE da prova.
- **1ª vida do perfil tratada:** janela deslogada renderiza o board como espectador com **"JOIN
  DRAFT" visível** — o script detecta, pausa e pede o login manual ("logue na janela e pressione
  Enter"; fallback sem stdin: espera o sinal sumir, até 120s) em vez de estourar em 20s. **JOIN
  DRAFT entrou na lista de cliques proibidos**; teste estático garante que o fluxo de login não
  contém `.click()`.
- **`designate` herda o fix por construção** — os dois comandos passam pelo mesmo `open_board`.
- README com o fluxo real da primeira execução. Testes 30 → **35**.

**FIX2 (MAN-OFF26-24-F2a-FIX2, 11/08):** a re-execução esbarrou no **hCaptcha do Sleeper, que
recusa verificar dentro do Chromium de teste** ("Failed to get captcha verification" — anti-bot
detecta o navegador de automação; o desafio nem renderiza). Bloqueio de **porta**, não de
operação (as designações do Cowork nunca exigiram captcha). Fix: launch pelo **Chrome real
instalado** (`channel="chrome"`, mesmo perfil dedicado) + as duas mitigações padrão do
Playwright para o widget renderizar o desafio **ao humano** (`AutomationControlled` off,
`--enable-automation` removido) — ⛔ **nada resolve nem burla captcha: o owner resolve na
janela**, e há teste de que nenhuma lib/serviço de resolução aparece no driver. Chrome ausente →
aborto com instrução (**nunca** fallback silencioso ao Chromium). Testes 35 → **36**; requisito
novo no README: Chrome instalado.

**FIX3 (MAN-OFF26-24-F2a-FIX3, 11/08):** o 1º `designate` real (Cam Ward → Trust The Process)
abortou correto e barulhento com **mapa slot↔owner VAZIO** — diagnóstico contra a API viva:
`draft_order` é **None** no draft `pre_draft` pós-RESET, **mas `slot_to_roster_id` está presente
e completo**, e `/league/rosters` dá roster→owner. **Cadeia de resolução implementada**
(`core.resolve_slot_map`, pura): (a) `draft_order` quando presente → (b)
**`slot_to_roster_id` × rosters** (API pura, sem ambiguidade — resolve o caso real) → (c) slots
observados nos picks; esgotou → **abort nomeando a fonte que faltou** + último recurso
`--team-slot N`. A confirmação final segue sendo **o menu do DOM ("for Team {N}")** dentro do
fluxo — confirmação, nunca fonte primária. A **fonte usada vai ao relatório JSON**
(`slot_map_source`). **De carona, um achado do diagnóstico: o check de owner do `validate`
estava INERTE** (mapa vazio → `slot_owner=""` → a comparação nunca disparava; os "18/18" valiam
para sid+salário, não para owner) — com a cadeia, o `validate` passa a conferir owner de
verdade. Testes 36 → **42** (cadeia com fixtures no formato real medido, incluindo o par
Cam Ward/michelzela do abort).

**FIX4 (MAN-OFF26-24-F2a-FIX4, 11/08):** o designate seguinte expôs, pelo call log, que a
**ordem do DOM das células não corresponde a colunas** — `[id^='draft-cell']` nth(1) caiu numa
célula **preenchida** do MellowBR, abriu **"Change Player"** e o underlay interceptou 30s de
retries até timeout (zero picks novos — nada alterado); e o handler crashou com
`UnboundLocalError: 'ok'` em vez do abort limpo. Três fixes: **(1) navegação POR COLUNA** — a
N-ésima `.team-column` (12 no DOM) → primeira `.cell` sem `.drafted`; a ordem é candidata e **o
menu segue decidindo** ("for Team {N}", agora julgado pelo núcleo puro `choose_menu_item`, com o
N casando por **fronteira** — "Team 1" não casa slot 10); qualquer outra coisa → Escape + abort
(nada de varrer células). **(2) "Change Player" virou proibição** (lista + decisão própria no
menu: célula preenchida = célula errada, nunca prosseguir). **(3) `ok` nasce antes do try e
QUALQUER exceção produz o abort padrão** (screenshot + relatório + evento no log) — o crash do
handler não engole mais o abort. Testes 42 → **50** (menu decidido com o call log real como
fixture; guardas estáticas: coluna-nunca-nth-global, CHANGE PLAYER na lista, handler sem
crash).

**FIX5 (MAN-OFF26-24-F2a-FIX5, 11/08):** a run seguinte avançou por TODO o caminho (mapa ✓
coluna ✓ célula ✓ menu "for Team 10" ✓ busca ✓) e abortou no anti-homônimo com **"0 candidatos
QB" — com o Cam Ward na própria lista do abort** (`'QB
TEN TEN'`). Bug de **parsing, não de
busca**: o innerText real vem **empilhado por newlines**, com **sigla duplicada** e **status de
injury concatenado** (`'RB
DET
QUES DET'`) — o matcher esperava o formato limpo do ensaio.
Fix: **`parse_result_row` + `select_candidate_rows` no núcleo puro** — tokenização por
whitespace, posição = vocabulário, sigla = 2-3 maiúsculas fora dele (QUES/OUT caem por
tamanho); **o critério NÃO relaxou** (posição exata; 0 ou 2+ candidatos abortam; sigla é logada
p/ conferência humana — a sheet não a carrega) e **o "+" clicado é o da linha ELEITA**
(`rows.nth(idx)`), nunca a primeira. Testes 50 → **60** — as linhas LITERAIS do abort são
fixture (Cam Ward acha exatamente 1 QB; 2 homônimos seguem abortando).

**FIX6 (MAN-OFF26-24-F2a-FIX6, 11/08):** o parser novo funcionou — sobre a lista ERRADA: as 57
linhas parseadas eram o **ranking de FUNDO da página** (todas as posições, 5 QBs), não o
resultado do modal ("5 candidatos QB" → abort correto, que recusou clicar QB aleatório). Fix:
**tudo escopado ao CONTAINER do modal** (`_modal` — o menor ancestral do botão "Assign a
player"/"SET PLAYER" que contém o input de busca, ancorado por estrutura): busca, linhas, "+" e
preço; ⛔ nenhum locator global sobrevive (guarda estática). E **o efeito da digitação é
conferido ANTES do matching** (`search_filter_check`, núcleo puro: dezenas de linhas = fundo/
busca não aplicada → abort "busca não filtrou" — o caso das 57 é fixture). Anti-homônimo
intacto. Testes 60 → **65**; README com a instrução do probe para o wrapper do modal.

**FIX7 (MAN-OFF26-24-F2a-FIX7, 11/08):** a heurística do FIX6 achou o trio **do fundo** — o
call log + screenshot provaram que o manual pick vive num **`<div id="modal"
role="alertdialog">`** (header **"Make Manual Pick for Team 10"** dentro dele, o sinal do
ensaio) e a página de fundo **duplica** input/lista/botão; o input resolvido ficou FORA do
dialog aberto, com o underlay interceptando 30s. Fix: **âncora no `#modal` quando presente**
(a heurística de ancestral vira FALLBACK, logada como `ancestral_fallback` no relatório);
**espera de ESTADO** pelo modal após o Set Player (não sleep; não abre → abort "modal do
manual pick não abriu"); e o **header vira verificação de identidade** (núcleo puro
`modal_header_check`: time errado → abort; dialog sem o header — residual/aviso → **Esc +
abort nomeando o conteúdo**). O caso do abort é impossível por construção: o escopo nasce do
próprio `#modal`. Testes 65 → **66**.

**F2a FECHADA (11/08, placar real):** 1 designação real **assentada e confirmada pela API** (Cam
Ward $1 → Trust The Process), `validate` **19/19 com zero divergências**, mapa vivo pela cadeia.
**A lição final, descoberta na própria pele:** o pick GRAVOU numa run intermediária que morreu
antes do poll (o desync do ensaio mordeu o script) e a run seguinte gastou um ciclo com "busca
vazia misteriosa" — jogador designado **some do pool designável**. Consequência de desenho:
**idempotência é a PRIMEIRA verificação, não a última.**

#### F2b — entregue (MAN-OFF26-24-F2b, 11/08/2026): loop completo + idempotência + auditoria como juiz

- **Idempotência pré-designação** (`core.idempotency_decision`, 4 casos + o de amount ausente):
  antes de QUALQUER clique, o sid é conferido nos picks da API — já assentado no time/preço certo
  → `ja_assentado` (sucesso, zero cliques); divergente → **conflito** (aborta o time, decisão
  humana); ausente → designa. E **"lista vazia após filtro" re-checa a API antes de abortar**
  (`EmptySearchResult` no driver — o desync corre; só vira abort se a API confirmar ausência).
- **Loop por time** (`populate --team-slot N`): designa os faltantes em sequência; ao fim,
  **conferência contagem+soma contra a sheet via API**; falha num keeper → **aborta O TIME** com
  o que assentou preservado (o modo de falha do runbook), sem contaminar os demais.
- **Campanha** (`populate --all`): 12 times em ordem de slot, pulando os completos —
  **retomável por construção**. `bloqueado_teto` ("does not have enough budget", §B.3.2 —
  casos reais: AlexTheDawg $203, Miller Time! $200) é **resultado esperado** pré-late-drop:
  registra e segue; o exit code o trata como não-falha.
- **O juiz independente:** o relatório instrui a **auditoria OFF26-4** (`/admin/keeper_audit`)
  sobre o board populado — o veredito é dela, não da contagem do script. Relatório JSON com o
  placar por time (designados/ja_assentados/bloqueados/falhas) + resumo da campanha.
- **Critério de 19/08 no README:** RESET (owner) → `populate --all` com sheet provisória
  (12/12 processados, zero intervenção) → auditoria coerente → RESET final (rollback provado).
- **Testes 66 → 86** (idempotência 5, plano/retomabilidade 3, teto 2, campanha 2, header do
  modal 3 — os do FIX7 que faltavam —, + 5 guardas estáticas: idempotência-antes-do-designate,
  recheck da busca vazia, teto não-erro, falha não contamina, populate sem RESET/START). Suítes
  verdes. ⚠️ O loop em navegador real é o ensaio do owner — o critério de 19/08.

**FIX8 (MAN-OFF26-24-FIX8, 11/08): o assentamento vira ASSÍNCRONO — o lag real matou o poll
bloqueante.** O teste morno provou o defeito da impaciência: o pick do Josh Allen ($30, preço
editado certo — o caminho >$1 provado de brinde) **gravou na hora** e a API pública levou
**>5 MINUTOS** para refleti-lo (validates 16:54→19 picks, 16:57→20, tudo casado); o poll de 15s
desistiu de um sucesso lento → retry → busca vazia (o board local, CERTO, já escondia o
designado) → abort falso. No ensaio o lag fora ~3s — **a variância é o fato central**. ⚠️
Hipótese do owner em teste (tarefa 7): a propagação pode depender de **visita de cliente**
(cache preguiçoso) — o validate que viu 20 rodou logo após abrir o board num navegador.

- **`command_pick`** — comanda (menu→busca→+→preço→SET PLAYER) e **segue sem poll**
  (`pendente_confirmacao`; o board local preenchendo a célula é o feedback); a recusa de TETO
  continua síncrona (o aviso é imediato).
- **`reconcile_team`** — reconciliação POR TIME: teto generoso (300s, poll 5s), **reload do
  board no MEIO do teto** com pendência viva (a visita do próprio script como possível gatilho
  do cache — tarefa 7) e **telemetria por keeper** (`segundos_apos_comando` + `apos_reload`):
  fila contínua = lag puro; rajada pós-reload = cache por visita. O achado redefine a espera
  de 22/08.
- **`post_teto_decision` (núcleo puro)** — pendente que não apareceu: board local o mostra
  designado → **`assentado_local_api_atrasada`** (aviso; ⛔ nunca re-comandar); disponível →
  **1 re-comando** + mini-reconciliação (60s); esgotou → falha **do keeper**, preservando o
  resto do time.
- **Idempotência em LOTE** (`classify_team_keepers`) antes do 1º clique; **busca vazia cruza
  run própria → API → board local** antes de abortar (tarefa 5 — `sumiu_da_busca_pos_comando`).
- **Testes 86 → 87** (simulador puro de reconciliação com lags 3s/40s/6min, decisão pós-teto,
  lote, + guarda estática do assíncrono: reload no meio, telemetria, poll bloqueante morto).
  Suítes verdes. Re-teste morno do owner: `populate --team-slot 10` → 2 no lote de
  ja_assentados + 19 comandados + reconciliação fechando o time — e a telemetria respondendo
  a hipótese do cache.

**FIX9 (MAN-OFF26-24-FIX9, 12/08): a campanha real expôs dois defeitos encadeados — o abort de
time deixava o MODAL aberto (crash cru no time seguinte) e o anti-homônimo contava OUTROS
jogadores como candidatos.** Run `populate_20260812T131804Z` (`--all`): idempotência em lote
funcionou (53 ja_assentados, zero cliques, board íntegro no validate) — e a falha no slot 3
derrubou o processo com traceback cru.

- **Diagnose do parser (screenshot `abort_slot3.png`): NÃO era artefato de DOM** (família FIX5
  descartada). A busca do Sleeper é **FUZZY**: "Malik Willis" devolveu 4 linhas REAIS — o alvo
  (QB·MIA) e três FAs de sigla vazia (Malik Williams WR, Malik Williams RB e **Hajj-Malik
  Williams QB** — o "segundo QB" do abort). O parse do FIX5 estava certo; faltava o **NOME** no
  critério de candidato. `select_candidate_rows_named` (núcleo puro): candidato REAL = posição
  exata (critério intacto) **E** nome buscado como sequência de tokens do texto da linha
  (`row_matches_name` — normaliza acentos/caixa/pontuação; hífen preservado: "Hajj-Malik" não
  casa "Malik"). ⛔ **Sigla vazia NÃO desqualifica** — FA real é linha legítima (filtrar por
  sigla excluiria keeper cortado da NFL). 0/2+ candidatos REAIS seguem abortando.
- **Higiene de estado (o crash):** o abort do anti-homônimo saía de `_pick_search_result` com o
  SET PLAYER aberto — o clique do time seguinte foi interceptado por `#modal[role=alertdialog]`
  por 30s até um TimeoutError que escapou **cru** (o loop de keepers só capturava
  BoardAbort/EmptySearchResult), violando a garantia do FIX4. Agora: `command_pick` fecha
  menu/modal em **QUALQUER** exceção (`_dismiss_modal`, melhor esforço, nunca levanta) e
  `_open_set_player_menu` **verifica estado sujo ANTES do 1º clique** (modal residual → Escape
  até limpar; não limpou → abort barulhento, nunca clicar através).
- **Cobertura do handler de crash:** exceção crua num keeper → **abort padrão do TIME**
  (screenshot `abort_slot{N}.png` + evento `falha_do_time`) e a campanha segue; crua fora do
  loop → **abort padrão da CAMPANHA** (`abort_campanha` no relatório + screenshot); falha do
  `open_board` → mensagem limpa via sys.exit. `settle_pendentes` idem (cru = falha DO KEEPER,
  resto do time preservado). O time entra no relatório ANTES de processar — falha não o apaga.
  Exit code: fatal → 1.
- **Réplica conferida (pergunta obrigatória da diagnose):** a lógica de parsing/contagem de
  candidatos vive SÓ em `core.py` — `board.py` é o único consumidor e os testes usam as funções
  reais (zero reimplementação em validate/helpers).
- **Testes 87 → 104** (fixture LITERAL do abort: 4 linhas → exatamente 1 candidato QB real;
  homônimos reais de mesmo nome+posição seguem dando 2; sigla vazia conta com o nome certo;
  textos ausentes não degradam para posição-só; + guardas estáticas: command_pick limpa em todo
  abort, estado sujo detectado pré-clique, eleição por nome, populate sem traceback cru, settle
  não derruba o time). Suítes verdes.

**FIX10 (MAN-OFF26-24-FIX10, 12/08): as DUAS caras do teto — o clamp silencioso do input,
detectado por read-back ANTES do SET PLAYER; conferência que aponta os picks; caso Travis
Hunter diagnosticado (two-way).** Run `populate_20260812T142940Z`: **12/12 times processados**,
147 designados + 74 já assentados; FIX9 validado em produção (Malik Willis designado entre 4
linhas; o abort do slot 11 não contaminou o slot 12 — higiene provada). Dois defeitos restantes:

- **Teto silencioso (slot 12, AlexTheDawg, sheet $203 > budget $200).** O Sleeper **CLAMPA o
  input de preço ao max bid sem aviso**: o script digitou $6/$4/$3/$2 e o board gravou
  $5/$1/$1/$1 ($196 no total) — detectado só na conferência de totais, tarde e sem apontar
  quais. Preço errado no board é divergência de severidade ALTA na doutrina OFF26-4 — pior que
  ausência, porque parece certo. **Modelo verificado ao dólar** contra os 4 clamps e o total:
  `max_bid = budget − gasto − $1 × (vagas vazias restantes do board de 22)` (`core.max_bid`;
  budget/slots derivados do próprio draft via `draft_budget_slots`, fallback $200/22).
- **Fix: read-back do input** (`parse_price_value` + `price_readback_decision`, puros) — após
  digitar, o valor EFETIVO é lido de volta (a **verdade operacional**; o max_bid do modelo é
  anotação de motivo no relatório): clampou → **SET PLAYER NÃO acionado**, modal fechado,
  keeper vira `bloqueado_teto` com os números (`clamp_do_input`: preco_sheet × preco_efetivo ×
  max_bid_modelo); read-back ilegível/maior → abort barulhento. ⛔ **A sheet é canônica — o
  script nunca grava preço diferente dela.** A recusa síncrona (§B.3.2) segue coberta, logada
  como `recusa_sincrona` — mesma classe, sem semântica paralela.
- **Grão do teto corrigido: pula O KEEPER, não o time** ($1 sempre cabe na reserva — o resto do
  time é alcançável). `bloqueados_teto` contado por keeper no resumo; os pulados saem da
  expectativa da conferência (campo `bloqueados_excluidos`).
- **Conferência aponta os picks** (`core.conference_report`, substitui a soma inline do CLI):
  divergente vira **nome + esperado + gravado** no relatório E no stdout; faltante nomeado.
- **Telemetria da run (tarefa 7):** 147 assentamentos, **todos `apos_reload: false`**, lag
  8–121s decrescendo linearmente dentro de cada time — **perfil de fila contínua (lag puro)**;
  evidência contra a hipótese do cache por visita (nenhum reload foi necessário).
- **Caso Travis Hunter (parecer read-only, slot 11):** o **único two-way entre os 237 keepers
  da sheet** — API viva e cache F13 concordam: `position: "WR"`, `fantasy_positions:
  ["DB","WR"]` (DB PRIMEIRO no array), Active/JAX. O modal devolveu 0 linhas (cross-check
  triplo run→API→board confirmou ausência real; os 6 comandados anteriores do mesmo time
  assentaram, lag 8–38s). A API prova a **classificação**, não o **mecanismo do pool da sala**
  → ⛔ sem tratamento cego: **pendência nomeada OFF26-24-HUNTER** com micro-probe manual (ver
  abaixo). Enquanto não tratado, a campanha volta a parar o time do achane nele (11 keepers
  depois dele ficam sem tentar).
- **Réplica conferida (pergunta obrigatória):** leitura/validação de preço só existe em
  `_set_price_and_confirm` (o read-back nasceu lá); interpretação de busca só em
  `_pick_search_result` → núcleo; a comparação sheet×board tinha DUAS implementações
  (`match_picks_to_sheet` no validate + soma inline do CLI) → a do CLI virou
  `conference_report` no core, e guarda estática recusa `def _team_conference` de volta.
- **Testes 104 → 121** (fixture aritmética REAL do AlexTheDawg: 4 clamps nos keepers certos e
  total $196; com detecção → 16 designados a preço de sheet + 2 bloqueados (Keenan $6, Kaleb
  $3) e ZERO preço errado no board; read-back decision; conference_report nomeando divergentes/
  faltantes/excluídos; bloqueados por keeper no resumo; guardas estáticas: read-back antes do
  confirm.click, teto pula o keeper, conferência exclui bloqueados). Suítes verdes.

**Pendência OFF26-24-HUNTER — ✅ FECHADA 12/08 pelo micro-probe do owner (screenshots) + FIX11.**
Resultado do probe: o Hunter **ESTÁ no pool da sala** — aparece na busca por "travis hunter" (1
linha) e por "hunter" (múltiplas, ele entre elas), **rank 167, tabs All E WR, "+" habilitado** —
designável manualmente; a classe `fora_do_pool_da_sala` **não se aplica**. O rótulo de posição
da linha é **"DB,WR"** (multi-posição, espelho de `fantasy_positions` da API). Mecanismo real do
abort: a busca devolveu a linha e a **eleição a descartou** — exigia posição EXATAMENTE igual à
da sheet ("WR" ≠ "DB,WR") → 0 candidatos → o caminho de lista-vazia cruzou a API (sem pick) e
abortou como "busca vazia sem rastro", **mascarando que o candidato existia**. Tratamento: FIX11
(abaixo).

**FIX11 (MAN-OFF26-24-FIX11, 12/08): matching de posição por PERTENCIMENTO — rótulo
multi-posição "DB,WR" casa a posição da sheet.** Fix inteiro no núcleo puro, board/CLI intocados:

- **`position_matches` (novo):** a posição da sheet casa se for **membro do conjunto** do rótulo
  da linha (separadores `,` e `/`), com igualdade cobrindo o caso comum ANTES do split (preserva
  "D/ST" como rótulo único). **Pertencimento não é afrouxamento:** "QB" segue não casando
  "DB,WR". `select_candidate_rows` (FIX5) passou a usar — fonte única do critério.
- **Parse (família FIX5) preservado e estendido:** token compound é reconhecido como rótulo de
  posição se 2+ partes e ao menos UMA no vocabulário ("DB" não precisa estar), e devolvido
  **ÍNTEGRO** ("DB,WR"), nunca quebrado em posição+sigla; a sigla (JAX) segue saindo ao lado.
- ⛔ **Critério do anti-homônimo intacto:** nome como sequência de tokens (FIX9) + posição da
  sheet pertencente à linha; 0 ou 2+ candidatos reais seguem abortando (dois "Travis Hunter"
  com rótulos contendo WR → 2 → abort, testado).
- **Réplica conferida (pergunta obrigatória):** a comparação de posição existia num único lugar
  (`core.select_candidate_rows`, o `pos == want` da linha 270) — `keeper_audit.py` só carrega
  posição como display (identidade por sid), o validate casa por sid, o CLI repassa, os testes
  usam as funções reais. O fix criou `position_matches` como fonte única.
- **Testes 121 → 134** (fixture literal do probe: "Travis Hunter"/"DB,WR"/JAX + sheet WR → 1
  candidato; sheet QB → 0; busca "hunter" multi-linha → só ele; homônimos verdadeiros → 2;
  parse do rótulo íntegro com sigla/injury; compound sem membro do vocabulário não vira rótulo;
  FIX5/FIX9 sem alteração de expectativa). Suítes verdes.

#### GO — critério de 19/08 CUMPRIDO (MAN-OFF26-24-GO, 12/08/2026): script promovido a PLANO A

**O ciclo limpo oficial rodou em 12/08 e cumpriu o critério integralmente, 7 dias antes do
prazo.** Arco do dia: campanha noturna interrompida por suspensão da máquina → diagnose via
validate (74 picks íntegros — a interrupção não corrompeu nada) → **FIX9 → FIX10 → FIX11**,
cada um nascido de falha REAL de campanha (commits `82f31bb` · `01c8e0b` · `c06b0c5`) → RESET →
**campanha oficial** (`populate_20260812T185453Z`) → auditoria OFF26-4 → alocação de owners →
RESET final.

- **Campanha oficial: 12/12 times processados, 235 designados + 2 `bloqueado_teto`, 0 falhas,
  zero intervenção manual.** Os 2 bloqueados são exatamente os declarados do AlexTheDawg
  (Keenan Allen $6 e Kaleb Johnson $3; sheet $203 > budget $200) — e o grão por keeper do FIX10
  fez o **Croskey-Merritt entrar a $4 DE SHEET** (pular o Keenan liberou teto, como o modelo
  previa). **Travis Hunter designado** (FIX11 em produção).
- **Auditoria OFF26-4 (o juiz independente): 2 divergências — exatamente os 2 bloqueados
  declarados; ZERO salário divergente; 12/12 populados**; banner de conferência antecipada
  correto (sheet provisória — OFF26-22).
- **RESET final exercido** (rollback provado, não presumido): validate pós-reset com **0 picks
  vivos, 237 keepers na sheet e draft_id NOVO derivado** — o **3º da sessão**, sem persistência
  em lugar nenhum (a doutrina D1 do OFF26-4 provada três vezes no mesmo dia).
- **Descoberta operacional — ALOCAÇÃO DE OWNERS (owner, 12/08):** feita em **Draft Settings →
  DRAFT ORDER** da liga fantasma (12 owners nos slots 1-12: MellowBR, rafadgil, TropadoJarra,
  icarocosta1, rafaelferreirap, fernandoxmf, murilofborges, LeoFBorges1, fertorquato,
  michelzela, gabrieldiinis, freddupont — conferida na tela E no validate). Efeitos
  verificados empiricamente: (a) o mapa slot↔owner do script passou a derivar de
  **`draft_order`** (a fonte (a) da cadeia FIX3, autoritativa) em vez de
  `slot_to_roster_id×rosters`; (b) a alocação **SOBREVIVE ao RESET DRAFT** — é configuração
  PERMANENTE da liga, não passo anual; (c) a tela contém **RANDOMIZE** (⛔ embaralharia os
  owners — sob board populado corromperia todas as colunas) e **RESET BUDGETS** — **ambos
  entram na lista de ações proibidas junto do START DRAFT** (registrados no runbook; a tela
  não é aberta pelo script — proibição HUMANA).
- **Telemetria consolidada (tarefa 7): 382 assentamentos em duas campanhas, ZERO reload,
  perfil de fila contínua (lag puro)** — a hipótese do cache por visita fica desfavorecida; a
  espera de 22/08 confia na reconciliação assíncrona do FIX8 como está.
- **Planos invertidos (decisão do owner):** `tools/phantom_board/` = **PLANO A** da população
  real de 22/08 — ordem no README: **conferir alocação → `populate --all` → auditoria OFF26-4
  → não tocar RANDOMIZE/RESET BUDGETS/START DRAFT**; `runbook_cowork_liga_fantasma.md` =
  **plano B/contingência** (cabeçalho atualizado com rebaixamento + conferência de alocação +
  proibições).

#### F1 — diagnose read-only (10/08/2026)

##### Q1 — Arquitetura: Playwright (Python) headed, na máquina do owner, perfil dedicado logado

**Recomendação: Python + Playwright**, rodando **headed** no PowerShell do owner. Racional:
- **Playwright > Selenium** para esta UI: auto-wait embutido (o board reescala e anima — a
  espera explícita do Selenium seria o grosso do código), seletores por role/texto de primeira
  classe e `trace viewer` para depurar falha do ensaio sem re-rodar.
- **Headed, não headless:** quem executa é o owner — ver a run acontecer é parte do modo de
  falha (parar barulhento + operador presente); e UI logada do Sleeper em headless é convite a
  detecção/comportamento divergente sem ganho nenhum (a run é 1× por ciclo, não um batch).
- **Login: perfil PERSISTENTE dedicado** (`launch_persistent_context(user_data_dir=<pasta
  própria>)`): o owner loga manualmente UMA vez nessa janela; a sessão persiste no perfil;
  **zero credencial no script, zero 2FA automatizado**. ⛔ Não usar o perfil principal do Chrome
  (Playwright não dirige um Chrome já aberto, e misturar perfis é fonte de sessão derrubada).

##### Q2 — Insumos do Manager: a sheet é legível, mas o payload JSON NÃO tem sid nem owner_id

- **`GET /api/cuts/keeper_sheet`** (`@admin_required`, `routes/cuts.py:513-516`) devolve por
  time: `team_id, team_name, fa_budget, num_keepers, num_ir` e `keepers[{id, name, position,
  salary, is_on_ir}]` + `stage`/`sync_timestamp`/`late_drop`. ⚠️ **Sem `sleeper_player_id` no
  keeper e sem `sleeper_owner_id` no time** — decisão **D3** registrada no próprio
  `keeper_audit.build_sheet` (`keeper_audit.py:488-495`): o enriquecimento é feito por
  **re-query**, não no payload da sheet.
- **A ponte owner↔coluna existe** (`Team.sleeper_owner_id`, M12 — `models.py:91`) e o
  `build_sheet` da auditoria já entrega **exatamente o pacote que o script precisa** (keepers
  com sid + `sleeper_owner_id` por time). **Parecer para a F2:** expor o `build_sheet` ao script
  (endpoint admin fino OU dump local) em vez de re-derivar — ⛔ **nenhuma segunda definição de
  "quem é keeper"** (a guarda do OFF26-11 vale aqui).
- **O que o script deriva sozinho:** o **`draft_id`** — redescoberto a cada uso pela **API
  PÚBLICA documentada da liga** (o objeto da liga o carrega; mesmo caminho D1 do OFF26-4, 1
  request read-only). ⛔ Isso NÃO é a API interna vetada — é a mesma chamada que a auditoria já
  faz em produção. E o **handle do owner na coluna** (estado com owners reais) casa com
  `Team.owner_name`/`sleeper_owner_id` do Manager.

##### Q3 — O mundo que o Code não vê: o que o runbook já fixou × o que SÓ o ensaio de 11/08 responde

**Já fixado pelo runbook OFF26-5 (2 execuções, correções contra a UI real):** `draft_id` muda a
cada RESET (URL velha trava em LOADING — redescoberta obrigatória); coluna identificada pelo
**owner** (estado real) ou pelo **menu de contexto** "Manually set a player for Team N" (estado
placeholder); fluxo célula → **Set Player** → busca → **"+" da linha, NUNCA o nome** (o nome
abre perfil e **cancela o fluxo inteiro**); **K/DEF abaixo da dobra**, revelados pela **seta ▼**
(scroll do mouse não move o board); o board **reescala após a 1ª interação** (referência
posicional quebra — mas **a vaga é atribuída POR POSIÇÃO**, então o que importa é a coluna);
**preço nasce $1 SEMPRE** (mesmo com $PROJ maior) e edita por **Ctrl+A + digitar**; K/DEF já
designados **somem do filtro**; anti-homônimo = **posição + sigla NFL** na linha do resultado
(o pool de designação só traz ofensivos elegíveis).

**O que SÓ o ensaio de 11/08 responde — a lista que vira spec (anotar TUDO):**
1. **Seletores/DOM reais** de cada elemento do fluxo: cabeçalho de coluna (onde vive o handle),
   itens do menu de contexto, campo "Find player Ctrl+U", linha de resultado (sub-elementos de
   nome/posição/sigla), o **"+"**, o preço "$ 1", o botão **SET PLAYER**, a seta **▼**, os
   filtros de posição.
2. **Atributos estáveis existem?** `data-*`/`aria-*`/testids × classes hasheadas × só texto
   visível — decide a estratégia da Q4.
3. **O board vive num iframe?** E as listas (colunas/resultados) são **virtualizadas**? (os dois
   mudam o código Playwright de cara).
4. **O que é "assentado"** depois do SET PLAYER: atualização síncrona da célula? toast?
   animação? — define o critério de espera pós-designação.
5. **Ofensivo já designado some da BUSCA** (como K/DEF somem do filtro)? — define o teste de
   idempotência/retomada.
6. **Menu de contexto no estado com owners reais:** o texto vira o nome do owner ou continua
   "Team N"? — define a âncora da verificação de coluna.
7. A **URL do board** navegável direto (`draft/<draft_id>`?) e o caminho liga → board pela UI.

##### Q4 — Robustez: texto visível como âncora, falha barulhenta, checkpoint por time

- **Seletores: texto visível primeiro** (getByRole/getByText nos rótulos de que a própria
  operação depende: "Manually set a player for", "Assign a player", "SET PLAYER"). Evidência a
  favor: entre junho e agosto a UI mudou **layout/posições** (reescala, dobra) — mas **os textos
  do fluxo sobreviveram** (as correções 🔧 do runbook são todas de posição/estado, nenhuma de
  rótulo). ⛔ **Posicional nunca** (o board reescala — documentado). Atributos só se o ensaio
  mostrar testids estáveis (classes hasheadas de SPA não contam).
- **Modo de falha: parar BARULHENTO no primeiro erro** — antes de cada ação, assert do estado
  esperado (o menu de contexto cita o time certo? a linha do resultado tem a posição+sigla
  esperadas?); qualquer mismatch → aborta com screenshot + trace. ⛔ Nunca "seguir tentando".
- **Relatório e retomada:** log JSON por designação (time, jogador, preço, timestamp); **a
  unidade verificável do runbook (o time) vira o checkpoint** — `--from-team` retoma do time N;
  ao fim de cada time, conferência local contra a sheet (contagem + soma) antes de seguir.

##### Q5 — Validação: a auditoria OFF26-4 é o verificador independente que já existe

- **Ensaio:** na fantasma, com a **sheet provisória** (dado real, zero escrita que importe — o
  board inteiro é descartável por RESET DRAFT).
- **Conferência automática em duas camadas:** (1) o próprio script, por time (contagem+soma vs
  sheet); (2) **a auditoria OFF26-4 rodada SOBRE o board populado** — ela compara o board lido
  ao vivo com a sheet, classe a classe, e **já existe** (⛔ nenhum verificador novo a escrever;
  sobre sheet provisória ela roda e desqualifica o veredito de gate — o que para o ENSAIO é
  irrelevante: o que se lê são as divergências, não o gate).
- **"Validado até 19/08" (proposta, endurecendo a do prompt):** 12/12 times populados em ensaio
  + **auditoria OFF26-4 sem NENHUMA divergência** (keeper ausente/salário/time errado zerados) +
  **zero intervenção manual** durante a run + **RESET DRAFT exercido ao final** (o rollback
  provado, não presumido). Qualquer item faltando em 19/08 → Cowork em 2026, script para 2027.

##### Q6 — Fronteiras

- **Auditoria pré-leilão: OFF26-4 segue dona** — o script a USA como verificador, não a replica.
- **Quando popular: runbook/calendário** — o script executa, não decide.
- ⛔ **Guarda de nascença:** `league_id 1389725099556372481` **hardcoded**; o script (1) resolve o
  draft SÓ a partir dessa liga e (2) confere o nome da liga na página antes do primeiro clique —
  qualquer outra coisa → recusa seca. **Nunca clicar START DRAFT** entra na lista de ações
  proibidas do código.
- **Zero escrita fora da liga fantasma**; o Manager não é tocado (o script só LÊ a sheet).

#### Plano de F2 (fases batendo em 19/08)

| Fase | Quando | Entrega | Gate |
|---|---|---|---|
| Insumo | **11/08** | Ensaio Cowork anota a lista da Q3 (seletores/DOM/iframe/virtualização/assentamento) | Sem a lista, F2a não começa |
| F2a | 12–13/08 | Esqueleto: lê a sheet (via `build_sheet` exposto), descobre o draft pela API pública, navega ao board, **guarda de league_id**, designa **1 keeper de $1** num time, RESET | 1 designação correta + rollback provado |
| F2b | 14–15/08 | Loop por time com checkpoint, preços editados (Ctrl+A), K/DEF via filtro, relatório JSON; **ensaio 12/12** + auditoria OFF26-4 zerada + RESET | O critério da Q5, primeira passagem |
| F2c | 16–19/08 | 2ª passagem limpa do ensaio ponta-a-ponta (repetibilidade) + correções | **19/08: go/no-go do owner** |

**Cross-refs:** [[OFF26-5]] (o runbook Cowork — plano A e fonte da anatomia), [[OFF26-4]] (a
auditoria como verificador; D1 = o mesmo caminho de descoberta do draft), [[OFF26-11]] (⛔ nenhuma
segunda definição de keeper — a sheet/`build_sheet` é a fonte), [[OFF26-2]] (a sheet), M12 (a
ponte `sleeper_owner_id`).

---

### OFF26-19 — Jogador em IR no Ano 4 não aparece como candidato a renovação
🔲 **Pendente** — Prioridade **Baixa** — achado do [[OFF26-16]], registrado em `MAN-IR-CLEANUP` (04/08/2026)

**Mecanismo.** Em [routes/roster.py](routes/roster.py), `renewal_candidates` deriva de
`active_players` — a lista que **exclui quem está em IR**:

```python
active_players = [p for p in all_players if not p.is_on_ir]
...
"renewal_candidates": [p for p in active_players if p.is_renewal_candidate()],
```

É **herança do mesmo filtro de IR** que o [[OFF26-16]] removeu das telas de cap. Lá o filtro foi
eliminado porque falseava a folha; aqui ele sobreviveu porque **não é pergunta de folha, é de
contrato** — e por isso ficou fora daquele escopo, deliberadamente.

**Dano potencial.** Um jogador **em IR no Ano 4** não aparece no aviso *"N jogador(es) no Ano 4 —
renovar ou cortar"*. O contrato expiraria **sem decisão registrada**, e o salário seguinte sairia
errado. **Dano silencioso**, da mesma família do discriminador keeper × arremate ([[OFF26-11]]):
não há erro visível, há uma decisão que ninguém foi convidado a tomar.

**Por que o perfil de risco é justamente esse:** fim de contrato **+** lesão é exatamente o caso que
mais exige decisão de renovação — o owner precisa escolher entre renovar por 4 anos ao valor ESPN ou
cortar. É o cruzamento que o filtro esconde.

**Dano HOJE: zero — verificado.** Não há nenhum jogador no Ano 4 na liga. A distribuição inteira é:

| contract_year | jogadores |
|---|---|
| ano 1 | 50 |
| ano 2 | 198 |
| **ano 4+** | **0** |

⇒ com a liga toda em anos 1-2, o primeiro Ano 4 só pode existir depois de **dois** rollovers. **Há
folga real** — é o que sustenta a prioridade Baixa apesar de o bug tocar salário.

**Mas é atemporal:** em qualquer intertemporada futura, jogador machucado em fim de contrato some do
fluxo. O bug não caduca, só está adormecido.

**Não corrigido aqui, de propósito.** A correção toca o **fluxo de renovações** e merece **F1
própria** quando for priorizada — em particular: o `is_renewal_candidate()` deve valer para jogador
em IR (provavelmente sim), e o mesmo filtro pode existir em outras superfícies de contrato (o
[[OFF26-16]] só varreu as de folha).

**Cross-refs:** [[OFF26-16]] (removeu o filtro irmão das telas de cap e expôs este), [[IR-CLEANUP]]
(mesma sessão), [[OFF26-11]] (mesma família de dano silencioso em contrato).

---

### OFF26-20 — Contrato carregado indevidamente em 29 free agents + coluna PROJ divergente
⚠️ **DADO ✅ EM PROD (22/22) · ENUM + PROJ IMPLEMENTADOS · Bryant/censo resolvidos — resta smoke pós-deploy** — Prioridade **Alta (prazo 18/08)** — `MAN-OFF26-20-F1` (04/08) → **`-F1B`** (05/08, inverte) → **`-F1C`** (05/08, **corrige o critério: o discriminador é o CANAL, e o problema cai de 73 para 29**) → **`-VERIF`/`-CANAL`** (05/08, grupo fecha em 22, aprovação nominal do owner) → **`-FIX`** (06/08, porta canônica + ensaio + **execução em prod pelo owner: 22/22**) → **`-CLOSE`** (06/08, **enum `fa_waiver` + PROJ na fonte única + Bryant/censo fechados**)

⚠️ **A hipótese do owner foi FALSIFICADA, e o achado é maior que o rótulo.** O rótulo ambíguo não é
cicatriz de importação: são **jogadores em Ano 1 com a bifurcação de regra PENDENTE**. E, ao medir,
apareceu um segundo problema **independente e maior** — a coluna PROJ das telas de roster usa uma
função que **mais nada usa**, e que discorda do rollover em **26 dos 248 jogadores**.

#### T1 — Censo dos rótulos e sua procedência

**Procedência:** o valor vem do campo `Player.acquisition_type` (banco). O rótulo é traduzido por
`_ACQ_LABELS` — **dict único** em [routes/roster.py:343](routes/roster.py#L343), consumido em três
pontos (`roster.py:85`, `league.py:90`, `roster.py:394`). **Não há derivação em template nem
fallback do sync.** O truncamento *"Waiver / Free A…"* é **puro CSS** (`td.col-acq` com
`text-overflow: ellipsis`), com o texto completo no `title` — **não é problema de dado**.

| `acquisition_type` | rótulo exibido | total | ano 1 | ano 2 |
|---|---|---|---|---|
| `auction_draft` | Startup Auction | 96 | — | 96 |
| `free_agent` | **Free Agent** | 39 | 10 | 29 |
| `fa_waiver` | **Waiver / Free Agent** ← *o ambíguo* | 37 | **5** | 32 |
| `rookie_draft` | Rookie Draft | 31 | 31 | — |
| `fa_auction` | FA Auction | 28 | **4** | 24 |
| `waiver` | **Waiver** | 17 | — | 17 |

#### T2 — Hipótese do owner: ⛔ FALSIFICADA

A hipótese era que todo `Waiver / Free Agent` estivesse em **Ano 2+**, com a bifurcação já ocorrida
(cicatriz benigna). **Há 5 em Ano 1** — bifurcação **pendente**, a ser resolvida no rollover de
18/08:

| jogador | time | tipo | salário | ESPN (provisório) |
|---|---|---|---|---|
| Chimere Dike | mongoloides | `fa_waiver` | $1 | 1.0 |
| Jaylin Noel | Fazenda Pederasta | `fa_waiver` | $1 | 1.0 |
| Malik Willis | Tropa do Bicampeonato | `fa_waiver` | $1 | 1.0 |
| Oronde Gadsden | 🕯️🕯️ achane 🕯️🕯️ | `fa_waiver` | $1 | 1.0 |
| Tyler Shough | Trust The Process | `fa_waiver` | $1 | 1.0 |

*(+ 4 `fa_auction` em Ano 1: Brenton Strange $4, Harold Fannin $1, Isaiah Bond $4, Tyler Loop $1.)*

**Sobre a correlação com a importação de histórico:** não é o eixo que explica o rótulo. Os seis
tipos convivem em Ano 1 **e** em Ano 2, e `fa_waiver` é simplesmente o enum que o pipeline grava —
não um resíduo de reconstrução malsucedida.

#### T3 — Onde a bifurcação vive, e o buraco

A bifurcação é **uma linha**, e aparece em três funções ([salary_engine.py](salary_engine.py)):

```python
_WAIVER_TYPES = {"waiver", "free_agent", "fa"}
...
if acq in _WAIVER_TYPES and next_yr == 2:
    new_sal = waiver_year2_salary(espn)      # floor(0.80 × ESPN)
else:
    new_sal = valorization_rule(prev, espn)  # max(prev, floor(0.5 × ESPN))
```

⛔ **`fa_waiver` e `fa_auction` NÃO estão em `_WAIVER_TYPES`.** Os **37** `fa_waiver` — cujo rótulo
literalmente diz *"Waiver / Free Agent"* — **nunca recebem a regra de waiver**; caem sempre na
valorização. O conjunto ainda carrega `"fa"`, que **não existe no banco** (enum morto).

**O que o rollover de 18/08 fará com os 5 de Ano 1:** `next_yr = 2`, `fa_waiver ∉ _WAIVER_TYPES` ⇒
**valorização**, `max($1, floor(0.5 × ESPN))` — em vez de `floor(0.80 × ESPN)`, que é o que o
regulamento **6.6** manda para aquisição em waiver/FA no 2º ano.

✅ **Dano HOJE: zero — por coincidência, não por desenho.** Os 5 têm `espn_ref_value = 1.0`
(tabela **provisória**): as duas regras dão **$1**. ⚠️ **Mas a tabela ESPN definitiva entra em 18/08
— o mesmo dia do rollover.** Com valor real, as regras divergem rápido:

| ESPN ajustado | regra correta (0,8×) | o que o código fará (valorização) | erro |
|---|---|---|---|
| $5 | $4 | $2 | −$2 |
| $10 | $8 | $5 | −$3 |
| $20 | $16 | $10 | −$6 |

⇒ **é um item de prazo**: a decisão precisa ser tomada **antes** de 18/08, e o erro seria **selado**
na keeper sheet de 20/08.

**Pergunta de regra para o owner (não de implementação):** `fa_auction` deve entrar no conjunto? A
**7.1.1** diz que a aquisição em waiver é por *"Waiver Auction"*, o que sugere que sim; mas os 4 de
Ano 1 têm salários de $4/$1 (parecem lances), enquanto a **6.6** manda que o ano 1 de waiver/FA seja
*"sem valor"* ($1). **As duas leituras são defensáveis — é decisão de liga.**

#### T4 — O caso Watson: os $4 vêm de uma reconstrução, e o rollover fará $3

`Christian Watson` — GB, `free_agent`, **ano 2**, salário **$1**, `espn_ref_value` **6.0**.

A tela de roster mostra **PROJ 2026 = $4** porque `Player.projected_next_salary()`
([models.py:176](models.py#L176)) chama `compute_salary_for_year`, que **reconstrói o contrato do
zero** e **descarta o salário armazenado**:

1. `year1_salary('free_agent', …)` → `free_agent ∈ _WAIVER_TYPES` → **$1** (ignora o `$1` real, mas coincide)
2. ano 2 → `floor(0.80 × 6)` = `floor(4.8)` = **$4** ← *o palpite do owner estava certo*
3. ano 3 → `valorization_rule(4, 6)` = `max(4, 3)` = **$4**

**Mas o rollover não usa essa função.** [offseason.py:681](routes/offseason.py#L681) chama
`apply_season_rollover`, que parte do **salário armazenado**: `next_yr = 3` (≠ 2, então **sem** regra
de waiver) → `valorization_rule($1, 6)` = `max(1, floor(3.0))` = **$3**.

⇒ **A coluna PROJ mostra $4; o rollover escreverá $3.**

**Resposta direta à pergunta do prompt** (*"há jogadores em ano 2+ sendo tratados como aquisição
nova?"*): **na tela, sim — em todos**; `compute_salary_for_year` trata todo jogador como se estivesse
sendo readquirido. **No rollover, não** — ele respeita o contrato armazenado. ✅ **O dano está
confinado ao display; o que será escrito em 18/08 não é afetado por esta função.**

#### T5 — Réplica: SIM, três definições de "próximo salário"

| # | função | consumidores | veredito |
|---|---|---|---|
| 1 | `compute_salary_for_year` (reconstrói do ano 1) via `Player.projected_next_salary()` | **só** [_macros.html:73](templates/_macros.html#L73) — a coluna **PROJ** de **`/` e `/team/<id>`** | ⛔ **diverge** |
| 2 | `salary_engine.project_next_salary` (usa salário armazenado) | Cap Projector, porta `/budget`, `to_dict()` | ✅ |
| 3 | `salary_engine.apply_season_rollover` (mesma lógica da 2 + texto da regra) | preview do admin e **o rollover real de 18/08** | ✅ |

**(2) e (3) concordam; a (1) discorda em 26 de 248 jogadores, e é a que aparece na tela mais vista.**
Soma das diferenças: **+$62**, sempre **superestimando**.

**Os maiores desvios não são de waiver/FA — são de ROOKIE**, e o prompt não os previa:

| jogador | tipo | salário | PROJ na tela | rollover fará | erro |
|---|---|---|---|---|---|
| Omarion Hampton | `rookie_draft` | $26 | **$44** | **$26** | **+$18** |
| Tetairoa McMillan | `rookie_draft` | $8 | $30 | $15 | +$15 |
| Emeka Egbuka | `rookie_draft` | $2 | $26 | $13 | +$13 |
| Cam Skattebo | `rookie_draft` | $2 | $25 | $12 | +$13 |
| Quinshon Judkins | `rookie_draft` | $2 | $24 | $12 | +$12 |

**Mecanismo:** para rookie, `year1_salary` devolve `floor(ESPN)` — então a função **recalcula o ano
1 com o ESPN de HOJE**, descartando o salário real do draft. Um rookie comprado a $26 com ESPN que
subiu para $44 aparece projetado a $44. **Isso viola diretamente o princípio "o DB é autoridade
sobre salários e anos de contrato"** do `CLAUDE.md`.

**Por que importa agora:** é a coluna que cada owner olha para decidir **o que cortar em 20/08**,
e ela **superestima** o custo futuro de manter — em até **$18** num único jogador.

#### Refutação de premissas (MAN-METH-REG)

**(a) Premissas deste prompt contraditas pelo observado:**
1. ⛔ **"O rótulo ambíguo vem de jogadores de anos anteriores; é cicatriz, não bug."** **Falsificada
   por 5 casos em Ano 1** — a bifurcação está **pendente**, não passada. E o problema real não é o
   rótulo (que é um dict correto, truncado por CSS): é o **enum `fa_waiver` não existir para o
   motor de salário**.
2. ⛔ **"Se a regra de FA nova for aplicada em vez da renovação, há jogadores em ano 2+ sendo
   tratados como aquisição nova."** A inferência está certa, mas **no lugar errado**: quem trata
   todo mundo como aquisição nova é a **coluna PROJ**, não o rollover. O rollover está correto.
3. ⚠️ **"A distinção Waiver × FA tem regras salariais diferentes."** No **regulamento**, 6.6 trata
   **waiver e FA juntos** (mesma regra: ano 1 sem valor, ano 2 = 0,8 × ESPN). **No código**, `waiver`
   e `free_agent` estão **no mesmo conjunto** e recebem tratamento idêntico. A distinção que existe
   de fato é **outra**: `fa_waiver`/`fa_auction` **fora** do conjunto × os demais dentro.

**(b) Comportamentos presentes que o prompt não previu:**
1. **Três** funções de "próximo salário", com a da tela divergindo das outras duas em **26/248**.
2. Os maiores erros são de **rookie** (**+$18** em Hampton), não de waiver/FA.
3. `"fa"` em `_WAIVER_TYPES` é **enum morto** — não existe no banco.
4. O truncamento é **CSS**, não dado.
5. **85 jogadores com `contract_start_season = 2025` e `contract_year = 2`**, com
   `current_season = 2025` — aparente inconsistência (contrato que começa no ano corrente deveria
   estar em ano 1). ⚠️ **Observação, não veredito:** o campo é escrito em pontos distintos
   (`record_acquisition`, `import_csv`, renovação) e a diagnose **não** apurou qual é a semântica
   pretendida. Merece verificação própria antes de 18/08, já que `contract_year` alimenta a
   bifurcação.

#### O que esta diagnose NÃO faz

Não corrige rótulo, salário, enum nem função; não altera `salary_engine`, schema ou o caminho
canônico. Se o owner decidir corrigir salário, o caminho é `correct_player_salary` — **nunca patch
direto**.

**Decisões do owner, em ordem de prazo:**
1. **Antes de 18/08:** `fa_waiver` entra em `_WAIVER_TYPES`? (e `fa_auction`?) — **regra de liga**.
   Hoje o dano é zero só porque a ESPN provisória é 1.0.
2. **Antes de 20/08:** a coluna PROJ passa a usar a fonte (2)/(3)? É correção de **display**, não
   toca o rollover — mas é o número que guia os cortes.
3. **Verificação:** a inconsistência `contract_start_season` × `contract_year` nos 85.

**Cross-refs:** [[OFF26-19]] (mesma família — filtro/regra de contrato que não acompanha o caso),
[[WV1]] (salário de aquisição via waiver sem drop tratado como FA — vizinho direto do `fa_waiver`),
[[F10]] (a invariante de fonte única, violada aqui pela 3ª definição), [[OFF26-11]] (dano silencioso
em contrato).

---

#### F1B (MAN-OFF26-20-F1B, 05/08/2026) — a arbitragem pelo regulamento INVERTE a conclusão

⚠️ **A conclusão da F1 — *"o rollover está certo e a tela está errada"* — estava PARCIALMENTE
ERRADA, e o owner tinha razão ao recusá-la.** Ela foi inferida da arquitetura (uma função respeita o
banco, a outra não), não medida contra o regulamento. Ao aplicar a régua definitiva, caso a caso,
apareceu **exatamente o cenário que o prompt anterior antecipou**: para uma coorte grande **o banco
está errado**, a função que o respeita **propaga o erro com convicção**, e a que reconstrói
**acerta**.

**O achado central é maior que tudo que a F1 reportou:** **73 jogadores** vão receber a **regra
errada** no rollover de 18/08 — não 5.

##### T1 — Regulamento à mão, caso a caso

Árbitro implementado **sem chamar o `salary_engine`**: 6.2/6.3 (valorização), 6.6 (waiver/FA ano 2),
6.9 (renovação), 6.10 (floor, mín $1). ⚠️ Todos os números usam **ESPN provisória** — o veredito é
sobre a **regra aplicada**, não sobre o valor final, que só se fecha em 18/08.

**Grupo B — os 21 rookies (dado consistente: `start=2025`, `ano=1`).**

> **Omarion Hampton** — `rookie_draft`, salário $26 (ano 1/2025), ESPN 2026 = 44.
> Em 2026 é **ano 2**. Rookie **não** é aquisição de waiver/FA ⇒ a 6.6 **não se aplica**; vale a
> **6.2/6.3**: `MAX(salário anterior, 50% do ESPN)` = `max(26, floor(0,5 × 44) = 22)` = **$26**.
> **Rollover $26 ✅ · Tela $44 ❌** — a tela descarta o contrato e recalcula o ano 1 como
> `floor(ESPN de hoje)`, violando a 6.1 (o ano 1 é *"o valor utilizado no Auction"*, não o ESPN
> corrente). Idêntico para **McMillan** ($15 ✅ × $30), **Egbuka** ($13 ✅ × $26).

⚠️ **E a tela erra nos DOIS sentidos** — a F1 disse "sempre para cima", o que é **falso**:

> **Ashton Jeanty** — `rookie_draft`, $57, ESPN 45. 6.2/6.3: `max(57, 22)` = **$57**.
> **Rollover $57 ✅ · Tela $45 ❌ — subestima em $12.** Idem **TreVeyon Henderson** ($21 ✅ × $10,
> −$11). **9 dos 26 subestimam.** É a direção perigosa: leva a manter um contrato que não cabe.

**Grupo A — os 5 divergentes que também estão entre os 85** (todos `free_agent`):

> **Christian Watson** — o histórico do Sleeper (eventos com `sleeper_event_ref`, i.e. transações
> reais) é: `2024 auction_draft` → `2025 rollover` → **`2025 drop`** → **`2025 free_agent`**.
> Ou seja: **foi dropado e readquirido como free agent em 2025**.
> Pela **6.1** (*"o primeiro ano é o ano da aquisição no draft ou nos waivers"*) o contrato
> **recomeçou em 2025 como ano 1**, salário $1 — que é *"sem valor"*, exatamente como manda a
> **6.6**. Logo, em **2026 ele está no ANO 2**, e a 6.6 manda **80% do ESPN**:
> `floor(0,8 × 6)` = **$4**.
> ⇒ **Tela $4 ✅ · Rollover $3 ❌.** O `contract_year = 2` armazenado está **errado**: deveria ser 1.
> Idem **Pierce** ($5 ✅ × $3), **Parker Washington** ($4 ✅ × $3), **Stafford** ($3 ✅ × $2),
> **Michael Wilson** ($2 ✅ × $1).

**Veredito agregado — a resposta a "qual função corrigir":**

| população | quem acerta | o que corrigir |
|---|---|---|
| 21 rookies + demais com dado consistente | **rollover** | **a tela** |
| **73 readquiridos em 2025** (inclui os 5 acima) | **a tela**, por acidente | **o DADO** (`contract_year`) — e a regra que o motor escolhe |
| 5 `fa_waiver` em ano 1 | ambos, **hoje** | `_WAIVER_TYPES` (latente até a ESPN definitiva) |

⇒ **Corrigir as três coisas: a tela, o dado e o enum.** Nenhuma das duas funções é "a certa".

##### T2 — Censo semântico: o vocabulário de EVENTO vazou para o campo de AQUISIÇÃO

| tipo | n | de onde vem | regra que o código aplica | regra devida | diverge? |
|---|---|---|---|---|---|
| `auction_draft` | 96 | CSV (`_norm_acq`) — **0 tocados pelo F8** | ano 1 = lance; depois 6.2/6.3 | 6.1 + 6.2/6.3 | não |
| `rookie_draft` | 31 | CSV — **0 tocados pelo F8** | ano 1 = `floor(ESPN×1,2)`; depois 6.2/6.3 | 8.2.7 + 6.2/6.3 | não |
| `waiver` | 17 | CSV — **0 tocados pelo F8** | ∈ `_WAIVER_TYPES` ⇒ 6.6 | 6.6 (ou **6.8** se readquirido pelo próprio owner) | **6.8 não é implementável** — falta o dado |
| `free_agent` | 39 | **F8 — 39/39** | ∈ `_WAIVER_TYPES` ⇒ 6.6 | 6.6 | não |
| **`fa_waiver`** | 37 | **F8 — 37/37** | ⛔ **fora** de `_WAIVER_TYPES` ⇒ valorização | 6.6 | **SIM** |
| **`fa_auction`** | 28 | **F8 — 28/28** | ⛔ **fora** ⇒ valorização | 6.6/7.1.1 (a decidir) | **provável** |

⛔ **RESPOSTA À PERGUNTA CENTRAL: é ACIDENTE, não decisão.** O mecanismo está em
[sync_sleeper.py:1217-1218](sync_sleeper.py#L1217-L1218), no rebuild canônico do F8:

```python
if ev["season"] >= 2025:
    new_acq = ev["event_type"]     # ← vocabulário de EVENTO gravado no campo de AQUISIÇÃO
```

`_norm_acq` ([import_csv.py:30](import_csv.py#L30)) **nunca produz** `fa_waiver` nem `fa_auction` —
seu contradomínio é `{auction_draft, waiver, free_agent, rookie_draft, unknown}`, e `_WAIVER_TYPES`
foi escrito contra **esse** vocabulário. O F8 introduziu um **segundo vocabulário** (o de
`PlayerHistory.event_type`) no mesmo campo, e **os dois nunca foram reconciliados**.

**Prova empírica** (`F8PlayerBackup`, 127 linhas): **100%** dos `fa_waiver`, `fa_auction` e
`free_agent` foram escritos pelo F8; **0%** dos `auction_draft`, `rookie_draft` e `waiver`. As
transições incluem `rookie_draft → fa_waiver` (7) e `auction_draft → fa_auction` (25).

**A ironia registrada:** o comentário nas linhas 1215-1216 diz *"Only update acquisition_type if
last event is >= 2025 (protege year-1 rules do salary_engine para contratos vigentes)"* — o autor
**sabia** que o campo alimenta regra salarial e pôs um guard **de season**. O buraco é de
**vocabulário**, e está justamente no ramo que o guard considerou seguro.

##### T3 — Os 85: semântica apurada, e ela INVERTE a leitura anterior

**Os dois campos têm escritores e semânticas diferentes:**

- `contract_year` — vem do **CSV do owner** ([import_csv.py:103](import_csv.py#L103),
  `contract_year_2025`), sob o guard `csv_bootstrap_done`.
- `contract_start_season` — **derivado** (`CURRENT_SEASON − cyr + 1`,
  [import_csv.py:105](import_csv.py#L105)) sob o guard **independente** `f8_rebuilt`; e, após o F8,
  **sobrescrito** por `ev["season"]` = **a season do último evento real**
  ([sync_sleeper.py:1232](sync_sleeper.py#L1232)).

Não é "erro de importação" nem "convenção legítima": é **colisão semântica entre dois escritores com
guards independentes**. E a apuração mostra qual dos dois está certo:

✅ **Os 85 têm, TODOS, `drop` real E reaquisição real de 2025** no chain do Sleeper (eventos com
`sleeper_event_ref`). Não é artefato: são transações da API.

| evento de reaquisição (2025) | n | mesmo time | time diferente |
|---|---|---|---|
| `fa_waiver` | 32 | 4 | 28 |
| `free_agent` | 29 | 7 | 22 |
| `fa_auction` | 24 | 1 | 23 |

⇒ **`contract_start_season = 2025` está CERTO; `contract_year = 2` está ERRADO** para esses
jogadores. Pela **6.1**, a aquisição de 2025 abre contrato novo — **ano 1 em 2025, ano 2 em 2026**.

**A 6.8 é a única defesa possível do `contract_year = 2`** — mas ela exige *"adquiridos … **pelo
próprio owner**"*, e **73 dos 85 foram readquiridos por um time DIFERENTE**. Para esses 73 a 6.8
**não pode** ser invocada: o contrato novo é inequívoco.

⚠️ **Isso corrige o que a diagnose F1B preliminar (relatada ao owner antes deste prompt) havia dito**
— que `contract_year` seria o campo autoritativo. Com o histórico de eventos em mãos, é o contrário.

**Exposição no rollover de 18/08** — os 73 serão tratados como **ano 3** (valorização) quando são
**ano 2** (6.6, `0,8 × ESPN`):

| ESPN 2026 | correto (0,8×E) | rollover fará | erro |
|---|---|---|---|
| $1 (hoje) | $73 | $226 | **+$153 a mais** |
| $5 | $292 | $278 | −$14 |
| $10 | $584 | $453 | **−$131 a menos** |
| $20 | $1.168 | $775 | **−$393 a menos** |

**O erro troca de sinal com o nível do ESPN** — hoje o rollover *sobrecobra* $79 no agregado
(ESPN quase toda 1.0); com valores reais passa a *subcobrar*. Em qualquer cenário, **a regra
aplicada está errada**, e o resultado entra **selado** na keeper sheet de 20/08.

**Cruzamento com os 26:** **5 dos 26 estão entre os 85** (Watson, Pierce, Stafford, Wilson, Parker
Washington) — e **sim, a divergência deles se explica por aí**. Os outros **21 não estão**: são
rookies com dado consistente, onde a tela erra sozinha. **Os outros 80 dos 85 não aparecem entre os
26 porque as duas funções concordam — e ambas erram**, mascaradas pela ESPN de 1.0. Era exatamente o
ponto do owner: *concordância prova consistência, não correção*.

⚠️ **Caveat de método:** o corte "mesmo time × time diferente" usa `PlayerHistory.team_name`, que o
[[S4]] registra como **chave instável**. Os 73 são um piso confiável para o argumento (a maioria
larga), mas a contagem exata merece conferência por `roster_id` antes de qualquer correção.

##### T4 — Alcance da função da tela

| função | consumidores |
|---|---|
| `Player.projected_next_salary()` → `compute_salary_for_year` **(a que reconstrói)** | **um único**: [_macros.html:73](templates/_macros.html#L73), a coluna PROJ — que serve **`/` e `/team/<id>`** |
| `salary_engine.project_next_salary` | **Cap Projector** ([salary.py:87](routes/salary.py#L87)), porta canônica `/budget` ([salary.py:150](routes/salary.py#L150), modo `projected:true`), `Player.to_dict()` |
| `apply_season_rollover` | preview do admin + **o rollover real** ([offseason.py:681](routes/offseason.py#L681)) |

**O Cap Projector usa a conta do backend** — a mesma do rollover. ⇒ **Cap Projector e coluna PROJ
mostram números diferentes para o mesmo jogador**, e nenhuma tela avisa disso.

##### Refutação de premissas (MAN-METH-REG)

**(a) Contraditas pelo observado:**
1. ⛔ **"a tela diverge sempre para cima, +$62"** (premissa do prompt, herdada da F1). **Falso:**
   **9 dos 26 subestimam**, até **−$12** (Jeanty). O +$62 é **saldo líquido**, não direção.
2. ⛔ **"o problema pode ser só de classificação de tipo, não de contrato errado"** (informação do
   owner sobre os waivers validados). **Parcialmente falso:** há **as duas coisas**. E note que os
   **17 `waiver`** — o grupo que o owner validou — são **exatamente os que o F8 não tocou**; a
   validação não alcança os 37 `fa_waiver`, que **nasceram do F8**.
3. ⚠️ **"rookie entra a `floor(ESPN × 1,2)` conforme rodada"** (DADOS do prompt). O regulamento
   **8.2.7** manda ESPN × 1,2 **sem** modulação por rodada — **não há regra por rodada no texto**.
4. ⚠️ **"o regulamento trata waiver e FA juntos"** (afirmação da própria F1). A **6.6** trata; mas a
   **6.8** os separa: dropado readquirido **em waiver pelo próprio owner** carrega o contrato
   anterior. **A distinção do owner existia; a F1 a negou por leitura incompleta.**

**(b) Não previstos pelo prompt:**
1. **73 jogadores** com a regra errada no rollover — o prompt falava em 5.
2. O vocabulário de **evento** vazando para `acquisition_type` via F8 (100% dos 3 tipos novos).
3. `contract_start_season` ser **o campo certo** e `contract_year` o errado — inverso do intuitivo.
4. O erro dos 73 **troca de sinal** conforme o ESPN.
5. A **6.8 é hoje inimplementável**: não há campo que distinga "readquirido pelo próprio owner via
   waiver" de "virou FA" — é o [[WV1]], que esta diagnose **confirma e agrava**.
6. `salary_history` está **vazia** e o `EspnValueStore` só tem **2026** ⇒ não é possível verificar se
   a 6.6 foi aplicada nos anos anteriores. A trilha de auditoria do salário **não existe**.

##### O que esta diagnose NÃO faz

Não corrige salário, tipo, campo nem função. Correção de salário passa por `correct_player_salary` —
**nunca patch**.

**Decisões do owner, em ordem de prazo:** *(⚠️ SUPERADAS pela F1C — ver abaixo)*
1. ⛔ **ANTES DE 18/08 — o item mais grave:** os **73** readquiridos em 2025 estão em **ano 2** ou
   **ano 3** em 2026? Pela 6.1 é ano 2. Se o owner concordar, **`contract_year` precisa ser corrigido
   antes do rollover**, senão 73 contratos saem com a regra errada e são selados em 20/08.
2. **Antes de 18/08:** `fa_waiver` (e `fa_auction`?) entram em `_WAIVER_TYPES`? Sem isso, mesmo com
   o `contract_year` certo, os 37 `fa_waiver` **continuam** sem a 6.6.
3. **Antes de 20/08:** a coluna PROJ passa a consumir a fonte do backend. Hoje ela contradiz o Cap
   Projector na mesma tela.
4. **Estrutural (pós-leilão):** reconciliar os dois vocabulários de `acquisition_type` e criar o
   dado que a **6.8** exige ([[WV1]]).

---

#### F1C (MAN-OFF26-20-F1C, 05/08/2026) — o discriminador é o CANAL, e o problema encolhe de 73 para 29

⚠️ **A F1B usou o critério errado.** O corte *"readquirido pelo próprio owner × por time diferente"*
saiu de uma leitura da 6.8 que **não corresponde à regra real da liga**, esclarecida pelo owner em
05/08 (autoridade sobre qualquer leitura do texto):

> **Waiver = leilão de FAAB.** O dropado fica travado no período de waiver e vai a leilão. Quem
> vence **leva o jogador com o contrato que ele tinha** — salário e contagem de anos preservados —
> **para qualquer time**, inclusive um diferente do original.
> **Free agent = grátis pós-lock.** Ninguém deu bid; o jogador entra **sem contrato**: $0/$1 no ano
> corrente e, na temporada seguinte já como **ano 2**, **0,8 × 1,2 × ESPN**.

⇒ **A identidade do time é irrelevante. O que decide é o CANAL.**

##### T1 — A distinção nunca se perdeu: ela está no sync

Está em [sync_sleeper.py:911-915](sync_sleeper.py#L911-L915), em `_collect_transaction_events`:

```python
type_map = {
    "waiver":      "fa_waiver",     # ← claim de waiver (FAAB)
    "free_agent":  "free_agent",    # ← add de free agent (grátis)
    "commissioner": "commissioner",
}
```

O `tx["type"]` da API do Sleeper **já carrega o canal**, e o sync o **preserva** fielmente em
`PlayerHistory.event_type`. Os **117 `fa_waiver`** e **150 `free_agent`** do histórico, todos com
`sleeper_event_ref`, são **transações reais da API** — não reconstrução.

**O que se perdeu:** o **valor do bid FAAB** (`tx["settings"]["waiver_bid"]`) **não é capturado**.
Para efeito de salário isso é **inócuo** — a **7.1.8** diz que *"os valores pagos pelos waivers não
são considerados na folha salarial"*. Nada relevante foi descartado.

⇒ **Não era preciso refazer a identificação: ela já existe, é canônica e vem da API.**

##### T2 — Censo pelo canal (alta confiança)

Para cada um dos 85, o **último evento de aquisição** (trocas resolvidas para a aquisição anterior,
pela **6.7** — *"jogador trocado carrega o contrato"*):

| canal de origem | n | regra da liga | `contract_year = 2` está… |
|---|---|---|---|
| **`fa_waiver`** (waiver/FAAB) | **32** | carrega o contrato | ✅ **CERTO** — nada a corrigir |
| **`free_agent`** (add grátis) | **29** | contrato novo | ⛔ **ERRADO** — deveria ser ano 1 |
| **`fa_auction`** (leilão 2025) | **24** | contrato novo | ⚠️ contagem errada, **sem efeito em 2026** |

**Confiança: ALTA** para os três grupos — o canal vem do `tx["type"]` da API, e o
`acquisition_type` do `Player` **bate com o último evento em 100% dos casos** (32/32, 29/29, 24/24).
**Nenhum indeterminado** nesta população.

##### T3 — Os três grupos, e o impacto real de 18/08

**(a) 32 via waiver — CERTOS.** Carregam contrato legitimamente, mesmo tendo trocado de time. O
rollover aplicará valorização, que é o que a regra manda. **Nada a corrigir.**

**(c) 24 via `fa_auction` — contagem errada, salário CERTO.** Adquiridos no leilão de 2025 ⇒ ano 1
em 2025, não 2. **Mas o erro não tem efeito em 2026:** na trilha de valorização,
`max(salário, 0,5 × ESPN)` dá **o mesmo número em qualquer ano ≥ 2**. O off-by-one só se materializa
na **renovação (ano 5)** — em 2029.

**(b) 29 via free agent — ERRADOS, e é este o grupo do prazo.** Deveriam estar em ano 1 (2025) ⇒
**ano 2 em 2026** ⇒ `0,8 × 1,2 × ESPN`. O rollover os tratará como ano 3 ⇒ valorização.

| ESPN (ajustado) | correto (0,8×E) | rollover fará | delta |
|---|---|---|---|
| **provisória de hoje** | **$42** | **$36** | **+$6** |
| $5 | $116 | $58 | +$58 |
| $10 | $232 | $145 | **+$87** |
| $20 | $464 | $290 | **+$174** |

⇒ **o rollover vai SUBCOBRAR** esses 29. Hoje são $6; com a ESPN definitiva de 18/08 o número é
desconhecido e cresce linearmente com o valor dos jogadores.

##### T4 — O fator 1,2: ambiguidade eliminada

O ×1,2 é aplicado **na fronteira de escrita**, nunca no cálculo:

- [espn_pdf_parser.py:129](espn_pdf_parser.py#L129) — `max(1.0, float(int(espn_raw * 1.2)))` (import PDF)
- [routes/admin.py:173](routes/admin.py#L173) — `set_espn_value(..., espn_raw * 1.2, ...)` (CSV bulk)

`Player.espn_ref_value` guarda o valor **já ajustado**, e `salary_engine._adj()` é **apenas um
guard de `None`** — não multiplica nada. Logo:

```
waiver_year2_salary(espn) = floor(0.80 × espn_ref_value) = floor(0,8 × 1,2 × ESPN_raw)   ✅
valorization_rule       = max(prev, floor(0.50 × espn_ref_value)) = 0,5 × 1,2 × raw      ✅
year1_salary(rookie)    = floor(espn_ref_value)          = 1,2 × raw                     ✅
```

⇒ **O código já implementa `0,8 × 1,2 × ESPN`.** Não há fator faltando em regra nenhuma. Confirma a
diagnose [[MAN-ESPN12]], que já havia varrido o tema e descartado réplica no client.

##### T5 — Revisão item a item da F1B

| conclusão da F1B | veredito |
|---|---|
| **"73 contratos errados"** | ⛔ **CAI** — critério errado. São **29** (só o canal FA). |
| **"`fa_waiver` fora de `_WAIVER_TYPES` é bug"** (da F1) | ⛔ **CAI E INVERTE** — waiver **carrega contrato** ⇒ valorização ⇒ **estar fora está CERTO**. E `free_agent` **dentro** está **CERTO** (FA → 0,8 no ano 2). |
| **"5 `fa_waiver` em ano 1 expostos"** | ⛔ **CAI** — o histórico mostra que os 5 entraram por waiver em 2025 sem contrato prévio; ano 1 está certo, e a valorização que receberão é o comportamento devido. **Ressalva abaixo.** |
| **"`contract_start_season` certo, `contract_year` errado"** | ⚠️ **SOBREVIVE PARCIALMENTE** — vale para os 29 (b) e, na contagem, para os 24 (c); **não vale** para os 32 (a), onde `contract_year = 2` é o correto. |
| **21 rookies com divergência de tela** | ✅ **SOBREVIVE INTACTO** — não depende deste critério. Hampton **$26** (rollover ✅) × $44 (tela ❌); Jeanty **$57** ✅ × $45 ❌. |
| **"a tela erra nos dois sentidos"** | ✅ **SOBREVIVE** — 9 dos 26 subestimam, até −$12. |
| **"o F8 grava `event_type` em `acquisition_type`"** | ✅ **Fato sobrevive**, ⚠️ **a leitura muda:** não é acidente **danoso** — os valores gravados (`fa_waiver`/`free_agent`) **são exatamente o canal**, e o `_WAIVER_TYPES` os trata **corretamente**. É **acoplamento frágil** (duas vocabulários no mesmo campo), não bug ativo. |
| **"os 17 `waiver` validados são os que o F8 não tocou"** | ✅ fato sobrevive; ⛔ a **conclusão** (que os `fa_waiver` estariam errados) cai. |
| **Cap Projector × coluna PROJ divergem** | ✅ **SOBREVIVE**. |
| **`salary_history` vazia, sem trilha de auditoria** | ✅ **SOBREVIVE**. |

⚠️ **ACHADO NOVO, de sinal trocado:** o enum **`waiver`** (17 jogadores, vocabulário do CSV) está
**DENTRO** de `_WAIVER_TYPES` — e, pela regra do owner, waiver **carrega contrato** e **não** deve
receber o 0,8. **Impacto em 2026: ZERO** — todos os 17 estão em `contract_year = 2`, logo
`next_yr = 3` e a regra do ano 2 **não dispara**. É **latente**, não ativo.

⚠️ **INDETERMINADO, declarado como tal:** os **5 `fa_waiver` em ano 1** (Dike, Noel, Willis,
Gadsden, Shough) entraram por waiver **sem contrato prévio** — a regra do owner diz o que acontece
quando o jogador **tem** contrato (carrega), mas **não diz** qual é o ano 2 de um contrato que
*nasceu* de um claim de waiver. O texto da **6.6** ("Waivers **ou** Free Agents … no segundo ano,
80%") mandaria 0,8; a regra do owner, lida como "waiver ≠ FA", mandaria valorização. **Não infiro:
é decisão do owner.** Hoje as duas dão $1 (ESPN provisória 1.0); em 18/08 podem divergir.

##### Refutação de premissas

**(a) Contraditas:**
1. ⛔ *"a identificação waiver × FA já foi feita — encontrar onde ela vive"* — **certo, e melhor do
   que o prompt supunha**: não foi verificação manual perdida; é **código vivo** que roda a cada
   sync, alimentado pela própria API.
2. ⚠️ *"o corte da F1B fica anulado não por instabilidade da chave, mas por critério errado"* —
   **confirmado**, e o caveat do `team_name` também deixa de importar: o novo corte não usa time.
3. ⚠️ *"o erro real está só nos que vieram como FA"* — **quase**: há também os **24 do leilão de
   2025** com a contagem errada; a diferença é que neles o erro **não afeta o salário de 2026**.

**(b) Não previstos:**
1. **Valorização é indiferente ao número do ano** (≥2) ⇒ off-by-one em `contract_year` **só importa**
   para quem está na porta do 0,8 (ano 2 de FA) ou na renovação (ano 5). Isso é o que reduz o
   problema de 73 para 29.
2. O `acquisition_type` do `Player` **bate com o último evento em 100%** dos 85 — o F8 fez esse
   trabalho corretamente.
3. O **bid FAAB não é capturado** pelo sync — inócuo hoje (7.1.8), mas é a única perda real.
4. O enum `waiver` está no conjunto errado — **espelho invertido** do que a F1 acusou.

##### O que muda para o owner

**Prioridade rebaixada de CRÍTICA para ALTA:** o grupo com erro de salário é **29**, não 73, e o
delta com a ESPN de hoje é **$6**. O prazo, porém, é o mesmo — e o número cresce com a ESPN
definitiva.

1. ⛔ **Antes de 18/08:** confirmar que os **29 do canal FA** devem ir a `contract_year = 1` (⇒ ano 2
   em 2026 ⇒ 0,8 × 1,2 × ESPN). Correção passa por `correct_player_salary` + ajuste de contagem —
   **nunca patch**.
2. **Antes de 18/08:** decidir o **indeterminado** dos 5 `fa_waiver` em ano 1.
3. **Antes de 20/08:** a coluna PROJ passa a consumir a fonte do backend (os 21 rookies seguem
   errados na tela — achado intacto).
4. **Sem pressa:** os 24 do `fa_auction` (contagem, efeito só em 2029) e o enum `waiver` no conjunto
   errado (latente). **Nada a fazer nos 32 do waiver — estão certos.**

---

#### VERIF (MAN-OFF26-20-VERIF, 05/08/2026) — os 34 verificados nominalmente contra a API

**Read-only absoluto.** Banco aberto em `mode=ro`; API do Sleeper só com `GET`. Nenhuma escrita,
nenhuma correção. Draft 2026 conferido em `pre_draft` — **board intacto**.

##### A premissa da data: CONFIRMADA, não falsificada

O owner condicionou a correção a uma pergunta: **algum dos 34 foi adquirido em 2024?** Se sim,
já passou pela valorização de 2025 e "corrigi-lo" quebraria um contrato certo.

**Resposta medida: 34 de 34 abrem em 2025. Zero em 2024.** Baixado o chain inteiro
(`1316547584378048512` 2026 → `1224848075609100288` 2025 → `1107510813394341888` 2024),
**1125 transações** e **9 drafts**. Os **173 refs `tx:`** do `PlayerHistory` desses 34 resolvem
**todos** contra a API — nenhum evento órfão.

⚠️ **Mas há uma ressalva que o corte automático não pega, e ela é o achado do dia** (ver "as duas
aberturas de 2024 candidatas", abaixo).

##### O eixo do erro não é um só — e a F1C errou ao tratá-lo como um só

A F1C separou "29 errados" × "5 indeterminados". A verificação mostra que o eixo é outro:

| Grupo | `contract_year` no banco | O DADO está | O MOTOR faz | Deveria fazer |
|---|---|---|---|---|
| **29 `free_agent`** | 2 (⇒ 2026 = ano 3) | ⛔ **ERRADO** (2025 = ano 1 ⇒ 2026 = ano 2) | valorização | 0,8 × ESPN REF |
| **5 `fa_waiver`** | 1 (⇒ 2026 = ano 2) | ✅ **CERTO** | valorização | 0,8 × ESPN REF |

⛔ **Os 34 receberão VALORIZAÇÃO no rollover de 18/08, e os 34 deveriam receber 0,8 × ESPN REF —
por causas OPOSTAS.** Nos 29 o dado está errado; nos 5 o dado está certo e quem erra é o enum
(`fa_waiver` ∉ `_WAIVER_TYPES`, então o ramo `next_yr == 2` não dispara).

✅ **Consequência verificável, e ela simplifica a correção futura:** pôr `fa_waiver` dentro de
`_WAIVER_TYPES` afeta **exclusivamente os 5**. Os outros 32 `fa_waiver` estão **todos** em
`contract_year = 2` ⇒ `next_yr = 3` ⇒ o ramo do 0,8 **nunca** os alcança. A régua da F1C ("estar
fora está certo") é **verdadeira para os 32 e falsa para os 5** — e o enum consegue servir aos dois.

##### ⛔ O delta de "+$6" é ilusão do ESPN provisório

**134 dos 248** jogadores do elenco estão com `espn_ref_value ≤ 1.0` — provisório. A tabela
definitiva entra **18/08, o mesmo dia do rollover**. Com o ESPN de hoje só **5 dos 34** divergem;
com valor real, **32 dos 34**:

| ESPN REF hipotético (p/ os que hoje estão em 1.0) | Rollover fará | Regra manda | Delta | Divergentes |
|---|---|---|---|---|
| 1 (hoje) | $41 | $47 | **+$6** | 5/34 |
| 4 | $68 | $101 | **+$33** | 32/34 |
| 6 | $95 | $128 | **+$33** | 32/34 |
| 10 | $149 | $236 | **+$87** | 32/34 |
| 20 | $284 | $452 | **+$168** | 32/34 |

O rollover **subcobra** em todos os cenários. **Não usar o "+$6" para dimensionar a urgência** — ele
mede o ESPN provisório, não o erro.

##### Tabela nominal dos 34

`A` = o que o rollover fará com o dado como está · `B` = o que a regra do owner manda ·
ESPN REF = valor já ajustado (× 1,2), como armazenado.

| Jogador | Time | Canal | Data | Season | Banco | ESPN REF | A | B | Veredito | Motivo |
|---|---|---|---|---|---|---|---|---|---|---|
| Alec Pierce | Tropa do Bicampeonato | FA | 2025-10-02 | 2025 | ano 2, $1 | 7 | $3 | $5 | **CORRIGIR** | — |
| Christian Watson | achane | FA | 2025-09-20 | 2025 | ano 2, $1 | 6 | $3 | $4 | **CORRIGIR** | — |
| Parker Washington | mongoloides | FA | 2025-10-31 | 2025 | ano 2, $1 | 6 | $3 | $4 | **CORRIGIR** | — |
| Michael Wilson | Miller Time! | FA | 2025-11-13 | 2025 | ano 2, $1 | 3 | $1 | $2 | **CORRIGIR** | — |
| Jonathon Brooks | 3 peat… of pain | FA | 2025-09-01 | 2025 | ano 2, $1 | 2 | $1 | $1 | **CORRIGIR** | — |
| AJ Barner | Trust The Process | FA | 2025-10-12 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Colby Parkinson | ESPN FANTASY LEAGUE | FA | 2025-12-28 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Detroit Lions | 3 peat… of pain | FA | 2025-10-27 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Devaughn Vele | Trust The Process | FA | 2025-11-27 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Dontayvion Wicks | Trust The Process | FA | 2025-12-07 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Evan Engram | Cangaceiros da Colina | FA | 2025-11-26 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Greg Dortch | Fazenda Pederasta | FA | 2025-11-21 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Houston Texans | mongoloides | FA | 2025-10-22 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Indianapolis Colts | achane | FA | 2025-10-01 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Jason Myers | 3 peat… of pain | FA | 2025-11-05 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Los Angeles Rams | Fazenda Pederasta | FA | 2025-09-01 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Malik Washington | Cangaceiros da Colina | FA | 2025-09-17 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Michael Carter | Miller Time! | FA | 2025-11-23 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| New Orleans Saints | Tropa do Bicampeonato | FA | 2025-11-05 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Ray Davis | rafaelferreirap | FA | 2025-10-08 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Tyreek Hill | Trust The Process | FA | 2025-10-12 | 2025 | ano 2, $1 | 1 | $1 | $1 | **CORRIGIR** | — |
| Chimere Dike | mongoloides | waiver $8 | 2025-11-19 | 2025 | ano 1, $1 | 1 | $1 | $1 | **CORRETO** (dado) | motor expõe |
| Oronde Gadsden | achane | waiver $16 | 2025-09-24 | 2025 | ano 1, $1 | 1 | $1 | $1 | **CORRETO** (dado) | motor expõe |
| Tyler Shough | Trust The Process | waiver $18 | 2025-10-29 | 2025 | ano 1, $1 | 1 | $1 | $1 | **CORRETO** (dado) | motor expõe |
| Matthew Stafford | achane | FA | 2025-09-21 | 2025 | ano 2, $1 | 4 | $2 | $3 | **AMBÍGUO** | trade depois |
| Kenny Gainwell | ESPN FANTASY LEAGUE | FA | 2025-09-01 | 2025 | ano 2, $1 | 2 | $1 | $1 | **AMBÍGUO** | **6.8 pelo próprio owner desde 2024** |
| Brian Robinson | rafaelferreirap | FA | 2025-11-20 | 2025 | ano 2, $1 | 1 | $1 | $1 | **AMBÍGUO** | trade depois + trade 2026 |
| C.J. Stroud | mongoloides | FA | 2025-09-19 | 2025 | ano 2, $1 | 1 | $1 | $1 | **AMBÍGUO** | trade depois |
| Jake Bates | AlexTheDawg | FA | 2025-09-24 | 2025 | ano 2, $1 | 1 | $1 | $1 | **AMBÍGUO** | **6.8 pelo próprio owner desde 2024** (com dono intermediário) |
| Jaylin Noel | Fazenda Pederasta | waiver $0 | 2025-10-31 | 2025 | ano 1, $1 | 1 | $1 | $1 | **AMBÍGUO** | 6.8 mesmo owner + **tinha contrato prévio** |
| Kendre Miller | Fazenda Pederasta | FA | 2025-09-01 | 2025 | ano 2, $1 | 1 | $1 | $1 | **AMBÍGUO** | trade depois |
| Malik Willis | Tropa do Bicampeonato | waiver $0 | 2025-12-27 | 2025 | ano 1, $1 | 1 | $1 | $1 | **AMBÍGUO** | 6.8 mesmo owner (drop/re-add em 2 dias) |
| Tank Bigsby | mongoloides | FA | 2025-11-26 | 2025 | ano 2, $1 | 1 | $1 | $1 | **AMBÍGUO** | 6.8 mesmo owner + 2 trades + trade 2026 |
| Tre Tucker | Tropa do Bicampeonato | FA | 2025-12-27 | 2025 | ano 1 (de fato), $1 | 1 | $1 | $1 | **AMBÍGUO** | 6.8 mesmo owner |

**21 CORRIGIR · 3 CORRETO (dado) · 10 AMBÍGUO.**

##### Transações de 2025 que fundamentam cada CORRIGIR

Todas na liga `1224848075609100288` (season 2025), `type = free_agent`, `status = complete`:

| Jogador | Ref da API | Data | Leg |
|---|---|---|---|
| AJ Barner | `tx:1283117168791130112` | 2025-10-12 | 6 |
| Alec Pierce | `tx:1279587411055108096` | 2025-10-02 | 5 |
| Christian Watson | `tx:1275215928606334976` | 2025-09-20 | 3 |
| Colby Parkinson | `tx:1311053358693380096` | 2025-12-28 | 17 |
| Detroit Lions | `tx:1288363160729812992` | 2025-10-27 | 8 |
| Devaughn Vele | `tx:1299786723500240896` | 2025-11-27 | 13 |
| Dontayvion Wicks | `tx:1303406960007200768` | 2025-12-07 | 14 |
| Evan Engram | `tx:1299523578932232192` | 2025-11-26 | 13 |
| Greg Dortch | `tx:1297385147657629696` | 2025-11-21 | 12 |
| Houston Texans | `tx:1286667851960176640` | 2025-10-22 | 8 |
| Indianapolis Colts | `tx:1279012938920787968` | 2025-10-01 | 5 |
| Jason Myers | `tx:1291820787824590848` | 2025-11-05 | 10 |
| Jonathon Brooks | `tx:1268069192796491776` | 2025-09-01 | 1 |
| Los Angeles Rams | `tx:1268345620540690432` | 2025-09-01 | 1 |
| Malik Washington | `tx:1273989571889102848` | 2025-09-17 | 3 |
| Michael Carter | `tx:1298336961068560384` | 2025-11-23 | 12 |
| Michael Wilson | `tx:1294821049795350528` | 2025-11-13 | 11 |
| New Orleans Saints | `tx:1291869173902770176` | 2025-11-05 | 10 |
| Parker Washington | `tx:1290000525504294912` | 2025-10-31 | 9 |
| Ray Davis | `tx:1281611004031045632` | 2025-10-08 | 6 |
| Tyreek Hill | `tx:1283116823738322944` | 2025-10-12 | 6 |

Os 3 CORRETO, por waiver com bid FAAB real: Dike `tx:1296727996714975232` (19/11, $8),
Gadsden `tx:1276420291110653952` (24/09, $16), Shough `tx:1289076463496101888` (29/10, $18).

##### ⚠️ As duas aberturas de 2024 candidatas — a falsificação parcial que o owner pediu para destacar

Nenhum dos 34 tem **transação de aquisição** de 2024 como último evento. Mas **dois** têm uma
aquisição de 2024 **pelo mesmo owner que os readquiriu em 2025** — e, se a **6.8** valer, é ela que
abre o contrato vigente, **não** a de 2025:

1. ⛔ **Kenny Gainwell** — `ESPN FANTASY LEAGUE` o adicionou como FA em **2024-11-27**, dropou em
   **2025-08-26** (pré-temporada) e o **readquiriu em 2025-09-01**, seis dias depois. É a 6.8
   literal: *readquirido pelo próprio owner*. Sob essa leitura: 2024 = ano 1, 2025 = ano 2,
   **2026 = ano 3 ⇒ valorização ⇒ o banco está CERTO e o rollover acerta.** Sob a leitura
   "recomeçou", está errado. **As duas leituras dão respostas opostas — é decisão do owner.**
2. ⚠️ **Jake Bates** — `AlexTheDawg` o adicionou por waiver em **2024-10-08**, dropou em
   **2024-12-04**, e o readquiriu como FA em **2025-09-24**. Mas houve **dono intermediário**
   (Vila Gugu FC / achane, de 12/2024 a 09/2025), o que enfraquece muito a 6.8.

Os outros 8 ambíguos têm **abertura inequivocamente em 2025** — o flag é sobre *qual* evento de
2025 abre, não sobre o ano. Para eles a resposta de 2026 (ano 2) é a mesma nas duas leituras.

##### Premissas refutadas

1. ⛔ **"os 5 `fa_waiver` entraram por waiver SEM contrato prévio"** (premissa do prompt) — **falso
   para Jaylin Noel**: ele foi **draftado no leilão de 2025** (r2p17, $1) pelo próprio
   `Fazenda Pederasta`, dropado, passou por achane e **voltou por waiver ($0) ao time original**.
   É 6.8 pura, com contrato prévio real. Os outros 4 (Dike, Willis, Gadsden, Shough) confirmam a
   premissa. **Sem efeito prático:** em qualquer leitura, o contrato de Noel abre em 2025.
2. ⛔ **"o delta é +$6"** — é +$6 **só com o ESPN provisório de hoje**. Ver a tabela de
   sensibilidade: escala a +$168.
3. ⛔ **"o grupo do problema são os 29 e os 5 são indeterminados"** — os **34** recebem a regra
   errada; os 5 por causa do enum, não do dado, e o dado deles está **certo**.
4. ⛔ **"o bid FAAB não é capturado"** (F1C-T1) — verdade quanto ao **sync**, mas o dado **está na
   API** e foi lido aqui: Dike $8, Gadsden $16, Shough $18, Tucker $66, Stafford $35. É recuperável
   a qualquer momento; não se perdeu.
5. ✅ **`team_name` é instável entre ligas, confirmado** — `Vila Gugu FC` (2024) e `achane`
   (2025/26) são o **mesmo `owner_id`** (`867557566065045504`). Esta verificação resolveu times por
   `owner_id` por liga, não por nome. Reforça a lição da F1B.
6. ⚠️ **Ressalva de fonte (não refutação, limitação):** o banco lido é o **seed local**
   (`dynasty.db` do git, 01/08), **não** o `/data/dynasty.db` de produção. Ele **reflete as trades
   de 28-30/07/2026** (Robinson→rafaelferreirap, Bigsby→mongoloides), o que indica que está fresco
   — mas **a lista nominal deve ser reconferida contra o banco vivo antes da correção**.

##### O que o owner precisa decidir

1. ⛔ **Aprovar (ou não) os 21 CORRIGIR** — todos com transação de 2025 citada acima. A correção é
   `contract_year: 2 → 1`, e passa por `correct_player_salary`, **nunca patch**.
2. ⛔ **Decidir os 3 CORRETO** — o dado está certo; a exposição é do enum. Requer `fa_waiver` em
   `_WAIVER_TYPES` (que, verificado, **só** os alcança).
3. ⚠️ **Arbitrar a 6.8 em Gainwell e Bates** — é a única dúvida com resposta oposta nas duas
   leituras.
4. ⚠️ **Os outros 8 ambíguos** — sob a **6.7** (a trade carrega o contrato) os 4 de "trade depois"
   (Stafford, Robinson, Stroud, K. Miller) são **determinados** e entrariam em CORRIGIR; só
   Stafford tem delta vivo hoje ($2 → $3). **Não os incluí na lista** porque o prompt classificou
   "trade no meio" como dúvida — mas registro que a 6.7 os resolve.

---

#### CANAL (MAN-OFF26-20-CANAL, 05/08/2026) — Gainwell resolvido pelo canal, e o grupo fecha em 22

**Read-only absoluto.** O owner recusou aprovar sem resolver o Gainwell pelo **canal** — o
discriminador que ele próprio fixou — em vez do padrão (mesmo owner + 6 dias). Tinha razão.

##### T1 — Gainwell: o canal é `free_agent`. Ele ENTRA no grupo.

A reaquisição de 2025-09-01 é **`tx:1268069831555424256`** (liga 2025, leg 1, `created`
2025-09-01): **`type: "free_agent"`, `status: "complete"`, `settings: null`, `waiver_bid: null`**.
Reconfirmada **ao vivo** na API nesta sessão (não só do dump). O drop pelo mesmo owner fora 6 dias
antes (`tx:1266160615966134272`, 2025-08-26).

**Prova de contraste na própria história dele:** em 2024 houve um waiver claim **sobre o Gainwell**
(`tx:1159714113438957568`, status `failed`) — e esse veio com `type: "waiver"` e
`settings.waiver_bid: 0`. Quando é waiver, a API marca; o add de 2025 não tem nada disso.

**Veredito condicional aplicado:** canal FA ⇒ a 6.8 não se aplica (ela só existe no canal waiver)
⇒ o contrato **reabre em 2025** ⇒ `contract_year = 2` está **errado também para ele**.
⛔ **A leitura "6.8 literal" da VERIF cai.** A leitura do owner (6 dias atravessam o waiver period)
está **confirmada pelo dado**. **O grupo de correção fecha em 22.**

##### T2 — Auditoria de canal dos 21 + Bates: `free_agent` em 23 de 23

Os 21 CORRIGIR: **21/21 com `type: "free_agent"`, `status: "complete"`, sem bid** (refs e datas na
tabela da VERIF — tipos reconferidos um a um contra a transação da API). **Nenhum waiver
inesperado.** Bates: opener `tx:1276659069179924480` (2025-09-24) também **`free_agent`** —
veredito de ambiguidade mantido como o prompt pede, mas registrado: sob a mesma régua do T1
(canal FA ⇒ 6.8 n/a), a ambiguidade dele se dissolve e ele seria elegível (delta $0 hoje:
ESPN REF 1.0).

✅ **Invariante estrutural que blinda o discriminador, medido nas 1125 transações do chain:**
**225/225** waivers completos têm `settings.waiver_bid`; **661/661** `free_agent` completos não
têm. O canal não é convenção de rótulo — é estrutura da API.

##### T3 — A conta da correção, e o que ela toca

Os 22 são **homogêneos**: `contract_year = 2` · `contract_start_season = 2025` ·
`acquisition_type = free_agent` · `salary = $1` · `needs_review = 0`.

**Campo tocado: UM SÓ — `Player.contract_year`, 2 → 1.** Nada mais:
- `salary` **fica** ($1 é o ano-1 de FA correto);
- `contract_start_season` **fica** (2025 já está certo);
- `acquisition_type` **fica** (`free_agent` é o canal real, e `free_agent ∈ _WAIVER_TYPES` ⇒ com
  `contract_year = 1` o rollover aplica sozinho o `0,8 × ESPN REF` no `next_yr = 2` — **a correção
  de dado basta; não precisa mexer no motor para os 22**);
- `espn_ref_value` **fica** (dono: import ESPN).

| Jogador | cy antes→depois | Regra antes → depois | 2026 antes → depois (ESPN REF atual) |
|---|---|---|---|
| Alec Pierce | 2→1 | valorização → 0,8 | $3 → **$5** |
| Christian Watson | 2→1 | valorização → 0,8 | $3 → **$4** |
| Parker Washington | 2→1 | valorização → 0,8 | $3 → **$4** |
| Michael Wilson | 2→1 | valorização → 0,8 | $1 → **$2** |
| Kenny Gainwell | 2→1 | valorização → 0,8 | $1 → $1 |
| Jonathon Brooks | 2→1 | valorização → 0,8 | $1 → $1 |
| os outros 16 (ESPN REF 1.0) | 2→1 | valorização → 0,8 | $1 → $1 |

**Total hoje: $28 → $33 (+$5).** Com a ESPN definitiva de 18/08 o delta escala (tabela de
sensibilidade da VERIF). Os 16 com ESPN REF 1.0 têm delta $0 **hoje** — a correção deles é de
**contagem**, e o valor aparece quando a definitiva entrar.

⚠️ **Declaração de mecanismo — há um vão canônico, e o owner precisa saber antes de aprovar:**
- `correct_player_salary` (models.py:216) corrige **salário** — não toca `contract_year`.
- A única porta que edita `contract_year` com trilha é o **approve do M2**
  (`_REVIEW_ALLOWED_EDITS`, admin.py:1015) — mas exige `needs_review = True`, e os 22 estão em 0.
- ⇒ **Não existe hoje porta canônica para corrigir `contract_year` fora de revisão.** O prompt de
  correção deverá criá-la no molde do M2: escrita do campo + `PlayerHistory` de auditoria
  (old→new nas notes) na mesma transação. **Trilha resultante:** 1 linha de `PlayerHistory` por
  jogador; `SalaryHistory` intocada (não há mudança de salário — e ela está vazia, F1B).

##### T4 — Reconferência contra o vivo: BLOQUEADA desta máquina, comando pronto

`/data/dynasty.db` só é alcançável via Render Dashboard → Shell (sem CLI/API key local; rotas de
prod atrás de OAuth). A VERIF leu o **seed local** (git, 01/08), que reflete as trades de
28-30/07 — frescor indireto, não prova. **Antes da correção, colar no Render Shell:**

```
sqlite3 -header -column /data/dynasty.db "select id,name,contract_year,contract_start_season,acquisition_type,salary,espn_ref_value,needs_review,is_dropped from players where sleeper_player_id in ('11603','8142','8167','6865','DET','11834','9486','4066','5970','HOU','IND','2747','11583','7567','LAR','11610','7607','10232','NO','9487','11575','3321') order by name;"
```

Esperado: 22 linhas, todas `contract_year=2, contract_start_season=2025,
acquisition_type=free_agent, salary=1, needs_review=0, is_dropped=0`. Qualquer divergência
suspende a linha correspondente.

##### Premissas refutadas / confirmadas

1. ✅ **A leitura do owner confirmada pelo dado:** 6 dias bastaram para atravessar o waiver period
   — o add voltou como `free_agent`.
2. ⛔ **"Gainwell é 6.8 literal" (VERIF) cai** — classificação por padrão, não por canal; o canal
   decide, e é FA.
3. ⚠️ **A régua do T1 generaliza além do escopo pedido** (registrado, não decidido): os flags
   "6.8 mesmo owner" de **Tucker** e **Bigsby** também se dissolvem (openers `free_agent`), e o de
   **Bates**; já **Willis** e **Noel** entraram por **waiver** real (bid $0) — para eles o flag
   segue de pé, e o caso Noel (claim que carrega contrato de leilão 2025) segue sendo o
   indeterminado legítimo.
4. ✅ **`fa_auction` não contamina o grupo:** nenhum dos 22 tem evento de leilão FA em 2025 como
   opener — os 24 do `fa_auction` são população disjunta (F1C).

#### FIX (MAN-OFF26-20-FIX, 06/08/2026) — porta canônica criada + ensaio 22/22; prod aguarda o owner

**Aprovação nominal do owner (05/08/2026)** sobre o estado conferido no T4 (prod ≡ seed, 22/22).
O vão canônico declarado no CANAL foi preenchido e a correção foi ensaiada de ponta a ponta em
cópia do seed. **A escrita em produção é do owner, no Render Shell** (passo a passo abaixo).

##### O que nasceu

- **`contract_year_correction.py` — a porta canônica** (molde M2/`correct_player_salary`):
  núcleo **puro** (`guard_mismatches`/`plan_correction` — sem Flask/DB) + camada ORM
  (`apply_contract_year_correction`) que encena `Player.contract_year` novo + `PlayerHistory`
  (`event_type='contract_year_correction'`, old→new nas notes, `sleeper_event_ref`) **na mesma
  transação, SEM commit** — o chamador comita, ou rollback desfaz escrita e trilha juntas.
  Guarda pré-escrita inegociável: linha que não case o estado esperado é **pulada e reportada**
  (ausente e ambíguo — inclusive duplicata dropada — também pulam). IDs sempre string
  (DEFs por sigla).
- **`off26_20_fix.py` — runner one-shot** com os 22 travados por `sleeper_player_id`, guarda =
  estado aprovado no T4, `event_ref='fix:off26-20'`. `--check` (read-only: guarda + dry-run do
  rollover) e `--apply` (**recusa escrever sem `--backup` conferido**: existência + tamanho).
  Pós-commit, verificação por conexão independente: diff da tabela inteira (só os elegíveis
  mudaram, e só `contract_year`+`updated_at`), contagem de trilha, casos vivos do rollover.
  Não roda o boot do app.py (app Flask mínimo — zero efeito colateral de import/sync).
- **`contract_year_correction_test.py` — 20 testes** (núcleo puro / ORM em memória / config do
  runner): guarda campo a campo, normalização SQL↔ORM, atomicidade via rollback, idempotência
  (2ª passada pula tudo), DEF por sigla, fora-da-lista intocado, casos vivos pelo motor real.

##### Ensaio (06/08, cópia do seed — o seed do git NÃO foi tocado)

`--check`: 22/22 elegíveis. `--apply`: 22 corrigidos, **22 linhas alteradas na tabela inteira**
(só `contract_year`+`updated_at`), 22 linhas de trilha, dry-run com os 4 casos vivos conferindo
(**Pierce $5, Watson $4, P. Washington $4, Wilson $2**), exit 0. Segunda `--apply`: 22 pulados
pela guarda (`contract_year=1`), zero escrita, exit 1. Suítes: **54 + 34 + 14 + 20 verdes**.

##### Execução em produção (owner, Render Shell) — nesta ordem

```
sqlite3 /data/dynasty.db ".backup '/data/pre_off26_20_fix.db'"
ls -la /data/pre_off26_20_fix.db
python off26_20_fix.py --check
python off26_20_fix.py --apply --backup /data/pre_off26_20_fix.db
```

Esperado: `--check` termina em "OK — 22/22 elegíveis, casos vivos conferem"; `--apply` termina em
"✅ OK" com "22 corrigidos; 22 linhas alteradas; 22 linhas de trilha". Qualquer PULADO no relatório
= linha fora do estado aprovado, deixada intacta de propósito. (`DYNASTY_DB=/data/dynasty.db` já
está no ambiente do serviço; o deploy que leva o runner precisa estar no ar antes.)

##### ✅ EXECUTADO EM PRODUÇÃO (owner, Render Shell, 06/08/2026 ~12:55 UTC)

Sequência integral rodada pelo owner em `/data/dynasty.db` (transcript conferido nesta sessão):

- **Backup:** `/data/pre_off26_20_fix.db`, 606.208 bytes, `ls -la` conferido ANTES da escrita.
- **`--check`:** 22/22 elegíveis, guarda exata, casos vivos conferem — prod ainda ≡ estado T4.
- **`--apply`:** **22 corrigidos (`contract_year 2 -> 1`); 22 linhas alteradas na tabela inteira
  (só `contract_year`+`updated_at`); 22 linhas de trilha** em `player_history`
  (`event_type='contract_year_correction'`, `sleeper_event_ref='fix:off26-20'`); dry-run do
  rollover com **Pierce $5, Watson $4, P. Washington $4, Wilson $2** ✓ — terminou em "✅ OK".
- Salário, `contract_start_season`, `acquisition_type`, `espn_ref_value`, `needs_review`:
  intocados (verificação por diff de tabela inteira, conexão independente). `SalaryHistory`
  não tocada. Board intacto, draft não iniciado.
- Nota: os nomes de time na trilha refletem prod ("Tropa do Jarra 🏆" — renomeado vs. seed).
- **O seed do git segue PRÉ-correção nos 22** (inofensivo: `init_data.py` nunca sobrescreve o
  vivo; corrigir o seed é opcional e só faria diferença num redeploy do zero).

##### Pendências (após a execução)

1. ~~Enum dos 5 `fa_waiver`~~ → **✅ resolvido no CLOSE** (decisão do owner 06/08, ver abaixo).
2. ~~Coluna PROJ~~ → **✅ resolvido no CLOSE** (fonte única, ver abaixo).
3. **Smoke visual pós-deploy** (roster/salary_history dos corrigidos — "Ano 1/4" e trilha;
   + PROJ e enum, ver pendências do CLOSE).
4. (Opcional) Alinhar o seed do git ao pós-correção — rodar o runner no seed local, ou
   substituir o seed por um backup de prod, quando o owner quiser.

#### CLOSE (MAN-OFF26-20-CLOSE, 06/08/2026) — enum `fa_waiver` + PROJ na fonte única + Bryant/censo

##### T2 — `fa_waiver ∈ _WAIVER_TYPES` (decisão do owner, 06/08)

**Regra do owner:** quem entra por waiver **sem contrato prévio a carregar** segue a trilha de FA
(ano 1 = $1, ano 2 = 0,8 × ESPN REF) — a regra de carregar contrato existe para impedir
reestruturação via FAAB; sem contrato anterior, não há o que proteger. `fa_waiver` é justamente o
que o **sync grava** para waiver claims ([sync_sleeper.py:912](sync_sleeper.py#L912)) — o enum
alinha o motor ao vocabulário do sync.

- **Guarda de alcance revalidada NA HORA (06/08, seed):** `fa_waiver` vivos = **5 em ano 1**
  (Dike 12540, Noel 12536, Willis 8161, Gadsden 12493, Shough 12545 — todos $1, ESPN REF 1.0,
  css 2025) + **32 em ano 2** (contrato carregado; `next_yr = 3` ⇒ **nunca** entram no ramo 0,8 —
  VALORIZAÇÃO, inalterados). Contagem **idêntica à de 04/08** — nenhuma trade mudou o quadro.
  O efeito da mudança alcança **exatamente os 5**.
- Hoje os 5 dão $1 → $1 no rollover (0,8×1,0 trunca no piso) — o efeito aparece quando a ESPN
  definitiva de 18/08 entrar.
- **Nota Noel (registrada):** waiver $0 pelo próprio time que o draftou — padrão 6.8, efeito
  prático hoje nulo; incluído na trilha FA **por decisão explícita do owner**.
- `_WAIVER_TYPES` vive só no `salary_engine` (4 pontos, todos coerentes); testes em
  `trilha_fa_proj_test.py` fixam: ano 1 = $1, 1→2 = 0,8, contrato carregado inalterado,
  alcance do 0,8 restrito à transição 1→2, projeção ≡ rollover.

##### T3 — Pat Bryant: CORRETO fora dos 22; censo: zero casos novos

**Bryant (12492) resolvido pela API, mesmo método do arco:** rookie draft 2025 (liga
1224848075609100288, round 3 pick 28) → **drop 01/10/2025** (`tx:1279129013574451200`) →
**reaquisição 22/10/2025 pelo canal FA**: `tx:1286718252017258496`, `type='free_agent'`,
`status='complete'`, `settings=None`, `waiver_bid=None` (o invariante estrutural 225/661
confirma o canal). Contrato vigente abre em 2025 por FA ⇒ estado correto =
`free_agent/css 2025/**ano 1**` — **exatamente o que o banco já tem**. Os 22 estavam errados
em ano 2; Bryant sempre esteve em ano 1. **Nada a corrigir.**

**Censo `free_agent` + `css=2025` vivos (seed):** 39 = **22 corrigidos** + 17 fora:
- **10 em ano 1** (Borregales, Cam Little, Cam Ward, C. Rodriguez, J. Lane, Hollins, **Bryant**,
  Ewers, Shedeur, Tez Johnson) — mesma forma do Bryant, **já corretos**;
- **7 em ano 2** (B. Robinson, Stroud, Bates, K. Miller, Stafford, Bigsby, Tucker) — **os 7
  ambíguos/excluídos que a VERIF já tinha** (29 do F1C = 22 + estes 7). **Zero casos novos.**

**Premissas do prompt refutadas:** (a) *"se é FA de 2025, deveria ter entrado na correção"* —
⛔ só se estivesse em ano 2; ele está em ano 1 (o próprio prompt antecipou a hipótese, confirmada);
(b) *"FA de 2025 sem passagem anterior pela liga"* — ⛔ Bryant TEVE passagem (draftado e dropado
em 2025); e o censo mostra que **não há** o caso hipotético em estado errado.

##### T4 — Coluna PROJ na fonte única

`Player.projected_next_salary()` ([models.py](models.py#L176)) agora **delega** a
`salary_engine.project_next_salary` — a mesma fonte do Cap Projector, da porta `/budget` e do
rollover real. A reconstrução via `compute_salary_for_year` (descartava o salário armazenado;
26/248 divergentes, +$62 sempre superestimando) **morreu nesse método** — `compute_salary_for_year`
segue existindo **só** para a calculadora/`full_contract_table` (exibição de contrato completo,
uso legítimo). Consumidor único da coluna ([_macros.html:73](templates/_macros.html#L73))
inalterado — muda a fonte, não a tela. **Guarda anti-réplica** (molde OFF26-16):
`trilha_fa_proj_test.TestGuardaAntiReplica` falha se `compute_salary_for_year` reaparecer em
`models.py`.

Validação pelos casos conhecidos (dados do seed): **Hampton $26** (não $44), **Jeanty $57** (não
$45 — o caso que SOBE), **Egbuka $13** (não $26), **McMillan $15** (não $30), **Watson ano 2 → $3**
(não $4 — o caso que abriu a F1). Os 22 corrigidos passam a exibir o valor do dry-run (Pierce $5)
— **em prod**; no seed local seguem pré-correção.

##### Suítes (06/08): 54 + 34 + 14 + 20 + **17 novas** (`trilha_fa_proj_test.py`) — todas verdes

##### Pendências de smoke (prod, pós-deploy)

1. **PROJ nas telas:** `/` e `/team/<id>` — conferir Hampton $26, Jeanty $57, Egbuka $13 e um dos
   22 (Pierce $5).
2. **Enum no dry-run de prod:** os 5 `fa_waiver` de ano 1 com regra "Waiver Ano 2" no preview do
   rollover (hoje $1 → $1 pelo piso).
3. Revalidar a contagem 5/32 em prod na hora do rollover:
   `sqlite3 /data/dynasty.db "select contract_year, count(*) from players where acquisition_type='fa_waiver' and is_dropped=0 group by 1;"`

---

## Itens UX

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

### UX10 — Fotos de jogadores desatualizadas
🔲 **Registrado 08/08/2026 (MAN-UX10-UX11-REG)** — Prioridade **Baixa** (cosmético, sem impacto em
dados) — **registro apenas; nenhuma diagnose feita**

**Sintoma reportado pelo owner (08/08/2026):** alguns jogadores exibem a **foto de temporada
anterior**. Exemplo concreto dado pelo owner: **David Montgomery**.

**Por que a prioridade é Baixa:** é cosmético. A **identidade** do jogador no Manager é resolvida
por `sleeper_id` (precedente do incidente "Brown"), então uma foto velha não contamina salário,
contrato, roster nem auditoria. O custo é de leitura: o owner reconhece jogador pela foto, e uma
foto de outro time induz erro de percepção — não de dado.

#### O que a F1 tem de responder ANTES de qualquer fix

⛔ **Não presumir a causa.** As três hipóteses abaixo levam a correções **diferentes e
incompatíveis**, e escolher errado produz um fix que não muda nada (ou que mascara o problema):

- **(a) cache** — a URL do CDN está **correta**, e o que serve imagem velha é cache (do navegador
  ou do próprio CDN). Fix seria de invalidação/cache-busting, **não** de construção de URL.
- **(b) URL construída com componente desatualizado** — algum ponto do Manager monta a URL com
  **temporada ou time** embutido, e esse componente ficou para trás. Fix seria na construção.
- **(c) fonte keyed por algo além do `sleeper_id`** — a imagem é buscada por uma chave que não é a
  identidade canônica. Fix seria de chave, e essa é a hipótese com maior chance de ter irmãos em
  outras telas.

**Pergunta de réplica (obrigatória, no molde das últimas sessões):** **a construção da URL de foto
existe em mais de um lugar — templates, JS, Python?** Se existir, o fix precisa nascer na fonte e
alcançar os outros sítios, ou vira a enésima réplica. A F1 responde antes de propor caminho.

**Método:** o exemplo do owner (David Montgomery) é o **caso-âncora** — a F1 deve começar por ele,
comparando o que a tela pede com o que o CDN devolve, e só então generalizar.

**Cross-refs:** [[UX1]] e [[UX3]] (✅ — foi por ali que as fotos entraram nas telas de roster e nas
telas densas; a construção de URL provavelmente nasceu numa dessas, ver `improvements_archive.md`),
[[UX11]] (mesmo registro, mesma família de "dado de jogador exibido sem fonte declarada").

**Transbordo da UX12-F1 (08/08/2026, MAN-UX12-REFINE): hipóteses (b) e (c) descartadas por
evidência.** A Q1 da diagnose do [[UX12]] (evidência no `improvements_archive.md`, seção UX12)
mapeou a construção da URL de foto de jogador: existem **exatamente 2 construtores,
deliberadamente espelhados** (macro server `player_photo` em `_macros.html:28-35` + helper JS
`renderPlayerPhoto` em `base.html:275-281`, cada um documentando o outro como contraparte), ambos
com a mesma URL `sleepercdn.com/content/nfl/players/thumb/<sleeper_player_id>.jpg` — **keyed só
por `sleeper_player_id`, sem componente de temporada nem de time**. Logo: **(b)** não tem
componente a estar desatualizado e **(c)** a chave é exatamente a identidade canônica — as duas
hipóteses ficam **sem mecanismo no lado do Manager**. Também responde a pergunta de réplica:
zero construção inline fora dos 2 helpers (os `sleepercdn.com/avatars/…` restantes são avatar de
**owner**, família distinta). **Sobra a hipótese (a)** — cache (navegador/CDN) ou o próprio CDN
do Sleeper servindo thumb velho — que não é corrigível por construção de URL; a F1 residual
deste item é confrontar o caso-âncora (David Montgomery) com o que o CDN devolve hoje.

---

### UX13 — Timeline exibe `event_type` cru `contract_year_correction`
🔲 **Registrado 08/08/2026 (MAN-O2-B1-DONE)** — Prioridade **Baixa** — **display de 1 linha,
causa evidente, sem diagnose; candidato a carona** em qualquer sessão que toque os templates

**Sintoma (visto pelo owner no smoke do Batch 1 do [[O2]]):** na Timeline do perfil do jogador,
eventos de correção de `contract_year` aparecem com a string crua `contract_year_correction`,
enquanto todos os demais eventos têm label PT-BR + badge.

**Causa (evidente — por isso sem F1):** o `event_type` é escrito por
`contract_year_correction.py` (porta canônica do OFF26-20-FIX, `EVENT_TYPE =
"contract_year_correction"`), e a chave **não existe** nos dicionários `EVENT_LABELS`/
`EVENT_BADGES` dos templates — o render cai no fallback `EVENT_LABELS[e.event_type] ||
e.event_type`.

**Superfície do fix (2 sítios, réplica declarada):** `templates/player_detail.html` e
`templates/salary_history.html` — o dicionário do primeiro é **cópia declarada** do segundo
("Labels e badges — copiados do salary_history", comentário no próprio template). O fix de uma
linha entra **nos dois**; se um dia os dicionários forem unificados, é outra conversa (e outro
item — não este).

**Cross-refs:** [[O2]] (onde o sintoma apareceu), OFF26-20-FIX (quem escreve o evento).

---

### UX14 — Time NFL de dropado com fallback no pool
🔲 **Registrado 10/08/2026 (MAN-ARC-BUSCA-DONE)** — Prioridade **Baixa/Média** — **registro
apenas; nenhuma diagnose feita**

**Sintoma (visto pelo owner no smoke do M21-A, 10/08):** o perfil do **Darren Waller** exibe
`🏈 —` — `Player.nfl_team` está **vazio** no banco, porque o sync só atualiza o campo de quem
está em roster (e só com valor truthy, a ressalva do [[UX11]]). Com FAs agora alcançáveis pela
busca (fatia A do [[M21]]), esse `—` aparece com mais frequência.

**Hipótese registrada (⛔ NÃO arbitrada):** **fallback de LEITURA no pool do Sleeper** quando o
campo local é vazio/dropado — o precedente é o [[O2]], que lê o pool **sem persistir nada**
(`nfl_context.py`, cache F13, sem rede no caminho de página). Se o pool também não tiver time,
`—` é **correto** (FA real na NFL — Waller pode ser exatamente esse caso).

**Questão de réplica OBRIGATÓRIA para a F1:** o fallback entra **na fonte única** mapeada pela
Q1 da UX12-F1 (`Player.nfl_team`, 8 sítios lendo a mesma coluna) ou vira **segunda fonte por
tela**? Se cada tela decidir seu fallback, a réplica que a Q1 refutou nasce aqui.

**Cross-refs:** [[M21]] (a fatia A tornou o sintoma visível), [[UX11]] (a mesma ressalva de
staleness, decidida — não reabrir), [[O2]] (o precedente de leitura do pool), [[F13]] (onde o
cache vive).

---

### UX15 — Jogador pré-selecionado na página de trade
🔲 **Registrado 10/08/2026 (MAN-ARC-BUSCA-DONE)** — Prioridade **Baixa** — **registro apenas;
nenhuma diagnose feita**

**Pedido do owner (smoke de 10/08):** o botão "⇄ Propor Trade" do perfil ([[M14]]) já navega com
**os dois times pré-selecionados**; falta **o jogador chegar marcado** no quadro — hoje o usuário
re-encontra na lista o jogador de cujo perfil veio.

**Enquadramento:** refinamento do **campo 3 do [[UX12]]** ("link p/ trade com o time já
pré-selecionado" — requisitos no archive, seção UX12); o campo fechou como "já existe" porque a
pré-seleção de times existia, e este item registra o degrau seguinte. **Provável F2 direta** — a
confirmar na F1 a **réplica**: a pré-seleção via query params existe em **quantos caminhos de
entrada** da página de trade (perfil, [[M9]]/picks, outros)? O novo param deve entrar na mesma
engrenagem, não criar um caminho paralelo.

**Cross-refs:** [[M14]] (query params existentes), [[UX12]] (origem do campo 3, archive),
[[M13]] (o botão no perfil), [[T1]] (o simulador onde o quadro vive).

---

### UX17 — Paridade da barra de status: roster próprio × detalhe de time
🔲 **Pendente** — Prioridade **Média** — registrado 13/08/2026 (MAN-L3-CLOSE-REG),
**registro apenas; nenhuma diagnose feita**

**Problema:** depois do [[L3]], a `/team/<id>` passou a mostrar **cap atual, resto atual, cap
projetado (com PROV), resto projetado, dynasty, ativos, IR e quebra por posição**. A tela do
**próprio roster** (`/`) segue com **salário usado, restante e %** — mais pobre justamente na
tela que o owner mais abre, e sem a grandeza de planejamento que motivou o L3 inteiro.

**Objetivo:** a mesma riqueza no roster próprio, sem criar uma segunda definição de nada.

**Perguntas que a F1 tem de MEDIR (⛔ não herdar premissa):**
1. **A barra do detalhe é macro compartilhável ou markup próprio?** — a [[L3]]-FIX-UX derrubou
   exatamente essa classe de premissa: o prompt afirmava que a macro do card era compartilhada com
   o `/team/<id>`, e **não era** (os dois usos eram os dois ramos do gate). Medir antes.
2. **O render de `/` já dispõe dos dados ou precisa invocar `compose_budget`?** — e **a que custo
   de query**: hoje `/` **não** consulta `ESPNImportLog` (selo PROV) nem `rollover_done` (gate). No
   [[L3]] o gate custou **+2 queries** por render, e o mesmo preço se repetiria aqui.
3. **Gate de fase e tags de provisoriedade valem idênticos?** — a resposta esperada é sim (mesma
   grandeza, mesma semântica), mas é decisão a registrar, não a assumir.

---

**F1 (13/08/2026, MAN-UX17-F1 — read-only; nenhuma escrita em código):**

**1. Compartilhamento — veredicto: MARKUP PRÓPRIO, zero compartilhamento.** `team-status-bar`,
`status-item` e `status-label` aparecem **exclusivamente** em `templates/team_detail.html`;
`_macros.html` tem **8 macros e nenhuma** de barra de status. O `/` usa **outra família de
classes** (`cap-bar-wrap` / `cap-bar-labels` / `cap-bar`, em `roster.html`), que compartilha só o
`.cap-bar` com o `cap_projector`. ⇒ **a paridade exige CRIAR o compartilhamento** (macro nova, no
molde do que o [[UX4]] fez com a linha de roster) — copiar o markup seria a réplica que esta
família proíbe. (A premissa "é macro compartilhável" foi medida, não assumida: a saga [[L3]] já
derrubou exatamente essa suposição uma vez.)

**2. De onde vem cada grandeza — e o que o `/` já tem:**
| Grandeza | Fonte no `/team/<id>` | O `/` já dispõe? |
|---|---|---|
| cap atual | `salary_engine.roster_salary(players)` | ✅ `summary.total_cap` — **mesma fonte única** ([[OFF26-16]]) |
| resto atual | `SALARY_CAP − cap_used` | ✅ |
| cap/resto **projetado** | `routes.salary.compose_budget(players)` | ❌ — mas **0 query** (os players já estão carregados) |
| selo **PROV** | `ESPNImportLog(season+1, status="final")` | ❌ — **+1 query** |
| **gate** de fase | `_projection_open()` → `get_config("rollover_done")` | ❌ — **+2 queries** |
| dynasty | `resolve_asset_value` sobre `dv_map` | ✅ **já carregado** (`roster.py:82-86`, UX4) |
| ativos / IR | derivação de `is_on_ir` | ✅ `active_players` / `ir_players` |
| quebra por posição | laço sobre `players` | ✅ derivável, 0 query |

**Custo medido (não estimado):** `/` hoje = **15 queries**; com a paridade = **18** (`/team/<id>`
faz 20 e `/league` 19, para calibrar). **+3, todas O(1) — nada por jogador.** Produzir **todas** as
grandezas da barra rica sobre os dados já carregados custou **0 queries** na medição (time do
owner: cap atual $176/$200 · cap proj **$177** · resto proj **$23** · dynasty 31.304 · 18 ativos ·
0 IR · 6 posições).

⚠️ **Achado estrutural — o mais importante desta F1:** `compose_budget` vive em
`routes/salary.py`, que **não importa** roster nem league ⇒ import de topo em `roster.py` é
**seguro**. Mas `_projection_open` vive em `routes/league.py`, que **importa `routes.roster`**
([routes/league.py:15](routes/league.py#L15)) ⇒ `roster.py` importá-lo no topo **fecha um ciclo de
import**. Saídas: **(a)** import diferido dentro da view · **(b)** mover o gate para módulo neutro ·
**(c)** ⛔ reimplementar a regra (= 2ª definição da fase, o que o [[L3]] proíbe). **Escolha
estrutural — do owner/F2, não desta F1.**

**3. Gate e PROV no `/`:** aplicam-se **identicamente** — mesma grandeza, mesma semântica,
pós-rollover o bloco projetado some e as correntes permanecem (é o que o `/team/<id>` já faz).
⚠️ Detalhe que muda o enunciado: **`/` não é "a tela do próprio roster"** — é um **visualizador de
qualquer time** via `?team=` ([routes/roster.py:63-73](routes/roster.py#L63-L73)), com *fallback*
para o time do usuário. A projeção deve seguir **o time exibido** (coerente com o detalhe); só o
banner M1 de cap estourado é que permanece amarrado ao time **do usuário**, por desenho.

**4. O que existe hoje no `/` e a barra rica NÃO tem** (cada um com parecer):
- **`%` de $200 explícito** — no `/team/<id>` o percentual só existe no `title` da barra de
  progresso → **perda não-intencional** se a barra rica for copiada ao pé da letra. Parecer:
  **preservar**.
- **3º nível de alerta no "Restante"** (`text-warn` abaixo de $20; o detalhe só marca negativo) →
  **perda não-intencional**. Parecer: **preservar** — é sinal de planejamento, não decoração.
- **Barra de progresso colorida** — existe nas **duas** (o detalhe ganhou a sua no UX4-c) → **sem
  perda**.
- **Busca/troca de equipe** (`team-filter-input` + dropdown) → **não faz parte da barra**: vive no
  `page-header-right`, região irmã. **Sem perda** — só não confundir uma coisa com a outra.
- **Banners** (M1 cap estourado · Ano 4 · needs_review) e **alerta de IR com nomes** → ficam abaixo
  do header, independentes da barra → **sem perda**.

**5. Premissas × código.** (a) *"a barra do detalhe é macro compartilhável"* → **REFUTADA**
(markup próprio). (b) *"o `/` exibe apenas salary usado/restante/%"* → **confirmada**
([roster.html:24-45](templates/roster.html#L24-L45)), com o adendo de que a barra de progresso e os
**3 níveis de cor** também estão lá e não aparecem na lista do prompt. (c) *"precisaria invocar o
helper de composição"* → **confirmada, e é a parte barata** (0 query); o que custa são gate e PROV.
(d) *"custo de query adicional"* → **quantificado: 15 → 18**. (e) *"tela do próprio roster"* →
**imprecisa**, ver item 3.

**Cross-refs:** [[UX4]] (a **tabela** de roster já convergiu entre as duas telas — este item é o
mesmo movimento para a **barra**), [[L3]] (helper canônico, gate, PROV), [[OFF26-16]] (a régua
única de folha que ambas as telas consomem), [[M17]] (o `/` deriva do usuário logado).

---

### OPS1 — Higiene do working tree local (banco de dev, handoffs soltos, backups pré-O5)
🔲 **Registrado 14/08/2026 (MAN-CLOSE-LOTE-14-08)** — Prioridade **Baixa** —
⚠️ **registro apenas: nenhuma ação de limpeza executada nesta sessão** (nenhum arquivo movido,
apagado ou ignorado)

**Problema:** o `git status` local nunca está limpo. Isso corrói o instrumento de conferência do
fim de sessão — o **diffstat antes do push** — porque o ruído permanente compete com o sinal do
que a sessão de fato mudou.

**Inventário medido (14/08/2026, `git status --porcelain`):**

| estado | arquivo | natureza |
|---|---|---|
| `M` | `dynasty.db` | **banco vivo de dev** versionado; muda a cada boot/sync/teste |
| `M` | `handoff_code_manager_23_04_2026.md` | handoff antigo, editado |
| `??` | `handoff_code_manager_11_06_2026.md` · `_10_07_2026.md` · `_24_04_2026.md` · `_28_04_2026_pt2.md` | handoffs de sessões passadas, nunca commitados |
| `??` | `improvements_backup_pre_O5_2026-08-13.md` · `improvements_archive_backup_pre_O5_2026-08-13.md` | backups pré-[[O5]] (**serviram de controle** do auditor: exit 1 com 83 violações) |
| `??` | `.phantom_board_profile/` | perfil do Playwright do [[OFF26-24]] (dado de browser, não fonte) |
| `??` | `AGENTS.md` | arquivo de instruções não versionado |

**Decidir item a item — três destinos:** `.gitignore` · pasta de archive local · descarte.

⛔ **`dynasty.db` NÃO é caso trivial e não deve ser resolvido por reflexo:** ele é simultaneamente
(a) o artefato consumido pelo `fantasy_optimizer` e pelo `predictor`, (b) o **seed do 1º deploy**
no Render (`init_data.py` o copia para `/data/`) e (c) um banco de dev que muda sozinho. Ignorá-lo
tem consequência **fora deste repo** — é decisão do owner, não higiene.

**O que este item NÃO é:** não é limpeza do disco de produção (o `/data` do Render é outro assunto,
ver a seção de deployment do `CLAUDE.md`) nem revisão geral de `.gitignore`.

**Cross-refs:** [[O5]] (de onde vêm os dois backups), [[OFF26-24]] (o `.phantom_board_profile/`),
[[O3]] (a disciplina de arquivos do backlog, que é o precedente de organização).

---

### OFF26-25 — O rollover não tem gate mecânico de tabela ESPN definitiva
⚠️ **IMPLEMENTADO 14/08/2026 (MAN-OFF26-25) — ✅ condicionado ao ciclo real** (recusa observada
no preflight de domingo + aceite na segunda, após o import final) — Registrado no mesmo dia
(MAN-DP-PREFLIGHT-1808, auditoria read-only de prontidão) — Prioridade **Alta (18/08)**

**O achado, numa linha:** o único gate do passo 4 é uma **flag manual que não sabe qual tabela
ESPN está no banco**.

```python
# routes/offseason.py:197
{"num": 4, "name": "Season Rollover", "key": "rollover_done",
 "done": rollover_done, "locked": not (lottery_locked and espn_updated)}
# routes/offseason.py:180
espn_updated = get_config("espn_values_updated", "false") == "true"
```

`espn_values_updated` é escrita **em um único lugar** — `confirm_espn`
([offseason.py:653](routes/offseason.py#L653)), o botão *"✅ Confirmar ESPN Atualizado"* do passo
3. O import ESPN **não a escreve** (zero ocorrências em `routes/admin.py`). ⇒ a flag pode estar
`true` desde um import **provisório** de junho, e o passo 4 aparece destravado.

**Por que dói justamente em 18/08:**
1. O rollover lê `player.espn_ref_value` ([salary_engine.py:204](salary_engine.py#L204)) — o que
   estiver na coluna. Com a provisória (≈1.0) a valorização degrada para
   `MAX(prev, floor(0.5×1)) = prev` e o waiver ano 2 vira `floor(0.8×1) = $1`: **roda sem erro e
   produz a folha inteira errada**.
2. É **once-only** (`if step4["done"]` → 400). A definitiva chegando depois **não reprocessa
   nada** — `rollover_done` já é `"true"`.
3. ⇒ o dano é **irreversível pelo app**. A única saída é restaurar o backup.

**A defesa que existe hoje é disciplina, não mecanismo:** dois `window.confirm()` em
[offseason.html:735-736](templates/offseason.html#L735-L736) — o primeiro pergunta literalmente
*"A tabela ESPN esta atualizada?"* e o segundo lembra do backup. É exatamente a classe que a
diretriz do owner no [[OFF26-23]] rejeita: **ponto de não-retorno não se protege com runbook**.

⛔ **A diagnose já existia e não é achado novo:** o [[OFF26-9]] (✅ 17/06/2026, archive) mediu isso
com todas as letras — *"o rollover **pode rodar sobre ESPN preliminar**… o gate do rollover é
satisfeito por um **checkbox do admin**, agnóstico a qual import (preliminar ou definitivo)
rodou"*. O que ele fez foi **corrigir a redação** (separar timing × qualidade de dado na D8 e no
microcopy). **O poka-yoke nunca foi construído** — e o [[OFF26-23]], que instituiu o princípio,
cercou os três pontos do *import do draft*, não este.

**Fix candidato (uma linha de condição, não um mecanismo novo):** o passo 4 passa a exigir
`ESPNImportLog.query.filter_by(season=current+1, status="final").first()` — **a mesma verdade que
a `/league` já consulta** para decidir o selo PROV ([league.py:138](routes/league.py#L138)). Sem
segunda definição de "definitiva"; o `espn_values_updated` pode continuar existindo como
confirmação humana **somada** ao dado.
⚠️ Decisões que são do owner e **não** foram tomadas aqui: se o gate é recusa dura ou 409 com
`force` explícito (molde do passo 5 do OFF26-23), e o que fazer com uma season sem tabela
definitiva.

**Por que NÃO é bloqueador de 18/08** (avaliado, não assumido): o roteiro do dia já põe o import
antes do rollover; o `--check` equivalente existe (**preview** do rollover em
[admin.py:177](routes/admin.py#L177), read-only, mostra `new_salary` de todos); e o **backup
manual** torna o pior caso reversível. O item é o que sobra **se as três falharem juntas**.

**Cross-refs:** [[OFF26-9]] (a diagnose, archive), [[OFF26-23]] (o princípio + os 3 poka-yokes do
import), [[MAN-METH-REG]] (candidato a baseline: *ponto de não-retorno recusa a inversão*).

---

#### FIX (MAN-OFF26-25, 14/08/2026) — a trava construída, e o furo que o parecer pegou antes

**Decisões do owner sobre o parecer pré-execução**, todas incorporadas: predicado sobre o import
**mais recente**, **helper único** nos 4 sítios (com o [[UX19]] de carona), **recusa dura** sem
`force`, flag manual **mantida** como dupla condição, runbook liberado.

⭐ **O ajuste que mudou a correção, não o estilo — predicado "mais recente" × "existe algum
final":** o enunciado original (*"existe no espn_import_log um import FINAL cuja season é a
alvo"*) tem um furo. `set_espn_value` sobrescreve `player.espn_ref_value` em **toda** importação
([models.py](models.py#L690)); reimportar uma **provisória** depois da definitiva — cenário real,
é o que se faz para corrigir um match na tela de review — devolve o banco ao estado provisório
**enquanto a linha `final` antiga continua no log**. Com o predicado do enunciado, o gate daria
**falso OK**: uma trava que mente é pior que trava nenhuma. Custo do ajuste: um `order_by`.
Coberto por `test_provisoria_DEPOIS_de_final_NAO_qualifica`.

⚠️ **Limite residual, declarado no docstring do helper e NÃO resolvido:** o predicado prova um
**EVENTO** (o import desta season), não o **ESTADO** da coluna que o rollover lê — um import
posterior para *outra* season sobrescreveria `espn_ref_value` sem tocar o predicado. Prova de
estado exigiria varrer `EspnValueStore`/`ESPNValue` da season alvo; decisão do owner foi ficar no
evento. O caso comum (reimport da mesma season) está coberto.

**O que nasceu:**
- **`models.espn_final_import(season)`** (+ `latest_espn_import`, a leitura que o preview usa
  para exibir o candidato mesmo quando ele **não** qualifica). ⛔ Fonte única: a consulta era
  **réplica inline em 2 sítios** da `/league` e teria virado 3ª e 4ª cópias; hoje **5
  consumidores** leem o helper (gate, `do_rollover`, preview, `/league`, `/team/<id>`) — mais o
  `/cap_projector`, cuja consulta inline era byte a byte a mesma leitura.
- **Dupla condição no passo 4** (`_get_step_statuses`): `lottery_locked and espn_updated and
  espn_final`. A flag manual segue sendo o passo 3 do painel, intacta.
- **`espn_gate_message(target_season, log)`** — núcleo **puro** (molde do `rollover_order_gate`),
  traduzindo a recusa em mensagem acionável: o que falta, o status e a data do que **viu**, e o
  caminho (*reimportar com o checkbox marcado*). ⚠️ **`UTC` explícito na data** — achado do
  próprio smoke: o servidor compõe a string e o preview formata o mesmo carimbo no fuso do
  device (M18), e perto da meia-noite as duas telas mostravam **dias diferentes** (28/07 UTC ×
  27/07 21:30 local).
- **Recusa DURA server-side**: 409 `blocked_by="espn_nao_definitiva"`, sem `force` — não há
  cenário legítimo de rodar sobre provisória (se a definitiva atrasa, adia-se o dia). O
  **once-only vem primeiro** na ordem das checagens: rollover já executado recusa por *"já
  executado"*, nunca pela condição nova (pós-rollover a season alvo vira a seguinte, que nunca
  tem definitiva — sem essa ordem a mensagem passaria a mentir).
- **Preview do `/admin`** exibe a tabela candidata (season · DEFINITIVA/PROVISÓRIA · data) e o
  veredito do gate — o último ponto de detecção antes do irreversível.

**Testes — `espn_gate_test.py` (33):** núcleo puro (6), predicado (6, incl. o furo acima e a
fronteira *final de OUTRA season não qualifica*), matriz de 4 células do destravamento (5),
endpoint (6, incl. *recusa não muta nada* e *não existe escape por force*), preview (4), guardas
estáticas (6: season literal por **AST** — não por texto, que dava falso positivo nas docstrings
—, anti-réplica da consulta, fiação do gate no POST, flag preservada, varredura do rollover
intocada). ⚠️ **`late_drop_test` teve a fixture ajustada** (+1 `ESPNImportLog` final): 3 testes
da urna passariam a recusar pelo gate novo e provariam o item errado.

⭐ **Smoke em NAVEGADOR REAL, bidirecional** (condição de push do owner; precedente 10/08, em que
DOM headless não pegou o JS quebrado). App servindo em localhost sobre **cópia** do banco, sessão
injetada por cookie assinado (sem OAuth, sem tocar código):
- **17/17 recusando** — as 3 funções de onclick definidas, zero erro de console, ⭐ **passo 4
  bloqueado COM a flag `true`** (a célula exata do item — o smoke clica o passo 3 **antes** de
  julgar, senão o "Bloqueado" poderia vir da flag velha), POST direto 409 com o payload certo,
  passos 3 e 5 respondendo, preview em PROVISÓRIA.
- **6/6 aceitando** — com a definitiva no log: passo 4 *Pendente*, botão de executar presente,
  preview **verde** com DEFINITIVA e sem menção a bloqueio. ⛔ O botão **não** foi clicado (a
  mutação é coberta pelo teste de endpoint).

**588 testes verdes.** Gate do [[O7]] exercido (o diff toca `admin.html`): **exit 0**.
**Runbook atualizado** (`runbook_urna_late_drop.md`, seção 17→18/08): o checkbox vira passo
explícito e a nota de que **não há tela para promover um import a final** — se esquecer, é
reimportar.

⚠️ **Consequência operacional consciente:** esquecer o checkbox deixou de produzir *folha errada
em silêncio* e passou a produzir *bloqueio duro com instrução*. É a troca desejada — e é por isso
que a mensagem carrega o caminho da solução.

**PROC1 — limitação declarada:** o diff é **Python + template autenticado + docs**; **nenhum
arquivo público mudou**, então a prova por artefato servido **não está disponível** (mesmo caso
da MAN-UX-BID0-F2 que motivou a repriorização do [[PROC2]]). A confirmação do deploy fica em
evidência circunstancial de restart até o [[PROC2]] existir.

---

### UX19 — Selo PROV falso nas grandezas correntes da `/league` pós-rollover
⚠️ **CORRIGIDO DE CARONA 14/08/2026 (MAN-OFF26-25) — ✅ condicionado à observação em 18/08** —
registrado no mesmo dia (MAN-DP-PREFLIGHT-1808) — Prioridade **Baixa** — cosmético, mas
aparece **no dia 18/08** e diz o contrário do que acabou de acontecer

**Mecânica:** o selo é decidido por season-alvo, não por estado do número.

```python
# routes/league.py:138 — idêntico no /team/<id> (:183)
espn_final = ESPNImportLog.query.filter_by(season=season + 1, status="final").first() is not None
... bid_provisional = not espn_final
```

Pré-rollover isso é exato: `season+1` = 2026 é a tabela que ainda vai entrar. **Depois do
rollover** `season` já é 2026, a consulta pergunta por uma tabela de **2027** — que não existe e
nem deveria — e `bid_provisional` volta a `True`.

**Onde isso vira pixel errado:** só na `/league`. O ramo pós-rollover da macro recebe o mesmo
`prov` ([league.html:81-83](templates/league.html#L81-L83)), então **"Bid máximo"** e **"Cap"** —
agora as grandezas **correntes**, derivadas da tabela definitiva importada horas antes — nascem
com a tag *"a tabela ESPN definitiva ainda não entrou"*.

**As duas superfícies vizinhas NÃO têm o defeito** (medido, não suposto):
- `/team/<id>`: os dois selos vivem **dentro** do `{% if show_projection %}`
  ([team_detail.html:52-65](templates/team_detail.html#L52-L65)) ⇒ somem junto com a projeção.
- `/cap_projector`: lê `espn_is_final` **por jogador** do store canônico
  ([salary.py:119](routes/salary.py#L119)); pós-rollover o store da season-alvo está vazio ⇒
  `None`, e o template só marca em `=== false` ⇒ **sem selo**.

⇒ o mesmo estado produz **três comportamentos diferentes** em três telas — e a que erra é a do
planejamento da auction.

**Fix candidato:** a `/league` já sabe se está pré ou pós-rollover (`show_projection`); passar
`prov=False` no ramo corrente resolve sem tocar o gate. Alternativa mais funda (e que também
serviria ao [[L4]]): o selo passar a perguntar *"o número que estou exibindo veio de tabela
definitiva?"* em vez de *"existe tabela definitiva para season+1?"*.

**Cross-refs:** [[L3]] (o card e o gate), [[L4]] (o outro efeito colateral do gate que só fecha),
[[OFF26-25]] (a mesma consulta `status='final'`, usada lá como gate que falta).

---

**FIX (14/08/2026, dentro da MAN-OFF26-25) — fechou de carona, por decisão do owner:**

O helper único do [[OFF26-25]] (`models.espn_final_import`) passou pelos **4 sítios**, e este
item estava exatamente num deles. A correção é a **primeira** das duas alternativas registradas
acima, aplicada na **rota** em vez do template:

```python
bid_provisional = show_projection and not espn_final     # routes/league.py, nos DOIS sítios
```

**Por que na rota e nas duas telas** (e não só o `prov=False` no ramo do `league.html`): o selo
qualifica o número **projetado** — quando a projeção fecha, não sobrou nada de provisório para
marcar. Pôr a regra na rota faz as duas telas responderem **a mesma coisa à mesma pergunta**; o
`/team/<id>` já se protegia por acidente de template (o `{% if show_projection %}` em volta), e
agora se protege por semântica.

⛔ **Não foi tocado** o predicado do selo (*"existe tabela definitiva para season+1?"*) — a
alternativa mais funda registrada acima, que perguntaria pela procedência do número exibido,
segue em aberto e é parente do [[L4]].

**Verificação:** `cap_projetado_test` (27) verde — inclusive as guardas de fase que já cobriam o
par pré/pós-rollover — e gate visual do [[O7]] exit 0. **Falta a observação em 18/08**, no dia em
que a projeção efetivamente fecha: mesma janela do [[OFF26-25]].

---

### UX21 — Página do lottery sem porta de entrada a partir do board de picks
🔲 **Registrado 17/08/2026 (MAN-LOTTERYLINK-REG)** — Prioridade **Baixa** — **registro apenas;
nenhuma direção arbitrada, nenhuma mudança de código**

**Problema:** `/picks/lottery/<season>` é uma tela **rica** — a ordem linear do Round 1, o pool de
bolinhas, o hash de auditoria e o histórico de re-runs (a camada do [[M8]], construída para que o
sorteio seja **verificável por qualquer owner**) — e **não tem link de entrada**. Os únicos acessos
são pelo `/offseason` (admin) e por quem já souber a URL. ⇒ a tela existe para dar **transparência
pública** e depende de conhecimento privado para ser alcançada.

⚠️ **A assimetria é medida, não suposta:** a tela de auditoria tem *"← Voltar ao Picks"*. **O
caminho de volta existe; o de ida, não.**

**Origem:** achado da **F1 do [[UX20]]** (relatório no `improvements_archive.md`), que o classificou
como *"órfão já existente"* — anterior ao redesenho, não criado por ele. Ficou **deliberadamente
fora do escopo**: a candidata **(c)** da F1 previa fechá-lo, e o owner escolheu a direção **(e)**,
que não o inclui. O fechamento **MAN-UX20-DONE** registrou a pendência explicitamente para que ela
não sumisse junto com o item concluído — este registro é o desdobramento disso.

**Escopo candidato — ⛔ NÃO arbitrado (a forma é decisão de implementação):**

- Candidato natural: o **cabeçalho do Round 1** do board. ⭐ A infra **já existe e já nomeia o
  destino** — o F2 do [[UX20]] criou o cabeçalho por round e o rotulou *"Round 1 · Sorteio
  (lottery)"*. Transformar esse rótulo (ou um ícone ao lado) em link para a auditoria **da season
  exibida** é o menor movimento possível.
- Outras formas não descartadas: atalho no rodapé do card de odds (que já fala do sorteio), ou
  entrada pelo menu. **A escolha não é feita aqui.**

⏳ **Timing — consideração do owner (17/08/2026), registrada:** implementar **quando o link tiver
destino vivo**. O lottery de **2026 perde relevância no rollover**, e o de **2027 só nasce com o
próximo sorteio** — um link agora apontaria para uma tela que a temporada acabou de tornar
histórica. **Sem prazo.** ⇒ o gatilho natural é o board voltar a exibir uma season **com lottery
travado** (a mesma janela em que o [[UX20]] tinha sintoma observável).

**Relações:**

- **[[UX20]]** ✅ — origem do achado (F1) e do registro (fechamento); ambos no
  `improvements_archive.md`. ⭐ O **cabeçalho por round** que o F2 criou é a **infra natural** deste
  link: o item nasceu mais barato do que era quando foi achado.
- **[[M8]]** — a página do lottery e a auditoria que ela expõe; **[[M15]]/[[M15-FIX]]** (os pesos e a
  legenda de odds que a mesma tela consome), **[[M16]]** (o lottery define só o R1 — que é
  exatamente o recorte da tela órfã).
- ⛔ **Não confundir com [[UX5]]** (densidade da seção Picks do `/team/<id>`) nem com o problema de
  **ordem** que o UX20 resolveu: aqui não há defeito de leitura nem de dado — é **alcançabilidade**.

---

### MAN-AUTH1 — Login OAuth não oferece seletor de contas Google (usuário com sessão Google não-cadastrada cai em 403 sem saída)
⚠️ **F2 implementada 17/08/2026 (MAN-AUTH1-F2, direção A+C do owner) — validada em localhost;
smoke de produção PENDENTE** (gate [[PROC1]]; o smoke real é o próprio Murilo, no PC do trabalho,
vendo o seletor). Registrado 17/08/2026 (MAN-AUTH1-REG) · F1 17/08 (MAN-AUTH1-F1, read-only) —
Prioridade **Média** — categoria **UX/auth**

> **Leitura desta seção:** o texto abaixo é o **registro original**, preservado como estava (a
> descrição do sintoma, que continua correta). O que a **F1 mediu** e o que a **F2 construiu** vêm
> **depois dele**, nas duas seções ao final — inclusive as premissas que a medição **refutou**.

**Sintoma (relato do owner da liga — Murilo, por WhatsApp, 17/08/2026):** no PC do trabalho, o
clique em login **não exibe o seletor de contas do Google**. O Google autentica **automaticamente**
com a conta ativa naquele navegador — o email **corporativo**, que não está cadastrado na liga — e
o app responde **403**. O usuário **nunca chega a escolher** a conta certa.

**O beco sem saída:** o `/logout` do app **não altera o comportamento** — ele encerra a **sessão
Flask**, não a **sessão Google do navegador**. Reentrar no login reautentica **a mesma conta
errada**, e o ciclo se repete. Não há, na tela do 403, caminho oferecido para trocar de conta.

**Workaround em uso hoje:** **aba anônima** (navegador sem sessão Google ativa ⇒ o Google volta a
pedir a conta). Funciona, é do usuário e não do app — não é solução.

**Natureza:** **bug de UX de autenticação**, não de permissão nem de cadastro. A conta correta
**existe** na tabela `users` e o `@login_required`/403 está fazendo exatamente o que deve fazer
com uma identidade desconhecida — o defeito é que o fluxo **não dá ao usuário a chance de se
identificar com a conta certa**, e depois **não oferece saída**. Fluxo afetado: autorização Google
OAuth (OpenID Connect via `authlib`), a camada do [[X1b]].

**⛔ Nada aqui foi conferido contra o código — é o trabalho da F1, que é obrigatória antes de
qualquer F2.** Perguntas que a F1 deve responder **medindo**, no espírito do [[MAN-METH-REG]]:

1. **Como o pedido de autorização é montado hoje** e o que ele diz (ou não diz) ao Google sobre
   escolha de conta — o comportamento observado é consistente com "o Google reusa a sessão única",
   mas a causa precisa ser lida no código, não suposta.
2. **O que a tela do 403 oferece** ao usuário não-cadastrado: existe alguma ação a partir dali, ou
   é folha morta? (O relato indica que é folha morta.)
3. **Qual é o alcance real do `/logout`** e se há algo que o app possa legitimamente fazer para
   encerrar/renegociar a sessão do provedor — separando o que é do app do que é do navegador.
4. **Réplica:** o login tem **um** ponto de entrada ou mais de um caminho chega ao provedor?
5. **Fronteira:** o remédio pertence ao pedido de autorização, à página de erro, ou aos dois? São
   consertos de custos e riscos diferentes, e a escolha é **do owner**.

**Relações:**

- **[[X1b]]** ✅ — a camada onde o fluxo vive (Google OAuth + Flask-Login).
- **[[X1c]]** / **[[M12]]** — cadastro email↔time: é o que torna a conta corporativa "desconhecida",
  e ⛔ **não é o defeito** (cadastrar o email do trabalho seria contornar, não corrigir).
- **[[F4]]** ✅ — precedente de mexida no fluxo OAuth (callback local); registro de evidência no
  `improvements_archive.md`.

#### F1 — 17/08/2026 (MAN-AUTH1-F1, read-only): o que a medição respondeu

**1. Construção do redirect** — sítio único, [auth.py:58-61](routes/auth.py#L58-L61). O registro do
cliente não passa `authorize_params`, e a chamada não passa kwargs; em authlib 1.6.9
`create_authorization_url` mescla **só esses dois**. Reproduzindo a chamada da linha 61 sem rede, a
URL sai com `client_id · nonce · redirect_uri · response_type=code · scope · state` — **`prompt`
ausente, `login_hint` ausente**. ⇒ hipótese do prompt **confirmada por medição**.

**2. Pontos de entrada** — o redirect é construído em **um** lugar, **zero réplicas**: o único link
do app é [login.html:8](templates/login.html#L8); a URL direta `/login/google` existe sem link; e
todo anônimo é funilado a `/login` pelo `unauthorized_handler` ([auth.py:36](routes/auth.py#L36)).
Nenhum JS inline monta a URL.

**3. O que o 403 exibia** — medido renderizando o template no contexto real: **nenhum email na
página**, **sem link de logout ou de login** (a navbar esconde o menu de usuário para anônimo —
[base.html:94](templates/base.html#L94), [base.html:115](templates/base.html#L115)), e **um** botão:
*"← Voltar ao Início"*. ⭐ **Ciclo de 3 saltos, medido:** 403 → `/` → 302 `/login` → botão →
reautenticação silenciosa → 403. ⚠️ **Achado além da hipótese:** a única frase acionável —
*"fale com o administrador"* — **aponta o remédio errado**, porque a conta do usuário **está**
cadastrada; ele autenticou com outra.

**4. O `/logout`** — `logout_user()` limpa a sessão Flask e marca o `remember_token`; **nada além**.
⭐ Para o rejeitado é **inerte por três motivos independentes**: (a) ele **nunca foi logado** — o
403 retorna antes do `login_user` ([auth.py:76-87](routes/auth.py#L76-L87)); (b) mesmo logado, não
tocaria a sessão Google; (c) **o link nem aparece** para anônimo.

**5. Premissas** — ⛔ **"os 11 owners entram hoje com 1 clique" está DESLOCADA:** `remember=True`
([auth.py:87](routes/auth.py#L87)) + `REMEMBER_COOKIE_DURATION` **default de 365 dias** (nenhum
override em `app.py`) ⇒ o caminho diário do owner recorrente é **zero clique no fluxo OAuth** — ele
entra pelo cookie e **não passa** por `/login/google`. Forçar o seletor só custa no caminho **frio**
(dispositivo novo, cookies limpos, pós-logout, pós-365 dias). ⛔ **Armadilha registrada:** não
encaminhar ao logout do Google — desconectaria **todos** os serviços Google daquela máquina; num PC
de trabalho é dano colateral fora da alçada do app. **A sessão do navegador não é nossa para
encerrar; o que está ao alcance é pedir a escolha.**

#### F2 — 17/08/2026 (MAN-AUTH1-F2): direção A+C do owner, construída

**(A) O pedido de autorização passa a forçar a escolha** — [auth.py:58-66](routes/auth.py#L58-L66),
o sítio único: `authorize_redirect(redirect_uri, prompt="select_account")`.

**(C) O 403 passou a ter nome e saída** — template **próprio** `templates/login_denied.html`
(⛔ o `error.html` genérico **não foi tocado**: segue servindo 404/500 e o `admin_required`). A tela
**nomeia o email rejeitado**, explica em 2 frases que a causa provável é a conta já logada no
navegador, oferece **"Entrar com outra conta"** — que reentra no fluxo e, pela metade A, **abre o
seletor** — e rebaixa o *"fale com o administrador"* ao **caso residual correto** (o email é mesmo o
seu e ainda não foi cadastrado), em nota discreta ao pé.

⛔ **Fora do escopo, por restrição do owner:** contratos de permissão, `unauthorized_handler`,
cookie/duração de sessão, seed de users, qualquer coisa que toque a sessão Google do navegador, e o
[[MAN-AUTH2]] (`next`/deep link — item separado).

**Verificação (localhost, cópia do banco, sem rede — só o que fala com o Google é substituído):**

- **(A)** `GET /login/google` → `302` com **`prompt=select_account`** na query, pela **rota real**.
- **(C)** callback com email não cadastrado → **403** exibindo o email, a explicação e o botão para
  `/login/google`; **nenhuma sessão criada** para o rejeitado; **nenhum** link para logout do Google
  nem para o `/logout` do app (que seria inerte).
- **Caminho feliz intacto:** callback com email cadastrado → `302` para `/`, sessão criada,
  **`remember_token` emitido como antes**; `GET /` autenticado → 200. `404` segue no `error.html`.
- `salary_engine_test` **62/62** ⚠️ (o prompt dizia 48 — a suíte está em 62 desde o [[UX18]]);
  `template_js_test` 3/3; **gate do [[O7]] exit 0** (22s, 4 páginas × 4 larguras).
- ⭐ **A tela nova o gate NÃO alcança** (não há rota que a renderize sem OAuth), então ela foi
  medida **ad-hoc com o mesmo instrumento** (`core.JS_OVERFLOW`, 4 larguras canônicas) — e a medição
  **pegou um defeito**: email corporativo longo **transbordava o documento a 390px** (culpado
  `strong`). Fechado no nascimento (`overflow-wrap:anywhere`); 8/8 medições limpas depois, e as duas
  capturas (390px e 1024px) conferidas a olho.

---

### MAN-AUTH2 — `next` morto no callback OAuth (cheiro de open redirect se populado) + deep link descartado no `unauthorized_handler`
🔲 **Registrado 17/08/2026 (MAN-AUTH2-REG)** — Prioridade **Baixa** — categoria **auth/robustez** —
**registro apenas; nenhuma direção arbitrada, nenhuma mudança de código**

**Origem:** achado de **carona da diagnose [[MAN-AUTH1]]-F1** (sessão read-only, 17/08), na seção
*"achados fora do escopo"*. Não foi registrado na hora porque aquele prompt restringia o escopo ao
item AUTH1 — este registro é o desdobramento, para o achado não se perder no relatório.

**Comportamento 1 — o destino original é descartado.** [auth.py:36](routes/auth.py#L36): o
`unauthorized_handler` manda o anônimo para `/login` **sem carregar o destino**:

```python
return redirect(url_for("auth.login_page"))     # ← sem next=
```

⇒ quem abre um **link profundo** (a página de um jogador, o detalhe de um time, uma proposta de
trade compartilhada) e ainda não tem sessão **perde o destino**: loga e chega na home. ⭐ **Medido
na F1, não deduzido:** `GET /team/1` como anônimo devolve `302` com `Location: /login` — **sem
`next`**.

**Comportamento 2 — o `next` do callback é código morto.** [auth.py:88](routes/auth.py#L88):

```python
next_page = request.args.get("next", url_for("roster.index"))
return redirect(next_page)
```

O parâmetro **nunca chega populado pelo fluxo real**: quem chama `/auth/callback` é o **redirect do
Google**, e ele carrega `code`/`state` — não um `next` nosso. ⇒ o `.get()` cai **sempre** no default
`roster.index`, e o ramo que lê a query string é **inalcançável**. ⚠️ **A parte que não é só
higiene:** se algum dia esse parâmetro passasse a chegar (alguém "consertando" o comportamento 1 da
forma óbvia), ele seria consumido **sem validação** — `redirect()` aceita destino **absoluto e
externo** ⇒ **cheiro de open redirect**. Hoje é inofensivo **porque está morto**; o risco nasce no
momento em que alguém o ressuscita sem guarda.

⭐ **Os dois comportamentos são a mesma cadeia partida ao meio:** o lado que **deveria produzir** o
destino não produz, e o lado que **consumiria** o destino existe, sem validação, sem consumidor.

**Natureza dupla — as metades são independentes e podem ser decididas separadamente:**

1. **Higiene (não muda comportamento observável):** ou o `next` do callback sai, ou ganha
   **validação defensiva** de destino relativo. Fecha o cheiro de open redirect **antes** de existir
   um consumidor — que é a única hora barata de fechar.
2. **Decisão de produto (opcional, é do owner):** restaurar o **deep link ponta a ponta** (o handler
   carrega o destino, o fluxo o preserva pelo `state`, o callback o consome **validado**) **×**
   assumir a **home como destino fixo** e apagar o resto. ⛔ **Não arbitrada aqui.** Nota de
   dimensionamento: o deep link só é sentido no caminho **frio** — a F1 mediu que o owner recorrente
   entra pelo `remember_token` (365 dias) e nem passa por essa cadeia.

**Relações:**

- **[[MAN-AUTH1]]** 🔲 — mesma diagnose de origem e **mesmo arquivo**, ⛔ **problema diferente**:
  lá é *quem* entra (conta errada, sem seletor, 403 sem saída); aqui é *para onde* vai quem entrou.
  Se as duas forem executadas juntas, o fluxo é tocado uma vez só — mas **nenhuma depende da outra**.
- **[[X1b]]** ✅ / **[[F4]]** ✅ — a camada e o precedente de mexida no callback (archive).
- **[[T1]]** — as **propostas de trade compartilháveis** (URL por UUID) são o caso de uso em que o
  descarte do destino mais aparece: link mandado ao outro owner, que loga e chega na home.

---

### OFF26-27 — Criação de stub no sync usava season estagnada (a raiz do carimbo 2025)
⚠️ **Fix no ar (`bdd3044`, 18/08/2026) — smoke de produção PENDENTE** — Prioridade **Crítica**,
prazo **antes do sync pós-cortes de 20/08** (o fix precisa estar deployado antes do próximo stub
nascer) — prompt MAN-OFF26-25 (⚠️ o ID de backlog é **27**: OFF26-25 já era o gate ESPN do rollover)

**Raiz (provada na F1 do [[OFF26-26]]):** [sync_sleeper.py:304](sync_sleeper.py#L304) criava o
Player stub com `contract_start_season=CURRENT_SEASON` — constante de módulo fixa em 2025, cujo
próprio comentário diz *"fallback — prefer get_current_season()"* — enquanto o rollover avança o
**AppConfig**. Todo entrante pós-rollover nascia na season errada; a classe 2026 inteira nasceu
assim (curada pelo one-shot do [[OFF26-26]]); o defeito seguia **ativo** para qualquer add/waiver
com os syncs frequentes da semana (cortes de 20/08, trades).

**Fix mínimo (`bdd3044`):** `stub_season = get_current_season()` lido **uma vez por sync**
(hoisted antes do loop de rosters) e usado no construtor; a constante segue como fallback de
última instância **dentro** do helper. Zero uso cru remanescente no módulo (só o import);
players existentes intocados (a linha 242 do sync — nunca tocar salary/contract de existente —
não foi alterada).

**Verificação:** `sync_stub_season_test.py` (6 testes) — guarda **AST** no construtor `Player(`
(reintroduzir a constante na criação de dados FALHA), `run_sync` contém a leitura canônica,
AppConfig 2026 → 2026, ausente → fallback sem quebrar, pós-rollover o carimbo acompanha.
⭐ **Smoke com `run_sync` REAL** contra cópia adaptada (2026) reproduziu o incidente como
validação: os 36 rookies ausentes do seed foram recriados como stubs **todos em
`contract_start_season=2026`**, e **zero** player existente teve salary/contract/acq/css alterado.
Suítes verdes: engine 62, poka_yoke 15, late_drop 64, espn_gate 33.

**Fora do escopo (mapeado na F1, sem mudança):** `import_csv` (dormente em prod — CSV fora do
git), `AuctionLog.season` default (latente — `record_acquisition` sempre passa explícito),
`/auction` (item próprio: [[OFF26-28]]). Nenhuma migração de dados: não há outros registros 2025
pós-rollover fora dos 36 já curados.

**Fecha ✅ quando:** hash `bdd3044`+ conferido em prod ([[PROC1]]) e o próximo jogador novo criado
por sync nascer `contract_start_season=2026` (a movimentação de 20/08 produz o caso natural).

---

### OFF26-28 — `/auction` carimba season 2025 hardcoded no cliente (4 campos + `now_year` órfão)
🔲 **Registrado 18/08/2026 (MAN-OFF26-24-REG)** — Prioridade **Alta**, prazo **antes de 24/08**
(a FA auction será REGISTRADA pelas portas do `/auction`) — achado irmão da F1 do [[OFF26-26]]
(⚠️ o "OFF26-26" do prompt de registro colidia com este incidente; ID de backlog = **28**)

**Sintoma:** o backend das 4 portas do `/auction` tem o default correto
(`get_current_season()` — [auction.py:37](routes/auction.py#L37) etc.), mas **o cliente sempre
envia a season explícita**, e ela nasce 2025 em quatro sítios do template:
[auction.html:88](templates/auction.html#L88) (`value="2025"` no rookie), [:170](templates/auction.html#L170)
e [:190](templates/auction.html#L190) (fallbacks `|| 2025` no JS), [:215](templates/auction.html#L215)
(excel: `season: 2025` fixo) — e o campo FA ([:49](templates/auction.html#L49)) usa
`{{ now_year if now_year else 2025 }}` com **`now_year` nunca passado pela rota**
([auction.py:15-20](routes/auction.py#L15-L20)) ⇒ renderiza 2025 também. Como o valor do cliente
sempre chega, **o default correto do servidor nunca é usado**.

**Consequência se não corrigido até 24/08:** todo registro do leilão carimba
`contract_start_season`, `SalaryHistory.season` e `AuctionLog.season` como **2025** — a mesma
classe de dano do [[OFF26-27]], por outra porta, e em massa (todos os arremates).

**Fix candidato (⛔ não arbitrado):** a rota passar `now_year=get_current_season()` + os 4 sítios
do template lerem a variável (e o fallback JS cair para o valor do campo, não para literal).
Enquanto não sai o fix, mitigação operacional: **conferir o campo "Temporada" = 2026 antes de
cada registro** — mas é disciplina, a classe que os poka-yokes da semana rejeitam.

**Relações:** [[OFF26-27]] (mesma família — fonte de season estagnada; lá constante de módulo, cá
literal de template), [[OFF26-3]]/[[OFF26-11]] (o caminho alternativo de registro — importador da
fantasma — que NÃO tem este defeito e é o plano A de 22-24/08; o `/auction` é o fallback manual).

---

### OFF26-29 — Picks 2026 consumidas seguem vivas como ativo no Manager
🔲 **Registrado 18/08/2026 (MAN-OFF26-24-REG); F1 read-only FEITA na mesma janela
(MAN-OFF26-27-F1 — ⚠️ ID de backlog = 29)** — Prioridade **Baixa (REG) — a F1 sugere reavaliar
para Média** (a exposição é na janela de trades até 24/08) — F2 aguarda decisão do owner

**Contexto:** o rookie draft 2026 foi materializado pelo [[OFF26-26]], mas as picks 2026 seguem
vivas como ativo: no Sleeper (draft `pre_draft` — governança por aviso) e no Manager (tabela
`Pick`).

**O que a F1 mediu (evidência na trilha da conversa de 18/08):**

- **7 consumidores** da Pick 2026; o funcional é **`/api/picks` sem filtro de consumida**
  ([picks.py:127-148](routes/picks.py#L127-L148)), que alimenta a lista de picks **selecionáveis**
  do simulador ([trades.html:329](templates/trades.html#L329)), o preview e as propostas
  (`_fetch_picks` resolve ao vivo, [trades.py:453](routes/trades.py#L453)). Board `/picks`,
  `/team/<id>` e a valoração dynasty ([dynasty_values.py:183](dynasty_values.py#L183) corta só
  `< current`) exibem/valoram normalmente.
- ⛔ **Premissa "permite registrar trade" DESLOCADA:** o Manager **não executa** trade (POSTs de
  `/trades` = preview puro, proposta, delete de registro); ativo só se move via sync ([[S1]]).
  Exposição real = **planejamento enganoso**, não execução.
- ⛔ **Delete REFUTADO como mecanismo:** o critério do sync é **ano-calendário**
  (`datetime.now().year` — [sync_sleeper.py:398-401](sync_sleeper.py#L398-L401); as 2026 morreriam
  só em 01/01/2027, rollover é irrelevante) e a recriação viria do próprio sync:
  `active_seasons` sai do `/traded_picks` do Sleeper, que ainda lista **21 picks 2026** (medido ao
  vivo, 18/08) — com o draft real `pre_draft` para sempre, o Sleeper nunca as solta.
- **Trade real do Sleeper com pick 2026 pós-expiração:** com a row viva, `_sync_trades` espelha e
  move ([sync_sleeper.py:746-757](sync_sleeper.py#L746-L757)) — correto para um espelho; com
  delete, warning `"não encontrada (drafada?)"` e Trade sem a pick rastreada.

**Recomendação da F1 (F2 ~1 sessão, zero schema, zero delete, sync intocado):** predicado
data-driven **`pick consumida = existe AuctionLog(entry_type='rookie_draft', season da pick)`** —
a mesma evidência que o gate do passo 5 ([[OFF26-23]]) já usa, materializada pelo reparo (36
registros) — em **helper único** + filtro no `/api/picks` (fecha simulador, propostas novas e
preset de uma vez) + selo/ocultação no board e `/team/<id>` (**selo × sumiço = decisão do
owner**). Autossustentável entre seasons (2027 fica tradável até o draft 2027 ter registro), sem
risco de ciclo de vida de flag (`rookie_draft_done` foi descartada como predicado — família
[[L4]]). Riscos nomeados: proposta antiga (TTL 7d) com pick 2026 ainda renderiza; valoração
dynasty da pick morta segue no delta até o filtro alcançar `_pick_asset_dict`; trade real no
Sleeper continua espelhando (correto — constar no aviso de governança).

**Pendências do registro original:** expirar/ocultar as picks 2026 no Manager (a F2 acima) +
**ensaio opcional do draft room na liga fantasma** (operacional, sem código).

---

### UX22 — Board de picks: visão de inventário quando a ordem da season não existe
⚠️ **F2 implementada 18/08/2026 (MAN-UX21-REG-F2, registro + execução na mesma janela) —
smoke de produção PENDENTE** (gate [[PROC1]]) — Prioridade **Alta** (semana de trades em curso)

> ⚠️ **Nota de ID:** o prompt pedia **UX21**, ocupado desde 17/08 (*página do lottery sem porta
> de entrada*). Nasceu **UX22**, próximo livre — precedente UX15→UX20, baseline de dedupe do [[O3]].

**Problema (feedback do owner, 18/08, com print):** após a ocultação das picks consumidas
([[OFF26-29]]), as seções 2027/2028 do board mostravam apenas *"ordem ainda não definida"* —
nenhuma pick listada. A informação de **POSSE** existe integralmente na tabela `Pick` (dono
original, dono atual, rodada, season); o que não existe antes do sorteio/classificação é a
**ORDEM** dentro da rodada. Na semana mais movimentada de trades, a página não respondia
*"quantas picks tenho, de quem, em que rodada"*.

**F2 — visão de inventário (leitura pura):**

- **Rota** ([routes/picks.py](routes/picks.py)): season presente na matriz cujo `round_centered`
  ficou sem rodadas ganha `inventory[season]` — picks por rodada ordenadas pelo **nome do dono
  atual** (alfabética é visivelmente não-draft: nada aqui inventa ordem) + contagem por time.
  Consumidas já saíram rio acima (predicado [[OFF26-29]] intocado).
- **Template** ([templates/picks.html](templates/picks.html)): a célula do inventário reusa a
  anatomia do board [[UX20]] (`draft-order-row`, 38px, `via <original>` na trocada, verde de
  "minha", ⇄ com pré-seleção) **sem o número de posição**; cabeçalho da coluna diz
  *"Round N · X picks · ordem pendente"*; chips de contagem por time no topo da seção; o aviso
  antigo **encolheu** para uma linha dentro da visão (*"a ordem virá do sorteio × classificação
  invertida e nada aqui a inventa"*). ⭐ Como as células carregam `data-team-name`, **o filtro por
  equipe e o clique-realça existentes funcionam no inventário sem uma linha de JS nova**.
- **Season com ordem → comportamento atual intacto:** quando o lottery/classificação nascer,
  `round_centered` ganha as rodadas e a visão de inventário **sai de cena sozinha** — nenhuma
  flag, nenhum estado novo.
- ⛔ Intocados: lógica de ordem (lottery/classificação), card Lottery Odds, predicado de
  consumida, schema, sync.

**Verificação:** `picks_inventory_test.py` (5 testes — posse+proveniência sem posição, gancho do
filtro nas células, contagem batendo com a tabela, consumida fora de qualquer visão, **render
ordenado intacto** via fixture de standings 2026→draft 2027); smoke com o app real sobre a cópia
do ensaio: **72 células = 72 picks** da tabela (2027+2028), chips somando 72, 2 seções de
inventário, nomes reais com emoji íntegros; **gate [[O7]] exercido e exit 0** (o diff toca
template — 4 larguras × 4 páginas limpas); suítes verdes (inventário 5, pick_consumed 13,
cap_projetado, engine 62, template_js, player_search, poka_yoke).

**Fecha ✅ quando:** smoke de prod do owner — board mostrando o inventário de 2027/2028 com as
contagens da liga real (gate [[PROC1]]: conferir o hash deployado antes).

**Relações:** [[OFF26-29]] (a ocultação que expôs o vazio — e o predicado que o inventário
herda), [[UX20]] (a anatomia de célula reusada), [[UX21]] (colisão de ID — item distinto),
[[M9]]/[[M9]]-FIX (o ⇄ preservado), [[M16]] (de onde a ordem virá quando existir).

---

### UX23 — Cap Projector mira a season de planejamento real (helper de fase + modo corrente D9)
⚠️ **F2 implementada 18/08/2026 (MAN-UX23-F2) — smoke de produção PENDENTE** ([[PROC1]]) —
Prioridade **Alta** (janela 20-24/08) — F1 18/08 (MAN-UX23-REG-F1, relatório na trilha da conversa)

**Sintoma (print do owner, 18/08):** pós-rollover o projector virou "2027" no meio da janela da
auction de 2026 — banner de ESPN respondendo a pergunta errada, Δ +$0 em toda linha, board DP1
**vazio** e cadeia DP2 **ignorando rookie em silêncio** (`rookie_espn_adjusted(sid, 2027)` → None
→ `continue`).

**O que a F1 provou:** alvo `get_current_season() + 1` **inline em 6 sítios** (rota:
data/budget/rookies; template: título ×2, rótulo, `SEASON_PROJ` do JS), **zero** helper e **zero**
gate de fase — a `/league` fecha a projeção com `_projection_open()`; o projector não tinha
equivalente. ⭐ A base correta **já existia**: modo D9 (`compose_budget(projected=False)` — *"o
salário armazenado já está valorizado; re-projetar duplicaria"*). O Δ +$0 **não era bug de
cálculo**: era `MAX(sal, floor(0.5×espn)) = sal` — a resposta certa para a pergunta errada.

**F2 (decisões do owner no REFINE: sinal = opção b/evidência AuctionLog; colunas saem; título
explicita o modo):**

- **`models.planning_target_season()`** — fonte única de fase: `current+1` pré-rollover ·
  `current` pós-rollover com auction pendente · `current+1` quando existir **evidência** de
  leilão (`AuctionLog fa_auction` da season corrente ≥ **`AUCTION_EVIDENCE_MIN = 3`**).
  ⭐ **Calibração do limiar (delegada ao Code, documentada no código):** leilão real entra em
  LOTE pelo importador (dezenas); 1-2 registros são assinatura de teste manual avulso no
  `/auction` — que não pode virar a chave no meio da janela 20-24/08. Hoje o [[OFF26-28]]
  (carimbo 2025) ainda "protege" por acidente; o limiar cobre o vão quando o 28 for corrigido.
  ⛔ `auction_done` (passo 7) **não é insumo** — flag manual fica como está.
- Os **6 sítios consomem o helper**: as 3 rotas via `_planning_ctx()`; títulos, rótulo do cap e
  `SEASON_PROJ`/`MODE` do JS **vêm do servidor**. Guardas **AST** falham se `current+1` inline
  voltar (rota E template).
- **Modo corrente**: colunas Sal-próximo/Δ **saem** (mostrar Δ zerado seria responder a pergunta
  errada), ordenação desempata pelo salário corrente, POST `/budget` envia `projected:false`
  (parâmetro D9 **que já existia** — consumido, não criado), título ganha a tag
  **"FOLHA CORRENTE · AUCTION 2026"**. Modo projetado (pós-virada): comportamento histórico
  **intacto**.
- **Banner, badge PROV, board DP1 e cadeia DP2 voltaram SOZINHOS** pela mudança do target nas
  queries — zero lógica nova, como a F1 previu.

**Verificação:** `planning_target_test.py` (12 — 3 fases; limiar 2 não vira × 3 vira; 36
`rookie_draft` **não** contam (o estado real de prod); `fa_auction` de outra season não conta;
payload `target_season`/`mode`; board de fase; guardas AST). **Smoke estado-de-prod** (cópia:
current 2026, rollover done, ESPN final, 0 fa_auction): título "Cap Projector 2026" + tag,
`espn_status=final`, **board DP1 com 251** (287 in_class − 36 draftados, auto-limpeza pelo filtro
de rosterados), DP2 **somando** o rookie do cenário, budget corrente == GET (a régua do Hub);
**fixture pós-24/08** (3 `fa_auction`): **volta a 2027/projetado sozinho**, tag some. Gate [[O7]]
exit 0; `template_js_test` + 9 suítes verdes. ⚠️ Nota do smoke: as 14 badges PROV vistas na cópia
são **artefato do boot local** (o `import_csv` do seed regrava `is_final=0` via `set_espn_value` —
em prod o CSV não existe e o boot não toca o store).

**Fecha ✅ quando:** smoke de prod do owner — título 2026 com a tag de modo, banner verde, board
populado, cenário somando (PROC1: conferir o hash deployado antes).

**Relações:** [[OFF26-29]] (a família do predicado por evidência), [[OFF26-28]] (o carimbo 2025 do
`/auction` — interage com o limiar, ver acima), [[DP1]]/[[DP2]] (as cadeias que voltaram),
[[OFF26-1]]-D9 (o modo de base reusado), [[UX19]]/[[L4]] (a família "gate que só fecha" — aqui o
sinal é por evidência justamente para não herdar esse problema), [[UX24]] (carona registrada).

---

### UX24 — Colunas "Proj `current+1`" do roster e do detalhe de time pós-rollover
🔲 **Registrado 18/08/2026 (carona da F1 do [[UX23]], conforme instrução do prompt do F2)** —
Prioridade **Baixa**

**Sintoma:** [roster.html:130](templates/roster.html#L130) e
[team_detail.html:123](templates/team_detail.html#L123) exibem a coluna
`Proj {{ g_current_season + 1 }}` — pós-rollover, **"Proj 2027"**, com a mesma semântica vazia que
o [[UX23]] diagnosticou no projector (re-projeção do salário já valorizado contra a mesma tabela
ESPN ⇒ Δ≈0 na maioria das linhas). Mesma família, superfície diferente; **menos grave** — é coluna
informativa de tabela, não ferramenta de decisão de auction.

**Candidato natural (⛔ não arbitrado):** as mesmas peças do UX23 — `planning_target_season()` já
existe como fonte única; em modo corrente a coluna se esconde ou se rotula. Fica para depois da
janela (a coluna não bloqueia nada em 20-24/08).

---

### OPS2 — Freeze administrativo de sync (janela de operação manual no Sleeper)
⚠️ **Implementado 18/08/2026 (MAN-OPS1-REG-F2) — o smoke de prod é o PRÓPRIO uso de hoje**
(congelar antes de o co-admin iniciar a operação) — Prioridade **Alta** (uso imediato)

> ⚠️ **Nota de ID:** o prompt veio como `MAN-OPS1-*`, mas **OPS1 é a higiene do working tree**
> (registrado 14/08). Nasceu **OPS2** — mesma regra de dedupe de sempre ([[O3]]).

**Problema:** operação manual em curso nos rosters do Sleeper (draft replay do OFF26-30 para
consumir as picks 2026): entre os drops e o complete, os rosters ficam **transitórios** — um sync
nessa janela fotografaria os 36 como dropados, sujando folha e keeper sheet na semana de cortes.
O botão é restrito a 3 admins, mas a lição [[OFF26-23]] vale: **o sistema recusa; não se depende
de disciplina.**

**Mecanismo (escopo mínimo, decisões do prompt honradas — sem TTL, sem agendamento, sem
auto-destrave):**

- **Flag** `sync_frozen` em AppConfig (molde das season flags; zero schema).
- **Guarda-helper única** `sync_sleeper.sync_freeze_reason()` — consultada pelas **duas entradas
  de motor**: [run_sync](sync_sleeper.py) recusa **antes de qualquer I/O** (nenhuma chamada de
  rede, nenhum SyncLog — a recusa não fotografa nada) e [_sync_trades](sync_sleeper.py), porque o
  **backfill de trades chama essa função direto**, sem passar pelo `run_sync` — porta mapeada e
  coberta pelo MESMO helper. ⛔ Nenhuma rota replica a checagem.
- **Portas cobertas:** botão da navbar (`POST /api/admin/sync` → **409** com mensagem acionável —
  *"…Destrave no painel /admin (card Sleeper Sync)"* — que o banner existente já exibe),
  backfill de trades (payload `frozen`, nada executa) e o boot do `app.py` (dormente em prod;
  degrada gracioso com payload de zeros). Não existe sync agendado — mapeado, nada mais a cobrir.
- **Toggle:** `POST /api/admin/sync_freeze` (`@admin_required`) + card do `/admin` com estado 🧊
  visível e botão Congelar/Destravar (decisão de menor atrito: o card de sync que os admins já
  usam; a navbar recusa com a mensagem, sem indicador novo).
- **Zero efeito fora do sync:** trades, telas e APIs de leitura intocadas; destravado, o
  comportamento é byte-idêntico (provado por sentinela: a guarda deixa o sync alcançar a camada
  de rede).

**Verificação:** `sync_freeze_test.py` (6 — recusa pré-I/O com sentinela de rede na 1ª e na 2ª
entrada de motor; destravado-passa; toggle liga/desliga; 409 da porta do botão; 403 sem admin);
smoke com app real sobre cópia: **congelar → botão 409 + backfill frozen + card 🧊 → destravar →
sync roda** (`success=True`). Gate [[O7]] exit 0 (diff toca `admin.html`); `template_js_test` +
suítes verdes.

**Relações:** [[OFF26-23]] (o princípio poka-yoke e o molde flag+endpoint+UI), [[OFF26-30]] (a
operação que estreia o freeze), [[OFF26-2]]/[[OFF26-4]] (as folhas/sheets que o freeze protege de
fotografia suja), [[OPS1]] (colisão de ID — item distinto, higiene do working tree).

---

### UX25 — Hub: excesso de roster vira obrigação explícita ("cortar ≥N até 20/08")
⚠️ **F2 implementada 19/08/2026 (MAN-UX-NEXT-REG-F2, F1-rápida + F2 na mesma sessão) — smoke de
produção PENDENTE** ([[PROC1]]; o diff toca `style.css`, artefato público conferível por URL) —
Prioridade **Crítica** (prazo 20/08)

**Problema (feedback do owner, 19/08, com print):** na janela pré-cortes, o card do Hub mostra
**"Slots livres 0"** tanto para o time exatamente no limite quanto para o time **acima** dele —
com os rosters inflados pelos 36 rookies, times com jogadores demais não viam **nenhuma**
obrigação. O cap negativo tem alerta próprio e **não** é o assunto deste item.

**F1-rápida (read-only, embutida):**

- **Truncamento confirmado:** `empty_spots = max(0, MAX_ROSTER − num_keepers)` no
  [salary_engine](salary_engine.py) — 27 jogadores → `max(0, −5)` → **0**, o excesso é engolido.
- **Limite canônico adotado: `MAX_ROSTER = 22` ATIVOS**, com os até 2 IR **fora da conta** — é a
  contagem de **composição** do regulamento (item 1.3), a mesma distinção que o [[OFF26-16]]
  cristalizou (IR conta na FOLHA, não na contagem). Fonte no código: a constante do engine —
  **zero literal novo**; os settings do Sleeper corroboram, mas a régua da liga é a do
  regulamento.

**F2 (leitura pura — zero schema, zero mudança de régua):**

- [league.py](routes/league.py): `cut_needed = max(0, ativos − MAX_ROSTER)` + `active_count` /
  `ir_count` / `roster_limit` como campos **novos** do card. ⛔ `atual` (a chamada do
  `draft_budget`) segue intocada — bid, slots e flags idênticos.
- [league.html](templates/league.html): faixa **"⚠️ Cortar ≥N jogador(es) até 20/08"** com a
  contagem **"X/22 ativos (+K IR)"** (o owner confere de onde vem o N; tooltip explica a régua).
  Renderiza **só** quando `cut_needed > 0` — time regular, zero ruído. CSS mínimo na cor de
  alerta que o card já usa.
- ⚠️ **Limite declarado:** o literal *"até 20/08"* morre com a janela — generalizar/remover fica
  para o pós-cortes (o mecanismo em si é permanente: excesso reaparece em qualquer inflação
  futura).

**Verificação:** `roster_excess_test.py` (5 — excesso vira obrigação; **IR fora da conta** (22+2
= legal); excesso com IR conta só ativos; limite exato/abaixo = zero; **réguas intocadas** — o
`slots` truncado continua o mesmo). Smoke na cópia inflada (estado 18/08): **3 cards com
obrigação** (24/22→≥2, 26/22→≥4, 27/22→≥5), 3/3 batendo com a query direta; ⭐ **âncora Trust The
Process conferida dos dois lados: 26 ativos → "cortar ≥4", e o Sleeper AO VIVO devolve os mesmos
26** (MellowBR: 22, regular — sem faixa). Gate [[O7]] exit 0; suítes verdes.

**-b (19/08/2026, MAN-UX25-b) — a mesma obrigação, VIVA no cap projector:** item **"Roster"** na
barra sticky, recalculado pelo **POST `/budget` que já roda a cada toggle** — o servidor conta
(ele conhece `is_on_ir` do banco; o payload do GET também o carrega — gap inexistente, conferido)
e o JS **só exibe** (F10); o limite chega no payload (`roster.limit` = `MAX_ROSTER` do engine —
zero hardcode no cliente). Exibição: `X/22 ativos (+K IR) ✓` discreto quando regular; **"· cortar
≥N"** em alerta quando o cenário excede, **contando para baixo** conforme os toggles até
regularizar. **Rookies do cenário ocupam vaga de ativo** (entram na contagem). **"Spots vazios"
mantido como está** — significado de vagas da AUCTION, onde 0 com excesso é verdadeiro; o
indicador novo ao lado desambigua (decisão de menor mudança). Campo `roster` **aditivo**;
D9/`budget` intocados — teste prova a folha $125 **com** o IR (régua [[OFF26-16]]) e o
`empty_spots` seguindo truncado. Smoke (cópia de prod): Trust **26/22 cortar ≥4 → toggla 4 → ✓ →
volta → reaparece**; rafaelferreirap com `+1 IR` fora da conta; Pitbull 22/22 neutro. +4 testes
(suíte em 9); `template_js_test` + gate [[O7]] exit 0.

**Fecha ✅ quando:** smoke de prod do owner — os cards estourados do Hub exibindo a faixa com N
correto **e** o projector com o indicador vivo (PROC1 pelo hash do `style.css` servido).

**Relações:** [[OFF26-16]] (a distinção folha × contagem que define a régua), [[UX18]] (o
precedente de "estado inviável sem alerta" e das flags canônicas), [[L3]] (o card em 3 zonas onde
a faixa se encaixa), [[OFF26-26]] (a entrada dos 36 que inflou os rosters), [[M1]] (o alerta de
cap que NÃO foi tocado).

---
