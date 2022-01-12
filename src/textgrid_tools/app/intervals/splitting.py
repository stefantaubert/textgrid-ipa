from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.common import process_grids
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_interval_format_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.core import split
from textgrid_tools.core.interval_format import IntervalFormat


def get_splitting_parser(parser: ArgumentParser):
  parser.description = "This command splits the content of a tier."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files which should be modified")
  parser.add_argument("tiers", metavar="tiers", nargs="+", type=str,
                      help="tiers which should be split")
  add_string_format_argument(parser, '--mark-format', "format of marks in tiers")
  add_interval_format_argument(parser, '--mark-type', "type of marks in tiers")
  parser.add_argument('--join-symbols', type=str, nargs="*",
                      help="join these symbols while splitting WORD to SYMBOLS", default=[])
  parser.add_argument('--ignore-join-symbols', type=str, nargs="*",
                      help="don't join to these symbols while splitting WORD to SYMBOLS", default=[])
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_split


def app_split(directory: Path, tiers: List[str], mark_format: StringFormat, mark_type: IntervalFormat, join_symbols: Optional[List[Symbol]], ignore_join_symbols: Optional[List[Symbol]], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    split,
    ignore_join_symbols=ignore_join_symbols,
    join_symbols=join_symbols,
    tier_names=set(tiers),
    tiers_interval_format=mark_type,
    tiers_string_format=mark_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
