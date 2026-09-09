"""
contract_regua.py — OFF26-42: régua canônica de contrato VIVO × MORTO (núcleo PURO).

A régua (decisão de liga, 25/08/2026 — fechada no OFF26-37, hoje no archive):
  1. Arrematado no FA auction → contrato NOVO do leilão (coberto pelo importador OFF26-3
     + keeper_exclusion — fora deste módulo).
  2. Adquirido na temporada com contrato VIVO (drop dentro da janela de waiver) → o
     waiver MANTÉM o contrato.
  3. Adquirido SEM contrato vivo (drop de intertemporada, ou janela vencida) → contrato
     NOVO, ano 1.
O discriminante é o ESTADO do contrato, não o canal nem o time.

⭐ ESTE MÓDULO É O ÚNICO LUGAR ONDE A DECISÃO VIVO × MORTO EXISTE (restrição do owner,
09/09/2026). O sync (`sync_sleeper._process_contract_regua`), a arbitragem do admin
(`routes/admin.py`) e qualquer runner de reparo CONSOMEM `decide_readd`; nenhum deles
replica a comparação. O [[WV1]] (janela de waiver como discriminador do canal) é
consumidor FUTURO do mesmo helper. Guarda AST em `contract_regua_test.py`.

Mesma separação do `salary_engine`: aqui NÃO há DB, rede nem Flask — só funções puras
sobre dicts. A camada de IO (varredura de transações, estado NFL, congelamento da lista
de exclusão) vive em `sync_sleeper.py`.

FORMALIZAÇÃO CANÔNICA DA JANELA (decisão 5 do owner, 09/09/2026):
    Δ(add − drop) ≤ waiver_clear_days × 24h  ⇒  contrato VIVO (caso 2)
`waiver_clear_days` vem das settings da liga na API — ⛔ nenhum literal de janela aqui.
O tipo da transação é SINAL DE CORROBORAÇÃO: waiver dentro do Δ e free_agent fora do Δ
confirmam; combinação divergente vira PENDÊNCIA na fila de arbitragem, com os dois
sinais citados.

⚠️ TIMESTAMP DO Δ — REFUTAÇÃO MEDIDA DA DECISÃO 8 (09/09/2026):
A decisão 8 pedia `status_updated` para claim de waiver e `created` para drop/FA — e
mandava conferir contra a medição Jones×Goff. A conferência (tw*.json da liga 2025)
REFUTA a mistura: `status_updated` de claims é o PROCESSAMENTO EM LOTE (difere do
`created` em até ~51h nos dados reais) e:
  - `status_updated` no add: Goff daria Δ 53,1h > 48h → INVERTERIA o veredito arbitrado
    em produção (preservado com 12,3h; reparo executado em 26/08 o deixou intacto);
  - `status_updated` nos dois lados: Jones daria Δ 47,2h < 48h → inverteria o Jones
    (arbitrado morto com 69,2h).
Só `created` NOS DOIS LADOS reproduz o precedente canônico (69,2h / 12,3h) — e a
decisão 5 fixa o precedente Jones×Goff como formalização canônica. `tx_timestamp` é o
ponto ÚNICO da escolha; trocar o campo é uma linha, aqui.
"""

MS_PER_HOUR = 60 * 60 * 1000
HOURS_PER_DAY = 24

# Fases do calendário (decisão 6: derivadas da DATA da transação contra o início da
# temporada NFL em /state/nfl — `offseason_mode` NÃO é fonte; divergência só vai a log).
FASE_INTERTEMPORADA = "intertemporada"
FASE_TEMPORADA = "temporada"

# Ações que `decide_readd` devolve — o executor (sync/arbitragem) só as executa.
ACAO_MANTER = "manter"                  # caso 2: contrato vivo, waiver mantém
ACAO_CONTRATO_NOVO = "contrato_novo"    # caso 3: contrato morto, ano 1 novo
ACAO_PENDENCIA = "pendencia"            # fila de arbitragem do admin
ACAO_INDETERMINADO = "indeterminado"    # sem transação de add na varredura — só warning

# Tipos de pendência (mesma fila, vereditos distintos):
KIND_COMISSARIO_DROP = "comissario_drop"
KIND_COMISSARIO_ADD = "comissario_add"
KIND_SINAL_DIVERGENTE = "sinal_divergente"

# Vereditos válidos por tipo (arbitragem é SEMPRE humana — nenhum caminho aplica o
# sugerido sem ação do admin):
VERDICTS_BY_KIND = {
    KIND_COMISSARIO_DROP: ("real", "manobra"),
    KIND_COMISSARIO_ADD: ("real", "manobra"),
    KIND_SINAL_DIVERGENTE: ("vivo", "morto"),
}

# Canal da transação → acquisition_type do contrato novo (caso 3). Mesmo vocabulário do
# rebuild F8 (`_collect_transaction_events`) para o `fa_waiver`/`free_agent`; add de
# comissário arbitrado "real" entra como free_agent (não há lance nem claim — é a
# semântica de FA; o tipo original fica citado na pendência/notes).
ACQ_TYPE_BY_TX = {
    "waiver": "fa_waiver",
    "free_agent": "free_agent",
    "commissioner": "free_agent",
}

# Canal da transação → event_type do evento de ADD na timeline quando o contrato é
# MANTIDO (caso 2 / manobra). Idêntico ao type_map do rebuild F8 — é o que faz a UNIQUE
# `uq_player_history_event` dedupar o evento ao vivo contra um rebuild futuro.
EVENT_TYPE_BY_TX = {
    "waiver": "fa_waiver",
    "free_agent": "free_agent",
    "commissioner": "commissioner",
}


def tx_timestamp(tx: dict) -> int:
    """O carimbo canônico de uma transação: `created`, NOS DOIS LADOS (drop e add).

    ⛔ Não trocar por `status_updated` sem decisão do owner — ver a refutação medida no
    docstring do módulo (inverteria Goff ou Jones, ambos arbitrados em produção)."""
    return int(tx.get("created") or 0)


def waiver_window_ms(waiver_clear_days) -> int:
    """Janela de waiver em ms — `waiver_clear_days` vem das settings da liga na API.

    ⛔ Nenhum literal de janela: se a liga mudar a config, a régua acompanha sozinha."""
    return int(waiver_clear_days) * HOURS_PER_DAY * MS_PER_HOUR


def season_start_ms(season_start_date: str) -> int:
    """'YYYY-MM-DD' (state/nfl `season_start_date`) → epoch ms UTC (meia-noite).

    A fronteira de fase da decisão 6: transação antes do kickoff da semana 1 =
    intertemporada; depois = temporada."""
    from datetime import datetime, timezone
    dt = datetime.strptime(season_start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def phase_of(ts_ms: int, start_ms: int) -> str:
    """Fase do calendário para um carimbo de transação (decisão 6)."""
    return FASE_INTERTEMPORADA if int(ts_ms) < int(start_ms) else FASE_TEMPORADA


def delta_hours(add_ts_ms: int, drop_ts_ms: int) -> float:
    return round((int(add_ts_ms) - int(drop_ts_ms)) / MS_PER_HOUR, 1)


def latest_before(events: list, before_ts_ms: int = None) -> dict | None:
    """O evento mais RECENTE de uma lista normalizada [{'ts', 'tx_id', 'type'}, ...],
    opcionalmente restrito a `ts` estritamente anterior a `before_ts_ms`.
    Quem governa a régua é sempre o ÚLTIMO evento (lição da cadeia do Jones)."""
    pool = [e for e in (events or [])
            if before_ts_ms is None or int(e.get("ts") or 0) < int(before_ts_ms)]
    if not pool:
        return None
    return max(pool, key=lambda e: int(e.get("ts") or 0))


def suggest_commissioner_verdict(drop_ts_ms, freeze_ts_ms, in_frozen_list) -> str | None:
    """Veredito SUGERIDO para transação de comissário (âncora da decisão do owner,
    09/09/2026): drop posterior ao congelamento da lista de exclusão, em jogador
    presente nela → sugere "manobra" (vaivém de plataforma para montar o board); drop
    anterior ao congelamento → sugere "real". Sem âncora (lista nunca congelada ou
    limpa) → SEM sugestão — degrada, nunca bloqueia. É sugestão: quem decide é o admin."""
    if not freeze_ts_ms or not drop_ts_ms:
        return None
    if int(drop_ts_ms) >= int(freeze_ts_ms):
        return "manobra" if in_frozen_list else None
    return "real"


def decide_readd(*, add: dict | None, drop: dict | None, window_ms: int,
                 start_ms: int, drop_verdict: str | None = None,
                 commissioner_add_as_real: bool = False) -> dict:
    """A DECISÃO da régua para um re-add (jogador dropado que voltou a um roster).

    add / drop: transações normalizadas {'ts', 'tx_id', 'type'} (ts = `tx_timestamp`);
        `drop` é o último drop do PRÓPRIO jogador anterior ao add (`latest_before`).
    window_ms: `waiver_window_ms(settings.waiver_clear_days)`.
    start_ms: fronteira de fase (`season_start_ms`).
    drop_verdict: veredito ARBITRADO de um drop de comissário ('real'|'manobra'|None).
    commissioner_add_as_real: a arbitragem "real" de um add de comissário re-chama esta
        função pedindo a régua plena (o desvio de comissário já foi decidido pelo admin).

    Devolve {'acao': ...} com o contexto que o executor e a pendência precisam. Nenhum
    efeito colateral; nenhuma leitura de banco.
    """
    if not add:
        return {"acao": ACAO_INDETERMINADO,
                "motivo": "re-add sem transação de add na varredura da season — "
                          "contrato intocado, reportado"}

    add_ts = int(add.get("ts") or 0)
    canal = add.get("type") or ""
    fase_add = phase_of(add_ts, start_ms)

    if canal == "commissioner" and not commissioner_add_as_real:
        return {"acao": ACAO_PENDENCIA, "kind": KIND_COMISSARIO_ADD,
                "canal": canal, "fase": fase_add,
                "motivo": "add por transação de comissário — arbitragem humana "
                          "(real × manobra); o sync não altera contrato"}

    if not drop:
        # Decisão 7: varredura COMPLETA da season sem drop → o drop é anterior à season,
        # fora de qualquer janela ⇒ contrato MORTO por dedução.
        return {"acao": ACAO_CONTRATO_NOVO, "caso": 3,
                "canal": canal, "acq_type": ACQ_TYPE_BY_TX.get(canal, "free_agent"),
                "fase": fase_add,
                "motivo": "sem drop na varredura completa da season — drop anterior à "
                          "season, fora de qualquer janela (morto por dedução)"}

    drop_ts = int(drop.get("ts") or 0)
    if drop.get("type") == "commissioner":
        if drop_verdict == "manobra":
            return {"acao": ACAO_MANTER, "caso": 2, "canal": canal, "fase": fase_add,
                    "motivo": f"drop de comissário tx {drop.get('tx_id')} arbitrado "
                              f"MANOBRA — contrato intacto"}
        if drop_verdict != "real":
            return {"acao": ACAO_PENDENCIA, "kind": KIND_COMISSARIO_DROP,
                    "canal": canal, "fase": fase_add,
                    "motivo": "o último drop é transação de comissário não arbitrada — "
                              "a régua espera o veredito (real × manobra)"}
        # 'real': segue como drop normal, abaixo.

    fase_drop = phase_of(drop_ts, start_ms)
    if fase_drop == FASE_INTERTEMPORADA:
        # Caso 3 pela letra da régua: não há waiver na intertemporada — o drop mata por si.
        return {"acao": ACAO_CONTRATO_NOVO, "caso": 3,
                "canal": canal, "acq_type": ACQ_TYPE_BY_TX.get(canal, "free_agent"),
                "fase": fase_add, "fase_drop": fase_drop,
                "motivo": "drop de intertemporada — o drop mata o contrato por si só "
                          "(não há waiver na intertemporada)"}

    dh = delta_hours(add_ts, drop_ts)
    wh = window_ms / MS_PER_HOUR
    dentro = (add_ts - drop_ts) <= int(window_ms)
    sinal_delta = f"Δ {dh}h {'dentro' if dentro else 'fora'} da janela de {wh:.0f}h"
    sinal_canal = f"canal {canal}"

    if canal == "waiver" and dentro:
        return {"acao": ACAO_MANTER, "caso": 2, "canal": canal,
                "delta_h": dh, "fase": fase_add, "fase_drop": fase_drop,
                "motivo": f"contrato VIVO — {sinal_delta}; {sinal_canal} corrobora"}
    if canal != "waiver" and not dentro:
        return {"acao": ACAO_CONTRATO_NOVO, "caso": 3,
                "canal": canal, "acq_type": ACQ_TYPE_BY_TX.get(canal, "free_agent"),
                "delta_h": dh, "fase": fase_add, "fase_drop": fase_drop,
                "motivo": f"contrato MORTO — {sinal_delta}; {sinal_canal} corrobora"}

    # Decisão 5: combinação divergente entre Δ e canal → pendência com os DOIS sinais.
    return {"acao": ACAO_PENDENCIA, "kind": KIND_SINAL_DIVERGENTE,
            "canal": canal, "delta_h": dh,
            "fase": fase_add, "fase_drop": fase_drop,
            "sinais": [sinal_delta, sinal_canal],
            "motivo": f"sinais divergentes — {sinal_delta}, mas {sinal_canal}; "
                      f"arbitragem humana (vivo × morto)"}
