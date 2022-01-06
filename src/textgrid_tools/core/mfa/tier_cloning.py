from logging import getLogger

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.core.globals import ExecutionResult
from textgrid_tools.core.mfa.helper import add_or_update_tier, get_tiers
from textgrid_tools.core.validation import (ExistingTierError,
                                            InvalidGridError,
                                            NonDistinctTiersError,
                                            NotExistingTierError)


def clone_tier(grid: TextGrid, tier_name: str, output_tier_name: str, ignore_marks: bool, overwrite_tier: bool) -> ExecutionResult:
  # TODO allow multiple output tier names
  if error := InvalidGridError.validate(grid):
    return error, False

  if error := NotExistingTierError.validate(grid, tier_name):
    return error, False

  if error := NonDistinctTiersError.validate(tier_name, output_tier_name):
    return error, False

  # TODO maybe check also if multiple of that name exist
  if not overwrite_tier and (error := ExistingTierError.validate(grid, output_tier_name)):
    return error, False

  logger = getLogger(__name__)
  tiers = list(get_tiers(grid, {tier_name}))
  if len(tiers) > 1:
    logger.warning(
      f"Found multiple tiers with name \"{tier_name}\", therefore cloning only the first one.")

  first_tier = tiers[0]
  new_tier = copy_tier(first_tier, ignore_marks)
  new_tier.name = output_tier_name

  changed_anything = add_or_update_tier(grid, None, new_tier, overwrite_tier)
  return None, changed_anything


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
