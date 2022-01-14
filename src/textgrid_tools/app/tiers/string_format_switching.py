from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional, Set

from text_utils.string_format import StringFormat
from textgrid_tools.app.common import process_grids
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.core import switch_string_format


def get_string_format_switching_parser(parser: ArgumentParser):
  parser.description = "This command converts text in TEXT format to the SYMBOL format."
  add_grid_directory_argument(parser)
  parser.add_argument("tiers", metavar="tiers", type=str, nargs="+",
                      help="tiers which formats should be switched")
  add_string_format_argument(parser, "--tiers-format", "format of tiers")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_switch_string_format


def app_switch_string_format(directory: Path, tiers: Set[str], tiers_format: StringFormat, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    switch_string_format,
    tier_names=set(tiers),
    tiers_string_format=tiers_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
