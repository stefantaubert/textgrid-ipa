from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import join_intervals_on_durations
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument, parse_positive_float)
from textgrid_tools_cli.intervals.common import add_join_empty_argument, add_join_with_argument


def get_duration_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals to intervals with a maximum duration."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  parser.add_argument("--duration", metavar="SECONDS", type=parse_positive_float,
                      help="maximum duration until intervals should be joined (in seconds)", default=10)
  parser.add_argument("--include-pauses", action="store_true",
                      help="include pauses at the beginning/ending while joining")
  add_join_with_argument(parser)
  add_join_empty_argument(parser)
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_join_intervals_on_durations


def app_join_intervals_on_durations(ns: Namespace) -> ExecutionResult:
  # print(ns.tiers)
  method = partial(
    join_intervals_on_durations,
    tier_names=ns.tiers,
    include_empty_intervals=ns.include_pauses,
    max_duration_s=ns.duration,
    join_with=ns.join_with,
    ignore_empty=not ns.join_empty,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
