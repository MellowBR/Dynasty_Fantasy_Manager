"""
cli.py — os comandos da F2a (OFF26-24). Rodar da RAIZ do repo:

    python -m tools.phantom_board.cli validate --sheet sheet.json
    python -m tools.phantom_board.cli probe
    python -m tools.phantom_board.cli designate --sheet sheet.json \\
        --team-slot 2 --player "Nome Exato" [--price N]

`validate` é READ-ONLY (API pública + arquivo da sheet — zero browser, zero escrita).
`designate` é a prova da fatia: UMA designação ponta a ponta, comando via DOM e
assentamento via API. Relatório JSON em tools/phantom_board/runs/ nos dois modos.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .core import (ASSENTADO_LOCAL, BLOQUEADO_TETO, CONFLITO, JA_ASSENTADO,
                   campaign_summary, classify_team_keepers, conference_report,
                   draft_budget_slots, flatten_sheet, idempotency_decision,
                   league_guard, match_picks_to_sheet, max_bid,
                   resolve_slot_map, team_totals)
from .sleeper_api import (fetch_draft, fetch_draft_id, fetch_picks,
                          fetch_rosters, fetch_users)


def _write_report(kind: str, payload: dict) -> Path:
    runs = Path(__file__).parent / config.RUNS_DIR_NAME
    runs.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = runs / f"{kind}_{stamp}.json"
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"\nRelatório: {path}")
    return path


def _load_sheet(path: str) -> dict:
    """A sheet vem do endpoint `/api/admin/keeper_sheet_export` do Manager (o pacote
    do build_sheet, com sid + owner_id), salva pelo owner logado no navegador.
    ⛔ Nenhuma segunda definição de keeper — o arquivo É a fonte."""
    sheet = json.loads(Path(path).read_text(encoding="utf-8"))
    if not sheet.get("teams"):
        sys.exit(f"Sheet '{path}' sem times — salve a resposta de "
                 f"/api/admin/keeper_sheet_export (logado como admin).")
    return sheet


def _guarded_draft() -> tuple:
    """Deriva o draft da liga fantasma e roda a guarda de nascença. Aborta em
    mismatch — ANTES de qualquer outra coisa, em todos os modos."""
    draft_id = fetch_draft_id(config.LEAGUE_ID)
    draft = fetch_draft(draft_id) if draft_id else {}
    err = league_guard(draft, config.LEAGUE_ID)
    if err:
        sys.exit(f"⛔ {err}")
    return draft_id, draft


def cmd_validate(args):
    """Read-only: picks vivos × keeper sheet. F2a: os 18 do ensaio = $176 (MellowBR)."""
    draft_id, draft = _guarded_draft()
    picks = fetch_picks(draft_id)
    users = fetch_users(config.LEAGUE_ID)
    # FIX3: cadeia (a) draft_order → (b) slot_to_roster_id×rosters → (c) picks.
    # Em pre_draft recém-resetado o draft_order vem null — a (b) resolve por API.
    slot_map, slot_source = resolve_slot_map(draft, users,
                                             fetch_rosters(config.LEAGUE_ID), picks)
    print(f"Mapa slot↔owner: {len(slot_map)} slots via {slot_source}")
    sheet = _load_sheet(args.sheet)
    rows = flatten_sheet(sheet)
    report = match_picks_to_sheet(picks, rows, slot_map)

    print(f"Liga {config.LEAGUE_ID} · draft {draft_id} (derivado agora)")
    print(f"Sheet: {len(rows)} keepers · estágio "
          f"{(sheet.get('stage_meta') or {}).get('stage', '?')}")
    print(f"Picks vivos: {len(picks)}")
    print(f"  casados: {len(report['matched'])}")
    print(f"  salário divergente: {len(report['salary_divergent'])}")
    print(f"  owner divergente: {len(report['owner_divergent'])}")
    print(f"  no board fora da sheet: {len(report['picks_not_in_sheet'])}")
    print(f"  na sheet ainda sem pick: {len(report['sheet_missing'])}")
    for team in sorted({m["team_name"] for m in report["matched"]}):
        t = team_totals(report, team)
        print(f"  → {t['team_name']}: {t['count']} picks, ${t['total']}")
    for e in report["salary_divergent"] + report["owner_divergent"]:
        print(f"  ⚠️ divergência: {e}")
    _write_report("validate", {
        "mode": "validate", "league_id": config.LEAGUE_ID, "draft_id": draft_id,
        "sheet_stage": (sheet.get("stage_meta") or {}).get("stage"),
        "slot_map_source": slot_source,
        "picks": len(picks), "report": report,
    })


def cmd_probe(args):
    """Abre o board (guardas ativas) com o Inspector — o owner anota o seletor da
    célula e o coloca em config.BOARD_CELL_SELECTOR. Nenhum clique automatizado."""
    from .board import open_board, probe
    pw, ctx, page, draft_id = open_board(headless=False)
    print(f"Board da fantasma aberto (draft {draft_id}). Use o Inspector para anotar "
          f"a classe da CÉLULA; feche a janela ao terminar.")
    try:
        probe(page)
    finally:
        ctx.tracing.stop()
        ctx.close()
        pw.stop()


def cmd_designate(args):
    """A prova da F2a: UMA designação ponta a ponta, assentada na API."""
    from .board import BoardAbort, designate, open_board

    sheet = _load_sheet(args.sheet)
    rows = flatten_sheet(sheet)
    alvo = [r for r in rows if r["name"].lower() == args.player.lower()]
    if len(alvo) != 1:
        sys.exit(f"⛔ '{args.player}' precisa casar exatamente 1 keeper da sheet "
                 f"(casou {len(alvo)}). Nomes são o rótulo; a identidade é o sid.")
    alvo = alvo[0]
    price = args.price if args.price is not None else alvo["salary"]

    log = []
    slot_source = "manual(--team-slot)"
    ok = False          # FIX4: definido ANTES do try — o finally sempre o encontra
    try:
        pw, ctx, page, draft_id = open_board(headless=False)
    except Exception as e:
        # FIX9: falha ao abrir o board → mensagem limpa, nunca traceback cru
        sys.exit(f"⛔ ERRO ao abrir o board ({type(e).__name__}): {e}")
    try:
        # FIX3: o slot do time-alvo sai da CADEIA (a)→(b)→(c); a confirmação final
        # segue sendo o menu do DOM ("for Team {N}") dentro do designate.
        slot_map, chain_source = resolve_slot_map(
            fetch_draft(draft_id), fetch_users(config.LEAGUE_ID),
            fetch_rosters(config.LEAGUE_ID), fetch_picks(draft_id))
        slots = {v["user_id"]: k for k, v in slot_map.items()}
        team_slot = args.team_slot or slots.get(alvo["owner_id"])
        if not args.team_slot:
            slot_source = chain_source
        if not team_slot:
            raise BoardAbort(
                f"Owner {alvo['owner_id']} ({alvo['team_name']}) sem slot no draft — "
                f"fonte da cadeia: {chain_source}; mapa: {slot_map or '{}'}. Faltou: "
                f"draft_order (null em pre_draft), slot_to_roster_id×rosters e picks "
                f"não cobrem o owner-alvo. Último recurso: --team-slot N (o menu do "
                f"DOM confirma o N antes de designar).")
        log.append({"event": "slot_resolvido", "team_slot": int(team_slot),
                    "source": slot_source})
        verdict = designate(page, draft_id, int(team_slot), alvo["name"],
                            alvo["position"], "", price, alvo["sid"], log)
        print(f"\n✅ {alvo['name']} → Team {team_slot} (${price}): {verdict} "
              f"(confirmado na API, não no board)")
        ok = True
    except Exception as e:
        # FIX4: QUALQUER exceção (BoardAbort ou Playwright/timeout cru) produz o
        # abort padrão — screenshot + relatório — em vez de crash no handler
        # (o call log real: UnboundLocalError de 'ok' engoliu o abort limpo).
        shot = Path(__file__).parent / config.RUNS_DIR_NAME / "abort.png"
        shot.parent.mkdir(exist_ok=True)
        try:
            page.screenshot(path=str(shot))
        except Exception:
            shot = None
        rotulo = ("ABORTADO" if isinstance(e, BoardAbort)
                  else f"ERRO ({type(e).__name__})")
        log.append({"event": "abort", "tipo": type(e).__name__, "msg": str(e)[:300]})
        print(f"\n⛔ {rotulo}: {e}" + (f"\nScreenshot: {shot}" if shot else ""))
    finally:
        trace = Path(__file__).parent / config.RUNS_DIR_NAME / "trace.zip"
        try:
            ctx.tracing.stop(path=str(trace))
        except Exception:
            pass
        ctx.close()
        pw.stop()
        _write_report("designate", {
            "mode": "designate", "ok": ok, "player": args.player,
            "price": price, "slot_map_source": slot_source, "log": log,
        })
    sys.exit(0 if ok else 1)


def cmd_populate(args):
    """F2b — o loop por time (a unidade do runbook) e a campanha completa.

    Idempotência é a PRIMEIRA verificação (lição da F2a): cada keeper é conferido
    na API antes de qualquer clique. Falha num keeper → aborta O TIME (o que
    assentou permanece) e, em --all, segue para o próximo. `bloqueado_teto` é
    resultado esperado pré-late-drop, não erro. Retomável por construção: rodar
    de novo pula o que já assentou. O VEREDITO final é da auditoria OFF26-4.

    FIX9 (campanha de 12/08): NENHUMA exceção escapa como traceback cru — cru
    num keeper aborta O TIME (abort padrão: screenshot + evento no relatório) e
    segue; cru fora do loop aborta a CAMPANHA, ainda com relatório coerente."""
    import time as _time
    from .board import (BoardAbort, EmptySearchResult, board_shows_designated,
                        command_pick, open_board, settle_pendentes)

    if not args.all and not args.team_slot:
        sys.exit("⛔ informe --team-slot N ou --all")
    sheet = _load_sheet(args.sheet)
    rows = flatten_sheet(sheet)

    team_results = []
    slot_source = None
    fatal = None        # FIX9: definido ANTES do try — o finally/exit o encontram
    try:
        pw, ctx, page, draft_id = open_board(headless=False)
    except Exception as e:
        # FIX9: falha ao abrir o board → mensagem limpa, nunca traceback cru
        sys.exit(f"⛔ ERRO ao abrir o board ({type(e).__name__}): {e}")
    try:
        draft = fetch_draft(draft_id)
        # FIX10: budget e board saem do próprio draft (fallback $200/22) — insumo
        # da ANOTAÇÃO de max bid; a verdade operacional é o read-back do input.
        budget, total_slots = draft_budget_slots(draft)
        slot_map, slot_source = resolve_slot_map(
            draft, fetch_users(config.LEAGUE_ID),
            fetch_rosters(config.LEAGUE_ID), fetch_picks(draft_id))
        if not slot_map:
            raise BoardAbort("Mapa slot↔owner vazio — nenhuma fonte da cadeia "
                             "serviu; nada a popular.")
        print(f"Mapa slot↔owner: {len(slot_map)} slots via {slot_source}")
        slots = sorted(slot_map) if args.all else [int(args.team_slot)]

        for slot in slots:
            owner = slot_map[slot]["user_id"]
            handle = slot_map[slot]["handle"]
            team_rows = [r for r in rows if r["owner_id"] == owner]
            res = {"slot": slot, "handle": handle,
                   "team_name": team_rows[0]["team_name"] if team_rows else "?",
                   "designados": 0, "ja_assentados": 0, "bloqueados_teto": 0,
                   "conflitos": 0, "status": "ok", "eventos": []}
            team_results.append(res)   # FIX9: no relatório JÁ — falha não o apaga
            if not team_rows:
                res["status"] = "sem_keepers_na_sheet"
                print(f"[slot {slot} {handle}] sem keepers na sheet — pulando")
                continue
            print(f"[slot {slot} {handle}] {len(team_rows)} keepers na sheet")

            try:
                # FIX8 (tarefa 4): idempotência EM LOTE — 1 chamada antes do 1º
                # clique (pendência de run anterior já entra como ja_assentado).
                picks = fetch_picks(draft_id)
                lote = classify_team_keepers(team_rows, picks, slot_map)
                pendentes = []
                # FIX10: estado p/ a anotação de max bid (gasto corrente + picks
                # feitos no board de `total_slots`) e p/ excluir os pulados por
                # teto da conferência.
                gasto, picks_feitos, bloqueados = 0, 0, []
                for r in team_rows:
                    dec, det = lote.get(r["sid"], (None, None))
                    if dec == JA_ASSENTADO:
                        res["ja_assentados"] += 1
                        gasto += (det or {}).get("amount") or 0
                        picks_feitos += 1
                        continue
                    if dec == CONFLITO:
                        res["conflitos"] += 1
                        res["status"] = "conflito"
                        res["eventos"].append({"keeper": r["name"],
                                               "conflito": det})
                        print(f"  ⛔ CONFLITO em {r['name']}: {det} — "
                              f"abortando o time")
                        break
                    # FIX8: comando ASSÍNCRONO — registra pendente e SEGUE (o
                    # board local preenchendo a célula é o feedback; a API pode
                    # atrasar 5min)
                    try:
                        verdict = command_pick(page, slot, r["name"],
                                               r["position"], "", r["salary"],
                                               r["sid"], res["eventos"],
                                               expected_max=max_bid(
                                                   budget, gasto, picks_feitos,
                                                   total_slots))
                    except EmptySearchResult:
                        # tarefa 5: comandado NESTA run? sinal de sucesso local.
                        if any(pd["sid"] == r["sid"] for pd in pendentes):
                            res["eventos"].append(
                                {"sid": r["sid"],
                                 "event": "sumiu_da_busca_pos_comando"})
                            continue
                        now = {str(x.get("player_id"))
                               for x in fetch_picks(draft_id)}
                        if r["sid"] in now:
                            res["ja_assentados"] += 1
                            gasto += r["salary"]
                            picks_feitos += 1
                            continue
                        if board_shows_designated(page, slot, r["name"]):
                            res["eventos"].append({"sid": r["sid"],
                                                   "event": ASSENTADO_LOCAL})
                            res["designados"] += 1
                            gasto += r["salary"]
                            picks_feitos += 1
                            continue
                        res["status"] = "falha"
                        res["eventos"].append({"keeper": r["name"],
                                               "falha": "busca vazia sem rastro "
                                                        "na API nem no board "
                                                        "local"})
                        print(f"  ⛔ FALHA em {r['name']} (busca vazia sem "
                              f"rastro) — abortando o time (o que assentou "
                              f"permanece)")
                        break
                    except BoardAbort as e:
                        res["status"] = "falha"
                        res["eventos"].append({"keeper": r["name"],
                                               "falha": str(e)[:300]})
                        print(f"  ⛔ FALHA em {r['name']}: {e} — abortando o "
                              f"time (o que assentou permanece)")
                        try:
                            page.screenshot(path=str(
                                Path(__file__).parent / config.RUNS_DIR_NAME /
                                f"abort_slot{slot}.png"))
                        except Exception:
                            pass
                        break
                    if verdict == BLOQUEADO_TETO:
                        # FIX10: o teto (clamp OU recusa síncrona) pula O KEEPER
                        # — nada foi gravado, o resto do time é alcançável ($1
                        # sempre cabe na reserva). Resultado, não falha.
                        res["bloqueados_teto"] += 1
                        bloqueados.append(r["sid"])
                        res["eventos"].append({"keeper": r["name"],
                                               "resultado": BLOQUEADO_TETO})
                        print(f"  🧱 teto em {r['name']} — pulando o keeper "
                              f"(esperado pré-late-drop; nada gravado); o "
                              f"time segue")
                        continue
                    pendentes.append({"sid": r["sid"], "name": r["name"],
                                      "slot": slot, "price": r["salary"],
                                      "position": r["position"],
                                      "cmd_at": _time.monotonic()})
                    gasto += r["salary"]
                    picks_feitos += 1
                    print(f"  📤 {r['name']} (${r['salary']}) comandado — "
                          f"pendente de confirmação")

                # FIX8 (tarefas 2/3/7): reconciliação paciente do TIME inteiro —
                # teto generoso, reload no meio (hipótese do cache por visita),
                # decisão pós-teto por pendente. Telemetria no relatório.
                if pendentes:
                    print(f"  ⏳ reconciliando {len(pendentes)} pendentes "
                          f"(teto {config.RECONCILE_TETO_SECONDS}s)...")
                    placar = settle_pendentes(page, draft_id, pendentes,
                                              res["eventos"])
                    res["designados"] += placar["assentados"] + placar["locais"]
                    if placar["locais"]:
                        print(f"  ⚠️ {placar['locais']} assentado(s) SÓ no board "
                              f"local (API atrasada) — conferir na auditoria")
                    if placar["falhas"]:
                        res["status"] = "falha_parcial"
                        res["eventos"].append(
                            {"falhas_de_keeper": placar["falhas"]})
                        print(f"  ⛔ {len(placar['falhas'])} keeper(s) falharam "
                              f"— o resto do time permanece")

                if res["status"] == "ok":
                    # FIX10: a conferência APONTA os picks — divergente vira
                    # nome + esperado + gravado (no relatório E no stdout); os
                    # pulados por teto saem da expectativa (campo próprio).
                    res["conferencia"] = conference_report(
                        fetch_picks(draft_id), team_rows, excluidos=bloqueados)
                    c = res["conferencia"]
                    for d in c["divergentes"]:
                        print(f"  ⚠️ preço divergente: {d['name']} — sheet "
                              f"${d['sheet']} × board ${d['board']}")
                    for m in c["faltantes"]:
                        print(f"  ⚠️ esperado e AUSENTE do board: {m['name']}")
                    if (c["picks_no_board"] != c["keepers_na_sheet"]
                            or c["total_no_board"] != c["total_na_sheet"]
                            or c["divergentes"]):
                        res["status"] = "divergencia_na_conferencia"
                    elif res["bloqueados_teto"]:
                        res["status"] = BLOQUEADO_TETO
                    print(f"  conferência: {c['picks_no_board']}/"
                          f"{c['keepers_na_sheet']} picks, "
                          f"${c['total_no_board']}/${c['total_na_sheet']}"
                          + (f" (+{res['bloqueados_teto']} bloqueado(s) por "
                             f"teto, fora da conta)"
                             if res["bloqueados_teto"] else ""))
            except Exception as e:
                # FIX9 — abort padrão do TIME para exceção CRUA (Timeout etc.):
                # screenshot + evento no relatório, status falha, e a campanha
                # segue ao próximo time (o crash real de 12/08 escapou daqui
                # como traceback, sem screenshot e sem registro).
                res["status"] = "falha"
                res["eventos"].append(
                    {"falha_do_time":
                     f"ERRO ({type(e).__name__}): {str(e)[:300]}"})
                print(f"  ⛔ ERRO CRU ({type(e).__name__}) no slot {slot}: {e} "
                      f"— abortando o time (o que assentou permanece)")
                try:
                    page.screenshot(path=str(
                        Path(__file__).parent / config.RUNS_DIR_NAME /
                        f"abort_slot{slot}.png"))
                except Exception:
                    pass
    except Exception as e:
        # FIX9 — NADA escapa como traceback cru: abort padrão da CAMPANHA
        # (screenshot + registro no relatório) e o processo encerra com o
        # relatório coerente no finally.
        fatal = f"{type(e).__name__}: {str(e)[:300]}"
        print(f"\n⛔ CAMPANHA ABORTADA ({type(e).__name__}): {e}")
        try:
            page.screenshot(path=str(Path(__file__).parent /
                                     config.RUNS_DIR_NAME /
                                     "abort_campanha.png"))
        except Exception:
            pass
    finally:
        try:
            ctx.tracing.stop(path=str(Path(__file__).parent /
                                      config.RUNS_DIR_NAME / "trace.zip"))
        except Exception:
            pass
        ctx.close()
        pw.stop()
        resumo = campaign_summary(team_results)
        print("=== CAMPANHA ===")
        for k, v in resumo.items():
            print(f"  {k}: {v}")
        print("⚖️ O VEREDITO é da auditoria OFF26-4 — abra /admin/keeper_audit "
              "no Manager e confira o board populado contra a sheet (o juiz "
              "independente; a contagem acima não substitui).")
        payload = {
            "mode": "populate", "all": bool(args.all),
            "slot_map_source": slot_source,
            "resumo": resumo, "times": team_results,
            "proximo_passo": "auditoria OFF26-4 em /admin/keeper_audit",
        }
        if fatal:
            payload["abort_campanha"] = fatal
        _write_report("populate", payload)
    ruim = [t for t in team_results
            if t["status"] not in ("ok", BLOQUEADO_TETO, "sem_keepers_na_sheet")]
    # (falha, falha_parcial, conflito e divergencia_na_conferencia caem aqui)
    sys.exit(1 if (ruim or fatal) else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="phantom_board",
                                 description="OFF26-24 — população do board da fantasma")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="read-only: picks vivos × keeper sheet")
    v.add_argument("--sheet", required=True)
    v.set_defaults(fn=cmd_validate)
    p = sub.add_parser("probe", help="abre o board + Inspector p/ anotar seletor")
    p.set_defaults(fn=cmd_probe)
    d = sub.add_parser("designate", help="UMA designação ponta a ponta (F2a)")
    d.add_argument("--sheet", required=True)
    d.add_argument("--player", required=True)
    d.add_argument("--team-slot", type=int, default=None,
                   help="opcional — sem ele, deriva do owner do keeper na sheet")
    d.add_argument("--price", type=int, default=None,
                   help="opcional — default é o salário da sheet")
    d.set_defaults(fn=cmd_designate)
    pop = sub.add_parser("populate", help="F2b: loop por time / campanha --all")
    pop.add_argument("--sheet", required=True)
    pop.add_argument("--team-slot", type=int, default=None)
    pop.add_argument("--all", action="store_true")
    pop.set_defaults(fn=cmd_populate)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
