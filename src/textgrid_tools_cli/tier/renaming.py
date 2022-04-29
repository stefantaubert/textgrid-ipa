from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional

from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument,
                                       add_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_tier_argument, parse_non_empty_or_whitespace)
from textgrid_tools import rename_tier
from textgrid_tools.validation import (NonDistinctTiersError)


def get_renaming_parser(parser: ArgumentParser):
  parser.description = "This command renames a tier."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be renamed")
  parser.add_argument("name", type=parse_non_empty_or_whitespace, metavar="tier",
                      help="new name of tier")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_rename_tier


def app_rename_tier(directory: Path, tier: str, name: str, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  assert len(name.strip()) > 0

  logger = getLogger(__name__)

  if error := NonDistinctTiersError.validate(tier, name):
    logger.error(error.default_message)
    return False, False

  method = partial(
    rename_tier,
    tier_name=tier,
    output_tier_name=name,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
