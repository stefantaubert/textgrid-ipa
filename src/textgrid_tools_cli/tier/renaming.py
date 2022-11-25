from argparse import ArgumentParser, Namespace
from functools import partial

from textgrid_tools import rename_tier
from textgrid_tools.validation import NonDistinctTiersError
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tier_argument, parse_non_empty_or_whitespace)
from textgrid_tools_cli.logging_configuration import init_and_get_console_logger


def get_renaming_parser(parser: ArgumentParser):
  parser.description = "This command renames a tier."
  add_directory_argument(parser)
  add_tier_argument(parser, "tier which should be renamed")
  parser.add_argument("name", type=parse_non_empty_or_whitespace, metavar="NEW-NAME",
                      help="new name of tier")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return app_rename_tier


def app_rename_tier(ns: Namespace) -> ExecutionResult:
  assert len(ns.name.strip()) > 0

  if error := NonDistinctTiersError.validate(ns.tier, ns.name):
    logger = init_and_get_console_logger(__name__)
    logger.error(error.default_message)
    return False, False

  method = partial(
    rename_tier,
    tier_name=ns.tier,
    output_tier_name=ns.name,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
