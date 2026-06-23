# Handoff — Sessão MAN-E4a-PRODF1 (23/06/2026)

## Natureza

Diagnose **read-only** (MAN-E4a-PRODF1) — por que o review do import ESPN em prod ainda
mostra match fuzzy/espúrio apesar de E4-a e E2-RISK implementados. Nenhum código, schema,
DB ou template alterado. E4-a e E2-RISK seguem **⚠️**. Só docs: achados na entrada E4-a
de `improvements.md` (+ nota no E2-RISK) + log no `manager_devplan.md` + este handoff.
Modelo: Opus.

## Pergunta

Owner rodou import ESPN real (cheat sheet PPR Top 300, upload PDF) e viu comportamento que
contradiz o E4-a: D/ST recebendo skill como candidato (Texans D/ST → Stefon Diggs; Rams
D/ST → Raheim Sanders), rookies 2026 em "Não Encontrados (76)", similaridade colapsando em
52.2%/50.0%. Parecia **modo legado** (fuzzy contra roster). Por quê?

## Vereditos por hipótese

- **H1 — resolver inativo / fallback legado por pool vazio → REFUTADA.**
  O wiring que liga o legado existe (`routes/admin.py:630` —
  `_sid_resolver = ... if _pool_idx else None`; pool vazio → `match_players` legado com
  auto-match 0.82/0.65). **Não foi acionado.** Prova decisiva: threshold de approximate é
  **0.65 no legado** (`espn_pdf_parser.py:262`) e **0.5 no resolver** (`:239`). As
  sugestões observadas (0.50/0.522) estão **abaixo de 0.65** → só o modo resolver as
  produz. Reforço: rookies em not_found carregam `resolved_sid` (`:204`), exclusivo do
  resolver. **O pool carregou e o resolver está ativo.**

- **H2 — código E4-a ausente/divergente em prod → REFUTADA** (com ressalva: o commit
  efetivamente deployado no Render não é inspecionável daqui). A assinatura comportamental
  (threshold 0.5 + rookie→not_found com sid + select default neutro do E2-RISK em
  `templates/espn_review.html:64`) é a do E4-a/E2-RISK, não a do legado.

- **H3 — lógica de sugestão replicada fora do matcher → REFUTADA.** Similaridade e
  candidatos são computados **só** em `match_players` (`espn_pdf_parser.py:226,244`),
  persistidos em `.espn_review_pending.json` (`admin.py:644-652`) e **apenas renderizados**
  por `espn_review.html:56,67`. Sem recálculo em template/JS/rota. A lógica do candidato
  espúrio **mora no próprio matcher** (ramo resolver-mode `:236-251`) — fonte única.

## Causa-raiz (CÓDIGO, não dado/ambiente)

No modo resolver, toda entrada que **não resolve a um sid** cai no ramo `:236-251`, que
monta candidatos por **fuzzy `>= 0.5` SEM filtro de posição/identidade**. D/ST **sempre**
caem aí (são excluídas do índice do pool em `admin.py:508` por id não-numérico). O bônus de
posição (`:228-231`) só soma +0.05 — **nudge, não filtro** — então uma D/ST recebe um skill
como sugestão. Gap de **desenho do E4-a**, presente desde a F2; não regressão, não
degradação. Não pego no smoke localhost (sheet/roster local não cruzou D/ST > 0.5).

## Eixos

- **Eixo A (D/ST + K com sugestão skill espúria) = BUG DE UI/SUGESTÃO (residual do E4-a).**
  Exclusão de D/ST do índice e do store (`:508`, `:550`) é **intencional**; o resíduo é só
  a tela oferecer candidato skill. **Severidade baixa/cosmética:** confirm gated por default
  neutro (E2-RISK) + `_resolve_not_found_to_store` pula K/DST (`:550`) → **sem corrupção**,
  só ruído visual.
- **Eixo B (rookies skill 2026 em not_found) = COMPORTAMENTO INTENCIONAL (E4-a correto).**
  Rookie resolve a sid → não-rosterado → not_found → store no confirm (reproduz o
  caso-âncora Carnell Tate de localhost). A premissa "rookie em not_found = bug" é **falsa**.

## Refutação de premissas (DEV_METHODOLOGY)

- (a) "parece modo legado/fuzzy contra roster" → **premissa falsa** (0.5 = resolver);
  "rookie em not_found = bug" → **premissa falsa** (E4-a correto); "ausência de âncora de
  posição" → **deslocamento** (o bônus existe em `:228-231`, mas não filtra).
- (b) ausentes do report: o **gate de confirm do E2-RISK** e o **skip K/DST do store**
  mitigam a severidade (sem corrupção) — comportamentos existentes não creditados.

## Veredito final & próxima fase

Problema de **CÓDIGO** (gap de desenho no ramo resolver-mode), **não** de dado/ambiente
(pool disponível, resolver ativo). **Próxima fase = F2 do E4-a** (não item novo, não só
re-smoke): guardar o fallback de candidatos por **filtro de posição/identidade** — entrada
D/ST/K nunca recebe skill; idealmente nenhuma entrada recebe candidato de posição
incompatível. O núcleo do E4-a/E2-RISK **passou** no smoke de prod (resolver ativo,
rookie→store, zero corrupção por inércia) → candidato a destravar ⚠️→✅ desses claims, com
o Eixo A rastreado como resíduo da F2. **Aguardar decisão do owner** (não gerar prompt de
correção ainda).

## Arquivos tocados (docs-only)

- `improvements.md` — bloco "Diagnose PRODF1" na entrada E4-a (status ⚠️ intocado) + nota
  de smoke prod 23/06 no E2-RISK.
- `manager_devplan.md` — entrada de log MAN-E4a-PRODF1 + linha "Última atualização".
- `handoff_code_manager_23_06_2026.md` — este arquivo.
