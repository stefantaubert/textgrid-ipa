from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import clone_tier
from textgrid_tools.globals import ExecutionResult
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tier_argument, add_tiers_argument)


def get_cloning_parser(parser: ArgumentParser):
  parser.description = "This command clones a tier."

  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be cloned")
  add_tiers_argument(parser, "tiers which should be cloned to")
  parser.add_argument("--ignore-marks", action="store_true",
                      help="ignore marks while cloning")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_clone_tier


def app_clone_tier(ns: Namespace) -> ExecutionResult:
  method = partial(
    clone_tier,
    tier_name=ns.tier,
    output_tier_names=ns.tiers,
    ignore_marks=ns.ignore_marks,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
