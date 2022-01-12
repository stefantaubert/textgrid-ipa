from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Callable, Optional, cast

from textgrid.textgrid import TextGrid
from textgrid_tools.app.helper import (copy_grid, get_grid_files, load_grid,
                                       save_grid)
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core.globals import ExecutionResult
from tqdm import tqdm


def process_grids(directory: Path, n_digits: int, output_directory: Optional[Path], overwrite: bool, method: Callable[[TextGrid], ExecutionResult]) -> ExecutionResult:
  logger = getLogger(__name__)

  if error := DirectoryNotExistsError.validate(directory):
    logger.error(error.default_message)
    return False, False

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)

  total_success = True
  total_changed_anything = False
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_out_abs = output_directory / rel_path

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists. Skipped.")
      continue

    grid_file_in_abs = directory / rel_path
    grid = load_grid(grid_file_in_abs, n_digits)

    error, changed_anything = method(grid)

    success = error is None
    total_success &= success
    total_changed_anything |= changed_anything

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    if changed_anything:
      save_grid(grid_file_out_abs, grid)
    elif directory != output_directory:
      copy_grid(grid_file_in_abs, grid_file_out_abs)

  return total_success, total_changed_anything
