import logging
import re
from fuzzywuzzy import fuzz
import pandas as pd

from utils import DFSException
import constants as cols

def clean_string_for_file_name(value):
    clean_val = re.sub('[^\w\s-]', '', value).strip().lower()
    clean_val = re.sub('[-\s]+', '-', clean_val)
    return clean_val


def normalize_string(value):
    clean_val = re.sub('[^\w\s-]', '', value).strip().lower()
    return clean_val


def match_ref_player(name, pos, team, reference_names, reference_pos, reference_teams, match_threshold=90, min_match_threshold=70):
    # Find reference name for a player to harmonize names across two datasets

    # Check to see if reference names, pos are same length
    if len(reference_names) != len(reference_pos) or len(reference_names) != len(reference_teams):
        err_msg = "Different number of reference names ({0}), " \
                  "positions ({1}), and teams({2})!".format(len(reference_names),
                                                            len(reference_pos),
                                                            len(reference_teams))
        logging.error(err_msg)
        raise DFSException(err_msg)

    # Normalize player names to remove differences in cases and punctuation
    norm_name = normalize_string(name)

    # Generate normalized list of reference players
    norm_reference_names = {}
    for i in range(len(reference_names)):
        norm_ref_name = normalize_string(reference_names[i])
        if norm_ref_name in norm_reference_names:
            norm_reference_names[norm_ref_name].append((reference_names[i], reference_pos[i], reference_teams[i]))
        else:
            norm_reference_names[norm_ref_name] = [(reference_names[i], reference_pos[i], reference_teams[i])]

    if norm_name in norm_reference_names:
        for player in norm_reference_names[norm_name]:
            if pos == player[1] and team == player[2]:
                # Return name if name matches and same position
                if name not in reference_names:
                    print(norm_name)
                    logging.debug("Normalizing resolved names: {0} | {1}".format(norm_name,
                                                                                 player[0]))
                return player[0]

        # Return none if can't find player match
        logging.warning("Player name matched but we disagree on position and/or team:\n"
                        "Name: {0} ({1}, {2})".format(name,pos,team))
        return None

    elif norm_name not in norm_reference_names:
        # Do fuzzy matching to see if name closely matches another name
        # Store results in case none exceed fuzzy match threshold and human input needed
        match_results = []
        for norm_ref_name in norm_reference_names:
            match_ratio = fuzz.partial_ratio(norm_name, norm_ref_name)

            # Return name if fuzzy match is over threshold
            if match_ratio > match_threshold:
                for player in norm_reference_names[norm_ref_name]:
                    if player[1] == pos and player[2] == team:
                        print(match_ratio)
                        logging.warning("Fuzzy match resolved names: {0} | {1}".format(norm_name,
                                                                                       norm_reference_names[norm_ref_name][0]))
                        return player[0]

                # Return none if can't find player match with same team/pos
                logging.warning("Player name matched but we disagree on position and/or team:\n"
                                "Name: {0} ({1}, {2})".format(name, pos, team))
                return None

            # Otherwise add match results to list of names
            match_results.append((norm_ref_name, match_ratio))

    # If no matches found > match threshold, ask user if any matches are correct
    match_results = sorted(match_results, key=lambda x: x[1], reverse=True)
    for match_result in match_results:
        # Break loop and return if the next closest match is below minimum match threshold
        if match_result[1] < min_match_threshold:
            logging.warning("Unable to match player: {0}".format(name))
            return None

        for player in norm_reference_names[match_result[0]]:
            # Ask for user input to determine whether match is correct
            ref_player = player[0]
            ref_pos    = player[1]
            ref_team   = player[2]
            is_match = None
            while is_match not in ["0", "1"]:
                is_match = input("Is this the same player (match score: {0})? "
                                 "{0} ({1}, {2}) and {3} ({4}, {5}) [0=No, 1=Yes]: ".format(match_result[1],
                                                                                            name,
                                                                                            pos,
                                                                                            team,
                                                                                            ref_player,
                                                                                            ref_pos,
                                                                                            ref_team))
            # Return player name if user thinks it's a match
            if is_match == "1":
                return ref_player

    # If user loops through all potential matches and doesn't agree, return None
    logging.warning("Unable to match player: {0}".format(name))
    return None


def harmonize_player_names(data, ref_data, match_threshold=90, min_match_threshold=75):
    # Apply fuzzing matching
    old_data = data.copy()

    def harm_names(row):
        return match_ref_player(row[cols.NAME_FIELD],
                                row[cols.POS_FIELD],
                                row[cols.TEAM_FIELD],
                                ref_data[cols.NAME_FIELD].tolist(),
                                ref_data[cols.POS_FIELD].tolist(),
                                ref_data[cols.TEAM_FIELD].tolist(),
                                match_threshold,
                                min_match_threshold)

    data[cols.NAME_FIELD] = data.apply(harm_names, axis=1)

    # Remove players that weren't found in reference dataset
    dropped_players = old_data[pd.isnull(data[cols.NAME_FIELD])]
    if len(dropped_players):
        logging.warning("Players not matching player in reference data: \n{0}".format(dropped_players))

    return data[~pd.isnull(data[cols.NAME_FIELD])].copy()


def merge_datasets(data, ref_data):

    # Harmonize data so it's in same team/player namespace as reference dataset
    data = harmonize_player_names(data, ref_data)

    # Merge dataframes
    merged_data = ref_data.merge(data, how="inner", on=[cols.NAME_FIELD, cols.TEAM_FIELD, cols.POS_FIELD])
    return merged_data


class PlayerDataImporter(object):
    REQUIRED_COLS = []

    def __init__(self, source=None):
        self.data = self.get_data(source)

    def get_data(self, source):
        # Read data
        data = self.read_data(source)

        # Do any pre-processing to make sure data is in a good form
        data = self.preprocess_data(data)

        # Check to make sure player name, position, and team columns present
        # Minimal information required for player data import
        self.validate_cols(data, required_cols=[cols.NAME_FIELD, cols.POS_FIELD, cols.TEAM_FIELD])

        # Check to make sure additional required columns specific to import source are present
        self.validate_cols(data, required_cols=self.REQUIRED_COLS)

        # Check to make sure required positions are present
        self.validate_pos(data)

        # Harmonize team names
        data = self.harmonize_teams(data)

        # Drop duplicate players
        data = data.drop_duplicates(subset=[cols.NAME_FIELD, cols.POS_FIELD, cols.TEAM_FIELD])

        # Post-process
        data = self.postprocess_data(data)

        return data


    @staticmethod
    def validate_cols(data, required_cols):
        # Check and raise errors if required columns not present in dataframe
        if not isinstance(required_cols, list):
            required_cols = [required_cols]

        errors = False
        for required_col in required_cols:
            if required_col not in data.columns:
                logging.error("Required column missing from data frame: {0}".format(required_col))
                errors = True

        if errors:
            err_msg = "Data missing required columns!"
            logging.error(err_msg)
            raise DFSException(err_msg)

    @staticmethod
    def validate_pos(data):
        # Check required columns present
        errors = False

        # Convert position column to uppercase
        data[cols.POS_FIELD] = data[cols.POS_FIELD].str.upper()

        # Check to make sure POS column contains all RB, WR, TE, QB
        pos_available = [x.upper() for x in set(list(data[cols.POS_FIELD]))]

        for pos in cols.REQUIRED_POS:
            if pos not in pos_available:
                logging.error("Missing players of position type: {0}".format(pos))
                errors = True

        # Check to make sure Pos column contains only RB, WR, TE, QB
        for pos in pos_available:
            if pos not in cols.REQUIRED_POS:
                logging.error("One or more players contains invalid position: {0}".format(pos))
                errors = True

        if errors:
            raise IOError("Improperly formatted draft board! See above errors")

    def read_data(self, source):
        if source.endswith("csv"):
            return pd.read_csv(source)
        elif source.endswith(".xlsx"):
            return pd.read_excel(source)
        else:
            logging.error("Unable to detect input source format")
            raise IOError("Unable to import data from source: {0}\nFile handle must be .csv or .xlsx!".format(source))

    def harmonize_team(self, team_name):
        if team_name.upper() in cols.team_synonyms:
            #logging.debug("Found team exactly in team synonym list {0}".format(team_name.upper()))
            return team_name.upper()
        for ref_team_name, team_syns in cols.team_synonyms.items():
            team_syns = [team_syn.lower() for team_syn in team_syns]
            if team_name.lower() in team_syns:
                logging.debug("Used synonym list to match team {0} to {1}".format(team_name, ref_team_name))
                return ref_team_name
        return None

    def harmonize_teams(self, data, team_col=cols.TEAM_FIELD):
        team_map = {team: self.harmonize_team(team) for team in data[team_col].unique()}
        for team in team_map:
            if team is None:
                logging.error("Unable to map team '{0}' to reference teams!".format(team))
                raise DFSException("Unable to harmonize teams from input source!")

        # Map team names to reference name
        data[team_col] = data[team_col].map(team_map)
        return data

    def preprocess_data(self, data):
        pass

    def postprocess_data(self, data):
        return data


class DKResultsImporter(PlayerDataImporter):
    REQUIRED_COLS = [cols.OPP_TEAM_FIELD, cols.POINTS_FIELD, cols.SALARY_FIELD]

    def __init__(self, source):
         super().__init__(source)

    def preprocess_data(self, data):

        # Make sure columns are the same
        assert "_".join(data.columns) == "_".join(["Week", "Year", "GID", "Name", "Pos", "Team",
                                                   "h/a", "Oppt", "DK points", "DK salary"]), \
            "Unexpected columns for DraftKings Importer!"

        # Rename columns to standard
        data = data[["Name", "Pos", "Team", "Oppt", "h/a", "DK points", "DK salary"]].copy()
        data.columns = [cols.NAME_FIELD,cols.POS_FIELD, cols.TEAM_FIELD,
                        cols.OPP_TEAM_FIELD, cols.HOME_TEAM_FIELD, cols.POINTS_FIELD, cols.SALARY_FIELD]

        # Replace def with D in pos field
        data[cols.POS_FIELD] = data[cols.POS_FIELD].str.replace("Def", cols.REQUIRED_POS["D"])

        # Split out player names from commas
        def fix_player_name(name):
            name = [x.strip() for x in name.split(",")]
            if len(name) > 1:
                # Return player names in firstname lastname order
                return " ".join([name[1], name[0]])
            else:
                # Return team defense by team name
                name = name[0].replace("Defense", "").strip()
                return cols.TEAM_MAP[name]

        data[cols.NAME_FIELD] = data[cols.NAME_FIELD].map(fix_player_name)

        def home_away_to_boolean(home_away):
            if home_away == "h":
                return True
            return False

        # Convert home/away to boolean field
        data[cols.HOME_TEAM_FIELD] = data[cols.HOME_TEAM_FIELD].map(home_away_to_boolean)

        # Remove any players with null salaries
        data = data[~pd.isnull(data[cols.SALARY_FIELD])]
        return data

    def postprocess_data(self, data):
        return self.harmonize_teams(data, team_col=cols.OPP_TEAM_FIELD)


class DKPriceImporter(PlayerDataImporter):
    REQUIRED_COLS = [cols.OPP_TEAM_FIELD, cols.POINTS_FIELD, cols.SALARY_FIELD]

    def __init__(self, source):
         super().__init__(source)

    def preprocess_data(self, data):

        # Make sure columns are the same
        assert "_".join(data.columns) == "_".join(["Position", "Name + ID", "Name", "ID", "Roster Position", "Salary",
                                                   "Game Info", "TeamAbbrev", "AvgPointsPerGame"]), \
            "Unexpected columns for DraftKings Prices Importer!"

        # Rename columns to standard
        data = data[["Name", "Roster Position", "Game Info", "TeamAbbrev", "AvgPointsPerGame", "Salary"]].copy()

        # Parse out home and opponent teams
        def get_opp_team(row):
            player_team = row["TeamAbbrev"]
            field = row["Game Info"]
            for team in field.split()[0].split("@"):
                if team != player_team:
                    return team

        data[cols.OPP_TEAM_FIELD] = data.apply(get_opp_team, axis=1)
        data = data[["Name", "Roster Position", "TeamAbbrev", cols.OPP_TEAM_FIELD, "AvgPointsPerGame", "Salary"]].copy()
        data.columns = [cols.NAME_FIELD,cols.POS_FIELD, cols.TEAM_FIELD,
                        cols.OPP_TEAM_FIELD, cols.POINTS_FIELD, cols.SALARY_FIELD]

        # Replace DST with D in pos field
        def fix_pos(field):
            return field.split("/")[0]

        data[cols.POS_FIELD] = data[cols.POS_FIELD].map(fix_pos)
        data[cols.POS_FIELD] = data[cols.POS_FIELD].str.replace("DST", cols.REQUIRED_POS["D"])
        return data

    def postprocess_data(self, data):
        return self.harmonize_teams(data, team_col=cols.OPP_TEAM_FIELD)


class FFAProjectionsImporter(PlayerDataImporter):
    REQUIRED_COLS = [cols.PROJ_POINTS_FIELD, cols.PROJ_POINTS_SD_FIELD]

    def __init__(self, source):
        super().__init__(source)

    def preprocess_data(self, data):
        assert "_".join(data.columns[0:5]) == "_".join(["playerId", "player", "team", "position", "age"]), \
            "Unexpected columns for FFA projections Importer!"

        # Remove players with missing data, free agents, and players that didn't end up playing that week
        data = data[~pd.isnull(data.points)]
        data = data[~pd.isnull(data.sdPts)]
        data = data[data.team != "FA"]

        if "actualPoints" in data.columns:
            data = data[~pd.isnull(data.actualPoints)]

        # Subset to only informative columns and standardize column names
        data = data[["player", "team", "position", "points", "sdPts", "tier"]].copy()
        data.columns = [cols.NAME_FIELD, cols.TEAM_FIELD, cols.POS_FIELD,
                        cols.PROJ_POINTS_FIELD, cols.PROJ_POINTS_SD_FIELD, "tier"]

        # Replace DST with D in pos field
        data[cols.POS_FIELD] = data[cols.POS_FIELD].str.replace("DST", cols.REQUIRED_POS["D"])

        # Remove players not in required positions
        data = data[data[cols.POS_FIELD].isin(cols.REQUIRED_POS.keys())]

        # Specific rule for Ty Montgomery because I'm lazy
        data[cols.POS_FIELD].loc[data[cols.NAME_FIELD] == "Ty Montgomery"] = "RB"

        # Remove players with no projections
        data = data[~pd.isnull(data[cols.PROJ_POINTS_SD_FIELD])]
        data = data[~pd.isnull(data[cols.PROJ_POINTS_FIELD])]
        data = data[data[cols.TEAM_FIELD] != "FA"]
        return data
