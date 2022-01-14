from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.common import process_grids
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.core import remove_symbols


def get_symbol_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes symbols from tiers."
  add_grid_directory_argument(parser)
  parser.add_argument("tiers", metavar="tiers", type=str, nargs="+",
                      help="tiers which should be transcribed")
  add_string_format_argument(parser, "--tiers-format", "format of tiers")
  parser.add_argument("symbols", type=str, nargs='+', help="remove these symbols")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_remove_symbols


def app_remove_symbols(directory: Path, tiers: List[str], tiers_format: StringFormat, symbols: List[Symbol], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    remove_symbols,
    tier_names=set(tiers),
    tiers_string_format=tiers_format,
    symbols=set(symbols),
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
