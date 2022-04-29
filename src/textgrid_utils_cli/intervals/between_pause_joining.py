from argparse import ArgumentParser
from functools import partial
from math import inf
from pathlib import Path
from typing import List, Optional

from ordered_set import OrderedSet

from textgrid_utils import join_intervals_between_pauses
from textgrid_utils_cli.common import process_grids_mp
from textgrid_utils_cli.globals import ExecutionResult
from textgrid_utils_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_maxtaskperchild_argument, add_n_digits_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument,
                                       parse_non_negative_float)


def get_between_pause_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent non-silence intervals."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  parser.add_argument('--pause', type=parse_non_negative_float, metavar="SECONDS",
                      help="until duration (in seconds) of adjacent pauses that should be merged, i.e., value \'0\' means only adjacent non-pause intervals are joined and \'inf\' means all intervals are joined", default=inf)
  parser.add_argument('--join-with', type=str, metavar="SYMBOL",
                      help="use this symbol as join symbol between the intervals", default=" ")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_intervals_between_pauses


def app_join_intervals_between_pauses(directory: Path, tiers: OrderedSet[str], pause: float, join_with: str, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    join_intervals_between_pauses,
    pause=pause,
    tier_names=tiers,
    join_with=join_with,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
