from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils import StringFormat
from text_utils.string_format import StringFormat
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument)
from textgrid_tools.app.tier.common import process_grids
from textgrid_tools.core import join_intervals_on_sentences
from textgrid_tools.core.interval_format import IntervalFormat


def init_files_join_intervals_on_sentences_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier to intervals containing sentences."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid files")
  parser.add_argument("tier", type=str, help="the tier on which the intervals should be joined")
  add_n_digits_argument(parser)
  parser.add_argument('--mark-format', choices=StringFormat,
                      type=StringFormat.__getitem__, default=StringFormat.TEXT, help="format of marks in tier")
  parser.add_argument('--mark-type', choices=IntervalFormat,
                      type=IntervalFormat.__getitem__, default=IntervalFormat.WORD, help="type of marks in tier")
  parser.add_argument("--strip-symbols", metavar="SYMBOL", type=str, nargs='*',
                      default=list(sorted(("\"", "'", "″", ",⟩", "›", "»", "′", "“", "”"))), help="symbols which should be temporary removed on word endings for sentence detection")
  parser.add_argument("--punctuation-symbols", metavar="SYMBOL", type=str, nargs='*',
                      default=list(sorted(("!", "?", ".", "¿", "¡", "。", "！", "？"))), help="symbols which indicate sentence endings")
  parser.add_argument("--output-tier", metavar="TIER", type=str, default=None,
                      help="tier on which the mapped content should be written to if not to tier")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="directory where to output the modified grid files if not to directory")
  add_overwrite_tier_argument(parser)
  add_overwrite_argument(parser)
  return files_join_intervals


def files_join_intervals(directory: Path, tiers: List[str], mark_format: StringFormat, mark_type: IntervalFormat, strip_symbols: List[str], punctuation_symbols: List[str], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  method = partial(
    join_intervals_on_sentences,
    punctuation_symbols=punctuation_symbols,
    strip_symbols=strip_symbols,
    tier_names=set(tiers),
    tiers_interval_format=mark_type,
    tiers_string_format=mark_format,
  )

  return process_grids(directory, n_digits, output_directory, overwrite, method)
