from argparse import ArgumentParser, Namespace
from functools import partial
from math import inf

from textgrid_tools import mark_silence
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument, parse_non_empty,
                                       parse_non_negative_float)
from textgrid_tools_cli.logging_configuration import init_and_get_console_logger
from textgrid_tools_cli.validation import ValidationError


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
  parser.add_argument("--mark", type=parse_non_empty, metavar="ASSIGN-MARK",
                      help="mark to assign to silence intervals", default="sil")
  parser.add_argument("--min-duration", type=parse_non_negative_float,
                      help="inclusive minimum duration of silence in seconds", default=0, metavar="MIN-DURATION")
  parser.add_argument("--max-duration", type=parse_non_negative_float,
                      help="exclusive maximum duration of silence in seconds", default=inf, metavar="MAX-DURATION")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_label_silence


def app_label_silence(ns: Namespace) -> ExecutionResult:
  if error := MaxNotGreaterThanMinError.validate(ns.min_duration, ns.max_duration):
    logger = init_and_get_console_logger(__name__)
    logger.error(error.default_message)
    return False, False

  method = partial(
    mark_silence,
    tier_names=ns.tiers,
    mark=ns.mark,
    min_duration=ns.min_duration,
    max_duration=ns.max_duration,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
