from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet
from text_utils import StringFormat, Symbol
from textgrid_utils_cli.common import process_grids_mp
from textgrid_utils_cli.globals import DEFAULT_PUNCTUATION, ExecutionResult
from textgrid_utils_cli.helper import (ConvertToOrderedSetAction,
                                       add_chunksize_argument,
                                       add_directory_argument,
                                       add_interval_format_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument, get_optional)
from textgrid_utils import join_interval_symbols
from textgrid_utils.interval_format import IntervalFormat


def get_symbols_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals based on content. Tip: Merge right first and then left."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  parser.add_argument('--mode', type=str, choices=["right", "left", "together"],
                      help="mode to join: right -> join marks from right; left -> join marks from left; together -> join adjacent intervals containing these marks together", default="right")
  # could be positional but clashes with tiers
  parser.add_argument('--join-symbols', type=str, nargs="+",
                      help="join these symbols", default=OrderedSet(DEFAULT_PUNCTUATION), action=ConvertToOrderedSetAction)
  parser.add_argument('--ignore-join-symbols', type=str, nargs="*",
                      help="don't join to these symbols; only relevant on modes 'right' and 'left'", default=OrderedSet(("", " ")), action=ConvertToOrderedSetAction)
  parser.add_argument('--custom-join-symbol', type=get_optional(str), metavar="SYMBOL",
                      help="use this symbol as join symbol between the intervals", default=None)
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_intervals_between_pauses


def app_join_intervals_between_pauses(directory: Path, tiers: OrderedSet[str], formatting: StringFormat, content: IntervalFormat, custom_join_symbol: Optional[Symbol], join_symbols: OrderedSet[Symbol], ignore_join_symbols: OrderedSet[Symbol], mode: str, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    join_interval_symbols,
    ignore_join_symbols=ignore_join_symbols,
    join_symbols=join_symbols,
    mode=mode,
    tier_names=tiers,
    tiers_interval_format=content,
    tiers_string_format=formatting,
    custom_join_symbol=custom_join_symbol,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)