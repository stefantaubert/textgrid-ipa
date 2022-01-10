from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
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
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to directory")
  add_overwrite_argument(parser)
  return files_remove_tiers


def files_remove_tiers(directory: Path, tiers: List[str], n_digits: int, output_directory: Path, overwrite: bool) -> ExecutionResult:
  method = partial(
    remove_tiers,
    tier_names=tiers,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
