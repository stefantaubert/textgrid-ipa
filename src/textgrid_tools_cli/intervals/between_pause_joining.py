from argparse import ArgumentParser
from functools import partial
from math import inf
from pathlib import Path
from typing import List, Optional

from ordered_set import OrderedSet
from text_utils import StringFormat, Symbol
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument,
                                       add_directory_argument,
                                       add_interval_format_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument, get_optional,
                                       parse_non_negative_float)
from textgrid_tools.core import join_intervals_between_pauses
from textgrid_tools.core.interval_format import IntervalFormat


def get_between_pause_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent non-silence intervals."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  parser.add_argument('--pause', type=parse_non_negative_float, metavar="SECONDS",
                      help="until duration (in seconds) of adjacent pauses that should be merged, i.e., value \'0\' means only adjacent non-pause intervals are joined and \'inf\' means all intervals are joined", default=inf)
  parser.add_argument('--custom-join-symbol', type=get_optional(str), metavar="SYMBOL",
                      help="use this symbol as join symbol between the intervals", default=None)
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_intervals_between_pauses


def app_join_intervals_between_pauses(directory: Path, tiers: OrderedSet[str], formatting: StringFormat, content: IntervalFormat, pause: float, custom_join_symbol: Optional[Symbol], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    join_intervals_between_pauses,
    pause=pause,
    tier_names=tiers,
    tiers_interval_format=content,
    tiers_string_format=formatting,
    custom_join_symbol=custom_join_symbol,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
