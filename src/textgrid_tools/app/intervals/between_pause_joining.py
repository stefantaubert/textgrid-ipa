from argparse import ArgumentParser
from functools import partial
from math import inf
from pathlib import Path
from typing import List, Optional

from text_utils import StringFormat
from textgrid_tools.app.common import process_grids
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_interval_format_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.core import join_intervals_between_pauses
from textgrid_tools.core.interval_format import IntervalFormat


def get_between_pause_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier to intervals containing sentences."
  add_grid_directory_argument(parser)
  parser.add_argument("tiers", type=str, nargs="+",
                      help="tiers on which the intervals should be joined")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  parser.add_argument('--pause', type=float, metavar="SECONDS",
                      help="until duration (in seconds) of adjacent pauses that should be merged, i.e., value \'0\' means only adjacent non-pause intervals are joined and \'inf\' means all intervals are joined", default=inf)
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_join_intervals_between_pauses


def app_join_intervals_between_pauses(directory: Path, tiers: List[str], formatting: StringFormat, content: IntervalFormat, pause: float, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    join_intervals_between_pauses,
    pause=pause,
    tier_names=set(tiers),
    tiers_interval_format=content,
    tiers_string_format=formatting,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
