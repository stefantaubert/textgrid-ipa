from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from ordered_set import OrderedSet
from text_utils import StringFormat
from textgrid_utils_cli.common import process_grids_mp
from textgrid_utils_cli.helper import (add_chunksize_argument,
                                       add_directory_argument,
                                       add_interval_format_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument,
                                       parse_non_empty_or_whitespace)
from textgrid_utils import join_intervals_on_boundaries
from textgrid_utils.globals import ExecutionResult
from textgrid_utils.interval_format import IntervalFormat


def get_boundary_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals according to the interval boundaries of another tier."
  add_directory_argument(parser)
  parser.add_argument("boundary_tier", metavar="boundary-tier", type=parse_non_empty_or_whitespace,
                      help="tier from which the boundaries should be considered")
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_intervals_on_boundaries


def app_join_intervals_on_boundaries(directory: Path, tiers: OrderedSet[str], formatting: StringFormat, content: IntervalFormat, boundary_tier: str, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    join_intervals_on_boundaries,
    boundary_tier_name=boundary_tier,
    tier_names=tiers,
    tiers_interval_format=content,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
