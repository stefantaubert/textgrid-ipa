from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import Optional

from ordered_set import OrderedSet
from textgrid_tools_cli.common import process_grids_mp
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (add_chunksize_argument,
                                       add_directory_argument,
                                       add_maxtaskperchild_argument,
                                       add_n_digits_argument,
                                       add_n_jobs_argument,
                                       add_output_directory_argument,
                                       add_overwrite_argument,
                                       add_tiers_argument)
from textgrid_tools.core import split_v2


def get_splitting_v2_parser(parser: ArgumentParser):
  parser.description = "This command splits the content of a tier."
  add_directory_argument(parser, "directory containing the grid files which should be modified")
  add_tiers_argument(parser, "tiers which should be split")
  parser.add_argument('--symbol', type=str, help="split on this symbol", default=" ")
  parser.add_argument("--keep", action="store_true",
                      help="keep the split symbol in a separate interval")
  add_n_digits_argument(parser)
  add_output_directory_argument(parser)
  add_overwrite_argument(parser)
  add_n_jobs_argument(parser)
  add_chunksize_argument(parser)
  add_maxtaskperchild_argument(parser)
  return app_split_v2


def app_split_v2(directory: Path, tiers: OrderedSet[str], symbol: str, keep: bool, n_digits: int, output_directory: Optional[Path], overwrite: bool, n_jobs: int, chunksize: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  method = partial(
    split_v2,
    symbol=symbol,
    keep=keep,
    tier_names=tiers,
  )

  return process_grids_mp(directory, n_digits, output_directory, overwrite, method, chunksize, n_jobs, maxtasksperchild)
