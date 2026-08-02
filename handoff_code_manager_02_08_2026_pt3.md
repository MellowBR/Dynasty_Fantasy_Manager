# Handoff pt3 — Fantasy Manager — 02/08/2026 (MAN-OFF26-10-11-REG)

> Continuação de `handoff_code_manager_02_08_2026_pt2.md` (fechamento do arco S2 → S5).
> Esta parte é **registro puro**: nenhum código, nenhuma diagnose, nenhuma decisão de produto
> arbitrada. Dois gaps novos entram no backlog e uma premissa factualmente errada é emendada.
>
> ⚠️ **LEIA A PARTE 2 (fim do arquivo) ANTES DE AGIR.** Depois desta parte, a liga fantasma foi
> **criada e testada na mão**, e o experimento **confirmou duas das questões que a parte 1 registra
> como "probe pendente"** e **refutou o §5 da F1 do OFF26-4**. Onde as duas partes divergirem,
> **vale a parte 2**.

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
| ambiente | **pronto para uso real** — board **vazio** |
| **RESET DRAFT** | ✅ **executado em 02/08/2026** — os 2 times da validação foram removidos |
| **`league_id`** | `1389725099556372481` |
| **`draft_id`** | `1389725100684611584` |

> Esta tabela registrava **duas pendências** quando a parte 2 foi commitada; **ambas foram
> resolvidas pelo owner na mesma sessão, logo depois** (`MAN-OFF26-IDS-REG`).

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
