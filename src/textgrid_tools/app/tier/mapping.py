from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional, Set

from text_utils.string_format import StringFormat
from text_utils.types import Symbol
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument)
from textgrid_tools.app.common import process_grids
from textgrid_tools.core import map_tier


def get_mapping_parser(parser: ArgumentParser):
  parser.description = "This command maps the content of a tier to another tier while ignoring pause-intervals."
  add_grid_directory_argument(parser)
  parser.add_argument("tier", metavar="tier", type=str,
                      help="tier which should be mapped")
  parser.add_argument("target_tiers", metavar="target-tiers",
                      type=str, nargs="+", help="tiers to which the content should be mapped")
  add_string_format_argument(parser, "--tier-format", "format of tier and target-tiers")
  add_string_format_argument(parser, "--target-tiers-format", "format of target-tiers")
  parser.add_argument("--include-pauses", action="store_true",
                      help="include mapping from and to pause intervals, i.e., those which contain nothing or only whitespace")
  parser.add_argument("--ignore", type=str, nargs="*",
                      metavar="MARK", help="ignore these marks", default=[])
  parser.add_argument("--ignore-symbols", type=str, nargs="*",
                      metavar="SYMBOL", help="ignore marks that contain only these symbols")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_map_tier


def app_map_tier(directory: Path, tier: str, tier_format: StringFormat, target_tiers: Set[str], target_tiers_format: StringFormat, include_pauses: bool, ignore: Set[str], ignore_symbols: Set[Symbol], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    map_tier,
    ignore_marks=ignore,
    include_pauses=include_pauses,
    only_symbols=ignore_symbols,
    target_tier_names=set(target_tiers),
    targets_string_format=target_tiers_format,
    tier_name=tier,
    tier_string_format=tier_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
