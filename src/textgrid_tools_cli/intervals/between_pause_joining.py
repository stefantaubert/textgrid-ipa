from argparse import ArgumentParser, Namespace
from functools import partial
from math import inf

from textgrid_tools import join_intervals_between_pauses
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument, parse_non_negative_float)
from textgrid_tools_cli.intervals.common import add_join_empty_argument, add_join_with_argument


def get_between_pause_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent non-silence intervals (LEGACY, please use join-between-marks)."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  parser.add_argument('--pause', type=parse_non_negative_float, metavar="SECONDS",
                      help="until duration (in seconds) of adjacent pauses that should be merged, i.e., value \'0\' means only adjacent non-pause intervals are joined and \'inf\' means all intervals are joined", default=inf)
  add_join_with_argument(parser)
  add_join_empty_argument(parser)
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_join_intervals_between_pauses


def app_join_intervals_between_pauses(ns: Namespace) -> ExecutionResult:
  method = partial(
    join_intervals_between_pauses,
    pause=ns.pause,
    tier_names=ns.tiers,
    join_with=ns.join_with,
    ignore_empty=not ns.join_empty,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
