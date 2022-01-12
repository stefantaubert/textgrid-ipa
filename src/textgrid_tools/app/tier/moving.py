from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import move_tier


def init_files_move_tier_parser(parser: ArgumentParser):
  parser.description = "This commands moves a tier to another position in the grid."
  add_grid_directory_argument(parser)
  parser.add_argument("tier", type=str, metavar="tier",
                      help="tier which should be moved")
  parser.add_argument("position", type=int, metavar="position",
                      help="move tier to this position (1 = first tier)")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return files_move_tier


def files_move_tier(directory: Path, tier: str, n_digits: int, output_directory: Optional[Path], position: int, overwrite: bool) -> ExecutionResult:
  method = partial(
    move_tier,
    tier_name=tier,
    position=position,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
