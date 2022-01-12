from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils import StringFormat
from text_utils.string_format import StringFormat
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_interval_format_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.app.common import process_grids
from textgrid_tools.core import join_intervals_on_durations
from textgrid_tools.core.interval_format import IntervalFormat


def get_duration_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier to intervals containing sentences."
  add_grid_directory_argument(parser)
  parser.add_argument("tiers", type=str, nargs="+",
                      help="tiers on which the intervals should be joined")
  add_string_format_argument(parser, '--mark-format', "format of marks in tiers")
  add_interval_format_argument(parser, '--mark-type', "type of marks in tiers")
  parser.add_argument("--max-duration", metavar="SECONDS", type=str,
                      help="maximum duration until intervals should be joined (in seconds)", default=10)
  parser.add_argument("--include-pauses", action="store_true",
                      help="include pauses at the beginning/ending while joining")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_join_intervals_on_durations


def app_join_intervals_on_durations(directory: Path, tiers: List[str], mark_format: StringFormat, mark_type: IntervalFormat, n_digits: int, max_duration: float, include_pauses: bool, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    join_intervals_on_durations,
    tier_names=set(tiers),
    include_empty_intervals=include_pauses,
    max_duration_s=max_duration,
    tiers_interval_format=mark_type,
    tiers_string_format=mark_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
