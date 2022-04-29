from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet

from textgrid_tools import join_marks
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_maxtaskperchild_argument,
                                       add_n_digits_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument, parse_non_empty)
from textgrid_tools_cli.intervals.common import add_join_empty_argument, add_join_with_argument
from textgrid_tools_cli.validation import ValidationError


class NoMarkDefinedError(ValidationError):
  @classmethod
  def validate(cls, marks: OrderedSet[str], empty: bool):
    if not (empty or len(marks) > 0):
      return cls()
    return None

  @property
  def default_message(self) -> str:
    return "At least one mark or 'empty' needs to be specified!"


def get_mark_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals containing specific marks."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  parser.add_argument("--empty", action="store_true",
                      help="join empty marks")
  parser.add_argument('--marks', type=parse_non_empty, metavar="MARK", nargs="*",
                      help="join adjacent intervals containing these marks", default=[], action=ConvertToOrderedSetAction)
  add_join_with_argument(parser)
  add_join_empty_argument(parser)
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_marks


def app_join_marks(directory: Path, tiers: OrderedSet[str], join_with: str, join_empty: bool, empty: bool, marks: OrderedSet[str], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  if error := NoMarkDefinedError.validate(marks, empty):
    logger = getLogger(__name__)
    logger.error(error.default_message)
    return False, False

  method = partial(
    join_marks,
    tier_names=tiers,
    join_with=join_with,
    ignore_empty=not join_empty,
    empty=empty,
    marks=marks,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
