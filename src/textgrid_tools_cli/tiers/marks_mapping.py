import json
from argparse import ArgumentParser, Namespace
from functools import partial

from ordered_set import OrderedSet

from textgrid_tools import map_marks
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_dry_run_argument,
                                       add_encoding_argument, add_maxtaskperchild_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument, get_optional,
                                       parse_existing_file, parse_non_empty)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_marks_mapping_parser(parser: ArgumentParser):
  parser.description = "This command maps marks."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers which should be transcribed")
  parser.add_argument("mapping", type=parse_existing_file,
                      metavar="MAP-PATH", help="path to mapping json")
  parser.add_argument("--replace-unmapped", action="store_true",
                      help="replace unmapped marks with a custom mark")
  parser.add_argument("--mark", metavar="UNMAPPED-MARK", type=get_optional(parse_non_empty),
                      help="custom mark to replace unmapped symbols", default=None)
  parser.add_argument("--ignore", metavar="IGNORE-MARK", type=str, nargs="*",
                      help="ignore mappings for these marks, i.e., keep them as they are", action=ConvertToOrderedSetAction, default=OrderedSet(("",)))
  add_encoding_argument(parser, "encoding of grids and mapping")
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  add_dry_run_argument(parser)
  return map_marks_ns


def map_marks_ns(ns: Namespace) -> ExecutionResult:

  try:
    with ns.mapping.open(mode='r', encoding=ns.encoding) as json_file:
      mapping_content = json.load(json_file)
  except Exception as ex:
    logger = init_and_get_console_logger(__name__)
    logger.error("Mapping couldn't be read!")
    flogger = get_file_logger()
    flogger.exception(ex)
    return False, False

  method = partial(
    map_marks,
    ignore=ns.ignore,
    mapping=mapping_content,
    replace_unmapped=ns.replace_unmapped,
    replace_unmapped_with=ns.mark,
    tier_names=ns.tiers,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
