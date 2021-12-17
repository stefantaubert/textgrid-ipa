from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, cast

from scipy.io.wavfile import read
from textgrid_tools.app.helper import (get_audio_files, get_grid_files,
                                       load_grid, save_grid)
from textgrid_tools.core.mfa.grid_audio_syncronization import (can_sync_grid_to_audio,
                                                        sync_grid_to_audio)
from tqdm import tqdm


def init_files_sync_grids_parser(parser: ArgumentParser):
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--audio_folder_in", type=Path, required=True)
  parser.add_argument("--n_digits", type=int, required=True)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_sync_grids


def files_sync_grids(grid_folder_in: Path, audio_folder_in: Path, n_digits: int, grid_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if not audio_folder_in.exists():
    logger.error("Audio folder does not exist!")
    return

  grid_files = get_grid_files(grid_folder_in)
  logger.info(f"Found {len(grid_files)} grid files.")

  audio_files = get_audio_files(audio_folder_in)
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

    grid_file_out_abs = grid_folder_out / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Target grids already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    audio_file_in_abs = audio_folder_in / grid_files[file_stem]
    sample_rate, audio_in = read(audio_file_in_abs)

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
  logger.info(f"Done. Written output to: {grid_folder_out}")
