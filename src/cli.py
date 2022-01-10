import argparse
from argparse import ArgumentParser
from logging import getLogger
from typing import Callable, Generator, Tuple

from textgrid_tools.app.globals import ExecutionResult
from textgrid_tools.app.grid.duration_splitting import \
    init_files_split_grid_on_durations_parser
from textgrid_tools.app.grid.interval_splitting import \
    init_files_split_grid_on_intervals_parser
from textgrid_tools.app.grid_audio_synchronization import \
    init_files_sync_grids_parser
from textgrid_tools.app.grid_interval_removal import \
    init_files_remove_intervals_parser
from textgrid_tools.app.grid_splitting import init_files_split_grid_parser
from textgrid_tools.app.grid_stats_generation import \
    init_files_print_stats_parser
from textgrid_tools.app.grid_to_text_conversion import \
    init_files_convert_grid_to_text_parser
from textgrid_tools.app.intervals.boundary_joining import \
    init_files_join_intervals_on_boundaries_parser
from textgrid_tools.app.intervals.interval_splitting import \
    init_files_split_intervals_parser
from textgrid_tools.app.intervals.pause_joining import \
    init_files_join_intervals_on_pauses_parser
from textgrid_tools.app.intervals.sentence_joining import \
    init_files_join_intervals_on_sentences_parser
from textgrid_tools.app.text_to_grid_conversion import \
    init_files_convert_text_to_grid_parser
from textgrid_tools.app.tier_arpa_to_ipa_mapping import \
    init_map_arpa_tier_to_ipa_parser
from textgrid_tools.app.tier_boundary_adjustment import \
    init_files_fix_boundaries_parser
from textgrid_tools.app.tier_cloning import init_files_clone_tier_parser
from textgrid_tools.app.tier_convert_text_to_symbols import \
    init_files_convert_text_to_symbols_parser
from textgrid_tools.app.tier_copying import init_files_copy_tier_to_grid_parser
from textgrid_tools.app.tier_dictionary_creation import \
    init_convert_texts_to_dicts_parser
from textgrid_tools.app.tier_mapping import \
    init_files_map_tier_to_other_tier_parser
from textgrid_tools.app.tier_moving import init_files_move_tier_parser
from textgrid_tools.app.tier_normalization import \
    init_files_normalize_tiers_parser
from textgrid_tools.app.tier_removal import init_files_remove_tiers_parser
from textgrid_tools.app.tier_renaming import init_files_rename_tier_parser
from textgrid_tools.app.tier_symbol_removal import \
    init_remove_symbols_from_tiers_parser
from textgrid_tools.app.tier_words_to_arpa_transcription import \
    init_app_transcribe_words_to_arpa_on_phoneme_level_parser

INVOKE_HANDLER_VAR = "invoke_handler"


def __configure_parser(parser: ArgumentParser, init_method: Callable[[ArgumentParser], Callable[..., ExecutionResult]]) -> None:
  invoke_method = init_method(parser)
  parser.set_defaults(**{
    INVOKE_HANDLER_VAR: invoke_method,
  })


def init_main_parser(parser: ArgumentParser):
  return parser.print_help


def formatter(prog):
  return argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40)


def _init_parser():
  # result = ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  result = ArgumentParser(formatter_class=formatter)
  result.description = "This program provides methods to modify TextGrids (.TextGrid) and their corresponding audio files (.wav)."
  __configure_parser(result, init_main_parser)

  subparsers = result.add_subparsers(help="description")

  methods: Generator[Tuple[str, str, Callable[[ArgumentParser], Callable[..., ExecutionResult]]]] = (
    ("convert-text-to-grid", "convert text files to grid files", init_files_convert_text_to_grid_parser),
    ("convert-grid-to-text", "convert grid files to text files", init_files_convert_grid_to_text_parser),
    ("create-dict-from-grids", "create pronunciation dictionary from multiple grid files",
     init_convert_texts_to_dicts_parser),
    ("join-tier-intervals-on-sentences", "join tier intervals sentence-wise",
     init_files_join_intervals_on_sentences_parser),
    ("join-tier-intervals-on-pauses", "join tier intervals on pauses",
     init_files_join_intervals_on_pauses_parser),
    ("join-tier-intervals-on-boundaries", "join tier intervals on boundaries",
     init_files_join_intervals_on_boundaries_parser),
    ("map-tier", "map content of one tier to another tier", init_files_map_tier_to_other_tier_parser),
    ("map-arpa-tier-to-ipa", "map a tier with ARPA transcriptions to IPA", init_map_arpa_tier_to_ipa_parser),
    ("remove-tiers", "remove tiers", init_files_remove_tiers_parser),
    ("remove-symbols-from-tiers", "remove symbols from tiers", init_remove_symbols_from_tiers_parser),
    ("remove-intervals", "remove intervals on all tiers", init_files_remove_intervals_parser),
    ("rename-tier", "rename a tier", init_files_rename_tier_parser),
    ("clone-tier", "clone a tier", init_files_clone_tier_parser),
    ("copy-tier", "copy tier from one grid to another", init_files_copy_tier_to_grid_parser),
    ("move-tier", "move a tier to another position in the grid", init_files_move_tier_parser),
    ("transcribe-words-to-arpa", "transcribe a tier containing words with help of a pronunciation dictionary to ARPA",
     init_app_transcribe_words_to_arpa_on_phoneme_level_parser),
    ("split-intervals", "split intervals", init_files_split_intervals_parser),
    ("split-grid", "split a grid file on intervals into multiple grid files (incl. audio files)",
     init_files_split_grid_parser),
    ("split-grid-on-intervals", "split a grid file on intervals into multiple grid files (incl. audio files)",
     init_files_split_grid_on_intervals_parser),
    ("split-grid-on-durations", "split a grid file on intervals based on durations into multiple grid files (incl. audio files)",
     init_files_split_grid_on_durations_parser),
    ("convert-text-to-symbols", "convert text string format to symbol string format",
     init_files_convert_text_to_symbols_parser),
    ("fix-boundaries", "align boundaries of tiers according to a reference tier",
     init_files_fix_boundaries_parser),
    ("sync-grid-to-audio", "synchronize grid minTime and maxTime according to the corresponding audio file",
     init_files_sync_grids_parser),
    ("print-stats", "print statistics", init_files_print_stats_parser),
    ("normalize-tiers", "normalize text of tiers", init_files_normalize_tiers_parser),
  )

  for command, description, method in methods:
    parser = subparsers.add_parser(command, help=description, formatter_class=formatter)
    __configure_parser(parser, method)

  return result


def _process_args(args):
  params = vars(args)

  if INVOKE_HANDLER_VAR in params:
    invoke_handler: Callable[..., ExecutionResult] = params.pop(INVOKE_HANDLER_VAR)
    error, changed_anything = invoke_handler(**params)
    logger = getLogger(__name__)
    if error is None:
      logger.info("Everything was successfull!")
    else:
      logger.warning("Not everything was successfull!")
    if not changed_anything:
      logger.info("Didn't changed anything.")


if __name__ == "__main__":
  main_parser = _init_parser()
  received_args = main_parser.parse_args()
  _process_args(received_args)
