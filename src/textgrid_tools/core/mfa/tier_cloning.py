from logging import getLogger

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.mfa.helper import (check_is_valid_grid, get_tiers,
                                            tier_exists)


def can_clone_tier(grid: TextGrid, tier: str) -> bool:
  logger = getLogger(__name__)

  if not check_is_valid_grid(grid):
    logger.error("Grid is invalid!")
    return False

  if not tier_exists(grid, tier):
    logger.error(f"Tier \"{tier}\" not found!")
    return False

  return True


def clone_tier(grid: TextGrid, tier: str, new_name: str, ignore_marks: bool) -> None:
  logger = getLogger(__name__)
  tiers = list(get_tiers(grid, {tier}))
  if len(tiers) > 1:
    logger.warning(
      f"Found multiple tiers with name \"{tier}\", therefore cloning only the first one.")

  first_tier = tiers[0]
  new_tier = copy_tier(first_tier, ignore_marks)
  new_tier.name = new_name
  grid.append(new_tier)


def copy_tier(tier: IntervalTier, ignore_marks: bool) -> IntervalTier:
  result = IntervalTier(
    name=tier.name,
    maxTime=tier.maxTime,
    minTime=tier.minTime,
  )

  for interval in tier.intervals:
    cloned_interval = copy_interval(interval, ignore_marks)
    result.addInterval(cloned_interval)

  return result


def copy_interval(interval: Interval, ignore_marks: bool) -> Interval:
  new_mark = "" if ignore_marks else str(interval.mark)
  result = Interval(
    minTime=interval.minTime,
    mark=new_mark,
    maxTime=interval.maxTime,
  )
  return result
