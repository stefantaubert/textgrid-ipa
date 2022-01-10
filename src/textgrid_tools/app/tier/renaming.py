from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional

from textgrid_tools.app.globals import DEFAULT_N_DIGITS, ExecutionResult
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import rename_tier
from textgrid_tools.core.validation import (InvalidTierNameError,
                                            NonDistinctTiersError)


def init_files_rename_tier_parser(parser: ArgumentParser):
  parser.description = "This command renames a tier."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--new_name", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_rename_tier


def files_rename_tier(directory: Path, tier: str, name: str, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if error := NonDistinctTiersError.validate(tier, name):
    logger.error(error.default_message)
    return False, False

  if error := InvalidTierNameError.validate(name):
    logger.error(error.default_message)
    return False, False

  method = partial(
    rename_tier,
    tier_name=tier,
    output_tier_name=name,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
