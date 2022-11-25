from argparse import ArgumentParser, Namespace
from functools import partial

from ordered_set import OrderedSet

from textgrid_tools import join_interval_symbols
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import DEFAULT_PUNCTUATION, ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_dry_run_argument,
                                       add_encoding_argument, add_maxtaskperchild_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument)
from textgrid_tools_cli.intervals.common import add_join_empty_argument, add_join_with_argument


def get_symbols_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals based on content. Tip: Merge right first and then left."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  parser.add_argument('--mode', type=str, choices=["right", "left", "together"],
                      help="mode to join: right -> join marks from right; left -> join marks from left; together -> join adjacent intervals containing these marks together", default="right")
  # could be positional but clashes with tiers
  parser.add_argument('--join-symbols', type=str, nargs="+", metavar="JOIN-SYMBOL",
                      help="join these symbols", default=OrderedSet(DEFAULT_PUNCTUATION), action=ConvertToOrderedSetAction)
  parser.add_argument('--ignore-join-symbols', type=str, nargs="*", metavar="IGNORE-SYMBOL",
                      help="don't join to these symbols; only relevant on modes 'right' and 'left'", default=OrderedSet(("", " ")), action=ConvertToOrderedSetAction)
  add_join_with_argument(parser)
  add_join_empty_argument(parser)
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_join_intervals_between_pauses


def app_join_intervals_between_pauses(ns: Namespace) -> ExecutionResult:
  method = partial(
    join_interval_symbols,
    ignore_join_symbols=ns.ignore_join_symbols,
    join_symbols=ns.join_symbols,
    mode=ns.mode,
    tier_names=ns.tiers,
    join_with=ns.join_with,
    ignore_empty=not ns.join_empty,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
