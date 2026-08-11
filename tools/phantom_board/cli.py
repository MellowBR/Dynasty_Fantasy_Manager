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
from .core import (flatten_sheet, league_guard, match_picks_to_sheet,
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
    pw, ctx, page, draft_id = open_board(headless=False)
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
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
