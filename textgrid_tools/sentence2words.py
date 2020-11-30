import os
from argparse import ArgumentParser
from logging import getLogger
from typing import List, Optional, Tuple

from textgrid.textgrid import Interval, IntervalTier, TextGrid

from textgrid_tools.utils import (check_paths_ok, collapse_whitespace,
                                  durations_to_interval_tier,
                                  get_parent_dirpath, update_or_add_tier)


def init_words_parser(parser: ArgumentParser):
  parser.add_argument("--file", type=str, required=True, help="TextGrid input filepath.")
  parser.add_argument("--output", type=str, required=True,
                      help="TextGrid output filepath.")
  parser.add_argument("--sentences-tier-name", type=str, default="sentences",
                      help="The name of the tier which should contain the IPA transcriptions for reference. If the tier exists, it will be overwritten.")
  parser.add_argument("--words-tier-name", type=str, default="words",
                      help="The name of the tier with the English words annotated.")
  return add_words


def add_words(file: str, output: str, sentences_tier_name: str, words_tier_name: str) -> None:
  logger = getLogger()
  if check_paths_ok(file, output, logger):
    grid = TextGrid()
    grid.read(file)

    logger.info("Extracting words from sentences...")

    add_words_tier(
      grid=grid,
      in_tier_name=sentences_tier_name,
      out_tier_name=words_tier_name,
    )

    os.makedirs(get_parent_dirpath(output), exist_ok=True)
    grid.write(output)
    logger.info("Success!")


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

  word_tier = durations_to_interval_tier(
    durations=word_durations,
    maxTime=in_tier.maxTime,
  )

  # word_tier.maxTime = start
  update_or_add_tier(grid, word_tier)
