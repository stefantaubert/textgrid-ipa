from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, cast

from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import get_grid_files, load_grid
from textgrid_tools.core.grid_stats_generation import print_stats
from tqdm import tqdm


def init_files_print_stats_parser(parser: ArgumentParser):
  parser.description = "This command generate statistics about the grid files."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--duration_threshold", type=float, default=0.002)
  parser.add_argument("--print_symbols_tiers", type=str, nargs='*', default="")
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  return files_print_stats


def files_print_stats(grid_folder_in: Path, duration_threshold: float, print_symbols_tiers: List[str], n_digits: int) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(grid_files)):
    logger.info(f"Calculating statistics for {file_stem} ...")

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)
    print_stats(grid_in, duration_threshold, set(print_symbols_tiers))
    logger.info("")
