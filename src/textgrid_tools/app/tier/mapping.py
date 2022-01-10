from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional, Set

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument, copy_grid,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core import map_tier


def get_map_tier_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files which should be modified")
  parser.add_argument("tier", metavar="tier", type=str,
                      help="tier which should be mapped")
  parser.add_argument("target_tiers", metavar="target-tier",
                      type=str, nargs="+", help="tiers to which the content should be mapped")
  parser.add_argument('--tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="format of tier")
  parser.add_argument('--target-tiers-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="tier format of target-tiers")
  parser.add_argument("--include-pauses", action="store_true",
                      help="include mapping from and to pause intervals, i.e., those which contain nothing or only whitespace")
  parser.add_argument("--ignore-marks", type=str, nargs="*",
                      metavar="SYMBOL", help="ignore these marks")
  parser.add_argument("--only-symbols", type=str, nargs="*",
                      metavar="SYMBOL", help="ignore marks that contain only these symbols")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return __main


def __main(directory: Path, tier: str, tier_format: StringFormat, target_tiers: Set[str], target_tiers_format: StringFormat, include_pauses: bool, ignore_marks: Set[str], only_symbols: Set[Symbol], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    map_tier,
    ignore_marks=ignore_marks,
    include_pauses=include_pauses,
    only_symbols=only_symbols,
    target_tier_names=set(target_tiers),
    targets_string_format=target_tiers_format,
    tier_name=tier,
    tier_string_format=tier_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
