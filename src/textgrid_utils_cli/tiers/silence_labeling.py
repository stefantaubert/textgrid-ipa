from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from math import inf
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet

from textgrid_utils import mark_silence
from textgrid_utils_cli.common import process_grids_mp
from textgrid_utils_cli.globals import ExecutionResult
from textgrid_utils_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_maxtaskperchild_argument, add_n_digits_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument, parse_non_empty,
                                       parse_non_negative_float)
from textgrid_utils_cli.validation import ValidationError


class MaxNotGreaterThanMinError(ValidationError):
  def __init__(self, min_duration: float, max_duration: float) -> None:
    super().__init__()
    self.min_duration = min_duration
    self.max_duration = max_duration

  @classmethod
  def validate(cls, min_duration: float, max_duration: float):
    if not min_duration < max_duration:
      return cls(min_duration, max_duration)
    return None

  @property
  def default_message(self) -> str:
    return "Duration needs to be greater than min-duration!"


def get_label_silence_parser(parser: ArgumentParser):
  parser.description = "This command labels silence intervals."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers where to label silence")
  parser.add_argument("--mark", type=parse_non_empty,
                      help="mark to assign to silence intervals", default="sil")
  parser.add_argument("--min-duration", type=parse_non_negative_float,
                      help="inclusive minimum duration of silence in seconds", default=0)
  parser.add_argument("--max-duration", type=parse_non_negative_float,
                      help="exclusive maximum duration of silence in seconds", default=inf)
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_label_silence


def app_label_silence(directory: Path, tiers: OrderedSet[str], n_digits: int, output_directory: Optional[Path], overwrite: bool, min_duration: float, max_duration: float, mark: str, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  if error := MaxNotGreaterThanMinError.validate(min_duration, max_duration):
    logger = getLogger(__name__)
    logger.error(error.default_message)
    return False, False

  method = partial(
    mark_silence,
    tier_names=tiers,
    mark=mark,
    min_duration=min_duration,
    max_duration=max_duration,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
