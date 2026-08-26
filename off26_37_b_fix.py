"""
off26_37_b_fix.py — runner ONE-SHOT da correção do GRUPO B do OFF26-37
(`contract_year` 3→2 nos 11 cujo contrato NASCEU NOVO em 2025).

Aprovação do owner em 26/08/2026, sobre a arbitragem MAN-CONTRATO-VIVO-ARB (commit `4da7133`) e o
parecer MAN-CONTRATO-VIVO-F1 (commit `3669dce`). Estado dos 11 medido pelo owner em produção
(`/data/dynasty.db`, `current_season=2026`, `rollover_done=true`) em 26/08/2026.

O QUE CORRIGE. Pelo **caso 3 da régua canônica** (adquirido SEM contrato vivo ⇒ contrato novo,
ano 1), o contrato destes 11 nasceu em **2025**; logo **2026 é ano 2**. O banco os conta a partir
do contrato anterior e o rollover de 17/08 incrementou o número errado: hoje marcam **ano 3**.

⛔ **NENHUM DINHEIRO SE MOVE.** `contract_year` 3 e 2 caem **ambos** no ramo da valorização
(`next_yr` não é 2 e não passa de 4) ⇒ a projeção do ano seguinte é idêntica **para qualquer
ESPN** — é a forma da regra, não o dado (parecer F1, eixo 2: 0 violações em 11/11). O passivo de
salário do **Stafford** (`$2 → $3`, ano 2 de waiver/FA) é **outra raiz** e **não entra aqui**
(decisão 4 do owner): este runner **não toca salário de ninguém**.

DUAS DECISÕES DE FORMA, e por quê:

  1. ⛔ **A LISTA É CONGELADA — derivá-la por query é DEFEITO, não otimização.** A F1 mediu que
     **60** jogadores compartilham o perfil (`css=2025` · canal waiver/FA · vivo), dos quais
     **48 seriam falso positivo — o Goff (3163) entre eles**. Nenhum critério de estado no banco
     separa alvo de não-alvo: o discriminante é a **cadeia da API de transações**, que o banco não
     carrega. O congelado aqui é a **lista**; o que se deriva no dia é a **elegibilidade**.

  2. ⭐ **DOIS LOTES, um por canal** (decisão 2 do owner). A guarda é **forte** e inclui
     `acquisition_type`; o grupo é de canal **misto** (6 `fa_waiver` + 5 `free_agent`), e uma
     guarda única com canal misto pularia metade do grupo por "divergência" que não é divergência.
     Cada lote roda com a sua própria `EXPECTED` contra a **mesma** porta canônica.

⛔ **A LISTA DE ELEGÍVEIS É DERIVADA AO VIVO NO DIA.** A intertemporada está aberta e os cortes
acontecem **direto no Sleeper** (OFF26-1 ETAPA2): o `is_dropped` do banco é só a fotografia do
último sync e pode estar atrasado de propósito. Corrigir contrato de quem acabou de ser cortado é
escrever em **contrato morto**. Sem API, não há escrita — a correção não tem prazo (o efeito é na
renovação).

⛔ **Escopo:** GRUPO B apenas. O Grupo A (6803 Aiyuk, 9486 Wicks) é **reset de quatro campos** por
`record_acquisition`, com perfil de risco próprio — runner separado, decisão 1 do owner. Os dois
sids do Grupo A são **casos negativos explícitos** na suíte deste arquivo.

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    # 0) BACKUP OBRIGATÓRIO (sem ele o --apply recusa escrever):
    sqlite3 /data/dynasty.db ".backup '/data/pre_off26_37_b_fix.db'"

    # 1) Conferência read-only (guarda + lotes + cruzamento ao vivo + invariante):
    python off26_37_b_fix.py --check

    # 2) Escrita (guarda → escrita+trilha → verificação → commit):
    python off26_37_b_fix.py --apply --backup /data/pre_off26_37_b_fix.db

    # Ensaio local: acrescentar --db <caminho de uma CÓPIA pós-rollover>
    # Inspeção sem rede (só no --check): --offline
"""

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace

BASE_DIR = Path(__file__).resolve().parent
LEAGUE_ID = "1316547584378048512"

# ── Lista CONGELADA dos 11 (arbitragem 4da7133 + estado medido em prod em 26/08/2026) ─────────
# (sid, nome, sleeper_owner_id do time no dia da medição). ⛔ sid é SEMPRE string: as DEFs usam
# sigla ('CHI'/'CLE'/'NE') — a armadilha conhecida da coerção a inteiro.
# O owner_id é REGISTRO da medição (identidade estável de time, nunca o nome); a guarda não o usa,
# porque trade legítima entre a medição e a execução não invalida a correção de contagem.
COHORT_FA_WAIVER = [
    ("3451",  "Ka'imi Fairbairn",      "695859519976210432"),
    ("5870",  "Daniel Jones",          "1130162144764506112"),
    ("8259",  "Cameron Dicker",        "867557566065045504"),
    ("CHI",   "Chicago Bears",         "1129822349391470592"),
    ("CLE",   "Cleveland Browns",      "695859519976210432"),
    ("NE",    "New England Patriots",  "1133818177651224576"),
]

COHORT_FREE_AGENT = [
    ("421",   "Matthew Stafford",      "867557566065045504"),
    ("8154",  "Brian Robinson",        "1133812910268010496"),
    ("9225",  "Tank Bigsby",           "205848303030505472"),
    ("10213", "Tre Tucker",            "698015187109773312"),
    ("11539", "Jake Bates",            "698015187109773312"),
]

# Guarda pré-escrita, por lote: o estado esperado PÓS-rollover de 17/08. A única diferença entre
# os dois é `acquisition_type` — é por isso que existem dois lotes.
_GUARD_BASE = {
    "contract_year": 3,
    "contract_start_season": 2025,
    "needs_review": False,
    "is_dropped": False,
}

LOTS = [
    {"canal": "fa_waiver",  "cohort": COHORT_FA_WAIVER,
     "expected": {**_GUARD_BASE, "acquisition_type": "fa_waiver"}},
    {"canal": "free_agent", "cohort": COHORT_FREE_AGENT,
     "expected": {**_GUARD_BASE, "acquisition_type": "free_agent"}},
]

NEW_YEAR = 2
EVENT_REF = "fix:off26-37-b"
REASON = ("Correção OFF26-37 Grupo B aprovada pelo owner em 26/08/2026 (caso 3 da régua canônica: "
          "adquirido sem contrato vivo abre contrato novo; ano 1 = 2025, logo 2026 é ano 2)")

# ⛔ Casos negativos que a suíte fiscaliza: nenhum deles pode ser alcançado pelo plano.
#    3163 = Goff (cy=3 CORRETO, contrato de 2024 preservado — claim 12,3h após o drop);
#    6803/9486 = Grupo A (reset de quatro campos, runner separado).
FORBIDDEN = {
    "3163": "Jared Goff — NAO e alvo: contrato de 2024 preservado (claim 12,3h, dentro da janela)",
    "6803": "Brandon Aiyuk — GRUPO A: reset de quatro campos por record_acquisition",
    "9486": "Dontayvion Wicks — GRUPO A: reset de quatro campos por record_acquisition",
}


# ── Núcleo puro ───────────────────────────────────────────────────────────────

def all_targets() -> list:
    """A lista congelada inteira, na ordem dos lotes — [(sid, nome, owner_id), ...]."""
    return [t for lot in LOTS for t in lot["cohort"]]


def cohort_sids() -> list:
    return [sid for sid, _n, _o in all_targets()]


def derive_eligible_by_roster(cohort: list, rostered_sids) -> tuple:
    """Cruza a lista congelada com os rosters vivos — puro, sem rede e sem DB.

    Devolve (targets, out): quem segue rosterado entra; quem não está foi cortado no Sleeper e
    fica de fora COM MOTIVO (o banco pode ainda não ter sincronizado — o Sleeper é a autoridade
    sobre membership).
    """
    rostered = {str(s) for s in rostered_sids}
    targets, out = [], []
    for sid, name, owner in cohort:
        if sid in rostered:
            targets.append((sid, name, owner))
        else:
            out.append({"sleeper_player_id": sid, "name": name,
                        "reason": "nao esta em nenhum roster ao vivo (cortado no Sleeper) - "
                                  "contrato morto, correcao de contagem nao se aplica"})
    return targets, out


def invariant_diff(before: dict, after: dict) -> list:
    """Compara salário e projeção do ano seguinte antes/depois — puro.

    before/after: sid → {"salary", "projected"}. Lista vazia = o invariante se sustenta
    (a correção mexe na CONTAGEM, nunca no dinheiro).
    """
    viol = []
    for sid, pre in before.items():
        post = after.get(sid)
        if post is None:
            viol.append(f"{sid}: ausente na releitura pós-escrita")
            continue
        if int(pre["salary"]) != int(post["salary"]):
            viol.append(f"{sid}: salário {pre['salary']} -> {post['salary']}")
        if int(pre["projected"]) != int(post["projected"]):
            viol.append(f"{sid}: projeção {pre['projected']} -> {post['projected']}")
    return viol


# ── Camada de IO ──────────────────────────────────────────────────────────────

def fetch_rostered_sids(league_id: str = LEAGUE_ID, timeout: int = 30) -> set:
    """GET read-only dos rosters da liga — devolve o conjunto de sleeper_player_ids rosterados.

    Inclui `reserve` (IR): jogador no IR segue sob contrato. Só leitura; nada é enviado.
    """
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        rosters = json.load(resp)
    sids = set()
    for ro in rosters:
        for key in ("players", "reserve", "taxi"):
            for pid in (ro.get(key) or []):
                sids.add(str(pid))
    return sids


def _db_path(cli_db: str = None) -> Path:
    """Caminho do banco, SEMPRE absoluto.

    ⛔ O `.resolve()` não é cosmético: com caminho RELATIVO o Flask-SQLAlchemy reescreve
    `sqlite:///dynasty.db` para dentro do `instance/` da app e **cria um banco vazio lá**,
    de modo que o runner leria uma base sem tabela em vez do banco pedido (medido nesta
    sessão com `--db dynasty.db`). Em produção o caminho vem absoluto por `DYNASTY_DB`, o que
    mantinha a armadilha latente no molde anterior."""
    return Path(cli_db or os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db")).resolve()


def _make_app(db_path: Path):
    """App Flask mínimo — só o bind do banco. NÃO roda o boot do app.py (sem import CSV,
    sem sync, sem seed): correção cirúrgica não dispara efeito colateral."""
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _snapshot_players(db_path: Path) -> dict:
    """Fotografa a tabela players inteira (todas as colunas) para o diff pós-escrita."""
    con = sqlite3.connect(str(db_path))
    cols = [r[1] for r in con.execute("PRAGMA table_info(players)")]
    rows = {r[0]: dict(zip(cols, r)) for r in
            con.execute(f"SELECT {', '.join(cols)} FROM players")}
    con.close()
    return rows


def _money_state(players: dict) -> dict:
    """sid → {salary, projected} com a projeção do ano seguinte pela fonte única."""
    from salary_engine import project_next_salary
    return {sid: {"salary": int(p.salary), "projected": int(project_next_salary(p))}
            for sid, p in players.items()}


def _money_state_from(sid_to_fields: dict) -> dict:
    """Mesma projeção sobre estado JÁ LIDO (stubs) — o 'depois' simulado do --check."""
    from salary_engine import project_next_salary
    out = {}
    for sid, f in sid_to_fields.items():
        stub = SimpleNamespace(salary=f["salary"], espn_ref_value=f["espn"],
                               acquisition_type=f["acq"], contract_year=f["year"])
        out[sid] = {"salary": int(f["salary"]), "projected": int(project_next_salary(stub))}
    return out


# ── Relatórios ────────────────────────────────────────────────────────────────

def _report_header(source: str) -> None:
    print(f"\nLista CONGELADA: {len(all_targets())} alvos em {len(LOTS)} lotes "
          f"({' + '.join(str(len(l['cohort'])) + ' ' + l['canal'] for l in LOTS)})")
    print(f"Cruzamento ao vivo: {source}")
    for sid, why in FORBIDDEN.items():
        print(f"  FORA (por decisao) {sid:>6}  {why}")


def _report_out(out: list) -> None:
    for o in out:
        print(f"  fora   {o['sleeper_player_id']:>6}  {o['name']:<22} {o['reason']}")


# ── Comandos ──────────────────────────────────────────────────────────────────

def _resolve_live(offline: bool) -> tuple:
    """Deriva a elegibilidade do dia. offline=True não cruza (só a guarda do banco filtra)."""
    if offline:
        return set(cohort_sids()), "SEM cruzamento ao vivo - so a guarda do banco filtra"
    rostered = fetch_rostered_sids()
    return rostered, f"rosters ao vivo do Sleeper ({len(rostered)} jogadores rosterados)"


def cmd_check(db_path: Path, offline: bool = False) -> int:
    """Read-only: monta os lotes, revalida a guarda e confere o invariante salarial."""
    from models import Player
    from contract_year_correction import plan_correction, _player_state

    try:
        rostered, source = _resolve_live(offline)
    except Exception as exc:
        print(f"⛔ Falha ao ler os rosters ao vivo ({exc.__class__.__name__}: {exc}).")
        print("   Use --offline para inspecionar sem rede (nao vale para --apply).")
        return 1

    if offline:
        print("⚠️  MODO OFFLINE — lista NAO cruzada com os rosters ao vivo. So para inspecao.")
    _report_header(source)

    app = _make_app(db_path)
    total_elig, total_alvos, viol = 0, 0, []
    with app.app_context():
        print(f"\nBanco: {db_path}")
        for lot in LOTS:
            targets, out = derive_eligible_by_roster(lot["cohort"], rostered)
            names = {sid: name for sid, name, _o in lot["cohort"]}
            ids = [sid for sid, _n, _o in targets]
            total_alvos += len(lot["cohort"])

            print(f"\n── lote {lot['canal']}: {len(lot['cohort'])} congelados, "
                  f"{len(targets)} vivos ─────────────")
            print(f"  guarda: {lot['expected']}")
            _report_out(out)

            players = Player.query.filter(Player.sleeper_player_id.in_(ids)).all() if ids else []
            rows_by_id = {}
            for p in players:
                rows_by_id.setdefault(p.sleeper_player_id, []).append(p)
            eligible, skipped = plan_correction(
                ids, {sid: [_player_state(p) for p in ps] for sid, ps in rows_by_id.items()},
                lot["expected"])
            total_elig += len(eligible)

            for sid in eligible:
                p = rows_by_id[sid][0]
                print(f"  ok     {sid:>6}  {p.name:<22} cy {p.contract_year} -> {NEW_YEAR}  "
                      f"salario atual ${int(p.salary)} = devido ${int(p.salary)}  "
                      f"espn={p.espn_ref_value} css={p.contract_start_season}")
            for s in skipped:
                print(f"  PULADO {s['sleeper_player_id']:>6}  "
                      f"{names.get(s['sleeper_player_id'], '?'):<22} {s['reason']}")

            elig_players = {sid: rows_by_id[sid][0] for sid in eligible}
            before = _money_state(elig_players)
            after = _money_state_from({sid: {"salary": p.salary, "espn": p.espn_ref_value,
                                             "acq": p.acquisition_type, "year": NEW_YEAR}
                                       for sid, p in elig_players.items()})
            viol.extend(invariant_diff(before, after))

    print(f"\nInvariante salarial (simulado, ano {NEW_YEAR}): "
          f"{'OK - salario e projecao identicos' if not viol else 'VIOLADO'}")
    for v in viol:
        print(f"  x {v}")

    all_ok = total_elig == total_alvos and not viol
    print(f"\n--check: {'OK - ' + str(total_elig) + '/' + str(total_alvos) + ' elegiveis, invariante intacto' if all_ok else 'ATENCAO - ver acima'}")
    return 0 if all_ok else 1


def _verify_backup(backup: Path, db_path: Path) -> bool:
    if not backup.exists():
        print(f"⛔ Backup nao encontrado: {backup}")
        return False
    b, d = backup.stat().st_size, db_path.stat().st_size
    if b < 0.5 * d:
        print(f"⛔ Backup implausivel: {b} bytes contra {d} do banco alvo")
        return False
    print(f"Backup conferido: {backup} ({b} bytes; banco alvo {d} bytes)")
    return True


def cmd_apply(db_path: Path, backup: Path) -> int:
    """Guarda → escrita+trilha (porta canônica), lote a lote → verificação → commit."""
    from models import db, Player
    from contract_year_correction import apply_contract_year_correction, EVENT_TYPE

    if not _verify_backup(backup, db_path):
        return 1

    # ⛔ Sem cruzamento ao vivo não há escrita: o banco pode estar congelado (OPS2) ou
    # atrasado, e o Sleeper é a autoridade sobre quem ainda está rosterado.
    try:
        rostered, source = _resolve_live(offline=False)
    except Exception as exc:
        print(f"⛔ Falha ao ler os rosters ao vivo do Sleeper ({exc.__class__.__name__}: {exc}).")
        print("   Nenhuma escrita. A elegibilidade SO e valida cruzada ao vivo - reagende.")
        return 1
    _report_header(source)

    pre = _snapshot_players(db_path)
    applied, money_before, viol = [], {}, []

    app = _make_app(db_path)
    with app.app_context():
        for lot in LOTS:
            targets, out = derive_eligible_by_roster(lot["cohort"], rostered)
            names = {sid: name for sid, name, _o in lot["cohort"]}
            ids = [sid for sid, _n, _o in targets]
            print(f"\n── lote {lot['canal']}: {len(lot['cohort'])} congelados, "
                  f"{len(targets)} vivos ─────────────")
            _report_out(out)
            if not ids:
                print("  (nenhum alvo vivo neste lote)")
                continue

            pre_players = {p.sleeper_player_id: p for p in
                           Player.query.filter(Player.sleeper_player_id.in_(ids)).all()}
            money_before.update(_money_state(pre_players))

            result = apply_contract_year_correction(
                ids, expected=lot["expected"], new_year=NEW_YEAR,
                reason=REASON, event_ref=EVENT_REF)
            for a in result["applied"]:
                print(f"  ok     {a['sleeper_player_id']:>6}  {a['name']:<22} "
                      f"{a['team'][:26]:<26} contract_year {a['old']} -> {a['new']}")
            for s in result["skipped"]:
                print(f"  PULADO {s['sleeper_player_id']:>6}  "
                      f"{names.get(s['sleeper_player_id'], '?'):<22} {s['reason']}")
            applied.extend(result["applied"])

        if not applied:
            db.session.rollback()
            print("\nNada elegivel - nenhuma escrita. (Ja corrigido, ou estado divergente.)")
            return 1

        # Verificação in-transação antes do commit: releitura dos objetos encenados.
        bad = [a for a in applied
               if db.session.get(Player, a["player_id"]).contract_year != NEW_YEAR]
        if bad:
            db.session.rollback()
            print(f"⛔ Releitura in-transacao divergente ({len(bad)}) - rollback, nada escrito.")
            return 1
        db.session.commit()

        post_players = {a["sleeper_player_id"]: db.session.get(Player, a["player_id"])
                        for a in applied}
        money_after = _money_state(post_players)
        viol = invariant_diff({sid: money_before[sid] for sid in post_players}, money_after)

    # ── Verificação pós-commit por conexão independente (raw sqlite) ──────────
    post = _snapshot_players(db_path)
    applied_ids = {a["player_id"] for a in applied}
    errors = []

    if set(pre) != set(post):
        errors.append(f"linhas criadas/apagadas em players: {sorted(set(pre) ^ set(post))}")
    changed = {pid for pid in pre if pid in post
               and any(pre[pid][c] != post[pid][c] for c in pre[pid])}
    if changed != applied_ids:
        errors.append(f"linhas alteradas != elegiveis: {sorted(changed ^ applied_ids)}")
    for pid in applied_ids:
        diff_cols = {c for c in pre[pid] if pre[pid][c] != post[pid][c]}
        if not diff_cols <= {"contract_year", "updated_at"}:
            errors.append(f"player {pid}: colunas alteradas alem do campo: {sorted(diff_cols)}")
        if post[pid]["contract_year"] != NEW_YEAR:
            errors.append(f"player {pid}: contract_year={post[pid]['contract_year']} "
                          f"(esperado {NEW_YEAR})")

    con = sqlite3.connect(str(db_path))
    trail = con.execute(
        "SELECT COUNT(*) FROM player_history WHERE event_type=? AND sleeper_event_ref=?",
        (EVENT_TYPE, EVENT_REF)).fetchone()[0]
    con.close()
    if trail != len(applied):
        errors.append(f"trilha: {trail} linhas em player_history (esperado {len(applied)})")
    errors.extend(f"invariante salarial: {v}" for v in viol)

    print(f"\nVerificacao pos-escrita: {len(applied)} corrigidos; "
          f"{len(changed)} linhas alteradas; {trail} linhas de trilha; "
          f"invariante {'OK' if not viol else 'VIOLADO'}.")
    if errors:
        print("⛔ FALHAS DE VERIFICACAO (o commit JA ocorreu - avaliar restore do backup):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ OK - so contract_year (+updated_at) dos elegiveis mudou; trilha completa; "
          "salario e projecao inalterados.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="OFF26-37 Grupo B: contract_year 3→2 nos 11 com contrato nascido em 2025")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="read-only: lotes + guarda + cruzamento ao vivo + invariante")
    mode.add_argument("--apply", action="store_true", help="escreve (exige --backup conferivel)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatorio no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrao: env DYNASTY_DB")
    ap.add_argument("--offline", action="store_true",
                    help="--check apenas: inspeciona sem cruzar com os rosters ao vivo")
    args = ap.parse_args(argv)

    db_path = _db_path(args.db)
    if not db_path.exists():
        print(f"⛔ Banco nao encontrado: {db_path}")
        return 1
    if args.apply and args.offline:
        print("⛔ --offline nao vale no --apply: a elegibilidade so e valida cruzada com os "
              "rosters ao vivo (o banco pode estar congelado ou atrasado). Nenhuma escrita.")
        return 1
    if args.apply and not args.backup:
        print("⛔ --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    return cmd_check(db_path, args.offline) if args.check else cmd_apply(db_path, Path(args.backup))


if __name__ == "__main__":
    sys.exit(main())
