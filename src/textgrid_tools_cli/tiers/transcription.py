from argparse import ArgumentParser, Namespace
from functools import partial

from pronunciation_dictionary import DeserializationOptions, MultiprocessingOptions, load_dict

from textgrid_tools import transcribe_text
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument, add_directory_argument,
                                       add_dry_run_argument, add_encoding_argument,
                                       add_maxtaskperchild_argument, add_n_jobs_argument,
                                       add_output_directory_argument, add_overwrite_argument,
                                       add_tiers_argument, get_optional, parse_existing_file,
                                       parse_non_negative_integer, parse_positive_integer)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_transcription_parser(parser: ArgumentParser):
  parser.description = "This command transcribes words using a pronunciation dictionary."
  add_directory_argument(parser)
  parser.add_argument("dictionary", metavar="DICTIONARY", type=parse_existing_file,
                      help="path to the pronunciation dictionary that contains pronunciations to all occurring marks")
  add_tiers_argument(parser, "tiers which should be transcribed")
  parser.add_argument("--seed", type=get_optional(parse_non_negative_integer), metavar="SEED",
                      help="seed for choosing the pronunciation from the dictionary (only useful if there exist words with multiple pronunciations)", default=None)
  parser.add_argument("--ignore-missing", action="store_true",
                      help="keep marks missing in dictionary unchanged")
  parser.add_argument("--assign-mark-to-missing", type=get_optional(str), metavar="MISSING-MARK", default=None,
                      help="if ignore-missing is true: assign this mark to the missing pronunciations; per default the interval marks will be kept unchanged")
  add_deserialization_group(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)

  mp_group = parser.add_argument_group('multiprocessing arguments')
  add_n_jobs_argument(mp_group)
  add_chunksize_argument(mp_group)
  mp_group.add_argument("-sd", "--chunksize-dictionary", type=parse_positive_integer, metavar="NUMBER",
                        help="amount of lines to chunk into one job", default=10000)
  add_maxtaskperchild_argument(mp_group)
  add_dry_run_argument(parser)
  return app_transcribe_text_v2


def add_deserialization_group(parser: ArgumentParser) -> None:
  group = parser.add_argument_group('deserialization arguments')
  add_encoding_argument(group, "encoding of the grid files and the dictionary")
  group.add_argument("-cc", "--consider-comments", action="store_true",
                     help="consider line comments while deserialization")
  group.add_argument("-cn", "--consider-numbers", action="store_true",
                     help="consider word numbers used to separate different pronunciations")
  group.add_argument("-cp", "--consider-pronunciation-comments", action="store_true",
                     help="consider comments in pronunciations")
  group.add_argument("-cw", "--consider-weights", action="store_true",
                     help="consider weights")


def app_transcribe_text_v2(ns: Namespace) -> ExecutionResult:
  mp_options = MultiprocessingOptions(ns.n_jobs, ns.maxtasksperchild, ns.chunksize_dictionary)
  options = DeserializationOptions(ns.consider_comments, ns.consider_numbers,
                                   ns.consider_pronunciation_comments, ns.consider_weights)
  try:
    pronunciation_dictionary = load_dict(ns.dictionary, ns.encoding, options, mp_options)
  except Exception as ex:
    logger = init_and_get_console_logger(__name__)
    logger.error("Pronunciation dictionary couldn't be read!")
    flogger = get_file_logger()
    flogger.exception(ex)
    return False, False

  method = partial(
    transcribe_text,
    tier_names=ns.tiers,
    pronunciation_dictionary=pronunciation_dictionary,
    seed=ns.seed,
    ignore_missing=ns.ignore_missing,
    replace_missing=ns.assign_mark_to_missing,
  )

  return process_grids_mp(ns.directory, ns.encoding, ns.output_directory, ns.overwrite, method, ns.chunksize, ns.n_jobs, ns.maxtasksperchild, ns.dry)
