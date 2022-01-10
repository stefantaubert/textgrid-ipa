from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, Optional, cast

from scipy.io.wavfile import read
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_audio_files,
                                       get_grid_files, load_grid, save_audio,
                                       save_grid)
from textgrid_tools.core.grid.duration_splitting import (
    can_split_grid_on_durations, split_grid_on_durations)
from tqdm import tqdm


def init_files_split_grid_on_durations_parser(parser: ArgumentParser):
  parser.description = "This command splits each interval into multiple grids."

  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grid and audio files")

  parser.add_argument("--duration", type=float, metavar="SECONDS",
                      help="maximum duration of consecutive intervals in an extract (in seconds)", default=10)
  parser.add_argument(
    "tier", type=str, help="the tier on which the intervals should be extracted (each other tier in grid needs to have at least the same interval boundaries)")
  parser.add_argument("--audio-directory", type=Path, metavar="PATH",
                      help="directory containing the audio files if not directory")
  parser.add_argument("--include-empty", action="store_true",
                      help="include empty intervals (i.e., those which contain no text or only whitespace) at the start/end of the final extracts")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="directory where to output the modified grid files if not to directory")
  parser.add_argument("--output-audio-directory", metavar='PATH', type=Path,
                      help="directory where to output the audio files if not to directory/output-directory")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return files_split_grid_on_durations


def files_split_grid_on_durations(directory: Path, tier: str, audio_directory: Path, duration: float, include_empty: bool, n_digits: int, output_directory: Optional[Path], output_audio_directory: Optional[Path], overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not directory.exists():
    logger.error("Textgrid folder does not exist!")
    return

  if audio_directory is None:
    audio_directory = directory

  if output_directory is None:
    output_directory = directory

  if output_audio_directory is None:
    output_audio_directory = output_directory

  grid_files = get_grid_files(directory)
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
  for file_stem in cast(Iterable[str], tqdm(common_files)):
    logger.info(f"Processing {file_stem} ...")

    grids_folder_out_abs = output_directory / file_stem
    audios_folder_out_abs = output_audio_directory / file_stem

    if (grids_folder_out_abs.exists() or audios_folder_out_abs.exists()) and not overwrite:
      logger.info("Target grids/audios already exist.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    audio_file_in_abs = audio_directory / audio_files[file_stem]
    sample_rate, audio_in = read(audio_file_in_abs)

    can_split = can_split_grid_on_durations(grid_in, audio_in, sample_rate, tier, duration)
    if not can_split:
      logger.info("Skipped.")
      continue

    try:
      grids_audios = split_grid_on_durations(
          grid_in, audio_in, sample_rate, tier, duration, include_empty, n_digits)
    except Exception:
      logger.info("Skipped.")
      continue

    logger.info("Saving...")
    for i, (new_grid, new_audio) in enumerate(tqdm(grids_audios)):
      grid_file_out_abs = grids_folder_out_abs / f"{i}.TextGrid"
      audio_file_out_abs = audios_folder_out_abs / f"{i}.wav"
      save_grid(grid_file_out_abs, new_grid)
      save_audio(audio_file_out_abs, new_audio, sample_rate)

  logger.info(f"Done. Written output to: {output_directory}")
