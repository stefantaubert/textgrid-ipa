from logging import getLogger
from typing import List, Tuple

import numpy as np
from audio_utils.audio import get_duration_s_samples
from text_utils import Language
from text_utils.symbol_format import SymbolFormat
from text_utils.text import text_to_sentences
from textgrid.textgrid import IntervalTier, TextGrid
from textgrid_tools.utils import durations_to_intervals


def extract_sentences_to_textgrid(original_text: str, audio: np.ndarray, sr: int, tier_name: str, time_factor: float) -> TextGrid:
  logger = getLogger(__name__)
  sentences = text_to_sentences(
    text=original_text,
    text_format=SymbolFormat.GRAPHEMES,
    lang=Language.ENG,
  )

  logger.info(f"Extracted {len(sentences)} sentences.")
  audio_len_s = get_duration_s_samples(len(audio), sr)
  audio_len_s_streched = audio_len_s * time_factor
  logger.info(f"Streched time by factor {time_factor}: {audio_len_s} -> {audio_len_s_streched}")

  grid = TextGrid(
    minTime=0,
    maxTime=audio_len_s_streched,
    name=None,
    strict=True,
  )

  tier = IntervalTier(
    name=tier_name,
    minTime=grid.minTime,
    maxTime=grid.maxTime,
  )

  avg_character_len_s = audio_len_s_streched / len(original_text)
  durations: List[Tuple[str, float]] = []
  for sentence in sentences:
    sentence_duration = len(sentence) * avg_character_len_s
    durations.append((sentence, sentence_duration))

  intervals = durations_to_intervals(durations, maxTime=grid.maxTime)
  tier.intervals.extend(intervals)
  grid.append(tier)

  return grid
