# Handoff — Sessão OFF26-1 F2 / implementação (16/06/2026 pt8)

## Natureza

**Implementação** (MAN-OFF26-1) da janela de cortes selada, sobre a Spec final (REFINE) e o
terreno (F1). Item marcado **⚠️** — e2e localhost verde, **aguarda smoke prod** (lição E1, sem
✅ prematuro).

## O que foi construído

- **`models.py`** — `CutDeclaration` (declaração editável/privada por `(season, team_id)`;
  `cut_ids_json`+`declared`; keepers = complemento) + `CutWindowAudit` (snapshot canônico no
  molde M8) + `compute_cut_snapshot_hash` (SHA256 determinístico). Tabelas novas → `create_all`
  (sem migração).
- **`routes/cuts.py`** (novo blueprint) — `/cuts` + APIs: `state` (contagem agregada, sem
  conteúdo), `declaration` GET/POST (escopo `current_user.team_id` — **sigilo**), `admin/open`
  (gate duro `needs_review`), `admin/close`, `admin/declare` (write-by-team, não lê alheio),
  `admin/lock` (revelação), `admin/replace` (M8 + reason), `audit`, `audit/verify`.
- **`routes/salary.py`** — D9: porta canônica `POST .../budget` ganhou `projected` (default
  `True` intocado; `False` = salário corrente já rollado). Fonte de cálculo segue `draft_budget`
  (sem 2ª rota / aritmética — invariante F10 preservada).
- **`app.py`** — registra `cuts_bp` + seed flag `cuts_window_open`.
- **`routes/offseason.py`** — passo 6 `done` = existe `CutWindowAudit` canônico.
- **`templates/cuts.html`** (novo) + link no passo 6 do `offseason.html`. Cliente só exibe o
  budget; `kept = roster − cortes` é seleção, não aritmética de cap (grep confirma).

## Verificação (e2e localhost, 23/23 + 48/48 salary_engine)

- **Sigilo:** `GET /api/cuts/declaration?team_id=<B>` por A → param ignorado, retorna time de A;
  `state` só conta; admin `declare` retorna `num_cuts`, nunca conteúdo. ✅
- **Default preservado:** budget sem `projected` == `projected:true`. ✅
- **Não-projetado:** `projected:false` usa salário corrente (10), `true` usa projetado (40). ✅
- **Gate:** `open` bloqueado (409) com `needs_review` pendente; libera ao zerar. ✅
- **Default zero cortes:** time sem declaração entra no snapshot com 0 cortes. ✅
- **M8:** 2º lock sem reason → 409; replace sem reason → 400; replace encadeia `previous_id`;
  `verify` hash_match. ✅
- **Não-mutação:** roster/Player intocados após lock+reveal; nada escrito no Sleeper. ✅

## A registrar / lembrar

- **improvements.md** já atualizado: Status Rápido OFF26-1 → ⚠️; seção ganhou subseção **F2**
  (arquivos, validação de sigilo, default preservado, não-mutação, fronteiras).
- **Dependência de dados p/ OFF26-7:** janela pressupõe **E4-a + Rollover (passo 4)** antes da
  abertura (D8) — budget não-projetado lê salário já valorizado. Encadear nessa ordem no dry run.
- **Smoke prod pendente (vira ✅ depois):** abrir janela com `needs_review` real zerado → owner
  declara → admin lock + verify hash → conferir contagem agregada e revelação.

## Estado

- Arquivos de código tocados: `models.py`, `routes/cuts.py` (novo), `routes/salary.py`,
  `app.py`, `routes/offseason.py`, `templates/cuts.html` (novo), `templates/offseason.html`.
  Docs: `improvements.md` + este handoff. Script e2e descartável **removido**.
- Sem push. Commit pode agrupar com docs pendentes do ciclo (pt6 F1, pt7 REFINE).
- `dynasty.db` local: `create_all` adicionou as 2 tabelas novas (aditivo, sem perda).
