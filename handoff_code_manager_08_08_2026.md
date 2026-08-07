# Handoff — MAN-OFF26-11-F2 (08/08/2026)
## O importador ingere só arremates: a keeper sheet CONGELADA como lista de exclusão

**Escopo:** F2 do [[OFF26-11]] — o **último item de código** do caminho crítico de 24/08.
**Status resultante:** OFF26-11 **🔲 → ⚠️**. ⛔ **Não marcado ✅** — o smoke real só existe depois
do leilão de 24/08.
**Decisão de produto:** já estava arbitrada em 06/08 (opção A — Manager é fonte única). Esta sessão
decidiu **como**, dentro da margem que o prompt delegou.

---

## 1. O que foi entregue

**`keeper_exclusion.py` (novo)** — o discriminador único, no molde do `salary_engine`/`keeper_audit`:

- **núcleo puro** (sem DB, sem rede, sem Flask): `build_index` · `classify_pick` ·
  `compute_exclusion_hash`;
- **IO**: `build_exclusion_source` (lê os dois produtores já existentes da sheet) ·
  `freeze_exclusion_list` / `get_frozen_exclusion` / `clear_frozen_exclusion` · `exclusion_gate`.

**Regra única, e é a decisão A inteira:** *pick cujo jogador consta na lista de exclusão **para o
mesmo time do pick** é keeper* — não é ingerido, não gera contrato, não toca salário,
`contract_year` nem histórico. Consta para **outro** time → pendência. Não consta → arremate.

**`routes/draft_import.py`** — o discriminador roda **antes** de qualquer resolução de identidade
local (o keeper não é "um pick que não casou"; é um pick que não se ingere por definição). Novas
rotas de congelamento. **`templates/draft_import.html`** — card da lista de exclusão, blocos
separados de *keepers excluídos* / *pendências* / *arremates*, e a ação nova de reativação.

---

## 2. Decisões tomadas dentro da margem delegada

### 2.1 Onde o discriminador nasce → módulo próprio, consumindo os produtores existentes

O prompt pediu explicitamente que não virasse mais uma réplica. A lista vem de
`keeper_audit.build_sheet` (o produtor que **já** enriquece a sheet com `sleeper_player_id`) e o
selo provisória × definitiva vem de `routes.cuts._build_keeper_sheet` (a fonte única do estágio).
**Nenhuma segunda definição de "quem é keeper"** — `keeper_exclusion` não consulta roster, não
filtra `is_dropped`, não decide nada sobre keeper.

**Por que DOIS produtores e não um:** `build_sheet` produz os keepers com id, mas **descarta**
`stage`, `stage_label`, `available`, `source` e `late_drop`. Sem o estágio não há como cumprir o
requisito 8 (sheet provisória bloqueia). A alternativa natural — passthrough aditivo em
`build_sheet` — foi **descartada** por encostar na restrição *"não alterar o formato do payload da
keeper sheet consumido pelo núcleo puro da auditoria"*. Preferiu-se o caminho de **risco zero**:
ler os dois. **Custo:** a sheet é montada duas vezes num caminho de admin usado **uma vez por
temporada**. Isso é um exagero consciente de cautela; se o OFF26-22 (abaixo) for feito, o
passthrough resolve os dois de uma vez.

### 2.2 O mecanismo de congelamento → **snapshot explícito com hash**

**É requisito de correção, não de robustez.** A sheet nasce do **roster vivo**, e o checklist
pós-leilão prevê que cada owner adicione seus arremates **manualmente na liga real**. Um sync entre
o leilão e o import faz o arremate aparecer como keeper — e ele seria **excluído da ingestão**.
Esse é o **dano invertido**: em vez de zerar a idade de um contrato, o contrato ano 1 **não nasce**.
É exatamente o caso canônico do owner ($50 dropado → recomprado por $50 pelo mesmo time).

**Escolhido:** `AppConfig["keeper_exclusion_frozen"]`, gravado por ato de admin
(`POST /api/draft_import/exclusion/freeze`), com `hash`, `frozen_at`, `sync_timestamp`,
`source_stage`, `late_drop_executed_at`. Recusa: sheet indisponível · **PROVISÓRIA** · keeper sem
`sleeper_player_id` · re-congelamento sem justificativa (molde M8).

**Descartadas, com motivo:**

| alternativa | por que não |
|---|---|
| derivar ao vivo no import | é o bug — contaminação |
| gatear por carimbo ("recusar se houve sync após a revelação") | recusa o import justamente no estado em que ele é correto, e não distingue o sync do drop do sync que trouxe arremates |
| snapshot automático no 1º preview | congela sem que ninguém tenha declarado o momento; se o 1º preview vier depois da contaminação, congela o erro |

**O que o congelamento NÃO cobre (declarado, não mitigado):**

1. **congelar tarde** — se o admin congelar depois de owners já terem readicionado arremates, a
   lista nasce contaminada. Mitigação é **operacional**: o snapshot carrega os carimbos, a tela os
   exibe, e o passo entrou no runbook **com hora marcada** (entre o sync final e o leilão);
2. **keeper que o board não designou** — é exposição ao leilão, matéria da auditoria OFF26-4, que
   roda antes; aqui ele apenas não aparece entre os picks;
3. **selo virado por sync tardio sem execução dos drops** — a sheet pode virar DEFINITIVA sem que
   os drops revelados tenham sido executados no Sleeper; quem prova isso é o operador (o runbook já
   manda conferir roster a roster).

**Sem persistência de `draft_id` em nenhuma forma** — nem no snapshot, nem em cache. O board é lido
derivando o `draft_id` do `league_id` a cada uso, como sempre.

### 2.3 Escopo por modo → gate em `acquisition_type != "rookie_draft"`

O importador já derivava o modo de `dtype == "linear"`. Registrado, porque **não é idêntico** a
gatear em `type == "auction"`: qualquer draft **não-linear** (ex.: `snake`) cairia na exclusão.
Coincide com os dois modos reais da liga; se um dia existir um terceiro tipo de sala, revisar.

---

## 3. Divergências spec × terreno (Passo 0)

### 3.1 ⛔ Premissa que CAIU — o caso canônico não era ingerível pela UI

`player_lookup.find_player_by_sleeper_id` filtra **`is_dropped=False`**. Logo o jogador dropado na
janela **nunca** cai em `matched`: vai para *picks sem match* com causa "jogador dropado no banco".
E o `<select>` do template oferecia apenas **Pular** e **Criar novo** — "criar novo" produziria um
**Player duplicado** com o mesmo `sleeper_player_id`, perdendo o histórico. A API já aceitava
`resolutions[sid] = <player_id>`; **nada na tela expunha isso**.

Sem corrigir, a validação central do item ($50 → contrato **ano 1**) era impossível de executar.
**Corrigido:** o preview devolve `suggested_player_id` / `suggested_name` /
`suggested_contract_year` / `suggested_salary` para essa causa, e a tela oferece
**"Reativar &lt;nome&gt; (ano 1)"**.

> **Padrão recorrente, digno de nota:** a capacidade existia no backend e morria na tela — mesma
> família do U-CONF (o `confirm()` nativo que barrou uma declaração no celular).

### 3.2 Achado lateral virou item — **OFF26-22 🔲 Média**

`keeper_audit.build_sheet` ainda abre com `if not raw.get("revealed"): return {"revealed": False}`.
Desde o U7, `_build_keeper_sheet` devolve **`revealed: True` incondicionalmente** — o ramo é
**código morto**, e com ele morreu o único bloqueio da auditoria por falta de insumo. Efeito:
**o gate de abertura do leilão audita sheet PROVISÓRIA como se fosse definitiva**, e emite
"liberada" sobre dado que ainda vai mudar. O estágio existe e está calculado; `build_sheet`
simplesmente o descarta. **Não tocado** (superfície da auditoria, sob restrição desta F2).
⚠️ O importador **não depende disso** — ele lê o selo direto da fonte e recusa congelar provisória.

### 3.3 Réplicas encontradas (a pergunta explícita do prompt)

Leitura de picks do Sleeper vive em **3 módulos**, com **3 coerções diferentes do lance**:

| sítio | papel | `metadata.amount` |
|---|---|---|
| `routes/draft_import.py` `_read_draft` | import (**escreve**) | `float(...)`, fallback **1.0** |
| `keeper_audit.py` `fetch_board` | board da fantasma (read-only) | string crua → `_to_int(...,0)` |
| `sync_sleeper.py` `_collect_draft_events` | backfill F8 | `int(...)`, fallback **None** |

**Não unificadas** — seria mudança de comportamento em `sync` e na auditoria, ambos fora do escopo
e sob restrição. Já era o achado **P6 do probe de 03/08** (candidato a helper único, espírito do
F10) e **segue aberto**.

**O fix NÃO precisa alcançar os outros sítios:** o sync não escreve salary/contract e a auditoria é
read-only. **Só o importador cria contrato**, e é lá que o discriminador nasceu.

Classificação de pick (linear × auction) existe **só** no importador (`_classify_draft` do sync
classifica *drafts*, não picks). Identidade: `find_player_by_sleeper_id` no importador,
`players_by_sid` inline no sync (2×), `board_by_sid` no núcleo da auditoria — **nenhum casa por
nome** no caminho do importador.

### 3.4 Comportamentos que a spec não mencionava e foram preservados

- store ESPN de rookie (E2): `store_espn_adjusted` / `projected_salary` no preview de unmatched;
- **idempotência por `event_ref`**: keeper excluído **nunca gera `event_ref`** → se um keeper
  tivesse sido ingerido por engano antes, a exclusão **não desfaz** (não há caso hoje);
- `skip` com justificativa segue sendo o único pulo — e é **declarado**, não silencioso;
- **`_budget_alerts` somava tudo** — no caminho novo isso seria **dupla contagem** (o keeper já está
  no roster corrente, base da simulação, e entraria de novo como pick adicionado). Com a exclusão,
  a soma passa a ser **só de arremates**, sem mudar a fórmula. Medido: keeper $40 + arremate $30 no
  mesmo time → folha simulada **$73** (base $43 + $30), bid máximo **$109**; a dupla contagem daria
  folha **$113**;
- **resolução keyed por `sleeper_player_id`, não por `pick_no`** (template e `confirm`): dois picks
  do mesmo jogador colidiriam na mesma resolução. **Latente, fora do alcance desta entrega.**

---

## 4. Validação (36 testes novos; 261 verdes no total)

| # | Validação | Resultado |
|---|---|---|
| V1 | keeper do mesmo time nos picks | **0 escritas**; `salary`/`contract_year`/`contract_start_season`/`acquisition_type`/`is_dropped` + contagens de `SalaryHistory`/`AuctionLog` idênticos antes/depois |
| V2 | caso canônico **$50** | `contract_year` **3 → 1**, salário **$50**, `is_dropped` **True → False**, +1 `SalaryHistory` +1 `AuctionLog` pela porta canônica |
| V3 | keeper de **outro** time | pendência, confirm **400**, motivo nomeado; **nem o arremate válido do mesmo lote entrou** |
| V4 | DEF com sigla (`"LAR"` keeper / `"SEA"` arremate) | classificação correta sem coerção, **sem falso keeper** |
| V5 | sheet provisória × ausente/não-congelada × outra season | bloqueio com **mensagens distintas**; **0 escritas** |
| V6 | **contaminação** (o caso que separa a implementação correta da invertida) | sheet **ao vivo** passa a listar o arremate como keeper; a **congelada** não → o arremate **continua sendo ingerido**, contrato ano 1 |
| V7 | reimport | **0 criados**, 1 já importado, contagens inalteradas |
| V8 | **regressão do modo linear** — rookie 2025 real (`1224848075617484800`) | preview do código novo **idêntico ao do HEAD** campo a campo (33 matched / 3 unmatched / causas / salários / alertas); **0 escritas** |
| V9 | preview não escreve | contagens iguais antes/depois, 2 execuções |
| V10 | alerta de budget | arremates **$30** × base **$43** → folha **$73**, bid máximo **$109**; dupla contagem daria **$113** |
| V11 | suítes | `salary_engine` **54/54** · `keeper_audit` **34/34** · `late_drop` **64/64** · `janela_ensaio` **22/22** · `cap_regua` **14/14** · `keeper_exclusion` **36/36** · `contract_year` 20/20 · `trilha_fa_proj` 17/17 |
| V12 | leitura real da fantasma (só `GET`) | `draft_id` derivado do `league_id`; **24 designações**; **`is_keeper: false` 24/24**; draft em **`pre_draft`** |

> **Nota sobre V8:** a baseline registrada em 05/06/2026 era **34 matched / 2 unmatched**; hoje o
> mesmo draft dá **33 / 3**. A diferença é **deriva do banco** (um jogador passou a `is_dropped`
> desde então), **não do código** — HEAD e código novo produzem o **mesmo** dicionário hoje, que é
> a comparação que prova ausência de regressão.

> **Nota sobre `salary_engine`:** são **54** testes, não 48. O número 48 do prompt e do `CLAUDE.md`
> estava desatualizado desde o OFF26-18. `CLAUDE.md` corrigido.

---

## 5. Confirmação empírica oportunista — **pós-draft NÃO OBSERVADO**

Leitura ao vivo de 08/08/2026, **só `GET`**, sem escrita de nenhum tipo:

```
league Dynasty SB FA Auction · season 2026 · status pre_draft
draft_id 1389755381567213568  (derivado de league_id 1389725099556372481)
type auction · rounds 22 · budget 200
24 picks · roster 3=10 / 4=8 / 5=6 · totais $148 / $95 / $60
is_keeper: {false} em 24/24
```

⛔ **O draft está em `pre_draft`** — os picks disponíveis são as **designações**, não o resultado de
um draft rodado. **A confirmação pós-draft do `is_keeper` continua NÃO OBSERVADA**, e não foi
forçada: rodar o draft de teste é **escrita na plataforma**, ato do owner. **Isso não bloqueia
nada** — o discriminador **não lê** o campo, e há teste que falha se a string `is_keeper` aparecer
no corpo do módulo.

---

## 6. O que ficou fora

- **Unificação da leitura de picks** (3 coerções) — toca sync e auditoria, ambos sob restrição.
- **OFF26-22** (auditoria × sheet provisória) — registrado como item, não corrigido.
- **Resolução keyed por sid em vez de pick_no** no importador — latente, não alcançado.
- **Reconciliação de salário keeper board × Manager** — **descartada pela decisão A**, de propósito.
- **Passthrough de `stage` em `keeper_audit.build_sheet`** — evitado por restrição; é o caminho
  natural se o OFF26-22 for feito.

## 7. O que o smoke de 24/08 precisa provar

1. que o board pós-leilão real traz **keepers e arremates na mesma lista de picks**, e que a
   exclusão os separa **com os 12 times de verdade** (o teste roda com 2);
2. que o **congelamento aconteceu no momento certo** do calendário — depois do sync final, **antes**
   do leilão — e que os carimbos exibidos batem com o que aconteceu;
3. o que os picks **pós-draft** de fato expõem sobre keeper (registro, não insumo);
4. que **nenhum keeper real** teve `contract_year` alterado — a conferência é direta: nenhum jogador
   que não trocou de time pode aparecer com `contract_year = 1` e `contract_start_season = 2026`;
5. que o caso canônico apareceu como *"Reativar (ano 1)"* e foi resolvido por essa ação, **não** por
   "Criar novo".

## 8. Ação do owner pendente (nenhuma bloqueia esta entrega)

- **Opcional, com prazo:** rodar um **draft de teste** sobre o board populado da fantasma antes do
  próximo RESET DRAFT, se quiser a confirmação pós-draft do `is_keeper` **como registro**. É
  escrita na plataforma e não foi feita. **Não é pré-condição de nada.**
- **Obrigatório no calendário:** o passo de **congelar a lista** entre o sync final (22/08) e o
  leilão (24/08) — já no `runbook_urna_late_drop.md`, seção "22–24/08".
