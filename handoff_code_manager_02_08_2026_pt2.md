# Handoff pt2 — Fantasy Manager — 02/08/2026 (fechamento do arco S2 → S5)

> Continuação de `handoff_code_manager_02_08_2026.md` (que cobre S2-REG → S3-DONE).
> Esta parte cobre **S2-F2** e **S2-DONE**. **O arco está fechado: S2 ✅ e S3 ✅, ambos com smoke em produção.**

---

## 1. Estado final

| item | estado |
|---|---|
| **S2** — sync ingere permutação administrativa de picks | **✅ 02/08/2026** (smoke prod, hash `9b4bcf1`) |
| **S3** — rename de time quebra o match de picks | **✅ 02/08/2026** (smoke prod, hash `89dc08d`) |
| **S4** — `PlayerHistory`/`Trade` sem chave estável de time | 🔲 não iniciado, não bloqueia |
| **S5** — tela que prescreve a permutação ao co-admin (ex-F2-3) | 🔲 não iniciado, não bloqueia |

**Operacional:** sync **liberado**, com o desconto **armado para 2026**. O rollover **desarma
sozinho** — o armamento guarda a *season*, não um booleano.

---

## 2. O fix do S2, em uma tela

`board_mirror.py` deriva **π = S⁻¹∘L** (`L` = `DraftLotteryResult`, `S` = `_build_default_draft_order`
— a mesma fonte única do M15/M16) e re-chaveia a entrada de `/traded_picks` para picks de **R1 da
draft season armada**. Isso **aniquila a ficção**: os movimentos puramente administrativos viram
no-ops (`pick de X → X`) e a trade real da janela é **re-rotulada sozinha**.

Três salvaguardas que valem lembrar antes de mexer:

1. **Bijeção obrigatória.** Se π não for bijetiva, `build_permutation` devolve `{}` e o desconto
   **não opera**. Board meio-montado desliga em vez de corromper — rótulo errado com cara de certo é
   pior que o bug conhecido.
2. **Armamento por season, não booleano.** `AppConfig["board_mirrored_season"]`. O rollover avança
   `current_season`, o valor deixa de casar, desarma. Um booleano dispararia o desconto no ano
   seguinte sobre board não montado.
3. **Toggle explícito, não detecção.** A montagem **não deixa rastro** (não é transação). Detectá-la
   seria inferir intenção a partir de ausência de evidência.

**Dois sítios ligados** — `_resolve_traded_pick_identity` (a costura que o S3 deixou pronta) **e** o
loop de picks do `_sync_trades`. O segundo foi extensão deliberada além da letra do prompt: sem ele,
uma trade real fechada na janela faria o passo 12 sobrescrever com rótulo errado o que o passo 11
gravou certo. Os outros dois chamadores de `_sync_trades` (backfill de ligas anteriores) não passam
desconto → identidade por default de parâmetro.

---

## 3. Smoke em produção (02/08/2026)

Hash live `9b4bcf1`; backup `/data/dynasty_pre_s2_smoke_2026-08-02.db`. Armado via `/admin` → sync.

- pos. **2** = Fazenda Pederasta, **sem troca**; pos. **5** = 3 peat → **Cangaceiros** (re-rótulo da
  trade de 29/07); pos. **3 e 4** com donas originais corretas
- **cruzamento com o board do Sleeper confere** — `1.05` via `fernandoxmf` no roster MellowBR
- **2ª execução do sync sem nenhuma alteração** — idempotência confirmada **em produção**
- verify do lottery 2026 conferindo; pos. 1 e 6–12, R2/R3 e futuras intactos

O alvo era, desde a derivação da F1b, **"o que o board já exibia"**. O Sleeper sempre esteve certo
na *sequência* e errado na *titularidade*; o Manager é que re-permutava ao projetar. Agora os dois
contam a mesma história.

---

## 4. F2-1 não foi implementada — de propósito

A F1b previa uma rota admin corretiva. **É redundante:** as 4 entradas administrativas re-chaveadas
formam uma **bijeção** sobre exatamente as 4 linhas divergentes, então o próprio sync as reescreve.
A correção do estado foi **armar + rodar o sync**. Implementar a rota teria produzido código morto.
Se aparecer um caso futuro em que a bijeção não cobre tudo, a decisão precisa ser reavaliada.

---

## 5. Nota de método (vale além deste arco)

O prompt da F2 trazia como critério de validação **"posição 2 → Cangaceiros via pick da 3 peat"** —
o que **contradizia a tabela-alvo da própria F1b**, citada pelo mesmo prompt como autoridade. O alvo
correto é **pos. 2 → Fazenda** e **pos. 5 → Cangaceiros**; "Cangaceiros na 2" era o estado
**permutado**, ou seja, o defeito. A correção partiu do Code, conferindo o critério contra a tabela
derivada **antes** de implementar; o smoke em produção confirmou a leitura corrigida.

Isso amplia o [[MAN-METH-REG]]: a regra candidata falava em refutar premissas do prompt **contra o
código**. Este caso mostra que ela vale também **contra artefatos derivados em fases anteriores**.
Aceitar o critério como dado teria produzido um fix "validado" contra o alvo errado — e o erro só
apareceria no ano seguinte.

---

## 6. Armadilhas (repetidas da pt1, porque continuam valendo)

- **`import app` dispara `run_sync()` de verdade** — `data/dynasty_rosters_clean.csv` existe local →
  `fresh_import` truthy. Toda validação usou Flask mínimo sobre cópia, com payloads capturados.
- **Nunca aponte `DYNASTY_DB` para o caminho padrão em smoke local** — é o seed versionado.
- **`/data/dynasty.db` é produção**, `/opt/render/project/src/dynasty.db` é o seed.
- **Não existe invariante "≤12 picks por time"** — um time acumula picks alheias via trade.
- Harness de render precisa de `user_loader`, filtro `utc_iso` e stub do blueprint `auth`
  (`base.html` usa `url_for('auth.logout')`).

---

## 7. Próximos passos sugeridos (nenhum urgente)

- **S5** — tela prescritiva. Remove o conhecimento tácito da montagem; a F1 deve decidir se além de
  prescrever ela também **verifica** a montagem contra π (barato, e a F1a já fez isso à mão).
- **S4** — chave estável em `PlayerHistory`/`Trade`. Toca schema, migração de 1.151 + 53 linhas e o
  índice UNIQUE de dedupe do F8a.
