from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional, Set

from text_utils.string_format import StringFormat
from textgrid_tools.app.globals import DEFAULT_N_DIGITS, ExecutionResult
from textgrid_tools.app.common import process_grids
from textgrid_tools.core import switch_string_format


def get_string_format_switching_parser(parser: ArgumentParser):
  parser.description = "This command converts text in TEXT format to the SYMBOL format."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--tier", type=str, required=True)
  parser.add_argument("--new_tier", type=str, required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return app_switch_string_format


def app_switch_string_format(directory: Path, tiers: Set[str], tiers_format: StringFormat, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    switch_string_format,
    tier_names=set(tiers),
    tiers_string_format=tiers_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
