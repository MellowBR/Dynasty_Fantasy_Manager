# Handoff — Sessão E4-d-F1 (16/06/2026 pt2)

## Natureza

Diagnose **read-only** (MAN-E4-d-F1). Nenhum arquivo de código alterado, nenhuma
escrita no banco, nenhum item marcado resolvido. E4-d permanece **🔲**.

Só docs tocadas: `improvements.md` (achados absorvidos na seção E4-d) + este handoff.

## Pergunta da diagnose

Como cada porta de aquisição do `/auction` resolve identidade de jogador e de time
hoje; se o matching frouxo está replicado além dos 2 pontos do AUD1; e se a régua
canônica de identidade (resolver E4-a, lookup por sid, guard E4-b) aplica como está.

## Achados (resumo — detalhe completo no E4-d de improvements.md)

**Mapa das 4 portas:**
- **FA individual / Rookie individual / Bulk:** jogador por `Player.name.ilike(nome)`
  exato-ci, escopado a `team_id`, **sem normalização e sem sid**. Time por
  `filter_by(name=)` **exato**. Jogador miss → `record_acquisition` cria **órfão
  silencioso sem sid** (parece sucesso). Time miss → 404 / erro visível (seguro).
- **Excel:** jogador por `find_player_by_name()` (normalizado, melhor, mas **sem sid**
  e sem escopo de time); miss → skip+erro (seguro). Time por
  `Team.name.ilike('%nome%')` **substring** → casa **time errado em silêncio**.

**Replicação (resposta explícita):**
- Jogador-sem-sid: replicado nas 3 portas individuais + variante no Excel —
  **tudo dentro de `auction.py`**, não vaza p/ outras rotas (o outro chamador de
  `record_acquisition`, `draft_import`, já é sid-first; `roster.py:332` é busca de UI).
- Time-substring: **isolado em 1 linha** (`auction.py:219`). Nenhuma outra rota usa
  substring de time. Sem replicação do bug de time.

**Régua canônica exige ADAPTAÇÃO:** o resolver `_resolve_entry_sid` (E4-a) desambigua
por **NFL team**; os forms do `/auction` enviam só nome + time **fantasy**, sem NFL
team nem sleeper_id. Name-only: nome único no pool → resolve sid; nome ambíguo (Brown)
→ None → porta deve degradar p/ miss visível / needs_review, nunca órfão.

**Modelo bom a espelhar:** `draft_import` (sid-first: `find_player_by_sleeper_id` +
passa `sleeper_player_id` ao helper) + guard E4-b (import_csv).

## Parecer de escopo p/ F2 (sem implementação)

1. **Time/Excel:** trocar substring por match exato + miss visível. ~1 linha, isolável.
2. **Jogador/4 portas:** unificar numa régua sid-first espelhando `draft_import`,
   reusando resolver E4-a + lookup por sid + guard E4-b (sem duplicar). Pool lazy.

## Decisões de escopo EM ABERTO (owner decide antes da F2)

- **(A)** Adicionar campo NFL team aos forms do `/auction` (Brown-safe completo) **ou**
  aceitar resolução name-only (ambíguos → needs_review)?
- **(B)** Fatiar: F2 = só o time do Excel (mínima) + item separado p/ a unificação
  sid-first das 4 portas, **ou** tudo num F2?
- **(C)** Promover prioridade? A FA auction 2026 é o 1º uso real do `/auction` (ver F9)
  — o fix de identidade idealmente entra antes do registro em massa real.

## Estado

- Nada commitado nesta sessão (decisão do owner; é só diagnose docs). Pode ser
  agrupada com o próximo commit de código, ou commitada isolada como docs-only.
- F9 da sessão anterior já está commitado e pushado (`1ad8bd2`) — smoke prod pendente.
