import argparse
import sys
from argparse import ArgumentParser
from importlib.metadata import version
from logging import getLogger
from pathlib import Path
from typing import Callable, Dict, Generator, List, Tuple

from textgrid_tools_cli import *
from textgrid_tools_cli.grid.creation_v2 import get_creation_v2_parser
from textgrid_tools_cli.intervals.splitting_v2 import get_splitting_v2_parser
from textgrid_tools_cli.logging_configuration import (configure_root_logger,
                                                      init_and_get_console_logger)

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
  yield "export-vocabulary", "export vocabulary out of multiple grid files", get_vocabulary_export_parser
  yield "plot-durations", "plot durations", get_grids_plot_interval_durations_parser
  yield "export-marks", "exports marks of a tier to a file", get_marks_exporting_parser


def get_grid_parsers() -> Parsers:
  yield "create", "convert text files to grid files", get_creation_parser
  yield "create-v2", "convert text files to grid files", get_creation_v2_parser
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
  yield "join-between-pauses", "join intervals between pauses", get_between_pause_joining_parser
  yield "join-by-boundary", "join intervals by boundaries of a tier", get_boundary_joining_parser
  yield "join-by-duration", "join intervals by a duration", get_duration_joining_parser
  yield "join-marks", "join intervals containing specific marks", get_mark_joining_parser
  yield "join-symbols", "join intervals containing specific symbols", get_symbols_joining_parser
  yield "fix-boundaries", "align boundaries of tiers according to a reference tier", get_boundary_fixing_parser
  yield "split", "split intervals", get_splitting_parser
  yield "split-v2", "split intervals", get_splitting_v2_parser
  yield "remove", "remove intervals", get_intervals_removing_parser
  yield "plot-durations", "plot durations", get_plot_interval_durations_parser


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
      print(f"  - {description}")


def _init_parser():
  main_parser = ArgumentParser(
    formatter_class=formatter,
    description="This program provides methods to modify TextGrids (.TextGrid) and their corresponding audios (.wav).",
  )
  main_parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
  subparsers = main_parser.add_subparsers(help="description")

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

  return main_parser


def parse_args(args: List[str]):
  configure_root_logger()
  logger = getLogger()

  if debug_file_exists():
    logger.debug("Received args:")
    logger.debug(args)

  parser = _init_parser()
  received_args = parser.parse_args(args)
  params = vars(received_args)

  if INVOKE_HANDLER_VAR in params:
    invoke_handler: Callable[..., ExecutionResult] = params.pop(INVOKE_HANDLER_VAR)
    success, changed_anything = invoke_handler(**params)
    # get logger after it had a change to be init with a logfile
    if success:
      logger.info(f"{CONSOLE_PNT_GREEN}Everything was successfull!{CONSOLE_PNT_RST}")
    else:
      logger.warning(
        f"{CONSOLE_PNT_RED}Not everything was successfull! See log for details.{CONSOLE_PNT_RST}")
    if not changed_anything:
      logger.info("Didn't changed anything.")
  else:
    parser.print_help()


def run():
  arguments = sys.argv[1:]
  parse_args(arguments)


def run_prod():
  run()


def debug_file_exists():
  return Path("/tmp/debug").is_file()


def create_debug_file():
  Path("/tmp/debug").write_text("", "UTF-8")


if __name__ == "__main__":
  # print_features()
  run()
