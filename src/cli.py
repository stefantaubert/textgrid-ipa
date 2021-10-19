import os
from argparse import ArgumentParser
from pathlib import Path

from text_utils.language import Language
from text_utils.pronunciation.main import EngToIPAMode
from text_utils.symbol_format import SymbolFormat

from textgrid_tools.app.main import (add_recording, clone, convert_to_ipa,
                                     detect_silence, extract_words, log_stats,
                                     to_dataset)
from textgrid_tools.app.mfa_utils import (add_ipa_from_words,
                                          add_original_text_layer,
                                          add_original_texts_layer,
                                          add_phonemes_from_phonemes,
                                          add_phonemes_from_words,
                                          convert_text_to_dict,
                                          normalize_text_file,
                                          normalize_text_files_in_folder)

BASE_DIR_VAR = "base_dir"
DEFAULT_MFA_IGNORE_PUNCTUATION = "、。।，@<>”(),.:;¿?¡!\\&%#*~【】，…‥「」『』〝〟″⟨⟩♪・‹›«»～′$+="  # missing: “”"


def add_base_dir(parser: ArgumentParser):
  assert BASE_DIR_VAR in os.environ.keys()
  base_dir = os.environ[BASE_DIR_VAR]
  parser.set_defaults(base_dir=Path(base_dir))


def _add_parser_to(subparsers, name: str, init_method):
  parser = subparsers.add_parser(name, help=f"{name} help")
  invoke_method = init_method(parser)
  parser.set_defaults(invoke_handler=invoke_method)
  add_base_dir(parser)
  return parser


def init_normalize_text_file_parser(parser: ArgumentParser):
  parser.add_argument("--text_path", type=Path, required=True)
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--out_path", type=Path, required=True)
  return normalize_text_file


def init_normalize_text_files_in_folder_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return normalize_text_files_in_folder


def init_convert_to_dict_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--step_name", type=str, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--tier_lang", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--ignore_tones", action="store_true")
  parser.add_argument("--ignore_arcs", action="store_true")
  parser.add_argument("--replace_unknown_ipa_by", type=str, default="_")
  return convert_text_to_dict


def init_add_original_text_layer_parser(parser: ArgumentParser):
  parser.add_argument("--grid_path", type=Path, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--text_path", type=Path, required=True)
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--out_path", type=Path, required=True)
  parser.add_argument("--trim_symbols", type=str, required=True)
  return add_original_text_layer


def init_add_original_texts_layer_parser(parser: ArgumentParser):
  parser.add_argument("--text_folder", type=Path, required=True)
  parser.add_argument("--textgrid_folder_in", type=Path, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--trim_symbols", type=str, required=True)
  parser.add_argument("--textgrid_folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return add_original_texts_layer


def init_add_ipa_from_words_parser(parser: ArgumentParser):
  parser.add_argument("--grid_path", type=Path, required=True)
  parser.add_argument("--original_text_tier_name", type=str, required=True)
  parser.add_argument("--new_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tier", action="store_true")
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--pronunciation_dict_file", type=Path, required=True)
  parser.add_argument("--out_path", type=Path, required=True)
  parser.add_argument("--trim_symbols", type=str, required=True)
  return add_ipa_from_words


def init_add_phonemes_from_words_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--original_text_tier_name", type=str, required=True)
  parser.add_argument("--new_ipa_tier_name", type=str, required=True)
  parser.add_argument("--new_arpa_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tiers", action="store_true")
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--pronunciation_dict_file", type=Path, required=True)
  parser.add_argument("--trim_symbols", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return add_phonemes_from_words


def init_add_phonemes_from_phonemes_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--original_text_tier_name", type=str, required=True)
  parser.add_argument("--reference_tier_name", type=str, required=True)
  parser.add_argument("--new_ipa_tier_name", type=str, required=True)
  parser.add_argument("--new_arpa_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_existing_tiers", action="store_true")
  parser.add_argument("--text_format", choices=SymbolFormat,
                      type=SymbolFormat.__getitem__, required=True)
  parser.add_argument("--language", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--pronunciation_dict_file", type=Path, required=True)
  parser.add_argument("--trim_symbols", type=str, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return add_phonemes_from_phonemes


def init_log_stats_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--step_name", type=str, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--tier_lang", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--ignore_tones", action="store_true")
  parser.add_argument("--ignore_arcs", action="store_true")
  parser.add_argument("--replace_unknown_ipa_by", type=str, default="_")
  return log_stats


def init_add_recording_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--audio_path", type=Path, required=True)
  parser.add_argument("--out_step_name", type=str, required=True)
  parser.add_argument("--overwrite_recording", action="store_true")
  return add_recording


def init_clone_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--in_step_name", type=str, required=True)
  parser.add_argument("--out_step_name", type=str, required=True)
  parser.add_argument("--overwrite_step", action="store_true")
  return clone


def init_detect_silence_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--in_step_name", type=str, required=True)
  parser.add_argument("--out_step_name", type=str, required=True)
  parser.add_argument("--out_tier_name", type=str, default="silence")
  parser.add_argument("--silence_boundary", type=float, default=0.25,
                      help="Percent of lower dB recognized as silence.")
  parser.add_argument("--chunk_size_ms", type=int, default=50)
  parser.add_argument("--min_silence_duration_ms", type=int, default=700)
  parser.add_argument("--min_content_duration_ms", type=int, default=200)
  parser.add_argument("--content_buffer_start_ms", type=int, default=50)
  parser.add_argument("--content_buffer_end_ms", type=int, default=100)
  parser.add_argument("--silence_mark", type=str, default="silence")
  parser.add_argument("--content_mark", type=str, default="")
  parser.add_argument("--overwrite_step", action="store_true")
  parser.add_argument("--overwrite_tier", action="store_true")
  return detect_silence


def init_extract_words_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--in_step_name", type=str, required=True)
  parser.add_argument("--out_step_name", type=str, required=True)
  parser.add_argument("--in_tier_name", type=str, required=True)
  parser.add_argument("--out_tier_name", type=str, required=True)
  parser.add_argument("--overwrite_step", action="store_true")
  parser.add_argument("--overwrite_tier", action="store_true")
  return extract_words


def init_convert_to_ipa_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--in_step_name", type=str, required=True)
  parser.add_argument("--out_step_name", type=str, required=True)
  parser.add_argument("--in_tier_name", type=str, required=True)
  parser.add_argument("--in_tier_lang", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--out_tier_name", type=str, required=True)
  parser.add_argument("--mode", choices=EngToIPAMode, type=EngToIPAMode.__getitem__, required=False)
  parser.add_argument("--replace_unknown_with", type=str, default="_")
  parser.add_argument("--overwrite_step", action="store_true")
  parser.add_argument("--overwrite_tier", action="store_true")
  parser.set_defaults(consider_ipa_annotations=True)
  return convert_to_ipa


def init_to_dataset_parser(parser: ArgumentParser):
  parser.add_argument("--recording_name", type=str, required=True)
  parser.add_argument("--step_name", type=str, required=True)
  parser.add_argument("--tier_name", type=str, required=True)
  parser.add_argument("--tier_lang", choices=Language, type=Language.__getitem__, required=True)
  parser.add_argument("--duration_s_max", type=float, required=True)
  parser.add_argument("--output_dir", type=Path, required=True)
  parser.add_argument("--speaker_name", type=str, required=True)
  parser.add_argument("--speaker_gender", type=str, required=True, choices=["m", "f"])
  parser.add_argument("--speaker_accent", type=str, required=True)
  parser.add_argument("--ignore_empty_marks", action="store_true")
  parser.add_argument("--overwrite_output", action="store_true")
  return to_dataset


def _init_parser():
  result = ArgumentParser()
  subparsers = result.add_subparsers(help="sub-command help")

  _add_parser_to(subparsers, "add-rec", init_add_recording_parser)
  _add_parser_to(subparsers, "rec-clone", init_clone_parser)
  _add_parser_to(subparsers, "rec-add-silence", init_detect_silence_parser)
  _add_parser_to(subparsers, "rec-add-words", init_extract_words_parser)
  _add_parser_to(subparsers, "rec-add-ipa", init_convert_to_ipa_parser)
  _add_parser_to(subparsers, "rec-print-stats", init_log_stats_parser)
  _add_parser_to(subparsers, "rec-to-dataset", init_to_dataset_parser)
  _add_parser_to(subparsers, "mfa-create-dict", init_convert_to_dict_parser)
  _add_parser_to(subparsers, "mfa-normalize-text", init_normalize_text_file_parser)
  _add_parser_to(subparsers, "mfa-normalize-texts", init_normalize_text_files_in_folder_parser)
  _add_parser_to(subparsers, "mfa-add-text", init_add_original_text_layer_parser)
  _add_parser_to(subparsers, "mfa-add-texts", init_add_original_texts_layer_parser)
  _add_parser_to(subparsers, "mfa-add-ipa", init_add_ipa_from_words_parser)
  _add_parser_to(subparsers, "mfa-add-phonemes-from-words", init_add_phonemes_from_words_parser)
  _add_parser_to(subparsers, "mfa-add-phonemes-from-phonemes",
                 init_add_phonemes_from_phonemes_parser)

  return result


def _process_args(args):
  params = vars(args)
  invoke_handler = params.pop("invoke_handler")
  invoke_handler(**params)


if __name__ == "__main__":
  main_parser = _init_parser()
  received_args = main_parser.parse_args()
  _process_args(received_args)
