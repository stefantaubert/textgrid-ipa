from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Optional

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.helper import (add_grid_directory_argument,
                                       add_n_digits_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument, copy_grid,
                                       get_audio_files, get_grid_files,
                                       load_grid, read_audio, save_grid)
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core import sync_grid_to_audio


def get_audio_synchronization_parser(parser: ArgumentParser):
  parser.description = "This command synchronizes the grids minTime and maxTime according to the audio, i.e. if minTime is not zero, then the first interval will be set to start at zero and if the last interval is not ending at the total duration of the audio, it will be adjusted to it."
  add_grid_directory_argument(parser)
  parser.add_argument("--audio-directory", type=Path, metavar="PATH",
                      help="directory containing the audio files if not the same directory")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_sync_grid_to_audio


def app_sync_grid_to_audio(directory: Path, audio_directory: Optional[Path], n_digits: int, output_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if error := DirectoryNotExistsError.validate(directory):
    logger.error(error.default_message)
    return False, False

  if audio_directory is not None:
    if error := DirectoryNotExistsError.validate(audio_directory):
      logger.error(error.default_message)
      return False, False
  else:
    audio_directory = directory

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  audio_files = get_audio_files(audio_directory)

  common_files = set(grid_files.keys()).intersection(audio_files.keys())
  missing_grid_files = set(audio_files.keys()).difference(grid_files.keys())
  missing_audio_files = set(grid_files.keys()).difference(audio_files.keys())

  if len(missing_grid_files) > 0:
    logger.info(f"{len(missing_grid_files)} grid files missing.")

  if len(missing_audio_files) > 0:
    logger.info(f"{len(missing_audio_files)} audio files missing.")

  #logger.info(f"Found {len(common_files)} matching files.")

  total_success = True
  total_changed_anything = False
  for file_nr, file_stem in enumerate(common_files, start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(common_files)})...")
    grid_file_out_abs = output_directory / grid_files[file_stem]
    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists. Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    grid = load_grid(grid_file_in_abs, n_digits)

    audio_file_in_abs = audio_directory / audio_files[file_stem]
    sample_rate, audio_in = read_audio(audio_file_in_abs)

    error, changed_anything = sync_grid_to_audio(grid, audio_in, sample_rate, n_digits)

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
