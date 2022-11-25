from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import split_intervals
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument)


def get_splitting_parser(parser: ArgumentParser):
  parser.description = "This command splits the content of a tier."
  add_directory_argument(parser, "directory containing the grid files which should be modified")
  add_tiers_argument(parser, "tiers which should be split")
  parser.add_argument('symbol', type=str, help="split on this symbol", metavar="SPLIT-SYMBOL")
  parser.add_argument("--keep", action="store_true",
                      help="keep the split symbol in a separate interval")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_split_intervals


def app_split_intervals(ns: Namespace) -> ExecutionResult:
  method = partial(
    split_intervals,
    symbol=ns.symbol,
    keep=ns.keep,
    tier_names=ns.tiers,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
