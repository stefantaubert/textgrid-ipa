from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import fix_interval_boundaries


def init_files_fix_boundaries_parser(parser: ArgumentParser):
  parser.description = "This command set the closest boundaries of tiers to those of a reference tier."
  add_grid_directory_argument(parser)
  parser.add_argument("tier", type=str, help="tier with contains the right boundaries")
  parser.add_argument("tiers", type=str, nargs="+", help="tiers that should be fixed")
  parser.add_argument("--difference_threshold", type=float, default=0.005,
                      help="maximum difference threshold to which boundaries should be fixed")
  add_output_directory_argument(parser)
  add_overwrite_tier_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return files_fix_boundaries


def files_fix_boundaries(directory: Path, tier: str, tiers: List[str], difference_threshold: Optional[float], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    fix_interval_boundaries,
    difference_threshold=difference_threshold,
    reference_tier_name=tier,
    tier_names=set(tiers),
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
