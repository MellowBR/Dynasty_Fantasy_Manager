"""
ensaio_janela_selada.py — OFF26-1-ENSAIO: operação do ensaio da janela selada.

O ensaio (pré-condição 1 da spec da urna, OFF26-10) roda o ciclo completo da janela de
cortes — abrir, declarar, lock, hash, reveal, keeper sheet — com declarações fictícias,
em localhost e depois em produção. Este script cobre o que a UI NÃO tem:

  * `--status`   → relatório read-only do estado da janela (flag, declarações, snapshots,
                   banner) — é a "consulta de conferência" do roteiro, antes e depois.
  * `--banner on|off` → liga/desliga o RÓTULO DE ENSAIO nas telas /cuts e /cuts/keeper_sheet
                   (AppConfig `cuts_ensaio_banner`) — mitigação do risco "owner declara
                   achando que vale".
  * `--reset --backup <path>` → DESFAZ um ciclo de ensaio por completo: apaga as declarações
                   (CutDeclaration) e os snapshots (CutWindowAudit) da season, fecha a janela
                   e desliga o banner. **Cobre também a URNA** (OFF26-10): apaga os bilhetes
                   (LateDropDeclaration), os snapshots (LateDropAudit) e zera a AGENDA — sem
                   isso, um horário de teste reabriria a urna sozinho em produção. **Sem backup conferido, nenhuma escrita** (molde do
                   runner do OFF26-20-FIX).

⚠️ POR QUE O RESET PRECISA APAGAR A TRILHA DO ENSAIO (comportamento declarado): o estado
"travada" da janela É a existência de um snapshot canônico (`CutWindowAudit.is_canonical`)
— não há flag separada. Um snapshot de ensaio deixado no banco manteria a janela travada e
**bloquearia a abertura da janela real de 20/08** (o /open recusa com 409). Logo o reset
devolve o banco ao estado pré-ensaio por inteiro; a evidência do ensaio fica no BACKUP
(feito antes, obrigatório) e no relatório da sessão — não na trilha viva.

O ensaio NÃO toca o Sleeper em nada: declarações, lock, hash e reveal são internos ao
Manager. As únicas tabelas em risco são as duas acima + 2 chaves de AppConfig.
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

BANNER_KEY = "cuts_ensaio_banner"
WINDOW_KEY = "cuts_window_open"

# OFF26-10 (MAN-OFF26-10, 07/08): o mesmo runner opera o ensaio da URNA. O banner e o
# MESMO (fonte unica do rotulo de teste, exibido tambem em /late_drop); o estado da urna
# tem chaves PROPRIAS -- a `cuts_window_open` nao e, e nao pode ser, o gate da urna.
URN_OPENS_KEY = "late_drop_opens_at"
URN_CLOSES_KEY = "late_drop_closes_at"
URN_BLOCK_R1_KEY = "late_drop_block_r1_rookie"


def _db_path(cli_db: str = None) -> Path:
    """Resolve o banco para caminho ABSOLUTO (relativo ao cwd de quem invocou).

    POSENSAIO (bug vivido na Etapa 1): com caminho relativo, o exists() do main
    passava (cwd) mas o SQLAlchemy resolvia a URI contra OUTRO diretório — e o
    SQLite criava lá um banco VAZIO em silêncio, mascarando a causa como
    "no such table". Resolver antes de qualquer conexão elimina a bifurcação."""
    return Path(cli_db or os.environ.get("DYNASTY_DB")
                or (BASE_DIR / "dynasty.db")).expanduser().resolve()


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco, sem o boot do app.py (sem import/sync)."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


# ── Núcleo (importável pelos testes; roda dentro de app context) ──────────────

def _has_table(name: str) -> bool:
    """Existe a tabela? Consulta pela MESMA sessão/transação.

    ⛔ Não usar `models._table_exists` aqui: ele inspeciona pelo ENGINE, abrindo outra
    conexão — e com pool compartilhado o close() dela **desfaz a transação em curso**,
    fazendo o `stage_reset` perder os deletes ainda não comitados (bug vivido e coberto
    por `janela_ensaio_test.TestResetDoEnsaio`)."""
    from sqlalchemy import text
    from models import db
    row = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": name}).first()
    return row is not None


def window_report(season: int) -> dict:
    """Relatório read-only do estado da janela na season. Não expõe conteúdo de
    declaração (nem IDs nem nomes de jogador) — só existência e contagens (D6)."""
    from models import CutDeclaration, CutWindowAudit, get_config  # noqa: F401
    decls = CutDeclaration.query.filter_by(season=season).all()
    audits = (CutWindowAudit.query.filter_by(season=season)
              .order_by(CutWindowAudit.id).all())
    canonical = [a for a in audits if a.is_canonical]
    state = ("locked" if canonical
             else "open" if get_config(WINDOW_KEY, "false") == "true"
             else "closed")
    return {
        "season": season,
        "state": state,
        "window_flag": get_config(WINDOW_KEY, "false"),
        "banner_flag": get_config(BANNER_KEY, "false"),
        "declarations": [{
            "team_id": d.team_id,
            "team": d.team.name if d.team else f"#{d.team_id}",
            "declared": d.declared,
            "num_cuts": len(d.cut_ids()),
        } for d in decls],
        "audits": [{
            "id": a.id,
            "is_canonical": a.is_canonical,
            "executed_at": str(a.executed_at),
            "result_hash": a.result_hash,
            "reason": a.reason,
        } for a in audits],
        "urn": urn_report(season),
    }


def urn_report(season: int) -> dict:
    """Estado da URNA (OFF26-10). Sigilo MAIS estrito que o da janela: nem conteudo nem
    existencia POR TIME saem daqui — so o agregado, para o operador conferir que o reset
    limpou tudo (na urna, ate a contagem por time seria vazamento; ver U1)."""
    from models import LateDropDeclaration, LateDropAudit, get_config
    # Banco anterior a urna (ex.: backup de antes do deploy, ou 1o boot ainda nao
    # rodado): o runner e a ferramenta de seguranca do operador — degrada, nao quebra.
    if not _has_table("late_drop_declarations"):
        return {"state": "sem_tabela", "opens_at": "", "closes_at": "",
                "block_r1_rookie": get_config(URN_BLOCK_R1_KEY, "false"),
                "num_declarations": 0, "audits": []}
    decls = LateDropDeclaration.query.filter_by(season=season).all()
    audits = (LateDropAudit.query.filter_by(season=season)
              .order_by(LateDropAudit.id).all())
    canonical = [a for a in audits if a.is_canonical]
    opens, closes = get_config(URN_OPENS_KEY, ""), get_config(URN_CLOSES_KEY, "")
    return {
        "state": "locked" if canonical else ("agendada" if opens else "sem_agenda"),
        "opens_at": opens,
        "closes_at": closes,
        "block_r1_rookie": get_config(URN_BLOCK_R1_KEY, "false"),
        "num_declarations": len(decls),
        "audits": [{
            "id": a.id,
            "is_canonical": a.is_canonical,
            "executed_at": str(a.executed_at),
            "result_hash": a.result_hash,
            "reason": a.reason,
        } for a in audits],
    }


def stage_reset(season: int) -> dict:
    """Encena o desfazer do ensaio na sessão ativa — SEM commit (o chamador comita,
    ou dá rollback e nada acontece). Apaga CutDeclaration + CutWindowAudit da season
    (e SÓ dela), fecha a janela e desliga o banner."""
    from models import (db, CutDeclaration, CutWindowAudit, LateDropDeclaration,
                        LateDropAudit, AppConfig)
    n_decls = CutDeclaration.query.filter_by(season=season).delete()
    n_audits = CutWindowAudit.query.filter_by(season=season).delete()
    # URNA (OFF26-10): mesma logica e mesmo motivo — snapshot canonico de ensaio deixado
    # no banco travaria a urna real de 22/08, e uma agenda de teste a abriria sozinha.
    if _has_table("late_drop_declarations"):
        n_urn_decls = LateDropDeclaration.query.filter_by(season=season).delete()
        n_urn_audits = LateDropAudit.query.filter_by(season=season).delete()
    else:
        n_urn_decls = n_urn_audits = 0
    for key, value in ((WINDOW_KEY, "false"), (BANNER_KEY, "false"),
                       (URN_OPENS_KEY, ""), (URN_CLOSES_KEY, ""),
                       (URN_BLOCK_R1_KEY, "false")):
        row = db.session.get(AppConfig, key)
        if row:
            row.value = value
        else:
            db.session.add(AppConfig(key=key, value=value))
    return {"deleted_declarations": n_decls, "deleted_audits": n_audits,
            "deleted_urn_declarations": n_urn_decls,
            "deleted_urn_audits": n_urn_audits}


# ── Comandos ──────────────────────────────────────────────────────────────────

def _print_report(r: dict) -> None:
    print(f"season {r['season']} · janela: {r['state']} "
          f"(flag={r['window_flag']}) · banner de ensaio: {r['banner_flag']}")
    print(f"declarações: {len(r['declarations'])}")
    for d in r["declarations"]:
        print(f"  team {d['team_id']:>2} {d['team']:<28} declared={d['declared']} "
              f"num_cuts={d['num_cuts']}")
    print(f"snapshots (CutWindowAudit): {len(r['audits'])}")
    for a in r["audits"]:
        star = "CANÔNICO" if a["is_canonical"] else "superseded"
        print(f"  #{a['id']} {star} {a['executed_at']} hash={a['result_hash'][:16]}… "
              f"reason={a['reason']!r}")
    u = r.get("urn") or {}
    print(f"URNA (late drop): {u.get('state')} · abre={u.get('opens_at') or '—'} "
          f"· fecha={u.get('closes_at') or '—'} · bloqueio rookie 1ª="
          f"{u.get('block_r1_rookie')}")
    print(f"  bilhetes depositados: {u.get('num_declarations', 0)} (conteúdo selado)")
    for a in u.get("audits", []):
        star = "CANÔNICO" if a["is_canonical"] else "superseded"
        print(f"  #{a['id']} {star} {a['executed_at']} hash={a['result_hash'][:16]}… "
              f"reason={a['reason']!r}")


def cmd_status(db_path: Path) -> int:
    from models import get_current_season
    app = _make_app(db_path)
    with app.app_context():
        season = get_current_season()
        print(f"Banco: {db_path}")
        _print_report(window_report(season))
    return 0


def cmd_banner(db_path: Path, mode: str) -> int:
    from models import db, set_config, get_current_season
    app = _make_app(db_path)
    with app.app_context():
        set_config(BANNER_KEY, "true" if mode == "on" else "false")
        db.session.commit()
        season = get_current_season()
        print(f"Banner de ensaio: {mode.upper()} (banco {db_path})")
        _print_report(window_report(season))
    return 0


def _verify_backup(backup: Path, db_path: Path) -> bool:
    if not backup.exists():
        print(f"⛔ Backup não encontrado: {backup}")
        return False
    b, d = backup.stat().st_size, db_path.stat().st_size
    if b < 0.5 * d:
        print(f"⛔ Backup implausível: {b} bytes contra {d} do banco alvo")
        return False
    print(f"Backup conferido: {backup} ({b} bytes; banco alvo {d} bytes)")
    return True


def cmd_reset(db_path: Path, backup: Path) -> int:
    """Backup gate → relatório do que vai sumir → stage + commit → verificação."""
    from models import db, get_current_season

    if not _verify_backup(backup, db_path):
        return 1

    app = _make_app(db_path)
    with app.app_context():
        season = get_current_season()
        before = window_report(season)
        print("\n── Estado ANTES do reset ──")
        _print_report(before)

        staged = stage_reset(season)
        db.session.commit()
        print(f"\nApagado: {staged['deleted_declarations']} declaração(ões), "
              f"{staged['deleted_audits']} snapshot(s).")

        after = window_report(season)
        print("\n── Estado DEPOIS do reset ──")
        _print_report(after)

    # Verificação por conexão independente (raw sqlite)
    con = sqlite3.connect(str(db_path))
    n_d = con.execute("SELECT COUNT(*) FROM cut_declarations WHERE season=?",
                      (season,)).fetchone()[0]
    n_a = con.execute("SELECT COUNT(*) FROM cut_window_audit WHERE season=?",
                      (season,)).fetchone()[0]
    flags = dict(con.execute(
        "SELECT key, value FROM app_config WHERE key IN (?, ?, ?, ?)",
        (WINDOW_KEY, BANNER_KEY, URN_OPENS_KEY, URN_CLOSES_KEY)))

    def _count(table):
        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)).fetchone()
        if not row:          # banco anterior a urna — nada a verificar
            return 0
        return con.execute(f"SELECT COUNT(*) FROM {table} WHERE season=?",
                           (season,)).fetchone()[0]

    n_ud, n_ua = _count("late_drop_declarations"), _count("late_drop_audit")
    con.close()

    errors = []
    if n_d != 0:
        errors.append(f"{n_d} declaração(ões) restante(s)")
    if n_a != 0:
        errors.append(f"{n_a} snapshot(s) restante(s)")
    if flags.get(WINDOW_KEY) not in (None, "false"):
        errors.append(f"janela ainda aberta ({WINDOW_KEY}={flags.get(WINDOW_KEY)!r})")
    if flags.get(BANNER_KEY) not in (None, "false"):
        errors.append(f"banner ainda ligado ({BANNER_KEY}={flags.get(BANNER_KEY)!r})")
    if n_ud != 0:
        errors.append(f"{n_ud} bilhete(s) de urna restante(s)")
    if n_ua != 0:
        errors.append(f"{n_ua} snapshot(s) de urna restante(s)")
    if flags.get(URN_OPENS_KEY) or flags.get(URN_CLOSES_KEY):
        errors.append("urna ainda agendada (late_drop_opens_at/closes_at)")
    if errors:
        print("⛔ FALHA NA VERIFICAÇÃO DO RESET: " + "; ".join(errors))
        return 1
    print("\n✅ RESET OK — 0 declarações, 0 snapshots, 0 bilhetes de urna, janela "
          "fechada, urna sem agenda, banner desligado. Janela e urna podem ser abertas "
          "de novo (estado pré-ensaio).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="OFF26-1-ENSAIO: status / banner / reset da janela selada")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--status", action="store_true", help="relatório read-only")
    mode.add_argument("--banner", choices=["on", "off"],
                      help="liga/desliga o rótulo de ENSAIO nas telas")
    mode.add_argument("--reset", action="store_true",
                      help="desfaz o ciclo de ensaio (exige --backup conferível)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatório no --reset)")
    ap.add_argument("--db", help="override do banco (ensaio local); padrão: env DYNASTY_DB")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        # Criar banco novo NUNCA é intenção de quem passa --db — recusar com a causa clara.
        print(f"⛔ Banco não encontrado: {db_path}")
        print("   (caminho relativo é resolvido contra o diretório ATUAL; confira o cwd ou use absoluto)")
        return 1
    if args.reset and not args.backup:
        print("⛔ --reset exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1

    if args.status:
        return cmd_status(db_path)
    if args.banner:
        return cmd_banner(db_path, args.banner)
    return cmd_reset(db_path, Path(args.backup).expanduser().resolve())


if __name__ == "__main__":
    sys.exit(main())
