import logging
import os
from functools import partial
from logging import Logger, getLogger
from multiprocessing import Pool
from pathlib import Path
from typing import Callable, List, Optional, OrderedDict, Tuple

from textgrid.textgrid import TextGrid
from textgrid_tools_cli.helper import (copy_grid, get_grid_files, save_grid,
                                       try_load_grid)
from textgrid_tools.globals import ExecutionResult


def getFileLogger() -> Logger:
  logger = getLogger("file-logger")
  if logger.propagate:
    logger.propagate = False
  return logger


def try_initFileLogger(path: Path) -> None:
  try:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.remove(path)
    path.write_text("")
    fh = logging.FileHandler(path)
    fh.setLevel(logging.DEBUG)
    flogger = getFileLogger()
    flogger.addHandler(fh)
  except:
    logger = getLogger(__name__)
    logger.error("Logfile couldn't be created!")


def process_grids(directory: Path, n_digits: int, output_directory: Optional[Path], overwrite: bool, method: Callable[[TextGrid], ExecutionResult]) -> ExecutionResult:
  logger = getLogger(__name__)

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)

  total_success = True
  total_changed_anything = False
  for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
    logger.info(f"Processing {file_stem} ({file_nr}/{len(grid_files)})...")
    grid_file_out_abs = output_directory / rel_path

    if grid_file_out_abs.exists() and not overwrite:
      logger.info("Grid already exists. Skipped.")
      continue

    grid_file_in_abs = directory / rel_path
    grid = try_load_grid(grid_file_in_abs, n_digits)

    error, changed_anything = method(grid)

    success = error is None
    total_success &= success
    total_changed_anything |= changed_anything

    if not success:
      logger.error(error.default_message)
      logger.info("Skipped.")
      continue

    if changed_anything:
      save_grid(grid_file_out_abs, grid)
    elif directory != output_directory:
      copy_grid(grid_file_in_abs, grid_file_out_abs)

  return total_success, total_changed_anything


def process_grids_mp(directory: Path, n_digits: int, output_directory: Optional[Path], overwrite: bool, method: Callable[[TextGrid], ExecutionResult], chunksize: int, n_jobs: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  logger = getLogger(__name__)

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)

  total_success = True
  total_changed_anything = False
  method_proxy = partial(
    process_grid,
    method=method,
    n_digits=n_digits,
    overwrite=overwrite,
    directory=directory,
    output_directory=output_directory,
  )

  with Pool(
    processes=n_jobs,
    initializer=__init_pool,
    initargs=(grid_files,),
    maxtasksperchild=maxtasksperchild,
  ) as pool:
    result: List[Tuple[bool, bool]] = list(pool.imap_unordered(
      method_proxy, enumerate(grid_files.keys(), start=1), chunksize=chunksize))

  total_success = all(success for success, _ in result)
  total_changed_anything = any(changed_anything for _, changed_anything in result)

  return total_success, total_changed_anything


process_grid_files: OrderedDict[str, Path] = None


def __init_pool(grid_files: OrderedDict[str, Path]) -> None:
  global process_grid_files
  process_grid_files = grid_files


def process_grid(i_file_stem: str, n_digits: int, overwrite: bool, method: Callable[[TextGrid], ExecutionResult], directory: Path, output_directory: Path) -> Tuple[bool, bool]:
  logger = getLogger(__name__)
  global process_grid_files
  file_nr, file_stem = i_file_stem
  rel_path = process_grid_files[file_stem]
  logger_prepend = f"[{file_stem}]"
  logger.info(f"Processing {file_stem} ({file_nr}/{len(process_grid_files)})...")
  grid_file_out_abs = output_directory / rel_path

  if grid_file_out_abs.exists() and not overwrite:
    logger.info(f"{logger_prepend} Grid already exists. Skipped.")
    return True, False

  grid_file_in_abs = directory / rel_path

  error, grid = try_load_grid(grid_file_in_abs, n_digits)

  if error:
    logger.error(error.default_message)
    return False, False
  assert grid is not None

  error, changed_anything = method(grid)
  success = error is None

  if not success:
    logger.error(f"{logger_prepend} {error.default_message}")
    logger.info(f"{logger_prepend} Skipped.")
    assert not changed_anything
  else:
    if changed_anything:
      save_grid(grid_file_out_abs, grid)
    elif directory != output_directory:
      copy_grid(grid_file_in_abs, grid_file_out_abs)
  return success, changed_anything
