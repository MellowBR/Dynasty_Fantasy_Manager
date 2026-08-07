"""
keeper_exclusion.py — OFF26-11: a keeper sheet como LISTA DE EXCLUSÃO do importador.

Decisão do owner (06/08/2026, MAN-OFF26-10-SPEC — **opção A**): o Manager é fonte única
da verdade sobre quem é keeper. No import do resultado do leilão de 24/08 o importador
([[OFF26-3]]) ingere **apenas os arremates**; keeper designado no board é **excluído por
definição**. A garantia de que board e sheet conferem é a auditoria [[OFF26-4]], que roda
**ANTES** do leilão, como gate. **Não há reconciliação pós-leilão** — este módulo nunca
compara salário de keeper e nunca emite divergência.

## Por que o discriminador não pode vir do Sleeper

A designação de keeper no board da liga fantasma chega pela API com **`is_keeper: false`**
(24/24 designações, medido em 03/08 e reconfirmado em 07/08/2026): o Sleeper trata a
designação como *pick forçado de leilão*, não como keeper. O campo **não discrimina**.
Ele permanece **registro, nunca insumo** — nenhuma linha deste módulo o lê.

## Por que a lista tem de ser CONGELADA (requisito de correção, não de robustez)

A keeper sheet nasce do **roster vivo** (U7 do [[OFF26-10]]), e o checklist pós-leilão
prevê que **cada owner adicione seus arremates manualmente na liga real**. Um sync entre o
leilão e o import faz o arremate **aparecer como keeper** — e ele seria excluído da
ingestão, que é o **dano invertido**: o contrato ano 1 do arremate simplesmente não nasce.

O caso canônico do owner é exatamente esse: jogador de **$50** dropado na janela, a leilão,
**recomprado pelo mesmo time por $50**. Valor idêntico, natureza diferente — o contrato
antigo morreu e nasce um contrato **ano 1**. Se o sync já o devolveu ao roster, uma lista
derivada ao vivo o chamaria de keeper.

**Mecanismo escolhido: CONGELAMENTO EXPLÍCITO (snapshot com hash).** Um ato de admin, num
instante nomeado — entre o sync final (sheet DEFINITIVA) e o leilão —, materializa a lista
em `AppConfig` e é ela, e só ela, que o importador consome. Ver `freeze_exclusion_list`.

Alternativas descartadas e por quê:
  · **derivar ao vivo no import** — é o bug (contaminação acima);
  · **gatear por carimbo de sync** ("recusar se houve sync depois da revelação") — recusa
    o import justamente no estado em que ele é correto, e não distingue o sync do drop do
    sync que trouxe arremates;
  · **snapshot automático no 1º preview** — congela sem que ninguém tenha declarado que
    aquele era o momento; se o 1º preview for depois da contaminação, congela o erro.

**O que o congelamento NÃO cobre** (declarado, não mitigado):
  1. congelar TARDE — se o admin congelar depois de owners já terem adicionado arremates
     na liga real, a lista nasce contaminada. Mitigação é operacional: o snapshot carrega
     `sync_timestamp` e `frozen_at`, a tela os exibe, e o runbook fixa o momento;
  2. keeper que o board **não** designou — isso é exposição ao leilão e é matéria da
     auditoria [[OFF26-4]], que roda antes; aqui ele só não aparece entre os picks;
  3. erro na própria sheet definitiva (drop revelado não executado no Sleeper) — o selo
     PROVISÓRIA já bloqueia o congelamento, mas um sync tardio pode virar o selo sem que
     os drops tenham sido executados; quem prova isso é o operador, não este módulo.

## Organização (mesmo princípio do `salary_engine` e do `keeper_audit`)

  · **NÚCLEO PURO** — `build_index` / `classify_pick`: sem DB, sem rede, sem Flask.
  · **IO** — `build_exclusion_source` (lê os dois produtores já existentes da sheet),
    `freeze_exclusion_list` / `get_frozen_exclusion` / `clear_frozen_exclusion`,
    `exclusion_gate` (o bloqueio que o importador consulta).

⛔ **Nenhuma segunda definição de "quem é keeper".** A lista vem de
`keeper_audit.build_sheet` (o produtor que já enriquece a sheet com `sleeper_player_id`) e
o estágio provisória × definitiva vem de `routes.cuts._build_keeper_sheet` (a fonte única
do selo). Este módulo não consulta roster, não filtra `is_dropped`, não decide keeper.

⛔ **Identidade só por `sleeper_id`** — nunca por nome, nem como desempate (incidente
"Brown"). `player_id` de DEF é **sigla** (`"LAR"`): a chave é sempre STRING, jamais coagida
a inteiro.
"""
import hashlib
import json
from datetime import datetime

# Chave única do snapshot congelado (AppConfig.value é Text — cabe o JSON).
FROZEN_KEY = "keeper_exclusion_frozen"

# ── Classificação de um pick (núcleo puro) ───────────────────────────────────
KIND_ARREMATE = "arremate"                  # ingerir (contrato ano 1)
KIND_KEEPER = "keeper"                      # excluir — não ingerir, não escrever nada
KIND_KEEPER_OTHER = "keeper_de_outro_time"  # PENDÊNCIA: bloqueia a confirmação
KIND_NO_ID = "sem_identidade"               # PENDÊNCIA: id do Sleeper ausente
KIND_NO_TEAM = "sem_time_local"             # PENDÊNCIA: roster não mapeado → não classificável

# Só estes três são pendência. Nenhum deles é "pulo silencioso": todos bloqueiam.
PENDING_KINDS = (KIND_KEEPER_OTHER, KIND_NO_ID, KIND_NO_TEAM)

KIND_REASON = {
    KIND_KEEPER_OTHER: (
        "Jogador consta na lista de exclusão como keeper de OUTRO time, e o board o "
        "designou para este. É a divergência mais grave da auditoria acontecendo ao vivo "
        "— o importador não arbitra sozinho quem é o dono."),
    KIND_NO_ID: (
        "Pick sem `player_id` do Sleeper: sem identidade resolvível não há como dizer se é "
        "keeper ou arremate (identidade SÓ por sleeper_id — nunca por nome)."),
    KIND_NO_TEAM: (
        "O roster deste pick não está mapeado a um time do Manager: sem saber de quem é o "
        "pick, o discriminador não consegue classificá-lo."),
}


def _sid(v):
    """Id de jogador é STRING sempre — DEF vem como sigla ('LAR'). Nunca coagir."""
    s = str(v or "").strip()
    return s or None


# ══════════════════════════════════════════════════════════════════════════════
# NÚCLEO PURO — sem DB, sem rede. Entra dado, sai classificação.
# ══════════════════════════════════════════════════════════════════════════════

def build_index(keepers: list) -> dict:
    """`[{sleeper_player_id, team_id, ...}]` → `{sid: entrada}`. Chave STRING.

    Keeper sem `sleeper_player_id` NÃO entra no índice (não se inventa identidade). O
    congelamento recusa a lista nesse estado — ver `freeze_exclusion_list`.
    """
    index = {}
    for k in keepers or []:
        sid = _sid(k.get("sleeper_player_id"))
        if sid:
            index[sid] = k
    return index


def classify_pick(sleeper_player_id, pick_team_id, index: dict) -> str:
    """Classifica UM pick do leilão contra a lista de exclusão congelada.

    Regra única (a decisão A inteira cabe aqui): **um pick cujo jogador consta na lista
    para o MESMO time do pick é keeper** — não é ingerido. Consta para outro time é
    pendência. Não consta é arremate.
    """
    sid = _sid(sleeper_player_id)
    if not sid:
        return KIND_NO_ID
    if pick_team_id is None:
        return KIND_NO_TEAM
    entry = index.get(sid)
    if entry is None:
        return KIND_ARREMATE
    return KIND_KEEPER if entry.get("team_id") == pick_team_id else KIND_KEEPER_OTHER


def compute_exclusion_hash(keepers: list) -> str:
    """Hash verificável da lista congelada (ordem-independente, molde M8 em espírito:
    o snapshot é auditável e re-derivável)."""
    canon = sorted(
        [[_sid(k.get("sleeper_player_id")), k.get("team_id"), int(k.get("salary") or 0)]
         for k in keepers or []],
        key=lambda r: (str(r[0]), r[1] or 0))
    blob = json.dumps(canon, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# IO — leitura dos produtores existentes da sheet + persistência do congelamento
# ══════════════════════════════════════════════════════════════════════════════

def build_exclusion_source(season: int) -> dict:
    """Lê a sheet pelos DOIS produtores já existentes — nenhuma definição nova.

    · `keeper_audit.build_sheet(season)`   → keepers enriquecidos com `sleeper_player_id`
                                             e o time por `sleeper_owner_id` (D3);
    · `routes.cuts._build_keeper_sheet`    → selo `stage` (provisória × definitiva), que
                                             `build_sheet` não repassa.

    Os dois são lidos separadamente **de propósito**: o payload que a auditoria consome
    não é tocado por este item (restrição da F2). O custo é uma segunda montagem da sheet
    num caminho de admin usado uma vez por temporada.
    """
    from keeper_audit import build_sheet
    from routes.cuts import _build_keeper_sheet

    raw = _build_keeper_sheet(season)
    enriched = build_sheet(season)

    keepers, missing_id = [], []
    for t in enriched.get("teams") or []:
        for sid, name, position, salary in t.get("keepers") or []:
            row = {
                "sleeper_player_id": _sid(sid),
                "team_id": t["team_id"], "team_name": t["team_name"],
                "name": name, "position": position, "salary": int(salary or 0),
            }
            if row["sleeper_player_id"]:
                keepers.append(row)
            else:
                missing_id.append(row)

    return {
        "season": season,
        "available": bool(raw.get("available")),
        "stage": raw.get("stage"),
        "stage_label": raw.get("stage_label"),
        "sync_timestamp": raw.get("sync_timestamp"),
        "late_drop": raw.get("late_drop") or {},
        "num_teams": len(enriched.get("teams") or []),
        "keepers": keepers,
        "keepers_sem_id": missing_id,
    }


def get_frozen_exclusion(season: int | None = None) -> dict | None:
    """Snapshot congelado, ou None. Se `season` for dado, exige que case."""
    from models import get_config
    raw = get_config(FROZEN_KEY, "") or ""
    if not raw.strip():
        return None
    try:
        snap = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(snap, dict) or not isinstance(snap.get("keepers"), list):
        return None
    if season is not None and snap.get("season") != season:
        return None
    return snap


def freeze_exclusion_list(season: int, executed_by=None, reason: str = "") -> dict:
    """Congela a lista de exclusão. Retorna `{"error": ...}` em vez de levantar.

    Recusa (cada uma com causa própria — nunca degrada para "congela assim mesmo"):
      · sheet indisponível;
      · sheet **PROVISÓRIA** — o late drop ainda não está refletido nos rosters;
      · keeper sem `sleeper_player_id` — auditoria incompleta, e sem id ele viraria
        arremate no import (falso negativo silencioso, o dano invertido);
      · re-congelamento sem justificativa (molde M8: substituir snapshot exige razão).
    """
    from models import set_config

    src = build_exclusion_source(season)
    if not src["available"]:
        return {"error": "Keeper sheet indisponível — não há o que congelar.",
                "state": "indisponivel", "source": src}
    if src["stage"] != "definitiva":
        return {"error": (
            "A keeper sheet ainda está PROVISÓRIA: a urna do late drop não revelou, ou "
            "não houve sync DEPOIS da revelação. Execute os drops no Sleeper, rode o sync "
            "final e congele então — congelar agora fixaria uma lista que ainda vai mudar."
        ), "state": "provisoria", "source": src}
    if src["keepers_sem_id"]:
        nomes = ", ".join(f"{k['name']} ({k['team_name']})" for k in src["keepers_sem_id"])
        return {"error": (
            f"{len(src['keepers_sem_id'])} keeper(s) sem `sleeper_player_id` no Manager: "
            f"{nomes}. Sem id não há identidade resolvível — no import eles seriam lidos "
            f"como arremate. Resolva o vínculo (sync) antes de congelar."
        ), "state": "sem_identidade", "source": src}

    previous = get_frozen_exclusion()
    reason = (reason or "").strip()
    if previous and not reason:
        return {"error": ("Já existe uma lista congelada para "
                          f"{previous.get('season')} ({previous.get('num_keepers')} "
                          f"keepers). Re-congelar exige justificativa."),
                "state": "ja_congelada", "previous": previous}

    keepers = src["keepers"]
    snap = {
        "season": season,
        "frozen_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "frozen_by": executed_by,
        "source_stage": src["stage"],
        "sync_timestamp": src["sync_timestamp"],
        "late_drop_executed_at": (src["late_drop"] or {}).get("executed_at"),
        "late_drop_result_hash": (src["late_drop"] or {}).get("result_hash"),
        "num_teams": src["num_teams"],
        "num_keepers": len(keepers),
        "hash": compute_exclusion_hash(keepers),
        "reason": reason or None,
        "previous_hash": previous.get("hash") if previous else None,
        "keepers": keepers,
    }
    set_config(FROZEN_KEY, json.dumps(snap, ensure_ascii=False))
    return {"success": True, "frozen": snap}


def clear_frozen_exclusion():
    """Descongela (limpa o snapshot). Ato de admin, explícito."""
    from models import set_config
    set_config(FROZEN_KEY, "")
    return {"success": True}


def exclusion_gate(season: int) -> tuple:
    """Porta que o importador consulta: `(index, frozen, error)`.

    `error` não-None significa **import bloqueado** — e a mensagem diz qual é o estado e o
    que falta. ⛔ Nunca degradar para "ingerir tudo": sem lista utilizável, todo keeper
    designado no board viraria contrato ano 1.
    """
    frozen = get_frozen_exclusion(season)
    if frozen:
        return build_index(frozen.get("keepers")), frozen, None

    # Sem lista congelada: o diagnóstico vem do estado ATUAL da sheet, para a mensagem
    # dizer o que falta (e não só "faltou congelar").
    stale = get_frozen_exclusion()          # existe, mas de outra season?
    src = build_exclusion_source(season)
    if stale:
        return None, None, {
            "state": "season_errada",
            "error": (f"A lista congelada é da season {stale.get('season')}, e este draft "
                      f"é de {season}. Congele a lista da season correta antes de importar."),
            "source": src,
        }
    if not src["available"]:
        return None, None, {
            "state": "indisponivel",
            "error": ("Keeper sheet indisponível — sem a lista de exclusão o importador "
                      "criaria contrato ano 1 para cada keeper designado no board."),
            "source": src,
        }
    if src["stage"] != "definitiva":
        return None, None, {
            "state": "provisoria",
            "error": ("A keeper sheet está PROVISÓRIA e não há lista congelada. Execute os "
                      "drops revelados no Sleeper, rode o sync final (a sheet vira "
                      "DEFINITIVA) e congele a lista de exclusão antes de importar."),
            "source": src,
        }
    return None, None, {
        "state": "nao_congelada",
        "error": ("A keeper sheet está DEFINITIVA, mas a lista de exclusão ainda não foi "
                  "CONGELADA. Congele-a antes do leilão: depois do leilão os owners "
                  "adicionam os arremates na liga real, e um sync passaria a mostrá-los "
                  "como keepers — eles seriam excluídos da ingestão."),
        "source": src,
    }
