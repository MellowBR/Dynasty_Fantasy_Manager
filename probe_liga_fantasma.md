# Probe da liga fantasma — leitor read-only da API do Sleeper

> **Ferramenta de diagnose, não código do projeto.** Guardada como documento de propósito: é um
> script **ad-hoc**, sem testes e sem dono, que não deve virar dependência de nada. Copie, rode,
> descarte.
>
> **Origem:** `MAN-OFF26-4-PROBE` (03/08/2026), que derrubou o bloqueador do [[OFF26-4]]. Os
> achados estão registrados em `improvements.md`, na seção do OFF26-4 — **este arquivo guarda só o
> instrumento**.

## Por que guardar

O probe **vai ser rodado de novo**, pelo menos três vezes:

1. **A cada RESET DRAFT** — o `draft_id` **muda** e o anterior morre (404). Este script redescobre
   o vigente a partir do `league_id`, que é estável.
2. **Antes de abrir o leilão** — conferir o board populado contra a keeper sheet, enquanto a
   auditoria [[OFF26-4]] não existe como código.
3. **Depois de rodar um draft de teste** — a confirmação **pós-draft** do `is_keeper` que o
   [[OFF26-11]] aguarda, e que ficou **fora do escopo** do probe de 03/08.

## ⛔ Regras

- **Read-only estrito.** Só `GET`. Nenhuma escrita, por nenhum canal.
- **Só a API pública** (`api.sleeper.app/v1`) — o mesmo `BASE_URL` de `sync_sleeper._get`.
  **Endpoints internos não documentados estão descartados por decisão registrada** (sem contrato,
  provável violação de ToS, expõem a conta de comissário da liga real).
- **Não iniciar o draft. Não executar RESET DRAFT.**
- Rodar de fora do projeto (scratchpad/temp). **Não commitar como `.py`.**

## Dados da liga

| campo | valor | estabilidade |
|---|---|---|
| `league_id` | `1389725099556372481` | **estável** — é o que se guarda |
| `draft_id` | **muda a cada reset** | derivar sempre; nunca reaproveitar anotado |

Em 03/08/2026 o `draft_id` vigente era `1389755381567213568` e o anterior
(`1389725100684611584`) já respondia **404**. **Se o número acima não bater, o script te diz qual
é o vigente — é essa a primeira coisa que ele faz.**

## O script

Salve como `probe.py` fora do repositório e rode com `PYTHONIOENCODING=utf-8 python probe.py`
(sem isso, o console do Windows quebra nos acentos e no `Σ`).

```python
"""Probe READ-ONLY da liga fantasma (Sleeper). Só GET. Não inicia draft, não reseta."""
import json
from collections import defaultdict

import requests

BASE = "https://api.sleeper.app/v1"
LEAGUE = "1389725099556372481"          # estável
ESPERADO = {3: (10, 148), 4: (8, 95), 5: (6, 60)}   # ajuste p/ a keeper sheet vigente


def g(path, timeout=15):
    r = requests.get(f"{BASE}{path}", timeout=timeout)
    return r.status_code, (r.json() if r.status_code == 200 else None)


# ---- P1: derivar o draft_id vigente (NUNCA reaproveitar um anotado) ----
sc, lg = g(f"/league/{LEAGUE}")
draft_id = lg.get("draft_id")           # caminho barato: vem no objeto da liga
print(f"[P1] league={lg.get('name')!r} status={lg.get('status')!r} season={lg.get('season')}")
print(f"[P1] draft_id VIGENTE = {draft_id}")
sc, drafts = g(f"/league/{LEAGUE}/drafts")   # caminho alternativo, p/ conferência
print(f"[P1] /drafts -> {len(drafts)} draft(s): "
      f"{[(d['draft_id'], d['status']) for d in drafts]}")
print(f"[P1] roster_positions ({len(lg['roster_positions'])} slots): {lg['roster_positions']}")
print(f"[P1] ATENÇÃO: league.settings.draft_rounds={lg['settings'].get('draft_rounds')} "
      f"NÃO é a contagem boa — usar rounds do DRAFT")

# ---- P2/P3: designações pré-draft, com valor ----
sc, drf = g(f"/draft/{draft_id}")
print(f"\n[P2] draft.status={drf['status']!r} type={drf['type']!r} "
      f"rounds={drf['settings']['rounds']} budget={drf['settings']['budget']}")
sc, picks = g(f"/draft/{draft_id}/picks")
print(f"[P2] {len(picks)} designações (funciona com status=pre_draft)")

by_roster = defaultdict(list)
for p in picks:
    by_roster[p["roster_id"]].append(p)

print(f"\n[P3] {'roster':<8}{'n':<5}{'soma':<8}{'esperado':<12}confere")
for rid in sorted(by_roster):
    ps = by_roster[rid]
    tot = sum(int(p["metadata"]["amount"]) for p in ps if p["metadata"].get("amount"))
    exp = ESPERADO.get(rid)
    ok = "-" if not exp else ("SIM" if (len(ps), tot) == exp else "*** NAO ***")
    print(f"     {rid:<8}{len(ps):<5}{tot:<8}{str(exp):<12}{ok}")

# ---- P4: pontes de identidade + is_keeper (OFF26-11) ----
print(f"\n[P4] is_keeper distintos: {sorted({p['is_keeper'] for p in picks}, key=str)}")
print(f"[P4] picked_by distintos:  {sorted({repr(p['picked_by']) for p in picks})}")
nao_num = [p['player_id'] for p in picks if not str(p['player_id']).isdigit()]
print(f"[P4] player_id NÃO numéricos (DEF vem como sigla): {nao_num}")

sc, ros = g(f"/league/{LEAGUE}/rosters")
nulos = [r["roster_id"] for r in ros if not r.get("owner_id")]
print(f"[P4] owner_id NULO em {len(nulos)}/{len(ros)}: {nulos}")

# ---- P5: budget por time NÃO existe na API (só soma) ----
print(f"\n[P5] roster.settings (sem campo de budget): {ros[0]['settings']}")
print(f"[P5] budget global do draft: {drf['settings']['budget']} -> por time, derivar por soma")

# ---- detalhamento de um time (conferência nominal) ----
ALVO = 3
print(f"\n[detalhe] roster_id={ALVO}")
for p in sorted(by_roster.get(ALVO, []), key=lambda x: x["pick_no"]):
    m = p["metadata"]
    print(f"  pick={p['pick_no']:<3} {m['first_name'][:1]}. {m['last_name']:<14}"
          f"{m['position']:<5}{m['team']:<5}${m['amount']:<5}is_keeper={p['is_keeper']}")
```

## O que cada bloco responde

| bloco | pergunta | resposta obtida em 03/08 |
|---|---|---|
| **P1** | dá para derivar o `draft_id` do `league_id`? | **sim, por dois caminhos**; o morto **não aparece** na lista |
| **P2** | a API expõe designações **antes** do draft? | **sim** — `/draft/{id}/picks` com `status: pre_draft` |
| **P3** | o **salário** é legível pré-draft? | **sim**, `metadata.amount` (**string**) — totais bateram exatos |
| **P4** | como se identifica jogador e time? | `player_id` (= `sleeper_player_id`) e `roster_id`; `picked_by` vazio |
| **P5** | há budget por time? | **não** — só o global; derivar por soma |

## Armadilhas que o script já contorna

- **`player_id` de DEF é sigla** (`"LAR"`), não número — **nunca** faça `int(player_id)`.
- **`metadata.amount` é string** — coagir na leitura.
- **Duas contagens de rodadas divergem:** `league.settings.draft_rounds` × `draft.settings.rounds`.
  **A boa é a do draft.**
- **Draft morto responde 404 limpo** (não trava) — o travamento em LOADING é do **app web**.

## O que este script ainda NÃO faz

- **A confirmação pós-draft do `is_keeper`** ([[OFF26-11]]): exige **rodar um draft de teste** sobre
  o board populado e reler `/draft/{id}/picks` **com `status: complete`**, comparando o campo. O
  script serve para a releitura; **quem tem de rodar o draft é o owner**, e isso **destrói o estado
  pré-draft** — decisão dele, não passo automático.
- **A costura `roster_id` ↔ time do Manager** — depende de `owner_id`, que só aparece quando os
  convites forem aceitos (D6 da spec do [[OFF26-4]]).
  > **Atualização (MAN-OFF26-4-OWNERCHECK, 03/08/2026):** com **8 dos 12** convites aceitos, a
  > costura foi conferida à parte e **casou 8/8** contra `Team.sleeper_owner_id` — resultado e
  > método na seção do [[OFF26-4]], junto ao D6. O bloco `[P4]` acima (`owner_id` nulo em N/12)
  > continua sendo a **medição de cobertura**: rodá-lo de novo diz **quantos owners ainda faltam**.
  > Os 4 restantes (rosters 9–12) **não se resolvem por leitura** — dependem de aceite.
