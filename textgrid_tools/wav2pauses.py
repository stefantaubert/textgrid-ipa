import os
from argparse import ArgumentParser
from dataclasses import dataclass
from logging import Logger, getLogger
from math import ceil, inf, log10
from typing import List, Optional, Tuple, Union

import numpy as np
from scipy.io.wavfile import read
from textgrid.textgrid import TextGrid
from tqdm import tqdm

from textgrid_tools.utils import (check_paths_ok, durations_to_interval_tier,
                                  get_parent_dirpath, ms_to_samples,
                                  update_or_add_tier)

SILENCE_INTERVAL_MARK = "pause"
CONTENT_INTERVAL_MARK = ""

FLOAT32_64_MIN_WAV = -1.0
INT16_MIN = np.iinfo(np.int16).min  # -32768 = -(2**15)
INT32_MIN = np.iinfo(np.int32).min  # -2147483648 = -(2**31)


def init_pause_parser(parser: ArgumentParser):
  parser.add_argument("--file", type=str, required=False, help="TextGrid input filepath.")
  parser.add_argument("--output", type=str, required=True, help="TextGrid output filepath.")
  parser.add_argument("--wav-file", type=str, required=True,
                      help="")
  parser.add_argument("--pauses-tier-name", type=str, default="pauses", help="")
  parser.add_argument("--silence-boundary", type=float, default=0.25,
                      help="Percent of lower dB recognized as silence.")
  parser.add_argument("--chunk-size-ms", type=int, default=50,
                      help="")
  parser.add_argument("--min-silence-duration-ms", type=int, default=700,
                      help="")
  parser.add_argument("--min-content-duration-ms", type=int, default=200,
                      help="")
  parser.add_argument("--content-buffer-start-ms", type=int, default=50,
                      help="")
  parser.add_argument("--content-buffer-end-ms", type=int, default=100,
                      help="")
  return add_pause


def add_pause(file: Optional[str], output: str, pauses_tier_name: str, wav_file: str, silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int, min_content_duration_ms: int, content_buffer_start_ms: int, content_buffer_end_ms: int) -> None:
  logger = getLogger()
  if file is None or check_paths_ok(file, output, logger):
    grid = TextGrid()
    if file is not None:
      grid.read(file)

    logger.info("Extracting pauses from wav...")

    sampling_rate, wav = read(wav_file)

    add_pause_tier(
      grid=grid,
      wav=wav,
      chunk_size_ms=chunk_size_ms,
      min_silence_duration_ms=min_silence_duration_ms,
      out_tier_name=pauses_tier_name,
      silence_boundary=silence_boundary,
      sr=sampling_rate,
      content_buffer_end_ms=content_buffer_end_ms,
      content_buffer_start_ms=content_buffer_start_ms,
      min_content_duration_ms=min_content_duration_ms,
      logger=logger,
    )

    os.makedirs(get_parent_dirpath(output), exist_ok=True)
    grid.write(output)
    logger.info("Success!")


def add_pause_tier(grid: Optional[TextGrid], wav: np.ndarray, sr: int, out_tier_name: Optional[str], silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int, min_content_duration_ms: int, content_buffer_start_ms: int, content_buffer_end_ms: int, logger: Logger) -> TextGrid:
  total_duration = get_duration_s(len(wav), sr)

  chunk_size = ms_to_samples(chunk_size_ms, sr)
  min_silence_duration = ms_to_samples(min_silence_duration_ms, sr)
  min_content_duration = ms_to_samples(min_content_duration_ms, sr)
  content_buffer_start = ms_to_samples(content_buffer_start_ms, sr)
  content_buffer_end = ms_to_samples(content_buffer_end_ms, sr)

  chunks = get_chunks(
    wav=wav,
    silence_boundary=silence_boundary,
    chunk_size=chunk_size,
    content_buffer_end=content_buffer_end,
    content_buffer_start=content_buffer_start,
    min_content_duration=min_content_duration,
    min_silence_duration=min_silence_duration,
  )

  logger.info(f"Extracted {len(chunks)} segments.")

  mark_duration: List[Tuple[str, float]] = list()
  for chunk in chunks:
    duration = get_duration_s(chunk.size, sr)
    mark = SILENCE_INTERVAL_MARK if chunk.is_silence else CONTENT_INTERVAL_MARK
    mark_duration.append((mark, duration))

  max_time = total_duration

  if grid is not None and len(grid.tiers) > 0:
    max_time = grid.tiers[0].maxTime

  pause_tier = durations_to_interval_tier(
    durations=mark_duration,
    maxTime=max_time,
  )

  pause_tier.name = out_tier_name

  if grid is None:
    grid = TextGrid(
      name="Grid",
      minTime=pause_tier.minTime,
      maxTime=pause_tier.maxTime,
      strict=True,
    )

  update_or_add_tier(grid, pause_tier)
  return grid


def get_dBFS(wav: np.ndarray, max_value: float) -> float:
  value = np.sqrt(np.mean((wav / max_value)**2))
  if value == 0:
    return -inf

  result = 20 * log10(value)
  return result


def get_duration_s(samples: int, sampling_rate: int) -> float:
  duration = samples / sampling_rate
  return duration


@dataclass
class Chunk:
  size: int
  is_silence: bool


def get_chunks(wav: np.ndarray, silence_boundary: float, chunk_size: int, min_silence_duration: int, min_content_duration: int, content_buffer_start: int, content_buffer_end: int) -> List[Chunk]:
  chunks = mask_silence(wav, silence_boundary, chunk_size)
  chunks = merge_same_coherent_chunks(chunks)
  chunks = merge_silent_chunks(chunks, min_silence_duration)
  chunks = merge_content_chunks(chunks, min_content_duration)
  chunks = add_content_start_buffer(chunks, content_buffer_start)
  chunks = add_content_end_buffer(chunks, content_buffer_end)
  return chunks


def add_content_start_buffer(chunks: List[Chunk], duration: int) -> List[Chunk]:
  content_mask = get_content_mask(chunks)
  tmp = add_start_buffer(chunks, content_mask, duration)
  tmp = remove_zero_duration_chunks(tmp)
  tmp = merge_same_coherent_chunks(tmp)
  return tmp


def add_start_buffer(chunks: List[Chunk], mask: List[bool], duration: int) -> List[Chunk]:
  assert len(chunks) == len(mask)
  if len(chunks) <= 1:
    return chunks

  for i in range(1, len(chunks)):
    current_mask = mask[i]
    current_chunk = chunks[i]
    previous_chunk = chunks[i - 1]
    if current_mask:
      reduce_duration = previous_chunk.size - max(0, previous_chunk.size - duration)
      # if it would be smaller than 0 there is a content therefore only the pause is removed
      previous_chunk.size -= reduce_duration
      current_chunk.size += reduce_duration

  return chunks


def add_content_end_buffer(chunks: List[Chunk], duration: int) -> List[Chunk]:
  content_mask = get_content_mask(chunks)
  tmp = add_end_buffer(chunks, content_mask, duration)
  tmp = remove_zero_duration_chunks(tmp)
  tmp = merge_same_coherent_chunks(tmp)
  return tmp


def add_end_buffer(chunks: List[Chunk], mask: List[bool], duration: int):
  assert len(chunks) == len(mask)
  if len(chunks) <= 1:
    return chunks

  for i in range(0, len(chunks) - 1):
    current_mask = mask[i]
    current_chunk = chunks[i]
    next_chunk = chunks[i + 1]
    if current_mask:
      reduce_duration = next_chunk.size - max(0, next_chunk.size - duration)
      # if it would be smaller than 0 there is a content therefore only the pause is removed
      next_chunk.size -= reduce_duration
      current_chunk.size += reduce_duration

  return chunks


def get_silence_mask(chunks: List[Chunk]) -> List[bool]:
  return [x.is_silence for x in chunks]


def get_content_mask(chunks: List[Chunk]) -> List[bool]:
  return [not x.is_silence for x in chunks]


def remove_zero_duration_chunks(chunks: List[Chunk]) -> List[Chunk]:
  res = [x for x in chunks if x.size > 0]
  return res


def merge_content_chunks(chunks: List[Chunk], min_duration: int) -> List[Chunk]:
  duration_mask = mask_too_short_entries(chunks, min_duration)
  process_mask = get_content_mask(chunks)
  mask = bool_and(duration_mask, process_mask)
  tmp = merge_marked_chunks(chunks, mask)
  tmp = merge_same_coherent_chunks(tmp)
  return tmp


def merge_silent_chunks(chunks: List[Chunk], min_duration: int) -> List[Chunk]:
  duration_mask = mask_too_short_entries(chunks, min_duration)
  process_mask = get_silence_mask(chunks)
  mask = bool_and(duration_mask, process_mask)
  tmp = merge_marked_chunks(chunks, mask)
  tmp = merge_same_coherent_chunks(tmp)
  return tmp


def mask_too_short_entries(chunks: List[Chunk], min_duration: int) -> List[bool]:
  res = [x.size < min_duration for x in chunks]
  return res


def bool_and(match_mask: List[bool], process_mask: List[bool]) -> List[bool]:
  res = [x and y for x, y in zip(match_mask, process_mask)]
  return res


def merge_marked_chunks(chunks: List[Chunk], merge_mask: List[bool]) -> List[Chunk]:
  assert len(chunks) == len(merge_mask)
  if len(chunks) == 1:
    return [chunks[0]]

  res: List[Chunk] = []
  merge_size = 0
  for i, _ in enumerate(chunks):
    current_chunk = chunks[i]
    merge_current_chunk = merge_mask[i]
    is_last_chunk = i == len(chunks) - 1
    if merge_current_chunk:
      if is_last_chunk:
        assert i - 1 >= 0
        assert merge_size == 0
        prev_chunk = chunks[i - 1]
        prev_chunk.size += current_chunk.size
      else:
        merge_size += current_chunk.size
    else:
      current_chunk.size += merge_size
      res.append(current_chunk)
      merge_size = 0

  return res


def merge_content_chunks_old(chunks: List[Chunk], min_duration: int) -> List[Chunk]:
  ''' Merges chunks with previous chunk if duration is smaller than min_duration. '''
  if len(chunks) <= 1:
    return chunks

  final_chunks: List[Chunk] = [chunks[0]]
  current_chunk: Chunk = None
  for i in range(1, len(chunks)):
    current_chunk = chunks[i]
    if current_chunk.is_silence:
      previous_chunk = chunks[i - 1]
      #assert not previous_chunk.is_silence
      merge_previous_chunk = previous_chunk.size < min_duration
      if merge_previous_chunk:
        current_chunk.size += previous_chunk.size
        final_chunks.append(current_chunk)
      else:
        final_chunks.append(previous_chunk)
        final_chunks.append(current_chunk)

  assert current_chunk is not None
  last_chunk = current_chunk

  if not last_chunk.is_silence:
    assert len(final_chunks) >= 1
    merge_last_chunk = last_chunk.size < min_duration
    if merge_last_chunk:
      previous_chunk = final_chunks[-1]
      previous_chunk.size += last_chunk.size
    else:
      final_chunks.append(last_chunk)

  return final_chunks


def merge_chunks(chunks: List[Chunk], min_duration: int, merge_silence: bool) -> List[Chunk]:
  ''' Merges chunks with previous chunk if duration is smaller than min_duration. '''
  if len(chunks) <= 1:
    return chunks

  final_chunks: List[Chunk] = list()
  current_chunk: Chunk = None
  for i in range(1, len(chunks)):
    current_chunk = chunks[i]
    process_chunk = (not merge_silence and current_chunk.is_silence) or (
      merge_silence and not current_chunk.is_silence)
    if process_chunk:
      previous_chunk = chunks[i - 1]
      #assert not previous_chunk.is_silence
      merge_previous_chunk = previous_chunk.size < min_duration
      if merge_previous_chunk:
        current_chunk.size += previous_chunk.size
        final_chunks.append(current_chunk)
      else:
        final_chunks.append(previous_chunk)
        final_chunks.append(current_chunk)

  if len(final_chunks) == 0:
    final_chunks.append(chunks[0])

  assert current_chunk is not None
  last_chunk = current_chunk
  if merge_silence:
    if last_chunk.is_silence:
      merge_last_chunk = last_chunk.size < min_duration
      if merge_last_chunk:
        previous_chunk = final_chunks[-1]
        previous_chunk.size += last_chunk.size
      else:
        final_chunks.append(last_chunk)
    else:
      final_chunks.append()

  process_last_chunk = (not merge_silence and not last_chunk.is_silence) or (
    merge_silence and last_chunk.is_silence)
  if process_last_chunk:
    assert len(final_chunks) >= 1
    merge_last_chunk = last_chunk.size < min_duration
    if merge_last_chunk:
      previous_chunk = final_chunks[-1]
      previous_chunk.size += last_chunk.size
    else:
      final_chunks.append(last_chunk)

  return final_chunks


def merge_same_coherent_chunks(chunks: List[Chunk]) -> List[Chunk]:
  if len(chunks) <= 1:
    return chunks

  current_samples: int = 0
  last_chunk: Optional[Chunk] = None
  splits: List[Chunk] = list()

  chunk: Chunk
  for chunk in tqdm(chunks):
    if last_chunk is None or chunk.is_silence == last_chunk.is_silence:
      current_samples += chunk.size
    else:
      c = Chunk(
        is_silence=last_chunk.is_silence,
        size=current_samples
      )
      splits.append(c)
      # splits.append((last_chunk, current_samples))
      current_samples = chunk.size
    last_chunk = chunk

  if current_samples > 0:
    c = Chunk(
      is_silence=last_chunk.is_silence,
      size=current_samples
    )
    splits.append(c)

  return splits


def chunk_wav(wav: np.ndarray, chunk_size: int) -> List[np.ndarray]:
  assert chunk_size > 0
  if chunk_size > len(wav):
    chunk_size = len(wav)
  its = len(wav) / chunk_size
  its = ceil(its)
  trim = 0
  res = []
  for _ in range(its):
    res.append(wav[trim:trim + chunk_size])
    trim += chunk_size
  return res


def get_dBFS_chunks(wav_chunks: List[np.ndarray], max_val: Union[int, float]) -> List[float]:
  dBFSs = [get_dBFS(x, max_val) for x in wav_chunks]
  return dBFSs


def mask_silence(wav: np.ndarray, silence_boundary: float, chunk_size: int):
  wav_chunks = chunk_wav(wav, chunk_size)
  max_value = -1 * get_min_value(wav.dtype)
  dBFSs = get_dBFS_chunks(wav_chunks, max_value)
  threshold = get_silence_threshold(dBFSs, silence_boundary)
  result = get_silence_chunks(wav_chunks, dBFSs, threshold)
  return result


def get_silence_threshold(dBFSs: List[float], silence_boundary: float) -> float:
  print(dBFSs)
  print(min(dBFSs))
  print(max(dBFSs))
  diff = abs(abs(min(dBFSs)) - abs(max(dBFSs)))
  threshold = diff * silence_boundary
  silence_threshold = min(dBFSs) + threshold
  return silence_threshold


def get_silence_chunks(wav_chunks: List[np.ndarray], dBFSs: List[float], silence_threshold: float):
  res: List[Chunk] = list()
  for chunk, dBFS in tqdm(zip(wav_chunks, dBFSs)):
    is_silence = dBFS < silence_threshold
    chunk_len = len(chunk)
    chunk = Chunk(
      size=chunk_len,
      is_silence=is_silence
    )
    res.append(chunk)

  return res


def get_min_value(dtype):
  if dtype == np.int16:
    return INT16_MIN

  if dtype == np.int32:
    return INT32_MIN

  if dtype == np.float32 or dtype == np.float64:
    return FLOAT32_64_MIN_WAV

  assert False
