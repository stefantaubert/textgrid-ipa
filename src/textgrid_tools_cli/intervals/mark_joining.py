from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet
from text_utils import StringFormat
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction,
                                       add_chunksize_argument,
                                       add_directory_argument,
                                       add_interval_format_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument, parse_non_empty,
                                       parse_non_negative_float)
from textgrid_tools_cli.validation import ValidationError
from textgrid_tools import IntervalFormat, join_marks


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
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  parser.add_argument("--empty", action="store_true",
                      help="join empty marks")
  parser.add_argument('--marks', type=parse_non_empty, metavar="MARK", nargs="*",
                      help="join adjacent intervals containing these marks", default=[], action=ConvertToOrderedSetAction)
  # TODO
  #parser.add_argument("--join-with", type=get_optional(parse_non_empty), default=None, help="join marks of intervals with this text in between")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_marks


def app_join_marks(directory: Path, tiers: OrderedSet[str], formatting: StringFormat, content: IntervalFormat, empty: bool, marks: OrderedSet[str], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  if error := NoMarkDefinedError.validate(marks, empty):
    logger = getLogger(__name__)
    logger.error(error.default_message)
    return False, False

  method = partial(
    join_marks,
    tier_names=tiers,
    tiers_interval_format=content,
    tiers_string_format=formatting,
    empty=empty,
    marks=marks,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
