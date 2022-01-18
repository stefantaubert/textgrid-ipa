from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils import StringFormat
from text_utils.string_format import StringFormat
from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_chunksize_argument,
                                       add_grid_directory_argument,
                                       add_interval_format_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument, add_tiers_argument, parse_non_whitespace, parse_positive_float)
from textgrid_tools.core import join_intervals_on_durations
from textgrid_tools.core.interval_format import IntervalFormat


def get_duration_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier to intervals containing sentences."
  add_grid_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  parser.add_argument("--duration", metavar="SECONDS", type=parse_positive_float,
                      help="maximum duration until intervals should be joined (in seconds)", default=10)
  parser.add_argument("--include-pauses", action="store_true",
                      help="include pauses at the beginning/ending while joining")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_intervals_on_durations


def app_join_intervals_on_durations(directory: Path, tiers: List[str], formatting: StringFormat, content: IntervalFormat, n_digits: int, duration: float, include_pauses: bool, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    join_intervals_on_durations,
    tier_names=set(tiers),
    include_empty_intervals=include_pauses,
    max_duration_s=duration,
    tiers_interval_format=content,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
