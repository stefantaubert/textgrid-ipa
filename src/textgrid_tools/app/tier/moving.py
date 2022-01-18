from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_chunksize_argument,
                                       add_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_tier_argument,
                                       parse_non_negative_integer)
from textgrid_tools.core import move_tier


def get_moving_parser(parser: ArgumentParser):
  parser.description = "This commands moves a tier to another position in the grid."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be moved")
  parser.add_argument("position", type=parse_non_negative_integer, metavar="position",
                      help="move tier to this position (0 = first tier)")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_move_tier


def app_move_tier(directory: Path, tier: str, n_digits: int, output_directory: Optional[Path], position: int, overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    move_tier,
    tier_name=tier,
    position=position,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
