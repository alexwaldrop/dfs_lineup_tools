# Draftboard fields
NAME_FIELD = "player"
POS_FIELD = "position"
PROJ_POINTS_FIELD = "points_projected"
PROJ_POINTS_SD_FIELD = "sdPts_projected"
POINTS_FIELD = "points_actual"
SALARY_FIELD = "salary"
TEAM_FIELD = "team"
OPP_TEAM_FIELD = "opp"
HOME_TEAM_FIELD = "home_team"
REQUIRED_POS = {"QB": "QB",
                "RB": "RB",
                "WR": "WR",
                "TE": "TE",
                "D": "D"}

TEAM_MAP = {
    "Chicago": "Bears",
    "New York J": "Jets",
    "Jacksonville": "Jaguars",
    "New Orleans": "Saints",
    "New England": "Patriots",
    "Detroit": "Lions",
    "Carolina": "Panthers",
    "Green Bay": "Packers",
    "Dallas": "Cowboys",
    "Buffalo": "Bills",
    "Pittsburgh": "Steelers",
    "Cleveland": "Browns",
    "LA Rams": "Rams",
    "Tampa Bay": "Buccaneers",
    "Houston": "Texans",
    "San Francisco": "49ers",
    "Minnesota": "Vikings",
    "New York G": "Giants",
    "Cincinnati": "Bengals",
    "Washington": "Redskins",
    "LA Chargers": "Chargers",
    "Philadelphia": "Eagles",
    "Kansas City": "Chiefs",
    "Seattle": "Seahawks",
    "Miami": "Dolphins",
    "Indianapolis": "Colts",
    "Atlanta": "Falcons",
    "Tennessee": "Titans",
    "Denver": "Broncos",
    "Arizona": "Cardinals",
    "Baltimore": "Ravens",
    "Oakland": "Raiders",
    "San Diego": "Chargers",
    "Los Angeles": "Rams"
}

team_synonyms = {
    "CHI": ["chi"],
    "NE": ["nwe", "ne"],
    "TB": ["tb", "tam"],
    "KC": ["kan", "kc"],
    "GB": ["gb", "gnb"],
    "NYJ": ["nyj"],
    "JAX": ["jac", "jax"],
    "NO": ["no", "nor"],
    "DET": ["det"],
    "CAR": ["car"],
    "DAL": ["dal"],
    "BUF": ["buf"],
    "PIT": ["pit"],
    "CLE": ["cle"],
    "LAR": ["lar", "la"],
    "HOU": ["hou"],
    "SF": ["sf", "sfo"],
    "MIN": ["min"],
    "NYG": ["nyg"],
    "CIN": ["cin"],
    "WAS": ["was"],
    "LAC": ["lac", "sdg", "sd"],
    "PHI": ["phi"],
    "SEA": ["sea"],
    "MIA": ["mia"],
    "IND": ["ind"],
    "ATL": ["atl"],
    "TEN": ["ten"],
    "DEN": ["den"],
    "ARI": ["ari"],
    "BAL": ["bal"],
    "OAK": ["oak"],
                 }

