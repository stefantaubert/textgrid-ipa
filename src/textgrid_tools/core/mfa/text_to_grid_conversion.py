from logging import getLogger
from typing import Optional

from textgrid.textgrid import Interval, IntervalTier, TextGrid


def can_convert_text_to_grid(tier_out: str, characters_per_second: float) -> bool:
  logger = getLogger(__name__)
  if len(tier_out) == 0:
    logger.error("Please specify an output name!")
    return False

  if characters_per_second <= 0:
    logger.error("characters_per_second need to be > 0!")
    return False
  return True


def convert_text_to_grid(text: str, grid_name_out: Optional[str], tier_out: str, characters_per_second: float) -> TextGrid:
  assert can_convert_text_to_grid(tier_out, characters_per_second)

  if len(text) == 0:
    duration = 1
  else:
    duration = len(text) / characters_per_second

  grid = TextGrid(
    maxTime=duration,
    minTime=0,
    name=grid_name_out,
    strict=True,
  )

  tier = IntervalTier(
    name=tier_out,
    minTime=0,
    maxTime=duration,
  )

  interval = Interval(
    minTime=0,
    maxTime=duration,
    mark=text,
  )

  tier.addInterval(interval)
  grid.append(tier)

  return grid
