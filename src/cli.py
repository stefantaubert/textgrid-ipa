import argparse
import logging
from argparse import ArgumentParser
from logging import getLogger
from typing import Callable, Dict, Generator, Tuple

from textgrid_tools.app import *

__version__ = "1.0.1"

INVOKE_HANDLER_VAR = "invoke_handler"


Parsers = Generator[Tuple[str, str, Callable[[ArgumentParser],
                                             Callable[..., ExecutionResult]]], None, None]


def formatter(prog):
  return argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40)


def get_grids_parsers() -> Parsers:
  yield "create-dictionary", "create pronunciation dictionary from multiple grid files", get_dictionary_creation_parser
  yield "plot-durations", "plot durations", get_grids_plot_interval_durations_parser
  yield "export-marks", "exports marks of a tier to a file", get_marks_exporting_parser


def get_grid_parsers() -> Parsers:
  yield "create", "convert text files to grid files", get_creation_parser
  yield "sync", "synchronize grid minTime and maxTime according to the corresponding audio file", get_audio_synchronization_parser
  yield "split", "split a grid file on intervals into multiple grid files (incl. audio files)", get_grid_splitting_parser
  yield "print-stats", "print statistics", get_stats_generation_parser


def get_tiers_parsers() -> Parsers:
  yield "transcribe-to-ipa", "transcribe tiers with ARPA transcriptions to IPA", get_arpa_to_ipa_transcription_parser
  yield "transcribe", "transcribe words of tiers using a pronunciation dictionary", get_transcription_parser
  yield "normalize", "normalize content of tiers", get_normalization_parser
  yield "remove", "remove tiers", get_tiers_removing_parser
  yield "switch-format", "switch tier format of tiers", get_string_format_switching_parser
  yield "remove-symbols", "remove symbols from tiers", get_symbol_removing_parser
  yield "mark-silence", "mark silence intervals", get_label_silence_parser


def get_tier_parsers() -> Parsers:
  yield "rename", "rename tier", get_renaming_parser
  yield "clone", "clone tier", get_cloning_parser
  yield "copy", "copy tier from one grid to another", get_copying_parser
  yield "map", "map tier to other tiers", get_mapping_parser
  yield "move", "move tier to another position", get_moving_parser
  yield "export", "export content of tier to a txt file", get_text_conversion_parser


def get_intervals_parsers() -> Parsers:
  yield "join-between-pauses", "join intervals between pauses", get_between_pause_joining_parser
  yield "join-by-boundary", "join intervals by boundaries of a tier", get_boundary_joining_parser
  yield "join-on-sentences", "join intervals sentence-wise", get_sentence_joining_parser
  yield "join-by-duration", "join intervals by a duration", get_duration_joining_parser
  yield "join-marks", "join intervals containing specific marks", get_mark_joining_parser
  yield "fix-boundaries", "align boundaries of tiers according to a reference tier", get_boundary_fixing_parser
  yield "split", "split intervals", get_intervals_splitting_parser
  yield "remove", "remove intervals", get_intervals_removing_parser
  yield "plot-durations", "plot durations", get_plot_interval_durations_parser


def _init_parser():
  main_parser = ArgumentParser(
    formatter_class=formatter,
    description="This program provides methods to modify TextGrids (.TextGrid) and their corresponding audios (.wav).",
  )
  main_parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
  subparsers = main_parser.add_subparsers(help="description")

  parsers: Dict[str, Tuple[Parsers, str]] = {
    "grids": (get_grids_parsers(), "execute commands targeted at multiple grids at once"),
    "grid": (get_grid_parsers(), "execute commands targeted at single grids"),
    "tiers": (get_tiers_parsers(), "execute commands targeted at multiple tiers at once"),
    "tier": (get_tier_parsers(), "execute commands targeted at single tiers"),
    "intervals": (get_intervals_parsers(), "execute commands targeted at intervals of tiers"),
  }

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


def configure_logger() -> None:
  loglevel = logging.DEBUG if __debug__ else logging.INFO
  main_logger = getLogger()
  main_logger.setLevel(loglevel)
  main_logger.manager.disable = logging.NOTSET
  if len(main_logger.handlers) > 0:
    console = main_logger.handlers[0]
  else:
    console = logging.StreamHandler()
    main_logger.addHandler(console)

  logging_formatter = logging.Formatter(
    '[%(asctime)s.%(msecs)03d] (%(levelname)s) %(message)s',
    '%Y/%m/%d %H:%M:%S',
  )
  console.setFormatter(logging_formatter)
  console.setLevel(loglevel)


def main():
  configure_logger()
  parser = _init_parser()
  received_args = parser.parse_args()
  params = vars(received_args)

  if INVOKE_HANDLER_VAR in params:
    invoke_handler: Callable[..., ExecutionResult] = params.pop(INVOKE_HANDLER_VAR)
    success, changed_anything = invoke_handler(**params)
    logger = getLogger(__name__)
    if success:
      logger.info("Everything was successfull!")
    else:
      logger.warning("Not everything was successfull!")
    if not changed_anything:
      logger.info("Didn't changed anything.")
  else:
    parser.print_help()


if __name__ == "__main__":
  main()
