from argparse import ArgumentParser, Namespace

from tqdm import tqdm

from textgrid_tools import sync_grid_to_audio
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       get_audio_files, get_grid_files, get_optional,
                                       parse_existing_directory, read_audio, try_copy_grid,
                                       try_load_grid, try_save_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_audio_synchronization_parser(parser: ArgumentParser):
  parser.description = "This command synchronizes the grids minTime and maxTime according to the audio, i.e., if minTime is not zero, then the first interval will be set to start at zero and if the last interval is not ending at the total duration of the audio, it will be adjusted to it."
  add_directory_argument(parser)
  parser.add_argument("--audio-directory", type=get_optional(parse_existing_directory), metavar="PATH",
                      help="directory containing the audio files if not the same directory")
  add_encoding_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  return app_sync_grid_to_audio


def app_sync_grid_to_audio(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  audio_directory = ns.audio_directory
  if audio_directory is None:
    audio_directory = ns.directory

  output_directory = ns.output_directory
  if output_directory is None:
    output_directory = ns.directory

  grid_files = get_grid_files(ns.directory)
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

  for file_nr, file_stem in enumerate(tqdm(common_files), start=1):
    flogger.info(f"Processing {file_stem}")
    grid_file_out_abs = output_directory / grid_files[file_stem]
    if grid_file_out_abs.exists() and not ns.overwrite:
      flogger.info("Grid already exists. Skipped.")
      continue

    grid_file_in_abs = ns.directory / grid_files[file_stem]
    error, grid = try_load_grid(grid_file_in_abs, ns.encoding)

    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue
    assert grid is not None

    audio_file_in_abs = audio_directory / audio_files[file_stem]
    sample_rate, audio_in = read_audio(audio_file_in_abs)
    error, changed_anything = sync_grid_to_audio(grid, audio_in, sample_rate, flogger)
    success = error is None
    total_success &= success
    total_changed_anything |= changed_anything

    if not success:
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue

    if changed_anything:
      error = try_save_grid(grid_file_out_abs, grid, ns.encoding)
      if error is not None:
        flogger.debug(error.exception)
        flogger.error(error.default_message)
        flogger.info("Skipped.")
        total_success = False
        continue
    elif ns.directory != output_directory:
      error = try_copy_grid(grid_file_in_abs, grid_file_out_abs)
      if error is not None:
        flogger.debug(error.exception)
        flogger.error(error.default_message)
        flogger.info("Skipped.")
        total_success = False
        continue

  return total_success, total_changed_anything
