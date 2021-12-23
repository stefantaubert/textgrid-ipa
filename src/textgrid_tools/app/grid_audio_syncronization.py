from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_audio_files,
                                       get_grid_files, load_grid, read_audio,
                                       save_grid)
from textgrid_tools.core.mfa.grid_audio_syncronization import (
    can_sync_grid_to_audio, sync_grid_to_audio)
from tqdm import tqdm


def init_files_sync_grids_parser(parser: ArgumentParser):
  parser.description = "This command synchronizes the grids minTime and maxTime according to the audio, i.e. if minTime is not zero, then the first interval will be set to start at zero and if the last interval is not ending at the total duration of the audio, it will be adjusted to it."
  parser.add_argument("input_directory", type=Path, metavar="input-directory",
                      help="the directory containing the grid files")
  parser.add_argument("audio_directory", type=Path, metavar="audio-directory",
                      help="the directory containing the audio files")
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  add_overwrite_argument(parser)
  return files_sync_grids


def files_sync_grids(input_directory: Path, audio_directory: Path, n_digits: int, output_directory: Optional[Path], overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not input_directory.exists():
    logger.error("Input directory does not exist!")
    return

  if not audio_directory.exists():
    logger.error("Audio directory does not exist!")
    return

  if output_directory is None:
    output_directory = input_directory

  grid_files = get_grid_files(input_directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  audio_files = get_audio_files(audio_directory)
  logger.info(f"Found {len(audio_files)} audio files.")

  common_files = set(grid_files.keys()).intersection(audio_files.keys())
  missing_grid_files = set(audio_files.keys()).difference(grid_files.keys())
  missing_audio_files = set(grid_files.keys()).difference(audio_files.keys())

  logger.info(f"{len(missing_grid_files)} grid files missing.")
  logger.info(f"{len(missing_audio_files)} audio files missing.")

  logger.info(f"Found {len(common_files)} matching files.")

  logger.info("Reading files...")
  all_successfull = True
  all_changed_anything = False
  for file_stem in cast(Iterable[str], tqdm(common_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grids already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = input_directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    audio_file_in_abs = audio_directory / audio_files[file_stem]
    sample_rate, audio_in = read_audio(audio_file_in_abs)

    can_sync = can_sync_grid_to_audio(grid_in, audio_in, sample_rate, n_digits)

    if not can_sync:
      logger.info("Skipped.")
      all_successfull = False
      continue

    changed_anything = sync_grid_to_audio(grid_in, audio_in, sample_rate, n_digits)
    all_changed_anything |= changed_anything

    if not changed_anything:
      logger.info("Didn't changed anything.")

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

  if not all_successfull:
    logger.info("Not all was successfull!")
  else:
    logger.info("All was successfull!")

  if not all_changed_anything:
    logger.info("Didn't changed anything on any file.")
  logger.info(f"Done. Written output to: {output_directory}")
