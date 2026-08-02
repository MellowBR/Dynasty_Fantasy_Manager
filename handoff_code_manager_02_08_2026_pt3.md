# Handoff pt3 — Fantasy Manager — 02/08/2026 (MAN-OFF26-10-11-REG)

> Continuação de `handoff_code_manager_02_08_2026_pt2.md` (fechamento do arco S2 → S5).
> Esta parte é **registro puro**: nenhum código, nenhuma diagnose, nenhuma decisão de produto
> arbitrada. Dois gaps novos entram no backlog e uma premissa factualmente errada é emendada.

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
