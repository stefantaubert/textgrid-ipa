from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional, Set

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import map_arpa_to_ipa


def init_map_arpa_tier_to_ipa_parser(parser: ArgumentParser):
  parser.description = "This command maps ARPA transcriptions to IPA."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files")
  parser.add_argument("tiers", metavar="tiers", type=str, nargs="+",
                      help="tiers which should be normalized")
  parser.add_argument('--tiers-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="format of tier")
  parser.add_argument("--replace-unknown", action="store_true",
                      help="replace unknown ARPA symbols with custom symbol")
  parser.add_argument("--symbol", metavar="SYMBOL", type=str,
                      help="replace unknown ARPA symbols with that symbol")
  parser.add_argument("--ignore", metavar="SYMBOL", type=str, nargs="*",
                      help="ignore these symbols while mapping")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return map_arpa_tier_to_ipa


def map_arpa_tier_to_ipa(directory: Path, tiers: List[str], tiers_format: StringFormat, replace_unknown: bool, replace_unknown_with: Optional[Symbol], ignore: Set[Symbol], n_digits: int, output_directory: Path, overwrite: bool) -> ExecutionResult:
  method = partial(
    map_arpa_to_ipa,
    ignore=set(ignore),
    replace_unknown=replace_unknown,
    replace_unknown_with=replace_unknown_with,
    tier_names=set(tiers),
    tiers_string_format=tiers_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
