from argparse import ArgumentParser
from dataclasses import dataclass
from logging import getLogger
from math import ceil, inf, log10
from typing import List, Optional, Tuple

import numpy as np
from scipy.io.wavfile import read
from tqdm import tqdm
from tqdm.std import trange

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import check_paths_ok, ms_to_samples, update_or_add_tier

FLOAT32_64_MIN_WAV = -1.0
INT16_MIN = np.iinfo(np.int16).min  # -32768 = -(2**15)
INT32_MIN = np.iinfo(np.int32).min  # -2147483648 = -(2**31)


def init_pause_parser(parser: ArgumentParser):
  parser.add_argument("-f", "--file", type=str, required=False, help="TextGrid input filepath.")
  parser.add_argument("-o", "--output", type=str, required=True,
                      help="TextGrid output filepath.")
  parser.add_argument("-w", "--wav-file", type=str, required=True,
                      help="")
  parser.add_argument("-p", "--pauses-tier-name", type=str, default="pauses", help="")
  parser.add_argument("-s", "--silence-boundary", type=float, default=0.25,
                      help="Percent of lower dB recognized as silence.")
  parser.add_argument("-c", "--chunk-size-ms", type=int, default=50,
                      help="")
  parser.add_argument("-m", "--min-silence-duration-ms", type=int, default=1000,
                      help="")
  return add_pause


def add_pause(file: Optional[str], output: str, pauses_tier_name: str, wav_file: str, silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int) -> None:
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
    )

    grid.write(output)
    logger.info("Success!")


def add_pause_tier(grid: Optional[TextGrid], wav: np.ndarray, sr: int, out_tier_name: Optional[str], silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int) -> TextGrid:
  total_duration = get_duration_s(len(wav), sr)

  pause_layer = IntervalTier(
    name=out_tier_name,
    minTime=0,
    maxTime=total_duration,
  )

  chunk_size = ms_to_samples(chunk_size_ms, sr)

  chunks = mask_silence(
    wav=wav,
    silence_boundary=silence_boundary,
    chunk_size=chunk_size,
  )

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
    #splits.append((last_chunk, current_samples))

  # buffer_samples_begin = 100
  # split: Chunk
  # for i, split in enumerate(splits):
  #   if not split.is_silence:
  #     if i > 0:
  #       assert splits[i-1].is_silence
  #       new_size = max(splits[i-1].size - buffer_samples_begin, 0)
  #       splits[i-1].size = new_size
  #       split.size += buffer_samples_begin
  #       last_chunk, last_sample_count = split[i - 1]

  mark_duration: List[Tuple[str, float]] = list()
  for split in splits:
    duration = get_duration_s(split.size, sr)
    if split.is_silence:
      capture_it = duration >= min_silence_duration_ms / 1000
      if capture_it:
        mark_duration.append(("silent", duration))
      else:
        if len(mark_duration) > 0:
          last_segment_was_no_silence = mark_duration[-1][0] == ""
          assert last_segment_was_no_silence
          previous_mark, previous_duration = mark_duration[-1]
          mark_duration[-1] = (previous_mark, previous_duration + duration)
        else:
          mark_duration.append(("", duration))
    else:
      if len(mark_duration) > 0:
        last_segment_was_no_silence = mark_duration[-1][0] == ""
        if last_segment_was_no_silence:
          previous_mark, previous_duration = mark_duration[-1]
          mark_duration[-1] = (previous_mark, previous_duration + duration)
        else:
          mark_duration.append(("", duration))
      else:
        mark_duration.append(("", duration))

  start = pause_layer.minTime
  for mark, duration in mark_duration:
    end = start + duration
    word_interval = Interval(
      minTime=start,
      maxTime=end,
      mark=mark,
    )
    # word_intervals.append(word_interval)
    pause_layer.addInterval(word_interval)
    start = end

  if grid is not None:
    if len(grid.tiers) > 0:
      pause_layer.maxTime = grid.tiers[0].maxTime
  else:
    grid = TextGrid(
      name="Grid",
      minTime=pause_layer.minTime,
      maxTime=pause_layer.maxTime,
      strict=True,
    )
  update_or_add_tier(grid, pause_layer)
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


def mask_silence(wav: np.ndarray, silence_boundary: float, chunk_size: int) -> List[Chunk]:
  assert chunk_size > 0
  if chunk_size > len(wav):
    chunk_size = len(wav)

  trim = 0
  max_value = -1 * get_min_value(wav.dtype)
  its = len(wav) / chunk_size
  its = ceil(its)
  res: List[Chunk] = list()

  dBFSs: List[float] = list()
  for _ in trange(its):
    dBFS = get_dBFS(wav[trim:trim + chunk_size], max_value)
    dBFSs.append(dBFS)
    trim += chunk_size

  #print(dBFSs)
  #print(min(dBFSs))
  #print(max(dBFSs))
  diff = abs(abs(min(dBFSs)) - abs(max(dBFSs)))
  threshold = diff * silence_boundary
  silence_threshold = min(dBFSs) + threshold

  trim = 0
  for dBFS in tqdm(dBFSs):
    is_silence = dBFS < silence_threshold
    chunk_len = len(wav[trim:trim + chunk_size])
    chunk = Chunk(
      size=chunk_len,
      is_silence=is_silence
    )
    res.append(chunk)

    trim += chunk_size

  return res


def get_min_value(dtype):
  if dtype == np.int16:
    return INT16_MIN

  if dtype == np.int32:
    return INT32_MIN

  if dtype == np.float32 or dtype == np.float64:
    return FLOAT32_64_MIN_WAV

  assert False
