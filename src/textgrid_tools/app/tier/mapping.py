from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional, Set

from textgrid_tools.app.common import process_grids
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.core import map_tier


def get_mapping_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals."
  add_grid_directory_argument(parser)
  parser.add_argument("tier", metavar="tier", type=str,
                      help="tier which should be mapped")
  parser.add_argument("target_tiers", metavar="target-tiers",
                      type=str, nargs="+", help="tiers to which the content should be mapped")
  parser.add_argument("--include-pauses", action="store_true",
                      help="include mapping from and to pause intervals, i.e., those which contain nothing or only whitespace")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_map_tier


def app_map_tier(directory: Path, tier: str, target_tiers: Set[str], include_pauses: bool, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    map_tier,
    include_pauses=include_pauses,
    target_tier_names=set(target_tiers),
    tier_name=tier,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
