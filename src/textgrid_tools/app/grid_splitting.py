import argparse
from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, cast

from scipy.io.wavfile import read
from textgrid_tools.app.globals import DEFAULT_N_DIGITS
from textgrid_tools.app.helper import (get_audio_files, get_grid_files,
                                       load_grid, save_audio, save_grid)
from textgrid_tools.core.mfa.grid_splitting import split_grid
from tqdm import tqdm


def init_files_split_grid_parser(parser: ArgumentParser):
  parser.description = "This command splits a grid into multiple grids."
  parser.add_argument("--grid_folder_in", type=Path, required=True)
  parser.add_argument("--audio_folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier", type=str, required=True)
  parser.add_argument("--split_marks", type=str, nargs='+', required=True)
  parser.add_argument("--n_digits", type=int, default=DEFAULT_N_DIGITS)
  parser.add_argument("--grid_folder_out", type=Path, required=True)
  parser.add_argument("--audio_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_split_grid


def files_split_grid(grid_folder_in: Path, audio_folder_in: Path, reference_tier: str, split_marks: List[str], n_digits: int, grid_folder_out: Path, audio_folder_out: Path, overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not grid_folder_in.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if not audio_folder_in.exists():
    logger.error("Audio folder does not exist!")
    return

  split_marks_set = set(split_marks)
  if len(split_marks_set) == 0:
    logger.error("No split marks provided.")
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
  for file_stem in cast(Iterable[str], tqdm(common_files)):
    logger.info(f"Processing {file_stem} ...")

    grids_folder_out_abs = grid_folder_out / file_stem
    audios_folder_out_abs = audio_folder_out / file_stem

    if (grids_folder_out_abs.exists() or audios_folder_out_abs.exists()) and not overwrite:
      logger.info("Target grids/audios already exist.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = grid_folder_in / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    audio_file_in_abs = audio_folder_in / audio_files[file_stem]
    sample_rate, audio_in = read(audio_file_in_abs)
    success, grids_audios = split_grid(
      grid_in, audio_in, sample_rate, reference_tier, split_marks_set, n_digits=n_digits)

    if success:
      assert grids_audios is not None
      logger.info("Saving...")
      for i, (new_grid, new_audio) in enumerate(tqdm(grids_audios)):
        grid_file_out_abs = grids_folder_out_abs / f"{i}.TextGrid"
        audio_file_out_abs = audios_folder_out_abs / f"{i}.wav"
        save_grid(grid_file_out_abs, new_grid)
        save_audio(audio_file_out_abs, new_audio, sample_rate)

  logger.info(f"Done. Written output to: {grid_folder_out}")
