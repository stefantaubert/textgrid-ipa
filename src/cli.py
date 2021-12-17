import os
from argparse import ArgumentParser
from pathlib import Path

from pronunciation_dict_parser.default_parser import PublicDictType
from text_utils.language import Language
from text_utils.symbol_format import SymbolFormat

from textgrid_tools.app.grid_splitting import init_files_split_grid_parser
from textgrid_tools.app.mfa_utils import (
    add_graphemes, add_marker, add_original_texts_layer,
    app_transcribe_words_to_arpa,
    app_transcribe_words_to_arpa_on_phoneme_level, convert_texts_to_arpa_dicts,
    extract_sentences_text_files, files_clone_tier, files_extract_tier_to_text,
    files_fix_boundaries, files_map_arpa_to_ipa, files_move_tier,
    files_print_stats, files_remove_intervals, files_remove_symbols,
    files_remove_tiers, files_rename_tier, files_split_intervals,
    files_sync_grids, merge_words_to_new_textgrid,
    normalize_text_files_in_folder)
from textgrid_tools.app.tier_moving import init_files_move_tier_parser
from textgrid_tools.app.tier_removal import init_files_remove_tiers_parser

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


def init_convert_texts_to_dicts_parser(parser: ArgumentParser):
  arpa_dicts = [
    PublicDictType.MFA_ARPA,
    PublicDictType.CMU_ARPA,
    PublicDictType.LIBRISPEECH_ARPA,
    PublicDictType.PROSODYLAB_ARPA,
  ]
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--trim_symbols", type=str, required=True)
  parser.add_argument("--consider_annotations", action="store_true")
  parser.add_argument("--out_path_mfa_dict", type=Path, required=False)
  parser.add_argument("--out_path_punctuation_dict", type=Path, required=False)
  parser.add_argument("--out_path_cache", type=Path, required=False)
  parser.add_argument("--dict_type", choices=arpa_dicts,
                      type=PublicDictType.__getitem__, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return convert_texts_to_arpa_dicts


def init_normalize_text_files_in_folder_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return normalize_text_files_in_folder


def init_files_rename_tier_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_rename_tier


def init_files_clone_tier_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_clone_tier


def init_files_map_arpa_to_ipa_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--arpa_tier_name", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--ipa_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return files_map_arpa_to_ipa


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


def init_files_remove_intervals_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--audio_folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--remove_marks", type=str, nargs='*')
  parser.add_argument("--remove_empty", action="store_true")
  parser.add_argument("--audio_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_remove_intervals


def init_files_sync_grids_parser(parser: ArgumentParser):
  parser.add_argument("--folder", type=Path, required=True)
  parser.add_argument("--audio_folder", type=Path, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return files_sync_grids



def init_files_print_stats_parser(parser: ArgumentParser):
  parser.add_argument("--folder", type=Path, required=True)
  parser.add_argument("--duration_threshold", type=float, default=0.002)
  parser.add_argument("--print_symbols_tier_names", type=str, nargs='*', default="")
  return files_print_stats


def init_files_fix_boundaries_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--difference_threshold", type=float, required=False)
  parser.add_argument("--overwrite", action="store_true")
  return files_fix_boundaries


def init_add_original_texts_layer_parser(parser: ArgumentParser):
  parser.add_argument("--text_folder", type=Path, required=True)
  parser.add_argument("--textgrid_folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--path_align_dict", type=Path, required=True)
  parser.add_argument("--textgrid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return add_original_texts_layer


def init_merge_words_to_new_textgrid_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--min_pause_s", type=float, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return merge_words_to_new_textgrid


def init_add_graphemes_from_words_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--original_text_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return add_graphemes


def init_add_marker_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return add_marker


def init_app_transcribe_words_to_arpa_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--original_text_tier_name", type=str, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--path_cache", type=Path, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--consider_annotations", action="store_true")
  parser.add_argument("--overwrite", action="store_true")
  return app_transcribe_words_to_arpa


def init_app_transcribe_words_to_arpa_on_phoneme_level_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--words_tier_name", type=str, required=True)
  parser.add_argument("--phoneme_tier_name", type=str, required=True)
  parser.add_argument("--arpa_tier_name", type=str, required=True)
  parser.add_argument("--consider_annotations", action="store_true")
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--path_cache", type=Path, required=True)
  parser.add_argument("--trim_symbols", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return app_transcribe_words_to_arpa_on_phoneme_level


def _init_parser():
  result = ArgumentParser()
  subparsers = result.add_subparsers(help="sub-command help")

  _add_parser_to(subparsers, "mfa-create-dict-from-texts", init_convert_texts_to_dicts_parser)
  _add_parser_to(subparsers, "mfa-normalize-texts", init_normalize_text_files_in_folder_parser)
  _add_parser_to(subparsers, "mfa-txt-to-textgrid", init_extract_sentences_text_files_parser)
  _add_parser_to(subparsers, "mfa-merge-words",
                 init_merge_words_to_new_textgrid_parser)
  _add_parser_to(subparsers, "mfa-add-texts", init_add_original_texts_layer_parser)
  _add_parser_to(subparsers, "mfa-textgrid-to-txt", init_files_extract_tier_to_text_parser)
  _add_parser_to(subparsers, "mfa-arpa-to-ipa", init_files_map_arpa_to_ipa_parser)
  _add_parser_to(subparsers, "remove-tiers", init_files_remove_tiers_parser)
  _add_parser_to(subparsers, "mfa-remove-symbols", init_files_remove_symbols_parser)
  _add_parser_to(subparsers, "mfa-rename-tier", init_files_rename_tier_parser)
  _add_parser_to(subparsers, "mfa-clone-tier", init_files_clone_tier_parser)
  _add_parser_to(subparsers, "move-tier", init_files_move_tier_parser)
  _add_parser_to(subparsers, "mfa-add-graphemes-from-words", init_add_graphemes_from_words_parser)
  _add_parser_to(subparsers, "mfa-add-marker-tier", init_add_marker_parser)
  _add_parser_to(subparsers, "mfa-words-to-arpa", init_app_transcribe_words_to_arpa_parser)
  _add_parser_to(subparsers, "mfa-words-to-arpa-on-phoneme-level",
                 init_app_transcribe_words_to_arpa_on_phoneme_level_parser)
  _add_parser_to(subparsers, "split",
                 init_files_split_grid_parser)
  _add_parser_to(subparsers, "mfa-remove-intervals",
                 init_files_remove_intervals_parser)
  _add_parser_to(subparsers, "mfa-fix-boundaries",
                 init_files_fix_boundaries_parser)
  _add_parser_to(subparsers, "mfa-sync-grid-to-audio",
                 init_files_sync_grids_parser)
  _add_parser_to(subparsers, "mfa-stats",
                 init_files_print_stats_parser)
  return result


def _process_args(args):
  params = vars(args)
  invoke_handler = params.pop("invoke_handler")
  invoke_handler(**params)


if __name__ == "__main__":
  main_parser = _init_parser()
  received_args = main_parser.parse_args()
  _process_args(received_args)
