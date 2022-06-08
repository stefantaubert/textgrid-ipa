from functools import partial
from logging import getLogger
from multiprocessing.pool import Pool, ThreadPool
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools_cli.helper import read_audio, try_save_grid
from textgrid_tools_cli.textgrid_io import get_lines, parse_text


def process_save_grid(item: Tuple[str, Path, TextGrid]) -> None:
  stem, grid_file_out_abs, grid = item
  assert grid is not None
  try:
    try_save_grid(grid_file_out_abs, grid, "UTF-8")
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


def process_save_text(item: Tuple[str, Path, str], encoding: str) -> None:
  stem, path, text = item
  assert text is not None
  try:
    path.write_text(text, encoding)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error(f"File '{path.absolute()}' could not be saved!")
    logger.exception(ex)
    return False
  return True


def save_texts(texts: Iterable[Tuple[str, Path, str]], encoding: str, total: int, n_jobs: int = 1, chunksize: int = 1) -> List[bool]:
  method_proxy = partial(
    process_save_text,
    encoding=encoding,
  )

  with ThreadPool(
    processes=n_jobs,
  ) as pool:
    iterator = pool.imap_unordered(method_proxy, texts, chunksize)
    iterator = tqdm(iterator, total=total, desc="Saving files", unit="file(s)")
    successes = list(iterator)
  return successes


def process_serialize_grid(item: Tuple[str, TextGrid]) -> Tuple[str, Optional[str]]:
  stem, grid = item
  assert grid is not None
  try:
    lines = get_lines(grid)
    text = '\n'.join(lines)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error("Grid could not be serialized!")
    logger.exception(ex)
    return stem, None
  return stem, text


def serialize_grids(grids: Iterable[Tuple[str, Path, TextGrid]], total: int, n_jobs: int = 1, chunksize: int = 1, maxtasksperchild: Optional[int] = None) -> Dict[str, str]:
  with Pool(
    processes=n_jobs,
    maxtasksperchild=maxtasksperchild,
  ) as pool:
    iterator = pool.imap_unordered(process_serialize_grid, grids, chunksize)
    iterator = tqdm(iterator, total=total, desc="Serializing grids", unit="grid(s)")
    texts = dict(iterator)

  remove_none_from_dict(texts)

  return texts


def process_serialize_grid_v2(stem: str) -> Tuple[str, Optional[str]]:
  global process_serialize_grid_v2_data
  grid = process_serialize_grid_v2_data[stem]
  assert grid is not None
  try:
    lines = get_lines(grid)
    text = '\n'.join(lines)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error("Grid could not be serialized!")
    logger.exception(ex)
    return stem, None
  print(f"serialized {stem}")
  return stem, text


process_serialize_grid_v2_data: Dict[str, TextGrid] = None


def init_serialize_grids_v2_pool(data: Dict[str, TextGrid]) -> None:
  global process_serialize_grid_v2_data
  process_serialize_grid_v2_data = data


def serialize_grids_v2(grids: Dict[str, TextGrid], n_jobs: int = 1, chunksize: int = 1, maxtasksperchild: Optional[int] = None) -> Dict[str, str]:
  with Pool(
    processes=n_jobs,
    maxtasksperchild=maxtasksperchild,
    initializer=init_serialize_grids_v2_pool,
    initargs=(grids,),
  ) as pool:
    iterator = pool.imap_unordered(process_serialize_grid_v2, grids, chunksize)
    iterator = tqdm(iterator, total=len(grids), desc="Serializing grids", unit="grid(s)")
    texts = dict(iterator)

  remove_none_from_dict(texts)

  return texts


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


def process_read_grid(item: Tuple[str, Path], encoding: str) -> Optional[str]:
  stem, path = item
  grid_in = TextGrid()
  try:
    grid_in.read(path, 16, encoding)
  except Exception as ex:
    logger = getLogger(stem)
    logger.error(f"File '{path.absolute()}' could not be read!")
    logger.exception(ex)
    return stem, None

  return stem, grid_in


def load_grids(files: Iterable[Tuple[str, Path]], encoding: str, total: int, n_jobs: int = 1, chunksize: int = 1, maxtasksperchild: Optional[int] = None) -> Dict[str, TextGrid]:
  read_method_proxy = partial(
    process_read_grid,
    encoding=encoding,
  )

  with Pool(
    processes=n_jobs,
    maxtasksperchild=maxtasksperchild,
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


def deserialize_grids(texts: Iterable[Tuple[str, str]], total: int, n_jobs: int = 1, chunksize: int = 1) -> Dict[str, TextGrid]:

  with Pool(
    processes=n_jobs,
  ) as pool:
    iterator = pool.imap_unordered(process_read_grid_from_text, texts, chunksize)
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
    logger.exception(ex)
    logger.error(f"Audio file '{path.absolute()}' could not be read!")
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
