# Handoff pt3 — Fantasy Manager — 02/08/2026 (MAN-OFF26-10-11-REG)

> Continuação de `handoff_code_manager_02_08_2026_pt2.md` (fechamento do arco S2 → S5).
> Esta parte é **registro puro**: nenhum código, nenhuma diagnose, nenhuma decisão de produto
> arbitrada. Dois gaps novos entram no backlog e uma premissa factualmente errada é emendada.
>
> ⚠️ **ESTE ARQUIVO TEM 6 PARTES — LEIA A ÚLTIMA ANTES DE AGIR.** A **parte 2** registra a liga
> fantasma **criada e testada na mão** (confirmou duas questões que a parte 1 deixa como "probe
> pendente" e **refutou o §5 da F1 do OFF26-4**); a **parte 3** registra a **2ª execução do Cowork**
> e, entre outras coisas, que **o `draft_id` registrado na parte 2 já está MORTO** — ele muda a cada
> reset; a **parte 4** (03/08) registra a **spec D1–D7 do OFF26-4**; a **parte 5** registra o
> **probe read-only do pré-draft**, que **derrubou o bloqueador do OFF26-4** e **refutou a premissa
> do LOADING** que a parte 4 carrega. **Onde as partes divergirem, vale a mais recente.**
>
> 🔴 **SE FOR LER SÓ UMA COISA, LEIA A PARTE 6 (§35):** **keeper fora do board é JOGADOR
> LEILOÁVEL.** Board incompleto na abertura do leilão = jogador com dono arrematado por outro time,
> ao vivo, sem desfazer limpo. Isso requalifica o OFF26-4 como **gate de integridade**, e torna a
> **população completa do board pré-condição de abertura**.

---

## 1. O que motivou a sessão

Sessão de planejamento com o owner fixou o **calendário real da intertemporada 2026**, confirmado
pelo comissário:

| data | etapa |
|---|---|
| **17/08** | rookie draft |
| **18/08** | congelamento ESPN |
| **20/08** | prazo de cortes |
| **22/08** | **late drop** — cada time pode dropar **no máximo um** jogador |
| **24/08** | FA auction |

Percorrer esse calendário contra o que o Manager já modela expôs **dois gaps que não existiam em
lugar nenhum do backlog**, além de uma premissa errada repetida desde o registro do pacote OFF26.

---

## 2. Os dois itens novos

### OFF26-10 — Late drop pós-lock na janela selada · 🔲 **Alta** (caminho crítico 22/08)

A janela do **OFF26-1** foi desenhada com **deadline único, lock e revelação simultânea**. O late
drop de 22/08 altera o conjunto de keepers **dois dias depois do lock**, e keeper sheet
(OFF26-2), budget de FA e board da liga fantasma derivam **todos** do snapshot selado
(`CutWindowAudit`).

**Consequência operacional já identificada:** a sheet emitida em **20/08 é provisória** para os
times que fecharam os cortes **acima do cap** — definitiva só após 22/08. É um artefato provisório
circulando com cara de definitivo exatamente no ponto em que o Cowork o transcreve para o board.

Dois fundamentos registrados junto, ambos **como descrição, não como decisão**:

- **Questão empírica (destino de probe, NÃO fato):** o Sleeper pode **recusar** a designação de
  keepers cuja soma ultrapasse o budget do auction — o cap não é campo, é o **budget sendo
  consumido**. Se recusar, a população do board **não** pode ser feita de uma vez em 20/08 e
  remendada depois; teria de ser **fatiada por time**. Não é assertável a partir do código.
- **Assimetria de limite:** o Sleeper conhece só o **budget global**; a regra da liga é mais
  apertada (reserva de **$1 por slot vazio**). Um time pode **passar no Sleeper e estar ilegal na
  regra da liga**.

> **DECISÃO EM ABERTO (do owner — não arbitrada):** o late drop é uma **segunda mini-janela
> selada**, ou uma **correção administrativa pós-lock** sobre o snapshot existente? Determina se há
> novo lock/hash, se a revelação é simultânea de novo, e o que a trilha de auditoria registra.

### OFF26-11 — Importador distingue keeper de arremate novo · 🔲 **Alta** (caminho crítico 24/08)

Os keepers **precisam** estar designados no board da liga fantasma — **não é opcional**: o Sleeper
não tem cap por time, e o cap individual **emerge** dos salários dos keepers consumindo o budget
global. Logo, quando o auction rodar, os picks conterão **keepers e arremates misturados**.

O importador **OFF26-3** escreve pela porta canônica de aquisição, que é porta de **contrato ano
1**. Ingerir um keeper **zera a idade de contrato** de um jogador que **nunca saiu do time** — dano
silencioso, com efeito visível **só anos depois, na renovação**.

**Caso canônico do owner:** jogador com contrato de **$50** é dropado na janela, vai a leilão e é
**recomprado pelo mesmo time por $50**. Valor idêntico, **natureza diferente** — o contrato antigo
morreu e nasceu um contrato ano 1. Tratar como continuidade perde a idade e corrompe a trajetória
de renovação.

**Por que nunca apareceu:** o importador foi validado contra os drafts reais de 2025, cujas salas
**não tinham keeper designado no board**. O caminho board-com-keepers é novo em 2026.

**Questão empírica pendente (probe, não suposição):** os picks pós-draft vêm marcados de forma que
permita separar keeper de arremate, ou o discriminador terá de vir da **keeper sheet do próprio
Manager**, como lista de exclusão? É o **mesmo probe que o OFF26-4 aguarda** (nada no código lê o
estado pré-draft hoje).

> **DECISÃO EM ABERTO (do owner — não arbitrada):** o Manager permanece **fonte única da verdade**
> sobre keepers e o importador ingere **apenas os arremates**? Ou o importador **reconcilia os dois
> lados** e reporta divergência de salário de keeper, virando uma **segunda auditoria** (sobreposta
> ao OFF26-4)?

---

## 3. A emenda — o rookie draft NÃO roda em liga fantasma

O registro do pacote OFF26 (05/06/2026) afirma, numa frase, que rookie draft e FA auction rodam
**ambos** em ligas fantasmas. **É falso**, e a metade do rookie draft **nunca foi justificada item a
item** — entrou por arrasto, colada no motivo real da FA auction.

**Evidência:**

- o importador **OFF26-3** foi validado contra o **rookie draft real de 2025**, lido da **chain de
  ligas da liga real** — não de sala separada;
- todo o arco **S2/S3**, fechado hoje mesmo, trata do **board de R1 2026 da liga real**: a
  permutação administrativa de picks, o espelhamento do board e a tela prescritiva pendente (S5)
  **só fazem sentido ali**.

**O motivo próprio da FA auction permanece válido:** a liga real é **dynasty com rosters cheios**, e
o auction pressupõe **rosters vazios sendo preenchidos por lance**, com o cap emergindo do budget
global consumido pelos keepers.

→ **Consequência propagada: existe UMA liga fantasma permanente — a da FA auction —, não duas.**

**Como foi aplicada** (precedente de correção de premissa do **DP1**: preservar a frase, anexar a
correção):

| onde | o que mudou |
|---|---|
| título da seção do pacote | "ligas fantasmas" → "**liga fantasma**" |
| parágrafo de contexto (05/06) | **preservado verbatim** + nota de emenda antes + bloco **EMENDA** depois |
| descrição do **OFF26-7** | cadeia ajustada (rookie draft na liga real; "monta" → "**popula**" a fantasma permanente) + **OFF26-10 e OFF26-11 entram como etapas** |
| `CLAUDE.md`, linha do `draft_import` | "importa drafts de liga fantasma" → **rookie linear na liga REAL / FA auction na fantasma**, com o alerta do OFF26-11 |

**Deixado intacto de propósito** — e este é o ponto a revisar se incomodar: a linha do **OFF26-3 no
Status Rápido** e sua **seção no `improvements_archive.md`** ainda se chamam "importador de drafts
de liga fantasma". Duas razões: (a) o prompt restringiu o Status Rápido a exatamente duas linhas
adicionadas, nenhuma alterada; (b) o archive é registro histórico por construção. O rótulo é
**nomeação de item fechado**, não premissa viva — e a emenda diz isso explicitamente, para que uma
diagnose futura que caia no archive saiba onde está a correção. Handoffs antigos (05/06, 08/06)
também carregam o rótulo e não foram tocados.

---

## 4. Cross-refs estabelecidos

- **OFF26-10** depende de **OFF26-1** (é o snapshot que ele altera); **afeta OFF26-2** (sheet
  provisória × definitiva) e **OFF26-4** (a auditoria compara contra qual versão?).
- **OFF26-11** depende de **OFF26-3** (✅, é a porta que ingere) e do **mesmo probe empírico que o
  OFF26-4 aguarda**.
- **Ambos entram como etapas do OFF26-7** (dry run E2E) — são **costuras**, exatamente o objeto
  daquele ensaio.

---

## 5. Estado do backlog após esta sessão

| item | estado |
|---|---|
| S2, S3 | ✅ 02/08/2026 (smoke prod) |
| S4, S5 | 🔲 não bloqueiam |
| **OFF26-10** | 🔲 **Alta — novo** |
| **OFF26-11** | 🔲 **Alta — novo** |
| OFF26-1, OFF26-2 | ⚠️ (smoke parcial 17/06; validação completa no OFF26-7) |
| OFF26-4, OFF26-7, OFF26-8 | 🔲 |

**Nenhum item existente teve status alterado.** Sem código, sem schema, sem rotas, sem testes.

---

## 6. O que a próxima sessão precisa decidir antes de qualquer F1

As duas **DECISÕES EM ABERTO** acima são do owner e **não foram arbitradas**. Nenhuma das duas
comporta F1 útil antes de resolvida:

1. **OFF26-10** — mini-janela selada × correção administrativa pós-lock.
2. **OFF26-11** — importar só arremates × reconciliar e reportar divergência.

Há ainda **um probe compartilhado** (OFF26-4 / OFF26-10 / OFF26-11) contra a liga fantasma real,
que pode ser levantado numa sessão só: o que a API do Sleeper expõe **pré-draft** sobre designações
de keeper, se ela **recusa** designação acima do budget, e se os picks **pós-draft** vêm marcados
como keeper.

---

## 7. Arquivos alterados

- `improvements.md` — 2 linhas no Status Rápido, 2 seções detalhadas novas, bloco EMENDA no
  registro do pacote, emenda na descrição do OFF26-7, cabeçalho "Atualizado em".
- `manager_devplan.md` — cabeçalho + entrada de log `MAN-OFF26-10-11-REG`.
- `CLAUDE.md` — linha do blueprint `draft_import`.
- `handoff_code_manager_02_08_2026_pt3.md` — este arquivo.

---
---

# PARTE 2 — Achados empíricos da liga fantasma (mesma sessão, `MAN-OFF26-10-11-REG`)

> A parte 1 acima registrou os dois gaps a partir do calendário. Depois disso, **a liga fantasma
> foi criada de fato no Sleeper e submetida a experimento manual** — e o resultado **refutou
> premissas registradas** e **invalidou metade do runbook**. Esta parte cobre isso.
>
> **Mesma sessão, mesmo ID de prompt** → este handoff continua sendo o único (não foi criado pt4).

---

## 8. A sala existe

**Dynasty SB FA Auction** — Redraft · 12 times · draft **Auction** · budget **$200** · **22
rodadas** · roster espelhando a liga real (**3 WR**).

| item | estado |
|---|---|
| ambiente | board **vazio** *(estado na parte 2 — **repopulado depois**; ver §21)* |
| **RESET DRAFT** | ✅ **executado em 02/08/2026** — os 2 times da validação foram removidos |
| **`league_id`** | `1389725099556372481` |
| ~~`draft_id`~~ | ~~`1389725100684611584`~~ ☠️ **MORTO — ver parte 3** (atual: `1389755381567213568`) |

> Esta tabela registrava **duas pendências** quando a parte 2 foi commitada; **ambas foram
> resolvidas pelo owner na mesma sessão, logo depois** (`MAN-OFF26-IDS-REG`).
>
> ⚠️ **E o `draft_id` acima morreu horas depois** — o RESET DRAFT gera um draft novo a cada vez.
> **Ver §16 (parte 3).** O `league_id` continua válido.

Os dois ids são **distintos e não deriváveis um do outro por inspeção** — lidos das URLs da página
da liga e do draft board. Isso **reforça o precedente do `draft_import.py`** apontado no §1 da F1
do OFF26-4: passa-se o **`draft_id`** e **deriva-se** o `league_id` do objeto do draft; o caminho
inverso não é inspecionável. **Registrados só como dado** — nenhuma forma persistida (constante,
`AppConfig`, coluna), porque a parametrização é decisão de produto **ainda em aberto**.

> ⚠️ **O reset apagou o alvo dos probes.** As verificações pendentes — o que a API expõe
> **pré-draft** (OFF26-4 §2) e o que os picks expõem **pós-draft** (confirmação do
> `is_keeper:false`, OFF26-11) — **exigem repopular o board antes de rodar**. É **pré-condição das
> diagnoses**, não um passo dentro delas.

---

## 9. A refutação que mais muda o terreno

A diagnose **MAN-OFF26-4-F1** (18/06/2026) afirmou, em negrito, que a reserva de **$1 por slot
vazio** é *"regra interna do Manager, inexistente no Sleeper"*, e concluiu que a auditoria **não
pode** comparar `fa_budget`, devendo usar `raw_budget` ou Σ salários.

**Está refutado. O Sleeper aplica a mesma reserva.**

```
teto = 200 − gasto − (vagas_restantes − 1)
```

| tentativa (time com $150 gastos, 21 vagas livres → teto $29) | resultado |
|---|---|
| $40 | rejeitado — *"The specified slot does not have enough budget."* |
| $33 | rejeitado |
| $32 | rejeitado |
| **$29** | **aceito** |

E **sem falso positivo** no sentido oposto: 10 keepers somando **$140** (folga de $49) passaram
**sem nenhum aviso**.

**Consequências:**
- a base de comparação da auditoria é **`usable_draft_budget`** — o número que a keeper sheet
  **já entrega** —, e **não** `raw_budget`;
- a **decisão de produto 2** do OFF26-4 vira **RESOLVIDA POR EVIDÊNCIA**: não há o que arbitrar,
  as duas plataformas usam a mesma fórmula;
- o texto original da F1 ficou **preservado verbatim**, com bloco `ATUALIZAÇÃO EMPÍRICA` anexo
  (precedente DP1).

> ⚠️ **Pendência que sobra (aritmética, não experimento):** o Sleeper reserva sobre as **22
> rodadas** da sala; a regra **8.3.4** conta slots pelo **regulamento da liga**. **Se as contagens
> divergirem, os limites não coincidem apesar de a fórmula ser idêntica.** Não precisa de nova
> experiência — precisa de uma conferência que **não foi feita**.

---

## 10. O que mudou nos dois itens novos

**OFF26-10** — a questão que eu havia registrado de manhã como *probe* ("o Sleeper **pode**
recusar designação acima do budget") **foi confirmada**. Time acima do teto **não entra no board**.
Logo a **população escalonada é obrigatória, não alternativa**: enquadrados em 20/08, estourados
**só depois do late drop de 22/08**. E abre funcionalidade concreta — o Manager pode **pré-calcular
quais times ficarão bloqueados**, antes de o Cowork tentar.

**OFF26-11** — a designação de keeper carrega **`is_keeper: false`**, e a UI **toca o som de lance
vencedor**: o Sleeper trata a designação como **pick forçado de leilão**. Registrado **como
indício, não como fato** — a verificação definitiva é o que os picks expõem **pós-draft**, e o
draft não rodou. Se confirmar, o campo **não serve de discriminador** e este virá da **keeper sheet
como lista de exclusão**, o que **inclina sem decidir** a decisão em aberto para "Manager é fonte
única da verdade".

**As duas decisões em aberto continuam em aberto.** Nenhuma foi arbitrada.

---

## 11. O runbook estava descrevendo uma UI que não existe mais

O achado grave: **o caminho de entrada da Fase B não existe**. Não há engrenagem → Draft Settings →
*SET KEEPERS/DYNASTY PLAYERS* → *SET PLAYERS*. **O board já está em modo de designação** no
pré-draft — clica-se **direto na célula vazia**. Caçar o caminho fantasma foi a maior fatia dos
~9 min de overhead da transcrição cronometrada.

As 8 correções aplicadas em `runbook_cowork_liga_fantasma.md`:

| # | correção |
|---|---|
| 1 | caminho de entrada **não existe** → clicar direto na célula vazia (§B.1 reescrita) |
| 2 | clicar no **"+" da linha, nunca no nome** — o nome abre o perfil e fechá-lo **cancela o fluxo inteiro** |
| 3 | **K e DEF abaixo da dobra** → seta ▼ (o scroll do mouse não move o board) |
| 4 | K e DEF pelo **filtro de posição**, não digitando nome |
| 5 | o preço **já vem $1** → keepers de $1 não precisam de edição |
| 6 | **Ctrl+A rebaixado de alerta a nota** (100% dos casos) |
| 7 | **homônimo suavizado, não removido** — o pool só traz ofensivos elegíveis (Josh Allen LB/JAX nem aparece), mas dois ofensivos homônimos seguiriam ambíguos |
| 8 | nome correto: **Dynasty SB FA Auction** |

**Uma adição além das 8, que você deve conferir:** criei a seção **§B.3.2** com o **teto de lance**
e a **ordem escalonada**. Não estava na lista, mas sem ela o Cowork bate na recusa em 2026 e não
sabe o que fazer — e a resposta certa (**não baixar o salário para "caber"**, registrar o time como
bloqueado e seguir) não é óbvia. O runbook também ganhou 3 armadilhas novas e a referência de tempo
no TL;DR.

**Nota sobre a validação:** o runbook ainda menciona *"SET KEEPERS/DYNASTY PLAYERS → SET PLAYERS"*
em **3 pontos — todos como negação explícita** ("não existe", "não procure"). Apaguei o caminho
como **instrução**; mantive como **aviso**, porque quem já leu a versão anterior vai procurá-lo.
Se preferir a remoção literal, é rápido.

---

## 12. Quanto custa, e o que se decidiu por causa disso

**Medido, não estimado:** 1 time (10 keepers) = **20 min 32 s**, dos quais **~9 min de overhead
único** de descoberta do caminho. Regime: **~75 s/jogador ≈ 12,5 min/time → ~2,5 h para os 12
times**. Referência: a transcrição **manual** do ano anterior consumiu **uma tarde inteira**.

**Decisões registradas:**
- **2026 → Cowork**, com o runbook corrigido.
- **Script determinístico → melhoria para 2027.** O argumento que o justificaria — *"não cabe na
  janela de 48 h entre o late drop e o leilão"* — **cai** diante das 2,5 h medidas.
- **API interna não documentada → deliberadamente descartada.** Sem contrato, quebra sem aviso,
  provável violação de termos de uso, e **expõe a conta de comissário da liga real**.

> O item de 2027 ficou registrado **dentro da seção do OFF26-5**, e **não** como linha do Status
> Rápido — a restrição do prompt era de que só OFF26-10/11 entrassem. **É candidato natural a ID
> próprio** na próxima sessão de registro; se quiser, eu abro.

---

## 13. Nota de método

Metade do valor desta sessão veio de **premissas caindo**: uma diagnose read-only de junho (§5 do
OFF26-4) e um runbook escrito com contexto fresco em junho **descreviam ambos um Sleeper que não é
o de hoje**. O denominador comum: os dois foram produzidos **sem tocar a plataforma real** — a F1
raciocinou sobre o código do Manager e concluiu sobre o Sleeper; o runbook documentou a UI de uma
liga de teste descartável.

**Vinte minutos de experimento manual derrubaram os dois.** É uma quarta família de ocorrência do
`MAN-METH-REG`: premissa sobre **sistema externo** só se assenta **tocando o sistema externo**.

---

## 14. Arquivos alterados (parte 2)

- `improvements.md` — bloco `ATUALIZAÇÃO EMPÍRICA` no OFF26-4; achados nas seções do OFF26-10 e
  OFF26-11; correção do runbook + medição de esforço + decisão de método na seção do OFF26-5;
  anexo de UI-desatualizada no OFF26-6; dados da liga criada no registro do pacote; cabeçalho.
- `runbook_cowork_liga_fantasma.md` — 8 correções + §B.3.2 nova + armadilhas + TL;DR + cabeçalho.
- `manager_devplan.md` — cabeçalho + entrada de log (2ª parte).
- `handoff_code_manager_02_08_2026_pt3.md` — esta parte.

**Status Rápido: não foi tocado nesta parte** — segue com exatamente as duas linhas novas da
parte 1.

---
---

# PARTE 3 — 2ª execução do Cowork: runbook validado, `draft_id` instável, falso achado rejeitado

> `MAN-OFF26-RUNBOOK-REG-PT2` · 02/08/2026. **Onde esta parte divergir das anteriores, vale esta.**
> Em particular: **o `draft_id` registrado na parte 2 e no `MAN-OFF26-IDS-REG` está MORTO.**

---

## 15. O que a execução produziu

Segunda rodada no mesmo dia, agora **com o runbook corrigido** e com a lista de keepers
**pré-ordenada na sequência do board**:

| time | keepers | total | resultado |
|---|---|---|---|
| **Team 3** | 10 | **$148** | ✅ confere |
| **Team 4** | 8 | **$95** | ✅ confere |
| **Team 5** | 6 | **$60** | ✅ confere |

**O runbook corrigido foi validado** — o fluxo levou o agente ao fim três vezes, **sem
redescoberta de caminho**. **A medição de tempo foi perdida** (§19).

---

## 16. ⚠️ O `draft_id` não é estável — leia antes de usar qualquer id anotado

| campo | valor | estabilidade |
|---|---|---|
| `league_id` | `1389725099556372481` | **estável** |
| `draft_id` **atual** | `1389755381567213568` | ⚠️ muda a cada reset |
| ~~`draft_id` anterior~~ | ~~`1389725100684611584`~~ | ☠️ **MORTO** |

O **RESET DRAFT gerou um draft novo, com id novo**: o valor que registrei há poucas horas **morreu
no mesmo dia**. E **morre em silêncio** — a URL antiga **trava indefinidamente em LOADING**, sem
erro. Se um board não carregar, **a primeira hipótese é id velho**, não lentidão.

**Efeito sobre a decisão 1 do OFF26-4 — restrição, não arbitragem.** Continuo sem escolher entre
(a) parâmetro por chamada, (b) `AppConfig`, (c) coluna em Team. O que a evidência elimina é um
atributo **transversal às três**:

> **Qualquer alternativa que persista `draft_id` está descartada por evidência.** Persiste-se o
> `league_id`; o `draft_id` é **derivado a cada uso**.

**A confirmar antes de desenhar, não assumir:** o precedente do `draft_import.py` é a derivação
**inversa** (`draft_id → league_id`). O caminho necessário aqui é `league_id → draft_id`,
presumivelmente via `/league/{lid}/drafts` — endpoint **já usado no código** (`sync_sleeper.py:762`)
mas **nunca exercitado contra a fantasma**.

**Por que isso é pior do que parece:** um id persistido que morre em silêncio faz a auditoria
**pendurar em vez de errar** — e o momento em que isso aconteceria é **logo depois de um reset**,
ou seja, **na virada da intertemporada**, que é exatamente quando ninguém tem tempo de diagnosticar.

---

## 17. ⛔ O falso achado — e por que ele quase passou

O relatório do Cowork **recomendou rebaixar o check anti-homônimo**, alegando que a sigla NFL do
Sleeper diverge da keeper sheet (**Waddle exibido como DEN**, **Hill sem sigla**).

**Rejeitado. Nada foi aplicado.** A causa foi a **lista de teste**, montada à mão com **times de
temporadas anteriores** — **dado velho na lista**, não divergência da plataforma. Na execução real
a sheet sai do **Manager**, que **sincroniza do Sleeper**: mesma fonte dos dois lados, sigla bate.

**A orientação registrada é a inversa da recomendada:** se a sigla divergir **na execução real**,
isso é **sinal de problema no sync ou na sheet** → **parar e reportar**. O check da §B.3 ficou
**inalterado**, e a armadilha 4 do runbook agora carrega esse aviso.

**O que torna o caso instrutivo — e vale como nota de método:** *a observação era verdadeira*. A
sigla **de fato** divergiu. O erro não estava no que se viu, e sim em **de onde o dado vinha**.
Recomendação vinda de execução com **dados sintéticos** precisa ser conferida contra a **origem do
dado** antes de virar correção de documento — sem isso, **uma proteção teria sido enfraquecida na
véspera do uso real, com justificativa aparentemente empírica**.

---

## 18. As 5 correções de runbook (+1)

| # | correção | onde |
|---|---|---|
| 1 | **coluna com placeholders**: cabeçalhos são **avatares vazios sem rótulo**; a verificação canônica é o **menu de contexto** (*"…for Team N"*). Os **dois estados** documentados — a orientação "pelo owner" só vale com owners reais dentro | §B.2 |
| 2 | **o board reescala** após a 1ª interação → quebra referência posicional; revelar FLEX/K/DEF antes, confirmar o time pelo menu | §B.2 |
| 3 | **a vaga é atribuída por posição** (RB entra no FLEX quando RB está cheio) → clicar a célula exata é **conveniência, não obrigação** — desarma boa parte de (2) | §B.3.0 (nova) |
| 4 | **o preço nasce em `$1` sempre**, inclusive com `$PROJ` maior → regra **generalizada** a qualquer keeper de $1 | §B.3 |
| 5 | **filtro de K/DEF** mais rápido, e **já-designados somem do filtro** → "primeiro disponível" é limpo | §B.3 |
| +1 | **não fixar URL de board** — entrada por descoberta (liga → pré-draft → widget Draftboard → globo), com o aviso do LOADING | §B.1 |

---

## 19. A medição que se perdeu, e o risco que ela revelou

Tempos de relógio: Team 3 = **26min52s** (10) · Team 4 = **14min13s** (8) · Team 5 = **13min58s**
(6) · total **58min26s**. **Esses números não medem o procedimento:** o ambiente acumulou **dezenas
de timeouts de captura de tela, 30 s cada**.

**Por que é o ambiente e não o método:** o **Team 4 foi mais rápido por jogador que o Team 3** e o
**Team 5 voltou a subir** — por concentração de timeouts, não por regressão (curva de aprendizado
não sobe). E a execução anterior, **no mesmo dia**, **sem** runbook corrigido e **sem** lista
ordenada, rendeu **~75 s/jogador**. Não existe explicação plausível para que corrigir o documento e
pré-ordenar a lista **piorasse** o trabalho.

**O risco registrado é a variância, não a duração:** mesmo ambiente, resultados muito diferentes,
**sem causa identificada**. Projeção: **~2 h** em regime, **~5 h** numa execução degradada — e
**não há como saber qual será antes de começar**.

**Mitigação: fatiar a transcrição por time.** Cada time é uma **unidade verificável** (confira o
total ao fechar). Se a sessão degradar, a seguinte **retoma do time seguinte, sem refazer nada** —
o modo de falha é **lentidão, não erro**, então o feito continua válido.

**Efeito sobre Cowork-2026 / script-2027 — reconsideração parcial, aberta.** A decisão vigente
**não muda**. O argumento original do script ("não cabe em 48 h") **segue caído**. Mas surge um
argumento **novo**: o script determinístico **não tem esse modo de falha**. Contra-argumentos
**preservados**: seletores frágeis (a UI **já mudou uma vez** entre junho e agosto), competição de
prazo com OFF26-4 e OFF26-11 no caminho crítico, e **estreia no dia do uso** como pior cenário.

---

## 20. Melhoria do OFF26-2 registrada (não implementada)

A lista pré-ordenada **eliminou busca, deliberação e navegação** — a execução virou **descida linha
a linha**, e **6 dos 24 keepers dispensaram edição de preço** por serem de $1.

→ **Emitir a keeper sheet time a time, na ordem das linhas do board, marcando os keepers de $1.**
A sheet é o **artefato de handoff** para o único passo do calendário que roda **fora** do Manager;
ordená-la na sequência do consumidor é a diferença entre dados **corretos** e dados **operáveis**.
A ordem é **derivável** da config de roster que o runbook já exige espelhar — mas **confirmar
contra o board real** antes de fixar (a ordem exata de banco/FLEX não foi verificada).

---

## 21. Estado da liga e a janela que está aberta

Board **populado** com **Team 3/4/5** (dados de teste); Team 1 e 2 foram limpos pelo reset. **Novo
RESET DRAFT pendente** antes do uso real — e ele **trocará o `draft_id` outra vez**.

> ✅ **Janela aberta:** o board **está populado agora**, então serve de **alvo** ao probe pré-draft
> do **OFF26-4** e à verificação de designações — **desde que rodados ANTES do próximo reset**. A
> confirmação **pós-draft** do `is_keeper:false` (**OFF26-11**) exige **rodar um draft de teste**,
> o que o board populado torna possível.
>
> Ou seja: **há uma oportunidade com prazo**, e o prazo é o próximo reset.

---

## 22. Arquivos alterados (parte 3)

- `improvements.md` — ids atualizados + instabilidade do `draft_id` (bloco do pacote e OFF26-4,
  como **restrição de desenho** sobre a decisão 1); 2ª execução, falso achado, correções, variância
  e reconsideração parcial na seção do **OFF26-5**; melhoria de ordenação no **OFF26-2**;
  pré-condições dos probes atualizadas no **OFF26-4** e **OFF26-11**; cabeçalho.
- `runbook_cowork_liga_fantasma.md` — 5 correções + entrada por descoberta (§B.1) + §B.3.0 nova +
  armadilha 4 com o aviso invertido + TL;DR + cabeçalho.
- `manager_devplan.md` — cabeçalho + entrada de log.
- `handoff_code_manager_02_08_2026_pt3.md` — esta parte.

**Status Rápido intocado. Nenhum status alterado. Zero arquivo de código.**

---
---

# PARTE 4 — Spec do OFF26-4 (auditoria de keepers pré-leilão)

> `MAN-OFF26-4-REFINE` · 03/08/2026. **Sincronização de spec, não implementação** — o OFF26-4 segue
> **🔲**. **Onde as partes divergirem, vale a mais recente.**

---

## 23. O que esta parte fez

Registrou, na seção do OFF26-4, um bloco **"Spec final — decisões de produto arbitradas"** no padrão
do OFF26-2, com **D1 a D7**. A **F1 (18/06)** e a **ATUALIZAÇÃO EMPÍRICA (02/08)** ficaram
**intactas abaixo**, como terreno — a spec é camada nova acima delas, e é ela que a F2 lê.

**Cada decisão está rotulada pela sua natureza**, porque as três não têm o mesmo peso:

| | decisão | natureza |
|---|---|---|
| **D1** | `league_id` em `AppConfig`; `draft_id` derivado | **arbitrada** |
| **D2** | base de budget = `usable_draft_budget` | **resolvida por evidência** |
| **D3** | ponte de `sleeper_player_id` | **delegada à F2, com critério** |
| **D4** | 12 times de uma vez; não-populado = estado próprio | **arbitrada** |
| **D5** | 4 classes de divergência + 1 estado | **arbitrada** (severidade → F2) |
| **D6** | ponte de owner por `sleeper_owner_id` | **arbitrada** |
| **D7** | probe exige board populado | **pré-condição registrada** |

---

## 24. O detalhe que decidiu o D1: a auditoria roda mais de uma vez

Não é gate único. **Roda 3× ou mais** numa janela de 48 h — após a 1ª leva de população (**20/08**),
após o remendo do late drop (**22/08**) e possivelmente uma vez final antes de **24/08**.

É isso que derruba o parâmetro-por-chamada (o molde do OFF26-3): **recolar o id a cada execução é
oportunidade recorrente de colar o errado, exatamente quando ninguém tem tempo de conferir.** A
coluna em `Team` cai por outro motivo — é atributo **de liga**, não de time.

**E a restrição que vem da evidência de 02/08:** persiste-se **apenas o `league_id`**. O `draft_id`
**muda a cada reset** e é **derivado a cada uso** — nenhuma persistência, nem cache.

**Um requisito de robustez que nasce do modo de falha, e que vale destacar:** a URL de um draft
morto **trava em LOADING em vez de dar erro**. A falha é **indistinguível de lentidão**, então a
derivação precisa de **timeout explícito e mensagem própria**. Numa janela de 48 h, **uma auditoria
que pendura é pior que uma que falha** — a que falha você conserta, a que pendura você fica olhando.

🔲 **A F2 herda uma pendência de terreno:** o caminho `league_id → draft_id` existe no código
(`/league/{lid}/drafts`) mas **nunca foi exercitado contra a fantasma**, e o precedente do
`draft_import.py` é a derivação **inversa**. Confirmar antes de construir sobre ele.

---

## 25. Duas restrições que limitam o que a F2 pode validar

**(a) D6 — a ponte de owner não tem como funcionar hoje.** Os **convites foram disparados em
03/08**, mas os times **ainda são placeholders**, com **`owner_id` nulo**. Enquanto for assim, a
auditoria **não consegue casar coluna e time**. → **A F2 não pode ser validada contra board de
placeholders.** Registrei isso também no bloco de estado da liga, no registro do pacote, para que
não seja descoberto no meio da F2.

**(b) D7 — o probe tem janela com prazo.** O §2 da F1 segue pendente (nada no código lê estado
pré-draft) e o probe **exige board populado**. Ele **está populado agora** (Team 3/4/5, dados de
teste — alvo válido), mas a janela **fecha no próximo RESET DRAFT**, já pendente, que **zera o
board e troca o `draft_id`**.

> As duas juntas descrevem uma tensão real: **o probe quer o board como está agora; a F2 quer o
> board com owners reais.** O reset fica no meio. Não arbitrei a ordem — é decisão do owner, e
> depende de quando os convites forem aceitos.

---

## 26. O que a spec deliberadamente NÃO decide

- **severidade** de cada classe de divergência (D5) → F2;
- **forma de exposição** do `sleeper_player_id` — payload × re-query (D3) → F2, com o critério
  "**preferir o caminho que não toque o OFF26-2**", que segue ⚠️ aguardando smoke;
- **extração** do helper de ponte de owner para local compartilhado (D6) → F2;
- **conferência aritmética** da ressalva do D2 — o Sleeper reserva sobre as **22 rodadas da sala**,
  a regra **8.3.4** conta pelo **regulamento**; se divergirem, os limites não coincidem apesar da
  fórmula idêntica. **Não depende de acesso à plataforma** — depende de conferir regulamento ×
  config, e **não foi feito**.

---

## 27. Arquivos alterados (parte 4)

- `improvements.md` — bloco de spec **D1–D7** na seção do OFF26-4 (acima da F1, que ficou íntegra);
  estado dos owners (placeholders, `owner_id` nulo) no bloco de estado da liga; cabeçalho.
- `manager_devplan.md` — cabeçalho + entrada de log.
- `handoff_code_manager_02_08_2026_pt3.md` — esta parte.

**Status do OFF26-4: 🔲 (inalterado). Status Rápido intocado. Nada do OFF26-2 alterado. Zero
arquivo de código.**

---
---

# PARTE 5 — Probe read-only do pré-draft: o bloqueador do OFF26-4 caiu

> `MAN-OFF26-4-PROBE` · 03/08/2026. **Read-only estrito:** zero escrita, **draft NÃO iniciado**,
> nenhum reset, **board intacto** ao fim. **Onde as partes divergirem, vale a mais recente.**

---

## 28. O resultado em uma frase

O §2 da F1 dizia que *"nada no código lê o estado pré-draft, e o que a API expõe é questão
empírica"*. **A API expõe tudo o que a auditoria precisa — designação, jogador, time e VALOR.**

O que impedia **não era a API**: era o **gate `status == "complete"`** nos dois consumidores de
picks do projeto. **A F1 estava certa na causa e incompleta no efeito.**

---

## 29. Respostas P1–P6

| | pergunta | resposta |
|---|---|---|
| **P1** | derivação `league_id → draft_id` | ✅ **funciona, por 2 caminhos** — `league.draft_id` no topo (1 request) e `/drafts` com 1 item; **o morto não aparece** |
| **P2** | designações pré-draft | ✅ **`GET /draft/{did}/picks` com `status: pre_draft`** — 24 registros, **mesma superfície que o projeto já usa** |
| **P3** | salário | ✅ **`metadata.amount`** (string) — **totais $148/$95/$60 reconstruídos exatos** |
| **P4** | identidade | jogador = `player_id` (= `sleeper_player_id`); time = `roster_id`; **`owner_id` nulo em 11/12** |
| **P5** | budget por time | ❌ **não existe campo** — só `budget: 200` global → **derivar por soma** |
| **P6** | réplica | ⚠️ **dupla** — `draft_import.py:39` e `sync_sleeper.py:872`, com coerções diferentes de `amount` |

**Verificação concreta:** os três totais saíram do payload **exatos**, e o Team 3 confere 10/10
nominalmente. Inclusive **Waddle = DEN — que vem do próprio Sleeper**. Isso fecha um ciclo: é a
confirmação independente de que a divergência de sigla relatada na 2ª execução do Cowork era **da
lista de teste**, e de que **rejeitar aquele falso achado foi a decisão certa**.

---

## 30. ⛔ Uma premissa do D1 caiu — e é boa notícia

O REFINE registrou, como requisito de robustez, que *"a URL de um draft morto trava em LOADING em
vez de dar erro"*, tornando a falha indistinguível de lentidão.

**Pela API isso é falso:** `GET /draft/{morto}` → **404, corpo `null`, 0,2 s**. O LOADING infinito é
comportamento do **app web**. **Pela porta que a auditoria vai usar, esse modo de falha não
existe** — morto × vivo se distingue de imediato.

O requisito de timeout continua sendo boa prática (o `_get` do projeto já tem `timeout=15`), mas
**deixa de ser mitigação de um risco real**. **O essencial do D1 — não persistir `draft_id` —
permanece intacto**, e agora com o caminho de derivação comprovado.

---

## 31. Três achados que mexem na spec

**(a) O D5 precisa de ajuste — não existe classe "slot errado".** `pick_no` e `round` **não
indicam vaga de roster**: as 24 designações ocupam `pick_no` 1..24 na ordem de criação (as 10 do
Team 3 são 1-10, todas `round=1`, num draft de 12 times). O payload traz a **posição do jogador**,
nunca a **vaga que ele ocupa**. → A auditoria verifica **presença, valor e time**; **alocação de
vaga não é auditável**.

**(b) A ressalva aritmética do D2 tem agora metade da conta medida.** `roster_positions` da fantasma
= **22 slots** (`QB,RB,RB,WR,WR,WR,TE,FLEX,K,DEF` + 12 `BN`). Falta o lado do regulamento (8.3.4).
**E apareceu um caso concreto:** a **fantasma não tem slot de IR**, enquanto a liga real tem (máx.
2) e o **D5 do OFF26-2** manda **contar IR normalmente** no budget. A divergência de contagem
deixou de ser hipótese.

**(c) O D6 se confirma, mas com um deslocamento de premissa.** `owner_id` é nulo em 11 dos 12
rosters — a F2 segue **não validável contra placeholders**. **Porém a auditoria não precisa de
`owner_id` para casar designação e time**: a pick **já vem chaveada por `roster_id`**. O `owner_id`
é necessário para casar **`roster_id` ↔ time do Manager** — outra coisa, e é só isso que o D6 trava.

---

## 32. Dois detalhes que vão morder quem implementar

- **⚠️ DEF tem `player_id` NÃO-NUMÉRICO:** `L. Rams` vem como **`"LAR"`**, sigla do time. Qualquer
  coerção a `int` quebra em defesas.
- **⚠️ `league.settings.draft_rounds = 3` × `draft.settings.rounds = 22`** — homônimos, valores
  diferentes, níveis diferentes. **Ler o do objeto do DRAFT.**
- Bônus: **`is_keeper: false` nas 24** — o indício do OFF26-11 ganha evidência de payload
  pré-draft. **Não é a confirmação definitiva**, que é pós-draft e ficou fora do escopo.
- Bônus 2: `copy_from_league_id` aponta para a **liga real** — a fantasma nasceu **por cópia**, o
  que explica o 3 WR.

---

## 33. O que fechou, o que segue aberto

**Fechou:** D7 (probe executado) · pendência herdada do D1 (derivação funciona) · premissa do
LOADING (refutada para a API) · **§2 da F1** (o bloqueador do item).

**Segue aberto:** ressalva aritmética do D2 (falta o regulamento) · D6 (placeholders) · D3 (decisão
da F2) · confirmação **pós-draft** do `is_keeper` (OFF26-11) · **e o D5 precisa do ajuste do §31a**.

> **A F2 do OFF26-4 está desbloqueada do lado da LEITURA.** O que ainda a limita é **validação**,
> não construção — e a **janela do D7 continua fechando no próximo RESET DRAFT**.

---

## 34. Arquivos alterados (parte 5)

- `improvements.md` — bloco `PROBE read-only do estado pré-draft` na seção do OFF26-4 (abaixo da
  spec e da restrição de desenho, acima do OFF26-5), com P1–P6, refutação de premissas e a tabela
  de "fecha × segue aberto"; cabeçalho.
- `manager_devplan.md` — cabeçalho + entrada de log.
- `handoff_code_manager_02_08_2026_pt3.md` — esta parte.

**Nenhum arquivo de código. Status Rápido intocado. OFF26-4 segue 🔲.** Os scripts do probe ficaram
no scratchpad da sessão, fora do repositório.

---
---

# PARTE 6 — Keeper fora do board é leiloável; a spec absorve o probe

> `MAN-OFF26-4-REFINE-PT2` · 03/08/2026. **Sincronização de spec + registro.** Sem código, sem F2.
> **Onde as partes divergirem, vale a mais recente.**

---

## 35. ⛔ O achado — e por que ele é o de maior peso do arco OFF26

**Um keeper que não esteja designado no board é, para o Sleeper, JOGADOR DISPONÍVEL.** Qualquer
owner pode nomeá-lo, e o leilão **processa o lance normalmente** — a plataforma **não tem como
saber** que ele já tem contrato vigente. O resultado é **um jogador com dono sendo arrematado por
outro time, ao vivo**, e o OFF26-3 ingerindo depois **como aquisição legítima**.

> **Não é erro de contabilidade que a auditoria corrige depois. É transação inválida em tempo real,
> sem forma limpa de desfazer sem interromper o leilão.**

Toda a modelagem anterior do OFF26-4 tratava divergência como **contabilidade a reconciliar**. Esta
classe **não se reconcilia**: quando ela se manifesta, o lance já foi dado e desfazer significa
**parar o leilão com 12 owners na sala**.

**→ O OFF26-4 deixa de ser conferência de cap e passa a ser GATE DE INTEGRIDADE DO LEILÃO.**

---

## 36. Onde o risco fica agudo: o encontro com o OFF26-10

O OFF26-10 já registrava que **times acima do teto não conseguem ser populados** até o late drop.
Junte com o achado:

> **Enquanto um time permanece bloqueado, TODOS os keepers dele estão expostos ao leilão.**

**→ População completa do board é PRÉ-CONDIÇÃO DE ABERTURA, não preparativo.** Abrir o leilão com
qualquer time não populado expõe os keepers dele.

**A decisão em aberto do OFF26-10 continua em aberto** — isto é registro de consequência, não
arbitragem. Mas qualquer desenho que saia dela **tem de terminar com o board 100% populado antes de
24/08**, e a janela 22/08 → 24/08 é curta.

**No runbook** entrou a **§B.5**, com o mesmo peso: *board incompleto não é estado aceitável para
iniciar o leilão*. O runbook já dizia "não clicar em START DRAFT até tudo estar populado" — o que
mudou é que aquilo era **higiene de processo** e agora é **integridade do leilão**. Fechei também o
loop no §B.3.2: time bloqueado **não pode ficar assim até o leilão**.

---

## 37. IR resolvido — e a alternativa que parecia equivalente não era

A liga real tem slot de IR; a fantasma **não tem nenhum** (22 = 10 titulares + 12 BN).

**Resolução do owner: designar o keeper em IR normalmente.** Excedentes caem no **banco**, vaga
**automática por posição**. Três efeitos: sai do pool disponível, consome budget corretamente, fica
visível à auditoria.

**A alternativa descartada merece registro porque parecia razoável:** descontar o valor do keeper em
IR do budget do time. Não resolve — **o problema não é o dinheiro, é a disponibilidade do jogador**.
Descontar budget deixa o keeper **no pool, leiloável**. E ainda ficaria **invisível para a
auditoria**, que deriva budget **por soma das designações** (a API não expõe budget por time — P5 do
probe).

---

## 38. O que mudou em cada decisão da spec

| | mudança |
|---|---|
| **D1** | 🔧 **corrigido, texto anterior preservado** — a "falha silenciosa" **não existe pela API** (404 em 0,2 s; o LOADING é do app web). **Timeout rebaixado de mitigação de risco a boa prática.** **A proibição de persistir `draft_id` permanece intacta**, e a derivação está comprovada em **1 requisição** |
| **D2** | metade **fechada** (sala = **22 slots**, medido); **8.3.4 segue pendente**, agora com o **caso concreto do IR**. +aritmética nova: nenhum time pode exceder **22 keepers** |
| **D5** | classe "slot errado" **não existe** — e **não precisa**: atribuição é automática por posição. **Severidade da classe 1 deixa de ser escolha da F2** (é bloqueante) |
| **D6** | **afrouxado com precisão** — `owner_id` nulo em 11/12 **não bloqueia**; designações vêm por `roster_id`. **Construção e validação parcial liberadas contra placeholders**; só a **costura `roster_id` ↔ time** espera os aceites |

**Armadilhas registradas para a F2:** `player_id` de **DEF é sigla** (`"LAR"`) — coerção a inteiro
quebra; e **`draft_rounds` da liga ≠ `rounds` do draft** — ler a do draft.

---

## 39. Nota de método: a terceira premissa da mesma família, na mesma sessão

As três caíram pelo **mesmo mecanismo — observação verdadeira, procedência errada**:

| # | premissa | a observação era… | a procedência era… |
|---|---|---|---|
| 1 | sigla NFL diverge da sheet | verdadeira | **lista de teste** com temporadas velhas |
| 2 | reserva de $1/vaga é só do Manager | verdadeira sobre o Manager | concluída sobre o **Sleeper sem tocar o Sleeper** |
| 3 | URL de draft morto trava em LOADING | verdadeira | comportamento do **app web**, generalizado para a **API** |

> **Padrão a vigiar: comportamento observado numa superfície NÃO vale como propriedade de outra.**
> Web ≠ API; lista de teste ≠ dado de produção; regra do Manager ≠ regra da plataforma.

Nos três casos a evidência era real e o que falhou foi a **inferência de escopo** — e nos três a
correção veio de **tocar a superfície certa**. Vale a pena notar que a nº 1 quase enfraqueceu uma
proteção, e a nº 3 quase gerou um requisito de robustez contra um risco inexistente: **os dois
sentidos do erro**.

---

## 40. Arquivos alterados (parte 6)

- `improvements.md` — requalificação da natureza do OFF26-4; correção do **D1** (texto anterior
  preservado); **D2** meio fechado; ajustes de **D5** e **D6**; bloco novo do achado + resolução do
  IR + armadilhas + nota de método; **propagação ao OFF26-10 e ao OFF26-5**; reforço de evidência no
  OFF26-11; cabeçalho.
- `runbook_cowork_liga_fantasma.md` — **§B.5 nova** (board incompleto não é aceitável), **§B.3.3
  nova** (keeper em IR), fechamento do loop no §B.3.2, TL;DR item 16 e cabeçalho.
- `manager_devplan.md` — cabeçalho + entrada de log.
- `handoff_code_manager_02_08_2026_pt3.md` — esta parte.

**Status de OFF26-4, OFF26-10 e OFF26-5 inalterados. Status Rápido intocado. Zero arquivo de
código.**

---

# PARTE 7 — A costura de owner da liga fantasma casa 8/8

> Sessão `MAN-OFF26-4-OWNERCHECK` (03/08/2026, Opus). **Verificação read-only + registro.** Zero
> escrita dos dois lados: API só `GET`, `dynasty.db` aberto em `mode=ro`. Draft **não iniciado**,
> **RESET DRAFT não executado**, board **intacto**. Scripts transitórios rodados no scratchpad,
> **não commitados**. Nenhuma rota, schema, template ou teste criado.

## 41. O resultado em uma frase

A **última incógnita do D6** — se `owner_id` da fantasma casa com `Team.sleeper_owner_id` do
Manager — foi exercitada **com owners reais pela primeira vez** e **casou 8 de 8, sem nenhum
não-casamento**.

| roster | `owner_id` | display (fantasma) | Team do Manager |
|---|---|---|---|
| 1 | `1130162144764506112` | MellowBR | #5 Cangaceiros da Colina |
| 2 | `695859519976210432` | rafadgil | #1 Pitbull do Samba |
| 3 | `695859970096328704` | TropadoJarra | #9 Tropa do Bicampeonato 🏆 |
| 4 | `205848303030505472` | icarocosta1 | #4 mongoloides |
| 5 | `1133812910268010496` | rafaelferreirap | #11 rafaelferreirap |
| 6 | `1129822349391470592` | fernandoxmf | #3 Fazenda Pederasta |
| 7 | `1131747074137272320` | murilofborges | #6 Miller Time! |
| 8 | `1133818177651224576` | LeoFBorges1 | #12 ESPN FANTASY LEAGUE |
| 9–12 | *(nulo)* | — | — |

## 42. ⚠️ O estado esperado divergiu: 8, não 7

O prompt esperava **7 aceites** e a API expôs **8** — `LeoFBorges1` (roster 8) entrou **entre a
leitura de tela do owner e a leitura da API**. Divergência benigna e na direção boa, mas o registro
importa:

> **A contagem de aceites muda entre uma olhada e a seguinte. A auditoria da F2 tem de ler, não
> assumir** — inclusive quando o número "já se sabe".

## 43. Por que este resultado não depende do banco local

A conferência rodou contra o `dynasty.db` de dev, que é o seed do git e pode estar defasado do
`/data/dynasty.db` de produção. Isso **não enfraquece o resultado**, porque o conjunto de ids foi
fechado contra a **API ao vivo**:

- os **12** `sleeper_owner_id` do Manager são **idênticos** aos **12** `user_id` da liga real
  (`manager − real = ∅` **e** `real − manager = ∅`);
- os **8** `owner_id` da fantasma são **subconjunto** desse conjunto.

Ou seja, o casamento se verifica **contra o Sleeper**, não contra o estado do banco. E confirma a
propriedade que sustenta o D6: **`owner_id` é identidade de CONTA — não de time, não de liga.** A
mesma conta atravessa as duas ligas com o mesmo valor.

## 44. O D6 fecha? Não — e a distinção importa

**Fechou:** a dúvida sobre *se a chave casa* (casa, 8/8) e a "última incógnita" como **risco de
desenho**. A F2 pode escrever a costura confiando na chave.

**Segue aberto:** **cobertura.** 4 rosters (9–12) com `owner_id` nulo, que **nenhuma leitura
resolve** — dependem de aceite. Times do Manager ainda sem owner na fantasma:

| Team | owner | `sleeper_owner_id` |
|---|---|---|
| #2 3 peat… of pain 🫠 | fertorquato | `732411754436526080` |
| #7 AlexTheDawg | freddupont | `698015187109773312` |
| #8 Trust The Process | michelzela | `1126909140380569600` |
| #10 🕯️🕯️ achane 🕯️🕯️ | gabrieldiinis | `867557566065045504` |

**Efeito colateral útil:** essa lista — *quem falta cutucar* — antes só existia olhando a tela.

**E há um caso que a F2 vai encontrar:** **coluna sem owner não é atribuível a time nenhum**,
distinto de "time não populado" (D4). Onde ele cai nas classes do D5 é decisão da F2; aqui ficou
registrado apenas que **o caso existe e foi observado**.

**Perspectiva:** pelo achado da PARTE 6 ("keeper fora do board é jogador leiloável"), esses 4
placeholders **já são bloqueantes de abertura por outro motivo**. **A costura não é o gargalo.**

## 45. 📌 O reforço da regra — que a medição rendeu de quebra

A regra **não mudou**: casamento **só** por `sleeper_owner_id`, **nunca** por nome. O que mudou é a
força do porquê — são **dois motivos independentes**, não um.

**Motivo 1 — instabilidade no tempo** *(já registrado)*: `Team.name` é mutado pelo sync. **Evidência
nova:** o Manager guarda `Tropa do Bicampeonato 🏆`; a liga real **hoje** exibe `Tropa do Jarra 🏆`.
O nome **já divergiu, sozinho**.

**Motivo 2 — espaços de nome SEPARADOS** *(novo, e mais fundamental)*: nada vincula o nome usado na
fantasma ao usado na real. Ele pode **nascer diferente e permanecer diferente para sempre**, sem
mutação nenhuma.

> Não é uma dessincronização a corrigir. **São dois namespaces** — casá-los é **erro de categoria**,
> não erro de atualização. O motivo 1 sugere "então mantenha sincronizado"; o motivo 2 fecha essa
> saída.

**Evidência de campo, medida:**

- **`metadata.team_name` é `None` nos 8 owners da fantasma — 8/8.** Enquanto ninguém batiza o time,
  a coluna exibe **username** (`rafadgil`, `fernandoxmf`). Durante boa parte da preparação **não
  existe nome de time para casar**: um casamento por nome não erraria — **não teria com o que
  trabalhar**.
- **Dois Rafas** entre os owners reais: `rafadgil` e `rafaelferreirap`. Colisão por nome é risco
  **concreto**, não hipotético.
- **`rafaelferreirap` não tem `team_name` nem na liga real** → o Manager guarda o **username** como
  `Team.name` (#11). Um cruzamento por nome acertaria esse caso **por coincidência de fallback**,
  não por identidade — **o pior tipo de acerto, porque valida a técnica errada.**

**Para quem ler isto no futuro:** ver nomes coincidentes nas duas telas **não** autoriza simplificar
a regra. A coincidência é acidente do momento; a identidade é o `owner_id`.

## 46. Nota de método

Três premissas "óbvias" caíram nas 24 h anteriores (PARTE 6, §39), todas por **procedência de
dado**. Esta **não caiu** — mas só se sabe disso porque foi **medida**. E a medição rendeu, de
quebra, o **motivo 2** do §45, que **nenhum raciocínio sobre a regra teria produzido**: ele só
apareceu porque alguém foi ler o campo `team_name` e o encontrou vazio doze vezes.

> Verificar uma premissa que se confirma **não é tempo perdido** — o retorno costuma vir pelo dado
> vizinho que ninguém tinha pensado em olhar.

## 47. Arquivos alterados (parte 7)

- `improvements.md` — bloco de conferência da costura + bloco de reforço da justificativa, ambos
  junto ao **D6** da spec do OFF26-4; cabeçalho.
- `probe_liga_fantasma.md` — nota em "o que este script ainda NÃO faz": a costura foi conferida à
  parte; o bloco `[P4]` vira **medição de cobertura**.
- `manager_devplan.md` — entrada de log.
- `handoff_code_manager_02_08_2026_pt3.md` — esta parte.

**Nenhum status alterado. Status Rápido intocado. Zero arquivo de código.**

---

# PARTE 8 — F2: a auditoria de keepers existe como código

> Sessão `MAN-OFF26-4` (03/08/2026, Opus). **Implementação em escopo único: leitura, diff e
> apresentação.** Read-only do lado da plataforma (só `GET`), draft **não iniciado**, **RESET DRAFT
> não executado**, board **intacto**. Status do OFF26-4: **🔲 → ⚠️** — não fecha ✅ sem smoke em
> produção, e a **sheet real só nasce em 20/08**.

## 48. O que existe agora

| arquivo | papel |
|---|---|
| `keeper_audit.py` | núcleo **puro** `audit(board, sheet)` + camada de leitura read-only |
| `keeper_audit_fixtures.py` | material de teste **congelado** (⛔ não é a sheet real) |
| `keeper_audit_test.py` | **29 testes**, sem Flask, sem banco, sem rede |
| `templates/keeper_audit.html` | relatório dos 12 de uma vez, veredito no topo |
| `routes/admin.py` | `/admin/keeper_audit`, `/api/admin/keeper_audit`, `POST /api/admin/phantom_league` |
| `app.py` | seed do `phantom_league_id` no `AppConfig` (D1) |

O núcleo segue a separação do `salary_engine`: **a lógica é pura e é ela que os testes exercem**;
rede e banco ficam na borda. É o que permite testar o diff **antes de existir sheet real**.

## 49. Veredito, não lista

A tela abre com **ABERTURA LIBERADA / BLOQUEADA** e os motivos. **Zero divergências não libera** —
bloqueiam:

- **keeper exposto** (classe 1 — a que não é escolha de desenho);
- **time não populado** (não é divergência, mas os keepers dele estão igualmente expostos);
- **time sem coluna** (convite não aceito);
- **coluna órfã** (não atribuível a time nenhum);
- **keeper sem `sleeper_player_id`** (auditoria incompleta para aquele jogador).

Isso é a requalificação do item virando comportamento: **gate de integridade, não conferência de
cap**. Um relatório que dissesse "0 divergências" com 9 colunas vazias estaria tecnicamente correto
e operacionalmente perigoso.

## 50. As decisões que a spec delegou

- **D3 — re-query, não payload.** `build_sheet` consome `_build_keeper_sheet` (fonte única do
  OFF26-2) e enriquece com `sleeper_player_id` consultando `Player`. **O OFF26-2 não foi tocado**,
  como o critério do owner mandava — ele segue ⚠️ aguardando smoke, e não ganhou risco novo.
- **D5 — severidade relativa:** `time_errado` e `salario_divergente` **alta**, `fora_da_sheet`
  **média**. A da classe 1 não era escolha.
- **Ordenação pior-primeiro.** Sob prazo, ninguém rola a página.

## 51. ⚠️ Sete divergências entre spec e terreno — relatadas, não resolvidas por conta própria

1. **O helper do D6 não tinha o que reusar.** `_team_by_roster` **consulta o banco** por roster; o
   núcleo puro casa `owner_id` ↔ time **em memória**, com dado que os dois lados já carregam. Não
   houve réplica nem extração. **A invariante do D6 foi cumprida — o meio previsto é que não se
   aplicava.**
2. **A spec previa UM estado; o terreno tem DOIS.** Time cujo owner não está em coluna nenhuma não
   é "coluna vazia": **não é auditável nem populável**. Estado novo `sem_coluna` — é a cobertura do
   D6 aparecendo como estado de relatório.
3. **"Coluna sem owner" ganhou tratamento, e é o inverso do (2).** Balde próprio; **nunca** conta
   como divergência de um time. Mesmo balde recebe coluna **com** owner sem time no Manager.
4. **Keeper sem `sleeper_player_id` não estava previsto.** Não é divergência — é **limite de
   insumo**. Vira aviso, entra em `unresolved_keepers` e bloqueia por **auditoria incompleta**.
   Cair para nome está proibido ("Brown"); **silenciar seria pior que acusar**.
5. **Budget: exibido, não diferenciado.** A base do D2 está certa e vem da sheet, mas diferença de
   soma **não virou classe** — é consequência das classes 1-4, e virá-la achado produziria
   exatamente a **quarta divergência** que a fixture B existe para proibir.
6. **A ressalva das 22 rodadas virou verificação automática** pelo lado da sala (aviso se um time
   trouxer mais keepers que `rounds`). O lado do **regulamento 8.3.4 segue pendente** — não é
   código.
7. **O timeout do D1 já existia.** `ss._get` traz `timeout=15`. Medido de novo: **id morto → erro
   em 0,21 s**, com mensagem citando o RESET DRAFT.

## 52. A fixture que estava errada — e a auditoria que estava certa

A primeira fixture "coerente" acusou **18 falsos `time_errado`**. A causa não era o diff: os **24
jogadores do board** estavam **espalhados pelos elencos reais** dos outros times, porque o board foi
populado a partir de uma **lista de teste**, não dos elencos daqueles três times. A auditoria estava
dizendo a verdade — **o jogador estava em dois lugares**. Corrigida a geração (os 24 pertencem aos
três times populados e a mais ninguém), a fixture A fecha em zero.

> Vale como método: **quando o instrumento acusa muito, a primeira hipótese não é "o instrumento
> exagera" — é "o material está errado".** Foi o mesmo mecanismo do falso achado de 02/08 (dados
> sintéticos quase enfraqueceram uma proteção), agora na direção contrária e pego a tempo.

## 53. A fixture B não cobre a classe mais grave

Os três erros pedidos — salário, keeper removido da sheet, jogador no time errado — são das classes
**2, 3 e 4**. **A classe 1 (bloqueante) não está entre eles**, porque "remover da sheet" deixa o
jogador **no board** (classe 4), e a classe 1 é o inverso. Sem uma fixture dirigida, **a classe que
governa a natureza do item ficaria sem teste**. Criada a **C**, mais duas: **coluna sem owner**
(terreno real de hoje) e **keeper sem sid** (com **dois Brown** — exatamente o caso que um fallback
por nome estragaria).

O teste que mais importa na B é o do **time errado contar UMA vez**: um diff ingênuo o contaria
duas ("ausente lá" + "sobrando cá") e entregaria a quarta divergência que denuncia auditoria que
inventa.

## 54. Validação

- **29/29** testes novos; **48/48** do `salary_engine` intactos.
- **Board REAL atravessando o núcleo inteiro:** `draft_id` derivado do `league_id`, **24
  designações** com `status=pre_draft`, **`rounds=22` lido do draft**, **3 colunas sem owner** →
  cruzado com a fixture A: **0 divergências, 3 `sem_coluna`, 3 órfãs**.
- **Sem sheet real (janela não revelada em localhost): a auditoria diz isso** e devolve **0 times**.
  É o caminho que a tela mostra hoje — **não 12 falsos positivos**.
- **`draft_id` não persistido em lugar nenhum** (grep): variável local, URL e tela.
- Board intacto, draft não iniciado, **nenhuma escrita na plataforma**. `git diff` **não toca**
  `salary_engine`, schema de cortes, `sync_sleeper` nem a keeper sheet. `dynasty.db` **não foi
  alterado** (o smoke rodou sobre cópia).

## 55. O que fica pendente

- **Smoke em produção (PROC1)** — o item **não fecha ✅** com localhost.
- **A auditoria nunca rodou com os DOIS lados reais.** O lado Manager foi sempre fixture; a sheet
  real só existe **a partir de 20/08**.
- **Cobertura do D6 aberta: 3 dos 12 times sem coluna.** Eram **4 de manhã e 3 à tarde** —
  `fertorquato` entrou entre duas leituras da **mesma sessão**. **Terceira leitura, terceira
  contagem** (7 esperados → 8 → 9 owners). Por isso a contagem é campo do relatório, nunca
  constante.
- **Ressalva aritmética do D2 pelo lado do regulamento (8.3.4).**
- Nada disso bloqueia a construção — bloqueia o **✅**.

## 56. Arquivos alterados (parte 8)

- **Novos:** `keeper_audit.py`, `keeper_audit_fixtures.py`, `keeper_audit_test.py`,
  `templates/keeper_audit.html`.
- **Alterados:** `routes/admin.py` (3 rotas), `templates/admin.html` (card), `app.py` (seed do
  `phantom_league_id`), `CLAUDE.md` (seção nova + estrutura + comando de teste),
  `improvements.md` (seção F2 + linha do Status Rápido + cabeçalho), `manager_devplan.md`,
  este handoff.

**Status do OFF26-4: ⚠️ (era 🔲). Nenhum outro item alterado.**

---

# PARTE 9 — O smoke de produção, e o ponto que ele não alcançava

> Sessão `MAN-OFF26-4-META` (03/08/2026, Opus). Correção de **borda e apresentação** nascida do
> smoke. Núcleo, veredito e classes **intocados**. Read-only; draft não iniciado; board intacto.

## 57. O smoke fechou 3 de 4 — e o que faltou era o único que importava provar em prod

Passaram: a rota responde e renderiza, o card do `/admin` leva à página, e o `phantom_league_id` foi
**semeado no `AppConfig` de produção** pelo boot.

**Não passou porque não era alcançável:** a auditoria bloqueia por ausência de sheet **antes** de
exibir qualquer coisa, então o bloco de meta não renderizava. A ordem era coerente — sem os dois
lados não há diff. A consequência não era: ficava sem prova **que o Render alcança a API do
Sleeper** e que a **derivação do `draft_id` funciona de lá**.

> Esses são modos de falha de **ambiente** — egress bloqueado, DNS, timeout de plano. **Nenhum
> aparece em localhost**, e todos apareceriam **em 20/08**, no dia em que a auditoria precisa
> funcionar. **Buraco de validação, não bug.**

## 58. ⚠️ E antes disso: os commits do dia estavam locais

O deploy vivo era o de **02/08**. Os 10 commits desta jornada — os nove de registro e o `d83d2f8`
com a auditoria — **nunca foram empurrados**. O auto-deploy dispara no **push**, e não houve push.

**O que salvou foi tentar o smoke.** Não fosse a tentativa, a descoberta seria em 20/08 — junto com
tudo o mais que só produção mostra. Fica como regra da sessão: **commit não é deploy**.

## 59. A correção foi menor que o diagnóstico

O `run_audit` **já lia os dois lados de forma independente**, e o `_no_input` **já carregava** a
meta no payload. Faltavam exatamente duas coisas:

1. a meta **carregar o suficiente** — designações lidas e colunas com dono × sem dono;
2. o template **renderizá-la fora do `{% if report.ok %}`**.

Nada no caminho do diff foi tocado. As fixtures A, B e C dão o mesmo resultado de antes.

## 60. Erro de liga virou estado próprio

Falha ao ler a liga **não se confunde** com bloqueio por falta de sheet: o veredito continua dizendo
o que falta de insumo, e o bloco diz o que houve com a liga. Exercido em render real:

| cenário | resultado |
|---|---|
| `league_id` válido, sem sheet | bloqueio **e** meta preenchida (`pre_draft`, 22 rodadas, 24 designações, selo "derivado") |
| `league_id` inválido | erro próprio, **HTTP 200 em 0,29 s** — sem pendurar, sem 500 |
| `league_id` vazio | "não configurada", sem exceção |

`run_audit` ganhou guarda contra exceção de rede/parse fora do que o `_get` já absorve.

## 61. Quarta leitura, quarto número

**7 esperados → 8 → 9 → 10 colunas com dono** — quatro contagens no mesmo dia, duas colunas ainda
sem dono. É a mesma lição de manhã, agora virando produto: **a contagem é campo do relatório, nunca
constante**, e o bloco novo a mostra ao vivo.

## 62. Arquivos alterados (parte 9)

- `keeper_audit.py` — meta enriquecida (`num_designations`, colunas com/sem dono, `error`,
  `available`) + guarda em `run_audit`.
- `templates/keeper_audit.html` — bloco "Liga fantasma" fora do `if report.ok`, com estado de erro
  próprio; sumário do diff separado.
- `keeper_audit_test.py` — 5 testes novos (**34/34**).
- `improvements.md`, `manager_devplan.md`, `CLAUDE.md`, este handoff.

**Item segue ⚠️ — falta o smoke com sheet real, só possível a partir de 20/08.**
