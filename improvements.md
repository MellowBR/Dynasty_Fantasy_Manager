# improvements.md — Fantasy Manager

> Backlog vivo de melhorias, bugs e features pendentes.
> Atualizado em: 03/08/2026-pt7 (sessão MAN-OFF26-4-LABELS: **smoke de produção do [[OFF26-4]] COMPLETO — 4 de 4** (deploy `aec8d8f`): o Render **alcança a API do Sleeper** e a **derivação do `draft_id` funciona de produção** (22 rodadas, 24 designações, 10/12 colunas com dono, `pre_draft`) → **modos de falha de ambiente descartados**, não são mais coisa a descobrir em 20/08. **(A) Rename:** a tela tinha **dois cards com o mesmo título** ("Liga fantasma" para leitura ao vivo **e** para configuração persistida) — sob prazo isso convida a procurar no card errado ou **salvar onde não se pretendia**. Agora **"Estado da liga fantasma"** × **"ID da liga fantasma"**; **só rótulo** (ordem, layout, lógica, rota e payload intactos), verificado em **5 estados da página** sem nenhuma duplicata. **(B) ✅ D2 — A CONFERÊNCIA ARITMÉTICA FOI FEITA e a pendência FECHA:** lido do regulamento (PDF em `data/`), a **8.3.4** diz *"completar as **22 posições do roster** … (22 – número de keepers)"* → **regulamento 22 = sala 22 (`roster_positions` e `rounds`) = Manager 22 (`MAX_ROSTER`)**, com a **mesma fórmula de reserva**. **O medo do D2 não se concretizou.** ⚠️ **Mas há diferença residual, e não é de contagem — é de QUEM ENTRA NA CONTA:** o item **1.3** diz que os **2 IR "não são considerados no total de 22"**; o **Manager conta o IR dentro** dos 22 e o **Sleeper também** (o keeper em IR **é designado** e ocupa uma das 22 rodadas). → **Manager e Sleeper concordam entre si, logo a auditoria NÃO produz falso positivo**; **ambos divergem do regulamento em até $2** de `usable_draft_budget` para time com IR (3 times hoje). **Nenhum cálculo alterado** — conferência é registro. 🔲 **Ambiguidade DEVOLVIDA ao owner:** a 8.3.4 não diz se **keeper em IR conta** em "(22 − keepers)"; leitura (a) conta → nada muda; leitura (b) não conta → o Manager está até $2 permissivo e **o ajuste mexeria no `salary_engine`** — **regra de liga, decisão do owner**. ⚠️ **Aritmética adicional respondida: SIM, um time PODE exceder o board** — o regulamento permite **24** (22+2 IR) e o board comporta **22 designações**; **1 time está em 24 HOJE** (medido ao vivo) e, se chegar assim em 20/08, **2 keepers ficam expostos** pelo achado "keeper fora do board é leiloável". **Segunda causa de time não populável**, ao lado do teto — e esta **não se resolve com o late drop** (1 drop não tira 2 excedentes); encadeia com [[OFF26-10]]/[[OFF26-5]], registrada como **risco, não solução**. ⛔ **QUARTA PREMISSA DA MESMA FAMÍLIA REFUTADA:** *"a fantasma não tem slot de IR"* é **FALSO** — `settings.reserve_slots = 2` **nas duas ligas**, e o `roster_positions` da liga **REAL** (que tem IR, 3 rosters usando) **também não lista "IR"**: o campo lido **não é onde o dado mora**. → **a divergência de config real × fantasma quanto a IR NÃO EXISTE**; a resolução do owner **permanece correta e necessária**, por outro motivo — **slot de IR não é slot de draft** (22 rodadas = 22 designações, com ou sem IR). **A decisão não muda; o porquê muda.** **Limitação registrada e não corrigida:** timeout parcial (`/league` responde, `/picks` não — ocorreu de fato nos testes) degrada para **"0 designações"**, indistinguível de board vazio — **falha para o lado SEGURO** (board vazio → todos "não populados" → veredito **BLOQUEADO**; a auditoria nunca libera por falta de leitura), então é **imprecisão de rótulo, não risco de gate**. **34/34** e **48/48**; fixtures A/B/C inalteradas; `draft_id` não persistido; board intacto, draft não iniciado, só `GET`. Status do OFF26-4 **inalterado (⚠️)** — falta o smoke com **sheet real**, a partir de 20/08.)
> Atualizado em: 03/08/2026-pt6 (sessão MAN-OFF26-4-META: **o smoke de produção do [[OFF26-4]] fechou 3 de 4 pontos e o 4º virou correção**. ⚠️ **Achado de processo antes de tudo:** os **10 commits do dia ficaram locais** — o deploy vivo era o de 02/08 e o smoke só foi possível depois do push; **o auto-deploy dispara no push, e não havia push**. Sem tentar o smoke, isso apareceria **em 20/08**. **Passaram:** rota responde e renderiza, card do `/admin` leva à página, `phantom_league_id` **semeado no `AppConfig` de produção** pelo boot. ⛔ **O 4º ponto NÃO ERA ALCANÇÁVEL — e era o único que só produção prova:** a auditoria bloqueia por ausência de sheet **antes** de exibir qualquer coisa, então o bloco de meta (`draft_id` derivado, `pre_draft`, rodadas) **não renderizava** — ficando sem prova que **o Render alcança a API do Sleeper** e que a **derivação funciona de lá**. **São modos de falha de AMBIENTE** (egress, DNS, timeout de plano) que **não aparecem em localhost** e seriam descobertos **no dia em que a auditoria precisa funcionar**. **Buraco de validação, não bug.** **F2-META (borda e apresentação; núcleo, veredito e classes INTOCADOS):** a meta da liga é lida e exibida **sempre**, inclusive sob bloqueio — o `run_audit` já lia os dois lados de forma independente, faltava a **meta carregar o suficiente** e o **template renderizá-la fora do `if report.ok`**. Campos: `draft_id` **com selo "derivado"** (não guardado), status, **rodadas lidas do DRAFT**, **designações no board** e **colunas com dono × sem dono**. **Erro de leitura é ESTADO PRÓPRIO do bloco**, distinto do bloqueio por falta de insumo: `league_id` inválido → **erro limpo em 0,29 s, HTTP 200**, sem pendurar e sem 500; `run_audit` ganhou guarda contra exceção de rede/parse — **falha de liga nunca derruba a rota**. **Motivo de produto independente do smoke:** `league_id` errado no `AppConfig` era **falha silenciosa até 20/08**; agora o operador confere que aponta para a liga certa **antes** de a sheet existir. **34/34** (29+5) e **48/48** do `salary_engine`; fixtures A/B/C com o mesmo resultado; `draft_id` segue **não persistido** (grep); board intacto, draft não iniciado, só `GET`. **⚠️ A contagem de donos mudou pela QUARTA vez no mesmo dia — 7 esperados → 8 → 9 → 10** (2 sem dono agora): é exatamente por isso que ela é **campo do relatório, nunca constante**, e é o que o bloco novo passa a mostrar ao vivo. Item segue **⚠️** — falta o smoke com **sheet real**, só possível a partir de **20/08**.)
> Atualizado em: 03/08/2026-pt5 (sessão MAN-OFF26-4: **F2 do [[OFF26-4]] — a auditoria de keepers pré-leilão EXISTE como código**. Status **🔲 → ⚠️** (não fecha ✅ sem smoke prod, [[PROC1]] — e a sheet real só nasce em **20/08**). Novo **`keeper_audit.py`**: núcleo `audit(board, sheet)` **puro** (sem DB, sem rede — molde `salary_engine`) + camada de leitura read-only (`fetch_board`/`build_sheet`/`run_audit`); `templates/keeper_audit.html` com **veredito no topo** (ABERTURA LIBERADA/BLOQUEADA + motivos), 3 rotas no admin (página, JSON, e `POST` que persiste **só o `league_id`**), seed do `phantom_league_id` no `AppConfig` (D1). **Zero divergências NÃO libera:** bloqueiam keeper exposto (classe 1), **time não populado**, **time sem coluna**, **coluna órfã** e **keeper sem identidade resolvível**. **Decisões que a spec delegou:** D3 = **re-query** (o [[OFF26-2]] **não foi tocado**, como o critério mandava); severidade relativa das classes 2-4 (alta/alta/média, com a 1 bloqueante por natureza); ordenação **pior primeiro**. **7 divergências spec × terreno RELATADAS, não resolvidas por conta própria** — as três de maior peso: **(1) o helper do D6 não tinha o que reusar** (`_team_by_roster` consulta o banco; o núcleo puro casa owner↔time **em memória**) — a invariante foi cumprida, o meio previsto é que não se aplicava; **(2) a spec previa UM estado e o terreno tem DOIS** — time **sem coluna** (convite não aceito) não é coluna vazia: não é auditável **nem populável**; **(3) keeper sem `sleeper_player_id` não é divergência, é limite de insumo** — vira aviso e **bloqueia por auditoria incompleta**, porque cair para nome está proibido ("Brown"). Mais: **budget divergente NÃO virou classe** (é consequência das classes 1-4; vira-lo achado produziria a 4ª divergência que a fixture B proíbe), a **ressalva das 22 rodadas virou verificação automática** pelo lado da sala, e o **timeout do D1 já existia** (`_get`, `timeout=15`; id morto → erro em **0,21 s**). **Fixtures:** **A** = board real (24 designações, $148/$95/$60, **dois DEF de id-sigla**) × sheet espelho → **0 divergências / 3 populados / 9 não populados**; **B** = A + **3 erros plantados** → **exatamente 3 achados, um por classe** (o cruzamento de time conta **UMA** vez — contá-lo duas daria a 4ª). ⚠️ **A B não cobre a classe 1** (os 3 erros pedidos são das classes 2/3/4) → fixture **C** dirigida, senão a classe **mais grave** ficaria sem teste; +2 dirigidas (coluna sem owner; keeper sem sid, **com dois Brown**). **Achado da geração da fixture:** os 24 do board estavam **espalhados pelos elencos reais** dos outros times → a fixture "coerente" acusava **18 falsos `time_errado`**; **o erro era da fixture** — a auditoria estava certa, o jogador **estava** em dois times. **Validação:** 29/29 novos + **48/48 do `salary_engine` intactos**; **board REAL atravessando o núcleo** (`draft_id` derivado, 24 designações `pre_draft`, `rounds=22` **lido do draft**, **3 colunas sem owner**) → 0 divergências, 3 `sem_coluna`, 3 órfãs; **sem sheet a auditoria DIZ isso** e devolve 0 times (não 12 falsos positivos); **`draft_id` não persistido** (grep); board intacto, draft não iniciado, só `GET`. **Cobertura do D6:** de manhã **4** times sem coluna, à tarde **3** — `fertorquato` entrou entre as duas leituras da MESMA sessão; **terceira leitura, terceira contagem**. `git diff` não toca `salary_engine`, schema de cortes, sync nem a keeper sheet.)
> Atualizado em: 03/08/2026-pt4 (sessão MAN-OFF26-4-OWNERCHECK: **verificação read-only da costura de owner — a última incógnita do D6 do [[OFF26-4]] foi exercitada com owners reais e CASOU 8/8, zero não-casamentos.** Zero escrita dos dois lados (API só `GET`, `dynasty.db` em `mode=ro`), draft **não iniciado**, board **intacto**, scripts transitórios não commitados. **⚠️ Estado esperado divergiu:** o prompt esperava **7 aceites**, a API expôs **8** — `LeoFBorges1` (roster 8) entrou entre a leitura de tela do owner e a leitura da API; benigna e na direção boa, mas registrada — **a contagem de aceites muda entre uma olhada e a seguinte; a F2 lê, não assume**. **O casamento não depende do banco local:** os 12 `sleeper_owner_id` do Manager são **idênticos** aos 12 `user_id` da liga real lidos ao vivo (`manager − real = ∅` e vice-versa) e os 8 da fantasma são **subconjunto** disso → confirma a propriedade que sustenta o D6: **`owner_id` é identidade de CONTA do Sleeper, não de time nem de liga**. **🔲 D6 SEGUE ABERTO — mecanismo confirmado, cobertura não:** 4 rosters (9–12) com `owner_id` nulo, que **nenhuma leitura resolve** (dependem de aceite); times do Manager ainda fora: **#2 3 peat…** (`fertorquato`), **#7 AlexTheDawg** (`freddupont`), **#8 Trust The Process** (`michelzela`), **#10 achane** (`gabrieldiinis`) — pelo achado "keeper fora do board é leiloável" esses 4 **já são bloqueantes de abertura por outro motivo**, a costura não é o gargalo. Registrado também que **coluna sem owner não é atribuível a time nenhum** (distinto de "time não populado" do D4) — o caso **existe e foi observado**; onde ele cai nas classes do D5 é da F2. **📌 REFORÇO DA JUSTIFICATIVA — a regra NÃO muda:** "casar só por `sleeper_owner_id`, nunca por nome" passa a ter **dois motivos independentes** — **(1) instabilidade no tempo** (`Team.name` mutado pelo sync), com **evidência nova**: o Manager guarda `Tropa do Bicampeonato 🏆` e a liga real **hoje** exibe `Tropa do Jarra 🏆`, o nome **já divergiu sozinho**; **(2) espaços de nome SEPARADOS** (novo, mais fundamental) — nada vincula o nome da fantasma ao da real, ele pode **nascer diferente e permanecer diferente para sempre**, sem mutação: **são dois namespaces**, casá-los é **erro de categoria**, não de atualização. **Evidência de campo medida:** `metadata.team_name` é **`None` nos 8 owners da fantasma (8/8)** → enquanto ninguém batiza o time a coluna exibe **username**, e durante boa parte da preparação **não existe nome de time para casar**; **dois Rafas** (`rafadgil`/`rafaelferreirap`) → colisão por nome é risco **concreto**; e **`rafaelferreirap` não tem `team_name` nem na liga real** → o Manager guarda o **username** como `Team.name` (#11), então um cruzamento por nome acertaria **por coincidência de fallback** — o pior tipo de acerto, porque **valida a técnica errada**. Nota anexada ao `probe_liga_fantasma.md` (o bloco `[P4]` vira **medição de cobertura**: quantos owners ainda faltam). Nenhum status alterado; Status Rápido intocado; sem código.)
> Atualizado em: 03/08/2026-pt3 (sessão MAN-OFF26-4-REFINE-PT2: **absorção dos achados do probe + o achado de maior peso do arco OFF26**. ⛔ **KEEPER FORA DO BOARD É JOGADOR LEILOÁVEL** — para o Sleeper ele é **disponível**; qualquer owner pode nomeá-lo e **o leilão processa o lance normalmente**, porque a plataforma **não sabe** que ele tem contrato vigente. Resultado: **jogador com dono arrematado por outro time AO VIVO**, e o [[OFF26-3]] ingerindo depois como aquisição legítima. **Não é erro de contabilidade que a auditoria corrige depois — é transação inválida em tempo real, sem desfazer limpo sem interromper o leilão.** → **o [[OFF26-4]] deixa de ser conferência de cap e vira GATE DE INTEGRIDADE DO LEILÃO**; a classe "keeper ausente do board" **não é divergência de transcrição** e sua severidade **deixa de ser escolha da F2** (é bloqueante). **Propagado ao [[OFF26-10]]** (times bloqueados pelo teto ficam com **todos os keepers expostos** até o late drop → **população completa do board é PRÉ-CONDIÇÃO DE ABERTURA**, não preparativo; a decisão em aberto do item **segue em aberto** — é registro de consequência) e ao [[OFF26-5]] + runbook (**board incompleto NÃO é estado aceitável**, nova §B.5). **IR RESOLVIDO (owner):** a fantasma não tem slot de IR → **designar o keeper em IR normalmente**, excedentes caem no **banco**, vaga automática por posição — sai do pool, consome budget, fica visível à auditoria. **Alternativa descartada:** descontar o valor do budget do time — **não resolve o risco** (o problema é disponibilidade, não dinheiro) e ficaria **invisível à auditoria**. **D2:** metade da ressalva **fechada** (sala = **22 slots**), metade do **regulamento 8.3.4 pendente**, agora com o **caso concreto do IR**; +aritmética nova a conferir (nenhum time pode exceder **22 keepers**). **🔧 D1 corrigido, texto anterior preservado:** a "falha silenciosa" **não existe pela porta da auditoria** (404 em 0,2 s; o LOADING é do **app web**) → **timeout rebaixado de mitigação de risco a boa prática**; **a proibição de persistir `draft_id` permanece intacta** e a derivação está comprovada por **1 requisição**. **D5:** classe "slot errado" **não existe** (vaga não é auditável **e não precisa ser** — atribuição automática por posição). **D6 afrouxado com precisão:** `owner_id` nulo em 11/12 **não bloqueia** — designações vêm por **`roster_id`** → **construção e validação parcial LIBERADAS contra placeholders**; só a **costura final `roster_id` ↔ time do Manager** espera os aceites. **Armadilhas p/ a F2:** `player_id` de **DEF é sigla** (`"LAR"`) e **`draft_rounds` da liga ≠ `rounds` do draft** (ler o do draft). **Nota de método — 3ª premissa da mesma família na sessão:** observação verdadeira, **procedência errada** (sigla/lista de teste · reserva de $1/só-Manager · LOADING/app-web) → **comportamento observado numa superfície não vale como propriedade de outra**. Status de OFF26-4/10/5 inalterados; Status Rápido intocado; sem código.)
> Atualizado em: 03/08/2026-pt2 (sessão MAN-OFF26-4-PROBE: **probe read-only executado contra a liga fantasma real — o bloqueador do §2 da F1 do [[OFF26-4]] CAIU**. Zero escrita, draft **não iniciado**, board **intacto**; scripts transitórios não commitados. **P1 ✅ a derivação `league_id → draft_id` funciona, e por DOIS caminhos** — `GET /league/{lid}` **já traz `draft_id` no topo** (1 request) e `/league/{lid}/drafts` devolve **1 draft, o vigente**; **o morto não aparece na lista**. **⛔ Premissa do D1 REFUTADA para a API:** o draft morto dá **404 + `null` em 0,2 s**, não trava — o "LOADING infinito" é do **app web**; pela porta que a auditoria usa **esse modo de falha não existe** (o essencial do D1 — **não persistir `draft_id`** — segue de pé). **P2/P3 ✅ designações EXPOSTAS pré-draft** em `GET /draft/{did}/picks` com `status: pre_draft` — **a MESMA superfície que o projeto já usa**: 24 registros, com **`metadata.amount` (string)**. **Os três totais foram RECONSTRUÍDOS do payload, exatos: $148 / $95 / $60**, e o Team 3 confere 10/10 nominalmente (inclusive **Waddle=DEN vindo do próprio Sleeper**, o que reforça que a divergência de sigla da 2ª execução era **da lista de teste** — ver [[OFF26-5]]). **P4:** jogador por **`player_id` = `sleeper_player_id`** ⚠️ **exceto DEF, que vem como sigla (`"LAR"`)** — coerção a `int` quebra; time por **`roster_id`**; `picked_by` vazio nas 24; **`owner_id` NULO em 11/12 rosters** → **D6 confirmado como bloqueio de VALIDAÇÃO**, mas **a auditoria não precisa de owner para casar** (a designação já vem chaveada por roster). **P5:** ❌ **não existe campo de budget por time** — só `draft.settings.budget=200` global → budget **derivável só por soma**, como o D2 já mandava. **P6:** **réplica dupla confirmada** — `draft_import.py:39` e `sync_sleeper.py:872` leem picks e **replicam a coerção de `amount`** (`float` × `int`), **ambos gateados em `status=="complete"`** — **é o gate, não a API, que impedia ler pré-draft**; a auditoria seria a **3ª réplica** (candidata a helper único, espírito do [[F10]]). **Achados não previstos:** **`is_keeper: false` nas 24** (o indício do [[OFF26-11]] ganha **evidência de payload pré-draft**; a confirmação pós-draft segue pendente); **`pick_no`/`round` NÃO indicam vaga de roster** → **não existe classe "slot errado" auditável, o D5 precisa de ajuste** (presença/valor/time sim, vaga não); **`roster_positions` = 22 slots (10 titulares + 12 BN)** → lado Sleeper da **ressalva do D2 agora medido**, falta o lado do regulamento; **⚠️ a fantasma NÃO tem slot de IR** e a liga real tem (o D5 do [[OFF26-2]] conta IR no budget) — divergência **concreta**, não hipotética, dentro da mesma ressalva; **`league.settings.draft_rounds=3` × `draft.settings.rounds=22`** (ler o do **draft**); **`copy_from_league_id`** = a fantasma foi criada **por cópia da liga real**. Status do OFF26-4 segue 🔲; Status Rápido intocado; sem código.)
> Atualizado em: 03/08/2026 (sessão MAN-OFF26-4-REFINE: **spec do [[OFF26-4]] sincronizada com a evidência de 02/08** — bloco **"Spec final — decisões de produto arbitradas"** (padrão do [[OFF26-2]]) com **D1–D7**, cada uma rotulada por natureza. **F1 e ATUALIZAÇÃO EMPÍRICA intactas abaixo, como terreno**; status segue **🔲** (a spec não é implementação). **Natureza que decide o D1:** a auditoria é gate que **roda 3× ou mais** numa janela de 48 h (após a 1ª leva de 20/08, após o remendo do late drop de 22/08, e final antes de 24/08). **D1 (arbitrada):** `league_id` em **`AppConfig`** — descartadas coluna em `Team` (é atributo de liga) e parâmetro por chamada (**recolar o id a cada execução sob prazo é oportunidade recorrente de colar o errado**); ⛔ **persiste-se APENAS o `league_id`** — o `draft_id` **muda a cada reset** e é **derivado a cada uso**, com **timeout explícito e mensagem própria** porque a URL morta **trava em LOADING** (falha indistinguível de lentidão); 🔲 a F2 **herda** a pendência de que `league_id → draft_id` **nunca foi exercitado contra a fantasma**. **D2 (resolvida por evidência):** base = **`usable_draft_budget`**, não `raw_budget` — o §5 da F1 está refutado; ⚠️ **ressalva aritmética pendente** (Sleeper reserva sobre **22 rodadas**, a 8.3.4 conta pelo **regulamento** — se divergirem, os limites não coincidem). **D3 (delegada com critério):** `sleeper_player_id` no payload × re-query fica com a F2, **preferindo o caminho que não toque o [[OFF26-2]]** (⚠️ aguardando smoke); invariante: identidade **só por `sleeper_id`**, nunca por nome ("Brown"). **D4:** relatório dos **12 de uma vez**, com **time não populado como ESTADO PRÓPRIO**, distinto de "keeper ausente" — não populado por regra ([[OFF26-10]]) **não é divergência de transcrição**. **D5:** 4 classes de divergência + 1 estado; severidade fica com a F2. **D6:** ponte **só** por `sleeper_owner_id`, reusando o helper existente; ⛔ **terreno não verificado** — convites disparados em **03/08**, times **ainda placeholders com `owner_id` nulo** → **a F2 não pode ser validada contra board de placeholders**. **D7 (pré-condição, não passo da F2):** o probe do §2 exige board populado — **janela ABERTA agora** (Team 3/4/5), **fecha no próximo reset**. Sem código; Status Rápido intocado; nada do OFF26-2 alterado.)
> Atualizado em: 02/08/2026-pt12 (sessão MAN-OFF26-RUNBOOK-REG-PT2: **2ª execução do Cowork** — runbook corrigido **VALIDADO** (Team 3 = 10 keepers/$148, Team 4 = 8/$95, Team 5 = 6/$60, totais conferindo, **sem redescoberta de caminho**). **Achado de maior alcance: o `draft_id` NÃO é estável** — o RESET DRAFT gerou draft novo e **matou no mesmo dia** o id registrado no pt11 (`1389725100684611584` → atual **`1389755381567213568`**; `league_id` `1389725099556372481` **estável**). A morte é **silenciosa**: a URL velha **trava em LOADING**, não dá erro. → **restrição de desenho sobre a decisão 1 do [[OFF26-4]]**: a decisão segue **em aberto**, mas **qualquer alternativa que persista `draft_id` está descartada por evidência** — persiste-se o `league_id` e **deriva-se** o draft a cada uso (caminho `league_id → draft_id` via `/league/{lid}/drafts` **a confirmar**, não assumir). **⛔ FALSO ACHADO rejeitado:** o Cowork recomendou **rebaixar o check anti-homônimo** por divergência de sigla (Waddle=DEN, Hill sem sigla) — **causa era a lista de TESTE**, montada à mão com times de temporadas antigas; na execução real a sheet sai do Manager, que sincroniza do Sleeper, e as siglas batem. **Check mantido inalterado** e **orientação invertida**: divergência de sigla na execução real = **parar e reportar**. **Nota de método:** recomendação vinda de execução com **dados sintéticos** exige conferir a **origem do dado** antes de virar correção — sem isso, uma proteção teria sido enfraquecida na véspera do uso real. **5 correções no runbook** (coluna com placeholders = menu de contexto; board **reescala**; vaga atribuída **por posição**; preço nasce **$1 sempre**, mesmo com `$PROJ` maior; filtro K/DEF **esconde já-designados**) + **não fixar URL de board**. **Melhoria do [[OFF26-2]] com evidência de campo:** ordenar a sheet **na sequência do board**, marcando os keepers de $1 (6 de 24 dispensaram edição) — registrada, **não implementada**. **⚠️ Medição perdida:** 58min26s para 3 times, dominados por **dezenas de timeouts de 30 s**; risco de **variância de ambiente sem causa identificada** (~2 h × ~5 h, imprevisível) → mitigação: **fatiar por time**, unidade verificável. **Decisão Cowork-2026 mantida**, com **reconsideração parcial aberta** (o argumento novo do script é **variância**, não duração; contra-argumentos preservados: seletores frágeis, competição de prazo com OFF26-4/11, estreia no dia do uso). **Board populado agora** = janela aberta p/ o probe pré-draft **antes do próximo reset** (que trocará o `draft_id` de novo). Sem código; nenhum status alterado; Status Rápido intocado.)
> Atualizado em: 02/08/2026-pt11 (sessão MAN-OFF26-IDS-REG: **fecha as 2 pendências abertas no pt10** sobre a liga fantasma **Dynasty SB FA Auction**. **(1) Identificadores registrados** — `league_id` = **`1389725099556372481`**, `draft_id` = **`1389725100684611584`**, lidos das URLs da página da liga e do draft board. Os dois são **distintos e não deriváveis um do outro por inspeção**, o que **reforça o precedente do `draft_import.py`** citado no §1 da F1 do [[OFF26-4]]: passa-se o `draft_id` e **deriva-se** o `league_id` do objeto do draft. Registrados como **DADO, deliberadamente NÃO persistidos** em constante/`AppConfig`/coluna — as opções (a)/(b)/(c) do §1 **seguem abertas**; ter o número não escolhe onde ele mora. **(2) RESET DRAFT executado — board VAZIO**, os 2 times da validação removidos (**estado daquele momento: o board foi repopulado na 2ª execução e este `draft_id` morreu no reset — ver pt12 acima**). **Consequência registrada como PRÉ-CONDIÇÃO, não detalhe:** o reset **apagou o alvo empírico** dos probes pendentes — o do §2 da F1 do [[OFF26-4]] (o que a API expõe **pré-draft**) e a confirmação **pós-draft** do indício `is_keeper:false` do [[OFF26-11]] **exigem repopular o board antes de rodar**, para que isso não seja descoberto no meio da diagnose. Nenhum status alterado, Status Rápido intocado, sem código.)
> Atualizado em: 02/08/2026-pt10 (sessão MAN-OFF26-10-11-REG, 2ª parte: **achados empíricos da liga fantasma** — a sala foi **criada de fato** (**Dynasty SB FA Auction**: Redraft, 12 times, Auction, budget $200, 22 rodadas, 3 WR; 2 times populados, RESET DRAFT e ids pendentes **naquele momento — ambos resolvidos no pt11 abaixo**) e submetida a experimento manual. **§5 da F1 do [[OFF26-4]] REFUTADO:** a reserva de **$1 por vaga não é regra só do Manager — o Sleeper aplica a mesma**. Fórmula confirmada `teto = 200 − gasto − (vagas_restantes − 1)`: time com $150 e 21 vagas → teto **$29** ($40/$33/$32 recusados com *"The specified slot does not have enough budget."*, **$29 aceito**; sem falso positivo — 10 keepers de $140 passaram calados). → base de comparação correta é **`usable_draft_budget`**, não `raw_budget`; **decisão de produto 2 do OFF26-4 = RESOLVIDA POR EVIDÊNCIA**. Ressalva pendente (aritmética, não experimento): o Sleeper reserva sobre as **22 rodadas**, a regra 8.3.4 conta slots pelo **regulamento** — se divergirem, os limites não coincidem. **[[OFF26-10]]:** a suspeita virou **fato** — time acima do teto **não entra no board**, logo a **população escalonada é OBRIGATÓRIA** (enquadrados em 20/08, estourados só após o late drop de 22/08); o Manager pode **pré-calcular os bloqueados**. **[[OFF26-11]]:** **indício forte** (não fato) — a designação carrega **`is_keeper: false`** e a UI toca som de lance vencedor → o Sleeper trata keeper como **pick forçado de leilão**; se confirmado **pós-draft** (ainda não observado), o discriminador terá de ser a keeper sheet como **lista de exclusão**. **Runbook [[OFF26-5]] corrigido (status ✅ mantido): o caminho da Fase B NÃO EXISTE** — o board já está em modo de designação (clicar direto na célula); +7 correções ("+" da linha nunca o nome, K/DEF abaixo da dobra via seta ▼, filtro de posição p/ K/DEF, preço já vem $1, Ctrl+A rebaixado a nota, homônimo suavizado — pool só de ofensivos elegíveis, nome da liga) + seção nova do teto de lance. **Esforço MEDIDO:** 1 time/10 keepers = **20min32s** (~9 min de overhead único) → **~75 s/jogador ≈ 2,5 h p/ 12 times** (vs. uma tarde inteira manual). **Decisão:** 2026 via **Cowork**; **script determinístico = melhoria p/ 2027** (o argumento da janela de 48 h **cai**); **API interna descartada** (sem contrato, provável violação de ToS, expõe a conta de comissário). Sem código.)
> Atualizado em: 02/08/2026-pt9 (sessão MAN-OFF26-10-11-REG: **registro docs-only** — calendário real da intertemporada 2026 fixado com o comissário (**17/08** rookie draft · **18/08** congelamento ESPN · **20/08** cortes · **22/08 late drop** (máx. 1 jogador/time) · **24/08** FA auction) expôs **2 gaps inéditos**, ambos 🔲 Alta. **OFF26-10** — o late drop altera os keepers **dois dias depois do lock** da janela selada, e sheet/budget/board derivam do snapshot: a sheet de 20/08 é **provisória** p/ quem fechou acima do cap. Registrados como **questão empírica (probe, não fato)**: o Sleeper pode **recusar** designação de keepers acima do budget (então a população do board teria de ser **fatiada por time**), e a **assimetria de limite** (Sleeper só conhece o budget global; a regra da liga reserva $1/slot vazio → passa lá, ilegal aqui). **Decisão em aberto:** 2ª mini-janela selada × correção administrativa pós-lock. **OFF26-11** — keepers **precisam** estar no board (o cap emerge do budget consumido), logo os picks virão **misturados**; o importador [[OFF26-3]] escreve pela porta de **contrato ano 1** → ingerir keeper **zera a idade do contrato** (dano silencioso, visível só na renovação; caso canônico: $50 dropado e recomprado por $50 — valor igual, natureza diferente). Probe pendente: os picks vêm marcados, ou o discriminador sai da keeper sheet como lista de exclusão? **Decisão em aberto:** importar só arremates × reconciliar e reportar divergência. **EMENDA de premissa:** o **rookie draft NÃO roda em liga fantasma** — a frase do registro do pacote (05/06) colou as duas salas sem justificar o rookie draft item a item; o [[OFF26-3]] foi validado contra o **rookie draft real de 2025** (chain da liga real) e todo o arco [[S2]]/[[S3]] trata do **board de R1 2026 da liga real**. O motivo da sala separada da **FA auction** permanece válido e é outro (dynasty com rosters cheios × auction que pressupõe rosters vazios). **Existe UMA liga fantasma permanente, não duas.** Texto histórico preservado verbatim + bloco EMENDA anexo (precedente [[DP1]]); título da seção e descrição do [[OFF26-7]] ajustados; `CLAUDE.md` sincronizado. Sem código; nenhum item existente teve status alterado.)
> Atualizado em: 02/08/2026-pt8 (sessão MAN-S2-DONE: **S2 ✅** — smoke em produção aprovado sobre o hash **`9b4bcf1`** (gate [[PROC1]]; backup `/data/dynasty_pre_s2_smoke_2026-08-02.db`): desconto armado para 2026 via `/admin` → sync rodado → **as 4 posições divergentes convergiram para o alvo da F1b** — pos. **2 = Fazenda Pederasta sem troca**, pos. **5 = 3 peat → Cangaceiros** (**re-rótulo da trade de 29/07 confirmado em prod**), pos. 3 e 4 com donas originais corretas; **cruzamento com o board do Sleeper confere** (`1.05` via `fernandoxmf` visível no roster MellowBR); **2ª execução do sync sem nenhuma alteração** (idempotência confirmada **em produção**); verify do lottery 2026 conferindo; pos. 1 e 6–12, R2/R3 e seasons futuras **intactos**. O alvo era, desde a derivação da F1b, "o que o board já exibia" — e é o que o Manager agora exibe. **Estado operacional:** sync liberado com o desconto **armado para 2026**; desarme no rollover **por construção** (armamento por season). **Migração O3:** seção detalhada do S2 (REG + F1a + F1b + F2 + smoke) movida **verbatim** para `improvements_archive.md`. **Fatia F2-3 desmembrada como [[S5]] 🔲** (tela que prescreve a permutação ao co-admin) para não se perder na migração — não iniciada, não bloqueia. Sem código.)
> Atualizado em: 02/08/2026-pt7 (sessão MAN-S2-F2: **código** — desconto determinístico da permutação administrativa. Novo **`board_mirror.py`**: π = S⁻¹∘L derivado das fontes canônicas (`DraftLotteryResult` × `_build_default_draft_order`, a mesma fonte única do M15/M16), **sem tabela hardcoded**, e **exige bijeção** — board meio-montado desliga o desconto em vez de corromper em silêncio. **Armamento guarda a SEASON, não um booleano** (decisão do Code): o **rollover desarma sozinho**, porque `draft_season` muda e o valor guardado deixa de casar — um booleano dispararia o desconto no ano seguinte sobre board não-montado. 2º gate: audit canônica de lottery. **Toggle explícito, não detecção automática** — a montagem não deixa rastro, e montagem parcial + desconto ligado = corrupção silenciosa. Ligado em `_resolve_traded_pick_identity` (a costura que o [[S3]] deixou pronta) **e**, por extensão deliberada, no **loop de picks do `_sync_trades`** — sem isso o passo 12 sobrescreveria com rótulo errado o que o passo 11 gravou certo, para trades reais fechadas na janela. Card mínimo de armar/desarmar no `/admin` (não é a tela prescritiva da F2-3). **F2-1 respondida: rota corretiva é REDUNDANTE** — as 4 entradas re-chaveadas formam **bijeção** sobre exatamente as 4 linhas divergentes, então o próprio sync as reescreve; implementar a rota seria código morto. **24/24 em cópia**: desarmado byte-equivalente, armado → **as 12 posições batem com o alvo da F1b**, idempotente na 2ª execução, 96 linhas fora do R1 2026 intocadas, trade real na janela move só a posição negociada, 3 gates, **M8 verify match+hash antes e depois**, `/admin` render+endpoint; 48/48. **Premissa do prompt contradita**: o critério "posição 2 → Cangaceiros" contradiz a tabela-alvo da própria F1b — o alvo é **pos. 2 → Fazenda** e **pos. 5 → Cangaceiros**; "Cangaceiros na 2" é o estado permutado atual, não o alvo. **✅ só após smoke prod (PROC1)**.)
> Atualizado em: 02/08/2026-pt6 (sessão MAN-S3-DONE: **S3 ✅** — smoke em produção aprovado sobre o hash **`89dc08d`** (gate [[PROC1]] cumprido: hash live no Render confirmado pelo owner; backup `/data/dynasty_pre_s3_smoke_2026-08-02.db`): `/picks` com **12 linhas por temporada e 108 picks**, `/league` com contagens corretas por time, **verify do lottery 2026 conferindo** (a migração do join para `team_id` não tocou a auditoria do [[M8]]), valores dynasty de picks resolvendo no `/trades`. **O caso concreto passou limpo:** o owner **religou o sync** e a **primeira execução real ingeriu o rename do time 9 ("Tropa do Jarra") sem duplicação**, com projeção **#11** preservada e display atualizado — o rename que criaria 9 picks duplicadas foi absorvido sem incidente. **Suspensão do sync ENCERRADA**; a diretriz na seção do [[S2]] foi atualizada (o bloqueio era do S3). **Migração O3:** seção detalhada do S3 movida **verbatim** para `improvements_archive.md` com nota de fechamento; Status Rápido mantém a linha como ✅. **[[S2]] segue 🔲** — posições **2–5 do R1 2026 permanecem no estado permutado** até o S2-F2, esperado e documentado. Sem código.)
> Atualizado em: 02/08/2026-pt5 (sessão MAN-S3-F2: **código** — picks casadas por **chave estável**, nome vira display. Desenho (A) da F1 em 4 pontos, **sem schema e sem migração** (os ids já existiam e já estavam corretos em 100% das linhas): (1) `_ensure_default_picks` indexa por `(season, round, original_team_id)`; (2) `_sync_traded_picks` casa por `original_team_id` — cópia literal do padrão de `_sync_trades:670`; (3) join da projeção migra para `team_id` (`_build_default_draft_order` passa a devolver `(pick_number, team_id, team_name)`; novo `_resolve_tid` cai no nome só em linha legada com id NULL) — **contrato do [[M8]] intacto por construção**: `_build_lottery_pool`/`_build_fixed_picks` não foram tocados e nenhum `team_name` de lottery/standings é reescrito; (4) `_refresh_pick_team_names` como passo 11b do `run_sync`, idempotente. **Ponto de costura do [[S2]]-F2 criado e documentado**: `_resolve_traded_pick_identity` (porta única `/traded_picks` → `Team` original/dono) — o S3 responde *como* se acha a pick, o desconto responderá *qual* pick é essa, entrando ali sobre id e nunca sobre string. **Validação 25/25 sobre cópia, sem rede** (harness sem `app.py`, que dispararia `run_sync()` real por causa do CSV local): regressão **byte-equivalente**, rename ingerido → **108 picks / 0 duplicatas** / time 9 com 9 e projeção #11 preservada, League Hub com contagens **idênticas à baseline**, dynasty por `DP_` sem fallback, grid e `/api/picks` OK, **M8 verify match+hash antes e depois**; `salary_engine_test` 48/48. Duas asserções minhas caíram e foram corrigidas (não existe invariante "≤12 picks por time" — Cangaceiros tem 16 e tinha 16 na baseline; o 17 da F1 era o valor inflado). **✅ só após smoke prod (PROC1); o sync permanece suspenso** — religar é decisão do owner. Sequência: **S3 smoke → sync liberado → S2-F2**.)
> Atualizado em: 02/08/2026-pt4 (sessão MAN-S4-REG: **registro docs-only** — novo item **S4** (🔲, Média): `PlayerHistory` e `Trade` identificam time **só por nome**, sem chave estável no schema. O `team_name` participa do **índice UNIQUE de dedupe** do [[F8]]a (`app.py:361`: `player_id, season, event_type, team_name, sleeper_event_ref`) e é gravado do nome vivo (`models.py:232,237`) → após um rename de time, o mesmo evento **não colide** com a linha antiga e a **idempotência do histórico cai**. Segunda superfície: `Trade.team_a/team_b` são strings e `roster.py:245-250` resolve a contraparte comparando com o `team_name` da `PlayerHistory` → pós-rename o timeline do jogador perde a contraparte. **Distinção do [[S3]]**: lá a chave estável **já existia e já estava correta** (fix sem schema, nada a migrar); aqui **não existe** — exige coluna nova, migração de 1.151 linhas de histórico + 53 de `Trade`, e mexer no UNIQUE do F8a (a garantia de idempotência do rebuild). **Não bloqueia** S2 nem S3; o gatilho é o mesmo rename pendente do time 9. Sem código, sem dado; nenhum item existente alterado além da linha no Status Rápido e do cross-ref na questão aberta do S3.)
> Atualizado em: 02/08/2026-pt3 (sessão MAN-S3-F1: **diagnose read-only ✅** — duplicação **reproduzida com o código real sobre cópia** (Flask mínimo apontando p/ `s3_sim.db`; **não** importa `app.py`, que dispararia `run_sync()` de verdade porque o CSV existe local). Resultado: **+9 picks** (3 seasons × 3 rounds) e **só `_ensure_default_picks` duplica** — roda antes (`:331`) e cria as linhas com o nome novo, que o `_sync_traded_picks` então acha e só atualiza → **dano 9, não 18** (corrige a F1b). Estado resultante é o pior dos dois mundos: linhas velhas guardam a projeção mas congelam a titularidade; linhas novas recebem a titularidade certa e **perdem a projeção**. Efeitos medidos: time renomeado **sem projeção** (fallback 999, desce no grid e aparece 2×), **League Hub inflado em 7 de 12 times** (Cangaceiros 9→17), valor dynasty caindo no fallback `FP_` ([[T2-FIX]]). **Sem mudança de schema**: `Pick.original_team_id` já existe e **nasce correto até nas duplicatas** (18 linhas com id=9) — e `_sync_trades:670` **já casa por id**, precedente canônico no mesmo arquivo. **Restrição forçada descoberta**: cascatear o rename para os nomes não fecha (a projeção casa `Pick` × `DraftLotteryResult` × `SeasonStandings` por string) e refrescar `DraftLotteryResult.team_name` **quebraria o verify do [[M8]]** → o join **tem** de migrar para `team_id`. Na fronteira de picks o **Sleeper nunca manda nome** (`/traded_picks` só tem `roster_id`/`owner_id`) — a string é auto-infligida. **Classe maior que picks**: `PlayerHistory` (`team_name` dentro do índice UNIQUE de dedupe do [[F8]]a) e `Trade` (`team_a`/`team_b`) **não têm chave estável nenhuma** → escopo separado. **F2: desenho (A)** — match por id nos 4 pontos, nome vira display derivado, **nada a migrar**; ponto de costura explícito p/ o [[S2]]-F2 se plugar. Sequência: **S3-F2 → sync liberado → S2-F2**.)
> Atualizado em: 02/08/2026-pt2 (sessão MAN-S2-F1b: **diagnose analítica ✅** — read-only, zero escrita. **Mecanismo formalizado e provado nas 12 posições:** o Manager exibe **O(L(π(p)))** com **π = S⁻¹∘L** (S = board do Sleeper/standings invertido, L = lottery); π é um **4-ciclo puro em {2,3,4,5}** e as outras 8 posições são **imunes por construção** (lottery não moveu 1º nem 6º; 7–12 são fixas nos dois modelos) → teto de dano = nº de seeds deslocadas, **nunca 12**. **Correção da F1a: são 4 posições divergentes, não 3** — a pos. 2 passou por comparar contra um canônico que ainda tinha o rótulo errado da trade de 29/07. **Estado-alvo derivado** (com re-rótulo: o ativo é a pick da 3 peat, não a da Fazenda) e **verificado 12/12 contra a leitura direta do board** — o Sleeper já exibe a ordem certa; o Manager é que a re-permuta. **Fonte única × réplica:** a *posição* tem fonte única (`_build_pick_projections`, sem réplica JS); o *dono* é lido cru em ≥4 sítios; **"dono-na-posição" não existe como objeto** — é join no template. **"Não fazer a montagem" não é opção**: editar `draft_order` vazaria o lottery para R2/R3 e quebraria o [[M16]] — a permutação de picks é a técnica correta e vai se repetir todo ano. **Recomendação F2: desenho (b) — desconto determinístico** (re-chavear `/traded_picks` por `L(S⁻¹(x))` torna os 3 movimentos administrativos **no-ops** e re-rotula a trade real sozinha), em 3 fatias: corretiva auditável + desconto escopado a R1 da draft season + **tela que prescreve a permutação** (sem ela o desconto é heurística). (a) rejeitado (conserta a tela, deixa o dado errado p/ os ≥4 leitores diretos); (c) rejeitado (schema + disciplina anual por menos). [[OFF26-3]] é **indiferente** aos três (lê `roster_id` do draft real). **Novo item [[S3]] 🔲 Alta — BLOQUEIA o retorno do sync**: rename de time quebra o match de picks por string e o próximo sync cria duplicatas; time 9 já renomeado no Sleeper, ainda não ingerido. Ordem obrigatória: **S3 → sync → S2-F2**.)
> Atualizado em: 02/08/2026 (sessão MAN-S2-F1a: **levantamento read-only ✅** — retrato do estado, zero escrita. **Premissa central do S2 REFUTADA:** as trocas administrativas **não são transações** (ferramenta de comissário) → `_sync_trades` nunca as viu; a porta é **`_sync_traded_picks`** (`sync_sleeper.py:407`), que reescreve o dono de toda pick de `/traded_picks` **em todo sync**, sem `Trade`, sem `PlayerHistory`, sem trilha. **Não existe trade só-picks em lugar nenhum da chain** (1.123 tx, 53 trades; as 6 de 2026 têm jogadores). **4 movimentos administrativos**, todos em **R1 2026** (1 mascarado por trade posterior), datados em **08/06/2026** pela série `sync_log.picks_updated` (18→**21**→32, aritmética fecha) — ~7 semanas antes do draft, não na véspera. **Intenção confirmada 12/12 slots**: a montagem faz o board do Sleeper (ordem = standings 2025 invertido, conferida em `slot_to_roster_id`) exibir a mesma sequência de donos que a ordem do lottery ([[M16]]) — tradução correta entre modelos incompatíveis, não erro do co-admin. **Dano hoje: 3 de 12 posições do R1 2026** (pos. 3/4/5); R2/R3/2027/2028 intactos; **0** `Trade`, **0** `PlayerHistory`, **0** divergência Manager × Sleeper → **nenhuma correção manual sobreviveu**. Pick 2 = pick da Fazenda Pederasta (`fernandoxmf`) — bate com o sintoma, pendente o owner confirmar "Fehl"=`fernandoxmf`. **Complicação p/ o fix:** a trade real de 29/07 foi registrada sobre a ficção → exige **re-rotulagem**, não só desfazer. Ressalva: base auditada = snapshot de prod do commit `326324a` (31/07), **não** `/data/dynasty.db` (Render Shell indisponível). Colateral: `_sync_traded_picks` casa pick por **string** de nome de time e o time 9 foi renomeado no Sleeper → risco de linha duplicada, candidato a item próprio.)
> Atualizado em: 01/08/2026 (sessão MAN-S2-REG: **registro docs-only** — novo item **S2** (🔲, Alta): o sync de trades ([[S1]]) ingeriu como trades reais as **trocas administrativas de picks** que o co-admin criou na UI do Sleeper só para montar a ordem do rookie draft 2026 (o Sleeper suporta uma ordem única para todos os rounds; o Manager já modela R1 = lottery e R2/R3 = standings invertido — [[M16]]). Sintoma em prod no rookie draft de 28/07: pick 2 do R1 2026 constava do time do Icaro, mas é do Fehl (Sleeper é a referência correta). **Risco de recorrência anual** — toda montagem de ordem de draft no Sleeper gera essas trocas. Diretriz vigente: **sync suspenso até o fix**. Sem código, sem dado; nenhum item existente alterado além da linha no Status Rápido.)
> Atualizado em: 31/07/2026-pt4 (sessão MAN-F13-CLOSE: **F13 ✅** — smoke prod OK sobre hash `2cd8de3` (backup `/data/pre_f13.db`): recaptura = **287** (145 entraram = os ausentes do cache congelado, 142 atualizados, 6 saíram por corte → desmarcação real), 2ª captura 0/0 **sem novo download** (carimbo por conteúdo operou), board 287 c/ 12 do import ESPN (6 valorados), busca/filtro no navegador. **Migração O3:** F13 → archive com nota de fechamento. **Baixa da ressalva do DP3** anexada no archive (board não mostra mais junho; dos 84 do import, só 12 são da classe). **Pendência**: frescor sobreviver ao 2º deploy → próximo release. Registrados: **F14 🔲** (nomes sem sufixo de geração, cosmético) + **regra no `DEV_METHODOLOGY.md`** (smoke local aponta `DYNASTY_DB` p/ cópia temp, nunca o seed). Sem código.)
> Atualizado em: 31/07/2026-pt3 (sessão MAN-F13-F1/F2: **F13 ⚠️** — cache do pool Sleeper descongelado. **F1:** prod **nem tenta** escrever (branch de download inalcançável por mtime de deploy + checkout-revert repõe junho); dano real > stale — classe viva 287 × 148 no cache, **145 sem sid** no pool de junho, 108/142 com team desatualizado. **F2 (caminho b + d):** cache movido p/ `dirname(DYNASTY_DB)` (volume, padrão E1), `git rm --cached` + removido da árvore (gitignore já cobria), validade por carimbo `fetched_at` **dentro** do arquivo (não mtime), formato antigo/ilegível→vencido sem lançar; sítio único de caminho e de validade; 6 consumidores intactos. Smoke cache 21/21 + e2e captura 287 (não 148) + 48/48. **✅ só após smoke prod.** CLAUDE.md sincronizado.)
> Atualizado em: 31/07/2026-pt2 (sessão MAN-DP3-CLOSE: **DP3 ✅** — smoke em prod OK sobre hash `e12fdef` (PROC1: hash live confirmado no Render; backup `/data/pre_dp3.db`): captura idempotente 148→0, board ordenado (valorados no topo), não-rookies fora, busca/filtro sem reload, cenário na barra fixa. **Migração O3:** seção detalhada movida verbatim p/ `improvements_archive.md` com nota de fechamento; Status Rápido mantém a linha ✅. **Ressalva:** board em prod exibe a classe do snapshot de junho — não é defeito do DP3 (predicado/captura corretos sobre o pool entregue); completude depende do **F13**. **F13 elevado 🔲 Baixa→Alta** com evidência de prod (148×288; TTL nunca vence por mtime renovado a cada deploy sobre arquivo versionado; mesmo loader serve o import ESPN) + janela antes do rookie draft (agosto). Nota de dependência do E4-c-2 atualizada (reescopo desbloqueado). Sem código.)
> Atualizado em: 31/07/2026 (sessão MAN-DP3 REG→F1→REFINE→F2→COMMIT: **DP3 ⚠️** — board de rookies do cap_projector refeito sob D1–D5: classe entrante por **snapshot materializado** (`RookieEspnValue.in_class`, captura admin idempotente por `(sid,season)` na tela do import ESPN, critério único `is_entering_class_member` = `years_exp==0`+skill+`active`+`status='Active'`), board lê membership − rosterados ($1 da fonte única p/ sem-ESPN), tela alt. A (valorados topo + massa atrás de busca/filtro). Smoke local 27/27 + 48/48; **✅ só após smoke prod (PROC1)**. Registrados: **F13 🔲** (versionamento do cache do pool, achado colateral) + nota de reescopo no E4-c-2 + comportamento sazonal da contagem (~288 julho / ~150 pós-corte NFL) + captura como passo 3 da intertemporada no CLAUDE.md.)
> Atualizado em: 23/06/2026-pt3 (sessão MAN-PROC1: **PROC1 ✅** — Forma 1 ancorada: o gate de hash deployado foi afinado no bullet de ✅ da seção "Checklist de fim de sessão" do **`DEV_METHODOLOGY.md`** (transversal manager+optimizer), sem seção paralela. **Migração O3:** seção do PROC1 movida p/ o archive com nota de fechamento. Registrado **PROC2 🔲** (follow-up da ressalva F1: surfacear `RENDER_GIT_COMMIT` no `/admin` — é código). ⚠️ A edição do `DEV_METHODOLOGY.md` (repo umbrella `Fantasy/`, ainda sem commits) fica aplicada no arquivo mas **não commitada** — pertence ao commit inicial do umbrella, do owner.)
> Atualizado em: 23/06/2026-pt2 (sessão MAN-PROC1-REG: **registro de processo** — novo item **PROC1** (🔲): fechamentos com gate de smoke de prod passam a exigir confirmação de que o **hash deployado live** é o commit validado (não basta commitado/pushado). Casos-âncora E1 (✅ prematuro) + E4-a (deploy live era 927831a docs-only, não 97b90ed do filtro). Sem código; nenhum item não relacionado alterado.)
> Atualizado em: 23/06/2026 (sessão MAN-E4a-DONE: **E4-a ✅ + E2-RISK ✅** após smoke prod do import ESPN real (deploy do filtro de posição, commit 97b90ed). **Eixo A fechado** — D/ST só recebem candidato compatível (Broncos D/ST → só Denver Broncos DEF; demais D/ST → "Não Encontrados" limpo, sem skill); **sem regressão** do ramo skill nem dos rookies→store. **Split de prod: 211 matched / 5 aproximados / 84 não encontrados→store / 62 ausentes no PDF.** **Migração O3:** seções detalhadas de E4-a e E2-RISK movidas verbatim p/ `improvements_archive.md` (com nota de fechamento); Status Rápido mantém as linhas como ✅. Sem código.)
> Atualizado em: 17/06/2026-pt8 (sessão MAN-OFF26-9-DONE: **OFF26-9 ✅** — smoke do microcopy do passo 6 (`/offseason`) conferido em prod pós-deploy (texto distingue abertura `needs_review` × recomendação de rollover; lê bem + layout intacto), satisfazendo o critério pendente. **Migração O3:** seção detalhada do OFF26-9 movida verbatim (estado ✅) para `improvements_archive.md`; Status Rápido mantido no ativo. Sem código. OFF26-1/2 seguem ⚠️.)
> Atualizado em: 17/06/2026-pt7 (sessão MAN-OFF26-5: **OFF26-5 ✅ (doc)** — criado o runbook **`runbook_cowork_liga_fantasma.md`** (raiz) a partir do conteúdo-base escrito pelo Cowork pós-PoC, com detalhes operacionais preservados (Ctrl+A no preço, anti-homônimo por sigla NFL, conexão da extensão, anatomia do board, TL;DR). **3 reconciliações** com as decisões do [[OFF26-6]]: (1) roster espelha a liga real — **WR 2→3 obrigatório**; (2) liga **PERMANENTE** + mapa por **`sleeper_owner_id`** (não nome/"Team N"); (3) **setup único × trabalho anual** separados, reset automático (redraft), **gatilho [[OFF26-4]]** ao término. Cross-refs OFF26-2/4/6. Sem código.)
> Atualizado em: 17/06/2026-pt6 (sessão MAN-OFF26-6: **OFF26-6 ✅ (op)** — PoC do Cowork montando a liga fantasma executado em liga de teste descartável (17/06). **Validado:** Cowork cria a liga (wizard 12 times + Auction) e seta keeper com salário sozinho (Draft Settings → SET KEEPERS), conferindo nome+time NFL (anti-homônimo). **Decisões de design:** liga fantasma **PERMANENTE** (redraft fixa, owners reais — placeholders sem dono não são gerenciáveis); reset de roster é automático (redraft), trabalho anual = só popular keepers; config de roster **espelha a real** (3WR etc.); mapa owner↔time por **`sleeper_owner_id`** (não nome). **Achados → [[OFF26-4]]:** cap = budget do auction ($200 global), restante só visível ao vivo → auditoria **calcula** ($200 − Σ keepers), não lê; keepers são designação de board → lê designações, não roster; ponte de owner já resolvida (`Team.sleeper_owner_id`, M12), resta só a ponte de jogador. GATE da FA auction Cowork passou. Sem código.)
> Atualizado em: 17/06/2026-pt5 (sessão MAN-OFF26-9-STATUS: **rebaixado OFF26-9 ✅ → ⚠️**. Revisão de planejamento: o FIX inclui um **artefato de runtime** — o microcopy do passo 6 em `templates/offseason.html`, lido na tela em prod no ponto de decisão que o fix esclarece. Regra "✅ só após smoke prod" aplica: clareza de UI + layout só se verificam na tela renderizada. Pendência p/ ✅: abrir `/offseason` em prod pós-deploy, conferir texto do passo 6 (lê bem + layout intacto). Partes docs-only permanecem aplicadas; microcopy **não** revertido; seção **não** migrada ao archive (O3 só no ✅). Sem mudança de código.)
> Atualizado em: 17/06/2026-pt4 (sessão MAN-OFF26-SMOKE-REG: **registro docs-only** do **smoke PARCIAL em prod** de **OFF26-1/2** (17/06, antes dos passos 3-ESPN/4-Rollover; backup `dynasty_prod_backup_17_06_2026_pre-off26.db` 540K). Validado: deploy live, tabelas `CutDeclaration`/`CutWindowAudit` criadas no schema de prod, tela `/cuts` "Fechada — 0/12" + roster + budget + cap soft, gate `needs_review` zerado, fluxo de 7 passos coerente com a F1. **Não validado (owner optou por não travar):** abertura+cortes reais, lock/reveal+hash, budget definitivo da keeper sheet → **tudo para o [[OFF26-7]]**. **Ambos permanecem ⚠️** — sem ✅.)
> Atualizado em: 17/06/2026-pt3 (sessão MAN-OFF26-9: **OFF26-9 ✅ — correção de redação/microcopy** (sem mudança de lógica). Separado o **timing "pós-rollover"** (qualidade de dado: budget valorizado) da **qualidade de dado "ESPN definitivo (E4-a)"** nos pontos que os fundiram: microcopy do **passo 6** do `offseason.html` (abertura = só `needs_review` zerado; rollover = recomendação), **D8** da OFF26-1 (esclarecimento anexo, decisão intacta), linha "Dependências" + nota do OFF26-7 na OFF26-1, e item 2 das pré-condições de smoke no handoff de fechamento (pt12). Nenhum gate/rota/schema/salary_engine/sync/D1–D11 tocado. Migração O3 (seção → archive) no fechamento.)
> Atualizado em: 17/06/2026-pt2 (sessão MAN-OFF26-PHASE-F1: **diagnose read-only ✅** — suspeita do owner **CONFIRMADA**. Abertura da janela de cortes (`admin_open_window`, cuts.py) checa **só** `needs_review` zerado — **NÃO** E4-a, **NÃO** rollover. Rollover (do_rollover) é gated na flag **manual** `espn_values_updated` (passo 3, set por `confirm_espn`), **não** pelo import E4-a; lê `Player.espn_ref_value` (qualquer) → roda sobre ESPN preliminar. `offseason_mode` só liga no rollover e gateia cosmético (banners). E4-a entrou como pré-condição **por arrasto** da D8/handoff (bundle "ESPN definitiva + valorização"). **Sem F2 de código** — desfecho é revisão de redação D8/pré-condição de smoke da OFF26-1, decisão do owner. Zero mutação.)
> Atualizado em: 17/06/2026 (sessão MAN-OFF26-PHASE-REG: **registro docs-only** — novo item **OFF26-9** (Alta, 🔲): investigação do acoplamento entre as fases da intertemporada (rollover/abertura da janela de cortes) e a dependência do ESPN definitivo (E4-a, deliberadamente tardio). Suspeita do owner: E4-a entrou nas pré-condições da abertura por arrasto; gate real seria rollover + `needs_review` zerado (D3 da OFF26-1). Natureza: investigação com F1 read-only (despacho em prompt separado), sem F2 garantido. Nenhum item OFF26 existente alterado; D1–D11 da OFF26-1 não reabertas.)
> Atualizado em: 15/06/2026-pt2 (sessão Opus, fechamento documental — **5 itens ✅ + migração O3**: UX8 e UX9 (smoke de prod 15/06), F11-FIX-UX (fecha junto com UX9 — sintoma eliminado pela raiz), DP2 (smoke de prod confirmado), F12 (critério dev-local). Seções detalhadas movidas verbatim p/ `improvements_archive.md`; Status Rápido mantém as 5 linhas como ✅. Zero mudança de código.)
> Atualizado em: 15/06/2026 (sessão Opus: **UX8 ⚠️ REG+F1+F2** — densidade vertical do cap projector, foto ao lado do nome (opção B); F2 flexou `.player-name-cell` (1 regra CSS, classe exclusiva, zero blast radius, 48/48), "tag malformada" da F1 era falso positivo (artefato Grep) → validado localhost, ✅ após smoke prod. **UX9 ⚠️ REG+F1+F2** — passo 2 do fluxo pré-temporada no /admin fragmentava em colunas; causa: `.workflow-steps li` é flex e o link inline `Intertemporada` partia o texto em flex items; F2 envolveu o body num `<span class="step-body">` (texto+link inline em ordem, estrutural não comprimento), 48/48 → localhost, ✅ após smoke prod; fecha o done do F11-FIX-UX junto)
> Atualizado em: 12/06/2026-pt3 (sessão Opus: **F10 ✅** smoke prod + archive; **DOC1 ✅** startup do CLAUDE.md reescrita contra o boot real; **F12 ⚠️** CSV bootstrap one-shot (flag `csv_bootstrap_done`); **F11-FIX-UX** layout do passo 2; **DP2 ⚠️** cadeia única — board sobre keep/corte + summary sticky, `/simulate` removido (fundido no `/budget`))
> Atualizado em: 16/06/2026-pt4 (sessão OFF26-6-7-REG: **registro docs-only** — 2 itens novos no pacote OFF26: **OFF26-6** PoC do Cowork montando a liga fantasma (validação operacional não-código, gate antes da FA auction real, dados fake, roda cedo/isolado) e **OFF26-7** dry run E2E da intertemporada (foco nas costuras entre módulos; depende de OFF26-1/2/4 existirem; OFF26-6 ⊂ OFF26-7; decisão em aberto: gate único vs. por etapas). Ambos 🔲. Nenhum item OFF26 existente alterado.)
> Atualizado em: 16/06/2026-pt3 (sessão E4-d-F1b: **diagnose read-only de aliases ✅** — veredito: **zero infra de alias** no codebase. TIME só tem `name`/`display_name`(=name)/`owner_name`, sem abreviação/mapa; "Houston/HOU" não tem fonte. JOGADOR: pool Sleeper (sid 5848 inspecionado) **não tem campo de apelido** → resolver cobre acento/sufixo/pontuação, NÃO Hollywood↔Marquise; E4-b **deletou** o órfão Brown, nunca resolveu o apelido. Parecer: time por `name`+`owner_name` exato→norm; apelido só por mapa curado (Sleeper não tem). 3 decisões D/E/F p/ owner. Item segue 🔲)
> Atualizado em: 16/06/2026-pt2 (sessão E4-d-F1: **E4-d diagnose read-only ✅** — mapa das 4 portas do `/auction`: jogador-sem-sid replicado nas 3 individuais + Excel (tudo em auction.py, não vaza); time-substring **isolado em 1 linha** (auction.py:219, Excel); resolver E4-a **exige adaptação** (forms não têm NFL team → name-only: único→sid, ambíguo→needs_review); órfão silencioso é o pior caso; parecer F2 + 3 decisões de escopo p/ owner. Item segue 🔲)
> Atualizado em: 16/06/2026 (sessão F9: **F9 ⚠️ localhost** — `bulk_register` roteado por `record_acquisition`, última réplica inline do `/auction` fechada [Player+SalaryHistory+AuctionLog atômicos], `_noop` vestigial removido, idempotência por `event_ref`; smoke temp DB BEFORE(0,0)→RUN1(2,2)→RUN2 idempotente, 48/48; ✅ aguarda smoke prod / FA auction 2026)
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
| M10 | Busca de Jogador: Global + Calculadora (refinado 28/04/2026 — MAN-M10-REFINE) | Média | 🔲 |
| M11 | Teste de auto-containment documental | Média | ✅ 22/04/2026 |
| M12 | Vincular owners a times via tela de admin com lookup do Sleeper | Média | ✅ 22/04/2026 |
| M13 | Página de jogador + "Propor Trade" | Média | ✅ 23/04/2026 |
| M14 | /trades aceitar query params team_a/team_b (pré-requisito M9 + M13) | Média | ✅ 23/04/2026 |
| M15 | Lottery com 6 seeds (inclusão do 7º colocado com 1 bolinha; pool 96) — MAN-M15-REG | Média | ✅ 05/06/2026 |
| M15-FIX | Editor de pesos do lottery: pool/legenda não re-renderizam ao editar + legenda /picks pós-sorteio lê canônico, não o audit | Média | ✅ 05/06/2026 |
| M16 | Lottery aplica ordem sorteada a R2/R3 (deveria ser standings invertido) — corrompe ordem + valores dynasty de R2/R3 — MAN-M16-REG | Alta | ✅ 05/06/2026 |
| OFF26-1 | Janela de cortes selada no Manager (declaração privada de cortes + budget ao vivo não-projetado + lock/revelação simultânea admin-manual, snapshot M8) — MAN-OFF26-REG/F1/REFINE/F2/SMOKE | Alta | ⚠️ F2 + e2e localhost 23/23; **smoke PARCIAL prod 17/06** (infra+abertura OK: deploy live, tabelas criadas, "Fechada — 0/12", gate `needs_review` zerado, cap soft); lock/hash + cortes reais ficam p/ OFF26-7 |
| OFF26-2 | Keeper sheet consolidada (12 times pós-revelação: keeper+salário+budget FA usable via porta projected:false+status declared, tabela+CSV) — insumo do Cowork — MAN-OFF26-REG/F1/REFINE/F2/SMOKE | Alta | ⚠️ F2 + e2e localhost 20/20; **smoke PARCIAL prod 17/06** (deploy live, `CutWindowAudit` criada); sheet depende da revelação (não travada) → validação completa no OFF26-7 |
| OFF26-3 | Importador de drafts de liga fantasma (rookie linear + FA auction via API, match por sleeper_player_id, preview + helper atômico) — MAN-OFF26-REG | Alta | ✅ 05/06/2026 |
| OFF26-4 | Auditoria de keepers pré-leilão (diff keeper sheet × config real da liga fantasma via API read-only; **gate de integridade do leilão**) — MAN-OFF26-REG/F1/REFINE/PROBE/OWNERCHECK/F2/META | Média | ⚠️ F2 + 34/34 localhost (48/48 do salary_engine intactos) + board REAL atravessando o núcleo; **smoke PARCIAL prod 03/08** (`d83d2f8`: rota+card+seed do `phantom_league_id` OK; o 4º ponto era inalcançável → F2-META expôs a meta da liga sob bloqueio); **falta smoke com sheet real (só a partir de 20/08)**; cobertura do D6 aberta (2/12 sem coluna) |
| OFF26-5 | Runbook do procedimento Cowork (documentação da transcrição supervisionada da keeper sheet → liga fantasma) — MAN-OFF26-REG/MAN-OFF26-5 | Média | ✅ 17/06/2026 (doc — `runbook_cowork_liga_fantasma.md`; reconciliado c/ OFF26-6: roster espelha real 3WR obrigatório, liga permanente + mapa por `sleeper_owner_id`, setup único × trabalho anual, gatilho OFF26-4) |
| OFF26-6 | PoC de viabilidade do Cowork montando a liga fantasma no Sleeper (validação operacional NÃO-código: roteiro de experimento + registro do resultado; gate antes de confiar a FA auction real ao procedimento) — MAN-OFF26-6-7-REG/PoC | Alta | ✅ 17/06/2026 (op — GATE passou: Cowork cria liga + seta keeper/salário sozinho; decisões: liga PERMANENTE redraft, config espelha real 3WR, mapa por `sleeper_owner_id`; achados → OFF26-4 calcula budget/lê designações) |
| OFF26-7 | Dry run E2E da intertemporada: ensaio da cadeia inteira encadeada, foco nas costuras entre módulos (OFF26-6 ⊂ OFF26-7); depende de OFF26-1/2/4 existirem; decisão em aberto (gate único vs. por etapas) — MAN-OFF26-6-7-REG | Alta | 🔲 (op) |
| OFF26-8 | Agente Cowork aplica os cortes do OFF26-1 no roster real do Sleeper (capability operacional NÃO-código: dirige a UI para dropar os cortados de cada time; irmão de OFF26-6, ⊂ OFF26-7); depende de OFF26-1 (fonte da lista) — MAN-OFF26-8-REG | Média | 🔲 (op) |
| OFF26-9 | Acoplamento das fases da intertemporada × dependência do ESPN definitivo: o rollover (e a abertura da janela de cortes OFF26-1) depende mesmo do E4-a (ESPN definitivo, deliberadamente tardio) ou só de rollover + `needs_review` zerado? Suspeita do owner: E4-a entrou nas pré-condições por arrasto, atrasando indevidamente o início da intertemporada — investigação (F1 read-only) + correção de redação/microcopy — MAN-OFF26-PHASE-REG/F1/FIX | Alta | ✅ 17/06/2026 (F1 confirmou: abertura só exige `needs_review` zerado, E4-a por arrasto; FIX separou timing × qualidade de dado na D8/pré-condições/microcopy; **smoke do microcopy do passo 6 em prod conferido** — texto lê bem + layout intacto; detalhe no archive) |
| OFF26-10 | **Late drop pós-lock** na janela selada: o late drop de **22/08** altera o conjunto de keepers **dois dias depois do lock** de 20/08, e keeper sheet, budget de FA e board da liga fantasma derivam todos do snapshot selado → a sheet de 20/08 é **provisória** para quem fechou os cortes acima do cap. Decisão em aberto: 2ª mini-janela selada × correção administrativa pós-lock sobre o snapshot existente — MAN-OFF26-10-11-REG | Alta | 🔲 |
| OFF26-11 | Importador (OFF26-3) **não distingue keeper de arremate novo**: com keepers designados no board da liga fantasma, os picks do auction vêm misturados, e a porta canônica de aquisição é porta de **contrato ano 1** → ingerir um keeper **zera a idade do contrato** de quem nunca saiu do time (dano silencioso, visível só na renovação). Decisão em aberto: importar só arremates × reconciliar e reportar divergência — MAN-OFF26-10-11-REG | Alta | 🔲 |
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
| DP1 | Board de planejamento de cap pré-draft: rookies entrantes com `espn_ref_value` + salário projetado `floor(ESPN×1.2)` + simulação de impacto no cap (projeção, não contrato) — lê o **store canônico** — MAN-DP1-REG | A definir | 🔲 (desbloqueado: E4-c-1 ✅ em prod) |
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
| UX8 | Densidade vertical do cap projector: foto **ao lado** do nome (não acima) — recupera densidade em telas 20+ jogadores (decisão owner: opção B, mock 15/06/2026). **F2 ✅ localhost:** flexada `.player-name-cell` (1 regra CSS, classe exclusiva → zero blast radius); "tag malformada" da F1 era falso positivo (artefato de Grep); 48/48 — MAN-UX8-REG/F1/F2 | Baixa/Média | ✅ 15/06/2026 (smoke de prod) |
| DATA-1 | Badges TRADE e REVISÃO removidos da macro de listagem (info pertence à timeline/admin, não à listagem) | Média | ✅ 24/04/2026 |
| T3 | Valores redraft do FantasyCalc no Trade Manager (modelo 3 — duas barras independentes dynasty + redraft) | Média | ✅ 27/04/2026 |
| T3-FIX-UX | Migrar barras dynasty + redraft de dual-fill (T2 pattern) para delta-pointing + corrigir overflow mobile + redraft no modal preview + descrição de trade em formato "de/para" 2-colunas + alinhamento vertical entre colunas (5 sub-iterações, owner-driven via screenshot mobile) | Média | ✅ 27-28/04/2026 |
| AUD1 | Auditoria estrutural read-only do codebase: 6 lentes de incidentes históricos (F1-only — achados viram itens próprios; Lente 6 = test drive do MAN-METH-REG) — MAN-AUD1-REG/F1 | Alta | ✅ 11/06/2026 (achados absorvidos: F11, F12, E4-d, M19, M20, DOC1) |
| PROC1 | Processo: gate de ✅ com smoke de prod exige confirmar que o hash deployado live é o commit validado (não basta commitado/pushado) — casos-âncora E1 + E4-a (927831a×97b90ed) — MAN-PROC1-REG/F1/DONE | Média | ✅ 23/06/2026 (Forma 1: regra afinada no bullet de gate da "Checklist de fim de sessão" do DEV_METHODOLOGY, transversal; robustez extra → PROC2; detalhe no archive) |
| PROC2 | Surfacear o hash deployado (`RENDER_GIT_COMMIT`) no `/admin` — robustez além da disciplina do PROC1 (follow-up da ressalva F1; é código) — MAN-PROC2 | Baixa | 🔲 |
| F11 | Rollover de season duplicado e divergente: `/api/admin/rollover/apply` (sem gate de etapas, sem check `rollover_done`, NÃO avança `current_season`) × `/api/offseason/rollover` (gated) — ambos vivos na UI; dupla execução incrementa contratos 2× — achado AUD1 Lente 2 | Alta | ✅ 12/06/2026 (prod LIMPO + fix Opção A + smoke prod OK) |
| F11-FIX-UX | Microcopy do card "Season Rollover (preview)" e do passo 2 do fluxo pré-temporada no /admin: linguagem de owner (prévia × aplicação real na Intertemporada), link p/ /offseason, sem nº de step e sem season hardcoded — carona da sessão F10 (padrão N1-FIX/T3-FIX-UX) | Baixa | ✅ 15/06/2026 (fecha junto com o [[UX9]] — sintoma do passo 2 eliminado pela raiz) |
| UX9 | Passo 2 do card "Ordem do Fluxo Pré-Temporada" (/admin) fragmenta em colunas. **F2 ✅ localhost:** body de cada passo envolto num `<span class="step-body">` (2 flex items: badge+body) → texto+link fluem inline em ordem; estrutural, não comprimento; local, zero blast radius; 48/48. Fecha o done do F11-FIX-UX quando passar em prod — MAN-UX9-REG/F1/F2 | Baixa | ✅ 15/06/2026 (smoke de prod) |
| F12 | `run_import` sobrescreve salary/contract_year a cada boot com CSV presente (dev local), sem SalaryHistory — reverte silenciosamente rollover/correções locais; coluna `salary_2025` hardcoded — achado AUD1 Lente 2 | Média | ✅ 15/06/2026 (bootstrap one-shot via flag `csv_bootstrap_done`; critério dev-local, sem smoke de prod) |
| F13 | Versionamento do cache do pool Sleeper (`.sleeper_players_cache.json`, ~15 MB, trackeado no git): mtime pós-deploy reinicia o TTL de 168h (frescor enganoso), cada refresh commitado incha a história, e em prod a raiz read-only (doutrina E1) faz a gravação do cache falhar silenciosamente → pós-TTL, todo load re-baixa ~15 MB da API. Cache em `dirname(DYNASTY_DB)` (volume, padrão E1) + gitignore + validade por carimbo `fetched_at` no conteúdo (não mtime) — achado colateral do smoke DP3-F2 — MAN-DP3-COMMIT/CLOSE/**F13-F1/F2/CLOSE** | **Alta** (janela: rookie draft ago) | ✅ 31/07/2026 (smoke prod OK sobre hash `2cd8de3`: recaptura = **287** (145 entraram, 142 atualizados, 6 saíram por corte), 2ª captura 0/0 sem novo download; board 287 c/ 12 do import ESPN, 6 valorados; busca/filtro no navegador; detalhe no archive; **pendência**: frescor sobreviver ao 2º deploy → próximo release) |
| F14 | Nomes do board de rookies (DP3) vêm do pool do Sleeper e perderam sufixos de geração (Jr./II/III) presentes na fonte ESPN — cosmético, **não** afeta identidade (resolvida por `sleeper_id`) — achado do smoke MAN-F13-CLOSE | Baixa (cosmético) | 🔲 |
| E4-d | Matching frouxo nas portas do /auction: single-entry FA/rookie matcha player por nome exato sem resolver sid (guard E4-b ausente — classe órfão) + upload Excel matcha Team por substring `%name%` — achado AUD1 Lente 4 | Baixa/Média | 🔲 |
| M19 | Validação de pesos do lottery só existe no client (JS floor/mín-1); `_normalize_weights` aceita float/zero/negativo — POST direto exclui time do pool silenciosamente — achado AUD1 Lente 1 | Baixa | 🔲 |
| M20 | Descomissionar write-side da flag single-user: sync escreve `is_my_team` via `MY_OWNER_ID`; record_acquisition/bulk_register propagam; colunas + to_dict + check_team.py + mapeamento standings (offseason.py:312) — fora do escopo M17 (só consumidores); **bloqueado: depende de M17, hoje ⚠️ (aguardando smoke prod)** — achado AUD1 Lente 3 | Baixa | 🔲 (bloqueado) |
| DOC1 | CLAUDE.md "App Startup Sequence" desatualizada: `init_auth` listado antes de sync/backfill (código: depois, app.py:138) + sync/backfill são condicionais a `fresh_import` (app.py:61), não passos de todo boot — docs-only fix — achado AUD1 Lente 6 | Média (blast radius: doc carregada em toda sessão) | ✅ 12/06/2026 (seção reescrita contra o boot real, passo a passo com âncoras) |
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

---

### PROC2 — Surfacear o hash deployado (`RENDER_GIT_COMMIT`) no `/admin`
🔲 **Registrado 23/06/2026** — follow-up do [[PROC1]] (ressalva da F1) — **robustez além de disciplina**

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

---

### OFF26-1 — Janela de cortes selada
⚠️ **F2 implementado (16/06/2026) — aguarda smoke prod** — Prioridade **Alta**

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

**Dependências:** é a **fonte** dos itens OFF26-2 e OFF26-4. **Pré-condição de ABERTURA
(trava de código — confirmada pela F1 do [[OFF26-9]]):** apenas **`needs_review` zerado**
(`admin_open_window` não checa E4-a nem rollover). **Recomendações de QUALIDADE DE DADO (não
travam abertura):** rodar o **Season Rollover (passo 4)** antes — para o budget não-projetado
(D9) exibir salário **já valorizado** —; e ter o **E4-a (ESPN definitiva)** para a **exatidão
dos valores** (e o salário de rookie no draft, evento posterior). Ver D8 + esclarecimento
MAN-OFF26-9.

#### Spec final — decisões de produto arbitradas (MAN-OFF26-1-REFINE, 16/06/2026)

Decisões do owner pós-F1. **Esta spec é a verdade do item e SUPERA o enquadramento
preliminar** de "keepers" da Descrição/Escopo acima (que falavam em declarar *keepers*;
a unidade real é a **lista de cortes** — ver D1). A F2 lê esta camada. O que a F1
mapeou (terreno/portas/gaps) continua válido abaixo; aqui ficam as **decisões**.

- **D1 — Unidade = lista de CORTES (`cut_ids`), não keepers.** Keepers são o **complemento**
  (roster atual − cortes). UI, snapshot, keeper sheet e todos os consumidores falam a língua
  do **corte**. (Resolve o "keepers vs cuts" que a F1 deixou em aberto.)

- **D2 — Default de quem não declara: zero cortes = mantém todos.** Coerente com o
  regulamento 5.2. O cap pode estourar pós-rollover; a **adequação é resolvida depois pelo
  admin** (e a trava de cap mora na fronteira do FA auction, não aqui — ver D9).

- **D3 — Pré-condição de ABERTURA: fila `needs_review` ZERADA é BLOQUEIO DURO.** O admin
  **não pode abrir** o prazo de cortes enquanto houver qualquer jogador em `needs_review`
  em qualquer roster. Previne propagar salário não-confiável para o snapshot selado e toda
  a cadeia a jusante. É **gate na abertura**, não validação por-jogador na declaração.

- **D4 — Lock + revelação: disparo admin-manual (botão), padrão M8.** O deadline é **data
  exibida**, não trava sozinho.

- **D5 — Owner que não declara ou cujo time viola adequação: o admin supre/ajusta
  manualmente** (corta pelo owner) **antes do lock**. (Precedente de escrita admin scoped a
  `team_id` arbitrário existe — F1; precisa de exceção explícita à regra cega-pré-lock.)

- **D6 — Sigilo: apenas a DECLARAÇÃO DE CORTES é secreta pré-lock, inclusive para admins**
  (que são owners). Exposto **só contagem agregada** ("8/12 declararam"), nunca conteúdo
  alheio. O **ROSTER permanece público** (já é hoje) — o sigilo recai sobre a **decisão de
  corte**, não sobre o roster. (Confirma o *deslocamento* que a F1 apontou.)

- **D7 — Revelação congela um SNAPSHOT auditável** (molde M8: canônico + `previous_id` +
  `reason` + `hash`; ver F1). **NÃO escreve no Sleeper** (isso é **OFF26-8**) **nem
  materializa cortes** no estado oficial do Manager. A aplicação de salário/adequação segue
  no rollover (passo 4) e na fronteira do FA auction.

- **D8 — Ordem no fluxo: a janela roda DEPOIS do Season Rollover (passo 4).** ⚙️ **DECISÃO
  DE INFRA DELIBERADA (a).** Lê salário **já valorizado** para a temporada nova (ESPN
  definitiva E4-a + regra de valorização aplicadas), porque a decisão de corte depende do
  salário **novo**. Cria a dependência de dados registrada acima (E4-a + rollover antes da
  janela). **Resolve o "gap timing" da F1** (passo 6 pós-rollover) escolhendo o lado
  pós-rollover.
  - **⚠️ Esclarecimento (MAN-OFF26-9, 17/06/2026 — NÃO altera a D8, só separa dois conceitos
    que a redação acima fundiu):** o "pós-rollover" da D8 é **timing de QUALIDADE DE DADO** —
    existe para o budget **não-projetado** (D9) exibir salário **já valorizado**, não como
    **trava de abertura**. A F1 do [[OFF26-9]] confirmou contra o código que a **abertura** da
    janela (`admin_open_window`, `routes/cuts.py`) exige **apenas `needs_review` zerado** — não
    checa E4-a nem `rollover_done`. A menção a "ESPN definitiva E4-a" nesta D8 é **qualidade do
    dado de salário** (afeta a exatidão dos valores valorizados e, depois, o salário de rookie
    no draft via `floor(ESPN×1.2)`), **eventos posteriores que não bloqueiam o início da
    intertemporada**. Em suma: **abrir** só pede `needs_review` zerado; **rodar pós-rollover** é
    recomendação para o budget aparecer valorizado; **E4-a** é exatidão de valor, não pré-condição
    de abertura. A decisão D8 (janela após o passo 4) permanece como está.

- **D9 — Budget ao vivo: consome a porta canônica `POST /api/cap_projector/<team>/budget`
  em MODO NÃO-PROJETADO.** ⚙️ **DECISÃO DE INFRA DELIBERADA (b).** Como o salário **já está
  rollado**, re-projetar (`project_next_salary`) **duplicaria** a valorização (o "gap duplo"
  da F1). Logo a janela precisa do salário **corrente** (já novo), não projetado. Isto é uma
  **ampliação consciente da porta canônica** (um modo não-projetado), **NÃO uma réplica e
  NÃO um débito** — a fonte de cálculo segue única (`draft_budget`); só muda a *base de
  salário* que alimenta o helper. **Registrar como decisão deliberada, não como violação do
  princípio de fonte única do F10.**

- **D10 — Validação 8.3.4 na janela: ALERTA, não trava.** O **enforcement** de adequação ao
  cap pertence à **fronteira do FA auction**, fora deste item. (Confirma a F1: hoje
  `insufficient_budget` já é soft.)

- **D11 — IR e K/DEF CONTAM no budget de keeper**, igual ao `draft_budget` atual. (Resolve o
  gap IR/K-DEF da F1 a favor de manter o comportamento do helper — sem exclusão especial.)

**Resumo das duas decisões que tocam infra (marcadas ⚙️, deliberadas):** (a) **D8** —
dependência de ordem pós-rollover (janela após o passo 4); (b) **D9** — ampliação da porta
canônica de budget com **modo não-projetado** (base = salário corrente já rollado), fonte de
cálculo ainda única.

#### F2 — Implementação (MAN-OFF26-1, 16/06/2026) — ⚠️ aguarda smoke prod

Construído sobre a Spec final. **e2e localhost: 23/23 checks** (script descartável, removido).
`salary_engine_test` 48/48. **Não marcar ✅ até smoke de produção** (lição E1).

**Arquivos tocados:**
- `models.py` — 2 models novos + helper de hash: **`CutDeclaration`** (estado editável/privado
  por `(season, team_id)`, `cut_ids_json`, `declared`; keepers por complemento) e
  **`CutWindowAudit`** (snapshot canônico no molde M8: `declarations_json` de todos os times +
  `is_canonical` + `previous_audit_id` + `reason` + `result_hash` + `executed_at/by`);
  `compute_cut_snapshot_hash` (SHA256 determinístico, ordenado por team_id/cut_id). Tabelas
  novas → criadas por `db.create_all()` (sem ALTER/migração).
- `routes/cuts.py` (**novo blueprint** `cuts_bp`) — página `/cuts` + API: `state` (contagem
  agregada, **sem conteúdo**), `declaration` GET/POST (**escopo `current_user.team_id`** — sem
  param de team_id, sigilo D6), `admin/open` (gate duro `needs_review` D3), `admin/close`,
  `admin/declare` (write-by-team D5, **não lê o alheio**), `admin/lock` (revelação D4/D7),
  `admin/replace` (M8, exige reason), `audit` (revela pós-lock) e `audit/verify` (re-deriva hash).
- `routes/salary.py` — **D9: ampliação da porta canônica** `POST .../budget` com
  `projected` (default `True` — **default intocado**; `False` = salário corrente já rollado).
  Fonte de cálculo segue `draft_budget` (sem 2ª rota, sem aritmética nova — invariante F10).
- `app.py` — registra `cuts_bp`; seed da flag `cuts_window_open`.
- `routes/offseason.py` — **backing do passo 6**: `done` = existe `CutWindowAudit` canônico.
- `templates/cuts.html` (**novo**) + link do passo 6 em `offseason.html`. O cliente só **exibe**
  o budget da porta; `kept_ids = roster − cortes` é **diferença de seleção, não aritmética de
  cap** (grep confirma: única referência a budget no template é display de `usable_draft_budget`).

**Validação de sigilo (requisito de segurança):** owner A tentando ler a declaração de B via
`GET /api/cuts/declaration?team_id=<B>` → o param é **ignorado**, retorna sempre o time de A.
Nenhuma rota expõe `cut_ids` alheios pré-lock; `state` só devolve contagem. Admin opera o time
alheio **só por escrita** (`admin/declare` retorna `num_cuts`, nunca o conteúdo). ✅ e2e.

**Default preservado (D9):** budget sem `projected` == `projected:true` (mesmo JSON); o
cap_projector (consumidor existente) não passa a flag → continua projetado. ✅ e2e.

**Não-mutação:** roster/Player intocados após lock+reveal (snapshot só lê). Nada escrito no
Sleeper. ✅ e2e.

**Fronteiras respeitadas:** 8.3.4 é só alerta (D10); IR/K-DEF contam (D11, herdado do
`draft_budget`); nenhum enforcement de cap; cortes reais no Sleeper = **OFF26-8**;
materialização de salário = Rollover/FA auction.

**Dependência de dados para o OFF26-7 (dry run E2E) — distinção MAN-OFF26-9:** a **abertura**
da janela exige só **`needs_review` zerado** (trava de código). O **Season Rollover (passo 4)**
e o **E4-a (ESPN definitiva)** são **qualidade de dado**, não travas: rodar o rollover antes
faz o budget não-projetado ler salário **já valorizado** (D8); o E4-a dá **exatidão de valor**
(e o salário de rookie no draft, evento posterior). Encadear nessa ordem no ensaio é
**recomendação para os valores aparecerem corretos**, não pré-condição que impeça abrir.

**Pendente (smoke prod):** abrir a janela em prod com `needs_review` real zerado; um owner
declarar; admin lock + verify hash; conferir contagem agregada e a revelação. Só então ✅.

#### Smoke PARCIAL em prod (MAN-OFF26-SMOKE-REG, 17/06/2026) — ⚠️ permanece (não vira ✅)

Smoke parcial executado pelo owner em produção **antes da intertemporada real** e **antes dos
passos 3 (ESPN) e 4 (Rollover)** do fluxo de offseason. Objetivo: validar **infraestrutura +
mecânica de abertura** sem criar snapshot canônico de teste no banco real. **Backup feito
antes:** `dynasty_prod_backup_17_06_2026_pre-off26.db` (540K). O owner optou por **NÃO travar
(lock)** a janela — a validação completa (lock/hash + cortes reais + budget definitivo) fica
para o **[[OFF26-7]]** (dry run E2E).

**Validado em prod (17/06):**
- Deploy do código OFF26-1/2 **live** — `/cuts` e o fluxo `/offseason` carregam sem erro.
- Tabelas novas (`CutDeclaration`, `CutWindowAudit`) **criadas no schema de prod** via
  `create_all` sem erro (toque de schema aditivo confirmado).
- Tela da janela renderiza: estado **"Fechada — 0/12"**, roster, budget **bruto/usável**,
  **alerta de cap soft** (não trava — D10), checkboxes de corte.
- **Gate `needs_review` zerado confirmado** (tela de Revisão de Jogadores) — pré-condição
  única de abertura (D3) satisfeita.
- Fluxo de 7 passos **coerente com o mapa da F1**.

**NÃO validado — fica para o [[OFF26-7]]:**
- Abertura efetiva da janela + declaração de **cortes reais**.
- **Lock/reveal** escrevendo o snapshot canônico + **verificação de hash** em prod.
- Conferência de budget da keeper sheet com **valores definitivos pós-ESPN/rollover**.

**Status:** **⚠️ mantido** — o smoke completo (com lock) ficou pendente; só vira ✅ após a
validação E2E na intertemporada real (OFF26-7).

#### F1 — Diagnose read-only do terreno (MAN-OFF26-1-F1, 16/06/2026)

Diagnose estritamente read-only (zero mutação). Mapeou os 5 terrenos que a janela
consome/colide. Base verificada para a F2.

**Budget canônico (fonte única confirmada pós-F10):** `salary_engine.draft_budget(team_players)`
([salary_engine.py:216-236]) é a função pura; a porta HTTP é `POST
/api/cap_projector/<team_name>/budget` ([routes/salary.py:114-179], `@login_required`),
body `{kept_ids:[Player.id], rookie_sids:[sleeper_id]}`, retorna
`{budget:{salary_cap, keeper_salaries, num_keepers, empty_spots, min_required_for_spots,
raw_budget, usable_draft_budget, over_cap, insufficient_budget}, cap_pct, shortfall, ...}`.
**Cobre o cenário keep-subconjunto** (passa-se os mantidos; cortados ficam fora) e **já
calcula a 8.3.4** (`usable = raw − empty_spots×$1`; `insufficient_budget`). **RÉPLICA:**
o F10/DP2 removeu o `POST /api/cap_projector/simulate` e a aritmética JS; o cliente só
exibe (`cap_projector.html` lê `b.*`, sem conta). **Fonte única confirmada** — OFF26-1
NÃO pode criar 3ª réplica; deve consumir esta porta.

**M8/LotteryAudit como molde:** [models.py:785-819]. **Transferível** (genérico):
`is_canonical`, `previous_audit_id` (cadeia), `reason` (obrigatório no replace),
`executed_at/by`, `result_hash` (SHA256 de conteúdo determinístico), blob JSON de
snapshot; **fluxo replace** = marca canônica antiga `is_canonical=False` + cria nova com
`previous_audit_id`+`reason` ([routes/offseason.py] `_execute_lottery_and_persist` /
`/lottery/replace`); endpoint `verify` re-deriva e compara hash. **Lottery-específico
(NÃO transfere):** `random_seed`, `weights_json`, `pool_json`. Para a janela, o snapshot
do lock guarda `declarations_json` (12 times). **Distinção arquitetural chave:** as
declarações **editáveis/privadas pré-lock** são um estado de trabalho SEPARADO (novo
storage por time) que **congela** no snapshot canônico no momento do lock — o audit M8
é molde só da peça "snapshot+canônica+replace", não do estado editável.

**Identidade de jogador/roster:** chave de declaração = **`Player.id`** (PK local — é o
que `kept_ids` já usa; `sleeper_player_id` só p/ rookies). Roster atual =
`Player.query.filter_by(team_id, is_dropped=False)`. `is_dropped` permanece na DB.

**Autorização — GAP NOVO sem precedente:** `@login_required`/`@admin_required` em
[routes/auth.py:101-112]; vínculo `User.team_id`+`team_rel`; context processor
`inject_user_team` ([app.py:115-121]). **Hoje NÃO existe escopo por-owner**: qualquer
logado lê o roster de qualquer time (`/api/roster/<id>`, `/team/<id>`, `/league` sem
filtro). **Sigilo-mesmo-de-admin é 100% novo e CONTRADIZ o modelo aberto atual.** Nuance:
o sigilo recai sobre a **declaração** (quem manteve quem), não sobre o roster (já público).
Admin escrevendo por time ausente **tem precedente** (admin.py escreve scoped a `team_id`
arbitrário), mas precisa de **exceção explícita** à regra cega-pré-lock.

**Estado de offseason:** `get_current_season()`/`is_offseason()` ([models.py:41-46]) sobre
AppConfig k-v. **O passo 6 "Definir Keepers / Cortes" do workflow é um placeholder**
(`_get_step_statuses`, [routes/offseason.py], `"done": False` hardcoded, sem flag, sem
backing) — é exatamente o slot da janela. `offseason_step` nunca é escrito (só lido); a UI
deriva estado de flags individuais.

**GAP CRÍTICO — base do budget × timing do rollover:** a porta canônica projeta cada
mantido via **`project_next_salary`** ([salary.py:149] → [salary_engine.py:169], usa
`contract_year+1`). O passo 6 fica **depois** do rollover (passo 4), que **já** incrementa
`contract_year` e valoriza `Player.salary`. Consumir a porta como está **pós-rollover
projeta um 2º incremento** (duplo). F2 deve arbitrar **quando** a janela roda e **qual
base** usa (salário corrente vs. projetado) para casar com o momento do fluxo.

**GAP — IR e K/DEF:** `Team.active_salary()` exclui `is_on_ir` ([models.py:96-100]), mas
`draft_budget` **conta** o salário de IR (só filtra `is_dropped`, [salary_engine.py:218]).
A barra de cap e o budget da janela divergiriam para times com IR. K/DEF idem (incluídos no
`draft_budget`, "excluídos em alguns contextos" no CLAUDE.md). Decisão pendente.

**GAP — 8.3.4 é soft hoje:** `insufficient_budget` é só **alerta**, nunca bloqueia
([draft_import.py], `cap_projector.html`). Se a janela deve **travar** declaração inválida,
é enforcement novo sobre a porta.

**REFUTAÇÃO DE PREMISSAS (MAN-METH-REG):**
- *(premissa que o código contradiz)* "sigilo total inclusive p/ admins" — **premissa nova
  válida, mas sem suporte e contra o modelo atual** (tudo público pós-login); exige
  construção do zero (deslocamento do modelo aberto → fechado por-declaração).
- *(premissa parcialmente falsa)* "budget ao vivo consome o endpoint canônico" — **certo
  consumir**, mas a projeção embutida (`project_next_salary`) **só casa se a janela roda
  pré-rollover**; pós-rollover é duplo. Seam, não bug.
- *(perda intencional?)* "validação 8.3.4" — hoje é **alerta soft**; tratar como trava é
  **decisão de produto**, não regressão silenciosa.
- *(perda não-intencional)* **IR/K-DEF**: a proposta é silente; o budget canônico conta IR
  e K/DEF, a barra de cap não conta IR. Precisa decisão.
- *(deslocamento)* o sigilo recai sobre a **declaração**, não o roster (já público) — a
  proposta diz "owner só vê o próprio roster", mas o roster já é visível a todos hoje.

**Decisões de produto ainda NÃO arbitradas (reveladas pela F1):** (1) janela pré ou
pós-rollover (define base do budget); (2) 8.3.4 trava ou só alerta; (3) IR conta no budget
de keeper?; (4) K/DEF conta?; (5) `needs_review` é elegível como keeper?; (6) a porta de
budget precisa de escopo por-owner (senão owner B sondável via `kept_ids`) ou aceita-se por
o roster já ser público?

**Gaps que a F2 fecha (curto):** storage editável/privado por-owner (≠ snapshot do lock);
autorização por-owner + cego-pré-lock (novo, sem precedente); endpoint só-contagem ("8/12")
sem vazar conteúdo; transição lock+reveal congelando snapshot canônico (molde M8:
`declarations_json`+`is_canonical`+`previous_audit_id`+`reason`+`result_hash`); reconciliar
base do budget com o timing do rollover; decidir 8.3.4 hard/soft e IR/K-DEF; backing do
passo 6 (flag + status em `_get_step_statuses`); caminho admin "supre time ausente" com
exceção à regra cega.

---

### OFF26-2 — Keeper sheet exportável
⚠️ **F2 implementado (16/06/2026) — aguarda smoke prod** — Prioridade **Alta**

**Descrição:** relatório por time gerado a partir da revelação do OFF26-1 — keepers,
salários e budget resultante para o FA Auction.

**Motivação:** é o **insumo** que o Cowork transcreve para a liga fantasma; sem ele,
a transcrição não tem fonte de verdade.

**Escopo resumido:** exportar, por time, a lista de keepers + salário + budget de FA,
derivada da revelação selada.

**Dependências:** depende do **OFF26-1** (revelação/snapshot canônico).

#### Spec final — decisões de produto arbitradas (MAN-OFF26-2-REFINE, 16/06/2026)

Decisões do owner pós-F1. **Esta spec é a verdade do item.** A F2 lê esta camada; o
terreno/portas/gaps da F1 continuam válidos abaixo.

- **D1 — Língua do KEEPER por inversão do snapshot.** A sheet mostra **quem fica + salário
  + budget de FA**, derivada de `keepers = roster_live − cut_ids` do snapshot canônico do
  OFF26-1 (`CutWindowAudit`, season = `get_current_season()`), chave **`Player.id`**.

- **D2 — Fonte mista assumida e mitigada (⚙️ DELIBERADA).** Os **cortes** vêm congelados do
  snapshot; **salário e budget** são derivados **AO VIVO** na geração. A página exibe o
  **timestamp do lock** + aviso ("salários conferidos agora; regenere se algo mudou desde o
  lock"). **Justificativa:** não congelar salário no snapshot evita **duplicar a fonte
  canônica `p.salary` dentro do audit** e **não mexe no OFF26-1 já validado** (⚠️ localhost).
  O risco (rollover/correção/drop entre lock e sheet) é coberto pelo aviso de timestamp.

- **D3 — Salário = `p.salary`** (valorizado pós-rollover, D8 do OFF26-1). A sheet **NÃO**
  re-deriva via `project_next_salary`.

- **D4 — Budget de FA = `usable_draft_budget`** (reserva $1/slot, regra 8.3.4), obtido pela
  porta canônica `POST /api/cap_projector/<team>/budget` em **`projected:false`** — **mesma
  chamada e mesmo modo da janela**, para a sheet **bater com o que o owner viu no lock**. A
  sheet **NÃO recalcula** budget.

- **D5 — IR conta normalmente** (D11 do OFF26-1 mantida — jogador no IR é tratado como
  qualquer outro no budget). A sheet **NÃO** tem coluna/flag de IR.

- **D6 — Colunas:** `keeper`, `salário`, `budget de FA do time`, e **`declared`** (declarou de
  verdade / default-zero mantém-todos / admin-supriu) como **coluna de conferência**. **SEM**
  slots vazios, **SEM** contagem 8.3.4 — pertencem à fronteira do FA auction, não à transcrição.

- **D7 — Granularidade: CONSOLIDADA** — os **12 times** de uma vez (o Cowork monta a liga
  inteira; a OFF26-4 também quer todos).

- **D8 — Saída:** **CSV** como artefato principal (consumo do Cowork + registro anual) **+
  tabela renderizada na mesma página** (conferência humana). A F2 verifica se há precedente
  de export reutilizável (F1: **não há** — `csv` stdlib + `Content-Disposition` é padrão novo).

- **D9 — Pré-condição:** só gera **após a revelação** do OFF26-1 (snapshot canônico da season
  existe — `_window_locked`/`revealed:true`); a página comunica claramente se a janela ainda
  **não foi locked/revelada**.

**Decisão que toca a arquitetura, marcada deliberada:** **D2** — derivar salário/budget ao
vivo + aviso de timestamp (em vez de congelar no snapshot), preservando a fonte única
`p.salary`/`draft_budget` e o OFF26-1 intocado.

#### F2 — Implementação (MAN-OFF26-2, 16/06/2026) — ⚠️ aguarda smoke prod

Construído sobre a Spec final. **LEITORA — não muta nada.** e2e localhost **20/20**;
`salary_engine_test` 48/48. **Não marcar ✅ até smoke de prod** (depende, como o OFF26-1, de
janela revelada numa season real pós-rollover).

**Arquivos tocados:**
- `routes/cuts.py` — `_build_keeper_sheet(season)` (deriva `keepers = roster_live − cut_ids`
  do snapshot canônico; salário = `p.salary`; budget = `usable_draft_budget` via o **único**
  `draft_budget` com base corrente — mesmo precedente de `draft_import.py`, **sem aritmética
  nova**), `_declared_status` (default-zero/owner/admin-supplied: declared do snapshot +
  `CutDeclaration.updated_by` live, congelada pós-lock), `_team_fa_budget`. Rotas:
  `GET /cuts/keeper_sheet` (página), `GET /api/cuts/keeper_sheet` (JSON),
  `GET /api/cuts/keeper_sheet.csv` (download, `Content-Disposition`, `csv` stdlib).
- `templates/keeper_sheet.html` (**novo**) — tabela consolidada 12 times + aviso de fonte
  mista com **timestamp do lock** (D2) + botão CSV + comunicação da pré-condição (D9).
- `templates/cuts.html` + `templates/offseason.html` — links para a sheet (reveal / passo 6).

**Validações (e2e):**
- **keepers = roster − cortes:** Alpha corta A-Three → keepers {A-One, A-Two}; **Bravo
  default-zero** → mantém todos (status `default_zero`); **Charlie admin-supriu** → status
  `admin_supplied`. ✅
- **Budget == porta:** `fa_budget` (sheet) == `usable_draft_budget` da porta em
  `projected:false` para os mesmos keepers (130 == 130; usa `p.salary`, não `raw_budget`). ✅
- **Paridade tabela × CSV:** nº de linhas do CSV == total de keepers; CSV carrega
  `fa_budget`+status por time. ✅
- **Sem snapshot:** página 200 comunicando a pré-condição (não quebra); JSON `revealed:false`. ✅
- **Sem mutação:** Player intocado após gerar sheet/CSV. ✅
- **Réplica:** grep confirma **zero** aritmética de cap em `cuts.py`/`keeper_sheet.html` (única
  referência a budget é `draft_budget(...)["usable_draft_budget"]`). Invariante F10 mantida. ✅

**Cadeia (para OFF26-4 e OFF26-7):** a **OFF26-4** (auditoria pré-leilão) compara a config real
da liga fantasma **contra esta sheet** — consumir `/api/cuts/keeper_sheet` (JSON) como base de
diff. O **OFF26-7** (dry run E2E) encadeia: revelação OFF26-1 → **keeper sheet (CSV)** → Cowork
transcreve → OFF26-4 audita. A sheet pressupõe **snapshot revelado** (logo E4-a + rollover +
janela locked antes).

**Pendente (smoke prod):** com janela revelada numa season real, abrir `/cuts/keeper_sheet`,
conferir keepers/salário/budget por time, baixar CSV e validar paridade. Só então ✅.

#### Smoke PARCIAL em prod (MAN-OFF26-SMOKE-REG, 17/06/2026) — ⚠️ permanece (não vira ✅)

Coberto pelo mesmo smoke parcial do [[OFF26-1]] em produção (17/06, **antes dos passos 3 ESPN
e 4 Rollover**; backup `dynasty_prod_backup_17_06_2026_pre-off26.db` 540K; owner optou por
**não travar** a janela).

**Validado em prod (17/06):** deploy OFF26-1/2 **live**; tabela **`CutWindowAudit`** (fonte da
keeper sheet) **criada no schema de prod** via `create_all` sem erro; fluxo `/offseason`
coerente.

**NÃO validado — depende da revelação, fica para o [[OFF26-7]]:** a keeper sheet só é exercível
**com janela revelada** (snapshot canônico), e o lock **não foi disparado** neste smoke. Logo
ficam pendentes: `/cuts/keeper_sheet` com dados reais, conferência de **keepers = roster −
cortes**, **budget de FA** com valores **definitivos pós-ESPN/rollover**, e **paridade
tabela×CSV** em prod.

**Status:** **⚠️ mantido** — a sheet depende da revelação do OFF26-1, que não ocorreu neste
smoke parcial; validação completa no OFF26-7.

#### Melhoria com validação empírica: ORDENAR a sheet na sequência do board (MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026)

> **Registro apenas — nada implementado.** A sheet hoje sai agrupada por time, em ordem de roster
> do Manager. A melhoria abaixo tem **evidência de campo**, não é preferência estética.

Na 2ª execução do Cowork (02/08), a lista de keepers foi entregue **pré-ordenada na sequência exata
do board** — e o efeito foi qualitativo, não marginal: **eliminou busca, deliberação e navegação**,
transformando a transcrição numa **descida linha a linha**. **6 dos 24 keepers dispensaram edição
de preço** por serem de **$1** (o campo já nasce em `$1` — ver [[OFF26-5]]).

**Forma da melhoria:** emitir a sheet **time a time, na ordem das linhas do board**, com **marcação
explícita dos keepers de $1** (os que não exigem edição de preço). O consumidor é o procedimento
Cowork ([[OFF26-5]]), não uma tela do Manager.

**Por que isto merece registro e não é detalhe de formatação:** a sheet é o **artefato de handoff**
entre o Manager e o único passo do calendário que roda **fora** dele. Ordená-la na sequência do
consumidor é a diferença entre "dados corretos" e "dados operáveis" — e o custo é de ordenação,
não de lógica nova.

**Dependência de terreno:** a ordem das linhas do board segue a **config de roster** (QB, RB, RB,
WR, WR, WR, TE, FLEX, DEF, K, banco…), que o runbook exige espelhar a liga real. Ou seja, a ordem
é **derivável** do que o Manager já sabe — mas **confirmar contra o board real** antes de fixar,
porque a ordem exata das vagas de banco/FLEX não foi verificada.

#### F1 — Diagnose read-only do terreno (MAN-OFF26-2-F1, 16/06/2026)

Read-only (zero mutação) sobre o OFF26-1 F2 recém-commitado (`2c243d4`), roster e a
porta de budget. Base verificada para a F2.

**Estrutura do snapshot revelado (o que a sheet deriva):** `CutWindowAudit`
([models.py:854]); `to_dict()` expõe `declarations` = lista por time
`[{team_id, team_name, cut_ids, cut_names, num_cuts, declared}]`. **ACHADO CHAVE: o
snapshot congela SÓ a decisão de corte — NÃO grava salário nem budget.** Acesso ao
canônico: `CutWindowAudit.query.filter_by(season=season, is_canonical=True).first()`,
já exposto por `GET /api/cuts/audit` (`{revealed:true, audit:{...}}`). **Chave de season:**
a janela usa `get_current_season()` **direto** (pós-rollover) — NÃO `season+1` (isso é só
o lottery). A sheet deve casar essa chave.

**Derivar keepers:** `keepers = roster_atual − cut_ids`, com `roster_atual =
Player.query.filter_by(team_id, is_dropped=False)` e chave **`Player.id`** (mesma de
`cut_ids`). ⚠️ **Fonte mista:** roster é LIVE, `cut_ids` vêm do SNAPSHOT — coerente só
enquanto o roster ficar estável pós-lock (sem drop/trade entre o lock e a geração da sheet).

**Salário a exibir (fonte canônica):** **`p.salary`** (já valorizado pós-rollover — D8).
A janela calculou budget em **modo não-projetado** (D9), logo a sheet usa o **mesmo**
`p.salary`, **não** `project_next_salary`. O snapshot não guarda salário → a sheet lê live;
bate com o lock só na janela estável pós-lock (ver acima).

**Budget de FA (consumir, nunca recalcular):** `POST /api/cap_projector/<team>/budget`
com **`projected:false`** + `kept_ids = roster − cuts` — **exatamente a chamada que a
janela fez** (salary.py:114-189, D9). Retorna `raw_budget`, `usable_draft_budget`,
`empty_spots`, `min_required_for_spots`, `insufficient_budget`. **Decisão pendente: qual
número é "o budget de FA"** que o Cowork digita (provável `usable_draft_budget`, que já
reserva $1/slot vazio — 8.3.4).

**Pré-condição de existência:** a sheet só faz sentido com snapshot canônico presente —
`_window_locked(season)` (cuts.py:34) / `revealed:true` no `/api/cuts/audit`. Gate.

**Formato de export (precedente no app):** **NÃO há** export de CSV, página imprimível
(`@media print`/`window.print`), nem clipboard-de-dados. O que existe: import CSV/Excel
(admin/auction), **JSON por time** (`/api/roster`, `/api/cap_projector`, `/api/cuts/audit`),
tabelas **server-side Jinja** (casa de `league.py` team_detail, `roster.py`) e **1
precedente de clipboard** (link de trade, `trades.html:659-670`). `pandas`+`openpyxl`
disponíveis (requirements). Opções viáveis p/ o Cowork: (a) página Jinja imprimível
(mais aderente à casa, Cowork lê na tela), (b) download CSV (`csv` stdlib + header
`Content-Disposition` — padrão novo), (c) clipboard TSV (reusa o mecanismo do trade).

**PERGUNTA DE RÉPLICA — fonte única confirmada:** o cálculo de budget é só `draft_budget`
(via porta; F10/F1 confirmaram, `cuts.html` só exibe). O salário do keeper é só `p.salary`
/ `project_next_salary` — nenhuma 2ª derivação. **A sheet DEVE consumir** (porta + `p.salary`),
**nunca recalcular.** Nenhuma réplica encontrada.

**REFUTAÇÃO DE PREMISSAS (MAN-METH-REG):**
- *(premissa falsa)* "o snapshot congela salários/budget no lock" — **falso**: congela só
  `cut_ids`/`cut_names`/`num_cuts`/`declared`. A sheet deriva salário/budget **live**; só
  bate com o lock enquanto não houver rollover/correção/drop entre lock e sheet.
- *(deslocamento)* "keeper = roster − cortes revelados" — verdadeiro, mas é **fonte mista**
  (roster live − cuts do snapshot). Decisão da F2: aceitar derivação live (documentar a
  premissa de janela estável) — o snapshot **não** guarda a composição do roster no lock.
- *(premissa correta)* "modo de budget = não-projetado p/ bater com o lock" — confirmada (D9).
- *(perda)* o snapshot tem `declared` (declaração real vs. default-zero vs. suprido por admin);
  a proposta da sheet é silente. O Cowork deveria ver a **proveniência** (sheet de time que
  não declarou = roster inteiro por default, não escolha ativa).
- *(deslocamento/decisão)* keepers incluem **IR** (roster só exclui `is_dropped`; IR conta no
  budget — D11). A sheet listará IR; decidir se sinaliza.

**Decisões de produto NÃO arbitradas (p/ o owner, antes da F2):** (1) **formato de export**
(página imprimível vs. CSV vs. clipboard TSV); (2) **por-time individual vs. consolidada**
(12 times — o Cowork monta a liga inteira; a OFF26-4 também quer todos); (3) **qual número
é o "budget de FA"** (`usable_draft_budget` vs. `raw_budget`); (4) a sheet **inclui** slots
vazios / contagem 8.3.4 / flag IR / status `declared`?

**Gaps que a F2 fecha (curto):** derivar keepers = roster live − `cut_ids` do snapshot
(documentar premissa de estabilidade pós-lock); coluna de salário = `p.salary` canônico;
budget consumido da porta em `projected:false` (nunca recalcular); gate por snapshot canônico
existir; escolher formato de export; surfacing de `declared`/IR/qual budget; decidir
por-time vs. consolidada.

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


### OFF26-5 — Runbook do procedimento Cowork
✅ **17/06/2026 — runbook criado (`runbook_cowork_liga_fantasma.md`), reconciliado com as
decisões do OFF26-6** — MAN-OFF26-6-7-REG/MAN-OFF26-5 — Prioridade **Média** — **item de
documentação (não é código)**

> **Critério de ✅:** documento de runbook criado no local/convenção do projeto, com os detalhes
> operacionais do PoC preservados — **sem código, sem smoke prod aplicável**.

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

#### Entrega (MAN-OFF26-5, 17/06/2026) — ✅ runbook criado

Arquivo **`runbook_cowork_liga_fantasma.md`** (raiz, convenção `manager_*.md`/`*_*.md` do
projeto). Conteúdo-base escrito pelo **Cowork** logo após o PoC ([[OFF26-6]]), com detalhes
operacionais fiéis **preservados** (edição do preço com **Ctrl+A**, anti-homônimo por **sigla
NFL** — dois Josh Allen, conexão da **extensão** Claude in Chrome, anatomia do **board**,
**SET PLAYERS** → board, **não clicar START DRAFT**, checklist **TL;DR**).

**3 reconciliações aplicadas (decisões do [[OFF26-6]]), sem perder detalhe operacional:**
1. **Config de roster espelha a liga real** — ajuste **WR 2→3 marcado como OBRIGATÓRIO** (não
   opcional); alvo 1QB/2RB/3WR/1TE/1FLEX/1DEF/1K (+ banco/IR reais); preservado o "como" (+/–).
2. **Liga PERMANENTE + mapa por owner** — liga criada **uma vez** com os 12 owners reais;
   identidade por **`sleeper_owner_id`/handle**, nunca por nome nem "Team N = roster N"; o
   bloqueio "times sem dono não renomeáveis" rebaixado a **nota histórica do PoC** (não-aplicável
   na liga permanente).
3. **SETUP ÚNICO × TRABALHO ANUAL separados** — Fase A (criar liga, roster, Auction+Budget,
   convidar owners) vs. Fase B (só popular keepers da [[OFF26-2]] no board); **reset de rosters é
   automático** (redraft); **gatilho da auditoria [[OFF26-4]] ao término**, antes do auction.

**Cross-refs:** [[OFF26-2]] (keeper sheet — fonte dos keepers/salários), [[OFF26-4]] (auditoria —
gatilho ao término), [[OFF26-6]] (PoC que originou o runbook). **Sem código.**

#### Correção do runbook contra a UI real (02/08/2026 — MAN-OFF26-10-11-REG) — **status ✅ mantido**

> Correção de **texto factual** de um item fechado: o runbook descrevia um caminho que **não existe**
> na interface atual. **O status não é reaberto** — o documento existe e cumpre sua função; o que
> mudou é o conteúdo, agora conferido contra uma transcrição real cronometrada.

**Origem:** a liga fantasma permanente foi **criada de fato** em 02/08/2026 — **Dynasty SB FA
Auction**, Redraft, 12 times, draft **Auction**, budget **$200**, **22 rodadas**, roster espelhando
a real (**3 WR**). O Cowork então transcreveu **1 time completo (10 keepers)** e, no caminho,
descobriu que a Fase B do runbook estava errada.

**8 correções aplicadas em `runbook_cowork_liga_fantasma.md`:**
1. **O caminho documentado NÃO EXISTE.** Não há engrenagem → Draft Settings → *SET
   KEEPERS/DYNASTY PLAYERS* → *SET PLAYERS*. O board **já está em modo de designação** no
   pré-draft; o fluxo real é clicar **direto na célula vazia** da coluna do time → menu → **Set
   Player**.
2. Dentro do Set Player, clicar no **"+" da linha, NUNCA no nome** — clicar no nome abre o perfil
   do jogador, e fechar o perfil **cancela o fluxo inteiro** sem setar nada.
3. **K e DEF ficam abaixo da dobra** do board; revelar pela **seta ▼** do canto direito — o
   **scroll do mouse não move o board**.
4. Para K e DEF, usar o **filtro de posição** em vez de digitar o nome.
5. O campo de preço **já vem com $1** → para keepers de $1 **não é preciso editar**.
6. **Ctrl+A antes de digitar funcionou em 100% dos casos** → rebaixado de **alerta** a **nota**.
7. **Homônimo:** o pool de designação traz **apenas ofensivos elegíveis**, então o Josh Allen
   **LB/JAX não aparece**. Alerta **suavizado, não removido** — dois ofensivos homônimos
   continuariam ambíguos.
8. Nome correto da liga: **Dynasty SB FA Auction**.

**Estado da liga (atualizado — MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026):** após o reset, a **2ª
execução do Cowork repopulou o board** com **Team 3 ($148)**, **Team 4 ($95)** e **Team 5 ($60)**
— dados de **teste**. **Novo RESET DRAFT pendente antes do uso real**, e ele **trocará o
`draft_id` outra vez**. Identificadores: **`league_id` = `1389725099556372481`** (estável) ·
**`draft_id` atual = `1389755381567213568`** — o anterior (`1389725100684611584`) **está morto**,
com a URL travando em LOADING. Tabela completa e a **restrição de desenho** decorrente no bloco do
pacote OFF26 e na seção do [[OFF26-4]]; **nada persistido em código** — a parametrização é decisão
em aberto do OFF26-4.
*(A URL do draft morto "travando em LOADING" é comportamento do **app web**; **pela API ela dá 404
limpo** — ver a correção de premissa do **D1** na spec do [[OFF26-4]].)*

#### ⛔ PROPAGAÇÃO (MAN-OFF26-4-REFINE-PT2, 03/08/2026) — board incompleto NÃO é estado aceitável

> Correção de conteúdo do runbook (**status ✅ mantido**), de peso operacional alto.

O [[OFF26-4]] registrou que **um keeper fora do board é JOGADOR LEILOÁVEL**: o Sleeper o trata como
**disponível**, qualquer owner pode **nomeá-lo** e o **lance é processado normalmente**. Isso muda o
peso de uma instrução que o runbook **já tinha** (*"NÃO clicar em START DRAFT até tudo estar
populado"*): deixa de ser **higiene de processo** e vira **integridade do leilão**.

**Aplicado em `runbook_cowork_liga_fantasma.md`: board incompleto NÃO é estado aceitável para
iniciar o leilão.** Cada keeper não designado é **um jogador com contrato vigente exposto a ser
arrematado por outro time, ao vivo, sem desfazer limpo**. Vale inclusive — e sobretudo — para o
caso do **[[OFF26-10]]**: times **bloqueados pelo teto** ficam com **todos os seus keepers
expostos** até serem populados após o late drop.

**Também registrado no runbook (resolução do owner, 03/08):** **keeper em IR se designa
normalmente**; os excedentes caem no **banco** e a vaga é atribuída **automaticamente por posição**
— a fantasma **não tem slot de IR** e isso **não é problema**. Detalhe e a alternativa descartada na
seção do [[OFF26-4]].

#### Medição de esforço e decisão de método (02/08/2026 — MAN-OFF26-10-11-REG)

**Medido, não estimado:** transcrição de **1 time (10 keepers)** pelo Cowork = **20 min 32 s**
totais, dos quais **~9 min de overhead único** de descoberta do caminho. **Ritmo de regime:
~75 s/jogador ≈ 12,5 min/time → ~2,5 h para os 12 times.** Comparação: a transcrição **manual** do
ano anterior consumiu **uma tarde inteira**.

**Decisão do owner (registrada):**
- **2026 → via Cowork**, com o runbook corrigido.
- **Script determinístico de transcrição → item de melhoria para 2027.** O argumento que o
  justificaria — *"não cabe na janela de 48 h entre o late drop (22/08) e o leilão (24/08)"* —
  **cai** diante dos **2,5 h medidos**. Registrado aqui, e **não** como linha do Status Rápido, por
  restrição do prompt de registro (só OFF26-10/11 entram); **candidato natural a ID próprio** na
  próxima sessão de registro.
- **Caminho via API interna não documentada: DELIBERADAMENTE DESCARTADO.** Sem contrato → quebra
  sem aviso; provável **violação de termos de uso**; e **expõe a conta de comissário da liga real**.
  Registrado para que não seja re-proposto como "otimização óbvia" em 2027.

#### 2ª execução do Cowork — runbook corrigido VALIDADO (MAN-OFF26-RUNBOOK-REG-PT2, 02/08/2026)

Segunda rodada no mesmo dia, agora **com o runbook já corrigido** e **com a lista de keepers
pré-ordenada na sequência do board**. Populados **Team 3 (10 keepers, $148)**, **Team 4 (8, $95)** e
**Team 5 (6, $60)** — **todos os totais conferindo**.

**Objetivo duplo — um resultado e uma perda:** o runbook corrigido **foi validado** (o fluxo real
descrito no `MAN-OFF26-10-11-REG` levou o agente ao fim três vezes, sem redescoberta de caminho);
a **medição de tempo foi perdida** por instabilidade de ambiente (ver bloco próprio abaixo).

##### ⛔ FALSO ACHADO — NÃO APLICAR: "rebaixar o check anti-homônimo"

> **Este é o registro mais importante desta entrada.** O relatório do Cowork **recomenda enfraquecer
> uma proteção**, e a recomendação **está errada**.

**O que o relatório diz:** que a sigla do time NFL exibida pelo Sleeper **diverge** da keeper sheet
(observado: **Waddle exibido como DEN**, **Hill sem sigla**), e que portanto o check anti-homônimo
da §B.3 deveria ser rebaixado.

**Por que está errado:** a causa foi a **lista de teste**, montada manualmente pelo owner-side com
**times de temporadas anteriores**. É **dado velho na lista**, não divergência da plataforma. Na
execução **real**, a keeper sheet sai do **Manager**, que **sincroniza do Sleeper** — os dois lados
**bebem da mesma fonte** e a sigla **bate**.

**A orientação correta é a INVERSA da recomendada:** se a sigla divergir na execução real, isso é
**sinal de problema no sync ou na sheet** → **parar e reportar**, não seguir em frente. Uma
divergência de sigla é **sintoma**, não ruído.

**Decisão registrada: o check anti-homônimo da §B.3 permanece INALTERADO**, sem nenhum
enfraquecimento. Nada foi aplicado no runbook a partir desta recomendação.

**Nota de método (família [[MAN-METH-REG]]):** *recomendação de melhoria vinda de execução com
**dados sintéticos** precisa ser conferida contra a **origem do dado** antes de virar correção de
documento.* Sem essa conferência, **uma proteção teria sido enfraquecida na véspera do uso real por
artefato de teste** — e o enfraquecimento pareceria justificado, porque a observação era verdadeira
(a sigla **de fato** divergiu). O erro não estava no que se viu; estava em **de onde o dado vinha**.

##### 5 correções aplicadas ao runbook

1. **Identificação de coluna com times placeholder — os DOIS estados.** Enquanto os times não
   tiverem donos reais, os cabeçalhos das colunas são **avatares vazios, sem rótulo de texto** — não
   há "Team N" escrito em lugar nenhum. A verificação canônica nesse estado é o **menu de contexto
   da célula**, que exibe *"Manually set a player for Team N"*. A orientação anterior ("identifique
   pelo owner") **pressupõe rótulos que só existirão quando os owners reais entrarem**.
2. **Reescala do board após a primeira interação.** O board **desloca/reescala**, o que **quebra
   referência posicional**. Mitigação observada: revelar **FLEX/K/DEF pela seta ▼ antes** de mirar
   as linhas de baixo, e **confirmar o time pelo menu de contexto antes de cada designação**.
3. **Atribuição de vaga é POR POSIÇÃO.** Escolher o jogador o coloca na vaga correta
   automaticamente (um **RB entra no FLEX** quando as vagas de RB estão cheias). **Clicar a célula
   exata é conveniência, não obrigação** — reduz a criticidade do item 2.
4. **O campo de preço nasce em `$1` SEMPRE**, inclusive quando o `$PROJ` é maior. **Regra
   generalizada:** vale para **qualquer keeper de $1**, não só K/DEF (o registro anterior sugeria
   escopo menor).
5. **Filtro de posição para K/DEF confirmado como mais rápido**, com propriedade útil descoberta:
   kickers e defesas **já designados somem do filtro** → "pegar o primeiro disponível" é **limpo e
   sem colisão**.

##### Ganho da lista ordenada — validado qualitativamente

A lista pré-ordenada na sequência do board **eliminou busca, deliberação e navegação**; a execução
virou **descida linha a linha**. **6 dos 24 keepers dispensaram edição de preço** (keepers de $1).
→ **Vira melhoria concreta do [[OFF26-2]]** (ordenar a sheet na sequência do board, marcando os de
$1), registrada lá **sem implementação**.

##### ⚠️ Medição PERDIDA + risco de variância de ambiente

**Tempos de relógio:** Team 3 = **26min52s** (10 keepers) · Team 4 = **14min13s** (8) · Team 5 =
**13min58s** (6) · **total 58min26s**. **Estes números NÃO medem o procedimento:** o ambiente do
Cowork acumulou **dezenas de timeouts de captura de tela, de 30 s cada**, que **dominam o relógio**.

**Evidência de que o gargalo é o ambiente, não o método:**
- o **Team 4 foi mais rápido por jogador que o Team 3**, e o **Team 5 voltou a subir** — por
  **concentração de timeouts**, não por regressão de fluxo (a curva de aprendizado não sobe);
- a execução **anterior**, no **mesmo dia**, **sem** runbook corrigido e **sem** lista ordenada,
  rendeu **~75 s/jogador**. **Nenhuma explicação plausível sustenta que corrigir o documento e
  pré-ordenar a lista tenha tornado o trabalho mais lento.**

**Risco operacional registrado:** as duas execuções rodaram **no mesmo ambiente**, com resultados
**muito diferentes** e **sem causa identificada**. A instabilidade é **imprevisível**. Projeção por
ritmo de regime: **~2 h para 12 times**; numa execução degradada como a segunda, **~5 h** — e **não
há como saber qual será antes de começar**.

**Mitigação registrada: fatiar a transcrição POR TIME**, cada um uma **unidade verificável** — se a
sessão degradar, a seguinte **retoma do time seguinte sem refazer nada**. É a mitigação certa
justamente porque o modo de falha é *lentidão*, não *erro*: o trabalho já feito permanece válido.

##### Efeito sobre a decisão Cowork-2026 / script-2027 — reconsideração PARCIAL, em aberto

- **A decisão vigente NÃO muda:** 2026 roda **via Cowork**.
- **O argumento original do script segue caído:** "não cabe na janela de 48 h" — o **tempo médio
  cabe**.
- **Mas surge um argumento NOVO, de natureza diferente: VARIÂNCIA.** O script determinístico **não
  tem esse modo de falha**. O risco deixou de ser "demora demais" e passou a ser "**não dá para
  prever quanto demora**" — e é a imprevisibilidade, não a duração, que ameaça uma janela de 48 h.
- **Contra-argumentos preservados (seguem válidos):** **fragilidade de seletores** (script que
  dirige UI quebra com mudança de front-end — e a UI **já mudou uma vez** entre junho e agosto);
  **competição por prazo** com [[OFF26-4]] e [[OFF26-11]], que estão no caminho crítico; e
  **estreia no dia do uso** como pior cenário possível.
- **Status: reconsideração parcial ABERTA.** Não arbitrada aqui.


---

### OFF26-6 — PoC de viabilidade do Cowork montando a liga fantasma
✅ **17/06/2026 — PoC executado em liga de teste descartável; mecânica central validada +
decisões de design arbitradas** — MAN-OFF26-6-7-REG/PoC — Prioridade **Alta** — **validação
operacional (NÃO é código do Manager)** — **GATE PASSOU**

> **Critério de ✅:** validação operacional com resultado documentado — **sem código, sem smoke
> prod aplicável** (a prova é o experimento na UI do Sleeper, registrado abaixo).

**Descrição:** prova de conceito, em liga de **teste descartável** e com antecedência,
de que **Cowork + Claude in Chrome** conseguem, dirigindo a UI do Sleeper, montar a liga
fantasma de ponta a ponta: **criar sala → popular 12 times → configurar draft auction →
setar keepers como rosters + budgets**. Produz um **roteiro de experimento** + **registro
estruturado do resultado** (onde o procedimento trava, que intervenção manual exige).

**Motivação:** a API do Sleeper é **read-only** — a montagem só é possível dirigindo a UI
pelo navegador, frágil por natureza e **nunca validada**. O runbook OFF26-5 já documenta
esse procedimento **assumindo que ele funciona**; falta o passo anterior, que prova **SE e
COMO** funciona. É premissa não testada no **caminho crítico** (a FA auction real depende
dela).

**Escopo resumido:** roteiro do experimento (passos da montagem na UI) + execução numa liga
de teste com **dados fake** (não precisa da keeper sheet real) + registro estruturado do
resultado (sucesso/trava por etapa, intervenções manuais necessárias). Testa a **mecânica
pura** da montagem, isolada das demais peças.

**Função de GATE:** deve **passar antes** de confiar a FA auction real ao procedimento Cowork.

**Dependências:** nenhuma para rodar (testa a mecânica isolada, dados fake). **Relação com
OFF26-5:** o resultado do PoC é o **insumo** do runbook (o runbook documenta o caminho
**comprovado** pelo PoC). **Relação com OFF26-7:** é um **subconjunto** dele (a etapa "Cowork
monta a liga" dentro do ensaio E2E maior).

#### Resultado do PoC (MAN-OFF26-6-PoC, 17/06/2026) — ✅ GATE passou

PoC executado pelo owner em **liga de teste descartável**. A **mecânica central foi validada**
e emergiram **decisões de design** que reformulam a estratégia da liga fantasma. Sem código.

**(a) Validado (Cowork + Claude in Chrome dirige a UI sozinho):**
- **Cria a liga no Sleeper** via wizard: Fantasy Football → nome → 12 times → Redraft →
  **Auction no Step 4**.
- **Seta keeper com salário**, descobrindo o mecanismo sozinho: Settings → Draft Settings →
  **"SET KEEPERS/DYNASTY PLAYERS"** → SET PLAYERS → draft board → slot do time → Set Player →
  busca jogador → define salário → **SET PLAYER**.
  > **⚠️ Anexo (02/08/2026 — MAN-OFF26-10-11-REG):** este **caminho não existe mais** na UI atual.
  > A transcrição real de 02/08 mostrou que o board **já está em modo de designação** no pré-draft —
  > clica-se **direto na célula vazia** → menu → **Set Player**. O registro acima é **preservado como
  > estado da UI em 17/06/2026**; o caminho vigente está no `runbook_cowork_liga_fantasma.md`
  > (corrigido) e na seção do [[OFF26-5]]. **A conclusão do PoC — o Cowork consegue designar keeper
  > com salário sozinho — permanece válida e agora está confirmada em escala** (10 keepers
  > cronometrados).
- **Confere nome completo + time NFL antes de adicionar** (comportamento anti-homônimo;
  ex.: Mahomes QB-KC, Bijan RB-ATL confirmados) — mesma higiene da classe "Brown" na camada de
  operação manual.

**(b) Decisões de design (arbitradas pelo owner a partir do PoC):**
- **Liga fantasma passa a ser PERMANENTE** (redraft fixa, com os 12 owners reais dentro), **não
  recriada a cada ano**. Motivo empírico: times **sem dono** (placeholders) **não são
  renomeáveis/gerenciáveis** pela UI — bloqueio observado no PoC. Liga permanente com owners
  reais elimina o bloqueio.
- **Reset de roster NÃO é trabalho do Cowork:** o formato **redraft reseta rosters
  automaticamente** na virada de season. O trabalho **anual** do Cowork = **apenas popular o
  pré-draft com os keepers**.
- **Config de roster da liga fantasma DEVE espelhar a liga real:** **1QB, 2RB, 3WR, 1TE, 1 FLEX
  (RB/WR/TE), 1DEF, 1K** (+ banco/IR conforme a liga real). Achado: a liga de teste nasceu com
  **2 WR** (padrão Sleeper) ≠ **3 WR** da liga real — **config exata é requisito**.
- **Mapeamento owner↔time ancorado em `sleeper_owner_id`** (chave canônica), **NUNCA no nome do
  time** (mutável). Mesma família de risco do "Brown" (id canônico vs. nome), aplicada à camada
  de **owner**.

**(c) Achados técnicos (impacto a jusante — ver [[OFF26-4]] / [[OFF26-5]] / [[OFF26-8]]):**
- **"Salary cap" no Sleeper não é toggle separado:** é o **budget do auction** (Draft Settings →
  Budget, **$200 global**). O cap individual **emerge** dos salários dos keepers consumindo o
  budget global.
- **Cap restante por time só é visível AO VIVO durante o auction;** no estado pré-draft **não há
  número de budget restante na tela**. → **Impacto [[OFF26-4]]:** a auditoria deve **CALCULAR**
  (`$200 − Σ salários dos keepers`), **não ler** um número pronto da liga fantasma.
- **Keepers ficam como designação de board no pré-draft;** só **populam o roster quando o draft
  roda**. → **Impacto [[OFF26-4]]:** a auditoria lê **designações de keeper**, não o roster.
- **Ponte de identidade de OWNER já existe no Manager:** `Team.sleeper_owner_id` (populado pelo
  Sleeper sync; vínculo **M12** ✅). → **Impacto [[OFF26-4]]:** a ponte de **owner está
  resolvida**; resta investigar na F1 **apenas a ponte de JOGADOR** (se
  `/api/cuts/keeper_sheet` expõe `sleeper_player_id`).

**Cross-refs de desfecho:**
- **[[OFF26-4]]** (auditoria de keepers pré-leilão): a auditoria **calcula** o budget (não lê),
  **lê designações de keeper** (não roster); **ponte de owner resolvida** via `sleeper_owner_id`;
  **resta a ponte de jogador** (escopo da F1 do OFF26-4).
- **[[OFF26-5]]** (runbook): documentar o caminho **comprovado** acima — incl. a config de roster
  espelhando a real (3 WR etc.), o modelo de **liga permanente** e o trabalho anual reduzido a
  **popular keepers no pré-draft**.
- **[[OFF26-8]]** (Cowork aplica cortes no Sleeper): mesma natureza operacional (dirigir a UI);
  o anti-homônimo (nome+time NFL) validado aqui vale para a aplicação de cortes.

**Status:** ✅ — GATE de viabilidade **passou** (a FA auction real pode ser confiada ao
procedimento Cowork, observadas as decisões de design acima). Sem smoke prod aplicável (a prova
é o experimento operacional registrado).

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

---

### OFF26-8 — Cowork aplica os cortes no roster real do Sleeper
🔲 **Registrado 16/06/2026** — MAN-OFF26-8-REG — Prioridade **Média** — **capability
operacional (NÃO é código do Manager)**

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

### OFF26-10 — Late drop pós-lock na janela selada
🔲 **Registrado 02/08/2026** — MAN-OFF26-10-11-REG — Prioridade **Alta** (caminho crítico
**22/08**)

**Calendário da intertemporada 2026, confirmado pelo comissário (02/08/2026):** **17/08**
rookie draft · **18/08** congelamento ESPN · **20/08** prazo de cortes · **22/08 late drop**
(cada time pode dropar **no máximo um** jogador) · **24/08** FA auction.

**Descrição:** a janela de cortes do [[OFF26-1]] foi desenhada com **deadline único, lock e
revelação simultânea**. O **late drop de 22/08** altera o conjunto de keepers **dois dias
depois do lock**, e keeper sheet ([[OFF26-2]]), budget de FA e board da liga fantasma derivam
**todos** do snapshot selado (`CutWindowAudit`). O item registra esse descompasso entre o
desenho vigente e o calendário real.

**Motivação:** consequência operacional **já identificada** — a keeper sheet emitida em 20/08 é
**provisória** para os times que fecharam os cortes **acima do cap**, tornando-se definitiva só
**após 22/08**. Sem tratamento explícito, um artefato provisório circula com cara de definitivo
no exato ponto em que o Cowork o transcreve para o board.

**Fundamentos registrados (descrição do terreno, não decisão):**
- O late drop existe como **válvula** para o time que fecha os cortes ainda acima do cap e se
  ajusta antes do leilão.

##### Achados empíricos (experimento manual na liga fantasma real, 02/08/2026)

A suspeita registrada mais cedo nesta mesma sessão — "o Sleeper pode recusar designação acima do
budget" — **deixou de ser probe: foi CONFIRMADA por experimento.**

- **Fórmula do teto de lance, confirmada:** `teto = 200 − gasto − (vagas_restantes − 1)`. O Sleeper
  reserva **$1 por vaga ainda não preenchida**. Time com **$150 gastos** e **21 vagas livres** →
  teto **$29**: **$40, $33 e $32 rejeitados** (*"The specified slot does not have enough budget."*),
  **$29 aceito**. Sem falso positivo no sentido oposto — outro time recebeu **10 keepers somando
  $140** (folga de $49) **sem nenhum aviso**.
- **Time acima do limite NÃO ENTRA no board** — a designação é **recusada**. Logo **a população
  escalonada é OBRIGATÓRIA, não alternativa**: os times já enquadrados entram na primeira leva
  (20/08) e os estourados **só depois do late drop** (22/08). Não existe "popular tudo em 20/08 e
  remendar".
- **Funcionalidade concreta que isso abre:** o Manager **pode calcular antecipadamente quais times
  ficarão bloqueados** — antes de o Cowork tentar e apanhar da UI.

> ##### ⛔ PROPAGAÇÃO (MAN-OFF26-4-REFINE-PT2, 03/08/2026) — o bloqueio EXPÕE os keepers do time
>
> O [[OFF26-4]] registrou que **um keeper fora do board é, para o Sleeper, JOGADOR DISPONÍVEL**:
> qualquer owner pode nomeá-lo e o leilão **processa o lance normalmente**. Combinado com o achado
> deste item — times acima do teto **não conseguem ser populados até o late drop** —, a consequência
> é direta e **não é hipotética**:
>
> **Enquanto um time permanece bloqueado, TODOS os keepers dele estão expostos ao leilão.**
>
> → **A população completa do board é PRÉ-CONDIÇÃO DE ABERTURA do leilão, não preparativo.**
> **Abrir o leilão com qualquer time não populado expõe os keepers desse time** — e o dano não é
> contábil: é **transação inválida ao vivo, sem forma limpa de desfazer sem interromper o leilão**.
>
> **O que isso NÃO decide:** a **decisão em aberto** deste item (2ª mini-janela selada × correção
> administrativa pós-lock) **permanece em aberto** — isto é **registro de consequência**, não
> arbitragem. Mas qualquer desenho que saia dela **tem de terminar com o board 100% populado antes
> de 24/08**, porque a janela 22/08 → 24/08 é curta e o custo de errar é o leilão.
- **Assimetria de limite — a premissa mudou de lado.** O que se supunha ser regra só do Manager
  (reserva de $1/slot) é **a mesma dos dois lados**; ver a **refutação do §5 da F1 do [[OFF26-4]]**,
  registrada nesta sessão. **Ressalva pendente:** o Sleeper reserva sobre as **22 rodadas** da sala;
  a regra **8.3.4** conta slots pelo **regulamento**. Se as contagens divergirem, os limites não
  coincidem apesar da fórmula idêntica — **conferência aritmética pendente, não experimento**.

**Escopo resumido:** registro apenas. Definir como a janela selada acomoda uma alteração de
keepers posterior ao lock, e o que isso implica para a emissão da keeper sheet, para o budget
de FA e para a ordem de população do board.

**DECISÃO EM ABERTO (pendente do owner — NÃO arbitrada):** o late drop é uma **segunda
mini-janela selada**, ou uma **correção administrativa pós-lock** sobre o snapshot existente? A
escolha determina se há **novo lock/hash**, se a **revelação é simultânea de novo**, e o que a
**trilha de auditoria** registra. Registrar a decisão antes de iniciar a F1 do item.

**Dependências:** depende do **[[OFF26-1]]** (é o snapshot que o late drop altera); **afeta
[[OFF26-2]]** (a sheet passa a ter versão provisória × definitiva) e **[[OFF26-4]]** (a
auditoria compara contra qual versão?). Entra como **etapa do [[OFF26-7]]**, entre o lock e a
sheet definitiva.

---

### OFF26-11 — Importador distingue keeper de arremate novo
🔲 **Registrado 02/08/2026** — MAN-OFF26-10-11-REG — Prioridade **Alta** (caminho crítico
**24/08**)

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

**DECISÃO EM ABERTO (pendente do owner — NÃO arbitrada):** o **Manager permanece fonte única da
verdade** sobre keepers e o importador ingere **apenas os arremates**? Ou o importador
**reconcilia os dois lados** e **reporta divergência de salário de keeper**, virando uma
**segunda auditoria** (sobreposta ao [[OFF26-4]], que audita o mesmo par **antes** do leilão)?
Registrar a decisão antes de iniciar a F1 do item.

**Dependências:** depende do **[[OFF26-3]]** (✅ — é a porta que ingere) e do **mesmo probe
empírico que o [[OFF26-4]] aguarda**. Entra como **etapa do [[OFF26-7]]** (import do resultado
do auction). Toca `record_acquisition` **apenas na leitura** (o que se decide ingerir), não na
porta em si.

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

