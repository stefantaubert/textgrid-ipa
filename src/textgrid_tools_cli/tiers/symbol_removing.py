from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import remove_symbols
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_dry_run_argument,
                                       add_encoding_argument, add_maxtaskperchild_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument, parse_non_empty)


def get_symbol_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes symbols from tiers."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers")
  parser.add_argument("--text", type=parse_non_empty, nargs='*',
                      help="remove this text from intervals", default=[], action=ConvertToOrderedSetAction, metavar="TEXT")
  parser.add_argument("--marks", type=parse_non_empty, nargs='*', metavar="MARK",
                      help="replace these marks with nothing", default=[], action=ConvertToOrderedSetAction)
  parser.add_argument("--marks-text", type=parse_non_empty, nargs='*',
                      help="remove mark from intervals if the mark consists only these texts", default=[], action=ConvertToOrderedSetAction, metavar="MARKS-TEXT")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_remove_symbols


def app_remove_symbols(ns: Namespace) -> ExecutionResult:
  method = partial(
    remove_symbols,
    tier_names=ns.tiers,
    text=ns.text,
    marks_text=ns.marks_text,
    marks=ns.marks,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
