from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_chunksize_argument,
                                       add_grid_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.core import remove_symbols


def get_symbol_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes symbols from tiers."
  add_grid_directory_argument(parser)
  parser.add_argument("tiers", metavar="tiers", type=str, nargs="+",
                      help="tiers which should be transcribed")
  add_string_format_argument(parser, "tiers")
  parser.add_argument("--symbols", type=str, nargs='*',
                      help="remove these symbols from intervals", default=[])
  parser.add_argument("--marks", type=str, nargs='*', metavar="MARK",
                      help="replace these marks with nothing", default=[])
  parser.add_argument("--marks-symbols", type=str, nargs='*',
                      help="remove these symbols from intervals if the mark consists only these symbols", default=[])
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_remove_symbols


def app_remove_symbols(directory: Path, tiers: List[str], formatting: StringFormat, symbols: List[Symbol], marks_symbols: List[Symbol], marks: List[str], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    remove_symbols,
    tier_names=set(tiers),
    tiers_string_format=formatting,
    symbols=set(symbols),
    marks_symbols=set(marks_symbols),
    marks=set(marks),
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
