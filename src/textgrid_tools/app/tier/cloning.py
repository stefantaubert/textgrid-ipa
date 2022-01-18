from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from ordered_set import OrderedSet
from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.helper import (add_chunksize_argument,
                                       add_grid_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_tier_argument, add_tiers_argument)
from textgrid_tools.core import clone_tier
from textgrid_tools.core.globals import ExecutionResult


def get_cloning_parser(parser: ArgumentParser):
  parser.description = "This command clones a tier."

  add_grid_directory_argument(parser)
  add_tier_argument(parser, "tier which should be cloned")
  add_tiers_argument(parser, "tiers which should be cloned to")
  parser.add_argument("--ignore-marks", action="store_true",
                      help="ignore marks while cloning")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_clone_tier


def app_clone_tier(directory: Path, tier: str, tiers: OrderedSet[str], n_digits: int, output_directory: Optional[Path], ignore_marks: bool, overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    clone_tier,
    tier_name=tier,
    output_tier_names=tiers,
    ignore_marks=ignore_marks,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
