from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import List, Optional

from text_utils import StringFormat
from text_utils.string_format import StringFormat
from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_chunksize_argument, add_grid_directory_argument,
                                       add_interval_format_argument, add_maxtaskperchild_argument,
                                       add_n_digits_argument, add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument, add_tiers_argument, parse_non_whitespace, parse_required)
from textgrid_tools.app.common import process_grids_mp
from textgrid_tools.core import join_intervals_on_sentences
from textgrid_tools.core.interval_format import IntervalFormat


def get_sentence_joining_parser(parser: ArgumentParser):
  parser.description = "This command joins adjacent intervals of a single tier to intervals containing sentences."
  add_grid_directory_argument(parser)
  add_tiers_argument(parser, "tiers on which the intervals should be joined")
  add_string_format_argument(parser, "tiers")
  add_interval_format_argument(parser, "tiers")
  parser.add_argument("--ignore", metavar="SYMBOL", type=parse_required, nargs='*',
                      default=list(sorted(("\"", "'", "″", ",⟩", "›", "»", "′", "“", "”"))), help="symbols which should be temporary ignored on word endings for sentence detection")
  parser.add_argument("--punctuation", metavar="SYMBOL", type=parse_required, nargs='*',
                      default=list(sorted(("!", "?", ".", "¿", "¡", "。", "！", "？"))), help="symbols which indicate sentence endings")
  add_output_directory_argument(parser)
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_join_intervals_on_sentences


def app_join_intervals_on_sentences(directory: Path, tiers: List[str], formatting: StringFormat, content: IntervalFormat, ignore: List[str], punctuation: List[str], n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    join_intervals_on_sentences,
    punctuation_symbols=set(punctuation),
    strip_symbols=ignore,
    tier_names=set(tiers),
    tiers_interval_format=content,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
