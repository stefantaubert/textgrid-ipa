from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet

from textgrid_utils import join_intervals_on_durations
from textgrid_utils_cli.common import process_grids_mp
from textgrid_utils_cli.globals import ExecutionResult
from textgrid_utils_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_maxtaskperchild_argument, add_n_digits_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument,
                                       parse_positive_float)


def get_duration_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals to intervals with a maximum duration."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  parser.add_argument("--duration", metavar="SECONDS", type=parse_positive_float,
                      help="maximum duration until intervals should be joined (in seconds)", default=10)
  parser.add_argument("--include-pauses", action="store_true",
                      help="include pauses at the beginning/ending while joining")
  parser.add_argument('--join-with', type=str, metavar="SYMBOL",
                      help="use this symbol as join symbol between the intervals", default=" ")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_intervals_on_durations


def app_join_intervals_on_durations(directory: Path, tiers: OrderedSet[str], join_with: str, n_digits: int, duration: float, include_pauses: bool, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  print(tiers)
  method = partial(
    join_intervals_on_durations,
    tier_names=tiers,
    include_empty_intervals=include_pauses,
    max_duration_s=duration,
    join_with=join_with,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)