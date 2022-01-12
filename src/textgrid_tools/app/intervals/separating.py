from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import separate
from textgrid_tools.core.interval_format import IntervalFormat

# TODO tiers support


def get_separating_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files which should be modified")
  parser.add_argument("tier", metavar="tier", type=str,
                      help="tier which should be mapped")
  parser.add_argument('--tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT)
  parser.add_argument('--tier-type', choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD)
  parser.add_argument('--join-symbols', type=str, nargs="*",
                      help="join these symbols while splitting WORD to SYMBOLS")
  parser.add_argument('--ignore-join-symbols', type=str, nargs="*",
                      help="don't join to these symbols while splitting WORD to SYMBOLS")
  add_n_digits_argument(parser)
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="tier on which the mapped content should be written if not to target-tier.")
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_separating_intervals


def app_separating_intervals(directory: Path, tiers: List[str], tier_format: StringFormat, tier_type: IntervalFormat, join_symbols: Optional[List[Symbol]], ignore_join_symbols: Optional[List[Symbol]], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    separate,
    ignore_join_symbols=ignore_join_symbols,
    join_symbols=join_symbols,
    tier_names=set(tiers),
    tiers_interval_format=tier_type,
    tiers_string_format=tier_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
