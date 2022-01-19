from ordered_set import OrderedSet
from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional, Set

from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (ConvertToOrderedSetAction,
                                       add_chunksize_argument,
                                       add_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_tier_argument,
                                       parse_non_empty_or_whitespace)
from textgrid_tools.core import map_tier


def get_mapping_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals on default."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be mapped")
  parser.add_argument("target_tiers", metavar="target-tiers",
                      type=parse_non_empty_or_whitespace, nargs="+", help="tiers to which the content should be mapped", action=ConvertToOrderedSetAction)
  parser.add_argument("--include-pauses", action="store_true",
                      help="include mapping from and to pause intervals, i.e., those which contain nothing or only whitespace")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_map_tier


def app_map_tier(directory: Path, tier: str, target_tiers: OrderedSet[str], include_pauses: bool, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    map_tier,
    include_pauses=include_pauses,
    target_tier_names=target_tiers,
    tier_name=tier,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
