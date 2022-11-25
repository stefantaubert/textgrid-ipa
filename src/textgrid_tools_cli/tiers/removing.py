from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import remove_tiers
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument)


def get_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes tiers from a grid."
  add_directory_argument(parser)
  add_tiers_argument(parser, "the tiers which should be removed")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_remove_tiers


def app_remove_tiers(ns: Namespace) -> ExecutionResult:
  method = partial(
    remove_tiers,
    tier_names=ns.tiers,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
