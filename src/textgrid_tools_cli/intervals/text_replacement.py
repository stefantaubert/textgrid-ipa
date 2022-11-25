from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import replace_text
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument, parse_pattern)


def get_text_replacement_parser(parser: ArgumentParser):
  parser.description = "This command replace text in intervals."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers which should be transcribed")
  parser.add_argument("pattern", type=parse_pattern,
                      metavar="PATTERN", help="regex pattern")
  parser.add_argument("replace_with", type=str, metavar="REPLACE-WITH",
                      help="replace pattern with this text")
  add_encoding_argument(parser, "encoding of grids")
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return replace_text_ns


def replace_text_ns(ns: Namespace) -> ExecutionResult:
  method = partial(
    replace_text,
    tier_names=ns.tiers,
    pattern=ns.pattern,
    replace_with=ns.replace_with,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
