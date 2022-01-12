from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument, add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import remove_tiers


def init_files_remove_tiers_parser(parser: ArgumentParser):
  parser.description = "This command removes tiers from a grid."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="the directory containing the grid files")
  parser.add_argument("tiers", metavar="tiers", type=str, nargs="+",
                      help="the tiers which should be removed")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return files_remove_tiers


def files_remove_tiers(directory: Path, tiers: List[str], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    remove_tiers,
    tier_names=set(tiers),
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
