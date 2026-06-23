# Handoff — Sessão MAN-E4a-F2-EixoA (23/06/2026 pt2)

## Natureza

F2 do **Eixo A** da diagnose PRODF1 (commit ed3a6e0): filtro de posição no fallback de
candidatos do review ESPN. **Código + docs** (não docs-only). Mudança de código real em
`espn_pdf_parser.py`, validada em localhost. **E4-a e E2-RISK seguem ⚠️** — o flip para ✅
depende de smoke em prod que **não é executável localmente** (ver "Bloqueio honesto").

## O que mudou (código)

`espn_pdf_parser.py`:
- Novo helper `_special_pos_compatible(entry_pos, cand_pos)` + constante `_SPECIAL_POS`.
- Novo ramo especial dentro de `match_players`, **só no modo resolver**
  (`if sid_resolver is not None`): quando a entrada é **D/ST ou K**, recompõe best/candidatos
  **só entre posições compatíveis** (D/ST → DEF/DST; K → K). Sem candidato compatível ≥0.5 →
  **not_found limpo**, em vez de oferecer skill cruzado.
- O **ramo skill segue byte-for-byte** (sem filtro skill×skill — fora do escopo desta fatia).
- **Modo legado (`sid_resolver=None`) intocado** (toda a mudança está dentro do bloco resolver).
- **Não toca:** resolução por sleeper_id, threshold do resolver, matched-by-id / not_found→store,
  `salary_engine`, store ESPN, sync, schema, `SalaryHistory`/`PlayerHistory`. Gate de confirm +
  default neutro do E2-RISK **só confirmados intactos**.

## Validação localhost (✓)

- Harness sintético (`match_players` direto, roster fake com Diggs WR, Sanders RB, Houston
  Texans DEF, Tucker K, Jayden Daniels QB rosterado):
  - **Texans D/ST → not_found** (não oferece Stefon Diggs). *(A DEF do roster existia mas o
    nome "Houston Texans" não cruza 0.5 com "Texans D/ST" → degradação limpa, exatamente o
    alvo: sem skill cruzado.)*
  - **Rams D/ST / Ravens D/ST → not_found** (sem sugestão de Sanders/skill).
  - **Sem regressão:** Carnell Tate (rookie) → not_found via `resolved_sid` (Eixo B intacto);
    Jayden Daniels (vet rosterado) → matched por id.
  - **Modo legado** reproduz o baseline (DST → not_found como antes).
- `salary_engine_test.py` → **48/48 OK**.

## Bloqueio honesto (passos 2 e 3 do prompt NÃO executados)

O prompt pedia, no mesmo passo: (2) colher o **split de prod** (matched-por-id / approximate /
not_found→store) do import real e (3) flipar **E4-a/E2-RISK → ✅**. **Ambos exigem deploy +
import ESPN real em produção** — fora do alcance desta sessão local. O prompt também proíbe
flipar ✅ "por inércia de localhost". Logo:
- Entreguei o **código + a narrativa de status** (mantida ⚠️), com o gate de ✅ explícito.
- **Não flipei ✅** (restrição respeitada).

### Procedimento de smoke prod p/ destravar ✅ (owner)
1. Backup: `sqlite3 /data/dynasty.db ".backup '/data/dynasty_prod_backup_2026-06-23_pre-e4af2.db'"`.
2. Deploy do commit deste handoff no Render.
3. `/admin/espn_import` → upload do mesmo cheat sheet PPR Top 300 → tela de review.
4. Conferir **(a)**: nenhuma D/ST ou K exibe candidato skill (Texans D/ST sem Diggs; Rams D/ST
   sem Sanders; cluster Ravens/Patriots/Lions/Chiefs sem candidato).
5. Colher **(b)** o split: nº de **matched** (por id) / **aproximados** / **não encontrados**
   (o cabeçalho do review já mostra os três; o confirm reporta `total_matched/approx/notfound`
   + o store recebe os not_found skill).
6. Com (a)+(b) OK, marcar **E4-a e E2-RISK → ✅** no `improvements.md` com os números anexados
   e migrar as seções fechadas para o `improvements_archive.md` (regra O3).

> Nota: por o smoke não rodar nesta sessão, o flip ✅ será uma edição de docs posterior. A
> preferência "status viaja com o código" do prompt pressupunha smoke in-session; como não é
> possível, o flip fica gated no smoke do owner (decisão dele sobre como commitar).

## Arquivos tocados

- **Código:** `espn_pdf_parser.py` (helper + ramo especial no modo resolver).
- **Docs:** `improvements.md` (F2-EixoA no E4-a + nota no E2-RISK; ambos seguem ⚠️ com gate
  de ✅), `manager_devplan.md` (log + "Última atualização"), este handoff.
