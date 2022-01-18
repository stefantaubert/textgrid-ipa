from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_chunksize_argument,
                                       add_grid_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_tier_argument, add_tiers_argument,
                                       parse_non_negative_float)
from textgrid_tools.core import fix_interval_boundaries


def get_boundary_fixing_parser(parser: ArgumentParser):
  parser.description = "This command set the closest boundaries of tiers to those of a reference tier."
  add_grid_directory_argument(parser)
  add_tier_argument(parser, "tier with contains the right boundaries")
  add_tiers_argument(parser, "tiers that should be fixed")
  parser.add_argument("--difference-threshold", type=parse_non_negative_float, default=0.005,
                      help="difference threshold to which boundaries should be fixed")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_fix_interval_boundaries


def app_fix_interval_boundaries(directory: Path, tier: str, tiers: List[str], difference_threshold: float, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    fix_interval_boundaries,
    difference_threshold=difference_threshold,
    reference_tier_name=tier,
    tier_names=tiers,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
