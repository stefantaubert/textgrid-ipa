from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional, Set

from ordered_set import OrderedSet
from pronunciation_dictionary import (DeserializationOptions,
                                      MultiprocessingOptions,
                                      get_dict_from_file)
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument,
                                       add_directory_argument,
                                       add_encoding_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_tiers_argument, get_optional,
                                       parse_existing_file,
                                       parse_non_negative_integer,
                                       parse_positive_integer)
from textgrid_tools.core import transcribe_text_v2


def get_transcription_v2_parser(parser: ArgumentParser):
  parser.description = "This command transcribes words using a pronunciation dictionary."
  add_directory_argument(parser)
  parser.add_argument("dictionary", metavar="dictionary", type=parse_existing_file,
                      help="path to the pronunciation dictionary that contains pronunciations to all occurring marks")
  add_tiers_argument(parser, "tiers which should be transcribed")
  parser.add_argument("--seed", type=get_optional(parse_non_negative_integer),
                      help="seed for choosing the pronunciation from the dictionary (only usefull if there exist words with multiple pronunciations)", default=None)
  parser.add_argument("--ignore-missing", action="store_true",
                      help="keep marks missing in dictionary unchanged")
  add_deserialization_group(parser)
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)

  mp_group = parser.add_argument_group('multiprocessing arguments')
  add_n_jobs_argument(mp_group)
  add_chunksize_argument(mp_group)
  mp_group.add_argument("-sd", "--chunksize-dictionary", type=parse_positive_integer, metavar="NUMBER",
                        help=f"amount of lines to chunk into one job", default=10000)
  add_maxtaskperchild_argument(mp_group)
  return app_transcribe_text_v2


def add_deserialization_group(parser: ArgumentParser) -> None:
  group = parser.add_argument_group('deserialization arguments')
  add_encoding_argument(group, "encoding of the dictionary")
  group.add_argument("-cc", "--consider-comments", action="store_true",
                     help="consider line comments while deserialization")
  group.add_argument("-cn", "--consider-numbers", action="store_true",
                     help="consider word numbers used to separate different pronunciations")
  group.add_argument("-cp", "--consider-pronunciation-comments", action="store_true",
                     help="consider comments in pronunciations")
  group.add_argument("-cw", "--consider-weights", action="store_true",
                     help="consider weights")


def app_transcribe_text_v2(directory: Path, tiers: OrderedSet[str], dictionary: Path, encoding: str, n_digits: int, output_directory: Optional[Path], overwrite: bool, consider_comments: bool, consider_numbers: bool, consider_pronunciation_comments: bool, consider_weights: bool, seed: Optional[int], ignore_missing: bool, n_jobs: int, chunksize: int, chunksize_dictionary: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  mp_options = MultiprocessingOptions(n_jobs, maxtasksperchild, chunksize_dictionary)
  options = DeserializationOptions(consider_comments, consider_numbers,
                                   consider_pronunciation_comments, consider_weights)
  try:
    pronunciation_dictionary = get_dict_from_file(dictionary, encoding, options, mp_options)
  except Exception as ex:
    logger = getLogger(__name__)
    logger.error("Pronunciation dictionary couldn't be read!")
    logger.debug(ex)
    return False, False

  method = partial(
    transcribe_text_v2,
    tier_names=tiers,
    pronunciation_dictionary=pronunciation_dictionary,
    seed=seed,
    ignore_missing=ignore_missing,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
