from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional, Set

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (ConvertToOrderedSetAction,
                                       add_chunksize_argument,
                                       add_grid_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument, get_optional,
                                       parse_non_empty)
from textgrid_tools.core import map_arpa_to_ipa


def get_arpa_to_ipa_transcription_parser(parser: ArgumentParser):
  parser.description = "This command maps ARPA transcriptions to IPA."
  add_grid_directory_argument(parser)
  add_tiers_argument(parser, "tiers which should be transcribed")
  add_string_format_argument(parser, "tiers")
  parser.add_argument("--replace-unknown", action="store_true",
                      help="replace unknown ARPA symbols with a custom symbol")
  parser.add_argument("--symbol", metavar="SYMBOL", type=get_optional(parse_non_empty),
                      help="custom symbol to replace unknown ARPA symbols")
  parser.add_argument("--ignore", metavar="SYMBOL", type=parse_non_empty, nargs="*",
                      help="ignore these symbols while transcription, i.e., keep them as they are", action=ConvertToOrderedSetAction)
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_map_arpa_to_ipa


def app_map_arpa_to_ipa(directory: Path, tiers: List[str], formatting: StringFormat, replace_unknown: bool, symbol: Optional[Symbol], ignore: Set[Symbol], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    map_arpa_to_ipa,
    ignore=set(ignore),
    replace_unknown=replace_unknown,
    replace_unknown_with=symbol,
    tier_names=tiers,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
