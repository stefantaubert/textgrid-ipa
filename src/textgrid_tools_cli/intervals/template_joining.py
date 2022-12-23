from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import join_by_template
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tier_argument, get_optional, parse_non_empty,
                                       parse_non_empty_or_whitespace)
from textgrid_tools_cli.intervals.common import add_join_empty_argument, add_join_with_argument


def get_template_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals according to a template."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier on which the intervals should be joined")
  parser.add_argument('template', type=parse_non_empty, metavar="MARK", nargs="+",
                      help="join adjacent intervals equaling to this template")
  parser.add_argument("--boundary-tier", metavar="BOUNDARY-TIER", type=get_optional(parse_non_empty_or_whitespace),
                      help="only apply templates in the intervals boundaries of this tier", default=None)
  add_join_with_argument(parser)
  add_join_empty_argument(parser)
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_join_template


def app_join_template(ns: Namespace) -> ExecutionResult:
  method = partial(
    join_by_template,
    tier_names={ns.tier},
    boundary_tier_name=ns.boundary_tier,
    join_with=ns.join_with,
    ignore_empty=not ns.join_empty,
    template=ns.template,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
