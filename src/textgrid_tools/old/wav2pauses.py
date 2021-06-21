import os
from argparse import ArgumentParser
from logging import Logger, getLogger
from typing import List, Optional, Tuple

import numpy as np
from audio_utils import get_chunks, get_duration_s, get_duration_s_samples
from scipy.io.wavfile import read
from textgrid.textgrid import TextGrid

from textgrid_tools.utils import (check_paths_ok, durations_to_interval_tier,
                                  get_parent_dirpath, ms_to_samples,
                                  update_or_add_tier)

SILENCE_INTERVAL_MARK = "pause"
CONTENT_INTERVAL_MARK = ""


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
  total_duration = get_duration_s(wav, sr)

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
    duration = get_duration_s_samples(chunk.size, sr)
    mark = SILENCE_INTERVAL_MARK if chunk.is_silence else CONTENT_INTERVAL_MARK
    mark_duration.append((mark, duration))

  max_time = total_duration

  if grid is not None and len(grid.tiers) > 0:
    max_time = grid.tiers[0].maxTime

  pause_tier = durations_to_interval_tier(
    durations=mark_duration,
    maxTime=max_time,
    name=out_tier_name,
  )

  if grid is None:
    grid = TextGrid(
      name="Grid",
      minTime=pause_tier.minTime,
      maxTime=pause_tier.maxTime,
      strict=True,
    )

  update_or_add_tier(grid, pause_tier)
  return grid
