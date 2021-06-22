from collections import Counter
from logging import getLogger
from typing import List, Optional, Tuple

import numpy as np
from audio_utils import (get_chunks, get_duration_s, get_duration_s_samples,
                         ms_to_samples)
from text_utils.ipa2symb import IPAExtractionSettings
from text_utils.language import Language
from text_utils.text import EngToIpaMode, text_to_ipa, text_to_symbols
from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import (check_interval_has_content,
                                  collapse_whitespace, durations_to_intervals,
                                  grid_contains_tier, intervals_to_tier,
                                  log_counter, update_tier)
from tqdm import tqdm


def get_template_textgrid(wav: np.ndarray, sr: int) -> TextGrid:
  total_duration = get_duration_s(wav, sr)
  grid = TextGrid(
    name="Recording",
    minTime=0,
    maxTime=total_duration,
    strict=True,
  )

  return grid


def add_pause_tier(grid: TextGrid, wav: np.ndarray, sr: int, out_tier_name: Optional[str], silence_boundary: float, chunk_size_ms: int, min_silence_duration_ms: int, min_content_duration_ms: int, content_buffer_start_ms: int, content_buffer_end_ms: int, silence_mark: str, content_mark: str, overwrite_tier: bool) -> None:
  logger = getLogger(__name__)

  if grid_contains_tier(grid, out_tier_name) and not overwrite_tier:
    logger.error(f"Tier {out_tier_name} already exists!")
    return

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

  logger.info(f"Extracted {len(chunks)} chunks.")

  mark_duration: List[Tuple[str, float]] = list()
  for chunk in chunks:
    duration = get_duration_s_samples(chunk.size, sr)
    mark = silence_mark if chunk.is_silence else content_mark
    mark_duration.append((mark, duration))

  intervals = durations_to_intervals(mark_duration, grid.maxTime)
  logger.info(f"Extracted {len(intervals)} intervals.")

  pause_tier = intervals_to_tier(intervals, out_tier_name)

  if grid_contains_tier(grid, pause_tier.name):
    assert overwrite_tier
    logger.info("Overwriting tier...")
    update_tier(grid, pause_tier)
  else:
    logger.info("Adding tier...")
    grid.append(pause_tier)


def add_words_tier(grid: TextGrid, in_tier_name: str, out_tier_name: str, overwrite_tier: bool) -> None:
  assert grid_contains_tier(grid, in_tier_name)
  logger = getLogger(__name__)

  if grid_contains_tier(grid, out_tier_name) and not overwrite_tier:
    logger.error(f"Tier {out_tier_name} already exists!")
    return

  in_tier: IntervalTier = grid.getFirst(in_tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals

  word_durations: List[Tuple[str, float]] = list()
  for tier_interval in in_tier_intervals:
    sentence: str = tier_interval.mark
    sentence = sentence.strip()
    sentence = collapse_whitespace(sentence)
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

  intervals = durations_to_intervals(word_durations, grid.maxTime)
  logger.info(f"Extracted {len(intervals)} intervals out of {len(in_tier_intervals)}.")

  pause_tier = intervals_to_tier(intervals, out_tier_name)

  if grid_contains_tier(grid, pause_tier.name):
    assert overwrite_tier
    logger.info("Overwriting tier...")
    update_tier(grid, pause_tier)
  else:
    logger.info("Adding tier...")
    grid.append(pause_tier)


def add_ipa_tier(grid: TextGrid, in_tier_name: str, out_tier_name: str, mode: Optional[EngToIpaMode], replace_unknown_with: str, consider_ipa_annotations: bool, overwrite_tier: bool, in_tier_lang: Language) -> None:
  assert grid_contains_tier(grid, in_tier_name)
  logger = getLogger(__name__)

  if grid_contains_tier(grid, out_tier_name) and not overwrite_tier:
    logger.error(f"Tier {out_tier_name} already exists!")
    return

  in_tier: IntervalTier = grid.getFirst(in_tier_name)
  in_tier_intervals: List[Interval] = in_tier.intervals

  ipa_intervals: List[Interval] = [
    Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=text_to_ipa(
        text=interval.mark,
        lang=in_tier_lang,
        mode=mode,
        replace_unknown_with=replace_unknown_with,
        consider_ipa_annotations=consider_ipa_annotations,
        use_cache=True,
        logger=logger,
      )
    ) for interval in tqdm(in_tier_intervals)
  ]

  logger.info(f"Processed {len(ipa_intervals)} intervals.")

  tier = intervals_to_tier(ipa_intervals, out_tier_name)

  if grid_contains_tier(grid, tier.name):
    assert overwrite_tier
    logger.info("Overwriting tier...")
    update_tier(grid, tier)
  else:
    logger.info("Adding tier...")
    grid.append(tier)


def log_tier_stats(grid: TextGrid, tier_name: str, lang: Language, ipa_settings: Optional[IPAExtractionSettings]) -> None:
  assert grid_contains_tier(grid, tier_name)
  logger = getLogger(__name__)
  tier_names = [x.name for x in grid.tiers]
  logger.info(f"Tiers: {', '.join(tier_names)}")
  tier: IntervalTier = grid.getFirst(tier_name)
  tier_intervals: List[Interval] = tier.intervals

  total_content_duration = 0.0
  all_symbols = []
  warn_symbols = ["\n", "\r", "\t", "\\", "/", "'", "\"", "[", "]", "(", ")", "|"]
  warn_symbols_str = " ".join([f"{x!r}"[1:-1] for x in warn_symbols])
  for interval in tier_intervals:
    has_content = check_interval_has_content(interval)
    if has_content:
      content_duration = interval.maxTime - interval.minTime
      total_content_duration += content_duration
      symbols = text_to_symbols(interval.mark, lang=lang, ipa_settings=ipa_settings, logger=logger)
      if any(x in interval.mark for x in warn_symbols):
        logger.warning(
          f"Interval [{interval.minTime}, {interval.maxTime}] ({interval.mark!r}) contains any of these undesired symbols: {warn_symbols_str}")
      all_symbols.extend(symbols)

  symbol_counter = Counter(all_symbols)
  logger.info("Symbols:")
  log_counter(symbol_counter)

  total_duration = tier.maxTime - tier.minTime
  content_percent = total_content_duration / total_duration * 100
  silence_percent = (total_duration - total_content_duration) / total_duration * 100
  logger.info(
    f"Duration content: {total_content_duration:.0f}s of {total_duration:.0f}s ({content_percent:.2f}%)")
  logger.info(f"Duration content: {total_content_duration/60:.0f}min of {total_duration/60:.0f}min")
  logger.info(
    f"Duration of silence: {total_duration - total_content_duration:.0f}s of {total_duration:.0f}s ({silence_percent:.2f}%)")
  logger.info(
    f"Duration of silence: {(total_duration - total_content_duration)/60:.0f}min of {total_duration/60:.0f}min")
