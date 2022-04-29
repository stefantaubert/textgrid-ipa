import json
from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet

from textgrid_utils import map_marks
from textgrid_utils_cli.common import process_grids_mp
from textgrid_utils_cli.globals import ExecutionResult
from textgrid_utils_cli.helper import (ConvertToOrderedSetAction, add_chunksize_argument,
                                       add_directory_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_digits_argument,
                                       add_n_jobs_argument, add_output_directory_argument,
                                       add_overwrite_argument, add_tiers_argument, get_optional,
                                       parse_existing_file, parse_non_empty)


def get_marks_mapping_parser(parser: ArgumentParser):
  parser.description = "This command maps marks."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers which should be transcribed")
  parser.add_argument("mapping", type=parse_existing_file,
                      metavar="mapping", help="path to mapping json")
  parser.add_argument("--replace-unmapped", action="store_true",
                      help="replace unmapped marks with a custom mark")
  parser.add_argument("--mark", metavar="SYMBOL", type=get_optional(parse_non_empty),
                      help="custom mark to replace unmapped symbols", default=None)
  parser.add_argument("--ignore", metavar="SYMBOL", type=str, nargs="*",
                      help="ignore these marks while mapping, i.e., keep them as they are", action=ConvertToOrderedSetAction, default=OrderedSet(("",)))
  add_encoding_argument(parser, "encoding of mapping")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return map_marks_ns


def map_marks_ns(directory: Path, mapping: Path, encoding: str, tiers: OrderedSet[str], replace_unmapped: bool, mark: Optional[str], ignore: OrderedSet[str], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:

  try:
    with mapping.open(mode='r', encoding=encoding) as json_file:
      mapping_content = json.load(json_file)
  except Exception as ex:
    logger = getLogger(__name__)
    logger.error("Mapping couldn't be read!")
    logger.exception(ex)
    return False, False

  method = partial(
    map_marks,
    ignore=ignore,
    mapping=mapping_content,
    replace_unmapped=replace_unmapped,
    replace_unmapped_with=mark,
    tier_names=tiers,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
