from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet
from scipy.io.wavfile import read
from textgrid_tools.app.helper import (add_n_digits_argument,
                                       add_overwrite_argument, get_audio_files,
                                       get_grid_files, load_grid, save_audio,
                                       save_grid)
from textgrid_tools.app.validation import DirectoryNotExistsError
from textgrid_tools.core import split_grid_on_intervals
from tqdm import tqdm


def get_splitting_parser(parser: ArgumentParser):
  parser.description = "This command splits a grid into multiple grids."
  parser.add_argument("directory", type=Path, metavar="directory",
                      help="directory containing the grids and audios")
  parser.add_argument("tier", type=str, metavar="tier",
                      help="tier on which intervals should be removed")
  parser.add_argument("--audio-directory", type=Path, metavar='PATH',
                      help="directory containing the audios if not directory")
  parser.add_argument("--include-pauses", action="store_true",
                      help="include pause intervals")
  parser.add_argument("--ignore-audio", action="store_true",
                      help="ignore audios")
  parser.add_argument("--output-directory", metavar='PATH', type=Path,
                      help="directory where to output the grids and audios if not to the same directory")
  parser.add_argument("--output-audio-directory", metavar='PATH', type=Path,
                      help="the directory where to output the modified audios if not to directory/audio-directory.")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_split_grid_on_intervals


def app_split_grid_on_intervals(directory: Path, audio_directory: Optional[Path], tier: str, include_pauses: bool, ignore_audio: bool, n_digits: int, output_directory: Optional[Path], output_audio_directory: Optional[Path], overwrite: bool) -> None:
  logger = getLogger(__name__)

  if error := DirectoryNotExistsError.validate(directory):
    logger.error(error.default_message)
    return False, False

  if not ignore_audio and audio_directory is not None and (error := DirectoryNotExistsError.validate(audio_directory)):
    logger.error(error.default_message)
    return False, False

  if audio_directory is None and not ignore_audio:
    audio_directory = directory

  if output_directory is None:
    output_directory = directory

  if output_audio_directory is None:
    output_audio_directory = audio_directory

  grid_files = get_grid_files(directory)

  audio_files = {}
  if not ignore_audio:
    assert audio_directory is not None
    audio_files = get_audio_files(audio_directory)

    missing_grid_files = set(audio_files.keys()).difference(grid_files.keys())
    missing_audio_files = set(grid_files.keys()).difference(audio_files.keys())

    if len(missing_grid_files) > 0:
      logger.info(f"{len(missing_grid_files)} grid files missing.")

    if len(missing_audio_files) > 0:
      logger.info(f"{len(missing_audio_files)} audio files missing.")

    # logger.info(f"Found {len(common_files)} matching files.")
    common_files = OrderedSet(grid_files.keys()).intersection(audio_files.keys())
  else:
    common_files = OrderedSet(grid_files.keys())

  total_success = True
  total_changed_anything = False
  for file_nr, file_stem in enumerate(common_files, start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(common_files)})...")

    grid_file_in_abs = directory / grid_files[file_stem]
    grid = load_grid(grid_file_in_abs, n_digits)

    sample_rate = None
    audio = None
    audio_provided = file_stem in audio_files
    if audio_provided:
      assert output_audio_directory is not None
      audio_file_in_abs = audio_directory / audio_files[file_stem]
      sample_rate, audio = read(audio_file_in_abs)

    (error, changed_anything), grids_audios = split_grid_on_intervals(
      grid, audio, sample_rate, tier, include_pauses, n_digits)

    success = error is None
    total_success &= success
    total_changed_anything |= changed_anything

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    assert grids_audios is not None
    for i, (new_grid, new_audio) in enumerate(tqdm(grids_audios)):
      grid_file_out_abs = output_directory / file_stem / f"{i}.TextGrid"
      if grid_file_out_abs.exists() and not overwrite:
        logger.info(f"Grid {i} already exists. Skipped.")
      else:
        save_grid(grid_file_out_abs, new_grid)
      if audio_provided:
        assert new_audio is not None
        audio_file_out_abs = output_audio_directory / file_stem / f"{i}.wav"
        if audio_file_out_abs.exists() and not overwrite:
          logger.info(f"Audio file {i} already exists. Skipped.")
        else:
          save_audio(audio_file_out_abs, new_audio, sample_rate)

  return total_success, total_changed_anything
