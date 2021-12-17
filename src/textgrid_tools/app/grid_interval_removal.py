from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, cast

from scipy.io.wavfile import read
from textgrid_tools.app.helper import (get_audio_files, get_grid_files,
                                       load_grid, save_audio, save_grid)
from textgrid_tools.core.mfa.grid_interval_removal import (
    can_remove_intervals, remove_intervals)
from tqdm import tqdm


def init_files_split_grid_parser(parser: ArgumentParser):
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--audio_folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier", type=str, required=True)
  parser.add_argument("--remove_marks", type=str, nargs='+', required=True)
  parser.add_argument("--remove_empty", action="store_true")
  parser.add_argument("--n_digits", type=int, required=True)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--audio_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_split_grid


def files_split_grid(grid_folder_in: Path, audio_folder_in: Path, reference_tier: str, remove_marks: Optional[List[str]], remove_empty: bool, n_digits: int, grid_folder_out: Path, audio_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if not audio_folder_in.exists():
    logger.error("Audio folder does not exist!")
    return

  remove_marks_set = set(remove_marks) if remove_marks is not None else set()

  if len(remove_marks_set) == 0 and not remove_empty:
    logger.info("Please set marks and/or remove_empty!")
    return

  logger.info(f"Marks: {remove_marks_set} and empty: {'yes' if remove_empty else 'no'}")

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
  for file_stem in cast(Iterable[str], tqdm(common_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = grid_folder_out / grid_files[file_stem]
    audio_file_out_abs = audio_folder_out / audio_files[file_stem]

    if (grid_file_out_abs.exists() or audio_file_out_abs.exists()) and not overwrite:
      logger.info("Target grids/audios already exist.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    audio_file_in_abs = audio_folder_in / grid_files[file_stem]
    sample_rate, audio_in = read(audio_file_in_abs)

    can_remove = can_remove_intervals(grid_in, audio_in, sample_rate, reference_tier,
                                      remove_marks_set, remove_empty)
    if not can_remove:
      logger.info("Skipped.")
      continue

    try:
      new_audio = remove_intervals(grid_in, audio_in, sample_rate, reference_tier,
                                   remove_marks_set, remove_empty, n_digits)
    except Exception:
      logger.info("Skipped.")
      continue

    assert new_audio is not None
    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)
    save_audio(audio_file_out_abs, new_audio, sample_rate)

  logger.info(f"Done. Written output to: {grid_folder_out}")
