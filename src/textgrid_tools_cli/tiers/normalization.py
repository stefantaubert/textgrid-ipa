from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet
from text_utils.language import Language
from text_utils.string_format import StringFormat
from text_utils.symbol_format import SymbolFormat
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument,
                                       add_directory_argument,
                                       add_language_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_symbol_format, add_tiers_argument)
from textgrid_tools.core import normalize_tiers


def get_normalization_parser(parser: ArgumentParser):
  parser.description = "This command normalizes text on tiers."
  add_directory_argument(parser)
  add_tiers_argument(parser, "tiers which should be normalized")
  add_language_argument(parser, "tiers")
  add_symbol_format(parser, "tiers")
  add_string_format_argument(parser, "tiers")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_normalize_tiers


def app_normalize_tiers(directory: Path, tiers: OrderedSet[str], formatting: StringFormat, symbol_format: SymbolFormat, language: Language, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    normalize_tiers,
    language=language,
    text_format=symbol_format,
    tier_names=tiers,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
