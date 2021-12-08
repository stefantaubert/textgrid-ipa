from logging import getLogger
from typing import List

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import interval_is_empty
from textgrid_tools.utils import update_or_add_tier


def add_graphemes_from_words(grid: TextGrid, original_text_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool):
  logger = getLogger(__name__)
  original_text_tier: IntervalTier = grid.getFirst(original_text_tier_name)
  if original_text_tier is None:
    raise Exception("Original text-tier not found!")

  new_ipa_tier: IntervalTier = grid.getFirst(new_tier_name)
  if new_ipa_tier is not None and not overwrite_existing_tier:
    raise Exception("Graphemes tier already exists!")

  original_text_tier_intervals: List[Interval] = original_text_tier.intervals

  graphemes_tier = IntervalTier(
    minTime=original_text_tier.minTime,
    maxTime=original_text_tier.maxTime,
    name=new_tier_name,
  )

  for interval in original_text_tier_intervals:
    graphemes = ""

    if not interval_is_empty(interval):
      graphemes = " ".join(list(str(interval.mark)))

    graphemes_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark=graphemes,
    )

    graphemes_tier.addInterval(graphemes_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, graphemes_tier)
  else:
    grid.append(graphemes_tier)
