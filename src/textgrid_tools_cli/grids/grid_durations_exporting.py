from argparse import ArgumentParser, Namespace
from typing import List

from tqdm import tqdm

from textgrid_tools.helper import samples_to_s
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_directory_argument, add_encoding_argument,
                                       get_audio_files, get_grid_files, parse_txt_path, read_audio,
                                       try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_durations_exporting_parser(parser: ArgumentParser):
  parser.description = "This command exports the durations of all grid/audio files into one text file."
  add_directory_argument(parser)
  parser.add_argument("output", type=parse_txt_path, metavar="OUTPUT",
                      help="path to output the durations (*.txt)")
  parser.add_argument("--mode", type=str, choices=["grid", "audio"],
                      default="grid", help="from which files the audio should be taken")
  add_encoding_argument(parser, "encoding of input grid files and OUTPUT text file")
  return export_durations_ns


def export_durations_ns(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  use_grids = True
  if ns.mode == "grid":
    files = get_grid_files(ns.directory)
  else:
    assert ns.mode == "audio"
    files = get_audio_files(ns.directory)
    use_grids = False

  durations: List[str] = []
  # TODO all successful false on skipped files
  all_successful = True
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(files.items()), start=1):
    flogger.info(f"Processing {file_stem}")
    file_in_abs = ns.directory / rel_path

    if use_grids:
      error, grid = try_load_grid(file_in_abs, ns.encoding)
      if error:
        flogger.debug(error.exception)
        flogger.error(error.default_message)
        flogger.info("Skipped.")
        all_successful = False
        continue
      assert grid is not None

      grid_duration = grid.maxTime - grid.minTime
      durations.append(str(grid_duration))
    else:
      try:
        sample_rate, audio_in = read_audio(file_in_abs)
      except Exception as ex:
        flogger.debug(ex)
        flogger.error("Audio file couldn't be read!")
        flogger.info("Skipped.")
        all_successful = False
        continue
      audio_samples_in = audio_in.shape[0]
      duration_s = samples_to_s(audio_samples_in, sample_rate)
      durations.append(str(duration_s))

  txt = "\n".join(durations)

  ns.output.parent.mkdir(parents=True, exist_ok=True)
  ns.output.write_text(txt, ns.encoding)
  logger.info(f"Exported {len(durations)} duration(s) to: \"{ns.output.absolute()}\".")

  return all_successful, True
