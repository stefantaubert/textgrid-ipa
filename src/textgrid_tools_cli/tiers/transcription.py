from argparse import ArgumentParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Optional, Set

from ordered_set import OrderedSet
from pronunciation_dict_parser import parse_dictionary_from_txt
from text_utils.string_format import StringFormat
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument,
                                       add_encoding_argument,
                                       add_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_string_format_argument,
                                       add_tiers_argument, parse_existing_file)
from textgrid_tools.core import transcribe_text


def get_transcription_parser(parser: ArgumentParser):
  parser.description = "This command transcribes words using a pronunciation dictionary."
  add_directory_argument(parser)
  parser.add_argument("dictionary", metavar="dictionary", type=parse_existing_file,
                      help="path to the pronunciation dictionary")
  add_tiers_argument(parser, "tiers which should be transcribed")
  add_string_format_argument(parser, "tiers")
  add_encoding_argument(parser, "encoding of the dictionary")
  # add_n_jobs_argument(parser)
  # parser.add_argument("--chunksize", type=int, metavar="NUMBER",
  #                     help="amount of intervals to chunk into one job", default=500)
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_transcribe_text


def app_transcribe_text(directory: Path, tiers: OrderedSet[str], formatting: StringFormat, dictionary: Path, encoding: str, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  pronunciation_dictionary = parse_dictionary_from_txt(dictionary, encoding)

  method = partial(
    transcribe_text,
    pronunciation_dictionary=pronunciation_dictionary,
    tier_names=tiers,
    tiers_string_format=formatting,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
