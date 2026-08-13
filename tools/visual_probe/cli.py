"""
cli.py — driver da sonda de validação visual (O7). Toda a decisão vive em `core.py`.

Perfil de execução (o que torna o gate barato o bastante para ser cumprido):
  · **sem app de pé**  — usa o test client do Flask para renderizar o HTML;
  · **sem login real** — injeta o cookie de sessão de um usuário do banco (zero OAuth);
  · **sem rede**       — `run_sync` é neutralizado antes do boot;
  · **sem estado**     — o banco é COPIADO para um diretório temporário, e é ele que o
                         app abre (`DYNASTY_DB`); o `dynasty.db` real nunca é aberto
                         para escrita.

⭐ `--css <arquivo>` é o **CONTROLE POSITIVO** e não é enfeite: troca só a folha de
estilo e roda a MESMA página. Um detector que nunca foi visto acusando o defeito
conhecido não vale como aprovação — foi assim que um poller "verde" escondeu um deploy
por 10 minutos durante a saga [[L3]]. Ver o README.

Uso:
    python tools/visual_probe/cli.py                      # suíte completa
    python tools/visual_probe/cli.py --page league        # uma página
    python tools/visual_probe/cli.py --width 1280         # uma largura
    python tools/visual_probe/cli.py --css /tmp/antigo.css --page league   # controle
    python tools/visual_probe/cli.py --list               # cobertura e motivos
"""
import argparse
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from tools.visual_probe import core                                # noqa: E402


def _listar() -> int:
    print("Cobertura (o critério decide a lista — ver core.PAGES):\n")
    for p in core.PAGES:
        fam = "geometria" + (" + anatomia" if p["anatomia"] else "")
        print(f"  {p['nome']:<12} {p['rota']:<16} [{fam}]")
        print(f"      {p['nota']}")
    print("\nLarguras canônicas:\n")
    for w in core.WIDTHS:
        print(f"  {w['px']:>5}px  {w['motivo']}")
    print("\nDefeitos conhecidos (reportam, não bloqueiam):\n")
    for c in core.KNOWN_DEFECTS:
        print(f"  [{c['id']}] {c['tipo']} @ {c['larguras']}px — {c['nota']}")
    problemas = core.validar_config()
    print("\nconfig:", "íntegra" if not problemas else f"PROBLEMAS {problemas}")
    return 1 if problemas else 0


def _preparar_app(tmp: Path):
    """Boot isolado: cópia do banco + sync neutralizado. Devolve (app, client, team_id)."""
    origem = Path(os.environ.get("DYNASTY_DB") or (BASE_DIR / "dynasty.db"))
    if not origem.exists():
        print(f"⛔ banco não encontrado: {origem}")
        raise SystemExit(2)
    copia = tmp / "probe.db"
    shutil.copyfile(origem, copia)
    os.environ["DYNASTY_DB"] = str(copia)
    os.environ.setdefault("SECRET_KEY", "visual-probe")

    import sync_sleeper
    sync_sleeper.run_sync = lambda *a, **k: {"teams_updated": 0, "players_updated": 0,
                                             "players_added": 0}
    from app import app
    from models import User, Team

    with app.app_context():
        user = User.query.filter_by(is_admin=True).first() or User.query.first()
        if user is None:
            print("⛔ nenhum usuário no banco — a sonda precisa de um para autenticar")
            raise SystemExit(2)
        time_id = Team.query.order_by(Team.name).first().id
        uid = user.id
    client = app.test_client()
    with client.session_transaction() as s:
        s["_user_id"] = str(uid)
        s["_fresh"] = True
    return app, client, time_id


def _salvar_paginas(client, tmp: Path, team_id: int, css: str | None, paginas) -> dict:
    """Renderiza cada página e grava em disco, com a folha de estilo ao lado."""
    shutil.copyfile(css or (BASE_DIR / "static" / "style.css"), tmp / "style.css")
    arquivos = {}
    for p in paginas:
        rota = p["rota"].format(team_id=team_id)
        r = client.get(rota)
        if r.status_code != 200:
            print(f"⛔ {rota} devolveu HTTP {r.status_code} — a sonda mede página que "
                  f"renderiza; verifique login/rota")
            raise SystemExit(2)
        html = r.get_data(as_text=True).replace('href="/static/style.css"',
                                                'href="style.css"')
        destino = tmp / f"{p['nome']}.html"
        destino.write_text(html, encoding="utf-8")
        arquivos[p["nome"]] = destino
    return arquivos


def _medir(arquivos, paginas, larguras, tmp: Path) -> list:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⛔ playwright não instalado. `pip install playwright && playwright "
              "install chromium`. A sonda NÃO degrada para 'passou' — sem browser não "
              "há medição.")
        raise SystemExit(2)

    medicoes = []
    with sync_playwright() as pw:
        try:
            navegador = pw.chromium.launch()
        except Exception as e:                                   # browser ausente
            print(f"⛔ falha ao abrir o Chromium: {e}\n   rode `playwright install chromium`")
            raise SystemExit(2)
        pagina = navegador.new_page()
        for w in larguras:
            pagina.set_viewport_size({"width": w["px"], "height": 1400})
            for p in paginas:
                pagina.goto("file:///" + str(arquivos[p["nome"]]).replace("\\", "/"))
                pagina.wait_for_timeout(120)
                achados = []
                for a in pagina.evaluate(core.JS_GEOMETRIA, p["geometria"]):
                    achados.append({**a, "pagina": p["nome"], "largura": w["px"]})
                ovf = pagina.evaluate(core.JS_OVERFLOW)
                if ovf["transborda"]:
                    achados.append({
                        "tipo": "overflow_documento", "pagina": p["nome"],
                        "largura": w["px"], "culpados": ovf["culpados"],
                        "detalhe": "documento rola na horizontal: "
                                   + ", ".join(ovf["culpados"][:4]),
                    })
                anat, ausente = None, False
                if p["anatomia"]:
                    medidas = pagina.evaluate(core.JS_ANATOMIA, p["anatomia"])
                    if len(medidas) < 2:
                        ausente = True
                    else:
                        anat = core.anatomia_divergente(medidas)
                        if anat:
                            achados.append({
                                "tipo": "anatomia", "pagina": p["nome"],
                                "largura": w["px"], "culpados": [p["anatomia"]["grupo"]],
                                "detalhe": f"{anat['n_assinaturas']} anatomias entre "
                                           f"{len(medidas)} irmãos · alturas "
                                           f"{anat['alturas']} · linhas {anat['linhas']}",
                            })
                medicoes.append({"pagina": p["nome"], "largura": w["px"],
                                 "achados": achados, "anatomia": anat,
                                 "anatomia_ausente": ausente})
                pagina.screenshot(path=str(tmp / f"{p['nome']}_{w['px']}.png"))
        navegador.close()
    return medicoes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sonda de validação visual (O7)")
    ap.add_argument("--css", help="CONTROLE POSITIVO: usa esta folha de estilo no lugar "
                                  "de static/style.css (mesma página, CSS trocado)")
    ap.add_argument("--page", action="append", help="restringe a página(s) por nome")
    ap.add_argument("--width", action="append", type=int, help="restringe a largura(s)")
    ap.add_argument("--list", action="store_true", help="mostra cobertura e motivos")
    ap.add_argument("--keep", action="store_true", help="preserva os artefatos do run")
    args = ap.parse_args(argv)

    if args.list:
        return _listar()

    problemas = core.validar_config()
    if problemas:
        print("⛔ configuração inválida:\n  " + "\n  ".join(problemas))
        return 2

    paginas = [p for p in core.PAGES if not args.page or p["nome"] in args.page]
    larguras = [w for w in core.WIDTHS if not args.width or w["px"] in args.width]
    if not paginas or not larguras:
        print("⛔ filtro não casou nenhuma página/largura (veja --list)")
        return 2

    inicio = time.time()
    tmp = Path(tempfile.mkdtemp(prefix="visual_probe_"))
    try:
        _, client, team_id = _preparar_app(tmp)
        arquivos = _salvar_paginas(client, tmp, team_id, args.css, paginas)
        medicoes = _medir(arquivos, paginas, larguras, tmp)
        achados = [a for m in medicoes for a in m["achados"]]
        classificado = core.classificar(achados)
        print(core.formatar({"medicoes": medicoes, "classificado": classificado,
                             "segundos": time.time() - inicio, "css": args.css}))
        if args.keep:
            print(f"\n  artefatos: {tmp}")
        return core.exit_code(classificado)
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
