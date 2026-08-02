# Handoff — Fantasy Manager — 02/08/2026 (arco S2 → S3 → S4)

> Sessão Opus. 7 commits. Fecha o **S3 ✅** (com smoke em produção) e deixa o **S2** pronto para a F2.
> **Estado do sync: RELIGADO** (suspensão encerrada em 02/08/2026).

---

## 1. O que aconteceu, em uma frase

O item S2 ("sync ingere trocas administrativas de picks") foi registrado a partir de um sintoma do
rookie draft; a diagnose **refutou a premissa central do próprio registro**, formalizou o mecanismo
real, e no caminho descobriu um bug **bloqueante e não relacionado** (S3) que foi diagnosticado,
corrigido e validado em produção na mesma sessão.

---

## 2. Commits (ordem cronológica)

| commit | o que é |
|---|---|
| `03a1f5d` | **S2 REG** — registro do item (docs) |
| `1949ac0` | **S2-F1a** — retrato read-only do estado; refuta a premissa central |
| `94ff868` | **S2-F1b** — formaliza o mecanismo, deriva o alvo, recomenda escopo; registra o S3 |
| `be16de1` | **S3-F1** — reproduz a duplicação com o código real sobre cópia |
| `f4b1b40` | **S4 REG** — registro do colateral (docs) |
| `89dc08d` | **S3-F2** — **código**: picks casadas por id de time |
| (este) | **S3-DONE** — fechamento com smoke prod + migração O3 |

---

## 3. S3 — ✅ CONCLUÍDO

**Problema:** o sync renomeia `Team.name` a partir do Sleeper, mas `Pick` era casada por **string de
nome**, e o rename não cascateava. O time 9 já estava renomeado no Sleeper ("Tropa do Bicampeonato"
→ "Tropa do Jarra") e não ingerido: o próximo sync criaria **9 picks duplicadas**.

**Fix (`89dc08d`), desenho (A), sem schema e sem migração** — os ids já existiam e já estavam
corretos em 100% das linhas:

1. `_ensure_default_picks` indexa por `(season, round, original_team_id)` — era daqui que nasciam as duplicatas
2. `_sync_traded_picks` casa por `original_team_id` (cópia literal do padrão de `_sync_trades:670`)
3. Join da projeção migra para `team_id`; `_build_default_draft_order` devolve `(pick_number, team_id, team_name)`
4. `_refresh_pick_team_names` (passo 11b do `run_sync`) — nome vira display derivado, idempotente

**Por que o join TEVE de ir para id:** refrescar `DraftLotteryResult.team_name` quebraria o verify
do M8 (compara o nome congelado no `pool_json` com a tabela viva). Restrição forçada, não estética.

**Smoke prod aprovado** (hash live `89dc08d`, gate PROC1; backup `/data/dynasty_pre_s3_smoke_2026-08-02.db`):
`/picks` 12 linhas/temporada e 108 picks · `/league` correto · verify do lottery conferindo ·
dynasty resolvendo no `/trades`. **O sync foi religado e a 1ª execução ingeriu o rename do time 9
sem duplicação**, com projeção #11 preservada.

---

## 4. S2 — 🔲 PENDENTE (F2 é o próximo passo)

**A premissa do registro original estava errada.** As trocas administrativas **não são transações** —
foram feitas por ferramenta de comissário, que altera `/traded_picks` **sem gerar transação**.
`_sync_trades` nunca as viu. A porta é **`_sync_traded_picks`**. Não existe **nenhuma** trade
só-picks em toda a chain (1.123 tx, 53 trades) — filtrar por isso não pegaria nada.

**Mecanismo (provado nas 12 posições):** o Manager exibe **`O(L(π(p)))` com `π = S⁻¹∘L`**, onde
`L` = lottery, `S` = board do Sleeper (standings 2025 invertido) e `O` = dono canônico por trades
reais. `π` é um **4-ciclo puro em {2,3,4,5}**; as outras 8 posições são **imunes por construção**.

**Dano atual: 4 de 12 posições** do R1 2026 (2, 3, 4 e 5). O estado-alvo foi derivado e **coincide
com a leitura direta do board do Sleeper nas 12 posições**. A trade real de 29/07 precisa ser
**re-rotulada** (o ativo é a pick da 3 peat, não a da Fazenda) — desfazer cegamente apagaria o que
o Cangaceiros comprou.

**Recomendação já registrada — desenho (b), 3 fatias:**
- **F2-1** corretiva das 4 linhas por rota admin auditável (molde M8)
- **F2-2** desconto determinístico em `_sync_traded_picks`, escopado a R1 da draft season, armado por flag
- **F2-3** tela que **prescreve** a permutação ao co-admin — sem ela o desconto é aposta na disciplina alheia

**O ponto de costura já está pronto no código:** `_resolve_traded_pick_identity`
(`sync_sleeper.py:407`) é a porta única "entrada de `/traded_picks` → `(season, round, Team
original, Team dono)`". O docstring documenta que o desconto entra **ali**, sobre `orig_team`, em
id e nunca em string. **Nenhum outro sítio precisa ser reaberto.**

⚠️ **Estado vivo:** o sync **reingere a permutação a cada execução**. As posições 2–5 seguem
permutadas e correção manual de dono de pick **não sobrevive** ao próximo sync. Conhecido e
documentado.

---

## 5. S4 — 🔲 registrado, fora do caminho crítico

`PlayerHistory` e `Trade` identificam time **só por nome**, sem chave estável no schema. O
`team_name` está **dentro do índice UNIQUE de dedupe do F8a** → pós-rename o mesmo evento não colide
e a **idempotência do histórico cai**. Exige coluna nova + migração de 1.151 linhas de histórico +
53 de `Trade` + mexer na garantia do rebuild. Não bloqueia nada.

---

## 6. Armadilhas desta sessão (ler antes de mexer nesta área)

- **`import app` dispara `run_sync()` de verdade.** `data/dynasty_rosters_clean.csv` existe na
  máquina local → `fresh_import` fica truthy → o boot roda o sync contra a API. Toda validação desta
  sessão usou **Flask mínimo apontando para cópia**, com payloads do Sleeper capturados em JSON.
  Nunca importe `app.py` num smoke local desta área.
- **Nunca aponte `DYNASTY_DB` para o caminho padrão em smoke local** (regra já no `DEV_METHODOLOGY`):
  o `dynasty.db` da raiz é o **seed versionado**, consumido por optimizer/predictor.
- **`/data/dynasty.db` é produção; `/opt/render/project/src/dynasty.db` é o seed.** O levantamento
  da F1a **não** conseguiu acessar prod (Render Shell indisponível) e correu sobre o snapshot de
  prod commitado em 31/07 (`326324a`) — limitação declarada no registro.
- **Não existe invariante "≤12 picks por time"** — um time acumula picks alheias via trade
  (Cangaceiros tem 16). Duas asserções minhas caíram na validação por isso; o errado era o teste.

---

## 7. Correções que fiz sobre o meu próprio trabalho

Registradas para que quem ler o histórico não tropece nos números antigos:

- **F1a disse "3 posições divergentes"; são 4.** A comparação usava um canônico que ainda carregava
  o rótulo errado da trade de 29/07, e a posição 2 passou como OK. Corrigido na F1b.
- **F1b disse que dois sítios duplicam; só um duplica.** `_ensure_default_picks` roda primeiro e já
  cria as linhas com o nome novo, que o `_sync_traded_picks` então encontra e apenas atualiza. Dano
  9, não 18. Corrigido na S3-F1 por reprodução.
- **O "17 picks do Cangaceiros" da S3-F1 era o valor inflado** pela duplicação, não a baseline (16).

---

## 8. Próximo passo

**S2-F2**, começando pela fatia corretiva (F2-1). A costura no código já existe; o estado-alvo já
está derivado e verificado na seção do S2 em `improvements.md` (tabela das 12 posições).
