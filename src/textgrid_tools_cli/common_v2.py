import logging
from functools import partial
from logging import getLogger
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter
from typing import Callable, Dict, List, Optional, Tuple

from ordered_set import OrderedSet
from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.globals import ExecutionResult
from textgrid_tools_cli.helper import get_chunks, get_grid_files
from textgrid_tools_cli.io import (deserialize_grids, load_texts, remove_none_from_dict, save_texts,
                                   serialize_grids)
from textgrid_tools_cli.logging_configuration import (get_file_logger, init_and_get_console_logger,
                                                      init_file_stem_logger_lists,
                                                      try_init_file_logger,
                                                      write_file_stem_logger_lists_to_file_logger)

# def process_grids(directory: Path, output_directory: Optional[Path], overwrite: bool, method: Callable[[TextGrid], ExecutionResult]) -> ExecutionResult:
#   logger = getLogger(__name__)

#   if output_directory is None:
#     output_directory = directory

#   grid_files = get_grid_files(directory)

#   total_success = True
#   total_changed_anything = False
#   for file_nr, (file_stem, rel_path) in enumerate(grid_files.items(), start=1):
#     logger.info(f"Processing {file_stem} ({file_nr}/{len(grid_files)})...")
#     grid_file_out_abs = output_directory / rel_path

#     if grid_file_out_abs.exists() and not overwrite:
#       logger.info("Grid already exists. Skipped.")
#       continue

#     grid_file_in_abs = directory / rel_path
#     grid = try_load_grid(grid_file_in_abs, n_digits)

#     error, changed_anything = method(grid)

#     success = error is None
#     total_success &= success
#     total_changed_anything |= changed_anything

#     if not success:
#       logger.error(error.default_message)
#       logger.info("Skipped.")
#       continue

#     if changed_anything:
#       save_grid(grid_file_out_abs, grid)
#     elif directory != output_directory:
#       copy_grid(grid_file_in_abs, grid_file_out_abs)

#   return total_success, total_changed_anything


def process_grids_mp(directory: Path, encoding: str, output_directory: Optional[Path], method: Callable[[TextGrid], ExecutionResult], chunksize: int, n_jobs: int, maxtasksperchild: Optional[int], log: Optional[Path], chunk: Optional[int]) -> ExecutionResult:

  start = perf_counter()
  if log:
    try_init_file_logger(log)
  logger = init_and_get_console_logger(__name__)
  flogger = get_file_logger()

  if output_directory is None:
    output_directory = directory

  grid_files = get_grid_files(directory)
  logger.info(f"Found {len(grid_files)} grid files.")

  file_stems = OrderedSet(grid_files.keys())

  logging_queues = init_file_stem_logger_lists(file_stems)

  chunked_list = get_chunks(file_stems, chunk)

  # TODO remove, only for debugging
  chunked_list = chunked_list[:1]

  total_success = True
  total_changed_anything = False

  method_proxy = partial(
    process_grid,
    method=method,
  )

  logger.debug(f"Jobs: {n_jobs}")
  logger.debug(f"Maxtask: {maxtasksperchild}")
  logger.debug(f"Chunksize: {chunksize}")
  logger.debug(f"Files: {len(file_stems)}")

  file_chunk: OrderedSet[str]
  for file_chunk in tqdm(chunked_list, desc="Processing chunks", unit="chunk(s)", position=0):
    # reading grids
    process_data = (
      (stem, directory / grid_files[stem])
      for stem in file_chunk
    )
    parsed_grid_files_as_text = load_texts(process_data, encoding, len(file_chunk), desc="grid")
    parsed_grid_files = deserialize_grids(
      parsed_grid_files_as_text.items(), len(parsed_grid_files_as_text), n_jobs, chunksize)

    # loggers = dict(zip(file_chunk, get_file_stem_loggers(file_chunk)))
    # processing grids
    with Pool(
      processes=n_jobs,
      initializer=__init_pool,
      initargs=(logging_queues,),
      maxtasksperchild=maxtasksperchild,
    ) as pool:
      iterator = pool.imap_unordered(method_proxy, parsed_grid_files.items(), chunksize)
      iterator = tqdm(iterator, total=len(parsed_grid_files),
                      desc="Processing", unit="file(s)")
      process_results: Dict[str, Tuple[Optional[TextGrid], bool]] = dict(iterator)

    remove_none_from_dict(process_results)

    # saving grids
    process_data = (
      (stem, grid)
      for stem, (grid, changed_anything) in process_results.items()
    )
    serialized_grids = serialize_grids(process_data, len(process_results), n_jobs, chunksize)
    process_data = (
      (stem, output_directory / f"{stem}.TextGrid", text)
      for stem, text in serialized_grids.items()
    )
    successes = save_texts(process_data, encoding, len(serialized_grids))

    total_success &= all(successes) and len(successes) == len(file_chunk)
    total_changed_anything |= any(changed_anything for grid,
                                  changed_anything in process_results.values())

  write_file_stem_logger_lists_to_file_logger(logging_queues)

  duration = perf_counter() - start
  flogger.debug(f"Total duration (s): {duration}")
  if log:
    logger = getLogger()
    logger.info(f"Written log to: {log.absolute()}")
  return total_success, total_changed_anything


process_logging_queues: Dict[str, List[Tuple[int, str]]] = None


def __init_pool(logging_queues: Dict[str, List[Tuple[int, str]]]) -> None:
  global process_logging_queues
  process_logging_queues = logging_queues


def process_grid(stem_grid: Tuple[str, TextGrid], method: Callable[[TextGrid], ExecutionResult]) -> Tuple[str, Optional[Tuple[TextGrid, bool]]]:
  global process_logging_queues
  file_stem, grid = stem_grid
  # try manual log(Level, args..) to cache
  # logger = multiprocessing.get_logger()
  logging_list = process_logging_queues[file_stem]
  # logger = getLogger(file_stem)

  error, changed_anything = method(grid)
  success = error is None

  if not success:
    logging_list.append((logging.ERROR, error.default_message))
    logging_list.append((logging.INFO, "Skipped."))
    assert not changed_anything
    return file_stem, None

  logging_list.append((logging.INFO, "Applied operations successfull."))

  if not changed_anything:
    logging_list.append((logging.INFO, "Didn't changed anything."))

  return file_stem, (grid, changed_anything)
