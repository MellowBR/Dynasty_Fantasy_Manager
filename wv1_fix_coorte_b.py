"""
wv1_fix_coorte_b.py — runner ONE-SHOT da correção MAN-WV1-FIX-COORTE-B.

Aprovação do owner em 20/08/2026, sobre o parecer pré-execução ([[MAN-METH-2]]) registrado na
seção WV1 do improvements.md (commit c2a6eb8).

O QUE CORRIGE. A **decisão ESTRITA** do owner (19/08) converteu os **17 claims ambíguos** da
MAN-WV1-F1 em **aquisição nova**: o claim só carrega o contrato anterior se vence a janela do
PRÓPRIO drop (clearance ~47h; `waiver_clear_days=2`); passada a clearance o jogador foi exposto
à liga inteira, e quem o pega faz aquisição nova — a regra de carregar existe para impedir reset
de contrato via drop-e-readd, não para permitir que o detentor do maior FAAB resgate contrato
antigo fora da janela. Aquisição nova ⇒ ano 1 = 2025 ⇒ **2026 é ano 2**; a coorte marca `cy=3`.

⭐ **NENHUM DINHEIRO SE MOVE.** Todos os elegíveis estão a $1 ⇒ `SALARY_FIXES` vazio e o
invariante volta a ser o do `off26_32_fix.py` ("mexe na contagem, nunca no dinheiro"), ao
contrário da coorte A, que corrigiu 2 salários.

FORMA — por que este arquivo IMPORTA o runner A em vez de estendê-lo. O `wv1_fix_coorte.py` **já
rodou em produção** (19/08, commit e7375a8); alterá-lo depois criaria um arquivo cujo
comportamento não é mais o que foi executado, o que corrói a auditoria de um reparo de contrato.
O núcleo puro de lá já é parametrizável (`triage`, `select_salary_fixes`, `expected_money_after`
recebem cohort/expected/fixes por argumento), então aqui só entram a lista congelada e a
orquestração: **zero réplica de regra, zero mutação do executado.**

⚠️ MUDANÇA DE CALENDÁRIO (owner, 20/08) E A CONSEQUÊNCIA DE DESENHO: a execução saiu de
pré-lock para **PÓS-lock**, na mesma ida do `off26_32_fix.py` — o owner prefere esperar os
cortes, e é provável que parte da coorte seja dropada. Isso muda o peso do cruzamento ao vivo:
pós-lock os cortes acontecem **direto no Sleeper** (OFF26-1 ETAPA2) e pode haver **freeze de
sync** (OPS2), de modo que o `is_dropped` do banco está **desatualizado de propósito**. Por isso,
aqui — ao contrário do runner A, que rodava pré-lock — **o cruzamento com os rosters ao vivo é
OBRIGATÓRIO no `--apply`**: quem não estiver rosterado ao vivo é tratado como dropado e pulado
(decisão 2, de 19/08), mesmo que o banco ainda o mostre vivo. Sem API, não há escrita — o
critério é o mesmo do OFF26-32, e a correção não tem prazo (o efeito é na renovação).

Uso (no Render Shell, com DYNASTY_DB=/data/dynasty.db no ambiente):

    sqlite3 /data/dynasty.db ".backup '/data/pre_wv1_fix_b.db'"
    python wv1_fix_coorte_b.py --check
    python wv1_fix_coorte_b.py --apply --backup /data/pre_wv1_fix_b.db

    # Ensaio local: --db <copia>;  inspeção sem rede: --offline (só no --check)
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import wv1_fix_coorte as A

# ── Coorte B CONGELADA — os 17 claims ambíguos resolvidos a jogador (parecer de 19/08).
# 6 sids são churn sem row em `Player` (9506, CAR, 5955, 8122, 11789, 8123) e ficam de fora da
# lista por não existirem; os 2 abaixo saem por MOTIVO, e o motivo é impresso no relatório.
COHORT_B = [
    ("3451",  "Ka'imi Fairbairn"),
    ("8259",  "Cameron Dicker"),
    ("11626", "Xavier Legette"),
    ("NE",    "New England Patriots"),
    ("12540", "Chimere Dike"),
    ("TB",    "Tampa Bay Buccaneers"),
    ("BAL",   "Baltimore Ravens"),
    ("9504",  "Kayshon Boutte"),
    ("3678",  "Wil Lutz"),
]

# Exclusões DOCUMENTADAS (molde do DROPPED_2026 do off26_32_fix): a exclusão é auditável,
# nunca silenciosa. ⛔ DET fora é requisito de correção, não preferência: a aquisição que o
# governa é um `free_agent ADD` POSTERIOR ao claim (cadeia conferida na API), e como a guarda
# exige `acquisition_type=fa_waiver` ele dispararia o ABORT — nenhuma linha seria escrita.
EXCLUDED = {
    "DET": ("Detroit Lions - a aquisicao que governa e um free_agent ADD posterior ao claim "
            "(26/10/2025); acquisition_type=free_agent no banco. Fora da coorte de waiver - e "
            "incluir dispararia o ABORT da guarda"),
    "9228": ("Bryce Young - duplicata: o claim que governa e o de 17/12, ja reparado na coorte A "
             "em 19/08 (fix:wv1-coorte)"),
}

# ⭐ Vazio de propósito: nenhum elegível da coorte B tem salário a corrigir.
SALARY_FIXES_B = {}

EVENT_REF = "fix:wv1-coorte-b"
REASON = ("Correcao MAN-WV1-FIX-COORTE-B aprovada pelo owner em 20/08/2026, sob a decisao "
          "ESTRITA de 19/08 (claim fora da janela do proprio drop = aquisicao nova; regra "
          "6.6/6.8: ano 1 = 2025, logo 2026 e ano 2)")


# ── Relatório ─────────────────────────────────────────────────────────────────

def _report(states, eligible, skipped, aborts, names, not_live, live_note):
    print(f"\nCoorte B congelada: {len(COHORT_B)} sids (decisao ESTRITA de 19/08; parecer c2a6eb8)")
    for sid, why in EXCLUDED.items():
        print(f"  EXCLUIDO {sid:>6}  {why}")
    print(f"Cruzamento ao vivo: {live_note}")
    print(f"Guarda da porta: {A.EXPECTED}")

    print(f"\nELEGIVEIS ({len(eligible)}):")
    for sid in eligible:
        st = states[sid][0]
        print(f"  ok     {sid:>6}  {st['name']:<22} {st['team'][:22]:<22} "
              f"cy {st['contract_year']} -> {A.NEW_YEAR}  sal ${int(st['salary'])} "
              f"espn {st['espn_ref_value']} css {st['contract_start_season']}")
    if not eligible:
        print("  (nenhum)")

    print(f"\nPULADOS ({len(skipped)}):")
    for s in skipped:
        sid = s["sleeper_player_id"]
        flag = "DROPADO" if "DROPADO" in s["reason"] or "ao vivo" in s["reason"] else "       "
        print(f"  {flag} {sid:>6}  {names.get(sid, '?'):<22} {s['reason']}")
    if not skipped:
        print("  (nenhum)")

    if aborts:
        print(f"\n[ABORT] MOTIVOS DE ABORTO ({len(aborts)}) - NADA sera escrito:")
        for a in aborts:
            print(f"  ABORT  {a['sleeper_player_id']:>6}  "
                  f"{names.get(a['sleeper_player_id'], '?'):<22} {a['reason']}")


def _live_filter(eligible, skipped, not_live):
    """Pós-lock: quem não está rosterado AO VIVO é dropado, mesmo que o banco diga o contrário."""
    kept = []
    for sid in eligible:
        if sid in not_live:
            skipped.append({"sleeper_player_id": sid,
                            "reason": "nao rosterado ao vivo - cortado no Sleeper; o banco ainda "
                                      "nao sincronizou (pulado, decisao 2)"})
        else:
            kept.append(sid)
    return kept, skipped


def _resolve_live(sids, offline):
    """Devolve (not_live, nota). Levanta se a API falhar e offline=False."""
    if offline:
        return set(), "SEM cruzamento ao vivo (--offline) - so inspecao"
    rostered = A.fetch_rostered_sids()
    return {s for s in sids if s not in rostered}, \
           f"rosters ao vivo do Sleeper ({len(rostered)} rosterados)"


# ── Comandos ──────────────────────────────────────────────────────────────────

def cmd_check(db_path: Path, offline: bool = False) -> int:
    names = dict(COHORT_B)
    sids = [sid for sid, _ in COHORT_B]
    try:
        not_live, live_note = _resolve_live(sids, offline)
    except Exception as exc:
        print(f"[X] Falha ao ler os rosters ao vivo ({exc.__class__.__name__}: {exc}). "
              "Use --offline para inspecionar sem rede.")
        return 1

    app = A._make_app(db_path)
    with app.app_context():
        states = A._states_from_db(sids)
        eligible, skipped, aborts = A.triage(states, cohort=COHORT_B, expected=A.EXPECTED)
        eligible, skipped = _live_filter(eligible, skipped, not_live)
        print(f"\nBanco: {db_path}")
        _report(states, eligible, skipped, aborts, names, not_live, live_note)

        to_fix, sal_mm = A.select_salary_fixes(eligible, states, fixes=SALARY_FIXES_B)
        print(f"\nCorrecoes de salario previstas: {len(to_fix)} "
              "(coorte B nao move dinheiro - todos a $1)")

        before = A._money_state(states, eligible)
        after = A.expected_money_after(states, eligible, fixes=SALARY_FIXES_B)
        viol = A.money_diff(before, after)
        print(f"\nInvariante financeiro (simulado): "
              f"{'OK - salario e projecao IDENTICOS' if not viol else 'VIOLADO'}")
        for v in viol:
            print(f"  x {v}")

    ok = not aborts and not viol and not to_fix
    print(f"\n--check: {'OK - ' + str(len(eligible)) + ' elegiveis, ' + str(len(skipped)) + ' pulados, nada de dinheiro se move' if ok else 'ATENCAO - ver acima; --apply RECUSA executar'}")
    return 0 if ok else 1


def cmd_apply(db_path: Path, backup: Path) -> int:
    from models import db, Player
    from contract_year_correction import apply_contract_year_correction, EVENT_TYPE

    if not A._verify_backup(backup, db_path):
        return 1

    names = dict(COHORT_B)
    sids = [sid for sid, _ in COHORT_B]
    # ⛔ Pós-lock, sem cruzamento ao vivo NAO HA ESCRITA: o banco pode estar congelado (OPS2)
    # ou atrasado, e o Sleeper e a autoridade sobre quem ainda esta rosterado.
    try:
        not_live, live_note = _resolve_live(sids, offline=False)
    except Exception as exc:
        print(f"[X] Falha ao ler os rosters ao vivo ({exc.__class__.__name__}: {exc}).")
        print("   Nenhuma escrita. Pos-lock a lista SO e valida cruzada ao vivo - reagende.")
        return 1

    pre = A._snapshot_players(db_path)
    app = A._make_app(db_path)
    with app.app_context():
        states = A._states_from_db(sids)
        eligible, skipped, aborts = A.triage(states, cohort=COHORT_B, expected=A.EXPECTED)
        eligible, skipped = _live_filter(eligible, skipped, not_live)
        _report(states, eligible, skipped, aborts, names, not_live, live_note)

        if aborts:
            print("\n[X] ABORTADO por estado inesperado (decisao 3 de 19/08). Nada escrito.")
            return 1
        if not eligible:
            print("\nNada elegivel - nenhuma escrita. (Ja corrigido, ou todos cortados.)")
            return 1

        money_before = A._money_state(states, eligible)

        result = apply_contract_year_correction(
            eligible, expected=A.EXPECTED, new_year=A.NEW_YEAR,
            reason=REASON, event_ref=EVENT_REF)
        if len(result["applied"]) != len(eligible):
            db.session.rollback()
            print(f"\n[X] A guarda da porta canonica recusou {len(result['skipped'])} linha(s) "
                  "que a triagem julgou elegiveis - rollback, nada escrito:")
            for s in result["skipped"]:
                print(f"  - {s['sleeper_player_id']}: {s['reason']}")
            return 1
        for a in result["applied"]:
            print(f"  escrito {a['sleeper_player_id']:>6}  {a['name']:<22} "
                  f"contract_year {a['old']} -> {a['new']}")

        bad = [a for a in result["applied"]
               if db.session.get(Player, a["player_id"]).contract_year != A.NEW_YEAR]
        if bad:
            db.session.rollback()
            print(f"\n[X] Releitura in-transacao divergente ({len(bad)}) - rollback, nada escrito.")
            return 1

        db.session.commit()
        applied = result["applied"]

        post_states = A._states_from_db(eligible)
        money_after = A._money_state(post_states, eligible)
        viol = A.money_diff(money_before, money_after)

    post = A._snapshot_players(db_path)
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
        if post[pid]["contract_year"] != A.NEW_YEAR:
            errors.append(f"player {pid}: contract_year={post[pid]['contract_year']} "
                          f"(esperado {A.NEW_YEAR})")

    con = sqlite3.connect(str(db_path))
    trail = con.execute(
        "SELECT COUNT(*) FROM player_history WHERE event_type=? AND sleeper_event_ref=?",
        (EVENT_TYPE, EVENT_REF)).fetchone()[0]
    con.close()
    if trail != len(applied):
        errors.append(f"trilha: {trail} linhas (esperado {len(applied)})")
    errors.extend(f"invariante financeiro: {v}" for v in viol)

    print(f"\nVerificacao pos-escrita: {len(applied)} contagens corrigidas; "
          f"{len(changed)} linhas alteradas; {trail} linhas de trilha; "
          f"invariante {'OK' if not viol else 'VIOLADO'}.")
    if errors:
        print("[X] FALHAS DE VERIFICACAO (o commit JA ocorreu - avaliar restore do backup):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[OK] So contract_year (+updated_at) dos elegiveis mudou; trilha completa; "
          "NENHUM salario ou projecao alterado.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="MAN-WV1-FIX-COORTE-B: contract_year 3->2 nos ex-ambiguos (decisao estrita)")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only: triagem + invariante")
    mode.add_argument("--apply", action="store_true", help="escreve (exige --backup conferivel)")
    ap.add_argument("--backup", help="caminho do backup feito ANTES (obrigatorio no --apply)")
    ap.add_argument("--db", help="override do banco (ensaio); padrao: env DYNASTY_DB")
    ap.add_argument("--offline", action="store_true",
                    help="--check apenas: inspeciona sem cruzar com os rosters ao vivo")
    args = ap.parse_args(argv)

    db_path = A._db_path(args.db)
    if not db_path.exists():
        print(f"[X] Banco nao encontrado: {db_path}")
        return 1
    if args.apply and args.offline:
        print("[X] --offline nao vale no --apply: pos-lock a lista so e valida cruzada com os "
              "rosters ao vivo (o banco pode estar congelado ou atrasado). Nenhuma escrita.")
        return 1
    if args.apply and not args.backup:
        print("[X] --apply exige --backup <caminho do backup feito antes>. Nenhuma escrita.")
        return 1
    return cmd_check(db_path, args.offline) if args.check else cmd_apply(db_path, Path(args.backup))


if __name__ == "__main__":
    sys.exit(main())
