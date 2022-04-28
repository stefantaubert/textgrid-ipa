from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import List, Optional

from ordered_set import OrderedSet
from scipy.io.wavfile import read
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction,
                                       add_directory_argument,
                                       add_n_digits_argument,
                                       add_overwrite_argument,
                                       add_tier_argument, copy_audio,
                                       copy_grid, get_audio_files,
                                       get_grid_files, get_optional, try_load_grid,
                                       parse_existing_directory,
                                       parse_non_empty, parse_path, save_audio,
                                       save_grid)
from textgrid_tools.core import remove_intervals
from textgrid_tools.core.intervals.removing import NothingDefinedToRemoveError

# TODO tiers support


def get_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes empty intervals and/or intervals containing specific marks. The corresponding audios can be adjusted, too."
  add_directory_argument(parser, "directory containing the grids and the corresponding audios")
  add_tier_argument(parser, "tier on which intervals should be removed")
  parser.add_argument("--audio-directory", type=get_optional(parse_existing_directory), metavar='PATH',
                      help="directory containing the audios if not directory")
  parser.add_argument("--ignore-audio", action="store_true",
                      help="ignore audios")
  parser.add_argument("--marks", type=parse_non_empty, nargs='*', metavar="MARK",
                      help="remove intervals containing these marks", default=[], action=ConvertToOrderedSetAction)
  parser.add_argument("--pauses", action="store_true",
                      help="remove pause intervals")
  parser.add_argument("-out", "--output-directory", metavar='PATH', type=get_optional(parse_path),
                      help="directory where to output the grids and audios if not to the same directory")
  parser.add_argument("--output-audio-directory", metavar='PATH', type=get_optional(parse_path),
                      help="the directory where to output the modified audio files if not to directory.")
  add_n_digits_argument(parser)
  add_overwrite_argument(parser)
  return app_remove_intervals


def app_remove_intervals(directory: Path, audio_directory: Optional[Path], ignore_audio: bool, tier: str, marks: OrderedSet[str], pauses: bool, n_digits: int, output_directory: Optional[Path], output_audio_directory: Optional[Path], overwrite: bool) -> ExecutionResult:
  logger = getLogger(__name__)

  if error := NothingDefinedToRemoveError.validate(marks, pauses):
    logger.error(error.default_message)
    return False, False

  if audio_directory is None and not ignore_audio:
    audio_directory = directory

  if output_directory is None:
    output_directory = directory

  if output_audio_directory is None:
    output_audio_directory = directory

  logger.debug(f"Marks: {'|'.join(OrderedSet(marks))}")
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

    grid_file_out_abs = output_directory / grid_files[file_stem]
    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists. Skipped.")
      continue

    grid_file_in_abs = directory / grid_files[file_stem]
    error, grid = try_load_grid(grid_file_in_abs, n_digits)

    if error:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue
    assert grid is not None

    sample_rate = None
    audio = None
    audio_provided = file_stem in audio_files
    if audio_provided:
      assert output_audio_directory is not None
      audio_file_out_abs = output_audio_directory / audio_files[file_stem]
      if audio_file_out_abs.exists() and not overwrite:
        logger.info("Audio file already exists. Skipped.")
        continue

      audio_file_in_abs = audio_directory / audio_files[file_stem]
      sample_rate, audio = read(audio_file_in_abs)

    (error, changed_anything), new_audio = remove_intervals(grid, audio, sample_rate, tier,
                                                            marks, pauses, n_digits)

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

    if audio_provided:
      assert new_audio is not None
      if changed_anything:
        save_audio(audio_file_out_abs, new_audio, sample_rate)
      elif directory != output_directory:
        copy_audio(audio_file_out_abs, audio_file_in_abs)

  return total_success, total_changed_anything
