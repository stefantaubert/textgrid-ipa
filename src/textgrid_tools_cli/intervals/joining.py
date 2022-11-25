from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import join_intervals
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument)
from textgrid_tools_cli.intervals.common import add_join_empty_argument, add_join_with_argument


def get_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  add_join_with_argument(parser)
  add_join_empty_argument(parser)
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_join_intervals


def app_join_intervals(ns: Namespace) -> ExecutionResult:
  method = partial(
    join_intervals,
    tier_names=ns.tiers,
    join_with=ns.join_with,
    ignore_empty=not ns.join_empty,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
