"""
seed_users.py — Populate the users table from a CSV file or CLI arguments.

Usage:
    # From CSV (columns: email, name, team_id, is_admin)
    python seed_users.py --csv users.csv

    # Single user via CLI
    python seed_users.py --email user@gmail.com --name "Erico" --team-id 1 --admin

    # List current users
    python seed_users.py --list

CSV format example (users.csv):
    email,name,team_id,is_admin
    erico@gmail.com,Erico,1,1
    owner2@gmail.com,Owner 2,2,0
    owner3@gmail.com,Owner 3,3,0
"""

import argparse
import csv
import sys
import os

# Ensure app context is available
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_app():
    from app import create_app
    return create_app()


def seed_from_csv(csv_path):
    app = get_app()
    with app.app_context():
        from models import db, User
        if not os.path.exists(csv_path):
            print(f"Erro: arquivo '{csv_path}' nao encontrado.")
            sys.exit(1)

        added, skipped = 0, 0
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email", "").strip().lower()
                if not email:
                    continue

                existing = User.query.filter_by(email=email).first()
                if existing:
                    print(f"  [skip] {email} ja existe (id={existing.id})")
                    skipped += 1
                    continue

                user = User(
                    email=email,
                    name=row.get("name", "").strip() or None,
                    team_id=int(row["team_id"]) if row.get("team_id") else None,
                    is_admin=str(row.get("is_admin", "0")).strip() in ("1", "true", "True", "yes"),
                )
                db.session.add(user)
                added += 1
                admin_tag = " [ADMIN]" if user.is_admin else ""
                print(f"  [add] {email} → team_id={user.team_id}{admin_tag}")

        db.session.commit()
        print(f"\nResultado: {added} adicionado(s), {skipped} pulado(s).")


def seed_single(email, name, team_id, is_admin):
    app = get_app()
    with app.app_context():
        from models import db, User
        email = email.strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"Erro: {email} ja existe (id={existing.id}).")
            sys.exit(1)

        user = User(
            email=email,
            name=name or None,
            team_id=team_id,
            is_admin=is_admin,
        )
        db.session.add(user)
        db.session.commit()
        admin_tag = " [ADMIN]" if is_admin else ""
        print(f"Usuario criado: {email} → team_id={team_id}{admin_tag} (id={user.id})")


def list_users():
    app = get_app()
    with app.app_context():
        from models import User
        users = User.query.order_by(User.id).all()
        if not users:
            print("Nenhum usuario cadastrado.")
            return

        print(f"{'ID':>4}  {'Email':<35}  {'Nome':<20}  {'Team':>4}  {'Admin'}")
        print("-" * 80)
        for u in users:
            admin = "SIM" if u.is_admin else ""
            print(f"{u.id:>4}  {u.email:<35}  {(u.name or '')::<20}  {(u.team_id or ''):>4}  {admin}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed users table for Dynasty SB")
    parser.add_argument("--csv", help="Path to CSV file with users")
    parser.add_argument("--email", help="Email for single user creation")
    parser.add_argument("--name", help="Name for single user", default="")
    parser.add_argument("--team-id", type=int, help="Team ID for single user")
    parser.add_argument("--admin", action="store_true", help="Set user as admin")
    parser.add_argument("--list", action="store_true", help="List current users")

    args = parser.parse_args()

    if args.list:
        list_users()
    elif args.csv:
        print(f"Importando usuarios de {args.csv}...")
        seed_from_csv(args.csv)
    elif args.email:
        seed_single(args.email, args.name, args.team_id, args.admin)
    else:
        parser.print_help()
