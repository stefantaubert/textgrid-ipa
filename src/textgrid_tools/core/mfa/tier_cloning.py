from logging import getLogger
from typing import Iterable, cast

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import get_tiers


def clone_tier(grid: TextGrid, tier_name: str, new_tier_name: str) -> None:
  logger = getLogger(__name__)
  tiers = list(get_tiers(grid, {tier_name}))
  if len(tiers) > 1:
    logger.warning(
      f"Found multiple tiers with name {tier_name}, therefore cloning only the first one.")

  first_tier = tiers[0]
  new_tier = copy_tier(first_tier)
  new_tier.name = new_tier_name
  grid.append(new_tier)


def copy_tier(tier: IntervalTier) -> IntervalTier:
  result = IntervalTier(
    name=tier.name,
    maxTime=tier.maxTime,
    minTime=tier.minTime,
  )

  for interval in tier.intervals:
    cloned_interval = copy_interval(interval)
    result.addInterval(cloned_interval)

  return result


def copy_interval(interval: Interval) -> Interval:
  result = Interval(
    minTime=interval.minTime,
    mark=interval.mark,
    maxTime=interval.maxTime,
  )
  return result
