from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, cast

from text_utils import StringFormat
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_overwrite_tier_argument,
                                       get_grid_files, load_grid, save_grid)
from textgrid_tools.core.intervals.joining.sentence_joining import (
    can_join_intervals, join_intervals)
from textgrid_tools.core.mfa.interval_format import IntervalFormat
from tqdm import tqdm


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


def files_join_intervals(directory: Path, tier: str, mark_format: StringFormat, mark_type: IntervalFormat, output_tier: Optional[str], strip_symbols: List[str], punctuation_symbols: List[str], overwrite_tier: bool, n_digits: int, output_directory: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not directory.exists():
    logger.error(f"Directory \"{directory}\" does not exist!")
    return

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grid already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    can_join = can_join_intervals(grid_in, tier, output_tier, overwrite_tier)
    if not can_join:
      logger.info("Skipped.")
      continue

    join_intervals(grid_in, tier, mark_format, mark_type,
                   set(strip_symbols), set(punctuation_symbols), output_tier, overwrite_tier)

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  logger.info(f"Done. Written output to: {output_directory}")
