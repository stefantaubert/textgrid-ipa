from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from ordered_set import OrderedSet
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import clone_tier
from textgrid_tools.core.globals import ExecutionResult


def init_files_clone_tier_parser(parser: ArgumentParser):
  parser.description = "This command clones a tier."

  add_grid_directory_argument(parser)
  parser.add_argument("tier", type=str, metavar="tier",
                      help="tier which should be cloned")
  parser.add_argument("tiers", type=str, nargs="+", metavar="tiers",
                      help="tiers to clone to")

  parser.add_argument("--ignore-marks", action="store_true",
                      help="ignore marks while cloning")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_clone_tier


def app_clone_tier(directory: Path, tier: str, tiers: List[str], n_digits: int, output_directory: Optional[Path], ignore_marks: bool, overwrite: bool) -> ExecutionResult:
  method = partial(
    clone_tier,
    tier_name=tier,
    output_tier_names=OrderedSet(tiers),
    ignore_marks=ignore_marks,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
