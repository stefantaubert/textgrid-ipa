from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import rename_tier
from textgrid_tools.core.validation import (InvalidTierNameError,
                                            NonDistinctTiersError)


def get_renaming_parser(parser: ArgumentParser):
  parser.description = "This command renames a tier."
  add_grid_directory_argument(parser)
  parser.add_argument("tier", type=str, metavar="tier",
                      help="tier which should be renamed")
  parser.add_argument("name", type=str, metavar="tier",
                      help="new name of tier")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_rename_tier


def app_rename_tier(directory: Path, tier: str, name: str, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
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
