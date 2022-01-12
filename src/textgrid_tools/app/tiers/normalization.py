from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils.language import Language
from text_utils.string_format import StringFormat
from text_utils.symbol_format import SymbolFormat
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument)
from textgrid_tools.app.common import process_grids
from textgrid_tools.core import normalize_tiers


def get_normalization_parser(parser: ArgumentParser):
  parser.description = "This command normalizes text on multiple tiers."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files")
  parser.add_argument("tiers", metavar="tiers", type=str, nargs="+",
                      help="tiers which should be normalized")
  parser.add_argument('--language', choices=Language,
                      type=Language.__getitem__, default=Language.ENG, help="language of tiers")
  parser.add_argument('--text-format', choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, default=SymbolFormat.GRAPHEMES, help="format of text")
  parser.add_argument('--tier-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="format of tier")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_normalize_tiers


def app_normalize_tiers(directory: Path, tiers: List[str], tier_format: StringFormat, text_format: SymbolFormat, language: Language, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    normalize_tiers,
    language=language,
    text_format=text_format,
    tier_names=set(tiers),
    tiers_string_format=tier_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
