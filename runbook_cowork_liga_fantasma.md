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
> **🔧 CORRIGIDO EM 02/08/2026 (MAN-OFF26-10-11-REG) contra a UI real.** A liga permanente
> **Dynasty SB FA Auction** foi criada e **1 time completo (10 keepers) foi transcrito e
> cronometrado** pelo Cowork. A transcrição revelou que **o caminho de entrada da FASE B
> documentado na versão anterior NÃO EXISTE** na interface atual (ver §B.1). As correções estão
> marcadas com **🔧 CORREÇÃO 02/08** ao longo do texto.
>
> **Esforço medido (não estimado):** **20 min 32 s** para 1 time de 10 keepers, dos quais **~9 min
> de overhead único** de descoberta do caminho. **Ritmo de regime: ~75 s/jogador ≈ 12,5 min/time →
> ~2,5 h para os 12 times.** (Referência: a transcrição **manual** do ano anterior consumiu **uma
> tarde inteira**.) **Decisão:** 2026 roda **via Cowork** com este runbook; um **script
> determinístico** fica como melhoria para **2027** — o argumento de "não caber na janela de 48 h
> entre o late drop e o leilão" **cai** diante das 2,5 h medidas. O caminho por **API interna não
> documentada** foi **deliberadamente descartado**: sem contrato, quebra sem aviso, provável
> violação de termos de uso e **expõe a conta de comissário da liga real**.
>
> **🔧 2ª RODADA DE CORREÇÕES — 02/08/2026 (MAN-OFF26-RUNBOOK-REG-PT2).** O runbook corrigido foi
> **exercitado e validado**: **Team 3 (10 keepers, $148)**, **Team 4 (8, $95)** e **Team 5 (6,
> $60)**, todos com os totais conferindo, **sem redescoberta de caminho**. Novas correções: **não
> fixar URL de board** (§B.1 — o `draft_id` **muda a cada reset** e a URL velha **trava em
> LOADING**), **identificação de coluna em liga com placeholders** (§B.2), **reescala do board**
> (§B.2), **vaga atribuída por posição** (§B.3.0), **preço nasce em $1 sempre** (§B.3) e **filtro
> de K/DEF esconde os já designados** (§B.3). **⛔ Uma recomendação da 2ª execução foi REJEITADA:**
> rebaixar o check anti-homônimo — ver armadilha 4. **Marcadas com 🔧 CORREÇÃO 02/08 (2ª
> execução).**
>
> ⚠️ **Variância de ambiente:** a 2ª execução levou **58min26s para 3 times** — não por regressão do
> método, e sim por **dezenas de timeouts de captura de tela (30 s cada)**. **Sem causa
> identificada; imprevisível.** Ver a mitigação de **fatiamento por time** no TL;DR.
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
  1. Clique em **LEAGUE NAME** e digite o nome da liga fantasma permanente — **`Dynasty SB FA
     Auction`** (🔧 **CORREÇÃO 02/08:** nome real da liga criada). Campo começa vazio.
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
  - ~~**SET KEEPERS/DYNASTY PLAYERS** — "Click below to go to draft lobby…" + botão **SET
    PLAYERS**.~~ 🔧 **CORREÇÃO 02/08: esta seção NÃO EXISTE na UI atual.** Não é por aqui que se
    setam keepers — ver **§B.1** para o caminho real.
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

## B.1 Entrar no board — 🔧 **CORRIGIDO EM 02/08/2026**

> ⚠️ **O caminho da versão anterior NÃO EXISTE.** Não procure engrenagem → Draft Settings →
> *SET KEEPERS/DYNASTY PLAYERS* → *SET PLAYERS*: **essa seção não está na UI atual**. Perder tempo
> caçando esse caminho foi a maior parte dos ~9 min de overhead da transcrição cronometrada.

**O board JÁ ESTÁ EM MODO DE DESIGNAÇÃO no pré-draft.** Basta chegar ao board e **clicar direto na
célula vazia** da coluna do time (§B.3). Não há modo a ativar, nem botão a apertar antes.

### 🔧 **CORREÇÃO 02/08 (2ª execução) — NÃO fixe a URL do draft board**

> ⛔ **O `draft_id` MUDA a cada RESET DRAFT** (e presumivelmente a cada virada de season). Uma URL
> de board anotada numa sessão **morre na seguinte** — e morre **em silêncio: a página trava
> indefinidamente em LOADING**, sem mensagem de erro. Se o board não carregar, **a primeira
> hipótese é URL velha**, não lentidão.

**Chegue ao board por descoberta, toda vez:**
1. Abrir a **página da liga** (o `league_id` **é estável** — esse sim pode ser anotado).
2. Ir ao **pré-draft** → widget **Draftboard** → **ícone de globo**.

*(Alternativa para quem estiver com acesso de leitura à API: reler o `draft_id` da liga antes da
sessão. De um jeito ou de outro, **o `draft_id` é redescoberto, nunca reaproveitado**.)*

No topo do board: nome da liga, resumo do formato e o botão **START DRAFT** — **NÃO clicar**.

## B.2 Anatomia do board
- **Colunas = times**; cada coluna é um roster. 🔧 **CORREÇÃO 02/08 (2ª execução) — a coluna se
  identifica de duas formas, conforme o estado da liga:**
  - **(a) Com owners reais dentro (estado do uso REAL):** ⚠️ **identifique pela coluna do OWNER
    (handle Sleeper), não pelo nome do time** (mutável). Case cada coluna ao owner da keeper sheet.
  - **(b) Com times placeholder (estado de TESTE):** os cabeçalhos são **avatares vazios, SEM
    rótulo de texto** — **não existe "Team N" escrito em lugar nenhum** na coluna. A verificação
    canônica nesse estado é o **menu de contexto da célula**, que exibe
    ***"Manually set a player for Team N"***. Abrir o menu **antes de cada designação** é o que
    confirma o time.
  - ⚠️ A orientação (a) **pressupõe rótulos que só existem quando os owners reais entram** — em
    liga de teste, use (b).
- **Linhas = vagas do roster** na ordem (QB, RB, RB, WR, WR, WR…). ⚠️ Confirme que o board reflete
  a config **3 WR** etc. (FASE A.3).
  - 🔧 **CORREÇÃO 02/08 — K e DEF ficam ABAIXO DA DOBRA.** As últimas linhas do board não aparecem
    de saída. **Revele pela seta ▼ do canto direito** — o **scroll do mouse NÃO move o board**.
    Esquecer isso faz parecer que o time está completo quando faltam 2 vagas.
  - 🔧 **CORREÇÃO 02/08 (2ª execução) — o board RESCALA após a primeira interação.** Ele
    **desloca/reescala**, o que **quebra qualquer referência posicional** memorizada. Mitigação
    observada: **revelar FLEX/K/DEF pela seta ▼ ANTES** de mirar as linhas de baixo, e **confirmar
    o time pelo menu de contexto antes de cada designação** (§B.2b). *(A criticidade disso é menor
    do que parece — ver §B.3.0: a vaga é atribuída por posição, não pela célula clicada.)*
- Embaixo: lista de jogadores com busca **"Find player Ctrl + U"**, filtros (All / QB / RB / WR /
  TE / FLEX / K / DEF) com contadores (ex.: "All 0/15"), colunas de projeção ($PROJ, BYE, PROJ…).
- No centro/topo: barra do leilão com seletor de preço **"–  $ 1  +"** e botão de ação.

## B.3 Atribuir um keeper a um time, com salário

### B.3.0 🔧 **NOVO 02/08 (2ª execução) — a vaga é atribuída POR POSIÇÃO**

Escolher o jogador **já o coloca na vaga correta automaticamente**: um **RB entra no FLEX** quando
as vagas de RB estão cheias. **Clicar a célula exata é conveniência, não obrigação** — o que
importa é acertar **a coluna (o time)**, não a linha. Isso desarma boa parte do risco da reescala
do board (§B.2).

1. Clique na **célula da posição** do time-alvo (ex.: célula **QB** da coluna do owner X). Aparece
   um **menu de contexto**:
   - **"Set Player — Manually set a player for Team N"**
   - **"Reset Nomination — Change nominator to Team N"**
2. Clique em **Set Player**. A barra do topo muda para **"Make Manual Pick for Team N"** com
   **"Assign a player"** e o campo de busca.
3. Clique no campo de busca e **digite o nome** do jogador (ex.: `Mahomes`).
   - 🔧 **CORREÇÃO 02/08 — para K e DEF, use o FILTRO DE POSIÇÃO** (K / DEF) em vez de digitar o
     nome. Digitar nome de kicker/defesa é lento e errático; o filtro entrega a lista curta direto.
     🔧 **Confirmado na 2ª execução**, com uma propriedade útil: **kickers e defesas já designados
     SOMEM do filtro** — então **"pegar o primeiro disponível" é limpo e sem risco de colisão**.
4. **VERIFICAÇÃO (anti-homônimo):** confira, na linha do resultado, **a posição e a sigla do time
   da NFL** sob o nome (ex.: "QB **KC**", "RB **ATL**").
   - 🔧 **CORREÇÃO 02/08 — alerta SUAVIZADO, não removido.** O pool de designação traz **apenas
     ofensivos elegíveis**, então o caso clássico do **Josh Allen LB/JAX simplesmente NÃO APARECE**
     na busca. O risco residual é menor do que a versão anterior dava a entender — mas **dois
     ofensivos homônimos continuariam ambíguos**, então **a conferência de posição + time NFL
     segue valendo**.
5. 🔧 **CORREÇÃO 02/08 — clique no "+" DA LINHA, NUNCA NO NOME.** O **"+"** (círculo) fica à
   **esquerda** da linha do jogador. **Clicar no nome abre o perfil do jogador, e fechar o perfil
   CANCELA O FLUXO INTEIRO** — volta ao board sem nada setado, e é preciso recomeçar da célula.
   Feito certo, o topo passa a mostrar o jogador + o seletor de preço **"–  $ 1  +"** e o botão
   **SET PLAYER**.
6. **Definir o salário** (valor da keeper sheet):
   - 🔧 **CORREÇÃO 02/08 — o campo JÁ VEM COM $1.** Para keepers de **$1 não é preciso editar
     nada**: vá direto ao **SET PLAYER**. (Como boa parte do roster tende a ser de $1, isso corta
     bastante tempo.) 🔧 **Generalizado na 2ª execução:** o campo **nasce em `$1` SEMPRE** —
     **inclusive quando o `$PROJ` exibido é maior**. A regra vale para **qualquer keeper de $1**,
     não só K/DEF. Não se deixe induzir pelo `$PROJ`: o que conta é o valor da keeper sheet.
   - Para os demais: clique sobre o número **"$ 1"** — ele vira editável (aparece cursor).
   - **Ctrl+A** para selecionar e **digite o valor** (ex.: `40`). Digitar é muito mais rápido que
     "+/–" (andam de 1 em 1). 🔧 **Nota 02/08:** o **Ctrl+A funcionou em 100% dos casos** na
     transcrição cronometrada — era alerta na versão anterior, é **nota** agora.
   - **Confira o valor** antes de confirmar (o cursor pode tapar o número).
7. Clique em **SET PLAYER** para confirmar.
8. A célula é preenchida (colorida) com jogador + salário, ex.: **"P. Mahomes $40 / QB - KC (5)"**.
   Os contadores embaixo atualizam (ex.: "All 1/15", "QB 1/1").
9. **Repita** para cada keeper, clicando na **próxima vaga** do mesmo time e refazendo 1–8; depois
   passe ao próximo owner.

### B.3.1 Exemplo concreto executado no PoC (time "Teste Alpha")
- **Patrick Mahomes** — verificado **QB, KC (Kansas City)** — salário **$40**.
- **Bijan Robinson** — verificado **RB, ATL (Atlanta)** — salário **$30**.
- Total de salários: **$70**; cap restante esperado: **$200 − $70 = $130**.

## B.3.2 🔧 **NOVO (02/08/2026) — o teto de lance bloqueia times estourados**

> Não estava neste runbook e **vai aparecer na tela** em 2026. Descoberto por experimento na
> própria liga; detalhe completo na seção do [[OFF26-10]] em `improvements.md`.

O Sleeper **impõe um teto por designação** e **reserva $1 por vaga ainda não preenchida**:

```
teto = 200 − gasto − (vagas_restantes − 1)
```

Ultrapassar → a designação é **recusada** com a mensagem literal
***"The specified slot does not have enough budget."*** (Verificado: time com $150 gastos e 21
vagas livres tem teto **$29** — $40/$33/$32 recusados, $29 aceito. E não há falso positivo: 10
keepers somando $140 passaram sem aviso.)

**Consequência operacional — a população é ESCALONADA, não de uma vez:**
1. Popular **primeiro** os times já enquadrados no cap.
2. Times ainda **acima do limite NÃO ENTRAM no board** — esperam o **late drop (22/08)** e só então
   são populados.

**Se a designação for recusada, NÃO tente contornar** (não baixe o salário para "caber"): o
salário vem da keeper sheet e é canônico. Registre o time como **bloqueado** e siga para o próximo.

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
4. **Risco de homônimo (Josh Allen)** — 🔧 **SUAVIZADO EM 02/08:** o pool de designação traz
   **apenas ofensivos elegíveis**, então o Josh Allen **LB/JAX não aparece** na busca — o caso
   clássico está fora de alcance. **O alerta permanece** em versão menor: **dois ofensivos
   homônimos continuariam ambíguos**, então siga conferindo **posição + sigla NFL** antes do "+".
   > ⛔ **NÃO rebaixar este check além disto (registro de 02/08, 2ª execução).** A 2ª execução
   > relatou **divergência de sigla** (Waddle como DEN, Hill sem sigla) e **recomendou enfraquecer
   > a conferência**. **A recomendação foi rejeitada:** a causa era a **lista de teste**, montada
   > à mão com **times de temporadas anteriores** — **dado velho na lista**, não divergência da
   > plataforma. Na execução **real** a keeper sheet sai do **Manager**, que **sincroniza do
   > Sleeper**: os dois lados bebem da **mesma fonte** e a sigla **bate**.
   >
   > **Orientação INVERTIDA, portanto:** se a sigla divergir **na execução real**, isso é **sinal
   > de problema no sync ou na sheet** → **PARE e REPORTE**. Não é ruído a ignorar, é **sintoma**.
5. **Edição do campo de preço** — 🔧 **REBAIXADO A NOTA EM 02/08:** o **Ctrl+A funcionou em 100%
   dos casos** na transcrição cronometrada. Fluxo: clicar no "$ 1" → **Ctrl+A** → digitar →
   conferir → SET PLAYER. E lembre: **para keepers de $1 não é preciso editar nada.**
6. 🔧 **NOVO 02/08 — "cliquei no jogador e o fluxo sumiu"** — foi clique **no nome** em vez do
   **"+"** da linha. O nome abre o perfil; fechar o perfil **cancela a designação inteira**.
   Recomeçar da célula.
7. 🔧 **NOVO 02/08 — "o time está completo mas faltam K e DEF"** — as linhas estão **abaixo da
   dobra**; revele com a **seta ▼** (o scroll do mouse não move o board).
8. 🔧 **NOVO 02/08 — "não consigo setar, diz que não tem budget"** — é o **teto de lance** (§B.3.2).
   O time está estourado e **só entra no board após o late drop**. Não baixe o salário.

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
6. 🔧 **NOVO 02/08 — teto de lance com reserva de $1/vaga** (`teto = 200 − gasto −
   (vagas_restantes − 1)`): **times acima do limite não podem ser populados**. → **população
   escalonada obrigatória** (ver §B.3.2 e [[OFF26-10]]).
7. 🔧 **NOVO 02/08 — o board já está em modo de designação** no pré-draft; **não existe** a seção
   *SET KEEPERS/DYNASTY PLAYERS* nas Draft Settings (ver §B.1).

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

### Trabalho anual (a cada intertemporada) — 🔧 **atualizado 02/08/2026**
9. (Reset de rosters é **automático** no redraft — **não fazer nada**.)
10. Chegar ao board **por descoberta**: página da liga → **pré-draft** → widget **Draftboard** →
    **ícone de globo**. **NUNCA reaproveitar URL de board anotada** — o `draft_id` muda a cada
    reset e a URL velha **trava em LOADING** (§B.1). **Não** procurar *SET KEEPERS/DYNASTY
    PLAYERS* — **não existe**; o board já está em modo de designação.
11. **Popular os times ENQUADRADOS primeiro.** Times acima do teto (§B.3.2) **não entram** — ficam
    para depois do **late drop (22/08)**.
12. Para cada keeper da **keeper sheet [[OFF26-2]]**: confirmar a coluna — **pelo OWNER** se os
    times têm dono, **pelo menu de contexto** (*"…for Team N"*) se forem placeholders (§B.2) →
    clicar na **célula vazia** → **Set Player** → buscar (**filtro de posição** para K/DEF) →
    **conferir posição + time NFL** → **"+" da linha (nunca o nome)** → se salário > $1: clicar no
    preço → **Ctrl+A** → digitar → **SET PLAYER**. Para **$1, não editar** — direto no SET PLAYER.
    *(A vaga é atribuída **por posição** — acertar a coluna é o que importa; §B.3.0.)*
13. **Revelar FLEX, K e DEF com a seta ▼** antes de mirar as linhas de baixo **e** antes de dar o
    time por completo (o board **reescala** após a 1ª interação).
14. Após o late drop, **popular os times que faltaram**.
15. **Rodar a auditoria [[OFF26-4]]** (diff vs. keeper sheet) **ANTES** de iniciar o auction.
16. **NÃO** clicar em **START DRAFT** até a auditoria bater e tudo estar populado.

> ⏱️ **Referência de tempo — e a variância que ela esconde.** Ritmo de regime medido na 1ª
> execução: ~**75 s/jogador** ≈ **12,5 min/time** ≈ **~2 h** para os 12 times. **Mas a 2ª execução,
> no mesmo ambiente, levou 58min26s para 3 times** — não por regressão do método, e sim por
> **dezenas de timeouts de captura de tela (30 s cada)** que dominaram o relógio. **A instabilidade
> é imprevisível e não tem causa identificada:** a mesma tarefa pode levar ~2 h ou ~5 h, e **não há
> como saber antes de começar**.
>
> ✅ **Mitigação: FATIE A TRANSCRIÇÃO POR TIME.** Cada time é uma **unidade verificável** (confira o
> total de salários ao fechar). Se a sessão degradar, **a seguinte retoma do time seguinte, sem
> refazer nada** — o modo de falha é **lentidão, não erro**, então o trabalho já feito continua
> válido.
