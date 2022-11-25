from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import move_tier
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tier_argument, parse_positive_integer)


def get_moving_parser(parser: ArgumentParser):
  parser.description = "This commands moves a tier to another position in the grid."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be moved")
  parser.add_argument("position", type=parse_positive_integer, metavar="POSITION",
                      help="move tier to this position (1 = first tier)")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_move_tier


def app_move_tier(ns: Namespace) -> ExecutionResult:
  method = partial(
    move_tier,
    tier_name=ns.tier,
    position_one_based=ns.position,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
