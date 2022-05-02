from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet

from textgrid_tools import remove_symbols
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_maxtaskperchild_argument,
                                       add_n_digits_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument, parse_non_empty)


def get_symbol_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes symbols from tiers."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers")
  parser.add_argument("--text", type=parse_non_empty, nargs='*',
                      help="remove this text from intervals", default=[], action=ConvertToOrderedSetAction)
  parser.add_argument("--marks", type=parse_non_empty, nargs='*', metavar="MARK",
                      help="replace these marks with nothing", default=[], action=ConvertToOrderedSetAction)
  parser.add_argument("--marks-text", type=parse_non_empty, nargs='*',
                      help="remove mark from intervals if the mark consists only these texts", default=[], action=ConvertToOrderedSetAction)
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_remove_symbols


def app_remove_symbols(directory: Path, tiers: OrderedSet[str], text: OrderedSet[str], marks_text: OrderedSet[str], marks: OrderedSet[str], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    remove_symbols,
    tier_names=tiers,
    text=text,
    marks_text=marks_text,
    marks=marks,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
