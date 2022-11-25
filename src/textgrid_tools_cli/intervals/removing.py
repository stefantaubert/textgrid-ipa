from argparse import ArgumentParser, Namespace

from ordered_set import OrderedSet
from scipy.io.wavfile import read
from tqdm import tqdm

from textgrid_tools import remove_intervals
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToOrderedSetAction, add_directory_argument,
                                       add_encoding_argument, add_overwrite_argument,
                                       add_tier_argument, copy_audio, get_audio_files,
                                       get_grid_files, get_optional, parse_existing_directory,
                                       parse_path, save_audio, try_copy_grid, try_load_grid,
                                       try_save_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger

# TODO maybe tiers support


def get_removing_parser(parser: ArgumentParser):
  parser.description = "This command removes empty intervals and/or intervals containing specific marks. The corresponding audios can be adjusted, too."
  add_directory_argument(parser, "directory containing the grids and the corresponding audios")
  add_tier_argument(parser, "tier on which intervals should be removed")
  parser.add_argument("marks", type=str, nargs='+', metavar="MARK",
                      help="remove intervals containing these marks", action=ConvertToOrderedSetAction)
  parser.add_argument("-m", "--mode", type=str, choices=["all", "start", "end", "both"], metavar="MODE",
                      help="mode to remove the intervals: all = on all locations; start = only from start; end = only from end; both = start + end", default="all")
  parser.add_argument("--audio-directory", type=get_optional(parse_existing_directory), metavar='AUDIO-DIRECTORY',
                      help="directory containing the audios if not directory")
  parser.add_argument("--ignore-audio", action="store_true",
                      help="ignore audios")
  parser.add_argument("-out", "--output-directory", metavar='OUTPUT-DIRECTORY', type=get_optional(parse_path),
                      help="directory where to output the grids and audios if not to the same directory")
  parser.add_argument("--output-audio-directory", metavar='OUTPUT-AUDIO-DIRECTORY', type=get_optional(parse_path),
                      help="the directory where to output the modified audio files if not to directory.")
  add_encoding_argument(parser)
  add_overwrite_argument(parser)
  return app_remove_intervals


def app_remove_intervals(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  audio_directory = ns.audio_directory
  if audio_directory is None and not ns.ignore_audio:
    audio_directory = ns.directory

  output_directory = ns.output_directory
  if output_directory is None:
    output_directory = ns.directory

  output_audio_directory = ns.output_audio_directory
  if output_audio_directory is None:
    output_audio_directory = ns.directory

  flogger.debug(f"Marks: {'|'.join(OrderedSet(ns.marks))}")
  grid_files = get_grid_files(ns.directory)

  audio_files = {}
  if not ns.ignore_audio:
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

    sample_rate = None
    audio = None
    audio_provided = file_stem in audio_files
    if audio_provided:
      assert output_audio_directory is not None
      audio_file_out_abs = output_audio_directory / audio_files[file_stem]
      if audio_file_out_abs.exists() and not ns.overwrite:
        flogger.info("Audio file already exists. Skipped.")
        continue

      audio_file_in_abs = audio_directory / audio_files[file_stem]
      sample_rate, audio = read(audio_file_in_abs)

    (error, changed_anything), new_audio = remove_intervals(grid, audio, sample_rate, ns.tier,
                                                            ns.marks, ns.mode, flogger)

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

    if audio_provided:
      assert new_audio is not None
      if changed_anything:
        try:
          save_audio(audio_file_out_abs, new_audio, sample_rate)
        except Exception as ex:
          flogger.debug(ex)
          flogger.error("Audio couldn't be saved!")
          flogger.info("Skipped.")
          total_success = False
          continue
      elif ns.directory != output_directory:
        try:
          copy_audio(audio_file_out_abs, audio_file_in_abs)
        except Exception as ex:
          flogger.debug(ex)
          flogger.error("Audio couldn't be saved!")
          flogger.info("Skipped.")
          total_success = False
          continue

  return total_success, total_changed_anything
