import argparse
import platform
import sys
from argparse import ArgumentParser
from importlib.metadata import version
from logging import getLogger
from pathlib import Path
from pkgutil import iter_modules
from tempfile import gettempdir
from time import perf_counter
from typing import Callable, Dict, Generator, List, Tuple

from textgrid_tools_cli import *
from textgrid_tools_cli.grids.audio_paths_exporting import get_audio_paths_exporting_parser
from textgrid_tools_cli.grids.audio_paths_importing import get_audio_paths_importing_parser
from textgrid_tools_cli.grids.durations_labelling import get_grids_label_durations_parser
from textgrid_tools_cli.grids.grid_durations_exporting import get_grid_durations_exporting_parser
from textgrid_tools_cli.grids.grid_paths_exporting import get_grid_paths_exporting_parser
from textgrid_tools_cli.grids.grid_paths_importing import get_grid_paths_importing_parser
from textgrid_tools_cli.grids.pronunciations_exporting import get_pronunciations_exporting_parser
from textgrid_tools_cli.grids.stats_generation import get_grids_plot_stats_parser
from textgrid_tools_cli.helper import get_optional, parse_path
from textgrid_tools_cli.intervals.template_joining import get_template_joining_parser
from textgrid_tools_cli.intervals.text_replacement import get_text_replacement_parser
from textgrid_tools_cli.logging_configuration import (configure_root_logger, get_file_logger,
                                                      try_init_file_logger)

__version__ = version("textgrid-tools")

INVOKE_HANDLER_VAR = "invoke_handler"

CONSOLE_PNT_GREEN = "\x1b[1;49;32m"
CONSOLE_PNT_RED = "\x1b[1;49;31m"
CONSOLE_PNT_RST = "\x1b[0m"


Parsers = Generator[Tuple[str, str, Callable[[ArgumentParser],
                                             Callable[..., ExecutionResult]]], None, None]


def formatter(prog):
  return argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40)


def get_grids_parsers() -> Parsers:
  yield "merge", "merge grids together", get_grids_merging_parser
  yield "plot-durations", "plot durations", get_grids_plot_interval_durations_parser
  yield "mark-durations", "mark intervals with specific durations with a text", get_grids_label_durations_parser
  yield "create-dictionary", "create pronunciation dictionary out of a word and a pronunciation tier", get_pronunciations_exporting_parser
  yield "plot-stats", "plot statistics", get_grids_plot_stats_parser
  yield "export-vocabulary", "export vocabulary out of multiple grid files", get_vocabulary_export_parser
  yield "export-marks", "exports marks of a tier to a file", get_marks_exporting_parser
  yield "export-durations", "exports durations of grids to a file", get_grid_durations_exporting_parser
  yield "export-paths", "exports grid paths to a file", get_grid_paths_exporting_parser
  yield "export-audio-paths", "exports audio paths to a file", get_audio_paths_exporting_parser
  yield "import-paths", "import grids from paths written in a file", get_grid_paths_importing_parser
  yield "import-audio-paths", "import audio files from paths written in a file", get_audio_paths_importing_parser


def get_grid_parsers() -> Parsers:
  yield "create", "convert text files to grid files", get_creation_parser
  yield "sync", "synchronize grid minTime and maxTime according to the corresponding audio file", get_audio_synchronization_parser
  yield "split", "split a grid file on intervals into multiple grid files (incl. audio files)", get_grid_splitting_parser
  yield "print-stats", "print statistics", get_stats_generation_parser


def get_tiers_parsers() -> Parsers:
  yield "apply-mapping", "apply mapping table to marks", get_marks_mapping_parser
  yield "transcribe", "transcribe words of tiers using a pronunciation dictionary", get_transcription_parser
  yield "remove", "remove tiers", get_tiers_removing_parser
  yield "remove-symbols", "remove symbols from tiers", get_symbol_removing_parser
  yield "mark-silence", "mark silence intervals", get_label_silence_parser


def get_tier_parsers() -> Parsers:
  yield "rename", "rename tier", get_renaming_parser
  yield "clone", "clone tier", get_cloning_parser
  yield "map", "map tier to other tiers", get_mapping_parser
  yield "move", "move tier to another position", get_moving_parser
  yield "export", "export content of tier to a txt file", get_exporting_parser
  yield "import", "import content of tier from a txt file", get_importing_parser


def get_intervals_parsers() -> Parsers:
  yield "join", "join adjacent intervals", get_joining_parser
  yield "join-between-marks", "join intervals between marks", get_between_marks_joining_parser
  yield "join-by-boundary", "join intervals by boundaries of a tier", get_boundary_joining_parser
  yield "join-by-duration", "join intervals by a duration", get_duration_joining_parser
  yield "join-marks", "join intervals containing specific marks", get_mark_joining_parser
  yield "join-symbols", "join intervals containing specific symbols", get_symbols_joining_parser
  yield "join-template", "join intervals according to a template", get_template_joining_parser
  yield "split", "split intervals", get_splitting_parser
  yield "fix-boundaries", "align boundaries of tiers according to a reference tier", get_boundary_fixing_parser
  yield "remove", "remove intervals", get_intervals_removing_parser
  yield "plot-durations", "plot durations", get_plot_interval_durations_parser
  yield "join-between-pauses", "join intervals between pauses (LEGACY, please use join-between-marks)", get_between_pause_joining_parser
  yield "replace-text", "replace text using regex pattern", get_text_replacement_parser


def get_parsers() -> Dict[str, Tuple[Parsers, str]]:
  parsers: Dict[str, Tuple[Parsers, str]] = {
    "grids": (get_grids_parsers(), "execute commands targeted at multiple grids at once"),
    "grid": (get_grid_parsers(), "execute commands targeted at single grids"),
    "tiers": (get_tiers_parsers(), "execute commands targeted at multiple tiers at once"),
    "tier": (get_tier_parsers(), "execute commands targeted at single tiers"),
    "intervals": (get_intervals_parsers(), "execute commands targeted at intervals of tiers"),
  }
  return parsers


def print_features():
  parsers = get_parsers()
  for parser_name, (methods, help_str) in parsers.items():
    print(f"- {parser_name}")
    for command, description, method in methods:
      print(f"  - `{command}`: {description}")


def _init_parser():
  main_parser = ArgumentParser(
    formatter_class=formatter,
    description="This program provides methods to modify TextGrids (.TextGrid) and their corresponding audio files (.wav).",
  )
  main_parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
  subparsers = main_parser.add_subparsers(help="description")
  default_log_path = Path(gettempdir()) / "textgrid-tools.log"

  parsers = get_parsers()
  for parser_name, (methods, help_str) in parsers.items():
    sub_parser = subparsers.add_parser(parser_name, help=help_str, formatter_class=formatter)
    subparsers_of_subparser = sub_parser.add_subparsers()
    for command, description, method in methods:
      method_parser = subparsers_of_subparser.add_parser(
        command, help=description, formatter_class=formatter)
      method_parser.set_defaults(**{
        INVOKE_HANDLER_VAR: method(method_parser),
      })
      logging_group = method_parser.add_argument_group("logging arguments")
      logging_group.add_argument("--log", type=get_optional(parse_path), metavar="FILE",
                                 nargs="?", const=None, help="path to write the log", default=default_log_path)
      logging_group.add_argument("--debug", action="store_true",
                                 help="include debugging information in log")

  return main_parser


def parse_args(args: List[str]) -> None:
  configure_root_logger()
  logger = getLogger()

  local_debugging = debug_file_exists()
  if local_debugging:
    logger.debug(f"Received arguments: {str(args)}")

  parser = _init_parser()

  try:
    ns = parser.parse_args(args)
  except SystemExit:
    # invalid command supplied
    return

  if hasattr(ns, INVOKE_HANDLER_VAR):
    invoke_handler: Callable[..., ExecutionResult] = getattr(ns, INVOKE_HANDLER_VAR)
    delattr(ns, INVOKE_HANDLER_VAR)
    log_to_file = ns.log is not None
    if log_to_file:
      log_to_file = try_init_file_logger(ns.log, local_debugging or ns.debug)
      if not log_to_file:
        logger.warning("Logging to file is not possible.")

    flogger = get_file_logger()
    if not local_debugging:
      sys_version = sys.version.replace('\n', '')
      flogger.debug(f"CLI version: {__version__}")
      flogger.debug(f"Python version: {sys_version}")
      flogger.debug("Modules: %s", ', '.join(sorted(p.name for p in iter_modules())))

      my_system = platform.uname()
      flogger.debug(f"System: {my_system.system}")
      flogger.debug(f"Node Name: {my_system.node}")
      flogger.debug(f"Release: {my_system.release}")
      flogger.debug(f"Version: {my_system.version}")
      flogger.debug(f"Machine: {my_system.machine}")
      flogger.debug(f"Processor: {my_system.processor}")

    flogger.debug(f"Received arguments: {str(args)}")
    flogger.debug(f"Parsed arguments: {str(ns)}")

    start = perf_counter()
    success, changed_anything = invoke_handler(ns)

    if success:
      logger.info(f"{CONSOLE_PNT_GREEN}Everything was successful!{CONSOLE_PNT_RST}")
      flogger.info("Everything was successful!")
    else:
      if log_to_file:
        logger.error(
          "Not everything was successful! See log for details.")
      else:
        logger.error(
          "Not everything was successful!")
      flogger.error("Not everything was successful!")

    if not changed_anything:
      logger.info("Didn't changed anything.")
      flogger.info("Didn't changed anything.")

    duration = perf_counter() - start
    flogger.debug(f"Total duration (s): {duration}")

    if log_to_file:
      logger.info(f"Written log to: {ns.log.absolute()}")

  else:
    parser.print_help()


def run():
  arguments = sys.argv[1:]
  parse_args(arguments)


def run_prod():
  run()


def debug_file_exists():
  return (Path(gettempdir()) / "textgrid-tools-debug").is_file()


def create_debug_file():
  (Path(gettempdir()) / "textgrid-tools-debug").write_text("", "UTF-8")


if __name__ == "__main__":
  # print_features()
  # create_debug_file()
  run()
