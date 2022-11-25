from argparse import ArgumentParser, Namespace
from functools import partial

from ordered_set import OrderedSet

from textgrid_tools import map_tier
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_dry_run_argument,
                                       add_encoding_argument, add_maxtaskperchild_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tier_argument,
                                       parse_non_empty_or_whitespace)


def get_mapping_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring empty intervals on default."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be mapped")
  parser.add_argument("target_tiers", metavar="TARGET-TIER",
                      type=parse_non_empty_or_whitespace, nargs="+", help="tiers to which the content should be mapped", action=ConvertToOrderedSetAction)
  parser.add_argument("--filter-from", type=str, nargs="*", action=ConvertToOrderedSetAction,
                      metavar="FILTER-FROM", default=OrderedSet([""]), help="skip intervals in TIER that contain this mark")
  parser.add_argument("--filter-from-mode", type=str, choices=["consider", "ignore"],
                      default="ignore", help="consider only/ignore all marks from FILTER-FROM")
  parser.add_argument("--filter-to", type=str, nargs="*", action=ConvertToOrderedSetAction, metavar="FILTER-TO",
                      default=OrderedSet([""]), help="skip intervals in TARGET-TIER's that contain this mark")
  parser.add_argument("--filter-to-mode", type=str, choices=["consider", "ignore"],
                      default="ignore", help="consider only/ignore all marks from FILTER-TO")
  parser.add_argument("--mode", type=str, choices=["replace", "prepend", "append"],
                      help="defines how the marks should be mapped", default="replace")
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_map_tier


def app_map_tier(ns: Namespace) -> ExecutionResult:
  method = partial(
    map_tier,
    target_tier_names=ns.target_tiers,
    tier_name=ns.tier,
    mode=ns.mode,
    filter_from=ns.filter_from,
    filter_from_mode=ns.filter_from_mode,
    filter_to=ns.filter_to,
    filter_to_mode=ns.filter_to_mode,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
