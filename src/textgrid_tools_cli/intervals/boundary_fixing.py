from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import fix_interval_boundaries
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tier_argument, add_tiers_argument, parse_positive_float)


def get_boundary_fixing_parser(parser: ArgumentParser):
  parser.description = "This command set the closest boundaries of tiers to those of a reference tier."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier with contains the right boundaries", meta_var="REFERENCE-TIER")
  add_tiers_argument(parser, "tiers that should be fixed")
  parser.add_argument("--difference-threshold", type=parse_positive_float, default=0.005, metavar="THRESHOLD",
                      help="difference threshold to which boundaries should be fixed; needs to be greater than zero")
  add_output_directory_argument(parser)
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_fix_interval_boundaries


def app_fix_interval_boundaries(ns: Namespace) -> ExecutionResult:
  method = partial(
    fix_interval_boundaries,
    difference_threshold=ns.difference_threshold,
    reference_tier_name=ns.tier,
    tier_names=ns.tiers,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
