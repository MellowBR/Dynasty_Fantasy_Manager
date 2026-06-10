# Handoff — Fantasy Manager — 10/06/2026

Estado pós-sessão DP1 (F1 + F2). **git = local = project knowledge** (tudo em `main`; após o push
do commit desta sessão, prod e git sincronizados). Este handoff é o input da próxima sessão; o
`improvements.md` (item DP1 + Status Rápido) tem o detalhe completo.

## Concluído nesta sessão

| Item | Resumo |
|------|--------|
| **DP1-F1** | Diagnose read-only do board de cap pré-draft — concluída e absorvida em `improvements.md` (bloco F1 — ACHADOS). Veredito: **cabe no modelo atual, sem nova representação de jogador** (`RookieEspnValue` já é a camada). **Correção de premissa decisiva** (ver abaixo). |
| **DP1-F2** | Board implementado: lista de rookies entrantes + **simulação de cenário multi-pick calculada no backend**. ⚠️ validado em localhost; smoke em prod pendente. |

## Correção de premissa (vale registrar — afeta docs antigos)

O REG e o handoff de 08–09/06 diziam **"DP1 lê o store canônico via `espn_store_adjusted`"**.
**Está empiricamente errado para listar entrantes hoje:** o backfill do `EspnValueStore` veio de
`SELECT FROM players` (`app.py:390`) → **só rosterados**. Os rookies não-rosterados vivem em
**`RookieEspnValue`** e nunca entram no canônico hoje; ler o canônico devolveria board **vazio**.

→ **A fonte do board é `RookieEspnValue` filtrada pela season entrante** (`get_current_season()+1`).
**[[E4-c-2]] não bloqueia nem é pré-requisito do DP1** — quando rodar (subsumir `RookieEspnValue`
no canônico), o read vira troca de 1 linha (`rookie_espn_adjusted` → `espn_store_adjusted`).

## DP1-F2 — o que foi entregue

Nova seção **"🏈 Planejamento de Rookie Draft"** em `templates/cap_projector.html`, abaixo do
projetor. Dois endpoints novos em `routes/salary.py` (ambos `@login_required`, **sem admin gate**):

- `GET /api/cap_projector/rookies` — entrantes da season de **`RookieEspnValue`** (ordenado por
  valor); cada um com ESPN ref (raw) + `projected_salary` via
  `year1_salary("rookie_draft", 0, espn_adjusted)` — **fonte única, sem row de Player, sem réplica**
  (mesma invocação do `draft_import.py`).
- `POST /api/cap_projector/simulate` — `{rookie_sids:[...]}` → budget do cenário **no backend** via
  `draft_budget()` canônico: roster ativo do `current_user.team_rel` (M17, cap atual) + rookies do
  cenário como "+salário" (objeto transitório em memória — **sem materializar Player**; stub-$1 segue
  rejeitado). Cenário vazio → budget atual, idêntico ao `/api/cap_projector`.

**Não amplia o F10:** a réplica JS de budget (`updateSummary`) ficou **intocada**; a nova seção lê
`keeper_salaries`/`usable_draft_budget` direto do backend — **0 agregação de cap em JS, 0 `×1.2`
novo** no template (grep confirmado). **Fora de escopo (explícito):** persistência de cenário
("salvar plano") e modelagem de picks (regra 8.2.7 não depende do slot).

## Validação localhost (10/06/2026)

`salary_engine_test.py` **48/48 verde**. Smoke via test client (usuário **não-admin** logado):
`GET /cap_projector` **200**; lista vem de `RookieEspnValue` (canônico vazio no DB de teste —
confirma a fonte correta); spot-check **$46→$55** e **$3→$3**; cenário 2 picks → **soma +$58** no
backend; cenário vazio → budget atual sem alteração; **nada escrito** (store + cap do time intactos).

## Próximo passo

- **Smoke em prod do DP1** → fecha ⚠️→✅. Depende de um **import ESPN da season** para popular
  `RookieEspnValue` (mesma dependência que valida E2/E2-RISK/E4-a). Um import real fecha vários.
- DP1 ⚠️ em `improvements.md` (item + Status Rápido) até o smoke em prod.

## Backlog 🔲 inalterado (ver handoff 08–09/06 + improvements.md)
E2 (fechar ✅ após rookie draft real ~ago) · E4-c-2 (higiene; **não** bloqueia DP1) · E4-a/E2-RISK/M17
(⚠️ smoke prod) · **F10** (`draft_budget` replicado em JS no cap_projector — o DP1 **não** ampliou o
débito; segue trabalho próprio) · OFF26-1/-2/-4/-5 · F9-F2 · WV1.

## Nota de produção / backup
Seed (git) ≠ produção (disco persistente do Render). Sem rotina de backup automatizada; antes de
operações destrutivas em prod, backup nomeado via `sqlite3 .backup` (ver CLAUDE.md → Deployment).
