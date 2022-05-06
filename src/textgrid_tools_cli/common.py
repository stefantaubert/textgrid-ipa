from functools import partial
from logging import LogRecord, getLogger
from math import ceil
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter
from typing import Callable, Dict, List, Optional, OrderedDict, Tuple

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.globals import ExecutionResult
from textgrid_tools_cli.logging_queue import StoreRecordsHandlerFaster
from textgrid_tools_cli.helper import get_grid_files, try_copy_grid, try_load_grid, try_save_grid
from textgrid_tools_cli.logging_configuration import get_file_logger, init_and_get_console_logger


def process_grids_mp(directory: Path, encoding: str, output_directory: Optional[Path], overwrite: bool, method: Callable[[TextGrid], ExecutionResult], chunksize: int, n_jobs: int, maxtasksperchild: Optional[int]) -> ExecutionResult:
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid file(s).")

  total_success = True
  total_changed_anything = False
  method_proxy = partial(
    process_grid,
    method=method,
    encoding=encoding,
    overwrite=overwrite,
    directory=directory,
    output_directory=output_directory,
  )

  keys = grid_files.keys()
  # TODO remove
  keys = list(keys)[:10]

  flogger.debug(f"Files: {len(keys)}")
  flogger.debug(f"Chunksize: {chunksize}")
  flogger.debug(f"Maxtask: {maxtasksperchild}")
  flogger.debug(f"Jobs: {n_jobs}")

  amount_of_jobs_required = ceil(len(keys) / chunksize)
  n_jobs = min(n_jobs, amount_of_jobs_required)
  flogger.debug(f"Jobs (final): {n_jobs}")

  with Pool(
    processes=n_jobs,
    initializer=__init_pool,
    initargs=(grid_files,),
    maxtasksperchild=maxtasksperchild,
  ) as pool:
    iterator = pool.imap_unordered(method_proxy, keys, chunksize=chunksize)
    iterator = tqdm(iterator, total=len(keys), desc="Processing", unit="file(s)")
    result: Dict[str, Tuple[bool, bool, List[LogRecord]]] = dict(iterator)

  for stem, (_, _, records) in result.items():
    flogger.info(f"Log messages for file: {stem}")
    for x in records:
      flogger.handle(x)

  total_success = all(success for success, _, _ in result.values())
  total_changed_anything = any(changed_anything for _, changed_anything, _ in result.values())

  return total_success, total_changed_anything


process_grid_files: OrderedDict[str, Path] = None


def __init_pool(grid_files: OrderedDict[str, Path]) -> None:
  global process_grid_files
  process_grid_files = grid_files


def process_grid(file_stem: str, encoding: str, overwrite: bool, method: Callable[[TextGrid], ExecutionResult], directory: Path, output_directory: Path) -> Tuple[str, Tuple[bool, bool, List[LogRecord]]]:
  global process_grid_files
  handler = StoreRecordsHandlerFaster()
  logger = getLogger(file_stem)
  logger.propagate = False
  logger.addHandler(handler)

  start = perf_counter()

  rel_path = process_grid_files[file_stem]
  grid_file_out_abs = output_directory / rel_path

  if grid_file_out_abs.exists() and not overwrite:
    logger.info("Grid already exists. Skipped.")
    logger.debug(f"Duration (s): {perf_counter() - start}")
    return file_stem, (True, False, handler.records)

  grid_file_in_abs = directory / rel_path

  error, grid = try_load_grid(grid_file_in_abs, encoding)

  if error:
    logger.error(error.default_message)
    logger.debug(f"Duration (s): {perf_counter() - start}")
    return file_stem, (False, False, handler.records)
  assert grid is not None

  error, changed_anything = method(grid, logger=logger)
  success = error is None

  if not success:
    logger.error(error.default_message)
    logger.info("Skipped.")
    assert not changed_anything
  else:
    logger.info("Applied operations successfully.")
    if changed_anything:
      error = try_save_grid(grid_file_out_abs, grid, encoding)
      if error:
        logger.error(error.default_message, exc_info=error.exception)
        logger.debug(f"Duration (s): {perf_counter() - start}")
        return file_stem, (False, False, handler.records)
      logger.info(f"Saved the grid to: {grid_file_out_abs.absolute()}")
    elif directory != output_directory:
      logger.info("Didn't changed anything.")
      error = try_copy_grid(grid_file_in_abs, grid_file_out_abs)
      if error:
        logger.error(error.default_message, exc_info=error.exception)
      else:
        logger.info(f"Copied the grid to: {grid_file_out_abs.absolute()}")

  del grid
  logger.debug(f"Duration (s): {perf_counter() - start}")
  return file_stem, (success, changed_anything, handler.records)
