from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Iterable, List, Optional, cast

from ordered_set import OrderedSet
from scipy.io.wavfile import read
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_audio_files,
                                       get_grid_files, load_grid, save_audio,
                                       save_grid)
from textgrid_tools.core.mfa.grid_interval_removal import (
    can_remove_intervals, remove_intervals)
from tqdm import tqdm


def init_files_remove_intervals_parser(parser: ArgumentParser):
  parser.description = "This command removes empty intervals and/or intervals containing specific marks. The corresponding audios can be adjusted, too."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="the directory containing grid files, from which intervals should be removed")
  parser.add_argument("tier", type=str, help="the tier on which intervals should be removed")
  parser.add_argument("--audio-directory", type=Path, metavar='',
                      help="the directory containing audio files")
  parser.add_argument("--marks", type=str, nargs='*',
                      help="remove intervals containing these marks")
  parser.add_argument("--empty", action="store_true",
                      help="remove empty intervals")
  add_n_digits_argument(parser)
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified grid files if not to input-directory")
  parser.add_argument("--output-audio-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified audio files if not to audio-directory.")
  add_overwrite_argument(parser)
  return files_remove_intervals


def files_remove_intervals(directory: Path, audio_directory: Path, tier: str, marks: Optional[List[str]], empty: bool, n_digits: int, output_directory: Optional[Path], output_audio_directory: Optional[Path], overwrite: bool) -> None:
  logger = getLogger(__name__)

  if not directory.exists():
    logger.error(f"Directory \"{directory}\" does not exist!")
    return

  if audio_directory is not None and not audio_directory.exists():
    logger.error(f"Directory \"{audio_directory}\" does not exist!")
    return

  remove_marks_set = set(marks) if marks is not None else set()

  if len(remove_marks_set) == 0 and not empty:
    logger.info("Please set marks and/or remove empty!")
    return

  if output_directory is None:
    output_directory = directory

  if output_audio_directory is None:
    output_audio_directory = audio_directory

  logger.info(f"Marks: {remove_marks_set} and empty: {'yes' if empty else 'no'}")

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid files.")
  print(grid_files)

  if audio_directory is not None:
    audio_files = get_audio_files(audio_directory)
    logger.info(f"Found {len(audio_files)} audio files.")

    common_files = OrderedSet(grid_files.keys()).intersection(audio_files.keys())
    missing_grid_files = set(audio_files.keys()).difference(grid_files.keys())
    missing_audio_files = set(grid_files.keys()).difference(audio_files.keys())

    logger.info(f"{len(missing_grid_files)} grid files missing.")
    logger.info(f"{len(missing_audio_files)} audio files missing.")

    logger.info(f"Found {len(common_files)} matching files.")
  else:
    audio_files = {}
    common_files = OrderedSet(grid_files.keys())

  logger.info("Reading files...")
  for file_stem in cast(Iterable[str], tqdm(common_files)):
    logger.info(f"Processing {file_stem} ...")

    grid_file_out_abs = output_directory / grid_files[file_stem]

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid file already exists.")
      logger.info("Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    grid_in = load_grid(grid_file_in_abs, n_digits)

    sample_rate = None
    audio_in = None
    audio_provided = file_stem in audio_files
    if audio_provided:
      audio_file_out_abs = output_audio_directory / audio_files[file_stem]
      if audio_file_out_abs.exists() and not overwrite:
        logger.info("Audio file already exists.")
        logger.info("Skipped.")
        continue

      audio_file_in_abs = audio_directory / audio_files[file_stem]
      sample_rate, audio_in = read(audio_file_in_abs)

    can_remove = can_remove_intervals(grid_in, audio_in, sample_rate, tier,
                                      remove_marks_set, empty)
    if not can_remove:
      logger.info("Skipped.")
      continue

    try:
      new_audio = remove_intervals(grid_in, audio_in, sample_rate, tier,
                                   remove_marks_set, empty, n_digits)
    except Exception:
      logger.info("Skipped.")
      continue

    logger.info("Saving...")
    save_grid(grid_file_out_abs, grid_in)

    if audio_provided:
      assert new_audio is not None
      save_audio(audio_file_out_abs, new_audio, sample_rate)

  logger.info(f"Done.")
