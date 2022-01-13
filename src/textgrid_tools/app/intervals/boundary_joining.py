from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils import StringFormat
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_interval_format_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.app.common import process_grids
from textgrid_tools.core import join_intervals_on_boundaries
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.interval_format import IntervalFormat


def get_boundary_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier according to the interval boundaries of another tier."
  add_grid_directory_argument(parser)
  parser.add_argument("boundary_tier", metavar="boundary-tier", type=str,
                      help="tier from which the boundaries should be considered")
  parser.add_argument("tiers", type=str, nargs="+",
                      help="tiers on which the intervals should be joined")
  add_string_format_argument(parser, '--mark-format', "format of marks in tiers")
  add_interval_format_argument(parser, '--mark-type', "type of marks in tiers")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_join_intervals_on_boundaries


def app_join_intervals_on_boundaries(directory: Path, tiers: List[str], mark_format: StringFormat, mark_type: IntervalFormat, boundary_tier: str, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    join_intervals_on_boundaries,
    boundary_tier_name=boundary_tier,
    tier_names=set(tiers),
    tiers_interval_format=mark_type,
    tiers_string_format=mark_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
