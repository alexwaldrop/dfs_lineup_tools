import argparse
import logging
import os
import pandas as pd
import numpy as np
import yaml
import json

import utils
import data_import as imp

def configure_argparser(argparser_obj):

    def file_type(arg_string):
        """
        This function check both the existance of input file and the file size
        :param arg_string: file name as string
        :return: file name as string
        """
        if not os.path.exists(arg_string):
            err_msg = "%s does not exist! " \
                      "Please provide a valid file!" % arg_string
            raise argparse.ArgumentTypeError(err_msg)

        return arg_string

    # Path to projections spreadsheet
    argparser_obj.add_argument("--harm",
                               action="store",
                               type=file_type,
                               dest="harm_file",
                               required=True,
                               help="Path to harmonized player spreadsheet")

    # Path to league config
    argparser_obj.add_argument("--lines",
                               action="store",
                               type=file_type,
                               dest="lines_file",
                               required=True,
                               help="Path to vegas lines for the wee")

    # Path to output file
    argparser_obj.add_argument("--out",
                               action="store",
                               type=str,
                               dest="output_file",
                               required=True,
                               help="Path to output file")

    # Verbosity level
    argparser_obj.add_argument("-v",
                               action='count',
                               dest='verbosity_level',
                               required=False,
                               default=0,
                               help="Increase verbosity of the program."
                                    "Multiple -v's increase the verbosity level:\n"
                                    "0 = Errors\n"
                                    "1 = Errors + Warnings\n"
                                    "2 = Errors + Warnings + Info\n"
                                    "3 = Errors + Warnings + Info + Debug")

def main():
    # Configure argparser
    argparser = argparse.ArgumentParser(prog="append_vegas_lines.py")
    configure_argparser(argparser)

    # Parse the arguments
    args = argparser.parse_args()

    # Configure logging
    utils.configure_logging(args.verbosity_level)

    # Get names of input/output files
    harm_file   = args.harm_file
    lines_file    = args.lines_file
    out_file    = args.output_file

    logging.info("Reading current draft kings prices")
    dk_df = imp.DKPriceImporter(dfs_file)

    logging.info("Reading FFA Projections...")
    proj_df = imp.FFAProjectionsImporter(proj_file)

    print(proj_df.data.head(25))
    print()
    print(dk_df.data.head(25))

    # Merge the two datasets
    data = imp.merge_datasets(proj_df.data, ref_data=dk_df.data)

    # Write to output file
    data.to_csv(out_file, index=False)

if __name__ == "__main__":
    main()