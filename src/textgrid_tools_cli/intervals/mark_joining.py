from argparse import ArgumentParser, Namespace
from functools import partial

from ordered_set import OrderedSet

from textgrid_tools import join_marks
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_dry_run_argument,
                                       add_encoding_argument, add_maxtaskperchild_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument, parse_non_empty)
from textgrid_tools_cli.intervals.common import add_join_empty_argument, add_join_with_argument
from textgrid_tools_cli.logging_configuration import init_and_get_console_logger
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
                      help="join adjacent intervals containing these marks", default=OrderedSet(), action=ConvertToOrderedSetAction)
  add_join_with_argument(parser)
  add_join_empty_argument(parser)
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_join_marks


def app_join_marks(ns: Namespace) -> ExecutionResult:
  if error := NoMarkDefinedError.validate(ns.marks, ns.empty):
    logger = init_and_get_console_logger(__name__)
    logger.error(error.default_message)
    return False, False

  method = partial(
    join_marks,
    tier_names=ns.tiers,
    join_with=ns.join_with,
    ignore_empty=not ns.join_empty,
    empty=ns.empty,
    marks=ns.marks,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
