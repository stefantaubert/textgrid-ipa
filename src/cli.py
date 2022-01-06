import argparse
from argparse import ArgumentParser, _SubParsersAction
from typing import Callable

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


def __add_parser_to(subparsers: _SubParsersAction, name: str, init_method: Callable[[ArgumentParser], Callable], help_msg: str):
  parser = subparsers.add_parser(name, help=help_msg, formatter_class=formatter)
  __configure_parser(parser, init_method)
  return parser


def __configure_parser(parser: ArgumentParser, init_method: Callable[[ArgumentParser], Callable]) -> None:
  invoke_method = init_method(parser)
  parser.set_defaults(**{
    INVOKE_HANDLER_VAR: invoke_method,
  })


def init_main_parser(parser: ArgumentParser):
  return parser.print_help


def formatter(prog):
  return argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40)


def _init_parser():
  #result = ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  result = ArgumentParser(formatter_class=formatter)
  result.description = "This program provides methods to modify TextGrids (.TextGrid) and their corresponding audio files (.wav)."
  __configure_parser(result, init_main_parser)

  subparsers = result.add_subparsers(help="description")

  __add_parser_to(subparsers, "convert-text-to-grid",
                  init_files_convert_text_to_grid_parser, "convert text files to grid files")
  __add_parser_to(subparsers, "convert-grid-to-text",
                  init_files_convert_grid_to_text_parser, "convert grid files to text files")
  __add_parser_to(subparsers, "create-dict-from-grids", init_convert_texts_to_dicts_parser,
                  "create pronunciation dictionary from multiple grid files")
  __add_parser_to(subparsers, "join-tier-intervals-on-sentences",
                  init_files_join_intervals_on_sentences_parser, "join tier intervals sentence-wise")
  __add_parser_to(subparsers, "join-tier-intervals-on-pauses",
                  init_files_join_intervals_on_pauses_parser, "join tier intervals on pauses")
  __add_parser_to(subparsers, "join-tier-intervals-on-boundaries",
                  init_files_join_intervals_on_boundaries_parser, "join tier intervals on boundaries")
  __add_parser_to(subparsers, "map-tier", init_files_map_tier_to_other_tier_parser,
                  "map content of one tier to another tier")
  __add_parser_to(subparsers, "map-arpa-tier-to-ipa", init_map_arpa_tier_to_ipa_parser,
                  "map a tier with ARPA transcriptions to IPA")
  __add_parser_to(subparsers, "remove-tiers", init_files_remove_tiers_parser, "remove tiers")
  __add_parser_to(subparsers, "remove-symbols-from-tiers",
                  init_remove_symbols_from_tiers_parser, "remove symbols from tiers")
  __add_parser_to(subparsers, "remove-intervals",
                  init_files_remove_intervals_parser, "remove intervals on all tiers")
  __add_parser_to(subparsers, "rename-tier", init_files_rename_tier_parser, "rename a tier")
  __add_parser_to(subparsers, "clone-tier", init_files_clone_tier_parser, "clone a tier")
  __add_parser_to(subparsers, "copy-tier",
                  init_files_copy_tier_to_grid_parser, "copy tier from one grid to another")
  __add_parser_to(subparsers, "move-tier", init_files_move_tier_parser,
                  "move a tier to another position in the grid")
  # _add_parser_to(subparsers, "mfa-words-to-arpa", init_app_transcribe_words_to_arpa_parser)
  __add_parser_to(subparsers, "transcribe-words-to-arpa",
                  init_app_transcribe_words_to_arpa_on_phoneme_level_parser, "transcribe a tier containing words with help of a pronunciation dictionary to ARPA")
  __add_parser_to(subparsers, "split-grid",
                  init_files_split_grid_parser, "split a grid file on intervals into multiple grid files (incl. audio files)")
  __add_parser_to(subparsers, "split-grid-on-intervals",
                  init_files_split_grid_on_intervals_parser, "split a grid file on intervals into multiple grid files (incl. audio files)")
  __add_parser_to(subparsers, "split-grid-on-durations",
                  init_files_split_grid_on_durations_parser, "split a grid file on intervals based on durations into multiple grid files (incl. audio files)")
  __add_parser_to(subparsers, "convert-text-to-symbols",
                  init_files_convert_text_to_symbols_parser, "convert text string format to symbol string format")
  __add_parser_to(subparsers, "fix-boundaries",
                  init_files_fix_boundaries_parser, "align boundaries of tiers according to a reference tier")
  __add_parser_to(subparsers, "sync-grid-to-audio",
                  init_files_sync_grids_parser, "synchronize grid minTime and maxTime according to the corresponding audio file")
  __add_parser_to(subparsers, "print-stats",
                  init_files_print_stats_parser, "print statistics")
  __add_parser_to(subparsers, "normalize-tiers",
                  init_files_normalize_tiers_parser, "normalize text of tiers")

  return result


def _process_args(args):
  params = vars(args)

  if INVOKE_HANDLER_VAR in params:
    invoke_handler = params.pop(INVOKE_HANDLER_VAR)
    invoke_handler(**params)


if __name__ == "__main__":
  main_parser = _init_parser()
  received_args = main_parser.parse_args()
  _process_args(received_args)
