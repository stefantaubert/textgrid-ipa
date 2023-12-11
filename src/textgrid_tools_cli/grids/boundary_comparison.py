from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Callable, List, Tuple, cast

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.grids.boundary_comparison import compare_multiple_grids
from textgrid_tools_cli.globals import ExecutionResult
from textgrid_tools_cli.helper import (ConvertToSetAction, add_directory_argument,
                                       add_encoding_argument, add_tier_argument, get_grid_files,
                                       get_optional, parse_existing_directory, parse_json,
                                       parse_path, parse_positive_float, try_load_grid)
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def get_boundary_comparison_parser(parser: ArgumentParser) -> Callable:
  parser.description = "This command compares the interval boundaries between grid files."
  add_directory_argument(parser)
  parser.add_argument("comparison_directory", type=parse_existing_directory, metavar="COMPARISON-DIRECTORY",
                      help="directory with the grid files that should be compared")
  add_tier_argument(parser, help_str="name of the tier, that contain the intervals that should be compared")
  parser.add_argument("output", type=parse_path, metavar="OUTPUT",
                      help="file to write the generated statistics (.csv)")
  parser.add_argument("--limits", type=get_optional(parse_positive_float), metavar="DURATION", nargs="*",                      help="limits that should be calculated (ms)", default={10, 20, 30}, action=ConvertToSetAction)
  parser.add_argument(
    "--ignore", type=str, help="ignore these marks", metavar="MARK", default={""}, nargs="*", action=ConvertToSetAction)
  parser.add_argument("--extra-groups", type=get_optional(parse_json), metavar="EXTRA-GROUP-JSON", help="add evaluation of these groups (keys=group name, values=list of marks)")
  add_encoding_argument(parser)
  return main


def main(ns: Namespace) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  grid_files1 = get_grid_files(ns.directory)

  grids: List[Tuple[TextGrid, TextGrid]] = []
  for file_nr, (file_stem, rel_path) in enumerate(tqdm(grid_files1.items()), start=1):
    flogger.info(f"Processing {file_stem}")
    grid_file1_in_abs = ns.directory / rel_path
    error, grid1 = try_load_grid(grid_file1_in_abs, ns.encoding)

    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue
    
    grid_file2_in_abs = ns.comparison_directory / rel_path
    error, grid2 = try_load_grid(grid_file2_in_abs, ns.encoding)
    
    if error:
      flogger.debug(error.exception)
      flogger.error(error.default_message)
      flogger.info("Skipped.")
      continue
    assert grid1 is not None
    assert grid2 is not None

    grids.append((grid1, grid2))

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False
  
  print(f"Found {len(grids)} grid pairs.")
  extra_groups = ns.extra_groups if ns.extra_groups else {}
  res_df, ref_fig = compare_multiple_grids(grids, ns.tier, ns.ignore, ns.limits, extra_groups)

  success = error is None

  if not success:
    logger.error(error.default_message)
    return False, False

  cast(Path, ns.output).parent.mkdir(parents=True, exist_ok=True)
  try:
    res_df.to_csv(ns.output, index=False)
  except Exception as ex:
    logger.error("Saving of output was not successful!")
    logger.debug(ex)
    return False, True
  try:
    ref_fig.savefig(str(ns.output) + ".png")
    ref_fig.savefig(str(ns.output) + ".pdf")
  except Exception as ex:
    logger.error("Saving of output image was not successful!")
    logger.debug(ex)
    return False, True

  logger.info(f"Exported statistics to: \"{ns.output.absolute()}\".")
  logger.info(f"Exported statistics to: \"{ns.output.absolute()}.png\".")

  return True, True
