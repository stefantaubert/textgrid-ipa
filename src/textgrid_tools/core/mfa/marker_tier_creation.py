from logging import getLogger
from typing import List

from textgrid.textgrid import Interval, IntervalTier, TextGrid
from textgrid_tools.utils import update_or_add_tier


def add_marker_tier(grid: TextGrid, reference_tier_name: str, new_tier_name: str, overwrite_existing_tier: bool):
  logger = getLogger(__name__)
  reference_tier: IntervalTier = grid.getFirst(reference_tier_name)
  if reference_tier is None:
    raise Exception("Reference tier not found!")

  new_ipa_tier: IntervalTier = grid.getFirst(new_tier_name)
  if new_ipa_tier is not None and not overwrite_existing_tier:
    raise Exception("New tier already exists!")

  reference_tier_intervals: List[Interval] = reference_tier.intervals

  new_tier = IntervalTier(
    minTime=reference_tier.minTime,
    maxTime=reference_tier.maxTime,
    name=new_tier_name,
  )

  for interval in reference_tier_intervals:
    marker_interval = Interval(
      minTime=interval.minTime,
      maxTime=interval.maxTime,
      mark="",
    )

    new_tier.addInterval(marker_interval)

  if overwrite_existing_tier:
    update_or_add_tier(grid, new_tier)
  else:
    grid.append(new_tier)
