# Runbook — Procedimento Cowork da liga fantasma (FA auction no Sleeper)

> **OFF26-5.** Runbook operacional do procedimento **Cowork + Claude in Chrome**: como dirigir
> a UI do Sleeper para **montar e popular** a liga fantasma usada na FA auction. A API do
> Sleeper é **read-only** — a montagem/população só é possível **dirigindo a UI pelo navegador**.
>
> **Dois usos:**
> 1. **Referência operacional reproduzível** entre temporadas.
> 2. **Material colável no prompt do Cowork** (ou guardado na memória do Projeto Cowork) para o
>    agente ir direto aos caminhos certos.
>
> **Origem:** o conteúdo operacional abaixo foi escrito pelo próprio Cowork logo após executar o
> **PoC [[OFF26-6]]** (17/06/2026), com contexto fresco — por isso os detalhes de interação são
> fiéis (edição do campo de preço, anti-homônimo, conexão da extensão, anatomia do board).
> **Reconciliado** com as decisões de design arbitradas no OFF26-6 (liga permanente, config
> espelhando a real, separação setup único × trabalho anual).
>
> **Não duplicar conteúdo canônico:** a fonte dos **keepers + salários** é a **keeper sheet
> ([[OFF26-2]])**; a **auditoria** pré-leilão é o **[[OFF26-4]]**; o PoC que originou este
> runbook é o **[[OFF26-6]]**.
>
> Todos os nomes de botões/labels estão **literais**, como aparecem na tela (UI do Sleeper em
> inglês).

---

## Visão geral — DUAS FASES (decisão OFF26-6)

A liga fantasma é **PERMANENTE**: criada **uma única vez** (redraft, com os **12 owners reais**
dentro) e **reutilizada todo ano**. Isso separa o trabalho em duas fases:

- **FASE A — SETUP ÚNICO (uma vez na vida da liga):** criar a liga permanente, configurar roster
  espelhando a liga real, ativar Auction + Budget $200, **convidar os 12 owners reais**.
- **FASE B — TRABALHO ANUAL (a cada intertemporada):** **apenas popular os keepers** no draft
  board, mapeando por **owner**, a partir da keeper sheet ([[OFF26-2]]). **O reset de rosters é
  automático** (formato redraft reseta tudo na virada de season) — **não fazer manualmente**.

> **Por que permanente?** No PoC, **times sem dono (placeholders "Team 2", "Team 3"…) não são
> renomeáveis nem gerenciáveis** pela UI (ver §B-limitações). Com a liga permanente e os owners
> reais já dentro, esse bloqueio **não ocorre** no uso anual.

---

## 0. Pré-requisitos (toda sessão)

- Estar **logado no Sleeper** no Chrome.
- Para automação via **Claude in Chrome**: a extensão precisa estar **conectada**. No PoC, a
  primeira tentativa falhou com **"Claude in Chrome is not connected"**; foi resolvido abrindo um
  navegador com a extensão **ativa e logada na mesma conta**. **Sempre confirme a conexão antes
  de começar.**

---

# FASE A — SETUP ÚNICO (criar a liga permanente)

> Roda **uma vez**. Depois disso, todo ano é só a FASE B.

## A.1 Criar a liga (wizard de 4 passos)

### A.1.1 Abrir o wizard
1. Na **barra lateral estreita à esquerda** (faixa de ícones), clique no ícone **"+"** (círculo
   com mais). Isso **expande** o painel de ligas (cabeçalho "LEAGUES", "MOCK DRAFTS" e a lista de
   ligas existentes).
2. Ao lado do título **"LEAGUES"**, clique no **"+" circular**. Abre o modal do wizard.

> Se clicar no "+" da barra estreita te levar para outra tela (ex.: Messages), o painel de ligas
> ainda fica expandido — clique no "+" ao lado de "LEAGUES" para abrir o wizard.

### A.1.2 Step 1 of 4 — "Choose your game"
- Três cards: **Fantasy Football**, **Fantasy LoL**, **Fantasy Basketball**.
- Clique em **Fantasy Football**. (Avança automaticamente para o Step 2.)

### A.1.3 Step 2 of 4 — "Choose your league size"
- Campos:
  - **LEAGUE NAME** — input com placeholder "Enter the name of your league".
  - **NUMBER OF TEAMS** — dropdown (`select`), default **"8"**, opções: 4, 6, 8, 10, 12, 14, 16,
    18, 20, 22, 24, 32.
  - **LOGO (optional)** — botão de câmera (ignorável).
- Ações:
  1. Clique em **LEAGUE NAME** e digite o nome da liga fantasma permanente. Campo começa vazio.
  2. No dropdown **NUMBER OF TEAMS**, selecione **12**.
  3. Clique em **NEXT**.

### A.1.4 Step 3 of 4 — "Set up your league"
- **START FROM SCRATCH** → card **"Create New League / Pick Your Own Settings"** (vem
  **selecionado** por padrão).
- **OR / COPY FROM AN EXISTING LEAGUE** → copia configs de uma liga existente.
- Deixe **Create New League** selecionado e clique em **NEXT**.

### A.1.5 Step 4 of 4 — "Define your league"
- **LEAGUE TYPE** (3 cards): **Redraft** ("All rosters from this season are reset") · **Keeper**
  ("Each owner can keep designated players for next season") · **Dynasty** ("All rosters stay with
  their owners"). **Redraft vem selecionado por padrão.**
- **DRAFT TYPE** (3 linhas): **Snake** (default) · **Linear** · **Auction** ("Players awarded to
  the highest bidder").
- Ações:
  1. Mantenha **Redraft** (NÃO clique em Dynasty). → é o Redraft que **reseta os rosters
     automaticamente** todo ano (base da FASE B).
  2. Clique em **Auction** (a linha fica destacada).
  3. Clique em **CREATE LEAGUE**.
- Resultado: cai na página da liga. Cabeçalho mostra o nome + **"2026 12-Team PPR"** (sem
  "Dynasty", confirmando Redraft). Aparece "Invite friends to play 1/12" + link de convite e a
  lista "1 (seu time) … Team 12".

> **Auction está disponível tanto no wizard (Step 4) quanto depois em Draft Settings.** Marcar no
> wizard garante o estado final; confirmar depois em Draft Settings (§A.4).

## A.2 Abrir as Configurações da liga

- No topo da página da liga, clique no **ícone de engrenagem** (à direita do nome). Abre o modal
  com o **menu lateral esquerdo**: League Settings · Team Settings · Roster Settings · Scoring
  Settings · Draft Settings · Division Settings · Member Settings · Co-owner Settings ·
  Commissioner Control · Previous Leagues · Delete League.
- Fechar o modal: **"X"** no canto superior direito.

## A.3 Roster Settings — **espelhar a liga real (OBRIGATÓRIO)**

- Caminho: engrenagem → **Roster Settings** ("Set roster positions").
- Layout: cada posição tem um contador com botões **"–"** e **"+"** e o número de vagas.

> ⚠️ **PASSO OBRIGATÓRIO (decisão OFF26-6) — a config de roster DEVE espelhar a liga real.** O
> Sleeper cria a liga com **defaults** que **NÃO** batem com a liga real. **Achado do PoC:** a
> liga de teste nasceu com **WR = 2** (padrão Sleeper), mas a **liga real usa 3 WR** — ajustar
> **2 → 3 WR** é **obrigatório**, não opcional.

**Config-alvo (liga real Dynasty SB):** **1 QB · 2 RB · 3 WR · 1 TE · 1 FLEX (W/R/T) · 1 DEF ·
1 K** (+ **banco/IR** conforme a liga real). **Confirme cada posição contra o regulamento/liga
real antes de seguir.**

**Defaults observados no PoC (a corrigir):**
- QUARTERBACK (QB): 1  ✅ ok
- RUNNING BACK (RB): 2  ✅ ok
- WIDE RECEIVER (WR): **2** ⚠️ **ajustar para 3** (clicar **"+"** uma vez)
- TIGHT END (TE): 1  ✅ ok
- FLEX (W/R/T): **2** ⚠️ **ajustar para 1** conforme a liga real (clicar **"–"**) — confira o nº
  real de FLEX
- FLEX (W/R), (W/T), (Q/W/R/T), (IDP): 0
- KICKER (K): 1 · DEFENSE (DEF): 1
- (DL), (LB), (DB): 0
- (BN) banco: 5 → conferir contra a liga real (role a seção até o fim para ver banco/IDP/IR)

- **Como ajustar:** clique em **"+"/"–"** ao lado da posição. **SAVE** se a seção pedir.

## A.4 Draft Settings — Auction + Budget $200 (o "cap")

- Caminho: engrenagem → **Draft Settings** ("Set draft time, time per pick, draft order, and set
  keepers/dynasty"). Role para ver tudo:
  - **DRAFT TIME** — data + hora + **SAVE DRAFT TIME**.
  - **AUTOSTART DRAFT** — toggle.
  - **DRAFT TYPE** — dropdown. **Confirmar = Auction** (do wizard).
  - **NOMINATION PHASE DURATION** — dropdown (default "60 Seconds"). [só auction]
  - **OFFERING PHASE DURATION** — dropdown (default "2 Minutes"). [só auction]
  - **BUDGET** — campo numérico (default **200**). **É o cap por time.**
  - **CPU AUTO PICK** — toggle.
  - **DRAFT ORDER** — **RANDOMIZE** / **RESET BUDGETS**; slots 1..12 com budget ($200);
    "UNASSIGNED MEMBERS"; banner amarelo quando há membros sem ordem.
  - **SET KEEPERS/DYNASTY PLAYERS** — "Click below to go to draft lobby…" + botão **SET PLAYERS**.
    ← **é por aqui que se setam keepers com salário** (FASE B).
  - **AVAILABLE PLAYERS TO DRAFT** — dropdown (default "All").
  - **ALPHABETICAL SORT** — toggle.
  - **RESET DRAFT (CANNOT BE UNDONE)** — botão **RESET** (cuidado).

> **Não existe toggle dedicado de "Salary Cap" no Sleeper** (verificadas TODAS as seções:
> League, Team, Roster, Scoring, Draft, Division, Member, Co-owner, Commissioner Control). O
> **cap é o BUDGET do Auction** ($200/time): o cap individual **emerge** dos salários dos keepers
> consumindo o budget global. **PPR** já é o padrão de scoring (confirma em **Scoring Settings →
> Receiving → Reception = +1**).

## A.5 Convidar os 12 owners reais (ancorar a identidade)

- Use o link **"Invite friends to play"** (página da liga) para trazer **os 12 owners reais**
  para dentro da liga permanente.

> ⚠️ **Mapeamento owner↔time por `sleeper_owner_id` / handle do Sleeper (decisão OFF26-6).** A
> chave canônica e **estável** é o **owner (handle do Sleeper)**, **NUNCA o nome do time**
> (mutável) nem o número "Team N". No Manager essa ponte **já existe**: `Team.sleeper_owner_id`
> (populado pelo Sleeper sync; vínculo **M12** ✅). Ao popular keepers (FASE B), **identifique o
> time pelo OWNER**, não pelo número/nome da coluna.

## A.6 (Setup) Renomear o próprio time

- Caminho: engrenagem → **Team Settings** ("Set team name and player nicknames") → campo **TEAM
  NAME**.
- **triple-click** (ou clicar + **Ctrl+A**) para selecionar o texto e **digite o novo nome**.
- **Salvar:** não há botão "Save" aqui — **salva ao sair do campo** (clique em área vazia do
  modal). Confirmação no **League Chat**: *"MellowBR has updated their team name: …"*.

> **Limitação (PoC):** **Team Settings só renomeia o SEU próprio time.** Times placeholder sem
> dono **não podem ser renomeados** (Commissioner Control não tem essa função). **Na liga
> permanente isso é irrelevante** — cada owner real renomeia o próprio time. Mantido como nota
> histórica do PoC.

---

# FASE B — TRABALHO ANUAL (popular os keepers)

> Roda **a cada intertemporada**. **Pré-requisito:** a **keeper sheet [[OFF26-2]]** revelada
> (fonte dos keepers + salários + budget). **NÃO** se mexe em roster manualmente — o **redraft já
> resetou os rosters** na virada de season.

## B.1 Entrar no modo de setar players
1. engrenagem → **Draft Settings** → role até o fim → **SET KEEPERS/DYNASTY PLAYERS** → clique em
   **SET PLAYERS**.
2. Abre uma **NOVA ABA** com o draft board (`/draft/nfl/<DRAFT_ID>`). No topo: nome da liga, "2
   Min Per Pick · 12 Teams · 15 Rounds · Invite Leaguemates" e botão **START DRAFT** (**NÃO
   clicar**, a menos que queira iniciar o draft).

## B.2 Anatomia do board
- **Colunas = times** (rótulos "Team 1" … "Team 12"); cada coluna é um roster.
  - ⚠️ **Identifique a coluna pelo OWNER (handle Sleeper), não pelo rótulo "Team N".** Na liga
    permanente os times têm dono e nome reais — case cada coluna ao owner correto da keeper sheet.
- **Linhas = vagas do roster** na ordem (QB, RB, RB, WR, WR, WR…). ⚠️ Confirme que o board reflete
  a config **3 WR** etc. (FASE A.3).
- Embaixo: lista de jogadores com busca **"Find player Ctrl + U"**, filtros (All / QB / RB / WR /
  TE / FLEX / K / DEF) com contadores (ex.: "All 0/15"), colunas de projeção ($PROJ, BYE, PROJ…).
- No centro/topo: barra do leilão com seletor de preço **"–  $ 1  +"** e botão de ação.

## B.3 Atribuir um keeper a um time, com salário
1. Clique na **célula da posição** do time-alvo (ex.: célula **QB** da coluna do owner X). Aparece
   um **menu de contexto**:
   - **"Set Player — Manually set a player for Team N"**
   - **"Reset Nomination — Change nominator to Team N"**
2. Clique em **Set Player**. A barra do topo muda para **"Make Manual Pick for Team N"** com
   **"Assign a player"** e o campo de busca.
3. Clique no campo de busca e **digite o nome** do jogador (ex.: `Mahomes`).
4. **VERIFICAÇÃO (passo crítico — anti-homônimo):** confira, na linha do resultado, **a posição e
   a sigla do time da NFL** sob o nome (ex.: "QB **KC**", "RB **ATL**"). Use isso para não pegar
   um homônimo. (Ver §B-armadilhas: dois Josh Allen.)
5. Clique no **"+"** (círculo) à **esquerda** da linha do jogador. O topo passa a mostrar o
   jogador + o seletor de preço **"–  $ 1  +"** e o botão **SET PLAYER**.
6. **Definir o salário** (valor da keeper sheet):
   - Clique sobre o número **"$ 1"** — ele vira editável (aparece cursor).
   - Pressione **Ctrl+A** para selecionar e **digite o valor** (ex.: `40`). Digitar é muito mais
     rápido que "+/–" (andam de 1 em 1).
   - **Confira o valor** antes de confirmar (o cursor pode tapar o número — dê zoom/afaste o mouse
     para ler "$ 40").
7. Clique em **SET PLAYER** para confirmar.
8. A célula é preenchida (colorida) com jogador + salário, ex.: **"P. Mahomes $40 / QB - KC (5)"**.
   Os contadores embaixo atualizam (ex.: "All 1/15", "QB 1/1").
9. **Repita** para cada keeper, clicando na **próxima vaga** do mesmo time e refazendo 1–8; depois
   passe ao próximo owner.

### B.3.1 Exemplo concreto executado no PoC (time "Teste Alpha")
- **Patrick Mahomes** — verificado **QB, KC (Kansas City)** — salário **$40**.
- **Bijan Robinson** — verificado **RB, ATL (Atlanta)** — salário **$30**.
- Total de salários: **$70**; cap restante esperado: **$200 − $70 = $130**.

## B.4 Ao terminar de popular — **gatilho da auditoria [[OFF26-4]]**

> ⚠️ **ANTES de iniciar o auction**, rode a **auditoria [[OFF26-4]]**: diff da liga fantasma
> **contra a keeper sheet [[OFF26-2]]**. Pontos que a auditoria precisa respeitar (achados do PoC):
> - **Budget é CALCULADO, não lido:** o cap restante por time **só aparece ao vivo durante o
>   auction**; no pré-draft **não há número de budget restante na tela**. A auditoria calcula
>   **`$200 − Σ salários dos keepers`**.
> - **Lê designações de keeper, não roster:** keepers setados no board **não populam o roster**
>   antes do draft (a página do time fica "Empty"); ficam só como **designação de keeper** no
>   board. A auditoria lê **as designações**.
> - **Owner por `sleeper_owner_id`** (ponte já resolvida no Manager via M12).
>
> Só **depois** de a auditoria bater, iniciar o auction.

---

## Armadilhas / hesitações resolvidas (do PoC)

1. **"Existe toggle de Salary Cap?"** — Não. O cap é o **BUDGET do Auction** ($200/time). (§A.4)
2. **"Auction no wizard ou em Settings?"** — Marcar no wizard (Step 4) e **confirmar** em Draft
   Settings → DRAFT TYPE.
3. **"Qual time é a coluna 'Team N'?"** — No board os times aparecem como "Team N", e a **ordem de
   draft** (slots) é um conceito separado (no PoC estava toda "unassigned"). **Na liga permanente,
   identifique a coluna pelo OWNER real (handle Sleeper), não pelo rótulo "Team N".** (No PoC,
   como liga nova, "Team 1" era o roster do comissário; isso **não** é regra de identidade — é
   coincidência do setup descartável.)
4. **Risco de homônimo (Josh Allen)** — Há **dois Josh Allen**: QB (Buffalo Bills) e LB/edge
   (Jacksonville Jaguars). **Sempre confirmar a sigla do time da NFL** na busca antes de clicar no
   "+". (Para Buffalo, escolher **QB, BUF**.)
5. **Edição do campo de preço** — Ao clicar no "$ 1", o cursor pode tapar o número. Resolver com
   **Ctrl+A → digitar → zoom para conferir** antes do SET PLAYER.

---

## Limitações / bloqueios da plataforma (resumo)

1. **Sem "Salary Cap" dedicado** — usar o **Budget** do Auction como cap.
2. **Keepers setados no board NÃO aparecem no roster antes do draft** — a página do time fica
   "Empty"; só populam **quando o auction roda**. Pré-draft são só designação de keeper no board.
   → relevante para a auditoria [[OFF26-4]] (lê designações, não roster).
3. **Cap restante não tem indicador numérico pré-draft** — o orçamento restante por time **só
   aparece ao vivo durante o auction**. → a auditoria **calcula** ($200 − Σ keepers).
4. **Não dá para renomear times sem dono** — Team Settings só edita o próprio time; sem função de
   comissário para "Team 2"/"Team 3". → **não-aplicável na liga permanente** (owners reais já
   dentro); nota histórica do PoC.
5. **Conexão da extensão** — a automação exige o **Claude in Chrome conectado**; checar antes.

---

## Checklist rápido (TL;DR)

### Setup único (uma vez)
1. Sidebar "+" → "+" ao lado de **LEAGUES** → wizard.
2. Step 1: **Fantasy Football**.
3. Step 2: nome + **NUMBER OF TEAMS = 12** → **NEXT**.
4. Step 3: **Create New League** → **NEXT**.
5. Step 4: **Redraft** + **Auction** → **CREATE LEAGUE**.
6. Engrenagem → **Draft Settings**: confirmar **DRAFT TYPE = Auction** e **BUDGET = 200** (o cap).
7. **Roster Settings**: **espelhar a liga real — ajustar WR 2→3** (e demais posições);
   **obrigatório**.
8. **Convidar os 12 owners reais** (link Invite) — identidade por **handle/`sleeper_owner_id`**.

### Trabalho anual (a cada intertemporada)
9. (Reset de rosters é **automático** no redraft — **não fazer nada**.)
10. Engrenagem → **Draft Settings → SET PLAYERS** (abre aba do draft board).
11. Para cada keeper da **keeper sheet [[OFF26-2]]**: localizar a coluna **pelo OWNER** → clicar na
    célula → **Set Player** → buscar → **conferir time NFL** → "+" → clicar no preço → **Ctrl+A** →
    digitar salário → **SET PLAYER**.
12. **Rodar a auditoria [[OFF26-4]]** (diff vs. keeper sheet) **ANTES** de iniciar o auction.
13. **NÃO** clicar em **START DRAFT** até a auditoria bater e tudo estar populado.
