from argparse import ArgumentParser
from functools import partial
from math import inf
from pathlib import Path
from typing import List, Optional

from text_utils import StringFormat
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import join_intervals_between_pauses
from textgrid_tools.core.interval_format import IntervalFormat


def init_files_join_intervals_on_pauses_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier to intervals containing sentences."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files")
  parser.add_argument("tier", type=str, help="the tier on which the intervals should be joined")
  add_n_digits_argument(parser)
  parser.add_argument('--mark-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="format of marks in tier")
  parser.add_argument('--mark-type', choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD, help="type of marks in tier")
  parser.add_argument('--join-pause', type=float, metavar="SECONDS",
                      help="until duration (in seconds) of adjacent pauses that should be merged, i.e., value \'0\' means only adjacent non-pause intervals are joined and \'inf\' means all intervals are joined", default=inf)
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="tier on which the mapped content should be written to if not to tier")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="directory where to output the modified grid files if not to directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_join_intervals_on_pauses


def files_join_intervals_on_pauses(directory: Path, tiers: List[str], mark_format: StringFormat, mark_type: IntervalFormat, join_pause: float, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    join_intervals_between_pauses,
    pause=join_pause,
    tier_names=set(tiers),
    tiers_interval_format=mark_type,
    tiers_string_format=mark_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
