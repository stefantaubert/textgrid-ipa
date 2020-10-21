from math import ceil
from typing import List, Optional, Tuple

import numpy as np
from epitran import Epitran
from scipy.io.wavfile import read
from tqdm import tqdm
from tqdm.std import trange

from silence_detection import (Chunk, get_duration_s, mask_silence,
                               ms_to_samples)
from textgrid.textgrid import Interval, IntervalTier, TextGrid


def update_or_add_tier(grid: TextGrid, tier: IntervalTier) -> None:
  existing_tier: Optional[IntervalTier] = grid.getFirst(tier.name)
  if existing_tier is not None:
    existing_tier.intervals.clear()
    existing_tier.intervals.extend(tier.intervals)
    existing_tier.maxTime = tier.maxTime
    existing_tier.minTime = tier.minTime
  else:
    grid.append(tier)


def add_ipa_tier(grid: TextGrid, in_tier_name: str,
                 out_tier_name: Optional[str]) -> None:
  in_tier: IntervalTier = grid.getFirst(in_tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals
  ipa_intervals = convert_to_ipa_intervals(in_tier_intervals)

  standard_tier = IntervalTier(
    name=out_tier_name,
    minTime=in_tier.minTime,
    maxTime=in_tier.maxTime
  )
  standard_tier.intervals.extend(ipa_intervals)

  update_or_add_tier(grid, standard_tier)


def add_words_tier(grid: TextGrid, in_tier_name: str,
                   out_tier_name: Optional[str]) -> None:
  in_tier: IntervalTier = grid.getFirst(in_tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals
  word_tier = IntervalTier(
    name=out_tier_name,
    minTime=in_tier.minTime,
    maxTime=in_tier.maxTime,
  )

  word_durations: List[Tuple[str, float]] = list()
  for tier_interval in in_tier_intervals:
    sentence: str = tier_interval.mark
    sentence = sentence.strip()
    sentence_len = len(sentence)

    is_pause = sentence_len == 0
    if is_pause:
      pause_duration = tier_interval.maxTime - tier_interval.minTime
      word_durations.append(("", pause_duration))
    else:
      words = sentence.split(" ")
      word_separator_counts = len(words) - 1
      sentence_len -= word_separator_counts
      sentence_duration: float = tier_interval.maxTime - tier_interval.minTime
      avg_char_duration = sentence_duration / sentence_len

      # word_intervals: List[Interval] = list()
      for word in words:
        word_duration = len(word) * avg_char_duration
        word_durations.append((word, word_duration))

  start = word_tier.minTime
  for word, duration in word_durations:
    end = start + duration
    word_interval = Interval(
      minTime=start,
      maxTime=end,
      mark=word,
    )
    # word_intervals.append(word_interval)
    word_tier.addInterval(word_interval)
    start = end
  word_tier.maxTime = start
  update_or_add_tier(grid, word_tier)


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


def convert_to_ipa_intervals(tiers: List[IntervalTier]) -> List[IntervalTier]:
  epi = Epitran('eng-Latn')
  ipa_intervals: List[Interval] = [convert_to_ipa_interval(x, epi) for x in tiers]
  return ipa_intervals


def convert_to_ipa_interval(tier: IntervalTier, epitran: Epitran) -> IntervalTier:
  ipa_interval = Interval(
    minTime=tier.minTime,
    maxTime=tier.maxTime,
    mark=epitran.transliterate(tier.mark),
  )
  return ipa_interval


if __name__ == "__main__":
  grid = TextGrid()
  grid.read("/datasets/sentences.TextGrid")

  file = "/datasets/test.wav"
  sampling_rate, wav = read(file)

  grid = add_pause_tier(
    # grid=None,
    grid=grid,
    wav=wav,
    sr=sampling_rate,
    out_tier_name="pause:gen",
    chunk_size_ms=50,
    silence_boundary=0.25,
    min_silence_duration_ms=1000,
  )

  grid.write("/datasets/pauses.TextGrid")

  add_words_tier(
    grid=grid,
    in_tier_name="sentences",
    out_tier_name="words:gen",
  )

  grid.write("/datasets/out1.TextGrid")

  add_ipa_tier(
    grid=grid,
    in_tier_name="words:gen",
    out_tier_name="IPA-standard",
  )
