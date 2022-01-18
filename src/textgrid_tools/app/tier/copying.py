from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Optional

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument, copy_grid,
                                       get_grid_files, get_optional, load_grid,
                                       parse_existing_directory,
                                       parse_non_empty_or_whitespace, save_grid)
from textgrid_tools.app.validation import (DirectoryNotExistsError,
                                           ValidationError)
from textgrid_tools.core import copy_tier_to_grid


def get_copying_parser(parser: ArgumentParser):
  parser.description = "This command copies a tier in one grid to a tier in another grid."
  parser.add_argument("reference_directory", metavar="reference-directory", type=parse_existing_directory,
                      help="the directory containing the grid files with the content that should be mapped")
  parser.add_argument("reference_tier", metavar="reference-tier", type=parse_non_empty_or_whitespace,
                      help="tier which should be copied")
  parser.add_argument("directory", type=parse_existing_directory, metavar="directory",
                      help="directory containing the grid files on which the tier should be added")
  parser.add_argument("--tier", metavar="NAME", type=get_optional(parse_non_empty_or_whitespace), default=None,
                      help="tier on which the mapped content should be written if not to reference-tier.")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_copy_tier_to_grid


class DirectoriesAreNotDistinctError(ValidationError):
  def __init__(self, path: Path) -> None:
    super().__init__()
    self.path = path

  @classmethod
  def validate(cls, dir1: Path, dir2: Path):
    if dir1 == dir2:
      return cls(dir1)
    return None

  @property
  def default_message(self) -> str:
    return "Directories are not distinct!"


def app_copy_tier_to_grid(reference_directory: Path, reference_tier: str, directory: Path, tier: Optional[str], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if error := DirectoryNotExistsError.validate(reference_directory):
    logger.error(error.default_message)
    return False, False

  if error := DirectoryNotExistsError.validate(directory):
    logger.error(error.default_message)
    return False, False

  if error := DirectoriesAreNotDistinctError.validate(directory, reference_directory):
    logger.error(error.default_message)
    return False, False

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  ref_grid_files = get_grid_files(reference_directory)

  common_files = set(grid_files.keys()).intersection(ref_grid_files.keys())
  missing_grid_files = set(ref_grid_files.keys()).difference(grid_files.keys())
  missing_ref_grid_files = set(grid_files.keys()).difference(ref_grid_files.keys())

  if len(missing_grid_files) > 0:
    logger.info(f"{len(missing_grid_files)} grid files missing.")

  if len(missing_ref_grid_files) > 0:
    logger.info(f"{len(missing_ref_grid_files)} reference grid files missing.")

  logger.info(f"Found {len(common_files)} matching files.")

  total_success = True
  total_changed_anything = False
  for file_nr, file_stem in enumerate(common_files, start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(common_files)})...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists. Skipped.")
      continue

    ref_grid_file_in_abs = reference_directory / ref_grid_files[file_stem]
    ref_grid_in = load_grid(ref_grid_file_in_abs, n_digits)

    grid_file_in_abs = directory / grid_files[file_stem]
    grid = load_grid(grid_file_in_abs, n_digits)

    error, changed_anything = copy_tier_to_grid(ref_grid_in, reference_tier, grid, tier)

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
