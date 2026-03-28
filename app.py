import os
from flask import Flask, redirect, url_for
from models import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'dynasty.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dynasty-sb-2025-secret")

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _run_migrations()
        _seed_app_config()
        from import_csv import run_import
        fresh_import = run_import()
        if fresh_import:
            print("[app] First run — running Sleeper sync to assign teams...")
            from sync_sleeper import run_sync
            summary = run_sync()
            print(f"[app] Sync done: {summary['teams_updated']} teams, "
                  f"{summary['players_updated']} assigned, "
                  f"{summary['players_added']} new from Sleeper")
            # Backfill player history from imported data
            from routes.admin import _backfill_player_history
            hist_count = _backfill_player_history()
            if hist_count:
                print(f"[app] Backfilled {hist_count} player history entries")

    # Context processor — injects offseason state into all templates
    @app.context_processor
    def inject_global_state():
        from models import get_config, get_current_season, is_offseason
        return {
            "g_offseason_mode": is_offseason(),
            "g_current_season": get_current_season(),
            "g_offseason_step": int(get_config("offseason_step", "0")),
        }

    # Register blueprints
    from routes.roster  import roster_bp
    from routes.salary  import salary_bp
    from routes.trades  import trades_bp
    from routes.picks   import picks_bp
    from routes.auction import auction_bp
    from routes.admin   import admin_bp
    from routes.offseason import offseason_bp

    app.register_blueprint(roster_bp)
    app.register_blueprint(salary_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(picks_bp)
    app.register_blueprint(auction_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(offseason_bp)

    # Error pages
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("error.html", code=404,
                               message="Página não encontrada."), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("error.html", code=500,
                               message="Erro interno do servidor."), 500

    return app


def _run_migrations():
    """Add columns that db.create_all() won't add to existing tables."""
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    if "espn_values" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("espn_values")]
        if "is_final" not in cols:
            db.session.execute(text("ALTER TABLE espn_values ADD COLUMN is_final BOOLEAN DEFAULT 0"))
            db.session.commit()
            print("[migrate] Added is_final to espn_values")


def _seed_app_config():
    """Seed default app_config values if missing."""
    from models import AppConfig, CURRENT_SEASON
    defaults = {
        "current_season": str(CURRENT_SEASON),
        "offseason_mode": "false",
        "offseason_step": "0",
        "season_closed": "false",
        "season_locked": "false",
        "espn_values_updated": "false",
        "rollover_done": "false",
        "rookie_draft_done": "false",
        "auction_done": "false",
        "playoffs_started": "false",
    }
    for key, val in defaults.items():
        if not db.session.get(AppConfig, key):
            db.session.add(AppConfig(key=key, value=val))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  Dynasty SB — Fantasy Manager")
    print("  http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)
