"""
keeper_audit_fixtures.py — MATERIAL DE TESTE do OFF26-4 (F2).

⛔ ISTO NÃO É A KEEPER SHEET REAL, E NUNCA SERÁ.
   A sheet real nasce da revelação da janela de cortes (OFF26-1/OFF26-2) em 20/08 e vive
   no banco, derivada por `routes/cuts._build_keeper_sheet`. Este arquivo é dado congelado
   para teste do diff — nenhum caminho de produção o importa (só `keeper_audit_test.py`).

Procedência (congelada em 03/08/2026, leitura read-only):
  · BOARD  — `GET /draft/{id}/picks` da liga fantasma `1389725099556372481`,
             24 designações reais (Team 3 $148 / Team 4 $95 / Team 5 $60), com os dois
             DEF de id-sigla ("LAR", "HOU") preservados de propósito.
  · SHEET  — elencos atuais do `dynasty.db` de dev; os 3 times que correspondem às colunas
             populadas recebem EXATAMENTE o conteúdo do board (por isso a fixture A é
             coerente por construção).
  · COLUNAS — as 9 atribuições reais de owner + 3 SINTÉTICAS (os owners que ainda não
             aceitaram o convite), para que a fixture A tenha os 12 times atribuíveis.
             O terreno real (coluna com `owner_id` nulo) é exercitado à parte, em
             `BOARD_SEM_OWNER`.

Enquadramento ao cap na geração (regra do owner: remover o de MENOR salário suficiente;
se nenhum resolver sozinho, remover o de MAIOR e reaplicar) — ⚠️ artifício de geração,
NÃO regra de negócio: os cortes reais são declarados pelos owners na janela selada.
Nenhum time precisou de corte: todos já fechavam em ≤ $200.
"""

# ── BOARD (lado Sleeper) ─────────────────────────────────────────────────────
# Formato = saída de `keeper_audit.fetch_board`, com o `amount` como STRING, do
# jeito que a API entrega (a coerção é responsabilidade do núcleo).
BOARD_A = {
    "league_id": "1389725099556372481",
    "league_name": "Dynasty SB FA Auction",
    "draft_id": "1389755381567213568",   # derivado, NUNCA persistido
    "draft_status": 'pre_draft',
    "draft_type": 'auction',
    "rounds": 22,        # do DRAFT, não da liga
    "budget": 200,
    "columns": [
        {"roster_id": '1', "owner_id": '1130162144764506112'},
        {"roster_id": '2', "owner_id": '695859519976210432'},
        {"roster_id": '3', "owner_id": '695859970096328704'},
        {"roster_id": '4', "owner_id": '205848303030505472'},
        {"roster_id": '5', "owner_id": '1133812910268010496'},
        {"roster_id": '6', "owner_id": '1129822349391470592'},
        {"roster_id": '7', "owner_id": '1131747074137272320'},
        {"roster_id": '8', "owner_id": '1133818177651224576'},
        {"roster_id": '9', "owner_id": '732411754436526080'},
        {"roster_id": '10', "owner_id": '698015187109773312'},  # sintética
        {"roster_id": '11', "owner_id": '1126909140380569600'},  # sintética
        {"roster_id": '12', "owner_id": '867557566065045504'},  # sintética
    ],
    "designations": [
        # roster 3 — 10 designações, $148
        {"roster_id": '3', "sleeper_player_id": '4881', "name": 'Lamar Jackson', "position": 'QB', "amount": '40'},
        {"roster_id": '3', "sleeper_player_id": '9509', "name": 'Bijan Robinson', "position": 'RB', "amount": '35'},
        {"roster_id": '3', "sleeper_player_id": '8150', "name": 'Kyren Williams', "position": 'RB', "amount": '12'},
        {"roster_id": '3', "sleeper_player_id": '7564', "name": "Ja'Marr Chase", "position": 'WR', "amount": '30'},
        {"roster_id": '3', "sleeper_player_id": '8112', "name": 'Drake London', "position": 'WR', "amount": '14'},
        {"roster_id": '3', "sleeper_player_id": '7526', "name": 'Jaylen Waddle', "position": 'WR', "amount": '8'},
        {"roster_id": '3', "sleeper_player_id": '11604', "name": 'Brock Bowers', "position": 'TE', "amount": '5'},
        {"roster_id": '3', "sleeper_player_id": '9224', "name": 'Chase Brown', "position": 'RB', "amount": '2'},
        {"roster_id": '3', "sleeper_player_id": '11533', "name": 'Brandon Aubrey', "position": 'K', "amount": '1'},
        {"roster_id": '3', "sleeper_player_id": 'LAR', "name": 'Los Angeles Rams', "position": 'DEF', "amount": '1'},
        # roster 4 — 8 designações, $95
        {"roster_id": '4', "sleeper_player_id": '11566', "name": 'Jayden Daniels', "position": 'QB', "amount": '28'},
        {"roster_id": '4', "sleeper_player_id": '6813', "name": 'Jonathan Taylor', "position": 'RB', "amount": '26'},
        {"roster_id": '4', "sleeper_player_id": '11584', "name": 'Bucky Irving', "position": 'RB', "amount": '10'},
        {"roster_id": '4', "sleeper_player_id": '9493', "name": 'Puka Nacua', "position": 'WR', "amount": '18'},
        {"roster_id": '4', "sleeper_player_id": '11632', "name": 'Malik Nabers', "position": 'WR', "amount": '9'},
        {"roster_id": '4', "sleeper_player_id": '4217', "name": 'George Kittle', "position": 'TE', "amount": '2'},
        {"roster_id": '4', "sleeper_player_id": '8259', "name": 'Cameron Dicker', "position": 'K', "amount": '1'},
        {"roster_id": '4', "sleeper_player_id": 'HOU', "name": 'Houston Texans', "position": 'DEF', "amount": '1'},
        # roster 5 — 6 designações, $60
        {"roster_id": '5', "sleeper_player_id": '4046', "name": 'Patrick Mahomes', "position": 'QB', "amount": '22'},
        {"roster_id": '5', "sleeper_player_id": '12527', "name": 'Ashton Jeanty', "position": 'RB', "amount": '20'},
        {"roster_id": '5', "sleeper_player_id": '3321', "name": 'Tyreek Hill', "position": 'WR', "amount": '9'},
        {"roster_id": '5', "sleeper_player_id": '12526', "name": 'Tetairoa McMillan', "position": 'WR', "amount": '7'},
        {"roster_id": '5', "sleeper_player_id": '8130', "name": 'Trey McBride', "position": 'TE', "amount": '1'},
        {"roster_id": '5', "sleeper_player_id": '2747', "name": 'Jason Myers', "position": 'K', "amount": '1'},
    ],
}

# ── SHEET (lado Manager) ─────────────────────────────────────────────────────
# Formato = saída de `keeper_audit.build_sheet`. Keeper = (sleeper_player_id, nome, posição, salário).
SHEET_A = {
    "revealed": True,
    "season": 2026,
    "lock_timestamp": "2026-08-03T00:00:00Z",   # carimbo fictício da fixture
    "teams": [
        {
            "team_id": 2, "team_name": '3 peat… of pain 🫠',
            "sleeper_owner_id": '732411754436526080',
            "fa_budget": 3, # usable_draft_budget (D2)
            "keepers": [
                ('6786', 'CeeDee Lamb', 'WR', 59),
                ('6794', 'Justin Jefferson', 'WR', 52),
                ('6801', 'Tee Higgins', 'WR', 19),
                ('11635', 'Ladd McConkey', 'WR', 18),
                ('4137', 'James Conner', 'RB', 11),
                ('6790', "D'Andre Swift", 'RB', 10),
                ('8110', 'Jake Ferguson', 'TE', 6),
                ('6804', 'Jordan Love', 'QB', 4),
                ('4033', 'David Njoku', 'TE', 3),
                ('4227', 'Harrison Butker', 'K', 2),
                ('12512', 'Quinshon Judkins', 'RB', 2),
                ('BUF', 'Buffalo Bills', 'DEF', 1),
                ('9501', 'DeMario Douglas', 'WR', 1),
                ('DET', 'Detroit Lions', 'DEF', 1),
                ('12469', 'Dylan Sampson', 'RB', 1),
                ('12508', 'Jaxson Dart', 'QB', 1),
                ('8143', 'Jerome Ford', 'RB', 1),
                ('4018', 'Joe Mixon', 'RB', 1),
                ('11583', 'Jonathon Brooks', 'RB', 1),
                ('8408', 'Jordan Mason', 'RB', 1),
                ('11627', 'Troy Franklin', 'WR', 1),
            ],
        },
        {
            "team_id": 7, "team_name": 'AlexTheDawg',
            "sleeper_owner_id": '698015187109773312',
            "fa_budget": 11, # usable_draft_budget (D2)
            "keepers": [
                ('7547', 'Amon-Ra St. Brown', 'WR', 61),
                ('4034', 'Christian McCaffrey', 'RB', 59),
                ('5846', 'DK Metcalf', 'WR', 21),
                ('5892', 'David Montgomery', 'RB', 10),
                ('5012', 'Mark Andrews', 'TE', 10),
                ('1479', 'Keenan Allen', 'WR', 6),
                ('12533', 'Jacory Croskey-Merritt', 'RB', 4),
                ('12504', 'Kaleb Johnson', 'RB', 3),
                ('BAL', 'Baltimore Ravens', 'DEF', 2),
                ('10226', 'Andrei Iosivas', 'WR', 1),
                ('11563', 'Bo Nix', 'QB', 1),
                ('10219', 'Chris Rodriguez', 'RB', 1),
                ('3294', 'Dak Prescott', 'QB', 1),
                ('10236', 'Dalton Kincaid', 'TE', 1),
                ('11539', 'Jake Bates', 'K', 1),
                ('4219', 'Jeremy McNichols', 'RB', 1),
                ('4144', 'Jonnu Smith', 'TE', 1),
                ('12474', 'Woody Marks', 'RB', 1),
            ],
        },
        {
            "team_id": 5, "team_name": 'Cangaceiros da Colina',
            "sleeper_owner_id": '1130162144764506112',
            "fa_budget": 20, # usable_draft_budget (D2)
            "keepers": [
                ('11628', 'Marvin Harrison', 'WR', 50),
                ('8146', 'Garrett Wilson', 'WR', 48),
                ('11620', 'Rome Odunze', 'WR', 29),
                ('11624', 'Xavier Worthy', 'WR', 14),
                ('2449', 'Stefon Diggs', 'WR', 12),
                ('12489', 'RJ Harvey', 'RB', 7),
                ('11560', 'Caleb Williams', 'QB', 4),
                ('6806', 'J.K. Dobbins', 'RB', 2),
                ('5870', 'Daniel Jones', 'QB', 1),
                ('4066', 'Evan Engram', 'TE', 1),
                ('12506', 'Harold Fannin', 'TE', 1),
                ('12483', 'Jack Bech', 'WR', 1),
                ('11643', 'Jaylen Wright', 'RB', 1),
                ('11610', 'Malik Washington', 'WR', 1),
                ('12495', 'Ollie Gordon', 'RB', 1),
                ('12492', 'Pat Bryant', 'WR', 1),
                ('TB', 'Tampa Bay Buccaneers', 'DEF', 1),
                ('3678', 'Wil Lutz', 'K', 1),
            ],
        },
        {
            "team_id": 12, "team_name": 'ESPN FANTASY LEAGUE',
            "sleeper_owner_id": '1133818177651224576',
            "fa_budget": 49, # usable_draft_budget (D2)
            "keepers": [
                ('5859', 'A.J. Brown', 'WR', 47),
                ('5850', 'Josh Jacobs', 'RB', 22),
                ('9997', 'Zay Flowers', 'WR', 12),
                ('4199', 'Aaron Jones', 'RB', 10),
                ('7588', 'Javonte Williams', 'RB', 9),
                ('6803', 'Brandon Aiyuk', 'WR', 8),
                ('4892', 'Baker Mayfield', 'QB', 7),
                ('4037', 'Chris Godwin', 'WR', 7),
                ('5045', 'Courtland Sutton', 'WR', 6),
                ('6783', 'Jerry Jeudy', 'WR', 5),
                ('8136', 'Rachaad White', 'RB', 5),
                ('11786', 'Cam Little', 'K', 3),
                ('6865', 'Colby Parkinson', 'TE', 1),
                ('11435', 'Emanuel Wilson', 'RB', 1),
                ('12457', 'Jaydon Blue', 'RB', 1),
                ('7567', 'Kenny Gainwell', 'RB', 1),
                ('4993', 'Mike Gesicki', 'TE', 1),
                ('NE', 'New England Patriots', 'DEF', 1),
                ('8121', 'Romeo Doubs', 'WR', 1),
            ],
        },
        {
            "team_id": 3, "team_name": 'Fazenda Pederasta',
            "sleeper_owner_id": '1129822349391470592',
            "fa_budget": 135, # usable_draft_budget (D2)
            "keepers": [
                ('5872', 'Deebo Samuel', 'WR', 18),
                ('11637', 'Keon Coleman', 'WR', 13),
                ('4950', 'Christian Kirk', 'WR', 10),
                ('5947', 'Jakobi Meyers', 'WR', 3),
                ('8134', 'Khalil Shakir', 'WR', 3),
                ('9508', 'Tyjae Spears', 'RB', 2),
                ('96', 'Aaron Rodgers', 'QB', 1),
                ('8111', 'Cade Otton', 'TE', 1),
                ('CHI', 'Chicago Bears', 'DEF', 1),
                ('7839', 'Evan McPherson', 'K', 1),
                ('5970', 'Greg Dortch', 'WR', 1),
                ('11571', 'Isaiah Davis', 'RB', 1),
                ('8131', 'Isaiah Likely', 'TE', 1),
                ('12641', 'Jaylin Lane', 'WR', 1),
                ('12536', 'Jaylin Noel', 'WR', 1),
                ('9757', 'Kendre Miller', 'RB', 1),
                ('12498', 'Mason Taylor', 'TE', 1),
                ('12497', 'Tory Horton', 'WR', 1),
            ],
        },
        {
            "team_id": 6, "team_name": 'Miller Time!',
            "sleeper_owner_id": '1131747074137272320',
            "fa_budget": 0, # usable_draft_budget (D2)
            "keepers": [
                ('8155', 'Breece Hall', 'RB', 39),
                ('8144', 'Chris Olave', 'WR', 38),
                ('10859', 'Sam LaPorta', 'TE', 28),
                ('12507', 'Omarion Hampton', 'RB', 26),
                ('2216', 'Mike Evans', 'WR', 21),
                ('2133', 'Davante Adams', 'WR', 18),
                ('4039', 'Cooper Kupp', 'WR', 12),
                ('8183', 'Brock Purdy', 'QB', 2),
                ('12484', 'Jayden Higgins', 'WR', 2),
                ('8676', 'Rashid Shaheed', 'WR', 2),
                ('5095', 'Daniel Carlson', 'K', 1),
                ('DEN', 'Denver Broncos', 'DEF', 1),
                ('GB', 'Green Bay Packers', 'DEF', 1),
                ('7002', 'Juwan Johnson', 'TE', 1),
                ('9504', 'Kayshon Boutte', 'WR', 1),
                ('11647', 'Kimani Vidal', 'RB', 1),
                ('12534', 'Kyle Monangai', 'RB', 1),
                ('4177', 'Mack Hollins', 'WR', 1),
                ('7607', 'Michael Carter', 'RB', 1),
                ('10232', 'Michael Wilson', 'WR', 1),
                ('12509', "Tre' Harris", 'WR', 1),
                ('2374', 'Tyler Lockett', 'WR', 1),
            ],
        },
        {
            "team_id": 4, "team_name": 'mongoloides',
            "sleeper_owner_id": '205848303030505472',
            "fa_budget": 91, # usable_draft_budget (D2)
            "keepers": [
                ('11566', 'Jayden Daniels', 'QB', 28),
                ('6813', 'Jonathan Taylor', 'RB', 26),
                ('11584', 'Bucky Irving', 'RB', 10),
                ('9493', 'Puka Nacua', 'WR', 18),
                ('11632', 'Malik Nabers', 'WR', 9),
                ('4217', 'George Kittle', 'TE', 2),
                ('8259', 'Cameron Dicker', 'K', 1),
                ('HOU', 'Houston Texans', 'DEF', 1),
            ],
        },
        {
            "team_id": 1, "team_name": 'Pitbull do Samba',
            "sleeper_owner_id": '695859519976210432',
            "fa_budget": 85, # usable_draft_budget (D2)
            "keepers": [
                ('6904', 'Jalen Hurts', 'QB', 27),
                ('12529', 'TreVeyon Henderson', 'RB', 21),
                ('8137', 'George Pickens', 'WR', 16),
                ('9488', 'Jaxon Smith-Njigba', 'WR', 13),
                ('7594', 'Chuba Hubbard', 'RB', 11),
                ('7611', 'Rhamondre Stevenson', 'RB', 7),
                ('8126', "Wan'Dale Robinson", 'WR', 5),
                ('12713', 'Andy Borregales', 'K', 1),
                ('CLE', 'Cleveland Browns', 'DEF', 1),
                ('12517', 'Colston Loveland', 'TE', 1),
                ('11564', 'Drake Maye', 'QB', 1),
                ('11646', 'Jalen Coker', 'WR', 1),
                ('3163', 'Jared Goff', 'QB', 1),
                ('3451', "Ka'imi Fairbairn", 'K', 1),
                ('12519', 'Luther Burden', 'WR', 1),
                ('PIT', 'Pittsburgh Steelers', 'DEF', 1),
                ('9502', 'Tank Dell', 'WR', 1),
                ('11597', 'Theo Johnson', 'TE', 1),
                ('9484', 'Tucker Kraft', 'TE', 1),
                ('8132', 'Tyler Allgeier', 'RB', 1),
            ],
        },
        {
            "team_id": 11, "team_name": 'rafaelferreirap',
            "sleeper_owner_id": '1133812910268010496',
            "fa_budget": 124, # usable_draft_budget (D2)
            "keepers": [
                ('4046', 'Patrick Mahomes', 'QB', 22),
                ('12527', 'Ashton Jeanty', 'RB', 20),
                ('3321', 'Tyreek Hill', 'WR', 9),
                ('12526', 'Tetairoa McMillan', 'WR', 7),
                ('8130', 'Trey McBride', 'TE', 1),
                ('2747', 'Jason Myers', 'K', 1),
            ],
        },
        {
            "team_id": 9, "team_name": 'Tropa do Bicampeonato  🏆',
            "sleeper_owner_id": '695859970096328704',
            "fa_budget": 40, # usable_draft_budget (D2)
            "keepers": [
                ('4881', 'Lamar Jackson', 'QB', 40),
                ('9509', 'Bijan Robinson', 'RB', 35),
                ('8150', 'Kyren Williams', 'RB', 12),
                ('7564', "Ja'Marr Chase", 'WR', 30),
                ('8112', 'Drake London', 'WR', 14),
                ('7526', 'Jaylen Waddle', 'WR', 8),
                ('11604', 'Brock Bowers', 'TE', 5),
                ('9224', 'Chase Brown', 'RB', 2),
                ('11533', 'Brandon Aubrey', 'K', 1),
                ('LAR', 'Los Angeles Rams', 'DEF', 1),
            ],
        },
        {
            "team_id": 8, "team_name": 'Trust The Process',
            "sleeper_owner_id": '1126909140380569600',
            "fa_budget": 97, # usable_draft_budget (D2)
            "keepers": [
                ('4984', 'Josh Allen', 'QB', 30),
                ('7569', 'Nico Collins', 'WR', 30),
                ('5927', 'Terry McLaurin', 'WR', 13),
                ('12501', 'Matthew Golden', 'WR', 6),
                ('7090', 'Darnell Mooney', 'WR', 3),
                ('11625', 'Adonai Mitchell', 'WR', 2),
                ('12481', 'Cam Skattebo', 'RB', 2),
                ('5849', 'Kyler Murray', 'QB', 2),
                ('11655', 'Tyrone Tracy', 'RB', 2),
                ('11603', 'AJ Barner', 'TE', 1),
                ('12522', 'Cam Ward', 'QB', 1),
                ('11834', 'Devaughn Vele', 'WR', 1),
                ('6130', 'Devin Singletary', 'RB', 1),
                ('9486', 'Dontayvion Wicks', 'WR', 1),
                ('7049', 'Jauan Jennings', 'WR', 1),
                ('SEA', 'Seattle Seahawks', 'DEF', 1),
                ('12545', 'Tyler Shough', 'QB', 1),
                ('11626', 'Xavier Legette', 'WR', 1),
            ],
        },
        {
            "team_id": 10, "team_name": '🕯️🕯️ achane 🕯️🕯️ ',
            "sleeper_owner_id": '867557566065045504',
            "fa_budget": 94, # usable_draft_budget (D2)
            "keepers": [
                ('9226', "De'Von Achane", 'RB', 35),
                ('7525', 'DeVonta Smith', 'WR', 27),
                ('7553', 'Kyle Pitts', 'TE', 11),
                ('12530', 'Travis Hunter', 'WR', 8),
                ('12503', 'Isaiah Bond', 'WR', 4),
                ('11586', 'Blake Corum', 'RB', 3),
                ('12514', 'Emeka Egbuka', 'WR', 2),
                ('9754', 'Quentin Johnston', 'WR', 2),
                ('ATL', 'Atlanta Falcons', 'DEF', 1),
                ('12490', 'Bhayshul Tuten', 'RB', 1),
                ('12455', 'Brashard Smith', 'RB', 1),
                ('8167', 'Christian Watson', 'WR', 1),
                ('3214', 'Hunter Henry', 'TE', 1),
                ('IND', 'Indianapolis Colts', 'DEF', 1),
                ('421', 'Matthew Stafford', 'QB', 1),
                ('11559', 'Michael Penix', 'QB', 1),
                ('12493', 'Oronde Gadsden', 'TE', 1),
                ('12500', 'Quinn Ewers', 'QB', 1),
                ('12524', 'Shedeur Sanders', 'QB', 1),
                ('12485', 'Tez Johnson', 'WR', 1),
            ],
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURE B — a MESMA fixture A com TRÊS erros plantados, e só três.
# ══════════════════════════════════════════════════════════════════════════════
# Derivada por mutação explícita (não é uma segunda cópia congelada): assim não há
# como as duas divergirem por descuido, e o que muda fica legível numa tela.
#
#   1. SALÁRIO ALTERADO   — Patrick Mahomes na sheet do time da coluna 5: $22 → $17.
#      Esperado: 1× `salario_divergente`.
#   2. KEEPER REMOVIDO DA SHEET — Bucky Irving sai da sheet do time da coluna 4,
#      mas continua designado no board. Esperado: 1× `fora_da_sheet`.
#   3. TIME ERRADO        — Drake London, designado na coluna 3, é movido na SHEET
#      para o time da coluna 4. Esperado: 1× `time_errado` — e NENHUMA outra: o
#      cruzamento tem de ser reconhecido como UM erro, não como "ausente lá" +
#      "sobrando cá". É exatamente essa contagem que denuncia auditoria que inventa.

_MAHOMES = "4046"
_IRVING = "11584"
_LONDON = "8112"


def _clone(sheet):
    return {**sheet, "teams": [{**t, "keepers": list(t["keepers"])}
                               for t in sheet["teams"]]}


def _team_by_owner(sheet, owner_id):
    return next(t for t in sheet["teams"] if t["sleeper_owner_id"] == owner_id)


def _owner_of_column(board, roster_id):
    return next(c["owner_id"] for c in board["columns"]
                if c["roster_id"] == roster_id)


def build_sheet_b():
    """SHEET_A + os três erros conhecidos. Nada mais."""
    sheet = _clone(SHEET_A)
    t3 = _team_by_owner(sheet, _owner_of_column(BOARD_A, "3"))
    t4 = _team_by_owner(sheet, _owner_of_column(BOARD_A, "4"))
    t5 = _team_by_owner(sheet, _owner_of_column(BOARD_A, "5"))

    # (1) salário alterado
    t5["keepers"] = [(s, n, p, 17) if s == _MAHOMES else (s, n, p, v)
                     for s, n, p, v in t5["keepers"]]
    # (2) keeper removido da sheet (segue no board)
    t4["keepers"] = [k for k in t4["keepers"] if k[0] != _IRVING]
    # (3) keeper no time errado: sai da sheet da coluna 3, entra na da coluna 4
    london = next(k for k in t3["keepers"] if k[0] == _LONDON)
    t3["keepers"] = [k for k in t3["keepers"] if k[0] != _LONDON]
    t4["keepers"] = t4["keepers"] + [london]
    return sheet


SHEET_B = build_sheet_b()


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures pequenas e dirigidas — o que a A e a B não alcançam
# ══════════════════════════════════════════════════════════════════════════════

# (C) Classe 1 — keeper na sheet e AUSENTE do board, com o time populado.
# É a classe bloqueante, e a fixture B não a contém por construção (os três erros
# plantados são das classes 2, 3 e 4). Sem esta, a classe mais grave ficaria sem
# teste.
BOARD_C = {
    "league_id": "L", "league_name": "fixture", "draft_id": "D",
    "draft_status": "pre_draft", "draft_type": "auction", "rounds": 22, "budget": 200,
    "columns": [{"roster_id": "1", "owner_id": "OWNER-1"}],
    "designations": [
        {"roster_id": "1", "sleeper_player_id": "4881", "name": "Lamar Jackson",
         "position": "QB", "amount": "40"},
    ],
}

SHEET_C = {
    "revealed": True, "season": 2026, "lock_timestamp": None,
    "teams": [{
        "team_id": 1, "team_name": "Time C", "sleeper_owner_id": "OWNER-1",
        "fa_budget": 139,
        "keepers": [
            ("4881", "Lamar Jackson", "QB", 40),
            ("9509", "Bijan Robinson", "RB", 35),   # ← exposto: fora do board
        ],
    }],
}

# (D) Terreno REAL de 03/08: coluna com `owner_id` nulo (convite não aceito). A
# coluna não é atribuível a time nenhum, e o time correspondente do Manager fica
# sem coluna. Nenhum dos dois é divergência de transcrição — mas os dois impedem
# a abertura.
BOARD_SEM_OWNER = {
    "league_id": "L", "league_name": "fixture", "draft_id": "D",
    "draft_status": "pre_draft", "draft_type": "auction", "rounds": 22, "budget": 200,
    "columns": [
        {"roster_id": "1", "owner_id": "OWNER-1"},
        {"roster_id": "2", "owner_id": None},        # convite não aceito
    ],
    "designations": [
        {"roster_id": "1", "sleeper_player_id": "4881", "name": "Lamar Jackson",
         "position": "QB", "amount": "40"},
        {"roster_id": "2", "sleeper_player_id": "9509", "name": "Bijan Robinson",
         "position": "RB", "amount": "35"},         # designação órfã
    ],
}

SHEET_SEM_OWNER = {
    "revealed": True, "season": 2026, "lock_timestamp": None,
    "teams": [
        {"team_id": 1, "team_name": "Com coluna", "sleeper_owner_id": "OWNER-1",
         "fa_budget": 139, "keepers": [("4881", "Lamar Jackson", "QB", 40)]},
        {"team_id": 2, "team_name": "Sem coluna", "sleeper_owner_id": "OWNER-2",
         "fa_budget": 179, "keepers": [("7564", "Ja'Marr Chase", "WR", 30)]},
    ],
}

# (E) Keeper sem `sleeper_player_id` no Manager — identidade não resolvível. NÃO é
# divergência (é limite de insumo), e cair para nome está proibido pelo incidente
# "Brown". Note os dois Brown: é o caso que o fallback por nome estragaria.
SHEET_SEM_SID = {
    "revealed": True, "season": 2026, "lock_timestamp": None,
    "teams": [{
        "team_id": 1, "team_name": "Time E", "sleeper_owner_id": "OWNER-1",
        "fa_budget": 139,
        "keepers": [
            ("4881", "Lamar Jackson", "QB", 40),
            (None, "Chase Brown", "RB", 2),
            ("", "Amon-Ra St. Brown", "WR", 61),
        ],
    }],
}
