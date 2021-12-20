

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


def init_normalize_text_files_in_folder_parser(parser: ArgumentParser):
  parser.add_argument("--folder_in", type=Path, required=True)
  parser.add_argument("--folder_out", type=Path, required=True)
  parser.add_argument("--overwrite", action="store_true")
  return normalize_text_files_in_folder


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



  _add_parser_to(subparsers, "add-rec", init_add_recording_parser)
  _add_parser_to(subparsers, "rec-clone", init_clone_parser)
  _add_parser_to(subparsers, "rec-add-silence", init_detect_silence_parser)
  _add_parser_to(subparsers, "rec-add-words", init_extract_words_parser)
  _add_parser_to(subparsers, "rec-add-ipa", init_convert_to_ipa_parser)
  _add_parser_to(subparsers, "rec-print-stats", init_log_stats_parser)
  _add_parser_to(subparsers, "rec-to-dataset", init_to_dataset_parser)
  _add_parser_to(subparsers, "mfa-normalize-texts", init_normalize_text_files_in_folder_parser)
  _add_parser_to(subparsers, "mfa-txt-to-textgrid", init_extract_sentences_text_files_parser)