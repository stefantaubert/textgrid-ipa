import os
from argparse import ArgumentParser
from pathlib import Path

from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat

from textgrid_tools.app.grid_audio_syncronization import \
    init_files_sync_grids_parser
from textgrid_tools.app.grid_interval_removal import \
    init_files_remove_intervals_parser
from textgrid_tools.app.grid_splitting import init_files_split_grid_parser
from textgrid_tools.app.grid_stats_generation import \
    init_files_print_stats_parser
from textgrid_tools.app.mfa_utils import (add_graphemes,
                                          extract_sentences_text_files,
                                          files_extract_tier_to_text,
                                          normalize_text_files_in_folder)
from textgrid_tools.app.text_to_grid_conversion import \
    init_files_convert_text_to_grid_parser
from textgrid_tools.app.tier_arpa_to_ipa_mapping import \
    init_map_arpa_tier_to_ipa_parser
from textgrid_tools.app.tier_boundary_adjustment import \
    init_files_fix_boundaries_parser
from textgrid_tools.app.tier_cloning import init_files_clone_tier_parser
from textgrid_tools.app.tier_dictionary_creation import \
    init_convert_texts_to_dicts_parser
from textgrid_tools.app.tier_interval_joining import \
    init_files_join_intervals_parser
from textgrid_tools.app.tier_moving import init_files_move_tier_parser
from textgrid_tools.app.tier_normalization import \
    init_files_normalize_tiers_parser
from textgrid_tools.app.tier_removal import init_files_remove_tiers_parser
from textgrid_tools.app.tier_renaming import init_files_rename_tier_parser
from textgrid_tools.app.tier_symbol_removal import \
    init_remove_symbols_from_tiers_parser
from textgrid_tools.app.tier_words_mapping import \
    init_files_map_words_to_tier_parser
from textgrid_tools.app.tier_words_to_arpa_transcription import \
    init_app_transcribe_words_to_arpa_on_phoneme_level_parser

BASE_DIR_VAR = "base_dir"
# DEFAULT_MFA_IGNORE_PUNCTUATION = "、。।，@<>”(),.:;¿?¡!\\&%#*~【】，…‥「」『』〝〟″⟨⟩♪・‹›«»～′$+="  # missing: “”"


def add_base_dir(parser: ArgumentParser):
  assert BASE_DIR_VAR in os.environ.keys()
  base_dir = os.environ[BASE_DIR_VAR]
  parser.set_defaults(base_dir=Path(base_dir))


def _add_parser_to(subparsers, name: str, init_method):
  parser = subparsers.add_parser(name, help=f"{name} help")
  invoke_method = init_method(parser)
  parser.set_defaults(invoke_handler=invoke_method)
  # add_base_dir(parser)
  return parser


def init_normalize_text_files_in_folder_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return normalize_text_files_in_folder


def init_files_extract_tier_to_text_parser(parser: ArgumentParser):
  parser.add_argument("--textgrid_folder_in", type=Path, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--txt_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_extract_tier_to_text


def init_extract_sentences_text_files_parser(parser: ArgumentParser):
  parser.add_argument("--text_folder_in", type=Path, required=True)
  parser.add_argument("--audio_folder", type=Path, required=True)
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return extract_sentences_text_files


def init_add_graphemes_from_words_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--original_text_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return add_graphemes


# def init_app_transcribe_words_to_arpa_parser(parser: ArgumentParser):
#   parser.add_argument("--folder_in", type=Path, required=True)
#   parser.add_argument("--original_text_tier_name", type=str, required=True)
#   parser.add_argument("--tier_name", type=str, required=True)
#   parser.add_argument("--overwrite_existing_tier", action="store_true")
#   parser.add_argument("--path_cache", type=Path, required=True)
#   parser.add_argument("--folder_out", type=Path, required=True)
#   parser.add_argument("--consider_annotations", action="store_true")
#   parser.add_argument("--overwrite", action="store_true")
#   return app_transcribe_words_to_arpa


def _init_parser():
  result = ArgumentParser()
  subparsers = result.add_subparsers(help="sub-command help")

  _add_parser_to(subparsers, "convert-text-to-grid",
                 init_files_convert_text_to_grid_parser)
  _add_parser_to(subparsers, "create-dict-from-grids", init_convert_texts_to_dicts_parser)
  _add_parser_to(subparsers, "mfa-normalize-texts", init_normalize_text_files_in_folder_parser)
  _add_parser_to(subparsers, "mfa-txt-to-textgrid", init_extract_sentences_text_files_parser)
  _add_parser_to(subparsers, "join-tier-intervals",
                 init_files_join_intervals_parser)
  _add_parser_to(subparsers, "map-words-to-tier", init_files_map_words_to_tier_parser)
  _add_parser_to(subparsers, "mfa-textgrid-to-txt", init_files_extract_tier_to_text_parser)
  _add_parser_to(subparsers, "map-arpa-tier-to-ipa", init_map_arpa_tier_to_ipa_parser)
  _add_parser_to(subparsers, "remove-tiers", init_files_remove_tiers_parser)
  _add_parser_to(subparsers, "remove-symbols-from-tiers", init_remove_symbols_from_tiers_parser)
  _add_parser_to(subparsers, "rename-tier", init_files_rename_tier_parser)
  _add_parser_to(subparsers, "clone-tier", init_files_clone_tier_parser)
  _add_parser_to(subparsers, "move-tier", init_files_move_tier_parser)
  _add_parser_to(subparsers, "mfa-add-graphemes-from-words", init_add_graphemes_from_words_parser)
  # _add_parser_to(subparsers, "mfa-words-to-arpa", init_app_transcribe_words_to_arpa_parser)
  _add_parser_to(subparsers, "transcribe-words-to-arpa-on-phoneme-level",
                 init_app_transcribe_words_to_arpa_on_phoneme_level_parser)
  _add_parser_to(subparsers, "split-grid",
                 init_files_split_grid_parser)
  _add_parser_to(subparsers, "remove-intervals",
                 init_files_remove_intervals_parser)
  _add_parser_to(subparsers, "fix-boundaries",
                 init_files_fix_boundaries_parser)
  _add_parser_to(subparsers, "sync-grid-to-audio",
                 init_files_sync_grids_parser)
  _add_parser_to(subparsers, "print-stats",
                 init_files_print_stats_parser)
  _add_parser_to(subparsers, "normalize-tiers",
                 init_files_normalize_tiers_parser)
  return result


def _process_args(args):
  params = vars(args)
  invoke_handler = params.pop("invoke_handler")
  invoke_handler(**params)


if __name__ == "__main__":
  main_parser = _init_parser()
  received_args = main_parser.parse_args()
  _process_args(received_args)
