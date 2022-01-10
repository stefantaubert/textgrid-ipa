from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Callable, Iterable, List, Optional, cast

from ordered_set import OrderedSet
from textgrid.textgrid import TextGrid
from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import (copy_grid, get_grid_files, load_grid,
                                       save_grid)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core import clone_tier
from textgrid_tools.core.globals import ExecutionResult
from tqdm import tqdm

# clones the first tier with the name


def init_files_clone_tier_parser(parser: ArgumentParser):
  parser.description = "This command clones a tier."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--new_tier", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  # parser.add_argument("--overwrite_tier", action="store_true")
  parser.add_argument("--ignore_marks", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return app_clone_tier


def app_clone_tier(directory: Path, tier: str, output_tiers: List[str], n_digits: int, output_directory: Optional[Path], ignore_marks: bool, overwrite: bool) -> ExecutionResult:
  method = partial(
    clone_tier,
    tier_name=tier,
    output_tier_names=OrderedSet(output_tiers),
    ignore_marks=ignore_marks,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)

