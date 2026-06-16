# Handoff — Sessão E4-d-F1b (16/06/2026 pt3)

## Natureza

Diagnose **read-only** (MAN-E4-d-F1b) — infra de aliases (time + jogador) nas portas
do `/auction`. Nenhum código alterado, nenhuma escrita no banco. E4-d permanece **🔲**.
Só docs: achados absorvidos na seção E4-d de `improvements.md` + este handoff.

## Pergunta

Que infraestrutura de resolução de alias já existe (time fantasy e jogador) antes de a
F2 escolher mecanismo, dado o requisito de aliases (time: Houston/Texans/HOU; jogador:
Hollywood↔Marquise = mesmo sid 5848).

## Veredito central

**Não existe NENHUMA infra de alias no sistema.** Grep `alias|nickname|abbrev|apelido|
Hollywood` em todo `*.py` → só um comentário (import_csv.py:111) e a docstring do E4-b.
Zero mapa de dados. O "Brown-safe" do E4-a resolve **casar demais** (homônimos por NFL
team), não **casar de menos** (alias). Problemas distintos.

## TIME (models.py:79-118 + sync_sleeper.py:107-176)

- Campos: `name` (= `metadata.team_name` do Sleeper), `display_name` (**hoje idêntico a
  name** — sync seta os dois iguais), `owner_name` (= handle do manager), IDs estáveis
  `sleeper_owner_id`/`sleeper_roster_id`.
- **Sem** abreviação/cidade/apelido, **sem** mapa. "Houston/Texans/HOU" não tem fonte.
  (`team_abbr` é do pool de jogadores = NFL team, irrelevante.)
- Aliases reais reusáveis: `name` + `owner_name`. Além disso → dado novo curado.
- FA/rookie individuais usam `<select>` (exato) — alias só afeta bulk + Excel (free-text).

## JOGADOR

- Cache real inspecionado (`.sleeper_players_cache.json`, 11.578 players). Marquise
  Brown (sid 5848): campos de nome = `full_name`/`first`/`last` + `search_*`.
  **"Hollywood" não existe em campo nenhum.** O Sleeper **não tem campo de apelido.**
- `_resolve_entry_sid`/`_norm_name` cobrem acento, sufixo, pontuação, caixa, espaço.
  **NÃO cobrem apelido** (fonte não contém).
- E4-b **deletou** o órfão "Hollywood Brown" (id 279, sem valor) via
  `cleanup_orphan_players` — **nunca resolveu** o apelido. Nenhum mecanismo mapeia
  apelido→sid hoje.

## Parecer de mecanismo p/ F2 (sem implementação)

- **TIME:** input contra `name` + `owner_name`, exato→normalizado (reusa `_norm_name`),
  **sem substring**. Aliases fora disso → mapa pequeno curado `{team_id: [aliases]}` OU
  exigir `name` canônico. Ambíguo → escolha visível, nunca time errado silencioso.
- **JOGADOR:** manter resolver Brown-safe (nome+nfl_team→sid; fallback nome-único).
  Apelido não está no Sleeper → só via mapa curado `apelido→sid`, pré-normalização ANTES
  do pool. Nunca fuzzy/substring (reabre o Brown; E2 já viu falso-positivo @0.665).
  Ambíguo → needs_review.

## Risco de casar demais (mitigado no parecer)

- TIME: abreviação curta colide entre times (= bug substring relocado) → alias curto só
  se único; ambíguo → escolha.
- JOGADOR: resolver já retorna None em ambiguidade; apelido só por mapa curado.

## Decisões EM ABERTO p/ o owner (antes da F2)

- **(D)** Time: só `name`+`owner_name` (simples; "Houston" cai em miss) **ou** mapa curado?
- **(E)** Jogador: mapa curado apelido→sid (cobre Hollywood↔Marquise) **ou** apelido →
  needs_review (sem auto-merge)?
- **(F)** Fonte de verdade dos mapas (se adotados): dict estático no código **ou** tabela
  no DB (implica schema). Quem mantém.

## Estado

- Nada commitado (diagnose docs-only; owner decide agrupar ou commitar isolada).
- Pendente do ciclo: F9 (`1ad8bd2`) aguarda smoke prod; E4-d aguarda decisões D/E/F +
  A/B/C da F1 antes da F2.
