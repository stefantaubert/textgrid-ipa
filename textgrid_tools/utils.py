import os
import re
from logging import Logger
from typing import List, Optional, Tuple

from textgrid.textgrid import Interval, IntervalTier, TextGrid


def durations_to_interval_tier(durations: List[Tuple[str, float]], maxTime: float) -> IntervalTier:
  word_tier = IntervalTier(
    minTime=0,
    maxTime=maxTime,
  )

  start = 0
  for i, word_duration in enumerate(durations):
    word, duration = word_duration
    end = start + duration
    is_last = i == len(durations) - 1
    if is_last:
      # to prevent calculation inprecisions due to float, and therefore an invalid tier size.
      end = maxTime
    word_interval = Interval(
      minTime=start,
      maxTime=end,
      mark=word,
    )
    # word_intervals.append(word_interval)
    word_tier.addInterval(word_interval)
    start = end

  return word_tier

def ms_to_samples(ms, sampling_rate: int):
  res = int(ms * sampling_rate / 1000)
  return res


def check_interval_has_content(interval: Interval) -> bool:
  content = interval.mark.strip()
  has_content = content != ""
  return has_content


def check_paths_ok(in_path: str, out_path: str, logger: Logger) -> bool:
  if not os.path.exists(in_path):
    logger.error("The file couldn't be found!")
    return False

  if in_path == out_path:
    logger.error("Input and output files should be different!")
    return False

  return True


# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')


def collapse_whitespace(text: str) -> str:
  return re.sub(_whitespace_re, ' ', text)


def update_or_add_tier(grid: TextGrid, tier: IntervalTier) -> None:
  existing_tier: Optional[IntervalTier] = grid.getFirst(tier.name)
  if existing_tier is not None:
    existing_tier.intervals.clear()
    existing_tier.intervals.extend(tier.intervals)
    existing_tier.maxTime = tier.maxTime
    existing_tier.minTime = tier.minTime
  else:
    grid.append(tier)
