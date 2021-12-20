from argparse import ArgumentParser

from textgrid_tools.app.grid_audio_syncronization import \
    init_files_sync_grids_parser
from textgrid_tools.app.grid_interval_removal import \
    init_files_remove_intervals_parser
from textgrid_tools.app.grid_splitting import init_files_split_grid_parser
from textgrid_tools.app.grid_stats_generation import \
    init_files_print_stats_parser
from textgrid_tools.app.grid_to_text_conversion import \
    init_files_convert_grid_to_text_parser
from textgrid_tools.app.text_to_grid_conversion import \
    init_files_convert_text_to_grid_parser
from textgrid_tools.app.tier_arpa_to_ipa_mapping import \
    init_map_arpa_tier_to_ipa_parser
from textgrid_tools.app.tier_boundary_adjustment import \
    init_files_fix_boundaries_parser
from textgrid_tools.app.tier_cloning import init_files_clone_tier_parser
from textgrid_tools.app.tier_convert_text_to_symbols import \
    init_files_convert_text_to_symbols_parser
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

# BASE_DIR_VAR = "base_dir"
# # DEFAULT_MFA_IGNORE_PUNCTUATION = "、。।，@<>”(),.:;¿?¡!\\&%#*~【】，…‥「」『』〝〟″⟨⟩♪・‹›«»～′$+="  # missing: “”"


# def add_base_dir(parser: ArgumentParser):
#   assert BASE_DIR_VAR in os.environ.keys()
#   base_dir = os.environ[BASE_DIR_VAR]
#   parser.set_defaults(base_dir=Path(base_dir))


def _add_parser_to(subparsers, name: str, init_method):
  parser = subparsers.add_parser(name, help=f"{name} help")
  invoke_method = init_method(parser)
  parser.set_defaults(invoke_handler=invoke_method)
  # add_base_dir(parser)
  return parser


def _init_parser():
  result = ArgumentParser()
  subparsers = result.add_subparsers(help="sub-command help")

  _add_parser_to(subparsers, "convert-text-to-grid",
                 init_files_convert_text_to_grid_parser)
  _add_parser_to(subparsers, "convert-grid-to-text",
                 init_files_convert_grid_to_text_parser)
  _add_parser_to(subparsers, "create-dict-from-grids", init_convert_texts_to_dicts_parser)
  _add_parser_to(subparsers, "join-tier-intervals",
                 init_files_join_intervals_parser)
  _add_parser_to(subparsers, "map-words-to-tier", init_files_map_words_to_tier_parser)
  _add_parser_to(subparsers, "map-arpa-tier-to-ipa", init_map_arpa_tier_to_ipa_parser)
  _add_parser_to(subparsers, "remove-tiers", init_files_remove_tiers_parser)
  _add_parser_to(subparsers, "remove-symbols-from-tiers", init_remove_symbols_from_tiers_parser)
  _add_parser_to(subparsers, "rename-tier", init_files_rename_tier_parser)
  _add_parser_to(subparsers, "clone-tier", init_files_clone_tier_parser)
  _add_parser_to(subparsers, "move-tier", init_files_move_tier_parser)
  # _add_parser_to(subparsers, "mfa-words-to-arpa", init_app_transcribe_words_to_arpa_parser)
  _add_parser_to(subparsers, "transcribe-words-to-arpa-on-phoneme-level",
                 init_app_transcribe_words_to_arpa_on_phoneme_level_parser)
  _add_parser_to(subparsers, "split-grid",
                 init_files_split_grid_parser)
  _add_parser_to(subparsers, "convert-text-to-symbols",
                 init_files_convert_text_to_symbols_parser)
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
