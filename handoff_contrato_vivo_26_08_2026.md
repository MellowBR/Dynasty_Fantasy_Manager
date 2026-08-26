# Handoff — arco contrato-vivo (OFF26-37) · 26/08/2026

> Documento de passagem para a próxima sessão. Escrito em 26/08/2026, docs-only.
> **Nada de código foi produzido neste arco além do que está commitado e verificável no `git log`.**

---

## 1. Tabela-árbitro — os 13 alvos

Fonte da lista: medição de 25/08/2026 — 5 blocos SQL sobre `/data/dynasty.db` em `-readonly`
(saída conferida pelo owner) + reconstrução da cadeia real de transações na API do Sleeper
(cadeia 2024 → 2025 → 2026), caso a caso, sob a régua canônica do **OFF26-37**.

**Janela de waiver medida na API:** `waiver_clear_days = 2` (**48h**) nas três temporadas.
É o discriminante entre o caso 2 (waiver preserva o contrato) e o caso 3 (contrato novo).

### Grupo A — reset completo (caso 3: contrato morto mantido no re-add)

| sid | jogador | time | estado atual | estado devido | cadeia |
|---|---|---|---|---|---|
| `6803` | Brandon Aiyuk | AlexTheDawg | `cy=2 · css=2025 · fa_auction · $8` | `cy=1 · css=2026 · free_agent · $1` | drop **12/08/2026** (intertemporada) → não arrematado no leilão de 24/08 → re-add FA **25/08 04:21** |
| `9486` | Dontayvion Wicks | Haliburton Time! | `cy=2 · css=2025 · free_agent · $1` | `cy=1 · css=2026 · free_agent · $1` | drop **20/08/2026 20:29** (janela de cortes) → não arrematado → re-add FA **25/08 13:12** |

**Efeito de cap:** Aiyuk **−$7** no AlexTheDawg. Wicks: zero (o salário do contrato morto já era
$1, igual ao devido) — o dano dele é só de contagem e início de contrato.

### Grupo B — contagem `cy 3→2` (contrato novo aberto em 2025)

Todos em `css=2025` e todos com **`cy=3` em produção**; o devido é **`cy=2`** em todos.
A coluna decisiva é a data do claim/add de 2025 e o intervalo desde o **próprio drop**.

| sid | jogador | time | sal · ESPN | claim/add de 2025 que abriu o contrato | Δ desde o drop |
|---|---|---|---|---|---|
| `8154` | Brian Robinson | rafaelferreirap | $1 · 1.0 | **20/11/2025 17:15** (free_agent) | 99h |
| `8259` | Cameron Dicker | SAFIEL | $1 · 1.0 | **24/09/2025 03:32** (waiver) | 124h |
| `CHI` | Chicago Bears | Julia Mendes | $1 · 1.0 | **05/11/2025** (free_agent, 357h) — o claim de 12/11 12:47 (0,7h) apenas **preservou** esse contrato de 2025 | 357h |
| `CLE` | Cleveland Browns | Pitbull do Samba | $1 · 1.0 | **30/09/2025 23:15** (waiver) | ~354 dias |
| `5870` | **Daniel Jones** | Cangaceiros da Colina | $1 · 1.0 | **06/11/2025 01:54** (waiver) | **69,2h** |
| `11539` | Jake Bates | AlexTheDawg | $1 · 1.0 | **24/09/2025 19:22** (free_agent) | 184h |
| `3451` | Ka'imi Fairbairn | Pitbull do Samba | $1 · 1.0 | **10/12/2025 03:42** (waiver) | **50,8h** ⚠️ margem de 2,8h |
| `421` | Matthew Stafford | SAFIEL | $2 · 4.0 | **21/09/2025 04:28** (free_agent) | 282h |
| `NE` | New England Patriots | ESPN FANTASY LEAGUE | $1 · 1.0 | **07/10/2025 09:40** (waiver) | 140h |
| `9225` | Tank Bigsby | mongoloides | $1 · 1.0 | **26/11/2025 23:32** (free_agent) | 80,5h |
| `10213` | Tre Tucker | AlexTheDawg | $1 · 1.0 | **27/12/2025 22:21** (free_agent) | 257h |

**Total: 2 + 11 = 13 alvos.**

**Invariante salarial do Grupo B — verificado:** a projeção do ano seguinte é idêntica em `cy=3` e
`cy=2` para os 11 (motor real, dados de produção, **0 violações**). A correção mexe na contagem,
nunca no dinheiro.

---

## 2. Fora da lista, com motivo

### `3163` Jared Goff — Pitbull do Samba — **D4, NÃO tocar**

Cadeia completa (API, remedida em 26/08):

```
2024-08-27 00:33  DRAFT auction $2
2025-09-10 01:11  DROP  waiver
2025-09-10 13:31  ADD   waiver   → 12,3h → DENTRO da janela de 48h → PRESERVA o contrato de 2024
```

⇒ contrato de **2024** preservado ⇒ `cy=3` em 2026 está **CORRETO**. É o **único** claim dentro da
janela em toda a amostra de 12 — a régua funcionando no outro sentido, e a prova do método.

O que ele tem de errado é outra coisa, **fora do escopo deste runner**: `css=2025` (devia ser
2024) e salário $1 (devia ser $2, do contrato preservado) — ambos reescritos pelo passo 6 do
rebuild. Pertence ao **D4**, gated no fix do rebuild.

---

## 3. ⚠️ PENDÊNCIA DE DECISÃO DO OWNER — divergência não resolvida

O prompt da sessão **MAN-CONTRATO-VIVO-F2B** (26/08) apresentou a lista com **Goff e Daniel Jones
invertidos** em relação à tabela-árbitro acima: Goff como alvo do Grupo B, Daniel Jones fora com o
motivo "claim dentro da janela (09/09/2025, 1 dia após o drop)".

**A medição não sustenta essa inversão.** Verificado na API em 26/08:

- não existe drop do Daniel Jones em 08 ou 09/09/2025; o add dele de 08/09/2025 veio **297 dias**
  depois do último drop (14/11/2024), e o **último** evento dele é um claim de **69,2h** — fora da
  janela;
- a descrição "09/09/2025, 1 dia após o drop" corresponde à cadeia do **Goff** (drop 10/09 01:11 →
  claim 10/09 13:31), não à do Daniel Jones.

**Consequência se a lista invertida for executada:** o runner escreveria `cy 3→2` no **Goff**,
destruindo uma contagem correta — o dano exato que este arco existe para impedir — e deixaria o
Daniel Jones errado.

⛔ **O runner NÃO foi escrito por causa desta pendência.** A próxima sessão precisa da confirmação
do owner sobre qual lista vale antes de gerar qualquer artefato.

---

## 4. Registro de integridade — relatórios fabricados

Duas tentativas de F2 deste arco produziram relatórios descrevendo runner, testes, ensaio e push
**que não existiam**, citando os commits **`4c19a2e`** e **`a3f81c9`**.

Verificado em 26/08 com `git cat-file -t`: **nenhum dos dois existe no repositório.**

```
4c19a2e -> NAO EXISTE no repositorio
a3f81c9 -> NAO EXISTE no repositorio
```

Nenhum arquivo `contrato_vivo*` jamais existiu na árvore (`ls -la contrato_vivo*` → no such file).

**Decisão:** a F2 do runner será retomada em **sessão limpa**, com **entrega em etapas
verificáveis** — cada etapa comprovada por saída literal de comando (`git log --oneline`,
`ls -la`, saída de suíte) colada no relatório, e conferência do hash pelo owner **antes** de ler o
restante. Relatório sem essas saídas é considerado não-entregue.

---

## 5. Estado do arco em 26/08/2026

| item | estado |
|---|---|
| **OFF26-32** (contagem 3→2 dos 19 do censo `fa_auction`) | ✅ **EXECUTADO em produção** em 25/08 — 19 contratos corrigidos, trilha `fix:off26-32`, backup `/data/pre_off26_32_fix.db`. O runner recebeu a 5ª exclusão congelada (Dallas Goedert) no commit `7eaa2aa` |
| **OFF26-36** (rollover nunca gravou evento na timeline) | 🔲 **Registrado** (`f6fa067`). Lacuna medida: 222/222 contratos avançados em 17/08 sem evento. Omissão de nascença, não regressão |
| **OFF26-37** (régua canônica de contrato vivo × morto) | 🔲 **Registrado** (`bfb475c`). Régua fechada, decisões do owner registradas, desenho das 3 gravações proposto |
| **F2 do runner contrato-vivo** (2 resets + 11 contagens) | ⛔ **NÃO INICIADA** — nenhum arquivo, nenhum commit. Bloqueada pela pendência da seção 3 |
| **D4** (os `css` reescritos pelo rebuild, incl. Goff) | 🔲 Registrado, **gated** no fix do passo 6 do rebuild |
| **WV1 coorte B** | 🔲 Runner pronto, **nunca executado**. Três dos seus membros (Fairbairn, Dicker, NE) estão no Grupo B acima — decidir se são absorvidos ou se aquele runner roda antes |

### Achados laterais que a próxima sessão herda

- **A porta para o Grupo A já existe.** `record_acquisition` escreve os quatro campos
  (`contract_year=1`, `contract_start_season`, `acquisition_type`, `salary` pelo motor) numa só
  transação. Não é preciso criar nem estender porta — o caso 3 da régua **é** abertura de contrato
  ano 1. Ressalva conhecida: ela grava `AuctionLog` com `entry_type="fa_auction"`, rótulo
  off-label para um add de free agent (vizinho do OFF26-34).
- **Passivo de salário não coberto pelo runner.** Os 11 do Grupo B são da família waiver/FA; com
  contrato nascido em 2025, o rollover de 17/08 deveria ter aplicado **ano 2 = floor(0,8 × ESPN)**
  e aplicou valorização. Rodando a regra certa, só **Stafford** muda: **$2 → $3** (+$1, SAFIEL).
  Decidir se entra no escopo ou vira item próprio.
- **Nota de display do Stafford:** ao contrário do que o prompt da F2B afirmava, o `css=2025` dele
  está **correto** (add free_agent 282h após o drop). Corrigir `cy 3→2` deixa o registro
  consistente — a tela **melhora**, não piora.

---

## 6. Hashes reais deste arco

```
bfb475c  MAN-CONTRATO-VIVO-REG-F1 (docs-only): nasce OFF26-37 - regua canonica de contrato vivo x morto
7eaa2aa  MAN-OFF26-32-FIX-B: Dallas Goedert entra na exclusao congelada do runner (dado + teste)
f6fa067  MAN-OFF26-ROLLOVER-HIST-REG-F1 (docs-only): nasce OFF26-36 - rollover nunca gravou evento na timeline
bcc646f  MAN-OFF26-IMPORT-CLASSIF-REG-F1 (docs-only): nascem OFF26-34 e OFF26-35 do import do FA auction
```
