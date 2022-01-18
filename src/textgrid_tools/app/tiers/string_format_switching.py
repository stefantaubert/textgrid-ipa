from ordered_set import OrderedSet
from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional, Set

from text_utils.string_format import StringFormat
from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_chunksize_argument,
                                       add_grid_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument)
from textgrid_tools.core import switch_string_format


def get_string_format_switching_parser(parser: ArgumentParser):
  parser.description = "This command converts text in TEXT format to the SYMBOL format."
  add_grid_directory_argument(parser)
  add_tiers_argument(parser, "tiers which formats should be switched")
  add_string_format_argument(parser, "tiers")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_switch_string_format


def app_switch_string_format(directory: Path, tiers: OrderedSet[str], formatting: StringFormat, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    switch_string_format,
    tier_names=tiers,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
