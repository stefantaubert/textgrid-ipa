from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import map_tier
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tier_argument, parse_non_empty_or_whitespace)


def get_mapping_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals on default."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be mapped")
  parser.add_argument("target_tiers", metavar="target-tiers",
                      type=parse_non_empty_or_whitespace, nargs="+", help="tiers to which the content should be mapped", action=ConvertToOrderedSetAction)
  parser.add_argument("--include-pauses", action="store_true",
                      help="include mapping from and to pause intervals, i.e., those which contain nothing or only whitespace")
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_map_tier


def app_map_tier(ns: Namespace) -> ExecutionResult:
  method = partial(
    map_tier,
    include_pauses=ns.include_pauses,
    target_tier_names=ns.target_tiers,
    tier_name=ns.tier,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild)
