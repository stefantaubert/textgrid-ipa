from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.globals import DEFAULT_N_DIGITS, ExecutionResult
from textgrid_tools.app.common import process_grids
from textgrid_tools.core import remove_symbols


def get_symbol_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes symbols from tiers."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tiers", type=str, nargs='+', required=True)
  parser.add_argument("--symbols", type=str, nargs='+', required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return app_remove_symbols


def app_remove_symbols(directory: Path, tiers: List[str], tiers_format: StringFormat, symbols: List[Symbol], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    remove_symbols,
    tier_names=set(tiers),
    tiers_string_format=tiers_format,
    symbols=set(symbols),
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
