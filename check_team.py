from app import create_app
from models import db, Player

app = create_app()
with app.app_context():
    players = Player.query.filter_by(is_my_team=True).order_by(Player.position).all()
    total = sum(p.salary for p in players)
    print('Jogadores: ' + str(len(players)) + ' | Cap: $' + str(total))
    print()
    for p in players:
        print('  ' + p.name.ljust(25) + ' ' + p.position.ljust(5) + ' $' + str(p.salary).ljust(4) + ' Ano ' + str(p.contract_year) + '/4')
