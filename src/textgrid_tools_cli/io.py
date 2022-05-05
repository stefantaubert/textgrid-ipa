import copy
import logging
import multiprocessing
import queue
import threading
from argparse import ArgumentParser
from functools import partial
from logging import Logger, getLogger
from logging.handlers import QueueHandler
from math import inf, isinf
from multiprocessing.pool import Pool, ThreadPool
from pathlib import Path
from time import perf_counter
from typing import Dict, Iterable, List, Optional, Tuple

from ordered_set import OrderedSet
from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools_cli.helper import read_audio, save_grid
from textgrid_tools_cli.textgrid_io import parse_text


def process_save_grid(item: Tuple[str, Path, TextGrid]) -> None:
  stem, grid_file_out_abs, grid = item
  assert grid is not None
  try:
    save_grid(grid_file_out_abs, grid)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error(f"Grid file '{grid_file_out_abs.absolute()}' could not be saved!")
    logger.exception(ex)
    return False
  return True


def save_grids(grids: Iterable[Tuple[str, Path, TextGrid]], total: int, n_jobs: int = 1, chunksize: int = 1) -> List[bool]:

  with ThreadPool(
    processes=n_jobs,
  ) as pool:
    iterator = pool.imap_unordered(process_save_grid, grids, chunksize)
    iterator = tqdm(iterator, total=total, desc="Saving grid files", unit="grid(s)")
    successes = list(iterator)
  return successes


def process_read_text(item: Tuple[str, Path], encoding: str) -> Optional[str]:
  stem, path = item
  try:
    text = path.read_text(encoding)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error(f"File '{path.absolute()}' could not be read!")
    logger.exception(ex)
    return stem, None

  return stem, text


def load_texts(files: Iterable[Tuple[str, Path]], encoding: str, total: int, n_jobs: int = 1, chunksize: int = 1, desc: str = "text") -> Dict[str, str]:
  read_method_proxy = partial(
    process_read_text,
    encoding=encoding,
  )

  with ThreadPool(
    processes=n_jobs,
  ) as pool:
    iterator = pool.imap_unordered(read_method_proxy, files, chunksize)
    iterator = tqdm(iterator, total=total,
                    desc=f"Reading {desc} files", unit="file(s)")
    parsed_text_files = dict(iterator)

  remove_none_from_dict(parsed_text_files)

  return parsed_text_files


def process_read_grid(item: Tuple[str, Path], n_digits: int, encoding: str) -> Optional[str]:
  stem, path = item
  grid_in = TextGrid()
  try:
    grid_in.read(path, n_digits, encoding)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error(f"File '{path.absolute()}' could not be read!")
    logger.exception(ex)
    return stem, None

  return stem, grid_in


def load_grids(files: Iterable[Tuple[str, Path]], n_digits: int, encoding: str, total: int, n_jobs: int = 1, chunksize: int = 1) -> Dict[str, TextGrid]:
  read_method_proxy = partial(
    process_read_grid,
    n_digits=n_digits,
    encoding=encoding,
  )

  with Pool(
    processes=n_jobs,
  ) as pool:
    iterator = pool.imap_unordered(read_method_proxy, files, chunksize)
    iterator = tqdm(iterator, total=total,
                    desc="Reading grid files", unit="file(s)")
    parsed_files = dict(iterator)

  remove_none_from_dict(parsed_files)

  return parsed_files


def process_read_grid_from_text(item: Tuple[str, str]) -> Tuple[str, Optional[TextGrid]]:
  stem, text = item
  try:
    grid = parse_text(text)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error("Grid could not be parsed!")
    logger.exception(ex)
    return stem, None
  return stem, grid


def load_grids_from_text(files: Iterable[Tuple[str, str]], total: int, n_jobs: int = 1, chunksize: int = 1) -> Dict[str, TextGrid]:

  with Pool(
    processes=n_jobs,
  ) as pool:
    iterator = pool.imap_unordered(process_read_grid_from_text, files, chunksize)
    iterator = tqdm(iterator, total=total,
                    desc="Parsing grid files", unit="grid(s)")
    parsed_files = dict(iterator)

  remove_none_from_dict(parsed_files)

  return parsed_files


def remove_none_from_dict(d: Dict) -> None:
  none_keys = {k for k, v in d.items() if v is None}
  for k in none_keys:
    d.pop(k)


def process_read_audio_durations(item: Tuple[str, Path, List[str]]) -> Tuple[str, Optional[Tuple[int, int]]]:
  stem, path = item
  try:
    sample_rate, audio_in = read_audio(path)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error(f"Audio file '{path.absolute()}' could not be read!")
    logger.exception(ex)
    return stem, None
  audio_samples_in = audio_in.shape[0]
  return stem, (sample_rate, audio_samples_in)


def load_audio_durations(files: Iterable[Tuple[str, Path]], total: int, n_jobs: int = 1, chunksize: int = 1) -> Dict[str, Tuple[int, float]]:
  with ThreadPool(
    processes=n_jobs,
  ) as pool:
    iterator = pool.imap_unordered(process_read_audio_durations, files, chunksize)
    iterator = tqdm(iterator, total=total,
                    desc="Reading audio files", unit="file(s)")
    parsed_audio_files = dict(iterator)

  remove_none_from_dict(parsed_audio_files)

  return parsed_audio_files
