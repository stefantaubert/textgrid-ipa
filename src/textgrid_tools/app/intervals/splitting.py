from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import DEFAULT_PUNCTUATION, ExecutionResult
from textgrid_tools.app.helper import (add_chunksize_argument,
                                       add_interval_format_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument,
                                       parse_existing_directory,
                                       parse_required)
from textgrid_tools.core import split
from textgrid_tools.core.interval_format import IntervalFormat


def get_splitting_parser(parser: ArgumentParser):
  parser.description = "This command splits the content of a tier."
  parser.add_argument("directory", type=parse_existing_directory, metavar="directory",
                      help="directory containing the grid files which should be modified")
  add_tiers_argument(parser, "tiers which should be split")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  parser.add_argument('--join-symbols', type=parse_required, nargs="*",
                      help="join these symbols while splitting WORD to SYMBOLS", default=DEFAULT_PUNCTUATION)
  parser.add_argument('--ignore-join-symbols', type=parse_required, nargs="*",
                      help="don't join to these symbols while splitting WORD to SYMBOLS", default=[])
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_split


def app_split(directory: Path, tiers: List[str], formatting: StringFormat, content: IntervalFormat, join_symbols: Optional[List[Symbol]], ignore_join_symbols: Optional[List[Symbol]], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    split,
    ignore_join_symbols=ignore_join_symbols,
    join_symbols=join_symbols,
    tier_names=set(tiers),
    tiers_interval_format=content,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
