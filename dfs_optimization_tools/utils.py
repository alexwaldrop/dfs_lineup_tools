import sys
import logging
from statistics import mean
import re

import constants as cols
#import dfs_optimization_tools.constants as cols
from fuzzywuzzy import fuzz


class DFSException(BaseException):
    # Define custom exception to use everywhere
    pass


def configure_logging(verbosity):
    # Setting the format of the logs
    FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"

    # Configuring the logging system to the lowest level
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, stream=sys.stderr)

    # Defining the ANSI Escape characters
    BOLD = '\033[1m'
    DEBUG = '\033[92m'
    INFO = '\033[94m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    END = '\033[0m'

    # Coloring the log levels
    if sys.stderr.isatty():
        logging.addLevelName(logging.ERROR, "%s%s%s%s%s" % (BOLD, ERROR, "FD_TOOLS_ERROR", END, END))
        logging.addLevelName(logging.WARNING, "%s%s%s%s%s" % (BOLD, WARNING, "FD_TOOLS_WARNING", END, END))
        logging.addLevelName(logging.INFO, "%s%s%s%s%s" % (BOLD, INFO, "FD_TOOLS_INFO", END, END))
        logging.addLevelName(logging.DEBUG, "%s%s%s%s%s" % (BOLD, DEBUG, "FD_TOOLS_DEBUG", END, END))
    else:
        logging.addLevelName(logging.ERROR, "FD_TOOLS_ERROR")
        logging.addLevelName(logging.WARNING, "FD_TOOLS_WARNING")
        logging.addLevelName(logging.INFO, "FD_TOOLS_INFO")
        logging.addLevelName(logging.DEBUG, "FD_TOOLS_DEBUG")

    # Setting the level of the logs
    level = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG][verbosity]
    logging.getLogger().setLevel(level)

def clean_string_for_file_name(value):
    clean_val = re.sub('[^\w\s-]', '', value).strip().lower()
    clean_val = re.sub('[-\s]+', '-', clean_val)
    return clean_val


def check_df_columns(df, required_cols, err_msg=None):
    # Check and raise errors if required columns not present in dataframe
    if not isinstance(required_cols, list):
        required_cols = [required_cols]

    errors = False
    for required_col in required_cols:
        if required_col not in df.columns:
            logging.error("Required column missing from data frame: {0}".format(required_col))
            errors = True

    if errors:
        err_msg = "Dataframe missing required columns!" if err_msg is None else err_msg
        logging.error(err_msg)
        raise DFSException(err_msg)


def drop_duplicates_and_warn(input_df, id_col, warn_msg=None):
    # De-duplicates with warning of items that will be deduplicated
    duplicates = input_df[id_col].value_counts()
    duplicates = duplicates[duplicates > 1]
    if len(duplicates):
        base_warn = "Dropping all but first duplicates: \n{0}".format(input_df[input_df[id_col].isin(duplicates.index)])
        warn_msg = base_warn if warn_msg is None else "{0}\n".format(warn_msg)
        logging.warning(warn_msg)
        input_df = input_df.drop_duplicates(subset=id_col)
    # Remove duplicate merge key
    return input_df


def normalize_string(value):
    clean_val = re.sub('[^\w\s-]', '', value).strip().lower()
    return clean_val


def match_reference_player_name(name, pos, reference_names, reference_pos, match_threshold=90, min_match_threshold=75):
    # Find reference name for a player to harmonize names across two datasets

    # Check to see if reference names, pos are same length
    if len(reference_names) != len(reference_pos):
        err_msg = "Different number of reference names ({0}) " \
                  "and positions ({1})!".format(len(reference_names), len(reference_pos))
        logging.error(err_msg)
        raise DFSException(err_msg)

    # Normalize player names to remove differences in cases and punctuation
    norm_name = normalize_string(name)
    norm_reference_names = {normalize_string(reference_names[i]): (reference_names[i], reference_pos[i]) for i in range(len(reference_names))}

    if norm_name in norm_reference_names and pos == norm_reference_names[norm_name][1]:
        # Return name if name matches and same position
        if name not in reference_names:
            print(norm_name)
            logging.debug("Normalizing resolved names: {0} | {1}".format(norm_name,
                                                                         norm_reference_names[norm_name][0]))
        return norm_reference_names[norm_name][0]

    elif norm_name not in norm_reference_names:
        # Do fuzzy matching to see if name closely matches another name
        # Store results in case none exceed fuzzy match threshold and human input needed
        match_results = []
        for norm_ref_name in norm_reference_names:
            match_ratio = fuzz.partial_ratio(norm_name, norm_ref_name)

            # Return name if fuzzy match is over threshold
            if match_ratio > match_threshold and norm_reference_names[norm_ref_name][1] == pos:
                print(match_ratio)
                logging.warning("Fuzzy match resolved names: {0} | {1}".format(norm_name,
                                                                               norm_reference_names[norm_ref_name][0]))
                return norm_reference_names[norm_ref_name][0]

            # Otherwise add match results to list of names
            match_results.append((norm_ref_name, match_ratio))

    elif norm_name in norm_reference_names and pos != norm_reference_names[norm_name][1]:
        # Raise error if there's a player that matches but for different position. That shouldn't happen.
        logging.error("Player name matched but we disagree on position:\n"
                      "Name: {0} ({1})\n"
                      "Ref Name: {2} ({3})".format(name,
                                                   pos,
                                                   norm_reference_names[norm_name][0],
                                                   norm_reference_names[norm_name][1]))
        raise DFSException("Player name matches but positional disagreement between "
                             "projections/ADP. See log for details.")

    # If no matches found > match threshold, ask user if any matches are correct
    match_results = sorted(match_results, key=lambda x: x[1], reverse=True)
    for match_result in match_results:
        # Break loop and return if the next closest match is below minimum match threshold
        if match_result[1] < min_match_threshold:
            return None

        # Ask for user input to determine whether match is correct
        ref_player = norm_reference_names[match_result[0]][0]
        ref_pos    = norm_reference_names[match_result[0]][1]
        is_match = None
        while is_match not in ["0", "1"]:
            is_match = input("Is this the same player (match score: {0})? "
                             "{0} ({1}) and {2} ({3}) [0=No, 1=Yes]: ".format(match_result[1],
                                                                              name,
                                                                              pos,
                                                                              ref_player,
                                                                              ref_pos))
        # Return player name if user thinks it's a match
        if is_match == "1":
            return ref_player

    # If user loops through all potential matches and doesn't agree, return None
    return None