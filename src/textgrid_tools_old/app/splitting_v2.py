from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import split_intervals
from textgrid_tools_cli.common_v2 import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_encoding_argument, add_maxtaskperchild_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_tiers_argument, parse_positive_integer)


def get_splitting_v2_parser(parser: ArgumentParser):
  parser.description = "This command splits the content of a tier."
  add_directory_argument(parser, "directory containing the grid files which should be modified")
  add_tiers_argument(parser, "tiers which should be split")
  parser.add_argument('--symbol', type=str, help="split on this symbol", default=" ")
  parser.add_argument("--keep", action="store_true",
                      help="keep the split symbol in a separate interval")

  parser.add_argument("--chunk", type=parse_positive_integer,
                      help="amount of files to process at a time; defaults to all items if not defined", default=None)
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  # add_log_argument(parser)
  return app_split_intervals


def app_split_intervals(ns: Namespace) -> ExecutionResult:
  method = partial(
    split_intervals,
    symbol=ns.symbol,
    keep=ns.keep,
    tier_names=ns.tiers,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.log, ns.chunk)
