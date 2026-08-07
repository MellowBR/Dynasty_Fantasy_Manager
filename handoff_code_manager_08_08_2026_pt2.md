# Handoff — MAN-OFF26-22 (08/08/2026, pt2)
## A auditoria de keepers roda sobre sheet provisória, mas não vale como gate

**Escopo:** [[OFF26-22]] — achado do Passo 0 do MAN-OFF26-11-F2, corrigido no dia seguinte por
estar no caminho crítico (a auditoria é o **gate de abertura** do leilão de 24/08).
**Status resultante:** 🔲 → **⚠️**. Falta a conferência em produção (PROC1).
**Decisão de produto:** já arbitrada pelo owner — **opção (b), rodar e desqualificar**.

---

## 1. O que mudou

Três estados no lugar de dois. O **diff** é o mesmo; o que muda é a **autoridade** do veredito.

| sheet | veredito | `gate_qualified` |
|---|---|---|
| **DEFINITIVA** | `liberada` / `bloqueada` — idêntico ao de hoje | `True` só em `liberada` |
| **PROVISÓRIA** | **`nao_qualificada`** — relatório completo, divergências listadas, *"ABERTURA LIBERADA" impossível* | `False` |
| **indisponível** | `bloqueada` por falta de insumo, causa real prefixada | `False` |

Sobre sheet provisória a tela diz, em vermelho: **"CONFERÊNCIA ANTECIPADA — este resultado NÃO é
gate"**, nomeia o estágio, cita **os dois carimbos** (quando a urna revelou × qual é o último sync),
diz o que falta, e mantém a lista de divergências — que é o valor de rodar cedo.

Arquivos: `keeper_audit.py` (só a camada de leitura), `keeper_audit_stage_test.py` (novo, 25),
`templates/keeper_audit.html`.

---

## 2. Decisões dentro da margem

### 2.1 O carimbo viaja por fora, e o núcleo nunca o vê

`build_sheet` entrega o estágio na chave **`stage_meta`**; **`run_audit` a remove** antes de chamar
`audit()`. O núcleo puro recebe, literalmente, o mesmo formato de sempre — é o que mantém as
fixtures congeladas válidas e permitiu **34/34 sem editar uma linha**. Dois testes guardam isso: um
espiona a chamada e falha se `stage_meta` chegar ao núcleo; outro falha se a string `stage` aparecer
no corpo de `audit()`.

### 2.2 `nao_qualificada` sempre que a sheet é provisória — inclusive quando há bloqueantes

Considerei manter `bloqueada` quando o diff já acusa problemas e usar o veredito novo só no lugar de
`liberada` (leitura literal do prompt). **Não fiz**, porque `bloqueada` é uma frase de gate: ela diz
"corrija isto e você passa" — e sobre sheet provisória isso é falso, corrigir tudo **não** libera.
Um único veredito para o estado provisório deixa a resposta inequívoca. Os motivos que o núcleo
encontrou continuam todos em `blocking_reasons`, com o motivo do estágio **em primeiro**.

### 2.3 `gate_qualified` (bool) como campo canônico

Consumidor não deve casar string de veredito. Quem precisar saber "isto libera o leilão?" lê o
booleano; a string é para humano.

### 2.4 O ramo "sem insumo" precisou de condição nova, não de preservação

O prompt pedia preservar o comportamento atual desse ramo. **Não havia comportamento atual:** ele
era **inalcançável**, porque `_build_keeper_sheet` devolve `revealed` **e** `available` hardcoded
como `True`. Revivido com uma condição que de fato dispara: `available` da fonte **E** pelo menos um
time na sheet. Hoje isso significa "nenhum time cadastrado" — improvável, mas agora é um caminho
real em vez de um `if` decorativo.

---

## 3. Passo 0 — verificação de terreno

1. ✅ **Gate morto:** `routes/cuts._build_keeper_sheet` linhas 480-481 devolvem `"revealed": True` e
   `"available": True` **hardcoded** — o `if not raw.get("revealed")` nunca disparava desde o U7.
2. ✅ **Estágio descartado:** o `build_sheet` antigo repassava só `revealed`/`season`/
   `lock_timestamp`/`teams`; `stage`, `stage_label`, `sync_timestamp`, `late_drop`, `available` e
   `source` morriam na montagem.
3. ⚠️ **A causa estrutural, que vale mais que o bug:** os 34 testes exercem `audit()` **diretamente**
   com fixtures — **nenhum** chamava `build_sheet` ou `run_audit`. A camada de leitura estava
   **inteiramente sem teste**, e foi exatamente ali que o U7 deixou código morto sem que nada
   acusasse. Um núcleo puro muito bem testado não protege a costura que o liga ao mundo.
4. ⚠️ **Resíduo declarado:** a frase do `_no_input` dentro do núcleo ainda diz "A janela de cortes
   ainda não foi revelada" — obsoleta desde o U7. Corrigir exigiria editar o núcleo (restrição), então
   `qualify` **prefixa** a causa correta e o operador a lê primeiro.

### A decisão "provisória × definitiva" está replicada? **Não.**

- **Calculada em um único lugar:** `routes/cuts.py:440-445` (revelação da urna + sync posterior).
  Grep confirma que nenhum outro sítio reimplementa a regra — e o fix entrou como **leitor**.
- **Consumida** comparando com o literal `"definitiva"` em 4 sítios: `keeper_exclusion.py` (freeze e
  gate do import), `templates/keeper_sheet.html` (2×), e agora `keeper_audit.STAGE_DEFINITIVA`.
- `templates/draft_import.html` apenas **exibe** `stage_label`/`source_stage` — não decide.
- ⚠️ **Colisão de vocabulário, não de lógica:** `routes/league.py:82` fala em "ESPN **DEFINITIVA**"
  e "selo PROV" — é a **tabela ESPN**, outro eixo. Confunde grep, não confunde código.
- **Resíduo menor:** o literal `"definitiva"` repetido nos 4 leitores. Uma constante compartilhada
  teria de morar no produtor ou no módulo de exclusão, ambos sob restrição nesta sessão.

---

## 4. Validação

| # | Validação | Resultado |
|---|---|---|
| V1 | sheet **provisória** (urna revelada, sem sync posterior) | relatório completo, divergências listadas, veredito **`nao_qualificada`**, motivo com os dois carimbos e o que falta |
| V2 | sheet **definitiva**, mesmo insumo | relatório **idêntico campo a campo**; únicas chaves novas: `sheet_stage`, `gate_qualified` |
| V2b | contraste com o **núcleo real** | definitiva → `liberada` + gate; provisória → `nao_qualificada` — **com as mesmas 0 divergências** |
| V3 | sheet **ausente** (zero times) | bloqueio por falta de insumo revivido, causa real prefixada, **não** se confunde com provisória |
| V4 | suítes | auditoria **34/34 sem editar teste nem fixture** · `salary_engine` **54/54** · exclusão **36/36** · late_drop 64 · janela 22 · cap_regua 14 · contract_year 20 · trilha_fa_proj 17 · **novos 25** → **286 verdes** |
| V5 | liga fantasma real, só `GET` | `/admin/keeper_audit` **200**; `draft_id` derivado (`1389755381567213568`, `pre_draft`, **24 designações**); sheet **PROVISÓRIA** (urna não revelada); veredito **`nao_qualificada`**; `gate_qualified: false`; "Abertura liberada" **ausente** do HTML; board intacto |

> Nenhum par das fixtures congeladas produz `liberada` (todas têm 9 times não populados por
> desenho) — por isso o V2b monta o menor cenário coerente possível, para o contraste sair do
> **núcleo real** e não de um dicionário sintético.

---

## 5. O que ficou fora

- **A frase obsoleta do `_no_input`** dentro do núcleo puro — restrição; mitigada por prefixo.
- **Constante compartilhada para `"definitiva"`** — teria de morar em módulo sob restrição.
- **`keeper_exclusion.build_exclusion_source` continua lendo `_build_keeper_sheet` por conta
  própria** para obter o estágio. Agora que `build_sheet` propaga `stage_meta`, essa segunda leitura
  ficou redundante — mas o módulo de exclusão está ⚠️ aguardando smoke e é intocável nesta sessão.
  **Simplificação óbvia para depois de 24/08.**
- **Bloquear a execução sobre sheet provisória** — descartado pela decisão (b) do owner.

## 6. O que falta para ✅

1. Abrir `/admin/keeper_audit` **em produção** e ver o selo **PROVISÓRIA** + o bloco de conferência
   antecipada (hoje a sheet de prod é provisória por definição — a urna não revelou).
2. Owner confirmar no painel do Render que o **hash live** é o desta entrega (PROC1).
3. A conferência com sheet **DEFINITIVA** — e portanto do caminho `liberada` + gate — só é possível
   **a partir de 22/08**, depois da revelação da urna e do sync final.
