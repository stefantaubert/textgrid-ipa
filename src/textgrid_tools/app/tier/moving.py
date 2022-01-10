from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from textgrid_tools.app.globals import DEFAULT_N_DIGITS, ExecutionResult
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import move_tier


def init_files_move_tier_parser(parser: ArgumentParser):
  parser.description = "This commands moves a tier to another position in the grid."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--position", type=int, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_move_tier


def files_move_tier(directory: Path, tier: str, n_digits: int, output_directory: Optional[Path], position: int, overwrite: bool) -> ExecutionResult:
  method = partial(
    move_tier,
    tier_name=tier,
    position=position,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
